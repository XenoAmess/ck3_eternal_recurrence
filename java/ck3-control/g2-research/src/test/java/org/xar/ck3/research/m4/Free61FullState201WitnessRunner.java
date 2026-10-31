package org.xar.ck3.research.m4;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.CallStep;

public final class Free61FullState201WitnessRunner {
    public static void verify(Free61FullState201WitnessApi.Witness w) {
        Image img = new Image(w.memorySeed());
        int[] cursor = new int[1];
        List<CallStep> events = w.events();
        Calls calls = new Calls() {
            @Override
            public NormalReturn tail(org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail t) {
                throw new AssertionError("tail not expected");
            }
            @Override
            public long readGsQword58() {
                throw new AssertionError("readGsQword58 not expected");
            }
            @Override
            public VolatileBits invoke(org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call c) {
                if (cursor[0] >= events.size()) throw new AssertionError("extra call");
                CallStep step = events.get(cursor[0]++);
                if (!step.expected().equals(c)) throw new AssertionError("call mismatch");
                Map<Long, Integer> before = img.snapshot();
                if (!step.expectedMemoryBefore().equals(before)) throw new AssertionError("memory before mismatch");
                img.mutate(step.mutation());
                return step.normalPost();
            }
        };
        NormalReturn actual = Free61FullState201.execute(w.entry(), img, calls);
        if (!actual.equals(w.expected())) throw new AssertionError("return mismatch");
        if (!img.snapshot().equals(w.expectedFinalBytes())) throw new AssertionError("final bytes mismatch");
        if (cursor[0] != events.size()) throw new AssertionError("events not consumed");
    }

    public static final class Image implements Memory {
        private final Map<Long, Integer> bytes;
        private final List<Long> readQwordAddresses;
        private final List<Long> writeQwordAddresses;

        public Image(Map<Long, Integer> seed) {
            this.bytes = new java.util.HashMap<>();
            for (Map.Entry<Long, Integer> e : seed.entrySet()) {
                if (e.getValue() < 0 || e.getValue() > 255) throw new IllegalArgumentException("invalid byte");
                this.bytes.put(e.getKey(), e.getValue());
            }
            this.readQwordAddresses = new java.util.ArrayList<>();
            this.writeQwordAddresses = new java.util.ArrayList<>();
        }

        public Map<Long, Integer> snapshot() {
            return new java.util.HashMap<>(this.bytes);
        }

        public void mutate(Map<Long, Integer> changes) {
            for (Map.Entry<Long, Integer> e : changes.entrySet()) {
                if (e.getValue() < 0 || e.getValue() > 255) throw new IllegalArgumentException("invalid byte");
                this.bytes.put(e.getKey(), e.getValue());
            }
        }

        public List<Long> readQwordAddresses() {
            return new java.util.ArrayList<>(this.readQwordAddresses);
        }

        public List<Long> writeQwordAddresses() {
            return new java.util.ArrayList<>(this.writeQwordAddresses);
        }

        private int getByte(long addr) {
            Integer v = this.bytes.get(addr);
            if (v == null) throw new UnsupportedOperationException("unknown read");
            return v;
        }

        private void setByte(long addr, int val) {
            if (val < 0 || val > 255) throw new IllegalArgumentException("invalid byte");
            this.bytes.put(addr, val);
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
            this.readQwordAddresses.add(addressBits);
            long b0 = getByte(addressBits);
            long b1 = getByte(addressBits + 1);
            long b2 = getByte(addressBits + 2);
            long b3 = getByte(addressBits + 3);
            long b4 = getByte(addressBits + 4);
            long b5 = getByte(addressBits + 5);
            long b6 = getByte(addressBits + 6);
            long b7 = getByte(addressBits + 7);
            return (b0) | (b1 << 8) | (b2 << 16) | (b3 << 24) | (b4 << 32) | (b5 << 40) | (b6 << 48) | (b7 << 56);
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
            throw new UnsupportedOperationException("lockedXaddDword unsupported");
        }

        @Override
        public void writeQword(long addressBits, long valueBits) {
            this.writeQwordAddresses.add(addressBits);
            setByte(addressBits, (int)(valueBits & 0xFF));
            setByte(addressBits + 1, (int)((valueBits >>> 8) & 0xFF));
            setByte(addressBits + 2, (int)((valueBits >>> 16) & 0xFF));
            setByte(addressBits + 3, (int)((valueBits >>> 24) & 0xFF));
            setByte(addressBits + 4, (int)((valueBits >>> 32) & 0xFF));
            setByte(addressBits + 5, (int)((valueBits >>> 40) & 0xFF));
            setByte(addressBits + 6, (int)((valueBits >>> 48) & 0xFF));
            setByte(addressBits + 7, (int)((valueBits >>> 56) & 0xFF));
        }

        @Override
        public void writeByte(long addressBits, int lowByteBits) {
            setByte(addressBits, lowByteBits & 0xFF);
        }

        @Override
        public Bits128 read128(long addressBits) {
            long low = readQword(addressBits);
            long high = readQword(addressBits + 8);
            return new Bits128(low, high);
        }

        @Override
        public void write128(long addressBits, Bits128 valueBits) {
            writeQword(addressBits, valueBits.lowBits());
            writeQword(addressBits + 8, valueBits.highBits());
        }
    }
}