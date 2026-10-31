package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost;

public final class Request140TestMemory implements RequestE92780.Memory {

    public enum Op {
        READ8, READ32, READ64, READ128,
        WRITE8, WRITE16, WRITE32, WRITE64, WRITE128
    }

    public record Access(Op op, long address, int width, long low, long high) {}

    private final Idler79eRegressionHost.Memory backing;
    private final List<Access> traceList = new ArrayList<>();

    public Request140TestMemory() {
        this.backing = new Idler79eRegressionHost.Memory();
    }

    public Idler79eRegressionHost.Memory bytes() {
        return backing;
    }

    public List<Access> trace() {
        return Collections.unmodifiableList(new ArrayList<>(traceList));
    }

    public void clearTrace() {
        traceList.clear();
    }

    private void record(Op op, long address, int width, long low, long high) {
        traceList.add(new Access(op, address, width, low, high));
    }

    private void validateAddressable(long address, int width) {
        for (int i = 0; i < width; i++) {
            backing.peekUnsignedByte(address + i);
        }
    }

    @Override
    public int readUnsignedByte(long address) {
        int val = backing.readUnsignedByte(address);
        record(Op.READ8, address, 1, (long) val, 0L);
        return val;
    }

    @Override
    public void writeByte(long address, byte value) {
        backing.writeByte(address, value);
        record(Op.WRITE8, address, 1, (long) (value & 0xFF), 0L);
    }

    @Override
    public void writeInt16(long address, short value) {
        validateAddressable(address, 2);
        backing.seedByte(address, (value & 0xFF));
        backing.seedByte(address + 1, ((value >>> 8) & 0xFF));
        record(Op.WRITE16, address, 2, (long) (value & 0xFFFF), 0L);
    }

    @Override
    public RequestE92780.Raw128 readRaw128(long address) {
        validateAddressable(address, 16);

        long low = 0L;
        long high = 0L;

        for (int i = 0; i < 8; i++) {
            int b = backing.peekUnsignedByte(address + i);
            low |= ((long) b) << (i * 8);
        }

        for (int i = 0; i < 8; i++) {
            int b = backing.peekUnsignedByte(address + 8 + i);
            high |= ((long) b) << (i * 8);
        }

        record(Op.READ128, address, 16, low, high);
        return new RequestE92780.Raw128(low, high);
    }

    @Override
    public void writeRaw128(long address, RequestE92780.Raw128 value) {
        validateAddressable(address, 16);

        long low = value.low();
        long high = value.high();

        for (int i = 0; i < 8; i++) {
            byte b = (byte) (low >>> (i * 8));
            backing.seedByte(address + i, (b & 0xFF));
        }

        for (int i = 0; i < 8; i++) {
            byte b = (byte) (high >>> (i * 8));
            backing.seedByte(address + 8 + i, (b & 0xFF));
        }

        record(Op.WRITE128, address, 16, low, high);
    }

    @Override
    public long readPointer(long address) {
        long val = backing.readPointer(address);
        record(Op.READ64, address, 8, val, 0L);
        return val;
    }

    @Override
    public int readInt32(long address) {
        int val = backing.readInt32(address);
        record(Op.READ32, address, 4, Integer.toUnsignedLong(val), 0L);
        return val;
    }

    @Override
    public void writeInt32(long address, int value) {
        backing.writeInt32(address, value);
        record(Op.WRITE32, address, 4, Integer.toUnsignedLong(value), 0L);
    }

    @Override
    public void writeInt64(long address, long value) {
        backing.writeInt64(address, value);
        record(Op.WRITE64, address, 8, value, 0L);
    }
}