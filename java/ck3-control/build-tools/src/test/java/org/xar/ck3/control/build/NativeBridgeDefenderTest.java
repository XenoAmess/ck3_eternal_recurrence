package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class NativeBridgeDefenderTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef pin(String name, String body) throws IOException {
        Path path = temporary.resolve(name); Files.writeString(path, body); return ControlBuild.FileRef.measure(path);
    }
    @Test void missingAdminTokenDisabledAndAckDoNotQualifyExclusionReadback() throws Exception {
        var injector = pin("xar_ck3_bridge_injector.exe", "not executable; data fixture only");
        var manifest = pin("manifest.json", "{\"schema\":\"xar.project-exe-exclusions.v1\",\"files\":[]}");
        for (String status : List.of("disabled", "settings_failed", "running", "verified")) {
            var receipt = pin("receipt-" + status + ".json", "{\"schema\":\"xar.project-exe-exclusions.v1\",\"status\":\"" + status + "\",\"admin_token\":false}");
            assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(receipt, manifest, injector));
        }
    }
    @Test void arbitraryInterpreterAndIncompleteHelperClosureAreRejected() throws Exception {
        var python = pin("other.exe", "fixture"); var helper = pin("other.py", "fixture");
        var runtime = new NativeBridgeDefender.HelperRuntime(temporary.resolve("base"), temporary.resolve("venv"), python, helper, List.of(python), List.of(helper));
        assertThrows(IOException.class, () -> NativeBridgeDefender.verifyHelperRuntime(temporary, runtime));
    }
    @Test void arbitraryNamedBinaryCannotMasqueradeAsProductionPe() throws Exception {
        var file = pin("xar_ck3_bridge.dll", "x".repeat(128));
        assertThrows(IOException.class, () -> NativeBridgeDefender.requirePe(file, true));
        assertThrows(IOException.class, () -> NativeBridgeDefender.requirePe(file, false));
    }
    @Test void nativeReceiptDecimalSizeRejectsBooleanBeforeReadback() throws Exception {
        var mapper = ControlBuild.strictMapper();
        for (String token : List.of("true", "1.0", "\"1\"")) {
            String raw = "{\"path\":\"fixture\",\"size\":" + token + ",\"sha256\":\"fixture\",\"target\":\"fixture\",\"target_id\":\"fixture\"}";
            assertThrows(IOException.class, () -> mapper.readValue(raw, NativeBridgeDefender.ManifestFile.class));
        }
    }

    private record DeclarationFixture(NativeBridgeBuild.Request request, NativeBridgeDefender.ConfiguredGraph graph,
            ControlBuild.FileRef declaration, NativeBridgeDefender.DeclaredManifest manifest, ControlBuild.FileRef manifestPin) { }
    private DeclarationFixture declarationFixture() throws Exception {
        Path source = temporary.resolve("source"), build = temporary.resolve("build"), scratch = temporary.resolve("state");
        Files.createDirectory(source); Files.createDirectory(build); Files.createDirectory(scratch);
        Files.writeString(source.resolve("CMakeLists.txt"), "project(data_fixture_only)");
        Files.writeString(source.resolve("injector.cpp"), "// source fixture, never compiled");
        var mapper = ControlBuild.strictMapper();
        Path reply = build.resolve(".cmake/api/v1/reply"); Files.createDirectories(reply);
        var targets = mapper.createArrayNode();
        for (String name : List.of("xar_ck3_bridge", "xar_ck3_bridge_injector")) {
            var target = mapper.createObjectNode(); target.put("id", name + "::fixture"); target.put("name", name);
            target.put("type", name.endsWith("injector") ? "EXECUTABLE" : "SHARED_LIBRARY");
            target.putObject("paths").put("source", ".");
            target.putArray("sources").addObject().put("path", "injector.cpp");
            target.putArray("artifacts").addObject().put("path", name + (name.endsWith("injector") ? ".exe" : ".dll"));
            Files.write(reply.resolve(name + ".json"), mapper.writeValueAsBytes(target));
            targets.addObject().put("id", name + "::fixture").put("name", name).put("jsonFile", name + ".json");
        }
        var model = mapper.createObjectNode(); model.putObject("paths").put("source", source.toString()).put("build", build.toString());
        var configuration = model.putArray("configurations").addObject(); configuration.put("name", "Release"); configuration.set("targets", targets);
        Files.write(reply.resolve("codemodel.json"), mapper.writeValueAsBytes(model));
        var cmake = mapper.createObjectNode(); cmake.putArray("inputs").addObject().put("path", "CMakeLists.txt");
        Files.write(reply.resolve("cmakeFiles.json"), mapper.writeValueAsBytes(cmake));
        var index = mapper.createObjectNode(); var objects = index.putArray("objects");
        var cm = objects.addObject(); cm.put("kind", "codemodel").put("jsonFile", "codemodel.json"); cm.putObject("version").put("major", 2);
        objects.addObject().put("kind", "cmakeFiles").put("jsonFile", "cmakeFiles.json");
        Files.write(reply.resolve("index-fixture.json"), mapper.writeValueAsBytes(index));
        Files.writeString(build.resolve("CMakeCache.txt"), "CMAKE_BUILD_TYPE:STRING=Release\nBUILD_TESTING:BOOL=OFF\n");
        Files.writeString(build.resolve("build.ninja"), "# data fixture");
        Files.writeString(build.resolve("compile_commands.json"), "[]");
        var toolPins = new java.util.ArrayList<ControlBuild.FileRef>();
        for (String name : List.of("cmd.exe", "vcvars64.bat", "java.exe", "cmake.exe", "ninja.exe", "cl.exe", "link.exe"))
            toolPins.add(pin(name, "data fixture only"));
        var tools = new NativeBridgeBuild.Toolchain(toolPins.get(0), toolPins.get(1), toolPins.get(2), toolPins.get(3),
                toolPins.get(4), toolPins.get(5), toolPins.get(6));
        var qualified = pin("qualified-tools.json", "{}");
        var request = new NativeBridgeBuild.Request(NativeBridgeBuild.REQUEST_SCHEMA, "xenoamess-full-tower-eb9d2c1186",
                NativeBridgeBuild.Stage.ENV, temporary, source, NativeBridgeBuild.inventory(source), build, scratch,
                qualified, tools, List.of(), 1, null, null, (NativeBridgeDefender.Runtime)null);
        var graph = NativeBridgeDefender.readDeclaredGraph(request);
        var requestPin = pin("declaration-request.json", "{}");
        var configure = pin("configure.json", "{}");
        var declarationValue = new NativeBridgeDefender.DeclaredSource("xar.native-declared-output-source/v1",
                request.machineId(), requestPin, configure, graph.graphRefs(), qualified);
        Path declarationPath = temporary.resolve("declaration.json");
        Files.write(declarationPath, RootNativePlanJson.mapper().writeValueAsBytes(declarationValue));
        var declaration = ControlBuild.FileRef.measure(declarationPath);
        var manifest = NativeBridgeDefender.declaredManifest(request, graph, declaration);
        Path manifestPath = temporary.resolve("declared-manifest.json");
        Files.write(manifestPath, mapper.writeValueAsBytes(manifest));
        return new DeclarationFixture(request, graph, declaration, manifest, ControlBuild.FileRef.measure(manifestPath));
    }
    private com.fasterxml.jackson.databind.node.ObjectNode syntheticAdministrativeReceipt(DeclarationFixture fixture) throws Exception {
        var mapper = ControlBuild.strictMapper(); var value = mapper.createObjectNode();
        value.put("schema", NativeBridgeDefender.DECLARED_SCHEMA).put("status", "verified").put("admin_token", true);
        value.put("proof_scope", "DECLARED_PROJECT_EXE_PATH_ONLY").put("settings_success_is_runtime_trust", false)
                .put("partial_mutation", false).put("observed_prior_settings_preserved", true)
                .put("manifest_sha256", NativeProjectExeUac.semanticSha(mapper.valueToTree(fixture.manifest())));
        value.set("declared_outputs", mapper.valueToTree(fixture.manifest().declaredOutputs()));
        value.putArray("before").add("C:/existing/%opaque%/*");
        value.putArray("after").add("C:/existing/%opaque%/*").add(fixture.graph().injector().toString());
        value.putArray("verified_requested_paths").add(fixture.graph().injector().toString()); value.putArray("missing_requested_paths");
        value.put("readback_visibility", "same administrative token and WMI client for before/after")
                .put("namespace", "root\\Microsoft\\Windows\\Defender")
                .put("settings_readback_schema", "xar.project-exe-three-settings-readback/v1")
                .put("settings_readback_complete", true).putNull("settings_readback_error");
        value.put("observed_extensions_unchanged", true).put("observed_processes_unchanged", true)
                .put("settings_readback_process_id", 1234).put("settings_readback_token_user_sid", "S-1-5-21-1-2-3-1001");
        var before = value.putObject("before_settings"); before.set("ExclusionPath", value.get("before").deepCopy());
        before.putArray("ExclusionExtension").add("existing"); before.putArray("ExclusionProcess").add("existing.exe");
        var after = before.deepCopy(); after.set("ExclusionPath", value.get("after").deepCopy()); value.set("after_settings", after);
        return value;
    }
    private ControlBuild.FileRef receiptPin(com.fasterxml.jackson.databind.node.ObjectNode value, String name) throws Exception {
        Path path = temporary.resolve(name); Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value));
        return ControlBuild.FileRef.measure(path);
    }
    @Test void actualConfiguredProducerPreservesAbsentContractAndOldBuiltReaderStillRejects() throws Exception {
        var fixture = declarationFixture(); var mapper = ControlBuild.strictMapper();
        var tree = mapper.valueToTree(fixture.manifest());
        assertFalse(tree.has("files")); assertFalse(tree.path("declared_outputs").get(0).has("sha256"));
        assertFalse(tree.path("declared_outputs").get(0).has("size"));
        assertEquals(fixture.manifest(), mapper.readValue(mapper.writeValueAsBytes(fixture.manifest()), NativeBridgeDefender.DeclaredManifest.class));
        assertEquals(NativeBridgeDefender.DeclaredOutputState.ABSENT, fixture.graph().output().expectedState());
        assertThrows(IOException.class, () -> NativeBridgeDefender.readGraph(fixture.request()));
        var invalid = ((com.fasterxml.jackson.databind.node.ObjectNode)tree).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)invalid.path("declared_outputs").get(0)).put("sha256", "0".repeat(64));
        assertThrows(IOException.class, () -> mapper.treeToValue(invalid, NativeBridgeDefender.DeclaredManifest.class));
    }
    @Test void presentDirectoryAndForeignTargetCannotUseDeclaredMissingMode() throws Exception {
        var fixture = declarationFixture();
        Files.writeString(fixture.graph().injector(), "present data");
        assertThrows(IOException.class, () -> NativeBridgeDefender.readDeclaredGraph(fixture.request()));
        Files.delete(fixture.graph().injector()); Files.createDirectory(fixture.graph().injector());
        assertThrows(IOException.class, () -> NativeBridgeDefender.readDeclaredGraph(fixture.request()));
        assertThrows(IllegalArgumentException.class, () -> new NativeBridgeDefender.DeclaredOutput(
                fixture.request().buildRoot().resolve("foreign.exe").toString(), "foreign", "id", NativeBridgeDefender.DeclaredOutputState.ABSENT));
    }
    @Test void sourceByteDriftRejectsDeclaredProducer() throws Exception {
        var fixture = declarationFixture(); Files.writeString(fixture.request().sourceRoot().resolve("injector.cpp"), "// changed");
        assertThrows(IOException.class, () -> NativeBridgeDefender.declaredManifest(fixture.request(), fixture.graph(), fixture.declaration()));
    }
    @Test void declaredFinalSoftwareGateBindsExactProducerManifestRawReceiptAndActualAdminIdentity() throws Exception {
        var fixture = declarationFixture(); var raw = syntheticAdministrativeReceipt(fixture);
        String interpreter = temporary.resolve("not-executed-python.exe").toString();
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        var receipt = receiptPin(raw, "receipt-ok.json");
        var result = NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter, "S-1-5-21-1-2-3-1001",
                fixture.graph().output(), fixture.manifestPin(), receipt);
        assertEquals("1234", result.processIdDecimal());
        for (String field : List.of("admin_token", "settings_readback_complete", "observed_extensions_unchanged")) {
            var changed = raw.deepCopy(); changed.put(field, false); var ref = receiptPin(changed, field + ".json");
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter,
                    "S-1-5-21-1-2-3-1001", fixture.graph().output(), fixture.manifestPin(), ref));
        }
        var wrongPid = raw.deepCopy(); wrongPid.put("settings_readback_process_id", 1235);
        var pidRef = receiptPin(wrongPid, "wrong-pid.json");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter,
                "S-1-5-21-1-2-3-1001", fixture.graph().output(), fixture.manifestPin(), pidRef));
        var wrongSid = raw.deepCopy(); wrongSid.put("settings_readback_token_user_sid", "S-1-5-21-1-2-3-1002");
        var sidRef = receiptPin(wrongSid, "wrong-sid.json");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter,
                "S-1-5-21-1-2-3-1001", fixture.graph().output(), fixture.manifestPin(), sidRef));
        var timeout = new NativeProjectExeUac.TerminalProof(true, identity, true, true, true, "0");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(timeout, interpreter,
                "S-1-5-21-1-2-3-1001", fixture.graph().output(), fixture.manifestPin(), receipt));
        var mixed = raw.deepCopy(); mixed.putArray("files");
        assertThrows(IOException.class, () -> NativeBridgeDefender.readDeclaredVerified(receiptPin(mixed, "mixed.json"),
                fixture.manifestPin(), fixture.graph().output()));
    }
    private record BuiltFixtureCodec(ControlBuild.FileRef executable, ControlBuild.FileRef manifest,
            com.fasterxml.jackson.databind.node.ObjectNode raw) { }
    private BuiltFixtureCodec builtFixtureCodec() throws Exception {
        return builtFixtureCodec(declarationFixture(),
                NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName(), "built-fixture");
    }
    private BuiltFixtureCodec builtFixtureCodec(DeclarationFixture declaration, String target, String tag) throws Exception {
        var mapper = ControlBuild.strictMapper();
        var executable = pin(target + ".exe", "software codec bytes, never a Native qualification");
        var manifest = mapper.createObjectNode(); manifest.put("schema", "xar.project-exe-exclusions.v1");
        manifest.put("repo", temporary.toString()).put("source_dir", declaration.request().sourceRoot().toString())
                .put("build_dir", declaration.request().buildRoot().toString()).put("configuration", "Release");
        manifest.putArray("requested_targets").add(target); manifest.put("external_candidate", "java-native-launch-reviewed-source");
        var files = manifest.putArray("files"); var row = files.addObject();
        row.put("path", executable.path()).put("size", executable.bytes()).put("sha256", executable.sha256())
                .put("target", target).put("target_id", target + "::software");
        var manifestRef = receiptPin(manifest, tag + "-manifest.json");
        var raw = syntheticAdministrativeReceipt(declaration); raw.put("schema", "xar.project-exe-exclusions.v1");
        raw.remove("proof_scope"); raw.remove("declared_outputs"); raw.set("files", files.deepCopy());
        raw.put("manifest_sha256", NativeProjectExeUac.semanticSha(manifest));
        raw.putArray("after").add("C:/existing/%opaque%/*").add(executable.path());
        raw.putArray("verified_requested_paths").add(executable.path());
        ((com.fasterxml.jackson.databind.node.ObjectNode)raw.get("after_settings")).set("ExclusionPath", raw.get("after").deepCopy());
        return new BuiltFixtureCodec(executable, manifestRef, raw);
    }

    @Test void allFiveHolyTargetsUseTheSameExactSingletonReceiptAndRetainedHistoryBoundary() throws Exception {
        // Software-only administrative-shaped receipts; no Windows setting, process launch or Native qualification.
        var declaration = declarationFixture();
        var targets = List.of(NativeFixtureBuild.FixtureTarget.HOLY_ORDER_WAR_ELIGIBILITY,
                NativeFixtureBuild.FixtureTarget.HOLY_ORDER_SERVICE_LIFECYCLE,
                NativeFixtureBuild.FixtureTarget.HOLY_ORDER_TROOP_ASSOCIATION,
                NativeFixtureBuild.FixtureTarget.HOLY_ORDER_HIRE_COST_CONTEXT,
                NativeFixtureBuild.FixtureTarget.HOLY_ORDER_CURRENT_REINFORCEMENT);
        var exactNames = List.of("xar_ck3_12003_holy_order_war_eligibility_test",
                "xar_ck3_12003_holy_order_service_lifecycle_test",
                "xar_ck3_12003_holy_order_troop_association_test",
                "xar_ck3_12003_holy_order_hire_cost_context_test",
                "xar_ck3_12003_holy_order_current_reinforcement_test");
        String interpreter = temporary.resolve("not-executed-base.exe").toString(), sid = "S-1-5-21-1-2-3-1001";
        var process = new NativeProjectExeUac.ProcessIdentity("1234", "1", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, process, true, true, false, "0");
        for (int index = 0; index < targets.size(); index++) {
            String target = targets.get(index).targetName(), tag = "holy-" + index;
            assertEquals(exactNames.get(index), target);
            var fixture = builtFixtureCodec(declaration, target, tag);
            for (boolean nullable : List.of(false, true)) {
                var raw = nullable ? nullableAdministrativeReceipt(fixture.raw()) : fixture.raw();
                var receipt = receiptPin(raw, tag + "-receipt-" + nullable + ".json");
                var proof = NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                        fixture.executable(), target, fixture.manifest(), receipt);
                assertEquals("1234", proof.processIdDecimal());
                assertEquals(nullable, proof instanceof NativeProjectExeUac.NullableSettingsReadback);
                String wrongTarget = targets.get((index + 1) % targets.size()).targetName();
                assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal,
                        interpreter, sid, fixture.executable(), wrongTarget, fixture.manifest(), receipt));
                assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(receipt,
                        fixture.manifest(), fixture.executable()));
                var broker = raw.deepCopy(); broker.put("broker_schema", "xar.project-exe-broker.receipt.v1");
                var brokerReceipt = receiptPin(broker, tag + "-broker-" + nullable + ".json");
                assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal,
                        interpreter, sid, fixture.executable(), target, fixture.manifest(), brokerReceipt));
            }
            Path retained = temporary.resolve(tag + "-retained.exe");
            Files.copy(Path.of(fixture.executable().path()), retained);
            var retainedRef = ControlBuild.FileRef.measure(retained);
            Files.delete(Path.of(fixture.executable().path()));
            var originalReceipt = receiptPin(fixture.raw(), tag + "-history.json");
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal,
                    interpreter, sid, fixture.executable(), target, fixture.manifest(), originalReceipt));
            assertEquals("1234", NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                    fixture.executable(), target, fixture.manifest(), originalReceipt, retainedRef).processIdDecimal());
        }
    }

    @Test void originalBuiltReceiptChecksAreSharedByTheFiniteFixtureAndKeepInjectorScopeStrict() throws Exception {
        var fixture = builtFixtureCodec(); var receipt = receiptPin(fixture.raw(), "built-fixture-ok.json");
        String target = NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName();
        NativeBridgeDefender.requireDirectBuiltFixtureReceipt(receipt, fixture.manifest(), fixture.executable(), target);
        assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(receipt, fixture.manifest(), fixture.executable()));
        for (String field : List.of("partial_mutation", "settings_success_is_runtime_trust")) {
            var raw = fixture.raw().deepCopy(); raw.put(field, true);
            var changed = receiptPin(raw, "built-" + field + ".json");
            assertThrows(IOException.class, () -> NativeBridgeDefender.requireDirectBuiltFixtureReceipt(changed, fixture.manifest(), fixture.executable(), target));
        }
        var broker = fixture.raw().deepCopy(); broker.put("broker_schema", "xar.project-exe-broker.receipt.v1");
        assertThrows(IOException.class, () -> NativeBridgeDefender.requireDirectBuiltFixtureReceipt(
                receiptPin(broker, "built-fixture-broker.json"), fixture.manifest(), fixture.executable(), target));
    }

    @Test void fixtureSoftwareCompletionRequiresTheActualDirectProcessSidAndAllThreeArrays() throws Exception {
        var fixture = builtFixtureCodec(); String interpreter = temporary.resolve("not-executed-base.exe").toString();
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        String target = NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName(), sid = "S-1-5-21-1-2-3-1001";
        var good = receiptPin(fixture.raw(), "built-completion-ok.json");
        assertEquals("1234", NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid, fixture.executable(),
                target, fixture.manifest(), good).processIdDecimal());
        for (String kind : List.of("pid", "sid", "array", "incomplete", "manifest")) {
            var raw = fixture.raw().deepCopy();
            switch (kind) {
                case "pid" -> raw.put("settings_readback_process_id", 999);
                case "sid" -> raw.put("settings_readback_token_user_sid", "S-1-5-21-1-2-3-1002");
                case "array" -> ((com.fasterxml.jackson.databind.node.ObjectNode)raw.get("after_settings")).putArray("ExclusionProcess").add("changed.exe");
                case "incomplete" -> raw.put("settings_readback_complete", false);
                case "manifest" -> raw.put("manifest_sha256", "0".repeat(64));
                default -> throw new AssertionError(kind);
            }
            var changed = receiptPin(raw, "built-completion-" + kind + ".json");
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                    fixture.executable(), target, fixture.manifest(), changed));
        }
        var timedOut = new NativeProjectExeUac.TerminalProof(true, identity, true, true, true, "0");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(timedOut, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), good));
        var redirector = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", temporary.resolve("venv-redirector.exe").toString());
        var wrongImage = new NativeProjectExeUac.TerminalProof(true, redirector, true, true, false, "0");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(wrongImage, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), good));
    }

    @Test void builtFixturePublicCodecAndCliDispatchRejectUnqualifiedLineageBeforeAnyLaunch() throws Exception {
        var fixture = builtFixtureCodec();
        Path base = temporary.resolve("fixture-python-base"); Files.createDirectories(base);
        Path image = base.resolve("python.exe"); Files.writeString(image, "codec only");
        var runtime = new NativeBridgeDefender.ManifestRuntime(NativeBridgeDefender.ManifestRuntime.DIRECT_SCHEMA,
                base, temporary.resolve("fixture-venv"), ControlBuild.FileRef.measure(image),
                pin("fixture-helper.py", "codec only"), pin("fixture-inventory.json", "{}"));
        var noQualification = pin("no-qualified-fixture-plan.json", "{}");
        String output = temporary.resolve("fixture-register").toString();
        var plan = new NativeProjectExeUac.BuiltFixturePlan(NativeProjectExeUac.BUILT_FIXTURE_PLAN_SCHEMA,
                "xenoamess-full-tower-eb9d2c1186", "2026-10-26T22:00:00Z", "2026-10-26T23:00:00Z",
                "/root/native_fixtures63", "S-1-5-21-1-2-3-1001", 120, noQualification, noQualification, noQualification,
                noQualification, List.of(noQualification), List.of(noQualification), runtime, fixture.manifest(), output,
                output + "/helper.json", output + "/INTENT.json", output + "/launch.json", output + "/result.json");
        var mapper = ControlBuild.strictMapper(); byte[] encoded = mapper.writeValueAsBytes(plan);
        assertEquals(plan, NativeProjectExeUac.parseBuiltFixturePlan(encoded));
        var pin = pin("built-plan.json", new String(encoded, java.nio.charset.StandardCharsets.UTF_8));
        var direct = assertThrows(IOException.class, () -> NativeProjectExeUac.reviewBuiltFixture(Path.of(pin.path())));
        var cli = assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{"review", pin.path()}));
        assertEquals(direct.getMessage(), cli.getMessage());
        assertFalse(Files.exists(Path.of(plan.intentPath())));
        Path unproducedManifest = temporary.resolve("must-not-be-produced-manifest.json");
        assertThrows(IOException.class, () -> NativeProjectExeUac.main(new String[]{"prepare-built-fixture-manifest",
                noQualification.path(), noQualification.path(), noQualification.path(), unproducedManifest.toString()}));
        assertFalse(Files.exists(unproducedManifest));
        for (String kind : List.of("missing", "boolean", "old-schema", "wrong-owner")) {
            var raw = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(plan);
            switch (kind) {
                case "missing" -> raw.remove("build_actual_ref");
                case "boolean" -> raw.put("wait_seconds", true);
                case "old-schema" -> raw.put("schema", "xar.exact-two-exe-uac-plan/v2");
                case "wrong-owner" -> raw.put("owner", "/root/native_fixture09");
                default -> throw new AssertionError(kind);
            }
            assertThrows(IOException.class, () -> NativeProjectExeUac.parseBuiltFixturePlan(mapper.writeValueAsBytes(raw)));
        }
        assertNotEquals(NativeProjectExeUac.ProofScope.DECLARED_PROJECT_EXE_PATH_ONLY,
                NativeProjectExeUac.ProofScope.SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS);
    }

    @Test void fixtureHistoryUsesQualifiedRetainedBytesWhileLiveCompletionStillRequiresTheOriginalExe() throws Exception {
        var fixture = builtFixtureCodec(); var receipt = receiptPin(fixture.raw(), "retained-completion.json");
        Path retained = temporary.resolve("retained-fixture.exe"); Files.copy(Path.of(fixture.executable().path()), retained);
        var copy = ControlBuild.FileRef.measure(retained); Files.delete(Path.of(fixture.executable().path()));
        String interpreter = temporary.resolve("not-executed-base.exe").toString(), sid = "S-1-5-21-1-2-3-1001";
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        String target = NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName();
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), receipt));
        assertEquals("1234", NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), receipt, copy).processIdDecimal());
        var wrongCopy = pin("different-retained-fixture.exe", "different content");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), receipt, wrongCopy));
    }

    private com.fasterxml.jackson.databind.node.ObjectNode nullableAdministrativeReceipt(
            com.fasterxml.jackson.databind.node.ObjectNode original) {
        var value = original.deepCopy();
        value.put("settings_readback_schema", "xar.project-exe-three-settings-readback/v2");
        for (String side : List.of("before", "after")) {
            var settings = (com.fasterxml.jackson.databind.node.ObjectNode)value.get(side + "_settings");
            settings.putNull("ExclusionExtension");
            var observations = value.putArray(side + "_property_observations");
            for (String name : List.of("ExclusionPath", "ExclusionExtension", "ExclusionProcess"))
                observations.addObject().put("name", name).put("cim_type", 8).put("is_array", true)
                        .put("value_state", settings.get(name).isNull() ? "OBSERVED_NULLABLE_VALUE" : "STRING_ARRAY");
        }
        value.put("nullable_observation_scope",
                "Same administrative WMI client, one MSFT_MpPreference instance and existing Name/CIMType8/IsArray=true properties. "
                + "Python None is retained as an observed nullable CIM value, distinct from an empty array; raw VARIANT is not remeasured by this reader. "
                + "No assertion that effective exclusions are empty or unconfigured.");
        return value;
    }

    @Test void actualDirectBuiltConsumerRetainsObservedNullablePropertiesAndRejectsUnqualifiedEvidence() throws Exception {
        // Synthetic administrative bytes exercise the software boundary; no Windows setting or qualification is produced.
        var fixture = builtFixtureCodec(); var raw = nullableAdministrativeReceipt(fixture.raw());
        String interpreter = temporary.resolve("not-executed-base.exe").toString(), sid = "S-1-5-21-1-2-3-1001";
        String target = NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName();
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        var proof = NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid,
                fixture.executable(), target, fixture.manifest(), receiptPin(raw, "built-nullable-ok.json"));
        assertInstanceOf(NativeProjectExeUac.NullableSettingsReadback.class, proof);
        assertNull(proof.before().exclusionExtension()); assertNull(proof.after().exclusionExtension());
        assertEquals(List.of("existing.exe"), proof.after().exclusionProcess());
        var mapper = ControlBuild.strictMapper(); var encoded = mapper.writeValueAsBytes(proof);
        assertEquals(proof, mapper.readValue(encoded, NativeProjectExeUac.ThreeSettingsReadback.class));
        assertTrue(mapper.readTree(encoded).path("before").get("ExclusionExtension").isNull());
        int index = 0;
        for (String kind : List.of("v1-null", "missing-observation", "null-to-empty", "boolean-cim",
                "wrong-cim", "not-array", "wrong-state", "wrong-name", "scope", "null-path", "pid", "sid", "admin")) {
            var changed = raw.deepCopy();
            switch (kind) {
                case "v1-null" -> {
                    changed.put("settings_readback_schema", "xar.project-exe-three-settings-readback/v1");
                    changed.remove(List.of("before_property_observations", "after_property_observations", "nullable_observation_scope"));
                }
                case "missing-observation" -> changed.remove("after_property_observations");
                case "null-to-empty" -> {
                    ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("after_settings")).putArray("ExclusionExtension");
                    ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("after_property_observations").get(1))
                            .put("value_state", "STRING_ARRAY");
                }
                case "boolean-cim" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("cim_type", true);
                case "wrong-cim" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("cim_type", 9);
                case "not-array" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("is_array", false);
                case "wrong-state" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("value_state", "STRING_ARRAY");
                case "wrong-name" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("name", "ExclusionPath");
                case "scope" -> changed.put("nullable_observation_scope", "empty means unconfigured");
                case "null-path" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("after_settings")).putNull("ExclusionPath");
                case "pid" -> changed.put("settings_readback_process_id", 999);
                case "sid" -> changed.put("settings_readback_token_user_sid", "S-1-5-21-1-2-3-1002");
                case "admin" -> changed.put("admin_token", false);
                default -> throw new AssertionError(kind);
            }
            var receipt = receiptPin(changed, "built-nullable-reject-" + index++ + ".json");
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter,
                    sid, fixture.executable(), target, fixture.manifest(), receipt), kind);
        }
    }

    @Test void actualDeclaredConsumerPreservesVersionedNullableProofAndOriginalTerminalGuards() throws Exception {
        var fixture = declarationFixture(); var raw = nullableAdministrativeReceipt(syntheticAdministrativeReceipt(fixture));
        String interpreter = temporary.resolve("not-executed-base.exe").toString(), sid = "S-1-5-21-1-2-3-1001";
        var identity = new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, identity, true, true, false, "0");
        var receipt = receiptPin(raw, "declared-nullable-ok.json");
        var proof = NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter, sid,
                fixture.graph().output(), fixture.manifestPin(), receipt);
        assertInstanceOf(NativeProjectExeUac.NullableSettingsReadback.class, proof);
        var mapper = ControlBuild.strictMapper();
        assertEquals(proof, mapper.readValue(mapper.writeValueAsBytes(proof), NativeProjectExeUac.ThreeSettingsReadback.class));
        assertNull(proof.before().exclusionExtension()); assertNull(proof.after().exclusionExtension());
        var arrayOnly = syntheticAdministrativeReceipt(fixture);
        arrayOnly.putArray("before_property_observations");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(terminal, interpreter, sid,
                fixture.graph().output(), fixture.manifestPin(), receiptPin(arrayOnly, "v1-mixed-observations.json")));
        var timedOut = new NativeProjectExeUac.TerminalProof(true, identity, true, true, true, "0");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(timedOut, interpreter, sid,
                fixture.graph().output(), fixture.manifestPin(), receipt));
        var wrongImage = new NativeProjectExeUac.TerminalProof(true,
                new NativeProjectExeUac.ProcessIdentity("1234", "18446744073709551615", temporary.resolve("redirector.exe").toString()),
                true, true, false, "0");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyDeclaredCompletion(wrongImage, interpreter, sid,
                fixture.graph().output(), fixture.manifestPin(), receipt));
        var persisted = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(proof);
        for (String kind : List.of("missing", "unknown-version", "extra", "wrong-type")) {
            var changed = persisted.deepCopy();
            switch (kind) {
                case "missing" -> changed.remove("before_property_observations");
                case "unknown-version" -> changed.put("schema", "xar.project-exe-three-settings-readback/v3");
                case "extra" -> changed.put("assumed_effective_empty", true);
                case "wrong-type" -> ((com.fasterxml.jackson.databind.node.ObjectNode)changed.path("before_property_observations").get(1)).put("cim_type", true);
                default -> throw new AssertionError(kind);
            }
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(changed), NativeProjectExeUac.ThreeSettingsReadback.class), kind);
        }
    }

    private byte[] originalCorpus(String name, String expectedSha) throws Exception {
        try (var input = NativeBridgeDefenderTest.class.getResourceAsStream("/" + name)) {
            assertNotNull(input, "Original producer corpus is mandatory");
            byte[] raw = input.readAllBytes();
            assertEquals(expectedSha, java.util.HexFormat.of().formatHex(
                    java.security.MessageDigest.getInstance("SHA-256").digest(raw)));
            return raw;
        }
    }
    @Test void originalPythonDeclaredProducerBytesReachTheSameVersionedJavaSettingsReader() throws Exception {
        // Original FakeCIM producer bytes and provenance; this is software evidence with no administrative Windows observation.
        var mapper = ControlBuild.strictMapper();
        var raw = mapper.readTree(originalCorpus("declared-nullable-python-producer-resume63.json",
                "f78fd5539e654ecc5e19fd2c5dab478b3f7af9f2fe7bc5bd65a1882a770859dc"));
        var source = mapper.readTree(originalCorpus("declared-nullable-python-producer-resume63.provenance.json",
                "b2f84007e4fcdc19c87783606a6cb8673bdfce98858bc371dfb351e7b917d5d0"));
        assertEquals("SOFTWARE_FAKE_CIM_ONLY_NOT_ADMINISTRATIVE_SYSTEM_EVIDENCE", source.path("source_kind").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", source.path("machine_id").textValue());
        assertEquals("b6dd3d3dc7b4158f6646ab083925a2be898368c3c96b824071856e286960ddec",
                source.path("producer_ref").path("sha256").textValue());
        assertEquals("738803513191a8776159b3787cad69b7bcceb9564d8d2eecd8472715863e5382",
                source.path("test_ref").path("sha256").textValue());
        assertEquals(0, source.path("actual_wmi_calls").intValue());
        assertEquals(0, source.path("actual_add_calls").intValue());
        assertEquals(0, source.path("actual_uac_calls").intValue());
        assertEquals("xar.project-exe-declared-path-exclusions/v1", raw.path("schema").textValue());
        assertEquals("xar.project-exe-three-settings-readback/v2", raw.path("settings_readback_schema").textValue());
        String sid = "S-1-5-21-101-102-103-1001";
        assertEquals(sid, raw.path("settings_readback_token_user_sid").textValue());
        assertEquals(149424L, raw.path("settings_readback_process_id").longValue());
        // Only the software reader's PID input is exercised; this is not a captured Windows process terminal.
        var softwareHelper = new WindowsJobProcess.ProcessIdentity(149424L, "1",
                temporary.resolve("software-producer-identity.exe").toString());
        var proof = NativeProjectExeUac.qualifyThreeSettings(raw, sid, softwareHelper);
        assertInstanceOf(NativeProjectExeUac.NullableSettingsReadback.class, proof);
        assertNull(proof.before().exclusionExtension()); assertNull(proof.after().exclusionExtension());
        assertNull(proof.before().exclusionProcess()); assertNull(proof.after().exclusionProcess());
        assertEquals(proof, mapper.readValue(mapper.writeValueAsBytes(proof), NativeProjectExeUac.ThreeSettingsReadback.class));
        var wrongPid = ((com.fasterxml.jackson.databind.node.ObjectNode)raw).deepCopy();
        wrongPid.put("settings_readback_process_id", 149425);
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyThreeSettings(wrongPid, sid, softwareHelper));
    }
    @Test void capturedFixtureObservationPinsRejectChangedLeaseEvidenceAndCannotBeRecreatedAtAnotherPath() throws Exception {
        var fixture = builtFixtureCodec(); var mapper = ControlBuild.strictMapper(); var marker = pin("lease-marker.json", "{}");
        String machine = "xenoamess-full-tower-eb9d2c1186", sid = "S-1-5-21-1-2-3-1001";
        String interpreter = temporary.resolve("not-executed-base.exe").toString();
        var process = new NativeProjectExeUac.ProcessIdentity("1234", "1", interpreter);
        var terminal = new NativeProjectExeUac.TerminalProof(true, process, true, true, false, "0");
        var review = new NativeProjectExeUac.BuiltFixtureReview("xar.native-built-fixture-uac-review/v1",
                machine, "2026-10-26T23:00:00Z", marker, marker, marker, marker, fixture.manifest(), "0".repeat(64),
                fixture.executable(), sid, "runas", interpreter, "", temporary.toString(), 0, 120,
                "2026-10-26T23:05:00Z", List.of(marker));
        // Synthetic native identity is serialized by the real observation writer; no Windows lease is claimed by this test.
        var guarded = new NativeProjectExeUac.GuardedInput(marker.path(),
                new NativeProjectExeUac.NativeFileIdentity("1", "2", Long.toString(marker.bytes()), marker.path(), false));
        var intent = new NativeProjectExeUac.BuiltFixtureIntent("xar.native-built-fixture-uac-intent/v1",
                machine, "2026-10-26T23:00:01Z", review, List.of(guarded), "No automatic resubmission. Timeout/crash/missing receipt requires original process and settings resolution.");
        Path intentPath = temporary.resolve("original-intent.json"), launchPath = temporary.resolve("original-launch.json");
        var intentRef = NativeProjectExeUac.writeBuiltFixtureIntent(intentPath, intent);
        var launch = new NativeProjectExeUac.CurrentNativeBuildLaunch("xar.native-built-fixture-uac-launch/v1",
                machine, "2026-10-26T23:00:02Z", true, process, true, sid);
        var launchRef = NativeProjectExeUac.writeBuiltFixtureLaunch(launchPath, launch);
        byte[] original = NativeProjectExeUac.readBuiltFixtureObservation(intentRef, intentPath);
        assertEquals(intent, mapper.readValue(original, NativeProjectExeUac.BuiltFixtureIntent.class));
        assertEquals(launch, mapper.readValue(NativeProjectExeUac.readBuiltFixtureObservation(launchRef, launchPath),
                NativeProjectExeUac.CurrentNativeBuildLaunch.class));
        assertThrows(IOException.class, () -> NativeProjectExeUac.writeBuiltFixtureIntent(intentPath, intent));
        for (String field : List.of("file_id_decimal", "native_final_path")) {
            var changed = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(original);
            var identity = (com.fasterxml.jackson.databind.node.ObjectNode)changed.path("guarded_inputs").get(0).path("identity");
            identity.put(field, field.equals("file_id_decimal") ? "3" : temporary.resolve("other.cpp").toString());
            Files.write(intentPath, mapper.writeValueAsBytes(changed));
            assertThrows(IOException.class, () -> NativeProjectExeUac.readBuiltFixtureObservation(intentRef, intentPath), field);
            Files.write(intentPath, original);
        }
        Path wrongPath = temporary.resolve("copied-intent.json"); Files.write(wrongPath, original);
        var wrongPin = ControlBuild.FileRef.measure(wrongPath);
        assertThrows(IOException.class, () -> NativeProjectExeUac.readBuiltFixtureObservation(wrongPin, intentPath));
        byte[] originalLaunch = NativeProjectExeUac.readBuiltFixtureObservation(launchRef, launchPath);
        var changedLaunch = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(originalLaunch);
        ((com.fasterxml.jackson.databind.node.ObjectNode)changedLaunch.get("process_identity")).put("pid_decimal", "1235");
        Files.write(launchPath, mapper.writeValueAsBytes(changedLaunch));
        assertThrows(IOException.class, () -> NativeProjectExeUac.readBuiltFixtureObservation(launchRef, launchPath));
        Files.write(launchPath, originalLaunch);
        for (boolean nullable : List.of(false, true)) {
            var raw = nullable ? nullableAdministrativeReceipt(fixture.raw()) : fixture.raw();
            var rawReceipt = receiptPin(raw, "observation-result-receipt-" + nullable + ".json");
            var settings = NativeProjectExeUac.qualifyBuiltFixtureCompletion(terminal, interpreter, sid, fixture.executable(),
                    NativeFixtureBuild.FixtureTarget.COMBATROLES_COMMANDER.targetName(), fixture.manifest(), rawReceipt);
            var result = new NativeProjectExeUac.BuiltFixtureRegistrationResult(NativeProjectExeUac.BUILT_FIXTURE_RESULT_SCHEMA,
                    machine, "2026-10-26T23:00:03Z", NativeProjectExeUac.Status.VERIFIED,
                    NativeProjectExeUac.ProofScope.SAME_OWNER_ADMIN_BUILT_FIXTURE_THREE_SETTINGS, marker, marker, marker,
                    fixture.executable(), review, true, true, null, process, true, sid, "0", false, rawReceipt, settings,
                    List.of(), false, false, terminal, intentRef, launchRef);
            byte[] encoded = mapper.writeValueAsBytes(result);
            assertEquals(result, mapper.readValue(encoded, NativeProjectExeUac.BuiltFixtureRegistrationResult.class));
            String trailing = new String(encoded, java.nio.charset.StandardCharsets.UTF_8) + " {}";
            assertThrows(IOException.class, () -> mapper.readValue(trailing, NativeProjectExeUac.BuiltFixtureRegistrationResult.class));
            for (String field : List.of("intent_ref", "launch_observation_ref")) {
                var persisted = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(result);
                persisted.remove(field);
                assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(persisted),
                        NativeProjectExeUac.BuiltFixtureRegistrationResult.class));
                persisted.putNull(field);
                assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(persisted),
                        NativeProjectExeUac.BuiltFixtureRegistrationResult.class));
            }
        }
    }

    private List<ControlBuild.FileRef> leaseRows(String group, int count) {
        var rows = new java.util.ArrayList<ControlBuild.FileRef>();
        for (int i = 0; i < count; i++)
            rows.add(new ControlBuild.FileRef(temporary.resolve(group).resolve(i + ".dat").toString(), 0, "0".repeat(64)));
        return rows;
    }
    private List<Object> leaseReviews(ControlBuild.FileRef marker, List<ControlBuild.FileRef> leased) {
        String machine = "xenoamess-full-tower-eb9d2c1186", opened = "2026-10-27T06:00:00Z";
        String deadline = "2026-10-27T07:00:00Z", sid = "S-1-5-21-1-2-3-1001";
        String image = temporary.resolve("software-only-python.exe").toString();
        Path buildRoot = temporary.resolve("lease-build");
        var injector = new ControlBuild.FileRef(buildRoot.resolve("xar_ck3_bridge_injector.exe").toString(), 64, "0".repeat(64));
        var current = new NativeProjectExeUac.CurrentNativeBuild("xar.current-native-build-uac-input/v2",
                temporary.resolve("lease-source").toString(), buildRoot.toString(), marker, marker, marker, marker, marker, injector);
        var output = new NativeBridgeDefender.DeclaredOutput(injector.path(), "xar_ck3_bridge_injector",
                "injector::software", NativeBridgeDefender.DeclaredOutputState.ABSENT);
        return List.of(
                new NativeProjectExeUac.CurrentNativeBuildReview("xar.current-native-build-uac-review/v1",
                        machine, opened, marker, current, marker, marker, sid, "runas", image, "", temporary.toString(),
                        0, 120, deadline, leased),
                new NativeProjectExeUac.DeclaredPathReview("xar.native-declared-exe-uac-review/v1",
                        machine, opened, marker, marker, marker, "0".repeat(64), output, sid, "runas", image, "",
                        temporary.toString(), 0, 120, deadline, leased),
                new NativeProjectExeUac.BuiltFixtureReview("xar.native-built-fixture-uac-review/v1",
                        machine, opened, marker, marker, marker, marker, marker, "0".repeat(64), injector, sid, "runas",
                        image, "", temporary.toString(), 0, 120, deadline, leased));
    }
    @Test void fullRuntimeLeaseReachesAllThreePersistedReviews() throws Exception {
        var rows = new java.util.ArrayList<>(leaseRows("runtime", 25875));
        rows.addAll(leaseRows("compile", 3984)); rows.addAll(leaseRows("retained", 3984));
        var expected = List.copyOf(rows);
        rows.add(expected.getFirst()); rows.add(expected.getLast());
        var leased = NativeProjectExeUac.mergeLeaseInputs(rows);
        assertEquals(expected, leased); assertEquals(33843, leased.size());
        assertThrows(UnsupportedOperationException.class, () -> leased.add(expected.getFirst()));
        var marker = pin("large-lease-marker.json", "{}"); var mapper = ControlBuild.strictMapper();
        for (Object review : leaseReviews(marker, leased)) {
            byte[] raw = mapper.writeValueAsBytes(review);
            assertEquals(review, mapper.readValue(raw, review.getClass()));
            var tree = mapper.readTree(raw).path("guarded_input_refs");
            assertEquals(33843, tree.size());
            assertEquals(expected.getLast().path(), tree.get(33842).path("path").textValue());
        }
        assertThrows(IllegalArgumentException.class, () -> NativeBridgeBuild.unique(leased));
        assertEquals(16000, NativeBridgeBuild.unique(leased.subList(0, 16000)).size());
    }
    @Test void leaseBoundsConflictsAndPersistedDuplicatesStayStrict() throws Exception {
        var rows = leaseRows("bounded", 65536);
        assertEquals(65536, NativeProjectExeUac.mergeLeaseInputs(rows).size());
        var overflow = new java.util.ArrayList<>(rows); overflow.add(leaseRows("overflow", 1).getFirst());
        assertThrows(IOException.class, () -> NativeProjectExeUac.mergeLeaseInputs(overflow));
        var marker = pin("bounded-lease-marker.json", "{}");
        assertThrows(IllegalArgumentException.class, () -> leaseReviews(marker, overflow));
        var first = rows.getFirst();
        var conflicting = new ControlBuild.FileRef(first.path(), 1, first.sha256());
        assertThrows(IOException.class, () -> NativeProjectExeUac.mergeLeaseInputs(List.of(first, conflicting)));
        var alias = new ControlBuild.FileRef(temporary.resolve("bounded").resolve("..").resolve("bounded")
                .resolve("0.dat").toString(), first.bytes(), first.sha256());
        assertThrows(IOException.class, () -> NativeProjectExeUac.mergeLeaseInputs(List.of(first, alias)));
        assertThrows(IllegalArgumentException.class, () -> leaseReviews(marker, List.of(first, first)));
        assertThrows(IllegalArgumentException.class, () -> leaseReviews(marker, List.of(first, alias)));
        var mapper = ControlBuild.strictMapper();
        for (Object review : leaseReviews(marker, List.of(first))) {
            var changed = (com.fasterxml.jackson.databind.node.ObjectNode)mapper.valueToTree(review);
            ((com.fasterxml.jackson.databind.node.ArrayNode)changed.get("guarded_input_refs")).add(mapper.valueToTree(first));
            assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(changed), review.getClass()));
        }
    }

    private record SoftwareBroker(ControlBuild.FileRef receipt, Path proofRoot,
            com.fasterxml.jackson.databind.node.ObjectNode raw) { }
    private ControlBuild.FileRef brokerLeaf(Path root, String name, com.fasterxml.jackson.databind.JsonNode value) throws Exception {
        Path path = root.resolve(name);
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value), java.nio.file.StandardOpenOption.CREATE_NEW);
        return ControlBuild.FileRef.measure(path);
    }
    private SoftwareBroker softwareBroker(BuiltFixtureCodec fixture, boolean nullable, String tag,
            java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode> mutation) throws Exception {
        // Actual Java manifest producer and filesystem reader, with explicit software-only broker-shaped bytes.
        // No protected installation, SYSTEM token, WMI call, Add, or registration qualification is created.
        var mapper = ControlBuild.strictMapper(); Path root = temporary.resolve(tag); Files.createDirectory(root);
        Path proofRoot = root.resolve("broker-proof-software"); Files.createDirectory(proofRoot);
        String installation = "11111111-2222-4333-8444-555555555555", requestId = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
        String owner = "S-1-5-21-1-2-3-1001";
        var seal = mapper.createObjectNode().put("schema", "xar.project-exe-broker.runtime-seal.v1")
                .put("installation_id", installation).put("python_version", "3.14.7");
        seal.putArray("files").addObject().put("path", "runtime/python.exe").put("size", 0).put("sha256", "0".repeat(64));
        var sealPin = brokerLeaf(proofRoot, "installed-runtime-seal.json", seal);
        var policy = mapper.createObjectNode().put("broker_schema", "xar.project-exe-broker.policy.v1")
                .put("installation_id", installation).put("owner_sid", owner).put("runtime_manifest_sha256", sealPin.sha256());
        var policyPin = brokerLeaf(proofRoot, "installed-policy.json", policy);
        var installationPin = brokerLeaf(proofRoot, "installed-manifest.json",
                mapper.createObjectNode().put("schema", "SOFTWARE_ONLY_NO_INSTALLATION"));
        var taskPin = brokerLeaf(proofRoot, "task-readback.json",
                mapper.createObjectNode().put("schema", "SOFTWARE_ONLY_NO_TASK"));
        byte[] manifestBytes = Files.readAllBytes(Path.of(fixture.manifest().path()));
        Files.write(proofRoot.resolve("manifest.json"), manifestBytes, java.nio.file.StandardOpenOption.CREATE_NEW);
        var manifestPin = ControlBuild.FileRef.measure(proofRoot.resolve("manifest.json"));
        var request = mapper.createObjectNode().put("schema", "xar.project-exe-broker.request.v1").put("request_id", requestId)
                .put("installation_id", installation).put("expected_policy_sha256", policyPin.sha256())
                .put("producer_kind", "cmake-file-api-v2").put("manifest_b64", java.util.Base64.getEncoder().encodeToString(manifestBytes))
                .put("manifest_sha256", fixture.manifest().sha256());
        var requestPin = brokerLeaf(proofRoot, "request.json", request);
        var raw = nullable ? nullableAdministrativeReceipt(fixture.raw()) : fixture.raw().deepCopy();
        raw.put("broker_schema", nullable ? NativeBridgeDefender.BROKER_NULLABLE_SCHEMA : NativeBridgeDefender.BROKER_ARRAY_SCHEMA)
                .put("system_token_sid", "S-1-5-18").put("settings_readback_process_id", 4321)
                .put("settings_readback_token_user_sid", "S-1-5-18");
        raw.putObject("broker_identity").put("installation_id", installation).put("owner_sid", owner).put("request_id", requestId)
                .put("request_sha256", requestPin.sha256()).put("manifest_bytes_sha256", fixture.manifest().sha256())
                .put("policy_sha256", policyPin.sha256()).put("runtime_manifest_sha256", sealPin.sha256())
                .put("runtime_verified", true).put("protected_code", true).put("request_owner_sid", owner).put("actual_token_sid", "S-1-5-18");
        mutation.accept(raw);
        var receipt = brokerLeaf(root, "helper-receipt.json", raw);
        var workerPin = brokerLeaf(proofRoot, "protected-worker-receipt.json", raw);
        var proof = mapper.createObjectNode().put("status", "verified").put("copied_receipt_bytes_sha256", receipt.sha256());
        var pins = proof.putObject("pins");
        for (var pin : List.of(policyPin, sealPin, installationPin, taskPin, manifestPin, requestPin, workerPin))
            pins.putObject(Path.of(pin.path()).getFileName().toString()).put("path", pin.path()).put("size", pin.bytes()).put("sha256", pin.sha256());
        brokerLeaf(proofRoot, "proof.json", proof);
        return new SoftwareBroker(receipt, proofRoot, raw);
    }
    @Test void brokerVersion2UsesTheSharedNullableContractAndKeepsVersion1ArrayOnly() throws Exception {
        var declaration = declarationFixture();
        var fixture = builtFixtureCodec(declaration, "xar_ck3_bridge_injector", "broker-injector");
        for (boolean nullable : List.of(false, true)) {
            var broker = softwareBroker(fixture, nullable, "broker-version-" + nullable, value -> { });
            var readback = NativeBridgeDefender.readVerified(broker.receipt(), fixture.manifest(), fixture.executable());
            assertEquals(NativeBridgeDefender.ReadbackRoute.PROTECTED_SYSTEM_BROKER, readback.route());
            assertEquals(8, readback.supplementalEvidence().size());
            assertEquals(fixture.raw().path("after").get(1).textValue(), readback.after().get(1));
            if (nullable) {
                var proof = NativeProjectExeUac.qualifyProtectedBrokerSettings(broker.raw());
                assertInstanceOf(NativeProjectExeUac.NullableSettingsReadback.class, proof);
                assertEquals("S-1-5-18", proof.tokenUserSid()); assertEquals("4321", proof.processIdDecimal());
                assertNull(proof.before().exclusionExtension()); assertNull(proof.after().exclusionExtension());
                var mapper = ControlBuild.strictMapper(); byte[] encoded = mapper.writeValueAsBytes(proof);
                assertEquals(proof, mapper.readValue(encoded, NativeProjectExeUac.ThreeSettingsReadback.class));
                assertTrue(mapper.readTree(encoded).path("before").has("ExclusionExtension"));
                assertTrue(mapper.readTree(encoded).path("before").get("ExclusionExtension").isNull());
                assertThrows(IOException.class, () -> mapper.readValue(
                        new String(encoded, java.nio.charset.StandardCharsets.UTF_8) + " {}", NativeProjectExeUac.ThreeSettingsReadback.class));
                assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyThreeSettings(broker.raw(),
                        "S-1-5-21-1-2-3-1001", new WindowsJobProcess.ProcessIdentity(4321L, "1", temporary.resolve("ordinary-client.exe").toString())));
            }
        }
    }
    @Test void protectedBrokerNullableEvidenceRejectsMissingNullEmptyTypeAndIdentitySubstitution() throws Exception {
        var fixture = builtFixtureCodec(declarationFixture(), "xar_ck3_bridge_injector", "broker-negative-injector");
        int index = 0;
        for (String kind : List.of("v1-null", "missing-settings", "missing-property", "missing-setting", "null-path", "null-to-empty",
                "wrong-cim-type", "wrong-state", "wrong-scope", "pid-type", "pid-zero", "pid-overflow", "owner-as-worker",
                "missing-error", "latched-error", "incomplete", "owner", "identity-extra", "manifest")) {
            var broker = softwareBroker(fixture, true, "broker-negative-" + index++, raw -> {
                var before = (com.fasterxml.jackson.databind.node.ObjectNode)raw.get("before_settings");
                var after = (com.fasterxml.jackson.databind.node.ObjectNode)raw.get("after_settings");
                var identity = (com.fasterxml.jackson.databind.node.ObjectNode)raw.get("broker_identity");
                switch (kind) {
                    case "v1-null" -> raw.put("broker_schema", NativeBridgeDefender.BROKER_ARRAY_SCHEMA);
                    case "missing-settings" -> raw.remove("after_settings");
                    case "missing-property" -> raw.remove("before_property_observations");
                    case "missing-setting" -> after.remove("ExclusionExtension");
                    case "null-path" -> before.putNull("ExclusionPath");
                    case "null-to-empty" -> {
                        after.putArray("ExclusionExtension");
                        ((com.fasterxml.jackson.databind.node.ObjectNode)raw.path("after_property_observations").get(1)).put("value_state", "STRING_ARRAY");
                    }
                    case "wrong-cim-type" -> ((com.fasterxml.jackson.databind.node.ObjectNode)raw.path("before_property_observations").get(1)).put("cim_type", true);
                    case "wrong-state" -> ((com.fasterxml.jackson.databind.node.ObjectNode)raw.path("before_property_observations").get(1)).put("value_state", "STRING_ARRAY");
                    case "wrong-scope" -> raw.put("nullable_observation_scope", "empty means unconfigured");
                    case "pid-type" -> raw.put("settings_readback_process_id", "4321");
                    case "pid-zero" -> raw.put("settings_readback_process_id", 0);
                    case "pid-overflow" -> raw.put("settings_readback_process_id", 4294967296L);
                    case "owner-as-worker" -> raw.put("settings_readback_token_user_sid", "S-1-5-21-1-2-3-1001");
                    case "missing-error" -> raw.remove("settings_readback_error");
                    case "latched-error" -> raw.put("settings_readback_error", "earlier WMI error");
                    case "incomplete" -> raw.put("settings_readback_complete", false);
                    case "owner" -> identity.put("request_owner_sid", "S-1-5-21-1-2-3-1002");
                    case "identity-extra" -> identity.put("ordinary_client_is_SYSTEM", true);
                    case "manifest" -> raw.put("manifest_sha256", "0".repeat(64));
                    default -> throw new AssertionError(kind);
                }
            });
            assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(
                    broker.receipt(), fixture.manifest(), fixture.executable()), kind);
        }
    }
    @Test void finiteFixtureBrokerReaderSharesOriginalProofAndKeepsDirectUacAndInjectorScopesSeparate() throws Exception {
        var declaration = declarationFixture(); int index = 0;
        for (var target : NativeFixtureBuild.FixtureTarget.values()) {
            String tag = "broker-fixture-" + index++;
            var fixture = builtFixtureCodec(declaration, target.targetName(), tag);
            var broker = softwareBroker(fixture, true, tag + "-readback", raw -> { });
            assertEquals(NativeBridgeDefender.ReadbackRoute.PROTECTED_SYSTEM_BROKER,
                    NativeBridgeDefender.readBuiltFixtureVerified(broker.receipt(), fixture.manifest(), fixture.executable(), target).route());
            assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(broker.receipt(), fixture.manifest(), fixture.executable()));
            assertThrows(IOException.class, () -> NativeBridgeDefender.requireDirectBuiltFixtureReceipt(
                    broker.receipt(), fixture.manifest(), fixture.executable(), target.targetName()));
            var client = new NativeProjectExeUac.ProcessIdentity("1234", "1", temporary.resolve("ordinary-client.exe").toString());
            var direct = new NativeProjectExeUac.TerminalProof(true, client, true, true, false, "0");
            assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyBuiltFixtureCompletion(direct, client.executable(),
                    "S-1-5-21-1-2-3-1001", fixture.executable(), target.targetName(), fixture.manifest(), broker.receipt()));
            Path retained = temporary.resolve(tag + "-retained.exe"); Files.copy(Path.of(fixture.executable().path()), retained);
            var retainedRef = ControlBuild.FileRef.measure(retained); Files.delete(Path.of(fixture.executable().path()));
            assertThrows(IOException.class, () -> NativeBridgeDefender.readBuiltFixtureVerified(
                    broker.receipt(), fixture.manifest(), fixture.executable(), target));
            assertEquals(NativeBridgeDefender.ReadbackRoute.PROTECTED_SYSTEM_BROKER,
                    NativeBridgeDefender.readBuiltFixtureVerified(broker.receipt(), fixture.manifest(), fixture.executable(), target, retainedRef).route());
        }
    }
    @Test void brokerProofRetainsAllEightLeavesAndRejectsChangedCopiedPolicySealManifestOrRequest() throws Exception {
        var fixture = builtFixtureCodec(declarationFixture(), "xar_ck3_bridge_injector", "broker-proof-injector");
        int index = 0;
        for (String name : List.of("installed-policy.json", "installed-runtime-seal.json", "installed-manifest.json",
                "task-readback.json", "manifest.json", "request.json", "protected-worker-receipt.json", "proof.json")) {
            var broker = softwareBroker(fixture, true, "broker-proof-tamper-" + index++, raw -> { });
            assertEquals(8, NativeBridgeDefender.readVerified(broker.receipt(), fixture.manifest(), fixture.executable()).supplementalEvidence().size());
            Path leaf = broker.proofRoot().resolve(name); byte[] original = Files.readAllBytes(leaf);
            if (name.equals("proof.json")) Files.delete(leaf);
            else Files.writeString(leaf, "{}");
            assertThrows(IOException.class, () -> NativeBridgeDefender.readVerified(
                    broker.receipt(), fixture.manifest(), fixture.executable()), name);
            Files.write(leaf, original);
            assertEquals(8, NativeBridgeDefender.readVerified(broker.receipt(), fixture.manifest(), fixture.executable()).supplementalEvidence().size());
        }
    }

    @Test void originalWorkerRegisterClaimBytesReachTheSharedJavaNullableSettingsCodec() throws Exception {
        // Actual candidate register_claim/DefenderWmi producer output with software services/Add.
        // No process_request identity, protected installation, SYSTEM token, or actual WMI is claimed.
        var mapper = ControlBuild.strictMapper();
        var raw = mapper.readTree(originalCorpus("broker-nullable-worker-producer-resume63.json",
                "3a5d7bbd6908ada6dd78b76e2b6e40cc89a3969ddfa45e7c567586f80d456bea"));
        assertFalse(raw.has("broker_identity"));
        assertEquals("xar.project-exe-broker.receipt.v2", raw.path("broker_schema").textValue());
        assertEquals(1, raw.path("calls").size()); assertTrue(raw.path("calls").get(0).path("return_value").isNull());
        var proof = NativeProjectExeUac.qualifyProtectedBrokerSettings(raw);
        assertInstanceOf(NativeProjectExeUac.NullableSettingsReadback.class, proof);
        assertEquals("95756", proof.processIdDecimal()); assertEquals("S-1-5-18", proof.tokenUserSid());
        assertNull(proof.before().exclusionExtension()); assertNull(proof.after().exclusionExtension());
        assertEquals(List.of(), proof.before().exclusionProcess()); assertEquals(List.of(), proof.after().exclusionProcess());
        assertEquals(proof, mapper.readValue(mapper.writeValueAsBytes(proof), NativeProjectExeUac.ThreeSettingsReadback.class));
        var missing = ((com.fasterxml.jackson.databind.node.ObjectNode)raw).deepCopy(); missing.remove("settings_readback_error");
        assertThrows(IOException.class, () -> NativeProjectExeUac.qualifyProtectedBrokerSettings(missing));
    }

}
