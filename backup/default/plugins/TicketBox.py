"""
Display list of ticket numbers in a box on the right side of the page.
The purpose of this macro is show related tickets compactly.
You can specify ticket number or report number which would be expanded
as ticket numbers. Tickets will be displayed as sorted and uniq'ed.

Example:
{{{
[[TicketBox(#1,#7,#31)]]               ... list of tickets
[[TicketBox(1,7,31)]]                  ... '#' char can be omitted
[[TicketBox({1})]]                     ... expand report result as ticket list
[[TicketBox([report:1])]]              ... alternate format of report
[[TicketBox([report:9?name=val])]]     ... report with dynamic variable
[[TicketBox([query:status=new])]]]     ... query string
[[TicketBox({1},[query:status=new])]]  ... conbination
[[TicketBox(500pt,{1})]]               ... with box width as 50 point
[[TicketBox(200px,{1})]]               ... with box width as 200 pixel
[[TicketBox(25%,{1})]]                 ... with box width as 25%
[[TicketBox(width=25%,{1})]]           ... another style for with
[[TicketBox(float=left,{1})]]          ... place box on the left
[[TicketBox(background=yellow,{1})]]   ... set background color as yellow
[[TicketBox('Hello, world',#1,#2)]]    ... Specify title
[[TicketBox("Other Title",#1,#2)]]     ... likewise
[[TicketBox('%d tickets',#1,#2)]]      ... embed ticket count in title
[[TicketBox({1}, inline)]]             ... display the box as block element.
[[TicketBox({1}, summary)]]            ... display with summary per line
[[TicketBox({1}, summary=Titre)]]      ... specify field name of summary
[[TicketBox({1}, ticket=ID)]]          ... specify sql field name of ticket num.
[[TicketBox({1}, nosort)]]             ... display numbers without sort
[[TicketBox({1}, inline_total)]]       ... inline text of total number /wo box.
}}}

[wiki:TracReports#AdvancedReports:DynamicVariables Dynamic Variables] 
is supported for report. Variables can be specified like
{{{[report:9?PRIORITY=high&COMPONENT=ui]}}}. Of course, the special
variable '{{{$USER}}}' is available. The login name (or 'anonymous)
is used as $USER if not specified explicitly.
"""

## NOTE: CSS2 defines 'max-width' but it seems that only few browser
##       support it. So I use 'width'. Any idea?

import re
import string
from trac import __version__ as trac_ver
from trac.wiki.formatter import wiki_to_oneliner
from trac.ticket.report import ReportModule
from trac.ticket.model import Ticket
try:
    from trac.ticket.query import Query
    has_query = True
except:
    has_query = False

# plugin info
revision="$Rev$"
home_page="http://trac-hacks.org/wiki/TicketBoxMacro"

## Mock request object for trac 0.10.x or before
class MockReq(object):
    def __init__(self, hdf):
        self.hdf = dict()
        self.args = {}
        self.authname = hdf.getValue('trac.authname', 'anonymous')
        

# get trac version
verstr = re.compile('([0-9.]+).*').match(trac_ver).group(1)
ver = [int(x) for x in verstr.split(".")]

if ver <= [0, 10]:
    report_query_field = 'sql'
    call_args = dict(get_sql=[],
                     sql_sub_vars=['req', 'sql', 'dv'],
                     )
elif ver < [0, 11]:
    report_query_field = 'query'
    call_args = dict(get_sql=[],
                     sql_sub_vars=['req', 'sql', 'dv', 'db'],
                     )
else:
    report_query_field = 'query'
    call_args = dict(get_sql=['req'],
                     sql_sub_vars=['sql', 'dv', 'db'],
                     )

## default style values
default_styles = { "float": "right",
                   "color": None,
                   "background": "#f7f7f0",
                   "width": "25%",
                   "border-color": None,
                   }

args_pat = [r"#?(?P<tktnum>\d+)",
            r"{(?P<rptnum>\d+)}",
            r"\[report:(?P<rptnum2>\d+)(?P<dv>\?.*)?\]",
            r"\[query:(?P<query>[^\]]*)\]",
            r"(?P<width>\d+(pt|px|%))",
            r"(?P<title>'[^']*'|\"[^\"]*\")",
            r"(?P<keyword>[^,= ]+)(?: *= *(?P<kwarg>\"[^\"]*\"|'[^']*'|[^,]*))?",
            ]

# default name of fields
default_summary_field = 'summary'
default_ticket_field = 'ticket'

