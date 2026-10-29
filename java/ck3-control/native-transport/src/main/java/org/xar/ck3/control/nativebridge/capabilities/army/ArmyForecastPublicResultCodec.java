package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.planning.military.NativeMilitaryInputView;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.forecast.CombatNativeEnvelope;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Pure method-specific public projection. Native readers/cache/publishers and their authority stay unchanged. */
public final class ArmyForecastPublicResultCodec {
    public enum Profile { ORIGINAL_PUBLIC_RESULT, NATIVE_CANDIDATE_PENDING_SERVICE_DERIVATIONS }
    private ArmyForecastPublicResultCodec() { }

    public static Profile profile(PublicMethod method) {
        return switch (method) {
            case QUERY_WAR_ENTRY_ASSESSMENTS, QUERY_CURRENT_BATTLE_KNIGHT_V1, QUERY_COMBAT_PHASE_EVENT_TRACE_V1,
                    QUERY_COMBAT_SIMULATION_INPUTS, QUERY_COMBAT_SIMULATION_INPUTS_V3 -> Profile.ORIGINAL_PUBLIC_RESULT;
            default -> throw new IllegalArgumentException("not a forecast public method");
        };
    }

    public static RawJson encode(PublicMethod actualMethod, ArmyForecastService.Reply reply) {
        // Explicit historical candidate entry point. Current Service10 always calls the three-argument API.
        return project(actualMethod, reply, Optional.empty(), false);
    }

    public static RawJson encode(PublicMethod actualMethod, ArmyForecastService.Reply reply,
            Optional<CombatLoadedPlaysetProof.Evidence> actualAlreadyCollected) {
        Objects.requireNonNull(actualAlreadyCollected);
        require(actualAlreadyCollected.equals(reply.loadedPlaysetEvidence()), "serialization evidence differs from the actual Service reply custody");
        return project(actualMethod, reply, actualAlreadyCollected, true);
    }

