package org.xar.ck3.control.wave2.events.choiceplanning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** Complete unavailable branch of the original event-window contract, not an available-option validator. */
final class UnavailableEventContextProjection {
    private static final Set<String> FIELDS = Set.of("schema", "schema_version", "status", "snapshot_revision",
            "date_raw", "current_event_instance_id", "window_match_count", "unavailable_reason", "event_definition_key",
            "calculated_event_id", "runtime_stats_ordinal", "root_scope", "saved_scopes", "options", "readiness", "provenance");
    private static final Set<String> READINESS = Set.of("event_definition_identity_ready", "root_scope_ready",
            "saved_scopes_ready", "option_presentation_ready", "effect_indicators_ready", "effect_preview_ready", "semantic_decision_ready");
    private static final Set<String> PROVENANCE = Set.of("root", "idler_vtable_rva", "manager_offset", "backend_id");
    private UnavailableEventContextProjection() { }

    static boolean valid(JsonNode node, BigInteger eventId, BigInteger dateRaw, BigInteger nativeRevision) {
        try {
            ObjectNode row = ChoicePlanningJson.exactObject(node, FIELDS);
            BigInteger version = ChoicePlanningJson.integer(row.get("schema_version"));
            ChoicePlanningJson.require(BigInteger.ONE.equals(version) || BigInteger.TWO.equals(version), "event schema version");
            ChoicePlanningJson.require((BigInteger.ONE.equals(version) ? "current-event-window-context-v1" : "current-event-window-context-v2")
                    .equals(ChoicePlanningJson.text(row.get("schema"))), "event schema");
            ChoicePlanningJson.require("unavailable".equals(ChoicePlanningJson.text(row.get("status"))), "unavailable branch required");
            ChoicePlanningJson.require(ChoicePlanningJson.unsigned(row.get("snapshot_revision"), true).equals(nativeRevision), "native frame");
            ChoicePlanningJson.require(ChoicePlanningJson.signed32(row.get("date_raw")).equals(dateRaw), "event date");
            ChoicePlanningJson.require(ChoicePlanningJson.positive32(row.get("current_event_instance_id")).equals(eventId), "event instance");
            BigInteger count = ChoicePlanningJson.integer(row.get("window_match_count"));
            ChoicePlanningJson.require(count.signum() >= 0 && count.compareTo(BigInteger.valueOf(32)) <= 0, "match count");
            ObjectNode readiness = ChoicePlanningJson.exactObject(row.get("readiness"), READINESS);
            for (String name : READINESS) { ChoicePlanningJson.bool(readiness.get(name)); }
            ObjectNode provenance = ChoicePlanningJson.exactObject(row.get("provenance"), PROVENANCE);
            String backend = ChoicePlanningJson.text(provenance.get("backend_id"));
            String root;
            String vtable;
            switch (backend) {
                case "ck3-1.19.0.6-native-event-window-v1" -> { root = "module+0x570F7B8->+0x10"; vtable = "0x40B1D30"; }
                case "ck3-1.20.0.2-native-event-window-v1", "ck3-1.20.0.3-native-event-window-v1" -> {
                    root = "module+0x5C6A520->+0x10"; vtable = "0x44BC408";
                }
                case "ck3-1.20.0.4-native-event-window-v1" -> { root = "module+0x5C6A520->+0x10"; vtable = "0x44BC418"; }
                default -> throw new IllegalArgumentException("unqualified event provenance backend");
            }
            ChoicePlanningJson.require(root.equals(ChoicePlanningJson.text(provenance.get("root")))
                    && vtable.equals(ChoicePlanningJson.text(provenance.get("idler_vtable_rva")))
                    && "+0x28".equals(ChoicePlanningJson.text(provenance.get("manager_offset"))), "event exact-build locator");
            String reason = ChoicePlanningJson.text(row.get("unavailable_reason"));
            boolean partial = "event_saved_scope_invalid".equals(reason)
                    && ChoicePlanningJson.bool(readiness.get("event_definition_identity_ready"));
            if (partial) {
                String key = ChoicePlanningJson.text(row.get("event_definition_key"));
                ChoicePlanningJson.require(key.getBytes(java.nio.charset.StandardCharsets.UTF_8).length <= 16_384, "definition key byte bound");
                ChoicePlanningJson.signed32(row.get("calculated_event_id"));
                ChoicePlanningJson.signed32(row.get("runtime_stats_ordinal"));
                ChoicePlanningJson.require(count.signum() == 0, "partial identity cannot gain a window");
            } else {
                for (String name : Set.of("event_definition_key", "calculated_event_id", "runtime_stats_ordinal")) {
                    ChoicePlanningJson.require(row.get(name).isNull(), "unavailable identity cannot be actionable");
                }
            }
            for (String name : Set.of("root_scope", "saved_scopes", "options")) {
                ChoicePlanningJson.require(row.get(name).isNull(), "unavailable event cannot contain scopes or options");
            }
            for (String name : READINESS) {
                ChoicePlanningJson.require(partial && "event_definition_identity_ready".equals(name)
                        || !ChoicePlanningJson.bool(readiness.get(name)), "unavailable readiness became actionable");
            }
            return true;
        } catch (IllegalArgumentException error) { return false; }
    }
}
