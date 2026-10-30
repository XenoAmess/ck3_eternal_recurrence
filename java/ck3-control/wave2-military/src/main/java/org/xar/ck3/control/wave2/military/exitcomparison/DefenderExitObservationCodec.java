package org.xar.ck3.control.wave2.military.exitcomparison;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.NativeTerminationOptions;
import org.xar.ck3.control.warpolicy.WarSide;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.AbsoluteOutcome;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.ContinuationHandoff;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.Frame;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.NativeLegality;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.NotApplicable;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.ObservationRed;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.OptionObservation;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.OptionsRequired;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.Outcome;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.RedReason;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservation.Result;

/** Declared legacy snapshot projection plus the existing complete native cache normalizer. */
public final class DefenderExitObservationCodec {
    private DefenderExitObservationCodec() { }

    /** Accepts the complete extensible SDK snapshot, not a synthetic GREEN qualification flag. */
    public static Result decodeAndObserve(byte[] raw) {
        JsonNode snapshot;
        try { snapshot = FullJsonTree.parse(raw, FullJsonTree.MAXIMUM_BYTES); }
        catch (IllegalArgumentException invalidJson) {
            throw new ContractViolationException("invalid complete defender-exit snapshot JSON", invalidJson);
        }
        if (!snapshot.isObject() || !actualTrue(snapshot.get("paused"))
                || !absentOrNull(snapshot.get("active_event"))
                || !absentOrNull(snapshot.get("pending_character_interaction"))
                || snapshot.get("active_wars") == null || !snapshot.get("active_wars").isArray()) {
            return new NotApplicable();
        }
        List<JsonNode> candidates = new ArrayList<>();
        for (JsonNode war : snapshot.get("active_wars")) {
            if (war.isObject() && textEquals(war.get("player_side"), "defender")
                    && actualTrue(war.get("player_is_primary_war_leader")) && positive(war.get("war_id"))
                    && integer(war.get("player_relative_war_score")) && war.get("player_relative_war_score").bigIntegerValue().signum() < 0) {
                candidates.add(war);
            }
        }
        if (candidates.size() != 1) { return new NotApplicable(); }
        JsonNode war = candidates.get(0);
        Frame frame;
        try { frame = frame(snapshot, war); }
        catch (ContractViolationException invalidFrame) { return new NotApplicable(); }
        List<JsonNode> matching = new ArrayList<>();
        JsonNode cache = snapshot.get("war_termination_options");
        if (cache != null && cache.isArray()) {
            for (JsonNode row : cache) {
                if (row.isObject() && integer(row.get("war_id")) && row.get("war_id").bigIntegerValue().equals(frame.warId())) {
                    matching.add(row);
                }
            }
        }
        if (matching.isEmpty()) { return new OptionsRequired(frame); }
        if (matching.size() != 1 || !sameFrame(frame, matching.get(0))) {
            return new ObservationRed(frame, RedReason.FRAME_OR_CARDINALITY_MISMATCH);
        }
        JsonNode row = matching.get(0);
        NativeTerminationOptions normalized;
        try {
            require(frame.warId().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "native WarID outside int32");
            normalized = NativeTerminationOptions.fromCache(row, frame.warId().intValueExact());
        } catch (ContractViolationException invalidOptions) {
            return new ObservationRed(frame, RedReason.SCHEMA_INVALID);
        }
        if (normalized.side() != WarSide.DEFENDER || !normalized.primary()
                || !BigInteger.valueOf(normalized.relativeScore()).equals(frame.relativeWarScore())) {
            return new ObservationRed(frame, RedReason.WAR_IDENTITY_MISMATCH);
        }
        if (normalized.activeCasusBelli() != NativeTerminationOptions.Truth.TRUE || normalized.casusBelli().isEmpty()
                || normalized.casusBelli().orElseThrow().databaseIndex() != 17
                || !normalized.casusBelli().orElseThrow().canonicalKey().equals("individual_county_de_jure_cb")) {
            return new NotApplicable();
        }
        List<OptionObservation> options = new ArrayList<>();
        for (Outcome name : Outcome.values()) {
            JsonNode option = row.get("options").get(name.wire());
            JsonNode response = option.get("recipient_response");
            boolean legal = actualTrue(option.get("context_constructed"))
                    && actualTrue(option.get("native_validator_passed")) && actualTrue(option.get("available"));
            Boolean accepted = textEquals(response.get("status"), "available")
                    ? actualTrue(response.get("would_accept_now")) : null;
            options.add(new OptionObservation(name, legal, accepted, option.get("terms_observable").booleanValue(),
                    option.get("terms").get("status").textValue(), option.get("terms").get("reason").textValue(),
                    AbsoluteOutcome.fromWire(option.get("outcome").textValue())));
        }
        Integer duration = row.get("war_duration_days").isNull() ? null : row.get("war_duration_days").intValue();
        return new NativeLegality(frame, 17, "individual_county_de_jure_cb", duration, options);
    }

