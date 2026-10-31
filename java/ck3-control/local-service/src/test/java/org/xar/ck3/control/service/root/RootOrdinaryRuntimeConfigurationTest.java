package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;

final class RootOrdinaryRuntimeConfigurationTest {
    @TempDir Path directory;

    @Test void actualProducerDecodesPathsPolicyAndLoopWithoutOpeningMetadataReferences() throws Exception {
        var root = configuration();
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertEquals(directory.resolve("state").normalize(), actual.stateDirectory());
        assertEquals(directory.resolve("war/budget.json").normalize(), actual.formalWarBudget());
        assertEquals(directory.resolve("war/model.json").normalize(), actual.formalWarModel());
        assertEquals(directory.resolve("state/worker-stop.request").normalize(), actual.stopPath());
        assertEquals(32, actual.loop().maximumTurns());
        assertEquals(2_147_483_648L, actual.maximumStorageBytes());
        assertEquals(InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE, actual.initialPolicy().kind());
        assertArrayEquals(StrictJson.canonical(lifecycle()), actual.initialPolicy().lifecycle().bytes());
        assertTrue(actual.initialPolicy().optionalSource().isEmpty());
        assertTrue(actual.initialPolicy().optionalEnvironment().isEmpty());
        assertFalse(Files.exists(directory.resolve("war/budget.json")));
    }
    @Test void configuredAttachBudgetsReachTypedConsumer() throws Exception {
        var root = configuration().put("maximum_frames_per_operation", 35).put("maximum_submissions", 47).put("maximum_storage_bytes", 91L);
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertEquals(35, actual.maximumFramesPerOperation());
        assertEquals(47, actual.maximumSubmissions());
        assertEquals(91L, actual.maximumStorageBytes());
    }
    @Test void floatBooleanAndStringNeverBecomeIntegerDefaults() throws Exception {
        var root = configuration().put("retained_frames", 2.0);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)));
        root.put("retained_frames", true);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)));
        root.put("retained_frames", "2");
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)));
    }
    @Test void duplicateFieldsAreRejectedByActualStrictParser() throws Exception {
        Path path = write(configuration());
        String raw = Files.readString(path, StandardCharsets.UTF_8);
        raw = raw.replace("\"machine_id\":\"fixture-machine\"", "\"machine_id\":\"fixture-machine\",\"machine_id\":\"other\"");
        Files.writeString(path, raw, StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(path));
    }
    @Test void missingSchemaAndUnknownFieldsAreRejected() throws Exception {
        var missing = configuration(); missing.remove("schema");
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(missing)));
        var unknown = configuration().put("unexpected_legacy_gate", true);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(unknown)));
    }
    @Test void warSourcesRemainPathsAndNullIsNotMissing() throws Exception {
        var root = configuration().put("formal_war_budget", 100);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)));
        var withNull = configuration(); withNull.putNull("stop_path");
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(withNull)));
    }
    @Test void realLifecycleFieldIsRequiredAndFixtureKindIsNotOrdinary() throws Exception {
        Path path = write(configuration());
        var policy = StrictJson.object(); var wrong = lifecycle(); wrong.remove("lifecycle"); wrong.put("kind", "rogue_one_life");
        policy.set("succession_lifecycle", wrong); Files.write(directory.resolve("policy.json"), StrictJson.canonical(policy));
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(path));
        wrong = lifecycle().put("lifecycle", "native_campaign_fixture"); policy.set("succession_lifecycle", wrong);
        Files.write(directory.resolve("policy.json"), StrictJson.canonical(policy));
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(path));
    }
    @Test void boundedReadRejectsOversizeBeforeUnboundedAllocation() throws Exception {
        Path path = directory.resolve("too-large.json"); Files.write(path, new byte[StrictJson.EXPLICIT_MAX_BYTES + 1]);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(path));
    }

    @Test void ordinaryVanillaFactoryPolicyReadsAsConfiguredData() throws Exception {
        var root = configuration();
        var factoryLifecycle = org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla();
        var lifecycleNode = factoryLifecycle.toJson();
        var policy = StrictJson.object();
        policy.set("succession_lifecycle", lifecycleNode);
        Files.write(directory.resolve("policy.json"), StrictJson.canonical(policy));
        
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        
        assertEquals(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION, actual.initialPolicy().kind());
        assertArrayEquals(StrictJson.canonical(lifecycleNode), actual.initialPolicy().lifecycle().bytes());
        assertTrue(actual.initialPolicy().optionalSource().isEmpty());
        assertTrue(actual.initialPolicy().optionalEnvironment().isEmpty());
        var actualLifecycle = StrictJson.parse(actual.initialPolicy().lifecycle().bytes(), 65536);
        assertTrue(actualLifecycle.get("environment_sha256").isNull());
        assertTrue(actualLifecycle.get("xar_enabled").isNull());
        
        assertThrows(java.io.IOException.class, () -> actual.initialPolicy().verify());
        assertThrows(IllegalStateException.class, () -> actual.initialPolicy().source());
        assertThrows(IllegalStateException.class, () -> actual.initialPolicy().environment());
    }

    @Test void ordinaryPolicyRejectsInvalidEnvironmentSha256Tokens() throws Exception {
        var root = configuration();
        var policy = StrictJson.object();
        var baseLifecycle = org.xar.ck3.control.contracts.NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson();
        
        var tokens = java.util.List.of("true", "123", "1.5", "{}", "[]");
        for (var token : tokens) {
            var lifecycleNode = baseLifecycle.deepCopy();
            lifecycleNode.set("environment_sha256", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8), 1024));
            policy.set("succession_lifecycle", lifecycleNode);
            Files.writeString(directory.resolve("policy.json"), policy.toString(), StandardCharsets.UTF_8);
            assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)), "reject token: " + token);
        }
        
        var missingLifecycle = baseLifecycle.deepCopy();
        missingLifecycle.remove("environment_sha256");
        policy.set("succession_lifecycle", missingLifecycle);
        Files.writeString(directory.resolve("policy.json"), policy.toString(), StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> RootOrdinaryRuntimeConfiguration.read(write(root)), "reject missing environment_sha256");
    }

    @Test void decisionProviderOmittedAttemptsAndBackoffUseDefaults() throws Exception {
        var root = configuration();
        var provider = StrictJson.object().put("endpoint", "http://127.0.0.1:8080/v1").put("model", "qwen38-coder").put("timeout_ms", 5000);
        root.set("decision_provider", provider);
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertTrue(actual.decisionProvider().isPresent());
        var dp = actual.decisionProvider().get();
        assertEquals(6, dp.maximumAttempts());
        assertEquals(java.time.Duration.ofSeconds(10), dp.retryBackoff());
    }

    @Test void decisionProviderExplicitAttemptsAndBackoffArePreserved() throws Exception {
        var root = configuration();
        var provider = StrictJson.object().put("endpoint", "http://127.0.0.1:8080/v1").put("model", "qwen38-coder").put("timeout_ms", 5000)
                .put("maximum_attempts", 1).put("retry_backoff_ms", 0);
        root.set("decision_provider", provider);
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertTrue(actual.decisionProvider().isPresent());
        var dp = actual.decisionProvider().get();
        assertEquals(1, dp.maximumAttempts());
        assertEquals(java.time.Duration.ofMillis(0), dp.retryBackoff());

        root = configuration();
        provider = StrictJson.object().put("endpoint", "http://127.0.0.1:8080/v1").put("model", "qwen38-coder").put("timeout_ms", 5000)
                .put("maximum_attempts", 4).put("retry_backoff_ms", 7);
        root.set("decision_provider", provider);
        actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertTrue(actual.decisionProvider().isPresent());
        dp = actual.decisionProvider().get();
        assertEquals(4, dp.maximumAttempts());
        assertEquals(java.time.Duration.ofMillis(7), dp.retryBackoff());
    }

    @Test void decisionProviderAbsentIsEmpty() throws Exception {
        var root = configuration();
        var actual = RootOrdinaryRuntimeConfiguration.read(write(root));
        assertTrue(actual.decisionProvider().isEmpty());
    }

    private ObjectNode configuration() throws IOException {
        var policy = StrictJson.object(); policy.set("succession_lifecycle", lifecycle());
        policy.put("environment_manifest", "deliberately-does-not-exist.json");
        Files.write(directory.resolve("policy.json"), StrictJson.canonical(policy));
        var root = StrictJson.object().put("schema", "xar.java-ordinary-runtime-configuration/v1")
                .put("machine_id", "fixture-machine").put("state_dir", "state")
                .put("stock_game_root", "stock").put("native_implementation", "native/bridge.dll")
                .put("launch_plan_file", "launch.json").put("initial_policy_file", "policy.json")
                .put("campaign_deadline_file", "campaign.json").put("formal_war_budget", "war/budget.json")
                .put("formal_war_model", "war/model.json").put("authority_id", "ordinary-fixture");
        root.set("configured_build", StrictJson.object().put("version", FrontendRulesData.Build.CK3_12004.version())
                .put("exe_sha256", FrontendRulesData.Build.CK3_12004.sha256()));
        return root;
    }
    private ObjectNode lifecycle() {
        return StrictJson.object().put("schema", "xar.ck3.succession-lifecycle-binding/v1")
                .put("lifecycle", "rogue_one_life").put("xar_enabled", "xar_on")
                .put("pact_contract", "terminal_settlement_required").put("source", "fixture-business-metadata")
                .put("environment_sha256", "opaque-metadata-not-a-source-qualification");
    }
    private Path write(ObjectNode root) throws IOException {
        Path path = directory.resolve("ordinary.json"); Files.writeString(path, root.toString(), StandardCharsets.UTF_8); return path;
    }
}
