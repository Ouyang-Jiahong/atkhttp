# atk_runner_single.py
import time
from typing import List, Dict, Any, Tuple
import requests

def run_atk_commands(
        commands: List[Dict[str, str]],
        base_url: str = "http://localhost:8080",
        host: str = "127.0.0.1",
        port: int = 6655,
        delay_sec: float = 0.1,
        timeout_open_close: float = 5.0,
        timeout_connect: float = 10.0,
) -> Dict[str, Any]:
    """
    运行一组 ATK 命令（通过 Java HTTP 桥）。
    - /atk/open → 逐条 /atk/connect（默认间隔 delay_sec 秒）→ /atk/close
    - 自动判错：出现 onError / NACK / onReceivedEx: code!=0 记为失败，但不中断后续命令
    - 自动等待策略：
        * New 命令：waitMs=60
        * 其他命令：waitMs=200
      （如确实需要自定义等待，可在某条命令里显式加 "waitMs": 数值 覆盖）
    仅需提供每条命令的 "command" 与 "objPath"（可选 "cmdParam"）。
    """
    base = base_url.rstrip("/")

    def _post(path: str, payload: Dict[str, Any], timeout: float) -> requests.Response:
        r = requests.post(f"{base}{path}", json=payload, timeout=timeout)
        r.raise_for_status()
        return r

    def _detect_ok(events: List[str]) -> Tuple[bool, str]:
        # 启发式判错：onError / NACK / onReceivedEx code!=0
        for line in events:
            if "onError" in line:
                return False, "onError in callback"
            if "NACK" in line:
                return False, "NACK received"
        for line in events:
            if "onReceivedEx" in line and "code=" in line:
                try:
                    seg = line.split("code=", 1)[1]
                    num_str = seg.split(None, 1)[0].strip().rstrip(":,;")
                    code = int(num_str)
                    if code != 0:
                        return False, f"onReceivedEx code={code}"
                except Exception:
                    pass
        return True, ""

    def _is_new(cmd_name: str) -> bool:
        return (cmd_name or "").strip().lower() == "new"

    results: List[Dict[str, Any]] = []
    overall_ok = True

    # /atk/open
    try:
        _post("/atk/open", {"host": host, "port": port}, timeout_open_close)
    except Exception as e:
        return {"ok": False, "results": [{
            "index": 0, "command": "OPEN", "objPath": "", "cmdParam": "",
            "ok": False, "reason": f"open_failed: {e}", "events": []
        }]}

    try:
        for idx, cmd in enumerate(commands, start=1):
            command  = (cmd.get("command")  or "")
            objPath  = (cmd.get("objPath")  or "")
            cmdParam = (cmd.get("cmdParam") or "")

            # 自动等待策略（可被该条命令的 "waitMs" 覆盖）
            default_wait_ms = 60 if _is_new(command) else 200
            wait_ms = int(cmd.get("waitMs", default_wait_ms))

            try:
                payload = {
                    "command":  command,
                    "objPath":  objPath,
                    "cmdParam": cmdParam,
                    "waitMs":   wait_ms,  # 仅传这一个等待参数，其他一律省略
                }
                r = _post("/atk/connect", payload, timeout_connect)
                data = r.json() if r.content else {}
                events = data.get("events", []) if isinstance(data, dict) else []
                ok, reason = _detect_ok(events)
            except Exception as e:
                ok, reason, events = False, f"http_error: {e}", []

            results.append({
                "index": idx,
                "command": command,
                "objPath": objPath,
                "cmdParam": cmdParam,
                "ok": ok,
                "reason": reason,
                "events": events,
                "waitMs": wait_ms,
            })

            if not ok:
                overall_ok = False

            time.sleep(max(0.0, float(delay_sec)))
    finally:
        try:
            _post("/atk/close", {}, timeout_open_close)
        except Exception:
            pass

    return {"ok": overall_ok, "results": results}


# --- 使用示例（可删） ---
if __name__ == "__main__":
    cmds = [
        {"command": "New", "objPath": "/ Scenario SimpleScenario"},
        {"command": "SetAnalysisTimePeriod", "objPath": "* \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\""},
        {"command": "Animate", "objPath": "* Reset"},

        {"command": "New", "objPath": "/ Facility GroundStation1"},
        {"command": "SetPosition", "objPath": "*/Facility/GroundStation1 Geodetic 39.9 116.4 50.0"},

        {"command": "New", "objPath": "/ Satellite Sat1"},
        {"command": "SetState",
         "objPath": "*/Satellite/Sat1 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 6878136.999999994412065 0.0 44.997423212349375 359.818801881724369 0 359.80316033301915"},

        {"command": "New", "objPath": "/ Satellite Sat2"},
        {"command": "SetState",
         "objPath": "*/Satellite/Sat2 Classical TwoBody NoProp 60.0 J2000 \"2025-01-01 00:00:00.000\" 6853454.382262638770044 0.0 98.137200680920444 100.582578708373092 0 0.023861912010873"},

        {"command": "New", "objPath": "/ Facility/GroundStation1/Sensor GroundSensor1"},
        {"command": "Define", "objPath": "*/Facility/GroundStation1/Sensor/GroundSensor1 SimpleCone 30"},
        {"command": "Point", "objPath": "*/Facility/GroundStation1/Sensor/GroundSensor1 Fixed Quaternion 0 0 0 -1"},

        {"command": "Access",
         "objPath": "*/Satellite/Sat2 */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\""},
        {"command": "Report_RM",
         "objPath": "*/Satellite/Sat2 Style \"Access\" Type Export File \"D:\\\\Codes\\\\atk-java-demo\\\\report\\\\Access.txt\" AccessObject */Satellite/Sat1 TimePeriod \"1 Jan 2025 00:00:00.00\" \"5 Jan 2025 00:00:00.00\" TimeStep 60"},
    ]

    result = run_atk_commands(
        commands=cmds,
        base_url="http://localhost:8080",
        host="127.0.0.1",
        port=6655,
        delay_sec=0.01,
    )

    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
