package org.xar.ck3.control.g2.m2.nativecode;

/** The actual2A328C9..2A328D0 pending-slot producer call edge only.
 * Other constructor/page/publication effects remain outside this adapter.
 */
public final class PendingSlotComponentCall2A328D0 {
    private PendingSlotComponentCall2A328D0() { }
    public static void initializeSelectedSlotComponent(PendingComponentInit2756120.Memory memory, long pendingObjectAddress, long moduleBase) {
        long componentAddress = pendingObjectAddress + 0x350L;
        PendingComponentInit2756120.initialize(memory, componentAddress, moduleBase);
    }
}
