#!/bin/env python
# -*- coding: utf-8 -*-

# from math import *
import numpy as np

"""
xmensur コアルーチン
"""

class Men(object):
    """メンズール要素のクラス"""
    def __init__(self, df = 0, db = 0, r = 0, group = None, prev = None, next = None, side = None, sidename = '', sidetype = None, sideratio = 1 ):
        self.df = df
        self.db = db
        self.r = r
        self.group = group # グループ管理
        self.next = next # next Men
        self.prev = prev # prev Men
        self.sidename = sidename # name of side men for searching later.
        self.side = side # side Men ( BRANCH, MERGE, TONEHOLE )
        self.sidetype = sidetype #BRANCH,MERGE,TONEHOLE ...
        self.sideratio = sideratio # 断面接続係数
        # 後で計算される
        self.p0 = 0 # 入口(マウスピース側)音圧
        self.u0 = 0 # 入口(マウスピース側)体積速度
        self.p1 = 0 # 出口(ベル側)音圧
        self.u1 = 0 # 出口(ベル側)体積速度
        self.xL = 0 # 入口位置でのメンズール全体先頭からの合計距離
        # 次との断面積の接続係数
        self.r_side = 1

    def append(self, next = None):
        """Append next Men to this."""
        self.next = next
        self.next.prepend(self)

    def prepend(self, prev = None):
        """Set prev Men."""
        self.prev = prev
    
    def setside(self, side = None):
        self.side = side
        side.side = self
        
    def get_fbr(self):
        return self.df, self.db, self.r 

    def __str__(self):
        return '%g,%g,%g,%s' % (self.df, self.db, self.r, self.group)

            