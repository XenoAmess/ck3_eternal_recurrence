package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningWire;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Software original-input -> real PlanningRequest/wire -> pure projection -> sole DATA serde.
 * No Game, collector, archive authority, native reader or action is constructed.
 */
final class OriginalPlanningFrameProjectionTest {
    private static final BigInteger WIDE = new BigInteger("18446744073709551615");
    private static Obj parse(String json) {
        return DriverJson.object(json.getBytes(StandardCharsets.UTF_8), 65536);
    }
    private static Obj snapshot(int actor) {
        return parse("""
                {"snapshot_id":"native:wide","revision":18446744073709551615,"native_revision":1,
                 "date_raw":1000,"episode_run_id":"software-episode","paused":true,"map_ready":true,
                 "played_character":{"character_id":%d},"diagnostics":{"connection_generation":18446744073709551615},
                 "active_wars":[],"player_armies":[]}
                """.formatted(actor));
    }
    private static PlanningRequest request(Obj snapshot) {
        Obj played = OpportunityJson.object(snapshot.get("played_character"), "played");
        BigInteger actor = OpportunityJson.integer(played.get("character_id"), "actor");
        var before = new ObservationIdentity("software-frame-projection",
                new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(actor, BigInteger.ONE, BigInteger.valueOf(1000)),
                        "native:wide", WIDE, "software-episode"), 1);
        var source = new G2Source(before.machineId(), "2026-10-24T00:00:00Z", "software-only",
                new ExactRef("software-source", 1, "a".repeat(64)));
        var observations = new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(),
                Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "software-session",
                Instant.parse("2026-10-24T00:01:00Z"), observations);
    }
    private static Obj roundtrip(Obj value) {
        return DriverJson.object(PublicDataJson.encodeTyped(value).bytes(), 65536);
    }

    @Test void sourceFramePreservesEightFieldsAndMissingBridgePidDoesNotMakeItPartial() {
        var actual = request(snapshot(73));
        var result = OriginalPlanningFrameProjection.sourceFrame(actual);
        assertEquals(parse("""
                {"schema":"xar.ck3.planning-source-frame/v1","status":"complete",
                 "snapshot_id":"native:wide","revision":18446744073709551615,"native_revision":1,
                 "date_raw":1000,"actor_character_id":73,"episode_run_id":"software-episode",
                 "connection_generation":18446744073709551615,"bridge_pid":null}
                """), roundtrip(result));
        for (Value bad : List.of(new Bool(true), new DecimalValue("1.0"), new Text("1"), Nil.INSTANCE)) {
            Obj diagnostic = new Obj(java.util.Map.of("connection_generation", bad));
            var frame = OriginalPlanningFrameProjection.sourceFrame(request(snapshot(73).with("diagnostics", diagnostic)));
            assertEquals(new Text("partial"), frame.get("status"));
            assertEquals(bad, frame.get("connection_generation"));
        }
        var absent = new java.util.LinkedHashMap<>(snapshot(73).members());
        absent.remove("diagnostics");
        assertEquals(Nil.INSTANCE, OriginalPlanningFrameProjection.sourceFrame(request(new Obj(absent))).get("connection_generation"));
    }

    @Test void cameraCopiesOriginalArmyNineFieldsObjectiveRowsAndNullAwareBuildFallback() {
        Obj observed = snapshot(73)
                .with("active_wars", parse("""
                  {"rows":[false,{"war_id":9,"allied_armies":[null,{"army_id":7,"current_province_id":3,
                   "in_combat":false,"controllable":true,"army_state":"moving","siege_days_left":-0.00,
                   "retreating":false,"move_target_province_id":4,"route_province_ids":[3,4],"ignored":99}],
                   "objective_province_states":[0,{"province_id":8,"active_siege":true,"ignored":42}],
                   "war_objective_province_ids":[8,9]}]}
                  """).get("rows"))
                .with("diagnostics", parse("""
                  {"connection_generation":1,"hello":{"expected_ck3_version":null,
                   "game_version":"fallback-must-not-replace-null","executable_sha256":"original-sha"}}
                  """))
                .with("active_event", new Bool(false))
                .with("pending_character_interaction", Nil.INSTANCE)
                .with("top_exclusive_modal_choice_hint", parse("{\"status\":\"present\"}"));
        Obj projected = OriginalPlanningFrameProjection.cameraInput(request(observed));
        Obj wire = roundtrip(projected);
        assertEquals(new Bool(true), wire.get("has_active_event"));
        assertEquals(new Bool(false), wire.get("has_pending_interaction"));
        assertEquals(new Bool(true), wire.get("mandatory_choice"));
        assertEquals(parse("{\"game_version\":null,\"executable_sha256\":\"original-sha\"}"), wire.get("source_build"));
        assertEquals(parse("""
                 {"rows":[{"war_id":9,"allied_armies":[{"army_id":7,"current_province_id":3,
                  "in_combat":false,"controllable":true,"army_state":"moving","siege_days_left":-0.00,
                  "retreating":false,"move_target_province_id":4,"route_province_ids":[3,4]}],
                  "objective_province_states":[{"province_id":8,"active_siege":true}],
                  "war_objective_province_ids":[8,9]}]}
                 """).get("rows"), wire.get("active_wars"));
        assertEquals(OriginalPlanningFrameProjection.sourceFrame(request(observed)), wire.get("source_frame"));
    }

    @Test void actualRequestAndWirePreserveIntentionalSignedRepairAndWideIntegerTokens() {
        for (int actor : new int[]{Integer.MIN_VALUE, -2, 0, 73, Integer.MAX_VALUE}) {
            var actual = PlanningWire.decodeRequest(PlanningWire.encodeRequest(request(snapshot(actor))));
            var result = roundtrip(OriginalPlanningFrameProjection.sourceFrame(actual));
            assertEquals(new Text("complete"), result.get("status"));
            assertEquals(new IntegerValue(BigInteger.valueOf(actor)), result.get("actor_character_id"));
            assertEquals(new IntegerValue(WIDE), result.get("revision"));
            assertEquals(new IntegerValue(WIDE), result.get("connection_generation"));
        }
        for (Value bad : List.of(new Bool(true), new DecimalValue("73.0"), new Text("73"),
                new IntegerValue(BigInteger.valueOf(-1)))) {
            Obj invalid = snapshot(73).with("played_character", new Obj(java.util.Map.of("character_id", bad)));
            assertThrows(IllegalArgumentException.class, () -> request(invalid));
        }
    }

    @Test void swayRetainsPresenceFallbackAndUsesOnlyActualSuppliedRootResult() {
        Obj root = parse("{\"campaign_root_context\":{\"status\":\"available\",\"player_character_id\":73,\"direct_landed_vassal_character_ids\":[9,10],\"ignored\":1}}");
        Obj base = snapshot(73).with("active_event", Nil.INSTANCE)
                .with("pending_character_interaction", new Bool(false));
        Obj result = roundtrip(OriginalPlanningFrameProjection.ordinarySwayInput(request(base), root));
        Obj compact = OpportunityJson.object(result.get("root"), "root");
        assertEquals(6, compact.members().size());
        assertEquals(Nil.INSTANCE, compact.get("snapshot_revision"));
        assertEquals(new Arr(List.of(new IntegerValue(BigInteger.valueOf(9)), new IntegerValue(BigInteger.TEN))),
                compact.get("direct_landed_vassal_character_ids"));
        Obj frame = OpportunityJson.object(result.get("snapshot"), "snapshot");
        assertEquals(parse("{\"active_event\":null,\"pending_character_interaction\":false}"), frame.get("active_context"));
        assertEquals(Nil.INSTANCE, frame.get("episode_character_id"));
        assertEquals(Nil.INSTANCE, frame.get("one_life_terminal_reason"));
        Obj missing = OriginalPlanningFrameProjection.ordinarySwayInput(request(snapshot(73)), Nil.INSTANCE);
        assertEquals(Nil.INSTANCE, missing.get("root"));
        assertEquals(Nil.INSTANCE, OpportunityJson.object(missing.get("snapshot"), "snapshot").get("active_context"));
        Obj explicit = parse("{\"active_event\":{\"id\":5},\"other\":null}");
        Obj chosen = OriginalPlanningFrameProjection.ordinarySwayInput(request(base.with("active_context", explicit)), root);
        assertEquals(explicit, OpportunityJson.object(chosen.get("snapshot"), "snapshot").get("active_context"));
    }

    @Test void activeArmyUsesExactTrueAndIntegerTypesWhileRouteNonListBecomesNull() {
        for (String army : List.of("{\"in_combat\":true}", "{\"retreating\":true}",
                "{\"move_target_province_id\":1}", "{\"army_state\":\"moving\"}",
                "{\"army_state\":\"siege\"}", "{\"army_state\":\"sieging\"}", "{\"army_state\":\"gathering\"}")) {
            var result = OriginalPlanningFrameProjection.cameraInput(request(snapshot(73)
                    .with("player_armies", new Arr(List.of(parse(army))))));
            assertEquals(new Bool(true), result.get("has_player_armies"));
        }
        var result = OriginalPlanningFrameProjection.cameraInput(request(snapshot(73)
                .with("player_armies", new Arr(List.of(parse("{\"in_combat\":1,\"retreating\":1,\"move_target_province_id\":1.0}"))))
                .with("active_wars", new Arr(List.of(parse("""
                    {"allied_armies":[{"route_province_ids":"not-a-list"}],
                     "war_objective_province_ids":"A😀"}
                    """))))));
        assertEquals(new Bool(false), result.get("has_player_armies"));
        Obj war = OpportunityJson.object(((Arr) result.get("active_wars")).items().getFirst(), "war");
        assertEquals(new Arr(List.of(new Text("A"), new Text("😀"))), war.get("war_objective_province_ids"));
        Obj army = OpportunityJson.object(((Arr) war.get("allied_armies")).items().getFirst(), "army");
        assertEquals(9, army.members().size());
        assertEquals(Nil.INSTANCE, army.get("route_province_ids"));
        assertEquals(Nil.INSTANCE, army.get("army_id"));
        assertEquals(result, roundtrip(result));
    }

    @Test void actualReadyRequestWireAndRawOverloadsShareTheIdenticalObservedInputs() {
        Obj root = parse("""
                {"campaign_root_context":{"status":"available","player_character_id":-2,
                 "player_character_alive":true,"snapshot_revision":18446744073709551615,
                 "date_raw":1000,"direct_landed_vassal_character_ids":[73]}}
                """);
        var actual = PlanningWire.decodeRequest(PlanningWire.encodeRequest(request(snapshot(-2)
                .with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE))));
        Obj sameSnapshot = actual.observations().snapshot();
        G2Source sameSource = actual.source();
        assertEquals(OriginalPlanningFrameProjection.sourceFrame(actual),
                OriginalPlanningFrameProjection.sourceFrame(sameSnapshot));
        assertEquals(OriginalPlanningFrameProjection.cameraInput(actual),
                OriginalPlanningFrameProjection.cameraInput(sameSnapshot));
        assertEquals(OriginalPlanningFrameProjection.ordinarySwayInput(actual, root),
                OriginalPlanningFrameProjection.ordinarySwayInput(sameSnapshot, root));
        assertSame(sameSnapshot, actual.observations().snapshot());
        assertSame(sameSource, actual.source());
        assertEquals(new IntegerValue(BigInteger.valueOf(-2)),
                OriginalPlanningFrameProjection.sourceFrame(sameSnapshot).get("actor_character_id"));
        assertFalse(OriginalPlanningFrameProjection.sourceFrame(sameSnapshot).members().containsKey("source"));
    }

    @Test void rawTerminalMissingNullAndChangedActorNeverRequireOrRepairAPlanningRequest() {
        var missingFields = new java.util.LinkedHashMap<>(snapshot(73).members());
        missingFields.remove("played_character");
        missingFields.remove("diagnostics");
        Obj missing = new Obj(missingFields);
        Obj nullActor = snapshot(73).with("played_character", Nil.INSTANCE);
        for (Obj raw : List.of(missing, nullActor,
                snapshot(73).with("played_character", new Obj(java.util.Map.of("character_id", Nil.INSTANCE))))) {
            Obj frame = OriginalPlanningFrameProjection.sourceFrame(raw);
            assertEquals(new Text("partial"), frame.get("status"));
            assertEquals(Nil.INSTANCE, frame.get("actor_character_id"));
            assertEquals(new IntegerValue(WIDE), frame.get("revision"));
            assertEquals(frame, OriginalPlanningFrameProjection.cameraInput(raw).get("source_frame"));
            Obj projected = OriginalPlanningFrameProjection.ordinarySwayInput(raw, Nil.INSTANCE);
            assertEquals(Nil.INSTANCE, projected.get("root"));
            Value originalPlayed = raw.get("played_character");
            assertEquals(originalPlayed instanceof Obj ? originalPlayed : Nil.INSTANCE,
                    OpportunityJson.object(projected.get("snapshot"), "snapshot").get("played_character"));
        }
        assertEquals(Nil.INSTANCE, OriginalPlanningFrameProjection.sourceFrame(missing).get("connection_generation"));
        Obj changedActor = parse("{\"character_id\":88,\"alive\":false,\"raw_detail\":null}");
        Obj terminal = snapshot(73).with("played_character", changedActor)
                .with("episode_character_id", new IntegerValue(BigInteger.valueOf(73)))
                .with("one_life_terminal_reason", new Text("actual_changed_actor_not_reconciled"));
        Obj frame = OriginalPlanningFrameProjection.sourceFrame(terminal);
        // Original complete is only a DATA-shape status, including on an unreconciled raw actor.
        assertEquals(new Text("complete"), frame.get("status"));
        assertEquals(new IntegerValue(BigInteger.valueOf(88)), frame.get("actor_character_id"));
        Obj compact = OpportunityJson.object(OriginalPlanningFrameProjection.ordinarySwayInput(terminal, Nil.INSTANCE)
                .get("snapshot"), "snapshot");
        assertEquals(changedActor, compact.get("played_character"));
        assertEquals(new IntegerValue(BigInteger.valueOf(73)), compact.get("episode_character_id"));
        assertEquals(new Text("actual_changed_actor_not_reconciled"), compact.get("one_life_terminal_reason"));
        assertEquals(Nil.INSTANCE, compact.get("active_context"));
        Obj explicitNulls = terminal.with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE);
        assertEquals(parse("{\"active_event\":null,\"pending_character_interaction\":null}"),
                OpportunityJson.object(OriginalPlanningFrameProjection.ordinarySwayInput(explicitNulls, Nil.INSTANCE)
                        .get("snapshot"), "snapshot").get("active_context"));
        assertFalse(missing.members().containsKey("played_character"));
        assertEquals(Nil.INSTANCE, nullActor.get("played_character"));
        for (Value originalActor : List.of(new Bool(true), new DecimalValue("73.0"), new Text("73"),
                new IntegerValue(BigInteger.valueOf(-1)))) {
            Obj raw = snapshot(73).with("played_character", new Obj(java.util.Map.of("character_id", originalActor)));
            Obj projected = OriginalPlanningFrameProjection.sourceFrame(raw);
            assertEquals(new Text("partial"), projected.get("status"));
            assertEquals(originalActor, projected.get("actor_character_id"));
        }
    }

    @Test void rawProjectionRetainsLargeIntegersAndDecimalTokensWithoutAProtocolOrWidthConversion() {
        BigInteger large = BigInteger.ONE.shiftLeft(160).add(BigInteger.valueOf(73));
        Obj observed = snapshot(73).with("revision", new IntegerValue(large))
                .with("diagnostics", parse("{\"connection_generation\":null,\"hello\":{\"expected_ck3_version\":null,\"game_version\":\"no-fallback\"}}"))
                .with("active_wars", new Arr(List.of(parse("{\"allied_armies\":[{\"siege_days_left\":-0.0000}]}"))));
        Obj source = OriginalPlanningFrameProjection.sourceFrame(observed);
        assertEquals(new IntegerValue(large), source.get("revision"));
        assertEquals(new Text("partial"), source.get("status"));
        Obj camera = OriginalPlanningFrameProjection.cameraInput(observed);
        Obj war = OpportunityJson.object(((Arr) camera.get("active_wars")).items().getFirst(), "war");
        Obj army = OpportunityJson.object(((Arr) war.get("allied_armies")).items().getFirst(), "army");
        assertEquals(new DecimalValue("-0.0000"), army.get("siege_days_left"));
        assertEquals(Nil.INSTANCE, OpportunityJson.object(camera.get("source_build"), "source_build").get("game_version"));
        Obj encoded = DriverJson.object(PublicDataJson.encodeFullMaterial(camera).bytes(), 65536);
        assertEquals(camera, encoded);
        assertEquals(new IntegerValue(large), OpportunityJson.object(encoded.get("source_frame"), "source_frame").get("revision"));
        assertFalse(observed.members().containsKey("active_event"));
    }
}
