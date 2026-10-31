package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.fail;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestGate424cffc;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestGateStaticDispatchConsumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestCriticalSectionImportBinding;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestStaticDispatch4267630;

import java.util.ArrayList;
import java.util.List;

public final class RequestGateStaticDispatch167Test {

    private static final long MODULE_BASE = 0x100000000L;
    private static final long READ_ADDR_1 = MODULE_BASE + 0x542f0b8L;
    private static final long READ_ADDR_2 = MODULE_BASE + 0x5c5d568L;

    // Hand-computed fixed decoded literal for the test scenario.
    // Seed1 (RBX initial): 0x0000000000000001L
    // Seed2 (XOR key):     0x0000000000000000L
    // Shift (ECX & 0x3F): 0x0000000000000001L (from Seed1 low bits masked)
    // ROR 1 of (0x1 ^ 0x0) is 0x8000000000000000L.
    private static final long FIXED_DECODED_VALUE = 0x8000000000000000L;

    private static final long SIZE_BITS = 0x8000000000000001L; // High bit set, nonzero

    @Test
    public void composedGateTransfersDecodedTargetAfterNamedLeave() {
        List<String> chronology = new ArrayList<>();
        long[] enterSeed = {0x0000000000000002L};
        long[] leaveSeed = {0x0000000000000003L};
        long[] targetCallCount = {0};
        long[] recordedTargetRax = {0};
        long[] recordedTargetRcx = {0};
        int[] recordedTargetEax = {-7};

        // Memory implementation: only allows reads at exact addresses, records chronology
        NativeTaskMemory memory = new NativeTaskMemory() {
            @Override
            public long readPointer(long address) {
                if (address == READ_ADDR_1) {
                    chronology.add("READ1");
                    return enterSeed[0];
                } else if (address == READ_ADDR_2) {
                    chronology.add("READ2");
                    return leaveSeed[0];
                } else {
                    throw new AssertionError("Illegal read at " + Long.toHexString(address));
                }
            }
            @Override
            public int readInt32(long address) {
                throw new AssertionError("Illegal readInt32");
            }
            @Override
            public void writeInt32(long address, int value) {
                throw new AssertionError("Illegal writeInt32");
            }
            @Override
            public void writeInt64(long address, long value) {
                throw new AssertionError("Illegal writeInt64");
            }
        };

        // Windows API ports: Enter and Leave
        RequestCriticalSectionImportBinding.WindowsApiPorts api = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
            @Override
            public void enterCriticalSection(long criticalSectionPtr) {
                chronology.add("ENTER");
                assertEquals(0x105c5d330L, criticalSectionPtr);
                // Supplied-port test mutation, not a claim about Windows lock effects.
                enterSeed[0] = 0x0000000000000001L;
                leaveSeed[0] = 0x0000000000000000L;
            }
            @Override
            public void leaveCriticalSection(long criticalSectionPtr) {
                chronology.add("LEAVE");
                assertEquals(0x105c5d330L, criticalSectionPtr);
                // Mutate seeds again after captured decode
                enterSeed[0] = 0x0000000000000000L;
                leaveSeed[0] = 0x0000000000000000L;
            }
        };

        // TailTarget: The dispatch target
        RequestStaticDispatch4267630.TailTarget target = new RequestStaticDispatch4267630.TailTarget() {
            @Override
            public int jumpRax(long targetRax, long knownRcx) {
                chronology.add("TARGET");
                targetCallCount[0]++;
                recordedTargetRax[0] = targetRax;
                recordedTargetRcx[0] = knownRcx;
                return recordedTargetEax[0];
            }
        };

        // Construct the ports for the gate
        RequestGate424cffc.Ports ports = RequestGateStaticDispatchConsumer.ports(MODULE_BASE, memory, api, target);

        // Execute the gate
        int result = RequestGate424cffc.execute(SIZE_BITS, ports);

        // Assertions
        assertEquals(1, result, "Gate should return 1 for nonzero target EAX");
        assertEquals(1, targetCallCount[0], "Target should be called exactly once");
        assertEquals(FIXED_DECODED_VALUE, recordedTargetRax[0], "Target RAX should be the fixed decoded value");
        assertEquals(SIZE_BITS, recordedTargetRcx[0], "Target RCX should be the original size bits");

        // Verify chronology: Enter -> Read1 -> Read2 -> Leave -> Target
        assertEquals(5, chronology.size());
        assertEquals("ENTER", chronology.get(0));
        assertEquals("READ1", chronology.get(1));
        assertEquals("READ2", chronology.get(2));
        assertEquals("LEAVE", chronology.get(3));
        assertEquals("TARGET", chronology.get(4));