    private static RawJson project(PublicMethod actualMethod, ArmyForecastService.Reply reply,
            Optional<CombatLoadedPlaysetProof.Evidence> actualAlreadyCollected, boolean originalPublic) {
        Objects.requireNonNull(reply); profile(actualMethod);
        var actual = reply.actual().value(); PlanningReadReceipt receipt = reply.actual().receipt();
        require(method(actual.kind()) == actualMethod, "public forecast method differs from actual typed original");
        Context context = ArmyNativeReadEvidence.contextForRequest(reply.before().context(), receipt.request());
        require(reply.before().actual().identity().equals(reply.after().actual().identity())
                && NativeMilitaryInputView.sameNativeOperands(reply.before().actual().semantic(), reply.after().actual().semantic())
                && reply.before().source().equals(reply.after().source()), "forecast public projection crossed its original complete source");
        var call = ArmyCallCodec.decode(actualMethod, new RawJson(OpportunityJson.encode(receipt.request().arguments())));
        var recipe = ArmyNativeRecipes.prepare(call, context, new ArmyNativeRecipes.NoFacts(), false);
        require(recipe instanceof ArmyNativeRecipes.Primitive, "forecast original request is not primitive");
        var primitive = (ArmyNativeRecipes.Primitive) recipe;
        require(primitive.effect() == ArmyNativeRecipes.Effect.READ_ONLY
                && primitive.request().step().equals(receipt.request().operation().value()), "forecast original operation changed");
        ObjectNode raw = ArmyNativeReadEvidence.result(context, receipt).deepCopy();
        if (actual instanceof ForecastReadObservation.WarEntry) {
            require(names(raw).equals(Set.of("step", "accepted", "status", "query_sequence", "war_entry_assessments")), "forecast original native outer fields changed");
        } else if (actual instanceof ForecastReadObservation.CurrentKnight) {
            require(names(raw).equals(Set.of("step", "accepted", "status", "query_sequence", "snapshot_revision", "current_battle_knight")), "forecast original native outer fields changed");
        } else {
            CombatNativeEnvelope.validate(raw, actual instanceof ForecastReadObservation.PhaseTrace
                    ? CombatNativeEnvelope.Payload.PHASE_TRACE : CombatNativeEnvelope.Payload.COMBAT_INPUTS);
        }
        yes(get(raw, "accepted")); positive(get(raw, "query_sequence")); equal(get(raw, "step"), primitive.request().step());
        ObjectNode expected = raw.deepCopy();
        ObjectNode before = object(OpportunityJson.toNode(reply.before().actual().semantic()));
        ObjectNode after = object(OpportunityJson.toNode(reply.after().actual().semantic()));

        if (actual instanceof ForecastReadObservation.WarEntry war) {
            var input = (ArmyCalls.WarEntry) call;
            var targets = input.targets().stream().map(PositiveId::value).toList();
            var value = WarEntryAssessmentCodec.normalize(get(raw, "war_entry_assessments"),
                    new WarEntryAssessmentCodec.Expected(targets, context.playerId(), context.nativeRevision(), context.dateRaw()));
            var scopes = WarEntryAssessmentCodec.targetScopes(before, targets);
            require(scopes.equals(WarEntryAssessmentCodec.targetScopes(after, targets)), "war-entry public target scope changed");
            require(immutable(value.toNativeJson()).equals(war.assessments())
                    && war.targetScopes().equals(OpportunityJson.parse(bytes(scopes.toNativeJson()))), "war-entry typed observation differs from actual native domain/scope");
            expected.set("war_entry_assessments", value.toNativeJson()); expected.set("target_scopes", scopes.toNativeJson());
        } else if (actual instanceof ForecastReadObservation.CurrentKnight knight) {
            BattleResponseCodec.knight(bytes(raw), context, ((ArmyCalls.Knight) call).selection());
            require(immutable(object(get(raw, "current_battle_knight"))).equals(knight.knight()), "typed current knight differs from original native packet");
        } else if (actual instanceof ForecastReadObservation.PhaseTrace trace) {
            var value = CombatPhaseEventTraceCodec.normalize(get(raw, "combat_phase_event_trace"), ((ArmyCalls.CombatId) call).combat().value());
            require(immutable(value.toNativeJson()).equals(trace.trace()), "typed phase trace differs from original native packet");
            expected.set("combat_phase_event_trace", value.toNativeJson());
        } else {
            var combat = (ForecastReadObservation.CombatInputs) actual;
            var value = combat.observation();
            require(value.request().equals(((ArmyCalls.Combat) call).selection())
                    && value.frame().snapshotId().equals(context.before().frame().snapshotId())
                    && value.frame().revision().equals(context.before().frame().revision())
                    && value.frame().nativeRevision().equals(context.nativeRevision())
                    && value.frame().dateRaw().equals(context.dateRaw())
                    && value.querySequence().equals(positive(get(raw, "query_sequence")).value()), "typed combat candidate source differs from actual original request");
            // This is the existing sole typed native-input observation, not the unported Service
            // knight-consumption/playset/physical-association derived public product.
            expected.set("combat_simulation_inputs", value.normalizedJson());
        }
        enrich(expected, context, receipt);
        require(immutable(expected).equals(actual.normalizedResult()), "forecast normalized outer fields differ from original packet and actual source");

        ObjectNode result = expected.deepCopy();
        boolean combatMethod = actual instanceof ForecastReadObservation.CombatInputs;
        if (!combatMethod || originalPublic) {
            // These two enrich-only fields are absent from the original three public methods.
            // They have just been checked against the actual packet/source; no arbitrary fields are dropped.
            result.remove(List.of("queried_episode_run_id", "queried_connection_generation"));
            if (result.has("backend_id")) equal(get(result, "backend_id"), "native-headless");
            else result.put("backend_id", "native-headless");
            if (actual instanceof ForecastReadObservation.WarEntry) {
                result.put("schema_version", 1); result.put("status", "available");
                result.set("target_character_ids", ((ObjectNode) OpportunityJson.toNode(((ForecastReadObservation.WarEntry) actual).assessments())).get("requested_target_character_ids").deepCopy());
            } else if (actual instanceof ForecastReadObservation.PhaseTrace) {
                result.put("production_trace_ready", false); result.put("qualified_win_probability_available", false);
            } else if (actual instanceof ForecastReadObservation.CombatInputs combat) {
                var observed = combat.observation(); var request = observed.request(); var scope = observed.scope();
                ObjectNode normalized = observed.normalizedJson(); ObjectNode completeness = object(get(normalized, "completeness"));
                result.put("schema_version", actualMethod == PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS ? 2 : 3)
                        .put("status", observed.status().wire()).put("scope", "explicit-hypothetical-active-war-contact");
                ObjectNode source = result.putObject("source");
                var hello = before.path("diagnostics").path("hello");
                for (String field : List.of("game_version", "executable_sha256"))
                    source.set(field, hello.isObject() && hello.has(field) ? hello.get(field).deepCopy() : empty().nullNode());
                for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw", "paused", "backend_id"))
                    source.set(field, get(before, field).deepCopy());
                result.put("target_province_id", request.targetProvinceId());
                if (request.attackerEntryProvinceId() == null) result.putNull("attacker_entry_province_id");
                else result.put("attacker_entry_province_id", request.attackerEntryProvinceId());
                var attackers = result.putArray("attacker_army_ids"); request.attackerArmyIds().forEach(attackers::add);
                var defenders = result.putArray("defender_army_ids"); request.defenderArmyIds().forEach(defenders::add);
                ObjectNode actualScope = scope.toJson(request);
                for (String field : List.of("attacker_side", "defender_side", "common_war_ids")) result.set(field, get(actualScope, field).deepCopy());
                for (String field : List.of("input_observation_ready", "monte_carlo_ready", "missing_required_domains"))
                    result.set(field, get(completeness, field).deepCopy());
                var input = new CombatPublicProjection.Input(reply.before().actual(), reply.after().actual(), reply.actual());
                if (actualMethod == PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS) {
                    require(actualAlreadyCollected.isEmpty(), "V2 cannot consume V3 loaded-playset evidence");
                    var derived = CombatPublicProjection.v2(input);
                    result.set("knight_stat_consumption_projection_v1", derived.knightConsumption().isPresent()
                            ? OpportunityJson.toNode(derived.knightConsumption().orElseThrow()) : empty().nullNode());
                    result.set("current_physical_entry_writeback_association_v1", derived.physicalAssociation().isPresent()
                            ? OpportunityJson.toNode(derived.physicalAssociation().orElseThrow()) : empty().nullNode());
                } else {
                    require(actualAlreadyCollected.isPresent(), "original CombatV3 requires already-collected actual loaded-playset evidence");
                    var derived = CombatPublicProjection.v3(input, actualAlreadyCollected.orElseThrow());
                    for (String field : List.of("base_input_observation_ready", "phase_raw_observation_ready", "offline_exact_state_refs_ready",
                            "phase_event_inputs_ready", "transition_fidelity_gate", "planner_usable", "active_attack_allowed", "missing_observation_domains"))
                        result.set(field, get(completeness, field).deepCopy());
                    result.set("phase_event_manifest_fidelity", OpportunityJson.toNode(derived.phaseEventManifestFidelity()));
                    result.set("loaded_playset_proof", OpportunityJson.toNode(derived.loadedPlaysetProof()));
                    var missing = result.putArray("missing_fidelity_gates"); derived.missingFidelityGates().forEach(missing::add);
                    result.set("current_special_knight_initial_value", OpportunityJson.toNode(derived.specialKnightInitialValue()));
                }
            }
        }
        return ArmyPublicWire.encodeExactSourceBound(immutable(result), context);
    }
    private static void enrich(ObjectNode result, Context context, PlanningReadReceipt receipt) {
        result.put("queried_snapshot_id", context.before().frame().snapshotId()).put("queried_revision", context.before().frame().revision())
                .put("queried_native_revision", context.nativeRevision()).put("queried_episode_run_id", context.before().frame().episodeRunId())
                .put("queried_connection_generation", receipt.before().binding().connectionGeneration());
    }
    private static Obj immutable(ObjectNode result) { return DriverJson.object(bytes(result), DriverJson.MAX_NATIVE_BYTES); }
    private static PublicMethod method(ForecastReadObservation.Kind kind) {
        return switch (kind) {
            case COMBAT_V2 -> PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS;
            case COMBAT_V3 -> PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3;
            case WAR_ENTRY -> PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS;
            case CURRENT_KNIGHT -> PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1;
            case PHASE_TRACE -> PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1;
        };
    }
}

