package org.xar.ck3.study.m6.activity266;

import java.util.Objects;
import java.util.function.LongConsumer;
import java.util.function.LongSupplier;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.activityprotocol264.ActivityCallProtocol264Api;
import org.xar.ck3.study.m6.activityprotocol264.ActivityCallProtocol264Api.FullOutcomePort;
import org.xar.ck3.study.m6.activity265.ActivityWordBlock265;

/**
 * SOURCE-ONLY, UNCOMPILED whole normal represented producer for RF [23FC970,23FDC67).
 * Exact 1093 supplied normal instructions; trailing CC at 23FDC66 and EH are outside
 * this normal graph. All 126 callees stay explicit whole-Outcome opaque ports.
 * No Game access, scalar adapter, prefix replay, absent architectural state defaults,
 * rollback, native extra push, or assumption that a child preserves DF/MXCSR.
 */
public final class ActivityEntry266 implements ActivityCallProtocol264Api.WholeActivityEntry {
    private final FullOutcomePort opaqueCalls;
    private final LongSupplier gsQword58;
    private final LongConsumer beforeBackwardEdgeTarget;

    /** Explicit source ports only. Budget receives the actual taken backward target RVA. */
    public ActivityEntry266(FullOutcomePort opaqueCalls, LongSupplier gsQword58,
            LongConsumer beforeBackwardEdgeTarget) {
        this.opaqueCalls = Objects.requireNonNull(opaqueCalls);
        this.gsQword58 = Objects.requireNonNull(gsQword58);
        this.beforeBackwardEdgeTarget = Objects.requireNonNull(beforeBackwardEdgeTarget);
    }

    @Override public QueueFp604Api.Outcome execute(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory sameMemory) {
        State s = new State(Objects.requireNonNull(input), Objects.requireNonNull(sameMemory),
                opaqueCalls, gsQword58, beforeBackwardEdgeTarget);
        while (s.outcome == null) {
            if (s.pc < 0x23FCE6A) s.pc = group0(s);
            else if (s.pc < 0x23FD31F) s.pc = group1(s);
            else if (s.pc < 0x23FD854) s.pc = group2(s);
            else s.pc = group3(s);
        }
        return s.outcome;
    }

    private static final class State {
        final long image;
        final Registers r;
        final PostState240Api.Context context;
        final GovernmentCrtBoundary185Api.Memory memory;
        final ActivityCallProtocol264Api.Binding binding;
        final FullOutcomePort opaqueCalls;
        final LongSupplier gsQword58;
        final LongConsumer beforeBackwardEdgeTarget;
        final Flags flags = new Flags();
        int pc = 0x23FC970;
        QueueFp604Api.Outcome outcome;

        State(PostState240Api.Input input, GovernmentCrtBoundary185Api.Memory memory,
                FullOutcomePort opaqueCalls, LongSupplier gsQword58, LongConsumer budget) {
            var e = input.entry(); var n = e.nonvolatileBits();
            image = e.imageBaseBits(); this.memory = memory;
            // The actual155 constructor narrows TLS/R12 by its old tail role; immediately
            // restore actual whole R12/RBX before the first source instruction or port.
            r = new Registers(new GovernmentPrimaryTail155Api.Entry(image, n.rdiBits(),
                    (int)n.r12Bits(), n.rsiBits(), n.r15Bits(), n.rbpBits(), e.rspBits(),
                    n.r13Bits(), n.r14Bits(), n.xmm6(), e.volatileBits()));
            r.rbx = n.rbxBits(); r.r12 = n.r12Bits();
            if (!r.volatileBits().equals(e.volatileBits()) || !r.nonvolatileBits().equals(n)
                    || r.rsp != e.rspBits())
                throw new IllegalStateException("Actual entry register copy mismatch");
            context = new PostState240Api.Context(image, r, input.directionFlagSet(), input.mxcsr(),
                    pc, input.originCallSiteRva());
            binding = new ActivityCallProtocol264Api.Binding(image, r, context, memory);
            this.opaqueCalls = opaqueCalls; this.gsQword58 = gsQword58;
            beforeBackwardEdgeTarget = budget;
        }
        int transfer(int target) {
            if (target <= pc) beforeBackwardEdgeTarget.accept(Integer.toUnsignedLong(target));
            return target;
        }
    }

    /** Only CF/ZF/SF/OF are read by this source. Unknown input/child flags stay UNKNOWN. */
    private static final class Flags {
        private static final int CF=1, ZF=2, SF=4, OF=8;
        private int known;
        private boolean carry, zero, sign, overflow;
        void invalidate() { known = 0; }
        private boolean require(int flag, boolean value, int pc) {
            if ((known & flag) == 0) throw new UnsupportedOperationException(
                    "Unrepresented/undefined flag " + flag + " read at source RVA " + Integer.toHexString(pc));
            return value;
        }
        boolean cf(int pc) { return require(CF, carry, pc); }
        boolean zf(int pc) { return require(ZF, zero, pc); }
        boolean sf(int pc) { return require(SF, sign, pc); }
        boolean of(int pc) { return require(OF, overflow, pc); }
        private static long mask(int width) { return width == 64 ? -1L : (1L << width) - 1L; }
        void arithmetic(long left, long right, long result, int width, boolean subtract) {
            long m = mask(width), a = left & m, b = right & m, v = result & m;
            long high = 1L << (width - 1);
            carry = subtract ? Long.compareUnsigned(a, b) < 0
                    : width == 64 ? Long.compareUnsigned(v, a) < 0 : a + b > m;
            overflow = subtract ? ((a ^ b) & (a ^ v) & high) != 0
                    : (~(a ^ b) & (a ^ v) & high) != 0;
            zero = v == 0; sign = (v & high) != 0; known = CF | ZF | SF | OF;
        }
        void logic(long result, int width) {
            long v = result & mask(width);
            carry = false; overflow = false; zero = v == 0;
            sign = (v & (1L << (width - 1))) != 0; known = CF | ZF | SF | OF;
        }
        void increment(long left, long result, int width) {
            boolean oldCarry = carry; int carryKnown = known & CF;
            arithmetic(left, 1L, result, width, false);
            carry = oldCarry; known = (known & ~CF) | carryKnown;
        }
        void shiftLeft(long left, long result, int width, int count) {
            carry = ((left >>> (width - count)) & 1L) != 0;
            long v = result & mask(width); zero = v == 0;
            sign = (v & (1L << (width - 1))) != 0;
            known = CF | ZF | SF; // All actual source counts are >1: OF remains undefined.
        }
        void multiplySigned(long left, long right, long result) {
            carry = Math.multiplyHigh(left, right) != (result >> 63);
            overflow = carry; known = CF | OF;
        }
        void bitTest(boolean actualBit) { carry = actualBit; known = CF; }
    }

