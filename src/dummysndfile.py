from PyQt4 import QtCore
from PyQt4 import QtGui
import qwave4
from config import config
import bisect
import decimal

def nearbyint(n):
    return int(decimal.Decimal(str(n)).to_integral(decimal.ROUND_HALF_UP))

class DummySndFile(qwave4.SndFile):
    def __init__(self,
                 data,
                 colorMap,
                 waveformMap,
                 name=None,
                 channels=1,
                 samplerate=8000,
                 length=60.0,
                 numLayers=3):
        qwave4.SndFile.__init__(self)
        self.qobj = QtCore.QObject()
        self.data = data
        self.colorMap = colorMap
        self.waveformMap = waveformMap
        if name is None:
            self.name = "dummy_sndfile_%x" % id(self)
        else:
            self.name = name
        self.channels = channels
        self.samplerate = samplerate
        self.length = length
        self.numLayers = numLayers
        self.items = {}
        self.box2items = {} # inversion of self.items
        self.qobj.connect(data.emitter,QtCore.SIGNAL("cellChanged"),self._cellChanged)
        self.qobj.connect(data.emitter,QtCore.SIGNAL("insertRow"),self._insertRow)
        self.qobj.connect(data.emitter,QtCore.SIGNAL("takeRow"),self._takeRow)
        
    def getChannels(self):
        return self.channels
    def getSampleRate(self):
        return self.samplerate
    def getLengthSeconds(self):
        return self.length
    def getFileName(self):
        return self.name
    def drawWaveform(self, waveform, channel, beg, dur):
        ends = [-9999999.99] * self.numLayers
        self.box2items = {}
        canvas = waveform.getCanvas()
        for item in self.items.values():
            scene = item.scene()
            if scene: scene.removeItem(item)
            del item
        self.items = {}
        t1 = waveform.getBeginSeconds()
        t2 = t1 + waveform.getWidthSeconds()
        pps = waveform.getPixelsPerSecond()
        maxx = nearbyint((t2-t1)*pps) + 1
        for seg in self.data:
            s = seg['start']
            e = seg['end']
            if e <= t1: continue
            if s >= t2: break
            spkr = seg['speaker']
            
            color = self.colorMap(spkr)
            x1 = nearbyint((s-t1)*pps)
            x2 = nearbyint((e-t1)*pps)
            for h in range(self.numLayers):
                if ends[h] <= s:
                    break
            else:
                print "hmm..."
                h = 0
            ends[h] = e
            if x1 < -1: x1 = -1
            if x2 > maxx: x2 = maxx
            r = QtGui.QGraphicsRectItem(x1,h*5+1,x2-x1,5)
            canvas.addItem(r)
            r.setBrush(QtGui.QBrush(QtGui.QColor(color)))
            r.setZValue(1.0)
            #r.show()
            self.items[seg.num] = r
            self.box2items[r] = seg

        try:
            secBs = self.data.getMetadata('sectionBoundaries',True)
        except KeyError:
            secBs = []
        for b in secBs:
            if b >= t1 and b <= t2:
                x = nearbyint((b-t1)*pps)
                l = QtGui.QGraphicsLineItem()
                l.setLine(x,0,x,canvas.height()-1)
                l.setZValue(100.0)
                #l.show()
                canvas.addItem(l)
                self.items[id(l)] = l
        
        canvas.update()

    def refresh(self):
        wform = self.waveformMap(self.name,0)
        self.drawWaveform(wform,None,None,None)

    def select(self, rec):
        """
        @param rec: selected rectangle
        @type rec: QCanvasRectangle
        """
        if rec in self.box2items:
            self.box2items[rec].select()
            
    # model-to-self
    def _cellChanged(self, i, c, v, w):
        """
        @param i: row index
        @param c: column index
        @param v: cell value
        """
        h = self.data.getColumnName(c)
        if h == 'start' or h == 'end':
            wform = self.waveformMap(self.name,0)
            self.drawWaveform(wform,None,None,None)
        elif h == 'speaker':
            if i in self.items:
                color = self.colorMap(v)
                self.items[i].setBrush(QtGui.QBrush(QtGui.QColor(color)))
                wform = self.waveformMap(self.name,0)
                wform.getCanvas().update()
            
                
    def _insertRow(self, i, row):
        wform = self.waveformMap(self.name,0)
        self.drawWaveform(wform,None,None,None)
        
    def _takeRow(self, i, r):
        wform = self.waveformMap(self.name,0)
        self.drawWaveform(wform,None,None,None)

