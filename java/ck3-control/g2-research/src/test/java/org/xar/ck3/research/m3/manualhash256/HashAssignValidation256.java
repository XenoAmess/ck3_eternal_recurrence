package org.xar.ck3.research.m3.manualhash256;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAssign855db0;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m3.hash188.HashInsertC39C60;
import org.xar.ck3.research.m3.hash256.HashAssignBinding256;

/** New finite public consumer witnesses, no old Test or physical Native fixture. */
public final class HashAssignValidation256 {
    private static int checks;
    private static int directEvents;
    private static int integrationEvents;
    private HashAssignValidation256() { }

    public static void main(String[] args) {
        qualifiedSitesPreserveAssignEffectsAndFailures();
        actualHashCallerAndUnqualifiedCallsRetainTheirContracts();
        equal(directEvents, 21, "direct literal event count");
        System.out.println("PASS groups=2 direct_literal_events=" + directEvents
                + " integration_observed_events=" + integrationEvents + " checks=" + checks);
    }

    private static void qualifiedSitesPreserveAssignEffectsAndFailures() {
        long dest = 0x5000L, source = 0x6000L;
        for (long site : new long[] {0xC39DA4L, 0xC39DFBL}) {
            Memory memory = new Memory();
            memory.descriptor(dest, "old", 15L);
            memory.text(source, "abc");
            AssignPorts assign = new AssignPorts(memory, dest, source, 3L);
            Fallback fallback = new Fallback();
            HashInsert188Api.Ports bound = HashAssignBinding256.bind(memory, assign, fallback);
            equal(memory.events.size(), 0, "factory has no RAM effects");
            bound.assign855db0(memory, site, dest, source, 3L);
            literal(memory, List.of(new Event("Q", dest + 0x18L, 15L, 0L),
                    new Event("W", dest + 0x10L, 3L, 0L),
                    new Event("COPY", dest, source, 3L), new Event("B", dest + 3L, 0L, 0L)));
            equal(memory.peek64(dest + 0x10L), 3L, "inline length");
            textEquals(memory, dest, "abc");
            equal(memory.peekByte(dest + 3L), 0, "inline terminator");
            equal(assign.copyCalls, 1, "one mature copy callback");
            equal(fallback.assignCalls, 0, "qualified site bypasses assign fallback");
        }

        Memory grown = new Memory();
        grown.descriptor(dest, "old", 16L);
        grown.seed64(dest, 0x7000L);
        for (int i = 0; i < 32; i++) { grown.seedByte(source + i, i + 1); }
        AssignPorts allocation = new AssignPorts(grown, 0x8000L, source, 32L);
        allocation.allocation = 0x8000L;
        allocation.descriptorToMutate = dest;
        HashAssignBinding256.bind(grown, allocation, new Fallback())
                .assign855db0(grown, 0xC39DFBL, dest, source, 32L);
        literal(grown, List.of(new Event("Q", dest + 0x18L, 16L, 0L),
                new Event("ALLOC", 48L, 0x8000L, 0L),
                new Event("W", dest + 0x10L, 32L, 0L), new Event("W", dest + 0x18L, 47L, 0L),
                new Event("COPY", 0x8000L, source, 32L), new Event("B", 0x8020L, 0L, 0L),
                new Event("Q", dest, 0x7400L, 0L), new Event("FREE", 0x7400L, 17L, 0L),
                new Event("W", dest, 0x8000L, 0L)));
        equal(grown.peek64(dest), 0x8000L, "late new pointer");
        equal(grown.peek64(dest + 0x18L), 47L, "growth capacity");
        equal(allocation.freeCalls, 1, "fresh pointer freed once");
        for (int i = 0; i < 32; i++) { equal(grown.peekByte(0x8000L + i), i + 1, "copied DATA byte"); }

        Memory failed = new Memory();
        failed.descriptor(dest, "old", 15L);
        failed.text(source, "x");
        AssignPorts throwsCopy = new AssignPorts(failed, dest, source, 1L);
        throwsCopy.failure = new IllegalStateException("owned copy failure256");
        RuntimeException caught = null;
        try {
            HashAssignBinding256.bind(failed, throwsCopy, new Fallback())
                    .assign855db0(failed, 0xC39DA4L, dest, source, 1L);
        } catch (RuntimeException failure) { caught = failure; }
        same(caught, throwsCopy.failure, "copy exception identity");
        literal(failed, List.of(new Event("Q", dest + 0x18L, 15L, 0L),
                new Event("W", dest + 0x10L, 1L, 0L), new Event("COPY", dest, source, 1L)));
        equal(failed.peekByte(dest + 1L), 'l', "no copy or terminator after failure");

        Memory unsupported = new Memory();
        unsupported.seed64(dest + 0x18L, 0L);
        RequestAssign855db0.UnsupportedSourcePath stopped = null;
        try {
            HashAssignBinding256.bind(unsupported,
                    new AssignPorts(unsupported, dest, source, -1L), new Fallback())
                    .assign855db0(unsupported, 0xC39DFBL, dest, source, -1L);
        } catch (RequestAssign855db0.UnsupportedSourcePath failure) { stopped = failure; }
        check(stopped != null, "unsigned oversized length keeps explicit source stop");
        equal(stopped.targetRva(), 0x8523A0L, "unexecuted helper boundary");
        equal(stopped.trapSiteRva(), 0x855EB5L, "source trap boundary");
        equal(stopped.knownR8(), -1L, "full unsigned length bits");
        literal(unsupported, List.of(new Event("Q", dest + 0x18L, 0L, 0L)));
    }

