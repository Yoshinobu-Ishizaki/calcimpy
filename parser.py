#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
WIIIのファイル表現とデータそのものの間を取り持つControllerクラス
単独でシェルから呼び出されると、コマンドラインプログラムとしても機能する。
"""

import re
# import numpy as np
import xmensur as xmn

# 予約語
# BRANCH = VALVE_OUT, MERGE = VALVE_IN, SPLIT = TONEHOLE
# Aliases
# < = BRANCH, > MERGE, | = SPLIT
# [ = MAIN, ] = END_MAIN
# { = GROUP, } = END_GROUP

type_keywords = ('SPLIT', 'VALVE_OUT', 'MERGE', 'VALVE_IN', 'TONEHOLE', 'BRANCH','OPEN_END', 'CLOSED_END', '<', '>', '|')
group_keywords = ('MAIN', 'END_MAIN', 'GROUP', 'END_GROUP', '[', ']', '{', '}')

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

def men_by_kwd( cur, lst ):
    """
    Handle BRANCH, MERGE, TONEHOLE,...
    Returns new Men item.
    """
    key = lst[0]
    if len(lst) > 2:
        name = lst[1]
        ratio = resolve_vars(lst[2:3])[0]

    df,db,r = cur.get_fbr()
    gp = cur.group

    men = None
    
    if key == 'BRANCH' or key == 'VALVE_OUT' or key == '<':
        men = xmn.Men( db, db, 0, gp, sidename = name, sidetype = 'BRANCH', sideratio = ratio )
    elif key == 'MERGE' or key =='VALVE_IN' or key == '>':
        men = xmn.Men( db, db, 0, gp, sidename = name, sidetype = 'MERGE', sideratio = ratio )
    elif key == 'SPLIT' or key == 'TONEHOLE' or key == '|':
        men = xmn.Men( db, db, 0, gp, sidename = name, sidetype = 'SPLIT', sideratio = ratio )
    elif key == 'OPEN_END':
        men = xmn.Men( db, db, 0 , gp )
    elif key == 'CLOSED_END':
        men = xmn.Men( db, 0, 0, gp )
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

def resolve_child_mensur():
    """Connect side mensur to Main"""
    men = men_grp_table['MAIN'] # top mensur cell

    while men:
        if men.sidename != '':
            if men.sidetype != 'MERGE':
                ms = men_grp_table[men.sidename]
            else:
                ms = end_mensur(men_grp_table[men.sidename])

            men.setside(ms)
        
        men = men.next

def print_mensur(men):
    while men:
        print(men) # output __str__
        if men.side:
            if men.sidetype != 'MERGE' and men.sideratio > HALF:
                men = men.side
            elif not men.next: # branch end
                men = men.side
            else:
                men = men.next
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
                men = xmn.Men( df,db,r, group = gnm ) # create men 

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

    mentop = build_mensur( lines )
 
    print_mensur(mentop)
    
    # debug
    # print('mensur table')
    # for m in men_grp_table:
    #    print(men_grp_table[m])

