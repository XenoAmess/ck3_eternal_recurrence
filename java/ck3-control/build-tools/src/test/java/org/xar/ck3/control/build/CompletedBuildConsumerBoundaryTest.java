package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Synthetic receipt/source fixtures exercise real readers and writers; they grant no artifact qualification. */
final class CompletedBuildConsumerBoundaryTest {
    @TempDir Path temporary;
    private static final String SDK_PRODUCER = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
    private static final String SUITE = "org.xar.ck3.control.fixture.CompletedConsumerTest";
    private static final ReactorTestClosure.RequiredSuite REQUIRED = new ReactorTestClosure.RequiredSuite(
            "local-service", "ck3-control-local-service", SUITE, 1);

    private record ServiceFixture(FileRef receipt, ControlBuild.BuildReceipt build, Path buildRoot) { }

    private ServiceFixture service(String name) throws Exception {
        Path root = temporary.resolve(name);
        var original = ControlBuildTest.completedReceiptFixture(root);
        for (Path tree : List.of(original.sourceRoot(), original.compiledRoot())) {
            Files.writeString(tree.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId>"
                    + "<artifactId>receipt</artifactId><version>1</version><packaging>pom</packaging>"
                    + "<modules><module>local-service</module></modules></project>");
            Path module = tree.resolve("local-service");
            Path source = module.resolve("src/test/java/" + SUITE.replace('.', '/') + ".java");
            Files.createDirectories(source.getParent());
            Files.writeString(source, "package org.xar.ck3.control.fixture; class CompletedConsumerTest {}\n");
            Files.writeString(module.resolve("pom.xml"),
                    "<project><artifactId>ck3-control-local-service</artifactId></project>");
        }
        Path buildRoot = Files.createDirectories(root.resolve("reactor"));
        Path deployment = Files.createDirectories(buildRoot.resolve("ck3-control-local-service/quarkus-app"));
        Path archive = deployment.resolve("quarkus-run.jar");
        Files.writeString(archive, "explicit synthetic service archive fixture");
        var mapper = ControlBuild.strictMapper();
        ObjectNode node = mapper.valueToTree(original.receipt());
        node.put("target_kind", ControlBuild.TargetKind.SERVICE_FAST_JAR.name());
        node.put("deployment_root", deployment.toString());
        node.set("source_pins", mapper.valueToTree(ControlBuild.sourceManifest(original.sourceRoot())));
        node.set("compiled_source_pins", mapper.valueToTree(ControlBuild.sourceManifest(original.compiledRoot())));
        node.set("complete_deployment", mapper.valueToTree(List.of(FileRef.measure(archive))));
        Path receipt = root.resolve("completed-service-fixture.json");
        Files.write(receipt, mapper.writeValueAsBytes(node), StandardOpenOption.CREATE_NEW);
        FileRef ref = FileRef.measure(receipt);
        var completed = ControlBuild.verifiedCompletedReceipt(ref);
        String originalJna = System.getProperty("jna.tmpdir");
        try {
            System.setProperty("jna.tmpdir", root.resolve("scratch").toRealPath().toString());
            assertEquals("Build capacity release expired",
                    assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(receipt)).getMessage());
        } finally {
            if (originalJna == null) System.clearProperty("jna.tmpdir");
            else System.setProperty("jna.tmpdir", originalJna);
        }
        return new ServiceFixture(ref, completed, buildRoot);
    }

    @Test void expiredCompletedBuildUsesItsOwnWindowUnderIndependentCurrentScratch() throws Exception {
        var fixture = ControlBuildTest.completedReceiptFixture(temporary.resolve("historical-build"));
        Path currentScratch = Files.createDirectories(temporary.resolve("independent-current/scratch")).toRealPath();
        assertNotEquals(fixture.receiptPath().getParent().resolve("scratch").toRealPath(), currentScratch);
        String originalJna = System.getProperty("jna.tmpdir");
        try {
            System.setProperty("jna.tmpdir", currentScratch.toString());
            assertEquals(fixture.receipt(), ControlBuild.verifiedCompletedReceipt(fixture.receiptRef()));
            assertEquals("Build capacity release expired",
                    assertThrows(IOException.class, () -> ControlBuild.acceptedReceipt(fixture.receiptPath())).getMessage());
        } finally {
            if (originalJna == null) System.clearProperty("jna.tmpdir");
            else System.setProperty("jna.tmpdir", originalJna);
        }
    }

    @Test void originalReactorReportProducerAndReaderUseCompletedBuildWhileReportDriftStillRejects() throws Exception {
        var fixture = service("reactor-report");
        Path report = fixture.buildRoot().resolve("ck3-control-local-service/surefire-reports/TEST-" + SUITE + ".xml");
        Files.createDirectories(report.getParent());
        Files.writeString(report, "<testsuite name=\"" + SUITE
                + "\" tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"><testcase name=\"original\" classname=\""
                + SUITE + "\"/></testsuite>");
        Path output = temporary.resolve("reactor-report-actual.json");
        var actual = ReactorTestClosure.run(Path.of(fixture.receipt().path()), output, List.of(REQUIRED));
        assertEquals(actual, ReactorTestClosure.requireAccepted(output, Path.of(fixture.receipt().path()), List.of(REQUIRED)));
        Files.writeString(report, Files.readString(report).replace("name=\"original\"", "name=\"changed\""));
        assertThrows(IOException.class, () -> ReactorTestClosure.requireAccepted(output,
                Path.of(fixture.receipt().path()), List.of(REQUIRED)));
        fixture.receipt().verify();
        assertEquals(fixture.build(), ControlBuild.verifiedCompletedReceipt(fixture.receipt()));
    }

    private FileRef sdkReview(ServiceFixture fixture, String name) throws Exception {
        Path canonical = Files.createDirectories(temporary.resolve(name + "-canonical"));
        Path sdk = Files.createDirectories(canonical.resolve("ck3_autonomous_player/src"));
        Path leaf = sdk.resolve("fixture.py"); Files.writeString(leaf, "FIXTURE = 1\n");
        Path producer = canonical.resolve(SDK_PRODUCER);
        Files.createDirectories(producer.getParent()); Files.writeString(producer, "# explicit source custody fixture\n");
        Path frozenSdk = Files.createDirectory(temporary.resolve(name + "-frozen-sdk"));
        Path frozenHost = Files.createDirectory(temporary.resolve(name + "-frozen-host"));
        Path frozenRuntime = Files.createDirectory(temporary.resolve(name + "-frozen-runtime"));
        var request = new SdkSourceAssembly.Request(SdkSourceAssembly.REQUEST_SCHEMA,
                WindowsJobProcess.currentMachineId(), canonical.toString(), "0".repeat(40), canonical.toString(),
                temporary.resolve(name + "-graph").toString(), sdk.toString(), "ck3_autonomous_player/src",
                List.of(".", "ck3_autonomous_player/src"), List.of(canonical.toString()),
                List.of(new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_SDK, frozenSdk.toString()),
                        new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_HOST, frozenHost.toString()),
                        new SdkSourceAssembly.ProtectedRoot(SdkSourceAssembly.ProtectedRole.FROZEN_RUNTIME, frozenRuntime.toString())),
                List.of(new SdkSourceAssembly.Source(SDK_PRODUCER, SdkSourceAssembly.SourceRole.PRODUCER,
                                SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, FileRef.measure(producer), List.of()),
                        new SdkSourceAssembly.Source("ck3_autonomous_player/src/fixture.py", SdkSourceAssembly.SourceRole.SDK_SOURCE,
                                SdkSourceAssembly.InputOrigin.CURRENT_CANONICAL, FileRef.measure(leaf), List.of())),
                List.of(new SdkSourceAssembly.ImportRoute("tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1",
                                SDK_PRODUCER, SdkSourceAssembly.ImportSourceLocation.FRESH_GRAPH, true),
                        new SdkSourceAssembly.ImportRoute("fixture", "ck3_autonomous_player/src/fixture.py",
                                SdkSourceAssembly.ImportSourceLocation.FRESH_GRAPH, false)),
                List.of(new SdkSourceAssembly.Deployment("completed-service", fixture.receipt(), ControlBuild.TargetKind.SERVICE_FAST_JAR)),
                new SdkSourceAssembly.ProducerReuse(SDK_PRODUCER,
                        "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1",
                        "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1"),
                8L << 20);
        Path requestPath = temporary.resolve(name + "-request.json");
        Files.write(requestPath, ControlBuild.strictMapper().writeValueAsBytes(request), StandardOpenOption.CREATE_NEW);
        var review = SdkSourceAssembly.review(FileRef.measure(requestPath));
        assertEquals(fixture.build().completeDeployment(), review.deploymentClosure().getFirst().completeFiles());
        return SdkSourceAssembly.writeReview(review, temporary.resolve(name + "-review.json"));
    }

    private SdkSourceAssembly.CapacityGate gate(FileRef evidence, Instant expires, AtomicInteger rechecks) {
        return new SdkSourceAssembly.CapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.Review review) {
                return new SdkSourceAssembly.WritePermit(review.machineId(), review.request().outputRoot(), expires.toString(),
                        8L << 20, 4096, 4096, evidence);
            }
            @Override public void revalidate(SdkSourceAssembly.WritePermit permit, long consumed) throws IOException {
                evidence.verify(); rechecks.incrementAndGet();
                if (consumed > permit.allocationUpperLimitBytes()) throw new IOException("actual fixture capacity exhausted");
            }
        };
    }

    @Test void sdkProducerAndReaderConsumeExpiredCompletedBuildUnderSeparateFreshPermit() throws Exception {
        var fixture = service("sdk-completed");
        FileRef reviewRef = sdkReview(fixture, "sdk-fresh");
        var checks = new AtomicInteger();
        var actual = SdkSourceAssembly.assemble(reviewRef, gate(reviewRef, Instant.now().plusSeconds(120), checks));
        assertTrue(checks.get() > 0);
        Path output = Path.of(actual.graphRoot()).resolve(".assembly/ACTUAL.json");
        assertEquals(actual, SdkSourceAssembly.readActual(FileRef.measure(output)));
        assertEquals(fixture.receipt(), actual.deploymentClosure().getFirst().actualBuildReceipt());
        Path archive = Path.of(fixture.build().completeDeployment().getFirst().path());
        Files.writeString(archive, "changed synthetic archive fixture");
        assertThrows(IOException.class, () -> SdkSourceAssembly.readActual(FileRef.measure(output)));
    }

    @Test void completedBuildCannotReplaceExpiredOrRejectedCurrentSdkAllocation() throws Exception {
        var fixture = service("sdk-no-authority");
        FileRef expired = sdkReview(fixture, "sdk-expired");
        assertThrows(IOException.class, () -> SdkSourceAssembly.assemble(expired,
                gate(expired, Instant.now().minusSeconds(1), new AtomicInteger())));
        assertFalse(Files.exists(temporary.resolve("sdk-expired-graph")));
        FileRef denied = sdkReview(fixture, "sdk-denied");
        assertThrows(IOException.class, () -> SdkSourceAssembly.assemble(denied, new SdkSourceAssembly.CapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.Review review) throws IOException {
                throw new IOException("current operation capacity refused");
            }
            @Override public void revalidate(SdkSourceAssembly.WritePermit permit, long consumed) { fail("No issued permit"); }
        }));
        assertFalse(Files.exists(temporary.resolve("sdk-denied-graph")));
        assertEquals(fixture.build(), ControlBuild.verifiedCompletedReceipt(fixture.receipt()));
    }

    @Test void successorOwnSelectionStillRejectsOriginal44AndForeignSourceIdentity() {
        FileRef selected = new FileRef(temporary.resolve("ToolsIntegratedAcceptedReadback24c.java").toString(),
                ToolsInputPostqualification.OWN_SOURCE_BYTES, ToolsInputPostqualification.OWN_SOURCE_SHA256);
        FileRef pin = new FileRef(temporary.resolve("metadata-only").toString(), 1, "0".repeat(64));
        var current = new ToolsInputPostqualification.FullOwnInputs(selected, pin, pin, pin, pin, pin, pin, pin);
        assertEquals(selected, current.producerSourceRef());
        FileRef original44 = new FileRef(selected.path(), 38123,
                "91548c5d7ad132e903383f7251b508770d246871abc69aba37d1dac3b0ba0d51");
        assertThrows(IllegalArgumentException.class, () -> new ToolsInputPostqualification.FullOwnInputs(
                original44, pin, pin, pin, pin, pin, pin, pin));
        FileRef foreign = new FileRef(selected.path(), selected.bytes(), "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> new ToolsInputPostqualification.FullOwnInputs(
                foreign, pin, pin, pin, pin, pin, pin, pin));
    }

    @Test void actualPostqualificationProducerRejectsExpiredConsumerWindowBeforePublishingAnything() throws Exception {
        var fixture = ControlBuildTest.completedReceiptFixture(temporary.resolve("expired-consumer"));
        FileRef pin = fixture.receiptRef();
        Instant observed = Instant.now(), review = observed.plusSeconds(300);
        var plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, WindowsJobProcess.currentMachineId(),
                observed.toString(), review.toString(), temporary.toString(), temporary.toString(), temporary.toString(),
                null, temporary.resolve("python.exe").toString(), "consumer-boundary-fixture",
                CiBootstrap.measure(fixture.releasePath()), Map.of(), Map.of(), Map.of(),
                List.of(CiBootstrap.measure(fixture.releasePath())), List.of(CiBootstrap.measure(fixture.releasePath())), false, false);
        Path planPath = temporary.resolve("expired-consumer-plan.json");
        Files.write(planPath, ControlBuild.strictMapper().writeValueAsBytes(plan), StandardOpenOption.CREATE_NEW);
        Path manifest = temporary.resolve("absent-consumer-manifest.json"), input = temporary.resolve("absent-consumer-input.json");
        var request = new ToolsPostqualificationInputProducer41.Request(ToolsPostqualificationInputProducer41.REQUEST_SCHEMA,
                FileRef.measure(planPath), FileRef.measure(fixture.releasePath()), pin,
                new ToolsPostqualificationInputProducer41.OwnSources(pin, pin, pin, pin, pin, pin, pin), List.of(pin),
                observed.plusSeconds(10).toString(), manifest.toString(), input.toString());
        Path requestPath = temporary.resolve("expired-consumer-request.json");
        Files.write(requestPath, ControlBuild.strictMapper().writeValueAsBytes(request), StandardOpenOption.CREATE_NEW);
        assertEquals("Actual current same-machine resource plan and original finite deadline required",
                assertThrows(IOException.class, () -> ToolsPostqualificationInputProducer41.produce(
                        FileRef.measure(requestPath), Clock.fixed(observed.plusSeconds(11), ZoneOffset.UTC))).getMessage());
        assertFalse(Files.exists(manifest)); assertFalse(Files.exists(input));
        assertEquals(fixture.receipt(), ControlBuild.verifiedCompletedReceipt(pin));
    }
}
