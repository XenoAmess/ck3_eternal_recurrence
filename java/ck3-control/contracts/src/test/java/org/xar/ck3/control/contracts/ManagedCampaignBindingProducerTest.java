package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Original allocator producer -> sole binding -> shared bytes roundtrip; never starts a host or claims Root admission. */
final class ManagedCampaignBindingProducerTest {
    @TempDir Path temporary;
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final String HOST_SHA = "f25af27d0221260a95b45fc5dcf417d25d733c8dbbdba7be866146643b75f1ee";
    private static final String ORIGINAL = """
        import argparse,ast,hashlib,json,sys
        from pathlib import Path
        anchor=Path(sys.argv[1]); host=anchor.parents[3]/'native_bridge/research/run_ck3_12002_mcp_live.py'
        if hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('native producer anchor drift')
        raw=host.read_bytes()
        if len(raw)!=322681 or hashlib.sha256(raw).hexdigest()!=sys.argv[3]: raise RuntimeError('original allocator source drift')
        tree=ast.parse(raw.decode('utf-8-sig'))
        names={'allocated_managed_campaign_run_binding','file_sha'}
        selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
        if len(selected)!=2: raise RuntimeError('original allocator functions missing')
        scope={'argparse':argparse,'hashlib':hashlib,'json':json,'Path':Path,'__file__':str(host)}
        future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*selected],type_ignores=[])),str(host),'exec'),scope)
        row=json.loads(Path(sys.argv[4]).read_bytes())
        args=argparse.Namespace(state_dir=Path(row['state_dir']),output=Path(row['output']),bridge_pipe=row['bridge_pipe'],
          agent_source_root=Path(row['agent_source_root']),saved_campaign_server=row['saved_campaign_server'],
          frontend_fixture_start_policy=Path(row['frontend_fixture_start_policy']) if row['frontend_fixture_start_policy'] is not None else None)
        try: result={'ok':True,'binding':scope['allocated_managed_campaign_run_binding'](args)}
        except ValueError: result={'ok':False}
        if host.read_bytes()!=raw or hashlib.sha256(anchor.read_bytes()).hexdigest()!=sys.argv[2]: raise RuntimeError('source changed during original producer call')
        sys.stdout.buffer.write(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        """;

    @Test void exactOriginalSavedAllocatorRoundTripsActualFiveFieldsAndRejectsForeignContext() throws Exception {
        var fixture = fixture(false); JsonNode original = original(fixture.arguments());
        assertTrue(original.get("ok").booleanValue());
        var binding = ManagedCampaignRunBinding.parse(original.get("binding"));
        assertEquals(fixture.run().getFileName().toString(), binding.runId());
        assertEquals(fixture.state().toRealPath().toString(), binding.stateDir());
        assertEquals(fixture.arguments().get("bridge_pipe").textValue(), binding.bridgePipe());
        assertEquals(sha(Files.readAllBytes(fixture.run().resolve("frozen-argv.json"))), binding.frozenArgvSha256());
        assertEquals(binding, ManagedCampaignRunBinding.parse(FullJsonTree.parse(FullJsonTree.encode(binding.toJson(), 65536), 65536)));
        // The original persistent episode pair stays absent from this allocator DATA.
        assertFalse(binding.toJson().has("episode_run_id")); assertFalse(binding.toJson().has("episode_character_id"));
        for (String field : List.of("state_dir", "output", "agent_source_root")) {
            var wrong = fixture.arguments().deepCopy(); wrong.put(field, temporary.resolve("foreign-" + field).toString());
            assertFalse(original(wrong).get("ok").booleanValue(), field);
        }
        var pipe = fixture.arguments().deepCopy().put("bridge_pipe", "different-pipe"); assertFalse(original(pipe).get("ok").booleanValue());
        var frozen = fixture.frozen().deepCopy().put("run_id", "another-allocated-run"); write(fixture.run().resolve("frozen-argv.json"), frozen);
        assertFalse(original(fixture.arguments()).get("ok").booleanValue());
    }

