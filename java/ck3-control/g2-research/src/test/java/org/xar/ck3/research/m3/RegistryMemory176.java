package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class RegistryMemory176 implements RegistryConsumerApi176.Memory {
    private final Map<Long, Byte> storage;
    private final List<String> trace;

    public RegistryMemory176(Map<Long, Byte> initial) {
        if (initial == null) {
            throw new NullPointerException("initial");
        }
        this.storage = new HashMap<>(initial);
        this.trace = new ArrayList<>();
    }

    public List<String> events() {
        return Collections.unmodifiableList(new ArrayList<>(trace));
    }

    public Map<Long, Byte> bytes() {
        return Collections.unmodifiableMap(new HashMap<>(storage));
    }

    public void clearEvents() {
        trace.clear();
    }

    public void seed8(long address, int value) {
        storage.put(address, (byte) (value & 0xFF));
    }

    public void seed32(long address, int value) {
        for (int i = 0; i < 4; i++) {
            long addr = address + i;
            storage.put(addr, (byte) ((value >>> (8 * i)) & 0xFF));
        }
    }

    public void seed64(long address, long value) {
        for (int i = 0; i < 8; i++) {
            long addr = address + i;
            storage.put(addr, (byte) ((value >>> (8 * i)) & 0xFF));
        }
    }

    private byte getByte(long address) {
        Byte b = storage.get(address);
        if (b == null) {
            throw new IllegalStateException("Missing byte at address: " + Long.toHexString(address));
        }
        return b;
    }

    private void requireBytes(long address, int count) {
        for (int i = 0; i < count; i++) {
            if (!storage.containsKey(address + i)) {
                throw new IllegalStateException("Missing byte at address: " + Long.toHexString(address + i));
            }
        }
    }

    @Override
    public int readUnsigned8(long address) {
        byte b = getByte(address);
        trace.add("R8:" + Long.toHexString(address));
        return b & 0xFF;
    }

    @Override
    public void write8(long address, int value) {
        requireBytes(address, 1);
        byte b = (byte) (value & 0xFF);
        storage.put(address, b);
        trace.add("W8:" + Long.toHexString(address) + ":" + Integer.toHexString(b & 0xFF));
    }

    @Override
    public long readPointer(long address) {
        requireBytes(address, 8);
        long val = 0;
        for (int i = 0; i < 8; i++) {
            byte b = getByte(address + i);
            val |= ((long) (b & 0xFF)) << (8 * i);
        }
        trace.add("R64:" + Long.toHexString(address));
        return val;
    }

    @Override
    public int readInt32(long address) {
        requireBytes(address, 4);
        int val = 0;
        for (int i = 0; i < 4; i++) {
            byte b = getByte(address + i);
            val |= (b & 0xFF) << (8 * i);
        }
        trace.add("R32:" + Long.toHexString(address));
        return val;
    }

    @Override
    public void writeInt32(long address, int value) {
        requireBytes(address, 4);
        for (int i = 0; i < 4; i++) {
            byte b = (byte) ((value >>> (8 * i)) & 0xFF);
            storage.put(address + i, b);
        }
        trace.add("W32:" + Long.toHexString(address) + ":" + Integer.toHexString(value));
    }

    @Override
    public void writeInt64(long address, long value) {
        requireBytes(address, 8);
        for (int i = 0; i < 8; i++) {
            byte b = (byte) ((value >>> (8 * i)) & 0xFF);
            storage.put(address + i, b);
        }
        trace.add("W64:" + Long.toHexString(address) + ":" + Long.toHexString(value));
    }
}