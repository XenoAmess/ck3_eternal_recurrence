package org.xar.ck3.research.m3;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.ArrayList;

public final class MapRehashValidation190 {
    private MapRehashValidation190() { }

    public static void main(String[] args) {
        List<MapRehashBook190.Scenario> scenarios = MapRehashBook190.cases();
        if (scenarios.size() != 7) {
            throw new AssertionError("Expected exactly 7 scenarios, got " + scenarios.size());
        }

        int totalEvents = 0;
        int totalPorts = 0;

        for (MapRehashBook190.Scenario s : scenarios) {
            Script script = new Script(s);

            MapRehashApi190.Completion actualCompletion;
            if (s.action() == MapRehashBook190.Action.GROW) {
                actualCompletion = MapRehash190.grow(script, script, s.moduleBase(), s.map(), new MapRehashApi190.Scratch(s.entryRsp()));
            } else {
                MapRehash190.rehash(script, script, s.moduleBase(), s.map(), s.exponent(), new MapRehashApi190.Scratch(s.entryRsp()));
                actualCompletion = MapRehashApi190.Completion.RETURNED;
            }

            if (actualCompletion != s.completion()) {
                throw new AssertionError("Completion mismatch for " + s.id() + ": expected " + s.completion() + " got " + actualCompletion);
            }

            if (!script.isExhausted()) {
                throw new AssertionError("Events not fully consumed for scenario " + s.id());
            }

            totalEvents += s.expected().size();
            totalPorts += script.portCount();
            System.out.println("Scenario " + s.id() + ": Events=" + s.expected().size() + " Ports=" + script.portCount() + " Completion=" + actualCompletion);
        }
        System.out.println("Total Events: " + totalEvents + " Total Ports: " + totalPorts);
    }

    private static class Script implements MapRehashApi190.Memory, MapRehashApi190.Ports {
        private final Map<Long, Byte> storage = new HashMap<>();
        private final List<MapRehashBook190.Event> expected;
        private int cursor = 0;
        private int ports = 0;

        Script(MapRehashBook190.Scenario s) {
            for (MapRehashBook190.Cell c : s.initial()) {
                applyCell(c);
            }
            this.expected = List.copyOf(s.expected());
        }

        boolean isExhausted() {
            return cursor == expected.size();
        }

        int portCount() {
            return ports;
        }

        void applyCell(MapRehashBook190.Cell c) {
            if (c.width() == 1) {
                storage.put(c.address(), (byte)(c.value() & 0xFF));
            } else if (c.width() == 4) {
                for (int i = 0; i < 4; i++) {
                    storage.put(c.address() + i, (byte)((c.value() >>> (i * 8)) & 0xFF));
                }
            } else if (c.width() == 8) {
                for (int i = 0; i < 8; i++) {
                    storage.put(c.address() + i, (byte)((c.value() >>> (i * 8)) & 0xFF));
                }
            } else {
                throw new AssertionError("Invalid width: " + c.width());
            }
        }

        private long readBytes(long address, int width) {
            long val = 0;
            for (int i = 0; i < width; i++) {
                Byte b = storage.get(address + i);
                if (b == null) throw new AssertionError("Missing byte at " + (address + i));
                val |= ((long)(b & 0xFF)) << (i * 8);
            }
            return val;
        }

        private void writeBytes(long address, int width, long value) {
            for (int i = 0; i < width; i++) {
                storage.put(address + i, (byte)((value >>> (i * 8)) & 0xFF));
            }
        }

        private MapRehashBook190.Event nextEvent(MapRehashBook190.Kind kind, long address) {
            if (cursor >= expected.size()) {
                throw new AssertionError("Unexpected event at cursor " + cursor);
            }
            MapRehashBook190.Event ev = expected.get(cursor++);
            if (ev.kind() != kind) throw new AssertionError("Kind mismatch: expected " + kind + " got " + ev.kind());
            if (ev.a() != address) throw new AssertionError("Address mismatch: expected " + address + " got " + ev.a());
            return ev;
        }

        private void checkUnusedFields(MapRehashBook190.Event ev, long b, long c, long d, long e) {
            if (ev.b() != b) throw new AssertionError("B mismatch");
            if (ev.c() != c) throw new AssertionError("C mismatch");
            if (ev.d() != d) throw new AssertionError("D mismatch");
            if (ev.e() != e) throw new AssertionError("E mismatch");
        }

