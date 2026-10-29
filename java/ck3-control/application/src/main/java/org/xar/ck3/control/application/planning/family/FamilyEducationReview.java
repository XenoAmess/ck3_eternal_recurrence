package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsCodec;
import org.xar.ck3.control.wave3.governance.educationoptions.EducationOptionsModel;

/** Complete pure payload-review consumer. The registered native read owns source qualification; review grants no dispatch. */
public final class FamilyEducationReview {
    static final String SCHEMA = "xar.ck3.education-payload-review-private.v1";
    private static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private FamilyEducationReview() { }
    public static Obj prepare(Obj query, Obj snapshot, Obj requested) {
        Value child = fullId(requested.get("child_full_id")), guardian = fullId(requested.get("guardian_full_id")), recipient = fullId(requested.get("recipient_id"));
        if (eq(child, guardian)) throw new IllegalArgumentException("education child and guardian must differ");
        Value requestedKeys = requested.get("requested_option_keys");
        if (requestedKeys == null) requestedKeys = Nil.INSTANCE;
        Set<String> keys = requestedKeys == Nil.INSTANCE ? null : optionKeys(requestedKeys);
        Obj context = object(query.get("character_interaction_ordinary_context")), roles = object(context.get("effective_roles"));
        requireBuild(snapshot, context);
        if (!eq(query.get("queried_revision"), snapshot.get("revision")) || !eq(query.get("queried_native_revision"), snapshot.get("native_revision"))
                || !eq(query.get("queried_snapshot_id"), snapshot.get("snapshot_id"))) throw new IllegalArgumentException("education preflight crossed current frame");
        if (!"educate_child_interaction".equals(string(context.get("interaction_key"))) || !eq(context.get("recipient_id"), recipient)
                || !eq(context.get("snapshot_revision"), snapshot.get("native_revision")) || !eq(context.get("date_raw"), snapshot.get("date_raw"))
                || !eq(context.get("player_character_id"), object(snapshot.get("played_character")).get("character_id")))
            throw new IllegalArgumentException("education native context crossed actual interaction, recipient or frame");
        var options = EducationOptionsCodec.decode(bytes(obj("schema", t(EducationOptionsCodec.INPUT_SCHEMA), "context", context)));
        BigInteger declared = integer(context.get("declared_option_count")), selected = integer(context.get("selected_option_count"));
        if (declared.signum() < 0 || selected.signum() < 0) throw new IllegalArgumentException("unsigned education counts required");
        boolean rowsAvailable = options.rows().isPresent() && options.rows().get().status() == EducationOptionsModel.Availability.AVAILABLE;
        List<EducationOptionsModel.Row> selectedRows = rowsAvailable ? options.rows().get().rows().stream().filter(EducationOptionsModel.Row::ordinalSelected).toList() : List.of();
        boolean unavailableKey = selectedRows.stream().anyMatch(row -> row.canonicalFlagKey() == null);
        Set<String> observedKeys = rowsAvailable && !unavailableKey ? new LinkedHashSet<>() : null;
        if (observedKeys != null) selectedRows.forEach(row -> observedKeys.add(row.canonicalFlagKey()));
        String reason = null;
        if (!"available".equals(string(context.get("status")))) reason = "native_context_unavailable";
        else if (roles.get("secondary_recipient_id") == Nil.INSTANCE || roles.get("secondary_actor_id") == Nil.INSTANCE) reason = "education_secondary_roles_unavailable";
        else if (!eq(roles.get("secondary_recipient_id"), child) || !eq(roles.get("secondary_actor_id"), guardian)) reason = "education_selected_full_roles_mismatch";
        else if (keys == null) reason = "education_option_intent_unsupplied";
        else if (options.rows().isPresent() && !rowsAvailable) reason = "education_option_rows_unavailable";
        else if (rowsAvailable && unavailableKey) reason = "observed_selected_option_key_unavailable";
        else if (rowsAvailable && !keys.equals(observedKeys)) reason = "education_selected_option_intent_mismatch";
        else if (!rowsAvailable && !keys.isEmpty()) reason = "requested_option_flag_identity_unpublished";
        else if (!rowsAvailable && selected.signum() != 0) reason = "observed_selected_option_identity_unpublished";
        else if (booleanValue(context.get("special_payload_present"), "special_payload_present")) reason = "education_special_payload_materialization_unqualified";
        boolean knownEmpty = "available".equals(string(context.get("status"))) && (rowsAvailable ? selectedRows.isEmpty() : options.rows().isEmpty() && selected.signum() == 0);
        Value nativeRows = rowsAvailable ? object(context.get("education_option_rows")).get("rows") : Nil.INSTANCE;
        Value optionKeys = rowsAvailable ? observedKeys == null ? Nil.INSTANCE : strings(observedKeys) : knownEmpty ? rows(List.of()) : Nil.INSTANCE;
        Obj optionSource = obj("status", t(knownEmpty ? "known_empty" : observedKeys != null ? "available" : "unavailable"),
                "declared_option_count", new IntegerValue(declared), "selected_option_count", new IntegerValue(selected),
                "selected_ordinal_count", rowsAvailable ? n(selectedRows.size()) : Nil.INSTANCE, "selected_option_keys", optionKeys,
                "native_selected_option_mask", Nil.INSTANCE, "native_option_rows", nativeRows, "raw_education_option_rows", nil(context.get("education_option_rows")));
        Obj intent = obj("recipient_id", recipient, "child_full_id", child, "guardian_full_id", guardian, "requested_option_keys", requestedKeys);
        Obj payload = null; Value token = Nil.INSTANCE;
        if (reason == null) {
            payload = obj("interaction_key", t("educate_child_interaction"), "full_id_encoding", t("uint32_generation_preserved"),
                    "effective_roles", roles, "semantic_subject_character_id", child, "semantic_object_character_id", guardian,
                    "selected_option_keys", rowsAvailable ? strings(observedKeys) : rows(List.of()), "all_declared_options_off", new Bool(knownEmpty),
                    "declared_option_count", new IntegerValue(declared), "selected_option_count", new IntegerValue(selected));
            if (rowsAvailable) payload = payload.with("selected_ordinal_count", n(selectedRows.size())).with("native_option_rows", nativeRows)
                    .with("selected_option_ordinals", new Arr(selectedRows.stream().<Value>map(row -> n(row.declaredOrdinal())).toList()))
                    .with("selected_option_flags_full_u32", new Arr(selectedRows.stream().<Value>map(row -> n(row.flagFullU32())).toList()))
                    .with("option_bank_values_u8", new Arr(options.rows().get().rows().stream().<Value>map(row -> n(row.bankValueU8())).toList()));
            token = t(ActionCodec.sha256(asciiCanonical(obj("source_query", query, "request_intent", intent, "semantic_payload", payload))));
        }
        return obj("schema", t(SCHEMA), "status", t(reason == null ? "available" : "unavailable"), "reason", reason == null ? Nil.INSTANCE : t(reason),
                "read_only", new Bool(true), "request_intent", intent, "source_query", query, "effective_roles", roles, "option_source", optionSource,
                "requested_shown", reason == null ? exactBoolean(context.get("shown"), "shown") : Nil.INSTANCE,
                "requested_can_send", reason == null ? exactBoolean(context.get("can_send"), "can_send") : Nil.INSTANCE,
                "semantic_payload", nil(payload), "review_token", token, "generic_ordinary_context_supported", exactBoolean(context.get("ordinary_context_supported"), "ordinary_context_supported"),
                "native_materialization_ready", new Bool(false), "dispatch_ready", new Bool(false), "submitted", new Bool(false), "material_result", new Bool(false));
    }
    private static void requireBuild(Obj snapshot, Obj context) {
        Obj hello = object(object(snapshot.get("diagnostics")).get("hello"));
        Value version = hello.members().containsKey("expected_ck3_version") ? hello.get("expected_ck3_version") : hello.get("game_version");
        Value sha = hello.members().containsKey("expected_ck3_sha256") ? hello.get("expected_ck3_sha256") : hello.get("executable_sha256");
        if (!"1.20.0.4".equals(string(version)) || !(sha instanceof Text hash) || !EXE.equalsIgnoreCase(hash.value())
                || !"1.20.0.4".equals(string(context.get("exact_build")))) throw new IllegalArgumentException("education payload requires the exact current .4 executable");
        Value actualHash = context.get("executable_sha256");
        if (!(actualHash instanceof Text nativeHash && EXE.equalsIgnoreCase(nativeHash.value()))
                && !(actualHash == Nil.INSTANCE && !"available".equals(string(context.get("status")))))
            throw new IllegalArgumentException("education native context executable changed");
    }
    private static Value fullId(Value raw) {
        BigInteger id = positive(raw); if (id.compareTo(BigInteger.valueOf(4_294_967_294L)) > 0) throw new IllegalArgumentException("complete unsigned Character ID required"); return raw;
    }
    private static Set<String> optionKeys(Value value) {
        List<Value> entries = array(value); if (entries.size() > 4096) throw new IllegalArgumentException("bounded education option intent required");
        Set<String> result = new LinkedHashSet<>();
        for (Value raw : entries) if (!result.add(EducationOptionsModel.key(text(raw)))) throw new IllegalArgumentException("duplicate education intent keys");
        return result;
    }
    private static Arr strings(Set<String> strings) { return new Arr(strings.stream().<Value>map(Text::new).toList()); }
    private static boolean booleanValue(Value value, String field) { return OpportunityJson.bool(value, field); }
    private static Bool exactBoolean(Value value, String field) { return new Bool(booleanValue(value, field)); }
    /** Python ensure_ascii=True digest domain, retaining full integers and the shared finite binary64 rendering. */
    public static byte[] asciiCanonical(Value value) {
        StringBuilder output = new StringBuilder(); append(value, output);
        if (output.length() > 2_097_152) throw new IllegalArgumentException("education review digest byte budget");
        return output.toString().getBytes(StandardCharsets.US_ASCII);
    }
    private static void append(Value value, StringBuilder output) {
        if (value instanceof Obj object) {
            List<String> keys = new ArrayList<>(object.members().keySet()); keys.sort(JointBudgetSelector::comparePythonText); output.append('{');
            for (int i = 0; i < keys.size(); i++) { if (i != 0) output.append(','); quote(keys.get(i), output); output.append(':'); append(object.get(keys.get(i)), output); } output.append('}');
        } else if (value instanceof Arr array) {
            output.append('['); for (int i = 0; i < array.items().size(); i++) { if (i != 0) output.append(','); append(array.items().get(i), output); } output.append(']');
        } else if (value instanceof Text text) quote(text.value(), output);
        else if (value instanceof IntegerValue number) output.append(number.value());
        else if (value instanceof DecimalValue) output.append(new String(ContinuityJson.canonical(OpportunityJson.toNode(value)), StandardCharsets.UTF_8));
        else if (value instanceof Bool bool) output.append(bool.value());
        else if (value == Nil.INSTANCE) output.append("null");
        else throw new IllegalArgumentException("missing education review digest value");
    }
    private static void quote(String value, StringBuilder output) {
        output.append('"'); String hex = "0123456789abcdef";
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> output.append("\\\""); case '\\' -> output.append("\\\\"); case '\b' -> output.append("\\b"); case '\f' -> output.append("\\f");
                case '\n' -> output.append("\\n"); case '\r' -> output.append("\\r"); case '\t' -> output.append("\\t");
                default -> { if (c < 0x20 || c >= 0x7f) output.append("\\u").append(hex.charAt((c >>> 12) & 15)).append(hex.charAt((c >>> 8) & 15)).append(hex.charAt((c >>> 4) & 15)).append(hex.charAt(c & 15)); else output.append(c); }
            }
        }
        output.append('"');
    }
}
