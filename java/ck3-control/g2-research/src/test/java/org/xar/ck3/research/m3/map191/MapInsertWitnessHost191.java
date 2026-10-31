package org.xar.ck3.research.m3.map191;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Input;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Memory;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Ports;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Bytes16;
import org.xar.ck3.research.m3.map191.MapInsertWitness191Api.Cell;
import org.xar.ck3.research.m3.map191.MapInsertWitness191Api.Kind;
import org.xar.ck3.research.m3.map191.MapInsertWitness191Api.Step;
import org.xar.ck3.research.m3.map191.MapInsertWitness191Api.Scene;

public final class MapInsertWitnessHost191 {
    private MapInsertWitnessHost191() { }

    public static void main(String[] args) {
        List<Scene> scenes = MapInsertWitnessBook191.scenes();
        if (scenes.size() != 3) throw new AssertionError("Expected 3 literal Scenes");
        int totalScenes = 0;
        int totalSteps = 0;
        int totalPortCalls = 0;
        int totalFinalCells = 0;

        for (Scene scene : scenes) {
            totalScenes++;
            Script script = new Script(scene);

            for (Cell cell : scene.initial()) {
                script.seed(cell);
            }

            long actualReturn = MapInsertC3B960.execute(scene.input(), script, script);

            if (actualReturn != scene.expectedReturn()) {
                throw new AssertionError("Return mismatch: expected " + scene.expectedReturn() + " got " + actualReturn);
            }

            if (script.cursor != scene.steps().size()) {
                throw new AssertionError("Cursor not exhausted: " + script.cursor + " vs " + scene.steps().size());
            }

            for (Cell cell : scene.finalCells()) {
                script.verifyFinal(cell);
            }

            totalSteps += scene.steps().size();
            totalPortCalls += script.portCount;
            totalFinalCells += scene.finalCells().size();

            System.out.println("Scene: " + scene.name() + " Steps: " + scene.steps().size() + " Ports: " + script.portCount + " FinalCells: " + scene.finalCells().size() + " Return: " + actualReturn);
        }

        System.out.println("Total Scenes: " + totalScenes + " Total Steps: " + totalSteps + " Total Ports: " + totalPortCalls + " Total FinalCells: " + totalFinalCells);
    }

    private static final class Script implements Memory, Ports {
        private final List<Step> steps;
        private final Map<Long, Byte> store = new HashMap<>();
        private int cursor = 0;
        private int portCount = 0;

        Script(Scene scene) {
            this.steps = List.copyOf(scene.steps());
        }

        private void seed(Cell cell) {
            applyEffect(cell);
        }

