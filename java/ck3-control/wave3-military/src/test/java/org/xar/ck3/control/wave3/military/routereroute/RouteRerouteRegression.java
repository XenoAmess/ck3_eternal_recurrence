package org.xar.ck3.control.wave3.military.routereroute;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.*;

/** Standalone finite regression and exact original-source differential. The domain never imports this runner. */
public final class RouteRerouteRegression {
    private static int assertions;
    private RouteRerouteRegression() { }
    private static final String ORIGINAL = """
import ast,json,pathlib,sys
chosen={
 sys.argv[1]:{'_fresh_move_route_preview','_same_frame_readonly_result_lease','_effective_command',
 '_effective_command_result','_history_after_latest_restore','_successful_merge_barrier'},
 sys.argv[2]:{'parse_preview_move_army_step','parse_merge_armies_step'},
 sys.argv[3]:{'canonical_public_cunit_decimal'}}
nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
for name,wanted in chosen.items():
 source=pathlib.Path(name).read_text(encoding='utf-8'); tree=ast.parse(source,filename=name)
 selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in wanted]
 if {n.name for n in selected}!=wanted:raise RuntimeError('original callable closure missing')
 nodes.extend(selected)
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
 '<exact-original-route-callable-closure>','exec'),ns)
cases=json.load(sys.stdin); outputs=[]
for case in cases:
 outputs.append(ns['_fresh_move_route_preview'](case['commands'],army_id=case['army_id'],
 origin_province_id=case['origin_province_id'],target_province_id=case['target_province_id'],
 date_raw=case['date_raw'],snapshot=case['snapshot']))
json.dump(outputs,sys.stdout,ensure_ascii=False,separators=(',',':'),allow_nan=False)
""";
    public static void main(String[] args) throws Exception {
        if (args.length != 1) { throw new IllegalArgumentException("one exact regression manifest required"); }
        Path manifestPath = Path.of(args[0]); byte[] manifestRaw = Files.readAllBytes(manifestPath);
        JsonNode manifest = StrictJson.parse(manifestRaw, 65_536);
        List<Source> sources = sources(manifest); verify(sources);
        Path repo = Path.of(text(manifest, "repository")); Path python = Path.of(text(manifest, "python"));
        Path stock = Path.of(text(manifest, "stock_defines"));
        String stockSha = text(manifest, "stock_sha256");
        StockRules rules = StockRouteRuleReader.read(stock, stockSha);
        List<ObjectNode> cases = cases();
        ArrayNode input = StrictJson.object().putArray("unused"); cases.forEach(input::add);
        byte[] expectedRaw = original(python, repo, caseBytes(input));
        EvidenceJson.Value expectedDocument = EvidenceJson.parse(expectedRaw);
        if (!(expectedDocument instanceof EvidenceJson.ArrayValue expected)) { throw new AssertionError("original result array required"); }
        check(expected.values().size() == cases.size(), "every original case returned");
        for (int index = 0; index < cases.size(); index++) {
            byte[] raw = caseBytes(cases.get(index));
            byte[] actual = RoutePreviewConsumerCodec.project(raw);
            check(expected.values().get(index).equals(EvidenceJson.parse(actual)), "source-bound complete preview parity " + index);
        }
        wrongTokens(); costs(rules); consumersAndInvalidation(); halt();
        verify(sources); check(java.util.Arrays.equals(manifestRaw, Files.readAllBytes(manifestPath)), "manifest unchanged");
        ObjectNode result = StrictJson.object();
        result.put("schema", "xar.route-reroute-regression/v1"); result.put("machine_id", text(manifest, "machine_id"));
        result.put("observed_at_utc", Instant.now().toString()); result.put("status", "PASS");
        result.put("source_bound_original_cases", cases.size()); result.put("assertions", assertions);
        result.put("original_callable_count", 9); result.put("source_postcheck", "MATCH");
        result.put("manifest_sha256", StockRouteRuleReader.sha256(manifestRaw)); result.put("stock_source_sha256", stockSha);
        result.put("consumer", "RouteReroutePolicy.selectRanked -> freshPreview -> typed original history closure");
        result.put("live_host_adoption", false); result.put("game_actions", 0); result.put("driver_save_body_reads", 0);
        result.put("combat_probability_known", false);
        Files.write(Path.of(text(manifest, "result_path")), StrictJson.canonical(result), StandardOpenOption.CREATE_NEW);
        System.out.println("PASS original=" + cases.size() + " assertions=" + assertions);
    }
    private record Source(Path path, long bytes, String sha256) { }
    private static List<Source> sources(JsonNode manifest) {
        List<Source> result = new ArrayList<>();
        for (JsonNode source : manifest.get("sources")) {
            result.add(new Source(Path.of(text(source, "path")), StrictJson.integer(source.get("bytes"), 1, 2_097_152), text(source, "sha256")));
        }
        return List.copyOf(result);
    }
    private static void verify(List<Source> sources) throws IOException {
        for (Source source : sources) {
            if (Files.isSymbolicLink(source.path()) || !Files.isRegularFile(source.path(), java.nio.file.LinkOption.NOFOLLOW_LINKS)
                    || Files.size(source.path()) != source.bytes()
                    || !StockRouteRuleReader.sha256(Files.readAllBytes(source.path())).equals(source.sha256())) {
                throw new IOException("exact source drift: " + source.path());
            }
        }
    }
    private static byte[] original(Path python, Path repo, byte[] input) throws Exception {
        Process process = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", ORIGINAL,
                repo.resolve("ck3_autonomous_player/src/xar_autoplayer/strategy.py").toString(),
                repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py").toString(),
                repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py").toString())
                .redirectErrorStream(true).start();
        try {
            try (var stdin = process.getOutputStream()) { stdin.write(input); }
            byte[] output = process.getInputStream().readNBytes(262_145);
            if (output.length > 262_144 || !process.waitFor(30, TimeUnit.SECONDS) || process.exitValue() != 0) {
                throw new IOException("original source differential failed: " + new String(output, StandardCharsets.UTF_8));
            }
            return output;
        } finally {
            if (process.isAlive()) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); }
        }
    }
    private static List<ObjectNode> cases() {
        List<ObjectNode> result = new ArrayList<>();
        ObjectNode available = row(2, 9, "available", "[3,9]");
        result.add(request(List.of(available)));
        result.add(request(List.of()));
        ObjectNode deferred = row(2, 9, "deferred", "[false]");
        result.add(request(List.of(deferred)));
        ObjectNode date = available.deepCopy(); date.withObject("/result/route_preview").put("previewed_date_raw", 41);
        result.add(request(List.of(available, date)));
        ObjectNode origin = available.deepCopy(); origin.withObject("/result/route_preview").put("origin_province_id", 4);
        result.add(request(List.of(origin)));
        ObjectNode failed = available.deepCopy(); failed.put("ok", false); result.add(request(List.of(available, failed)));
        ObjectNode malformed = available.deepCopy(); malformed.withObject("/result/route_preview").set("route_province_ids", parse("[3,true,9]"));
        result.add(request(List.of(available, malformed)));
        ObjectNode empty = row(2, 9, "available", "[]"); result.add(request(List.of(empty)));
        ObjectNode wrongLease = available.deepCopy(); wrongLease.withObject("/result").put("queried_revision", 8);
        result.add(request(List.of(available, wrongLease)));
        ObjectNode restore = parseObject("{\"command\":\"restore-checkpoint\",\"ok\":true}");
        result.add(request(List.of(available, restore))); result.add(request(List.of(restore, available)));
        ObjectNode merge = parseObject("{\"command\":\"merge-armies-2-with-4\",\"ok\":true}");
        result.add(request(List.of(available, merge))); result.add(request(List.of(merge, available)));
        ObjectNode failedMerge = merge.deepCopy(); failedMerge.put("ok", false); result.add(request(List.of(available, failedMerge)));
        ObjectNode otherMerge = parseObject("{\"command\":\"merge-armies-3-with-4\",\"ok\":true}");
        result.add(request(List.of(available, otherMerge)));
        ObjectNode autoNested = parseObject("{\"command\":\"auto-turn\",\"ok\":true,\"result\":{\"auto_turn\":{\"selected_step\":\"preview-move-army-2-to-9\"}}}");
        autoNested.withObject("/result/auto_turn").set("result", available.get("result")); result.add(request(List.of(autoNested)));
        ObjectNode autoRoot = autoNested.deepCopy();
        available.get("result").properties().forEach(entry -> autoRoot.withObject("/result").set(entry.getKey(), entry.getValue()));
        autoRoot.withObject("/result/auto_turn/result/route_preview").put("previewed_date_raw", 1); result.add(request(List.of(autoRoot)));
        ObjectNode nullDate = request(List.of(available)); nullDate.putNull("date_raw"); result.add(nullDate);
        ObjectNode noSnapshot = request(List.of(available)); noSnapshot.putNull("snapshot"); result.add(noSnapshot);
        ObjectNode otherTarget = row(2, 10, "available", "[10]"); result.add(request(List.of(available, otherTarget)));
        ObjectNode invalidCommand = available.deepCopy(); invalidCommand.put("command", "preview-move-army-02-to-9"); result.add(request(List.of(invalidCommand)));
        ObjectNode invalidStatus = available.deepCopy(); invalidStatus.withObject("/result/route_preview").put("status", "unknown");
        result.add(request(List.of(available, invalidStatus)));
        ObjectNode extra = available.deepCopy(); extra.withObject("/result/route_preview").set("source_extension", parse("{\"value\":\"RAW_FLOAT_SENTINEL\",\"large\":18446744073709551615,\"empty\":[],\"none\":null}"));
        result.add(request(List.of(extra)));
        ObjectNode zero = request(List.of(row(0, 9, "available", "[9]"))); zero.put("army_id", 0); result.add(zero);
        return List.copyOf(result);
    }
    private static ObjectNode request(List<ObjectNode> rows) {
        ObjectNode root = parseObject("{\"commands\":[],\"snapshot\":{\"snapshot_id\":\"s1\",\"revision\":7,\"native_revision\":11,\"episode_run_id\":\"ep1\",\"diagnostics\":{\"connection_generation\":3}},\"army_id\":2,\"origin_province_id\":1,\"target_province_id\":9,\"date_raw\":42}");
        ArrayNode commands = root.withArray("commands"); rows.forEach(row -> commands.add(row.deepCopy())); return root;
    }
    private static ObjectNode row(int army, int target, String status, String route) {
        ObjectNode root = parseObject("{\"command\":\"preview-move-army-" + army + "-to-" + target + "\",\"ok\":true,\"result\":{\"queried_snapshot_id\":\"s1\",\"queried_revision\":7,\"queried_native_revision\":11,\"queried_connection_generation\":3,\"queried_episode_run_id\":\"ep1\",\"route_preview\":{\"status\":\"" + status + "\",\"army_id\":" + army + ",\"origin_province_id\":1,\"target_province_id\":" + target + ",\"previewed_date_raw\":42,\"route_province_ids\":" + route + "}}}");
        return root;
    }
    private static void wrongTokens() {
        for (String token : List.of("true", "2.0", "\"2\"", "null")) {
            ObjectNode input = request(List.of(row(2, 9, "available", "[9]"))); input.put("army_id", "RAW_TOKEN_SENTINEL");
            rejects(() -> RoutePreviewConsumerCodec.decode(rawToken(input, token)), "strict query token " + token);
            ObjectNode receipt = request(List.of(row(2, 9, "available", "[9]")));
            receipt.withObject("/commands/0/result/route_preview").put("army_id", "RAW_TOKEN_SENTINEL");
            check(RoutePreviewConsumerCodec.project(rawToken(receipt, token)).length == 4, "wrong receipt ID unusable " + token);
        }
        rejects(() -> RoutePreviewConsumerCodec.decode("{\"commands\":[],\"commands\":[]}".getBytes(StandardCharsets.UTF_8)), "duplicate keys rejected");
        rejects(() -> RoutePreviewConsumerCodec.decode(new byte[]{(byte)0xff}), "invalid UTF8 rejected");
        ObjectNode badLease = request(List.of()); badLease.withObject("/snapshot/diagnostics").put("connection_generation", true);
        rejects(() -> RoutePreviewConsumerCodec.decode(badLease.toString().getBytes(StandardCharsets.UTF_8)), "bool generation rejected");
    }
    private static byte[] rawToken(ObjectNode input, String token) {
        String json = input.toString(), marker = "\"RAW_TOKEN_SENTINEL\"";
        check(json.indexOf(marker) >= 0 && json.indexOf(marker) == json.lastIndexOf(marker), "one exact raw-token slot");
        // The token is an immutable test vector, inserted after object serialization so 2.0 cannot become 2.
        return json.replace(marker, token).getBytes(StandardCharsets.UTF_8);
    }
    private static byte[] caseBytes(JsonNode value) {
        return value.toString().replace("\"RAW_FLOAT_SENTINEL\"", "1.0").getBytes(StandardCharsets.UTF_8);
    }
    private static void costs(StockRules rules) {
        check(rules.waterMinimumDays() == 120 && rules.waterSavingsDays() == 65, "actual vanilla ordinary thresholds");
        check(rules.holyWaterMinimumDays() == 180 && rules.holyWaterSavingsDays() == 90, "actual vanilla GHW thresholds");
        check(rules.goalsForFinalPathfinding() == 10 && rules.pathFactor() == 5, "actual source search hints");
        check(RouteReroutePolicy.costCandidates(rules, cost(120, 55, 24, true, false)).considerWaterPreview(), "ordinary boundary candidate");
        check(!RouteReroutePolicy.costCandidates(rules, cost(119, 54, 24, true, false)).considerWaterPreview(), "minimum travel days");
        check(!RouteReroutePolicy.costCandidates(rules, cost(120, 56, 24, true, false)).considerWaterPreview(), "minimum savings");
        check(!RouteReroutePolicy.costCandidates(rules, cost(179, 89, 40, true, true)).considerWaterPreview(), "GHW threshold separate");
        check(RouteReroutePolicy.costCandidates(rules, cost(180, 90, 36, true, true)).considerWaterPreview(), "GHW exact boundary");
        check(!RouteReroutePolicy.costCandidates(rules, cost(120, 241, 24, true, false)).withinWaterFactor(), "water factor gate");
        check(!RouteReroutePolicy.costCandidates(rules, cost(121, 50, 24, true, false)).withinMaximumPathFactor(), "path factor gate");
        CostCandidates huge = RouteReroutePolicy.costCandidates(rules, new Costs(new CurrentMovement.FixedPoint(Long.MAX_VALUE),
                new CurrentMovement.FixedPoint(Long.MAX_VALUE), new CurrentMovement.FixedPoint(Long.MAX_VALUE),
                new CurrentMovement.FixedPoint(Long.MAX_VALUE), new CurrentMovement.FixedPoint(Long.MAX_VALUE), true, false));
        check(huge.withinWaterFactor() && huge.withinMaximumPathFactor() && !huge.combatProbabilityKnown(), "BigInteger costs do not overflow or imply win odds");
        check(!RouteReroutePolicy.allowSupplyRerouteCandidate(rules, 4, true), "stock support near target");
        check(RouteReroutePolicy.allowSupplyRerouteCandidate(rules, 5, true), "stock support outside near target");
        check(RouteReroutePolicy.allowSupplyRerouteCandidate(rules, 1, false), "player-support exception scoped");
        CostCandidates separate = RouteReroutePolicy.costCandidates(rules, new Costs(new CurrentMovement.FixedPoint(12_000_000),
                new CurrentMovement.FixedPoint(5_500_000), new CurrentMovement.FixedPoint(1_000_000),
                new CurrentMovement.FixedPoint(2_100_000), new CurrentMovement.FixedPoint(200_000), true, false));
        check(separate.considerWaterPreview() && !separate.withinWaterFactor(), "travel days never substitute for path costs");
    }
    private static Costs cost(long land, long water, long straight, boolean body, boolean holy) {
        return new Costs(new CurrentMovement.FixedPoint(land * 100_000), new CurrentMovement.FixedPoint(water * 100_000),
                new CurrentMovement.FixedPoint(land * 100_000), new CurrentMovement.FixedPoint(water * 100_000),
                new CurrentMovement.FixedPoint(straight * 100_000), body, holy);
    }
    private static CacheScope scope(String historySha, String hostileSha, Optional<CurrentMovement> movement) {
        return new CacheScope("test-machine", "a".repeat(64), new Lease("s1", 7, 11, 3, "ep1"), 42, 2, 1,
                List.of(3, 9), movement, hostileSha, "b".repeat(64), "c".repeat(64), historySha);
    }
    private static void consumersAndInvalidation() {
        Lookup input = RoutePreviewConsumerCodec.decode(request(List.of(row(2, 9, "available", "[3,9]"))).toString().getBytes(StandardCharsets.UTF_8));
        CacheScope scope = scope("1".repeat(64), "2".repeat(64), Optional.empty());
        Plan first = RouteReroutePolicy.selectRanked(input.history(), scope, List.of(new Goal(9, false, true)), new Cache(List.of()));
        check(first instanceof CandidateReady, "ranked consumer enters actual typed lookup");
        CandidateReady ready = (CandidateReady) first;
        check(ready.objectiveRank() == 0 && ready.targetProvinceId() == 9, "existing caller goal order retained");
        Plan cached = RouteReroutePolicy.selectRanked(List.of(), scope, List.of(new Goal(9, false, true)), ready.cache());
        check(cached instanceof CandidateReady, "same complete source scope reuses preview without scanning history");
        Plan changedHostiles = RouteReroutePolicy.selectRanked(List.of(), scope("1".repeat(64), "3".repeat(64), Optional.empty()),
                List.of(new Goal(9, false, true)), ready.cache());
        check(changedHostiles instanceof PreviewRequired, "hostile source change invalidates cached preview");
        Plan changedHistory = RouteReroutePolicy.selectRanked(List.of(), scope("4".repeat(64), "2".repeat(64), Optional.empty()),
                List.of(new Goal(9, false, true)), ready.cache());
        check(changedHistory instanceof PreviewRequired, "new readonly receipt/merge/restore history invalidates cache including negatives");
        Plan noContact = RouteReroutePolicy.selectRanked(input.history(), scope, List.of(new Goal(9, false, false)), new Cache(List.of()));
        check(noContact instanceof NoCandidate, "route quality grants no contact or combat permission");
        List<Goal> goals = new ArrayList<>(); for (int i = 0; i < 20; i++) { goals.add(new Goal(20 + i, true, false)); }
        goals.add(new Goal(9, false, true));
        Plan beyondStockHint = RouteReroutePolicy.selectRanked(input.history(), scope, goals, new Cache(List.of()));
        check(beyondStockHint instanceof CandidateReady candidate && candidate.objectiveRank() == 20, "stock top-ten hint never truncates existing candidate fallthrough");
        Lookup deferred = RoutePreviewConsumerCodec.decode(request(List.of(row(2, 9, "deferred", "[]"))).toString().getBytes(StandardCharsets.UTF_8));
        Plan unknown = RouteReroutePolicy.selectRanked(deferred.history(), scope, List.of(new Goal(9, false, true)), new Cache(List.of()));
        check(unknown instanceof ReadinessRequired, "deferred preview requires native readiness");
        byte[] packet = request(List.of(row(2, 9, "available", "[3,9]"))).toString().getBytes(StandardCharsets.UTF_8);
        CacheScope bound = RoutePlanningConsumer.bindInputs(scope, packet, List.of(new Goal(9, false, true)));
        check(RoutePlanningConsumer.plan(packet, bound, List.of(new Goal(9, false, true)), new Cache(List.of())) instanceof CandidateReady,
                "source-bound consumer validates actual history before policy entry");
        byte[] changed = request(List.of()).toString().getBytes(StandardCharsets.UTF_8);
        rejects(() -> RoutePlanningConsumer.plan(changed, bound, List.of(new Goal(9, false, true)), new Cache(List.of())),
                "old digest cannot be supplied with changed actual history");
        rejects(() -> RoutePlanningConsumer.plan(packet, bound, List.of(new Goal(9, false, false)), new Cache(List.of())),
                "changed goal or contact qualification invalidates bound cache inputs");
    }
    private static Optional<CurrentMovement> movement(long progress) {
        String value = "{\"status\":\"available\",\"source\":\"native_current_route_edge\",\"unit_state_raw\":7,\"accumulated_movement_weight_raw\":1,\"cached_edge_speed_raw\":1,\"normalized_edge_progress\":{\"raw\":" + progress + ",\"scale\":100000},\"first_route_edge_remaining_duration\":null,\"unavailable_reason\":null,\"loaded_movement_lock_cutoff\":{\"raw\":50000,\"scale\":100000}}";
        return CurrentMovementCodec.normalize(value.getBytes(StandardCharsets.UTF_8));
    }
    private static void halt() {
        HaltExpectation equal = RouteReroutePolicy.haltExpectation(1, List.of(3, 9), movement(50_000));
        check(equal.status() == LockStatus.CURRENT_PROVINCE && equal.expectedRoute().isEmpty(), "native strict > excludes equality");
        HaltExpectation locked = RouteReroutePolicy.haltExpectation(1, List.of(3, 9), movement(50_001));
        check(locked.status() == LockStatus.FIRST_EDGE_RETAINED && locked.expectedRoute().equals(List.of(3)), "locked edge retained instead of immediate stopping");
        check(!locked.actualStopVerified() && locked.requiresNativeValidator(), "Halt expected route has no action/postcondition credit");
        check(RouteReroutePolicy.haltExpectation(1, List.of(), Optional.empty()).status() == LockStatus.UNAVAILABLE, "missing movement stays unknown");
        for (SubmissionState state : SubmissionState.values()) {
            check(RouteReroutePolicy.maySubmitHalt(state, true, true) == (state == SubmissionState.NEVER_SUBMITTED), "unknown/ACK/rejection do not resubmit " + state);
        }
        check(!RouteReroutePolicy.maySubmitHalt(SubmissionState.NEVER_SUBMITTED, true, false), "native validation cannot be bypassed");
    }
    private static JsonNode parse(String value) { return StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode parseObject(String value) { JsonNode node = parse(value); if (node instanceof ObjectNode object) { return object; } throw new IllegalArgumentException(); }
    private static String text(JsonNode value, String key) { return StrictJson.text(value.get(key)); }
    private static void check(boolean condition, String reason) { assertions++; if (!condition) { throw new AssertionError(reason); } }
    private static void rejects(Runnable action, String reason) {
        try { action.run(); } catch (IllegalArgumentException expected) { assertions++; return; } throw new AssertionError(reason);
    }
}
