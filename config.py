from PyQt4.QtCore import Qt
from keyseqinputdialog import *
import sys
import os
import codecs

__all__ = ['Config', 'config', 'config_description']



config_default = {
    "autosaveInterval":'120.0',
    "defaultFontSize":'15',
    "guidelines":'"qrtr"',
    "targetLang":'"en_US"',
    "sectionSpeakerId":'"__section__"',
    "sectionTypes":'["report","conversational","non-news"]',
    "sectionColors":'["#8888FF","#88FF88","#FFFFAA"]',
    "suSymbols":'["/.","/?","/-","/@"]',
    "suTypes":'["statement","question","incomplete","backchannel"]',
    "suColors":'["#8888FF",Qt.red,"#88FF88","#FFFFAA"]',
    "speakerSidebarWidth":'60',
    "segmentOnDummyAudio":'False',
    "xtransdir":'r"%s"' % os.path.normpath(os.path.expanduser('~')+"/.xtrans"),
    "KB_splitSegment":'Ctrl+Return',
    "KB_joinSegments":'Ctrl+j',
    "KB_deleteSegment":'Ctrl+Delete',
    "KB_insertSegment":'Ctrl+Insert',
    "KB_playRegion":'Alt+Space',
    "KB_playAtRegionEnd":'Alt+Return',
    "KB_playWaveformBegin":'Alt+|',
    "KB_playLastSeconds":'Alt+\\',
    "KB_rewindOneSecond":'Alt+[',
    "KB_forwardOneSecond":'Alt+]',
    "KB_togglePause":'Alt+p',
    "KB_stopPlaying":'Alt+s',
    "KB_markAndPlay":'Alt+m',
    "KB_shrinkAtRightEdge":'Alt+Comma',
    "KB_growAtRightEdge":'Alt+.',
    "KB_shrinkAtLeftEdge":'Ctrl+.',
    "KB_growAtLeftEdge":'Ctrl+Comma',
    "KB_bigShrinkAtRightEdge":'Alt+<',
    "KB_bigGrowAtRightEdge":'Alt+>',
    "KB_bigShrinkAtLeftEdge":'Ctrl+>',
    "KB_bigGrowAtLeftEdge":'Ctrl+<',
    "KB_zoomIn":'Alt+a',
    "KB_zoomOut":'Alt+z',
    "KB_zoomInRegion":'Alt+x',
    "KB_insertSectionBoundary":'Ctrl+i,Ctrl+s',
    "KB_deleteSectionBoundaryLeft":'Ctrl+d,Ctrl+s',
    "KB_editSectionBoundaryTypeLeft":'Ctrl+e,Ctrl+s',
    "KB_insertSuStatement":'Ctrl+i,Ctrl+u,Ctrl+s',
    "KB_insertSuQuestion":'Ctrl+i,Ctrl+u,Ctrl+q',
    "KB_insertSuIncomplete":'Ctrl+i,Ctrl+u,Ctrl+i',
    "KB_insertSuBackchannel":'Ctrl+i,Ctrl+u,Ctrl+b',
    "KB_deleteSU":'Ctrl+d,Ctrl+u',
    "KB_undo": 'Ctrl+z',
    "KB_redo": 'Ctrl+y',
    "FSKB_Ctrl_L":'("Ctrl+L"," <laugh> * </laugh> ")',
    "FSKB_Ctrl_H":'("Ctrl+H"," <cough/> ")',
    "FSKB_Ctrl_S":'("Ctrl+S"," <sneeze/> ")',
    "FSKB_Ctrl_B":'("Ctrl+B"," <breath/> ")',
    "FSKB_Ctrl_P":'("Ctrl+P"," <lipsmack/> ")',
    "FSKB_Ctrl_G":'("Ctrl+G"," <background> * </background>")',
    "FSKB_Ctrl_F":'("Ctrl+F"," <foreign lang=\\"English\\"> * </foreign> ")',
    "FSKB_Ctrl_N":'("Ctrl+N"," <lname/> ")'
    }

