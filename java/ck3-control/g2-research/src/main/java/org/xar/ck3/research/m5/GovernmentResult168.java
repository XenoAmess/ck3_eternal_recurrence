package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentResult168Api.Instance;
import org.xar.ck3.research.m5.GovernmentResult168Api.WorkBudget;

/** Owned normal-entry translation of the two complete compared RFs; no live Game access. */
public final class GovernmentResult168 {
    private GovernmentResult168() { }
    public static NormalReturn execute(Instance instance, Entry entry, Memory memory, WorkBudget budget) {
        Registers r = GovernmentCallee164Api.registers(entry);
        acquire(instance, r, memory, budget);
        lookup(instance, entry.imageBaseBits(), r, memory, budget);
        return finish(r, memory);
    }
    private static void acquire(Instance instance, Registers r, Memory memory, WorkBudget budget) {
        memory.writeQword(r.rsp + 8, r.rbx);
        r.r8 = 0;
        r.rbx = (int) r.rdx;
        int flag = memory.readUnsignedByte(r.rcx + 0xEE0L);
        r.r9 = flag == 0 ? 1 : 0;
        r.r11 = Integer.toUnsignedLong(-2);
        if (r.r9 == 0) return;
        r.r9 = Integer.toUnsignedLong((int) r.r9 - 1);
        r.r8 = 2;
        long lockAddress = r.rcx + 0xEA0L;
        r.rax = Integer.toUnsignedLong((int) r.r8);
        r.rax = Integer.toUnsignedLong(memory.lockedXaddDword(lockAddress, (int) r.rax));
        while ((r.rax & 1) != 0) {
            budget.beforeStep(instance.entryRva() + 0x80L, lockAddress);
            r.rax = Integer.toUnsignedLong((int) r.r11);
            r.rax = Integer.toUnsignedLong(memory.lockedXaddDword(lockAddress, (int) r.rax));
            do {
                budget.beforeStep(instance.entryRva() + 0x90L, lockAddress);
                r.rax = Integer.toUnsignedLong(memory.readDword(lockAddress));
            } while ((r.rax & 1) != 0);
            r.rax = Integer.toUnsignedLong((int) r.r8);
            r.rax = Integer.toUnsignedLong(memory.lockedXaddDword(lockAddress, (int) r.rax));
        }
        r.r8 = 1;
    }

    private static void lookup(Instance instance, long imageBaseBits, Registers r, Memory memory, WorkBudget budget) {
        r.r9 = memory.readDword(r.rcx + 0x18CL);
        r.r10 = memory.readQword(r.rcx + 0x180L);
        r.rdx = r.r9 & r.rbx;
        r.rax = r.rdx + r.rdx * 2;
        r.rdx = (r.rdx & 0xFFFFFFFFFFFFFF00L) | 1L;
        long bucketAddress = r.r10 + r.rax * 8;
        int marker = memory.readUnsignedByte(bucketAddress + 4L);
        r.rax = bucketAddress;
        boolean fallbackIndex = marker < (int) (r.rdx & 0xFFL);
        if (!fallbackIndex) {
            while (true) {
                budget.beforeStep(instance.entryRva() + 0xD8L, r.rax);
                if ((int) r.rbx == memory.readDword(r.rax + 8L)) break;
                r.rax += 0x18L;
                r.rdx = (r.rdx & 0xFFFFFFFFFFFFFF00L) | ((r.rdx + 1) & 0xFFL);
                int nextMarker = memory.readUnsignedByte(r.rax + 4L);
                if ((int) (r.rdx & 0xFFL) > nextMarker) {
                    fallbackIndex = true;
                    break;
                }
            }
        }
        if (fallbackIndex) {
            r.rax = Integer.toUnsignedLong(memory.readUnsignedByte(r.rcx + 0x190L));
            r.rax = Integer.toUnsignedLong((int) r.rax + 1);
            r.rax = Integer.toUnsignedLong((int) r.rax + (int) r.r9);
            r.rax = (int) r.rax;
            r.rdx = r.rax + r.rax * 2;
            r.rax = r.r10 + r.rdx * 8;
        }
        if (memory.readUnsignedByte(r.rax + 4L) == 0xFF) {
            r.rax = memory.readQword(imageBaseBits + instance.fallbackSlotRva());
        } else {
            r.rax = memory.readQword(r.rax + 0x10L);
        }
    }

    private static NormalReturn finish(Registers r, Memory memory) {
        long r8d = r.r8 & 0xFFFFFFFFL;
        long subResult = (r8d - 1) & 0xFFFFFFFFL;
        r.r8 = subResult;
        if (r.r8 == 0) {
            int r11dAddend = (int) r.r11;
            long lockAddr = r.rcx + 0xEA0L;
            int oldVal = memory.lockedXaddDword(lockAddr, r11dAddend);
            r.r11 = Integer.toUnsignedLong(oldVal);
            r.rbx = memory.readQword(r.rsp + 8);
            long rip = memory.readQword(r.rsp);
            long newRsp = r.rsp + 8;
            return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, newRsp);
        } else if (r.r8 != 1) {
            r.rbx = memory.readQword(r.rsp + 8);
            long rip = memory.readQword(r.rsp);
            long newRsp = r.rsp + 8;
            return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, newRsp);
        } else {
            r.rbx = memory.readQword(r.rsp + 8);
            long rip = memory.readQword(r.rsp);
            long newRsp = r.rsp + 8;
            return new NormalReturn(r.volatileBits(), r.nonvolatileBits(), rip, newRsp);
        }
    }
}
