package org.xar.ck3.study.m6.oracle251;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.study.m6.postfree251.FreePostState251;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import static org.xar.ck3.study.m6.oracle251.FreePostState251QualificationData.*;

/**
 * Four necessary source-scoped synthetic-carrier cases against the actual 251 entry.
 * Authored source-only; later software validation is recorded separately. No native or FP arithmetic claim.
 * Expectations precede the API read; see the frozen oracle, annex, and API mapping.
 */
public final class FreePostState251LiteralTest {
    private FreePostState251LiteralTest() { }

    private static final long ARTIFICIAL_OUTER_ORIGIN = 0xF25100L;
    private static final List<String> FOUR_CALL_TRACE = List.of(
            event("W32", S + 0x10L, 0L), event("R32", S + 0x10L),
            event("W64", S - 8L, ENTRY_N.rbxBits()),
            event("R64", I + 0x5C5DE30L), event("R64", I + 0x43DA748L),
            event("W64", C, I + 0x424E380L), event("CHILD", 0x424E37AL),
            event("SUP64", S - 8L, SCRIPT_SAVED_RBX), event("SUP64", S, SCRIPT_OUTER_RET),
            event("W64", C, I + 0x424E389L), event("CHILD", 0x424E384L),
            event("R64", I + 0x43DA738L),
            event("W64", C, I + 0x424E392L), event("CHILD", 0x424E38CL),
            event("W64", C, I + 0x424E399L), event("CHILD", 0x424E394L),
            event("W32", DESTINATION, 0x89ABCDEFL),
            event("R64", S - 8L), event("R64", S));
    private static final List<String> ZERO_CALL_TRACE = List.of(
            event("W32", S + 0x10L, 0L), event("R32", S + 0x10L), event("R64", S));

    public static void main(String[] args) {
        zeroCallRetainsExplicitPartialEnvironment();
        fourCallsPropagateActualPostEnvironmentWithoutReplay();
        firstStopKeepsCurrentChildAndAlreadyPushedPrefix();
        secondStopSkipsRbxAssignmentAndActualOuterRet();
    }

    public static void zeroCallRetainsExplicitPartialEnvironment() {
        Ram ram = new Ram(ZERO_CALL.initialQwords());
        FreePostState251 entry = new FreePostState251((frame, sameMemory) -> {
            throw new AssertionError("Null path reached an opaque child");
        });
        QueueFp604Api.Outcome result = entry.execute(input(ZERO_CALL), ram);
        equal(ZERO_CALL.expectedNormal(), result, "Q0 complete normal/environment");
        equal(ZERO_CALL_TRACE, ram.events, "Q0 no owned CALL or saved-RBX effect");
        ram.expectQwords(ZERO_CALL.expectedFinalQwords());
    }

    public static void fourCallsPropagateActualPostEnvironmentWithoutReplay() {
        Ram ram = new Ram(FOUR_CALL.initialQwords());
        SuppliedChildren children = new SuppliedChildren(ram, -1);
        QueueFp604Api.Outcome result = new FreePostState251(children).execute(input(FOUR_CALL), ram);
        equal(FOUR_CALL.expectedNormal(), result, "Q1 complete V/N/RET/SP/DF/MXCSR");
        equal(4, children.invocations, "Q1 exactly four opaque effects");
        equal(FOUR_CALL_TRACE, ram.events, "Q1 one owned push each, no bridge RET read/replay");
        ram.expectQwords(FOUR_CALL.expectedFinalQwords());
    }

    public static void firstStopKeepsCurrentChildAndAlreadyPushedPrefix() {
        runStop(FIRST_STOP, 0, FOUR_CALL_TRACE.subList(0, 7));
    }

    public static void secondStopSkipsRbxAssignmentAndActualOuterRet() {
        runStop(SECOND_STOP, 1, FOUR_CALL_TRACE.subList(0, 11));
    }

    private static void runStop(StopPrefix expected, int stoppedOrdinal, List<String> expectedTrace) {
        Ram ram = new Ram(INITIAL_QWORD_RAM);
        SuppliedChildren children = new SuppliedChildren(ram, stoppedOrdinal);
        QueueFp604Api.Outcome result = new FreePostState251(children).execute(input(FOUR_CALL), ram);
        if (result != expected.suppliedStopObject()) {
            throw new AssertionError(expected.name() + ": supplied child Stopped identity lost");
        }
        equal(expected.callsThroughStopped().size(), children.invocations, "stop exact call prefix");
        equal(expectedTrace, ram.events, "stop no later push/store/epilogue/RET read");
        ram.expectQwords(expected.expectedCompletedPrefixQwords());
        // Identity above retains the synthetic deeper state, explicit post environment and actual origin.
        // No ordinary exception or actual FP trap is manufactured by this test supplier.
    }

    private static PostState240Api.Input input(NormalVector vector) {
        return new PostState240Api.Input(vector.entry(), vector.inputEnvironment().df(),
                vector.inputEnvironment().mxcsr(), ARTIFICIAL_OUTER_ORIGIN);
    }

    private static final class SuppliedChildren implements FreePostState251Api.Children {
        private final Ram ram;
        private final int stoppedOrdinal;
        private int invocations;

        private SuppliedChildren(Ram ram, int stoppedOrdinal) {
            this.ram = ram;
            this.stoppedOrdinal = stoppedOrdinal;
        }

