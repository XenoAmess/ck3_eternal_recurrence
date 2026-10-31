package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m1.GovernmentRegistryForward185;
import org.xar.ck3.research.m1.GovernmentRegistryTable186;

public final class GovernmentCrtRegistry188Bridge {

    private static final long SITE_4223EFB = 0x4223EFBL;
    private static final long TARGET_424DE78 = 0x424DE78L;
    private static final long SITE_4223F0C = 0x4223F0CL;
    private static final long TARGET_424DEEC = 0x424DEECL;

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBase,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls fallback) {

        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);

        GovernmentSharedManager167Api.Memory shared = view(memory);

        GovernmentPrimaryTail155Api.Calls internal = new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall c) {
                GovernmentCrtBoundary185Api.Call crtCall = new GovernmentCrtBoundary185Api.Call(
                    c.callSiteRva(),
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    c.targetRva(),
                    c.rspBits(),
                    c.volatileBits(),
                    c.nonvolatileBits()
                );
                return fallback.invoke(crtCall);
            }
        };

        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call c) {
                if (c.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    long site = c.callSiteRva();
                    long target = c.targetBits();

                    if (site == SITE_4223EFB && target == TARGET_424DE78) {
                        return execute(imageBase, shared, internal, c, true);
                    } else if (site == SITE_4223F0C && target == TARGET_424DEEC) {
                        return execute(imageBase, shared, internal, c, false);
                    }
                }
                return fallback.invoke(c);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t) {
                return fallback.tail(t);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }

    private static GovernmentPrimaryTail155Api.VolatileBits execute(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls internal,
            GovernmentCrtBoundary185Api.Call c,
            boolean forward) {

        GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
            imageBase,
            c.rspBits() - 8,
            c.volatileBits(),
            c.nonvolatileBits()
        );

        GovernmentCallee164Api.NormalReturn result = forward ? GovernmentRegistryForward185.execute(entry, memory, internal) : GovernmentRegistryTable186.execute(entry, memory, internal);

        long expectedRip = imageBase + c.callSiteRva() + 5;
        if (result.returnRipBits() != expectedRip) {
            throw new UnsupportedOperationException("Invalid return RIP");
        }
        if (result.callerRspBits() != c.rspBits()) {
            throw new UnsupportedOperationException("Invalid return SP");
        }
        if (!result.nonvolatileBits().equals(c.nonvolatileBits())) {
            throw new UnsupportedOperationException("Nonvolatile bits mismatch");
        }

        return result.volatileBits();
    }

    private static GovernmentSharedManager167Api.Memory view(GovernmentCrtBoundary185Api.Memory memory) {
        if (memory instanceof GovernmentSharedManager167Api.Memory) {
            return (GovernmentSharedManager167Api.Memory) memory;
        }
        return new GovernmentSharedManager167Api.Memory() {
            @Override
            public int readDword(long addressBits) { return memory.readDword(addressBits); }
            @Override
            public long readQword(long addressBits) { return memory.readQword(addressBits); }
            @Override
            public int readUnsignedByte(long addressBits) { return memory.readUnsignedByte(addressBits); }
            @Override
            public void writeDword(long addressBits, int valueBits) { memory.writeDword(addressBits, valueBits); }
            @Override
            public int lockedXaddDword(long addressBits, int addendBits) { return memory.lockedXaddDword(addressBits, addendBits); }
            @Override
            public void writeQword(long addressBits, long valueBits) { memory.writeQword(addressBits, valueBits); }
            @Override
            public void writeByte(long addressBits, int lowByteBits) { memory.writeByte(addressBits, lowByteBits); }
            @Override
            public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) { return memory.read128(addressBits); }
            @Override
            public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) { memory.write128(addressBits, valueBits); }
            @Override
            public int lockedXaddByte(long addressBits, int addendBits) { throw new UnsupportedOperationException("lockedXaddByte not supported"); }
        };
    }
}