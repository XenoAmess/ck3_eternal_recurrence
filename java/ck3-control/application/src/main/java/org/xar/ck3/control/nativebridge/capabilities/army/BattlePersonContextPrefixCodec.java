package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** Strict current PERSON source operands. No emitter, model rebuild, append or native authority. */
public final class BattlePersonContextPrefixCodec {
    private static final BigInteger GOVERNMENT_MAGIC = new BigInteger("4744624f", 16);
    private static final BigInteger SUBC_MAGIC = new BigInteger("5362436f", 16);
    private static final String MAPPING = "first_full_id_10_mapping";
    private static final String DEFAULT_550 = "inline_culture_mapped_default_5dc2380";
    private static final String DEFAULT_940 = "inline_nested_mapped_default_5dc21b0";
    private static final String[] FAMILIES_0A0 = {"primary_direct", "manager_range", "source_a18", "conditional_direct"};
    private static final String[] FAMILIES_550 = {"government_indexed", "culture_direct", "culture_mapped"};
    private static final String[] FAMILIES_FB10 = {"preferred", "list_218", "list_248"};
    private static final String[] RITE_SELECTIONS = {"first_selection", "second_selection", "third_selection"};
    private BattlePersonContextPrefixCodec() { }

    public static JsonNode normalize(BattlePersonExternalCodec.Leaf leaf, JsonNode raw, String field) {
        Objects.requireNonNull(leaf); require(raw != null, field, "explicit native JSON value required");
        require(Set.of(BattlePersonExternalCodec.Leaf.LATER_DIRECT_291C3FB_44C, BattlePersonExternalCodec.Leaf.HELPER_291F0A0,
                BattlePersonExternalCodec.Leaf.LATER_HELPERS_291F550_291F940, BattlePersonExternalCodec.Leaf.TAIL_DIRECT_291C5B7_291CC49,
                BattlePersonExternalCodec.Leaf.TAIL_PREFIX_2753860_2922530, BattlePersonExternalCodec.Leaf.MIDDLE_HELPERS_291F260_291FB10).contains(leaf),
                field, "leaf belongs to another unique PERSON codec");
        if (nil(raw)) return NullNode.instance;
        return switch (leaf) {
            case LATER_DIRECT_291C3FB_44C -> laterDirect(raw, field);
            case HELPER_291F0A0 -> helper0a0(raw, field);
            case LATER_HELPERS_291F550_291F940 -> laterHelpers(raw, field);
            case TAIL_DIRECT_291C5B7_291CC49 -> tailDirect(raw, field);
            case TAIL_PREFIX_2753860_2922530 -> tailPrefix(raw, field);
            case MIDDLE_HELPERS_291F260_291FB10 -> middleHelpers(raw, field);
            default -> throw bad(field, "leaf belongs to another unique PERSON codec");
        };
    }

