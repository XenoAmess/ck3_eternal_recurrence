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
import static org.xar.ck3.control.wave2.events.nativepulse.NativeNamedScriptValueProgram.*;

class NativeNamedScriptValueProgramTest {
    private static final NativePlayableAnnualGate.Executable EXE = NativePlayableAnnualGate.Executable.exact(NativePlayableAnnualGate.EXECUTABLE_SHA256).orElseThrow();
    private static final BigInteger OBJECT = new BigInteger("18446744073709550002");
    private static final NativeRawScriptValue.Context CONTEXT = new NativeRawScriptValue.Context(new NativeRawScriptValue.Scope(BigInteger.ONE, BigInteger.TEN), BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO, 0);
    private static NativeRawScriptValue.Input operand(ExactRef ref, long raw) {
        return new NativeRawScriptValue.Input(EXE, ref, ref, new NativeRawScriptValue.Pdx(0, raw, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of()), CONTEXT, Optional.empty(), List.of(), List.of());
    }
    private static Input input(ExactRef ref) {
        var root = new NativeScriptMathProgram.Root(OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, NativeScriptMathProgram.MATH_BASE_VTABLE_RVA, NativeScriptMathProgram.Entry.NAMED_VALUE_70_375438F);
        var math = new NativeScriptMathProgram.Input(EXE, ref, root, CONTEXT, Optional.empty(), List.of(new NativeScriptMathProgram.SimpleField(0x2d2, ref, operand(ref, 150000)), new NativeScriptMathProgram.SimpleField(0x4f3, ref, operand(ref, 50000))));
        return new Input(ref, 3, new Before(new BigInteger("9007199254740993"), PRIMARY_VTABLE, SECONDARY_VTABLE, 999, true, Optional.of(BigInteger.valueOf(77))), math, Optional.empty());
    }
    private static Input withRaw(Input input, ExactRef ref, Optional<Long> observed) {
        var after = produce(input).after(); var leaf = after.dynamic70().orElseThrow();
        var calls = observed.isEmpty() ? List.<NativeRawScriptValue.OriginalRawCall>of() : List.of(new NativeRawScriptValue.OriginalRawCall(leaf, CONTEXT, Optional.empty(), Optional.empty(), observed.orElseThrow(), ref));
        var raw = new NativeRawScriptValue.Input(EXE, ref, ref, new NativeRawScriptValue.Pdx(3, -17, 0, Optional.of(after), Optional.empty(), Optional.empty(), List.of()), CONTEXT, Optional.empty(), calls, List.of());
        return new Input(input.originalLoadSource(), 3, input.before(), input.originalMath(), Optional.of(raw));
    }
    @Test void actualWriterProducerToMathRawAndWeightedConsumers() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve("synthetic original definition and callback fixture".getBytes(StandardCharsets.UTF_8)); Input input = withRaw(input(ref), ref, Optional.of(200000L));
        Produced produced = produce(input); assertEquals(Optional.of(BigInteger.valueOf(77)), produced.destroyedOld70()); assertTrue(produced.afterFlag7C());
        assertEquals(999, produced.after().storedRaw68()); assertTrue(produced.after().rawReady7B()); assertEquals(OBJECT, produced.after().dynamic70().orElseThrow().objectAddressU64());
        Result result = run(input); assertEquals(Status.MATCHED_ORIGINAL_RAW_PROJECTION, result.status()); assertEquals(200000L, result.raw().orElseThrow().raw().orElseThrow().longValue());
        var modifier = new NativeOnActionWeightProgram.TriggerModifier(new NativeOnActionWeightProgram.Always(new NativeOnActionWeightProgram.InlineBool(true)), weightOperand(input), new NativeOnActionWeightProgram.InlineRaw(0));
        var review = new NativeOnActionWeightProgram.Review(EXE, new NativeOnActionWeightProgram.Context(0, NativeOnActionWeightProgram.ScopeVerdict.VALIDATED), List.of(new NativeOnActionWeightProgram.RowSource(3, 20, Optional.of(new NativeOnActionWeightProgram.Definition(Optional.empty(), Optional.of(new NativeOnActionWeightProgram.Program(100000, List.of(modifier))))))), 0);
        var computed = assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, NativeOnActionWeightProgram.analyze(NativeOnActionWeightProgram.decode(NativeOnActionWeightProgram.encode(review))).computation());
        assertEquals(40, computed.rows().getFirst().nativeWeight()); assertTrue(result.staticKindThreeWriterRouteReviewed()); assertFalse(result.completeNativeAst()); assertFalse(result.currentLoadedSourceQualified()); assertFalse(result.nativeGameExecuted());
    }
    @Test void missingRawProjectionAndMismatchNeverBecomeNativeObservations() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve(new byte[]{1}); Input base = input(ref);
        assertEquals(Status.MATH_RECONSTRUCTED_NO_RAW_OBSERVATION, run(base).status());
        assertEquals(Status.UNKNOWN_RAW, run(withRaw(base, ref, Optional.empty())).status());
        assertEquals(Status.ORIGINAL_RAW_MISMATCH, run(withRaw(base, ref, Optional.of(199999L))).status());
        assertInstanceOf(NativeOnActionWeightProgram.DynamicRaw.class, weightOperand(withRaw(base, ref, Optional.empty())));
        Produced p = produce(base); assertThrows(IllegalArgumentException.class, () -> consume(new Produced(base, p.after(), Optional.empty(), true, p.math())));
        assertThrows(IllegalArgumentException.class, () -> new Input(ref, 2, base.before(), base.originalMath(), Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> new Before(BigInteger.ONE, PRIMARY_VTABLE, SECONDARY_VTABLE + 8, 0, false, Optional.empty()));
    }
    @Test void unaryLoadRetainsConstructorFieldsAndRejectsParsedDynamicOperand() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve(new byte[]{2}); Input base = input(ref);
        var unary = new NativeScriptMathProgram.SimpleField(0x548, ref, operand(ref, 0));
        var math = new NativeScriptMathProgram.Input(EXE, ref, base.originalMath().root(), CONTEXT, Optional.empty(), List.of(new NativeScriptMathProgram.SimpleField(0x2d2, ref, operand(ref, 150001)), unary));
        Input input = new Input(ref, 3, base.before(), math, Optional.empty()); assertEquals(200000, run(input).math().reconstructedPrefixRaw());
        assertEquals(0, run(input).math().applied().getLast().operandRaw());
        assertEquals(OperandLoad.CONSTRUCTOR_FIELDS_RETAINED, operandLoad(NativeScriptMathProgram.Operator.ABSOLUTE));
        assertEquals(OperandLoad.RAW_PDX_VIRTUAL_18, operandLoad(NativeScriptMathProgram.Operator.UNREVIEWED_CALLEE_8));
        assertThrows(IllegalArgumentException.class, () -> new NativeScriptMathProgram.SimpleField(0x548,ref,operand(ref,123)));
        var unknown = new NativeScriptMathProgram.Input(EXE, ref, math.root(), CONTEXT, Optional.empty(), List.of(new NativeScriptMathProgram.UnreviewedField(1234, ref, "actual unreviewed native node")));
        assertEquals(Status.UNKNOWN_MATH, run(new Input(ref, 3, base.before(), unknown, Optional.empty())).status());
    }
    @Test void uniqueNestedCodecsStrictFieldsAndDecimalIdentityRoundTrip() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve(new byte[]{3}); Input input = withRaw(input(ref), ref, Optional.of(200000L)); byte[] encoded = NativeNamedScriptValueProgramJson.encode(input);
        assertEquals(input, NativeNamedScriptValueProgramJson.decode(encoded)); assertArrayEquals(encoded, NativeNamedScriptValueProgramJson.encode(NativeNamedScriptValueProgramJson.decode(encoded)));
        List<Consumer<ObjectNode>> invalid = List.of(row -> row.remove("original_raw_consumer"), row -> row.put("lexical_kind_1c8", true), row -> row.put("lexical_kind_1c8", 3.0), row -> row.putNull("original_math"), row -> row.put("extra", 1),
            row -> row.withObject("before").put("definition_u64", 9007199254740993L), row -> row.withObject("before").put("dynamic_70_u64", "077"), row -> row.withObject("before").put("stored_raw_68", 999), row -> row.withObject("before").putNull("raw_ready_7b"));
        for (Consumer<ObjectNode> mutation : invalid) { ObjectNode row = (ObjectNode) StrictJson.parse(encoded, NativeScriptMathProgramJson.MAX_BYTES); mutation.accept(row); assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramJson.decode(row.toString().getBytes(StandardCharsets.UTF_8))); }
    }
    @Test void realProducerArchivesAllConsumersAndColdReplayRejectsNestedTampering() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve("synthetic exact input bytes".getBytes(StandardCharsets.UTF_8)); Input input = withRaw(input(ref), ref, Optional.of(200000L));
        var recorded = NativeNamedScriptValueProgramArchive.preserve(input, store); var cold = NativeNamedScriptValueProgramArchive.replay(NativeNamedScriptValueProgramArchive.decode(NativeNamedScriptValueProgramArchive.encode(recorded)), store);
        assertEquals(input, cold.original()); assertEquals(run(input), cold.recomputed()); assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class, weightOperand(cold.original()));
        var missingRaw = new NativeNamedScriptValueProgramArchive.Recorded(recorded.original(), recorded.derived(), recorded.math(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramArchive.replay(missingRaw, store));
        ExactRef wrong = store.preserve("{}".getBytes(StandardCharsets.UTF_8)); assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramArchive.replay(new NativeNamedScriptValueProgramArchive.Recorded(recorded.original(), wrong, recorded.math(), recorded.raw()), store));
        byte[] saved = store.contents.get(ref.path()); store.contents.put(ref.path(), new byte[]{9}); assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramArchive.replay(recorded, store)); store.contents.put(ref.path(), saved);
    }
    private static final class Store implements NativeOnActionFieldArchive.Store {
        private final Map<String, byte[]> contents = new HashMap<>(); private int sequence;
        @Override public ExactRef preserve(byte[] original) { try { byte[] bytes = original.clone(); String path = "memory/" + sequence++; contents.put(path, bytes); return new ExactRef(path, bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
            catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
        @Override public byte[] load(ExactRef ref) throws IOException { byte[] bytes = contents.get(ref.path()); if (bytes == null) throw new IOException("missing original fixture"); return bytes.clone(); }
    }
}
