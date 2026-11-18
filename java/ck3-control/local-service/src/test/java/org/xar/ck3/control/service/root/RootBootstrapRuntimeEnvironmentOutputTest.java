package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Owned Win32 storage fixtures only; no production issuer, ENV qualification or Game admission. */
final class RootBootstrapRuntimeEnvironmentOutputTest {
    @TempDir Path directory;
    private static final Instant NOW = Instant.now();
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    private static final byte[] BODY = "{\"software_fixture_only\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8);

    private record Fixture(Path asset, Path control, FileRef financial, CapacityRelease capacity, FileRef capacityRef) {
        FileRef bind(Clock clock) throws IOException {
            return RootProfileBootstrapCommand.bindIssuedCapacity(new RootProfileBootstrapCommand.IssuerBindingRequest(
                    "xar.java-root-bootstrap-issuer-binding-request/v1", capacity.machineId(), NOW.plusSeconds(900).toString(),
                    capacityRef, control.resolve("binding.json").toString()), clock).binding().original();
        }
    }

    @Test void publicBindingAndOriginalGuardAdmitOneExactEnvironmentUsingTheCurrentIssuerSource() throws Exception {
        Fixture fixture = fixture("positive", List.of(environment()), List.of());
        FileRef bindingRef = fixture.bind(CLOCK);
        Binding binding = decode(Files.readAllBytes(Path.of(bindingRef.path())), Binding.class);
        assertEquals(RUNTIME_BINDING, binding.schema());
        assertEquals(RUNTIME_ISSUER, binding.issuerTask());
        assertEquals(fixture.financial(), fixture.capacity().originalFinancialHeadRef());
        try (var guard = RootBootstrapOutputGuard.readExact(bindingRef, CLOCK)) {
            Path target = fixture.asset().resolve(environment().fileName());
            guard.requireTargets(List.of(target));
            var created = guard.files().createNew(target, BODY);
            guard.files().verify(created);
            assertArrayEquals(BODY, guard.files().read(created, 65536));
            assertEquals(1, guard.accounting().completedOutputs());
            assertEquals(0, guard.accounting().unresolvedPeakBytes());
            assertThrows(IOException.class, () -> guard.files().createNew(fixture.asset().resolve("initial-policy.json"), BODY));
        }
    }

    @Test void versionIssuerPurposeAndRetentionDoNotBroadenLegacyAuthority() throws Exception {
        Fixture fixture = fixture("versions", List.of(environment()), List.of());
        var mapper = ControlBuild.strictMapper();
        for (String issuer : List.of(ISSUER, ROOT_ISSUER, "/root")) {
            ObjectNode wrong = mapper.valueToTree(fixture.capacity()); wrong.put("issuer_task", issuer);
            assertThrows(IOException.class, () -> decode(mapper.writeValueAsBytes(wrong), CapacityRelease.class));
        }
        for (String schema : List.of(CAPACITY, ROOT_CAPACITY)) {
            ObjectNode wrong = mapper.valueToTree(fixture.capacity()); wrong.put("schema", schema);
            assertThrows(IOException.class, () -> decode(mapper.writeValueAsBytes(wrong), CapacityRelease.class));
        }
        ObjectNode wrongPurpose = mapper.valueToTree(fixture.capacity()); wrongPurpose.put("purpose", FORMAL_PURPOSE);
        assertThrows(IOException.class, () -> decode(mapper.writeValueAsBytes(wrongPurpose), CapacityRelease.class));
        ObjectNode wrongOwner = mapper.valueToTree(fixture.capacity()); wrongOwner.put("owner_task", RUNTIME_ISSUER);
        assertThrows(IOException.class, () -> decode(mapper.writeValueAsBytes(wrongOwner), CapacityRelease.class));
        var c = fixture.capacity();
        var retained = new RetainedAllocation(fixture.financial(), 4096, fixture.financial(),
                RetentionPurpose.ACTIVE_PROFILE_PRODUCTION_INPUT, c.reviewAtUtc(), fixture.financial());
        assertThrows(IllegalArgumentException.class, () -> new CapacityRelease(RUNTIME_CAPACITY, PURPOSE, c.machineId(),
                c.ownerTask(), RUNTIME_ISSUER, c.windowId(), c.observedAtUtc(), c.reviewAtUtc(), c.policyRef(), c.declarationRef(),
                c.censusRef(), c.originalFinancialHeadRef(), c.jointMaximumChargedBytes(), c.volumes(), List.of(retained)));
        var legacy = new CapacityRelease(CAPACITY, PURPOSE, c.machineId(), c.ownerTask(), ISSUER, c.windowId(),
                c.observedAtUtc(), c.reviewAtUtc(), c.policyRef(), c.declarationRef(), c.censusRef(), c.originalFinancialHeadRef(),
                c.jointMaximumChargedBytes(), c.volumes(), List.of(retained));
        assertEquals(legacy, decode(encode(legacy), CapacityRelease.class));
        assertThrows(IllegalArgumentException.class, () -> new Binding(RUNTIME_BINDING, PURPOSE, c.machineId(), "/root", ISSUER,
                c.windowId(), c.observedAtUtc(), c.reviewAtUtc(), c.declarationRef(), c.censusRef(), fixture.capacityRef()));
    }

