package org.xar.ck3.control.service;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2CallContextWire;
import org.xar.ck3.control.g2.context.RootG2HandoffWire;

@Path(RootG2HandoffWire.HTTP_PATH)
@Produces(MediaType.APPLICATION_JSON)
public final class RootG2HandoffResource {
    private final RootG2HandoffHost host;
    @Inject public RootG2HandoffResource(RootG2HandoffHost host) { this.host = java.util.Objects.requireNonNull(host); }
    @POST @Consumes(MediaType.APPLICATION_JSON)
    public Response context(byte[] raw) {
        RootG2HandoffWire.Input input;
        try { input = RootG2HandoffWire.decode(raw); }
        catch (java.io.IOException | RuntimeException error) { return error(G2HttpError.Code.MALFORMED_REQUEST); }
        G2CallContextProducer.Result result = host.redeem(input);
        if (result instanceof G2CallContextProducer.Available available) {
            return identified(Response.ok(G2CallContextWire.encodeContext(available.context()), MediaType.APPLICATION_JSON_TYPE)).build();
        }
        return error(G2HttpError.Code.ENGINE_UNAVAILABLE);
    }
    private static Response error(G2HttpError.Code code) {
        return identified(Response.status(code.httpStatus()).type(MediaType.APPLICATION_JSON_TYPE)
                .entity(G2Wire.encodeError(new G2HttpError(G2HttpError.SCHEMA, code, "Root-issued child/request handoff unavailable")))).build();
    }
    private static Response.ResponseBuilder identified(Response.ResponseBuilder response) {
        return response.header("X-Xar-Producer", G2CallContextWire.PRODUCER)
                .header("X-Xar-Producer-Version", G2CallContextWire.PRODUCER_VERSION)
                .header("X-Xar-Contract-Revision", G2CallContextWire.SCHEMA);
    }
}
