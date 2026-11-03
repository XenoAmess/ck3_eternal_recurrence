package org.xar.ck3.study.m6.activityguard264;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.activityprotocol264.ActivityCallProtocol264Api;
import org.xar.ck3.study.m6.activityprotocol264.ActivityCallProtocol264Api.Frame;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Four source-edge groups, six helper calls; no whole activity or native execution. */
public final class ActivityCallProtocol264GuardTest {
    private static final long IMAGE = 0x1234_0000_0000_0000L;
    private static final long SP = 0x0000_0077_0000_3000L;
    private static final long CHILD_SP = 0x0000_0077_0000_2FF8L;
    private static final long DIRECT_SITE = 0x23FCB01L;
    private static final long DIRECT_TARGET_RVA = 0x23FC7E0L;
    private static final long DIRECT_RET = 0x1234_0000_023F_CB06L;
    private static final long INDIRECT_SITE = 0x23FCA56L;
    private static final long INDIRECT_RET = 0x1234_0000_023F_CA59L;
    private static final long INDIRECT_TARGET = 0x6ABC_DEF0_1234_5678L;
    private static final long OLD_SLOT = 0x7777_8888_9999_AAAAL;
    private static final long ORIGIN = 0x1A8DC5CL;
    private static final QueueFp604Api.Mxcsr PRE_MX = new QueueFp604Api.Mxcsr(0x0201, 0x03C7);
    private static final QueueFp604Api.Mxcsr POST_MX = new QueueFp604Api.Mxcsr(0x1204, 0xF3CF);
    private static final Bits128 X6 = new Bits128(0xC01, 0xD01);
    private static final NonvolatileBits PRE_N = new NonvolatileBits(
            0x8101, 0x8202, 0x8303, 0x8404, 0x8505, 0x8606, 0x8707, 0x8808, X6);
    private static final VolatileBits PRE_V = new VolatileBits(
            0x1101, 0x2202, 0x3303, 0x4404, 0x5505, 0x6606, 0x7707,
            new Bits128(0x101, 0x201), new Bits128(0x102, 0x202),
            new Bits128(0x103, 0x203), new Bits128(0x104, 0x204),
            new Bits128(0x105, 0x205), new Bits128(0x106, 0x206));
    private static final VolatileBits POST_V = new VolatileBits(
            0xA101, 0xA202, 0xA303, 0xA404, 0xA505, 0xA606, 0xA707,
            new Bits128(0xA01, 0xB01), new Bits128(0xA02, 0xB02),
            new Bits128(0xA03, 0xB03), new Bits128(0xA04, 0xB04),
            new Bits128(0xA05, 0xB05), new Bits128(0xA06, 0xB06));

    private ActivityCallProtocol264GuardTest() { }

    public static void main(String[] args) {
        check(args.length == 0, "only the new four groups are selected");
        directNormalCommitsAllOfferedState();
        indirectTargetAliasesReturnSlot();
        invalidNormalCannotCommit();
        ordinaryPushErrorCannotCallChild();
        System.out.println("Four new activity call-protocol guard groups passed (six helper invocations)");
    }

    private static void directNormalCommitsAllOfferedState() {
        Fixture fixture = new Fixture(DIRECT_SITE, false, null);
        QueueFp604Api.Normal offered = normal(DIRECT_RET, SP, PRE_N);
        int[] calls = {0};
        QueueFp604Api.Outcome outcome = ActivityCallProtocol264Api.invokeOwnedCall(
                DIRECT_SITE, fixture.binding, frame -> {
                    calls[0]++;
                    fixture.memory.trace.add(new Access("childPort", DIRECT_SITE, DIRECT_TARGET_RVA));
                    checkFrame(frame, fixture, DIRECT_SITE, TargetKind.DIRECT_RVA,
                            DIRECT_TARGET_RVA, DIRECT_RET, 5);
                    return offered;
                });

        check(offered.equals(outcome), "the full offered Normal is returned");
        check(calls[0] == 1, "exactly one direct child call");
        check(fixture.memory.trace.equals(List.of(
                new Access("writeQword", CHILD_SP, DIRECT_RET),
                new Access("childPort", DIRECT_SITE, DIRECT_TARGET_RVA))),
                "direct source owns one push and no indirect read");
        checkCommitted(fixture, DIRECT_RET);
    }

