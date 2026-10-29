package org.xar.ck3.control.application.planning.family;

import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Pure original result/alliance reducer. It grants no Native read or physical-write authority. */
public final class FamilyResultReducer {
    private FamilyResultReducer() { }
    public static Obj reduce(Query query, Obj ledger, Obj arguments, Obj result, BridgeIdentity bridge, BigInteger observedDateRaw) {
        if (observedDateRaw == null || observedDateRaw.signum() < 0) throw new IllegalArgumentException("nonnegative original read frame date required");
        boolean family = query == Query.FAMILY_RESULT || query == Query.FAMILY_ALLIANCE;
        boolean childDefault = query == Query.DEFAULT_RESULT || query == Query.DEFAULT_ALLIANCE;
        if (query == Query.FAMILY_ALLIANCE || query == Query.MATRILINEAL_ALLIANCE || query == Query.DEFAULT_ALLIANCE)
            return alliance(query, ledger, object(arguments.get("resolved")), result, bridge);
        if (query != Query.FAMILY_RESULT && query != Query.MATRILINEAL_RESULT && query != Query.DEFAULT_RESULT)
            throw new IllegalArgumentException("not a family material result operation");
        Obj pending = object(arguments.get("pending")); boolean cold = yes(arguments.get("cold"));
        Obj prior = ledger.get("resolved") instanceof Obj resolved ? resolved : null;
        boolean recheck = cold && ledger.get("pending") == Nil.INSTANCE && prior != null && pending.equals(prior.get("source_pending"));
        if (!recheck && !pending.equals(ledger.get("pending"))) throw new IllegalArgumentException("pending family pair changed before result reduction");
        String status = text(result.get("status"));
        if (family && yes(pending.get("fulfill_existing_betrothal"))
                && (!yes(result.get("fulfill_existing_betrothal")) || !oneOf(result.get("status"), "pending", "accepted_pending", "refused", "invalidated", "marriage")))
            throw new IllegalArgumentException("fulfillment result cannot consume original betrothal");
        for (String key : List.of("heir_character_id", "candidate_character_id"))
            if (result.get(key) != null && !eq(pending.get(key), result.get(key))) throw new IllegalArgumentException("family result crossed source pair");
        if (recheck) {
            if (!material(prior) || !(status.equals(string(prior.get("status"))) || "betrothal".equals(string(prior.get("status"))) && "marriage".equals(status))
                    || !yes(result.get("material_result"))) throw new IllegalArgumentException("cold restore lost earlier bilateral material pair");
            Obj verified = prior.with("status", t(status)).with("post_bridge_pid", n(bridge.pid())).with("post_bridge_creation_date", t(bridge.creationDate()))
                    .with("cold_recovery_verified", new Bool(true));
            if (!family) verified = remove(verified, "actual_alliance_result", "alliance_bridge_pid", "alliance_bridge_creation_date");
            else if (!status.equals(string(prior.get("status")))) verified = remove(verified, "alliance_result")
                    .with("cold_material_transition", t("betrothal_to_marriage")).with("cold_material_native_revision", result.get("post_native_revision"));
            return ledger.with("resolved", verified);
        }
        if (oneOf(result.get("status"), "marriage", "betrothal", "refused", "invalidated") || childDefault && "gone_unmaterialized".equals(status)) {
            if (material(result) && !yes(result.get("material_result"))) throw new IllegalArgumentException("material status requires observed material result");
            Obj resolved;
            if (family) resolved = obj("status", t(status), "material_result", result.get("material_result"), "episode_run_id", pending.get("episode_run_id"),
                    "heir_character_id", pending.get("heir_character_id"), "candidate_character_id", pending.get("candidate_character_id"),
                    "post_native_revision", result.get("post_native_revision"), "cold_recovery", new Bool(cold), "source_pending", pending,
                    "post_bridge_pid", n(bridge.pid()), "post_bridge_creation_date", t(bridge.creationDate()));
            else resolved = result.with("source_pending", pending).with("episode_run_id", pending.get("episode_run_id"))
                    .with("post_bridge_pid", n(bridge.pid())).with("post_bridge_creation_date", t(bridge.creationDate()));
            if (oneOf(result.get("status"), "refused", "invalidated")) resolved = resolved.with("rejected_candidate_ids", updatedHistory(pending, "prior_rejected_candidate_ids"));
            else if ("gone_unmaterialized".equals(status)) resolved = resolved.with("attempted_candidate_ids", updatedHistory(pending, "prior_attempted_candidate_ids"));
            return ledger.with("pending", Nil.INSTANCE).with("resolved", resolved);
        }
        if (!oneOf(result.get("status"), "pending", "accepted_pending")) throw new IllegalArgumentException("unavailable or UNKNOWN result cannot clear/replay family proposal");
        Obj updated = pending.with("last_checked_native_revision", result.get("post_native_revision"))
                .with("last_checked_bridge_pid", n(bridge.pid())).with("last_checked_bridge_creation_date", t(bridge.creationDate()));
        if (family && yes(pending.get("fulfill_existing_betrothal")))
            updated = remove(updated, "last_consumed_checkpoint_native_revision", "last_consumed_checkpoint_date_raw")
                    .with("last_checked_date_raw", new IntegerValue(observedDateRaw));
        if (family && cold && "pending".equals(status)) {
            updated = updated.with("cold_absent_relation_unresolved", new Bool(true));
            for (String field : List.of("outbound_pending_state", "outbound_pending_id", "outbound_pending_age_days", "outbound_pending_ai_reply_cutoff_days"))
                updated = updated.with("last_" + field, nil(result.get(field)));
        } else if (!family) updated = updated.with("last_outbound_pending_state", nil(result.get("outbound_pending_state")));
        if (childDefault) updated = remove(updated, "last_consumed_checkpoint_native_revision", "last_consumed_checkpoint_date_raw");
        return ledger.with("pending", updated);
    }
    /** Consumes the already observed same-frame bilateral relation; this never submits or invents an outcome. */
    public static Obj matureWarm(Obj ledger, Obj relation, BridgeIdentity bridge, String episodeRunId, BigInteger nativeRevision) {
        if (episodeRunId == null || episodeRunId.isBlank() || nativeRevision == null || nativeRevision.signum() <= 0)
            throw new IllegalArgumentException("actual warm family read frame required");
        if (!t("xar.ck3.first-heir-marriage-formal.v1").equals(ledger.get("schema")) || ledger.get("pending") != Nil.INSTANCE)
            throw new IllegalArgumentException("warm family transition requires the exact resolved family domain");
        Obj resolved = object(ledger.get("resolved"));
        if (!"betrothal".equals(string(resolved.get("status"))) || !yes(resolved.get("material_result"))
                || !t(episodeRunId).equals(resolved.get("episode_run_id")) || !bridge.matches(resolved, "post_")
                || !t("xar.ck3.current-first-heir-relationship.v1").equals(relation.get("schema"))
                || !"available".equals(string(relation.get("status"))) || !yes(relation.get("bilateral_verified"))
                || !new IntegerValue(nativeRevision).equals(relation.get("native_revision"))
                || !eq(resolved.get("heir_character_id"), relation.get("heir_character_id")))
            throw new IllegalArgumentException("warm family transition lacks the same current bilateral heir and Bridge");
        Value candidate = resolved.get("candidate_character_id"); positive(candidate);
        List<Value> spouses = array(relation.get("spouse_character_ids"));
        if (!eq(relation.get("primary_spouse_character_id"), candidate) && !spouses.contains(candidate))
            throw new IllegalArgumentException("the original betrothed candidate is not an observed current spouse");
        Obj updated = remove(resolved.with("status", t("marriage")).with("warm_material_transition", t("betrothal_to_marriage"))
                .with("warm_material_native_revision", new IntegerValue(nativeRevision)), "alliance_result");
        return ledger.with("resolved", updated);
    }
    private static Arr updatedHistory(Obj pending, String field) {
        Set<BigInteger> ids = new HashSet<>(FamilyOrdinaryPolicy.candidateHistory(pending, field));
        if (!ids.add(positive(pending.get("candidate_character_id")))) throw new IllegalArgumentException("duplicate family refusal/attempt history");
        return new Arr(ids.stream().sorted().<Value>map(IntegerValue::new).toList());
    }
    private static Obj alliance(Query query, Obj ledger, Obj resolved, Obj result, BridgeIdentity bridge) {
        if (ledger.get("pending") != Nil.INSTANCE || !resolved.equals(ledger.get("resolved")) || !material(resolved) || !yes(resolved.get("material_result")))
            throw new IllegalArgumentException("alliance read lacks exact resolved material pair");
        if (query == Query.MATRILINEAL_ALLIANCE || query == Query.DEFAULT_ALLIANCE) return ledger.with("resolved", resolved.with("actual_alliance_result", result)
                .with("alliance_bridge_pid", n(bridge.pid())).with("alliance_bridge_creation_date", t(bridge.creationDate())));
        Obj pending = object(resolved.get("source_pending")); Value before = pending.get("preproposal_played_has_recipient_alliance"), after = result.get("played_has_recipient_alliance");
        String transition = before instanceof Bool b && after instanceof Bool a ? "observed_" + b.value() + "_to_" + a.value() : "unknown";
        Obj observation = obj("status", result.get("alliance_status"), "recipient_character_id", pending.get("recipient_character_id"),
                "played_has_recipient_alliance", nil(after), "recipient_has_played_alliance", nil(result.get("recipient_has_played_alliance")),
                "preproposal_played_has_recipient_alliance", before instanceof Bool ? before : Nil.INSTANCE,
                "played_to_recipient_alliance_transition", t(transition), "relationship_status", nil(result.get("relationship_status")),
                "native_revision", nil(result.get("native_revision")), "bridge_pid", n(bridge.pid()), "bridge_creation_date", t(bridge.creationDate()));
        return ledger.with("resolved", resolved.with("alliance_result", observation));
    }
    private static Obj remove(Obj original, String... fields) {
        Map<String, Value> copy = new LinkedHashMap<>(original.members()); for (String field : fields) copy.remove(field); return new Obj(copy);
    }
}
