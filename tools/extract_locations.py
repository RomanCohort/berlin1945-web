#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从游戏源码里抽出 LOCATIONS 表，生成 tank_host/tank_locations.json。

页面上的行军图要用游戏自己的 risk / tags —— 网页不该自己再编一份，否则迟早漂。
所以这一步在**构建时**读一次游戏源码，产出 JSON，页面把它内联进去。

    python tools/extract_locations.py                       # 用默认路径
    python tools/extract_locations.py --game /path/game.py
    python tools/extract_locations.py --check                # 只比对，不写（CI 用）
"""
import argparse
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_GAME = os.environ.get("TANK_GAME", "/opt/tank-demo/game.py")
OUT = os.path.join(ROOT, "tank_host", "tank_locations.json")


def extract(game_path):
    lines = io.open(game_path, encoding="utf-8", errors="replace").read().splitlines()
    start = None
    for i, l in enumerate(lines):
        if l.startswith("LOCATIONS = {"):
            start = i
            break
    if start is None:
        raise SystemExit("在 %s 里找不到 LOCATIONS" % game_path)
    depth, end = 0, None
    for k in range(start, len(lines)):
        depth += lines[k].count("{") - lines[k].count("}")
        if k > start and depth <= 0:
            end = k
            break
    if end is None:
        raise SystemExit("LOCATIONS 的括号没闭合")
    # 这是字典字面量，ast 直接求值就行 —— 别自己写解析器
    value = ast.literal_eval(ast.parse("\n".join(lines[start:end + 1])).body[0].value)
    slim = {}
    for key, item in value.items():
        if not isinstance(item, dict):
            continue
        slim[str(key)] = {"name": item.get("name") or "",
                          "risk": float(item.get("risk") or 0.0),
                          "tags": list(item.get("tags") or [])}
    return slim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--out", default=OUT, help="输出路径（默认 tank_host/tank_locations.json）")
    ap.add_argument("--check", action="store_true",
                    help="只比对：和已提交的 JSON 不一致就退出 1（不改文件）")
    args = ap.parse_args()
    if not os.path.exists(args.game):
        print("[locations] 找不到游戏源码 %s（用 --game 指定）" % args.game)
        return 1
    slim = extract(args.game)
    new = json.dumps(slim, ensure_ascii=False, indent=0, sort_keys=True)
    if args.check:
        old = io.open(args.out, encoding="utf-8").read() if os.path.exists(args.out) else ""
        if json.loads(old or "{}") == slim:
            print("[locations] 与 %s 一致（%d 个地点）" % (args.out, len(slim)))
            return 0
        print("[locations] 不一致：游戏里的 LOCATIONS 变了，请重跑本脚本并提交")
        return 1
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(new)
    print("[locations] 写入 %s（%d 个地点）" % (args.out, len(slim)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
