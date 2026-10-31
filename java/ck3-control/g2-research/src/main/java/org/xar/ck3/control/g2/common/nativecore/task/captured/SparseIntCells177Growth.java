package org.xar.ck3.control.g2.common.nativecore.task.captured;
/**
 * Known growth caller effects using supplied storage and opaque external calls.
 * Symbolic frame addresses are not live native pointers. The error branch is
 * a Java projection, not native INT3/unwind or exception-environment equivalence.
 */
public final class SparseIntCells177Growth {
 private SparseIntCells177Growth() { }
 public sealed interface Plan permits NormalPlan,ReturnPlan,ErrorPlan { }
 public record NormalPlan(int capacity,int maximumDistance) implements Plan { }
 public enum ReturnPlan implements Plan { INSTANCE }
 public enum ErrorPlan implements Plan { INSTANCE }
 public enum FrameAddress { LOCAL_OUTPUT_SP_PLUS30, LOCAL_OBJECT_SP_PLUS50 }
 public record KnownVirtual8(long target,long rcx,long rdx,int r8d,long r9) { }
 public record KnownVirtual16(long target,long rcx,long rdx,int r8d) { }
 public record Known17836d0(long rcx,FrameAddress rdx,int r8d,long r9) { }
 public interface Ports {
  long callVirtual8(KnownVirtual8 known);
  void callVirtual16(KnownVirtual16 known);
  long callB15000();
  void call17836d0(Known17836d0 known);
  void call86f210(FrameAddress rcx,long rdx);
  void call4232cf4();
 }
public static Plan plan(int priorMask) {
    int exponent = 3;
    if (priorMask >= 1) {
        final int highestBit = 31 - Integer.numberOfLeadingZeros(priorMask);
        exponent = Math.max(3, highestBit + 2);
        if (exponent >= 31) return ErrorPlan.INSTANCE;
        if (Integer.compareUnsigned(exponent - 1, 29) > 0) return ReturnPlan.INSTANCE;
    }
    return new NormalPlan(1 << (exponent & 31), (exponent + 2) & 0xFF);
}
public static void applyNormal(long table, NormalPlan plan, SparseIntCells177.Memory memory, Ports ports) {
    final int capacity = plan.capacity();
    final long oldCells = memory.readPointer(table + 8L);
    final int maximumDistance = plan.maximumDistance() & 0xFF;
    final long allocationReceiver = memory.readPointer(table + 0x20L);
    final int newMask = capacity - 1;
    memory.writeByte(table + 0x18L, (byte) maximumDistance);
    memory.writeInt32(table + 0x14L, newMask);

    int remaining = memory.readInt32(table + 0x10L);
    memory.writeInt32(table + 0x10L, 0);
    final long allocationVtable = memory.readPointer(allocationReceiver);
    final long allocationTarget = memory.readPointer(allocationVtable + 8L);
    final int allocationUnits = (maximumDistance + 1) + capacity;
    final long allocationBytes = ((long) allocationUnits) * 12L;
    final long newCells = ports.callVirtual8(new KnownVirtual8(
            allocationTarget, allocationReceiver, allocationBytes, 4, allocationTarget));

    final int freshMaximumDistance = memory.readUnsignedByte(table + 0x18L);
    final long markerUnits = ((long) capacity) + freshMaximumDistance;
    memory.writeInt64(table + 8L, newCells);
    final long markerEnd = newCells + markerUnits * 12L;
    long marker = newCells;
    while (marker != markerEnd) {
        memory.writeByte(marker, (byte) 0);
        marker += 12L;
    }
    memory.writeByte(markerEnd, (byte) 0xFF);

    final long firstB15000 = ports.callB15000();
    if (oldCells != firstB15000 && remaining > 0) {
        long cursor = oldCells + 6L;
        while (remaining > 0) {
            if (memory.readUnsignedByte(cursor - 6L) != 0) {
                final long pairAddress = cursor - 2L;
                int hash = (memory.readUnsignedByte(pairAddress) ^ 0x811C9DC5) * 0x01000193;
                hash = (hash ^ memory.readUnsignedByte(pairAddress + 1L)) * 0x01000193;
                hash = (hash ^ memory.readUnsignedByte(pairAddress + 2L)) * 0x01000193;
                hash = (hash ^ memory.readUnsignedByte(pairAddress + 3L)) * 0x01000193;
                ports.call17836d0(new Known17836d0(
                        table, FrameAddress.LOCAL_OUTPUT_SP_PLUS30, hash, pairAddress));
                remaining--;
            }
            cursor += 12L;
        }
    }

    final long secondB15000 = ports.callB15000();
    if (oldCells != secondB15000) {
        final long releaseReceiver = memory.readPointer(table + 0x20L);
        final long releaseVtable = memory.readPointer(releaseReceiver);
        final long releaseTarget = memory.readPointer(releaseVtable + 0x10L);
        ports.callVirtual16(new KnownVirtual16(releaseTarget, releaseReceiver, oldCells, 4));
    }
}
public static void apply(long table, SparseIntCells177.Memory memory, Ports ports) {
    final Plan selected = plan(memory.readInt32(table + 0x14L));
    if (selected instanceof NormalPlan normal) {
        applyNormal(table, normal, memory, ports);
    } else if (selected == ErrorPlan.INSTANCE) {
        ports.call86f210(FrameAddress.LOCAL_OBJECT_SP_PLUS50, table);
        ports.call4232cf4();
        throw new IllegalStateException("source INT3 at177FD69");
    }
}
}