    @Test void actualGuardRejectsOtherRolesAdditionalOutputsAndGeneratedDirectoriesBeforeAnEnvironmentWrite() throws Exception {
        Fixture wrong = fixture("wrong-role", List.of(output(Kind.INITIAL_POLICY, "initial-policy.json")), List.of());
        Fixture multiple = fixture("multiple", List.of(environment(), output(Kind.INITIAL_POLICY, "initial-policy.json")), List.of());
        Fixture directories = fixture("directories", List.of(environment()), List.of("mod"));
        for (Fixture fixture : List.of(wrong, multiple, directories)) {
            assertThrows(IOException.class, () -> fixture.bind(CLOCK));
            assertFalse(Files.exists(fixture.asset().resolve(environment().fileName())));
        }
    }

    @Test void exactCurrentFinancialOriginalAndReviewRemainRequired() throws Exception {
        Fixture changed = fixture("source-drift", List.of(environment()), List.of());
        Files.writeString(Path.of(changed.financial().path()), "changed-current-issuer-observation");
        assertThrows(IOException.class, () -> changed.bind(CLOCK));
        assertFalse(Files.exists(changed.asset().resolve(environment().fileName())));
        Fixture expired = fixture("expired", List.of(environment()), List.of());
        assertThrows(IOException.class, () -> expired.bind(Clock.fixed(NOW.plusSeconds(1801), ZoneOffset.UTC)));
        assertFalse(Files.exists(expired.asset().resolve(environment().fileName())));
    }

    private Fixture fixture(String name, List<Output> outputs, List<String> directories) throws IOException {
        Path base = Files.createDirectory(directory.resolve(name));
        Path asset = Files.createDirectory(base.resolve("asset")), control = Files.createDirectory(base.resolve("control"));
        String machine = WindowsJobProcess.currentMachineId(), review = NOW.plusSeconds(1800).toString();
        Declaration declaration = new Declaration(DECLARATION, PURPOSE, machine, "/root", name,
                NOW.minusSeconds(1).toString(), review, asset.toString(), SharedSourceFiles.nativeDirectory(asset),
                control.toString(), SharedSourceFiles.nativeDirectory(control), 1536L * 1024, 512L * 1024,
                1L << 20, 64, outputs, directories, List.of());
        FileRef declarationRef = write(control.resolve("declaration.json"), encode(declaration));
        FileRef censusRef = write(control.resolve("census.json"), encode(RootBootstrapOutputGuard.observeAssetRoot(declarationRef, CLOCK)));
        ObjectNode policy = StrictJson.object().put("policy_version", "1.0.0");
        policy.putObject("capacity").put("safety_floor_bytes", 2L << 30).put("safety_ceiling_bytes", 20L << 30)
                .put("default_project_quota_ceiling_bytes", 100L << 30)
                .put("safety_volume_fraction", new java.math.BigDecimal("0.05"))
                .put("default_project_quota_volume_fraction", new java.math.BigDecimal("0.10"));
        FileRef policyRef = write(control.resolve("policy.json"), ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume = asset.getRoot();
        long total = Files.getFileStore(volume).getTotalSpace(), free = Files.getFileStore(volume).getUsableSpace();
        ObjectNode financial = StrictJson.object().put("scope", "software-only-current-runtime-volume-observation")
                .put("machine_id", machine).put("total_bytes", total).put("usable_bytes", free)
                .put("production_qualification", false);
        FileRef head = write(control.resolve("current-runtime-fixture.json"), StrictJson.canonical(financial));
        var usage = new RootRuntimeStorageContract.ExistingUsage(
                RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER, null, total - free, head);
        var release = new CapacityRelease(RUNTIME_CAPACITY, PURPOSE, machine, "/root", RUNTIME_ISSUER, name,
                NOW.toString(), review, policyRef, declarationRef, censusRef, head, 2L << 20,
                List.of(new Volume(volume.toString(), 2L << 20, 0, 0, total, review, usage, List.of(), 0)), List.of());
        FileRef capacityRef = write(control.resolve("capacity.json"), encode(release));
        return new Fixture(asset, control, head, release, capacityRef);
    }

    private static Output environment() { return output(Kind.PROFILE_ENVIRONMENT, "xar-autoplayer-environment.json"); }
    private static Output output(Kind kind, String name) { return new Output(kind, name, BODY.length, DriverJson.sha256(BODY)); }
    private static FileRef write(Path target, byte[] bytes) throws IOException { Files.write(target, bytes); return FileRef.measure(target); }
}
