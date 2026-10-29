package org.xar.ck3.control.wave2.development.constructioneconomy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;

import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

/** Strict application requests assembled by existing pure adapters. This class performs no native query. */
public final class ConstructionEconomyProjectionJson {
    public static final String PREPARE_SCHEMA = "xar.ck3.construction-economy-prepare-input.v1";
    public static final String COMPLETED_SCHEMA = "xar.ck3.construction-economy-completed-input.v1";
    public static final String QUOTE_SCHEMA = "xar.ck3.construction-economy-quote-input.v1";
    public static final String QUERY_OUTCOME_SCHEMA = "xar.ck3.construction-economy-query-outcome-input.v1";
    public static final String ENRICH_SCHEMA = "xar.ck3.construction-economy-enrich-input.v1";
    private static final Set<String> QUERY_FIELDS = Set.of("schema", "cash", "expected_revision", "receipt",
            "reserve_gold_raw", "existing_commitment_gold_raw", "horizon_months");
    private static final Set<String> ENRICH_FIELDS = Set.of("schema", "cash", "expected_revision", "receipt",
            "reserve_gold_raw", "existing_commitment_gold_raw", "horizon_months", "baseline");

    private ConstructionEconomyProjectionJson() { }

    public record PrepareRequest(Receipt receipt, CashPacket cash, BudgetPolicy policy) { }
    public record CompletedRequest(Receipt receipt, CashPacket cash, String exactBuild) { }
    public record QuoteRequest(ConstructionQuote quote, QuoteCashObservation observation,
            boolean wartime, boolean requireSameFrame) { }
    public record QueryRequest(CashPacket cash, BigInteger expectedRevision, Receipt receipt, BudgetPolicy policy) { }
    public record EnrichRequest(M5Plan baseline, QueryRequest query) { }

    public static PrepareRequest decodePrepare(byte[] raw) {
        ObjectNode root = request(raw, PREPARE_SCHEMA, Set.of("schema", "receipt", "cash", "reserve_gold_raw",
                "existing_commitment_gold_raw", "horizon_months"));
        Receipt receipt = ConstructionEconomyCodec.decodeReceiptProjection(root.get("receipt"));
        BigInteger cost = receipt.candidate().cost().orElseThrow(
                () -> new IllegalArgumentException("stock_gold_cost_raw is absent"));
        return new PrepareRequest(receipt, ConstructionEconomyCodec.decodeCashProjection(root.get("cash")), policy(root, cost));
    }

    public static CompletedRequest decodeCompleted(byte[] raw) {
        ObjectNode root = request(raw, COMPLETED_SCHEMA, Set.of("schema", "receipt", "cash", "exact_ck3_build"));
        return new CompletedRequest(ConstructionEconomyCodec.decodeReceiptProjection(root.get("receipt")),
                ConstructionEconomyCodec.decodeCashProjection(root.get("cash")), StrictJson.text(root.get("exact_ck3_build")));
    }

    public static QuoteRequest decodeQuote(byte[] raw) {
        ObjectNode root = request(raw, QUOTE_SCHEMA, Set.of("schema", "quote", "observation", "cash",
                "reserve_gold_raw", "wartime", "require_same_frame"));
        QuoteCashObservation observation = switch (StrictJson.text(root.get("observation"))) {
            case "missing" -> {
                requireAbsentCash(root);
                yield new NoCashObservation();
            }
            case "unavailable" -> {
                requireAbsentCash(root);
                yield new UnavailableCashObservation();
            }
            case "known" -> new ObservedCash(ConstructionEconomyCodec.decodeCashProjection(root.get("cash")),
                    nonnegative(root.get("reserve_gold_raw")));
            default -> throw new IllegalArgumentException("unknown construction quote cash observation");
        };
        return new QuoteRequest(ConstructionEconomyCodec.decodeQuoteProjection(root.get("quote")), observation,
                bool(root.get("wartime")), bool(root.get("require_same_frame")));
    }

