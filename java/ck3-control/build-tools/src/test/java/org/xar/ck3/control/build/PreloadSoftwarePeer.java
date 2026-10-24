package org.xar.ck3.control.build;
/** Ordinary Java natural-loader child only. */
public final class PreloadSoftwarePeer {
    private PreloadSoftwarePeer() { }
    public static void main(String[] args) throws Exception {
        System.out.print("SOFTWARE_READY\n"); System.out.flush(); Thread.sleep(1800);
    }
}
