package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
/**
 * Source-bound 605-byte component using supplied storage and opaque helper projections.
 * Floating arithmetic uses Java 21 round-to-nearest semantics; native MXCSR modes,
 * traps, DAZ and FTZ are outside this software projection. No process binding.
 */
public final class SparseIntCells177 {
 private SparseIntCells177() { }
 public record Raw128(long low,long high) { }
 public enum FrameAddress { LOCAL_OUTPUT_RBP_MINUS10, LOCAL_PAIR_RBP_MINUS1C }
 /** Known caller fields only; unknown stack arguments and complete native ABI are not supplied. */
 public record Known1783480(long rcx,long rdx,int r8d,long r9,long stack28) { }
 /** Only known caller registers and initialized localpair DWORDs, not a native function signature. */
 public record Known17836d0(long rcx,FrameAddress rdx,int r8d,FrameAddress r9,int localPairKey,int localPairValue) { }
 public interface Memory extends NativeTaskMemory {
  int readUnsignedByte(long address);
  void writeByte(long address,byte value);
  /** One non-LOCK INC m32 effect, modulo32; no atomicity guarantee. */
  void incrementInt32(long address);
  /** Source MOVUPS16B store of full captured bits; no zeroing padding or atomicity guarantee. */
  void writeRaw128(long address,Raw128 bits);
 }
 public interface Ports {
  void call177fbd0(long rcx);
  void call1783480(Known1783480 known);
  Raw128 call17836d0(Known17836d0 known);
 }
 public static long put(long table, long output, int rawHash, long keyAddress,
                       long valueAddress, Memory memory, Ports ports) {
    final int mask = memory.readInt32(table + 0x14L);
    final long index = ((long) mask) & ((long) rawHash);
    long cell = memory.readPointer(table + 8L) + index * 12L;
    int distance = 1;

    // 177ED51..177ED70: only this lookup captures the input key once.
    if (memory.readUnsignedByte(cell) >= distance) {
        final int wantedKey = memory.readInt32(keyAddress);
        while (true) {
            if (wantedKey == memory.readInt32(cell + 4L)) {
                final int newValue = memory.readInt32(valueAddress);
                memory.writeInt32(cell + 8L, newValue);
                memory.writeInt64(output, cell);
                memory.writeByte(output + 8L, (byte) 0);
                return output;
            }
            cell += 12L;
            distance = (distance + 1) & 0xFF;
            if (distance > memory.readUnsignedByte(cell)) break;
        }
    }

    if (distance > memory.readUnsignedByte(table + 0x18L)) {
        ports.call177fbd0(table);
        ports.call1783480(new Known1783480(table, output, rawHash,
                keyAddress, valueAddress));
        return output;
    }
    final int nextCount = memory.readInt32(table + 0x10L) + 1;
    final float ratio = ((float) nextCount) / ((float) mask);
    final float threshold = Float.intBitsToFloat(memory.readInt32(table + 0x1CL));
    if (ratio > threshold) {
        ports.call177fbd0(table);
        ports.call1783480(new Known1783480(table, output, rawHash,
                keyAddress, valueAddress));
        return output;
    }

    final int marker = memory.readUnsignedByte(cell);
    if (marker == 0) {
        memory.writeByte(cell, (byte) distance);
        final int newKey = memory.readInt32(keyAddress);
        memory.writeInt32(cell + 4L, newKey);
        final int newValue = memory.readInt32(valueAddress);
        memory.writeInt32(cell + 8L, newValue);
        memory.incrementInt32(table + 0x10L);
        memory.writeInt64(output, cell);
        memory.writeByte(output + 8L, (byte) 1);
        return output;
    }

    int carryDistance = (marker + 1) & 0xFF;
    if (memory.readUnsignedByte(cell + 12L) == 0) {
        memory.writeByte(cell + 12L, (byte) carryDistance);
        final int movedKey = memory.readInt32(cell + 4L);
        memory.writeInt32(cell + 16L, movedKey);
        final int movedValue = memory.readInt32(cell + 8L);
        memory.writeInt32(cell + 20L, movedValue);
        memory.writeByte(cell, (byte) distance);
        final int newValue = memory.readInt32(valueAddress);
        final int newKey = memory.readInt32(keyAddress);
        memory.writeInt32(cell + 4L, newKey);
        memory.writeInt32(cell + 8L, newValue);
        memory.incrementInt32(table + 0x10L);
        memory.writeInt64(output, cell);
        memory.writeByte(output + 8L, (byte) 1);
        return output;
    }

    // 177EE1E..177EE46: RDX retains this insertion slot through the carry loop.
    final long originalSlot = cell;
    int carryKey = memory.readInt32(cell + 4L);
    int carryValue = memory.readInt32(cell + 8L);
    memory.writeByte(cell, (byte) distance);
    final int newValue = memory.readInt32(valueAddress);
    final int newKey = memory.readInt32(keyAddress);
    memory.writeInt32(cell + 4L, newKey);
    memory.writeInt32(cell + 8L, newValue);

    while (true) {
        final int nextMarker = memory.readUnsignedByte(cell + 12L);
        cell += 12L;
        if (nextMarker == 0) {
            memory.writeByte(cell, (byte) carryDistance);
            memory.writeInt32(cell + 4L, carryKey);
            memory.writeInt32(cell + 8L, carryValue);
            memory.incrementInt32(table + 0x10L);
            memory.writeInt64(output, originalSlot);
            memory.writeByte(output + 8L, (byte) 1);
            return output;
        }

        if (nextMarker < carryDistance) {
            memory.writeByte(cell, (byte) carryDistance);
            final int previousKey = carryKey;
            carryKey = memory.readInt32(cell + 4L);
            memory.writeInt32(cell + 4L, previousKey);
            final int previousValue = carryValue;
            carryValue = memory.readInt32(cell + 8L);
            memory.writeInt32(cell + 8L, previousValue);
            carryDistance = (nextMarker + 1) & 0xFF;
            continue;
        }

        carryDistance = (carryDistance + 1) & 0xFF;
        if (carryDistance <= memory.readUnsignedByte(table + 0x18L)) continue;

        // 177EE9C is an observable read even though its saved byte is later dead.
        memory.readUnsignedByte(originalSlot);
        memory.writeByte(originalSlot, (byte) carryDistance);
        final int previousKey = carryKey;
        carryKey = memory.readInt32(originalSlot + 4L);
        memory.writeInt32(originalSlot + 4L, previousKey);
        final int previousValue = carryValue;
        carryValue = memory.readInt32(originalSlot + 8L);
        memory.writeInt32(originalSlot + 8L, previousValue);
        ports.call177fbd0(table);
        final int pairHash = Idler28eed20.prepare(0L, 0, carryKey).r8d();
        final Raw128 returnedRaw128 = ports.call17836d0(new Known17836d0(
                table, FrameAddress.LOCAL_OUTPUT_RBP_MINUS10, pairHash,
                FrameAddress.LOCAL_PAIR_RBP_MINUS1C, carryKey, carryValue));
        memory.writeRaw128(output, returnedRaw128);
        return output;
    }
}
}
