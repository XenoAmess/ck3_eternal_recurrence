package org.xar.ck3.research.m3.index183;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.index183.RegistrationIndex183Api.*;
import org.xar.ck3.research.m3.index183.RegistrationIndexWitness183Api.*;

public final class RegistrationIndexWitnessHost183 {
    private RegistrationIndexWitnessHost183() { }

    private static final class State implements Memory, Ports {
        private final Map<Long, Byte> bytes = new LinkedHashMap<>();
        private final List<Step> steps;
        private int cursor;

        private State(Scene scene) {
            if (scene.initial().size() > 256 || scene.steps().size() > 256 || scene.finalCells().size() > 256)
                throw new AssertionError("finite scene bounds");
            steps = List.copyOf(scene.steps());
            for (Cell cell : scene.initial()) put(cell, true);
        }

        private static int width(Kind kind) {
            return switch (kind) {
                case R8, W8 -> 1;
                case R32, W32 -> 4;
                case R64, W64 -> 8;
                case R128, W128 -> 16;
                case COMPARE -> throw new AssertionError("COMPARE has typed arguments, no memory width");
            };
        }

        private static long masked(long value, int width) {
            return width == 1 ? value & 0xFFL : width == 4 ? value & 0xFFFFFFFFL : value;
        }

        private long peek(long address, int width) {
            long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                if (b == null) throw new AssertionError("unmapped byte at " + Long.toUnsignedString(address + i, 16));
                value |= (b & 0xFFL) << (8 * i);
            }
            return value;
        }

        private void poke(long address, int width, long value, boolean initialize) {
            for (int i = 0; i < width; i++) {
                long at = address + i;
                byte b = (byte) (value >>> (8 * i));
                if (!initialize && !bytes.containsKey(at)) throw new AssertionError("write outside mapped storage");
                Byte old = bytes.put(at, b);
                if (initialize && old != null && old.byteValue() != b) throw new AssertionError("conflicting initial byte");
            }
        }

        private void put(Cell cell, boolean initialize) {
            int w = cell.width();
            if (w != 1 && w != 4 && w != 8 && w != 16) throw new AssertionError("invalid cell width");
            poke(cell.address(), Math.min(w, 8), cell.low(), initialize);
            if (w == 16) poke(cell.address() + 8, 8, cell.high(), initialize);
        }

        private Step next(Kind kind) {
            if (cursor >= steps.size()) throw new AssertionError("unexpected source event " + kind);
            Step step = steps.get(cursor++);
            if (step.kind() != kind) throw new AssertionError("global event order: expected " + step.kind() + " got " + kind);
            return step;
        }

        private void memoryEvent(Kind kind, long address, long low, long high) {
            Step step = next(kind);
            int w = width(kind);
            if (step.address() != address || masked(step.low(), w) != masked(low, w)
                    || step.high() != (w == 16 ? high : 0)
                    || !step.arguments().isEmpty() || step.returned() != 0 || !step.effects().isEmpty())
                throw new AssertionError("source memory event address/width/value differs at " + (cursor - 1));
        }

        @Override public long readPointer(long address) {
            long value = peek(address, 8);
            memoryEvent(Kind.R64, address, value, 0);
            return value;
        }

        @Override public int readInt32(long address) {
            int value = (int) peek(address, 4);
            memoryEvent(Kind.R32, address, value, 0);
            return value;
        }

        @Override public int readUnsigned8(long address) {
            int value = (int) peek(address, 1);
            memoryEvent(Kind.R8, address, value, 0);
            return value;
        }

        @Override public Bytes16 read128(long address) {
            Bytes16 value = new Bytes16(peek(address, 8), peek(address + 8, 8));
            memoryEvent(Kind.R128, address, value.low(), value.high());
            return value;
        }

        @Override public void writeInt32(long address, int value) {
            memoryEvent(Kind.W32, address, value, 0);
            poke(address, 4, value, false);
        }

        @Override public void writeInt64(long address, long value) {
            memoryEvent(Kind.W64, address, value, 0);
            poke(address, 8, value, false);
        }

        @Override public void write8(long address, int value) {
            memoryEvent(Kind.W8, address, value, 0);
            poke(address, 1, value, false);
        }

        @Override public void write128(long address, Bytes16 value) {
            memoryEvent(Kind.W128, address, value.low(), value.high());
            poke(address, 8, value.low(), false);
            poke(address + 8, 8, value.high(), false);
        }

        @Override public int compare42270b0(Memory memory, long callSiteRva, long rcx, long rdx, long signedR8) {
            if (memory != this) throw new AssertionError("opaque callback changed shared Memory");
            Step step = next(Kind.COMPARE);
            List<Long> args = List.of(callSiteRva, rcx, rdx, signedR8);
            if (step.address() != 0 || step.low() != 0 || step.high() != 0 || !step.arguments().equals(args))
                throw new AssertionError("exact callback site/arguments differ");
            if (step.effects().size() > 64) throw new AssertionError("finite controlled effects");
            for (Cell cell : step.effects()) put(cell, false);
            return step.returned();
        }

        private void verifyFinal(Cell cell) {
            int w = cell.width();
            if (w != 1 && w != 4 && w != 8 && w != 16) throw new AssertionError("invalid final width");
            if (peek(cell.address(), Math.min(w, 8)) != masked(cell.low(), w)
                    || w == 16 && peek(cell.address() + 8, 8) != cell.high())
                throw new AssertionError("final storage differs");
        }
    }

    public static void verify(Scene scene) {
        State state = new State(scene);
        int result = RegistrationIndex3F542C0.find(state, state, scene.input());
        if (result != scene.expectedEax() || state.cursor != state.steps.size())
            throw new AssertionError("return or complete source trace differs");
        for (Cell cell : scene.finalCells()) state.verifyFinal(cell);
    }

    public static void main(String[] args) {
        List<Scene> scenes = RegistrationIndexWitnessBook183.scenes();
        if (scenes.size() != 4) throw new AssertionError("exactly four new scenes required");
        for (Scene scene : scenes) verify(scene);
        System.out.println(scenes.size());
    }
}