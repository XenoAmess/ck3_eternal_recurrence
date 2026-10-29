package org.xar.ck3.control.service;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomEndpoint12004;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;

/** Additional resource in the existing Quarkus application; no independent service or Game authority. */
@Path(PrisonerRansomEndpoint12004.PATH)
@Produces(MediaType.APPLICATION_JSON)
public final class PrisonerRansomResource12004 {
    private final Optional<PrisonerVanillaResearch.Catalog> catalog;
    /** The installed current-build catalog provider is not yet qualified; absence stays explicit. */
    public PrisonerRansomResource12004() { this(Optional.empty()); }
    public PrisonerRansomResource12004(Optional<PrisonerVanillaResearch.Catalog> catalog) { this.catalog = java.util.Objects.requireNonNull(catalog); }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response evaluate(byte[] raw) {
        try {
            return Response.ok(PrisonerRansomEndpoint12004.evaluate(raw, catalog), MediaType.APPLICATION_JSON_TYPE)
                    .header("X-Xar-Producer", "java-prisoner-ransom-read-only-12004").build();
        } catch (IllegalArgumentException error) {
            byte[] body = StrictJson.canonical(StrictJson.object().put("schema", "xar.prisoner-ransom-error/v1")
                    .put("status", "rejected").put("reason", "malformed_or_source_mismatched_input").put("submission_authority", false));
            return Response.status(400).type(MediaType.APPLICATION_JSON_TYPE).entity(body).build();
        }
    }
}
