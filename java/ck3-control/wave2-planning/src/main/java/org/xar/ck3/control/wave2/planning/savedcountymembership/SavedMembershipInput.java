package org.xar.ck3.control.wave2.planning.savedcountymembership;

import java.math.BigInteger;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.planning.scoretarget.ScalarField;

/** Declared immutable projection of the actual SaveProjection membership dependency closure. */
public record SavedMembershipInput(BigInteger actor, Optional<BigInteger> house,
        Optional<BigInteger> dynasty, String sourceRef, SavedProjection projection, CountyMapping mapping) {
    public SavedMembershipInput {
        Objects.requireNonNull(actor); Objects.requireNonNull(house); Objects.requireNonNull(dynasty);
        StrictJson.text(sourceRef); Objects.requireNonNull(projection); Objects.requireNonNull(mapping);
    }

    public record SavedProjection(Map<BigInteger, Title> titles, Map<BigInteger, House> houses,
            Map<BigInteger, BigInteger> characterHouses, Set<BigInteger> characterHouseUnknown,
            Set<BigInteger> characterSources, boolean streamComplete, BigInteger unknownKeyFields,
            List<String> rootKeys, ScalarField date) {
        public SavedProjection {
            // Stream order affects the original cache terminal proof; Map.copyOf is not sufficient.
            titles = ordered(titles); houses = ordered(houses); characterHouses = ordered(characterHouses);
            characterHouseUnknown = Set.copyOf(characterHouseUnknown); characterSources = Set.copyOf(characterSources);
            Objects.requireNonNull(unknownKeyFields);
            StrictJson.require(unknownKeyFields.signum() >= 0, "nonnegative unknown field count required");
            rootKeys = List.copyOf(rootKeys); Objects.requireNonNull(date);
        }
    }
    public record Title(ScalarField key, ScalarField holder, ScalarField liege,
            boolean conflictingHolder, boolean conflictingLiege) {
        public Title { Objects.requireNonNull(key); Objects.requireNonNull(holder); Objects.requireNonNull(liege); }
    }
    public record House(ScalarField dynasty, ScalarField parent, boolean conflictingDynasty, boolean conflictingParent) {
        public House { Objects.requireNonNull(dynasty); Objects.requireNonNull(parent); }
    }
    public sealed interface CountyMapping permits MappingRows, UnavailableMapping { }
    public record MappingRows(Map<String, MappingRow> counties) implements CountyMapping {
        public MappingRows { counties = ordered(counties); }
    }
    public record UnavailableMapping(UnavailableKind kind) implements CountyMapping {
        public UnavailableMapping { Objects.requireNonNull(kind); }
    }
    public enum UnavailableKind { NULL, BOOLEAN, INTEGER, FRACTIONAL, STRING, ARRAY, OBJECT }
    public sealed interface MappingRow permits Baronies, InvalidMappingRow { }
    public record Baronies(Map<String, Province> provinces) implements MappingRow {
        public Baronies { provinces = ordered(provinces); }
    }
    public record InvalidMappingRow(UnavailableKind kind) implements MappingRow {
        public InvalidMappingRow { Objects.requireNonNull(kind); }
    }
    public sealed interface Province permits ProvinceId, InvalidProvince { }
    public record ProvinceId(BigInteger value) implements Province {
        public ProvinceId { Objects.requireNonNull(value); }
    }
    public record InvalidProvince(UnavailableKind kind) implements Province {
        public InvalidProvince { Objects.requireNonNull(kind); }
    }

    private static <K, V> Map<K, V> ordered(Map<K, V> source) {
        Map<K, V> result = new LinkedHashMap<>();
        source.forEach((key, value) -> result.put(Objects.requireNonNull(key), Objects.requireNonNull(value)));
        return Collections.unmodifiableMap(result);
    }
}
