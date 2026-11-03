package org.xar.ck3.research.m3.add4range262.manual;

import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.add4range262.Add4Range262;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * Independent public-DATA foreign-protocol witness; Native first execution is recorded separately.
 * No selected COPY/range producer is run. Every public Memory member throws on access.
 * Source-only whole-growth reasoning is recorded separately in INDEPENDENT-ORACLE262.txt.
 */
public final class Add4RangeForeign262 {
    private Add4RangeForeign262() { }

    private record Site(long rva, GovernmentCrtBoundary185Api.TargetKind kind,
                        long targetBits, int instructionLength) { }

    // These are the six real nonselected instructions, not made-up substitutes for ADD219.
    // Indirect target bits are explicit owned DATA, not a claimed native allocator/free ABI.
    private static final Site[] NONSELECTED = {
        new Site(0xADD153L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                0x00007FF58A01D530L, 3),
        new Site(0xADD16DL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, 5),
        new Site(0xADD17CL, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, 5),
        new Site(0xADD1A0L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, 5),
        new Site(0xADD1B5L, GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                0x00007FF58A01DC90L, 3),
        new Site(0xADD1F7L, GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA, 0x4226860L, 5)
    };

    /** Manual entry for the finite foreign-protocol cases. */
    public static void main(String[] arguments) {
        verifyAll();
    }

    public static void verifyAll() {
        for (int index = 0; index < NONSELECTED.length; index++) {
            verifySite(NONSELECTED[index], index, false);
        }
        // The four COPY instructions belong to the old259 outer binding in withCopy.
        // Only the actual allocator/free instructions remain foreign through that composition.
        verifySite(NONSELECTED[0], 0, true);
        verifySite(NONSELECTED[4], 4, true);
        verifyNullRejections();
        verifyPublicConstructorRejections();
    }

    private static void verifySite(Site site, int index, boolean withCopy) {
        Add4Fp639Api.CallFrame frame = publicCallFrame(site, index);
        String label = (withCopy ? "withCopy/" : "bind/") + Long.toHexString(site.rva());
        for (int defect = 0; defect < 4; defect++) {
            verifyReturned(frame, normal(frame, defect), defect, withCopy, label + "/normal" + defect);
        }
        for (QueueFp604Api.StopReason reason : QueueFp604Api.StopReason.values()) {
            verifyReturned(frame, stopped(frame, reason), -1, withCopy, label + "/" + reason);
        }
        verifyThrown(frame, new UnsupportedOperationException(label + "/runtime-marker"),
                withCopy, label + "/runtime-identity");
        verifyThrown(frame, new AssertionError(label + "/error-marker"),
                withCopy, label + "/error-identity");
        Bound bound = bind(null, null, withCopy);
        Throwable failure = capture(() -> bound.router().invoke(frame));
        require(failure instanceof NullPointerException, label + "/null-outcome rejected");
        verifyForeignOnly(bound, frame, 1, label + "/null-outcome");
    }

    private static void verifyReturned(Add4Fp639Api.CallFrame frame, QueueFp604Api.Outcome offered,
            int normalDefect, boolean withCopy, String label) {
        Bound bound = bind(offered, null, withCopy);
        QueueFp604Api.Outcome returned = bound.router().invoke(frame);
        require(returned == offered, label + "/same Outcome object");
        verifyForeignOnly(bound, frame, 1, label);

        // Deliberately AFTER delegation: whole639.call owns this normal-return validation.
        // Foreign malformed Normal DATA must reach that caller without wrapper repair/checking.
        if (returned instanceof QueueFp604Api.Normal normal) {
            if (normalDefect == 0) {
                frame.checkNormalReturn(normal);
            } else {
                Throwable failure = capture(() -> frame.checkNormalReturn(normal));
                require(failure instanceof IllegalArgumentException, label + "/caller rejects afterwards");
            }
        }
    }

