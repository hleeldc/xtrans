from PyQt4 import QtCore
from PyQt4 import QtGui
from at4 import TranscriptWaveform, WaveformWithResizableSelection
import qwave4
import dummysndfile
import locale

__all__ = ["XtransWaveform"]

class MyWaveform(WaveformWithResizableSelection):
    def __init__(self, *args, **kw):
        WaveformWithResizableSelection.__init__(self, *args, **kw)
        self.sndfile = self.getSndFile()
        self.imdummy = isinstance(self.sndfile, dummysndfile.DummySndFile)
        if self.imdummy:
            self.canvas = self.getCanvas()
        
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            sndfile = self.getSndFile()
            encoding = locale.getpreferredencoding()
            msg = "path: %s" % sndfile.getFileName().decode(encoding)
            msg += "\nchannel: %d" % self.getChannel()
            msg += "\nsample rate: %d" % sndfile.getSampleRate()
            QtGui.QMessageBox.information(
                self, "Audio File Info",
                msg,
                "OK")
            return
        
        WaveformWithResizableSelection.mousePressEvent(self, e)
        if self.imdummy:
            for item in self.canvas.items(e.posF()):
                if isinstance(item, QtGui.QGraphicsRectItem):
                    self.sndfile.select(item)
                    break


    def isDummy(self):
        return self.imdummy
    
