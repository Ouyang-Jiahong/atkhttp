package com.example.atkhttp.controller;

import com.atk.connector.tcp.AtkClientTools;
import com.atk.connector.tcp.CommandData;
import com.atk.connector.tcp.CmdResult;
import com.atk.connector.tcp.IClientCallBack;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * ATK 控制器
 *
 * 提供基于 HTTP 的 REST 接口，用于与 ATK 服务建立连接、发送命令和关闭连接。
 * 支持以下操作：
 * - /open：建立与指定 ATK 服务的 TCP 连接
 * - /connect：发送控制命令并等待响应结果
 * - /close：关闭当前连接
 *
 * 本控制器通过 AtkClientTools 与底层 TCP 客户端交互，并使用回调机制收集通信过程中的事件信息。
 */
@RestController
@RequestMapping("/atk")
public class AtkController {

    private final AtkClientTools tools = AtkClientTools.getInstance(true);

    private volatile String currentHost;
    private volatile int currentPort;

    /**
     * 存储回调过程中产生的事件日志（如连接状态、接收数据等）
     * 使用线程安全的队列以支持异步回调写入
     */
    private final java.util.concurrent.ConcurrentLinkedQueue<String> events = new java.util.concurrent.ConcurrentLinkedQueue<>();

    /**
     * 用于同步等待单次命令执行完成的信号量
     * 在发送命令后阻塞线程，直到收到响应或超时
     */
    private volatile CountDownLatch pending;

    /**
     * 建立与 ATK 服务的连接
     *
     * 接收主机地址和端口，初始化连接并注册回调处理器。
     * 等待最多 5 秒以确认连接成功，超时则抛出异常。
     *
     * @param req 包含目标主机（host）和端口（port）的请求体
     * @return 若连接成功，返回 "connected"
     * @throws Exception 若连接超时或初始化失败
     */
    @PostMapping("/open")
    public String atkOpen(@RequestBody OpenRequest req) throws Exception {
        currentHost = req.host;
        currentPort = req.port;

        CountDownLatch connected = new CountDownLatch(1);

        IClientCallBack cb = new IClientCallBack() {
            @Override public void onError(Throwable e) {
                String msg = "程序出现错误: " + e;
                System.err.println(msg);
                events.add(msg);
                CountDownLatch p = pending;
                if (p != null) p.countDown();
            }
            @Override public void onConnected(String address, int port) {
                String msg = "已连接上 ATK客户端: " + address + ":" + port;
                System.out.println(msg);
                events.add(msg);
                connected.countDown();
            }
            @Override public void onReceived(String address, int port, String type, String payload) {
                System.out.println(type);
                events.add(type);
                AtkClientTools.commandFlag = true;
            }
            @Override public void onReceivedEx(String address, int port, CmdResult result, int code, String gStrCommand) {
                String header = "[CB] onReceivedEx: code=" + code + " cmd=" + gStrCommand;
                System.out.println(header);
                events.add(header);
                if (result != null && result.getmVectData() != null) {
                    for (String s : result.getmVectData()) {
                        System.out.println(s);
                        events.add(s);
                    }
                }
                CountDownLatch p = pending;
                if (p != null) p.countDown();
                AtkClientTools.commandFlag = true;
            }
            @Override public void onSent(String address, int port, byte[] data) {
                String msg = "[CB] onSent: " + data.length + " bytes";
                System.out.println(msg);
                events.add(msg);
            }
        };

        tools.atkOpen(currentHost, currentPort, cb);

        if (!connected.await(5000, TimeUnit.MILLISECONDS)) {
            throw new IllegalStateException("连接 ATK 超时（5s）");
        }
        return "connected";
    }

    /**
     * 向已连接的 ATK 服务发送命令
     *
     * 清空之前的事件记录，发送指定命令，并等待响应完成或超时。
     * 默认等待时间为 3000 毫秒，可通过请求参数自定义。
     *
     * @param req 包含命令内容、对象路径、参数及可选等待时间的请求体
     * @return 包含本次操作期间所有回调事件的日志列表
     * @throws InterruptedException 若等待过程中被中断
     */
    @PostMapping("/connect")
    public EventsResponse atkConnect(@RequestBody ConnectRequest req) throws InterruptedException {
        events.clear();
        pending = new CountDownLatch(1);

        CommandData data = new CommandData();
        data.setStrCommand(nz(req.command));
        data.setStrObjPath(nz(req.objPath));
        data.setStrCMDParam(nz(req.cmdParam));

        tools.atkExecuteCommand(currentHost, currentPort, data, false);

        long waitMs = (req.waitMs != null && req.waitMs > 0) ? req.waitMs : 3000L;
        pending.await(waitMs, TimeUnit.MILLISECONDS);
        pending = null;

        return new EventsResponse(new java.util.ArrayList<>(events));
    }

    /**
     * 关闭与 ATK 服务的连接
     *
     * 调用底层工具类关闭当前维护的连接（基于 currentHost 和 currentPort）。
     *
     * @return 操作完成后返回 "closed"
     */
    @PostMapping("/close")
    public String atkClose() {
        tools.atkClose(currentHost, currentPort);
        return "closed";
    }

    /**
     * 安全地将字符串值转为非 null 字符串（null 时返回空串）
     *
     * @param s 输入字符串
     * @return 非 null 字符串
     */
    private static String nz(String s) { return s == null ? "" : s; }

    // --- 数据传输对象（DTO）定义 ---

    /**
     * 打开连接请求的数据结构
     */
    public static class OpenRequest {
        public String host;   // 目标主机地址
        public int port;      // 目标端口号
    }

    /**
     * 发送命令请求的数据结构
     */
    public static class ConnectRequest {
        public String command;   // 要执行的命令名称
        public String objPath;   // 目标对象路径
        public String cmdParam;  // 命令参数
        public Long waitMs;      // 等待响应的最长时间（毫秒），可选
    }

    /**
     * 命令执行结果的响应结构
     * 返回回调过程中收集的所有事件日志
     */
    public static class EventsResponse {
        public java.util.List<String> events;  // 回调事件日志列表

        public EventsResponse(java.util.List<String> events) {
            this.events = events;
        }
    }
}