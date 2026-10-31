package org.xar.ck3.research.m3.hash188;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Input;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Memory;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Ports;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Bytes16;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Cell;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Kind;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Step;
import org.xar.ck3.research.m3.hash188.HashInsertWitness188Api.Scene;

import org.xar.ck3.research.m3.PostRegistrationApi178;

public final class HashInsertCallerBindingWitness188 {
    private HashInsertCallerBindingWitness188() { }
    public static void main(String[] args) { run(); }
    private static void run() {
        Scene scene = HashInsertWitnessBook188.scenes().get(0);
        Input in = scene.input();
        Script script = new Script(scene);
        for (Cell cell : scene.initial()) {
            script.seed(cell);
        }
        long sentinel = 0xF123456789ABCDEFL;
        OpaqueProbe opaque = new OpaqueProbe(script, sentinel);
        PostRegistrationApi178.Ports bound = PostRegistrationHashInsertBinding188.bind(
            script,
            in.moduleBase(),
            new PostRegistrationApi178.CallerOwnedScratch(in.scratch().bodyRsp() + 0xB0L),
            script,
            opaque
        );

        // Witness A: Real callee execution via binding
        if (scene.steps().size() != 10) throw new AssertionError("Expected 10 steps");
        bound.callc39c60(script, in.map(), in.output(), in.hash(), in.descriptor());
        if (script.cursor != 10) throw new AssertionError("Script cursor not exhausted");
        if (script.portCount != 1) throw new AssertionError("Hash port count mismatch");
        if (opaque.c39Calls != 0) throw new AssertionError("Opaque C39 called unexpectedly");
        if (opaque.otherCalls != 0) throw new AssertionError("Opaque other called unexpectedly");
        for (Cell cell : scene.finalCells()) {
            script.verifyFinal(cell);
        }

        // Witness B: Opaque forwarding
        long gsResult = bound.gs58(script);
        if (gsResult != sentinel) throw new AssertionError("GS58 sentinel mismatch");
        if (opaque.gsCalls != 1) throw new AssertionError("GS58 call count mismatch");
        if (opaque.c39Calls != 0 || opaque.otherCalls != 0) throw new AssertionError("Opaque counters changed unexpectedly");
        if (script.cursor != 10) throw new AssertionError("Script cursor changed after GS58");
        if (script.portCount != 1) throw new AssertionError("Script port count changed after GS58");

        // Witness C: Foreign memory rejection
        Script foreign = new Script(scene);
        boolean threw = false;
        try {
            bound.callc39c60(foreign, in.map(), in.output(), in.hash(), in.descriptor());
        } catch (IllegalArgumentException e) {
            threw = true;
        }
        if (!threw) throw new AssertionError("Foreign memory did not throw IllegalArgumentException");
        if (script.cursor != 10) throw new AssertionError("Captured script cursor changed after foreign call");
        if (script.portCount != 1) throw new AssertionError("Captured script port count changed after foreign call");
        if (foreign.cursor != 0) throw new AssertionError("Foreign script cursor advanced");
        if (foreign.portCount != 0) throw new AssertionError("Foreign script port count advanced");
        if (opaque.c39Calls != 0 || opaque.otherCalls != 0 || opaque.gsCalls != 1) throw new AssertionError("Opaque counters changed after foreign call");

        System.out.println("Witness A: Consumed 10 steps, 1 hash port, 0 opaque C39/other.");
        System.out.println("Witness B: GS58 forwarded, 1 opaque GS call.");
        System.out.println("Witness C: Foreign memory rejected with IllegalArgumentException.");
    }

    private static final class Script implements PostRegistrationHashInsertBinding188.Memory, Ports {
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
        public void copy855f00(Memory memory, long siteRva, long rcx, long rdx) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.COPY, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 2) throw new AssertionError("COPY args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx) throw new AssertionError("COPY args mismatch");
            portCount++;
            for (Cell cell : step.effects()) {
                applyEffect(cell);
            }
        }

