package org.xar.ck3.control.application.planning.military;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Required original producer parity, including retained .3 offline callback serializer input; no live Game claim. */
final class OrdinaryWhitePeaceOriginalParityTest {
    @TempDir Path temporary;
    private static final Map<String,String> PINS = Map.of(
        "src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",
        "src/xar_autoplayer/bridge/war_declaration_continuity_v1.py", "c4c33bdee442526b0ab666670fbfab29b6971405881486440c394dd77c04cd50",
        "src/xar_autoplayer/bridge/declaration_contract.py", "b5ed2eb40f8f52298886d764259501559a551b4096ecaa839e39fa45a12e151c",
        "tests/fixtures/native_12003/defender_white_peace_g54/options-legal.json", "f1278a49f53b70258780ae33f5be4cfc9a4ff702fd49a22a7b2b676509689610",
        "tests/fixtures/native_12003/defender_white_peace_g54/fixture-context.json", "74c085531be030e3c2ea6159733e69319e463b2c76fdd3607be0ee4ebb27bb82");
    private static final String SCRIPT = """
import sys,json,copy,threading
from pathlib import Path
root=Path(sys.argv[1])/"ck3_autonomous_player"
sys.path.insert(0,str(root/"src"))
from xar_autoplayer.bridge import native_driver as n
from xar_autoplayer.bridge import war_declaration_continuity_v1 as d
input=json.load(sys.stdin)
out=[]
for item in input["policy"]:
    out.append({"snapshot":item,"war_id":23,"original":n._white_peace_readiness(item,23)})
fixture=root/"tests/fixtures/native_12003/defender_white_peace_g54"
packet=json.loads((fixture/"options-legal.json").read_text(encoding="utf-8-sig"))
leaf=packet.get("result",packet)["war_termination_options"]
ctx=json.loads((fixture/"fixture-context.json").read_text(encoding="utf-8-sig"))
war={key:leaf[key] for key in ["war_id","player_side","player_is_primary_war_leader","player_relative_war_score"]}
war["targeted_title_ids"]=[2128]
snapshot={"paused":True,"snapshot_id":"retained-offline-fixture","revision":12,"native_revision":11,
 "date_raw":ctx["date_raw"],"episode_run_id":None,"diagnostics":{"connection_generation":1},
 "played_character":{"character_id":ctx["actor_character_id"]},"active_wars":[war],"war_termination_terms":[]}
options=copy.deepcopy(leaf)
options.update(queried_snapshot_id=snapshot["snapshot_id"],queried_revision=12,queried_native_revision=11,
 queried_connection_generation=1,episode_run_id=None)
snapshot["war_termination_options"]=[options]
out.append({"snapshot":snapshot,"war_id":leaf["war_id"],"original":n._white_peace_readiness(snapshot,leaf["war_id"])})
hist=[]
for case in input["history"]:
    hist.append({"case":case,"cooldown":n._white_peace_proposal_cooldown(case["rows"],war_id=23,current_date_raw=case["date"],episode_run_id=case["episode"]),
     "fence":n._white_peace_submission_fence(case["rows"],war_id=23,episode_run_id=case["episode"],variant=case["variant"])})
decl=[]
class Driver:
    state_dir=None
    _war_declaration_continuity_loaded_v1=True
    def __init__(self,previous):
        self._driver_state_lock=threading.RLock()
        self._war_declaration_continuity_v1=previous
    def get_current_prewar_force_coalition_coverage_v2(self,declaration_id,snapshot): return None
selection={"declaration_id":"42-8--1","target_character_id":42,"casus_belli_index":8,
 "configuration_index":-1,"claimant_character_id":7,"casus_belli_key":"claim_cb","target_title_ids":[101]}
for state in input["declaration"]:
    frame=copy.deepcopy(state)
    previous=frame.get("war_declaration_continuity_v1")
    driver=Driver(previous)
    try:
        d.prepare_declaration_attempt_v1(driver,frame,selection,"source-original-request")
        allowed=True
    except ValueError:
        allowed=False
    decl.append({"snapshot":state,"allowed":allowed})
print(json.dumps({"policy":out,"history":hist,"declaration":decl},ensure_ascii=False))
""";
    @Test void originalFourBranchesCooldownFenceAndDeclarationLatchRoundTrip() throws Exception {
        Path repository = required("xar.repository.root"), python = required("xar.python"); assertTrue(Files.isRegularFile(python));
        List<Value> cases = policyCases(), histories = historyCases(), declarations = declarationCases();
        var input = new Obj(Map.of("policy", new Arr(cases), "history", new Arr(histories), "declaration", new Arr(declarations)));
        byte[] request = DriverJson.encode(input); assertTrue(request.length < 2 * 1024 * 1024);
        Path output = temporary.resolve("original-policy.stdout.json"), error = temporary.resolve("original-policy.stderr.txt");
        pin(repository); ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-c", SCRIPT, repository.toString());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectOutput(output.toFile()); builder.redirectError(error.toFile());
        Process process = builder.start(); try {
            try (var inputStream = process.getOutputStream()) { inputStream.write(request); }
            if (!process.waitFor(90, TimeUnit.SECONDS)) { process.destroyForcibly(); fail("required original white-peace policy oracle timed out"); }
            assertTrue(Files.size(output) <= 4L * 1024 * 1024 && Files.size(error) <= 16384, "bounded original producer output required");
            assertEquals(0, process.exitValue(), Files.readString(error));
            Obj original = DriverJson.object(Files.readAllBytes(output), DriverJson.MAX_NATIVE_BYTES);
            for (Value raw : OpportunityJson.array(original.get("policy"), "actual original policy cases")) {
                Obj test = OpportunityJson.object(raw, "actual original case"), snapshot = OpportunityJson.object(test.get("snapshot"), "actual policy input");
                int id = OpportunityJson.integer(test.get("war_id"), "selected war").intValueExact();
                var decision = OrdinaryWhitePeacePolicy.evaluate(snapshot, id);
                var result = OrdinaryWhitePeacePolicy.originalTuple(decision);
                assertEquals(test.get("original"), result, snapshot.toString());
                assertEquals(result, OpportunityJson.parse(OpportunityJson.encode(result)));
                var variant = decision instanceof OrdinaryWhitePeacePolicy.Ready ready ? ready.variant() : null;
                assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.DE_JURE_NO_SAFE_ROUTE,
                        org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy.deJureWhitePeace(snapshot, id));
                assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_DE_JURE || variant == OrdinaryWhitePeacePolicy.Variant.DEFENDER_MINOR_RELIGIOUS,
                        org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy.defenderProposal(snapshot, id));
                assertEquals(variant == OrdinaryWhitePeacePolicy.Variant.CLAIM_CB,
                        org.xar.ck3.control.application.planning.warexit.WarExitPolicies.claimTermsReady(snapshot, id));
                assertEquals(OrdinaryWhitePeacePolicy.needsClaimTerms(snapshot, id),
                        org.xar.ck3.control.application.planning.warexit.WarExitPolicies.claimWhitePeaceCandidate(snapshot, id));
            }
            for (Value raw : OpportunityJson.array(original.get("history"), "original history cases")) {
                Obj test = OpportunityJson.object(raw, "history comparison"), data = OpportunityJson.object(test.get("case"), "history input");
                Arr rows = (Arr) data.get("rows");
                Value cooldown = OrdinaryWarAdmissionRules.whitePeaceCooldown(rows, 23, data.get("date"), data.get("episode")).<Value>map(value -> value).orElse(Nil.INSTANCE);
                var variant = java.util.Arrays.stream(OrdinaryWhitePeacePolicy.Variant.values()).filter(value -> value.wire().equals(OpportunityJson.text(data.get("variant"), "variant"))).findFirst().orElseThrow();
                Value fence = OrdinaryWarAdmissionRules.whitePeaceFence(rows, 23, data.get("episode"), variant).<Value>map(value -> value).orElse(Nil.INSTANCE);
                assertEquals(test.get("cooldown"), cooldown); assertEquals(test.get("fence"), fence);
            }
            for (Value raw : OpportunityJson.array(original.get("declaration"), "original declaration preparation cases")) {
                Obj test = OpportunityJson.object(raw, "declaration comparison");
                Obj frame = OpportunityJson.object(test.get("snapshot"), "original declaration frame"); boolean allowed;
                try {
                    allowed = OrdinaryWarAdmissionRules.declaration(frame, List.of()) == OrdinaryWarAdmissionRules.Declaration.CLEAR;
                    if (allowed) OrdinaryWarAdmissionRules.declarationBefore(frame);
                } catch (IllegalArgumentException refused) { allowed = false; }
                assertEquals(OpportunityJson.bool(test.get("allowed"), "original preparation"), allowed);
            }
        } finally { if (process.isAlive()) process.destroyForcibly(); pin(repository); }
    }
    private static List<Value> policyCases() {
        List<Value> cases = new ArrayList<>();
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) {
            ObjectNode base = OrdinaryWhitePeacePolicyTest.frame(variant); cases.add(OrdinaryWhitePeacePolicyTest.obj(base));
            for (String flag : List.of("context_constructed", "native_validator_passed", "available")) {
                ObjectNode bad = base.deepCopy(); OrdinaryWhitePeacePolicyTest.white(bad).put(flag, false); cases.add(OrdinaryWhitePeacePolicyTest.obj(bad));
            }
            for (String flag : List.of("player_is_primary_war_leader", "cb_allows_white_peace", "active_casus_belli_present")) {
                ObjectNode bad = base.deepCopy(); OrdinaryWhitePeacePolicyTest.options(bad).put(flag, false); cases.add(OrdinaryWhitePeacePolicyTest.obj(bad));
            }
            ObjectNode stale = base.deepCopy(); OrdinaryWhitePeacePolicyTest.options(stale).put("queried_revision", 11); cases.add(OrdinaryWhitePeacePolicyTest.obj(stale));
            ObjectNode paused = base.deepCopy(); paused.put("paused", false); cases.add(OrdinaryWhitePeacePolicyTest.obj(paused));
            ObjectNode absent = base.deepCopy(); absent.putArray("active_wars"); cases.add(OrdinaryWhitePeacePolicyTest.obj(absent));
            ObjectNode missing = base.deepCopy(); missing.putArray("war_termination_options"); cases.add(OrdinaryWhitePeacePolicyTest.obj(missing));
            for (int acceptance : List.of(0, -1)) {
                ObjectNode bad = base.deepCopy(); ((ObjectNode) OrdinaryWhitePeacePolicyTest.white(bad).get("ai_acceptance")).put("raw", acceptance); cases.add(OrdinaryWhitePeacePolicyTest.obj(bad));
            }
        }
        ObjectNode missingTerms = OrdinaryWhitePeacePolicyTest.frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB); missingTerms.putArray("war_termination_terms"); cases.add(OrdinaryWhitePeacePolicyTest.obj(missingTerms));
        ObjectNode wrongClaim = OrdinaryWhitePeacePolicyTest.frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB); ((ObjectNode) wrongClaim.get("war_termination_terms").get(0).get("claims").get(0)).put("present", false); cases.add(OrdinaryWhitePeacePolicyTest.obj(wrongClaim));
        return List.copyOf(cases);
    }
    private static List<Value> historyCases() {
        List<Value> result = new ArrayList<>();
        for (var variant : OrdinaryWhitePeacePolicy.Variant.values()) for (int date : List.of(999, 1000, 1719, 1720, 5000)) {
            Obj action = OrdinaryWhitePeacePolicyTest.historyAction(23, 1000, "source-episode", "submitted_pending", "individual_county_de_jure_cb", 17);
            Obj row = new Obj(Map.of("command", new Text("offer-white-peace-23"), "ok", new Bool(true), "index", new IntegerValue(BigInteger.valueOf(4)), "result", new Obj(Map.of("war_termination_result", action))));
            result.add(new Obj(Map.of("rows", new Arr(List.of(row)), "date", new IntegerValue(BigInteger.valueOf(date)), "episode", new Text("source-episode"), "variant", new Text(variant.wire()))));
        }
        return List.copyOf(result);
    }
    private static List<Value> declarationCases() {
        List<Value> result = new ArrayList<>(); var base = OrdinaryWhitePeacePolicyTest.frame(OrdinaryWhitePeacePolicy.Variant.CLAIM_CB);
        ((ObjectNode) base.get("diagnostics")).put("bridge_pid", 123).putObject("hello").put("pid", 123);
        result.add(OrdinaryWhitePeacePolicyTest.obj(base));
        for (String status : List.of("submission_unknown", "declaration_submitted", "war_started", "native_rejected", "not_submitted")) {
            var frame = base.deepCopy(); frame.putObject("war_declaration_continuity_v1").put("schema", "war-declaration-continuity-v1").put("status", status).put("request_id", "retained-original");
            result.add(OrdinaryWhitePeacePolicyTest.obj(frame));
        }
        for (String field : List.of("duplicate", "negative", "too_large", "bool", "too_many", "zero")) {
            var frame = base.deepCopy(); var wars = frame.putArray("active_wars");
            switch (field) {
                case "duplicate" -> { wars.addObject().put("war_id", 23); wars.addObject().put("war_id", 23); }
                case "negative" -> wars.addObject().put("war_id", -1);
                case "too_large" -> wars.addObject().put("war_id", 2147483648L);
                case "bool" -> wars.addObject().put("war_id", true);
                case "too_many" -> { for (int i = 0; i < 257; i++) wars.addObject().put("war_id", i); }
                case "zero" -> wars.addObject().put("war_id", 0);
                default -> throw new IllegalStateException("finite original admission cases");
            }
            result.add(OrdinaryWhitePeacePolicyTest.obj(frame));
        }
        for (String field : List.of("actor_zero", "actor_bool", "pid_mismatch", "generation_bool", "generation_zero")) {
            var frame = base.deepCopy();
            switch (field) {
                case "actor_zero" -> ((ObjectNode) frame.get("played_character")).put("character_id", 0);
                case "actor_bool" -> ((ObjectNode) frame.get("played_character")).put("character_id", true);
                case "pid_mismatch" -> ((ObjectNode) frame.get("diagnostics").get("hello")).put("pid", 124);
                case "generation_bool" -> ((ObjectNode) frame.get("diagnostics")).put("connection_generation", true);
                case "generation_zero" -> ((ObjectNode) frame.get("diagnostics")).put("connection_generation", 0);
                default -> throw new IllegalStateException("finite original owner cases");
            }
            result.add(OrdinaryWhitePeacePolicyTest.obj(frame));
        }
        return List.copyOf(result);
    }
    private static Path required(String name) { String value = System.getProperty(name); assertNotNull(value, "required original producer input missing: " + name); Path path = Path.of(value); assertTrue(path.isAbsolute()); return path; }
    private static void pin(Path repository) throws Exception { for (var pin : PINS.entrySet()) assertEquals(pin.getValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(repository.resolve("ck3_autonomous_player").resolve(pin.getKey())))), pin.getKey()); }
}
