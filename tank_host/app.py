#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立部署用的 FastAPI —— 把会话管理挂成 /api/tank/*。

线上站点是把它并进了 character_chat 那个服务（同一个 uvicorn），
这个文件让它可以单独跑：

    pip install fastapi uvicorn
    TANK_GAME=/srv/tank-demo/game.py uvicorn tank_host.app:app --host 127.0.0.1 --port 8100

页面：把 web/standalone.py 生成的 html 丢给 nginx（或任何静态服务器），
并把 /api/tank/ 反代到这里。注意 nginx 要给 /api/tank/poll 留够超时。
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request

from . import sessions as T

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tank_host.app")

app = FastAPI(title="Berlin 1945 web host", version="1.0.0",
              description="把终端游戏挂到网页上的宿主层（子进程 + 管道桥）。")


def _client_key(request: Request, client_id: str = "") -> str:
    """限流按谁算：优先真实 IP，回环（本机直连 / 隧道转发）时退回访客 id。

    为什么要有这一步：回环场景下所有人都是 127.0.0.1，按 IP 卡会让一个人
    把别人全挡在门外（线上实测踩过）。
    """
    ip = (request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for")
          or (request.client.host if request.client else "") or "")
    ip = ip.split(",")[0].strip()[:64]
    if not ip or ip in ("127.0.0.1", "::1", "localhost"):
        return "c:" + ((client_id or "anon").strip()[:64] or "anon")
    return ip


@app.get("/")
def index():
    return {"name": "berlin1945-web", "version": app.version,
            "endpoints": ["/api/tank/new", "/api/tank/poll", "/api/tank/send",
                          "/api/tank/close", "/api/tank/mine", "/api/tank/stats"]}


@app.post("/api/tank/new")
def tank_new(request: Request, mode: str = "play", client_id: str = ""):
    """开一局。mode=play 真人玩 / mode=auto 看它自己打（不接受输入）。"""
    try:
        return T.create(mode, _client_key(request, client_id), client_id)
    except T.TankError as e:
        raise HTTPException(status_code=e.code, detail=str(e))
    except Exception as e:
        logger.warning("tank_new 失败: %r" % (e,))
        raise HTTPException(status_code=503, detail="现在开不了新局。")


@app.get("/api/tank/poll")
def tank_poll(sid: str = "", off: int = 0):
    """增量取输出。off 是上一次返回的字符偏移。"""
    try:
        return T.poll(sid, off)
    except T.TankError as e:
        raise HTTPException(status_code=e.code, detail=str(e))


@app.post("/api/tank/send")
def tank_send(sid: str = "", line: str = ""):
    """把玩家输入的那一行送去游戏进程的 stdin。"""
    try:
        return T.send(sid, line)
    except T.TankError as e:
        raise HTTPException(status_code=e.code, detail=str(e))


@app.get("/api/tank/mine")
def tank_mine(client_id: str = ""):
    """这个浏览器还有没有在跑的局（刷新页面后据此把旧局接回来）。"""
    return T.mine(client_id)


@app.post("/api/tank/close")
def tank_close(sid: str = "", client_id: str = ""):
    """结束这一局。sid 为空时按 client_id 关（刷新后页面手里没有 sid）。"""
    if not (sid or "").strip() and (client_id or "").strip():
        return T.close_client(client_id)
    return T.close(sid)


@app.get("/api/tank/stats")
def tank_stats():
    """还开着几局、内存够不够。"""
    return T.stats()
