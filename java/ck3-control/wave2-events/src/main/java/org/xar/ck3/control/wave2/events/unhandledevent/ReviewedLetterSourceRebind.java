package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** The three existing finite letter reviews, with actual installed source and GUI hash reads. */
final class ReviewedLetterSourceRebind {
    private ReviewedLetterSourceRebind() { }
    static final Set<String> KEYS = Set.of("faction_demand.0101", "ecumenical_council_events.0082", "sway_ongoing.1003");
    private static final String POLICY = "two-reviewed-letter-source-shapes-12004-v1";
    private static final String SWAY_POLICY = "sway1003-reviewed-letter-source-shapes-12004-v1";
    private static final Map<String, String> GUI = Map.of(
        "gui/event_windows/letter_event.gui", "eb141a50868cd0f32cb9327630a895024edaa9e7580ab4520be88032bfc4ee8c",
        "gui/shared/event_windows.gui", "6756fed934b15e20f2e9460a891c5b40f0012e6f8f51ac6ae45a018fd9a82639");
    private record Review(String relative, int count, String sourceSha, String definitionSha, String optionsSha) { }
    private static final Map<String, Review> REVIEWS = Map.of(
        "faction_demand.0101", new Review("events/factions/faction_demands.txt", 3,
            "eb17720ca9d48acfb8cc24e5f61edc62fd2d4d2d599561c92854fc762104eccd", "940aad8858ceca76b47fee049055d68a8f98a23f4044761b59561942cb8b75f7", "fe3f9e729592133fed0faaa4b4b57b0051183a1450bcdb85d37627700f017ea6"),
        "ecumenical_council_events.0082", new Review("events/activities/ecumenical_council_activity/pam_ecumenical_council_events.txt", 1,
            "194d12e1fe54b015d6f89ef15c4d435e80ea6b3bf4c453623d2240de29c4a559", "27b9f85792a014009245ae2733a361f0154536590bdb3f45b67cdced3a662df9", "80ad6cd429d44d7a785575f7417d3a8bb06c4a51b574ebc8f8cbb0acf9fe771a"),
        "sway_ongoing.1003", new Review("events/scheme_events/sway_scheme/sway_ongoing_events.txt", 1,
            "cac2328a721aae13c5c60dbe81eccdf83cd8bf06eca1f51f247a098c0f435adc", "e3446738b3d835048bbcecf8bc8791fdc0bd96fdf4952d984314ee963c7c6295", "cb16650d3b41b5c0ff0fe3365712fa89aaf1ccf70f5a165c253f34d3f824d8a8"));
    private record OpaqueRole(String name, String kind, int rawType) { }
    private static final List<OpaqueRole> SWAY_OPAQUE = List.of(new OpaqueRole("scheme", "scheme", 9), new OpaqueRole("artifact", "artifact", 31),
        new OpaqueRole("evaluated_compliment_type", "flag", 3), new OpaqueRole("compliment_outcome", "flag", 3));
    private static final List<OpaqueRole> COUNCIL_OPAQUE = List.of(new OpaqueRole("activity", "activity", 6), new OpaqueRole("province", "province", 8),
        new OpaqueRole("activity_location", "province", 8), new OpaqueRole("ec_council", "activity", 6), new OpaqueRole("ec_council_faith", "faith", 13),
        new OpaqueRole("ec_letter_tenet_1", "tenet", 40), new OpaqueRole("ec_letter_tenet_2", "tenet", 40), new OpaqueRole("ec_letter_doctrine_1", "doctrine", 39));

