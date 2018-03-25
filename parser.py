#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
WIIIのファイル表現とデータそのものの間を取り持つControllerクラス
単独でシェルから呼び出されると、コマンドラインプログラムとしても機能する。
"""

#from wiii_core import *
#from math import *

# 予約語
# SPLIT = VALVE_OUT, JOIN = VALVE_IN, BRANCH = TONEHOLE
keywords = ('SPLIT', 'VALVE_OUT', 'JOIN', 'VALVE_IN', 'TONEHOLE', 'BRANCH', 'OPEN_END', 'CLOSED_END',
            'MAIN', 'END_MAIN', 'GROUP', 'END_GROUP')

# デフォルト変数。
OPEN = 1
CLOSE = 0
HALF = 0.5

HEAD = 0
LAST = 1

# グループ管理用
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

def men_by_kwd( lst ):
    """
    Handle SPLIT, JOINT, TONEHOLE,...
    Returns new Men item.
    """
    key = lst[0]
    if len(lst) > 2:
        name, ratio = lst[1:3]
    lastmen = mensur[-1]
    gp = group_tree[-1]
    df,db,r = lastmen.get_fbr()

    men = None
    
    if key == 'SPLIT' or key == 'VALVE_OUT':
        men = Men( db, db, 0, gp, sidename = name, sidetype = 'SPLIT', sideratio = ratio )
    elif key == 'JOIN' or key =='VALVE_IN':
        men = Men( db, db, 0, gp, sidename = name, sidetype = 'JOIN', sideratio = ratio )
    elif key == 'BRANCH' or key == 'TONEHOLE':
        men = Men( db, db, 0, gp, sidename = name, sidetype = 'BRANCH', sideratio = ratio )
    elif key == 'OPEN_END':
        men = Men( db, db, 0 , gp )
    elif key == 'CLOSED_END':
        men = Men( db, 0, 0, gp )
    else:
        pass
    
    if men :
        lastmen.append(men)

    return men

def find_grp_end_mensur( name, end = HEAD ):
    for m in mensur:
        if m.group == name:
            if end == HEAD:
                if m.prev == None:
                    return m
                elif m.prev.group != name:
                    return m
            if end == LAST:
                if m.next == None:
                    return m
                elif m.next.group != name:
                    return m
    else:
        return None


def update_men_group():
    """Updates Group Table for Mensur"""
    for gnm in group_names:
        men = find_grp_end_mensur(gnm)
        men_grp_table[gnm] = men

    men_grp_table['MAIN'] = mensur[0] # kore ha tokubetsu

def resolve_child_mensur():
    """Connect side mensur to Main"""
    for m in mensur:
        if len(m.sidename) > 0:
            if m.sidetype == 'JOIN':
                ms = find_grp_end_mensur(m.sidename, LAST)
            else:
                ms = find_grp_end_mensur(m.sidename, HEAD)
            m.side = ms
            
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
    for ln in lines:
        s = eat_comment(ln.rstrip())
        if len(s) == 0:
            continue # ignore blank line

        # remove whitespaces
        ss = s.strip()
        # is it var def ?
        if '=' in ss:
            exec(ss, globals()) # execute as python code, so that setting vars et al.
            continue

        # it is command or normal DF,DB,R
        wd = ss.split(',')
        if wd[0] in keywords:
            if wd[0] == 'GROUP' or wd[0] == 'MAIN':
                if wd[0] == 'MAIN':
                    gn = 'MAIN'
                else:
                    gn = wd[1]
                assert (not gn in group_names), "group name %s is doubling" % gn # group name must be unique
                group_names.append( gn )
                group_tree.append( gn )
                continue
            
            elif wd[0] == 'END_GROUP' or wd[0] == 'END_MAIN':
                group_tree.pop()
                continue
            else:
                # other SPLIT, TONEHOLE, ...
                men = men_by_kwd(wd)
        else:
            # normal df,db,r,cmt line
            df,db,r = resolve_vars( wd[:3] ) # only df,db,r 
            men = Men( df,db,r, group = group_tree[-1] ) # create men 
            
        if men != None:
            if len(mensur) :
                lastmen = mensur[-1]
                lastmen.append( men )
            mensur.append(men)
        
    # update group talble
    update_men_group()
    # now resolve childs
    resolve_child_mensur()

    # return topmost mensur
    return men_grp_table['MAIN']

######################################################################
# もし単独で呼び出されたら、コマンドラインプログラムとして実行する。
if __name__ == "__main__" :
    # exec this as standalone program.
    from optparse import OptionParser
    parser = OptionParser(usage = "usage: %prog [options] file.men", version = "%prog 0.1.0")
    #parser.add_option()
    opts, args = parser.parse_args()

    path = args[0]

    #read mensur file here
    fd = open(path,'r')
    lines = fd.readlines()
    fd.close()

    try:
        mtop = build_mensur( lines )
    except AssertionError , msg :
        print msg 

    #debug
    #for m in mensur:
        #print m.get_fbr()
        #print m

    m = mtop
    while( m ):
        print m
        m = m.next

    
    print men_grp_table
