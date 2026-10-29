package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Factual complete direct-vassal capital seeds. Native route/contact checks remain authoritative. */
public final class DefenderRefugeScopes {
    private DefenderRefugeScopes() { }

    public static Optional<List<Integer>> directVassalCapitalProvinceIds(Obj root) {
        if (root == null || !named(root,"status","available")) return Optional.empty();
        Obj readiness = obj(root.get("readiness")).orElse(null);
        Value actor = root.get("player_character_id"), topLiege = root.get("top_liege_character_id");
        if (!yes(readiness,"direct_landed_vassals_ready") || !yes(readiness,"related_character_contexts_ready")
                || !int32Id(actor) || !int32Id(topLiege) || !(root.get("direct_landed_vassal_character_ids") instanceof Arr ids)
                || !(root.get("related_character_contexts") instanceof Arr rows)) return Optional.empty();
        List<Integer> direct = new ArrayList<>();
        for (Value value : ids.items()) { if (!int32Id(value)) return Optional.empty(); direct.add(integer(value,"vassal").intValueExact()); }
        if (new HashSet<>(direct).size() != direct.size()) return Optional.empty();
        Map<Integer,Optional<Integer>> found = new LinkedHashMap<>();
        for (Value value : rows.items()) {
            if (!(value instanceof Obj row)) return Optional.empty();
            if (!named(row,"relationship_role","direct_landed_vassal")) continue;
            if (!int32Id(row.get("character_id"))) return Optional.empty();
            int character = idAt(row,"character_id");
            if (!direct.contains(character) || found.containsKey(character)
                    || !eq(row,"immediate_liege_character_id",actor) || !eq(row,"top_liege_character_id",topLiege)) return Optional.empty();
            Obj title = obj(row.get("primary_title")).orElse(null);
            if (title == null || !int32Id(title.get("title_id")) || !(title.get("tier_raw") instanceof IntegerValue tier)
                    || tier.value().compareTo(BigInteger.ONE) < 0 || tier.value().compareTo(BigInteger.valueOf(6)) > 0) return Optional.empty();
            Value raw = row.get("capital_province_id");
            if (raw != null && raw != Nil.INSTANCE && !int32Id(raw)) return Optional.empty();
            found.put(character, int32Id(raw) ? Optional.of(integer(raw,"capital").intValueExact()) : Optional.empty());
        }
        if (!found.keySet().equals(new HashSet<>(direct))) return Optional.empty();
        List<Integer> provinces = found.values().stream().flatMap(Optional::stream).sorted().toList();
        if (new HashSet<>(provinces).size() != provinces.size()) return Optional.empty();
        return Optional.of(provinces);
    }

    public static Optional<Obj> directVassalRefugeLifecycleScope(Obj snapshot, Obj root) {
        if (snapshot == null || root == null) return Optional.empty();
        Value actor = actor(snapshot);
        if (!yes(snapshot,"paused") || !yes(snapshot,"map_ready") || !nil(snapshot,"active_event")
                || !nil(snapshot,"pending_character_interaction") || !named(root,"status","available")
                || !equalField(root,"snapshot_revision",snapshot,"native_revision")
                || !equalField(root,"date_raw",snapshot,"date_raw") || !eq(root,"player_character_id",actor)) return Optional.empty();
        Optional<List<Integer>> maybeCandidates = directVassalCapitalProvinceIds(root);
        if (maybeCandidates.isEmpty() || maybeCandidates.orElseThrow().isEmpty()
                || !(snapshot.get("active_wars") instanceof Arr wars) || wars.items().size() != 1
                || !(wars.items().getFirst() instanceof Obj war) || !named(war,"player_side","defender")
                || !yes(war,"player_is_primary_war_leader") || !emptyArray(war,"war_objective_province_ids")
                || !(snapshot.get("player_armies") instanceof Arr)) return Optional.empty();
        List<Obj> controlled = rows(snapshot.get("player_armies")).stream().filter(a -> yes(a,"controllable")).toList();
        if (controlled.size() != 1) return Optional.empty();
        Obj army = controlled.getFirst();
        List<Value> countyCapitals = new ArrayList<>();
        for (Obj row : rows(root.get("held_title_partition"))) {
            Obj title = obj(row.get("title")).orElse(null);
            if (title != null && eq(title,"tier_raw",new IntegerValue(BigInteger.TWO))) countyCapitals.add(row.get("capital_province_id"));
        }
        if (countyCapitals.size() != 1 || !int32Id(countyCapitals.getFirst()) || !unitId(army.get("army_id"))
                || !int32Id(army.get("current_province_id"))) return Optional.empty();
        int own = integer(countyCapitals.getFirst(),"own capital").intValueExact(), current = idAt(army,"current_province_id");
        List<Integer> candidates = maybeCandidates.orElseThrow();
        if (current != own && !candidates.contains(current) || !eq(army,"owner_character_id",actor)
                || !named(army,"army_state","regular") || !no(army,"in_combat") || !no(army,"retreating")
                || !emptyArray(army,"route_province_ids") || !nil(army,"move_target_province_id")
                || !(war.get("enemy_armies") instanceof Arr enemies)) return Optional.empty();
        List<Integer> hostiles = new ArrayList<>();
        for (Value value : enemies.items()) {
            if (!(value instanceof Obj enemy)) return Optional.empty();
            if (yes(enemy,"retreating")) continue;
            if (!unitId(enemy.get("army_id"))) return Optional.empty();
            hostiles.add(integerAt(enemy,"army_id").intValueExact());
        }
        if (hostiles.isEmpty() || hostiles.size() > 64 || new HashSet<>(hostiles).size() != hostiles.size()) return Optional.empty();
        hostiles.sort(Integer::compareTo);
        List<Integer> destinations = new ArrayList<>(candidates.stream().filter(v -> v != current).toList());
        if (current != own) destinations.add(own);
        return Optional.of(new Obj(Map.of("army_id",army.get("army_id"),"current_province_id",army.get("current_province_id"),
                "own_capital_province_id",new IntegerValue(BigInteger.valueOf(own)),"current_kind",new Text(current == own ? "directly_held_capital" : "direct_vassal_capital"),
                "candidate_province_ids",integers(destinations),"hostile_army_ids",integers(hostiles))));
    }

    public static Optional<Obj> sameFrameDirectVassalRefugeScope(Obj snapshot, Obj cachedQuery) {
        if (snapshot == null || cachedQuery == null) return Optional.empty();
        Obj diagnostics = obj(snapshot.get("diagnostics")).orElse(null), binding = obj(cachedQuery.get("cache_binding")).orElse(null);
        if (diagnostics == null || binding == null) return Optional.empty();
        for (String key : List.of("snapshot_id","revision","native_revision","date_raw"))
            if (!equalField(binding,key,snapshot,key)) return Optional.empty();
        if (!eq(binding,"actor_character_id",actor(snapshot)) || !equalField(binding,"bridge_pid",diagnostics,"bridge_pid")
                || !equalField(binding,"connection_generation",diagnostics,"connection_generation")) return Optional.empty();
        return obj(cachedQuery.get("campaign_root_context")).flatMap(root -> directVassalRefugeLifecycleScope(snapshot,root));
    }
    private static Value actor(Obj snapshot) {
        Value actor = snapshot.get("actor_character_id");
        if (actor == null || actor == Nil.INSTANCE) return obj(snapshot.get("played_character")).map(p -> p.get("character_id")).orElse(Nil.INSTANCE);
        return actor;
    }
}
