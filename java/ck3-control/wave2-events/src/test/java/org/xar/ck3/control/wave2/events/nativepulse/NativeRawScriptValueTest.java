package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeRawScriptValue.*;

/** Actual producer -> strict original codec -> shared reconstruction -> original weighted consumer/archive. */
final class NativeRawScriptValueTest {
    private static final NativePlayableAnnualGate.Executable EXE = NativePlayableAnnualGate.Executable.CURRENT_12004;
    private static final BigInteger ZERO = BigInteger.ZERO;
    private static final ExactRef FIXTURE = new ExactRef("fixture/source-only", 1, "0".repeat(64));
    private static final Leaf A = new Leaf(new BigInteger("18446744073709550001"), BigInteger.valueOf(0x3761780));
    private static final Leaf B = new Leaf(new BigInteger("18446744073709550002"), BigInteger.valueOf(0x3761780));
    private static final Context CONTEXT = new Context(scope(5, 7), new BigInteger("18446744073709550003"), ZERO, BigInteger.TEN, 0);
    private static Pdx scalar(int kind, long raw) { return new Pdx(kind, raw, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of()); }
    private static Input input(Pdx value, Optional<Random> random) { return new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, random, List.of(), List.of()); }
    private static Scope scope(int type, long payload) { return new Scope(BigInteger.valueOf(type), new BigInteger(Long.toUnsignedString(payload))); }
    private static long known(Input input) { Result result = analyze(input); assertEquals(Status.RECONSTRUCTED, result.status()); return result.raw().orElseThrow(); }
    private static ScriptValue ready(long raw) { return new ScriptValue(raw, true, Optional.empty()); }

    @Test void kindZeroSkipsEveryDynamicPointerAndRandomBranch() {
        Pdx value = new Pdx(0, Long.MIN_VALUE, 55, Optional.of(new ScriptValue(8, true, Optional.of(A))), Optional.of(ready(3)), Optional.of(B),
            List.of(new ScopeStep(A, new ScopeMask(BigInteger.ONE, ZERO))));
        Input input = input(value, Optional.of(new Random(2, 9))); Result result = analyze(input);
        assertEquals(Long.MIN_VALUE, known(input)); assertEquals(Branch.INLINE_KIND_ZERO, result.branch());
        assertEquals(input.originalRandom(), result.afterRandom()); assertTrue(result.trace().isEmpty());
    }
    @Test void b8OverrideWinsBeforeRangeLowerAndScopeAndRequiresOriginalInvocation() {
        Random random = new Random(17, 991); Random after = new Random(19, 991);
        Pdx value = new Pdx(2, 33, 88, Optional.of(ready(77)), Optional.of(ready(44)), Optional.of(A), List.of());
        Input missing = input(value, Optional.of(random)); assertEquals(Status.ORIGINAL_LEAF_UNAVAILABLE, analyze(missing).status());
        OriginalRawCall original = new OriginalRawCall(A, CONTEXT, Optional.of(random), Optional.of(after), -900, FIXTURE);
        Input supplied = new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.of(random), List.of(original), List.of());
        Result result = analyze(supplied); assertEquals(-900, known(supplied)); assertEquals(Branch.OVERRIDE_B8, result.branch());
        assertEquals(Optional.of(after), result.afterRandom()); assertEquals(1, result.rawCallsConsumed());
        OriginalRawCall crossed = new OriginalRawCall(B, CONTEXT, Optional.of(random), Optional.of(after), -900, FIXTURE);
        assertEquals(Status.ORIGINAL_INVOCATION_MISMATCH, analyze(new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.of(random), List.of(crossed), List.of())).status());
    }
    @Test void scriptValueDynamicPrecedesReadyAndNotReadyReturnsZero() {
        Pdx dynamic = new Pdx(1, 999, 0, Optional.of(new ScriptValue(456, true, Optional.of(A))), Optional.empty(), Optional.empty(), List.of());
        assertEquals(Status.ORIGINAL_LEAF_UNAVAILABLE, analyze(input(dynamic, Optional.empty())).status());
        Input supplied = new Input(EXE, FIXTURE, FIXTURE, dynamic, CONTEXT, Optional.empty(),
            List.of(new OriginalRawCall(A, CONTEXT, Optional.empty(), Optional.empty(), 123, FIXTURE)), List.of());
        assertEquals(123, known(supplied));
        Pdx notReady = new Pdx(1, 999, 0, Optional.of(new ScriptValue(456, false, Optional.empty())), Optional.empty(), Optional.empty(), List.of());
        assertEquals(0, known(input(notReady, Optional.empty())));
    }
    @Test void kindTwoWithoutRandomTakesGeneralLowerOrStoredPath() {
        Pdx value = new Pdx(2, 10, 99, Optional.of(ready(20)), Optional.of(new ScriptValue(7, true, Optional.of(A))), Optional.empty(), List.of());
        Result result = analyze(input(value, Optional.empty())); assertEquals(20, result.raw().orElseThrow().longValue());
        assertEquals(Branch.LOWER_SCRIPT_VALUE_A8, result.branch()); assertEquals(0, result.rawCallsConsumed());
        assertEquals(10, known(input(scalar(2, 10), Optional.empty())));
    }
    @Test void inclusiveRangeUsesTwoRandomWordsSortsEndpointsAndWrapsCounter() {
        assertEquals(8051925661761608175L, random63(new Random(0, 0)));
        assertEquals(4972963477199015354L, random63(new Random(0xffff_ffffL, 0xffff_ffffL)));
        Pdx inverted = new Pdx(2, 25, -11, Optional.empty(), Optional.empty(), Optional.empty(), List.of());
        Result result = analyze(input(inverted, Optional.of(new Random(0xffff_ffffL, 0xffff_ffffL))));
        assertEquals(13, result.raw().orElseThrow().longValue()); assertEquals(Optional.of(new Random(1, 0xffff_ffffL)), result.afterRandom());
        Pdx equal = new Pdx(2, -19, -19, Optional.empty(), Optional.empty(), Optional.empty(), List.of());
        assertEquals(-19, known(input(equal, Optional.of(new Random(0, 0)))));
    }
    @Test void wrappedZeroWidthPreservesCounterMutationAndNativeFault() {
        Pdx full = new Pdx(2, Long.MIN_VALUE, Long.MAX_VALUE, Optional.empty(), Optional.empty(), Optional.empty(), List.of());
        Result result = analyze(input(full, Optional.of(new Random(0xffff_ffffL, 123))));
        assertEquals(Status.NATIVE_DIVISOR_ZERO, result.status()); assertTrue(result.raw().isEmpty());
        assertEquals(Optional.of(new Random(1, 123)), result.afterRandom());
    }
    @Test void rangeLowerThenUpperShareCallbackRandomStateAndOriginalOrder() {
        Pdx value = new Pdx(2, 999, 888, Optional.of(new ScriptValue(11, true, Optional.of(A))),
            Optional.of(new ScriptValue(12, true, Optional.of(B))), Optional.empty(), List.of());
        Random r0 = new Random(5, 8), r1 = new Random(7, 8), r2 = new Random(9, 8);
        List<OriginalRawCall> calls = List.of(new OriginalRawCall(A, CONTEXT, Optional.of(r0), Optional.of(r1), 1, FIXTURE),
            new OriginalRawCall(B, CONTEXT, Optional.of(r1), Optional.of(r2), 1, FIXTURE));
        Input original = new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.of(r0), calls, List.of());
        Result result = analyze(original); assertEquals(1, result.raw().orElseThrow().longValue()); assertEquals(2, result.rawCallsConsumed());
        assertEquals(Optional.of(new Random(11, 8)), result.afterRandom());
        List<OriginalRawCall> wrong = List.of(calls.get(1), calls.get(0));
        assertEquals(Status.ORIGINAL_INVOCATION_MISMATCH, analyze(new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.of(r0), wrong, List.of())).status());
    }
    @Test void scopeTypeZeroBypassesMaskAndWrongTypeFallsBackBeforeLeaf() {
        ScopeStep denied = new ScopeStep(A, new ScopeMask(BigInteger.ONE, ZERO));
        Pdx value = new Pdx(1, 90, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of(denied));
        assertEquals(90, known(input(value, Optional.empty()))); assertEquals(0, analyze(input(value, Optional.empty())).scopeCallsConsumed());
        Context zero = CONTEXT.withCurrent(scope(0, 0));
        Input noLeaf = new Input(EXE, FIXTURE, FIXTURE, value, zero, Optional.empty(), List.of(), List.of());
        assertEquals(Status.ORIGINAL_LEAF_UNAVAILABLE, analyze(noLeaf).status());
        Context beyond = CONTEXT.withCurrent(scope(129, 0));
        assertEquals(Status.NATIVE_SCOPE_MASK_OUT_OF_BOUNDS, analyze(new Input(EXE, FIXTURE, FIXTURE, value, beyond, Optional.empty(), List.of(), List.of())).status());
    }
    @Test void scopeChainUsesPreviousScopeWithOriginalContextWordsAndTypeOneSignedPayload() {
        ScopeMask all = new ScopeMask(ZERO, ZERO); Scope intermediate = scope(10, 72), output = scope(1, Long.MIN_VALUE);
        Pdx value = new Pdx(1, 90, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of(new ScopeStep(A, all), new ScopeStep(B, all)));
        List<OriginalScopeCall> calls = List.of(new OriginalScopeCall(A, CONTEXT, intermediate, FIXTURE),
            new OriginalScopeCall(B, CONTEXT.withCurrent(intermediate), output, FIXTURE));
        Input original = new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.empty(), List.of(), calls);
        assertEquals(Long.MIN_VALUE, known(original)); assertEquals(2, analyze(original).scopeCallsConsumed());
        List<OriginalScopeCall> invalid = List.of(calls.get(0), new OriginalScopeCall(B, CONTEXT, output, FIXTURE));
        assertEquals(Status.ORIGINAL_INVOCATION_MISMATCH, analyze(new Input(EXE, FIXTURE, FIXTURE, value, CONTEXT, Optional.empty(), List.of(), invalid)).status());
    }
    @Test void actualTriggerGuardExactTypeHasPriorityAndZeroDiffersFromScopeChain() {
        ScopeMask firstOnly = new ScopeMask(BigInteger.ONE, ZERO), empty = new ScopeMask(ZERO, ZERO);
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 5, scope(5, 7), firstOnly));
        assertEquals(ScopeEligibility.INELIGIBLE, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 4, scope(5, 7), firstOnly));
        assertEquals(ScopeEligibility.INELIGIBLE, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 0, scope(0, 7), firstOnly));
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.CHAIN_3755500, 0, scope(0, 7), firstOnly));
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 0, scope(0, 7), empty));
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 0, scope(128, 7), new ScopeMask(ZERO, BigInteger.ONE.shiftLeft(63))));
        assertEquals(ScopeEligibility.MASK_OUT_OF_BOUNDS, scopeEligibility(ScopeUse.TRIGGER_GUARD_372B4C0, 0, scope(129, 7), firstOnly));
        assertEquals(ScopeEligibility.ELIGIBLE, scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 5, scope(5, 7), firstOnly));
        assertEquals(ScopeEligibility.INELIGIBLE, scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(0, 7), firstOnly));
        assertEquals(ScopeEligibility.MASK_OUT_OF_BOUNDS, scopeEligibility(ScopeUse.EFFECT_DISPATCH_3765E50, 0, scope(129, 7), firstOnly));
    }
    @Test void codecPreservesFullQwordsNullVersusEmptyAndRejectsCoercionMissingAndExtra() {
        Input original = input(new Pdx(2, Long.MIN_VALUE, Long.MAX_VALUE, Optional.of(ready(1)), Optional.empty(), Optional.of(A), List.of()), Optional.of(new Random(0xffff_ffffL, 2)));
        byte[] bytes = NativeRawScriptValueJson.encode(original); assertEquals(original, NativeRawScriptValueJson.decode(bytes));
        assertArrayEquals(bytes, NativeRawScriptValueJson.encode(NativeRawScriptValueJson.decode(bytes)));
        List<Consumer<ObjectNode>> invalid = List.of(row -> row.remove("original_random"), row -> row.put("extra", true), row -> row.putNull("original_raw_calls"),
            row -> row.withObject("value").put("native_kind_c0", true), row -> row.withObject("value").put("native_kind_c0", 2.0),
            row -> row.withObject("value").put("stored_raw_98", 42), row -> row.withObject("value").put("stored_raw_98", "-0"),
            row -> row.withObject("value").put("stored_raw_98", "9223372036854775808"), row -> row.withObject("context").put("word_08_u64", 9007199254740993L),
            row -> row.withObject("context").put("word_08_u64", "018446744073709550003"), row -> row.withObject("context").put("word_08_u64", "18446744073709551616"),
            row -> row.withObject("original_random").put("counter_u32", "4294967296"), row -> row.withObject("value").withObject("lower_a8").put("raw_ready_7b", 1),
            row -> row.put("exe_sha256", "0".repeat(64)));
        for (Consumer<ObjectNode> mutation : invalid) { ObjectNode row = (ObjectNode) StrictJson.parse(bytes, NativeRawScriptValueJson.MAX_BYTES); mutation.accept(row);
            assertThrows(IllegalArgumentException.class, () -> NativeRawScriptValueJson.decode(row.toString().getBytes(StandardCharsets.UTF_8))); }
        assertThrows(IllegalArgumentException.class, () -> NativeRawScriptValueJson.decode("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
    }
    @Test void sameProducerCodecOriginalWeightedConsumerAndRandomRefusal() {
        Input original = input(new Pdx(1, 99, 0, Optional.of(ready(200000)), Optional.empty(), Optional.empty(), List.of()), Optional.empty());
        NativeOnActionWeightProgram.RawValue factor = weightOperand(NativeRawScriptValueJson.decode(NativeRawScriptValueJson.encode(original)));
        var modifier = new NativeOnActionWeightProgram.TriggerModifier(new NativeOnActionWeightProgram.Always(new NativeOnActionWeightProgram.InlineBool(true)), factor, new NativeOnActionWeightProgram.InlineRaw(0));
        var program = new NativeOnActionWeightProgram.Program(100000, List.of(modifier));
        var review = new NativeOnActionWeightProgram.Review(EXE, new NativeOnActionWeightProgram.Context(0, NativeOnActionWeightProgram.ScopeVerdict.VALIDATED),
            List.of(new NativeOnActionWeightProgram.RowSource(3, 20, Optional.of(new NativeOnActionWeightProgram.Definition(Optional.empty(), Optional.of(program))))), 0);
        var computation = assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, NativeOnActionWeightProgram.analyze(NativeOnActionWeightProgram.decode(NativeOnActionWeightProgram.encode(review))).computation());
        assertEquals(40, computation.rows().getFirst().nativeWeight()); assertEquals(3, computation.originalRowIndex().orElseThrow());
        assertInstanceOf(NativeOnActionWeightProgram.DynamicRaw.class, weightOperand(input(scalar(2, 1), Optional.of(new Random(0, 0)))));
        assertFalse(analyze(original).completeNativeAst()); assertFalse(analyze(original).currentLoadedSourceQualified()); assertFalse(analyze(original).nativeGameExecuted());
    }
    @Test void originalArchiveRoundTripColdRecomputeAndAstDerivedOriginalTamperRefusal() throws Exception {
        MemoryStore store = new MemoryStore(); ExactRef observation = store.preserve("original-frame".getBytes(StandardCharsets.UTF_8));
        ExactRef ast = store.preserve("original-ast-source".getBytes(StandardCharsets.UTF_8));
        Input original = new Input(EXE, observation, ast, scalar(0, Long.MAX_VALUE), CONTEXT, Optional.empty(), List.of(), List.of());
        var record = NativeRawScriptValueArchive.preserve(original, store);
        var cold = NativeRawScriptValueArchive.replay(NativeRawScriptValueArchive.decode(NativeRawScriptValueArchive.encode(record)), store);
        assertEquals(original, cold.original()); assertArrayEquals(NativeRawScriptValueJson.encode(analyze(original)), NativeRawScriptValueJson.encode(cold.recomputed()));
        ExactRef falseDerived = store.preserve("{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeRawScriptValueArchive.replay(new NativeRawScriptValueArchive.Recorded(record.original(), falseDerived), store));
        byte[] old = store.contents.get(ast.path()); store.contents.put(ast.path(), "changed".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeRawScriptValueArchive.replay(record, store)); store.contents.put(ast.path(), old);
        store.contents.put(record.original().path(), "{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeRawScriptValueArchive.replay(record, store));
    }
    private static final class MemoryStore implements NativeOnActionFieldArchive.Store {
        private final Map<String, byte[]> contents = new HashMap<>(); private int sequence;
        @Override public ExactRef preserve(byte[] original) {
            try { byte[] bytes = original.clone(); String path = "memory/" + sequence++; contents.put(path, bytes);
                return new ExactRef(path, bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
            catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        }
        @Override public byte[] load(ExactRef ref) throws IOException { byte[] bytes = contents.get(ref.path()); if (bytes == null) throw new IOException("missing original"); return bytes.clone(); }
    }
}
