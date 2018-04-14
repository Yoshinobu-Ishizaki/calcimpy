# -*- encoding: utf-8 -*-
'''
xmensur calculation module
'''

__version__ = '0.1'

import xmensur
import numpy as np
from scipy import special 

from numba import jit, c16, f8

# import pyximport
# pyximport.install()
# import impcore

# constants
PI = np.pi
PI2 = np.pi * 2.0
GMM = 1.4 # specific head ratio
PR = 0.72 # Prandtl number

# parameters
_tp = 24.0 # temperature
_mf = 0.0 # minfreq
_Mf = 2000.0 # maxfreq
_sf = 2.5 # stepfreq
_rad = 'PIPE' # radiation type
_c0 = 331.45 * np.sqrt(_tp / 273.16 + 1)
_rho = 1.2929 * ( 273.16 / (273.16 + _tp) )
_rhoc0 = _rho * _c0
_mu = (18.2 + 0.0456*(_tp - 25)) * 1.0e-6 # viscosity constant. linear approximation from Scientific Dictionary.    
_nu = _mu/_rho # dynamic viscous constant 
rad_calc = 'PIPE'

def set_params( temperature, minfreq, maxfreq, stepfreq, rad ):
    '''set parameter and update some constants'''
    global _tp, _mf,_Mf,_sf,_rad,_c0,_rho,_rhoc0,_mu,_nu, rad_calc
    _tp = temperature
    _mf = minfreq
    _Mf = maxfreq
    _sf = stepfreq
    rad_calc = rad
    # calculation follows 
    _c0 = 331.45 * np.sqrt(_tp / 273.16 + 1)
    _rho = 1.2929 * ( 273.16 / (273.16 + _tp) )
    _rhoc0 = _rho * _c0
    
    _mu = (18.2 + 0.0456*(_tp - 25)) * 1.0e-6 # viscosity constant. linear approximation from Scientific Dictionary.    
    _nu = _mu/_rho # dynamic viscous constant 

def get_params():
    return _tp,_mf,_Mf,_sf,_c0,_rho,_rhoc0,_mu,_nu,rad_calc

def radimp( wf, dia ):
    '''calculatio radiation impedance for each frequency'''

    if not wf > 0:
        return 0

    if dia > 0 :
        if rad_calc == 'NONE':
            return 0 # simple open end impedance
        else:
            s = dia*dia*np.pi/4.0
            k = wf/_c0
            x = k*dia

            re = _rhoc0/s*(1 - special.jn(1,x)/x*2) # 1st order bessel function 
            im = _rhoc0/s*special.struve( 1,x )/x*2 # 1st order struve function

            if rad_calc == 'BAFFLE':
                zr = re + im*1j
            elif rad_calc == 'PIPE':
                # real is about 0.5 times and imaginary is 0.7 times when without frange
                zr = 0.5*re + 0.7*im*1j
        
            return zr
    else:
        return np.inf # closed end

def transmission_matrix(men1, men2):
    '''calculate transmission matrix from men2 -> men1
    returns matrix'''
    if men2 == None:
        men = xmensur.end_mensur(men1)
        men = men.prev
    else:
        men = men2
    
    m = np.eye(2,dtype = complex)
    while men != None and men != men1:
        m = np.dot(men.tm,m)
        men = men.prev
    m = np.dot(men1.tm,m)

    return m

def child_impedance(wf,men):
    '''handle impedance connection between child and current'''
    if men.c_type == 'SPLIT':
        # split (tonehole) type 
        input_impedance(wf,men.child) # recursive call for input impedance
        if men.c_ratio == 0:
            men.zo = men.next.zi
        else:
            z1 = men.child.zi / men.c_ratio # adjust blending ratio
            z2 = men.next.zi
            if z1 == 0 and z2 == 0:
                z = 0
            else:
                z = z1*z2/(z1+z2)
            men.zo = z 
    elif men.c_type == 'BRANCH' and men.c_ratio > 0:
        # multiple tube connection
        input_impedance(wf,men.child)
        m = transmission_matrix(men.child,None)
	    
        jnt = xmensur.joint_mensur(men)
        n = transmission_matrix(men.next,jnt)

        # section area adjustment
        if men.c_ratio == 1:
            m[0,1] = np.inf    
        else:
            m[0,1] /= (1 - men.c_ratio)
        m[1,0] *= (1 - men.c_ratio)
        if men.c_ratio == 0:
            n[0,1] = np.inf
        else:
            n[0,1] /= men.c_ratio
        n[1,0] *= men.c_ratio

        z2 = jnt.next.zi
        dv = (m[1,1]*n[0,1] + m[0,1]*n[1,1] + ((m[0,1] + n[0,1])*(m[1,0] + n[1,0]) - (m[0,0] - n[0,0])*(m[1,1] - n[1,1]))*z2)
        if dv != 0:
            z = (m[0,1]*n[0,1] + (m[0,1]*n[0,0] + m[0,0]*n[0,1])*z2)/ dv
        else:
            z = 0        
        men.zo = z
    elif men.c_type == 'ADDON' and men.c_ratio > 0:
        # this routine will not called until 'ADDON(LOOP)' type of connection is implemented 
        input_impedance(wf,men.child)	
        m = transmission_matrix(men.child,None)
	    
        z1 = m[0,1]/(m[0,1]*m[1,0]-(1-m[0,0])*(1-m[1,1]))
        z2 = men.next.zi
        if men.c_ratio == 0:
            men.zo = men.next.zi
        elif men.c_ratio == 1:
            men.zo = z1
        else:
            z1 /= men.c_ratio
            z2 /= (1 - men.c_ratio)	
            if z1 == 0 and z2 == 0:
                z = 0
            else:
                z = z1*z2/(z1+z2)
            men.zo = z

