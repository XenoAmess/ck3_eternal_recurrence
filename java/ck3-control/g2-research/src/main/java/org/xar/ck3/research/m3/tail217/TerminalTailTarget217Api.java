package org.xar.ck3.research.m3.tail217;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;

/** Supplied-storage business contract of 188B at 42421C8; no full CPU ABI. */
public interface TerminalTailTarget217Api {
    interface Memory extends Terminal207Api.Memory {
        int readUnsigned16(long address);
        void write8(long address, int value);
    }

    /** Actual entry RSP, supplied by its owner; all local addresses derive from it. */
    record Scratch(long entryRsp) { }

    /** ECX/EDX/R8D preserve the received low 32-bit patterns. */
    record Input(long moduleBase, int ecx, int edx, int r8d, Scratch scratch) { }

    interface Ports {
        long call43da620(Memory memory, long siteRva, long actualTarget, int ecx);
        void call42422d0(Memory memory, long siteRva, int ecx);
        long call42420c0(Memory memory, long siteRva, long rcx, long rdx, long r8, long r9);
        void call4242284(Memory memory, long siteRva, int ecx);
    }

    sealed interface Outcome permits NormalReturn, Trap { }
    record NormalReturn(long rawRax) implements Outcome { }
    enum Trap implements Outcome {
        INT3_4242283
    }
}
