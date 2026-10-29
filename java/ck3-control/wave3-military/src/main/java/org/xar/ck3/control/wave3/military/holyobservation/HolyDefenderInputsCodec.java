package org.xar.ck3.control.wave3.military.holyobservation;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract.Choice;
import org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.Build;
import org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.ContextRoles;
import org.xar.ck3.control.wave3.military.holyobservation.HolyDefenderInputs.Joiner;

/** Exact child DTO and complete normalized owner/frame checks. No private native transport is opened. */
public final class HolyDefenderInputsCodec {
    private static final Set<String> FIELDS = Set.of("schema", "read_only", "available", "unavailable_reason", "capture_epoch",
            "native_revision", "public_revision", "date_raw", "played_character_id", "declaration_id", "selected_declaration",
            "primary_attacker_character_id", "primary_defender_character_id", "primary_defender_faith_available",
            "primary_defender_faith_unavailable_reason", "primary_defender_rite_id", "primary_defender_faith_id", "cb_flags_raw",
            "defender_faith_can_join", "native_joiner_set_observed", "joiner_count", "joiners", "raw_scale", "unit", "is_final_join_score");
    private static final Set<String> ROW_FIELDS = Set.of("character_id", "row_faith_available", "row_fervor_available", "unavailable_reason",
            "rite_id", "faith_id", "faith_fervor_raw", "matches_primary_defender_faith");
    private static final Set<String> SELECTED_FIELDS = Set.of("target_character_id", "casus_belli_index", "casus_belli_key",
            "configuration_index", "claimant_character_id", "target_title_ids");
    private HolyDefenderInputsCodec() { }

