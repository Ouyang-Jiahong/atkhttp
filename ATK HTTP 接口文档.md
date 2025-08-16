# ATK HTTP 接口文档

## 基本信息

* **服务地址**：`http://<server>:8080/atk`
* **数据格式**：请求和响应均为 `application/json`
* **接口列表**：

    * [POST /atk/open](#post-atkopen)
    * [POST /atk/connect](#post-atkconnect)
    * [POST /atk/close](#post-atkclose)

---

## POST /atk/open

建立与 ATK 服务的连接。

### 请求参数

```json
{
  "host": "127.0.0.1",   // ATK 服务 IP
  "port": 6655           // ATK 服务端口
}
```

### 响应示例

```json
"connected"
```

### 说明

* 成功时返回 `"connected"`。
* 若 5 秒内未能建立连接，会抛出异常。

---

## POST /atk/connect

向 ATK 发送一条命令，并返回回调信息。

### 请求参数

```json
{
  "command": "New",          // 命令关键字
  "objPath": "/ Satellite S1", // 命令作用对象路径
  "cmdParam": "",            // 命令参数，可选
  "waitMs": 500              // （可选）等待回调的最大时间，默认 3000 毫秒
}
```

### 响应参数

```json
{
  "events": [
    "[CB] onSent: 25 bytes",
    "[CB] onReceivedEx: code=0 cmd=New",
    "Satellite created successfully"
  ]
}
```

### 说明

* `events` 为本次命令执行期间收到的回调信息，按时间顺序排列。
* 默认最多等待 3000ms，若设置 `waitMs`，则按指定时间等待。
* 即使命令失败（如返回 `NACK`），仍会返回所有回调信息。

---

## POST /atk/close

关闭当前与 ATK 的连接。

### 请求参数

```json
{}
```

### 响应示例

```json
"closed"
```

### 说明

* 成功关闭连接时返回 `"closed"`。

---

## 使用示例（Python）

```python
import requests

base = "http://localhost:8080/atk"

# 1. 打开连接
requests.post(f"{base}/open", json={"host":"127.0.0.1","port":6655})

# 2. 发送命令
resp = requests.post(f"{base}/connect",
    json={"command":"New","objPath":"/ Scenario Demo","cmdParam":"","waitMs":500})
print(resp.json())

# 3. 关闭连接
requests.post(f"{base}/close")
