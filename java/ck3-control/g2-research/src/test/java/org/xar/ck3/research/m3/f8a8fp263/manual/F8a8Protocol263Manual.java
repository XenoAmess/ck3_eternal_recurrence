package org.xar.ck3.research.m3.f8a8fp263.manual;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8Fp263Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8FullState263;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Two finite new263 protocol cases. Oracle sealed before implementation read:
 * 245f11d6136a0b09d08c3a962cb2a411f6d232547d1bd3bf4d0e8a3564b4f79d
 * No child algorithm, old Test suite, native attachment or hardware qualification.
 */
public final class F8a8Protocol263Manual {
    private F8a8Protocol263Manual() { }

    private static final long IMAGE = 0x0000000140000000L;
    private static final long E = 0x0000000000001800L;
    private static final long PRE_SP = 0x00000000000017A8L;
    private static final long CHILD_SP = 0x00000000000017A0L;
    private static final long SAVED1 = 0xC1C2C3C4C5C6C7C8L;
    private static final long SAVED2 = 0xD1D2D3D4D5D6D7D8L;
    private static final long RET0 = 0x1111000022223333L;
    private static final long RET1 = 0xE1E2E3E4E5E6E7E8L;
    private static final long RET2 = 0xF1F2F3F4F5F6F7F8L;
    private static final VolatileBits ENTRY_V = new VolatileBits(0x0102030405060708L, 0x0000000000002000L, 0x1112131415161718L, 0x2122334455667788L, 0x3132435465768798L, 0x41425364758697A8L, 0x515263748596A7B8L,
        new Bits128(0x6100000000000001L, 0x7100000000000002L),
        new Bits128(0x6100000000000101L, 0x7100000000000102L),
        new Bits128(0x6100000000000201L, 0x7100000000000202L),
        new Bits128(0x6100000000000301L, 0x7100000000000302L),
        new Bits128(0x6100000000000401L, 0x7100000000000402L),
        new Bits128(0x6100000000000501L, 0x7100000000000502L));
    private static final NonvolatileBits ENTRY_N = new NonvolatileBits(0x2122232425262728L, 0x3132333435363738L, 0x4142434445464748L, 0x5152535455565758L, 0x6162636465666768L, 0x7172737475767778L, 0x8182838485868788L, 0x9192939495969798L, new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final NonvolatileBits CALL_N = new NonvolatileBits(0x2122232425262728L, 0x00000000000017F8L, 0x4142434445464748L, 0x5152535455565758L, 0x6162636465666768L, 0x7172737475767778L, 0x8182838485868788L, 0x9192939495969798L, new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final NonvolatileBits FINAL_N = new NonvolatileBits(0x2122232425262728L, 0xD1D2D3D4D5D6D7D8L, 0x4142434445464748L, 0x5152535455565758L, 0x6162636465666768L, 0x7172737475767778L, 0x8182838485868788L, 0x9192939495969798L, new Bits128(0xA1A2A3A4A5A6A7A8L, 0xB1B2B3B4B5B6B7B8L));
    private static final VolatileBits FIRST_CALL_V = new VolatileBits(0x0000000000002000L, 0x0000000000001810L, 0x0000000000001820L, 0x00000000000017E0L, 0x0000000000001818L, 0x41425364758697A8L, 0x515263748596A7B8L,
        new Bits128(0x6100000000000001L, 0x7100000000000002L),
        new Bits128(0x6100000000000101L, 0x7100000000000102L),
        new Bits128(0x6100000000000201L, 0x7100000000000202L),
        new Bits128(0x6100000000000301L, 0x7100000000000302L),
        new Bits128(0x6100000000000401L, 0x7100000000000402L),
        new Bits128(0x6100000000000501L, 0x7100000000000502L));
    private static final VolatileBits SECOND_CALL_V = new VolatileBits(0xA101020304050607L, 0x0000000000001810L, 0x00000000000017CCL, 0x00000000000017E8L, 0x00000000000017C8L, 0xA651525354555657L, 0xA761626364656667L,
        new Bits128(0x8100000000000001L, 0x9100000000000002L),
        new Bits128(0x8100000000000101L, 0x9100000000000102L),
        new Bits128(0x8100000000000201L, 0x9100000000000202L),
        new Bits128(0x8100000000000301L, 0x9100000000000302L),
        new Bits128(0x8100000000000401L, 0x9100000000000402L),
        new Bits128(0x8100000000000501L, 0x9100000000000502L));
    private static final VolatileBits FIRST_OFFER_V = new VolatileBits(0xA101020304050607L, 0xA211121314151617L, 0xA321222324252627L, 0xA431323334353637L, 0xA541424344454647L, 0xA651525354555657L, 0xA761626364656667L,
        new Bits128(0x8100000000000001L, 0x9100000000000002L),
        new Bits128(0x8100000000000101L, 0x9100000000000102L),
        new Bits128(0x8100000000000201L, 0x9100000000000202L),
        new Bits128(0x8100000000000301L, 0x9100000000000302L),
        new Bits128(0x8100000000000401L, 0x9100000000000402L),
        new Bits128(0x8100000000000501L, 0x9100000000000502L));
    private static final VolatileBits SECOND_OFFER_V = new VolatileBits(0xB101020304050607L, 0xB211121314151617L, 0xB321222324252627L, 0xB431323334353637L, 0xB541424344454647L, 0xB651525354555657L, 0xB761626364656667L,
        new Bits128(0xA100000000000001L, 0xB100000000000002L),
        new Bits128(0xA100000000000101L, 0xB100000000000102L),
        new Bits128(0xA100000000000201L, 0xB100000000000202L),
        new Bits128(0xA100000000000301L, 0xB100000000000302L),
        new Bits128(0xA100000000000401L, 0xB100000000000402L),
        new Bits128(0xA100000000000501L, 0xB100000000000502L));
    private record Access(String method, long address, int width, String value) { }
    private static final List<Access> NORMAL_TRACE = List.of(
        new Access("writeQword", 0x00000000000017F8L, 8, "0x3132333435363738"),
        new Access("writeQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x00000000000017E0L, 8, "0x00000000000017D0"),
        new Access("writeDword", 0x0000000000001818L, 4, "0x00000005"),
        new Access("writeDword", 0x0000000000001820L, 4, "0x00000005"),
        new Access("writeQword", 0x00000000000017E8L, 8, "0x00000000000017D0"),
        new Access("writeQword", 0x00000000000017F0L, 8, "0x00000000000017D8"),
        new Access("writeDword", 0x00000000000017C8L, 4, "0x00000004"),
        new Access("writeDword", 0x00000000000017CCL, 4, "0x00000004"),
        new Access("writeQword", 0x00000000000017D8L, 8, "0x0000000145C5DCD8"),
        new Access("writeDword", 0x0000000000002028L, 4, "0x00000001"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x0000000000002000L, 8, "0x00000001444267F0"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeDword", 0x00000000000023A8L, 4, "0x00000001"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x0000000000002088L, 8, "0x000000014542F770"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeWord", 0x00000000000020BCL, 2, "0x0043"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeWord", 0x00000000000021C2L, 2, "0x0043"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("readQword", 0x00000000000023A0L, 8, "0xAABBCCDDEEFF1020"),
        new Access("writeQword", 0x00000000000023A0L, 8, "0x0000000000000000"),
        new Access("writeQword", 0x00000000000017A0L, 8, "0x000000014424F95A"),
        new Access("writeQword", 0x00000000000017F8L, 8, "0xC1C2C3C4C5C6C7C8"),
        new Access("writeQword", 0x0000000000001800L, 8, "0xE1E2E3E4E5E6E7E8"),
        new Access("writeQword", 0x00000000000017A0L, 8, "0x000000014424F96F"),
        new Access("writeQword", 0x00000000000017F8L, 8, "0xD1D2D3D4D5D6D7D8"),
        new Access("writeQword", 0x0000000000001800L, 8, "0xF1F2F3F4F5F6F7F8"),
        new Access("readQword", 0x00000000000017F8L, 8, "0xD1D2D3D4D5D6D7D8"),
        new Access("readQword", 0x0000000000001800L, 8, "0xF1F2F3F4F5F6F7F8"));
    private static final List<Access> STOP_TRACE = List.of(
        new Access("writeQword", 0x00000000000017F8L, 8, "0x3132333435363738"),
        new Access("writeQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x00000000000017E0L, 8, "0x00000000000017D0"),
        new Access("writeDword", 0x0000000000001818L, 4, "0x00000005"),
        new Access("writeDword", 0x0000000000001820L, 4, "0x00000005"),
        new Access("writeQword", 0x00000000000017E8L, 8, "0x00000000000017D0"),
        new Access("writeQword", 0x00000000000017F0L, 8, "0x00000000000017D8"),
        new Access("writeDword", 0x00000000000017C8L, 4, "0x00000004"),
        new Access("writeDword", 0x00000000000017CCL, 4, "0x00000004"),
        new Access("writeQword", 0x00000000000017D8L, 8, "0x0000000145C5DCD8"),
        new Access("writeDword", 0x0000000000002028L, 4, "0x00000001"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x0000000000002000L, 8, "0x00000001444267F0"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeDword", 0x00000000000023A8L, 4, "0x00000001"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeQword", 0x0000000000002088L, 8, "0x000000014542F770"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeWord", 0x00000000000020BCL, 2, "0x0043"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("writeWord", 0x00000000000021C2L, 2, "0x0043"),
        new Access("readQword", 0x00000000000017D0L, 8, "0x0000000000002000"),
        new Access("readQword", 0x00000000000023A0L, 8, "0xAABBCCDDEEFF1020"),
        new Access("writeQword", 0x00000000000023A0L, 8, "0x0000000000000000"),
        new Access("writeQword", 0x00000000000017A0L, 8, "0x000000014424F95A"),
        new Access("writeQword", 0x00000000000017F8L, 8, "0xC1C2C3C4C5C6C7C8"),
        new Access("writeQword", 0x0000000000001800L, 8, "0xE1E2E3E4E5E6E7E8"),
        new Access("writeQword", 0x00000000000017A0L, 8, "0x000000014424F96F"));

    public static void main(String[] args) {
        runCase(false);
        runCase(true);
        System.out.print("F8a8Protocol263Manual: 2 finite cases completed\n");
    }

    private static void runCase(boolean stopAtSecond) {
        Ram ram = new Ram(0x1000L, 8192);
        ram.seedQword(E - 8L, 0xDEADBEEF11223344L);
        ram.seedQword(E, RET0);
        ram.seedQword(0x23A0L, 0xAABBCCDDEEFF1020L);
        ram.seedDword(0x23A8L, 0xEEDDCCBB);
        QueueFp604Api.Mxcsr fp0 = new QueueFp604Api.Mxcsr(0x0001, 0x0003);
        QueueFp604Api.Mxcsr fp1 = new QueueFp604Api.Mxcsr(0x0040, 0x00C0);
        QueueFp604Api.Mxcsr fp2 = new QueueFp604Api.Mxcsr(0x0081, 0x00C3);
        QueueFp604Api.Mxcsr fpStop = new QueueFp604Api.Mxcsr(0x0002, 0x0003);
        int[] budgetCalls = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (header, address) -> {
            budgetCalls[0]++;
            throw new AssertionError("straight-line helper consumed loop budget");
        };
        QueueFp604Api.Input input = new QueueFp604Api.Input(
            new FullCopy437Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE, E, ENTRY_V, ENTRY_N), false, budget),
            fp0);
        QueueFp604Api.Normal firstOffer = new QueueFp604Api.Normal(
            new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                FIRST_OFFER_V, 0x000000014424F95AL, PRE_SP, CALL_N), true), fp1);
        QueueFp604Api.Normal secondOffer = new QueueFp604Api.Normal(
            new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                SECOND_OFFER_V, 0x000000014424F96FL, PRE_SP, CALL_N), false), fp2);
        QueueFp604Api.Stopped stopped = new QueueFp604Api.Stopped(
            QueueFp604Api.StopReason.MISSING_POST_STATE,
            new QueueFp604Api.Snapshot(
                new GovernmentCrtBoundary185Api.Entry(IMAGE, CHILD_SP, SECOND_CALL_V, CALL_N),
                0x424F800L, false, fpStop), 0, 0x424F96AL);
        int[] count = {0};
        F8a8Fp263Api.Calls calls = frame -> {
            int ordinal = ++count[0];
            if (ordinal > 2) throw new AssertionError("unexpected third callback");
            long site = ordinal == 1 ? 0x424F955L : 0x424F96AL;
            long target = ordinal == 1 ? 0x424F780L : 0x424F800L;
            long rip = ordinal == 1 ? 0x000000014424F95AL : 0x000000014424F96FL;
            VolatileBits expectedV = ordinal == 1 ? FIRST_CALL_V : SECOND_CALL_V;
            GovernmentCrtBoundary185Api.Call expectedCall = new GovernmentCrtBoundary185Api.Call(
                site, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                target, PRE_SP, expectedV, CALL_N);
            GovernmentCrtBoundary185Api.Entry expectedChild =
                new GovernmentCrtBoundary185Api.Entry(IMAGE, CHILD_SP, expectedV, CALL_N);
            if (!frame.original().equals(expectedCall) || !frame.childEntry().equals(expectedChild)
                    || frame.directionFlagSet() != (ordinal == 2)
                    || frame.preMxcsr() != (ordinal == 1 ? fp0 : fp1)
                    || frame.returnRipBits() != rip)
                throw new AssertionError("full independent frame mismatch at callback " + ordinal);
            if (ram.peekQword(CHILD_SP) != rip)
                throw new AssertionError("actual owned CALL push missing");
            List<Access> expectedPrefix = ordinal == 1 ? NORMAL_TRACE.subList(0, 25) : STOP_TRACE;
            if (!ram.events().equals(expectedPrefix))
                throw new AssertionError("Memory prefix mismatch at callback " + ordinal
                    + ": " + ram.events());
            if (ordinal == 1) {
                if (ram.peekQword(E - 8L) != ENTRY_N.rbpBits() || ram.peekQword(E) != RET0)
                    throw new AssertionError("PUSH RBP or existing outer RET mismatch");
                ram.writeQword(E - 8L, SAVED1);
                ram.writeQword(E, RET1);
                return firstOffer;
            }
            if (stopAtSecond) return stopped;
            ram.writeQword(E - 8L, SAVED2);
            ram.writeQword(E, RET2);
            return secondOffer;
        };

        QueueFp604Api.Outcome outcome = F8a8FullState263.execute(input, ram, calls);
        if (count[0] != 2 || budgetCalls[0] != 0)
            throw new AssertionError("callback or budget count mismatch");
        if (stopAtSecond) {
            if (outcome != stopped || !ram.events().equals(STOP_TRACE)
                    || ram.peekQword(E - 8L) != SAVED1 || ram.peekQword(E) != RET1)
                throw new AssertionError("Stopped identity or exact no-epilogue prefix mismatch");
        } else {
            if (!(outcome instanceof QueueFp604Api.Normal normal))
                throw new AssertionError("normal scenario did not complete normally");
            FullCopy437Api.CallResult expected = new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(
                    SECOND_OFFER_V, RET2, E + 8L, FINAL_N), false);
            if (!normal.base().equals(expected) || normal.postMxcsr() != fp2
                    || !ram.events().equals(NORMAL_TRACE)
                    || ram.peekQword(E - 8L) != SAVED2 || ram.peekQword(E) != RET2)
                throw new AssertionError("fresh full return or exact Memory trace mismatch");
        }
    }

    /** Mechanical finite supplied storage only; no target or opaque-child instruction semantics. */
    private static final class Ram implements FullCopy437Api.Memory {

        private final long base;
        private final byte[] bytes;
        private final List<Access> accesses = new ArrayList<>();

        public Ram(long base, int size) {
            if (size < 32 || size > 65536) throw new IllegalArgumentException("finite RAM size");
            this.base = base;
            this.bytes = new byte[size];
            for (int i = 0; i < size; i++) bytes[i] = (byte)((i * 37 + 0x5B) & 0xFF);
        }

        private int offset(long address, int width) {
            long delta = address - base;
            if (width < 1 || width > 32 || delta < 0 || delta > bytes.length - width)
                throw new IllegalArgumentException("outside finite owned RAM");
            return (int)delta;
        }
        private long raw(long address, int width) {
            int at = offset(address, width);
            long value = 0;
            for (int i = 0; i < width; i++) value |= (long)(bytes[at + i] & 0xFF) << (i * 8);
            return value;
        }
        private void put(long address, int width, long value) {
            int at = offset(address, width);
            for (int i = 0; i < width; i++) bytes[at + i] = (byte)(value >>> (i * 8));
        }
        private void log(String method, long address, int width, long value) {
            String hex = String.format(Locale.ROOT, "0x%0" + (width * 2) + "X", value);
            accesses.add(new Access(method, address, width, hex));
        }
        private Bits128 raw128(long address) {
            offset(address, 16);
            return new Bits128(raw(address, 8), raw(address + 8, 8));
        }
        private void put128(long address, Bits128 value) {
            Objects.requireNonNull(value);
            offset(address, 16);
            put(address, 8, value.lowBits());
            put(address + 8, 8, value.highBits());
        }
        public void seedQword(long address, long value) { put(address, 8, value); }
        public void seedDword(long address, int value) { put(address, 4, Integer.toUnsignedLong(value)); }
        public long peekQword(long address) { return raw(address, 8); }
        public List<Access> events() { return List.copyOf(accesses); }

        @Override public int readDword(long address) {
            long value = raw(address, 4); log("readDword", address, 4, value); return (int)value;
        }
        @Override public long readQword(long address) {
            long value = raw(address, 8); log("readQword", address, 8, value); return value;
        }
        @Override public int readUnsignedByte(long address) {
            long value = raw(address, 1); log("readUnsignedByte", address, 1, value); return (int)value;
        }
        @Override public int readUnsignedWord(long address) {
            long value = raw(address, 2); log("readUnsignedWord", address, 2, value); return (int)value;
        }
        @Override public void writeDword(long address, int value) {
            long bits = Integer.toUnsignedLong(value); put(address, 4, bits); log("writeDword", address, 4, bits);
        }
        @Override public void writeQword(long address, long value) {
            put(address, 8, value); log("writeQword", address, 8, value);
        }
        @Override public void writeByte(long address, int value) {
            long bits = value & 0xFFL; put(address, 1, bits); log("writeByte", address, 1, bits);
        }
        @Override public void writeWord(long address, int value) {
            long bits = value & 0xFFFFL; put(address, 2, bits); log("writeWord", address, 2, bits);
        }
        @Override public synchronized int lockedXaddDword(long address, int addend) {
            int old = (int)raw(address, 4);
            put(address, 4, Integer.toUnsignedLong(old + addend));
            accesses.add(new Access("lockedXaddDword", address, 4,
                String.format(Locale.ROOT, "old=0x%08X add=0x%08X", old, addend)));
            return old;
        }
        @Override public Bits128 read128(long address) {
            Bits128 value = raw128(address);
            accesses.add(new Access("read128", address, 16, value.toString()));
            return value;
        }
        @Override public void write128(long address, Bits128 value) {
            put128(address, value); accesses.add(new Access("write128", address, 16, value.toString()));
        }
        @Override public void write128NonTemporal(long address, Bits128 value) {
            put128(address, value); accesses.add(new Access("write128NonTemporal", address, 16, value.toString()));
        }
        @Override public FullCopy437Api.Bits256 read256(long address) {
            offset(address, 32);
            FullCopy437Api.Bits256 value = new FullCopy437Api.Bits256(raw128(address), raw128(address + 16));
            accesses.add(new Access("read256", address, 32, value.toString()));
            return value;
        }
        @Override public void write256(long address, FullCopy437Api.Bits256 value) {
            Objects.requireNonNull(value); offset(address, 32);
            put128(address, value.low()); put128(address + 16, value.high());
            accesses.add(new Access("write256", address, 32, value.toString()));
        }
        @Override public void write256NonTemporal(long address, FullCopy437Api.Bits256 value) {
            Objects.requireNonNull(value); offset(address, 32);
            put128(address, value.low()); put128(address + 16, value.high());
            accesses.add(new Access("write256NonTemporal", address, 32, value.toString()));
        }
        @Override public void sfence() { accesses.add(new Access("sfence", 0L, 0, "")); }

    }
}
