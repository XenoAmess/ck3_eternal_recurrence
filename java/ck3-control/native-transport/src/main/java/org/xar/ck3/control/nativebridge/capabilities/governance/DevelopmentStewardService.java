package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.NativeWire;

/** The actual current headless service branch, including original precheck/error order. */
public final class DevelopmentStewardService {
    private DevelopmentStewardService() { }

    public enum ErrorKind {
        BRIDGE_UNAVAILABLE("BridgeUnavailableError"),
        PRE_SUBMISSION_REVISION_MISMATCH("PreSubmissionRevisionMismatchError"),
        UNSUPPORTED_STEP("UnsupportedStepError");
        private final String pythonName;
        ErrorKind(String pythonName) { this.pythonName = pythonName; }
        public String pythonName() { return pythonName; }
    }
    public enum Error {
        PAUSED_REQUIRED(ErrorKind.BRIDGE_UNAVAILABLE,
                "steward develop-county actions require a paused CK3 snapshot"),
        STALE_REVISION(ErrorKind.PRE_SUBMISSION_REVISION_MISMATCH,
                "steward develop-county action source revision is stale"),
        QUERY_UNSUPPORTED(ErrorKind.UNSUPPORTED_STEP,
                "selected backend cannot query steward development candidates"),
        CANDIDATE_UNAVAILABLE(ErrorKind.BRIDGE_UNAVAILABLE,
                "steward develop-county request is not bound to an available same-frame native candidate"),
        TRANSPORT_UNSUPPORTED(ErrorKind.UNSUPPORTED_STEP,
                "selected backend lacks the fail-closed steward develop-county action transport"),
        EXECUTOR_UNSUPPORTED(ErrorKind.UNSUPPORTED_STEP,
                "selected backend has no typed steward develop-county executor");
        private final ErrorKind kind;
        private final String message;
        Error(ErrorKind kind, String message) { this.kind = kind; this.message = message; }
        public ErrorKind kind() { return kind; }
        public String message() { return message; }
    }
    /** Internal persisted diagnostic, not a second MCP error wire. */
    public record Fault(Error error, Optional<ExactRef> candidateOriginal) {
        public Fault {
            Objects.requireNonNull(error); Objects.requireNonNull(candidateOriginal);
            candidateOriginal.ifPresent(ref -> StrictJson.require(ref.bytes() > 0, "nonempty actual candidate evidence required"));
            StrictJson.require(error != Error.PAUSED_REQUIRED && error != Error.STALE_REVISION && error != Error.QUERY_UNSUPPORTED || candidateOriginal.isEmpty(),
                    "pre-query failure cannot claim a candidate was read");
        }
        public ErrorKind kind() { return error.kind(); }
        public String message() { return error.message(); }
    }

    /** Root supplies the original HELLO and executable steps from its actual held readiness lease. */
    public static void beforeCandidateRead(NativeWire.Hello originalHello, Set<OperationKey> originalLeaseExecutableSteps) {
        Objects.requireNonNull(originalHello); Objects.requireNonNull(originalLeaseExecutableSteps);
        if (!originalHello.capabilities().contains("game.command." + DevelopmentStewardAction.QUERY_STEP)
                || !originalLeaseExecutableSteps.contains(new OperationKey(DevelopmentStewardAction.QUERY_STEP)))
            throw failure(Error.QUERY_UNSUPPORTED, Optional.empty());
    }
    public static final class Failure extends RuntimeException {
        private static final long serialVersionUID = 1L;
        // Process-local diagnostic payload; encodeFault is the wire contract, not Java serialization.
        @SuppressWarnings("serial")
        private final Fault fault;
        public Failure(Fault fault) { super(Objects.requireNonNull(fault).message()); this.fault = fault; }
        public Fault fault() { return fault; }
    }

    /** Called before a candidate read; pause has precedence over stale revision. */
    public static void beforeQuery(DevelopmentStewardAction.Request request, boolean actuallyPaused, BigInteger publicRevision) {
        Objects.requireNonNull(request); Objects.requireNonNull(publicRevision);
        if (!actuallyPaused) throw failure(Error.PAUSED_REQUIRED, Optional.empty());
        if (!publicRevision.equals(request.expectedRevision())) throw failure(Error.STALE_REVISION, Optional.empty());
    }

    /** The normalized current Material profile has no native_legal field and fails this original check. */
    public static void candidate(DevelopmentStewardResults.SameFrameFacts facts) {
        Objects.requireNonNull(facts);
        var value = facts.original().value();
        if (!(value instanceof DevelopmentModels.Legacy legacy)
                || legacy.stewardId() != facts.action().councillorId() || !legacy.shown() || !legacy.valid()
                || legacy.taskFailureReason().isPresent() || facts.selectedLegacyCandidate().isEmpty())
            throw failure(Error.CANDIDATE_UNAVAILABLE, Optional.of(facts.original().originalReceipt()));
    }

