package org.xar.ck3.control.wave2.planning.savedcountymembership;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.wave2.planning.scoretarget.ScalarField;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.CountyState;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Factor;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Family;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Geography;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Realm;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Reason;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult.Truth;

/** Whole active audit_saved_county_membership_v1 pure dependency closure. */
public final class SavedCountyMembership {
    private SavedCountyMembership() { }

    public static SavedMembershipResult audit(SavedMembershipInput input) {
        return new Evaluation(input).run();
    }

    private static final class Evaluation {
        private final SavedMembershipInput input;
        private final Map<BigInteger, Realm> realmCache = new HashMap<>();
        private final Map<BigInteger, Family> familyCache = new HashMap<>();
        Evaluation(SavedMembershipInput input) { this.input = input; }

        SavedMembershipResult run() {
            Map<String, Integer> keyCounts = new HashMap<>();
            input.projection().titles().values().forEach(title -> text(title.key()).ifPresent(key -> keyCounts.merge(key, 1, Integer::sum)));
            Set<String> maps = validMaps();
            Map<BigInteger, CountyState> states = new LinkedHashMap<>();
            for (var entry : input.projection().titles().entrySet()) {
                SavedMembershipInput.Title title = entry.getValue(); Optional<String> key = text(title.key());
                if (key.isPresent() && (key.orElseThrow().startsWith("b_") || key.orElseThrow().startsWith("d_")
                        || key.orElseThrow().startsWith("k_") || key.orElseThrow().startsWith("e_"))) { continue; }
                boolean geographic = key.isPresent() && key.orElseThrow().startsWith("c_") && maps.contains(key.orElseThrow())
                        && keyCounts.get(key.orElseThrow()) == 1;
                states.put(entry.getKey(), new CountyState(key, geographic ? Geography.KNOWN_COUNTY : Geography.UNKNOWN,
                        realm(entry.getKey()), family(title.holder().integer())));
            }
            List<BigInteger> realmKnown = new ArrayList<>(), realmUnknown = new ArrayList<>();
            List<BigInteger> familyKnown = new ArrayList<>(), familyUnknown = new ArrayList<>();
            for (var entry : states.entrySet()) {
                CountyState state = entry.getValue(); boolean geographic = state.geography() == Geography.KNOWN_COUNTY;
                if (geographic && state.realm().membership() == Truth.YES) { realmKnown.add(entry.getKey()); }
                if (state.realm().membership() != Truth.NO && (!geographic || state.realm().membership() == Truth.UNKNOWN)) {
                    realmUnknown.add(entry.getKey());
                }
                Optional<Factor> factor = state.family().factor();
                if (geographic && factor.isPresent() && factor.orElseThrow() != Factor.ZERO) { familyKnown.add(entry.getKey()); }
                if (!factor.equals(Optional.of(Factor.ZERO)) && (!geographic || factor.isEmpty())) { familyUnknown.add(entry.getKey()); }
            }
            boolean census = input.projection().streamComplete() && input.projection().unknownKeyFields().signum() == 0
                    && input.projection().rootKeys().contains("landed_titles");
            return new SavedMembershipResult(input.sourceRef(), text(input.projection().date()), input.actor(), input.house(), input.dynasty(),
                    census, census && states.values().stream().allMatch(state -> state.geography() == Geography.KNOWN_COUNTY),
                    scope(realmKnown, realmUnknown, census, true),
                    scope(familyKnown, familyUnknown, census, input.house().isPresent() && input.dynasty().isPresent()), states);
        }

        private Set<String> validMaps() {
            Map<String, SavedMembershipInput.MappingRow> rows = input.mapping() instanceof SavedMembershipInput.MappingRows maps
                    ? maps.counties() : Map.of();
            Set<String> valid = new HashSet<>();
            for (var entry : rows.entrySet()) {
                if (!entry.getKey().startsWith("c_") || !(entry.getValue() instanceof SavedMembershipInput.Baronies baronies)
                        || baronies.provinces().isEmpty()) { continue; }
                Set<BigInteger> seen = new HashSet<>(); boolean ready = true;
                for (var barony : baronies.provinces().entrySet()) {
                    if (!barony.getKey().startsWith("b_") || !(barony.getValue() instanceof SavedMembershipInput.ProvinceId province)
                            || province.value().signum() <= 0 || !seen.add(province.value())) { ready = false; break; }
                }
                if (ready) { valid.add(entry.getKey()); }
            }
            Map<BigInteger, Set<String>> provinces = new HashMap<>(); Map<String, Set<String>> baronies = new HashMap<>();
            for (String county : valid) {
                if (!(rows.get(county) instanceof SavedMembershipInput.Baronies mapping)) { throw new IllegalStateException("validated mapping changed"); }
                for (var entry : mapping.provinces().entrySet()) {
                    if (!(entry.getValue() instanceof SavedMembershipInput.ProvinceId province)) { throw new IllegalStateException("validated province changed"); }
                    provinces.computeIfAbsent(province.value(), ignored -> new HashSet<>()).add(county);
                    baronies.computeIfAbsent(entry.getKey(), ignored -> new HashSet<>()).add(county);
                }
            }
            Set<String> conflicted = new HashSet<>();
            provinces.values().stream().filter(owners -> owners.size() > 1).forEach(conflicted::addAll);
            baronies.values().stream().filter(owners -> owners.size() > 1).forEach(conflicted::addAll);
            valid.removeAll(conflicted); return valid;
        }

