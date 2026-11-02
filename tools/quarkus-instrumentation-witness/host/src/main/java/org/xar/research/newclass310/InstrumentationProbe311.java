package org.xar.research.newclass310;

import jakarta.annotation.PreDestroy;
import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/** Private software witness; this owns only a counter thread and never accesses Game. */
@Path("/instrumentation-probe")
@ApplicationScoped
public class InstrumentationProbe311 {
    private Delegate delegate;

    @PostConstruct
    void initialize() {
        if (delegate != null) throw new IllegalStateException("private delegate initialized twice");
        delegate = new Delegate();
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> observe() {
        String nonce = System.getProperty("fixture.nonce");
        if (nonce == null || nonce.isBlank()) throw new IllegalStateException("private fixture nonce is required");
        ClassLoader loader = InstrumentationProbe311.class.getClassLoader();
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("nonce", nonce);
        row.put("class_change_agent_argument_present", java.lang.management.ManagementFactory.getRuntimeMXBean()
                .getInputArguments().stream().anyMatch(a -> a.startsWith("-javaagent:") && a.contains("quarkus-class-change-agent")));
        row.put("pid", ProcessHandle.current().pid());
        row.put("start_instant", ProcessHandle.current().info().startInstant().orElseThrow().toString());
        row.put("application_loader", loader.toString());
        row.put("application_loader_identity", System.identityHashCode(loader));
        row.put("dependency_loader", BusinessRevision.class.getClassLoader().toString());
        row.put("delegate_token", delegate.token);
        row.put("delegate_identity", System.identityHashCode(delegate));
        row.put("worker_thread_id", delegate.worker.threadId());
        row.put("worker_alive", delegate.worker.isAlive());
        row.put("progress", delegate.progress.get());
        row.put("worker_last_value", delegate.lastValue);
        row.put("new_invocation_value", BusinessRevision.value());
        row.put("closed", delegate.closed.get());
        return row;
    }

    @PreDestroy
    void destroy() {
        if (delegate != null) delegate.close();
    }

    private static final class Delegate {
        private final String token = UUID.randomUUID().toString();
        private final AtomicLong progress = new AtomicLong();
        private final AtomicBoolean closed = new AtomicBoolean();
        private volatile String lastValue = "NO_INVOCATION_YET";
        private final Thread worker;

        private Delegate() {
            worker = new Thread(this::run, "private-instrumentation311-counter");
            worker.setDaemon(true);
            worker.start();
            System.out.println("INSTRUMENTATION311_DELEGATE_CREATED token=" + token + " thread=" + worker.threadId());
        }

        private void run() {
            while (!closed.get()) {
                // This loop's active frame stays alive; each invocation can observe a redefined callee.
                lastValue = BusinessRevision.value();
                progress.incrementAndGet();
                try {
                    Thread.sleep(20L);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }

        private void close() {
            if (!closed.compareAndSet(false, true)) return;
            worker.interrupt();
            try {
                worker.join(2000L);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("private counter cleanup interrupted", interrupted);
            }
            if (worker.isAlive()) throw new IllegalStateException("private counter did not stop");
            System.out.println("INSTRUMENTATION311_DELEGATE_CLOSED token=" + token + " thread=" + worker.threadId());
        }
    }
}
