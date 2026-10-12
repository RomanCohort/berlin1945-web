#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《柏林1945：虎王车长》网页试玩 —— 页面本体（HTML + JS）。

**不依赖任何站点框架**：仓库那份自包含演示页（web/standalone.py）和线上站点
（/opt/sitegen/tank_page.py）用的都是这一份 —— 抄两遍迟早漂。

页面只干一件事：把游戏子进程的 stdin/stdout 接到浏览器上（后端见 sessions.py）。
  · 输入：文本框 + 15 个快捷键（数字 0-9 / 回车 / A 自动存档 / 突围 / q / r
    —— 这些键是**扫游戏源码扫出来的**，见 README）
  · 输出：等宽 pre，按 offset 增量轮询，超过 20 万字符自动滚掉前半
  · 刷新页面后按访客身份把上一局接回来（GET /api/tank/mine）

window.TANK_API 可以指定后端前缀（留空＝同域）。
"""

REPO = 'https://github.com/RomanCohort/berlin-tank-commander'
HOST_REPO = 'https://github.com/RomanCohort/berlin1945-web'


def section(zh):
    if zh:
        lead = (u'《柏林1945：虎王车长》—— 站主写的文字冒险。你是一辆虎王坦克的车长，'
                u'在每一个路口决定让谁活下来。')
        how = (u'这里是<b>真的在玩</b>：服务器上跑着一个游戏进程，你在下面输入的每一个选择'
               u'都会送到它的标准输入 —— 不是脚本回放，也不是录像。')
        notes = [u'游戏本体一个字都没改，只是把它的输入输出接到了网页上。',
                 u'存档、事件记录都只写在这一局的临时目录里，会话一结束就删掉。',
                 u'同时最多 4 局；一个人一局；闲置 10 分钟自动回收。',
                 u'常用：数字选择、直接回车用默认值、q 退出、r 重开。']
        play, auto, ph, snd = u'开始新游戏', u'看它自己打一局', u'在这里输入你的选择…', u'发送'
        quick, src, idle = u'常用输入', u'源码：', u'还没开始 —— 点上面任一按钮。'
        stop = u'结束这一局'
    else:
        lead = (u'Berlin 1945: Tiger II Commander — a text adventure by this site\'s owner. '
                u'You are the commander of a Tiger II; every crossroads decides who lives.')
        how = (u'This is a <b>real session</b>: a game process runs on the server and everything '
               u'you type below goes straight to its stdin — not a replay, not a recording.')
        notes = [u'The game itself is unmodified; only its stdin/stdout are bridged to the web.',
                 u'Saves and event logs are written to this session\'s temp directory and deleted with it.',
                 u'Up to 4 games at once, one per person; idle sessions are reclaimed after 10 minutes.',
                 u'Handy: digits to choose, Enter for the default, q to quit, r to restart.']
        play, auto, ph, snd = u'New game', u'Watch it play itself', u'type your choice here…', u'Send'
        quick, src, idle = u'Quick keys', u'Source: ', u'Not started — pick one of the buttons above.'
        stop = u'End this game'
    lis = u'\n'.join(u'    <li>%s</li>' % n for n in notes)
    btn = ('padding:.45rem 1rem;border:1px solid var(--rule);border-radius:6px;'
           'cursor:pointer;font:inherit')
    return u"""
<section id="tank">
  <p class="lead">%s</p>
  <p class="lead">%s</p>
  <p class="meta">%s<a href="%s">%s</a></p>
  <ul class="plain">
%s
  </ul>
  <p>
    <button type="button" id="tplay" style="%s">%s</button>
    <button type="button" id="tauto" style="%s">%s</button>
    <button type="button" id="tstop" style="%s">%s</button>
    <span class="meta" id="tstat" style="margin-left:.6rem">%s</span>
  </p>
  <pre id="tlog" aria-live="polite" style="background:#101418;color:#d8e0e8;border-radius:8px;
       padding:.9rem 1rem;height:32rem;overflow:auto;font:13px/1.5 ui-monospace,Consolas,Menlo,monospace;
       white-space:pre-wrap;word-break:break-word"></pre>
  <p id="tbar" style="display:none">
    <input id="tline" type="text" placeholder="%s" aria-label="%s" maxlength="200"
           style="padding:.45rem .6rem;border:1px solid var(--rule);border-radius:6px;font:inherit;width:70%%">
    <button type="button" id="tsend" style="%s">%s</button>
  </p>
  <p id="tkeys" style="display:none">
    <span class="meta">%s</span>
    <span class="tkeyset">
      <button type="button" class="tkey" data-v="1">1</button>
      <button type="button" class="tkey" data-v="2">2</button>
      <button type="button" class="tkey" data-v="3">3</button>
      <button type="button" class="tkey" data-v="4">4</button>
      <button type="button" class="tkey" data-v="5">5</button>
      <button type="button" class="tkey" data-v="6">6</button>
      <button type="button" class="tkey" data-v="7">7</button>
      <button type="button" class="tkey" data-v="8">8</button>
      <button type="button" class="tkey" data-v="9">9</button>
      <button type="button" class="tkey" data-v="0">0</button>
    </span>
    <span class="tkeyset">
      <button type="button" class="tkey" data-v="">回车（默认）</button>
      <button type="button" class="tkey" data-v="A">A（自动存档）</button>
      <button type="button" class="tkey" data-v="突围">突围</button>
      <button type="button" class="tkey" data-v="q">q（退出）</button>
      <button type="button" class="tkey" data-v="r">r（重开）</button>
    </span>
  </p>
