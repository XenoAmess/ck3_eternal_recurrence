package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotArrayReserve1ACE4B0.Memory;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotArrayReserve1ACE4B0.Calls;
import static org.xar.ck3.control.g2.m2.nativecode.SlotArrayReserveFixture244.*;
public final class SlotArrayReserveWitness244 {
    private static final List<Scene> scenes = SlotArrayReserveCases244.scenes();
    public static int verify() {
        int count = 0;
        for (Scene s : scenes) {
            Cursor c = new Cursor(s.steps());
            Memory m = new MemoryImpl(c);
            Calls k = new CallsImpl(c, m);
            PendingSlotArrayReserve1ACE4B0.reserve(m, k, s.table(), s.requested());
            if (c.index != s.steps().size()) throw new AssertionError("steps not exhausted");
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
        public long allocate(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.kind() != Kind.ALLOC) throw new AssertionError("expected ALLOC");
            if (s.address() != target) throw new AssertionError("target mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != Integer.toUnsignedLong(r8d)) throw new AssertionError("r8d mismatch");
            return s.value();
        }
        public void release(Memory memory, long target, long rcx, long rdx, int r8d) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.kind() != Kind.RELEASE) throw new AssertionError("expected RELEASE");
            if (s.address() != target) throw new AssertionError("target mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != Integer.toUnsignedLong(r8d)) throw new AssertionError("r8d mismatch");
        }
        public void call4226860(Memory memory, long rcx, long rdx, long r8) {
            if (memory != expectedMemory) throw new AssertionError("Memory identity mismatch");
            Step s = c.next();
            if (s.kind() != Kind.COPY) throw new AssertionError("expected COPY");
            if (s.address() != 0) throw new AssertionError("address mismatch");
            if (s.value() != 0) throw new AssertionError("value mismatch");
            if (s.a() != rcx) throw new AssertionError("rcx mismatch");
            if (s.b() != rdx) throw new AssertionError("rdx mismatch");
            if (s.c() != r8) throw new AssertionError("r8 mismatch");
        }
    }
}