package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;
import org.xar.ck3.research.m1.GovernmentThreadNotify181;
import org.xar.ck3.research.m1.GovernmentThreadWait179;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

public final class GovernmentCrtNative192Calls {
    private GovernmentCrtNative192Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        GovernmentSharedManager167Api.Memory sharedMemory;
        if (memory instanceof GovernmentSharedManager167Api.Memory) {
            sharedMemory = (GovernmentSharedManager167Api.Memory) memory;
        } else {
            sharedMemory = new LiveView(memory);
        }

        return new BoundCalls(image, sharedMemory, fallback);
    }

    private static final class BoundCalls implements GovernmentCrtBoundary185Api.Calls {
        private final long boundImage;
        private final GovernmentSharedManager167Api.Memory sharedMemory;
        private final GovernmentCrtBoundary185Api.Calls fallback;

        BoundCalls(long image, GovernmentSharedManager167Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
            this.boundImage = image;
            this.sharedMemory = memory;
            this.fallback = fallback;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.callSiteRva() == 0x4223AA9L
                    && call.targetBits() == 0x4223B30L) {
                return invokeWait179(call);
            }
            return fallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && transfer.jumpSiteRva() == 0x4223A7FL
                    && transfer.targetBits() == 0x4223AECL) {
                return invokeNotify181(transfer);
            }
            return fallback.tail(transfer);
        }

        private GovernmentPrimaryTail155Api.VolatileBits invokeWait179(GovernmentCrtBoundary185Api.Call call) {
            GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                    boundImage,
                    call.rspBits() - 8,
                    call.volatileBits(),
                    call.nonvolatileBits()
            );
            GovernmentThreadHeader178Api.Ports ports = new PortsAdapter(boundImage, sharedMemory, fallback);
            try {
                GovernmentThreadWait179.execute(entry, sharedMemory, ports);
                throw new UnsupportedOperationException("unexpected normal Wait return");
            } catch (TerminalTail t) {
                if (t.owner != ports) throw t;
                GovernmentCrtBoundary185Api.NormalReturn actual = t.captured;
                if (actual.returnRipBits() != boundImage + 0x4223AAEL) {
                    throw new IllegalStateException("RIP mismatch");
                }
                if (actual.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("RSP mismatch");
                }
                if (!actual.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("NV mismatch");
                }
                return actual.volatileBits();
            }
        }

        private GovernmentCrtBoundary185Api.NormalReturn invokeNotify181(GovernmentCrtBoundary185Api.Tail transfer) {
            GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                    transfer.entry().imageBaseBits(),
                    transfer.entry().rspBits(),
                    transfer.entry().volatileBits(),
                    transfer.entry().nonvolatileBits()
            );
            GovernmentThreadHeader178Api.Ports ports = new PortsAdapter(transfer.entry().imageBaseBits(), sharedMemory, fallback);
            try {
                GovernmentThreadNotify181.execute(entry, sharedMemory, ports);
                throw new UnsupportedOperationException("unexpected normal Notify return");
            } catch (TerminalTail t) {
                if (t.owner != ports) throw t;
                return t.captured;
            }
        }
    }

    private static final class PortsAdapter implements GovernmentThreadHeader178Api.Ports {
        private final long invocationImage;
        private final GovernmentSharedManager167Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;

        PortsAdapter(long image, GovernmentSharedManager167Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
            this.invocationImage = image;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invokeIat(GovernmentThreadHeader178Api.IatCall iat) {
            long target = memory.readQword(invocationImage + iat.slotRva());
            if (iat.tailJump()) {
                GovernmentCrtBoundary185Api.Tail tail = new GovernmentCrtBoundary185Api.Tail(
                        iat.callSiteRva(),
                        GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                        target,
                        new GovernmentCrtBoundary185Api.Entry(
                                invocationImage,
                                iat.rspBits(),
                                iat.volatileBits(),
                                iat.nonvolatileBits()
                        )
                );
                GovernmentCrtBoundary185Api.NormalReturn captured = fallback.tail(tail);
                throw new TerminalTail(this, captured);
            } else {
                GovernmentCrtBoundary185Api.Call call = new GovernmentCrtBoundary185Api.Call(
                        iat.callSiteRva(),
                        GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                        target,
                        iat.rspBits(),
                        iat.volatileBits(),
                        iat.nonvolatileBits()
                );
                return fallback.invoke(call);
            }
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            GovernmentCrtBoundary185Api.Call mapped = new GovernmentCrtBoundary185Api.Call(
                    call.callSiteRva(),
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    call.targetRva(),
                    call.rspBits(),
                    call.volatileBits(),
                    call.nonvolatileBits()
            );
            return fallback.invoke(mapped);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }
    }

    private static final class TerminalTail extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient Object owner;
        private final transient GovernmentCrtBoundary185Api.NormalReturn captured;

        TerminalTail(Object owner, GovernmentCrtBoundary185Api.NormalReturn captured) {
            super(null, null, false, false);
            this.owner = owner;
            this.captured = captured;
        }
    }

    private static final class LiveView implements GovernmentSharedManager167Api.Memory {
        private final GovernmentCrtBoundary185Api.Memory delegate;

        LiveView(GovernmentCrtBoundary185Api.Memory delegate) {
            this.delegate = delegate;
        }

        @Override
        public int readDword(long addressBits) {
            return delegate.readDword(addressBits);
        }

        @Override
        public long readQword(long addressBits) {
            return delegate.readQword(addressBits);
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            return delegate.readUnsignedByte(addressBits);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            delegate.writeDword(addressBits, valueBits);
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            return delegate.lockedXaddDword(addressBits, addendBits);
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            delegate.writeQword(addressBits, valueBits);
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            delegate.writeByte(addressBits, lowByteBits);
        }

        @Override
        public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
            return delegate.read128(addressBits);
        }

        @Override
        public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
            delegate.write128(addressBits, valueBits);
        }

        @Override
        public int lockedXaddByte(long addressBits, int addendBits) {
            throw new UnsupportedOperationException();
        }
    }
}
