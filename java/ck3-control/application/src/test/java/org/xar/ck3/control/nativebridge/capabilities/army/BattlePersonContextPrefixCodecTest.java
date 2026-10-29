package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonExternalCodec.Leaf;

/** Actual original Python normalizers -> strict Java boundary. Test ports never qualify Native execution. */
final class BattlePersonContextPrefixCodecTest {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final int MAX_CAPTURE = 4_194_304;
    private static final List<Leaf> OWNED = List.of(Leaf.LATER_DIRECT_291C3FB_44C, Leaf.HELPER_291F0A0, Leaf.LATER_HELPERS_291F550_291F940,
            Leaf.TAIL_DIRECT_291C5B7_291CC49, Leaf.TAIL_PREFIX_2753860_2922530, Leaf.MIDDLE_HELPERS_291F260_291FB10);
    private static final List<String> ORIGINAL_SOURCES = List.of(
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_context_source_inputs_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_later_direct_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_helper_291f0a0_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_remaining_helpers_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_tail_direct_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_tail_prefix_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_middle_helpers_contract.py",
            "ck3_autonomous_player/tests/unit/test_battle_person_later_direct_12003.py",
            "ck3_autonomous_player/tests/unit/test_battle_person_helper_291f0a0_12003.py",
            "ck3_autonomous_player/tests/unit/test_battle_person_remaining_helpers_12003.py",
            "ck3_autonomous_player/tests/unit/test_battle_person_tail_direct_12003.py");

    @Test void nativeSignedClampThresholdLookupWrapAndDuplicateOccurrencesRoundtrip() throws Exception {
        for (Seed seed : List.of(new Seed(Leaf.TAIL_PREFIX_2753860_2922530, prefix()), new Seed(Leaf.MIDDLE_HELPERS_291F260_291FB10, middle()))) {
            JsonNode original = seed.raw().deepCopy(); JsonNode result = BattlePersonExternalCodec.normalize(seed.leaf(), seed.raw(), "fixture");
            assertEquals(original, seed.raw(), "strict validation must not mutate retained original Native JSON");
            JsonNode persisted = JSON.readTree(JSON.writeValueAsBytes(result));
            assertEquals(result, BattlePersonExternalCodec.normalize(seed.leaf(), persisted, "fixture"));
            assertEquals(result, BattlePersonContextPrefixCodec.normalize(seed.leaf(), persisted, "fixture"));
        }
        JsonNode rank = BattlePersonContextPrefixCodec.normalize(Leaf.MIDDLE_HELPERS_291F260_291FB10, middle(), "fixture")
                .path("helper_291f260").path("families").get(0);
        assertEquals(new BigInteger("-9223372036854675809"), rank.path("weight_q64").bigIntegerValue());
        assertEquals(2, rank.path("weight_key_probes").size(), "native repeated final probe is retained");
        JsonNode contexts = BattlePersonContextPrefixCodec.normalize(Leaf.MIDDLE_HELPERS_291F260_291FB10, middle(), "fixture")
                .path("helper_291fb10").path("preferred").path("rows").get(0);
        assertEquals(2, contexts.path("modifier_rows").size()); assertTrue(contexts.path("modifier_rows").get(1).path("property_block").isNull());
        assertEquals(new BigInteger("2147483647"), BattlePersonContextPrefixCodec.normalize(Leaf.TAIL_PREFIX_2753860_2922530, prefix(), "fixture")
                .path("helper_2922530").path("rows").get(2).path("selected_index_raw").bigIntegerValue());
    }