    private static int group0(State s) {
        switch (s.pc) {
            case 0x23FC970: {
                {
                // 0x23fc970 48895c2410 mov qword ptr [rsp + 0x10], rbx
                s.pc = 0x23FC970; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x10), s.r.rbx);
                }
                {
                // 0x23fc975 55 push rbp
                s.pc = 0x23FC975; s.context.beforeInstruction(s.pc);
                long value = s.r.rbp;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc976 56 push rsi
                s.pc = 0x23FC976; s.context.beforeInstruction(s.pc);
                long value = s.r.rsi;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc977 57 push rdi
                s.pc = 0x23FC977; s.context.beforeInstruction(s.pc);
                long value = s.r.rdi;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc978 4154 push r12
                s.pc = 0x23FC978; s.context.beforeInstruction(s.pc);
                long value = s.r.r12;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc97a 4155 push r13
                s.pc = 0x23FC97A; s.context.beforeInstruction(s.pc);
                long value = s.r.r13;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc97c 4156 push r14
                s.pc = 0x23FC97C; s.context.beforeInstruction(s.pc);
                long value = s.r.r14;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc97e 4157 push r15
                s.pc = 0x23FC97E; s.context.beforeInstruction(s.pc);
                long value = s.r.r15;
                s.r.rsp -= 8L;
                s.memory.writeQword(s.r.rsp, value);
                }
                {
                // 0x23fc980 488dac2450faffff lea rbp, [rsp - 0x5b0]
                s.pc = 0x23FC980; s.context.beforeInstruction(s.pc);
                s.r.rbp = (s.r.rsp - 0x5b0);
                }
                {
                // 0x23fc988 4881ecb0060000 sub rsp, 0x6b0
                s.pc = 0x23FC988; s.context.beforeInstruction(s.pc);
                long left = s.r.rsp;
                long right = 0x6B0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                s.r.rsp = result;
                }
                {
                // 0x23fc98f 488bf2 mov rsi, rdx
                s.pc = 0x23FC98F; s.context.beforeInstruction(s.pc);
                s.r.rsi = s.r.rdx;
                }
                {
                // 0x23fc992 4c8bf1 mov r14, rcx
                s.pc = 0x23FC992; s.context.beforeInstruction(s.pc);
                s.r.r14 = s.r.rcx;
                }
                {
                // 0x23fc995 33db xor ebx, ebx
                s.pc = 0x23FC995; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fc997 448beb mov r13d, ebx
                s.pc = 0x23FC997; s.context.beforeInstruction(s.pc);
                s.r.r13 = ((s.r.rbx & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fc99a 899d00060000 mov dword ptr [rbp + 0x600], ebx
                s.pc = 0x23FC99A; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x600), (int)((s.r.rbx & 0xFFFFFFFFL)));
                }
                {
                // 0x23fc9a0 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FC9A0; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fc9a3 8178384f624447 cmp dword ptr [rax + 0x38], 0x4744624f
                s.pc = 0x23FC9A3; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 0x38)));
                long right = 0x4744624FL;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fc9aa 0f84d9000000 je 0x23fca89
                s.pc = 0x23FC9AA; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCA89 : 0x23FC9B0);
                }
            }
            case 0x23FC9B0: {
                {
                // 0x23fc9b0 4885d2 test rdx, rdx
                s.pc = 0x23FC9B0; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.rdx;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fc9b3 0f844c120000 je 0x23fdc05
                s.pc = 0x23FC9B3; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDC05 : 0x23FC9B9);
                }
            }
            case 0x23FC9B9: {
                {
                // 0x23fc9b9 488d0578060902 lea rax, [rip + 0x2090678]
                s.pc = 0x23FC9B9; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fc9c0 4889442470 mov qword ptr [rsp + 0x70], rax
                s.pc = 0x23FC9C0; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x70), s.r.rax);
                }
                {
                // 0x23fc9c5 41bc01000000 mov r12d, 1
                s.pc = 0x23FC9C5; s.context.beforeInstruction(s.pc);
                s.r.r12 = (0x1L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fc9cb 4489642478 mov dword ptr [rsp + 0x78], r12d
                s.pc = 0x23FC9CB; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x78), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fc9d0 885c247c mov byte ptr [rsp + 0x7c], bl
                s.pc = 0x23FC9D0; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x7c), (int)((s.r.rbx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fc9d4 488d542470 lea rdx, [rsp + 0x70]
                s.pc = 0x23FC9D4; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x70);
                }
                {
                // 0x23fc9d9 488bce mov rcx, rsi
                s.pc = 0x23FC9D9; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fc9dc e87fa7b501 call 0x3f57160
                s.pc = 0x23FC9DC; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fc9e1 488d05f0063302 lea rax, [rip + 0x23306f0]
                s.pc = 0x23FC9E1; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472D0D8L);
                }
                {
                // 0x23fc9e8 4889442470 mov qword ptr [rsp + 0x70], rax
                s.pc = 0x23FC9E8; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x70), s.r.rax);
                }
                {
                // 0x23fc9ed c744247815000000 mov dword ptr [rsp + 0x78], 0x15
                s.pc = 0x23FC9ED; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x78), (int)(0x15L));
                }
                {
                // 0x23fc9f5 885c247c mov byte ptr [rsp + 0x7c], bl
                s.pc = 0x23FC9F5; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x7c), (int)((s.r.rbx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fc9f9 33d2 xor edx, edx
                s.pc = 0x23FC9F9; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fc9fb 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FC9FB; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca01 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCA01; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fca05 e806a5e201 call 0x4226f10
                s.pc = 0x23FCA05; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca0a 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCA0A; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fca0e e8cdcf48fe call 0x8899e0
                s.pc = 0x23FCA0E; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca13 90 nop
                s.pc = 0x23FCA13; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fca14 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FCA14; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fca19 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FCA19; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fca1d 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FCA1D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fca22 4533c9 xor r9d, r9d
                s.pc = 0x23FCA22; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca25 4533c0 xor r8d, r8d
                s.pc = 0x23FCA25; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca28 488d542470 lea rdx, [rsp + 0x70]
                s.pc = 0x23FCA28; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x70);
                }
                {
                // 0x23fca2d 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCA2D; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fca32 e8e99ba101 call 0x3e16620
                s.pc = 0x23FCA32; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca37 90 nop
                s.pc = 0x23FCA37; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fca38 48395d60 cmp qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCA38; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fca3c 7422 je 0x23fca60
                s.pc = 0x23FCA3C; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCA60 : 0x23FCA3E);
                }
            }
            case 0x23FCA3E: {
                {
                // 0x23fca3e 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCA3E; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fca42 e889d048fe call 0x889ad0
                s.pc = 0x23FCA42; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca47 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FCA47; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fca4b 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FCA4B; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fca4e 448d4308 lea r8d, [rbx + 8]
                s.pc = 0x23FCA4E; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx + 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca52 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FCA52; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fca56 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FCA56; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca59 48895d60 mov qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCA59; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rbx);
                }
                {
                // 0x23fca5d 895d68 mov dword ptr [rbp + 0x68], ebx
                s.pc = 0x23FCA5D; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FCA60);
                }
            }
            case 0x23FCA60: {
                {
                // 0x23fca60 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FCA60; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fca65 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FCA65; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fca6b 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FCA6B; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fca71 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FCA71; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fca76 488bce mov rcx, rsi
                s.pc = 0x23FCA76; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fca79 e8529548fe call 0x885fd0
                s.pc = 0x23FCA79; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fca7e 90 nop
                s.pc = 0x23FCA7E; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fca7f 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCA7F; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fca84 e977110000 jmp 0x23fdc00
                s.pc = 0x23FCA84; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDC00);
                }
            }
            case 0x23FCA89: {
                {
                // 0x23fca89 488b15d8aa8603 mov rdx, qword ptr [rip + 0x386aad8]
                s.pc = 0x23FCA89; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.image + 0x5C67568L));
                }
                {
                // 0x23fca90 4885d2 test rdx, rdx
                s.pc = 0x23FCA90; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.rdx;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fca93 7432 je 0x23fcac7
                s.pc = 0x23FCA93; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCAC7 : 0x23FCA95);
                }
            }
            case 0x23FCA95: {
                {
                // 0x23fca95 448b4108 mov r8d, dword ptr [rcx + 8]
                s.pc = 0x23FCA95; s.context.beforeInstruction(s.pc);
                s.r.r8 = (Integer.toUnsignedLong(s.memory.readDword((s.r.rcx + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca99 418bc0 mov eax, r8d
                s.pc = 0x23FCA99; s.context.beforeInstruction(s.pc);
                s.r.rax = ((s.r.r8 & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fca9c 25ffffff00 and eax, 0xffffff
                s.pc = 0x23FCA9C; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = 0xFFFFFFL;
                long result = left & right;
                s.flags.logic(result, 32);
                s.r.rax = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcaa1 3b422c cmp eax, dword ptr [rdx + 0x2c]
                s.pc = 0x23FCAA1; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = Integer.toUnsignedLong(s.memory.readDword((s.r.rdx + 0x2c)));
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcaa4 7321 jae 0x23fcac7
                s.pc = 0x23FCAA4; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.cf(s.pc)) ? 0x23FCAC7 : 0x23FCAA6);
                }
            }
            case 0x23FCAA6: {
                {
                // 0x23fcaa6 8bc8 mov ecx, eax
                s.pc = 0x23FCAA6; s.context.beforeInstruction(s.pc);
                s.r.rcx = ((s.r.rax & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcaa8 4803c9 add rcx, rcx
                s.pc = 0x23FCAA8; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rcx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fcaab 488b4220 mov rax, qword ptr [rdx + 0x20]
                s.pc = 0x23FCAAB; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rdx + 0x20));
                }
                {
                // 0x23fcaaf 4c8b64c808 mov r12, qword ptr [rax + rcx*8 + 8]
                s.pc = 0x23FCAAF; s.context.beforeInstruction(s.pc);
                s.r.r12 = s.memory.readQword((s.r.rax + s.r.rcx*8 + 8));
                }
                {
                // 0x23fcab4 4c89a508060000 mov qword ptr [rbp + 0x608], r12
                s.pc = 0x23FCAB4; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x608), s.r.r12);
                }
                {
                // 0x23fcabb 4d85e4 test r12, r12
                s.pc = 0x23FCABB; s.context.beforeInstruction(s.pc);
                long left = s.r.r12;
                long right = s.r.r12;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fcabe 7407 je 0x23fcac7
                s.pc = 0x23FCABE; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCAC7 : 0x23FCAC0);
                }
            }
            case 0x23FCAC0: {
                {
                // 0x23fcac0 4539442418 cmp dword ptr [r12 + 0x18], r8d
                s.pc = 0x23FCAC0; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.r12 + 0x18)));
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcac5 740e je 0x23fcad5
                s.pc = 0x23FCAC5; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCAD5 : 0x23FCAC7);
                }
            }
            case 0x23FCAC7: {
                {
                // 0x23fcac7 4c8b25a2aa8603 mov r12, qword ptr [rip + 0x386aaa2]
                s.pc = 0x23FCAC7; s.context.beforeInstruction(s.pc);
                s.r.r12 = s.memory.readQword((s.image + 0x5C67570L));
                }
                {
                // 0x23fcace 4c89a508060000 mov qword ptr [rbp + 0x608], r12
                s.pc = 0x23FCACE; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x608), s.r.r12);
                return s.transfer(0x23FCAD5);
                }
            }
            case 0x23FCAD5: {
                {
                // 0x23fcad5 41817c241c72616843 cmp dword ptr [r12 + 0x1c], 0x43686172
                s.pc = 0x23FCAD5; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.r12 + 0x1c)));
                long right = 0x43686172L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcade 0f8539100000 jne 0x23fdb1d
                s.pc = 0x23FCADE; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FDB1D : 0x23FCAE4);
                }
            }
            case 0x23FCAE4: {
                {
                // 0x23fcae4 41837c2418ff cmp dword ptr [r12 + 0x18], -1
                s.pc = 0x23FCAE4; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.r12 + 0x18)));
                long right = -0x1L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcaea 0f842d100000 je 0x23fdb1d
                s.pc = 0x23FCAEA; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB1D : 0x23FCAF0);
                }
            }
            case 0x23FCAF0: {
                {
                // 0x23fcaf0 49399c24d0010000 cmp qword ptr [r12 + 0x1d0], rbx
                s.pc = 0x23FCAF0; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.r12 + 0x1d0));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcaf8 0f851f100000 jne 0x23fdb1d
                s.pc = 0x23FCAF8; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FDB1D : 0x23FCAFE);
                }
            }
            case 0x23FCAFE: {
                {
                // 0x23fcafe 498bce mov rcx, r14
                s.pc = 0x23FCAFE; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.r14;
                }
                {
                // 0x23fcb01 e8dafcffff call 0x23fc7e0
                s.pc = 0x23FCB01; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcb06 4c8bf8 mov r15, rax
                s.pc = 0x23FCB06; s.context.beforeInstruction(s.pc);
                s.r.r15 = s.r.rax;
                }
                {
                // 0x23fcb09 4889442470 mov qword ptr [rsp + 0x70], rax
                s.pc = 0x23FCB09; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x70), s.r.rax);
                }
                {
                // 0x23fcb0e 418b4e08 mov ecx, dword ptr [r14 + 8]
                s.pc = 0x23FCB0E; s.context.beforeInstruction(s.pc);
                s.r.rcx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb12 898df0050000 mov dword ptr [rbp + 0x5f0], ecx
                s.pc = 0x23FCB12; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x5f0), (int)((s.r.rcx & 0xFFFFFFFFL)));
                }
                {
                // 0x23fcb18 488d95f0050000 lea rdx, [rbp + 0x5f0]
                s.pc = 0x23FCB18; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x5f0);
                }
                {
                // 0x23fcb1f 488d8d40040000 lea rcx, [rbp + 0x440]
                s.pc = 0x23FCB1F; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x440);
                }
                {
                // 0x23fcb26 e8f5d25ffe call 0x9f9e20
                s.pc = 0x23FCB26; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcb2b 4d85ff test r15, r15
                s.pc = 0x23FCB2B; s.context.beforeInstruction(s.pc);
                long left = s.r.r15;
                long right = s.r.r15;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fcb2e 742e je 0x23fcb5e
                s.pc = 0x23FCB2E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCB5E : 0x23FCB30);
                }
            }
            case 0x23FCB30: {
                {
                // 0x23fcb30 418b4f08 mov ecx, dword ptr [r15 + 8]
                s.pc = 0x23FCB30; s.context.beforeInstruction(s.pc);
                s.r.rcx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r15 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb34 81e1ffffff00 and ecx, 0xffffff
                s.pc = 0x23FCB34; s.context.beforeInstruction(s.pc);
                long left = (s.r.rcx & 0xFFFFFFFFL);
                long right = 0xFFFFFFL;
                long result = left & right;
                s.flags.logic(result, 32);
                s.r.rcx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb3a c744246003000000 mov dword ptr [rsp + 0x60], 3
                s.pc = 0x23FCB3A; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x60), (int)(0x3L));
                }
                {
                // 0x23fcb42 48894c2468 mov qword ptr [rsp + 0x68], rcx
                s.pc = 0x23FCB42; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x68), s.r.rcx);
                }
                {
                // 0x23fcb47 4c8d442460 lea r8, [rsp + 0x60]
                s.pc = 0x23FCB47; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.r.rsp + 0x60);
                }
                {
                // 0x23fcb4c 8b1566f59403 mov edx, dword ptr [rip + 0x394f566]
                s.pc = 0x23FCB4C; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5D4C0B8L)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb52 488d8d58040000 lea rcx, [rbp + 0x458]
                s.pc = 0x23FCB52; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x458);
                }
                {
                // 0x23fcb59 e892d53301 call 0x373a0f0
                s.pc = 0x23FCB59; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FCB5E);
                }
            }
            case 0x23FCB5E: {
                {
                // 0x23fcb5e 498b9630050000 mov rdx, qword ptr [r14 + 0x530]
                s.pc = 0x23FCB5E; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.r14 + 0x530));
                }
                {
                // 0x23fcb65 488bda mov rbx, rdx
                s.pc = 0x23FCB65; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.r.rdx;
                }
                {
                // 0x23fcb68 44386a04 cmp byte ptr [rdx + 4], r13b
                s.pc = 0x23FCB68; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rdx + 4)) & 0xFFL);
                long right = (s.r.r13 & 0xFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fcb6c 750c jne 0x23fcb7a
                s.pc = 0x23FCB6C; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FCB7A : 0x23FCB6E);
                }
            }
            case 0x23FCB6E: {
                {
                // 0x23fcb6e 6690 nop
                s.pc = 0x23FCB6E; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FCB70);
                }
            }
            case 0x23FCB70: {
                {
                // 0x23fcb70 4883c320 add rbx, 0x20
                s.pc = 0x23FCB70; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x20L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fcb74 44386b04 cmp byte ptr [rbx + 4], r13b
                s.pc = 0x23FCB74; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rbx + 4)) & 0xFFL);
                long right = (s.r.r13 & 0xFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fcb78 74f6 je 0x23fcb70
                s.pc = 0x23FCB78; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCB70 : 0x23FCB7A);
                }
            }
            case 0x23FCB7A: {
                {
                // 0x23fcb7a 410fb68e40050000 movzx ecx, byte ptr [r14 + 0x540]
                s.pc = 0x23FCB7A; s.context.beforeInstruction(s.pc);
                s.r.rcx = ((s.memory.readUnsignedByte((s.r.r14 + 0x540)) & 0xFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb82 ffc1 inc ecx
                s.pc = 0x23FCB82; s.context.beforeInstruction(s.pc);
                long left = (s.r.rcx & 0xFFFFFFFFL);
                long result = left + 1L;
                s.flags.increment(left, result, 32);
                s.r.rcx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb84 41038e3c050000 add ecx, dword ptr [r14 + 0x53c]
                s.pc = 0x23FCB84; s.context.beforeInstruction(s.pc);
                long left = (s.r.rcx & 0xFFFFFFFFL);
                long right = Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x53c)));
                long result = left + right;
                s.flags.arithmetic(left, right, result, 32, false);
                s.r.rcx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcb8b 4863f9 movsxd rdi, ecx
                s.pc = 0x23FCB8B; s.context.beforeInstruction(s.pc);
                s.r.rdi = (long)(int)((s.r.rcx & 0xFFFFFFFFL));
                }
                {
                // 0x23fcb8e 48c1e705 shl rdi, 5
                s.pc = 0x23FCB8E; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long result = left << 5;
                s.flags.shiftLeft(left, result, 64, 5);
                s.r.rdi = result;
                }
                {
                // 0x23fcb92 4803fa add rdi, rdx
                s.pc = 0x23FCB92; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = s.r.rdx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fcb95 483bdf cmp rbx, rdi
                s.pc = 0x23FCB95; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcb98 7428 je 0x23fcbc2
                s.pc = 0x23FCB98; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCBC2 : 0x23FCB9A);
                }
            }
            case 0x23FCB9A: {
                {
                // 0x23fcb9a 660f1f440000 nop word ptr [rax + rax]
                s.pc = 0x23FCB9A; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FCBA0);
                }
            }
            case 0x23FCBA0: {
                {
                // 0x23fcba0 4c8d4310 lea r8, [rbx + 0x10]
                s.pc = 0x23FCBA0; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.r.rbx + 0x10);
                }
                {
                // 0x23fcba4 8b5308 mov edx, dword ptr [rbx + 8]
                s.pc = 0x23FCBA4; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.rbx + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcba7 488d8d58040000 lea rcx, [rbp + 0x458]
                s.pc = 0x23FCBA7; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x458);
                }
                {
                // 0x23fcbae e83dd53301 call 0x373a0f0
                s.pc = 0x23FCBAE; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FCBB3);
                }
            }
            case 0x23FCBB3: {
                {
                // 0x23fcbb3 4883c320 add rbx, 0x20
                s.pc = 0x23FCBB3; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x20L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fcbb7 44386b04 cmp byte ptr [rbx + 4], r13b
                s.pc = 0x23FCBB7; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rbx + 4)) & 0xFFL);
                long right = (s.r.r13 & 0xFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fcbbb 74f6 je 0x23fcbb3
                s.pc = 0x23FCBBB; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCBB3 : 0x23FCBBD);
                }
            }
            case 0x23FCBBD: {
                {
                // 0x23fcbbd 483bdf cmp rbx, rdi
                s.pc = 0x23FCBBD; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcbc0 75de jne 0x23fcba0
                s.pc = 0x23FCBC0; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FCBA0 : 0x23FCBC2);
                }
            }
            case 0x23FCBC2: {
                {
                // 0x23fcbc2 41b101 mov r9b, 1
                s.pc = 0x23FCBC2; s.context.beforeInstruction(s.pc);
                s.r.r9 = (s.r.r9 & ~0xFFL) | ((0x1L) & 0xFFL);
                }
                {
                // 0x23fcbc5 4c8bc6 mov r8, rsi
                s.pc = 0x23FCBC5; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rsi;
                }
                {
                // 0x23fcbc8 488d9540040000 lea rdx, [rbp + 0x440]
                s.pc = 0x23FCBC8; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x440);
                }
                {
                // 0x23fcbcf 498b0e mov rcx, qword ptr [r14]
                s.pc = 0x23FCBCF; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fcbd2 e8890d7c00 call 0x2bbd960
                s.pc = 0x23FCBD2; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcbd7 84c0 test al, al
                s.pc = 0x23FCBD7; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fcbd9 0f84260f0000 je 0x23fdb05
                s.pc = 0x23FCBD9; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCBDF);
                }
            }
            case 0x23FCBDF: {
                {
                // 0x23fcbdf 488b0512bc8b03 mov rax, qword ptr [rip + 0x38bbc12]
                s.pc = 0x23FCBDF; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.image + 0x5CB87F8L));
                }
                {
                // 0x23fcbe6 8b80b0020000 mov eax, dword ptr [rax + 0x2b0]
                s.pc = 0x23FCBE6; s.context.beforeInstruction(s.pc);
                s.r.rax = (Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 0x2b0)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcbec 498d5e10 lea rbx, [r14 + 0x10]
                s.pc = 0x23FCBEC; s.context.beforeInstruction(s.pc);
                s.r.rbx = (s.r.r14 + 0x10);
                }
                {
                // 0x23fcbf0 480fbae00b bt rax, 0xb
                s.pc = 0x23FCBF0; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                s.flags.bitTest((left & (1L << 11)) != 0);
                }
                {
                // 0x23fcbf5 0f82be000000 jb 0x23fccb9
                s.pc = 0x23FCBF5; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.cf(s.pc)) ? 0x23FCCB9 : 0x23FCBFB);
                }
            }
            case 0x23FCBFB: {
                {
                // 0x23fcbfb 4d8bc7 mov r8, r15
                s.pc = 0x23FCBFB; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.r15;
                }
                {
                // 0x23fcbfe 418b5608 mov edx, dword ptr [r14 + 8]
                s.pc = 0x23FCBFE; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc02 498b0e mov rcx, qword ptr [r14]
                s.pc = 0x23FCC02; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fcc05 e82678d100 call 0x3114430
                s.pc = 0x23FCC05; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcc0a 483903 cmp qword ptr [rbx], rax
                s.pc = 0x23FCC0A; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbx));
                long right = s.r.rax;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcc0d 0f84a6000000 je 0x23fccb9
                s.pc = 0x23FCC0D; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCCB9 : 0x23FCC13);
                }
            }
            case 0x23FCC13: {
                {
                // 0x23fcc13 b9ce370000 mov ecx, 0x37ce
                s.pc = 0x23FCC13; s.context.beforeInstruction(s.pc);
                s.r.rcx = (0x37CEL) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc18 e8c32cb501 call 0x3f4f8e0
                s.pc = 0x23FCC18; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcc1d 488bf0 mov rsi, rax
                s.pc = 0x23FCC1D; s.context.beforeInstruction(s.pc);
                s.r.rsi = s.r.rax;
                }
                {
                // 0x23fcc20 488b1b mov rbx, qword ptr [rbx]
                s.pc = 0x23FCC20; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.memory.readQword((s.r.rbx));
                }
                {
                // 0x23fcc23 4883c318 add rbx, 0x18
                s.pc = 0x23FCC23; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x18L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fcc27 498b3e mov rdi, qword ptr [r14]
                s.pc = 0x23FCC27; s.context.beforeInstruction(s.pc);
                s.r.rdi = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fcc2a 4883c718 add rdi, 0x18
                s.pc = 0x23FCC2A; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = 0x18L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fcc2e b858010000 mov eax, 0x158
                s.pc = 0x23FCC2E; s.context.beforeInstruction(s.pc);
                s.r.rax = (0x158L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc33 65488b0c2558000000 mov rcx, qword ptr gs:[0x58]
                s.pc = 0x23FCC33; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.gsQword58.getAsLong();
                }
                {
                // 0x23fcc3c 488b11 mov rdx, qword ptr [rcx]
                s.pc = 0x23FCC3C; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fcc3f 803c1000 cmp byte ptr [rax + rdx], 0
                s.pc = 0x23FCC3F; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rax + s.r.rdx)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fcc43 0f85bc0e0000 jne 0x23fdb05
                s.pc = 0x23FCC43; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCC49);
                }
            }
            case 0x23FCC49: {
                {
                // 0x23fcc49 8b0d8ddd8603 mov ecx, dword ptr [rip + 0x386dd8d]
                s.pc = 0x23FCC49; s.context.beforeInstruction(s.pc);
                s.r.rcx = (Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5C6A9DCL)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc4f 90 nop
                s.pc = 0x23FCC4F; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcc50 81f9a0860100 cmp ecx, 0x186a0
                s.pc = 0x23FCC50; s.context.beforeInstruction(s.pc);
                long left = (s.r.rcx & 0xFFFFFFFFL);
                long right = 0x186A0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcc56 0f8da90e0000 jge 0x23fdb05
                s.pc = 0x23FCC56; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.sf(s.pc) == s.flags.of(s.pc)) ? 0x23FDB05 : 0x23FCC5C);
                }
            }
            case 0x23FCC5C: {
                {
                // 0x23fcc5c b900000100 mov ecx, 0x10000
                s.pc = 0x23FCC5C; s.context.beforeInstruction(s.pc);
                s.r.rcx = (0x10000L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc61 e80a2db601 call 0x3f5f970
                s.pc = 0x23FCC61; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcc66 4885c0 test rax, rax
                s.pc = 0x23FCC66; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rax;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fcc69 0f84960e0000 je 0x23fdb05
                s.pc = 0x23FCC69; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCC6F);
                }
            }
            case 0x23FCC6F: {
                {
                // 0x23fcc6f 4889742438 mov qword ptr [rsp + 0x38], rsi
                s.pc = 0x23FCC6F; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x38), s.r.rsi);
                }
                {
                // 0x23fcc74 48895c2430 mov qword ptr [rsp + 0x30], rbx
                s.pc = 0x23FCC74; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x30), s.r.rbx);
                }
                {
                // 0x23fcc79 48897c2428 mov qword ptr [rsp + 0x28], rdi
                s.pc = 0x23FCC79; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rdi);
                }
                {
                // 0x23fcc7e 488d0d6b043302 lea rcx, [rip + 0x233046b]
                s.pc = 0x23FCC7E; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.image + 0x472D0F0L);
                }
                {
                // 0x23fcc85 48894c2420 mov qword ptr [rsp + 0x20], rcx
                s.pc = 0x23FCC85; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rcx);
                }
                {
                // 0x23fcc8a 41b904000000 mov r9d, 4
                s.pc = 0x23FCC8A; s.context.beforeInstruction(s.pc);
                s.r.r9 = (0x4L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc90 41b8460c0000 mov r8d, 0xc46
                s.pc = 0x23FCC90; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0xC46L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcc96 488d15c3fc3202 lea rdx, [rip + 0x232fcc3]
                s.pc = 0x23FCC96; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.image + 0x472C960L);
                }
                {
                // 0x23fcc9d 488bc8 mov rcx, rax
                s.pc = 0x23FCC9D; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rax;
                }
                {
                // 0x23fcca0 e8eb6f6bff call 0x1ab3c90
                s.pc = 0x23FCCA0; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcca5 41bc01000000 mov r12d, 1
                s.pc = 0x23FCCA5; s.context.beforeInstruction(s.pc);
                s.r.r12 = (0x1L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fccab f0440fc12528dd8603 lock xadd dword ptr [rip + 0x386dd28], r12d
                s.pc = 0x23FCCAB; s.context.beforeInstruction(s.pc);
                int addend = (int)((s.r.r12 & 0xFFFFFFFFL));
                int old = s.memory.lockedXaddDword((s.image + 0x5C6A9DCL), addend);
                long left = Integer.toUnsignedLong(old);
                long right = Integer.toUnsignedLong(addend);
                s.flags.arithmetic(left, right, left + right, 32, false);
                s.r.r12 = (Integer.toUnsignedLong(old)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fccb4 e94c0e0000 jmp 0x23fdb05
                s.pc = 0x23FCCB4; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDB05);
                }
            }
            case 0x23FCCB9: {
                {
                // 0x23fccb9 4c8bc6 mov r8, rsi
                s.pc = 0x23FCCB9; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rsi;
                }
                {
                // 0x23fccbc 418b5608 mov edx, dword ptr [r14 + 8]
                s.pc = 0x23FCCBC; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fccc0 488bcb mov rcx, rbx
                s.pc = 0x23FCCC0; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fccc3 e818d53b00 call 0x27ba1e0
                s.pc = 0x23FCCC3; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fccc8 84c0 test al, al
                s.pc = 0x23FCCC8; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fccca 0f84350e0000 je 0x23fdb05
                s.pc = 0x23FCCCA; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCCD0);
                }
            }
            case 0x23FCCD0: {
                {
                // 0x23fccd0 498b8424b0010000 mov rax, qword ptr [r12 + 0x1b0]
                s.pc = 0x23FCCD0; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.r12 + 0x1b0));
                }
                {
                // 0x23fccd8 4885c0 test rax, rax
                s.pc = 0x23FCCD8; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rax;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fccdb 0f8489010000 je 0x23fce6a
                s.pc = 0x23FCCDB; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCE6A : 0x23FCCE1);
                }
            }
            case 0x23FCCE1: {
                {
                // 0x23fcce1 4883b8f804000000 cmp qword ptr [rax + 0x4f8], 0
                s.pc = 0x23FCCE1; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rax + 0x4f8));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcce9 0f847b010000 je 0x23fce6a
                s.pc = 0x23FCCE9; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCE6A : 0x23FCCEF);
                }
            }
            case 0x23FCCEF: {
                {
                // 0x23fccef 4885f6 test rsi, rsi
                s.pc = 0x23FCCEF; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fccf2 0f840d0e0000 je 0x23fdb05
                s.pc = 0x23FCCF2; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCCF8);
                }
            }
            case 0x23FCCF8: {
                {
                // 0x23fccf8 488bce mov rcx, rsi
                s.pc = 0x23FCCF8; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fccfb e8c0455dfe call 0x9d12c0
                s.pc = 0x23FCCFB; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcd00 488d0529023302 lea rax, [rip + 0x2330229]
                s.pc = 0x23FCD00; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CF30L);
                }
                {
                // 0x23fcd07 4889442470 mov qword ptr [rsp + 0x70], rax
                s.pc = 0x23FCD07; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x70), s.r.rax);
                }
                {
                // 0x23fcd0c c744247829000000 mov dword ptr [rsp + 0x78], 0x29
                s.pc = 0x23FCD0C; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x78), (int)(0x29L));
                }
                {
                // 0x23fcd14 c644247c00 mov byte ptr [rsp + 0x7c], 0
                s.pc = 0x23FCD14; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x7c), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fcd19 488d3d80a445fe lea rdi, [rip - 0x1ba5b80]
                s.pc = 0x23FCD19; s.context.beforeInstruction(s.pc);
                s.r.rdi = (s.image + 0x8571A0L);
                }
                {
                // 0x23fcd20 48897c2420 mov qword ptr [rsp + 0x20], rdi
                s.pc = 0x23FCD20; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rdi);
                }
                {
                // 0x23fcd25 4c8d0d24a445fe lea r9, [rip - 0x1ba5bdc]
                s.pc = 0x23FCD25; s.context.beforeInstruction(s.pc);
                s.r.r9 = (s.image + 0x857150L);
                }
                {
                // 0x23fcd2c 41bc01000000 mov r12d, 1
                s.pc = 0x23FCD2C; s.context.beforeInstruction(s.pc);
                s.r.r12 = (0x1L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd32 458bc4 mov r8d, r12d
                s.pc = 0x23FCD32; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.r12 & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd35 418d542477 lea edx, [r12 + 0x77]
                s.pc = 0x23FCD35; s.context.beforeInstruction(s.pc);
                s.r.rdx = ((s.r.r12 + 0x77)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd3a 488d8d10020000 lea rcx, [rbp + 0x210]
                s.pc = 0x23FCD3A; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x210);
                }
                {
                // 0x23fcd41 e83272e201 call 0x4223f78
                s.pc = 0x23FCD41; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcd46 90 nop
                s.pc = 0x23FCD46; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcd47 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCD47; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcd4b e890cc48fe call 0x8899e0
                s.pc = 0x23FCD4B; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcd50 90 nop
                s.pc = 0x23FCD50; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcd51 488d05182d0a02 lea rax, [rip + 0x20a2d18]
                s.pc = 0x23FCD51; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x449FA70L);
                }
                {
                // 0x23fcd58 4889442460 mov qword ptr [rsp + 0x60], rax
                s.pc = 0x23FCD58; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.rax);
                }
                {
                // 0x23fcd5d c744246809000000 mov dword ptr [rsp + 0x68], 9
                s.pc = 0x23FCD5D; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)(0x9L));
                }
                {
                // 0x23fcd65 c644246c00 mov byte ptr [rsp + 0x6c], 0
                s.pc = 0x23FCD65; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fcd6a 33db xor ebx, ebx
                s.pc = 0x23FCD6A; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd6c 899d10020000 mov dword ptr [rbp + 0x210], ebx
                s.pc = 0x23FCD6C; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x210), (int)((s.r.rbx & 0xFFFFFFFFL)));
                }
                {
                // 0x23fcd72 ba10000000 mov edx, 0x10
                s.pc = 0x23FCD72; s.context.beforeInstruction(s.pc);
                s.r.rdx = (0x10L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd77 65488b042558000000 mov rax, qword ptr gs:[0x58]
                s.pc = 0x23FCD77; s.context.beforeInstruction(s.pc);
                s.r.rax = s.gsQword58.getAsLong();
                }
                {
                // 0x23fcd80 488b08 mov rcx, qword ptr [rax]
                s.pc = 0x23FCD80; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rax));
                }
                {
                // 0x23fcd83 8b040a mov eax, dword ptr [rdx + rcx]
                s.pc = 0x23FCD83; s.context.beforeInstruction(s.pc);
                s.r.rax = (Integer.toUnsignedLong(s.memory.readDword((s.r.rdx + s.r.rcx)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd86 390538aa8603 cmp dword ptr [rip + 0x386aa38], eax
                s.pc = 0x23FCD86; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5C677C4L)));
                long right = (s.r.rax & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcd8c 0f8f960e0000 jg 0x23fdc28
                s.pc = 0x23FCD8C; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc) && s.flags.sf(s.pc) == s.flags.of(s.pc)) ? 0x23FDC28 : 0x23FCD92);
                }
            }
            case 0x23FCD92: {
                {
                // 0x23fcd92 8b0530aa8603 mov eax, dword ptr [rip + 0x386aa30]
                s.pc = 0x23FCD92; s.context.beforeInstruction(s.pc);
                s.r.rax = (Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5C677C8L)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcd98 8985f0050000 mov dword ptr [rbp + 0x5f0], eax
                s.pc = 0x23FCD98; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x5f0), (int)((s.r.rax & 0xFFFFFFFFL)));
                }
                {
                // 0x23fcd9e 488b9508060000 mov rdx, qword ptr [rbp + 0x608]
                s.pc = 0x23FCD9E; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x608));
                }
                {
                // 0x23fcda5 48899508060000 mov qword ptr [rbp + 0x608], rdx
                s.pc = 0x23FCDA5; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x608), s.r.rdx);
                }
                {
                // 0x23fcdac 4c8d8df0050000 lea r9, [rbp + 0x5f0]
                s.pc = 0x23FCDAC; s.context.beforeInstruction(s.pc);
                s.r.r9 = (s.r.rbp + 0x5f0);
                }
                {
                // 0x23fcdb3 4c8d8508060000 lea r8, [rbp + 0x608]
                s.pc = 0x23FCDB3; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.r.rbp + 0x608);
                }
                {
                // 0x23fcdba 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FCDBA; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fcdbf 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCDBF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcdc3 e828bba101 call 0x3e188f0
                s.pc = 0x23FCDC3; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcdc8 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FCDC8; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fcdcd 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FCDCD; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcdd1 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FCDD1; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fcdd6 458bcc mov r9d, r12d
                s.pc = 0x23FCDD6; s.context.beforeInstruction(s.pc);
                s.r.r9 = ((s.r.r12 & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcdd9 4c8d8510020000 lea r8, [rbp + 0x210]
                s.pc = 0x23FCDD9; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.r.rbp + 0x210);
                }
                {
                // 0x23fcde0 488d542470 lea rdx, [rsp + 0x70]
                s.pc = 0x23FCDE0; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x70);
                }
                {
                // 0x23fcde5 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCDE5; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcdea e83198a101 call 0x3e16620
                s.pc = 0x23FCDEA; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcdef c7850006000008000000 mov dword ptr [rbp + 0x600], 8
                s.pc = 0x23FCDEF; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x600), (int)(0x8L));
                }
                {
                // 0x23fcdf9 48837d6000 cmp qword ptr [rbp + 0x60], 0
                s.pc = 0x23FCDF9; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcdfe 7424 je 0x23fce24
                s.pc = 0x23FCDFE; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCE24 : 0x23FCE00);
                }
            }
            case 0x23FCE00: {
                {
                // 0x23fce00 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCE00; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fce04 e8c7cc48fe call 0x889ad0
                s.pc = 0x23FCE04; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce09 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FCE09; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fce0d 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FCE0D; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fce10 41b808000000 mov r8d, 8
                s.pc = 0x23FCE10; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fce16 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FCE16; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fce1a ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FCE1A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce1d 48895d60 mov qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCE1D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rbx);
                }
                {
                // 0x23fce21 895d68 mov dword ptr [rbp + 0x68], ebx
                s.pc = 0x23FCE21; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FCE24);
                }
            }
            case 0x23FCE24: {
                {
                // 0x23fce24 4c8bcf mov r9, rdi
                s.pc = 0x23FCE24; s.context.beforeInstruction(s.pc);
                s.r.r9 = s.r.rdi;
                }
                {
                // 0x23fce27 4d8bc4 mov r8, r12
                s.pc = 0x23FCE27; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.r12;
                }
                {
                // 0x23fce2a ba78000000 mov edx, 0x78
                s.pc = 0x23FCE2A; s.context.beforeInstruction(s.pc);
                s.r.rdx = (0x78L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fce2f 488d8d10020000 lea rcx, [rbp + 0x210]
                s.pc = 0x23FCE2F; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x210);
                }
                {
                // 0x23fce36 e8e16de201 call 0x4223c1c
                s.pc = 0x23FCE36; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce3b 90 nop
                s.pc = 0x23FCE3B; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fce3c 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FCE3C; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fce41 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FCE41; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fce47 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FCE47; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fce4d 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FCE4D; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fce52 488bce mov rcx, rsi
                s.pc = 0x23FCE52; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fce55 e8769148fe call 0x885fd0
                s.pc = 0x23FCE55; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce5a 90 nop
                s.pc = 0x23FCE5A; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fce5b 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCE5B; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fce60 e8eb9145fe call 0x856050
                s.pc = 0x23FCE60; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce65 e99b0c0000 jmp 0x23fdb05
                s.pc = 0x23FCE65; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDB05);
                }
            }
            default: throw new UnsupportedOperationException("Not a normal activity source block: " + Integer.toHexString(s.pc));
        }
    }

    private static int group1(State s) {
        switch (s.pc) {
            case 0x23FCE6A: {
                {
                // 0x23fce6a 488b05dfbd8603 mov rax, qword ptr [rip + 0x386bddf]
                s.pc = 0x23FCE6A; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.image + 0x5C68C50L));
                }
                {
                // 0x23fce71 8b4808 mov ecx, dword ptr [rax + 8]
                s.pc = 0x23FCE71; s.context.beforeInstruction(s.pc);
                s.r.rcx = (Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fce74 41394e20 cmp dword ptr [r14 + 0x20], ecx
                s.pc = 0x23FCE74; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x20)));
                long right = (s.r.rcx & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fce78 0f8dc1000000 jge 0x23fcf3f
                s.pc = 0x23FCE78; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.sf(s.pc) == s.flags.of(s.pc)) ? 0x23FCF3F : 0x23FCE7E);
                }
            }
            case 0x23FCE7E: {
                {
                // 0x23fce7e 4885f6 test rsi, rsi
                s.pc = 0x23FCE7E; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fce81 0f847e0c0000 je 0x23fdb05
                s.pc = 0x23FCE81; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCE87);
                }
            }
            case 0x23FCE87: {
                {
                // 0x23fce87 488bce mov rcx, rsi
                s.pc = 0x23FCE87; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fce8a e831445dfe call 0x9d12c0
                s.pc = 0x23FCE8A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fce8f 488d057a003302 lea rax, [rip + 0x233007a]
                s.pc = 0x23FCE8F; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CF10L);
                }
                {
                // 0x23fce96 4889442460 mov qword ptr [rsp + 0x60], rax
                s.pc = 0x23FCE96; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.rax);
                }
                {
                // 0x23fce9b c74424681c000000 mov dword ptr [rsp + 0x68], 0x1c
                s.pc = 0x23FCE9B; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)(0x1CL));
                }
                {
                // 0x23fcea3 c644246c00 mov byte ptr [rsp + 0x6c], 0
                s.pc = 0x23FCEA3; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fcea8 33d2 xor edx, edx
                s.pc = 0x23FCEA8; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fceaa 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FCEAA; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fceb0 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCEB0; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fceb4 e857a0e201 call 0x4226f10
                s.pc = 0x23FCEB4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fceb9 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCEB9; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcebd e81ecb48fe call 0x8899e0
                s.pc = 0x23FCEBD; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcec2 90 nop
                s.pc = 0x23FCEC2; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcec3 33db xor ebx, ebx
                s.pc = 0x23FCEC3; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcec5 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FCEC5; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fceca 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FCECA; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcece 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FCECE; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fced3 4533c9 xor r9d, r9d
                s.pc = 0x23FCED3; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fced6 4533c0 xor r8d, r8d
                s.pc = 0x23FCED6; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fced9 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FCED9; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fcede 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCEDE; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcee3 e83897a101 call 0x3e16620
                s.pc = 0x23FCEE3; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcee8 90 nop
                s.pc = 0x23FCEE8; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcee9 48395d60 cmp qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCEE9; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fceed 7422 je 0x23fcf11
                s.pc = 0x23FCEED; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCF11 : 0x23FCEEF);
                }
            }
            case 0x23FCEEF: {
                {
                // 0x23fceef 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCEEF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcef3 e8d8cb48fe call 0x889ad0
                s.pc = 0x23FCEF3; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcef8 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FCEF8; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fcefc 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FCEFC; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fceff 448d4308 lea r8d, [rbx + 8]
                s.pc = 0x23FCEFF; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx + 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcf03 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FCF03; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fcf07 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FCF07; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf0a 48895d60 mov qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCF0A; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rbx);
                }
                {
                // 0x23fcf0e 895d68 mov dword ptr [rbp + 0x68], ebx
                s.pc = 0x23FCF0E; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FCF11);
                }
            }
            case 0x23FCF11: {
                {
                // 0x23fcf11 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FCF11; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcf16 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FCF16; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcf1c 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FCF1C; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fcf22 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FCF22; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fcf27 488bce mov rcx, rsi
                s.pc = 0x23FCF27; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fcf2a e8a19048fe call 0x885fd0
                s.pc = 0x23FCF2A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf2f 90 nop
                s.pc = 0x23FCF2F; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcf30 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCF30; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcf35 e8169145fe call 0x856050
                s.pc = 0x23FCF35; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf3a e9c60b0000 jmp 0x23fdb05
                s.pc = 0x23FCF3A; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDB05);
                }
            }
            case 0x23FCF3F: {
                {
                // 0x23fcf3f 4183bebc00000000 cmp dword ptr [r14 + 0xbc], 0
                s.pc = 0x23FCF3F; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0xbc)));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fcf47 0f85c1000000 jne 0x23fd00e
                s.pc = 0x23FCF47; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD00E : 0x23FCF4D);
                }
            }
            case 0x23FCF4D: {
                {
                // 0x23fcf4d 4885f6 test rsi, rsi
                s.pc = 0x23FCF4D; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fcf50 0f84af0b0000 je 0x23fdb05
                s.pc = 0x23FCF50; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FCF56);
                }
            }
            case 0x23FCF56: {
                {
                // 0x23fcf56 488bce mov rcx, rsi
                s.pc = 0x23FCF56; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fcf59 e862435dfe call 0x9d12c0
                s.pc = 0x23FCF59; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf5e 488d0523003302 lea rax, [rip + 0x2330023]
                s.pc = 0x23FCF5E; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CF88L);
                }
                {
                // 0x23fcf65 4889442460 mov qword ptr [rsp + 0x60], rax
                s.pc = 0x23FCF65; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.rax);
                }
                {
                // 0x23fcf6a c744246822000000 mov dword ptr [rsp + 0x68], 0x22
                s.pc = 0x23FCF6A; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)(0x22L));
                }
                {
                // 0x23fcf72 c644246c00 mov byte ptr [rsp + 0x6c], 0
                s.pc = 0x23FCF72; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fcf77 33d2 xor edx, edx
                s.pc = 0x23FCF77; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcf79 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FCF79; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcf7f 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCF7F; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcf83 e8889fe201 call 0x4226f10
                s.pc = 0x23FCF83; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf88 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCF88; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcf8c e84fca48fe call 0x8899e0
                s.pc = 0x23FCF8C; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcf91 90 nop
                s.pc = 0x23FCF91; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcf92 33db xor ebx, ebx
                s.pc = 0x23FCF92; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcf94 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FCF94; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fcf99 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FCF99; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcf9d 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FCF9D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fcfa2 4533c9 xor r9d, r9d
                s.pc = 0x23FCFA2; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcfa5 4533c0 xor r8d, r8d
                s.pc = 0x23FCFA5; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcfa8 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FCFA8; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fcfad 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCFAD; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcfb2 e86996a101 call 0x3e16620
                s.pc = 0x23FCFB2; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcfb7 90 nop
                s.pc = 0x23FCFB7; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcfb8 48395d60 cmp qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCFB8; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcfbc 7422 je 0x23fcfe0
                s.pc = 0x23FCFBC; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FCFE0 : 0x23FCFBE);
                }
            }
            case 0x23FCFBE: {
                {
                // 0x23fcfbe 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FCFBE; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fcfc2 e809cb48fe call 0x889ad0
                s.pc = 0x23FCFC2; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcfc7 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FCFC7; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fcfcb 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FCFCB; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fcfce 448d4308 lea r8d, [rbx + 8]
                s.pc = 0x23FCFCE; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx + 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fcfd2 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FCFD2; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fcfd6 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FCFD6; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcfd9 48895d60 mov qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FCFD9; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rbx);
                }
                {
                // 0x23fcfdd 895d68 mov dword ptr [rbp + 0x68], ebx
                s.pc = 0x23FCFDD; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FCFE0);
                }
            }
            case 0x23FCFE0: {
                {
                // 0x23fcfe0 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FCFE0; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fcfe5 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FCFE5; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fcfeb 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FCFEB; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fcff1 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FCFF1; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fcff6 488bce mov rcx, rsi
                s.pc = 0x23FCFF6; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fcff9 e8d28f48fe call 0x885fd0
                s.pc = 0x23FCFF9; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fcffe 90 nop
                s.pc = 0x23FCFFE; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fcfff 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FCFFF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd004 e8479045fe call 0x856050
                s.pc = 0x23FD004; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd009 e9f70a0000 jmp 0x23fdb05
                s.pc = 0x23FD009; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDB05);
                }
            }
            case 0x23FD00E: {
                {
                // 0x23fd00e 41b701 mov r15b, 1
                s.pc = 0x23FD00E; s.context.beforeInstruction(s.pc);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((0x1L) & 0xFFL);
                }
                {
                // 0x23fd011 498b06 mov rax, qword ptr [r14]
                s.pc = 0x23FD011; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fd014 80b8f80b000000 cmp byte ptr [rax + 0xbf8], 0
                s.pc = 0x23FD014; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rax + 0xbf8)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd01b 0f85d6000000 jne 0x23fd0f7
                s.pc = 0x23FD01B; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD0F7 : 0x23FD021);
                }
            }
            case 0x23FD021: {
                {
                // 0x23fd021 498d8ec8000000 lea rcx, [r14 + 0xc8]
                s.pc = 0x23FD021; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.r14 + 0xc8);
                }
                {
                // 0x23fd028 e8d3e3ffff call 0x23fb400
                s.pc = 0x23FD028; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd02d 85c0 test eax, eax
                s.pc = 0x23FD02D; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = (s.r.rax & 0xFFFFFFFFL);
                long result = left & right;
                s.flags.logic(result, 32);
                }
                {
                // 0x23fd02f 0f85c2000000 jne 0x23fd0f7
                s.pc = 0x23FD02F; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD0F7 : 0x23FD035);
                }
            }
            case 0x23FD035: {
                {
                // 0x23fd035 4885f6 test rsi, rsi
                s.pc = 0x23FD035; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd038 0f84c70a0000 je 0x23fdb05
                s.pc = 0x23FD038; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD03E);
                }
            }
            case 0x23FD03E: {
                {
                // 0x23fd03e 4532ff xor r15b, r15b
                s.pc = 0x23FD03E; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd041 488bce mov rcx, rsi
                s.pc = 0x23FD041; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd044 e877425dfe call 0x9d12c0
                s.pc = 0x23FD044; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd049 488d0510ff3202 lea rax, [rip + 0x232ff10]
                s.pc = 0x23FD049; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CF60L);
                }
                {
                // 0x23fd050 4889442460 mov qword ptr [rsp + 0x60], rax
                s.pc = 0x23FD050; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.rax);
                }
                {
                // 0x23fd055 c744246826000000 mov dword ptr [rsp + 0x68], 0x26
                s.pc = 0x23FD055; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)(0x26L));
                }
                {
                // 0x23fd05d 44887c246c mov byte ptr [rsp + 0x6c], r15b
                s.pc = 0x23FD05D; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd062 33d2 xor edx, edx
                s.pc = 0x23FD062; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd064 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FD064; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd06a 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD06A; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd06e e89d9ee201 call 0x4226f10
                s.pc = 0x23FD06E; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd073 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD073; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd077 e864c948fe call 0x8899e0
                s.pc = 0x23FD077; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd07c 90 nop
                s.pc = 0x23FD07C; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd07d 33db xor ebx, ebx
                s.pc = 0x23FD07D; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd07f 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FD07F; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fd084 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FD084; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd088 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD088; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd08d 4533c9 xor r9d, r9d
                s.pc = 0x23FD08D; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd090 4533c0 xor r8d, r8d
                s.pc = 0x23FD090; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd093 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FD093; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fd098 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD098; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd09d e87e95a101 call 0x3e16620
                s.pc = 0x23FD09D; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd0a2 448d6b40 lea r13d, [rbx + 0x40]
                s.pc = 0x23FD0A2; s.context.beforeInstruction(s.pc);
                s.r.r13 = ((s.r.rbx + 0x40)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd0a6 48395d60 cmp qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FD0A6; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd0aa 7422 je 0x23fd0ce
                s.pc = 0x23FD0AA; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD0CE : 0x23FD0AC);
                }
            }
            case 0x23FD0AC: {
                {
                // 0x23fd0ac 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD0AC; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd0b0 e81bca48fe call 0x889ad0
                s.pc = 0x23FD0B0; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd0b5 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FD0B5; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fd0b9 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD0B9; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd0bc 448d4308 lea r8d, [rbx + 8]
                s.pc = 0x23FD0BC; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx + 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd0c0 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FD0C0; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fd0c4 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FD0C4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd0c7 48895d60 mov qword ptr [rbp + 0x60], rbx
                s.pc = 0x23FD0C7; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rbx);
                }
                {
                // 0x23fd0cb 895d68 mov dword ptr [rbp + 0x68], ebx
                s.pc = 0x23FD0CB; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FD0CE);
                }
            }
            case 0x23FD0CE: {
                {
                // 0x23fd0ce 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FD0CE; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd0d3 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FD0D3; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd0d9 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD0D9; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd0df 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FD0DF; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fd0e4 488bce mov rcx, rsi
                s.pc = 0x23FD0E4; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd0e7 e8e48e48fe call 0x885fd0
                s.pc = 0x23FD0E7; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd0ec 90 nop
                s.pc = 0x23FD0EC; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd0ed 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD0ED; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd0f2 e8598f45fe call 0x856050
                s.pc = 0x23FD0F2; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FD0F7);
                }
            }
            case 0x23FD0F7: {
                {
                // 0x23fd0f7 498b9eb0000000 mov rbx, qword ptr [r14 + 0xb0]
                s.pc = 0x23FD0F7; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.memory.readQword((s.r.r14 + 0xb0));
                }
                {
                // 0x23fd0fe 496386bc000000 movsxd rax, dword ptr [r14 + 0xbc]
                s.pc = 0x23FD0FE; s.context.beforeInstruction(s.pc);
                s.r.rax = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0xbc))));
                }
                {
                // 0x23fd105 486bf838 imul rdi, rax, 0x38
                s.pc = 0x23FD105; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = 0x38L;
                long result = left * right;
                s.flags.multiplySigned(left, right, result);
                s.r.rdi = result;
                }
                {
                // 0x23fd109 4803fb add rdi, rbx
                s.pc = 0x23FD109; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = s.r.rbx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fd10c 4c8d0525ff0802 lea r8, [rip + 0x208ff25]
                s.pc = 0x23FD10C; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.image + 0x448D038L);
                }
                {
                // 0x23fd113 41bc01000000 mov r12d, 1
                s.pc = 0x23FD113; s.context.beforeInstruction(s.pc);
                s.r.r12 = (0x1L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd119 483bdf cmp rbx, rdi
                s.pc = 0x23FD119; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd11c 0f8411020000 je 0x23fd333
                s.pc = 0x23FD11C; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD333 : 0x23FD122);
                }
            }
            case 0x23FD122: {
                {
                // 0x23fd122 48833b00 cmp qword ptr [rbx], 0
                s.pc = 0x23FD122; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbx));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd126 0f85e1000000 jne 0x23fd20d
                s.pc = 0x23FD126; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD20D : 0x23FD12C);
                }
            }
            case 0x23FD12C: {
                {
                // 0x23fd12c 4885f6 test rsi, rsi
                s.pc = 0x23FD12C; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd12f 0f84d0090000 je 0x23fdb05
                s.pc = 0x23FD12F; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD135);
                }
            }
            case 0x23FD135: {
                {
                // 0x23fd135 4532ff xor r15b, r15b
                s.pc = 0x23FD135; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd138 4c89442460 mov qword ptr [rsp + 0x60], r8
                s.pc = 0x23FD138; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.r8);
                }
                {
                // 0x23fd13d 4489642468 mov dword ptr [rsp + 0x68], r12d
                s.pc = 0x23FD13D; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd142 44887c246c mov byte ptr [rsp + 0x6c], r15b
                s.pc = 0x23FD142; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd147 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FD147; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fd14c 488bce mov rcx, rsi
                s.pc = 0x23FD14C; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd14f e80ca0b501 call 0x3f57160
                s.pc = 0x23FD14F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd154 488d052dfd3202 lea rax, [rip + 0x232fd2d]
                s.pc = 0x23FD154; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CE88L);
                }
                {
                // 0x23fd15b 488945a0 mov qword ptr [rbp - 0x60], rax
                s.pc = 0x23FD15B; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x60), s.r.rax);
                }
                {
                // 0x23fd15f c745a823000000 mov dword ptr [rbp - 0x58], 0x23
                s.pc = 0x23FD15F; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x58), (int)(0x23L));
                }
                {
                // 0x23fd166 44887dac mov byte ptr [rbp - 0x54], r15b
                s.pc = 0x23FD166; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x54), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd16a 33d2 xor edx, edx
                s.pc = 0x23FD16A; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd16c 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FD16C; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd172 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD172; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd176 e8959de201 call 0x4226f10
                s.pc = 0x23FD176; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd17b 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD17B; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd17f e85cc848fe call 0x8899e0
                s.pc = 0x23FD17F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd184 90 nop
                s.pc = 0x23FD184; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd185 48c744242800000000 mov qword ptr [rsp + 0x28], 0
                s.pc = 0x23FD185; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), 0x0L);
                }
                {
                // 0x23fd18e 488d4560 lea rax, [rbp + 0x60]
                s.pc = 0x23FD18E; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd192 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD192; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd197 4533c9 xor r9d, r9d
                s.pc = 0x23FD197; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd19a 4533c0 xor r8d, r8d
                s.pc = 0x23FD19A; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd19d 488d55a0 lea rdx, [rbp - 0x60]
                s.pc = 0x23FD19D; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x60);
                }
                {
                // 0x23fd1a1 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD1A1; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd1a6 e87594a101 call 0x3e16620
                s.pc = 0x23FD1A6; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd1ab 410fbaed07 bts r13d, 7
                s.pc = 0x23FD1AB; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 7)) != 0);
                s.r.r13 = (left | (1L << 7)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd1b0 48837d6000 cmp qword ptr [rbp + 0x60], 0
                s.pc = 0x23FD1B0; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x60));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd1b5 7426 je 0x23fd1dd
                s.pc = 0x23FD1B5; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD1DD : 0x23FD1B7);
                }
            }
            case 0x23FD1B7: {
                {
                // 0x23fd1b7 488d4d60 lea rcx, [rbp + 0x60]
                s.pc = 0x23FD1B7; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x60);
                }
                {
                // 0x23fd1bb e810c948fe call 0x889ad0
                s.pc = 0x23FD1BB; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd1c0 488b4d70 mov rcx, qword ptr [rbp + 0x70]
                s.pc = 0x23FD1C0; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x70));
                }
                {
                // 0x23fd1c4 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD1C4; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd1c7 41b808000000 mov r8d, 8
                s.pc = 0x23FD1C7; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd1cd 488b5560 mov rdx, qword ptr [rbp + 0x60]
                s.pc = 0x23FD1CD; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x60));
                }
                {
                // 0x23fd1d1 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FD1D1; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd1d4 33c0 xor eax, eax
                s.pc = 0x23FD1D4; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = (s.r.rax & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rax = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd1d6 48894560 mov qword ptr [rbp + 0x60], rax
                s.pc = 0x23FD1D6; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x60), s.r.rax);
                }
                {
                // 0x23fd1da 894568 mov dword ptr [rbp + 0x68], eax
                s.pc = 0x23FD1DA; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x68), (int)((s.r.rax & 0xFFFFFFFFL)));
                return s.transfer(0x23FD1DD);
                }
            }
            case 0x23FD1DD: {
                {
                // 0x23fd1dd 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FD1DD; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd1e2 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FD1E2; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd1e8 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD1E8; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd1ee 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FD1EE; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fd1f3 488bce mov rcx, rsi
                s.pc = 0x23FD1F3; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd1f6 e8d58d48fe call 0x885fd0
                s.pc = 0x23FD1F6; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd1fb 90 nop
                s.pc = 0x23FD1FB; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd1fc 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD1FC; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd201 e84a8e45fe call 0x856050
                s.pc = 0x23FD201; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd206 4c8d052bfe0802 lea r8, [rip + 0x208fe2b]
                s.pc = 0x23FD206; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.image + 0x448D038L);
                return s.transfer(0x23FD20D);
                }
            }
            case 0x23FD20D: {
                {
                // 0x23fd20d 8b5308 mov edx, dword ptr [rbx + 8]
                s.pc = 0x23FD20D; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.rbx + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd210 85d2 test edx, edx
                s.pc = 0x23FD210; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left & right;
                s.flags.logic(result, 32);
                }
                {
                // 0x23fd212 7e1a jle 0x23fd22e
                s.pc = 0x23FD212; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc) || s.flags.sf(s.pc) != s.flags.of(s.pc)) ? 0x23FD22E : 0x23FD214);
                }
            }
            case 0x23FD214: {
                {
                // 0x23fd214 488b0535ba8603 mov rax, qword ptr [rip + 0x386ba35]
                s.pc = 0x23FD214; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.image + 0x5C68C50L));
                }
                {
                // 0x23fd21b 488b88a0000000 mov rcx, qword ptr [rax + 0xa0]
                s.pc = 0x23FD21B; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rax + 0xa0));
                }
                {
                // 0x23fd222 3b914c010000 cmp edx, dword ptr [rcx + 0x14c]
                s.pc = 0x23FD222; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = Integer.toUnsignedLong(s.memory.readDword((s.r.rcx + 0x14c)));
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd228 0f8cf1000000 jl 0x23fd31f
                s.pc = 0x23FD228; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.sf(s.pc) != s.flags.of(s.pc)) ? 0x23FD31F : 0x23FD22E);
                }
            }
            case 0x23FD22E: {
                {
                // 0x23fd22e 4885f6 test rsi, rsi
                s.pc = 0x23FD22E; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd231 0f84ce080000 je 0x23fdb05
                s.pc = 0x23FD231; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD237);
                }
            }
            case 0x23FD237: {
                {
                // 0x23fd237 4532ff xor r15b, r15b
                s.pc = 0x23FD237; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd23a 4c8945b0 mov qword ptr [rbp - 0x50], r8
                s.pc = 0x23FD23A; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x50), s.r.r8);
                }
                {
                // 0x23fd23e 448965b8 mov dword ptr [rbp - 0x48], r12d
                s.pc = 0x23FD23E; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x48), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd242 44887dbc mov byte ptr [rbp - 0x44], r15b
                s.pc = 0x23FD242; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x44), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd246 488d55b0 lea rdx, [rbp - 0x50]
                s.pc = 0x23FD246; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x50);
                }
                {
                // 0x23fd24a 488bce mov rcx, rsi
                s.pc = 0x23FD24A; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd24d e80e9fb501 call 0x3f57160
                s.pc = 0x23FD24D; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd252 488d0507fc3202 lea rax, [rip + 0x232fc07]
                s.pc = 0x23FD252; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CE60L);
                }
                {
                // 0x23fd259 48894590 mov qword ptr [rbp - 0x70], rax
                s.pc = 0x23FD259; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x70), s.r.rax);
                }
                {
                // 0x23fd25d c7459827000000 mov dword ptr [rbp - 0x68], 0x27
                s.pc = 0x23FD25D; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x68), (int)(0x27L));
                }
                {
                // 0x23fd264 44887d9c mov byte ptr [rbp - 0x64], r15b
                s.pc = 0x23FD264; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x64), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd268 33d2 xor edx, edx
                s.pc = 0x23FD268; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd26a 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FD26A; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd270 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD270; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd277 e8949ce201 call 0x4226f10
                s.pc = 0x23FD277; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd27c 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD27C; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd283 e858c748fe call 0x8899e0
                s.pc = 0x23FD283; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd288 90 nop
                s.pc = 0x23FD288; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd289 48c744242800000000 mov qword ptr [rsp + 0x28], 0
                s.pc = 0x23FD289; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), 0x0L);
                }
                {
                // 0x23fd292 488d8590020000 lea rax, [rbp + 0x290]
                s.pc = 0x23FD292; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd299 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD299; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd29e 4533c9 xor r9d, r9d
                s.pc = 0x23FD29E; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd2a1 4533c0 xor r8d, r8d
                s.pc = 0x23FD2A1; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd2a4 488d5590 lea rdx, [rbp - 0x70]
                s.pc = 0x23FD2A4; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x70);
                }
                {
                // 0x23fd2a8 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD2A8; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd2ad e86e93a101 call 0x3e16620
                s.pc = 0x23FD2AD; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd2b2 410fbaed08 bts r13d, 8
                s.pc = 0x23FD2B2; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 8)) != 0);
                s.r.r13 = (left | (1L << 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd2b7 4883bd9002000000 cmp qword ptr [rbp + 0x290], 0
                s.pc = 0x23FD2B7; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x290));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd2bf 7435 je 0x23fd2f6
                s.pc = 0x23FD2BF; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD2F6 : 0x23FD2C1);
                }
            }
            case 0x23FD2C1: {
                {
                // 0x23fd2c1 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD2C1; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd2c8 e803c848fe call 0x889ad0
                s.pc = 0x23FD2C8; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd2cd 488b8da0020000 mov rcx, qword ptr [rbp + 0x2a0]
                s.pc = 0x23FD2CD; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x2a0));
                }
                {
                // 0x23fd2d4 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD2D4; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd2d7 41b808000000 mov r8d, 8
                s.pc = 0x23FD2D7; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd2dd 488b9590020000 mov rdx, qword ptr [rbp + 0x290]
                s.pc = 0x23FD2DD; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x290));
                }
                {
                // 0x23fd2e4 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FD2E4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd2e7 33c0 xor eax, eax
                s.pc = 0x23FD2E7; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = (s.r.rax & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rax = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd2e9 48898590020000 mov qword ptr [rbp + 0x290], rax
                s.pc = 0x23FD2E9; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x290), s.r.rax);
                }
                {
                // 0x23fd2f0 898598020000 mov dword ptr [rbp + 0x298], eax
                s.pc = 0x23FD2F0; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x298), (int)((s.r.rax & 0xFFFFFFFFL)));
                return s.transfer(0x23FD2F6);
                }
            }
            case 0x23FD2F6: {
                {
                // 0x23fd2f6 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FD2F6; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd2fb 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FD2FB; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd301 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD301; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd307 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FD307; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fd30c 488bce mov rcx, rsi
                s.pc = 0x23FD30C; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd30f e8bc8c48fe call 0x885fd0
                s.pc = 0x23FD30F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd314 90 nop
                s.pc = 0x23FD314; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd315 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD315; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd31a e8318d45fe call 0x856050
                s.pc = 0x23FD31A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FD31F);
                }
            }
            default: throw new UnsupportedOperationException("Not a normal activity source block: " + Integer.toHexString(s.pc));
        }
    }

    private static int group2(State s) {
        switch (s.pc) {
            case 0x23FD31F: {
                {
                // 0x23fd31f 4883c338 add rbx, 0x38
                s.pc = 0x23FD31F; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x38L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fd323 483bdf cmp rbx, rdi
                s.pc = 0x23FD323; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd326 4c8d050bfd0802 lea r8, [rip + 0x208fd0b]
                s.pc = 0x23FD326; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.image + 0x448D038L);
                }
                {
                // 0x23fd32d 0f85effdffff jne 0x23fd122
                s.pc = 0x23FD32D; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD122 : 0x23FD333);
                }
            }
            case 0x23FD333: {
                {
                // 0x23fd333 498b06 mov rax, qword ptr [r14]
                s.pc = 0x23FD333; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fd336 80b8ed3b000000 cmp byte ptr [rax + 0x3bed], 0
                s.pc = 0x23FD336; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rax + 0x3bed)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd33d 0f840e010000 je 0x23fd451
                s.pc = 0x23FD33D; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD451 : 0x23FD343);
                }
            }
            case 0x23FD343: {
                {
                // 0x23fd343 498b96b0000000 mov rdx, qword ptr [r14 + 0xb0]
                s.pc = 0x23FD343; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.r14 + 0xb0));
                }
                {
                // 0x23fd34a 8b4208 mov eax, dword ptr [rdx + 8]
                s.pc = 0x23FD34A; s.context.beforeInstruction(s.pc);
                s.r.rax = (Integer.toUnsignedLong(s.memory.readDword((s.r.rdx + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd34d 49638ebc000000 movsxd rcx, dword ptr [r14 + 0xbc]
                s.pc = 0x23FD34D; s.context.beforeInstruction(s.pc);
                s.r.rcx = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0xbc))));
                }
                {
                // 0x23fd354 4c6bc138 imul r8, rcx, 0x38
                s.pc = 0x23FD354; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = 0x38L;
                long result = left * right;
                s.flags.multiplySigned(left, right, result);
                s.r.r8 = result;
                }
                {
                // 0x23fd358 4c03c2 add r8, rdx
                s.pc = 0x23FD358; s.context.beforeInstruction(s.pc);
                long left = s.r.r8;
                long right = s.r.rdx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.r8 = result;
                }
                {
                // 0x23fd35b 493bd0 cmp rdx, r8
                s.pc = 0x23FD35B; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r8;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd35e 0f84ed000000 je 0x23fd451
                s.pc = 0x23FD35E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD451 : 0x23FD364);
                }
            }
            case 0x23FD364: {
                {
                // 0x23fd364 394208 cmp dword ptr [rdx + 8], eax
                s.pc = 0x23FD364; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.rdx + 8)));
                long right = (s.r.rax & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd367 750e jne 0x23fd377
                s.pc = 0x23FD367; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD377 : 0x23FD369);
                }
            }
            case 0x23FD369: {
                {
                // 0x23fd369 4883c238 add rdx, 0x38
                s.pc = 0x23FD369; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = 0x38L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdx = result;
                }
                {
                // 0x23fd36d 493bd0 cmp rdx, r8
                s.pc = 0x23FD36D; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r8;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd370 75f2 jne 0x23fd364
                s.pc = 0x23FD370; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD364 : 0x23FD372);
                }
            }
            case 0x23FD372: {
                {
                // 0x23fd372 e9da000000 jmp 0x23fd451
                s.pc = 0x23FD372; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD451);
                }
            }
            case 0x23FD377: {
                {
                // 0x23fd377 4885f6 test rsi, rsi
                s.pc = 0x23FD377; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd37a 0f8485070000 je 0x23fdb05
                s.pc = 0x23FD37A; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD380);
                }
            }
            case 0x23FD380: {
                {
                // 0x23fd380 4532ff xor r15b, r15b
                s.pc = 0x23FD380; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd383 488bce mov rcx, rsi
                s.pc = 0x23FD383; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd386 e8353f5dfe call 0x9d12c0
                s.pc = 0x23FD386; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd38b 488d054efb3202 lea rax, [rip + 0x232fb4e]
                s.pc = 0x23FD38B; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CEE0L);
                }
                {
                // 0x23fd392 48894590 mov qword ptr [rbp - 0x70], rax
                s.pc = 0x23FD392; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x70), s.r.rax);
                }
                {
                // 0x23fd396 c7459829000000 mov dword ptr [rbp - 0x68], 0x29
                s.pc = 0x23FD396; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x68), (int)(0x29L));
                }
                {
                // 0x23fd39d 44887d9c mov byte ptr [rbp - 0x64], r15b
                s.pc = 0x23FD39D; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x64), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd3a1 33d2 xor edx, edx
                s.pc = 0x23FD3A1; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3a3 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FD3A3; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3a9 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD3A9; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd3b0 e85b9be201 call 0x4226f10
                s.pc = 0x23FD3B0; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd3b5 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD3B5; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd3bc e81fc648fe call 0x8899e0
                s.pc = 0x23FD3BC; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd3c1 90 nop
                s.pc = 0x23FD3C1; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd3c2 33db xor ebx, ebx
                s.pc = 0x23FD3C2; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3c4 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FD3C4; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fd3c9 488d8590020000 lea rax, [rbp + 0x290]
                s.pc = 0x23FD3C9; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd3d0 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD3D0; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd3d5 4533c9 xor r9d, r9d
                s.pc = 0x23FD3D5; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3d8 4533c0 xor r8d, r8d
                s.pc = 0x23FD3D8; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3db 488d5590 lea rdx, [rbp - 0x70]
                s.pc = 0x23FD3DB; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x70);
                }
                {
                // 0x23fd3df 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD3DF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd3e4 e83792a101 call 0x3e16620
                s.pc = 0x23FD3E4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd3e9 410fbaed09 bts r13d, 9
                s.pc = 0x23FD3E9; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 9)) != 0);
                s.r.r13 = (left | (1L << 9)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd3ee 48399d90020000 cmp qword ptr [rbp + 0x290], rbx
                s.pc = 0x23FD3EE; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x290));
                long right = s.r.rbx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd3f5 7431 je 0x23fd428
                s.pc = 0x23FD3F5; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD428 : 0x23FD3F7);
                }
            }
            case 0x23FD3F7: {
                {
                // 0x23fd3f7 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD3F7; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fd3fe e8cdc648fe call 0x889ad0
                s.pc = 0x23FD3FE; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd403 488b8da0020000 mov rcx, qword ptr [rbp + 0x2a0]
                s.pc = 0x23FD403; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x2a0));
                }
                {
                // 0x23fd40a 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD40A; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd40d 448d4308 lea r8d, [rbx + 8]
                s.pc = 0x23FD40D; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx + 8)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd411 488b9590020000 mov rdx, qword ptr [rbp + 0x290]
                s.pc = 0x23FD411; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x290));
                }
                {
                // 0x23fd418 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FD418; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd41b 48899d90020000 mov qword ptr [rbp + 0x290], rbx
                s.pc = 0x23FD41B; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x290), s.r.rbx);
                }
                {
                // 0x23fd422 899d98020000 mov dword ptr [rbp + 0x298], ebx
                s.pc = 0x23FD422; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x298), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FD428);
                }
            }
            case 0x23FD428: {
                {
                // 0x23fd428 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FD428; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd42d 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FD42D; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd433 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD433; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd439 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FD439; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fd43e 488bce mov rcx, rsi
                s.pc = 0x23FD43E; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd441 e88a8b48fe call 0x885fd0
                s.pc = 0x23FD441; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd446 90 nop
                s.pc = 0x23FD446; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd447 488d4c2440 lea rcx, [rsp + 0x40]
                s.pc = 0x23FD447; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd44c e8ff8b45fe call 0x856050
                s.pc = 0x23FD44C; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FD451);
                }
            }
            case 0x23FD451: {
                {
                // 0x23fd451 498bbeb0010000 mov rdi, qword ptr [r14 + 0x1b0]
                s.pc = 0x23FD451; s.context.beforeInstruction(s.pc);
                s.r.rdi = s.memory.readQword((s.r.r14 + 0x1b0));
                }
                {
                // 0x23fd458 496386bc010000 movsxd rax, dword ptr [r14 + 0x1bc]
                s.pc = 0x23FD458; s.context.beforeInstruction(s.pc);
                s.r.rax = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x1bc))));
                }
                {
                // 0x23fd45f 48c1e004 shl rax, 4
                s.pc = 0x23FD45F; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long result = left << 4;
                s.flags.shiftLeft(left, result, 64, 4);
                s.r.rax = result;
                }
                {
                // 0x23fd463 4803c7 add rax, rdi
                s.pc = 0x23FD463; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rdi;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rax = result;
                }
                {
                // 0x23fd466 488985f0050000 mov qword ptr [rbp + 0x5f0], rax
                s.pc = 0x23FD466; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x5f0), s.r.rax);
                }
                {
                // 0x23fd46d 483bf8 cmp rdi, rax
                s.pc = 0x23FD46D; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = s.r.rax;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd470 0f84fb030000 je 0x23fd871
                s.pc = 0x23FD470; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD871 : 0x23FD476);
                }
            }
            case 0x23FD476: {
                {
                // 0x23fd476 4883c708 add rdi, 8
                s.pc = 0x23FD476; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = 0x8L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fd47a 488bc8 mov rcx, rax
                s.pc = 0x23FD47A; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rax;
                }
                {
                // 0x23fd47d 0f1f00 nop dword ptr [rax]
                s.pc = 0x23FD47D; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD480);
                }
            }
            case 0x23FD480: {
                {
                // 0x23fd480 488d5ff8 lea rbx, [rdi - 8]
                s.pc = 0x23FD480; s.context.beforeInstruction(s.pc);
                s.r.rbx = (s.r.rdi - 8);
                }
                {
                // 0x23fd484 488b03 mov rax, qword ptr [rbx]
                s.pc = 0x23FD484; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rbx));
                }
                {
                // 0x23fd487 80b84003000000 cmp byte ptr [rax + 0x340], 0
                s.pc = 0x23FD487; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rax + 0x340)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd48e 0f84cc030000 je 0x23fd860
                s.pc = 0x23FD48E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD860 : 0x23FD494);
                }
            }
            case 0x23FD494: {
                {
                // 0x23fd494 448b07 mov r8d, dword ptr [rdi]
                s.pc = 0x23FD494; s.context.beforeInstruction(s.pc);
                s.r.r8 = (Integer.toUnsignedLong(s.memory.readDword((s.r.rdi)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd497 4183f8ff cmp r8d, -1
                s.pc = 0x23FD497; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = -0x1L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd49b 0f8581000000 jne 0x23fd522
                s.pc = 0x23FD49B; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD522 : 0x23FD4A1);
                }
            }
            case 0x23FD4A1: {
                {
                // 0x23fd4a1 4885f6 test rsi, rsi
                s.pc = 0x23FD4A1; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd4a4 0f845b060000 je 0x23fdb05
                s.pc = 0x23FD4A4; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD4AA);
                }
            }
            case 0x23FD4AA: {
                {
                // 0x23fd4aa 4532ff xor r15b, r15b
                s.pc = 0x23FD4AA; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd4ad 488d0584fb0802 lea rax, [rip + 0x208fb84]
                s.pc = 0x23FD4AD; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fd4b4 48894590 mov qword ptr [rbp - 0x70], rax
                s.pc = 0x23FD4B4; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x70), s.r.rax);
                }
                {
                // 0x23fd4b8 44896598 mov dword ptr [rbp - 0x68], r12d
                s.pc = 0x23FD4B8; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x68), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd4bc 44887d9c mov byte ptr [rbp - 0x64], r15b
                s.pc = 0x23FD4BC; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x64), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd4c0 488d5590 lea rdx, [rbp - 0x70]
                s.pc = 0x23FD4C0; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x70);
                }
                {
                // 0x23fd4c4 488bce mov rcx, rsi
                s.pc = 0x23FD4C4; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd4c7 e8949cb501 call 0x3f57160
                s.pc = 0x23FD4C7; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd4cc 488d05ddf93202 lea rax, [rip + 0x232f9dd]
                s.pc = 0x23FD4CC; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CEB0L);
                }
                {
                // 0x23fd4d3 488945b0 mov qword ptr [rbp - 0x50], rax
                s.pc = 0x23FD4D3; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x50), s.r.rax);
                }
                {
                // 0x23fd4d7 c745b82d000000 mov dword ptr [rbp - 0x48], 0x2d
                s.pc = 0x23FD4D7; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x48), (int)(0x2DL));
                }
                {
                // 0x23fd4de 44887dbc mov byte ptr [rbp - 0x44], r15b
                s.pc = 0x23FD4DE; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x44), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd4e2 48897c2430 mov qword ptr [rsp + 0x30], rdi
                s.pc = 0x23FD4E2; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x30), s.r.rdi);
                }
                {
                // 0x23fd4e7 48895c2420 mov qword ptr [rsp + 0x20], rbx
                s.pc = 0x23FD4E7; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rbx);
                }
                {
                // 0x23fd4ec 488d55b0 lea rdx, [rbp - 0x50]
                s.pc = 0x23FD4EC; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x50);
                }
                {
                // 0x23fd4f0 488d4d18 lea rcx, [rbp + 0x18]
                s.pc = 0x23FD4F0; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x18);
                }
                {
                // 0x23fd4f4 e8f748dcfe call 0x11c1df0
                s.pc = 0x23FD4F4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd4f9 410fbaed0a bts r13d, 0xa
                s.pc = 0x23FD4F9; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 10)) != 0);
                s.r.r13 = (left | (1L << 10)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd4fe 488d5518 lea rdx, [rbp + 0x18]
                s.pc = 0x23FD4FE; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x18);
                }
                {
                // 0x23fd502 48837d3010 cmp qword ptr [rbp + 0x30], 0x10
                s.pc = 0x23FD502; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x30));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd507 480f435518 cmovae rdx, qword ptr [rbp + 0x18]
                s.pc = 0x23FD507; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rbp + 0x18));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd50c 4c8b4528 mov r8, qword ptr [rbp + 0x28]
                s.pc = 0x23FD50C; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rbp + 0x28));
                }
                {
                // 0x23fd510 488bce mov rcx, rsi
                s.pc = 0x23FD510; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd513 e8b88a48fe call 0x885fd0
                s.pc = 0x23FD513; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd518 90 nop
                s.pc = 0x23FD518; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd519 488d4d18 lea rcx, [rbp + 0x18]
                s.pc = 0x23FD519; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x18);
                }
                {
                // 0x23fd51d e932030000 jmp 0x23fd854
                s.pc = 0x23FD51D; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD854);
                }
            }
            case 0x23FD522: {
                {
                // 0x23fd522 488b153fa08603 mov rdx, qword ptr [rip + 0x386a03f]
                s.pc = 0x23FD522; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.image + 0x5C67568L));
                }
                {
                // 0x23fd529 4885d2 test rdx, rdx
                s.pc = 0x23FD529; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.rdx;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd52c 7426 je 0x23fd554
                s.pc = 0x23FD52C; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD554 : 0x23FD52E);
                }
            }
            case 0x23FD52E: {
                {
                // 0x23fd52e 418bc0 mov eax, r8d
                s.pc = 0x23FD52E; s.context.beforeInstruction(s.pc);
                s.r.rax = ((s.r.r8 & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd531 25ffffff00 and eax, 0xffffff
                s.pc = 0x23FD531; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = 0xFFFFFFL;
                long result = left & right;
                s.flags.logic(result, 32);
                s.r.rax = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd536 3b422c cmp eax, dword ptr [rdx + 0x2c]
                s.pc = 0x23FD536; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long right = Integer.toUnsignedLong(s.memory.readDword((s.r.rdx + 0x2c)));
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd539 7319 jae 0x23fd554
                s.pc = 0x23FD539; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.cf(s.pc)) ? 0x23FD554 : 0x23FD53B);
                }
            }
            case 0x23FD53B: {
                {
                // 0x23fd53b 8bc8 mov ecx, eax
                s.pc = 0x23FD53B; s.context.beforeInstruction(s.pc);
                s.r.rcx = ((s.r.rax & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd53d 4803c9 add rcx, rcx
                s.pc = 0x23FD53D; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rcx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fd540 488b4220 mov rax, qword ptr [rdx + 0x20]
                s.pc = 0x23FD540; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rdx + 0x20));
                }
                {
                // 0x23fd544 488b44c808 mov rax, qword ptr [rax + rcx*8 + 8]
                s.pc = 0x23FD544; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rax + s.r.rcx*8 + 8));
                }
                {
                // 0x23fd549 4885c0 test rax, rax
                s.pc = 0x23FD549; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rax;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd54c 7406 je 0x23fd554
                s.pc = 0x23FD54C; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD554 : 0x23FD54E);
                }
            }
            case 0x23FD54E: {
                {
                // 0x23fd54e 44394018 cmp dword ptr [rax + 0x18], r8d
                s.pc = 0x23FD54E; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 0x18)));
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd552 7407 je 0x23fd55b
                s.pc = 0x23FD552; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD55B : 0x23FD554);
                }
            }
            case 0x23FD554: {
                {
                // 0x23fd554 488b0515a08603 mov rax, qword ptr [rip + 0x386a015]
                s.pc = 0x23FD554; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.image + 0x5C67570L));
                return s.transfer(0x23FD55B);
                }
            }
            case 0x23FD55B: {
                {
                // 0x23fd55b 4883b8d001000000 cmp qword ptr [rax + 0x1d0], 0
                s.pc = 0x23FD55B; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rax + 0x1d0));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd563 0f8485000000 je 0x23fd5ee
                s.pc = 0x23FD563; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD5EE : 0x23FD569);
                }
            }
            case 0x23FD569: {
                {
                // 0x23fd569 4885f6 test rsi, rsi
                s.pc = 0x23FD569; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd56c 0f8493050000 je 0x23fdb05
                s.pc = 0x23FD56C; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD572);
                }
            }
            case 0x23FD572: {
                {
                // 0x23fd572 4532ff xor r15b, r15b
                s.pc = 0x23FD572; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd575 488d05bcfa0802 lea rax, [rip + 0x208fabc]
                s.pc = 0x23FD575; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fd57c 488945a0 mov qword ptr [rbp - 0x60], rax
                s.pc = 0x23FD57C; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x60), s.r.rax);
                }
                {
                // 0x23fd580 448965a8 mov dword ptr [rbp - 0x58], r12d
                s.pc = 0x23FD580; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x58), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd584 44887dac mov byte ptr [rbp - 0x54], r15b
                s.pc = 0x23FD584; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x54), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd588 488d55a0 lea rdx, [rbp - 0x60]
                s.pc = 0x23FD588; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x60);
                }
                {
                // 0x23fd58c 488bce mov rcx, rsi
                s.pc = 0x23FD58C; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd58f e8cc9bb501 call 0x3f57160
                s.pc = 0x23FD58F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd594 488d0595f83202 lea rax, [rip + 0x232f895]
                s.pc = 0x23FD594; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CE30L);
                }
                {
                // 0x23fd59b 4889442460 mov qword ptr [rsp + 0x60], rax
                s.pc = 0x23FD59B; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x60), s.r.rax);
                }
                {
                // 0x23fd5a0 c74424682c000000 mov dword ptr [rsp + 0x68], 0x2c
                s.pc = 0x23FD5A0; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rsp + 0x68), (int)(0x2CL));
                }
                {
                // 0x23fd5a8 44887c246c mov byte ptr [rsp + 0x6c], r15b
                s.pc = 0x23FD5A8; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x6c), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd5ad 48897c2430 mov qword ptr [rsp + 0x30], rdi
                s.pc = 0x23FD5AD; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x30), s.r.rdi);
                }
                {
                // 0x23fd5b2 48895c2420 mov qword ptr [rsp + 0x20], rbx
                s.pc = 0x23FD5B2; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rbx);
                }
                {
                // 0x23fd5b7 488d542460 lea rdx, [rsp + 0x60]
                s.pc = 0x23FD5B7; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x60);
                }
                {
                // 0x23fd5bc 488d4d38 lea rcx, [rbp + 0x38]
                s.pc = 0x23FD5BC; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x38);
                }
                {
                // 0x23fd5c0 e82b48dcfe call 0x11c1df0
                s.pc = 0x23FD5C0; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd5c5 410fbaed0b bts r13d, 0xb
                s.pc = 0x23FD5C5; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 11)) != 0);
                s.r.r13 = (left | (1L << 11)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd5ca 488d5538 lea rdx, [rbp + 0x38]
                s.pc = 0x23FD5CA; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x38);
                }
                {
                // 0x23fd5ce 48837d5010 cmp qword ptr [rbp + 0x50], 0x10
                s.pc = 0x23FD5CE; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x50));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd5d3 480f435538 cmovae rdx, qword ptr [rbp + 0x38]
                s.pc = 0x23FD5D3; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rbp + 0x38));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd5d8 4c8b4548 mov r8, qword ptr [rbp + 0x48]
                s.pc = 0x23FD5D8; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rbp + 0x48));
                }
                {
                // 0x23fd5dc 488bce mov rcx, rsi
                s.pc = 0x23FD5DC; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd5df e8ec8948fe call 0x885fd0
                s.pc = 0x23FD5DF; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd5e4 90 nop
                s.pc = 0x23FD5E4; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd5e5 488d4d38 lea rcx, [rbp + 0x38]
                s.pc = 0x23FD5E5; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x38);
                }
                {
                // 0x23fd5e9 e966020000 jmp 0x23fd854
                s.pc = 0x23FD5E9; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD854);
                }
            }
            case 0x23FD5EE: {
                {
                // 0x23fd5ee c644242801 mov byte ptr [rsp + 0x28], 1
                s.pc = 0x23FD5EE; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x28), (int)(0x1L) & 0xFF);
                }
                {
                // 0x23fd5f3 48c744242000000000 mov qword ptr [rsp + 0x20], 0
                s.pc = 0x23FD5F3; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), 0x0L);
                }
                {
                // 0x23fd5fc 4c8b4c2470 mov r9, qword ptr [rsp + 0x70]
                s.pc = 0x23FD5FC; s.context.beforeInstruction(s.pc);
                s.r.r9 = s.memory.readQword((s.r.rsp + 0x70));
                }
                {
                // 0x23fd601 418b5608 mov edx, dword ptr [r14 + 8]
                s.pc = 0x23FD601; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd605 498b0e mov rcx, qword ptr [r14]
                s.pc = 0x23FD605; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fd608 e843f47b00 call 0x2bbca50
                s.pc = 0x23FD608; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd60d 84c0 test al, al
                s.pc = 0x23FD60D; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fd60f 0f859b010000 jne 0x23fd7b0
                s.pc = 0x23FD60F; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD7B0 : 0x23FD615);
                }
            }
            case 0x23FD615: {
                {
                // 0x23fd615 4885f6 test rsi, rsi
                s.pc = 0x23FD615; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd618 0f84e7040000 je 0x23fdb05
                s.pc = 0x23FD618; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD61E);
                }
            }
            case 0x23FD61E: {
                {
                // 0x23fd61e 4532ff xor r15b, r15b
                s.pc = 0x23FD61E; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd621 33c9 xor ecx, ecx
                s.pc = 0x23FD621; s.context.beforeInstruction(s.pc);
                long left = (s.r.rcx & 0xFFFFFFFFL);
                long right = (s.r.rcx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rcx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd623 48894c2440 mov qword ptr [rsp + 0x40], rcx
                s.pc = 0x23FD623; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x40), s.r.rcx);
                }
                {
                // 0x23fd628 48894c2450 mov qword ptr [rsp + 0x50], rcx
                s.pc = 0x23FD628; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x50), s.r.rcx);
                }
                {
                // 0x23fd62d 48c74424580f000000 mov qword ptr [rsp + 0x58], 0xf
                s.pc = 0x23FD62D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x58), 0xFL);
                }
                {
                // 0x23fd636 884c2440 mov byte ptr [rsp + 0x40], cl
                s.pc = 0x23FD636; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x40), (int)((s.r.rcx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd63a 0fb705e3be0302 movzx eax, word ptr [rip + 0x203bee3]
                s.pc = 0x23FD63A; s.context.beforeInstruction(s.pc);
                // Whole source WORD/byte group: 23FD63A, 23FD641, 23FD645, 23FD64C, exactly once.
                s.r.rax = ActivityWordBlock265.execute(s.image, s.r.rbp, s.memory);
                }
                {
                // 0x23fd64f 488d442440 lea rax, [rsp + 0x40]
                s.pc = 0x23FD64F; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd654 488945e8 mov qword ptr [rbp - 0x18], rax
                s.pc = 0x23FD654; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x18), s.r.rax);
                }
                {
                // 0x23fd658 48894df0 mov qword ptr [rbp - 0x10], rcx
                s.pc = 0x23FD658; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x10), s.r.rcx);
                }
                {
                // 0x23fd65c b9d8000000 mov ecx, 0xd8
                s.pc = 0x23FD65C; s.context.beforeInstruction(s.pc);
                s.r.rcx = (0xD8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd661 e82e65e201 call 0x4223b94
                s.pc = 0x23FD661; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd666 48898500060000 mov qword ptr [rbp + 0x600], rax
                s.pc = 0x23FD666; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x600), s.r.rax);
                }
                {
                // 0x23fd66d 488bc8 mov rcx, rax
                s.pc = 0x23FD66D; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rax;
                }
                {
                // 0x23fd670 e84b903c01 call 0x37c66c0
                s.pc = 0x23FD670; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd675 488bd8 mov rbx, rax
                s.pc = 0x23FD675; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.r.rax;
                }
                {
                // 0x23fd678 410fbaed0c bts r13d, 0xc
                s.pc = 0x23FD678; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 12)) != 0);
                s.r.r13 = (left | (1L << 12)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd67d 488945f0 mov qword ptr [rbp - 0x10], rax
                s.pc = 0x23FD67D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x10), s.r.rax);
                }
                {
                // 0x23fd681 c644242801 mov byte ptr [rsp + 0x28], 1
                s.pc = 0x23FD681; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x28), (int)(0x1L) & 0xFF);
                }
                {
                // 0x23fd686 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD686; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd68b 4c8b4c2470 mov r9, qword ptr [rsp + 0x70]
                s.pc = 0x23FD68B; s.context.beforeInstruction(s.pc);
                s.r.r9 = s.memory.readQword((s.r.rsp + 0x70));
                }
                {
                // 0x23fd690 448b07 mov r8d, dword ptr [rdi]
                s.pc = 0x23FD690; s.context.beforeInstruction(s.pc);
                s.r.r8 = (Integer.toUnsignedLong(s.memory.readDword((s.r.rdi)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd693 418b5608 mov edx, dword ptr [r14 + 8]
                s.pc = 0x23FD693; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd697 498b0e mov rcx, qword ptr [r14]
                s.pc = 0x23FD697; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14));
                }
                {
                // 0x23fd69a e8b1f37b00 call 0x2bbca50
                s.pc = 0x23FD69A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd69f 90 nop
                s.pc = 0x23FD69F; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd6a0 4885db test rbx, rbx
                s.pc = 0x23FD6A0; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rbx;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd6a3 7525 jne 0x23fd6ca
                s.pc = 0x23FD6A3; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD6CA : 0x23FD6A5);
                }
            }
            case 0x23FD6A5: {
                {
                // 0x23fd6a5 b9d8000000 mov ecx, 0xd8
                s.pc = 0x23FD6A5; s.context.beforeInstruction(s.pc);
                s.r.rcx = (0xD8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd6aa e8e564e201 call 0x4223b94
                s.pc = 0x23FD6AA; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd6af 48898500060000 mov qword ptr [rbp + 0x600], rax
                s.pc = 0x23FD6AF; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x600), s.r.rax);
                }
                {
                // 0x23fd6b6 488bc8 mov rcx, rax
                s.pc = 0x23FD6B6; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rax;
                }
                {
                // 0x23fd6b9 e802903c01 call 0x37c66c0
                s.pc = 0x23FD6B9; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd6be 488bd8 mov rbx, rax
                s.pc = 0x23FD6BE; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.r.rax;
                }
                {
                // 0x23fd6c1 410fbaed0d bts r13d, 0xd
                s.pc = 0x23FD6C1; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 13)) != 0);
                s.r.r13 = (left | (1L << 13)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd6c6 488945f0 mov qword ptr [rbp - 0x10], rax
                s.pc = 0x23FD6C6; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x10), s.r.rax);
                return s.transfer(0x23FD6CA);
                }
            }
            case 0x23FD6CA: {
                {
                // 0x23fd6ca c683d000000000 mov byte ptr [rbx + 0xd0], 0
                s.pc = 0x23FD6CA; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbx + 0xd0), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fd6d1 488bcb mov rcx, rbx
                s.pc = 0x23FD6D1; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd6d4 e897da3e01 call 0x37eb170
                s.pc = 0x23FD6D4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd6d9 488bcb mov rcx, rbx
                s.pc = 0x23FD6D9; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd6dc e88fdb3e01 call 0x37eb270
                s.pc = 0x23FD6DC; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd6e1 c683d000000001 mov byte ptr [rbx + 0xd0], 1
                s.pc = 0x23FD6E1; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbx + 0xd0), (int)(0x1L) & 0xFF);
                }
                {
                // 0x23fd6e8 4c8d442440 lea r8, [rsp + 0x40]
                s.pc = 0x23FD6E8; s.context.beforeInstruction(s.pc);
                s.r.r8 = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd6ed 488d55e0 lea rdx, [rbp - 0x20]
                s.pc = 0x23FD6ED; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x20);
                }
                {
                // 0x23fd6f1 488d4df0 lea rcx, [rbp - 0x10]
                s.pc = 0x23FD6F1; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x10);
                }
                {
                // 0x23fd6f5 e8a6053601 call 0x375dca0
                s.pc = 0x23FD6F5; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd6fa 488b5df0 mov rbx, qword ptr [rbp - 0x10]
                s.pc = 0x23FD6FA; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.memory.readQword((s.r.rbp - 0x10));
                }
                {
                // 0x23fd6fe 4885db test rbx, rbx
                s.pc = 0x23FD6FE; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rbx;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd701 7416 je 0x23fd719
                s.pc = 0x23FD701; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD719 : 0x23FD703);
                }
            }
            case 0x23FD703: {
                {
                // 0x23fd703 488bcb mov rcx, rbx
                s.pc = 0x23FD703; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd706 e8f526daff call 0x219fe00
                s.pc = 0x23FD706; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd70b bad8000000 mov edx, 0xd8
                s.pc = 0x23FD70B; s.context.beforeInstruction(s.pc);
                s.r.rdx = (0xD8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd710 488bcb mov rcx, rbx
                s.pc = 0x23FD710; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd713 e82c68e201 call 0x4223f44
                s.pc = 0x23FD713; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd718 90 nop
                s.pc = 0x23FD718; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD719);
                }
            }
            case 0x23FD719: {
                {
                // 0x23fd719 488d0518f90802 lea rax, [rip + 0x208f918]
                s.pc = 0x23FD719; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fd720 488945f8 mov qword ptr [rbp - 8], rax
                s.pc = 0x23FD720; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 8), s.r.rax);
                }
                {
                // 0x23fd724 44896500 mov dword ptr [rbp], r12d
                s.pc = 0x23FD724; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd728 c6450400 mov byte ptr [rbp + 4], 0
                s.pc = 0x23FD728; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp + 4), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fd72c 488d55f8 lea rdx, [rbp - 8]
                s.pc = 0x23FD72C; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 8);
                }
                {
                // 0x23fd730 488bce mov rcx, rsi
                s.pc = 0x23FD730; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd733 e8289ab501 call 0x3f57160
                s.pc = 0x23FD733; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd738 488d542440 lea rdx, [rsp + 0x40]
                s.pc = 0x23FD738; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rsp + 0x40);
                }
                {
                // 0x23fd73d 48837c245810 cmp qword ptr [rsp + 0x58], 0x10
                s.pc = 0x23FD73D; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rsp + 0x58));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd743 480f43542440 cmovae rdx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD743; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rsp + 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd749 4c8b442450 mov r8, qword ptr [rsp + 0x50]
                s.pc = 0x23FD749; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rsp + 0x50));
                }
                {
                // 0x23fd74e 488bce mov rcx, rsi
                s.pc = 0x23FD74E; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd751 e87a8848fe call 0x885fd0
                s.pc = 0x23FD751; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd756 90 nop
                s.pc = 0x23FD756; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd757 488b542458 mov rdx, qword ptr [rsp + 0x58]
                s.pc = 0x23FD757; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rsp + 0x58));
                }
                {
                // 0x23fd75c 4883fa10 cmp rdx, 0x10
                s.pc = 0x23FD75C; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd760 7232 jb 0x23fd794
                s.pc = 0x23FD760; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.cf(s.pc)) ? 0x23FD794 : 0x23FD762);
                }
            }
            case 0x23FD762: {
                {
                // 0x23fd762 48ffc2 inc rdx
                s.pc = 0x23FD762; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.rdx = result;
                }
                {
                // 0x23fd765 488b4c2440 mov rcx, qword ptr [rsp + 0x40]
                s.pc = 0x23FD765; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rsp + 0x40));
                }
                {
                // 0x23fd76a 488bc1 mov rax, rcx
                s.pc = 0x23FD76A; s.context.beforeInstruction(s.pc);
                s.r.rax = s.r.rcx;
                }
                {
                // 0x23fd76d 4881fa00100000 cmp rdx, 0x1000
                s.pc = 0x23FD76D; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = 0x1000L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd774 7219 jb 0x23fd78f
                s.pc = 0x23FD774; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.cf(s.pc)) ? 0x23FD78F : 0x23FD776);
                }
            }
            case 0x23FD776: {
                {
                // 0x23fd776 4883c227 add rdx, 0x27
                s.pc = 0x23FD776; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = 0x27L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdx = result;
                }
                {
                // 0x23fd77a 488b49f8 mov rcx, qword ptr [rcx - 8]
                s.pc = 0x23FD77A; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rcx - 8));
                }
                {
                // 0x23fd77e 482bc1 sub rax, rcx
                s.pc = 0x23FD77E; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rcx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                s.r.rax = result;
                }
                {
                // 0x23fd781 4883c0f8 add rax, -8
                s.pc = 0x23FD781; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = -0x8L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rax = result;
                }
                {
                // 0x23fd785 4883f81f cmp rax, 0x1f
                s.pc = 0x23FD785; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = 0x1FL;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd789 0f8793040000 ja 0x23fdc22
                s.pc = 0x23FD789; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.cf(s.pc) && !s.flags.zf(s.pc)) ? 0x23FDC22 : 0x23FD78F);
                }
            }
            case 0x23FD78F: {
                {
                // 0x23fd78f e8b067e201 call 0x4223f44
                s.pc = 0x23FD78F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FD794);
                }
            }
            case 0x23FD794: {
                {
                // 0x23fd794 48c744245000000000 mov qword ptr [rsp + 0x50], 0
                s.pc = 0x23FD794; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x50), 0x0L);
                }
                {
                // 0x23fd79d 48c74424580f000000 mov qword ptr [rsp + 0x58], 0xf
                s.pc = 0x23FD79D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x58), 0xFL);
                }
                {
                // 0x23fd7a6 c644244000 mov byte ptr [rsp + 0x40], 0
                s.pc = 0x23FD7A6; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rsp + 0x40), (int)(0x0L) & 0xFF);
                }
                {
                // 0x23fd7ab e9a9000000 jmp 0x23fd859
                s.pc = 0x23FD7AB; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD859);
                }
            }
            case 0x23FD7B0: {
                {
                // 0x23fd7b0 488b442470 mov rax, qword ptr [rsp + 0x70]
                s.pc = 0x23FD7B0; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rsp + 0x70));
                }
                {
                // 0x23fd7b5 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FD7B5; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fd7ba 4d8d8eb0010000 lea r9, [r14 + 0x1b0]
                s.pc = 0x23FD7BA; s.context.beforeInstruction(s.pc);
                s.r.r9 = (s.r.r14 + 0x1b0);
                }
                {
                // 0x23fd7c1 448b07 mov r8d, dword ptr [rdi]
                s.pc = 0x23FD7C1; s.context.beforeInstruction(s.pc);
                s.r.r8 = (Integer.toUnsignedLong(s.memory.readDword((s.r.rdi)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd7c4 418b5608 mov edx, dword ptr [r14 + 8]
                s.pc = 0x23FD7C4; s.context.beforeInstruction(s.pc);
                s.r.rdx = (Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 8)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd7c8 488b0b mov rcx, qword ptr [rbx]
                s.pc = 0x23FD7C8; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbx));
                }
                {
                // 0x23fd7cb e8a0f77b00 call 0x2bbcf70
                s.pc = 0x23FD7CB; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd7d0 84c0 test al, al
                s.pc = 0x23FD7D0; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fd7d2 0f8581000000 jne 0x23fd859
                s.pc = 0x23FD7D2; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD859 : 0x23FD7D8);
                }
            }
            case 0x23FD7D8: {
                {
                // 0x23fd7d8 4885f6 test rsi, rsi
                s.pc = 0x23FD7D8; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd7db 0f8424030000 je 0x23fdb05
                s.pc = 0x23FD7DB; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD7E1);
                }
            }
            case 0x23FD7E1: {
                {
                // 0x23fd7e1 4532ff xor r15b, r15b
                s.pc = 0x23FD7E1; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd7e4 488d054df80802 lea rax, [rip + 0x208f84d]
                s.pc = 0x23FD7E4; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fd7eb 48894508 mov qword ptr [rbp + 8], rax
                s.pc = 0x23FD7EB; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 8), s.r.rax);
                }
                {
                // 0x23fd7ef 44896510 mov dword ptr [rbp + 0x10], r12d
                s.pc = 0x23FD7EF; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x10), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fd7f3 44887d14 mov byte ptr [rbp + 0x14], r15b
                s.pc = 0x23FD7F3; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp + 0x14), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd7f7 488d5508 lea rdx, [rbp + 8]
                s.pc = 0x23FD7F7; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 8);
                }
                {
                // 0x23fd7fb 488bce mov rcx, rsi
                s.pc = 0x23FD7FB; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd7fe e85d99b501 call 0x3f57160
                s.pc = 0x23FD7FE; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd803 488d057ef03202 lea rax, [rip + 0x232f07e]
                s.pc = 0x23FD803; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472C888L);
                }
                {
                // 0x23fd80a 48894580 mov qword ptr [rbp - 0x80], rax
                s.pc = 0x23FD80A; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x80), s.r.rax);
                }
                {
                // 0x23fd80e c745882f000000 mov dword ptr [rbp - 0x78], 0x2f
                s.pc = 0x23FD80E; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x78), (int)(0x2FL));
                }
                {
                // 0x23fd815 44887d8c mov byte ptr [rbp - 0x74], r15b
                s.pc = 0x23FD815; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x74), (int)((s.r.r15 & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd819 48897c2430 mov qword ptr [rsp + 0x30], rdi
                s.pc = 0x23FD819; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x30), s.r.rdi);
                }
                {
                // 0x23fd81e 48895c2420 mov qword ptr [rsp + 0x20], rbx
                s.pc = 0x23FD81E; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rbx);
                }
                {
                // 0x23fd823 488d5580 lea rdx, [rbp - 0x80]
                s.pc = 0x23FD823; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x80);
                }
                {
                // 0x23fd827 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FD827; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fd82b e8c045dcfe call 0x11c1df0
                s.pc = 0x23FD82B; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd830 410fbaed0e bts r13d, 0xe
                s.pc = 0x23FD830; s.context.beforeInstruction(s.pc);
                long left = (s.r.r13 & 0xFFFFFFFFL);
                s.flags.bitTest((left & (1L << 14)) != 0);
                s.r.r13 = (left | (1L << 14)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd835 488d55c0 lea rdx, [rbp - 0x40]
                s.pc = 0x23FD835; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fd839 48837dd810 cmp qword ptr [rbp - 0x28], 0x10
                s.pc = 0x23FD839; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp - 0x28));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd83e 480f4355c0 cmovae rdx, qword ptr [rbp - 0x40]
                s.pc = 0x23FD83E; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rbp - 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fd843 4c8b45d0 mov r8, qword ptr [rbp - 0x30]
                s.pc = 0x23FD843; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rbp - 0x30));
                }
                {
                // 0x23fd847 488bce mov rcx, rsi
                s.pc = 0x23FD847; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd84a e8818748fe call 0x885fd0
                s.pc = 0x23FD84A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd84f 90 nop
                s.pc = 0x23FD84F; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fd850 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FD850; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                return s.transfer(0x23FD854);
                }
            }
            default: throw new UnsupportedOperationException("Not a normal activity source block: " + Integer.toHexString(s.pc));
        }
    }

    private static int group3(State s) {
        switch (s.pc) {
            case 0x23FD854: {
                {
                // 0x23fd854 e8f78745fe call 0x856050
                s.pc = 0x23FD854; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FD859);
                }
            }
            case 0x23FD859: {
                {
                // 0x23fd859 488b8df0050000 mov rcx, qword ptr [rbp + 0x5f0]
                s.pc = 0x23FD859; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x5f0));
                return s.transfer(0x23FD860);
                }
            }
            case 0x23FD860: {
                {
                // 0x23fd860 4883c710 add rdi, 0x10
                s.pc = 0x23FD860; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = 0x10L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fd864 488d47f8 lea rax, [rdi - 8]
                s.pc = 0x23FD864; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rdi - 8);
                }
                {
                // 0x23fd868 483bc1 cmp rax, rcx
                s.pc = 0x23FD868; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rcx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd86b 0f850ffcffff jne 0x23fd480
                s.pc = 0x23FD86B; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD480 : 0x23FD871);
                }
            }
            case 0x23FD871: {
                {
                // 0x23fd871 498b9e98000000 mov rbx, qword ptr [r14 + 0x98]
                s.pc = 0x23FD871; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.memory.readQword((s.r.r14 + 0x98));
                }
                {
                // 0x23fd878 4963bea4000000 movsxd rdi, dword ptr [r14 + 0xa4]
                s.pc = 0x23FD878; s.context.beforeInstruction(s.pc);
                s.r.rdi = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0xa4))));
                }
                {
                // 0x23fd87f 48c1e704 shl rdi, 4
                s.pc = 0x23FD87F; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long result = left << 4;
                s.flags.shiftLeft(left, result, 64, 4);
                s.r.rdi = result;
                }
                {
                // 0x23fd883 4803fb add rdi, rbx
                s.pc = 0x23FD883; s.context.beforeInstruction(s.pc);
                long left = s.r.rdi;
                long right = s.r.rbx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rdi = result;
                }
                {
                // 0x23fd886 483bdf cmp rbx, rdi
                s.pc = 0x23FD886; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd889 7464 je 0x23fd8ef
                s.pc = 0x23FD889; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD8EF : 0x23FD88B);
                }
            }
            case 0x23FD88B: {
                {
                // 0x23fd88b 4883c308 add rbx, 8
                s.pc = 0x23FD88B; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x8L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fd88f 90 nop
                s.pc = 0x23FD88F; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD890);
                }
            }
            case 0x23FD890: {
                {
                // 0x23fd890 488b0b mov rcx, qword ptr [rbx]
                s.pc = 0x23FD890; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbx));
                }
                {
                // 0x23fd893 4881c1f0000000 add rcx, 0xf0
                s.pc = 0x23FD893; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = 0xF0L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fd89a 4c8bc6 mov r8, rsi
                s.pc = 0x23FD89A; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rsi;
                }
                {
                // 0x23fd89d 488d9540040000 lea rdx, [rbp + 0x440]
                s.pc = 0x23FD89D; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x440);
                }
                {
                // 0x23fd8a4 e827c03901 call 0x37998d0
                s.pc = 0x23FD8A4; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd8a9 84c0 test al, al
                s.pc = 0x23FD8A9; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fd8ab 750c jne 0x23fd8b9
                s.pc = 0x23FD8AB; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD8B9 : 0x23FD8AD);
                }
            }
            case 0x23FD8AD: {
                {
                // 0x23fd8ad 4885f6 test rsi, rsi
                s.pc = 0x23FD8AD; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd8b0 0f844f020000 je 0x23fdb05
                s.pc = 0x23FD8B0; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD8B6);
                }
            }
            case 0x23FD8B6: {
                {
                // 0x23fd8b6 4532ff xor r15b, r15b
                s.pc = 0x23FD8B6; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                return s.transfer(0x23FD8B9);
                }
            }
            case 0x23FD8B9: {
                {
                // 0x23fd8b9 488b0b mov rcx, qword ptr [rbx]
                s.pc = 0x23FD8B9; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbx));
                }
                {
                // 0x23fd8bc 4881c1f0000000 add rcx, 0xf0
                s.pc = 0x23FD8BC; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = 0xF0L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fd8c3 4c8bc6 mov r8, rsi
                s.pc = 0x23FD8C3; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rsi;
                }
                {
                // 0x23fd8c6 488d9540040000 lea rdx, [rbp + 0x440]
                s.pc = 0x23FD8C6; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x440);
                }
                {
                // 0x23fd8cd e8febf3901 call 0x37998d0
                s.pc = 0x23FD8CD; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd8d2 84c0 test al, al
                s.pc = 0x23FD8D2; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fd8d4 750c jne 0x23fd8e2
                s.pc = 0x23FD8D4; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD8E2 : 0x23FD8D6);
                }
            }
            case 0x23FD8D6: {
                {
                // 0x23fd8d6 4885f6 test rsi, rsi
                s.pc = 0x23FD8D6; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd8d9 0f8426020000 je 0x23fdb05
                s.pc = 0x23FD8D9; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD8DF);
                }
            }
            case 0x23FD8DF: {
                {
                // 0x23fd8df 4532ff xor r15b, r15b
                s.pc = 0x23FD8DF; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                return s.transfer(0x23FD8E2);
                }
            }
            case 0x23FD8E2: {
                {
                // 0x23fd8e2 4883c310 add rbx, 0x10
                s.pc = 0x23FD8E2; s.context.beforeInstruction(s.pc);
                long left = s.r.rbx;
                long right = 0x10L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rbx = result;
                }
                {
                // 0x23fd8e6 488d43f8 lea rax, [rbx - 8]
                s.pc = 0x23FD8E6; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbx - 8);
                }
                {
                // 0x23fd8ea 483bc7 cmp rax, rdi
                s.pc = 0x23FD8EA; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rdi;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd8ed 75a1 jne 0x23fd890
                s.pc = 0x23FD8ED; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD890 : 0x23FD8EF);
                }
            }
            case 0x23FD8EF: {
                {
                // 0x23fd8ef 41807e3000 cmp byte ptr [r14 + 0x30], 0
                s.pc = 0x23FD8EF; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.r14 + 0x30)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd8f4 0f8497010000 je 0x23fda91
                s.pc = 0x23FD8F4; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDA91 : 0x23FD8FA);
                }
            }
            case 0x23FD8FA: {
                {
                // 0x23fd8fa 498b4e68 mov rcx, qword ptr [r14 + 0x68]
                s.pc = 0x23FD8FA; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14 + 0x68));
                }
                {
                // 0x23fd8fe 49634674 movsxd rax, dword ptr [r14 + 0x74]
                s.pc = 0x23FD8FE; s.context.beforeInstruction(s.pc);
                s.r.rax = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x74))));
                }
                {
                // 0x23fd902 488d14c1 lea rdx, [rcx + rax*8]
                s.pc = 0x23FD902; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rcx + s.r.rax*8);
                }
                {
                // 0x23fd906 33db xor ebx, ebx
                s.pc = 0x23FD906; s.context.beforeInstruction(s.pc);
                long left = (s.r.rbx & 0xFFFFFFFFL);
                long right = (s.r.rbx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rbx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd908 448bc3 mov r8d, ebx
                s.pc = 0x23FD908; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.rbx & 0xFFFFFFFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd90b 483bca cmp rcx, rdx
                s.pc = 0x23FD90B; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rdx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd90e 741d je 0x23fd92d
                s.pc = 0x23FD90E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD92D : 0x23FD910);
                }
            }
            case 0x23FD910: {
                {
                // 0x23fd910 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD910; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd913 4885c0 test rax, rax
                s.pc = 0x23FD913; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rax;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd916 740c je 0x23fd924
                s.pc = 0x23FD916; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD924 : 0x23FD918);
                }
            }
            case 0x23FD918: {
                {
                // 0x23fd918 8178384f624447 cmp dword ptr [rax + 0x38], 0x4744624f
                s.pc = 0x23FD918; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 0x38)));
                long right = 0x4744624FL;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd91f 7503 jne 0x23fd924
                s.pc = 0x23FD91F; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD924 : 0x23FD921);
                }
            }
            case 0x23FD921: {
                {
                // 0x23fd921 49ffc0 inc r8
                s.pc = 0x23FD921; s.context.beforeInstruction(s.pc);
                long left = s.r.r8;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.r8 = result;
                return s.transfer(0x23FD924);
                }
            }
            case 0x23FD924: {
                {
                // 0x23fd924 4883c108 add rcx, 8
                s.pc = 0x23FD924; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = 0x8L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fd928 483bca cmp rcx, rdx
                s.pc = 0x23FD928; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rdx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd92b 75e3 jne 0x23fd910
                s.pc = 0x23FD92B; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD910 : 0x23FD92D);
                }
            }
            case 0x23FD92D: {
                {
                // 0x23fd92d 498b5638 mov rdx, qword ptr [r14 + 0x38]
                s.pc = 0x23FD92D; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.r14 + 0x38));
                }
                {
                // 0x23fd931 4d634e44 movsxd r9, dword ptr [r14 + 0x44]
                s.pc = 0x23FD931; s.context.beforeInstruction(s.pc);
                s.r.r9 = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x44))));
                }
                {
                // 0x23fd935 4c03ca add r9, rdx
                s.pc = 0x23FD935; s.context.beforeInstruction(s.pc);
                long left = s.r.r9;
                long right = s.r.rdx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.r9 = result;
                }
                {
                // 0x23fd938 488bcb mov rcx, rbx
                s.pc = 0x23FD938; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd93b 493bd1 cmp rdx, r9
                s.pc = 0x23FD93B; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r9;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd93e 7415 je 0x23fd955
                s.pc = 0x23FD93E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD955 : 0x23FD940);
                }
            }
            case 0x23FD940: {
                {
                // 0x23fd940 488bc1 mov rax, rcx
                s.pc = 0x23FD940; s.context.beforeInstruction(s.pc);
                s.r.rax = s.r.rcx;
                }
                {
                // 0x23fd943 48ffc1 inc rcx
                s.pc = 0x23FD943; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.rcx = result;
                }
                {
                // 0x23fd946 803a07 cmp byte ptr [rdx], 7
                s.pc = 0x23FD946; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rdx)) & 0xFFL);
                long right = 0x7L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd949 480f44c8 cmove rcx, rax
                s.pc = 0x23FD949; s.context.beforeInstruction(s.pc);
                long value = s.r.rax;
                if (s.flags.zf(s.pc)) { s.r.rcx = value; }
                }
                {
                // 0x23fd94d 48ffc2 inc rdx
                s.pc = 0x23FD94D; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.rdx = result;
                }
                {
                // 0x23fd950 493bd1 cmp rdx, r9
                s.pc = 0x23FD950; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r9;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd953 75eb jne 0x23fd940
                s.pc = 0x23FD953; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD940 : 0x23FD955);
                }
            }
            case 0x23FD955: {
                {
                // 0x23fd955 443bc1 cmp r8d, ecx
                s.pc = 0x23FD955; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.rcx & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd958 0f8570000000 jne 0x23fd9ce
                s.pc = 0x23FD958; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD9CE : 0x23FD95E);
                }
            }
            case 0x23FD95E: {
                {
                // 0x23fd95e 498b8e80000000 mov rcx, qword ptr [r14 + 0x80]
                s.pc = 0x23FD95E; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.r14 + 0x80));
                }
                {
                // 0x23fd965 4963868c000000 movsxd rax, dword ptr [r14 + 0x8c]
                s.pc = 0x23FD965; s.context.beforeInstruction(s.pc);
                s.r.rax = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x8c))));
                }
                {
                // 0x23fd96c 488d14c1 lea rdx, [rcx + rax*8]
                s.pc = 0x23FD96C; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rcx + s.r.rax*8);
                }
                {
                // 0x23fd970 4c8bc3 mov r8, rbx
                s.pc = 0x23FD970; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rbx;
                }
                {
                // 0x23fd973 483bca cmp rcx, rdx
                s.pc = 0x23FD973; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rdx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd976 741d je 0x23fd995
                s.pc = 0x23FD976; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD995 : 0x23FD978);
                }
            }
            case 0x23FD978: {
                {
                // 0x23fd978 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FD978; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fd97b 4885c0 test rax, rax
                s.pc = 0x23FD97B; s.context.beforeInstruction(s.pc);
                long left = s.r.rax;
                long right = s.r.rax;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd97e 740c je 0x23fd98c
                s.pc = 0x23FD97E; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD98C : 0x23FD980);
                }
            }
            case 0x23FD980: {
                {
                // 0x23fd980 8178384f624447 cmp dword ptr [rax + 0x38], 0x4744624f
                s.pc = 0x23FD980; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.r.rax + 0x38)));
                long right = 0x4744624FL;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd987 7503 jne 0x23fd98c
                s.pc = 0x23FD987; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD98C : 0x23FD989);
                }
            }
            case 0x23FD989: {
                {
                // 0x23fd989 49ffc0 inc r8
                s.pc = 0x23FD989; s.context.beforeInstruction(s.pc);
                long left = s.r.r8;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.r8 = result;
                return s.transfer(0x23FD98C);
                }
            }
            case 0x23FD98C: {
                {
                // 0x23fd98c 4883c108 add rcx, 8
                s.pc = 0x23FD98C; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = 0x8L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rcx = result;
                }
                {
                // 0x23fd990 483bca cmp rcx, rdx
                s.pc = 0x23FD990; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long right = s.r.rdx;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd993 75e3 jne 0x23fd978
                s.pc = 0x23FD993; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD978 : 0x23FD995);
                }
            }
            case 0x23FD995: {
                {
                // 0x23fd995 498b5650 mov rdx, qword ptr [r14 + 0x50]
                s.pc = 0x23FD995; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.r14 + 0x50));
                }
                {
                // 0x23fd999 4d634e5c movsxd r9, dword ptr [r14 + 0x5c]
                s.pc = 0x23FD999; s.context.beforeInstruction(s.pc);
                s.r.r9 = (long)(int)(Integer.toUnsignedLong(s.memory.readDword((s.r.r14 + 0x5c))));
                }
                {
                // 0x23fd99d 4c03ca add r9, rdx
                s.pc = 0x23FD99D; s.context.beforeInstruction(s.pc);
                long left = s.r.r9;
                long right = s.r.rdx;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.r9 = result;
                }
                {
                // 0x23fd9a0 488bcb mov rcx, rbx
                s.pc = 0x23FD9A0; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rbx;
                }
                {
                // 0x23fd9a3 493bd1 cmp rdx, r9
                s.pc = 0x23FD9A3; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r9;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd9a6 741d je 0x23fd9c5
                s.pc = 0x23FD9A6; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FD9C5 : 0x23FD9A8);
                }
            }
            case 0x23FD9A8: {
                {
                // 0x23fd9a8 0f1f840000000000 nop dword ptr [rax + rax]
                s.pc = 0x23FD9A8; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FD9B0);
                }
            }
            case 0x23FD9B0: {
                {
                // 0x23fd9b0 488bc1 mov rax, rcx
                s.pc = 0x23FD9B0; s.context.beforeInstruction(s.pc);
                s.r.rax = s.r.rcx;
                }
                {
                // 0x23fd9b3 48ffc1 inc rcx
                s.pc = 0x23FD9B3; s.context.beforeInstruction(s.pc);
                long left = s.r.rcx;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.rcx = result;
                }
                {
                // 0x23fd9b6 803a07 cmp byte ptr [rdx], 7
                s.pc = 0x23FD9B6; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.rdx)) & 0xFFL);
                long right = 0x7L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fd9b9 480f44c8 cmove rcx, rax
                s.pc = 0x23FD9B9; s.context.beforeInstruction(s.pc);
                long value = s.r.rax;
                if (s.flags.zf(s.pc)) { s.r.rcx = value; }
                }
                {
                // 0x23fd9bd 48ffc2 inc rdx
                s.pc = 0x23FD9BD; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long result = left + 1L;
                s.flags.increment(left, result, 64);
                s.r.rdx = result;
                }
                {
                // 0x23fd9c0 493bd1 cmp rdx, r9
                s.pc = 0x23FD9C0; s.context.beforeInstruction(s.pc);
                long left = s.r.rdx;
                long right = s.r.r9;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fd9c3 75eb jne 0x23fd9b0
                s.pc = 0x23FD9C3; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FD9B0 : 0x23FD9C5);
                }
            }
            case 0x23FD9C5: {
                {
                // 0x23fd9c5 443bc1 cmp r8d, ecx
                s.pc = 0x23FD9C5; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.rcx & 0xFFFFFFFFL);
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fd9c8 0f84c3000000 je 0x23fda91
                s.pc = 0x23FD9C8; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDA91 : 0x23FD9CE);
                }
            }
            case 0x23FD9CE: {
                {
                // 0x23fd9ce 4885f6 test rsi, rsi
                s.pc = 0x23FD9CE; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fd9d1 0f842e010000 je 0x23fdb05
                s.pc = 0x23FD9D1; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FD9D7);
                }
            }
            case 0x23FD9D7: {
                {
                // 0x23fd9d7 4532ff xor r15b, r15b
                s.pc = 0x23FD9D7; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                }
                {
                // 0x23fd9da 488bce mov rcx, rsi
                s.pc = 0x23FD9DA; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fd9dd e8de385dfe call 0x9d12c0
                s.pc = 0x23FD9DD; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fd9e2 488d051ff43202 lea rax, [rip + 0x232f41f]
                s.pc = 0x23FD9E2; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472CE08L);
                }
                {
                // 0x23fd9e9 48894580 mov qword ptr [rbp - 0x80], rax
                s.pc = 0x23FD9E9; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x80), s.r.rax);
                }
                {
                // 0x23fd9ed c7458827000000 mov dword ptr [rbp - 0x78], 0x27
                s.pc = 0x23FD9ED; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x78), (int)(0x27L));
                }
                {
                // 0x23fd9f4 885d8c mov byte ptr [rbp - 0x74], bl
                s.pc = 0x23FD9F4; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x74), (int)((s.r.rbx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fd9f7 33d2 xor edx, edx
                s.pc = 0x23FD9F7; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd9f9 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FD9F9; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fd9ff 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FD9FF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fda06 e80595e201 call 0x4226f10
                s.pc = 0x23FDA06; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda0b 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FDA0B; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fda12 e8c9bf48fe call 0x8899e0
                s.pc = 0x23FDA12; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda17 90 nop
                s.pc = 0x23FDA17; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fda18 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FDA18; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fda1d 488d8590020000 lea rax, [rbp + 0x290]
                s.pc = 0x23FDA1D; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x290);
                }
                {
                // 0x23fda24 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FDA24; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fda29 4533c9 xor r9d, r9d
                s.pc = 0x23FDA29; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fda2c 4533c0 xor r8d, r8d
                s.pc = 0x23FDA2C; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fda2f 488d5580 lea rdx, [rbp - 0x80]
                s.pc = 0x23FDA2F; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x80);
                }
                {
                // 0x23fda33 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FDA33; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fda37 e8e48ba101 call 0x3e16620
                s.pc = 0x23FDA37; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda3c 90 nop
                s.pc = 0x23FDA3C; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fda3d 4883bd9002000000 cmp qword ptr [rbp + 0x290], 0
                s.pc = 0x23FDA3D; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x290));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fda45 7433 je 0x23fda7a
                s.pc = 0x23FDA45; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDA7A : 0x23FDA47);
                }
            }
            case 0x23FDA47: {
                {
                // 0x23fda47 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FDA47; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fda4e e87dc048fe call 0x889ad0
                s.pc = 0x23FDA4E; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda53 488b8da0020000 mov rcx, qword ptr [rbp + 0x2a0]
                s.pc = 0x23FDA53; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x2a0));
                }
                {
                // 0x23fda5a 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FDA5A; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fda5d 41b808000000 mov r8d, 8
                s.pc = 0x23FDA5D; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fda63 488b9590020000 mov rdx, qword ptr [rbp + 0x290]
                s.pc = 0x23FDA63; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x290));
                }
                {
                // 0x23fda6a ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FDA6A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda6d 48899d90020000 mov qword ptr [rbp + 0x290], rbx
                s.pc = 0x23FDA6D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x290), s.r.rbx);
                }
                {
                // 0x23fda74 899d98020000 mov dword ptr [rbp + 0x298], ebx
                s.pc = 0x23FDA74; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x298), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FDA7A);
                }
            }
            case 0x23FDA7A: {
                {
                // 0x23fda7a 488d55c0 lea rdx, [rbp - 0x40]
                s.pc = 0x23FDA7A; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fda7e 488bce mov rcx, rsi
                s.pc = 0x23FDA7E; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fda81 e80a8bb501 call 0x3f56590
                s.pc = 0x23FDA81; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda86 90 nop
                s.pc = 0x23FDA86; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fda87 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FDA87; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fda8b e8c08545fe call 0x856050
                s.pc = 0x23FDA8B; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fda90 90 nop
                s.pc = 0x23FDA90; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDA91);
                }
            }
            case 0x23FDA91: {
                {
                // 0x23fda91 0f57c0 xorps xmm0, xmm0
                s.pc = 0x23FDA91; s.context.beforeInstruction(s.pc);
                s.r.x0 = new Bits128(0L, 0L); // Source XORPS zeroing, no DF/MXCSR effect.
                }
                {
                // 0x23fda94 0f118510020000 movups xmmword ptr [rbp + 0x210], xmm0
                s.pc = 0x23FDA94; s.context.beforeInstruction(s.pc);
                s.memory.write128((s.r.rbp + 0x210), s.r.x0);
                }
                {
                // 0x23fda9b 0f118520020000 movups xmmword ptr [rbp + 0x220], xmm0
                s.pc = 0x23FDA9B; s.context.beforeInstruction(s.pc);
                s.memory.write128((s.r.rbp + 0x220), s.r.x0);
                }
                {
                // 0x23fdaa2 0f118530020000 movups xmmword ptr [rbp + 0x230], xmm0
                s.pc = 0x23FDAA2; s.context.beforeInstruction(s.pc);
                s.memory.write128((s.r.rbp + 0x230), s.r.x0);
                }
                {
                // 0x23fdaa9 0f118540020000 movups xmmword ptr [rbp + 0x240], xmm0
                s.pc = 0x23FDAA9; s.context.beforeInstruction(s.pc);
                s.memory.write128((s.r.rbp + 0x240), s.r.x0);
                }
                {
                // 0x23fdab0 0f118550020000 movups xmmword ptr [rbp + 0x250], xmm0
                s.pc = 0x23FDAB0; s.context.beforeInstruction(s.pc);
                s.memory.write128((s.r.rbp + 0x250), s.r.x0);
                }
                {
                // 0x23fdab7 488d9510020000 lea rdx, [rbp + 0x210]
                s.pc = 0x23FDAB7; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp + 0x210);
                }
                {
                // 0x23fdabe 498bce mov rcx, r14
                s.pc = 0x23FDABE; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.r14;
                }
                {
                // 0x23fdac1 e82a0c7c00 call 0x2bbe6f0
                s.pc = 0x23FDAC1; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdac6 4c8bc6 mov r8, rsi
                s.pc = 0x23FDAC6; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.r.rsi;
                }
                {
                // 0x23fdac9 488b9508060000 mov rdx, qword ptr [rbp + 0x608]
                s.pc = 0x23FDAC9; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x608));
                }
                {
                // 0x23fdad0 488d8d10020000 lea rcx, [rbp + 0x210]
                s.pc = 0x23FDAD0; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x210);
                }
                {
                // 0x23fdad7 e8140cd100 call 0x310e6f0
                s.pc = 0x23FDAD7; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdadc 84c0 test al, al
                s.pc = 0x23FDADC; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fdade 7508 jne 0x23fdae8
                s.pc = 0x23FDADE; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FDAE8 : 0x23FDAE0);
                }
            }
            case 0x23FDAE0: {
                {
                // 0x23fdae0 4885f6 test rsi, rsi
                s.pc = 0x23FDAE0; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fdae3 7420 je 0x23fdb05
                s.pc = 0x23FDAE3; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB05 : 0x23FDAE5);
                }
            }
            case 0x23FDAE5: {
                {
                // 0x23fdae5 4532ff xor r15b, r15b
                s.pc = 0x23FDAE5; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                return s.transfer(0x23FDAE8);
                }
            }
            case 0x23FDAE8: {
                {
                // 0x23fdae8 4180be2005000000 cmp byte ptr [r14 + 0x520], 0
                s.pc = 0x23FDAE8; s.context.beforeInstruction(s.pc);
                long left = (s.memory.readUnsignedByte((s.r.r14 + 0x520)) & 0xFFL);
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 8, true);
                }
                {
                // 0x23fdaf0 7416 je 0x23fdb08
                s.pc = 0x23FDAF0; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDB08 : 0x23FDAF2);
                }
            }
            case 0x23FDAF2: {
                {
                // 0x23fdaf2 498d8ec8010000 lea rcx, [r14 + 0x1c8]
                s.pc = 0x23FDAF2; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.r14 + 0x1c8);
                }
                {
                // 0x23fdaf9 488bd6 mov rdx, rsi
                s.pc = 0x23FDAF9; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.r.rsi;
                }
                {
                // 0x23fdafc e85f26f3ff call 0x2330160
                s.pc = 0x23FDAFC; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdb01 84c0 test al, al
                s.pc = 0x23FDB01; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left & right;
                s.flags.logic(result, 8);
                }
                {
                // 0x23fdb03 7503 jne 0x23fdb08
                s.pc = 0x23FDB03; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FDB08 : 0x23FDB05);
                }
            }
            case 0x23FDB05: {
                {
                // 0x23fdb05 4532ff xor r15b, r15b
                s.pc = 0x23FDB05; s.context.beforeInstruction(s.pc);
                long left = (s.r.r15 & 0xFFL);
                long right = (s.r.r15 & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.r15 = (s.r.r15 & ~0xFFL) | ((result) & 0xFFL);
                return s.transfer(0x23FDB08);
                }
            }
            case 0x23FDB08: {
                {
                // 0x23fdb08 488d8d40040000 lea rcx, [rbp + 0x440]
                s.pc = 0x23FDB08; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x440);
                }
                {
                // 0x23fdb0f e8cc0548fe call 0x87e0e0
                s.pc = 0x23FDB0F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdb14 410fb6c7 movzx eax, r15b
                s.pc = 0x23FDB14; s.context.beforeInstruction(s.pc);
                s.r.rax = ((s.r.r15 & 0xFFL)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb18 e9ea000000 jmp 0x23fdc07
                s.pc = 0x23FDB18; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDC07);
                }
            }
            case 0x23FDB1D: {
                {
                // 0x23fdb1d 4885f6 test rsi, rsi
                s.pc = 0x23FDB1D; s.context.beforeInstruction(s.pc);
                long left = s.r.rsi;
                long right = s.r.rsi;
                long result = left & right;
                s.flags.logic(result, 64);
                }
                {
                // 0x23fdb20 0f84df000000 je 0x23fdc05
                s.pc = 0x23FDB20; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDC05 : 0x23FDB26);
                }
            }
            case 0x23FDB26: {
                {
                // 0x23fdb26 488d050bf50802 lea rax, [rip + 0x208f50b]
                s.pc = 0x23FDB26; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x448D038L);
                }
                {
                // 0x23fdb2d 48894580 mov qword ptr [rbp - 0x80], rax
                s.pc = 0x23FDB2D; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x80), s.r.rax);
                }
                {
                // 0x23fdb31 41bc01000000 mov r12d, 1
                s.pc = 0x23FDB31; s.context.beforeInstruction(s.pc);
                s.r.r12 = (0x1L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb37 44896588 mov dword ptr [rbp - 0x78], r12d
                s.pc = 0x23FDB37; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x78), (int)((s.r.r12 & 0xFFFFFFFFL)));
                }
                {
                // 0x23fdb3b 885d8c mov byte ptr [rbp - 0x74], bl
                s.pc = 0x23FDB3B; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x74), (int)((s.r.rbx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fdb3e 488d5580 lea rdx, [rbp - 0x80]
                s.pc = 0x23FDB3E; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x80);
                }
                {
                // 0x23fdb42 488bce mov rcx, rsi
                s.pc = 0x23FDB42; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fdb45 e81696b501 call 0x3f57160
                s.pc = 0x23FDB45; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdb4a 488d05fff53202 lea rax, [rip + 0x232f5ff]
                s.pc = 0x23FDB4A; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.image + 0x472D150L);
                }
                {
                // 0x23fdb51 48894580 mov qword ptr [rbp - 0x80], rax
                s.pc = 0x23FDB51; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp - 0x80), s.r.rax);
                }
                {
                // 0x23fdb55 c7458815000000 mov dword ptr [rbp - 0x78], 0x15
                s.pc = 0x23FDB55; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp - 0x78), (int)(0x15L));
                }
                {
                // 0x23fdb5c 885d8c mov byte ptr [rbp - 0x74], bl
                s.pc = 0x23FDB5C; s.context.beforeInstruction(s.pc);
                s.memory.writeByte((s.r.rbp - 0x74), (int)((s.r.rbx & 0xFFL)) & 0xFF);
                }
                {
                // 0x23fdb5f 33d2 xor edx, edx
                s.pc = 0x23FDB5F; s.context.beforeInstruction(s.pc);
                long left = (s.r.rdx & 0xFFFFFFFFL);
                long right = (s.r.rdx & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.rdx = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb61 41b8a8010000 mov r8d, 0x1a8
                s.pc = 0x23FDB61; s.context.beforeInstruction(s.pc);
                s.r.r8 = (0x1A8L) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb67 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FDB67; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fdb6e e89d93e201 call 0x4226f10
                s.pc = 0x23FDB6E; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdb73 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FDB73; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fdb7a e861be48fe call 0x8899e0
                s.pc = 0x23FDB7A; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdb7f 90 nop
                s.pc = 0x23FDB7F; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fdb80 48895c2428 mov qword ptr [rsp + 0x28], rbx
                s.pc = 0x23FDB80; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x28), s.r.rbx);
                }
                {
                // 0x23fdb85 488d8590020000 lea rax, [rbp + 0x290]
                s.pc = 0x23FDB85; s.context.beforeInstruction(s.pc);
                s.r.rax = (s.r.rbp + 0x290);
                }
                {
                // 0x23fdb8c 4889442420 mov qword ptr [rsp + 0x20], rax
                s.pc = 0x23FDB8C; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rsp + 0x20), s.r.rax);
                }
                {
                // 0x23fdb91 4533c9 xor r9d, r9d
                s.pc = 0x23FDB91; s.context.beforeInstruction(s.pc);
                long left = (s.r.r9 & 0xFFFFFFFFL);
                long right = (s.r.r9 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r9 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb94 4533c0 xor r8d, r8d
                s.pc = 0x23FDB94; s.context.beforeInstruction(s.pc);
                long left = (s.r.r8 & 0xFFFFFFFFL);
                long right = (s.r.r8 & 0xFFFFFFFFL);
                long result = left ^ right;
                s.flags.logic(result, 32);
                s.r.r8 = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdb97 488d5580 lea rdx, [rbp - 0x80]
                s.pc = 0x23FDB97; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x80);
                }
                {
                // 0x23fdb9b 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FDB9B; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fdb9f e87c8aa101 call 0x3e16620
                s.pc = 0x23FDB9F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdba4 90 nop
                s.pc = 0x23FDBA4; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fdba5 4883bd9002000000 cmp qword ptr [rbp + 0x290], 0
                s.pc = 0x23FDBA5; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp + 0x290));
                long right = 0x0L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fdbad 7432 je 0x23fdbe1
                s.pc = 0x23FDBAD; s.context.beforeInstruction(s.pc);
                return s.transfer((s.flags.zf(s.pc)) ? 0x23FDBE1 : 0x23FDBAF);
                }
            }
            case 0x23FDBAF: {
                {
                // 0x23fdbaf 488d8d90020000 lea rcx, [rbp + 0x290]
                s.pc = 0x23FDBAF; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp + 0x290);
                }
                {
                // 0x23fdbb6 e815bf48fe call 0x889ad0
                s.pc = 0x23FDBB6; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdbbb 488b8da0020000 mov rcx, qword ptr [rbp + 0x2a0]
                s.pc = 0x23FDBBB; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.memory.readQword((s.r.rbp + 0x2a0));
                }
                {
                // 0x23fdbc2 488b01 mov rax, qword ptr [rcx]
                s.pc = 0x23FDBC2; s.context.beforeInstruction(s.pc);
                s.r.rax = s.memory.readQword((s.r.rcx));
                }
                {
                // 0x23fdbc5 458d442407 lea r8d, [r12 + 7]
                s.pc = 0x23FDBC5; s.context.beforeInstruction(s.pc);
                s.r.r8 = ((s.r.r12 + 7)) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdbca 488b9590020000 mov rdx, qword ptr [rbp + 0x290]
                s.pc = 0x23FDBCA; s.context.beforeInstruction(s.pc);
                s.r.rdx = s.memory.readQword((s.r.rbp + 0x290));
                }
                {
                // 0x23fdbd1 ff5010 call qword ptr [rax + 0x10]
                s.pc = 0x23FDBD1; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdbd4 48899d90020000 mov qword ptr [rbp + 0x290], rbx
                s.pc = 0x23FDBD4; s.context.beforeInstruction(s.pc);
                s.memory.writeQword((s.r.rbp + 0x290), s.r.rbx);
                }
                {
                // 0x23fdbdb 899d98020000 mov dword ptr [rbp + 0x298], ebx
                s.pc = 0x23FDBDB; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.r.rbp + 0x298), (int)((s.r.rbx & 0xFFFFFFFFL)));
                return s.transfer(0x23FDBE1);
                }
            }
            case 0x23FDBE1: {
                {
                // 0x23fdbe1 488d55c0 lea rdx, [rbp - 0x40]
                s.pc = 0x23FDBE1; s.context.beforeInstruction(s.pc);
                s.r.rdx = (s.r.rbp - 0x40);
                }
                {
                // 0x23fdbe5 48837dd810 cmp qword ptr [rbp - 0x28], 0x10
                s.pc = 0x23FDBE5; s.context.beforeInstruction(s.pc);
                long left = s.memory.readQword((s.r.rbp - 0x28));
                long right = 0x10L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 64, true);
                }
                {
                // 0x23fdbea 480f4355c0 cmovae rdx, qword ptr [rbp - 0x40]
                s.pc = 0x23FDBEA; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword((s.r.rbp - 0x40));
                if (!s.flags.cf(s.pc)) { s.r.rdx = value; }
                }
                {
                // 0x23fdbef 4c8b45d0 mov r8, qword ptr [rbp - 0x30]
                s.pc = 0x23FDBEF; s.context.beforeInstruction(s.pc);
                s.r.r8 = s.memory.readQword((s.r.rbp - 0x30));
                }
                {
                // 0x23fdbf3 488bce mov rcx, rsi
                s.pc = 0x23FDBF3; s.context.beforeInstruction(s.pc);
                s.r.rcx = s.r.rsi;
                }
                {
                // 0x23fdbf6 e8d58348fe call 0x885fd0
                s.pc = 0x23FDBF6; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdbfb 90 nop
                s.pc = 0x23FDBFB; s.context.beforeInstruction(s.pc);
                }
                {
                // 0x23fdbfc 488d4dc0 lea rcx, [rbp - 0x40]
                s.pc = 0x23FDBFC; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.r.rbp - 0x40);
                return s.transfer(0x23FDC00);
                }
            }
            case 0x23FDC00: {
                {
                // 0x23fdc00 e84b8445fe call 0x856050
                s.pc = 0x23FDC00; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                return s.transfer(0x23FDC05);
                }
            }
            case 0x23FDC05: {
                {
                // 0x23fdc05 32c0 xor al, al
                s.pc = 0x23FDC05; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFL);
                long right = (s.r.rax & 0xFFL);
                long result = left ^ right;
                s.flags.logic(result, 8);
                s.r.rax = (s.r.rax & ~0xFFL) | ((result) & 0xFFL);
                return s.transfer(0x23FDC07);
                }
            }
            case 0x23FDC07: {
                {
                // 0x23fdc07 488b9c24f8060000 mov rbx, qword ptr [rsp + 0x6f8]
                s.pc = 0x23FDC07; s.context.beforeInstruction(s.pc);
                s.r.rbx = s.memory.readQword((s.r.rsp + 0x6f8));
                }
                {
                // 0x23fdc0f 4881c4b0060000 add rsp, 0x6b0
                s.pc = 0x23FDC0F; s.context.beforeInstruction(s.pc);
                long left = s.r.rsp;
                long right = 0x6B0L;
                long result = left + right;
                s.flags.arithmetic(left, right, result, 64, false);
                s.r.rsp = result;
                }
                {
                // 0x23fdc16 415f pop r15
                s.pc = 0x23FDC16; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.r15 = value;
                }
                {
                // 0x23fdc18 415e pop r14
                s.pc = 0x23FDC18; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.r14 = value;
                }
                {
                // 0x23fdc1a 415d pop r13
                s.pc = 0x23FDC1A; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.r13 = value;
                }
                {
                // 0x23fdc1c 415c pop r12
                s.pc = 0x23FDC1C; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.r12 = value;
                }
                {
                // 0x23fdc1e 5f pop rdi
                s.pc = 0x23FDC1E; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.rdi = value;
                }
                {
                // 0x23fdc1f 5e pop rsi
                s.pc = 0x23FDC1F; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.rsi = value;
                }
                {
                // 0x23fdc20 5d pop rbp
                s.pc = 0x23FDC20; s.context.beforeInstruction(s.pc);
                long value = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.r.rbp = value;
                }
                {
                // 0x23fdc21 c3 ret
                s.pc = 0x23FDC21; s.context.beforeInstruction(s.pc);
                long returnRip = s.memory.readQword(s.r.rsp);
                s.r.rsp += 8L;
                s.outcome = s.context.finishNormal(returnRip);
                return -1;
                }
            }
            case 0x23FDC22: {
                {
                // 0x23fdc22 e8494ee301 call 0x4232a70
                s.pc = 0x23FDC22; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdc27 90 nop
                s.pc = 0x23FDC27; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FDC28);
                }
            }
            case 0x23FDC28: {
                {
                // 0x23fdc28 488d0d959b8603 lea rcx, [rip + 0x3869b95]
                s.pc = 0x23FDC28; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.image + 0x5C677C4L);
                }
                {
                // 0x23fdc2f e8505ee201 call 0x4223a84
                s.pc = 0x23FDC2F; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdc34 833d899b8603ff cmp dword ptr [rip + 0x3869b89], -1
                s.pc = 0x23FDC34; s.context.beforeInstruction(s.pc);
                long left = Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5C677C4L)));
                long right = -0x1L;
                long result = left - right;
                s.flags.arithmetic(left, right, result, 32, true);
                }
                {
                // 0x23fdc3b 0f8551f1ffff jne 0x23fcd92
                s.pc = 0x23FDC3B; s.context.beforeInstruction(s.pc);
                return s.transfer((!s.flags.zf(s.pc)) ? 0x23FCD92 : 0x23FDC41);
                }
            }
            case 0x23FDC41: {
                {
                // 0x23fdc41 8b0561218603 mov eax, dword ptr [rip + 0x3862161]
                s.pc = 0x23FDC41; s.context.beforeInstruction(s.pc);
                s.r.rax = (Integer.toUnsignedLong(s.memory.readDword((s.image + 0x5C5FDA8L)))) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdc47 89057b9b8603 mov dword ptr [rip + 0x3869b7b], eax
                s.pc = 0x23FDC47; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.image + 0x5C677C8L), (int)((s.r.rax & 0xFFFFFFFFL)));
                }
                {
                // 0x23fdc4d ffc0 inc eax
                s.pc = 0x23FDC4D; s.context.beforeInstruction(s.pc);
                long left = (s.r.rax & 0xFFFFFFFFL);
                long result = left + 1L;
                s.flags.increment(left, result, 32);
                s.r.rax = (result) & 0xFFFFFFFFL;
                }
                {
                // 0x23fdc4f 890553218603 mov dword ptr [rip + 0x3862153], eax
                s.pc = 0x23FDC4F; s.context.beforeInstruction(s.pc);
                s.memory.writeDword((s.image + 0x5C5FDA8L), (int)((s.r.rax & 0xFFFFFFFFL)));
                }
                {
                // 0x23fdc55 488d0d689b8603 lea rcx, [rip + 0x3869b68]
                s.pc = 0x23FDC55; s.context.beforeInstruction(s.pc);
                s.r.rcx = (s.image + 0x5C677C4L);
                }
                {
                // 0x23fdc5c e8c35de201 call 0x4223a24
                s.pc = 0x23FDC5C; s.context.beforeInstruction(s.pc);
                QueueFp604Api.Outcome offered = ActivityCallProtocol264Api.invokeOwnedCall(s.pc, s.binding, s.opaqueCalls);
                if (offered instanceof QueueFp604Api.Stopped) { s.outcome = offered; return -1; }
                s.flags.invalidate();
                }
                {
                // 0x23fdc61 e92cf1ffff jmp 0x23fcd92
                s.pc = 0x23FDC61; s.context.beforeInstruction(s.pc);
                return s.transfer(0x23FCD92);
                }
            }
            default: throw new UnsupportedOperationException("Not a normal activity source block: " + Integer.toHexString(s.pc));
        }
    }
}
