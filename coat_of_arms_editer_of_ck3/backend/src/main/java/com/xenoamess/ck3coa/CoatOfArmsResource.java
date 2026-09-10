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

    public record ProbeRequest(String source, long expectedRevision, boolean apply) {}

    public record ExportRequest(long expectedRevision) {}
}
