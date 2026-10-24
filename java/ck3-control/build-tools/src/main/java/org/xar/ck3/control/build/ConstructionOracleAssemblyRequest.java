package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Data-only construction reference-input assembly request.
 * Emits exact source-adoption intents and finite argument roles. It does not
 * adopt files, invoke Python, qualify a main, start a host, or execute a capture.
 * The SDK source composer and the shared compiled producer own those steps.
 */
public final class ConstructionOracleAssemblyRequest {
    private static final String SCHEMA = "xar.construction-oracle-assembly-request/v1";
    private static final String PLAN_SCHEMA = "xar.construction-oracle-assembly-plan/v1";
    private static final String CLIENT_SHA =
            "33eb88d51196532184527eba0812333b33372eea4b071ce115a59004feb00380";
    private static final String CLIENT_TARGET =
            "tools/g2_saved_campaign/java_map_admission_client_v1.py";
    private static final String UNIT = "ck3_autonomous_player/tests/unit/";
    private static final String FIXTURES =
            "ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/";
    private static final String W2 =
            "org.xar.ck3.control.wave2.development.";
    private static final String W3 =
            "org.xar.ck3.control.wave3.development.";

    public enum ProducerRole { REFERENCE_ORACLE }
    public enum ClientRole { ROOT_SELECTED_CONSUMER_155 }
    public enum Boundary { SOURCE_PLAN_ONLY }
    public enum ArgumentRole {
        PRODUCER_MODE, MACHINE_ID, REPOSITORY, INTERPRETER,
        EXISTING_ORACLE_UNIT_DIRECTORY, ACCEPTED_STANDARD_BATCH_FILE,
        CAPTURE_ID, NEW_OUTPUT
    }
    public enum RequiredStep {
        CANONICAL_REFERENCE_INPUT_ADOPTION,
        CURRENT_CONSTRUCTION_ADAPTER_ADOPTION,
        QUALIFIED_EXISTING_DIRECTORY_ARGUMENT,
        SELECTED_MAIN_AND_MODULE_PROVENANCE,
        FRESH_RUNTIME_CLAIM,
        ACTUAL_REFERENCE_CAPTURE,
        ACTUAL_RESOURCE_CONSUMER
    }
    public enum Leaf {
        INCOME("income", "constructionincome/golden.json", 32768, 45, 22),
        PROVINCE("province", "constructionincome/province-golden.json", 32768, 45, 20),
        READBACK("readback", "constructionreadback/golden.json", 65536, 45, 22),
        SCENE("scene", "constructionscene/original-producer-golden-v1.json", 90000, 100, 64),
        QUERY("query", "constructionquery/original-producer-golden-v1.json.gz", 40000, 100, 38);

        private final String mode;
        private final String resource;
        private final long maxBytes;
        private final int timeoutSeconds;
        private final int cases;
        Leaf(String mode, String resource, long maxBytes, int timeoutSeconds, int cases) {
            this.mode = mode;
            this.resource = resource;
            this.maxBytes = maxBytes;
            this.timeoutSeconds = timeoutSeconds;
            this.cases = cases;
        }
    }

    public record ReferenceSource(ControlBuild.FileRef sourceRef, String repositoryTarget,
            ProducerRole producerRole) {
        public ReferenceSource {
            Objects.requireNonNull(sourceRef);
            require(producerRole == ProducerRole.REFERENCE_ORACLE, "Exact reference producer role required");
            relative(repositoryTarget);
            String expected = switch (repositoryTarget) {
                case UNIT + "construction_python_oracle_v1.py" -> "25679:f159d71fdf3086bf75300208ab63fc7bdedc1fea1eeb6a63fcb4a553f37e0d8f";
                case UNIT + "construction_java_fixture_v1.py" -> "6935:cb5fb5d38d978da992721227afc9a528e2137515db02e66b8a5d5cddd5192731";
                case FIXTURES + "source-pins.json" -> "3532:c97fca5b750fae654325d3bdadb809fe6e610921d4dbe7d7822ed0691257e4c8";
                case FIXTURES + "construction_formal_consumer.py.txt" -> "40508:90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e";
                case FIXTURES + "domain_construction_private_transport_v1.py.txt" -> "66026:c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e";
                case FIXTURES + "m5-construction-cash-enrichment.py.txt" -> "615:5f9dbd4cefa9b15fd97b6e0275b62099b2b846a27408f99e050610b6071130e4";
                case FIXTURES + "construction-original-data-fixtures.py.txt" -> "20014:aba97265f08a8b75437858189b7fca48e5372fa9df1d5c80252d1c459c39e79f";
                case FIXTURES + "construction-original-cash-setup.py.txt" -> "1593:1f0989d17ee20d29f5e1c92639855db3d3d855b70e82c688be4fbaac12f6fe84";
                default -> throw new IllegalArgumentException("Unlisted original target");
            };
            require(expected.equals(sourceRef.bytes() + ":" + sourceRef.sha256()),
                    "Only the unchanged previously audited original can occupy this target");
            require(!repositoryTarget.equals(CLIENT_TARGET), "Reference originals cannot replace the common client");
        }
    }

