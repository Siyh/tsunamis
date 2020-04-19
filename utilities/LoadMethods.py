# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 15:36:06 2020

@author: Marcus
"""
import os

def LoadInput(path):
    if not path: path = os.path.join(path, "input.txt")
    if not os.path.exists(path): return
    parameters={}
    
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                if line[0] != '!':
                    try:
                        k, vs = line.split(' = ')
                    except:
                        print('Odd line: ' + line)
                        continue
                    try:
                        v = float(vs) if '.' in vs else int(vs)
                    except:
                        if vs == 'T':
                            v = True
                        elif vs == 'F':
                            v = False
                        else:
                            v = vs
                    parameters[k] = v
                    
    return parameters
                

                
                
    