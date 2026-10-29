package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.PrisonerOrdinaryPolicy12004;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;

/** Operation-specific original diagnostics. Never submits; timeout requires the original typed deadline proof. */
public final class PrisonerPublicFailure12004 extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public enum Operation {
        COLLECTION("private prisoner collection"), RANSOM("private ransom"), RELEASE("private release");
        private final String prefix;
        Operation(String prefix) { this.prefix = prefix; }
    }
    public enum Kind { UNAVAILABLE, UNKNOWN, RESPONSE_TIMEOUT, REJECTED_BEFORE_DISPATCH, NATIVE_RED, MALFORMED_ACK }
    private static final NativeWire.Field NO_NATIVE_ERROR = new NativeWire.Field(NativeWire.Presence.ABSENT, Optional.empty());
    private final Operation operation;
    private final Kind kind;
    private final Optional<NativeActionPort.DispatchOutcome> originalOutcome;
    private final Optional<PlanningReadResult.Unavailable<RawJson>> originalRead;
    private final Optional<ActionReceipt> canonicalReceipt;
    private final List<ExactRef> originalReferences;
    private final NativeWire.Field nativeError;

    private PrisonerPublicFailure12004(Operation operation, Kind kind, String message, Throwable cause,
            Optional<NativeActionPort.DispatchOutcome> originalOutcome,
            Optional<PlanningReadResult.Unavailable<RawJson>> originalRead, Optional<ActionReceipt> canonicalReceipt,
            List<ExactRef> originalReferences, NativeWire.Field nativeError) {
        super(Objects.requireNonNull(message), cause);
        StrictJson.require(!message.isEmpty(), "original prisoner diagnostic must be nonempty");
        this.operation = Objects.requireNonNull(operation); this.kind = Objects.requireNonNull(kind);
        this.originalOutcome = Objects.requireNonNull(originalOutcome); this.originalRead = Objects.requireNonNull(originalRead);
        this.canonicalReceipt = Objects.requireNonNull(canonicalReceipt); this.originalReferences = List.copyOf(originalReferences);
        this.originalReferences.forEach(ref -> StrictJson.require(ref.bytes() > 0, "original prisoner evidence must be nonempty"));
        this.nativeError = Objects.requireNonNull(nativeError);
    }
    public Operation operation() { return operation; }
    public Kind kind() { return kind; }
    public Optional<NativeActionPort.DispatchOutcome> originalOutcome() { return originalOutcome; }
    public Optional<PlanningReadResult.Unavailable<RawJson>> originalRead() { return originalRead; }
    public Optional<ActionReceipt> canonicalReceipt() { return canonicalReceipt; }
    public List<ExactRef> originalReferences() { return originalReferences; }
    public NativeWire.Field nativeError() { return nativeError; }
    public Optional<String> requestId() { return originalOutcome.map(NativeActionPort.DispatchOutcome::requestId); }
    /** Only the original release native-RED branch published these two Python exception attributes. */
    public boolean publishesNativeAttributes() { return operation == Operation.RELEASE && kind == Kind.NATIVE_RED; }
    public String pythonClassName() { return "BridgeUnavailableError"; }

    public static Operation operation(OperationKey key) {
        if (PrisonerOrdinaryPolicy12004.RANSOM.equals(Objects.requireNonNull(key))) return Operation.RANSOM;
        if (PrisonerOrdinaryPolicy12004.RELEASE.equals(key)) return Operation.RELEASE;
        throw new IllegalArgumentException("public prisoner failure needs its actual ransom/release operation");
    }

    public static PrisonerPublicFailure12004 read(PlanningReadResult.Unavailable<RawJson> original, ExactRef source,
            OperationKey operation, Instant deadline) {
        Objects.requireNonNull(original); Objects.requireNonNull(source); Objects.requireNonNull(operation); Objects.requireNonNull(deadline);
        StrictJson.require(java.util.stream.IntStream.range(0, 64).anyMatch(ordinal -> PrisonerNativeQueries.step(ordinal).equals(operation.value())),
                "actual prisoner collection contract operation required");
        var outcome = original.original();
        if (outcome.orElse(null) instanceof NativeActionPort.AckReceived ack && !ack.nativeOk())
            return nativeRed(Operation.COLLECTION, ack, Optional.of(original), Optional.empty(), List.of(source));
        if (outcome.orElse(null) instanceof NativeActionPort.Unknown unknown
                && responseTimeout(unknown, operation, deadline, Optional.empty(), Optional.empty()))
            return failure(Operation.COLLECTION, Kind.RESPONSE_TIMEOUT, timeoutMessage(Operation.COLLECTION), null,
                    outcome, Optional.of(original), Optional.empty(), List.of(source), NO_NATIVE_ERROR);
        Kind kind = outcome.orElse(null) instanceof NativeActionPort.Unknown ? Kind.UNKNOWN
                : outcome.orElse(null) instanceof NativeActionPort.RejectedBeforeDispatch ? Kind.REJECTED_BEFORE_DISPATCH : Kind.UNAVAILABLE;
        String reason = outcome.orElse(null) instanceof NativeActionPort.Unknown unknown ? unknown.reason() : original.reason();
        return failure(Operation.COLLECTION, kind, reason, null, outcome, Optional.of(original), Optional.empty(), List.of(source), NO_NATIVE_ERROR);
    }

    /** Uses the original locked archive only; no new receipt or reference is manufactured. */
    public static Optional<PrisonerPublicFailure12004> canonical(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(receipt); Objects.requireNonNull(archive);
        Operation operation = operation(receipt.command().operation());
        ExactRef receiptRef = archive.receiptReferenceOf(receipt);
        StrictJson.require(archive.loadReceipt(receiptRef).equals(receipt), "canonical public prisoner receipt changed");
        var dispatch = ActionTransitions.dispatch(receipt.state());
        var references = new ArrayList<ExactRef>(); references.add(receiptRef);
        if (dispatch.isPresent()) {
            var original = dispatch.orElseThrow(); var dispatchRef = archive.referenceOf(original);
            StrictJson.require(archive.load(dispatchRef).equals(original), "canonical prisoner dispatch original changed");
            references.add(dispatchRef);
            if (original instanceof NativeActionPort.AckReceived ack) {
                if (!ack.nativeOk()) return Optional.of(nativeRed(operation, ack, Optional.empty(), Optional.of(receipt), references));
                return Optional.empty();
            }
            if (original instanceof NativeActionPort.Unknown unknown) {
                var attempt = ActionTransitions.attempt(receipt.state());
                boolean timeout = attempt.isPresent() && responseTimeout(unknown, receipt.command().operation(), receipt.command().deadline(),
                        Optional.of(receipt.command().before().frame().identity().nativeRevision()), Optional.of(attempt.orElseThrow().preparedRequest()));
                return Optional.of(failure(operation, timeout ? Kind.RESPONSE_TIMEOUT : Kind.UNKNOWN,
                        timeout ? timeoutMessage(operation) : unknown.reason(), null, dispatch, Optional.empty(), Optional.of(receipt), references, NO_NATIVE_ERROR));
            }
            var rejected = (NativeActionPort.RejectedBeforeDispatch) original;
            return Optional.of(failure(operation, Kind.REJECTED_BEFORE_DISPATCH, rejected.proof().reason(), null,
                    dispatch, Optional.empty(), Optional.of(receipt), references, NO_NATIVE_ERROR));
        }
        String reason = receipt.state() instanceof ActionState.Unknown unknown ? unknown.reason()
                : operation.prefix + " submission has no retained dispatch outcome";
        return Optional.of(failure(operation, Kind.UNKNOWN, reason, null, Optional.empty(), Optional.empty(),
                Optional.of(receipt), references, NO_NATIVE_ERROR));
    }

    public static PrisonerPublicFailure12004 malformedAcknowledgement(ActionReceipt receipt, ActionPorts.OutcomeArchive archive) {
        var outcome = ActionTransitions.dispatch(receipt.state());
        StrictJson.require(outcome.orElse(null) instanceof NativeActionPort.AckReceived, "malformed ACK requires an actual canonical ACK");
        var references = List.of(archive.receiptReferenceOf(receipt), archive.referenceOf(outcome.orElseThrow()));
        return failure(operation(receipt.command().operation()), Kind.MALFORMED_ACK,
                operation(receipt.command().operation()).prefix + " ACK is not a material result", null,
                outcome, Optional.empty(), Optional.of(receipt), references, NO_NATIVE_ERROR);
    }
    public static PrisonerPublicFailure12004 local(Operation operation, Throwable cause, List<ExactRef> references) {
        Objects.requireNonNull(cause);
        String reason = cause.getMessage(); if (reason == null || reason.isEmpty()) reason = cause.getClass().getName();
        return failure(operation, Kind.UNAVAILABLE, reason, cause, Optional.empty(), Optional.empty(), Optional.empty(), references, NO_NATIVE_ERROR);
    }

    private static String timeoutMessage(Operation operation) {
        return operation == Operation.COLLECTION ? "private prisoner collection command_result timed out"
                : operation.prefix + " submission is unresolved after timeout";
    }
    /** Only the source-issued response deadline proof and its original request may select Python's timeout branch. */
    private static boolean responseTimeout(NativeActionPort.Unknown original, OperationKey operation, Instant deadline,
            Optional<java.math.BigInteger> nativeRevision, Optional<NativeRequest> prepared) {
        if (original.failureCause().isEmpty()) return false;
        var cause = original.failureCause().orElseThrow();
        if (cause.kind() != NativeActionPort.FailureKind.DEADLINE_EXPIRED || cause.stage() != NativeActionPort.FailureStage.RESPONSE_WAIT
                || cause.deadline().isEmpty() || !cause.deadline().orElseThrow().suppliedDeadline().equals(deadline)) return false;
        try {
            var sent = NativeWire.decodeExecuteRequest(original.originalRequestPacket());
            if (!sent.requestId().equals(original.requestId()) || !sent.step().equals(operation.value())
                    || sent.expectedRevision().isEmpty() || sent.expectedRevision().orElseThrow().signum() <= 0
                    || nativeRevision.isPresent() && !sent.expectedRevision().orElseThrow().equals(nativeRevision.orElseThrow())) return false;
            if (prepared.isPresent()) {
                var expected = prepared.orElseThrow();
                if (!expected.step().equals(sent.step()) || !StrictJson.parse(expected.additionalFields().bytes(), RawJson.MAXIMUM_BYTES)
                        .equals(StrictJson.parse(sent.normalizedAdditionalFields().value(), RawJson.MAXIMUM_BYTES))) return false;
            }
            return true;
        } catch (IOException | IllegalArgumentException malformedOriginal) { return false; }
    }

    static PrisonerPublicFailure12004 nativeRed(Operation operation, NativeActionPort.AckReceived ack,
            Optional<PlanningReadResult.Unavailable<RawJson>> read, Optional<ActionReceipt> receipt, List<ExactRef> references) {
        try {
            var decoded = NativeWire.decode(ack.originalPacket());
            StrictJson.require(decoded instanceof NativeWire.CommandResult, "prisoner native error requires its original command_result");
            var result = (NativeWire.CommandResult) decoded;
            StrictJson.require(!result.nativeOk() && result.requestId().equals(ack.requestId())
                    && java.util.Arrays.equals(result.payload().value(), ack.originalFrame().bytes()), "prisoner native error packet/payload/request differs");
            NativeWire.Field error = result.error(); JsonNode value = error.presence() == NativeWire.Presence.VALUE
                    ? StrictJson.parse(error.token().orElseThrow().value(), RawJson.MAXIMUM_BYTES) : null;
            String message;
            if (operation == Operation.COLLECTION) message = operation.prefix + " native RED: "
                    + (value != null && value.isTextual() && !value.textValue().isEmpty() ? value.textValue() : "unknown native error");
            else message = operation.prefix + " native RED: " + repr(value);
            return failure(operation, Kind.NATIVE_RED, message, null, Optional.of(ack), read, receipt, references, error);
        } catch (IOException | IllegalArgumentException malformed) {
            return failure(operation, Kind.MALFORMED_ACK, operation.prefix + (operation == Operation.COLLECTION
                    ? " command_result is malformed" : " command result is malformed"), malformed,
                    Optional.of(ack), read, receipt, references, NO_NATIVE_ERROR);
        }
    }
    private static PrisonerPublicFailure12004 failure(Operation operation, Kind kind, String message, Throwable cause,
            Optional<NativeActionPort.DispatchOutcome> outcome, Optional<PlanningReadResult.Unavailable<RawJson>> read,
            Optional<ActionReceipt> receipt, List<ExactRef> references, NativeWire.Field nativeError) {
        return new PrisonerPublicFailure12004(operation, kind, message, cause, outcome, read, receipt, references, nativeError);
    }
    /** Python repr for the JSON value retained by command_result.error, including missing-as-None. */
    private static String repr(JsonNode value) {
        if (value == null || value.isNull()) return "None";
        if (value.isTextual()) return reprText(value.textValue());
        if (value.isBoolean()) return value.booleanValue() ? "True" : "False";
        if (value.isIntegralNumber()) return value.bigIntegerValue().toString();
        if (value.isFloatingPointNumber()) {
            double number = value.doubleValue(); StrictJson.require(Double.isFinite(number), "finite original native error number required");
            // JSON-decoded Python float and Java double share IEEE754; match Python's decimal/exponent spelling.
            String text = Double.toString(number).toLowerCase(java.util.Locale.ROOT);
            int exponent = text.indexOf('e');
            if (exponent >= 0) {
                String mantissa = text.substring(0, exponent); int power = Integer.parseInt(text.substring(exponent + 1));
                if (power >= -4 && power < 16) {
                    String plain = java.math.BigDecimal.valueOf(number).stripTrailingZeros().toPlainString();
                    return plain.indexOf('.') < 0 ? plain + ".0" : plain;
                }
                if (mantissa.endsWith(".0")) mantissa = mantissa.substring(0, mantissa.length() - 2);
                return mantissa + "e" + (power >= 0 ? "+" : "-") + String.format(java.util.Locale.ROOT, "%02d", Math.abs(power));
            }
            return text;
        }
        var parts = new ArrayList<String>();
        if (value.isArray()) { value.forEach(item -> parts.add(repr(item))); return "[" + String.join(", ", parts) + "]"; }
        StrictJson.require(value.isObject(), "native error must retain its JSON domain");
        value.fields().forEachRemaining(entry -> parts.add(reprText(entry.getKey()) + ": " + repr(entry.getValue())));
        return "{" + String.join(", ", parts) + "}";
    }
    private static String reprText(String text) {
        char quote = text.indexOf('\'') >= 0 && text.indexOf('"') < 0 ? '"' : '\'';
        var out = new StringBuilder().append(quote);
        text.codePoints().forEach(code -> {
            if (code == quote || code == '\\') out.append('\\').appendCodePoint(code);
            else if (code == '\n') out.append("\\n"); else if (code == '\r') out.append("\\r"); else if (code == '\t') out.append("\\t");
            else {
                int type = Character.getType(code);
                boolean printable = code == 0x20 || !(Character.isISOControl(code) || type == Character.FORMAT
                        || type == Character.SURROGATE || type == Character.PRIVATE_USE || type == Character.UNASSIGNED
                        || type == Character.SPACE_SEPARATOR || type == Character.LINE_SEPARATOR || type == Character.PARAGRAPH_SEPARATOR);
                if (printable) out.appendCodePoint(code);
                else if (code <= 0xff) out.append(String.format(java.util.Locale.ROOT, "\\x%02x", code));
                else if (code <= 0xffff) out.append(String.format(java.util.Locale.ROOT, "\\u%04x", code));
                else out.append(String.format(java.util.Locale.ROOT, "\\U%08x", code));
            }
        });
        return out.append(quote).toString();
    }
}
