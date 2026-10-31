package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.study.m6.element150.Element150Inputs;
import org.xar.ck3.study.m6.element150.Element150Candidate;
import org.xar.ck3.study.m6.element172.Element172Inputs;
import org.xar.ck3.study.m6.element172.Element172Candidate;

/** Full322 normal37282B0, known150/172 element bodies reused, four deepM6ports remain explicit. */
public final class PendingEmbeddedElements37282B0 {
    private PendingEmbeddedElements37282B0() { }
    public interface Memory extends Element150Inputs.Memory, Element172Inputs.Memory { }
    public interface Calls {
        void call889780(Memory memory, long rcx, long rdx);
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void callDBDB80(Memory memory, long rcx, long rdx, int r8d, int r9d);
        void virtualDestroy(Memory memory, long target, long rcx, long rdx);
        void copy16_21A5050(Memory memory, long destinationHeader, long sourceHeader);
        void copy4_B2EEE0(Memory memory, long destinationHeader, long sourceHeader);
        void copy16_8C70B0(Memory memory, long destinationHeader, long rdxZero, long begin, long end);
        void copy4_ADD0D0(Memory memory, long destinationHeader, long rdxZero, long begin, long end);
    }

    private static final class Adapter150 implements Element150Inputs.Calls {
        private final Memory mem;
        private final Calls calls;
        Adapter150(Memory mem, Calls calls) { this.mem = mem; this.calls = calls; }
        public void copy16_21a5050(long destinationHeader, long sourceHeader) {
            calls.copy16_21A5050(mem, destinationHeader, sourceHeader);
        }
        public void copy4_b2eee0(long destinationHeader, long sourceHeader) {
            calls.copy4_B2EEE0(mem, destinationHeader, sourceHeader);
        }
    }

    private static final class Adapter172 implements Element172Inputs.Calls {
        private final Memory mem;
        private final Calls calls;
        Adapter172(Memory mem, Calls calls) { this.mem = mem; this.calls = calls; }
        public void copy16_8c70b0(long destinationHeader, long rdxZero, long begin, long end) {
            calls.copy16_8C70B0(mem, destinationHeader, rdxZero, begin, end);
        }
        public void copy4_add0d0(long destinationHeader, long rdxZero, long begin, long end) {
            calls.copy4_ADD0D0(mem, destinationHeader, rdxZero, begin, end);
        }
    }

    public static long copy(Memory memory, Calls calls, long destination, long source, long moduleBase) {
        if (destination == source) return destination;
        Adapter150 element150 = new Adapter150(memory, calls);
        Adapter172 element172 = new Adapter172(memory, calls);
        int sourceCount = memory.read32(source + 0xCL);
        long sourceBuffer = memory.read64(source);
        calls.call889780(memory, destination, source);
        int currentCount = memory.read32(destination + 0xCL);
        if (sourceCount > currentCount) {
            int capacity = memory.read32(destination + 0x8L);
            if (sourceCount > capacity) {
                long allocator = memory.read64(destination + 0x10L);
                long allocatorVtable = memory.read64(allocator);
                long allocateTarget = memory.read64(allocatorVtable + 0x8L);
                long bytes = Integer.toUnsignedLong(sourceCount) * 72L;
                long newBuffer = calls.allocate(memory, allocateTarget, allocator, bytes, 8);
                int oldCount = memory.read32(destination + 0xCL);
                long oldBuffer = memory.read64(destination);
                int remaining = oldCount;
                if (remaining > 0) {
                    long to = newBuffer;
                    long from = oldBuffer;
                    do {
                        Element150Candidate.copy(new Element150Inputs.Input(to, from, moduleBase), memory, element150);
                        to += 72L;
                        remaining--;
                        from += 72L;
                    } while (remaining > 0);
                    oldCount = memory.read32(destination + 0xCL);
                }
                calls.callDBDB80(memory, destination, newBuffer, oldCount, sourceCount);
            }
        } else {
            long buffer = memory.read64(destination);
            long end = buffer + (long) currentCount * 72L;
            long slot = buffer + (long) sourceCount * 72L;
            while (slot != end) {
                long vtable = memory.read64(slot);
                long target = memory.read64(vtable);
                calls.virtualDestroy(memory, target, slot, 0L);
                slot += 72L;
            }
        }
        memory.write32(destination + 0xCL, sourceCount);
        if (sourceCount > 0) {
            long to = memory.read64(destination);
            long from = sourceBuffer;
            int remaining = sourceCount;
            do {
                Element172Candidate.assign(new Element172Inputs.Input(to, from, moduleBase), memory, element172);
                to += 72L;
                remaining--;
                from += 72L;
            } while (remaining > 0);
        }
        return destination;
    }
}
