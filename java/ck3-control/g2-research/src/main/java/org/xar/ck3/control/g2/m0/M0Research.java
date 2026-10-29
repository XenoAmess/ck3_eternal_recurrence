package org.xar.ck3.control.g2.m0;

import java.util.Objects;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;

/** One shared G2 entry; original source-normalized M0 inputs carry no action or ledger authority. */
public final class M0Research implements G2Domain {
    @Override public Milestone milestone() { return Milestone.M0; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request);
        if (request.milestone() != milestone()) { throw new IllegalArgumentException("M0 request milestone differs"); }
        byte[] raw = request.payload().bytes();
        JsonNode root = StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES);
        String operation = root.has("operation") ? StrictJson.text(root.get("operation")) : "";
        byte[] evaluated = switch (operation) {
            case RefusedDemandSettlementExposure.OPERATION -> RefusedDemandSettlementExposure.execute(raw);
            case "evaluate-immediate-exit" -> RaiktorImmediateInputCodec.executeOperation(raw);
            case "project-terminal-control" -> RaiktorTerminalInputProjection.executeOperation(raw);
            case "project-terminal-control-from-snapshot" -> RaiktorTerminalInputProjection.executeSnapshotOperation(raw);
            case RaiktorRecommendationComposer.OPERATION -> RaiktorRecommendationComposer.executeOperation(raw);
            case RaiktorUtilityComparisonTrace.OPERATION -> RaiktorUtilityComparisonTrace.executeOperation(raw);
            case "normalize-white-peace-observation", "normalize-surrender-session" ->
                RaiktorExitObservationCodec.execute(raw);
            case "" -> RaiktorRecommendationInputCodec.execute(raw);
            default -> {
                if (!RaiktorRawOperations.supports(operation)) throw new IllegalArgumentException("unsupported M0 operation");
                yield RaiktorRawOperations.execute(raw);
            }
        };
        return new G2Response(request.requestId(), request.milestone(), request.source(),
                ProjectionJson.value(evaluated, ProjectionJson.MAX_BYTES));
    }
}
