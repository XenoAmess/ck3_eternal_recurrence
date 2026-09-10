package com.xenoamess.ck3coa;

import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import java.util.Map;

@Provider
public class McpGatewayExceptionMapper implements ExceptionMapper<McpGatewayException> {
    @Override
    public Response toResponse(McpGatewayException exception) {
        return Response.status(Response.Status.SERVICE_UNAVAILABLE)
                .type(MediaType.APPLICATION_JSON_TYPE)
                .entity(Map.of(
                        "schema", "coat-of-arms-companion-error-v1",
                        "status", "mcp_unavailable",
                        "message", exception.getMessage()))
                .build();
    }
}
