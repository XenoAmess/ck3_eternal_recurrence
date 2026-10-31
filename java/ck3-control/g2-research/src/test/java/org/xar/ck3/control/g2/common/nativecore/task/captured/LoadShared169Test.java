package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadSharedGetterC45df0;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadSharedSubmitC45e70;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Request140TestMemory;

public final class LoadShared169Test {

    @Test
    public void getterCase1FirstHelperNonNullYFieldZero() {
        Request140TestMemory mem = new Request140TestMemory();
        long moduleBase = 0x100000L;
        long globalA = moduleBase + 0x5C6A520L;
        long rootObject = 0x700000L;
        long xAddr = rootObject + 0x10L;
        long yAddr = 0x100000L + 0x1000L;
        long yPlus28 = yAddr + 0x28L;

        mem.bytes().map(globalA, 8);
        mem.bytes().map(xAddr, 8);
        mem.bytes().map(yPlus28, 8);

        mem.bytes().seedInt64(globalA, rootObject);
        mem.bytes().seedInt64(xAddr, 0x1234567887654321L);
        mem.bytes().seedInt64(yPlus28, 0xCAFEBABEL);

        final long[] capturedArgs = new long[5];
        final int[] capturedFailureMode = new int[1];
        final int[] getterCount = new int[1];

        LoadSharedGetterC45df0.Ports ports = new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                    long targetToken, int failureModeBits) {
                if (++getterCount[0] != 1) throw new AssertionError("unexpected fallback after nonzero Y");
                capturedArgs[0] = objectPointer;
                capturedArgs[1] = adjustmentBits;
                capturedArgs[2] = sourceToken;
                capturedArgs[3] = targetToken;
                capturedFailureMode[0] = failureModeBits;
                mem.bytes().seedInt64(yPlus28, 0L);
                return yAddr;
            }
        };

        long result = LoadSharedGetterC45df0.get(moduleBase, mem, ports);

        Assertions.assertEquals(1, getterCount[0]);
        Assertions.assertEquals(0L, result);
        Assertions.assertEquals(0x1234567887654321L, capturedArgs[0]);
        Assertions.assertEquals(0, capturedArgs[1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, capturedArgs[2]);
        Assertions.assertEquals(moduleBase + 0x5514460L, capturedArgs[3]);
        Assertions.assertEquals(0, capturedFailureMode[0]);

        List<Request140TestMemory.Access> trace = mem.trace();
        Assertions.assertEquals(3, trace.size());
        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(0).op());
        Assertions.assertEquals(globalA, trace.get(0).address());
        Assertions.assertEquals(8, trace.get(0).width());
        Assertions.assertEquals(rootObject, trace.get(0).low());
        Assertions.assertEquals(0L, trace.get(0).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(1).op());
        Assertions.assertEquals(xAddr, trace.get(1).address());
        Assertions.assertEquals(8, trace.get(1).width());
        Assertions.assertEquals(0x1234567887654321L, trace.get(1).low());
        Assertions.assertEquals(0L, trace.get(1).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(2).op());
        Assertions.assertEquals(yPlus28, trace.get(2).address());
        Assertions.assertEquals(8, trace.get(2).width());
        Assertions.assertEquals(0L, trace.get(2).low());
        Assertions.assertEquals(0L, trace.get(2).high());
    }

    @Test
    public void getterCase2FirstHelperNullSecondNonNullZ() {
        Request140TestMemory mem = new Request140TestMemory();
        long moduleBase = 0x100000L;
        long globalA = moduleBase + 0x5C6A520L;
        long rootObject = 0x700000L;
        long xAddr = rootObject + 0x10L;
        long zAddr = 0x100000L + 0x2000L;
        long zPlus10 = zAddr + 0x10L;
        long originalX = 0x1234567887654321L;
        long mutatedX = 0xFEDCBA9876543210L;
        long zField = -1L;

        mem.bytes().map(globalA, 8);
        mem.bytes().map(xAddr, 8);
        mem.bytes().map(zPlus10, 8);

        mem.bytes().seedInt64(globalA, rootObject);
        mem.bytes().seedInt64(xAddr, originalX);
        mem.bytes().seedInt64(zPlus10, zField);

        final long[][] allArgs = new long[2][5];
        final int[] callCount = new int[1];

        LoadSharedGetterC45df0.Ports ports = new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                    long targetToken, int failureModeBits) {
                int idx = callCount[0]++;
                allArgs[idx][0] = objectPointer;
                allArgs[idx][1] = adjustmentBits;
                allArgs[idx][2] = sourceToken;
                allArgs[idx][3] = targetToken;
                allArgs[idx][4] = failureModeBits;
                if (idx == 0) {
                    mem.bytes().seedInt64(xAddr, mutatedX);
                    return 0L;
                } else {
                    return zAddr;
                }
            }
        };

        long result = LoadSharedGetterC45df0.get(moduleBase, mem, ports);

        Assertions.assertEquals(zField, result);
        Assertions.assertEquals(2, callCount[0]);

        Assertions.assertEquals(originalX, allArgs[0][0]);
        Assertions.assertEquals(0, allArgs[0][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, allArgs[0][2]);
        Assertions.assertEquals(moduleBase + 0x5514460L, allArgs[0][3]);
        Assertions.assertEquals(0, allArgs[0][4]);

        Assertions.assertEquals(originalX, allArgs[1][0]);
        Assertions.assertEquals(0, allArgs[1][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, allArgs[1][2]);
        Assertions.assertEquals(moduleBase + 0x5519DC0L, allArgs[1][3]);
        Assertions.assertEquals(0, allArgs[1][4]);

        List<Request140TestMemory.Access> trace = mem.trace();
        Assertions.assertEquals(3, trace.size());
        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(0).op());
        Assertions.assertEquals(globalA, trace.get(0).address());
        Assertions.assertEquals(8, trace.get(0).width());
        Assertions.assertEquals(rootObject, trace.get(0).low());
        Assertions.assertEquals(0L, trace.get(0).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(1).op());
        Assertions.assertEquals(xAddr, trace.get(1).address());
        Assertions.assertEquals(8, trace.get(1).width());
        Assertions.assertEquals(originalX, trace.get(1).low());
        Assertions.assertEquals(0L, trace.get(1).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(2).op());
        Assertions.assertEquals(zPlus10, trace.get(2).address());
        Assertions.assertEquals(8, trace.get(2).width());
        Assertions.assertEquals(zField, trace.get(2).low());
        Assertions.assertEquals(0L, trace.get(2).high());
    }

    @Test
    public void getterCase3BothHelpersNull() {
        Request140TestMemory mem = new Request140TestMemory();
        long moduleBase = 0x100000L;
        long globalA = moduleBase + 0x5C6A520L;
        long rootObject = 0x700000L;
        long xAddr = rootObject + 0x10L;
        long originalX = 0x1234567887654321L;

        mem.bytes().map(globalA, 8);
        mem.bytes().map(xAddr, 8);

        mem.bytes().seedInt64(globalA, rootObject);
        mem.bytes().seedInt64(xAddr, originalX);

        final long[][] allArgs = new long[2][5];
        final int[] callCount = new int[1];

        LoadSharedGetterC45df0.Ports ports = new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                    long targetToken, int failureModeBits) {
                int idx = callCount[0]++;
                allArgs[idx][0] = objectPointer;
                allArgs[idx][1] = adjustmentBits;
                allArgs[idx][2] = sourceToken;
                allArgs[idx][3] = targetToken;
                allArgs[idx][4] = failureModeBits;
                return 0L;
            }
        };

        long result = LoadSharedGetterC45df0.get(moduleBase, mem, ports);

        Assertions.assertEquals(0L, result);
        Assertions.assertEquals(2, callCount[0]);

        Assertions.assertEquals(originalX, allArgs[0][0]);
        Assertions.assertEquals(0, allArgs[0][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, allArgs[0][2]);
        Assertions.assertEquals(moduleBase + 0x5514460L, allArgs[0][3]);
        Assertions.assertEquals(0, allArgs[0][4]);

        Assertions.assertEquals(originalX, allArgs[1][0]);
        Assertions.assertEquals(0, allArgs[1][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, allArgs[1][2]);
        Assertions.assertEquals(moduleBase + 0x5519DC0L, allArgs[1][3]);
        Assertions.assertEquals(0, allArgs[1][4]);

        List<Request140TestMemory.Access> trace = mem.trace();
        Assertions.assertEquals(2, trace.size());
        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(0).op());
        Assertions.assertEquals(globalA, trace.get(0).address());
        Assertions.assertEquals(8, trace.get(0).width());
        Assertions.assertEquals(rootObject, trace.get(0).low());
        Assertions.assertEquals(0L, trace.get(0).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(1).op());
        Assertions.assertEquals(xAddr, trace.get(1).address());
        Assertions.assertEquals(8, trace.get(1).width());
        Assertions.assertEquals(originalX, trace.get(1).low());
        Assertions.assertEquals(0L, trace.get(1).high());
    }

    @Test
    public void callerCase4SubmitWithNonNullM() {
        Request140TestMemory mem = new Request140TestMemory();
        long moduleBase = 0x100000L;
        long globalA = moduleBase + 0x5C6A520L;
        long rootObject = 0x700000L;
        long xAddr = rootObject + 0x10L;
        long yAddr = 0x100000L + 0x1000L;
        long yPlus28 = yAddr + 0x28L;
        long mAddr = 0x100000L + 0x3000L;
        long mPlus18 = mAddr + 0x18L;
        long holderAddr = 0x100000L + 0x4000L;
        long scratchAddr = 0x100000L + 0x5000L;
        long scratchSentinel = 0x5555AAAAFFFF0001L;
        long o1 = 0x11111111L;
        long o2 = 0x22222222L;
        long o3 = 0x33333333L;
        long o4 = 0x44444444L;

        mem.bytes().map(globalA, 8);
        mem.bytes().map(xAddr, 8);
        mem.bytes().map(yPlus28, 8);
        mem.bytes().map(holderAddr, 8);
        mem.bytes().map(scratchAddr, 8);

        mem.bytes().seedInt64(globalA, rootObject);
        mem.bytes().seedInt64(xAddr, 0x1234567887654321L);
        mem.bytes().seedInt64(yPlus28, mAddr);
        mem.bytes().seedInt64(holderAddr, o1);
        mem.bytes().seedInt64(scratchAddr, scratchSentinel);

        final long[][] getterArgs = new long[1][5];
        final int[] getterCallCount = new int[1];
        final List<String> sequence = new ArrayList<>();

        LoadSharedGetterC45df0.Ports getterPorts = new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                    long targetToken, int failureModeBits) {
                sequence.add("convert");
                getterArgs[0][0] = objectPointer;
                getterArgs[0][1] = adjustmentBits;
                getterArgs[0][2] = sourceToken;
                getterArgs[0][3] = targetToken;
                getterArgs[0][4] = failureModeBits;
                getterCallCount[0]++;
                return yAddr;
            }
        };

        final long[][] appendArgs = new long[1][2];
        final int[] appendCallCount = new int[1];
        final long[] virtual0Args = new long[2];
        final int[] virtual0Flags = new int[2];
        final int[] virtual0Count = new int[1];

        LoadSharedSubmitC45e70.Ports submitPorts = new LoadSharedSubmitC45e70.Ports() {
            @Override
            public void callC45ee0(long containerAddress, long holderAddress) {
                sequence.add("append");
                appendArgs[0][0] = containerAddress;
                appendArgs[0][1] = holderAddress;
                appendCallCount[0]++;
                Assertions.assertEquals(mPlus18, containerAddress);
                Assertions.assertEquals(scratchAddr, holderAddress);
                Assertions.assertEquals(0L, mem.bytes().peekInt64(holderAddr));
                Assertions.assertEquals(o1, mem.bytes().peekInt64(scratchAddr));
                mem.bytes().seedInt64(scratchAddr, o2);
                mem.bytes().seedInt64(holderAddr, o3);
            }
            @Override
            public void virtual0(long receiver, int flags) {
                sequence.add("virtual:" + Long.toHexString(receiver));
                virtual0Args[virtual0Count[0]] = receiver;
                virtual0Flags[virtual0Count[0]] = flags;
                virtual0Count[0]++;
                if (virtual0Count[0] == 1) {
                    mem.bytes().seedInt64(holderAddr, o4);
                }
            }
        };

        LoadSharedSubmitC45e70.submit(moduleBase, holderAddr, scratchAddr, mem, getterPorts, submitPorts);

        Assertions.assertEquals(List.of("convert", "append",
                "virtual:" + Long.toHexString(o2), "virtual:" + Long.toHexString(o4)), sequence);
        Assertions.assertEquals(1, getterCallCount[0]);
        Assertions.assertEquals(0x1234567887654321L, getterArgs[0][0]);
        Assertions.assertEquals(0, getterArgs[0][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, getterArgs[0][2]);
        Assertions.assertEquals(moduleBase + 0x5514460L, getterArgs[0][3]);
        Assertions.assertEquals(0, getterArgs[0][4]);

        Assertions.assertEquals(1, appendCallCount[0]);
        Assertions.assertEquals(mPlus18, appendArgs[0][0]);
        Assertions.assertEquals(scratchAddr, appendArgs[0][1]);

        Assertions.assertEquals(2, virtual0Count[0]);
        Assertions.assertEquals(o2, virtual0Args[0]);
        Assertions.assertEquals(1, virtual0Flags[0]);
        Assertions.assertEquals(o4, virtual0Args[1]);
        Assertions.assertEquals(1, virtual0Flags[1]);

        Assertions.assertEquals(o4, mem.bytes().peekInt64(holderAddr));
        Assertions.assertEquals(o2, mem.bytes().peekInt64(scratchAddr));

        List<Request140TestMemory.Access> trace = mem.trace();
        Assertions.assertEquals(8, trace.size());
        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(0).op());
        Assertions.assertEquals(globalA, trace.get(0).address());
        Assertions.assertEquals(8, trace.get(0).width());
        Assertions.assertEquals(rootObject, trace.get(0).low());
        Assertions.assertEquals(0L, trace.get(0).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(1).op());
        Assertions.assertEquals(xAddr, trace.get(1).address());
        Assertions.assertEquals(8, trace.get(1).width());
        Assertions.assertEquals(0x1234567887654321L, trace.get(1).low());
        Assertions.assertEquals(0L, trace.get(1).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(2).op());
        Assertions.assertEquals(yPlus28, trace.get(2).address());
        Assertions.assertEquals(8, trace.get(2).width());
        Assertions.assertEquals(mAddr, trace.get(2).low());
        Assertions.assertEquals(0L, trace.get(2).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(3).op());
        Assertions.assertEquals(holderAddr, trace.get(3).address());
        Assertions.assertEquals(8, trace.get(3).width());
        Assertions.assertEquals(o1, trace.get(3).low());
        Assertions.assertEquals(0L, trace.get(3).high());

        Assertions.assertEquals(Request140TestMemory.Op.WRITE64, trace.get(4).op());
        Assertions.assertEquals(holderAddr, trace.get(4).address());
        Assertions.assertEquals(8, trace.get(4).width());
        Assertions.assertEquals(0L, trace.get(4).low());
        Assertions.assertEquals(0L, trace.get(4).high());

        Assertions.assertEquals(Request140TestMemory.Op.WRITE64, trace.get(5).op());
        Assertions.assertEquals(scratchAddr, trace.get(5).address());
        Assertions.assertEquals(8, trace.get(5).width());
        Assertions.assertEquals(o1, trace.get(5).low());
        Assertions.assertEquals(0L, trace.get(5).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(6).op());
        Assertions.assertEquals(scratchAddr, trace.get(6).address());
        Assertions.assertEquals(8, trace.get(6).width());
        Assertions.assertEquals(o2, trace.get(6).low());
        Assertions.assertEquals(0L, trace.get(6).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(7).op());
        Assertions.assertEquals(holderAddr, trace.get(7).address());
        Assertions.assertEquals(8, trace.get(7).width());
        Assertions.assertEquals(o4, trace.get(7).low());
        Assertions.assertEquals(0L, trace.get(7).high());
    }

    @Test
    public void callerCase5SubmitWithNullM() {
        Request140TestMemory mem = new Request140TestMemory();
        long moduleBase = 0x100000L;
        long globalA = moduleBase + 0x5C6A520L;
        long rootObject = 0x700000L;
        long xAddr = rootObject + 0x10L;
        long holderAddr = 0x100000L + 0x4000L;
        long scratchAddr = 0x100000L + 0x5000L;
        long scratchSentinel = 0x5555AAAAFFFF0001L;
        long o = 0x55555555L;

        mem.bytes().map(globalA, 8);
        mem.bytes().map(xAddr, 8);
        mem.bytes().map(holderAddr, 8);
        mem.bytes().map(scratchAddr, 8);

        mem.bytes().seedInt64(globalA, rootObject);
        mem.bytes().seedInt64(xAddr, 0x1234567887654321L);
        mem.bytes().seedInt64(holderAddr, o);
        mem.bytes().seedInt64(scratchAddr, scratchSentinel);

        final long[][] getterArgs = new long[2][5];
        final int[] getterCallCount = new int[1];
        final List<String> sequence = new ArrayList<>();

        LoadSharedGetterC45df0.Ports getterPorts = new LoadSharedGetterC45df0.Ports() {
            @Override
            public long call4260e74(long objectPointer, int adjustmentBits, long sourceToken,
                    long targetToken, int failureModeBits) {
                int idx = getterCallCount[0]++;
                sequence.add(idx == 0 ? "convert:first" : "convert:fallback");
                getterArgs[idx][0] = objectPointer;
                getterArgs[idx][1] = adjustmentBits;
                getterArgs[idx][2] = sourceToken;
                getterArgs[idx][3] = targetToken;
                getterArgs[idx][4] = failureModeBits;
                return 0L;
            }
        };

        final int[] appendCallCount = new int[1];
        final long[] virtual0Args = new long[1];
        final int[] virtual0Flags = new int[1];
        final int[] virtual0Count = new int[1];

        LoadSharedSubmitC45e70.Ports submitPorts = new LoadSharedSubmitC45e70.Ports() {
            @Override
            public void callC45ee0(long containerAddress, long holderAddress) {
                appendCallCount[0]++;
                throw new AssertionError("append forbidden for null M");
            }
            @Override
            public void virtual0(long receiver, int flags) {
                sequence.add("virtual");
                virtual0Args[virtual0Count[0]] = receiver;
                virtual0Flags[virtual0Count[0]] = flags;
                virtual0Count[0]++;
            }
        };

        LoadSharedSubmitC45e70.submit(moduleBase, holderAddr, scratchAddr, mem, getterPorts, submitPorts);

        Assertions.assertEquals(List.of("convert:first", "convert:fallback", "virtual"), sequence);
        Assertions.assertEquals(2, getterCallCount[0]);
        Assertions.assertEquals(0x1234567887654321L, getterArgs[0][0]);
        Assertions.assertEquals(0, getterArgs[0][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, getterArgs[0][2]);
        Assertions.assertEquals(moduleBase + 0x5514460L, getterArgs[0][3]);
        Assertions.assertEquals(0, getterArgs[0][4]);
        Assertions.assertEquals(0x1234567887654321L, getterArgs[1][0]);
        Assertions.assertEquals(0, getterArgs[1][1]);
        Assertions.assertEquals(moduleBase + 0x5514438L, getterArgs[1][2]);
        Assertions.assertEquals(moduleBase + 0x5519DC0L, getterArgs[1][3]);
        Assertions.assertEquals(0, getterArgs[1][4]);

        Assertions.assertEquals(0, appendCallCount[0]);
        Assertions.assertEquals(1, virtual0Count[0]);
        Assertions.assertEquals(o, virtual0Args[0]);
        Assertions.assertEquals(1, virtual0Flags[0]);

        Assertions.assertEquals(o, mem.bytes().peekInt64(holderAddr));
        Assertions.assertEquals(scratchSentinel, mem.bytes().peekInt64(scratchAddr));

        List<Request140TestMemory.Access> trace = mem.trace();
        Assertions.assertEquals(3, trace.size());
        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(0).op());
        Assertions.assertEquals(globalA, trace.get(0).address());
        Assertions.assertEquals(8, trace.get(0).width());
        Assertions.assertEquals(rootObject, trace.get(0).low());
        Assertions.assertEquals(0L, trace.get(0).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(1).op());
        Assertions.assertEquals(xAddr, trace.get(1).address());
        Assertions.assertEquals(8, trace.get(1).width());
        Assertions.assertEquals(0x1234567887654321L, trace.get(1).low());
        Assertions.assertEquals(0L, trace.get(1).high());

        Assertions.assertEquals(Request140TestMemory.Op.READ64, trace.get(2).op());
        Assertions.assertEquals(holderAddr, trace.get(2).address());
        Assertions.assertEquals(8, trace.get(2).width());
        Assertions.assertEquals(o, trace.get(2).low());
        Assertions.assertEquals(0L, trace.get(2).high());
    }
}