    public static QueryRequest decodeQueryOutcome(byte[] raw) {
        return queryRequest(request(raw, QUERY_OUTCOME_SCHEMA, QUERY_FIELDS));
    }

    public static EnrichRequest decodeEnrich(byte[] raw) {
        ObjectNode root = request(raw, ENRICH_SCHEMA, ENRICH_FIELDS);
        return new EnrichRequest(ConstructionEconomyCodec.decodePlanProjection(root.get("baseline")), queryRequest(root));
    }

    public static byte[] prepare(byte[] raw) {
        PrepareRequest input = decodePrepare(raw);
        return ConstructionEconomyCodec.encodePrepared(ConstructionEconomyAdapters.prepare(input.receipt().candidate(),
                input.cash(), input.policy().reserve(), input.policy().commitments(), input.policy().horizonMonths()));
    }

    public static byte[] completed(byte[] raw) {
        CompletedRequest input = decodeCompleted(raw);
        return ConstructionEconomyCodec.encodeCompleted(ConstructionEconomyAdapters.completed(input.receipt(), input.cash(), input.exactBuild()));
    }

    public static byte[] quote(byte[] raw) {
        QuoteRequest input = decodeQuote(raw);
        return ConstructionEconomyCodec.encodeQuoteProjection(ConstructionEconomyAdapters.projectQuote(input.quote(),
                input.observation(), input.wartime(), input.requireSameFrame()));
    }

    public static byte[] queryOutcome(byte[] raw) {
        return ConstructionEconomyCodec.encodeQueryOutcome(query(decodeQueryOutcome(raw)));
    }

    public static byte[] enrich(byte[] raw) {
        EnrichRequest input = decodeEnrich(raw);
        return ConstructionEconomyCodec.encodeEnrichedPlan(ConstructionEconomyAdapters.enrichM5Plan(input.baseline(), query(input.query())));
    }

    private static QueryOutcome query(QueryRequest input) {
        // The calling driver already performed the single read. Its public revision is bound below;
        // snapshot_revision belongs to the separate native revision domain.
        return ConstructionEconomyAdapters.queryOutcome(ignoredRevision -> input.cash(), input.expectedRevision(), input.receipt(),
                input.policy().reserve(), input.policy().commitments(), input.policy().horizonMonths());
    }

    private static QueryRequest queryRequest(ObjectNode root) {
        CashPacket cash = ConstructionEconomyCodec.decodeCashProjection(root.get("cash"));
        BigInteger expected = StrictJson.integer(root.get("expected_revision"), BigInteger.ONE, StrictJson.UINT64_MAX);
        if (!cash.frame().queriedRevision().equals(Optional.of(expected))) {
            throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE,
                    "construction cash must bind the expected public query revision");
        }
        return new QueryRequest(cash, expected, ConstructionEconomyCodec.decodeReceiptProjection(root.get("receipt")),
                policy(root, BigInteger.ZERO));
    }

    private static BudgetPolicy policy(ObjectNode root, BigInteger cost) {
        return new BudgetPolicy(cost, nonnegative(root.get("reserve_gold_raw")),
                nonnegative(root.get("existing_commitment_gold_raw")),
                Math.toIntExact(StrictJson.integer(root.get("horizon_months"), 1, 24)));
    }

    private static BigInteger nonnegative(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() >= 0,
                "construction budget requires a nonnegative exact integer");
        return value.bigIntegerValue();
    }

    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "construction projection boolean required");
        return value.booleanValue();
    }

    private static void requireAbsentCash(ObjectNode root) {
        StrictJson.require(root.get("cash").isNull() && root.get("reserve_gold_raw").isNull(),
                "unobserved construction quote cash and reserve must be explicit null");
    }

    private static ObjectNode request(byte[] raw, String schema, Set<String> fields) {
        // Use the original codec parser and its token categories; no nested request is serialized before validation.
        ObjectNode root = StrictJson.object(ConstructionEconomyCodec.parseProjection(raw), fields);
        StrictJson.require(schema.equals(StrictJson.text(root.get("schema"))), "construction economy projection schema mismatch");
        return root;
    }
}
