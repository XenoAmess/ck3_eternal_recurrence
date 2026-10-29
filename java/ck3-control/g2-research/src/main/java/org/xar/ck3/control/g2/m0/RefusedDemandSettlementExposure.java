package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.warpolicy.ObservationContext;
import org.xar.ck3.control.warpolicy.ReviewedSourceRegistry;
import org.xar.ck3.control.warpolicy.WarOutcomeStakesProjector;
import org.xar.ck3.control.warpolicy.WarOutcomeStakesResult;
import org.xar.ck3.control.warpolicy.WarSide;

/** Source-reviewed white-peace and defeat branches, attached to the existing exact native-CB projector. */
public final class RefusedDemandSettlementExposure {
    public static final String OPERATION = "refused-demand-settlement-exposure";
    public static final String RESEARCH_SHA256 = "1c6bf0524a0c3e845215a124ce77f1f6ae10add24b6f582fa5af6518e1738a96";
    private static final Map<String, String> SOURCE_SHA256 = Map.of(
            "common/casus_belli_types/00_civil_war.txt", "a9f5d844413bd7acfd4d4b1611877ac34e78eb293f309c0e7a41f27aca3a0047",
            "common/scripted_effects/00_war_effects.txt", "f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b",
            "common/opinion_modifiers/00_war_opinions.txt", "750864482d2d6c5d268424a1e03cba24301dedf853722d7fc12cb6f9fbcc68dc");
    private RefusedDemandSettlementExposure() { }

    public enum Settlement {
        WHITE_PEACE, PLAYER_DEFEAT;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
        static Settlement decode(JsonNode value) {
            String text = StrictJson.text(value);
            for (Settlement candidate : values()) { if (candidate.wire().equals(text)) { return candidate; } }
            throw new IllegalArgumentException("unsupported refused-demand settlement");
        }
    }
    public enum Status { UNKNOWN, SOURCE_REVIEWED_CONDITIONAL }
    public enum PoliticalReason { REVOKE_TITLE_REASON, IMPRISONMENT_REASON, BANISH_REASON, EXECUTE_REASON }
    public record Assessment(Status status, Settlement settlement, List<PoliticalReason> conditionalReasons,
            boolean conditionalHardImprisonmentIfNotImprisoned, boolean conditionalDirectVassalCooldown,
            WarOutcomeStakesResult sourceObservation) {
        public Assessment {
            Objects.requireNonNull(status); Objects.requireNonNull(settlement); Objects.requireNonNull(sourceObservation);
            conditionalReasons = List.copyOf(conditionalReasons);
            if (status == Status.UNKNOWN && (!conditionalReasons.isEmpty()
                    || conditionalHardImprisonmentIfNotImprisoned || conditionalDirectVassalCooldown)) {
                throw new IllegalArgumentException("unknown source cannot grant political-effect knowledge");
            }
            if (status == Status.SOURCE_REVIEWED_CONDITIONAL && (!sourceBound(sourceObservation)
                    || conditionalReasons.isEmpty() || conditionalHardImprisonmentIfNotImprisoned != (settlement == Settlement.PLAYER_DEFEAT))) {
                throw new IllegalArgumentException("conditional political result lacks its exact source branch");
            }
        }
    }

    public static Assessment assess(WarOutcomeStakesResult observed, Settlement settlement) {
        Objects.requireNonNull(observed); Objects.requireNonNull(settlement);
        if (!sourceBound(observed)) { return new Assessment(Status.UNKNOWN, settlement, List.of(), false, false, observed); }
        List<PoliticalReason> reasons = settlement == Settlement.WHITE_PEACE
                ? List.of(PoliticalReason.REVOKE_TITLE_REASON, PoliticalReason.IMPRISONMENT_REASON)
                : List.of(PoliticalReason.REVOKE_TITLE_REASON, PoliticalReason.IMPRISONMENT_REASON,
                        PoliticalReason.BANISH_REASON, PoliticalReason.EXECUTE_REASON);
        boolean immediate = observed.liegeRelation().orElseThrow()
                == WarOutcomeStakesResult.LiegeRelation.IMMEDIATE_LIEGE_CHARACTER_ID;
        return new Assessment(Status.SOURCE_REVIEWED_CONDITIONAL, settlement, reasons,
                settlement == Settlement.PLAYER_DEFEAT, immediate, observed);
    }