</section>
""" % (lead, how, src, REPO, REPO.split('//', 1)[1], lis,
       btn, play, btn, auto, btn, stop, idle, ph, ph, btn, snd, quick)


JS = u"""
<script>
(function () {
  var API = window.TANK_API || '';
  var log = document.getElementById('tlog'), stat = document.getElementById('tstat'),
      bar = document.getElementById('tbar'), keys = document.getElementById('tkeys'),
      inp = document.getElementById('tline');
  var sid = null, off = 0, timer = null;
  var MAXLEN = 200000;      // 日志别无限长（旁观模式一次就两千多行）
  // 和站里其它页共用一个访客 id：限流按它计数（隧道/本机代理下拿不到真 IP）
  var cid = localStorage.getItem('rc_cid');
  if (!cid) { cid = 'c' + Math.random().toString(36).slice(2, 12); localStorage.setItem('rc_cid', cid); }
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
  function stop() { if (timer) { clearInterval(timer); timer = null; } }
  function start(mode) {
    stop(); sid = null; off = 0;
    log.textContent = '正在启动游戏进程…\\n';
    show('启动中…');
    bar.style.display = 'none'; keys.style.display = 'none';
    fetch(API + '/api/tank/new?mode=' + mode + '&client_id=' + encodeURIComponent(cid), { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.sid) { say('\\n' + err(d, '开不了新局。')); show('开不了新局'); return; }
        sid = d.sid; off = d.off || 0;
        say(d.text || '');
        if (d.kind === 'auto') { show('旁观模式：它自己在打'); }
        else {
          show('进行中（会话 ' + sid + '）');
          bar.style.display = ''; keys.style.display = ''; inp.focus();
        }
        poll();
        timer = setInterval(poll, 700);
      })
      .catch(function (e) { say('\\n出错了：' + ((e && e.message) || '请求失败')); show('出错'); });
  }
  function poll() {
    if (!sid) return;
    fetch(API + '/api/tank/poll?sid=' + encodeURIComponent(sid) + '&off=' + off)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || d.detail) { say('\\n' + err(d, '会话丢了。')); show('会话丢了'); stop(); return; }
        if (d.truncated) say('\\n[……输出太快，中间一部分没跟上]\\n');
        say(d.text || '');
        off = d.off;
        if (!d.alive) {
          stop(); show('这一局结束了 —— 想看别的就再点上面');
          bar.style.display = 'none'; keys.style.display = 'none';
        }
      })
      .catch(function () {});
  }
  function send(v) {
    if (!sid) return;
    fetch(API + '/api/tank/send?sid=' + encodeURIComponent(sid) + '&line=' + encodeURIComponent(v),
          { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.detail) show(d.detail); })
      .catch(function () {});
    setTimeout(poll, 120);
  }
  document.getElementById('tplay').addEventListener('click', function () { start('play'); });
  document.getElementById('tauto').addEventListener('click', function () { start('auto'); });
  document.getElementById('tstop').addEventListener('click', function () {
    var old = sid;
    sid = null; stop();
    // sid 可能为空（刷新过页面）——把 client_id 也带上，服务器按身份关
    fetch(API + '/api/tank/close?sid=' + encodeURIComponent(old || '')
          + '&client_id=' + encodeURIComponent(cid), { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        show((d && d.closed) ? '已结束这一局 —— 可以再开新的了。' : '现在确实没有在跑的局。');
        bar.style.display = 'none'; keys.style.display = 'none';
      })
      .catch(function () { show('结束失败，稍后再试。'); });
  });
  document.getElementById('tsend').addEventListener('click', function () {
    var v = inp.value; inp.value = ''; send(v);
  });
  inp.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); var v = inp.value; inp.value = ''; send(v); }
  });
  document.querySelectorAll('.tkeyset').forEach(function (st) {
    st.style.cssText = 'display:inline-flex;flex-wrap:wrap;gap:.25rem;margin-right:.8rem';
  });
  document.querySelectorAll('.tkey').forEach(function (b) {
    b.style.cssText = 'padding:.25rem .55rem;border:1px solid var(--rule);'
                    + 'border-radius:5px;cursor:pointer;font:inherit;font-size:.9em';
    b.addEventListener('click', function () { send(b.getAttribute('data-v')); });
  });
  // 刷新/换标签后把上一局接回来：以前刷新就丢掉 sid，页面和服务器各说各话
  //（"你已有一局在跑" vs "没有在跑的局"）。现在开场先问服务器一句。
  (function resume() {
    fetch(API + '/api/tank/mine?client_id=' + encodeURIComponent(cid))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.sid) { show('没有在跑的局 —— 点上面按钮开一局。'); return; }
        sid = d.sid; off = 0;
        log.textContent = '（接回上一局，会话 ' + sid + '）\\n';
        show('已接回上一局（闲置 ' + (d.idle || 0) + ' 秒）');
        bar.style.display = ''; keys.style.display = '';
        poll();
        timer = setInterval(poll, 700);
      })
      .catch(function () {});
  })();
  // 不再用 beforeunload 关局：那会让"刷新"变成"弃局"（刷新后接不回来），
  // 闲置回收交给服务端（TANK_IDLE_S）。
})();
</script>
"""



def page_body(zh, api_base=""):
    """整块页面内容（说明 + 表单 + 按键 + 日志区 + JS）。"""
    return (u'<script>window.TANK_API = %s;</script>\n' % (u"'" + api_base + u"'")
            + section(zh) + JS)
