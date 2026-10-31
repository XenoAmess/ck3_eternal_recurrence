package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;

import static org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost.*;

public final class Idler79eCompositionWitnesses {
    private Idler79eCompositionWitnesses() { }

    private static final int INITIAL_KEY = 0x79E;
    private static final int CHANGED_KEY = 0x12345678;

    private static final class Fixture {
        final Memory memory = new Memory();
        final Probe probe = new Probe();
        final long base = 0x1000L;
        final long event = memory.allocate(16);
        final long gate = base + 0x5CC1628L;
        final long rootSlot = base + 0x5C6A520L;
        final long otherSlot = base + 0x5C68C50L;
        Fixture() {
            memory.map(gate, 4);
            memory.map(rootSlot, 8);
            memory.map(otherSlot, 8);
            memory.seedInt32(event + 4, INITIAL_KEY);
            memory.seedInt32(event + 8, 1);
        }
        byte execute() { return Idler79eEvent.handle79e(base, event, memory, probe); }
    }

    private record Chain(long global, long intermediate, long header, long cells) { }

    private static Chain chain(Fixture fixture, int key, int payload, int active) {
        Memory memory = fixture.memory;
        long global = memory.allocate(0xA8);
        long intermediate = memory.allocate(8);
        long header = intermediate + 0x222E8L;
        memory.map(header, 64);
        long cells = memory.allocate(36);
        memory.seedInt64(global + 0xA0, intermediate);
        memory.seedInt64(header + 0x20, cells);
        memory.seedInt32(header + 0x2C, 1);
        memory.seedInt32(header + 0x28, active);
        memory.seedByte(cells, 1);
        memory.seedInt32(cells + 4, payload);
        memory.seedInt32(cells + 8, key);
        memory.seedByte(cells + 12, 1);
        memory.seedInt32(cells + 16, 0x55667788);
        memory.seedInt32(cells + 20, CHANGED_KEY);
        memory.seedByte(cells + 24, 1);
        return new Chain(global, intermediate, header, cells);
    }

    private static long keyReads(Fixture fixture) {
        return fixture.memory.trace().stream()
                .filter(access -> access.op() == Op.READ32 && access.address() == fixture.event + 4).count();
    }

    public static void witness1() {
        Memory memory = new Memory();
        Probe probe = new Probe();
        long event = memory.allocate(16);
        memory.seedInt32(event + 8, Integer.MIN_VALUE);
        equal(1, Idler79eEvent.handle79e(0x1000L, event, memory, probe), "first gate normal AL one");
        same(List.of(new Access(Op.READ32, event + 8, 4, Integer.MIN_VALUE)), memory.trace(),
                "only first DWORD gate; no event ID/key/global read");
        check(probe.calls383e320().isEmpty() && probe.calls28eed20().isEmpty(), "first gate has no ports");
    }

    public static void witness2() {
        Memory memory = new Memory();
        Probe probe = new Probe();
        long base = 0x1000L;
        long event = memory.allocate(16);
        long gate = base + 0x5CC1628L;
        memory.map(gate, 4);
        memory.seedInt32(event + 8, 1);
        memory.seedInt32(gate, -1);
        equal(1, Idler79eEvent.handle79e(base, event, memory, probe), "second gate normal AL one");
        same(List.of(new Access(Op.READ32, event + 8, 4, 1),
                new Access(Op.READ32, gate, 4, -1)), memory.trace(), "two gate DWORDs in source order");
        check(probe.calls383e320().isEmpty() && probe.calls28eed20().isEmpty(), "second gate has no ports");
    }

