package org.xar.ck3.control.build;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.win32.W32APIOptions;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Test-only named-pipe peers. Uses the production resource ABI; never a Native owner. */
public final class PreloadEndpointSoftwarePeer {
    private PreloadEndpointSoftwarePeer() { }
    private static final WindowsPreloadCustody.Api K = Native.load("kernel32",
            WindowsPreloadCustody.Api.class, W32APIOptions.UNICODE_OPTIONS);
    private static HANDLE valid(HANDLE handle) throws IOException {
        if (handle == null || WinBase.INVALID_HANDLE_VALUE.equals(handle))
            throw new IOException("software pipe acquire Win32=" + Native.getLastError());
        return handle;
    }
    private static void close(HANDLE handle) throws IOException {
        if (handle != null && !K.CloseHandle(handle))
            throw new IOException("software pipe close Win32=" + Native.getLastError());
    }
    private static HANDLE server(String name, boolean nonblocking) throws IOException {
        return valid(K.CreateNamedPipe(name, 3 | 0x80000, nonblocking ? 1 : 0, 1, 4096, 4096, 0, null));
    }
    private static void connected(HANDLE handle) throws IOException {
        long deadline = System.nanoTime() + 5_000_000_000L;
        while (!K.ConnectNamedPipe(handle, null)) {
            int error = Native.getLastError();
            if (error == 535) return;
            if (error != 536 || System.nanoTime() - deadline >= 0)
                throw new IOException("software pipe connect Win32=" + error);
            try { Thread.sleep(10); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("software connect interrupted", interrupted);
            }
        }
    }
    private static String locator(HANDLE handle) {
        return Long.toUnsignedString(Pointer.nativeValue(handle.getPointer()));
    }
    private record Params(String schema, String pipeName, String handleDecimal) { }
    private record Notice(String jsonrpc, String method, Params params) { }
    private static String notification(HANDLE handle, String name, String mode) throws IOException {
        var mapper = ControlBuild.strictMapper();
        ObjectNode root = mapper.valueToTree(new Notice("2.0", "notifications/xar/native-server-locator",
                new Params("xar.root-native-server-locator/v1", name, locator(handle))));
        if (!(root.get("params") instanceof ObjectNode params)) throw new IOException("software notice params object");
        switch (mode) {
            case "notice-good", "notice-delay" -> { }
            case "notice-bad-resource" -> params.put("handle_decimal", "1");
            case "notice-number" -> params.put("handle_decimal", 4);
            case "notice-bool" -> params.put("handle_decimal", true);
            case "notice-float" -> params.put("handle_decimal", 4.0);
            case "notice-zero" -> params.put("handle_decimal", "0");
            case "notice-leading-zero" -> params.put("handle_decimal", "04");
            case "notice-overflow" -> params.put("handle_decimal", "18446744073709551616");
            case "notice-extra" -> params.put("native", true);
            case "notice-missing" -> params.remove("handle_decimal");
            case "notice-schema" -> params.put("schema", "wrong");
            case "notice-wrong-pipe" -> params.put("pipe_name", name + "-wrong");
            case "notice-rpc-id" -> root.put("id", 1);
            case "notice-duplicate" -> { }
            default -> throw new IOException("unsupported fixed software notice mode");
        }
        String raw = mapper.writeValueAsString(root);
        return mode.equals("notice-duplicate") ? raw.replace("\"schema\":", "\"schema\":\"wrong\",\"schema\":") : raw;
    }
    public static void main(String[] args) throws Exception {
        if (args.length == 1 && args[0].equals("idle")) { Thread.sleep(1500); return; }
        if (args.length == 2 && (args[0].equals("client") || args[0].equals("client-locator"))) {
            HANDLE client = valid(K.CreateFile(args[1], 0xc0000000, 0, null, 3, 0, null));
            try {
                System.out.print("SOFTWARE_CLIENT_READY\n"); System.out.flush();
                Thread.sleep(args[0].equals("client-locator") ? 4000 : 10000);
            } finally { close(client); }
            return;
        }
        if (args.length != 3 || !(args[0].equals("server") || args[0].startsWith("notice-")))
            throw new IllegalArgumentException("fixed software peer modes required");
        HANDLE primary = null, auxiliary = null, client = null, waiting = null, waitingClient = null;
        try {
            primary = server(args[1], true); auxiliary = server(args[2], true);
            client = valid(K.CreateFile(args[2], 0xc0000000, 0, null, 3, 0, null));
            connected(auxiliary);
            waiting = server(args[2] + "-wait", false);
            waitingClient = valid(K.CreateFile(args[2] + "-wait", 0xc0000000, 0, null, 3, 0, null));
            connected(waiting);
            if (args[0].startsWith("notice-")) {
                if (args[0].equals("notice-delay")) Thread.sleep(2000);
                System.out.print(notification(primary, args[1], args[0]) + "\n");
                System.out.flush();
                if (args[0].equals("notice-delay")) {
                    System.err.print("SOFTWARE_NOTICE_EMITTED\n"); System.err.flush();
                }
                if (!args[0].equals("notice-good") && !args[0].equals("notice-bad-resource")) {
                    Thread.sleep(1500); return;
                }
            } else System.out.print(locator(primary) + " " + locator(auxiliary) + " " + locator(client)
                    + " " + locator(waiting) + "\n");
            System.out.flush();
            connected(primary);
            System.out.print("SOFTWARE_CONNECTED\n"); System.out.flush();
            var reader = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.US_ASCII));
            for (String line; (line = reader.readLine()) != null;) {
                if (line.equals("CLOSE_PRIMARY")) {
                    close(primary); primary = null;
                    System.out.print("SOFTWARE_CLOSED\n"); System.out.flush();
                } else if (line.equals("STOP")) return;
                else throw new IOException("unexpected software control line");
            }
        } finally {
            try { close(primary); } finally {
                try { close(client); } finally {
                    try { close(auxiliary); } finally {
                        try { close(waitingClient); } finally { close(waiting); }
                    }
                }
            }
        }
    }
}
