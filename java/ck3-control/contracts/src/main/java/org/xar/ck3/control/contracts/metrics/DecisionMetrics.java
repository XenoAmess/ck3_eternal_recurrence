package org.xar.ck3.control.contracts.metrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Observations carried by the existing receipt/writer. These values grant no action or saved-day credit. */
public final class DecisionMetrics {
    public static final String SCHEMA = "xar.decision-metrics/v2";
    private DecisionMetrics() { }

    public enum Stage {
        QUEUED, DOMAIN_EVALUATION, NATIVE_AUTHORITY, NATIVE_ACK_OBSERVATION, POSTSTATE_VALIDATION,
        GAME_DATE_OBSERVATION, SAVE_ACCEPTANCE, PERSISTENCE
    }
    /** RETURNED describes a local call return, not a game/business result. */
    public enum Terminal { RETURNED, UNKNOWN, TIMED_OUT }

    public record Context(String machineId, String scopeId, String batchId, String requestId, String clockDomainId) {
        public Context {
            StrictJson.text(machineId); StrictJson.text(scopeId); StrictJson.text(batchId);
            StrictJson.text(requestId); StrictJson.text(clockDomainId);
        }
    }

    /** Monotonic values are local to one clock domain/JVM and one retained owner thread. */
    public record Tick(String clockDomainId, long elapsedNanos, Instant utc, long threadId, OptionalLong threadCpuNanos) {
        public Tick {
            StrictJson.text(clockDomainId); Objects.requireNonNull(utc); Objects.requireNonNull(threadCpuNanos);
            StrictJson.require(elapsedNanos >= 0 && threadId > 0, "nonnegative local monotonic tick and owner thread required");
            StrictJson.require(threadCpuNanos.isEmpty() || threadCpuNanos.getAsLong() >= 0, "CPU unavailable remains absent");
        }
    }

    public record Span(Stage stage, Tick began, Tick ended, Terminal terminal) {
        public Span {
            Objects.requireNonNull(stage); Objects.requireNonNull(began); Objects.requireNonNull(ended); Objects.requireNonNull(terminal);
            StrictJson.require(began.clockDomainId().equals(ended.clockDomainId()) && began.threadId() == ended.threadId(),
                    "span cannot cross JVM clock domains or CPU owner threads");
            StrictJson.require(ended.elapsedNanos() >= began.elapsedNanos(), "monotonic clock rollback rejected");
            if (began.threadCpuNanos().isPresent() && ended.threadCpuNanos().isPresent()) {
                StrictJson.require(ended.threadCpuNanos().getAsLong() >= began.threadCpuNanos().getAsLong(), "CPU counter rollback rejected");
            }
        }
        public long wallNanos() { return ended.elapsedNanos() - began.elapsedNanos(); }
        public OptionalLong cpuNanos() {
            return began.threadCpuNanos().isPresent() && ended.threadCpuNanos().isPresent()
                    ? OptionalLong.of(ended.threadCpuNanos().getAsLong() - began.threadCpuNanos().getAsLong()) : OptionalLong.empty();
        }
        public boolean utcRegressed() { return ended.utc().isBefore(began.utc()); }
    }

    /** Returned primitive ACKs remain observable even when the later business poststate is invalid. */
    public record Acknowledgements(int commandCount, int acceptedAckCount, String originalProjectionSha256) {
        public Acknowledgements {
            StrictJson.require(commandCount >= 0 && acceptedAckCount >= 0 && acceptedAckCount <= commandCount,
                    "separate native command and accepted ACK counts");
            sha(originalProjectionSha256);
        }
    }

    /** Aggregate original-authority timing is separate from the returned native command/ACK counts. */
    public record NativeObservation(int commandCount, int acceptedAckCount, int startingDateRaw, int endingDateRaw,
                                    String originalProjectionSha256) {
        public NativeObservation {
            StrictJson.require(commandCount >= 0 && acceptedAckCount >= 0 && acceptedAckCount <= commandCount,
                    "separate bounded native command and accepted ACK counts");
            wholeDays(startingDateRaw, endingDateRaw); sha(originalProjectionSha256);
        }
        public int observedGameDays() { return (endingDateRaw - startingDateRaw) / 24; }
        public int savedDayCredit() { return 0; }
    }

    /** Only the savedproof adapter consumes actual completed measurement objects to produce this observation. */
    public record SavedObservation(String machineId, int dateRaw, ExactRef canonicalProof, ExactRef save) {
        public SavedObservation {
            StrictJson.text(machineId); StrictJson.require(dateRaw >= 0, "saved date is a nonnegative int32");
            Objects.requireNonNull(canonicalProof); Objects.requireNonNull(save);
        }
    }

