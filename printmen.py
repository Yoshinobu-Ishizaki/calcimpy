# -*- coding: utf-8 -*-
'''
test program to show various calculation result of xmensur
'''
__version__ = '0.1'

import xmensur as xmn

import argparse

import numpy as np

if __name__ == "__main__" :
    # exec this as standalone program.

    parser = argparse.ArgumentParser(description='Print mensur data.')
    parser.add_argument('-v', '--version', action = 'version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-c','--convert',action = 'store_true',help = 'convert to L,D. L: total length from beginning. D: diameter.')
    parser.add_argument('filepath')

    args = parser.parse_args()

    path = args.filepath
    if path:
        #read mensur file here
        fd = open(path,'r')
        lines = fd.readlines()
        fd.close()

        mentop = xmn.build_mensur( lines )
    
        if not args.convert:
            print('#',path)
            xmn.print_mensur(mentop,True)
        else:
            xmn.print_mensur_ld(mentop)
        
    