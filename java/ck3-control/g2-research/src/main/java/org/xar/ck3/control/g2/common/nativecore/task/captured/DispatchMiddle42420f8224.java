package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle219Api;
import org.xar.ck3.research.m3.dispatch219.DispatchMiddle42420F8;
import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.retained.InGameIdlerEventDispatch;

public final class DispatchMiddle42420f8224 {
    private DispatchMiddle42420f8224() { }

    public interface Memory32 extends TerminalTailTarget42421c8213.Memory16 {
        int exchangeDword(long address, int value);
    }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            Memory32 memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        Frame f = new Frame(entry, memory, calls);

        // 1. Physical prologue: save INCOMING NV.RBX to [E-8]
        // E = entry.rspBits(). Work = E - 0x28.
        // [E-8] is work + 0x20.
        f.memory.writeQword(f.work + 0x20L, f.entry.nonvolatileBits().rbxBits());

        // 2. Invoke DispatchMiddle42420F8 business logic exactly once
        // Input: moduleBase = image, rcxAddress = entry.volatileBits().rcxBits()
        DispatchMiddle219Api.Input input = new DispatchMiddle219Api.Input(
            f.image,
            f.v.rcxBits()
        );

        // Ports3 implementation
        Ports3 ports = new Ports3(f);
        // Memory8 view implementation
        Memory8 memView = new Memory8(f);

        DispatchMiddle42420F8.execute(memView, ports, input);

        // 3. Outcome handling (NormalReturn path)
        // Fresh physical reads in source order for epilogue
        // RBX read from [E-8] = work + 0x20
        long rbx = f.memory.readQword(f.work + 0x20L);

        // Construct restored NonvolatileBits
        // RBX: from fresh read at [E-8]
        // RBP, RSI, RDI, R12, R13, R14, R15, XMM6: from Entry (as they are not modified by the prologue/epilogue in this specific frame layout description, or preserved)
        // Note: The prompt says "remainingNVentry/XMM6". This implies using Entry's values for non-RBX non-volatile registers.
        GovernmentPrimaryTail155Api.NonvolatileBits restoredNV = new GovernmentPrimaryTail155Api.NonvolatileBits(
            rbx,
            entry.nonvolatileBits().rbpBits(),
            entry.nonvolatileBits().rsiBits(),
            entry.nonvolatileBits().rdiBits(),
            entry.nonvolatileBits().r12Bits(),
            entry.nonvolatileBits().r13Bits(),
            entry.nonvolatileBits().r14Bits(),
            entry.nonvolatileBits().r15Bits(),
            entry.nonvolatileBits().xmm6()
        );

        // Return RIP: The prompt says "freshRETQ[E]".
        // The return address is at [E].
        long retRip = f.memory.readQword(f.e);

        // Caller RSP: E + 8 (after pop and ret? No, ret pops the return address, so RSP becomes E+8?
        // Wait. Entry RSP = E.
        // Push RBX: RSP = E-8.
        // Sub 0x20: RSP = E-0x28.
        // ... business ...
        // Add 0x20: RSP = E-8.
        // Pop RBX: RSP = E.
        // Ret: Pops return address from [E], RSP becomes E+8.
        // So Caller RSP is E+8.

