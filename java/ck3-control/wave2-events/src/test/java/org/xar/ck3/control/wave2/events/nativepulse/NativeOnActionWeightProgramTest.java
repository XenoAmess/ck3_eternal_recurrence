package org.xar.ck3.control.wave2.events.nativepulse;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionWeightProgram.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Serialized definition producer -> reviewed concrete semantics -> original weighted-index consumer. */
final class NativeOnActionWeightProgramTest {
    private static final Always YES = new Always(new InlineBool(true)), NO = new Always(new InlineBool(false));
    private static final UnreviewedTrigger UNKNOWN = new UnreviewedTrigger("actual concrete trigger not reviewed");
    private static Review review(int mode, ScopeVerdict scope, Trigger trigger, Program program) {
        return new Review(NativePlayableAnnualGate.Executable.CURRENT_12004, new Context(mode, scope),
            List.of(new RowSource(3, 20, Optional.of(new Definition(Optional.ofNullable(trigger), Optional.ofNullable(program))))), 0);
    }
    private static NativeOnActionWeightedIndex.Computed known(Review review) {
        return assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, analyze(review).computation());
    }
    private static int weight(Review review) { return known(review).rows().getFirst().nativeWeight(); }
    private static TriggerModifier change(Trigger condition, long factor, long addend) {
        return new TriggerModifier(condition, new InlineRaw(factor), new InlineRaw(addend));
    }
    private static ObjectNode tree(Review review) { return (ObjectNode) StrictJson.parse(encode(review), 131072); }
    private static ObjectNode program(ObjectNode root) { return (ObjectNode) root.path("rows").get(0).path("definition").path("weight_program"); }

    @Test void serializedProducerPreservesFirstValidAndOuterOrder() {
        var first = new FirstValid(List.of(change(NO, 900000, 0), change(YES, 200000, 0),
            new UnreviewedModifier("unreached unsupported modifier")));
        var input = review(0, ScopeVerdict.VALIDATED, new And(List.of(YES), List.of()),
            new Program(100000, List.of(first, change(YES, 100000, 25000))));
        byte[] serialized = encode(input); Review decoded = decode(serialized);
        assertEquals(input, decoded); assertArrayEquals(serialized, encode(decoded));
        var analysis = analyze(decoded); var computed = assertInstanceOf(NativeOnActionWeightedIndex.Computed.class, analysis.computation());
        assertEquals(45, computed.rows().getFirst().nativeWeight()); assertEquals(3, computed.originalRowIndex().orElseThrow());
        assertEquals(NativeOnActionWeightedIndex.Status.INDEX_CHOSEN, computed.status());
        assertFalse(analysis.actualNativeAstObserved()); assertFalse(analysis.loadedScriptIdentityVerified());
        assertFalse(analysis.cacheFreshnessVerified()); assertFalse(analysis.liveSelectionCreditGranted()); assertFalse(analysis.eventDispatched());
    }
    @Test void childBanksAndExhaustiveMode() {
        var and = new And(List.of(YES), List.of(NO)); var or = new Or(List.of(NO), List.of(YES));
        assertEquals(20, weight(review(0, ScopeVerdict.VALIDATED, and, null)));
        assertEquals(0, weight(review(1, ScopeVerdict.VALIDATED, and, null)));
        assertEquals(0, weight(review(3, ScopeVerdict.VALIDATED, and, null)));
        assertEquals(20, weight(review(2, ScopeVerdict.VALIDATED, and, null)));
        assertEquals(0, weight(review(0, ScopeVerdict.VALIDATED, or, null)));
        assertEquals(20, weight(review(1, ScopeVerdict.VALIDATED, or, null)));
        assertEquals(20, weight(review(3, ScopeVerdict.VALIDATED, or, null)));
        assertEquals(0, weight(review(2, ScopeVerdict.VALIDATED, or, null)));
        var andUnknown = new And(List.of(NO, UNKNOWN), List.of());
        var orUnknown = new Or(List.of(YES, UNKNOWN), List.of());
        assertEquals(0, weight(review(0, ScopeVerdict.VALIDATED, andUnknown, null)));
        assertEquals(20, weight(review(0, ScopeVerdict.VALIDATED, orUnknown, null)));
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class, analyze(review(2, ScopeVerdict.VALIDATED, andUnknown, null)).computation());
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class, analyze(review(2, ScopeVerdict.VALIDATED, orUnknown, null)).computation());
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class,
            analyze(review(0, ScopeVerdict.VALIDATED, new And(List.of(UNKNOWN, NO), List.of()), null)).computation());
    }
    @Test void zeroGatePrecedesConditionAndFactor() {
        var skipped = new TriggerModifier(UNKNOWN, new DynamicRaw(2, "factor unavailable"), new InlineRaw(999));
        assertEquals(0, weight(review(0, ScopeVerdict.UNRESOLVED, null, new Program(0, List.of(skipped)))));
        var dynamicAdd = new TriggerModifier(YES, new InlineRaw(100000), new DynamicRaw(1, "context-dependent add unavailable"));
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class,
            analyze(review(0, ScopeVerdict.VALIDATED, null, new Program(0, List.of(dynamicAdd)))).computation());
        var falseBeforeDynamic = new TriggerModifier(NO, new DynamicRaw(1, "not reached"), new DynamicRaw(1, "not reached"));
        assertEquals(20, weight(review(0, ScopeVerdict.VALIDATED, null, new Program(100000, List.of(falseBeforeDynamic)))));
    }
    @Test void unresolvedBranchesAndScope() {
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class,
            analyze(review(4, ScopeVerdict.VALIDATED, new And(List.of(), List.of()), null)).computation());
        assertEquals(20, weight(review(4, ScopeVerdict.VALIDATED, YES, null)));
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class, analyze(review(0, ScopeVerdict.UNRESOLVED, YES, null)).computation());
        assertEquals(0, weight(review(0, ScopeVerdict.REJECTED, YES, null)));
        var dynamic = new Always(new DynamicBool(2, "bool template unresolved"));
        assertEquals(dynamic, decode(encode(review(0, ScopeVerdict.VALIDATED, dynamic, null))).rows().getFirst().definition().orElseThrow().trigger().orElseThrow());
        assertInstanceOf(NativeOnActionWeightedIndex.Unresolved.class, analyze(review(0, ScopeVerdict.VALIDATED, dynamic, null)).computation());
    }
    @Test void wideMultiplyDiffersFromChooser() {
        assertEquals(600000, multiplyRaw(200000, 300000)); assertEquals(-1, multiplyRaw(-199999, 1));
        assertEquals(Long.MAX_VALUE, multiplyRaw(Long.MAX_VALUE, 100000));
        assertEquals(Long.MIN_VALUE, multiplyRaw(Long.MIN_VALUE, 100000));
        assertEquals(Long.MIN_VALUE, multiplyRaw(Long.MAX_VALUE, Long.MAX_VALUE));
        assertEquals(Long.MIN_VALUE, multiplyRaw(Long.MIN_VALUE, Long.MIN_VALUE));
        assertEquals(92233720370002L, multiplyRaw(3037000500L, 3037000500L));
        assertEquals(-92233720370002L, multiplyRaw(-3037000500L, 3037000500L));
        assertEquals(-1, NativeOnActionWeightedIndex.scriptedWeight(100000, Long.MAX_VALUE));
        var additionWrap = new Program(Long.MAX_VALUE, List.of(change(YES, 100000, 1)));
        assertEquals(0, weight(review(0, ScopeVerdict.VALIDATED, null, additionWrap)));
    }
    @Test void strictSerializedBoundary() {
        var original = review(0, ScopeVerdict.VALIDATED, YES, new Program(Long.MIN_VALUE, List.of()));
        List<Consumer<ObjectNode>> invalid = List.of(
            root -> root.put("exe_sha256", "0".repeat(64)), root -> root.put("mode", true), root -> root.put("random31", 1.0),
            root -> root.put("extra", 1), root -> root.remove("purpose"),
            root -> program(root).put("base_raw", 7), root -> program(root).put("base_raw", "-0"),
            root -> program(root).put("base_raw", "+1"), root -> program(root).put("base_raw", "01"),
            root -> program(root).put("base_raw", "9223372036854775808"), root -> program(root).remove("modifiers"),
            root -> ((ObjectNode) root.path("rows").get(0).path("definition")).remove("trigger"),
            root -> ((ObjectNode) root.path("rows").get(0).path("definition").path("trigger").path("value")).put("inline_bool", 1));
        for (Consumer<ObjectNode> mutate : invalid) { ObjectNode raw = tree(original); mutate.accept(raw);
            byte[] bytes = raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> decode(bytes)); }
        assertEquals(original, decode(encode(original)));
        assertThrows(IllegalArgumentException.class, () -> decode("{\"schema\":1,\"schema\":2}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void sentinelPointersAndDepthBudget() {
        var review = new Review(NativePlayableAnnualGate.Executable.CURRENT_12004, new Context(4, ScopeVerdict.UNRESOLVED),
            List.of(new RowSource(0, 1, Optional.empty()), new RowSource(1, 1, Optional.of(new Definition(Optional.empty(), Optional.empty())))), 0);
        assertEquals(review, decode(encode(review))); assertEquals(2, known(review).rows().size());
        ObjectNode json = tree(review); assertTrue(json.path("rows").get(0).get("definition").isNull());
        assertTrue(json.path("rows").get(1).path("definition").get("trigger").isNull());
        Trigger nested = YES; for (int depth = 0; depth < 35; depth++) nested = new And(List.of(nested), List.of());
        var tooDeep = review(0, ScopeVerdict.VALIDATED, nested, null);
        assertThrows(IllegalArgumentException.class, () -> encode(tooDeep));
        assertThrows(IllegalArgumentException.class, () -> analyze(tooDeep));
    }
}
