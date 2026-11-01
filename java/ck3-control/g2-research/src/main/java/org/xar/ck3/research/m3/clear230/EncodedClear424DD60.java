package org.xar.ck3.research.m3.clear230;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.Input;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.Ports;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.RdxR9;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.EntryUnknown;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.Reloaded;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api.IndirectArguments;

public final class EncodedClear424DD60 {
    private EncodedClear424DD60() { }

    public static long execute(NativeTaskMemory memory, Ports ports, Input input) {
        long moduleBase = input.moduleBase();
        long entryRcx = input.entryRcx();

        // 1. Initial pointer chain: R64[entryRcx] -> RAX; R64[RAX] -> RBX
        long rax = memory.readPointer(entryRcx);
        long rbx = memory.readPointer(rax);

        // 2. Null second value check: if RBX == 0, return 0xFFFFFFFF (zero-extended)
        if (rbx == 0L) {
            return 0x00000000FFFFFFFFL;
        }

        // 3. Load global cookie C = R64[base + 0x542F0B8]
        long cookie = memory.readPointer(moduleBase + 0x542F0B8L);
        int ecxLow6 = (int) (cookie & 0x3FL);

        // 4. Decode initial begin/end fields from RBX
        // RDI = ROR64(R8 xor R64[RBX], R8low6)
        long rdi = Long.rotateRight(cookie ^ memory.readPointer(rbx), ecxLow6);
        // RBX = ROR64(R64[RBX+8] xor R8, R8low6)
        long rbxDecoded = Long.rotateRight(memory.readPointer(rbx + 8L) ^ cookie, ecxLow6);

        // 5. Initial guard: if decoded begin (rdi) is 0 or UINT64_MAX, return 0
        // Check: unsigned(rdi - 1) > 0xFFFFFFFFFFFFFFFD
        // This is true if rdi == 0 or rdi == -1 (0xFFFFFFFFFFFFFFFF)
        if (Long.compareUnsigned(rdi - 1L, 0xFFFFFFFFFFFFFFFDL) > 0) {
            return 0L;
        }

        // 6. Setup loop variables
        // R14 captures initial cookie marker (immutable)
        long initialMarker = cookie;
        // R15 captures begin (rdi)
        long savedBegin = rdi;
        // RBP captures end (rbxDecoded)
        long savedEnd = rbxDecoded;
        // Reverse cursor begins at decoded end
        long cursor = savedEnd;
        // RdxR9 state initialized once before loop
        RdxR9 rdxR9State = EntryUnknown.UNKNOWN;

        // 7. Reverse loop
        while (true) {
            // Subtract 8 from cursor before compare
            cursor -= 8L;

            // Compare cursor with current begin (rdi)
            // If cursor < rdi (unsigned), break loop
            if (Long.compareUnsigned(cursor, rdi) < 0) {
                break;
            }

            // Read cell at cursor
            long cellValue = memory.readPointer(cursor);

            // If cellValue == initialMarker, skip (continue to next decrement)
            if (cellValue == initialMarker) {
                continue;
            }

            // Decode cell via current cookie/CL
            // RAX = ROR64(R64[cell] xor currentR8, CL)
            long decodedRax = Long.rotateRight(cellValue ^ cookie, ecxLow6);

            // Write initialMarker to cell BEFORE IAT call
            memory.writeInt64(cursor, initialMarker);

            // Fresh IAT call: R64[base + 0x43DBBA8]
            long iatTarget = memory.readPointer(moduleBase + 0x43DBBA8L);

            // Call 43dbba8 with arguments
            // IndirectArguments: ECX is cookie low6, R8 is current full64 cookie
            IndirectArguments args = new IndirectArguments(ecxLow6, cookie, rdxR9State);
            if (ports instanceof EncodedClear230BoundsPorts) {
                EncodedClear230BoundsPorts boundsPorts = (EncodedClear230BoundsPorts) ports;
                boundsPorts.call43dbba8WithBounds(memory, 0x424DDE5L, iatTarget, decodedRax, args, new EncodedClear230BoundsPorts.DecodedBounds(savedBegin, savedEnd));
            } else {
                ports.call43dbba8(memory, 0x424DDE5L, iatTarget, decodedRax, args);
            }

            // After opaque return: refresh global cookie, entryRcx, outer, descriptor, begin/end
            cookie = memory.readPointer(moduleBase + 0x542F0B8L);
            ecxLow6 = (int) (cookie & 0x3FL);

            long outer = memory.readPointer(entryRcx);
            long descriptor = memory.readPointer(outer);
            long encodedBegin = memory.readPointer(descriptor);
            long encodedEnd = memory.readPointer(descriptor + 8L);

            // Decode new begin/end
            long newBegin = Long.rotateRight(encodedBegin ^ cookie, ecxLow6);
            long newEnd = Long.rotateRight(encodedEnd ^ cookie, ecxLow6);

            // Update RdxR9 to Reloaded
            rdxR9State = new Reloaded(descriptor, newBegin);

            // Check if bounds changed
            if (newBegin == savedBegin && newEnd == savedEnd) {
                // Continue current cursor
                // No restart
            } else {
                // Save new begin/end
                savedBegin = newBegin;
                savedEnd = newEnd;
                // Restart from new end
                cursor = savedEnd;
                // Update rdi for comparison in next iteration
                rdi = savedBegin;
            }
        }

        // 8. Final free branch
        // If rdi (current begin) == UINT64_MAX, skip direct E364 and post-free cookie reload
        if (rdi != 0xFFFFFFFFFFFFFFFFL) {
            // Call 424e364 with RCX = current begin (rdi)
            if (ports instanceof EncodedClear230BoundsPorts) {
                EncodedClear230BoundsPorts boundsPorts = (EncodedClear230BoundsPorts) ports;
                boundsPorts.call424e364WithBounds(memory, 0x424DE32L, rdi, new EncodedClear230BoundsPorts.DecodedBounds(savedBegin, savedEnd));
            } else {
                ports.call424e364(memory, 0x424DE32L, rdi);
            }

            // After normal return, fresh global cookie => R8
            cookie = memory.readPointer(moduleBase + 0x542F0B8L);
        }

        // 9. Final three stores
        // Each store independently fresh R64[entryRcx] THEN fresh R64[outer] before W64[target+offset]=same localR8
        // Offset 0
        long outer0 = memory.readPointer(entryRcx);
        long target0 = memory.readPointer(outer0);
        memory.writeInt64(target0 + 0L, cookie);

        // Offset 8
        long outer8 = memory.readPointer(entryRcx);
        long target8 = memory.readPointer(outer8);
        memory.writeInt64(target8 + 8L, cookie);

        // Offset 16
        long outer16 = memory.readPointer(entryRcx);
        long target16 = memory.readPointer(outer16);
        memory.writeInt64(target16 + 16L, cookie);

        // 10. Return 0
        return 0L;
    }
}