package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;

public record ManagerSelectorFrame(CareerJson.Header header, boolean provider_observed, Optional<Selection> selection,
        CareerReadiness.Selector readiness, CareerProvenance provenance) {
    public enum TitleTier { DUCHY, KINGDOM, EMPIRE, HEGEMONY }
    public record Selection(int manager_character_id, int subordinate_character_id, int manager_contract_id,
            int subordinate_contract_id, int manager_primary_title_id, int manager_primary_title_tier_raw,
            TitleTier manager_primary_title_tier_key, String manager_government_key) { }
    public static ManagerSelectorFrame decode(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "selector_kind", "request_nonce", "snapshot_revision", "date_raw", "paused",
                "player_character_id", "provider_observed", "selection", "readiness", "unavailable_reason", "provenance");
        require(text(row.get("selector_kind")).equals(DEPENDENCY), "selector kind drift");
        Header header = CareerJson.header(row, binding, false, false);
        CareerReadiness.Selector readiness = CareerReadiness.Selector.parse(row.get("readiness"));
        CareerProvenance provenance = CareerProvenance.parse(row.get("provenance"), CareerProvenance.Profile.SELECTOR);
        boolean observed = bool(row.get("provider_observed"));
        if (header.status() == Availability.UNAVAILABLE) {
            require(Set.of("unsupported_build", "requires_application_main", "requires_paused", "map_not_ready",
                    "native_relationship_enumeration_unavailable", "no_bounded_ai_direct_manager",
                    "bounded_ai_manager_has_no_direct_subordinate", "state_changed", "internal_error").contains(header.unavailable_reason().orElseThrow())
                    && !observed && row.get("selection").isNull() && !readiness.ready(), "unavailable selector leaked a candidate");
            return new ManagerSelectorFrame(header, false, Optional.empty(), readiness, provenance);
        }
        require(observed && readiness.flags().stream().allMatch(Boolean::booleanValue), "selector candidate not completely native observed");
        JsonNode s = exact(row.get("selection"), "manager_character_id", "subordinate_character_id", "manager_contract_id",
                "subordinate_contract_id", "manager_primary_title_id", "manager_primary_title_tier_raw", "manager_primary_title_tier_key", "manager_government_key");
        int manager = id(s.get("manager_character_id")), subordinate = id(s.get("subordinate_character_id"));
        int tier = int32(s.get("manager_primary_title_tier_raw")); require(tier >= 3 && tier <= 6 && manager != subordinate, "invalid manager/subordinate identities or tier");
        TitleTier tierKey = TitleTier.values()[tier - 3];
        require(text(s.get("manager_primary_title_tier_key")).equals(tierKey.name().toLowerCase(java.util.Locale.ROOT))
                && text(s.get("manager_government_key")).equals("celestial_government"), "selector manager tier/government drift");
        Selection selection = new Selection(manager, subordinate, id(s.get("manager_contract_id")), id(s.get("subordinate_contract_id")),
                id(s.get("manager_primary_title_id")), tier, tierKey, text(s.get("manager_government_key")));
        return new ManagerSelectorFrame(header, true, Optional.of(selection), readiness, provenance);
    }
}
