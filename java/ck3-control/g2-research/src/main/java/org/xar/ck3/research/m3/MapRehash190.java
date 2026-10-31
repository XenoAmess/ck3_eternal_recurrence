package org.xar.ck3.research.m3;

public final class MapRehash190 {
    private MapRehash190() { }

    public static MapRehashApi190.Completion grow(
            MapRehashApi190.Memory memory, MapRehashApi190.Ports ports,
            long moduleBase, long map, MapRehashApi190.Scratch scratch) {
        long entryRsp = scratch.entryRsp();
        long r10 = map;
        int ecx = memory.readInt32(r10 + 0x14L);
        ecx++;
        int eax = CapacityIndex179.select(ecx, 1);
        if (eax >= 0x1F) {
            long rdx = r10;
            long rcx = entryRsp + 0x8L;
            ports.call86f210(memory, rcx, rdx);
            ports.call4232cf4(memory);
            return MapRehashApi190.Completion.UNSUPPORTED_INT3_AFTER_ERROR_CALLS_RETURNED;
        }
        rehash(memory, ports, moduleBase, r10, eax, scratch);
        return MapRehashApi190.Completion.RETURNED;
    }

    public static void rehash(
            MapRehashApi190.Memory memory, MapRehashApi190.Ports ports,
            long moduleBase, long map, int exponent, MapRehashApi190.Scratch scratch) {
        long entryRsp = scratch.entryRsp();
        long local = entryRsp - 0x48L;

        int eax = exponent - 1;
        if (Integer.compareUnsigned(eax, 0x1D) > 0) {
            return;
        }

        int ecx = exponent;

        int dl = (exponent + 2) & 0xFF;
        long rbp = memory.readPointer(map + 0x8L);
        int ebx = 1;
        int edx = dl;
        int r8d = 8;
        memory.write8(map + 0x18L, edx);
        ebx = ebx << ecx;
        long rcx = memory.readPointer(map + 0x20L);
        int edi = memory.readInt32(map + 0x10L);
        eax = ebx - 1;
        memory.writeInt32(map + 0x10L, 0);
        memory.writeInt32(map + 0x14L, eax);
        long rax = memory.readPointer(rcx);
        long r9 = memory.readPointer(rax + 0x8L);
        eax = edx + 1;
        eax = eax + ebx;
        long rdx = (long) eax;
        rdx = rdx + rdx * 4;
        rdx = rdx << 3;
        long allocResult = ports.allocatorSlot08(memory, r9, rcx, rdx, r8d);
        rax = allocResult;
        ecx = memory.readUnsigned8(map + 0x18L);
        rdx = (long) ebx;
        rdx = rdx + ecx;
        memory.writeInt64(map + 0x8L, allocResult);
        rcx = rdx + rdx * 4;
        rdx = rax + rcx * 8;
        if (rax != rdx) {
            memory.write8(rax + 0x4L, 0);
            rax = rax + 0x28L;
            while (rax != rdx) {
                memory.write8(rax + 0x4L, 0);
                rax = rax + 0x28L;
            }
        }
        memory.write8(rdx + 0x4L, 0xFF);
        long tableBase1 = StaticTableBase180.get(memory, ports, moduleBase);
        if (rbp != tableBase1) {
            if (edi > 0) {
                long rbx = rbp + 0x8L;
                while (true) {
                    int flag = memory.readUnsigned8(rbx - 0x4L);
                    if (flag == 0) {
                        rbx = rbx + 0x28L;
                        if (edi > 0) {
                            continue;
                        } else {
                            break;
                        }
                    }
                    int r8d2 = memory.readInt32(rbx - 0x8L);
                    long rax2 = local + 0x58L;
                    long r9_2 = rbx;
                    memory.writeInt64(local + 0x20L, rax2);
                    long rdx2 = local + 0x30L;
                    memory.write8(local + 0x58L, 0);
                    long rcx2 = map;
                    ports.callc3b960(memory, rcx2, rdx2, r8d2, r9_2, rax2);
                    rcx2 = rbx;
                    ports.call856050(memory, rcx2);
                    edi--;
                    rbx = rbx + 0x28L;
                    if (edi <= 0) {
                        break;
                    }
                }
            }
        }
        long tableBase2 = StaticTableBase180.get(memory, ports, moduleBase);
        if (rbp != tableBase2) {
            long rcx3 = memory.readPointer(map + 0x20L);
            int r8d3 = 8;
            long rdx3 = rbp;
            long rax3 = memory.readPointer(rcx3);
            long code = memory.readPointer(rax3 + 0x10L);
            ports.allocatorSlot10(memory, code, rcx3, rdx3, r8d3);
        }
    }
}
