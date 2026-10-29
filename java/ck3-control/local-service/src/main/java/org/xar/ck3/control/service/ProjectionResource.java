package org.xar.ck3.control.service;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.List;
import java.time.Instant;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.build.ProjectionArtifactAuthority;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionArtifactInputCodec;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceGrant;
import org.xar.ck3.control.contracts.projection.ProjectionEvidenceCodec;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;

/** One local HTTP transport for registered projections and fixed read-only source contexts. */
@Path("/v1/projections")
@Produces(MediaType.APPLICATION_JSON)
public final class ProjectionResource {
    public static final String PRODUCER = "java-quarkus-projection/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    private final ProjectionHost host;
    private final String machineId;
    @Inject public ProjectionResource(ProjectionHost host,
            @ConfigProperty(name = "xar.projection.machine-id", defaultValue = "unknown") String machineId) {
        this.host = host;
        if (!machineId.matches("[a-z0-9][a-z0-9-]{0,63}")) { throw new IllegalArgumentException("explicit machine ID or unknown required"); }
        this.machineId = machineId;
    }
    public record OperationIdentity(String operation, int input_max_bytes, int output_max_bytes) { }
    public record Identity(String schema, String producer, String producer_version, String request_schema,
            String result_schema, int envelope_max_bytes, List<OperationIdentity> operations) {
        public Identity { operations = List.copyOf(operations); }
    }
    public record CatalogIdentity(String provider_class, String artifact_path, List<OperationIdentity> operations) {
        public CatalogIdentity { operations = List.copyOf(operations); }
    }
    public record Catalogs(String schema, String machine_id, String observed_at_utc, List<CatalogIdentity> catalogs) {
        public Catalogs { catalogs = List.copyOf(catalogs); }
    }
    public record EventSources(String state_root, String stock_game_root) { }
    public record Context(String schema, String machine_id, String observed_at_utc, EventSources event_sources) { }

    public record EvidenceGrants(String schema, String machine_id, String observed_at_utc, List<ProjectionEvidenceCodec.WireGrant> grants) {
        public EvidenceGrants { grants = List.copyOf(grants); }
    }
    public record EvidenceUnavailable(String schema, String status, String code) { }

    @POST @Path("/call") @Consumes(MediaType.APPLICATION_JSON)
    public Response call(byte[] raw) {
        ProjectionResult result = host.call(raw);
        int status = switch (result) {
            case ProjectionResult.Succeeded ignored -> 200;
            case ProjectionResult.Rejected rejected -> switch (rejected.error().code()) {
                case OPERATION_UNAVAILABLE -> 503;
                case PAYLOAD_TOO_LARGE -> 413;
                case DOMAIN_REJECTED -> 422;
                case PROJECTION_FAILED, INVALID_RESULT -> 500;
                default -> 400;
            };
        };
        // Raw JSON bytes must remain HTTP JSON, never Jackson's byte-array/base64 representation.
        return identified(Response.status(status).entity(ProjectionWire.encodeResult(result)).type(MediaType.APPLICATION_JSON_TYPE)).build();
    }

    @GET @Path("/identity")
    public Response identity() {
        List<OperationIdentity> operations = host.profiles().stream().map(profile -> new OperationIdentity(
                profile.operation().wire(), profile.inputMaximumBytes(), profile.outputMaximumBytes())).toList();
        return identified(Response.ok(new Identity("xar.projection-host-identity/v1", PRODUCER, PRODUCER_VERSION,
                ProjectionCall.SCHEMA, ProjectionResult.SCHEMA, ProjectionWire.MAX_ENVELOPE_BYTES, operations))).build();
    }

    @GET @Path("/catalogs")
    public Response catalogs() {
        List<CatalogIdentity> catalogs = host.catalogs().stream().map(catalog -> new CatalogIdentity(
                catalog.providerClass(), catalog.artifactPath(), catalog.operations().stream().map(profile ->
                        new OperationIdentity(profile.operation().wire(), profile.inputMaximumBytes(), profile.outputMaximumBytes())).toList())).toList();
        return identified(Response.ok(new Catalogs("xar.projection-host-catalogs/v1", machineId,
                Instant.now().toString(), catalogs))).build();
    }

    @GET @Path("/context")
    public Response context() {
        EventSources eventSources = host.context().eventSources().map(source ->
                new EventSources(source.stateRoot().toString(), source.stockGameRoot().toString())).orElse(null);
        return identified(Response.ok(new Context("xar.projection-host-context/v1", machineId,
                Instant.now().toString(), eventSources))).build();
    }

    @GET @Path("/evidence-grants")
    public Response evidenceGrants() {
        try {
            List<ProjectionEvidenceGrant> snapshot = host.context().eventSources()
                    .map(source -> source.evidenceGrants()).orElseGet(List::of);
            List<ProjectionEvidenceCodec.WireGrant> grants = snapshot.stream().map(ProjectionEvidenceCodec::wire).toList();
            return identified(Response.ok(new EvidenceGrants("xar.projection-host-evidence-grants/v1", machineId,
                    Instant.now().toString(), grants))).build();
        } catch (ProjectionProtocolException unavailable) {
            return identified(Response.status(503).entity(new EvidenceUnavailable(
                    "xar.projection-host-evidence-grants-unavailable/v1", "unavailable", "operation-unavailable"))).build();
        }
    }

    public record ArtifactUnavailable(String schema, String status, String code) { }
    @GET @Path("/artifact-inputs")
    public Response artifactInputs() {
        try {
            if ("unknown".equals(machineId)) throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE,
                    "artifact context requires the configured actual machine");
            byte[] body = ProjectionArtifactInputCodec.encodeContext(new ProjectionArtifactAuthority.Context(
                    machineId, Instant.now(), host.artifactInputs()));
            return identified(Response.ok(body).type(MediaType.APPLICATION_JSON_TYPE)).build();
        } catch (ProjectionProtocolException unavailable) {
            return identified(Response.status(503).entity(new ArtifactUnavailable(
                    "xar.projection-artifact-input-unavailable/v1", "unavailable", "operation-unavailable"))).build();
        }
    }
    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", PRODUCER).header("X-Xar-Producer-Version", PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", ProjectionCall.SCHEMA);
    }
}
