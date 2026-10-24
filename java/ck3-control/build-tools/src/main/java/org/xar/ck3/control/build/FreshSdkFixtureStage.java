package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Shared fixture stage, without a launcher or live SDK authority. */
public final class FreshSdkFixtureStage {
    private FreshSdkFixtureStage() {}
    public static final String SCHEMA = "xar.fresh-sdk-fixture-stage/v7";
    private static final String COLD = "tools/g2_saved_campaign/test_current_saved_campaign_cold_v1.py";
    private static final SdkSourceAssembly.Digest COLD_ORIGINAL = new SdkSourceAssembly.Digest(232879,
            "4f6f984f1c2d7b70c1a707491ef1d4fc3828f230a2e5bf0337a257562bd65ae0");
    private static final SdkSourceAssembly.Digest COLD_JAVA_INSTALLED = new SdkSourceAssembly.Digest(238249,
            "854e3788d3fd22211dc5bba41dc7cf6c36554c95535d55055da3bd107047594c");
    private static final String CONTINUITY = "tools/g2_saved_campaign/test_current_saved_continuity_v1.py";
    private static final String JAVA_CONTINUITY = "tools/g2_saved_campaign/test_java_saved_continuity_v1.py";
    private static final String CROWN = "ck3_autonomous_player/tests/unit/test_crown_java_policy_consumers_v1.py";
    private static final String CROWN_ORIGINAL = "tools/g2_saved_campaign/test_pending_material_crown_schema_adapter_v1.py";
    private static final String CROWN_ADAPTER = "tools/g2_saved_campaign/pending_material_crown_schema_adapter_v1.py";
    private static final String CROWN_NORMAL = "ck3_autonomous_player/tests/unit/test_g2_normal_crown_service_compound_v1.py";
    private static final String PROJECTION_CLIENT = "tools.g2_saved_campaign.java_map_admission_client_v1";
    private static final String PROJECTION_TEST = "tools/g2_saved_campaign/test_java_projection_client_v1.py";
    private static final String PROJECTION_TEST_MODULE = "tools.g2_saved_campaign.test_java_projection_client_v1";
    private static final String CONTINUATION = "CurrentSavedSdkPersistenceTests::test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations";
    private static final String SCORE_SUITE = "ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py";
    private static final String SCORE_CLI = "ck3_autonomous_player/tools/score_ck3_campaign.py";
    private static final List<String> SCORE_HELPERS = List.of("campaign_score_save_reader", "campaign_score_existing_inputs_v1",
            "campaign_score_cadence_v1", "campaign_score_target_projection");
    private static final String BUDGET_MODULE = "xar_autoplayer.war_emergency_budget_v1";
    private static final String BUDGET_HELPER = "ck3_autonomous_player/tests/unit/test_war_reinforcement_tradeoff_v1.py";
    private static final String BUDGET_CORPUS = "war-budget/src/test/resources/org/xar/ck3/control/warbudget/budget_golden_v1.jsonl.gz";
    private static final SdkSourceAssembly.Digest BUDGET_CORPUS_CONTENT = new SdkSourceAssembly.Digest(78376,
            "8ff4a406cc0d1244bd77f25140d1fa43c981d612c6afd0677485202203b21a6c");
    private static final List<String> BUDGET_CONSUMERS = List.of("war_reinforcement_finance_v1", "war_political_survival_stakes_v1",
            "war_reinforcement_tradeoff_v1", "war_strategic_reserve_v1", "war_mercenary_consumer_v1", "construction_formal_consumer",
            "m5_observed_opportunity_selector", "activity_feast_stage5_budget_v1", "bridge.version_identity",
            "bridge.domain_construction_private_transport_v1", "bridge.native_driver", "bridge.service", "bridge.mcp_server");
    private static final List<WholeTest> BUDGET_TESTS = List.of(
            new WholeTest("ck3_autonomous_player/tests/unit/test_war_emergency_budget_v1.py", new SdkSourceAssembly.Digest(15930, "2b90ba3f63643992aa533c50f825187d21841f12e0d626f85472330f82d0cced")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_war_crisis_spend_down_v1.py", new SdkSourceAssembly.Digest(9858, "83bead7057032650ec36089dce14cfd12f39d673e489713dada36d5551af3743")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_war_political_survival_stakes_v1.py", new SdkSourceAssembly.Digest(12740, "57a44d417600229199503977b252786edc937388e985b7da672c6c3ea01c179c")));
    private record WholeTest(String path, SdkSourceAssembly.Digest content) {}
    private static final List<WholeTest> M7_TESTS = List.of(
            new WholeTest("ck3_autonomous_player/tests/unit/test_g2_government_protocol_live_fix.py", new SdkSourceAssembly.Digest(3834, "644fc2f5e2a4e6e6f5e3b2af7f064d29d880f9241acb4de33eb73a936529dba0")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_g2_government_python_wire.py", new SdkSourceAssembly.Digest(6956, "ec5a96388a7b71fc72b5e018cf61424ff2892bc3dff3cbdd2d23488063ef8452")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_g2_nonwar_service_government_v1.py", new SdkSourceAssembly.Digest(7662, "5d23e668f27263043711be24e6d26003db2e7efc7c3d4b5b1e2f8bf26b60568b")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_ordinary_campaign_goal.py", new SdkSourceAssembly.Digest(15144, "400a364c72ef2987a9e3b59712b05ea02c7cb621b0a063b37024e4632ea381ab")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_ordinary_campaign_government_context_leaf_v1.py", new SdkSourceAssembly.Digest(7429, "7b9ada7c47bc8804b5d0621a4e16975d000e0a2c2b6995ec93b63196fcc906e9")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_player_heir_candidate_component_v1.py", new SdkSourceAssembly.Digest(14022, "5df2d10d457f9d6dbe838aa0f3f5d62cc168b75a4230b73f77d18936729ff74a")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_successor_ui_app_owner_v1.py", new SdkSourceAssembly.Digest(30029, "5eb60db1896cd6cf10abac309c358e7d13a112db0f21e784583b783055a732b2")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_successor_ui_checkpoint_cold_app_v1.py", new SdkSourceAssembly.Digest(14301, "689f09de0bb30031b7c7d871695afe871719cee022b72dcada37bdbd8519048c")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_successor_ui_checkpoint_lineage_v1.py", new SdkSourceAssembly.Digest(13156, "411a4d1df373ab082ea9c935728e8722d8399d6fd742dacd81332508a3b0df4c")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_successor_ui_pending_ledger_v1.py", new SdkSourceAssembly.Digest(19773, "75efadb1d18fb170f2b4b8b2e3ecba099171f316bbd5a7153cc1bbc73d02d77c")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_verified_successor_ui_service_v1.py", new SdkSourceAssembly.Digest(14719, "157b41adca88e83621b27ec7dc89001aaa9e30eaaf14d73d87cb456b0a047dc6")));
    private static final long MIB = 1L << 20;

    public enum Stage { IMPORT_PROBE, COMPLETE_COLD_FILE, COMPLETE_CONTINUITY_FILES, INDEPENDENT_CONTINUATION }
    public enum OriginKind { SOURCE, EXTENSION, BUILTIN, FROZEN, NAMESPACE, IN_MEMORY }
    public enum StartupProbeScope { NOT_RUN }
    public enum CanonicalStepScope { NOT_RUN }
    private static final List<WholeTest> M0_TESTS = List.of(
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_recommendation.py", new SdkSourceAssembly.Digest(20563, "7b52524ff8c2f0b19659c263919d350079a92008b9342d6c522881fad16e5c77")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_action_gate.py", new SdkSourceAssembly.Digest(5347, "f71104b0a30a357d2270a188237bc4685bacdf814d0ad91769f516f677e826c1")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_formal_exit_consumer.py", new SdkSourceAssembly.Digest(10019, "61b3b2b65b67c7c49ed6b4af490f5607079895cf09bc46890d0e116640b105dc")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_postcondition.py", new SdkSourceAssembly.Digest(14448, "c844f1b081141a3789597c7fff9dd3e4c66da2a27876f6c80ac165794d2e2895")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_postwar_evidence.py", new SdkSourceAssembly.Digest(11010, "f7a654d80dbdb9666019bdfeee135e0b2b5f16afec95ee889980874bf0be56e7")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_checkpoint_replay_recommendation_provider.py", new SdkSourceAssembly.Digest(4015, "4b4e959c3046bc8cde301ec930932d3caa97b315e52d7b1b7c46867c683463a8")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_gen034_three_way_recommendation_live_acceptance.py", new SdkSourceAssembly.Digest(10860, "34505c51ae4bdafee01bb49c5da357d5a1b96c365823cdf57356f27e48eb7f37")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_gen034_three_way_exit_action_live_acceptance.py", new SdkSourceAssembly.Digest(29724, "c986ff2677da2316281b003693ab67ce632c0c9fe1a89cc6e4aa69b8940079c2")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_prepare_g2_three_way_exit_file_intake.py", new SdkSourceAssembly.Digest(17208, "2f01e7390dc8aa835577b7d3ff5531893056a00bacb223e931923cb5ebff54a2")),
            new WholeTest("ck3_autonomous_player/tests/unit/test_raiktor_exit_utility_evaluator.py", new SdkSourceAssembly.Digest(8113, "4e8d4db124eb7dca316addd39d4c6fe995660e05e01daa4e73c87e684d558a2c"))
    );
    private static final WholeTest M0_LEGACY = new WholeTest("ck3_autonomous_player/tests/unit/test_g2_m0_current_sdk_consumers_v1.py", new SdkSourceAssembly.Digest(14459, "cad65cdf3f588835b042042aa0d37a7f782bc7a48b0f7380e2f3a17f184e821b"));
    public enum ConsumerGroupKind { M7_WHOLE11, M0_CURRENT_WHOLE90, M0_LEGACY_FORMAL, BUDGET_COMPLETE_FILES }
    /** The external owner uses the existing storage policy and its actual runtime card. */
    @FunctionalInterface public interface ResourceGuard { void revalidate(long pendingMetadataBytes) throws IOException; }

