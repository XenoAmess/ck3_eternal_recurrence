package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Frozen observation API for held 914B3763730; no process or native execution. */
public final class RegistryConsumerApi176 {
    private RegistryConsumerApi176() { }

    public interface Memory extends NativeTaskMemory {
        /** One exact unsigned byte, represented as 0..255. */
        int readUnsigned8(long address);
        /** Writes the low eight bits at one supplied address. */
        void write8(long address, int value);
    }

    /** Caller owns all scratch storage and its initial contents; this record allocates nothing. */
    public record Scratch(long sourceRsp) {
        public long sourceRbp() { return sourceRsp + 0x100L; }
    }

    /**
     * Every port may mutate Memory or throw; no call is assumed side-effect-free.
     * Code arguments are the actual pointer bits read for that indirect call.
     * Al methods return observed bits; only their low byte is consumed.
     * sourceRsp parameters expose actual caller stack storage, not invented native arguments.
     */
    public interface Ports {
        void call9ce3f0(Memory memory, long vectorHeader);
        void callca6190(Memory memory, long vectorHeader, int requestedCount);
        int handlerAl(Memory memory, long code, long keyAndVector);
        /** RCX=descriptor; source stack+20 contains the explicit fifth argument. */
        void call3f7aa40(Memory memory, long descriptor, long sourceRsp);
        void allocatorSlot10(Memory memory, long code, long allocator, long block, int alignment);
        long objectSlot08(Memory memory, long code, long receiver);
        int objectSlotA8Al(Memory memory, long code, long receiver);
        void objectSlot00(Memory memory, long code, long receiver, int flag);
        long objectSlot30(Memory memory, long code, long receiver, long output);
        int incomingSlot48Al(Memory memory, long code, long receiver);
        long call3768260(Memory memory);
        long call3f8a6d0(Memory memory, long context, int key);
        long call3f4f8e0(Memory memory, int key);
        void call3795e30(Memory memory, long copied16, int modeByte, long descriptor);
        long call3f95fd0(Memory memory, long field, long output);
        /** Source3982 establishes no new explicit RCX operand; no receiver is invented. */
        long call864a20(Memory memory);
        void call857a70(Memory memory, long output, long format, long operands);
        /** Returns the actual supplied GS:[58h] observation; normal pointer reads follow it. */
        long gs58(Memory memory);
        long call3f5f970(Memory memory, int flag);
        /** Stack+28 is explicitly written; stack+20 retains supplied/earlier source content. */
        void call857b60(Memory memory, long logger, long descriptor, int line, int level, long sourceRsp);
        /** Single atomic DWORD operation; returns old bits, which this source does not consume. */
        int atomicXadd32(Memory memory, long address, int delta);
        void call4223f44(Memory memory, long base, long bytes);
        void call4232a70(Memory memory);
    }

    public enum Completion {
        RETURNED,
        /** Source would execute INT3 after an unexpectedly returning error call; not run here. */
        UNSUPPORTED_INT3_AFTER_ERROR_CALL_RETURNED
    }
}
