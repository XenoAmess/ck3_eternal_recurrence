package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Cell;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Scene;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityWitnessData237.Step;

/** Owner complete ordered script consumer, after two whole model candidates were rejected. */
public final class PendingSlotCapacityWitnessHost237 {
    private PendingSlotCapacityWitnessHost237() { }
    private static void require(boolean condition, String reason) {
        if (!condition) throw new AssertionError(reason);
    }
    public static int verify(List<Scene> scenes) {
        require(scenes != null && !scenes.isEmpty() && scenes.size() <= 16, "scene count");
        int count = 0;
        for (Scene scene : scenes) {
            require(scene != null, "null scene");
            Fixture fixture = new Fixture(scene);
            boolean actual = PendingSlotCapacity1ACDFB0.grow(fixture, fixture, scene.tableAddress(), scene.requestedCapacity());
            require(actual == scene.expectedAl(), scene.name() + " AL");
            fixture.finish();
            count++;
        }
        return count;
    }
    public static void main(String[] args) {
        System.out.println(verify(PendingSlotCapacityWitnessBook237.scenes()));
    }
    private static final class Fixture implements PendingSlotCapacity1ACDFB0.Memory, PendingSlotCapacity1ACDFB0.Calls {
        private final Scene scene;
        private final Map<Long, Byte> bytes = new HashMap<>();
        private int cursor;
        Fixture(Scene scene) {
            this.scene = scene;
            require(scene.initial() != null && scene.steps() != null && scene.finalCells() != null, "null data");
            require(scene.initial().size() <= 256 && scene.steps().size() <= 512 && scene.finalCells().size() <= 256, "data count");
            for (Cell cell : scene.initial()) initialize(cell);
            for (Step step : scene.steps()) {
                require(step != null && step.effects() != null && step.effects().size() <= 256, "step data");
                boolean callback = step.kind().equals("RESERVE") || step.kind().equals("SET");
                require(callback || step.effects().isEmpty(), "effects outside callback");
                require(step.kind().equals("R8") || step.kind().equals("R32") || step.kind().equals("R64")
                        || step.kind().equals("W32") || step.kind().equals("W64") || callback, "unknown kind");
                require(step.kind().equals("SET") || step.bytes() == 0, "unexpected byte count");
            }
        }
        private static void width(int width) { require(width == 1 || width == 4 || width == 8, "byte width"); }
        private static long masked(long value, int width) {
            return width == 8 ? value : width == 4 ? value & 0xFFFFFFFFL : value & 0xFFL;
        }
        private void initialize(Cell cell) {
            require(cell != null, "null cell"); width(cell.width());
            for (int i = 0; i < cell.width(); i++) bytes.put(cell.address() + i, (byte) (cell.value() >>> (i * 8)));
        }
        private long peek(long address, int width) {
            width(width); long value = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                require(b != null, scene.name() + " uninitialized " + Long.toUnsignedString(address + i, 16));
                value |= (b & 0xFFL) << (i * 8);
            }
            return value;
        }
        private Step take(String kind, long address, long value, long count) {
            require(cursor < scene.steps().size(), scene.name() + " extra step " + cursor);
            Step step = scene.steps().get(cursor++);
            require(step.kind().equals(kind) && step.address() == address && step.value() == value && step.bytes() == count,
                    scene.name() + " step " + (cursor - 1) + " expected=" + step + " actual=" + kind + ":" + Long.toUnsignedString(address, 16) + ":" + value + ":" + count);
            return step;
        }
        private long read(String kind, long address, int width) {
            long value = peek(address, width); take(kind, address, value, 0); return value;
        }
        @Override public int read8(long address) { return (int) read("R8", address, 1); }
        @Override public int read32(long address) { return (int) read("R32", address, 4); }
        @Override public long read64(long address) { return read("R64", address, 8); }
        @Override public void write32(long address, int value) {
            take("W32", address, Integer.toUnsignedLong(value), 0); initialize(new Cell(address, 4, value));
        }
        @Override public void write64(long address, long value) {
            take("W64", address, value, 0); initialize(new Cell(address, 8, value));
        }
        private void callback(String kind, PendingSlotCapacity1ACDFB0.Memory memory, long rcx, int edx, long r8) {
            require(memory == this, "callback memory identity");
            Step step = take(kind, rcx, Integer.toUnsignedLong(edx), r8);
            for (Cell cell : step.effects()) initialize(cell);
        }
        @Override public void call1ACE4B0(PendingSlotCapacity1ACDFB0.Memory memory, long rcx, int edx) {
            callback("RESERVE", memory, rcx, edx, 0);
        }
        @Override public void call4226F10(PendingSlotCapacity1ACDFB0.Memory memory, long rcx, int edx, long r8) {
            callback("SET", memory, rcx, edx, r8);
        }
        void finish() {
            require(cursor == scene.steps().size(), scene.name() + " unconsumed steps " + cursor);
            for (Cell cell : scene.finalCells()) require(peek(cell.address(), cell.width()) == masked(cell.value(), cell.width()), scene.name() + " final cell " + cell);
        }
    }
}
