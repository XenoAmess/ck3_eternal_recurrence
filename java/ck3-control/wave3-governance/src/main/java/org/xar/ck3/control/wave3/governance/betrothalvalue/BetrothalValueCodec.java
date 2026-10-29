package org.xar.ck3.control.wave3.governance.betrothalvalue;

import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.ValueFields.*;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalProposals;

/** Strict finite JSON entry; the existing builder remains the sole proposal projection codec. */
public final class BetrothalValueCodec {
    public static final String SCHEMA = "xar.ck3.betrothal-value-request.v1";
    private BetrothalValueCodec() { }

    public static EvaluationInput decode(byte[] raw) {
        ObjectValue root = object(BetrothalCodec.decodeEvidence(raw));
        require(root.values().keySet().equals(Set.of("schema", "snapshot", "relationship")), "all and only value request envelope fields required");
        require(SCHEMA.equals(text(get(root, "schema"))), "value request schema changed");
        ObjectValue snapshot = object(get(root, "snapshot")), relation = object(get(root, "relationship"));
        // This is the builder's declared field projection, not native qualification or the full validator.
        BuildInput builder = BetrothalCodec.decodeBuild(BetrothalCodec.encodeEvidence(new ObjectValue(Map.of(
                "schema", new TextValue(BetrothalCodec.BUILD_SCHEMA), "relation", relation, "snapshot", snapshot,
                "selected", new BooleanValue(false), "reasons", new ArrayValue(List.of())))));
        WireValue playedValue = get(snapshot, "played_character");
        PlayedCharacter played = playedValue instanceof ObjectValue player
                ? new PlayedCharacter(character(get(player, "character_id")), nullableBoolean(get(player, "alive"))) : null;
        Snapshot projectedSnapshot = new Snapshot(nullableBoolean(get(snapshot, "paused")), nullableBoolean(get(snapshot, "map_ready")), played,
                nullableInteger(get(snapshot, "native_revision")), nullableInteger(get(snapshot, "date_raw")), nullableText(get(snapshot, "episode_run_id")), snapshot, builder.frame());
        Field<List<BigInteger>> spouses = !relation.values().containsKey("spouse_character_ids") ? Field.missing()
                : nil(get(relation, "spouse_character_ids")) ? Field.nil() : Field.of(characters(get(relation, "spouse_character_ids")));
        Relationship projectedRelation = new Relationship(nullableText(get(relation, "schema")), nullableText(get(relation, "status")),
                nullableBoolean(get(relation, "read_only")), nullableBoolean(get(relation, "advertised")), nullableInteger(get(relation, "native_revision")),
                character(get(relation, "heir_character_id")), character(get(relation, "betrothed_character_id")), character(get(relation, "primary_spouse_character_id")), spouses,
                nullableBoolean(get(relation, "bilateral_verified")), get(relation, "betrothal_actionability"), nullableText(get(relation, "exact_ck3_build")),
                nullableText(get(relation, "exe_sha256")), builder.relation(), relation);
        return new EvaluationInput(projectedSnapshot, projectedRelation);
    }

    public static byte[] encode(EvaluationInput input) {
        return BetrothalCodec.encodeEvidence(new ObjectValue(Map.of("schema", new TextValue(SCHEMA),
                "snapshot", input.snapshot().original(), "relationship", input.relationship().original())));
    }

    public static byte[] encodeChoice(Choice choice) {
        Map<String, WireValue> output = new HashMap<>();
        Actionability value = choice.value().projection();
        output.put("status", new TextValue(choice.status() == ChoiceStatus.SELECTED ? "selected" : "held"));
        output.put("reasons", new ArrayValue(choice.reasons().stream().<WireValue>map(reason -> new TextValue(reason.wire())).toList()));
        output.put("selected_step", choice.status() == ChoiceStatus.SELECTED ? new TextValue(BetrothalProposals.SUBMIT_STEP) : NullValue.INSTANCE);
        output.put("heir_character_id", wire(choice.heir())); output.put("candidate_character_id", wire(choice.partner()));
        output.put("recipient_character_id", wire(value.roles().recipient())); output.put("intermediary_character_id", wire(value.roles().intermediary()));
        output.put("generic_costs", BetrothalCodec.projectEvidence(BetrothalCodec.resourceNode(choice.resourceProposal()).get("immediate_generic_costs")));
        output.put("matrilineal_option_selected", wire(value.matrilinealOptionSelected()));
        output.put("native_child_house_preview", value.nativeChildHousePreview());
        output.put("current_first_heir_descendants_v1", choice.descendants()); output.put("current_first_heir_descendants_summary_v1", choice.descendantsSummary());
        output.put("effective_matrilineal_if_accepted", wire(value.effectiveMatrilinealIfAccepted()));
        output.put("predicted_outcome_if_accepted", value.predictedOutcomeIfAccepted() == null ? NullValue.INSTANCE : new TextValue(value.predictedOutcomeIfAccepted()));
        output.put("resource_proposal", BetrothalCodec.decodeEvidence(BetrothalCodec.encodeResource(choice.resourceProposal())));
        return BetrothalCodec.encodeEvidence(new ObjectValue(output));
    }

    public static byte[] encodeValidatedActionability(ValidatedActionability value) {
        return BetrothalCodec.encodeEvidence(value.original());
    }
}
