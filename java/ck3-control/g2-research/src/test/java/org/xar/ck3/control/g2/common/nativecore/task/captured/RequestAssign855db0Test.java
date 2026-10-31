package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class RequestAssign855db0Test {
@org.junit.jupiter.api.Test
public void normalWithinAndGrowthKeepCapturedAndFreshRoles() {
    {
        final long d = 0x10000L, s = 0x20000L;
        final Request140TestMemory m = new Request140TestMemory();
        final Idler79eRegressionHost.Memory b = m.bytes();
        b.map(d, 64); b.map(s, 64);
        for (int i = 0; i < 64; i++) { b.seedByte(d + i, 0xa5); b.seedByte(s + i, 0xc3); }
        b.seedInt64(d + 0x10L, 0x1111222233334444L);
        b.seedInt64(d + 0x18L, 15L);
        final byte[] expected = new byte[64];
        for (int i = 0; i < 64; i++) expected[i] = (byte) b.peekUnsignedByte(d + i);
        final java.util.List<String> calls = new java.util.ArrayList<>();
        RequestAssign855db0.Ports p = new RequestAssign855db0.Ports() {
            @Override public long call856db0(long rcx) { throw new AssertionError("reuse allocation"); }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                calls.add("copy");
                org.junit.jupiter.api.Assertions.assertEquals(d, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(s, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(5L, r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 15L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 5L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(5L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(0xa5, b.peekUnsignedByte(d + 5L));
                b.seedInt64(d, 0x1020304050607080L);
                b.seedInt64(d + 0x18L, 0x55L);
                b.seedByte(d + 0x2dL, 0x7b);
            }
            @Override public void call4223f44(long rcx, long rdx, java.util.OptionalLong r8) { throw new AssertionError("reuse free"); }
        };
        long result = RequestAssign855db0.assign(d, s, 5L, m, p);
        java.util.List<Request140TestMemory.Access> actual = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(d, result);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("copy"), calls);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 15L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 5L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, d + 5L, 1, 0L, 0L)), actual);
        long[][] stores = {{0, 8, 0x1020304050607080L}, {0x10, 8, 5}, {0x18, 8, 0x55}, {0x2d, 1, 0x7b}, {5, 1, 0}};
        for (long[] row : stores) for (int j = 0; j < row[1]; j++) expected[(int) row[0] + j] = (byte) (row[2] >>> (8 * j));
        for (int i = 0; i < 64; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expected[i] & 255, b.peekUnsignedByte(d + i), "reuse receiver " + i);
            org.junit.jupiter.api.Assertions.assertEquals(0xc3, b.peekUnsignedByte(s + i), "reuse source " + i);
        }
    }
    {
        final long d = 0x30000L, s = 0x40000L, oldP = 0x50018L, freshP = 0x60020L, h = 0x60008L, newP = 0x70000L;
        final Request140TestMemory m = new Request140TestMemory();
        final Idler79eRegressionHost.Memory b = m.bytes();
        b.map(d, 64); b.map(s, 64); b.map(0x50000L, 64); b.map(0x60000L, 64); b.map(newP, 8192);
        for (int i = 0; i < 64; i++) { b.seedByte(d + i, 0xa5); b.seedByte(s + i, 0xc7); b.seedByte(0x50000L + i, 0xb5); b.seedByte(0x60000L + i, 0xb6); }
        for (int i = 0; i < 8192; i++) b.seedByte(newP + i, 0xa6);
        b.seedInt64(d, oldP); b.seedInt64(d + 0x10L, 0xaaa0L); b.seedInt64(d + 0x18L, 4095L);
        b.seedInt64(oldP - 8L, 0x50000L); b.seedInt64(freshP - 8L, 0xdeadL);
        final byte[] expected = new byte[64];
        for (int i = 0; i < 64; i++) expected[i] = (byte) b.peekUnsignedByte(d + i);
        final java.util.List<String> calls = new java.util.ArrayList<>();
        RequestAssign855db0.Ports p = new RequestAssign855db0.Ports() {
            @Override public long call856db0(long rcx) {
                calls.add("alloc");
                org.junit.jupiter.api.Assertions.assertEquals(6143L, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(0xaaa0L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(4095L, b.peekInt64(d + 0x18L));
                b.seedInt64(d + 0x18L, 2L); b.seedInt64(d + 0x10L, 0x9999L); b.seedByte(d + 0x28L, 0x55);
                return newP;
            }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                calls.add("copy");
                org.junit.jupiter.api.Assertions.assertEquals(newP, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(s, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(4100L, r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 4100L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 6142L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(4100L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(6142L, b.peekInt64(d + 0x18L));
                org.junit.jupiter.api.Assertions.assertEquals(oldP, b.peekInt64(d));
                org.junit.jupiter.api.Assertions.assertEquals(0xa6, b.peekUnsignedByte(newP + 4100L));
                b.seedInt64(d, freshP); b.seedInt64(d + 0x18L, 3L); b.seedInt64(d + 0x10L, 0x2222L);
                b.seedInt64(freshP - 8L, h); b.seedByte(newP + 1L, 0x66); b.seedByte(d + 0x2dL, 0x77);
            }
            @Override public void call4223f44(long rcx, long rdx, java.util.OptionalLong r8) {
                calls.add("free");
                org.junit.jupiter.api.Assertions.assertEquals(h, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(4135L, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.OptionalLong.of(h), r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 4100L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 6142L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, newP + 4100L, 1, 0L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d, 8, freshP, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, freshP - 8L, 8, h, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(freshP, b.peekInt64(d));
                org.junit.jupiter.api.Assertions.assertEquals(3L, b.peekInt64(d + 0x18L));
                org.junit.jupiter.api.Assertions.assertEquals(0x2222L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(0, b.peekUnsignedByte(newP + 4100L));
                b.seedInt64(d, 0x7f000L); b.seedByte(d + 0x2eL, 0x88);
            }
        };
        long result = RequestAssign855db0.assign(d, s, 4100L, m, p);
        java.util.List<Request140TestMemory.Access> actual = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(d, result);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("alloc", "copy", "free"), calls);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 4100L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 6142L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, newP + 4100L, 1, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d, 8, freshP, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, freshP - 8L, 8, h, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d, 8, newP, 0L)), actual);
        long[][] stores = {{0, 8, newP}, {0x10, 8, 0x2222}, {0x18, 8, 3}, {0x28, 1, 0x55}, {0x2d, 1, 0x77}, {0x2e, 1, 0x88}};
        for (long[] row : stores) for (int j = 0; j < row[1]; j++) expected[(int) row[0] + j] = (byte) (row[2] >>> (8 * j));
        for (int i = 0; i < 64; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expected[i] & 255, b.peekUnsignedByte(d + i), "growth receiver " + i);
            org.junit.jupiter.api.Assertions.assertEquals(0xc7, b.peekUnsignedByte(s + i), "growth source " + i);
        }
        for (int i = 0; i < 8192; i++) org.junit.jupiter.api.Assertions.assertEquals(i == 1 ? 0x66 : i == 4100 ? 0 : 0xa6, b.peekUnsignedByte(newP + i), "growth buffer " + i);
    }
}

@org.junit.jupiter.api.Test
public void unsupportedAndThrowingPathsStopLaterEffects() {
    {
        final long d = 0x80000L, s = 0x90000L;
        final Request140TestMemory m = new Request140TestMemory();
        final Idler79eRegressionHost.Memory b = m.bytes();
        b.map(d, 64); b.map(s, 64);
        for (int i = 0; i < 64; i++) { b.seedByte(d + i, 0x5a); b.seedByte(s + i, 0x6b); }
        b.seedInt64(d + 0x18L, 16L);
        final byte[] expected = new byte[64];
        for (int i = 0; i < 64; i++) expected[i] = (byte) b.peekUnsignedByte(d + i);
        RequestAssign855db0.Ports p = new RequestAssign855db0.Ports() {
            @Override public long call856db0(long rcx) { throw new AssertionError("unsupported allocation"); }
            @Override public void call4226860(long rcx, long rdx, long r8) { throw new AssertionError("unsupported copy"); }
            @Override public void call4223f44(long rcx, long rdx, java.util.OptionalLong r8) { throw new AssertionError("unsupported free"); }
        };
        RequestAssign855db0.UnsupportedSourcePath ex = org.junit.jupiter.api.Assertions.assertThrows(RequestAssign855db0.UnsupportedSourcePath.class,
            () -> RequestAssign855db0.assign(d, s, Long.MIN_VALUE, m, p));
        java.util.List<Request140TestMemory.Access> actual = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(0x8523a0L, ex.targetRva());
        org.junit.jupiter.api.Assertions.assertEquals(0x855eb5L, ex.trapSiteRva());
        org.junit.jupiter.api.Assertions.assertEquals(d, ex.knownRcx());
        org.junit.jupiter.api.Assertions.assertEquals(s, ex.knownRdx());
        org.junit.jupiter.api.Assertions.assertEquals(Long.MIN_VALUE, ex.knownR8());
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 16L, 0L)), actual);
        for (int i = 0; i < 64; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expected[i] & 255, b.peekUnsignedByte(d + i), "unsupported receiver " + i);
            org.junit.jupiter.api.Assertions.assertEquals(0x6b, b.peekUnsignedByte(s + i), "unsupported source " + i);
        }
    }
    {
        final long d = 0xa0000L, s = 0xb0000L, oldP = 0xc0010L, freshP = 0xd0048L, h = 0xd0000L, newP = 0xe0000L;
        final Request140TestMemory m = new Request140TestMemory();
        final Idler79eRegressionHost.Memory b = m.bytes();
        b.map(d, 64); b.map(s, 64); b.map(0xc0000L, 64); b.map(0xd0000L, 128); b.map(newP, 8192);
        for (int i = 0; i < 64; i++) { b.seedByte(d + i, 0xa5); b.seedByte(s + i, 0x6c); b.seedByte(0xc0000L + i, 0xb7); }
        for (int i = 0; i < 128; i++) b.seedByte(0xd0000L + i, 0xb8);
        for (int i = 0; i < 8192; i++) b.seedByte(newP + i, 0x7c);
        b.seedInt64(d, oldP); b.seedInt64(d + 0x10L, 0x7777L); b.seedInt64(d + 0x18L, 4095L);
        b.seedInt64(oldP - 8L, 0xc0000L); b.seedInt64(freshP - 8L, 0xd0020L);
        final byte[] expected = new byte[64];
        for (int i = 0; i < 64; i++) expected[i] = (byte) b.peekUnsignedByte(d + i);
        final java.util.List<String> calls = new java.util.ArrayList<>();
        RequestAssign855db0.Ports p = new RequestAssign855db0.Ports() {
            @Override public long call856db0(long rcx) {
                calls.add("alloc");
                org.junit.jupiter.api.Assertions.assertEquals(6143L, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(0x7777L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(oldP, b.peekInt64(d));
                return newP;
            }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                calls.add("copy");
                org.junit.jupiter.api.Assertions.assertEquals(newP, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(s, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(4100L, r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 4100L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 6142L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(4100L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(6142L, b.peekInt64(d + 0x18L));
                org.junit.jupiter.api.Assertions.assertEquals(0x7c, b.peekUnsignedByte(newP + 4100L));
                b.seedInt64(d, freshP); b.seedInt64(d + 0x10L, 0x2345L); b.seedInt64(d + 0x18L, 1L);
                b.seedInt64(freshP - 8L, h); b.seedByte(newP + 2L, 0x92); b.seedByte(d + 0x2aL, 0x84);
            }
            @Override public void call4223f44(long rcx, long rdx, java.util.OptionalLong r8) { throw new AssertionError("header rejection free"); }
        };
        RequestAssign855db0.UnsupportedSourcePath ex = org.junit.jupiter.api.Assertions.assertThrows(RequestAssign855db0.UnsupportedSourcePath.class,
            () -> RequestAssign855db0.assign(d, s, 4100L, m, p));
        java.util.List<Request140TestMemory.Access> actual = m.trace();
        org.junit.jupiter.api.Assertions.assertEquals(0x4232a70L, ex.targetRva());
        org.junit.jupiter.api.Assertions.assertEquals(0x855ebbL, ex.trapSiteRva());
        org.junit.jupiter.api.Assertions.assertEquals(72L, ex.knownRcx());
        org.junit.jupiter.api.Assertions.assertEquals(4135L, ex.knownRdx());
        org.junit.jupiter.api.Assertions.assertEquals(h, ex.knownR8());
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("alloc", "copy"), calls);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 4095L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 4100L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 6142L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, newP + 4100L, 1, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d, 8, freshP, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, freshP - 8L, 8, h, 0L)), actual);
        long[][] stores = {{0, 8, freshP}, {0x10, 8, 0x2345}, {0x18, 8, 1}, {0x2a, 1, 0x84}};
        for (long[] row : stores) for (int j = 0; j < row[1]; j++) expected[(int) row[0] + j] = (byte) (row[2] >>> (8 * j));
        for (int i = 0; i < 64; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expected[i] & 255, b.peekUnsignedByte(d + i), "header rejection receiver " + i);
            org.junit.jupiter.api.Assertions.assertEquals(0x6c, b.peekUnsignedByte(s + i), "header rejection source " + i);
        }
        for (int i = 0; i < 8192; i++) org.junit.jupiter.api.Assertions.assertEquals(i == 2 ? 0x92 : i == 4100 ? 0 : 0x7c, b.peekUnsignedByte(newP + i), "header rejection buffer " + i);
    }
    {
        final long d = 0xf0000L, s = 0x110000L, oldP = 0x120000L, freshP = 0x130000L, newP = 0x140000L;
        final Request140TestMemory m = new Request140TestMemory();
        final Idler79eRegressionHost.Memory b = m.bytes();
        b.map(d, 64); b.map(s, 64); b.map(oldP, 64); b.map(freshP, 64); b.map(newP, 64);
        for (int i = 0; i < 64; i++) { b.seedByte(d + i, 0xa5); b.seedByte(s + i, 0x6d); b.seedByte(oldP + i, 0xb9); b.seedByte(freshP + i, 0xba); b.seedByte(newP + i, 0x7d); }
        b.seedInt64(d, oldP); b.seedInt64(d + 0x10L, 0x8888L); b.seedInt64(d + 0x18L, 16L);
        final byte[] expected = new byte[64];
        for (int i = 0; i < 64; i++) expected[i] = (byte) b.peekUnsignedByte(d + i);
        final RuntimeException sentinel = new RuntimeException("free sentinel");
        final java.util.List<String> calls = new java.util.ArrayList<>();
        RequestAssign855db0.Ports p = new RequestAssign855db0.Ports() {
            @Override public long call856db0(long rcx) {
                calls.add("alloc");
                org.junit.jupiter.api.Assertions.assertEquals(32L, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 16L, 0L)), m.trace());
                return newP;
            }
            @Override public void call4226860(long rcx, long rdx, long r8) {
                calls.add("copy");
                org.junit.jupiter.api.Assertions.assertEquals(newP, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(s, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(17L, r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 16L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 17L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 31L, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(17L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(31L, b.peekInt64(d + 0x18L));
                b.seedInt64(d, freshP); b.seedInt64(d + 0x10L, 0x2222L); b.seedInt64(d + 0x18L, 0L); b.seedByte(newP + 3L, 0x93);
            }
            @Override public void call4223f44(long rcx, long rdx, java.util.OptionalLong r8) {
                calls.add("free");
                org.junit.jupiter.api.Assertions.assertEquals(freshP, rcx);
                org.junit.jupiter.api.Assertions.assertEquals(17L, rdx);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.OptionalLong.empty(), r8);
                org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 16L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 17L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 31L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, newP + 17L, 1, 0L, 0L),
                    new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d, 8, freshP, 0L)), m.trace());
                org.junit.jupiter.api.Assertions.assertEquals(freshP, b.peekInt64(d));
                org.junit.jupiter.api.Assertions.assertEquals(0L, b.peekInt64(d + 0x18L));
                org.junit.jupiter.api.Assertions.assertEquals(0x2222L, b.peekInt64(d + 0x10L));
                org.junit.jupiter.api.Assertions.assertEquals(0, b.peekUnsignedByte(newP + 17L));
                throw sentinel;
            }
        };
        RuntimeException ex = org.junit.jupiter.api.Assertions.assertThrows(RuntimeException.class,
            () -> RequestAssign855db0.assign(d, s, 17L, m, p));
        java.util.List<Request140TestMemory.Access> actual = m.trace();
        org.junit.jupiter.api.Assertions.assertSame(sentinel, ex);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of("alloc", "copy", "free"), calls);
        org.junit.jupiter.api.Assertions.assertEquals(java.util.List.of(
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d + 0x18L, 8, 16L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x10L, 8, 17L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE64, d + 0x18L, 8, 31L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.WRITE8, newP + 17L, 1, 0L, 0L),
            new Request140TestMemory.Access(Request140TestMemory.Op.READ64, d, 8, freshP, 0L)), actual);
        long[][] stores = {{0, 8, freshP}, {0x10, 8, 0x2222}, {0x18, 8, 0}};
        for (long[] row : stores) for (int j = 0; j < row[1]; j++) expected[(int) row[0] + j] = (byte) (row[2] >>> (8 * j));
        for (int i = 0; i < 64; i++) {
            org.junit.jupiter.api.Assertions.assertEquals(expected[i] & 255, b.peekUnsignedByte(d + i), "throw receiver " + i);
            org.junit.jupiter.api.Assertions.assertEquals(0x6d, b.peekUnsignedByte(s + i), "throw source " + i);
            org.junit.jupiter.api.Assertions.assertEquals(i == 3 ? 0x93 : i == 17 ? 0 : 0x7d, b.peekUnsignedByte(newP + i), "throw buffer " + i);
        }
    }
}
}
