#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《柏林1945：虎王车长》网页试玩 —— 页面本体（HTML + JS）。

和癌症那页是"同一家人"：**地图/态势当主角，终端退成读数板**。
区别在数据来源 —— 柏林坦克**一个字都没改**，它每回合本来就打两行结构化状态：

    [回合12 | 行动3 | 米特街区 | 天气晴]
    [燃油180/200 | 机枪弹382/400 | 炮弹AP30/40 HE38/40 | 士气71/200 |
     损伤6/100 | 装甲105 | 友军坦克3 | 胜利点0(无勋章) | 崩溃10/100 |
     好感51 沦陷70 驻军4 | 逃窜敌人0]

所以宿主什么都不用动，网页直接**解析它自己打印的东西**。战斗行同理：
`战斗回合 3 | 距离480m 烟幕2 机动1 掩护1 照明0 我方压制0`。

地图怎么画：这个游戏的 LOCATIONS 是 80 个**编号平表**（没有邻接、没有坐标），
画一张"城市平面图"就是编数据。所以画的是**实际走过的行军路线** ——
节点顺序来自日志里真实出现过的地点，风险色来自游戏自己的 LOCATIONS 表
（构建时由 gen_tank_locations.py 抽出，见 tank_locations.json）。
"""

import io
import json
import os

REPO = 'https://github.com/RomanCohort/berlin-tank-commander'
HOST_REPO = 'https://github.com/RomanCohort/berlin1945-web'
MIRROR = '/repos/berlin-tank-commander/'


def _locations_json():
    """把构建时抽出的地点表内联进来。读不到就退化成空表（页面自己会兜）。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tank_locations.json')
    try:
        with io.open(path, encoding='utf-8') as fh:
            raw = fh.read()
        json.loads(raw)                     # 先验一遍，坏数据不如不内联
        return raw
    except Exception:
        return '{}'


def _keys(zh):
    label = '常用输入' if zh else 'Quick keys'
    fine = [('', '回车（默认）' if zh else 'Enter (default)'),
            ('q', 'q 退出' if zh else 'q quit'),
            ('r', 'r 重开' if zh else 'r restart')]
    out = ['<span class="bk-keyset"><span class="bk-klab">%s</span>' % label]
    for n in '123456789':
        out.append('<button type="button" class="bkey" data-v="%s">%s</button>' % (n, n))
    out.append('</span>')
    out.append('<span class="bk-keyset">')
    for v, t in fine:
        out.append('<button type="button" class="bkey" data-v="%s">%s</button>' % (v, t))
    out.append('</span>')
    return '\n        '.join(out)