    static Map<String, String> installedSourceHashes() {
        Map<String, String> result = new LinkedHashMap<>(GUI);
        REVIEWS.values().forEach(review -> result.put(review.relative(), review.sourceSha()));
        return Map.copyOf(result);
    }
    static ObjectValue shape(ObjectValue capture, ObjectValue facts, SourceReviewedEventConsumer.NativeBinding current) throws IOException {
        return shape(capture, facts, current, null);
    }
    static ObjectValue shape(ObjectValue capture, ObjectValue facts, SourceReviewedEventConsumer.NativeBinding current,
            TrustedEventSourceContext trusted) throws IOException {
        String key = current.eventKey(); require(KEYS.contains(key), "letter key has no finite source-rebind review"); Review review = REVIEWS.get(key);
        ObjectValue source = o(facts, "binding"); String definition = text(facts, "definition");
        require(current.build().equals("1.20.0.4") && current.exeSha256().equals(SourceReviewedEventConsumer.BUILDS.get("1.20.0.4"))
            && current.backend().equals(SourceReviewedEventConsumer.BACKEND) && current.optionCount().equals(BigInteger.valueOf(review.count()))
            && List.of("event_definition_key", "ck3_build", "required_ck3_exe_sha256", "native_backend_id", "native_option_count")
                .stream().allMatch(field -> v(source, field).equals(v(current.json(), field)))
            && eq(source, "source_sha256", s(review.sourceSha())) && eq(source, "option_catalogue_sha256", s(review.optionsSha()))
            && eq(facts, "source_relative", s(review.relative())) && definition != null && sha(definition.getBytes(StandardCharsets.UTF_8)).equals(review.definitionSha())
            && fingerprint(v(facts, "options")).equals(review.optionsSha()), "reviewed letter build/definition/source/catalogue differs");
        ObjectValue shape = SourceReviewedEventConsumer.rootShape(capture, facts, current, "letter_event");
        ObjectValue context = o(capture, "window_context"), frame = o(capture, "binding"), provenance = o(context, "provenance");
        require(eq(context, "schema_version", i(1)) && eq(context, "window_match_count", i(1)) && yes(frame, "paused") && yes(frame, "map_ready")
            && positive(number(frame, "revision")) && positive(number(frame, "native_revision")) && eq(frame, "snapshot_id", s("native:" + number(frame, "native_revision")))
            && text(frame, "episode_run_id") != null && !text(frame, "episode_run_id").isEmpty() && positive(number(frame, "bridge_pid")) && positive(number(frame, "connection_generation"))
            && eq(provenance, "root", s("module+0x5C6A520->+0x10")) && eq(provenance, "idler_vtable_rva", s("0x44BC418")) && eq(provenance, "manager_offset", s("+0x28")), "reviewed letter current native frame/provider differs");
        Path relative = Path.of(review.relative()); Path declaredSource = Path.of(text(facts, "source_path"));
        if (trusted != null) trusted.read(declaredSource, 2_097_152, TrustedEventSourceContext.FileRole.SOURCE);
        Path sourcePath = declaredSource.toRealPath(); Path game = sourcePath;
        for (int index = 0; index < relative.getNameCount(); index++) {
            game = game.getParent(); require(game != null, "reviewed letter source path has no expected game root");
        }
        require(sourcePath.equals(game.resolve(relative).toRealPath()), "reviewed letter source location differs");
        checked(sourcePath, review.sourceSha(), trusted, TrustedEventSourceContext.FileRole.SOURCE);
        for (Map.Entry<String, String> gui : GUI.entrySet()) checked(game.resolve(gui.getKey()), gui.getValue(), trusted, TrustedEventSourceContext.FileRole.GUI);
        List<ObjectValue> ordered = objects(context, "options").stream().sorted(Comparator.comparing(row -> number(row, "rendered_index"))).toList();
        List<BigInteger> shown = new ArrayList<>();
        for (int index = 0; index < ordered.size(); index++) {
            ObjectValue row = ordered.get(index);
            require(yes(row, "shown") && v(row, "enabled") instanceof BooleanValue && eq(row, "rendered_index", i(index)), "reviewed letter actual displayed option shape differs");
            shown.add(number(row, "native_option_index"));
        }
        require(key.equals("faction_demand.0101") ? shown.equals(List.of(BigInteger.ZERO, BigInteger.TWO))
            || shown.equals(List.of(BigInteger.ZERO, BigInteger.ONE, BigInteger.TWO)) : shown.equals(List.of(BigInteger.ZERO)), "reviewed letter actual displayed option shape differs");
        Map<String, ObjectValue> roles = new LinkedHashMap<>();
        for (Value rawRole : array(context, "saved_scopes")) {
            ObjectValue row = o(rawRole);
            require(row != null && text(row, "name") != null && positive(number(row, "name_identifier")), "reviewed letter saved role names unavailable");
            require(!roles.containsKey(text(row, "name")), "reviewed letter saved role names duplicated"); roles.put(text(row, "name"), row);
        }
        BigInteger actor = number(frame, "actor_character_id");
        Map<String, Value> ids = new LinkedHashMap<>(); List<Value> gaps = new ArrayList<>();
        if (key.equals("faction_demand.0101")) {
            require(roles.keySet().equals(Set.of("faction", "faction_leader", "faction_target")), "reviewed liberty saved roles differ");
            BigInteger faction = id(roles.get("faction"), "faction", 25, "faction_id");
            BigInteger leader = id(roles.get("faction_leader"), "character", 4, "character_id"), target = id(roles.get("faction_target"), "character", 4, "character_id");
            ids.put("faction_id", RetainedJson.value(faction)); ids.put("faction_leader_character_id", RetainedJson.value(leader)); ids.put("faction_target_character_id", RetainedJson.value(target));
            require(target.equals(actor) && !leader.equals(actor), "reviewed liberty current target/leader semantics differ");
        } else if (key.equals("sway_ongoing.1003")) {
            Set<String> required = Set.of("owner", "target", "compliment_receiver", "scheme", "evaluated_compliment_type", "compliment_outcome");
            Set<String> permitted = new java.util.HashSet<>(required); permitted.addAll(Set.of("artifact", "friend"));
            require(roles.keySet().containsAll(required) && permitted.containsAll(roles.keySet()), "reviewed sway saved roles differ");
            for (String name : List.of("owner", "target", "compliment_receiver", "friend")) if (roles.containsKey(name)) ids.put(name + "_character_id", RetainedJson.value(id(roles.get(name), "character", 4, "character_id")));
            require(ids.get("owner_character_id").equals(RetainedJson.value(actor)) && !ids.get("target_character_id").equals(RetainedJson.value(actor))
                && !ids.get("compliment_receiver_character_id").equals(RetainedJson.value(actor)), "reviewed sway current owner/target/receiver semantics differ");
            opaque(roles, SWAY_OPAQUE, gaps);
        } else {
            Set<String> required = Set.of("activity", "host", "province", "activity_location", "root_scope", "ec_council", "ec_council_faith", "ec_reporter");
            Set<String> permitted = new java.util.HashSet<>(required); permitted.addAll(Set.of("ec_letter_tenet_1", "ec_letter_tenet_2", "ec_letter_doctrine_1"));
            require(roles.keySet().containsAll(required) && permitted.containsAll(roles.keySet()), "reviewed council saved roles differ");
            for (String name : List.of("host", "root_scope", "ec_reporter")) ids.put(name + "_character_id", RetainedJson.value(id(roles.get(name), "character", 4, "character_id")));
            require(ids.get("host_character_id").equals(ids.get("root_scope_character_id")), "reviewed council current host/root role shape differs");
            opaque(roles, COUNCIL_OPAQUE, gaps);
        }
        Map<String, Value> gui = new LinkedHashMap<>(); GUI.forEach((name, hash) -> gui.put(name, s(hash)));
        return put(shape, f("source_rebind_policy", s(key.equals("sway_ongoing.1003") ? SWAY_POLICY : POLICY)), f("reviewed_letter_key", s(key)),
            f("knowledge_scope", s("exact_definition_source_and_current_native_role_type_shape_only")), f("current_role_identities", new ObjectValue(ids)),
            f("scope_identity_gaps", new ArrayValue(gaps)), f("gui_source_sha256", new ObjectValue(gui)), f("loaded_gui_bytes_verified", b(false)),
            f("execution_contract_qualified", b(false)), f("semantic_decision_ready", b(false)));
    }
    private static ObjectValue scope(ObjectValue role, String kind, int raw) {
        ObjectValue scope = o(role, "scope");
        require(eq(scope, "status", s("available")) && eq(scope, "type_key", s(kind)) && eq(scope, "raw_type_index", i(raw)) && eq(scope, "subtype", i(0)), "reviewed letter role type shape differs");
        return scope;
    }
    private static BigInteger id(ObjectValue role, String kind, int raw, String field) {
        ObjectValue identity = o(scope(role, kind, raw), "typed_identity"); BigInteger value = number(identity, field);
        require(eq(identity, "status", s("available")) && eq(identity, "kind", s(kind)) && positive(value), "reviewed letter current role identity unavailable"); return value;
    }
    private static void opaque(Map<String, ObjectValue> roles, List<OpaqueRole> definitions, List<Value> gaps) {
        for (OpaqueRole definition : definitions) if (roles.containsKey(definition.name())) {
            ObjectValue identity = o(scope(roles.get(definition.name()), definition.kind(), definition.rawType()), "typed_identity");
            require(eq(identity, "status", s("unavailable")) && eq(identity, "reason", s("generic_scope_payload_identity_not_closed")), "reviewed letter opaque role representation differs");
            gaps.add(obj(f("role", s(definition.name())), f("type_key", s(definition.kind())), f("typed_identity_verified", b(false))));
        }
    }
    private static void checked(Path path, String expected, TrustedEventSourceContext trusted,
            TrustedEventSourceContext.FileRole role) throws IOException {
        require(sha(SourceReviewedEventConsumer.read(path, 2_097_152, trusted, role)).equals(expected), "reviewed letter source/GUI SHA differs");
    }
}
