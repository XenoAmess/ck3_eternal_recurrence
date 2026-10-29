package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual typed planner result -> original public PLAN -> real PublicBindings -> cold DATA decoder. */
final class RootPublicPlanPresentationTest {
    private static final org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags FLAGS =
            new org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags(false,false,false,false,false,false,false);
    private static Obj data(String json) { return DriverJson.object(json.getBytes(StandardCharsets.UTF_8), RawJson.MAXIMUM_BYTES); }
    private static PlanningResult waiting(PlanningRequest request, Obj original) {
        var draft = new OrdinaryPolicy.Draft("one-life-turn-v1", "current_life_domain", "retain actual complete domain result",
                OrdinaryPolicy.Kind.ORDINARY, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), original);
        var trace = new PlanTrace(request.before(), java.util.Arrays.stream(PlanningStage.values()).map(stage ->
                new PlanTrace.StageVisit(stage, PlanTrace.Outcome.KEPT, "software source envelope projection",
                        Optional.of(new ExactRef("software-stage-source",1,"b".repeat(64))), Optional.<Obj>empty())).toList(), Optional.of(draft));
        return new PlanningResult.ReadOnlyWait(request.before(), draft.reason(), trace);
    }
    private static Obj plan() {
        return data("{\"policy\":\"one-life-turn-v1\",\"phase\":\"current_life_domain\","
                + "\"reason\":\"retain actual complete domain result\",\"selected_step\":null,"
                + "\"event_decision\":{\"definition\":\"rite_growth.0010\",\"options\":[0,1],\"material\":null},"
                + "\"campaign_goal_plan_used\":{\"focus\":\"succession\",\"rows\":[]},"
                + "\"player_risk_context\":{\"war\":true,\"cash\":-0.0},"
                + "\"construction_pending_action\":null,\"council\":{\"available\":false},"
                + "\"realm_membership_feedback_v1\":{\"declined\":0},"
                + "\"source_owned_extension\":{\"cash\":-0.0,\"cost\":1.2500e-7,\"empty\":{},\"optional\":null}}");
    }
    @Test void allRetainedDomainFieldsAndOriginalDecimalTokensSurviveTheActualPublicConsumerAndColdSerde() throws Exception {
        PlanningRequest request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"), BigInteger.ONE);
        PlanningResult actual = waiting(request, plan());
        RawJson expected = RootPublicPlanPresentation.produce(request, actual, FLAGS).bytes();
        var registry = new PublicBindings();
        new RootMcpPlanning(new RootMcpPlanning.Backend() {
            public RootMcpPlanning.Admission admission() { return new RootMcpPlanning.Admission(true, false, List.of()); }
            public RawJson plan(PublicPlanningCodec.PlanRequest caller) throws java.io.IOException {
                return new RootPublicPlanPresentation().encode(request, actual, FLAGS);
            }
            public RawJson execute(PublicPlanningCodec.ExecuteRequest caller) { throw new AssertionError(); }
        }).register(registry, new ExactRef("software-plan-projection-only", 1, "a".repeat(64)));
        registry.freeze(Set.of(PublicMethod.PLAN_TURN));
        RawJson actualPublic = registry.lookup(PublicMethod.PLAN_TURN).orElseThrow().invoke(new PublicBindings.Missing());
        assertEquals(expected, actualPublic);
        var cold = RootPublicPlanPresentation.decode(actualPublic);
        for (var field : plan().members().entrySet())
            if (!field.getKey().equals("player_risk_context")) assertEquals(field.getValue(), cold.plan().get(field.getKey()));
        assertEquals(new OpportunityJson.Text("unavailable"), ((Obj)cold.plan().get("player_risk_context")).get("status"));
        assertEquals(cold.original(), RootPublicPlanPresentation.decode(cold.bytes()).original());
        String encoded = new String(actualPublic.bytes(), StandardCharsets.UTF_8);
        assertTrue(encoded.contains("-0.0")); assertTrue(encoded.contains("1.2500e-7"));
        assertTrue(cold.original().members().containsKey("_auto_camera_hotspot_input"));
        assertEquals(OpportunityJson.Nil.INSTANCE, cold.original().get("_declaration_opportunity_cooldown_v1"));
        assertFalse(cold.original().members().containsKey("status"), "PLAN is the original plan envelope, not an AUTO status/receipt");
        assertFalse(cold.original().members().containsKey("receipt"));
    }
    @Test void fullWidthActualPlanningIdentitiesUseCanonicalStringsWithoutChangingOrdinaryPlanNumbers() throws Exception {
        BigInteger maximum = new BigInteger("18446744073709551615");
        var request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot(maximum.toString()), maximum);
        var result = RootPublicPlanPresentation.produce(request, waiting(request, plan()), FLAGS);
        assertEquals(new OpportunityJson.Text(maximum.toString()), result.original().get("revision"));
        assertEquals(new OpportunityJson.Text(maximum.toString()), result.sourceFrame().get("native_revision"));
        assertEquals(result.original(), RootPublicPlanPresentation.decode(result.bytes()).original());
        assertEquals(data("{\"declined\":0}"), result.plan().get("realm_membership_feedback_v1"));
    }
    @Test void missingProducerOrForeignTraceCannotBecomeACompletePublicPlan() {
        var first = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"), BigInteger.ONE);
        var second = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("2"), BigInteger.TWO);
        assertThrows(java.io.IOException.class, () -> RootPublicPlanPresentation.produce(first, waiting(second, plan()), FLAGS));
        var trace = new PlanTrace(first.before(), List.of(), Optional.empty());
        var incomplete = new PlanningResult.IncompleteMigration(first.before(), List.of(PlanningStage.ORDINARY_CORE), trace);
        assertThrows(java.io.IOException.class, () -> RootPublicPlanPresentation.produce(first, incomplete, FLAGS));
        assertThrows(java.io.IOException.class, () -> RootPublicPlanPresentation.produce(first,
                new PlanningResult.ReadOnlyWait(first.before(), "actual producer absent", trace), FLAGS));
    }
    @Test void coldDecoderRejectsWrongPresenceTypesSourceIdentityAndDuplicateFields() throws Exception {
        var request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"), BigInteger.ONE);
        String original = new String(RootPublicPlanPresentation.produce(request, waiting(request, plan()), FLAGS).bytes().bytes(), StandardCharsets.UTF_8);
        for (String changed : List.of(
                original.replace("\"revision\":\"1\"", "\"revision\":true"),
                original.replace("\"revision\":\"1\"", "\"revision\":1.0"),
                original.replace("\"actor_character_id\":29829", "\"actor_character_id\":-1"),
                original.replace("\"actor_character_id\":29829", "\"actor_character_id\":29829.0"),
                original.replace("\"selected_step\":null", "\"selected_step\":false"),
                original.replace("\"planning_source_frame\":", "\"wrong_source_frame\":"),
                original.replaceFirst("\\{", "{\"revision\":\"999\","))) {
            assertNotEquals(original, changed);
            assertThrows(IllegalArgumentException.class, () -> RootPublicPlanPresentation.decode(
                    new RawJson(changed.getBytes(StandardCharsets.UTF_8))));
        }
    }
    @Test void riskPublicRolesUseTheSameTypedProducerWhileItsInternalNumericContractRemainsUnchanged() {
        var maximum = new BigInteger("18446744073709551615");
        var risk = new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Context(
                org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Status.PARTIAL,
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Binding("native:1",maximum,maximum,53217264,29829),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Source(maximum,"software-risk-data"),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.CurrentScope(maximum,false),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Known<>(
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Health(300000,
                                org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Band.FINE_OR_BETTER,false,false)),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("stress unavailable"),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Alerts(
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Known<>(false),
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("stress unavailable"),
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("heir unavailable"),
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("partition unavailable")),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Signals(
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("succession unavailable"),
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("stress unavailable"),
                        new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Unknown<>("legitimacy unavailable")),
                new org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.Readiness(true,false,false,false),null);
        var internal = org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec.encode(risk);
        var external = org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec.encodePublic(risk);
        assertTrue(internal.path("binding").path("revision").isIntegralNumber());
        for (var role : List.of(List.of("binding","revision"),List.of("binding","native_revision"),
                List.of("source","query_sequence"),List.of("current_scope","connection_generation")))
            assertEquals(maximum.toString(), external.path(role.get(0)).path(role.get(1)).textValue());
        assertEquals(internal.path("health"), external.path("health"));
        assertEquals(internal.path("alerts"), external.path("alerts"));
        var missing = org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskContext.unavailable("actual same-frame root absent");
        assertEquals(org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec.encode(missing),
                org.xar.ck3.control.wave2.planning.playerrisk.PlayerRiskCodec.encodePublic(missing));
    }

    @Test void retainedOriginalSnapshotsAndRecorderArraysUseTheOwningPublicCodecAtTheRealEnvelopeBoundary() throws Exception {
        var maximum = org.xar.ck3.control.contracts.StrictJson.UINT64_MAX;
        Obj originalSnapshot = data(PublicPlanningCodecTest.snapshot(maximum.toString()))
                .with("format_version",new OpportunityJson.IntegerValue(BigInteger.ONE))
                .with("speed",new OpportunityJson.IntegerValue(BigInteger.ONE))
                .with("episode_character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(29829)))
                .with("player_armies",new OpportunityJson.Arr(List.of()))
                .with("active_event",OpportunityJson.Nil.INSTANCE)
                .with("pending_character_interaction",OpportunityJson.Nil.INSTANCE)
                .with("one_life_terminal_reason",OpportunityJson.Nil.INSTANCE);
        var request = PublicPlanningCodecTest.original(new String(DriverJson.encode(originalSnapshot),StandardCharsets.UTF_8),maximum);
        var complete = waiting(request,plan());
        var trace = new PlanTrace(request.before(),List.of(new PlanTrace.StageVisit(
                PlanningStage.ORDINARY_CORE,PlanTrace.Outcome.KEPT,"actual envelope before domain consumers",
                Optional.of(new ExactRef("software-core-stage",1,"c".repeat(64))),Optional.<Obj>empty())),
                complete.trace().finalPlan());
        var early = new PlanningResult.ReadOnlyWait(request.before(),"domain consumers not yet visited",trace);
        var enabled = new org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags(
                false,true,true,true,true,true,false);
        var produced = RootPublicPlanPresentation.produce(request,early,enabled);
        Obj detached = produced.original();
        for(String field:List.of("_private_faction_snapshot_v1","_private_construction_snapshot_v1",
                "_private_family_marriage_snapshot_v1","_private_council_snapshot_v1","_private_m5_snapshot_v1")) {
            Obj snapshot = (Obj)detached.get(field);
            assertEquals(new OpportunityJson.Text(maximum.toString()),snapshot.get("native_revision"));
            assertEquals(originalSnapshot,DriverJson.object(
                    org.xar.ck3.control.application.driver.PublicSnapshotCodec.decodePlanningSnapshotData(
                            new RawJson(DriverJson.encode(snapshot))).bytes(),RawJson.MAXIMUM_BYTES));
        }
        for(String field:List.of("_private_faction_history_v1","_private_construction_history_v1",
                "_private_council_history_v1","_private_m5_history_v1"))
            assertEquals(new OpportunityJson.Arr(List.of()),detached.get(field));
        Obj sway = (Obj)detached.get("_ordinary_sway_input_v1");
        assertEquals(new OpportunityJson.Text(maximum.toString()),((Obj)sway.get("snapshot")).get("revision"));
        assertEquals(detached,RootPublicPlanPresentation.decode(produced.bytes()).original());
        Obj invalid = detached.with("_private_faction_snapshot_v1",
                ((Obj)detached.get("_private_faction_snapshot_v1")).with("revision",new OpportunityJson.Bool(true)));
        assertThrows(IllegalArgumentException.class,()->RootPublicPlanPresentation.decode(
                new RawJson(DriverJson.encode(invalid))));
        assertEquals(OpportunityJson.Nil.INSTANCE,detached.get("_private_lifestyle_scope_v1"));
    }


    @Test void unresolvedLifestyleIntentAndItsSeparateOriginalAckKeepTheirOwnScopedWideRoles() throws Exception {
        var maximum = org.xar.ck3.control.contracts.StrictJson.UINT64_MAX;
        Obj pending = data("{\"status\":\"action_state_unknown\",\"action_request_id\":\"life-perk-data\","
                + "\"target_key\":\"diplomacy_thoughtful\",\"kind\":\"perk\",\"pre_public_revision\":"+maximum+","
                + "\"episode_run_id\":\"native-29829-2bc2d599f7f9\",\"native_command_submitted\":null,"
                + "\"source_frame\":{\"snapshot_id\":\"native:"+maximum+"\",\"revision\":"+maximum+","
                + "\"native_revision\":"+maximum+",\"date_raw\":53217264,\"player_character_id\":29829},"
                + "\"native_ack\":{\"status\":\"submitted_verification_pending\",\"pre_public_revision\":"+maximum+"},"
                + "\"native_frame\":{\"type\":\"command_result\",\"ok\":true,\"result\":{\"pre_public_revision\":"+maximum+"}}}");
        Obj row = data("{\"command\":\"private-select-player-lifestyle-perk-v1\",\"ok\":true}").with("result",pending);
        var request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot(maximum.toString()),maximum)
                .withHistory(List.of(row));
        var complete = waiting(request,plan());
        var trace = new PlanTrace(request.before(),List.of(new PlanTrace.StageVisit(
                PlanningStage.ORDINARY_CORE,PlanTrace.Outcome.KEPT,"before the original LIFE consumer",
                Optional.of(new ExactRef("software-core-stage",1,"c".repeat(64))),Optional.<Obj>empty())),
                complete.trace().finalPlan());
        var early = new PlanningResult.ReadOnlyWait(request.before(),"LIFE has not consumed this intent",trace);
        var enabled = new org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags(
                true,false,false,false,false,false,false);
        var produced = RootPublicPlanPresentation.produce(request,early,enabled);
        Obj exposed = (Obj)produced.original().get("_private_lifestyle_pending_v1");
        var expected = new OpportunityJson.Text(maximum.toString());
        assertEquals(expected,exposed.get("pre_public_revision"));
        assertEquals(expected,((Obj)exposed.get("source_frame")).get("revision"));
        assertEquals(expected,((Obj)exposed.get("source_frame")).get("native_revision"));
        assertEquals(expected,((Obj)exposed.get("native_ack")).get("pre_public_revision"));
        assertEquals(expected,((Obj)((Obj)exposed.get("native_frame")).get("result")).get("pre_public_revision"));
        assertEquals(OpportunityJson.Nil.INSTANCE,exposed.get("native_command_submitted"));
        assertEquals(produced.original(),RootPublicPlanPresentation.decode(produced.bytes()).original());
        Obj invalid = produced.original().with("_private_lifestyle_pending_v1",
                exposed.with("pre_public_revision",new OpportunityJson.Bool(true)));
        assertThrows(IllegalArgumentException.class,()->RootPublicPlanPresentation.decode(new RawJson(DriverJson.encode(invalid))));
    }


    @Test void completePlanMaterialKeepsLegitimateLongFiniteDecimalTokensWithoutWideningTheCallerProtocol() throws Exception {
        String token = "7".repeat(5000)+".0";
        Obj detail = plan().with("source_owned_extension",new Obj(java.util.Map.of(
                "exact_finite_decimal",new OpportunityJson.DecimalValue(token))));
        var request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"),BigInteger.ONE);
        var produced = RootPublicPlanPresentation.produce(request,waiting(request,detail),FLAGS);
        assertEquals(detail.get("source_owned_extension"),produced.plan().get("source_owned_extension"));
        assertEquals(produced.original(),RootPublicPlanPresentation.decode(produced.bytes()).original());
        assertTrue(new String(produced.bytes().bytes(),StandardCharsets.UTF_8).contains(token));
        assertThrows(IllegalArgumentException.class,()->new RawJson(produced.bytes().bytes()));
    }

    @Test void oldSafeIntegerPlanningDataRemainsReadableWithoutConvertingUnknownStringsToIdentities() throws Exception {
        var request = PublicPlanningCodecTest.original(PublicPlanningCodecTest.snapshot("1"), BigInteger.ONE);
        String original = new String(RootPublicPlanPresentation.produce(request, waiting(request,plan()), FLAGS).bytes().bytes(),
                StandardCharsets.UTF_8);
        String oldSafe = original.replace("\"revision\":\"1\"", "\"revision\":1")
                .replace("\"native_revision\":\"1\"", "\"native_revision\":1")
                .replace("\"connection_generation\":\"1\"", "\"connection_generation\":1");
        var decoded = RootPublicPlanPresentation.decode(new RawJson(oldSafe.getBytes(StandardCharsets.UTF_8)));
        assertEquals(new OpportunityJson.IntegerValue(BigInteger.ONE), decoded.original().get("revision"));
        assertEquals(decoded.original(),RootPublicPlanPresentation.decode(decoded.bytes()).original());
    }

}

