# -*- coding: utf-8 -*-
'''
test program to show various calculation result of xmensur
'''
__version__ = '0.1'

import xmensur as xmn
import imped

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

        mentop = xmn.build_mensur( lines )
    
        # set calculation conditions
        imped.set_params(temperature = float(args.temperature), minfreq = float(args.minfreq), \
        maxfreq = float(args.maxfreq), stepfreq = float(args.stepfreq), rad = args.radiation )

        # print(imped.get_params())

        if args.print_mensur:
            xmn.print_mensur(mentop)
        
        if args.calculation == 'II':
            nn = (imped._Mf - imped._mf)/imped._sf + 1
            ff = np.linspace(imped._mf, imped._Mf,nn, endpoint=True)
            wff = np.pi*2*ff
            s = mentop.df*mentop.df*np.pi/4 # section area 
            for i in np.arange(nn,dtype = int):
                imped.input_impedance(wff[i],mentop)
                # output impedance density
                print(ff[i],',',np.real(mentop.zi)*s,',',np.imag(mentop.zi)*s)
                # print(ff[i])

        elif args.calculation == 'RI':
            men = xmn.end_mensur(mentop)
            dia = men.df
            # print(dia)
            nn = (imped._Mf - imped._mf)/imped._sf + 1
            ff = np.linspace(imped._mf, imped._Mf,nn, endpoint=True)
            wff = np.pi*2*ff
            for wf in wff:
                imp = imped.radimp(wf,dia)
                print(f,',',np.real(imp),',',np.imag(imp))
