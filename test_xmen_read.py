# -*- coding: utf-8 -*-

import xmensur
import xmenParser as prs

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

    mentop = prs.build_mensur( lines )
 
    prs.print_mensur(mentop)
    
    # debug
    # print('mensur table')
    # for m in men_grp_table:
    #    print(men_grp_table[m])

