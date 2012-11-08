# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re
from trac.core import *
from trac.resource import Resource
from tractags.query import *
from trac.perm import IPermissionRequestor, PermissionError
from trac.web.chrome import add_warning
from trac.wiki.model import WikiPage
from trac.util.text import to_unicode
from trac.util.compat import set, groupby
from trac.resource import IResourceManager, get_resource_url, \
    get_resource_description
from genshi import Markup
from genshi.builder import tag as tag_


class InvalidTagRealm(TracError):
    pass


class ITagProvider(Interface):
    def get_taggable_realm():
        """Return the realm this provider supports tags on."""

    def get_tagged_resources(req, tags=None):
        """Return a sequence of resources and *all* their tags.

        :param tags: If provided, return only those resources with the given
                     tags.

        :rtype: Sequence of (resource, tags) tuples.
        """

    def get_resource_tags(req, resource):
        """Get tags for a Resource object."""

    def set_resource_tags(req, resource, tags):
        """Set tags for a resource."""

    def remove_resource_tags(req, resource):
        """Remove all tags from a resource."""


class DefaultTagProvider(Component):
    """An abstract base tag provider that stores tags in the database.

    Use this if you need storage for your tags. Simply set the class variable
    `realm` and optionally `check_permission()`.

    See tractags.wiki.WikiTagProvider for an example.
    """

    implements(ITagProvider)

    abstract = True

    # Resource realm this provider manages tags for. Set this.
    realm = None

    # Public methods
    def check_permission(self, perm, operation):
        """Delegate function for checking permissions.

        Override to implement custom permissions. Defaults to TAGS_VIEW and
        TAGS_MODIFY.
        """
        map = {'view': 'TAGS_VIEW', 'modify': 'TAGS_MODIFY'}
        return map[operation] in perm('tag')

    # ITagProvider methods
    def get_taggable_realm(self):
        return self.realm

    def get_tagged_resources(self, req, tags):
        if not self.check_permission(req.perm, 'view'):
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        args = [self.realm]
        sql = 'SELECT DISTINCT name FROM tags WHERE tagspace=%s'
        if tags:
            sql += ' AND tags.tag IN (%s)' % ', '.join(['%s' for t in tags])
            args += tags
        sql += ' ORDER by name'
        cursor.execute(sql, args)

        resources = {}
        for name, in cursor:
            resource = Resource(self.realm, name)
            if self.check_permission(req.perm(resource), 'view'):
                resources[resource.id] = resource

        if not resources:
          return

        args = [self.realm] + list(resources)
        # XXX Is this going to be excruciatingly slow?
        sql = 'SELECT DISTINCT name, tag FROM tags WHERE tagspace=%%s AND ' \
              'name IN (%s) ORDER BY name' % ', '.join(['%s' for _ in resources])
        cursor.execute(sql, args)

        for name, tags in groupby(cursor, lambda row: row[0]):
            resource = resources[name]
            yield resource, set([tag[1] for tag in tags])

    def get_resource_tags(self, req, resource):
        assert resource.realm == self.realm
        if not self.check_permission(req.perm(resource), 'view'):
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT tag FROM tags WHERE tagspace=%s AND name=%s',
                       (self.realm, resource.id))
        for row in cursor:
            yield row[0]

    def set_resource_tags(self, req, resource, tags):
        assert resource.realm == self.realm
        if not self.check_permission(req.perm(resource), 'modify'):
            raise PermissionError(resource=resource, env=self.env)
        db = self.env.get_db_cnx()
        try:
            cursor = db.cursor()
            cursor.execute('DELETE FROM tags WHERE tagspace=%s AND name=%s',
                           (self.realm, resource.id))
            for tag in tags:
                cursor.execute('INSERT INTO tags (tagspace, name, tag) '
                               'VALUES (%s, %s, %s)',
                               (self.realm, resource.id, tag))
            db.commit()
        except:
            db.rollback()
            raise

    def remove_resource_tags(self, req, resource):
        assert resource.realm == self.realm
        if not self.check_permission(req.perm(resource), 'modify'):
            raise PermissionError(resource=resource, env=self.env)
        db = self.env.get_db_cnx()
        try:
            cursor = db.cursor()
            cursor.execute('DELETE FROM tags WHERE tagspace=%s AND name=%s',
                           (self.realm, resource.id))
            db.commit()
        except:
            db.rollback()
            raise


