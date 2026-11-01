package org.xar.ck3.research.m3.lookup221;

import org.xar.ck3.research.m3.lookup221.ModuleLookup221Api;

/** Actual91B business projection for 42422D0. */
public final class ModuleLookup42422D0 implements ModuleLookup221Api {
    public ModuleLookup42422D0() { }

    @Override
    public void execute(Memory memory, Ports ports, Input input) {
        long E = input.scratch().entryRsp();
        long base = input.moduleBase();
        int ecx = input.entryECX();

        // 1. Observable RMW on own slot (entryE + 0x10)
        long slot = E + 0x10L;
        memory.readPointer(slot);
        memory.writeInt64(slot, 0L);

        // 2. First IAT call: 43DA458 @ 42422EC
        long target458 = memory.readPointer(base + 0x43DA458L);
        int eax = ports.call43da458(memory, 0x42422ECL, target458, 0L, base + 0x4423EB8L, slot);

        if (eax != 0) {
            // 3. Second IAT call: 43DA680 @ 4242302
            long rcx = memory.readPointer(slot);
            long target680 = memory.readPointer(base + 0x43DA680L);
            long rax = ports.call43da680(memory, 0x4242302L, target680, rcx, base + 0x4423ED0L);

            if (rax != 0L) {
                // 4. Third IAT call: 43DBBA8 @ 424230F
                long targetbba8 = memory.readPointer(base + 0x43DBBA8L);
                ports.call43dbba8(memory, 0x424230FL, targetbba8, ecx, rax);
            }
        }

        // 5. Fresh slot cleanup and conditional fourth call
        long freshSlot = memory.readPointer(slot);
        if (freshSlot != 0L) {
            long target7c0 = memory.readPointer(base + 0x43DA7C0L);
            ports.call43da7c0(memory, 0x424231FL, target7c0, freshSlot);
        }
    }
}