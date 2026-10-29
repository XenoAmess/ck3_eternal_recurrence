package org.xar.ck3.control.wave3.governance.guardianskills;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusManagement;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceCodec;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.BindingStatus;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.GuardianProfile;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.SkillObservation;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsModel.*;

/** One intrinsic profile implementation is shared with preference; this leaf adds the original context binding. */
public final class GuardianSkillsCodec {
    public static final String INPUT_SCHEMA = "xar.java.request-guardian-focus-skill-input.v1";
    private GuardianSkillsCodec() { }

    public static GuardianProfile validate(byte[] profileRaw, byte[] contextRaw) {
        GuardianProfile profile = EducationPreferenceCodec.decodeGuardianProfile(profileRaw);
        return GuardianSkillInputs.validateContextBinding(profile, context(StrictJson.parse(contextRaw)));
    }

    public static Input decode(byte[] raw) {
        return projectParsedInput(StrictJson.parse(raw));
    }

    /** Internal field parser; public consumers use the bounded raw codec or typed records. */
    static Input projectParsedInput(JsonNode parsed) {
        JsonNode root = StrictJson.object(parsed, Set.of("schema", "needs", "context"));
        StrictJson.require(text(root, "schema").equals(INPUT_SCHEMA), "guardian focus-skill wrapper schema");
        JsonNode needs = object(required(root, "needs")); JsonNode context = object(required(root, "context"));
        JsonNode rawFrame = required(needs, "frame"); Optional<FamilyFrame> family = rawFrame.isNull() ? Optional.empty() : Optional.of(familyFrame(rawFrame));
        FocusSubject subject = new FocusSubject(id(needs, "raw_character_id"), focus(required(needs, "focus_management")), family);
        JsonNode rawProfile = context.get("request_guardian_skill_inputs_v1");
        if (rawProfile == null || rawProfile.isNull()) { return new Input(subject, Optional.empty(), Optional.empty()); }
        GuardianProfile profile = EducationPreferenceCodec.decodeGuardianProfile(StrictJson.canonical(rawProfile)); Context owner = context(context);
        GuardianSkillInputs.validateContextBinding(profile, owner); return new Input(subject, Optional.of(profile), Optional.of(owner));
    }

    public static FocusSubject fromNeedsRow(EducationNeedsModel.NeedsRowProjection needs) {
        var original = needs.focusSourceFrame();
        return new FocusSubject(needs.childFullId(), needs.focusManagement(), Optional.of(new FamilyFrame(original.nativeRevision(),
                original.playedCharacterId(), original.heirCharacterId(), original.dateRaw())));
    }

    public static byte[] encodeInput(Input input) {
        ObjectNode root = StrictJson.object(); root.put("schema", INPUT_SCHEMA); ObjectNode needs = root.putObject("needs");
        needs.put("raw_character_id", input.needs().childFullId()); needs.set("focus_management", focus(input.needs().focusManagement()));
        needs.set("frame", familyFrame(input.needs().familyFrame())); ObjectNode context = root.putObject("context");
        if (input.profile().isEmpty()) { context.putNull("request_guardian_skill_inputs_v1"); }
        else {
            Context owner = input.context().orElseThrow(); context.put("exact_build", owner.exactBuild()); context.put("interaction_key", owner.interactionKey());
            context.put("status", owner.status()); context.put("snapshot_revision", owner.frame().nativeRevision()); context.put("date_raw", owner.frame().dateRaw());
            context.put("player_character_id", owner.frame().playerCharacterId()); ObjectNode roles = context.putObject("effective_roles");
            roles.put("secondary_actor_id", owner.secondaryActorId()); roles.put("secondary_recipient_id", owner.secondaryRecipientId());
            context.set("request_guardian_skill_inputs_v1", profile(input.profile().get()));
        }
        return StrictJson.canonical(root);
    }

    public static byte[] encodeProjection(Projection projection) {
        ObjectNode root = StrictJson.object(); root.put("schema", "request_guardian_focus_skill_inputs_v1");
        GuardianProfile profile = projection.profile().orElse(null);
        root.put("child_character_id", profile == null ? null : profile.childCharacterId()); root.put("focus_child_character_id", projection.needs().childFullId());
        root.put("character_id", profile == null ? null : profile.characterId()); root.put("owning_native_revision", profile == null ? null : profile.owningNativeRevision());
        root.put("role_source", "request_guardian_secondary_actor"); root.put("binding_status", profile == null ? BindingStatus.UNAVAILABLE.wire() : profile.bindingStatus().wire());
        root.set("focus_management", focus(projection.needs().focusManagement())); root.put("focus_key", projection.needs().focusManagement().currentKey());
        root.set("family_focus_frame", familyFrame(projection.needs().familyFrame())); root.put("focus_projection_join_available", projection.join().available());
        root.put("focus_projection_unavailable_reason", projection.join().reason()); root.set("focus_skill", skill(projection.focusSkill())); root.set("learning_skill", skill(projection.learningSkill()));
        root.set("raw_profile", profile == null ? StrictJson.object().nullNode() : profile(profile)); root.put("effect_educator_selection_observed", false);
        return StrictJson.canonical(root);
    }