    public record SelectedClient(ControlBuild.FileRef sourceRef, String logicalModule,
            ClientRole clientRole) {
        public SelectedClient {
            Objects.requireNonNull(sourceRef);
            require(sourceRef.bytes() == 201217 && sourceRef.sha256().equals(CLIENT_SHA),
                    "Root-selected 155-op client 33eb is required; historical clients are not substitutes");
            require("tools.g2_saved_campaign.java_map_admission_client_v1".equals(logicalModule),
                    "Single canonical client module required");
            require(clientRole == ClientRole.ROOT_SELECTED_CONSUMER_155, "Exact current consumer role required");
        }
    }

    /** Existing domain-owner request, not an implementation copied from old clients. */
    public record AdapterRequest(String soleOwner, List<String> requiredTypes,
            String bindSignature, String exchangeSignature, String successBytes,
            String domainException, List<String> commonImports,
            List<ControlBuild.FileRef> historicalCandidateRefs) {
        public AdapterRequest {
            require("/root/g2_m4_java".equals(soleOwner), "Construction adapter has one domain owner");
            requiredTypes = List.copyOf(requiredTypes);
            require(requiredTypes.equals(List.of("ConstructionProjectionExchangeV1",
                    "ConstructionProjectionOperationV1", "ConstructionProjectionContractV1",
                    "ConstructionProjectionPortV1", "ConstructionProjectionInputRejectedV1")),
                    "Complete typed construction adapter boundary required");
            require("bind_construction_java_port_v1(driver: object, exchange) -> None".equals(bindSignature),
                    "Exact binding ABI required");
            require("(operation: str, request_utf8: bytes, request_id: str) -> bytes; positional".equals(exchangeSignature),
                    "Three positional argument exchange ABI required");
            require("issued/context-validated ProjectionResult.result_bytes".equals(successBytes),
                    "Shared validated result bytes required");
            require("ProjectionDomainRejected".equals(domainException), "Shared typed domain exception required");
            commonImports = List.copyOf(commonImports);
            require(commonImports.equals(List.of("JavaProjectionServiceV1", "ProjectionOperation",
                    "ProjectionResult", "ProjectionUnavailable", "bind_projection_config_v1",
                    "call_projection_v1", "qualify_projection_service_v1",
                    "require_current_projection_config_v1", "require_result_context_v1")),
                    "Complete existing common fixture ABI required");
            historicalCandidateRefs = List.copyOf(historicalCandidateRefs);
            require(historicalCandidateRefs.size() == 2, "PORT02 and ERROR04 source references required");
        }
    }

