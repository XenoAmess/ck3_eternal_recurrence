package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Objects;

/** One installed normalizer for each of the eleven source-input late leaves; no unknown field passthrough. */
public final class BattlePersonContextLateCodec {
    private BattlePersonContextLateCodec() { }
    public static JsonNode normalize(BattlePersonExternalCodec.Leaf leaf,JsonNode raw,String field) {
        Objects.requireNonNull(leaf);Objects.requireNonNull(field);
        return switch(leaf) {
            case QUALIFIER_28BC0D0 -> BattlePersonQualifierCodec.normalize(raw,field);
            case LIST_PREDICATE_2530DD0 -> BattlePersonListPredicateCodec.normalize(raw,field);
            case GATED_TEMPORARY_TAIL_291C7A7 -> BattlePersonGatedCodec.normalize(raw,field);
            case AFTER_GATED_TAIL_326A8E0_2920310 -> BattlePersonAfterGatedCodec.normalize(raw,field);
            case PROVIDER192_AND2920850 -> BattlePersonProviderListsCodec.normalize(raw,field);
            case FOLLOWING_2920B50 -> BattlePersonRankedCodec.normalize(raw,field);
            case FOLLOWING_2BCA620 -> BattlePersonBalanceCodec.normalize(raw,field);
            case FOLLOWING_GOVERNMENT_LAND_312A950 -> BattlePersonLandCodec.normalize(raw,field);
            case FOLLOWING_2921350 -> BattlePersonProvinceCodec.normalize(raw,field);
            case FOLLOWING_2921020 -> BattlePersonLegacyCodec.normalize(raw,field);
            case FOLLOWING_DIAC_2920D60 -> BattlePersonDiacCodec.normalize(raw,field);
            default -> throw new IllegalArgumentException("late source-input owner does not own leaf: "+leaf.wire());
        };
    }
}