    public record SavedWindow(SavedObservation before, SavedObservation after) {
        public SavedWindow {
            Objects.requireNonNull(before); Objects.requireNonNull(after);
            StrictJson.require(before.machineId().equals(after.machineId()), "saved observations cannot cross machines");
            wholeDays(before.dateRaw(), after.dateRaw());
        }
        public int observedSavedDays() { return (after.dateRaw() - before.dateRaw()) / 24; }
    }

    public record Snapshot(Context context, List<Span> spans, Optional<Acknowledgements> acknowledgements, Optional<NativeObservation> nativeObservation,
                           Optional<SavedWindow> savedWindow) {
        public Snapshot {
            Objects.requireNonNull(context); spans = List.copyOf(spans);
            Objects.requireNonNull(acknowledgements); Objects.requireNonNull(nativeObservation); Objects.requireNonNull(savedWindow);
            long previous = -1;
            for (Span span : spans) {
                StrictJson.require(span.began().clockDomainId().equals(context.clockDomainId())
                        && span.began().elapsedNanos() >= previous, "ordered nonoverlapping spans in the same retained clock domain");
                previous = span.ended().elapsedNanos();
            }
            savedWindow.ifPresent(window -> StrictJson.require(window.before().machineId().equals(context.machineId()), "saved metric machine differs"));
            if (acknowledgements.isPresent()) {
                StrictJson.require(spans.stream().anyMatch(span -> span.stage() == Stage.NATIVE_ACK_OBSERVATION
                        && span.terminal() == Terminal.RETURNED), "ACK observation requires returned primitive decoder stage");
            }
            if (nativeObservation.isPresent()) {
                StrictJson.require(spans.stream().anyMatch(span -> span.stage() == Stage.POSTSTATE_VALIDATION
                        && span.terminal() == Terminal.RETURNED), "game-day metric requires completed poststate validation");
                Acknowledgements ack = acknowledgements.orElseThrow(() -> new IllegalArgumentException("validated native poststate requires original ACK observation"));
                NativeObservation observed = nativeObservation.orElseThrow();
                StrictJson.require(ack.commandCount() == observed.commandCount() && ack.acceptedAckCount() == observed.acceptedAckCount()
                        && ack.originalProjectionSha256().equals(observed.originalProjectionSha256()), "ACK and native poststate belong to one original projection");
            }
        }
        /** Incomplete per-request instrumentation does not provide a complete-batch rate denominator. */
        public boolean speedupClaimAllowed() { return false; }
        public boolean replayAllowed() { return false; }
    }

    public static byte[] encode(Snapshot snapshot) {
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        Context c = snapshot.context(); ObjectNode context = row.putObject("context");
        context.put("machine_id", c.machineId()); context.put("scope_id", c.scopeId()); context.put("batch_id", c.batchId());
        context.put("request_id", c.requestId()); context.put("clock_domain_id", c.clockDomainId());
        var spans = row.putArray("spans");
        for (Span span : snapshot.spans()) {
            ObjectNode item = spans.addObject(); item.put("stage", span.stage().name()); item.put("terminal", span.terminal().name());
            item.set("began", tick(span.began())); item.set("ended", tick(span.ended()));
        }
        if (snapshot.acknowledgements().isPresent()) {
            Acknowledgements a = snapshot.acknowledgements().orElseThrow(); ObjectNode item = row.putObject("acknowledgements");
            item.put("command_count", a.commandCount()); item.put("accepted_ack_count", a.acceptedAckCount());
            item.put("original_projection_sha256", a.originalProjectionSha256());
        } else { row.putNull("acknowledgements"); }
        if (snapshot.nativeObservation().isPresent()) {
            NativeObservation n = snapshot.nativeObservation().orElseThrow(); ObjectNode item = row.putObject("native_observation");
            item.put("command_count", n.commandCount()); item.put("accepted_ack_count", n.acceptedAckCount());
            item.put("starting_date_raw", n.startingDateRaw()); item.put("ending_date_raw", n.endingDateRaw());
            item.put("original_projection_sha256", n.originalProjectionSha256());
        } else { row.putNull("native_observation"); }
        if (snapshot.savedWindow().isPresent()) {
            SavedWindow window = snapshot.savedWindow().orElseThrow(); ObjectNode item = row.putObject("saved_window");
            item.set("before", saved(window.before())); item.set("after", saved(window.after()));
        } else { row.putNull("saved_window"); }
        return StrictJson.canonical(row);
    }

