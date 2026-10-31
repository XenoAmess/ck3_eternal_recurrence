package org.xar.ck3.research.m5;

import java.util.*;

public final class GovernmentLookupWithRoot179Probe {
    private GovernmentLookupWithRoot179Probe() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new AssertionError("no arguments");
        verify(new GovernmentLookupWithRoot179Fixtures());
    }

    public static void verify(GovernmentLookupHelper176WitnessApi.Book book) {
        List<GovernmentLookupHelper176WitnessApi.Witness> witnesses = book.witnesses();
        if (witnesses.size() != 1) throw new AssertionError("Expected exactly 1 witness, got " + witnesses.size());
        Set<String> names = new HashSet<>();
        for (GovernmentLookupHelper176WitnessApi.Witness w : witnesses) {
            if (w.name().isBlank()) throw new AssertionError("Blank witness name");
            if (names.contains(w.name())) throw new AssertionError("Duplicate witness name: " + w.name());
            names.add(w.name());
        }
        int count = 0;
        for (GovernmentLookupHelper176WitnessApi.Witness w : witnesses) {
            try {
                runWitness(w);
                count++;
            } catch (Throwable t) {
                throw new AssertionError("Witness " + w.name() + " failed: " + t.getMessage(), t);
            }
        }
        System.out.println("cases=" + count);
    }

    private static void runWitness(GovernmentLookupHelper176WitnessApi.Witness w) {
        Map<Long, Integer> seedMap = new HashMap<>();
        for (GovernmentLookupHelper176WitnessApi.SeedByte sb : w.memorySeed()) {
            if (sb.byteBits() < 0 || sb.byteBits() > 255) throw new AssertionError("Out of range seed byte");
            if (seedMap.containsKey(sb.addressBits())) throw new AssertionError("Conflicting seed byte at 0x" + Long.toHexString(sb.addressBits()));
            seedMap.put(sb.addressBits(), sb.byteBits());
        }

        List<GovernmentLookupHelper176WitnessApi.CallStep> callSteps = new ArrayList<>(w.calls());
        List<GovernmentLookupHelper176WitnessApi.AtomicStep> atomicSteps = new ArrayList<>(w.atomics());
        List<Long> gsScript = new ArrayList<>(w.gsQword58());

        MemoryImpl mem = new MemoryImpl(seedMap, atomicSteps);
        mem.trackedSlot=w.entry().rspBits()-0x30L;
        mem.trackedReturn=w.entry().imageBaseBits()+0x3f5f980L;
        CallsImpl calls = new CallsImpl(mem, callSteps, atomicSteps, gsScript);

        int[] loopCursor={0};
        GovernmentLookupHelper176Api.LoopBudget budget=(header,node,end)->{
            if (loopCursor[0]>=w.loops().size()) throw new AssertionError("unexpected loop header");
            var observed=new GovernmentLookupHelper176WitnessApi.LoopStep(header,node,end);
            if (!observed.equals(w.loops().get(loopCursor[0]++))) throw new AssertionError("loop event mismatch");
        };
        GovernmentLookupHelper176Api.NormalReturn actual = GovernmentLookupWithRoot179.execute(w.entry(), mem, calls, budget);
        if (loopCursor[0]!=w.loops().size()) throw new AssertionError("unconsumed loop events");
        GovernmentLookupHelper176Api.NormalReturn expected = w.expected();

        if (!actual.equals(expected)) throw new AssertionError("NormalReturn mismatch");

        if (!calls.isDone()) throw new AssertionError("Scripts not fully consumed");
        if (mem.trackedWrites!=1) throw new AssertionError("C090 CALL slot must be written once, observed "+mem.trackedWrites);

        Map<Long, Integer> finalBytes = new HashMap<>(seedMap);
        for (Map.Entry<Long, Integer> e : w.expectedFinalBytes().entrySet()) {
            if (e.getValue() < 0 || e.getValue() > 255) throw new AssertionError("out of range final byte");
            finalBytes.put(e.getKey(), e.getValue());
        }

        if (!mem.bytes.equals(finalBytes)) throw new AssertionError("complete final image mismatch");

        for (Map.Entry<Long, Integer> e : finalBytes.entrySet()) {
            long addr = e.getKey();
            int expectedByte = e.getValue();
            int actualByte = mem.readUnsignedByte(addr);
            if (actualByte != expectedByte) throw new AssertionError("Final byte mismatch at 0x" + Long.toHexString(addr) + ": expected " + expectedByte + " got " + actualByte);
        }
    }

    private static class MemoryImpl implements GovernmentLookupWithRoot179Api.Memory {
        private final Map<Long, Integer> bytes;
        private final List<GovernmentLookupHelper176WitnessApi.AtomicStep> atomics;
        private int atomicCursor;
        private long trackedSlot,trackedReturn;
        private int trackedWrites;

        MemoryImpl(Map<Long, Integer> seed, List<GovernmentLookupHelper176WitnessApi.AtomicStep> atomics) {
            this.bytes = new HashMap<>(seed);
            this.atomics = atomics;
        }

        boolean atomicsDone() { return atomicCursor == atomics.size(); }

        private int getByte(long addr) {
            Integer v = bytes.get(addr);
            if (v == null) throw new AssertionError("Absent byte at 0x" + Long.toHexString(addr));
            return v;
        }

        private void setByte(long addr, int val) {
            bytes.put(addr, val & 0xFF);
        }

        @Override
        public int readDword(long addressBits) {
            int b0 = getByte(addressBits);
            int b1 = getByte(addressBits + 1);
            int b2 = getByte(addressBits + 2);
            int b3 = getByte(addressBits + 3);
            return (b0) | (b1 << 8) | (b2 << 16) | (b3 << 24);
        }

        @Override
        public long readQword(long addressBits) {
            long lo = readDword(addressBits) & 0xFFFFFFFFL;
            long hi = readDword(addressBits + 4) & 0xFFFFFFFFL;
            return lo | (hi << 32);
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            return getByte(addressBits);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            setByte(addressBits, valueBits & 0xFF);
            setByte(addressBits + 1, (valueBits >>> 8) & 0xFF);
            setByte(addressBits + 2, (valueBits >>> 16) & 0xFF);
            setByte(addressBits + 3, (valueBits >>> 24) & 0xFF);
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            int old = readDword(addressBits);
            int next = old + addendBits;
            if (atomicCursor >= atomics.size()) throw new AssertionError("unexpected atomic");
            var observed = new GovernmentLookupHelper176WitnessApi.AtomicStep(addressBits, addendBits, old, next);
            if (!observed.equals(atomics.get(atomicCursor++))) throw new AssertionError("atomic event mismatch");
            writeDword(addressBits, next);
            return old;
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            if (addressBits==trackedSlot) {
                trackedWrites++;
                if(valueBits!=trackedReturn) throw new AssertionError("wrong C090 CALL return value");
            }
            writeDword(addressBits, (int)(valueBits & 0xFFFFFFFF));
            writeDword(addressBits + 4, (int)(valueBits >>> 32));
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            setByte(addressBits, lowByteBits);
        }

        @Override
        public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
            long lo = readQword(addressBits);
            long hi = readQword(addressBits + 8);
            return new GovernmentPrimaryTail155Api.Bits128(lo, hi);
        }

        @Override
        public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
            writeQword(addressBits, valueBits.lowBits());
            writeQword(addressBits + 8, valueBits.highBits());
        }
    }

    private static class CallsImpl implements GovernmentLookupHelper176Api.Calls {
        private final MemoryImpl mem;
        private final List<GovernmentLookupHelper176WitnessApi.CallStep> callSteps;
        private final List<Long> gsScript;
        private int callIdx = 0;
        private int gsIdx = 0;

        CallsImpl(MemoryImpl mem, List<GovernmentLookupHelper176WitnessApi.CallStep> callSteps,
                  List<GovernmentLookupHelper176WitnessApi.AtomicStep> atomicSteps,
                  List<Long> gsScript) {
            this.mem = mem;
            this.callSteps = callSteps;
            this.gsScript = gsScript;
        }

        public boolean isDone() {
            return callIdx == callSteps.size() && mem.atomicsDone() && gsIdx == gsScript.size();
        }

        @Override
        public long readGsQword58() {
            if (gsIdx >= gsScript.size()) throw new AssertionError("GS script exhausted");
            return gsScript.get(gsIdx++);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            if (callIdx >= callSteps.size()) throw new AssertionError("Call steps exhausted");
            GovernmentLookupHelper176WitnessApi.CallStep step = callSteps.get(callIdx++);

            GovernmentPrimaryTail155Api.OpaqueCall expected = step.expected();
            if (!call.equals(expected)) throw new AssertionError("OpaqueCall mismatch");

            for (Map.Entry<Long, Integer> e : step.expectedMemoryBefore().entrySet()) {
                long addr = e.getKey();
                int expectedVal = e.getValue();
                int actualVal = mem.readUnsignedByte(addr);
                if (actualVal != expectedVal) throw new AssertionError("Memory before call mismatch at 0x" + Long.toHexString(addr));
            }

            for (GovernmentLookupHelper176WitnessApi.SeedByte sb : step.mutation()) {
                if (sb.byteBits() < 0 || sb.byteBits() > 255) throw new AssertionError("out of range mutation");
                mem.setByte(sb.addressBits(), sb.byteBits());
            }

            return step.normalPost();
        }
    }
}
