package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.Objects;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.research.m3.clear230.EncodedClear230Api;
import org.xar.ck3.research.m3.clear230.EncodedClear230BoundsPorts;
import org.xar.ck3.research.m3.clear230.EncodedClear424DD60;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Supplied-memory normal frame around the once-only existing business producer. */
public final class EncodedClear424dd60228 {
    private EncodedClear424dd60228() { }

    public static NormalReturn execute(Entry entry, Memory memory, Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        long e = entry.rspBits();
        NonvolatileBits n = entry.nonvolatileBits();
        memory.writeQword(e + 8L, n.rbxBits());
        memory.writeQword(e + 0x10L, n.rbpBits());
        memory.writeQword(e + 0x18L, n.rsiBits());
        memory.writeQword(e - 8L, n.rdiBits());
        memory.writeQword(e - 0x10L, n.r14Bits());
        memory.writeQword(e - 0x18L, n.r15Bits());

        Frame frame = new Frame(entry, memory, calls);
        long result = EncodedClear424DD60.execute(frame.view, frame,
                new EncodedClear230Api.Input(entry.imageBaseBits(), entry.volatileBits().rcxBits()));
        VolatileBits actual = frame.finish(result);

        long bx = memory.readQword(e + 8L);
        long bp = memory.readQword(e + 0x10L);
        long si = memory.readQword(e + 0x18L);
        long r15 = memory.readQword(e - 0x18L);
        long r14 = memory.readQword(e - 0x10L);
        long di = memory.readQword(e - 8L);
        long rip = memory.readQword(e);
        NonvolatileBits restored = new NonvolatileBits(bx, bp, si, di,
                n.r12Bits(), n.r13Bits(), r14, r15, n.xmm6());
        return new NormalReturn(actual, rip, e + 8L, restored);
    }

    private enum LastPort { NONE, IAT, FREE }

    private static VolatileBits replace(VolatileBits source, long rax, long rcx,
            long rdx, long r8, long r9) {
        return new VolatileBits(rax, rcx, rdx, r8, r9,
                source.r10Bits(), source.r11Bits(), source.xmm0(), source.xmm1(),
                source.xmm2(), source.xmm3(), source.xmm4(), source.xmm5());
    }

    private static final class Frame implements EncodedClear230BoundsPorts {
        private final Entry entry;
        private final Memory memory;
        private final Calls calls;
        private final long work;
        private final NativeView view;
        private VolatileBits current;
        private LastPort lastPort = LastPort.NONE;
        private DecodedBounds lastIatBounds;
        private long lastIatCursor;

        Frame(Entry entry, Memory memory, Calls calls) {
            this.entry = entry;
            this.memory = memory;
            this.calls = calls;
            work = entry.rspBits() - 0x38L;
            current = entry.volatileBits();
            view = new NativeView(memory);
        }

        private void requireView(NativeTaskMemory observed) {
            if (observed != view) {
                throw new UnsupportedOperationException("Foreign business memory view");
            }
        }

        private NonvolatileBits active(long cursor, DecodedBounds bounds) {
            NonvolatileBits n = entry.nonvolatileBits();
            return new NonvolatileBits(cursor, bounds.endBits(),
                    entry.volatileBits().rcxBits(), bounds.beginBits(),
                    n.r12Bits(), n.r13Bits(), view.initialCookie,
                    bounds.beginBits(), n.xmm6());
        }

        private void invoke(long site, int length, TargetKind kind, long target,
                VolatileBits value, NonvolatileBits nonvolatile) {
            memory.writeQword(work - 8L, entry.imageBaseBits() + site + length);
            current = Objects.requireNonNull(calls.invoke(new Call(site, kind, target,
                    work, value, nonvolatile)));
        }

        @Override
        public void call43dbba8WithBounds(NativeTaskMemory observed, long site,
                long target, long liveRax, EncodedClear230Api.IndirectArguments args,
                DecodedBounds bounds) {
            requireView(observed);
            if (site != 0x424DDE5L || view.initialReads != 5 || view.writesSaturated == 0) {
                throw new UnsupportedOperationException("Unqualified IAT source event");
            }
            Objects.requireNonNull(bounds);
            long rdx;
            long r9;
            if (args.rdxR9() instanceof EncodedClear230Api.Reloaded reloaded) {
                rdx = reloaded.rdx();
                r9 = reloaded.r9();
            } else if (args.rdxR9() == EncodedClear230Api.EntryUnknown.UNKNOWN) {
                rdx = entry.volatileBits().rdxBits();
                r9 = entry.volatileBits().r9Bits();
            } else {
                throw new UnsupportedOperationException("Unknown RDX/R9 source role");
            }
            long cursor = view.lastWriteAddress;
            VolatileBits value = replace(current, liveRax,
                    Integer.toUnsignedLong(args.ecx()), rdx, args.r8(), r9);
            lastIatBounds = bounds;
            lastIatCursor = cursor;
            invoke(site, 6, TargetKind.INDIRECT_ABSOLUTE, target, value, active(cursor, bounds));
            lastPort = LastPort.IAT;
            view.beginNormalIatRefresh();
        }

