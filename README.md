# berlin1945-web

把《柏林1945：虎王车长》这类**「input() + print」式终端游戏**架到网页上的宿主层。

- 游戏本体：<https://github.com/RomanCohort/berlin-tank-commander>（**一个字都不改**）
- 线上试玩：<https://www.romancohort.cloud/tank/>

## 它怎么工作

游戏本来就是「读一行输入、打一堆文字」的形态，所以这里既不需要终端模拟器，也不需要 PTY：

```
浏览器 --POST /api/tank/send--> 子进程 stdin
       <--GET /api/tank/poll--- 子进程 stdout（增量，按字符偏移）
```

每一局：

1. 起一个子进程（`python game.py`），**cwd 与 HOME 都指向这一局自己的临时目录** —— 游戏写在 `~/<游戏名>/` 下的存档、事件记录、崩溃报告因此全落在临时目录里，会话结束就删
2. 一个读线程把 stdout 增量喂进环形缓冲（按**字符**切，不会切断多字节字符），网页按 offset 取增量
3. 网页送来的那一行写进它的 stdin

## 为什么敢公开

公开前把游戏源码过了一遍：

- 只 import 标准库，**不联网**（全文没有 socket / urllib / requests）
- **没有 eval / exec / __import__**
- 唯一的"后门"是游戏内调试菜单（开局菜单输入 `20070529` 改数值）—— 那是设计好的玩法，不是代码执行入口
- 实测常驻内存 ~52MB（玩起来后）、冷启动 ~0.4s

## 护栏（公开端点，缺一不可）

| 项 | 值 | 为什么 |
|---|---|---|
| 并发上限 | 4 | 每局 ~52MB；1 核 896MB 的机器要留余量 |
| 一个人一局 | 按 `client_id` | 按 IP 会把同一个校园网出口的人互相挡住（实测踩过） |
| 单出口上限 | 3 | 防一个人把名额占满 |
| 闲置回收 | 10 分钟 | 关页面不保证发得出请求 |
| 生命周期上限 | 1 小时 | 兜底 |
| 输入限速 | 0.25 秒/行 | 防脚本刷 |
| 输出缓冲 | 256KB/局 | 防内存涨 |
| 内存闸 | 可用 <150MB 拒新局 | 这台机器历史上被 OOM 打过 |
| 孤儿回收 | 开机 + 每 30 秒 | 服务重启后旧游戏进程会变孤儿（实测占了 45MB） |

另外子进程带 `PR_SET_PDEATHSIG`：服务一停，游戏进程跟着死。

## 快捷键是扫代码扫出来的

别猜玩家要按什么键 —— 去游戏源码里数：`choose(ins, "...", {"1": ...})` 的选项键和 `get_valid_input(ins, "...")` 的提示语。这部游戏实际用到的是：

**数字 0-9**（菜单；`0` 在多个菜单里表示"返回"）· **回车**（默认值）· **A**（自动存档）· **突围**（一个难度选项，是词不是键）· **q**（退出）· **r**（重开）

页面上因此有 17 个快捷键按钮（数字一排 + 动作一排），文本框留给名字和数值。换别的游戏时，把这一段重扫一遍即可。

## 刷新页面不会丢局

早期版本有个自相矛盾的 bug：`开始新游戏` 说"你已有一局在跑"，`结束这一局` 却说"没有在跑的局" —— 因为页面把 `sid` 存在自己手里，刷新就没了，而服务器那局还活着（按 `client_id` 判）。现在：

- 页面打开先问 `GET /api/tank/mine?client_id=`，有旧局就**接回来**（连输出一起）
- `POST /api/tank/close` 不带 `sid` 也能按身份关，并如实返回关掉了几局

## 跑起来

```bash
pip install -r requirements.txt
export TANK_GAME=/srv/tank-demo/game.py
export TANK_AUTOPLAY=/srv/tank-demo/autoplay.py
uvicorn tank_host.app:app --host 127.0.0.1 --port 8100

python web/standalone.py --api http://127.0.0.1:8100 > tank.html   # 生成页面
```

部署样例见 `deploy/`（nginx 反代 + systemd）。

环境变量：`TANK_GAME` / `TANK_AUTOPLAY` / `TANK_PYTHON` / `TANK_MAX_SESSIONS` / `TANK_MAX_PER_CLIENT` / `TANK_MAX_PER_IP` / `TANK_IDLE_S` / `TANK_IDLE_FREE_S` / `TANK_INPUT_GAP_S` / `TANK_BUF_CHARS` / `TANK_MIN_FREE_MB`。

## 换成别的游戏

只要满足「读 stdin 一行、往 stdout 打字」，就能直接换：

```bash
TANK_GAME=/srv/tank-demo/other_game.py TANK_AUTOPLAY= uvicorn tank_host.app:app
```

`TANK_AUTOPLAY` 留空则没有"旁观"按钮。用了 `curses` / `termios` / 清屏控制序列的游戏**不适用**（这套走的是管道，不是 tty）—— 那种游戏要上真终端（xterm.js + PTY）。

## 目录

```
tank_host/sessions.py   会话管理：子进程 / 增量缓冲 / 护栏 / 孤儿回收
tank_host/app.py        独立 FastAPI（/api/tank/*）
tank_host/ui.py         页面 HTML+JS（无框架依赖，站点版与独立版共用一份）
game/autoplay.py        旁观模式：用默认输入自己打完一局（0.4s，两三千行输出）
web/tank_page.py        接进站点生成器（thin）
web/standalone.py       生成自包含演示页
deploy/                 nginx / systemd 样例
```

## License

MIT