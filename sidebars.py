from PyQt4 import QtCore
from PyQt4 import QtGui
import at4
from config import config
import bisect
import traceback

__all__ = ["SectionSideBar", "SuSideBar", "SpeakerSideBar"]

class MyMap:
    def __init__(self, cmap=None, keys=None, values=None, default=None):
        """
        @param cmap: A function returning a mapping.  If this is None,
        keys and values are used.
        @param keys: A function returning a list of keys.
        If keys and values are None,
        cmap is used.  If keys is not None, values shouldn't be None.  If
        they are not None, their lengths should match.  If cmap is None,
        this shouldn't be None.
        @param values: A function returning a list of values.
        If keys and values are None,
        cmap is used.  If values is not None, keys shouldn't be None.  If
        they are not None, their lengths should match.  If cmap is None,
        this shouldn't be None.
        @param dc: default value
        @type cmap: dictionary
        @type keys: list
        @type values: list
        @type default: any
        """
        if cmap:
            def cmapf(k):
                h = cmap()
                if k in h:
                    return h[k]
                else:
                    return default
        else:
            def cmapf(k):
                try:
                    idx = keys().index(k)
                except ValueError:
                    return default
                try:
                    return values()[idx]
                except ValueError:
                    return default
        self.cmapf = cmapf

    def __call__(self, k):
        return self.cmapf(k)

    def __getitem__(self, k):
        return self.cmapf(k)

class SectionSideBar(at4.TranscriptEditSideBarCanvas):
    def __init__(self, te, colorMap=lambda x:Qt.white, parent=None, xtrans=None):
        """
        @param te: TranscriptEdit
        @param colorMap: speaker color map
        """
        colorMap = MyMap(keys=lambda:config['sectionTypes'],
                         values=lambda:config['sectionColors'],
                         default=QtCore.Qt.gray)
        at4.TranscriptEditSideBarCanvas.__init__(
            self, te, "", "", colorMap, parent)
        self._te = te
        self._box2idx = {}
        self.xtrans = xtrans
        self.toggle = True
        self.timer = None
        self.currentItem = None
        
    def _newbox(self, top, w, h, sec, color):
        item = QtGui.QGraphicsRectItem(0, top, w, h)
        self._canvas.addItem(item)
        self._boxes[sec] = item
        self._box2idx[item] = sec
        item.setBrush(QtGui.QBrush(color))
        item.show()
        
    def repaint(self, layout):
        self._boxes = {}
        self._box2idx = {}
        for item in self._canvas.items():
            #item.setCanvas(None)
            self._canvas.removeItem(item)
            del item

        if layout and self._data is not None:
            secBs = self._data.getMetadata("sectionBoundaries",True)
            secTs = self._data.getMetadata("sectionTypes",True)
            w = self.width() - 1
            l0 = layout[0]
            #sec0 = l0[1]['section']
            sec0 = bisect.bisect_right(secBs,l0[1]['start']) - 1
            secE = secBs[sec0+1]
            #secTyp0 = l0[1]['sectionType']
            secTyp0 = secTs[sec0]
            top = l0[2]
            h0 = 0
            for para,seg,y,h in layout:
                #sec = seg['section']
                t = seg['start']
                if t >= secE:
                    color = QtGui.QColor(self._colorMap(secTyp0))
                    self._newbox(top, w, h0, sec0, color)
                    while t >= secE:
                        sec0 += 1
                        secE = secBs[sec0+1]
                    secTyp0 = secTs[sec0]
                    top = y
                    h0 = h
                else:
                    h0 += h
            color = QtGui.QColor(self._colorMap(secTyp0))
            self._newbox(top, w, h0, sec0, color)
        self._canvas.update()

    def timerEvent(self, e):
        if self.toggle:
            pen = QtGui.QPen(QtCore.Qt.white)
        else:
            pen = QtGui.QPen(QtCore.Qt.black)
        self.currentItem.setPen(pen)
        self.toggle = not self.toggle
        self._canvas.update()
    
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            item = self._canvas.itemAt(self.mapToScene(e.pos()))
            if item is None: return
            i = self._box2idx[item]
            self.currentItem = item
            self.toggle = True
            self.timer = self.startTimer(250)
            menu = QtGui.QMenu(self)
            act1 = menu.addAction("Edit section type")
            act2 = menu.addAction("Delete section boundary")
            p = self.mapToGlobal(e.pos())
            a = menu.exec_(p)
            self.killTimer(self.timer)
            self.toggle = False
            self.timerEvent(None)
            if a is act1:
                self.xtrans.editSectionBoundaryTypeLeft(i)
            elif a is act2:
                self.xtrans.deleteSectionBoundaryLeft(i)
            
    # model-to-self
    def _cellChanged(self, i, c, v, w):
        pass    # don't do anything


class Format:
    def __init__(self, m):
        self.m = m
    def __mod__(self, x):
        return self.m[x]
    
