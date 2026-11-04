package org.xar.ck3.study.m6.activity266test;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.Access;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.Fixture;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.MemoryEvent;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.NormalExpectation;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.RamLiteral;
import org.xar.ck3.study.m6.activity264literal.ActivityEntry264LiteralData.StoppedExpectation;
import org.xar.ck3.study.m6.activityprotocol264.ActivityCallProtocol264Api;
import org.xar.ck3.study.m6.activity266.ActivityEntry266;

/**
 * Independent finite behavioral test source, using the previously frozen public literal data.
 * SOURCE ONLY: no Java compile, JVM execution, producer behavior or native acceptance is claimed.
 * The main adapter uses the whole owner's supplied actual public constructor with OPAQUE.
 * The memory port observes operation/order/address/width/value; expected source PCs are diagnostics,
 * not an invented instruction-PC observation channel. No target algorithm is implemented here.
 */
public final class ActivityEntry266IndependentTest {
    private ActivityEntry266IndependentTest() { }

    /** Actual public port used by the whole-producer constructor adapter below. */
    public static final ScriptedOpaque OPAQUE = new ScriptedOpaque();

    /** Actual public constructor supplied by the whole-entry owner; still source-only here. */
    public static void main(String[] args) {
        ActivityEntry266 actual = new ActivityEntry266(OPAQUE,
                () -> { throw new AssertionError("GS:[58] is not reached by these three fixtures"); },
                target -> { throw new AssertionError("Unexpected taken backedge target "
                        + Long.toUnsignedString(target, 16)); });
        runThree(actual);
        System.out.println("Three actual whole-entry fixture checks passed.");
    }

    /**
     * Execute all three frozen scenes against one actual whole executor. The actual public main
     * adapter configures the whole producer with OPAQUE; supplied executors must use that same port.
     * Normal equality checks all represented V/N/RIP/RSP/DF/partial-MX fields through record equality.
     * This finite runner is serialized; expected values are never obtained from producer outputs.
     */
    public static void runThree(PostState240Api.EntryExecutor actual) {
        Objects.requireNonNull(actual, "actual whole executor");
        synchronized (OPAQUE) {
            for (Fixture fixture : ActivityEntry264LiteralData.ALL) {
                TraceMemory memory = new TraceMemory(fixture);
                OPAQUE.select(fixture, memory);
                try {
                    QueueFp604Api.Outcome outcome = actual.execute(fixture.input(), memory);
                    memory.requireComplete();
                    if (fixture.expected() instanceof NormalExpectation expected) {
                        requireEqual(expected.value(), outcome, fixture.caseId() + " complete Normal");
                        OPAQUE.requireCallCount(0);
                    } else {
                        StoppedExpectation expected = (StoppedExpectation) fixture.expected();
                        require(expected.requireSameReference(), "fixture must require Stopped identity");
                        require(expected.noNormalReturn() && expected.noParentEpilogue()
                                && expected.noParentStateReplacement(), "fixture stop boundary");
                        require(outcome == expected.offered(),
                                fixture.caseId() + " must return the exact supplied Stopped object");
                        OPAQUE.requireCallCount(1);
                    }
                } finally {
                    OPAQUE.clear();
                }
            }
        }
    }

    /**
     * Artificial full-Outcome callback. It checks the actual CALL frame then returns the one
     * frozen fixture Stopped object. No opaque callee execution, post-state or native fault is made up.
     */
    public static final class ScriptedOpaque implements ActivityCallProtocol264Api.FullOutcomePort {
        private Fixture fixture;
        private TraceMemory memory;
        private int calls;

        private void select(Fixture selected, TraceMemory selectedMemory) {
            require(fixture == null && memory == null, "opaque script already active");
            fixture = selected;
            memory = selectedMemory;
            calls = 0;
        }

        private void clear() {
            fixture = null;
            memory = null;
            calls = 0;
        }

        private void requireCallCount(int expected) {
            require(calls == expected, fixture.caseId() + " opaque CALL count " + calls
                    + ", expected " + expected);
        }

