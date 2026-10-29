package org.xar.ck3.control.wave3.governance.marriagenotice;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;
import org.xar.ck3.control.wave2.governance.betrothal.MarriageProjectionJson;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffCodec;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueCodec;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel;
import org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValuePolicy;
import org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingConsumerPort;

/** Actual shared-host ports; the original callback, process lookup and writer remain at their consumers. */
public final class MarriageWave3ProjectionCatalog implements ProjectionPortCatalog {
    public MarriageWave3ProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new ReviewPort()), RegisteredProjection.of(new ContinuePort()),
                RegisteredProjection.of(new ValuePort()), RegisteredProjection.of(new PendingPort()));
    }
    public record ReviewApplication(boolean applied, MarriageNoticeModel.ReviewResult evidence) {
        public ReviewApplication { Objects.requireNonNull(evidence); }
    }
    public static final class ReviewPort implements ProjectionPort<MarriageNoticeModel.ReviewInput, ReviewApplication> {
        @Override public int inputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return BetrothalCodec.MAX_BYTES + 1024; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.MARRIAGE_NOTICE_REVIEW; }
        @Override public MarriageNoticeModel.ReviewInput decode(byte[] rawPayload) { return MarriageNoticeCodec.decodeReview(rawPayload); }
        @Override public ReviewApplication project(MarriageNoticeModel.ReviewInput input) {
            MarriageNoticeModel.ReviewResult result = MarriageNoticePolicy.reviewSource(input);
            return new ReviewApplication(result instanceof MarriageNoticeModel.ReviewedEvidence, result);
        }
        @Override public byte[] encode(ReviewApplication result) {
            ObjectNode root = StrictJson.object(); root.put("applied", result.applied());
            root.set("evidence", MarriageProjectionJson.value(MarriageNoticeCodec.encodeReview(result.evidence()), BetrothalCodec.MAX_BYTES));
            return MarriageProjectionJson.bytes(root, BetrothalCodec.MAX_BYTES + 1024);
        }
    }
    public static final class ValuePort implements ProjectionPort<BetrothalValueModel.EvaluationInput, BetrothalValueModel.Choice> {
        @Override public int inputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.BETROTHAL_VALUE_EVALUATE; }
        @Override public BetrothalValueModel.EvaluationInput decode(byte[] rawPayload) { return BetrothalValueCodec.decode(rawPayload); }
        @Override public BetrothalValueModel.Choice project(BetrothalValueModel.EvaluationInput input) { return BetrothalValuePolicy.evaluate(input); }
        @Override public byte[] encode(BetrothalValueModel.Choice result) { return BetrothalValueCodec.encodeChoice(result); }
    }

    public sealed interface NoticeCall permits ClassifyNotice, PrepareNotice, CompleteNotice { }
    public record ClassifyNotice(MarriageNoticeModel.Plan plan) implements NoticeCall { }
    public record PrepareNotice(MarriageNoticeModel.ContinueInput input) implements NoticeCall { }
    public record CompleteNotice(MarriageNoticeModel.ContinueInput input, MarriageNoticeModel.Plan ordinaryPlan) implements NoticeCall { }
    public sealed interface NoticeResult permits ClassifiedNotice, UnchangedNotice, NoticeProjection, FinishedNotice { }
    public record ClassifiedNotice(boolean blocked) implements NoticeResult { }
    public record UnchangedNotice(MarriageNoticeModel.Plan plan) implements NoticeResult { }
    public record NoticeProjection(MarriageNoticeModel.OrdinaryProjection projection) implements NoticeResult { }
    public record FinishedNotice(MarriageNoticeModel.ContinuationResult result) implements NoticeResult { }

    /** Pure prepare -> original ordinary callback -> pure completion, with the same one policy guard. */
    public static final class ContinuePort implements ProjectionPort<NoticeCall, NoticeResult> {
        public static final String SCHEMA = "xar.ck3.marriage-notice-operation.v1";
        public static final int MAXIMUM_BYTES = 2 * BetrothalCodec.MAX_BYTES + 1024;
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return BetrothalCodec.MAX_BYTES + 1024; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.MARRIAGE_NOTICE_CONTINUE; }
        @Override public NoticeCall decode(byte[] rawPayload) {
            ObjectNode root = MarriageProjectionJson.object(rawPayload, MAXIMUM_BYTES,
                    fields(MarriageProjectionJson.value(rawPayload, MAXIMUM_BYTES).path("stage").textValue()));
            StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "notice operation schema differs");
            String stage = StrictJson.text(root.get("stage"));
            if ("classify".equals(stage)) {
                return new ClassifyNotice(MarriageNoticeCodec.decodePlan(MarriageProjectionJson.bytes(root.get("plan"), BetrothalCodec.MAX_BYTES)));
            }
            MarriageNoticeModel.ContinueInput input = MarriageNoticeCodec.decodeContinue(
                    MarriageProjectionJson.bytes(root.get("input"), BetrothalCodec.MAX_BYTES));
            return "prepare".equals(stage) ? new PrepareNotice(input) : new CompleteNotice(input,
                    MarriageNoticeCodec.decodePlan(MarriageProjectionJson.bytes(root.get("ordinary_plan"), BetrothalCodec.MAX_BYTES)));
        }
        private static Set<String> fields(String stage) {
            return switch (stage == null ? "" : stage) {
                case "classify" -> Set.of("schema", "stage", "plan");
                case "prepare" -> Set.of("schema", "stage", "input");
                case "complete" -> Set.of("schema", "stage", "input", "ordinary_plan");
                default -> throw new IllegalArgumentException("unknown notice operation stage");
            };
        }
        @Override public NoticeResult project(NoticeCall input) {
            return switch (input) {
                case ClassifyNotice classify -> new ClassifiedNotice(MarriageNoticePolicy.isBlockedReply(classify.plan()));
                case PrepareNotice prepare -> {
                    Optional<MarriageNoticeModel.OrdinaryProjection> projection = MarriageNoticePolicy.prepareOrdinaryProjection(prepare.input());
                    yield projection.<NoticeResult>map(NoticeProjection::new).orElseGet(() -> new UnchangedNotice(prepare.input().blockedPlan()));
                }
                case CompleteNotice complete -> new FinishedNotice(MarriageNoticePolicy.continueOrdinary(
                        complete.input(), projection -> complete.ordinaryPlan()));
            };
        }
        @Override public byte[] encode(NoticeResult result) {
            ObjectNode root = StrictJson.object();
            switch (result) {
                case ClassifiedNotice classified -> { root.put("status", "classification"); root.put("blocked", classified.blocked()); }
                case UnchangedNotice unchanged -> {
                    root.put("status", "unchanged"); root.set("plan", MarriageProjectionJson.value(
                            BetrothalCodec.encodeEvidence(unchanged.plan().original()), BetrothalCodec.MAX_BYTES));
                }
                case NoticeProjection projection -> {
                    root.put("status", "projection"); root.set("projection", MarriageProjectionJson.value(
                            MarriageNoticeCodec.encodeProjection(projection.projection()), BetrothalCodec.MAX_BYTES));
                }
                case FinishedNotice finished -> {
                    root.put("status", finished.result() instanceof MarriageNoticeModel.ContinuedPlan ? "continued" : "unchanged");
                    root.set("plan", MarriageProjectionJson.value(MarriageNoticeCodec.encodeContinuation(finished.result()), BetrothalCodec.MAX_BYTES));
                }
            }
            return MarriageProjectionJson.bytes(root, outputMaximumBytes());
        }
    }

    public sealed interface PendingCall permits PreparePending, CompletePending { }
    public record PreparePending(MarriagePendingConsumerPort.PreparedInput input) implements PendingCall { }
    public record CompletePending(MarriagePendingConsumerPort.PreparedInput input) implements PendingCall {
        public CompletePending {
            Objects.requireNonNull(input);
            StrictJson.require(!input.needsCurrentProcess(), "same-episode pending needs actual current bridge identity");
        }
    }
    public sealed interface PendingResult permits BridgeIdentityRequired, AppliedPending { }
    public record BridgeIdentityRequired() implements PendingResult { }
    public record AppliedPending(MarriagePendingConsumerPort.AppliedPlan result) implements PendingResult { }

    /** Preparation preserves the original rule that a foreign episode never queries process identity. */
    public static final class PendingPort implements ProjectionPort<PendingCall, PendingResult> {
        public static final String SCHEMA = "xar.ck3.pending-marriage-operation.v1";
        public static final int MAXIMUM_BYTES = MarriageHandoffCodec.MAXIMUM_BYTES + 1024;
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.PENDING_MARRIAGE_PLAN; }
        @Override public PendingCall decode(byte[] rawPayload) {
            ObjectNode root = MarriageProjectionJson.object(rawPayload, MAXIMUM_BYTES, Set.of("schema", "stage", "request"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "pending marriage operation schema differs");
            MarriagePendingConsumerPort.PreparedInput input = MarriagePendingConsumerPort.decodePrepared(
                    MarriageProjectionJson.bytes(root.get("request"), MarriageHandoffCodec.MAXIMUM_BYTES));
            return switch (StrictJson.text(root.get("stage"))) {
                case "prepare" -> new PreparePending(input);
                case "complete" -> new CompletePending(input);
                default -> throw new IllegalArgumentException("unknown pending marriage operation stage");
            };
        }
        @Override public PendingResult project(PendingCall input) {
            return switch (input) {
                case PreparePending prepare -> prepare.input().needsCurrentProcess() ? new BridgeIdentityRequired()
                        : new AppliedPending(MarriagePendingConsumerPort.project(prepare.input()));
                case CompletePending complete -> new AppliedPending(MarriagePendingConsumerPort.project(complete.input()));
            };
        }
        @Override public byte[] encode(PendingResult result) {
            ObjectNode root = StrictJson.object();
            switch (result) {
                case BridgeIdentityRequired ignored -> root.put("status", "bridge_identity_required");
                case AppliedPending applied -> {
                    root = (ObjectNode) MarriageProjectionJson.value(MarriagePendingConsumerPort.encodeApplied(applied.result()), MarriageHandoffCodec.MAXIMUM_BYTES);
                    root.put("status", "applied");
                }
            }
            return MarriageProjectionJson.bytes(root, MAXIMUM_BYTES);
        }
    }
}
