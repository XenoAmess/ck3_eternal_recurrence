package org.xar.ck3.control.vanilla.schemesway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.function.Consumer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule.*;
import static org.xar.ck3.control.vanilla.schemesway.SourceBoundSwayReevaluationCache.Disposition.*;

/** Actual original-producer differentials plus independent source/revision/type rejection checks. */
public final class SwayScheduleVerification {
    private int assertions;
    private int negativeCases;
    private SwayScheduleVerification() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) { throw new IllegalArgumentException("actual-original-producer-golden required"); }
        new SwayScheduleVerification().run(Path.of(arguments[0]));
    }

    private void run(Path golden) throws Exception {
        JsonNode corpus = StrictJson.parse(Files.readAllBytes(golden), 262144);
        check("xar.vanilla-sway-scheduler-golden/v1".equals(corpus.path("schema").asText()), "exact golden schema");
        for (JsonNode item : corpus.path("plan_cases")) {
            Request request = SwayScheduleWire.decode(StrictJson.canonical(item.get("input")));
            JsonNode actual = StrictJson.parse(SwayScheduleWire.encode(plan(request)));
            check(actual.equals(item.get("expected")), item.path("id").asText() + " original producer diff: " + actual);
            check(!plan(request).submitAllowed() && !plan(request).nativeAiRankClaimed()
                    && !plan(request).terminalOrUsefulGainClaimed(), "pure nomination has no action/result authority");
            if (plan(request).state().isPresent()) {
                State state = plan(request).state().orElseThrow();
                check(state.equals(SwayScheduleWire.decodeState(SwayScheduleWire.encodeState(state))), "state persistence round trip");
            }
        }
        for (JsonNode item : corpus.path("complete_cases")) {
            State state = SwayScheduleWire.decodeState(StrictJson.canonical(item.get("state")));
            State actual = complete(state, item.get("date_raw").bigIntegerValue(),
                    Job.valueOf(item.get("job_kind").textValue().toUpperCase(Locale.ROOT)),
                    Outcome.valueOf(item.get("outcome").textValue().toUpperCase(Locale.ROOT)),
                    item.get("target_character_id").isNull() ? Optional.empty() : Optional.of(item.get("target_character_id").longValue()),
                    item.get("action_id").isNull() ? Optional.empty() : Optional.of(item.get("action_id").textValue()));
            check(StrictJson.parse(SwayScheduleWire.encodeState(actual)).equals(item.get("expected")),
                    item.path("id").asText() + " original complete producer diff");
        }
        ObjectNode base = (ObjectNode) corpus.path("plan_cases").get(0).get("input").deepCopy();
        Request original = SwayScheduleWire.decode(StrictJson.canonical(base));
        check(!original.frame().orElseThrow().publicRevision().equals(original.frame().orElseThrow().nativeRevision()), "public!=native fixture is mandatory");
        verifyCache(original);
        verifyBoundary(base);
        verifyStockReferences(corpus);
        ObjectNode result = StrictJson.object(); result.put("status", "PASS");
        result.put("plan_original_producer_differentials", corpus.path("plan_cases").size());
        result.put("complete_original_producer_differentials", corpus.path("complete_cases").size());
        result.put("independent_negative_boundary_cases", negativeCases); result.put("assertions", assertions);
        result.put("scope", "actual original pure producer replay and strict Java nomination/cache only; no native AI equivalence, production adoption, Game, SDK, Driver or SAVE credit");
        System.out.println(new String(StrictJson.canonical(result), StandardCharsets.UTF_8));
    }

    private void verifyStockReferences(JsonNode corpus) {
        G2Source source = new G2Source(corpus.path("machine_id").textValue(), corpus.path("observed_at_utc").textValue(),
                "1.20.0.4", ExactRef.fromJson(corpus.get("current_stock_source_ref")));
        var profile = StockSwayCandidateProfile.sourceBound(source);
        check(profile.currentEarlyGateKey().equals("is_available"), "actual .4 early gate differs from old generic ai_potential description");
        check(profile.targetGroups().size() == 3 && profile.targetGroups().get(0).maximum().orElseThrow() == 10
                && profile.targetGroups().get(1).maximum().orElseThrow() == 10 && profile.targetGroups().get(2).maximum().isEmpty(), "three actual authored target groups/caps");
        check(profile.cadence().stream().map(StockSwayCandidateProfile.Cadence::months).toList().equals(List.of(0, 120, 24, 6, 6, 6)), "authored tier cadence retained exactly");
        check(profile.orderedModifierReferences().size() == corpus.path("current_stock_authored_operands").size(), "authored reference cardinality");
        for (int i = 0; i < profile.orderedModifierReferences().size(); i++) {
            var authored = profile.orderedModifierReferences().get(i); JsonNode captured = corpus.path("current_stock_authored_operands").get(i);
            check(authored.operation().name().equalsIgnoreCase(captured.path("operation").textValue())
                    && authored.authoredOperand().compareTo(new java.math.BigDecimal(captured.path("operand").textValue())) == 0,
                    "authored operation/value/order from exact current source at index " + i);
        }
        check(!profile.computesScore() && !profile.completeNativeCandidatesClaimed() && !profile.submissionAuthorized(), "authored reference table has no evaluator/action authority");
        expectFailure(() -> StockSwayCandidateProfile.sourceBound(new G2Source(source.machineId(), source.observedAtUtc(), "1.19.0.6", source.sourceRef())), "old native study cannot be relabeled current");
        expectFailure(() -> StockSwayCandidateProfile.sourceBound(new G2Source(source.machineId(), source.observedAtUtc(), source.exactBuild(),
                new ExactRef(source.sourceRef().path(), source.sourceRef().bytes(), "a".repeat(64)))), "different stock file digest rejected");
    }

    private void verifyCache(Request original) {
        SourceBoundSwayReevaluationCache cache = new SourceBoundSwayReevaluationCache();
        check(cache.evaluate(original).disposition() == COMPUTED, "first exact input computes");
        for (int i = 0; i < 20; i++) {
            var reused = cache.evaluate(original);
            check(reused.disposition() == REUSED_EXACT_INPUT && reused.computations() == 1, "identical input avoids pure reevaluation");
            check(reused.decision().equals(plan(original)), "cached candidate/reason/state equal uncached");
        }
        Frame frame = original.frame().orElseThrow();
        Frame publicChanged = new Frame(frame.snapshotId(), frame.publicRevision().add(BigInteger.ONE), frame.nativeRevision(),
                frame.dateRaw(), frame.actorCharacterId(), frame.paused(), frame.mapReady(), frame.alive(), frame.context());
        Request publicRequest = changed(original, Optional.of(publicChanged), original.root(), original.state(), original.source());
        cache.evaluate(original);
        check(cache.evaluate(publicRequest).disposition() == COMPUTED, "public revision invalidates independently of native");
        check(plan(publicRequest).equals(plan(original)), "public revision change alone preserves original pure decision");
        Frame nativeChanged = new Frame(frame.snapshotId(), frame.publicRevision(), frame.nativeRevision().add(BigInteger.ONE),
                frame.dateRaw(), frame.actorCharacterId(), frame.paused(), frame.mapReady(), frame.alive(), frame.context());
        Request nativeRequest = changed(original, Optional.of(nativeChanged), original.root(), original.state(), original.source());
        cache.evaluate(original);
        check(cache.evaluate(nativeRequest).disposition() == COMPUTED, "native revision invalidates independently of public");
        check(plan(nativeRequest).reason() == Reason.SAME_FRAME_ROOT_UNAVAILABLE, "native root join remains required");
        Root root = original.root().orElseThrow();
        Root reordered = new Root(root.available(), root.actorCharacterId(), root.alive(), root.nativeRevision(), root.dateRaw(), Optional.of(List.of(500L, 900L, 100L)));
        Request reorderedRequest = changed(original, original.frame(), Optional.of(reordered), original.state(), original.source());
        cache.evaluate(original);
        check(cache.evaluate(reorderedRequest).disposition() == COMPUTED, "frontier order belongs in cache key");
        check(plan(reorderedRequest).targetCharacterId().equals(Optional.of(500L)), "candidate order never silently sorted");
        State initial = plan(original).state().orElseThrow();
        State cooled = new State(initial.actorCharacterId(), Optional.of(900L), 2, Optional.of(BigInteger.valueOf(1000)),
                Optional.of(BigInteger.valueOf(5000)), initial.frontierMembership(), Optional.empty(), Optional.empty(), Optional.of(Job.QUERY_SELECTED_TARGET));
        Request cooledRequest = changed(original, original.frame(), original.root(), Optional.of(cooled), original.source());
        cache.evaluate(original);
        check(cache.evaluate(cooledRequest).disposition() == COMPUTED && plan(cooledRequest).job().isEmpty(), "scheduler state cannot be omitted from cache key");
        G2Source source = original.source();
        G2Source foreign = new G2Source("explicit-other-machine", source.observedAtUtc(), source.exactBuild(), source.sourceRef());
        Request foreignRequest = changed(original, original.frame(), original.root(), original.state(), foreign);
        cache.evaluate(original);
        check(cache.evaluate(foreignRequest).disposition() == COMPUTED, "source machine change never reuses current machine entry");
        check(foreignRequest.source().machineId().equals("explicit-other-machine") && !plan(foreignRequest).submitAllowed(), "foreign evidence remains explicit and has no live permission");
        ExactRef altered = new ExactRef(source.sourceRef().path(), source.sourceRef().bytes(), "a".repeat(64));
        G2Source changedSource = new G2Source(source.machineId(), source.observedAtUtc(), source.exactBuild(), altered);
        cache.evaluate(original);
        check(cache.evaluate(changed(original, original.frame(), original.root(), original.state(), changedSource)).disposition() == COMPUTED,
                "source digest is part of full cache identity");
        Frame later = new Frame(frame.snapshotId(), frame.publicRevision(), frame.nativeRevision(), frame.dateRaw().add(RAW_PER_DAY),
                frame.actorCharacterId(), frame.paused(), frame.mapReady(), frame.alive(), frame.context());
        Root laterRoot = new Root(root.available(), root.actorCharacterId(), root.alive(), root.nativeRevision(), later.dateRaw(), root.frontier());
        cache.evaluate(original);
        check(cache.evaluate(changed(original, Optional.of(later), Optional.of(laterRoot), original.state(), source)).disposition() == COMPUTED,
                "date invalidates with both revisions unchanged");
        Ledger pending = new Ledger(Optional.of(new Pending("synthetic-new-pending", 7, 900)), Optional.empty());
        Request pendingRequest = new Request(source, original.frame(), original.selectedStep(), original.root(), pending, original.state(), false);
        cache.evaluate(original);
        check(cache.evaluate(pendingRequest).disposition() == COMPUTED && plan(pendingRequest).job().equals(Optional.of(Job.RECONCILE_PENDING)),
                "new pending fact invalidates and changes query into read-only recovery");
        Request selectedOther = new Request(source, original.frame(), Step.OTHER, original.root(), original.ledger(), original.state(), false);
        cache.evaluate(original);
        check(cache.evaluate(selectedOther).disposition() == COMPUTED && plan(selectedOther).reason() == Reason.PRESERVE_SELECTED_STEP,
                "selected ordinary priority remains a cache dependency");
        Frame modal = new Frame(frame.snapshotId(), frame.publicRevision(), frame.nativeRevision(), frame.dateRaw(), frame.actorCharacterId(),
                frame.paused(), frame.mapReady(), frame.alive(), Context.MANDATORY);
        cache.evaluate(original);
        check(cache.evaluate(changed(original, Optional.of(modal), original.root(), original.state(), source)).disposition() == COMPUTED,
                "mandatory context invalidates independently of revisions");
        cache.clear(); check(cache.evaluate(original).disposition() == COMPUTED, "explicit owner clear forces recomputation");
        check(original.root().orElseThrow().frontier().orElseThrow().equals(List.of(900L, 100L, 500L)), "cache cannot mutate held native order");
        expectFailure(() -> original.root().orElseThrow().frontier().orElseThrow().add(800L), "immutable frontier");
    }

    private void verifyBoundary(ObjectNode base) {
        rejected(base, value -> value.remove("source"), "missing required source");
        rejected(base, value -> value.put("unexpected", 1), "unknown wrapper field");
        rejected(base, value -> ((ObjectNode) value.get("snapshot")).put("revision", true), "revision bool");
        rejected(base, value -> ((ObjectNode) value.get("snapshot")).put("native_revision", 3.0), "native revision float equality");
        rejected(base, value -> ((ObjectNode) value.get("snapshot")).put("native_revision", 9007199254740992L), "unsafe numeric native revision");
        rejected(base, value -> ((ObjectNode) value.get("snapshot")).put("date_raw", 1000.0), "date float equality");
        rejected(base, value -> ((ObjectNode) value.get("snapshot")).put("paused", "true"), "bool coercion");
        rejected(base, value -> ((ObjectNode) value.get("snapshot").get("played_character")).put("character_id", true), "character bool");
        rejected(base, value -> ((ObjectNode) value.get("snapshot").get("played_character")).put("character_id", 7.0), "character float");
        rejected(base, value -> ((ObjectNode) value.get("root")).put("direct_landed_vassal_character_ids", "[]"), "frontier string is not array");
        rejected(base, value -> ((ObjectNode) value.get("root")).putArray("direct_landed_vassal_character_ids").add(true), "frontier bool");
        rejected(base, value -> ((ObjectNode) value.get("source")).put("exact_build", "1.20.0.3"), "different build");
        rejected(base, value -> ((ObjectNode) value.get("source")).remove("machine_id"), "missing source machine");
        rejected(base, value -> ((ObjectNode) value.get("source").get("source_ref")).put("bytes", 1.0), "source bytes float");
        rejected(base, value -> ((ObjectNode) value.get("source").get("source_ref")).put("sha256", "not-a-sha"), "source digest malformed");
        String raw = new String(StrictJson.canonical(base), StandardCharsets.UTF_8);
        expectFailure(() -> SwayScheduleWire.decode(("{\"source\":null," + raw.substring(1)).getBytes(StandardCharsets.UTF_8)), "duplicate JSON field"); negativeCases++;
        JsonNode state = StrictJson.parse(SwayScheduleWire.encodeState(State.initial(7)));
        ObjectNode missing = ((ObjectNode) state).deepCopy(); missing.remove("frontier_membership");
        expectFailure(() -> SwayScheduleWire.decodeState(StrictJson.canonical(missing)), "missing is distinct from null frontier membership"); negativeCases++;
    }

    private static Request changed(Request value, Optional<Frame> frame, Optional<Root> root, Optional<State> state, G2Source source) {
        return new Request(source, frame, value.selectedStep(), root, value.ledger(), state, value.activeObservationOnly());
    }
    private void rejected(ObjectNode base, Consumer<ObjectNode> mutation, String name) {
        ObjectNode altered = base.deepCopy(); mutation.accept(altered);
        expectFailure(() -> SwayScheduleWire.decode(StrictJson.canonical(altered)), name); negativeCases++;
    }
    private void expectFailure(Runnable operation, String name) {
        boolean failed = false;
        try { operation.run(); } catch (IllegalArgumentException | UnsupportedOperationException expected) { failed = true; }
        check(failed, "expected rejection: " + name);
    }
    private void check(boolean condition, String name) { assertions++; if (!condition) { throw new AssertionError(name); } }
}