    @Test void exactOriginalFixtureAllocatorRequiresTheActualFrozenPolicyBytesAndStartupMode() throws Exception {
        var fixture = fixture(true); assertTrue(original(fixture.arguments()).get("ok").booleanValue());
        var absentMode = fixture.arguments().deepCopy().putNull("frontend_fixture_start_policy");
        assertFalse(original(absentMode).get("ok").booleanValue());
        Path other = temporary.resolve("foreign-policy.json"); Files.writeString(other, "{\"different\":true}", StandardCharsets.UTF_8);
        var wrongPolicy = fixture.arguments().deepCopy().put("frontend_fixture_start_policy", other.toString());
        assertFalse(original(wrongPolicy).get("ok").booleanValue());
        var duplicated = fixture.frozen().deepCopy(); ((com.fasterxml.jackson.databind.node.ArrayNode) duplicated.get("argv")).add("--state-dir").add(fixture.state().toString());
        write(fixture.run().resolve("frozen-argv.json"), duplicated);
        assertFalse(original(fixture.arguments()).get("ok").booleanValue());
    }

    @Test void strictBindingSchemaRejectsEveryMissingNullWrongTypeAndExtraFieldWithoutPathRewriting() {
        var row = JSON.objectNode().put("run_id", "run").put("state_dir", "D:\\Actual State\\MixedCase\\..\\State")
                .put("bridge_pipe", "actual-pipe").put("host_path", "D:\\Actual Host.java").put("frozen_argv_sha256", "a".repeat(64));
        var binding = ManagedCampaignRunBinding.parse(row); assertEquals(row.get("state_dir").textValue(), binding.stateDir());
        assertEquals(row, binding.toJson());
        for (String key : List.of("run_id", "state_dir", "bridge_pipe", "host_path", "frozen_argv_sha256")) {
            var missing = row.deepCopy(); missing.remove(key); assertThrows(IllegalArgumentException.class, () -> ManagedCampaignRunBinding.parse(missing));
            for (JsonNode wrong : List.of(JSON.nullNode(), JSON.booleanNode(true), JSON.numberNode(1), JSON.objectNode(), JSON.arrayNode())) {
                var invalid = row.deepCopy(); invalid.set(key, wrong); assertThrows(IllegalArgumentException.class, () -> ManagedCampaignRunBinding.parse(invalid));
            }
            var empty = row.deepCopy().put(key, ""); assertThrows(IllegalArgumentException.class, () -> ManagedCampaignRunBinding.parse(empty));
        }
        assertThrows(IllegalArgumentException.class, () -> ManagedCampaignRunBinding.parse(row.deepCopy().put("frozen_argv_sha256", "A".repeat(64))));
        assertThrows(IllegalArgumentException.class, () -> ManagedCampaignRunBinding.parse(row.deepCopy().put("episode_run_id", "fabricated")));
    }

    @Test void explicitSessionModeCannotAcquireAnEpisodeByAnUnboundOrManagedDataBranch() {
        SessionMode unbound = SessionMode.UnboundData.INSTANCE;
        assertFalse(unbound instanceof SessionMode.NativeCampaign); assertFalse(unbound instanceof SessionMode.OneLife);
        var binding = new ManagedCampaignRunBinding("actual-run", "actual-state", "actual-pipe", "actual-host", "a".repeat(64));
        SessionMode managed = new SessionMode.NativeCampaign(binding); assertFalse(managed instanceof SessionMode.OneLife);
        assertEquals(binding, ((SessionMode.NativeCampaign) managed).binding());
        assertThrows(NullPointerException.class, () -> new SessionMode.NativeCampaign(null));
        assertThrows(IllegalArgumentException.class, () -> new SessionMode.OneLife(BigInteger.ZERO, "episode"));
        assertThrows(IllegalArgumentException.class, () -> new SessionMode.OneLife(BigInteger.ONE, ""));
    }

