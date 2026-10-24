package org.xar.ck3.control.build;

import com.sun.jna.platform.win32.Kernel32;

/** Real Windows exit-code software fixture; it creates no Native or Game authority. */
public final class Exit259SoftwarePeer {
    private Exit259SoftwarePeer() { }

    public static void main(String[] arguments) {
        if (arguments.length != 0) throw new IllegalArgumentException("No operands accepted");
        System.out.print("SOFTWARE_EXIT259\n");
        System.out.flush();
        Kernel32.INSTANCE.ExitProcess(259);
        throw new AssertionError("ExitProcess returned");
    }
}