        private Realm realm(BigInteger identity) {
            List<BigInteger> path = new ArrayList<>(); Set<BigInteger> seen = new HashSet<>(); Realm result;
            while (true) {
                if (realmCache.containsKey(identity)) { result = realmCache.get(identity); break; }
                if (seen.contains(identity)) { result = new Realm(Truth.UNKNOWN, Reason.CYCLIC_DE_FACTO_LIEGE, identity); break; }
                SavedMembershipInput.Title row = input.projection().titles().get(identity);
                if (row == null) { result = new Realm(Truth.UNKNOWN, Reason.MISSING_DE_FACTO_LIEGE_TITLE, identity); break; }
                seen.add(identity); path.add(identity); Optional<BigInteger> holder = row.holder().integer();
                if (row.conflictingHolder() || holder.isEmpty()) { result = new Realm(Truth.UNKNOWN, Reason.TITLE_HOLDER_UNAVAILABLE, identity); break; }
                if (holder.orElseThrow().equals(input.actor())) { result = new Realm(Truth.YES, Reason.HELD_BY_PLAYER_ON_TITLE_CHAIN, identity); break; }
                if (row.conflictingLiege()) { result = new Realm(Truth.UNKNOWN, Reason.CONFLICTING_DE_FACTO_LIEGE, identity); break; }
                if (row.liege() instanceof ScalarField.Missing) { result = new Realm(Truth.NO, Reason.COMPLETE_FOREIGN_TITLE_ROOT, identity); break; }
                Optional<BigInteger> next = row.liege().integer();
                if (next.isEmpty()) { result = new Realm(Truth.UNKNOWN, Reason.INVALID_DE_FACTO_LIEGE, identity); break; }
                identity = next.orElseThrow();
            }
            for (BigInteger node : path) { realmCache.put(node, result); }
            return result;
        }

        private Family family(Optional<BigInteger> holder) {
            if (holder.isEmpty() || input.projection().characterHouseUnknown().contains(holder.orElseThrow())
                    || !input.projection().characterSources().contains(holder.orElseThrow()) || input.house().isEmpty() || input.dynasty().isEmpty()) {
                return unknown(Reason.HOLDER_HOUSE_OR_FOUNDING_ANCHOR_UNAVAILABLE);
            }
            BigInteger start = input.projection().characterHouses().get(holder.orElseThrow());
            if (start == null) { return new Family(Optional.of(Factor.ZERO), Reason.COMPLETE_CHARACTER_WITHOUT_HOUSE); }
            if (familyCache.containsKey(start)) { return familyCache.get(start); }
            BigInteger identity = start; List<BigInteger> path = new ArrayList<>(); Set<BigInteger> seen = new HashSet<>(); Family result;
            while (true) {
                if (familyCache.containsKey(identity)) {
                    result = familyCache.get(identity);
                    if (!path.isEmpty() && result.factor().equals(Optional.of(Factor.ZERO))) { result = unknown(Reason.PARENT_DYNASTY_DISAGREES); }
                    break;
                }
                if (seen.contains(identity)) { result = unknown(Reason.CYCLIC_PARENT_HOUSE); break; }
                SavedMembershipInput.House row = input.projection().houses().get(identity);
                if (row == null) { result = unknown(Reason.MISSING_HOUSE_ON_ANCESTRY); break; }
                seen.add(identity); path.add(identity);
                if (row.conflictingDynasty() || row.conflictingParent()) { result = unknown(Reason.CONFLICTING_HOUSE_ANCESTRY); break; }
                Optional<BigInteger> observedDynasty = row.dynasty().integer();
                if (observedDynasty.isEmpty()) { result = unknown(Reason.HOUSE_DYNASTY_UNAVAILABLE); break; }
                if (!observedDynasty.equals(input.dynasty())) {
                    result = path.size() == 1 ? new Family(Optional.of(Factor.ZERO), Reason.DIFFERENT_DYNASTY)
                            : unknown(Reason.PARENT_DYNASTY_DISAGREES); break;
                }
                if (identity.equals(input.house().orElseThrow())) { result = new Family(Optional.of(Factor.FULL), Reason.FOUNDING_HOUSE_ANCESTRY); break; }
                if (row.parent() instanceof ScalarField.Missing) { result = new Family(Optional.of(Factor.HALF), Reason.COMPLETE_OTHER_HOUSE_ROOT_IN_DYNASTY); break; }
                Optional<BigInteger> parent = row.parent().integer();
                if (parent.isEmpty()) { result = unknown(Reason.INVALID_PARENT_HOUSE); break; }
                identity = parent.orElseThrow();
            }
            // Preserve the producer's start-only cache; do not poison the foreign endpoint.
            familyCache.put(start, result); return result;
        }
    }

    private static Family unknown(Reason reason) { return new Family(Optional.empty(), reason); }
    private static Optional<String> text(ScalarField value) { return value instanceof ScalarField.Text text ? Optional.of(text.value()) : Optional.empty(); }
    private static SavedMembershipResult.Scope scope(List<BigInteger> known, List<BigInteger> unknown, boolean census, boolean ready) {
        List<BigInteger> orderedKnown = known.stream().sorted().toList(), orderedUnknown = unknown.stream().sorted().toList();
        return new SavedMembershipResult.Scope(census && ready && unknown.isEmpty(), orderedKnown, orderedUnknown, known.size(),
                census && ready ? OptionalInt.of(known.size() + unknown.size()) : OptionalInt.empty());
    }
}