        @Override
        public void assign855db0(Memory memory, long siteRva, long rcx, long rdx, long r8) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            Step step = nextStep(Kind.ASSIGN, siteRva);
            List<Long> args = step.arguments();
            if (args.size() != 3) throw new AssertionError("ASSIGN args size mismatch");
            if (args.get(0) != rcx || args.get(1) != rdx || args.get(2) != r8) throw new AssertionError("ASSIGN args mismatch");
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
        public void insertC3b960(Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
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
    private static final class OpaqueProbe implements PostRegistrationApi178.Ports {
        private final PostRegistrationHashInsertBinding188.Memory expectedMemory;
        private final long sentinel;
        private int gsCalls;
        private int c39Calls;
        private int otherCalls;
        OpaqueProbe(PostRegistrationHashInsertBinding188.Memory expectedMemory, long sentinel) {
            this.expectedMemory = expectedMemory;
            this.sentinel = sentinel;
        }
        @Override
        public int call3f542c0(PostRegistrationApi178.Memory memory, long receiver, long descriptor) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3f542c0");
        }
        @Override
        public long callc3e150(PostRegistrationApi178.Memory memory) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque callc3e150");
        }
        @Override
        public int call86e160(PostRegistrationApi178.Memory memory, int requested, int zeroEdx) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call86e160");
        }
        @Override
        public void callc3b700(PostRegistrationApi178.Memory memory, long header, int exponent) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque callc3b700");
        }
        @Override
        public void call3763f90(PostRegistrationApi178.Memory memory, long receiver, long outputVector) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3763f90");
        }
        @Override
        public long objectSlot80(PostRegistrationApi178.Memory memory, long code, long receiver) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque objectSlot80");
        }
        @Override
        public int call3f7e220(PostRegistrationApi178.Memory memory, long dataRdx, int lengthR8d) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3f7e220");
        }
        @Override
        public void callc39c60(PostRegistrationApi178.Memory memory, long header, long output, int hash, long descriptor) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            c39Calls++;
            throw new AssertionError("C39 edge must execute real callee, not opaque");
        }
        @Override
        public long calla92eb0(PostRegistrationApi178.Memory memory) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque calla92eb0");
        }
        @Override
        public long call3793900(PostRegistrationApi178.Memory memory, long context, int hash) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3793900");
        }
        @Override
        public int call3f6d2b0Al(PostRegistrationApi178.Memory memory, long descriptor, long data) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3f6d2b0Al");
        }
        @Override
        public void call857a70(PostRegistrationApi178.Memory memory, long output, long format, long operands) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call857a70");
        }
        @Override
        public long gs58(PostRegistrationApi178.Memory memory) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            gsCalls++;
            return sentinel;
        }
        @Override
        public long call3f5f970(PostRegistrationApi178.Memory memory, int flag) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call3f5f970");
        }
        @Override
        public void call857b60(PostRegistrationApi178.Memory memory, long logger, long descriptor, int line, int level, long sourceRsp) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call857b60");
        }
        @Override
        public int atomicXadd32(PostRegistrationApi178.Memory memory, long address, int delta) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque atomicXadd32");
        }
        @Override
        public void call4223f44(PostRegistrationApi178.Memory memory, long base, long bytes) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call4223f44");
        }
        @Override
        public void call4232a70(PostRegistrationApi178.Memory memory) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call4232a70");
        }
        @Override
        public void objectSlot00(PostRegistrationApi178.Memory memory, long code, long receiver, int flag) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque objectSlot00");
        }
        @Override
        public void allocatorSlot10(PostRegistrationApi178.Memory memory, long code, long receiver, long rows, int alignment) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque allocatorSlot10");
        }
        @Override
        public void call4223a84(PostRegistrationApi178.Memory memory, long guard) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call4223a84");
        }
        @Override
        public void call4223a24(PostRegistrationApi178.Memory memory, long guard) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call4223a24");
        }
        @Override
        public void call856050(PostRegistrationApi178.Memory memory, long field) {
            if (memory != expectedMemory) throw new AssertionError("Opaque Memory identity");
            otherCalls++;
            throw new AssertionError("Unexpected opaque call856050");
        }
    }
}
