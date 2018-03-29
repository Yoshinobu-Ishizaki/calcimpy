#!/bin/env python
# -*- coding: utf-8 -*-

import re
import numpy as np

"""
xmensur core routine and handler functions
"""
class Men(object):
    """メンズール要素のクラス"""
    def __init__(self, df = 0, db = 0, r = 0, comment = '', group = None, prev = None, next = None, child = None, c_name = '', c_type = None, c_ratio = 1 ):
        self.df = df
        self.db = db
        self.r = r
        self.group = group # to be used inside 
        self.comment = comment # comment string 
        self.next = next # next Men
        self.prev = prev # prev Men
        self.parent = None
        self.child = child # child Men ( BRANCH, MERGE, TONEHOLE )
        self.c_name = c_name # name of child men for searching later.
        self.c_type = c_type #BRANCH,MERGE,TONEHOLE ...
        self.c_ratio = c_ratio # child connection ratio
        # below are calculated later
        # for impedance
        self.tm = np.zeros((2,2),dtype = complex) # transmission matrix
        self.zi = 0 # impedance at input end
        self.zo = 0 # impedance at output end
        # for pressure 
        self.pi = 0 # pressure at input end
        self.ui = 0 # volume verosity at input end
        self.po = 0 # pressure at output end
        self.uo = 0 # volume verosity at output end
        # for printing total length 
        self.xL = 0 # total length from 1st mensur

    def append(self, next = None):
        """Append next Men to this."""
        self.next = next
        self.next.prepend(self)

    def prepend(self, prev = None):
        """Set prev Men."""
        self.prev = prev
    
    def setchild(self, child):
        if child:
            self.child = child
            child.parent = self
        
    def get_fbr(self):
        return self.df, self.db, self.r 

    def __str__(self):
        return '%g,%g,%g,%s' % (self.df*1000, self.db*1000, self.r*1000, self.comment)


# reserved words
# BRANCH = VALVE_OUT, MERGE = VALVE_IN, SPLIT = TONEHOLE
# Aliases
# < = BRANCH, > MERGE, | = SPLIT
# [ = MAIN, ] = END_MAIN
# { = GROUP, } = END_GROUP

type_keywords = ('SPLIT', 'VALVE_OUT', 'MERGE', 'VALVE_IN', 'TONEHOLE', 'BRANCH','OPEN_END', 'CLOSED_END',\
'INSERT', '<', '>', '|','@')
group_keywords = ('MAIN', 'END_MAIN', 'GROUP', 'END_GROUP', '[', ']', '{', '}')

# default values
OPEN = 1
CLOSE = 0
HALF = 0.5
HEAD = 0
LAST = 1

# mensur group storing
group_names = []
group_tree = []

# list of all mensur items 
mensur = []
# dictionary for each head of mensur group
men_grp_table = {}

def eat_comment( s ):
    """Eat comment string after # char."""
    n = s.find('#')
    if n >= 0 :
        return s[:n]
    else:
        return s

def resolve_vars( lst ):
    """Resolve vars in each args"""
    v = []
    for w in lst:
        try:
            f = float(w)
        except ValueError:
            # by eval, string w which contain vars predefined is parsed.
            f = eval( w )
            
        v.append(f)
    return v

def men_by_kwd( cur, lst ):
    """
    Handle BRANCH, MERGE, TONEHOLE,...
    Returns new Men item.
    """
    key = lst[0]
    if len(lst) > 1:
        name = lst[1]
    elif len(lst) > 2:
        ratio = resolve_vars(lst[2:3])[0]

    df,db,r = cur.get_fbr()
    gp = cur.group

    men = None
    
    if key == 'BRANCH' or key == 'VALVE_OUT' or key == '<':
        men = Men( db, db, 0, gp, c_name = name, c_type = 'BRANCH', c_ratio = ratio )
    elif key == 'MERGE' or key =='VALVE_IN' or key == '>':
        men = Men( db, db, 0, gp, c_name = name, c_type = 'MERGE', c_ratio = ratio )
    elif key == 'SPLIT' or key == 'TONEHOLE' or key == '|':
        men = Men( db, db, 0, gp, c_name = name, c_type = 'SPLIT', c_ratio = ratio )
    elif key == 'INSERT' or key == '@':
        men = Men( db, db, 0, c_name = name, c_type = 'INSERT', c_ratio = 1)
    elif key == 'OPEN_END':
        men = Men( db, 0, 0 , '', group = gp )
    elif key == 'CLOSED_END':
        men = Men( 0, 0, 0, '', group = gp )
    else:
        pass
    
    if men :
        cur.append(men)

    return men


def top_mensur(men):
    if men:
        while men.prev:
            men = men.prev
    return men

def end_mensur(men):
    if men:
        while men.next:
            men = men.next
    return men

