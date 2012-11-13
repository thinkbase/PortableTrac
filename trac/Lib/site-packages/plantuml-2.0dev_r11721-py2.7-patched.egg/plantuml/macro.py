# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Polar Technologies - www.polartech.es
# Copyright (C) 2010 Alvaro J Iradier
# Copyright (C) 2012 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import hashlib
import os
import re
from subprocess import Popen, PIPE

from genshi.builder import tag
from trac.config import Option
from trac.core import implements
from trac.util.translation import _
from trac.versioncontrol.api import RepositoryManager
from trac.web import IRequestHandler
from trac.wiki.formatter import format_to_html, system_message
from trac.wiki.macros import WikiMacroBase

img_dir = 'cache/plantuml'

class PlantUmlMacro(WikiMacroBase):
    """
    A wiki processor that renders PlantUML diagrams in wiki text.
    
    Example:
    {{{
    {{{
    #!PlantUML
    @startuml
    Alice -> Bob: Authentication Reque
    st
    Bob --> Alice: Authentication Response
    Alice -> Bob: Another authentication Request
    Alice <-- Bob: another authentication Response
    @enduml
    }}}
    }}}
    
    Results in:
    {{{
    #!PlantUML
    @startuml
    Alice -> Bob: Authentication Request
    Bob --> Alice: Authentication Response
    Alice -> Bob: Another authentication Request
    Alice <-- Bob: another authentication Response
    @enduml
    }}}
    """

    implements(IRequestHandler)

    plantuml_jar = Option('plantuml', 'plantuml_jar', '',
        """Path to PlantUML jar file. The jar file can be downloaded from the
          [http://plantuml.sourceforge.net/download.html PlantUML] site.""")
    java_bin = Option('plantuml', 'java_bin', 'java',
        """Path to the Java binary file. The default is `java`, which and
           assumes that the Java binary is on the search path.""")
    
    def __init__(self):
        self.abs_img_dir = os.path.join(os.path.abspath(self.env.path), img_dir)
        if not os.path.isdir(self.abs_img_dir):
            os.makedirs(self.abs_img_dir)

    def expand_macro(self, formatter, name, content):
        if not self.plantuml_jar:
            return system_message(_("Installation error: plantuml_jar option not defined in trac.ini"))
        if not os.path.exists(self.plantuml_jar):
            return system_message(_("Installation error: plantuml.jar not found at '%s'") % self.plantuml_jar)
        
        # Trac 0.12 supports expand_macro(self, formatter, name, content, args)
        # which allows us to readily differentiate between a WikiProcess and WikiMacro
        # call. To support Trac 0.11, some additional work is required.
        try:
            args = formatter.code_processor.args
        except AttributeError:
            args = None
        
        path = None
        if not args: #Could be WikiProcessor or WikiMacro call
            if content.strip().startswith("@startuml"):
                markup = content
                path = None
            else:
                path = content
                if not path:
                    return system_message(_("Path not specified"))
        elif args: #WikiProcessor with args
            path = args.get('path')
            if not path:
                return system_message(_("Path not specified"))
        
        if path:
            markup, exists = self._read_source_from_repos(formatter, path)
            if not exists:
                return markup
        else:
            if not content:
                return system_message(_("No UML text defined"))
            markup = content.encode('utf-8').strip()

        img_id = hashlib.sha1(markup).hexdigest()
        if not self._is_img_existing(img_id):
            cmd = '%s -jar -Djava.awt.headless=true "%s" -charset UTF-8 -pipe' % (self.java_bin, self.plantuml_jar)
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            (img_data, stderr) = p.communicate(input=markup)
            if p.returncode != 0:
                return system_message(_("Error running plantuml: '%s'") % stderr)            
            self._write_img_to_file(img_id, img_data)
        
        link = formatter.href('plantuml', id=img_id)
        return tag.img(src=link)

    def get_macros(self):
        yield 'plantuml' #WikiProcessor syntax
        yield 'PlantUml' #WikiMacros syntax
        yield 'PlantUML' #deprecated, retained for backward compatibility

    # IRequestHandler
    def match_request(self, req):
        return re.match(r'/plantuml?$', req.path_info)
    
    def process_request(self, req):
        img_id = req.args.get('id')
        img_data = self._read_img_from_file(img_id)
        req.send(img_data, 'image/png', status=200)
        return ""

    # Internal
    def _get_img_path(self, img_id):
        img_path = os.path.join(self.abs_img_dir, img_id)
        img_path += '.png'
        return img_path

    def _is_img_existing(self, img_id):
        img_path = self._get_img_path(img_id)
        return os.path.isfile(img_path)

    def _write_img_to_file(self, img_id, data):
        img_path = self._get_img_path(img_id)
        open(img_path, 'wb').write(data)

    def _read_img_from_file(self, img_id):
        img_path = self._get_img_path(img_id)
        img_data = open(img_path, 'rb').read()
        return img_data

    def _read_source_from_repos(self, formatter, src_path):
        repos_mgr = RepositoryManager(self.env)
        try: #0.12+
            repos_name, repos, source_obj = repos_mgr.get_repository_by_path(src_path)
        except AttributeError, e: #0.11
            repos = repos_mgr.get_repository(formatter.req.authname)
        path, rev = _split_path(src_path)
        if repos.has_node(path, rev):
            node = repos.get_node(path, rev)
            content = node.get_content().read()
            exists = True
        else:
            rev = rev or repos.get_youngest_rev()
            # TODO: use `raise NoSuchNode(path, rev)`
            content = system_message(_("No such node '%s' at revision '%s'") % (path, rev) )
            exists = False
        
        return (content, exists)

def _split_path(fqpath):
    if '@' in fqpath:
        path, rev = fqpath.split('@', 1)
    else:
        path, rev = fqpath, None
    return path, rev
