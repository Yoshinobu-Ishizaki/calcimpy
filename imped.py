# -*- encoding: utf-8 -*-
'''
xmensur calculation module
'''

__version__ = '0.1'

import xmensur
import numpy as np
from scipy import special 

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

    if( wf > 0 ):
        if rad_calc == 'NONE':
            return 0
        else:
            s = dia*dia*np.pi/4.0
            k = wf/_c0
            x = k*dia

            re = _rhoc0/s*(1 - special.jn(1,x)/x*2) # 1st order bessel function 
            im = _rhoc0/s*special.struve( 1,x )/x*2 # 1st order struve function

            if rad_calc == 'BUFFLE':
                zr = re + im*1j
            elif rad_calc == 'PIPE':
                # real is about 0.5 times and imaginary is 0.7 times when without frange
                zr = 0.5*re + 0.7*im*1j
        
            return zr
    else:
        return 0

def transmission_matrix(men1, men2):
    '''calculate transmission matrix from men2 -> men1
    returns matrix'''
    if men2 == None:
        men = end_mensur(men1)
        men = men.prev
    else:
        men = men2
    
    m = np.eye(2,dtype = complex)
    while men != None and men != men1:
        np.dot(men.tm,m)
        men = men.prev

    return m

def child_impedance(wf,men):
    '''handle impedance connection between side and current'''
    if men.side == None:
        return

    if men.sidetype == 'SPLIT':
        # split (tonehole) type 
        input_impedance(wf,men.side) # recursive call for input impedance
        if men.sideratio == 0:
            men.zo = men.next.zi
        elif men.sideratio == 1:
            men.zo = men.side.zi
        else:
            z1 = men.side.zi / men.sideratio
            z2 = men.next.zi / (1-men.sideratio)
            z = z1*z2/(z1+z2)
            men.zo = z 
    elif men.sidetype == 'BRANCH' and men.sideratio > 0:
        # multiple tube connection
        input_impedance(wf,men.side)
        m = transmission_matrix(men.side,None)
	    
        jnt = joint_mensur(men)
        n = transmission_matrix(men.next,jnt)

        # section area adjustment
        if men.sideratio == 1:
            m[0,1] = np.inf    
        else:
            m[0,1] /= (1 - men.sideratio)
        m[1,0] *= (1 - men.sideratio)
        if men.sideratio == 0:
            n[0,1] = np.inf
        else:
            n[0,1] /= men.sideratio
        n[1,0] *= men.sideratio

        z2 = jnt.next.zi
        z = (m[0,1]*n[0,1] + (m[0,1]*n[0,0] + m[0,0]*n[0,1])*z2)/ \
        (m[1,1]*n[0,1] + m[0,1]*n[1,1] + ((m[0,1] + n[0,1])*(m[1,0] + n[1,0]) - (m[0,0] - n[0,0])*(m[1,1] - n[1,1]))*z2)
        men.zo = z
    elif men.sidetype == 'ADDON' and men.sideratio > 0:
        # this routine will not called until 'ADDON(LOOP)' type of connection is implemented 
        input_impedance(wf,men.side)	
        m = transmission_matrix(men.side,None)
	    
        z1 = m[0,1]/(m[0,1]*m[1,0]-(1-m[0,0])*(1-m[1,1]))
        z2 = men.next.zi
        if men.sideratio == 0:
            men.zo = men.next.zi
        elif men.sideratio == 1:
            men.zo = z1
        else:
            z1 /= men.sideratio
            z2 /= (1 - men.sideratio)	
            z = z1*z2/(z1+z2)
            men.zo = z

def calc_transmission(wf,men):
    '''calculate transmission matrix for a given mensur cell'''
    d = (men.df + men.db )*0.5
    aa = (1+(GMM-1)/np.sqrt(PR))*np.sqrt(2*wf*_nu)/_c0/d # wall dumping factor
    k = np.sqrt( (wf/_c0)*(wf/_c0 - 2*(-1+1j)*aa) ) # complex wave number including wall dumping
    x = k * men.r

    if men.r > 0:
        if men.df != men.db :
            # taper
            r1 = men.df*0.5
            r2 = men.db*0.5
            
            men.tm[0,0] = ( r2*x*np.cos(x) -(r2-r1)*np.sin(x))/(r1*x)
            men.tm[0,1] = 1j*_rhoc0*np.sin(x)/(PI*r1*r2)
            men.tm[1,0] = -1j*PI*( (r2-r1)*(r2-r1)*x*np.cos(x) - \
            ((r2-r1)*(r2-r1) + x*x*r1*r2 )*np.sin(x) )/(k*k*L*L*rhoc0)
            men.tm[1,1] = ( r1*x*np.cos(x) + (r2-r1)*np.sin(x))/(r2*x)
        else:
            # straight
            s1 = PI/4*men.df*men.df
            men.tm[0,0] = men.tm[1,1] = np.cos(x)
            men.tm[0,1] = 1j*_rhoc0*np.sin(x)/s1
            men.tm[1,0] = 1j*s1*np.sin(x)/_rhoc0
    else:
        # length 0
        men.tm = np.eye(2, dtype=complex)
    
def calc_impedance(wf, men):
    '''calculate impedance and other data for a given mensur cell'''
    if men.child:
        child_impedance(wf,men)

    if men.r > 0:
        calc_transmission(wf,men) 
        men.zi = (men.tm[0,0]*men.zo + men.tm[0,1])/(men.tm[1,0]*men.zo + men.tm[1,1] ) 
    else:
        # length 0
        men.zi = men.zo

def input_impedance(wf, men):
    '''calculate input impedance of given mensur
    wf : wave frequency 2*pi*frq
    '''
    # cur.po = 0.02 + 0j # 60dB(SPL) = 20*1e-6 * 10^(60/20)
    # does not need to calculate impedance

    cur = xmensur.end_mensur(men)
    # end impedance
    if cur.db > 0:
        cur.zo = radimp(wf,cur.db)
    else:
        # closed end 
        cur.zo = np.inf
    
    # cur.uo = cur.po/cur.zo

    while cur != men:
        calc_impedance(wf,cur)
        cur = cur.prev
    calc_impedance(wf,men)
    