def joint_mensur(men):
    '''joint point of mensur which is BRANCH type'''
    if men.c_type == 'BRANCH':
        e = end_mensur(men.child)
        if e.parent and e.parent.c_type == 'MERGE':
            return e.parent
        else:
            return None
    else:
        return None

def resolve_child_mensur():
    """Connect child mensur to Main"""
    men = men_grp_table['MAIN'] # top mensur cell

    while men:
        if men.c_name != '':
            if men.c_type == 'INSERT':
                # join child group to main trunc
                men2 = men.next
                ms = men_grp_table[men.c_name]
                me = end_mensur(ms)

                men.next = ms
                ms.prev = men
                me.next = men2
                men2.prev = me
            else:
                if men.c_type == 'MERGE':
                    ms = end_mensur(men_grp_table[men.c_name])
                else:
                    ms = men_grp_table[men.c_name]
                men.setchild(ms)
        
        men = men.next

def print_mensur(men, main = False):
    '''print mensur.
    Print MAIN tag if main = True
    '''
    mychild = {}
    if main:
        print('MAIN')
    while men:
        print(men) # output __str__
        if men.child:
            print(men.c_type,',',men.c_name,',',men.c_ratio)
            if men.c_type != 'MERGE':
                mychild[men.c_name] = men.child

        men = men.next
    if main:
        print('END_MAIN')

    for nm in mychild.keys():
        print('\nGROUP,',nm)
        print_mensur(mychild[nm]) # recursive call to child mensur
        print('END_GROUP')

def print_mensur_ld(men):
    '''print mensur converted to L,D data.
    Ignore showing SPLIT type because it is not connected straight forward.
    '''
    print('L,D')
    xL = 0.0
    s = '0,0'
    print(s)
    while men:
        ss = '{0:.3f},{1:.3f}'.format(xL*1000,men.df*1000)
        if ss != s:
            print(ss)
            s = ss
        xL += men.r
        ss = '{0:.3f},{1:.3f}'.format(xL*1000,men.db*1000)
        if ss != s:
            print(ss)
            s = ss

        if men.child and men.c_type == 'BRANCH' and men.c_ratio > HALF:
            men = men.child
        elif men.child and men.c_type == 'MERGE' and men.c_ratio > HALF:
            men = men.parent
        else:
            men = men.next
    
def clear_mensur():
    """Cleans all global mensur list, table"""
    del mensur[:]
    del group_names[:]
    del group_tree[:]


######################################################################
def build_mensur( lines ):
    """Parse text lines which read from mensur file,
    then build mensur objects.
    """
    global group_tree, group_names

    cur = None # current mensur cell 
    gnm = '' # current group name

    spcrm = re.compile(r'[\t\s]+') # remove all spaces and tabs

    for ln in lines:
        s = eat_comment(ln.rstrip())
        # remove whitespaces
        ss = spcrm.sub('',s)
        if len(ss) == 0:
            continue # ignore blank line

        wd = ss.split(',')
        # is it var def ?
        if '=' in wd[0]:
            exec(wd[0], globals()) # execute as python code, so that setting vars et al.
            continue

        # it is command or normal DF,DB,R
        if wd[0] in group_keywords:
            #print(wd)
            if wd[0] == 'END_MAIN' or wd[0] == ']':
                group_tree = []
                cur = None 
            elif wd[0] == 'END_GROUP' or wd[0] == '}':
                group_tree.pop()
                if not len(group_tree):
                    cur = None
            else:
                if wd[0] == 'MAIN' or wd[0] == '[':
                    gnm = 'MAIN'
                    group_tree = [gnm]
                elif wd[0] == 'GROUP' or wd[0] == '{':
                    group_tree.append(wd[1])
                    gnm = ':'.join(group_tree) # nested groups are connected by :                
                assert (not gnm in group_names), "group name %s is doubling" % gnm # group name must be unique
                group_names.append( gnm )
        else:
            if wd[0] in type_keywords:
                # BRANCH, MERGE, SPLIT, etc...
                cur = men_by_kwd(cur,wd)
            else:
                # normal df,db,r,cmt line
                df,db,r = resolve_vars( wd[:3] ) # only df,db,r 
                if len(wd) > 3:
                    cmt = ''.join(wd[3:])
                else:
                    cmt = ''
                men = Men( df*0.001,db*0.001,r*0.001, comment = cmt, group = gnm ) # create men 

                if not cur:
                    if group_tree[0] == 'MAIN':
                        men_grp_table['MAIN'] = men
                    else:
                        # print(gnm)
                        men_grp_table[gnm] = men
                    cur = men
                else:
                    cur.append(men)
                    cur = men
    
    # debug
    # print(men_grp_table)
    # print(group_names)

    # now resolve childs
    resolve_child_mensur()

    # return topmost mensur
    return men_grp_table['MAIN']

