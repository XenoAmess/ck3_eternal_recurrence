package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedInit550Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import java.util.Objects;

public final class EmbeddedInitFullState8895D0 {
    private EmbeddedInitFullState8895D0() { }

    public static FullCopy437Api.CallResult execute(FullCopy437Api.Input input, FullCopy437Api.Memory memory, EmbeddedInit550Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        boolean df = input.directionFlagSet();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits(); // E
        long rcx = entry.volatileBits().rcxBits(); // D (receiver)

        // Prologue: Save RBX, RBP, RSI to E+8, E+0x10, E+0x18
        memory.writeQword(rsp + 0x8, entry.nonvolatileBits().rbxBits());
        memory.writeQword(rsp + 0x10, entry.nonvolatileBits().rbpBits());
        memory.writeQword(rsp + 0x18, entry.nonvolatileBits().rsiBits());
        // Push RDI
        long rspAfterPush = rsp - 8;
        memory.writeQword(rspAfterPush, entry.nonvolatileBits().rdiBits());
        // Sub RSP, 0x20
        long bodyRsp = rspAfterPush - 0x20; // E - 0x28

        // Initialize Registers from Entry
        GovernmentCallee164Api.Entry calleeEntry = new GovernmentCallee164Api.Entry(
            imageBase, rsp, entry.volatileBits(), entry.nonvolatileBits()
        );
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(calleeEntry);
        // Apply initial volatile bits explicitly to ensure state matches entry
        r.apply(entry.volatileBits());

        // 8895E4: LEA rbx,[rcx+0x18]
        r.rbx = rcx + 0x18;
        // 8895E8: XOR ebp,ebp -> ebp = 0
        r.rbp = 0;
        // 8895EA: MOV QWORD PTR [rcx],rbp
        memory.writeQword(rcx, r.rbp);
        // 8895ED: LEA rax,[rip+0x3c03cac] -> rax = imageBase + 0x448D2A0
        r.rax = imageBase + 0x448D2A0L;
        // 8895F4: MOV DWORD PTR [rcx+0x8],ebp
        memory.writeDword(rcx + 0x8, (int)r.rbp);
        // 8895F7: MOV rsi,rcx
        r.rsi = rcx;
        // 8895FA: MOV QWORD PTR [rcx+0x10],rbx
        memory.writeQword(rcx + 0x10, r.rbx);
        // 8895FE: MOV QWORD PTR [rbx],rax
        memory.writeQword(r.rbx, r.rax);
        // 889601: LEA r8d,[rbp+0x8] -> r8d = 8 (since rbp=0)
        r.r8 = 8;
        // 889605: LEA rax,[rip+0x4c54cd4] -> rax = imageBase + 0x54DE2E0
        r.rax = imageBase + 0x54DE2E0L;
        // 88960C: MOV QWORD PTR [rbx+0xc8],rax
        memory.writeQword(r.rbx + 0xC8, r.rax);
        // 889613: MOV rdx,QWORD PTR [rsi]
        r.rdx = memory.readQword(r.rsi);
        // 889616: MOV DWORD PTR [rcx+0xc],ebp
        memory.writeDword(rcx + 0xC, (int)r.rbp);
        // 889619: MOV rcx,QWORD PTR [rcx+0x10]
        r.rcx = memory.readQword(rcx + 0x10);
        // 88961D: MOV rax,QWORD PTR [rcx]
        r.rax = memory.readQword(r.rcx);

        // Call 1: 889620 CALL QWORD PTR [rax+0x10]
        // Read target BEFORE push
        long target1 = memory.readQword(r.rax + 0x10);
        // Physical PUSH of return address to childSP = bodyRsp - 8
        long childRsp1 = bodyRsp - 8;
        memory.writeQword(childRsp1, imageBase + 0x889623L);

        GovernmentCrtBoundary185Api.Call call1 = new GovernmentCrtBoundary185Api.Call(
            0x889620L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target1, bodyRsp, r.volatileBits(), r.nonvolatileBits()
        );
        GovernmentCrtBoundary185Api.Entry childEntry1 = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childRsp1, r.volatileBits(), r.nonvolatileBits()
        );
        EmbeddedInit550Api.CallFrame frame1 = new EmbeddedInit550Api.CallFrame(call1, childEntry1, df, 3, imageBase + 0x889623L);
        FullCopy437Api.CallResult res1 = calls.invoke(frame1);
        frame1.checkNormalReturn(res1);

