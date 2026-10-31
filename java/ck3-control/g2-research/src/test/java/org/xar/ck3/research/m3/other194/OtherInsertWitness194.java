package org.xar.ck3.research.m3.other194;

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

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.map191.MapInsert191Api.Scratch;
public final class OtherInsertWitness194 {
    private OtherInsertWitness194() { }
    public static void main(String[] args) { run(); }
    private static void run() {
        Scene frame = frameScene();
        Script memory = new Script(frame);
        for (Cell cell : frame.initial()) memory.seed(cell);
        MapInsert191Api.Ports bound = OtherInsertCallerBinding194.bind(frame.input().moduleBase(), memory, memory);
        Input input = frame.input();
        bound.insertC3a5f0(memory, 0xC3BBC1L, input.map(), input.output(), input.hash(), input.descriptor());
        if (memory.cursor != frame.steps().size() || memory.portCount != 2) throw new AssertionError("Frame plan/callback count");
        for (Cell cell : frame.finalCells()) memory.verifyFinal(cell);

        Scene delegated = delegatesScene();
        Script fallback = new Script(delegated);
        for (Cell cell : delegated.initial()) fallback.seed(cell);
        MapInsert191Api.Ports forwarded = OtherInsertCallerBinding194.bind(delegated.input().moduleBase(), fallback, fallback);
        int equal = forwarded.equal3f6d2b0(fallback, 0xC3B9CAL, 0x8123456700006000L, 0x9234567800007000L);
        if (equal != 0x12340001) throw new AssertionError("EQUAL return bits changed");
        forwarded.insertSlotC3cf10(fallback, 0xC3BAB8L, 0x22002000L, 254, 0x80000001, 0x44004000L);
        forwarded.rehashC3a400(fallback, 0xC3BBADL, 0x11001000L);
        forwarded.destroy856050(fallback, 0xC3BBCAL, 0x44004000L);
        int capacity = forwarded.capacity86e160(fallback, 0xC3BC2FL, 0x80000002, -1);
        if (capacity != 0x80000003) throw new AssertionError("CAPACITY return bits changed");
        forwarded.reserveC3b700(fallback, 0xC3BC3EL, 0x11001000L, -3);
        forwarded.overflow86f210(fallback, 0xC3BC83L, 0x33003000L, 0x11001000L);
        forwarded.terminal4232cf4(fallback, 0xC3BC88L);
        if (fallback.cursor != 8 || fallback.portCount != 8) throw new AssertionError("Eight delegates not consumed once");
        for (Cell cell : delegated.finalCells()) fallback.verifyFinal(cell);

        Script foreign = new Script(frame);
        int beforeCursor = memory.cursor;
        int beforePorts = memory.portCount;
        boolean foreignRejected = false;
        try {
            bound.insertC3a5f0(foreign, 0xC3BBC1L, input.map(), input.output(), input.hash(), input.descriptor());
        } catch (IllegalArgumentException expected) {
            foreignRejected = true;
        }
        if (!foreignRejected || memory.cursor != beforeCursor || memory.portCount != beforePorts
                || foreign.cursor != 0 || foreign.portCount != 0) throw new AssertionError("Foreign Memory rejection effects");
        boolean siteRejected = false;
        try {
            bound.insertC3a5f0(memory, 0xC39EC1L, input.map(), input.output(), input.hash(), input.descriptor());
        } catch (IllegalArgumentException expected) {
            siteRejected = true;
        }
        if (!siteRejected || memory.cursor != beforeCursor || memory.portCount != beforePorts
                || foreign.cursor != 0 || foreign.portCount != 0) throw new AssertionError("Wrong site rejection effects");
        System.out.println("194 groups=4 frameEvents=" + memory.cursor + " framePorts=" + memory.portCount
                + " delegateEvents=" + fallback.cursor + " delegatePorts=" + fallback.portCount);
    }

