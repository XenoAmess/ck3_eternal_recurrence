package org.xar.ck3.control.service;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import java.util.function.Function;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.OfflineMandatoryChoiceReviewProducer;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import static org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.*;

/** Knowledge-file routes in the existing host; payloads contain captured references, never output roots. */
@Path("/v1/offline-event-analysis")
@Produces(MediaType.APPLICATION_JSON)
public final class OfflineEventAnalysisResource {
    public static final String PRODUCER = "java-quarkus-offline-event-analysis/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    private static final Logger LOG = Logger.getLogger(OfflineEventAnalysisResource.class);
    private final OfflineEventAnalysisHost host;
    private final String machineId;
    @Inject public OfflineEventAnalysisResource(OfflineEventAnalysisHost host,
            @ConfigProperty(name = "xar.projection.machine-id", defaultValue = "unknown") String machineId) {
        this.host = java.util.Objects.requireNonNull(host);
        if (!machineId.matches("[a-z0-9][a-z0-9-]{0,63}")) throw new IllegalArgumentException("explicit machine ID or unknown required");
        this.machineId = machineId;
    }
    public record MandatoryContext(String review_root, String grants_manifest) { }
    public record BatchContext(String incident_root, String knowledge_root, String grants_manifest) { }
    public record Context(String schema, String machine_id, String observed_at_utc, MandatoryContext mandatory_reviews, BatchContext event_batches) { }

    @GET @Path("/context")
    public Response context() {
        var mandatory = host.mandatoryScope().map(scope -> new MandatoryContext(scope.reviewRoot().toString(), scope.grantsManifest().toString())).orElse(null);
        var batches = host.batchScope().map(scope -> new BatchContext(scope.incidentRoot().toString(), scope.knowledgeRoot().toString(), scope.grantsManifest().toString())).orElse(null);
        return identified(Response.ok(new Context("xar.offline-event-analysis-context/v1", machineId, Instant.now().toString(), mandatory, batches))).build();
    }
    @POST @Path("/mandatory-review-inputs") @Consumes(MediaType.APPLICATION_JSON)
    public Response capture(byte[] raw) {
        return invoke(raw, OfflineEventAnalysisWire::decodeCapture, CaptureRequest::batchId,
                request -> OfflineEventAnalysisWire.encode(host.capture(request)));
    }
    @POST @Path("/mandatory-reviews") @Consumes(MediaType.APPLICATION_JSON)
    public Response reviews(byte[] raw) {
        return invoke(raw, OfflineEventAnalysisWire::decodeReview, ReviewRequest::batchId,
                request -> OfflineEventAnalysisWire.encode(host.review(request)));
    }
    @POST @Path("/batches") @Consumes(MediaType.APPLICATION_JSON)
    public Response batches(byte[] raw) {
        return invoke(raw, OfflineEventAnalysisWire::decodeBatch, BatchRequest::batchId, host::batch);
    }
    @FunctionalInterface private interface Action<I> { byte[] run(I request) throws IOException; }
    private <I> Response invoke(byte[] raw, Function<byte[], I> decode, Function<I, String> identifier, Action<I> action) {
        I request;
        try { request = decode.apply(raw); }
        catch (OfflineEventAnalysisWire.InvalidRequest failure) {
            return rejected(Optional.empty(), ErrorCode.INVALID_REQUEST, failure.oversized() ? 413 : 400, "invalid exact offline request");
        } catch (RuntimeException failure) {
            log(Optional.empty(), ErrorCode.PUBLICATION_FAILED, failure);
            return rejected(Optional.empty(), ErrorCode.PUBLICATION_FAILED, 500, "offline request decoder failed internally");
        }
        Optional<String> id = Optional.of(identifier.apply(request));
        try { return identified(Response.ok(action.run(request)).type(MediaType.APPLICATION_JSON_TYPE)).build(); }
        catch (OfflineMandatoryChoiceReviewProducer.SourceChangedException failure) {
            log(id, ErrorCode.SOURCE_CHANGED, failure);
            return rejected(id, ErrorCode.SOURCE_CHANGED, 409, "captured original offline sources changed");
        } catch (OfflineMandatoryChoiceReviewProducer.SourceUnavailableException | TrustedEventSourceContext.UnavailableException failure) {
            log(id, ErrorCode.OPERATION_UNAVAILABLE, failure);
            return rejected(id, ErrorCode.OPERATION_UNAVAILABLE, 503, "configured original offline sources unavailable");
        } catch (ProjectionProtocolException failure) {
            ErrorCode code = failure.code() == ProjectionError.Code.OPERATION_UNAVAILABLE ? ErrorCode.OPERATION_UNAVAILABLE : ErrorCode.PUBLICATION_FAILED;
            log(id, code, failure);
            return rejected(id, code, code == ErrorCode.OPERATION_UNAVAILABLE ? 503 : 500, "configured offline operation unavailable");
        } catch (IllegalArgumentException failure) {
            log(id, ErrorCode.SOURCE_CHANGED, failure);
            return rejected(id, ErrorCode.SOURCE_CHANGED, 409, "captured offline sources or immutable knowledge differ");
        } catch (IOException | RuntimeException failure) {
            log(id, ErrorCode.PUBLICATION_FAILED, failure);
            return rejected(id, ErrorCode.PUBLICATION_FAILED, 500, "offline publication failed; completion unknown");
        }
    }
    private Response rejected(Optional<String> id, ErrorCode code, int status, String message) {
        return identified(Response.status(status).entity(OfflineEventAnalysisWire.encode(
                new OfflineEventAnalysisContract.Error(id, code, message))).type(MediaType.APPLICATION_JSON_TYPE)).build();
    }
    private void log(Optional<String> id, ErrorCode code, Exception failure) {
        LOG.warnf(failure, "offline_event_analysis_error machine_id=%s batch_id=%s code=%s", machineId, id.orElse("unknown"), code.wire());
    }
    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", PRODUCER).header("X-Xar-Producer-Version", PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", CONTRACT);
    }
}
