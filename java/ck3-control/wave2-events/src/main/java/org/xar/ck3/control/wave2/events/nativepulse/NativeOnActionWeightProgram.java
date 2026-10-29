package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Offline .4 concrete semantics feeding the existing weighted-index consumer.
 * No native AST receipt, loaded identity, cache, RNG or dispatch credit.
 * ScopeVerdict is supplied review input for 372E000, never inferred here.
 */
public final class NativeOnActionWeightProgram {
    public static final String SCHEMA = "xar.on-action-weight-program-review/v1";
    private static final int MAX_BYTES = 131072, MAX_DEPTH = 32, MAX_NODES = 4096, MAX_CHILDREN = 512;
    private static final long SAFE_PRODUCT_OPERAND = 3037000499L;
    private NativeOnActionWeightProgram() { }

    public enum ScopeVerdict { VALIDATED, REJECTED, UNRESOLVED }
    public record Context(int mode, ScopeVerdict rootScope) {
        public Context { StrictJson.require(mode >= 0 && mode <= 4, "reviewed context mode 0..4 required"); Objects.requireNonNull(rootScope); }
    }
    public sealed interface Trigger permits And, Or, Always, UnreviewedTrigger { }
    /** Native child pointer vectors at +40/count+4C and +88/count+94, in original order. */
    public record And(List<Trigger> children40, List<Trigger> children88) implements Trigger {
        public And { children40 = children(children40); children88 = children(children88); }
    }
    public record Or(List<Trigger> children40, List<Trigger> children88) implements Trigger {
        public Or { children40 = children(children40); children88 = children(children88); }
    }
    public sealed interface BoolValue permits InlineBool, DynamicBool { }
    /** 1B2E210: native kind at +B8 is zero, bool byte at +98. */
    public record InlineBool(boolean value) implements BoolValue { }
    public record DynamicBool(int nativeKind, String diagnosis) implements BoolValue {
        public DynamicBool { nonzeroKind(nativeKind); diagnosis = diagnosisText(diagnosis); }
    }
    /** CAlwaysTrigger's actual +D8 virtual returns true; its +C8 compares against the Pdx bool value. */
    public record Always(BoolValue value) implements Trigger { public Always { Objects.requireNonNull(value); } }
    public record UnreviewedTrigger(String diagnosis) implements Trigger {
        public UnreviewedTrigger { diagnosis = diagnosisText(diagnosis); }
    }
    public sealed interface RawValue permits InlineRaw, DynamicRaw { }
    /** 9D7060: native kind at +C0 is zero, signed raw qword at +98. */
    public record InlineRaw(long raw) implements RawValue { }
    public record DynamicRaw(int nativeKind, String diagnosis) implements RawValue {
        public DynamicRaw { nonzeroKind(nativeKind); diagnosis = diagnosisText(diagnosis); }
    }
    public sealed interface Modifier permits TriggerModifier, FirstValid, UnreviewedModifier { }
    /** CTriggerValueModifier +48 condition, +118 factor, +208 addend. */
    public record TriggerModifier(Trigger condition, RawValue factor, RawValue addend) implements Modifier {
        public TriggerModifier { Objects.requireNonNull(condition); Objects.requireNonNull(factor); Objects.requireNonNull(addend); }
    }
    /** Each child's virtual +30 shares the accumulator; first true return ends this list. */
    public record FirstValid(List<Modifier> modifiers) implements Modifier {
        public FirstValid { modifiers = children(modifiers); }
    }
    public record UnreviewedModifier(String diagnosis) implements Modifier {
        public UnreviewedModifier { diagnosis = diagnosisText(diagnosis); }
    }
    public record Program(long baseRaw, List<Modifier> modifiers) {
        public Program { modifiers = children(modifiers); }
    }
    /** Empty optionals preserve the actual absence of the +2F8 trigger or +2F0 weight pointer. */
    public record Definition(Optional<Trigger> trigger, Optional<Program> weightProgram) {
        public Definition { Objects.requireNonNull(trigger); Objects.requireNonNull(weightProgram); }
    }
    /** Empty definition is the null-definition sentinel, distinct from a defined row with absent pointers. */
    public record RowSource(int originalIndex, int baseWeight, Optional<Definition> definition) {
        public RowSource { StrictJson.require(originalIndex >= 0, "original row index required"); Objects.requireNonNull(definition); }
    }
    public record Review(NativePlayableAnnualGate.Executable executable, Context context, List<RowSource> rows, int random31) {
        public Review {
            Objects.requireNonNull(executable); Objects.requireNonNull(context); rows = children(rows);
            StrictJson.require(rows.size() <= 256 && random31 >= 0, "bounded review rows and native random31 required");
            Set<Integer> indexes = new HashSet<>();
            for (RowSource row : rows) StrictJson.require(indexes.add(row.originalIndex()), "original row index repeated");
        }
    }
    /** Arithmetic/selection analysis only, even when every supplied node is understood. */
    public record Analysis(NativeOnActionWeightedIndex.Result computation) {
        public Analysis { Objects.requireNonNull(computation); }
        public boolean actualNativeAstObserved() { return false; }
        public boolean loadedScriptIdentityVerified() { return false; }
        public boolean cacheFreshnessVerified() { return false; }
        public boolean liveSelectionCreditGranted() { return false; }
        public boolean eventDispatched() { return false; }
    }
    private sealed interface TruthResult permits Truth, Unresolved { }
    private record Truth(boolean value) implements TruthResult { }
    private sealed interface FoldResult permits Fold, Unresolved { }
    private record Fold(long raw, boolean applied) implements FoldResult { }
    private record Unresolved(String diagnosis) implements TruthResult, FoldResult { }

