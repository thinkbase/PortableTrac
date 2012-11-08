# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Edgewall Software
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

from datetime import datetime
import imp
import inspect
import os
import re
from StringIO import StringIO

from genshi.builder import Element, tag
from genshi.core import Markup

from trac.core import *
from trac.resource import Resource, get_resource_url, get_resource_summary
from trac.util.datefmt import format_date, utc
from trac.util.compat import sorted, groupby, any, set
from trac.util.html import escape
from trac.util.text import unquote, to_unicode
from trac.util.translation import _
from trac.wiki.api import IWikiMacroProvider, WikiSystem, parse_args
from trac.wiki.formatter import format_to_html, format_to_oneliner, \
                                extract_link, OutlineFormatter
from trac.wiki.model import WikiPage
from trac.web.chrome import add_stylesheet

from trac.wiki.macros import TracGuideTocMacro

class ZhTracGuideTocMacro(TracGuideTocMacro):
    """
    This macro shows a quick and dirty way to make a table-of-contents
    for a set of wiki pages.
    """

    TOC = [('ZhTracGuide',                    u'索引'),
           ('ZhTracInstall',                  u'安装'),
           ('ZhTracInterfaceCustomization',   u'自定义'),
           ('ZhTracPlugins',                  u'插件'),
           ('ZhTracUpgrade',                  u'升级'),
           ('ZhTracIni',                      u'配置'),
           ('ZhTracAdmin',                    u'管理'),
           ('ZhTracBackup',                   u'恢复'),
           ('ZhTracLogging',                  u'日志'),
           ('ZhTracPermissions' ,             u'权限'),
           ('ZhTracWiki',                     u'Wiki帮助'),
           ('ZhWikiFormatting',               u'Wiki格式'),
           ('ZhTracTimeline',                 u'时间轴'),
           ('ZhTracBrowser',                  u'代码库'),
           ('TracRevisionLog',                u'修订日志'),
           ('ZhTracChangeset',                u'变量集'),
           ('ZhTracTickets',                  u'传票'),
           ('TracWorkflow',                   u'工作流'),
           ('ZhTracRoadmap',                  u'路线图'),
           ('ZhTracQuery',                    u'传票查询'),
           ('ZhTracReports',                  u'报表'),
           ('ZhTracRss',                      u'RSS支持'),
           ('ZhTracNotification',             u'通知')
           ]