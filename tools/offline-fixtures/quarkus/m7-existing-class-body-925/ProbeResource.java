package org.xar.fixture.indexnext;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.HeaderParam;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Only the new private fixture owns this finite-callee counter; no Game/business owner import. */
@Path("/fixture-index")
@ApplicationScoped
public class ProbeResource {
    private final String token = UUID.randomUUID().toString();
    private final AtomicLong progress = new AtomicLong();
    private final AtomicBoolean closed = new AtomicBoolean();
    private volatile String failure;
    private Thread worker;

    @PostConstruct
    public void start() {
        worker = new Thread(this::run, "private-contracts-index-next-counter");
        worker.setDaemon(true);
        worker.start();
        System.out.println("INDEX_NEXT_DELEGATE_CREATED token=" + token + " thread=" + worker.threadId());
    }

    private void run() {
        byte[] material = "{\"fixture\":1}".getBytes(StandardCharsets.UTF_8);
        while (!closed.get()) {
            try {
                if (FullJsonTree.parse(material, 128).path("fixture").intValue() != 1) {
                    throw new IllegalStateException("original finite fixture DATA changed");
                }
                progress.incrementAndGet();
                Thread.sleep(50);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                return;
            } catch (RuntimeException error) {
                failure = error.getClass().getName() + ":" + error.getMessage();
                return;
            }
        }
    }

    private boolean owned(String supplied) {
        return supplied != null && supplied.equals(System.getProperty("fixture.nonce"));
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response observe(@HeaderParam("X-Fixture-Nonce") String supplied) {
        if (!owned(supplied)) return Response.status(403).build();
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("nonce", System.getProperty("fixture.nonce"));
        row.put("mode", System.getProperty("fixture.mode"));
        row.put("pid", ProcessHandle.current().pid());
        row.put("start_instant", ProcessHandle.current().info().startInstant().orElseThrow().toString());
        row.put("application_loader", getClass().getClassLoader().toString());
        row.put("application_loader_identity", System.identityHashCode(getClass().getClassLoader()));
        row.put("dependency_loader", FullJsonTree.class.getClassLoader().toString());
        row.put("dependency_loader_identity", System.identityHashCode(FullJsonTree.class.getClassLoader()));
        row.put("enum_loader_identity", System.identityHashCode(enumClass().getClassLoader()));
        row.put("delegate_token", token);
        row.put("worker_thread_id", worker.threadId());
        row.put("worker_alive", worker.isAlive());
        row.put("progress", progress.get());
        row.put("failure", failure);
        row.put("closed", closed.get());
        row.put("agent_argument", ManagementFactory.getRuntimeMXBean().getInputArguments().stream()
                .anyMatch(item -> item.startsWith("-javaagent:") && item.contains("quarkus-class-change-agent")));
        row.put("probe_object_identity", System.identityHashCode(this));
        row.put("probe_class_identity", System.identityHashCode(ProbeResource.class));
        row.put("method_body_value", "M7_BODY_V1");
        return Response.ok(row).build();
    }

    private static Class<?> enumClass() {
        try {
            return Class.forName("org.xar.ck3.control.contracts.FullJsonTree$1", false, FullJsonTree.class.getClassLoader());
        } catch (ClassNotFoundException failure) {
            throw new IllegalStateException("exact second family member is required", failure);
        }
    }

    @POST
    @Path("/stop")
    public Response stop(@HeaderParam("X-Fixture-Nonce") String supplied) {
        if (!owned(supplied)) return Response.status(403).build();
        Thread stop = new Thread(() -> {
            try { Thread.sleep(200); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
            System.exit(0);
        }, "private-contracts-index-next-stop");
        stop.setDaemon(false);
        stop.start();
        return Response.accepted().build();
    }

    @PreDestroy
    public void close() {
        if (!closed.compareAndSet(false, true)) return;
        worker.interrupt();
        try { worker.join(2000); }
        catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
        if (worker.isAlive()) throw new IllegalStateException("private counter failed to close");
        System.out.println("INDEX_NEXT_DELEGATE_CLOSED token=" + token);
    }
}
