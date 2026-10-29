package org.xar.ck3.control.wave2.development;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Arrays;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomy;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyCodec;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.BudgetRequest;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyProjectionJson;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionIncomeJson;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncomeJson;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentJson;
import org.xar.ck3.control.wave2.development.constructionmode3.ConstructionMode3Codec;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReadbackJson;
import org.xar.ck3.control.wave2.development.constructionscene.ConstructionSceneCodec;
import org.xar.ck3.control.wave2.development.constructionvalue.ConstructionValueCodec;

/** Pure application dispatch. Supplied observations grant no native execution or continuation qualification. */
public final class ConstructionProjectionDispatcher {
    public static final int MAX_REQUEST_BYTES = StrictJson.EXPLICIT_MAX_BYTES;

    private ConstructionProjectionDispatcher() { }

    public enum Operation {
        INTENT("intent", ConstructionIntentJson.REQUEST_SCHEMA, ConstructionIntentJson.MAX_INPUT_BYTES),
        READBACK("readback", ConstructionReadbackJson.SCHEMA, ConstructionReadbackJson.MAX_BYTES),
        INCOME("income", ConstructionIncomeJson.SCHEMA, ConstructionIncomeJson.MAX_BYTES),
        PROVINCE_INCOME("province-income", ConstructionProvinceIncomeJson.SCHEMA, StrictJson.INPUT_MAX_BYTES),
        SCENE("scene", ConstructionSceneCodec.SCENE_SCHEMA, ConstructionSceneCodec.MAX_BYTES),
        CLAN_CASH("clan-cash", ConstructionSceneCodec.CASH_SCHEMA, ConstructionSceneCodec.MAX_BYTES),
        VALUE_LOOKUP("value-lookup", ConstructionValueCodec.LOOKUP_SCHEMA, ConstructionValueCodec.MAX_BYTES),
        VALUE_SELECT("value-select", ConstructionValueCodec.SELECT_SCHEMA, ConstructionValueCodec.MAX_BYTES),
        VALUE_CONSUME("value-consume", ConstructionValueCodec.SELECT_SCHEMA, ConstructionValueCodec.MAX_BYTES),
        MODE3("mode3", ConstructionMode3Codec.REQUEST_SCHEMA, ConstructionMode3Codec.MAX_BYTES),
        ECONOMY_OUTCOME("economy-outcome", "xar.ck3.construction-economy-input.v1", ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_BUDGET("economy-budget", "xar.ck3.construction-monthly-budget-input.v1", ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_PREPARE("economy-prepare", ConstructionEconomyProjectionJson.PREPARE_SCHEMA, ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_COMPLETED("economy-completed", ConstructionEconomyProjectionJson.COMPLETED_SCHEMA, ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_QUOTE("economy-quote", ConstructionEconomyProjectionJson.QUOTE_SCHEMA, ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_QUERY_OUTCOME("economy-query-outcome", ConstructionEconomyProjectionJson.QUERY_OUTCOME_SCHEMA, ConstructionEconomyCodec.MAX_BYTES),
        ECONOMY_ENRICH("economy-enrich", ConstructionEconomyProjectionJson.ENRICH_SCHEMA, ConstructionEconomyCodec.MAX_BYTES);

        private final String wire;
        private final String requestSchema;
        private final int maximumBytes;

        Operation(String wire, String requestSchema, int maximumBytes) {
            this.wire = wire;
            this.requestSchema = requestSchema;
            this.maximumBytes = maximumBytes;
        }

        public String wire() { return wire; }
        public String requestSchema() { return requestSchema; }
        public int maximumRequestBytes() { return maximumBytes; }
        public int maximumResponseBytes() { return maximumBytes; }

        public static Operation fromWire(String wire) {
            return Arrays.stream(values()).filter(operation -> operation.wire.equals(wire)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown construction projection operation"));
        }
    }

    public record OperationContract(String operation, String request_schema, int maximum_request_bytes,
            int maximum_response_bytes) { }

    public static List<OperationContract> operationContracts() {
        return Arrays.stream(Operation.values()).map(operation -> new OperationContract(operation.wire(),
                operation.requestSchema(), operation.maximumRequestBytes(), operation.maximumResponseBytes())).toList();
    }

    public static byte[] project(String operation, byte[] requestUtf8) {
        return project(Operation.fromWire(operation), requestUtf8);
    }

    public static byte[] project(Operation operation, byte[] requestUtf8) {
        StrictJson.require(operation != null, "construction projection operation required");
        JsonNode request = StrictJson.parse(requestUtf8, operation.maximumRequestBytes());
        StrictJson.require(request.isObject(), "construction projection object required");
        StrictJson.require(operation.requestSchema().equals(StrictJson.text(request.get("schema"))),
                "construction projection schema does not match operation");
        // Route the original bytes. Reencoding a parsed 1.0 can erase the token category needed by a leaf guard.
        byte[] response = switch (operation) {
            case INTENT -> ConstructionIntentJson.project(requestUtf8);
            case READBACK -> ConstructionReadbackJson.project(requestUtf8);
            case INCOME -> ConstructionIncomeJson.project(requestUtf8);
            case PROVINCE_INCOME -> ConstructionProvinceIncomeJson.project(requestUtf8);
            case SCENE -> ConstructionSceneCodec.scope(requestUtf8);
            case CLAN_CASH -> ConstructionSceneCodec.clanCashReason(requestUtf8);
            case VALUE_LOOKUP -> ConstructionValueCodec.lookup(requestUtf8);
            case VALUE_SELECT -> ConstructionValueCodec.select(requestUtf8);
            case VALUE_CONSUME -> ConstructionValueCodec.consumeSelection(requestUtf8);
            case MODE3 -> ConstructionMode3Codec.evaluate(requestUtf8);
            case ECONOMY_OUTCOME -> ConstructionEconomyCodec.encodeOutcome(ConstructionEconomy.classify(
                    ConstructionEconomyCodec.decodeOutcomeRequest(requestUtf8)));
            case ECONOMY_BUDGET -> {
                BudgetRequest budget = ConstructionEconomyCodec.decodeBudgetRequest(requestUtf8);
                yield ConstructionEconomyCodec.encodeBudget(ConstructionEconomy.projectBudget(budget.cash(), budget.policy()));
            }
            case ECONOMY_PREPARE -> ConstructionEconomyProjectionJson.prepare(requestUtf8);
            case ECONOMY_COMPLETED -> ConstructionEconomyProjectionJson.completed(requestUtf8);
            case ECONOMY_QUOTE -> ConstructionEconomyProjectionJson.quote(requestUtf8);
            case ECONOMY_QUERY_OUTCOME -> ConstructionEconomyProjectionJson.queryOutcome(requestUtf8);
            case ECONOMY_ENRICH -> ConstructionEconomyProjectionJson.enrich(requestUtf8);
        };
        StrictJson.require(response != null && response.length > 0 && response.length <= operation.maximumResponseBytes(),
                "construction projection response exceeds operation budget");
        return response;
    }
}
