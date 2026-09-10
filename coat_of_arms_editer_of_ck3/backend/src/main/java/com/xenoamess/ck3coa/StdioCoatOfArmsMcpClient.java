package com.xenoamess.ck3coa;

import io.modelcontextprotocol.client.McpClient;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.client.transport.ServerParameters;
import io.modelcontextprotocol.client.transport.StdioClientTransport;
import io.modelcontextprotocol.json.McpJsonDefaults;
import io.modelcontextprotocol.spec.McpSchema.CallToolRequest;
import io.modelcontextprotocol.spec.McpSchema.CallToolResult;
import jakarta.annotation.PreDestroy;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@ApplicationScoped
public class StdioCoatOfArmsMcpClient implements CoatOfArmsMcpClient {
    private static final Set<String> REQUIRED_TOOLS = Set.of(
            "ck3_take_snapshot",
            "ck3_probe_coat_of_arms_source_v1",
            "ck3_export_coat_of_arms_source_v1",
            "ck3_query_coat_of_arms_resource_catalog_v1",
            "ck3_read_coat_of_arms_resource_asset_v1",
            "ck3_read_coat_of_arms_render_support_v1",
            "ck3_query_coat_of_arms_load_configuration_v1");

    private final McpConfiguration configuration;
    private McpSyncClient client;

    @Inject
    public StdioCoatOfArmsMcpClient(McpConfiguration configuration) {
        this.configuration = configuration;
    }

    @Override
    public synchronized Object callTool(
            String toolName,
            Map<String, Object> arguments) {
        if (!REQUIRED_TOOLS.contains(toolName)) {
            throw new IllegalArgumentException("tool is outside the coat-of-arms allowlist");
        }
        try {
            CallToolResult result = client().callTool(
                    CallToolRequest.builder(toolName)
                            .arguments(arguments)
                            .build());
            if (Boolean.TRUE.equals(result.isError())) {
                throw new McpGatewayException("MCP tool returned an error: " + toolName);
            }
            if (result.structuredContent() == null) {
                throw new McpGatewayException(
                        "MCP tool returned no structured content: " + toolName);
            }
            return result.structuredContent();
        } catch (McpGatewayException | IllegalArgumentException error) {
            throw error;
        } catch (RuntimeException error) {
            resetClient();
            throw new McpGatewayException("MCP stdio request failed", error);
        }
    }

    private McpSyncClient client() {
        if (client != null) {
            return client;
        }
        String pythonPath = requireConfigured("pythonPath", configuration.pythonPath());
        String stateDirectory = requireConfigured(
                "stateDirectory", configuration.stateDirectory());
        String gameDirectory = requireConfigured(
                "gameDirectory", configuration.gameDirectory());

        List<String> arguments = new ArrayList<>(List.of(
                "-m",
                "xar_autoplayer.bridge.mcp_server",
                "--driver",
                configuration.driver(),
                "--state-dir",
                stateDirectory));
        configuration.pipeName().filter(value -> !value.isBlank()).ifPresent(value -> {
            arguments.add("--pipe-name");
            arguments.add(value);
        });
        ServerParameters parameters = ServerParameters
                .builder(configuration.pythonCommand())
                .args(arguments)
                .addEnvVar("PYTHONPATH", pythonPath)
                .addEnvVar("XAR_CK3_GAME_DIR", gameDirectory)
                .build();
        StdioClientTransport transport = new StdioClientTransport(
                parameters,
                McpJsonDefaults.getMapper());
        McpSyncClient candidate = McpClient.sync(transport)
                .requestTimeout(configuration.requestTimeout())
                .build();
        try {
            candidate.initialize();
            Set<String> available = candidate.listTools().tools().stream()
                    .map(tool -> tool.name())
                    .collect(Collectors.toUnmodifiableSet());
            if (!available.containsAll(REQUIRED_TOOLS)) {
                throw new McpGatewayException(
                        "MCP server lacks required coat-of-arms tools");
            }
        } catch (RuntimeException error) {
            try {
                candidate.closeGracefully();
            } catch (RuntimeException closeError) {
                error.addSuppressed(closeError);
            }
            throw error;
        }
        client = candidate;
        return client;
    }

    private static String requireConfigured(
            String name,
            java.util.Optional<String> value) {
        if (value.isEmpty() || value.get().isBlank()) {
            throw new McpGatewayException("missing companion configuration: " + name);
        }
        return value.get();
    }

    private void resetClient() {
        if (client == null) {
            return;
        }
        try {
            client.closeGracefully();
        } finally {
            client = null;
        }
    }

    @PreDestroy
    void close() {
        resetClient();
    }
}
