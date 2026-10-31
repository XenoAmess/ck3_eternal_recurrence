package org.xar.ck3.control.g2.common.nativecore.task.captured;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory.*;
public final class RequestConstruct855f00Test {
    @org.junit.jupiter.api.Test
    public void inlineAndAliasedInputsRespectSourceReadOrder() {
        final Request140TestMemory memA = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytesA = memA.bytes();
        final long dA = 0x10000L;
        final long sA = 0x20000L;
        final long dataA = 0x30000L;
        final long rawLow = 0x1122334455667788L;
        final long rawHigh = 0x99AABBCCDDEEFF00L;
        bytesA.map(dA, 0x40);
        bytesA.map(sA, 0x40);
        bytesA.map(dataA, 0x40);
        for (int index = 0; index < 0x40; index++) {
            bytesA.seedByte(dA + index, 0xAA);
            bytesA.seedByte(sA + index, 0xBB);
            bytesA.seedByte(dataA + index, 0xCC);
        }
        bytesA.seedInt64(sA, dataA);
        bytesA.seedInt64(sA + 0x10, 15L);
        bytesA.seedInt64(sA + 0x18, 31L);
        bytesA.seedInt64(dataA, rawLow);
        bytesA.seedInt64(dataA + 8, rawHigh);
        final byte[] initialDA = new byte[0x40];
        final byte[] initialSA = new byte[0x40];
        final byte[] initialDataA = new byte[0x40];
        for (int index = 0; index < 0x40; index++) {
            initialDA[index] = (byte) bytesA.peekUnsignedByte(dA + index);
            initialSA[index] = (byte) bytesA.peekUnsignedByte(sA + index);
            initialDataA[index] = (byte) bytesA.peekUnsignedByte(dataA + index);
        }
        final byte[] expectedDA = initialDA.clone();
        for (int index = 0; index < 8; index++) {
            expectedDA[index] = (byte) (rawLow >>> (index * 8));
            expectedDA[8 + index] = (byte) (rawHigh >>> (index * 8));
            expectedDA[0x10 + index] = (byte) (15L >>> (index * 8));
            expectedDA[0x18 + index] = (byte) (15L >>> (index * 8));
        }
        final int[] callsA = {0, 0};
        final RequestConstruct855f00.Ports portsA = new RequestConstruct855f00.Ports() {
            @Override public long call856db0(long rcx) {
                callsA[0]++;
                throw new AssertionError("Short-length fixture invoked allocation port");
            }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                callsA[1]++;
                throw new AssertionError("Short-length fixture invoked copy port");
            }
        };
        memA.clearTrace();
        org.junit.jupiter.api.Assertions.assertEquals(dA,
                RequestConstruct855f00.construct(dA, sA, memA, portsA));
        org.junit.jupiter.api.Assertions.assertArrayEquals(new int[]{0, 0}, callsA);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dA, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dA + 0x10, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dA + 0x18, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, sA + 0x18, 8, 31, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, sA + 0x10, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, sA, 8, dataA, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128, dataA, 16, rawLow, rawHigh),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, dA, 16, rawLow, rawHigh),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dA + 0x10, 8, 15, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dA + 0x18, 8, 15, 0)
        ), memA.trace());
        org.junit.jupiter.api.Assertions.assertEquals(rawLow, bytesA.peekInt64(dA));
        org.junit.jupiter.api.Assertions.assertEquals(rawHigh, bytesA.peekInt64(dA + 8));
        org.junit.jupiter.api.Assertions.assertEquals(15L, bytesA.peekInt64(dA + 0x10));
        org.junit.jupiter.api.Assertions.assertEquals(15L, bytesA.peekInt64(dA + 0x18));
        for (int index = 0; index < 0x40; index++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedDA[index] & 0xFF,
                    bytesA.peekUnsignedByte(dA + index), "distinct destination byte " + index);
            org.junit.jupiter.api.Assertions.assertEquals(initialSA[index] & 0xFF,
                    bytesA.peekUnsignedByte(sA + index), "unchanged source byte " + index);
            org.junit.jupiter.api.Assertions.assertEquals(initialDataA[index] & 0xFF,
                    bytesA.peekUnsignedByte(dataA + index), "unchanged data byte " + index);
        }

        final Request140TestMemory memB = new Request140TestMemory();
        final Idler79eRegressionHost.Memory bytesB = memB.bytes();
        final long dB = 0x40000L;
        final long preservedHigh = 0xBBBBBBBBBBBBBBBBL;
        bytesB.map(dB, 0x40);
        for (int index = 0; index < 0x40; index++) bytesB.seedByte(dB + index, 0xBB);
        bytesB.seedInt64(dB, 0x1234567890ABCDEFL);
        bytesB.seedInt64(dB + 0x10, 37L);
        bytesB.seedInt64(dB + 0x18, 31L);
        final byte[] initialDB = new byte[0x40];
        for (int index = 0; index < 0x40; index++) {
            initialDB[index] = (byte) bytesB.peekUnsignedByte(dB + index);
        }
        final byte[] expectedDB = initialDB.clone();
        for (int index = 0; index < 8; index++) {
            expectedDB[index] = 0;
            expectedDB[0x10 + index] = 0;
            expectedDB[0x18 + index] = (byte) (15L >>> (index * 8));
        }
        final int[] callsB = {0, 0};
        final RequestConstruct855f00.Ports portsB = new RequestConstruct855f00.Ports() {
            @Override public long call856db0(long rcx) {
                callsB[0]++;
                throw new AssertionError("Aliased erased-length fixture invoked allocation port");
            }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                callsB[1]++;
                throw new AssertionError("Aliased erased-length fixture invoked copy port");
            }
        };
        memB.clearTrace();
        org.junit.jupiter.api.Assertions.assertEquals(dB,
                RequestConstruct855f00.construct(dB, dB, memB, portsB));
        org.junit.jupiter.api.Assertions.assertArrayEquals(new int[]{0, 0}, callsB);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dB, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dB + 0x10, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dB + 0x18, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, dB + 0x18, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ64, dB + 0x10, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.READ128, dB, 16, 0, preservedHigh),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE128, dB, 16, 0, preservedHigh),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dB + 0x10, 8, 0, 0),
                new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, dB + 0x18, 8, 15, 0)
        ), memB.trace());
        org.junit.jupiter.api.Assertions.assertEquals(0L, bytesB.peekInt64(dB));
        org.junit.jupiter.api.Assertions.assertEquals(preservedHigh, bytesB.peekInt64(dB + 8));
        org.junit.jupiter.api.Assertions.assertEquals(0L, bytesB.peekInt64(dB + 0x10));
        org.junit.jupiter.api.Assertions.assertEquals(15L, bytesB.peekInt64(dB + 0x18));
        for (int index = 0; index < 0x40; index++) {
            org.junit.jupiter.api.Assertions.assertEquals(expectedDB[index] & 0xFF,
                    bytesB.peekUnsignedByte(dB + index), "aliased destination/source byte " + index);
        }
    }

