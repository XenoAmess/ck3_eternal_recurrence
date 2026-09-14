package com.xenoamess.ck3coa;

import jakarta.inject.Inject;
import jakarta.ws.rs.BadRequestException;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DefaultValue;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import java.util.LinkedHashMap;
import java.util.Map;

@Path("/api/ck3/coat-of-arms")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class CoatOfArmsResource {
    private static final String COAT_OF_ARMS_PROBE_CAPABILITY =
            "game.command.probe-coat-of-arms-source-v1";
    private static final String COAT_OF_ARMS_EXPORT_CAPABILITY =
            "game.command.export-coat-of-arms-source-v1";
    private static final String EXPECTED_GAME_VERSION = "1.19.0.6";
    private static final String EXPECTED_EXECUTABLE_SHA256 =
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

    private final CoatOfArmsMcpClient mcp;
    private final McpConfiguration configuration;

    @Inject
    public CoatOfArmsResource(
            CoatOfArmsMcpClient mcp,
            McpConfiguration configuration) {
        this.mcp = mcp;
        this.configuration = configuration;
    }

    @GET
    @Path("/session")
    public Object session() {
        return mcp.callTool("ck3_take_snapshot", Map.of());
    }

    @GET
    @Path("/binding")
    public Object sourceBinding() {
        Map<?, ?> capabilities = requireMap(
                mcp.callTool("ck3_get_capabilities", Map.of()),
                "MCP capabilities");
        if (!"native-headless".equals(capabilities.get("backend_id"))
                || !"native-headless".equals(capabilities.get("mode"))
                || !"injected-dll-named-pipe".equals(capabilities.get("source"))
                || !Boolean.FALSE.equals(capabilities.get("visual_fallback"))
                || !containsString(
                        capabilities.get("bridge_capabilities"),
                        COAT_OF_ARMS_PROBE_CAPABILITY)
                || !containsString(
                        capabilities.get("bridge_capabilities"),
                        COAT_OF_ARMS_EXPORT_CAPABILITY)) {
            throw new McpGatewayException(
                    "MCP capabilities do not expose the exact native CoA binding");
        }
        Map<?, ?> diagnostics = requireMap(
                capabilities.get("diagnostics"), "MCP diagnostics");
        Map<?, ?> hello = requireMap(diagnostics.get("hello"), "MCP hello");
        long connectionGeneration = positiveLong(
                diagnostics.get("connection_generation"),
                "MCP connection generation");
        long bridgePid = positiveLong(
                diagnostics.get("bridge_pid"), "MCP bridge PID");
        if (!Boolean.TRUE.equals(diagnostics.get("connected"))
                || !Boolean.TRUE.equals(hello.get("ck3_build_match"))
                || !"ready".equals(hello.get("game_adapter_status"))
                || !EXPECTED_GAME_VERSION.equals(hello.get("expected_ck3_version"))
                || !EXPECTED_EXECUTABLE_SHA256.equals(
                        hello.get("expected_ck3_sha256"))
                || positiveLong(
                        hello.get("connection_generation"),
                        "MCP hello connection generation") != connectionGeneration
                || positiveLong(hello.get("pid"), "MCP hello PID") != bridgePid
                || !containsString(
                        hello.get("capabilities"), COAT_OF_ARMS_PROBE_CAPABILITY)
                || !containsString(
                        hello.get("capabilities"), COAT_OF_ARMS_EXPORT_CAPABILITY)) {
            throw new McpGatewayException(
                    "MCP native CoA binding is disconnected or not the exact build");
        }

        Object snapshotState = capabilities.get("snapshot");
        long revision;
        String revisionSource;
        if (Boolean.TRUE.equals(snapshotState)) {
            Map<?, ?> snapshot = requireMap(
                    mcp.callTool("ck3_take_snapshot", Map.of()),
                    "MCP snapshot");
            revision = positiveLong(snapshot.get("revision"), "MCP snapshot revision");
            revisionSource = "snapshot";
        } else if (Boolean.FALSE.equals(snapshotState)) {
            revision = 0;
            revisionSource = "frontend";
        } else {
            throw new McpGatewayException(
                    "MCP capabilities lack a boolean snapshot state");
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("schema", "coat-of-arms-source-binding-v1");
        result.put("schema_version", 1);
        result.put("status", "bound");
        result.put("revision_source", revisionSource);
        result.put("revision", revision);
        result.put("connection_generation", connectionGeneration);
        result.put("bridge_pid", bridgePid);
        result.put("game_version", EXPECTED_GAME_VERSION);
        result.put("executable_sha256", EXPECTED_EXECUTABLE_SHA256);
        return result;
    }

    @POST
    @Path("/open-native-designer")
    public Object openNativeDesigner() {
        return mcp.callTool(
                "ck3_activate_frontend_coat_of_arms_designer_v1",
                Map.of());
    }

    @POST
    @Path("/commit-native-design")
    public Object commitNativeDesign() {
        return mcp.callTool(
                "ck3_commit_frontend_dynasty_coat_of_arms_v1",
                Map.of());
    }

    @GET
    @Path("/native-designer-tree")
    public Object nativeDesignerTree() {
        return mcp.callTool(
                "ck3_inspect_frontend_coat_of_arms_tree_v1",
                Map.of());
    }

    @POST
    @Path("/enter-native-custom-mode")
    public Object enterNativeCustomMode() {
        return mcp.callTool(
                "ck3_activate_frontend_coat_of_arms_custom_mode_v1",
                Map.of());
    }

    @GET
    @Path("/resources")
    public Object resources(
            @QueryParam("kind") String kind,
            @QueryParam("query") String query,
            @QueryParam("visibleOnly") @DefaultValue("true") boolean visibleOnly,
            @QueryParam("offset") @DefaultValue("0") int offset,
            @QueryParam("limit") @DefaultValue("50") int limit) {
        if (kind == null || kind.isBlank()) {
            throw new BadRequestException("kind is required");
        }
        Map<String, Object> arguments = new LinkedHashMap<>();
        arguments.put(
                "game_directory",
                configuration.gameDirectory().orElseThrow(() ->
                        new McpGatewayException(
                                "missing companion configuration: gameDirectory")));
        arguments.put("kind", kind);
        if (query != null) {
            arguments.put("query", query);
        }
        arguments.put("visible_only", visibleOnly);
        arguments.put("offset", offset);
        arguments.put("limit", limit);
        return mcp.callTool(
                "ck3_query_coat_of_arms_resource_catalog_v1",
                arguments);
    }

    @GET
    @Path("/asset")
    public Object asset(
            @QueryParam("kind") String kind,
            @QueryParam("name") String name) {
        if (kind == null || kind.isBlank()) {
            throw new BadRequestException("kind is required");
        }
        if (name == null || name.isBlank()) {
            throw new BadRequestException("name is required");
        }
        return mcp.callTool(
                "ck3_read_coat_of_arms_resource_asset_v1",
                Map.of(
                        "game_directory",
                        configuration.gameDirectory().orElseThrow(() ->
                                new McpGatewayException(
                                        "missing companion configuration: gameDirectory")),
                        "kind",
                        kind,
                        "name",
                        name));
    }

    @GET
    @Path("/render-support")
    public Object renderSupport() {
        return mcp.callTool(
                "ck3_read_coat_of_arms_render_support_v1",
                Map.of(
                        "game_directory",
                        configuration.gameDirectory().orElseThrow(() ->
                                new McpGatewayException(
                                        "missing companion configuration: gameDirectory"))));
    }

    @GET
    @Path("/load-configuration")
    public Object loadConfiguration() {
        return mcp.callTool(
                "ck3_query_coat_of_arms_load_configuration_v1",
                Map.of(
                        "user_directory",
                        configuration.userDirectory().orElseThrow(() ->
                                new McpGatewayException(
                                "missing companion configuration: userDirectory"))));
    }

    @GET
    @Path("/dlc-sources")
    public Object dlcSources() {
        return mcp.callTool(
                "ck3_query_coat_of_arms_installed_dlc_sources_v1",
                Map.of(
                        "game_directory",
                        configuration.gameDirectory().orElseThrow(() ->
                                new McpGatewayException(
                                        "missing companion configuration: gameDirectory"))));
    }

    @GET
    @Path("/runtime-features")
    public Object runtimeFeatures(
            @QueryParam("expectedRevision") Long expectedRevision) {
        if (expectedRevision == null || expectedRevision < 0) {
            throw new BadRequestException(
                    "expectedRevision must be a non-negative integer");
        }
        return mcp.callTool(
                "ck3_query_loaded_feature_manifest_v1",
                Map.of("expected_revision", expectedRevision));
    }

    @GET
    @Path("/configured-resources")
    public Object configuredResources(
            @QueryParam("kind") String kind,
            @QueryParam("query") String query,
            @QueryParam("visibleOnly") @DefaultValue("true") boolean visibleOnly,
            @QueryParam("offset") @DefaultValue("0") int offset,
            @QueryParam("limit") @DefaultValue("50") int limit) {
        if (kind == null || kind.isBlank()) {
            throw new BadRequestException("kind is required");
        }
        Map<String, Object> arguments = new LinkedHashMap<>();
        arguments.put(
                "user_directory",
                configuration.userDirectory().orElseThrow(() ->
                        new McpGatewayException(
                                "missing companion configuration: userDirectory")));
        arguments.put("kind", kind);
        if (query != null) {
            arguments.put("query", query);
        }
        arguments.put("visible_only", visibleOnly);
        arguments.put("offset", offset);
        arguments.put("limit", limit);
        return mcp.callTool(
                "ck3_query_coat_of_arms_configured_resource_catalog_v1",
                arguments);
    }

    @GET
    @Path("/configured-asset")
    public Object configuredAsset(
            @QueryParam("kind") String kind,
            @QueryParam("candidateId") String candidateId) {
        if (kind == null || kind.isBlank()) {
            throw new BadRequestException("kind is required");
        }
        if (candidateId == null || candidateId.isBlank()) {
            throw new BadRequestException("candidateId is required");
        }
        return mcp.callTool(
                "ck3_read_coat_of_arms_configured_resource_asset_v1",
                Map.of(
                        "user_directory",
                        configuration.userDirectory().orElseThrow(() ->
                                new McpGatewayException(
                                        "missing companion configuration: userDirectory")),
                        "kind",
                        kind,
                        "candidate_id",
                        candidateId));
    }

    @POST
    @Path("/probe")
    public Object probe(ProbeRequest request) {
        if (request == null || request.source() == null) {
            throw new BadRequestException("source is required");
        }
        return mcp.callTool(
                "ck3_probe_coat_of_arms_source_v1",
                Map.of(
                        "source", request.source(),
                        "expected_revision", request.expectedRevision(),
                        "apply", request.apply()));
    }

    @POST
    @Path("/export")
    public Object export(ExportRequest request) {
        if (request == null) {
            throw new BadRequestException("request body is required");
        }
        return mcp.callTool(
                "ck3_export_coat_of_arms_source_v1",
                Map.of("expected_revision", request.expectedRevision()));
    }

    private static Map<?, ?> requireMap(Object value, String label) {
        if (!(value instanceof Map<?, ?> map)) {
            throw new McpGatewayException(label + " is not an object");
        }
        return map;
    }

    private static long positiveLong(Object value, String label) {
        if (!(value instanceof Number number)) {
            throw new McpGatewayException(label + " is not an integer");
        }
        long result = number.longValue();
        if (result < 1 || number.doubleValue() != (double) result) {
            throw new McpGatewayException(label + " is not a positive integer");
        }
        return result;
    }

    private static boolean containsString(Object value, String expected) {
        if (!(value instanceof Iterable<?> items)) {
            return false;
        }
        for (Object item : items) {
            if (expected.equals(item)) {
                return true;
            }
        }
        return false;
    }

    public record ProbeRequest(String source, long expectedRevision, boolean apply) {}

    public record ExportRequest(long expectedRevision) {}
}
