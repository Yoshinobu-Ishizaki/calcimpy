# -*- encoding: utf-8 -*-
'''
xmensur calculation module
'''

__version__ = '0.1'

import xmensur
import numpy as np
from scipy import special 

# constants
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

def set_params( temperature, minfreq, maxfreq, stepfreq ):
    '''set parameter and update some constants'''
    _tp = temperature
    _mf = minfreq
    _Mf = maxfreq
    _sf = stepfreq
    # calculation follows 
    _c0 = 331.45 * np.sqrt(_tp / 273.16 + 1)
    _rho = 1.2929 * ( 273.16 / (273.16 + _tp) )
    _rhoc0 = _rho * _c0
    
    _mu = (18.2 + 0.0456*(_tp - 25)) * 1.0e-6 # viscosity constant. linear approximation from Scientific Dictionary.    
    _nu = _mu/_rho # dynamic viscous constant 

def get_params():
    return _tp,_mf,_Mf,_sf,_c0,_rho,_rhoc0,_mu,_nu 

def radimp( dia, f, rad_calc ):
    '''calculatio radiation impedance for each frequency'''

    if( f > 0 ):
        if rad_calc == 'NONE':
            return 0
        else:
            s = dia*dia*np.pi/4.0
            k = 2*np.pi*f/_c0
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