config_description = {
    "defaultFontSize":"Default text font size",
    "guidelines":"Annotation guidelines to be used",
    "targetLang":"Language to be used in transcription",
    "sectionSpeakerId":"Speaker id for section record",
    "sectionTypes":"List of section types",
    "sectionColors":"List of colors for section types",
    "suSymbols":"List of SU symbols",
    "suTypes":"List of SU types",
    "suColors":"List of colors for SUs",
    "speakerSidebarWidth":"Width of speaker side bar",
    "segmentOnDummyAudio":"Allow/disallow creating segment on the box display",
    "xtransdir":"Directory to store application information",
    "KB_splitSegment":"Split segment into two",
    "KB_joinSegments":"Join the current and following segments",
    "KB_deleteSegment":"Delete current segment",
    "KB_insertSegment":"Insert a segment for the selected region",
    "KB_playRegion":"Play current region",
    "KB_playAtRegionEnd":"Play from the right edge of current selection",
    "KB_playWaveformBegin":"Play from the begining of current waveform window",
    "KB_playLastSeconds":"Play just ending part of current selection",
    "KB_rewindOneSecond":"Rewind one second",
    "KB_forwardOneSecond":"Fast-forward one second",
    "KB_togglePause":"Pause/resume playback",
    "KB_stopPlaying":"Stop playback",
    "KB_markAndPlay":"Toggle between two actions: play/begin_selection vs. stop_playing/finalize_selection",
    "KB_shrinkAtRightEdge":"Shrink current selection; move right edge to the left by one pixel",
    "KB_growAtRightEdge":"Grow current selection; move right edge to the right by one pixel",
    "KB_shrinkAtLeftEdge":"Shrink current selection; move left edge to the right by one pixel",
    "KB_growAtLeftEdge":"Grow current selection; move left edge to the left by one pixel",
    "KB_bigShrinkAtRightEdge":"Fast-shink current selection; move right edge to the left by a couple of pixels",
    "KB_bigGrowAtRightEdge":"Fast-grow current selection; move right edge to the right by a couple of pixels",
    "KB_bigShrinkAtLeftEdge":"Fast-shrink current selection; move left edge to the right by a couple of pixels",
    "KB_bigGrowAtLeftEdge":"Fast-grow current selection; move left edge to the left by a couple of pixels",
    "KB_zoomIn":"Zoom in where the cursor is placed",
    "KB_zoomOut":"Zoom out where the cursor is placed",
    "KB_zoomInRegion":"Make current selection fit the current waveform window",
    "KB_insertSectionBoundary":"Insert section boundary",
    "KB_deleteSectionBoundaryLeft":"Delete section boundary on the left of the cursor",
    "KB_editSectionBoundaryTypeLeft":"Edit section boundary type",
    "KB_insertSuStatement":"Set SU type (statement) for current segment",
    "KB_insertSuQuestion":"Set SU type (question) for current segment",
    "KB_insertSuIncomplete":"Set SU type (incomplete) for current segment",
    "KB_insertSuBackchannel":"Set SU type (backchannel) for current segment",
    "KB_deleteSU":"Unset SU type for current segment",
    "KB_undo": "Undo previous operation",
    "KB_redo": "Redo an undone operation",
##     "KB_insertTagLaugh":"Insert <laugh></laugh> in text",
##     "KB_insertTagCough":"Insert <cough/> in text",
##     "KB_insertTagSneeze":"Insert <sneeze/> in text",
##     "KB_insertTagBreath":"Insert <breath/> in text",
##     "KB_insertTagLipsmack":"Insert <lipsmack/> in text",
##     "KB_insertTagBackground":"Insert <background></background> in text",
##     "KB_insertTagForeign":"Insert <foreign language=\"...\"></foreign> in text",
##     "KB_insertTagLastName":"Insert <lname/> in text",    
}

if sys.platform == 'win32':
    config_default["KB_insertSegment"] = 'Ctrl+n'
    config_default["KB_deleteSegment"] = 'Ctrl+D'
    config_default["KB_playRegion"] = 'Tab'

class Config(dict):
    def __getitem__(self, k):
        """
        Return the interpreted value.
        """
        #try:
        if k[:3] == 'KB_':
            v = dict.__getitem__(self, k)
            return str2qkeyseq(v)
        else:
            return eval(dict.__getitem__(self, k))
##         except Exception, e:
##             print "WARNING: error in configuration for entry %s; %s" % (`k`,str(e))
##             raise e
##             return None

    def rawValue(self, k):
        return dict.__getitem__(self, k)

    def read(self, f):
        f = codecs.getreader('utf-8')(f)
        for i,l in enumerate(f):
            l = l.strip()
            if not l: continue
            if l[:2] == ';;': continue
            try:
                k,v = l.split("\t")
            except ValueError:
                print "WARNING: error in configuration file at line %d" % (i+1)
                continue
            if k not in config_default and not k.startswith('FSKB_'):
                print "WARNING: unknown configuration entry %s" % `k`
                continue
            if k.startswith('FSKB_'):
                try:
                    seq = eval(v)[0]
                except SyntaxError:
                    print "WARNING: invalid config value at line %d:", (i+1,v)
                    continue
                k = 'FSKB_'+str2objname(seq)
            if k in self:
                print "WARNING: duplicated entry for %s; the exsiting value will be overwritten" % `k`
            self[k] = v

    def save(self, f):
        f = codecs.getwriter("utf-8")(f)
        keys = self.keys()
        keys.sort()
        for k in keys:
            f.write("%s\t%s\n" % (k,self.rawValue(k)))

    def reset(self):
        self.update(config_default)
        
config = Config(config_default)
config_default = Config(config_default)
#config.read(_configs.split("\n"))

