package org.xar.ck3.research.m3;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;

public final class MoveSlotValidation193 {
    private MoveSlotValidation193() { }

    public static void main(String[] args) {
        List<MoveSlotBook193.Scenario> scenarios = MoveSlotBook193.cases();
        if (scenarios.size() != 3) {
            throw new AssertionError("Expected exactly 3 scenarios, got " + scenarios.size());
        }

        int totalEvents = 0;
        int totalPorts = 0;

        for (MoveSlotBook193.Scenario s : scenarios) {
            Script script = new Script(s);

            // Seed initial cells
            for (MoveSlotBook193.Cell c : s.initial()) {
                if (c.width() == 1) {
                    script.setByte(c.address(), (byte)c.value());
                } else if (c.width() == 4) {
                    script.setInt32(c.address(), (int)c.value());
                } else if (c.width() == 8) {
                    script.setInt64(c.address(), c.value());
                } else {
                    throw new AssertionError("Invalid initial cell width: " + c.width());
                }
            }

            // Execute target
            MoveSlot193.move(script, script, s.bucket(), s.probe(), s.hash(), s.descriptor());

            // Verify cursor
            if (script.cursor != script.expected.size()) {
                throw new AssertionError("Cursor mismatch for scenario " + s.id() + ": expected " + script.expected.size() + " got " + script.cursor);
            }

            totalEvents += script.expected.size();
            totalPorts += script.cleanupCount;
        }

        System.out.println("Scenarios: " + scenarios.size() + ", Events: " + totalEvents + ", Ports: " + totalPorts);
    }

    private static class Script implements RequestE92780.Memory, MoveSlotApi193.Ports {
        private final MoveSlotBook193.Scenario scenario;
        private final List<MoveSlotBook193.Event> expected;
        private final Map<Long, Byte> storage = new HashMap<>();
        private int cursor = 0;
        private int cleanupCount = 0;

        Script(MoveSlotBook193.Scenario scenario) {
            this.scenario = scenario;
            this.expected = List.copyOf(scenario.expected());
        }

        private void checkEvent(MoveSlotBook193.Kind kind, long address, long low, long high) {
            if (cursor >= expected.size()) {
                throw new AssertionError("Unexpected operation: " + kind + " at " + address);
            }
            MoveSlotBook193.Event e = expected.get(cursor);
            if (e.kind() != kind || e.address() != address || e.low() != low || e.high() != high) {
                throw new AssertionError("Event mismatch at cursor " + cursor + ": expected " + e + " got kind=" + kind + " addr=" + address + " low=" + low + " high=" + high);
            }
            if (!e.writesAfter().isEmpty() && kind != MoveSlotBook193.Kind.CLEANUP) {
                 throw new AssertionError("Non-cleanup event has writesAfter");
            }
            cursor++;
        }

        private void applyWritesAfter(List<MoveSlotBook193.Cell> writes) {
            for (MoveSlotBook193.Cell c : writes) {
                if (c.width() == 1) {
                    setByte(c.address(), (byte)c.value());
                } else if (c.width() == 4) {
                    setInt32(c.address(), (int)c.value());
                } else if (c.width() == 8) {
                    setInt64(c.address(), c.value());
                } else {
                    throw new AssertionError("Invalid writeAfter cell width: " + c.width());
                }
            }
        }

        private void setByte(long address, byte value) {
            storage.put(address, value);
        }

        private void setInt32(long address, int value) {
            storage.put(address, (byte)(value & 0xFF));
            storage.put(address + 1, (byte)((value >> 8) & 0xFF));
            storage.put(address + 2, (byte)((value >> 16) & 0xFF));
            storage.put(address + 3, (byte)((value >> 24) & 0xFF));
        }

        private void setInt64(long address, long value) {
            for (int i = 0; i < 8; i++) {
                storage.put(address + i, (byte)((value >> (i * 8)) & 0xFF));
            }
        }

        private byte getByte(long address) {
            Byte b = storage.get(address);
            if (b == null) {
                throw new AssertionError("Missing byte at address " + address);
            }
            return b;
        }

        private long getInt64(long address) {
            long v = 0;
            for (int i = 0; i < 8; i++) {
                v |= (long)(getByte(address + i) & 0xFF) << (i * 8);
            }
            return v;
        }

        @Override
        public long readPointer(long address) {
            throw new AssertionError("readPointer not projected");
        }

        @Override
        public int readInt32(long address) {
            throw new AssertionError("readInt32 not projected");
        }

        @Override
        public void writeInt32(long address, int value) {
            checkEvent(MoveSlotBook193.Kind.WRITE_INT32, address, (long)value, 0L);
            setInt32(address, value);
        }

        @Override
        public void writeInt64(long address, long value) {
            checkEvent(MoveSlotBook193.Kind.WRITE_INT64, address, value, 0L);
            setInt64(address, value);
        }

        @Override
        public int readUnsignedByte(long address) {
            throw new AssertionError("readUnsignedByte not projected");
        }

        @Override
        public void writeByte(long address, byte value) {
            checkEvent(MoveSlotBook193.Kind.WRITE_BYTE, address, (long)Byte.toUnsignedInt(value), 0L);
            setByte(address, value);
        }

        @Override
        public void writeInt16(long address, short value) {
            throw new AssertionError("writeInt16 not projected");
        }

        @Override
        public RequestE92780.Raw128 readRaw128(long address) {
            long low = getInt64(address);
            long high = getInt64(address + 8L);
            checkEvent(MoveSlotBook193.Kind.READ_RAW128, address, low, high);
            return new RequestE92780.Raw128(low, high);
        }

        @Override
        public void writeRaw128(long address, RequestE92780.Raw128 value) {
            checkEvent(MoveSlotBook193.Kind.WRITE_RAW128, address, value.low(), value.high());
            setInt64(address, value.low());
            setInt64(address + 8, value.high());
        }

        @Override
        public void call856050(RequestE92780.Memory memory, long descriptor) {
            if (memory != this) {
                throw new AssertionError("Memory identity mismatch");
            }
            checkEvent(MoveSlotBook193.Kind.CLEANUP, descriptor, 0L, 0L);
            MoveSlotBook193.Event e = expected.get(cursor - 1);
            applyWritesAfter(e.writesAfter());
            cleanupCount++;
        }
    }
}