    private static Scene delegatesScene() {
        return new Scene("eight_exact_delegates",
            new Input(0x55000000L, 0x11001000L, 0x33003000L, 0x80000000, 0x44004000L, new Scratch(0L)),
            List.of(),
            List.of(
                port(Kind.EQUAL, 0xC3B9CAL, List.of(0x8123456700006000L, 0x9234567800007000L), 0x12340001L,
                    List.of(c(0x60006000L, 8, 0xFEDCBA9876543210L, 0))),
                port(Kind.INSERT_SLOT, 0xC3BAB8L, List.of(0x22002000L, 254L, -2147483647L, 0x44004000L), 0, List.of()),
                port(Kind.REHASH, 0xC3BBADL, List.of(0x11001000L), 0, List.of()),
                port(Kind.DESTROY, 0xC3BBCAL, List.of(0x44004000L), 0, List.of()),
                port(Kind.CAPACITY, 0xC3BC2FL, List.of(-2147483646L, -1L), -2147483645L, List.of()),
                port(Kind.RESERVE, 0xC3BC3EL, List.of(0x11001000L, -3L), 0, List.of()),
                port(Kind.OVERFLOW, 0xC3BC83L, List.of(0x33003000L, 0x11001000L), 0, List.of()),
                port(Kind.TERMINAL, 0xC3BC88L, List.of(), 0, List.of(c(0x60006008L, 1, 0xABL, 0)))),
            0L,
            List.of(c(0x60006000L, 8, 0xFEDCBA9876543210L, 0), c(0x60006008L, 1, 0xABL, 0)));
    }
private static Scene frameScene() {
    long moduleBase = 0x55000000L;
    long map = 0x11001000L;
    long data = 0x22002000L;
    long result = 0x33003000L;
    long descriptor = 0x44004000L;
    int hash = 0x80000000;
    long wrapperBody = result - 0x70L;
    long firstChildBody = wrapperBody - 0xB0L;
    long firstChildRbp = firstChildBody + 0x70L;
    long fifthFlagAddr = firstChildBody + 0xC0L;
    long fifthPtrAddr = firstChildBody + 0x20L;

    List<Cell> initial = List.of(
        c(map + 0x14L, 4, 3L, 0L),
        c(map + 8L, 8, data, 0L),
        c(data + 4L, 1, 0L, 0L),
        c(map + 0x18L, 1, 0L, 0L),
        c(map + 0x10L, 4, 0L, 0L),
        c(map + 0x1CL, 4, 0x3F800000L, 0L),
        c(descriptor, 16, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L),
        c(descriptor + 0x10L, 16, 0x100000013L, 0x200000022L)
    );

    List<Step> steps = List.of(
        mem(Kind.R32, map + 0x14L, 3L, 0L),
        mem(Kind.R64, map + 8L, data, 0L),
        mem(Kind.R8, data + 4L, 0L, 0L),
        mem(Kind.R8, map + 0x18L, 0L, 0L),
        port(Kind.CAPACITY, 0xC3BC2FL, List.of(4L, 1L), 1L, List.of()),
        port(Kind.RESERVE, 0xC3BC3EL, List.of(map, 1L), 0L, List.of(c(map + 0x18L, 1, 2L, 0L))),
        mem(Kind.W8, fifthFlagAddr, 0L, 0L),
        mem(Kind.W64, fifthPtrAddr, fifthFlagAddr, 0L),
        mem(Kind.R32, map + 0x14L, 3L, 0L),
        mem(Kind.R64, map + 8L, data, 0L),
        mem(Kind.R8, data + 4L, 0L, 0L),
        mem(Kind.R8, map + 0x18L, 2L, 0L),
        mem(Kind.R32, map + 0x10L, 0L, 0L),
        mem(Kind.R32, map + 0x1CL, 0x3F800000L, 0L),
        mem(Kind.R8, data + 4L, 0L, 0L),
        mem(Kind.W32, data, 0x80000000L, 0L),
        mem(Kind.W8, data + 4L, 1L, 0L),
        mem(Kind.W64, data + 8L, 0L, 0L),
        mem(Kind.W64, data + 0x18L, 0L, 0L),
        mem(Kind.W64, data + 0x20L, 0L, 0L),
        mem(Kind.R128, descriptor, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L),
        mem(Kind.W128, data + 8L, 0x0123456789ABCDEFL, 0xFEDCBA9876543210L),
        mem(Kind.R128, descriptor + 0x10L, 0x100000013L, 0x200000022L),
        mem(Kind.W128, data + 0x18L, 0x100000013L, 0x200000022L),
        mem(Kind.W64, descriptor + 0x10L, 0L, 0L),
        mem(Kind.W64, descriptor + 0x18L, 0x0FL, 0L),
        mem(Kind.W8, descriptor, 0L, 0L),
        mem(Kind.R32, map + 0x10L, 0L, 0L),
        mem(Kind.W32, map + 0x10L, 1L, 0L),
        mem(Kind.W64, result, data, 0L),
        mem(Kind.W8, result + 8L, 1L, 0L)
    );

    List<Cell> finalCells = List.of(
        c(result, 8, data, 0L),
        c(result + 8L, 1, 1L, 0L),
        c(map + 0x10L, 4, 1L, 0L),
        c(fifthFlagAddr, 1, 0L, 0L),
        c(fifthPtrAddr, 8, fifthFlagAddr, 0L),
        c(descriptor, 1, 0L, 0L),
        c(descriptor + 0x10L, 8, 0L, 0L),
        c(descriptor + 0x18L, 8, 0x0FL, 0L)
    );

    Input input = new Input(moduleBase, map, result, hash, descriptor, new Scratch(firstChildBody));
    return new Scene("frame", input, initial, steps, result, finalCells);
}

    private static Cell c(long a,int w,long l,long h) { return new Cell(a,w,l,h); }
    private static Step mem(Kind k,long a,long l,long h) { return new Step(k,a,l,h,List.of(),0,List.of()); }
    private static Step port(Kind k,long a,List<Long> args,long r,List<Cell> effects) { return new Step(k,a,0,0,args,r,effects); }
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