        // Update state from Call 1
        r.apply(res1.normalReturn().volatileBits());
        df = res1.postDirectionFlagSet();

        // 889623: MOV rax,QWORD PTR [rbx]
        r.rax = memory.readQword(r.rbx);
        // 889626: LEA r8,[rsi+0x8]
        r.r8 = r.rsi + 8;
        // 88962A: MOV rdx,rsi
        r.rdx = r.rsi;
        // 88962D: MOV QWORD PTR [rsi],rbp
        memory.writeQword(r.rsi, r.rbp);
        // 889630: MOV rcx,rbx
        r.rcx = r.rbx;
        // 889633: MOV QWORD PTR [rsi+0x8],rbp
        memory.writeQword(r.rsi + 8, r.rbp);

        // Call 2: 889637 CALL QWORD PTR [rax+0x20]
        // Read target AFTER clears
        long target2 = memory.readQword(r.rax + 0x20);
        // Physical PUSH of return address to childSP = bodyRsp - 8
        long childRsp2 = bodyRsp - 8;
        memory.writeQword(childRsp2, imageBase + 0x88963AL);

        GovernmentCrtBoundary185Api.Call call2 = new GovernmentCrtBoundary185Api.Call(
            0x889637L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, target2, bodyRsp, r.volatileBits(), r.nonvolatileBits()
        );
        GovernmentCrtBoundary185Api.Entry childEntry2 = new GovernmentCrtBoundary185Api.Entry(
            imageBase, childRsp2, r.volatileBits(), r.nonvolatileBits()
        );
        EmbeddedInit550Api.CallFrame frame2 = new EmbeddedInit550Api.CallFrame(call2, childEntry2, df, 3, imageBase + 0x88963AL);
        FullCopy437Api.CallResult res2 = calls.invoke(frame2);
        frame2.checkNormalReturn(res2);

        // Update state from Call 2
        r.apply(res2.normalReturn().volatileBits());
        df = res2.postDirectionFlagSet();

        // Epilogue
        // 88963A: MOV rbx,QWORD PTR [rsp+0x30] -> rsp is bodyRsp (E-28). E-28+0x30 = E+8
        r.rbx = memory.readQword(bodyRsp + 0x30);
        // 88963F: MOV rax,rsi
        r.rax = r.rsi;
        // 889642: MOV rsi,QWORD PTR [rsp+0x40] -> E-28+0x40 = E+0x18
        r.rsi = memory.readQword(bodyRsp + 0x40);
        // 889647: MOV rbp,QWORD PTR [rsp+0x38] -> E-28+0x38 = E+0x10
        r.rbp = memory.readQword(bodyRsp + 0x38);
        // 88964C: ADD rsp,0x20
        long rspAfterAdd = bodyRsp + 0x20; // E-8
        // 889650: POP rdi
        long rdi = memory.readQword(rspAfterAdd);
        long rspAfterPop = rspAfterAdd + 8; // E
        // 889651: RET
        long retAddr = memory.readQword(rspAfterPop);
        long finalCallerRsp = rspAfterPop + 8; // E+8

        GovernmentPrimaryTail155Api.NonvolatileBits finalN = new GovernmentPrimaryTail155Api.NonvolatileBits(
            r.rbx, r.rbp, r.rsi, rdi, r.r12, r.r13, r.r14, r.r15, r.x6
        );
        GovernmentPrimaryTail155Api.VolatileBits finalV = r.volatileBits();

        GovernmentCrtBoundary185Api.NormalReturn nr = new GovernmentCrtBoundary185Api.NormalReturn(
            finalV, retAddr, finalCallerRsp, finalN
        );

        return new FullCopy437Api.CallResult(nr, df);
    }
}