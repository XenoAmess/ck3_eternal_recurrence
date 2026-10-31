package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Known caller projection only, not a live/native callee ABI or success result. */
public final class Idler28eed20 {
    private Idler28eed20() { }

    public enum FrameAddress {
        LOCAL_OUT_30,
        SAVED_ORIGINAL_R8D_60,
        SAVED_ORIGINAL_EDX_58
    }

    /** Symbolic frame addresses have no numeric/live address or contents beyond explicit saved DWORDs. Unknown stack20 omitted. */
    public record Known177ed10(long rcx, FrameAddress rdx, int r8d, FrameAddress r9,
                               FrameAddress stack28, int savedEdx58, int savedR8d60) { }

    @FunctionalInterface
    public interface Port {
        long call177ed10(Known177ed10 known);
    }

    /** The four original DWORD bytes feed source32-bit FNV in little-endian order. */
    public static Known177ed10 prepare(long entryRcx, int entryEdx, int entryR8d) {
        int hash = 0x811C9DC5;
        for (int shift = 0; shift < 32; shift += 8) {
            hash = (hash ^ ((entryR8d >>> shift) & 0xFF)) * 0x01000193;
        }
        return new Known177ed10(entryRcx + 0x18L, FrameAddress.LOCAL_OUT_30, hash,
                FrameAddress.SAVED_ORIGINAL_R8D_60, FrameAddress.SAVED_ORIGINAL_EDX_58,
                entryEdx, entryR8d);
    }

    public static long invoke(long entryRcx, int entryEdx, int entryR8d, Port port) {
        Known177ed10 known = prepare(entryRcx, entryEdx, entryR8d);
        return port.call177ed10(known);
    }
}