    public static void witness3() {
        Fixture fixture = new Fixture();
        Memory memory = fixture.memory;
        long root = memory.allocate(64);
        memory.seedInt64(fixture.rootSlot, root);
        memory.seedByte(root + 0x20, 3);
        memory.seedInt32(root + 0x24, INITIAL_KEY + 1);
        memory.seedByte(root + 20, 0);
        memory.seedInt32(root + 24, INITIAL_KEY);
        Chain chain = chain(fixture, INITIAL_KEY, 0x11223344, 0);
        memory.seedInt64(fixture.otherSlot, chain.global());
        memory.onAccess((m, access) -> {
            if (access.op() == Op.READ32 && access.address() == fixture.event + 4) {
                m.seedInt32(fixture.event + 4, CHANGED_KEY);
            }
        });

        equal(1, fixture.execute(), "key-mismatch skip normal AL one");
        check(fixture.probe.calls383e320().isEmpty(), "hex root key mismatch skips opaque port");
        equal(CHANGED_KEY, memory.peekInt32(fixture.event + 4), "key changed after capture");
        equal(1, keyReads(fixture), "no extra key reload when opaque call is skipped");
        same(List.of(new Call28(chain.header(), 1, 0x11223344)), fixture.probe.calls28eed20(), "scan still uses captured initial key");
        same(List.of(
                new Access(Op.READ32, fixture.event + 8, 4, 1),
                new Access(Op.READ32, fixture.gate, 4, 0),
                new Access(Op.READ32, fixture.event + 4, 4, INITIAL_KEY),
                new Access(Op.READ64, fixture.rootSlot, 8, root),
                new Access(Op.READ8, root + 0x20, 1, 3),
                new Access(Op.READ32, root + 0x24, 4, INITIAL_KEY + 1)
        ), memory.trace().subList(0, 6), "actual hexadecimal root offsets precede skip");
    }

    public static void witness4() {
        Fixture fixture = new Fixture();
        Memory memory = fixture.memory;
        long root = memory.allocate(64);
        memory.seedInt64(fixture.rootSlot, root);
        memory.seedByte(root + 0x20, 1);
        memory.seedInt32(root + 0x24, INITIAL_KEY);
        Chain oldChain = chain(fixture, INITIAL_KEY, 0x10203040, 1);
        int payload = 0x9ABCDEF0;
        Chain newChain = chain(fixture, CHANGED_KEY, payload, 1);
        memory.seedInt64(fixture.otherSlot, oldChain.global());
        memory.seedInt64(newChain.global() + 0xA0, oldChain.intermediate());
        int[] flagReads = {0};
        memory.onAccess((m, access) -> {
            if (access.op() == Op.READ8 && access.address() == root + 0x20) {
                if (++flagReads[0] == 1) m.seedByte(root + 0x20, 0xFE);
            }
        });
        List<String> portOrder = new ArrayList<>();
        Idler79ePorts.Known383e320 expectedKnown = new Idler79ePorts.Known383e320(
                root, 0xFE, -1, fixture.base + 0x476C7B0L, 8, 0L, 0,
                fixture.base + 0x476C848L, INITIAL_KEY);
        int freshEventValue = 0x80000005;
        fixture.probe.on383e320(known -> {
            portOrder.add("383");
            same(expectedKnown, known, "nine actual known fields; no R9 or padding invention");
            equal(1, keyReads(fixture), "initial key captured before opaque call");
            check(memory.trace().stream().noneMatch(access -> access.address() == fixture.otherSlot),
                    "other global is not loaded before opaque callback");
            memory.seedInt32(fixture.event + 4, CHANGED_KEY);
            memory.seedInt32(fixture.event + 8, freshEventValue);
            memory.seedInt64(fixture.otherSlot, newChain.global());
            memory.seedInt64(newChain.global() + 0xA0, newChain.intermediate());
        });
        fixture.probe.on28eed20(call -> {
            portOrder.add("28");
            equal(0, memory.peekUnsignedByte(newChain.cells()), "occupied selected cell cleared before tail");
            equal(0, memory.peekInt32(newChain.header() + 0x28), "primitive DEC completed before tail");
            equal(1, memory.peekUnsignedByte(oldChain.cells()), "old global cells untouched");
            equal(1, memory.peekInt32(oldChain.header() + 0x28), "old global count untouched");
        });

        equal(1, fixture.execute(), "enabled opaque callback normal AL one");
        equal(2, flagReads[0], "fresh flag is a distinct source read");
        equal(2, keyReads(fixture), "normal opaque return causes one fresh key read");
        same(List.of(expectedKnown), fixture.probe.calls383e320(), "one enabled opaque projection");
        same(List.of(new Call28(newChain.header(), freshEventValue, payload)), fixture.probe.calls28eed20(),
                "fresh key/global/A0 and event data feed exact tail");
        same(List.of("383", "28"), portOrder, "opaque callback precedes clear tail");
        equal(1, memory.peekUnsignedByte(newChain.cells() + 12), "clear terminates after fresh zero count");
        same(List.of(
                new Access(Op.READ32, fixture.event + 8, 4, 1),
                new Access(Op.READ32, fixture.gate, 4, 0),
                new Access(Op.READ32, fixture.event + 4, 4, INITIAL_KEY),
                new Access(Op.READ64, fixture.rootSlot, 8, root),
                new Access(Op.READ8, root + 0x20, 1, 1),
                new Access(Op.READ32, root + 0x24, 4, INITIAL_KEY),
                new Access(Op.READ8, root + 0x20, 1, 0xFE),
                new Access(Op.READ32, fixture.event + 4, 4, CHANGED_KEY),
                new Access(Op.READ64, fixture.otherSlot, 8, newChain.global()),
                new Access(Op.READ64, newChain.global() + 0xA0, 8, newChain.intermediate()),
                new Access(Op.READ64, newChain.header() + 0x20, 8, newChain.cells()),
                new Access(Op.READ8, newChain.cells(), 1, 1),
                new Access(Op.READ8, newChain.header() + 0x30, 1, 0),
                new Access(Op.READ32, newChain.header() + 0x2C, 4, 1),
                new Access(Op.READ32, newChain.cells() + 8, 4, CHANGED_KEY),
                new Access(Op.READ32, newChain.cells() + 4, 4, payload),
                new Access(Op.READ32, newChain.header() + 0x28, 4, 1),
                new Access(Op.READ8, newChain.cells(), 1, 1),
                new Access(Op.WRITE8, newChain.cells(), 1, 0),
                new Access(Op.DEC32, newChain.header() + 0x28, 4, 0),
                new Access(Op.READ32, newChain.header() + 0x28, 4, 0),
                new Access(Op.READ32, fixture.event + 8, 4, freshEventValue)
        ), memory.trace(), "source memory order around opaque callback and clear composition");
    }

