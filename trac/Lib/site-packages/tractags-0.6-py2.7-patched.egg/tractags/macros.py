# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.resource import Resource, get_resource_url, render_resource_link
from trac.wiki.macros import WikiMacroBase
from trac.util.compat import sorted, set
from tractags.api import TagSystem
from genshi.builder import tag as builder


def render_cloud(env, req, cloud, renderer=None):
    """Render a tag cloud

    :cloud: Dictionary of {object: count} representing the cloud.
    :param renderer: A callable with signature (tag, count, percent) used to
                     render the cloud objects.
    """
    min_px = 10.0
    max_px = 30.0
    scale = 1.0

    if renderer is None:
        def default_renderer(tag, count, percent):
            href = get_resource_url(env, Resource('tag', tag), req.href)
            return builder.a(tag, rel='tag', title='%i' % count, href=href,
                             style='font-size: %ipx' %
                                   int(min_px + percent * (max_px - min_px)))
        renderer = default_renderer

    # A LUT from count to n/len(cloud)
    size_lut = dict([(c, float(i)) for i, c in
                     enumerate(sorted(set([r for r in cloud.values()])))])
    if size_lut:
        scale = 1.0 / len(size_lut)

    ul = builder.ul(class_='tagcloud')
    last = len(cloud) - 1
    for i, (tag, count) in enumerate(sorted(cloud.iteritems())):
        percent = size_lut[count] * scale
        li = builder.li(renderer(tag, count, percent))
        if i == last:
            li(class_='last')
        li()
        ul(li)
    return ul


class TagCloudMacro(WikiMacroBase):
    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_result = TagSystem(self.env).query(req, content)
        all_tags = {}
        # Find tag counts
        for resource, tags in query_result:
            for tag in tags:
                try:
                    all_tags[tag] += 1
                except KeyError:
                    all_tags[tag] = 1
        return render_cloud(self.env, req, all_tags)



class ListTaggedMacro(WikiMacroBase):
    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_result = TagSystem(self.env).query(req, content)

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        ul = builder.ul(class_='taglist')
        # Beware: Resources can be Unicode strings.
        for resource, tags in sorted(query_result, key=lambda r: r[0].id):
            tags = sorted(tags)
            if tags:
                rendered_tags = [
                    link(resource('tag', tag))
                    for tag in tags
                    ]
                li = builder.li(link(resource), ' (', rendered_tags[0],
                                [(' ', tag) for tag in rendered_tags[1:]],
                                ')')
            else:
                li = builder.li(link(resource))
            ul(li, '\n')
        return ul
