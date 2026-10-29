package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.governance.council.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original native Council producer -> shared DTO -> actual native request builder; other vectors are labelled synthetic. */
final class GovernanceActionPreparationTest {
    private static final String SHA = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final Instant NOW = Instant.parse("2026-10-23T18:00:00Z");
    private static final ExactRef REF = new ExactRef("synthetic-source-identity-no-runtime-qualification", 1, "a".repeat(64));
    private static ActionCommand command(String step, Obj args, String snapshot, long publicRevision, long nativeRevision, long date) {
        var source = new G2Source("xenoamess-full-tower-eb9d2c1186", NOW.toString(), "1.20.0.2", REF);
        var before = new ObservationIdentity(source.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777217), BigInteger.valueOf(nativeRevision), BigInteger.valueOf(date)), snapshot, BigInteger.valueOf(publicRevision), "synthetic-preparation-episode"), 1);
        return new ActionCommand("governance-preparation-test", before, source, "synthetic-session", new OperationKey(step), args,
                new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION, before, source, "xar.java.governance-independent-effect/v1", List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static GovernanceActionPreparation producer() {
        return new GovernanceActionPreparation("1.20.0.2", SHA,
                (borrowed, command, requestId) -> { throw new AssertionError("private Council refresh cannot run without its real borrowed writer/scope"); },
                (borrowed, command) -> { throw new AssertionError("LIFE refresh must borrow the actual writer"); });
    }
    @Test void nativeOriginalPublicCouncilTraversesSharedCodecAndExactPreparation() throws Exception {
        String root = System.getProperty("xar.repository.root"); assertNotNull(root, "required original native repository missing");
        var original = StrictJson.parse(Files.readAllBytes(Path.of(root, "ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json"))).get("result").get("council_composition_candidates");
        var frame = new CouncilModels.Frame("native:council12002", BigInteger.valueOf(8), BigInteger.valueOf(7), 53178264, 16777217);
        var typed = CouncilCodec.decodeNative(StrictJson.canonical(original), frame, CouncilModels.Position.STEWARD, "1.20.0.2", SHA);
        Obj args = new Obj(java.util.Map.of()).with("position_key", new Text("councillor_steward")).with("candidate_character_id", new IntegerValue(BigInteger.valueOf(16777232))).with("original_query", parse(CouncilCodec.encode(typed))).with("expected_has_incumbent", new Bool(true)).with("expected_incumbent_character_id", new IntegerValue(BigInteger.valueOf(16777218)));
        NativeRequest request = producer().prepare(command(CouncilActionCodec.ASSIGN, args, frame.snapshotId(), 8, 7, frame.dateRaw()), "step-101-exact");
        assertEquals(Optional.of("game.action.assign-councillor-v1"), request.requiredCapability());
        var wire = StrictJson.parse(request.additionalFields().bytes()); assertEquals(7, wire.get("expected_native_revision").intValue());
        assertEquals(8, wire.get("expected_public_revision").intValue()); assertEquals(16777232, wire.get("candidate_character_id").intValue());
        Obj wrong = args.with("expected_has_incumbent", new IntegerValue(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> producer().prepare(command(CouncilActionCodec.ASSIGN, wrong, frame.snapshotId(), 8, 7, frame.dateRaw()), "step-102-wrong"));
    }
    @Test void syntheticFocusProjectionPreservesPublicFrameButUsesActualNativeSnapshotOnWire() {
        Obj ready = new Obj(java.util.Map.of()).with("same_frame_ready", new Bool(true)).with("legal_focus_candidates_ready", new Bool(true));
        Obj snapshot = new Obj(java.util.Map.of()).with("snapshot_id", new Text("public:100")).with("episode_run_id", new Text("synthetic-preparation-episode")).with("public_revision", new IntegerValue(BigInteger.valueOf(100))).with("native_revision", new IntegerValue(BigInteger.valueOf(40))).with("proof_epoch", new IntegerValue(BigInteger.valueOf(40))).with("date_raw", new IntegerValue(BigInteger.valueOf(53169072))).with("player_character_id", new IntegerValue(BigInteger.valueOf(16777217))).with("readiness", ready).with("legal_focus_candidates", new Obj(java.util.Map.of()).with("status", new Text("available")).with("items", new Arr(List.of(new Obj(java.util.Map.of()).with("key", new Text("martial_authority_focus")).with("lifestyle_key", new Text("martial_lifestyle"))))));
        Obj query = new Obj(java.util.Map.of()).with("status", new Text("stock_focus_available")).with("formal_precondition_status", new Text("stock_focus_ready")).with("episode_run_id", new Text("synthetic-preparation-episode")).with("snapshot", snapshot).with("source_frame", new Obj(java.util.Map.of()).with("snapshot_id", new Text("public:100")).with("revision", new IntegerValue(BigInteger.valueOf(100))).with("native_revision", new IntegerValue(BigInteger.valueOf(40))).with("date_raw", new IntegerValue(BigInteger.valueOf(53169072))).with("player_character_id", new IntegerValue(BigInteger.valueOf(16777217)))).with("focus_query", new Obj(java.util.Map.of()).with("native_legal", new Bool(true)).with("target_key", new Text("martial_authority_focus")));
        Obj args = new Obj(java.util.Map.of()).with("target_key", new Text("martial_authority_focus")).with("target_lifestyle_key", new Text("martial_lifestyle")).with("original_query", query).with("decision", new Obj(java.util.Map.of()));
        var prepared = producer().prepare(command(GovernanceActionPreparation.FOCUS, args, "public:100", 100, 40, 53169072), "step-103-focus");
        var wire = StrictJson.parse(prepared.additionalFields().bytes());
        assertEquals("native:40", wire.get("expected_snapshot_id").textValue()); assertEquals(40, wire.get("expected_proof_epoch").intValue());
        assertFalse(wire.has("target_lifestyle_key")); assertFalse(wire.has("original_query"));
        assertDoesNotThrow(() -> GovernanceActionBindings.validateWire(prepared));
        Obj falseQuery = query.with("focus_query", new Obj(java.util.Map.of()).with("native_legal", new Bool(false)).with("target_key", new Text("martial_authority_focus")));
        assertThrows(IllegalArgumentException.class, () -> producer().prepare(command(GovernanceActionPreparation.FOCUS, args.with("original_query", falseQuery), "public:100", 100, 40, 53169072), "step-104-invalid"));
    }
    @Test void privateCouncilWithoutBorrowedWriterCannotRefreshOrSubmitAndWireFieldsStayClosed() {
        assertThrows(IllegalArgumentException.class, () -> producer().prepare(command(CouncilActionCodec.PRIVATE_ASSIGN, new Obj(java.util.Map.of()), "native:13", 13, 13, 53175816), "step-105-private"));
        var malformed = new NativeRequest(CouncilActionCodec.PRIVATE_ASSIGN, Optional.empty(), new RawJson(StrictJson.canonical(StrictJson.object().put("candidate_character_id", 16777232).put("expected_revision", 13))));
        assertThrows(IllegalArgumentException.class, () -> GovernanceActionBindings.validateWire(malformed));
    }
    @Test void retainedCrownNativeQueryTraversesRealNormalizerSharedPolicyAndSubmitProducer() throws Exception {
        String root = System.getProperty("xar.repository.root"); assertNotNull(root);
        var original = CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,
                "ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_realm_law_action/wire-law-crown-query.json"))).get("result"));
        var placeholder = command(GovernanceActionPreparation.CROWN, new Obj(java.util.Map.of()), "public:100", 100, 40, 53169072);
        var read = new PlanningReadRequest(placeholder.before(), placeholder.source(), placeholder.sessionId(), new OperationKey(GovernancePlanningReads.CROWN), new Obj(java.util.Map.of()), placeholder.deadline());
        ObjectNode normalized = GovernancePlanningReads.crown(original, read, "1.20.0.2", SHA);
        var readback = org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.decodeReadback(StrictJson.canonical(normalized));
        var choice = org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.choose(readback);
        Obj args = new Obj(java.util.Map.of()).with("readback", parse(StrictJson.canonical(normalized))).with("law_key", new Text(choice.lawKey())).with("choice", parse(org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec.encodeChoice(choice)));
        var prepared = producer().prepare(command(GovernanceActionPreparation.CROWN, args, "public:100", 100, 40, 53169072), "original-crown-101");
        assertDoesNotThrow(() -> GovernanceActionBindings.validateWire(prepared));
        var wire = StrictJson.parse(prepared.additionalFields().bytes()); assertEquals("original-crown-101", wire.get("submitted_request_id").textValue());
        assertEquals("crown_authority_1", wire.get("law_key").textValue()); assertEquals(20000000, wire.get("budget_prestige_raw").intValue());
        assertEquals("public:100", normalized.get("queried_snapshot_id").textValue()); assertEquals(100, normalized.get("queried_revision").intValue());
        assertEquals(40, normalized.get("snapshot_revision").intValue()); assertFalse(wire.has("expected_snapshot_revision"));
        ObjectNode wrong = original.deepCopy(); ((ObjectNode) wrong.get("observation")).put("snapshot_revision", 100);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.crown(wrong, read, "1.20.0.2", SHA));
        ObjectNode wrongKind = original.deepCopy(); ((ObjectNode) wrongKind.get("observation")).put("available", 1);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.crown(wrongKind, read, "1.20.0.2", SHA));
    }
    @Test void syntheticNativeLifeStatePlusFinalFocusTraversesRealCompositionAndProducer() {
        ObjectNode state = CouncilCodec.object(StrictJson.parse("""
                {"step":"private-query-player-lifestyle-current-state-v1","private_build":true,"advertised":false,"status":"available","episode_run_id":"synthetic-preparation-episode","snapshot":{
                  "private_build":true,"advertised":false,"status":"available","snapshot_id":"native:40","public_revision":40,"native_revision":40,"proof_epoch":40,"date_raw":53169072,"player_character_id":16777217,
                  "current_focus":{"presence":"absent"},"current_lifestyle_progress":{"presence":"absent"},"owned_perk_keys":[],"actor_traits":{"status":"available","observed_keys":[]},
                  "legal_focus_candidates":{"status":"unavailable","reason":"not_requested","items":[]},"legal_perk_candidates":{"status":"unavailable","reason":"not_requested","items":[]},
                  "readiness":{"current_focus_ready":true,"lifestyle_progress_ready":true,"owned_perks_ready":true,"legal_focus_candidates_ready":false,"legal_perk_candidates_ready":false,"same_frame_ready":true}}}
                """.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        ObjectNode focus = CouncilCodec.object(StrictJson.parse("""
                {"step":"private-query-player-lifestyle-martial-authority-v1","private_build":true,"advertised":false,"status":"observed_native_legal","read_only":true,"policy_scoped":true,
                 "episode_run_id":"synthetic-preparation-episode","snapshot_id":"native:40","target_key":"martial_authority_focus","native_legal":true,"scanned_database_rows":20,"target_lifestyle_key":"martial_lifestyle",
                 "target_lifestyle_progress":{"presence":"present","source":"exact_native_getters","xp_total_raw":0,"xp_within_level_raw":0,"xp_per_level":1000,"unspent_perk_points":0,"used_perk_points":0}}
                """.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var parent = command(GovernanceActionPreparation.FOCUS, new Obj(java.util.Map.of()), "public:100", 100, 40, 53169072);
        var read = new PlanningReadRequest(parent.before(), parent.source(), parent.sessionId(), new OperationKey(GovernancePlanningReads.STATE), new Obj(java.util.Map.of()), parent.deadline());
        var normalizedState = GovernancePlanningReads.life(state, read, GovernancePlanningReads.STATE);
        var normalizedFocus = GovernancePlanningReads.focus(focus, read, GovernancePlanningReads.MARTIAL);
        var combined = GovernancePlanningReads.combine(normalizedState, normalizedFocus);
        assertEquals("public:100", combined.get("snapshot").get("snapshot_id").textValue());
        assertEquals(100, combined.get("snapshot").get("public_revision").intValue()); assertEquals(40, combined.get("snapshot").get("proof_epoch").intValue());
        Obj args = new Obj(java.util.Map.of()).with("target_key", new Text("martial_authority_focus")).with("target_lifestyle_key", new Text("martial_lifestyle")).with("original_query", parse(StrictJson.canonical(combined))).with("decision", new Obj(java.util.Map.of()));
        var prepared = producer().prepare(command(GovernanceActionPreparation.FOCUS, args, "public:100", 100, 40, 53169072), "focus-composed-102");
        assertEquals("native:40", StrictJson.parse(prepared.additionalFields().bytes()).get("expected_snapshot_id").textValue());
        var illegalFocus = focus.deepCopy().put("status", "observed_native_illegal").put("native_legal", false);
        var normalizedIllegal = GovernancePlanningReads.focus(illegalFocus, read, GovernancePlanningReads.MARTIAL);
        var blocked = GovernancePlanningReads.combine(normalizedState, normalizedIllegal);
        assertEquals("stock_focus_readback_red", blocked.get("status").textValue());
        assertEquals(normalizedState, blocked.get("state")); assertEquals(normalizedIllegal, blocked.get("focus"));
        assertFalse(blocked.at("/focus/native_legal").booleanValue());
        assertFalse(blocked.has("snapshot")); assertFalse(blocked.has("focus_query"));
        var consumer = StrictJson.object().put("schema", org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumerCodec.SCHEMA)
                .put("preferred_focus_target_key", "martial_authority_focus").put("allow_wartime_initial_focus", true);
        consumer.putObject("baseline_plan").put("selected_step", "life-advance");
        consumer.putObject("scope").put("status", "admitted").put("at_peace", true).put("government_key", "feudal_government");
        consumer.set("query", blocked);
        var decision = org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.consume(
                org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumerCodec.decode(StrictJson.canonical(consumer)));
        assertEquals(org.xar.ck3.control.wave2.planning.lifestyleconsumer.LifestyleConsumer.Route.NATIVE_QUERY_UNAVAILABLE, decision.route());
        Obj blockedArgs = args.with("original_query", parse(StrictJson.canonical(blocked)));
        assertThrows(IllegalArgumentException.class, () -> producer().prepare(command(GovernanceActionPreparation.FOCUS, blockedArgs,
                "public:100", 100, 40, 53169072), "focus-illegal-must-not-submit"));
        var wrongLegalType = focus.deepCopy().put("native_legal", 1);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.focus(wrongLegalType, read, GovernancePlanningReads.MARTIAL));
        var crossedIllegal = normalizedIllegal.deepCopy(); crossedIllegal.putObject("source_frame").put("native_revision", 41);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.combine(normalizedState, crossedIllegal));
        var wrongFrame = state.deepCopy(); ((ObjectNode) wrongFrame.get("snapshot")).put("snapshot_id", "public:100");
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.life(wrongFrame, read, GovernancePlanningReads.STATE));
        var wrongXp = focus.deepCopy(); ((ObjectNode) wrongXp.get("target_lifestyle_progress")).put("xp_total_raw", true);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.focus(wrongXp, read, GovernancePlanningReads.MARTIAL));
    }
}
