package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.List;

import static org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost.*;

public final class Idler79eScanClearWitnesses {
    private Idler79eScanClearWitnesses() { }

    public static void scanInitialCellsRetention() {
        Memory memory = new Memory();
        long header = memory.allocate(64);
        long cells = memory.allocate(48);
        int key = 0x12345678;
        int payload = 0xCAFEBABE;
        memory.seedInt64(header + 0x20, cells);
        memory.seedInt32(header + 0x2C, 2);
        memory.seedByte(cells + 12, 1);
        memory.seedInt32(cells + 16, payload);
        memory.seedInt32(cells + 20, key);
        memory.onAccess((m, access) -> {
            if (access.op() == Op.READ64 && access.address() == header + 0x20) {
                m.seedInt64(header + 0x20, 0xDEADL);
            }
        });

        Idler79ePorts.ScanResult result = Idler79eCells.scan(header, key, memory);

        same(new Idler79ePorts.ScanResult(cells, payload), result, "captured cells and signed DWORD payload");
        equal(0xDEADL, memory.peekInt64(header + 0x20), "observer really changed cells field");
        same(List.of(
                new Access(Op.READ64, header + 0x20, 8, cells),
                new Access(Op.READ8, cells, 1, 0),
                new Access(Op.READ8, cells + 12, 1, 1),
                new Access(Op.READ8, header + 0x30, 1, 0),
                new Access(Op.READ32, header + 0x2C, 4, 2),
                new Access(Op.READ32, cells + 20, 4, key),
                new Access(Op.READ32, cells + 16, 4, payload)
        ), memory.trace(), "stride twelve and capture-before-observer read order");
    }

    public static void scanEndCalculationWrap() {
        Memory memory = new Memory();
        long header = memory.allocate(64);
        long cells = memory.allocate(48);
        memory.seedInt64(header + 0x20, cells);
        memory.seedByte(header + 0x30, 3);
        memory.seedInt32(header + 0x2C, 0);
        memory.seedByte(cells + 12, 1);
        memory.seedInt32(cells + 16, 0x55667788);
        memory.seedInt32(cells + 20, 0x10203040);
        memory.onAccess((m, access) -> {
            if (access.op() == Op.READ8 && access.address() == cells) {
                m.seedByte(header + 0x30, 1);
                m.seedInt32(header + 0x2C, -1);
            }
        });

        Idler79ePorts.ScanResult result = Idler79eCells.scan(header, 0x10203040, memory);

        same(new Idler79ePorts.ScanResult(cells, -1), result, "FFFFFFFF increment wraps to zero; span is one");
        same(List.of(
                new Access(Op.READ64, header + 0x20, 8, cells),
                new Access(Op.READ8, cells, 1, 0),
                new Access(Op.READ8, cells + 12, 1, 1),
                new Access(Op.READ8, header + 0x30, 1, 1),
                new Access(Op.READ32, header + 0x2C, 4, -1)
        ), memory.trace(), "header values are read after initial marker search; equality skips payload");
    }

    public static void scanNoEndGuardThrows() {
        Memory memory = new Memory();
        long header = memory.allocate(64);
        long cells = memory.allocate(16);
        memory.seedInt64(header + 0x20, cells);
        expectThrows(IllegalArgumentException.class, () -> Idler79eCells.scan(header, 7, memory));
        same(List.of(
                new Access(Op.READ64, header + 0x20, 8, cells),
                new Access(Op.READ8, cells, 1, 0),
                new Access(Op.READ8, cells + 12, 1, 0)
        ), memory.trace(), "initial zero search reaches unmapped cell before reading any end fields");

        Memory afterMismatch = new Memory();
        long nextHeader = afterMismatch.allocate(64);
        long nextCells = afterMismatch.allocate(24);
        afterMismatch.seedInt64(nextHeader + 0x20, nextCells);
        afterMismatch.seedByte(nextCells, 1);
        afterMismatch.seedInt32(nextCells + 8, 8);
        expectThrows(IllegalArgumentException.class, () -> Idler79eCells.scan(nextHeader, 7, afterMismatch));
        same(List.of(
                new Access(Op.READ64, nextHeader + 0x20, 8, nextCells),
                new Access(Op.READ8, nextCells, 1, 1),
                new Access(Op.READ8, nextHeader + 0x30, 1, 0),
                new Access(Op.READ32, nextHeader + 0x2C, 4, 0),
                new Access(Op.READ32, nextCells + 8, 4, 8),
                new Access(Op.READ8, nextCells + 12, 1, 0)
        ), afterMismatch.trace(), "later zero skip also crosses the computed end before checking it");
    }

