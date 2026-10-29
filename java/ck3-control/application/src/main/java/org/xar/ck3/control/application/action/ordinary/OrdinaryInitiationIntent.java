package org.xar.ck3.control.application.action.ordinary;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.require;

/** One command-argument contract shared by family planning, public facade and native preparation. */
public record OrdinaryInitiationIntent(String interactionKey, long recipientId, Optional<Education> education,
        Optional<Obj> planningProof) {
    public static final String SCHEMA = "xar.ck3.ordinary-initiation-intent/v1";
    public record Education(long childId, long guardianId, List<String> optionKeys) {
        public Education {
            character(childId); character(guardianId); require(childId != guardianId, "education pair differs");
            optionKeys = List.copyOf(optionKeys); require(optionKeys.size() <= 4096 && optionKeys.stream().distinct().count() == optionKeys.size(), "complete distinct education option intent");
            optionKeys.forEach(OrdinaryInitiationIntent::key);
        }
    }
    public OrdinaryInitiationIntent {
        key(interactionKey); character(recipientId); education = Objects.requireNonNull(education); planningProof = Objects.requireNonNull(planningProof);
        require(education.isPresent() == interactionKey.equals("educate_child_interaction"), "education initiation needs the exact complete intent; other interactions carry no education fields");
        require(education.isEmpty() || recipientId == education.orElseThrow().childId(), "education recipient is the exact child");
    }
    public Obj toJson() {
        var fields = new java.util.LinkedHashMap<String, Value>(); fields.put("schema", new Text(SCHEMA)); fields.put("interaction_key", new Text(interactionKey));
        fields.put("recipient_id", number(recipientId));
        fields.put("education", education.<Value>map(value -> new Obj(java.util.Map.of("child_full_id", number(value.childId()), "guardian_full_id", number(value.guardianId()),
                "requested_option_keys", new Arr(value.optionKeys().stream().<Value>map(Text::new).toList())))).orElse(Nil.INSTANCE));
        fields.put("planning_proof", planningProof.<Value>map(value -> value).orElse(Nil.INSTANCE)); return new Obj(fields);
    }
    public static OrdinaryInitiationIntent fromJson(Obj value) {
        require(value.members().keySet().equals(Set.of("schema", "interaction_key", "recipient_id", "education", "planning_proof")), "closed ordinary initiation arguments");
        require(SCHEMA.equals(OpportunityJson.text(value.get("schema"), "schema")), "ordinary initiation argument version");
        Optional<Education> education = Optional.empty();
        if (value.get("education") != Nil.INSTANCE) {
            Obj row = OpportunityJson.object(value.get("education"), "education"); require(row.members().keySet().equals(Set.of("child_full_id", "guardian_full_id", "requested_option_keys")), "complete education intent fields");
            education = Optional.of(new Education(id(row.get("child_full_id")), id(row.get("guardian_full_id")),
                    OpportunityJson.array(row.get("requested_option_keys"), "requested_option_keys").stream().map(raw -> OpportunityJson.text(raw, "option key")).toList()));
        }
        Optional<Obj> proof = value.get("planning_proof") == Nil.INSTANCE ? Optional.empty() : Optional.of(OpportunityJson.object(value.get("planning_proof"), "planning proof"));
        return new OrdinaryInitiationIntent(OpportunityJson.text(value.get("interaction_key"), "interaction_key"), id(value.get("recipient_id")), education, proof);
    }
    private static IntegerValue number(long value) { return new IntegerValue(java.math.BigInteger.valueOf(value)); }
    private static long id(Value value) { long id = OpportunityJson.integer(value, "full Character ID").longValueExact(); character(id); return id; }
    private static void character(long value) { require(value > 0 && value <= 0xffff_fffeL, "complete generation-bearing uint32 Character ID"); }
    private static void key(String value) { require(value != null && value.matches("[A-Za-z0-9_]{1,128}"), "exact ASCII key"); }
}
