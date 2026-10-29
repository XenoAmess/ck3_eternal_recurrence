package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class ControlCiPlannedFixtureProductionTest {
    @TempDir Path root;

    private FileRef pin(String name) throws IOException {
        Path path = root.resolve(name); Files.writeString(path, "synthetic source metadata, never a qualified build");
        return FileRef.measure(path);
    }

    private ControlCi.PlannedFixtureProductionRequest request() throws IOException {
        var source = pin("sdk-plan.json"); var fixture = pin("original-request.json"); var payload = pin("probe-payload.json");
        var host = new RootSoftwareFixtureHandoff.Request(List.of(fixture), List.of(fixture), fixture, payload);
        return new ControlCi.PlannedFixtureProductionRequest(ControlCi.PLANNED_FIXTURE_PRODUCTION_SCHEMA, "fixture-machine",
                Instant.now().plusSeconds(300).toString(), source, host, pin("current-inputs.json"));
    }

    @Test void plannedContractPreservesOriginalTypedInputsAndHasNoFutureBuildAcrossJson() throws Exception {
        var request = request(); var mapper = ControlBuild.strictMapper(); byte[] bytes = mapper.writeValueAsBytes(request);
        assertEquals(request, ControlCi.decodePlannedFixtureProductionRequest(bytes));
        var node = (ObjectNode) mapper.readTree(bytes);
        assertEquals(6, node.size()); assertFalse(node.has("qualified_tools_build_ref")); assertFalse(node.has("sdk_production_inputs_ref"));
        var malformed = new ArrayList<ObjectNode>();
        for (String field : List.of("sdk_production_plan_ref", "software_fixture", "current_oracle_inputs_ref")) {
            var missing = node.deepCopy(); missing.remove(field); malformed.add(missing);
            var nil = node.deepCopy(); nil.putNull(field); malformed.add(nil);
        }
        for (String field : List.of("qualified_tools_build_ref", "sdk_production_inputs_ref")) {
            var future = node.deepCopy(); future.set(field, mapper.valueToTree(request.sdkProductionPlanRef())); malformed.add(future);
        }
        var wrongSchema = node.deepCopy(); wrongSchema.put("schema", ControlCi.CURRENT_FIXTURE_PRODUCTION_SCHEMA); malformed.add(wrongSchema);
        var bool = node.deepCopy(); ((ObjectNode) bool.get("sdk_production_plan_ref")).put("bytes", true); malformed.add(bool);
        var floating = node.deepCopy(); ((ObjectNode) floating.get("current_oracle_inputs_ref")).put("bytes", 1.0); malformed.add(floating);
        for (var bad : malformed) assertThrows(IOException.class, () -> ControlCi.decodePlannedFixtureProductionRequest(mapper.writeValueAsBytes(bad)));
        assertThrows(IOException.class, () -> mapper.readValue(bytes, ControlCi.CurrentFixtureProductionRequest.class));
    }

    private List<String> bootstrapArguments(FileRef planned) {
        return List.of("--repo-root", root.toString(), "--work-root", root.resolve("work").toString(),
                "--python-executable", root.resolve("python.exe").toString(), "--system-growth-reserve-bytes", "1",
                "--max-project-bytes", "8589934592", "--planned-fixture-production-request", planned.path(),
                "--planned-fixture-production-request-bytes", Long.toString(planned.bytes()),
                "--planned-fixture-production-request-sha256", planned.sha256());
    }

    @Test void bootstrapAndQualifiedChildForwardOnlyTheSameExactPlannedRequest() throws Exception {
        var source = pin("planned.json"); var plan = pin("resource-plan.json"); var completed = pin("actual-tools-path.json");
        var values = CiBootstrap.arguments(bootstrapArguments(source).toArray(String[]::new));
        assertNull(CiBootstrap.fixtureProductionPin(values));
        var bootstrap = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        CiBootstrap.appendPlannedFixtureProduction(bootstrap, CiBootstrap.plannedFixtureProductionPin(values));
        var first = ControlCi.invocation(bootstrap.toArray(String[]::new));
        assertEquals(source, first.plannedFixtureProductionRequestRef());
        assertNull(first.fixtureProductionRequestRef()); assertNull(first.fixtureRequestRef()); assertNull(first.toolsReceiptPath());
        var child = new ArrayList<>(List.of("--bootstrap-plan", plan.path(), "--qualified-tools-receipt", completed.path()));
        ControlCi.forwardFixtureRequests(child, null, null, first.plannedFixtureProductionRequestRef());
        var second = ControlCi.invocation(child.toArray(String[]::new));
        assertEquals(source, second.plannedFixtureProductionRequestRef()); assertEquals(Path.of(completed.path()), second.toolsReceiptPath());
        assertNull(second.fixtureProductionRequestRef()); assertNull(second.fixtureRequestRef());
    }

    @Test void sourcePlanCannotMixWithCompletedRoutesOrEnterTheMavenOnlyEntry() throws Exception {
        var source = pin("mixed.json"); var plan = pin("mixed-resource-plan.json");
        var args = new ArrayList<>(bootstrapArguments(source));
        args.set(10, "--fixture-production-request");
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.arguments(args.toArray(String[]::new)));
        var mavenOnly = new ArrayList<>(List.of("--ensure-default-maven-only")); mavenOnly.addAll(bootstrapArguments(source));
        assertThrows(IllegalArgumentException.class, () -> CiBootstrap.invocation(mavenOnly.toArray(String[]::new)));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), source, null, source));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), null, source, source));
        var pipeline = new ArrayList<>(List.of("--bootstrap-plan", plan.path()));
        ControlCi.forwardFixtureRequests(pipeline, null, null, source);
        pipeline.addAll(List.of("--fixture-production-request", source.path(), Long.toString(source.bytes()), source.sha256()));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.invocation(pipeline.toArray(String[]::new)));
    }

    @Test void eitherForwardingBoundaryRejectsChangedOriginalPins() throws Exception {
        var source = pin("changed.json");
        var values = CiBootstrap.arguments(bootstrapArguments(source).toArray(String[]::new));
        var original = CiBootstrap.plannedFixtureProductionPin(values);
        Files.writeString(Path.of(source.path()), "changed original source plan");
        assertThrows(IOException.class, () -> CiBootstrap.appendPlannedFixtureProduction(new ArrayList<>(), original));
        assertThrows(IOException.class, () -> ControlCi.forwardFixtureRequests(new ArrayList<>(), null, null, source));
        assertThrows(IOException.class, () -> CiBootstrap.plannedFixtureProductionPin(values));
    }

    @Test void selectedCurrentOraclePinIsBoundBeforeTheQualifiedChildReadsItsEnvironment() throws Exception {
        var selected = pin("selected-current-inputs.json");
        var environment = new java.util.TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.put("XAR_ORACLE_REPO", root.toString()); environment.put("XAR_FULL_PARITY_CURRENT_INPUTS", "stale");
        ControlCi.bindCurrentOracleEnvironment(environment, selected);
        assertEquals(selected.path(), environment.get("XAR_FULL_PARITY_CURRENT_INPUTS"));
        assertEquals(selected.sha256(), environment.get("XAR_FULL_PARITY_CURRENT_INPUTS_SHA256"));
        assertEquals(root.toString(), environment.get("XAR_ORACLE_REPO"));
        Files.writeString(Path.of(selected.path()), "changed selected original");
        assertThrows(IOException.class, () -> ControlCi.bindCurrentOracleEnvironment(environment, selected));
        // This mechanical forwarding check does not treat synthetic metadata as actual oracle inputs.
    }

    @Test void actualWriterCliCallsTheStrictSdkSourcePlanReaderBeforePublishing() throws Exception {
        var request = request(); var hostPath = root.resolve("software-inputs.json");
        Files.write(hostPath, ControlBuild.strictMapper().writeValueAsBytes(request.softwareFixture())); var host = FileRef.measure(hostPath);
        Path output = root.resolve("not-written.json");
        String[] arguments = {"--write-planned-fixture-production-request", request.sdkProductionPlanRef().path(),
                Long.toString(request.sdkProductionPlanRef().bytes()), request.sdkProductionPlanRef().sha256(),
                "--software-fixture-inputs", host.path(), Long.toString(host.bytes()), host.sha256(),
                "--current-oracle-inputs", request.currentOracleInputsRef().path(),
                Long.toString(request.currentOracleInputsRef().bytes()), request.currentOracleInputsRef().sha256(), "--output", output.toString()};
        assertThrows(IOException.class, () -> ControlCi.main(arguments)); assertFalse(Files.exists(output));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.main(java.util.Arrays.copyOf(arguments, 13)));
        assertThrows(IOException.class, () -> ControlCi.writePlannedFixtureProductionRequest(request, output)); assertFalse(Files.exists(output));
    }

    @Test void bindingEvidenceKeepsTheActualCompletedReceiptAndOriginalRequestDistinct() throws Exception {
        var planned = pin("binding-plan.json"); var tools = pin("actual-completed-receipt.json");
        var sdk = pin("bound-sdk-v3.json"); var production = pin("bound-current-request.json");
        var binding = new ControlCi.PlannedFixtureBinding("xar.java-control-CI-planned-fixture-binding/v1", "fixture-machine", planned, tools, sdk, production);
        var mapper = ControlBuild.strictMapper();
        assertEquals(binding, mapper.readValue(mapper.writeValueAsBytes(binding), ControlCi.PlannedFixtureBinding.class));
        assertThrows(IllegalArgumentException.class, () -> new ControlCi.PlannedFixtureBinding(binding.schema(), binding.machineId(), planned, null, sdk, production));
        // These are shape-only test pins. No constructor or JSON roundtrip grants completed-build authority.
    }
    private String[] localBinderArguments(FileRef card, FileRef planned) {
        return new String[] {"--bind-root-local-planned-fixture-production", card.path(),
                Long.toString(card.bytes()), card.sha256(), "--planned-fixture-production-request",
                planned.path(), Long.toString(planned.bytes()), planned.sha256()};
    }

    @Test void rootLocalBinderSelectsTwoExactOriginalPinsWithoutAnArbitraryOutput() throws Exception {
        var card = pin("root-card.json"); var planned = pin("local-planned.json");
        var args = localBinderArguments(card, planned);
        var invocation = ControlCi.rootLocalBinderInvocation(args);
        assertEquals(card, invocation.cardRef()); assertEquals(planned, invocation.plannedRef());
        var outputOverride = java.util.Arrays.copyOf(args, 10);
        outputOverride[8] = "--output-root"; outputOverride[9] = root.resolve("elsewhere").toString();
        assertThrows(IllegalArgumentException.class, () -> ControlCi.rootLocalBinderInvocation(outputOverride));
    }

    @Test void rootLocalBinderRejectsMissingMixedOrChangedCliInputsBeforePublication() throws Exception {
        var card = pin("exact-root-card.json"); var planned = pin("exact-local-planned.json");
        var args = localBinderArguments(card, planned);
        assertThrows(IllegalArgumentException.class, () -> ControlCi.rootLocalBinderInvocation(java.util.Arrays.copyOf(args, 7)));
        var mixed = args.clone(); mixed[4] = "--fixture-production-request";
        assertThrows(IllegalArgumentException.class, () -> ControlCi.rootLocalBinderInvocation(mixed));
        var wrongBytes = args.clone(); wrongBytes[2] = Long.toString(card.bytes() + 1);
        assertThrows(IOException.class, () -> ControlCi.rootLocalBinderInvocation(wrongBytes));
        var wrongHash = args.clone(); wrongHash[7] = "0".repeat(64);
        assertThrows(IOException.class, () -> ControlCi.rootLocalBinderInvocation(wrongHash));
        var wrongType = args.clone(); wrongType[2] = "true";
        assertThrows(IllegalArgumentException.class, () -> ControlCi.rootLocalBinderInvocation(wrongType));
        Files.writeString(Path.of(planned.path()), "changed original planned request");
        assertThrows(IOException.class, () -> ControlCi.rootLocalBinderInvocation(args));
        assertFalse(Files.exists(root.resolve("artifacts")));
    }

    @Test void rootLocalBinderCliRejectsLegacyOrUnbackedCardsWithoutPublishingAnything() throws Exception {
        var original = pin("unqualified-card-input.json"); var planned = pin("unqualified-planned.json");
        for (String schema : List.of(ControlCi.ROOT_CARD_SCHEMA, ControlCi.POSTQUALIFIED_ROOT_CARD_SCHEMA)) {
            var card = new ControlCi.RootSoftwareExecutionCard(schema, ControlCi.ExecutionPurpose.ROOT_LOCAL_FULL_SOFTWARE,
                    "fixture-machine", "2026-10-26T20:00:00Z", "2026-10-26T23:30:00Z", "/root/sdk_current", "sdk-local",
                    original, original, original, original, original, ControlBuild.SourceLimitProfile.G2_FULL_PARITY_20261025_R7,
                    ControlCi.POSTQUALIFIED_ROOT_CARD_SCHEMA.equals(schema) ? original : null);
            var path = root.resolve("unqualified-root-card.json");
            Files.write(path, ControlBuild.strictMapper().writeValueAsBytes(card));
            assertThrows(IOException.class, () -> ControlCi.main(localBinderArguments(FileRef.measure(path), planned)));
            assertFalse(Files.exists(root.resolve("artifacts")));
            assertFalse(Files.exists(root.resolve("sdk-production-inputs.json")));
            assertFalse(Files.exists(root.resolve("fixture-production-request.json")));
        }
    }

    @Test void rootLocalBindingWindowUsesTheEarliestOriginalDeadlineBeforeAnyWrite() throws Exception {
        var now = Instant.parse("2026-10-26T20:00:00Z");
        var exact = now.plusSeconds(900); var below = exact.minusNanos(1);
        ControlCi.requireRootLocalBindingWindow(now, exact, exact, exact);
        assertThrows(IOException.class, () -> ControlCi.requireRootLocalBindingWindow(now, below, exact, exact));
        assertThrows(IOException.class, () -> ControlCi.requireRootLocalBindingWindow(now, exact, below, exact));
        assertThrows(IOException.class, () -> ControlCi.requireRootLocalBindingWindow(now, exact, exact, below));
        assertThrows(IOException.class, () -> ControlCi.requireRootLocalBindingWindow(now, now, exact, exact));
        assertFalse(Files.exists(root.resolve("artifacts")));
    }


}
