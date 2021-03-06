"""
calcimpy
Input impedance calculation program for air column ( wind instruments ).
"""
import argparse
import sys
import os.path
import numpy as np
import pandas as pd

import xmensur as xmn
import imped

__version__ = '1.1.0'


def main():
    parser = argparse.ArgumentParser(description='calcimpy : input impedance calculation for air column')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-m', '--minfreq', default='0.0', help='minimum frequency to calculate, default 0 Hz.')
    parser.add_argument('-M', '--maxfreq', default='2000.0', help='maximum frequency to calculate, default 2000 Hz.')
    parser.add_argument('-s', '--stepfreq', default='2.5', help='step frequency for calculation, default 2.5 Hz.')
    parser.add_argument('-t', '--temperature', default='24.0', help='air temperature, default 24 celsius.')
    parser.add_argument('-R', '--radiation', choices=['PIPE', 'BAFFLE', 'NONE'], default='PIPE', help='type of calculation of radiation, default PIPE.')
    parser.add_argument('-o', '--output', default='', help='output filename, stdout is used when "-"')
    parser.add_argument('filepath')

    args = parser.parse_args()

    path = args.filepath
    if path:
        # read mensur file here
        mentop = xmn.read_mensur_file(path)
        # set calculation conditions
        imped.set_params(temperature=float(args.temperature), minfreq=float(args.minfreq),
                         maxfreq=float(args.maxfreq), stepfreq=float(args.stepfreq), rad=args.radiation)

        nn = (imped._Mf - imped._mf)/imped._sf + 1
        ff = np.linspace(imped._mf, imped._Mf, nn, endpoint=True)
        wff = np.pi*2*ff
        # set file output
        if args.output == '-':
            fout = sys.stdout
        elif args.output == '':
            # default *.imp
            rt, ext = os.path.splitext(path)
            fout = open(rt + '.imp', 'w')
        else:
            fout = open(args.output, 'w')

        s = mentop.df*mentop.df*np.pi/4  # section area
        zz = [s * imped.input_impedance(frq, mentop) for frq in wff]
        zr = np.real(zz)
        zi = np.imag(zz)
        mg = [0 if z == 0 else 20*np.log10(np.abs(z)) for z in zz]

        dt = pd.DataFrame()
        dt['freq'] = ff
        dt['imp.real'] = zr
        dt['imp.imag'] = zi
        dt['imp.mag'] = mg

        dt.to_csv(fout, index=False)
        fout.close()

if __name__ == "__main__":
        main()
