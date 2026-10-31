package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.fail;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestCriticalSectionImportBinding.WindowsApiPorts;

import java.util.ArrayList;
import java.util.List;

public class RequestCriticalSectionDecode166Test {

    private static final long MODULE_BASE = 0x140000000L;
    private static final long RVA_542F0B8 = 0x542F0B8L;
    private static final long RVA_5C5D568 = 0x5C5D568L;
    private static final long EXPECTED_CS_PTR = MODULE_BASE + 0x5C5D330L;

    @Test
    public void namedApiBoundarySurroundsFreshReadsAndCapturedReturn() {
        final List<String> chronology = new ArrayList<>();
        final long[] seed1 = {0x0000000000000002L};
        final long[] seed2 = {0x0000000000000003L};

        final WindowsApiPorts api = new WindowsApiPorts() {
            @Override
            public void enterCriticalSection(long criticalSectionPtr) {
                chronology.add("Enter");
                assertEquals(EXPECTED_CS_PTR, criticalSectionPtr, "Enter CS ptr");
                seed1[0] = 0x0000000000000001L;
                seed2[0] = 0x0000000000000000L;
            }
            @Override
            public void leaveCriticalSection(long criticalSectionPtr) {
                chronology.add("Leave");
                assertEquals(EXPECTED_CS_PTR, criticalSectionPtr, "Leave CS ptr");
                seed1[0] = 0xFFFFFFFFFFFFFFFFL;
                seed2[0] = 0xFFFFFFFFFFFFFFFFL;
            }
        };

        final NativeTaskMemory memory = new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                chronology.add("Read:" + Long.toHexString(address));
                if (address == MODULE_BASE + RVA_542F0B8) {
                    return seed1[0];
                } else if (address == MODULE_BASE + RVA_5C5D568) {
                    return seed2[0];
                }
                throw new AssertionError("Unexpected read at " + Long.toHexString(address));
            }
            @Override
            public int readInt32(long address) {
                throw new AssertionError("readInt32 should not be called");
            }
            @Override
            public void writeInt32(long address, int value) {
                throw new AssertionError("writeInt32 should not be called");
            }
            @Override
            public void writeInt64(long address, long value) {
                throw new AssertionError("writeInt64 should not be called");
            }
        };

        long result = RequestCriticalSectionDecodeConsumer.decode(MODULE_BASE, memory, api);

        assertEquals(0x8000000000000000L, result, "Captured return value");

        assertEquals(4, chronology.size(), "Chronology size");
        assertEquals("Enter", chronology.get(0));
        assertEquals("Read:" + Long.toHexString(MODULE_BASE + RVA_542F0B8), chronology.get(1));
        assertEquals("Read:" + Long.toHexString(MODULE_BASE + RVA_5C5D568), chronology.get(2));
        assertEquals("Leave", chronology.get(3));
    }

    @Test
    public void abruptNamedCallsStopTheActualSourceContinuation() {
        // Subcase 1: Enter throws
        {
            final List<String> chronology = new ArrayList<>();
            final RuntimeException enterEx = new RuntimeException("Enter failed");

            final WindowsApiPorts api = new WindowsApiPorts() {
                @Override
                public void enterCriticalSection(long criticalSectionPtr) {
                    chronology.add("Enter");
                    throw enterEx;
                }
                @Override
                public void leaveCriticalSection(long criticalSectionPtr) {
                    chronology.add("Leave");
                    throw new RuntimeException("Leave should not be called");
                }
            };

            final NativeTaskMemory memory = new NativeTaskMemory() {
                @Override
                public long readPointer(long address) {
                    chronology.add("Read");
                    return 0L;
                }
                @Override
                public int readInt32(long address) { throw new AssertionError(); }
                @Override
                public void writeInt32(long address, int value) { throw new AssertionError(); }
                @Override
                public void writeInt64(long address, long value) { throw new AssertionError(); }
            };

            try {
                RequestCriticalSectionDecodeConsumer.decode(MODULE_BASE, memory, api);
                fail("Expected RuntimeException from Enter");
            } catch (RuntimeException e) {
                assertSame(enterEx, e, "Enter exception identity");
            }

            assertEquals(1, chronology.size(), "Only Enter logged");
            assertEquals("Enter", chronology.get(0));
        }

        // Subcase 2: Leave throws after two reads
        {
            final List<String> chronology = new ArrayList<>();
            final RuntimeException leaveEx = new RuntimeException("Leave failed");

            final WindowsApiPorts api = new WindowsApiPorts() {
                @Override
                public void enterCriticalSection(long criticalSectionPtr) {
                    chronology.add("Enter");
                }
                @Override
                public void leaveCriticalSection(long criticalSectionPtr) {
                    chronology.add("Leave");
                    throw leaveEx;
                }
            };

            final NativeTaskMemory memory = new NativeTaskMemory() {
                @Override
                public long readPointer(long address) {
                    chronology.add("Read:" + Long.toHexString(address));
                    return 0L;
                }
                @Override
                public int readInt32(long address) { throw new AssertionError(); }
                @Override
                public void writeInt32(long address, int value) { throw new AssertionError(); }
                @Override
                public void writeInt64(long address, long value) { throw new AssertionError(); }
            };

            try {
                RequestCriticalSectionDecodeConsumer.decode(MODULE_BASE, memory, api);
                fail("Expected RuntimeException from Leave");
            } catch (RuntimeException e) {
                assertSame(leaveEx, e, "Leave exception identity");
            }

            assertEquals(4, chronology.size(), "Enter + 2 reads + Leave");
            assertEquals("Enter", chronology.get(0));
            assertEquals("Read:" + Long.toHexString(MODULE_BASE + RVA_542F0B8), chronology.get(1));
            assertEquals("Read:" + Long.toHexString(MODULE_BASE + RVA_5C5D568), chronology.get(2));
            assertEquals("Leave", chronology.get(3));
        }
    }
}
