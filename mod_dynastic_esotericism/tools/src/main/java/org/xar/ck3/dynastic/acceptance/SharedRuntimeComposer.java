package org.xar.ck3.dynastic.acceptance;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

/** Freezes a shared source successor and binds an explicitly qualified native producer. */
public final class SharedRuntimeComposer {
    private static final ObjectMapper JSON = new ObjectMapper().enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
    private static final String SOURCE_INDEX_SCHEMA = "ck3-common-source-index-v1";
    private static final long MAX_SOURCE_BYTES = 128L * 1024L * 1024L;
    private static final List<String> REQUIRED_FLAGS = List.of(
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_CONTEXT_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_CATALOGUE_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1",
            "XAR_CK3_ENABLE_G2_PRISONER_RELEASE_PREVIEW_PRIVATE_V1",
            "XAR_ENABLE_RELIGION_UI12004_PRESENTATION", "XAR_ENABLE_RITE_CREATION_ACTIONS12004",
            "XAR_CK3_ENABLE_ORDINARY_INTERACTION_PRIVATE_V1", "XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1");
    private static final List<String> TOOLS = List.of(
            "ck3_open_ingame_decisions_v1", "ck3_query_ingame_decision_item_v1",
            "ck3_select_ingame_decision_item_v1", "ck3_confirm_ingame_decision_outcome_v1",
            "ck3_select_event_option", "ck3_query_player_religion_context_v1",
            "ck3_query_player_rite_members_v1",
            "ck3_query_player_prisoner_collection_private_v1",
            "ck3_query_player_religion_doctrines_v1", "ck3_query_player_religion_doctrine_knowledge_v1",
            "ck3_query_player_religion_reform_context_v1", "ck3_query_player_religion_draft_groups_v1",
            "ck3_query_player_religion_draft_doctrine_choices_v1", "ck3_query_player_religion_draft_resource_costs_v1",
            "ck3_query_player_rite_creation_action_context_v1", "ck3_execute_player_rite_creation_action_v1",
            "ck3_collect_player_rite_creation_action_result_v1", "ck3_verify_player_rite_creation_action_completed_v1",
            "ck3_query_character_interaction_ordinary_v1", "ck3_initiate_character_interaction_ordinary_v1",
            "ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1", "ck3_observe_normal_exit_v1");

    private SharedRuntimeComposer() { }

    public record FilePin(String path, long bytes, String sha256) { }
    public record SourceContent(long bytes, String sha256) {
        public SourceContent {
            if (bytes < 0 || sha256 == null || !sha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("canonical source content signature required");
            }
        }
    }
    public enum Qualification { SHARED_SOURCE_AND_NATIVE_BUILD_SUCCESSOR_LIVE_NOT_QUALIFIED }
    private enum OverlayDisposition { CURRENT_FROZEN_INPUT, CURRENT_PROJECTED_HOST, PARENT_SOURCE_OUTSIDE_SELECTED_CLOSURE }
    public record Result(String runtime, String manifest, String sourceIndex, long copiedBytes, int copiedFiles,
            Qualification qualification) { }

    public static int run(String[] args) {
        try {
            Map<String, String> options = parse(args);
            Result result = compose(Path.of(options.get("--repo-root")), Path.of(options.get("--base-runtime")),
                    Path.of(options.get("--native-index")), Path.of(options.get("--host-projection")),
                    Path.of(options.get("--output")), options.get("--machine-id"));
            System.out.println(JSON.writerWithDefaultPrettyPrinter().writeValueAsString(result));
            return 0;
        } catch (IOException | IllegalArgumentException error) {
            System.err.println("Shared runtime composition failed: " + error.getMessage());
            return 1;
        }
    }

