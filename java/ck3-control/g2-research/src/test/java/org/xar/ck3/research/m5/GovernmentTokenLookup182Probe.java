package org.xar.ck3.research.m5;

import java.util.*;
import org.xar.ck3.research.m5.GovernmentTokenLookup182WitnessApi.*;

public final class GovernmentTokenLookup182Probe {
    private GovernmentTokenLookup182Probe() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new AssertionError("no arguments");
        verify(new GovernmentTokenLookup182Fixtures());
    }

    public static void verify(Book book) {
        List<Witness> witnesses = book.witnesses();
        if (witnesses.size() != 3) throw new AssertionError("Expected exactly 3 witnesses, got " + witnesses.size());
        Set<String> names = new HashSet<>();
        for (Witness w : witnesses) {
            if (w.name().isBlank()) throw new AssertionError("Blank witness name");
            if (names.contains(w.name())) throw new AssertionError("Duplicate witness name: " + w.name());
            names.add(w.name());
        }
        int count = 0;
        for (Witness w : witnesses) {
            try {
                runWitness(w);
                count++;
            } catch (Throwable t) {
                throw new AssertionError("Witness " + w.name() + " failed: " + t.getMessage(), t);
            }
        }
        System.out.println("cases=" + count);
    }

    private static void runWitness(Witness w) {
        Map<Long, Integer> initialBytes = new HashMap<>();
        for (SeedByte sb : w.memorySeed()) {
            if (sb.byteBits() < 0 || sb.byteBits() > 255) throw new AssertionError("Out of range seed byte");
            if (initialBytes.containsKey(sb.addressBits())) throw new AssertionError("Conflicting seed byte at 0x" + Long.toHexString(sb.addressBits()));
            initialBytes.put(sb.addressBits(), sb.byteBits());
        }

        List<Event> events = w.events();
        Recorder rec = new Recorder(initialBytes, events);

        GovernmentTokenLookup182Api.NormalReturn actual = GovernmentTokenLookup182.execute(
            w.entry(), rec, rec, rec, rec
        );

        if (!actual.equals(w.expected())) throw new AssertionError("NormalReturn mismatch");
        if (rec.cursor != events.size()) throw new AssertionError("Events not fully consumed");

        Map<Long, Integer> expectedFinal = new HashMap<>(initialBytes);
        for (Map.Entry<Long, Integer> e : w.expectedFinalBytes().entrySet()) {
            if (e.getValue() < 0 || e.getValue() > 255) throw new AssertionError("out of range final byte");
            expectedFinal.put(e.getKey(), e.getValue());
        }

        if (!rec.bytes.equals(expectedFinal)) throw new AssertionError("complete final image mismatch");
    }

    private static class Recorder implements GovernmentTokenLookup182Api.Memory, GovernmentTokenLookup182Api.Calls, GovernmentTokenLookup182Api.Pause, GovernmentTokenLookup182Api.LoopBudget {
        final Map<Long, Integer> bytes;
        final List<Event> events;
        int cursor = 0;

        Recorder(Map<Long, Integer> seed, List<Event> events) {
            this.bytes = new HashMap<>(seed);
            this.events = events;
        }

        private int getByte(long addr) {
            Integer v = bytes.get(addr);
            if (v == null) throw new AssertionError("Absent byte at 0x" + Long.toHexString(addr));
            return v;
        }

        private void setByte(long addr, int val) {
            bytes.put(addr, val & 0xFF);
        }

        private int readDwordHelper(long addressBits) {
            int b0 = getByte(addressBits);
            int b1 = getByte(addressBits + 1);
            int b2 = getByte(addressBits + 2);
            int b3 = getByte(addressBits + 3);
            return (b0) | (b1 << 8) | (b2 << 16) | (b3 << 24);
        }

        private void writeDwordHelper(long addressBits, int valueBits) {
            setByte(addressBits, valueBits & 0xFF);
            setByte(addressBits + 1, (valueBits >>> 8) & 0xFF);
            setByte(addressBits + 2, (valueBits >>> 16) & 0xFF);
            setByte(addressBits + 3, (valueBits >>> 24) & 0xFF);
        }

        private long readQwordHelper(long addressBits) {
            long lo = readDwordHelper(addressBits) & 0xFFFFFFFFL;
            long hi = readDwordHelper(addressBits + 4) & 0xFFFFFFFFL;
            return lo | (hi << 32);
        }

        @Override
        public int readUnsignedWord(long addressBits) {
            int b0 = getByte(addressBits);
            int b1 = getByte(addressBits + 1);
            return (b0) | (b1 << 8);
        }

        @Override
        public void writeWord(long addressBits, int lowWordBits) {
            setByte(addressBits, lowWordBits & 0xFF);
            setByte(addressBits + 1, (lowWordBits >>> 8) & 0xFF);
        }

        @Override
        public int readDword(long addressBits) {
            return readDwordHelper(addressBits);
        }

        @Override
        public long readQword(long addressBits) {
            return readQwordHelper(addressBits);
        }

        @Override
        public int readUnsignedByte(long addressBits) {
            return getByte(addressBits);
        }

        @Override
        public void writeDword(long addressBits, int valueBits) {
            writeDwordHelper(addressBits, valueBits);
        }

        @Override
        public int lockedXaddDword(long addressBits, int addendBits) {
            if (cursor >= events.size()) throw new AssertionError("unexpected atomic");
            Event e = events.get(cursor++);
            if (!(e instanceof AtomicStep)) throw new AssertionError("Expected AtomicStep");
            AtomicStep step = (AtomicStep) e;

            if (step.addressBits() != addressBits) throw new AssertionError("Atomic address mismatch");
            if (step.addendBits() != addendBits) throw new AssertionError("Atomic addend mismatch");

            int old = readDwordHelper(addressBits);
            if (old != step.oldBits()) throw new AssertionError("Atomic old mismatch");

            int stored = old + addendBits;
            if (stored != step.storedBits()) throw new AssertionError("Atomic stored mismatch");

            writeDwordHelper(addressBits, stored);
            return old;
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            writeDwordHelper(addressBits, (int)(valueBits & 0xFFFFFFFF));
            writeDwordHelper(addressBits + 4, (int)(valueBits >>> 32));
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            setByte(addressBits, lowByteBits);
        }

        @Override
        public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
            long lo = readQwordHelper(addressBits);
            long hi = readQwordHelper(addressBits + 8);
            return new GovernmentPrimaryTail155Api.Bits128(lo, hi);
        }

        @Override
        public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
            writeQword(addressBits, valueBits.lowBits());
            writeQword(addressBits + 8, valueBits.highBits());
        }

        @Override
        public long readGsQword58() {
            if (cursor >= events.size()) throw new AssertionError("GS script exhausted");
            Event e = events.get(cursor++);
            if (!(e instanceof GsStep)) throw new AssertionError("Expected GsStep");
            GsStep step = (GsStep) e;
            return step.returnedBits();
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
            if (cursor >= events.size()) throw new AssertionError("Call steps exhausted");
            Event e = events.get(cursor++);
            if (!(e instanceof CallStep)) throw new AssertionError("Expected CallStep");
            CallStep step = (CallStep) e;

            if (!call.equals(step.expected())) throw new AssertionError("OpaqueCall mismatch");

            // Check COMPLETE current byte-map equals expectedMemoryBefore
            if (step.expectedMemoryBefore().size() != bytes.size()) throw new AssertionError("Memory before call size mismatch");
            for (Map.Entry<Long, Integer> entry : step.expectedMemoryBefore().entrySet()) {
                long addr = entry.getKey();
                int expectedVal = entry.getValue();
                if (expectedVal < 0 || expectedVal > 255) throw new AssertionError("out of range expected byte");
                int actualVal = getByte(addr);
                if (actualVal != expectedVal) throw new AssertionError("Memory before call mismatch at 0x" + Long.toHexString(addr));
            }

            // Apply explicit mutation in list order
            for (SeedByte sb : step.mutation()) {
                if (sb.byteBits() < 0 || sb.byteBits() > 255) throw new AssertionError("out of range mutation");
                setByte(sb.addressBits(), sb.byteBits());
            }

            return step.normalPost();
        }

        @Override
        public void at(long pauseRva) {
            if (cursor >= events.size()) throw new AssertionError("Pause script exhausted");
            Event e = events.get(cursor++);
            if (!(e instanceof PauseStep)) throw new AssertionError("Expected PauseStep");
            PauseStep step = (PauseStep) e;

            if (step.pauseRva() != pauseRva) throw new AssertionError("Pause RVA mismatch");

            for (SeedByte sb : step.mutation()) {
                if (sb.byteBits() < 0 || sb.byteBits() > 255) throw new AssertionError("out of range mutation");
                setByte(sb.addressBits(), sb.byteBits());
            }
        }

        @Override
        public void beforeStep(long headerRva, long lockAddressBits) {
            if (cursor >= events.size()) throw new AssertionError("Loop budget exhausted");
            Event e = events.get(cursor++);
            if (!(e instanceof LoopStep)) throw new AssertionError("Expected LoopStep");
            LoopStep step = (LoopStep) e;

            if (step.headerRva() != headerRva) throw new AssertionError("Loop header RVA mismatch");
            if (step.lockAddressBits() != lockAddressBits) throw new AssertionError("Loop lock address mismatch");
        }
    }
}
