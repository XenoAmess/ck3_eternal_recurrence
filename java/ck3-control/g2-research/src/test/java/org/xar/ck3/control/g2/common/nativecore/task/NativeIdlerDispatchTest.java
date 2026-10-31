package org.xar.ck3.control.g2.common.nativecore.task;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class NativeIdlerDispatchTest {

    private static final long PAGE_BYTES = 4096L;
    private static final int MAX_VIRTUAL_CALLS = 16;
    private static final long TERMINAL_RVA = 0x42207F8L;
    private static final long A_SENTINEL = 0x1122334455667788L;
    private static final long B_SENTINEL = 0x66778899AABBCCDDL;

    private static final class ControlledTerminal extends RuntimeException {
        private static final long serialVersionUID = 1L;
    }

    private record Write(long address, int bytes, long value) { }
    private record OnCall(long expectedReceiver, List<Write> writes) { }
    private record Layout(long holder, long event, long entryA, long entryB,
                         long listA, long negativeCell, long receiverA, long receiverB) { }
    private record Plan(String name, List<Write> seed, int lookupResult,
                       List<Write> onLookup, List<OnCall> onVirtual,
                       List<Long> expectedReceivers, int expectedLookupKey,
                       boolean expectedTerminal, List<Write> expectedFinal) { }

    private static final class OwnedMemory implements NativeTaskMemory {
        private final List<Region> regions = new ArrayList<>();
        private record Region(long address, byte[] data) { }

        OwnedMemory(Layout layout) {
            allocate(layout.holder(), 0x48);
            allocate(layout.event(), 0x20);
            allocate(layout.entryA(), 0x48);
            allocate(layout.entryB(), 0x48);
            allocate(layout.listA(), 0x90);
            allocate(0x9000L, 0x90);
            allocate(layout.negativeCell(), 8);
            allocate(layout.receiverA(), 8);
            allocate(layout.receiverB(), 8);
        }

        private void allocate(long address, int bytes) {
            regions.add(new Region(address, new byte[bytes]));
        }

        private Region region(long address, int bytes) {
            for (Region r : regions) {
                long offset = address - r.address();
                if (offset >= 0L && bytes >= 0 && bytes <= r.data().length
                        && offset <= r.data().length - bytes) {
                    return r;
                }
            }
            throw new IllegalArgumentException("Outside owned memory: "
                    + Long.toHexString(address) + " width=" + bytes);
        }

        public long readPointer(long address) {
            Region r = region(address, 8);
            int offset = (int) (address - r.address());
            long value = 0L;
            for (int i = 0; i < 8; i++) {
                value |= (long) (r.data()[offset + i] & 0xFF) << (8 * i);
            }
            return value;
        }

        public int readInt32(long address) {
            Region r = region(address, 4);
            int offset = (int) (address - r.address());
            int value = 0;
            for (int i = 0; i < 4; i++) {
                value |= (r.data()[offset + i] & 0xFF) << (8 * i);
            }
            return value;
        }

        public void writeInt32(long address, int value) {
            Region r = region(address, 4);
            int offset = (int) (address - r.address());
            for (int i = 0; i < 4; i++) {
                r.data()[offset + i] = (byte) (value >>> (8 * i));
            }
        }

        public void writeInt64(long address, long value) {
            Region r = region(address, 8);
            int offset = (int) (address - r.address());
            for (int i = 0; i < 8; i++) {
                r.data()[offset + i] = (byte) (value >>> (8 * i));
            }
        }

        void apply(List<Write> writes) {
            for (Write write : writes) {
                if (write.bytes() == 1) {
                    Region r = region(write.address(), 1);
                    r.data()[(int) (write.address() - r.address())] = (byte) write.value();
                } else if (write.bytes() == 4) {
                    writeInt32(write.address(), (int) write.value());
                } else if (write.bytes() == 8) {
                    writeInt64(write.address(), write.value());
                } else {
                    throw new IllegalArgumentException("Unsupported write width " + write.bytes());
                }
            }
        }

        long bits(Write field) {
            if (field.bytes() == 1) {
                Region r = region(field.address(), 1);
                return Byte.toUnsignedInt(r.data()[(int) (field.address() - r.address())]);
            }
            if (field.bytes() == 4) {
                return Integer.toUnsignedLong(readInt32(field.address()));
            }
            return readPointer(field.address());
        }
    }

    private static final class Scenario implements NativeIdlerDispatch.Calls {
        private final OwnedMemory memory;
        private final Layout layout;
        private final Plan plan;
        private final ControlledTerminal terminalException = new ControlledTerminal();
        private final List<Write> trace = new ArrayList<>();
        private int virtualCount = 0;
        private int lookupCount = 0;
        private int terminalCount = 0;
        private boolean terminal = false;
        private Throwable firstFailure = null;
        private int checks = 0;

        Scenario(OwnedMemory memory, Layout layout, Plan plan) {
            this.memory = memory;
            this.layout = layout;
            this.plan = plan;
        }

        void prepare() {
            firstFailure = null;
            virtualCount = 0;
            lookupCount = 0;
            terminalCount = 0;
            terminal = false;
            trace.clear();
            checks = 0;
        }

        private void note(boolean condition, String message) {
            checks++;
            if (!condition && firstFailure == null) {
                firstFailure = new AssertionError(plan.name() + ": " + message);
            }
        }

        private void check(boolean condition, String message) {
            checks++;
            if (!condition) {
                throw new AssertionError(plan.name() + ": " + message);
            }
        }

        private void remember(Throwable failure) {
            if (firstFailure == null) {
                firstFailure = failure;
            }
        }

        public void virtualSlot10(long receiver, long eventAddress) {
            int index = virtualCount++;
            trace.add(new Write(receiver, 8, eventAddress));
            note(eventAddress == layout.event(), "virtual event address");
            if (virtualCount > MAX_VIRTUAL_CALLS || index >= plan.onVirtual().size()) {
                throw new AssertionError(plan.name() + ": unexpected or excessive virtual callback");
            }
            OnCall onCall = plan.onVirtual().get(index);
            note(receiver == onCall.expectedReceiver(), "ordered virtual receiver " + index);
            memory.apply(onCall.writes());
        }

        public int findEventBucket(long registryAddress, int copiedEventType) {
            lookupCount++;
            note(lookupCount == 1, "one lookup");
            note(registryAddress == layout.holder() + 0x30L, "lookup registry field address");
            note(copiedEventType == plan.expectedLookupKey(), "copied DWORD lookup key");
            int result = firstFailure == null ? plan.lookupResult() : -1;
            trace.add(new Write(registryAddress, 4, copiedEventType));
            if (firstFailure == null) {
                memory.apply(plan.onLookup());
            }
            return result;
        }

        public void onNullListener(long nativeCallTargetRva) {
            terminalCount++;
            terminal = true;
            trace.add(new Write(nativeCallTargetRva, 8, 0L));
            note(nativeCallTargetRva == TERMINAL_RVA, "known terminal call target");
            note(terminalCount == 1, "one controlled terminal");
            throw terminalException;
        }

        void verifyRun() {
            if (firstFailure != null) {
                throw new AssertionError(plan.name() + ": callback failure", firstFailure);
            }
            check(lookupCount == 1, "one completed lookup");
            check(virtualCount == plan.expectedReceivers().size(), "expected virtual count");
            check(terminal == plan.expectedTerminal(), "controlled terminal flag");
            check(terminalCount == (plan.expectedTerminal() ? 1 : 0), "terminal callback count");
        }
    }

    private static Write w(long address, int bytes, long value) {
        return new Write(address, bytes, value);
    }

    private static OnCall on(long receiver, Write... writes) {
        return new OnCall(receiver, Arrays.asList(writes));
    }

    private static List<Write> commonSeed(Layout l, long listB) {
        return List.of(
            w(l.holder() + 8L, 8, 0L),
            w(l.holder() + 0x10L, 8, 0L),
            w(l.holder() + 0x30L, 8, l.entryA()),
            w(l.event(), 4, 0x6EB),
            w(l.entryA() + 0x28L, 8, l.listA()),
            w(l.entryA() + 0x34L, 4, 0L),
            w(l.entryB() + 0x28L, 8, listB),
            w(l.entryB() + 0x34L, 4, 0L),
            w(l.entryA() + 0x40L, 8, A_SENTINEL),
            w(l.entryB() + 0x40L, 8, B_SENTINEL),
            w(l.listA() + 0x40L, 8, l.receiverA()),
            w(l.listA() + 0x88L, 8, l.receiverB()),
            w(listB + 0x40L, 8, l.receiverA()),
            w(listB + 0x88L, 8, l.receiverA())
        );
    }

    private static List<Write> seeded(Layout l, long listB, Write... changes) {
        List<Write> seed = new ArrayList<>(commonSeed(l, listB));
        seed.addAll(Arrays.asList(changes));
        return seed;
    }

    private static Plan forwardsPlan(Layout l, long listB) {
        return new Plan("fresh-forward-and-event",
            seeded(l, listB, w(l.holder() + 8L, 8, l.receiverA()),
                    w(l.holder() + 0x10L, 8, l.receiverA()), w(l.event(), 4, 0x601)),
            -7, List.of(),
            List.of(on(l.receiverA(), w(l.holder() + 0x10L, 8, l.receiverB()),
                            w(l.event(), 4, 0x6EB)), on(l.receiverB())),
            List.of(l.receiverA(), l.receiverB()), 0x6EB, false,
            List.of(w(l.holder() + 0x10L, 8, l.receiverB()), w(l.event(), 4, 0x6EB),
                    w(l.holder() + 0x30L, 8, l.entryA()),
                    w(l.entryA() + 0x40L, 8, A_SENTINEL)));
    }

    private static Plan freshListsPlan(Layout l, long listB) {
        return new Plan("held-entry-fresh-list",
            seeded(l, listB, w(l.entryA() + 0x34L, 4, 7),
                    w(l.entryB() + 0x34L, 4, 2)),
            0, List.of(w(l.holder() + 0x30L, 8, l.entryB())),
            List.of(on(l.receiverA(), w(l.holder() + 0x30L, 8, l.entryA()),
                            w(l.entryB() + 0x28L, 8, l.listA())), on(l.receiverB())),
            List.of(l.receiverA(), l.receiverB()), 0x6EB, false,
            List.of(w(l.entryA() + 0x40L, 8, A_SENTINEL),
                    w(l.entryB() + 0x40L, 8, 0L),
                    w(l.holder() + 0x30L, 8, l.entryA()),
                    w(l.entryB() + 0x28L, 8, l.listA()),
                    w(l.entryA() + 0x34L, 4, 7), w(l.entryB() + 0x34L, 4, 2)));
    }

    private static Plan zeroCountPlan(Layout l, long listB) {
        return new Plan("zero-count",
            seeded(l, listB, w(l.entryA() + 0x34L, 4, 0)), 0, List.of(), List.of(),
            List.of(), 0x6EB, false,
            List.of(w(l.entryA() + 0x40L, 8, 0L),
                    w(l.entryA() + 0x34L, 4, 0),
                    w(l.entryB() + 0x40L, 8, B_SENTINEL)));
    }

    private static Plan negativeCountPlan(Layout l, long listB) {
        return new Plan("negative-count",
            seeded(l, listB, w(l.entryA() + 0x34L, 4, -7)), 0, List.of(), List.of(),
            List.of(), 0x6EB, false,
            List.of(w(l.entryA() + 0x40L, 8, 0L),
                    w(l.entryA() + 0x34L, 4, -7),
                    w(l.entryB() + 0x40L, 8, B_SENTINEL)));
    }

    private static Plan signedWrapPlan(Layout l) {
        long holder = l.holder();
        long event = l.event();
        long entryA = l.entryA();
        long entryB = l.entryB();
        long listA = l.listA();
        long negativeCell = l.negativeCell();
        long receiverA = l.receiverA();
        long receiverB = l.receiverB();

        List<Write> seed = List.of(
            new Write(holder + 8, 8, 0L),
            new Write(holder + 0x10, 8, 0L),
            new Write(holder + 0x30, 8, entryA),
            new Write(event, 4, 0x6EB),
            new Write(entryA + 0x34, 4, 2),
            new Write(entryA + 0x28, 8, listA),
            new Write(entryA + 0x40, 8, 0x1111111111111111L),
            new Write(entryB + 0x40, 8, 0x2222222222222222L),
            new Write(listA + 0x40, 8, receiverA),
            new Write(negativeCell, 8, receiverB)
        );

        int lookupResult = 0;
        List<Write> onLookup = List.of();

        long cursorMax = (long) Integer.MAX_VALUE;
        long limitMinPlus1 = (long) Integer.MIN_VALUE + 1;
        long nextCursor = (long) Integer.MIN_VALUE;
        long anchor = negativeCell - 72L * nextCursor - 0x40L;

        List<Write> firstCallbackWrites = List.of(
            new Write(holder + 0x30, 8, entryB),
            new Write(entryA + 0x40, 4, Integer.MAX_VALUE),
            new Write(entryA + 0x44, 4, Integer.MIN_VALUE + 1),
            new Write(entryA + 0x28, 8, anchor)
        );

        List<Write> secondCallbackWrites = List.of();

        List<OnCall> onVirtual = List.of(
            new OnCall(receiverA, firstCallbackWrites),
            new OnCall(receiverB, secondCallbackWrites)
        );

        List<Long> expectedReceivers = List.of(receiverA, receiverB);
        int expectedLookupKey = 0x6EB;
        boolean expectedTerminal = false;

        List<Write> expectedFinal = List.of(
            new Write(entryA + 0x40, 8, 0L),
            new Write(entryB + 0x40, 8, 0x2222222222222222L),
            new Write(holder + 0x30, 8, entryB),
            new Write(entryA + 0x28, 8, anchor),
            new Write(entryA + 0x34, 4, 2),
            new Write(negativeCell, 8, receiverB)
        );

        return new Plan(
            "signedWrapWitness",
            seed,
            lookupResult,
            onLookup,
            onVirtual,
            expectedReceivers,
            expectedLookupKey,
            expectedTerminal,
            expectedFinal
        );
    }

    private static Plan nullListenerPlan(Layout l, long listB) {
        return new Plan("controlled-null-terminal",
            seeded(l, listB, w(l.entryA() + 0x34L, 4, 1),
                    w(l.listA() + 0x40L, 8, 0L)), 0, List.of(), List.of(), List.of(),
            0x6EB, true,
            List.of(w(l.entryA() + 0x40L, 4, 0),
                    w(l.entryA() + 0x44L, 4, 1),
                    w(l.entryA() + 0x34L, 4, 1),
                    w(l.entryB() + 0x40L, 8, B_SENTINEL)));
    }

    private static Layout makeLayout() {
        long holder = 0x1000L;
        long event = 0x2000L;
        long entryA = 0x3000L;
        long entryB = 0x4000L;
        long listA = 0x5000L;
        long negativeCell = 0x6000L;
        long receiverA = 0x7000L;
        long receiverB = 0x8000L;
        return new Layout(holder, event, entryA, entryB, listA, negativeCell, receiverA, receiverB);
    }

    @Test
    public void testForwards() {
        Layout l = makeLayout();
        long listB = 0x9000L;
        Plan plan = forwardsPlan(l, listB);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            Assertions.fail("Unexpected terminal");
        }
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }

    @Test
    public void testFreshLists() {
        Layout l = makeLayout();
        long listB = 0x9000L;
        Plan plan = freshListsPlan(l, listB);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            Assertions.fail("Unexpected terminal");
        }
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }

    @Test
    public void testZeroCount() {
        Layout l = makeLayout();
        long listB = 0x9000L;
        Plan plan = zeroCountPlan(l, listB);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            Assertions.fail("Unexpected terminal");
        }
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }

    @Test
    public void testNegativeCount() {
        Layout l = makeLayout();
        long listB = 0x9000L;
        Plan plan = negativeCountPlan(l, listB);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            Assertions.fail("Unexpected terminal");
        }
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }

    @Test
    public void testSignedWrap() {
        Layout l = makeLayout();
        Plan plan = signedWrapPlan(l);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            Assertions.fail("Unexpected terminal");
        }
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }

    @Test
    public void testNullListener() {
        Layout l = makeLayout();
        long listB = 0x9000L;
        Plan plan = nullListenerPlan(l, listB);
        OwnedMemory memory = new OwnedMemory(l);
        memory.apply(plan.seed());
        Scenario scenario = new Scenario(memory, l, plan);
        ControlledTerminal caught = null;
        try {
            NativeIdlerDispatch.dispatch(l.holder(), l.event(), memory, scenario);
        } catch (ControlledTerminal e) {
            caught = e;
        }
        Assertions.assertSame(scenario.terminalException, caught, "Exact public callback exception");
        scenario.verifyRun();
        for (Write field : plan.expectedFinal()) {
            long mask = field.bytes() == 1 ? 0xFFL : field.bytes() == 4 ? 0xFFFFFFFFL : -1L;
            Assertions.assertEquals(field.value() & mask, memory.bits(field),
                "expected field " + Long.toHexString(field.address()) + " width=" + field.bytes());
        }
    }
}
