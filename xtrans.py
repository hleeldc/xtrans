"""
Xtrans: neXt generation TRANScription toolkit

Demonstrates how to build a transcription tool using Transcript,
TranscriptEdit and TranscriptWaveform.

It's rather long, but is not a complex program-- it's just a huge
boiler plate program.
"""

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from at4 import *
try:
    from xtrans_qwave import *
except ImportError, e:
    print >>sys.stderr, "There seems to be a problem in importing the qwave4 module"
    print >>sys.stderr, "qwave4 is required to run xtrans, so this is a critical error"
    print >>sys.stderr
    print >>sys.stderr,  str(e)
    sys.exit(1)
from dummysndfile import *
from otherwidgets import *
from listdialog import *
from sidebars import *
from config import *
from capabilities import *
from configdialog import *
if capabilities["spellchecker"]:
    from spellcheckdialog import *
from keyseqinputdialog import str2qkeyseq
import os
import random
import bisect
import threading
import time
import copy
import codecs

from speakerwidgets import *

def nop(): pass
class call:
    def __init__(self, func, *args):
        self.func = func
        self.args = args
    def __call__(self):
        return apply(self.func, self.args)

class Xtrans(QtGui.QMainWindow):
    def __init__(self, reverse=False):
        QtGui.QMainWindow.__init__(self)

        # data model
        self.data = None

        self.colorMap = speakercode.SpeakerCode()
        
        # central widget
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Vertical)
        upper_panel = QtGui.QWidget(splitter)  # upper panel
        splitter.setStretchFactor(0, 1)
         
        self.tred = TranscriptEdit(upper_panel)
        f = self.tred.font()
        f.setPointSize(16)
        self.tred.setFont(f)
        self.secbx = SectionSideBar(self.tred, parent=upper_panel, xtrans=self)
        self.spkrbx = SpeakerSideBar(
            self.tred, 'speaker', '%s', self.colorMap.color, upper_panel, xtrans=self)
        self.subx = SuSideBar(self.tred, parent=upper_panel, xtrans=self)
        self.spkrbx.setFixedWidth(config['speakerSidebarWidth'])
        self.secbx.setFixedWidth(8)
        self.subx.setFixedWidth(12)
        #self.tred.setKeyBindings({"Tab":nop})   # block tabs being inserted
        self.wave = XtransWaveform(splitter)
        #splitter.setResizeMode(self.wave, splitter.FollowSizeHint)

        # undo/redo
        self.undoStatus = []
        self.redoStatus = []
        self.undoStatusSection = []
        self.redoStatusSection = []

        # speaker panel
        self.spkrPanel = QtGui.QWidget(upper_panel)
        self.spkrSelPanel = SpeakerSelectionPanel(
            self.colorMap.color, self.spkrPanel)
        btnVOS = SmallButton("VOS", self.spkrPanel)
        btnVAS = SmallButton("VAS", self.spkrPanel)
        btnSRT = SmallButton("SRT", self.spkrPanel)
        btnCLR = SmallButton("CLR", self.spkrPanel)
        btnNSI = SmallButton("NSI", self.spkrPanel)
        btnESIg = SmallButton("ESIg", self.spkrPanel)
        btnMRG = SmallButton("MRG", self.spkrPanel)
        btnMRGg = SmallButton("MRGg", self.spkrPanel)
        btnLRS = SmallButton("LRS", self.spkrPanel)
        btnLAS = SmallButton("LAS", self.spkrPanel)
        btnLAG = SmallButton("LAG", self.spkrPanel)
        btnVOS.setToolTip("View only selected speaker's segments")
        btnVAS.setToolTip("View all speakers' segments")
        btnLRS.setToolTip("Listen random segments of selected speaker")
        btnLAS.setToolTip("Listen all segments of selected speaker")
        btnLAG.setToolTip("Listen all gaps")
        btnNSI.setToolTip("Assign new speaker ID for a single segment")
        btnESIg.setToolTip("Edit speaker information of all segments of selected speaker")
        btnMRG.setToolTip("Merge current segment into another speaker")
        btnMRGg.setToolTip("Merge all segments of selected speaker into another speaker")
        btnSRT.setToolTip("Toggle speaker sorting method (chronological/aphabetical)")
        btnCLR.setToolTip("Clear current speaker selection")
        self.connect(btnVOS, QtCore.SIGNAL("clicked()"), self.viewBySpeaker)
        self.connect(btnVAS, QtCore.SIGNAL("clicked()"), self.viewAllSpeakers)
        self.connect(btnLRS, QtCore.SIGNAL("clicked()"), self.listenRandomSample)
        self.connect(btnLAS, QtCore.SIGNAL("clicked()"), self.listenAll)
        self.connect(btnLAG, QtCore.SIGNAL("clicked()"), self.listenGaps)
        self.connect(btnNSI, QtCore.SIGNAL("clicked()"), self.assignNewSpeakerId)
        self.connect(btnESIg, QtCore.SIGNAL("clicked()"), self.editSpeakerInfoGlobal)
        self.connect(btnMRG, QtCore.SIGNAL("clicked()"), self.mergeSpeaker)
        self.connect(btnMRGg, QtCore.SIGNAL("clicked()"), self.mergeSpeakerGlobal)
        self.connect(btnSRT, QtCore.SIGNAL("clicked()"), self.spkrSelPanel.toggleSorting)
        self.connect(btnCLR, QtCore.SIGNAL("clicked()"), self.spkrSelPanel.clearSelection)

        # flags for listenAll
        self._btnLAS = btnLAS
        self._stopListenAll = False
        self._listenAllThread = None
        self._btnLasColor = btnLAS.palette().color(QtGui.QPalette.Button)

        # flags for listenGaps
        self._btnLAG = btnLAG
        self._stopListenGaps = False
        self._listenGapsThread = None
        self._btnLagColor = btnLAG.palette().color(QtGui.QPalette.Button)
        
        # dummy audio
        self.dummyAudio = None

        # filename for saving purpose
        self.filename = None
        self.filenameVerified = False
        self.formatName = {".tdf":"LDC .tdf transcript",
                           ".txt":"CTS style .txt file",
                           ".trs":"Transcriber transcript",
                           ".wl.sgm":"LDC Weblog SGML file",
                           ".ng.sgm":"LDC Newsgroup SGML file"}

        self.audioFiles = []    # list of audio filenames

        # status bar
        self.lblToggleMarking = QtGui.QLabel("ready", self.statusBar())
        self.blinker = False
        self.blinkerTimer = None
        self.blinkerColor = self.lblToggleMarking.palette().color(QtGui.QPalette.Background)
        self.statusBar().addWidget(self.lblToggleMarking,0)

        # autosave timer
        self.autosaveTimer = None
        self.autosaveFilename = None
        
        # menu
        menuBar = self.menuBar()
        menu_File = menuBar.addMenu("&File")
        menu_File.addAction("&New", self.menu_File_New)
        menu_File.addAction("&Open", self.menu_File_Open)
        menu_File.addAction("&Save", self.menu_File_Save)
        menu_File.addAction("Sa&ve As", self.menu_File_SaveAs)
        menu_File.addAction("&Revert", self.menu_File_Revert)
        menu_File.addSeparator()
        menu_File.addAction("Open &audio file", self.menu_File_OpenAudio)
        #menu_File.insertItem("Open &dummy audio file", self.menu_File_OpenDummyAudio)
        menu_File.addAction("&Close audio file", self.menu_File_CloseAudio)
        menu_File.addSeparator()
        menu_File_Import = menu_File.addMenu("&Import")
        menu_File_Import.addAction("&Transcriber", self.menu_File_Import_Transcriber)
        menu_File_Import.addAction("SGML: &Weblog", self.menu_File_Import_WeblogSgm)
        menu_File_Import.addAction("SGML: &Newsgroup", self.menu_File_Import_NewsgroupSgm)
        menu_File_Export = menu_File.addMenu("&Export")
        menu_File_Export.addAction("&CTS Style .txt", self.menu_File_Export_Txt)
        menu_File_Export.addAction("&Transcriber", self.menu_File_Export_Transcriber)
        menu_File_Export.addAction("SGML: &Weblog", self.menu_File_Export_WeblogSgm)
        menu_File_Export.addAction("SGML: &Newsgroup", self.menu_File_Export_NewsgroupSgm)
        menu_File.addSeparator()
        menu_File.addAction("E&xit", QtGui.QApplication.closeAllWindows)
        menu_Edit = menuBar.addMenu("&Edit")
        menu_Edit.addAction("Insert Segment", self.insertSegment)
        menu_Edit.addAction("Delete Segment", self.deleteSegment)
        menu_Edit.addSeparator()
        for suType in config["suTypes"]:
            f = call(self.setSU, suType)
            menu_Edit.addAction("Set %s SU" % suType, f)