        chronology.clear();
        targetCallCount[0] = 0;
        recordedTargetEax[0] = 0;
        int zeroResult = RequestGate424cffc.execute(SIZE_BITS, ports);
        assertEquals(0, zeroResult);
        assertEquals(1, targetCallCount[0]);
        assertEquals(FIXED_DECODED_VALUE, recordedTargetRax[0]);
        assertEquals(SIZE_BITS, recordedTargetRcx[0]);
        assertEquals(List.of("ENTER", "READ1", "READ2", "LEAVE", "TARGET"), chronology);
    }

    @Test
    public void composedFailuresStopBeforeOrAtTheTarget() {
        // Subcase 1: Leave throws before target
        {
            List<String> chronology = new ArrayList<>();
            long[] targetCallCount = {0};
            RuntimeException leaveFailure = new RuntimeException("LeaveFailure");

            NativeTaskMemory memory = new NativeTaskMemory() {
                @Override
                public long readPointer(long address) {
                    if (address == READ_ADDR_1) {
                        chronology.add("READ1");
                        return 0x0000000000000001L;
                    } else if (address == READ_ADDR_2) {
                        chronology.add("READ2");
                        return 0x0000000000000000L;
                    } else {
                        throw new AssertionError("Illegal read");
                    }
                }
                @Override
                public int readInt32(long address) { throw new AssertionError(); }
                @Override
                public void writeInt32(long address, int value) { throw new AssertionError(); }
                @Override
                public void writeInt64(long address, long value) { throw new AssertionError(); }
            };

            RequestCriticalSectionImportBinding.WindowsApiPorts api = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
                @Override
                public void enterCriticalSection(long criticalSectionPtr) {
                    chronology.add("ENTER");
                }
                @Override
                public void leaveCriticalSection(long criticalSectionPtr) {
                    chronology.add("LEAVE");
                    throw leaveFailure;
                }
            };

            RequestStaticDispatch4267630.TailTarget target = new RequestStaticDispatch4267630.TailTarget() {
                @Override
                public int jumpRax(long targetRax, long knownRcx) {
                    targetCallCount[0]++;
                    return 1;
                }
            };

            RequestGate424cffc.Ports ports = RequestGateStaticDispatchConsumer.ports(MODULE_BASE, memory, api, target);

            try {
                RequestGate424cffc.execute(SIZE_BITS, ports);
                fail("Should have thrown");
            } catch (RuntimeException e) {
                assertSame(leaveFailure, e);
            }

            assertEquals(0, targetCallCount[0], "Target should not be called if Leave throws");
            assertEquals(4, chronology.size());
            assertEquals("ENTER", chronology.get(0));
            assertEquals("READ1", chronology.get(1));
            assertEquals("READ2", chronology.get(2));
            assertEquals("LEAVE", chronology.get(3));
        }

        // Subcase 2: Target throws after Leave
        {
            List<String> chronology = new ArrayList<>();
            long[] targetCallCount = {0};
            RuntimeException targetFailure = new RuntimeException("TargetFailure");

            NativeTaskMemory memory = new NativeTaskMemory() {
                @Override
                public long readPointer(long address) {
                    if (address == READ_ADDR_1) {
                        chronology.add("READ1");
                        return 0x0000000000000001L;
                    } else if (address == READ_ADDR_2) {
                        chronology.add("READ2");
                        return 0x0000000000000000L;
                    } else {
                        throw new AssertionError("Illegal read");
                    }
                }
                @Override
                public int readInt32(long address) { throw new AssertionError(); }
                @Override
                public void writeInt32(long address, int value) { throw new AssertionError(); }
                @Override
                public void writeInt64(long address, long value) { throw new AssertionError(); }
            };

            RequestCriticalSectionImportBinding.WindowsApiPorts api = new RequestCriticalSectionImportBinding.WindowsApiPorts() {
                @Override
                public void enterCriticalSection(long criticalSectionPtr) {
                    chronology.add("ENTER");
                }
                @Override
                public void leaveCriticalSection(long criticalSectionPtr) {
                    chronology.add("LEAVE");
                }
            };

            RequestStaticDispatch4267630.TailTarget target = new RequestStaticDispatch4267630.TailTarget() {
                @Override
                public int jumpRax(long targetRax, long knownRcx) {
                    chronology.add("TARGET");
                    targetCallCount[0]++;
                    throw targetFailure;
                }
            };

            RequestGate424cffc.Ports ports = RequestGateStaticDispatchConsumer.ports(MODULE_BASE, memory, api, target);

            try {
                RequestGate424cffc.execute(SIZE_BITS, ports);
                fail("Should have thrown");
            } catch (RuntimeException e) {
                assertSame(targetFailure, e);
            }

            assertEquals(1, targetCallCount[0], "Target should be called once");
            assertEquals(5, chronology.size());
            assertEquals("ENTER", chronology.get(0));
            assertEquals("READ1", chronology.get(1));
            assertEquals("READ2", chronology.get(2));
            assertEquals("LEAVE", chronology.get(3));
            assertEquals("TARGET", chronology.get(4));
        }
    }
}
