package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

final class ControlCiStageTest {
    @TempDir Path root;
    private ControlBuild.FileRef pin(String name) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, "synthetic immutable source pin"); return ControlBuild.FileRef.measure(path);
    }
    @Test void pinnedRequestHasOneStrictSchemaAndRequiresBothConfigs() throws Exception {
        var request = new ControlCi.FixtureRequest(ControlCi.FIXTURE_REQUEST_SCHEMA, "fixture-machine", Instant.now().plusSeconds(60).toString(), pin("fresh.json"), pin("canonical.json"));
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(request);
        assertEquals(request, mapper.readValue(raw, ControlCi.FixtureRequest.class));
        for (String wrong : List.of(raw.replace(ControlCi.FIXTURE_REQUEST_SCHEMA, "old-request/v0"),
                raw.replace("\"canonical_config_ref\"", "\"unknown_config_ref\""),
                raw.replace("\"bytes\":" + request.freshSdkConfigRef().bytes(), "\"bytes\":true"))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, ControlCi.FixtureRequest.class));
        }
    }
    @Test void cliForwardsExactPinsAndRejectsMissingDuplicateAndChangedRequests() throws Exception {
        Path plan = Path.of(pin("plan.json").path()); var request = pin("request.json");
        String[] valid = {"--bootstrap-plan", plan.toString(), "--fixture-stage-request", request.path(), Long.toString(request.bytes()), request.sha256()};
        var parsed = ControlCi.invocation(valid); assertEquals(request, parsed.fixtureRequestRef()); assertNull(parsed.toolsReceiptPath());
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--fixture-stage-request", request.path()}));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--unknown"}));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(new String[] {"--bootstrap-plan", plan.toString(), "--qualified-tools-receipt", plan.toString(), "--qualified-tools-receipt", plan.toString()}));
        Files.writeString(Path.of(request.path()), "changed request"); assertThrows(IOException.class, () -> ControlCi.invocation(valid));
    }
    private void report(String suite, String attributes, String cases) throws IOException {
        Files.writeString(root.resolve("TEST-" + suite + ".xml"), "<testsuite name=\"" + suite + "\" " + attributes + ">" + cases + "</testsuite>");
    }
    @Test void lateSelectedSuiteCannotDisappearFromActualToolReports() throws Exception {
        report("FirstTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"actual\"/>");
        ControlCi.requireJUnit(root, Set.of("FirstTest"));
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("FirstTest", "LateAddedTest")));
        report("LateAddedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"late_actual\"/>");
        ControlCi.requireJUnit(root, Set.of("FirstTest", "LateAddedTest"));
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("FirstTest")));
    }
    @Test void greenSurefireSummaryCannotHideSkippedOrMissingActualCaseChildren() throws Exception {
        report("SelectedTest", "tests=\"2\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"only_one\"/>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
        report("SelectedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"hidden_skip\"><skipped/></testcase>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
        report("SelectedTest", "tests=\"1\" failures=\"0\" errors=\"0\" skipped=\"0\"", "<testcase name=\"hidden_failure\"><failure/></testcase>");
        assertThrows(IOException.class, () -> ControlCi.requireJUnit(root, Set.of("SelectedTest")));
    }
    @Test void redReceiptPreservesFailedStageAndEveryUnstartedSuccessorAcrossJson() throws Exception {
        var stages = ControlCi.initialStages(); var evidence = pin("actual-stage.json");
        stages.set(ControlCi.Stage.EXPECTED_MAVEN_RED.ordinal(), new ControlCi.StageActual(ControlCi.Stage.EXPECTED_MAVEN_RED, ControlCi.StageState.PASS, evidence, null));
        stages.set(ControlCi.Stage.REACTOR.ordinal(), new ControlCi.StageActual(ControlCi.Stage.REACTOR, ControlCi.StageState.RED, evidence, "actual reactor failure"));
        var receipt = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "2026-10-22T00:00:00Z", "2026-10-22T00:00:01Z", ControlCi.PipelineState.RED, "actual reactor failure",
                evidence, evidence, evidence, null, evidence, null, List.of(), null, null, null, null, ControlCi.ExecutionPurpose.HOSTED_CI, null, stages);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(receipt);
        assertEquals(receipt, mapper.readValue(raw, ControlCi.Receipt.class));
        assertEquals(ControlCi.StageState.NOT_RUN, receipt.stages().get(ControlCi.Stage.CANONICAL_THIRTY.ordinal()).state());
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace(ControlCi.ACTUAL_SCHEMA, "xar.java-control-CI-actual/v3"), ControlCi.Receipt.class));
        var incomplete = new ArrayList<>(stages); incomplete.removeLast();
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.RED, "incomplete", null, null, null, null, null, null, List.of(), null, null, null, null, ControlCi.ExecutionPurpose.HOSTED_CI, null, incomplete));
    }
    @Test void bootstrapAndQualifiedChildForwardTheSameProductionPinAndRejectDrift() throws Exception {
        var production = pin("production-input.json"); var plan = pin("forwarded-plan.json");
        String[] args = {"--repo-root", root.toString(), "--work-root", root.resolve("work").toString(),
                "--python-executable", root.resolve("python.exe").toString(), "--system-growth-reserve-bytes", "1",
                "--max-project-bytes", "8589934592", "--fixture-production-request", production.path(),
                "--fixture-production-request-bytes", Long.toString(production.bytes()), "--fixture-production-request-sha256", production.sha256()};
        var values = CiBootstrap.arguments(args); var pinned = CiBootstrap.fixtureProductionPin(values);
        var bootstrap = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        CiBootstrap.appendFixtureProduction(bootstrap, pinned);
        var first = ControlCi.invocation(bootstrap.toArray(String[]::new));
        assertEquals(production, first.fixtureProductionRequestRef()); assertNull(first.fixtureRequestRef());
        var qualified = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        ControlCi.forwardFixtureRequests(qualified, null, first.fixtureProductionRequestRef());
        assertEquals(first, ControlCi.invocation(qualified.toArray(String[]::new)));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.arguments(java.util.Arrays.copyOf(args, 14)));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), production, production));
        var both = new ArrayList<>(qualified); both.addAll(List.of("--fixture-stage-request", production.path(), Long.toString(production.bytes()), production.sha256()));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(both.toArray(String[]::new)));
        Files.writeString(Path.of(production.path()), "changed actual production input");
        assertThrows(IOException.class, () -> CiBootstrap.appendFixtureProduction(new ArrayList<>(), pinned));
        assertThrows(IOException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), null, production));
    }
    @Test void requestedProductionCannotDisappearIntoAnOptionalBasePass() throws Exception {
        var evidence = pin("requested-production.json"); var stages = ControlCi.initialStages();
        for (var stage : ControlCi.Stage.values()) if (stage != ControlCi.Stage.FRESH_SDK && stage != ControlCi.Stage.CANONICAL_THIRTY) {
            stages.set(stage.ordinal(), new ControlCi.StageActual(stage, ControlCi.StageState.PASS, evidence, null));
        }
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b",
                ControlCi.PipelineState.PASS, null, evidence, evidence, evidence, null, evidence, evidence, List.of(), evidence, evidence, null, evidence, ControlCi.ExecutionPurpose.HOSTED_CI, null, stages));
        var red = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.RED,
                "actual host fixture unavailable", evidence, evidence, evidence, null, evidence, evidence, List.of(), evidence, evidence, null, evidence, ControlCi.ExecutionPurpose.HOSTED_CI, null, stages);
        assertEquals(red, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(red), ControlCi.Receipt.class));
        assertEquals(ControlCi.StageState.NOT_RUN, red.stages().get(ControlCi.Stage.CANONICAL_THIRTY.ordinal()).state());
    }
    @Test void productionInputHasItsOwnStrictContractWithoutInventingAnOriginOrStageConfig() throws Exception {
        var request = pin("original-request.raw"); var payload = pin("original-payload.raw");
        var host = new RootSoftwareFixtureHandoff.Request(List.of(request, payload), List.of(request), request, payload);
        var input = new ControlCi.FixtureProductionRequest(ControlCi.FIXTURE_PRODUCTION_SCHEMA, "fixture-machine",
                Instant.now().plusSeconds(60).toString(), pin("sdk-inputs.json"), host);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(input);
        assertEquals(input, mapper.readValue(raw, ControlCi.FixtureProductionRequest.class));
        assertFalse(raw.contains("origin_ref")); assertFalse(raw.contains("fresh_sdk_config_ref"));
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace("sdk_production_inputs_ref", "unknown_inputs_ref"), ControlCi.FixtureProductionRequest.class));
        assertThrows(IOException.class, () -> mapper.readValue(raw.replace(ControlCi.FIXTURE_PRODUCTION_SCHEMA, "old-production/v0"), ControlCi.FixtureProductionRequest.class));
    }
    private record ProducerInputs(CiBootstrap.Plan plan, FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical) { }
    private ProducerInputs producerInputs() throws IOException {
        Path repo = root.resolve("repository"), work = root.resolve("work");
        Path tools = repo.resolve("java/ck3-control/build-tools"); Files.createDirectories(tools);
        Files.writeString(tools.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion><groupId>fixture</groupId><artifactId>metadata</artifactId><version>1</version></project>");
        Files.createDirectories(work.resolve("artifacts"));
        Path git = root.resolve("git.exe"); Files.writeString(git, "metadata fixture, never executable");
        var ref = pin("metadata.pin"); var golden = goldenPlan();
        Path goldenPath = root.resolve("golden-plan.json"); Files.write(goldenPath, ControlBuild.strictMapper().writeValueAsBytes(golden));
        String machine = WindowsJobProcess.currentMachineId(), review = Instant.now().plusSeconds(300).toString();
        var sourcePins = ControlBuild.sourceManifest(tools).stream().map(value -> new CiBootstrap.FilePin(value.path(), value.bytes(), value.sha256())).toList();
        var plan = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, machine, Instant.now().toString(), review,
                repo.toString(), work.toString(), root.toString(), "mvn", ref.path(), "metadata-fixture",
                sourcePins.getFirst(), java.util.Map.of(), java.util.Map.of(), java.util.Map.of(), sourcePins, sourcePins, false, false);
        String fixtureReview = CiBootstrap.pipelineTiming(plan).workDeadline().toString();
        var clientRef = ControlBuild.FileRef.measure(root.resolve("client.py"));
        var bootstrap = new RootSoftwareChildBootstrap.Configuration(RootSoftwareChildBootstrap.SCHEMA, RootSoftwareChildBootstrap.SCOPE,
                machine, "metadata-only-no-host-qualification", new RootSoftwareChildBootstrap.ServiceProof(ref, ref, clientRef),
                new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32, ref, null),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.java_map_admission_client_v1", clientRef),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.current_saved_continuity_v1", ref),
                new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", ref),
                ref, ref, ref, List.of(ref), List.of());
        var bootstrapRef = RootSoftwareChildBootstrap.writeConfiguration(bootstrap, root.resolve("bootstrap.json"));
        var fresh = new FreshSdkFixtureStage.Config(FreshSdkFixtureStage.SCHEMA, machine, fixtureReview,
                repo.toString(), work.resolve("artifacts/fresh").toString(), ref, ref, ref, ref, ref, ref, List.of(ref),
                List.of(root.resolve("dependencies").toString()), List.of(ref), ref, List.of(), bootstrapRef,
                ControlBuild.FileRef.measure(goldenPath), 64L << 20, 60, 59);
        var canonical = new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, machine, fixtureReview,
                repo.toString(), work.resolve("artifacts/canonical").toString(), ref, ControlBuild.FileRef.measure(git), ref, ref,
                List.of(ref), List.of(root.resolve("dependencies").toString()), List.of(ref), ref,
                CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE, bootstrapRef, 64L << 20, 60);
        return new ProducerInputs(plan, fresh, canonical);
    }
    @Test void actualTypedProducerRoundTripsThroughTheSharedReaderWithOneNestedGoldenPlan() throws Exception {
        var input = producerInputs(); Path output = Path.of(input.plan().workRoot()).resolve("artifacts/request");
        var requestRef = ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output);
        var request = ControlCi.readFixtureRequest(requestRef, input.plan()); var mapper = ControlBuild.strictMapper();
        assertEquals(input.fresh(), mapper.readValue(Files.readAllBytes(Path.of(request.freshSdkConfigRef().path())), FreshSdkFixtureStage.Config.class));
        assertEquals(input.canonical(), mapper.readValue(Files.readAllBytes(Path.of(request.canonicalConfigRef().path())), CanonicalColdWarmStage.Config.class));
        assertFalse(Files.readString(Path.of(requestRef.path())).contains("producer_golden_plan_ref"));
        Path planPath = root.resolve("cli-plan.json"); Files.write(planPath, mapper.writeValueAsBytes(input.plan()));
        Path cliOutput = output.resolveSibling("cli-request"); var freshRef = request.freshSdkConfigRef(); var canonicalRef = request.canonicalConfigRef();
        ControlCi.main(new String[] {"--write-fixture-stage-request", planPath.toString(), "--fresh-sdk-config", freshRef.path(), Long.toString(freshRef.bytes()), freshRef.sha256(),
                "--canonical-config", canonicalRef.path(), Long.toString(canonicalRef.bytes()), canonicalRef.sha256(), "--output-root", cliOutput.toString()});
        var cliRequest = ControlCi.readFixtureRequest(ControlBuild.FileRef.measure(cliOutput.resolve("fixture-stage-request.json")), input.plan());
        assertEquals(freshRef.sha256(), cliRequest.freshSdkConfigRef().sha256());
        assertEquals(canonicalRef.sha256(), cliRequest.canonicalConfigRef().sha256());
        assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output));
        requestRef.verify();
        Files.writeString(Path.of(FreshSdkFixtureStage.readProducerGoldenPlan(input.fresh().producerGoldenPlanRef()).contextInput().path()), "changed actual source");
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(requestRef, input.plan()));
        assertThrows(IOException.class, () -> ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output.resolveSibling("changed")));
        assertFalse(Files.exists(output.resolveSibling("changed")));
    }
    @Test void producerFailureRetainsAlreadyWrittenConfigWithoutPublishingARequest() throws Exception {
        var input = producerInputs(); Path output = root.resolve("partial"); var calls = new java.util.concurrent.atomic.AtomicInteger();
        assertThrows(IOException.class, () -> ControlCi.writeFixtureDocuments(output, input.plan().machineId(), input.fresh().reviewAtUtc(),
                input.fresh(), input.canonical(), () -> { if (calls.incrementAndGet() == 3) throw new IOException("actual resource guard rejection"); }));
        assertTrue(Files.isRegularFile(output.resolve("fresh-sdk-config.json")));
        assertFalse(Files.exists(output.resolve("canonical-config.json"))); assertFalse(Files.exists(output.resolve("fixture-stage-request.json")));
        assertEquals(input.fresh(), ControlBuild.strictMapper().readValue(Files.readAllBytes(output.resolve("fresh-sdk-config.json")), FreshSdkFixtureStage.Config.class));
    }
    @Test void typedProducerCliPinsBothInputsAndRejectsIncompleteOrChangedArguments() throws Exception {
        var plan = pin("producer-plan.json"); var fresh = pin("producer-fresh.json"); var canonical = pin("producer-canonical.json");
        String[] args = {"--write-fixture-stage-request", plan.path(), "--fresh-sdk-config", fresh.path(), Long.toString(fresh.bytes()), fresh.sha256(),
                "--canonical-config", canonical.path(), Long.toString(canonical.bytes()), canonical.sha256(), "--output-root", root.resolve("new-output").toString()};
        var invocation = ControlCi.fixtureWriterInvocation(args); assertEquals(fresh, invocation.freshConfigRef()); assertEquals(canonical, invocation.canonicalConfigRef());
        assertThrows(IllegalArgumentException.class, () -> ControlCi.fixtureWriterInvocation(java.util.Arrays.copyOf(args, 11)));
        var wrong = args.clone(); wrong[4] = "true"; assertThrows(IllegalArgumentException.class, () -> ControlCi.fixtureWriterInvocation(wrong));
        Files.writeString(Path.of(fresh.path()), "changed input"); assertThrows(IOException.class, () -> ControlCi.fixtureWriterInvocation(args));
    }
    @Test void readerRejectsRemovedGoldenPlanAndARequestBeyondTheSharedWorkDeadline() throws Exception {
        var input = producerInputs(); Path output = Path.of(input.plan().workRoot()).resolve("artifacts/request");
        var requestRef = ControlCi.writeFixtureRequest(input.plan(), input.fresh(), input.canonical(), output);
        var request = ControlCi.readFixtureRequest(requestRef, input.plan()); var mapper = ControlBuild.strictMapper();
        var missing = mapper.readTree(Files.readAllBytes(Path.of(request.freshSdkConfigRef().path())));
        assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, missing).remove("producer_golden_plan_ref");
        assertThrows(IOException.class, () -> mapper.treeToValue(missing, FreshSdkFixtureStage.Config.class));
        var late = new ControlCi.FixtureRequest(ControlCi.FIXTURE_REQUEST_SCHEMA, input.plan().machineId(), input.plan().reviewAtUtc(), request.freshSdkConfigRef(), request.canonicalConfigRef());
        Path latePath = root.resolve("late.json"); Files.write(latePath, mapper.writeValueAsBytes(late));
        assertThrows(IOException.class, () -> ControlCi.readFixtureRequest(ControlBuild.FileRef.measure(latePath), input.plan()));
    }
    private ControlCi.RootSoftwareExecutionCard localCard(CiBootstrap.Plan plan, ControlBuild.FileRef ref) {
        return new ControlCi.RootSoftwareExecutionCard(ControlCi.ROOT_CARD_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,
                plan.machineId(), plan.observedAtUtc(), plan.reviewAtUtc(), plan.ownerTask(), "software-slot", ref, ref, ref, ref, ref,
                ControlBuild.SourceLimitProfile.G2_STABILIZATION_20261023);
    }
    @Test void rootLocalCardAndPlanKeepStrictPurposeAndNormalProfileAcrossJson() throws Exception {
        var input = producerInputs(); var ref = pin("local-card-input.json"); var card = localCard(input.plan(), ref);
        var mapper = ControlBuild.strictMapper(); String raw = mapper.writeValueAsString(card);
        assertEquals(card, mapper.readValue(raw, ControlCi.RootSoftwareExecutionCard.class));
        for (String wrong : List.of(raw.replace("ROOT_LOCAL_FULL_SOFTWARE", "HOSTED_CI"),
                raw.replace("G2_STABILIZATION_20261023", "STANDARD_8_MIB"),
                raw.replace("\"slot_id\":\"software-slot\"", "\"slot_id\":true"),
                raw.replace("\"owner_task\":\"" + card.ownerTask() + "\"", "\"owner_task\":\"github-actions-java-ci\""),
                raw.replace(card.reviewAtUtc(), card.observedAtUtc()))) {
            assertNotEquals(raw, wrong); assertThrows(IOException.class, () -> mapper.readValue(wrong, ControlCi.RootSoftwareExecutionCard.class));
        }
        var plan = new ControlCi.RootLocalPlan(ControlCi.ROOT_PLAN_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, ref);
        assertEquals(plan, mapper.readValue(mapper.writeValueAsBytes(plan), ControlCi.RootLocalPlan.class));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.RootLocalPlan(ControlCi.ROOT_PLAN_SCHEMA, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, null));
    }
    @Test void wholeSoftwareDeadlineCannotBorrowTheOrdinary180SecondSlot() throws Exception {
        var input = producerInputs(); var ref = pin("slot-card.json"); var card = localCard(input.plan(), ref);
        var standing = ControlBuild.strictMapper().createObjectNode(); var slot = standing.putArray("slots").addObject();
        slot.put("slot_id", card.slotId()); slot.put("coordinator", card.ownerTask()); slot.put("timeout_seconds", 180); slot.put("output_root", root.toString());
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
        slot.put("timeout_seconds", 2700); ControlCi.requireRootSlot(input.plan(), card, standing);
        slot.put("coordinator", "wrong-owner");
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
        slot.put("coordinator", card.ownerTask());
        slot.put("output_root", root.resolve("another-scope").toString());
        assertThrows(IOException.class, () -> ControlCi.requireRootSlot(input.plan(), card, standing));
    }
    @Test void localActualRequiresFullSdkAndCannotClaimHostedMavenExecution() throws Exception {
        var ref = pin("local-actual.json"); var stages = ControlCi.initialStages();
        for (var stage : ControlCi.Stage.values()) if (stage != ControlCi.Stage.EXPECTED_MAVEN_RED) {
            stages.set(stage.ordinal(), new ControlCi.StageActual(stage, ControlCi.StageState.PASS, ref, null));
        }
        var actual = new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.PASS,
                null, ref, ref, ref, null, ref, ref, List.of(), ref, ref, ref, ref, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, stages);
        assertEquals(actual, ControlBuild.strictMapper().readValue(ControlBuild.strictMapper().writeValueAsBytes(actual), ControlCi.Receipt.class));
        stages.set(ControlCi.Stage.CANONICAL_THIRTY.ordinal(), new ControlCi.StageActual(ControlCi.Stage.CANONICAL_THIRTY, ControlCi.StageState.NOT_RUN, null, null));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.PASS,
                null, ref, ref, ref, null, ref, ref, List.of(), ref, ref, ref, ref, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, stages));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.Receipt(ControlCi.ACTUAL_SCHEMA, "fixture-machine", "a", "b", ControlCi.PipelineState.RED,
                "incomplete", ref, ref, ref, null, ref, ref, List.of(), ref, ref, null, null, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE, ref, stages));
    }

    private FreshSdkFixtureStage.ProducerGoldenPlan goldenPlan() throws IOException {
        var mapper = ControlBuild.strictMapper(); var refs = new java.util.ArrayList<ControlBuild.FileRef>();
        for (int index = 0; index < 19; index++) {
            Path file = root.resolve("golden-" + index + ".raw"); Files.writeString(file, "original producer bytes " + index); refs.add(ControlBuild.FileRef.measure(file));
        }
        Path client = root.resolve("client.py"), test = root.resolve("client-test.py"); Files.writeString(client, "exact client"); Files.writeString(test, "exact test");
        var clientRef = ControlBuild.FileRef.measure(client); var testRef = ControlBuild.FileRef.measure(test);
        var origin = mapper.createObjectNode();
        for (String field : List.of("observed_at_utc", "status", "existing_setup_spec_ref", "setup_source_field", "framework", "golden_install", "actual_config_seam", "authority")) origin.put(field, "synthetic original handoff");
        origin.put("schema", "xar.existing-python-producer-golden-install-map/v1"); origin.put("machine_id", WindowsJobProcess.currentMachineId());
        origin.put("observed_at_utc", Instant.now().toString()); origin.set("existing_setup_spec_ref", mapper.valueToTree(clientRef));
        origin.put("status", "EXACT_EXISTING_SETUP_HANDOFF_NO_NEW_RUNNER");
        origin.put("logical_module", "tools.g2_saved_campaign.test_java_projection_client_v1"); origin.set("test_module_ref", mapper.valueToTree(testRef));
        var classes = origin.putObject("classes"); classes.put("ProjectionClientContractTests", 49); classes.put("ProjectionClientG2ProducerGoldenTests", 4); classes.put("ProjectionClientActualJavaTests", 2);
        var rows = origin.putArray("roles"); var roles = new java.util.ArrayList<>(List.of("context_input", "context_result", "evaluate_request"));
        var vectors = new java.util.ArrayList<FreshSdkFixtureStage.ProducerGoldenVector>();
        for (var milestone : FreshSdkFixtureStage.GoldenMilestone.values()) {
            roles.add("G2-" + milestone.name() + ".request"); roles.add("G2-" + milestone.name() + ".result");
            int index = milestone.ordinal() * 2 + 3; vectors.add(new FreshSdkFixtureStage.ProducerGoldenVector(milestone, refs.get(index), refs.get(index + 1)));
        }
        for (int index = 0; index < roles.size(); index++) { var row = rows.addObject(); row.put("role", roles.get(index)); row.set("ref", mapper.valueToTree(refs.get(index))); }
        Path originPath = root.resolve("original-install-map.json"); Files.write(originPath, mapper.writeValueAsBytes(origin));
        return new FreshSdkFixtureStage.ProducerGoldenPlan("xar.sdk-producer-golden-plan/v1", WindowsJobProcess.currentMachineId(), ControlBuild.FileRef.measure(originPath),
                new SdkSourceAssembly.Digest(clientRef.bytes(), clientRef.sha256()), new SdkSourceAssembly.Digest(testRef.bytes(), testRef.sha256()), refs.get(0), refs.get(1), refs.get(2), vectors);
    }
}
