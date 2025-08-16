# atk_runner_single.py
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

def open_atk(base_url: str, host: str, port: int, timeout: float = 5.0) -> None:
    """建立与 ATK 的连接。"""
    _post(base_url, "/atk/open", {"host": host, "port": port}, timeout)

def close_atk(base_url: str, timeout: float = 5.0) -> None:
    """关闭与 ATK 的连接。"""
    _post(base_url, "/atk/close", {}, timeout)

def send_atk_command(
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

def run_atk_commands(
        commands: List[Dict[str, str]],
        base_url: str = "http://localhost:8080",
        host: str = "127.0.0.1",
        port: int = 6655,
        delay_sec: float = 0.1,        # 你标注的稳定间隔
        timeout_open_close: float = 5.0,
        timeout_connect: float = 10.0,
) -> Dict[str, Any]:
    """
    批量执行命令：/atk/open → 逐条 /atk/connect（统一 waitMs=200ms，命令间隔 delay_sec）→ /atk/close
    返回每条命令的执行结果，不因失败中断。
    """
    results: List[Dict[str, Any]] = []
    overall_ok = True

    # 打开连接
    try:
        open_atk(base_url, host, port, timeout_open_close)
    except Exception as e:
        return {"ok": False, "results": [{
            "index": 0, "command": "OPEN", "objPath": "", "cmdParam": "",
            "ok": False, "reason": f"open_failed: {e}", "events": []
        }]}

    try:
        for idx, cmd in enumerate(commands, start=1):
            res = send_atk_command(
                base_url=base_url,
                command=(cmd.get("command") or ""),
                objPath=(cmd.get("objPath") or ""),
                cmdParam=(cmd.get("cmdParam") or ""),
                wait_ms=200,                         # 统一等待
                timeout_connect=timeout_connect,
            )
            res["index"] = idx
            results.append(res)
            if not res["ok"]:
                overall_ok = False
            time.sleep(max(0.0, float(delay_sec)))
    finally:
        # 按你之前习惯：提示并延迟 5s 再关闭（可按需删掉这两行）
        print("命令已执行完成，还有五秒断开连接！")
        time.sleep(5)
        try:
            close_atk(base_url, timeout_open_close)
        except Exception:
            pass

    return {"ok": overall_ok, "results": results}

# ============== 使用示例（可删） ==============
if __name__ == "__main__":
    base = "http://localhost:8080"
    # 手动发送（你有“手动空间”）：
    open_atk(base, "127.0.0.1", 6655)
    print(send_atk_command(base, "New", "/ Scenario SimpleScenario"))
    print(send_atk_command(base, "SetAnalysisTimePeriod", "* \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\""))
    print(send_atk_command(base, "Animate", "* Reset"))
    close_atk(base)

    # 或：批量发送
    cmds = [
        {"command": "New", "objPath": "/ Facility GroundStation1"},
        {"command": "SetPosition", "objPath": "*/Facility/GroundStation1 Geodetic 39.9 116.4 50.0"},
    ]
    print(run_atk_commands(cmds, base_url=base, host="127.0.0.1", port=6655, delay_sec=0.1))