    public static byte[] evaluate(byte[] raw) { return encode(decodeAndObserve(raw)); }

    public static byte[] encode(Result result) {
        require(result != null, "typed observation result required");
        if (result instanceof NotApplicable) { return StrictJson.canonical(NullNode.instance); }
        ObjectNode output = StrictJson.object();
        output.put("policy", DefenderExitObservation.POLICY);
        output.putNull("recommended_outcome");
        output.putNull("action_literal");
        if (result instanceof OptionsRequired required) {
            output.put("status", "current_native_options_required");
            output.set("frame", frameNode(required.frame()));
            output.put("required_observation_step", required.requiredObservationStep());
            output.putNull("options");
            output.putNull("material_terms");
        } else if (result instanceof ObservationRed red) {
            output.put("status", "observation_red");
            output.put("reason", red.reason().wire());
            output.set("frame", frameNode(red.frame()));
            output.putNull("options");
            output.putNull("material_terms");
        } else if (result instanceof NativeLegality observed) {
            output.put("status", "native_legality_observed_material_comparison_open");
            output.set("frame", frameNode(observed.frame()));
            ObjectNode cb = output.putObject("casus_belli");
            cb.put("database_index", observed.casusBelliIndex());
            cb.put("canonical_key", observed.casusBelliKey());
            if (observed.warDurationDays() == null) { output.putNull("war_duration_days"); }
            else { output.put("war_duration_days", observed.warDurationDays()); }
            ObjectNode options = output.putObject("options");
            for (OptionObservation option : observed.options()) {
                ObjectNode projection = options.putObject(option.outcome().wire());
                projection.put("native_legal_now", option.nativeLegalNow());
                if (option.recipientAcceptsNow() == null) { projection.putNull("recipient_accepts_now"); }
                else { projection.put("recipient_accepts_now", option.recipientAcceptsNow()); }
                projection.put("material_terms_observable", option.materialTermsObservable());
                projection.put("material_terms_status", option.materialTermsStatus());
                projection.put("material_terms_reason", option.materialTermsReason());
                projection.put("outcome", option.absoluteOutcome().wire());
            }
            ObjectNode material = output.putObject("material_terms");
            material.putNull("title_holder_and_vassal_effects");
            material.putNull("signed_actor_and_opponent_resources");
            material.putNull("directed_truce");
            material.putNull("continue_war_risk");
            ObjectNode readiness = output.putObject("decision_readiness");
            readiness.put("status", "exit_selection_blocked");
            ArrayNode legal = readiness.putArray("legal_outcomes_now");
            observed.legalAcceptedOutcomes().forEach(outcome -> legal.add(outcome.wire()));
            ArrayNode blockers = readiness.putArray("blocking_observations");
            blockers.add("de_jure_cb_current_title_and_vassal_effects");
            blockers.add("same_frame_signed_actor_and_opponent_resource_deltas");
            blockers.add("same_frame_directed_truce");
            blockers.add("bounded_continue_war_loss_and_contact_risk");
            readiness.put("generic_claim_cb_terms_query_applicable", false);
            readiness.put("historical_surrender_result_reusable_as_current_terms", false);
        }
        return StrictJson.canonical(output);
    }

