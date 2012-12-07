# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Alexander Slesarev <nuald@codedgers.com>.
# All rights reserved by Codedgers Inc (http://codedgers.com).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Code example processor module. """

import re
import inspect
import copy
import os.path
from trac.wiki.macros import IWikiMacroProvider
from trac.core import implements, Component, TracError
from trac.util.text import to_unicode
from trac.versioncontrol.api import NoSuchNode, RepositoryManager
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome, \
    Markup, add_script
from trac.config import Option

try:
    __import__('pygments', {}, {}, [])
    HAVE_PYGMENTS = True
except ImportError:
    HAVE_PYGMENTS = False

if HAVE_PYGMENTS:
    from pygments.lexers import get_lexer_by_name
    from trac.mimeview.pygments import GenshiHtmlFormatter
    from pygments.util import ClassNotFound

__all__ = ['CodeExample']


class CodeExample(Component):
    """Render a code example box that supports syntax highlighting.
    It support three types of examples: simple, correct, and incorrect.
    The '''SELECT ALL''' link highlights all of the code in the box
    to simplify the copy and paste action.

    The simple example:
    {{{
    {{{
    #!CodeExample
    #!python
    @staticmethod
    def get_templates_dirs():
        \"\"\" Notify Trac about templates dir. \"\"\"
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    }}}
    }}}

    will be rendered as:

    [[Image(//chrome/ce/img/example1.png)]]

    The incorrect example:
    {{{
    {{{
    #!CodeExample
    ## type = bad
    #!haskell
    fibs = 0 : 1 : [ a + b | a <- fibs | b <- tail fibs ]
    }}}
    }}}

    will be rendered as:

    [[Image(//chrome/ce/img/example2.png)]]

    The correct example:
    {{{
    {{{
    #!CodeExample
    ## type = good
    #!haskell
    fibs = 0 : 1 : zipWith (+) fibs (tail fibs)
    }}}
    }}}

    will be rendered as:

    [[Image(//chrome/ce/img/example3.png)]]

    There is also support for getting sources from the repository:
    {{{
    {{{
    #!CodeExample
    ## path=GPGMail/Source/GPGMailPreferences.m
    ## regex=".*updater\s*{"
    ## lines=3
    #!objective-c
    }}}
    }}}

    will be rendered as:

    [[Image(//chrome/ce/img/example4.png)]]

    Parameters:
        * '''type''' - (optional) a type of the example: simple (default),
        good, bad
        * '''title''' - (optional) the title of the example
        * '''path''' - (optional) a file in the repository (using TracLinks
        format for source code)
        * '''repo''' - (optional) repository to use (Trac 0.12 and upper only)
        * '''regex''' - (optional) a regular expression indicates
        where to start an example
        * '''lines''' - (optional) number of lines to show
    """

    implements(ITemplateProvider, IWikiMacroProvider)

    styles = {
        'CodeExample': {'title': u'EXAMPLE', 'css_class': 'example'},
        'BadCodeExample': {'title': u'INCORRECT EXAMPLE',
                           'css_class': 'bad_example'},
        'GoodCodeExample': {'title': u'CORRECT EXAMPLE',
                            'css_class': 'good_example'}}

    default_style = Option('mimeviewer', 'pygments_default_style', 'trac',
        """The default style to use for Pygments syntax highlighting.""")

    def __init__(self):
        Component.__init__(self)
        self._render_exceptions = []
        self._index = 0
        self._link = None
        self._args = None
        self._type = 'CodeExample'
        self._path = None, None, None, None
        self._regex_match = None
        self._lines_match = None
        self._title = None
        self._repo = None

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield self.__class__.__name__

    def get_macro_description(self, name):
        """Returns the required macro description."""
        doc = inspect.getdoc(self.__class__)
        return doc and to_unicode(doc) or ''

    def render_as_lang(self, lang, content):
        """ Try to render 'content' as 'lang' code. """
        try:
            lexer = get_lexer_by_name(lang, stripnl=False)
            tokens = lexer.get_tokens(content)
            stream = GenshiHtmlFormatter().generate(tokens)
            return stream.render(strip_whitespace=False)
        except ClassNotFound, exception:
            self._render_exceptions.append(exception)
        return content

    def get_analyzed_content(self, text, required_lines):
        """ Strip text for required lines. """
        lines = list(enumerate(text.split('\n')))
        if required_lines:
            lines_range = self.get_range(required_lines)
            lines = [i for i in lines if i[0] + 1 in lines_range]
        return lines

    def get_quote(self, text, args, required_lines=None, focus_line=None):
        """ Try to get the required quote from the text. """
        begin_idx = 0
        content = self.get_analyzed_content(text, required_lines)
        if self._regex_match:
            regex = self._regex_match.group(1)
            for begin_idx, lines in list(enumerate(content)):
                if re.search(regex, lines[1]):
                    break
            else:
                err = 'Nothing is match to regex: ' + regex
                self._render_exceptions.append(err)
                begin_idx = 0
        if begin_idx and self._link and not focus_line:
            self._link += "#L%d" % (list(content)[begin_idx][0] + 1)
        if self._link and focus_line:
            self._link += "#L%d" % focus_line
        simple_content = [i[1] for i in content]
        if self._lines_match:
            lines = int(self._lines_match.group(1))
            return '\n'.join(simple_content[begin_idx:lines + begin_idx])
        else:
            return '\n'.join(simple_content[begin_idx:])

    def get_repos_manager(self):
        """ Get repository manager. """
        return RepositoryManager(self.env)

    def extract_match(self, expr):
        """ Search for regexp and remove from arguments if found. """
        match = re.search(expr, self._args, re.MULTILINE)
        if match:
            self._args = self._args.replace(match.group(0), '').strip()
        return match

    def extract_path(self):
        """ Parse source path. """
        self._path = None, None, None, None
        path_match = self.extract_match(
            '^\s*##\s*path\s*=\s*(?P<path>.+?)(?P<rev>@\w+)?' \
            '(?P<lines>:\d+(-\d+)?(,\d+(-\d+)?)*)?(?P<focus>#L\d+)?\s*$')
        if path_match:
            path = path_match.group('path')
            rev = path_match.group('rev')
            if rev:
                rev = rev[1:]
            lines = path_match.group('lines')
            if lines:
                lines = lines[1:]
            focus_line = path_match.group('focus')
            if focus_line:
                focus_line = int(focus_line[2:])
            self._path = path, rev, lines, focus_line

    @staticmethod
    def get_range(lines):
        """ Get range from lines string. """
        groups = lines.split(',')
        lines_range = set()
        for group in groups:
            numbers = group.strip().split('-')
            if len(numbers) == 2:
                num1, num2 = numbers
                lines_range |= set(range(int(num1), int(num2) + 1))
            else:
                lines_range.add(int(numbers[0]))
        return sorted(lines_range)

    def get_sources(self, src):
        """ Try to get sources from the required path. """
        try:
            repo_mgr = self.get_repos_manager()
            repos = repo_mgr.get_repository(self._repo)
        except TracError, exception:
            self._render_exceptions.append(exception)
            return src
        try:
            path, rev, lines, focus_line = self._path
            if repos and path:
                try:
                    node = repos.get_node(path, rev)
                    self._link = self.env.href.browser(node.path)
                    stream = node.get_content()
                    src = self.get_quote(to_unicode(stream.read()), src, lines,
                                     focus_line)
                except NoSuchNode, exception:
                    self._render_exceptions.append(exception)
            else:
                self._render_exceptions.append('Path element is not found.')
        finally:
            repo_mgr.shutdown()
        return src

    def actualize(self, src, is_path):
        """ Detect and load required sources. """
        if is_path:
            src = self.get_sources(src)
        return src

    def pygmentize_args(self, args, have_pygments):
        """ Process args via Pygments. """
        is_path = self._path[0] != None
        if have_pygments:
            args += '\n'  # fix pigmentation issues
            match = re.match('^#!(.+?)\s+((.*\s*)*)$', args, re.MULTILINE)
            if match:
                lang = match.group(1)
                src = self.actualize(match.group(2), is_path)
                return self.render_as_lang(lang, src)
        return self.actualize(args, is_path)

    @staticmethod
    def get_templates_dirs():
        """ Notify Trac about templates dir. """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    @staticmethod
    def get_htdocs_dirs():
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('ce', os.path.abspath(resource_filename(__name__, 'htdocs')))]

    @staticmethod
    def is_have_pygments():
        """ Helper for checking is Pygments installed. """
        return HAVE_PYGMENTS

    def extract_type(self):
        """ Extract macro type. """
        self._type = 'CodeExample'
        match = self.extract_match('^\s*##\s*type\s*=\s*(.+)\s*$')
        if match:
            macro_type = match.group(1)
            if 'bad' in macro_type:
                self._type = 'BadCodeExample'
            if 'good' in macro_type:
                self._type = 'GoodCodeExample'
        self._title = self.styles[self._type]['title']
        match = self.extract_match('^\s*##\s*title\s*=\s*(.+)\s*$')
        if match:
            self._title = match.group(1)

    def extract_repo(self):
        """ Extract macro type. """
        self._repo = None
        match = self.extract_match('^\s*##\s*repo\s*=\s*(.+)\s*$')
        if match:
            self._repo = match.group(1)

    def extract_options(self):
        """ Extract options from the macro arguments. """
        self.extract_type()
        self.extract_path()
        self.extract_repo()
        self._regex_match = self.extract_match(
            '^\s*##\s*regex\s*=\s*"?(.+?)"?\s*$')
        self._lines_match = self.extract_match(
            '^\s*##\s*lines\s*=\s*(\d+)\s*$')

    def expand_macro(self, formatter, name, args):
        """ Expand macro parameters and return required html. """
        self._render_exceptions = []
        self._link = None
        self._index += 1
        self._args = args
        self.extract_options()
        add_stylesheet(formatter.req, '/pygments/%s.css' %
                       formatter.req.session.get('pygments_style',
                                                 self.default_style))
        add_script(formatter.req, 'ce/js/select_code.js')
        add_stylesheet(formatter.req, 'ce/css/codeexample.css')
        data = copy.copy(self.styles[self._type])
        args = to_unicode(self.pygmentize_args(self._args, HAVE_PYGMENTS))
        data.update({'args': Markup(args)})
        data.update({'exceptions': self._render_exceptions})
        data.update({'index': self._index})
        data.update({'link': self._link})
        data.update({'title': self._title})
        req = formatter.req
        return Chrome(self.env).render_template(req, 'codeexample.html', data,
            None, fragment=True).render(strip_whitespace=False)
