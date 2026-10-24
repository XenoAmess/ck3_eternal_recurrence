package org.xar.ck3.dynastic.acceptance;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class SharedRuntimeComposerTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @TempDir Path temporary;

    private static ObjectNode pin(Path path) throws IOException, NoSuchAlgorithmException {
        byte[] bytes = Files.readAllBytes(path);
        ObjectNode result = JSON.createObjectNode();
        result.put("path", path.toRealPath().toString());
        result.put("bytes", bytes.length);
        result.put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return result;
    }

    private static void write(Path path, JsonNode node) throws IOException {
        Files.writeString(path, JSON.writeValueAsString(node));
    }

    @Test
    void freezesCurrentInputsPreservesParentFieldsAndRecordsRealDifferences() throws IOException, NoSuchAlgorithmException {
        Path repo = temporary.resolve("repo");
        Path sdk = repo.resolve("ck3_autonomous_player/src/xar_autoplayer");
        Path tools = repo.resolve("tools");
        Files.createDirectories(sdk);
        Files.createDirectories(tools.resolve("ck3_mod_acceptance_cases"));
        Path changed = sdk.resolve("__init__.py");
        Files.writeString(changed, "# actual source now differs\n");
        Path currentFactory = sdk.resolve("bridge/mcp_server.py");
        Files.createDirectories(currentFactory.getParent());
        Files.writeString(currentFactory, "# authored current global factory source\n");
        Path canonicalHost = repo.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py");
        Files.createDirectories(canonicalHost.getParent());
        Files.writeString(canonicalHost, "# authored canonical host bytes; not a runtime qualification\n");
        for (String name : List.of("ck3_mod_acceptance_launcher.py", "ck3_mod_acceptance_queue.py", "ck3_mod_acceptance_keeper.py",
                "ck3_mod_acceptance_build_runtime.py", "codex_task_bus.py")) {
            Files.writeString(tools.resolve(name), "# authored tool\n");
        }
        Path leaseHelper = repo.resolve("promo/ck3_native_war_ai/integration/screen_bus_lease.py");
        Files.createDirectories(leaseHelper.getParent());
        Files.writeString(leaseHelper, "# authored clean checkout lease helper\n");
        for (String name : List.of("__init__.py", "generic_product_adapter.py", "dynastic_esotericism_core.json",
                "dynastic_esotericism_cold_reload.json", "dynastic_esotericism_old_save_bootstrap.json",
                "dynastic_esotericism_pre_product_seed.json")) {
            Files.writeString(tools.resolve("ck3_mod_acceptance_cases").resolve(name), "{}\n");
        }
        Path oldRepo = temporary.resolve("previous-repo");
        ObjectNode old = pin(changed);
        old.put("path", oldRepo.resolve("ck3_autonomous_player/src/xar_autoplayer/__init__.py").toString());
        old.put("sha256", "0".repeat(64));
        Path parentIndex = temporary.resolve("parent-source.json");
        ObjectNode parentSource = JSON.createObjectNode();
        parentSource.putArray("files").add(old);
        write(parentIndex, parentSource);
        ObjectNode manifest = JSON.createObjectNode();
        manifest.put("schema", "ck3-mod-acceptance-shared-runtime-v1");
        manifest.put("machine_id", "authored-machine");
        manifest.putObject("native");
        manifest.putObject("capabilities");
        manifest.putObject("host_features");
        manifest.putObject("source_root").put("path_key", "source_root");
        ObjectNode parentSourceMetadata = manifest.putObject("source_index");
        ObjectNode sourceIdentity = pin(parentIndex);
        parentSourceMetadata.put("path_key", "source_index");
        parentSourceMetadata.set("bytes", sourceIdentity.get("bytes"));
        parentSourceMetadata.set("sha256", sourceIdentity.get("sha256"));
        manifest.put("preserved_unknown_parent_field", "retain exactly");
        Path parentManifest = temporary.resolve("parent-manifest.json");
        write(parentManifest, manifest);
        ObjectNode runtime = JSON.createObjectNode();
        runtime.put("schema", "ck3-mod-acceptance-runtime-v1");
        runtime.put("machine_id", "authored-machine");
        runtime.put("repo_root", oldRepo.toString());
        runtime.set("manifest", pin(parentManifest));
        runtime.putObject("paths").put("source_index", parentIndex.toString()).put("source_root", oldRepo.toString())
                .put("host", canonicalHost.toString());
        ObjectNode allocation = runtime.putObject("allocation");
        allocation.put("preserved_allocation_field", 7);
        allocation.set("task_bus", pin(tools.resolve("codex_task_bus.py")));
        Path parentRegistration = temporary.resolve("old-global/registration_mcp.py");
        Files.createDirectories(parentRegistration.getParent());
        Files.writeString(parentRegistration, "# authored predecessor registration provider\n");
        ObjectNode parentOverlay = runtime.putObject("allocator_overlay");
        parentOverlay.set("parent-registration", pin(parentRegistration));
        parentOverlay.set("old-sdk", old.deepCopy());
        ObjectNode oldHost = pin(canonicalHost);
        oldHost.put("path", oldRepo.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py").toString());
        oldHost.put("sha256", "0".repeat(64));
        parentOverlay.set("old-host", oldHost);
        ObjectNode unselected = old.deepCopy();
        unselected.put("path", oldRepo.resolve("tools/unselected_previous_case.py").toString());
        parentOverlay.set("old-unselected", unselected);
        runtime.putObject("runtime_environment").putArray("PYTHONPATH").add(temporary.resolve("old-import").toString());
        Path parentRuntime = temporary.resolve("parent-runtime.json");
        write(parentRuntime, runtime);
        ObjectNode projection = JSON.createObjectNode();
        projection.put("schema", "ck3-common-canonical-host-successor-v1");
        projection.put("machine_id", "authored-machine");
        projection.put("qualification", "SOURCE_PROJECTION_ONLY_LIVE_NOT_QUALIFIED");
        projection.put("runtime_binding", temporary.resolve("successor/runtime.json").toString());
        projection.set("parent_runtime", pin(parentRuntime));
        projection.set("parent_manifest", pin(parentManifest));
        projection.set("parent_host", pin(canonicalHost));
        projection.set("canonical_host", pin(canonicalHost));
        projection.set("producer", pin(tools.resolve("ck3_mod_acceptance_build_runtime.py")));
        projection.set("projected_host", pin(canonicalHost));
        projection.put("game_started", false);
        projection.put("allocated", false);
        projection.put("actual_live_qualified", false);
        Path projectedRegistration = temporary.resolve("registration_mcp.py");
        Files.writeString(projectedRegistration, "# authored same-service current-factory projection\n");
        ObjectNode registrationProjection = projection.putObject("registration_projection");
        registrationProjection.set("parent", pin(parentRegistration));
        registrationProjection.set("current_factory", pin(currentFactory));
        registrationProjection.set("projected", pin(projectedRegistration));
        registrationProjection.put("binding", "existing_same_service_builder_to_current_global_factory");
        Path projectionPath = temporary.resolve("host-projection.json");
        write(projectionPath, projection);
        Path dll = temporary.resolve("authored.dll");
        Files.writeString(dll, "authored compile output, not native qualification");
        Path flagsPath = temporary.resolve("flags.json");
        ObjectNode flags = JSON.createObjectNode();
        for (String part : List.of("CONTEXT", "DOCTRINES", "DOCTRINE_KNOWLEDGE", "DOCTRINE_CATALOGUE", "REFORM_CONTEXT", "DRAFT_GROUPS", "DRAFT_DOCTRINE_CHOICES", "DRAFT_TENET_CHOICES", "DRAFT_RESOURCE_COSTS")) {
            flags.put("XAR_CK3_ENABLE_G2_PLAYER_RELIGION_" + part + "_PRIVATE_QUERY_V1", "ON");
        }
        flags.put("XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1", "ON");
        flags.put("XAR_ENABLE_RELIGION_UI12004_PRESENTATION", "ON");
        flags.put("XAR_ENABLE_RITE_CREATION_ACTIONS12004", "ON");
        flags.put("XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1", "ON");
        flags.put("XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1", "ON");
        write(flagsPath, flags);
        ObjectNode nativeIndex = JSON.createObjectNode();
        nativeIndex.put("schema", "xar.common-native-qualified-producer-index.v1");
        nativeIndex.put("machine_id", "authored-machine");
        nativeIndex.put("live_qualified", false);
        ObjectNode nativeTools = nativeIndex.putObject("runtime_native_tools");
        nativeTools.set("dll", pin(dll));
        nativeTools.set("injector", pin(dll));
        nativeIndex.set("feature_flags", pin(flagsPath));
        nativeIndex.set("cmake_cache", pin(dll));
        nativeIndex.set("native_source_manifest", pin(dll));
        Path waitPath = temporary.resolve("producer-wait.json");
        ObjectNode wait = JSON.createObjectNode();
        wait.put("machine_id", "authored-machine");
        wait.put("returncode", 0);
        wait.put("game_execution", false);
        wait.put("live_qualified", false);
        write(waitPath, wait);
        nativeIndex.set("producer_original_wait", pin(waitPath));
        Path buildPath = temporary.resolve("build-output.json");
        ObjectNode build = JSON.createObjectNode();
        build.put("machine_id", "authored-machine");
        build.put("compiler_linker_returncode", 0);
        build.put("outer_producer_returncode", 0);
        build.put("game_execution", false);
        build.put("live_qualified", false);
        build.set("bridge_DLL", pin(dll));
        build.set("reused_injector", pin(dll));
        build.set("feature_flags", pin(flagsPath));
        build.set("cache", pin(dll));
        build.set("source_manifest", pin(dll));
        build.set("producer_original_wait", pin(waitPath));
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        Path nativePath = temporary.resolve("native-index.json");
        write(nativePath, nativeIndex);
        Path output = temporary.resolve("successor");
        SharedRuntimeComposer.Result result = SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, output, "authored-machine");
        JsonNode actual = JSON.readTree(Path.of(result.runtime()).toFile());
        JsonNode actualManifest = JSON.readTree(Path.of(result.manifest()).toFile());
        JsonNode actualIndex = JSON.readTree(Path.of(result.sourceIndex()).toFile());
        assertEquals("retain exactly", actualManifest.path("preserved_unknown_parent_field").textValue());
        assertEquals(7, actual.path("allocation").path("preserved_allocation_field").intValue());
        assertEquals(1, actualIndex.path("actual_changed_parent_files").size());
        assertEquals(15, result.copiedFiles());
        assertEquals(18, actualIndex.path("files").size());
        assertEquals(projectedRegistration.toRealPath().toString(), actual.path("allocator_overlay")
                .path("current-global-registration-provider").path("path").textValue());
        assertEquals(leaseHelper.toRealPath().toString(), actual.path("allocator_overlay")
                .path("clean-lease-screen-helper").path("path").textValue());
        assertEquals(output.resolve("source/ck3_autonomous_player/src/xar_autoplayer/__init__.py").toRealPath().toString(),
                actual.path("allocator_overlay").path("old-sdk").path("path").textValue());
        assertEquals(canonicalHost.toRealPath().toString(), actual.path("allocator_overlay").path("old-host").path("path").textValue());
        assertFalse(actual.path("allocator_overlay").has("old-unselected"));
        assertEquals(parentOverlay, actual.path("parent_allocator_overlay"));
        assertEquals(3, actualIndex.path("allocator_overlay_projection").size());
        assertTrue(Files.isDirectory(output.resolve("userdirs")));
        assertEquals(SharedRuntimeComposer.Qualification.SHARED_SOURCE_AND_NATIVE_BUILD_SUCCESSOR_LIVE_NOT_QUALIFIED,
                result.qualification());
        assertFalse(actualManifest.path("capabilities").path("ck3_execute_player_rite_creation_action_v1").path("actual_live_qualified").booleanValue());
        assertTrue(Files.isRegularFile(output.resolve("source/tools/ck3_mod_acceptance_cases/generic_product_adapter.py")));
        assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, output, "authored-machine"));
        flags.put("XAR_ENABLE_RITE_CREATION_ACTIONS12004", "OFF");
        write(flagsPath, flags);
        nativeIndex.set("feature_flags", pin(flagsPath));
        build.set("feature_flags", pin(flagsPath));
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        write(nativePath, nativeIndex);
        projection.put("runtime_binding", temporary.resolve("rejected/runtime.json").toString());
        write(projectionPath, projection);
        IllegalArgumentException offFlag = assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, temporary.resolve("rejected"), "authored-machine"));
        assertTrue(offFlag.getMessage().contains("native provider not compiled"));
        assertFalse(Files.exists(temporary.resolve("rejected")));
        build.put("outer_producer_returncode", true);
        write(buildPath, build);
        nativeIndex.set("build_output", pin(buildPath));
        nativeIndex.set("production_qualification", pin(buildPath));
        write(nativePath, nativeIndex);
        projection.put("runtime_binding", temporary.resolve("boolean-code-rejected/runtime.json").toString());
        write(projectionPath, projection);
        IllegalArgumentException booleanCode = assertThrows(IllegalArgumentException.class,
                () -> SharedRuntimeComposer.compose(repo, parentRuntime, nativePath, projectionPath, temporary.resolve("boolean-code-rejected"), "authored-machine"));
        assertTrue(booleanCode.getMessage().contains("producer completion"));
    }
}