    private static void verifyThrown(Add4Fp639Api.CallFrame frame, Throwable marker,
            boolean withCopy, String label) {
        Bound bound = bind(null, marker, withCopy);
        Throwable observed = capture(() -> bound.router().invoke(frame));
        require(observed == marker, label + "/same exception object");
        verifyForeignOnly(bound, frame, 1, label);
    }

    private record Bound(Add4Fp639Api.Calls router, RecordingForeign foreign,
                         NoMemory memory, NoBudget budget, NoTail tails) { }

    private static Bound bind(QueueFp604Api.Outcome offered, Throwable marker, boolean withCopy) {
        NoMemory memory = new NoMemory();
        NoBudget budget = new NoBudget();
        NoTail tails = new NoTail();
        RecordingForeign foreign = new RecordingForeign(offered, marker);
        Add4Fp639Api.Calls router = withCopy
                ? Add4Range262.withCopy(memory, budget, tails, foreign)
                : Add4Range262.bind(memory, budget, foreign);
        Bound bound = new Bound(router, foreign, memory, budget, tails);
        verifyForeignOnly(bound, null, 0, "binding-construction");
        return bound;
    }

    private static void verifyForeignOnly(Bound bound, Add4Fp639Api.CallFrame frame,
            int expectedCalls, String label) {
        require(bound.foreign().calls == expectedCalls, label + "/one foreign call");
        require(bound.foreign().lastFrame == frame, label + "/same frame object");
        require(bound.memory().calls == 0, label + "/zero Memory calls");
        require(bound.budget().calls == 0, label + "/zero budget calls");
        require(bound.tails().calls == 0, label + "/zero COPY tail calls");
    }

    /** Uses only the actual public constructors and supplies every represented register member. */
    private static Add4Fp639Api.CallFrame publicCallFrame(Site site, int index) {
        long image = 0x0000000140000000L + index * 0x100000L;
        long preCallRsp = 0x0000010020001000L + index * 0x100L;
        long seed = 0xC120000000000000L ^ (site.rva() * 0x10101L) ^ index;
        VolatileBits v = volatileBits(seed);
        NonvolatileBits n = nonvolatileBits(seed ^ 0x76543210FEDCBA98L);
        var call = new GovernmentCrtBoundary185Api.Call(site.rva(), site.kind(),
                site.targetBits(), preCallRsp, v, n);
        var child = new GovernmentCrtBoundary185Api.Entry(image, preCallRsp - 8L, v, n);
        // Known controls/status are explicit fixture DATA; no implicit constant/default FP state.
        var mxcsr = new QueueFp604Api.Mxcsr(0x20 | ((index & 3) << 13), 0xE03F);
        return new Add4Fp639Api.CallFrame(call, child, (index & 1) != 0, mxcsr,
                site.instructionLength(), image + site.rva() + site.instructionLength());
    }

