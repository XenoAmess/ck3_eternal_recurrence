package org.xar.ck3.control.wave2.events.nativepulse;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionNameIndex.Name;

/**
 * One four-field producer -> postload -> dispatch-input consumer pipeline from the actual .4 reader ABI.
 * Inputs retain original token order and separately captured lookup/value observations. This does not
 * assert that a native loaded-object reader, VFS closure, reload generation or complete dispatcher exists.
 */
public final class NativeOnActionFields {
    public static final int EVENT_SIGNATURE = 0x4a6f4576;
    private NativeOnActionFields() { }
    public enum Field {
        EVENTS_0270(0x518, true, false), EVENTS_0258(0x519, true, true),
        ACTIONS_02B8(0x51b, false, false), ACTIONS_02A0(0x51c, false, true);
        private final int token; private final boolean event, first;
        Field(int token, boolean event, boolean first) { this.token = token; this.event = event; this.first = first; }
        public int nativeToken() { return token; } public boolean event() { return event; } public boolean firstValid() { return first; }
    }
    public enum Code { DUPLICATE_DELAY, INVALID_DELAY_UNIT, VALUE_NOT_WRITTEN, MINIMUM_EXCEEDS_MAXIMUM, INVALID_EVENT_REFERENCE, UNRESOLVED_ACTION_REFERENCE, EVENT_SCOPE_MISMATCH }
    public record Diagnostic(Field field, int block, int token, Code code) {
        public Diagnostic { Objects.requireNonNull(field); Objects.requireNonNull(code); }
    }
    /** The observed script-value object's +7A validity byte and signed int32 +60 value remain separate. */
    public record CompiledValue(BigInteger address, boolean integerReady, int integerValue) {
        public CompiledValue { NativeOnActionNameIndex.pointer(address); }
        public int currentInteger() { return integerReady ? integerValue : 0; }
    }
    /** Literal writes never silently erase an existing compiled pointer, and compiled writes retain the literal. */
    public sealed interface Write permits LiteralWrite, CompiledWrite, NoWrite { }
    public record LiteralWrite(int value) implements Write { }
    public record CompiledWrite(CompiledValue value) implements Write { public CompiledWrite { Objects.requireNonNull(value); } }
    public record NoWrite(String diagnosis) implements Write { public NoWrite { StrictJson.text(diagnosis); } }
    public sealed interface DelayUpdate permits Scalar, Range { }
    public record Scalar(Write value) implements DelayUpdate { public Scalar { Objects.requireNonNull(value); } }
    public record Range(Write minimum, Write maximum) implements DelayUpdate {
        public Range { Objects.requireNonNull(minimum); Objects.requireNonNull(maximum); }
    }
    public record Delay(int unitDays, int minimumLiteral, int maximumLiteral, Optional<CompiledValue> minimumCompiled, Optional<CompiledValue> maximumCompiled) {
        public Delay { Objects.requireNonNull(minimumCompiled); Objects.requireNonNull(maximumCompiled); }
        public static Delay initial() { return new Delay(0, -1, -1, Optional.empty(), Optional.empty()); }
    }
    public record EventTarget(BigInteger address, int signature, int rootScopeU16) {
        public EventTarget { NativeOnActionNameIndex.pointer(address); scope(rootScopeU16); }
    }
    public sealed interface Token permits DelayDirective, EventReference, ActionReference { }
    /** Numeric unit token is kept until its actual native mapping is proved; unsupported tokens follow native diagnostics. */
    public record DelayDirective(int nativeUnitToken, DelayUpdate update) implements Token {
        public DelayDirective { Objects.requireNonNull(update); }
    }
    public record EventReference(Name requestedName, Optional<EventTarget> originalLookup) implements Token {
        public EventReference { Objects.requireNonNull(requestedName); Objects.requireNonNull(originalLookup); }
    }
    public record ActionReference(Name requestedName) implements Token { public ActionReference { Objects.requireNonNull(requestedName); } }
    /** Each field occurrence constructs a fresh reader; existing definition vectors survive and are appended to. */
    public record Block(Field field, ExactRef originalSourcePiece, List<Token> tokens) {
        public Block { Objects.requireNonNull(field); Objects.requireNonNull(originalSourcePiece); tokens = List.copyOf(tokens);
            StrictJson.require(originalSourcePiece.bytes() > 0 && tokens.size() <= 8192, "bounded original source block required"); }
    }
    public record Predicate(Field field, int rowIndex, BigInteger address, boolean eligible) {
        public Predicate { Objects.requireNonNull(field); StrictJson.require(rowIndex >= 0, "original row index required"); NativeOnActionNameIndex.pointer(address); }
    }
    public record RandomState(long counterU32, long seedU32) {
        public RandomState { u32(counterU32); u32(seedU32); }
    }
    public record Input(NativePlayableAnnualGate.Executable executable, ExactRef originalObservation,
                        List<Block> originalBlocks, NativeOnActionNameIndex.Table actions,
                        int eventScopeBefore0258U16, List<Predicate> originalPredicates,
                        RandomState eventOriginalRandom, RandomState actionOriginalRandom) {
        public Input {
            Objects.requireNonNull(executable); Objects.requireNonNull(originalObservation);
            StrictJson.require(originalObservation.bytes() > 0, "nonempty original observation custody required");
            originalBlocks = List.copyOf(originalBlocks); Objects.requireNonNull(actions);
            scope(eventScopeBefore0258U16); originalPredicates = List.copyOf(originalPredicates);
            Objects.requireNonNull(eventOriginalRandom); Objects.requireNonNull(actionOriginalRandom);
            StrictJson.require(actions.executable() == executable && originalBlocks.size() <= 1024 && originalPredicates.size() <= 32768, "bounded same-build original inputs required");
            StrictJson.require(originalBlocks.stream().mapToLong(block -> block.tokens().size()).sum() <= 16384, "whole original token budget exceeded");
            var seen = new java.util.HashSet<String>();
            for (Predicate p : originalPredicates) StrictJson.require(seen.add(p.field().name() + ":" + p.rowIndex()), "repeated original predicate row");
        }
    }
    public sealed interface Row permits EventRow, ActionRow { Delay delay(); Name name(); }
    public record EventRow(Name name, EventTarget target, Delay delay) implements Row {
        public EventRow { Objects.requireNonNull(name); Objects.requireNonNull(target); Objects.requireNonNull(delay);
            StrictJson.require(target.signature() == EVENT_SIGNATURE, "only native event-signature rows can be appended"); }
    }
    public record ActionRow(Name name, Optional<BigInteger> resolvedAddress, Delay delay) implements Row {
        public ActionRow { Objects.requireNonNull(name); Objects.requireNonNull(resolvedAddress); resolvedAddress.ifPresent(NativeOnActionNameIndex::pointer); Objects.requireNonNull(delay); }
    }
    public record FieldRows(Field field, List<Row> rows) {
        public FieldRows { Objects.requireNonNull(field); rows = List.copyOf(rows);
            StrictJson.require(rows.size() <= 32768 && rows.stream().allMatch(row -> field.event() == (row instanceof EventRow)), "exact field reader row family required"); }
    }
    public record Produced(List<FieldRows> fields, List<Diagnostic> diagnostics) {
        public Produced { fields = List.copyOf(fields); diagnostics = List.copyOf(diagnostics);
            StrictJson.require(fields.stream().map(FieldRows::field).toList().equals(List.of(Field.values())), "all four fields in the one canonical order required"); }
        public List<Row> rows(Field field) { return fields.get(field.ordinal()).rows(); }
    }
    public record Postloaded(Produced definition, int eventScopeU16) { public Postloaded { Objects.requireNonNull(definition); scope(eventScopeU16); } }
    public record Emission(Field field, int rowIndex, BigInteger address, int delayDays) {
        public Emission { Objects.requireNonNull(field); NativeOnActionNameIndex.pointer(address); }
    }
    public enum ProjectionStatus { FOUR_FIELDS_RECONSTRUCTED, PREDICATE_UNAVAILABLE, NATIVE_DIVISOR_ZERO }
    public record Projection(Postloaded postloaded, List<Emission> emissions, RandomState afterEventRandom, RandomState afterActionRandom,
                             ProjectionStatus status, Optional<Field> unresolvedField, int unresolvedRow) {
        public Projection { Objects.requireNonNull(postloaded); emissions = List.copyOf(emissions); Objects.requireNonNull(afterEventRandom);
            Objects.requireNonNull(afterActionRandom); Objects.requireNonNull(status); Objects.requireNonNull(unresolvedField); }
        public boolean completeNativeDispatcher() { return false; }
        public boolean currentLoadedSourceQualified() { return false; }
        public boolean nativeGameExecuted() { return false; }
    }
    public static Produced produce(Input original) {
        Objects.requireNonNull(original); EnumMap<Field,List<Row>> fields = new EnumMap<>(Field.class);
        for (Field field : Field.values()) fields.put(field, new ArrayList<>());
        List<Diagnostic> diagnostics = new ArrayList<>();
        for (int b = 0; b < original.originalBlocks().size(); b++) {
            Block block = original.originalBlocks().get(b); Delay delay = Delay.initial();
            for (int t = 0; t < block.tokens().size(); t++) {
                Token token = block.tokens().get(t);
                if (token instanceof DelayDirective directive) {
                    // Named reader resets before checking the unit token; EventReader retains all old raw fields.
                    if (!block.field().event()) delay = Delay.initial();
                    int unit = unit(directive.nativeUnitToken());
                    if (unit == 0) { diagnostics.add(new Diagnostic(block.field(), b, t, Code.INVALID_DELAY_UNIT)); continue; }
                    if (delay.minimumLiteral() >= 0 || delay.minimumCompiled().isPresent()) diagnostics.add(new Diagnostic(block.field(), b, t, Code.DUPLICATE_DELAY));
                    delay = update(delay, unit, directive.update(), block.field(), b, t, diagnostics);
                } else if (token instanceof EventReference reference) {
                    StrictJson.require(block.field().event(), "event-reference token supplied to the named on-action reader");
                    if (reference.originalLookup().isEmpty() || reference.originalLookup().orElseThrow().signature() != EVENT_SIGNATURE)
                        diagnostics.add(new Diagnostic(block.field(), b, t, Code.INVALID_EVENT_REFERENCE));
                    else fields.get(block.field()).add(new EventRow(reference.requestedName(), reference.originalLookup().orElseThrow(), delay));
                } else {
                    StrictJson.require(!block.field().event(), "on-action name token supplied to the event reader");
                    fields.get(block.field()).add(new ActionRow(((ActionReference) token).requestedName(), Optional.empty(), delay));
                }
            }
        }
        return new Produced(java.util.Arrays.stream(Field.values()).map(field -> new FieldRows(field, fields.get(field))).toList(), diagnostics);
    }
    private static Delay update(Delay before, int unit, DelayUpdate update, Field field, int block, int token, List<Diagnostic> diagnostics) {
        Delay result;
        if (update instanceof Scalar scalar) {
            result = write(before, scalar.value(), true, field, block, token, diagnostics);
            result = new Delay(unit, result.minimumLiteral(), result.minimumLiteral(), result.minimumCompiled(), result.maximumCompiled());
        } else {
            Range range = (Range) update;
            result = write(before, range.minimum(), true, field, block, token, diagnostics);
            result = write(result, range.maximum(), false, field, block, token, diagnostics);
            result = new Delay(unit, result.minimumLiteral(), result.maximumLiteral(), result.minimumCompiled(), result.maximumCompiled());
            if (result.minimumLiteral() > result.maximumLiteral()) diagnostics.add(new Diagnostic(field, block, token, Code.MINIMUM_EXCEEDS_MAXIMUM));
        }
        return result;
    }
    private static Delay write(Delay before, Write write, boolean minimum, Field field, int block, int token, List<Diagnostic> diagnostics) {
        int lo = before.minimumLiteral(), hi = before.maximumLiteral(); Optional<CompiledValue> lc = before.minimumCompiled(), hc = before.maximumCompiled();
        if (write instanceof LiteralWrite literal) { if (minimum) lo = literal.value(); else hi = literal.value(); }
        else if (write instanceof CompiledWrite compiled) { if (minimum) lc = Optional.of(compiled.value()); else hc = Optional.of(compiled.value()); }
        else diagnostics.add(new Diagnostic(field, block, token, Code.VALUE_NOT_WRITTEN));
        return new Delay(before.unitDays(), lo, hi, lc, hc);
    }
    public static Postloaded postload(Input original, Produced produced) {
        Objects.requireNonNull(original); Objects.requireNonNull(produced); List<FieldRows> fields = new ArrayList<>(); List<Diagnostic> diagnostics = new ArrayList<>(produced.diagnostics());
        for (FieldRows field : produced.fields()) {
            List<Row> rows = new ArrayList<>();
            for (int r = 0; r < field.rows().size(); r++) {
                Row row = field.rows().get(r);
                if (row instanceof ActionRow action) {
                    Optional<BigInteger> found = action.name().text().isEmpty() ? Optional.empty() : NativeOnActionNameIndex.find(original.actions(), action.name()).map(NativeOnActionNameIndex.Entry::address);
                    if (!action.name().text().isEmpty() && found.isEmpty()) diagnostics.add(new Diagnostic(field.field(), -1, r, Code.UNRESOLVED_ACTION_REFERENCE));
                    rows.add(new ActionRow(action.name(), found, action.delay()));
                } else rows.add(row);
            }
            fields.add(new FieldRows(field.field(), rows));
        }
        // 37CB900 checks +240 first. This input is its exact accumulator BEFORE +258/+270; +240 is not reconstructed here.
        int scope = original.eventScopeBefore0258U16();
        for (Field field : List.of(Field.EVENTS_0258, Field.EVENTS_0270)) {
            List<Row> rows = fields.get(field.ordinal()).rows();
            for (int r = 0; r < rows.size(); r++) {
                int current = ((EventRow) rows.get(r)).target().rootScopeU16(); if (current == 0) continue;
                if (scope == 0) scope = current;
                else if (scope != current) diagnostics.add(new Diagnostic(field, -1, r, Code.EVENT_SCOPE_MISMATCH));
            }
        }
        return new Postloaded(new Produced(fields, diagnostics), scope);
    }
    private record Delayed(int days, RandomState after, boolean divisorZero) { }
    /** Original concrete consumers call all eligible +270/+2B8 rows, then the first eligible +258/+2A0 row. */
    public static Projection project(Input original, Postloaded postloaded) {
        List<Emission> emissions = new ArrayList<>(); RandomState events = original.eventOriginalRandom(), actions = original.actionOriginalRandom();
        for (Field field : Field.values()) {
            // The event consumer's later +240 weighted chooser is outside these fields and can consume RNG.
            // The action consumer therefore starts from its own original observation, never inferred here.
            RandomState random = field.event() ? events : actions;
            List<Row> rows = postloaded.definition().rows(field);
            for (int r = 0; r < rows.size(); r++) {
                Row row = rows.get(r); Optional<BigInteger> address = row instanceof EventRow event ? Optional.of(event.target().address()) : ((ActionRow) row).resolvedAddress();
                if (address.isEmpty()) continue;
                final int index = r;
                Optional<Predicate> predicate = original.originalPredicates().stream().filter(p -> p.field() == field && p.rowIndex() == index).findFirst();
                if (predicate.isEmpty()) return new Projection(postloaded, emissions, events, actions, ProjectionStatus.PREDICATE_UNAVAILABLE, Optional.of(field), r);
                StrictJson.require(predicate.orElseThrow().address().equals(address.orElseThrow()), "original predicate crossed the loaded row target");
                if (!predicate.orElseThrow().eligible()) continue;
                Delayed delay = delay(row.delay(), random); random = delay.after();
                if (field.event()) events = random; else actions = random;
                if (delay.divisorZero()) return new Projection(postloaded, emissions, events, actions, ProjectionStatus.NATIVE_DIVISOR_ZERO, Optional.of(field), r);
                emissions.add(new Emission(field, r, address.orElseThrow(), delay.days()));
                if (field.firstValid()) break;
            }
        }
        return new Projection(postloaded, emissions, events, actions, ProjectionStatus.FOUR_FIELDS_RECONSTRUCTED, Optional.empty(), -1);
    }
    private static Delayed delay(Delay delay, RandomState random) {
        int minimum = delay.unitDays() * delay.minimumCompiled().map(CompiledValue::currentInteger).orElse(delay.minimumLiteral());
        if (delay.maximumLiteral() < 0 && delay.maximumCompiled().isEmpty()) return new Delayed(minimum, random, false);
        int maximum = delay.unitDays() * delay.maximumCompiled().map(CompiledValue::currentInteger).orElse(delay.maximumLiteral());
        if (minimum > maximum) return new Delayed(0, random, false);
        int value = (int) random.seedU32() - (int) random.counterU32() * 0x4ad685b3;
        value = (value ^ (value >>> 8)) + 0x68e31da4;
        value ^= value << 8; value *= 0x1b56c4e9; value ^= value >>> 8; value *= 0x92d68ca2; value ^= value >>> 8;
        RandomState after = new RandomState((random.counterU32() + 1) & 0xffffffffL, random.seedU32());
        int width = maximum - minimum + 1;
        if (width == 0) return new Delayed(0, after, true);
        return new Delayed(minimum + ((value & Integer.MAX_VALUE) % width), after, false);
    }
    private static int unit(int token) { return switch (token) { case 0x514 -> 1; case 0x515 -> 30; case 0x516 -> 365; case 0x52f -> 7; default -> 0; }; }
    private static void scope(int value) { StrictJson.require(value >= 0 && value <= 65535, "native scope uint16 required"); }
    private static void u32(long value) { StrictJson.require(value >= 0 && value <= 0xffffffffL, "native random uint32 required"); }
}