    public static Analysis analyze(Review review) {
        // The same traversal bounds apply to typed callers and decoded JSON callers.
        encode(review);
        List<NativeOnActionWeightedIndex.Row> rows = new ArrayList<>();
        for (RowSource row : review.rows()) rows.add(produce(row, review.context()));
        return new Analysis(NativeOnActionWeightedIndex.evaluate(new NativeOnActionWeightedIndex.Input(
            review.executable(), rows, review.random31())));
    }
    private static NativeOnActionWeightedIndex.Row produce(RowSource row, Context context) {
        NativeOnActionWeightedIndex.Evaluation evaluation;
        if (row.definition().isEmpty()) evaluation = new NativeOnActionWeightedIndex.Constant();
        else {
            Definition definition = row.definition().orElseThrow();
            TruthResult predicate = definition.trigger().isEmpty() ? new Truth(true) : trigger(definition.trigger().orElseThrow(), context);
            if (predicate instanceof Unresolved unavailable) evaluation = new NativeOnActionWeightedIndex.Unavailable(unavailable.diagnosis());
            else if (!((Truth) predicate).value()) evaluation = new NativeOnActionWeightedIndex.Excluded();
            else if (definition.weightProgram().isEmpty()) evaluation = new NativeOnActionWeightedIndex.Constant();
            else {
                Program program = definition.weightProgram().orElseThrow();
                FoldResult result = foldAll(program.baseRaw(), program.modifiers(), context);
                evaluation = result instanceof Fold known ? new NativeOnActionWeightedIndex.Scripted(known.raw())
                    : new NativeOnActionWeightedIndex.Unavailable(((Unresolved) result).diagnosis());
            }
        }
        return new NativeOnActionWeightedIndex.Row(row.originalIndex(), row.baseWeight(), evaluation);
    }
    private static TruthResult trigger(Trigger node, Context context) {
        if (context.rootScope() == ScopeVerdict.UNRESOLVED) return new Unresolved("native root-scope dispatch validation unresolved");
        if (context.rootScope() == ScopeVerdict.REJECTED) return new Truth(false);
        if (node instanceof UnreviewedTrigger unknown) return new Unresolved(unknown.diagnosis());
        if (node instanceof Always always) return always.value() instanceof InlineBool inline ? new Truth(inline.value())
            : new Unresolved(((DynamicBool) always.value()).diagnosis());
        if (context.mode() == 4) return new Unresolved("And/Or mode4 concrete path is not reviewed");
        boolean conjunction = node instanceof And;
        List<Trigger> a = conjunction ? ((And) node).children40() : ((Or) node).children40();
        List<Trigger> b = conjunction ? ((And) node).children88() : ((Or) node).children88();
        List<Trigger> selected = context.mode() == 1 || context.mode() == 3 ? b : a;
        boolean value = conjunction;
        for (Trigger child : selected) {
            TruthResult result = trigger(child, context);
            if (result instanceof Unresolved) return result;
            boolean actual = ((Truth) result).value();
            value = conjunction ? value && actual : value || actual;
            // Mode2 calls every child. An unresolved later child cannot be hidden by an earlier decisive result.
            if (context.mode() != 2 && actual != conjunction) return new Truth(actual);
        }
        return new Truth(value);
    }
    private static FoldResult foldAll(long raw, List<Modifier> modifiers, Context context) {
        for (Modifier modifier : modifiers) {
            FoldResult result = modifier(raw, modifier, context);
            if (result instanceof Unresolved) return result;
            raw = ((Fold) result).raw();
            // 3761780 ignores each modifier's boolean return and continues all outer entries.
        }
        return new Fold(raw, false);
    }
    private static FoldResult modifier(long raw, Modifier node, Context context) {
        if (node instanceof UnreviewedModifier unknown) return new Unresolved(unknown.diagnosis());
        if (node instanceof FirstValid first) {
            for (Modifier child : first.modifiers()) {
                FoldResult result = modifier(raw, child, context);
                if (result instanceof Unresolved) return result;
                Fold known = (Fold) result; raw = known.raw();
                if (known.applied()) return known;
            }
            return new Fold(raw, false);
        }
        TriggerModifier modifier = (TriggerModifier) node;
        // 2878E7F..E95 checks current==0 and native [this+2C8]==0 BEFORE condition/factor evaluation.
        if (raw == 0 && modifier.addend() instanceof InlineRaw) return new Fold(raw, false);
        TruthResult condition = trigger(modifier.condition(), context);
        if (condition instanceof Unresolved unavailable) return unavailable;
        if (!((Truth) condition).value()) return new Fold(raw, false);
        if (modifier.factor() instanceof DynamicRaw unknown) return new Unresolved(unknown.diagnosis());
        long scaled = multiplyRaw(raw, ((InlineRaw) modifier.factor()).raw());
        if (modifier.addend() instanceof DynamicRaw unknown) return new Unresolved(unknown.diagnosis());
        return new Fold(scaled + ((InlineRaw) modifier.addend()).raw(), true);
    }
    /** 2878EDA..F77, distinct from the original chooser's baseWeight*scriptedRaw calculation. */
    public static long multiplyRaw(long current, long factor) {
        if (current >= -SAFE_PRODUCT_OPERAND && current <= SAFE_PRODUCT_OPERAND
                && factor >= -SAFE_PRODUCT_OPERAND && factor <= SAFE_PRODUCT_OPERAND)
            return (current * factor) / 100000L;
        // cmovl/cmovg choose r8=max, r9=min. Native low64 products and additions wrap.
        long larger = Math.max(current, factor), smaller = Math.min(current, factor);
        long quotient = larger / 100000L, remainder = larger - quotient * 100000L;
        return quotient * smaller + (remainder * smaller) / 100000L;
    }

