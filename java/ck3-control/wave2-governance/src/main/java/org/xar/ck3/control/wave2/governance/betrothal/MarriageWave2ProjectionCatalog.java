package org.xar.ck3.control.wave2.governance.betrothal;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageEpisodeHandoff;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffCodec;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffConsumerPort;
import org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel;

/** Typed pure operations registered into the one projection host; owns no writer or transport. */
public final class MarriageWave2ProjectionCatalog implements ProjectionPortCatalog {
    public MarriageWave2ProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new BuildPort()), RegisteredProjection.of(new AdaptPort()),
                RegisteredProjection.of(new EpisodeHandoffPort()));
    }

    public static final class BuildPort implements ProjectionPort<BetrothalModel.BuildInput, BetrothalModel.ResourceProposal> {
        @Override public int inputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.BETROTHAL_BUILD; }
        @Override public BetrothalModel.BuildInput decode(byte[] rawPayload) { return BetrothalCodec.decodeBuild(rawPayload); }
        @Override public BetrothalModel.ResourceProposal project(BetrothalModel.BuildInput input) { return BetrothalProposals.build(input); }
        @Override public byte[] encode(BetrothalModel.ResourceProposal result) { return BetrothalCodec.encodeResource(result); }
    }
    public static final class AdaptPort implements ProjectionPort<BetrothalModel.AdaptInput, BetrothalModel.Opportunity> {
        @Override public int inputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return BetrothalCodec.MAX_BYTES; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.BETROTHAL_ADAPT; }
        @Override public BetrothalModel.AdaptInput decode(byte[] rawPayload) { return BetrothalCodec.decodeAdapt(rawPayload); }
        @Override public BetrothalModel.Opportunity project(BetrothalModel.AdaptInput input) { return BetrothalProposals.adapt(input); }
        @Override public byte[] encode(BetrothalModel.Opportunity result) { return BetrothalCodec.encodeOpportunity(result); }
    }

    public sealed interface HandoffCall permits PrepareHandoff, RevalidateHandoff { }
    public record PrepareHandoff(MarriageHandoffModel.Request request) implements HandoffCall { }
    public record RevalidateHandoff(MarriageHandoffModel.Request request, MarriageHandoffModel.Ledger currentLedger) implements HandoffCall { }
    public sealed interface HandoffResult permits PreparedHandoff, RevalidatedHandoff { }
    public record PreparedHandoff(MarriageHandoffModel.Reduction reduction) implements HandoffResult { }
    public record RevalidatedHandoff(MarriageHandoffModel.Ledger ledger) implements HandoffResult { }

    /** A second call recomputes the real reducer under the caller's original writer lock. */
    public static final class EpisodeHandoffPort implements ProjectionPort<HandoffCall, HandoffResult> {
        public static final String SCHEMA = "xar.ck3.episode-handoff-operation.v1";
        public static final int MAXIMUM_BYTES = 2 * MarriageHandoffCodec.MAXIMUM_BYTES + 1024;
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MarriageHandoffCodec.MAXIMUM_BYTES + 1024; }
        @Override public ProjectionOperation operation() { return ProjectionOperation.EPISODE_HANDOFF; }
        @Override public HandoffCall decode(byte[] rawPayload) {
            ObjectNode root = MarriageProjectionJson.object(rawPayload, MAXIMUM_BYTES,
                    fields(MarriageProjectionJson.value(rawPayload, MAXIMUM_BYTES).path("stage").textValue()));
            StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "episode handoff operation schema differs");
            MarriageHandoffModel.Request request = MarriageHandoffCodec.decodeRequest(
                    MarriageProjectionJson.bytes(root.get("request"), MarriageHandoffCodec.MAXIMUM_BYTES));
            return switch (StrictJson.text(root.get("stage"))) {
                case "prepare" -> new PrepareHandoff(request);
                case "revalidate" -> new RevalidateHandoff(request, MarriageHandoffCodec.decodeLedger(
                        MarriageProjectionJson.bytes(root.get("current_ledger"), MarriageHandoffCodec.MAXIMUM_BYTES)));
                default -> throw new IllegalArgumentException("unknown episode handoff stage");
            };
        }
        private static Set<String> fields(String stage) {
            return switch (stage == null ? "" : stage) {
                case "prepare" -> Set.of("schema", "stage", "request");
                case "revalidate" -> Set.of("schema", "stage", "request", "current_ledger");
                default -> throw new IllegalArgumentException("unknown episode handoff stage");
            };
        }
        @Override public HandoffResult project(HandoffCall input) {
            return switch (input) {
                case PrepareHandoff prepare -> new PreparedHandoff(MarriageEpisodeHandoff.reduce(prepare.request()));
                case RevalidateHandoff revalidate -> {
                    MarriageHandoffModel.Reduction reduction = MarriageEpisodeHandoff.reduce(revalidate.request());
                    if (!(reduction instanceof MarriageHandoffModel.Archived)) { throw new ProjectionDomainRejection("only an original archived proposal can be revalidated"); }
                    yield new RevalidatedHandoff(MarriageHandoffConsumerPort.revalidateOriginalWriterUpdate(
                            (MarriageHandoffModel.Archived) reduction, MarriageHandoffCodec.encodeLedger(revalidate.currentLedger())));
                }
            };
        }
        @Override public byte[] encode(HandoffResult result) {
            ObjectNode root = StrictJson.object();
            switch (result) {
                case PreparedHandoff prepared -> {
                    root.put("stage", "prepared"); root.set("result", MarriageProjectionJson.value(
                            MarriageHandoffCodec.encodeResult(prepared.reduction()), MarriageHandoffCodec.MAXIMUM_BYTES));
                }
                case RevalidatedHandoff revalidated -> {
                    root.put("stage", "revalidated"); root.set("ledger", MarriageProjectionJson.value(
                            MarriageHandoffCodec.encodeLedger(revalidated.ledger()), MarriageHandoffCodec.MAXIMUM_BYTES));
                }
            }
            return MarriageProjectionJson.bytes(root, outputMaximumBytes());
        }
    }
}