##         menu_Edit.insertItem("Set Statement SU", self.insertSuStatement)
##         menu_Edit.insertItem("Set Question SU", self.insertSuQuestion)
##         menu_Edit.insertItem("Set Incomplete SU", self.insertSuIncomplete)
##         menu_Edit.insertItem("Set Backchannel SU", self.insertSuBackchannel)
        menu_Edit.addAction("Unset SU", self.deleteSU)
        menu_Edit.addSeparator()
        menu_Edit.addAction("Insert Section Boundary", self.insertSectionBoundary)
        menu_Edit.addAction("Delete Section Boundary", self.deleteSectionBoundaryLeft)
        menu_Edit.addAction("Edit Section Boundary Type", self.editSectionBoundaryTypeLeft)
        menu_Edit.addSeparator()
        menu_Edit.addAction("&Associate transcript to audio", self.menu_Edit_Assoc)
        menu_Edit.addAction("&Blindly associate transcript to audio", self.menu_Edit_BlindAssoc)
        menu_View = menuBar.addMenu("&View")
        menu_View.addAction("Change &font", self.menu_View_ChangeFont)
        #menu_View_BySpeaker = QPopupMenu(self)
        #menu_View.addSeparator()
        if reverse:
            self.menuItem_View_SetAlignment = menu_View.addAction(
                "Align left", self.menu_View_SetAlignment)
        else:
            self.menuItem_View_SetAlignment = menu_View.addAction(
                "Align right", self.menu_View_SetAlignment)
        self.menuItem_View_ShowSpeakerPanel = menu_View.addAction(
            "Hide speaker panel", self.menu_View_ShowSpeakerPanel)
        menu_Tools = menuBar.addMenu("&Tools")
        act = menu_Tools.addAction("&Check spelling", self.menu_Tools_CheckSpell)
        if not capabilities["spellchecker"]: act.setEnabled(False)
        menu_Tools.addAction("&View CTS-style transcript", self.menu_Tools_ViewCtsStyle)
        menu_Tools.addSeparator()
        menu_Tools.addAction("&Load configuration file", self.menu_Tools_LoadConfigFile)
        menu_Tools.addAction("&Save configuration file", self.menu_Tools_SaveConfigFile)
        menu_Tools.addAction("&Edit key bindings", self.menu_Tools_EditKeyBindings)
        menu_Tools.addAction("E&dit free string key bindings", self.menu_Tools_EditFreeStringKeyBindings)
        self.menu_View = menu_View
        #self.menu_View_BySpeaker = menu_View_BySpeaker
        #self.connect(menu_View_BySpeaker, SIGNAL("activated(int)"),
        #             self.updateViewBySpeakerMenuItemId)
        #self.viewBySpeakerMenu2spkr = {}

        # key bindings
        self.keyBindingFuncMap = {
            "KB_splitSegment":self.splitSegment,
            "KB_splitSegment":self.splitSegment,
            "KB_joinSegments":self.joinSegments,
            "KB_deleteSegment":self.deleteSegment,
            "KB_insertSegment":self.insertSegment,
            "KB_playRegion":self.playRegion,
            "KB_playAtRegionEnd":self.playAtRegionEnd,
            "KB_playWaveformBegin":self.playWaveformBegin,
            "KB_playLastSeconds":self.playLastSeconds,
            "KB_rewindOneSecond":self.rewindOneSecond,
            "KB_forwardOneSecond":self.forwardOneSecond,
            "KB_togglePause":self.togglePause,
            "KB_stopPlaying":self.stopPlaying,
            "KB_markAndPlay":self.toggleMarking,
            "KB_shrinkAtRightEdge":self.shrinkAtRightEdge,
            "KB_growAtRightEdge":self.growAtRightEdge,
            "KB_growAtLeftEdge":self.growAtLeftEdge,
            "KB_shrinkAtLeftEdge":self.shrinkAtLeftEdge,
            "KB_bigShrinkAtRightEdge":self.bigShrinkAtRightEdge,
            "KB_bigGrowAtRightEdge":self.bigGrowAtRightEdge,
            "KB_bigGrowAtLeftEdge":self.bigGrowAtLeftEdge,
            "KB_bigShrinkAtLeftEdge":self.bigShrinkAtLeftEdge,
            "KB_zoomIn":self.zoomIn,
            "KB_zoomOut":self.zoomOut,
            "KB_zoomInRegion":self.zoomInRegion,
            "KB_insertSectionBoundary":self.insertSectionBoundary,
            "KB_deleteSectionBoundaryLeft":self.deleteSectionBoundaryLeft,
            "KB_editSectionBoundaryTypeLeft":self.editSectionBoundaryTypeLeft,
            "KB_insertSuStatement":self.insertSuStatement,
            "KB_insertSuQuestion":self.insertSuQuestion,
            "KB_insertSuIncomplete":self.insertSuIncomplete,
            "KB_insertSuBackchannel":self.insertSuBackchannel,
            "KB_deleteSU":self.deleteSU,
            "KB_undo": self.undo,
            "KB_redo": self.redo,
            }            

        self.keyBindingAccelIdMap = {}  # given config name, stores action obj
        for k,v in self.keyBindingFuncMap.items():
            act = QtGui.QAction(self)
            act.setShortcut(config[k])
            act.triggered.connect(v)
            self.addAction(act)
            act.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            self.keyBindingAccelIdMap[k] = act
        self.fstrMap = {}  # given action, stores a string
        self._resetFreeStringKeybindings()
        #self.connect(self.accel, SIGNAL("activated(int)"), self.handleFreeStringKeyBindings)

        self.setCentralWidget(splitter)
        upper = QtGui.QHBoxLayout(upper_panel)
        self.uppertext = QtGui.QHBoxLayout()
        upper.addLayout(self.uppertext)
        if reverse:
            self.uppertext.setDirection(QtGui.QBoxLayout.RightToLeft)
            self.tred.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.uppertext.addWidget(self.secbx)
        self.uppertext.addWidget(self.spkrbx)
        self.uppertext.addWidget(self.subx)
        self.uppertext.addWidget(self.tred)
        upper.addWidget(self.spkrPanel)
        uright = QtGui.QVBoxLayout(self.spkrPanel)
        self.uppertext.setStretchFactor(self.tred, 1)
        upper.setStretchFactor(self.uppertext, 1)
        uright.addWidget(self.spkrSelPanel)
        btnpnl = QtGui.QGridLayout()
        uright.addLayout(btnpnl)
        btnpnl.addWidget(btnVOS,  0, 0)
        btnpnl.addWidget(btnVAS,  0, 1)
        btnpnl.addWidget(btnSRT,  0, 2)
        btnpnl.addWidget(btnCLR,  0, 3)
        btnpnl.addWidget(btnNSI,  1, 0)
        btnpnl.addWidget(btnESIg, 1, 1)
        btnpnl.addWidget(btnMRG,  1, 2)
        btnpnl.addWidget(btnMRGg, 1, 3)
        btnpnl.addWidget(btnLRS,  3, 0)
        btnpnl.addWidget(btnLAS,  3, 1)
        btnpnl.addWidget(btnLAG,  3, 2)
        #btnpnl.setSpacing(0)
        upper.setSpacing(0)

    def _resetFreeStringKeybindings(self):
        for act in self.fstrMap.keys():
            self.removeAction(act)
        self.fstrMap = {}
        for name in config:
            if name.startswith('FSKB_'):
                seq, s = config[name]
                act = QtGui.QAction(self)
                act.setShortcut(str2qkeyseq(seq))
                act.triggered.connect(call(self.handleFreeStringKeyBindings,s))
                self.addAction(act)
                self.fstrMap[act] = s

    #def actionEvent(self, e):
    #    if e.action() in self.fstrMap:
    #        self.handleFreeStringKeyBindings(e.action())
    #    else:
    #        QtGui.QMainWindow.actionEvent(self, e)

    def keyPressEvent(self, e):
        self.tred.setFocus(QtCore.Qt.OtherFocusReason)
        QtGui.QMainWindow.keyPressEvent(self, e)
        
    def closeEvent(self, e):
        if not self._showCloseFileWarning():
            e.ignore()
        else:
            self._stopAutoSaving()
            QtGui.QMainWindow.closeEvent(self, e)
            
    def timerEvent(self, e):
        if self.wave.isSelecting():
            palette = self.lblToggleMarking.palette()
            if self.blinker:
                palette.setBrush(palette.WindowText, self.blinkerColor)
            else:
                palette.setBrush(palette.WindowText, QtCore.Qt.black)
            self.lblToggleMarking.setPalette(palette)
            self.blinker = not self.blinker
        elif e.timerId() == self.autosaveTimer:
            self.statusBar().showMessage("Auto-saving ...", 1000)
            self.data.exportTdf(self.autosaveFilename)

    def _setData(self):
        # initialize color
        self.colorMap.clear()
        h = {}
        spkrs = []
        for row in self.data:
            spkr = row['speaker']
            if spkr not in h:
                h[spkr] = 1
                spkrs.append(spkr)
        for k in spkrs:
            self.colorMap.color(k)
            
        self.tred.setData(self.data, lambda x:x['speaker']!=config['sectionSpeakerId'])
        self.spkrbx.setData(self.data)
        self.secbx.setData(self.data)
        self.subx.setData(self.data)
        self.wave.setData(self.data)
        self.spkrSelPanel.setData(self.data)

        # dummy sndfile
        if self.dummyAudio:
            self.wave.removeDummySndFile(self.dummyAudio)
        if len(self.data):
            length = self.data[-1]['end']
        else:
            length = 60.0
        sndfile = DummySndFile(
            self.data,self.colorMap.color,self.wave.getWaveform,
            channels=1,length=length)
        filename = sndfile.getFileName()
        self.wave.addDummySndFile(sndfile)
        self.wave.placeWaveform(filename, 0, 0, True)
        w = self.wave.getWaveform(filename, 0)
        w.setFixedHeight(17)
        self.dummyAudio = sndfile


    def _startAutoSaving(self, filename):
        self._stopAutoSaving()
        self.autosaveFilename = filename + '.sav'
        self.autosaveTimer = self.startTimer(config['autosaveInterval'] * 1000)
        
    def _stopAutoSaving(self):
        self._removeAutoSaveFile()
        if self.autosaveTimer is not None:
            self.killTimer(self.autosaveTimer)

    def _removeAutoSaveFile(self):
        try:
            os.unlink(self.autosaveFilename)
        except OSError:
            pass
        except TypeError:
            pass
        
    def save(self, filename, format):
        if self.data is None: return
        if format == ".tdf":
            saveFunc = self.data.exportTdf
        elif format == ".txt":
            saveFunc = self.data.exportTxt
        elif format == ".trs":
            saveFunc = self.data.exportTrs
        elif format == ".wl.sgm":
            saveFunc = self.data.exportWeblogSgm
        elif format == ".ng.sgm":
            saveFunc = self.data.exportNewsgroupSgm
        else:
            QtGui.QMessageBox.critical(
                self, "Save Error",
                "Can't handle file format %s.\n"
                "Saving aborted." % format,
                "OK")
            return False
        try:
            saveFunc(filename)
            self._removeAutoSaveFile()
        except Error, e:
            QtGui.QMessageBox.critical(
                self, "Save Error",
                "Saving failed: %s" % str(e),
                "OK")
            return False
        
        if format == '.tdf':
            # if format is not .tdf, the file is being exported--
            #   no need to change current file status
            self.filename = filename
            self.filenameVerified = True
            self.setWindowTitle("Xtrans: "+os.path.basename(filename))
            self._startAutoSaving(filename)

        return True
    
    def saveAs(self, filenameHint, format, formatName):
        if self.data is None: return
        filename = QtGui.QFileDialog.getSaveFileName(
            self,
            "Save File As",
            filenameHint,
            "%s (*%s);; All (*.*)" % (formatName,format))
        filename = unicode(filename)
        if filename:
            if os.path.exists(filename):
                if os.path.isdir(filename):
                    QtGui.QMessageBox.critical(
                        self, "Save Error",
                        "'%s' is a directory" % filename,
                        "OK")
                    return False
                else:
                    res = QtGui.QMessageBox.warning(
                        self, "Warning",
                        "'%s' will be overwritten" % filename,
                        "OK", "Cancel")
                    if res == 1:
                        return False
            return self.save(filename, format)
        else:
            return False


    def _showCloseFileWarning(self):
        """
        @return False if user wants to save but failed
        or if user wants to cancel
        """
        if self.data is not None and len(self.data) > 0:
            ans = QtGui.QMessageBox.question(
                self, "Save File",
                "Current file will be closed.\n"
                "Do you want to save it?",
                "&Yes", "&No", "&Cancel")
            if ans == 0:
                if self.menu_File_Save() == False:
                    #self._showSaveFailedWarning()
                    return False
                else:
                    return True
            elif ans == 2:
                return False
        return True

    def _showSaveFailedWarning(self):
        QtGui.QMessageBox.critical(
            self, "Save Error",
            "Couldn't save the file.",
            "OK")
        
    def menu_File_New(self):
        if not self._showCloseFileWarning():
            return
            
        self.data = Transcript()
        self.data.metadata['sectionBoundaries'] = str([0.0,9999999.0])
        self.data.metadata['sectionTypes'] = str([None,None])
        #self.trans.setData(self.data)
        #self.wave.setData(self.data)
        self._setData()

        # filename for saving purpose
        if self.audioFiles:
            s = os.path.basename(self.audioFiles[-1])
            i = s.rfind('.')
            if i > 0:
                self.filename = s[:i] + ".tdf"
            else:
                self.filename = "unnamed.tdf"
        else:
            self.filename = "unnamed.tdf"
        self.filenameVerified = False

        self.setWindowTitle("Xtrans: " + self.filename)

        self._startAutoSaving(self.filename)


    def menu_File_Open(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open TDF file",
                "",
                "LDC TDF format (*.tdf);;"
                "All (*.*)"
                )
            filename = unicode(filename)
            if not filename: return
            if not os.path.exists(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return
            
        self.statusBar().showMessage("Opening transcript ...")

        try:
            self.data = Transcript.importTdf(filename)
        except Error, e:
            msg = "Error while opening the file:\n\n" \
                  "%s\n\n" \
                  "Error message:\n\n%s" % (filename, e.msg)
            QtGui.QMessageBox.critical(self, "Open Error", msg, "OK")
            self.statusBar().message("Failed to open file.", 2000)
            return
        
        try:
            self.data.getMetadata('sectionBoundaries')
        except KeyError:
            self.data.setMetadata('sectionBoundaries',[0.0,9999999.0])
        try:
            self.data.getMetadata('sectionTypes')
        except KeyError:
            self.data.setMetadata('sectionTypes',[None,None])
        self.data.sort('start')
        self._setData()

        # audio binding
        if self.audioFiles:
            try:
                ab = self.data.getMetadata("audioBinding", True)
            except KeyError:
                ab = None
            if ab:
                for i in range(0,len(ab),4):
                    fileid,ch1,pat,ch2 = ab[i:i+4]
                    for af in self.audioFiles:
                        if pat in af:
                            if ch2 < self.wave.getChannels(af):
                                self.wave.setAssociation(fileid,ch1,af,ch2)
            
        # filename for saving purpose
        self.filename = filename
        self.filenameVerified = True
        self.setWindowTitle("Xtrans: "+os.path.basename(filename))

        self.statusBar().showMessage("Transcript loaded succefully.", 2000)

        self._startAutoSaving(self.filename)
        
    def menu_File_Save(self):
        if self.data is None: return False
        if self.filenameVerified:
            return self.save(self.filename, ".tdf")
        else:
            return self.saveAs(self.filename, ".tdf", self.formatName[".tdf"])

    def menu_File_SaveAs(self):
        if self.data is None: return False
        return self.saveAs(self.filename, ".tdf", self.formatName[".tdf"])

    def menu_File_Revert(self):
        if self.data is None:
            QtGui.QMessageBox.warning(self, "No file", "There is nothing to revert!")
            return False
        if not self.filenameVerified:
            QtGui.QMessageBox.warning(
                self, "Not saved",
                "This is a new file that doesn't exists on the disk.")
            return False
        self.menu_File_Open(self.filename)
        
    def menu_File_OpenAudio(self, filename=None):
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open audio file",
                "",
                "Audio files (*.wav *.sph);;"
                "All (*.*)"
                )
            filename = unicode(filename)
            if not filename: return
        if not os.path.exists(filename):
            QtGui.QMessageBox.critical(
                self, "Audio File Open Error",
                "Audio file '%s' doesn't exist" % filename,
                "OK")
            return
        if os.path.isdir(filename):
            QtGui.QMessageBox.critical(
                self, "Audio File Open Error",
                "'%s' is a directory" % filename,
                "OK")
            return
        self.statusBar().showMessage("Opening audio file ...")
        sndfile = self.wave.addSndFile(filename)
        for ch in range(0,sndfile.getChannels()):
            self.wave.placeWaveform(filename, ch, self.wave.numWaveforms())
            #self.wave.getWaveform(filename, ch).setFixedHeight(50)
        self.audioFiles.append(filename)

        # audio binding
        try:
            ab = self.data.getMetadata("audioBinding", True)
        except KeyError:
            ab = None
        if ab:
            for i in range(0,len(ab),4):
                fileid,ch1,pat,ch2 = ab[i:i+4]
                if pat in filename:
                    if ch2 < self.wave.getChannels(filename):
                        self.wave.setAssociation(fileid,ch1,filename,ch2)
            
        self.statusBar().showMessage("Audio file loaded succefully.", 2000)

    def menu_File_CloseAudio(self):
        desc = "Please choose files to close in the list box below,\n" \
               "and press the OK button."
        d = ListDialog(self.audioFiles, description=desc,
                       caption="Close Audio File", parent=self)
        d.exec_()
        for f in d.getSelectedItems():
            self.wave.removeSndFile(f)
            self.audioFiles.remove(f)
    
    def menu_File_Import_Transcriber(self, filename=None):
        """
        Import transcriber file.

        @param filename: Name of the file to open. If it is omitted,
        None or an integer, a file open dialog will pop up.
        @param filename: str, None or int
        """

        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Transcriber File",
                "",
                "%s (*.trs);; All (*.*)" % self.formatName[".trs"]
                )
            filename = unicode(filename)
            if not filename : return
            if not os.path.exists(filename):
                msg = "'%s' doesn't exist" % filename
                QtGui.QMessageBox.critical(self, "Open Error", msg, "OK")
                return
            if os.path.isdir(filename):
                msg = "'%s' is a directory" % filename
                QtGui.QMessageBox.critical(self, "Open Error", msg, "OK")
                return

        try:
            self.data = Transcript.importTrs(filename)
        except Error, e:
            if e.errno == ERR_TRANS_IMPORT:
                msg = "Transcriber file import error:\n%s" % e.msg
            else:
                msg = "Found some problem in importing the file:\n%s" % e.msg
            QtGui.QMessageBox.critical(self, "Open Error", msg, "OK")
            return
            
        self.data.sort('start')
        self._setData()

        # filename for saving purpose
        self.filename = filename + ".tdf"
        self.filenameVerified = False
        self.setWindowTitle("Xtrans: "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

    def menu_File_Import_WeblogSgm(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Weblog SGM File",
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".wl.sgm"]
                )
            filename = unicode(filename)
            if not filename: return
            if not os.path.exists(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return

        self.data = Transcript.importWeblogSgm(filename)
        self.data.sort('start')
        self._setData()

        # filename for saving purpose
        self.filename = filename + ".tdf"
        self.filenameVerified = False
        self.setWindowTitle("Xtrans: "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

        
    def menu_File_Import_NewsgroupSgm(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Newsgroup SGM file",
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".ng.sgm"]
                )
            filename = unicode(filename)
            if not filename: return
            if not os.path.exists(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' doesn't exist" % filename,
                    "OK")
                return
            if os.path.isdir(filename):
                QtGui.QMessageBox.critical(
                    self, "Open Error",
                    "'%s' is a directory" % filename,
                    "OK")
                return

        self.data = Transcript.importNewsgroupSgm(filename)
        self.data.sort('start')
        self._setData()

        # filename for saving purpose
        self.filename = filename + ".tdf"
        self.filenameVerified = False
        self.setWindowTitle("Xtrans: "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

        
    def menu_File_Export_Txt(self):
        if self.data is None: return
        self.saveAs(self.filename + ".txt", ".txt", self.formatName[".txt"])
        
    def menu_File_Export_Transcriber(self):
        if self.data is None: return
        self.saveAs(self.filename + ".trs", ".trs", self.formatName[".trs"])
    
    def menu_File_Export_WeblogSgm(self):
        if self.data is None: return
        self.saveAs(self.filename + ".sgm", ".wl.sgm", self.formatName[".wl.sgm"])
    
    def menu_File_Export_NewsgroupSgm(self):
        if self.data is None: return
        self.saveAs(self.filename + ".sgm", ".ng.sgm", self.formatName[".ng.sgm"])
    
    def menu_Edit_Assoc(self):
        data = self.tred.getData()
        if data is not None:
            d = TransAudioAssocDialog(data, self.wave)
            d.exec_()

    def menu_Edit_BlindAssoc(self):
        if self.data and (self.audioFiles or self.dummyAudio):
            h = {}  # collection of all (fileid,channel) pairs
            h2 = {} # fileid-#channel dictionary
            for row in self.data:
                f,c = row['file'],row['channel']
                if (f,c) not in h:
                    h[f,c] = 1
                    if f not in h2:
                        h2[f] = 1
                    else:
                        h2[f] += 1

            h3 = {} # #channel-audio dict
            for af in self.audioFiles:
                n = self.wave.getChannels(af)
                if n in h3:
                    h3[n].append(af)
                else:
                    h3[n] = [af]

            # make a copy of h3 cauz we'll use it later
            h3copy = copy.deepcopy(h3)

            # first mapping try
            # # channels specified by transcript and the audio file
            # should match exactly
            r = []  # will contain unmapped (fileid,channel) pairs
            for f,nc in h2.items():
                if nc in h3:
                    af = h3[nc][0]
                    del h3[nc][0]
                    if not h3[nc]:
                        del h3[nc]
                else:
                    r.append((f,nc))
                    continue
                for c in range(nc):
                    self.wave.setAssociation(f,c,af,c)

            # second mapping try
            # # channels specified by transcript can be smaller than
            # that of the audio file
            r2 = [] # will contain still unmapped (fileid,channel) pairs
            for f,nc in r:
                for nc2 in h3:
                    if nc2 >= nc:
                        af = h3[nc2][0]
                        del h3[nc2][0]
                        if not h3[nc2]:
                            del h3[nc2]
                        break
                else:
                    r2.append((f,nc))
                    continue
                for c in range(nc):
                    self.wave.setAssociation(f,c,af,c)

            # third mapping try
            # same as the second try, but we can use already mapped
            # audio files (from h3copy)
            r3 = []
            for f,nc in r2:
                for nc2 in h3copy:
                    if nc2 >= nc:
                        af = h3copy[nc2][0]
                        break
                else:
                    r3.append((f,nc))
                    continue
                for c in range(nc):
                    self.wave.setAssociation(f,c,af,c)

            # finally, map all unmapped transcript channels to the dummy audio
            if self.dummyAudio:
                af = self.dummyAudio.getFileName()
                for f,nc in r3:
                    for c in range(nc):
                        self.wave.setAssociation(f,c,af,0)

            self.data.select(self.data.getSelection())
            
    def menu_View_ChangeFont(self):
        font, ok = QtGui.QFontDialog.getFont(self.tred.font(), self)
        if ok: self.tred.setFont(font)

    def menu_View_SetAlignment(self):
        if self.menuItem_View_SetAlignment.text() == "Align left":
            self.menuItem_View_SetAlignment.setText("Align right")
            self.uppertext.setDirection(QtGui.QBoxLayout.LeftToRight)
            self.tred.setLayoutDirection(QtCore.Qt.LeftToRight)
        else:
            self.menuItem_View_SetAlignment.setText("Align left")
            self.uppertext.setDirection(QtGui.QBoxLayout.RightToLeft)
            self.tred.setLayoutDirection(QtCore.Qt.RightToLeft)
            
    def menu_View_ShowSpeakerPanel(self):
        if self.spkrPanel.isHidden():
            self.menuItem_View_ShowSpeakerPanel.setText("Hide speaker panel")
            self.spkrPanel.show()
        else:
            self.menuItem_View_ShowSpeakerPanel.setText("Show speaker panel")
            self.spkrPanel.hide()

    def _replaceKeyBinding(self, binding, keyseq):
        func = self.keyBindingFuncMap[binding]
        if binding in self.keyBindingAccelIdMap:
            action = self.keyBindingAccelIdMap[binding]
            action.setShortcut(keyseq)

    def menu_Tools_CheckSpell(self):
        if self.data is None: return
        d = SpellChecker(self.data, self.tred)
        d.exec_()

    def menu_Tools_ViewCtsStyle(self):
        if self.data is None: return
        filename = config['xtransdir']+"/tmp.cts.txt"
        try:
            self.data.exportTxt(filename)
        except Error, e:
            QtGui.QMessageBox.critical(
                self, "View Error",
                "Error occurred during processing:\n%s" % e,
                "OK")
            return
        d = QtGui.QDialog(self)
        l = QtGui.QVBoxLayout(d)
        t = QtGui.QTextEdit(d)
        b = QtGui.QPushButton("Close", d)
        l.addWidget(t)
        l.addWidget(b)
        t.setMinimumWidth(600)
        t.setMinimumHeight(400)
        t.setFont(self.tred.font())
        l.setSpacing(5)
        l.setMargin(10)
        self.connect(b, QtCore.SIGNAL("clicked()"), d, QtCore.SLOT("accept()"))
        t.setText(codecs.getreader("utf-8")(file(filename)).read())
        d.setWindowTitle("CTS-Style Transcript")
        d.exec_()
        os.unlink(filename)
                
    def menu_Tools_LoadConfigFile(self, filename=None):
        if filename and type(filename) != int:
            if not os.path.exists(filename):
                QtGui.QMessageBox.critical(
                    self, "Load Error",
                    "Can't find config file %s." % `filename`,
                    "OK")
                return
        else:
            filename = QtGui.QFileDialog.getOpenFileName(
                self, "Open Config File", "", "All (*.*)")
            filename = unicode(filename)
        if filename:
            cfg = Config()
            cfg.read(open(filename))
            for k in config.keys():
                if k.startswith('FSKB_'):
                    del config[k]
            for k in cfg.keys():
                if k in config and k[:3] == 'KB_' and config[k] != cfg[k]:
                    self._replaceKeyBinding(k,cfg[k])
                config[k] = cfg.rawValue(k)
            self._resetFreeStringKeybindings()
    
    def menu_Tools_SaveConfigFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(
            self, "Save Config File", "xtrans.cfg", "All (*.*)")
        filename = unicode(filename)
        if filename:
            config.save(open(filename,"w"))

    def menu_Tools_EditKeyBindings(self):
        d = KeyBindingDialog(config, config_description, self)
        d.exec_()
        for k in d.changes.keys():
            self._replaceKeyBinding(k,config[k])

    def menu_Tools_EditFreeStringKeyBindings(self):
        d = FreeStringKeyBindingDialog(config, self)
        d.exec_()
        self._resetFreeStringKeybindings()
        
    # speaker panel slots
    def viewBySpeaker(self):
        if self.data is None: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if tup:
            spkr,typ,dialect = tup
            self.tred.setFilter(lambda x:x['speaker']==spkr)
            self.wave.setFilter(lambda x:x['speaker']==spkr)

    def viewAllSpeakers(self):
        if self.data is None: return
        self.tred.setFilter(lambda x:x['speaker']!=config['sectionSpeakerId'])
        self.wave.setFilter(lambda x:True)

    def listenRandomSample(self):
        if self.data is None or not self.audioFiles: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if not tup:
           QtGui.QMessageBox.warning(
               self, "Warning",
               "Select one of the speakers in\n"
               "the speaker list and try again.")
           return
        spkr,typ,dialect = tup
        L = [x.num for x in self.data if x['speaker']==spkr]
        random.shuffle(L)
        self.wave.playSegment(self.data[L[0]])

    def listenAll(self):
        if self.data is None or not self.audioFiles: return
        if self._listenGapsThread: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if not tup:
            QtGui.QMessageBox.warning(
                self, "Warning",
                "Select one of the speakers in\n"
                "the speaker list and try again.")
            return
        spkr,typ,dialect = tup
        
        if self._listenAllThread:
            self._stopListenAll = True
            self.wave.player.stop()
            self._listenAllThread.join()
            self._listenAllThread = None
            self._btnLAS.setText("LAS")
            palette = self._btnLAS.palette()
            palette.setColor(palette.Button, self._btnLasColor)
            self._btnLAS.setPalette(palette)
            return

        def f():
            for seg in self.data:
                if self._stopListenAll: break
                if seg['speaker'] == spkr:
                    self.wave.playSegment(seg)
                    self.wave.player.wait()
                    time.sleep(0.5)
            palette = self._btnLAS.palette()
            palette.setColor(palette.Button, self._btnLasColor)
            self._btnLAS.setPalette(palette)
            self._btnLAS.setText("LAS")
            self._listenAllThread = None

        palette = self._btnLAS.palette()
        palette.setColor(palette.Button, QtCore.Qt.red)
        self._btnLAS.setPalette(palette)
        self._btnLAS.setText("STOP")
        self._stopListenAll = False
        self._listenAllThread = threading.Thread(target=f)
        self._listenAllThread.start()

    def listenGaps(self):
        if self.data is None or not self.audioFiles: return
        if self._listenAllThread: return

        if self._listenGapsThread:
            self._stopListenGaps = True
            self.wave.player.stop()
            self._listenGapsThread.join()
            self._listenGapsThread = None
            self._btnLAG.setText("LAG")
            palette = self._btnLAG.palette()
            palette.setColor(palette.Button, self._btnLagColor)
            self._btnLAG.setPalette(palette)
            return

        limit = 0
        for sndfile in self.wave.getSndFiles().values():
            t = sndfile.getLengthSeconds()
            if t > limit: limit = t
            
        def f():
            maxend = 0
            for seg in self.data:
                if self._stopListenGaps: break
                s = seg['start']
                e = seg['end']
                if s > maxend:
                    self.wave.playRegion(maxend, s-maxend)
                    self.wave.player.wait()
                    time.sleep(0.5)
                if maxend < e:
                    maxend = e
            if not self._stopListenGaps and maxend < limit:
                self.wave.playRegion(maxend, limit-maxend)
                self.wave.player.wait()
            palette = self._btnLAG.palette()
            palette.setColor(palette.Button, self._btnLagColor)
            self._btnLAG.setPalette(palette)
            self._btnLAG.setText("LAG")
            self._listenGapsThread = None
            
        palette = self._btnLAG.palette()
        palette.setColor(palette.Button, QtCore.Qt.red)
        self._btnLAG.setPalette(palette)
        self._btnLAG.setText("STOP")
        self._stopListenGaps = False
        self._listenGapsThread = threading.Thread(target=f)
        self._listenGapsThread.start()
        
    def editSpeakerInfoGlobal(self, seg=None):
        if self.data is None: return
        if seg is None:
            tup = self.spkrSelPanel.getSelectedSpeaker()
            if not tup:
                QtGui.QMessageBox.warning(
                    self, "Warning",
                    "Select one of the speakers in\n"
                    "the speaker list and try again.")
                return
            spkr,typ,dialect = tup
            for row in self.data:
                if row['speaker'] == spkr:
                    break
            else:
                # FIXME: should handle this anomaly
                return
        else:
            row = seg
            
        d = SpeakerInfoDialog(self.data, self.spkrSelPanel.getSpeakers(), self)
        d.setInfo(row['speaker'],
                  row['speakerType'],
                  row['speakerDialect'])
        if d.exec_():
            spkr,typ,dialect = d.getValues()
            orgSpkr = row['speaker']
            #c = self.colorMap.color(orgSpkr)
            #self.colorMap.set_color(spkr, c) # this refreshes sidebar
            top1 = self.data.undoStackStatus()[0]
            for row in self.data:
                if row['speaker'] == orgSpkr:
                    row['speaker'] = spkr
                    row['speakerType'] = typ
                    row['speakerDialect'] = dialect
            top2 = self.data.undoStackStatus()[0]
            self.undoStatus.append((top2,top2 - top1))
            #self.spkrSelPanel.setData(self.data)    # refresh

            
    def assignNewSpeakerId(self, seg=None):
        if self.data is None: return
        if seg is None:
            sel = self.data.getSelection()
            if sel is None: return
            seg = self.data[sel]
        d = SpeakerInfoDialog(self.data, self.spkrSelPanel.getSpeakers(), self)
        d.setInfo(seg['speaker'],
                  seg['speakerType'],
                  seg['speakerDialect'])
        #d.setSpeakerTypeComboDisabled(True)
        #d.setSpeakerDialectComboDisabled(True)
        if d.exec_():
            spkr,typ,dialect = d.getValues()
            for row in self.data:
                if row['speaker'] == spkr:
                    QtGui.QMessageBox.critical(
                        self,
                        "Speaker ID Assignment Error",
                        "Speaker ID is not unique.",
                        "OK")
                    return
            top = self.data.undoStackStatus()[0]
            seg['speaker'] = spkr
            seg['speakerType'] = typ
            seg['speakerDialect'] = dialect
            self.undoStatus.append((top+3,3))
            #self.colorMap.set_color(spkr, self.colorMap.color(spkr))
            #self.spkrSelPanel.setData(self.data)    # refresh
            
    def mergeSpeakerGlobal(self, seg=None):
        if self.data is None: return
        if seg is None:
            tup = self.spkrSelPanel.getSelectedSpeaker()
            if not tup:
                QtGui.QMessageBox.warning(
                    self, "Warning",
                    "Select one of the speakers in\n"
                    "the speaker list and try again.")
                return
            spkr,typ,dialect = tup
        else:
            spkr = seg['speaker']
            typ = seg['speakerType']
            dialect = seg['speakerDialect']
        h = {}
        for row in self.data:
            s = row['speaker']
            if s in h:
                h[s].append(row)
            else:
                h[s] = [row]
        if spkr not in h:
            # FIXME: what the heck
            return
        spkrs = h.keys()
        spkrs.remove(spkr)
        spkrs.sort()
        desc = "Select a speaker so that the selected segment\n" \
               "is attributed to that speaker."
        d = ListDialog(spkrs, description=desc, multiChoice=False, parent=self)
        d.exec_()
        res = d.getSelectedItems()
        if res:
            L = h[res[0]]
            for row in self.data:
                if row['speaker']==spkr:
                    s = row['start']
                    e = row['end']
                    for row2 in L:
                        if row2['start'] < e and row2['end'] > s:
                            QtGui.QMessageBox.critical(
                                self, "Speaker Merge Error",
                                "Can't merge because of an overlapping.\n",
                                "OK")
                            return

            seg = L[0]
            newspkr = seg['speaker']
            newtyp = seg['speakerType']
            newdialect = seg['speakerDialect']
            for row in self.data:
                if row['speaker'] == spkr:
                    row['speaker'] = newspkr
                    row['speakerType'] = newtyp
                    row['speakerDialect'] = newdialect
            #self.spkrSelPanel.setData(self.data)    # refresh

        
    def mergeSpeaker(self, seg=None):
        if self.data is None: return
        if seg is None:
            sel = self.data.getSelection()
            if sel is None: return
            seg = self.data[sel]
        h = {}
        for row in self.data:
            h[row['speaker']] = row
        spkrs = h.keys()
        spkrs.remove(seg['speaker'])
        spkrs.sort()
        desc = "Select a speaker so that the selected segment\n" \
               "is attributed to that speaker."
        d = ListDialog(spkrs, description=desc, multiChoice=False, parent=self)
        d.exec_()
        res = d.getSelectedItems()
        if res:
            spkr = res[0]

            s = seg['start']
            e = seg['end']
            for row in self.data:
                if row['speaker']==spkr and row['start']<e and row['end']>s:
                    QtGui.QMessageBox.critical(
                        self, "Speaker Merge Error",
                        "Can't merge because of an overlapping.\n",
                        "OK")
                    return
                
            row = h[spkr]
            top = self.data.undoStackStatus()[0]
            seg['speaker'] = spkr
            seg['speakerType'] = row['speakerType']
            seg['speakerDialect'] = row['speakerDialect']
            self.undoStatus.append((top+3,3))
            #self.spkrSelPanel.setData(self.data)    # refresh

        
    # shorcut bindings: join/split
    def splitSegment(self):
        if self.data is None: return
        cur = self.tred.textCursor()
        charIdx = cur.position() - cur.block().position()
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        lst = seg.toList()

        i = seg.getColumnIndex('start')
        t0 = seg[i]
        t1 = seg['end']
        tt = self.wave.getCursorPositionS()
        #tt = (t0 + t1) / 2.0
        if tt <= t0 or tt >= t1:
            QtGui.QMessageBox.warning(self, "Error",
                "Waveform cursor is out of segment boundaries.")
            return

        top1 = self.data.undoStackStatus()[0]
        
        seg['end'] = tt
        lst[i] = tt

        i = seg.getColumnIndex('transcript')
        trans = seg['transcript']
        seg[i] = trans[:charIdx]
        lst[i] = trans[charIdx:]

        seg['suType'] = None

        if segIdx+1 >= len(self.data):
            segIdx2 = segIdx + 1
        else:
            for segIdx2 in range(segIdx+1,len(self.data)):
                if tt < self.data[segIdx2]['start']:
                    break
            else:
                segIdx2 += 1
        self.data.insertRow(segIdx2,lst)

        top2 = self.data.undoStackStatus()[0]
        self.undoStatus.append((top2,top2 - top1))
        
    def joinSegments(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        if segIdx >= len(self.data): return
        cur = self.tred.textCursor()
        para = cur.block().blockNumber()
        pos = cur.position()
        charIdx = pos - cur.block().position()

        seg1 = self.data[segIdx]
        segIdx2 = None
        seg2 = None
        fileid = seg1['file']
        channel = seg1['channel']
        speaker = seg1['speaker']
        for para in range(para+1,cur.document().blockCount()):
            segIdx2 = self.tred.getSegmentIndex(para)
            seg2 = self.data[segIdx2]
            if fileid == seg2['file'] and \
               channel == seg2['channel'] and \
               speaker == seg2['speaker']:
                break
        else:
            QtGui.QMessageBox.critical(
                self, "Join Error",
                "Can't find the next segment on the current\n"
                "\"virtual channel\"  Join aborted",
                "OK")
            return

        top1 = self.data.undoStackStatus()[0]
        self.data.takeRow(segIdx2)
        seg1['transcript'] += " " + seg2['transcript']
        seg1['end'] = seg2['end']
        seg1['suType'] = seg2['suType']
        top2 = self.data.undoStackStatus()[0]
        self.undoStatus.append((top2,top2-top1))
        
        cur.setPosition(pos)
        self.tred.setTextCursor(cur)
        #self.tred.setCursorPosition(segIdx,charIdx)

    def deleteSegment(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        if segIdx is None or segIdx >= len(self.data):
            return
        self.data.takeRow(segIdx)

    def insertSegment(self):
        if self.data is None: return
        wform,beg,end = self.wave.getSelectedRegionS()
        if not wform:
            QtGui.QMessageBox.critical(
                self, "Segment Insertion Error",
                "There is no selected region.",
                "OK")
            return
        if wform.getSndFile()==self.dummyAudio and \
           not config["segmentOnDummyAudio"]:
            QtGui.QMessageBox.critical(
                self, "Segment Insertion Error",
                "Current configuration does not allow creation\n"
                "of a segment on a segment span display.",
                "OK")
            return
        if beg < 0.0:
            QtGui.QMessageBox.critical(
                self, "Segment Insertion Error",
                "Can't insert a segment with negative timestamps.\n",
                "OK")
            return

        tup = self.wave.getAssociationForWaveform(wform)
        if tup is None:
            filepath = wform.getSndFile().getFileName()
            fileid = os.path.basename(filepath)
            ch = wform.getChannel()
        else:
            fileid,ch = tup
            filepath = None
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if tup:
            spkr,typ,dialect = tup
        else:
            d = SpeakerInfoDialog(self.data, self.spkrSelPanel.getSpeakers(), self)
            if d.exec_():
                spkr,typ,dialect = d.getValues()
                for row in self.data:
                    if row['speaker'] == spkr:
                        return
            else:
                return
            
        i = self.data.bisect_left('start',beg)
        overlap = False
        if i > 0:
            for j in range(i-1,-1,-1):
                row = self.data[j]
                if row['end'] <= beg:
                    break
                elif row['file']==fileid and \
                     row['channel']==ch and \
                     row['speaker']==spkr:
                    overlap = True
                    break
        if not overlap and i < len(self.data):
            for j in range(i,len(self.data)):
                row = self.data[j]
                if row['start'] >= end:
                    break
                elif row['file']==fileid and \
                     row['channel']==ch and \
                     row['speaker']==spkr:
                    overlap = True
                    break
        if overlap:
            QtGui.QMessageBox.critical(
                self, "Segment Insertion Error",
                "Can't insert the segment because it overlaps with\n"
                "a segment spanning from %.3f to %.3f" % (row['start'], row['end']),
                "OK")
            return
        else:
            secBs = self.data.getMetadata('sectionBoundaries',True)
            sec = bisect.bisect_right(secBs,beg)
            if secBs[sec] < end:
                QtGui.QMessageBox.critical(
                    self, "Segment Insertion Error",
                    "Can't insert the segment because it overlaps with\n"
                    "a section boundary at %.3f." % secBs[sec],
                    "OK")
                return
            sec -= 1
            secTyp = self.data.getMetadata('sectionTypes',True)[sec]
            if len(self.data) == 0:
                #sec = 0
                trn = 0
                seg = 0
                #secTyp = None
            else:
                if i >= len(self.data):
                    row = self.data[-1]
                    delta = 1
                else:
                    row = self.data[i]
                    delta = -1
                #sec = row['section']
                trn = row['turn']
                seg = row['segment'] + delta
                #secTyp = row['sectionType']
            record = [fileid,ch,beg,end,spkr,typ,dialect,"",
                      sec,trn,seg,secTyp]
            self.data.insertRow(i,record)
            if filepath is not None:    # no association for this file
                self.wave.setAssociation(fileid,ch,filepath,ch)
            #self.spkrSelPanel.setData(self.data)
            self.spkrSelPanel.setCurrentSpeaker(spkr)

    def zoomIn(self, *args):
        #self.wave.zoomAtCenter(2.0)
        self.wave.zoomInAtCursor()

    def zoomOut(self, *args):
        #self.wave.zoomAtCenter(0.5)
        self.wave.zoomOutAtCursor()

    def zoomInRegion(self):
        wform, t1, t2 = self.wave.getSelectedRegionS()
        self.wave.zoomInRegion(t1, t2)

    def insertSectionBoundary(self):
        if self.data is None: return
        wform,t1,t2 = self.wave.getSelectedRegionS()
        i = self.data.bisect_left('start',t1)
        for j in range(i):
            seg = self.data[j]
            if seg['start'] < t1 and seg['end'] > t1:
                QtGui.QMessageBox.critical(
                    self, "Section Boundary Insertion Error",
                    "Can't insert the section boundary at %.3f\n"
                    "because it overlaps with a segment." % t1,
                    "OK")
                return

        desc = "Please choose a section type for the new section\n" \
               "and press the OK button."
        lst = config['sectionTypes']
        d = ListDialog(lst, description=desc,
                       caption="Select Section Type",
                       multiChoice=False,
                       parent=self)
        d.exec_()
        res = d.getSelectedItems()
        if res:
            secT = res[0]
        else:
            return

        try:
            secBs = eval(self.data.metadata['sectionBoundaries'])
            secTs = eval(self.data.metadata['sectionTypes'])
        except KeyError:
            secBs = [0.0]
            secTs = [None]
        i = bisect.bisect_left(secBs,t1)
        secBs.insert(i,t1)
        secTs.insert(i,secT)

        self.data.setMetadata('sectionBoundaries',secBs)
        self.data.setMetadata('sectionTypes',secTs)

        t2 = secBs[i+1]
        j = self.data.bisect_left('start',t1)
        top1 = self.data.undoStackStatus()[0]
        for k in range(j,len(self.data)):
            seg = self.data[k]
            if seg['start'] >= t2: break
            seg['sectionType'] = secT
            seg['section'] = i
        top2 = self.data.undoStackStatus()[0]
        self.undoStatus.append((top2,top2 - top1))
        self.undoStatusSection.append((top2,('insert',i,t1,secT)))
            
        #self.trans.refreshSidebar()
        self.secbx.repaint(self.tred.getSideBarLayout())
        self.dummyAudio.refresh()

    def deleteSectionBoundaryLeft(self, secIdx=None):
        if self.data is None: return
        try:
            secBs = eval(self.data.metadata['sectionBoundaries'])
            secTs = eval(self.data.metadata['sectionTypes'])
        except KeyError:
            return
        #t = self.wave.getCursorPositionS()
        if secIdx:
            i = secIdx
        else:
            wform,t,t2 = self.wave.getSelectedRegionS()
            i = bisect.bisect_right(secBs, t) - 1
        if i == 0 or i == len(secBs)-1: return
        t1 = secBs[i]
        secT0 = secTs[i]
        del secBs[i]
        del secTs[i]
        t2 = secBs[i]

        self.data.setMetadata('sectionBoundaries',secBs)
        self.data.setMetadata('sectionTypes',secTs)

        secI = i-1
        secT = secTs[secI]
        j = self.data.bisect_left('start',t1)
        top1 = self.data.undoStackStatus()[0]
        for k in range(j,len(self.data)):
            seg = self.data[k]
            if seg['start'] >= t2: break
            seg['sectionType'] = secT
            seg['section'] = secI
        top2 = self.data.undoStackStatus()[0]
        self.undoStatus.append((top2,top2 - top1))
        self.undoStatusSection.append((top2,('delete',i,t1,secT0)))
        
        #self.trans.refreshSidebar()
        self.secbx.repaint(self.tred.getSideBarLayout())
        self.dummyAudio.refresh()
        
    def editSectionBoundaryTypeLeft(self, secIdx=None):
        if self.data is None: return
        try:
            secBs = eval(self.data.metadata['sectionBoundaries'])
            secTs = eval(self.data.metadata['sectionTypes'])
        except KeyError:
            return
        if secIdx:
            i = secIdx
        else:
            wform,t,t2 = self.wave.getSelectedRegionS()
            i = bisect.bisect_right(secBs, t) - 1
        desc = "Please choose a section type for the selected section\n" \
               "and press the OK button. Current type is '%s'." % secTs[i]
        lst = config["sectionTypes"]
        d = ListDialog(lst, description=desc,
                       caption="Select Section Type",
                       multiChoice=False,
                       defaultChoices=[secTs[i]],
                       parent=self)
        d.exec_()
        res = d.getSelectedItems()
        if res:
            secT0 = secTs[i]
            secTs[i] = res[0]
            self.data.setMetadata('sectionTypes',secTs)

            secT = secTs[i]
            j = self.data.bisect_left('start',secBs[i])
            t2 = secBs[i+1]
            top1 = self.data.undoStackStatus()[0]
            for k in range(j,len(self.data)):
                seg = self.data[k]
                if seg['start'] >= t2: break
                seg['sectionType'] = secT
                seg['section'] = i
            top2 = self.data.undoStackStatus()[0]
            self.undoStatus.append((top2,top2 - top1))
            self.undoStatusSection.append((top2,("edit",i,secT,secT0)))
            
            #self.trans.refreshSidebar()
            self.secbx.repaint(self.tred.getSideBarLayout())
            self.dummyAudio.refresh()

    def playRegion(self):
        self.wave.play()

    def playAtRegionEnd(self):
        self.wave.playAtRegionEnd()

    def playLastSeconds(self):
        self.wave.playLastSeconds()
        
    def playWaveformBegin(self):
        self.wave.playWaveformBegin()
        
    def rewindOneSecond(self):
        self.wave.rewindOneSecond()
        
    def forwardOneSecond(self):
        self.wave.forwardOneSecond()

    def togglePause(self):
        self.wave.pauseOrResume()

    def stopPlaying(self):
        self.wave.stop()

    def toggleMarking(self):
        self.wave.toggleMarking()
        if self.wave.isSelecting():
            self.blinkerTimer = self.startTimer(500)
            self.lblToggleMarking.setText("marking")
        else:
            if self.blinkerTimer:
                self.killTimer(self.blinkerTimer)
            palette = self.lblToggleMarking.palette()
            palette.setBrush(palette.WindowText, QtCore.Qt.black)
            self.lblToggleMarking.setPalette(palette)
            self.lblToggleMarking.setText("ready")

    def growAtLeftEdge(self):
        self.wave.growAtLeftEdge(1.0)

    def shrinkAtLeftEdge(self):
        self.wave.shrinkAtLeftEdge(1.0)

    def growAtRightEdge(self):
        self.wave.growAtRightEdge(1.0)

    def shrinkAtRightEdge(self):
        self.wave.shrinkAtRightEdge(1.0)

    def bigGrowAtLeftEdge(self):
        self.wave.growAtLeftEdge(3.0)

    def bigShrinkAtLeftEdge(self):
        self.wave.shrinkAtLeftEdge(3.0)

    def bigGrowAtRightEdge(self):
        self.wave.growAtRightEdge(3.0)

    def bigShrinkAtRightEdge(self):
        self.wave.shrinkAtRightEdge(3.0)

    def setSU(self, suType, seg=None):
        if self.data is None: return
        if seg is None:
            segIdx = self.data.getSelection()
            seg = self.data[segIdx]
        seg['suType'] = suType
        
    def insertSuStatement(self, *args):
        if self.data is None: return
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        seg['suType'] = config['suTypes'][0]
        
    def insertSuQuestion(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        seg['suType'] = config['suTypes'][1]
        
    def insertSuIncomplete(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        seg['suType'] = config['suTypes'][2]
        
    def insertSuBackchannel(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        seg['suType'] = config['suTypes'][3]
        
    def deleteSU(self):
        if self.data is None: return
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        seg['suType'] = ''

    def handleFreeStringKeyBindings(self, s):
        """
        @param aid: a QAction object
        """
        seg = self.data.getSelection()
        if seg is None: return
        a = s.split('*')
        pos = None
        for i,x in enumerate(a):
            if x and x[-1] == '\\':
                a[i] = x[:-1]+'*'
            else:
                pos = sum([len(x) for x in a[:i+1]])
                break
        s = ''.join(a)
        
        cur = self.tred.textCursor()
        if cur.hasSelection():
            text = s[:pos] + unicode(cur.selectedText()) + s[pos:]
        else:
            text = s
        cur.insertText(text)
            

    def undo(self):
        top, limit = self.data.undoStackStatus()

        if self.redoStatus and top > self.redoStatus[-1][0]:
            while len(self.redoStatusSection) > limit:
                self.redoStatusSection.pop()
                self.redoStatus.pop()
                
        if self.undoStatus and top==self.undoStatus[-1][0]:
            _,d = self.undoStatus.pop()
            self.data.undo(d)
            self.redoStatus.append((top-d,d))
            # section
            if self.undoStatusSection and top==self.undoStatusSection[-1][0]:
                _,(op,i,t1,t2) = self.undoStatusSection.pop()
                if op == 'edit':
                    secTs = self.data.getMetadata('sectionTypes', True)
                    secTs[i] = t2
                    self.data.setMetadata('sectionTypes', secTs)
                elif op == 'delete':
                    secBs = self.data.getMetadata('sectionBoundaries', True)
                    secTs = self.data.getMetadata('sectionTypes', True)
                    secBs.insert(i,t1)
                    secTs.insert(i,t2)
                    self.data.setMetadata('sectionBoundaries', secBs)
                    self.data.setMetadata('sectionTypes', secTs)
                elif op == 'insert':
                    secBs = self.data.getMetadata('sectionBoundaries', True)
                    secTs = self.data.getMetadata('sectionTypes', True)
                    del secBs[i]
                    del secTs[i]
                    self.data.setMetadata('sectionBoundaries', secBs)
                    self.data.setMetadata('sectionTypes', secTs)
                self.dummyAudio.refresh()
                self.redoStatusSection.append((top-d,(op,i,t1,t2)))
                self.secbx.repaint(self.tred.getSideBarLayout())
        else:
            self.data.undo()


    def redo(self):
        top, limit = self.data.undoStackStatus()
        if self.redoStatus and top==self.redoStatus[-1][0]:
            _,d = self.redoStatus.pop()
            self.data.redo(d)
            self.undoStatus.append((top+d,d))
            #section
            if self.redoStatusSection and top==self.redoStatusSection[-1][0]:
                _,(op,i,t1,t2) = self.redoStatusSection.pop()
                if op == 'edit':
                    secTs = self.data.getMetadata('sectionTypes', True)
                    secTs[i] = t1
                    self.data.setMetadata('sectionTypes', secTs)
                elif op == 'delete':
                    secBs = self.data.getMetadata('sectionBoundaries', True)
                    secTs = self.data.getMetadata('sectionTypes', True)
                    del secBs[i]
                    del secTs[i]
                    self.data.setMetadata('sectionBoundaries', secBs)
                    self.data.setMetadata('sectionTypes', secTs)
                elif op == 'insert':
                    secBs = self.data.getMetadata('sectionBoundaries', True)
                    secTs = self.data.getMetadata('sectionTypes', True)
                    secBs.insert(i,t1)
                    secTs.insert(i,t2)
                    self.data.setMetadata('sectionBoundaries', secBs)
                    self.data.setMetadata('sectionTypes', secTs)
                self.dummyAudio.refresh()
                self.undoStatusSection.append((top+d,(op,i,t1,t2)))
                self.secbx.repaint(self.tred.getSideBarLayout())
        else:
            self.data.redo()

        
if __name__ == "__main__":
    from optparse import OptionParser

    xtransdir = config['xtransdir']
    if os.path.exists(xtransdir):
        if not os.path.isdir(xtransdir):
            print
            print "Please remove the following file and try again."
            print os.path.normpath(xtransdir)
            print
            sys.exit(1)
    else:
        os.mkdir(xtransdir)
    
    app = QtGui.QApplication(sys.argv)

    parser = OptionParser()
    parser.add_option("-i", "--file", dest="filename",
                      help="open FILE at start", metavar="FILE")
    parser.add_option("-f", "--format", dest="format", default='.tdf',
                      help="input file in of FORMAT format", metavar="FORMAT")
    parser.add_option("-s", "--sound", dest="soundfile",
                      help="open an audio file FILE at start. If there are "
                      "more than one files to open, use comma to list the "
                      "files. There shouldn't be any space around comma.",
                      metavar="FILE")
    parser.add_option("-r", "--right-to-left", dest="bidi",
                      action="store_true", default=False,
                      help="text goes from right to left")
    parser.add_option("-a", "--blind-assoc", dest="assoc",
                      action="store_true", default=False,
                      help="blindly associate the transcript to audio channels")
    parser.add_option("-o", "--output", dest="ofilename",
                      help="save file as FILE and exit", metavar="FILE")
    parser.add_option("-n", "--new", dest="newfile",
                      action="store_true", default=False,
                      help="open a new file at start")
    parser.add_option("-c", "--config", dest="config",
                      help="start with config file FILE", metavar="FILE")
    
    (options, args) = parser.parse_args(app.argv()[1:])
    
    if options.bidi or \
       (len(args)>0 and args[0] == "arabic"):
        bidi = True
    else:
        bidi = False

    w = Xtrans(reverse=bidi)
    w.setWindowTitle("Xtrans: no file")

    if options.config:
        w.menu_Tools_LoadConfigFile(options.config)
        
    if options.filename:
        if options.format == '.tdf':
            w.menu_File_Open(options.filename)
        elif options.format == '.trs':
            w.menu_File_Import_Transcriber(options.filename)
        elif options.format == '.wl.sgm':
            w.menu_File_Import_WeblogSgm(options.filename)
        elif options.format == '.ng.sgm':
            w.menu_File_Import_NewsgroupSgm(options.filename)

        if options.ofilename:
            w.save(options.ofilename, '.tdf')
            sys.exit(0)
    else:
    #elif options.newfile:
        w.menu_File_New()
        
    w.resize(800, 600)
    w.show()

    if options.soundfile:
        for f in options.soundfile.split(','):
            w.menu_File_OpenAudio(f)

    if options.assoc:
        w.menu_Edit_BlindAssoc()

    w.statusBar().showMessage("")
    
    app.exec_()

