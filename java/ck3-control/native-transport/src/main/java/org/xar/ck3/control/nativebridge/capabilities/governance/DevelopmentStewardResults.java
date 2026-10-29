package org.xar.ck3.control.nativebridge.capabilities.governance;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction.Ack;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction.AckStatus;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction.Receipt;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction.Request;

/** Same-frame facts, the actual closed permission factory, and non-replaying historical receipt reduction. */
public final class DevelopmentStewardResults {
    private DevelopmentStewardResults() { }

    /** Exact original sources explain missing authority; they do not mint native authority. */
    public record SourceEvidence(ExactRef service, ExactRef driver, ExactRef contract, ExactRef nativeExecutor, ExactRef abiLedger) {
        public SourceEvidence {
            pin(service, 897392, "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e");
            pin(driver, 1658471, "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
            pin(contract, 14182, "3a029fc7016922adb773e7ee8192b8c0a12a95e097f08976c0bd1f70df24be12");
            pin(nativeExecutor, 15132, "31f8ac3e392ebd9da78c9a7f413c915a55d58d81f263de18b98f7879badf6453");
            pin(abiLedger, 2113, "c64dee3e0b7a5f1c3855ace909374156e378b2587d941bea1b1efb010b36574c");
        }
        public List<ExactRef> all() { return List.of(service, driver, contract, nativeExecutor, abiLedger); }
    }

    public enum Reason {
        NATIVE_MATERIAL_IS_NOT_ACTION_LEGALITY,
        NATIVE_CANDIDATE_UNAVAILABLE,
        LEGACY_COMMAND_ABI_UNCERTIFIED_AND_DRIVER_EXECUTOR_ABSENT,
        BUILD_HAS_NO_QUALIFIED_STEWARD_EXECUTOR
    }

    /** No certified subtype exists in this source generation. A boolean/callback cannot enable dispatch. */
    public sealed interface Permission permits Unavailable { }
    public record Unavailable(Reason reason, DevelopmentModels.Provenance provenance, SourceEvidence source) implements Permission {
        public Unavailable { Objects.requireNonNull(reason); Objects.requireNonNull(provenance); Objects.requireNonNull(source); }
    }

    public static final class SameFrameFacts {
        private final Request action;
        private final PlanningReadRequest query;
        private final PlanningReadResult.Known<DevelopmentModels.Observation> original;
        private final Optional<DevelopmentModels.LegacyCandidate> selected;
        private SameFrameFacts(Request action, PlanningReadRequest query,
                PlanningReadResult.Known<DevelopmentModels.Observation> original,
                Optional<DevelopmentModels.LegacyCandidate> selected) {
            this.action = action; this.query = query; this.original = original; this.selected = selected;
        }
        public Request action() { return action; }
        public PlanningReadRequest query() { return query; }
        public PlanningReadResult.Known<DevelopmentModels.Observation> original() { return original; }
        public Optional<DevelopmentModels.LegacyCandidate> selectedLegacyCandidate() { return selected; }
    }

    /** The Root additionally verifies this read's actual archive reference under its original writer Session. */
    public static SameFrameFacts bind(Request action, PlanningReadRequest query,
            PlanningReadResult.Known<DevelopmentModels.Observation> original) {
        Objects.requireNonNull(action); Objects.requireNonNull(query); Objects.requireNonNull(original);
        var current = GovernanceNativeReads.frame(query);
        var observed = original.value();
        StrictJson.require(query.operation().value().equals(DevelopmentStewardAction.QUERY_STEP)
                && query.before().frame().revision().equals(action.expectedRevision())
                && original.receipt().request().equals(query) && original.originalReceipt().bytes() > 0
                && observed.frame().nativeRevision().equals(current.nativeRevision())
                && observed.frame().dateRaw() == current.dateRaw()
                && observed.provenance().gameVersion().equals(query.source().exactBuild()),
                "development candidate lost its actual full same-frame request/original/native date");
        GovernanceNativeReads.verifyGuards(original.receipt());
        Optional<DevelopmentModels.LegacyCandidate> selected = Optional.empty();
        if (observed instanceof DevelopmentModels.Legacy legacy) {
            StrictJson.require(legacy.playerId() == current.ownerId(), "legacy candidate belongs to another actual player");
            List<DevelopmentModels.LegacyCandidate> matching = legacy.candidates().stream()
                    .filter(candidate -> candidate.countyTitleId() == action.countyTitleId()).toList();
            StrictJson.require(matching.size() <= 1, "duplicate original native county candidate");
            if (!matching.isEmpty()) selected = Optional.of(matching.getFirst());
        } else if (observed instanceof DevelopmentModels.Material material) {
            StrictJson.require(material.playerId() == current.ownerId(), "development material belongs to another actual player");
        }
        return new SameFrameFacts(action, query, original, selected);
    }

