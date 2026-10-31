package org.xar.ck3.research.m4;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m4.Free61FullState201WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Literal oracle derived from the held 61 bytes, never from executing the candidate. */
public final class Free61FullState201WitnessBook implements Free61FullState201WitnessApi.Book {
    private static final long I = 0x180000000L;
    private static final long SP = 0x9008L;
    private static final long PRE = 0x8FE0L;
    private static final long SLOT = 0x8FD8L;
    private static final long HEAP = 0xA0A1A2A3A4A5A6A7L;
    private static final long TARGET1 = 0x1234567812345678L;
    private static final long TARGET2 = 0x7766554433221100L;
    private static final long RET = 0x1020304050607080L;

    static void q(Map<Long,Integer> bytes, long at, long value) {
        for (int j = 0; j < 8; j++) bytes.put(at + j, (int)(value >>> (8 * j)) & 255);
    }
    static void d(Map<Long,Integer> bytes, long at, int value) {
        for (int j = 0; j < 4; j++) bytes.put(at + j, (value >>> (8 * j)) & 255);
    }
    static Bits128 x(long tag) { return new Bits128(0xA000000000000000L + tag, 0xB000000000000000L + tag); }
    static VolatileBits v(long rax, long rcx, int tag) {
        return new VolatileBits(rax, rcx, 0xCC00000000000000L + tag, 0x8800000000000000L + tag,
                0x9900000000000000L + tag, 0xAA00000000000000L + tag, 0xBB00000000000000L + tag,
                x(tag * 10L), x(tag * 10L + 1), x(tag * 10L + 2), x(tag * 10L + 3), x(tag * 10L + 4), x(tag * 10L + 5));
    }
    static VolatileBits args(VolatileBits v, long rcx, long rdx, long r8) {
        return new VolatileBits(v.raxBits(), rcx, rdx, r8, v.r9Bits(), v.r10Bits(), v.r11Bits(),
                v.xmm0(), v.xmm1(), v.xmm2(), v.xmm3(), v.xmm4(), v.xmm5());
    }
    static NonvolatileBits n(long rbx, int tag) {
        return new NonvolatileBits(rbx, 0xD100000000000000L + tag, 0xD200000000000000L + tag,
                0xD300000000000000L + tag, 0xD400000000000000L + tag, 0xD500000000000000L + tag,
                0xD600000000000000L + tag, 0xD700000000000000L + tag, x(600 + tag));
    }
    private static Map<Long,Integer> seed() {
        Map<Long,Integer> m = new HashMap<>(); q(m, SP, RET); return m;
    }
    private static Map<Long,Integer> prologue(Map<Long,Integer> seed, NonvolatileBits n, long internalRet) {
        Map<Long,Integer> m = new HashMap<>(seed);
        q(m, 0x9000L, n.rbxBits()); q(m, SLOT, internalRet); return m;
    }
    private static Call frame(long site, TargetKind kind, long target, VolatileBits v, NonvolatileBits n) {
        return new Call(site, kind, target, PRE, v, n);
    }
    private static Witness nullCase() {
        Map<Long,Integer> m = seed();
        VolatileBits v = v(0xF123456789ABCDEFL, 0L, 1);
        NonvolatileBits n = n(0x8123456789ABCDEFL, 1);
        return new Witness("null-only-fresh-ret", new Entry(I, SP, v, n), m, List.of(), m,
                new NormalReturn(v, RET, 0x9010L, n));
    }
    private static Witness successCase() {
        Map<Long,Integer> m = seed(); q(m, I + 0x5C5DE30L, HEAP); q(m, I + 0x43DA748L, TARGET1);
        VolatileBits in = v(0xFA123456789ABCDEL, 0x445566778899AABBL, 2);
        NonvolatileBits n = n(0x8888777766665555L, 2);
        Map<Long,Integer> before = prologue(m, n, I + 0x424E380L);
        Map<Long,Integer> mutation = new HashMap<>();
        q(mutation, 0x9000L, 0x3333444455556666L); q(mutation, SP, 0xEEDDCCBBAA998877L);
        mutation.put(0x333L, 0xAB);
        VolatileBits post = v(0xAABBCCDD00000001L, 0x2233445566778899L, 3);
        CallStep step = new CallStep(frame(0x424E37AL, TargetKind.INDIRECT_ABSOLUTE, TARGET1,
                args(in, HEAP, 0L, in.rcxBits()), n), before, mutation, post);
        Map<Long,Integer> end = new HashMap<>(before); end.putAll(mutation);
        return new Witness("success-full-rax-fresh-pop-ret", new Entry(I, SP, in, n), m, List.of(step), end,
                new NormalReturn(post, 0xEEDDCCBBAA998877L, 0x9010L, n(0x3333444455556666L, 2)));
    }
    private static Witness failureCase() {
        Map<Long,Integer> m = seed(); q(m, I + 0x5C5DE30L, HEAP); q(m, I + 0x43DA748L, TARGET1);
        q(m, I + 0x43DA738L, 0x1111222233334444L); q(m, 0x7000L, 0xDEADBEEFCAFEBABEL);
        VolatileBits in = v(0x9876543212345678L, 0xFFEEDDCCBBAA0011L, 4);
        NonvolatileBits n = n(0x1122334455667788L, 4);
        VolatileBits p1 = v(0x1234567800000000L, 0x1122000000000001L, 5);
        VolatileBits p2 = v(0x7000L, 0x1122000000000002L, 6);
        VolatileBits p3 = v(0xFEEDFACE80000002L, 0x1122000000000003L, 7);
        VolatileBits p4 = v(0xC0DEC0DE87654321L, 0x1122000000000004L, 8);
        Map<Long,Integer> b1 = prologue(m, n, I + 0x424E380L);
        CallStep s1 = new CallStep(frame(0x424E37AL, TargetKind.INDIRECT_ABSOLUTE, TARGET1,
                args(in, HEAP, 0L, in.rcxBits()), n), b1, Map.of(), p1);
        Map<Long,Integer> b2 = new HashMap<>(b1); q(b2, SLOT, I + 0x424E389L);
        Map<Long,Integer> mutation = new HashMap<>(); q(mutation, I + 0x43DA738L, TARGET2);
        q(mutation, 0x9000L, 0x9988776655443322L); q(mutation, SP, 0x1029384756ABCDEFL);
        CallStep s2 = new CallStep(frame(0x424E384L, TargetKind.DIRECT_RVA, 0x423B18CL, p1, n), b2, mutation, p2);
        Map<Long,Integer> b3 = new HashMap<>(b2); b3.putAll(mutation); q(b3, SLOT, I + 0x424E392L);
        CallStep s3 = new CallStep(frame(0x424E38CL, TargetKind.INDIRECT_ABSOLUTE, TARGET2,
                p2, n(0x7000L, 4)), b3, Map.of(), p3);
        Map<Long,Integer> b4 = new HashMap<>(b3); q(b4, SLOT, I + 0x424E399L);
        CallStep s4 = new CallStep(frame(0x424E394L, TargetKind.DIRECT_RVA, 0x423B0D4L,
                args(p3, 0x80000002L, p3.rdxBits(), p3.r8Bits()), n(0x7000L, 4)), b4, Map.of(), p4);
        Map<Long,Integer> end = new HashMap<>(b4); d(end, 0x7000L, 0x87654321);
        return new Witness("low-eax-zero-fresh-iat2-mapper-u32-dword", new Entry(I, SP, in, n), m,
                List.of(s1, s2, s3, s4), end,
                new NormalReturn(p4, 0x1029384756ABCDEFL, 0x9010L, n(0x9988776655443322L, 4)));
    }
    @Override public List<Witness> witnesses() { return List.of(nullCase(), successCase(), failureCase()); }
}
