package org.xar.ck3.research.m3.lookup221;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Supplied-storage business contract of 91B at 42422D0; no full CPU ABI. */
public interface ModuleLookup221Api {
    interface Memory extends NativeTaskMemory {
        long readPointer(long address);
        void writeInt64(long address, long value);
    }

    /** Actual entry RSP, supplied by its owner; all local addresses derive from it. */
    record Scratch(long entryRsp) { }

    /** ECX preserves the received low 32-bit pattern. */
    record Input(long moduleBase, int entryECX, Scratch scratch) { }

    interface Ports {
        int call43da458(Memory memory, long siteRva, long codeTarget, long rcx, long rdx, long r8);
        long call43da680(Memory memory, long siteRva, long codeTarget, long rcx, long rdx);
        void call43dbba8(Memory memory, long siteRva, long codeTarget, int ecx, long rax);
        void call43da7c0(Memory memory, long siteRva, long codeTarget, long rcx);
    }

    /** Normal return is void; no Trap or RAX consumption in business projection. */
    void execute(Memory memory, Ports ports, Input input);
}