    public static Result compose(Path repository, Path baseRuntime, Path nativeIndex, Path hostProjection, Path destination,
            String machineId) throws IOException {
        Path repo = repository.toRealPath();
        Path output = destination.toAbsolutePath().normalize();
        if (Files.exists(output, LinkOption.NOFOLLOW_LINKS) || output.startsWith(repo)) {
            throw new IllegalArgumentException("a fresh external shared-runtime destination is required");
        }
        ObjectNode runtime = object(JSON.readTree(baseRuntime.toFile()), "base runtime").deepCopy();
        if (!text(runtime, "schema").equals("ck3-mod-acceptance-runtime-v1")
                || !text(runtime, "machine_id").equals(machineId)) {
            throw new IllegalArgumentException("base runtime schema or observed machine differs");
        }
        FilePin parentManifestPin = checkedPin(runtime.get("manifest"));
        ObjectNode manifest = object(JSON.readTree(Path.of(parentManifestPin.path()).toFile()), "shared manifest").deepCopy();
        if (!text(manifest, "machine_id").equals(machineId)) throw new IllegalArgumentException("manifest machine differs");
        if (!text(manifest, "schema").equals("ck3-mod-acceptance-shared-runtime-v1")) {
            throw new IllegalArgumentException("shared manifest schema differs");
        }
        ObjectNode parentPaths = object(runtime.get("paths"), "parent paths");
        Path parentSourceRoot = Path.of(text(parentPaths, "source_root")).toAbsolutePath().normalize();
        Path parentRepository = Path.of(text(runtime, "repo_root")).toAbsolutePath().normalize();
        ObjectNode hostReceipt = object(JSON.readTree(hostProjection.toFile()), "canonical host projection");
        if (!text(hostReceipt, "schema").equals("ck3-common-canonical-host-successor-v1")
                || !text(hostReceipt, "machine_id").equals(machineId)
                || !text(hostReceipt, "qualification").equals("SOURCE_PROJECTION_ONLY_LIVE_NOT_QUALIFIED")
                || !Path.of(text(hostReceipt, "runtime_binding")).toAbsolutePath().normalize().equals(output.resolve("runtime.json"))
                || !checkedPin(hostReceipt.get("parent_runtime")).equals(pin(baseRuntime))
                || !checkedPin(hostReceipt.get("parent_manifest")).equals(parentManifestPin)
                || !Boolean.FALSE.equals(booleanValue(hostReceipt.get("game_started")))
                || !Boolean.FALSE.equals(booleanValue(hostReceipt.get("allocated")))
                || !Boolean.FALSE.equals(booleanValue(hostReceipt.get("actual_live_qualified")))) {
            throw new IllegalArgumentException("canonical host projection crossed its original runtime or source-only boundary");
        }
        FilePin currentHost = checkedPin(hostReceipt.get("projected_host"));
        FilePin parentHost = checkedPin(hostReceipt.get("parent_host"));
        if (!parentHost.equals(pin(Path.of(text(parentPaths, "host"))))) {
            throw new IllegalArgumentException("projection parent host differs from original runtime");
        }
        FilePin canonicalHost = checkedPin(hostReceipt.get("canonical_host"));
        FilePin hostProducer = checkedPin(hostReceipt.get("producer"));
        if (!Path.of(canonicalHost.path()).equals(repo.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"))
                || !Path.of(hostProducer.path()).equals(repo.resolve("tools/ck3_mod_acceptance_build_runtime.py"))) {
            throw new IllegalArgumentException("host projection must come from this selected canonical checkout");
        }
        FilePin registrationProvider = null;
        if (hostReceipt.has("registration_projection")) {
            ObjectNode projection = object(hostReceipt.get("registration_projection"), "global registration projection");
            if (projection.size() != 4 || !text(projection, "binding").equals("existing_same_service_builder_to_current_global_factory")) {
                throw new IllegalArgumentException("exact same-service global registration projection required");
            }
            FilePin parentRegistration = checkedPin(projection.get("parent"));
            FilePin currentFactory = checkedPin(projection.get("current_factory"));
            registrationProvider = checkedPin(projection.get("projected"));
            if (!Path.of(currentFactory.path()).equals(repo.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"))
                    || !Path.of(registrationProvider.path()).equals(hostProjection.toRealPath().getParent().resolve("registration_mcp.py"))) {
                throw new IllegalArgumentException("global registration projection crossed its canonical factory or output root");
            }
            ObjectNode parentOverlays = object(runtime.get("allocator_overlay"), "parent source overlay");
            boolean retained = false;
            for (JsonNode row : parentOverlays) {
                if (row.isObject() && row.path("path").isTextual()
                        && row.path("path").textValue().equals(parentRegistration.path())) {
                    retained = checkedPin(row).equals(parentRegistration);
                }
            }
            if (!retained) throw new IllegalArgumentException("registration predecessor is absent from the selected parent graph");
        }
        FilePin parentSourcePin = pin(Path.of(text(parentPaths, "source_index")));
        ObjectNode parentSourceMetadata = object(manifest.get("source_index"), "parent source metadata");
        if (!text(parentSourceMetadata, "path_key").equals("source_index")
                || !parentSourceMetadata.path("bytes").isIntegralNumber()
                || parentSourceMetadata.path("bytes").longValue() != parentSourcePin.bytes()
                || !text(parentSourceMetadata, "sha256").equals(parentSourcePin.sha256())) {
            throw new IllegalArgumentException("parent source index differs from its manifest");
        }
        ObjectNode parentSource = object(JSON.readTree(Path.of(parentSourcePin.path()).toFile()), "parent source index");
        List<FilePin> oldFiles = parentSourceFiles(parentSource, parentSourceRoot, machineId);
        ObjectNode nativeRow = object(JSON.readTree(nativeIndex.toFile()), "qualified native index");
        if (!text(nativeRow, "schema").equals("xar.common-native-qualified-producer-index.v1")
                || !text(nativeRow, "machine_id").equals(machineId)
                || !nativeRow.path("live_qualified").isBoolean() || nativeRow.path("live_qualified").booleanValue()) {
            throw new IllegalArgumentException("exact native source-build index and unqualified-live boundary required");
        }
        ObjectNode nativeTools = object(nativeRow.get("runtime_native_tools"), "native tools");
        FilePin dll = checkedPin(nativeTools.get("dll"));
        FilePin injector = checkedPin(nativeTools.get("injector"));
        FilePin flagsPin = checkedPin(nativeRow.get("feature_flags"));
        FilePin buildPin = checkedPin(nativeRow.get("build_output"));
        if (!checkedPin(nativeRow.get("production_qualification")).equals(buildPin)) {
            throw new IllegalArgumentException("native qualification must identify the same completed producer");
        }
        ObjectNode build = object(JSON.readTree(Path.of(buildPin.path()).toFile()), "native build output");
        if (!text(build, "machine_id").equals(machineId)
                || !integerEquals(build.get("compiler_linker_returncode"), 0)
                || !integerEquals(build.get("outer_producer_returncode"), 0)
                || !Boolean.FALSE.equals(booleanValue(build.get("game_execution")))
                || !Boolean.FALSE.equals(booleanValue(build.get("live_qualified")))
                || !checkedPin(build.get("bridge_DLL")).equals(dll)
                || !checkedPin(build.get("reused_injector")).equals(injector)
                || !checkedPin(build.get("feature_flags")).equals(flagsPin)
                || !checkedPin(build.get("cache")).equals(checkedPin(nativeRow.get("cmake_cache")))
                || !checkedPin(build.get("source_manifest")).equals(checkedPin(nativeRow.get("native_source_manifest")))) {
            throw new IllegalArgumentException("native producer completion/source/output binding is incomplete");
        }
        FilePin waitPin = checkedPin(nativeRow.get("producer_original_wait"));
        if (!checkedPin(build.get("producer_original_wait")).equals(waitPin)) {
            throw new IllegalArgumentException("native producer wait differs from completed build");
        }
        ObjectNode wait = object(JSON.readTree(Path.of(waitPin.path()).toFile()), "original producer wait");
        if (!text(wait, "machine_id").equals(machineId) || !integerEquals(wait.get("returncode"), 0)
                || !Boolean.FALSE.equals(booleanValue(wait.get("game_execution")))
                || !Boolean.FALSE.equals(booleanValue(wait.get("live_qualified")))) {
            throw new IllegalArgumentException("original native producer did not finish successfully");
        }
        ObjectNode flags = object(JSON.readTree(Path.of(flagsPin.path()).toFile()), "compiled feature flags");
        for (String flag : REQUIRED_FLAGS) {
            if (!flags.path(flag).isTextual() || !flags.path(flag).textValue().equals("ON")) {
                throw new IllegalArgumentException("native provider not compiled: " + flag);
            }
        }
        if (!flags.path("XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1").isTextual()
                || !flags.path("XAR_CK3_ENABLE_G2_PRISONER_RANSOM_ACTION_PRIVATE_V1").textValue().equals("OFF")) {
            throw new IllegalArgumentException("read-only prisoner preview requires prisoner actions compiled OFF");
        }
        Path source = output.resolve("source");
        FilePin leaseHelper = pin(repo.resolve("promo/ck3_native_war_ai/integration/screen_bus_lease.py"));
        FilePin leaseBus = pin(repo.resolve("tools/codex_task_bus.py"));
        FilePin installedBus = checkedPin(object(runtime.get("allocation"), "allocation").get("task_bus"));
        if (leaseBus.bytes() != installedBus.bytes() || !leaseBus.sha256().equals(installedBus.sha256())) {
            throw new IllegalArgumentException("clean lease task bus differs from selected installed task bus");
        }
        List<Path> selected = sourceFiles(repo);
        long total = 0;
        for (Path path : selected) total = Math.addExact(total, Files.size(path));
        if (total > MAX_SOURCE_BYTES) throw new IllegalArgumentException("finite shared source budget exceeded");
        Files.createDirectories(source);
        List<FilePin> copied = new ArrayList<>();
        for (Path path : selected) {
            if (Files.isSymbolicLink(path)) throw new IllegalArgumentException("shared source cannot follow links");
            FilePin before = pin(path);
            Path target = source.resolve(repo.relativize(path));
            Files.createDirectories(target.getParent());
            Files.copy(path, target, StandardCopyOption.COPY_ATTRIBUTES);
            FilePin after = pin(target);
            if (after.bytes() != before.bytes() || !after.sha256().equals(before.sha256()) || !pin(path).equals(before)) {
                throw new IOException("source changed while freezing: " + path);
            }
            copied.add(after);
        }
        ObjectNode index = JSON.createObjectNode();
        index.put("schema", SOURCE_INDEX_SCHEMA);
        index.put("machine_id", machineId);
        index.put("observed_at_utc", Instant.now().toString());
        index.set("parent_runtime", JSON.valueToTree(pin(baseRuntime)));
        index.set("parent_manifest", JSON.valueToTree(parentManifestPin));
        index.set("parent_source_index", JSON.valueToTree(parentSourcePin));
        index.put("source_only_no_live_qualification", true);
        Map<String, SourceContent> sourceContents = new LinkedHashMap<>();
        for (FilePin file : copied) {
            String relative = source.relativize(Path.of(file.path())).toString().replace(java.io.File.separatorChar, '/');
            sourceRelativePath(relative);
            if (sourceContents.putIfAbsent(relative, new SourceContent(file.bytes(), file.sha256())) != null) {
                throw new IllegalArgumentException("duplicate canonical source file: " + relative);
            }
        }
        // Registration and clean lease inputs remain exact external pins in the
        // existing host projection and allocator_overlay, never relative aliases.
        index.set("files", JSON.valueToTree(sourceContents));
        index.set("canonical_host_projection", JSON.valueToTree(pin(hostProjection)));
        ArrayNode differences = JSON.createArrayNode();
        Map<Path, FilePin> actualByRelativePath = new LinkedHashMap<>();
        for (int number = 0; number < selected.size(); number++) {
            actualByRelativePath.put(repo.relativize(selected.get(number)), copied.get(number));
        }
        int compared = 0;
        for (FilePin old : oldFiles) {
            Path oldPath = Path.of(old.path()).toAbsolutePath().normalize();
            FilePin current = oldPath.startsWith(parentSourceRoot)
                    ? actualByRelativePath.get(parentSourceRoot.relativize(oldPath)) : null;
            if (current != null) compared++;
            if (current != null && (current.bytes() != old.bytes() || !current.sha256().equals(old.sha256()))) {
                ObjectNode difference = JSON.createObjectNode();
                difference.set("parent_declared", JSON.valueToTree(old));
                difference.set("current_frozen", JSON.valueToTree(current));
                differences.add(difference);
            }
        }
        index.put("parent_source_root", parentSourceRoot.toString());
        index.put("selected_repository", repo.toString());
        index.put("comparison_key", "relative_path_below_explicit_parent_source_root");
        index.put("compared_parent_file_count", compared);
        index.put("out_of_scope_parent_file_count", oldFiles.size() - compared);
        index.set("actual_changed_parent_files", differences);
        ObjectNode parentOverlays = object(runtime.get("allocator_overlay"), "parent allocator overlay").deepCopy();
        runtime.set("parent_allocator_overlay", parentOverlays);
        ObjectNode activeOverlays = JSON.createObjectNode();
        ArrayNode overlayProjection = index.putArray("allocator_overlay_projection");
        Path canonicalHostRelative = Path.of("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py");
        for (Map.Entry<String, JsonNode> entry : parentOverlays.properties()) {
            FilePin previous = declaredPin(entry.getValue());
            Path original = Path.of(previous.path()).toAbsolutePath().normalize();
            Path relative = original.startsWith(parentSourceRoot) ? parentSourceRoot.relativize(original)
                    : original.startsWith(parentRepository) ? parentRepository.relativize(original) : null;
            if (relative == null) {
                activeOverlays.set(entry.getKey(), JSON.valueToTree(checkedPin(entry.getValue())));
                continue;
            }
            FilePin replacement = relative.equals(canonicalHostRelative) ? currentHost : actualByRelativePath.get(relative);
            ObjectNode transition = overlayProjection.addObject();
            transition.put("key", entry.getKey());
            transition.set("parent_declared", entry.getValue().deepCopy());
            OverlayDisposition disposition = replacement == null ? OverlayDisposition.PARENT_SOURCE_OUTSIDE_SELECTED_CLOSURE
                    : relative.equals(canonicalHostRelative) ? OverlayDisposition.CURRENT_PROJECTED_HOST
                    : OverlayDisposition.CURRENT_FROZEN_INPUT;
            transition.put("disposition", disposition.name());
            if (replacement != null) {
                transition.set("current_active", JSON.valueToTree(replacement));
                activeOverlays.set(entry.getKey(), JSON.valueToTree(replacement));
            }
        }
        runtime.set("allocator_overlay", activeOverlays);
        Path sourceIndex = output.resolve("source-index.json");
        writeJson(sourceIndex, index);
        ObjectNode paths = object(runtime.get("paths"), "runtime paths");
        paths.put("source_root", source.toString());
        paths.put("source_index", sourceIndex.toString());
        paths.put("native_source_index", nativeIndex.toRealPath().toString());
        paths.put("dll", dll.path());
        paths.put("injector", injector.path());
        paths.put("host", currentHost.path());
        manifest.set("host", keyedPin("host", currentHost));
        if (manifest.has("host_support_projection")) {
            manifest.set("parent_host_support_projection", manifest.remove("host_support_projection"));
        }
        manifest.set("canonical_host_projection", JSON.valueToTree(pin(hostProjection)));
        ObjectNode hostFeatures = object(manifest.get("host_features"), "host features");
        hostFeatures.put("saved_campaign_inject_after_load", true);
        hostFeatures.put("saved_campaign_debug_mode", true);
        runtime.put("repo_root", repo.toString());
        runtime.put("userdir_root", output.resolve("userdirs").toString());
        Files.createDirectory(output.resolve("userdirs"));
        runtime.put("artifacts_root", output.resolve("runs").toString());
        runtime.put("observed_at_utc", Instant.now().toString());
        runtime.put("qualification", Qualification.SHARED_SOURCE_AND_NATIVE_BUILD_SUCCESSOR_LIVE_NOT_QUALIFIED.name());
        Path tools = source.resolve("tools");
        runtime.set("reviewed_launcher", JSON.valueToTree(pin(tools.resolve("ck3_mod_acceptance_launcher.py"))));
        runtime.set("control_queue", JSON.valueToTree(pin(tools.resolve("ck3_mod_acceptance_queue.py"))));
        ObjectNode allocation = object(runtime.get("allocation"), "allocation");
        allocation.put("lease_repo", repo.toString());
        allocation.set("screen_keeper", JSON.valueToTree(pin(tools.resolve("ck3_mod_acceptance_keeper.py"))));
        ObjectNode overlays = object(runtime.get("allocator_overlay"), "allocator overlay");
        if (registrationProvider != null) overlays.set("current-global-registration-provider", JSON.valueToTree(registrationProvider));
        overlays.set("clean-lease-screen-helper", JSON.valueToTree(leaseHelper));
        overlays.set("clean-lease-task-bus", JSON.valueToTree(leaseBus));
        for (FilePin file : copied) {
            if (Path.of(file.path()).startsWith(tools)) overlays.set("shared-successor:" + source.relativize(Path.of(file.path())), JSON.valueToTree(file));
        }
        ObjectNode environment = object(runtime.get("runtime_environment"), "runtime environment");
        JsonNode parentEnvironment = environment.get("PYTHONPATH");
        ArrayNode imports = JSON.createArrayNode();
        imports.add(source.resolve("ck3_autonomous_player/src").toString());
        imports.add(tools.toString());
        imports.add(source.toString());
        if (parentEnvironment != null && parentEnvironment.isArray()) {
            for (JsonNode entry : parentEnvironment) {
                if (!entry.isTextual()) throw new IllegalArgumentException("parent import path must be text");
                Path parentImport = Path.of(entry.textValue()).toAbsolutePath().normalize();
                if (!parentImport.startsWith(parentSourceRoot) && !parentImport.startsWith(parentRepository)) imports.add(entry);
            }
        }
        else if (parentEnvironment != null && parentEnvironment.isTextual()) {
            for (String part : parentEnvironment.textValue().split(java.util.regex.Pattern.quote(java.io.File.pathSeparator))) imports.add(part);
        } else throw new IllegalArgumentException("explicit parent Python import environment required");
        environment.set("PYTHONPATH", imports);
        manifest.set("source_index", keyedPin("source_index", pin(sourceIndex)));
        manifest.set("native_source_index", keyedPin("native_source_index", pin(nativeIndex)));
        ObjectNode nativeManifest = object(manifest.get("native"), "native manifest");
        nativeManifest.set("dll", keyedPin("dll", dll));
        nativeManifest.set("injector", keyedPin("injector", injector));
        ObjectNode evidence = JSON.createObjectNode();
        evidence.put("schema", "ck3-shared-religion-source-build-successor-v1");
        evidence.put("machine_id", machineId);
        evidence.put("observed_at_utc", Instant.now().toString());
        evidence.set("source_index", JSON.valueToTree(pin(sourceIndex)));
        evidence.set("native_source_index", JSON.valueToTree(pin(nativeIndex)));
        evidence.set("feature_flags", JSON.valueToTree(flagsPin));
        evidence.put("actual_live_qualified", false);
        Path evidencePath = output.resolve("SOURCE-BUILD-ADMISSION.json");
        writeJson(evidencePath, evidence);
        ObjectNode capabilities = object(manifest.get("capabilities"), "capabilities");
        for (String tool : TOOLS) {
            ObjectNode status = JSON.createObjectNode();
            status.put("source_build_ready", true);
            status.put("actual_live_qualified", false);
            status.set("evidence", JSON.valueToTree(pin(evidencePath)));
            capabilities.set(tool, status);
        }
        manifest.set("shared_successor", evidence);
        ObjectNode qualification = JSON.createObjectNode();
        if (manifest.has("qualification")) qualification.set("parent_qualification", manifest.get("qualification").deepCopy());
        qualification.set("current_source_index", JSON.valueToTree(pin(sourceIndex)));
        qualification.set("current_native_source_index", JSON.valueToTree(pin(nativeIndex)));
        qualification.put("actual_live_qualified", false);
        manifest.set("qualification", qualification);
        Path newManifest = output.resolve("manifest.json");
        writeJson(newManifest, manifest);
        runtime.set("manifest", JSON.valueToTree(pin(newManifest)));
        Path newRuntime = output.resolve("runtime.json");
        writeJson(newRuntime, runtime);
        return new Result(newRuntime.toString(), newManifest.toString(), sourceIndex.toString(), total, copied.size(),
                Qualification.SHARED_SOURCE_AND_NATIVE_BUILD_SUCCESSOR_LIVE_NOT_QUALIFIED);
    }

    private static List<Path> sourceFiles(Path root) throws IOException {
        List<Path> result = new ArrayList<>();
        for (String relative : List.of("ck3_autonomous_player/src")) {
            try (Stream<Path> files = Files.walk(root.resolve(relative))) {
                result.addAll(files.filter(Files::isRegularFile).filter(SharedRuntimeComposer::sourceFile).sorted().toList());
            }
        }
        try (Stream<Path> files = Files.list(root.resolve("tools"))) {
            result.addAll(files.filter(Files::isRegularFile).filter(path -> {
                String name = path.getFileName().toString();
                return sourceFile(path) && (name.startsWith("ck3_mod_acceptance") || name.startsWith("steam_offline")
                        || Set.of("codex_task_bus.py", "ck3_live_run_id.py", "fixture_engine_prepare.py",
                                "storage_short_commit.py", "desktop_coordinate_map.py", "independent_mod_release.py",
                                "build_native_configured_successor.py", "record_native_capability_segment.py",
                                "build_normal_exit_source_inventory_v1.py").contains(name));
            }).sorted().toList());
        }
        for (String name : List.of("__init__.py", "generic_product_adapter.py", "dynastic_esotericism_core.json",
                "dynastic_esotericism_cold_reload.json", "dynastic_esotericism_old_save_bootstrap.json",
                "dynastic_esotericism_pre_product_seed.json")) {
            result.add(root.resolve("tools/ck3_mod_acceptance_cases").resolve(name));
        }
        result.add(root.resolve("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"));
        result.add(root.resolve("promo/ck3_native_war_ai/integration/screen_bus_lease.py"));
        return result;
    }

    private static boolean sourceFile(Path path) {
        String name = path.getFileName().toString();
        return name.endsWith(".py") || name.endsWith(".json") || name.endsWith(".txt") || name.endsWith(".yml");
    }

    private static Path sourceRelativePath(String value) {
        if (value.isEmpty() || value.indexOf('\\') >= 0 || value.indexOf(':') >= 0 || value.indexOf('\0') >= 0) {
            throw new IllegalArgumentException("canonical relative source path required");
        }
        for (String part : value.split("/", -1)) {
            if (part.isEmpty() || part.equals(".") || part.equals("..")) {
                throw new IllegalArgumentException("source path cannot escape or alias its frozen root");
            }
        }
        Path path = Path.of(value);
        if (path.isAbsolute()) throw new IllegalArgumentException("relative source path required");
        return path;
    }

    static List<FilePin> parentSourceFiles(ObjectNode index, Path sourceRoot, String machineId) {
        if (!text(index, "machine_id").equals(machineId)) throw new IllegalArgumentException("parent source machine differs");
        String schema = text(index, "schema");
        JsonNode files = index.get("files");
        List<FilePin> result = new ArrayList<>();
        if (schema.equals(SOURCE_INDEX_SCHEMA)) {
            ObjectNode entries = object(files, "canonical parent source files");
            for (Map.Entry<String, JsonNode> entry : entries.properties()) {
                Path relative = sourceRelativePath(entry.getKey());
                ObjectNode metadata = object(entry.getValue(), "source content signature");
                JsonNode count = metadata.get("bytes");
                if (metadata.size() != 2 || count == null || !count.isIntegralNumber()
                        || !count.canConvertToLong() || count.longValue() < 0) {
                    throw new IllegalArgumentException("exact source signature fields and integral bytes required");
                }
                SourceContent content = new SourceContent(count.longValue(), text(metadata, "sha256"));
                result.add(new FilePin(sourceRoot.resolve(relative).toString(), content.bytes(), content.sha256()));
            }
        } else if (schema.equals("xar.e04.r15.selected-source-index.v1")
                || schema.equals("ck3-shared-source-frozen-successor-v1")) {
            // Explicit import of pinned historical parents; no new output or
            // live consumer is allowed to use their absolute FilePin list.
            if (files == null || !files.isArray()) throw new IllegalArgumentException("historical parent file list required");
            for (JsonNode file : files) result.add(declaredPin(file));
        } else {
            throw new IllegalArgumentException("unsupported pinned parent source index schema");
        }
        Set<Path> unique = new HashSet<>();
        for (FilePin file : result) {
            if (!unique.add(Path.of(file.path()).toAbsolutePath().normalize())) {
                throw new IllegalArgumentException("duplicate parent source file");
            }
        }
        return List.copyOf(result);
    }

    private static ObjectNode keyedPin(String key, FilePin pin) {
        ObjectNode result = JSON.createObjectNode();
        result.put("path_key", key);
        result.put("bytes", pin.bytes());
        result.put("sha256", pin.sha256());
        return result;
    }

    private static ObjectNode object(JsonNode value, String label) {
        if (!(value instanceof ObjectNode object)) throw new IllegalArgumentException("object required: " + label);
        return object;
    }

    private static String text(ObjectNode object, String field) {
        JsonNode value = object.get(field);
        if (value == null || !value.isTextual() || value.textValue().isEmpty()) throw new IllegalArgumentException("text field required: " + field);
        return value.textValue();
    }

    private static boolean integerEquals(JsonNode value, long expected) {
        return value != null && value.isIntegralNumber() && value.canConvertToLong() && value.longValue() == expected;
    }

    private static Boolean booleanValue(JsonNode value) {
        if (value == null || !value.isBoolean()) throw new IllegalArgumentException("explicit boolean required");
        return value.booleanValue();
    }

    private static FilePin declaredPin(JsonNode value) {
        ObjectNode object = object(value, "file pin");
        JsonNode count = object.get("bytes");
        if (object.size() != 3 || count == null || !count.isIntegralNumber() || !count.canConvertToLong() || count.longValue() < 0) {
            throw new IllegalArgumentException("exact file pin fields and integral byte count required");
        }
        FilePin declared = new FilePin(text(object, "path"), count.longValue(), text(object, "sha256"));
        if (!Path.of(declared.path()).isAbsolute() || !declared.sha256().matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("absolute file path and canonical SHA-256 required");
        }
        return declared;
    }

    private static FilePin checkedPin(JsonNode value) throws IOException {
        FilePin declared = declaredPin(value);
        if (!pin(Path.of(declared.path())).equals(declared)) throw new IOException("frozen input changed: " + declared.path());
        return declared;
    }

    private static FilePin pin(Path input) throws IOException {
        Path path = input.toRealPath();
        byte[] bytes = Files.readAllBytes(path);
        try {
            return new FilePin(path.toString(), bytes.length,
                    HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 provider absent", error);
        }
    }

    private static void writeJson(Path path, ObjectNode value) throws IOException {
        Files.writeString(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsString(value) + "\n",
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    private static Map<String, String> parse(String[] args) {
        Set<String> keys = Set.of("--repo-root", "--base-runtime", "--native-index", "--host-projection", "--output", "--machine-id");
        if (args.length != keys.size() * 2) throw new IllegalArgumentException("all six shared runtime options required");
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < args.length; index += 2) {
            if (!keys.contains(args[index]) || args[index + 1].isBlank() || result.putIfAbsent(args[index], args[index + 1]) != null) {
                throw new IllegalArgumentException("unknown, empty or repeated shared runtime option");
            }
        }
        if (!result.keySet().equals(keys)) throw new IllegalArgumentException("missing shared runtime option");
        return Map.copyOf(result);
    }
}
