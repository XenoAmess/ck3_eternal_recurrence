package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Locale;
import java.util.Objects;

/** Single typed dispatch for the original 23 source-census and ten current-person extensions. */
public final class BattlePersonExternalCodec {
    private BattlePersonExternalCodec() { }
    public enum Leaf {
        LATER_DIRECT_291C3FB_44C, HELPER_291F0A0, LATER_HELPERS_291F550_291F940,
        TAIL_DIRECT_291C5B7_291CC49, TAIL_PREFIX_2753860_2922530, MIDDLE_HELPERS_291F260_291FB10,
        TRAIT_STAGE_291D460, ABSENT_RECIPIENT_INPUTS, HELPER_2922070, CONFERENCE_24B1D00,
        UNCACHED_RECIPIENT_INPUTS, PROVIDER_BUCKET_291C5B2,
        QUALIFIER_28BC0D0, LIST_PREDICATE_2530DD0, GATED_TEMPORARY_TAIL_291C7A7,
        AFTER_GATED_TAIL_326A8E0_2920310, PROVIDER192_AND2920850, FOLLOWING_2920B50,
        FOLLOWING_2BCA620, FOLLOWING_GOVERNMENT_LAND_312A950, FOLLOWING_2921350,
        FOLLOWING_2921020, FOLLOWING_DIAC_2920D60,
        CARRIER_1C8_B70_DIRECT, FOLLOWING_2921A90, FOLLOWING_2921A90_CONDITIONAL,
        FOLLOWING_2921A90_OPINION, FOLLOWING_2921A90_SCOPE_WEIGHTS, FOLLOWING_2922680,
        FOLLOWING_291CE01_GOVERNMENT_GATE, FOLLOWING_291E3A0_LOCAL_TITLES,
        FOLLOWING_291E3A0_FIRST_TITLE_VECTOR, FOLLOWING_291E3A0_CAPTURED_TAIL;

        public String wire() { return name().toLowerCase(Locale.ROOT); }
        public static Leaf fromWire(String value) {
            for (Leaf leaf : values()) if (leaf.wire().equals(value)) return leaf;
            throw new IllegalArgumentException("unknown original person extension: " + value);
        }
    }
    public static JsonNode normalize(Leaf leaf, JsonNode raw, String field) {
        Objects.requireNonNull(leaf, "typed original person extension required");
        Objects.requireNonNull(field, "original field provenance required");
        JsonNode normalized = switch (leaf) {
            case LATER_DIRECT_291C3FB_44C, HELPER_291F0A0, LATER_HELPERS_291F550_291F940,
                    TAIL_DIRECT_291C5B7_291CC49, TAIL_PREFIX_2753860_2922530, MIDDLE_HELPERS_291F260_291FB10 ->
                    BattlePersonContextPrefixCodec.normalize(leaf, raw, field);
            case TRAIT_STAGE_291D460, ABSENT_RECIPIENT_INPUTS, HELPER_2922070, CONFERENCE_24B1D00,
                    UNCACHED_RECIPIENT_INPUTS, PROVIDER_BUCKET_291C5B2 ->
                    BattlePersonContextEarlyCodec.normalize(leaf, raw, field);
            case QUALIFIER_28BC0D0, LIST_PREDICATE_2530DD0, GATED_TEMPORARY_TAIL_291C7A7,
                    AFTER_GATED_TAIL_326A8E0_2920310, PROVIDER192_AND2920850, FOLLOWING_2920B50,
                    FOLLOWING_2BCA620, FOLLOWING_GOVERNMENT_LAND_312A950, FOLLOWING_2921350,
                    FOLLOWING_2921020, FOLLOWING_DIAC_2920D60 ->
                    BattlePersonContextLateCodec.normalize(leaf, raw, field);
            case CARRIER_1C8_B70_DIRECT, FOLLOWING_2921A90, FOLLOWING_2921A90_CONDITIONAL,
                    FOLLOWING_2921A90_OPINION, FOLLOWING_2921A90_SCOPE_WEIGHTS, FOLLOWING_2922680,
                    FOLLOWING_291CE01_GOVERNMENT_GATE, FOLLOWING_291E3A0_LOCAL_TITLES,
                    FOLLOWING_291E3A0_FIRST_TITLE_VECTOR, FOLLOWING_291E3A0_CAPTURED_TAIL ->
                    BattlePersonCurrentExternalCodec.normalize(leaf, raw, field);
        };
        return Objects.requireNonNull(normalized, "normalizers must preserve explicit null as NullNode");
    }
}
