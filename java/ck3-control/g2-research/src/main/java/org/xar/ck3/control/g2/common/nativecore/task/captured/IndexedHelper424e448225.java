package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;

public final class IndexedHelper424e448225 {
    private IndexedHelper424e448225() { }

    public interface Memory64 extends GovernmentCrtBoundary185Api.Memory {
        long exchangeQword(long address, long value);
    }

    private enum Phase {
        ENCODED_Q, INITIAL_COOKIE_Q, AFTER_INITIAL,
        MODULE_CACHE_Q, PATH_Q, LOAD_IAT_Q, LOAD_PORT,
        ERROR_IAT_Q, ERROR_PORT, WORD1_PORT, WORD2_PORT, RETRY_IAT_Q, RETRY_PORT,
        MODULE_FAIL_XCHG, MODULE_SUCCESS_XCHG, NEXT_INDEX_OR_EXHAUST,
        UNLOAD_IAT_Q, UNLOAD_PORT, MODULE_COOKIE_Q, RESOLVE_IAT_Q, RESOLVE_PORT,
        SUCCESS_COOKIE_Q, SUCCESS_XCHG, FAIL_COOKIE_Q, FAIL_XCHG,
        DONE_SUCCESS, DONE_FAILURE
    }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            Memory64 memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        Frame f = new Frame(entry, memory, calls);
        f.prologue();

        long result = IndexedLookupHelper424E448.execute(
            new MemoryView(f),
            new PortsView(f),
            new IndexedHelper225Api.Input(
                f.image,
                (int) entry.volatileBits().rcxBits(),
                entry.volatileBits().rdxBits(),
                entry.volatileBits().r8Bits(),
                entry.volatileBits().r9Bits()
            )
        );

