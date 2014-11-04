from io import StringIO

from pdfminer.pdfparser import PDFParser, PDFPage, PSEOF
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter as PI
from pdfminer.pdfdevice import PDFDevice
from pdfminer.converter import TextConverter
try:
    from pdfminer.pdfparser import PDFDocument
except ImportError:
    from pdfminer.pdfdocument import PDFDocument

from . import utils

__all__ = ['PDF']

class PDFPageInterpreter(PI):
    def process_page(self, page):
        if 1 <= self.debug:
            print('Processing page: %r' % page, file=stderr)
        (x0,y0,x1,y1) = page.mediabox
        if page.rotate == 90:
            ctm = (0,-1,1,0, -y0,x1)
        elif page.rotate == 180:
            ctm = (-1,0,0,-1, x1,y1)
        elif page.rotate == 270:
            ctm = (0,1,-1,0, y1,-x0)
        else:
            ctm = (1,0,0,1, -x0,-y0)
        self.device.outfp.seek(0)
        self.device.outfp.buf = ''
        self.device.begin_page(page, ctm)
        self.render_contents(page.resources, page.contents, ctm=ctm)
        self.device.end_page(page)
        return self.device.outfp.getvalue()

class PDF(list):
    def __init__(self, file, password='', just_text=1):
        self.parser = PDFParser(file)
        self.doc = PDFDocument()
        try:
            self.doc.set_parser(self.parser)
        ## not nice or understood but works
        except (PSEOF, AttributeError):
            self.doc.set_parser(self.parser)
        self.doc.initialize(password)
        if self.doc.is_extractable:
            self.resmgr = PDFResourceManager()
            self.device = TextConverter(self.resmgr, outfp=StringIO())
            self.interpreter = PDFPageInterpreter(
               self.resmgr, self.device)
            ## probably breaks functionality
            pageid = 1            
            attrs = {'Resources': '', 'MediaBox' : ''}
            for page in PDFPage(self.doc, pageid, attrs):
                self.append(self.interpreter.process_page(page))
            self.metadata = self.doc.info
        if just_text:
            self._cleanup()

    def _cleanup(self):
        """ 
        Frees lots of non-textual information, such as the fonts
        and images and the objects that were needed to parse the
        PDF.
        """
        del self.device
        del self.doc
        del self.parser
        del self.resmgr
        del self.interpreter

    def text(self, clean=True):
        """ 
        Returns the text of the PDF as a single string.
        Options:

          :clean:
            Removes misc cruft, like lots of whitespace.
        """
        if clean:
            return utils.normalise_whitespace(''.join(self))
        else:
            return ''.join(self) 
