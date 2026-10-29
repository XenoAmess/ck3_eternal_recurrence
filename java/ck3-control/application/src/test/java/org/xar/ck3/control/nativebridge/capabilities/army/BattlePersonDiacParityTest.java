package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Executes the complete unchanged original tests, captures their actual producers, then consumes in Java. */
final class BattlePersonDiacParityTest {
    private static final String PROGRAM = """
            import contextlib,copy,dataclasses,hashlib,io,json,runpy,sys
            from pathlib import Path
            root=Path(sys.argv[1]);sys.dont_write_bytecode=True
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'ck3_autonomous_player/tests/unit'))
            pins={
              'bridge/battle_context_source_inputs_contract.py':'aef31456253ca7fd5160dfd73d244bc929c4284e621ca3a638eef38515a9d245',
              'bridge/battle_terminal_transition_contract.py':'f8a0c5d4513eee9a0c918dfa244b72613f13479b2d2ecb68c225f02847dd81db',
              'bridge/battle_person_rule43_diac_contract.py':'25a18e45461c73b331d8835c6224e5155ca3ea4128ed4beb408f07c31c3641ef',
              'simulation/battle_person_rule43_diac_12003.py':'65fcd9e90f5f92837b231149780227a9ffcee3de7187a4f919e9a1cd66e7dcaa',
              'bridge/battle_person_diac_literal_numeric_contract.py':'a220d26106f8335521ff57b01cc44738df54ef1a066ada7e1e58e1ddc10b3fc9',
              'simulation/battle_person_diac_literal_numeric_12003.py':'b2293108e3c7beab864cea7e4995da5ce280879b87000b879a3063a2f1c8813b',
              'simulation/battle_trait_numeric_inputs_12003.py':'ae974dd51678fec9f05ea40c4991de30678ca356d30df298b97b88bb92a1810a',
              'simulation/battle_context_preparation_branch_291e210_12003.py':'70de9b44bcbc9f82d26d787abf408deef99cbf1d84e4a60645b56d61879e9cb6'}
            testpins={'test_battle_person_diac_literal_numeric_12003.py':'a82adbaa275ea8b8cb3af4953da8b497edb4faa1d4dc7ab68a0ab8644f913173','test_rule43_integrated_current_person_12003.py':'fdf14bd27f62d96e6eea9785ce160a37410378d03d008d8ec9432f6166a0d6f6'}
            def verify():
                for name,pin in pins.items():assert hashlib.sha256((root/'ck3_autonomous_player/src/xar_autoplayer'/name).read_bytes()).hexdigest()==pin,name
                for name,pin in testpins.items():assert hashlib.sha256((root/'ck3_autonomous_player/tests/unit'/name).read_bytes()).hexdigest()==pin,name
            verify()
            from xar_autoplayer.bridge.battle_person_rule43_diac_contract import normalize_following_diac_2920d60 as direct_rule
            from xar_autoplayer.simulation.battle_person_rule43_diac_12003 import emit_following_diac_2920d60_requests_12003,first_rule43_unknown_node_12003
            from xar_autoplayer.simulation.battle_person_diac_literal_numeric_12003 import emit_diac_literal_numeric_requests_12003,emit_diac_literal_numeric_row_requests_12003
            def requests(fn):
                try:return {'accepted':True,'requests':[dataclasses.asdict(value) for value in fn()]}
                except ValueError as error:return {'accepted':False,'error_type':type(error).__name__}
            numeric=[]
            module=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_battle_person_diac_literal_numeric_12003.py'))
            test=module['test_diac_literal_actual_quantization_flags_extremes_duplicates_empty_dynamic_and_scope_address'];g=test.__globals__;original=g['normalize']
            def capture_numeric(raw):
                record={'raw':copy.deepcopy(raw)};numeric.append(record)
                try:normalized=original(raw)
                except ValueError as error:record.update(accepted=False,error_type=type(error).__name__);raise
                record.update(accepted=True,normalized=copy.deepcopy(normalized),whole=requests(lambda:emit_diac_literal_numeric_requests_12003(normalized)),rows=[requests(lambda i=i:emit_diac_literal_numeric_row_requests_12003(normalized,i)) for i in range(len(normalized['declarations']))])
                return normalized
            g['normalize']=capture_numeric
            with contextlib.redirect_stdout(io.StringIO()):test()
            rules=[]
            module=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_rule43_integrated_current_person_12003.py'))
            test=module['Rule43IntegratedCurrentPerson12003Tests']('test_current_query_closed_branches_and_first_unknown');g=test.test_current_query_closed_branches_and_first_unknown.__globals__;original_rule=g['normalize']
            def capture_rule(raw):
                record={'raw':copy.deepcopy(raw)};rules.append(record)
                try:normalized=direct_rule(raw)
                except ValueError as error:record.update(accepted=False,error_type=type(error).__name__)
                else:
                    primary_rule=normalized['primary']['rule'];record.update(accepted=True,normalized=copy.deepcopy(normalized),whole=requests(lambda:emit_following_diac_2920d60_requests_12003(normalized)),unknown=None if primary_rule is None else first_rule43_unknown_node_12003(primary_rule))
                try:section=original_rule(raw)
                except ValueError:record['actual_parent_accepted']=False;raise
                record['actual_parent_accepted']=True;record['section']=copy.deepcopy(section);return section
            g['normalize']=capture_rule
            with contextlib.redirect_stdout(io.StringIO()):test.test_current_query_closed_branches_and_first_unknown()
            # Additional inputs are built with unchanged existing fixture helpers;
            # all normalization, recursive evaluation and requests are original.
            base=module['leaf']();reference=module['node'](slotc8_rva=0x3730940,slot60_rva=0x9CFEE0,children_count_raw=None,children_array_present=None,reference_arguments_count_raw=0,reference_compare_raw=2,nested_present=False,result=False)
            base['primary']['rule']=module['rule'](result=False,nodes=[reference]);base['current_character_full_id_raw']=module['ACTOR'];base['secondary']=module['selection'](owner_matches=True);base.update(selected_family='secondary_658',numeric_inputs=module['numeric']())
            capture_rule(base)
            mismatch=copy.deepcopy(base);mismatch['secondary'].update(diac_owner_full_id_raw=module['ACTOR']+1,owner_matches=False,rule=None);mismatch.update(selected_family='none',numeric_inputs=None);capture_rule(mismatch)
            owner_unknown=copy.deepcopy(base);owner_unknown.update(status='partial',ready=False,reason='owner_DWORD_unread',current_character_full_id_raw=None,selected_family=None,numeric_inputs=None);owner_unknown['secondary']['owner_matches']=None;capture_rule(owner_unknown)
            root_unknown=module['leaf']();root_unknown['primary']['rule']=module['rule'](nodes=[],result=None,reason='rule_node_unread');root_unknown.update(status='partial',ready=False,reason='rule_node_unread',selected_family=None,numeric_inputs=None);capture_rule(root_unknown)
            verify();print(json.dumps({'producer':'unchanged-complete-original-Diac-tests-and-native-contracts','original_tests_executed':2,'numeric':numeric,'rules':rules},separators=(',',':')))
            """;
    private static JsonNode saved;
    private static synchronized JsonNode corpus() throws Exception {
        if (saved != null) return saved;
        String configuredRoot = System.getProperty("xar.repository.root"), configuredPython = System.getProperty("xar.python"); assertNotNull(configuredRoot, "actual repository required; no skip"); assertNotNull(configuredPython, "actual compatible Python required; no skip");
        Path root = Path.of(configuredRoot), python = Path.of(configuredPython); assertTrue(root.isAbsolute() && Files.isDirectory(root)); assertTrue(python.isAbsolute() && Files.isRegularFile(python));
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-X", "utf8", "-c", PROGRAM, root.toString()).directory(root.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        FutureTask<byte[]> stdout = new FutureTask<>(() -> process.getInputStream().readNBytes(1024 * 1024 + 1)), stderr = new FutureTask<>(() -> process.getErrorStream().readNBytes(8193)); Thread.ofVirtual().start(stdout); Thread.ofVirtual().start(stderr);
        try { process.getOutputStream().close(); assertTrue(process.waitFor(45, TimeUnit.SECONDS), "actual original Diac producer timed out"); byte[] out = stdout.get(5, TimeUnit.SECONDS), err = stderr.get(5, TimeUnit.SECONDS); assertEquals(0, process.exitValue(), new String(err, StandardCharsets.UTF_8)); assertTrue(out.length <= 1024 * 1024 && err.length <= 8192); saved = StrictJson.parse(out, 1024 * 1024); return saved; }
        finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
    }
    private static void equalJson(JsonNode expected, JsonNode actual) { assertArrayEquals(StrictJson.canonical(expected, 1024 * 1024), StrictJson.canonical(actual, 1024 * 1024)); }
    private static ArrayNode requests(List<BattlePersonDiacNumericCodec.Request> rows) { ArrayNode result = BattleContextJson.list(); rows.forEach(r -> result.add(r.toJson())); return result; }
    @Test void actualCompleteNumericProducerRowsQuantizationAndPartialEmissionMatch() throws Exception {
        JsonNode corpus = corpus(); assertEquals(2, corpus.path("original_tests_executed").intValue()); assertTrue(corpus.path("numeric").size() >= 12);
        for (JsonNode row : corpus.get("numeric")) {
            if (!row.path("accepted").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.decode(row.get("raw"))); continue; }
            var normalized = BattlePersonDiacNumericCodec.decode(row.get("raw")); equalJson(row.get("normalized"), normalized.toJson());
            if (row.path("whole").path("accepted").booleanValue()) equalJson(row.path("whole").get("requests"), requests(BattlePersonDiacNumericCodec.emit(normalized))); else assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.emit(normalized));
            for (int i = 0; i < row.path("rows").size(); i++) { final int index = i; JsonNode expected = row.path("rows").get(i); if (expected.path("accepted").booleanValue()) equalJson(expected.get("requests"), requests(BattlePersonDiacNumericCodec.emitRow(normalized, i))); else assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.emitRow(normalized, index)); }
            equalJson(normalized.toJson(), BattlePersonDiacNumericCodec.normalize(StrictJson.parse(StrictJson.canonical(normalized.toJson(), 1024 * 1024), 1024 * 1024)));
            assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.emitRow(normalized, -1)); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.emitRow(normalized, normalized.declarations().size()));
        }
    }
    @Test void completeActualParentProducerFeedsUniqueLateFacadeRecursiveRuleAndEmission() throws Exception {
        int accepted = 0, unknown = 0, secondary = 0;
        for (JsonNode row : corpus().get("rules")) {
            if (!row.path("accepted").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(row.get("raw"), "following_diac_2920d60")); continue; }
            var following = BattlePersonDiacCodec.decode(row.get("raw"), "following_diac_2920d60").orElseThrow();
            equalJson(row.get("normalized"), following.toJson());
            equalJson(row.get("normalized"), BattlePersonExternalCodec.normalize(BattlePersonExternalCodec.Leaf.FOLLOWING_DIAC_2920D60, row.get("raw"), "following_diac_2920d60"));
            if (row.path("whole").path("accepted").booleanValue()) equalJson(row.path("whole").get("requests"), requests(BattlePersonDiacCodec.emit(following))); else { assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.emit(following)); unknown++; }
            JsonNode seam = following.primary().rule().flatMap(BattlePersonDiacCodec::firstUnknownNode).<JsonNode>map(BattlePersonDiacCodec.UnknownOccurrence::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance); equalJson(row.get("unknown"), seam);
            if (row.path("actual_parent_accepted").booleanValue() && row.path("whole").path("accepted").booleanValue()) equalJson(row.path("whole").get("requests"), requests(BattlePersonDiacCodec.emitFromCurrentSourceInputs(row.get("section"))));
            equalJson(following.toJson(), BattlePersonDiacCodec.normalize(StrictJson.parse(StrictJson.canonical(following.toJson(), 1024 * 1024), 1024 * 1024), "following_diac_2920d60"));
            if (following.selectedFamily().equals(Optional.of(BattlePersonDiacCodec.Family.SECONDARY_658))) secondary++; accepted++;
        }
        assertTrue(accepted >= 10 && unknown >= 3 && secondary >= 1);
    }
    @Test void strictNativeWidthsTypesVerdictsOccurrencePathsAndUndemandedReadsReject() throws Exception {
        ObjectNode base = corpus().get("rules").get(0).get("raw").deepCopy();
        for (String key : List.of("character_id", "current_character_full_id_raw")) for (String invalid : List.of("true", "29829.0", "\"29829\"", "2147483648")) { ObjectNode bad = base.deepCopy(); bad.set(key, StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8))); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(bad, "following_diac_2920d60")); }
        ObjectNode wrongVerdict = base.deepCopy(); ((ObjectNode) wrongVerdict.path("primary").path("rule").path("nodes").get(0)).put("result", false); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(wrongVerdict, "following_diac_2920d60"));
        ObjectNode wrongPath = base.deepCopy(); ((ObjectNode) wrongPath.path("primary").path("rule").path("nodes").get(0)).put("path", "other-native-occurrence"); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(wrongPath, "following_diac_2920d60"));
        for (String key : List.of("status", "ready", "reason", "primary", "secondary", "selected_family", "numeric_inputs")) { ObjectNode missing = base.deepCopy(); missing.remove(key); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(missing, "following_diac_2920d60")); }
        ObjectNode extra = base.deepCopy(); extra.put("rule43_ready_override", true); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(extra, "following_diac_2920d60"));
        ObjectNode secondaryAfterAccepted = base.deepCopy(); secondaryAfterAccepted.set("secondary", base.get("primary").deepCopy()); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(secondaryAfterAccepted, "following_diac_2920d60"));
        ObjectNode numeric = corpus().get("numeric").get(0).get("raw").deepCopy();
        for (String invalid : List.of("true", "1.0", "18446744073709551615", "\"0\"")) { ObjectNode malformed = numeric.deepCopy(); ((ObjectNode) malformed.path("declarations").get(0)).set("scale_gate_280_raw", StrictJson.parse(invalid.getBytes(StandardCharsets.UTF_8))); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacNumericCodec.decode(malformed)); }
        ObjectNode literalRva = base.deepCopy(); ((ObjectNode) literalRva.path("primary").path("rule").path("nodes").get(0)).put("slot58_rva", "0x855ab0"); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(literalRva, "following_diac_2920d60"));
        assertTrue(BattlePersonDiacCodec.normalize(com.fasterxml.jackson.databind.node.NullNode.instance, "following_diac_2920d60").isNull()); assertThrows(IllegalArgumentException.class, () -> BattlePersonDiacCodec.normalize(null, "following_diac_2920d60"));
    }
    @Test void literalQuantizationUsesSignedDivisionAndWrap32WithNoNumericRounding() {
        BigInteger q = BigInteger.valueOf(100_000);
        assertEquals(new BigInteger("70231305300000"), BattlePersonDiacNumericCodec.quantize(BigInteger.valueOf(Long.MIN_VALUE), 0, Optional.of(0)));
        assertEquals(new BigInteger("-214748364800000"), BattlePersonDiacNumericCodec.quantize(new BigInteger("214748364899999"), 0, Optional.of(2)));
        assertEquals(q.negate(), BattlePersonDiacNumericCodec.quantize(BigInteger.valueOf(-199_999), 0, Optional.of(0)));
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE), BattlePersonDiacNumericCodec.quantize(BigInteger.valueOf(Long.MAX_VALUE), 0, Optional.of(3)));
        assertEquals(BigInteger.valueOf(-150_000), BattlePersonDiacNumericCodec.quantize(BigInteger.valueOf(-150_000), 7, Optional.empty()));
    }
}