    /** Consumer projection only; terminal candidates never gain authority through read-only metadata. */
    public static byte[] encodeWithContinuationHandoff(Result result, String selectedStep) {
        JsonNode encoded = StrictJson.parse(encode(result));
        if (result instanceof NativeLegality) {
            ObjectNode output = (ObjectNode) encoded;
            ContinuationHandoff handoff = DefenderExitObservation.continuationHandoff(selectedStep);
            ObjectNode row = output.putObject("continuation_handoff");
            row.put("status", handoff.status().wire());
            if (handoff.candidateSelectedStep() == null) { row.putNull("candidate_selected_step"); }
            else { row.put("candidate_selected_step", handoff.candidateSelectedStep()); }
            row.put("current_frame_revalidation_required", true);
            row.put("exit_action_authorized", false);
        }
        return StrictJson.canonical(encoded);
    }

    private static Frame frame(JsonNode snapshot, JsonNode war) {
        JsonNode played = snapshot.get("played_character");
        JsonNode diagnostics = snapshot.get("diagnostics");
        require(played != null && played.isObject() && diagnostics != null && diagnostics.isObject(),
                "player and diagnostics projections required");
        return new Frame(string(snapshot.get("snapshot_id")), exactInteger(snapshot.get("revision")),
                exactInteger(snapshot.get("native_revision")), exactInteger(snapshot.get("date_raw")),
                string(snapshot.get("episode_run_id")), exactInteger(diagnostics.get("connection_generation")),
                exactInteger(played.get("character_id")), exactInteger(war.get("war_id")),
                exactInteger(war.get("player_relative_war_score")));
    }
    private static boolean sameFrame(Frame frame, JsonNode row) {
        return textEquals(row.get("queried_snapshot_id"), frame.snapshotId())
                && integerEquals(row.get("queried_revision"), frame.revision())
                && integerEquals(row.get("queried_native_revision"), frame.nativeRevision())
                && integerEquals(row.get("queried_connection_generation"), frame.connectionGeneration())
                && textEquals(row.get("episode_run_id"), frame.episodeRunId());
    }
    private static ObjectNode frameNode(Frame frame) {
        ObjectNode row = StrictJson.object();
        row.put("snapshot_id", frame.snapshotId());
        row.put("revision", frame.revision());
        row.put("native_revision", frame.nativeRevision());
        row.put("date_raw", frame.dateRaw());
        row.put("episode_run_id", frame.episodeRunId());
        row.put("connection_generation", frame.connectionGeneration());
        row.put("played_character_id", frame.playedCharacterId());
        row.put("war_id", frame.warId());
        row.put("player_relative_war_score", frame.relativeWarScore());
        return row;
    }
    private static boolean actualTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean absentOrNull(JsonNode value) { return value == null || value.isNull(); }
    private static boolean integer(JsonNode value) { return value != null && value.isIntegralNumber(); }
    private static boolean positive(JsonNode value) { return integer(value) && value.bigIntegerValue().signum() > 0; }
    private static boolean integerEquals(JsonNode value, BigInteger expected) {
        return integer(value) && value.bigIntegerValue().equals(expected);
    }
    private static boolean textEquals(JsonNode value, String expected) {
        return value != null && value.isTextual() && value.textValue().equals(expected);
    }
    private static BigInteger exactInteger(JsonNode value) {
        require(integer(value), "exact JSON integer required; no bool, float or string");
        return value.bigIntegerValue();
    }
    private static String string(JsonNode value) {
        require(value != null && value.isTextual(), "JSON string required");
        DefenderExitObservation.textAllowEmpty(value.textValue());
        return value.textValue();
    }
}
