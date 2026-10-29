package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageAlliance;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Public policy -> real alliance producer -> exact read receipt -> real shared reducer -> next turn.
 * Result packets and custody are software inputs; no Game qualification is granted. */
final class FamilyMatrilinealMaterialContinuationTest {
    private static final ExactRef SOURCE = ref("software-matrilineal-source");
    private static final FamilyPorts.BridgeIdentity CURRENT = new FamilyPorts.BridgeIdentity(41, "2026-10-26T08:00:00Z");
    private static final FamilyPorts.BridgeIdentity OLD = new FamilyPorts.BridgeIdentity(31, "2026-10-25T08:00:00Z");
    private static final Instant NOW = Instant.parse("2026-10-26T08:00:00Z");
    private static ExactRef ref(String path) { return new ExactRef(path, 1, "a".repeat(64)); }
    private static Obj domain() { return obj("pending", Nil.INSTANCE, "resolved", Nil.INSTANCE); }
    private static Obj bound(Obj original, FamilyPorts.BridgeIdentity bridge, String prefix) {
        return original.with(prefix + "bridge_pid", n(bridge.pid())).with(prefix + "bridge_creation_date", t(bridge.creationDate()));
    }
    private static Obj pending() {
        return bound(obj("episode_run_id", t("software-matrilineal-episode"), "played_character_id", n(1),
                "heir_character_id", n(11), "candidate_character_id", n(12), "recipient_character_id", n(13),
                "source_date_raw", n(53000000), "pre_native_revision", n(7)), OLD, "source_");
    }
    private static Obj resolved(FamilyPorts.BridgeIdentity relationBridge, FamilyPorts.BridgeIdentity allianceBridge) {
        // The actual normalized alliance producer has no Bridge fields. The reducer owns the outer binding.
        Obj alliance = nativeAlliance(FamilyPorts.Query.MATRILINEAL_ALLIANCE);
        return bound(bound(obj("episode_run_id", t("software-matrilineal-episode"), "status", t("marriage"),
                "material_result", new Bool(true), "heir_character_id", n(11), "candidate_character_id", n(12),
                "source_pending", pending(), "actual_alliance_result", alliance), relationBridge, "post_"), allianceBridge, "alliance_");
    }
    private static PlanningRequest request() {
        var source = new G2Source("software-matrilineal-no-game", NOW.toString(), "software-only", SOURCE);
        Obj snapshot = obj("snapshot_id", t("native:9"), "revision", n(10), "native_revision", n(9),
                "date_raw", n(53000024), "episode_run_id", t("software-matrilineal-episode"),
                "paused", new Bool(true), "map_ready", new Bool(true), "active_wars", rows(List.of()),
                "player_armies", rows(List.of()), "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(1), "alive", new Bool(true)));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,
                BigInteger.valueOf(9), BigInteger.valueOf(53000024)), "native:9", BigInteger.TEN, "software-matrilineal-episode");
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        return new PlanningRequest(before, source, "software-matrilineal-session", NOW.plusSeconds(30),
                new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(),
                        Optional.empty(), Optional.empty(), false));
    }
    private static OrdinaryPolicy.Draft baseline() {
        return new OrdinaryPolicy.Draft("one-life-turn-v1", "software-baseline", "existing ordinary turn",
                OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                Optional.empty(), obj("selected_step", t("life-advance")));
    }
    private record Consumption(FamilyPorts.Query query, Obj arguments, FamilyPorts.ObservedRead observed) { }
    private static final class Fixture {
        private final List<FamilyPorts.Query> queries = new ArrayList<>();
        private final List<Obj> arguments = new ArrayList<>();
        private final List<Consumption> consumed = new ArrayList<>();
        private FamilyPorts.Documents documents;
        private final FamilyOrdinaryPolicy policy;
        private boolean unavailable;
        private int commandPreparations;
        private Fixture(Obj body) { this(body, false); }
        private Fixture(Obj body, boolean childDefault) {
            documents = new FamilyPorts.Documents(domain(), body, domain(), CURRENT, ref("software-head"),
                    List.of(ref("family"), ref("matrilineal"), ref("default")));
            var projections = new EnumMap<FamilyPorts.Query, FamilyPorts.ProjectedSource>(FamilyPorts.Query.class);
            for (var query : List.of(FamilyPorts.Query.MATRILINEAL_RESULT, FamilyPorts.Query.MATRILINEAL_ALLIANCE,
                    FamilyPorts.Query.DEFAULT_RESULT, FamilyPorts.Query.DEFAULT_ALLIANCE)) {
                projections.put(query, new FamilyPorts.ProjectedSource() {
                    @Override public FamilyPorts.ProjectedRead read(PlanningRequest actual, Obj args) {
                        queries.add(query); arguments.add(args);
                        if (unavailable) return new FamilyPorts.ProjectedRead(args,
                                new PlanningReadResult.Unavailable<>("software native result unavailable", Optional.empty()));
                        Obj value = query == FamilyPorts.Query.MATRILINEAL_RESULT || query == FamilyPorts.Query.DEFAULT_RESULT
                                ? obj("status", t("marriage"), "material_result", new Bool(true), "post_native_revision", n(9))
                                : nativeAlliance(query);
                        return softwareRead(actual, query, args, value);
                    }
                    @Override public Obj decode(PlanningReadReceipt receipt) {
                        throw new AssertionError("the current material continuation must use the actual read result");
                    }
                });
            }
            policy = new FamilyOrdinaryPolicy(SOURCE, new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest actual) {
                    throw new AssertionError("the installed projected read must be used");
                }
            }, new FamilyPorts.Reads(Map.of(), projections), actual -> new FamilyPorts.KnownDocuments(documents),
                    (actual, operation, args, plan) -> {
                        commandPreparations++;
                        throw new AssertionError("a retained material or UNKNOWN proposal must not prepare another send");
                    }, (actual, query, args, observed) -> {
                        consumed.add(new Consumption(query, args, observed));
                        Obj ledger = childDefault ? documents.childDefault() : documents.matrilineal();
                        Obj reduced = FamilyResultReducer.reduce(query, ledger, args, observed.value(), CURRENT, observed.receipt().request().before().frame().identity().dateRaw());
                        documents = new FamilyPorts.Documents(documents.family(), childDefault ? documents.matrilineal() : reduced,
                                childDefault ? reduced : documents.childDefault(), CURRENT, documents.canonicalHead(), documents.importedDocuments());
                        return true;
                    }, new FamilyPorts.Settings(false, false, false, childDefault, childDefault ? Optional.empty()
                            : Optional.of(new FamilyPorts.Pair(BigInteger.valueOf(11), BigInteger.valueOf(12)))));
            if (childDefault) documents = new FamilyPorts.Documents(domain(), domain(), body, CURRENT,
                    documents.canonicalHead(), documents.importedDocuments());
        }
        private Fixture(FamilyPorts.BridgeIdentity relationBridge, FamilyPorts.BridgeIdentity allianceBridge) {
            this(obj("pending", Nil.INSTANCE, "resolved", resolved(relationBridge, allianceBridge)));
        }
    }
    private static Obj nativeAlliance(FamilyPorts.Query query) {
        var route = query == FamilyPorts.Query.DEFAULT_ALLIANCE ? FamilyMarriageResults.Route.DEFAULT : FamilyMarriageResults.Route.MATRILINEAL;
        var binding = new FamilyMarriageAlliance.Binding(route, InteractionModels.Build.CROZIER4, "native:9", BigInteger.TEN,
                BigInteger.valueOf(9), BigInteger.valueOf(53000024), BigInteger.ONE, BigInteger.valueOf(13),
                BigInteger.valueOf(11), BigInteger.valueOf(12), FamilyMarriageResults.Relationship.MARRIAGE);
        return FamilyMarriageAlliance.project(new FamilyMarriageAlliance.Observation(binding,
                FamilyMarriageAlliance.AllianceStatus.NOT_ALLIED, false, false));
    }
    private static FamilyPorts.ProjectedRead softwareRead(PlanningRequest actual, FamilyPorts.Query query, Obj args, Obj value) {
        String id = "software-matrilineal-read";
        var request = new PlanningReadRequest(actual.before(), actual.source(), actual.sessionId(), query.operation(), args, actual.deadline());
        var raw = new RawJson(bytes(obj("type", t("command_result"), "protocol_version", n(1), "request_id", t(id),
                "ok", new Bool(true), "result", value)));
        byte[] encoded = raw.bytes();
        byte[] packet = ByteBuffer.allocate(encoded.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(encoded.length).put(encoded).array();
        Obj decoded = object(object(OpportunityJson.parse(raw.bytes())).get("result"));
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(bytes(decoded))), raw, packet);
        var guard = new PlanningReadGuard(new GuardEvidence(actual.before(), actual.source(), actual.sessionId(), BigInteger.ONE,
                query.operation(), SOURCE, SOURCE, "software-matrilineal-no-game-custody", NOW, actual.deadline()),
                true, true, true, "b".repeat(64));
        var receipt = new PlanningReadReceipt(request, "software-matrilineal-contract:" + query.name(), id, guard, guard, ack);
        return new FamilyPorts.ProjectedRead(args, new PlanningReadResult.Known<>(decoded, receipt, ref("software-read")));
    }

    @Test void coldMaterialWithOldAllianceFirstRechecksTheOriginalPairThroughTheExistingResultConsumer() {
        Fixture f = new Fixture(OLD, OLD);
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_RESULT), f.queries);
        assertEquals(pending(), f.arguments.getFirst().get("pending"));
        assertEquals(new Bool(true), f.arguments.getFirst().get("cold"));
        assertEquals(new Bool(true), f.arguments.getFirst().get("material_recheck"));
        assertEquals(n(10), f.arguments.getFirst().get("expected_revision"));
        assertEquals(1, f.consumed.size());
        assertEquals(FamilyPorts.Query.MATRILINEAL_RESULT, f.consumed.getFirst().query());
        assertEquals(f.arguments.getFirst(), f.consumed.getFirst().observed().receipt().request().arguments());
        Obj rechecked = object(f.documents.matrilineal().get("resolved"));
        assertEquals(pending(), rechecked.get("source_pending"));
        assertTrue(CURRENT.matches(rechecked, "post_"));
        assertNull(rechecked.get("actual_alliance_result"));
        assertNull(rechecked.get("alliance_bridge_pid"));
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(), baseline()));
        Obj settled = object(f.documents.matrilineal().get("resolved"));
        assertTrue(CURRENT.matches(settled, "alliance_"));
        assertNull(object(settled.get("actual_alliance_result")).get("bridge_pid"));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_RESULT, FamilyPorts.Query.MATRILINEAL_ALLIANCE), f.queries);
        assertEquals(2, f.consumed.size()); assertEquals(0, f.commandPreparations);
    }
    @Test void warmMaterialWithStaleAllianceRechecksBothDirectionsThroughTheSeparateAllianceConsumer() {
        Fixture f = new Fixture(CURRENT, OLD); Value before = f.documents.matrilineal().get("resolved");
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_ALLIANCE), f.queries);
        assertEquals(before, f.arguments.getFirst().get("resolved"));
        assertEquals(1, f.consumed.size());
        assertEquals(FamilyPorts.Query.MATRILINEAL_ALLIANCE, f.consumed.getFirst().query());
        assertEquals(t("not_allied"), f.consumed.getFirst().observed().value().get("alliance_status"));
        assertEquals(new Bool(false), f.consumed.getFirst().observed().value().get("played_has_recipient_alliance"));
        assertEquals(new Bool(false), f.consumed.getFirst().observed().value().get("recipient_has_played_alliance"));
        assertTrue(CURRENT.matches(object(f.documents.matrilineal().get("resolved")), "alliance_"));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(), baseline()));
        assertEquals(1, f.queries.size());
        assertEquals(0, f.commandPreparations);
    }
    @Test void currentMaterialAndCurrentAllianceRetainTheResultWithoutAnotherReadOrSend() {
        Fixture f = new Fixture(CURRENT, CURRENT);
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(), baseline()));
        assertTrue(f.queries.isEmpty()); assertTrue(f.consumed.isEmpty()); assertEquals(0, f.commandPreparations);
    }
    @Test void unavailableColdReadRetainsTheOriginalMaterialAndDoesNotManufactureAReplyOrRetry() {
        Fixture f = new Fixture(OLD, OLD); f.unavailable = true;
        byte[] before = bytes(f.documents.matrilineal());
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_RESULT), f.queries);
        assertTrue(f.consumed.isEmpty()); assertArrayEquals(before, bytes(f.documents.matrilineal()));
        assertEquals(0, f.commandPreparations);
    }
    @Test void coldUnknownPendingUsesTheOriginalResultReadWithoutPreparingAnotherProposal() {
        Fixture f = new Fixture(obj("pending", pending(), "resolved", Nil.INSTANCE)); f.unavailable = true;
        byte[] before = bytes(f.documents.matrilineal());
        assertInstanceOf(OrdinaryPolicy.Wait.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_RESULT), f.queries);
        assertEquals(pending(), f.arguments.getFirst().get("pending"));
        assertEquals(new Bool(true), f.arguments.getFirst().get("cold"));
        assertTrue(f.consumed.isEmpty()); assertArrayEquals(before, bytes(f.documents.matrilineal()));
        assertEquals(0, f.commandPreparations);
    }
    @Test void explicitNullAllianceCannotBorrowAnOuterBindingWithoutAnActualBilateralResult() {
        Obj resolved = resolved(CURRENT, CURRENT).with("actual_alliance_result", Nil.INSTANCE);
        Fixture f = new Fixture(obj("pending", Nil.INSTANCE, "resolved", resolved));
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.MATRILINEAL_ALLIANCE), f.queries);
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(), baseline()));
        assertEquals(1, f.queries.size()); assertEquals(0, f.commandPreparations);
    }
    @Test void defaultChildUsesTheSameOuterBindingAndDoesNotRepeatACompletedAllianceRead() {
        Fixture f = new Fixture(obj("pending", Nil.INSTANCE, "resolved", resolved(CURRENT, OLD)), true);
        assertInstanceOf(OrdinaryPolicy.Refresh.class, f.policy.evaluate(request(), baseline()));
        assertEquals(List.of(FamilyPorts.Query.DEFAULT_ALLIANCE), f.queries);
        Obj settled = object(f.documents.childDefault().get("resolved"));
        assertTrue(CURRENT.matches(settled, "alliance_"));
        assertNull(object(settled.get("actual_alliance_result")).get("bridge_pid"));
        assertInstanceOf(OrdinaryPolicy.Keep.class, f.policy.evaluate(request(), baseline()));
        assertEquals(1, f.queries.size()); assertEquals(0, f.commandPreparations);
    }
}
