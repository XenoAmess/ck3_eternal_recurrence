package org.xar.ck3.research.m3.manager177;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Cell;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Memory;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Outcome;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Ports;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Scene;
import org.xar.ck3.research.m3.manager177.ManagerInitializer177Api.Step;

/** Owner exact source-script consumer. Opaque callbacks apply only explicitly supplied input effects. */
public final class ManagerInitializerWitnessHost177 {
    private ManagerInitializerWitnessHost177() { }
    private static void require(boolean value, String why) { if (!value) throw new AssertionError(why); }
    public static int verify(List<Scene> scenes) {
        require(scenes != null && !scenes.isEmpty() && scenes.size() <= 16, "scene count");
        for (Scene scene : scenes) {
            Fixture fixture = new Fixture(scene);
            Outcome actual = ManagerInitializer3763590.initialize(scene.imageBase(), fixture, fixture);
            require(actual.equals(scene.expected()), scene.name() + " outcome");
            fixture.finish();
        }
        return scenes.size();
    }
    public static void main(String[] args) { System.out.println(verify(ManagerInitializerWitnessBook177.scenes())); }
    private static final class Fixture implements Memory, Ports {
        private final Scene scene;
        private final Map<Long, Byte> bytes = new HashMap<>();
        private int cursor;
        Fixture(Scene scene) {
            require(scene != null && scene.initial() != null && scene.steps() != null && scene.finalCells() != null, "scene shape");
            this.scene = scene;
            require(scene.initial().size() <= 512 && scene.steps().size() <= 512 && scene.finalCells().size() <= 512, "scene limits");
            for (Cell cell : scene.initial()) initialize(cell);
        }
        private static void width(int value) { require(value == 1 || value == 4 || value == 8, "byte width"); }
        private static long mask(long value, int width) { return width == 8 ? value : width == 4 ? value & 0xFFFFFFFFL : value & 0xFFL; }
        private void initialize(Cell cell) {
            require(cell != null, "cell"); width(cell.width());
            for (int i = 0; i < cell.width(); i++) bytes.put(cell.address() + i, (byte) (cell.value() >>> (8 * i)));
        }
        private long peek(long address, int width) {
            width(width); long result = 0;
            for (int i = 0; i < width; i++) {
                Byte b = bytes.get(address + i);
                require(b != null, scene.name() + " uninitialized " + Long.toUnsignedString(address + i, 16));
                result |= (b & 0xFFL) << (8 * i);
            }
            return result;
        }
        private Step take(String kind, long... args) {
            require(cursor < scene.steps().size(), scene.name() + " extra " + kind);
            Step expected = scene.steps().get(cursor++);
            require(expected != null && expected.effects() != null && expected.effects().size() <= 512, "step shape");
            require(kind.equals(expected.kind()) && Arrays.equals(args, expected.args()), scene.name() + " step " + (cursor - 1)
                    + " expected " + expected.kind() + Arrays.toString(expected.args()) + " got " + kind + Arrays.toString(args));
            return expected;
        }
        private long read(String kind, long address, int width) {
            long value = peek(address, width); Step step = take(kind, address, value);
            require(step.effects().isEmpty(), "read effects"); return value;
        }
        private void write(String kind, long address, int width, long value) {
            Step step = take(kind, address, mask(value, width));
            require(step.effects().isEmpty(), "write effects"); initialize(new Cell(address, width, value));
        }
        @Override public long readPointer(long address) { return read("R64", address, 8); }
        @Override public int readInt32(long address) { return (int) read("R32", address, 4); }
        @Override public void writeInt64(long address, long value) { write("W64", address, 8, value); }
        @Override public void writeInt32(long address, int value) { write("W32", address, 4, value); }
        @Override public void writeByte(long address, int value) { write("W8", address, 1, value); }
        private long callback(String kind, Memory memory, long... args) {
            require(memory == this, "callback memory identity"); Step step = take(kind, args);
            for (Cell cell : step.effects()) initialize(cell);
            return step.returned();
        }
        @Override public long context(long site, Memory memory) { return callback("CONTEXT", memory, site); }
        @Override public long allocateObject(long site, Memory memory, int size) { return callback("OBJECT", memory, site, Integer.toUnsignedLong(size)); }
        @Override public long allocatorProvider(long site, Memory memory) { return callback("PROVIDER", memory, site); }
        @Override public void initializeMap(long site, Memory memory, long receiver) { callback("MAP", memory, site, receiver); }
        @Override public long allocateSlots(long site, Memory memory, long target, long allocator, int size, int alignment) {
            return callback("ALLOC", memory, site, target, allocator, Integer.toUnsignedLong(size), Integer.toUnsignedLong(alignment));
        }
        @Override public void copy(long site, Memory memory, long destination, long source, long size) { callback("COPY", memory, site, destination, source, size); }
        @Override public void releaseSlots(long site, Memory memory, long target, long allocator, long data, int alignment) {
            callback("RELEASE", memory, site, target, allocator, data, Integer.toUnsignedLong(alignment));
        }
        @Override public void destroyOld(long site, Memory memory, long object) { callback("DESTROY", memory, site, object); }
        @Override public void freeOld(long site, Memory memory, long object, int size) { callback("FREE", memory, site, object, Integer.toUnsignedLong(size)); }
        void finish() {
            require(cursor == scene.steps().size(), scene.name() + " remaining " + (scene.steps().size() - cursor));
            for (Cell cell : scene.finalCells()) require(peek(cell.address(), cell.width()) == mask(cell.value(), cell.width()), scene.name() + " final " + cell);
        }
    }
}
