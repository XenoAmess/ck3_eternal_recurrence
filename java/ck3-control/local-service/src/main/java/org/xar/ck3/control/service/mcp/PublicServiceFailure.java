package org.xar.ck3.control.service.mcp;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original service fault carried to the existing MCP ToolFailure boundary, never an action ACK. */
public final class PublicServiceFailure extends RuntimeException {
    private static final long serialVersionUID=1L;
    public enum Kind {
        BRIDGE_UNAVAILABLE("BridgeUnavailableError"),
        PRE_SUBMISSION_REVISION_MISMATCH("PreSubmissionRevisionMismatchError"),
        FACTION_GIFT_PENDING_FRAME_READY("FactionGiftPendingFrameReadyError"),
        UNSUPPORTED_STEP("UnsupportedStepError"),
        VALUE_ERROR("ValueError"),
        STEP_POSTCONDITION_ERROR("StepPostconditionError"),
        NATIVE_COMMAND_REJECTED("_NativeCommandRejectedError"),
        NATIVE_COMMAND_RESULT_TIMEOUT("_NativeCommandResultTimeoutError"),
        RUNTIME_ERROR("RuntimeError");
        private final String pythonClassName;
        Kind(String pythonClassName){this.pythonClassName=pythonClassName;}
        public String pythonClassName(){return pythonClassName;}
        public static Kind exact(String original) {
            for(Kind kind:values())if(kind.pythonClassName.equals(original))return kind;
            throw new IllegalArgumentException("unsupported original public service error type");
        }
    }
    /** Original PreSubmissionRevisionMismatchError(message) constructor defaults. */
    public enum PreSubmissionDefaults {
        ORIGINAL;
        public Optional<RawJson> selectedStep(){return Optional.empty();}
        public Optional<RawJson> plan(){return Optional.empty();}
        public int replanCount(){return 0;}
    }
    /** Only producer-proven original public exception attributes, never an inferred native result. */
    public record NativeAttributes(RawJson nativeError,String requestId) {
        public NativeAttributes {
            Objects.requireNonNull(nativeError);nativeError.requireProtocolBound();
            StrictJson.require(requestId!=null&&!requestId.isBlank(),"original native request id required");
        }
    }
    /** Keeps the same source carrier; all its outcomes, receipts and reference lists remain accessible. */
    public record Details(RuntimeException originalFailure,Optional<NativeAttributes> nativeAttributes,
            Optional<PreSubmissionDefaults> preSubmissionDefaults) {
        public Details {
            Objects.requireNonNull(originalFailure);Objects.requireNonNull(nativeAttributes);
            Objects.requireNonNull(preSubmissionDefaults);
        }
    }
    private final Kind kind;
    private final Optional<ExactRef> originalCandidate;
    private final Optional<Details> details;
    public PublicServiceFailure(Kind kind,String originalMessage,Optional<ExactRef> originalCandidate) {
        super(Objects.requireNonNull(originalMessage));
        StrictJson.require(!originalMessage.isEmpty(),"original service error message required");
        this.kind=Objects.requireNonNull(kind);this.originalCandidate=Objects.requireNonNull(originalCandidate);
        originalCandidate.ifPresent(value->StrictJson.require(value.bytes()>0,"nonempty original candidate evidence required"));
        details=Optional.empty();
    }
    public PublicServiceFailure(Kind kind,String originalMessage,Optional<ExactRef> originalCandidate,Details originalDetails) {
        super(Objects.requireNonNull(originalMessage),Objects.requireNonNull(originalDetails).originalFailure());
        StrictJson.require(!originalMessage.isEmpty(),"original service error message required");
        this.kind=Objects.requireNonNull(kind);this.originalCandidate=Objects.requireNonNull(originalCandidate);
        originalCandidate.ifPresent(value->StrictJson.require(value.bytes()>0,"nonempty original candidate evidence required"));
        StrictJson.require(originalMessage.equals(originalDetails.originalFailure().getMessage()),"source service error message changed");
        StrictJson.require(originalDetails.nativeAttributes().isEmpty()||kind==Kind.BRIDGE_UNAVAILABLE,
                "native public attributes require the original bridge failure profile");
        StrictJson.require(originalDetails.preSubmissionDefaults().isEmpty()||kind==Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                "pre-submission defaults require the original revision mismatch profile");
        details=Optional.of(originalDetails);
    }
    public Kind kind(){return kind;}
    public Optional<ExactRef> originalCandidate(){return originalCandidate;}
    public Optional<Details> details(){return details;}
    public Optional<RuntimeException> originalFailure(){return details.map(Details::originalFailure);}
    public Optional<NativeAttributes> nativeAttributes(){return details.flatMap(Details::nativeAttributes);}
    public Optional<PreSubmissionDefaults> preSubmissionDefaults(){return details.flatMap(Details::preSubmissionDefaults);}
}
