# -*- coding: utf-8 -*-
'''
calcprs
pressure calculation program for air column ( wind instruments )
'''
__version__ = '1.0.0'

import xmensur
import imped

import argparse
import sys
import os.path

import numpy as np

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='pressure calculation for air column')
    parser.add_argument('-v', '--version', action = 'version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-f', '--freq', default = '440.0', help = 'frequency to calculate, default 440 Hz.')
    parser.add_argument('-p', '--pressure', default = '60.0', help = 'pressure at starting point, default 60dBSPL.')
    parser.add_argument('-T', '--from_tail', action = 'store_true', help = 'calculate from tail if true, default false.')
    parser.add_argument('-o','--output',default = '', help = 'output filename, stdout is used when "-"' )
    parser.add_argument('-s','--step',default = '1', help = 'slice mensur by step, default 1mm.' )
    
    parser.add_argument('filepath')

    args = parser.parse_args()
    
    path = args.filepath

    if path:
        mentop = xmensur.read_mensur_file(path)

        stp = float(args.step)/1000.0 # mm unit
        xmensur.slice_mensur(mentop, stp)

        # calc impedance first
        fq = float(args.freq)
        wf = np.pi*2*fq
        p0 = 2.0e-5 # 20 micro Pa is a basic pressure for dBSPL
        imped.input_impedance(wf,mentop)

        pdB = float(args.pressure)
        p = p0 * np.power(10.0, pdB/20.0 ) # dBSPL -> Pa

        # calc pressure from end position
        imped.calc_pressure(wf,mentop,endp = p, from_tail = args.from_tail)

        # set file output
        if args.output == '-':
            fout = sys.stdout
        elif args.output == '':
            # default *.prs
            rt, ext = os.path.splitext(path)
            fout = open( rt + '.prs','w')
        else:
            fout = open(args.output,'w') 

        sys.stdout = fout

        # print pressure
        print('#{0}, freq: {1}(Hz), p: {2}(dBSPL), from_tail: {3}'.format(path,args.freq,args.pressure, args.from_tail))
        xmensur.print_pressure(mentop)
    