    @Test void typesMissingNullAndActualNativeAlgorithmsRejectDrift() {
        for (Leaf leaf : OWNED) assertTrue(BattlePersonExternalCodec.normalize(leaf, NullNode.instance, "fixture").isNull());
        ObjectNode missing = prefix(); missing.remove("helper_2753860"); rejects(Leaf.TAIL_PREFIX_2753860_2922530, missing);
        ObjectNode bool = prefix(); bool.put("character_id", true); rejects(Leaf.TAIL_PREFIX_2753860_2922530, bool);
        ObjectNode decimal = prefix(); decimal.put("character_id", 29829.0); rejects(Leaf.TAIL_PREFIX_2753860_2922530, decimal);
        ObjectNode overflow = prefix(); overflow.put("character_id", BigInteger.ONE.shiftLeft(31)); rejects(Leaf.TAIL_PREFIX_2753860_2922530, overflow);
        ObjectNode clamp = prefix(); object(clamp.path("helper_2922530").path("rows").get(2)).put("selected_index_raw", -1); rejects(Leaf.TAIL_PREFIX_2753860_2922530, clamp);
        ObjectNode order = middle(); object(order.path("helper_291f260").path("families").get(0)).put("native_index", 1); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, order);
        ObjectNode probe = middle(); object(probe.path("helper_291f260").path("families").get(0).path("weight_key_probes").get(1)).put("native_index", 1); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, probe);
        ObjectNode wrap = middle(); object(wrap.path("helper_291f260").path("families").get(0)).put("weight_q64", Long.MIN_VALUE); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, wrap);
        ObjectNode threshold = middle(); ((ArrayNode) threshold.path("helper_291f260").path("families").get(0).path("thresholds_consumed_q64")).add(20); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, threshold);
        ObjectNode token = middle(); object(token.path("helper_291fb10").path("preferred").path("rows").get(0).path("modifier_rows").get(1)).put("base_selection", "token_indexed"); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, token);
        ObjectNode undemanded = middle(); object(undemanded.path("helper_291fb10").path("preferred").path("rows").get(0).path("modifier_rows").get(1)).set("property_block", pc()); rejects(Leaf.MIDDLE_HELPERS_291F260_291FB10, undemanded);
    }

    @Test void sharedMappedFamilyRetainsWholeQwordMembershipAndNativeDefaultGuard() throws Exception {
        ObjectNode rite = JSON.createObjectNode(); nulls(rite, "first_key_b4_raw", "second_key_4b8_raw", "third_key_98_raw", "reason");
        rite.put("first_selection", "registry_full_id_8"); rite.put("second_selection", "native_fallback"); rite.put("third_selection", "registry_full_id_8");
        rite.put("selected_identity", "rite"); rite.put("membership_count", 1); rite.put("membership_array_present", true);
        rite.putArray("membership_identities").add("qword:0000000000000080");
        ObjectNode validatedRite = BattlePersonContextPrefixCodec.rite(rite, "rite"); assertTrue(BattlePersonContextPrefixCodec.membershipReady(validatedRite));
        ObjectNode row = JSON.createObjectNode(); row.put("native_index", 0); row.put("source_identity", "source"); row.put("key_identity", "qword:0000000000000080");
        row.put("key_magic_raw", 0); row.putNull("key_full_id_raw"); row.put("admitted", true); row.put("property_selection", "inline_nested_mapped_default_5dc21b0");
        row.putNull("mapping_native_index"); row.put("property_identity", "pc"); row.set("property_block", pc()); row.putNull("reason");
        ObjectNode family = available(); family.put("admitted", true); family.put("count", 1); family.put("array_present", true); family.putArray("rows").add(row);
        JsonNode normalized = BattlePersonContextPrefixCodec.mappedFamily(family, "mapped", validatedRite, "inline_nested_mapped_default_5dc21b0", BigInteger.TWO.negate());
        assertEquals(normalized, BattlePersonContextPrefixCodec.mappedFamily(JSON.readTree(JSON.writeValueAsBytes(normalized)), "mapped", validatedRite, "inline_nested_mapped_default_5dc21b0", BigInteger.TWO.negate()));
        assertThrows(IllegalArgumentException.class, () -> BattlePersonContextPrefixCodec.mappedFamily(family, "mapped", validatedRite, "inline_nested_mapped_default_5dc21b0", BigInteger.ZERO));
        ObjectNode changed = family.deepCopy(); object(changed.path("rows").get(0)).put("key_identity", "qword:0000000000000081");
        assertThrows(IllegalArgumentException.class, () -> BattlePersonContextPrefixCodec.mappedFamily(changed, "mapped", validatedRite, "inline_nested_mapped_default_5dc21b0", BigInteger.TWO.negate()));
    }

    @Test void completeActualOriginalProducerDifferentialAndSourceRoundtrip() throws Exception {
        String rootValue = System.getProperty("xar.repository.root"), python = System.getProperty("xar.python");
        assertNotNull(rootValue, "full migration CI must configure the actual original repository; missing is RED");
        assertNotNull(python, "full migration CI must configure the original Python test interpreter; missing is RED");
        Path root = Path.of(rootValue).toRealPath(); List<String> before = new ArrayList<>();
        for (String source : ORIGINAL_SOURCES) before.add(sha(Files.readAllBytes(root.resolve(source))));
        ObjectNode input = JSON.createObjectNode(); ArrayNode seeds = input.putArray("seeds");
        for (Seed seed : List.of(new Seed(Leaf.TAIL_PREFIX_2753860_2922530, prefix()), new Seed(Leaf.MIDDLE_HELPERS_291F260_291FB10, middle()))) {
            ObjectNode row = seeds.addObject(); row.put("leaf", seed.leaf().wire()); row.set("raw", seed.raw());
        }
        ArrayNode sources = input.putArray("sources"); ORIGINAL_SOURCES.forEach(sources::add);
        Process child = new ProcessBuilder(python, "-B", "-X", "utf8", "-c", ORIGINAL, root.toString())
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] capture;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var output = readers.submit(() -> child.getInputStream().readNBytes(MAX_CAPTURE + 1));
            try (var sink = child.getOutputStream()) { sink.write(JSON.writeValueAsBytes(input)); }
            if (!child.waitFor(Duration.ofSeconds(90).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); fail("original PERSON normalizer capture timed out");
            }
            capture = output.get(5, TimeUnit.SECONDS);
        } finally { if (child.isAlive()) child.destroyForcibly(); }
        assertEquals(0, child.exitValue()); assertTrue(capture.length > 0 && capture.length <= MAX_CAPTURE);
        JsonNode result = JSON.readTree(capture); assertTrue(result.path("cases").isArray()); Set<Leaf> seen = java.util.EnumSet.noneOf(Leaf.class);
        int accepted = 0, rejected = 0;
        for (JsonNode row : result.path("cases")) {
            Leaf leaf = Leaf.fromWire(row.path("leaf").textValue()); seen.add(leaf); JsonNode raw = row.get("raw");
            if (row.path("ok").booleanValue()) {
                JsonNode actual = BattlePersonExternalCodec.normalize(leaf, raw, "fixture"); assertEquals(row.get("normalized"), actual, leaf + " actual producer drift");
                assertEquals(actual, BattlePersonExternalCodec.normalize(leaf, JSON.readTree(JSON.writeValueAsBytes(actual)), "fixture")); accepted++;
            } else { assertThrows(IllegalArgumentException.class, () -> BattlePersonExternalCodec.normalize(leaf, raw, "fixture"), leaf + " accepted original rejection"); rejected++; }
        }
        assertEquals(Set.copyOf(OWNED), seen); assertTrue(accepted >= 12); assertTrue(rejected >= 24);
        for (int i = 0; i < ORIGINAL_SOURCES.size(); i++) {
            String source = ORIGINAL_SOURCES.get(i); assertEquals(before.get(i), result.path("source_shas").path(source).textValue());
            assertEquals(before.get(i), sha(Files.readAllBytes(root.resolve(source))), "original source changed during the differential");
        }
    }

    private record Seed(Leaf leaf, ObjectNode raw) { }
    private static void rejects(Leaf leaf, JsonNode raw) { assertThrows(IllegalArgumentException.class, () -> BattlePersonExternalCodec.normalize(leaf, raw, "fixture")); }
    private static ObjectNode object(JsonNode raw) { assertInstanceOf(ObjectNode.class, raw); return (ObjectNode) raw; }
    private static String sha(byte[] raw) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
    private static void nulls(ObjectNode row, String... names) { for (String name : names) row.putNull(name); }
    private static ObjectNode available() { ObjectNode row = JSON.createObjectNode(); row.put("status", "available"); row.put("ready", true); row.putNull("reason"); return row; }
    private static ObjectNode pc() { ObjectNode row = JSON.createObjectNode(); row.put("keys_count", 0); row.putNull("values_count"); row.putNull("keys_u16"); row.putNull("values_q64"); row.putNull("reason"); return row; }
    private static ObjectNode prefix() {
        ObjectNode helper = available(); nulls(helper, "land_field_1f8_raw", "owner_key_1e0_raw", "initial_relation_key_c8_raw", "last_character_id_18_raw", "government_selection", "government_identity", "initial_relation_selection", "initial_relation_identity");
        helper.put("first_key_158_raw", Integer.MIN_VALUE); helper.put("owner_id_160_raw", 100); helper.put("character_id_18_raw", 100);
        helper.put("land_field_1f8_raw", 0); helper.put("caller_gate_218_raw", 1); helper.put("caller_gate_218_recheck_raw", 255); helper.put("government_mode_80c_raw", 2);
        helper.put("first_selection", "registry_full_id"); helper.put("first_identity", "first"); helper.put("definition_identity", "definition");
        helper.put("definition_pointer_260_identity", "pointer"); helper.put("predicate_pointer_selection", "government_800"); helper.put("predicate_pointer_identity", "pointer");
        helper.put("owner_selection", "registry_full_id"); helper.put("owner_identity", "owner"); helper.put("property_identity", "property");
        helper.put("caller_admitted", true); helper.put("character_land_present", true); helper.put("predicate_admitted", true); helper.put("owner_admitted", true);
        helper.putNull("relation_rows"); helper.set("property_block", pc());
        ObjectNode table = available(); table.put("first_key_158_raw", 0); table.put("first_selection", "native_fallback"); table.put("first_identity", "first");
        table.put("definition_identity", "definition"); table.put("definition_magic_38_raw", new BigInteger("4744624f", 16)); table.put("admitted", true);
        table.put("type_280_raw", 2); table.put("owner_id_160_raw", 100); table.put("character_id_18_raw", 100); ArrayNode rows = table.putArray("rows");
        int[] counts = {0, 1, Integer.MIN_VALUE}, requested = {0, -1, Integer.MAX_VALUE}, selected = {-1, 0, Integer.MAX_VALUE};
        for (int i = 0; i < 3; i++) { ObjectNode row = rows.addObject(); row.put("native_index", i); row.put("admitted", true); row.put("definition_identity", "definition");
            row.put("count_214_raw", counts[i]); row.put("requested_index_228_raw", requested[i]); row.put("selected_index_raw", selected[i]);
            row.put("table_identity", "table"); row.put("property_identity", "property"); row.set("property_block", pc()); row.putNull("reason"); }
        ObjectNode result = available(); result.put("character_id", 29829); result.set("helper_2753860", helper); result.set("helper_2922530", table); return result;
    }
    private static ObjectNode middle() {
        ObjectNode rank = available(); rank.put("component_present", true); ArrayNode families = rank.putArray("families"); int[] keys = {45, 44, 46, 47};
        for (int i = 0; i < 4; i++) {
            ObjectNode row = available(); row.put("native_index", i); row.put("override_raw", -1); row.put("threshold_count", 2); row.put("rank_raw", 1); row.put("manager_count_raw", 2);
            row.put("definition_gate_raw", 1); row.putNull("weight_default_guard_raw"); row.put("weight_keys_count_raw", 1); row.put("weight_native_index", 0);
            row.put("score_q64", 7); row.put("weight_value_q64", Long.MAX_VALUE); row.put("weight_q64", new BigInteger("-9223372036854675809"));
            row.put("definition_selection", "manager_rank_index"); row.put("definition_identity", "definition"); row.put("weight_source_selection", "exact_owner_carrier_10");
            row.put("weight_source_identity", "weight"); row.put("property_identity", "property"); row.put("threshold_array_present", true); row.put("admitted", true);
            row.put("weight_carrier_present", true); row.put("weight_owner_matches", true); row.put("weight_found", true); row.putArray("thresholds_consumed_q64").add(5).add(10);
            row.put("weight_key_u16", keys[i]); ArrayNode probes = row.putArray("weight_key_probes"); for (int j = 0; j < 2; j++) { ObjectNode probe = probes.addObject(); probe.put("native_index", 0); probe.put("key_u16", keys[i]); }
            row.set("property_block", pc()); families.add(row);
        }
        ObjectNode context = available(); context.put("native_index", 0); nulls(context, "requested_full_id_raw"); context.put("full_id_raw", -2); context.put("owner_full_id_raw", 100); context.put("character_full_id_raw", 100);
        context.put("modifier_count", 2); context.put("selection", "land_1c0"); context.put("context_identity", "context"); context.put("terminal_property_identity", "terminal");
        context.put("admitted", true); context.put("owner_matches", true); context.put("modifier_array_present", true); context.put("token_array_present", true);
        context.put("magic_raw", new BigInteger("5362436f", 16)); context.set("terminal_property_block", pc()); ArrayNode modifiers = context.putArray("modifier_rows");
        for (int i = 0; i < 2; i++) { ObjectNode row = modifiers.addObject(); row.put("native_index", i); row.put("modifier_identity", "same-modifier"); row.put("token_u8", i + 1);
            row.put("modifier_count_u8", 2); row.put("base_selection", i == 0 ? "token_indexed" : "native_modifier_fallback"); row.put("property_identity", "property"); row.put("gate_raw", i == 0 ? 1 : 0);
            row.put("admitted", i == 0); if (i == 0) row.set("property_block", pc()); else row.putNull("property_block"); row.putNull("reason"); }
        ObjectNode fb10 = available(); fb10.put("land_present", true);
        for (String name : List.of("preferred", "list_218", "list_248")) { ObjectNode family = available(); family.put("header_selection", "actual-header");
            int count = name.equals("list_248") ? 0 : 1; family.put("count", count); if (name.equals("preferred")) family.putNull("array_present"); else family.put("array_present", false);
            ArrayNode rows = family.putArray("rows"); if (count == 1) rows.add(context.deepCopy()); fb10.set(name, family); }
        ObjectNode result = available(); result.put("character_id", 29829); result.set("helper_291f260", rank); result.set("helper_291fb10", fb10); return result;
    }

    private static final String ORIGINAL = """
        import sys,json,copy,runpy,hashlib,importlib
        from pathlib import Path
        root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
        incoming=json.load(sys.stdin)
        before={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in incoming['sources']}
        names={
          'later_direct_291c3fb_44c':('battle_person_later_direct_contract','normalize_later_direct_291c3fb_44c'),
          'helper_291f0a0':('battle_person_helper_291f0a0_contract','normalize_helper_291f0a0'),
          'later_helpers_291f550_291f940':('battle_person_remaining_helpers_contract','normalize_later_helpers_291f550_291f940'),
          'tail_direct_291c5b7_291cc49':('battle_person_tail_direct_contract','normalize_tail_direct_291c5b7_291cc49'),
          'tail_prefix_2753860_2922530':('battle_person_tail_prefix_contract','normalize_tail_prefix_2753860_2922530'),
          'middle_helpers_291f260_291fb10':('battle_person_middle_helpers_contract','normalize_middle_helpers_291f260_291fb10')}
        seeds=list(incoming['seeds'])
        fixture_names=[('test_battle_person_later_direct_12003.py','later_direct_291c3fb_44c'),
          ('test_battle_person_helper_291f0a0_12003.py','helper_291f0a0'),
          ('test_battle_person_remaining_helpers_12003.py','later_helpers_291f550_291f940'),
          ('test_battle_person_tail_direct_12003.py','tail_direct_291c5b7_291cc49')]
        for filename,leaf in fixture_names:
          original=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit'/filename))
          seeds.append({'leaf':leaf,'raw':original['source']()[leaf]})
        def scalar_paths(value,path=()):
          if isinstance(value,dict):
            for key,item in value.items():yield from scalar_paths(item,path+(key,))
          elif isinstance(value,list):
            for index,item in enumerate(value):yield from scalar_paths(item,path+(index,))
          else:yield path
        def set_path(value,path,new):
          for key in path[:-1]:value=value[key]
          value[path[-1]]=new
        cases=[]
        for seed in seeds:
          leaf=seed['leaf'];raw=seed['raw'];variants=[copy.deepcopy(raw),None]
          for key in list(raw)[:8]:
            missing=copy.deepcopy(raw);del missing[key];variants.append(missing)
          extra=copy.deepcopy(raw);extra['invented_field']=True;variants.append(extra)
          paths=list(scalar_paths(raw));selected=paths[:12]+paths[-12:]
          for path in selected:
            original=raw
            for key in path:original=original[key]
            wrong=(1 if type(original) is bool else True if type(original) is int else '' if type(original) is str else 1.0)
            value=copy.deepcopy(raw);set_path(value,path,wrong);variants.append(value)
          module,function=names[leaf];normalize=getattr(importlib.import_module('xar_autoplayer.bridge.'+module),function)
          for value in variants:
            original=copy.deepcopy(value);case={'leaf':leaf,'raw':value}
            try:case.update(ok=True,normalized=normalize(value,'fixture'))
            except (ValueError,TypeError,KeyError):case.update(ok=False)
            if value!=original:raise RuntimeError('actual original normalizer mutated source')
            cases.append(case)
        after={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in incoming['sources']}
        if before!=after:raise RuntimeError('actual original sources changed')
        print(json.dumps({'cases':cases,'source_shas':after},separators=(',',':'),ensure_ascii=False,allow_nan=False))
        """;
}