        // Memory interface
        @Override
        public long readPointer(long address) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.READ_POINTER, address);
            checkMemoryReadFields(ev);
            long val = readBytes(address, 8);
            if (ev.returned() != val) throw new AssertionError("Returned mismatch for READ_POINTER");
            return val;
        }

        @Override
        public int readInt32(long address) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.READ_INT32, address);
            checkMemoryReadFields(ev);
            long val = readBytes(address, 4);
            int actual = (int)val;
            if (ev.returned() != (long)actual) throw new AssertionError("Returned mismatch for READ_INT32");
            return actual;
        }

        @Override
        public void writeInt32(long address, int value) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.WRITE_INT32, address);
            checkMemoryWriteFields(ev);
            long val = Integer.toUnsignedLong(value);
            if ((ev.b() & 0xFFFFFFFFL) != val) throw new AssertionError("Value mismatch for WRITE_INT32");
            writeBytes(address, 4, val);
        }

        @Override
        public void writeInt64(long address, long value) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.WRITE_INT64, address);
            checkMemoryWriteFields(ev);
            if (ev.b() != value) throw new AssertionError("Value mismatch for WRITE_INT64");
            writeBytes(address, 8, value);
        }

        @Override
        public int readUnsigned8(long address) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.READ8, address);
            checkMemoryReadFields(ev);
            long val = readBytes(address, 1);
            if (ev.returned() != val) throw new AssertionError("Returned mismatch for READ8");
            return (int)val;
        }

        @Override
        public void write8(long address, int value) {
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.WRITE8, address);
            checkMemoryWriteFields(ev);
            long val = value & 0xFF;
            if ((ev.b() & 0xFFL) != val) throw new AssertionError("Value mismatch for WRITE8");
            writeBytes(address, 1, val);
        }

        // Ports interface
        @Override
        public long gs58(C3e150Api180.Memory memory) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.GS58, 0);
            checkUnusedFields(ev, 0, 0, 0, 0);
            applyWritesAfter(ev);
            return ev.returned();
        }

        @Override
        public void call4223a84(C3e150Api180.Memory memory, long guard) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.INIT_HEADER, guard);
            checkUnusedFields(ev, 0, 0, 0, 0);
            applyWritesAfter(ev);
        }

        @Override
        public void call4223a24(C3e150Api180.Memory memory, long guard) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.INIT_FOOTER, guard);
            checkUnusedFields(ev, 0, 0, 0, 0);
            applyWritesAfter(ev);
        }

        @Override
        public long allocatorSlot08(MapRehashApi190.Memory memory, long code, long allocator, long bytes, int alignment) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.ALLOCATE08, code);
            if (ev.b() != allocator) throw new AssertionError("Allocator mismatch");
            if (ev.c() != bytes) throw new AssertionError("Bytes mismatch");
            if (ev.d() != (long)alignment) throw new AssertionError("Alignment mismatch");
            if (ev.e() != 0) throw new AssertionError("E mismatch");
            applyWritesAfter(ev);
            return ev.returned();
        }

        @Override
        public void allocatorSlot10(MapRehashApi190.Memory memory, long code, long allocator, long block, int alignment) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.FREE10, code);
            if (ev.b() != allocator) throw new AssertionError("Allocator mismatch");
            if (ev.c() != block) throw new AssertionError("Block mismatch");
            if (ev.d() != (long)alignment) throw new AssertionError("Alignment mismatch");
            if (ev.e() != 0) throw new AssertionError("E mismatch");
            applyWritesAfter(ev);
        }

        @Override
        public void callc3b960(MapRehashApi190.Memory memory, long map, long output, int hash, long descriptor, long flagAddress) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.INSERT, map);
            if (ev.b() != output) throw new AssertionError("Output mismatch");
            if (ev.c() != (long)hash) throw new AssertionError("Hash mismatch");
            if (ev.d() != descriptor) throw new AssertionError("Descriptor mismatch");
            if (ev.e() != flagAddress) throw new AssertionError("FlagAddress mismatch");
            applyWritesAfter(ev);
        }

        @Override
        public void call856050(MapRehashApi190.Memory memory, long descriptor) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.CLEANUP, descriptor);
            checkUnusedFields(ev, 0, 0, 0, 0);
            applyWritesAfter(ev);
        }

        @Override
        public void call86f210(MapRehashApi190.Memory memory, long output, long map) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.ERROR_BUILD, output);
            if (ev.b() != map) throw new AssertionError("Map mismatch");
            checkUnusedFields(ev, map, 0, 0, 0);
            applyWritesAfter(ev);
        }

        @Override
        public void call4232cf4(MapRehashApi190.Memory memory) {
            if (memory != this) throw new AssertionError("Memory identity mismatch");
            ports++;
            MapRehashBook190.Event ev = nextEvent(MapRehashBook190.Kind.ERROR_THROW, 0);
            checkUnusedFields(ev, 0, 0, 0, 0);
            applyWritesAfter(ev);
        }

        private void checkMemoryReadFields(MapRehashBook190.Event ev) {
            checkUnusedFields(ev, 0, 0, 0, 0);
            if (!ev.writesAfter().isEmpty()) throw new AssertionError("Memory event has opaque effects");
        }

        private void checkMemoryWriteFields(MapRehashBook190.Event ev) {
            if (ev.c() != 0 || ev.d() != 0 || ev.e() != 0) throw new AssertionError("Memory write placeholder mismatch");
            if (ev.returned() != 0) throw new AssertionError("Memory write return placeholder mismatch");
            if (!ev.writesAfter().isEmpty()) throw new AssertionError("Memory event has opaque effects");
        }

        private void applyWritesAfter(MapRehashBook190.Event ev) {
            for (MapRehashBook190.Cell cell : ev.writesAfter()) {
                applyCell(cell);
            }
        }
    }
}