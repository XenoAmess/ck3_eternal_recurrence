package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Memory;

/**
 * Executes ONLY original17B[0x88036A,0x88037B) instructions:
 * LEA ESI,[RAX+1], MOVD XMM0,ECX, MOV RCX,QWORD[RBX+0x10], MOV R8D,8.
 * EntryRegisters currentaftergrowthselectedCMP: RAXsignedcount,ECXcapacitylow32,RBXcontainer,otherscurrent,bodySPexisting.
 * Honor32bitESIwrap+zeroextend/MOVDlow32zerosallupper96/64bitfreshallocatorRCX/R8Dzeroextend8 andEXACTorder.
 * SameMemorycanobserveRegisters orthrow atreadQword, thenallpriorinteger/lanechangespersist butlaterR8writehasnotoccurred; no catch/repair/reorder.
 * PreserveallotherGPR/XMM1..6/SP/RBP/N. STOPbeforeCVTDQ2PS: no Javafloat/double/FProunding/MXCSRdefault orFPstatusclaims, Calls/push/RET/loops/RAMwrites/Test/newAPI/platform.
 * NullguardmaybeoptionalbutnotextraMemory. Existing599partialentryiscontextonly, do notinvokeorchangeit.
 * Completeactualshape/interval/instructionsgiven, noownernewbody/oracle/expectedtrace. Notfull227growth/Nativeimplementation.
 */
public final class QueueAppendGrowthPreFp602 {
    private QueueAppendGrowthPreFp602() { }

    public static void prepare(Registers r, Memory memory) {
        // LEA ESI,[RAX+1] -> rsi = rax + 1 (32-bit wrap, zero-extended to 64-bit)
        r.rsi = Integer.toUnsignedLong((int)(r.rax + 1));

        // MOVD XMM0,ECX -> xmm0 low 32 bits = ecx, upper 96 bits zero
        r.x0 = new Bits128(Integer.toUnsignedLong((int)r.rcx), 0L);

        // MOV RCX,QWORD[RBX+0x10] -> rcx = readQword(rbx + 0x10)
        r.rcx = memory.readQword(r.rbx + 0x10);

        // MOV R8D,8 -> r8 = 8 (zero-extended)
        r.r8 = 8L;
    }
}