    public record Request(String schema, String machineId, ControlBuild.FileRef sourceWindowRef,
            ControlBuild.FileRef originalAuditRef, ControlBuild.FileRef separationAuditRef,
            ControlBuild.FileRef captureReceiptRef, ControlBuild.FileRef testCompilationRef,
            SelectedClient selectedClient, List<ReferenceSource> referenceSources,
            ControlBuild.FileRef standardJavaSourceRef, ControlBuild.FileRef sceneJavaSourceRef,
            ControlBuild.FileRef queryJavaSourceRef, AdapterRequest adapterRequest) {
        public Request {
            require(SCHEMA.equals(schema), "Exact assembly schema required");
            require(machineId != null && !machineId.isBlank(), "Explicit machine identity required");
            Objects.requireNonNull(sourceWindowRef);
            Objects.requireNonNull(originalAuditRef);
            Objects.requireNonNull(separationAuditRef);
            Objects.requireNonNull(captureReceiptRef);
            Objects.requireNonNull(testCompilationRef);
            Objects.requireNonNull(selectedClient);
            Objects.requireNonNull(standardJavaSourceRef);
            Objects.requireNonNull(sceneJavaSourceRef);
            Objects.requireNonNull(queryJavaSourceRef);
            Objects.requireNonNull(adapterRequest);
            referenceSources = List.copyOf(referenceSources);
            require(referenceSources.size() == 8, "Exactly the eight previously audited reference originals required");
            Set<String> targets = new HashSet<>();
            for (ReferenceSource source : referenceSources) {
                require(targets.add(source.repositoryTarget()), "Duplicate reference source target");
            }
            require(targets.equals(Set.of(UNIT + "construction_python_oracle_v1.py",
                    UNIT + "construction_java_fixture_v1.py", FIXTURES + "source-pins.json",
                    FIXTURES + "construction_formal_consumer.py.txt",
                    FIXTURES + "domain_construction_private_transport_v1.py.txt",
                    FIXTURES + "m5-construction-cash-enrichment.py.txt",
                    FIXTURES + "construction-original-data-fixtures.py.txt",
                    FIXTURES + "construction-original-cash-setup.py.txt")),
                    "Finite original-oracle source target set required");
            require(standardJavaSourceRef.bytes() == 22360 && standardJavaSourceRef.sha256().equals(
                    "40a4e4ba9ce5a2d035ed2b5267b15ddc2814b088b8a43e044f8854e75bffb56b"),
                    "Unchanged genuine05 Standard02 source required");
            require(sceneJavaSourceRef.bytes() == 18383 && sceneJavaSourceRef.sha256().equals(
                    "64528200e8e90a948c24259cd03f75767c7e6a17ec03ccf55753444f059ebafe"),
                    "Unchanged genuine05 Scene source required");
            require(queryJavaSourceRef.bytes() == 16812 && queryJavaSourceRef.sha256().equals(
                    "cef69805f34d775466f33114be300b6cb855d46eaa8c8a940a1034eaa4456a80"),
                    "Unchanged genuine05 Query source required");
        }
    }

    public record CaptureRecipe(Leaf leaf, String mainClass, ControlBuild.FileRef javaSourceRef,
            String producerMode, List<ArgumentRole> argumentRoles, String resourceRelativePath,
            long outputMaxBytes, int innerTimeoutSeconds, int expectedCases,
            int expectedAdditionalTimeCases, List<String> originalConsumerClasses,
            List<String> requiredInputRelativePaths, List<String> requiredOriginalSourceTargets) {
        public CaptureRecipe {
            Objects.requireNonNull(leaf);
            argumentRoles = List.copyOf(argumentRoles);
            originalConsumerClasses = List.copyOf(originalConsumerClasses);
            requiredInputRelativePaths = List.copyOf(requiredInputRelativePaths);
            requiredOriginalSourceTargets = List.copyOf(requiredOriginalSourceTargets);
        }
    }

    public record StandardRequestContract(String schema, List<String> captureRowFields,
            int exactJavaSourceFilenameCount, boolean commandTailEightEqualsMainArguments,
            String oracleDirectoryRelativePath, List<String> requiredInputRelativePaths) {
        public StandardRequestContract {
            captureRowFields = List.copyOf(captureRowFields);
            requiredInputRelativePaths = List.copyOf(requiredInputRelativePaths);
        }
    }

    public record Plan(String schema, String machineId, Boundary boundary,
            ControlBuild.FileRef assemblyRequestRef, Request sourceIntent,
            List<CaptureRecipe> captures, StandardRequestContract standardRequestContract,
            List<RequiredStep> remainingSteps, boolean captureExecuted,
            boolean javaProjectionExecuted, boolean runtimeQualificationGranted) {
        public Plan {
            require(PLAN_SCHEMA.equals(schema), "Exact plan schema required");
            require(boundary == Boundary.SOURCE_PLAN_ONLY, "An assembly request cannot grant runtime qualification");
            require(!captureExecuted && !javaProjectionExecuted && !runtimeQualificationGranted,
                    "Source assembly cannot claim execution or qualification");
            Objects.requireNonNull(assemblyRequestRef);
            Objects.requireNonNull(sourceIntent);
            Objects.requireNonNull(standardRequestContract);
            captures = List.copyOf(captures);
            remainingSteps = List.copyOf(remainingSteps);
        }
    }