        @Override
        public QueueFp604Api.Outcome invoke(ActivityCallProtocol264Api.Frame frame) {
            require(fixture != null && memory != null, "opaque callback outside runThree");
            require(fixture.expected() instanceof StoppedExpectation,
                    fixture.caseId() + " unexpected opaque CALL");
            require(calls == 0, fixture.caseId() + " repeated opaque CALL");
            Objects.requireNonNull(frame, "actual CALL frame");
            StoppedExpectation expected = (StoppedExpectation) fixture.expected();
            var call = expected.call();
            var source = frame.source();

            require(source.callSiteRva() == 0x23fc9dcL, "first actual CALL site");
            requireEqual("e87fa7b501", source.instructionBytes(), "actual CALL bytes");
            require(source.instructionLength() == 5, "actual CALL length");
            require(source.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    "actual direct CALL kind");
            requireEqual(Long.valueOf(0x3f57160L), source.directTargetRva(), "actual direct target");
            require(source.continuationRva() == 0x23fc9e1L, "actual source continuation");
            requireEqual(call.beforePush(), frame.call(), "full pre-push V/N/SP CALL");
            requireEqual(call.childInputAfterPush(), frame.childInput(),
                    "full child Entry/DF/partial-MX/source-origin");
            require(frame.returnRipBits() == call.returnRipBits(), "actual pushed return RIP");
            require(frame.memory() == memory, "shared RAM identity");

            var expectedBefore = new PostState240Api.Input(
                    new GovernmentCrtBoundary185Api.Entry(
                            call.childInputAfterPush().entry().imageBaseBits(),
                            call.beforePush().rspBits(), call.beforePush().volatileBits(),
                            call.beforePush().nonvolatileBits()),
                    call.preDirectionFlagSet(), call.preMxcsr(),
                    fixture.input().originCallSiteRva());
            requireEqual(expectedBefore, frame.before(), "actual parent pre-push input");
            require(frame.childInput().originCallSiteRva() == source.callSiteRva(),
                    "child source-origin must be the actual source CALL");
            memory.requireComplete(); // Includes the one architectural CALL return-slot write.
            calls++;
            return expected.offered(); // Return this object itself; do not construct another snapshot.
        }
    }

    /**
     * Owned sparse RAM with strict exact-once port trace. Loading fixture bytes is not a source event.
     * Byte storage makes overlapping saves/object/tag reads observe source-order writes naturally.
     */
    private static final class TraceMemory implements GovernmentCrtBoundary185Api.Memory {
        private final Fixture fixture;
        private final Map<Long, Integer> bytes = new HashMap<>();
        private int eventIndex;

        private TraceMemory(Fixture fixture) {
            this.fixture = Objects.requireNonNull(fixture);
            for (RamLiteral literal : fixture.initialRam()) {
                requireWidth(literal.widthBytes());
                store(literal.addressBits(), literal.widthBytes(), literal.valueBits());
            }
        }

        private static void requireWidth(int width) {
            require(width == 1 || width == 4 || width == 8, "unexpected fixture width " + width);
        }

        private static long lowBits(long value, int width) {
            return width == 8 ? value : value & ((1L << (width * 8)) - 1L);
        }

        private void store(long address, int width, long value) {
            for (int index = 0; index < width; index++) {
                bytes.put(address + index, (int) ((value >>> (8 * index)) & 0xffL));
            }
        }

        private long load(long address, int width) {
            long result = 0;
            for (int index = 0; index < width; index++) {
                Integer value = bytes.get(address + index);
                require(value != null, fixture.caseId() + " absent RAM byte at "
                        + Long.toUnsignedString(address + index, 16));
                result |= ((long) value) << (8 * index);
            }
            return result;
        }

        private MemoryEvent next(Access operation, int width, long address) {
            requireWidth(width);
            require(eventIndex < fixture.events().size(), fixture.caseId() + " extra RAM event");
            MemoryEvent expected = fixture.events().get(eventIndex);
            String where = fixture.caseId() + " event " + eventIndex + " sourcePC "
                    + Long.toUnsignedString(expected.instructionRva(), 16);
            require(expected.operation() == operation, where + " operation");
            require(expected.widthBytes() == width, where + " byte width");
            require(expected.addressBits() == address, where + " address");
            return expected;
        }

        private long read(int width, long address) {
            MemoryEvent expected = next(Access.READ, width, address);
            long actual = load(address, width);
            require(actual == lowBits(expected.valueBits(), width),
                    fixture.caseId() + " read bits at event " + eventIndex);
            eventIndex++;
            return actual;
        }

        private void write(int width, long address, long value) {
            MemoryEvent expected = next(Access.WRITE, width, address);
            require(lowBits(value, width) == lowBits(expected.valueBits(), width),
                    fixture.caseId() + " write bits at event " + eventIndex);
            store(address, width, value);
            eventIndex++;
        }

        private void requireComplete() {
            require(eventIndex == fixture.events().size(), fixture.caseId() + " missing RAM events: "
                    + eventIndex + "/" + fixture.events().size());
        }

        @Override public int readDword(long address) { return (int) read(4, address); }
        @Override public long readQword(long address) { return read(8, address); }
        @Override public int readUnsignedByte(long address) { return (int) read(1, address); }
        @Override public void writeDword(long address, int value) {
            write(4, address, Integer.toUnsignedLong(value));
        }
        @Override public void writeQword(long address, long value) { write(8, address, value); }
        @Override public void writeByte(long address, int value) { write(1, address, value & 0xffL); }
        @Override public int lockedXaddDword(long address, int addend) {
            throw new AssertionError(fixture.caseId() + " unexpected locked XADD");
        }
        @Override public Bits128 read128(long address) {
            throw new AssertionError(fixture.caseId() + " unexpected read128");
        }
        @Override public void write128(long address, Bits128 value) {
            throw new AssertionError(fixture.caseId() + " unexpected write128");
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void requireEqual(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(message + ": expected " + expected + ", actual " + actual);
        }
    }
}
