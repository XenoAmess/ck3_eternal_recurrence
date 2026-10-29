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
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;

/** HTTP JSON adapter only: no file, native, action, publication, lease or writer capability. */
@Path(G2Wire.HTTP_PATH)
@Produces(MediaType.APPLICATION_JSON)
public final class G2ResearchResource {
    private final G2ResearchHost host;

    @Inject public G2ResearchResource(G2ResearchHost host) { this.host = Objects.requireNonNull(host); }

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    public Response evaluate(byte[] raw) {
        if (raw == null || raw.length == 0) return rejected(G2HttpError.Code.MALFORMED_REQUEST);
        if (raw.length > G2Wire.MAX_REQUEST_BYTES) return rejected(G2HttpError.Code.PAYLOAD_TOO_LARGE);
        G2Request request;
        try { request = G2Wire.decodeRequest(raw); }
        catch (G2Exception error) { return rejected(error.code()); }
        catch (RuntimeException error) { return rejected(G2HttpError.Code.MALFORMED_REQUEST); }
        G2Response result;
        try { result = host.evaluate(request); }
        catch (G2Exception error) { return rejected(error.code()); }
        catch (IllegalArgumentException error) { return rejected(G2HttpError.Code.DOMAIN_REJECTED); }
        catch (RuntimeException error) { return rejected(G2HttpError.Code.INTERNAL_FAILURE); }
        try {
            byte[] body = G2Wire.encodeResponse(result);
            if (body.length == 0 || body.length > G2Wire.MAX_RESPONSE_BYTES) return rejected(G2HttpError.Code.INVALID_RESULT);
            // Return original canonical JSON document bytes, not a byte[] Jackson value/base64 string.
            return identified(Response.ok(body, MediaType.APPLICATION_JSON_TYPE)).build();
        } catch (RuntimeException error) { return rejected(G2HttpError.Code.INVALID_RESULT); }
    }

    private static Response rejected(G2HttpError.Code code) {
        G2HttpError error = new G2HttpError(G2HttpError.SCHEMA, code, message(code));
        return identified(Response.status(code.httpStatus()).type(MediaType.APPLICATION_JSON_TYPE)
                .entity(G2Wire.encodeError(error))).build();
    }

    private static String message(G2HttpError.Code code) {
        return switch (code) {
            case MALFORMED_REQUEST -> "request does not satisfy the strict G2 research contract";
            case PAYLOAD_TOO_LARGE -> "request exceeds the G2 research input role budget";
            case DOMAIN_REJECTED -> "domain input does not satisfy the selected milestone contract";
            case SOURCE_MISMATCH -> "result source or request identity differs from the submitted research input";
            case ENGINE_UNAVAILABLE -> "requested G2 research domain is unavailable";
            case INTERNAL_FAILURE -> "G2 research evaluation failed";
            case INVALID_RESULT -> "G2 research result does not satisfy its output contract";
        };
    }

    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", G2Wire.PRODUCER)
                .header("X-Xar-Producer-Version", G2Wire.PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", G2Wire.REQUEST_SCHEMA);
    }
}