    private static Context context(JsonNode node) {
        object(node); JsonNode roles = object(required(node, "effective_roles"));
        return new Context(text(node, "exact_build"), text(node, "interaction_key"), text(node, "status"),
                new QueryFrame(StrictJson.integer(required(node, "snapshot_revision"), BigInteger.ZERO, StrictJson.UINT64_MAX),
                        StrictJson.integer(required(node, "date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE), StrictJson.integer(required(node, "player_character_id"), 1, Integer.MAX_VALUE)),
                nullableId(roles, "secondary_actor_id"), nullableId(roles, "secondary_recipient_id"));
    }
    private static FamilyFrame familyFrame(JsonNode node) {
        StrictJson.object(node, Set.of("native_revision", "played_character_id", "heir_character_id", "date_raw"));
        JsonNode revision = required(node, "native_revision"), date = required(node, "date_raw");
        return new FamilyFrame(revision.isNull() ? null : StrictJson.integer(revision, BigInteger.ZERO, StrictJson.UINT64_MAX),
                nullableId(node, "played_character_id"), nullableId(node, "heir_character_id"), date.isNull() ? null : StrictJson.integer(date, Long.MIN_VALUE, Long.MAX_VALUE));
    }
    private static JsonNode familyFrame(Optional<FamilyFrame> frame) {
        if (frame.isEmpty()) { return StrictJson.object().nullNode(); }
        FamilyFrame value = frame.get(); ObjectNode node = StrictJson.object(); node.put("native_revision", value.nativeRevision());
        node.put("played_character_id", value.playedCharacterId()); node.put("heir_character_id", value.heirCharacterId()); node.put("date_raw", value.dateRaw()); return node;
    }
    private static FocusManagement focus(JsonNode node) {
        StrictJson.object(node, Set.of("available", "state", "current_key", "focus_absent", "education_focus_present", "unavailable_reason"));
        String wire = text(node, "state"); FocusState state = null;
        for (FocusState candidate : FocusState.values()) { if (candidate.wire().equals(wire)) { state = candidate; } }
        StrictJson.require(state != null, "known focus-management state required");
        return new FocusManagement(bool(node, "available"), state, nullableText(node, "current_key"), nullableBool(node, "focus_absent"),
                nullableBool(node, "education_focus_present"), nullableText(node, "unavailable_reason"));
    }
    private static ObjectNode focus(FocusManagement value) {
        ObjectNode node = StrictJson.object(); node.put("available", value.available()); node.put("state", value.state().wire()); node.put("current_key", value.currentKey());
        node.put("focus_absent", value.focusAbsent()); node.put("education_focus_present", value.educationFocusPresent()); node.put("unavailable_reason", value.unavailableReason()); return node;
    }
    private static ObjectNode skill(SkillObservation value) {
        ObjectNode node = StrictJson.object(); node.put("available", value.available()); node.put("value", value.value()); node.put("unavailable_reason", value.unavailableReason()); return node;
    }
    private static JsonNode profile(GuardianProfile profile) { return StrictJson.parse(profile.original().canonicalJson().getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode required(JsonNode node, String key) { JsonNode value = node.get(key); StrictJson.require(value != null, "required field: " + key); return value; }
    private static JsonNode object(JsonNode node) { StrictJson.require(node != null && node.isObject(), "required legacy projection object"); return node; }
    private static String text(JsonNode node, String key) { return StrictJson.text(required(node, key)); }
    private static String nullableText(JsonNode node, String key) { JsonNode value = required(node, key); return value.isNull() ? null : StrictJson.text(value); }
    private static boolean bool(JsonNode node, String key) { JsonNode value = required(node, key); StrictJson.require(value.isBoolean(), "exact Boolean token required"); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode node, String key) { return required(node, key).isNull() ? null : bool(node, key); }
    private static long id(JsonNode node, String key) { return StrictJson.integer(required(node, key), 0, 4_294_967_294L); }
    private static Long nullableId(JsonNode node, String key) { return required(node, key).isNull() ? null : id(node, key); }
}
