package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.military.combatwire.PersonSixStageCaptureCodec;

/** Original Python producers/consumers are the oracle. No generated replacement Python implementation. */
class BattlePersonSixStageCaptureParityTest {
    private record Pin(String relative, String sha256) { }
    private static final List<Pin> PINS = List.of(
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_six_stage_capture_12004.py", "84bda389a1b8f1fd1807d2a0e05b77c380f60d6eb5d9630e52aa2d11cb11d58b"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_carrier_direct_12004.py", "b77aaa18590d6620c4c6c0a36d3c94b4bd17670106276f4858282abcbd74eb84"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_context_source_inputs_contract.py", "aef31456253ca7fd5160dfd73d244bc929c4284e621ca3a638eef38515a9d245"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_context_admissions_v86_contract.py", "996131b53fac8acf58895c6aa7e0133cdb6bf3b4e347f7a8c5fb6fdc42167fef"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py", "9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_person_pc_merger_12004.py", "35d1a1c64cf189cf34cca1ea5ead4c7dfff3a8bccd472cbf112876224db62f70"),
            new Pin("ck3_autonomous_player/tests/test_battle_person_six_stage_capture_12004.py", "95a78a24f3f4b2c1b0c58720a309bd5e74e17677cc5c2302ec970865c424791d")
    );
    private enum Operation {
        QUERY, CAPTURE, SELECT, REQUESTS, OCCURRENCE, BASELINE, PREPARATION, BASES, BASE,
        PIETY, CLASSIFIED_ROW, CLASSIFIED_VALUE
    }
    private static final BigInteger REVISION = BigInteger.valueOf(23);
    private static final int DATE = 53288784;
    private static ObjectNode object(JsonNode node) { return assertInstanceOf(ObjectNode.class, node); }
    private static ObjectNode at(JsonNode node, String pointer) { return object(node.at(pointer)); }
    private static void pins() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        assertNotNull(configured, "required original source root is unavailable");
        Path root = Path.of(configured); assertTrue(root.isAbsolute()); root = root.toRealPath();
        for (Pin pin : PINS) {
            Path file = root.resolve(pin.relative()).toRealPath(); assertTrue(file.startsWith(root));
            assertTrue(Files.isRegularFile(file)); assertTrue(Files.size(file) <= 2 * 1024 * 1024);
            assertEquals(pin.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), pin.relative());
        }
    }
    private static ObjectNode call(String source, JsonNode input) throws Exception {
        pins(); ObjectNode result = BattleOriginalOracle.call(source, input); pins(); return result;
    }
    private static ObjectNode fixture() throws Exception {
        return call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'test_battle_person_six_stage_capture_12004.py'
                spec=importlib.util.spec_from_file_location('xar_retained_six_stage_fixture',path)
                fixture=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(fixture)
                print(json.dumps({'query':fixture._query(),'absent_complete':fixture._absent_pc(),'absent_partial':fixture._absent_pc(complete=False)},allow_nan=False))
                """, ArmyJson.empty());
    }
    private static ObjectNode original(Operation operation, JsonNode value, long index, long row, int mode, long character) throws Exception {
        ObjectNode input = ArmyJson.empty(); input.put("operation", operation.name()); input.set("value", value);
        input.put("index", index); input.put("row", row); input.put("mode", mode); input.put("character", character);
        input.put("revision", REVISION); input.put("date", DATE); input.putArray("characters").add(29829);
        return call("""
                import json,sys
                from xar_autoplayer.bridge import battle_person_six_stage_capture_12004 as original
                data=json.load(sys.stdin)
                op,v=data['operation'],data['value']
                try:
                    if op=='QUERY': value=original.normalize_person_six_stage_query_12004(v,expected_snapshot_revision=data['revision'],expected_observed_date_raw=data['date'],expected_character_ids=data['characters'])
                    elif op=='CAPTURE': value=original.normalize_person_six_stage_capture_12004(v)
                    elif op=='SELECT': value=original.select_person_six_stage_capture_12004(v,data['character'])
                    elif op=='REQUESTS': value=original.emit_captured_person_six_stage_requests_12004(v)
                    elif op=='OCCURRENCE': value=original.emit_captured_person_six_stage_occurrence_requests_12004(v,data['index'])
                    elif op=='BASELINE': value=original.emit_captured_person_pre_six_aggregate_12004(v)
                    elif op=='PREPARATION': value=original.emit_captured_person_preparation_model_12004(v)
                    elif op=='BASES': value=original.emit_captured_person_base_points_12004(v)
                    elif op=='BASE': value=original.emit_captured_person_base_point_12004(v,data['index'])
                    elif op=='PIETY': value=original.emit_captured_person_piety_category_12004(v,data['index'])
                    elif op=='CLASSIFIED_ROW': value=original.emit_captured_person_classified_piety_row_12004(v,data['index'],data['row'],data['mode'])
                    elif op=='CLASSIFIED_VALUE': value=original.emit_captured_person_classified_piety_value_12004(v,data['index'],data['mode'])
                    else: raise AssertionError('unknown original operation')
                    print(json.dumps({'accepted':True,'value':value},allow_nan=False))
                except (ValueError,TypeError,KeyError) as error:
                    print(json.dumps({'accepted':False,'error_type':type(error).__name__},allow_nan=False))
                """, input);
    }
    private static JsonNode java(Operation operation, JsonNode value, long index, long row, int mode, long character) {
        return switch (operation) {
            case QUERY -> BattlePersonSixStageCaptureCodec.normalize(value, "person_six_stage_captures", REVISION, DATE, List.of(29829L));
            case CAPTURE -> PersonSixStageCaptureCodec.normalize(value);
            case SELECT -> BattlePersonSixStageCaptureCodec.select(value, character);
            case REQUESTS -> BattlePersonSixStageConsumers.emitRequests(value);
            case OCCURRENCE -> BattlePersonSixStageConsumers.emitOccurrenceRequests(value, index);
            case BASELINE -> BattlePersonSixStageConsumers.emitPreSixAggregate(value);
            case PREPARATION -> BattlePersonSixStageConsumers.emitPreparationModel(value);
            case BASES -> BattlePersonSixStageConsumers.emitBasePoints(value);
            case BASE -> BattlePersonSixStageConsumers.emitBasePoint(value, index);
            case PIETY -> BattlePersonSixStageConsumers.emitPietyCategory(value, index);
            case CLASSIFIED_ROW -> BattlePersonSixStageConsumers.emitClassifiedPietyRow(value, index, row, mode);
            case CLASSIFIED_VALUE -> BattlePersonSixStageConsumers.emitClassifiedPietyValue(value, index, mode);
        };
    }
    private static void compare(Operation operation, JsonNode value, long index, long row, int mode, long character) throws Exception {
        ObjectNode original = original(operation, value, index, row, mode, character);
        if (original.get("accepted").booleanValue()) {
            JsonNode actual = java(operation, value, index, row, mode, character);
            ObjectNode envelope = ArmyJson.empty(); envelope.set("value", actual);
            byte[] encoded = ArmyJson.bytes(envelope);
            ObjectNode persisted = ArmyJson.parse(encoded);
            assertEquals(original.get("value"), persisted.get("value"), operation.name());
            assertArrayEquals(encoded, ArmyJson.bytes(persisted));
        } else assertThrows(IllegalArgumentException.class, () -> java(operation, value, index, row, mode, character), operation.name());
    }
    private static ObjectNode section(JsonNode leaf) {
        ObjectNode result = ArmyJson.empty(); result.set("character_id", leaf.get("character_id").deepCopy());
        result.set(BattlePersonSixStageCaptureCodec.CAPTURE_FIELD, leaf.deepCopy()); return result;
    }
    private static ObjectNode leaf(ObjectNode fixture) { return at(fixture, "/query/character_captures/0"); }
    @Test void originalFullQueryToUniqueCaptureNormalizerAndAllOwnedAppendConsumersRoundtrip() throws Exception {
        ObjectNode fixture = fixture(), query = at(fixture, "/query");
        compare(Operation.QUERY, query, 0, 0, 1, 29829);
        compare(Operation.SELECT, query, 0, 0, 1, 29829);
        ObjectNode section = BattlePersonSixStageCaptureCodec.select(query, 29829);
        compare(Operation.REQUESTS, section, 0, 0, 1, 29829);
        for (int index = 0; index < 6; index++) compare(Operation.OCCURRENCE, section, index, 0, 1, 29829);
        var typed = BattlePersonSixStageCaptureCodec.decode(query, "person_six_stage_captures", REVISION, DATE, List.of(29829L));
        assertEquals(Long.valueOf(29829), typed.owners().getFirst().characterId());
        assertEquals("0x12345000", typed.owners().getFirst().characterIdentity());
        assertEquals(REVISION, typed.nativeRevision()); assertEquals(DATE, typed.observedDateRaw());
        ObjectNode detached = typed.toJson(); detached.put("observed_date_raw", 1);
        assertEquals(DATE, typed.toJson().get("observed_date_raw").intValue());
        byte[] copy = typed.normalizedBytes(); copy[0] = 0; assertNotEquals(0, typed.normalizedBytes()[0]);
    }
    @Test void nullableNativeOwnerZeroHighBitAndFullRequestedOrderKeepIndependentDomains() throws Exception {
        ObjectNode fixture = fixture(), query = at(fixture, "/query");
        for (long id : new long[] {0, 0x8000_0000L, 0xffff_ffffL}) {
            ObjectNode changed = query.deepCopy(); at(changed, "/character_captures/0").put("character_id", id);
            var typed = BattlePersonSixStageCaptureCodec.decode(changed, "sidecar", REVISION, DATE, List.of(id));
            assertEquals(Long.valueOf(id), typed.owners().getFirst().characterId());
            compare(Operation.CAPTURE, changed.get("character_captures").get(0), 0, 0, 1, id);
            compare(Operation.SELECT, changed, 0, 0, 1, id);
        }
        ObjectNode empty = query.deepCopy(); empty.put("snapshot_revision", 0); empty.put("observed_date_raw", Integer.MIN_VALUE); empty.putArray("character_captures");
        assertTrue(BattlePersonSixStageCaptureCodec.decode(empty, "sidecar", BigInteger.ZERO, Integer.MIN_VALUE, List.of()).owners().isEmpty());
        ObjectNode max = query.deepCopy(); max.put("snapshot_revision", new BigInteger("18446744073709551615"));
        assertEquals(new BigInteger("18446744073709551615"), BattlePersonSixStageCaptureCodec.decode(max, "sidecar", new BigInteger("18446744073709551615"), DATE, List.of(29829L)).nativeRevision());
        ObjectNode duplicate = query.deepCopy(); ((ArrayNode) duplicate.get("character_captures")).add(duplicate.get("character_captures").get(0).deepCopy());
        assertEquals(2, BattlePersonSixStageCaptureCodec.decode(duplicate, "sidecar", REVISION, DATE, List.of(29829L, 29829L)).owners().size());
        assertThrows(IllegalArgumentException.class, () -> BattlePersonSixStageCaptureCodec.select(duplicate, 29829));
        ObjectNode unobserved = unobserved(leaf(fixture), fixture.get("absent_partial")); unobserved.putNull("character_id");
        assertNull(BattlePersonSixStageCaptureCodec.captureOwner(unobserved).characterId());
        ObjectNode invalid = query.deepCopy(); ((ArrayNode) invalid.get("character_captures")).set(0, unobserved);
        assertThrows(IllegalArgumentException.class, () -> BattlePersonSixStageCaptureCodec.normalize(invalid, "sidecar", REVISION, DATE, List.of(29829L)));
    }
    private static ObjectNode unobserved(ObjectNode leaf, JsonNode absent) {
        ObjectNode result = leaf.deepCopy(); result.put("capture_observed", false).put("capture_complete", false).put("raw_counts_ready", false).put("ready", false)
                .put("reason", "native_six_stage_unobserved").put("capture_sequence", 0);
        for (String key : List.of("capture_date_raw", "character_identity", "context_identity", "capture_thread_id", "query_thread_id", "source_return_rva")) result.putNull(key);
        for (JsonNode value : result.get("stages")) {
            ObjectNode stage = object(value); stage.put("observed", false).putNull("raw_count_i32");
            for (String kind : List.of("first", "second")) { stage.put(kind + "_append_observed", false); stage.set(kind + "_pc", absent.deepCopy()); }
        }
        return result;
    }
    @Test void originalPartialUnreadCompletedSkipAndNegativeCapturedWeightsAreNeverRecomputed() throws Exception {
        ObjectNode fixture = fixture(), capture = leaf(fixture).deepCopy();
        at(capture, "/stages/0").put("raw_count_i32", -7);
        at(capture, "/stages/0/first_pc").put("weight_q100000", -700000);
        at(capture, "/stages/0/second_pc").put("weight_q100000", -500000);
        compare(Operation.REQUESTS, section(capture), 0, 0, 1, 29829);
        ObjectNode skipped = leaf(fixture).deepCopy(); at(skipped, "/stages/0").put("first_append_observed", false).set("first_pc", fixture.get("absent_complete").deepCopy());
        compare(Operation.REQUESTS, section(skipped), 0, 0, 1, 29829);
        ObjectNode unread = leaf(fixture).deepCopy(); unread.put("ready", false).put("reason", "native_six_stage_pc_partial");
        at(unread, "/stages/0/first_pc").put("ready", false).put("reason", "pc_values_unread"); at(unread, "/stages/0/first_pc/properties").putNull("values_q64");
        compare(Operation.REQUESTS, section(unread), 0, 0, 1, 29829);
        compare(Operation.OCCURRENCE, section(unread), 0, 0, 1, 29829);
        compare(Operation.OCCURRENCE, section(unread), 1, 0, 1, 29829);
        ObjectNode none = unobserved(leaf(fixture), fixture.get("absent_partial"));
        compare(Operation.CAPTURE, none, 0, 0, 1, 29829); compare(Operation.REQUESTS, section(none), 0, 0, 1, 29829);
    }
    private static void invalidQuery(JsonNode changed) throws Exception {
        compare(Operation.QUERY, changed, 0, 0, 1, 29829);
        assertThrows(IllegalArgumentException.class, () -> java(Operation.QUERY, changed, 0, 0, 1, 29829));
    }
    @Test void queryProducerRejectsAllWrongFieldsTokenDomainsAndSourceOrderDrift() throws Exception {
        ObjectNode query = at(fixture(), "/query");
        for (String name : List.of("schema", "snapshot_revision", "observed_date_raw", "character_captures")) {
            ObjectNode missing = query.deepCopy(); missing.remove(name); invalidQuery(missing);
            ObjectNode nullValue = query.deepCopy(); nullValue.putNull(name); invalidQuery(nullValue);
        }
        ObjectNode unknown = query.deepCopy(); unknown.put("inferred_ready", true); invalidQuery(unknown);
        for (String name : List.of("snapshot_revision", "observed_date_raw")) for (JsonNode wrong : List.of(BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("23.0")), TextNode.valueOf("23"))) {
            ObjectNode changed = query.deepCopy(); changed.set(name, wrong); invalidQuery(changed);
        }
        ObjectNode stale = query.deepCopy(); stale.put("snapshot_revision", 24); invalidQuery(stale);
        ObjectNode drift = query.deepCopy(); at(drift, "/character_captures/0").put("character_id", 29830); invalidQuery(drift);
        ObjectNode nullLeaf = query.deepCopy(); ((ArrayNode) nullLeaf.get("character_captures")).set(0, NullNode.instance); invalidQuery(nullLeaf);
        assertThrows(IllegalArgumentException.class, () -> BattlePersonSixStageCaptureCodec.decode(query, "sidecar", REVISION, DATE, List.of(-1L)));
        assertThrows(IllegalArgumentException.class, () -> BattlePersonSixStageCaptureCodec.decode(query, "sidecar", REVISION, DATE, List.of(0x1_0000_0000L)));
    }
    private static ObjectNode rich(ObjectNode source) {
        ObjectNode leaf = source.deepCopy();
        for (String key : List.of("pre_six_aggregate", "post_six_aggregate")) {
            ObjectNode aggregate = leaf.putObject(key); aggregate.put("observed", true).put("context_pc_offset", 0x68)
                    .put("source_stage", key.startsWith("pre_") ? "before_first_count_callback" : "same_thread_capture_completion");
            ObjectNode pc = aggregate.putObject("pc"); pc.put("ready", true).putNull("reason"); pc.put("admitted", true).put("identity", "0x22345078").put("count_i32", 0).putNull("weight_q100000");
            ObjectNode properties = pc.putObject("properties"); properties.putArray("keys_u16"); properties.putArray("values_q64");
        }
        leaf.put("aggregate_postimage_inputs_ready", true).put("aggregate_postimage_comparison_ready", true);
        ObjectNode preparation = leaf.putObject("preparation_model"); preparation.put("observed", true).put("ready", true).putNull("reason");
        preparation.put("model_identity", "0x22345000").put("owner_character_identity", "0x12345000").put("owner_character_id", 29829).put("owner_matches_capture", true)
                .put("context_offset", 16).put("owner_offset", 8).put("source_stage", "before_first_count_callback");
        ObjectNode base = leaf.putObject("base_point_inputs"); base.put("source_stage", "before_each_original_count").put("character_offset", 0xc0).put("stride_bytes", 4).put("ready", true).putNull("reason");
        ArrayNode observed = base.putArray("observed"), points = base.putArray("values_i32"); for (int index = 0; index < 6; index++) { observed.add(true); points.add(index + 1); }
        ObjectNode piety = leaf.putObject("piety_category_inputs"); piety.put("source_stage", "before_each_original_count").put("getter_rva", 0x28be0b0).put("key_table_rva", 0x4807608)
                .put("key_stride_bytes", 8).put("character_extension_offset", 0x1b0).put("score_offset", 0x118).put("cap_offset", 0x120)
                .put("threshold_pointer_rva", 0x54582d8).put("threshold_count_rva", 0x54582e4);
        ObjectNode classified = leaf.putObject("classified_piety_inputs"); classified.put("source_stage", "before_each_original_count").put("context_rows_offset", 0).put("context_count_offset", 12)
                .put("row_stride_bytes", 16).put("row_pc_offset", 0).put("row_scale_offset", 8).put("classified_reader_rva", 0x2438980).put("key_lookup_rva", 0x23036e0);
        ArrayNode categories = piety.putArray("stages"), stages = classified.putArray("stages");
        for (int index = 0; index < 6; index++) {
            ObjectNode category = categories.addObject(); category.put("index", index).put("observed", true).put("ready", true).putNull("reason");
            category.put("property_key_u16", 97).put("extension_identity", "0x1000").put("score_q64", "200000").put("cap_i32", -1).put("threshold_count_i32", 2).put("category_i32", 1);
            category.putArray("thresholds_used_q64").add("100000").add("300000");
            ObjectNode stage = stages.addObject(); stage.put("index", index).put("observed", true).put("ready", true).putNull("reason");
            stage.put("property_key_u16", 97).put("row_count_i32", 3).put("row_array_identity", "0x9000"); ArrayNode rows = stage.putArray("rows");
            for (int row = 0; row < 3; row++) {
                ObjectNode entry = rows.addObject(); entry.put("native_index", row).put("ready", true).putNull("reason");
                entry.put("pc_identity", "0x8000").put("pc_count_i32", 1).put("lookup_selection", row == 2 ? "absent" : "mapped");
                if (row == 2) entry.putNull("selected_index_u32"); else entry.put("selected_index_u32", 0);
                entry.put("raw_value_q64", row == 0 ? "9223372036854775799" : row == 1 ? "-9223372036854775799" : "0").put("scale_q64", "100000");
            }
        }
        return leaf;
    }
    @Test void wholeOptionalPreparationBasePietyAndClassifiedConsumersMatchActualOriginalProducers() throws Exception {
        ObjectNode capture = rich(leaf(fixture())); compare(Operation.CAPTURE, capture, 0, 0, 1, 29829);
        ObjectNode section = section(capture);
        for (Operation operation : List.of(Operation.REQUESTS, Operation.BASELINE, Operation.PREPARATION, Operation.BASES)) compare(operation, section, 0, 0, 1, 29829);
        for (int index = 0; index < 6; index++) {
            compare(Operation.BASE, section, index, 0, 1, 29829); compare(Operation.PIETY, section, index, 0, 1, 29829);
            for (int mode : List.of(1, 2)) {
                compare(Operation.CLASSIFIED_VALUE, section, index, 0, mode, 29829);
                for (int row = 0; row < 3; row++) compare(Operation.CLASSIFIED_ROW, section, index, row, mode, 29829);
            }
        }
        ObjectNode unavailable = capture.deepCopy(); at(unavailable, "/base_point_inputs").put("ready", false).put("reason", "base_point_unread");
        ((ArrayNode) unavailable.at("/base_point_inputs/values_i32")).set(0, NullNode.instance);
        compare(Operation.BASES, section(unavailable), 0, 0, 1, 29829); compare(Operation.BASE, section(unavailable), 1, 0, 1, 29829);
    }
    @Test void suppliedCaptureMetadataAndNestedSemanticFailuresReachTheSameSharedLeaf() throws Exception {
        ObjectNode base = leaf(fixture());
        List<ObjectNode> invalid = new ArrayList<>();
        ObjectNode caller = base.deepCopy(); caller.put("source_return_rva", "0x291ebef"); invalid.add(caller);
        ObjectNode thread = base.deepCopy(); thread.put("query_thread_id", 4243); invalid.add(thread);
        ObjectNode scope = base.deepCopy(); scope.put("full_helper_ready", true); invalid.add(scope);
        ObjectNode order = base.deepCopy(); at(order, "/stages/0").put("index", 1); invalid.add(order);
        ObjectNode decimal = base.deepCopy(); ((ArrayNode) decimal.at("/stages/0/first_pc/properties/values_q64")).set(0, TextNode.valueOf("1.0")); invalid.add(decimal);
        ObjectNode overflow = base.deepCopy(); ((ArrayNode) overflow.at("/stages/0/first_pc/properties/values_q64")).set(0, TextNode.valueOf("9223372036854775808")); invalid.add(overflow);
        for (String key : List.of("capture_sequence", "capture_date_raw", "character_id", "capture_thread_id", "query_thread_id"))
            for (JsonNode wrong : List.of(BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("1.0")), TextNode.valueOf("1"))) {
                ObjectNode changed = base.deepCopy(); changed.set(key, wrong); invalid.add(changed);
            }
        ObjectNode model = rich(base); at(model, "/preparation_model").put("owner_character_id", 30111); invalid.add(model);
        ObjectNode category = rich(base); at(category, "/piety_category_inputs/stages/0").put("category_i32", 2); invalid.add(category);
        ObjectNode mapped = rich(base); at(mapped, "/classified_piety_inputs/stages/0/rows/0").put("selected_index_u32", 1); invalid.add(mapped);
        ObjectNode extra = rich(base); at(extra, "/classified_piety_inputs/stages/0/rows/0").put("requested_effect_ready", true); invalid.add(extra);
        for (ObjectNode changed : invalid) {
            compare(Operation.CAPTURE, changed, 0, 0, 1, 29829);
            assertThrows(IllegalArgumentException.class, () -> PersonSixStageCaptureCodec.normalize(changed));
        }
        ObjectNode lowercase = base.deepCopy(); lowercase.put("executable_sha256", lowercase.get("executable_sha256").textValue().toLowerCase(Locale.ROOT));
        compare(Operation.CAPTURE, lowercase, 0, 0, 1, 29829);
    }
    @Test void exactSignedMaximumKernelAndNativeDivideFeedTheRealClassifiedConsumer() throws Exception {
        ObjectNode inputs = ArmyJson.empty(); ArrayNode values = inputs.putArray("values");
        for (long value : new long[] {Long.MIN_VALUE, Long.MAX_VALUE, -100001, -100000, -99999, -1, 0, 1, 99999, 100000, 100001}) values.add(value);
        ObjectNode original = call("""
                import json,sys
                from xar_autoplayer.simulation.battle_person_pc_merger_12004 import _divide_q_from_instructions,native_fixed_mul_q_12004
                values=json.load(sys.stdin)['values']
                print(json.dumps({'divide':[_divide_q_from_instructions(v) for v in values],
                    'pairs':[[a,b,native_fixed_mul_q_12004(a,b)] for a in values for b in values]},allow_nan=False))
                """, inputs);
        for (int index = 0; index < values.size(); index++) assertEquals(original.get("divide").get(index).longValue(), values.get(index).longValue() / 100000L);
        for (JsonNode row : original.get("pairs")) assertEquals(row.get(2).longValue(), BattleRecipientArithmetic.uncachedFixedMultiplyQ64(row.get(0).longValue(), row.get(1).longValue()));
        ObjectNode capture = rich(leaf(fixture())); at(capture, "/classified_piety_inputs/stages/0/rows/1").put("raw_value_q64", "9223372036854775799");
        compare(Operation.CLASSIFIED_VALUE, section(capture), 0, 0, 1, 29829);
    }
}
