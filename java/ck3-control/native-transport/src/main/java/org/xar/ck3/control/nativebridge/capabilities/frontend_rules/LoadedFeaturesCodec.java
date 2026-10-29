package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.LoadedFeaturesData.*;

/** Exact original producer envelope and full nested registry validation, before constructing the domain. */
public final class LoadedFeaturesCodec {
    private LoadedFeaturesCodec() { }
    private record Definition(long id, String key) { }
    private static final List<Definition> BASE = List.of(
        new Definition(0x3587,"garments_of_the_hre"), new Definition(0x3588,"fashion_of_the_abbasid_court"), new Definition(0x34A7,"the_northern_lords"),
        new Definition(0x3538,"hybridize_culture"), new Definition(0x3539,"diverge_culture"), new Definition(0x3270,"royal_court"), new Definition(0x366D,"reform_culture"),
        new Definition(0x34DC,"court_artifacts"), new Definition(0x3773,"the_fate_of_iberia"), new Definition(0x3608,"friends_and_foes"), new Definition(0x37CF,"tours_and_tournaments"),
        new Definition(0x37CE,"advanced_activities"), new Definition(0x36C4,"accolades"), new Definition(0x377A,"legacy_of_persia"), new Definition(0x35E0,"elegance_of_the_empire"),
        new Definition(0x394A,"wards_and_wardens"), new Definition(0x3B0A,"legends_of_the_dead"), new Definition(0x3A5B,"legends"), new Definition(0x3A09,"north_african_attire"),
        new Definition(0x3A08,"couture_of_the_capets"), new Definition(0x3953,"landless_playable"), new Definition(0x3A00,"admin_gov"), new Definition(0x3A02,"roads_to_power"),
        new Definition(0x3A01,"court_room_view"), new Definition(0x39DA,"wandering_nobles"), new Definition(0x3CBB,"west_slavic_attire"), new Definition(0x3A07,"medieval_monuments"),
        new Definition(0x3C98,"khans_of_the_steppe"), new Definition(0x3CA1,"nomads"), new Definition(0x3A06,"arctic_attire"), new Definition(0x39F7,"crowns_of_the_world"),
        new Definition(0x3D67,"landless_adventurer"), new Definition(0x39ED,"coronations"), new Definition(0x39EE,"all_under_heaven"), new Definition(0x39EF,"merit_admin"),
        new Definition(0x39F0,"advanced_aspirations"), new Definition(0x39F1,"barter_troops"), new Definition(0x39DB,"high_medieval_warfare_attire"), new Definition(0x39DC,"holy_buildings"),
        new Definition(0x39DD,"north_pacific_attire"), new Definition(0x39DE,"east_asian_wonders"), new Definition(0x39DF,"celestial_court_attire"), new Definition(0x4101,"symbols_of_authority"), new Definition(0x4102,"songs_of_the_realm"));
    private static List<Definition> definitions(Build build) {
        if (build == Build.CK3_11906) return BASE;
        List<Definition> values = new ArrayList<>(BASE.subList(0, 36)); values.addAll(BASE.subList(37, BASE.size())); values.add(new Definition(0x4169, "by_god_alone")); return List.copyOf(values);
    }
    public record Envelope(Manifest manifest, BigInteger querySequence) { public Envelope { java.util.Objects.requireNonNull(manifest); positiveU64(querySequence); } }
    public static Envelope decode(RawJson raw, Build expectedBuild, BigInteger expectedNativeRevision, int expectedDateRaw) {
        ObjectNode envelope = object(raw); Set<String> fields = new java.util.HashSet<>(Set.of("step", "accepted", "status", "query_sequence", "snapshot_revision", "loaded_feature_manifest"));
        if (envelope.has("backend_id")) fields.add("backend_id"); exact(envelope, fields); nativeBackend(envelope);
        equalText(envelope, "step", "query-loaded-feature-manifest-v1"); expectedBool(envelope, "accepted", true);
        BigInteger revision = u64(envelope, "snapshot_revision"); require(revision.equals(expectedNativeRevision), "loaded-feature envelope revision drift");
        Manifest manifest = manifest(obj(envelope, "loaded_feature_manifest"), expectedBuild, expectedNativeRevision, expectedDateRaw);
        equalText(envelope, "status", manifest.unavailableReason().isEmpty() ? "available" : "unavailable"); return new Envelope(manifest, u64(envelope, "query_sequence"));
    }
    private static Manifest manifest(ObjectNode frame, Build expectedBuild, BigInteger expectedRevision, int expectedDate) {
        exact(frame, Set.of("schema", "schema_version", "status", "snapshot_revision", "date_raw", "unavailable_reason", "build", "effective_feature_flags", "script_dlc_keys", "entitlements", "readiness", "provenance"));
        schema(frame, "loaded-feature-manifest-v1"); String status = text(frame, "status"); require(status.equals("available") || status.equals("unavailable"), "unknown manifest status"); boolean available = status.equals("available");
        BigInteger revision = u64(frame, "snapshot_revision"); int date = count(frame, "date_raw", Integer.MIN_VALUE, Integer.MAX_VALUE); require(revision.equals(expectedRevision) && date == expectedDate, "loaded-feature original frame changed");
        Optional<String> reasonText = nullableText(frame, "unavailable_reason"); require(available == reasonText.isEmpty(), "manifest reason/status contradiction"); Optional<UnavailableReason> reason = reasonText.map(UnavailableReason::require);
        ObjectNode buildNode = obj(frame, "build"); exact(buildNode, Set.of("version", "exe_sha256")); Build build = Build.require(text(buildNode, "version"), text(buildNode, "exe_sha256")); require(build == expectedBuild, "loaded-feature build disagrees with original hello");
        Flags flags = flags(obj(frame, "effective_feature_flags"), build, reason); ScriptDlcs dlcs = dlcs(obj(frame, "script_dlc_keys"), reason);
        ObjectNode entitlements = obj(frame, "entitlements"); exact(entitlements, Set.of("status", "unavailable_reason", "items")); equalText(entitlements, "status", "unavailable"); equalText(entitlements, "unavailable_reason", "store_verdict_provenance_unclosed"); require(field(entitlements, "items").isNull(), "entitlements invented ownership");
        ObjectNode ready = obj(frame, "readiness"); exact(ready, Set.of("effective_feature_flags_ready", "script_dlc_keys_ready", "entitlements_ready", "same_frame_ready", "actionable_ready"));
        Readiness readiness = new Readiness(bool(ready, "effective_feature_flags_ready"), bool(ready, "script_dlc_keys_ready"), bool(ready, "entitlements_ready"), bool(ready, "same_frame_ready"), bool(ready, "actionable_ready"));
        ObjectNode provenance = obj(frame, "provenance"); exact(provenance, Set.of("feature_root_slot_rva", "feature_bitset_rva", "feature_enum_table_rva", "script_dlc_set_rva", "backend_id"));
        Provenance expected = build == Build.CK3_11906 ? new Provenance("0x576CC68", "root+0x2B0", "0x42F7850..0x42F7900", "0x5762590", build.backendId("loaded-feature-manifest-v1"))
                : new Provenance("0x5CB87F8", "root+0x2B0", build == Build.CK3_12004 ? "0x47334D0..0x4733580" : "0x47334C0..0x4733570", "0x5CC15E0", build.backendId("loaded-feature-manifest-v1"));
        Provenance actual = new Provenance(text(provenance, "feature_root_slot_rva"), text(provenance, "feature_bitset_rva"), text(provenance, "feature_enum_table_rva"), text(provenance, "script_dlc_set_rva"), text(provenance, "backend_id")); require(actual.equals(expected), "loaded-feature provenance changed");
        return new Manifest(build, revision, date, reason, flags, dlcs, readiness, actual);
    }
    private static Flags flags(ObjectNode value, Build build, Optional<UnavailableReason> reason) {
        exact(value, Set.of("status", "unavailable_reason", "native_count", "items")); availability(value, reason);
        if (reason.isPresent()) { require(field(value, "native_count").isNull() && field(value, "items").isNull(), "unavailable flags invented native state"); return new UnavailableFlags(reason.get()); }
        List<Definition> definitions = definitions(build); require(count(value, "native_count", 44, 44) == definitions.size(), "native feature counter mismatch");
        JsonNode rows = field(value, "items"); require(rows.isArray() && rows.size() == definitions.size(), "complete native feature registry required"); List<Feature> items = new ArrayList<>();
        for (int index = 0; index < rows.size(); index++) {
            JsonNode row = rows.get(index); exact(row, Set.of("native_index", "cstring_id", "key", "enabled")); Definition expected = definitions.get(index);
            int nativeIndex = count(row, "native_index", 0, 43); long id = integer(row, "cstring_id", BigInteger.ONE, BigInteger.valueOf(0xffff_ffffL)).longValueExact(); String key = text(row, "key");
            require(nativeIndex == index && id == expected.id() && key.equals(expected.key()), "native feature registry drift"); items.add(new Feature(nativeIndex, id, key, bool(row, "enabled")));
        }
        return new AvailableFlags(items);
    }
    private static ScriptDlcs dlcs(ObjectNode value, Optional<UnavailableReason> reason) {
        exact(value, Set.of("status", "unavailable_reason", "enumerated_count", "keys")); availability(value, reason);
        if (reason.isPresent()) { require(field(value, "enumerated_count").isNull() && field(value, "keys").isNull(), "unavailable DLCs invented state"); return new UnavailableScriptDlcs(reason.get()); }
        int count = count(value, "enumerated_count", 0, Integer.MAX_VALUE); JsonNode rows = field(value, "keys"); require(rows.isArray() && rows.size() == count, "DLC count/vector mismatch");
        List<String> keys = new ArrayList<>(); for (JsonNode row : rows) { require(row.isTextual(), "DLC key must be text"); keys.add(row.textValue()); } return new AvailableScriptDlcs(keys);
    }
    private static void availability(ObjectNode value, Optional<UnavailableReason> reason) {
        equalText(value, "status", reason.isEmpty() ? "available" : "unavailable"); require(nullableText(value, "unavailable_reason").equals(reason.map(UnavailableReason::wire)), "nested unavailability reason drift");
    }
}
