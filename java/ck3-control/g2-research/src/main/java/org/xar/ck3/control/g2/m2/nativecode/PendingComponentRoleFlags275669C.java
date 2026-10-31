package org.xar.ck3.control.g2.m2.nativecode;

/** Exact role-flag block 275669C..27566F5 of the held 1473-byte body.
 * The intervening calls after role resolution are not implemented here.
 */
public final class PendingComponentRoleFlags275669C {
    private PendingComponentRoleFlags275669C() { }
    public interface Memory {
        int read8(long address);
        int read32(long address);
        long read64(long address);
        void write8(long address, int value);
    }
    public interface Calls {
        boolean call2BAA6F0(Memory memory, int ecx);
    }
    public static void apply(Memory memory, Calls calls, long componentAddress,
            long contextAddress, PendingComponentRoles27563E1.Resolved roles) {
        long contextOwner = memory.read64(contextAddress);
        boolean first;
        if (memory.read8(contextOwner + 0x2728L) != 0) {
            first = true;
        } else if (memory.read32(roles.rdi() + 0x1CL) != 0x43686172) {
            first = false;
        } else {
            int id = memory.read32(roles.rdi() + 0x18L);
            first = id != -1 && memory.read64(roles.rdi() + 0x1D0L) == 0
                    && calls.call2BAA6F0(memory, id);
        }
        memory.write8(componentAddress + 0x25CL, first ? 1 : 0);
        boolean second = memory.read32(roles.r15() + 0x1CL) == 0x43686172
                && memory.read32(roles.r15() + 0x18L) != -1;
        memory.write8(componentAddress + 0x264L, second ? 1 : 0);
    }
}