    public record Config(String schema, String machineId, String reviewAtUtc, String canonicalRepository,
            String workRoot, ControlBuild.FileRef pythonExecutable, ControlBuild.FileRef basePythonExecutable,
            ControlBuild.FileRef viewsActualRef, ControlBuild.FileRef selectedAssemblyActualRef,
            ControlBuild.FileRef deploymentReceiptRef, ControlBuild.FileRef supportContractRef,
            List<ControlBuild.FileRef> supportSources, List<String> dependencyRoots,
            List<ControlBuild.FileRef> dependencySources, ControlBuild.FileRef executionCardRef,
            List<ExpectedModule> additionalRequiredModules,
            ControlBuild.FileRef rootBootstrapRef,
            ControlBuild.FileRef producerGoldenPlanRef,
            long commandMemoryBytes, int commandTimeoutSeconds, int expectedColdParents) {
        public Config {
            supportSources = List.copyOf(supportSources); dependencyRoots = List.copyOf(dependencyRoots);
            dependencySources = List.copyOf(dependencySources);
            additionalRequiredModules = List.copyOf(additionalRequiredModules);
            if (!SCHEMA.equals(schema) || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Exact SDK fixture contract and machine required");
            Instant.parse(reviewAtUtc); Path repo = absolute(canonicalRepository), work = absolute(workRoot);
            if (repo.startsWith(work) || work.startsWith(repo) || commandMemoryBytes < 64 * MIB
                    || commandMemoryBytes > 1536 * MIB || commandTimeoutSeconds < 1 || commandTimeoutSeconds > 900
                    || !List.of(59, 63).contains(expectedColdParents) || supportSources.isEmpty()
                    || dependencyRoots.isEmpty() || dependencySources.isEmpty()) throw new IllegalArgumentException("Separate roots and finite explicit fixture resources required");
            for (String root : dependencyRoots) absolute(root);
            unique(supportSources); unique(dependencySources);
            if (dependencyRoots.stream().distinct().count() != dependencyRoots.size()) throw new IllegalArgumentException("Unique dependency roots required");
            if (additionalRequiredModules.size() > 128 || additionalRequiredModules.stream().map(ExpectedModule::module).distinct().count() != additionalRequiredModules.size())
                throw new IllegalArgumentException("Finite unique additional actual consumer imports required");
            for (var ref : List.of(pythonExecutable, basePythonExecutable, viewsActualRef, selectedAssemblyActualRef,
                    deploymentReceiptRef, supportContractRef, executionCardRef, rootBootstrapRef, producerGoldenPlanRef)) absolute(ref.path());
        }
    }
    public enum GoldenMilestone {
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M0") M0,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M1") M1,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M2") M2,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M3") M3,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M4") M4,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M5") M5,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M6") M6,
        @com.fasterxml.jackson.annotation.JsonProperty("G2-M7") M7
    }
    public record ProducerGoldenVector(GoldenMilestone milestone, ControlBuild.FileRef request, ControlBuild.FileRef result) {
        public ProducerGoldenVector {
            if (milestone == null) throw new IllegalArgumentException("One closed original G2 milestone required");
            absolute(request.path()); absolute(result.path());
        }
    }
    public record ProducerGoldenPlan(String schema, String machineId, ControlBuild.FileRef originalInstallMapRef,
            SdkSourceAssembly.Digest clientContent, SdkSourceAssembly.Digest testContent,
            ControlBuild.FileRef contextInput, ControlBuild.FileRef contextResult, ControlBuild.FileRef evaluateRequest,
            List<ProducerGoldenVector> vectors) {
        public ProducerGoldenPlan {
            vectors = List.copyOf(vectors);
            if (!"xar.sdk-producer-golden-plan/v1".equals(schema) || machineId == null || machineId.isBlank()
                    || clientContent == null || testContent == null || clientContent.bytes() < 1 || testContent.bytes() < 1
                    || !vectors.stream().map(ProducerGoldenVector::milestone).toList().equals(List.of(GoldenMilestone.values())))
                throw new IllegalArgumentException("Exact source-bound original producer plan and all eight ordered milestones required");
            absolute(originalInstallMapRef.path());
            List<ControlBuild.FileRef> refs = new ArrayList<>(List.of(contextInput, contextResult, evaluateRequest));
            for (var vector : vectors) refs.addAll(List.of(vector.request(), vector.result()));
            unique(refs); long bytes = 0;
            if (refs.stream().map(ref -> Path.of(ref.path()).normalize().toString().toLowerCase(java.util.Locale.ROOT)).distinct().count() != 19)
                throw new IllegalArgumentException("Original nineteen fixture paths cannot have case aliases");
            for (var ref : refs) {
                absolute(ref.path());
                if (ref.bytes() < 1 || ref.bytes() > 4 * MIB) throw new IllegalArgumentException("Nonempty bounded original producer bytes required");
                bytes = Math.addExact(bytes, ref.bytes());
            }
            if (bytes > 4 * MIB) throw new IllegalArgumentException("Bounded complete nineteen-file producer fixture set required");
        }
    }
    public static List<ControlBuild.FileRef> producerGoldenInputs(ProducerGoldenPlan plan) {
        List<ControlBuild.FileRef> refs = new ArrayList<>(List.of(plan.contextInput(), plan.contextResult(), plan.evaluateRequest()));
        for (var vector : plan.vectors()) refs.addAll(List.of(vector.request(), vector.result()));
        return List.copyOf(refs);
    }
    public static ProducerGoldenPlan readProducerGoldenPlan(ControlBuild.FileRef planRef) throws IOException {
        planRef.verify(); ProducerGoldenPlan plan = read(Path.of(planRef.path()), ProducerGoldenPlan.class); planRef.verify();
        plan.originalInstallMapRef().verify(); var origin = read(Path.of(plan.originalInstallMapRef().path()), com.fasterxml.jackson.databind.JsonNode.class);
        requireFields(origin, Set.of("schema", "machine_id", "observed_at_utc", "status", "existing_setup_spec_ref", "setup_source_field",
                "test_module_ref", "logical_module", "classes", "framework", "golden_install", "actual_config_seam", "authority", "roles"));
        if (!origin.path("schema").isTextual() || !origin.path("schema").textValue().equals("xar.existing-python-producer-golden-install-map/v1")
                || !origin.path("machine_id").isTextual() || !origin.path("machine_id").textValue().equals(plan.machineId())
                || !origin.path("logical_module").isTextual() || !origin.path("logical_module").textValue().equals(PROJECTION_TEST_MODULE))
            throw new IOException("Original nineteen-file producer handoff and same canonical test module required");
        for (String field : List.of("observed_at_utc", "status", "setup_source_field", "framework", "golden_install", "actual_config_seam", "authority"))
            if (!origin.path(field).isTextual() || origin.path(field).textValue().isBlank()) throw new IOException("Typed original handoff metadata required");
        if (!origin.path("status").textValue().equals("EXACT_EXISTING_SETUP_HANDOFF_NO_NEW_RUNNER")) throw new IOException("Original source-only fixture handoff status required");
        try { Instant.parse(origin.path("observed_at_utc").textValue()); }
        catch (java.time.format.DateTimeParseException failure) { throw new IOException("Original handoff observation time required", failure); }
        var setup = ControlBuild.strictMapper().treeToValue(origin.get("existing_setup_spec_ref"), ControlBuild.FileRef.class);
        if (setup == null || setup.bytes() < 1) throw new IOException("Original setup specification reference required"); absolute(setup.path());
        var test = ControlBuild.strictMapper().treeToValue(origin.get("test_module_ref"), ControlBuild.FileRef.class);
        if (test == null || !new SdkSourceAssembly.Digest(test.bytes(), test.sha256()).equals(plan.testContent())) throw new IOException("Original handoff test content differs");
        var classes = origin.path("classes"); requireFields(classes, Set.of("ProjectionClientContractTests", "ProjectionClientG2ProducerGoldenTests", "ProjectionClientActualJavaTests"));
        for (String name : List.of("ProjectionClientContractTests", "ProjectionClientG2ProducerGoldenTests", "ProjectionClientActualJavaTests")) {
            var count = classes.get(name); int expected = name.equals("ProjectionClientContractTests") ? 49 : name.equals("ProjectionClientG2ProducerGoldenTests") ? 4 : 2;
            if (!count.isIntegralNumber() || !count.canConvertToInt() || count.intValue() != expected) throw new IOException("Original complete client class inventory must be 49/4/2");
        }
        List<String> roles = new ArrayList<>(List.of("context_input", "context_result", "evaluate_request"));
        for (var milestone : GoldenMilestone.values()) roles.addAll(List.of("G2-" + milestone.name() + ".request", "G2-" + milestone.name() + ".result"));
        var rows = origin.path("roles"); if (!rows.isArray() || rows.size() != 19) throw new IOException("Exactly nineteen original fixture roles required");
        List<ControlBuild.FileRef> inputs = producerGoldenInputs(plan);
        for (int index = 0; index < roles.size(); index++) {
            var row = rows.get(index); requireFields(row, row.has("qualification") ? Set.of("role", "ref", "qualification") : Set.of("role", "ref"));
            if (row.has("qualification")) {
                if (!row.get("qualification").isArray()) throw new IOException("Typed original fixture qualification required");
                for (var item : row.get("qualification")) if (!item.isTextual() || item.textValue().isBlank()) throw new IOException("Original fixture qualification must remain text");
            }
            if (!row.path("role").isTextual() || !row.path("role").textValue().equals(roles.get(index))
                    || !inputs.get(index).equals(ControlBuild.strictMapper().treeToValue(row.get("ref"), ControlBuild.FileRef.class)))
                throw new IOException("Typed fixture role/ref differs from original producer handoff");
        }
        plan.originalInstallMapRef().verify(); for (var input : inputs) input.verify(); return plan;
    }
    private static void requireFields(com.fasterxml.jackson.databind.JsonNode node, Set<String> expected) throws IOException {
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        if (!node.isObject() || !actual.equals(expected)) throw new IOException("Closed producer handoff fields required");
    }
    public record ExpectedModule(String module, ControlBuild.FileRef source) {
        public ExpectedModule {
            if (module == null || !module.matches("[A-Za-z_][A-Za-z0-9_]*(?:[.][A-Za-z_][A-Za-z0-9_]*)*")) throw new IllegalArgumentException("Exact module name required");
            absolute(source.path());
        }
    }
    public record ModuleOrigin(String module, OriginKind kind, String file, List<String> namespacePaths) {
        public ModuleOrigin {
            namespacePaths = List.copyOf(namespacePaths);
            if (module == null || module.isBlank() || kind == null || file != null && file.isBlank()
                    || (kind == OriginKind.SOURCE || kind == OriginKind.EXTENSION) && file == null) throw new IllegalArgumentException("Typed actual module origin required");
        }
    }
    public record ScoreInputs(ExpectedModule client, ExpectedModule score, List<ExpectedModule> helpers,
            ControlBuild.FileRef suiteRef, ControlBuild.FileRef cliRef) {
        public ScoreInputs { helpers = List.copyOf(helpers); }
    }
    public record M0Source(String relativePath, String path, long bytes, String sha256) {}
    public record M0Inputs(String schema, String graphRoot, String sdkRoot, String outputRoot, List<M0Source> sources) {
        public M0Inputs { sources = List.copyOf(sources); }
    }
    public enum BudgetFunction {
        @com.fasterxml.jackson.annotation.JsonProperty("priority_emergency_level_v1") PRIORITY,
        @com.fasterxml.jackson.annotation.JsonProperty("observe_emergency_policy_v1") POLICY,
        @com.fasterxml.jackson.annotation.JsonProperty("valid_saved_emergency_revision_v1") SAVED_REVISION,
        @com.fasterxml.jackson.annotation.JsonProperty("emergency_quote_budget_v1") QUOTE,
        @com.fasterxml.jackson.annotation.JsonProperty("observe_emergency_recovery_v1") RECOVERY
    }
    public record BudgetGoldenProbe(BudgetFunction function, int ordinal, int requestLine, int resultLine,
            SdkSourceAssembly.Digest request, SdkSourceAssembly.Digest result) {}
    public record BudgetInputs(ExpectedModule client, ExpectedModule producer, List<ExpectedModule> consumers,
            ControlBuild.FileRef helperRef, ControlBuild.FileRef sourceCorpusRef, ControlBuild.FileRef compiledCorpusRef,
            List<BudgetGoldenProbe> probes) {
        public BudgetInputs { consumers = List.copyOf(consumers); probes = List.copyOf(probes); }
    }
    public record BudgetProbeObservation(BudgetFunction function, int ordinal, IssuedHttpProbe httpProbe, String resultPostcheck) {}
    public record BudgetConsumersObservation(String schema, String purpose, BudgetInputs sources, List<BudgetProbeObservation> probes,
            boolean canonicalSameObject, boolean clientApisUnchanged, String sourcePostcheck) {
        public BudgetConsumersObservation { probes = List.copyOf(probes); }
    }
    public record IssuedHttpProbe(String requestId, String requestSha256, String responseSha256, String transportKind,
            boolean actualHttpInvoked, com.fasterxml.jackson.databind.JsonNode httpCall) {}
    public record ScoreConsumersObservation(String schema, String purpose, int found, int started, int succeeded,
            int failures, int errors, int skipped, int actualHttpProbeCalls, boolean canonicalSameObject,
            boolean clientApisUnchanged, boolean actualHttpInvoked, String sourcePostcheck, ScoreInputs sources, IssuedHttpProbe probe) {}
    public record ConsumerGroupInput(ConsumerGroupKind kind, List<String> modules, List<ControlBuild.FileRef> testSources,
            List<String> pytestArguments, String stdoutPath, String stderrPath, String junitPath) {
        public ConsumerGroupInput { modules = List.copyOf(modules); testSources = List.copyOf(testSources); pytestArguments = List.copyOf(pytestArguments); }
    }
    public record ConsumerGroupObservation(ConsumerGroupKind kind, int collectedParents, int exitCode, String sourcePostcheck,
            List<ControlBuild.FileRef> testSources) { public ConsumerGroupObservation { testSources = List.copyOf(testSources); } }
    public record ConsumerGroupActual(ConsumerGroupKind kind, ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            ControlBuild.FileRef junitRef, SupplementalFixtureCi.PytestCounts counts) {}
    public record Observation(String schema, String stage, String pythonExecutable, String basePythonExecutable,
            String basePrefix, List<Integer> pythonVersion, String pytestVersion, String mcpVersion,
            List<ModuleOrigin> before, List<ModuleOrigin> after, int exitCode, String error,
            RootSoftwareChildBootstrap.ChildEvidence bootstrapEvidence, ScoreConsumersObservation scoreConsumers,
            BudgetConsumersObservation budgetConsumers, List<ConsumerGroupObservation> completeConsumers) {
        public Observation { pythonVersion = List.copyOf(pythonVersion); before = List.copyOf(before); after = List.copyOf(after); completeConsumers = List.copyOf(completeConsumers); }
    }
    public record CommandActual(Stage stage, List<String> arguments, WindowsJobProcess.ConsoleMode consoleMode, WindowsJobProcess.CommandResult result,
            ControlBuild.FileRef inputRef, ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef,
            ControlBuild.FileRef observationRef, List<ControlBuild.FileRef> observedSources,
            ControlBuild.FileRef junitRef, SupplementalFixtureCi.PytestCounts pytestCounts,
            String fixtureCleanup, String error, List<ConsumerGroupActual> completeConsumers) {
        public CommandActual { arguments = List.copyOf(arguments); observedSources = List.copyOf(observedSources); completeConsumers = List.copyOf(completeConsumers); }
    }
    public record Actual(String schema, String machineId, String startedAtUtc, String observedAtUtc,
            SupplementalFixtureCi.Status status, String error, ControlBuild.FileRef configRef,
            List<ControlBuild.FileRef> producerClosure, List<ExpectedModule> requiredFreshModules,
            List<CommandActual> commands, List<ControlBuild.FileRef> sourcePins,
            String sourcePostcheck, StartupProbeScope startupPublicProbe, CanonicalStepScope canonicalThirtyCommandStep) {
        public Actual { producerClosure = List.copyOf(producerClosure); requiredFreshModules = List.copyOf(requiredFreshModules); commands = List.copyOf(commands); sourcePins = List.copyOf(sourcePins); }
    }
    private record PythonInput(String schema, Stage stage, List<String> importRoots, List<String> requiredModules,
            String observationPath, List<String> pytestArguments, ControlBuild.FileRef bootstrapRef,
            ControlBuild.FileRef producerGoldenPlanRef, ProducerGoldenPlan producerGoldens,
            ControlBuild.FileRef projectionClientTestRef, ScoreInputs scoreInputs, BudgetInputs budgetInputs, M0Inputs m0Inputs, List<ConsumerGroupInput> completeConsumers) {
        private PythonInput { completeConsumers = List.copyOf(completeConsumers); }
    }
    private record Binding(SdkSourceAssembly.Actual assembly, List<ExpectedModule> required,
            List<ControlBuild.FileRef> sources, Set<String> sdkPaths, Set<String> allowedPaths) {}

    /* Python alone can inspect its actual module objects. This adapter installs exact producer fixtures
       through existing test APIs, invokes existing pytest and exports module metadata. Java validates every source and all outcomes; no business
       implementation, pytest plugin or parallel Python CI module is introduced. */
    private static final String OBSERVER = """
        import importlib, json, pathlib, sys, traceback
        request=json.loads(pathlib.Path(sys.argv[1]).read_bytes())
        sys.path[:0]=request['import_roots']
        def origins(names):
            rows=[]
            for name in sorted(names):
                module=sys.modules.get(name)
                if module is None: continue
                file=getattr(module,'__file__',None)
                if file is not None and not isinstance(file,str): raise TypeError('module file')
                paths=list(getattr(module,'__path__',()))
                if any(not isinstance(p,str) for p in paths): raise TypeError('namespace path')
                spec=getattr(module,'__spec__',None); origin=getattr(spec,'origin',None)
                kind=('BUILTIN' if origin=='built-in' else 'FROZEN' if origin=='frozen' else
                    'EXTENSION' if file and file.lower().endswith(('.pyd','.dll')) else
                    'SOURCE' if file else 'NAMESPACE' if paths else 'IN_MEMORY')
                rows.append({'module':name,'kind':kind,'file':file,'namespace_paths':paths})
            return rows
        code=3; error=None; before=[]; pytest_version=''; mcp_version=''; _xar_root_stack=None; _xar_root_bootstrap_evidence=None; projection_tests=None; projection_client=None; score_consumers=None; budget_consumers=None; complete_consumers=[]
        try:
            root_bootstrap_ref=request['bootstrap_ref']
            __XAR_ROOT_BOOTSTRAP_PREFIX__
            if request['stage']=='COMPLETE_CONTINUITY_FILES':
                bi=request['budget_inputs']; budget_client=_xar_root_client
                if bi is None or bi['client']['source']!=_xar_root_cfg['client']['source']: raise RuntimeError('budget and Root must bind the same selected client')
                for item in (bi['client'],bi['producer'],*bi['consumers']): _xar_root_read(item['source'],2097152)
                budget=_xar_root_load(bi['producer'])
                budget_api=(budget_client.require_current_projection_config_v1,budget_client.call_current_projection_v1,budget_client.require_result_context_v1)
                def budget_identity():
                    package=sys.modules.get('xar_autoplayer')
                    return (sys.modules.get(bi['client']['module']) is budget_client
                        and sys.modules['tools.g2_saved_campaign'].java_map_admission_client_v1 is budget_client
                        and sys.modules.get(bi['producer']['module']) is budget
                        and package is not None and package.war_emergency_budget_v1 is budget and budget._projection is budget_client
                        and budget_client.require_current_projection_config_v1() is _xar_root_config
                        and _xar_root_config.purpose=='FULL_SOFTWARE' and _xar_root_config.transport is None)
                if not budget_identity(): raise RuntimeError('actual canonical mechanical budget producer required before consumer imports')
            for name in request['required_modules']: importlib.import_module(name)
            before=origins(request['required_modules'])
            import pytest, importlib.metadata
            pytest_version=pytest.__version__; mcp_version=importlib.metadata.version('mcp')
            if request['stage']=='IMPORT_PROBE': code=0
            else:
                b=importlib.import_module('tools.g2_saved_campaign.test_current_saved_basis_v1')
                if request['stage']=='INDEPENDENT_CONTINUATION': b.HARD=524288; b.SOFT=458752
                c=importlib.import_module('tools.g2_saved_campaign.test_current_saved_campaign_cold_v1')
                if c.basis_fixture is not b: raise RuntimeError('one actual fixture module required')
                if request['stage']=='COMPLETE_CONTINUITY_FILES':
                    import unittest, importlib.util, contextlib
                    si=request['score_inputs']; projection_client=_xar_root_client
                    for item in (si['client'],si['score'],*si['helpers']): _xar_root_read(item['source'],2097152)
                    for ref in (si['suite_ref'],si['cli_ref']): _xar_root_read(ref,2097152)
                    if si['client']['source']!=_xar_root_cfg['client']['source']: raise RuntimeError('selected current client and actual Root bootstrap differ')
                    score=_xar_root_load(si['score'])
                    for item in si['helpers']: _xar_root_load(item)
                    import xar_autoplayer
                    def score_identity():
                        return (sys.modules.get(si['client']['module']) is projection_client
                            and sys.modules['tools.g2_saved_campaign'].java_map_admission_client_v1 is projection_client
                            and sys.modules.get(si['score']['module']) is score
                            and xar_autoplayer.campaign_development_score_v1 is score and score._projection is projection_client)
                    if not score_identity(): raise RuntimeError('one canonical selected score/client object required before suite import')
                    config=projection_client.require_current_projection_config_v1()
                    if config is not _xar_root_config or config.purpose!='FULL_SOFTWARE' or config.transport is not None: raise RuntimeError('actual FULL_SOFTWARE config required')
                    api=(projection_client.require_current_projection_config_v1,projection_client.call_current_projection_v1,projection_client.require_result_context_v1)
                    suite_path=pathlib.Path(si['suite_ref']['path'])
                    if suite_path.parents[2]/'tools/score_ck3_campaign.py'!=pathlib.Path(si['cli_ref']['path']): raise RuntimeError('selected suite must derive selected current CLI')
                    if 'test_campaign_development_score_v1' in sys.modules: raise RuntimeError('score suite cannot freeze imports before actual bootstrap')
                    spec=importlib.util.spec_from_file_location('test_campaign_development_score_v1',suite_path)
                    if spec is None or spec.loader is None: raise RuntimeError('selected whole score test source required')
                    suite=importlib.util.module_from_spec(spec); sys.modules[spec.name]=suite; spec.loader.exec_module(suite)
                    if suite.Interval is not score.Interval or suite.build_report is not score.build_report: raise RuntimeError('score suite imported a different production object')
                    whole=unittest.defaultTestLoader.loadTestsFromModule(suite); found=whole.countTestCases()
                    if found!=18: raise RuntimeError('whole original score module must discover exactly18')
                    outcome=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(whole)
                    if not outcome.wasSuccessful() or outcome.testsRun!=18 or outcome.skipped or outcome.expectedFailures or outcome.unexpectedSuccesses: raise RuntimeError('whole18 score/CLI consumers incomplete or skipped')
                    operation=projection_client.ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE
                    payload=projection_client.encode_projection_payload_v1({'schema':'g2.campaign-score-arithmetic/v1','profile':'python-decimal-default-28-half-even/v1','operation':'display','input':{'lower':'1','upper':'1','places':2}},maximum_bytes=65536)
                    request_id='score18-'+str(_xar_root_os.getpid())
                    issued=projection_client.call_current_projection_v1(operation=operation,payload=payload,request_id=request_id)
                    custody=projection_client.require_result_context_v1(issued,config=config,operation=operation,request_id=request_id,payload=payload)
                    if custody.config is not config or not issued.http_call.actual_http_invoked or issued.http_call.transport_kind!='stdlib-http-loopback/v1': raise RuntimeError('actual issued stdlib HTTP result required')
                    if api!=(projection_client.require_current_projection_config_v1,projection_client.call_current_projection_v1,projection_client.require_result_context_v1) or not score_identity(): raise RuntimeError('real client APIs or canonical objects changed')
                    for item in (si['client'],si['score'],*si['helpers']): _xar_root_read(item['source'],2097152)
                    for ref in (si['suite_ref'],si['cli_ref']): _xar_root_read(ref,2097152)
                    projection_client.qualify_projection_service_v1(config)
                    score_consumers={'schema':'xar.sdk-score-whole-consumers/v1','purpose':'FULL_SOFTWARE','found':found,'started':outcome.testsRun,'succeeded':outcome.testsRun,'failures':0,'errors':0,'skipped':0,'actual_http_probe_calls':1,'canonical_same_object':True,'client_apis_unchanged':True,'actual_http_invoked':True,'source_postcheck':'MATCH','sources':si,'probe':{'request_id':issued.request_id,'request_sha256':issued.request_sha256,'response_sha256':issued.response_sha256,'transport_kind':issued.http_call.transport_kind,'actual_http_invoked':issued.http_call.actual_http_invoked,'http_call':issued.http_call.to_wire()}}
                    plan=request['producer_goldens']
                    if json.loads(_xar_root_read(request['producer_golden_plan_ref'],4194304)) != plan: raise RuntimeError('exact typed producer plan differs')
                    _xar_root_read(request['projection_client_test_ref'],4194304)
                    projection_client=importlib.import_module('tools.g2_saved_campaign.java_map_admission_client_v1')
                    projection_tests=importlib.import_module('tools.g2_saved_campaign.test_java_projection_client_v1')
                    if projection_tests.client is not projection_client or pathlib.Path(projection_tests.__file__).resolve()!=pathlib.Path(request['projection_client_test_ref']['path']).resolve(): raise RuntimeError('one exact canonical client test instance required')
                    golden=projection_tests.ProjectionClientG2ProducerGoldenTests
                    golden.install_producer_golden_v1(context_input=_xar_root_read(plan['context_input'],4194304),context_result=_xar_root_read(plan['context_result'],4194304),evaluate_request=_xar_root_read(plan['evaluate_request'],4194304))
                    golden.install_domain_producer_golden_v1(vectors=tuple((projection_client.G2MilestoneV1(row['milestone']),_xar_root_read(row['request'],4194304),_xar_root_read(row['result'],4194304)) for row in plan['vectors']))
                    if projection_tests.ProjectionClientActualJavaTests.provided_config is not None: raise RuntimeError('actual client config cannot hot-rebind')
                    projection_tests.ProjectionClientActualJavaTests.provided_config=projection_client.require_current_projection_config_v1()
                code=int(pytest.main(request['pytest_arguments']))
                if projection_tests is not None and (sys.modules.get('tools.g2_saved_campaign.test_java_projection_client_v1') is not projection_tests or projection_tests.ProjectionClientActualJavaTests.provided_config is not projection_client.require_current_projection_config_v1()): raise RuntimeError('canonical collected module and same Root config must remain installed')
                if code==0:
                    class CompleteCollection:
                        count: int = 0
                        def pytest_collection_finish(self, session: pytest.Session) -> None:
                            self.count=len(session.items)
                    for group in request['complete_consumers']:
                        for ref in group['test_sources']: _xar_root_read(ref,2097152)
                        if group['kind'].startswith('M0_'):
                            import __main__
                            __main__._xar_m0_current_inputs=request['m0_inputs']
                            import __main__, importlib, sys
                            from pathlib import Path
                            _m0 = __main__._xar_m0_current_inputs
                            if _m0.get('schema') != 'xar.g2-m0-current-consumer-inputs/v1':
                                raise AssertionError('exact M0 current fixture required before test import')
                            _m0_graph = Path(_m0['graph_root']).resolve(strict=True)
                            _m0_sdk = Path(_m0['sdk_root']).resolve(strict=True)
                            if _m0_sdk != (_m0_graph/'ck3_autonomous_player/src').resolve(strict=True):
                                raise AssertionError('M0 SDK must be in the actual selected graph')
                            _m0_sources = {row['relative_path']: row for row in _m0['sources']}
                            if len(_m0_sources) != len(_m0['sources']):
                                raise AssertionError('unique exact M0 actual sources required')
                            for _p in sys.path:
                                if not _p:
                                    continue
                                _q = Path(_p).resolve()
                                if _q.name == 'src' and _q.parent.name == 'ck3_autonomous_player' and _q != _m0_sdk:
                                    raise AssertionError('old R/frozen SDK source path is forbidden in current M0')
                            _m0_paths = [_m0_graph, _m0_sdk,
                                         _m0_graph/'ck3_autonomous_player/tests/unit',
                                         _m0_graph/'ck3_autonomous_player/native_bridge/research']
                            for _p in reversed(_m0_paths):
                                if not _p.is_dir():
                                    raise AssertionError('complete staged M0 consumer closure required')
                                _s = str(_p)
                                if _s not in sys.path:
                                    sys.path.insert(0, _s)
                            import tools.g2_saved_campaign.java_map_admission_client_v1 as _m0_client
                            if _m0_client is not _xar_root_client:
                                raise AssertionError('M0 must use the Root-installed canonical client object')
                            if _m0_client.require_current_projection_config_v1() is not _xar_root_config:
                                raise AssertionError('actual same-process Root FULL_SOFTWARE configuration required')
                            for _name, _relative in (
                                ('tools.g2_saved_campaign.java_map_admission_client_v1',
                                 'tools/g2_saved_campaign/java_map_admission_client_v1.py'),
                                ('xar_autoplayer.simulation.raiktor_three_way_exit_recommendation',
                                 'ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_recommendation.py'),
                                ('xar_autoplayer.raiktor_formal_exit',
                                 'ck3_autonomous_player/src/xar_autoplayer/raiktor_formal_exit.py'),
                                ('prepare_gen034_checkpoint_replay_recommendation',
                                 'ck3_autonomous_player/native_bridge/research/prepare_gen034_checkpoint_replay_recommendation.py'),
                                ('run_gen034_three_way_recommendation_live_acceptance',
                                 'ck3_autonomous_player/native_bridge/research/run_gen034_three_way_recommendation_live_acceptance.py'),
                            ):
                                _module = importlib.import_module(_name)
                                _expected = Path(_m0_sources[_relative]['path']).resolve(strict=True)
                                if _expected != (_m0_graph/_relative).resolve(strict=True) or Path(_module.__file__).resolve(strict=True) != _expected:
                                    raise AssertionError('M0 imported a stale/canonical fallback module')
                            for _name, _module in list(sys.modules.items()):
                                if (_name == 'xar_autoplayer' or _name.startswith('xar_autoplayer.')) and getattr(_module, '__file__', None):
                                    if not Path(_module.__file__).resolve(strict=True).is_relative_to(_m0_sdk):
                                        raise AssertionError('all current M0 SDK imports must stay in selected source32')
                        if group['kind']=='BUDGET_COMPLETE_FILES':
                            import gzip, hashlib, struct, math
                            if not budget_identity(): raise RuntimeError('whole budget consumers lost canonical installed producer')
                            for item in bi['consumers']: _xar_root_load(item)
                            helper_name=pathlib.Path(bi['helper_ref']['path']).stem
                            _xar_root_read(bi['helper_ref'],2097152)
                            budget_helper=importlib.import_module(helper_name)
                            if pathlib.Path(budget_helper.__file__).resolve()!=pathlib.Path(bi['helper_ref']['path']).resolve(): raise RuntimeError('budget helper must be the selected canonical test module')
                            for name,module in tuple(sys.modules.items()):
                                file=getattr(module,'__file__',None)
                                if file is not None and pathlib.Path(file).resolve()==pathlib.Path(bi['helper_ref']['path']).resolve() and name!=helper_name: raise RuntimeError('duplicate budget test helper instance')
                            packed=_xar_root_read(bi['source_corpus_ref'],1048576)
                            if _xar_root_read(bi['compiled_corpus_ref'],1048576)!=packed: raise RuntimeError('source and compiled original budget corpus differ')
                            flat=gzip.decompress(packed)
                            if len(flat)!=2192787 or hashlib.sha256(flat).hexdigest()!='1ebee2e6c4d8d7e11f1984b4649905fd44c9e198e4565adfbb8f72fa9a539e27': raise RuntimeError('exact retained original budget capture required')
                            rows=flat.split(b'\\n')
                            if rows[-1]!=b'' or len(rows)!=638: raise RuntimeError('complete original budget JSONL required')
                            def budget_equal(left: object,right: object) -> bool:
                                if type(left) is not type(right): return False
                                if isinstance(left,dict) and isinstance(right,dict): return left.keys()==right.keys() and all(budget_equal(left[key],right[key]) for key in left)
                                if isinstance(left,list) and isinstance(right,list): return len(left)==len(right) and all(budget_equal(a,b) for a,b in zip(left,right))
                                if isinstance(left,float) and isinstance(right,float): return math.isfinite(left) and math.isfinite(right) and struct.pack('>d',left)==struct.pack('>d',right)
                                return left==right
                            budget_probes=[]
                            for vector in bi['probes']:
                                payload=rows[vector['request_line']-1]; expected=rows[vector['result_line']-1]
                                for raw,content in ((payload,vector['request']),(expected,vector['result'])):
                                    if len(raw)!=content['bytes'] or hashlib.sha256(raw).hexdigest()!=content['sha256']: raise RuntimeError('original budget vector row identity differs')
                                packet=budget_client.decode_projection_object_v1(payload,maximum_bytes=65536)
                                if packet['schema']!='g2.war-budget-request/v1' or packet['operation']!=vector['function']: raise RuntimeError('original budget vector function differs')
                                operation=budget_client.ProjectionOperation.WAR_BUDGET_EVALUATE
                                request_id='budget-'+str(vector['ordinal'])+'-'+str(_xar_root_os.getpid())
                                issued=budget_client.call_current_projection_v1(operation=operation,payload=payload,request_id=request_id)
                                custody=budget_client.require_result_context_v1(issued,config=_xar_root_config,operation=operation,request_id=request_id,payload=payload)
                                value=budget_client.decode_projection_json_v1(issued.require_success(),maximum_bytes=16384)
                                if custody.config is not _xar_root_config or not budget_equal(value,json.loads(expected)): raise RuntimeError('actual budget result changed original JSON prototype/value')
                                budget_probes.append({'function':vector['function'],'ordinal':vector['ordinal'],'http_probe':{'request_id':issued.request_id,'request_sha256':issued.request_sha256,'response_sha256':issued.response_sha256,'transport_kind':issued.http_call.transport_kind,'actual_http_invoked':issued.http_call.actual_http_invoked,'http_call':issued.http_call.to_wire()},'result_postcheck':'MATCH'})
                        collected=CompleteCollection()
                        with open(group['stdout_path'],'x',encoding='utf-8') as out, open(group['stderr_path'],'x',encoding='utf-8') as err:
                            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                                code=int(pytest.main(group['pytest_arguments'],plugins=[collected]))
                        if group['kind']=='BUDGET_COMPLETE_FILES':
                            if not budget_identity() or sys.modules.get(helper_name) is not budget_helper: raise RuntimeError('budget producer/helper canonical identity changed')
                            if budget_api!=(budget_client.require_current_projection_config_v1,budget_client.call_current_projection_v1,budget_client.require_result_context_v1): raise RuntimeError('current budget client APIs changed')
                            for item in (bi['client'],bi['producer'],*bi['consumers']): _xar_root_read(item['source'],2097152)
                            for ref in (bi['helper_ref'],bi['source_corpus_ref'],bi['compiled_corpus_ref']): _xar_root_read(ref,2097152)
                            budget_client.qualify_projection_service_v1(_xar_root_config)
                            budget_consumers={'schema':'xar.sdk-budget-whole-consumers/v1','purpose':'FULL_SOFTWARE','sources':bi,'probes':budget_probes,'canonical_same_object':True,'client_apis_unchanged':True,'source_postcheck':'MATCH'}
                        for ref in group['test_sources']: _xar_root_read(ref,2097152)
                        complete_consumers.append({'kind':group['kind'],'collected_parents':collected.count,'exit_code':code,'source_postcheck':'MATCH','test_sources':group['test_sources']})
                        if code!=0: break
                if budget_consumers is not None:
                    if not budget_identity() or budget_api!=(budget_client.require_current_projection_config_v1,budget_client.call_current_projection_v1,budget_client.require_result_context_v1): raise RuntimeError('complete consumers changed canonical budget/client config')
                if score_consumers is not None:
                    if api!=(projection_client.require_current_projection_config_v1,projection_client.call_current_projection_v1,projection_client.require_result_context_v1) or not score_identity() or projection_client.require_current_projection_config_v1() is not config: raise RuntimeError('whole consumers changed actual canonical client/config')
                    for item in (si['client'],si['score'],*si['helpers']): _xar_root_read(item['source'],2097152)
                    for ref in (si['suite_ref'],si['cli_ref']): _xar_root_read(ref,2097152)
                    projection_client.qualify_projection_service_v1(config)

        except BaseException as failure:
            code=code if code else 1; error=type(failure).__name__+': '+str(failure); traceback.print_exc()
        finally:
            try:
                value={'schema':'xar.sdk-python-origin-observation/v7','stage':request['stage'],
                    'python_executable':sys.executable,'base_python_executable':sys._base_executable,
                    'base_prefix':sys.base_prefix,'python_version':list(sys.version_info[:3]),
                    'pytest_version':pytest_version,'mcp_version':mcp_version,'before':before,
                    'after':origins(tuple(sys.modules)),'exit_code':code,'error':error,
                    'bootstrap_evidence':_xar_root_bootstrap_evidence,'score_consumers':score_consumers,'budget_consumers':budget_consumers,'complete_consumers':complete_consumers}
                raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')
                if len(raw)>4194304: raise RuntimeError('bounded actual import metadata required')
                with open(request['observation_path'],'xb') as stream: stream.write(raw)
            finally:
                if _xar_root_stack is not None: _xar_root_stack.close()
        raise SystemExit(code)
        """.replace("    __XAR_ROOT_BOOTSTRAP_PREFIX__\n", RootSoftwareChildBootstrap.pythonPrefix().indent(4));

    public static ControlBuild.FileRef run(Config config, ResourceGuard resources) throws IOException, InterruptedException {
        check(config, resources); Binding binding = bind(config); verifyBinding(config, binding); Path work = absolute(config.workRoot());
        SharedSourceFiles.plainAncestors(work);
        if (Files.exists(work, LinkOption.NOFOLLOW_LINKS)) throw new IOException("SDK fixture work root must be create-only");
        Files.createDirectories(work); Files.createDirectory(work.resolve("scratch"));
        Path configPath = work.resolve("config.json"); write(configPath, config, config, resources);
        String started = Instant.now().toString(), error = null, postcheck = "UNKNOWN";
        List<CommandActual> commands = new ArrayList<>(); List<ControlBuild.FileRef> closure = ControlBuild.producerClosure();
        try {
            for (Stage stage : Stage.values()) {
                CommandActual command = command(config, binding, stage, resources); commands.add(command);
                if (command.error() != null || !command.result().passed()) throw new IOException("Actual SDK stage rejected: " + stage + ": " + command.error());
            }
        } catch (IOException | RuntimeException failure) { error = failure.getClass().getSimpleName() + ": " + failure.getMessage(); }
        finally {
            if (error == null && commands.size() != Stage.values().length) error = "SDK fixture execution interrupted or incomplete";
            try { verifyBinding(config, binding); for (var ref : closure) ref.verify(); check(config, resources); postcheck = "MATCH"; }
            catch (IOException | RuntimeException failure) { error = append(error, "Source recheck: " + failure.getMessage()); postcheck = "UNAVAILABLE"; }
            write(work.resolve("actual.json"), new Actual(SCHEMA, config.machineId(), started, Instant.now().toString(),
                    error == null && commands.size() == Stage.values().length ? SupplementalFixtureCi.Status.PASS : SupplementalFixtureCi.Status.RED,
                    error, ControlBuild.FileRef.measure(configPath), closure, binding.required(), commands, binding.sources(), postcheck,
                    StartupProbeScope.NOT_RUN, CanonicalStepScope.NOT_RUN), config, resources);
        }
        if (error != null) throw new IOException(error);
        return requireAccepted(work.resolve("actual.json"), resources);
    }

    private static CommandActual command(Config config, Binding binding, Stage stage, ResourceGuard resources) throws IOException, InterruptedException {
        Path work = absolute(config.workRoot()), stageRoot = work.resolve(stage.name().toLowerCase(java.util.Locale.ROOT));
        Files.createDirectory(stageRoot); Path scratch = Files.createDirectory(stageRoot.resolve("scratch"));
        Path continuity = Files.createDirectories(scratch.resolve("continuity/test-continuity"));
        Path basis = scratch.resolve("basis"), closed = scratch.resolve("closure"), cache = scratch.resolve("pycache-no-read");
        Path xml = stageRoot.resolve("pytest.xml"), observation = stageRoot.resolve("origins.json"), input = stageRoot.resolve("input.json");
        List<String> roots = importRoots(stage, binding.assembly().graphRoot(), binding.assembly().sdkRoot(), config.canonicalRepository(), config.dependencyRoots());
        List<String> args = pytestArguments(stage, Path.of(binding.assembly().graphRoot()), xml, scratch.resolve("pytest-temp"));
        write(input, new PythonInput("xar.sdk-python-origin-input/v7", stage, roots,
                binding.required().stream().map(ExpectedModule::module).toList(), observation.toString(), args, config.rootBootstrapRef(),
                config.producerGoldenPlanRef(), readProducerGoldenPlan(config.producerGoldenPlanRef()), source(binding, PROJECTION_TEST), stage == Stage.COMPLETE_CONTINUITY_FILES ? scoreInputs(binding) : null, stage == Stage.COMPLETE_CONTINUITY_FILES ? budgetInputs(config, binding) : null, m0Inputs(stage, binding, stageRoot), consumerGroups(stage, binding, stageRoot)), config, resources);
        Map<String, String> env = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); env.putAll(System.getenv());
        env.keySet().removeIf(name -> name.toUpperCase(java.util.Locale.ROOT).startsWith("XAR_"));
        for (String name : List.of("PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS")) env.remove(name);
        env.put("PYTHONDONTWRITEBYTECODE", "1"); env.put("PYTHONSAFEPATH", "1"); env.put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        env.put("PYTHONPYCACHEPREFIX", cache.toString()); env.put("PYTHONIOENCODING", "utf-8");
        for (String name : List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")) env.put(name, "1");
        for (String name : List.of("TEMP", "TMP", "TMPDIR", "RUNNER_TEMP")) env.put(name, scratch.toString());
        env.put("XAR_CURRENT_SAVED_BASIS_TEST_ROOT", basis.toString()); env.put("XAR_CURRENT_SAVED_BASIS_TEST_REVIEW_UTC", config.reviewAtUtc());
        env.put("XAR_CURRENT_SAVED_BASIS_MACHINE_ID", config.machineId()); env.put("XAR_CURRENT_SAVED_CLOSURE_TEST_ROOT", closed.toString());
        env.put("XAR_CONTINUITY_TEST_FIXTURE_ROOT", continuity.toString());
        List<String> arguments = List.of("-I", "-S", "-B", "-X", "utf8", "-X", "pycache_prefix=" + cache, "-c", OBSERVER, input.toString());
        Path stdout = stageRoot.resolve("stdout.log"), stderr = stageRoot.resolve("stderr.log");
        verifyBinding(config, binding); for (var ref : ControlBuild.producerClosure()) ref.verify(); check(config, resources); WindowsJobProcess.CommandResult result;
        try (var child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(Path.of(config.pythonExecutable().path()), arguments,
                scratch, Map.copyOf(env), stdout, stderr, config.commandMemoryBytes()), WindowsJobProcess.ConsoleMode.DETACHED)) {
            result = child.await(Duration.ofSeconds(config.commandTimeoutSeconds()), Instant.parse(config.reviewAtUtc()),
                    () -> { try { check(config, resources); } catch (IOException failure) { throw new IllegalStateException(failure); } });
        }
        String error = null, cleanup = "NOT_CHECKED"; List<ControlBuild.FileRef> observed = List.of(); SupplementalFixtureCi.PytestCounts counts = null; List<ConsumerGroupActual> complete = List.of();
        try {
            Observation actual = read(observation, Observation.class); validateObservation(config, binding, stage, actual);
            observed = observedSources(actual);
            if (stage != Stage.IMPORT_PROBE) {
                counts = SupplementalFixtureCi.readPytest(xml, stdout, pytestModules(stage)); requireCounts(stage, counts, config.expectedColdParents());
                if (stage == Stage.COMPLETE_CONTINUITY_FILES) requireProjectionClientClasses(xml);
                complete = readConsumerGroups(consumerGroups(stage, binding, stageRoot)); requireCollectedCounts(actual.completeConsumers(), complete);
            }
            requireAbsent(basis); requireAbsent(closed); requireAbsent(cache);
            try (var files = Files.list(continuity)) { if (files.findAny().isPresent()) throw new IOException("Continuity fixture cleanup incomplete"); }
            cleanup = "BASIS_CLOSURE_CACHE_ABSENT_CONTINUITY_EMPTY"; verifyBinding(config, binding); check(config, resources);
        } catch (IOException | RuntimeException failure) { error = failure.getClass().getSimpleName() + ": " + failure.getMessage(); }
        ControlBuild.FileRef inputRef = null, stdoutRef = null, stderrRef = null, observationRef = null, xmlRef = null;
        try { inputRef = ControlBuild.FileRef.measure(input); stdoutRef = ControlBuild.FileRef.measure(stdout); stderrRef = ControlBuild.FileRef.measure(stderr); observationRef = maybe(observation); xmlRef = maybe(xml); }
        catch (IOException unavailable) { error = append(error, "Actual terminal retained; evidence reference unavailable: " + unavailable.getMessage()); }
        return new CommandActual(stage, arguments, WindowsJobProcess.ConsoleMode.DETACHED, result, inputRef, stdoutRef, stderrRef, observationRef, observed, xmlRef, counts, cleanup, error, complete);
    }



    private static BudgetInputs budgetInputs(Config config, Binding binding) throws IOException {
        var producer = selected(binding, "ck3_autonomous_player/src/xar_autoplayer/war_emergency_budget_v1.py", SdkSourceAssembly.SourceRole.SDK_SOURCE);
        if (producer.bytes() != 4728 || !producer.sha256().equals("d3938c90c626d2ccc24a14125da217a8551e9c7367703aa5b159d0ec04a717fd"))
            throw new IOException("Current budget consumers require the selected mechanical Java adapter");
        List<ExpectedModule> consumers = new ArrayList<>();
        for (String name : BUDGET_CONSUMERS) consumers.add(new ExpectedModule("xar_autoplayer." + name,
                selected(binding, "ck3_autonomous_player/src/xar_autoplayer/" + name.replace('.', '/') + ".py", SdkSourceAssembly.SourceRole.SDK_SOURCE)));
        var helper = budgetTestSource(binding, BUDGET_HELPER, new SdkSourceAssembly.Digest(28524,
                "3420dab5250ffe39246c30d9479c2cde73ee17eba1c16f6878a345db25fa010d"));
        var receipt = ControlBuild.acceptedReceipt(Path.of(config.deploymentReceiptRef().path()));
        var sourceCorpus = budgetCorpus(receipt.sourcePins(), Path.of(receipt.sourceRoot()).resolve(BUDGET_CORPUS));
        var compiledCorpus = budgetCorpus(receipt.compiledSourcePins(), Path.of(receipt.compiledSourceRoot()).resolve(BUDGET_CORPUS));
        return new BudgetInputs(new ExpectedModule(PROJECTION_CLIENT, source(binding, PROJECTION_CLIENT.replace('.', '/') + ".py")),
                new ExpectedModule(BUDGET_MODULE, producer), consumers, helper, sourceCorpus, compiledCorpus, budgetProbes());
    }
    private static ControlBuild.FileRef budgetTestSource(Binding binding, String path, SdkSourceAssembly.Digest expected) throws IOException {
        var rows = binding.assembly().actualSourceClosure().stream().filter(row -> row.relativePath().equals(path)).toList();
        if (rows.size() != 1 || !List.of(SdkSourceAssembly.SourceRole.ORIGINAL_CONSUMER_TEST, SdkSourceAssembly.SourceRole.STAGED_CONSUMER_TEST).contains(rows.getFirst().role()))
            throw new IOException("Exact original or explicitly staged budget consumer test required");
        var ref = rows.getFirst().actual(); ref.verify();
        if (ref.bytes() != expected.bytes() || !ref.sha256().equals(expected.sha256())) throw new IOException("Complete original budget consumer source drift");
        return ref;
    }
    private static ControlBuild.FileRef budgetCorpus(List<ControlBuild.FileRef> pins, Path expected) throws IOException {
        var rows = pins.stream().filter(ref -> Path.of(ref.path()).toAbsolutePath().normalize().equals(expected.toAbsolutePath().normalize())).toList();
        if (rows.size() != 1) throw new IOException("Budget original corpus must have exact source and compiled-source witnesses");
        var ref = rows.getFirst(); ref.verify();
        if (ref.bytes() != BUDGET_CORPUS_CONTENT.bytes() || !ref.sha256().equals(BUDGET_CORPUS_CONTENT.sha256()))
            throw new IOException("Retained original budget corpus differs");
        return ref;
    }
    private static List<BudgetGoldenProbe> budgetProbes() {
        return List.of(
            new BudgetGoldenProbe(BudgetFunction.PRIORITY, 4, 12, 13,
                new SdkSourceAssembly.Digest(1653, "21a51f6f7e6290f4c7c1cffdfab75cf8379da42c7a8b89946c23582120d53e0b"),
                new SdkSourceAssembly.Digest(1, "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b")),
            new BudgetGoldenProbe(BudgetFunction.POLICY, 5, 15, 16,
                new SdkSourceAssembly.Digest(4868, "b887c104ed53c78e6b7e1aa451a2ed2068ae2eb354e63d2f1fefea33177dc1bb"),
                new SdkSourceAssembly.Digest(2291, "dd728203244f98b8eeec4a3997b3e489df085f62370510b263839c1226c522c5")),
            new BudgetGoldenProbe(BudgetFunction.SAVED_REVISION, 54, 162, 163,
                new SdkSourceAssembly.Digest(10427, "b94b9e29ec33de049757465d39ea868d6c66a5b3929dd5f0df0f1df7fe9d162e"),
                new SdkSourceAssembly.Digest(2782, "733a079cf54960232bbe2cd07decd6f61c1913ebe1ae80fc76c227eed6ba73ea")),
            new BudgetGoldenProbe(BudgetFunction.QUOTE, 36, 108, 109,
                new SdkSourceAssembly.Digest(7324, "13872d0906975b7ab6d84ccf90c8d014414bb8da4f98bee555f4e44f0e97cc49"),
                new SdkSourceAssembly.Digest(4382, "7c697e8312460731aa3929bc292e8dab76e10c9b027fb81d1a85c7f7e73ea077")),
            new BudgetGoldenProbe(BudgetFunction.RECOVERY, 55, 165, 166,
                new SdkSourceAssembly.Digest(23486, "dee831da024979665cd0daea268408d7a946f59424e540e65674fe78a5adfe6c"),
                new SdkSourceAssembly.Digest(473, "7cd7a277d75255800dc5f58262573c3d7006113940cc3a50efa0d7ba76e18bba")));
    }
    static void requireBudgetConsumers(BudgetConsumersObservation actual, BudgetInputs expected) throws IOException {
        if (actual == null || !"xar.sdk-budget-whole-consumers/v1".equals(actual.schema()) || !"FULL_SOFTWARE".equals(actual.purpose())
                || !expected.equals(actual.sources()) || !actual.canonicalSameObject() || !actual.clientApisUnchanged()
                || !"MATCH".equals(actual.sourcePostcheck()) || actual.probes().size() != expected.probes().size())
            throw new IOException("Actual whole budget consumers must retain the current canonical client/config and exact sources");
        for (int index = 0; index < expected.probes().size(); index++) {
            var wanted = expected.probes().get(index); var found = actual.probes().get(index); var call = found.httpProbe();
            if (found.function() != wanted.function() || found.ordinal() != wanted.ordinal() || !"MATCH".equals(found.resultPostcheck())
                    || call == null || !call.actualHttpInvoked() || !"stdlib-http-loopback/v1".equals(call.transportKind())
                    || !call.requestId().startsWith("budget-") || !call.requestSha256().matches("[0-9a-f]{64}") || !call.responseSha256().matches("[0-9a-f]{64}")
                    || call.httpCall() == null || !"xar.java-projection-http-call/v1".equals(call.httpCall().path("schema").asText())
                    || !call.httpCall().path("actual_HTTP_call").isBoolean() || !call.httpCall().path("actual_HTTP_call").booleanValue())
                throw new IOException("Every budget function requires its original positive vector through real issued HTTP custody");
        }
    }

    private static ScoreInputs scoreInputs(Binding binding) throws IOException {
        List<ExpectedModule> helpers = new ArrayList<>();
        for (String name : SCORE_HELPERS) helpers.add(new ExpectedModule("xar_autoplayer." + name,
                selected(binding, "ck3_autonomous_player/src/xar_autoplayer/" + name + ".py", SdkSourceAssembly.SourceRole.SDK_SOURCE)));
        return new ScoreInputs(new ExpectedModule(PROJECTION_CLIENT,
                source(binding, PROJECTION_CLIENT.replace('.', '/') + ".py")),
                new ExpectedModule("xar_autoplayer.campaign_development_score_v1",
                        selected(binding, "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py", SdkSourceAssembly.SourceRole.SDK_SOURCE)),
                helpers, selected(binding, SCORE_SUITE, SdkSourceAssembly.SourceRole.STAGED_CONSUMER_TEST),
                selected(binding, SCORE_CLI, SdkSourceAssembly.SourceRole.CONSUMER_SOURCE));
    }
    private static ControlBuild.FileRef selected(Binding binding, String path, SdkSourceAssembly.SourceRole role) throws IOException {
        var rows = binding.assembly().actualSourceClosure().stream().filter(row -> row.relativePath().equals(path)).toList();
        if (rows.size() != 1 || rows.getFirst().role() != role) throw new IOException("One exact selected consumer source/role required: " + path);
        rows.getFirst().actual().verify(); return rows.getFirst().actual();
    }
    private static List<ConsumerGroupInput> consumerGroups(Stage stage, Binding binding, Path root) throws IOException {
        if (stage != Stage.COMPLETE_CONTINUITY_FILES) return List.of();
        List<ConsumerGroupInput> groups = new ArrayList<>();
        List<String> modules = new ArrayList<>(); List<ControlBuild.FileRef> refs = new ArrayList<>();
        for (WholeTest test : M7_TESTS) {
            var ref = selected(binding, test.path(), SdkSourceAssembly.SourceRole.STAGED_CONSUMER_TEST);
            if (ref.bytes() != test.content().bytes() || !ref.sha256().equals(test.content().sha256())) throw new IOException("M7 complete test differs from selected frozen contract");
            modules.add(test.path()); refs.add(ref);
        }
        groups.add(consumerGroup(ConsumerGroupKind.M7_WHOLE11, modules, refs, binding, root));
        for (var kind : List.of(ConsumerGroupKind.M0_CURRENT_WHOLE90, ConsumerGroupKind.M0_LEGACY_FORMAL)) {
            List<String> paths = new ArrayList<>(); List<ControlBuild.FileRef> exact = new ArrayList<>();
            for (WholeTest test : kind == ConsumerGroupKind.M0_CURRENT_WHOLE90 ? M0_TESTS : List.of(M0_LEGACY)) {
                var ref = selected(binding, test.path(), SdkSourceAssembly.SourceRole.STAGED_CONSUMER_TEST);
                if (ref.bytes() != test.content().bytes() || !ref.sha256().equals(test.content().sha256())) throw new IOException("Current M0 whole test source differs");
                paths.add(test.path()); exact.add(ref);
            }
            groups.add(consumerGroup(kind, paths, exact, binding, root));
        }
        List<String> budgetModules = new ArrayList<>(); List<ControlBuild.FileRef> budgetRefs = new ArrayList<>();
        for (WholeTest test : BUDGET_TESTS) {
            budgetModules.add(test.path()); budgetRefs.add(budgetTestSource(binding, test.path(), test.content()));
        }
        groups.add(consumerGroup(ConsumerGroupKind.BUDGET_COMPLETE_FILES, budgetModules, budgetRefs, binding, root));
        return List.copyOf(groups);
    }
    private static M0Inputs m0Inputs(Stage stage, Binding binding, Path root) throws IOException {
        if (stage != Stage.COMPLETE_CONTINUITY_FILES) return null;
        Path graph = Path.of(binding.assembly().graphRoot()).toRealPath(); List<M0Source> sources = new ArrayList<>();
        for (var item : binding.assembly().actualSourceClosure()) {
            Path path = Path.of(item.actual().path()).toRealPath();
            if (!path.startsWith(graph)) throw new IOException("M0 current inputs require materialized actual graph sources");
            String relative = graph.relativize(path).toString().replace('\\', '/');
            if (!relative.equals(item.relativePath())) throw new IOException("M0 materialized source path differs from selected closure");
            sources.add(new M0Source(relative, item.actual().path(), item.actual().bytes(), item.actual().sha256()));
        }
        return new M0Inputs("xar.g2-m0-current-consumer-inputs/v1", graph.toString(), binding.assembly().sdkRoot(),
                root.resolve("scratch").toString(), sources);
    }
    private static ConsumerGroupInput consumerGroup(ConsumerGroupKind kind, List<String> modules,
            List<ControlBuild.FileRef> refs, Binding binding, Path root) {
        String name = kind.name().toLowerCase(java.util.Locale.ROOT); Path xml = root.resolve(name + ".xml");
        List<String> arguments = new ArrayList<>(List.of("-q", "-ra", "--color=no", "-p", "no:cacheprovider",
                kind == ConsumerGroupKind.BUDGET_COMPLETE_FILES ? "--import-mode=prepend" : "--import-mode=importlib", "--junitxml=" + xml, "--basetemp=" + root.resolve("scratch/" + name),
                "--rootdir=" + binding.assembly().graphRoot()));
        for (String module : modules) arguments.add(Path.of(binding.assembly().graphRoot()).resolve(module).toString());
        return new ConsumerGroupInput(kind, modules, refs, arguments, root.resolve(name + ".stdout.log").toString(),
                root.resolve(name + ".stderr.log").toString(), xml.toString());
    }
    static void requireScoreConsumers(ScoreConsumersObservation actual, ScoreInputs expected) throws IOException {
        if (actual == null || !"xar.sdk-score-whole-consumers/v1".equals(actual.schema()) || !"FULL_SOFTWARE".equals(actual.purpose())
                || actual.found() != 18 || actual.started() != 18 || actual.succeeded() != 18 || actual.failures() != 0
                || actual.errors() != 0 || actual.skipped() != 0 || actual.actualHttpProbeCalls() != 1
                || !actual.canonicalSameObject() || !actual.clientApisUnchanged() || !actual.actualHttpInvoked()
                || !"MATCH".equals(actual.sourcePostcheck()) || !expected.equals(actual.sources())
                || actual.probe() == null || !actual.probe().actualHttpInvoked() || !"stdlib-http-loopback/v1".equals(actual.probe().transportKind())
                || !actual.probe().requestId().startsWith("score18-") || !actual.probe().requestSha256().matches("[0-9a-f]{64}")
                || !actual.probe().responseSha256().matches("[0-9a-f]{64}") || actual.probe().httpCall() == null
                || !"xar.java-projection-http-call/v1".equals(actual.probe().httpCall().path("schema").asText())
                || !actual.probe().httpCall().path("actual_HTTP_call").isBoolean() || !actual.probe().httpCall().path("actual_HTTP_call").booleanValue())
            throw new IOException("Actual whole18 score/CLI consumers and unchanged canonical FULL_SOFTWARE client required");
    }
    private static void requireConsumerObservations(List<ConsumerGroupInput> expected, List<ConsumerGroupObservation> actual) throws IOException {
        if (actual.size() != expected.size()) throw new IOException("Every complete current consumer group must execute");
        for (int index = 0; index < expected.size(); index++) {
            var plan = expected.get(index); var observed = actual.get(index);
            if (observed.kind() != plan.kind() || observed.collectedParents() < 1 || observed.exitCode() != 0 || !"MATCH".equals(observed.sourcePostcheck())
                    || !observed.testSources().equals(plan.testSources())) throw new IOException("Complete consumer group failed or source changed");
        }
    }
    static void requireConsumerCounts(ConsumerGroupInput input, SupplementalFixtureCi.PytestCounts counts) throws IOException {
        SupplementalFixtureCi.requirePassed(counts);
        if (!counts.modules().stream().map(SupplementalFixtureCi.ModuleCount::path).toList().equals(input.modules()))
            throw new IOException("Whole consumer group module inventory differs");
        if (input.kind() == ConsumerGroupKind.BUDGET_COMPLETE_FILES && counts.modules().size() != 3
                || input.kind() == ConsumerGroupKind.M7_WHOLE11 && counts.modules().size() != 11
                || input.kind() == ConsumerGroupKind.M0_CURRENT_WHOLE90 && (counts.testcaseElements() != 90
                        || !counts.modules().stream().map(SupplementalFixtureCi.ModuleCount::parents).toList().equals(List.of(17, 7, 7, 8, 7, 3, 5, 19, 10, 7)))
                || input.kind() == ConsumerGroupKind.M0_LEGACY_FORMAL && counts.testcaseElements() != 4)
            throw new IOException("Complete M7/M0 consumer group count differs");
    }
    private static void requireCollectedCounts(List<ConsumerGroupObservation> observed, List<ConsumerGroupActual> actual) throws IOException {
        if (observed.size() != actual.size()) throw new IOException("Every collected complete consumer group requires its actual XML/count evidence");
        for (int index = 0; index < actual.size(); index++)
            if (observed.get(index).kind() != actual.get(index).kind() || observed.get(index).collectedParents() != actual.get(index).counts().testcaseElements())
                throw new IOException("Collected and executed complete consumer parent counts differ");
    }
    private static List<ConsumerGroupActual> readConsumerGroups(List<ConsumerGroupInput> inputs) throws IOException {
        List<ConsumerGroupActual> groups = new ArrayList<>();
        for (var input : inputs) {
            var out = ControlBuild.FileRef.measure(Path.of(input.stdoutPath())); var err = ControlBuild.FileRef.measure(Path.of(input.stderrPath()));
            var xml = ControlBuild.FileRef.measure(Path.of(input.junitPath()));
            var counts = SupplementalFixtureCi.readPytest(Path.of(xml.path()), Path.of(out.path()), input.modules()); requireConsumerCounts(input, counts);
            groups.add(new ConsumerGroupActual(input.kind(), out, err, xml, counts));
        }
        return List.copyOf(groups);
    }

    static int coldParents(SdkSourceAssembly.Digest source) throws IOException {
        if (COLD_ORIGINAL.equals(source)) return 59;
        if (COLD_JAVA_INSTALLED.equals(source)) return 63;
        throw new IOException("Unreviewed cold consumer source cannot inherit a parent count");
    }
    static void requireColdSourceCount(int expected, SdkSourceAssembly.Digest source) throws IOException {
        if (expected != coldParents(source)) throw new IOException("Configured cold count differs from exact selected whole source");
    }
    static List<String> pytestModules(Stage stage) {
        return switch (stage) {
            case IMPORT_PROBE -> List.of();
            case COMPLETE_COLD_FILE, INDEPENDENT_CONTINUATION -> List.of(COLD);
            case COMPLETE_CONTINUITY_FILES -> List.of(CROWN, CROWN_ORIGINAL, CONTINUITY, JAVA_CONTINUITY, PROJECTION_TEST);
        };
    }
    static List<String> importRoots(Stage stage, String graph, String sdk, String repository, List<String> dependencies) {
        List<String> roots = new ArrayList<>(List.of(graph, sdk));
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) {
            roots.add(Path.of(graph).resolve("ck3_autonomous_player/tests/unit").toString());
            roots.add(Path.of(graph).resolve("tools/g2_saved_campaign").toString());
        }
        roots.add(repository); roots.addAll(dependencies); return List.copyOf(roots);
    }
    static List<String> pytestArguments(Stage stage, Path graph, Path xml, Path temporary) {
        if (stage == Stage.IMPORT_PROBE) return List.of();
        List<String> arguments = new ArrayList<>(List.of("-q", "-ra", "--color=no", "-o", "verbosity_subtests=1", "-p", "no:cacheprovider", "--import-mode=importlib",
                "--junitxml=" + xml, "--basetemp=" + temporary));
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) arguments.add("--rootdir=" + graph);
        for (String module : pytestModules(stage)) arguments.add(graph.resolve(module) + (stage == Stage.INDEPENDENT_CONTINUATION ? "::" + CONTINUATION : ""));
        return List.copyOf(arguments);
    }
    static void requireCounts(Stage stage, SupplementalFixtureCi.PytestCounts counts, int expected) throws IOException {
        SupplementalFixtureCi.requirePassed(counts);
        if (stage == Stage.IMPORT_PROBE || !counts.modules().stream().map(SupplementalFixtureCi.ModuleCount::path).toList().equals(pytestModules(stage)))
            throw new IOException("Every selected complete module must execute actual parent tests");
        if (stage != Stage.COMPLETE_CONTINUITY_FILES && counts.testcaseElements() != (stage == Stage.INDEPENDENT_CONTINUATION ? 1 : expected))
            throw new IOException("Actual complete-file/independent continuation parent count differs");
        if (stage == Stage.COMPLETE_CONTINUITY_FILES && counts.modules().getLast().parents() != 55) throw new IOException("Complete projection client requires all fifty-five parent tests");
    }
    static void requireProjectionClientClasses(Path xml) throws IOException {
        int contract = 0, golden = 0, actualJava = 0;
        try {
            if (Files.size(xml) > 4 * MIB) throw new IOException("Bounded complete pytest XML required");
            var factory = javax.xml.parsers.DocumentBuilderFactory.newInstance();
            factory.setFeature(javax.xml.XMLConstants.FEATURE_SECURE_PROCESSING, true);
            factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_DTD, ""); factory.setAttribute(javax.xml.XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            var cases = factory.newDocumentBuilder().parse(xml.toFile()).getElementsByTagName("testcase");
            for (int index = 0; index < cases.getLength(); index++) {
                String classname = ((org.w3c.dom.Element) cases.item(index)).getAttribute("classname");
                switch (classname) {
                    case PROJECTION_TEST_MODULE + ".ProjectionClientContractTests" -> contract++;
                    case PROJECTION_TEST_MODULE + ".ProjectionClientG2ProducerGoldenTests" -> golden++;
                    case PROJECTION_TEST_MODULE + ".ProjectionClientActualJavaTests" -> actualJava++;
                    default -> {
                        if (classname.contains("test_java_projection_client_v1")) throw new IOException("Projection client parents must retain canonical class identity");
                    }
                }
            }
        } catch (javax.xml.parsers.ParserConfigurationException | org.xml.sax.SAXException failure) {
            throw new IOException("Invalid complete projection client class evidence", failure);
        }
        if (contract != 49 || golden != 4 || actualJava != 2) throw new IOException("All complete client classes must execute: 49 contract, 4 producer golden, 2 actual Java");
    }

    private static Binding bind(Config config) throws IOException {
        var views = SdkSourceAssembly.readViewsActual(config.viewsActualRef());
        if (!views.consumerActualRef().equals(config.selectedAssemblyActualRef())) throw new IOException("Exact selected CONSUMER view required");
        var assembly = SdkSourceAssembly.readActual(config.selectedAssemblyActualRef());
        if (!Path.of(assembly.canonicalTestRepository()).toRealPath().equals(absolute(config.canonicalRepository()).toRealPath())) throw new IOException("Explicit canonical support repository differs");
        var deployment = ControlBuild.acceptedReceipt(Path.of(config.deploymentReceiptRef().path()));
        if (assembly.deploymentClosure().stream().noneMatch(item -> item.actualBuildReceipt().equals(config.deploymentReceiptRef())
                && item.targetKind() == deployment.targetKind() && item.completeFiles().equals(deployment.completeDeployment()))) throw new IOException("Fresh view must bind this accepted deployment");
        Path work = absolute(config.workRoot());
        for (String root : List.of(assembly.graphRoot(), assembly.sdkRoot(), config.canonicalRepository())) {
            Path source = absolute(root); if (work.startsWith(source) || source.startsWith(work)) throw new IOException("Owned SDK output must be disjoint from source roots");
        }
        List<ExpectedModule> required = new ArrayList<>(); Set<String> sdk = new HashSet<>(), allowed = new HashSet<>(); List<ControlBuild.FileRef> sources = new ArrayList<>();
        for (var source : assembly.actualSourceClosure()) {
            sources.add(source.actual()); allowed.add(real(source.actual().path()));
            if (source.role() == SdkSourceAssembly.SourceRole.SDK_SOURCE) sdk.add(real(source.actual().path()));
            if (source.role() == SdkSourceAssembly.SourceRole.SHARED_TRANSPORT || source.role() == SdkSourceAssembly.SourceRole.PRODUCER)
                required.add(new ExpectedModule(source.relativePath().replace('/', '.').replaceFirst("[.]py$", ""), source.actual()));
        }
        var clientSources = assembly.actualSourceClosure().stream()
                .filter(row -> row.relativePath().equals(PROJECTION_CLIENT.replace('.', '/') + ".py")).toList();
        if (clientSources.size() != 1 || clientSources.getFirst().role() != SdkSourceAssembly.SourceRole.SHARED_TRANSPORT)
            throw new IOException("One canonical selected projection client must retain SHARED_TRANSPORT role");
        required = new ArrayList<>(requireSharedProducerModules(required, clientSources.getFirst().actual()));
        List<ExpectedModule> sdkFirst = new ArrayList<>();
        for (String name : List.of("xar_autoplayer", "xar_autoplayer.cold_checkpoint_validator", "xar_autoplayer.environment", "xar_autoplayer.runtime",
                "xar_autoplayer.native_session", "xar_autoplayer.bridge.native_driver", "xar_autoplayer.bridge.mcp_server", "xar_autoplayer.bridge.route_window_clock_v1")) {
            Path expected = Path.of(assembly.sdkRoot()).resolve(name.replace('.', '/') + (name.equals("xar_autoplayer") ? "/__init__.py" : ".py"));
            ControlBuild.FileRef source = assembly.actualSourceClosure().stream().map(SdkSourceAssembly.OutputSource::actual).filter(ref -> Path.of(ref.path()).equals(expected)).findFirst()
                    .orElseThrow(() -> new IOException("Required SDK import absent from exact source closure: " + name));
            sdkFirst.add(new ExpectedModule(name, source));
        }
        sdkFirst.addAll(required); required = sdkFirst;
        required = requiredModules(required, assembly.actualSourceClosure().stream().map(SdkSourceAssembly.OutputSource::actual).toList(), config.additionalRequiredModules());
        for (String test : List.of(COLD, CONTINUITY, JAVA_CONTINUITY, CROWN, CROWN_ORIGINAL, CROWN_ADAPTER, CROWN_NORMAL, PROJECTION_TEST)) if (assembly.actualSourceClosure().stream().noneMatch(source -> source.relativePath().equals(test))) throw new IOException("Fresh test/consumer module absent: " + test);
        var coldSource = assembly.actualSourceClosure().stream().filter(row -> row.relativePath().equals(COLD)).findFirst()
                .orElseThrow(() -> new IOException("Whole selected cold consumer source missing")).actual();
        requireColdSourceCount(config.expectedColdParents(), new SdkSourceAssembly.Digest(coldSource.bytes(), coldSource.sha256()));
        for (var ref : config.supportSources()) { if (!Path.of(ref.path()).toRealPath().startsWith(absolute(config.canonicalRepository()).toRealPath())) throw new IOException("Support source outside declared repository"); sources.add(ref); allowed.add(real(ref.path())); }
        for (var ref : config.dependencySources()) {
            boolean contained = false; for (String root : config.dependencyRoots()) {
                Path dependency = absolute(root).toRealPath(); if (work.startsWith(dependency) || dependency.startsWith(work)) throw new IOException("Owned output overlaps interpreter dependencies");
                if (Path.of(ref.path()).toRealPath().startsWith(dependency)) contained = true;
            }
            if (!contained) throw new IOException("Dependency source outside explicit roots"); sources.add(ref); allowed.add(real(ref.path()));
        }
        var bootstrap = RootSoftwareChildBootstrap.readConfiguration(config.rootBootstrapRef());
        sources.addAll(RootSoftwareChildBootstrap.inputRefs(bootstrap));
        var golden = readProducerGoldenPlan(config.producerGoldenPlanRef());
        var client = required.stream().filter(row -> row.module().equals(PROJECTION_CLIENT)).findFirst().orElseThrow(() -> new IOException("Selected canonical client required")).source();
        var test = assembly.actualSourceClosure().stream().filter(row -> row.relativePath().equals(PROJECTION_TEST)).findFirst().orElseThrow().actual();
        if (!golden.machineId().equals(config.machineId()) || !golden.clientContent().equals(new SdkSourceAssembly.Digest(client.bytes(), client.sha256()))
                || !golden.testContent().equals(new SdkSourceAssembly.Digest(test.bytes(), test.sha256())) || !bootstrap.client().source().equals(client))
            throw new IOException("One machine and selected client/test/Root bootstrap cohort required");
        sources.add(golden.originalInstallMapRef()); sources.addAll(producerGoldenInputs(golden));
        sources.addAll(List.of(config.pythonExecutable(), config.basePythonExecutable(), config.viewsActualRef(), config.selectedAssemblyActualRef(), config.deploymentReceiptRef(), config.supportContractRef(), config.executionCardRef(), config.rootBootstrapRef(), config.producerGoldenPlanRef()));
        sources.addAll(List.of(views.requestRef(), views.source32ReuseActualRef(), views.hardlinkAllocationActualRef(), views.storageEvidence()));
        sources.addAll(source32Metadata(read(Path.of(views.requestRef().path()), SdkSourceAssembly.ViewsRequest.class).source32Reuse(), views.sdkSourceViews()));
        return new Binding(assembly, List.copyOf(required), List.copyOf(sources), Set.copyOf(sdk), Set.copyOf(allowed));
    }

    static List<ControlBuild.FileRef> source32Metadata(SdkSourceAssembly.Source32Reuse reuse, List<SdkSourceAssembly.Source32View> views) throws IOException {
        List<ControlBuild.FileRef> refs = new ArrayList<>(List.of(reuse.baseFreezeRef(), reuse.exporterSourceRef()));
        for (var view : views) {
            refs.addAll(List.of(view.sdkFreezeRef(), view.source32AnchorRef(), view.assemblyActualRef()));
            if (view.role() == SdkSourceAssembly.SourceViewRole.CONSUMER
                    && SdkDerivedSource32.SCHEMA.equals(read(Path.of(view.sdkFreezeRef().path()), com.fasterxml.jackson.databind.JsonNode.class).path("schema").textValue())) {
                var lineage = SdkDerivedSource32.read(view.sdkFreezeRef());
                refs.addAll(List.of(lineage.parentFreezeRef(), lineage.parentAnchorRef(), lineage.assemblyActualRef()));
            }
        }
        return refs.stream().distinct().toList();
    }
    private static void validateObservation(Config config, Binding binding, Stage stage, Observation actual) throws IOException {
        if (!"xar.sdk-python-origin-observation/v7".equals(actual.schema()) || !actual.stage().equals(stage.name()) || actual.exitCode() != 0 || actual.error() != null
                || !real(actual.pythonExecutable()).equals(real(config.pythonExecutable().path())) || !real(actual.basePythonExecutable()).equals(real(config.basePythonExecutable().path()))
                || actual.pythonVersion().size() != 3 || actual.pythonVersion().get(0) != 3 || actual.pythonVersion().get(1) != 13
                || !actual.pytestVersion().equals("9.1.1") || !actual.mcpVersion().equals("2.0.0")) throw new IOException("Exact successful interpreter/pytest/MCP observation required");
        var bootstrap = RootSoftwareChildBootstrap.readConfiguration(config.rootBootstrapRef());
        RootSoftwareChildBootstrap.requireEvidence(bootstrap, actual.bootstrapEvidence());
        if (!config.rootBootstrapRef().equals(actual.bootstrapEvidence().bootstrapRef())) throw new IOException("Observed child bootstrap must bind this exact input reference");
        requireModuleOrigins(binding.required(), actual.before()); requireModuleOrigins(binding.required(), actual.after());
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) {
            requireScoreConsumers(actual.scoreConsumers(), scoreInputs(binding)); requireBudgetConsumers(actual.budgetConsumers(), budgetInputs(config, binding));
        } else if (actual.budgetConsumers() != null) throw new IOException("Budget whole consumers only execute after the admitted host exists");
        if (stage != Stage.COMPLETE_CONTINUITY_FILES && actual.scoreConsumers() != null) throw new IOException("Score consumers only execute in the retained host complete stage");
        requireConsumerObservations(consumerGroups(stage, binding, absolute(config.workRoot()).resolve(stage.name().toLowerCase(java.util.Locale.ROOT))), actual.completeConsumers());
        Path graph = Path.of(binding.assembly().graphRoot()).toRealPath(), sdkRoot = Path.of(binding.assembly().sdkRoot()).toRealPath();
        Path support = absolute(config.canonicalRepository()).toRealPath(), base = Path.of(config.basePythonExecutable().path()).toRealPath().getParent();
        if (!Path.of(actual.basePrefix()).toRealPath().equals(base)) throw new IOException("Observed base interpreter root differs");
        for (ModuleOrigin origin : actual.after()) {
            if (origin.module().equals("tools") || origin.module().equals("tools.g2_saved_campaign")) {
                if (origin.kind() != OriginKind.NAMESPACE || origin.file() != null || origin.namespacePaths().isEmpty()) throw new IOException("Fresh/support tools packages must remain observed namespaces");
                String relative = origin.module().replace('.', '/');
                for (String path : origin.namespacePaths()) if (!Path.of(path).toRealPath().equals(graph.resolve(relative).toRealPath()) && !Path.of(path).toRealPath().equals(support.resolve(relative).toRealPath())) throw new IOException("Unexpected tools namespace search path");
            }
            if (origin.file() == null) {
                if (origin.module().startsWith("xar_autoplayer")) throw new IOException("Actual SDK source origin missing");
                continue;
            }
            String path = real(origin.file());
            if (origin.module().equals("xar_autoplayer") || origin.module().startsWith("xar_autoplayer.")) {
                if (!Path.of(path).startsWith(sdkRoot) || !binding.sdkPaths().contains(path)) throw new IOException("SDK module loaded outside exact selected SDK source: " + origin.module());
            } else if (origin.module().equals("tools") || origin.module().startsWith("tools.")) {
                if (!binding.allowedPaths().contains(path)) throw new IOException("Undeclared actual support source: " + origin.module());
            } else if (!binding.allowedPaths().contains(path)) {
                Path source = Path.of(path);
                boolean interpreter = source.startsWith(base.resolve("Lib")) && !source.startsWith(base.resolve("Lib/site-packages")) || source.startsWith(base.resolve("DLLs"));
                if (!interpreter) throw new IOException("Undeclared external module source: " + origin.module() + " " + path);
            }
        }
        requireModuleOrigins(List.of(new ExpectedModule("tools.g2_saved_campaign.test_current_saved_campaign_cold_v1",
                source(binding, COLD))), stage == Stage.IMPORT_PROBE ? List.of() : actual.after(), stage == Stage.IMPORT_PROBE);
        requireModuleOrigins(List.of(new ExpectedModule("tools.g2_saved_campaign.test_current_saved_continuity_v1",
                source(binding, CONTINUITY))), stage == Stage.IMPORT_PROBE ? List.of() : actual.after(), stage == Stage.IMPORT_PROBE);
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) requireModuleOrigins(List.of(new ExpectedModule("tools.g2_saved_campaign.test_java_saved_continuity_v1",
                source(binding, JAVA_CONTINUITY))), actual.after());
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) requireModuleOrigins(List.of(
                new ExpectedModule("ck3_autonomous_player.tests.unit.test_crown_java_policy_consumers_v1", source(binding, CROWN)),
                new ExpectedModule("tools.g2_saved_campaign.test_pending_material_crown_schema_adapter_v1", source(binding, CROWN_ORIGINAL)),
                new ExpectedModule("pending_material_crown_schema_adapter_v1", source(binding, CROWN_ADAPTER)),
                new ExpectedModule("test_g2_normal_crown_service_compound_v1", source(binding, CROWN_NORMAL))), actual.after());
        if (stage == Stage.COMPLETE_CONTINUITY_FILES) {
            var budget = budgetInputs(config, binding); List<ExpectedModule> budgetModules = new ArrayList<>(List.of(budget.client(), budget.producer(),
                    new ExpectedModule("test_war_reinforcement_tradeoff_v1", budget.helperRef()))); budgetModules.addAll(budget.consumers());
            requireModuleOrigins(budgetModules, actual.after());
            var si = scoreInputs(binding); List<ExpectedModule> scoreModules = new ArrayList<>(List.of(si.client(), si.score(),
                    new ExpectedModule("test_campaign_development_score_v1", si.suiteRef()))); scoreModules.addAll(si.helpers());
            requireModuleOrigins(scoreModules, actual.after());
            var expected = new ExpectedModule(PROJECTION_TEST_MODULE, source(binding, PROJECTION_TEST));
            requireModuleOrigins(List.of(expected), actual.after());
            for (var origin : actual.after()) if (origin.file() != null && real(origin.file()).equals(real(expected.source().path())) && !origin.module().equals(PROJECTION_TEST_MODULE))
                throw new IOException("Collected projection test source must have only its canonical module instance");
        }
    }
    static void requireModuleOrigins(List<ExpectedModule> expected, List<ModuleOrigin> actual) throws IOException { requireModuleOrigins(expected, actual, false); }
    static List<ExpectedModule> requireSharedProducerModules(List<ExpectedModule> actual, ControlBuild.FileRef currentClient) throws IOException {
        var clients = actual.stream().filter(module -> module.module().equals(PROJECTION_CLIENT)).toList();
        if (clients.size() != 1 || !clients.getFirst().source().equals(currentClient)
                || actual.stream().filter(module -> !module.module().equals(PROJECTION_CLIENT)).count() != 15
                || actual.stream().map(ExpectedModule::module).distinct().count() != 16)
            throw new IOException("All fifteen original producer/shared imports plus one exact current canonical client required");
        return List.copyOf(actual);
    }
    static List<ExpectedModule> requiredModules(List<ExpectedModule> baseline, List<ControlBuild.FileRef> selectedSources,
            List<ExpectedModule> additional) throws IOException {
        List<ExpectedModule> result = new ArrayList<>(baseline); Set<String> names = new HashSet<>();
        for (var module : baseline) if (!names.add(module.module())) throw new IOException("Duplicate baseline module identity");
        for (var module : additional) {
            if (!names.add(module.module()) || !selectedSources.contains(module.source()) || !module.source().path().endsWith(".py"))
                throw new IOException("Additional actual consumer must select one exact source in this assembly: " + module.module());
            result.add(module);
        }
        return List.copyOf(result);
    }
    private static void requireModuleOrigins(List<ExpectedModule> expected, List<ModuleOrigin> actual, boolean notLoaded) throws IOException {
        if (notLoaded) return; Set<String> names = new HashSet<>(); for (var row : actual) if (!names.add(row.module())) throw new IOException("Duplicate actual module identity");
        for (var item : expected) {
            var rows = actual.stream().filter(row -> row.module().equals(item.module())).toList();
            if (rows.size() != 1 || rows.getFirst().file() == null || !real(rows.getFirst().file()).equals(real(item.source().path()))) throw new IOException("Selected fresh module actually loaded elsewhere: " + item.module());
            item.source().verify();
        }
    }
    private static ControlBuild.FileRef source(Binding binding, String relative) throws IOException {
        return binding.assembly().actualSourceClosure().stream().filter(row -> row.relativePath().equals(relative)).map(SdkSourceAssembly.OutputSource::actual).findFirst().orElseThrow(() -> new IOException("Fresh source missing"));
    }
    private static List<ControlBuild.FileRef> observedSources(Observation actual) throws IOException {
        Set<String> paths = new HashSet<>(); List<ControlBuild.FileRef> refs = new ArrayList<>();
        for (var origin : actual.after()) if (origin.file() != null && paths.add(real(origin.file()))) { SharedSourceFiles.plainAncestors(Path.of(origin.file())); refs.add(ControlBuild.FileRef.measure(Path.of(origin.file()).toRealPath())); }
        refs.sort(java.util.Comparator.comparing(ControlBuild.FileRef::path)); return List.copyOf(refs);
    }
    private static void verifyBinding(Config config, Binding binding) throws IOException {
        for (var ref : binding.sources()) ref.verify();
        List<String> roots = new ArrayList<>(List.of(binding.assembly().graphRoot(), binding.assembly().sdkRoot(), config.canonicalRepository())); roots.addAll(config.dependencyRoots());
        for (String root : roots) for (String relative : List.of("tools/__init__.py", "tools/g2_saved_campaign/__init__.py")) {
            Path initializer = absolute(root).resolve(relative); SharedSourceFiles.plainAncestors(initializer);
            try { Files.readAttributes(initializer, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS); throw new IOException("Regular package could hide fresh tools namespace: " + initializer); }
            catch (java.nio.file.NoSuchFileException absent) { /* Explicit namespace boundary, checked before imports. */ }
        }
        SdkSourceAssembly.readViewsActual(config.viewsActualRef()); SdkSourceAssembly.readActual(config.selectedAssemblyActualRef());
    }
    public static ControlBuild.FileRef requireAccepted(Path path, ResourceGuard resources) throws IOException {
        Actual actual = read(path, Actual.class); Config config = read(Path.of(actual.configRef().path()), Config.class); check(config, resources);
        Path work = absolute(config.workRoot()); SharedSourceFiles.plainAncestors(work);
        if (!path.toRealPath().equals(work.resolve("actual.json").toRealPath()) || !Path.of(actual.configRef().path()).toRealPath().equals(work.resolve("config.json").toRealPath())
                || !actual.schema().equals(SCHEMA) || actual.status() != SupplementalFixtureCi.Status.PASS || actual.error() != null || !actual.machineId().equals(config.machineId())
                || !actual.sourcePostcheck().equals("MATCH") || !actual.producerClosure().equals(ControlBuild.producerClosure()) || actual.commands().size() != Stage.values().length
                || actual.startupPublicProbe() != StartupProbeScope.NOT_RUN
                || actual.canonicalThirtyCommandStep() != CanonicalStepScope.NOT_RUN) throw new IOException("Complete owned fresh SDK actual required");
        Binding binding = bind(config); if (!binding.required().equals(actual.requiredFreshModules()) || !binding.sources().equals(actual.sourcePins())) throw new IOException("Exact selected-view/source custody differs");
        actual.configRef().verify(); for (var ref : actual.producerClosure()) ref.verify(); verifyBinding(config, binding);
        for (int index = 0; index < Stage.values().length; index++) {
            CommandActual command = actual.commands().get(index); Stage stage = Stage.values()[index]; Path root = work.resolve(stage.name().toLowerCase(java.util.Locale.ROOT));
            if (command.stage() != stage || command.consoleMode() != WindowsJobProcess.ConsoleMode.DETACHED || command.error() != null || !command.result().passed() || !command.fixtureCleanup().equals("BASIS_CLOSURE_CACHE_ABSENT_CONTINUITY_EMPTY")) throw new IOException("Actual complete stage failed");
            if (!real(command.result().identity().executable()).equals(real(config.pythonExecutable().path()))) throw new IOException("Actual SDK child executable differs");
            for (var ref : List.of(command.inputRef(), command.stdoutRef(), command.stderrRef(), command.observationRef())) ref.verify();
            for (var expected : List.of(new ExpectedModule("input", command.inputRef()), new ExpectedModule("stdout", command.stdoutRef()),
                    new ExpectedModule("stderr", command.stderrRef()), new ExpectedModule("origins", command.observationRef()))) {
                String suffix = expected.module().equals("input") || expected.module().equals("origins") ? ".json" : ".log";
                if (!real(expected.source().path()).equals(root.resolve(expected.module() + suffix).toRealPath().toString())) throw new IOException("Exact owned evidence path required");
            }
            List<String> roots = importRoots(stage, binding.assembly().graphRoot(), binding.assembly().sdkRoot(), config.canonicalRepository(), config.dependencyRoots());
            PythonInput expectedInput = new PythonInput("xar.sdk-python-origin-input/v7", stage, roots,
                    binding.required().stream().map(ExpectedModule::module).toList(), root.resolve("origins.json").toString(),
                    pytestArguments(stage, Path.of(binding.assembly().graphRoot()), root.resolve("pytest.xml"), root.resolve("scratch/pytest-temp")), config.rootBootstrapRef(),
                    config.producerGoldenPlanRef(), readProducerGoldenPlan(config.producerGoldenPlanRef()), source(binding, PROJECTION_TEST), stage == Stage.COMPLETE_CONTINUITY_FILES ? scoreInputs(binding) : null, stage == Stage.COMPLETE_CONTINUITY_FILES ? budgetInputs(config, binding) : null, m0Inputs(stage, binding, root), consumerGroups(stage, binding, root));
            if (!expectedInput.equals(read(Path.of(command.inputRef().path()), PythonInput.class))) throw new IOException("Actual fixed pytest/import plan differs");
            List<String> expectedArguments = List.of("-I", "-S", "-B", "-X", "utf8", "-X", "pycache_prefix=" + root.resolve("scratch/pycache-no-read"), "-c", OBSERVER, command.inputRef().path());
            if (!command.arguments().equals(expectedArguments)) throw new IOException("Actual independent SDK argv differs");
            Observation observed = read(Path.of(command.observationRef().path()), Observation.class); validateObservation(config, binding, stage, observed);
            if (!observedSources(observed).equals(command.observedSources())) throw new IOException("Actually imported source refs changed");
            requireAbsent(root.resolve("scratch/basis")); requireAbsent(root.resolve("scratch/closure")); requireAbsent(root.resolve("scratch/pycache-no-read"));
            SharedSourceFiles.plainAncestors(root.resolve("scratch/continuity/test-continuity"));
            try (var remaining = Files.list(root.resolve("scratch/continuity/test-continuity"))) { if (remaining.findAny().isPresent()) throw new IOException("Current continuity fixture is no longer empty"); }
            var completeGroups = readConsumerGroups(consumerGroups(stage, binding, root));
            requireCollectedCounts(observed.completeConsumers(), completeGroups);
            if (!completeGroups.equals(command.completeConsumers())) throw new IOException("Actual whole consumer XML/log/count refs changed");
            if (stage != Stage.IMPORT_PROBE) {
                command.junitRef().verify();
                if (!real(command.junitRef().path()).equals(root.resolve("pytest.xml").toRealPath().toString())) throw new IOException("Exact owned XML required");
                var counts = SupplementalFixtureCi.readPytest(Path.of(command.junitRef().path()), Path.of(command.stdoutRef().path()), pytestModules(stage));
                requireCounts(stage, counts, config.expectedColdParents());
                if (stage == Stage.COMPLETE_CONTINUITY_FILES) requireProjectionClientClasses(Path.of(command.junitRef().path()));
                if (!counts.equals(command.pytestCounts())) throw new IOException("Actual pytest counts changed");
            }
        }
        return ControlBuild.FileRef.measure(path);
    }
    private static void check(Config config, ResourceGuard resources) throws IOException {
        if (!WindowsJobProcess.currentMachineId().equals(config.machineId()) || !Instant.now().isBefore(Instant.parse(config.reviewAtUtc()))) throw new IOException("Fresh machine-bound SDK fixture lease required");
        if (!FreshSdkFixtureStage.class.getProtectionDomain().getCodeSource().getLocation().equals(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation())) throw new IOException("Fresh SDK stage must belong to the same qualified shared producer artifact");
        config.executionCardRef().verify(); resources.revalidate(0);
    }
    private static void unique(List<ControlBuild.FileRef> refs) { if (refs.stream().map(ControlBuild.FileRef::path).distinct().count() != refs.size()) throw new IllegalArgumentException("Unique explicit source pins required"); }
    private static Path absolute(String value) { Path path = Path.of(value); if (!path.isAbsolute() || !path.equals(path.normalize())) throw new IllegalArgumentException("Explicit normalized absolute path required"); return path; }
    private static String real(String value) throws IOException { SharedSourceFiles.plainAncestors(Path.of(value)); return Path.of(value).toRealPath().toString(); }
    private static void requireAbsent(Path path) throws IOException { SharedSourceFiles.plainAncestors(path); if (Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Fresh fixture/cache remains: " + path); }
    private static ControlBuild.FileRef maybe(Path path) throws IOException { return Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) ? ControlBuild.FileRef.measure(path) : null; }
    private static <T> T read(Path path, Class<T> type) throws IOException { SharedSourceFiles.plainAncestors(path); if (Files.size(path) > 4 * MIB) throw new IOException("Bounded SDK fixture metadata required"); return ControlBuild.strictMapper().readValue(Files.readAllBytes(path), type); }
    private static void write(Path path, Record value, Config config, ResourceGuard resources) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value);
        if (bytes.length > 4 * MIB) throw new IOException("Bounded SDK fixture metadata required");
        try { check(config, resources); resources.revalidate(bytes.length); SharedSourceFiles.plainAncestors(path); Files.write(path, bytes, StandardOpenOption.CREATE_NEW); }
        catch (IOException unavailable) {
            if (value instanceof Actual actual) {
                var tree = ControlBuild.strictMapper().valueToTree(actual);
                if (tree instanceof com.fasterxml.jackson.databind.node.ObjectNode node) {
                    node.put("status", SupplementalFixtureCi.Status.RED.name()); node.put("error", append(actual.error(), "Owned metadata unavailable: " + unavailable.getMessage()));
                    Actual red = ControlBuild.strictMapper().treeToValue(node, Actual.class);
                    byte[] fallback = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(red);
                    if (fallback.length <= 4 * MIB) System.err.println(new String(fallback, StandardCharsets.UTF_8));
                }
            }
            throw unavailable;
        }
    }
    private static String append(String current, String next) { return current == null ? next : current + "; " + next; }
}