def section(zh):
    if zh:
        how = (u'下面是<b>真的在跑的游戏进程</b>：你输入的每个字都送进它的标准输入。'
               u'上面那张行军图、那几条仪表，都是**从它自己打的字里解析出来的** —— '
               u'没动游戏源码一个字。')
        notes = [
            u'<b>行军路线</b>按日志里真实出现过的地点顺序画；节点颜色是游戏自己给的'
            u'<code>risk</code>（构建时从源码抽出，写在 <code>tank_locations.json</code>）。',
            u'<b>战区控制</b>是它那行总览里的「好感 / 沦陷 / 驻军」—— 和癌症那页同一个模型。',
            u'遭遇战开打时，会多出一块<b>战术面板</b>（距离 / 烟幕 / 机动 / 掩护 / 照明 / 压制）。',
            u'存档写在会话临时目录里，会话结束连目录一起删；最多 4 局，一人一局，闲置 10 分钟回收。',
        ]
        src = u'源码'
        play, auto, ph, snd = u'开始新游戏', u'看它自己打一局', u'在这里输入你的选择…', u'发送'
        idle, stop = u'还没开始。', u'结束这一局'
        h_route, h_gauge, h_sector, h_task, h_log = u'行军路线', u'车辆与士气', u'战区控制', u'任务与委托', u'战斗记录'
        no_route = u'开一局后，这里会画出你实际走过的路线。'
        no_task = u'暂未解析到任务。'
        combat_title = u'遭遇战'
    else:
        how = (u'The thing below is a <b>real game process</b>: every character you type goes to its '
               u'stdin. The march map and gauges above are parsed from what the game itself prints — '
               u'not a line of its source was changed.')
        notes = [
            u'<b>March route</b> follows the locations the log actually visited; node colour is the '
            u'game\'s own <code>risk</code>, extracted at build time into <code>tank_locations.json</code>.',
            u'<b>Sector control</b> is the favour / fall / garrison triplet from its status line — the '
            u'same model the cancer page uses.',
            u'When a firefight starts, a <b>tactical panel</b> appears (range / smoke / maneuver / '
            u'cover / illumination / suppression).',
            u'Saves live in the session temp directory and die with it. Up to 4 games, one per person, '
            u'idle sessions reclaimed after 10 minutes.',
        ]
        src = u'Source'
        play, auto, ph, snd = u'New game', u'Watch it play itself', u'type your choice here…', u'Send'
        idle, stop = u'Not started.', u'End this game'
        h_route, h_gauge, h_sector, h_task, h_log = (u'March route', u'Vehicle', u'Sector control',
                                                     u'Objectives', u'Battle log')
        no_route = u'Start a game and the route you actually took will be drawn here.'
        no_task = u'No objectives parsed yet.'
        combat_title = u'Firefight'
    lis = u'\n'.join(u'          <li>%s</li>' % n for n in notes)
    return u"""
    <div class="bk-intro">
      <p class="bk-how">%s</p>
      <p class="bk-src">%s：<a href="%s">站内镜像</a>　<a href="%s">GitHub</a>　<a href="%s">宿主层</a></p>
    </div>

    <div class="bk-stage">
      <section class="bk-panel bk-map">
        <h3>%s</h3>
        <div id="bk-route" class="bk-route"></div>
        <p class="bk-cap" id="bk-routecap">%s</p>
      </section>

      <section class="bk-panel">
        <h3>%s</h3>
        <div id="bk-gauge" class="bk-gauge"></div>
      </section>

      <section class="bk-panel">
        <h3>%s</h3>
        <div id="bk-sector" class="bk-sector"></div>
      </section>

      <section class="bk-panel">
        <h3>%s</h3>
        <div id="bk-task" class="bk-task"></div>
      </section>

      <section class="bk-panel bk-wide" id="bk-combatwrap" hidden>
        <h3>%s</h3>
        <div id="bk-combat" class="bk-combat"></div>
      </section>

      <section class="bk-panel bk-wide bk-console">
        <div class="bk-bar">
          <button type="button" id="tplay" class="bk-btn bk-btn-go">%s</button>
          <button type="button" id="tauto" class="bk-btn">%s</button>
          <button type="button" id="tstop" class="bk-btn bk-btn-quiet">%s</button>
          <span class="bk-stat" id="tstat">%s</span>
        </div>
        <h3 class="bk-logtitle">%s</h3>
        <pre id="tlog" aria-live="polite" tabindex="0"></pre>
        <div class="bk-entry" id="tbar" hidden>
          <input id="tline" type="text" placeholder="%s" aria-label="%s" maxlength="200">
          <button type="button" id="tsend" class="bk-btn bk-btn-go">%s</button>
        </div>
        <div class="bk-keys" id="tkeys" hidden>
        %s
        </div>
      </section>
    </div>

    <details class="bk-notes">
      <summary>怎么玩、数据从哪来（点开）</summary>
      <ul class="plain">
%s
      </ul>
    </details>
""" % (how, src, MIRROR, REPO, HOST_REPO,
       h_route, no_route, h_gauge, h_sector, h_task, combat_title,
       play, auto, stop, idle, h_log, ph, ph, snd, _keys(zh), lis)