        return f.finish(result);
    }

    private static final class Frame {
        final GovernmentCrtBoundary185Api.Entry entry;
        final Memory64 memory;
        final GovernmentCrtBoundary185Api.Calls calls;
        final long e, image, work;
        GovernmentPrimaryTail155Api.VolatileBits v;
        long rbx, rbp, rsi, rdi, r12, r13, r14, r15;
        Phase phase;

        Frame(GovernmentCrtBoundary185Api.Entry entry, Memory64 memory, GovernmentCrtBoundary185Api.Calls calls) {
            this.entry = Objects.requireNonNull(entry);
            this.memory = Objects.requireNonNull(memory);
            this.calls = Objects.requireNonNull(calls);
            this.e = entry.rspBits();
            this.image = entry.imageBaseBits();
            this.work = this.e - 0x48L;
            this.v = entry.volatileBits();
            this.phase = Phase.ENCODED_Q;

            GovernmentPrimaryTail155Api.NonvolatileBits incomingNV = entry.nonvolatileBits();
            this.rbx = incomingNV.rbxBits();
            this.rbp = incomingNV.rbpBits();
            this.rsi = incomingNV.rsiBits();
            this.rdi = incomingNV.rdiBits();
            this.r12 = incomingNV.r12Bits();
            this.r13 = incomingNV.r13Bits();
            this.r14 = incomingNV.r14Bits();
            this.r15 = incomingNV.r15Bits();

            // Source setup changes
            this.r15 = Integer.toUnsignedLong((int) entry.volatileBits().rcxBits());
            this.r14 = this.image;
            this.r12 = entry.volatileBits().r9Bits();
            this.rbp = entry.volatileBits().r8Bits();
            this.r13 = entry.volatileBits().rdxBits();
        }

        void prologue() {
            GovernmentPrimaryTail155Api.NonvolatileBits incomingNV = entry.nonvolatileBits();
            memory.writeQword(e + 8L, incomingNV.rbxBits());
            memory.writeQword(e + 0x10L, incomingNV.rbpBits());
            memory.writeQword(e + 0x18L, incomingNV.rsiBits());
            memory.writeQword(e - 8L, incomingNV.rdiBits());
            memory.writeQword(e - 0x10L, incomingNV.r12Bits());
            memory.writeQword(e - 0x18L, incomingNV.r13Bits());
            memory.writeQword(e - 0x20L, incomingNV.r14Bits());
            memory.writeQword(e - 0x28L, incomingNV.r15Bits());
        }

        void v6(long rax, long rcx, long rdx, long r8, long r9, long r10) {
            this.v = new GovernmentPrimaryTail155Api.VolatileBits(
                rax, rcx, rdx, r8, r9, r10,
                this.v.r11Bits(),
                this.v.xmm0(), this.v.xmm1(), this.v.xmm2(),
                this.v.xmm3(), this.v.xmm4(), this.v.xmm5()
            );
        }

        GovernmentPrimaryTail155Api.NonvolatileBits activeNv() {
            return new GovernmentPrimaryTail155Api.NonvolatileBits(
                this.rbx, this.rbp, this.rsi, this.rdi,
                this.r12, this.r13, this.r14, this.r15,
                entry.nonvolatileBits().xmm6()
            );
        }

        long invoke(long site, GovernmentCrtBoundary185Api.TargetKind kind, long target, int length) {
            memory.writeQword(work - 8L, image + site + length);
            GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                site, kind, target, work, this.v, activeNv()
            );
            GovernmentPrimaryTail155Api.VolatileBits returned = calls.invoke(call);
            Objects.requireNonNull(returned);
            this.v = returned;
            return returned.raxBits();
        }

        void require(Phase... allowed) {
            for (Phase p : allowed) {
                if (this.phase == p) return;
            }
            throw new IllegalStateException("Unexpected phase: " + this.phase);
        }

        GovernmentCrtBoundary185Api.NormalReturn finish(long oldScalarResult) {
            if (this.phase == Phase.AFTER_INITIAL) {
                if (oldScalarResult != 0L) {
                    // Initial decoded was nonzero, returned as is
                    this.v = new GovernmentPrimaryTail155Api.VolatileBits(
                        oldScalarResult, this.v.rcxBits(), oldScalarResult, this.v.r8Bits(), this.v.r9Bits(),
                        this.v.r10Bits(), this.v.r11Bits(),
                        this.v.xmm0(), this.v.xmm1(), this.v.xmm2(),
                        this.v.xmm3(), this.v.xmm4(), this.v.xmm5()
                    );
                } else {
                    // Initial decoded was -1
                    this.v = new GovernmentPrimaryTail155Api.VolatileBits(
                        0L, this.v.rcxBits(), -1L, this.v.r8Bits(), this.v.r9Bits(),
                        this.v.r10Bits(), this.v.r11Bits(),
                        this.v.xmm0(), this.v.xmm1(), this.v.xmm2(),
                        this.v.xmm3(), this.v.xmm4(), this.v.xmm5()
                    );
                }
            } else if (this.phase == Phase.DONE_FAILURE) {
                if (oldScalarResult != 0L) {
                    throw new IllegalStateException("DONE_FAILURE requires scalar 0");
                }
                this.v = new GovernmentPrimaryTail155Api.VolatileBits(
                    0L, this.v.rcxBits(), this.v.rdxBits(), this.v.r8Bits(), this.v.r9Bits(),
                    this.v.r10Bits(), this.v.r11Bits(),
                    this.v.xmm0(), this.v.xmm1(), this.v.xmm2(),
                    this.v.xmm3(), this.v.xmm4(), this.v.xmm5()
                );
            } else if (this.phase == Phase.DONE_SUCCESS) {
                this.v = new GovernmentPrimaryTail155Api.VolatileBits(
                    oldScalarResult, this.v.rcxBits(), this.v.rdxBits(), this.v.r8Bits(), this.v.r9Bits(),
                    this.v.r10Bits(), this.v.r11Bits(),
                    this.v.xmm0(), this.v.xmm1(), this.v.xmm2(),
                    this.v.xmm3(), this.v.xmm4(), this.v.xmm5()
                );
            } else {
                throw new IllegalStateException("Unexpected finish phase: " + this.phase);
            }

            long rbx = memory.readQword(e + 8L);
            long rbp = memory.readQword(e + 0x10L);
            long rsi = memory.readQword(e + 0x18L);
            long r15 = memory.readQword(e - 0x28L);
            long r14 = memory.readQword(e - 0x20L);
            long r13 = memory.readQword(e - 0x18L);
            long r12 = memory.readQword(e - 0x10L);
            long rdi = memory.readQword(e - 8L);
            long retRip = memory.readQword(e);

            GovernmentPrimaryTail155Api.NonvolatileBits restoredNV = new GovernmentPrimaryTail155Api.NonvolatileBits(
                rbx, rbp, rsi, rdi, r12, r13, r14, r15,
                entry.nonvolatileBits().xmm6()
            );

            return new GovernmentCrtBoundary185Api.NormalReturn(
                this.v, retRip, e + 8L, restoredNV
            );
        }
    }

    private static final class MemoryView implements IndexedHelper225Api.Memory {
        private final Frame f;

        MemoryView(Frame f) {
            this.f = f;
        }

        @Override
        public int readInt32(long address) {
            f.require(Phase.AFTER_INITIAL, Phase.NEXT_INDEX_OR_EXHAUST);
            int value = f.memory.readDword(address);
            if (f.phase == Phase.AFTER_INITIAL) {
                f.v6(f.v.raxBits(), f.v.rcxBits(), 0L, f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
            }
            f.rsi = Integer.toUnsignedLong(value);
            f.phase = Phase.MODULE_CACHE_Q;
            return value;
        }

        @Override
        public void writeInt32(long address, int value) {
            f.memory.writeDword(address, value);
        }

        @Override
        public long readPointer(long address) {
            f.require(Phase.ENCODED_Q, Phase.INITIAL_COOKIE_Q, Phase.MODULE_CACHE_Q, Phase.PATH_Q,
                    Phase.LOAD_IAT_Q, Phase.ERROR_IAT_Q, Phase.RETRY_IAT_Q, Phase.UNLOAD_IAT_Q,
                    Phase.RESOLVE_IAT_Q, Phase.MODULE_COOKIE_Q, Phase.NEXT_INDEX_OR_EXHAUST,
                    Phase.SUCCESS_COOKIE_Q, Phase.FAIL_COOKIE_Q);
            long value = f.memory.readQword(address);
            switch (f.phase) {
                case Phase.ENCODED_Q:
                    f.v6(f.v.raxBits(), value, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.phase = Phase.INITIAL_COOKIE_Q;
                    break;
                case Phase.INITIAL_COOKIE_Q:
                    f.rdi = -1L;
                    f.v6(value & 63L, (f.v.rcxBits() & ~255L) | (value & 63L), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), value);
                    f.phase = Phase.AFTER_INITIAL;
                    break;
                case Phase.MODULE_CACHE_Q:
                    f.rbx = value;
                    if (value == -1L) {
                        f.rbp += 4L;
                        f.phase = Phase.NEXT_INDEX_OR_EXHAUST;
                    } else if (value == 0L) {
                        f.phase = Phase.PATH_Q;
                    } else {
                        f.phase = Phase.MODULE_COOKIE_Q;
                    }
                    break;
                case Phase.PATH_Q:
                    f.r14 = value;
                    f.phase = Phase.LOAD_IAT_Q;
                    break;
                case Phase.LOAD_IAT_Q:
                    f.phase = Phase.LOAD_PORT;
                    break;
                case Phase.ERROR_IAT_Q:
                    f.phase = Phase.ERROR_PORT;
                    break;
                case Phase.RETRY_IAT_Q:
                    f.phase = Phase.RETRY_PORT;
                    break;
                case Phase.UNLOAD_IAT_Q:
                    f.phase = Phase.UNLOAD_PORT;
                    break;
                case Phase.RESOLVE_IAT_Q:
                    f.phase = Phase.RESOLVE_PORT;
                    break;
                case Phase.MODULE_COOKIE_Q:
                    f.r14 = f.image;
                    f.v6(f.v.raxBits(), f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), value);
                    f.phase = Phase.RESOLVE_IAT_Q;
                    break;
                case Phase.NEXT_INDEX_OR_EXHAUST:
                    f.rbx = 0L;
                    f.v6(f.v.raxBits(), f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), value);
                    f.phase = Phase.FAIL_XCHG;
                    break;
                case Phase.SUCCESS_COOKIE_Q:
                    f.v6(f.v.raxBits(), (long)(64 - (int)(value & 63L)), f.v.rdxBits(), value, f.v.r9Bits(), f.v.r10Bits());
                    f.phase = Phase.SUCCESS_XCHG;
                    break;
                case Phase.FAIL_COOKIE_Q:
                    f.v6(f.v.raxBits(), f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), value);
                    f.phase = Phase.FAIL_XCHG;
                    break;
                default:
                    throw new IllegalStateException("Unexpected QWORD source phase");
            }
            return value;
        }

        @Override
        public void writeInt64(long address, long value) {
            f.memory.writeQword(address, value);
        }

        @Override
        public long exchangeInt64(long address, long newValue) {
            f.require(Phase.MODULE_FAIL_XCHG, Phase.MODULE_SUCCESS_XCHG, Phase.SUCCESS_XCHG, Phase.AFTER_INITIAL, Phase.FAIL_XCHG);
            long old;
            switch (f.phase) {
                case Phase.MODULE_FAIL_XCHG:
                    f.rbx = 0L;
                    f.r14 = f.image;
                    f.v6(-1L, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    old = f.memory.exchangeQword(address, newValue);
                    f.v6(old, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.rbp += 4L;
                    f.phase = Phase.NEXT_INDEX_OR_EXHAUST;
                    break;
                case Phase.MODULE_SUCCESS_XCHG:
                    f.r14 = f.image;
                    f.v6(f.rbx, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    old = f.memory.exchangeQword(address, newValue);
                    f.v6(old, f.v.rcxBits(), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    if (old == 0L) {
                        f.phase = Phase.MODULE_COOKIE_Q;
                    } else {
                        f.phase = Phase.UNLOAD_IAT_Q;
                    }
                    break;
                case Phase.SUCCESS_XCHG:
                    old = f.memory.exchangeQword(address, newValue);
                    f.v6(f.v.raxBits(), f.v.rcxBits(), old, f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.phase = Phase.DONE_SUCCESS;
                    break;
                case Phase.AFTER_INITIAL:
                    f.rbx = 0L;
                    f.v6(f.v.raxBits(), f.v.rcxBits(), 0L, f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.v6((long)((int)(f.v.r10Bits() & 63L)), (long)(64 - (int)(f.v.r10Bits() & 63L)), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.rdi = newValue;
                    old = f.memory.exchangeQword(address, newValue);
                    f.rdi = old;
                    f.phase = Phase.DONE_FAILURE;
                    break;
                case Phase.FAIL_XCHG:
                    f.v6((long)((int)(f.v.r10Bits() & 63L)), (long)(64 - (int)(f.v.r10Bits() & 63L)), f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
                    f.rdi = newValue;
                    old = f.memory.exchangeQword(address, newValue);
                    f.rdi = old;
                    f.phase = Phase.DONE_FAILURE;
                    break;
                default:
                    throw new IllegalStateException("Unexpected exchange source phase");
            }
            return old;
        }
    }
    private static final class PortsView implements IndexedHelper225Api.Ports {
        final Frame f;
        PortsView(Frame f) { this.f = f; }

        @Override public long call43da478(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, int edx, int r8d) {
            if (siteRva == 0x424E4EBL) {
                f.require(Phase.LOAD_PORT);
                f.v6(f.v.raxBits(), rcx, Integer.toUnsignedLong(edx), Integer.toUnsignedLong(r8d), f.v.r9Bits(), f.v.r10Bits());
                long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
                f.rbx = rax;
                if (rax == 0L) {
                    f.phase = Phase.ERROR_IAT_Q;
                } else {
                    f.phase = Phase.MODULE_SUCCESS_XCHG;
                    f.r14 = f.image;
                }
                return rax;
            } else if (siteRva == 0x424E53BL) {
                f.require(Phase.RETRY_PORT);
                f.v6(f.v.raxBits(), rcx, Integer.toUnsignedLong(edx), Integer.toUnsignedLong(r8d), f.v.r9Bits(), f.v.r10Bits());
                long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
                f.rbx = rax;
                f.r14 = f.image;
                if (rax == 0L) {
                    f.phase = Phase.MODULE_FAIL_XCHG;
                } else {
                    f.phase = Phase.MODULE_SUCCESS_XCHG;
                }
                return rax;
            }
            throw new IllegalStateException("Unexpected 43DA478 site");
        }

        @Override public int call43da738(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget) {
            if (siteRva != 0x424E4F9L) throw new IllegalStateException("Unexpected 43DA738 site");
            f.require(Phase.ERROR_PORT);
            long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
            int eax = (int) rax;
            if (eax == 0x57) {
                f.rbx = 7L;
                f.phase = Phase.WORD1_PORT;
            } else {
                f.rbx = 0L;
                f.r14 = f.image;
                f.phase = Phase.MODULE_FAIL_XCHG;
            }
            return eax;
        }

        @Override public int call4246a60(IndexedHelper225Api.Memory memory, long siteRva, long rcx, long rdx, int r8d) {
            if (siteRva == 0x424E514L) {
                f.require(Phase.WORD1_PORT);
                f.v6(f.v.raxBits(), rcx, rdx, Integer.toUnsignedLong(r8d), f.v.r9Bits(), f.v.r10Bits());
                long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4246A60L, 5);
                int eax = (int) rax;
                if (eax == 0) {
                    f.rbx = 0L;
                    f.r14 = f.image;
                    f.phase = Phase.MODULE_FAIL_XCHG;
                } else {
                    f.phase = Phase.WORD2_PORT;
                }
                return eax;
            } else if (siteRva == 0x424E52AL) {
                f.require(Phase.WORD2_PORT);
                f.v6(f.v.raxBits(), rcx, rdx, Integer.toUnsignedLong(r8d), f.v.r9Bits(), f.v.r10Bits());
                long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4246A60L, 5);
                int eax = (int) rax;
                if (eax == 0) {
                    f.rbx = 0L;
                    f.r14 = f.image;
                    f.phase = Phase.MODULE_FAIL_XCHG;
                } else {
                    f.phase = Phase.RETRY_IAT_Q;
                }
                return eax;
            }
            throw new IllegalStateException("Unexpected 4246A60 site");
        }

        @Override public void call43da7c0(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx) {
            if (siteRva != 0x424E574L) throw new IllegalStateException("Unexpected 43DA7C0 site");
            f.require(Phase.UNLOAD_PORT);
            f.v6(f.v.raxBits(), rcx, f.v.rdxBits(), f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
            f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
            f.phase = Phase.MODULE_COOKIE_Q;
        }

        @Override public long call43da680(IndexedHelper225Api.Memory memory, long siteRva, long actualTarget, long rcx, long rdx) {
            if (siteRva != 0x424E5A0L) throw new IllegalStateException("Unexpected 43DA680 site");
            f.require(Phase.RESOLVE_PORT);
            f.v6(f.v.raxBits(), rcx, rdx, f.v.r8Bits(), f.v.r9Bits(), f.v.r10Bits());
            long rax = f.invoke(siteRva, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE, actualTarget, 6);
            if (rax == 0L) {
                f.phase = Phase.FAIL_COOKIE_Q;
            } else {
                f.phase = Phase.SUCCESS_COOKIE_Q;
            }
            return rax;
        }
    }
}