        return new GovernmentCrtBoundary185Api.NormalReturn(
            f.v, // Current whole V from latest actual source effect
            retRip,
            f.e + 8L,
            restoredNV
        );
    }

    private static final class Frame {
        final GovernmentCrtBoundary185Api.Entry entry;
        final Memory32 memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        final long e, image, work;
        final GovernmentPrimaryTail155Api.NonvolatileBits activeNV;
        GovernmentPrimaryTail155Api.VolatileBits v;
        private static final int FLAG = 0, EXCHANGE = 1, FIRST_POINTER = 2,
                FIRST_DWORD = 3, COOKIE_A = 4, COOKIE_B = 5, MAYBE_IAT = 6,
                EXPECT_INDIRECT = 7, EXPECT_DE88 = 8, SECOND_POINTER = 9,
                SECOND_DWORD = 10, AFTER_SECOND_DWORD = 11, THIRD_POINTER = 12,
                THIRD_DWORD = 13, AFTER_THIRD_DWORD = 14, FOURTH_POINTER = 15,
                FINAL_BYTE = 16, DONE = 17;
        int phase;

        Frame(GovernmentCrtBoundary185Api.Entry entry, Memory32 memory, GovernmentCrtBoundary185Api.Calls calls) {
            this.entry = Objects.requireNonNull(entry);
            this.memory = Objects.requireNonNull(memory);
            this.calls = Objects.requireNonNull(calls);
            this.e = entry.rspBits();
            this.image = entry.imageBaseBits();
            this.work = this.e - 0x28L;
            this.v = entry.volatileBits();
            this.phase = 0;

            // Active NV: RBX=entryRCX (full 64-bit), others from entry
            long rbx = this.v.rcxBits();
            this.activeNV = new GovernmentPrimaryTail155Api.NonvolatileBits(
                rbx,
                entry.nonvolatileBits().rbpBits(),
                entry.nonvolatileBits().rsiBits(),
                entry.nonvolatileBits().rdiBits(),
                entry.nonvolatileBits().r12Bits(),
                entry.nonvolatileBits().r13Bits(),
                entry.nonvolatileBits().r14Bits(),
                entry.nonvolatileBits().r15Bits(),
                entry.nonvolatileBits().xmm6()
            );
        }

        void requirePhase(int expected) {
            if (phase != expected) {
                throw new IllegalStateException("Unexpected 42420F8 source phase " + phase);
            }
        }

        void args(long rax, long rcx, long rdx, long r8, long r9) {
            v = new GovernmentPrimaryTail155Api.VolatileBits(
                rax, rcx, rdx, r8, r9, v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5()
            );
        }

        long invoke(long site, GovernmentCrtBoundary185Api.TargetKind kind, long target, int instructionLength) {
            // Write return address to [work-8] = [E-0x30]
            // Prompt: "EverycallwriteQ[work-8]=I+site+len"
            memory.writeQword(work - 8L, image + site + instructionLength);

            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site, kind, target, work, v, activeNV
            );

            GovernmentPrimaryTail155Api.VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            v = returned;
            return returned.raxBits();
        }
    }

    private static final class Memory8 implements DispatchMiddle219Api.Memory {
        private final Frame f;
        Memory8(Frame f) { this.f = Objects.requireNonNull(f); }

        public long readPointer(long address) {
            int role = f.phase;
            if (role != Frame.FIRST_POINTER && role != Frame.COOKIE_A
                    && role != Frame.COOKIE_B && role != Frame.MAYBE_IAT
                    && role != Frame.SECOND_POINTER && role != Frame.THIRD_POINTER
                    && role != Frame.FOURTH_POINTER) {
                throw new IllegalStateException("Unexpected 42420F8 QWORD source phase " + role);
            }
            long value = f.memory.readQword(address);
            switch (role) {
                case Frame.FIRST_POINTER:
                    f.args(value, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.FIRST_DWORD;
                    break;
                case Frame.COOKIE_A:
                    f.args(value, value & 63L, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.COOKIE_B;
                    break;
                case Frame.COOKIE_B:
                    f.args(f.v.raxBits(), f.v.rcxBits(), value, f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.MAYBE_IAT;
                    break;
                case Frame.MAYBE_IAT:
                    // The old body fetched a code target, not a MOV into RAX.
                    f.phase = Frame.EXPECT_INDIRECT;
                    break;
                case Frame.SECOND_POINTER:
                    f.args(value, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.SECOND_DWORD;
                    break;
                case Frame.THIRD_POINTER:
                    f.args(value, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.THIRD_DWORD;
                    break;
                case Frame.FOURTH_POINTER:
                    f.args(value, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
                    f.phase = Frame.FINAL_BYTE;
                    break;
                default:
                    throw new AssertionError("Unreachable QWORD source phase");
            }
            return value;
        }

        public int readInt32(long address) {
            int role = f.phase;
            if (role != Frame.FIRST_DWORD && role != Frame.SECOND_DWORD
                    && role != Frame.THIRD_DWORD) {
                throw new IllegalStateException("Unexpected 42420F8 DWORD source phase " + role);
            }
            int value = f.memory.readDword(address);
            if (role == Frame.FIRST_DWORD) {
                f.args(f.v.raxBits(), Integer.toUnsignedLong(value), f.v.rdxBits(),
                        f.v.r8Bits(), f.v.r9Bits());
                // Only classify the already observed old-body event stream.
                f.phase = value == 0 ? Frame.COOKIE_A
                        : value == 1 ? Frame.EXPECT_DE88 : Frame.SECOND_POINTER;
            } else if (role == Frame.SECOND_DWORD) {
                // CMP [RAX],0 changes no represented volatile register.
                f.phase = Frame.AFTER_SECOND_DWORD;
            } else {
                f.phase = Frame.AFTER_THIRD_DWORD;
            }
            return value;
        }

        public void writeInt32(long address, int value) {
            f.memory.writeDword(address, value);
        }

        public void writeInt64(long address, long value) {
            f.memory.writeQword(address, value);
        }

        public int readUnsigned8(long address) {
            f.requirePhase(Frame.FLAG);
            int value = f.memory.readUnsignedByte(address);
            f.phase = value == 0 ? Frame.EXCHANGE : Frame.DONE;
            return value;
        }

        public int readUnsigned16(long address) {
            return f.memory.readUnsigned16(address);
        }

        public void write8(long address, int value) {
            int role = f.phase;
            if (role != Frame.AFTER_THIRD_DWORD && role != Frame.FINAL_BYTE) {
                throw new IllegalStateException("Unexpected 42420F8 BYTE-write source phase " + role);
            }
            f.memory.writeByte(address, value);
            f.phase = role == Frame.AFTER_THIRD_DWORD ? Frame.FOURTH_POINTER : Frame.DONE;
        }

        public void exchangeInt32(long address, int value) {
            f.requirePhase(Frame.EXCHANGE);
            int old = f.memory.exchangeDword(address, value);
            f.args(Integer.toUnsignedLong(old), f.v.rcxBits(), f.v.rdxBits(),
                    f.v.r8Bits(), f.v.r9Bits());
            f.phase = Frame.FIRST_POINTER;
        }
    }

    private static final class Ports3 implements DispatchMiddle219Api.Ports {
        final Frame f;
        Ports3(Frame f) { this.f = f; }

        public void call43dbba8(DispatchMiddle219Api.Memory m, long siteRva, long actualTarget,
                               long liveRax, int ecx, int edx, int r8d) {
            // Source: 4242147. Len 6. Kind: INDIRECT_ABSOLUTE (IAT read).
            // Args: RAX=liveRax, RCX=0, RDX=0, R8=0.
            // Prompt: "sourceRAX=oldpasseddecoded,RCX/RDX/R8D=0; preserveallothercurrentV"
            f.requirePhase(Frame.EXPECT_INDIRECT);
            f.args(liveRax, 0L, 0L, 0L, f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
            f.phase = Frame.EXPECT_DE88;
        }

        public void call424de88(DispatchMiddle219Api.Memory m, long siteRva, long rcx) {
            // Source: 4242162. Len 5. Kind: DIRECT_RVA.
            // Args: RCX=passed global argument.
            // Prompt: "DE88@4242162 len5 onlysetRCX=passedglobalargument, othercurrentVcarry"
            if (f.phase != Frame.MAYBE_IAT && f.phase != Frame.EXPECT_DE88) {
                throw new IllegalStateException("Unexpected 4242162 source phase " + f.phase);
            }
            f.args(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424DE88L, 5);
            f.phase = Frame.SECOND_POINTER;
        }

        public void call424e1ac(DispatchMiddle219Api.Memory m, long siteRva, long rcx, long rdx) {
            // Source: 424217E or 4242191. Len 5. Kind: DIRECT_RVA.
            // Args: RCX/RDX=oldpassedargs.
            // Prompt: "E1AC@424217E and4242191 len5 setRCX/RDX=oldpassedargs, otherVcarry"
            f.requirePhase(Frame.AFTER_SECOND_DWORD);
            if (siteRva != 0x424217EL && siteRva != 0x4242191L) {
                throw new IllegalStateException("Unexpected 424E1AC source site");
            }
            f.args(f.v.raxBits(), rcx, rdx, f.v.r8Bits(), f.v.r9Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x424E1ACL, 5);
            f.phase = siteRva == 0x4242191L ? Frame.THIRD_POINTER : Frame.AFTER_SECOND_DWORD;
        }
    }
}