        @Override
        public void call424e364WithBounds(NativeTaskMemory observed, long site,
                long rcx, DecodedBounds bounds) {
            requireView(observed);
            Objects.requireNonNull(bounds);
            if (site != 0x424DE32L || view.initialReads != 5 || rcx != bounds.beginBits()) {
                throw new UnsupportedOperationException("Unqualified free source event");
            }
            long cursor;
            long rax;
            if (view.cellSeenSinceCheckpoint) {
                cursor = view.lastCellAddress - 8L;
                rax = view.lastCellValue;
            } else if (view.hadIat) {
                cursor = (bounds.equals(lastIatBounds) ? lastIatCursor : bounds.endBits()) - 8L;
                rax = bounds.endBits();
            } else {
                cursor = bounds.endBits() - 8L;
                rax = bounds.beginBits() - 1L;
            }
            if (view.hadIat && view.refreshReads != 5) {
                throw new UnsupportedOperationException("Incomplete source reload");
            }
            long rdx = view.hadIat ? view.refreshedDescriptor : entry.volatileBits().rdxBits();
            long r9 = view.hadIat ? bounds.beginBits() : entry.volatileBits().r9Bits();
            long r8 = view.hadIat ? view.refreshedCookie : view.initialCookie;
            VolatileBits value = replace(current, rax, rcx, rdx, r8, r9);
            invoke(site, 5, TargetKind.DIRECT_RVA, 0x424E364L, value, active(cursor, bounds));
            lastPort = LastPort.FREE;
        }

        @Override
        public void call43dbba8(NativeTaskMemory observed, long site, long target,
                long liveRax, EncodedClear230Api.IndirectArguments arguments) {
            throw new UnsupportedOperationException("Current decoded-bound DATA required");
        }

        @Override
        public void call424e364(NativeTaskMemory observed, long site, long rcx) {
            throw new UnsupportedOperationException("Current decoded-bound DATA required");
        }

        VolatileBits finish(long result) {
            VolatileBits initial = entry.volatileBits();
            if (view.writesSaturated == 0) {
                if (lastPort == LastPort.NONE && view.initialReads == 2
                        && result == 0xFFFFFFFFL) {
                    return replace(initial, result, initial.rcxBits(), initial.rdxBits(),
                            initial.r8Bits(), initial.r9Bits());
                }
                if (lastPort == LastPort.NONE && view.initialReads == 5 && result == 0L) {
                    return replace(initial, 0L, view.initialCookie & 63L, initial.rdxBits(),
                            view.initialCookie, initial.r9Bits());
                }
                throw new UnsupportedOperationException("Unqualified early normal return");
            }
            if (result != 0L || view.writesSaturated != 3) {
                throw new UnsupportedOperationException("Unqualified normal clear completion");
            }
            if (lastPort == LastPort.FREE) {
                return replace(current, 0L, view.lastWritePriorQValue,
                        current.rdxBits(), view.lastWriteValue, current.r9Bits());
            }
            if (lastPort == LastPort.IAT && view.refreshReads == 5) {
                // A completed clear with no FREE can only follow begin == -1.
                return replace(current, 0L, view.lastWritePriorQValue,
                        view.refreshedDescriptor, view.lastWriteValue, -1L);
            }
            throw new UnsupportedOperationException("Missing actual normal opaque reply");
        }
    }

    /** Bounded observations of business requests only; physical/provider RAM bypasses it. */
    private static final class NativeView implements NativeTaskMemory {
        private final Memory memory;
        private int initialReads;
        private long initialCookie;
        private int refreshReads = 5;
        private long refreshedCookie;
        private long refreshedDescriptor;
        private boolean hadIat;
        private boolean cellSeenSinceCheckpoint;
        private long lastCellAddress;
        private long lastCellValue;
        private long lastQValue;
        private int writesSaturated;
        private long lastWriteAddress;
        private long lastWritePriorQValue;
        private long lastWriteValue;

        NativeView(Memory memory) { this.memory = memory; }

        void beginNormalIatRefresh() {
            hadIat = true;
            refreshReads = 0;
            cellSeenSinceCheckpoint = false;
        }

        @Override
        public long readPointer(long address) {
            long value = memory.readQword(address);
            lastQValue = value;
            if (initialReads < 5) {
                initialReads++;
                if (initialReads == 3) {
                    initialCookie = value;
                }
            } else if (refreshReads < 5) {
                refreshReads++;
                if (refreshReads == 1) {
                    refreshedCookie = value;
                } else if (refreshReads == 3) {
                    refreshedDescriptor = value;
                }
            } else {
                // Provisional until the next real port: final pointer chains need no cursor.
                cellSeenSinceCheckpoint = true;
                lastCellAddress = address;
                lastCellValue = value;
            }
            return value;
        }

        @Override
        public int readInt32(long address) { return memory.readDword(address); }

        @Override
        public void writeInt32(long address, int value) { memory.writeDword(address, value); }

        @Override
        public void writeInt64(long address, long value) {
            memory.writeQword(address, value);
            if (writesSaturated < 3) {
                writesSaturated++;
            }
            lastWriteAddress = address;
            lastWritePriorQValue = lastQValue;
            lastWriteValue = value;
        }
    }
}
