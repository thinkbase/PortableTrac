"""
$Id$
$HeadURL$

Copyright (c) 2008 Malcolm Smith. All rights reserved.

Module documentation goes here.

Usage: gantt [options] < inputfile

Options:
    -h / --help
        Print this message and exit.
    - o / --outfile=<filename>
        send output png to this filename 
    - v / --verbose
        use verbose output
    --infile=<filename>
        use filename for input
     


"""

__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.2'


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import hashlib
import os
import sys
import re
import inspect

import getopt
from dateutil.relativedelta import *
from datetime import *
import yaml
import Image, ImageDraw, ImageColor, ImageFont

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.web.main import IRequestHandler
from trac.util import escape
from trac.wiki.formatter import wiki_to_oneliner
from trac import mimeview


_TRUE_VALUES = ('yes', 'true', 'on', 'aye', '1', 1, True)


class GanttMacro(Component):
    """
    GanttMacro (http://trac-hacks.org/wiki/GanttPlugin) provides
    a plugin for Trac to render gantt charts within a Trac wiki page.
    """
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)

    # Available formats and processors, default first (dot/png)
    processors = ['std']
    bitmap_formats = ['png', 'jpg', 'gif']
    vector_formats = []
    formats = bitmap_formats + vector_formats 
    cmd_paths = {}

    #def __init__(self):
        #self.log.info('version: %s - id: %s' % (__version__, str(__id__)))
        #self.log.info('processors: %s' % str(GanttMacro.processors))
        #self.log.info('formats: %s' % str(GanttMacro.formats))


    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        self.load_config()
        for p in ['.' + p for p in GanttMacro.processors] + ['']: 
            for f in ['/' + f for f in GanttMacro.formats] + ['']:
                yield 'gantt%s%s' % (p, f)


    def get_macro_description(self, name):
        """
        Return a plain text description of the macro with the
        specified name. 
        """
        if name == 'gantt':
            return inspect.getdoc(GanttMacro)
        else:
            return None


    def expand_macro(self, formatter, name, content):
        """Called by the formatter when rendering the parsed wiki text. (since 0.11)

	Should be used instead of render_macro to return the HTML output of the macro.

        req - can be retrieved via formatter.context.req
        
        name - Wiki macro command that resulted in this method being
               called. In this case, it should be 'gantt', followed
               (or not) by the processor name, then by an output
               format, as following: gantt.<processor>/<format>

               Valid processor names are: std  the default is std
               
               Valid output formats are: jpg, png, gif
               The default is the value specified in the out_format
               configuration parameter. If out_format is not specified
               in the configuration, then the default is png.

               examples: gantt.std/png   -> std    png
                         gantt/jpg       -> std    jpg

        content - The text the user entered for the macro to process.
        """

        #self.log.debug('dir(req): %s' % str(dir(req)))
        #if hasattr(req, 'args'):
        #    self.log.debug('req.args: %s' % str(req.args))
        #else:
        #    self.log.debug('req.args attribute does not exist')
        #if hasattr(req, 'base_url'):
        #    self.log.debug('req.base_url: %s' % str(req.base_url))
        #else:
        #    self.log.debug('req.base_url attribute does not exist')

        # check and load the configuration
        trouble, msg = self.load_config()
        if trouble:
            return msg.getvalue()

        buf = StringIO()


        ## Extract processor and format from name
        l_proc = l_out_format = ''

        # first try with the RegExp engine
        try: 
            m = re.match('gantt\.?([a-z]*)\/?([a-z]*)', name)
            (l_proc, l_out_format) = m.group(1, 2)

        # or use the string.split method
        except:
            (d_sp, s_sp) = (name.split('.'), name.split('/'))
            if len(d_sp) > 1:
                s_sp = d_sp[1].split('/')
                if len(s_sp) > 1:
                    l_out_format = s_sp[1]
                l_proc = s_sp[0]
            elif len(s_sp) > 1:
                l_out_format = s_sp[1]
            
        # assign default values, if instance ones are empty
        self.out_format = (self.out_format, l_out_format)[bool(len(l_out_format))]
        self.processor  = (self.processor,  l_proc)      [bool(len(l_proc))]


        if self.processor in GanttMacro.processors:
            proc_cmd = ""
        else:
            self.log.error('render_macro: requested processor (%s) not found.' % self.processor)
            buf.write('<p>Gantt macro processor error: requested processor <b>(%s)</b> not found.</p>' % self.processor)
            return buf.getvalue()
           
        if self.out_format not in GanttMacro.formats:
            self.log.error('render_macro: requested format (%s) not found.' % self.out_format)
            buf.write('<p>Gantt macro processor error: requested format <b>(%s)</b> not valid.</p>' % self.out_format)
            return buf.getvalue()

        encoding = 'utf-8'
        if type(content) == type(u''):
            content  = content.encode(encoding)
            sha_text = self.processor.encode(encoding) + content
        else:
            sha_text = self.processor + content

        sha_key  = hashlib.sha1(sha_text).hexdigest()
        img_name = '%s.%s.%s' % (sha_key, self.processor, self.out_format) # cache: hash.<dot>.<png>
        img_path = os.path.join(self.cache_dir, img_name)
        map_name = '%s.%s.map' % (sha_key, self.processor)       # cache: hash.<dot>.map
        map_path = os.path.join(self.cache_dir, map_name)

        # Check for URL="" presence in graph code
        URL_in_graph = 'URL=' in content

        # Create image if not in cache
        if not os.path.exists(img_path):
            self.clean_cache()

        #self.log.debug('render_macro.URL_in_graph: %s' % str(URL_in_graph))
        if URL_in_graph: # translate wiki TracLinks in URL
            content = re.sub(r'URL\s*:\s*"(.*?)"', self.expand_wiki_links, content.decode(encoding)).encode(encoding)
        try :
            data = yaml.load(content)
            mstart,mend = self.process_dates(data)
            self.draw_chart(data,mstart,mend,img_path,80,20,False)
        except yaml.YAMLError,  detail :
            msg = "Data Loading Error: "
            if hasattr(detail, 'message'):
                msg = msg + detail.message	    
            if hasattr(detail, 'problem_mark'):
                mark = detail.problem_mark
                msg = msg + "<br />Error position: (%s:%s)" % (mark.line+1, mark.column+1)		
            return self.show_err(msg).getvalue()
            
        buf.write('<img src="%s/gantt/%s"/>' % (formatter.context.req.base_url, img_name))
        return buf.getvalue()



    def expand_wiki_links(self, match):
        wiki_url = match.groups()[0]                     # TracLink ([1], source:file/, ...)
        html_url = wiki_to_oneliner(wiki_url, self.env)  # <a href="http://someurl">...</a>
        href     = re.search('href="(.*?)"', html_url)   # http://someurl
        url      = href and href.groups()[0] or html_url
        if self.out_format == 'svg':
            format = 'URL="javascript:window.parent.location.href=\'%s\'"'
        else:
            format = 'URL="%s"'
        return format % url


    def load_config(self):
        """Load the gantt trac.ini configuration into object instance variables."""
        buf        = StringIO()
        trouble    = False
        self.exe_suffix = ''
        if sys.platform == 'win32':
            self.exe_suffix = '.exe'

        if 'gantt' not in self.config.sections():
            msg = 'The <b>gantt</b> section was not found in the trac configuration file.'
            buf = self.show_err(msg)
            trouble = True
        else:
            # check for the cache_dir entry
            self.cache_dir = self.config.get('gantt', 'cache_dir')
            if not self.cache_dir:
                msg = 'The <b>gantt</b> section is missing the <b>cache_dir</b> field.'
                buf = self.show_err(msg)
                trouble = True
            else:
                if not os.path.exists(self.cache_dir):
                    msg = 'The <b>cache_dir</b> is set to <b>%s</b> but that path does not exist.' % self.cache_dir
                    buf = self.show_err(msg)
                    trouble = True
                #self.log.debug('self.cache_dir: %s' % self.cache_dir)


            #Get optional configuration parameters from trac.ini.

            # check for the default processor - processor
            self.processor = self.config.get('gantt', 'processor', GanttMacro.processors[0])
            #self.log.debug('self.processor: %s' % self.processor)

            # check for the default output format - out_format
            self.out_format = self.config.get('gantt', 'out_format', GanttMacro.formats[0])
            #self.log.debug('self.out_format: %s' % self.out_format)

            # check if we should run the cache manager
            self.cache_manager = self.boolean(self.config.get('gantt', 'cache_manager', False))
            if self.cache_manager:
                self.cache_max_size  = int(self.config.get('gantt', 'cache_max_size',  10000000))
                self.cache_min_size  = int(self.config.get('gantt', 'cache_min_size',  5000000))
                self.cache_max_count = int(self.config.get('gantt', 'cache_max_count', 2000))
                self.cache_min_count = int(self.config.get('gantt', 'cache_min_count', 1500))

                #self.log.debug('self.cache_max_count: %d' % self.cache_max_count)
                #self.log.debug('self.cache_min_count: %d' % self.cache_min_count)
                #self.log.debug('self.cache_max_size: %d'  % self.cache_max_size)
                #self.log.debug('self.cache_min_size: %d'  % self.cache_min_size)

        # setup mimetypes to support the IHTMLPreviewRenderer interface
        if 'gantt' not in MIME_MAP:
            MIME_MAP['gantt'] = 'application/gantt'
        for processor in GanttMacro.processors:
            if processor not in MIME_MAP:
                MIME_MAP[processor] = 'application/gantt'

        return trouble, buf


    def show_err(self, msg):
        """Display msg in an error box, using Trac style."""
        buf = StringIO()
        buf.write('<div id="content" class="error"><div class="message"> \n\
                   <strong>Gantt macro processor has detected an error. Please fix the problem before continuing.</strong> \n\
                   <pre>%s</pre> \n\
                   </div></div>' % escape(msg))
        self.log.error(msg)
        return buf


    def clean_cache(self):
        """
        The cache manager (clean_cache) is an attempt at keeping the
        cache directory under control. When the cache manager
        determines that it should clean up the cache, it will delete
        files based on the file access time. The files that were least
        accessed will be deleted first.

        The gantt section of the trac configuration file should
        have an entry called cache_manager to enable the cache
        cleaning code. If it does, then the cache_max_size,
        cache_min_size, cache_max_count and cache_min_count entries
        must also be there.
        """

        if self.cache_manager:

            # os.stat gives back a tuple with: st_mode(0), st_ino(1),
            # st_dev(2), st_nlink(3), st_uid(4), st_gid(5),
            # st_size(6), st_atime(7), st_mtime(8), st_ctime(9)

            entry_list = {}
            atime_list = {}
            size_list = {}
            count = 0
            size = 0

            for name in os.listdir(self.cache_dir):
                #self.log.debug('clean_cache.entry: %s' % name)
                entry_list[name] = os.stat(os.path.join(self.cache_dir, name))

                atime_list.setdefault(entry_list[name][7], []).append(name)
                count = count + 1

                size_list.setdefault(entry_list[name][6], []).append(name)
                size = size + entry_list[name][6]

            atime_keys = atime_list.keys()
            atime_keys.sort()

            #self.log.debug('clean_cache.atime_keys: %s' % atime_keys)
            #self.log.debug('clean_cache.count: %d' % count)
            #self.log.debug('clean_cache.size: %d' % size)
        
            # In the spirit of keeping the code fairly simple, the
            # clearing out of files from the cache directory may
            # result in the count dropping below cache_min_count if
            # multiple entries are have the same last access
            # time. Same for cache_min_size.
            if count > self.cache_max_count or size > self.cache_max_size:
                while len(atime_keys) and (self.cache_min_count < count or self.cache_min_size < size):
                    key = atime_keys.pop(0)
                    for file in atime_list[key]:
                        #self.log.debug('clean_cache.unlink: %s' % file)
                        os.unlink(os.path.join(self.cache_dir, file))
                        count = count - 1
                        size = size - entry_list[file][6]
        else:
            #self.log.debug('clean_cache: cache_manager not set')
            pass


    # Extra helper functions
    def boolean(self, value):
        # This code is almost directly from trac.config in the 0.10 line...
        if isinstance(value, basestring):
            value = value.lower() in _TRUE_VALUES
        return bool(value)


    MIME_TYPES = ('application/gantt')

    # IHTMLPreviewRenderer methods
    
    def get_quality_ratio(self, mimetype):
        if mimetype in self.MIME_TYPES:
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        ext = filename.split('.')[1]
        name = ext == 'gantt' and 'gantt' or 'gantt.%s' % ext
        text = hasattr(content, 'read') and content.read() or content
        return self.render_macro(req, name, text)


    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/gantt')


    def process_request(self, req):
        # check and load the configuration
        trouble, msg = self.load_config()
        if trouble:
            return msg.getvalue()

        pieces = [item for item in req.path_info.split('/gantt') if len(item)]

        if len(pieces):
            pieces = [item for item in pieces[0].split('/') if len(item)]

            if len(pieces):
                name = pieces[0]
                img_path = os.path.join(self.cache_dir, name)
                return req.send_file(img_path, mimeview.get_mimetype(img_path))
        return


    # Gantt Drawing code
    def draw_chart(self,data,mstart,mend,outfilename,cellW,cellH,verbose) :
        # Calculate scale days 
        scale_days = (mend - mstart).days
        pixels_per_day = cellW / 30

        titles = [];
        monthdays = [];
        cur = mstart
        while (cur <= mend) :
            stitle = cur.strftime("%Y-%m")
            titles.append(stitle)
            monthdays.append((self.datefromstr(stitle) + relativedelta(months=+1,days=-1)).day)
            cur = cur + relativedelta(months=+1)
            
        # Render graphic

        cols = len(titles) # number of data columns
        rows = len(data)        # number of data rows
        #cellW = 80         # cell width
        #cellH = 20         # cell height
        lftColW = 150      # width of left column (task names)
        topRowH = 25       # height top row (month names)


        # calculate image size and define the canvas:
        imgH = topRowH + (cellH * rows)
        chartW = (sum(monthdays)  * pixels_per_day)
        imgW = lftColW + chartW

        im = Image.new("RGBA",[imgW,imgH])

        draw = ImageDraw.Draw(im)

        ## color in the headers:
        fcolor = ImageColor.getrgb('gainsboro')

        draw.rectangle((0,0,imgW,topRowH),fill=fcolor)
        draw.rectangle((0,0,lftColW,imgH), fill=fcolor)

        # and the area where toprow and lftcol overlap:
        draw.rectangle((0,0,lftColW,topRowH), fill="silver")

        ## draw the grid:
        xpos = 0
        x = 0
        for i in range(cols) :
            xpos = monthdays[i] * pixels_per_day
            # range(lftColW, imgW, cellW):
            draw.line((x + lftColW,0,x + lftColW,imgH),fill="black")
            x = x + xpos

        for y in range(topRowH, imgH, cellH):
            draw.line((0, y, imgW, y),fill="black")


        ## column titles, centered horizontally and vertically:
        ## font could be "arial.ttf"
	font_path = self.config.get('gantt', 'font_path')
	font = ImageFont.truetype(font_path,12)
	
        x = 0
        for i in range(cols):
            xpos = monthdays[i] * pixels_per_day
            tsizeX,tsizeY = font.getsize(titles[i])
            draw.text( (lftColW + x
                    + (xpos - tsizeX)/2, # left
                    (topRowH - tsizeY )),                         # top
                    titles[i],
                    font = font, fill="black")
            x = x + xpos


        now = datetime.now()
        if ((now - mstart).days > 0) :
            ## draw "past" shading first, so it goes on bottom:
            draw.rectangle((lftColW,topRowH, lftColW 
                + ((now - mstart).days * pixels_per_day), imgH),
                outline="black", fill="lightgray")

        ## draw the charts:
        i = 0
        keylist = data.keys()
        keylist.sort()
        for k in keylist :
            # draw label left-aligned and approximately 
            # centered vertically
            draw.text((5,                          # left
                topRowH + 5 + (i * cellH)), # top	
                data[k]["title"],
                font=font, fill="black")

            rect = (lftColW + (data[k]["start_days"].days * pixels_per_day), # left
                topRowH + (i * cellH),           # top
                lftColW + (data[k]["end_days"].days * pixels_per_day),   # right
                topRowH + ((i+1) * cellH))       # bottom
            if (verbose) :
                print data[k]["title"],rect
                
            # Draw task duration sized box
            if ("color" in data[k].keys()) :
                colorname = data[k]["color"]
            else :
                colorname = "green"
            # colorname = data[k].keys()
            draw.rectangle(rect,
              outline="black",
              fill=ImageColor.getrgb(colorname)
             )
            i = i + 1
            

        ## redraw outer border
        draw.rectangle((0, 0, imgW-1, imgH-1),outline="black")
        im.save(outfilename)
        draw = None
        im = None

    def process_dates(self,data) :
        startdates = enddates = [];
        keylist = data.keys()
        keylist.sort()
        for k in keylist :
            row = data[k]
            days = 0.0
            start = self.datefromstr(row["start"])
            row["startdt"] = start
            if ("end" in row.keys()) :
                row["enddt"] = self.datefromstr(row["end"])

            if (not "enddt" in row.keys()) :
                if ("w" in row["dur"].lower())  :
                    days = float(row["dur"].lower().replace("w",""))*7.0
                if ("d" in row["dur"].lower()) :
                    days = float(row["dur"].lower().replace("d",""))
                row["enddt"] = timedelta(days) + start
            
            startdates.append(row["startdt"] .strftime("%Y-%m"))
            enddates.append(row["enddt"] .strftime("%Y-%m"))

        mstart  = self.datefromstr(min(startdates))
        mend  = self.datefromstr(max(enddates))

        cur = mstart
        while 1 :
            cur = cur + relativedelta(months=+1)
            if (cur > mend) :
                break
        # Set ending range to next month after max end date
        mend = cur

        for k in data.keys() :
            row = data[k]
            dur_days = row["enddt"] - row["startdt"] 
            row["start_days"] = row["startdt"] - mstart
            row["end_days"] = row["enddt"] - mstart

        return mstart,mend

    def datefromstr(self,sDate) :
        tmp = sDate.split("-")
        if len(tmp) > 2 :
            d = datetime(int(tmp[0]),int(tmp[1]),int(tmp[2]))
            return d

        if len(tmp) > 1 :
            d = datetime(int(tmp[0]),int(tmp[1]),1)
            return d

    # from http://mail.python.org/pipermail/image-sig/2004-December.txt 
    def IntelliDraw(self,drawer,text,font,containerWidth):
        words = text.split()  
        lines = [] # prepare a return argument
        lines.append(words) 
        finished = False
        line = 0
        while not finished:
            thistext = lines[line]
            newline = []
            innerFinished = False
            while not innerFinished:
                #print 'thistext: '+str(thistext)
                if drawer.textsize(' '.join(thistext),font)[0] > containerWidth:
                    # this is the heart of the algorithm: we pop words off the current
                    # sentence until the width is ok, then in the next outer loop
                    # we move on to the next sentence. 
                    newline.insert(0,thistext.pop(-1))
                else:
                    innerFinished = True
            if len(newline) > 0:
                lines.append(newline)
                line = line + 1
            else:
                finished = True
        tmp = []        
        for i in lines:
            tmp.append( ' '.join(i) )
        lines = tmp
        (width,height) = drawer.textsize(lines[0],font)            
        return (lines,width,height)

