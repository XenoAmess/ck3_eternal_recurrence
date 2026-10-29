package org.xar.ck3.control.wave2.events.nativepulse;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Exact .4 Raw-Pdx branch and ScriptValue wrapper reconstruction from supplied original inputs.
 * Concrete virtual AST/scope leaves remain original observations, not an invented evaluator.
 * No loaded-source, current-scope, Game, AST-completeness or dispatch qualification is granted.
 */
public final class NativeRawScriptValue {
    private static final BigInteger U64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private NativeRawScriptValue() { }

    /** Both native scope qwords are retained. Only the low16 tag is interpreted here. */
    public record Scope(BigInteger metadataU64, BigInteger payloadU64) {
        public Scope { u64(metadataU64); u64(payloadU64); }
        public int nativeTypeU16() { return metadataU64.and(BigInteger.valueOf(65535)).intValue(); }
    }
    /** Unknown native context qwords are preserved under offset names, never given guessed roles. */
    public record Context(Scope current, BigInteger word08U64, BigInteger word10U64,
                          BigInteger word18U64, int modeU8) {
        public Context { Objects.requireNonNull(current); u64(word08U64); u64(word10U64); u64(word18U64);
            StrictJson.require(modeU8 >= 0 && modeU8 <= 255, "native context byte required"); }
        public Context withCurrent(Scope value) { return new Context(value, word08U64, word10U64, word18U64, modeU8); }
    }
    public record Random(long counterU32, long seedU32) {
        public Random { u32(counterU32); u32(seedU32); }
    }
    /** Original object identity distinguishes distinct AST leaves with equal scalar results. */
    public record Leaf(BigInteger objectAddressU64, BigInteger virtualTargetRvaU64) {
        public Leaf { u64(objectAddressU64); u64(virtualTargetRvaU64);
            StrictJson.require(objectAddressU64.signum() > 0 && virtualTargetRvaU64.signum() > 0, "nonzero original leaf identity required"); }
    }
    /** +70 dynamic pointer has precedence over +7B readiness and +68 stored raw. */
    public record ScriptValue(long storedRaw68, boolean rawReady7B, Optional<Leaf> dynamic70) {
        public ScriptValue { Objects.requireNonNull(dynamic70); }
    }
    /** Native virtual+30 returns a two-qword accepted-type mask, not trigger truth. */
    public record ScopeMask(BigInteger firstU64, BigInteger secondU64) {
        public ScopeMask { u64(firstU64); u64(secondU64); }
        public boolean empty() { return firstU64.signum() == 0 && secondU64.signum() == 0; }
        private boolean includes(int type) { int bit = type - 1; return (bit < 64 ? firstU64 : secondU64).testBit(bit & 63); }
    }
    public record ScopeStep(Leaf leaf, ScopeMask originalAcceptedTypes) {
        public ScopeStep { Objects.requireNonNull(leaf); Objects.requireNonNull(originalAcceptedTypes); }
    }
    public enum ScopeUse { CHAIN_3755500, TRIGGER_GUARD_372B4C0, EFFECT_DISPATCH_3765E50 }
    public enum ScopeEligibility { ELIGIBLE, INELIGIBLE, MASK_OUT_OF_BOUNDS }
    /**
     * Reconstructs only the reviewed mask gates. Scope registry object-validity,
     * trigger truth and effect execution are separate and are not inferred here.
     */
    public static ScopeEligibility scopeEligibility(ScopeUse use, int declaredTypeU16, Scope current, ScopeMask mask) {
        Objects.requireNonNull(use); Objects.requireNonNull(current); Objects.requireNonNull(mask);
        StrictJson.require(declaredTypeU16 >= 0 && declaredTypeU16 <= 65535, "declared native type word required");
        int type = current.nativeTypeU16();
        if (use == ScopeUse.CHAIN_3755500 && type == 0) return ScopeEligibility.ELIGIBLE;
        if (use != ScopeUse.CHAIN_3755500 && declaredTypeU16 != 0 && declaredTypeU16 == type) return ScopeEligibility.ELIGIBLE;
        if (mask.empty()) return ScopeEligibility.ELIGIBLE;
        if (type == 0) return ScopeEligibility.INELIGIBLE;
        if (type > 128) return ScopeEligibility.MASK_OUT_OF_BOUNDS;
        return mask.includes(type) ? ScopeEligibility.ELIGIBLE : ScopeEligibility.INELIGIBLE;
    }
    public record Pdx(int nativeKindC0, long storedRaw98, long upperRawA0,
                      Optional<ScriptValue> lowerA8, Optional<ScriptValue> upperB0,
                      Optional<Leaf> overrideB8, List<ScopeStep> scopeChain08) {
        public Pdx { StrictJson.require(nativeKindC0 >= 0, "nonnegative native kind required");
            Objects.requireNonNull(lowerA8); Objects.requireNonNull(upperB0); Objects.requireNonNull(overrideB8);
            scopeChain08 = List.copyOf(scopeChain08); StrictJson.require(scopeChain08.size() <= 512, "bounded original scope chain required"); }
    }
    /** Original callback output for this projected invocation, not a complete native call ABI or semantic proof. */
    public record OriginalRawCall(Leaf leaf, Context before, Optional<Random> randomBefore,
                                  Optional<Random> randomAfter, long outputRaw, ExactRef originalObservation) {
        public OriginalRawCall { Objects.requireNonNull(leaf); Objects.requireNonNull(before); Objects.requireNonNull(randomBefore);
            Objects.requireNonNull(randomAfter); evidence(originalObservation);
            StrictJson.require(randomBefore.isPresent() == randomAfter.isPresent(), "callback cannot add or erase RNG pointer"); }
    }
    public record OriginalScopeCall(Leaf leaf, Context before, Scope output, ExactRef originalObservation) {
        public OriginalScopeCall { Objects.requireNonNull(leaf); Objects.requireNonNull(before); Objects.requireNonNull(output); evidence(originalObservation); }
    }
    public record Input(NativePlayableAnnualGate.Executable executable, ExactRef originalObservation,
                        ExactRef originalAstSource, Pdx value, Context context, Optional<Random> originalRandom,
                        List<OriginalRawCall> originalRawCalls, List<OriginalScopeCall> originalScopeCalls) {
        public Input { Objects.requireNonNull(executable); evidence(originalObservation); evidence(originalAstSource);
            Objects.requireNonNull(value); Objects.requireNonNull(context); Objects.requireNonNull(originalRandom);
            originalRawCalls = List.copyOf(originalRawCalls); originalScopeCalls = List.copyOf(originalScopeCalls);
            StrictJson.require(originalRawCalls.size() <= 1024 && originalScopeCalls.size() <= 1024, "bounded original callback observations required");
            // A leaf may recur with a different invocation. The ordered call list preserves each actual occurrence.
        }
    }
    public enum Status { RECONSTRUCTED, ORIGINAL_LEAF_UNAVAILABLE, ORIGINAL_INVOCATION_MISMATCH,
        NATIVE_DIVISOR_ZERO, NATIVE_SCOPE_MASK_OUT_OF_BOUNDS }
    public enum Branch { INLINE_KIND_ZERO, OVERRIDE_B8, RANGE_KIND_TWO, LOWER_SCRIPT_VALUE_A8, SCOPE_CHAIN, STORED_FALLBACK }
    public enum TraceKind { RAW_VIRTUAL_30, SCOPE_VIRTUAL_20, SCRIPT_VALUE_INLINE, SCOPE_REJECTED, RANGE64 }
    public record Trace(TraceKind kind, Optional<Leaf> leaf, int ordinal) {
        public Trace { Objects.requireNonNull(kind); Objects.requireNonNull(leaf); StrictJson.require(ordinal >= 0, "trace ordinal required"); }
    }
    public record Result(Status status, Branch branch, Optional<Long> raw, Optional<Random> afterRandom,
                         int rawCallsConsumed, int scopeCallsConsumed, List<Trace> trace, String diagnosis) {
        public Result { Objects.requireNonNull(status); Objects.requireNonNull(branch); Objects.requireNonNull(raw); Objects.requireNonNull(afterRandom);
            trace = List.copyOf(trace); StrictJson.text(diagnosis);
            StrictJson.require((status == Status.RECONSTRUCTED) == raw.isPresent(), "only reconstructed result carries a scalar"); }
        public boolean completeNativeAst() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }

