#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成一个**自包含**的试玩页（含 HTML+JS，只依赖 tank_host.ui）。

    python web/standalone.py > tank.html                     # 同域后端
    python web/standalone.py --api http://127.0.0.1:8100 > tank.html

把它放进任意静态目录、把 /api/tank/ 反代到宿主服务即可。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tank_host import ui          # noqa: E402

TPL = """<!doctype html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>柏林1945 · 试玩</title>
<style>
  :root { --rule: #d8d8d8; --ink: #222; --accent: #1f6feb; }
  body { max-width: 60rem; margin: 2rem auto; padding: 0 1rem; color: var(--ink);
         font: 16px/1.7 -apple-system, "Segoe UI", Roboto, "Noto Sans SC", sans-serif; }
  h1 { font-size: 1.4rem; margin-bottom: .2rem; }
  .meta { color: #666; font-size: .9rem; }
  .lead { font-size: 1rem; }
  .plain { padding-left: 1.2rem; }
  button { font: inherit; }
</style>
</head>
<body>
<h1>柏林1945：虎王车长 · 试玩</h1>
<p class="meta">宿主层：<a href="%(host)s">berlin1945-web</a> · 游戏本体：<a href="%(game)s">berlin-tank-commander</a></p>
%(body)s
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--api', default='', help='宿主服务地址；留空 = 同域')
    ap.add_argument('--lang', default='zh', choices=('zh', 'en'))
    a = ap.parse_args()
    out = TPL % {'lang': 'zh-CN' if a.lang == 'zh' else 'en',
                 'host': ui.HOST_REPO, 'game': ui.REPO,
                 'body': ui.page_body(a.lang == 'zh', a.api)}
    # 显式按 UTF-8 写：Windows 控制台默认 GBK，页面里只要有一个非 GBK 字符
    # （中文标点以外，比如圆点、对勾）就会 UnicodeEncodeError，而且报的是
    # 一句和真正原因毫无关系的编码错。
    try:
        buf = sys.stdout.buffer
    except AttributeError:                     # 被重定向成非缓冲对象时退回文本写
        sys.stdout.write(out)
    else:
        buf.write(out.encode('utf-8'))
        buf.flush()
    return 0


if __name__ == '__main__':
    sys.exit(main())