    public static void finishUsesSelectionInitialCells() {
        Memory memory = new Memory();
        Probe probe = new Probe();
        long header = memory.allocate(64);
        long cells = memory.allocate(48);
        long event = memory.allocate(16);
        int freshEventValue = 0x80000005;
        memory.seedInt32(header + 0x28, 1);
        memory.seedInt64(header + 0x20, cells);
        memory.seedByte(cells, 1);
        memory.seedByte(cells + 24, 1);
        memory.seedByte(cells + 36, 1);
        memory.seedInt32(event + 8, 11);
        int[] decrements = {0};
        memory.onAccess((m, access) -> {
            if (access.op() == Op.DEC32 && access.address() == header + 0x28) {
                if (++decrements[0] == 1) {
                    m.seedInt32(header + 0x28, 2);
                    m.seedInt64(header + 0x20, 0xDEADL);
                }
            } else if (access.op() == Op.READ8 && access.address() == cells + 12) {
                m.seedInt32(header + 0x28, 0);
                m.seedInt32(event + 8, freshEventValue);
            }
        });
        probe.on28eed20(call -> {
            equal(0, memory.peekUnsignedByte(cells + 24), "second occupied marker cleared before tail");
            equal(-1, memory.peekInt32(header + 0x28), "tail follows fresh negative DEC count");
        });

        Idler79eClear.finish(header, event, new Idler79ePorts.ScanResult(cells, 0x12345678), memory, probe);

        equal(2, decrements[0], "exactly two primitive decrements");
        equal(0, memory.peekUnsignedByte(cells), "first occupied marker cleared");
        equal(0, memory.peekUnsignedByte(cells + 12), "zero marker remains zero");
        equal(0, memory.peekUnsignedByte(cells + 24), "held EAX survives zero-marker observer mutation");
        equal(1, memory.peekUnsignedByte(cells + 36), "negative fresh count terminates before next cell");
        equal(0xDEADL, memory.peekInt64(header + 0x20), "header cells mutation was real");
        same(List.of(new Call28(header, freshEventValue, 0x12345678)), probe.calls28eed20(), "fresh tail values");
        same(List.of(
                new Access(Op.READ32, header + 0x28, 4, 1),
                new Access(Op.READ8, cells, 1, 1),
                new Access(Op.WRITE8, cells, 1, 0),
                new Access(Op.DEC32, header + 0x28, 4, 0),
                new Access(Op.READ32, header + 0x28, 4, 2),
                new Access(Op.READ8, cells + 12, 1, 0),
                new Access(Op.READ8, cells + 24, 1, 1),
                new Access(Op.WRITE8, cells + 24, 1, 0),
                new Access(Op.DEC32, header + 0x28, 4, -1),
                new Access(Op.READ32, header + 0x28, 4, -1),
                new Access(Op.READ32, event + 8, 4, freshEventValue)
        ), memory.trace(), "one DEC event, fresh count only after occupied cells, tail after clear");
    }

    public static void finishSentinelAndFreshEvent() {
        Memory negative = new Memory();
        long header = negative.allocate(64);
        negative.seedInt32(header + 0x28, Integer.MIN_VALUE);
        Probe sentinel = new Probe();
        Idler79eClear.finish(header, 0, new Idler79ePorts.ScanResult(0, -1), negative, sentinel);
        same(List.of(new Access(Op.READ32, header + 0x28, 4, Integer.MIN_VALUE)), negative.trace(),
                "signed nonpositive count and raw sentinel do not touch unmapped cells or event");
        check(sentinel.calls28eed20().isEmpty(), "raw minus one suppresses tail");

        Memory zero = new Memory();
        long zeroHeader = zero.allocate(64);
        long event = zero.allocate(16);
        zero.seedInt32(event + 8, 11);
        zero.onAccess((m, access) -> {
            if (access.op() == Op.READ32 && access.address() == zeroHeader + 0x28) {
                m.seedInt32(zeroHeader + 0x28, -7);
                m.seedInt32(event + 8, 99);
            }
        });
        Probe tail = new Probe();
        Idler79eClear.finish(zeroHeader, event, new Idler79ePorts.ScanResult(0, 0xDEADBEEF), zero, tail);
        same(List.of(new Call28(zeroHeader, 99, 0xDEADBEEF)), tail.calls28eed20(), "event value is read after initial count");
        same(List.of(new Access(Op.READ32, zeroHeader + 0x28, 4, 0),
                new Access(Op.READ32, event + 8, 4, 99)), zero.trace(), "no cell read at zero count");

        Memory matched = new Memory();
        long matchedHeader = matched.allocate(64);
        long cells = matched.allocate(12);
        matched.seedInt64(matchedHeader + 0x20, cells);
        matched.seedByte(cells, 1);
        matched.seedInt32(cells + 8, 77);
        matched.seedInt32(cells + 4, -1);
        Idler79ePorts.ScanResult selected = Idler79eCells.scan(matchedHeader, 77, matched);
        same(new Idler79ePorts.ScanResult(cells, -1), selected, "a matched payload can also be sentinel bits");
        matched.clearTrace();
        Probe matchedTail = new Probe();
        Idler79eClear.finish(matchedHeader, 0, selected, matched, matchedTail);
        check(matchedTail.calls28eed20().isEmpty(), "matched payload minus one still suppresses tail");
        same(List.of(new Access(Op.READ32, matchedHeader + 0x28, 4, 0)), matched.trace(), "sentinel never reloads unmapped event");
    }

    public static void run() {
        test("scanInitialCellsRetention", Idler79eScanClearWitnesses::scanInitialCellsRetention);
        test("scanEndCalculationWrap", Idler79eScanClearWitnesses::scanEndCalculationWrap);
        test("scanNoEndGuardThrows", Idler79eScanClearWitnesses::scanNoEndGuardThrows);
        test("finishUsesSelectionInitialCells", Idler79eScanClearWitnesses::finishUsesSelectionInitialCells);
        test("finishSentinelAndFreshEvent", Idler79eScanClearWitnesses::finishSentinelAndFreshEvent);
    }
}
