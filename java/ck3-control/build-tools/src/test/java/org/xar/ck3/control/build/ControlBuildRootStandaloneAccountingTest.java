package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Small real filesystem regressions. These fixture grants never authorize project execution. */
final class ControlBuildRootStandaloneAccountingTest {
    @TempDir Path temporary;
    private static final String ROOT = "/root/ck3-resume91-root-20261116-research";
    private record Fixture(ControlBuildAccountingTest.Fixture base, Path financial) { }

    @Test void actualRootAttemptUsesIndependentSourcesAndLeavesCanonicalRepositoryUnknown() throws Exception {
        Fixture fixture = fixture("root-live");
        Path cache = fixture.base().config().workRoot().resolve("m2/retained.bin");
        Files.write(cache, new byte[65536]); var original = ControlBuild.FileRef.measure(cache);
        var result = ControlBuild.accountWorkpackage(fixture.base().config(), () -> {});
        assertEquals(ControlBuild.RepositoryAccountingState.CONSERVATIVE_VOLUME_COVERAGE, result.repositoryAccountingState());
        assertNull(result.mavenRepositoryBaselineBytes()); assertNull(result.mavenRepositoryCurrentBytes());
        assertTrue(result.logicalBytesByScope().values().stream().mapToLong(Long::longValue).sum() < 65536);
        assertEquals(1, result.volumes().size()); original.verify();
        assertEquals(ControlBuild.FinancialLayout.ROOT_STANDALONE_V1, fixture.base().release().workpackageAccounting().financialLayout());
    }