        @Override public QueueFp604Api.Outcome invoke(
                FreePostState251Api.AlreadyPushedCallFrame frame,
                GovernmentCrtBoundary185Api.Memory sameMemory) {
            int ordinal = invocations++;
            if (sameMemory != ram || ordinal >= FOUR_CALL.calls().size()) {
                throw new AssertionError("Different RAM or duplicated child effect");
            }
            CallLiteral literal = FOUR_CALL.calls().get(ordinal);
            equal(0x424E364L, frame.ownerEntryRva(), "held61 owner");
            equal(I, frame.imageBaseBits(), "image");
            equal(literal.beforeOwnedPush(), frame.call(), "complete actual source Call");
            equal(literal.afterOwnedPush(), frame.childInput().entry(), "complete actual child Entry");
            equal(literal.explicitInputEnvironment().df(), frame.childInput().directionFlagSet(),
                    "preceding child post DF consumed");
            equal(literal.explicitInputEnvironment().mxcsr(), frame.childInput().mxcsr(),
                    "preceding child post MXCSR/status knowledge consumed");
            equal(literal.beforeOwnedPush().callSiteRva(), frame.childInput().originCallSiteRva(),
                    "actual child origin, not artificial outer origin");
            equal(literal.length(), frame.instructionLength(), "literal instruction length");
            equal(literal.returnRip(), frame.returnRipBits(), "actual continuation metadata");
            equal(literal.returnRip(), ram.peekQword(C), "already owned one-slot continuation");
            ram.events.add(event("CHILD", literal.beforeOwnedPush().callSiteRva()));

            if (ordinal == stoppedOrdinal) {
                return ordinal == 0 ? FIRST_SUPPLIED_STOP : SECOND_SUPPLIED_STOP;
            }
            if (ordinal == 0) {
                // Explicit supplied data script only: these are not inferred imported side effects.
                ram.suppliedQword(S - 8L, SCRIPT_SAVED_RBX);
                ram.suppliedQword(S, SCRIPT_OUTER_RET);
            }
            return FOUR_CALL.suppliedNormals().get(ordinal);
        }
    }

    /** Strict byte RAM. Test-only peeks do not masquerade as production memory operations. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final Map<Long, Long> initialQwords;
        private final List<String> events = new ArrayList<>();

        private Ram(Map<Long, Long> initialQwords) {
            this.initialQwords = initialQwords;
            initialQwords.forEach(this::putQword);
        }

        private int requiredByte(long address) {
            Byte value = bytes.get(address);
            if (value == null) throw new AssertionError("Unheld supplied RAM byte " + hex(address));
            return value & 0xFF;
        }

        private void putByte(long address, int value) { bytes.put(address, (byte) value); }
        private void putQword(long address, long value) {
            for (int lane = 0; lane < 8; lane++) putByte(address + lane, (int) (value >>> (lane * 8)));
        }

        private long peekQword(long address) {
            long result = 0;
            for (int lane = 0; lane < 8; lane++) result |= (long) requiredByte(address + lane) << (lane * 8);
            return result;
        }

        @Override public long readQword(long address) {
            events.add(event("R64", address));
            return peekQword(address);
        }

        @Override public int readDword(long address) {
            events.add(event("R32", address));
            int result = 0;
            for (int lane = 0; lane < 4; lane++) result |= requiredByte(address + lane) << (lane * 8);
            return result;
        }

        @Override public void writeQword(long address, long value) {
            if (address != S - 8L && address != C) {
                throw new AssertionError("Unexpected production QWORD write " + hex(address));
            }
            events.add(event("W64", address, value));
            putQword(address, value);
        }

        @Override public void writeDword(long address, int value) {
            if (address != S + 0x10L && address != DESTINATION) {
                throw new AssertionError("Unexpected production DWORD write " + hex(address));
            }
            events.add(event("W32", address, Integer.toUnsignedLong(value)));
            for (int lane = 0; lane < 4; lane++) putByte(address + lane, value >>> (lane * 8));
        }

        private void suppliedQword(long address, long value) {
            if (address != S - 8L && address != S) throw new AssertionError("Undeclared supplier RAM write");
            events.add(event("SUP64", address, value));
            putQword(address, value);
        }

        private void expectQwords(Map<Long, Long> expectedChangedQwords) {
            Ram expected = new Ram(initialQwords);
            expectedChangedQwords.forEach(expected::putQword);
            equal(expected.bytes, bytes, "entire supplied RAM including retained adjacent DWORDs");
        }

        @Override public int readUnsignedByte(long address) { throw unused("readUnsignedByte"); }
        @Override public int lockedXaddDword(long address, int addend) { throw unused("lockedXaddDword"); }
        @Override public void writeByte(long address, int value) { throw unused("writeByte"); }
        @Override public Bits128 read128(long address) { throw unused("read128"); }
        @Override public void write128(long address, Bits128 value) { throw unused("write128"); }
        private AssertionError unused(String name) { return new AssertionError("No held source operation: " + name); }
    }

    private static String hex(long value) { return Long.toUnsignedString(value, 16); }
    private static String event(String operation, long address) { return operation + ":" + hex(address); }
    private static String event(String operation, long address, long value) {
        return operation + ":" + hex(address) + ":" + hex(value);
    }
    private static void equal(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
        }
    }
}