class SuSideBar(at4.TranscriptEditSideBarCanvas):
    def __init__(self, te, colorMap=lambda x:Qt.white, parent=None, xtrans=None):
        """
        @param te: TranscriptEdit
        @param colorMap: speaker color map
        """
        colorMap = MyMap(keys=lambda:config['suSymbols']+config['suTypes'],
                         values=lambda:config['suColors']+config['suColors'],
                         default=QtCore.Qt.gray)
        symbolMap = MyMap(keys=lambda:config['suTypes']+config['suSymbols'],
                          values=lambda:config['suSymbols']+config['suSymbols'],
                          default=None)
        at4.TranscriptEditSideBarCanvas.__init__(
            self, te, "suType", Format(symbolMap), colorMap, parent)
        self.xtrans = xtrans
        self._box2seg = {}
        self.toggle = True
        self.currentItem = None
        self.timer = None
        
    def repaint(self, layout):
        self._boxes = {}
        self._box2seg = {}
        for item in self._canvas.items():
            self._canvas.removeItem(item)
            del item

        w = self.width() - 1
        for para,seg,y,h in layout:
            item = at4.TranscriptEditSideBarBox(
                seg, self._field, self._format, 0, y, w, h, self._canvas)
            self._boxes[para] = item
            self._box2seg[item] = seg
            color = QtGui.QColor(self._colorMap(seg[self._field]))
            item.setBrush(QtGui.QBrush(color))
            item.show()
        self._canvas.update()

    def timerEvent(self, e):
        if self.toggle:
            pen = QtGui.QPen(QtCore.Qt.white)
        else:
            pen = QtGui.QPen(QtCore.Qt.black)
        self.currentItem.setPen(pen)
        self.toggle = not self.toggle
        self._canvas.update()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            item = self._canvas.itemAt(self.mapToScene(e.pos()))
            if item is None: return
            seg = self._box2seg[item]
            seg.select()
            self.currentItem = item
            self.toggle = True
            self.timer = self.startTimer(250)
            menu = QtGui.QMenu(self)
            for typ in config['suTypes']:
                action = menu.addAction("Set %s SU" % typ)
                action.setData(QtCore.QVariant(typ))
            menu.addSeparator()
            menu.addAction("Unset SU")
            p = self.mapToGlobal(e.pos())
            action = menu.exec_(p)
            if action:
                if action.data().isNull():
                    self.xtrans.deleteSU()
                else:
                    typ = unicode(action.data().toString())
                    self.xtrans.setSU(typ, seg)
            self.killTimer(self.timer)
            self.toggle = False
            self.timerEvent(None)

class SpeakerSideBar(at4.TranscriptEditSideBarCanvas):
    def __init__(self, te, field, format, cmap, parent=None, xtrans=None):
        at4.TranscriptEditSideBarCanvas.__init__(self, te, field, format, cmap, parent)
        self.xtrans = xtrans
        self._box2seg = {}
        self.toggle = True
        self.currentItem = None
        self.timer = None
        
    def repaint(self, layout):
        self._boxes = {}
        self._box2seg = {}
        for item in self._canvas.items():
            self._canvas.removeItem(item)
            del item

        w = self.width() - 1
        for para,seg,y,h in layout:
            item = at4.TranscriptEditSideBarBox(
                seg, self._field, self._format, 0, y, w, h, self._canvas)
            self._boxes[para] = item
            self._box2seg[item] = seg
            color = QtGui.QColor(self._colorMap(seg[self._field]))
            item.setBrush(QtGui.QBrush(color))
            item.show()
        #self._canvas.update()


    def timerEvent(self, e):
        if self.toggle:
            pen = QtGui.QPen(QtCore.Qt.white)
        else:
            pen = QtGui.QPen(QtCore.Qt.black)
        self.currentItem.setPen(pen)
        self.toggle = not self.toggle
        self._canvas.update()

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            item = self._canvas.itemAt(self.mapToScene(e.pos()))
            if item is None: return
            item.setZValue(1)
            seg = self._box2seg[item]
            self.currentItem = item
            self.toggle = True
            self.timer = self.startTimer(250)
            menu = QtGui.QMenu()
            menu.addAction("Assign new speaker id (single)",
                           lambda:self.xtrans.assignNewSpeakerId(seg))
            menu.addAction("Edit speaker infomation (global)",
                           lambda:self.xtrans.editSpeakerInfoGlobal(seg))
            menu.addAction("Merge into another speaker (single)",
                           lambda:self.xtrans.mergeSpeaker(seg))
            menu.addAction("Merge into another speaker (global)",
                           lambda:self.xtrans.mergeSpeakerGlobal(seg))
            menu.exec_(self.mapToGlobal(e.pos()))
            self.killTimer(self.timer)
            self.toggle = False
            self.timerEvent(None)
            item.setZValue(0)
        elif e.button() == QtCore.Qt.LeftButton:
            item = self._canvas.itemAt(self.mapToScene(e.pos()))
            if item is None: return
            seg = self._box2seg[item]
            seg.select()
