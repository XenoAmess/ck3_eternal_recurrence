package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFields.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionNameIndex.*;

final class NativeOnActionFieldsTest {
    private static final NativePlayableAnnualGate.Executable EXE = NativePlayableAnnualGate.Executable.exact(NativePlayableAnnualGate.EXECUTABLE_SHA256).orElseThrow();
    private static final Field EVENTS = Field.EVENTS_0270, FIRST_EVENT = Field.EVENTS_0258, ACTIONS = Field.ACTIONS_02B8;
    private static final BigInteger EVENT_A = new BigInteger("18446744073709550001"), EVENT_B = new BigInteger("18446744073709550002"), ACTION = new BigInteger("18446744073709550003");
    @Test void actualHashUnsignedIndexCollisionAndExactCase() {
        assertEquals(0, hash(new Name(""))); assertEquals(4138058784L, hash(new Name("foo")));
        assertEquals(613153351L, hash(new Name("hello"))); assertEquals(1319662467L, hash(new Name("Foo")));
        assertEquals(374375328L, hash(new Name("on_yearly_pulse")));
        Name a = new Name("on_action_36633"), b = new Name("on_action_43549");
        assertEquals(3609448875L, hash(a)); assertEquals(hash(a), hash(b));
        Table table = table(List.of(entry(b, 20), entry(a, 10), entry(new Name("foo"), 30), entry(new Name("Foo"), 40)));
        assertEquals(BigInteger.TEN, find(table, a).orElseThrow().address());
        assertEquals(BigInteger.valueOf(20), find(table, b).orElseThrow().address());
        assertEquals(BigInteger.valueOf(40), find(table, new Name("Foo")).orElseThrow().address());
        assertTrue(find(table, new Name("FOO")).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> new Table(EXE, table.definitions(), List.of(1L)));
        assertThrows(IllegalArgumentException.class, () -> new Name("bad\0tail"));
        assertThrows(IllegalArgumentException.class, () -> new Name("\ud800"));
    }
    @Test void eventWritesRetainRawCompiledFieldsAcrossDuplicateDelaysAndAppendOccurrences() {
        ExactRef ref = fakeRef();
        CompiledValue lo = new CompiledValue(BigInteger.valueOf(80), true, 9), hi = new CompiledValue(BigInteger.valueOf(81), true, 12);
        Block first = new Block(EVENTS, ref, List.of(new DelayDirective(0x514, new Range(new CompiledWrite(lo), new CompiledWrite(hi))), event(EVENT_A, 5),
            new DelayDirective(0x514, new Scalar(new LiteralWrite(3))), event(EVENT_B, 5), new DelayDirective(0x777, new Scalar(new LiteralWrite(99))), event(EVENT_A, 5),
            new DelayDirective(0x514, new Range(new NoWrite("bad original value"), new LiteralWrite(20))), event(EVENT_B, 5),
            new EventReference(new Name("absent"), Optional.empty()), new EventReference(new Name("bad-signature"), Optional.of(new EventTarget(BigInteger.ONE, 0, 5)))));
        Input input = input(List.of(first, new Block(EVENTS, ref, List.of(event(EVENT_A, 5)))), emptyTable(), List.of());
        Produced produced = produce(input); assertEquals(5, produced.rows(EVENTS).size());
        Delay initial = produced.rows(EVENTS).get(0).delay(), changed = produced.rows(EVENTS).get(1).delay();
        assertEquals(-1, initial.minimumLiteral()); assertEquals(Optional.of(lo), initial.minimumCompiled());
        assertEquals(3, changed.minimumLiteral()); assertEquals(3, changed.maximumLiteral());
        assertEquals(Optional.of(lo), changed.minimumCompiled()); assertEquals(Optional.of(hi), changed.maximumCompiled());
        assertEquals(changed, produced.rows(EVENTS).get(2).delay());
        assertEquals(3, produced.rows(EVENTS).get(3).delay().minimumLiteral()); assertEquals(20, produced.rows(EVENTS).get(3).delay().maximumLiteral());
        assertEquals(Delay.initial(), produced.rows(EVENTS).get(4).delay());
        assertEquals(2, produced.diagnostics().stream().filter(d -> d.code() == Code.DUPLICATE_DELAY).count());
        assertEquals(2, produced.diagnostics().stream().filter(d -> d.code() == Code.INVALID_EVENT_REFERENCE).count());
        assertTrue(produced.diagnostics().stream().anyMatch(d -> d.code() == Code.VALUE_NOT_WRITTEN));
    }
    @Test void namedReaderResetsBeforeEvenInvalidUnitAndPostloadKeepsMissingAndEmptyDistinct() {
        var ref = fakeRef(); Input input = input(List.of(new Block(ACTIONS, ref, List.of(
            new DelayDirective(0x515, new Scalar(new CompiledWrite(new CompiledValue(BigInteger.TEN, true, 5)))), action("go"),
            new DelayDirective(0x777, new Scalar(new LiteralWrite(99))), action("go"), action("missing"), action("")))),
            table(List.of(new Entry(new Name("go"), ACTION, hash(new Name("go"))))), List.of());
        Postloaded loaded = postload(input, produce(input)); List<Row> rows = loaded.definition().rows(ACTIONS);
        assertEquals(30, rows.get(0).delay().unitDays()); assertEquals(-1, rows.get(0).delay().maximumLiteral());
        assertTrue(rows.get(0).delay().maximumCompiled().isEmpty());
        assertEquals(Delay.initial(), rows.get(1).delay());
        assertEquals(Optional.of(ACTION), ((ActionRow) rows.get(0)).resolvedAddress());
        assertTrue(((ActionRow) rows.get(2)).resolvedAddress().isEmpty()); assertTrue(((ActionRow) rows.get(3)).resolvedAddress().isEmpty());
        assertEquals(1, loaded.definition().diagnostics().stream().filter(d -> d.code() == Code.UNRESOLVED_ACTION_REFERENCE).count());
    }
    @Test void scopePrefixRetainsFirstValueAndMismatchDiagnosesWithoutDroppingRows() {
        Input original = input(List.of(new Block(EVENTS, fakeRef(), List.of(event(EVENT_A, 5))), new Block(FIRST_EVENT, fakeRef(), List.of(event(EVENT_B, 7)))), emptyTable(), List.of());
        Input input = new Input(EXE, original.originalObservation(), original.originalBlocks(), original.actions(), 3, original.originalPredicates(), original.eventOriginalRandom(), original.actionOriginalRandom());
        Postloaded loaded = postload(input, produce(input)); assertEquals(3, loaded.eventScopeU16());
        assertEquals(2, loaded.definition().diagnostics().stream().filter(d -> d.code() == Code.EVENT_SCOPE_MISMATCH).count());
        assertEquals(1, loaded.definition().rows(EVENTS).size()); assertEquals(1, loaded.definition().rows(FIRST_EVENT).size());
    }
    @Test void concreteConsumersUseIndependentOriginalRandomStatesAroundExcludedWeightedChooser() {
        Input input = input(List.of(new Block(EVENTS, fakeRef(), List.of(range(1, 9), event(EVENT_A, 0))),
            new Block(ACTIONS, fakeRef(), List.of(range(1, 9), action("go")))), table(List.of(new Entry(new Name("go"), ACTION, hash(new Name("go"))))),
            List.of(new Predicate(EVENTS, 0, EVENT_A, true), new Predicate(ACTIONS, 0, ACTION, true)));
        Projection projection = NativeOnActionFieldArchive.run(input);
        assertEquals(List.of(1, 6), projection.emissions().stream().map(Emission::delayDays).toList());
        assertEquals(new RandomState(8, 123), projection.afterEventRandom()); assertEquals(new RandomState(100, 456), projection.afterActionRandom());
        assertEquals(ProjectionStatus.FOUR_FIELDS_RECONSTRUCTED, projection.status());
        assertFalse(projection.completeNativeDispatcher()); assertFalse(projection.currentLoadedSourceQualified()); assertFalse(projection.nativeGameExecuted());
    }
    @Test void allEligibleAndFirstEligiblePreserveOrderAndUnknownFirstCannotBeSkipped() {
        List<Block> blocks = List.of(new Block(EVENTS, fakeRef(), List.of(event(EVENT_A, 0), event(EVENT_B, 0), event(EVENT_A, 0))),
            new Block(FIRST_EVENT, fakeRef(), List.of(event(EVENT_A, 0), event(EVENT_B, 0))));
        List<Predicate> predicates = List.of(new Predicate(EVENTS, 0, EVENT_A, false), new Predicate(EVENTS, 1, EVENT_B, true), new Predicate(EVENTS, 2, EVENT_A, true),
            new Predicate(FIRST_EVENT, 0, EVENT_A, true), new Predicate(FIRST_EVENT, 1, EVENT_B, true));
        Projection complete = NativeOnActionFieldArchive.run(input(blocks, emptyTable(), predicates));
        assertEquals(List.of(EVENT_B, EVENT_A, EVENT_A), complete.emissions().stream().map(Emission::address).toList());
        Projection unknown = NativeOnActionFieldArchive.run(input(List.of(blocks.get(1)), emptyTable(), List.of(predicates.get(4))));
        assertEquals(ProjectionStatus.PREDICATE_UNAVAILABLE, unknown.status()); assertEquals(0, unknown.unresolvedRow()); assertTrue(unknown.emissions().isEmpty());
        assertThrows(IllegalArgumentException.class, () -> NativeOnActionFieldArchive.run(input(List.of(blocks.get(0)), emptyTable(), List.of(new Predicate(EVENTS, 0, EVENT_B, true)))));
    }
    @Test void delayNativeInt32CasesKeepCounterFaultAndNoRangePathsDistinct() {
        List<Predicate> predicates = List.of(new Predicate(EVENTS, 0, EVENT_A, true));
        Projection inverted = NativeOnActionFieldArchive.run(input(List.of(new Block(EVENTS, fakeRef(), List.of(range(4, 2), event(EVENT_A, 0)))), emptyTable(), predicates));
        assertEquals(0, inverted.emissions().getFirst().delayDays()); assertEquals(new RandomState(7, 123), inverted.afterEventRandom());
        Projection fault = NativeOnActionFieldArchive.run(input(List.of(new Block(EVENTS, fakeRef(), List.of(range(Integer.MIN_VALUE, Integer.MAX_VALUE), event(EVENT_A, 0)))), emptyTable(), predicates));
        assertEquals(ProjectionStatus.NATIVE_DIVISOR_ZERO, fault.status()); assertTrue(fault.emissions().isEmpty()); assertEquals(new RandomState(8, 123), fault.afterEventRandom());
        Input raw = input(List.of(new Block(EVENTS, fakeRef(), List.of(range(1, 9), event(EVENT_A, 0)))), emptyTable(), predicates);
        Input wrapped = new Input(EXE, raw.originalObservation(), raw.originalBlocks(), raw.actions(), 0, predicates, new RandomState(0xffffffffL, 0xffffffffL), raw.actionOriginalRandom());
        Projection wrap = NativeOnActionFieldArchive.run(wrapped); assertEquals(8, wrap.emissions().getFirst().delayDays()); assertEquals(0, wrap.afterEventRandom().counterU32());
        Input noRange = input(List.of(new Block(EVENTS, fakeRef(), List.of(new DelayDirective(0x516, new Scalar(new CompiledWrite(new CompiledValue(BigInteger.TEN, false, 123)))), event(EVENT_A, 0)))), emptyTable(), predicates);
        Projection notReady = NativeOnActionFieldArchive.run(noRange); assertEquals(0, notReady.emissions().getFirst().delayDays()); assertEquals(new RandomState(7, 123), notReady.afterEventRandom());
    }
    @Test void exactOriginalCodecRejectsCoercionMissingNullExtraAndWrongHash() {
        Input original = input(List.of(new Block(EVENTS, fakeRef(), List.of(event(EVENT_A, 0)))), emptyTable(), List.of(new Predicate(EVENTS, 0, EVENT_A, true)));
        byte[] encoded = NativeOnActionFieldsJson.encode(original); assertEquals(original, NativeOnActionFieldsJson.decode(encoded));
        ObjectNode root = json(encoded); root.put("event_scope_before_0258_u16", true); rejects(root);
        root = json(encoded); root.put("event_scope_before_0258_u16", 1.0); rejects(root);
        root = json(encoded); root.remove("original_predicates"); rejects(root);
        root = json(encoded); root.putNull("original_blocks"); rejects(root);
        root = json(encoded); root.put("unknown", 1); rejects(root);
        root = json(encoded); root.withObject("event_original_random").put("counter_u32", "07"); rejects(root);
        root = json(encoded); root.withObject("event_original_random").put("seed_u32", 123); rejects(root);
        root = json(encoded); ((ObjectNode) root.withArray("original_predicates").get(0)).put("eligible", 1); rejects(root);
        root = json(encoded); ((ObjectNode) ((ArrayNode) ((ObjectNode) root.withArray("original_blocks").get(0)).get("tokens")).get(0)).withObject("original_lookup").put("address_u64", 10); rejects(root);
        root = json(encoded); root.put("exe_sha256", "0".repeat(64)); rejects(root);
        Table table = table(List.of(entry(new Name("go"), 10))); Input withTable = input(List.of(), table, List.of());
        root = json(NativeOnActionFieldsJson.encode(withTable)); ((ObjectNode) root.withObject("action_name_index").withArray("definitions").get(0)).put("native_hash_u32", "0"); rejects(root);
    }
    @Test void originalProducerAllConsumersArchiveColdReplayAndTamperUseOnePipeline() throws Exception {
        MemoryStore store = new MemoryStore(); ExactRef observation = store.preserve("original independent values and frame".getBytes(StandardCharsets.UTF_8));
        ExactRef source = store.preserve("events={ foo }".getBytes(StandardCharsets.UTF_8));
        Input input = new Input(EXE, observation, List.of(new Block(EVENTS, source, List.of(range(1, 9), event(EVENT_A, 4)))), emptyTable(), 0,
            List.of(new Predicate(EVENTS, 0, EVENT_A, true)), new RandomState(7, 123), new RandomState(99, 456));
        NativeOnActionFieldArchive.Recorded recorded = NativeOnActionFieldArchive.preserve(input, store);
        byte[] persisted = NativeOnActionFieldArchive.encode(recorded);
        var cold = NativeOnActionFieldArchive.replay(NativeOnActionFieldArchive.decode(persisted), store);
        assertEquals(input, cold.original()); assertEquals(1, cold.recomputed().emissions().getFirst().delayDays());
        assertArrayEquals(NativeOnActionFieldsJson.encode(NativeOnActionFieldArchive.run(input)), NativeOnActionFieldsJson.encode(cold.recomputed()));
        ExactRef wrongDerived = store.preserve("{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeOnActionFieldArchive.replay(new NativeOnActionFieldArchive.Recorded(recorded.original(), wrongDerived), store));
        byte[] old = store.contents.get(source.path()); store.contents.put(source.path(), "different".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeOnActionFieldArchive.replay(recorded, store)); store.contents.put(source.path(), old);
        store.contents.put(recorded.original().path(), "{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class, () -> NativeOnActionFieldArchive.replay(recorded, store));
    }
    private static Input input(List<Block> blocks, Table table, List<Predicate> predicates) { return new Input(EXE, fakeRef(), blocks, table, 0, predicates, new RandomState(7, 123), new RandomState(99, 456)); }
    private static Table emptyTable() { return new Table(EXE, List.of(), List.of()); }
    private static Table table(List<Entry> entries) { List<Entry> sorted = new ArrayList<>(entries); sorted.sort(Comparator.comparingLong(Entry::nativeHashU32));
        return new Table(EXE, sorted, sorted.stream().map(Entry::nativeHashU32).toList()); }
    private static Entry entry(Name name, long pointer) { return new Entry(name, BigInteger.valueOf(pointer), hash(name)); }
    private static ExactRef fakeRef() { return new ExactRef("source-only-fixture", 1, "0".repeat(64)); }
    private static EventReference event(BigInteger address, int scope) { return new EventReference(new Name("event_" + address), Optional.of(new EventTarget(address, EVENT_SIGNATURE, scope))); }
    private static ActionReference action(String name) { return new ActionReference(new Name(name)); }
    private static DelayDirective range(int minimum, int maximum) { return new DelayDirective(0x514, new Range(new LiteralWrite(minimum), new LiteralWrite(maximum))); }
    private static ObjectNode json(byte[] raw) { return (ObjectNode) StrictJson.parse(raw, NativeOnActionFieldsJson.MAX_BYTES); }
    private static void rejects(ObjectNode root) { assertThrows(IllegalArgumentException.class, () -> NativeOnActionFieldsJson.decode(root.toString().getBytes(StandardCharsets.UTF_8))); }
    private static final class MemoryStore implements NativeOnActionFieldArchive.Store {
        private final Map<String,byte[]> contents = new HashMap<>(); private int sequence;
        @Override public ExactRef preserve(byte[] raw) {
            try { String path = "memory/" + sequence++; byte[] bytes = raw.clone(); contents.put(path, bytes);
                return new ExactRef(path, bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
            catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        }
        @Override public byte[] load(ExactRef ref) throws IOException { byte[] bytes = contents.get(ref.path()); if (bytes == null) throw new IOException("missing original"); return bytes.clone(); }
    }
}
