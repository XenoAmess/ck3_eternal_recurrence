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

class NativeNamedLoadFinalizerRegressionTest {
    private static final BigInteger OBJECT = new BigInteger("18446744073709550002");
    private static final List<BigInteger> NODES = List.of(new BigInteger("9007199254740993"), new BigInteger("18446744073709550003"));
    private static Input input(ExactRef ref) {
        var exe = NativePlayableAnnualGate.Executable.exact(NativePlayableAnnualGate.EXECUTABLE_SHA256).orElseThrow();
        var context = new NativeRawScriptValue.Context(new NativeRawScriptValue.Scope(BigInteger.ONE, BigInteger.TEN), BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO, 0);
        var operand = new NativeRawScriptValue.Input(exe, ref, ref, new NativeRawScriptValue.Pdx(0, 200000, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of()), context, Optional.empty(), List.of(), List.of());
        var math = new NativeScriptMathProgram.Input(exe, ref, new NativeScriptMathProgram.Root(OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, NativeScriptMathProgram.MATH_BASE_VTABLE_RVA, NativeScriptMathProgram.Entry.NAMED_VALUE_70_375438F), context, Optional.empty(), List.of(new NativeScriptMathProgram.SimpleField(0x2d2, ref, operand), new NativeScriptMathProgram.SimpleField(0x2a4, ref, operand)));
        Input base = new Input(ref, 3, new Before(BigInteger.TEN, PRIMARY_VTABLE, SECONDARY_VTABLE, 0, false, Optional.empty()), math, Optional.empty());
        var after = produce(base).after(); var call = new NativeRawScriptValue.OriginalRawCall(after.dynamic70().orElseThrow(), context, Optional.empty(), Optional.empty(), 200000, ref);
        var raw = new NativeRawScriptValue.Input(exe, ref, ref, new NativeRawScriptValue.Pdx(3, -9, 0, Optional.of(after), Optional.empty(), Optional.empty(), List.of()), context, Optional.empty(), List.of(call), List.of());
        return new Input(ref, 3, base.before(), math, Optional.of(raw));
    }
    private static LoadObservation observation(ExactRef ref) { return new LoadObservation(ref, OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, MATH_FINALIZER_RVA, NODES, NODES); }
    @Test void originalProducerAllConsumersNewAndLegacyArchiveRoundTrips() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve("synthetic original loader/vector/callback fixture".getBytes(StandardCharsets.UTF_8)); Input input = input(ref);
        ObservedLoad source = new ObservedLoad(input, observation(ref)); byte[] original = NativeNamedScriptValueProgramJson.encode(source);
        ObservedLoad decoded = NativeNamedScriptValueProgramJson.decodeObserved(original); assertEquals(source, decoded); assertArrayEquals(original, NativeNamedScriptValueProgramJson.encode(decoded));
        assertEquals(produce(input), produce(decoded)); assertEquals(Status.MATCHED_ORIGINAL_RAW_PROJECTION, run(decoded).status()); assertEquals(run(input), run(decoded));
        assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class, weightOperand(decoded));
        var modifier = new NativeOnActionWeightProgram.TriggerModifier(new NativeOnActionWeightProgram.Always(new NativeOnActionWeightProgram.InlineBool(true)), weightOperand(decoded), new NativeOnActionWeightProgram.InlineRaw(0));
        var review = new NativeOnActionWeightProgram.Review(input.originalMath().executable(), new NativeOnActionWeightProgram.Context(0, NativeOnActionWeightProgram.ScopeVerdict.VALIDATED), List.of(new NativeOnActionWeightProgram.RowSource(3, 20, Optional.of(new NativeOnActionWeightProgram.Definition(Optional.empty(), Optional.of(new NativeOnActionWeightProgram.Program(100000, List.of(modifier))))))), 0);
        var weighted = assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, NativeOnActionWeightProgram.analyze(NativeOnActionWeightProgram.decode(NativeOnActionWeightProgram.encode(review))).computation()); assertEquals(40, weighted.rows().getFirst().nativeWeight());
        var record = NativeNamedScriptValueProgramArchive.preserve(decoded, store);
        var cold = NativeNamedScriptValueProgramArchive.replay(NativeNamedScriptValueProgramArchive.decodeObserved(NativeNamedScriptValueProgramArchive.encode(record)), store);
        assertEquals(source, cold.original()); assertEquals(run(source), cold.recomputed());
        var legacy = NativeNamedScriptValueProgramArchive.decode(NativeNamedScriptValueProgramArchive.encode(record.named())); assertEquals(input, NativeNamedScriptValueProgramArchive.replay(legacy, store).original());
        assertFalse(cold.recomputed().currentLoadedSourceQualified()); assertFalse(cold.recomputed().completeNativeAst()); assertFalse(cold.recomputed().nativeGameExecuted());
    }
    @Test void realObjectSlotAndOrderedNodeIdentityAreRequiredBeforeProducer() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve(new byte[]{1}); Input source = input(ref);
        assertThrows(IllegalArgumentException.class, () -> new ObservedLoad(source, new LoadObservation(ref, OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, MATH_FINALIZER_RVA, NODES, List.of(NODES.get(1), NODES.get(0)))));
        assertThrows(IllegalArgumentException.class, () -> new ObservedLoad(source, new LoadObservation(ref, OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, MATH_FINALIZER_RVA, List.of(), List.of())));
        assertThrows(IllegalArgumentException.class, () -> new ObservedLoad(source, new LoadObservation(ref, BigInteger.ONE, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, MATH_FINALIZER_RVA, NODES, NODES)));
        assertThrows(IllegalArgumentException.class, () -> new LoadObservation(ref, OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA, MATH_FINALIZER_RVA + 1, NODES, NODES));
        assertThrows(IllegalArgumentException.class, () -> new LoadObservation(ref, OBJECT, NativeScriptMathProgram.MATH_PRIMARY_VTABLE_RVA + 8, MATH_FINALIZER_RVA, NODES, NODES));
    }
    @Test void strictObservationWireRejectsCoercionsMissingAndInventedReturnBoolean() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve(new byte[]{2}); byte[] original = NativeNamedScriptValueProgramJson.encode(new ObservedLoad(input(ref), observation(ref)));
        List<Consumer<ObjectNode>> invalid = List.of(row -> row.remove("observation"), row -> row.putNull("original"), row -> row.withObject("observation").put("math_object_u64", 12L),
            row -> row.withObject("observation").put("finalizer_slot_28_rva", true), row -> row.withObject("observation").put("finalizer_slot_28_rva", 8522.0),
            row -> row.withObject("observation").put("callback_return", true), row -> row.withObject("observation").putNull("nodes_before_u64"),
            row -> row.withObject("observation").putArray("nodes_after_u64").add("09007199254740993"), row -> row.withObject("observation").putArray("nodes_before_u64").add(9007199254740993L));
        for (Consumer<ObjectNode> mutation : invalid) { var row = (ObjectNode) StrictJson.parse(original, NativeScriptMathProgramJson.MAX_BYTES); mutation.accept(row); assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramJson.decodeObserved(row.toString().getBytes(StandardCharsets.UTF_8))); }
    }
    @Test void coldReplayReadsOriginalObservationAndBindsSameNestedNamedProducer() throws Exception {
        Store store = new Store(); ExactRef ref = store.preserve("fixture input".getBytes(StandardCharsets.UTF_8)); ObservedLoad input = new ObservedLoad(input(ref), observation(ref));
        var record = NativeNamedScriptValueProgramArchive.preserve(input, store); ExactRef other = store.preserve("other exact input".getBytes(StandardCharsets.UTF_8));
        var different = NativeNamedScriptValueProgramArchive.preserve(input(other), store);
        assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramArchive.replay(new NativeNamedScriptValueProgramArchive.ObservedRecorded(record.original(), different), store));
        byte[] saved = store.contents.get(ref.path()); store.contents.put(ref.path(), new byte[]{9}); assertThrows(IllegalArgumentException.class, () -> NativeNamedScriptValueProgramArchive.replay(record, store)); store.contents.put(ref.path(), saved);
        assertEquals(run(input), NativeNamedScriptValueProgramArchive.replay(record, store).recomputed());
    }
    private static final class Store implements NativeOnActionFieldArchive.Store {
        private final Map<String, byte[]> contents = new HashMap<>(); private int next;
        @Override public ExactRef preserve(byte[] value) { try { byte[] bytes = value.clone(); String path = "memory/" + next++; contents.put(path, bytes); return new ExactRef(path, bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
            catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
        @Override public byte[] load(ExactRef ref) throws IOException { byte[] value = contents.get(ref.path()); if (value == null) throw new IOException("missing original fixture"); return value.clone(); }
    }
}
