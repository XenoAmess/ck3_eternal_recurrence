package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.control.g2.m2.nativecode.FullPage495Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import java.util.Objects;

public final class PendingPageReserveFullState2A321F0 {
    private PendingPageReserveFullState2A321F0() { }

    public static FullCopy437Api.CallResult execute(FullPage495Api.Input input, FullPage495Api.Memory memory, FullPage495Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.entry();
        long imageBase = entry.imageBaseBits();
        long rsp = entry.rspBits();
        boolean df = input.directionFlagSet();
        GovernmentCrtBoundary185Api.LoopBudget budget = input.budget();

        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(imageBase, rsp, entry.volatileBits(), entry.nonvolatileBits()));

        // 2A321F0: push r14
        r.rsp -= 8;
        memory.writeQword(r.rsp, r.r14);

        // 2A321F2: sub rsp, 0x40
        r.rsp -= 0x40;

        // 2A321F6: cmp BYTE PTR [rcx+0x40], 0
        int flag = memory.readUnsignedByte(r.rcx + 0x40);

        // 2A321FA: mov r14, rcx
        r.r14 = r.rcx;

        // 2A321FD: jne 0x2a3221f
        if (flag != 0) {
            // 2A3221F: xor al, al
            r.rax = (r.rax & ~0xFFL);
            // 2A32221: add rsp, 0x40
            r.rsp += 0x40;
            // 2A32225: pop r14
            r.r14 = memory.readQword(r.rsp);
            r.rsp += 8;
            // 2A32227: ret
            long rip = memory.readQword(r.rsp);
            r.rsp += 8;
            return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
        }

        // 2A321FF: cmp edx, 0xffffff
        if (Integer.compareUnsigned((int) r.rdx, 0xFFFFFF) >= 0) {
            // 2A32207: lea rax, [rip+0x32eb8cb] # 0x5d1dad9
            r.rax = imageBase + 0x5D1DAD9L;
            // 2A3220E: lea rcx, [rip+0x1b842b3] # 0x45b64c8
            r.rcx = imageBase + 0x45B64C8L;
            // 2A32215: mov QWORD PTR [rsp+0x20], rax
            memory.writeQword(r.rsp + 0x20, r.rax);
            // 2A3221A: call 0x3f7aa40
            df = invokeDirect(r, memory, calls, imageBase, df, 0x2A3221A, 0x3F7AA40, 0x2A3221F);
            // 2A3221F: xor al, al
            r.rax = (r.rax & ~0xFFL);
            // 2A32221: add rsp, 0x40
            r.rsp += 0x40;
            // 2A32225: pop r14
            r.r14 = memory.readQword(r.rsp);
            r.rsp += 8;
            // 2A32227: ret
            long rip = memory.readQword(r.rsp);
            r.rsp += 8;
            return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
        }

        // 2A32228: mov QWORD PTR [rsp+0x60], rbp
        memory.writeQword(r.rsp + 0x60, r.rbp);
        // 2A3222D: mov ebp, DWORD PTR [rcx+0xc]
        r.rbp = Integer.toUnsignedLong(memory.readDword(r.rcx + 0xC));
        // 2A32230: mov eax, ebp
        r.rax = r.rbp;
        // 2A32232: shl eax, 0xa
        r.rax = (r.rax << 10) & 0xFFFFFFFFL;
        // 2A32235: cmp edx, eax
        // 2A32237: jbe 0x2a3235f
        if (Integer.compareUnsigned((int) r.rdx, (int) r.rax) <= 0) {
            // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
            r.rbp = memory.readQword(r.rsp + 0x60);
            // 2A32364: mov al, 1
            r.rax = (r.rax & ~0xFFL) | 1;
            // 2A32366: add rsp, 0x40
            r.rsp += 0x40;
            // 2A3236A: pop r14
            r.r14 = memory.readQword(r.rsp);
            r.rsp += 8;
            // 2A3236C: ret
            long rip = memory.readQword(r.rsp);
            r.rsp += 8;
            return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
        }

