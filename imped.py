"""
xmensur calculation module
"""
import numpy as np
from scipy import special

import xmensur
# from numba import jit, c16, f8
import impcore

__version__ = '1.1.0'

# constants
PI = np.pi
PI2 = np.pi * 2.0
GMM = 1.4  # specific head ratio
PR = 0.72  # Prandtl number

# parameters
_tp = 24.0  # temperature
_mf = 0.0  # minfreq
_Mf = 2000.0  # maxfreq
_sf = 2.5  # stepfreq
_c0 = 331.45 * np.sqrt(_tp / 273.16 + 1)
_rho = 1.2929 * (273.16 / (273.16 + _tp))
_rhoc0 = _rho * _c0
_mu = (18.2 + 0.0456*(_tp - 25)) * 1.0e-6  # viscosity constant. Linear approximation from Scientific Dictionary.
_nu = _mu/_rho  # dynamic viscous constant.
_rad_calc = 'PIPE'  # radiation type


def set_params(temperature, minfreq, maxfreq, stepfreq, rad):
    """Set parameter and update some constants"""
    global _tp, _mf, _Mf, _sf, _c0, _rho, _rhoc0, _mu, _nu, _rad_calc
    _tp = temperature
    _mf = minfreq
    _Mf = maxfreq
    _sf = stepfreq
    _rad_calc = rad
    # calculation follows
    _c0 = 331.45 * np.sqrt(_tp / 273.16 + 1)
    _rho = 1.2929 * (273.16 / (273.16 + _tp))
    _rhoc0 = _rho * _c0
    _mu = (18.2 + 0.0456*(_tp - 25)) * 1.0e-6  # viscosity constant. linear approximation from Scientific Dictionary.
    _nu = _mu/_rho  # dynamic viscous constant.


def get_params():
    return _tp, _mf, _Mf, _sf, _c0, _rho, _rhoc0, _mu, _nu, _rad_calc


def radimp(wf, dia):
    """calculatio radiation impedance for each frequency"""
    if not wf > 0:
        return 0

    if dia > 0:
        if _rad_calc == 'NONE':
            return 0  # simple open end impedance
        else:
            s = dia*dia*np.pi/4.0
            k = wf/_c0
            x = k*dia

            re = _rhoc0/s*(1 - special.jn(1, x)/x*2)  # 1st order bessel function.
            im = _rhoc0/s*special.struve(1, x)/x*2  # 1st order struve function.

            if _rad_calc == 'BAFFLE':
                zr = re + im*1j
            elif _rad_calc == 'PIPE':
                # real is about 0.5 times and imaginary is 0.7 times when without frange.
                zr = 0.5*re + 0.7*im*1j

            return zr
    else:
        return np.inf  # closed end


def transmission_matrix(men1, men2):
    """calculate transmission matrix from men2 -> men1
    returns matrix"""
    if men2 is None:
        men = xmensur.end_mensur(men1)
        men = men.prev
    else:
        men = men2

    m = np.eye(2, dtype=complex)
    while men is not None and men != men1:
        m = np.dot(men.tm, m)
        men = men.prev
    m = np.dot(men1.tm, m)

    return m


def child_impedance(wf, men):
    """handle impedance connection between child and current"""
    if men.c_type == 'SPLIT':
        # split (tonehole) type.
        input_impedance(wf, men.child)  # recursive call for input impedance
        if men.c_ratio == 0:
            men.zo = men.next.zi
        else:
            z1 = men.child.zi / men.c_ratio  # adjust blending ratio
            z2 = men.next.zi
            if z1 == 0 and z2 == 0:
                z = 0
            else:
                z = z1*z2/(z1+z2)
            men.zo = z
    elif men.c_type == 'BRANCH' and men.c_ratio > 0:
        # multiple tube connection
        input_impedance(wf, men.child)
        m = transmission_matrix(men.child, None)
        jnt = xmensur.joint_mensur(men)
        n = transmission_matrix(men.next, jnt)

        # section area adjustment
        if men.c_ratio == 1:
            m[0, 1] = np.inf
        else:
            m[0, 1] /= (1 - men.c_ratio)
        m[1, 0] *= (1 - men.c_ratio)
        if men.c_ratio == 0:
            n[0, 1] = np.inf
        else:
            n[0, 1] /= men.c_ratio
        n[1, 0] *= men.c_ratio

        z2 = jnt.next.zi
        dv = (m[1, 1]*n[0, 1] + m[0, 1]*n[1, 1] + (
            (m[0, 1] + n[0, 1])*(m[1, 0] + n[1, 0]) - (m[0, 0] - n[0, 0])*(m[1, 1] - n[1, 1]))*z2)
        if dv != 0:
            z = (m[0, 1]*n[0, 1] + (m[0, 1]*n[0, 0] + m[0, 0]*n[0, 1])*z2)/dv
        else:
            z = 0
        men.zo = z
    elif men.c_type == 'ADDON' and men.c_ratio > 0:
        # this routine will not called until 'ADDON(LOOP)' type of connection is implemented.
        input_impedance(wf, men.child)
        m = transmission_matrix(men.child, None)
        z1 = m[0, 1]/(m[0, 1]*m[1, 0]-(1-m[0, 0])*(1-m[1, 1]))
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


def calc_impedance(wf, men):
    """calculate impedance and other data for a given mensur cell"""
    if men.child:
        child_impedance(wf, men)
    elif men.next:
        men.zo = men.next.zi

    if men.r > 0:
        men.tm = impcore.calc_transmission(wf, men.df, men.db, men.r, _c0, _rhoc0, _nu)
        men.zi = impcore.zo2zi(men.tm, men.zo)
    else:
        # length 0
        men.zi = men.zo


def input_impedance(wf, men):
    """calculate input impedance of given mensur
    wf : wave frequency 2*pi*frq
    """
    # cur.po = 0.02 + 0j # 60dB(SPL) = 20*1e-6 * 10^(60/20)
    # does not need to calculate impedance

    if wf == 0:
        return 0

    cur = xmensur.end_mensur(men)
    # end impedance
    cur.zo = radimp(wf, cur.df)

    while cur != men:
        calc_impedance(wf, cur)
        cur = cur.prev
    calc_impedance(wf, men)

    return men.zi


def calc_pressure(wf, mensur, endp, from_tail=False):
    """Calculate pressure from end at wave frequency wf.
    Input_impedance routine must be called before using this.
    """
    if not from_tail:
        men = mensur
        # closed end at head is supposed. not good for flute like instrument ?
        v = [endp, 0.0]
        while men:
            men.pi = v[0]
            men.ui = v[1]
            ti = np.linalg.inv(men.tm)
            v = np.dot(ti, v)  # update v
            men.po = v[0]
            men.uo = v[1]

            men = xmensur.actual_next_mensur(men)
    else:
        men = xmensur.end_mensur(mensur)
        z = men.zo
        if z == 0:
            v = [0, endp/_rhoc0]  # open end with no end correction.
        else:
            v = [endp, endp/z]
        while men:
            men.po = v[0]
            men.uo = v[1]
            v = np.dot(men.tm, v)
            men.pi = v[0]
            men.ui = v[1]

            men = xmensur.actual_prev_mensur(men)
