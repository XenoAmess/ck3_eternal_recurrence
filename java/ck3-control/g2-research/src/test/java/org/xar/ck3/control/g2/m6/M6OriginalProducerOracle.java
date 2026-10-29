package org.xar.ck3.control.g2.m6;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Explicit offline oracle. The shared qualified launcher owns the whole Java/Python native Job. */
public final class M6OriginalProducerOracle {
    private M6OriginalProducerOracle() { }
    private static final String SCRIPT = """
            import sys,json,hashlib
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'));sys.path.insert(0,str(root/'tools'))
            from xar_autoplayer.bridge.sway_terminal_source_producer_12004 import compose_sway_terminal_sources_12004
            from g2_saved_campaign.sway_start_typed_classifier_v1 import classify_ordinary_sway_start_applied_v1
            ledger=json.loads(Path(sys.argv[2]).read_bytes());auto=json.loads(Path(sys.argv[3]).read_bytes())
            rows=[ledger['resolved'],*ledger['resolved'].get('previous_interventions',[])]
            output={'schema':'xar.g2.m6.actual-original-producers/v1','ordinary_start':classify_ordinary_sway_start_applied_v1(auto['result']['structured_content'],initial_frame={'actor_character_id':31254,'episode_run_id':'native-31254-6271ac8cd441'},game_pid=214568),'compositions':[compose_sway_terminal_sources_12004(original_resolved=row,completion_read=row['latest_instance_observation']['native_observation']) for row in rows]}
            refs=[]
            for rel in ('ck3_autonomous_player/src/xar_autoplayer/bridge/sway_terminal_source_producer_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/sway_completion_causal_private_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/active_scheme_sway_completion_termination_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','tools/g2_saved_campaign/sway_start_typed_classifier_v1.py'):
                raw=(root/rel).read_bytes();refs.append({'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            output['source_refs']=refs
            print(json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;

    public static void main(String[] args) throws Exception {
        require(args.length == 6, "repository existing-python original-ledger-copy original-AUTO48-copy absent-output-dir lease-deadline");
        Path root = Path.of(args[0]).toRealPath(), python = Path.of(args[1]).toRealPath();
        Path ledgerFile = Path.of(args[2]).toRealPath(), autoFile = Path.of(args[3]).toRealPath();
        Path output = Path.of(args[4]).toAbsolutePath().normalize(); Instant deadline = Instant.parse(args[5]);
        require(!Files.exists(output) && Instant.now().isBefore(deadline), "fresh output and unexpired allocation required");
        byte[] ledger = Files.readAllBytes(ledgerFile), auto = Files.readAllBytes(autoFile);
        pin(ledger, 21864, "edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580");
        pin(auto, 87990, "44defd2b790131659d9dbd617b755b98d9d36820789bbc5e8248274152c93c24");
        List<ExactRef> sourceBefore = new ArrayList<>();
        for (String rel : List.of("ck3_autonomous_player/src/xar_autoplayer/bridge/sway_terminal_source_producer_12004.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/sway_completion_causal_private_12004.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/active_scheme_sway_completion_termination_private_transport.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py", "tools/g2_saved_campaign/sway_start_typed_classifier_v1.py")) {
            Path file = root.resolve(rel); sourceBefore.add(ref(file.toString(), Files.readAllBytes(file)));
        }
        Files.createDirectory(output);
        Path stdout = output.resolve("original-producers.json"), stderr = output.resolve("original-producers.stderr.log");
        List<String> command = new ArrayList<>(List.of(python.toString(), "-B", "-X", "utf8", "-c", SCRIPT,
                root.toString(), ledgerFile.toString(), autoFile.toString()));
        Process process = new ProcessBuilder(command).directory(root.toFile())
                .redirectOutput(stdout.toFile()).redirectError(stderr.toFile()).start();
        String stop = null;
        Instant producerDeadline = Instant.now().plus(Duration.ofSeconds(60));
        while (!process.waitFor(250, TimeUnit.MILLISECONDS)) {
            if (!Instant.now().isBefore(deadline) || !Instant.now().isBefore(producerDeadline)) {
                stop = "producer_timeout_or_release_expired"; break;
            }
            if ((Files.exists(stdout) && Files.size(stdout) > 131_072)
                    || (Files.exists(stderr) && Files.size(stderr) > 32_768)) {
                stop = "producer_output_budget_exceeded"; break;
            }
        }
        if (stop != null) process.destroyForcibly();
        boolean parentExited = process.waitFor(5, TimeUnit.SECONDS);
        if (!parentExited) { process.destroyForcibly(); stop = "producer_parent_exit_not_observed"; }
        if (stop == null && ((Files.exists(stdout) && Files.size(stdout) > 131_072)
                || (Files.exists(stderr) && Files.size(stderr) > 32_768))) stop = "producer_output_budget_exceeded";
        int exitCode = parentExited ? process.exitValue() : 124;
        boolean innerPassed = exitCode == 0 && stop == null;
        ObjectNode actual = StrictJson.object(); actual.put("schema", "xar.g2.m6.original-producer-difference/v1");
        actual.put("machine_id", "xenoamess-full-tower-eb9d2c1186"); actual.put("observed_at_utc", Instant.now().toString());
        actual.put("machine_identity_source", "RUNTIME15 admitted machine; actual shared launcher must revalidate it");
        actual.put("historical_source_machine_id", "xenoamess-full-tower-eb9d2c1186");
        actual.put("historical_start_observed_at_utc", "2026-10-19T03:34:34Z");
        actual.put("historical_ledger_collected_at_utc", "2026-10-20T00:47:10Z");
        actual.put("inner_exit_code", exitCode); actual.put("producer_parent_exit_observed", parentExited);
        actual.put("process_pid", process.pid());
        actual.put("outer_native_job_receipt_required", true);
        if (stop == null) actual.putNull("stop_reason"); else actual.put("stop_reason", stop);
        actual.set("ledger_source", ref(ledgerFile.toString(), ledger).toJson()); actual.set("ordinary_auto_source", ref(autoFile.toString(), auto).toJson());
        actual.put("source_inventory_scope", "five direct called source units; transitive Python imports are not full-source qualification");
        Files.write(output.resolve("PRODUCER-TERMINAL.json"), StrictJson.canonical(actual), StandardOpenOption.CREATE_NEW);
        boolean sourcesMatch = true;
        for (ExactRef before : sourceBefore) sourcesMatch &= before.equals(ref(before.path(), Files.readAllBytes(Path.of(before.path()))));
        actual.put("producer_sources_pre_post_match", sourcesMatch);
        int compared = 0;
        boolean ordinaryMatched = false;
        try { if (innerPassed && sourcesMatch) {
            byte[] rawOracle = Files.readAllBytes(stdout); require(rawOracle.length <= 131_072, "bounded actual oracle output required");
            JsonNode oracle = StrictJson.parse(rawOracle, 131_072);
            JsonNode ledgerTree = StrictJson.parse(ledger);
            var campaign = M6SourceProducer.fromClosedLedger(ledger, source(ledgerFile.toString(), ledger));
            List<JsonNode> rows = List.of(ledgerTree.path("resolved"), ledgerTree.path("resolved").path("previous_interventions").get(0));
            require(oracle.path("compositions").size() == rows.size(), "actual producer row count differs");
            for (int index = 0; index < rows.size(); index++) {
                JsonNode rawCompletion = rows.get(index).path("latest_instance_observation").path("native_observation");
                JsonNode javaPlane = StrictJson.parse(M6SourceProducer.composeCurrentObservation(StrictJson.canonical(rawCompletion),
                        campaign.episodes().get(index).identity()).bytes());
                require(javaPlane.equals(oracle.path("compositions").get(index).get("current_instance_observation")),
                        "Java current observation differs from actual original source composer");
                require(oracle.path("compositions").get(index).path("named_material_observation").isNull(),
                        "a historical summary must not become current raw named opinion");
                require(!oracle.path("compositions").get(index).path("terminal_cause_observed").booleanValue(),
                        "unobserved original terminal acquired cause");
                compared++;
            }
            byte[] packet = packet(ledger, ledgerFile, auto, autoFile);
            var produced = M6SourceProducer.fromEvidencePacket(packet, source("memory:source-bound-packet", packet));
            var credit = oracle.path("ordinary_start");
            ordinaryMatched = credit.path("primitive_accepted").isBoolean() && credit.path("primitive_accepted").booleanValue()
                    && credit.path("original_action_id").textValue().equals(produced.episodes().get(1).identity().actionId())
                    && produced.episodes().get(1).start().orElseThrow().origin() == G2M6Contracts.StartOrigin.ORDINARY_FULL_PLANNER;
            require(ordinaryMatched, "strict Java ordinary Start differs from actual original classifier");
            Files.write(output.resolve("source-bound-packet.json"), packet, StandardOpenOption.CREATE_NEW);
        } } catch (RuntimeException | java.io.IOException failure) {
            actual.put("consumer_failure_class", failure.getClass().getName());
            actual.put("consumer_failure", String.valueOf(failure.getMessage())); ordinaryMatched = false;
        }
        actual.put("actual_composer_rows_compared", compared); actual.put("ordinary_classifier_matches", ordinaryMatched);
        actual.put("new_game_days", 0); actual.put("new_natural_terminal_credit", false);
        boolean passed = innerPassed && sourcesMatch && compared == 2 && ordinaryMatched;
        actual.put("passed", passed);
        Files.write(output.resolve("ACTUAL.json"), StrictJson.canonical(actual), StandardOpenOption.CREATE_NEW);
        System.out.println(new String(StrictJson.canonical(actual), java.nio.charset.StandardCharsets.UTF_8));
        require(passed, "actual original producer qualification failed; preserve actual native Job result");
    }
    private static byte[] packet(byte[] ledger, Path ledgerPath, byte[] auto, Path autoPath) {
        return M6SourceProducer.encodeEvidencePacket(ledger, ref(ledgerPath.toString(), ledger), auto, ref(autoPath.toString(), auto),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
    }
    private static G2Source source(String path, byte[] raw) {
        return new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-20T00:47:10Z", M6SourceProducer.BUILD, ref(path, raw));
    }
    private static ExactRef ref(String path, byte[] raw) {
        try { return new ExactRef(path, raw.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))); }
        catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static void pin(byte[] raw, long size, String sha) { ExactRef ref = ref("memory:retained-source", raw); require(ref.bytes() == size && ref.sha256().equals(sha), "actual original source resource differs"); }
}