def uniq(x):
    """Remove duplicated items and return new list.
    If there are duplicated items, first appeared item remains and
    others are removed.

    >>> uniq([1,2,3,3,2,4,1])
    [1, 2, 3, 4]
    """
    y=[]
    for i in x:
        if not y.count(i):
            y.append(i)
    return y

def sqlstr(x):
    """Make quoted value string for SQL.
    Return single quotated string with escaping.
    Return itself if argument is not string,

    >>> sqlstr('abc')
    "'abc'"
    >>> sqlstr(u'abc')
    u"'abc'"
    >>> sqlstr("a'bc")
    "'a''bc'"
    >>> sqlstr(1)
    1
    """
    if isinstance(x, basestring):
        return "'%s'" % x.replace( "'","''" )
    else:
        return x

def unquote(s):
    """remove quotation chars on both side.

    >>> unquote('"abc"')
    'abc'
    >>> unquote("'abc'")
    'abc'
    >>> unquote('abc')
    'abc'
    """
    if 2 <= len(s) and s[0] + s[-1] in ['""', "''"]:
        return s[1:-1]
    else:
        return s

def parse(content):
    """Split macro argument string by comma considering quotation/escaping.

    >>> parse("1,2,3")
    ['1', '2', '3']
    >>> parse('"Hello, world", {1}')
    ['"Hello, world"', '{1}']
    >>> parse("key='a,b,c',key2=\\"d,e\\"")
    ["key='a,b,c'", 'key2="d,e"']
    """
    result = []
    args_re = re.compile("^(" + string.join(args_pat, "|") + ") *(,|$)")
    content = content.lstrip()
    while content:
        m = args_re.match(content)
        if m:
            item = m.group(1)
            content = content[m.end(0):].lstrip()
        else:
            item, content = [x.strip() for x in content.split(',', 1)]
        item = item.strip()
        result.append(item)
    return result

def call(func, vars):
    names = call_args[func.__name__]
    args = [vars[x] for x in names]
    # NOTE: ignore 3rd return value 'missing' in Trac 0.12.
    return func(*args)[:2]
    
