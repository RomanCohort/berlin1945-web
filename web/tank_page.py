#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染「柏林1945」试玩页 —— /tank/ 与 /tank/en/。

页面内容（HTML/JS）在 tankui.py 里，这一层只负责套站点外壳 —— 这样仓库里
那份独立部署用的演示页和线上页面共用同一份前端。
site.yml 里标 dynamic: true，让 sitepages 跳过本页。
"""
import os
import sys

sys.path.insert(0, '/opt/sitegen')
import sitegen as S          # noqa: E402
import sitepages as SP       # noqa: E402
import tankui                # noqa: E402


def main():
    cfg = S.load_config()
    page = None
    for p in (cfg.get('pages') or []):
        if p.get('id') == 'tank':
            page = p
            break
    if not page:
        print('[tank] site.yml 里没有 id: tank 的页，什么都不做')
        return 1
    base = page['path'].rstrip('/')
    for lang, suffix in (('zh', '/index.html'), ('en', '/en/index.html')):
        p = dict(page)
        p['body_zh' if lang == 'zh' else 'body_en'] = tankui.page_body(lang == 'zh')
        html_out = SP.render_subpage(cfg, lang, p)
        out = os.path.join(S.WEBROOT, base.lstrip('/') + suffix)
        d = os.path.dirname(out)
        if not os.path.isdir(d):
            os.makedirs(d)
        tmp = out + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            fh.write(html_out)
        os.replace(tmp, out)
        print('[tank] 写入 %s (%d 字节)' % (out, len(html_out.encode('utf-8'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
