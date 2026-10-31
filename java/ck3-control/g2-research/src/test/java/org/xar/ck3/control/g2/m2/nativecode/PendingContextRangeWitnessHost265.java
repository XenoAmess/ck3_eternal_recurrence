package org.xar.ck3.control.g2.m2.nativecode;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextRangeInsertBCB7C0.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextRangeInsertBCB7C0.Calls;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextRangeWitness265Api.*;

public final class PendingContextRangeWitnessHost265 {
    private PendingContextRangeWitnessHost265() { }

    private static final class State implements Memory, Calls {
        private final Map<Long, Byte> bytes = new LinkedHashMap<>();
        private final List<Step> steps;
        private int cursor;

        private State(Scene scene) {
            if (scene.initial().size() > 256 || scene.steps().size() > 256 || scene.finalCells().size() > 256) throw new AssertionError("finite scene bounds");
            steps = List.copyOf(scene.steps());
            for (Cell cell : scene.initial()) put(cell, true);
        }

        private static int width(Kind kind) {
            return switch (kind) {
                case R32, W32 -> 4;
                case R64, W64 -> 8;
                case ALLOCATE, RELEASE, COPY, FINALIZE -> throw new AssertionError("CALL has typed arguments, no memory width");
            };
        }

        private static long masked(long value, int w) {
            return w == 4 ? value & 0xFFFFFFFFL : value;
        }

        private long peek(long address, int w) {
            long value = 0;
            for (int i = 0; i < w; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("unmapped byte at " + Long.toUnsignedString(address + i, 16));
                value |= (b & 0xFFL) << (8 * i);
            }
            return value;
        }

        private void poke(long address, int w, long value, boolean initialize) {
            for (int i = 0; i < w; i++) {
                long at = address + i;
                byte b = (byte) (value >>> (8 * i));
                if (!initialize && !bytes.containsKey(at)) throw new AssertionError("write outside mapped storage");
                Byte old = bytes.put(at, b);
                if (initialize && old != null && old.byteValue() != b) throw new AssertionError("conflicting initial byte");
            }
        }

        private void put(Cell cell, boolean initialize) {
            int w = cell.width();
            if (w != 4 && w != 8) throw new AssertionError("invalid cell width");
            poke(cell.address(), w, cell.value(), initialize);
        }

        private Step next(Kind kind) {
            if (cursor >= steps.size()) throw new AssertionError("unexpected source event " + kind);
            Step step = steps.get(cursor++);
            if (step.kind() != kind) throw new AssertionError("global event order: expected " + step.kind() + " got " + kind);
            return step;
        }

        private void memoryEvent(Kind kind, long address, long value) {
            Step step = next(kind);
            int w = width(kind);
            if (step.address() != address || masked(step.value(), w) != masked(value, w) || !step.arguments().isEmpty() || step.returned() != 0 || !step.effects().isEmpty())
                throw new AssertionError("source memory event address/width/value differs at " + (cursor - 1));
        }

        @Override public int read32(long address) {
            int value = (int) peek(address, 4);
            memoryEvent(Kind.R32, address, value);
            return value;
        }

        @Override public long read64(long address) {
            long value = peek(address, 8);
            memoryEvent(Kind.R64, address, value);
            return value;
        }

        @Override public void write32(long address, int value) {
            memoryEvent(Kind.W32, address, value);
            poke(address, 4, value, false);
        }

        @Override public void write64(long address, long value) {
            memoryEvent(Kind.W64, address, value);
            poke(address, 8, value, false);
        }

        @Override public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.ALLOCATE);
            List<Long> args = List.of(target, rcx, rdx, Integer.toUnsignedLong(r8d));
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args) || step.effects().size() > 64)
                throw new AssertionError("exact callback site/arguments differ");
            for (Cell cell : step.effects()) put(cell, false);
            return step.returned();
        }

        @Override public void release(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.RELEASE);
            List<Long> args = List.of(target, rcx, rdx, Integer.toUnsignedLong(r8d));
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args) || step.returned() != 0 || step.effects().size() > 64)
                throw new AssertionError("exact callback site/arguments differ");
            for (Cell cell : step.effects()) put(cell, false);
        }

        @Override public void call4226860(Memory memory, long rcx, long rdx, long r8) {
            if (memory != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.COPY);
            List<Long> args = List.of(rcx, rdx, r8);
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args) || step.returned() != 0 || step.effects().size() > 64)
                throw new AssertionError("exact callback site/arguments differ");
            for (Cell cell : step.effects()) put(cell, false);
        }

        @Override public void call9CF240(Memory memory, long rcx, long rdx, long r8) {
            if (memory != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.FINALIZE);
            List<Long> args = List.of(rcx, rdx, r8);
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args) || step.returned() != 0 || step.effects().size() > 64)
                throw new AssertionError("exact callback site/arguments differ");
            for (Cell cell : step.effects()) put(cell, false);
        }

        private void verifyFinal(Cell cell) {
            int w = cell.width();
            if (w != 4 && w != 8) throw new AssertionError("invalid final width");
            if (peek(cell.address(), w) != masked(cell.value(), w)) throw new AssertionError("final storage differs");
        }
    }

    public static void verify(Scene scene) {
        State state = new State(scene);
        PendingContextRangeInsertBCB7C0.insert(state, state, scene.input());
        if (state.cursor != state.steps.size()) throw new AssertionError("complete source trace differs");
        for (Cell cell : scene.finalCells()) state.verifyFinal(cell);
    }

    public static void main(String[] args) {
        List<Scene> scenes = PendingContextRangeWitnessBook265.scenes();
        if (scenes.size() != 3) throw new AssertionError("exactly three new scenes required");
        for (Scene scene : scenes) verify(scene);
        System.out.println(scenes.size());
    }
}