CSS = u"""
<style>
/* 柏林这页和癌症那页共用一套语言（地图当主角、数据才有颜色、等宽数字），
   但配色不同：那边是"组织/血"的冷青与赤，这边是**作战地图**的土黄与钢蓝。 */
#tank {
  --bk-ink: var(--fg);
  --bk-panel: color-mix(in srgb, var(--fg) 6%, transparent);
  --bk-edge: color-mix(in srgb, var(--fg) 20%, transparent);
  --bk-safe:  #4a7f6a;
  --bk-warn:  #c9a227;
  --bk-hot:   #c0483a;
  --bk-go:    #6ea8d8;
  --bk-here:  #e0c060;
}
@media (prefers-color-scheme: light) {
  #tank { --bk-panel: #f5f6f7; --bk-edge: #d9dade; --bk-go: #2f5d8a; --bk-here: #8a6a10; }
}

#tank .bk-intro { margin: 0 0 1rem; }
#tank .bk-how { color: var(--muted); margin: 0 0 .35rem; }
#tank .bk-src { color: var(--muted); font-size: .84rem; margin: 0; }

/* 舞台破格：正文列宽放不下"图 + 三块仪表" */
#tank .bk-stage {
  display: grid; gap: 1rem; margin: 0 0 1.6rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
@media (max-width: 860px) { #tank .bk-stage { grid-template-columns: 1fr; } }
@media (min-width: 1080px) {
  #tank .bk-stage {
    position: relative; left: 50%;
    width: min(80rem, calc(100vw - 3rem));
    margin-left: calc(min(80rem, calc(100vw - 3rem)) / -2);
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
  #tank .bk-map { grid-column: span 2; }
  #tank .bk-wide { grid-column: 1 / -1; }
}

#tank .bk-panel {
  border: 1px solid var(--bk-edge); border-radius: 10px;
  background: var(--bk-panel); padding: .8rem .9rem; margin: 0; min-width: 0;
}
#tank .bk-panel h3 {
  font-size: .74rem; font-weight: 600; color: var(--muted);
  margin: 0 0 .55rem; letter-spacing: .04em;
}

/* 行军图：一条折线 + 地点节点。长路线用横向滚动，不缩成一团 */
#tank .bk-route { overflow-x: auto; }
#tank .bk-route svg { display: block; height: auto; }
#tank .bk-node { stroke: var(--bg); stroke-width: 1.5; }
#tank .bk-line { fill: none; stroke: var(--bk-edge); stroke-width: 2; }
#tank .bk-here { fill: none; stroke: var(--bk-here); stroke-width: 3; }
#tank .bk-node-lab {
  font-size: 9px; fill: var(--muted);
  font-variant-numeric: tabular-nums;
}
#tank .bk-cap { color: var(--muted); font-size: .78rem; margin: .5rem 0 0; }

/* 仪表：标签 + 条 + 等宽数字。数字全部右对齐 */
#tank .bk-g { display: grid; grid-template-columns: 4.6rem 1fr auto; gap: .45rem .5rem; align-items: center; }
#tank .bk-gk { font-size: .8rem; color: var(--muted); }
#tank .bk-gb { height: .42rem; border-radius: 2px; background: var(--rule); overflow: hidden; }
#tank .bk-gb > i { display: block; height: 100%; background: var(--bk-go); transition: width .35s ease; }
#tank .bk-gv {
  font: .78rem ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums; color: var(--fg); white-space: nowrap;
}
#tank .bk-warnfill > i { background: var(--bk-warn); }
#tank .bk-hotfill > i { background: var(--bk-hot); }

/* 战区：三格数字 + 一条沦陷条，和癌症那页的读数行同一套读法 */
#tank .bk-sector .bk-s {
  display: grid; grid-template-columns: 1fr auto; gap: .2rem .5rem;
  align-items: center; padding: .35rem 0; border-bottom: 1px solid var(--rule);
}
#tank .bk-sector .bk-s:last-child { border-bottom: none; }
#tank .bk-sname { font-weight: 600; font-size: .86rem; }
#tank .bk-snum {
  font: .78rem ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums; color: var(--muted);
}
#tank .bk-sbar { grid-column: 1 / -1; height: .4rem; border-radius: 2px; background: var(--rule); overflow: hidden; }
#tank .bk-sbar > i { display: block; height: 100%; transition: width .35s ease; }

/* 任务：名字 + 进度 + 计数 */
#tank .bk-task .bk-t {
  display: grid; grid-template-columns: 1fr auto; gap: .15rem .5rem;
  align-items: baseline; padding: .28rem 0; border-bottom: 1px solid var(--rule);
  font-size: .84rem;
}
#tank .bk-task .bk-t:last-child { border-bottom: none; }
#tank .bk-tgroup { color: var(--muted); font-size: .72rem; margin: .5rem 0 .1rem; }
#tank .bk-tgroup:first-child { margin-top: 0; }
#tank .bk-tbar { grid-column: 1 / -1; height: .3rem; border-radius: 2px; background: var(--rule); overflow: hidden; }
#tank .bk-tbar > i { display: block; height: 100%; background: var(--bk-go); }
#tank .bk-tnum {
  font: .76rem ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums; color: var(--muted);
}

/* 战术面板：一排 chip，开打了才出现 */
#tank .bk-combat { display: flex; flex-wrap: wrap; gap: .4rem; }
#tank .bk-chip {
  border: 1px solid var(--bk-edge); border-radius: 999px;
  padding: .2rem .7rem; font-size: .8rem;
}
#tank .bk-chip b { font-weight: 600; margin-left: .3rem; font-variant-numeric: tabular-nums; }
#tank .bk-chip.on { border-color: var(--bk-warn); color: var(--bk-warn); }
#tank .bk-chip.bad { border-color: var(--bk-hot); color: var(--bk-hot); }

/* 终端 */
#tank .bk-console { display: flex; flex-direction: column; }
#tank .bk-bar { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin-bottom: .5rem; }
#tank .bk-stat { color: var(--muted); font-size: .82rem; margin-left: auto; }
#tank .bk-logtitle { margin: .2rem 0 .4rem; }
#tank .bk-btn {
  padding: .32rem .85rem; border: 1px solid var(--bk-edge); border-radius: 8px;
  background: transparent; color: var(--fg); font: inherit; font-size: .86rem; cursor: pointer;
}
#tank .bk-btn:hover:enabled { border-color: var(--bk-go); }
#tank .bk-btn:focus-visible { outline: 2px solid var(--bk-go); outline-offset: 2px; }
#tank .bk-btn-go { border-color: var(--bk-go); color: var(--bk-go); font-weight: 600; }
#tank .bk-btn-quiet { color: var(--muted); }
#tank #tlog {
  margin: 0; padding: .7rem .8rem; height: 28rem; overflow: auto; resize: vertical;
  border: 1px solid var(--bk-edge); border-radius: 8px; background: transparent;
  font: 12.5px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: pre-wrap; word-break: break-word;
}
#tank #tlog:focus-visible { outline: 2px solid var(--bk-go); outline-offset: -2px; }
#tank .bk-entry { display: flex; gap: .5rem; margin-top: .6rem; }
#tank .bk-entry[hidden], #tank .bk-keys[hidden] { display: none; }
#tank #tline {
  flex: 1 1 auto; min-width: 0; padding: .4rem .6rem; border: 1px solid var(--bk-edge);
  border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem;
}
#tank .bk-keys { display: flex; flex-wrap: wrap; gap: .3rem .8rem; margin-top: .6rem; }
#tank .bk-keyset { display: inline-flex; flex-wrap: wrap; align-items: center; gap: .28rem; }
#tank .bk-klab { color: var(--muted); font-size: .74rem; }
#tank .bkey {
  padding: .18rem .5rem; border: 1px solid var(--bk-edge); border-radius: 6px;
  background: transparent; color: var(--fg); font: inherit; font-size: .8rem; cursor: pointer;
}
#tank .bkey:hover { border-color: var(--bk-go); }
#tank .bk-notes { margin-top: 1.4rem; }
#tank .bk-notes summary { cursor: pointer; color: var(--muted); font-size: .88rem; }
</style>
"""


