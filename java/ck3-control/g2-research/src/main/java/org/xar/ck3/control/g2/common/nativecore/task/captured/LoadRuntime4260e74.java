package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Only the held normal 358B projection with explicitly supplied opaque callbacks. */
public final class LoadRuntime4260e74 {
    private LoadRuntime4260e74() { }

    /** Known volatile inputs, with only the two actually stored stack arguments. */
    public record SearchCall(long rcx, long rdx, long r8, long r9, long liveRax,
            OptionalLong stack20, OptionalLong stack28) { }

    /** Source scratch has no supplied initial bits; no made-up native stack address. */
    public static final class LocalSlot64 {
        private OptionalLong value = OptionalLong.empty();
        public OptionalLong value() { return value; }
        public void store(long bits) { value = OptionalLong.of(bits); }
    }

    public interface Ports {
        long call43da2d0(long rcx, LocalSlot64 outSlot, long knownR8, long knownR9, long liveRax);
        long call4260af0(SearchCall call);
        long call4260968(SearchCall call);
        long call4260c28(SearchCall call);
    }

    /** Java unsupported-source boundary; it does not perform the native cold EH calls. */
    public static final class SourceBoundary extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final int failureModeBits;
        private final long completeObjectBits;
        public SourceBoundary(int failureModeBits, long completeObjectBits) {
            super("Unexecuted source failure branch 4260FB6 -> 4260E5C / 4226790; terminal4260FD9");
            this.failureModeBits = failureModeBits;
            this.completeObjectBits = completeObjectBits;
        }
        public int failureModeBits() { return failureModeBits; }
        public long completeObjectBits() { return completeObjectBits; }
        public long sourceTargetRva() { return 0x4260FB6L; }
        public long terminalRva() { return 0x4260FD9L; }
    }

    public static long execute(long moduleBase, long objectBits, int adjustmentBits,
            long sourceToken, long targetToken, int failureModeBits,
            NativeTaskMemory memory, Ports ports) {
        if (objectBits == 0L) { return 0L; }
        long vptr = memory.readPointer(objectBits);
        long col = memory.readPointer(vptr - 8L);
        long complete = objectBits - Integer.toUnsignedLong(memory.readInt32(col + 0x4L));
        int displacementBits = memory.readInt32(col + 0x8L);
        long displacement = Integer.toUnsignedLong(displacementBits);
        int masked = (displacementBits == 0 ? 0 : -1)
                & memory.readInt32(objectBits - displacement);
        complete -= (long) masked;
        long relativeBase;
        if (memory.readInt32(col) == 0) {
            LocalSlot64 slot = new LocalSlot64();
            relativeBase = ports.call43da2d0(col, slot, sourceToken, targetToken,
                    Integer.toUnsignedLong(masked));
            slot.store(relativeBase);
        } else {
            relativeBase = col - (long) memory.readInt32(col + 0x14L);
        }
        long descriptorOffset = (long) memory.readInt32(col + 0x10L);
        int flags = memory.readInt32(relativeBase + descriptorOffset + 0x4L);
        long result;
        if ((flags & 1) == 0) {
            result = ports.call4260af0(new SearchCall(col, sourceToken, targetToken,
                    relativeBase, descriptorOffset, OptionalLong.empty(), OptionalLong.empty()));
        } else {
            SearchCall call = new SearchCall(complete, col, sourceToken,
                    objectBits - (long) adjustmentBits - complete, descriptorOffset,
                    OptionalLong.of(targetToken), OptionalLong.of(relativeBase));
            result = (flags & 2) == 0 ? ports.call4260968(call) : ports.call4260c28(call);
        }
        if (result == 0L) {
            if (failureModeBits == 0) { return 0L; }
            throw new SourceBoundary(failureModeBits, complete);
        }
        return LoadResultAdjustment4260f6b.adjust(complete, result, memory);
    }
}