class XtransWaveform(TranscriptWaveform):
    def __init__(self, *args, **kw):
        TranscriptWaveform.__init__(self, waveformCls=MyWaveform, *args, **kw)
        self.player.getPlayerTicker().registerReceiver(self)
        self.mutex = QtCore.QMutex()

        ##
        ## public properties
        self._selecting = False  # waveform selection by tick is happening

    def isSelecting(self):
        return self._selecting

    ####################
    # player control
    #
    def play(self):
        beg = self.selection.getBeginSeconds()
        dur = self.selection.getWidthSeconds()
        if dur == 0 or self._selecting:
            self.playFrom(beg)
        else:
            self.playRegion(beg, dur)

    def playSegment(self, seg=None):
        if seg is None:
            if self.currentSegment is None:
                return
            else:
                seg = self.currentSegment
        self.paused = False
        self.pauseBtn.setDown(False)
        s = seg['start']
        d = seg['end'] - s
        self.player.play(s,d)

    def repeatSegment(self, seg=None):
        if seg is None:
            if self.currentSegment is None:
                return
            else:
                seg = self.currentSegment
        self.paused = False
        self.pauseBtn.setDown(False)
        s = seg['start']
        d = seg['end'] - s
        self.player.repeat(s,d)
        
    def playFrom(self, t):
        self.paused = False
        self.pauseBtn.setDown(False)
        t2 = self.getMaxEndTime()
        if t < 0.0: t = 0.0
        self.player.play(t, t2-t)

    def playAtRegionEnd(self):
        wform = self.selection.getSelectedWaveform()
        if wform:
            s = self.selection.getBeginSeconds()
            d = self.selection.getWidthSeconds()
            t1 = s + d
            t2 = self.getMaxEndTime()
            self.player.play(t1,t2-t1)

    def playLastSeconds(self):
        """
        play the last 1 second of the selected region
        """
        s = self.selection.getBeginSeconds()
        d = self.selection.getWidthSeconds()
        if d < 1.0:
            self.player.play(s,d)
        else:
            e = s + self.selection.getWidthSeconds()
            self.player.play(e-1.0,1.0)
        
    def playWaveformBegin(self):
        wform = self.selection.getSelectedWaveform()
        if wform:
            t1 = wform.getBeginSeconds()
            t2 = self.getMaxEndTime()
            self.player.play(t1,t2-t1)
            
    def rewindOneSecond(self):
        if self.player.isDevicePlaying():
            if self._selecting:
                t = self.selection.getBeginSeconds()
                t1 = max(t,self.player.playerPosition() - 1.0)
                t2 = self.getMaxEndTime()
            else:
                t1 = self.player.playerPosition() - 1.0
                dur = self.selection.getWidthSeconds()
                if dur == 0:
                    t2 = self.getMaxEndTime()
                else:
                    t2 = self.selection.getBeginSeconds()+dur
            if t1 < 0.0: t1 = 0.0
            if t1 < t2:
                self.player.play(t1, t2-t1)
        else:
            wforms = self.getWaveforms()
            if wforms:
                wform = wforms[0]
                t = wform.getBeginSeconds() - wform.getWidthSeconds() / 10.0
                wform.display(max(0.0,t))
                
    def forwardOneSecond(self):
        if self.player.isDevicePlaying():
            t1 = self.player.playerPosition() + 1
            if self._selecting:
                t2 = self.getMaxEndTime()
            else:
                dur = self.selection.getWidthSeconds()
                if dur == 0.0:
                    t2 = self.getMaxEndTime()
                else:
                    t2 = self.selection.getBeginSeconds()+dur
            if t1 < t2:
                self.player.play(t1, t2-t1)
        else:
            wforms = self.getWaveforms()
            if wforms:
                wform = wforms[0]
                d = wform.getWidthSeconds() / 10.0
                wform.display(wform.getBeginSeconds()+d)
            
    def toggleMarking(self):
        # find the selected waveform
        wform = self.selection.getSelectedWaveform()
        if not wform: return

        t0 = self.selection.getBeginSeconds()
        t = t0 + self.selection.getWidthSeconds()
        if self._selecting:
            if self.player.isDevicePlaying(): self.stop()
            self.selection.expandSelectionEnd(wform,t)
            self.selection.freezeSelection(wform,t)
            self._selecting = False
        else:
            #if not self.player.isDevicePlaying():
            self.playFrom(t)
            self.selection.beginSelection(wform,t)
            self._selecting = True

    def continueMarking(self):
        wform = self.selection.getSelectedWaveform()
        if not wform: return
        
    ####################
    # selection control
    #
    def growAtLeftEdge(self, f=1.0):
        wform = self.selection.getSelectedWaveform()
        if wform:
            s = self.selection.getBeginSeconds()
            e = s + self.selection.getWidthSeconds()
            spp = wform.getSecondsPerPixel() * f
            if self.currentSegment: wform.setSelectionResizing(True)
            self.selection.expandSelectionBegin(wform,s-spp)
            self.selection.freezeSelection(wform,e)
            wform.setSelectionResizing(False)

    def growAtRightEdge(self, f=1.0):
        wform = self.selection.getSelectedWaveform()
        if wform:
            s = self.selection.getBeginSeconds()
            e = s + self.selection.getWidthSeconds()
            spp = wform.getSecondsPerPixel() * f
            if self.currentSegment: wform.setSelectionResizing(True)
            self.selection.expandSelectionEnd(wform,e+spp)
            self.selection.freezeSelection(wform,0.0)
            wform.setSelectionResizing(False)

    def shrinkAtLeftEdge(self, f=1.0):
        wform = self.selection.getSelectedWaveform()
        if wform:
            s = self.selection.getBeginSeconds()
            e = s + self.selection.getWidthSeconds()
            spp = wform.getSecondsPerPixel() * f
            t = min(e,s+spp)
            if self.currentSegment: wform.setSelectionResizing(True)
            self.selection.expandSelectionBegin(wform,t)
            self.selection.freezeSelection(wform,e)
            wform.setSelectionResizing(False)

    def shrinkAtRightEdge(self, f=1.0):
        wform = self.selection.getSelectedWaveform()
        if wform:
            s = s = self.selection.getBeginSeconds()
            e = s + self.selection.getWidthSeconds()
            spp = wform.getSecondsPerPixel() * f
            t = max(s,e-spp)
            if self.currentSegment: wform.setSelectionResizing(True)
            self.selection.expandSelectionEnd(wform,t)
            self.selection.freezeSelection(wform,0.0)
            wform.setSelectionResizing(False)

                
    ####################
    # player ticker interface
    #
    def customEvent(self, e):
        if e.type() == qwave4.PlayerPosition:
            if not self.player.isDevicePlaying(): return
            if self.mutex.tryLock():
                wforms = self.getWaveforms()
                t = self.player.playerPosition()
                if wforms:
                    wform = wforms[0]
                    beg = wform.getBeginSeconds()
                    dur = wform.getWidthSeconds()
                    end = beg + dur
                    if beg > t:
                        wform.display(t)
                        #for w in wforms:
                        #    w.display(t)
                    elif end < t:
                        wform.display(beg + dur)
                        #for w in wforms:
                        #    w.display(beg+dur)
                    if self._selecting:
                        self.selection.expandSelectionEnd(wform,t)
                        self.selection.freezeSelection(wform,t)
                self.mutex.unlock()

    ####################
    # model-to-gui
    #
    def _select(self, i):
        if self._selecting: return
        else: TranscriptWaveform._select(self, i)