        // 2A3223D: shr edx, 0xa
        r.rdx = Integer.toUnsignedLong((int) r.rdx >>> 10);
        // 2A32240: mov QWORD PTR [rsp+0x58], rbx
        memory.writeQword(r.rsp + 0x58, r.rbx);
        // 2A32245: mov QWORD PTR [rsp+0x38], rsi
        memory.writeQword(r.rsp + 0x38, r.rsi);
        // 2A3224A: mov QWORD PTR [rsp+0x30], rdi
        memory.writeQword(r.rsp + 0x30, r.rdi);
        // 2A3224F: lea edi, [rdx+0x1]
        r.rdi = (r.rdx + 1) & 0xFFFFFFFFL;
        // 2A32252: cmp edi, ebp
        // 2A32254: jle 0x2a32283
        if ((int) r.rdi <= (int) r.rbp) {
            // 2A32283: mov rcx, QWORD PTR [rcx]
            r.rcx = memory.readQword(r.rcx);
            // 2A32286: movsxd rax, ebp
            r.rax = (long) (int) r.rbp;
            // 2A32289: lea rbx, [rcx+rdi*8]
            r.rbx = r.rcx + (r.rdi * 8);
            // 2A3228D: lea rsi, [rcx+rax*8]
            r.rsi = r.rcx + (r.rax * 8);
            // 2A32291: cmp rbx, rsi
            // 2A32294: je 0x2a322b1
            if (r.rbx == r.rsi) {
                // 2A322B1: mov DWORD PTR [r14+0xc], edi
                memory.writeDword(r.r14 + 0xC, (int) r.rdi);
                // 2A322B5: cmp ebp, edi
                // 2A322B7: jae 0x2a32350
                if (Integer.compareUnsigned((int) r.rbp, (int) r.rdi) >= 0) {
                    // 2A32350: mov rsi, QWORD PTR [rsp+0x38]
                    r.rsi = memory.readQword(r.rsp + 0x38);
                    // 2A32355: mov rbx, QWORD PTR [rsp+0x58]
                    r.rbx = memory.readQword(r.rsp + 0x58);
                    // 2A3235A: mov rdi, QWORD PTR [rsp+0x30]
                    r.rdi = memory.readQword(r.rsp + 0x30);
                    // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
                    r.rbp = memory.readQword(r.rsp + 0x60);
                    // 2A32364: mov al, 1
                    r.rax = (r.rax & ~0xFFL) | 1;
                    // 2A32366: add rsp, 0x40
                    r.rsp += 0x40;
                    // 2A3236A: pop r14
                    r.r14 = memory.readQword(r.rsp);
                    r.rsp += 8;
                    // 2A3236C: ret
                    long rip = memory.readQword(r.rsp);
                    r.rsp += 8;
                    return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
                }
            } else {
                // 2A32296: mov rcx, QWORD PTR [rbx]
                while (r.rbx != r.rsi) {
                    budget.beforeStep(0x2A32296, r.rbx);
                    r.rcx = memory.readQword(r.rbx);
                    // 2A32299: test rcx, rcx
                    // 2A3229C: je 0x2a322a8
                    if (r.rcx != 0) {
                        // 2A3229E: mov edx, 0x172000
                        r.rdx = 0x172000L;
                        // 2A322A3: call 0x4223f44
                        df = invokeDirect(r, memory, calls, imageBase, df, 0x2A322A3, 0x4223F44, 0x2A322A8);
                    }
                    // 2A322A8: add rbx, 0x8
                    r.rbx += 8;
                    // 2A322AC: cmp rbx, rsi
                    // 2A322AF: jne 0x2a32296
                }
                // 2A322B1: mov DWORD PTR [r14+0xc], edi
                memory.writeDword(r.r14 + 0xC, (int) r.rdi);
                // 2A322B5: cmp ebp, edi
                // 2A322B7: jae 0x2a32350
                if (Integer.compareUnsigned((int) r.rbp, (int) r.rdi) >= 0) {
                    // 2A32350: mov rsi, QWORD PTR [rsp+0x38]
                    r.rsi = memory.readQword(r.rsp + 0x38);
                    // 2A32355: mov rbx, QWORD PTR [rsp+0x58]
                    r.rbx = memory.readQword(r.rsp + 0x58);
                    // 2A3235A: mov rdi, QWORD PTR [rsp+0x30]
                    r.rdi = memory.readQword(r.rsp + 0x30);
                    // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
                    r.rbp = memory.readQword(r.rsp + 0x60);
                    // 2A32364: mov al, 1
                    r.rax = (r.rax & ~0xFFL) | 1;
                    // 2A32366: add rsp, 0x40
                    r.rsp += 0x40;
                    // 2A3236A: pop r14
                    r.r14 = memory.readQword(r.rsp);
                    r.rsp += 8;
                    // 2A3236C: ret
                    long rip = memory.readQword(r.rsp);
                    r.rsp += 8;
                    return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
                }
            }
        } else {
            // 2A32256: mov edx, edi
            r.rdx = r.rdi;
            // 2A32258: call 0x2a32620
            df = invokeDirect(r, memory, calls, imageBase, df, 0x2A32258, 0x2A32620, 0x2A3225D);
            // 2A3225D: movsxd rax, DWORD PTR [r14+0xc]
            r.rax = (long) memory.readDword(r.r14 + 0xC);
            // 2A32261: mov edx, edi
            r.rdx = r.rdi;
            // 2A32263: sub edx, eax
            r.rdx = (r.rdx - r.rax) & 0xFFFFFFFFL;
            // 2A32265: mov rcx, rax
            r.rcx = r.rax;
            // 2A32268: mov rax, QWORD PTR [r14]
            r.rax = memory.readQword(r.r14);
            // 2A3226B: lea rcx, [rax+rcx*8]
            r.rcx = r.rax + (r.rcx * 8);
            // 2A3226F: test edx, edx
            // 2A32271: jle 0x2a322b1
            if ((int) r.rdx <= 0) {
                // 2A322B1: mov DWORD PTR [r14+0xc], edi
                memory.writeDword(r.r14 + 0xC, (int) r.rdi);
                // 2A322B5: cmp ebp, edi
                // 2A322B7: jae 0x2a32350
                if (Integer.compareUnsigned((int) r.rbp, (int) r.rdi) >= 0) {
                    // 2A32350: mov rsi, QWORD PTR [rsp+0x38]
                    r.rsi = memory.readQword(r.rsp + 0x38);
                    // 2A32355: mov rbx, QWORD PTR [rsp+0x58]
                    r.rbx = memory.readQword(r.rsp + 0x58);
                    // 2A3235A: mov rdi, QWORD PTR [rsp+0x30]
                    r.rdi = memory.readQword(r.rsp + 0x30);
                    // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
                    r.rbp = memory.readQword(r.rsp + 0x60);
                    // 2A32364: mov al, 1
                    r.rax = (r.rax & ~0xFFL) | 1;
                    // 2A32366: add rsp, 0x40
                    r.rsp += 0x40;
                    // 2A3236A: pop r14
                    r.r14 = memory.readQword(r.rsp);
                    r.rsp += 8;
                    // 2A3236C: ret
                    long rip = memory.readQword(r.rsp);
                    r.rsp += 8;
                    return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
                }
            } else {
                // 2A32273: mov r8d, edx
                r.r8 = r.rdx;
                // 2A32276: xor edx, edx
                r.rdx = 0;
                // 2A32278: shl r8, 0x3
                r.r8 <<= 3;
                // 2A3227C: call 0x4226f10
                df = invokeDirect(r, memory, calls, imageBase, df, 0x2A3227C, 0x4226F10, 0x2A32281);
                // 2A32281: jmp 0x2a322b1
                // 2A322B1: mov DWORD PTR [r14+0xc], edi
                memory.writeDword(r.r14 + 0xC, (int) r.rdi);
                // 2A322B5: cmp ebp, edi
                // 2A322B7: jae 0x2a32350
                if (Integer.compareUnsigned((int) r.rbp, (int) r.rdi) >= 0) {
                    // 2A32350: mov rsi, QWORD PTR [rsp+0x38]
                    r.rsi = memory.readQword(r.rsp + 0x38);
                    // 2A32355: mov rbx, QWORD PTR [rsp+0x58]
                    r.rbx = memory.readQword(r.rsp + 0x58);
                    // 2A3235A: mov rdi, QWORD PTR [rsp+0x30]
                    r.rdi = memory.readQword(r.rsp + 0x30);
                    // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
                    r.rbp = memory.readQword(r.rsp + 0x60);
                    // 2A32364: mov al, 1
                    r.rax = (r.rax & ~0xFFL) | 1;
                    // 2A32366: add rsp, 0x40
                    r.rsp += 0x40;
                    // 2A3236A: pop r14
                    r.r14 = memory.readQword(r.rsp);
                    r.rsp += 8;
                    // 2A3236C: ret
                    long rip = memory.readQword(r.rsp);
                    r.rsp += 8;
                    return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
                }
            }
        }