    private static boolean sourceBound(WarOutcomeStakesResult observed) {
        return observed.status() == WarOutcomeStakesResult.Status.SOURCE_REVIEWED_CONDITIONAL
                && observed.side().orElse(null) == WarSide.ATTACKER
                && observed.casusBelli().map(cb -> cb.canonicalKey().equals("refused_liege_demand_war")).orElse(false)
                && observed.profileId().orElse("").equals("refused-liege-demand-primary-rebel-political-exposure-v1")
                && observed.liegeRelation().isPresent() && observed.consultedSources().equals(SOURCE_SHA256);
    }

    /** Original native query and source identity validation happen in the existing shared projector. */
    public static byte[] execute(byte[] raw) {
        ObjectNode outer = StrictJson.object(StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES),
                Set.of("operation", "settlement", "war_outcome_stakes_request"));
        StrictJson.require(OPERATION.equals(StrictJson.text(outer.get("operation"))), "M0 political operation differs");
        Settlement settlement = Settlement.decode(outer.get("settlement"));
        ObjectNode request = StrictJson.object(outer.get("war_outcome_stakes_request"), Set.of("schema", "war_id", "snapshot",
                "campaign_root", "current_source_sha256", "observation_context"));
        StrictJson.require(WarOutcomeStakesProjector.REQUEST_SCHEMA.equals(StrictJson.text(request.get("schema"))), "war stakes request schema differs");
        int warId = (int) StrictJson.integer(request.get("war_id"), 1, Integer.MAX_VALUE);
        WarOutcomeStakesResult observed = new WarOutcomeStakesProjector(ReviewedSourceRegistry.bundled()).project(
                request.get("snapshot"), warId, request.get("campaign_root"), request.get("current_source_sha256"),
                ObservationContext.fromJson(request.get("observation_context")));
        Assessment assessment = assess(observed, settlement);
        ObjectNode result = StrictJson.object();
        result.put("schema", "xar.g2-m0-refused-demand-settlement-exposure/v1");
        result.put("status", assessment.status().name().toLowerCase(Locale.ROOT));
        result.put("settlement", settlement.wire()); result.put("research_sha256", RESEARCH_SHA256);
        var reasons = result.putArray("conditional_political_reasons");
        assessment.conditionalReasons().forEach(reason -> reasons.add(reason.name().toLowerCase(Locale.ROOT)));
        result.put("conditional_hard_imprisonment_if_not_imprisoned", assessment.conditionalHardImprisonmentIfNotImprisoned());
        result.put("conditional_direct_vassal_faction_cooldown", assessment.conditionalDirectVassalCooldown());
        result.set("source_observation", observed.toJson());
        if (assessment.status() == Status.SOURCE_REVIEWED_CONDITIONAL) {
            JsonNode matching = null;
            for (JsonNode query : request.get("snapshot").get("war_termination_options")) {
                if (StrictJson.integer(query.get("war_id"), 1, Integer.MAX_VALUE) == warId) { matching = query; break; }
            }
            if (matching == null) { throw new IllegalStateException("qualified query disappeared from immutable input"); }
            JsonNode option = matching.get("options").get(settlement == Settlement.WHITE_PEACE ? "white_peace" : "surrender");
            result.set("native_legal_now", option.get("available"));
            result.set("recipient_accepts_now", option.get("recipient_response").get("would_accept_now"));
        } else { result.putNull("native_legal_now"); result.putNull("recipient_accepts_now"); }
        result.put("actual_penalty_verified", false); result.put("automatic_title_transfer_verified", false);
        result.putNull("actual_war_result"); result.putNull("selected_action"); result.put("action_ready", false);
        result.put("continue_legal_war_processing", true);
        return StrictJson.canonical(result, StrictJson.OUTPUT_MAX_BYTES);
    }
}