    public record Preparation(SameFrameFacts facts, Unavailable permission) {
        public Preparation { Objects.requireNonNull(facts); Objects.requireNonNull(permission); }
    }

    /** Migrates the real factory outcome; original .4 material never becomes legacy command permission. */
    public static Preparation prepare(SameFrameFacts facts, SourceEvidence source) {
        Objects.requireNonNull(facts); Objects.requireNonNull(source);
        var observation = facts.original().value();
        Reason reason;
        if (observation instanceof DevelopmentModels.Material) reason = Reason.NATIVE_MATERIAL_IS_NOT_ACTION_LEGALITY;
        else if (observation instanceof DevelopmentModels.Unavailable) reason = Reason.NATIVE_CANDIDATE_UNAVAILABLE;
        else if (observation.provenance().gameVersion().equals(DevelopmentStewardAction.VERSION))
            reason = Reason.LEGACY_COMMAND_ABI_UNCERTIFIED_AND_DRIVER_EXECUTOR_ABSENT;
        else reason = Reason.BUILD_HAS_NO_QUALIFIED_STEWARD_EXECUTOR;
        return new Preparation(facts, new Unavailable(reason, observation.provenance(), source));
    }

    /** Data reduction only. An actual Root observer must separately prove native custody and complete archives. */
    public sealed interface Result permits Pending, AppliedObserved, RejectedObserved, UnknownSubmission {
        default boolean replayAllowed() { return false; }
    }
    public record Pending(Ack ack, Optional<Receipt> originalUnverifiedReceipt) implements Result {
        public Pending { Objects.requireNonNull(ack); Objects.requireNonNull(originalUnverifiedReceipt); }
    }
    public record AppliedObserved(Receipt original) implements Result {
        public AppliedObserved { Objects.requireNonNull(original); StrictJson.require(original.postconditionVerified(), "verified original task receipt required"); }
    }
    public record RejectedObserved(Ack ack, Optional<Receipt> originalReceipt) implements Result {
        public RejectedObserved { Objects.requireNonNull(ack); Objects.requireNonNull(originalReceipt); StrictJson.require(ack.status() == AckStatus.REJECTED_BEFORE_SUBMIT, "actual pre-submit rejection required"); }
    }
    public record UnknownSubmission(Request request, Optional<RawJson> originalResponse) implements Result {
        public UnknownSubmission { Objects.requireNonNull(request); Objects.requireNonNull(originalResponse); }
    }

    public static Result reduce(Ack ack, Optional<Receipt> receipt) {
        Objects.requireNonNull(ack); Objects.requireNonNull(receipt);
        StrictJson.require(DevelopmentStewardAction.decodeAck(ack.original(), ack.request()).equals(ack),
                "steward ACK fields differ from their original producer body");
        receipt.ifPresent(original -> StrictJson.require(original.ack().equals(ack)
                && DevelopmentStewardAction.decodeReceipt(original.original(), ack).equals(original),
                "steward receipt lost its original ACK/body"));
        if (ack.status() == AckStatus.REJECTED_BEFORE_SUBMIT) return new RejectedObserved(ack, receipt);
        if (receipt.isPresent() && receipt.orElseThrow().postconditionVerified())
            return new AppliedObserved(receipt.orElseThrow());
        // A no-new-frame/progress/unverified native receipt remains UNKNOWN.
        // The exact receipt is retained; neither that result nor an ACK permits resubmission.
        return new Pending(ack, receipt);
    }

    private static void pin(ExactRef ref, long bytes, String sha) {
        Objects.requireNonNull(ref);
        StrictJson.require(ref.bytes() == bytes && ref.sha256().equals(sha), "development original source evidence changed");
    }
}