    public static Plan assemble(Request request, ControlBuild.FileRef requestRef) {
        Objects.requireNonNull(request);
        Objects.requireNonNull(requestRef);
        List<CaptureRecipe> recipes = new ArrayList<>();
        for (Leaf leaf : Leaf.values()) {
            boolean standard = leaf == Leaf.INCOME || leaf == Leaf.PROVINCE || leaf == Leaf.READBACK;
            List<ArgumentRole> arguments = standard
                    ? List.of(ArgumentRole.PRODUCER_MODE, ArgumentRole.MACHINE_ID,
                            ArgumentRole.REPOSITORY, ArgumentRole.INTERPRETER,
                            ArgumentRole.EXISTING_ORACLE_UNIT_DIRECTORY,
                            ArgumentRole.ACCEPTED_STANDARD_BATCH_FILE,
                            ArgumentRole.CAPTURE_ID, ArgumentRole.NEW_OUTPUT)
                    : List.of(ArgumentRole.REPOSITORY, ArgumentRole.INTERPRETER, ArgumentRole.NEW_OUTPUT);
            String mainClass = standard ? W2 + "constructionincome.ConstructionStandardGoldenCapture02"
                    : leaf == Leaf.SCENE ? W2 + "constructionscene.ConstructionSceneGoldenCapture"
                    : W3 + "constructionquery.ConstructionQueryGoldenCapture";
            ControlBuild.FileRef source = standard ? request.standardJavaSourceRef()
                    : leaf == Leaf.SCENE ? request.sceneJavaSourceRef() : request.queryJavaSourceRef();
            List<String> consumers = switch (leaf) {
                case INCOME -> List.of("ConstructionIncomeTest", "ConstructionProjectionCatalogTest");
                case PROVINCE -> List.of("ConstructionProvinceIncomeTest");
                case READBACK -> List.of("ConstructionReceiptReadbackTest", "ConstructionProjectionCatalogTest");
                case SCENE -> List.of("ConstructionScenePolicyTest");
                case QUERY -> List.of("ConstructionQueryCodecTest");
            };
            List<String> inputs = requiredInputRelativePaths(leaf);
            List<String> originalTargets = request.referenceSources().stream()
                    .map(ReferenceSource::repositoryTarget)
                    .filter(target -> !target.endsWith("construction-original-cash-setup.py.txt"))
                    .filter(target -> !standard || !target.endsWith("construction-original-data-fixtures.py.txt"))
                    .toList();
            recipes.add(new CaptureRecipe(leaf, mainClass, source, leaf.mode, arguments,
                    leaf.resource, leaf.maxBytes, leaf.timeoutSeconds, leaf.cases,
                    leaf == Leaf.READBACK ? 9 : 0, consumers, inputs, originalTargets));
        }
        StandardRequestContract standard = new StandardRequestContract(
                "xar.shared-golden-capture-batch/v1",
                List.of("id", "command", "cwd", "source_refs", "input_refs", "output_path", "max_output_bytes"),
                1, true, "ck3_autonomous_player/tests/unit",
                List.of("java/ck3-control/wave2-development/src/test/resources/constructionincome/golden-inputs.json",
                        "java/ck3-control/wave2-development/src/test/resources/constructionincome/province-golden-inputs.json",
                        "java/ck3-control/wave2-development/src/test/resources/constructionreadback/golden-inputs.json",
                        "tools/g2_saved_campaign/fixtures/construction_cold_readback_p02_0011_minimal.json"));
        return new Plan(PLAN_SCHEMA, request.machineId(), Boundary.SOURCE_PLAN_ONLY, requestRef,
                request, recipes, standard, List.of(RequiredStep.values()), false, false, false);
    }


