# -*- coding: utf-8 -*-
'''
test program to show various calculation result of xmensur
'''
__version__ = '0.1'

import xmensur
import xmenParser as prs
import xmenCalc

import argparse

import numpy as np

if __name__ == "__main__" :
    # exec this as standalone program.

    parser = argparse.ArgumentParser(description='Xmensur test program.')
    parser.add_argument('-v', '--version', action = 'version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-m', '--minfreq', default = '0.0', help = 'minimum frequency to calculate.')
    parser.add_argument('-M', '--maxfreq', default = '2000.0', help = 'maximum frequency to calculate.')
    parser.add_argument('-s','--stepfreq', default = '2.5', help = 'step frequency for calculation.')
    parser.add_argument('-t','--temperature', default = '24.0', help = 'air temperature (celsius).')
    parser.add_argument('-R','--radiation',choices = ['PIPE','BAFFLE','NONE'], default = 'PIPE', help = 'type of calculation of radiation.')
    parser.add_argument('-C','--calculation',choices = ['II','RI'], default = 'II', help = 'type of calculation. Input Impedance(default)/Radiation Impedance.')
    parser.add_argument('-P','--print_mensur',action = 'store_true',help = 'print out mensur data.')
    parser.add_argument('filepath')

    args = parser.parse_args()

    # debug
    # print(vars(args))

    path = args.filepath
    if path:
        #read mensur file here
        fd = open(path,'r')
        lines = fd.readlines()
        fd.close()

        mentop = prs.build_mensur( lines )
    
        # set calculation conditions
        xmenCalc.set_params(temperature = float(args.temperature), minfreq = float(args.minfreq), \
        maxfreq = float(args.maxfreq), stepfreq = float(args.stepfreq) )

        # print(xmenCalc.get_params())

        if args.print_mensur:
            prs.print_mensur(mentop)
        
        if args.calculation == 'II':
            pass
        elif args.calculation == 'RI':
            nn = (xmenCalc._Mf - xmenCalc._mf)/xmenCalc._sf + 1
            ff = np.linspace(xmenCalc._mf, xmenCalc._Mf,nn, endpoint=True)
            for f in ff:
                imp = xmenCalc.radimp(0.25,f,args.radiation)
                print(f,',',np.real(imp),',',np.imag(imp))
