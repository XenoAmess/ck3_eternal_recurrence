package org.xar.ck3.control.wave2.planning.savedcountymembership;

import java.math.BigInteger;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;

/** Pure three-state membership and source-bound evidence; no current native or SAVE qualification. */
public record SavedMembershipResult(String sourceRef, Optional<String> date, BigInteger actor,
        Optional<BigInteger> house, Optional<BigInteger> dynasty, boolean titleCensusComplete,
        boolean geographyComplete, Scope realm, Scope family, Map<BigInteger, CountyState> states) {
    public SavedMembershipResult {
        Objects.requireNonNull(sourceRef); Objects.requireNonNull(date); Objects.requireNonNull(actor);
        Objects.requireNonNull(house); Objects.requireNonNull(dynasty); Objects.requireNonNull(realm); Objects.requireNonNull(family);
        states = Collections.unmodifiableMap(new LinkedHashMap<>(states));
    }
    public record Scope(boolean complete, List<BigInteger> known, List<BigInteger> unknown,
            int countLower, OptionalInt countUpper) {
        public Scope { known = List.copyOf(known); unknown = List.copyOf(unknown); Objects.requireNonNull(countUpper); }
    }
    public record CountyState(Optional<String> key, Geography geography, Realm realm, Family family) {
        public CountyState { Objects.requireNonNull(key); Objects.requireNonNull(geography); Objects.requireNonNull(realm); Objects.requireNonNull(family); }
    }
    public record Realm(Truth membership, Reason reason, BigInteger terminal) {
        public Realm { Objects.requireNonNull(membership); Objects.requireNonNull(reason); Objects.requireNonNull(terminal); }
    }
    public record Family(Optional<Factor> factor, Reason reason) {
        public Family { Objects.requireNonNull(factor); Objects.requireNonNull(reason); }
    }
    public enum Truth { YES, NO, UNKNOWN }
    public enum Geography { KNOWN_COUNTY, UNKNOWN }
    public enum Factor {
        ZERO("0"), HALF("0.5"), FULL("1");
        private final String lexical;
        Factor(String lexical) { this.lexical = lexical; }
        public String lexical() { return lexical; }
    }
    public enum Reason {
        CYCLIC_DE_FACTO_LIEGE, MISSING_DE_FACTO_LIEGE_TITLE, TITLE_HOLDER_UNAVAILABLE,
        HELD_BY_PLAYER_ON_TITLE_CHAIN, CONFLICTING_DE_FACTO_LIEGE, COMPLETE_FOREIGN_TITLE_ROOT,
        INVALID_DE_FACTO_LIEGE, HOLDER_HOUSE_OR_FOUNDING_ANCHOR_UNAVAILABLE,
        COMPLETE_CHARACTER_WITHOUT_HOUSE, PARENT_DYNASTY_DISAGREES, CYCLIC_PARENT_HOUSE,
        MISSING_HOUSE_ON_ANCESTRY, CONFLICTING_HOUSE_ANCESTRY, HOUSE_DYNASTY_UNAVAILABLE,
        DIFFERENT_DYNASTY, FOUNDING_HOUSE_ANCESTRY, COMPLETE_OTHER_HOUSE_ROOT_IN_DYNASTY,
        INVALID_PARENT_HOUSE;
        public String wire() { return name().toLowerCase(Locale.ROOT); }
    }
}