    public static void witness5() {
        Fixture missing = new Fixture();
        expectThrows(IllegalArgumentException.class, missing::execute);
        same(List.of(
                new Access(Op.READ32, missing.event + 8, 4, 1),
                new Access(Op.READ32, missing.gate, 4, 0),
                new Access(Op.READ32, missing.event + 4, 4, INITIAL_KEY),
                new Access(Op.READ64, missing.rootSlot, 8, 0),
                new Access(Op.READ64, missing.otherSlot, 8, 0)
        ), missing.memory.trace(), "zero other global still attempts unmapped A0 instead of null guard");
        check(missing.probe.calls383e320().isEmpty() && missing.probe.calls28eed20().isEmpty(), "unmapped A0 has no tail");

        Fixture exceptional = new Fixture();
        long root = exceptional.memory.allocate(64);
        exceptional.memory.seedInt64(exceptional.rootSlot, root);
        exceptional.memory.seedByte(root + 0x20, 1);
        exceptional.memory.seedInt32(root + 0x24, INITIAL_KEY);
        IllegalStateException failure = new IllegalStateException("controlled opaque callback");
        exceptional.probe.on383e320(known -> { throw failure; });
        IllegalStateException actual = expectThrows(IllegalStateException.class, exceptional::execute);
        check(actual == failure, "opaque callback exception is propagated unchanged");
        equal(1, exceptional.probe.calls383e320().size(), "projection is captured before throwing callback");
        check(exceptional.probe.calls28eed20().isEmpty(), "exception prevents tail");
        equal(1, keyReads(exceptional), "exception prevents fresh key reload");
        check(exceptional.memory.trace().stream().noneMatch(access -> access.address() == exceptional.otherSlot),
                "exception prevents global load");
    }

    public static void run() {
        test("eventFirstGate", Idler79eCompositionWitnesses::witness1);
        test("eventSecondGate", Idler79eCompositionWitnesses::witness2);
        test("eventSkippedCallKeepsCapturedKey", Idler79eCompositionWitnesses::witness3);
        test("eventOpaqueMutationThenFreshComposition", Idler79eCompositionWitnesses::witness4);
        test("eventUnguardedAndExceptionalBoundaries", Idler79eCompositionWitnesses::witness5);
    }
}
