package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Software contract regression; no accepted build, actual SDK execution or game qualification is claimed. */
final class CiBootstrapCompletePipelineTimingTest {
    private static final Instant START = Instant.parse("2026-10-25T00:00:00Z");

    private static CiBootstrap.Plan plan(String schema, Instant observed, Instant review) {
        var pin = new CiBootstrap.FilePin(Path.of("software-policy.json").toAbsolutePath().toString(), 1, "0".repeat(64));
        var quota = new CiBootstrap.QuotaOverride("software-owner", "github-actions-java-ci",
                "software fixture finite review", 8L << 30, review.toString(), pin);
        return new CiBootstrap.Plan(schema, "software-machine", observed.toString(), review.toString(),
                "software-repo", "software-work", "software-java", null, "software-python",
                "github-actions-java-ci", pin, Map.of(), Map.of("software-volume", quota),
                Map.of("scratch", 1024L), List.of(pin), List.of(pin), false, false);
    }

    @Test void completePublishedPlanRetainsOriginalClockAndPins(@TempDir Path directory) throws Exception {
        var original = plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(Duration.ofHours(7)));
        var reference = CiBootstrap.publish(directory.resolve("complete-plan.json"), original);
        var decoded = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(reference.path())), CiBootstrap.Plan.class);
        assertEquals(original, decoded);
        assertEquals(CiBootstrap.PipelineProfile.COMPLETE_CURRENT, CiBootstrap.pipelineProfile(decoded));
        var timing = CiBootstrap.pipelineTiming(decoded);
        assertEquals(START, timing.observedAt());
        assertEquals(START.plus(Duration.ofHours(7)), timing.outerDeadline());
        assertEquals(timing.outerDeadline().minusSeconds(30), timing.workDeadline());
        assertEquals(Duration.ofHours(6).minusSeconds(30), timing.remainingWork(START.plus(Duration.ofHours(1))));
        assertThrows(IOException.class, () -> timing.remainingWork(timing.workDeadline()));
        assertEquals(Duration.ofSeconds(30), timing.remainingOuter(timing.workDeadline()));
        assertThrows(IOException.class, () -> timing.remainingOuter(timing.outerDeadline()));
        assertEquals(timing, CiBootstrap.pipelineTiming(decoded));
    }

    @Test void completeAdmissionIncludesAllFourFreshCommandsAndCanonicalReviewReserve() throws IOException {
        var budget = CiBootstrap.completePipelineBudget();
        assertEquals(FreshSdkFixtureStage.Stage.values().length, budget.freshCommands());
        assertEquals(4, budget.freshCommands());
        assertEquals(900, budget.freshCommandSeconds());
        assertEquals(2100, budget.canonicalSeconds());
        assertEquals(900, budget.originalReviewSeconds());
        assertEquals(Duration.ofSeconds(22780), budget.minimumTotal());
        assertEquals(3660, budget.bootstrapSeconds());
        assertEquals(8100, budget.nativeBuildSeconds());
        assertEquals(4500 + ControlBuild.maximumBuildTimeoutSeconds(ControlBuild.TargetKind.SERVICE_FAST_JAR),
                budget.nativeBuildSeconds());
        var exact = plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(budget.minimumTotal()));
        var timing = CiBootstrap.pipelineTiming(exact);
        CiBootstrap.requireCompletePipeline(exact);
        long preceding = budget.bootstrapSeconds() + budget.nativeBuildSeconds() + budget.mapConsumerSeconds()
                + budget.pythonStaticSeconds() + budget.supplementalSeconds() + budget.preparationSeconds()
                + budget.freshCommands() * budget.freshCommandSeconds();
        assertEquals(Duration.ofSeconds(3000), timing.remainingWork(START.plusSeconds(preceding)));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineTiming(
                plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(budget.minimumTotal()).minusNanos(1))));
    }

    @Test void completeAuthorityHasFiniteMaximumAndDoesNotRestartAtNestedAdmission() throws IOException {
        var maximum = plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(Duration.ofHours(8)));
        var timing = CiBootstrap.pipelineTiming(maximum);
        assertEquals(Duration.ofMinutes(30).minusSeconds(30), timing.remainingWork(START.plus(Duration.ofMinutes(450))));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineTiming(
                plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(Duration.ofHours(8)).plusNanos(1))));
        assertThrows(IOException.class, () -> timing.remainingWork(START.minusNanos(1)));
    }

    @Test void executionLeaseOnlyNarrowsQuotaAndPreservesOriginalTimeline(@TempDir Path directory) throws Exception {
        var original = plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(Duration.ofHours(7)));
        var execution = CiBootstrap.pipelineExecutionPlan(original);
        String work = CiBootstrap.pipelineTiming(original).workDeadline().toString();
        assertEquals(work, execution.reviewAtUtc());
        assertEquals(work, execution.quotaOverrides().get("software-volume").reviewAtUtc());
        assertEquals(original.observedAtUtc(), execution.observedAtUtc());
        assertEquals(original.schema(), execution.schema());
        assertEquals(original.policyRef(), execution.policyRef());
        assertEquals(original.sourcePins(), execution.sourcePins());
        assertEquals(original.bootstrapRuntimeClosure(), execution.bootstrapRuntimeClosure());
        var pin = CiBootstrap.publish(directory.resolve("execution-lease.json"), execution);
        assertEquals(execution, ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(pin.path())), CiBootstrap.Plan.class));
        assertEquals(START.plus(Duration.ofHours(7)).toString(), original.reviewAtUtc());
    }

    @Test void legacyWireAndOldServiceConstructorsKeepTheirBounds(@TempDir Path directory) throws Exception {
        var legacy = plan(CiBootstrap.PLAN_SCHEMA, START, START.plus(Duration.ofMinutes(90)));
        var pin = CiBootstrap.publish(directory.resolve("legacy-plan.json"), legacy);
        var decoded = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(pin.path())), CiBootstrap.Plan.class);
        assertEquals(legacy, decoded);
        assertEquals(START.plus(Duration.ofMinutes(45)), CiBootstrap.pipelineTiming(decoded).outerDeadline());
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.requireCompletePipeline(decoded));
        Path root = directory.toAbsolutePath();
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(root.resolve("build.json"),
                root.resolve("service"), root.resolve("java.exe"), Instant.now().plus(Duration.ofHours(6)), 8089));
        var old = new MapAdmissionServiceOwner.Config(root.resolve("build.json"), root.resolve("service"),
                root.resolve("java.exe"), Instant.now().plusSeconds(60), 8089);
        assertEquals(CiBootstrap.PipelineProfile.LEGACY, old.pipelineProfile());
    }

    @Test void actualMapConfigToOwnerCarriesProfileAndSameAbsoluteDeadline(@TempDir Path directory) {
        Path root = directory.toAbsolutePath();
        Instant deadline = Instant.now().plus(Duration.ofHours(6));
        var config = new MapAdmissionCi.Config(root, root.resolve("build.json"), root.resolve("map-ci"),
                root.resolve("java.exe"), root.resolve("python.exe"), deadline, 8089,
                CiBootstrap.PipelineProfile.COMPLETE_CURRENT);
        var owner = MapAdmissionCi.serviceConfig(config, null, null);
        assertEquals(CiBootstrap.PipelineProfile.COMPLETE_CURRENT, owner.pipelineProfile());
        assertEquals(deadline, owner.leaseDeadline());
        assertEquals(config.workRoot().resolve("service"), owner.workRoot());
        assertEquals(config.buildReceipt(), owner.buildReceipt());
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(owner.buildReceipt(),
                owner.workRoot(), owner.javaExecutable(), Instant.now().plus(Duration.ofHours(8)).plusSeconds(60),
                8089, null, null, null, null, null, null, CiBootstrap.PipelineProfile.COMPLETE_CURRENT));
        assertThrows(NullPointerException.class, () -> new MapAdmissionCi.Config(root, root.resolve("build.json"),
                root.resolve("map-ci"), root.resolve("java.exe"), root.resolve("python.exe"), deadline, 8089, null));
    }

    @Test void hostedProfileRequiresNewExplicitReviewForCompleteRoute() throws Exception {
        byte[] old = hostedProfile("xar.java-control-CI-profile/v1", 90);
        byte[] current = hostedProfile("xar.java-control-CI-profile/v2", 245);
        assertEquals(Duration.ofMinutes(90), CiBootstrap.hostedReviewDuration(old, 8L << 30, CiBootstrap.PipelineProfile.LEGACY));
        assertEquals(Duration.ofMinutes(90), CiBootstrap.hostedReviewDuration(current, 8L << 30, CiBootstrap.PipelineProfile.LEGACY));
        assertEquals(Duration.ofMinutes(245), CiBootstrap.hostedReviewDuration(current, 8L << 30, CiBootstrap.PipelineProfile.COMPLETE_CURRENT));
        assertThrows(IOException.class, () -> CiBootstrap.hostedReviewDuration(old, 8L << 30, CiBootstrap.PipelineProfile.COMPLETE_CURRENT));
        assertThrows(IOException.class, () -> CiBootstrap.hostedReviewDuration(
                hostedProfile("xar.java-control-CI-profile/v2", 244), 8L << 30, CiBootstrap.PipelineProfile.COMPLETE_CURRENT));
    }

    @Test void planReaderRejectsUnknownSchemaAndExtraWireFields(@TempDir Path directory) throws Exception {
        var original = plan(CiBootstrap.COMPLETE_PLAN_SCHEMA, START, START.plus(Duration.ofHours(7)));
        var pin = CiBootstrap.publish(directory.resolve("strict-plan.json"), original);
        String raw = Files.readString(Path.of(pin.path()), StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                raw.replace(CiBootstrap.COMPLETE_PLAN_SCHEMA, "xar.java-control-CI-bootstrap-plan/v99"), CiBootstrap.Plan.class));
        assertThrows(IOException.class, () -> ControlBuild.strictMapper().readValue(
                raw.replaceFirst("\\{", "{\"unexpected\":true,"), CiBootstrap.Plan.class));
        assertTrue(CiBootstrap.supportedPlanSchema(original.schema()));
        assertTrue(!CiBootstrap.supportedPlanSchema(null));
    }

    @Test void hostedSoftwareAndManagedActualUseDifferentFinitePlanAndProfileContracts() throws Exception {
        var software=plan(CiBootstrap.SOFTWARE_PLAN_SCHEMA,START,START.plusSeconds(18000));
        var managed=plan(CiBootstrap.MANAGED_PLAN_SCHEMA,START,START.plusSeconds(43200));
        assertEquals(CiBootstrap.PipelineProfile.HOSTED_SOFTWARE,CiBootstrap.pipelineProfile(software));
        assertEquals(CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE,CiBootstrap.pipelineProfile(managed));
        assertEquals(Duration.ofSeconds(31000),CiBootstrap.managedPipelineMinimum());
        assertEquals(8100,CiBootstrap.completePipelineBudget().nativeBuildSeconds());
        assertEquals(START.plusSeconds(43200-30),CiBootstrap.pipelineTiming(managed).workDeadline());
        assertThrows(IllegalArgumentException.class,()->CiBootstrap.pipelineTiming(
                plan(CiBootstrap.MANAGED_PLAN_SCHEMA,START,START.plusSeconds(30999))));
        // Hosted 300 minutes is an explicit finite declaration, not authority to compress real bounds.
        assertThrows(IllegalArgumentException.class,()->CiBootstrap.pipelineTiming(software));
        assertThrows(IllegalArgumentException.class,()->CiBootstrap.pipelineTiming(
                plan(CiBootstrap.SOFTWARE_PLAN_SCHEMA,START,START.plusSeconds(18001))));
        var mapper=ControlBuild.strictMapper();
        for(var original:List.of(software,managed))
            assertEquals(original,mapper.readValue(mapper.writeValueAsBytes(original),CiBootstrap.Plan.class));
        byte[] profile=("{\"schema\":\"xar.java-control-CI-profile/v3\",\"max_project_bytes\":8589934592,"
                +"\"review_minutes\":300,\"task\":\"github-actions-java-ci\","
                +"\"qualification_scope\":\"SOFTWARE_ONLY_NOT_POSTQUALIFIED\"}").getBytes(StandardCharsets.UTF_8);
        assertEquals(Duration.ofMinutes(300),CiBootstrap.hostedReviewDuration(profile,8L<<30,CiBootstrap.PipelineProfile.HOSTED_SOFTWARE));
        assertThrows(IOException.class,()->CiBootstrap.hostedReviewDuration(profile,8L<<30,CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE));
        assertThrows(IOException.class,()->CiBootstrap.hostedReviewDuration(
                hostedProfile("xar.java-control-CI-profile/v2",245),8L<<30,CiBootstrap.PipelineProfile.HOSTED_SOFTWARE));
        var service=new MapAdmissionCi.Config(Path.of("repository").toAbsolutePath(),Path.of("build.json").toAbsolutePath(),
                Path.of("map-output").toAbsolutePath(),Path.of("java.exe").toAbsolutePath(),Path.of("python.exe").toAbsolutePath(),
                Instant.now().plusSeconds(40000),8089,CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE);
        assertEquals(CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE,MapAdmissionCi.serviceConfig(service,null,null).pipelineProfile());
        assertEquals(service.leaseDeadline(),MapAdmissionCi.serviceConfig(service,null,null).leaseDeadline());
    }

    @Test void currentManagedPlanKeepsTwelveHourMaximumAndOriginalExecutionClock(@TempDir Path directory) throws Exception {
        var maximum = plan(CiBootstrap.MANAGED_PLAN_SCHEMA, START, START.plusSeconds(43200));
        assertEquals("xar.java-control-CI-bootstrap-plan/v4", maximum.schema());
        var published = CiBootstrap.publish(directory.resolve("managed-twelve-hour-plan.json"), maximum);
        var decoded = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(published.path())), CiBootstrap.Plan.class);
        assertEquals(maximum, decoded);
        var timing = CiBootstrap.pipelineTiming(decoded);
        assertEquals(START, timing.observedAt());
        assertEquals(START.plusSeconds(43200), timing.outerDeadline());
        assertEquals(START.plusSeconds(43170), timing.workDeadline());
        assertEquals(Duration.ofHours(12), timing.profile().maximumServiceLease());
        assertEquals(Duration.ofSeconds(7170), timing.remainingWork(START.plusSeconds(36000)));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineTiming(
                plan(CiBootstrap.MANAGED_PLAN_SCHEMA, START, START.plusSeconds(43200).plusNanos(1))));
        var minimum = plan(CiBootstrap.MANAGED_PLAN_SCHEMA, START, START.plusSeconds(31000));
        CiBootstrap.requireCompletePipeline(minimum);
        assertEquals(START.plusSeconds(30970), CiBootstrap.pipelineTiming(minimum).workDeadline());
        var execution = CiBootstrap.pipelineExecutionPlan(maximum);
        assertEquals(maximum.schema(), execution.schema());
        assertEquals(maximum.observedAtUtc(), execution.observedAtUtc());
        assertEquals(START.plusSeconds(43170).toString(), execution.reviewAtUtc());
        assertEquals(execution.reviewAtUtc(), execution.quotaOverrides().get("software-volume").reviewAtUtc());
        assertEquals(maximum.sourcePins(), execution.sourcePins());
        assertEquals(maximum.bootstrapRuntimeClosure(), execution.bootstrapRuntimeClosure());
        assertEquals(START.plusSeconds(43200).toString(), maximum.reviewAtUtc());
        var service = new MapAdmissionCi.Config(directory.toAbsolutePath(), directory.resolve("build.json").toAbsolutePath(),
                directory.resolve("map-service").toAbsolutePath(), directory.resolve("java.exe").toAbsolutePath(),
                directory.resolve("python.exe").toAbsolutePath(), Instant.now().plusSeconds(40000), 8089,
                CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE);
        assertEquals(service.leaseDeadline(), MapAdmissionCi.serviceConfig(service, null, null).leaseDeadline());
        assertThrows(IllegalArgumentException.class, () -> new MapAdmissionServiceOwner.Config(
                directory.resolve("build.json").toAbsolutePath(), directory.resolve("map-too-long").toAbsolutePath(),
                directory.resolve("java.exe").toAbsolutePath(), Instant.now().plusSeconds(43260), 8089,
                null, null, null, null, null, null, CiBootstrap.PipelineProfile.ROOT_MANAGED_COMPLETE));
    }

    @Test void historicalManagedWireRemainsEightHourDataAndDoesNotAcquireCurrentExecution(@TempDir Path directory) throws Exception {
        var old = plan(CiBootstrap.HISTORICAL_MANAGED_PLAN_SCHEMA, START, START.plusSeconds(28800));
        var pin = CiBootstrap.publish(directory.resolve("historical-managed-plan.json"), old);
        var mapper = ControlBuild.strictMapper();
        var decoded = mapper.readValue(Files.readAllBytes(Path.of(pin.path())), CiBootstrap.Plan.class);
        assertEquals(old, decoded);
        assertEquals("xar.java-control-CI-bootstrap-plan/v3", decoded.schema());
        assertEquals(START.plusSeconds(28800).toString(), decoded.reviewAtUtc());
        assertTrue(CiBootstrap.supportedPlanSchema(decoded.schema()));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.pipelineProfile(decoded));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.requireCompletePipeline(decoded));
        assertThrows(IllegalArgumentException.class, () -> plan(CiBootstrap.HISTORICAL_MANAGED_PLAN_SCHEMA,
                START, START.plusSeconds(28800).plusNanos(1)));
        String raw = Files.readString(Path.of(pin.path()), StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> mapper.readValue(
                raw.replace(START.plusSeconds(28800).toString(), START.plusSeconds(43200).toString()), CiBootstrap.Plan.class));
        assertEquals(Duration.ofHours(8), CiBootstrap.PipelineProfile.COMPLETE_CURRENT.maximumTotal());
        assertEquals(Duration.ofMinutes(300), CiBootstrap.PipelineProfile.HOSTED_SOFTWARE.maximumTotal());
    }

    private static byte[] hostedProfile(String schema, int minutes) {
        return ("{\"schema\":\"" + schema + "\",\"max_project_bytes\":8589934592,\"review_minutes\":"
                + minutes + ",\"task\":\"github-actions-java-ci\"}").getBytes(StandardCharsets.UTF_8);
    }
}