    private static void indirectTargetAliasesReturnSlot() {
        Fixture fixture = new Fixture(INDIRECT_SITE, true, null);
        QueueFp604Api.Normal offered = normal(INDIRECT_RET, SP, PRE_N);
        int[] calls = {0};
        QueueFp604Api.Outcome outcome = ActivityCallProtocol264Api.invokeOwnedCall(
                INDIRECT_SITE, fixture.binding, frame -> {
                    calls[0]++;
                    fixture.memory.trace.add(new Access("childPort", INDIRECT_SITE, INDIRECT_TARGET));
                    checkFrame(frame, fixture, INDIRECT_SITE, TargetKind.INDIRECT_ABSOLUTE,
                            INDIRECT_TARGET, INDIRECT_RET, 3);
                    check(fixture.memory.cells.get(CHILD_SP).longValue() == INDIRECT_RET,
                            "push has overwritten the aliased target cell before the child port");
                    return offered;
                });

        check(offered.equals(outcome) && calls[0] == 1, "one indirect child Normal");
        check(fixture.memory.trace.equals(List.of(
                new Access("readQword", CHILD_SP, 0),
                new Access("writeQword", CHILD_SP, INDIRECT_RET),
                new Access("childPort", INDIRECT_SITE, INDIRECT_TARGET))),
                "fresh target read must precede overwriting the same qword with RET");
        checkCommitted(fixture, INDIRECT_RET);
    }

    private static void invalidNormalCannotCommit() {
        // Three independent rows distinguish each guard; the other two fields stay valid.
        for (int row = 0; row < 3; row++) {
            Fixture fixture = new Fixture(DIRECT_SITE, false, null);
            long returnedRip = row == 0 ? DIRECT_RET + 8 : DIRECT_RET;
            long returnedSp = row == 1 ? SP + 8 : SP;
            NonvolatileBits returnedN = row == 2
                    ? new NonvolatileBits(0x8102, 0x8202, 0x8303, 0x8404,
                            0x8505, 0x8606, 0x8707, 0x8808, X6)
                    : PRE_N;
            QueueFp604Api.Normal offered = normal(returnedRip, returnedSp, returnedN);
            int[] calls = {0};

            expectInvalid(() -> ActivityCallProtocol264Api.invokeOwnedCall(
                    DIRECT_SITE, fixture.binding, frame -> {
                        calls[0]++;
                        fixture.memory.trace.add(new Access("childPort", DIRECT_SITE, DIRECT_TARGET_RVA));
                        checkFrame(frame, fixture, DIRECT_SITE, TargetKind.DIRECT_RVA,
                                DIRECT_TARGET_RVA, DIRECT_RET, 5);
                        return offered;
                    }));

            check(calls[0] == 1, "bad Normal still follows exactly one child call");
            check(fixture.context.snapshot().equals(fixture.before),
                    "bad RIP/SP/N must not commit any V/N/SP/DF/MXCSR field");
            check(fixture.context.mxcsr() == PRE_MX, "bad Normal retains original MXCSR object");
            check(fixture.memory.cells.equals(Map.of(CHILD_SP, DIRECT_RET)),
                    "completed RET push remains; guard rejection does not invent rollback");
            check(fixture.memory.trace.equals(List.of(
                    new Access("writeQword", CHILD_SP, DIRECT_RET),
                    new Access("childPort", DIRECT_SITE, DIRECT_TARGET_RVA))),
                    "bad Normal has no later memory operation or retry");
        }
    }

    private static void ordinaryPushErrorCannotCallChild() {
        RuntimeException supplied = new IllegalStateException("owned push before-write failure");
        Fixture fixture = new Fixture(DIRECT_SITE, false, supplied);
        int[] calls = {0};
        expectSame(supplied, () -> ActivityCallProtocol264Api.invokeOwnedCall(
                DIRECT_SITE, fixture.binding, frame -> {
                    calls[0]++;
                    throw new AssertionError("child must not run after failed owned push");
                }));

        check(calls[0] == 0, "ordinary push error cannot invoke child");
        check(fixture.context.snapshot().equals(fixture.before),
                "failed push retains complete represented parent state");
        check(fixture.context.mxcsr() == PRE_MX, "failed push retains MXCSR object");
        check(fixture.memory.cells.equals(Map.of(CHILD_SP, OLD_SLOT)),
                "this supplied before-write failure has no RAM commit");
        check(fixture.memory.trace.equals(List.of(new Access("writeQword", CHILD_SP, DIRECT_RET))),
                "only the failing push attempt occurs");
    }

