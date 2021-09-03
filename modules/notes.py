#!/usr/bin/python
# -*- coding: utf-8 -*-
""" notes.py
Definition of Notes class
Todo:
    * Create docstring
"""

import numpy as np
import js2py
import chardet
import math
import pdb
import random
from contextlib import closing
from bs4 import BeautifulSoup
import sys,os

# my modules
sys.path.append(os.path.dirname(__file__))
import utils

# for debug
import matplotlib.pyplot as plt
import os

class Notes:
    """ Notes
    Load (song_title).html and convert notes to np.array
    Attributes
        quaterNoteLen: length of quater Note
        hcn: 0 or 1, 1 mean HCN
        printOn: if True, print Notes-On-timing on Screen for debug
        maxDensityNotesBar: numpy array of bar whitch has highest density
        maxDensity: max density
        difficulty: score difficulty in (n, h, a, l)
        playmode: "sp" or "dp"
        jsbody: string of loaded javascript
        measure: number of bars in song
        ln, sp, dp, c1, c2, cn, tc: notes infomation before convert
        keyNum: number of keys in single play
        DEFLEN: default length of bar
        context: evaled jsbody
        notesArrayList: list of notesArray of each bars
        bpmArrayList: list of bpmArray of each bars
        notesArray: numpy array of converted Notes
        bpmArray: numpy array of converted bpm
    """
    def __init__(self, path, keyNum=8, deflen=192, difficulty="a", playmode="dp", printOn=False):
        self.quaterNoteLen = deflen // 4
        self.hcn = 0
        self.printOn = printOn
        self.maxDensityNotesBar, self.maxDensity = 0, 0
        self.difficulty, self.playmode = difficulty, playmode
        self.jsbody = self._parseHTML(path)
        self.measure = self._getMeasure() # measure is necessary before header analysis
        self.ln, self.sp, self.dp, self.c1, self.c2, self.cn, self.tc = self._initNotes(self.measure, 7)
        self.keyNum, self.DEFLEN = keyNum, deflen
        self.context = self._analyze()
        self.notesArrayList, self.bpmArrayList = [], []
        self.notesArray, self.bpmArray = None, None

    def _parseHTML(self, htmlpath):
        enc = utils.checkEncoding(htmlpath)
        if enc != "utf-8": enc = "shift_jis"
        with open(htmlpath, "r", encoding=str(enc)) as f:
            soup = BeautifulSoup(f, "lxml")
        js_text = soup.text
        sol_char = "<!--\n"
        eol_char = "hd();"
        eol_char2 = "w("
        sol = js_text.find(sol_char)
        eol = min(js_text.find(eol_char), js_text.find(eol_char2))
        jsbody = js_text[sol + len(sol_char):eol]
        return jsbody

    def _getMeasure(self):
        findStr = "measure="
        idx = self.jsbody.find(findStr) + len(findStr)
        diff = self.jsbody[idx:].find(";")
        measure = self.jsbody[idx:idx + diff]
        return int(measure)

    def _analyze(self):
        self.genre, self.title, self.bpm = "", "", ""
        if self.playmode == "sp":
            k = 1
        else: # dp
            k = 0
        if self.difficulty == "a": # another
            a, l, g, hps, pty, kuro = 1, 0, 0, 0, 0, 0
        elif self.difficulty == "l": # legendaria
            a, l, g, hps, pty, kuro = 1, 0, 0, 0, 0, 1
        elif self.difficulty == "h": # hyper
            a, l, g, hps, pty, kuro = 0, 0, 0, 1, 0, 0
        else: # normal
            a, l, g, hps, pty, kuro = 0, 1, 0, 0, 0, 0
        gap, sc32, s = 8, [], "00000" # Used in javascript only

        dic = {"ln":self.ln, "tc":self.tc, "cn":self.cn, "LNDEF":self.DEFLEN*2, \
               "genre":self.genre, "title":self.title, "bpm":self.bpm, \
               "a":a, "l":l, "k":k, "g":g, "hps":hps, "pty":pty, "kuro":kuro, \
               "ln":self.ln, "sp":self.sp, "dp":self.dp, \
               "tc":self.tc, "c1":self.c1, "c2":self.c2, \
               "cn":self.cn, "hcn":self.hcn, \
               "gap":gap, "sc32":sc32, "s":s, "document":False}
        context = js2py.EvalJs(dic)
        self.jsbody = self.jsbody.replace("document.all", "document")
        context.execute(self.jsbody)
        self.ln, self.tc, self.cn, self.DEFLEN, self.genre, self.title, self.bpm = \
            context.ln, context.tc, context.cn, context.LNDEF, context.genre, context.title, context.bpm
        self.DEFLEN = self.DEFLEN // 2 # my DEFLEN = 192, textage LNDEF = 384
        self.ln = [x // 2 if x else self.DEFLEN for x in self.ln] # 同上
        if self.printOn: print("GENRE : {0}\nTITLE : {1}\nBPM : {2}".format(self.genre, self.title, self.bpm))

        return context

    def _getStartBPM(self):
        startBPM = ""
        for curBPM in self.tc:
            if curBPM:
                startBPM = curBPM[0][:3]
                break
        if startBPM == "":
            startBPM = self.bpm
        return startBPM

    def _initNotes(self, measure, numNotesType=1):
        """
        return instance of notes placement like 'sp', 'dp, 'c1', ...
        args
            mesure : Number of bar in the song
            numNotesType : Number of instance -> if you need 'sp' and 'dp', numNotesType = 2
        """
        return [[list() for x in range(measure)] for x in range(numNotesType)]

    def setOptions(self, lkey=1234567, rkey=1234567, lrnd=False, rrnd=False, db=False, flip=False, autoSC=False):
        if db:
            self.notesArray[8:-1, :, :] = self.notesArray[1:8, :, :]
            self.notesArray[-1, :, :] = self.notesArray[0, :, :]
        if lrnd: lkey = ''.join(random.sample("1234567", self.keyNum-1))
        if rrnd: rkey = ''.join(random.sample("1234567", self.keyNum-1))
        if flip:
            self.notesArray[1:8, :, :], self.notesArray[8:-1, :, :] = self.notesArray[8:-1, :, :], self.notesArray[1:8, :, :]
            self.notesArray[[0, -1], :, :] = self.notesArray[[-1, 0], :, :]
        if autoSC: self.notesArray[[0, -1], :, :] = 0
        dstkey = [int(x) for x in str(lkey)] + [int(x) + self.keyNum - 1 for x in str(rkey)]
        self.notesArray[1:-1, :, :] = self.notesArray[dstkey, :, :]

    def _isSameLen(self):
        c1len, c2len, splen, dplen = len(self.context.c1), len(self.context.c2), len(self.context.sp), len(self.context.dp)
        return c1len == c2len == splen == dplen

    def _zeroPadding(self, arr, length=192, axis=1):
        dist_shape = list(arr.shape) # 16, srcLen, 3
        dist_shape[axis] =  length - arr.shape[axis] % length
        return np.concatenate([np.zeros(dist_shape), arr], axis=axis)

    def convertNotes(self, printOn=False):
        if printOn: self.printOn = True
        if not self._isSameLen():
            self.context.c1, self.context.c2 = self._initNotes(len(self.context.sp), 2)
        currentBPM = self._getStartBPM()
        for idx, (spp, dpp, c1p, c2p, lnBar, tcp) in \
                enumerate(zip(self.context.sp, self.context.dp, self.context.c1, self.context.c2, self.ln, self.tc)):
            notesArrayBar = np.zeros((16, lnBar, 3))
            bpmArrayBar = np.zeros((lnBar))
            if self.printOn: print("bar:{0}".format(idx))
            # normal notes
            notesType = 0
            if spp:
                notesArrayBar += self._convertNotesBar(spp, lnBar)
            if dpp:
                notesArrayBar += self._convertNotesBar(dpp, lnBar, 2)
            # charge notes
            if c1p is not None:
                notesArrayBar += self._convertChargeNotesBar(c1p, lnBar, 1)
            if c2p is not None:
                notesArrayBar += self._convertChargeNotesBar(c2p, lnBar, 2)
            # bpm
            if not tcp:
                bpmArrayBar[:] = int(currentBPM)
            else:
                for sofranInfo in tcp:
                    newBPM = sofranInfo[:3]
                    pos = int(sofranInfo[3:]) * (3/2) # 整合性を取る，textageのフォーマットよくわからん -> 画面表示用の数字だからか
                    bpmArrayBar[int(pos):] = int(newBPM)
                    currentBPM = newBPM
            density = self._calcMaxDensity(notesArrayBar, bpmArrayBar, lnBar)
            if self.maxDensity < density: self.maxDensity, self.maxDensityNotesBar = density, idx
            self.notesArrayList.append(notesArrayBar)
            self.bpmArrayList.append(bpmArrayBar)
        self.notesArray = self._zeroPadding(np.concatenate(self.notesArrayList, 1), length=192) # 16, length x N, 3
        self.bpmArray = self._zeroPadding(np.concatenate(self.bpmArrayList, 0), length=192, axis=0) # length x N
        if self.playmode == "sp":
            self.setOptions(db=True)

    def _convertChargeNotesBar(self, cns, lnBar, playside):
        CNDEFLEN = 128
        notesArrayBar = np.zeros((16, lnBar, 3))
        posRate = lnBar / CNDEFLEN
        notesType = 1 if not self.hcn else 2
        for cn_split in cns:
            startPoint = int(cn_split[1] * posRate)
            if len(cn_split) > 2 and cn_split[2]:
                keyLength = int(cn_split[2] * posRate)
            else:
                keyLength = self._getDist(4)
            for key in str(cn_split[0]):
                if playside == 1:
                    key = int(key)
                else:
                    key = 15 if int(key) == 0 else int(key) + self.keyNum - 1
                self._printNoteInfo(playside, key, startPoint, cnlen=keyLength)
                notesArrayBar[key, startPoint:startPoint+keyLength, notesType] = 1
        return notesArrayBar

    def _convertNotesBar(self, notes, lnBar, playside=1):
        """
        return numpy array whitch shpae (16, lnBar, 3) of notes in bar (width x height x ch)
            notes : notes information text like "0004081020408000"(hex)
            playside : 1p:1, 2p:2
        """
        if notes[0] == "#": # #構文
            notesArrayBar = self._sharp2array(notes, lnBar, playside)
        else: # #構文以外
            notesArrayBar = self._number2array(notes, lnBar, playside)

        return notesArrayBar

    def _number2array(self, notes, lnBar, playside):
        notesType = 0
        notesArrayBar = np.zeros((16, lnBar, 3))
        if notes[0] == "x": # 一部だけ間隔が変わるやつ
            # xAAAYY@BBOOOO ... AA/2で小節の分割数（len）を指定，YYは普通のノーツ指定，@直後のBBで@-@間のノーツ間隔を指定
            divNum = int(notes[1:4], 16) // 2
            height = lnBar // divNum
            noteSplit = []
            divs = []
            div = 0
            charIdx = 4
            while True:
                if notes[charIdx] is "@":
                    div += int(notes[charIdx+1:charIdx+3], 16)
                    charIdx += 3
                notesInBar = int(notes[charIdx:charIdx+2], 16) if charIdx < (len(notes)-1) else 0
                noteSplit.append(notesInBar)
                divs.append(div)
                div = 1
                charIdx += 2
                if charIdx >= (len(notes)-1): break
        else:
            # only number
            lenOfBar = len(notes)
            divNum = lenOfBar // 2 # 2桁で一つのタイミングのノーツを指定しているから
            height = lnBar // divNum
            divs = [0 if x==0 else 1 for x in range(divNum)]
            noteSplit = [int(notes[idx:idx+2], 16) for idx in range(0, len(notes), 2)]

        idx = 0
        for noteBin, div in zip(noteSplit, divs):
            idx += div
            if noteBin == 0: continue
            for keyIdx in range(self.keyNum):
                noteOn = (noteBin >> keyIdx) & 1
                if playside == 2:
                    keyIdx = keyIdx + self.keyNum - 1  if keyIdx != 0 else 15
                if noteOn:
                    self._printNoteInfo(playside, keyIdx, idx*height)
                    notesArrayBar[keyIdx, height*idx, notesType] = 1

        return notesArrayBar


    def _sharp2array(self, notes, lnBar, playside=1):
        notesType = 0
        notesArrayBar = np.zeros((16, lnBar, 3))
        b64="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        charIdx = 1
        multiScAssign = False
        ### Define
        divNums = {"B":2, "Q":4, "O":8, "X":16, "Z":32, "S":6, "T":12, "U":24}
        divNumsConst = {"C":2, "R":4, "P":8}
        ###
        while charIdx < len(notes):
            keyOns = ""
            scAssign, uniNoteAssign, uniChordAssign, doBackBeat, constNotesAssign = False, False, False, False, False
            switchChar = notes[charIdx]
            if self.printOn: print("    switch : {}".format(switchChar))
            if switchChar in divNums:
                divNum = divNums[switchChar]
            elif switchChar.upper() in divNums:
                divNum = divNums[switchChar.upper()]
                doBackBeat = True
            elif switchChar in divNumsConst:
                divNum = divNumsConst[switchChar]
                constNotesAssign = True
            elif switchChar.upper() in divNumsConst:
                divNum = divNumsConst[switchChar.upper()]
                doBackBeat = True
                constNotesAssign = True
            elif switchChar in "1234567":
                uniNoteAssign = True
                charIdx += 1
                uniNoteChar = notes[charIdx:charIdx+2]
                keyOns += switchChar
                height = len(b64) * b64.find(uniNoteChar[0]) + 1 * b64.find(uniNoteChar[1])
                height = height // 2
                charIdx += len(uniNoteChar)
            elif switchChar in "89":
                uniChordAssign = True
                charIdx += 1
                keyOnsChar = notes[charIdx]
                if switchChar in "9":
                    keyOns += "1"
                keyOns += "".join([str(x + 2) for x in range(self.keyNum) if b64.find(keyOnsChar)>>x & 1])
                uniNoteChar = notes[charIdx+1:charIdx+3]
                height = len(b64) * b64.find(uniNoteChar[0]) + 1 * b64.find(uniNoteChar[1])
                height = height // 2
                charIdx += len(uniNoteChar) + 1
            elif switchChar == "_": # scratch
                scAssign = True
                charIdx += 1
                scNotesChar = "AA" if charIdx >= len(notes) else notes[charIdx:]
                height = len(b64) * b64.find(scNotesChar[0]) + 1 * b64.find(scNotesChar[1])
                height = height // 2 # my DEFLEN = 192, textage LNDEF = 384
                keyOns += "0"
                charIdx += len(scNotesChar)
            elif switchChar == "-": # 1/6か1/2か, scratchの細かいやつ
                multiScAssign = True
                charIdx += 1
                continue
            else:
                print("  dummy")
                pdb.set_trace()
                break

            ### note Assignment
            if uniNoteAssign or scAssign:
                for keyOn in keyOns:
                    keyOn = int(keyOn)
                    if playside == 2:
                        keyOn = keyOn + self.keyNum-1 if not keyOn == 0 else 15
                    noteTiming = height
                    notesArrayBar[keyOn, noteTiming, notesType] = 1
                    self._printNoteInfo(playside, keyOn, noteTiming)
            elif multiScAssign or constNotesAssign:
                charIdx += 1
                height = self._getDist(divNum)
                lenStr = math.ceil(lnBar / (height * 6)) # divNum // 6 + 1
                if multiScAssign:
                    if constNotesAssign:
                        keyOns = "1" * (lnBar // height)
                    else:
                        for noteChar in notes[charIdx:charIdx+lenStr]:
                            keyOns += "{0:06b}".format(int(b64.find(noteChar)))
                        charIdx += lenStr
                else:
                    keyOns = notes[charIdx] * (lnBar // height)
                    charIdx += 1
                for idx, keyOn in enumerate(keyOns):
                    if keyOn == "0": continue
                    if multiScAssign:
                        keyOn = 0 if playside == 1 else 15
                    else:
                        keyOn = int(keyOn) if playside == 1 else int(keyOn) + self.keyNum - 1
                    noteTiming = height * idx if not doBackBeat else (height // 2) + (height * idx)
                    notesArrayBar[keyOn, noteTiming, notesType] = 1
                    self._printNoteInfo(playside, keyOn, noteTiming)
            elif uniChordAssign:
                for keyOn in keyOns:
                    keyOn = int(keyOn) if playside == 1 else int(keyOn) + self.keyNum - 1
                    notesArrayBar[keyOn, height, notesType] = 1
                    self._printNoteInfo(playside, keyOn, height)

            else:
                # Make KeyOns
                charIdx += 1
                height = self._getDist(divNum)
                lenStr = math.ceil(lnBar / (height * 2))
                for noteChar in notes[charIdx:charIdx+lenStr]:
                    keyOns += "{0:02o}".format(b64.find(noteChar))
                charIdx += lenStr
                # Assignment
                for idx, keyOn in enumerate(keyOns):
                    if keyOn == "0": continue
                    keyOn = int(keyOn)
                    if playside == 2:
                        keyOn = keyOn + self.keyNum - 1
                    noteTiming = height * idx if not doBackBeat else (height // 2) + (height * idx)
                    notesArrayBar[int(keyOn), noteTiming, notesType] = 1
                    self._printNoteInfo(playside, keyOn, noteTiming)

        return notesArrayBar

    def _getDist(self, div):
        # See Note No.2
        return (self.quaterNoteLen * 4) // div

    def _printNoteInfo(self, playside, key, bar, cnlen=0):
        if not self.printOn: return
        if int(playside) == 2:
            key -= (self.keyNum - 1)
        p1SC = int(key) == 0
        p2SC = (int(key) == 8 and playside == 2)
        if p1SC or p2SC: key = "S"
        cnComment = " Charge length:{0}".format(cnlen) if cnlen > 0 else ""
        print("    noteOn! side:{0}, key:{1}, beat:{2}".format(playside, key, bar) + cnComment)

    def _calcMaxDensity(self, array, bpmArray, lnBar=192, weights=(1, 16/192, 16*2/192)):
        array = array * bpmArray.reshape((1, -1, 1))
        densities = np.array([array[:,:,idx].sum()/(lnBar/self.quaterNoteLen)/60  for idx in range(3)])
        density = np.sum(densities * weights)
        return density

    def getMaxDensityNotesArray(self, length=None, withBPM=False, numArray=1):
        if not length: return self.notesArrayList[self.maxDensityNotesBar]
        arrs = [None for x in range(numArray)]
        arrsBPM = [None for x in range(numArray)]
        numBar = self.notesArray.shape[1]//length
        densities = np.zeros((numBar))
        for idx in range(numBar):
            notesIdx = idx * length
            densities[idx] = self._calcMaxDensity(self.notesArray[:,notesIdx:notesIdx+length,:],
                                                 self.bpmArray[notesIdx:notesIdx+length])
        sortedIdxs = np.argsort(densities)[::-1]
        for idx in range(numArray):
            sortedIdx = sortedIdxs[idx] * length
            arrs[idx] = self.notesArray[:,sortedIdx:sortedIdx+length,:]
            arrsBPM[idx] = self.bpmArray[sortedIdx:sortedIdx+length]
        if withBPM:
            return arrs, arrsBPM
        else:
            return arrs

if __name__ == "__main__":
    testp = input("Enter html path to encode : ")
    tn = Notes(testp)
    tn.convertAllNotes()
