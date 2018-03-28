# -*- coding: utf-8 -*-
'''
calcimpy
input impedance calculation program for air column ( wind instruments )
'''
__version__ = '1.0.0'

import xmensur as xmn
import imped

import argparse
import sys
import os.path

import numpy as np

if __name__ == "__main__" :
    # exec this as standalone program.
    parser = argparse.ArgumentParser(description='calcimpy : input impedance calculation for air column')
    parser.add_argument('-v', '--version', action = 'version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-m', '--minfreq', default = '0.0', help = 'minimum frequency to calculate.')
    parser.add_argument('-M', '--maxfreq', default = '2000.0', help = 'maximum frequency to calculate.')
    parser.add_argument('-s','--stepfreq', default = '2.5', help = 'step frequency for calculation.')
    parser.add_argument('-t','--temperature', default = '24.0', help = 'air temperature (celsius).')
    parser.add_argument('-R','--radiation',choices = ['PIPE','BAFFLE','NONE'], default = 'PIPE', help = 'type of calculation of radiation.')
    parser.add_argument('-o','--output',default = '', help = 'output filename, stdout is used when "-"' )
    parser.add_argument('filepath')

    args = parser.parse_args()

    path = args.filepath
    if path:
        #read mensur file here
        fd = open(path,'r')
        lines = fd.readlines()
        fd.close()

        mentop = xmn.build_mensur( lines )
    
        # set calculation conditions
        imped.set_params(temperature = float(args.temperature), minfreq = float(args.minfreq), \
        maxfreq = float(args.maxfreq), stepfreq = float(args.stepfreq), rad = args.radiation )

        # print(imped.get_params())

        nn = (imped._Mf - imped._mf)/imped._sf + 1
        ff = np.linspace(imped._mf, imped._Mf,nn, endpoint=True)
        wff = np.pi*2*ff
        
        # set file output
        if args.output == '-':
            fout = sys.stdout
        elif args.output == '':
            # default *.imp
            rt, ext = os.path.splitext(path)
            fout = open( rt + '.imp','w')
        else:
            fout = fopen(args.output,'w') 

        sys.stdout = fout
        s = mentop.df*mentop.df*np.pi/4 # section area 
        for i in np.arange(nn,dtype = int):
            # output impedance density
            imped.input_impedance(wff[i],mentop)
            z = mentop.zi
            print(ff[i],',',np.real(z)*s,',',np.imag(z)*s)