    /** Finite raw inputs for one leaf; these paths are not a list of importable modules. */
    public static List<String> requiredInputRelativePaths(Leaf leaf) {
        Objects.requireNonNull(leaf);
        String resources = "java/ck3-control/wave2-development/src/test/resources/";
        return switch (leaf) {
            case INCOME -> List.of(resources + "constructionincome/golden-inputs.json");
            case PROVINCE -> List.of(resources + "constructionincome/province-golden-inputs.json");
            case READBACK -> List.of(resources + "constructionreadback/golden-inputs.json",
                    "tools/g2_saved_campaign/fixtures/construction_cold_readback_p02_0011_minimal.json");
            case SCENE -> List.of(UNIT + "test_construction_formal_private_consumer.py",
                    UNIT + "test_construction_monthly_budget_v1.py",
                    UNIT + "test_clan_construction_scope_cash_compound_v1.py");
            case QUERY -> List.of(UNIT + "test_construction_formal_private_consumer.py",
                    UNIT + "fixtures/construction_material_outside_projection.json");
        };
    }

    public record CaptureInputs(String schema, Leaf leaf, ControlBuild.FileRef referenceActualRef,
            List<ControlBuild.FileRef> inputRefs, boolean runtimeQualificationGranted) {
        public CaptureInputs {
            require("xar.construction-capture-inputs/v1".equals(schema), "Exact capture input metadata required");
            Objects.requireNonNull(leaf); Objects.requireNonNull(referenceActualRef);
            inputRefs = List.copyOf(inputRefs);
            require(!runtimeQualificationGranted, "Source input custody cannot grant runtime qualification");
        }
    }

    /** The complete SDK reader remains authoritative. Standard3 does not qualify Scene/Query. */
    public static CaptureInputs requireCaptureInputs(ControlBuild.FileRef referenceActualRef, Leaf leaf) throws IOException {
        var actual = SdkSourceAssembly.readReferenceActual(referenceActualRef);
        require(actual.purpose() == SdkSourceAssembly.ReferencePurpose.REFERENCE_ORACLE_ONLY,
                "Construction capture inputs require the explicit original-producer reference");
        List<ControlBuild.FileRef> inputs = selectCaptureInputRefs(leaf, Path.of(actual.graphRoot()),
                actual.actualSourceClosure(), actual.selectedImportRoutes());
        referenceActualRef.verify();
        return new CaptureInputs("xar.construction-capture-inputs/v1", leaf, referenceActualRef, inputs, false);
    }

    static List<ControlBuild.FileRef> selectCaptureInputRefs(Leaf leaf, Path graphRoot,
            List<SdkSourceAssembly.OutputSource> sources,
            List<SdkSourceAssembly.SelectedImportRoute> routes) throws IOException {
        Path graph = graphRoot.toAbsolutePath().normalize();
        List<ControlBuild.FileRef> result = new ArrayList<>();
        for (String relative : requiredInputRelativePaths(leaf)) {
            var matches = sources.stream().filter(source -> source.relativePath().equals(relative)).toList();
            require(matches.size() == 1, "Required original leaf input absent or duplicated: " + relative);
            var selected = matches.getFirst(); var ref = selected.actual();
            require(Path.of(ref.path()).toAbsolutePath().normalize().equals(graph.resolve(relative)),
                    "Leaf input must occupy its exact physical reference path");
            if (relative.endsWith(".py")) {
                String expected = switch (relative) {
                    case UNIT + "test_construction_formal_private_consumer.py" ->
                            "105470:7a6e579551ac71e5cad3f7522dd454d1ddb884932d26293aed5d68b2d731dffb";
                    case UNIT + "test_construction_monthly_budget_v1.py" ->
                            "12358:bdd2ca9a328a6b534ede68e5de773cf73e0d6764bc2a7fa217d8746b93182933";
                    case UNIT + "test_clan_construction_scope_cash_compound_v1.py" ->
                            "8183:4f8dcaa3039877c347dd548f3dadc6499839bf5feb4822e0ecf7a4140e143edb";
                    default -> throw new IllegalArgumentException("Unlisted original capture test");
                };
                require(selected.role() == SdkSourceAssembly.SourceRole.ORIGINAL_CONSUMER_TEST
                        && expected.equals(ref.bytes() + ":" + ref.sha256()),
                        "Current staged tests cannot substitute for unchanged original capture inputs");
                String module = Path.of(relative).getFileName().toString().replaceFirst("\\.py$", "");
                require(routes.stream().filter(route -> route.module().equals(module)
                        && route.relativeSource().equals(relative)
                        && route.location() == SdkSourceAssembly.ImportSourceLocation.FRESH_GRAPH
                        && route.physicalRef().equals(ref)).count() == 1,
                        "Original capture test requires its explicit physical import route: " + relative);
            }
            ref.verify(); result.add(ref);
        }
        return List.copyOf(result);
    }

