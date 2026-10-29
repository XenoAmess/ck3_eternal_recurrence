package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.warpolicy.NativeTerminationTerms.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** The original generic-visible regiment contract; current soldiers never prove authored-source losses. */
public final class NativeRaiktorWarBound {
    private NativeRaiktorWarBound() { }
    public static ObjectNode normalize(JsonNode value, int warId, int attacker, int defender,
            BigInteger snapshotRevision, BigInteger nativeRevision, int dateRaw) {
        ObjectNode root = exact(value, Set.of("schema_version", "backend_id", "status", "failure", "active_frame",
                "postwar_frame", "owner_character_id", "war_id", "source_attribution", "soldiers", "cleanup",
                "regiments", "readiness"), "war-bound regiment root");
        require(integer(root.get("schema_version")).equals(BigInteger.ONE)
                && text(root.get("backend_id")).equals("ck3-1.19.0.6-native-raiktor-war-bound-regiment-v1")
                && text(root.get("status")).equals("generic_war_bound_visible_source_unattributed")
                && root.get("failure").isNull(), "Raiktor war-bound regiment observation unavailable");
        require(warId != -1 && attacker != -1 && defender != -1
                && fullId(root.get("war_id")) == warId && fullId(root.get("owner_character_id")) == attacker,
                "Raiktor war-bound regiment binding disagrees");
        ObjectNode active = exact(root.get("active_frame"), Set.of("snapshot_revision", "native_revision", "date_raw",
                "paused", "war_id", "active_casus_belli_database_index", "active_casus_belli_key",
                "primary_attacker_character_id", "primary_defender_character_id"), "active_frame");
        require(bool(active.get("paused")) && fullId(active.get("war_id")) == warId
                && text(active.get("active_casus_belli_key")).equals("raiktor_claim_cb")
                && fullId(active.get("primary_attacker_character_id")) == attacker
                && fullId(active.get("primary_defender_character_id")) == defender
                && positiveU64(active.get("snapshot_revision")).equals(positiveU64(snapshotRevision))
                && positiveU64(active.get("native_revision")).equals(positiveU64(nativeRevision))
                && signed32(active.get("date_raw")) == dateRaw, "Raiktor war-bound active frame disagrees");
        nonnegative32(active.get("active_casus_belli_database_index"));
        ObjectNode source = exact(root.get("source_attribution"), Set.of("mode", "authored_candidate_name",
                "authored_spawn_army_count", "authored_soldiers_per_army", "authored_total_soldiers"), "source_attribution");
        require(text(source.get("mode")).equals("authored_candidate_only")
                && text(source.get("authored_candidate_name")).equals("norman_highwaymen")
                && number(source.get("authored_spawn_army_count"), 6, 6) == 6
                && number(source.get("authored_soldiers_per_army"), 500, 500) == 500
                && number(source.get("authored_total_soldiers"), 3000, 3000) == 3000,
                "Raiktor authored source boundary disagrees");
        ObjectNode soldiers = exact(root.get("soldiers"), Set.of("current_soldiers_observable", "observed_current_soldiers",
                "pre_soldiers_observable", "observed_pre_soldiers", "proven_soldier_loss_observable", "proven_soldiers_lost"), "soldiers");
        long total = number(soldiers.get("observed_current_soldiers"), 0, Long.MAX_VALUE);
        require(bool(soldiers.get("current_soldiers_observable")) && !bool(soldiers.get("pre_soldiers_observable"))
                && soldiers.get("observed_pre_soldiers").isNull() && !bool(soldiers.get("proven_soldier_loss_observable"))
                && soldiers.get("proven_soldiers_lost").isNull(), "Raiktor soldier observation overclaims evidence");
        ObjectNode cleanup = exact(root.get("cleanup"), Set.of("observable", "status"), "cleanup");
        boolean observable = bool(cleanup.get("observable"));
        if (observable) {
            require(Set.of("destroyed", "still_alive").contains(text(cleanup.get("status"))), "Raiktor cleanup status is unknown");
            ObjectNode post = exact(root.get("postwar_frame"), Set.of("snapshot_revision", "native_revision", "date_raw",
                    "paused", "frozen_war_id", "frozen_war_absent_from_active_wars"), "postwar_frame");
            require(bool(post.get("paused")) && bool(post.get("frozen_war_absent_from_active_wars"))
                    && fullId(post.get("frozen_war_id")) == warId, "Raiktor postwar frame disagrees");
            positiveU64(post.get("snapshot_revision")); positiveU64(post.get("native_revision")); signed32(post.get("date_raw"));
        } else require(root.get("postwar_frame").isNull() && cleanup.get("status").isNull(), "Raiktor cleanup frame exists without observation");
        var regiments = array(root.get("regiments"));
        require(!regiments.isEmpty(), "Raiktor war-bound regiment list is empty");
        Set<Integer> persistentIds = new HashSet<>(); Set<Integer> currentIds = new HashSet<>();
        BigInteger computedTotal = BigInteger.ZERO; boolean anyAlive = false;
        for (JsonNode valueRegiment : regiments) {
            ObjectNode regiment = exact(valueRegiment, Set.of("persistent_regiment_id", "bound_war_id",
                    "war_keep_on_attacker_victory", "current_soldiers", "postwar_persistent_state", "composition_rows"), "regiment");
            require(persistentIds.add(fullId(regiment.get("persistent_regiment_id"))), "duplicate persistent regiment generation");
            require(fullId(regiment.get("bound_war_id")) == warId && !bool(regiment.get("war_keep_on_attacker_victory")),
                    "generic war-bound selector drifted");
            long regimentTotal = number(regiment.get("current_soldiers"), 0, Long.MAX_VALUE);
            var rows = array(regiment.get("composition_rows")); require(rows.size() == 7, "war-bound composition must contain seven rows");
            JsonNode persistent = regiment.get("postwar_persistent_state");
            if (observable) {
                require(Set.of("destroyed", "still_alive").contains(text(persistent)), "postwar persistent state is unknown");
                anyAlive |= text(persistent).equals("still_alive");
            } else require(persistent.isNull(), "active observation invented postwar state");
            long computed = 0;
            for (int ordinal = 0; ordinal < rows.size(); ordinal++) {
                ObjectNode row = exact(rows.get(ordinal), Set.of("composition_ordinal", "current_army_regiment_id", "raised_carmy_id",
                        "current_soldiers", "current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence"), "composition row");
                require(number(row.get("composition_ordinal"), ordinal, ordinal) == ordinal, "war-bound composition ordinal drifted");
                JsonNode currentId = row.get("current_army_regiment_id");
                if (currentId.isNull()) {
                    require(row.get("raised_carmy_id").isNull() && row.get("current_soldiers").isNull(), "absent current regiment row is malformed");
                    if (observable) {
                        for (String key : List.of("current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence"))
                            require(text(row.get(key)).equals("not_present"), "absent cleanup row is malformed");
                    } else noCleanup(row);
                    continue;
                }
                require(currentIds.add(fullId(currentId)), "duplicate current regiment generation"); fullId(row.get("raised_carmy_id"));
                computed = Math.addExact(computed, nonnegative32(row.get("current_soldiers")));
                if (observable) {
                    String current = text(row.get("current_army_regiment_state"));
                    String army = text(row.get("raised_carmy_state")); String roster = text(row.get("frozen_carmy_roster_evidence"));
                    require(Set.of("destroyed", "still_alive").contains(current) && Set.of("destroyed", "still_alive").contains(army),
                            "current cleanup state is unknown");
                    require(!(army.equals("destroyed") && !roster.equals("frozen_army_destroyed"))
                            && !(army.equals("still_alive") && !Set.of("detached", "still_attached").contains(roster))
                            && !(current.equals("destroyed") && roster.equals("still_attached")), "cleanup roster evidence disagrees");
                    anyAlive |= current.equals("still_alive");
                } else noCleanup(row);
            }
            require(computed == regimentTotal, "regiment soldier aggregate disagrees");
            computedTotal = computedTotal.add(BigInteger.valueOf(regimentTotal));
        }
        require(computedTotal.equals(BigInteger.valueOf(total)), "war-bound soldier aggregate disagrees");
        require(!observable || text(cleanup.get("status")).equals("still_alive") == anyAlive, "aggregate cleanup status disagrees");
        ObjectNode readiness = exact(root.get("readiness"), Set.of("exact_raiktor_war_context_ready",
                "generic_war_bound_identity_ready", "current_soldiers_ready", "postwar_cleanup_ready",
                "source_specific_attribution_ready", "pre_soldiers_ready", "proven_soldier_loss_ready",
                "independently_visible_value_ready", "raiktor_source_specific_domain_ready"), "readiness");
        for (String key : List.of("exact_raiktor_war_context_ready", "generic_war_bound_identity_ready",
                "current_soldiers_ready", "independently_visible_value_ready")) require(bool(readiness.get(key)), "Raiktor war-bound readiness overclaims evidence");
        require(bool(readiness.get("postwar_cleanup_ready")) == observable, "Raiktor cleanup readiness differs");
        for (String key : List.of("source_specific_attribution_ready", "pre_soldiers_ready", "proven_soldier_loss_ready",
                "raiktor_source_specific_domain_ready")) require(!bool(readiness.get(key)), "Raiktor war-bound readiness overclaims evidence");
        return root.deepCopy();
    }
    private static void noCleanup(ObjectNode row) {
        for (String key : List.of("current_army_regiment_state", "raised_carmy_state", "frozen_carmy_roster_evidence"))
            require(row.get(key).isNull(), "active row invented cleanup state");
    }
}
