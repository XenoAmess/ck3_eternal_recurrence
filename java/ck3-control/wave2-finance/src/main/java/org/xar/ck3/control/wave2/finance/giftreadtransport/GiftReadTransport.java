package org.xar.ck3.control.wave2.finance.giftreadtransport;

import java.io.Serial;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.Objects;
import java.util.UUID;
import java.util.function.Supplier;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.CandidateResult;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootProjection;

/** Read-only application adapter. Only an existing owned driver can implement the narrow port. */
public final class GiftReadTransport {
    private GiftReadTransport() { }
    public enum Presence { MISSING, NULL, VALUE }
    public record Read<T>(Presence presence, T value) {
        public Read {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("read presence/value mismatch"); }
        }
        public static <T> Read<T> missing() { return new Read<>(Presence.MISSING, null); }
        public static <T> Read<T> nil() { return new Read<>(Presence.NULL, null); }
        public static <T> Read<T> of(T value) { return new Read<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean known() { return presence == Presence.VALUE; }
        public boolean nullLike() { return presence != Presence.VALUE; }
    }
    /** Validated opaque SDK JSON, defensively copied; business logic uses the typed projection. */
    public static final class ObjectDocument {
        private final byte[] bytes;
        ObjectDocument(byte[] bytes) { this.bytes = bytes.clone(); }
        public byte[] bytes() { return bytes.clone(); }
    }
    public record OpaqueValue(String canonicalJson) {
        public OpaqueValue { Objects.requireNonNull(canonicalJson); }
    }
    public record Binding(Read<String> snapshotId, Read<BigInteger> revision, Read<BigInteger> nativeRevision,
            Read<BigInteger> dateRaw, Read<Boolean> paused, Read<Boolean> mapReady,
            Read<BigInteger> actorId, Read<Boolean> actorAlive, Read<OpaqueValue> activeEvent,
            Read<OpaqueValue> pendingInteraction) {
        public Binding {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(paused); Objects.requireNonNull(mapReady);
            Objects.requireNonNull(actorId); Objects.requireNonNull(actorAlive);
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingInteraction);
        }
        public boolean sameOriginalGetValues(Binding other) {
            return same(snapshotId, other.snapshotId) && same(revision, other.revision)
                    && same(nativeRevision, other.nativeRevision) && same(dateRaw, other.dateRaw)
                    && same(paused, other.paused) && same(mapReady, other.mapReady)
                    && same(actorId, other.actorId) && same(actorAlive, other.actorAlive)
                    && same(activeEvent, other.activeEvent) && same(pendingInteraction, other.pendingInteraction);
        }
        private static <T> boolean same(Read<T> left, Read<T> right) {
            return left.nullLike() && right.nullLike() || left.known() && right.known() && left.value().equals(right.value());
        }
    }
    public record Snapshot(ObjectDocument original, Binding binding, Read<OpaqueValue> terminalReason) {
        public Snapshot { Objects.requireNonNull(original); Objects.requireNonNull(binding); Objects.requireNonNull(terminalReason); }
    }
    public record Diagnostics(Read<Boolean> privateBuild) {
        public Diagnostics { Objects.requireNonNull(privateBuild); }
    }
    /** Original timeout is positive seconds, not an integer identity; no binary floating conversion. */
    public record Timeout(BigDecimal seconds) {
        public Timeout {
            Objects.requireNonNull(seconds);
            if (seconds.signum() <= 0) { throw new IllegalArgumentException("faction gift query timeout must be positive"); }
        }
    }
    public record ReadId(String value) {
        public ReadId {
            Objects.requireNonNull(value);
            if (!value.matches("faction-gift-read-[0-9a-f]{32}")) { throw new IllegalArgumentException("canonical one-shot read identity required"); }
        }
    }
    public record Command(ReadId requestId, BigInteger expectedRevision, BigInteger expectedDateRaw,
            BigInteger expectedPlayerCharacterId) {
        public Command {
            Objects.requireNonNull(requestId); Objects.requireNonNull(expectedRevision);
            Objects.requireNonNull(expectedDateRaw); Objects.requireNonNull(expectedPlayerCharacterId);
            if (expectedRevision.signum() <= 0 || expectedDateRaw.signum() < 0 || expectedPlayerCharacterId.signum() <= 0) {
                throw new IllegalArgumentException("ordinary query command frame required");
            }
        }
    }
    public record Envelope(Read<String> type, Read<BigInteger> protocolVersion, Read<String> requestId,
            Read<Boolean> ok, Read<ObjectDocument> result, Read<String> error) {
        public Envelope {
            Objects.requireNonNull(type); Objects.requireNonNull(protocolVersion); Objects.requireNonNull(requestId);
            Objects.requireNonNull(ok); Objects.requireNonNull(result); Objects.requireNonNull(error);
        }
    }
    public sealed interface WaitResult permits TimedOut, Received { }
    public record TimedOut() implements WaitResult { }
    public record Received(Envelope envelope) implements WaitResult {
        public Received { Objects.requireNonNull(envelope); }
    }
    public interface ExistingOwnedReadPort {
        Snapshot takeInternalSemanticSnapshot();
        Diagnostics diagnostics();
        void send(Command command);
        WaitResult waitForCommandResult(ReadId requestId, Timeout timeout);
    }
    public record Request(Snapshot expectedSnapshot, RootProjection root, BigInteger minimumGoldReserveRaw,
            Timeout timeout) {
        public Request {
            Objects.requireNonNull(expectedSnapshot); Objects.requireNonNull(root);
            Objects.requireNonNull(minimumGoldReserveRaw); Objects.requireNonNull(timeout);
        }
    }
    public sealed interface Result permits PrivateRouteOff, Candidate { }
    public record PrivateRouteOff() implements Result { }
    public record Candidate(CandidateResult candidate) implements Result {
        public Candidate { Objects.requireNonNull(candidate); }
    }
    public enum Failure {
        SOURCE_CHANGED("private faction query source frame changed"),
        ORDINARY_FRAME_REQUIRED("private faction query requires an ordinary paused living-player frame"),
        ROOT_REQUIRED("private faction query lacks same-frame public root"),
        TARGETING_COUNT_REQUIRED("private faction query lacks a nonempty exact targeting count"),
        TIMED_OUT("private faction query command_result timed out"),
        COMMAND_RESULT_RED("private faction query returned RED or malformed command_result"),
        RESULT_MISSING("private faction query result is missing"),
        FRAME_CROSSED("private faction query crossed its paused frame");
        private final String message;
        Failure(String message) { this.message = message; }
        public String message() { return message; }
    }
    public static final class ReadFailure extends RuntimeException {
        @Serial private static final long serialVersionUID = 1L;
        private final Failure failure;
        ReadFailure(Failure failure) { super(failure.message()); this.failure = failure; }
        ReadFailure(Failure failure, String detail) { super(failure.message() + ": " + detail); this.failure = failure; }
        public Failure failure() { return failure; }
    }

    public static Result query(Request request, ExistingOwnedReadPort port) {
        return query(request, port, () -> "faction-gift-read-" + UUID.randomUUID().toString().replace("-", ""));
    }

    public static Result query(Request request, ExistingOwnedReadPort port, Supplier<String> readIdFactory) {
        Objects.requireNonNull(request); Objects.requireNonNull(port); Objects.requireNonNull(readIdFactory);
        Snapshot before = Objects.requireNonNull(port.takeInternalSemanticSnapshot()); Binding binding = before.binding();
        if (!binding.sameOriginalGetValues(request.expectedSnapshot().binding())) { throw new ReadFailure(Failure.SOURCE_CHANGED); }
        if (!ordinary(before)) { throw new ReadFailure(Failure.ORDINARY_FRAME_REQUIRED); }
        Diagnostics diagnostics = Objects.requireNonNull(port.diagnostics());
        if (!yes(diagnostics.privateBuild())) { return new PrivateRouteOff(); }
        FactionCandidatePolicy.Frame frame = new FactionCandidatePolicy.Frame(binding.nativeRevision().value(),
                binding.dateRaw().value(), binding.actorId().value());
        if (request.root().frame().filter(frame::equals).isEmpty()
                || request.root().governmentKey().filter("feudal_government"::equals).isEmpty()) {
            throw new ReadFailure(Failure.ROOT_REQUIRED);
        }
        if (request.root().targetingCount().isEmpty() || request.root().targetingCount().get().signum() <= 0) {
            throw new ReadFailure(Failure.TARGETING_COUNT_REQUIRED);
        }
        ReadId id = new ReadId(readIdFactory.get());
        port.send(new Command(id, frame.nativeRevision(), frame.dateRaw(), frame.actorId()));
        WaitResult waited = Objects.requireNonNull(port.waitForCommandResult(id, request.timeout()));
        if (waited instanceof TimedOut) { throw new ReadFailure(Failure.TIMED_OUT); }
        Envelope envelope = ((Received) waited).envelope();
        if (!equal(envelope.type(), "command_result") || !equal(envelope.protocolVersion(), BigInteger.ONE)
                || !equal(envelope.requestId(), id.value()) || !yes(envelope.ok())) {
            String error = envelope.error().known() && !envelope.error().value().isEmpty() ? envelope.error().value() : "unknown";
            throw new ReadFailure(Failure.COMMAND_RESULT_RED, error);
        }
        if (!envelope.result().known()) { throw new ReadFailure(Failure.RESULT_MISSING); }
        Snapshot after = Objects.requireNonNull(port.takeInternalSemanticSnapshot());
        if (!after.binding().sameOriginalGetValues(binding)) { throw new ReadFailure(Failure.FRAME_CROSSED); }
        return new Candidate(FactionCandidateCodec.evaluatePrivateCandidate(before.original().bytes(), request.root(),
                envelope.result().value().bytes(), request.minimumGoldReserveRaw()));
    }

    private static boolean ordinary(Snapshot snapshot) {
        Binding frame = snapshot.binding();
        return yes(frame.paused()) && yes(frame.mapReady()) && yes(frame.actorAlive())
                && positive(frame.actorId()) && positive(frame.nativeRevision())
                && frame.dateRaw().known() && frame.dateRaw().value().signum() >= 0
                && frame.activeEvent().nullLike() && frame.pendingInteraction().nullLike() && snapshot.terminalReason().nullLike();
    }
    private static boolean positive(Read<BigInteger> value) { return value.known() && value.value().signum() > 0; }
    private static boolean yes(Read<Boolean> value) { return value.known() && value.value().booleanValue(); }
    private static <T> boolean equal(Read<T> value, T expected) { return value.known() && value.value().equals(expected); }
}