class TagSystem(Component):
    """Tagging system for Trac."""

    implements(IPermissionRequestor, IResourceManager)

    tag_providers = ExtensionPoint(ITagProvider)

    # Internal variables
    _tag_split = re.compile('[,\s]+')
    _realm_provider_map = None

    # Public methods
    def query(self, req, query='', attribute_handlers=None):
        """Return a sequence of (resource, tags) tuples matching a query.

        Query syntax is described in tractags.query.

        :param attribute_handlers: Register additional query attribute
                                   handlers. See Query documentation for more
                                   information.
        """
        def realm_handler(_, node, context):
            return query.match(node, [context.realm])

        all_attribute_handlers = {
            'realm': realm_handler,
            }
        all_attribute_handlers.update(attribute_handlers or {})
        if re.search(r'(expression|tagspace|tagspaces|operation|showheadings'
                     '|expression)=', query):
            message = Markup('You seem to be using an old Tag query. '
                             'Try using the <a href="%s">new syntax</a> in your '
                             '<strong>ListTagged</strong> macro.',
                             req.href('tags'))
            add_warning(req, message)
        query = Query(query, attribute_handlers=all_attribute_handlers)

        query_tags = set(query.terms())
        for provider in self.tag_providers:
            for resource, tags in provider.get_tagged_resources(req, query_tags):
                if query(tags, context=resource):
                    yield resource, tags

    def get_tags(self, req, resource):
        """Get tags for resource."""
        return set(self._get_provider(resource.realm) \
                   .get_resource_tags(req, resource))

    def set_tags(self, req, resource, tags):
        """Set tags on a resource.

        Existing tags are replaced.
        """
        return self._get_provider(resource.realm) \
            .set_resource_tags(req, resource, set(tags))

    def add_tags(self, req, resource, tags):
        """Add to existing tags on a resource."""
        tags = set(tags)
        tags.update(self.get_tags(req, resource))
        self.set_tags(req, resource, tags)

    def delete_tags(self, req, resource, tags=None):
        """Delete tags on a resource.

        If tags is None, remove all tags on the resource.
        """
        provider = self._get_provider(resource.realm)
        if tags is None:
            provider.remove_resource_tags(req, resource)
        else:
            tags = set(tags)
            current_tags = provider.get_resource_tags(req, resource)
            current_tags.remove(tags)
            provider.set_resource_tags(req, resource, tags)

    def split_into_tags(self, text):
        """Split plain text into tags."""
        return set([t.strip() for t in self._tag_split.split(text) if t.strip()])

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['TAGS_VIEW', 'TAGS_MODIFY']

    # IResourceManager methods
    def get_resource_realms(self):
        yield 'tag'

    def get_resource_url(self, resource, href, **kwargs):
        page = WikiPage(self.env, resource.id)
        if page.exists:
            return get_resource_url(self.env, page.resource, href, **kwargs)
        return href("tags/'%s'" % unicode(resource.id).replace("'", "\\'"))

    def get_resource_description(self, resource, format='default', context=None,
                                 **kwargs):
        page = WikiPage(self.env, resource.id)
        if page.exists:
            return get_resource_description(self.env, page.resource, format,
                                            **kwargs)
        rid = to_unicode(resource.id)
        if format in ('compact', 'default'):
            return rid
        else:
            return u'tag:%s' % rid

    # Internal methods
    def _populate_provider_map(self):
        if self._realm_provider_map is None:
            self._realm_provider_map = {}
            for provider in self.tag_providers:
                self._realm_provider_map[provider.get_taggable_realm()] = \
                    provider

    def _get_provider(self, realm):
        self._populate_provider_map()
        try:
            return self._realm_provider_map[realm]
        except KeyError:
            raise InvalidTagRealm('Tags are not supported on the "%s" realm' % realm)
