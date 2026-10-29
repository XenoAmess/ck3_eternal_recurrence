package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Set;

import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;

import com.fasterxml.jackson.databind.JsonNode;

public final class RootOrdinaryRuntimeConfiguration {

    private static final Set<String> REQUIRED_ROOT_FIELDS = Set.of(
        "schema", "machine_id", "state_dir", "stock_game_root", "native_implementation",
        "launch_plan_file", "initial_policy_file", "campaign_deadline_file",
        "formal_war_budget", "formal_war_model", "configured_build", "authority_id"
    );

    private static final Set<String> OPTIONAL_ROOT_FIELDS = Set.of(
        "stop_path", "retained_frames", "retained_origins", "operation_timeout_ms",
        "freshness_ms", "heartbeat_maximum_age_ms", "batch_id_prefix", "maximum_turns",
        "batch_wall_ms", "readiness_timeout_ms", "poll_interval_ms", "checkpoint_every_advances",
        "maximum_frames_per_operation", "maximum_submissions", "maximum_storage_bytes"
    );

    private final Path configurationFile;
    private final String machineId;
    private final Path stateDirectory;
    private final Path stockGameRoot;
    private final Path nativeImplementation;
    private final Path launchPlanFile;
    private final Path campaignDeadlineFile;
    private final Path stopPath;
    private final Path formalWarBudget;
    private final Path formalWarModel;
    private final FrontendRulesData.Build configuredBuild;
    private final InitialEpisodePolicy initialPolicy;
    private final String authorityId;
    private final int retainedFrames;
    private final int retainedOrigins;
    private final Duration operationTimeout;
    private final Duration freshness;
    private final Duration heartbeatMaximumAge;
    private final int maximumFramesPerOperation;
    private final int maximumSubmissions;
    private final long maximumStorageBytes;
    private final RootOrdinaryWorkerLoop.Configuration loopConfig;

    public static RootOrdinaryRuntimeConfiguration read(Path configPath) throws IOException {
        try {
            return decode(configPath);
        } catch (IllegalArgumentException invalid) {
            throw new IOException("Invalid ordinary runtime configuration: " + configPath, invalid);
        }
    }

