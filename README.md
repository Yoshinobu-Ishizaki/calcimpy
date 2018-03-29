# calcimpy
Input impedance calculation for air column ( wind instrument ) by python.

## Plan
This is going to be new python programs written from scratch.


## Documentation

1. [Basics](doc/calcimpy_basics.md) : Basic concept of caclimpy.

1. [Webster equation memo](doc/Webster_equation.nb.pdf) : Simple memo about Webster equation for basic calculation of input impedance.

1. [Loop impedance memo](doc/loop_impedance.nb.pdf) : Simple memo about impedance lcalculation of looped multi-column.

## Sample and examples

**sample/**
Some simple sample XMEN files.

**practice/**
Example of calculation and its study (jupyter notebooks).

## Programs

**calcimpy.py**
CUI program for input impedance calculation of given XMEN file.

**printmen.py**
CUI program for printing XMEN file.
Converting to L, D data can be done.

**xmensur.py** 
Module for handling XMEN file.

**imped.py**
Module for calculation subroutines.

## ChangeLog

2018/03/29
- added printmen.py
- edited calcimpy_basics.md

2018/03/28
- calcimpy.py completed
- doc/plot_impedance.ipynb : comparison of legacy C program 'calcimp' and new 'calcimpy.py'
- some documentation

2018/03/25
- Implemented parser.py.
- Begin doc/calcimpy_basics.md
