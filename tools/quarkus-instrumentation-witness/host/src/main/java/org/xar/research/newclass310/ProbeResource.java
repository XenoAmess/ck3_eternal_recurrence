package org.xar.research.newclass310;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.util.LinkedHashMap;
import java.util.Map;

@Path("/probe")
public final class ProbeResource {
    private Map<String, Object> identity() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("nonce", System.getProperty("fixture.nonce"));
        out.put("pid", ProcessHandle.current().pid());
        out.put("start_instant", ProcessHandle.current().info().startInstant().orElseThrow().toString());
        out.put("host_loader", ProbeResource.class.getClassLoader().toString());
        out.put("dependency_loader", BusinessRevision.class.getClassLoader().toString());
        out.put("added_resource", String.valueOf(BusinessRevision.class.getClassLoader().getResource(
                "org/xar/research/newclass310/AddedType.class")));
        return out;
    }
    @GET @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> value() {
        Map<String, Object> out = identity();
        out.put("value", BusinessRevision.value());
        return out;
    }
    @GET @Path("/loader") @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> loader() { return identity(); }

    @POST @Path("/stop")
    public Response stop(@HeaderParam("X-Fixture-Nonce") String supplied) {
        String expected = System.getProperty("fixture.nonce");
        if (expected == null || !expected.equals(supplied)) return Response.status(403).build();
        Thread stop = new Thread(() -> {
            try { Thread.sleep(200); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
            System.exit(0);
        }, "owned-software-fixture-stop");
        stop.setDaemon(false);
        stop.start();
        return Response.accepted().build();
    }
}
