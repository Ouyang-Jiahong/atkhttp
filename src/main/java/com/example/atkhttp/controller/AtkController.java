package com.example.atkhttp.controller;

import com.atk.connector.tcp.AtkClientTools;
import com.atk.connector.tcp.CommandData;
import com.atk.connector.tcp.CmdResult;
import com.atk.connector.tcp.IClientCallBack;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * ATK 控制器，提供 HTTP 接口与 ATK 服务进行交互。
 * 包含 open、connect、close 三个操作。
 */
@RestController
@RequestMapping("/atk")
public class AtkController {

    private final AtkClientTools tools = AtkClientTools.getInstance(true);

    private volatile String currentHost;
    private volatile int currentPort;

    /** 用于暂存当前命令的回调事件 */
    private final java.util.concurrent.ConcurrentLinkedQueue<String> events = new java.util.concurrent.ConcurrentLinkedQueue<>();
    /** 用于阻塞等待一次命令的回调完成 */
    private volatile CountDownLatch pending;

    /**
     * 建立与 ATK 的连接
     */
    @PostMapping("/open")
    public String atkOpen(@RequestBody OpenRequest req) throws Exception {
        currentHost = req.host;
        currentPort = req.port;

        CountDownLatch connected = new CountDownLatch(1);

        IClientCallBack cb = new IClientCallBack() {
            @Override public void onError(Throwable e) {
                String msg = "[CB] onError: " + e;
                System.err.println(msg);
                events.add(msg);
                CountDownLatch p = pending;
                if (p != null) p.countDown();
            }
            @Override public void onConnected(String address, int port) {
                String msg = "[CB] onConnected: " + address + ":" + port;
                System.out.println(msg);
                events.add(msg);
                connected.countDown();
            }
            @Override public void onReceived(String address, int port, String type, String payload) {
                String msg = "[CB] onReceived: " + type + " | " + payload;
                System.out.println(msg);
                events.add(msg);
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
     * 发送命令到 ATK，并收集回调信息
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
     * 关闭与 ATK 的连接
     */
    @PostMapping("/close")
    public String atkClose() {
        tools.atkClose(currentHost, currentPort);
        return "closed";
    }

    private static String nz(String s) { return s == null ? "" : s; }

    // --- DTO ---
    public static class OpenRequest { public String host; public int port; }
    public static class ConnectRequest {
        public String command; public String objPath; public String cmdParam;
        public Long waitMs;
    }
    public static class EventsResponse {
        public java.util.List<String> events;
        public EventsResponse(java.util.List<String> events) { this.events = events; }
    }
}
