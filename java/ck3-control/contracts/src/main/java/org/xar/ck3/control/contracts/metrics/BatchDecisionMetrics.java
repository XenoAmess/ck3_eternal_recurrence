package org.xar.ck3.control.contracts.metrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Snapshot;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Terminal;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Tick;

/** Complete retained caller window, including gaps between request stages. It grants no business credit. */
public final class BatchDecisionMetrics {
    public static final String SCHEMA = "xar.batch-decision-metrics/v1";
    public static final int MAXIMUM_BYTES = StrictJson.EXPLICIT_MAX_BYTES;
    private BatchDecisionMetrics() { }

    public record Context(String machineId, String scopeId, String batchId, String clockDomainId) {
        public Context {
            StrictJson.text(machineId); StrictJson.text(scopeId); StrictJson.text(batchId); StrictJson.text(clockDomainId);
        }
    }

    public record Window(Tick began, Tick ended, Terminal terminal) {
        public Window {
            Objects.requireNonNull(began); Objects.requireNonNull(ended); Objects.requireNonNull(terminal);
            StrictJson.require(began.clockDomainId().equals(ended.clockDomainId()) && began.threadId() == ended.threadId(),
                    "batch window must retain its original clock domain and owner thread");
            StrictJson.require(ended.elapsedNanos() >= began.elapsedNanos(), "batch monotonic rollback rejected");
            if (began.threadCpuNanos().isPresent() && ended.threadCpuNanos().isPresent()) {
                StrictJson.require(ended.threadCpuNanos().getAsLong() >= began.threadCpuNanos().getAsLong(), "batch CPU rollback rejected");
            }
        }
        public long totalWallNanos() { return ended.elapsedNanos() - began.elapsedNanos(); }
        public OptionalLong ownerCpuNanos() {
            return began.threadCpuNanos().isPresent() && ended.threadCpuNanos().isPresent()
                    ? OptionalLong.of(ended.threadCpuNanos().getAsLong() - began.threadCpuNanos().getAsLong()) : OptionalLong.empty();
        }
    }

    public record Batch(Context context, Window window, List<Snapshot> requests) {
        public Batch {
            Objects.requireNonNull(context); Objects.requireNonNull(window); requests = List.copyOf(requests);
            StrictJson.require(context.clockDomainId().equals(window.began().clockDomainId()), "original batch clock domain required");
            Set<String> ids = new HashSet<>();
            long previous = window.began().elapsedNanos();
            for (Snapshot request : requests) {
                DecisionMetrics.Context c = request.context();
                StrictJson.require(context.machineId().equals(c.machineId()) && context.scopeId().equals(c.scopeId())
                        && context.batchId().equals(c.batchId()) && context.clockDomainId().equals(c.clockDomainId()),
                        "all request observations must belong to the original batch");
                StrictJson.require(ids.add(c.requestId()), "duplicate request identity cannot be counted twice");
                for (DecisionMetrics.Span span : request.spans()) {
                    StrictJson.require(window.terminal() != Terminal.RETURNED || span.terminal() == Terminal.RETURNED,
                            "returned batch cannot hide an unknown or timed-out request stage");
                    StrictJson.require(span.began().threadId() == window.began().threadId()
                            && span.began().elapsedNanos() >= previous && span.ended().elapsedNanos() <= window.ended().elapsedNanos(),
                            "request stages must be ordered inside the complete batch window");
                    previous = span.ended().elapsedNanos();
                }
            }
        }
        public boolean speedupClaimAllowed() { return false; }
        public boolean replayAllowed() { return false; }
    }

    public static byte[] encode(Batch batch) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        Context c = batch.context(); ObjectNode context = row.putObject("context");
        context.put("machine_id", c.machineId()); context.put("scope_id", c.scopeId());
        context.put("batch_id", c.batchId()); context.put("clock_domain_id", c.clockDomainId());
        ObjectNode window = row.putObject("window"); window.set("began", DecisionMetrics.tick(batch.window().began()));
        window.set("ended", DecisionMetrics.tick(batch.window().ended())); window.put("terminal", batch.window().terminal().name());
        var requests = row.putArray("requests");
        for (Snapshot request : batch.requests()) requests.add(StrictJson.parse(DecisionMetrics.encode(request)));
        return StrictJson.canonical(row, MAXIMUM_BYTES);
    }

    public static Batch decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAXIMUM_BYTES), Set.of("schema", "context", "window", "requests"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact batch decision metrics schema required");
        ObjectNode c = StrictJson.object(row.get("context"), Set.of("machine_id", "scope_id", "batch_id", "clock_domain_id"));
        Context context = new Context(text(c, "machine_id"), text(c, "scope_id"), text(c, "batch_id"), text(c, "clock_domain_id"));
        ObjectNode w = StrictJson.object(row.get("window"), Set.of("began", "ended", "terminal"));
        Window window = new Window(DecisionMetrics.tick(w.get("began")), DecisionMetrics.tick(w.get("ended")), Terminal.valueOf(text(w, "terminal")));
        JsonNode values = row.get("requests"); StrictJson.require(values.isArray(), "request metrics must be an array");
        var requests = new java.util.ArrayList<Snapshot>();
        for (JsonNode value : values) requests.add(DecisionMetrics.decode(StrictJson.canonical(value)));
        return new Batch(context, window, requests);
    }

    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
}