    @Test void rootSourceBindingsCapsAndVersionCannotBeSubstituted() throws Exception {
        List<Consumer<ObjectNode>> changes = List.of(
                node -> node.put("attempt", "another-attempt"),
                node -> node.put("issuer_task", "/root/budget_fast_lane"),
                node -> node.put("canonical_maven_repository", temporary.resolve("foreign-m2").toString()),
                node -> node.put("maximum_new_native_bytes", 65L << 20),
                node -> node.put("current_whole_project_actual_usage_bytes", 0),
                node -> node.put("schema", "xar.java-phase1.resume56-r3-financial-supplement/v1"),
                node -> ((ObjectNode) node.path("volume_observations").elements().next()).remove("other_unspent_project_holds_bytes"),
                node -> ((ObjectNode) node.path("volume_observations").elements().next()).put("other_unspent_project_holds_bytes", 1),
                node -> node.put("unversioned_extra_permission", true));
        int index = 0;
        for (Consumer<ObjectNode> change : changes) {
            Fixture fixture = fixture("reject-root-" + index++); changeFinancial(fixture, change);
            assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(fixture.base().config(), () -> {}));
        }
        Fixture swapped = fixture("legacy-layout");
        var body = (ObjectNode) ControlBuild.strictMapper().valueToTree(swapped.base().release());
        ((ObjectNode) body.path("workpackage_accounting")).put("financial_layout", "CAPACITY_SUPPLEMENT18");
        Files.write(swapped.base().config().capacityRelease(), ControlBuild.strictMapper().writeValueAsBytes(body));
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(swapped.base().config(), () -> {}));
        Fixture changedSource = fixture("changed-source");
        var rootRef = changedSource.base().release().workpackageAccounting().reservationSourceRefs().getLast();
        Files.writeString(Path.of(rootRef.path()), "{}");
        assertThrows(IOException.class, () -> ControlBuild.accountWorkpackage(changedSource.base().config(), () -> {}));
    }

    @Test void newQuotaSeparatesPhysicalReservesAndStillChargesOtherProjectHolds() throws Exception {
        var volume = new ControlBuild.VolumeObservation("D:\\", 1000, 500, 500, 500, 300, 550, 100, 100, 100);
        assertThrows(IOException.class, () -> ControlBuild.requireVolumeQuote(volume));
        ControlBuild.requireRootStandaloneVolumeQuote(volume, 50);
        assertThrows(IOException.class, () -> ControlBuild.requireRootStandaloneVolumeQuote(volume, 51));
        var lowFree = new ControlBuild.VolumeObservation("D:\\", 1000, 250, 750, 750, 300, 950, 100, 100, 100);
        assertThrows(IOException.class, () -> ControlBuild.requireRootStandaloneVolumeQuote(lowFree));
        var usedUpper = new ControlBuild.VolumeObservation("D:\\", 1000, 500, 500, 551, 300, 550, 100, 100, 100);
        assertThrows(IOException.class, () -> ControlBuild.requireRootStandaloneVolumeQuote(usedUpper));
    }

    @Test void completedReceiptReusesTheSameRootFinancialContractAndRejectsChangedVolume() throws Exception {
        Fixture fixture = fixture("root-cold");
        var terminal = ControlBuildTest.completedReceiptFixture(temporary.resolve("terminal"));
        var accounting = ControlBuild.accountWorkpackage(fixture.base().config(), () -> {});
        Files.write(fixture.base().accounting(), ControlBuild.strictMapper().writeValueAsBytes(accounting));
        Path receipt = temporary.resolve("completed-root.json");
        Files.write(receipt, ControlBuild.strictMapper().writeValueAsBytes(completed(fixture.base(), terminal.receipt())));
        assertEquals(ControlBuild.FinancialLayout.ROOT_STANDALONE_V1, fixture.base().release().workpackageAccounting().financialLayout());
        assertEquals(ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receipt)).targetKind());
        ObjectNode changed = ControlBuild.strictMapper().valueToTree(accounting);
        ((ObjectNode) changed.path("volumes").get(0)).put("all_holds_bytes", 1)
                .put("required_free_bytes", 1 + accounting.volumes().getFirst().systemGrowthReserve() + accounting.volumes().getFirst().safetyReserve());
        Files.write(fixture.base().accounting(), ControlBuild.strictMapper().writeValueAsBytes(changed));
        Files.write(receipt, ControlBuild.strictMapper().writeValueAsBytes(completed(fixture.base(), terminal.receipt())));
        assertThrows(IOException.class, () -> ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receipt)));
    }

    @Test void completedReaderPreservesTheReleasedForwardSlashVolumeKeyInsteadOfRenderingItsPathAgain() throws Exception {
        Fixture fixture = fixture("root-forward-slash"); var mapper = ControlBuild.strictMapper();
        String oldKey = fixture.base().release().volumes().keySet().iterator().next(); String wireKey = oldKey.replace('\\', '/');
        ObjectNode financial = (ObjectNode) mapper.readTree(Files.readAllBytes(fixture.financial()));
        var rootRef = mapper.treeToValue(financial.path("root_authority_ref"), ControlBuild.FileRef.class);
        ObjectNode root = (ObjectNode) mapper.readTree(Files.readAllBytes(Path.of(rootRef.path())));
        ObjectNode holds = (ObjectNode) root.path("other_unspent_project_holds_bytes_by_volume"); holds.set(wireKey, holds.remove(oldKey));
        Files.write(Path.of(rootRef.path()), mapper.writeValueAsBytes(root)); var newRootRef = ControlBuild.FileRef.measure(Path.of(rootRef.path()));
        ObjectNode volumes = (ObjectNode) financial.path("volume_observations"); volumes.set(wireKey, volumes.remove(oldKey));
        financial.set("root_authority_ref", mapper.valueToTree(newRootRef));
        List<ControlBuild.FileRef> refs = new ArrayList<>(fixture.base().release().workpackageAccounting().reservationSourceRefs());
        refs.set(refs.indexOf(rootRef), newRootRef); financial.set("reservation_source_refs", mapper.valueToTree(refs));
        Files.write(fixture.financial(), mapper.writeValueAsBytes(financial));
        ObjectNode release = mapper.valueToTree(fixture.base().release()); ObjectNode releasedVolumes = (ObjectNode) release.path("volumes");
        releasedVolumes.set(wireKey, releasedVolumes.remove(oldKey));
        ObjectNode authority = (ObjectNode) release.path("workpackage_accounting"); authority.set("reservation_source_refs", mapper.valueToTree(refs));
        authority.set("financial_source_ref", mapper.valueToTree(ControlBuild.FileRef.measure(fixture.financial())));
        Files.write(fixture.base().config().capacityRelease(), mapper.writeValueAsBytes(release));
        var accounting = ControlBuild.accountWorkpackage(fixture.base().config(), () -> {});
        assertNotEquals(wireKey, accounting.volumes().getFirst().volumeRoot());
        assertEquals(Path.of(wireKey), Path.of(accounting.volumes().getFirst().volumeRoot()));
        Files.write(fixture.base().accounting(), mapper.writeValueAsBytes(accounting));
        var terminal = ControlBuildTest.completedReceiptFixture(temporary.resolve("forward-slash-terminal"));
        Path receipt = temporary.resolve("forward-slash-completed.json"); Files.write(receipt, mapper.writeValueAsBytes(completed(fixture.base(), terminal.receipt())));
        assertEquals(ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(receipt)).targetKind());
    }

    private Fixture fixture(String attempt) throws Exception {
        var existing = new ControlBuildAccountingTest(); existing.temporary = temporary;
        var base = existing.fixture(attempt); var old = base.release(); var mapper = ControlBuild.strictMapper();
        Files.createDirectory(base.config().workRoot().resolve("m2"));
        String volume = old.volumes().keySet().iterator().next(); var previous = old.volumes().get(volume);
        var policy = CiBootstrap.readPolicy(Files.readAllBytes(Path.of(old.policyRef().path())));
        var budget = CiBootstrap.calculate(policy, previous.totalVolumeBytes(), previous.availableBytes(), 64L << 20,
                previous.otherUnspentReservations(), previous.systemGrowthReserve(), previous.currentProjectUsageConservativeUpper());
        Path fundPath = temporary.resolve(attempt).resolve("native-fund.json"); ObjectNode fund = mapper.createObjectNode();
        fund.put("schema", "native.allocator.runtime-qualified-env-tools64-prospective/v1").put("atUtc", old.observedAtUtc())
                .put("machine_id", old.machineId()).put("owner", old.ownerTask()).put("allocator", "/root/native_continue")
                .put("new_distinct_net_upper_once_bytes", 64L << 20).put("raw_before", 100).put("raw_after", 100 + (64L << 20));
        fund.putObject("quote").put("source", 8L << 20).put("incremental_build_and_completed_deployment", 32L << 20)
                .put("tmp", 8L << 20).put("logs_and_durable_receipt", 8L << 20).put("new_m2_metadata_only", 8L << 20);
        fund.putObject("quota_exception").put("maximum_new_project_bytes", 64L << 20).put("maximum_project_bytes", 1);
        Files.write(fundPath, mapper.writeValueAsBytes(fund)); var fundRef = ControlBuild.FileRef.measure(fundPath);
        Path rootPath = temporary.resolve(attempt).resolve("root-authority.json"); ObjectNode root = mapper.createObjectNode();
        root.put("schema", ControlBuild.ROOT_STANDALONE_AUTHORITY_SCHEMA).put("machine_id", old.machineId()).put("issuer_task", ROOT)
                .put("owner_task", old.ownerTask()).put("attempt", attempt).put("observed_at_utc", old.observedAtUtc()).put("review_at_utc", old.reviewAtUtc())
                .put("work_root", base.config().workRoot().toString()).put("maximum_new_project_bytes", 64L << 20).put("maximum_project_bytes", budget.effectiveProjectQuota());
        root.set("policy_ref", mapper.valueToTree(old.policyRef())); root.set("native_fund_ref", mapper.valueToTree(fundRef));
        root.putObject("other_unspent_project_holds_bytes_by_volume").put(volume, 0);
        Files.write(rootPath, mapper.writeValueAsBytes(root)); var rootRef = ControlBuild.FileRef.measure(rootPath);
        List<ControlBuild.FileRef> refs = List.of(old.policyRef(), fundRef, rootRef);
        ObjectNode financial = mapper.createObjectNode();
        financial.put("schema", ControlBuild.ROOT_STANDALONE_FINANCIAL_SCHEMA).put("machine_id", old.machineId())
                .put("status", "RELEASED_ROOT_STANDALONE_BOUNDED_BUILD").put("issuer_task", ROOT).put("owner_task", old.ownerTask()).put("attempt", attempt)
                .put("observed_at_utc", old.observedAtUtc()).put("review_at_utc", old.reviewAtUtc()).put("work_root", base.config().workRoot().toString())
                .put("canonical_maven_repository", base.config().workRoot().resolve("m2").toRealPath().toString())
                .put("repository_accounting_state", "CONSERVATIVE_VOLUME_COVERAGE").putNull("current_whole_project_actual_usage_bytes")
                .put("maximum_new_native_bytes", 64L << 20).put("maximum_project_bytes", budget.effectiveProjectQuota()).put("shared_canonical_m2_growth_hold_once_bytes", 8L << 20);
        financial.set("attempt_roots", mapper.valueToTree(old.workpackageAccounting().measuredRoots()));
        financial.set("policy_ref", mapper.valueToTree(old.policyRef())); financial.set("root_authority_ref", mapper.valueToTree(rootRef));
        financial.set("native_fund_ref", mapper.valueToTree(fundRef)); financial.set("reservation_source_refs", mapper.valueToTree(refs));
        ObjectNode original = financial.putObject("volume_observations").putObject(volume);
        original.put("total", budget.totalVolumeBytes()).put("free", budget.availableBytes()).put("used_upper", budget.currentProjectUsageConservativeUpper())
                .put("actual_cluster_bytes", 4096).put("effective_project_quota", budget.effectiveProjectQuota())
                .put("all_holds_bytes", budget.thisWritePeak() + budget.otherUnspentReservations()).put("other_unspent_project_holds_bytes", 0)
                .put("system_growth_reserve", budget.systemGrowthReserve()).put("safety_reserve", budget.safetyReserve());
        var oldFinancial = mapper.readTree(Files.readAllBytes(Path.of(old.workpackageAccounting().financialSourceRef().path())));
        original.set("native_root_identity", oldFinancial.path("fresh_observations").path(volume.substring(0, 1).toUpperCase(java.util.Locale.ROOT)).path("native_root_identity"));
        Path financialPath = temporary.resolve(attempt).resolve("root-financial.json"); Files.write(financialPath, mapper.writeValueAsBytes(financial));
        var a = old.workpackageAccounting();
        Map<String, Long> scopes = new java.util.HashMap<>(a.nativeCapsByScope()); scopes.put("logs", 4L << 20);
        var authority = new ControlBuild.AttemptAccountingAuthority(a.schema(), a.attempt(), ControlBuild.FinancialLayout.ROOT_STANDALONE_V1,
                ControlBuild.FileRef.measure(financialPath), refs, a.measuredRoots(), scopes, a.maximumNewLogicalBytes(),
                scopes, a.maximumNewNativeBytes(), 8L << 20);
        var release = new ControlBuild.AttemptCapacityRelease(old.schema(), old.machineId(), old.observedAtUtc(), old.reviewAtUtc(), old.status(), old.ownerTask(),
                old.policyRef(), old.approvedOutputRoots(), old.mavenRepository(), old.buildRoot(), old.temporaryRoot(), old.parts(), Map.of(volume, budget), old.quotaOverrides(),
                old.memoryLimitBytes(), old.mavenHeapBytes(), authority);
        Files.write(base.config().capacityRelease(), mapper.writeValueAsBytes(release));
        return new Fixture(new ControlBuildAccountingTest.Fixture(base.config(), release, base.source(), base.snapshot(), base.build(), base.accounting()), financialPath);
    }

    private static void changeFinancial(Fixture fixture, Consumer<ObjectNode> mutation) throws Exception {
        var mapper = ControlBuild.strictMapper(); ObjectNode body = (ObjectNode) mapper.readTree(Files.readAllBytes(fixture.financial())); mutation.accept(body);
        Files.write(fixture.financial(), mapper.writeValueAsBytes(body)); ObjectNode release = mapper.valueToTree(fixture.base().release());
        ((ObjectNode) release.path("workpackage_accounting")).set("financial_source_ref", mapper.valueToTree(ControlBuild.FileRef.measure(fixture.financial())));
        Files.write(fixture.base().config().capacityRelease(), mapper.writeValueAsBytes(release));
    }

    private static ControlBuild.BuildReceipt completed(ControlBuildAccountingTest.Fixture fixture, ControlBuild.BuildReceipt terminal) throws Exception {
        Path deployment = fixture.build().resolve("ck3-control-build-tools");
        List<ControlBuild.FileRef> pins = new ArrayList<>(List.of(ControlBuild.FileRef.measure(deployment.resolve("ck3-control-build-tools-0.1.0-SNAPSHOT.jar")),
                ControlBuild.FileRef.measure(deployment.resolve("lib/fixture.jar")))); pins.sort(java.util.Comparator.comparing(ControlBuild.FileRef::path));
        var match = new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null);
        return new ControlBuild.BuildReceipt(ControlBuild.SCOPED_BUILD_SCHEMA, terminal.machineId(), Instant.now().toString(), "PASS",
                fixture.source().toString(), fixture.snapshot().toString(), deployment.toString(), match, match,
                ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME, ControlBuild.SourceLimitProfile.STANDARD_8_MIB,
                ControlBuild.sourceManifest(fixture.source()), ControlBuild.sourceManifest(fixture.snapshot()), pins, terminal.producerRuntimePins(),
                ControlBuild.FileRef.measure(fixture.config().capacityRelease()), terminal.mavenToolchain(), terminal.javaExecutableRef(), terminal.toolchainProbe(),
                terminal.mavenResult(), Map.of(), null, ControlBuild.FileRef.measure(fixture.accounting()));
    }
}