    /** One producer and consumer path is shared by direct analysis, weighted adapter and archive replay. */
    public static Result analyze(Input input) {
        Objects.requireNonNull(input); State state = new State(input); Pdx value = input.value();
        if (value.nativeKindC0() == 0) return state.known(Branch.INLINE_KIND_ZERO, value.storedRaw98());
        if (value.overrideB8().isPresent()) {
            Optional<Long> raw = state.rawLeaf(value.overrideB8().orElseThrow(), input.context());
            return state.finish(Branch.OVERRIDE_B8, raw);
        }
        if (value.nativeKindC0() == 2 && state.random.isPresent()) {
            Optional<Long> lower = value.lowerA8().isEmpty() ? Optional.of(value.storedRaw98()) : state.script(value.lowerA8().orElseThrow(), input.context());
            if (lower.isEmpty()) return state.finish(Branch.RANGE_KIND_TWO, lower);
            Optional<Long> upper = value.upperB0().isEmpty() ? Optional.of(value.upperRawA0()) : state.script(value.upperB0().orElseThrow(), input.context());
            if (upper.isEmpty()) return state.finish(Branch.RANGE_KIND_TWO, upper);
            Random before = state.random.orElseThrow(); long numerator = random63(before);
            state.random = Optional.of(new Random((before.counterU32() + 2) & 0xffff_ffffL, before.seedU32()));
            state.trace(TraceKind.RANGE64, Optional.empty());
            long minimum = Math.min(lower.orElseThrow(), upper.orElseThrow());
            long divisor = Math.max(lower.orElseThrow(), upper.orElseThrow()) - minimum + 1;
            if (divisor == 0) { state.fail(Status.NATIVE_DIVISOR_ZERO, "E46530 updates counter by two before signed idiv faults on zero wrapped width");
                return state.finish(Branch.RANGE_KIND_TWO, Optional.empty()); }
            // Signed wrapped width is intentional. Numerator is at most Long.MAX_VALUE, so MIN/-1 is impossible.
            return state.known(Branch.RANGE_KIND_TWO, minimum + numerator % divisor);
        }
        if (value.lowerA8().isPresent()) return state.finish(Branch.LOWER_SCRIPT_VALUE_A8, state.script(value.lowerA8().orElseThrow(), input.context()));
        if (!value.scopeChain08().isEmpty()) {
            Scope current = input.context().current();
            for (ScopeStep step : value.scopeChain08()) {
                ScopeMask mask = step.originalAcceptedTypes();
                // 3755500 differs from 372B4C0: scope type zero bypasses mask rejection here.
                ScopeEligibility eligibility = scopeEligibility(ScopeUse.CHAIN_3755500, 0, current, mask);
                if (eligibility == ScopeEligibility.MASK_OUT_OF_BOUNDS) { state.fail(Status.NATIVE_SCOPE_MASK_OUT_OF_BOUNDS, "native type would read beyond the reconstructed two-qword mask");
                    return state.finish(Branch.SCOPE_CHAIN, Optional.empty()); }
                if (eligibility == ScopeEligibility.INELIGIBLE) { state.trace(TraceKind.SCOPE_REJECTED, Optional.of(step.leaf())); return state.known(Branch.SCOPE_CHAIN, value.storedRaw98()); }
                Optional<Scope> next = state.scopeLeaf(step.leaf(), input.context().withCurrent(current));
                if (next.isEmpty()) return state.finish(Branch.SCOPE_CHAIN, Optional.empty());
                current = next.orElseThrow();
                if (current.nativeTypeU16() == 0) return state.known(Branch.SCOPE_CHAIN, value.storedRaw98());
            }
            // Native returned type 1 is the raw qword; a different type diagnoses then falls back.
            return state.known(Branch.SCOPE_CHAIN, current.nativeTypeU16() == 1 ? current.payloadU64().longValue() : value.storedRaw98());
        }
        return state.known(Branch.STORED_FALLBACK, value.storedRaw98());
    }

