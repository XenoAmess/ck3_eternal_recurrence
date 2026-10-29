package org.xar.ck3.control.wave3.governance.betrothalvalue;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.ValueFields.*;

import java.math.BigInteger;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Complete original fixed-pair DTO validator, including prospective House input. */
public final class CurrentPairActionabilityValidator {
    private static final String[] ADULT_FIELDS = {"heir_is_adult", "partner_is_adult", "heir_adult_measure_raw",
            "partner_adult_measure_raw", "heir_adult_threshold_raw", "partner_adult_threshold_raw"};
    private CurrentPairActionabilityValidator() { }

    public static ValidatedActionability validate(WireValue input, Roles expected) {
        Objects.requireNonNull(expected);
        ObjectValue value = nil(input) ? unavailable(expected) : object(input);
        NativeStatus status = status(get(value, "status"));
        String reason = nullableText(get(value, "unavailable_reason"));
        require(status == NativeStatus.AVAILABLE ? reason == null : reason != null && !reason.isEmpty(), "actionability status/reason mismatch");
        Roles roles = new Roles(character(get(value, "actor_character_id")), character(get(value, "heir_character_id")),
                character(get(value, "partner_character_id")), character(get(value, "recipient_character_id")), character(get(value, "intermediary_character_id")));
        require(roles.actor() == null || roles.actor().equals(expected.actor()), "actionability actor changed");
        require(roles.heir() == null || roles.heir().equals(expected.heir()), "actionability heir changed");
        require(roles.partner() == null || roles.partner().equals(expected.partner()), "actionability partner changed");
        boolean adultAvailable = bool(get(value, "adult_readback_available"));
        boolean sampled = bool(get(value, "final_legality_sampled"));
        boolean acceptanceReady = bool(get(value, "recipient_acceptance_ready"));
        Boolean ready = nullableBoolean(get(value, "ready_to_marry_betrothed"));
        Boolean heirAdult = null, partnerAdult = null;
        BigInteger heirMeasure = null, partnerMeasure = null, heirThreshold = null, partnerThreshold = null;
        if (adultAvailable) {
            require(expected.partner() != null, "adult pair has no partner");
            heirAdult = bool(get(value, ADULT_FIELDS[0])); partnerAdult = bool(get(value, ADULT_FIELDS[1]));
            heirMeasure = signed(get(value, ADULT_FIELDS[2]), 16); partnerMeasure = signed(get(value, ADULT_FIELDS[3]), 16);
            heirThreshold = signed(get(value, ADULT_FIELDS[4]), 32); partnerThreshold = signed(get(value, ADULT_FIELDS[5]), 32);
            require(heirAdult == (heirMeasure.compareTo(heirThreshold) >= 0)
                    && partnerAdult == (partnerMeasure.compareTo(partnerThreshold) >= 0)
                    && Objects.equals(ready, heirAdult && partnerAdult), "adulthood flags/thresholds changed");
        } else {
            require(ready == null, "unavailable adulthood has readiness");
            for (String field : ADULT_FIELDS) { require(nil(get(value, field)), "unavailable adulthood has values"); }
        }
        Boolean complete = nullableBoolean(get(value, "complete_can_send"));
        require(sampled ? complete != null : complete == null, "legality sampled/complete mismatch");
        BigInteger score = null, answer = null;
        if (acceptanceReady) {
            score = signed(get(value, "recipient_ai_accept_raw"), 64);
            answer = integer(get(value, "recipient_answer_status_raw"));
            require(answer.signum() >= 0 && answer.compareTo(BigInteger.TWO) <= 0, "recipient answer outside 0/1/2");
        } else { require(nil(get(value, "recipient_ai_accept_raw")) && nil(get(value, "recipient_answer_status_raw")), "unavailable acceptance has values"); }
        Boolean effective = nullableBoolean(get(value, "effective_matrilineal_if_accepted"));
        Boolean selected = nullableBoolean(get(value, "matrilineal_option_selected"));
        String outcome = nullableText(get(value, "predicted_outcome_if_accepted"));
        require(outcome == null || Set.of("marriage", "betrothal").contains(outcome), "unknown native outcome");
        GenericCosts costs = costs(get(value, "generic_costs"));
        if (status == NativeStatus.AVAILABLE) {
            require(adultAvailable && sampled && acceptanceReady && costs != null && effective != null && outcome != null
                    && roles.actor() != null && roles.heir() != null && roles.partner() != null && roles.recipient() != null, "available native value incomplete");
        }
        if (status == NativeStatus.NOT_APPLICABLE) {
            require(expected.partner() == null && !adultAvailable && !sampled && !acceptanceReady && costs == null
                    && effective == null && selected == null && outcome == null, "inapplicable native value has pair values");
        }
        WireValue rawPreview = get(value, "native_child_house_preview");
        ChildHousePreview preview = preview(rawPreview, expected.heir(), expected.partner(), selected, effective, complete);
        Actionability projection = new Actionability(roles, costs, ready, outcome, selected, rawPreview, effective, score, answer);
        return new ValidatedActionability(status, reason,
                new AdultReadback(adultAvailable, heirAdult, partnerAdult, heirMeasure, partnerMeasure, heirThreshold, partnerThreshold, ready),
                new LegalityReadback(sampled, complete), new RecipientReadback(acceptanceReady, score, answer), preview, projection, value);
    }