    private static QueueFp604Api.Normal normal(long rip, long sp, NonvolatileBits n) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(POST_V, rip, sp, n), false), POST_MX);
    }

    private static void checkFrame(Frame frame, Fixture fixture, long site, TargetKind kind,
            long target, long ret, int length) {
        check(frame.memory() == fixture.memory, "same owned RAM by identity");
        check(frame.before().entry().equals(fixture.before.currentState()), "full actual parent preimage");
        check(frame.before().directionFlagSet() && frame.before().mxcsr() == PRE_MX,
                "explicit pre DF and partial MXCSR reach the port");
        check(frame.before().originCallSiteRva() == ORIGIN, "retained parent origin");
        check(frame.call().callSiteRva() == site && frame.call().kind() == kind
                        && frame.call().targetBits() == target && frame.call().rspBits() == SP,
                "actual call form, target encoding and pre-push SP");
        check(frame.call().volatileBits().equals(fixture.before.currentState().volatileBits())
                        && frame.call().nonvolatileBits().equals(PRE_N), "full call V/N image");
        check(frame.source().instructionLength() == length && frame.returnRipBits() == ret,
                "source length determines exact continuation");
        check(frame.childInput().entry().equals(new GovernmentCrtBoundary185Api.Entry(
                        IMAGE, CHILD_SP, fixture.before.currentState().volatileBits(), PRE_N)),
                "child entry owns exactly one pushed qword");
        check(frame.childInput().directionFlagSet() && frame.childInput().mxcsr() == PRE_MX
                        && frame.childInput().originCallSiteRva() == site,
                "child explicit state and actual CALL origin");
        check(fixture.context.snapshot().equals(fixture.before),
                "parent state remains uncommitted during port invocation");
        check(fixture.memory.cells.equals(Map.of(CHILD_SP, ret)), "exact owned RET exists before child");
    }

    private static void checkCommitted(Fixture fixture, long pushedRet) {
        check(fixture.context.currentState().equals(new GovernmentCrtBoundary185Api.Entry(
                        IMAGE, SP, POST_V, PRE_N)),
                "all represented V/N/SP fields match the actual Normal after commit");
        check(!fixture.context.directionFlagSet() && fixture.context.mxcsr() == POST_MX,
                "explicit changed DF and partial MXCSR are committed, not assumed preserved");
        check(fixture.context.instructionRva() == fixture.site, "helper retains actual CALL marker");
        check(fixture.context.originCallSiteRva() == ORIGIN, "caller origin remains intact");
        check(fixture.memory.cells.equals(Map.of(CHILD_SP, pushedRet)), "one exact RET remains in shared RAM");
    }

    private static void expectInvalid(Runnable action) {
        try { action.run(); }
        catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("invalid child Normal was accepted");
    }

    private static void expectSame(RuntimeException supplied, Runnable action) {
        try { action.run(); }
        catch (RuntimeException actual) {
            if (actual != supplied) throw new AssertionError("ordinary push error was replaced", actual);
            return;
        }
        throw new AssertionError("ordinary push error was swallowed");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private record Access(String operation, long address, long value) { }

    private static final class Fixture {
        final long site;
        final ProtocolMemory memory;
        final PostState240Api.Context context;
        final ActivityCallProtocol264Api.Binding binding;
        final QueueFp604Api.Snapshot before;

        Fixture(long site, boolean indirectAlias, RuntimeException pushError) {
            this.site = site;
            Registers registers = new Registers(new GovernmentPrimaryTail155Api.Entry(
                    IMAGE, 0x8404, 0x8505, 0x8303, 0x8808, 0x8202, SP,
                    0x8606, 0x8707, X6, PRE_V));
            registers.rbx = 0x8101;
            if (indirectAlias) registers.rax = 0x0000_0077_0000_2FE8L;
            memory = new ProtocolMemory(indirectAlias ? INDIRECT_TARGET : OLD_SLOT, pushError);
            context = new PostState240Api.Context(IMAGE, registers, true, PRE_MX, site, ORIGIN);
            binding = new ActivityCallProtocol264Api.Binding(IMAGE, registers, context, memory);
            before = context.snapshot();
            check(before.currentState().nonvolatileBits().equals(PRE_N), "literal complete N setup");
        }
    }

    private static final class ProtocolMemory implements GovernmentCrtBoundary185Api.Memory {
        final Map<Long, Long> cells = new HashMap<>();
        final List<Access> trace = new ArrayList<>();
        private final RuntimeException pushError;

        ProtocolMemory(long initialSlot, RuntimeException pushError) {
            cells.put(CHILD_SP, initialSlot);
            this.pushError = pushError;
        }

        @Override public long readQword(long address) {
            trace.add(new Access("readQword", address, 0));
            Long value = cells.get(address);
            if (value == null) throw new AssertionError("unexpected qword read address");
            return value;
        }

        @Override public void writeQword(long address, long value) {
            trace.add(new Access("writeQword", address, value));
            if (pushError != null) throw pushError;
            if (!cells.containsKey(address)) throw new AssertionError("unexpected qword write address");
            cells.put(address, value);
        }

        @Override public int readDword(long address) { throw unexpected("readDword"); }
        @Override public int readUnsignedByte(long address) { throw unexpected("readUnsignedByte"); }
        @Override public void writeDword(long address, int value) { throw unexpected("writeDword"); }
        @Override public int lockedXaddDword(long address, int value) { throw unexpected("lockedXaddDword"); }
        @Override public void writeByte(long address, int value) { throw unexpected("writeByte"); }
        @Override public Bits128 read128(long address) { throw unexpected("read128"); }
        @Override public void write128(long address, Bits128 value) { throw unexpected("write128"); }

        private AssertionError unexpected(String operation) {
            return new AssertionError("extra or widened protocol Memory operation: " + operation);
        }
    }
}
