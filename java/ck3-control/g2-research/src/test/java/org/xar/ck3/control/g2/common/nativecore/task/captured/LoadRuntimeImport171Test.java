package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class LoadRuntimeImport171Test {

    @Test
    public void testWindowsApiPortsForwardingAndSlotLifetime() {
        final long pcValue = 0x1234567890ABCDEFL;
        final long returnValue = 0xFEDCBA9876543210L;
        final long poisonValue = 0xCAFEBABECAFEBABEL;
        final LoadRuntime4260e74.LocalSlot64 slot = new LoadRuntime4260e74.LocalSlot64();
        final LoadRuntime4260e74.LocalSlot64 errorSlot = new LoadRuntime4260e74.LocalSlot64();
        final RuntimeException same = new IllegalStateException("owned callback failure");
        final List<String> trace = new ArrayList<>();

        final LoadRuntimeImportBinding.WindowsApiPorts mockApi = new LoadRuntimeImportBinding.WindowsApiPorts() {
            @Override
            public long rtlPcToFileHeader(long pc, LoadRuntime4260e74.LocalSlot64 s) {
                trace.add("api");
                if (pc == -1L) { assertSame(errorSlot, s); throw same; }
                assertEquals(pcValue, pc);
                assertSame(slot, s);
                assertTrue(s.value().isEmpty());
                s.store(poisonValue);
                return returnValue;
            }
        };

        final LoadRuntimeImportBinding.SearchPorts mockSearch = new LoadRuntimeImportBinding.SearchPorts() {
            @Override public long call4260af0(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("Unexpected call4260af0"); }
            @Override public long call4260968(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("Unexpected call4260968"); }
            @Override public long call4260c28(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("Unexpected call4260c28"); }
        };

        final LoadRuntime4260e74.Ports ports = LoadRuntimeImportBinding.ports(mockApi, mockSearch);
        assertEquals(List.of(), trace);
        final long result = ports.call43da2d0(pcValue, slot, Long.MIN_VALUE, -7L, 0xABCDEF0123456789L);

        assertEquals(returnValue, result);
        assertEquals(OptionalLong.of(poisonValue), slot.value());
        assertEquals(List.of("api"), trace);
        assertSame(same, assertThrows(IllegalStateException.class,
                () -> ports.call43da2d0(-1L, errorSlot, 1L, 2L, 3L)));
        assertEquals(OptionalLong.empty(), errorSlot.value());
        assertEquals(List.of("api", "api"), trace);
    }

    @Test
    public void testSearchPortsRoutingAndPacketIdentity() {
        List<String> trace = new ArrayList<>();
        LoadRuntime4260e74.SearchCall packet = new LoadRuntime4260e74.SearchCall(
                Long.MIN_VALUE, 0xFEDCBA9876543210L, -1L, 0L, 0x80000000000000AAL,
                OptionalLong.of(0xF000000000000001L), OptionalLong.of(-7L));
        LoadRuntimeImportBinding.SearchPorts search = new LoadRuntimeImportBinding.SearchPorts() {
            @Override public long call4260af0(LoadRuntime4260e74.SearchCall c) {
                trace.add("af0"); assertSame(packet, c); return 0L;
            }
            @Override public long call4260968(LoadRuntime4260e74.SearchCall c) {
                trace.add("968"); assertSame(packet, c); return -1L;
            }
            @Override public long call4260c28(LoadRuntime4260e74.SearchCall c) {
                trace.add("c28"); assertSame(packet, c); return Long.MIN_VALUE;
            }
        };
        LoadRuntime4260e74.Ports ports = LoadRuntimeImportBinding.ports(
                (pc, slot) -> { throw new AssertionError("unexpected API"); }, search);
        assertEquals(List.of(), trace);
        assertEquals(0L, ports.call4260af0(packet));
        assertEquals(-1L, ports.call4260968(packet));
        assertEquals(Long.MIN_VALUE, ports.call4260c28(packet));
        assertEquals(List.of("af0", "968", "c28"), trace);
    }
}
