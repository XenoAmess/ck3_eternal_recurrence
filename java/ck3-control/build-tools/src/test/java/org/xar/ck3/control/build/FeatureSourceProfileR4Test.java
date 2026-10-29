package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.CompleteSourceGraph.Profile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class FeatureSourceProfileR4Test {
    @TempDir Path temporary;

    @Test void actualFullAccountingPersistsAsTypedCompilerEvidenceAndKeepsItsTemporaryRoot() throws Exception {
        Path work = Files.createDirectory(temporary.resolve("accounting-work"));
        Path source = Files.createDirectory(temporary.resolve("accounting-source"));
        for (String part : List.of("m2", "build", "tools", "scratch", "artifacts", "logs"))
            Files.createDirectory(work.resolve(part));
        Files.writeString(work.resolve("m2/retained.bin"), "abc");
        Files.writeString(work.resolve("build/compiled.bin"), "defgh");
        Path policy = temporary.resolve("accounting-policy.json");
        Files.writeString(policy, "{\"schema\":\"xar-storage-retention-policy-v1\"}");
        var mapper = ControlBuild.strictMapper(); var release = mapper.createObjectNode();
        String machine = WindowsJobProcess.currentMachineId(); Instant now = Instant.now();
        release.put("schema", "xar.java-phase1.manual-capacity-release/v1");
        release.put("status", "RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE");
        release.put("machine_id", machine); release.put("single_Maven_writer", "/root");
        release.put("review_at_utc", now.plusSeconds(600).toString());
        release.putArray("approved_output_roots").add(work.toString()).add(source.toString());
        release.put("Maven_repository", work.resolve("m2").toString());
        release.put("build_root", work.resolve("build").toString());
        release.put("temporary_root", work.resolve("scratch").toString());
        var parts = release.putObject("parts");
        for (String part : List.of("m2", "build", "tools", "scratch", "artifacts")) parts.put(part, 1L << 20);
        parts.put("metadata_logs", 1L << 20);
        release.set("policy_ref", mapper.valueToTree(FileRef.measure(policy)));
        var store = Files.getFileStore(work);
        var volume = release.putObject("volumes").putObject(work.getRoot().toString());
        volume.put("required_free", (1L << 20) + 3); volume.put("this_write_peak", 1L << 20);
        volume.put("other_unspent_reservations", 1); volume.put("system_growth_reserve", 1); volume.put("safety_reserve", 1);
        volume.put("current_project_usage_conservative_upper", store.getTotalSpace() - store.getUsableSpace());
        volume.put("effective_project_quota", store.getTotalSpace());
        release.put("test_RAM_joint_hard_bytes", 256L << 20); release.put("Maven_heap_bytes", 96L << 20);
        Path releasePath = temporary.resolve("accounting-release.json");
        Files.write(releasePath, mapper.writeValueAsBytes(release), StandardOpenOption.CREATE_NEW);
        var config = new ControlBuild.Config(source, work, releasePath, "compiler-accounting", "/root", null,
                temporary, "3.10.0", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        var overlapping = new ControlBuild.Config(work, work, releasePath, "compiler-accounting", "/root", null,
                temporary, "3.10.0", 60, ControlBuild.TargetKind.SERVICE_FAST_JAR,
                ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(overlapping, () -> {}));
        ControlBuild.WorkpackageAccounting accounting;
        try (var held = ControlBuild.prepareWorkpackageTemporaryRoot(config, () -> {})) {
            accounting = Full35CompileOnly.compilerAccounting(config, held, () -> {});
            assertEquals(work.resolve("scratch"), held.root());
            assertEquals(held.root(), Full35CompileOnly.accountingTemporary(accounting));
            held.requireCurrent();
        }
        assertEquals(ControlBuild.AccountingMode.FULL_PART_INVENTORY, accounting.mode());
        assertEquals(3L, accounting.logicalBytesByScope().get("m2").longValue());
        assertEquals(5L, accounting.logicalBytesByScope().get("build").longValue());
        assertEquals(3L, accounting.mavenRepositoryBaselineBytes().longValue());
        assertEquals(3L, accounting.mavenRepositoryCurrentBytes().longValue());
        assertEquals(0L, accounting.peakNewLogicalBytes());
        assertEquals(work.resolve("scratch"), Full35CompileOnly.accountingTemporary(accounting));
        assertThrows(IOException.class, () -> Full35CompileOnly.accountingTemporary(null));
        var ref = accounting.capacityReleaseRef();
        var actual = new Full35CompileOnly.Actual(Full35CompileOnly.RECEIPT_SCHEMA, machine, now.toString(),
                Full35CompileOnly.Scope.COMPILER_DIAGNOSTIC_ONLY_NOT_FULL35_SDK_HOST_OR_GAME_QUALIFICATION,
                Full35CompileOnly.State.COMPILE_RED, Full35CompileOnly.Tests.NOT_TESTED,
                ref, ref, ref, ref, ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4, 35, List.of(),
                work.toString(), work.resolve("snapshot").toString(), work.resolve("build").toString(),
                null, null, List.of(), List.of(), List.of(), null, null, null, null, List.of(), List.of(), null,
                accounting, "Software accounting/serde fixture; no Maven compiler was invoked");
        byte[] bytes = mapper.writeValueAsBytes(actual);
        assertEquals(actual, mapper.readValue(bytes, Full35CompileOnly.Actual.class));
        var tree = mapper.readTree(bytes);
        assertFalse(tree.has("final_logical_bytes_by_part"));
        assertEquals(mapper.readTree(mapper.writeValueAsBytes(accounting)), tree.get("final_workpackage_accounting"));
        ((com.fasterxml.jackson.databind.node.ObjectNode) tree.get("final_workpackage_accounting")).put("mode", "UNKNOWN_MODE");
        assertThrows(IOException.class, () -> mapper.treeToValue(tree, Full35CompileOnly.Actual.class));
        ref.verify();
    }

    @Test void missingAttemptTmpIsCreatedBeforeTheActualCompilerGuardAndStaysHeldThroughFailure() throws Exception {
        var shared = new ControlBuildAccountingTest();
        shared.temporary = Files.createDirectory(temporary.resolve("shared-attempt-fixture"));
        var fixture = shared.fixture("compiler-tmp-entry");
        var config = fixture.config();
        Path root = config.workRoot().resolve("scratch/" + config.attempt() + "-tmp");
        Files.delete(root);
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(config, () -> {}));
        assertFalse(Files.exists(root), "The public accounting reader must remain read-only");
        assertTrue(Files.isDirectory(fixture.snapshot()));
        assertTrue(Files.isDirectory(fixture.build()));
        ControlBuild.PreparedTemporaryRoot original;
        IOException injected = new IOException("original compiler guard rejection before any Maven child");
        IOException actual = assertThrows(IOException.class, () -> {
            try (var held = ControlBuild.prepareWorkpackageTemporaryRoot(config, () -> {})) {
                var accounting = Full35CompileOnly.compilerAccounting(config, held, () -> {});
                assertEquals(root, Full35CompileOnly.accountingTemporary(accounting));
                assertThrows(IOException.class, () -> Files.move(root, root.resolveSibling("escaped-tmp")));
                held.requireCurrent();
                Full35CompileOnly.compilerAccounting(config, held, () -> { throw injected; });
            }
        });
        assertSame(injected, actual);
        assertTrue(Files.isDirectory(root));
        assertFalse(Files.exists(config.workRoot().resolve("logs/build-" + config.attempt() + "-version.cmd")));
        assertFalse(Files.exists(config.workRoot().resolve("logs/build-" + config.attempt() + "-test-compile.cmd")));
        assertThrows(IOException.class, () -> ControlBuild.prepareWorkpackageTemporaryRoot(config, () -> {}),
                "A failed attempt is not silently adopted or recreated");

        var next = shared.fixture("compiler-token-closed");
        Path nextRoot = next.config().workRoot().resolve("scratch/" + next.config().attempt() + "-tmp");
        Files.delete(nextRoot);
        try (var held = ControlBuild.prepareWorkpackageTemporaryRoot(next.config(), () -> {})) { original = held; }
        assertThrows(IOException.class, () -> Full35CompileOnly.compilerAccounting(next.config(), original, () -> {}));
        assertThrows(IOException.class, original::requireCurrent);
    }

    @Test void versionedAdapterMustJoinTheActualWholeOwnAndCompleteRuntimeMetadata() throws Exception {
        var mapper=ControlBuild.strictMapper();String machine="fixture-machine-123";
        FileRef whole=new FileRef(temporary.resolve("whole.json").toString(),1,"0".repeat(64));
        FileRef ownRef=new FileRef(temporary.resolve("own.json").toString(),1,"1".repeat(64));
        var runtime=new java.util.ArrayList<FileRef>();
        for(int index=0;index<6;index++) runtime.add(new FileRef(temporary.resolve("runtime-"+index).toString(),1,"2".repeat(64)));
        var qualification=new Full35CompileOnly.AdapterQualification(
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.qualified-adapter/v1","DECLARED_METADATA_ONLY"),whole,ownRef,
                new Full35CompileOnly.OwnReadbackExpectation("fixture.own-readback/v1","INTEGRATED_TOOLS_RUNTIME_ONLY"));
        var legacy=new Full35CompileOnly.Request(Full35CompileOnly.REQUEST_SCHEMA,machine,"/root",whole,ownRef,runtime,
                temporary.resolve("source").toString(),temporary.resolve("work").toString(),whole,"feature17",temporary.toString(),900);
        var versioned=new Full35CompileOnly.QualifiedRequest(Full35CompileOnly.QUALIFIED_REQUEST_SCHEMA,legacy,qualification);
        assertEquals(legacy,mapper.readValue(mapper.writeValueAsBytes(legacy),Full35CompileOnly.Request.class));
        assertEquals(versioned,mapper.readValue(mapper.writeValueAsBytes(versioned),Full35CompileOnly.QualifiedRequest.class));
        var delivery=mapper.createObjectNode();delivery.put("schema","fixture.qualified-adapter/v1");
        delivery.put("status","DECLARED_METADATA_ONLY");delivery.put("machine_id",machine);
        delivery.set("qualified_whole_build_receipt_ref",mapper.valueToTree(whole));
        delivery.set("qualified_own_archive_actual_ref",mapper.valueToTree(ownRef));delivery.set("complete_runtime",mapper.valueToTree(runtime));
        var own=mapper.createObjectNode();own.put("schema","fixture.own-readback/v1");own.put("scope","INTEGRATED_TOOLS_RUNTIME_ONLY");
        own.put("machine_id",machine);own.set("build_receipt_ref",mapper.valueToTree(whole));own.set("complete_running_runtime",mapper.valueToTree(runtime));
        // Metadata joins grant no qualification. Production must additionally verify the real completed build receipt.
        Full35CompileOnly.requireAdapterMetadata(delivery,own,qualification,machine,runtime);
        own.set("build_receipt_ref",mapper.valueToTree(ownRef));
        assertThrows(IOException.class,()->Full35CompileOnly.requireAdapterMetadata(delivery,own,qualification,machine,runtime));
        own.set("build_receipt_ref",mapper.valueToTree(whole));delivery.put("status","WRONG_STATUS");
        assertThrows(IOException.class,()->Full35CompileOnly.requireAdapterMetadata(delivery,own,qualification,machine,runtime));
        delivery.put("status","DECLARED_METADATA_ONLY");own.set("complete_running_runtime",mapper.valueToTree(runtime.subList(0,5)));
        assertThrows(IOException.class,()->Full35CompileOnly.requireAdapterMetadata(delivery,own,qualification,machine,runtime));
    }

    @Test void actualAssemblyPlanFinalTreeSdkIndexAndCompilerKeepOneR4Profile() throws Exception {
        var fixture = SourceRelocationTestSupport.fixture(temporary, Profile.G2_FULL_PARITY_20261024_R4, 4100);
        FileRef input = SourceRelocationTestSupport.json(temporary.resolve("input.json"), fixture.input());
        Path request = temporary.resolve("request.json"), audit = temporary.resolve("audit.json");
        Path output = temporary.resolve("plan.json");
        Source08Assembly.main(new String[] {input.path(), request.toString(), audit.toString()});
        SourceGraphPlanProducer.main(new String[] {request.toString(), output.toString()});
        FileRef planRef = FileRef.measure(output);
        var plan = CompleteSourceGraph.readPlan(planRef);
        var selected = CompleteSourceGraph.resolve(plan);
        assertTrue(selected.files().size() > 4096);
        assertEquals(Profile.G2_FULL_PARITY_20261024_R4, plan.profile());
        assertEquals(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4,
                Full35CompileOnly.sourceProfile(plan));
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3));
        Path copied = temporary.resolve("final-tree");
        var actualPins = SourceRelocationTestSupport.copyFinal(plan, copied);
        assertEquals(actualPins, CompleteSourceGraph.verifyMaterialized(plan, copied).sourcePins());
        for (var move : plan.relocations()) assertFalse(Files.exists(copied.resolve(move.oldTargetRelative())));
        var index = SourceGraphSdkIndexProducer.produce(input, planRef,
                Clock.fixed(Instant.parse("2026-10-24T00:00:00Z"), ZoneOffset.UTC));
        assertEquals(selected.files().stream().filter(row -> row.targetRelative().endsWith(".java")).count(),
                (long) index.selectedFiles().size());
        for (var move : plan.relocations())
            assertTrue(index.selectedFiles().stream().noneMatch(row -> row.targetRelative().equals(move.oldTargetRelative())));
        input.verify(); planRef.verify(); fixture.baseline().inventoryRef().verify();
    }

    @Test void actualSourceInventoryGivesOnlyApplicationAndLocalSrcTwelveMiB() throws Exception {
        var fixture = SourceRelocationTestSupport.fixture(temporary, Profile.G2_FULL_PARITY_20261024_R4, 0);
        for (String module : List.of("application", "local-service")) {
            Path file = sized(fixture.root().resolve(module + "/src/main/resources/profile.bin"), 9L << 20);
            assertTrue(ControlBuild.sourceManifest(fixture.root(),
                    ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4).contains(FileRef.measure(file)));
            assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                    ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R3));
            Files.delete(file);
        }
        Path other = sized(fixture.root().resolve("g2-research/src/main/resources/profile.bin"), 9L << 20);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4));
        Files.delete(other);
        Path metadata = sized(fixture.root().resolve("application/.mvn/profile.bin"), 9L << 20);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4));
        Files.delete(metadata);
        sized(fixture.root().resolve("application/src/main/resources/too-large.bin"), (12L << 20) + 1);
        assertThrows(IOException.class, () -> ControlBuild.sourceManifest(fixture.root(),
                ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R4));
    }

    @Test void compilerFollowsActualR2OrR4PlanAndRejectsUnsupportedGraphProfiles() throws Exception {
        var r2 = SourceRelocationTestSupport.fixture(Files.createDirectory(temporary.resolve("r2")),
                Profile.G2_FULL_PARITY_20261024_R2, 0);
        assertEquals(ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261024_R2,
                Full35CompileOnly.sourceProfile(SourceRelocationTestSupport.produce(r2)));
        var r3 = SourceRelocationTestSupport.fixture(Files.createDirectory(temporary.resolve("r3")),
                Profile.G2_FULL_PARITY_20261024_R3, 0);
        var unsupported = SourceRelocationTestSupport.produce(r3);
        assertThrows(IOException.class, () -> Full35CompileOnly.sourceProfile(unsupported));
        assertThrows(IOException.class, () -> Full35CompileOnly.sourceProfile(null));
        assertEquals(4096, Profile.G2_FULL_PARITY_20261024_R2.maxFiles());
        assertEquals(4096, Profile.G2_FULL_PARITY_20261024_R3.maxFiles());
    }

    @Test void materializerAndAuditRetainFiniteNativeAndLogicalR4Extents() throws Exception {
        Profile profile = Profile.G2_FULL_PARITY_20261024_R4;
        // The real candidate's rounded-file estimate tests admission; this is not a native-copy receipt.
        var estimate = new CompleteSourceGraphMaterializer.NativeSize(4530, 1593, 61365318,
                70901760, 6524928, 77426688);
        CompleteSourceGraphMaterializer.requireSize(estimate, profile);
        CompleteSourceGraphMaterializer.requireProfileBudget(profile, 80L << 20);
        assertThrows(IOException.class, () -> CompleteSourceGraphMaterializer.requireProfileBudget(profile, 79L << 20));
        assertThrows(IllegalArgumentException.class, () -> CompleteSourceGraphMaterializer.requireSize(
                new CompleteSourceGraphMaterializer.NativeSize(5121, 1, 1, 4096, 4096, 8192), profile));
        assertThrows(IllegalArgumentException.class, () -> CompleteSourceGraphMaterializer.requireSize(
                new CompleteSourceGraphMaterializer.NativeSize(1, 1, (64L << 20) + 1, 4096, 4096, 8192), profile));
        assertThrows(IllegalArgumentException.class, () -> CompleteSourceGraphMaterializer.requireSize(
                new CompleteSourceGraphMaterializer.NativeSize(1, 1, 1, 80L << 20, 4096, (80L << 20) + 4096), profile));
    }

    private static Path sized(Path path, long bytes) throws IOException {
        Files.createDirectories(path.getParent());
        try (var channel = Files.newByteChannel(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            channel.position(bytes - 1); channel.write(ByteBuffer.wrap(new byte[] {0}));
        }
        return path;
    }

    @Test void standaloneAdapterQualificationRequiresStrictPinnedContract() throws Exception {
        var mapper = ControlBuild.strictMapper();
        FileRef whole = adapterTestJson(temporary.resolve("adapter-whole.json"), mapper.createObjectNode());
        FileRef own = adapterTestJson(temporary.resolve("adapter-own.json"), mapper.createObjectNode());
        var expected = new Full35CompileOnly.AdapterQualification(
                new SharedOwnedCommandBinding.AuthorityExpectation("fixture.adapter/v1", "DECLARED_METADATA_ONLY"),
                whole, own, new Full35CompileOnly.OwnReadbackExpectation("fixture.own/v1", "INTEGRATED_TOOLS_RUNTIME_ONLY"));
        FileRef qualification = adapterTestJson(temporary.resolve("adapter-qualification.json"), expected);
        assertEquals(expected, Full35CompileOnly.readAdapterQualification(qualification));
        assertThrows(IOException.class, () -> Full35CompileOnly.main(new String[] {"--qualify-adapter"}));
        int badIndex = 0;
        for (var bad : List.of(mapper.getNodeFactory().booleanNode(true), mapper.getNodeFactory().numberNode(1.0),
                mapper.getNodeFactory().textNode("1"), mapper.getNodeFactory().nullNode())) {
            var wire = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(expected));
            assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                    wire.required("whole_build_receipt_ref")).set("bytes", bad);
            FileRef altered = adapterTestJson(temporary.resolve("adapter-bad-" + badIndex++ + ".json"), wire);
            assertThrows(IOException.class, () -> Full35CompileOnly.readAdapterQualification(altered));
        }
        for (String mutation : List.of("missing", "null", "unknown")) {
            var wire = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, mapper.valueToTree(expected));
            if (mutation.equals("missing")) wire.remove("own_readback_expectation");
            else if (mutation.equals("null")) wire.putNull("own_readback_expectation");
            else wire.put("unqualified_fallback", true);
            FileRef altered = adapterTestJson(temporary.resolve("adapter-" + mutation + ".json"), wire);
            assertThrows(IOException.class, () -> Full35CompileOnly.readAdapterQualification(altered));
        }
        FileRef nullQualification = adapterTestJson(temporary.resolve("adapter-null-root.json"), mapper.getNodeFactory().nullNode());
        assertThrows(IOException.class, () -> Full35CompileOnly.readAdapterQualification(nullQualification));
        Files.writeString(Path.of(qualification.path()), "{}", StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IOException.class, () -> Full35CompileOnly.readAdapterQualification(qualification));
    }

    private static FileRef adapterTestJson(Path path, Object value) throws IOException {
        Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(value), StandardOpenOption.CREATE_NEW);
        return FileRef.measure(path);
    }
}
