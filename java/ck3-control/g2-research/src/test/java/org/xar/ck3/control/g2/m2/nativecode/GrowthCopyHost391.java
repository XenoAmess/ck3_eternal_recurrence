package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Op;
import org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Step;
import org.xar.ck3.control.g2.m2.nativecode.GrowthCopyData391.Scene;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.Copy4226860Api.Bits256;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWithKnownCopy1ACDFB0.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWithKnownCopy1ACDFB0.Calls;

public final class GrowthCopyHost391 {
    private static final int MAX_STEPS = 128;

    public static int verify() {
        List<Scene> scenes = GrowthCopyCases391.scenes();
        if (scenes.size() != 1) {
            throw new AssertionError("Expected exactly one scene");
        }
        Scene scene = scenes.get(0);
        List<Step> steps = scene.steps();
        if (steps.size() > MAX_STEPS) {
            throw new AssertionError("Too many steps");
        }

        Cursor cursor = new Cursor(steps);
        Memory memory = new MemoryImpl(cursor);
        Calls calls = new CallsImpl(cursor, memory);

        boolean result = PendingSlotCapacityWithKnownCopy1ACDFB0.grow(
            memory,
            calls,
            scene.table(),
            scene.requested(),
            scene.moduleBase()
        );

        if (result != scene.expected()) {
            throw new AssertionError("Result mismatch");
        }
        if (cursor.index != steps.size()) {
            throw new AssertionError("Steps not exhausted");
        }
        return 1;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }

    private static final class Cursor {
        int index = 0;
        List<Step> steps;

        Cursor(List<Step> steps) {
            this.steps = steps;
        }

        Step next() {
            if (index >= steps.size()) {
                throw new AssertionError("No more steps");
            }
            Step s = steps.get(index++);
            if (s.op() != Op.ALLOC && s.returned() != 0) {
                throw new AssertionError("Non-ALLOC returned mismatch");
            }
            return s;
        }
    }

    private static final class MemoryImpl implements Memory {
        Cursor c;

        MemoryImpl(Cursor c) {
            this.c = c;
        }

        private int canonical8(int v) {
            return v & 0xFF;
        }

        private int canonical16(int v) {
            return v & 0xFFFF;
        }

        private int canonical32(int v) {
            return v;
        }

        @Override
        public int read8(long address) {
            Step s = c.next();
            if (s.op() != Op.R8) throw new AssertionError("Expected R8");
            if (s.values().size() != 2) throw new AssertionError("R8 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R8 address mismatch");
            return canonical8(s.values().get(1).intValue());
        }

        @Override
        public int read16(long address) {
            Step s = c.next();
            if (s.op() != Op.R16) throw new AssertionError("Expected R16");
            if (s.values().size() != 2) throw new AssertionError("R16 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R16 address mismatch");
            return canonical16(s.values().get(1).intValue());
        }

        @Override
        public int read32(long address) {
            Step s = c.next();
            if (s.op() != Op.R32) throw new AssertionError("Expected R32");
            if (s.values().size() != 2) throw new AssertionError("R32 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R32 address mismatch");
            return canonical32(s.values().get(1).intValue());
        }

        @Override
        public long read64(long address) {
            Step s = c.next();
            if (s.op() != Op.R64) throw new AssertionError("Expected R64");
            if (s.values().size() != 2) throw new AssertionError("R64 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R64 address mismatch");
            return s.values().get(1);
        }

        @Override
        public Bits128 read128(long address) {
            Step s = c.next();
            if (s.op() != Op.R128) throw new AssertionError("Expected R128");
            if (s.values().size() != 3) throw new AssertionError("R128 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R128 address mismatch");
            return new Bits128(s.values().get(1), s.values().get(2));
        }

