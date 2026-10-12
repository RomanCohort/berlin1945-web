"""《柏林1945：虎王车长》的网页宿主层。

把一个「input() + print」式的终端游戏架到网页上：每局一个子进程，
cwd 与 HOME 指向各自的临时目录，stdout 增量喂给浏览器，浏览器的输入写进
它的 stdin。**游戏本体一个字都不用改**（见 README）。

    sessions.py  会话管理（子进程 / 缓冲 / 护栏）
    app.py       独立 FastAPI（/api/tank/*）
    ui.py        页面 HTML+JS（无框架依赖，站点版与独立版共用）
"""

__version__ = "1.0.0"
