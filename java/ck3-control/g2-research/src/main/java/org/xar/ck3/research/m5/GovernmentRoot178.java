package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Entry;
import org.xar.ck3.research.m5.GovernmentRoot178Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Memory;
import org.xar.ck3.research.m5.GovernmentRoot178Api.Calls;

public final class GovernmentRoot178 {
    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        VolatileBits v = entry.volatileBits();
        NonvolatileBits nv = entry.nonvolatileBits();

        // Prologue: sub rsp, 0x28
        rsp = rsp - 0x28;

        // mov edx, 0x10
        v = new VolatileBits(v.raxBits(), v.rcxBits(), 0x10L, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

        // mov rax, QWORD PTR gs:0x58
        long gs58 = calls.readGsQword58();
        v = new VolatileBits(gs58, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

        // mov rcx, QWORD PTR [rax]
        long rax = v.raxBits();
        long rcx = memory.readQword(rax);
        v = new VolatileBits(rax, rcx, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

        // mov eax, DWORD PTR [rdx+rcx*1]
        long rdx = v.rdxBits();
        long addr = rdx + rcx;
        int eax = memory.readDword(addr);
        v = new VolatileBits(Integer.toUnsignedLong(eax), rcx, rdx, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

        // cmp DWORD PTR [rip+0x1e65112], eax # 0x5dc11c0
        long cmpAddr = imageBase + 0x5dc11c0L;
        int cmpVal = memory.readDword(cmpAddr);
        int eaxVal = (int)v.raxBits();
        boolean jg = cmpVal > eaxVal;

        if (jg) {
            // jg 0x3f5c0bc -> jump to 0x3f5c0bc
            // lea rcx, [rip+0x1e650fd] # 0x5dc11c0
            long leaAddr = imageBase + 0x5dc11c0L;
            v = new VolatileBits(v.raxBits(), leaAddr, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                    v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

            // call 0x4223a84
            long callSiteRva = 0x3f5c0c3L;
            long targetRva = 0x4223a84L;
            long preCallRsp = rsp;
            long retAddr = imageBase + callSiteRva + 5;
            memory.writeQword(preCallRsp - 8, retAddr);
            OpaqueCall oc = new OpaqueCall(callSiteRva, targetRva, preCallRsp, v, nv);
            v = calls.invoke(oc);

            // cmp DWORD PTR [rip+0x1e650f1], 0xffffffff # 0x5dc11c0
            long cmp2Addr = imageBase + 0x5dc11c0L;
            int cmp2Val = memory.readDword(cmp2Addr);
            boolean jne = cmp2Val != 0xffffffff;

            if (jne) {
                // jne 0x3f5c0b0 -> jump to 0x3f5c0b0
                // lea rax, [rip+0x1e65119] # 0x5dc11d0
                long lea2Addr = imageBase + 0x5dc11d0L;
                v = new VolatileBits(lea2Addr, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // add rsp, 0x28
                rsp = rsp + 0x28;

                // ret
                long returnRip = memory.readQword(rsp);
                rsp = rsp + 8;
                return new NormalReturn(v, returnRip, rsp, nv);
            } else {
                // xorps xmm0, xmm0
                Bits128 zeroXmm = new Bits128(0L, 0L);
                v = new VolatileBits(v.raxBits(), v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        zeroXmm, v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // movss DWORD PTR [rip+0x1e650f4], xmm0 # 0x5dc11d0
                long movssAddr = imageBase + 0x5dc11d0L;
                int low32 = (int)v.xmm0().lowBits();
                memory.writeDword(movssAddr, low32);

                // mov QWORD PTR [rip+0x1e650f1], 0x0 # 0x5dc11d8
                long mov1Addr = imageBase + 0x5dc11d8L;
                memory.writeQword(mov1Addr, 0L);

                // mov QWORD PTR [rip+0x1e650ee], 0x0 # 0x5dc11e0
                long mov2Addr = imageBase + 0x5dc11e0L;
                memory.writeQword(mov2Addr, 0L);

                // mov ecx, 0x40
                v = new VolatileBits(v.raxBits(), 0x40L, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // call 0x4223b94
                long callSiteRva2 = 0x3f5c0f7L;
                long targetRva2 = 0x4223b94L;
                long preCallRsp2 = rsp;
                long retAddr2 = imageBase + callSiteRva2 + 5;
                memory.writeQword(preCallRsp2 - 8, retAddr2);
                OpaqueCall oc2 = new OpaqueCall(callSiteRva2, targetRva2, preCallRsp2, v, nv);
                v = calls.invoke(oc2);

                // mov QWORD PTR [rax], rax
                long rax2 = v.raxBits();
                memory.writeQword(rax2, rax2);

                // mov QWORD PTR [rax+0x8], rax
                memory.writeQword(rax2 + 8, rax2);

                // mov QWORD PTR [rip+0x1e650ce], rax # 0x5dc11d8
                long mov3Addr = imageBase + 0x5dc11d8L;
                memory.writeQword(mov3Addr, rax2);

                // mov QWORD PTR [rip+0x1e650d3], 0x0 # 0x5dc11e8
                long mov4Addr = imageBase + 0x5dc11e8L;
                memory.writeQword(mov4Addr, 0L);

                // xorps xmm0, xmm0
                Bits128 zeroXmm2 = new Bits128(0L, 0L);
                v = new VolatileBits(v.raxBits(), v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        zeroXmm2, v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // movdqa XMMWORD PTR [rip+0x1e650d0], xmm0 # 0x5dc11f0
                long movdqaAddr = imageBase + 0x5dc11f0L;
                memory.write128(movdqaAddr, zeroXmm2);

                // mov QWORD PTR [rip+0x1e650d5], 0x7 # 0x5dc1200
                long mov5Addr = imageBase + 0x5dc1200L;
                memory.writeQword(mov5Addr, 7L);

                // mov QWORD PTR [rip+0x1e650d2], 0x8 # 0x5dc1208
                long mov6Addr = imageBase + 0x5dc1208L;
                memory.writeQword(mov6Addr, 8L);

                // movss xmm0, DWORD PTR [rip+0xa9a326] # 0x49f6464
                long movss2Addr = imageBase + 0x49f6464L;
                int srcLow32 = memory.readDword(movss2Addr);
                Bits128 xmm0 = new Bits128(Integer.toUnsignedLong(srcLow32), 0L);
                v = new VolatileBits(v.raxBits(), v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        xmm0, v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // movss DWORD PTR [rip+0x1e6508a], xmm0 # 0x5dc11d0
                long movss3Addr = imageBase + 0x5dc11d0L;
                int dstLow32 = (int)v.xmm0().lowBits();
                memory.writeDword(movss3Addr, dstLow32);

                // mov r8, rax
                v = new VolatileBits(v.raxBits(), v.rcxBits(), v.rdxBits(), v.raxBits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // mov edx, 0x10
                v = new VolatileBits(v.raxBits(), v.rcxBits(), 0x10L, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // lea rcx, [rip+0x1e65093] # 0x5dc11e8
                long lea3Addr = imageBase + 0x5dc11e8L;
                v = new VolatileBits(v.raxBits(), lea3Addr, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // call 0x3714560
                long callSiteRva3 = 0x3f5c155L;
                long targetRva3 = 0x3714560L;
                long preCallRsp3 = rsp;
                long retAddr3 = imageBase + callSiteRva3 + 5;
                memory.writeQword(preCallRsp3 - 8, retAddr3);
                OpaqueCall oc3 = new OpaqueCall(callSiteRva3, targetRva3, preCallRsp3, v, nv);
                v = calls.invoke(oc3);

                // nop

                // lea rcx, [rip+0x47b6be] # 0x43d7820
                long lea4Addr = imageBase + 0x43d7820L;
                v = new VolatileBits(v.raxBits(), lea4Addr, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // call 0x4223f24
                long callSiteRva4 = 0x3f5c162L;
                long targetRva4 = 0x4223f24L;
                long preCallRsp4 = rsp;
                long retAddr4 = imageBase + callSiteRva4 + 5;
                memory.writeQword(preCallRsp4 - 8, retAddr4);
                OpaqueCall oc4 = new OpaqueCall(callSiteRva4, targetRva4, preCallRsp4, v, nv);
                v = calls.invoke(oc4);

                // nop

                // lea rcx, [rip+0x1e65051] # 0x5dc11c0
                long lea5Addr = imageBase + 0x5dc11c0L;
                v = new VolatileBits(v.raxBits(), lea5Addr, v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // call 0x4223a24
                long callSiteRva5 = 0x3f5c16fL;
                long targetRva5 = 0x4223a24L;
                long preCallRsp5 = rsp;
                long retAddr5 = imageBase + callSiteRva5 + 5;
                memory.writeQword(preCallRsp5 - 8, retAddr5);
                OpaqueCall oc5 = new OpaqueCall(callSiteRva5, targetRva5, preCallRsp5, v, nv);
                v = calls.invoke(oc5);

                // lea rax, [rip+0x1e65055] # 0x5dc11d0
                long lea6Addr = imageBase + 0x5dc11d0L;
                v = new VolatileBits(lea6Addr, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                        v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

                // add rsp, 0x28
                rsp = rsp + 0x28;

                // ret
                long returnRip = memory.readQword(rsp);
                rsp = rsp + 8;
                return new NormalReturn(v, returnRip, rsp, nv);
            }
        } else {
            // lea rax, [rip+0x1e65119] # 0x5dc11d0
            long leaRaxAddr = imageBase + 0x5dc11d0L;
            v = new VolatileBits(leaRaxAddr, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits(),
                    v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());

            // add rsp, 0x28
            rsp = rsp + 0x28;

            // ret
            long returnRip = memory.readQword(rsp);
            rsp = rsp + 8;
            return new NormalReturn(v, returnRip, rsp, nv);
        }
    }
}
