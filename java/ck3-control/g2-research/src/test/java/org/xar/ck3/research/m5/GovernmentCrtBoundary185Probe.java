package org.xar.ck3.research.m5;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentCrtBoundary185Probe {
    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("args");
        verify(new GovernmentCrtBoundary185Fixtures());
    }

    public static void verify(Book book) {
        List<Witness> ws = book.witnesses();
        if (ws.size() != 5) throw new IllegalArgumentException("count");
        Set<String> names = new HashSet<>();
        Map<Subject, Integer> counts = new HashMap<>();
        for (Witness w : ws) {
            if (w.name().isBlank() || names.contains(w.name())) throw new IllegalArgumentException("name");
            names.add(w.name());
            counts.put(w.subject(), counts.getOrDefault(w.subject(), 0) + 1);
        }
        if (counts.getOrDefault(Subject.RVA_4223A84, 0) != 2 || counts.getOrDefault(Subject.RVA_4223A24, 0) != 1 || counts.getOrDefault(Subject.RVA_4223F24, 0) != 2) throw new IllegalArgumentException("dist");
        for (Witness w : ws) run(w);
        System.out.println("cases=5");
    }

    private static void run(Witness w) {
        Recorder r = new Recorder(w);
        NormalReturn actual;
        switch (w.subject()) {
            case Subject.RVA_4223A84: actual = GovernmentCrtBoundary185.execute3A84(w.entry(), r, r, r); break;
            case Subject.RVA_4223A24: actual = GovernmentCrtBoundary185.execute3A24(w.entry(), r, r); break;
            case Subject.RVA_4223F24: actual = GovernmentCrtBoundary185.execute3F24(w.entry(), r, r); break;
            default: throw new IllegalArgumentException("subject");
        }
        if (!actual.equals(w.expected())) throw new AssertionError("return");
        if (r.cursor != w.events().size()) throw new AssertionError("cursor");
        Map<Long, Integer> expectedFinal = new HashMap<>(w.memorySeed());
        for (Map.Entry<Long, Integer> e : w.expectedFinalBytes().entrySet()) {
            if (e.getValue() < 0 || e.getValue() > 255) throw new AssertionError("finalbyte");
            expectedFinal.put(e.getKey(), e.getValue());
        }
        if (!r.bytes.equals(expectedFinal)) throw new AssertionError("memory");
    }

    private static final class Recorder implements Memory, Calls, LoopBudget {
        private final Map<Long, Integer> bytes;
        private final List<Event> events;
        private int cursor = 0;

        Recorder(Witness w) {
            this.bytes = new HashMap<>();
            for (Map.Entry<Long, Integer> e : w.memorySeed().entrySet()) {
                if (e.getValue() < 0 || e.getValue() > 255) throw new AssertionError("seedbyte");
                this.bytes.put(e.getKey(), e.getValue());
            }
            this.events = w.events();
        }

        private int getByte(long addr) {
            Integer v = bytes.get(addr);
            if (v == null) throw new AssertionError("missingbyte");
            return v;
        }

        // Memory
        public int readDword(long addressBits) {
            return getByte(addressBits) | (getByte(addressBits + 1) << 8) | (getByte(addressBits + 2) << 16) | (getByte(addressBits + 3) << 24);
        }
        public long readQword(long addressBits) {
            long v = 0;
            for (int i = 0; i < 8; i++) v |= ((long) getByte(addressBits + i)) << (i * 8);
            return v;
        }
        public int readUnsignedByte(long addressBits) { return getByte(addressBits); }
        public void writeDword(long addressBits, int valueBits) {
            for (int i = 0; i < 4; i++) bytes.put(addressBits + i, (valueBits >>> (i * 8)) & 0xFF);
        }
        public void writeQword(long addressBits, long valueBits) {
            for (int i = 0; i < 8; i++) bytes.put(addressBits + i, (int)((valueBits >>> (i * 8)) & 0xFF));
        }
        public void writeByte(long addressBits, int lowByteBits) {
            bytes.put(addressBits, lowByteBits & 0xFF);
        }
        public Bits128 read128(long addressBits) {
            long low = 0, high = 0;
            for (int i = 0; i < 8; i++) low |= ((long) getByte(addressBits + i)) << (i * 8);
            for (int i = 0; i < 8; i++) high |= ((long) getByte(addressBits + 8 + i)) << (i * 8);
            return new Bits128(low, high);
        }
        public void write128(long addressBits, Bits128 valueBits) {
            long low = valueBits.lowBits(), high = valueBits.highBits();
            for (int i = 0; i < 8; i++) bytes.put(addressBits + i, (int)((low >>> (i * 8)) & 0xFF));
            for (int i = 0; i < 8; i++) bytes.put(addressBits + 8 + i, (int)((high >>> (i * 8)) & 0xFF));
        }
        public int lockedXaddDword(long addressBits, int addendBits) {
            throw new UnsupportedOperationException("atomic");
        }

        // Calls
        public long readGsQword58() {
            if (cursor >= events.size()) throw new AssertionError("gsorder");
            Event e = events.get(cursor++);
            if (!(e instanceof GsStep)) throw new AssertionError("gsstep");
            return ((GsStep) e).returnedBits();
        }
        public VolatileBits invoke(Call call) {
            if (cursor >= events.size()) throw new AssertionError("callorder");
            Event e = events.get(cursor++);
            if (!(e instanceof CallStep)) throw new AssertionError("callevent");
            CallStep cs = (CallStep) e;
            if (!call.equals(cs.expected())) throw new AssertionError("callequals");
            if (!bytes.equals(cs.expectedMemoryBefore())) throw new AssertionError("callmem");
            for (Map.Entry<Long, Integer> m : cs.mutation().entrySet()) {
                if (m.getValue() < 0 || m.getValue() > 255) throw new AssertionError("mutbyte");
                bytes.put(m.getKey(), m.getValue());
            }
            return cs.normalPost();
        }
        public NormalReturn tail(Tail transfer) {
            if (cursor >= events.size()) throw new AssertionError("tailorder");
            Event e = events.get(cursor++);
            if (!(e instanceof TailStep)) throw new AssertionError("tailevent");
            TailStep ts = (TailStep) e;
            if (!transfer.equals(ts.expected())) throw new AssertionError("tailequals");
            if (!bytes.equals(ts.expectedMemoryBefore())) throw new AssertionError("tailmem");
            for (Map.Entry<Long, Integer> m : ts.mutation().entrySet()) {
                if (m.getValue() < 0 || m.getValue() > 255) throw new AssertionError("mutbyte");
                bytes.put(m.getKey(), m.getValue());
            }
            return ts.normalPost();
        }

        // LoopBudget
        public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            if (cursor >= events.size()) throw new AssertionError("looporder");
            Event e = events.get(cursor++);
            if (!(e instanceof LoopStep)) throw new AssertionError("loopevent");
            LoopStep ls = (LoopStep) e;
            if (loopHeaderRva != ls.loopHeaderRva() || guardAddressBits != ls.guardAddressBits()) throw new AssertionError("loopfields");
        }
    }
}
