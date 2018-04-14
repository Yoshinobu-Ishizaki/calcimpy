# -*- encoding: utf-8 -*-
'''
impcore.py
core calculation routines for imped
'''

import numpy as np
from numba import c16, f8
from numba.pycc import CC

cc = CC('impcore')
cc.verbose = True

GMM = 1.4 # specific head ratio
PR = 0.72 # Prandtl number
PI = np.pi
Wdmp = (1+(GMM-1)/np.sqrt(PR))

@cc.export('calc_transmission','c16[:,:](f8,f8,f8,f8,f8,f8,f8)')
def calc_transmission(wf, df, db, r, c0, rhoc0, nu ):
    '''calculate transmission matrix for a given mensur cell
    always call with r > 0
    '''
    d = ( df + db )*0.5
    aa = Wdmp * np.sqrt(2*wf*nu)/c0/d # wall dumping factor
    k = np.sqrt( (wf/c0)*(wf/c0 - 2*(-1+1j)*aa) ) # complex wave number including wall dumping
    x = k * r
    cc = np.cos(x)
    ss = np.sin(x)

    tm = np.empty((2,2),dtype = c16)

    if df != db :
        # taper
        r1 = df*0.5
        r2 = db*0.5
        dr = r2-r1
        
        tm[0,0] = ( r2*x*cc -dr*ss)/(r1*x)
        tm[0,1] = 1j*rhoc0*ss/(PI*r1*r2)
        tm[1,0] = -1j*PI*( dr*dr*x*cc - (dr*dr + x*x*r1*r2 )*ss )/(x*x*rhoc0)
        tm[1,1] = ( r1*x*cc + dr*ss)/(r2*x)
    else:
        # straight
        s1 = PI/4*df*df
        tm[0,0] = tm[1,1] = cc
        tm[0,1] = 1j*rhoc0*ss/s1
        tm[1,0] = 1j*s1*ss/rhoc0
    
    return tm

@cc.export('zo2zi','c16(c16[:,:],c16)')
def zo2zi(tm, zo):
    if not np.isinf(zo):
        zi = (tm[0,0]*zo + tm[0,1])/(tm[1,0]*zo + tm[1,1] ) 
    else:
        if tm[1,0] != 0:
            zi = tm[0,0]/tm[1,0]
        else:
            zi = np.inf

    return zi

if __name__ == '__main__':
    cc.compile()
