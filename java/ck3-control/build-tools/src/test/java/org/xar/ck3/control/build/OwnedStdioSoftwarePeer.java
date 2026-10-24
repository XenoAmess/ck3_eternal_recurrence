package org.xar.ck3.control.build;

import java.nio.charset.StandardCharsets;

/** Software Java child only; does not expose MCP, Native or CK3 adapters. */
public final class OwnedStdioSoftwarePeer {
    private OwnedStdioSoftwarePeer() { }
    public static void main(String[] args) throws Exception {
        System.err.print("SOFTWARE_STDERR\n"); System.err.flush();
        switch (args[0]) {
            case "echo" -> { System.in.transferTo(System.out); System.out.flush(); }
            case "split" -> {
                byte[] raw = "first\n\u6c49\u5b57-9007199254740993\nthird\n".getBytes(StandardCharsets.UTF_8);
                for (byte value : raw) { System.out.write(value); System.out.flush(); Thread.sleep(2); }
                System.in.read();
            }
            case "partial" -> { System.out.write("unfinished".getBytes(StandardCharsets.UTF_8)); System.out.flush(); }
            case "exit7" -> System.exit(7);
            case "silent", "no-read" -> Thread.sleep(60_000);
            default -> throw new IllegalArgumentException("Unknown software peer mode");
        }
    }
}
