package org.xar.ck3.research.m1;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

public final class GovernmentResizeBase203 {
    private static final long BASE = 0x4251F4CL;
    private static final long SITE_F64 = 0x4251F64L, SITE_F70 = 0x4251F70L, SITE_F7D = 0x4251F7DL;
    private static final long SITE_F95 = 0x4251F95L, SITE_FA1 = 0x4251FA1L, SITE_FB9 = 0x4251FB9L;
    private static final long TGT_FDA0 = 0x424FDA0L, TGT_E364 = 0x424E364L, TGT_B18C = 0x423B18CL;
    private static final long TGT_E250 = 0x424E250L, TGT_CFFC = 0x424CFFCL;
    private static final long SLOT_IAT = 0x43DA388L, SLOT_GS = 0x5C5DE30L;
    private static final long RET_F8A = 0x4251F8AL, RET_F88 = 0x4251F88L;

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls, LoopBudget budget) {
        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
        long rsp = entry.rspBits();
        long imageBase = entry.imageBaseBits();

        memory.writeQword(rsp + 8, r.rbx);
        memory.writeQword(rsp - 8, r.rdi);
        rsp -= 8;
        rsp -= 0x20;

        r.rbx = r.rdx;
        r.rdi = r.rcx;

        if (r.rcx != 0) {
            if (r.rbx != 0) {
                if (Long.compareUnsigned(r.rbx, 0xFFFFFFFFFFFFFFE0L) <= 0) {
                    while (true) {
                        r.rcx = memory.readQword(imageBase + SLOT_GS);

                        r.r9 = r.rbx;
                        r.r8 = r.rdi;
                        r.rdx = 0L; // XOR EDX, EDX sets entire 64-bit register to 0

                        long targetBits = memory.readQword(imageBase + SLOT_IAT);
                        r = invokeCall(r, rsp, imageBase, SITE_FB9, TargetKind.INDIRECT_ABSOLUTE, targetBits, 6, memory, calls);

                        if (r.rax == 0) {
                            budget.beforeStep(0x4251F95L, 0L);
                            r = invokeCall(r, rsp, imageBase, SITE_F95, TargetKind.DIRECT_RVA, TGT_E250, 5, memory, calls);

                            if ((r.rax & 0xFFFFFFFFL) == 0) {
                                r = invokeCall(r, rsp, imageBase, SITE_F7D, TargetKind.DIRECT_RVA, TGT_B18C, 5, memory, calls);
                                memory.writeDword(r.rax, 0xC);
                                r.rax = 0L; // XOR EAX, EAX sets entire 64-bit register to 0
                                return epilogue(r, rsp, imageBase, memory);
                            }

                            r.rcx = r.rbx;
                            r = invokeCall(r, rsp, imageBase, SITE_FA1, TargetKind.DIRECT_RVA, TGT_CFFC, 5, memory, calls);

                            if ((r.rax & 0xFFFFFFFFL) == 0) {
                                r = invokeCall(r, rsp, imageBase, SITE_F7D, TargetKind.DIRECT_RVA, TGT_B18C, 5, memory, calls);
                                memory.writeDword(r.rax, 0xC);
                                r.rax = 0L;
                                return epilogue(r, rsp, imageBase, memory);
                            }

                        } else {
                            return epilogue(r, rsp, imageBase, memory);
                        }
                    }
                } else {
                    r = invokeCall(r, rsp, imageBase, SITE_F7D, TargetKind.DIRECT_RVA, TGT_B18C, 5, memory, calls);
                    memory.writeDword(r.rax, 0xC);
                    r.rax = 0L;
                    return epilogue(r, rsp, imageBase, memory);
                }
            } else {
                r = invokeCall(r, rsp, imageBase, SITE_F70, TargetKind.DIRECT_RVA, TGT_E364, 5, memory, calls);
                r.rax = 0L;
                return epilogue(r, rsp, imageBase, memory);
            }
        } else {
            r.rcx = r.rdx;
            r = invokeCall(r, rsp, imageBase, SITE_F64, TargetKind.DIRECT_RVA, TGT_FDA0, 5, memory, calls);
            return epilogue(r, rsp, imageBase, memory);
        }
    }

    private static Registers invokeCall(Registers r, long rsp, long imageBase, long site, TargetKind kind, long target, int len, Memory memory, Calls calls) {
        long preRsp = rsp;
        long retAddr = imageBase + site + len;
        memory.writeQword(preRsp - 8, retAddr);
        rsp -= 8;
        VolatileBits v = r.volatileBits();
        NonvolatileBits n = r.nonvolatileBits();
        Call c = new Call(site, kind, target, preRsp, v, n);
        VolatileBits postV = calls.invoke(c);
        r.apply(postV);
        return r;
    }

    private static NormalReturn epilogue(Registers r, long rsp, long imageBase, Memory memory) {
        r.rbx = memory.readQword(rsp + 0x30);
        rsp += 0x20;
        r.rdi = memory.readQword(rsp);
        rsp += 8;
        long retRip = memory.readQword(rsp);
        rsp += 8;
        return new NormalReturn(r.volatileBits(), retRip, rsp, r.nonvolatileBits());
    }
}