    private record Fixture(Path run, Path state, ObjectNode arguments, ObjectNode frozen) { }
    private Fixture fixture(boolean policy) throws Exception {
        Path anchor = anchor(), repository = anchor.getParent().getParent().getParent().getParent();
        Path host = repository.resolve("native_bridge/research/run_ck3_12002_mcp_live.py");
        Path run = Files.createDirectories(temporary.resolve(policy ? "actual-fixture-allocation" : "actual-saved-allocation"));
        Path state = Files.createDirectories(temporary.resolve("actual-state-" + policy)), output = run.resolve("actual-report.json");
        ObjectNode arguments = JSON.objectNode().put("state_dir", state.toString()).put("output", output.toString()).put("bridge_pipe", "actual-allocated-pipe")
                .put("agent_source_root", repository.resolve("src").toString()).put("saved_campaign_server", !policy).putNull("frontend_fixture_start_policy");
        var argv = JSON.arrayNode().add(required("xar.native.producer.python")).add("-X").add("utf8").add("-B").add(host.toString())
                .add("--state-dir").add(state.toString()).add("--bridge-pipe").add("actual-allocated-pipe")
                .add("--agent-source-root").add(repository.resolve("src").toString()).add("--output").add(output.toString());
        if (policy) {
            Path actualPolicy = temporary.resolve("actual-policy.json"); Files.writeString(actualPolicy, "{\"actual_fixture_input\":true}", StandardCharsets.UTF_8);
            arguments.put("frontend_fixture_start_policy", actualPolicy.toString());
            argv.add("--frontend-fixture-start-policy").add(actualPolicy.toString()).add("--frontend-robert-bootstrap").add("--fixture-profile");
        } else argv.add("--saved-campaign-save").add(temporary.resolve("actual-save.ck3").toString());
        ObjectNode frozen = JSON.objectNode().put("run_id", run.getFileName().toString()).put("state_dir", state.toString()); frozen.set("argv", argv);
        write(run.resolve("frozen-argv.json"), frozen); return new Fixture(run, state, arguments, frozen);
    }
    private JsonNode original(ObjectNode arguments) throws Exception {
        Path anchor = anchor(), python = Path.of(required("xar.native.producer.python")); String anchorSha = required("xar.native.producer.sha256");
        if (!python.isAbsolute() || !anchorSha.matches("[a-f0-9]{64}")) throw new IllegalStateException("NOT EXECUTED: explicit original Python/anchor pins required");
        assertEquals(anchorSha, sha(Files.readAllBytes(anchor)));
        Path host = anchor.getParent().getParent().getParent().getParent().resolve("native_bridge/research/run_ck3_12002_mcp_live.py");
        byte[] source = Files.readAllBytes(host); assertEquals(322681, source.length); assertEquals(HOST_SHA, sha(source));
        Path request = temporary.resolve("original-allocator-args.json"), output = temporary.resolve("original-allocator-result.json"), error = temporary.resolve("original-allocator.stderr");
        write(request, arguments);
        var process = new ProcessBuilder(python.toString(), "-X", "utf8", "-c", ORIGINAL, anchor.toString(), anchorSha, HOST_SHA, request.toString())
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new IOException("original allocator producer timeout"); }
        if (process.exitValue() != 0) throw new IOException("original allocator producer failed: " + Files.readString(error, StandardCharsets.UTF_8));
        assertArrayEquals(source, Files.readAllBytes(host)); assertEquals(anchorSha, sha(Files.readAllBytes(anchor)));
        return FullJsonTree.parse(Files.readAllBytes(output), 65536);
    }
    private static Path anchor() { Path value = Path.of(required("xar.native.producer.source")); if (!value.isAbsolute()) throw new IllegalStateException("NOT EXECUTED: absolute original source required"); return value; }
    private static void write(Path target, JsonNode value) throws IOException { Files.write(target, FullJsonTree.encode(value, 65536)); }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: original fixture property missing: " + name); return value; }
    private static String sha(byte[] value) throws Exception { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
}