    public static ChildHousePreview preview(WireValue input, BigInteger heir, BigInteger partner,
                                           Boolean selected, Boolean effective, Boolean complete) {
        if (nil(input)) { return null; }
        ObjectValue value = object(input); NativeStatus status = status(get(value, "status"));
        String reason = text(get(value, "reason"));
        require(status == NativeStatus.AVAILABLE ? reason.isEmpty() : !reason.isEmpty(), "preview status/reason mismatch");
        BigInteger subject = character(get(value, "subject_character_id"));
        BigInteger candidate = character(get(value, "candidate_character_id"));
        require(Objects.equals(subject, heir) && Objects.equals(candidate, partner)
                && Boolean.FALSE.equals(nullableBoolean(get(value, "requested_matrilineal_option"))), "preview pair/requested option changed");
        Boolean previewSelected = nullableBoolean(get(value, "selected_matrilineal_option"));
        Boolean previewEffective = nullableBoolean(get(value, "effective_matrilineal_if_accepted"));
        Boolean previewComplete = nullableBoolean(get(value, "complete_can_send"));
        BigInteger parent = nullableInteger(get(value, "native_selected_parent_character_id"));
        BigInteger house = nullableInteger(get(value, "house_id")), dynasty = nullableInteger(get(value, "dynasty_id"));
        if (status == NativeStatus.AVAILABLE) {
            require(partner != null && selected != null && previewSelected != null && previewEffective != null && previewComplete != null
                    && Objects.equals(previewSelected, selected) && Objects.equals(previewEffective, effective)
                    && Objects.equals(previewComplete, complete) && parent != null
                    && (parent.equals(heir) || parent.equals(partner)), "preview finalized values changed");
            for (BigInteger identity : new BigInteger[] {house, dynasty}) {
                require(identity == null || identity.signum() >= 0 && identity.bitLength() <= 31, "preview House/Dynasty out of range");
            }
        } else {
            require(previewSelected == null && previewEffective == null && previewComplete == null && parent == null && house == null && dynasty == null
                    && (status != NativeStatus.NOT_APPLICABLE || partner == null), "unavailable preview has values");
        }
        return new ChildHousePreview(status, reason, subject, candidate, previewSelected, previewEffective, previewComplete, parent, house, dynasty, value);
    }

    private static GenericCosts costs(WireValue input) {
        if (nil(input)) { return null; }
        ObjectValue value = object(input);
        BigInteger scale = integer(get(value, "raw_scale"));
        String payer = text(get(value, "payer_role")), timing = text(get(value, "application_timing"));
        require(scale.equals(BigInteger.valueOf(100_000)) && payer.equals("actor") && timing.equals("on_send"), "native send cost metadata changed");
        EnumMap<CostTerm, Field<BigInteger>> amounts = new EnumMap<>(CostTerm.class);
        Map<String, WireValue> extensions = new HashMap<>(value.values());
        extensions.keySet().removeAll(Set.of("raw_scale", "payer_role", "application_timing"));
        for (CostTerm term : CostTerm.values()) { amounts.put(term, Field.of(signed(get(value, term.wire()), 64))); extensions.remove(term.wire()); }
        return new GenericCosts(Field.of(scale), Field.of(payer), Field.of(timing), amounts, new ObjectValue(extensions));
    }
    private static NativeStatus status(WireValue input) {
        String value = text(input);
        for (NativeStatus status : NativeStatus.values()) { if (status.wire().equals(value)) { return status; } }
        throw new ProjectionDomainRejection("unknown fixed-pair native status");
    }
    private static ObjectValue unavailable(Roles roles) {
        Map<String, WireValue> fields = new HashMap<>();
        fields.put("status", new TextValue("unavailable")); fields.put("unavailable_reason", new TextValue("native_readback_not_supplied"));
        fields.put("actor_character_id", wire(roles.actor())); fields.put("heir_character_id", wire(roles.heir())); fields.put("partner_character_id", wire(roles.partner()));
        fields.put("adult_readback_available", new BooleanValue(false)); fields.put("final_legality_sampled", new BooleanValue(false)); fields.put("recipient_acceptance_ready", new BooleanValue(false));
        for (String field : ADULT_FIELDS) { fields.put(field, NullValue.INSTANCE); }
        for (String field : Set.of("ready_to_marry_betrothed", "complete_can_send", "recipient_ai_accept_raw", "recipient_answer_status_raw", "generic_costs",
                "matrilineal_option_selected", "native_child_house_preview", "effective_matrilineal_if_accepted", "predicted_outcome_if_accepted", "recipient_character_id", "intermediary_character_id")) {
            fields.put(field, NullValue.INSTANCE);
        }
        return new ObjectValue(fields);
    }
}