    private static void actualHashCallerAndUnqualifiedCallsRetainTheirContracts() {
        long map = 0x1000L, data = 0x2000L, descriptor = 0x4000L, output = 0x9000L;
        long bucket = data + 0x28L;
        Memory memory = new Memory();
        memory.seed64(map + 8L, data);
        memory.seed32(map + 0x10L, 0);
        memory.seed32(map + 0x14L, 1);
        memory.seedByte(map + 0x18L, 3);
        memory.seed32(map + 0x1CL, 0x40000000); // exact finite software ratio1/1, limit2.
        memory.seedByte(data + 4L, 1);
        memory.descriptor(data + 8L, "aaa", 15L);
        memory.seed32(bucket, 7);
        memory.seedByte(bucket + 4L, 1);
        memory.descriptor(bucket + 8L, "old", 15L);
        memory.seedByte(bucket + 0x2CL, 0);
        memory.descriptor(descriptor, "xyz", 15L);
        AssignPorts assign = new AssignPorts(memory, bucket + 8L, descriptor, 3L);
        Fallback fallback = new Fallback();
        fallback.hashMemory = memory;
        fallback.hashDescriptor = descriptor;
        fallback.hashRight = data + 8L;
        HashInsert188Api.Ports bound = HashAssignBinding256.bind(memory, assign, fallback);
        long returned = HashInsertC39C60.execute(new HashInsert188Api.Input(
                0x140000000L, map, output, 0, descriptor, new HashInsert188Api.Scratch(0xA000L)), memory, bound);
        equal(returned, output, "actual parent return");
        equal(assign.copyCalls, 1, "actual caller reaches mature assign");
        equal(fallback.equalCalls, 1, "one source comparison");
        equal(fallback.assignCalls, 0, "actual assign never opaque fallback");
        equal(memory.peek64(output), bucket, "actual output bucket");
        equal(memory.peekByte(output + 8L), 1, "actual inserted flag");
        equal(memory.peek32(map + 0x10L), 1, "actual incremented map count");
        textEquals(memory, bucket + 8L, "xyz");
        equal(memory.peek64(bucket + 0x18L), 3L, "assigned descriptor length");
        integrationEvents = memory.events.size(); // observed, not a frozen full-parent trace claim.

        int before = memory.events.size();
        Memory foreign = new Memory();
        fallback.allowAssign = true;
        for (HashInsert188Api.Memory supplied : new HashInsert188Api.Memory[] {memory, foreign, null}) {
            long site = supplied == memory ? 0x123456L : 0xC39DA4L;
            bound.assign855db0(supplied, site, -1L, Long.MIN_VALUE, -7L);
            check(new AssignCall(supplied, site, -1L, Long.MIN_VALUE, -7L).equals(fallback.lastAssign),
                    "unqualified callback preserves full arguments and Memory identity");
        }
        equal(fallback.assignCalls, 3, "one delegate for each unqualified input");
        equal(memory.events.size(), before, "nonqualifications do not touch captured RAM");
        equal(foreign.events.size(), 0, "foreign RAM untouched");
        equal(bound.equal3f6d2b0(foreign, 0x31L, -2L, -3L), 0x81234567, "full int fallback return");
        bound.terminal4232cf4(foreign, 0x32L);
        equal(fallback.terminal2Calls, 1, "old terminal overload retained");
        RuntimeException caught = null;
        try { bound.terminal4232cf4(foreign, 0x33L, Long.MIN_VALUE); }
        catch (RuntimeException failure) { caught = failure; }
        same(caught, fallback.terminalMarker, "new terminal overload exception identity");
        equal(fallback.terminal3Calls, 1, "new terminal overload retained");
        equal(fallback.lastEntryRsp, Long.MIN_VALUE, "full terminal entry frame forwarded");
    }

