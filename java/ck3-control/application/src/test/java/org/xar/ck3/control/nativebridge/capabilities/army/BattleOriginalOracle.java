package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;

/** Test-only calls to the actual retained Python producer; no Python implementation or file is added. */
public final class BattleOriginalOracle {
    private BattleOriginalOracle() { }
    private record SourcePin(String relative, String sha256) { }
    private static final List<SourcePin> SOURCES = List.of(
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_control_contract.py", "2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_actual_geography_contract.py", "63b4cf5db603c89fbfa0a3d18261f9dc4d26e4015aac9f4dea4efb811f9153f7"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_rule_context_contract.py", "85aaaf7a008af5267fc02c3d93c7316113c7a30d64e0a03a785747578dcccd86"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_stored_advantage_sources_contract.py", "9a8d21e17ab766754c8e8ba1083186483d43a4be485185225a7ae275aa735c98"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_stored_effect_flags_contract.py", "596690f88e8e4b2482c7747e97aeeeccb66a8c43b0158b674efe75d3207b0073"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_dynamic_advantage_contract.py", "7ded880c2cf630c9c92d0c849577e44147ecc1af7e6f0c6db2fe27ad723e8f5b"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_dynamic_components_contract.py", "5006b25991a1ac1dfa920a1dbade425d5c803068c1bf8c19940d523b5fd25128"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_own_nested_modifier_contract.py", "933d016c7d418d5334d29219c77f52bd6993057ff57c0cd80aee34a422db5626"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/entry_preceding_capture_contract_12004.py", "abee0bf563c485baa2b456c9bc10983dab13d5e8e7722c9a1caf9469da4255b9"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_finalizer_manager_inputs_contract_v1.py", "98f98e45db77699ca32031d908e8300f2087e99230cc094ccd01cd58bb4cdf52"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_warscore_caps_contract_v1.py", "9296a4251215e0c37cca4787bf8e279d8b0f2bc35f52fb217d043745625eb6dc"),
            new SourcePin("ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py", "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e"),
            new SourcePin("ck3_autonomous_player/tests/unit/test_battle_control_snapshot_v1_bridge.py", "6f17e14e7b9e9f4fa3462dd5eb3b7c365fbd551369b00caa271d9ea346e93508"));
    private static Path configured(String property, boolean directory) throws IOException {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException("required original-producer property missing: " + property);
        Path supplied = Path.of(value); if (!supplied.isAbsolute()) throw new IllegalStateException("absolute path required: " + property);
        Path actual = supplied.toRealPath();
        if (directory ? !Files.isDirectory(actual) : !Files.isRegularFile(actual)) throw new IllegalStateException("unavailable original producer: " + property);
        return actual;
    }
    private static void verify(Path root) throws IOException {
        for (SourcePin pin : SOURCES) {
            Path path = root.resolve(pin.relative()).toRealPath();
            if (!path.startsWith(root) || !Files.isRegularFile(path) || Files.size(path) > 2 * 1024 * 1024) throw new IllegalStateException("original source unavailable: " + pin.relative());
            try {
                String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
                if (!actual.equals(pin.sha256())) throw new IllegalStateException("original source drift: " + pin.relative());
            } catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        }
    }
    public static ObjectNode normalizeControl(JsonNode input, int subject, BigInteger revision, long date) throws Exception {
        ObjectNode value = ArmyJson.empty(); value.set("input", input); value.put("subject", subject); value.put("revision", revision); value.put("date", date);
        return call("""
                import json,sys
                from xar_autoplayer.bridge.battle_control_contract import normalize_battle_control_snapshot_v1
                v=json.load(sys.stdin)
                print(json.dumps(normalize_battle_control_snapshot_v1(v['input'],expected_subject_public_cunit_id=v['subject'],expected_snapshot_revision=v['revision'],expected_observed_date_raw=v['date']),allow_nan=False))
                """, value);
    }
    public static ObjectNode fixture() throws Exception {
        return call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_battle_control_snapshot_v1_bridge.py'
                spec=importlib.util.spec_from_file_location('xar_original_battle_fixture',path)
                module=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                frame=module._battle_frame()
                print(json.dumps({'parent':frame,'counter':module._active_counter_inputs(frame),'resume':module._active_resume_receipt(frame)},allow_nan=False))
                """, ArmyJson.empty());
    }
    public static ObjectNode call(String source, JsonNode input) throws Exception {
        if (source == null || source.isBlank() || source.length() > 64 * 1024) throw new IllegalArgumentException("bounded original call required");
        Path root = configured("xar.repository.root", true), python = configured("xar.python", false); verify(root);
        String bootstrap = """
                import sys
                from pathlib import Path
                sys.dont_write_bytecode=True
                root=Path(sys.argv[1])
                sys.path.insert(0,str(root))
                sys.path.insert(0,str(root/'ck3_autonomous_player'))
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))
                """;
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-c", bootstrap + source, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        FutureTask<byte[]> stdout = new FutureTask<>(() -> process.getInputStream().readNBytes(8 * 1024 * 1024 + 1));
        FutureTask<byte[]> stderr = new FutureTask<>(() -> process.getErrorStream().readNBytes(16385));
        Thread.ofVirtual().start(stdout); Thread.ofVirtual().start(stderr);
        try {
            byte[] request = ArmyJson.bytes(input); if (request.length > 8 * 1024 * 1024) throw new IllegalArgumentException("bounded original request required");
            try (var stream = process.getOutputStream()) { stream.write(request); }
            if (!process.waitFor(60, TimeUnit.SECONDS)) throw new IllegalStateException("original BattleControl producer timed out");
            byte[] output = stdout.get(5, TimeUnit.SECONDS), errors = stderr.get(5, TimeUnit.SECONDS);
            if (output.length > 8 * 1024 * 1024 || errors.length > 16384) throw new IllegalStateException("original producer output exceeded bound");
            if (process.exitValue() != 0) throw new IllegalStateException("original producer exit=" + process.exitValue() + ": " + new String(errors, StandardCharsets.UTF_8));
            verify(root); return ArmyJson.parse(output);
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
    }
}
