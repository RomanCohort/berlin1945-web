#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拿**真日志**单测页面里的解析块。

做法：从 tank_host/ui.py 生成的页面里抠出 //<PARSE> 之间那段（只依赖 S 和正则），
配上 node 跑真行。加这个是因为第一次跑就抓到一个真 bug：任务行以 `-` 开头，
会掉进"非方括号"那一支，而那支末尾的 return false 把它挡在后面 ——
页面上的「任务与委托」会永远是空的，而肉眼看不出来。

    python tests/parse_test.py
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tank_host import ui          # noqa: E402

SAMPLES = [
    "[回合1 | 行动3 | 米特街区 | 天气晴]",
    "[燃油200/200 | 机枪弹400/400 | 炮弹AP40/40 HE40/40 | 士气71/200 | 损伤6/100"
    " | 装甲105 | 友军坦克3 | 胜利点0(无勋章) | 崩溃10/100 | 好感51 沦陷70 驻军4 | 逃窜敌人0]",
    "[燃油188/200 | 机枪弹362/400 | 炮弹AP36/40 HE39/40 | 士气64/200 | 损伤22/100"
    " | 装甲98 | 友军坦克2 | 胜利点3(铁十字) | 崩溃18/100 | 好感44 沦陷76 驻军3"
    " | 逃窜敌人2 | 坦克击毁1 成就2]",
    "- 护送撤离 [进行中] 0/2",
    "- 肃清敌人 [进行中] 2/2",
    "战斗回合 3  | 距离480m 烟幕2 机动1 掩护1 照明0 我方压制0",
]


def extract(page_body):
    m = re.search(r"//<PARSE>[^\n]*\n(.*?)//</PARSE>", page_body, re.S)
    if not m:
        raise SystemExit("抠不到解析块（//<PARSE> 标记没了吗？）")
    return m.group(1)


def main():
    block = extract(ui.page_body(True))
    harness = (
        "var S = { visited: [], loc: '', turn: 0, ap: 0, weather: '', gauges: {},\n"
        "          sector: null, tasks: [], combat: null };\n" + block +
        "\nvar lines = " + json.dumps(SAMPLES, ensure_ascii=False) + ";\n"
        "lines.forEach(function (l) { parseLine(l); });\n"
        "if (S.turn !== 1 || S.loc !== '米特街区') { throw new Error('回合/地点没解析到'); }\n"
        "// 两行总览都喂进去：后一行必须覆盖前一行\n"
        "if (!S.sector || S.sector.favor !== 44 || S.sector.fall !== 76"
        " || S.sector.garrison !== 3) { throw new Error('战区: ' + JSON.stringify(S.sector)); }\n"
        "if (S.gauges.fuel[0] !== 188 || S.gauges.he[0] !== 39 || S.gauges.collapse[0] !== 18)"
        " { throw new Error('仪表: ' + JSON.stringify(S.gauges)); }\n"
        "if (S.armor !== 98 || S.vp !== 3 || S.tankKills !== 1) { throw new Error('数值'); }\n"
        "if (S.tasks.length !== 2 || S.tasks[0].name !== '护送撤离' || S.tasks[0].need !== 2)"
        " { throw new Error('任务: ' + JSON.stringify(S.tasks)); }\n"
        "if (!S.combat || S.combat.dist !== '480m' || S.combat.smoke !== 2)"
        " { throw new Error('战斗: ' + JSON.stringify(S.combat)); }\n"
        "if (S.visited.length !== 1) { throw new Error('路线没记录'); }\n"
        "console.log('parse ok');\n"
    )
    path = os.path.join(ROOT, "tests", "parse_test.js")
    io.open(path, "w", encoding="utf-8").write(harness)
    r = subprocess.run(["node", path], capture_output=True)
    if r.returncode == 0:
        print("[parse_test] PASS  " + r.stdout.decode("utf-8", "replace").strip())
        return 0
    print("[parse_test] FAIL")
    print(r.stderr.decode("utf-8", "replace")[:800])
    return 1


if __name__ == "__main__":
    sys.exit(main())
