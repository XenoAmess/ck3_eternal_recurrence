package org.xar.ck3.research.m5;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.MemorySeed;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155WitnessApi.SeedByte;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.Failure;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.Phase;
import org.xar.ck3.research.m5.GovernmentWhole4798WitnessApi.Witness;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;
import org.xar.ck3.research.m5.GovernmentLookupLoop580WitnessApi.CpuInput;
import org.xar.ck3.research.m5.GovernmentLookupLoop580WitnessApi.CpuReply;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.AtomicStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.DeepStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsPort;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.GsStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.HashStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.LookupStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.ResultStep;
import org.xar.ck3.research.m5.GovernmentWholeConcrete173WitnessApi.Branch;


public final class GovernmentWholeRoot181Probe {
    private GovernmentWholeRoot181Probe() { }
    private static void check(boolean ok, String reason) { if (!ok) throw new AssertionError(reason); }
    private static final class OwnedStop extends UnsupportedOperationException {
        private static final long serialVersionUID = 1L;
        OwnedStop(String reason) { super(reason); }
    }
    private static final class Activity {
        long count, stopAt = -1;
        Failure stopKind;
        final OwnedStop budget = new OwnedStop("whole-owned-budget"), cpu = new OwnedStop("whole-owned-cpu"), call = new OwnedStop("whole-owned-call");
        void hit() { count++; }
        void stop(Failure kind) { check(stopAt < 0, "second stop observation"); stopAt = count; stopKind = kind; }
        void noLater() { if (stopAt >= 0) check(count == stopAt, "activity after owned unavailable/rejection"); }
    }
    private static final class Memory implements GovernmentWholeRoot181Api.Memory {
        final Map<Long, Integer> bytes = new HashMap<>();
        final Map<Long, Integer> seedSnapshot = new HashMap<>();
        final Activity activity;
        final AtomicScript atomic;
        long trackedSlot,trackedReturn;
        int trackedWrites;
        Memory(MemorySeed seed, Activity a, AtomicScript as) {
            activity = a; atomic = as;
            for (SeedByte b : seed.bytes()) {
                check(b.byteBits() >= 0 && b.byteBits() <= 255, "invalid seed byte");
                Integer old = bytes.putIfAbsent(b.addressBits(), b.byteBits());
                check(old == null || old.intValue() == b.byteBits(), "conflicting seed bytes");
                seedSnapshot.put(b.addressBits(), b.byteBits());
            }
        }
        int peek(long a) { Integer b = bytes.get(a); check(b != null, "missing owned byte " + Long.toHexString(a)); return b; }
        long read(long a, int width) { long n = 0; for (int i = 0; i < width; i++) n |= ((long) peek(a + i)) << (8 * i); return n; }
        void write(long a, long n, int width) { for (int i = 0; i < width; i++) bytes.put(a + i, (int) (n >>> (8 * i)) & 255); }
        @Override public int readUnsignedByte(long a) { activity.hit(); return peek(a); }
        @Override public int readUnsignedWord(long a) { activity.hit(); return (int) read(a, 2); }
        @Override public int readDword(long a) { activity.hit(); return (int) read(a, 4); }
        @Override public long readQword(long a) { activity.hit(); return read(a, 8); }
        @Override public Bits128 read128(long a) { activity.hit(); return new Bits128(read(a, 8), read(a + 8, 8)); }
        @Override public void writeByte(long a, int n) { activity.hit(); write(a, n, 1); }
        @Override public void writeWord(long a, int n) { activity.hit(); write(a, n, 2); }
        @Override public void writeDword(long a, int n) { activity.hit(); write(a, Integer.toUnsignedLong(n), 4); }
        @Override public void writeQword(long a, long n) { activity.hit(); if(a==trackedSlot && n==trackedReturn) trackedWrites++; write(a, n, 8); }
        @Override public void write128(long a, Bits128 n) { activity.hit(); write(a, n.lowBits(), 8); write(a + 8, n.highBits(), 8); }
        @Override public int lockedXaddDword(long a, int addend) {
            activity.hit();
            int old = (int) read(a, 4);
            int stored = old + addend;
            atomic.consume(new AtomicStep(32, a, addend, old, stored));
            write(a, Integer.toUnsignedLong(stored), 4);
            return old;
        }
        @Override public int lockedXaddByte(long a, int addend) {
            activity.hit();
            int old = peek(a);
            int stored = (old + addend) & 255;
            atomic.consume(new AtomicStep(8, a, addend & 255, old, stored));
            write(a, stored, 1);
            return old;
        }
        void verify(Map<Long, Integer> expected) {
            for (var e : expected.entrySet()) {
                check(e.getValue() >= 0 && e.getValue() <= 255, "invalid expected byte");
                check(peek(e.getKey()) == e.getValue(), "byte mismatch " + Long.toHexString(e.getKey()) + " expected=" + e.getValue() + " actual=" + peek(e.getKey()));
            }
        }
        void verifyFinal(Map<Long, Integer> explicit) {
            Map<Long, Integer> finalMap = new HashMap<>(seedSnapshot);
            finalMap.putAll(explicit);
            verify(finalMap);
            check(bytes.equals(finalMap), "complete final image has missing/unexpected bytes");
        }
        void mutate(List<SeedByte> changes) { for (SeedByte b : changes) { check(b.byteBits() >= 0 && b.byteBits() <= 255, "invalid mutation byte"); writeByte(b.addressBits(), b.byteBits()); } }
    }
    private static final class AtomicScript {
        final List<AtomicStep> steps; int cursor;
        AtomicScript(List<AtomicStep> steps) { this.steps = steps; cursor = 0; }
        void consume(AtomicStep expected) {
            check(cursor < steps.size(), "unexpected atomic step");
            var actual = steps.get(cursor++);
            check(actual.equals(expected), "atomic step mismatch expected=" + actual + " observed=" + expected);
        }
        void done() { check(cursor == steps.size(), "unconsumed atomic steps"); }
    }
    private static final class GsScript {
        final List<GsStep> steps; int cursor;
        GsScript(List<GsStep> steps) { this.steps = steps; cursor = 0; }
        long consume(GsPort port) {
            check(cursor < steps.size(), "unexpected gs step");
            var actual = steps.get(cursor++);
            check(actual.port() == port, "gs port mismatch expected=" + actual.port() + " observed=" + port);
            return actual.returnedQword58Bits();
        }
        void done() { check(cursor == steps.size(), "unconsumed gs steps"); }
    }
    private static final class DeepScript {
        final List<DeepStep> steps; final Activity activity; int cursor;
        DeepScript(List<DeepStep> steps, Activity activity) {
            this.steps = steps; this.activity = activity; cursor = 0;
            for (DeepStep step : steps) check(!step.reject(), "these two new witnesses require normal deep work");
        }
        void consume(DeepStep expected) {
            activity.hit();
            check(cursor < steps.size(), "unexpected deep step");
            var actual = steps.get(cursor++);
            check(actual.equals(expected), "deep step mismatch expected=" + actual + " observed=" + expected);
            if (actual.reject()) throw new OwnedStop("deep-reject");
        }
        void done() { check(cursor == steps.size(), "unconsumed deep steps"); }
    }
    private static final class Ordinary implements GovernmentInitialFrame162Api.Calls {
        final List<GovernmentWhole4798WitnessApi.OrdinaryStep> steps; final Memory memory; final GsScript gs; final GsPort port; int cursor;
        Ordinary(List<GovernmentWhole4798WitnessApi.OrdinaryStep> steps, Memory memory, GsScript gs, GsPort port) { this.steps = steps; this.memory = memory; this.gs = gs; this.port = port; }
        @Override public long readGsQword58() { memory.activity.hit(); return gs.consume(port); }
        @Override public VolatileBits invoke(OpaqueCall actual) {
            memory.activity.hit(); check(cursor < steps.size(), "unexpected ordinary call " + Long.toHexString(actual.callSiteRva()));
            var expected = steps.get(cursor++);
            check(actual.equals(expected.expected()), "full ordinary frame mismatch step " + cursor + " expected=" + expected.expected() + " actual=" + actual);
            memory.verify(expected.expectedMemoryBytes()); memory.mutate(expected.mutation());
            if (expected.unsupported()) { memory.activity.stop(Failure.CALL_UNSUPPORTED); throw memory.activity.call; }
            return expected.normalPost();
        }
        void done() { check(cursor == steps.size(), "unconsumed ordinary calls"); }
    }
    private static final class LookupCalls implements GovernmentLookupLoop580Api.Calls {
        final Witness witness; final Memory memory; final GsScript gs; int cursor;
        LookupCalls(Witness w, Memory m, GsScript gs) { witness = w; memory = m; this.gs = gs; }
        @Override public long readGsQword58() { memory.activity.hit(); return gs.consume(GsPort.LOOKUP); }
        @Override public GovernmentLookupLoop580Api.CallPost invoke(GovernmentLookupLoop580Api.CallFrame actual) {
            memory.activity.hit(); check(cursor < witness.lookupCalls().size(), "unexpected lookup call");
            var e = witness.lookupCalls().get(cursor++); check(actual.equals(e.expected()), "full lookup frame mismatch");
            memory.verify(e.expectedMemoryBytes()); memory.mutate(e.memoryMutation());
            if (e.unsupported()) { memory.activity.stop(Failure.CALL_UNSUPPORTED); throw memory.activity.call; }
            return Objects.requireNonNull(e.normalPost());
        }
        void done() { check(cursor == witness.lookupCalls().size(), "unconsumed lookup calls"); }
    }
    private static final class Cpu implements GovernmentLookupLoop580Api.Cpu {
        final Witness witness; final Activity activity; int cursor;
        Cpu(Witness w, Activity a) { witness = w; activity = a; }
        CpuReply reply(CpuInput actual) {
            activity.hit(); check(cursor < witness.cpuCalls().size(), "unexpected CPU instruction");
            var e = witness.cpuCalls().get(cursor++); check(actual.equals(e.expected()), "CPU raw input/environment mismatch");
            if (e.unsupported()) { activity.stop(Failure.CPU_UNSUPPORTED); throw activity.cpu; }
            return Objects.requireNonNull(e.normalPost());
        }
        GovernmentLookupLoop580Api.VectorPost vector(CpuInput actual) {
            CpuReply r = reply(actual); check(r instanceof GovernmentLookupLoop580WitnessApi.VectorReply, "expected vector reply");
            return ((GovernmentLookupLoop580WitnessApi.VectorReply) r).post();
        }
        @Override public GovernmentLookupLoop580Api.VectorPost movssMemoryXmm6(long site, int bits, Bits128 x, Mxcsr32 m) { return vector(new GovernmentLookupLoop580WitnessApi.Movss(site, bits, x, m)); }
        @Override public GovernmentLookupLoop580Api.VectorPost movdXmm0(long site, int bits, Bits128 x, Mxcsr32 m) { return vector(new GovernmentLookupLoop580WitnessApi.Movd(site, bits, x, m)); }
        @Override public GovernmentLookupLoop580Api.VectorPost cvtdq2psXmm0(long site, Bits128 x, Mxcsr32 m) { return vector(new GovernmentLookupLoop580WitnessApi.Convert(site, x, m)); }
        @Override public GovernmentLookupLoop580Api.VectorPost mulssXmm0(long site, Bits128 x, Bits128 y, Mxcsr32 m) { return vector(new GovernmentLookupLoop580WitnessApi.Multiply(site, x, y, m)); }
        @Override public GovernmentLookupLoop580Api.EaxPost cvttss2siEax(long site, Bits128 x, Mxcsr32 m) {
            CpuReply r = reply(new GovernmentLookupLoop580WitnessApi.Truncate(site, x, m)); check(r instanceof GovernmentLookupLoop580WitnessApi.EaxReply, "expected EAX reply");
            return ((GovernmentLookupLoop580WitnessApi.EaxReply) r).post();
        }
        void done() { check(cursor == witness.cpuCalls().size(), "unconsumed CPU instructions"); }
    }
    private static final class Budgets {
        final Witness witness; final Activity activity; int cursor;
        Budgets(Witness w, Activity a) { witness = w; activity = a; }
        void visit(Phase phase, long header, long current, long end) {
            activity.hit(); check(cursor < witness.budgets().size(), "unexpected budget event " + phase);
            var e = witness.budgets().get(cursor++);
            check(e.phase() == phase && e.headerRva() == header && e.cursorOrCapacityBits() == current
                    && e.endSlotOrFixedEndOrSignedLimitBits() == end, "exact budget event mismatch " + phase);
            if (e.reject()) { activity.stop(Failure.BUDGET); throw activity.budget; }
        }
        GovernmentWhole4798Api.Budgets ports() {
            return new GovernmentWhole4798Api.Budgets(
                    (h, c) -> visit(Phase.INITIAL, h, c, 0),
                    (h, c, e) -> visit(Phase.LOOKUP, h, c, e),
                    (h, c, e) -> visit(Phase.EARLIER, h, c, e),
                    (h, c, e) -> visit(Phase.ROWS, h, c, e),
                    (h, c, e) -> visit(Phase.COMPACTION, h, c, e),
                    (h, c, e) -> visit(Phase.TAIL, h, c, e));
        }
        void done() { check(cursor == witness.budgets().size(), "unconsumed budget events"); }
    }
    private static final class MxcsrBoundary implements GovernmentWhole4798Api.MxcsrBoundary {
        final Witness witness; final Activity activity; boolean initialSeen, finalSeen;
        MxcsrBoundary(Witness w, Activity a) { witness = w; activity = a; }
        @Override public GovernmentWhole4798Api.MxcsrObservation afterInitial(GovernmentInitialFrame162Api.Join actual) {
            activity.hit(); check(!initialSeen && witness.afterInitial() != null, "unexpected initial MXCSR observation"); initialSeen = true;
            check(actual.equals(witness.afterInitial().expectedJoin()), "full initial join mismatch expected=" + witness.afterInitial().expectedJoin() + " actual=" + actual);
            var observation = witness.afterInitial().observation();
            if (observation instanceof GovernmentWhole4798Api.UnavailableMxcsr) activity.stop(Failure.INITIAL_MXCSR_UNAVAILABLE);
            return observation;
        }
        @Override public GovernmentWhole4798Api.MxcsrObservation afterNormalReturn(GovernmentMiddle166Api.Result actual) {
            activity.hit(); check(!finalSeen && witness.afterFinal() != null, "unexpected final MXCSR observation"); finalSeen = true;
            check(actual.equals(witness.afterFinal().expectedResult()), "full Middle result mismatch expected=" + witness.afterFinal().expectedResult() + " actual=" + actual);
            return witness.afterFinal().observation();
        }
        void done() { check(initialSeen == (witness.afterInitial() != null), "initial observation not consumed"); check(finalSeen == (witness.afterFinal() != null), "final observation not consumed"); }
    }
    private static final class Post153 implements GovernmentPrimarySuffix155Api.VolatileBoundary {
        final Witness witness; final Activity activity; int cursor;
        Post153(Witness w, Activity a) { witness = w; activity = a; }
        @Override public GovernmentPrimarySuffix155Api.VolatileObservation afterPrefix(GovernmentPrimarySuffix155Api.Entry entry,
                GovernmentCaller153Api.Outcome outcome, long r14) {
            activity.hit(); check(cursor < witness.post153().size(), "unexpected post153 observation");
            var e = witness.post153().get(cursor++);
            check(entry.equals(e.expectedEntry()) && outcome == e.expectedOutcome() && r14 == e.expectedPostPrefixR14Bits(), "full post153 boundary mismatch");
            if (e.observation() instanceof GovernmentPrimarySuffix155Api.UnavailableVolatile) activity.stop(Failure.POST153_UNAVAILABLE);
            return e.observation();
        }
        void done() { check(cursor == witness.post153().size(), "unconsumed post153 observations"); }
    }
    private static AssertionError forbidden() { return new AssertionError("unexpected lookup155/prefix153 port in signed-guard-skip witness"); }
    private static final InternedLookup155Api.Calls NO_LOOKUP155 = new InternedLookup155Api.Calls() {
        @Override public long readGsQword58() { throw forbidden(); }
        @Override public void pauseSpin() { throw forbidden(); }
        @Override public void call4223A84(long a) { throw forbidden(); }
        @Override public void call4223F24(long a) { throw forbidden(); }
        @Override public void call4223A24(long a) { throw forbidden(); }
    };
    private static final GovernmentCaller153Api.Calls NO_PREFIX153 = new GovernmentCaller153Api.Calls() {
        @Override public long readGsQword58() { throw forbidden(); }
        @Override public long call3F4F8E0(GovernmentTierLookupKey150.LookupKey32 key) { throw forbidden(); }
        @Override public long call3F5F970(int bits) { throw forbidden(); }
        @Override public void callABBAF0(GovernmentCaller153Api.DiagnosticCall call) { throw forbidden(); }
    };
    private static void run(GovernmentWholeConcrete173WitnessApi.Witness w) {
        Activity a = new Activity();
        AtomicScript atomic = new AtomicScript(w.atomicSteps());
        GsScript gs = new GsScript(w.gsSteps());
        DeepScript deep = new DeepScript(w.deepSteps(), a);
        Memory memory = new Memory(w.whole().memorySeed(), a, atomic);
        memory.trackedSlot=w.whole().expectedResult().initialJoin().frameRspBits()-0x88L;
        memory.trackedReturn=w.whole().entry().imageBaseBits()+0x3f5f980L;

        // Build DeepInputs using the witness's explicit MXCSR observations
        var m0Obs = new GovernmentWhole4798Api.AvailableMxcsr(w.m0HashMxcsrAt4FE());
        var m1Obs = new GovernmentWhole4798Api.AvailableMxcsr(w.m1HashMxcsrAt85E());
        var deepInputs = new GovernmentWholeConcrete173Api.DeepInputs(
                m0Obs, m1Obs,
                new GovernmentByteUpdate169Api.LoopBudget() { @Override public void beforeIteration(long h, long r8, long r9d, long rbx) { deep.consume(new HashStep(Branch.M0_2D0B490, h, r8, r9d, rbx, false)); } },
                new GovernmentLookup167Api.SpinBudget() { @Override public void beforeStep(long i, long l) { deep.consume(new LookupStep(Branch.M0_2D0B490, i, l, false)); } },
                new GovernmentResult168Api.WorkBudget() { @Override public void beforeStep(long i, long a) { deep.consume(new ResultStep(Branch.M0_2D0B490, i, a, false)); } },
                new GovernmentByteUpdate169Api.LoopBudget() { @Override public void beforeIteration(long h, long r8, long r9d, long rbx) { deep.consume(new HashStep(Branch.M1_2D1B7F0, h, r8, r9d, rbx, false)); } },
                new GovernmentLookup167Api.SpinBudget() { @Override public void beforeStep(long i, long l) { deep.consume(new LookupStep(Branch.M1_2D1B7F0, i, l, false)); } },
                new GovernmentResult168Api.WorkBudget() { @Override public void beforeStep(long i, long a) { deep.consume(new ResultStep(Branch.M1_2D1B7F0, i, a, false)); } },
                new GovernmentByteUpdate169Api.LoopBudget() { @Override public void beforeIteration(long h, long r8, long r9d, long rbx) { deep.consume(new HashStep(Branch.PRIMARY_LOOKUP, h, r8, r9d, rbx, false)); } }
        );

        // Wrap the whole witness for the standard 4798 protocol
        Witness whole = w.whole();
        Ordinary initial = new Ordinary(whole.initialCalls(), memory, gs, GsPort.INITIAL);
        Ordinary fallback = new Ordinary(whole.ordinaryCalls(), memory, gs, GsPort.ORDINARY);
        LookupCalls lookup = new LookupCalls(whole, memory, gs);
        Cpu cpu = new Cpu(whole, a);
        Budgets budgets = new Budgets(whole, a);
        MxcsrBoundary fp = new MxcsrBoundary(whole, a);
        Post153 post = new Post153(whole, a);
        var calls = new GovernmentWhole4798Api.Calls(initial, lookup, fallback, NO_LOOKUP155, NO_PREFIX153, post);

        // Execute the new subject
        GovernmentWhole4798Api.Result actual = null;
        RuntimeException failure = null;
        try {
            actual = GovernmentWholeRoot181.execute(whole.entry(), memory, calls, budgets.ports(), cpu, fp, deepInputs, (header,node,end) -> { throw new AssertionError("unexpected helper loop"); });
        } catch (RuntimeException e) {
            failure = e;
        }

        // Verify normal completion (both cases must be NONE failure)
        check(whole.failure() == Failure.NONE, "expected normal whole result");
        if (failure != null) throw new AssertionError("unexpected subject failure", failure);
        check(actual != null, "missing normal whole result");
        check(Objects.equals(actual.initialJoin(), whole.expectedResult().initialJoin()), "initial join mismatch expected=" + whole.expectedResult().initialJoin() + " observed=" + actual.initialJoin());
        check(Objects.equals(actual.lookupJoin(), whole.expectedResult().lookupJoin()), "lookup join mismatch expected=" + whole.expectedResult().lookupJoin() + " observed=" + actual.lookupJoin());
        check(Objects.equals(actual.earlierJoin(), whole.expectedResult().earlierJoin()), "earlier join mismatch expected=" + whole.expectedResult().earlierJoin() + " observed=" + actual.earlierJoin());
        check(Objects.equals(actual.rowsJoin(), whole.expectedResult().rowsJoin()), "rows join mismatch expected=" + whole.expectedResult().rowsJoin() + " observed=" + actual.rowsJoin());
        check(Objects.equals(actual.middleResult(), whole.expectedResult().middleResult()), "middle result mismatch expected=" + whole.expectedResult().middleResult() + " observed=" + actual.middleResult());
        check(Objects.equals(actual, whole.expectedResult()), "full whole result mismatch expected=" + whole.expectedResult() + " observed=" + actual);

        // Verify scripts consumed
        deep.done();
        atomic.done();
        gs.done();

        // Verify memory final state
        memory.verifyFinal(whole.expectedFinalBytes());
        check(memory.trackedWrites==2, "two C090 calls must write returnslot twice: "+memory.trackedWrites);

        // Verify all cursors done
        initial.done(); fallback.done(); lookup.done(); cpu.done(); budgets.done(); fp.done(); post.done();
        a.noLater();
    }

    public static void main(String[] args) {
        check(args.length == 0, "no arguments");
        List<GovernmentWholeConcrete173WitnessApi.Witness> cases = new GovernmentWholeRoot181Fixtures().witnesses();
        check(cases.size() == 1, "expected exactly one new normalized-whole witness");
        HashSet<String> names = new HashSet<>();
        for (GovernmentWholeConcrete173WitnessApi.Witness w : cases) {
            check(!w.whole().name().isBlank() && names.add(w.whole().name()), "blank/duplicate witness name");
            try { run(w); } catch (RuntimeException | AssertionError e) { throw new AssertionError("whole witness " + w.whole().name() + " failed", e); }
        }
        System.out.println("GovernmentWholeRoot181Probe:1/1 whole-with-root only");
    }
}
