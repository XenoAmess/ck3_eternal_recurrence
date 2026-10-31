package org.xar.ck3.control.g2.common.nativecore.task.captured;
/** Supplied-memory projection with Java fixed float/RNE semantics; no native ABI, MXCSR or private-frame equivalence. */
public final class SparseIntCells1783480 {
 private SparseIntCells1783480() { }
 /** Known supplied-memory call effects only, not complete native ABI or private frame addresses. */
 public interface Ports {
  void call177fbd0(long table);
  /** Source writes local flag BYTE0 at stack20; callee normal body never reads this input. */
  void retry1783480(long table,long output,int rawHash,long keyAddress,long valueAddress);
  /** Source's initialized local pair and local output, full16B output including padding returned as bits. stack20 unknown. */
  SparseIntCells177.Raw128 carry17836d0(long table,int rawHash,int key,int value);
 }
 public static long put(long table, long output, int rawHash, long keyAddress,
                       long valueAddress, SparseIntCells177.Memory memory, Ports ports) {
    final int mask = memory.readInt32(table + 0x14L);
    final long index = ((long) mask) & ((long) rawHash);
    long cell = memory.readPointer(table + 8L) + index * 12L;
    int distance = 1;

    if (memory.readUnsignedByte(cell) >= distance) {
        final int wantedKey = memory.readInt32(keyAddress);
        while (true) {
            if (wantedKey == memory.readInt32(cell + 4L)) {
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
        ports.retry1783480(table, output, rawHash, keyAddress, valueAddress);
        return output;
    }
    final int nextCount = memory.readInt32(table + 0x10L) + 1;
    final float ratio = ((float) nextCount) / ((float) mask);
    final float threshold = Float.intBitsToFloat(memory.readInt32(table + 0x1CL));
    if (ratio > threshold) {
        ports.call177fbd0(table);
        ports.retry1783480(table, output, rawHash, keyAddress, valueAddress);
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
        final SparseIntCells177.Raw128 returnedRaw128 = ports.carry17836d0(table, pairHash, carryKey, carryValue);
        memory.writeRaw128(output, returnedRaw128);
        return output;
    }
}
}