    private static QueueFp604Api.Normal normal(Add4Fp639Api.CallFrame frame, int defect) {
        long seed = 0xE13A5067C892DB4FL ^ frame.call().callSiteRva() ^ (defect * 0x1101L);
        long rip = frame.returnRipBits() + (defect == 1 ? 1L : 0L);
        long rsp = frame.call().rspBits() + (defect == 2 ? 8L : 0L);
        NonvolatileBits n = defect == 3 ? nonvolatileBits(seed) : frame.call().nonvolatileBits();
        var result = new GovernmentCrtBoundary185Api.NormalReturn(volatileBits(seed), rip, rsp, n);
        // Partial knowledge and changed DF are intentional foreign DATA, not wrapper defaults.
        var fp = new QueueFp604Api.Mxcsr((int)(frame.call().callSiteRva() + defect * 7L) & 0x3F, 0x3F);
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(result,
                !frame.directionFlagSet()), fp);
    }

    private static QueueFp604Api.Stopped stopped(Add4Fp639Api.CallFrame frame,
            QueueFp604Api.StopReason reason) {
        long seed = 0x97A5C3E1D6B48F20L ^ frame.call().callSiteRva() ^ reason.ordinal();
        var state = new GovernmentCrtBoundary185Api.Entry(frame.childEntry().imageBaseBits() + 0x4000L,
                frame.childEntry().rspBits() - 0x10L, volatileBits(seed), nonvolatileBits(~seed));
        var fp = new QueueFp604Api.Mxcsr((int)(seed >>> 8) & 0x3F, 0x3F);
        var snapshot = new QueueFp604Api.Snapshot(state, frame.call().callSiteRva() + 0x700L,
                !frame.directionFlagSet(), fp);
        int raised = reason == QueueFp604Api.StopReason.ARCHITECTURAL_FP_CONDITION ? 0x21 : 0;
        return new QueueFp604Api.Stopped(reason, snapshot, raised,
                0x00000000D0000000L | frame.call().callSiteRva());
    }

    private static VolatileBits volatileBits(long seed) {
        return new VolatileBits(seed ^ 0x1101L, seed ^ 0x2202L, seed ^ 0x3303L,
                seed ^ 0x4404L, seed ^ 0x5505L, seed ^ 0x6606L, seed ^ 0x7707L,
                bits(seed, 0x101L), bits(seed, 0x202L), bits(seed, 0x303L),
                bits(seed, 0x404L), bits(seed, 0x505L), bits(seed, 0x606L));
    }

    private static NonvolatileBits nonvolatileBits(long seed) {
        return new NonvolatileBits(seed ^ 0x8101L, seed ^ 0x8202L, seed ^ 0x8303L, seed ^ 0x8404L,
                seed ^ 0x8505L, seed ^ 0x8606L, seed ^ 0x8707L, seed ^ 0x8808L, bits(seed, 0x909L));
    }

    private static Bits128 bits(long seed, long tag) {
        return new Bits128(seed ^ tag, Long.rotateLeft(~seed, 17) ^ (tag << 32));
    }

    private static void verifyNullRejections() {
        NoMemory memory = new NoMemory();
        NoBudget budget = new NoBudget();
        NoTail tails = new NoTail();
        RecordingForeign foreign = new RecordingForeign(null, null);
        expectNull(() -> Add4Range262.bind(null, budget, foreign), "bind/null-memory");
        expectNull(() -> Add4Range262.bind(memory, null, foreign), "bind/null-budget");
        expectNull(() -> Add4Range262.bind(memory, budget, null), "bind/null-foreign");
        expectNull(() -> Add4Range262.withCopy(null, budget, tails, foreign), "withCopy/null-memory");
        expectNull(() -> Add4Range262.withCopy(memory, null, tails, foreign), "withCopy/null-budget");
        expectNull(() -> Add4Range262.withCopy(memory, budget, null, foreign), "withCopy/null-tails");
        expectNull(() -> Add4Range262.withCopy(memory, budget, tails, null), "withCopy/null-foreign");
        Add4Fp639Api.Calls narrow = Add4Range262.bind(memory, budget, foreign);
        Add4Fp639Api.Calls composed = Add4Range262.withCopy(memory, budget, tails, foreign);
        expectNull(() -> narrow.invoke(null), "bind/null-frame");
        expectNull(() -> composed.invoke(null), "withCopy/null-frame");
        require(foreign.calls == 0, "null-rejection/foreign untouched");
        require(memory.calls == 0 && budget.calls == 0 && tails.calls == 0,
                "null-rejection/effect ports untouched");
    }

    private static void verifyPublicConstructorRejections() {
        Add4Fp639Api.CallFrame valid = publicCallFrame(NONSELECTED[1], 1);
        var c = valid.call();
        var wrongSite = new GovernmentCrtBoundary185Api.Call(0xADD16EL, c.kind(), c.targetBits(),
                c.rspBits(), c.volatileBits(), c.nonvolatileBits());
        var wrongTarget = new GovernmentCrtBoundary185Api.Call(c.callSiteRva(), c.kind(), 0x9D0950L,
                c.rspBits(), c.volatileBits(), c.nonvolatileBits());
        require(capture(() -> new Add4Fp639Api.CallFrame(wrongSite, valid.childEntry(),
                valid.directionFlagSet(), valid.preMxcsr(), 5, valid.returnRipBits()))
                instanceof IllegalArgumentException, "public constructor rejects wrong site");
        require(capture(() -> new Add4Fp639Api.CallFrame(wrongTarget, valid.childEntry(),
                valid.directionFlagSet(), valid.preMxcsr(), 5, valid.returnRipBits()))
                instanceof IllegalArgumentException, "public constructor rejects wrong target");
    }

    private static void expectNull(Runnable action, String label) {
        require(capture(action) instanceof NullPointerException, label);
    }

    private static Throwable capture(Runnable action) {
        try {
            action.run();
            return null;
        } catch (RuntimeException | Error failure) {
            return failure;
        }
    }

    private static void require(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }

    private static final class RecordingForeign implements Add4Fp639Api.Calls {
        private final QueueFp604Api.Outcome offered;
        private final Throwable marker;
        private int calls;
        private Add4Fp639Api.CallFrame lastFrame;

        private RecordingForeign(QueueFp604Api.Outcome offered, Throwable marker) {
            this.offered = offered;
            this.marker = marker;
        }

        @Override public QueueFp604Api.Outcome invoke(Add4Fp639Api.CallFrame frame) {
            calls++;
            lastFrame = frame;
            if (marker instanceof RuntimeException failure) throw failure;
            if (marker instanceof Error failure) throw failure;
            return offered;
        }
    }

    private static final class NoBudget implements GovernmentCrtBoundary185Api.LoopBudget {
        private int calls;
        @Override public void beforeStep(long loopHeaderRva, long guardAddressBits) {
            calls++;
            throw new AssertionError("Foreign frame touched budget");
        }
    }

    private static final class NoTail implements FullCopyWithFp613.TailCalls {
        private int calls;
        @Override public QueueFp604Api.Outcome tail(FullCopyWithFp613.TailCall frame) {
            calls++;
            throw new AssertionError("Foreign frame touched COPY tail");
        }
    }

    /** Every actual inherited Memory member is declared; any call is a witness failure. */
    private static final class NoMemory implements Add4Range262.Memory {
        private int calls;
        private AssertionError touched(String member) {
            calls++;
            return new AssertionError("Foreign frame touched Memory." + member);
        }
        @Override public int readDword(long addressBits) { throw touched("readDword"); }
        @Override public long readQword(long addressBits) { throw touched("readQword"); }
        @Override public int readUnsignedByte(long addressBits) { throw touched("readUnsignedByte"); }
        @Override public void writeDword(long addressBits, int valueBits) { throw touched("writeDword"); }
        @Override public int lockedXaddDword(long addressBits, int addendBits) { throw touched("lockedXaddDword"); }
        @Override public void writeQword(long addressBits, long valueBits) { throw touched("writeQword"); }
        @Override public void writeByte(long addressBits, int lowByteBits) { throw touched("writeByte"); }
        @Override public Bits128 read128(long addressBits) { throw touched("read128"); }
        @Override public void write128(long addressBits, Bits128 valueBits) { throw touched("write128"); }
        @Override public void writeWord(long addressBits, int valueBits) { throw touched("writeWord"); }
        @Override public void write128NonTemporal(long addressBits, Bits128 valueBits) { throw touched("write128NonTemporal"); }
        @Override public void sfence() { throw touched("sfence"); }
        @Override public int readUnsignedWord(long addressBits) { throw touched("readUnsignedWord"); }
        @Override public FullCopy437Api.Bits256 read256(long addressBits) { throw touched("read256"); }
        @Override public void write256(long addressBits, FullCopy437Api.Bits256 valueBits) { throw touched("write256"); }
        @Override public void write256NonTemporal(long addressBits, FullCopy437Api.Bits256 valueBits) { throw touched("write256NonTemporal"); }
        @Override public void vzeroUpper() { throw touched("vzeroUpper"); }
    }
}