    public static Request read(byte[] json) throws IOException {
        require(json.length > 0 && json.length <= 16384, "Finite assembly request required");
        JsonNode node = ControlBuild.strictMapper().readTree(json);
        require(node != null && node.isObject(), "Assembly request must be a JSON object");
        strictIntegers(node);
        return ControlBuild.strictMapper().treeToValue(node, Request.class);
    }

    private static void strictIntegers(JsonNode node) {
        if (node.isObject()) {
            node.properties().forEach(entry -> {
                if ("bytes".equals(entry.getKey())) {
                    require(entry.getValue().isIntegralNumber() && entry.getValue().canConvertToLong(),
                            "FileRef bytes must be an exact JSON integer, not bool, float or string");
                }
                strictIntegers(entry.getValue());
            });
        } else if (node.isArray()) {
            node.forEach(ConstructionOracleAssemblyRequest::strictIntegers);
        }
    }

    private static void relative(String path) {
        require(path != null && !path.isBlank() && !path.contains("\\") && !path.contains(":")
                && !path.startsWith("/") && !List.of(path.split("/", -1)).contains("..")
                && !List.of(path.split("/", -1)).contains(""), "Finite repository-relative path required");
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }

    /** input-request exact-bytes exact-sha256 new-plan-output; no child is started. */
    public static void main(String[] args) throws IOException {
        if (args.length == 5 && "CAPTURE_INPUTS".equals(args[0])) {
            require(args[2].matches("[1-9][0-9]{0,7}"), "Exact positive reference byte count required");
            var reference = new ControlBuild.FileRef(args[1], Long.parseLong(args[2]), args[3]);
            System.out.println(ControlBuild.strictMapper().writeValueAsString(
                    requireCaptureInputs(reference, Leaf.valueOf(args[4]))));
            return;
        }
        if (args.length == 8 && "REFERENCE_VIEW".equals(args[0])) {
            var referenceRef=new ControlBuild.FileRef(args[1],Long.parseLong(args[2]),args[3]);
            var reference=SdkSourceAssembly.readReferenceRequest(referenceRef);
            require(reference.purpose()==SdkSourceAssembly.ReferencePurpose.REFERENCE_ORACLE_ONLY,
                    "Construction entry requires its explicit original-eight reference contract");
            var originalRef=reference.constructionRequestRef(); originalRef.verify();
            assemble(read(Files.readAllBytes(Path.of(originalRef.path()))),originalRef);
            SdkSourceAssembly.main(java.util.Arrays.copyOfRange(args, 1, 8));
            return;
        }
        require(args.length == 4, "request-path request-bytes request-sha256 new-plan-output");
        Path input = Path.of(args[0]).toAbsolutePath().normalize();
        ControlBuild.FileRef requestRef = new ControlBuild.FileRef(
                input.toString(), Long.parseLong(args[1]), args[2]);
        require(requestRef.bytes() > 0 && requestRef.bytes() <= 16384, "Finite assembly request reference required");
        requestRef.verify();
        Request request = read(Files.readAllBytes(input));
        Path output = Path.of(args[3]).toAbsolutePath().normalize();
        require(Files.isDirectory(output.getParent()) && !Files.exists(output),
                "Create-only plan output in an existing admitted directory required");
        Plan plan = assemble(request, requestRef);
        byte[] json = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(plan);
        require(json.length <= 32768, "Finite assembly plan required");
        Files.write(output, json, StandardOpenOption.CREATE_NEW);
        System.out.println(ControlBuild.strictMapper().writeValueAsString(ControlBuild.FileRef.measure(output)));
    }

    private ConstructionOracleAssemblyRequest() {}
}
