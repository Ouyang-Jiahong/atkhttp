package com.example.atkhttp.controller;

import com.atk.connector.tcp.AtkClientTools;
import com.atk.connector.tcp.CommandData;
import com.atk.connector.tcp.CmdResult;
import com.atk.connector.tcp.IClientCallBack;
import org.springframework.web.bind.annotation.*;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/atk")
public class AtkController {

    // 打开 debug，便于看底层日志（需要可改成 false）
    private final AtkClientTools tools = AtkClientTools.getInstance(true);

    // 记录当前连接
    private volatile String currentHost;
    private volatile int currentPort;

    @PostMapping("/open")
    public String atkOpen(@RequestBody OpenRequest req) throws Exception {
        currentHost = req.host;
        currentPort = req.port;

        CountDownLatch connected = new CountDownLatch(1);

        IClientCallBack cb = new IClientCallBack() {
            @Override public void onError(Throwable e) {
                System.err.println("[CB] onError: " + e);
            }
            @Override public void onConnected(String address, int port) {
                System.out.println("[CB] onConnected: " + address + ":" + port);
                connected.countDown();
            }
            @Override public void onReceived(String address, int port, String type, String payload) {
                System.out.println("[CB] onReceived: " + type + " | " + payload);
            }
            @Override public void onReceivedEx(String address, int port, CmdResult result, int code, String gStrCommand) {
                System.out.println("[CB] onReceivedEx: code=" + code + " cmd=" + gStrCommand);
                if (result != null && result.getmVectData() != null) {
                    for (String s : result.getmVectData()) System.out.println(s);
                }
            }
            @Override public void onSent(String address, int port, byte[] data) {
                System.out.println("[CB] onSent: " + data.length + " bytes");
            }
        };

        tools.atkOpen(currentHost, currentPort, cb);

        if (!connected.await(5000, TimeUnit.MILLISECONDS)) {
            throw new IllegalStateException("连接 ATK 超时（5s）");
        }
        return "connected";
    }

    @PostMapping("/connect")
    public String atkConnect(@RequestBody ConnectRequest req) {
        CommandData data = new CommandData();
        data.setStrCommand(nz(req.command));
        data.setStrObjPath(nz(req.objPath));
        data.setStrCMDParam(nz(req.cmdParam));
        tools.atkConnect(currentHost, currentPort, data, false);
        return "sent";
    }

    @PostMapping("/close")
    public String atkClose() {
        tools.atkClose(currentHost, currentPort);
        return "closed";
    }

    private static String nz(String s) { return s == null ? "" : s; }

    // --- DTO ---
    public static class OpenRequest { public String host; public int port; }
    public static class ConnectRequest { public String command; public String objPath; public String cmdParam; }
}
