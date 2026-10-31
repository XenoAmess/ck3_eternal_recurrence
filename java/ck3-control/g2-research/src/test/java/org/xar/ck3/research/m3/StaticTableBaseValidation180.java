package org.xar.ck3.research.m3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m3.C3e150Api180.Memory;
import org.xar.ck3.research.m3.C3e150Api180.Ports;
import org.xar.ck3.research.m3.StaticTableBaseBook180.Kind;
import org.xar.ck3.research.m3.StaticTableBaseBook180.Event;
import org.xar.ck3.research.m3.StaticTableBaseBook180.Scenario;

public final class StaticTableBaseValidation180 {
    private StaticTableBaseValidation180() { }

    public static void main(String[] args) {
        List<Scenario> scenarios = StaticTableBaseBook180.cases();
        int totalScenes = 0;
        int totalAssertions = 0;

        for (Scenario scenario : scenarios) {
            totalScenes++;
            Fixture fixture = new Fixture(scenario);
            Ports ports = new PortsImpl(fixture, scenario);
            long returned = StaticTableBase180.get(fixture, ports, scenario.moduleBase());
            totalAssertions++;
            if (returned != scenario.expectedReturned()) {
                throw new AssertionError("Returned mismatch for " + scenario.id());
            }
            List<Event> actual = fixture.events();
            List<Event> expected = scenario.expectedEvents();
            totalAssertions++;
            if (!actual.equals(expected)) {
                throw new AssertionError("Events mismatch for " + scenario.id());
            }
            System.out.println("Scene " + scenario.id() + " events=" + actual.size());
        }
        System.out.println("Total scenes=" + totalScenes + " assertions=" + totalAssertions);
    }

    private static final class Fixture implements Memory {
        private final Map<Long, Byte> storage = new HashMap<>();
        private final List<Event> observed = new ArrayList<>();
        private final Scenario scenario;

        Fixture(Scenario scenario) {
            this.scenario = scenario;
            seedPointer(scenario.gs58(), scenario.tlsModule());
            seedDword(scenario.tlsModule() + 0x10L, scenario.tlsEpoch());
            seedDword(scenario.moduleBase() + 0x5D1F630L, scenario.guardBefore());
        }

        private void seedPointer(long address, long value) {
            for (int i = 0; i < 8; i++) {
                storage.put(address + i, (byte) (value >>> (8 * i)));
            }
        }

        private void seedDword(long address, long value) {
            for (int i = 0; i < 4; i++) {
                storage.put(address + i, (byte) (value >>> (8 * i)));
            }
        }

        @Override
        public long readPointer(long address) {
            long value = 0L;
            for (int i = 0; i < 8; i++) {
                Byte b = storage.get(address + i);
                if (b == null) throw new AssertionError("Missing byte at " + (address + i));
                value |= ((long) (b & 0xFF)) << (8 * i);
            }
            observed.add(new Event(Kind.READ_POINTER, address, value));
            return value;
        }

        @Override
        public int readInt32(long address) {
            int value = 0;
            for (int i = 0; i < 4; i++) {
                Byte b = storage.get(address + i);
                if (b == null) throw new AssertionError("Missing byte at " + (address + i));
                value |= (b & 0xFF) << (8 * i);
            }
            observed.add(new Event(Kind.READ_DWORD, address, Integer.toUnsignedLong(value)));
            return value;
        }

        @Override
        public void write8(long address, int value) {
            int low8 = value & 0xFF;
            storage.put(address, (byte) low8);
            observed.add(new Event(Kind.WRITE_BYTE, address, low8));
        }

        @Override
        public int readUnsigned8(long address) {
            throw new AssertionError("Unexpected readUnsigned8");
        }

        @Override
        public void writeInt32(long address, int value) {
            throw new AssertionError("Unexpected writeInt32");
        }

        @Override
        public void writeInt64(long address, long value) {
            throw new AssertionError("Unexpected writeInt64");
        }

        List<Event> events() {
            return observed;
        }
    }

    private static final class PortsImpl implements Ports {
        private final Fixture fixture;
        private final Scenario scenario;

        PortsImpl(Fixture fixture, Scenario scenario) {
            this.fixture = fixture;
            this.scenario = scenario;
        }

        @Override
        public long gs58(Memory memory) {
            if (memory != fixture) throw new AssertionError("Memory identity mismatch");
            fixture.observed.add(new Event(Kind.GS58, 0L, scenario.gs58()));
            return scenario.gs58();
        }

        @Override
        public void call4223a84(Memory memory, long guard) {
            if (memory != fixture) throw new AssertionError("Memory identity mismatch");
            fixture.observed.add(new Event(Kind.HEADER, guard, 0L));
            long addr = scenario.moduleBase() + 0x5D1F630L;
            if (guard != addr) throw new AssertionError("Wrong guard arg");
            fixture.storage.put(addr, (byte) (scenario.guardAfterHeader() & 0xFF));
            fixture.storage.put(addr + 1, (byte) ((scenario.guardAfterHeader() >>> 8) & 0xFF));
            fixture.storage.put(addr + 2, (byte) ((scenario.guardAfterHeader() >>> 16) & 0xFF));
            fixture.storage.put(addr + 3, (byte) ((scenario.guardAfterHeader() >>> 24) & 0xFF));
        }

        @Override
        public void call4223a24(Memory memory, long guard) {
            if (memory != fixture) throw new AssertionError("Memory identity mismatch");
            fixture.observed.add(new Event(Kind.FOOTER, guard, 0L));
        }
    }
}