        // 2A322BD: mov rsi, rbp
        r.rsi = r.rbp;
        // 2A322C0: shl rsi, 0x3
        r.rsi <<= 3;
        // 2A322C4: sub edi, ebp
        r.rdi = (r.rdi - r.rbp) & 0xFFFFFFFFL;
        // 2A322C6: mov ebp, edi
        r.rbp = r.rdi;
        // 2A322D0: mov rbx, QWORD PTR [r14]
        while (r.rbp != 0) {
            budget.beforeStep(0x2A322D0, r.rsi);
            r.rbx = memory.readQword(r.r14);
            // 2A322D3: mov ecx, 0x172000
            r.rcx = 0x172000L;
            // 2A322D8: add rbx, rsi
            r.rbx += r.rsi;
            // 2A322DB: call 0x4223b94
            df = invokeDirect(r, memory, calls, imageBase, df, 0x2A322DB, 0x4223B94, 0x2A322E0);
            // 2A322E0: xor edx, edx
            r.rdx = 0;
            // 2A322E2: mov r8d, 0x172000
            r.r8 = 0x172000L;
            // 2A322E8: mov rcx, rax
            r.rcx = r.rax;
            // 2A322EB: mov rdi, rax
            r.rdi = r.rax;
            // 2A322EE: call 0x4226f10
            df = invokeDirect(r, memory, calls, imageBase, df, 0x2A322EE, 0x4226F10, 0x2A322F3);
            // 2A322F3: lea rax, [rsp+0x50]
            r.rax = r.rsp + 0x50;
            // 2A322F8: cmp rbx, rax
            if (r.rbx == r.rax) {
                // 2A3230A: mov rcx, rdi
                r.rcx = r.rdi;
                // 2A3230D: mov edx, 0x172000
                r.rdx = 0x172000L;
                // 2A32312: call 0x4223f44
                df = invokeDirect(r, memory, calls, imageBase, df, 0x2A32312, 0x4223F44, 0x2A32317);
            } else {
                // 2A322FD: mov rcx, QWORD PTR [rbx]
                r.rcx = memory.readQword(r.rbx);
                // 2A32300: mov QWORD PTR [rbx], rdi
                memory.writeQword(r.rbx, r.rdi);
                // 2A32303: test rcx, rcx
                // 2A32306: je 0x2a32317
                if (r.rcx != 0) {
                    // 2A32308: jmp 0x2a3230d
                    // 2A3230D: mov edx, 0x172000
                    r.rdx = 0x172000L;
                    // 2A32312: call 0x4223f44
                    df = invokeDirect(r, memory, calls, imageBase, df, 0x2A32312, 0x4223F44, 0x2A32317);
                }
            }
            // 2A32317: mov rbx, QWORD PTR [rbx]
            r.rbx = memory.readQword(r.rbx);
            // 2A3231A: xor edx, edx
            r.rdx = 0;
            // 2A3231C: mov rcx, rbx
            r.rcx = r.rbx;
            // 2A3231F: mov r8d, 0x172000
            r.r8 = 0x172000L;
            // 2A32325: call 0x4226f10
            df = invokeDirect(r, memory, calls, imageBase, df, 0x2A32325, 0x4226F10, 0x2A3232A);
            // 2A3232A: lea rax, [rbx+0x10]
            r.rax = r.rbx + 0x10;
            // 2A3232E: mov ecx, 0x400
            r.rcx = 0x400L;
            // 2A32333: mov DWORD PTR [rax], 0xffffffff
            while (r.rcx != 0) {
                budget.beforeStep(0x2A32333, r.rax);
                memory.writeDword(r.rax, -1);
                // 2A32339: lea rax, [rax+0x5c8]
                r.rax += 0x5C8;
                // 2A32340: sub rcx, 0x1
                r.rcx -= 1;
                // 2A32344: jne 0x2a32333
            }
            // 2A32346: add rsi, 0x8
            r.rsi += 8;
            // 2A3234A: sub rbp, 0x1
            r.rbp -= 1;
            // 2A3234E: jne 0x2a322d0
        }