    private static RootOrdinaryRuntimeConfiguration decode(Path configPath) throws IOException {
        Path absoluteConfigPath = configPath.toAbsolutePath().normalize();
        Path configParent = absoluteConfigPath.getParent();

        byte[] configBytes = readBoundedFile(absoluteConfigPath);
        JsonNode root;
        try {
            root = StrictJson.parse(configBytes, StrictJson.EXPLICIT_MAX_BYTES);
        } catch (Exception e) {
            throw new IOException("Invalid configuration JSON: " + e.getMessage(), e);
        }

        StrictJson.object(root, REQUIRED_ROOT_FIELDS, OPTIONAL_ROOT_FIELDS);

        String schema = StrictJson.text(root.get("schema"));
        if (!schema.equals("xar.java-ordinary-runtime-configuration/v1")) {
            throw new IOException("Unsupported schema: " + schema);
        }

        String machineId = StrictJson.text(root.get("machine_id"));
        Path stateDirectory = resolvePath(root.get("state_dir"), configParent);
        Path stockGameRoot = resolvePath(root.get("stock_game_root"), configParent);
        Path nativeImplementation = resolvePath(root.get("native_implementation"), configParent);
        Path launchPlanFile = resolvePath(root.get("launch_plan_file"), configParent);
        Path campaignDeadlineFile = resolvePath(root.get("campaign_deadline_file"), configParent);
        Path formalWarBudget = resolvePath(root.get("formal_war_budget"), configParent);
        Path formalWarModel = resolvePath(root.get("formal_war_model"), configParent);
        String authorityId = StrictJson.text(root.get("authority_id"));

        JsonNode buildNode = StrictJson.object(root.get("configured_build"), Set.of("version", "exe_sha256"));
        String buildVersion = StrictJson.text(buildNode.get("version"));
        String buildSha = StrictJson.text(buildNode.get("exe_sha256"));
        FrontendRulesData.Build configuredBuild = FrontendRulesData.Build.require(buildVersion, buildSha);

        Path stopPath;
        if (root.has("stop_path")) {
            stopPath = resolvePath(root.get("stop_path"), configParent);
        } else {
            stopPath = stateDirectory.resolve("worker-stop.request");
        }

        int retainedFrames = root.has("retained_frames") ? (int) StrictJson.integer(root.get("retained_frames"), 1, Integer.MAX_VALUE) : 16;
        int retainedOrigins = root.has("retained_origins") ? (int) StrictJson.integer(root.get("retained_origins"), 1, Integer.MAX_VALUE) : 128;
        long opTimeoutMs = root.has("operation_timeout_ms") ? StrictJson.integer(root.get("operation_timeout_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 30000L;
        long freshnessMs = root.has("freshness_ms") ? StrictJson.integer(root.get("freshness_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 5000L;
        long heartbeatMaxAgeMs = root.has("heartbeat_maximum_age_ms") ? StrictJson.integer(root.get("heartbeat_maximum_age_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 10000L;

        int maximumFramesPerOperation = root.has("maximum_frames_per_operation") ? (int) StrictJson.integer(root.get("maximum_frames_per_operation"), 1, 65536) : 65536;
        int maximumSubmissions = root.has("maximum_submissions") ? (int) StrictJson.integer(root.get("maximum_submissions"), 1, 1000000) : 1000000;

        long maximumStorageBytes = root.has("maximum_storage_bytes") ? StrictJson.integer(root.get("maximum_storage_bytes"), 1, StrictJson.MAX_SAFE_INTEGER) : 2_147_483_648L;

        String batchIdPrefix = root.has("batch_id_prefix") ? StrictJson.text(root.get("batch_id_prefix")) : "ordinary";
        int maximumTurns = root.has("maximum_turns") ? (int) StrictJson.integer(root.get("maximum_turns"), 1, Integer.MAX_VALUE) : 32;
        long batchWallMs = root.has("batch_wall_ms") ? StrictJson.integer(root.get("batch_wall_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 300000L;
        long readinessTimeoutMs = root.has("readiness_timeout_ms") ? StrictJson.integer(root.get("readiness_timeout_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 30000L;
        long pollIntervalMs = root.has("poll_interval_ms") ? StrictJson.integer(root.get("poll_interval_ms"), 1, StrictJson.MAX_SAFE_INTEGER) : 250L;
        int checkpointEveryAdvances = root.has("checkpoint_every_advances") ? (int) StrictJson.integer(root.get("checkpoint_every_advances"), 1, Integer.MAX_VALUE) : 1;

        RootOrdinaryWorkerLoop.Configuration loopConfig = new RootOrdinaryWorkerLoop.Configuration(
            batchIdPrefix,
            maximumTurns,
            Duration.ofMillis(batchWallMs),
            Duration.ofMillis(readinessTimeoutMs),
            Duration.ofMillis(pollIntervalMs),
            checkpointEveryAdvances
        );

        Path initialPolicyFile = resolvePath(root.get("initial_policy_file"), configParent);
        InitialEpisodePolicy initialPolicy = readInitialPolicy(initialPolicyFile);

        return new RootOrdinaryRuntimeConfiguration(
            absoluteConfigPath,
            machineId,
            stateDirectory,
            stockGameRoot,
            nativeImplementation,
            launchPlanFile,
            campaignDeadlineFile,
            stopPath,
            formalWarBudget,
            formalWarModel,
            configuredBuild,
            initialPolicy,
            authorityId,
            retainedFrames,
            retainedOrigins,
            Duration.ofMillis(opTimeoutMs),
            Duration.ofMillis(freshnessMs),
            Duration.ofMillis(heartbeatMaxAgeMs),
            maximumFramesPerOperation,
            maximumSubmissions,
            maximumStorageBytes,
            loopConfig
        );
    }

    private static byte[] readBoundedFile(Path path) throws IOException {
        try (var stream = Files.newInputStream(path)) {
            byte[] bytes = stream.readNBytes(StrictJson.EXPLICIT_MAX_BYTES + 1);
            if (bytes.length > StrictJson.EXPLICIT_MAX_BYTES) {
                throw new IOException("File exceeds 1 MiB limit: " + path);
            }
            return bytes;
        }
    }

    private static Path resolvePath(JsonNode node, Path base) {
        String pathStr = StrictJson.text(node);
        Path p = Path.of(pathStr);
        if (!p.isAbsolute()) {
            p = base.resolve(p);
        }
        return p.normalize();
    }

    private static InitialEpisodePolicy readInitialPolicy(Path policyPath) throws IOException {
        byte[] policyBytes = readBoundedFile(policyPath);
        JsonNode policyRoot;
        try {
            policyRoot = StrictJson.parse(policyBytes, StrictJson.EXPLICIT_MAX_BYTES);
        } catch (Exception e) {
            throw new IOException("Invalid initial policy JSON: " + e.getMessage(), e);
        }

        if (!policyRoot.isObject()) {
            throw new IOException("Initial policy root must be a JSON object");
        }

        JsonNode lifecycleNode = policyRoot.get("succession_lifecycle");
        if (lifecycleNode == null || !lifecycleNode.isObject()) {
            throw new IOException("Missing or invalid succession_lifecycle object");
        }

        String lifecycleKind = StrictJson.text(lifecycleNode.get("lifecycle"));
        InitialEpisodePolicy.Lifecycle lifecycle;
        switch (lifecycleKind) {
            case "rogue_one_life":
                lifecycle = InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE;
                break;
            case "ordinary_campaign_succession":
                lifecycle = InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION;
                break;
            default:
                throw new IOException("Unsupported lifecycle: " + lifecycleKind);
        }

        RawJson lifecycleRaw = new RawJson(StrictJson.canonical(lifecycleNode));
        return InitialEpisodePolicy.ordinary(lifecycle, lifecycleRaw);
    }

    private RootOrdinaryRuntimeConfiguration(
        Path configurationFile,
        String machineId,
        Path stateDirectory,
        Path stockGameRoot,
        Path nativeImplementation,
        Path launchPlanFile,
        Path campaignDeadlineFile,
        Path stopPath,
        Path formalWarBudget,
        Path formalWarModel,
        FrontendRulesData.Build configuredBuild,
        InitialEpisodePolicy initialPolicy,
        String authorityId,
        int retainedFrames,
        int retainedOrigins,
        Duration operationTimeout,
        Duration freshness,
        Duration heartbeatMaximumAge,
        int maximumFramesPerOperation,
        int maximumSubmissions,
        long maximumStorageBytes,
        RootOrdinaryWorkerLoop.Configuration loopConfig
    ) {
        this.configurationFile = configurationFile;
        this.machineId = machineId;
        this.stateDirectory = stateDirectory;
        this.stockGameRoot = stockGameRoot;
        this.nativeImplementation = nativeImplementation;
        this.launchPlanFile = launchPlanFile;
        this.campaignDeadlineFile = campaignDeadlineFile;
        this.stopPath = stopPath;
        this.formalWarBudget = formalWarBudget;
        this.formalWarModel = formalWarModel;
        this.configuredBuild = configuredBuild;
        this.initialPolicy = initialPolicy;
        this.authorityId = authorityId;
        this.retainedFrames = retainedFrames;
        this.retainedOrigins = retainedOrigins;
        this.operationTimeout = operationTimeout;
        this.freshness = freshness;
        this.heartbeatMaximumAge = heartbeatMaximumAge;
        this.maximumFramesPerOperation = maximumFramesPerOperation;
        this.maximumSubmissions = maximumSubmissions;
        this.maximumStorageBytes = maximumStorageBytes;
        this.loopConfig = loopConfig;
    }

    public Path configurationFile() { return configurationFile; }
    public String machineId() { return machineId; }
    public Path stateDirectory() { return stateDirectory; }
    public Path stockGameRoot() { return stockGameRoot; }
    public Path nativeImplementation() { return nativeImplementation; }
    public Path launchPlanFile() { return launchPlanFile; }
    public Path campaignDeadlineFile() { return campaignDeadlineFile; }
    public Path stopPath() { return stopPath; }
    public Path formalWarBudget() { return formalWarBudget; }
    public Path formalWarModel() { return formalWarModel; }
    public FrontendRulesData.Build configuredBuild() { return configuredBuild; }
    public InitialEpisodePolicy initialPolicy() { return initialPolicy; }
    public String authorityId() { return authorityId; }
    public int retainedFrames() { return retainedFrames; }
    public int retainedOrigins() { return retainedOrigins; }
    public Duration operationTimeout() { return operationTimeout; }
    public Duration freshness() { return freshness; }
    public Duration heartbeatMaximumAge() { return heartbeatMaximumAge; }
    public int maximumFramesPerOperation() { return maximumFramesPerOperation; }
    public int maximumSubmissions() { return maximumSubmissions; }
    public long maximumStorageBytes() { return maximumStorageBytes; }
    public RootOrdinaryWorkerLoop.Configuration loop() { return loopConfig; }
}
