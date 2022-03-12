# -*- coding: utf-8 -*-
"""

read cfg file
@author: huang

"""

import pandas as pd
import os

class configuration(object):
    def __init__(self):
        self.filename = ''
        self.cappingMolPair = []
        self.cappingBonds = []
        self.unrctStruct = []
        self.monInfo = ''
        self.croInfo = ''
        self.boxSize = ''
        self.monR_list = ''
        self.croR_list = ''
        self.cutoff = ''
        self.bondsRatio = ''
        self.maxBonds = ''
        self.HTProcess = ''
        self.CPU = ''
        self.GPU = ''
        self.trials = ''
        self.reProject = ''
        self.rctInfo = ''
        self.stepwise = ''
        self.cappingBonds = []
        self.boxLimit = 1
        self.layerConvLimit = 1
        self.layerDir       = ''

    @classmethod
    def readCfgFile(cls,filename):
        inst=cls()
        inst.filename=filename
        baseList=[]
        # read all lines, append each to baseList.
        # skip any lines beginning with '#'
        # and ignore anything after '#' on a line
        with open(filename,'r') as f:
            for l in f:
                if l[0]!='#':
                    try:
                        l=l[:l.index('#')].strip()
                    except:
                        pass
                    baseList.append(l)
        # set all variables
        baseDict={}
        keyCounts={}
        for l in baseList:
            if '=' in l:
                k,v=[a.strip() for a in l.split('=')]
                if not k in keyCounts:
                    keyCounts[k]=0
                keyCounts[k]+=1
                if ',' in v:
                    v=[a.strip() for a in v.split(',')]
                # repeated keys build lists
                if keyCounts[k]>1:
                    if keyCounts[k]==2:
                        baseDict[k]=[baseDict[k]]
                    baseDict[k].append(v)
                else:    
                    baseDict[k]=v
        inst.baseDict=baseDict

        for k,v in inst.baseDict.items():
            if k.startswith('mol'):
                inst.cappingMolPair.append(v)
                inst.unrctStruct.append(v[1])
            elif k.startswith('cappingBond'):
                for cb in v:
                    inst.cappingBonds.append(cb)

        rctInfo = []
        for line in baseList: # Reaction Info
            if '+' in line:
                rct = [x.split() for x in line.split('+')]
                rctInfo.append(rct)
        inst.rctInfo=rctInfo
        return inst

    def setName(self, filename):
        # this method will be superseded
        self.name = filename
        
    
    def readCfg(self):
        # this method will be superseded
        monInfo = []
        croInfo = []
        
        monNum = ''
        monR_list = {}
        croNum = ''
        croR_list = {}
        
        df = pd.read_csv(self.name, header=None, sep='\n', skip_blank_lines=True)
        df = df[df[0].str.startswith('#') == False]
        baseList = df.iloc[:][0]

        # Get capping parameters
        i = 1
        while i < 10:
            for l1 in baseList:
                if 'mol{}'.format(i) in l1:
                    tmpMolPair = l1.split('=')[1].split(',')
                    self.cappingMolPair.append(tmpMolPair)
                    self.unrctStruct.append(tmpMolPair[1].strip())
            i += 1

        for l1 in baseList:
            if l1.startswith('cappingBonds'):
                self.cappingBonds.append(l1.split('=')[1].split(','))

        # Get monomer and crosslinker info
        i = 1
        while i < 5:
            for l1 in baseList:
                if 'monName{}'.format(i) in l1:
                    monName = l1.split('=')[1].strip(' ')
                    for l2 in baseList:
                        key1 = 'monNum{}'.format(i)
                        if key1 in l2:
                            monNum = l2.split('=')[1].strip(' ')
                    
                    for l2 in baseList:
                        key2 = 'mon{}R_list'.format(i)
                        if key2 in l2:
                            monR_list_tmp = l2.split('=')[1].strip(' ').split('#')[0].split(',')
                    
                    for l2 in baseList:
                        key3 = 'mon{}R_rNum'.format(i)
                        if key3 in l2:
                            monR_rNum = l2.split('=')[1].strip(' ').split('#')[0].split(',')
                    
                    for l2 in baseList:
                        key4 = 'mon{}R_rct'.format(i)
                        if key4 in l2:
                            monR_rct = l2.split('=')[1].strip(' ').split('#')[0].split(',')

                    for l2 in baseList:
                        key4 = 'mon{}R_group'.format(i)
                        if key4 in l2:
                            monR_group = l2.split('=')[1].strip(' ').split('#')[0].split(',')

                    for idx in range(len(monR_list_tmp)):
                        monR_list_tmp[idx] = [monR_list_tmp[idx].strip(), monR_rNum[idx].strip(),
                                              monR_rct[idx].strip(), monR_group[idx].strip()]
                    
                    monInfo.append([i, monName, monNum, monR_list_tmp])
                    monR_list[monName] = monR_list_tmp
            i += 1

        i = 1
        while i < 5:
            for l1 in baseList:
                if 'croName{}'.format(i) in l1:
                    croName = l1.split('=')[1].strip(' ')
                    for l2 in baseList:
                        key1 = 'croNum{}'.format(i)
                        if key1 in l2:
                            croNum = l2.split('=')[1].strip(' ')
                    
                    for l2 in baseList:
                        key2 = 'cro{}R_list'.format(i)
                        if key2 in l2:
                            croR_list_tmp = l2.split('=')[1].strip(' ').split('#')[0].split(',')
                                                
                    for l2 in baseList:
                        key3 = 'cro{}R_rNum'.format(i)
                        if key3 in l2:
                            croR_rNum = l2.split('=')[1].strip(' ').split('#')[0].split(',')
                    
                    for l2 in baseList:
                        key4 = 'cro{}R_rct'.format(i)
                        if key4 in l2:
                            croR_rct = l2.split('=')[1].strip(' ').split('#')[0].split(',')

                    for l2 in baseList:
                        key4 = 'cro{}R_group'.format(i)
                        if key4 in l2:
                            croR_group = l2.split('=')[1].strip(' ').split('#')[0].split(',')

                    for idx in range(len(croR_list_tmp)):
                        croR_list_tmp[idx] = [croR_list_tmp[idx].strip(), croR_rNum[idx].strip(),
                                              croR_rct[idx].strip(), croR_group[idx].strip()]
                                                
                    croInfo.append([i, croName, croNum, croR_list_tmp])
                    croR_list[croName] = croR_list_tmp
            i += 1

        reProject = '' # para could be missing in the options file

        for line in baseList: # Basic Info
            if 'boxSize' in line:
                boxSize = line.split('=')[1].strip(' ').split()    
            if 'cutoff' in line:
                cutoff = float(line.split('=')[1].strip(' '))
            if 'bondsRatio' in line:
                bondsRatio = line.split('=')[1].strip(' ')
            if 'HTProcess' in line:
                HTProcess = line.split('=')[1].strip(' ')
            if 'CPU' in line:
                CPU = line.split('=')[1].strip(' ')
            if 'GPU' in line:
                GPU = line.split('=')[1].strip(' ')
            if 'trials' in line:
                trials = line.split('=')[1].strip(' ')
            if 'reProject' in line:
                reProject = line.split('=')[1].strip(' ')
            if 'stepwise' in line:
                tmpStr =  line.split('=')[1]
                stepwise = tmpStr.split(',')
            if 'boxLimit' in line:
                boxLimit = line.split('=')[1].strip(' ')
            if 'boxDir' in line:
                boxDir = line.split('=')[1].strip(' ')
            if 'layerConvLimit' in line:
                layerConvLimit = line.split('=')[1].strip(' ')
        rctInfo = []
        for line in baseList: # React Info
            if '+' in line:
                rct = [x.split() for x in line.split('+')]
                rctInfo.append(rct)
            
        self.monInfo = monInfo
        self.croInfo = croInfo
        self.boxSize = boxSize
        self.monR_list = monR_list
        self.croR_list = croR_list
        self.cutoff = cutoff
        self.bondsRatio = bondsRatio
        self.rctInfo = rctInfo
        try:
            self.CPU = CPU
        except:
            self.CPU = 0
        try:
            self.GPU = GPU
        except:
            self.GPU = 0
        self.trials = trials
        self.HTProcess = HTProcess
        self.reProject = reProject
        self.stepwise = stepwise
        self.boxLimit = boxLimit
        self.layerDir = boxDir
        self.layerConvLimit = layerConvLimit
        
if __name__ == '__main__':
    pass