        // 2A32350: mov rsi, QWORD PTR [rsp+0x38]
        r.rsi = memory.readQword(r.rsp + 0x38);
        // 2A32355: mov rbx, QWORD PTR [rsp+0x58]
        r.rbx = memory.readQword(r.rsp + 0x58);
        // 2A3235A: mov rdi, QWORD PTR [rsp+0x30]
        r.rdi = memory.readQword(r.rsp + 0x30);
        // 2A3235F: mov rbp, QWORD PTR [rsp+0x60]
        r.rbp = memory.readQword(r.rsp + 0x60);
        // 2A32364: mov al, 1
        r.rax = (r.rax & ~0xFFL) | 1;
        // 2A32366: add rsp, 0x40
        r.rsp += 0x40;
        // 2A3236A: pop r14
        r.r14 = memory.readQword(r.rsp);
        r.rsp += 8;
        // 2A3236C: ret
        long rip = memory.readQword(r.rsp);
        r.rsp += 8;
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), rip, r.rsp, r.nonvolatileBits()), df);
    }

    private static long unsigned(int bits) { return Integer.toUnsignedLong(bits); }

    private static boolean invokeDirect(GovernmentPrimaryTail155Api.Registers r, FullPage495Api.Memory memory, FullPage495Api.Calls calls, long imageBase,
            boolean df, long site, long target, long continuation) {
        long preSP = r.rsp;
        GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, preSP,
                r.volatileBits(), r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
                imageBase, preSP - 8, call.volatileBits(), call.nonvolatileBits());
        FullPage495Api.CallFrame frame = new FullPage495Api.CallFrame(call, child, df, 5, imageBase + continuation);
        memory.writeQword(child.rspBits(), frame.returnRipBits());
        r.rsp = child.rspBits();
        FullCopy437Api.CallResult result = calls.invoke(frame);
        frame.checkNormalReturn(result);
        r.apply(result.normalReturn().volatileBits());
        r.rsp = result.normalReturn().callerRspBits();
        return result.postDirectionFlagSet();
    }
}
