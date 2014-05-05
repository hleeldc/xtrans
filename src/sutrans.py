"""
"""

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from at4 import *
from otherwidgets import *
from listdialog import *
from sidebars import *
from config import *
from capabilities import *
from configdialog import *
from transcriptedit_su import *
if capabilities["spellchecker"]:
    from spellcheckdialog import *
from keyseqinputdialog import str2qkeyseq
import os
import random
import bisect
import time
import copy
import codecs

from speakerwidgets import *

PROGNAM = 'SUtrans'

def nop(): pass

class Xtrans(QtGui.QMainWindow):
    def __init__(self, reverse=False):
        QtGui.QMainWindow.__init__(self)

        # data model
        self.data = None

        self.colorMap = speakercode.SpeakerCode()

        # widgets
        cw = QtGui.QWidget(self)
        
        self.tred = SuTranscriptEdit(self, config, cw)
        f = self.tred.font()
        f.setPointSize(16)
        self.tred.setFont(f)
        
        self.spkrbx = SpeakerSideBarSUTrans(self.tred,
                                            'speaker',
                                            '%s',
                                            self.colorMap.color,
                                            parent=cw,
                                            xtrans=self)
        self.spkrbx.setFixedWidth(config['speakerSidebarWidth'])

        self.subx = SuSideBar(self.tred, parent=cw, xtrans=self)
        self.subx.setFixedWidth(12)

        # build speaker panel widget
        self.spkrPanel = QtGui.QWidget(cw)
        self.spkrPanel.setFixedWidth(180)
        
        self.spkrSelPanel = SpeakerSelectionPanel(self.colorMap.color,
                                                  self.spkrPanel)
        btnVOS = SmallButton("VOS", self.spkrPanel)
        btnVAS = SmallButton("VAS", self.spkrPanel)
        btnSRT = SmallButton("SRT", self.spkrPanel)
        btnCLR = SmallButton("CLR", self.spkrPanel)
        btnHDE = SmallButton("HIDE", self.spkrPanel)
        btnSHW = SmallButton("SHOW", self.spkrPanel)
        btnVOS.setToolTip("View only selected speaker's segments")
        btnVAS.setToolTip("View all speakers' segments")
        btnSRT.setToolTip("Toggle speaker sorting method (chronological/aphabetical)")
        btnCLR.setToolTip("Clear current speaker selection")
        self.connect(btnVOS, QtCore.SIGNAL("clicked()"), self.viewBySpeaker)
        self.connect(btnVAS, QtCore.SIGNAL("clicked()"), self.viewAllSpeakers)
        self.connect(btnSRT, QtCore.SIGNAL("clicked()"),
                     self.spkrSelPanel.toggleSorting)
        self.connect(btnCLR, QtCore.SIGNAL("clicked()"),
                     self.spkrSelPanel.clearSelection)
        self.connect(btnHDE, QtCore.SIGNAL("clicked()"), self.hideSpeaker)
        self.connect(btnSHW, QtCore.SIGNAL("clicked()"), self.showSpeaker)

        # layout
        layout = QtGui.QHBoxLayout(cw)
        layout2 = QtGui.QHBoxLayout()
        if reverse:
            layout2.setDirection(QtGui.QBoxLayout.RightToLeft)
            self.tred.setLayoutDirection(QtCore.Qt.RightToLeft)
        layout2.addWidget(self.spkrbx)
        layout2.addWidget(self.subx)
        layout2.addWidget(self.tred)
        layout2.setStretchFactor(self.tred, 1)
        layout2.setSpacing(0)

        layout4 = QtGui.QGridLayout()
        layout4.addWidget(btnVOS, 0, 0)
        layout4.addWidget(btnVAS, 0, 1)
        layout4.addWidget(btnSRT, 0, 2)
        layout4.addWidget(btnCLR, 0, 3)
        layout4.addWidget(btnHDE, 1, 0)
        layout4.addWidget(btnSHW, 1, 1)

        layout3 = QtGui.QVBoxLayout(self.spkrPanel)
        layout3.addWidget(self.spkrSelPanel)
        layout3.addLayout(layout4)

        layout.addLayout(layout2)
        layout.addWidget(self.spkrPanel)
        
        self.setCentralWidget(cw)

        # undo/redo
        self.tred.undo = self.undo
        self.tred.redo = self.redo
        self.undoStatus = []
        self.redoStatus = []
        self.undoStatusSection = []
        self.redoStatusSection = []

        # hidden speakers
        self.hiddenSpeakers = []
        
        # filename for saving purpose
        self.filename = None
        self.filenameVerified = False
        self.formatName = {".tdf":"LDC .tdf transcript",
                           ".txt":"CTS style .txt file",
                           ".trs":"Transcriber transcript",
                           ".wl.sgm":"LDC Weblog SGML file",
                           ".ng.sgm":"LDC Newsgroup SGML file",
                           ".nw.sgm":"LDC Newswire SGML file"}

        # autosave timer
        self.autosaveTimer = None
        self.autosaveFilename = None
        
        # menu
        menuBar = self.menuBar()
        menu_File = menuBar.addMenu('&File')
        menu_File.addAction("&Open", self.menu_File_Open)
        menu_File.addAction("&Save", self.menu_File_Save)
        menu_File.addAction("Sa&ve As", self.menu_File_SaveAs)
        menu_File.addSeparator()
        menu_File_Import = menu_File.addMenu('&Import')
        menu_File_Import.addAction("SGML: &Weblog",
                                   self.menu_File_Import_WeblogSgm)
        menu_File_Import.addAction("SGML: &Newsgroup",
                                   self.menu_File_Import_NewsgroupSgm)
        menu_File_Import.addAction("SGML: &Newswire",
                                   self.menu_File_Import_NewswireSgm)
        menu_File_Export = menu_File.addMenu('&Export')
        menu_File_Export.addAction("SGML: &Weblog",
                                   self.menu_File_Export_WeblogSgm)
        menu_File_Export.addAction("SGML: &Newsgroup",
                                   self.menu_File_Export_NewsgroupSgm)
        menu_File_Export.addAction("SGML: &Newswire",
                                   self.menu_File_Export_NewswireSgm)
        menu_File.addSeparator()
        menu_File.addAction("E&xit", QtGui.QApplication.closeAllWindows)
        menu_Edit = menuBar.addMenu('&Edit')
        class F:
            xtrans = self
            def __init__(self, suType):
                self.typ = suType
            def __call__(self, *args):
                F.xtrans.setSU(self.typ)
        self.setSuFuncs = {}
        for suType in config["suTypes"]:
            f = F(suType)
            menu_Edit.addAction("Set %s SU" % suType, f)
            self.setSuFuncs[suType] = f
        menu_Edit.addAction("Unset SU", self.deleteSU)
        menu_Edit.addSeparator()
        menu_View = menuBar.addMenu('&View')
        menu_View.addAction("Change &font", self.menu_View_ChangeFont)
        menu_View.addSeparator()
        self.menuItem_View_ShowSpeakerPanel = menu_View.addAction(
            "Hide speaker panel", self.menu_View_ShowSpeakerPanel)
        menu_Tools = menuBar.addMenu('&Tools')
        menu_Tools.addAction("&Load configuration file",
                             self.menu_Tools_LoadConfigFile)
        menu_Tools.addAction("&Save configuration file",
                             self.menu_Tools_SaveConfigFile)
        menu_Tools.addAction("&Edit key bindings",
                             self.menu_Tools_EditKeyBindings)

        # key bindings
        self.keyBindingFuncMap = {
            "KB_splitSegment": self.splitSegment,
            "KB_joinSegments": self.joinSegments,
            "KB_insertSuStatement": self.insertSuStatement,
            "KB_insertSuQuestion": self.insertSuQuestion,
            "KB_insertSuIncomplete": self.insertSuIncomplete,
            "KB_insertSuBackchannel": self.insertSuBackchannel,
            "KB_deleteSU": self.deleteSU,
            "KB_undo": self.undo,
            "KB_redo": self.redo,
            }            

        self.keyBindingAccelIdMap = {}
        for k,v in self.keyBindingFuncMap.items():
            act = QtGui.QAction(self)
            act.setShortcut(config[k])
            act.triggered.connect(v)
            self.addAction(act)
            act.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            self.keyBindingAccelIdMap[k] = act


    def closeEvent(self, e):
        if not self._showCloseFileWarning():
            e.ignore()
        else:
            self._stopAutoSaving()
            QtGui.QMainWindow.closeEvent(self, e)
            
    def timerEvent(self, e):
        if e.timerId() == self.autosaveTimer:
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
            
        self.tred.setData(self.data,
                          lambda x:x['speaker']!=config['sectionSpeakerId'])
        self.spkrbx.setData(self.data)
        self.subx.setData(self.data)
        self.spkrSelPanel.setData(self.data)


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
        elif format == ".nw.sgm":
            saveFunc = self.data.exportNewswireSgm
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
            self.setCaption(PROGNAM + ": "+os.path.basename(filename))
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
            msg = "TDF import error:\n%s" % e.msg
            QtGui.QMessageBox.critical(self, "Open Error", msg, "OK")
            self.statusBar().showMessage("Failed to open file.", 2000)
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
        #self.trans.setData(self.data)
        #self.wave.setData(self.data)
        self._setData()

        # filename for saving purpose
        self.filename = filename
        self.filenameVerified = True
        self.setWindowTitle(PROGNAM + ": "+os.path.basename(filename))

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

    def menu_File_Import_WeblogSgm(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Weblog SGM File",
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".wl.sgm"])
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
        self.setCaption(PROGNAM + ": "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

        
    def menu_File_Import_NewsgroupSgm(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Newsgroup SGM file",
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".ng.sgm"])
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
        self.setCaption(PROGNAM + ": "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

        
    def menu_File_Import_NewswireSgm(self, filename=None):
        if not self._showCloseFileWarning():
            return
            
        if filename is None or type(filename)==int:
            filename = QtGui.QFileDialog.getOpenFileName(
                self,
                "Open Newswire SGM file",
                "",
                "%s (*.sgm);; All (*.*)" % self.formatName[".nw.sgm"])
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

        self.data = Transcript.importNewswireSgm(filename)
        self.data.sort('start')
        self._setData()

        # filename for saving purpose
        self.filename = filename + ".tdf"
        self.filenameVerified = False
        self.setCaption(PROGNAM + ": "+os.path.basename(self.filename))

        self._startAutoSaving(self.filename)

        
    def menu_File_Export_WeblogSgm(self):
        if self.data is None: return
        self.saveAs(self.filename + ".sgm", ".wl.sgm", self.formatName[".wl.sgm"])
    
    def menu_File_Export_NewsgroupSgm(self):
        if self.data is None: return
        self.saveAs(self.filename + ".sgm", ".ng.sgm", self.formatName[".ng.sgm"])
    
    def menu_File_Export_NewswireSgm(self):
        if self.data is None: return
        self.saveAs(self.filename + ".sgm", ".nw.sgm", self.formatName[".nw.sgm"])
    
    def menu_View_ChangeFont(self):
        self.tred.setFont(QFontDialog.getFont(self.tred.font(),self)[0])
    
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
            aid = self.keyBindingAccelIdMap[binding]
            self.accel.disconnectItem(aid, func)
            self.accel.removeItem(aid)
        aid = self.accel.insertItem(keyseq)
        self.accel.connectItem(aid, func)
        self.keyBindingAccelIdMap[binding] = aid

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
            cfg.read(file(filename))
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
            config.save(file(filename,"w"))

    def menu_Tools_EditKeyBindings(self):
        d = KeyBindingDialog(config, config_description, self)
        d.exec_()
        for k in d.changes.keys():
            self._replaceKeyBinding(k,config[k])

    # speaker panel slots
    def hideSpeaker(self):
        if self.data is None: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if tup:
            spkr,typ,dialect = tup
            if spkr not in self.hiddenSpeakers:
                self.hiddenSpeakers.append(spkr)
            self.tred.setFilter(lambda x:x['speaker'] not in self.hiddenSpeakers)

    def showSpeaker(self):
        if self.data is None: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if tup:
            spkr,typ,dialect = tup
            if spkr in self.hiddenSpeakers:
                self.hiddenSpeakers.remove(spkr)
            self.tred.setFilter(lambda x:x['speaker'] not in self.hiddenSpeakers)

    def viewBySpeaker(self):
        if self.data is None: return
        tup = self.spkrSelPanel.getSelectedSpeaker()
        if tup:
            spkr,typ,dialect = tup
            self.hiddenSpeakers = self.spkrSelPanel.getSpeakers()
            self.hiddenSpeakers.remove(spkr)
            self.tred.setFilter(lambda x:x['speaker']==spkr)

    def viewAllSpeakers(self):
        if self.data is None: return
        self.hiddenSpeakers = []
        self.tred.setFilter(lambda x:x['speaker']!=config['sectionSpeakerId'])
        #self.wave.setFilter(lambda x:True)

    # shorcut bindings: join/split
    def splitSegment(self):
        if self.data is None: return
        
        cur = self.tred.textCursor()
        charIdx = cur.position() - cur.block().position()
        segIdx = self.data.getSelection()
        seg = self.data[segIdx]
        lst = seg.toList()

        i_start = seg.getColumnIndex('start')
        t0 = seg[i_start]
        t1 = seg['end']

        i_trans = seg.getColumnIndex('transcript')
        trans = seg[i_trans]

        if charIdx == 0 or charIdx == len(trans) or len(trans) == 0:
            return

        tt = t0 + (t1 - t0) / len(trans) * charIdx

        if tt <= t0 or tt >= t1:
            return

        top1 = self.data.undoStackStatus()[0]
        
        seg['end'] = tt
        lst[i_start] = tt

        seg[i_trans] = trans[:charIdx]
        lst[i_trans] = trans[charIdx:]

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
        charIdx = cur.position()
        para = cur.blockNumber()

        seg1 = self.data[segIdx]
        segIdx2 = None
        seg2 = None
        fileid = seg1['file']
        channel = seg1['channel']
        speaker = seg1['speaker']
        for para in range(para+1,self.tred.document().blockCount()):
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
        cur.setPosition(charIdx)
        self.tred.setTextCursor(cur)

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
    parser.add_option("-r", "--right-to-left", dest="bidi",
                      action="store_true", default=False,
                      help="text goes from right to left")
    parser.add_option("-o", "--output", dest="ofilename",
                      help="save file as FILE and exit", metavar="FILE")
    parser.add_option("-c", "--config", dest="config",
                      help="start with config file FILE", metavar="FILE")
    
    (options, args) = parser.parse_args()
    
    if options.bidi or \
       (len(args)>0 and args[0] == "arabic"):
        bidi = True
    else:
        bidi = False

    w = Xtrans(reverse=bidi)
    w.setWindowTitle(PROGNAM + ": no file")

    if options.config:
        w.menu_Tools_LoadConfigFile(options.config)
        
    if options.filename:
        if options.format == '.tdf':
            w.menu_File_Open(options.filename)
        elif options.format == '.wl.sgm':
            w.menu_File_Import_WeblogSgm(options.filename)
        elif options.format == '.ng.sgm':
            w.menu_File_Import_NewsgroupSgm(options.filename)
        elif options.format == '.nw.sgm':
            w.menu_File_Import_NewswireSgm(options.filename)
        else:
            print >>sys.stderr, "Unkown format:", options.format
            sys.exit(1)
            
        if options.ofilename:
            w.save(options.ofilename, '.tdf')
            sys.exit(0)

    w.resize(800, 500)
    w.show()

    w.statusBar().showMessage("")
    
    app.exec_()