        @Override
        public Bits256 read256(long address) {
            Step s = c.next();
            if (s.op() != Op.R256) throw new AssertionError("Expected R256");
            if (s.values().size() != 5) throw new AssertionError("R256 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("R256 address mismatch");
            Bits128 low = new Bits128(s.values().get(1), s.values().get(2));
            Bits128 high = new Bits128(s.values().get(3), s.values().get(4));
            return new Bits256(low, high);
        }

        @Override
        public void write8(long address, int value) {
            Step s = c.next();
            if (s.op() != Op.W8) throw new AssertionError("Expected W8");
            if (s.values().size() != 2) throw new AssertionError("W8 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W8 address mismatch");
            if (canonical8(s.values().get(1).intValue()) != canonical8(value)) throw new AssertionError("W8 value mismatch");
        }

        @Override
        public void write16(long address, int value) {
            Step s = c.next();
            if (s.op() != Op.W16) throw new AssertionError("Expected W16");
            if (s.values().size() != 2) throw new AssertionError("W16 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W16 address mismatch");
            if (canonical16(s.values().get(1).intValue()) != canonical16(value)) throw new AssertionError("W16 value mismatch");
        }

        @Override
        public void write32(long address, int value) {
            Step s = c.next();
            if (s.op() != Op.W32) throw new AssertionError("Expected W32");
            if (s.values().size() != 2) throw new AssertionError("W32 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W32 address mismatch");
            if (canonical32(s.values().get(1).intValue()) != canonical32(value)) throw new AssertionError("W32 value mismatch");
        }

        @Override
        public void write64(long address, long value) {
            Step s = c.next();
            if (s.op() != Op.W64) throw new AssertionError("Expected W64");
            if (s.values().size() != 2) throw new AssertionError("W64 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W64 address mismatch");
            if (s.values().get(1) != value) throw new AssertionError("W64 value mismatch");
        }

        @Override
        public void write128(long address, Bits128 value) {
            Step s = c.next();
            if (s.op() != Op.W128) throw new AssertionError("Expected W128");
            if (s.values().size() != 3) throw new AssertionError("W128 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W128 address mismatch");
            if (s.values().get(1) != value.low() || s.values().get(2) != value.high()) throw new AssertionError("W128 value mismatch");
        }

        @Override
        public void write256(long address, Bits256 value) {
            Step s = c.next();
            if (s.op() != Op.W256) throw new AssertionError("Expected W256");
            if (s.values().size() != 5) throw new AssertionError("W256 arity mismatch");
            if (s.values().get(0) != address) throw new AssertionError("W256 address mismatch");
            if (s.values().get(1) != value.low128().low() || s.values().get(2) != value.low128().high()) throw new AssertionError("W256 low mismatch");
            if (s.values().get(3) != value.high128().low() || s.values().get(4) != value.high128().high()) throw new AssertionError("W256 high mismatch");
        }

        @Override
        public void storeFence() {
            Step s = c.next();
            if (s.op() != Op.FENCE) throw new AssertionError("Expected FENCE");
            if (!s.values().isEmpty()) throw new AssertionError("FENCE arity mismatch");
        }
    }

    private static final class CallsImpl implements Calls {
        Cursor c;
        final Memory expectedMemory;

        CallsImpl(Cursor c, Memory expectedMemory) {
            this.c = c;
            this.expectedMemory = expectedMemory;
        }

        @Override
        public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.op() != Op.ALLOC) throw new AssertionError("Expected ALLOC");
            if (s.values().size() != 4) throw new AssertionError("ALLOC arity mismatch");
            if (s.values().get(0) != target) throw new AssertionError("ALLOC target mismatch");
            if (s.values().get(1) != rcx) throw new AssertionError("ALLOC rcx mismatch");
            if (s.values().get(2) != rdx) throw new AssertionError("ALLOC rdx mismatch");
            if (s.values().get(3) != Integer.toUnsignedLong(r8d)) throw new AssertionError("ALLOC r8d mismatch");
            return s.returned();
        }

        @Override
        public void release(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.op() != Op.FREE) throw new AssertionError("Expected FREE");
            if (s.values().size() != 4) throw new AssertionError("FREE arity mismatch");
            if (s.values().get(0) != target) throw new AssertionError("FREE target mismatch");
            if (s.values().get(1) != rcx) throw new AssertionError("FREE rcx mismatch");
            if (s.values().get(2) != rdx) throw new AssertionError("FREE rdx mismatch");
            if (s.values().get(3) != Integer.toUnsignedLong(r8d)) throw new AssertionError("FREE r8d mismatch");
            if (s.returned() != 0) throw new AssertionError("FREE returned mismatch");
        }

        @Override
        public void call4226F10(Memory memory, long rcx, int edx, long r8) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.op() != Op.SET) throw new AssertionError("Expected SET");
            if (s.values().size() != 3) throw new AssertionError("SET arity mismatch");
            if (s.values().get(0) != rcx) throw new AssertionError("SET rcx mismatch");
            if (s.values().get(1) != Integer.toUnsignedLong(edx)) throw new AssertionError("SET edx mismatch");
            if (s.values().get(2) != r8) throw new AssertionError("SET r8 mismatch");
            if (s.returned() != 0) throw new AssertionError("SET returned mismatch");
        }
    }
}