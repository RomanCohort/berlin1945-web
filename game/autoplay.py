#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""旁观模式：让《柏林1945》用默认输入自己打完一局，把过程打到 stdout。

游戏自带的 InputStream 支持 default_when_empty —— 每个提示都回车走默认，
一局 0.4 秒就跑完（实测 21 章、两千多行输出）。用它做一个「看它自己打一局」
的按钮，成本几乎为零：同一个会话机制，只是不接受输入。

不修改游戏本体，只 import 它。
"""
import importlib.util
import os
import sys

GAME = os.environ.get('TANK_GAME', '/srv/tank-demo/game.py')

spec = importlib.util.spec_from_file_location('berlin1945', GAME)
g = importlib.util.module_from_spec(spec)
sys.modules['berlin1945'] = g          # dataclasses 需要能在 sys.modules 里找到它
spec.loader.exec_module(g)

rng = g._rng_from_env()
ins = g.InputStream(default_when_empty=True)
try:
    name, callsign, diff, breakout = g.intro(ins)
    s = g.build_state(ins, name, callsign, diff, rng, breakout)
    g.main_loop(ins, s)
except SystemExit:
    pass
except Exception as e:                 # 游戏自己崩了也要把原因说清楚
    print('\n[旁观模式中断] %s: %s' % (type(e).__name__, e))
print('\n[旁观模式结束] 这一局是自动走的默认选项，不是真人操作。')