def main()  : 
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hvo", ["help", "verbose", "outfile=","infile="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage(2)

	verbose = False
	outfilename = "test.png"
	infile = None
	
	for o, a in opts:
		if o in ("-v", "--verbose"):
			verbose = True
		elif o in ("-h", "--help"):
			usage(0)
			sys.exit()
		elif o in ("-o", "--outfile"):
			outfilename = a 
		elif o in ("--infile"):
			infile = open(a,"r") 
		else:
			assert False, "unhandled option"
	if (not infile) :
		infile = sys.stdin
	try :
		data = yaml.load(infile)
	except yaml.YAMLError,  detail :
		msg = "Data Loading Error: "
                if hasattr(detail, 'message'):
			msg = msg + detail.message
		if hasattr(detail, 'problem_mark'):
			mark = detail.problem_mark
			msg = msg + "\nError position: (%s:%s)" % (mark.line+1, mark.column+1)		
		print msg
		sys.exit(0)
		
	if (verbose) : 
		print "input"
		print yaml.dump(data)

	from trac.core import ComponentManager, ComponentMeta
	compmgr = ComponentManager()
	# Make sure we have no external components hanging around in the
	# component registry
	old_registry = ComponentMeta._registry
	ComponentMeta._registry = {}


	xx = GanttMacro(compmgr)

	start,end = xx.process_dates(data)

	if (verbose) : 
		print "min start %s" % start
		print "max end %s" % end
		print "processed"
		print yaml.dump(data)


	xx.draw_chart(data,start,end,outfilename,80,20,verbose)


def usage(code, msg=''):
    print >> sys.stderr, __doc__
    if msg:
        print >> sys.stderr, msg
    sys.exit(code)


# Start here 
if __name__ == "__main__":
    main()
    