JS = u"""
<script>
window.BK_LOC = @@LOCATIONS@@;
(function () {
  var API = window.TANK_API || '';
  var L = window.BK_LOC || {};
  var log = document.getElementById('tlog'), stat = document.getElementById('tstat'),
      bar = document.getElementById('tbar'), keys = document.getElementById('tkeys'),
      inp = document.getElementById('tline');
  var sid = null, off = 0, timer = null, inflight = false, pending = '';
  var MAXLEN = 200000;
  var NL = String.fromCharCode(10);
  var cid = 'b' + Math.random().toString(36).slice(2, 12);
  try { cid = localStorage.getItem('rc_cid') || cid; localStorage.setItem('rc_cid', cid); } catch (e) {}

  // ── 风险色：游戏自己给的 risk（0..1）→ 土黄到铁锈红 ───────────────
  function riskColor(r) {
    r = Math.max(0, Math.min(1, r || 0));
    var a = [74, 127, 106], b = [192, 72, 58];
    if (r > 0.6) { a = [201, 162, 39]; b = [192, 72, 58]; r = (r - 0.6) / 0.4; }
    else { r = r / 0.6; }
    return 'rgb(' + a.map(function (v, i) { return Math.round(v + (b[i] - v) * r); }).join(',') + ')';
  }
  function byName(name) {
    for (var k in L) { if (L.hasOwnProperty(k) && L[k].name === name) { return L[k]; } }
    return null;
  }
  function say(t) {
    if (!t) return;
    log.textContent += t;
    if (log.textContent.length > MAXLEN) {
      log.textContent = '[……前面的内容太长，已经滚掉了]' + log.textContent.slice(-150000);
    }
    log.scrollTop = log.scrollHeight;
  }
  function show(t) { stat.textContent = t; }
  function err(d, what) { return (d && (d.detail || d.error)) || what; }
  function stopTimer() { if (timer) { clearInterval(timer); timer = null; } }

  // ── 状态：全部从游戏自己打的两行里解析 ────────────────────────────
  var S = { visited: [], loc: '', turn: 0, ap: 0, weather: '', gauges: {},
            sector: null, tasks: [], combat: null };

  //<PARSE> —— 这一块被 test_tank_parse.py 原样抠出来喂真日志做单测，
  //         所以别在这里引用 DOM 或其它外部变量（只依赖 S 和正则）。
  function num(re, s, i) { var m = s.match(re); return m ? Number(m[i || 1]) : null; }

  function parseLine(l) {
    var m;
    // 方括号那两行（回合 / 资源总览）
    if (l.charAt(0) === '[') {
      m = l.match(/^\\[回合(\\d+) \\| 行动(\\d+) \\| ([^|\\]]+) \\| 天气(\\S+)\\]/);
      if (m) {
        S.turn = Number(m[1]); S.ap = Number(m[2]);
        S.loc = m[3].trim(); S.weather = m[4];
        if (S.visited[S.visited.length - 1] !== S.loc) { S.visited.push(S.loc); }
        return true;
      }
    }
    if (l.indexOf('[燃油') === 0) {
      var g = {};
      g.fuel = [num(/燃油(\\d+)/, l), num(/燃油\\d+\\/(\\d+)/, l)];
      g.mg = [num(/机枪弹(\\d+)/, l), num(/机枪弹\\d+\\/(\\d+)/, l)];
      g.ap = [num(/炮弹AP(\\d+)/, l), num(/炮弹AP\\d+\\/(\\d+)/, l)];
      g.he = [num(/炮弹AP\\d+\\/\\d+ HE(\\d+)/, l), num(/HE(\\d+)\\/\\d+/, l)];
      g.morale = [num(/士气(\\d+)/, l), num(/士气\\d+\\/(\\d+)/, l)];
      g.damage = [num(/损伤(\\d+)/, l), num(/损伤\\d+\\/(\\d+)/, l)];
      g.collapse = [num(/崩溃(\\d+)/, l), num(/崩溃\\d+\\/(\\d+)/, l)];
      S.gauges = g;
      S.armor = num(/装甲(\\d+)/, l);
      S.allyTanks = num(/友军坦克(\\d+)/, l);
      S.vp = num(/胜利点(\\d+)/, l);
      S.fleeing = num(/逃窜敌人(\\d+)/, l);
      S.tankKills = num(/坦克击毁(\\d+)/, l);
      var s = l.match(/好感(\\d+) 沦陷(\\d+) 驻军(\\d+)/);
      if (s) { S.sector = { favor: Number(s[1]), fall: Number(s[2]), garrison: Number(s[3]) }; }
      return true;
    }
    // 战斗行：没有方括号，以「战斗回合」开头
    if (l.indexOf('战斗回合') === 0) {
      S.combat = {
        round: num(/战斗回合\\s*(\\d+)/, l),
        dist: (l.match(/距离([^\\s]+)/) || [, ''])[1],
        smoke: num(/烟幕(\\d+)/, l), maneuver: num(/机动(\\d+)/, l),
        cover: num(/掩护(\\d+)/, l), light: num(/照明(\\d+)/, l),
        suppress: num(/我方压制(\\d+)/, l)
      };
      return true;
    }
    // 任务 / 委托行：以 "-" 开头（这一段原来写在"非方括号"那一支里，
    // 结果被那句 return false 挡在前面，永远走不到 —— 单测抓到的）
    // 用 \\u2022 而不是直接把圆点写进正则：页面源码里带非 GBK 字符时，
    // 在 Windows 控制台跑生成器会 UnicodeEncodeError（实测踩过）。
    m = l.match(/^[-\\u2022]\\s*(.+?)\\s*\\[(进行中|已完成|失败)\\][^0-9]*(\\d+)\\/(\\d+)/);
    if (m) {
      S.tasks.push({ name: m[1].trim(), state: m[2], done: Number(m[3]), need: Number(m[4]) });
      if (S.tasks.length > 40) { S.tasks.shift(); }
      return true;
    }
    return false;
  }
  //</PARSE>

  function paint() {
    paintRoute(); paintGauges(); paintSector(); paintTasks(); paintCombat();
  }

  function paintRoute() {
    var el = document.getElementById('bk-route');
    var cap = document.getElementById('bk-routecap');
    var v = S.visited;
    if (!v.length) {
      el.innerHTML = '<p class="bk-cap">' + (window.BK_TXT || {}).noRoute + '</p>';
      return;
    }
    var W = Math.max(320, v.length * 74 + 40), H = 132;
    var parts = ['<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" role="img">'];
    var pts = [], i, x, y = 74;
    for (i = 0; i < v.length; i++) { x = 30 + i * 74; pts.push([x, y]); }
    var d = '';
    for (i = 0; i < pts.length; i++) {
      d += (i ? ' L' : 'M') + pts[i][0] + ' ' + pts[i][1];
    }
    parts.push('<path class="bk-line" d="' + d + '"/>');
    for (i = 0; i < v.length; i++) {
      var info = byName(v[i]), risk = info ? info.risk : 0;
      var last = (i === v.length - 1);
      parts.push('<circle class="bk-node" cx="' + pts[i][0] + '" cy="' + y + '" r="' + (last ? 11 : 8)
        + '" fill="' + riskColor(risk) + '"><title>' + v[i]
        + '　risk ' + risk.toFixed(2)
        + (info && info.tags.length ? '　' + info.tags.join('/') : '') + '</title></circle>');
      if (last) {
        parts.push('<circle class="bk-here" cx="' + pts[i][0] + '" cy="' + y + '" r="17"/>');
      }
      parts.push('<text class="bk-node-lab" x="' + pts[i][0] + '" y="' + (y + 30)
        + '" text-anchor="middle">' + (i + 1) + '</text>');
    }
    parts.push('</svg>');
    el.innerHTML = parts.join('');
    el.scrollLeft = el.scrollWidth;
    var cur = byName(S.loc);
    cap.textContent = '第 ' + v.length + ' 站 · ' + S.loc
      + (cur ? '　risk ' + cur.risk.toFixed(2) : '')
      + (S.weather ? '　天气' + S.weather : '');
  }

  function gauge(label, pair, warn, hot) {
    if (!pair || pair[0] == null) { return ''; }
    var v = pair[0], max = pair[1] || 1;
    var cls = 'bk-gb' + (hot ? ' bk-hotfill' : (warn ? ' bk-warnfill' : ''));
    return '<span class="bk-gk">' + label + '</span>'
      + '<span class="' + cls + '"><i style="width:' + Math.min(100, v / max * 100) + '%"></i></span>'
      + '<span class="bk-gv">' + v + '/' + max + '</span>';
  }

  function paintGauges() {
    var el = document.getElementById('bk-gauge'), g = S.gauges || {};
    var h = '<div class="bk-g">';
    h += gauge('燃油', g.fuel) + gauge('机枪弹', g.mg) + gauge('炮弹 AP', g.ap) + gauge('炮弹 HE', g.he);
    h += gauge('士气', g.morale, true, false)
       + gauge('损伤', g.damage, false, false)
       + gauge('崩溃', g.collapse, true, true);
    h += '<span class="bk-gk">装甲</span><span></span><span class="bk-gv">'
       + (S.armor == null ? '—' : S.armor) + '</span>';
    h += '<span class="bk-gk">友军坦克</span><span></span><span class="bk-gv">'
       + (S.allyTanks == null ? '—' : S.allyTanks) + '</span>';
    h += '<span class="bk-gk">胜利点</span><span></span><span class="bk-gv">'
       + (S.vp == null ? '—' : S.vp) + '</span>';
    h += '</div>';
    el.innerHTML = h;
  }

  function paintSector() {
    var el = document.getElementById('bk-sector');
    if (!S.sector) { el.innerHTML = '<p class="bk-cap">—</p>'; return; }
    var s = S.sector;
    el.innerHTML = '<div class="bk-s">'
      + '<span class="bk-sname">' + (S.loc || '当前街区') + '</span>'
      + '<span class="bk-snum">好感 ' + s.favor + '　驻军 ' + s.garrison + '</span>'
      + '<span class="bk-sbar"><i style="width:' + Math.min(100, s.fall)
      + '%;background:' + riskColor(s.fall / 100) + '"></i></span>'
      + '</div>'
      + '<p class="bk-cap">沦陷 ' + s.fall + '%　'
      + (S.fleeing == null ? '' : '逃窜敌人 ' + S.fleeing) + '</p>';
  }

  function paintTasks() {
    var el = document.getElementById('bk-task');
    if (!S.tasks.length) { el.innerHTML = '<p class="bk-cap">—</p>'; return; }
    var seen = {}, h = '';
    for (var i = 0; i < S.tasks.length; i++) {
      var t = S.tasks[i];
      // 同名任务只留最后一条（游戏每回合重印一遍）
      seen[t.name] = t;
    }
    for (var k in seen) {
      if (!seen.hasOwnProperty(k)) { continue; }
      var x = seen[k], pct = x.need ? Math.min(100, x.done / x.need * 100) : 0;
      h += '<div class="bk-t"><span>' + k + '</span>'
        + '<span class="bk-tnum">' + x.done + '/' + x.need + '</span>'
        + '<span class="bk-tbar"><i style="width:' + pct + '%"></i></span></div>';
    }
    el.innerHTML = h;
  }

  function chip(label, val, cls) {
    return '<span class="bk-chip ' + (cls || '') + '">' + label + '<b>'
      + (val == null ? '—' : val) + '</b></span>';
  }

  function paintCombat() {
    var wrap = document.getElementById('bk-combatwrap');
    var el = document.getElementById('bk-combat');
    var c = S.combat;
    if (!c) { wrap.hidden = true; return; }
    wrap.hidden = false;
    el.innerHTML = chip('距离', c.dist || '—')
      + chip('烟幕', c.smoke, c.smoke ? 'on' : '')
      + chip('机动', c.maneuver, c.maneuver ? 'on' : '')
      + chip('掩护', c.cover, c.cover ? 'on' : '')
      + chip('照明', c.light, c.light ? 'on' : '')
      + chip('我方压制', c.suppress, c.suppress ? 'bad' : '');
  }

  function ingest(text) {
    if (!text) return;
    pending += text;
    var cut = pending.lastIndexOf(NL);
    if (cut < 0) { return; }
    var whole = pending.slice(0, cut + 1);
    pending = pending.slice(cut + 1);
    var lines = whole.split(NL), keep = [], dirty = false;
    for (var i = 0; i < lines.length; i++) {
      if (parseLine(lines[i])) { dirty = true; }
      keep.push(lines[i]);
    }
    say(keep.join(NL));
    if (dirty) { paint(); }
  }

  // ── 会话（沿用和癌症那页同一套桥）────────────────────────────────
  function start(mode) {
    stopTimer(); sid = null; off = 0;
    S.visited = []; S.tasks = []; S.combat = null;
    log.textContent = '正在启动游戏进程…' + NL;
    show('启动中…');
    bar.hidden = true; keys.hidden = true;
    fetch(API + '/api/tank/new?mode=' + mode + '&client_id=' + encodeURIComponent(cid),
          { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.sid) { say(NL + err(d, '开不了新局。') + NL); show('开不了新局'); resume(); return; }
        sid = d.sid; off = d.off || 0;
        say(d.text || '');
        if (d.kind === 'auto') { show('旁观模式：它自己在打'); }
        else { show('进行中（会话 ' + sid + '）'); bar.hidden = false; keys.hidden = false; inp.focus(); }
        ingest(d.text || '');
        poll(); timer = setInterval(poll, 700);
      })
      .catch(function (e) { say(NL + '出错了：' + ((e && e.message) || '请求失败')); show('出错'); });
  }

  function poll() {
    if (!sid || inflight) return;
    inflight = true;
    fetch(API + '/api/tank/poll?sid=' + encodeURIComponent(sid) + '&off=' + off)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || d.detail) { say(NL + err(d, '会话丢了。') + NL); show('会话丢了'); stopTimer(); return; }
        if (d.truncated) { say(NL + '[……输出太快，中间一段没跟上]' + NL); }
        ingest(d.text || '');
        off = d.off;
        if (!d.alive) {
          stopTimer(); show('这一局结束。再开一局，或看它自己打一局。');
          bar.hidden = true; keys.hidden = true;
        }
      })
      .catch(function () {})
      .then(function () { inflight = false; });
  }

  function send(v) {
    if (!sid) return;
    fetch(API + '/api/tank/send?sid=' + encodeURIComponent(sid) + '&line=' + encodeURIComponent(v),
          { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.detail) { show(d.detail); } })
      .catch(function () {});
    setTimeout(poll, 120);
  }

  document.getElementById('tplay').addEventListener('click', function () { start('play'); });
  document.getElementById('tauto').addEventListener('click', function () { start('auto'); });
  document.getElementById('tstop').addEventListener('click', function () {
    var old = sid;
    sid = null; stopTimer();
    fetch(API + '/api/tank/close?sid=' + encodeURIComponent(old || '')
          + '&client_id=' + encodeURIComponent(cid), { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        show((d && d.closed) ? '已结束，可以再开一局。' : '现在没有在跑的局。');
        bar.hidden = true; keys.hidden = true;
      })
      .catch(function () { show('结束失败，稍后再试。'); });
  });
  document.getElementById('tsend').addEventListener('click', function () {
    var v = inp.value; inp.value = ''; send(v);
  });
  inp.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); var v = inp.value; inp.value = ''; send(v); }
  });
  var kb = document.querySelectorAll('.bkey');
  for (var q = 0; q < kb.length; q++) {
    kb[q].addEventListener('click', function () { send(this.getAttribute('data-v')); });
  }

  function resume() {
    fetch(API + '/api/tank/mine?client_id=' + encodeURIComponent(cid))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.sid) { show('没有在跑的局。点「开始新游戏」。'); return; }
        if (d.sid === sid) {
          show('已接回上一局。');
          if (!timer) { poll(); timer = setInterval(poll, 700); }
          bar.hidden = false; keys.hidden = false;
          return;
        }
        sid = d.sid; off = 0;
        log.textContent = '（接回上一局，会话 ' + sid + '）' + NL;
        show('已接回上一局（闲置 ' + (d.idle || 0) + ' 秒）');
        bar.hidden = false; keys.hidden = false;
        stopTimer(); poll(); timer = setInterval(poll, 700);
      })
      .catch(function () {});
  }

  paint();
  resume();
})();
</script>
"""


def page_body(zh, api_base=""):
    """整块页面内容（说明 + 行军图 + 仪表 + 战区 + 任务 + 战术 + 终端 + JS）。"""
    js = JS.replace('@@LOCATIONS@@', _locations_json())
    txt = {'noRoute': u'开一局后，这里会画出你实际走过的路线。' if zh
           else u'Start a game and the route you actually took will be drawn here.'}
    return (u'<script>window.TANK_API = %s;window.BK_TXT = %s;</script>\n'
            % (u"'" + api_base + u"'", json.dumps(txt, ensure_ascii=False))
            + section(zh) + CSS + js)
