# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""
A generalised query parser and matcher.
"""

import re
from trac.core import TracError


__all__ = ['Query', 'InvalidQuery']


class InvalidQuery(TracError):
    """Raised when a query is invalid."""


class QueryNode(object):
    """A query parse node.

    >>> QueryNode(QueryNode.TERM, 'one')
    ("one")
    >>> QueryNode(QueryNode.AND,
    ...     left=QueryNode(QueryNode.TERM, 'one'),
    ...     right=QueryNode(QueryNode.TERM, 'two'))
    (and
      ("one")
      ("two"))
    >>> QueryNode(QueryNode.NOT, left=QueryNode(QueryNode.TERM, 'one'))
    (not
      ("one")
      nil)
    """


    # TODO Separate lexer and parser identifiers
    NULL = 0
    TERM = 1
    NOT = 2
    AND = 3
    OR = 4
    ATTR = 5
    BEGINSUB = 6
    ENDSUB = 7

    __slots__ = ('type', 'value', 'left', 'right')

    _type_map = {None: 'null', NULL: 'null', TERM: 'term', NOT: 'not', AND:
                 'and', OR: 'or', ATTR: 'attr'}

    def __init__(self, type, value=None, left=None, right=None):
        self.type = type
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self):
        def show(node, depth=0):
            if node.type == QueryNode.TERM:
                text = u'%s("%s"' % (u'  ' * depth, node.value)
            elif node.type == QueryNode.ATTR:
                text = u'%s(attr' % (u'  ' * depth,)
            else:
                text = u'%s(%s%s' % (u'  ' * depth, self._type_map[node.type],
                                    node.value and u' "%s"' % (node.value,) or
                                    u'')
            if node.left or node.right:
                text += u'\n'
                if node.left:
                    text += show(node.left, depth + 1)
                else:
                    text += u'%snil' % (u'  ' * (depth + 1))
                text += u'\n'
                if node.right:
                    text += show(node.right, depth + 1)
                else:
                    text += u'%snil' % (u'  ' * (depth + 1))
            text += u')'
            return text
        return show(self).encode('utf-8')


class Query(QueryNode):
    """Query parser.

    Converts a simple query language into a parse tree which Indexers can then
    convert into their own implementation-specific representation.

    The query language is in the following form:

        <term> <term>     Document must contain all of these terms.
        "some term"       Return documents matching this exact phrase.
        -<term>           Exclude documents containing this term.
        <term> or <term>  Return documents matching either term.

        <attr>:<term>     Customisable attribute matching.

    eg.

    >>> Query('lettuce tomato -cheese')
    (and
      ("lettuce")
      (and
        ("tomato")
        (not
          ("cheese")
          nil)))

    >>> Query('"mint slices" -timtams')
    (and
      ("mint slices")
      (not
        ("timtams")
        nil))

    >>> Query('"brie cheese" or "camembert cheese"')
    (or
      ("brie cheese")
      ("camembert cheese"))

    >>> Query('type:(soft or hard) (brie or camembert or cheddar)')
    (and
      (attr
        ("type")
        (or
          ("soft")
          ("hard")))
      (or
        ("brie")
        (or
          ("camembert")
          ("cheddar"))))
    """

    _tokenise_re = re.compile(r"""
        (?P<not>-)|
        (?P<or>or)|
        \"(?P<dquote>(?:\\.|[^\"])*)\"|
        '(?P<squote>(?:\\.|[^'])*)'|
        (?P<startsub>\()|
        (?P<endsub>\))|
        (?P<attr>:)|
        (?P<term>[^:()"'\s]+)""", re.UNICODE | re.IGNORECASE | re.VERBOSE)

    _group_map = {'dquote': QueryNode.TERM, 'squote': QueryNode.TERM,
                  'term': QueryNode.TERM, 'not': QueryNode.NOT,
                  'or': QueryNode.OR, 'attr': QueryNode.ATTR,
                  'startsub': QueryNode.BEGINSUB, 'endsub': QueryNode.ENDSUB}

    def __init__(self, phrase, attribute_handlers=None):
        """Construct a new Query.

        Attribute handlers are callables with the signature
        (attribute_name, node, context) where node is the QueryNode
        representing the RHS of the attribute expression and context is a custom
        parameter passed to Query.__call__().

        :param phrase: Query phrase.
        :param attribute_handlers: A dictionary of attribute handlers.
        """
        QueryNode.__init__(self, None)
        tokens = self._tokenise(phrase)
        root = self.parse(tokens)
        self.phrase = phrase
        self._compiled = None
        self.attribute_handlers = attribute_handlers or {}
        self.attribute_handlers.setdefault('*', self._invalid_handler)
        if root:
            # Make ourselves into the root node
            for k in self.__slots__:
                setattr(self, k, getattr(root, k))

    def parse(self, tokens):
        left = self.parse_unary(tokens)
        while tokens:
            if tokens[0][0] == QueryNode.ENDSUB:
                return left
            if tokens[0][0] == QueryNode.OR:
                tokens.pop(0)
                return QueryNode(QueryNode.OR, left=left,
                                 right=self.parse(tokens))
            elif tokens[0][0] == QueryNode.ATTR:
                tokens.pop(0)
                if left.type is not QueryNode.TERM:
                    raise InvalidQuery('Attribute must be a word')
                left = QueryNode(QueryNode.ATTR, left=left,
                                 right=self.parse_unary(tokens))
            else:
                return QueryNode(QueryNode.AND, left=left,
                                 right=self.parse(tokens))
        return left

    def parse_unary(self, tokens):
        """Parse a unary operator. Currently only NOT.

        >>> q = Query('')
        >>> q.parse_unary(q._tokenise('-foo'))
        (not
          ("foo")
          nil)
        """
        if not tokens:
            return None
        if tokens[0][0] == QueryNode.BEGINSUB:
            tokens.pop(0)
            if tokens[0][0] == QueryNode.ENDSUB:
                return None
            node = self.parse(tokens)
            if not tokens or tokens[0][0] != QueryNode.ENDSUB:
                raise InvalidQuery('Expected ) at end of sub-expression')
            tokens.pop(0)
            return node
        if tokens[0][0] == QueryNode.NOT:
            tokens.pop(0)
            return QueryNode(QueryNode.NOT, left=self.parse_terminal(tokens))
        return self.parse_terminal(tokens)

    def parse_terminal(self, tokens):
        """Parse a terminal token.

        >>> q = Query('')
        >>> q.parse_terminal(q._tokenise('foo'))
        ("foo")
        """

        if not tokens:
            raise InvalidQuery('Unexpected end of string')
        if tokens[0][0] in (QueryNode.TERM, QueryNode.OR):
            token = tokens.pop(0)
            return QueryNode(QueryNode.TERM, value=token[1])
        raise InvalidQuery('Expected terminal, got "%s"' % tokens[0][1])

    def terms(self, exclude_not=True):
        """A generator returning the terms contained in the Query.

        >>> q = Query('foo -bar or baz')
        >>> list(q.terms())
        ['foo', 'baz']
        >>> list(q.terms(exclude_not=False))
        ['foo', 'bar', 'baz']
        """
        def _convert(node):
            if not node:
                return
            if node.type == node.TERM:
                yield node.value
            elif node.type == node.ATTR:
                return
            elif node.type == node.NOT and exclude_not:
                return
            else:
                for child in _convert(node.left):
                    yield child
                for child in _convert(node.right):
                    yield child

        return _convert(self)

    def __call__(self, terms, context=None):
        """Match the query against a sequence of terms."""
        return self.match(self, terms, context)

    def match(self, node, terms, context=None):
        """Match a node against a set of terms."""
        def _match(node):
            if not node or node.type == node.NULL:
                return True
            elif node.type == node.TERM:
                return node.value in terms
            elif node.type == node.AND:
                return _match(node.left) and _match(node.right)
            elif node.type == node.OR:
                return _match(node.left) or _match(node.right)
            elif node.type == node.NOT:
                return not _match(node.left)
            elif node.type == node.ATTR:
                return self.attribute_handlers.get(
                    node.left.value,
                    self.attribute_handlers['*']
                    )(node.left.value, node.right, context)
            elif node.type is None:
                return True
            else:
                raise NotImplementedError(node.type)
        return _match(node)


    def _compile_call(self, text, attribute_handlers=None):
        import compiler
        import types
        from compiler import ast, misc, pycodegen

        raise NotImplementedError('Incomplete')

        # TODO Make this work?
        def _generate(node):
            if node.type == node.TERM:
                return ast.Compare(ast.Const(node.value),
                                   [('in', ast.Name('text'))])
            elif node.type == node.AND:
                return ast.And([_generate(node.left), _generate(node.right)])
            elif node.type == node.OR:
                return ast.Or([_generate(node.left), _generate(node.right)])
            elif node.type == node.NOT:
                return ast.Not(_generate(node.left))
            elif node.type == node.ATTR:
                raise NotImplementedError

        qast = ast.Expression(ast.Lambda(['self', 'text',
                                          'attribute_handlers'],
                                         [ast.Name('None')],
                                         0,
                                         _generate(self)))
        misc.set_filename('<%s compiled query>' % self.__class__.__name__,
                          qast)
        gen = pycodegen.ExpressionCodeGenerator(qast)
        self.__call__ = types.MethodType(eval(gen.getCode()), self, Query)
        return self.__call__(text)

    def as_string(self, and_=' AND ', or_=' OR ', not_='NOT '):
        """Convert Query to a boolean expression. Useful for indexers with
        "typical" boolean query syntaxes.

        eg. "term AND term OR term AND NOT term"

        The expanded operators can be customised for syntactical variations.

        >>> Query('foo bar').as_string()
        'foo AND bar'
        >>> Query('foo bar or baz').as_string()
        'foo AND bar OR baz'
        >>> Query('foo -bar or baz').as_string()
        'foo AND NOT bar OR baz'
        """
        def _convert(node):
            if not node or node.type == node.NULL:
                return ''
            if node.type == node.AND:
                return '%s%s%s' % (_convert(node.left), and_,
                                   _convert(node.right))
            elif node.type == node.OR:
                return '%s%s%s' % (_convert(node.left), or_,
                                   _convert(node.right))
            elif node.type == node.NOT:
                return '%s%s' % (not_, _convert(node.left))
            elif node.type == node.TERM:
                return node.value
            elif node.type == node.ATTR:
                return '%s:%s' % (_convert(node.left), _convert(node.right))
            else:
                raise NotImplementedError
        return _convert(self)

    def reduce(self, reduce):
        """Pass each TERM node through `Reducer`."""
        def _reduce(node):
            if not node:
                return
            if node.type == node.TERM:
                node.value = reduce(node.value, unique=False, split=False)
            _reduce(node.left)
            _reduce(node.right)
        _reduce(self)

    # Internal methods
    def _tokenise(self, phrase):
        """Tokenise a phrase string.

        >>> q = Query('')
        >>> q._tokenise('one')
        [(1, 'one')]
        >>> q._tokenise('one two')
        [(1, 'one'), (1, 'two')]
        >>> q._tokenise('one or two')
        [(1, 'one'), (4, 'or'), (1, 'two')]
        >>> q._tokenise('"one two"')
        [(1, 'one two')]
        >>> q._tokenise("'one two'")
        [(1, 'one two')]
        >>> q._tokenise('-one')
        [(2, '-'), (1, 'one')]
        """
        tokens = [(self._group_map[token.lastgroup], token.group(token.lastindex))
                  for token in self._tokenise_re.finditer(phrase)]
        return tokens

    def _invalid_handler(self, name, node, context):
        raise InvalidQuery('Invalid attribute "%s"' % name)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