@jit(c16[:,:](f8,f8,f8,f8),nopython=True, cache=True)
def calc_transmission(wf, df, db, r):
    '''calculate transmission matrix for a given mensur cell
    always call with r > 0
    '''
    d = (df + db )*0.5
    aa = (1+(GMM-1)/np.sqrt(PR))*np.sqrt(2*wf*_nu)/_c0/d # wall dumping factor
    k = np.sqrt( (wf/_c0)*(wf/_c0 - 2*(-1+1j)*aa) ) # complex wave number including wall dumping
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
        tm[0,1] = 1j*_rhoc0*ss/(PI*r1*r2)
        tm[1,0] = -1j*PI*( dr*dr*x*cc - (dr*dr + x*x*r1*r2 )*ss )/(x*x*_rhoc0)
        tm[1,1] = ( r1*x*cc + dr*ss)/(r2*x)
    else:
        # straight
        s1 = PI/4*df*df
        tm[0,0] = tm[1,1] = cc
        tm[0,1] = 1j*_rhoc0*ss/s1
        tm[1,0] = 1j*s1*ss/_rhoc0
    
    return tm

@jit(c16(c16[:,:],c16), nopython = True, cache=True)
def zo2zi(tm, zo):
    if not np.isinf(zo):
        zi = (tm[0,0]*zo + tm[0,1])/(tm[1,0]*zo + tm[1,1] ) 
    else:
        if tm[1,0] != 0:
            zi = tm[0,0]/tm[1,0]
        else:
            zi = np.inf

    return zi

def calc_impedance(wf, men):
    '''calculate impedance and other data for a given mensur cell'''
    if men.child:
        child_impedance(wf,men)
    elif men.next:
        men.zo = men.next.zi

    if men.r > 0:
        men.tm = calc_transmission(wf,men.df, men.db, men.r) 
        men.zi = zo2zi(men.tm, men.zo)
    else:
        # length 0
        men.zi = men.zo

def input_impedance(wf, men):
    '''calculate input impedance of given mensur
    wf : wave frequency 2*pi*frq
    '''
    # cur.po = 0.02 + 0j # 60dB(SPL) = 20*1e-6 * 10^(60/20)
    # does not need to calculate impedance

    if wf == 0:
        return 0

    cur = xmensur.end_mensur(men)
    # end impedance
    cur.zo = radimp(wf,cur.df)
    
    while cur != men:
        calc_impedance(wf,cur)
        cur = cur.prev
    calc_impedance(wf,men)

    return men.zi
    
def calc_pressure(wf, mensur, endp, from_tail = False):
    '''calculate pressure from end at wave frequency wf.
    input_impedance routine must be called before using this.
    branch and  
    '''
    if not from_tail:
        men = mensur
        # closed end at head is supposed. not good for flute like instrument ?
        v = [ endp, 0.0 ]
        while men:
            men.pi = v[0]
            men.ui = v[1]
            ti = np.linalg.inv(men.tm)
            v = np.dot(ti,v) # update v
            men.po = v[0]
            men.uo = v[1]

            men = xmensur.actual_next_mensur(men)

    else:
        men = xmensur.end_mensur(mensur)
        z = men.zo
        if z == 0:
            v = [0, endp/_rhoc0] # open end with no end correction
        else:
            v = [endp, endp/z]
        while men:
            men.po = v[0]
            men.uo = v[1]
            v = np.dot(men.tm,v) 
            men.pi = v[0]
            men.ui = v[1]

            men = xmensur.actual_prev_mensur(men)


