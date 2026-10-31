package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
import org.xar.ck3.control.g2.m2.nativecode.PendingContextTailWitness271Api.*;

public final class PendingContextTailWitnessHost271 {
    private static final int MAX_STEPS = 256;

    public static void verify(Scene scene) {
        if (scene.steps().size() > MAX_STEPS) throw new AssertionError("TOO_MANY_STEPS");
        if (scene.initial().size() > 256 || scene.finalCells().size() > 256) throw new AssertionError("TOO_MANY_CELLS");
        State state = new State(scene);
        long result = PendingContextTailCopy2503880.copy(state, state, scene.destination(), scene.source());
        if (result != scene.expectedReturn()) throw new AssertionError("MISMATCH_RETURN");
        if (state.cursor != scene.steps().size()) throw new AssertionError("NOT_EXHAUSTED");
        for (Cell c : scene.finalCells()) state.verifyFinal(c);
    }

    public static void main(String[] args) {
        List<Scene> scenes = PendingContextTailWitnessBook271.scenes();
        if (scenes.size() != 2) throw new AssertionError("EXACT_TWO_SCENES");
        for (Scene scene : scenes) {
            verify(scene);
        }
        System.out.println(2);
    }

    private static final class State implements PendingContextTailCopy2503880.Memory, PendingContextTailCopy2503880.Calls {
        private final Map<Long, Byte> bytes = new LinkedHashMap<>();
        private final List<Step> steps;
        private int cursor;

        private State(Scene scene) {
            steps = List.copyOf(scene.steps());
            for (Cell c : scene.initial()) put(c, true);
        }

        private static int width(Kind kind) {
            return switch (kind) {
                case R8 -> 1;
                case R64, W64 -> 8;
                case HELPER, VIRTUAL -> throw new AssertionError("CALL has typed arguments, no memory width");
            };
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
            if (w != 1 && w != 8) throw new AssertionError("invalid cell width");
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
            if (step.address() != address || masked(step.value(), w) != masked(value, w)
                    || !step.arguments().isEmpty() || step.effects().size() != 0)
                throw new AssertionError("source memory event address/width/value differs at " + (cursor - 1));
        }

        private static long masked(long value, int w) {
            return w == 1 ? value & 0xFFL : value;
        }

        @Override public int read8(long address) {
            long value = peek(address, 1);
            memoryEvent(Kind.R8, address, value);
            return (int) value;
        }

        @Override public long read64(long address) {
            long value = peek(address, 8);
            memoryEvent(Kind.R64, address, value);
            return value;
        }

        @Override public void write64(long address, long value) {
            memoryEvent(Kind.W64, address, value);
            poke(address, 8, value, false);
        }

        @Override public long call25037E0(PendingContextTailCopy2503880.Memory m, long rcx, long rdx) {
            if (m != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.HELPER);
            List<Long> args = List.of(rcx, rdx);
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args))
                throw new AssertionError("exact callback site/arguments differ");
            if (step.effects().size() > 64) throw new AssertionError("finite controlled effects");
            for (Cell c : step.effects()) put(c, false);
            return step.returned();
        }

        @Override public void virtual10(PendingContextTailCopy2503880.Memory m, long target, long rcx, long rdx, long r8) {
            if (m != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.VIRTUAL);
            List<Long> args = List.of(target, rcx, rdx, r8);
            if (step.address() != 0 || step.value() != 0 || !step.arguments().equals(args))
                throw new AssertionError("exact callback site/arguments differ");
            if (step.effects().size() > 64) throw new AssertionError("finite controlled effects");
            for (Cell c : step.effects()) put(c, false);
        }

        private void verifyFinal(Cell cell) {
            int w = cell.width();
            if (w != 1 && w != 8) throw new AssertionError("invalid final width");
            if (peek(cell.address(), w) != masked(cell.value(), w)) throw new AssertionError("final storage differs");
        }
    }
}