        private void verifyFinal(Cell cell) {
            long addr = cell.address();
            int width = cell.width();
            long low = cell.low();
            long high = cell.high();

            if (width == 1) {
                if (!store.containsKey(addr)) throw new AssertionError("Missing byte at " + Long.toHexString(addr));
                byte actual = store.get(addr);
                byte expected = (byte)low;
                if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(addr));
            } else if (width == 4) {
                for (int i = 0; i < 4; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else if (width == 8) {
                for (int i = 0; i < 8; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else if (width == 16) {
                for (int i = 0; i < 8; i++) {
                    long a = addr + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(low >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
                for (int i = 0; i < 8; i++) {
                    long a = addr + 8 + i;
                    if (!store.containsKey(a)) throw new AssertionError("Missing byte at " + Long.toHexString(a));
                    byte actual = store.get(a);
                    byte expected = (byte)(high >>> (8 * i));
                    if (actual != expected) throw new AssertionError("Byte mismatch at " + Long.toHexString(a));
                }
            } else {
                throw new AssertionError("Unsupported width: " + width);
            }
        }

        private void applyEffect(Cell cell) {
            long addr = cell.address();
            int width = cell.width();
            long low = cell.low();
            long high = cell.high();

            if (width == 1) {
                store.put(addr, (byte)low);
            } else if (width == 4) {
                for (int i = 0; i < 4; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
            } else if (width == 8) {
                for (int i = 0; i < 8; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
            } else if (width == 16) {
                for (int i = 0; i < 8; i++) {
                    store.put(addr + i, (byte)(low >>> (8 * i)));
                }
                for (int i = 0; i < 8; i++) {
                    store.put(addr + 8 + i, (byte)(high >>> (8 * i)));
                }
            } else {
                throw new AssertionError("Unsupported width: " + width);
            }
        }

        private Step nextStep(Kind expectedKind, long expectedAddress) {
            if (cursor >= steps.size()) {
                throw new AssertionError("Step cursor exhausted");
            }
            Step step = steps.get(cursor);
            if (step.kind() != expectedKind) {
                throw new AssertionError("Kind mismatch: expected " + expectedKind + " got " + step.kind());
            }
            if (step.address() != expectedAddress) {
                throw new AssertionError("Address mismatch: expected " + Long.toHexString(expectedAddress) + " got " + Long.toHexString(step.address()));
            }
            cursor++;
            return step;
        }

        private long readBytes(long address, int width) {
            long result = 0;
            for (int i = 0; i < width; i++) {
                long addr = address + i;
                if (!store.containsKey(addr)) {
                    throw new AssertionError("Missing byte at " + Long.toHexString(addr));
                }
                byte b = store.get(addr);
                result |= ((long)b & 0xFFL) << (8 * i);
            }
            return result;
        }

        private void writeBytes(long address, int width, long value) {
            for (int i = 0; i < width; i++) {
                long addr = address + i;
                byte b = (byte)(value >>> (8 * i));
                store.put(addr, b);
            }
        }

        @Override
        public long readPointer(long address) {
            Step step = nextStep(Kind.R64, address);
            long actual = readBytes(address, 8);
            if (step.low() != actual) {
                throw new AssertionError("R64 read mismatch at " + Long.toHexString(address));
            }
            return actual;
        }

        @Override
        public int readInt32(long address) {
            Step step = nextStep(Kind.R32, address);
            long actual = readBytes(address, 4);
            if ((step.low() & 0xFFFFFFFFL) != actual) {
                throw new AssertionError("R32 read mismatch at " + Long.toHexString(address));
            }
            return (int)actual;
        }

        @Override
        public void writeInt32(long address, int value) {
            Step step = nextStep(Kind.W32, address);
            long expected = Integer.toUnsignedLong(value);
            if ((step.low() & 0xFFFFFFFFL) != expected) {
                throw new AssertionError("W32 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 4, expected);
        }

        @Override
        public void writeInt64(long address, long value) {
            Step step = nextStep(Kind.W64, address);
            if (step.low() != value) {
                throw new AssertionError("W64 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 8, value);
        }

        @Override
        public int readUnsigned8(long address) {
            Step step = nextStep(Kind.R8, address);
            long actual = readBytes(address, 1);
            if ((step.low() & 0xFFL) != actual) {
                throw new AssertionError("R8 read mismatch at " + Long.toHexString(address));
            }
            return (int)(actual & 0xFF);
        }

        @Override
        public void write8(long address, int value) {
            Step step = nextStep(Kind.W8, address);
            long expected = (long)value & 0xFFL;
            if ((step.low() & 0xFFL) != expected) {
                throw new AssertionError("W8 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 1, expected);
        }

        @Override
        public Bytes16 read128(long address) {
            Step step = nextStep(Kind.R128, address);
            long low = readBytes(address, 8);
            long high = readBytes(address + 8, 8);
            if (step.low() != low || step.high() != high) {
                throw new AssertionError("R128 read mismatch at " + Long.toHexString(address));
            }
            return new Bytes16(low, high);
        }

        @Override
        public void write128(long address, Bytes16 value) {
            Step step = nextStep(Kind.W128, address);
            if (step.low() != value.low() || step.high() != value.high()) {
                throw new AssertionError("W128 value mismatch at " + Long.toHexString(address));
            }
            writeBytes(address, 8, value.low());
            writeBytes(address + 8, 8, value.high());
        }

        @Override
        public int equal3f6d2b0(Memory memory, long siteRva, long rcx, long rdx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.EQUAL, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("EQUAL args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx) throw new AssertionError("EQUAL args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
            return (int)step.returned();
        }





        @Override
        public void insertSlotC3cf10(Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.INSERT_SLOT, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 4) throw new AssertionError("INSERT_SLOT args size mismatch");
            if (args.get(0) != bucket || args.get(1) != (long) probe
                    || args.get(2) != (long) hash || args.get(3) != descriptor) {
                throw new AssertionError("INSERT_SLOT args mismatch");
            }
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void rehashC3a400(Memory memory, long siteRva, long map) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.REHASH, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 1) throw new AssertionError("REHASH args size mismatch");
            if (args.get(0) != map) throw new AssertionError("REHASH args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void insertC3a5f0(Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.INSERT_OTHER, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 4) throw new AssertionError("INSERT_OTHER args size mismatch");
            if (args.get(0) != map || args.get(1) != result || args.get(2) != (long)hash || args.get(3) != descriptor) throw new AssertionError("INSERT_OTHER args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void destroy856050(Memory memory, long siteRva, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.DESTROY, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 1) throw new AssertionError("DESTROY args size mismatch");
            if (args.get(0) != descriptor) throw new AssertionError("DESTROY args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public int capacity86e160(Memory memory, long siteRva, int ecx, int edx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.CAPACITY, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("CAPACITY args size mismatch");
            if (args.get(0) != (long)ecx || args.get(1) != (long)edx) throw new AssertionError("CAPACITY args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
            return (int)step.returned();
        }

        @Override
        public void reserveC3b700(Memory memory, long siteRva, long map, int edx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.RESERVE, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("RESERVE args size mismatch");
            if (args.get(0) != map || args.get(1) != (long)edx) throw new AssertionError("RESERVE args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void overflow86f210(Memory memory, long siteRva, long rcx, long rdx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.OVERFLOW, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("OVERFLOW args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx) throw new AssertionError("OVERFLOW args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void terminal4232cf4(Memory memory, long siteRva) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.TERMINAL, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 0) throw new AssertionError("TERMINAL args size mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }
    }
}