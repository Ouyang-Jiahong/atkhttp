import time
from typing import List, Dict, Any, Tuple
import requests

# ============== 基础工具（统一 200ms 等待） ==============

def _post(base_url: str, path: str, payload: Dict[str, Any], timeout: float) -> requests.Response:
    r = requests.post(f"{base_url.rstrip('/')}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r

def _detect_ok(events: List[str]) -> Tuple[bool, str]:
    # 简单启发式：出现 onError/NACK 或 onReceivedEx code!=0 视为失败
    for line in events:
        if "onError" in line:
            return False, "onError in callback"
        if "NACK" in line:
            return False, "NACK received"
    for line in events:
        if "onReceivedEx" in line and "code=" in line:
            try:
                num = int(line.split("code=", 1)[1].split(None, 1)[0].strip().rstrip(":,;"))
                if num != 0:
                    return False, f"onReceivedEx code={num}"
            except Exception:
                pass
    return True, ""

# ============== 对外函数（更少参数、更易用） ==============

def atkOpen(base_url: str, host: str, port: int, timeout: float = 5.0) -> None:
    """建立与 ATK 的连接。"""
    _post(base_url, "/atk/open", {"host": host, "port": port}, timeout)

def atkClose(base_url: str, timeout: float = 5.0) -> None:
    """关闭与 ATK 的连接。"""
    _post(base_url, "/atk/close", {}, timeout)

def atkConnect(
        base_url: str,
        command: str,
        objPath: str,
        cmdParam: str = "",
        wait_ms: int = 200,
        timeout_connect: float = 10.0,
) -> Dict[str, Any]:
    """
    发送单条命令（统一 waitMs=200ms），返回执行结果。
    你可手动按你的节奏一条条调用这个函数。
    """
    payload = {
        "command": command or "",
        "objPath": objPath or "",
        "cmdParam": cmdParam or "",
        "waitMs": int(wait_ms),     # 统一 200ms 等待
    }
    try:
        r = _post(base_url, "/atk/connect", payload, timeout_connect)
        data = r.json() if r.content else {}
        events = data.get("events", []) if isinstance(data, dict) else []
        ok, reason = _detect_ok(events)
    except Exception as e:
        ok, reason, events = False, f"http_error: {e}", []
    return {
        "command": command, "objPath": objPath, "cmdParam": cmdParam,
        "ok": ok, "reason": reason, "events": events, "waitMs": int(wait_ms),
    }