    private record Event(String operation, long address, long value, long extra) { }
    private record AssignCall(HashInsert188Api.Memory memory, long site, long rcx, long rdx, long r8) { }

    private static final class Memory implements HashAssignBinding256.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final List<Event> events = new ArrayList<>();
        private void seedByte(long address, int value) { bytes.put(address, (byte) value); }
        private void store(long address, long value, int width) {
            for (int i = 0; i < width; i++) { seedByte(address + i, (int) (value >>> (8 * i))); }
        }
        private long load(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) { throw new AssertionError("unseeded DATA byte " + Long.toHexString(address + i)); }
                value |= (b.byteValue() & 0xFFL) << (8 * i);
            }
            return value;
        }
        private void seed64(long address, long value) { store(address, value, 8); }
        private void seed32(long address, int value) { store(address, value, 4); }
        private long peek64(long address) { return load(address, 8); }
        private int peek32(long address) { return (int) load(address, 4); }
        private int peekByte(long address) { return (int) load(address, 1); }
        private void text(long address, String text) {
            for (int i = 0; i < text.length(); i++) { seedByte(address + i, text.charAt(i)); }
        }
        private void descriptor(long address, String text, long capacity) {
            for (int i = 0; i < 32; i++) { seedByte(address + i, 0); }
            text(address, text);
            seed64(address + 0x10L, text.length());
            seed64(address + 0x18L, capacity);
        }
        @Override public long readPointer(long address) {
            long value = peek64(address); events.add(new Event("Q", address, value, 0L)); return value;
        }
        @Override public int readInt32(long address) {
            int value = peek32(address); events.add(new Event("I", address, value, 0L)); return value;
        }
        @Override public void writeInt32(long address, int value) {
            events.add(new Event("D", address, value, 0L)); store(address, value, 4);
        }
        @Override public void writeInt64(long address, long value) {
            events.add(new Event("W", address, value, 0L)); store(address, value, 8);
        }
        @Override public int readUnsigned8(long address) {
            int value = peekByte(address); events.add(new Event("U", address, value, 0L)); return value;
        }
        @Override public void write8(long address, int value) {
            events.add(new Event("B", address, value & 0xFF, 0L)); seedByte(address, value);
        }
        @Override public HashInsert188Api.Bytes16 read128(long address) {
            long low = peek64(address), high = peek64(address + 8L);
            events.add(new Event("R128", address, low, high)); return new HashInsert188Api.Bytes16(low, high);
        }
        @Override public void write128(long address, HashInsert188Api.Bytes16 value) {
            events.add(new Event("W128", address, value.low(), value.high()));
            seed64(address, value.low()); seed64(address + 8L, value.high());
        }
        @Override public int readUnsignedByte(long address) { return readUnsigned8(address); }
        @Override public void writeByte(long address, byte value) { write8(address, value); }
        @Override public void writeInt16(long address, short value) {
            events.add(new Event("H", address, value & 0xFFFF, 0L)); store(address, value, 2);
        }
        @Override public RequestE92780.Raw128 readRaw128(long address) {
            long low = peek64(address), high = peek64(address + 8L);
            events.add(new Event("RRAW128", address, low, high)); return new RequestE92780.Raw128(low, high);
        }
        @Override public void writeRaw128(long address, RequestE92780.Raw128 value) {
            events.add(new Event("WRAW128", address, value.low(), value.high()));
            seed64(address, value.low()); seed64(address + 8L, value.high());
        }
    }

    private static final class AssignPorts implements RequestAssign855db0.Ports {
        private final Memory memory;
        private final long expectedDest, expectedSource, expectedLength;
        private long allocation, descriptorToMutate;
        private RuntimeException failure;
        private int copyCalls, freeCalls;
        private AssignPorts(Memory memory, long dest, long source, long length) {
            this.memory = memory; expectedDest = dest; expectedSource = source; expectedLength = length;
        }
        @Override public long call856db0(long bytes) {
            equal(bytes, 48L, "bounded growth request"); check(allocation != 0, "allocation configured");
            memory.events.add(new Event("ALLOC", bytes, allocation, 0L)); return allocation;
        }
        @Override public void call4226860(long dest, long source, long length) {
            equal(dest, expectedDest, "copy destination"); equal(source, expectedSource, "copy source");
            equal(length, expectedLength, "full length argument"); copyCalls++;
            memory.events.add(new Event("COPY", dest, source, length));
            if (failure != null) { throw failure; }
            check(length >= 0 && length <= 32, "finite fixture copy");
            for (long i = 0; i < length; i++) { memory.seedByte(dest + i, memory.peekByte(source + i)); }
            if (descriptorToMutate != 0) { memory.seed64(descriptorToMutate, 0x7400L); }
        }
        @Override public void call4223f44(long pointer, long bytes, OptionalLong r8) {
            check(OptionalLong.empty().equals(r8), "small oldblock R8 remains unknown"); freeCalls++;
            memory.events.add(new Event("FREE", pointer, bytes, 0L));
        }
    }

    private static final class Fallback implements HashInsert188Api.Ports {
        private Memory hashMemory;
        private long hashDescriptor, hashRight, lastEntryRsp;
        private boolean allowAssign;
        private int assignCalls, equalCalls, terminal2Calls, terminal3Calls;
        private AssignCall lastAssign;
        private final RuntimeException terminalMarker = new IllegalStateException("owned terminal marker256");
        @Override public int equal3f6d2b0(HashInsert188Api.Memory m, long site, long rcx, long rdx) {
            equalCalls++;
            if (site == 0xC39CCAL) {
                same(m, hashMemory, "actual equality Memory"); equal(rcx, hashDescriptor, "actual left");
                equal(rdx, hashRight, "actual right"); return 0;
            }
            return 0x81234567;
        }
        @Override public void assign855db0(HashInsert188Api.Memory m, long site, long rcx, long rdx, long r8) {
            check(allowAssign, "qualified callback must not fallback"); assignCalls++;
            lastAssign = new AssignCall(m, site, rcx, rdx, r8);
        }
        @Override public void terminal4232cf4(HashInsert188Api.Memory m, long site) { terminal2Calls++; }
        @Override public void terminal4232cf4(HashInsert188Api.Memory m, long site, long entryRsp) {
            terminal3Calls++; lastEntryRsp = entryRsp; throw terminalMarker;
        }
        @Override public void copy855f00(HashInsert188Api.Memory m, long s, long a, long b) { unexpected(); }
        @Override public void rehashC3a400(HashInsert188Api.Memory m, long s, long a) { unexpected(); }
        @Override public void insertC3b960(HashInsert188Api.Memory m, long s, long a, long b, int h, long d) { unexpected(); }
        @Override public void destroy856050(HashInsert188Api.Memory m, long s, long a) { unexpected(); }
        @Override public int capacity86e160(HashInsert188Api.Memory m, long s, int a, int b) { unexpected(); return 0; }
        @Override public void reserveC3b700(HashInsert188Api.Memory m, long s, long a, int b) { unexpected(); }
        @Override public void overflow86f210(HashInsert188Api.Memory m, long s, long a, long b) { unexpected(); }
        private void unexpected() { throw new AssertionError("unexpected opaque port"); }
    }

    private static void literal(Memory memory, List<Event> expected) {
        check(memory.events.equals(expected), "literal order expected " + expected + " got " + memory.events);
        directEvents += memory.events.size();
    }
    private static void textEquals(Memory memory, long address, String text) {
        for (int i = 0; i < text.length(); i++) { equal(memory.peekByte(address + i), text.charAt(i), "DATA text"); }
    }
    private static void check(boolean value, String message) {
        checks++; if (!value) { throw new AssertionError(message); }
    }
    private static void equal(long actual, long expected, String message) {
        check(actual == expected, message + ": " + actual + " != " + expected);
    }
    private static void same(Object actual, Object expected, String message) { check(actual == expected, message); }
}
