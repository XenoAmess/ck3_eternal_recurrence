package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Pure metadata producer/consumer contracts. Synthetic references grant no real build, lease, native or HTTP qualification. */
final class ProjectionArtifactOwnerV3Test {
    @TempDir Path temporary;
    private static final String MACHINE = "synthetic-owner-v3";
    private static final Instant ISSUED = Instant.parse("2026-10-22T00:00:00Z"), EXPIRES = ISSUED.plusSeconds(300);

    @Test void singleScopeProducerAndConsumerKeepExactSixteenFieldsAndNoEightOrSixtyFourMiBSemanticCap() throws Exception {
        Scope produced = scope(); byte[] raw = encodeScope(produced);
        assertEquals(16, ControlBuild.strictMapper().readTree(raw).size()); assertEquals(produced, decodeScope(raw));
        assertTrue(produced.maxInputBytes() > 64L << 20); assertEquals("18446744073709551615", decodeScope(raw).ownerProcess().creationFiletime());
    }
    @Test void scopeConsumerRejectsMissingExtraBooleanFloatNullAndUnsafeIntegerFields() throws Exception {
        for (String field : List.of("scope_id", "owner_session_id", "machine_id", "owner_process", "source_snapshot_ref", "runtime_binding_ref")) {
            ObjectNode row = ProjectionArtifactAuthority.scope(scope()); row.remove(field); assertThrows(IllegalArgumentException.class, () -> decodeScope(bytes(row)));
        }
        ObjectNode alias = ProjectionArtifactAuthority.scope(scope()); alias.put("event_role", "read-any-file"); assertThrows(IllegalArgumentException.class, () -> decodeScope(bytes(alias)));
        for (String token : List.of("true", "1.0", "null", "\"1\"", "9007199254740992")) {
            String raw = new String(encodeScope(scope()), java.nio.charset.StandardCharsets.UTF_8);
            raw = raw.replace("\"max_input_bytes\":100000000", "\"max_input_bytes\":" + token); String rejected = raw;
            assertThrows(IllegalArgumentException.class, () -> decodeScope(rejected.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        }
        ObjectNode badPid = ProjectionArtifactAuthority.scope(scope()); ((ObjectNode) badPid.get("owner_process")).put("pid", true);
        assertThrows(IllegalArgumentException.class, () -> decodeScope(bytes(badPid)));
        ObjectNode badBirth = ProjectionArtifactAuthority.scope(scope()); ((ObjectNode) badBirth.get("owner_process")).put("creation_filetime", 1L);
        assertThrows(IllegalArgumentException.class, () -> decodeScope(bytes(badBirth)));
    }
    @Test void leaseProducerRoundtripHasSixFieldsAndRejectsAnotherPurposeOrScopeField() throws Exception {
        Lease produced = new Lease(ref("scope.json"), process(), ISSUED, EXPIRES, Purpose.FULL); byte[] raw = encodeLease(produced);
        assertEquals(6, ControlBuild.strictMapper().readTree(raw).size()); assertEquals(produced, decodeLease(raw));
        ObjectNode row = (ObjectNode) ControlBuild.strictMapper().readTree(raw); row.put("purpose", "capture");
        assertThrows(IllegalArgumentException.class, () -> decodeLease(bytes(row)));
        row.put("purpose", "full"); row.put("scope_id", "alias"); assertThrows(IllegalArgumentException.class, () -> decodeLease(bytes(row)));
    }
    @Test void contextDistinguishesExplicitNullMissingAndTheCompleteCurrentActiveBinding() throws Exception {
        Context empty = new Context(MACHINE, ISSUED, Optional.empty()); byte[] raw = encodeContext(empty);
        assertEquals(4, ControlBuild.strictMapper().readTree(raw).size()); assertEquals(empty, decodeContext(raw));
        ObjectNode missing = context(empty); missing.remove("artifact_inputs"); assertThrows(IllegalArgumentException.class, () -> decodeContext(bytes(missing)));
        Context active = new Context(MACHINE, ISSUED, Optional.of(new Active(ref("scope.json"), ref("lease.json"), scope(), process())));
        assertEquals(active, decodeContext(encodeContext(active)));
        ObjectNode drift = context(active); ((ObjectNode) drift.get("artifact_inputs").get("scope")).put("machine_id", "other-machine");
        assertThrows(IllegalArgumentException.class, () -> decodeContext(bytes(drift)));
    }
    @Test void sourceAndRuntimeWitnessesRequireOrderedCompleteAcceptedClosuresAndFixedOwnerIdentity() throws Exception {
        ControlBuild.BuildReceipt accepted = build(); Scope fixed = scope();
        SourceBinding source = new SourceBinding(MACHINE, fixed.buildReceiptRef(), accepted.sourcePins(), accepted.compiledSourcePins());
        RuntimeBinding runtime = new RuntimeBinding(MACHINE, fixed.buildReceiptRef(), fixed.ownerSessionId(), fixed.ownerProcess(), ownerSources(accepted), accepted.producerRuntimePins());
        assertEquals(source, decodeSourceBinding(encodeSourceBinding(source))); assertEquals(runtime, decodeRuntimeBinding(encodeRuntimeBinding(runtime)));
        requireBindings(fixed, accepted, source, runtime);
        List<ControlBuild.FileRef> reversed = new ArrayList<>(accepted.sourcePins()); Collections.reverse(reversed);
        assertThrows(IOException.class, () -> requireBindings(fixed, accepted, new SourceBinding(MACHINE, fixed.buildReceiptRef(), reversed, accepted.compiledSourcePins()), runtime));
        assertThrows(IOException.class, () -> requireBindings(fixed, accepted, source,
                new RuntimeBinding(MACHINE, fixed.buildReceiptRef(), "other-owner-session", fixed.ownerProcess(), runtime.ownerSourceRefs(), runtime.ownerRuntimeRefs())));
        assertThrows(IOException.class, () -> requireBindings(fixed, accepted, source,
                new RuntimeBinding(MACHINE, fixed.buildReceiptRef(), fixed.ownerSessionId(), fixed.ownerProcess(), runtime.ownerSourceRefs(), List.of(ref("unrelated-owner.jar")))));
    }
    @Test void sourceSubsetUsesTheExactQualifiedModulePathAndCannotAcceptANameContainedElsewhere() throws Exception {
        ControlBuild.BuildReceipt original = build(); List<ControlBuild.FileRef> changed = new ArrayList<>(original.sourcePins());
        changed.set(0, ref("source/another/build-tools/src/main/java/org/xar/ck3/control/build/ProjectionArtifactAuthority.java"));
        assertThrows(IOException.class, () -> ownerSources(build(changed, original.compiledSourcePins())));
        ObjectNode binding = (ObjectNode) ControlBuild.strictMapper().readTree(encodeSourceBinding(new SourceBinding(MACHINE, ref("build.json"), original.sourcePins(), original.compiledSourcePins())));
        binding.putNull("compiled_source_refs"); assertThrows(IllegalArgumentException.class, () -> decodeSourceBinding(bytes(binding)));
    }
    @Test void v2StaysExactSixteenAndV3UsesIndependentStrictSeventeenWithSharedTypedObservation() throws Exception {
        var v2 = v2(); var mapper = ControlBuild.strictMapper(); byte[] raw2 = mapper.writeValueAsBytes(v2);
        assertEquals(16, mapper.readTree(raw2).size()); assertEquals(v2, MapAdmissionServiceOwner.readProjectionProgram(raw2));
        var v3 = v3(); byte[] raw3 = mapper.writeValueAsBytes(v3);
        assertEquals(17, mapper.readTree(raw3).size()); assertEquals(v3, MapAdmissionServiceOwner.readProjectionProgram(raw3));
        assertInstanceOf(MapAdmissionServiceOwner.ProjectionProgramManifestV3.class, MapAdmissionServiceOwner.readProjectionProgram(raw3));
        ObjectNode extra = (ObjectNode) mapper.readTree(raw2); extra.putNull("artifact_inputs");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readProjectionProgram(bytes(extra)));
        ObjectNode absent = (ObjectNode) mapper.readTree(raw3); absent.remove("artifact_inputs");
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readProjectionProgram(bytes(absent)));
        ObjectNode unknown = (ObjectNode) mapper.readTree(raw3); unknown.put("permission_alias", true);
        assertThrows(IOException.class, () -> MapAdmissionServiceOwner.readProjectionProgram(bytes(unknown)));
    }
    @Test void v3RejectsCaptureQualificationAndAProofFromAnotherBuildBeforePublication() throws Exception {
        var good = v3();
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.ProjectionProgramManifestV3(good.schema(), good.machineId(), good.observedAtUtc(),
                good.deploymentRoot(), good.files(), good.sourceRefs(), good.buildReceiptRef(), good.javaExecutableRef(), true, true, good.projection(), good.hostContext(),
                null, null, ProjectionCaptureScope.Qualification.TEST_COMPILED_CAPTURE_ONLY, null, good.artifactInputs()));
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.ProjectionProgramManifestV3(good.schema(), good.machineId(), good.observedAtUtc(),
                good.deploymentRoot(), good.files(), good.sourceRefs(), ref("other-build.json"), good.javaExecutableRef(), true, true, good.projection(), good.hostContext(),
                null, null, ProjectionCaptureScope.Qualification.FULL_SOFTWARE, null, good.artifactInputs()));
    }
    @Test void rootGrantRejectsCoercionAndJobExpansionAndDoesNotBorrowEventConfiguration() throws Exception {
        var grant = new ProjectionArtifactInputOwner.RootGrant(ProjectionArtifactInputOwner.GRANT_SCHEMA, MACHINE, "owner-v3", ISSUED.toString(), EXPIRES.toString(),
                temporary.resolve("slot").toString(), temporary.resolve("scope.json").toString(), temporary.resolve("lease.json").toString(),
                temporary.resolve("source.json").toString(), temporary.resolve("runtime.json").toString(), 100_000_000, ProjectionArtifactInputOwner.JOB_MEMORY_BYTES,
                ref("military.jar"), ref("policy.json"), ref("input-capacity.json"));
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(grant); assertEquals(grant, ControlBuild.strictMapper().readValue(raw, ProjectionArtifactInputOwner.RootGrant.class));
        ObjectNode wrong = (ObjectNode) ControlBuild.strictMapper().readTree(raw); wrong.put("max_input_bytes", true);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(bytes(wrong), ProjectionArtifactInputOwner.RootGrant.class));
        ObjectNode widened = (ObjectNode) ControlBuild.strictMapper().readTree(raw); widened.put("job_memory_limit_bytes", 1L << 30);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(bytes(widened), ProjectionArtifactInputOwner.RootGrant.class));
    }
    @Test void nonProjectionAndCaptureEntrypointsRejectBusinessScopeBeforeReadingAnyFiles() {
        var config = new MapAdmissionServiceOwner.Config(temporary.resolve("missing-build.json"), temporary.resolve("work"), temporary.resolve("java.exe"),
                Instant.now().plusSeconds(60), 8089, null, null, null, null,
                new ProjectionArtifactInputOwner.Config(ref("missing-grant.json"), "scope", "owner-session"));
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionServiceOwner.start(config));
        assertThrows(IllegalArgumentException.class, () -> MapAdmissionServiceOwner.startForCapture(config, temporary.resolve("missing-capture.json")));
    }
    @Test void rootInputReservationUsesTheExistingPolicyCalculatorAndRejectsWrongPartOrVolumeEquation() throws Exception {
        Instant now = Instant.now(), review = now.plusSeconds(300);
        var grant = new ProjectionArtifactInputOwner.RootGrant(ProjectionArtifactInputOwner.GRANT_SCHEMA, MACHINE, "owner-v3", now.toString(), review.toString(),
                temporary.resolve("slot").toString(), temporary.resolve("scope.json").toString(), temporary.resolve("lease.json").toString(),
                temporary.resolve("source.json").toString(), temporary.resolve("runtime.json").toString(), 100_000_000, ProjectionArtifactInputOwner.JOB_MEMORY_BYTES,
                ref("military.jar"), ref("policy.json"), ref("input-capacity.json"));
        var syntheticPolicy = new CiBootstrap.Policy(1, 1000, new java.math.BigDecimal("0.01"), 1_000_000_000,
                new java.math.BigDecimal("0.1"), 168);
        var volume = CiBootstrap.calculate(syntheticPolicy, 10_000_000_000L, 5_000_000_000L, 100_000_000, 0, 1000, 100_000_000);
        var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", MACHINE, now.toString(), review.toString(), "RELEASED", "owner-v3",
                grant.policyRef(), List.of(grant.inputRoot()), temporary.toString(), Map.of("projection_input", 100_000_000L),
                Map.of(temporary.getRoot().toString(), volume), Map.of(), ProjectionArtifactInputOwner.JOB_MEMORY_BYTES, 256L << 20);
        assertEquals(volume, ProjectionArtifactInputOwner.requireBudget(grant, release, syntheticPolicy));
        var wrongPart = new ControlBuild.CapacityRelease(release.schema(), release.machineId(), release.observedAtUtc(), release.reviewAtUtc(), release.status(), release.ownerTask(),
                release.policyRef(), release.approvedOutputRoots(), release.temporaryRoot(), Map.of("event_input", 100_000_000L), release.volumes(), release.quotaOverrides(), release.memoryLimitBytes(), release.mavenHeapBytes());
        assertThrows(IOException.class, () -> ProjectionArtifactInputOwner.requireBudget(grant, wrongPart, syntheticPolicy));
        var wrongVolume = new CiBootstrap.VolumeBudget(volume.totalVolumeBytes(), volume.availableBytes(), volume.thisWritePeak(), volume.otherUnspentReservations(),
                volume.systemGrowthReserve(), volume.safetyReserve(), volume.currentProjectUsageConservativeUpper(), volume.effectiveProjectQuota(), volume.requiredFree() + 1);
        var drift = new ControlBuild.CapacityRelease(release.schema(), release.machineId(), release.observedAtUtc(), release.reviewAtUtc(), release.status(), release.ownerTask(),
                release.policyRef(), release.approvedOutputRoots(), release.temporaryRoot(), release.parts(), Map.of(temporary.getRoot().toString(), wrongVolume), release.quotaOverrides(), release.memoryLimitBytes(), release.mavenHeapBytes());
        assertThrows(IOException.class, () -> ProjectionArtifactInputOwner.requireBudget(grant, drift, syntheticPolicy));
    }
    private Scope scope() {
        return new Scope("scope", "owner-session", MACHINE, process(), InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE, temporary.resolve("slot"), temporary.resolve("lease.json"),
                100_000_000, ISSUED, EXPIRES, ref("source-binding.json"), ref("military.jar"), ref("build.json"), ref("runtime-binding.json"), ProjectionArtifactInputOwner.PRODUCER_CLASS);
    }
    private ProcessIdentity process() { return new ProcessIdentity(1, "18446744073709551615", temporary.resolve("java.exe")); }
    private ControlBuild.FileRef ref(String name) { return new ControlBuild.FileRef(temporary.resolve(name).toString(), 1, "0".repeat(64)); }
    private static byte[] bytes(ObjectNode row) throws IOException { return ControlBuild.strictMapper().writeValueAsBytes(row); }
    private ControlBuild.BuildReceipt build() {
        List<ControlBuild.FileRef> sources = new ArrayList<>(), compiled = new ArrayList<>();
        for (String name : List.of("ProjectionArtifactAuthority.java", "ProjectionArtifactInputOwner.java", "MapAdmissionServiceOwner.java")) {
            String suffix = "build-tools/src/main/java/org/xar/ck3/control/build/" + name; sources.add(ref("source/" + suffix)); compiled.add(ref("compiled/" + suffix));
        }
        return build(sources, compiled);
    }
    private ControlBuild.BuildReceipt build(List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> compiled) {
        return new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, MACHINE, ISSUED.toString(), "PASS", temporary.resolve("source").toString(), temporary.resolve("compiled").toString(), temporary.resolve("deployment").toString(),
                new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null), new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null), ControlBuild.TargetKind.SERVICE_FAST_JAR,
                ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022, sources, compiled, List.of(ref("military.jar")), List.of(ref("owner.jar")),
                ref("capacity.json"), null, ref("java.exe"), null, null, Map.of(), null);
    }
    private MapAdmissionServiceOwner.ProjectionProgramManifest v2() {
        var profile = new ProjectionDeploymentProof.OperationProfile(InputOperation.MILITARY_COMBAT_ROLES_NORMALIZE.wire(), 65536, 65536);
        var identity = new ProjectionDeploymentProof.Identity("xar.projection-host-identity/v1", ProjectionDeploymentProof.PRODUCER, ProjectionDeploymentProof.VERSION,
                ProjectionDeploymentProof.CALL_SCHEMA, ProjectionDeploymentProof.RESULT_SCHEMA, ProjectionDeploymentProof.MAX_ENVELOPE_BYTES, List.of(profile));
        var proof = new ProjectionDeploymentProof.Attestation(identity, List.of());
        var host = new MapAdmissionServiceOwner.ObservedHostContext(new MapAdmissionServiceOwner.HostContext("xar.projection-host-context/v1", MACHINE, ISSUED.toString(), null), ref("host-response.json"));
        return new MapAdmissionServiceOwner.ProjectionProgramManifest("xar.java-projection-complete-fastjar-deployment/v2", MACHINE, ISSUED.toString(), temporary.resolve("deployment").toString(),
                List.of(ref("military.jar")), build().sourcePins(), ref("build.json"), ref("java.exe"), true, true, proof, host, null, null, ProjectionCaptureScope.Qualification.FULL_SOFTWARE, null);
    }
    private MapAdmissionServiceOwner.ProjectionProgramManifestV3 v3() {
        var base = v2(); var observation = new Observed(new Context(MACHINE, ISSUED, Optional.of(new Active(ref("scope.json"), ref("lease.json"), scope(), process()))), ref("artifact-response.json"));
        return new MapAdmissionServiceOwner.ProjectionProgramManifestV3("xar.java-projection-complete-fastjar-deployment/v3", MACHINE, base.observedAtUtc(), base.deploymentRoot(), base.files(), base.sourceRefs(),
                base.buildReceiptRef(), base.javaExecutableRef(), true, true, base.projection(), base.hostContext(), null, null, ProjectionCaptureScope.Qualification.FULL_SOFTWARE, null, observation);
    }
}
