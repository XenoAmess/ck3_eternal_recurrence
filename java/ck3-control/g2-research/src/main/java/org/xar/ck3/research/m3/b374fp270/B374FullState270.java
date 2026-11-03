package org.xar.ck3.research.m3.b374fp270;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;

/** Retained374-byte normal source protocol; opaque lower Outcomes, no hardware or loaded proof. */
public final class B374FullState270 {
    private B374FullState270() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, B374Fp270Api.Calls calls) {
        Objects.requireNonNull(input);
        State s = new State(input, Objects.requireNonNull(memory), Objects.requireNonNull(calls));
        try {
            prolog(s);
            firstFields(s);
            at100(s);
            // 42567EB MOV RCX,[RBX+120]; 42567F2 CALL425689C.
            s.r.rcx = s.memory.readQword(s.r.rbx + 0x120L);
            invoke(s, 0x42567F2L, 0x425689CL);
            rows(s);
            return epilogAndTail(s);
        } catch (StoppedSignal signal) {
            return signal.outcome;
        }
    }

    private static void prolog(State s) {
        long entryRsp = s.r.rsp;
        s.memory.writeQword(entryRsp + 8L, s.r.rbx);
        s.memory.writeQword(entryRsp + 0x10L, s.r.rbp);
        s.memory.writeQword(entryRsp + 0x18L, s.r.rsi);
        s.memory.writeQword(entryRsp - 8L, s.r.rdi);
        s.r.rsp = entryRsp - 0x28L;
    }

    private static void firstFields(State s) {
        // 4256710: MOV RAX, QWORD [RCX + 0xF8]
        long firstRax = s.memory.readQword(s.r.rcx + 0xF8L);
        s.r.rax = firstRax;

        // 4256717: MOV RBX, RCX
        s.r.rbx = s.r.rcx;

        // 425671A: TEST RAX, RAX
        // 425671D: JE 0x4256798 (if RAX == 0)
        if (firstRax == 0) {
            return;
        }

        // 425671F: LEA RCX, [RIP + 0x11D8AFA] -> image + 0x542F220
        long sentinel1 = s.image + 0x542F220L;
        s.r.rcx = sentinel1;

        // 4256726: CMP RAX, RCX
        // 4256729: JE 0x4256798 (if RAX == RCX)
        if (firstRax == sentinel1) {
            return;
        }

        // 425672B: MOV RAX, QWORD [RBX + 0xE0]
        long e0 = s.memory.readQword(s.r.rbx + 0xE0L);
        s.r.rax = e0;

        // 4256732: TEST RAX, RAX
        // 4256735: JE 0x4256798 (if RAX == 0)
        if (e0 == 0) {
            return;
        }

        // 4256737: CMP DWORD [RAX], 0
        // 425673A: JNE 0x4256798 (if DWORD != 0)
        if (s.memory.readDword(e0) != 0) {
            return;
        }

        // 425673C: MOV RCX, QWORD [RBX + 0xF0]
        long f0 = s.memory.readQword(s.r.rbx + 0xF0L);
        s.r.rcx = f0;

        // 4256743: TEST RCX, RCX
        // 4256746: JE 0x425675E (if RCX == 0)
        if (f0 != 0) {
            // 4256748: CMP DWORD [RCX], 0
            // 425674B: JNE 0x425675E (if DWORD != 0)
            if (s.memory.readDword(f0) == 0) {
                // 425674D: CALL 0x424E364
                invoke(s, 0x425674DL, 0x424E364L);

                // 4256752: MOV RCX, QWORD [RBX + 0xF8]
                s.r.rcx = s.memory.readQword(s.r.rbx + 0xF8L);

                // 4256759: CALL 0x42552D0
                invoke(s, 0x4256759L, 0x42552D0L);
            }
        }

        // 425675E: MOV RCX, QWORD [RBX + 0xE8]
        long e8 = s.memory.readQword(s.r.rbx + 0xE8L);
        s.r.rcx = e8;

        // 4256765: TEST RCX, RCX
        // 4256768: JE 0x4256780 (if RCX == 0)
        if (e8 != 0) {
            // 425676A: CMP DWORD [RCX], 0
            // 425676D: JNE 0x4256780 (if DWORD != 0)
            if (s.memory.readDword(e8) == 0) {
                // 425676F: CALL 0x424E364
                invoke(s, 0x425676FL, 0x424E364L);

                // 4256774: MOV RCX, QWORD [RBX + 0xF8]
                s.r.rcx = s.memory.readQword(s.r.rbx + 0xF8L);

                // 425677B: CALL 0x4255910
                invoke(s, 0x425677BL, 0x4255910L);
            }
        }

        // 4256780: MOV RCX, QWORD [RBX + 0xE0]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0xE0L);

        // 4256787: CALL 0x424E364
        invoke(s, 0x4256787L, 0x424E364L);

        // 425678C: MOV RCX, QWORD [RBX + 0xF8]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0xF8L);

        // 4256793: CALL 0x424E364
        invoke(s, 0x4256793L, 0x424E364L);
    }

    private static void at100(State s) {
        // 4256798: MOV RAX, QWORD PTR [RBX + 0x100]
        long rax = s.memory.readQword(s.r.rbx + 0x100L);
        s.r.rax = rax;

        // 425679F: TEST RAX, RAX
        if (rax == 0) {
            return; // JE 0x42567EB
        }

        // 42567A4: CMP DWORD PTR [RAX], 0
        int dwordVal = s.memory.readDword(rax);
        if (dwordVal != 0) {
            return; // JNE 0x42567EB
        }

        // 42567A9: MOV RCX, QWORD PTR [RBX + 0x108]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0x108L);
        // 42567B0: SUB RCX, 0xFE
        s.r.rcx -= 0xFE;
        // 42567B7: CALL 0x424E364
        invoke(s, 0x42567B7L, 0x424E364L);

        // 42567BC: MOV RCX, QWORD PTR [RBX + 0x110]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0x110L);
        // 42567C3: MOV EDI, 0x80
        s.r.rdi = 0x80;
        // 42567C8: SUB RCX, RDI
        s.r.rcx -= s.r.rdi;
        // 42567CB: CALL 0x424E364
        invoke(s, 0x42567CBL, 0x424E364L);

        // 42567D0: MOV RCX, QWORD PTR [RBX + 0x118]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0x118L);
        // 42567D7: SUB RCX, RDI
        s.r.rcx -= s.r.rdi;
        // 42567DA: CALL 0x424E364
        invoke(s, 0x42567DAL, 0x424E364L);

        // 42567DF: MOV RCX, QWORD PTR [RBX + 0x100]
        s.r.rcx = s.memory.readQword(s.r.rbx + 0x100L);
        // 42567E6: CALL 0x424E364
        invoke(s, 0x42567E6L, 0x424E364L);
    }

    private static void rows(State s) {
        // 42567F7: LEA RSI, [RBX + 0x128]
        s.r.rsi = s.r.rbx + 0x128L;
        // 42567FE: MOV EBP, 6
        s.r.rbp = 6L;
        // 4256803: LEA RDI, [RBX + 0x38]
        s.r.rdi = s.r.rbx + 0x38L;

        // Fixed six iterations
        for (int i = 0; i < 6; i++) {
            // 4256807: LEA RAX, [RIP + 0x11d8c8a] -> image + 0x542f498
            s.r.rax = s.image + 0x542f498L;

            // 425680E: CMP QWORD PTR [RDI - 0x10], RAX
            long cmpVal = s.memory.readQword(s.r.rdi - 0x10L);
            if (cmpVal == s.r.rax) {
                // JE 0x425682E: Skip to 425682E
            } else {
                // 4256814: MOV RCX, QWORD PTR [RDI]
                s.r.rcx = s.memory.readQword(s.r.rdi);
                // 4256817: TEST RCX, RCX
                if (s.r.rcx != 0) {
                    // 425681C: CMP DWORD PTR [RCX], 0
                    int dwordVal = s.memory.readDword(s.r.rcx);
                    if (dwordVal == 0) {
                        // 4256821: CALL 0x424E364
                        invoke(s, 0x4256821L, 0x424E364L);
                        // 4256826: MOV RCX, QWORD PTR [RSI]
                        s.r.rcx = s.memory.readQword(s.r.rsi);
                        // 4256829: CALL 0x424E364
                        invoke(s, 0x4256829L, 0x424E364L);
                    }
                }
            }

            // 425682E: CMP QWORD PTR [RDI - 0x18], 0
            long cmp2Val = s.memory.readQword(s.r.rdi - 0x18L);
            if (cmp2Val != 0) {
                // 4256835: MOV RCX, QWORD PTR [RDI - 8]
                s.r.rcx = s.memory.readQword(s.r.rdi - 8L);
                // 4256839: TEST RCX, RCX
                if (s.r.rcx != 0) {
                    // 425683E: CMP DWORD PTR [RCX], 0
                    int dwordVal2 = s.memory.readDword(s.r.rcx);
                    if (dwordVal2 == 0) {
                        // 4256843: CALL 0x424E364
                        invoke(s, 0x4256843L, 0x424E364L);
                    }
                }
            }

            // 4256848: ADD RSI, 8
            s.r.rsi += 8L;
            // 425684C: ADD RDI, 0x20
            s.r.rdi += 0x20L;
            // 4256850: SUB RBP, 1
            s.r.rbp -= 1L;
            // 4256854: JNE 0x4256807 (Loop back if RBP != 0)
        }
    }

    private static QueueFp604Api.Outcome epilogAndTail(State s) {
        // 4256856: MOV RCX, RBX
        s.r.rcx = s.r.rbx;

        // 4256859: MOV RBX, QWORD PTR [RSP + 0x30]
        s.r.rbx = s.memory.readQword(s.r.rsp + 0x30L);

        // 425685E: MOV RBP, QWORD PTR [RSP + 0x38]
        s.r.rbp = s.memory.readQword(s.r.rsp + 0x38L);

        // 4256863: MOV RSI, QWORD PTR [RSP + 0x40]
        s.r.rsi = s.memory.readQword(s.r.rsp + 0x40L);

        // 4256868: ADD RSP, 0x20
        s.r.rsp += 0x20L;

        // 425686C: POP RDI
        s.r.rdi = s.memory.readQword(s.r.rsp);
        s.r.rsp += 8L;

        // Construct actual 185.Tail at 425686D with DIRECT_RVA target 424E364
        // Entry is the actual full restored state after local epilogue reads.
        GovernmentCrtBoundary185Api.Tail transfer = new GovernmentCrtBoundary185Api.Tail(
            0x425686DL,
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
            0x424E364L,
            new GovernmentCrtBoundary185Api.Entry(
                s.image,
                s.r.rsp,
                s.r.volatileBits(),
                s.r.nonvolatileBits()
            )
        );

        B374Fp270Api.TailFrame frame = new B374Fp270Api.TailFrame(transfer, s.df, s.fp);

        QueueFp604Api.Outcome outcome = Objects.requireNonNull(s.calls.tail(frame));

        if (outcome instanceof QueueFp604Api.Normal normal) {
            frame.checkNormalReturn(normal);
        }

        return outcome;
    }

    /** Mechanical owned CALL only; no lower algorithm or default callee state. */
    private static void invoke(State s, long site, long target) {
        long beforeRsp = s.r.rsp;
        GovernmentCrtBoundary185Api.Call original = new GovernmentCrtBoundary185Api.Call(
            site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, target, beforeRsp,
            s.r.volatileBits(), s.r.nonvolatileBits());
        GovernmentCrtBoundary185Api.Entry child = new GovernmentCrtBoundary185Api.Entry(
            s.image, beforeRsp - 8L, original.volatileBits(), original.nonvolatileBits());
        B374Fp270Api.CallFrame frame = new B374Fp270Api.CallFrame(original, child, s.df, s.fp);
        s.memory.writeQword(child.rspBits(), frame.returnRipBits());
        s.r.rsp = child.rspBits();
        QueueFp604Api.Outcome outcome = Objects.requireNonNull(s.calls.invoke(frame));
        if (outcome instanceof QueueFp604Api.Stopped stopped) {
            throw new StoppedSignal(stopped);
        }
        QueueFp604Api.Normal normal = (QueueFp604Api.Normal) outcome;
        frame.checkNormalReturn(normal);
        s.r.apply(normal.base().normalReturn().volatileBits());
        // All represented N bits were checked equal to the actual pre-call snapshot.
        s.r.rsp = normal.base().normalReturn().callerRspBits();
        s.df = normal.base().postDirectionFlagSet();
        s.fp = normal.postMxcsr();
    }

    private static final class State {
        final long image;
        final FullCopy437Api.Memory memory;
        final B374Fp270Api.Calls calls;
        final GovernmentPrimaryTail155Api.Registers r;
        boolean df;
        QueueFp604Api.Mxcsr fp;

        State(QueueFp604Api.Input input, FullCopy437Api.Memory memory, B374Fp270Api.Calls calls) {
            GovernmentCrtBoundary185Api.Entry e = input.base().entry();
            image = e.imageBaseBits();
            this.memory = memory;
            this.calls = calls;
            r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                image, e.rspBits(), e.volatileBits(), e.nonvolatileBits()));
            df = input.base().directionFlagSet();
            fp = input.mxcsr();
        }
    }

    private static final class StoppedSignal extends RuntimeException {
        private static final long serialVersionUID = 1L;
        final transient QueueFp604Api.Stopped outcome;

        StoppedSignal(QueueFp604Api.Stopped outcome) {
            super(null, null, false, false);
            this.outcome = outcome;
        }
    }
}