    /**
     * Existing weighted-index arithmetic has no state-passing raw RNG interface. Refuse every
     * potentially random subtree there, including callbacks whose counter happens to return unchanged.
     */
    public static NativeOnActionWeightProgram.RawValue weightOperand(Input input) {
        Result result = analyze(input);
        boolean virtual = result.trace().stream().anyMatch(row -> row.kind() == TraceKind.RAW_VIRTUAL_30 || row.kind() == TraceKind.SCOPE_VIRTUAL_20);
        if (result.status() == Status.RECONSTRUCTED && !virtual && result.trace().stream().noneMatch(row -> row.kind() == TraceKind.RANGE64))
            return new NativeOnActionWeightProgram.InlineRaw(result.raw().orElseThrow());
        return new NativeOnActionWeightProgram.DynamicRaw(Math.max(1, input.value().nativeKindC0()),
            result.status() == Status.RECONSTRUCTED ? "raw operand requires complete native callback ABI and random/state propagation before weighted chooser adoption" : result.diagnosis());
    }
    /** E46530 two-word generator, signed range reduction and counter mutation are separate. */
    public static long random63(Random original) {
        int first = mixed((int) original.counterU32(), (int) original.seedU32());
        int second = mixed((int) (original.counterU32() + 1), (int) original.seedU32());
        return ((long) (first & 0x7fff_ffff) << 32) | Integer.toUnsignedLong(second);
    }
    private static int mixed(int counter, int seed) {
        int value = seed - counter * 0x4ad685b3;
        value = (value ^ (value >>> 8)) + 0x68e31da4;
        value = (value ^ (value << 8)) * 0x1b56c4e9;
        value = (value ^ (value >>> 8)) * 0x92d68ca2;
        return value ^ (value >>> 8);
    }
    private static final class State {
        private final Input input;
        private Optional<Random> random;
        private int rawIndex, scopeIndex;
        private final List<Trace> trace = new ArrayList<>();
        private Status status = Status.RECONSTRUCTED;
        private String diagnosis = "source-reviewed wrapper reconstruction only; concrete virtual leaves are original observations";
        private State(Input input) { this.input = input; random = input.originalRandom(); }
        private void trace(TraceKind kind, Optional<Leaf> leaf) { trace.add(new Trace(kind, leaf, trace.size())); }
        private void fail(Status code, String message) { status = code; diagnosis = message; }
        private Optional<Long> script(ScriptValue value, Context context) {
            if (value.dynamic70().isPresent()) return rawLeaf(value.dynamic70().orElseThrow(), context);
            trace(TraceKind.SCRIPT_VALUE_INLINE, Optional.empty());
            return Optional.of(value.rawReady7B() ? value.storedRaw68() : 0L);
        }
        private Optional<Long> rawLeaf(Leaf leaf, Context context) {
            if (rawIndex >= input.originalRawCalls().size()) { fail(Status.ORIGINAL_LEAF_UNAVAILABLE, "concrete virtual+30 AST implementation and original callback output unavailable"); return Optional.empty(); }
            OriginalRawCall call = input.originalRawCalls().get(rawIndex);
            if (!call.leaf().equals(leaf) || !call.before().equals(context) || !call.randomBefore().equals(random)) {
                fail(Status.ORIGINAL_INVOCATION_MISMATCH, "original raw callback identity/context/RNG does not match this exact invocation"); return Optional.empty(); }
            rawIndex++; random = call.randomAfter(); trace(TraceKind.RAW_VIRTUAL_30, Optional.of(leaf)); return Optional.of(call.outputRaw());
        }
        private Optional<Scope> scopeLeaf(Leaf leaf, Context context) {
            if (scopeIndex >= input.originalScopeCalls().size()) { fail(Status.ORIGINAL_LEAF_UNAVAILABLE, "concrete virtual+20 scope implementation and original callback output unavailable"); return Optional.empty(); }
            OriginalScopeCall call = input.originalScopeCalls().get(scopeIndex);
            if (!call.leaf().equals(leaf) || !call.before().equals(context)) {
                fail(Status.ORIGINAL_INVOCATION_MISMATCH, "original scope callback identity/context does not match this exact invocation"); return Optional.empty(); }
            scopeIndex++; trace(TraceKind.SCOPE_VIRTUAL_20, Optional.of(leaf)); return Optional.of(call.output());
        }
        private Result known(Branch branch, long raw) { return finish(branch, Optional.of(raw)); }
        private Result finish(Branch branch, Optional<Long> raw) { return new Result(status, branch, raw, random, rawIndex, scopeIndex, trace, diagnosis); }
    }
    static void u64(BigInteger value) { Objects.requireNonNull(value); StrictJson.require(value.signum() >= 0 && value.compareTo(U64_MAX) <= 0, "unsigned64 required"); }
    private static void u32(long value) { StrictJson.require(value >= 0 && value <= 0xffff_ffffL, "unsigned32 required"); }
    private static void evidence(ExactRef value) { Objects.requireNonNull(value); StrictJson.require(value.bytes() > 0 && value.bytes() <= NativeRawScriptValueJson.MAX_BYTES, "bounded original evidence required"); }
}