    public static byte[] encode(Review review) {
        Objects.requireNonNull(review); Budget budget = new Budget();
        ObjectNode root = StrictJson.object().put("schema", SCHEMA).put("purpose", "STATIC_SOURCE_REVIEW")
            .put("exe_sha256", NativePlayableAnnualGate.EXECUTABLE_SHA256).put("mode", review.context().mode())
            .put("root_scope", review.context().rootScope().name()).put("random31", review.random31());
        ArrayNode rows = root.putArray("rows");
        for (RowSource row : review.rows()) {
            budget.visit(0); ObjectNode out = rows.addObject().put("original_index", row.originalIndex()).put("base_weight", row.baseWeight());
            if (row.definition().isEmpty()) out.putNull("definition");
            else {
                Definition definition = row.definition().orElseThrow(); ObjectNode def = out.putObject("definition");
                if (definition.trigger().isEmpty()) def.putNull("trigger"); else def.set("trigger", triggerTree(definition.trigger().orElseThrow(), budget, 1));
                if (definition.weightProgram().isEmpty()) def.putNull("weight_program");
                else { Program program = definition.weightProgram().orElseThrow(); ObjectNode weight = def.putObject("weight_program").put("base_raw", Long.toString(program.baseRaw()));
                    weight.set("modifiers", modifierTrees(program.modifiers(), budget, 1)); }
            }
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }
    public static Review decode(byte[] bytes) {
        ObjectNode root = exact(StrictJson.parse(bytes, MAX_BYTES), "schema", "purpose", "exe_sha256", "mode", "root_scope", "random31", "rows");
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))) && "STATIC_SOURCE_REVIEW".equals(StrictJson.text(root.get("purpose"))), "exact offline review schema required");
        var executable = NativePlayableAnnualGate.Executable.exact(StrictJson.text(root.get("exe_sha256")))
            .orElseThrow(() -> new IllegalArgumentException("reviewed .4 executable required"));
        Context context = new Context(integer(root.get("mode"), 0, 4), ScopeVerdict.valueOf(StrictJson.text(root.get("root_scope"))));
        List<RowSource> rows = new ArrayList<>(); Budget budget = new Budget();
        for (JsonNode raw : array(root.get("rows"))) {
            budget.visit(0); ObjectNode row = exact(raw, "original_index", "base_weight", "definition"); JsonNode defRaw = row.get("definition");
            Optional<Definition> definition = Optional.empty();
            if (!defRaw.isNull()) {
                ObjectNode def = exact(defRaw, "trigger", "weight_program"); JsonNode weightRaw = def.get("weight_program");
                Optional<Program> program = Optional.empty();
                if (!weightRaw.isNull()) { ObjectNode weight = exact(weightRaw, "base_raw", "modifiers");
                    program = Optional.of(new Program(decimal(weight.get("base_raw")), modifiers(weight.get("modifiers"), budget, 1))); }
                definition = Optional.of(new Definition(def.get("trigger").isNull() ? Optional.empty() : Optional.of(triggerNode(def.get("trigger"), budget, 1)), program));
            }
            rows.add(new RowSource(integer(row.get("original_index"), 0, Integer.MAX_VALUE), integer(row.get("base_weight"), Integer.MIN_VALUE, Integer.MAX_VALUE), definition));
        }
        return new Review(executable, context, rows, integer(root.get("random31"), 0, Integer.MAX_VALUE));
    }
    private static ObjectNode triggerTree(Trigger node, Budget budget, int depth) {
        budget.visit(depth); ObjectNode out = StrictJson.object();
        if (node instanceof Always always) { out.put("kind", "CAlwaysTrigger"); out.set("value", boolTree(always.value())); }
        else if (node instanceof UnreviewedTrigger unknown) out.put("kind", "UNREVIEWED").put("diagnosis", unknown.diagnosis());
        else { boolean and = node instanceof And; out.put("kind", and ? "CAndTrigger" : "COrTrigger");
            List<Trigger> a = and ? ((And) node).children40() : ((Or) node).children40(), b = and ? ((And) node).children88() : ((Or) node).children88();
            ArrayNode aa = out.putArray("children40"), bb = out.putArray("children88");
            for (Trigger child : a) aa.add(triggerTree(child, budget, depth + 1));
            for (Trigger child : b) bb.add(triggerTree(child, budget, depth + 1)); }
        return out;
    }
    private static Trigger triggerNode(JsonNode raw, Budget budget, int depth) {
        budget.visit(depth); String kind = kind(raw);
        if (kind.equals("CAlwaysTrigger")) { ObjectNode node = exact(raw, "kind", "value"); return new Always(boolNode(node.get("value"))); }
        if (kind.equals("UNREVIEWED")) { ObjectNode node = exact(raw, "kind", "diagnosis"); return new UnreviewedTrigger(StrictJson.text(node.get("diagnosis"))); }
        StrictJson.require(kind.equals("CAndTrigger") || kind.equals("COrTrigger"), "explicit reviewed trigger RTTI required");
        ObjectNode node = exact(raw, "kind", "children40", "children88");
        List<Trigger> a = new ArrayList<>(), b = new ArrayList<>();
        for (JsonNode child : array(node.get("children40"))) a.add(triggerNode(child, budget, depth + 1));
        for (JsonNode child : array(node.get("children88"))) b.add(triggerNode(child, budget, depth + 1));
        return kind.equals("CAndTrigger") ? new And(a, b) : new Or(a, b);
    }
    private static ObjectNode boolTree(BoolValue value) {
        if (value instanceof InlineBool inline) return StrictJson.object().put("native_kind", 0).put("inline_bool", inline.value());
        DynamicBool dynamic = (DynamicBool) value; return StrictJson.object().put("native_kind", dynamic.nativeKind()).put("diagnosis", dynamic.diagnosis());
    }
    private static BoolValue boolNode(JsonNode raw) {
        StrictJson.require(raw != null && raw.isObject(), "bool-value object required"); int kind = integer(raw.get("native_kind"), 0, Integer.MAX_VALUE);
        if (kind == 0) { ObjectNode node = exact(raw, "native_kind", "inline_bool"); JsonNode value = node.get("inline_bool");
            StrictJson.require(value.isBoolean(), "actual JSON boolean required"); return new InlineBool(value.booleanValue()); }
        return new DynamicBool(kind, StrictJson.text(exact(raw, "native_kind", "diagnosis").get("diagnosis")));
    }
    private static ObjectNode rawTree(RawValue value) {
        if (value instanceof InlineRaw inline) return StrictJson.object().put("native_kind", 0).put("inline_raw", Long.toString(inline.raw()));
        DynamicRaw dynamic = (DynamicRaw) value; return StrictJson.object().put("native_kind", dynamic.nativeKind()).put("diagnosis", dynamic.diagnosis());
    }
    private static RawValue rawNode(JsonNode raw) {
        StrictJson.require(raw != null && raw.isObject(), "raw-value object required"); int kind = integer(raw.get("native_kind"), 0, Integer.MAX_VALUE);
        if (kind == 0) return new InlineRaw(decimal(exact(raw, "native_kind", "inline_raw").get("inline_raw")));
        return new DynamicRaw(kind, StrictJson.text(exact(raw, "native_kind", "diagnosis").get("diagnosis")));
    }
    private static ArrayNode modifierTrees(List<Modifier> modifiers, Budget budget, int depth) {
        ArrayNode out = StrictJson.object().putArray("items");
        for (Modifier modifier : modifiers) {
            budget.visit(depth); ObjectNode node = out.addObject();
            if (modifier instanceof TriggerModifier value) {
                node.put("kind", "CTriggerValueModifier"); node.set("condition", triggerTree(value.condition(), budget, depth + 1));
                node.set("factor", rawTree(value.factor())); node.set("addend", rawTree(value.addend()));
            } else if (modifier instanceof FirstValid first) {
                node.put("kind", "CFirstValidValueModifier"); node.set("modifiers", modifierTrees(first.modifiers(), budget, depth + 1));
            } else node.put("kind", "UNREVIEWED").put("diagnosis", ((UnreviewedModifier) modifier).diagnosis());
        }
        return out;
    }
    private static List<Modifier> modifiers(JsonNode raw, Budget budget, int depth) {
        List<Modifier> result = new ArrayList<>();
        for (JsonNode child : array(raw)) {
            budget.visit(depth); String kind = kind(child);
            if (kind.equals("CTriggerValueModifier")) { ObjectNode node = exact(child, "kind", "condition", "factor", "addend");
                result.add(new TriggerModifier(triggerNode(node.get("condition"), budget, depth + 1), rawNode(node.get("factor")), rawNode(node.get("addend")))); }
            else if (kind.equals("CFirstValidValueModifier")) result.add(new FirstValid(modifiers(exact(child, "kind", "modifiers").get("modifiers"), budget, depth + 1)));
            else { StrictJson.require(kind.equals("UNREVIEWED"), "explicit reviewed modifier RTTI required");
                result.add(new UnreviewedModifier(StrictJson.text(exact(child, "kind", "diagnosis").get("diagnosis")))); }
        }
        return result;
    }
    private static String kind(JsonNode raw) { StrictJson.require(raw != null && raw.isObject(), "node object required"); return StrictJson.text(raw.get("kind")); }
    private static ObjectNode exact(JsonNode node, String... fields) { return StrictJson.object(node, Set.of(fields)); }
    private static ArrayNode array(JsonNode node) { StrictJson.require(node instanceof ArrayNode && node.size() <= MAX_CHILDREN, "bounded explicit JSON array required"); return (ArrayNode) node; }
    private static int integer(JsonNode node, int min, int max) { return (int) StrictJson.integer(node, min, max); }
    private static long decimal(JsonNode node) {
        String value = StrictJson.text(node); long result = Long.parseLong(value);
        StrictJson.require(Long.toString(result).equals(value), "canonical signed decimal string required"); return result;
    }
    private static String diagnosisText(String value) { StrictJson.text(value); StrictJson.require(!value.isBlank(), "nonblank diagnosis required"); return value; }
    private static void nonzeroKind(int kind) { StrictJson.require(kind > 0, "nonzero dynamic native kind required"); }
    private static <T> List<T> children(List<T> values) { List<T> result = List.copyOf(values); StrictJson.require(result.size() <= MAX_CHILDREN, "bounded original-order children required"); return result; }
    private static final class Budget {
        private int nodes;
        private void visit(int depth) { StrictJson.require(depth <= MAX_DEPTH && ++nodes <= MAX_NODES, "review AST depth/node budget exceeded"); }
    }
}