    private static ObjectNode laterDirect(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "ordered_header_selection", "ordered_count",
                "ordered_array_present", "ordered_rows", "guarded_selection", "guarded_magic_raw", "guarded_admitted", "guarded_property_block", "reason");
        requiredNumber(r, f, "character_id", 32, false);
        words(r, f, 32, false, "ordered_count"); bools(r, f, "ordered_array_present", "guarded_admitted");
        selection(r, f, "ordered_header_selection", "character_1b0_inline_98", "inline_static_545a3e8");
        selection(r, f, "guarded_selection", "character_1c0_pointer_388", "native_fallback");
        words(r, f, 32, true, "guarded_magic_raw"); propertiesField(r, f, "guarded_property_block");
        r.set("ordered_rows", indexed(r.get("ordered_rows"), f + ".ordered_rows", (value, name, index) -> {
            ObjectNode row = plain(value, name, "native_index", "requested_full_id_raw", "selection", "selected_identity",
                    "selected_field_24c_raw", "admitted", "property_block", "reason");
            index(row, name, index); words(row, name, 32, false, "requested_full_id_raw", "selected_field_24c_raw");
            selection(row, name, "selection", "registry_full_id", "native_fallback"); strings(row, name, "selected_identity", "reason");
            bools(row, name, "admitted"); propertiesField(row, name, "property_block");
            require(Objects.equals(b(row, "admitted"), nonzero(n(row, "selected_field_24c_raw"))), name, "signed32 admission differs");
            require(yes(row, "admitted") || nil(row.get("property_block")), name, "undemanded +80 property"); return row;
        }));
        require(Objects.equals(b(r, "guarded_admitted"), equalWhenKnown(n(r, "guarded_magic_raw"), GOVERNMENT_MAGIC)), f, "guarded magic admission differs");
        require(yes(r, "guarded_admitted") || nil(r.get("guarded_property_block")), f, "undemanded +AA0 property");
        JsonNode rows = r.get("ordered_rows"); BigInteger count = n(r, "ordered_count");
        boolean ordered = present(r, "ordered_header_selection") && nonnegative(count) && present(r, "ordered_array_present")
                && sizeEquals(rows, count) && (zero(count) || yes(r, "ordered_array_present"));
        if (ordered) ordered = all(rows, row -> allPresent(row, "requested_full_id_raw", "selection", "selected_identity", "admitted")
                && nil(row.get("reason")) && (!yes(row, "admitted") || propertiesReady(row.get("property_block"))));
        complete(r, ordered && present(r, "guarded_selection") && present(r, "guarded_admitted")
                && (!yes(r, "guarded_admitted") || propertiesReady(r.get("guarded_property_block"))), f); return r;
    }

    private static ObjectNode helper0a0(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "first_selection", "manager_definition_selection",
                "manager_definition_identity", "recipient_source", "range_selection", "first_key_b4_raw", "range_count_raw", "range_native_index",
                "default_pc_guard_raw", "pointer_list_guard_raw", "predicate_character_15c_raw", "predicate_first_key_b4_raw",
                "predicate_second_key_4b8_raw", "predicate_second_a0_raw", "recipient_q64", "range_lower_q64", "range_upper_q64",
                "manager_present", "predicate_admitted", "primary_direct", "manager_range", "source_a18", "conditional_direct", "reason");
        requiredNumber(r, f, "character_id", 32, false); bools(r, f, "manager_present", "predicate_admitted");
        strings(r, f, "first_selection", "manager_definition_selection", "manager_definition_identity", "recipient_source", "range_selection");
        words(r, f, 32, false, "first_key_b4_raw", "range_count_raw", "range_native_index", "default_pc_guard_raw", "pointer_list_guard_raw",
                "predicate_character_15c_raw", "predicate_first_key_b4_raw", "predicate_second_key_4b8_raw", "predicate_second_a0_raw");
        words(r, f, 64, false, "recipient_q64", "range_lower_q64", "range_upper_q64");
        for (String family : FAMILIES_0A0) r.set(family, family0a0(r.get(family), f + "." + family, family));
        BigInteger character = n(r, "predicate_character_15c_raw"), second = n(r, "predicate_second_a0_raw");
        Boolean predicate = minusOne(character) ? Boolean.FALSE : equalWhenKnown(character, second);
        require(Objects.equals(b(r, "predicate_admitted"), predicate), f, "exact DWORD predicate differs");
        if (minusOne(character)) undemanded(r, f, "predicate_first_key_b4_raw", "predicate_second_key_4b8_raw", "predicate_second_a0_raw");
        require(Objects.equals(b(r.get("conditional_direct"), "admitted"), predicate), f, "conditional family native AL differs");
        complete(r, familiesReady(r, FAMILIES_0A0), f);
        require(!no(r, "manager_present") || !yes(r.get("manager_range"), "ready"), f, "lazy null manager cannot provide ready range");
        if ("absent_1c8_2bfac30_unobserved".equals(s(r, "recipient_source")))
            require(nil(r.get("recipient_q64")) && !yes(r.get("manager_range"), "ready"), f, "absent recipient cannot be established");
        return r;
    }
    private static ObjectNode family0a0(JsonNode raw, String f, String family) {
        ObjectNode r = available(raw, f, "status", "ready", "selected_source", "admitted", "count", "array_present", "rows", "reason");
        r.set("selected_source", text(r.get("selected_source"), f + ".selected_source", false, true));
        bools(r, f, "admitted", "array_present"); words(r, f, 32, false, "count");
        r.set("rows", indexed(r.get("rows"), f + ".rows", (value, name, ordinal) -> {
            ObjectNode row = plain(value, name, "native_index", "source_identity", "gate_raw", "admitted", "property_block", "reason");
            index(row, name, ordinal); strings(row, name, "source_identity", "reason"); words(row, name, 32, false, "gate_raw");
            bools(row, name, "admitted"); propertiesField(row, name, "property_block");
            if (family.equals("manager_range") || family.equals("source_a18"))
                require(Objects.equals(b(row, "admitted"), nonzero(n(row, "gate_raw"))), name, "native nonzero gate differs");
            else require(nil(row.get("gate_raw")) && !no(row, "admitted"), name, "direct PC has no additional gate");
            require(yes(row, "admitted") || nil(row.get("property_block")), name, "undemanded PC"); return row;
        }));
        JsonNode rows = r.get("rows"); BigInteger count = n(r, "count"); boolean done;
        if (no(r, "admitted")) done = nil(r.get("count")) && nil(r.get("array_present")) && empty(rows);
        else if (family.equals("manager_range")) done = yes(r, "admitted") && sizeEquals(rows, BigInteger.ONE)
                && count != null && Objects.equals(n(rows.get(0), "gate_raw"), count) && nil(r.get("array_present"));
        else done = yes(r, "admitted") && nonnegative(count) && present(r, "array_present") && sizeEquals(rows, count)
                && (zero(count) || yes(r, "array_present"));
        if (done && yes(r, "admitted")) done = all(rows, row -> allPresent(row, "source_identity", "admitted")
                && nil(row.get("reason")) && (!yes(row, "admitted") || propertiesReady(row.get("property_block"))));
        complete(r, done && nil(r.get("reason")), f); return r;
    }

    private enum FamilyKind { GOVERNMENT, DIRECT, MAPPED }
    static ObjectNode rite(JsonNode raw, String f) {
        ObjectNode r = plain(raw, f, "first_key_b4_raw", "second_key_4b8_raw", "third_key_98_raw", "first_selection", "second_selection",
                "third_selection", "selected_identity", "membership_count", "membership_array_present", "membership_identities", "reason");
        words(r, f, 32, false, "first_key_b4_raw", "second_key_4b8_raw", "third_key_98_raw", "membership_count");
        strings(r, f, "selected_identity", "reason"); bools(r, f, "membership_array_present");
        for (String key : RITE_SELECTIONS) selection(r, f, key, "registry_full_id_8", "native_fallback");
        r.set("membership_identities", array(r.get("membership_identities"), f + ".membership_identities", true,
                (item, name) -> text(item, name, false, true))); return r;
    }
    static boolean membershipReady(JsonNode r) {
        BigInteger count = n(r, "membership_count");
        return nil(r.get("reason")) && present(r, "selected_identity") && allPresent(r, RITE_SELECTIONS)
                && nonnegative(count) && present(r, "membership_array_present") && sizeEquals(r.get("membership_identities"), count)
                && (zero(count) || yes(r, "membership_array_present"));
    }
    static ObjectNode mappedFamily(JsonNode raw, String field, JsonNode normalizedRite, String defaultSelection, BigInteger guard) {
        return family(raw, field, FamilyKind.MAPPED, normalizedRite, defaultSelection, guard);
    }
    private static ObjectNode mappedRow(JsonNode raw, String f, FamilyKind kind, String fallback) {
        ObjectNode r = plain(raw, f, "native_index", "source_identity", "key_identity", "key_magic_raw", "key_full_id_raw", "admitted",
                "property_selection", "mapping_native_index", "property_identity", "property_block", "reason");
        requiredNumber(r, f, "native_index", 32, false); words(r, f, 32, true, "key_magic_raw");
        words(r, f, 32, false, "key_full_id_raw", "mapping_native_index"); bools(r, f, "admitted");
        strings(r, f, "source_identity", "key_identity", "property_identity", "reason"); propertiesField(r, f, "property_block");
        if (kind == FamilyKind.MAPPED) selection(r, f, "property_selection", MAPPING, fallback);
        else if (kind == FamilyKind.GOVERNMENT) selection(r, f, "property_selection", "government_indexed_1c0", "inline_government_default_5d65890");
        else selection(r, f, "property_selection", "direct_pc_pointer");
        if (kind != FamilyKind.MAPPED) {
            undemanded(r, f, "key_identity", "key_magic_raw", "key_full_id_raw", "mapping_native_index");
            require(!no(r, "admitted"), f, "direct PC has no additional admission gate");
        } else if (!yes(r, "admitted")) undemanded(r, f, "key_magic_raw", "key_full_id_raw", "mapping_native_index", "property_selection", "property_identity", "property_block");
        else if (MAPPING.equals(s(r, "property_selection"))) require(GOVERNMENT_MAGIC.equals(n(r, "key_magic_raw"))
                && allPresent(r, "key_full_id_raw", "mapping_native_index"), f, "mapping requires consumed full ID and index");
        require(yes(r, "admitted") || nil(r.get("property_block")), f, "undemanded PC"); return r;
    }
    private static ObjectNode family(JsonNode raw, String f, FamilyKind kind, JsonNode rite, String fallback, BigInteger guard) {
        ObjectNode r = available(raw, f, "status", "ready", "admitted", "count", "array_present", "rows", "reason");
        bools(r, f, "admitted", "array_present"); words(r, f, 32, false, "count");
        r.set("rows", indexed(r.get("rows"), f + ".rows", (item, name, ordinal) -> {
            ObjectNode row = mappedRow(item, name, kind, fallback); require(n(row, "native_index").equals(BigInteger.valueOf(ordinal)), name, "native row order differs"); return row;
        }));
        JsonNode rows = r.get("rows"); BigInteger count = n(r, "count");
        if (!nil(rows)) for (JsonNode row : rows) {
            BigInteger mapped = n(row, "mapping_native_index");
            if (mapped != null) {
                require(count != null && mapped.signum() >= 0 && mapped.compareTo(count) < 0, f, "mapping index outside native count");
                if (mapped.compareTo(BigInteger.valueOf(rows.size())) < 0) {
                    BigInteger selected = n(rows.get(mapped.intValueExact()), "key_full_id_raw");
                    require(selected == null || selected.equals(n(row, "key_full_id_raw")), f, "mapped full ID differs");
                }
            }
            if (kind == FamilyKind.MAPPED && membershipReady(rite) && present(row, "key_identity")) {
                boolean found = false; for (JsonNode id : rite.get("membership_identities")) if (s(row, "key_identity").equals(id.textValue())) found = true;
                require(Objects.equals(b(row, "admitted"), found), f, "whole QWORD membership admission differs");
            }
        }
        boolean done;
        if (no(r, "admitted")) done = nil(r.get("count")) && nil(r.get("array_present")) && empty(rows);
        else if (kind == FamilyKind.GOVERNMENT) done = yes(r, "admitted") && BigInteger.ONE.equals(count) && nil(r.get("array_present")) && sizeEquals(rows, BigInteger.ONE);
        else done = yes(r, "admitted") && nonnegative(count) && present(r, "array_present") && sizeEquals(rows, count) && (zero(count) || yes(r, "array_present"));
        if (done && yes(r, "admitted")) {
            done = all(rows, row -> allPresent(row, "source_identity", "admitted") && nil(row.get("reason"))
                    && (kind != FamilyKind.MAPPED || present(row, "key_identity"))
                    && (!yes(row, "admitted") || (allPresent(row, "property_selection", "property_identity") && pc(row.get("property_block"))
                        && (kind != FamilyKind.MAPPED || (present(row, "key_magic_raw") && guard != null))
                        && (!(Objects.equals(s(row, "property_selection"), fallback) || "inline_government_default_5d65890".equals(s(row, "property_selection")))
                            || goodGuard(guard)))));
            if (kind == FamilyKind.MAPPED && positive(count)) done = done && membershipReady(rite);
        }
        complete(r, done && nil(r.get("reason")), f); return r;
    }

    private static ObjectNode laterHelpers(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "helper_291f550", "helper_291f940", "reason");
        requiredNumber(r, f, "character_id", 32, false); r.set("helper_291f550", helper550(r.get("helper_291f550"), f + ".helper_291f550"));
        r.set("helper_291f940", helper940(r.get("helper_291f940"), f + ".helper_291f940"));
        complete(r, yes(r.get("helper_291f550"), "ready") && yes(r.get("helper_291f940"), "ready"), f); return r;
    }
    private static ObjectNode helper550(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "culture_selection", "culture_identity", "government_selection", "government_identity",
                "culture_key_b0_raw", "culture_full_id_raw", "government_full_id_raw", "government_default_guard_raw", "mapped_default_guard_raw",
                "culture_magic_raw", "government_magic_raw", "admitted", "rite", "government_indexed", "culture_direct", "culture_mapped", "reason");
        strings(r, f, "culture_selection", "culture_identity", "government_selection", "government_identity");
        words(r, f, 32, false, "culture_key_b0_raw", "culture_full_id_raw", "government_full_id_raw", "government_default_guard_raw", "mapped_default_guard_raw");
        words(r, f, 32, true, "culture_magic_raw", "government_magic_raw"); bools(r, f, "admitted");
        BigInteger magic = n(r, "culture_magic_raw"), id = n(r, "culture_full_id_raw");
        Boolean admitted = magic == null ? null : !magic.equals(new BigInteger("43756c74", 16)) ? Boolean.FALSE : id == null ? null : !minusOne(id);
        require(Objects.equals(b(r, "admitted"), admitted), f, "Culture admission differs");
        r.set("rite", rite(r.get("rite"), f + ".rite"));
        for (int i = 0; i < FAMILIES_550.length; i++) {
            String name = FAMILIES_550[i]; FamilyKind kind = FamilyKind.values()[i];
            BigInteger guard = n(r, kind == FamilyKind.GOVERNMENT ? "government_default_guard_raw" : "mapped_default_guard_raw");
            r.set(name, family(r.get(name), f + "." + name, kind, r.get("rite"), DEFAULT_550, guard));
            require(Objects.equals(b(r.get(name), "admitted"), admitted), f, "family differs from Culture admission");
        }
        if (Boolean.FALSE.equals(admitted)) {
            undemanded(r, f, "government_selection", "government_identity", "government_magic_raw", "government_full_id_raw", "government_default_guard_raw", "mapped_default_guard_raw");
            for (JsonNode operand : r.get("rite")) require(nil(operand), f, "skipped Culture has undemanded rite operand");
        }
        complete(r, allPresent(r, "culture_selection", "culture_identity") && admitted != null && familiesReady(r, FAMILIES_550), f); return r;
    }
    private static ObjectNode helper940(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "direct_ready", "mapped_ready", "first_key_158_raw", "first_selection", "second_key_2c_raw",
                "second_selection", "selected_identity", "outer_count", "outer_array_present", "outer_rows", "mapped_default_guard_raw", "rite", "reason");
        requiredBool(r, f, "direct_ready", "mapped_ready"); bools(r, f, "outer_array_present");
        words(r, f, 32, false, "first_key_158_raw", "second_key_2c_raw", "outer_count", "mapped_default_guard_raw");
        strings(r, f, "first_selection", "second_selection", "selected_identity"); r.set("rite", rite(r.get("rite"), f + ".rite"));
        r.set("outer_rows", indexed(r.get("outer_rows"), f + ".outer_rows", (value, name, ordinal) -> {
            ObjectNode row = plain(value, name, "native_index", "source_identity", "direct_gate_raw", "direct_admitted", "direct_property_identity",
                    "direct_property_block", "direct_reason", "inner_mapped"); index(row, name, ordinal);
            words(row, name, 32, false, "direct_gate_raw"); bools(row, name, "direct_admitted");
            strings(row, name, "source_identity", "direct_property_identity", "direct_reason"); propertiesField(row, name, "direct_property_block");
            require(Objects.equals(b(row, "direct_admitted"), nonzero(n(row, "direct_gate_raw"))), name, "direct signed32 gate differs");
            if (!yes(row, "direct_admitted")) undemanded(row, name, "direct_property_identity", "direct_property_block");
            row.set("inner_mapped", mappedFamily(row.get("inner_mapped"), name + ".inner_mapped", r.get("rite"), DEFAULT_940, n(r, "mapped_default_guard_raw"))); return row;
        }));
        BigInteger count = n(r, "outer_count"); JsonNode rows = r.get("outer_rows");
        boolean header = allPresent(r, "first_selection", "second_selection", "selected_identity", "outer_array_present") && nonnegative(count)
                && sizeEquals(rows, count) && (zero(count) || yes(r, "outer_array_present"));
        boolean direct = header && all(rows, row -> allPresent(row, "source_identity", "direct_admitted") && nil(row.get("direct_reason"))
                && (!yes(row, "direct_admitted") || (present(row, "direct_property_identity") && pc(row.get("direct_property_block")))));
        boolean mapped = header && all(rows, row -> present(row, "source_identity") && yes(row.get("inner_mapped"), "ready"));
        require(yes(r, "direct_ready") == direct && yes(r, "mapped_ready") == mapped, f, "independent direct/mapped availability differs");
        complete(r, direct && mapped, f); return r;
    }

    private static ObjectNode tailDirect(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "government_870_a30", "carrier_weighted630", "reason");
        requiredNumber(r, f, "character_id", 32, false); r.set("government_870_a30", government(r.get("government_870_a30"), f + ".government_870_a30"));
        r.set("carrier_weighted630", weighted(r.get("carrier_weighted630"), f + ".carrier_weighted630"));
        complete(r, yes(r.get("government_870_a30"), "ready") && yes(r.get("carrier_weighted630"), "ready"), f); return r;
    }
    private static ObjectNode government(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "land_present", "government_selection", "government_identity", "government_magic_raw", "admitted",
                "property_870_identity", "property_870", "second_land_present", "subcarrier_magic_raw", "subcarrier_full_id_raw",
                "additional_a30_admitted", "property_a30_identity", "property_a30", "reason");
        bools(r, f, "land_present", "admitted", "second_land_present", "additional_a30_admitted");
        strings(r, f, "government_identity", "property_870_identity", "property_a30_identity");
        selection(r, f, "government_selection", "character_death_1d0_88", "character_land_1c0_3f8", "native_government_fallback");
        words(r, f, 32, true, "government_magic_raw", "subcarrier_magic_raw"); words(r, f, 32, false, "subcarrier_full_id_raw");
        propertiesField(r, f, "property_870", "property_a30");
        BigInteger magic = n(r, "government_magic_raw"); Boolean admitted = no(r, "land_present") ? Boolean.FALSE
                : yes(r, "land_present") && magic != null ? magic.equals(GOVERNMENT_MAGIC) : null;
        require(Objects.equals(b(r, "admitted"), admitted), f, "native land/magic gate differs");
        if (!yes(r, "land_present")) undemanded(r, f, "government_selection", "government_identity", "government_magic_raw");
        require(!present(r, "government_identity") || present(r, "government_selection"), f, "selected government lacks selection");
        require(magic == null || present(r, "government_identity"), f, "magic lacks selected identity");
        if (!Boolean.TRUE.equals(admitted)) undemanded(r, f, "property_870_identity", "property_870", "second_land_present", "subcarrier_magic_raw",
                "subcarrier_full_id_raw", "additional_a30_admitted", "property_a30_identity", "property_a30");
        else {
            BigInteger submagic = n(r, "subcarrier_magic_raw"), id = n(r, "subcarrier_full_id_raw");
            Boolean additional = no(r, "second_land_present") ? Boolean.FALSE : null;
            if (yes(r, "second_land_present") && submagic != null) additional = !submagic.equals(SUBC_MAGIC) ? Boolean.TRUE : id == null ? null : minusOne(id);
            require(Objects.equals(b(r, "additional_a30_admitted"), additional), f, "subcarrier gate differs");
            if (!yes(r, "second_land_present")) undemanded(r, f, "subcarrier_magic_raw", "subcarrier_full_id_raw");
            if (!SUBC_MAGIC.equals(submagic)) undemanded(r, f, "subcarrier_full_id_raw");
            if (!Boolean.TRUE.equals(additional)) undemanded(r, f, "property_a30_identity", "property_a30");
        }
        boolean done = Boolean.FALSE.equals(admitted);
        if (Boolean.TRUE.equals(admitted)) done = present(r, "property_870_identity") && pc(r.get("property_870"))
                && present(r, "additional_a30_admitted") && (!yes(r, "additional_a30_admitted") || (present(r, "property_a30_identity") && pc(r.get("property_a30"))));
        complete(r, done && nil(r.get("reason")), f); return r;
    }
    private static ObjectNode weighted(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "carrier_present", "key_274_raw", "selection", "selected_identity", "count_63c", "array_present", "rows", "reason");
        bools(r, f, "carrier_present", "array_present"); words(r, f, 32, false, "key_274_raw", "count_63c");
        strings(r, f, "selected_identity"); selection(r, f, "selection", "registry_full_id_8", "native_fallback");
        r.set("rows", indexed(r.get("rows"), f + ".rows", (value, name, ordinal) -> {
            ObjectNode row = plain(value, name, "native_index", "property_identity", "property_block", "weight_q64", "reason");
            index(row, name, ordinal); strings(row, name, "property_identity", "reason"); propertiesField(row, name, "property_block"); words(row, name, 64, false, "weight_q64");
            require(present(row, "property_identity") == present(row, "property_block"), name, "PC identity and block differ");
            require(nil(row.get("reason")) == (present(row, "weight_q64") && pc(row.get("property_block"))), name, "row availability differs"); return row;
        }));
        BigInteger key = n(r, "key_274_raw"); JsonNode rows = r.get("rows");
        boolean skipped = no(r, "carrier_present") || (yes(r, "carrier_present") && minusOne(key));
        if (!yes(r, "carrier_present")) undemanded(r, f, "key_274_raw");
        if (!yes(r, "carrier_present") || key == null || minusOne(key)) {
            undemanded(r, f, "selection", "selected_identity", "count_63c", "array_present");
            require(skipped ? empty(rows) : nil(rows), f, "skipped/unobserved carrier rows differ");
        } else {
            BigInteger count = n(r, "count_63c");
            require(!present(r, "selected_identity") || present(r, "selection"), f, "selected carrier lacks selection");
            if (!present(r, "selected_identity")) undemanded(r, f, "count_63c", "array_present");
            if (count == null || count.signum() <= 0) {
                undemanded(r, f, "array_present"); require(zero(count) ? empty(rows) : nil(rows), f, "zero/unavailable native count rows differ");
            } else if (!yes(r, "array_present")) require(nil(rows), f, "unavailable array contains rows");
            else require(sizeEquals(rows, count), f, "rows differ from native count63c");
        }
        BigInteger count = n(r, "count_63c"); boolean selected = allPresent(r, "selection", "selected_identity");
        boolean done = skipped || (selected && zero(count));
        if (selected && positive(count) && yes(r, "array_present") && !nil(rows)) done = all(rows, row -> nil(row.get("reason")));
        complete(r, done && nil(r.get("reason")), f); return r;
    }

    private static ObjectNode tailPrefix(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "helper_2753860", "helper_2922530", "reason");
        requiredNumber(r, f, "character_id", 32, false); r.set("helper_2753860", helper275(r.get("helper_2753860"), f + ".helper_2753860"));
        r.set("helper_2922530", helper2530(r.get("helper_2922530"), f + ".helper_2922530"));
        complete(r, yes(r.get("helper_2753860"), "ready") && yes(r.get("helper_2922530"), "ready"), f); return r;
    }
    private static ObjectNode helper275(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "first_key_158_raw", "land_field_1f8_raw", "owner_key_1e0_raw", "owner_id_160_raw",
                "character_id_18_raw", "initial_relation_key_c8_raw", "last_character_id_18_raw", "caller_gate_218_raw", "caller_gate_218_recheck_raw",
                "government_mode_80c_raw", "first_selection", "first_identity", "definition_identity", "definition_pointer_260_identity", "government_selection",
                "government_identity", "predicate_pointer_selection", "predicate_pointer_identity", "owner_selection", "owner_identity", "initial_relation_selection",
                "initial_relation_identity", "property_identity", "caller_admitted", "character_land_present", "predicate_admitted", "owner_admitted",
                "relation_rows", "property_block", "reason");
        words(r, f, 32, false, "first_key_158_raw", "land_field_1f8_raw", "owner_key_1e0_raw", "owner_id_160_raw", "character_id_18_raw",
                "initial_relation_key_c8_raw", "last_character_id_18_raw");
        words(r, f, 8, true, "caller_gate_218_raw", "caller_gate_218_recheck_raw", "government_mode_80c_raw");
        strings(r, f, "first_selection", "first_identity", "definition_identity", "definition_pointer_260_identity", "government_selection", "government_identity",
                "predicate_pointer_selection", "predicate_pointer_identity", "owner_selection", "owner_identity", "initial_relation_selection", "initial_relation_identity", "property_identity");
        bools(r, f, "caller_admitted", "character_land_present", "predicate_admitted", "owner_admitted"); propertiesField(r, f, "property_block");
        r.set("relation_rows", indexed(r.get("relation_rows"), f + ".relation_rows", (value, name, ordinal) -> {
            ObjectNode row = plain(value, name, "native_index", "character_identity", "magic_1c_raw", "character_id_18_raw", "accepted", "next_selection", "next_key_c8_raw", "next_identity", "reason");
            index(row, name, ordinal); words(row, name, 32, true, "magic_1c_raw"); words(row, name, 32, false, "character_id_18_raw", "next_key_c8_raw");
            strings(row, name, "character_identity", "next_selection", "next_identity", "reason"); bools(row, name, "accepted");
            BigInteger magic = n(row, "magic_1c_raw"), word = n(row, "character_id_18_raw");
            Boolean admitted = magic == null ? null : !magic.equals(new BigInteger("43686172", 16)) ? Boolean.FALSE : word == null ? null : !minusOne(word);
            require(Objects.equals(b(row, "accepted"), admitted), name, "Character relation magic/full ID admission differs"); return row;
        }));
        Boolean caller = nonzero(n(r, "caller_gate_218_raw")); require(Objects.equals(b(r, "caller_admitted"), caller), f, "BYTE218 caller gate differs");
        BigInteger sentinel = n(r, "land_field_1f8_raw"); String a = s(r, "definition_pointer_260_identity"), z = s(r, "predicate_pointer_identity");
        Boolean predicate = no(r, "character_land_present") || minusOne(sentinel) ? Boolean.FALSE
                : yes(r, "character_land_present") && sentinel != null && a != null && z != null ? a.equals(z) : null;
        if (Boolean.TRUE.equals(caller)) require(Objects.equals(b(r, "predicate_admitted"), predicate), f, "pointer predicate differs");
        if (present(r, "predicate_pointer_selection")) {
            BigInteger mode = n(r, "government_mode_80c_raw"); String expected = BigInteger.TWO.equals(mode) ? "government_800" : "native_default_5d26d50";
            require(mode != null && expected.equals(s(r, "predicate_pointer_selection")), f, "government BYTE80C pointer selection differs");
        }
        BigInteger owner = n(r, "owner_id_160_raw"), actor = n(r, "character_id_18_raw"), finalId = n(r, "last_character_id_18_raw");
        Boolean ownerAdmission = owner != null && actor != null && owner.equals(actor) ? Boolean.TRUE : equalWhenKnown(owner, finalId);
        if (Boolean.TRUE.equals(predicate)) require(Objects.equals(b(r, "owner_admitted"), ownerAdmission), f, "direct/final Character owner admission differs");
        if (!yes(r, "owner_admitted")) undemanded(r, f, "property_identity", "property_block");
        boolean done = nil(r.get("reason")) && allPresent(r, "first_key_158_raw", "first_selection", "first_identity") && caller != null;
        if (done && Boolean.TRUE.equals(caller)) {
            done = present(r, "caller_gate_218_recheck_raw") && !zero(n(r, "caller_gate_218_recheck_raw")) && present(r, "definition_identity") && a != null && predicate != null;
            if (done && Boolean.TRUE.equals(predicate)) {
                done = allPresent(r, "owner_selection", "owner_identity") && owner != null && actor != null && ownerAdmission != null;
                if (done && Boolean.TRUE.equals(ownerAdmission)) done = present(r, "property_identity") && pc(r.get("property_block"));
            }
        }
        complete(r, done, f); return r;
    }
    private static ObjectNode helper2530(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "first_key_158_raw", "first_selection", "first_identity", "definition_identity", "definition_magic_38_raw",
                "admitted", "type_280_raw", "owner_id_160_raw", "character_id_18_raw", "rows", "reason");
        words(r, f, 32, false, "first_key_158_raw", "owner_id_160_raw", "character_id_18_raw"); words(r, f, 32, true, "definition_magic_38_raw");
        words(r, f, 8, true, "type_280_raw"); strings(r, f, "first_selection", "first_identity", "definition_identity"); bools(r, f, "admitted");
        Boolean admitted = equalWhenKnown(n(r, "definition_magic_38_raw"), GOVERNMENT_MAGIC);
        require(Objects.equals(b(r, "admitted"), admitted), f, "definition magic38 admission differs");
        BigInteger type = n(r, "type_280_raw"), owner = n(r, "owner_id_160_raw"), actor = n(r, "character_id_18_raw");
        Boolean[] expected = {type == null ? null : type.compareTo(BigInteger.valueOf(3)) < 0, Boolean.TRUE, equalWhenKnown(owner, actor)};
        JsonNode originalRows = r.get("rows"); require(nil(originalRows) || (originalRows.isArray() && (originalRows.size() == 0 || originalRows.size() == 3)), f, "three call ordinals or whole skip required");
        r.set("rows", indexed(originalRows, f + ".rows", (value, name, ordinal) -> row2530(value, name, ordinal, expected[ordinal])));
        JsonNode rows = r.get("rows"); boolean done = nil(r.get("reason")) && allPresent(r, "first_selection", "first_identity", "definition_identity") && admitted != null && !nil(rows);
        if (done && Boolean.FALSE.equals(admitted)) done = empty(rows);
        else if (done) done = rows.size() == 3 && all(rows, row -> present(row, "admitted") && nil(row.get("reason")) && (!yes(row, "admitted")
                || (allPresent(row, "definition_identity", "count_214_raw", "requested_index_228_raw", "selected_index_raw", "table_identity", "property_identity") && pc(row.get("property_block")))));
        complete(r, done, f); return r;
    }
    private static ObjectNode row2530(JsonNode raw, String f, int ordinal, Boolean admission) {
        ObjectNode r = plain(raw, f, "native_index", "admitted", "definition_identity", "count_214_raw", "requested_index_228_raw", "selected_index_raw",
                "table_identity", "property_identity", "property_block", "reason");
        index(r, f, ordinal); bools(r, f, "admitted"); words(r, f, 32, false, "count_214_raw", "requested_index_228_raw", "selected_index_raw");
        strings(r, f, "definition_identity", "table_identity", "property_identity", "reason"); propertiesField(r, f, "property_block");
        require(Objects.equals(b(r, "admitted"), admission), f, "native call admission differs");
        BigInteger count = n(r, "count_214_raw"), requested = n(r, "requested_index_228_raw");
        if (count != null && requested != null) {
            // Native signed32 subtraction wraps before the signed minimum comparison.
            BigInteger actual = requested.signum() < 0 ? BigInteger.ZERO : requested.min(BigInteger.valueOf(count.subtract(BigInteger.ONE).intValue()));
            require(actual.equals(n(r, "selected_index_raw")), f, "signed32 native clamp differs");
        }
        if (!Boolean.TRUE.equals(admission)) undemanded(r, f, "definition_identity", "count_214_raw", "requested_index_228_raw", "selected_index_raw", "table_identity", "property_identity", "property_block");
        return r;
    }

    private static ObjectNode middleHelpers(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "character_id", "helper_291f260", "helper_291fb10", "reason");
        requiredNumber(r, f, "character_id", 32, false); r.set("helper_291f260", helper260(r.get("helper_291f260"), f + ".helper_291f260"));
        r.set("helper_291fb10", helperFb10(r.get("helper_291fb10"), f + ".helper_291fb10"));
        complete(r, yes(r.get("helper_291f260"), "ready") && yes(r.get("helper_291fb10"), "ready"), f); return r;
    }
    private static ObjectNode helper260(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "component_present", "families", "reason"); bools(r, f, "component_present");
        require(r.get("families").isArray() && r.get("families").size() == 4, f, "four native families required");
        r.set("families", indexed(r.get("families"), f + ".families", (item, name, ordinal) -> rankFamily(item, name, ordinal, b(r, "component_present"))));
        complete(r, all(r.get("families"), row -> yes(row, "ready")), f); return r;
    }
    private static BigInteger rankExpected(ObjectNode r, Boolean component, String f) {
        if (Boolean.FALSE.equals(component)) {
            undemanded(r, f, "score_q64", "override_raw", "threshold_count", "threshold_array_present", "thresholds_consumed_q64"); return BigInteger.ZERO;
        }
        if (component == null) return null;
        BigInteger score = n(r, "score_q64"), override = n(r, "override_raw"), count = n(r, "threshold_count"); JsonNode rows = r.get("thresholds_consumed_q64");
        if (score == null || override == null || count == null || nil(rows)) return null;
        int rank = 0;
        if (count.signum() <= 0) {
            require(rows.isEmpty() && nil(r.get("threshold_array_present")), f, "nonpositive count contains thresholds");
        } else {
            require(BigInteger.valueOf(rows.size()).compareTo(count) <= 0, f, "threshold prefix exceeds native count"); boolean stopped = false;
            for (int i = 0; i < rows.size(); i++) {
                if (score.compareTo(rows.get(i).bigIntegerValue()) < 0) { require(i == rows.size() - 1, f, "thresholds continue after stop"); stopped = true; break; }
                rank++;
            }
            if (!yes(r, "threshold_array_present") || (!stopped && !sizeEquals(rows, count))) return null;
        }
        BigInteger value = BigInteger.valueOf(rank); return override.signum() >= 0 ? value.min(override) : value;
    }
    private record Lookup(boolean found, BigInteger index) { }
    private static Lookup lookupExpected(ObjectNode r, String f) {
        BigInteger count = n(r, "weight_keys_count_raw"); JsonNode probes = r.get("weight_key_probes");
        if (!nonnegative(count) || nil(probes)) return null;
        int cursor = 0; BigInteger lower = BigInteger.ZERO, remaining = count;
        while (remaining.signum() > 0) {
            BigInteger half = remaining.divide(BigInteger.TWO); if (cursor >= probes.size()) return null;
            JsonNode probe = probes.get(cursor++); require(n(probe, "native_index").equals(lower.add(half)), f, "weight lookup probe order differs");
            BigInteger key = n(probe, "key_u16"); if (key.compareTo(n(r, "weight_key_u16")) < 0) lower = lower.add(remaining.subtract(half)); remaining = half;
        }
        boolean found = false;
        if (!lower.equals(count)) {
            if (cursor >= probes.size()) return null; JsonNode probe = probes.get(cursor++);
            require(n(probe, "native_index").equals(lower), f, "final weight lookup probe order differs"); found = n(probe, "key_u16").equals(n(r, "weight_key_u16"));
        }
        require(cursor == probes.size(), f, "unused weight lookup probes"); return new Lookup(found, found ? lower : null);
    }
    private static ObjectNode rankFamily(JsonNode raw, String f, int ordinal, Boolean component) {
        ObjectNode r = available(raw, f, "status", "ready", "native_index", "override_raw", "threshold_count", "rank_raw", "manager_count_raw", "definition_gate_raw",
                "weight_default_guard_raw", "weight_keys_count_raw", "weight_native_index", "score_q64", "weight_value_q64", "weight_q64", "definition_selection",
                "definition_identity", "weight_source_selection", "weight_source_identity", "property_identity", "threshold_array_present", "admitted", "weight_carrier_present",
                "weight_owner_matches", "weight_found", "thresholds_consumed_q64", "weight_key_u16", "weight_key_probes", "property_block", "reason");
        index(r, f, ordinal); requiredNumber(r, f, "weight_key_u16", 16, true);
        require(n(r, "weight_key_u16").intValueExact() == new int[] {45, 44, 46, 47}[ordinal], f, "native family weight key differs");
        words(r, f, 32, false, "override_raw", "threshold_count", "rank_raw", "manager_count_raw", "definition_gate_raw", "weight_default_guard_raw", "weight_keys_count_raw", "weight_native_index");
        words(r, f, 64, false, "score_q64", "weight_value_q64", "weight_q64"); strings(r, f, "definition_identity", "weight_source_identity", "property_identity");
        selection(r, f, "definition_selection", "manager_rank_index", "native_rank_fallback");
        selection(r, f, "weight_source_selection", "exact_owner_carrier_10", "inline_weight_default_5d67b90");
        bools(r, f, "threshold_array_present", "admitted", "weight_carrier_present", "weight_owner_matches", "weight_found"); propertiesField(r, f, "property_block");
        r.set("thresholds_consumed_q64", numbers(r.get("thresholds_consumed_q64"), f + ".thresholds_consumed_q64", 64, false, true, false));
        r.set("weight_key_probes", indexed(r.get("weight_key_probes"), f + ".weight_key_probes", (value, name, ignored) -> {
            ObjectNode p = plain(value, name, "native_index", "key_u16"); requiredNumber(p, name, "native_index", 32, false); requiredNumber(p, name, "key_u16", 16, true); return p;
        }));
        BigInteger gate = n(r, "definition_gate_raw"); require(Objects.equals(b(r, "admitted"), nonzero(gate)), f, "definition nonzero admission differs");
        BigInteger expectedRank = rankExpected(r, component, f); if (expectedRank != null) require(expectedRank.equals(n(r, "rank_raw")), f, "rank differs from consumed thresholds");
        boolean selectionReady = expectedRank != null && allPresent(r, "definition_selection", "definition_identity") && gate != null;
        BigInteger rank = n(r, "rank_raw"), count = n(r, "manager_count_raw");
        if (present(r, "definition_selection") && rank != null) {
            String expected = rank.signum() >= 0 && count == null ? null : rank.signum() >= 0 && rank.compareTo(count) < 0 ? "manager_rank_index" : "native_rank_fallback";
            require(expected == null || expected.equals(s(r, "definition_selection")), f, "rank/count definition selection differs");
        }
        boolean weightReady = false;
        if (!yes(r, "admitted")) undemanded(r, f, "weight_carrier_present", "weight_owner_matches", "weight_source_selection", "weight_source_identity", "weight_default_guard_raw",
                "weight_keys_count_raw", "weight_key_probes", "weight_found", "weight_native_index", "weight_value_q64", "weight_q64", "property_identity", "property_block");
        else {
            Lookup lookup = lookupExpected(r, f);
            if (lookup != null) {
                require(Objects.equals(b(r, "weight_found"), lookup.found()) && Objects.equals(n(r, "weight_native_index"), lookup.index()), f, "native lower-bound result differs");
                BigInteger value = n(r, "weight_value_q64"); require(lookup.found() || value == null, f, "absent weight key contains value");
                if (!lookup.found() || value != null) {
                    // The addition is the native signed64 value operation, modulo 2^64.
                    BigInteger weighted = BigInteger.valueOf(BigInteger.valueOf(100000).add(value == null ? BigInteger.ZERO : value).longValue());
                    require(weighted.equals(n(r, "weight_q64")), f, "signed64 wrapping addition differs"); weightReady = allPresent(r, "weight_source_selection", "weight_source_identity");
                }
            }
            if ("exact_owner_carrier_10".equals(s(r, "weight_source_selection"))) weightReady = weightReady && yes(r, "weight_carrier_present") && yes(r, "weight_owner_matches");
            else if ("inline_weight_default_5d67b90".equals(s(r, "weight_source_selection"))) weightReady = weightReady && goodGuard(n(r, "weight_default_guard_raw"));
        }
        complete(r, selectionReady && (no(r, "admitted") || (weightReady && present(r, "property_identity") && pc(r.get("property_block")))) && nil(r.get("reason")), f); return r;
    }

    private static ObjectNode modifier(JsonNode raw, String f, int ordinal) {
        ObjectNode r = plain(raw, f, "native_index", "modifier_identity", "token_u8", "modifier_count_u8", "base_selection", "property_identity", "gate_raw", "admitted", "property_block", "reason");
        index(r, f, ordinal); strings(r, f, "modifier_identity", "base_selection", "property_identity", "reason");
        words(r, f, 8, true, "token_u8", "modifier_count_u8"); words(r, f, 32, false, "gate_raw"); bools(r, f, "admitted"); propertiesField(r, f, "property_block");
        require(Objects.equals(b(r, "admitted"), nonzero(n(r, "gate_raw"))), f, "modifier signed32 gate differs");
        BigInteger token = n(r, "token_u8"), count = n(r, "modifier_count_u8");
        String expected = token == null || count == null ? null : count.compareTo(token) > 0 ? "token_indexed" : "native_modifier_fallback";
        require(!present(r, "base_selection") || Objects.equals(s(r, "base_selection"), expected), f, "modifier native u8 selection differs");
        require(yes(r, "admitted") || nil(r.get("property_block")), f, "undemanded modifier PC"); return r;
    }
    private static ObjectNode context(JsonNode raw, String f, int ordinal) {
        ObjectNode r = available(raw, f, "status", "ready", "native_index", "requested_full_id_raw", "full_id_raw", "owner_full_id_raw", "character_full_id_raw", "modifier_count",
                "selection", "context_identity", "terminal_property_identity", "admitted", "owner_matches", "modifier_array_present", "token_array_present", "magic_raw", "modifier_rows", "terminal_property_block", "reason");
        index(r, f, ordinal); words(r, f, 32, false, "requested_full_id_raw", "full_id_raw", "owner_full_id_raw", "character_full_id_raw", "modifier_count");
        words(r, f, 32, true, "magic_raw"); strings(r, f, "context_identity", "terminal_property_identity");
        selection(r, f, "selection", "land_1c0", "land_1c8", "native_subc_fallback", "registry_full_id_8");
        bools(r, f, "admitted", "owner_matches", "modifier_array_present", "token_array_present"); propertiesField(r, f, "terminal_property_block");
        r.set("modifier_rows", indexed(r.get("modifier_rows"), f + ".modifier_rows", BattlePersonContextPrefixCodec::modifier));
        BigInteger magic = n(r, "magic_raw"), fullId = n(r, "full_id_raw");
        Boolean admitted = magic == null ? null : !magic.equals(SUBC_MAGIC) ? Boolean.FALSE : fullId == null ? null : !minusOne(fullId);
        require(Objects.equals(b(r, "admitted"), admitted), f, "SubC magic/full ID predicate differs");
        require(Objects.equals(b(r, "owner_matches"), equalWhenKnown(n(r, "owner_full_id_raw"), n(r, "character_full_id_raw"))), f, "full-ID owner equality differs");
        JsonNode rows = r.get("modifier_rows"); BigInteger count = n(r, "modifier_count"); boolean consumed;
        if (Boolean.FALSE.equals(admitted)) {
            undemanded(r, f, "owner_matches", "modifier_array_present", "token_array_present", "owner_full_id_raw", "character_full_id_raw", "modifier_count", "terminal_property_identity", "terminal_property_block");
            consumed = empty(rows);
        } else {
            consumed = Boolean.TRUE.equals(admitted) && present(r, "owner_matches") && count != null && sizeEquals(rows, count.max(BigInteger.ZERO))
                    && present(r, "terminal_property_identity") && pc(r.get("terminal_property_block"));
            if (consumed && positive(count)) consumed = yes(r, "modifier_array_present") && yes(r, "token_array_present")
                    && all(rows, row -> allPresent(row, "modifier_identity", "base_selection", "property_identity", "admitted") && nil(row.get("reason"))
                        && (!yes(row, "admitted") || pc(row.get("property_block"))));
        }
        complete(r, consumed && allPresent(r, "selection", "context_identity") && nil(r.get("reason")), f); return r;
    }
    private static ObjectNode contextFamily(JsonNode raw, String f, String family) {
        ObjectNode r = available(raw, f, "status", "ready", "header_selection", "count", "array_present", "rows", "reason");
        strings(r, f, "header_selection"); words(r, f, 32, false, "count"); bools(r, f, "array_present");
        r.set("rows", indexed(r.get("rows"), f + ".rows", BattlePersonContextPrefixCodec::context)); BigInteger count = n(r, "count");
        boolean done = nonnegative(count) && sizeEquals(r.get("rows"), count) && present(r, "header_selection") && all(r.get("rows"), row -> yes(row, "ready")) && nil(r.get("reason"));
        if (family.equals("preferred")) done = done && BigInteger.ONE.equals(count) && nil(r.get("array_present"));
        else done = done && present(r, "array_present");
        complete(r, done, f); return r;
    }
    private static ObjectNode helperFb10(JsonNode raw, String f) {
        ObjectNode r = available(raw, f, "status", "ready", "land_present", "preferred", "list_218", "list_248", "reason"); bools(r, f, "land_present");
        for (String family : FAMILIES_FB10) r.set(family, contextFamily(r.get(family), f + "." + family, family));
        complete(r, present(r, "land_present") && familiesReady(r, FAMILIES_FB10), f); return r;
    }

    @FunctionalInterface private interface IndexedNormalizer { JsonNode normalize(JsonNode raw, String field, int index); }
    private static JsonNode indexed(JsonNode raw, String f, IndexedNormalizer normalize) {
        int[] cursor = {0}; return array(raw, f, true, (item, name) -> normalize.normalize(item, name, cursor[0]++));
    }
    private static ObjectNode plain(JsonNode raw, String f, String... fields) { return exact(raw, f, Set.of(fields)).deepCopy(); }
    private static ObjectNode available(JsonNode raw, String f, String... fields) {
        ObjectNode result = plain(raw, f, fields); Availability actual = availability(result, f); availabilityFields(result, actual, "reason"); return result;
    }
    private static void strings(ObjectNode r, String f, String... keys) { for (String key : keys) r.set(key, text(r.get(key), f + "." + key, true, true)); }
    private static void words(ObjectNode r, String f, int bits, boolean unsigned, String... keys) {
        for (String key : keys) r.set(key, number(r.get(key), f + "." + key, bits, unsigned, true));
    }
    private static void requiredNumber(ObjectNode r, String f, String key, int bits, boolean unsigned) { r.set(key, number(r.get(key), f + "." + key, bits, unsigned, false)); }
    private static void bools(ObjectNode r, String f, String... keys) { for (String key : keys) r.set(key, bool(r.get(key), f + "." + key, true)); }
    private static void requiredBool(ObjectNode r, String f, String... keys) { for (String key : keys) r.set(key, bool(r.get(key), f + "." + key, false)); }
    private static void propertiesField(ObjectNode r, String f, String... keys) { for (String key : keys) r.set(key, properties(r.get(key), f + "." + key)); }
    private static void selection(ObjectNode r, String f, String key, String... allowed) {
        r.set(key, text(r.get(key), f + "." + key, true, true)); String selected = s(r, key);
        require(selected == null || Set.of(allowed).contains(selected), f + "." + key, "invalid native selection");
    }
    private static void index(ObjectNode r, String f, int ordinal) {
        requiredNumber(r, f, "native_index", 32, false); require(n(r, "native_index").equals(BigInteger.valueOf(ordinal)), f, "stored native order differs");
    }
    private static void undemanded(JsonNode r, String f, String... keys) { for (String key : keys) require(nil(r.get(key)), f, "undemanded native operand " + key); }
    private static void complete(ObjectNode r, boolean expected, String f) { require(yes(r, "ready") == expected, f, "availability differs from consumed native operands"); }
    private static boolean familiesReady(JsonNode r, String... names) { for (String name : names) if (!yes(r.get(name), "ready")) return false; return true; }
    private static boolean all(JsonNode rows, Predicate<JsonNode> predicate) { if (nil(rows)) return false; for (JsonNode row : rows) if (!predicate.test(row)) return false; return true; }
    private static boolean empty(JsonNode rows) { return rows != null && rows.isArray() && rows.isEmpty(); }
    private static boolean sizeEquals(JsonNode rows, BigInteger count) { return rows != null && rows.isArray() && count != null && count.equals(BigInteger.valueOf(rows.size())); }
    private static boolean present(JsonNode r, String key) { return r.get(key) != null && !nil(r.get(key)); }
    private static boolean allPresent(JsonNode r, String... keys) { for (String key : keys) if (!present(r, key)) return false; return true; }
    private static boolean pc(JsonNode value) { return propertiesReady(value) && nil(value.get("reason")); }
    private static BigInteger n(JsonNode r, String key) { return integer(r.get(key)); }
    private static Boolean b(JsonNode r, String key) { return booleanValue(r.get(key)); }
    private static String s(JsonNode r, String key) { return string(r.get(key)); }
    private static boolean yes(JsonNode r, String key) { return Boolean.TRUE.equals(b(r, key)); }
    private static boolean no(JsonNode r, String key) { return Boolean.FALSE.equals(b(r, key)); }
    private static boolean zero(BigInteger value) { return BigInteger.ZERO.equals(value); }
    private static boolean minusOne(BigInteger value) { return BigInteger.ONE.negate().equals(value); }
    private static boolean nonnegative(BigInteger value) { return value != null && value.signum() >= 0; }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static boolean goodGuard(BigInteger value) { return value != null && !zero(value) && !minusOne(value); }
    private static Boolean nonzero(BigInteger value) { return value == null ? null : value.signum() != 0; }
    private static Boolean equalWhenKnown(BigInteger first, BigInteger second) { return first == null || second == null ? null : first.equals(second); }
}
