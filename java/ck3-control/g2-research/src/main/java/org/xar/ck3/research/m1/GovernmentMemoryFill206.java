package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;

public final class GovernmentMemoryFill206 {
    private GovernmentMemoryFill206() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentMemoryFill206Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        
        // Prefix: R11=RCX, EDX=zeroextendedDL, R9=0x101010101010101*RDX
        r.r11 = r.rcx;
        r.rdx = r.rdx & 0xFFL;
        r.r9 = 0x0101010101010101L * r.rdx;
        
        long r8 = r.r8;
        
        if (Long.compareUnsigned(r8, 16L) <= 0) {
            // <=16 path: no XMM0 touch, table dispatch
            r.rdx = r.r9;
            r.r9 = imageBase;
            long tableAddr = imageBase + 0x60900B0L + r8 * 4L;
            int eax = memory.readDword(tableAddr);
            r.rax = Integer.toUnsignedLong(eax);
            r.r9 += r.rax;
            r.rcx += r8;
            r.rax = r.r11;
            
            long target = r.r9;
            if (target == imageBase + 0x422704EL) { // index 0
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x422704BL) { // index 1
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227077L) { // index 2
                memory.writeWord(r.rcx - 2, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227047L) { // index 3
                memory.writeWord(r.rcx - 3, (int)r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227054L) { // index 4
                memory.writeDword(r.rcx - 4, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227064L) { // index 5
                memory.writeDword(r.rcx - 5, (int)r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227074L) { // index 6
                memory.writeDword(r.rcx - 6, (int)r.rdx);
                memory.writeWord(r.rcx - 2, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227044L) { // index 7
                memory.writeDword(r.rcx - 7, (int)r.rdx);
                memory.writeWord(r.rcx - 3, (int)r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x422707CL) { // index 8
                memory.writeQword(r.rax, r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227058L) { // index 9
                memory.writeQword(r.rcx - 9, r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227090L) { // index 10
                memory.writeQword(r.rax, r.rdx);
                memory.writeWord(r.rax + 8, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227080L) { // index 11
                memory.writeQword(r.rax, r.rdx);
                memory.writeWord(r.rax + 8, (int)r.rdx);
                memory.writeByte(r.rax + 0xA, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227050L) { // index 12
                memory.writeQword(r.rcx - 0xC, r.rdx);
                memory.writeDword(r.rcx - 4, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227060L) { // index 13
                memory.writeQword(r.rcx - 0xD, r.rdx);
                memory.writeDword(r.rcx - 5, (int)r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227070L) { // index 14
                memory.writeQword(r.rcx - 0xE, r.rdx);
                memory.writeDword(r.rcx - 6, (int)r.rdx);
                memory.writeWord(r.rcx - 2, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227040L) { // index 15
                memory.writeQword(r.rcx - 0xF, r.rdx);
                memory.writeDword(r.rcx - 7, (int)r.rdx);
                memory.writeWord(r.rcx - 3, (int)r.rdx);
                memory.writeByte(r.rcx - 1, (int)r.rdx);
                return finish(r, rsp, memory);
            } else if (target == imageBase + 0x4227098L) { // index 16
                memory.writeQword(r.rax, r.rdx);
                memory.writeQword(r.rax + 8, r.rdx);
                return finish(r, rsp, memory);
            } else {
                return calls.tail(new GovernmentCrtBoundary185Api.Tail(
                    0x422703BL, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target,
                    new GovernmentCrtBoundary185Api.Entry(imageBase, rsp, r.volatileBits(), r.nonvolatileBits())));
            }
        }
        
        // >16 path: construct XMM0
        long pattern = 0x0101010101010101L * r.rdx;
        r.x0 = new GovernmentPrimaryTail155Api.Bits128(pattern, pattern);
        
        if (Long.compareUnsigned(r8, 0x80L) > 0) {
            // Check global byte at 5C5CBB0
            int flag = memory.readUnsignedByte(imageBase + 0x5C5CBB0L) & 2;
            if (flag != 0) {
                return calls.tail(new GovernmentCrtBoundary185Api.Tail(
                    0x4226F57L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226EF0L,
                    new GovernmentCrtBoundary185Api.Entry(imageBase, rsp, r.volatileBits(), r.nonvolatileBits())));
            }
            
            // One-off write128 at RCX
            memory.write128(r.rcx, r.x0);
            
            // Exact source arithmetic
            r.r8 += r.rcx;
            r.rcx += 0x10L;
            r.rcx &= ~0xF;
            r.r8 -= r.rcx;
            r.r9 = r.r8 >>> 7;
            
            if (r.r9 != 0) {
                long threshold = memory.readQword(imageBase + 0x542F0A8L);
                boolean useNT = Long.compareUnsigned(r.r9, threshold) > 0;
                
                if (useNT) {
                    // Non-temporal loop at 4226FE0
                    while (r.r9 != 0) {
                        budget.beforeStep(0x4226FE0L, r.rcx);
                        memory.write128NonTemporal(r.rcx, r.x0);
                        memory.write128NonTemporal(r.rcx + 0x10, r.x0);
                        r.rcx += 0x80;
                        memory.write128NonTemporal(r.rcx - 0x60, r.x0);
                        memory.write128NonTemporal(r.rcx - 0x50, r.x0);
                        r.r9--;
                        memory.write128NonTemporal(r.rcx - 0x40, r.x0);
                        memory.write128NonTemporal(r.rcx - 0x30, r.x0);
                        memory.write128NonTemporal(r.rcx - 0x20, r.x0);
                        memory.write128NonTemporal(r.rcx - 0x10, r.x0);
                    }
                    memory.sfence();
                } else {
                    // Cached ordinary loop at 4226F80
                    while (r.r9 != 0) {
                        budget.beforeStep(0x4226F80L, r.rcx);
                        memory.write128(r.rcx, r.x0);
                        memory.write128(r.rcx + 0x10, r.x0);
                        r.rcx += 0x80;
                        memory.write128(r.rcx - 0x60, r.x0);
                        memory.write128(r.rcx - 0x50, r.x0);
                        r.r9--;
                        memory.write128(r.rcx - 0x40, r.x0);
                        memory.write128(r.rcx - 0x30, r.x0);
                        memory.write128(r.rcx - 0x20, r.x0);
                        memory.write128(r.rcx - 0x10, r.x0);
                    }
                }
            }
            
            // AND R8, 7F
            r.r8 &= 0x7F;
        }
        
        // Common FB0: R9 = R8 >>> 4
        r.r9 = r.r8 >>> 4;
        if (r.r9 != 0) {
            // FC0 loop
            while (r.r9 != 0) {
                budget.beforeStep(0x4226FC0L, r.rcx);
                memory.write128(r.rcx, r.x0);
                r.rcx += 0x10;
                r.r9--;
            }
        }
        
        // R8 &= 0xF
        r.r8 &= 0xF;
        if (r.r8 != 0) {
            // Overlap write at 4226FD2: movups [rcx + r8 - 0x10], xmm0
            memory.write128(r.rcx + r.r8 - 0x10, r.x0);
        }
        
        // Final: RAX = R11
        r.rax = r.r11;
        
        return finish(r, rsp, memory);
    }

    private static GovernmentCrtBoundary185Api.NormalReturn finish(GovernmentPrimaryTail155Api.Registers r, long rsp, GovernmentMemoryFill206Api.Memory memory) {
        long returnRip = memory.readQword(rsp);
        return new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip, rsp + 8, r.nonvolatileBits());
    }
}
