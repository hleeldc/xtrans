from PyQt4 import QtGui
from at4 import TranscriptEdit

class SuTranscriptEdit(TranscriptEdit):
    def __init__(self, xtrans, config, parent=None):
        TranscriptEdit.__init__(self, parent)
        self.xtrans = xtrans
        self.config = config

        class F:
            xtrans = self.xtrans
            text = self
            def __init__(self, suType):
                self.typ = suType
            def __call__(self, *args):
                p,c = F.text.getCursorPosition()
                if unicode(F.text.text(p))[c:].strip() != "":
                    F.xtrans.splitSegment()
                    i = F.xtrans.data.getSelection()
                    xtrans.data.select(i-1)
                    p,c = F.text.getCursorPosition()
                    F.text.setCursorPosition(p,F.text.paragraphLength(p))
                F.xtrans.setSU(self.typ)
                
        self.setSuFuncs = []
        for suType in config["suTypes"]:
            self.setSuFuncs.append((suType,F(suType)))

    def createPopupMenu(self, *args):
        menu = QPopupMenu(self)
        for k,v in self.setSuFuncs:
            menu.insertItem(k,v)
        return menu


    def _highlightParagraph(self, p):
        pass
