package org.xar.ck3.control.service;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.xar.ck3.control.contracts.StrictJson;

@Path("/v1/status")
@Produces(MediaType.APPLICATION_JSON)
public final class ServiceStatusResource {
    public record ServiceStatus(
            String schema, String service, String status,
            int input_max_bytes, int output_max_bytes) { }

    @GET
    public ServiceStatus status() {
        return new ServiceStatus("xar.ck3.control.service-status/v1", "ck3-control", "ready",
                StrictJson.INPUT_MAX_BYTES, StrictJson.OUTPUT_MAX_BYTES);
    }
}
