package org.xar.ck3.control.service;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2CallContextWire;

/** Future read-only context adapter; request payload fields cannot choose roots or install capabilities. */
@Path(G2CallContextWire.HTTP_PATH)
@Produces(MediaType.APPLICATION_JSON)
public final class G2CallContextResource {
    private static final System.Logger LOG = System.getLogger(G2CallContextResource.class.getName());
    private final G2CallContextHost host;

    @Inject public G2CallContextResource(G2CallContextHost host) { this.host = Objects.requireNonNull(host); }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response context(byte[] raw) {
        if (raw == null || raw.length == 0) return rejected(G2HttpError.Code.MALFORMED_REQUEST);
        if (raw.length > G2CallContextWire.MAX_INPUT_BYTES) return rejected(G2HttpError.Code.PAYLOAD_TOO_LARGE);
        G2CallContextWire.Input input;
        try { input = G2CallContextWire.decodeInput(raw); }
        catch (G2Exception error) { return rejected(error.code()); }
        catch (RuntimeException error) { return rejected(G2HttpError.Code.MALFORMED_REQUEST); }
        try {
            G2CallContextProducer.Result result = host.context(input.milestone(), input.payload());
            return switch (result) {
                case G2CallContextProducer.Available available -> {
                    byte[] body = G2CallContextWire.encodeContext(available.context());
                    if (body.length == 0 || body.length > G2CallContextWire.MAX_CONTEXT_BYTES) {
                        yield rejected(G2HttpError.Code.INVALID_RESULT);
                    }
                    yield identified(Response.ok(body, MediaType.APPLICATION_JSON_TYPE)).build();
                }
                case G2CallContextProducer.Unavailable unavailable -> {
                    LOG.log(System.Logger.Level.DEBUG, "Root call-context unavailable: {0}: {1}", unavailable.reason(), unavailable.detail());
                    yield rejected(G2HttpError.Code.ENGINE_UNAVAILABLE);
                }
            };
        } catch (G2Exception error) { return rejected(error.code()); }
        catch (RuntimeException error) { return rejected(G2HttpError.Code.INTERNAL_FAILURE); }
    }

    private static Response rejected(G2HttpError.Code code) {
        String message = switch (code) {
            case MALFORMED_REQUEST -> "request does not satisfy the strict call-context contract";
            case PAYLOAD_TOO_LARGE -> "request exceeds the call-context input role budget";
            case ENGINE_UNAVAILABLE -> "Root call-context provider is unavailable";
            case DOMAIN_REJECTED -> "Root call-context input was rejected";
            case SOURCE_MISMATCH -> "Root call-context source binding differs";
            case INVALID_RESULT -> "Root call-context result is invalid";
            case INTERNAL_FAILURE -> "Root call-context evaluation failed";
        };
        return identified(Response.status(code.httpStatus()).type(MediaType.APPLICATION_JSON_TYPE)
                .entity(G2Wire.encodeError(new G2HttpError(G2HttpError.SCHEMA, code, message)))).build();
    }

    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", G2CallContextWire.PRODUCER)
                .header("X-Xar-Producer-Version", G2CallContextWire.PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", G2CallContextWire.SCHEMA);
    }
}
