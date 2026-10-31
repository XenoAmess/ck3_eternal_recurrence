package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotWithGrowthAndCopies2A32770.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotWithGrowthAndCopies2A32770.Calls;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotProducer2A32770.Input;
import static org.xar.ck3.control.g2.m2.nativecode.SlotProducerGrowthFixture253.*;

public final class SlotProducerGrowthWitness253 {
    private static final List<Scene> scenes = SlotProducerGrowthCases253.scenes();

    public static int verify() {
        int count = 0;
        for (Scene s : scenes) {
            Cursor c = new Cursor(s.steps());
            Memory m = new MemoryImpl(c);
            Calls k = new CallsImpl(c, m);
            long ret = PendingSlotWithGrowthAndCopies2A32770.produce(m, k, s.input());
            if (ret != s.expectedReturn()) throw new AssertionError("Return mismatch");
            if (c.index != s.steps().size()) throw new AssertionError("Steps not exhausted");
            count++;
        }
        return count;
    }

    public static void main(String[] args) { System.out.println(verify()); }

    private static final class Cursor {
        int index = 0;
        List<Step> steps;
        Cursor(List<Step> steps) { this.steps = steps; }
        Step next() {
            if (index >= steps.size()) throw new AssertionError("no more steps");
            return steps.get(index++);
        }
    }

    private static final class MemoryImpl implements Memory {
        Cursor c;
        MemoryImpl(Cursor c) { this.c = c; }
        public int read8(long address) {
            Step s = c.next();
            if (s.kind() != Kind.R8) throw new AssertionError("expected R8");
            if (s.address() != address) throw new AssertionError("address mismatch");
            return (int) s.value();
        }
        public int read32(long address) {
            Step s = c.next();
            if (s.kind() != Kind.R32) throw new AssertionError("expected R32");
            if (s.address() != address) throw new AssertionError("address mismatch");
            return (int) s.value();
        }
        public long read64(long address) {
            Step s = c.next();
            if (s.kind() != Kind.R64) throw new AssertionError("expected R64");
            if (s.address() != address) throw new AssertionError("address mismatch");
            return s.value();
        }
        public void write16(long address, int value) {
            throw new AssertionError("Unexpected write16 after PAGEfalse");
        }
        public PendingContextCopy3076B60.Bits128 read128(long address) {
            throw new AssertionError("Unexpected read128 after PAGEfalse");
        }
        public void write128(long address, PendingContextCopy3076B60.Bits128 value) {
            throw new AssertionError("Unexpected write128 after PAGEfalse");
        }
        public void write8(long address, int value) {
            Step s = c.next();
            if (s.kind() != Kind.W8) throw new AssertionError("expected W8");
            if (s.address() != address) throw new AssertionError("address mismatch");
            if ((int) s.value() != value) throw new AssertionError("value mismatch");
        }
        public void write32(long address, int value) {
            Step s = c.next();
            if (s.kind() != Kind.W32) throw new AssertionError("expected W32");
            if (s.address() != address) throw new AssertionError("address mismatch");
            if ((int) s.value() != value) throw new AssertionError("value mismatch");
        }
        public void write64(long address, long value) {
            Step s = c.next();
            if (s.kind() != Kind.W64) throw new AssertionError("expected W64");
            if (s.address() != address) throw new AssertionError("address mismatch");
            if (s.value() != value) throw new AssertionError("value mismatch");
        }
    }

    private static final class CallsImpl implements Calls {
        Cursor c;
        final Memory expectedMemory;
        CallsImpl(Cursor c, Memory expectedMemory) { this.c = c; this.expectedMemory = expectedMemory; }

        private void checkMemory(Object memory) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
        }

        public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            checkMemory(memory);
            Step s = c.next();
            if (s.kind() != Kind.ALLOC) throw new AssertionError("expected ALLOC");
            if (s.address() != target) throw new AssertionError("target mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != Integer.toUnsignedLong(r8d)) throw new AssertionError("r8d mismatch");
            return s.value();
        }

        public void release(Memory memory, long target, long rcx, long rdx, int r8d) {
            checkMemory(memory);
            Step s = c.next();
            if (s.kind() != Kind.RELEASE) throw new AssertionError("expected RELEASE");
            if (s.address() != target) throw new AssertionError("target mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != Integer.toUnsignedLong(r8d)) throw new AssertionError("r8d mismatch");
        }

        public void call4226860(Memory memory, long rcx, long rdx, long r8) {
            checkMemory(memory);
            Step s = c.next();
            if (s.kind() != Kind.COPY) throw new AssertionError("expected COPY");
            if (s.address() != 0) throw new AssertionError("address mismatch");
            if (s.value() != 0) throw new AssertionError("value mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != r8) throw new AssertionError("r8 mismatch");
        }

        public void call4226F10(Memory memory, long rcx, int edx, long r8) {
            checkMemory(memory);
            Step s = c.next();
            if (s.kind() != Kind.SET) throw new AssertionError("expected SET");
            if (s.address() != 0) throw new AssertionError("address mismatch");
            if (s.value() != 0) throw new AssertionError("value mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != Integer.toUnsignedLong(edx)) throw new AssertionError("edx mismatch");
            if (s.c() != r8) throw new AssertionError("r8 mismatch");
        }

        public boolean call2A321F0(PendingSlotProducer2A32770.Memory memory, long rcx, int edx) {
            checkMemory(memory);
            Step s = c.next();
            if (s.kind() != Kind.PAGE) throw new AssertionError("expected PAGE");
            if (s.address() != 0) throw new AssertionError("address mismatch");
            if (s.value() != 0 && s.value() != 1) throw new AssertionError("value mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != Integer.toUnsignedLong(edx)) throw new AssertionError("edx mismatch");
            if (s.c() != 0) throw new AssertionError("c mismatch");
            return s.value() != 0;
        }

        public void call105D2D0(PendingContextCopy3076B60.Memory memory, long rcx) {
            throw new AssertionError("Unexpected call105D2D0");
        }

        public void callBCB7C0(PendingContextCopy3076B60.Memory memory, long rcx, int edx, long r8, long r9) {
            throw new AssertionError("Unexpected callBCB7C0");
        }

        public void call2503880(PendingContextCopy3076B60.Memory memory, long rcx, long rdx) {
            throw new AssertionError("Unexpected call2503880");
        }

        public void call8895D0(PendingEmbeddedCopy373ACF0.Memory memory, long rcx, long rdx) {
            throw new AssertionError("Unexpected call8895D0");
        }

        public void call37282B0(PendingEmbeddedCopy373ACF0.Memory memory, long rcx, long rdx) {
            throw new AssertionError("Unexpected call37282B0");
        }

        public void call260E040(PendingEmbeddedCopy373ACF0.Memory memory, long rcx, long rdx) {
            throw new AssertionError("Unexpected call260E040");
        }

        public void call3727180(PendingEmbeddedCopy373ACF0.Memory memory, long rcx, long rdx) {
            throw new AssertionError("Unexpected call3727180");
        }
    }
}