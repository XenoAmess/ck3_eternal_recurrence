package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.warbudget.WarBudgetCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomy;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.BudgetRequest;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyProjectionJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.wave2.planning.warcashprovenance.WarFinancingCapabilityGap;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCash;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;

/**
 * M4 application composition of the existing development and emergency-budget policies.
 *
 * <p>Original payload bytes reach the responsible codec before reencoding. Source metadata
 * describes the caller's evidence; this pure domain does not read it, grant native source
 * qualification, submit an action, or update a ledger. M4's accepted material window is
 * not reevaluated by these economic projections.</p>
 */
public final class M4Research implements G2Domain {
    public static final int MAXIMUM_PAYLOAD_BYTES = OrdinaryWartimeConstructionCodec.MAX_BYTES;

    @Override public Milestone milestone() { return Milestone.M4; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request, "request");
        StrictJson.require(request.milestone() == milestone(), "M4 request milestone required");
        StrictJson.require(request.payload().isObject(), "M4 original domain object required");
        byte[] original = request.payload().bytes();
        JsonNode envelope = StrictJson.parse(original, MAXIMUM_PAYLOAD_BYTES);
        String schema = StrictJson.text(envelope.get("schema"));
        byte[] result = switch (schema) {
            case OrdinaryWartimeConstructionCodec.SCHEMA -> OrdinaryWartimeConstructionCodec.evaluate(original);
            case WartimeConstructionCodec.SCHEMA -> WartimeConstructionCodec.encode(
                    WartimeConstructionCash.observe(WartimeConstructionCodec.decode(original)));
            case "xar.ck3.construction-economy-input.v1" -> ConstructionEconomyCodec.encodeOutcome(
                    ConstructionEconomy.classify(ConstructionEconomyCodec.decodeOutcomeRequest(original)));
            case "xar.ck3.construction-monthly-budget-input.v1" -> budget(original);
            case ConstructionEconomyProjectionJson.PREPARE_SCHEMA -> ConstructionEconomyProjectionJson.prepare(original);
            case ConstructionEconomyProjectionJson.COMPLETED_SCHEMA -> ConstructionEconomyProjectionJson.completed(original);
            case ConstructionEconomyProjectionJson.QUOTE_SCHEMA -> ConstructionEconomyProjectionJson.quote(original);
            case ConstructionEconomyProjectionJson.QUERY_OUTCOME_SCHEMA -> ConstructionEconomyProjectionJson.queryOutcome(original);
            case ConstructionEconomyProjectionJson.ENRICH_SCHEMA -> ConstructionEconomyProjectionJson.enrich(original);
            case WarBudgetCodec.SCHEMA -> WarBudgetCodec.evaluate(original);
            case FinancingGapCodec.REQUEST_SCHEMA -> FinancingGapCodec.encode(
                    WarFinancingCapabilityGap.observe(FinancingGapCodec.decode(original)));
            // Native provider -> HolyLoanCodec.project is the producer. Its complete typed
            // observation remains zero funding credit and never becomes a loan submission.
            case HolyLoanCodec.SCHEMA -> HolyLoanCodec.encode(HolyLoanCodec.decodeObservation(original));
            default -> throw new IllegalArgumentException("unsupported M4 payload schema: " + schema);
        };
        return new G2Response(request.requestId(), milestone(), request.source(),
                ProjectionJson.value(result, MAXIMUM_PAYLOAD_BYTES));
    }

    private static byte[] budget(byte[] original) {
        BudgetRequest input = ConstructionEconomyCodec.decodeBudgetRequest(original);
        return ConstructionEconomyCodec.encodeBudget(ConstructionEconomy.projectBudget(input.cash(), input.policy()));
    }
}