    public static HolyDefenderInputs normalize(JsonNode raw, HolyCostObservation owner, JsonNode snapshot) {
        require(owner != null, "complete normalized owning declaration context required");
        ObjectNode input = StrictJson.object(raw, FIELDS);
        require(text(input.get("schema")).equals(schema(owner.build())), "defender input schema belongs to another exact build");
        StrictJson.trueValue(input.get("read_only"));
        StrictJson.integer(input.get("raw_scale"), 100_000, 100_000);
        require(text(input.get("unit")).equals("fervor_points") && !bool(input.get("is_final_join_score")),
                "fervor inputs cannot become a final join score");
        ObjectNode outer = object(snapshot);
        ObjectNode hello = object(object(outer.get("diagnostics")).get("hello"));
        require(owner.originalExecutableSha256().equals(owner.build().executableSha256())
                && text(hello.get("expected_ck3_version")).equals(owner.build().gameVersion())
                && text(hello.get("expected_ck3_sha256")).equals(owner.build().executableSha256()),
                "exact owner identity mismatch");
        BigInteger epoch = uint64(input.get("capture_epoch"));
        BigInteger nativeRevision = uint64(input.get("native_revision"));
        BigInteger publicRevision = uint64(input.get("public_revision"));
        require(epoch.equals(owner.captureEpoch()) && nativeRevision.equals(owner.nativeRevision())
                && publicRevision.equals(owner.publicRevision()) && nativeRevision.equals(uint64(outer.get("native_revision")))
                && publicRevision.equals(uint64(outer.get("revision"))), "child revisions differ from owner or snapshot");
        int date = signed32(input.get("date_raw"));
        int played = signed32(input.get("played_character_id"));
        require(date == owner.dateRaw() && date == signed32(outer.get("date_raw")) && played == owner.playedCharacterId()
                && played == signed32(object(outer.get("played_character")).get("character_id")), "child date/player differs from owner or snapshot");
        String declarationId = text(input.get("declaration_id"));
        require(!declarationId.isEmpty() && declarationId.equals(owner.declarationId()), "child declaration differs from owner");
        ObjectNode selected = StrictJson.object(input.get("selected_declaration"), SELECTED_FIELDS);
        ObjectNode row = selected.deepCopy(); row.put("declaration_id", declarationId);
        ObjectNode catalogue = StrictJson.object(); catalogue.putArray("declarable_wars").add(row);
        Choice childChoice = HolyCostJsonAdapter.selectedDeclaration(catalogue, declarationId);
        require(childChoice.equals(owner.selectedDeclaration()), "child selected declaration differs from owner");
        boolean available = bool(input.get("available"));
        boolean observed = bool(input.get("native_joiner_set_observed"));
        require(available == observed, "availability must describe complete native set observation");
        String reason = reason(input.get("unavailable_reason"), available);
        Long attacker = uint32Nullable(input.get("primary_attacker_character_id"));
        Long defender = uint32Nullable(input.get("primary_defender_character_id"));
        ContextRoles roles = owner.roles();
        role(attacker, roles.additionalRoleCharacterId()); role(defender, roles.recipientCharacterId());
        boolean rolesComplete = attacker != null && defender != null
                && Boolean.FALSE.equals(roles.additionalRoleUsesNativeFallback()) && Boolean.FALSE.equals(roles.recipientUsesNativeFallback());
        boolean fallback = Boolean.TRUE.equals(roles.additionalRoleUsesNativeFallback()) || Boolean.TRUE.equals(roles.recipientUsesNativeFallback());
        require(!observed || rolesComplete, "observed set requires actual non-fallback receivers");
        require(!fallback || !available && !observed, "native role fallback cannot claim an observed set");
        boolean primaryFaith = bool(input.get("primary_defender_faith_available"));
        String primaryReason = reason(input.get("primary_defender_faith_unavailable_reason"), primaryFaith);
        Long primaryRite = uint32Nullable(input.get("primary_defender_rite_id"));
        Long primaryFaithId = uint32Nullable(input.get("primary_defender_faith_id"));
        Long flags = uint32Nullable(input.get("cb_flags_raw"));
        Boolean canJoin = nullableBool(input.get("defender_faith_can_join"));
        long count = unsigned32(input.get("joiner_count"));
        JsonNode rows = input.get("joiners");
        require(rows.isArray() && rows.size() == count, "joiners must be the complete ordered native set");
        List<Joiner> joiners = new ArrayList<>();
        for (JsonNode rawRow : rows) {
            ObjectNode value = StrictJson.object(rawRow, ROW_FIELDS);
            boolean faithAvailable = bool(value.get("row_faith_available"));
            boolean fervorAvailable = bool(value.get("row_fervor_available"));
            joiners.add(new Joiner(unsigned32(value.get("character_id")), faithAvailable, fervorAvailable,
                    reason(value.get("unavailable_reason"), faithAvailable && fervorAvailable),
                    uint32Nullable(value.get("rite_id")), uint32Nullable(value.get("faith_id")),
                    signed64Nullable(value.get("faith_fervor_raw")), nullableBool(value.get("matches_primary_defender_faith"))));
        }
        return new HolyDefenderInputs(owner.build(), available, reason, epoch, nativeRevision, publicRevision, date, played,
                declarationId, childChoice, attacker, defender, primaryFaith, primaryReason, primaryRite, primaryFaithId,
                flags, canJoin, observed, count, joiners);
    }
    public static ObjectNode encode(HolyDefenderInputs value) {
        ObjectNode output = StrictJson.object();
        output.put("schema", schema(value.build())); output.put("read_only", true); output.put("available", value.available());
        output.put("unavailable_reason", value.unavailableReason()); output.put("capture_epoch", value.captureEpoch());
        output.put("native_revision", value.nativeRevision()); output.put("public_revision", value.publicRevision());
        output.put("date_raw", value.dateRaw()); output.put("played_character_id", value.playedCharacterId());
        output.put("declaration_id", value.declarationId()); output.set("selected_declaration", HolyCostJsonAdapter.selectedJson(value.selectedDeclaration()));
        output.put("primary_attacker_character_id", value.primaryAttackerCharacterId()); output.put("primary_defender_character_id", value.primaryDefenderCharacterId());
        output.put("primary_defender_faith_available", value.primaryDefenderFaithAvailable());
        output.put("primary_defender_faith_unavailable_reason", value.primaryDefenderFaithUnavailableReason());
        output.put("primary_defender_rite_id", value.primaryDefenderRiteId()); output.put("primary_defender_faith_id", value.primaryDefenderFaithId());
        output.put("cb_flags_raw", value.cbFlagsRaw()); output.put("defender_faith_can_join", value.defenderFaithCanJoin());
        output.put("native_joiner_set_observed", value.nativeJoinerSetObserved()); output.put("joiner_count", value.joinerCount());
        ArrayNode rows = output.putArray("joiners");
        for (Joiner row : value.joiners()) {
            rows.addObject().put("character_id", row.characterId()).put("row_faith_available", row.faithAvailable())
                    .put("row_fervor_available", row.fervorAvailable()).put("unavailable_reason", row.unavailableReason())
                    .put("rite_id", row.riteId()).put("faith_id", row.faithId()).put("faith_fervor_raw", row.faithFervorRaw())
                    .put("matches_primary_defender_faith", row.matchesPrimaryDefenderFaith());
        }
        output.put("raw_scale", 100_000); output.put("unit", "fervor_points"); output.put("is_final_join_score", false);
        return output;
    }
    private static void role(Long child, Integer owner) {
        require(child == null || owner != null && child == Integer.toUnsignedLong(owner), "child role differs from actual owning role bits");
    }
    private static String schema(Build build) {
        return build == Build.CK3_12004 ? "ck3_12004_holy_war_defender_join_inputs_v1" : "ck3_12003_holy_war_defender_join_inputs_v1";
    }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "source object required"); return (ObjectNode) value; }
    private static String text(JsonNode value) { require(value != null && value.isTextual(), "source string required"); return value.textValue(); }
    private static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "actual boolean required"); return value.booleanValue(); }
    private static Boolean nullableBool(JsonNode value) { require(value != null, "nullable boolean field required"); return value.isNull() ? null : bool(value); }
    private static int signed32(JsonNode value) { return (int) StrictJson.integer(value, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    private static BigInteger uint64(JsonNode value) { return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX); }
    private static long unsigned32(JsonNode value) { return StrictJson.integer(value, 0, 0xffff_ffffL); }
    private static Long uint32Nullable(JsonNode value) { require(value != null, "nullable uint32 field required"); return value.isNull() ? null : unsigned32(value); }
    private static Long signed64Nullable(JsonNode value) { require(value != null, "nullable int64 field required"); return value.isNull() ? null : StrictJson.integer(value, Long.MIN_VALUE, Long.MAX_VALUE); }
    private static String reason(JsonNode value, boolean available) {
        require(value != null, "availability reason field required");
        String reason = value.isNull() ? null : text(value);
        HolyDefenderInputs.reason(reason, available);
        return reason;
    }
}
