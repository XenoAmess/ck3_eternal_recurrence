package org.xar.ck3.control.wave2.events.nativepulse;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Reviewed named kind3 Load -> actual +70 Math object -> existing evaluators. Static source only. */
public final class NativeNamedScriptValueProgram {
    public static final long PRIMARY_VTABLE = 0x49290b0L;
    public static final long SECONDARY_VTABLE = 0x49290c0L;
    public static final BigInteger BASE_EVALUATOR = BigInteger.valueOf(0xa07610L);
    public static final long MATH_FINALIZER_RVA = 0x8522c0L;
    private NativeNamedScriptValueProgram() { }

    /** Native definition memory before Load; the previous +70 pointee's class is deliberately unknown. */
    public record Before(BigInteger definitionU64, long primaryVtableRva, long secondaryVtableRva,
                         long storedRaw68, boolean rawReady7B, Optional<BigInteger> dynamic70) {
        public Before { pointer(definitionU64); Objects.requireNonNull(dynamic70); dynamic70.ifPresent(NativeNamedScriptValueProgram::pointer);
            StrictJson.require(primaryVtableRva == PRIMARY_VTABLE && secondaryVtableRva == SECONDARY_VTABLE,
                "reviewed named definition primary and +88 secondary identity required"); }
    }
    public record Input(ExactRef originalLoadSource, int originalLexicalKind1C8, Before before,
                        NativeScriptMathProgram.Input originalMath, Optional<NativeRawScriptValue.Input> originalRawConsumer) {
        public Input { Objects.requireNonNull(originalLoadSource); Objects.requireNonNull(before); Objects.requireNonNull(originalMath); Objects.requireNonNull(originalRawConsumer);
            StrictJson.require(originalLoadSource.bytes() > 0 && originalLoadSource.bytes() <= NativeScriptMathProgramJson.MAX_BYTES, "bounded original definition source required");
            StrictJson.require(originalLexicalKind1C8 == 3, "only actual named kind3 allocation/writer branch reviewed here");
            StrictJson.require(originalMath.root().entry() == NativeScriptMathProgram.Entry.NAMED_VALUE_70_375438F, "actual named +70 consumer required");
            for (NativeScriptMathProgram.Field field : originalMath.originalFields()) if (field instanceof NativeScriptMathProgram.SimpleField simple) validateOperandLoad(simple);
        }
    }
    /** Original boundary observation, not a claim that this Java process captured a loaded Game object. */
    public record LoadObservation(ExactRef originalObservation, BigInteger mathObjectU64, long primaryVtableRva,
                                  long finalizerSlot28Rva, List<BigInteger> nodesBefore, List<BigInteger> nodesAfter) {
        public LoadObservation { Objects.requireNonNull(originalObservation); pointer(mathObjectU64);
            StrictJson.require(originalObservation.bytes() > 0 && originalObservation.bytes() <= NativeScriptMathProgramJson.MAX_BYTES, "bounded original loader observation required");
            StrictJson.require(primaryVtableRva == NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA && finalizerSlot28Rva == MATH_FINALIZER_RVA,
                "exact current4 Math primary virtual28 ret0 required");
            nodesBefore = List.copyOf(nodesBefore); nodesAfter = List.copyOf(nodesAfter);
            StrictJson.require(nodesBefore.size() <= 256 && nodesAfter.size() <= 256, "bounded actual node occurrences required");
            nodesBefore.forEach(NativeNamedScriptValueProgram::pointer); nodesAfter.forEach(NativeNamedScriptValueProgram::pointer);
        }
    }
    public record ObservedLoad(Input original, LoadObservation observation) {
        public ObservedLoad { Objects.requireNonNull(original); Objects.requireNonNull(observation);
            StrictJson.require(observation.mathObjectU64().equals(original.originalMath().root().originalObjectU64()), "actual finalizer object must be this named Math allocation");
            StrictJson.require(observation.nodesBefore().equals(observation.nodesAfter())
                && observation.nodesAfter().size() == original.originalMath().originalFields().size(), "ret0 preserves exact node identities/order/count; equal numeric output is insufficient");
        }
    }
    public enum OperandLoad { CONSTRUCTOR_FIELDS_RETAINED, RAW_PDX_VIRTUAL_18 }
    /** 374A0C0: operations9..12 skip operand Load; A13AE0 explicitly initialized these fields to zero/null. */
    public static OperandLoad operandLoad(NativeScriptMathProgram.Operator operator) {
        return NativeScriptMathProgram.operandLoad(operator)==NativeScriptMathProgram.OperandLoad.CONSTRUCTOR_FIELDS_RETAINED
            ?OperandLoad.CONSTRUCTOR_FIELDS_RETAINED:OperandLoad.RAW_PDX_VIRTUAL_18;
    }
    private static void validateOperandLoad(NativeScriptMathProgram.SimpleField field) {
        NativeScriptMathProgram.validateOperandLoad(field);
    }
    public record Produced(Input original, NativeRawScriptValue.ScriptValue after, Optional<BigInteger> destroyedOld70,
                           boolean afterFlag7C, NativeScriptMathProgram.Produced math) {
        public Produced { Objects.requireNonNull(original); Objects.requireNonNull(after); Objects.requireNonNull(destroyedOld70); Objects.requireNonNull(math); }
    }
    /** 3753D53..DCD: allocate68B, install vtables, destroy old70, write new70, Load, then set7C. */
    public static Produced produce(Input input) {
        NativeRawScriptValue.Leaf leaf = new NativeRawScriptValue.Leaf(input.originalMath().root().originalObjectU64(), BASE_EVALUATOR);
        return new Produced(input, new NativeRawScriptValue.ScriptValue(input.before().storedRaw68(), input.before().rawReady7B(), Optional.of(leaf)),
            input.before().dynamic70(), true, NativeScriptMathProgram.produce(input.originalMath()));
    }
    /** 3F7E620 ignores callback return; C2 0000 neither changes the vector nor defines a success boolean. */
    public static Produced produce(ObservedLoad observed) { return produce(observed.original()); }
    public enum Status { MATH_RECONSTRUCTED_NO_RAW_OBSERVATION, MATCHED_ORIGINAL_RAW_PROJECTION, UNKNOWN_MATH, UNKNOWN_RAW, ORIGINAL_RAW_MISMATCH }
    public record Result(Status status, NativeScriptMathProgram.Result math, Optional<NativeRawScriptValue.Result> raw) {
        public Result { Objects.requireNonNull(status); Objects.requireNonNull(math); Objects.requireNonNull(raw); }
        public boolean staticKindThreeWriterRouteReviewed() { return true; }
        public boolean completeNativeAst() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }
    public static Result consume(Produced produced) {
        Input input = produced.original(); StrictJson.require(produced.equals(produce(input)), "consumer requires actual named producer fields and original math order");
        NativeScriptMathProgram.Result math = NativeScriptMathProgram.consume(produced.math());
        if (input.originalRawConsumer().isEmpty()) return new Result(math.status() == NativeScriptMathProgram.Status.RECONSTRUCTED
            ? Status.MATH_RECONSTRUCTED_NO_RAW_OBSERVATION : Status.UNKNOWN_MATH, math, Optional.empty());
        NativeRawScriptValue.Input original = input.originalRawConsumer().orElseThrow(); NativeRawScriptValue.Pdx value = original.value();
        StrictJson.require(original.executable() == input.originalMath().executable() && original.context().equals(input.originalMath().originalContext())
            && original.originalRandom().equals(input.originalMath().originalRandom()), "same original executable/context/RNG for named and Raw consumers required");
        StrictJson.require(value.nativeKindC0() != 0 && value.nativeKindC0() != 2 && value.overrideB8().isEmpty()
            && value.lowerA8().equals(Optional.of(produced.after())), "only original Raw lower+A8 invocation of produced named definition accepted");
        // No OriginalRawCall is manufactured from the Java result. Absent native projections remain unavailable.
        NativeRawScriptValue.Result raw = NativeRawScriptValue.analyze(original);
        Status status = math.status() != NativeScriptMathProgram.Status.RECONSTRUCTED ? Status.UNKNOWN_MATH
            : raw.status() != NativeRawScriptValue.Status.RECONSTRUCTED ? Status.UNKNOWN_RAW
            : raw.raw().orElseThrow() == math.reconstructedPrefixRaw() && raw.afterRandom().equals(math.afterRandom())
                ? Status.MATCHED_ORIGINAL_RAW_PROJECTION : Status.ORIGINAL_RAW_MISMATCH;
        return new Result(status, math, Optional.of(raw));
    }
    public static Result run(Input input) { return consume(produce(input)); }
    public static Result run(ObservedLoad observed) { return consume(produce(observed)); }
    public static NativeOnActionWeightProgram.RawValue weightOperand(Input input) {
        return weightOperand(input, run(input));
    }
    public static NativeOnActionWeightProgram.RawValue weightOperand(ObservedLoad observed) {
        return weightOperand(observed.original(), run(observed));
    }
    private static NativeOnActionWeightProgram.RawValue weightOperand(Input input, Result result) {
        return result.status() == Status.MATH_RECONSTRUCTED_NO_RAW_OBSERVATION || result.status() == Status.MATCHED_ORIGINAL_RAW_PROJECTION
            ? NativeScriptMathProgram.weightOperand(input.originalMath())
            : new NativeOnActionWeightProgram.DynamicRaw(1, "named producer/consumer unavailable or mismatched: " + result.status());
    }
    private static void pointer(BigInteger value) { NativeRawScriptValue.u64(value); StrictJson.require(value.signum() > 0, "nonzero original pointer required"); }
}
