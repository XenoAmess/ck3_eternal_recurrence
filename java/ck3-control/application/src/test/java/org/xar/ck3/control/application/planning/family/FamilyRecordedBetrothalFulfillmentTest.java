package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel.ExactBuild;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.CostTerm;

/** Public policy -> original fixed-pair validator -> actual command/pending producer.
 * Native packets, seed material and Bridge are explicit software inputs, not live custody.
 * Real sole-writer material replay is outside this software fixture's scope. */
final class FamilyRecordedBetrothalFulfillmentTest {
    private static final ExactRef SOURCE = ref("software-fulfillment-source");
    private static final BridgeIdentity BRIDGE = new BridgeIdentity(77, "2026-10-26T00:00:00Z");
    private static final String EPISODE = "software-recorded-betrothal";
    private static final String STEP = "submit-current-first-heir-betrothal-fulfillment-v1-private";
    private static ExactRef ref(String path) { return new ExactRef(path, 1, "a".repeat(64)); }
    private static Obj ledger(Slot slot) {
        return obj("schema", t(FamilyDomainSource.schema(slot)), "pending", Nil.INSTANCE, "resolved", Nil.INSTANCE);
    }
    private static Obj snapshot() {
        return obj("snapshot_id", t("native:7"), "revision", n(8), "native_revision", n(7), "date_raw", n(100),
                "episode_run_id", t(EPISODE), "paused", new Bool(true), "map_ready", new Bool(true),
                "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "active_wars", rows(List.of()), "player_armies", rows(List.of()),
                "played_character", obj("character_id", n(1), "alive", new Bool(true)),
                "diagnostics", obj("hello", obj("expected_ck3_version", t(ExactBuild.CK3_12004.version()),
                        "expected_ck3_sha256", t(ExactBuild.CK3_12004.sha256()))));
    }
    /** Same finite adulthood/final-terms values as the original formal consumer's
     * software relation fixture; identities are intentionally local unit values. */
    private static Obj relationship() {
        Obj costs = obj("raw_scale", n(100000), "payer_role", t("actor"), "application_timing", t("on_send"));
        for (CostTerm term : CostTerm.values()) costs = costs.with(term.wire(), n(0));
        Obj value = obj("status", t("available"), "unavailable_reason", Nil.INSTANCE,
                "actor_character_id", n(1), "heir_character_id", n(3), "partner_character_id", n(2),
                "recipient_character_id", n(4), "intermediary_character_id", Nil.INSTANCE,
                "adult_readback_available", new Bool(true), "heir_is_adult", new Bool(true), "partner_is_adult", new Bool(true),
                "heir_adult_measure_raw", n(19), "partner_adult_measure_raw", n(20),
                "heir_adult_threshold_raw", n(19), "partner_adult_threshold_raw", n(20),
                "ready_to_marry_betrothed", new Bool(true), "final_legality_sampled", new Bool(true),
                "complete_can_send", new Bool(true), "recipient_acceptance_ready", new Bool(true),
                "recipient_ai_accept_raw", n(900000), "recipient_answer_status_raw", n(0), "generic_costs", costs,
                "matrilineal_option_selected", new Bool(false), "effective_matrilineal_if_accepted", new Bool(false),
                "predicted_outcome_if_accepted", t("marriage"), "native_child_house_preview", Nil.INSTANCE);
        return obj("schema", t("xar.ck3.current-first-heir-relationship.v1"), "exact_ck3_build", t(ExactBuild.CK3_12004.version()),
                "exe_sha256", t(ExactBuild.CK3_12004.sha256()), "status", t("available"), "read_only", new Bool(true),
                "advertised", new Bool(false), "native_revision", n(7), "root_query_sequence", n(1),
                "heir_character_id", n(3), "betrothed_character_id", n(2), "primary_spouse_character_id", Nil.INSTANCE,
                "spouse_character_ids", rows(List.of()), "bilateral_verified", new Bool(true), "betrothal_actionability", value);
    }
    private static Obj originalPending() {
        return obj("episode_run_id", t(EPISODE), "played_character_id", n(1), "heir_character_id", n(3),
                "candidate_character_id", n(2), "recipient_character_id", n(4), "pre_native_revision", n(6),
                "source_date_raw", n(99), "source_bridge_pid", n(BRIDGE.pid()),
                "source_bridge_creation_date", t(BRIDGE.creationDate()), "fulfill_existing_betrothal", new Bool(false),
                "matrilineal_option_selected", new Bool(false));
    }
    private static Obj originalMaterial() {
        Obj body = ledger(Slot.FAMILY).with("pending", originalPending());
        Obj result = obj("status", t("betrothal"), "material_result", new Bool(true),
                "heir_character_id", n(3), "candidate_character_id", n(2), "post_native_revision", n(7));
        body = FamilyResultReducer.reduce(Query.FAMILY_RESULT, body,
                obj("pending", originalPending(), "cold", new Bool(false)), result, BRIDGE, integer(snapshot().get("date_raw")));
        return FamilyResultReducer.reduce(Query.FAMILY_ALLIANCE, body,
                obj("resolved", body.get("resolved")), allianceResult(), BRIDGE, integer(snapshot().get("date_raw")));
    }
    private static Obj allianceResult() {
        return obj("alliance_status", t("unknown"), "played_has_recipient_alliance", new Bool(true),
                "recipient_has_played_alliance", new Bool(false), "relationship_status", t("betrothal"), "native_revision", n(7));
    }
    private static PlanningRequest request(Obj snapshot) {
        var source = new G2Source("software-fulfillment-machine", "2026-10-26T00:00:00Z", "software-current4", SOURCE);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                integer(snapshot.get("native_revision")), integer(snapshot.get("date_raw"))),
                text(snapshot.get("snapshot_id")), integer(snapshot.get("revision")), text(snapshot.get("episode_run_id")));
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123,
                new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningRequest(before, source, "software-fulfillment-session", Instant.parse("2026-10-26T01:00:00Z"),
                new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey(STEP)), Set.of(), Optional.empty(),
                        List.of(), Optional.empty(), Optional.empty(), false));
    }
    private static OrdinaryPolicy.Draft baseline() {
        return new OrdinaryPolicy.Draft("one-life-turn-v1", "quiet", "independent quiet baseline", OrdinaryPolicy.Kind.ORDINARY,
                Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), obj("selected_step", t("life-advance")));
    }
    private static final class Fixture {
        private Obj relation = relationship();
        private boolean resultUnavailable;
        private Optional<Obj> resultOverride = Optional.empty();
        private final List<Query> readQueries = new ArrayList<>();
        private final List<ActionCommand> commands = new ArrayList<>();
        private Documents documents = new Documents(originalMaterial(), ledger(Slot.CHILD_MATRILINEAL), ledger(Slot.DEFAULT_MARRIAGE),
                BRIDGE, ref("software-head"), List.of(ref("software-family"), ref("software-matri"), ref("software-default")));
        private final FamilyOrdinaryPolicy policy;
        private Fixture() {
            var projections = new EnumMap<Query, ProjectedSource>(Query.class);
            for (Query query : List.of(Query.CURRENT_RELATION, Query.FAMILY_RESULT, Query.FAMILY_ALLIANCE))
                projections.put(query, new ProjectedSource() {
                    @Override public ProjectedRead read(PlanningRequest actual, Obj arguments) {
                        readQueries.add(query);
                        if (query == Query.FAMILY_RESULT && resultUnavailable)
                            return new ProjectedRead(arguments, new PlanningReadResult.Unavailable<>("software unknown result", Optional.empty()));
                        Obj value = switch (query) {
                            case CURRENT_RELATION -> relation;
                            case FAMILY_RESULT -> resultOverride.orElseGet(() -> obj("status", t("betrothal"), "material_result", new Bool(true),
                                    "heir_character_id", n(3), "candidate_character_id", n(2), "post_native_revision", n(7)));
                            case FAMILY_ALLIANCE -> allianceResult();
                            default -> throw new AssertionError("no alternate candidate or education read");
                        };
                        return packet(actual, query, arguments, value, readQueries.size());
                    }
                    @Override public Obj decode(PlanningReadReceipt original) {
                        return FamilyJson.decode(original.original().originalResultToken().orElseThrow().bytes());
                    }
                });
            FamilyCommands producer = new FamilyCommands((actual, operation, arguments, plan) -> {
                throw new AssertionError("no independent date command is prepared by the optional family policy");
            }, (actual, command) -> commands.add(command));
            policy = new FamilyOrdinaryPolicy(SOURCE, new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest actual) {
                    throw new AssertionError("only the installed projected software read is available");
                }
            }, new Reads(Map.of(), projections), actual -> new KnownDocuments(documents), producer,
                    (actual, query, arguments, observed) -> {
                        Obj reduced = FamilyResultReducer.reduce(query, documents.family(), arguments, observed.value(), documents.bridge(), observed.receipt().request().before().frame().identity().dateRaw());
                        family(reduced); return true;
                    }, new Settings(true, true, false, false, Optional.empty()));
        }
        private void family(Obj body) {
            documents = new Documents(body, documents.matrilineal(), documents.childDefault(), documents.bridge(),
                    documents.canonicalHead(), documents.importedDocuments());
        }
        private void resolved(Obj resolved) { family(documents.family().with("resolved", resolved)); }
    }
    private static ProjectedRead packet(PlanningRequest actual, Query query, Obj arguments, Obj value, int ordinal) {
        String id = "software-fulfillment-read-" + ordinal;
        var request = new PlanningReadRequest(actual.before(), actual.source(), actual.sessionId(), query.operation(), arguments, actual.deadline());
        var raw = new RawJson(bytes(obj("type", t("command_result"), "protocol_version", n(1), "request_id", t(id),
                "ok", new Bool(true), "result", value)));
        byte[] encoded = raw.bytes();
        byte[] wire = ByteBuffer.allocate(encoded.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(encoded.length).put(encoded).array();
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(bytes(value))), raw, wire);
        var guard = new PlanningReadGuard(new GuardEvidence(actual.before(), actual.source(), actual.sessionId(),
                BigInteger.ONE, query.operation(), SOURCE, SOURCE, "software-no-native-custody",
                Instant.parse("2026-10-26T00:00:00Z"), actual.deadline()), true, true, true, "b".repeat(64));
        var receipt = new PlanningReadReceipt(request, "software-fulfillment:" + query.name(), id, guard, guard, ack);
        return new ProjectedRead(arguments, new PlanningReadResult.Known<>(value, receipt, ref(id)));
    }

    /** A detail replacement preserves the chosen baseline while recording the actual relation. */
    private static Obj retainedBaselineObservation(Fixture fixture) {
        OrdinaryPolicy.Draft previous = baseline(); Obj beforeMaterial = fixture.documents.family();
        var retained = assertInstanceOf(OrdinaryPolicy.Replace.class,
                fixture.policy.evaluate(request(snapshot()), previous)).draft();
        assertEquals(previous.policy(), retained.policy()); assertEquals(previous.phase(), retained.phase());
        assertEquals(previous.reason(), retained.reason()); assertEquals(previous.kind(), retained.kind());
        assertEquals(previous.command(), retained.command()); assertEquals(previous.purpose(), retained.purpose());
        assertEquals(previous.domain(), retained.domain());
        previous.detail().members().forEach((key, value) -> assertEquals(value, retained.detail().get(key)));
        assertEquals(fixture.relation, retained.detail().get("family_marriage_current_relationship"));
        assertEquals(beforeMaterial, fixture.documents.family(), "a relationship annotation does not reduce new material");
        assertEquals(List.of(Query.CURRENT_RELATION), fixture.readQueries);
        assertTrue(fixture.commands.isEmpty(), "preserving an observed baseline never prepares a send");
        return retained.detail();
    }
    @Test void recordedProposalBetrothalCanUseTheExistingAdultFulfillmentProducer() {
        Fixture f = new Fixture(); PlanningRequest actual = request(snapshot());
        Obj oldMaterial = object(f.documents.family().get("resolved"));
        var decision = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(actual, baseline()));
        ActionCommand command = decision.draft().command().orElseThrow();
        assertEquals(STEP, command.operation().value()); assertEquals(List.of(Query.CURRENT_RELATION), f.readQueries);
        assertEquals(List.of(command), f.commands);
        assertEquals(FamilyMarriageIntent.Route.FULFILL_BETROTHAL, FamilyMarriageIntent.fromJson(command.arguments()).route());
        assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
        var send = new FamilyNativePreparation.MaterializedSend(1, 4, OptionalLong.of(3), OptionalLong.of(2),
                OptionalLong.empty(), 5, ref("software-actual-preparation-read"));
        var domains = new FamilyPendingProducer.State(f.documents.family(), f.documents.matrilineal(), f.documents.childDefault());
        Obj reviewed = FamilyMarriagePreparationReview.review(FamilyMarriageIntent.fromJson(command.arguments()), snapshot(), BRIDGE,
                domains, new FamilyMarriagePreparationReview.Policy(false), new FamilyMarriagePreparationReview.Fulfillment(f.relation));
        assertNotEquals(decision.draft().detail(), reviewed, "fresh strategy review produces the prepared plan");
        var produced = FamilyPendingProducer.produce(command, snapshot(), BRIDGE, domains, reviewed, send);
        assertEquals(oldMaterial, produced.body().get("resolved"));
        assertEquals(new Bool(true), produced.pending().get("fulfill_existing_betrothal"));
        assertEquals(n(4), produced.pending().get("recipient_character_id"));
        assertEquals(send.toJson(), produced.pending().get("native_send_context"));
        assertEquals(produced.body(), FamilyDomainSource.validate(Slot.FAMILY, bytes(produced.body())));
        f.family(produced.body());
        var retained = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(actual, baseline()));
        assertTrue(retained.draft().command().isEmpty(), "unresolved new fulfillment never prepares a second command");
        assertEquals(1, f.commands.size()); assertEquals(List.of(Query.CURRENT_RELATION), f.readQueries);
    }
    @Test void materialAndAllianceRechecksStillPrecedeFulfillmentAfterBridgeChange() {
        Fixture f = new Fixture();
        f.resolved(object(f.documents.family().get("resolved")).with("post_bridge_pid", n(78)));
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(snapshot()), baseline()));
        assertEquals(List.of(Query.CURRENT_RELATION, Query.FAMILY_RESULT), f.readQueries); assertTrue(f.commands.isEmpty());
        Obj resolved = object(f.documents.family().get("resolved"));
        f.resolved(resolved.with("alliance_result", object(resolved.get("alliance_result")).with("bridge_pid", n(78))));
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(snapshot()), baseline()));
        assertEquals(List.of(Query.CURRENT_RELATION, Query.FAMILY_RESULT, Query.CURRENT_RELATION, Query.FAMILY_ALLIANCE), f.readQueries);
        assertTrue(f.commands.isEmpty());
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot()), baseline()));
        assertEquals(STEP, selected.draft().command().orElseThrow().operation().value()); assertEquals(1, f.commands.size());
    }
    @Test void marriageAndAlreadyConsumedFulfillmentRepliesNeverPrepareAgain() {
        for (boolean priorFulfillment : List.of(false, true)) {
            Fixture f = new Fixture(); Obj resolved = object(f.documents.family().get("resolved"));
            f.resolved(priorFulfillment
                    ? resolved.with("source_pending", object(resolved.get("source_pending")).with("fulfill_existing_betrothal", new Bool(true)))
                    : resolved.with("status", t("marriage")));
            Obj detail = retainedBaselineObservation(f);
            assertEquals(f.documents.family().get("resolved"), detail.get("family_marriage_result_consumed"));
            assertNull(detail.get("current_betrothal_choice"), "consumed material never opens a second fulfillment choice");
        }
    }
    @Test void fulfillmentPendingDatesConvergeThroughTheRealReducerOnWarmAndColdReads() {
        for (boolean cold : List.of(false, true)) for (String status : List.of("pending", "accepted_pending")) {
            Fixture f = new Fixture();
            Obj pending = originalPending().with("fulfill_existing_betrothal", new Bool(true))
                    .with("last_consumed_checkpoint_native_revision", n(6)).with("last_consumed_checkpoint_date_raw", n(99));
            if (cold) pending = pending.with("source_bridge_pid", n(78));
            f.family(ledger(Slot.FAMILY).with("pending", pending));
            f.resultOverride = Optional.of(obj("status", t(status), "fulfill_existing_betrothal", new Bool(true),
                    "heir_character_id", n(3), "candidate_character_id", n(2), "post_native_revision", n(7)));
            assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(snapshot()), baseline()));
            Obj retained = object(f.documents.family().get("pending"));
            assertEquals(n(100), retained.get("last_checked_date_raw"));
            assertEquals(n(7), retained.get("last_checked_native_revision"));
            assertEquals(n(99), retained.get("source_date_raw"), "observation date does not rewrite the original proposal date");
            assertEquals(n(BRIDGE.pid()), retained.get("last_checked_bridge_pid"));
            assertEquals(f.documents.family(), FamilyDomainSource.validate(Slot.FAMILY, bytes(f.documents.family())),
                    "the stamped date survives the actual family document validator and JSON round trip");
            assertNull(retained.get("last_consumed_checkpoint_native_revision"));
            assertNull(retained.get("last_consumed_checkpoint_date_raw"));
            assertEquals(pending.get("candidate_character_id"), retained.get("candidate_character_id"));
            assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(snapshot()), baseline()));
            assertEquals(List.of(Query.FAMILY_RESULT), f.readQueries);
            Obj nextDay = snapshot().with("date_raw", n(101));
            assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(nextDay), baseline()));
            assertEquals(n(101), object(f.documents.family().get("pending")).get("last_checked_date_raw"));
            assertInstanceOf(OrdinaryPolicy.Replace.class, f.policy.evaluate(request(nextDay), baseline()));
            assertEquals(List.of(Query.FAMILY_RESULT, Query.FAMILY_RESULT), f.readQueries);
            assertTrue(f.commands.isEmpty(), "observing an unresolved fulfillment never resends");
        }
    }
    @Test void unavailableFulfillmentResultDoesNotStampAnObservationDate() {
        Fixture f = new Fixture(); f.resultUnavailable = true;
        f.family(ledger(Slot.FAMILY).with("pending", originalPending().with("fulfill_existing_betrothal", new Bool(true))));
        Obj before = f.documents.family();
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request(snapshot()), baseline()));
        assertEquals(before, f.documents.family()); assertTrue(f.commands.isEmpty());
    }
    @Test void fixedPairAdultLegalityAndUnknownReadsRetainTheirExistingGates() {
        Fixture minor = new Fixture(); Obj value = object(minor.relation.get("betrothal_actionability"));
        minor.relation = minor.relation.with("betrothal_actionability", value.with("heir_is_adult", new Bool(false))
                .with("heir_adult_measure_raw", n(18)).with("ready_to_marry_betrothed", new Bool(false)));
        Obj minorChoice = object(retainedBaselineObservation(minor).get("current_betrothal_choice"));
        assertEquals(t("held"), minorChoice.get("status"));
        assertTrue(array(minorChoice.get("reasons")).contains(t("actual_pair_not_ready")));
        Fixture illegal = new Fixture();
        illegal.relation = illegal.relation.with("betrothal_actionability", object(illegal.relation.get("betrothal_actionability")).with("complete_can_send", new Bool(false)));
        Obj illegalChoice = object(retainedBaselineObservation(illegal).get("current_betrothal_choice"));
        assertEquals(t("held"), illegalChoice.get("status"));
        assertTrue(array(illegalChoice.get("reasons")).contains(t("native_final_can_send_not_true")));
        Fixture coldUnknown = new Fixture(); coldUnknown.resultUnavailable = true;
        coldUnknown.resolved(object(coldUnknown.documents.family().get("resolved")).with("post_bridge_pid", n(78)));
        assertInstanceOf(OrdinaryPolicy.Wait.class, coldUnknown.policy.evaluate(request(snapshot()), baseline()));
        assertTrue(coldUnknown.commands.isEmpty()); assertEquals(List.of(Query.CURRENT_RELATION, Query.FAMILY_RESULT), coldUnknown.readQueries);
        Fixture alternative = new Fixture();
        assertInstanceOf(OrdinaryPolicy.Wait.class, alternative.policy.evaluateForCandidate(request(snapshot()), baseline(), BigInteger.TWO));
        assertTrue(alternative.commands.isEmpty());
        Fixture malformed = new Fixture(); Obj actionability = object(malformed.relation.get("betrothal_actionability"));
        malformed.relation = malformed.relation.with("betrothal_actionability", actionability.with("generic_costs",
                object(actionability.get("generic_costs")).with("gold_raw", new Bool(false))));
        assertInstanceOf(OrdinaryPolicy.Stop.class, malformed.policy.evaluate(request(snapshot()), baseline()));
        assertTrue(malformed.commands.isEmpty(), "a boolean cannot pass the actual integer cost decoder");
        Fixture changedPair = new Fixture();
        changedPair.relation = changedPair.relation.with("betrothed_character_id", n(5)).with("primary_spouse_character_id", n(2));
        Obj changedDetail = retainedBaselineObservation(changedPair);
        assertEquals(changedPair.documents.family().get("resolved"), changedDetail.get("family_marriage_result_consumed"));
        assertNull(changedDetail.get("current_betrothal_choice"), "prior material cannot authorize fulfillment of another current pair");
    }
}

