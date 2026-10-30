package org.xar.ck3.control.wave2.finance.factionalerts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel.*;

/** Single original _subrealm_counties_component validator shared by alert and membership consumers. */
public final class FactionSubrealmCodec {
    public static final String COMPONENT = COUNTY_COMPONENT;
    public static final String SCOPE = COUNTY_SCOPE;
    public static final String SOURCE = COUNTY_SOURCE;
    private static final Set<String> FIELDS = Set.of("status", "complete", "scope", "source", "snapshot_revision", "date_raw", "actor_character_id", "county_title_ids", "unavailable_reason");
    private FactionSubrealmCodec() { }
    public static ObjectNode toJson(SubrealmCounties component, int actor, BigInteger nativeRevision, int dateRaw) {
        NativeCharacterId.of(actor);
        StrictJson.require(component != null && nativeRevision != null && nativeRevision.signum() > 0
                && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "validated subrealm component/owner/revision required");
        ObjectNode root = StrictJson.object(); boolean complete = component instanceof CompleteCounties;
        root.put("status", complete ? "available" : "unavailable"); root.put("complete", complete);
        root.put("scope", SCOPE); root.put("source", SOURCE); root.put("snapshot_revision", nativeRevision);
        root.put("date_raw", dateRaw); root.put("actor_character_id", actor);
        if (component instanceof CompleteCounties counties) {
            var ids = root.putArray("county_title_ids"); counties.countyTitleIds().forEach(ids::add); root.putNull("unavailable_reason");
        } else { root.putNull("county_title_ids"); root.put("unavailable_reason", ((IncompleteCounties) component).unavailableReason()); }
        return root;
    }
    public static SubrealmCounties parse(JsonNode raw, int actor, BigInteger nativeRevision, int dateRaw) {
        NativeCharacterId.of(actor);
        StrictJson.require(nativeRevision != null && nativeRevision.signum() > 0
                && nativeRevision.compareTo(StrictJson.UINT64_MAX) <= 0, "validated expected subrealm owner/revision required");
        if (!(raw instanceof ObjectNode root)) throw refusal("subrealm county component fields are invalid");
        Set<String> fields = new HashSet<>(); root.fieldNames().forEachRemaining(fields::add);
        if (!fields.equals(FIELDS)) throw refusal("subrealm county component fields are invalid");
        if (!text(root.get("scope"), COUNTY_SCOPE) || !text(root.get("source"), COUNTY_SOURCE)
                || !character(root.get("actor_character_id")).equals(BigInteger.valueOf(actor))
                || !integer(root.get("snapshot_revision"), "subrealm.revision", BigInteger.ONE, StrictJson.UINT64_MAX).equals(nativeRevision)
                || !integer(root.get("date_raw"), "subrealm.date", BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).equals(BigInteger.valueOf(dateRaw))) {
            throw refusal("subrealm county source does not match the owner frame");
        }
        JsonNode complete = root.get("complete");
        if (!complete.isBoolean()) throw refusal("subrealm.complete must be boolean");
        if (complete.booleanValue()) {
            if (!text(root.get("status"), "available") || !root.get("unavailable_reason").isNull()) throw refusal("complete subrealm county component has contradictory status");
            List<Integer> ids = ids(root.get("county_title_ids"));
            if (ids.size() > 16384) throw refusal("subrealm county set exceeds its source bound");
            return new CompleteCounties(ids);
        }
        JsonNode reason = root.get("unavailable_reason");
        if (!text(root.get("status"), "unavailable") || !root.get("county_title_ids").isNull()
                || !reason.isTextual() || reason.textValue().isEmpty() || reason.textValue().codePointCount(0, reason.textValue().length()) > 256) {
            throw refusal("incomplete subrealm county component cannot expose a partial set");
        }
        return new IncompleteCounties(reason.textValue());
    }
    private static List<Integer> ids(JsonNode node) {
        if (!node.isArray()) throw refusal("subrealm.county_title_ids must be a list");
        List<Integer> ids = new ArrayList<>(); int previous = 0; int index = 0; boolean ordered = true;
        for (JsonNode value : node) {
            int id = integer(value, "subrealm.county_title_ids[" + index++ + "]", BigInteger.ONE, BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
            ordered &= id > previous; previous = id; ids.add(id);
        }
        if (!ordered) throw refusal("subrealm.county_title_ids must be sorted and unique"); return List.copyOf(ids);
    }
    private static BigInteger character(JsonNode node) {
        try { return NativeCharacterId.fromJson(node).asBigInteger(); }
        catch (IllegalArgumentException error) { throw refusal("subrealm.actor must be an exact present native character identity"); }
    }
    private static BigInteger integer(JsonNode node, String field, BigInteger minimum, BigInteger maximum) {
        if (node == null || !node.isIntegralNumber() || node.bigIntegerValue().compareTo(minimum) < 0 || node.bigIntegerValue().compareTo(maximum) > 0) {
            throw refusal(field + " must be an integer in [" + minimum + ", " + maximum + "]");
        }
        return node.bigIntegerValue();
    }
    private static boolean text(JsonNode node, String expected) { return node != null && node.isTextual() && node.textValue().equals(expected); }
    private static org.xar.ck3.control.contracts.projection.ProjectionDomainRejection refusal(String reason) {
        return new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection(reason);
    }
}