def run0(req, env, db, content):
    args = parse(content or '')
    items = []
    summary = None
    ticket = default_ticket_field
    summaries = {}
    inline = False
    nosort = False
    inline_total = False
    title = "Tickets"
    styles = default_styles.copy()
    args_re = re.compile("^(?:" + string.join(args_pat, "|") + ")$")
    # process options first
    for arg in args:
        match = args_re.match(arg)
        if not match:
            env.log.debug('TicketBox: unknown arg: %s' % arg)
            continue
        elif match.group('title'):
            title = match.group('title')[1:-1]
        elif match.group('width'):
            styles['width'] = match.group('width')
        elif match.group('keyword'):
            kw = match.group('keyword').lower()
            kwarg = unquote(match.group('kwarg') or '')
            if kw == 'summary':
                summary = kwarg or default_summary_field
            elif kw == 'ticket':
                ticket = kwarg or default_ticket_field
            elif kw == 'inline':
                inline = True
            elif kw == 'nosort':
                nosort = True
            elif kw == 'nowrap':
                styles['white-space'] = 'nowrap'
            elif kw == 'inline_total':
                inline_total = True
            elif kw in styles and kwarg:
                styles[kw] = kwarg
    # pick up ticket numbers and report numbers
    for arg in args:
        sql = None
        params = []
        match = args_re.match(arg)
        id_name = ticket
        sidx = iidx = -1
        if not match:
            continue
        elif match.group('tktnum'):
            items.append(int(match.group('tktnum')))
        elif match.group('query'):
            if not has_query:
                raise Exception('You cannot use trac query for this version of trac')
            q = Query.from_string(env, match.group('query'))
            sql, params = call(q.get_sql, locals())
            id_name = 'id'
        elif match.group('rptnum') or match.group('rptnum2'):
            num = match.group('rptnum') or match.group('rptnum2')
            #env.log.debug('dynamic variables = %s' % dv)
            curs = db.cursor()
            try:
                curs.execute('SELECT %s FROM report WHERE id=%s'
                             % (report_query_field, num))
                rows = curs.fetchall()
                if len(rows) == 0:
                    raise Exception("No such report: %s"  % num)
                sql = rows[0][0]
            finally:
                curs.close()
            if sql:
                sql = sql.strip()
                if has_query and sql.lower().startswith("query:"):
                    if sql.lower().startswith('query:?'):
                        raise Exception('URL style of query string is not supported.')
                    q = Query.from_string(env, sql[6:])
                    sql, params = call(q.get_sql, locals())
                    id_name = 'id'
        if sql:
            if not params:
                # handle dynamic variables
                # NOTE: sql_sub_vars() takes different arguments in
                #       several trac versions.
                #       For 0.10 or before, arguments are (req, query, args)
                #       For 0.10.x, arguments are (req, query, args, db)
                #       For 0.11 or later, arguments are (query, args, db)
                dv = ReportModule(env).get_var_args(req)
                sql, params = call(ReportModule(env).sql_sub_vars, locals())
            try:
                #env.log.debug('sql = %s' % sql)
                curs = db.cursor()
                curs.execute(sql, params)
                rows = curs.fetchall()
                if rows:
                    descriptions = [desc[0] for desc in curs.description]
                    try:
                        iidx = descriptions.index(id_name)
                    except:
                        raise Exception('No such column for ticket number: %r'
                                        % id_name )
                    if summary:
                        try:
                            sidx = descriptions.index(summary)
                        except:
                            raise Exception('No such column for summary: %r'
                                            % summary)
                    for row in rows:
                        items.append(row[iidx])
                        if summary and 0 <= sidx:
                            summaries[row[iidx]] = row[sidx]
            finally:
                curs.close()

    if summary:
        # get summary text
        for id in items:
            if summaries.get(id):
                continue
            tkt = Ticket(env, tkt_id=id)
            if not tkt:
                continue
            summaries[id] = tkt['summary']
    
    items = uniq(items)
    if not nosort:
        items.sort()
    html = ''

    if inline_total:
        # return simple text of total count to be placed inline.
        return '<span class="ticketbox"><span id="total">%s</span></span>' \
            % len(items)
    
    if ver < [0, 11]:
        fargs = dict(db=db)
    else:
        fargs = dict(db=db, req=req)
    if summary:
        format = '%(summary)s (%(id)s)'
        sep = '<br/>'
    else:
        format = '%(id)s'
        sep = ', '
    lines = []
    for n in items:
        kwds = dict(id="#%d" % n)
        if summary:
            kwds['summary'] = summaries[n]
        lines.append(wiki_to_oneliner(format % kwds, env, **fargs))
    html = sep.join(lines)
    if html:
        try:
            title = title % len(items)  # process %d in title
        except:
            pass
        if inline:
            for key in ['float', 'width']:
                del styles[key]
        style = ';'.join(["%s:%s" % (k,v) for k,v in styles.items() if v])
        return '<fieldset class="ticketbox" style="%s"><legend>%s</legend>%s</fieldset>' % \
               (style, title, html)
    else:
        return ''

def run(req, env, content):
    
    db = env.get_db_cnx()
    try:
        return run0(req, env, db, content)
    finally:
        if db and not hasattr(env, 'get_cnx_pool'):
            # for old version which does not have db connection pool,
            # we should close db.
            db.close()

# single file macro I/F (not plugin, for 0.10.x or before)
def execute(hdf, txt, env):
    req = MockReq(hdf)
    return run(req, env, txt)


try:
    from trac.wiki.macros import WikiMacroBase

    class TicketBoxMacro(WikiMacroBase):
        __doc__ = __doc__
        
        # plugin macro I/F for trac 0.10.x
        def render_macro(self, req, name, content):
            db = env.get_db_cnx()
            try:
                run(req, self.env, db, content)
            finally:
                if db and not hasattr(env, 'get_cnx_pool'):
                    # for old version which does not have db connection pool,
                    # we should close db.
                    db.close()

        # plugin macro I/F for trac 0.11 or later
        def expand_macro(self, formatter, name, args):
            """Return some output that will be displayed in the Wiki content.

            `name` is the actual name of the macro (no surprise, here it'll be
            `'HelloWorld'`),
            `args` is the text enclosed in parenthesis at the call of the macro.
              Note that if there are ''no'' parenthesis (like in, e.g.
              [[HelloWorld]]), then `args` is `None`.
            """
            if 'TICKET_VIEW' not in formatter.perm('ticket'):
                return '' # no permission, no display
            return run(formatter.req, formatter.env, args)
except ImportError:
    # trac 0.9
    pass

if __name__ == '__main__':
    import sys, doctest
    doctest.testmod(sys.modules[__name__])