@org.junit.jupiter.api.Test public void heapArgumentsStayCapturedAndFailuresStopFinalWrites() {
    final Request140TestMemory.Op W = Request140TestMemory.Op.WRITE64;
    final Request140TestMemory.Op R = Request140TestMemory.Op.READ64;
    final long D = 0x1000L, S = 0x2000L, Q = 0x3000L;
    final Request140TestMemory memA = new Request140TestMemory();
    memA.bytes().map(D, 0x40); memA.bytes().map(S, 0x40); memA.bytes().map(Q, 0x40);
    for (int i = 0; i < 0x40; i += 8) memA.bytes().seedInt64(D + i, 0xA5A5A5A5A5A5A5A5L);
    memA.bytes().seedInt64(S, S); memA.bytes().seedInt64(S + 0x10L, 16L); memA.bytes().seedInt64(S + 0x18L, 15L);
    final byte[] initialA = new byte[0x40], expectedSourceA = new byte[0x40];
    for (int i = 0; i < 0x40; i++) {
        initialA[i] = (byte) memA.bytes().peekUnsignedByte(D + i);
        expectedSourceA[i] = (byte) memA.bytes().peekUnsignedByte(S + i);
    }
    final java.util.List<String> eventsA = new java.util.ArrayList<>();
    final long[] aArgs = new long[4];
    final RequestConstruct855f00.Ports portsA = new RequestConstruct855f00.Ports() {
        @Override public long call856db0(long rcx) {
            eventsA.add("alloc"); aArgs[0] = rcx;
            if (memA.trace().size() != 5 || memA.bytes().peekInt64(D) != 0L
                    || memA.bytes().peekInt64(D + 0x10L) != 0L || memA.bytes().peekInt64(D + 0x18L) != 0L) throw new AssertionError("A alloc prefix");
            memA.bytes().seedInt64(S + 0x10L, 99L); memA.bytes().seedInt64(S + 0x18L, 99L);
            return Q;
        }
        @Override public void call4226860(long rcx, long rdx, long r8) {
            eventsA.add("copy"); aArgs[1] = rcx; aArgs[2] = rdx; aArgs[3] = r8;
            if (memA.trace().size() != 6 || memA.bytes().peekInt64(D) != Q) throw new AssertionError("A copy prefix");
            memA.bytes().seedInt64(D + 8L, 0x1122334455667788L);
            memA.bytes().seedInt64(D + 0x10L, 0xCAFEL);
        }
    };
    final long resA = RequestConstruct855f00.construct(D, S, memA, portsA);
    if (resA != D || !eventsA.equals(java.util.List.of("alloc", "copy"))) throw new AssertionError("A return/calls");
    if (aArgs[0] != 32L || aArgs[1] != Q || aArgs[2] != S || aArgs[3] != 17L) throw new AssertionError("A captured args");
    final java.util.List<Request140TestMemory.Access> expectedTraceA = java.util.List.of(
            new Request140TestMemory.Access(W, D, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(R, S + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(R, S + 0x10L, 8, 16L, 0L),
            new Request140TestMemory.Access(W, D, 8, Q, 0L),
            new Request140TestMemory.Access(W, D + 0x10L, 8, 16L, 0L),
            new Request140TestMemory.Access(W, D + 0x18L, 8, 31L, 0L));
    if (!expectedTraceA.equals(memA.trace())) throw new AssertionError("A exact trace: " + memA.trace());
    final byte[] expectedA = initialA.clone();
    final int[] aOffsets = {0, 8, 0x10, 0x18};
    final long[] aValues = {Q, 0x1122334455667788L, 16L, 31L};
    for (int field = 0; field < aOffsets.length; field++) for (int i = 0; i < 8; i++) expectedA[aOffsets[field] + i] = (byte) (aValues[field] >>> (i * 8));
    for (int i = 0; i < 8; i++) { expectedSourceA[0x10 + i] = (byte) (99L >>> (i * 8)); expectedSourceA[0x18 + i] = (byte) (99L >>> (i * 8)); }
    for (int i = 0; i < 0x40; i++) {
        if (memA.bytes().peekUnsignedByte(D + i) != (expectedA[i] & 0xFF)) throw new AssertionError("A D byte " + i);
        if (memA.bytes().peekUnsignedByte(S + i) != (expectedSourceA[i] & 0xFF)) throw new AssertionError("A S byte " + i);
    }

    final long D2 = 0x4000L, S2 = 0x5000L;
    final Request140TestMemory memB = new Request140TestMemory();
    memB.bytes().map(D2, 0x40); memB.bytes().map(S2, 0x40); memB.bytes().map(Q, 0x40);
    for (int i = 0; i < 0x40; i += 8) memB.bytes().seedInt64(D2 + i, 0x6B6B6B6B6B6B6B6BL);
    memB.bytes().seedInt64(S2, S2); memB.bytes().seedInt64(S2 + 0x10L, -1L); memB.bytes().seedInt64(S2 + 0x18L, 15L);
    final byte[] initialB = new byte[0x40], expectedSourceB = new byte[0x40];
    for (int i = 0; i < 0x40; i++) {
        initialB[i] = (byte) memB.bytes().peekUnsignedByte(D2 + i);
        expectedSourceB[i] = (byte) memB.bytes().peekUnsignedByte(S2 + i);
    }
    final java.util.List<String> eventsB = new java.util.ArrayList<>();
    final long[] bArgs = new long[4];
    final RequestConstruct855f00.Ports portsB = new RequestConstruct855f00.Ports() {
        @Override public long call856db0(long rcx) {
            eventsB.add("alloc"); bArgs[0] = rcx;
            if (memB.trace().size() != 5 || memB.bytes().peekInt64(D2) != 0L
                    || memB.bytes().peekInt64(D2 + 0x10L) != 0L || memB.bytes().peekInt64(D2 + 0x18L) != 0L) throw new AssertionError("B alloc prefix");
            return Q;
        }
        @Override public void call4226860(long rcx, long rdx, long r8) {
            eventsB.add("copy"); bArgs[1] = rcx; bArgs[2] = rdx; bArgs[3] = r8;
            if (memB.trace().size() != 6 || memB.bytes().peekInt64(D2) != Q) throw new AssertionError("B copy prefix");
        }
    };
    final long resB = RequestConstruct855f00.construct(D2, S2, memB, portsB);
    if (resB != D2 || !eventsB.equals(java.util.List.of("alloc", "copy"))) throw new AssertionError("B return/calls");
    if (bArgs[0] != Long.MIN_VALUE || bArgs[1] != Q || bArgs[2] != S2 || bArgs[3] != 0L) throw new AssertionError("B raw args");
    final java.util.List<Request140TestMemory.Access> expectedTraceB = java.util.List.of(
            new Request140TestMemory.Access(W, D2, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D2 + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D2 + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(R, S2 + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(R, S2 + 0x10L, 8, -1L, 0L),
            new Request140TestMemory.Access(W, D2, 8, Q, 0L),
            new Request140TestMemory.Access(W, D2 + 0x10L, 8, -1L, 0L),
            new Request140TestMemory.Access(W, D2 + 0x18L, 8, Long.MAX_VALUE, 0L));
    if (!expectedTraceB.equals(memB.trace())) throw new AssertionError("B exact trace: " + memB.trace());
    final byte[] expectedB = initialB.clone();
    final int[] bOffsets = {0, 0x10, 0x18}; final long[] bValues = {Q, -1L, Long.MAX_VALUE};
    for (int field = 0; field < bOffsets.length; field++) for (int i = 0; i < 8; i++) expectedB[bOffsets[field] + i] = (byte) (bValues[field] >>> (i * 8));
    for (int i = 0; i < 0x40; i++) {
        if (memB.bytes().peekUnsignedByte(D2 + i) != (expectedB[i] & 0xFF)) throw new AssertionError("B D byte " + i);
        if (memB.bytes().peekUnsignedByte(S2 + i) != (expectedSourceB[i] & 0xFF)) throw new AssertionError("B S byte " + i);
    }

    final long D3 = 0x6000L, S3 = 0x7000L;
    final Request140TestMemory memC = new Request140TestMemory();
    memC.bytes().map(D3, 0x40); memC.bytes().map(S3, 0x40); memC.bytes().map(Q, 0x40);
    for (int i = 0; i < 0x40; i += 8) memC.bytes().seedInt64(D3 + i, 0x7C7C7C7C7C7C7C7CL);
    memC.bytes().seedInt64(S3, S3); memC.bytes().seedInt64(S3 + 0x10L, 16L); memC.bytes().seedInt64(S3 + 0x18L, 15L);
    final byte[] initialC = new byte[0x40], expectedSourceC = new byte[0x40];
    for (int i = 0; i < 0x40; i++) {
        initialC[i] = (byte) memC.bytes().peekUnsignedByte(D3 + i);
        expectedSourceC[i] = (byte) memC.bytes().peekUnsignedByte(S3 + i);
    }
    final java.util.List<String> eventsC = new java.util.ArrayList<>();
    final long[] cArgs = new long[4];
    final IllegalStateException sentinel = new IllegalStateException("SENTINEL");
    final RequestConstruct855f00.Ports portsC = new RequestConstruct855f00.Ports() {
        @Override public long call856db0(long rcx) {
            eventsC.add("alloc"); cArgs[0] = rcx;
            if (memC.trace().size() != 5 || memC.bytes().peekInt64(D3) != 0L
                    || memC.bytes().peekInt64(D3 + 0x10L) != 0L || memC.bytes().peekInt64(D3 + 0x18L) != 0L) throw new AssertionError("C alloc prefix");
            return Q;
        }
        @Override public void call4226860(long rcx, long rdx, long r8) {
            eventsC.add("copy"); cArgs[1] = rcx; cArgs[2] = rdx; cArgs[3] = r8;
            if (memC.trace().size() != 6 || memC.bytes().peekInt64(D3) != Q) throw new AssertionError("C copy prefix");
            throw sentinel;
        }
    };
    try {
        RequestConstruct855f00.construct(D3, S3, memC, portsC);
        throw new AssertionError("C no throw");
    } catch (IllegalStateException observed) {
        if (observed != sentinel) throw new AssertionError("C exception identity");
    }
    if (!eventsC.equals(java.util.List.of("alloc", "copy"))) throw new AssertionError("C calls");
    if (cArgs[0] != 32L || cArgs[1] != Q || cArgs[2] != S3 || cArgs[3] != 17L) throw new AssertionError("C args");
    final java.util.List<Request140TestMemory.Access> expectedTraceC = java.util.List.of(
            new Request140TestMemory.Access(W, D3, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D3 + 0x10L, 8, 0L, 0L),
            new Request140TestMemory.Access(W, D3 + 0x18L, 8, 0L, 0L),
            new Request140TestMemory.Access(R, S3 + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(R, S3 + 0x10L, 8, 16L, 0L),
            new Request140TestMemory.Access(W, D3, 8, Q, 0L));
    if (!expectedTraceC.equals(memC.trace())) throw new AssertionError("C exact failure prefix: " + memC.trace());
    final byte[] expectedC = initialC.clone();
    final int[] cOffsets = {0, 0x10, 0x18}; final long[] cValues = {Q, 0L, 0L};
    for (int field = 0; field < cOffsets.length; field++) for (int i = 0; i < 8; i++) expectedC[cOffsets[field] + i] = (byte) (cValues[field] >>> (i * 8));
    for (int i = 0; i < 0x40; i++) {
        if (memC.bytes().peekUnsignedByte(D3 + i) != (expectedC[i] & 0xFF)) throw new AssertionError("C D byte " + i);
        if (memC.bytes().peekUnsignedByte(S3 + i) != (expectedSourceC[i] & 0xFF)) throw new AssertionError("C S byte " + i);
    }
}

}