    public static Snapshot decode(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "context", "spans", "acknowledgements", "native_observation", "saved_window"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact decision metric version required");
        ObjectNode c = StrictJson.object(row.get("context"), Set.of("machine_id", "scope_id", "batch_id", "request_id", "clock_domain_id"));
        Context context = new Context(text(c, "machine_id"), text(c, "scope_id"), text(c, "batch_id"), text(c, "request_id"), text(c, "clock_domain_id"));
        JsonNode sourceSpans = row.get("spans"); StrictJson.require(sourceSpans.isArray(), "metric spans must be an array");
        var spans = new java.util.ArrayList<Span>();
        for (JsonNode value : sourceSpans) {
            ObjectNode item = StrictJson.object(value, Set.of("stage", "terminal", "began", "ended"));
            spans.add(new Span(Stage.valueOf(text(item, "stage")), tick(item.get("began")), tick(item.get("ended")), Terminal.valueOf(text(item, "terminal"))));
        }
        Optional<Acknowledgements> acknowledgements = Optional.empty(); JsonNode a = row.get("acknowledgements");
        if (!a.isNull()) {
            ObjectNode item = StrictJson.object(a, Set.of("command_count", "accepted_ack_count", "original_projection_sha256"));
            acknowledgements = Optional.of(new Acknowledgements(integer(item, "command_count"), integer(item, "accepted_ack_count"), text(item, "original_projection_sha256")));
        }
        Optional<NativeObservation> nativeObservation = Optional.empty(); JsonNode n = row.get("native_observation");
        if (!n.isNull()) {
            ObjectNode item = StrictJson.object(n, Set.of("command_count", "accepted_ack_count", "starting_date_raw", "ending_date_raw", "original_projection_sha256"));
            nativeObservation = Optional.of(new NativeObservation(integer(item, "command_count"), integer(item, "accepted_ack_count"),
                    integer(item, "starting_date_raw"), integer(item, "ending_date_raw"), text(item, "original_projection_sha256")));
        }
        Optional<SavedWindow> savedWindow = Optional.empty(); JsonNode s = row.get("saved_window");
        if (!s.isNull()) {
            ObjectNode item = StrictJson.object(s, Set.of("before", "after")); savedWindow = Optional.of(new SavedWindow(saved(item.get("before")), saved(item.get("after"))));
        }
        return new Snapshot(context, spans, acknowledgements, nativeObservation, savedWindow);
    }

    static ObjectNode tick(Tick tick) {
        ObjectNode item = StrictJson.object(); item.put("clock_domain_id", tick.clockDomainId());
        item.put("elapsed_nanos", Long.toString(tick.elapsedNanos())); item.put("utc", tick.utc().toString());
        item.put("thread_id", Long.toString(tick.threadId()));
        if (tick.threadCpuNanos().isPresent()) { item.put("thread_cpu_nanos", Long.toString(tick.threadCpuNanos().getAsLong())); }
        else { item.putNull("thread_cpu_nanos"); }
        return item;
    }
    static Tick tick(JsonNode value) {
        ObjectNode item = StrictJson.object(value, Set.of("clock_domain_id", "elapsed_nanos", "utc", "thread_id", "thread_cpu_nanos"));
        JsonNode cpu = item.get("thread_cpu_nanos");
        return new Tick(text(item, "clock_domain_id"), decimal(item.get("elapsed_nanos")), Instant.parse(StrictJson.utc(text(item, "utc"))),
                decimal(item.get("thread_id")), cpu.isNull() ? OptionalLong.empty() : OptionalLong.of(decimal(cpu)));
    }
    private static ObjectNode saved(SavedObservation saved) {
        ObjectNode item = StrictJson.object(); item.put("machine_id", saved.machineId()); item.put("date_raw", saved.dateRaw());
        item.set("canonical_proof", saved.canonicalProof().toJson()); item.set("save", saved.save().toJson()); return item;
    }
    private static SavedObservation saved(JsonNode value) {
        ObjectNode item = StrictJson.object(value, Set.of("machine_id", "date_raw", "canonical_proof", "save"));
        return new SavedObservation(text(item, "machine_id"), integer(item, "date_raw"), ExactRef.fromJson(item.get("canonical_proof")), ExactRef.fromJson(item.get("save")));
    }
    private static long decimal(JsonNode value) {
        String text = StrictJson.text(value); StrictJson.require(text.matches("0|[1-9][0-9]*"), "canonical decimal string required for 64-bit metric");
        BigInteger integer = new BigInteger(text); StrictJson.require(integer.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "signed monotonic domain exceeded");
        return integer.longValueExact();
    }
    private static int integer(ObjectNode item, String field) { return (int) StrictJson.integer(item.get(field), 0, Integer.MAX_VALUE); }
    private static String text(ObjectNode item, String field) { return StrictJson.text(item.get(field)); }
    private static void wholeDays(int start, int end) {
        StrictJson.require(start >= 0 && end >= start && (end - start) % 24 == 0, "forward complete native game-day dates required");
    }
    private static void sha(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "exact projection SHA-256 required"); }
}

