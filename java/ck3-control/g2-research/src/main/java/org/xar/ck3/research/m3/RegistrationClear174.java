package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class RegistrationClear174 {
    private RegistrationClear174() { }

    public static RegistrationClearApi174.Completion clear(NativeTaskMemory memory, RegistrationClearApi174.Ports ports, long receiver, RegistrationClearApi174.Limits limits) {
        // 1. Perform the initial source reads in order: pointer[receiver+B8], signedDWORD[receiver+C4].
        long rbx = memory.readPointer(receiver + 0xB8L);
        int rdi = memory.readInt32(receiver + 0xC4L);

        // 2. If initialcount<0 or>limits.maxFirstRows return UNSUPPORTED_INITIAL_RANGE with those 2 reads only.
        if (rdi < 0 || rdi > limits.maxFirstRows()) {
            return RegistrationClearApi174.Completion.UNSUPPORTED_INITIAL_RANGE;
        }

        // 3. For supported firstpass, preserve full 154B normal ordering.
        // Calculate end pointer: rbp = rbx + (rdi * 0x68)
        long rbp = rbx + (long)rdi * 0x68L;

        // Loop while rbx != rbp
        boolean firstPassEntered = false;
        while (rbx != rbp) {
            firstPassEntered = true;
            // mov rcx, qword ptr [rbx]
            long rcx = memory.readPointer(rbx);
            // mov rdx, rbx
            long rdx = rbx;
            // call 0000000002304040 (destroyRow)
            ports.destroyRow(memory, rcx, rdx);
            // add rbx, 68h
            rbx += 0x68L;
        }

        // mov edi, dword ptr [rsi+00000000000000C4h]
        // Note: rsi was set to rcx (receiver) at 25F8A1B. This is a fresh read of the count.
        // If firstpass was skipped (initial count 0), source does not reload count; preserve initial count.
        int edi = firstPassEntered ? memory.readInt32(receiver + 0xC4L) : rdi;

        // test edi, edi
        // jle 00000000025F8A7B (skip cleanup loop if edi <= 0)
        if (edi > 0) {
            // Check cleanup range limit before entering loop
            if (edi > limits.maxCleanupRows()) {
                return RegistrationClearApi174.Completion.UNSUPPORTED_CLEANUP_RANGE;
            }

            // mov rbx, qword ptr [rsi+00000000000000B8h]
            rbx = memory.readPointer(receiver + 0xB8L);
            // add rbx, 28h
            rbx += 0x28L;

            // Loop while edi > 0
            while (edi > 0) {
                // lea rcx, [rbx+20h]
                long rcx = rbx + 0x20L;
                // call 0000000000856050 (cleanupField)
                ports.cleanupField(memory, rcx);

                // mov rcx, rbx
                rcx = rbx;
                // call 0000000000856050 (cleanupField)
                ports.cleanupField(memory, rcx);

                // dec edi
                edi--;
                // add rbx, 68h
                rbx += 0x68L;
            }
        }

        // 4. Otherwise return CLEARED only after source final count store.
        // mov dword ptr [rsi+00000000000000C4h], 0
        memory.writeInt32(receiver + 0xC4L, 0);

        return RegistrationClearApi174.Completion.CLEARED;
    }
}