    /** Cannot be constructed from caller capability strings or a semantic snapshot field. */
    public static final class OriginalCapabilities {
        private final DevelopmentStewardResults.SameFrameFacts facts;
        private final NativeWire.Hello hello;
        private OriginalCapabilities(DevelopmentStewardResults.SameFrameFacts facts, NativeWire.Hello hello) {
            this.facts = facts; this.hello = hello;
        }
        public NativeWire.Hello originalHello() { return hello; }
    }

    /** Root obtains all three original packets from its held transport and same writer archive. */
    public static OriginalCapabilities bindCapabilities(DevelopmentStewardResults.SameFrameFacts facts,
            byte[] currentCachedHello, byte[] archivedBeforeHello, byte[] archivedAfterHello) throws IOException {
        Objects.requireNonNull(facts);
        var receipt = facts.original().receipt();
        original(receipt.before().binding().capabilityEvidence(), archivedBeforeHello);
        original(receipt.after().binding().capabilityEvidence(), archivedAfterHello);
        StrictJson.require(Arrays.equals(currentCachedHello, archivedBeforeHello)
                && Arrays.equals(currentCachedHello, archivedAfterHello), "Steward actual cached/guard HELLO originals differ");
        NativeWire.Frame decoded = NativeWire.decode(currentCachedHello);
        StrictJson.require(decoded instanceof NativeWire.Hello, "Steward original capability packet must be HELLO");
        NativeWire.Hello hello = (NativeWire.Hello) decoded;
        StrictJson.require(hello.pid() == facts.query().before().game().pid()
                && hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration())
                && hello.connectionGeneration().equals(receipt.after().binding().connectionGeneration())
                && hello.gameSha256().equalsIgnoreCase(facts.original().value().provenance().executableSha256())
                && hello.buildMatch() && hello.adapterStatus().equals("ready"),
                "Steward capabilities crossed actual owner/generation/exact source build");
        return new OriginalCapabilities(facts, hello);
    }

    /** This source generation has no headless method. It cannot receive an invented executor/permission. */
    public static Failure currentHeadlessRejection(DevelopmentStewardResults.SameFrameFacts facts,
            OriginalCapabilities capabilities, DevelopmentStewardResults.SourceEvidence actualOriginalSources) {
        Objects.requireNonNull(facts); Objects.requireNonNull(capabilities); Objects.requireNonNull(actualOriginalSources);
        candidate(facts);
        StrictJson.require(capabilities.facts == facts, "Steward HELLO evidence belongs to another candidate read");
        if (!capabilities.hello.capabilities().contains(DevelopmentStewardAction.TRANSPORT_CAPABILITY))
            return failure(Error.TRANSPORT_UNSUPPORTED, Optional.of(facts.original().originalReceipt()));
        // SourceEvidence pins native_driver.py. The mandatory original-producer
        // regression asserts absence on its actual NativeHeadlessGameplayDriver class.
        // There is no callable/boolean dispatch seam in this generation.
        return failure(Error.EXECUTOR_UNSUPPORTED, Optional.of(facts.original().originalReceipt()));
    }
    public static Failure failure(Error error, Optional<ExactRef> candidateOriginal) {
        return new Failure(new Fault(error, candidateOriginal));
    }

    public static RawJson encodeFault(Fault fault) {
        Objects.requireNonNull(fault);
        ObjectNode row = StrictJson.object().put("error", fault.error().name())
                .put("python_error", fault.kind().pythonName()).put("message", fault.message());
        if (fault.candidateOriginal().isEmpty()) row.putNull("candidate_original");
        else {
            ExactRef ref = fault.candidateOriginal().orElseThrow();
            row.putObject("candidate_original").put("path", ref.path()).put("bytes", ref.bytes()).put("sha256", ref.sha256());
        }
        return new RawJson(StrictJson.canonical(row));
    }
    public static Fault decodeFault(RawJson raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw.bytes()), Set.of("error", "python_error", "message", "candidate_original"));
        Error error = Error.valueOf(StrictJson.text(row.get("error")));
        StrictJson.require(StrictJson.text(row.get("python_error")).equals(error.kind().pythonName())
                && StrictJson.text(row.get("message")).equals(error.message()), "Steward error kind/message changed");
        JsonNode ref = row.get("candidate_original");
        Optional<ExactRef> source = Optional.empty();
        if (!ref.isNull()) {
            ObjectNode object = StrictJson.object(ref, Set.of("path", "bytes", "sha256"));
            source = Optional.of(new ExactRef(StrictJson.text(object.get("path")),
                    StrictJson.integer(object.get("bytes"), 1, Long.MAX_VALUE), StrictJson.text(object.get("sha256"))));
        }
        return new Fault(error, source);
    }
    private static void original(ExactRef ref, byte[] packet) {
        var actual = NativeRequestChronology.PacketIdentity.of(packet);
        StrictJson.require(ref.bytes() == actual.bytes() && ref.sha256().equals(actual.sha256()), "Steward archived HELLO hash/bytes changed");
    }
}
