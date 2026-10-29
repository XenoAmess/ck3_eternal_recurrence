package org.xar.ck3.control.wave2.development.constructioneconomy;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

/** Retained original-producer cash enters the shared decoder and real construction consumers. No native/live credit. */
final class ConstructionCashMonthlySourceTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void retainedProducerBudgetKeepsNetAndReplacesCurrentMilitaryOnce() throws IOException {
        ObjectNode request = budgetRequest("negative_net_raised_once");
        ObjectNode cash = object(request.get("cash"));
        RawCashCodec.validateMonthlySourceContract(bytes(cash));
        BudgetRequest decoded = ConstructionEconomyCodec.decodeBudgetRequest(bytes(request));
        Budget budget = ConstructionEconomy.projectBudget(decoded.cash(), decoded.policy());
        assertEquals(BigInteger.valueOf(-200000), budget.current().netRate().orElseThrow());
        assertEquals(BigInteger.valueOf(-500000), budget.allRaised().netRate().orElseThrow());
        JsonNode encoded = JSON.readTree(ConstructionEconomyCodec.encodeBudget(budget));
        assertEquals(cash, encoded.get("source_cash_resources"));
        assertFalse(encoded.get("future_war_cost_upper_ready").booleanValue());
        assertFalse(encoded.get("formal_action_ready").booleanValue());
        BudgetRequest restored = ConstructionEconomyCodec.decodeBudgetRequest(bytes(request));
        assertEquals(encoded, JSON.readTree(ConstructionEconomyCodec.encodeBudget(
                ConstructionEconomy.projectBudget(restored.cash(), restored.policy()))));
    }

    @Test void directBudgetCannotUseAnotherActorWarUnitOrResourceVector() throws IOException {
        for (String kind : List.of("current", "all_raised")) {
            for (String field : List.of("owner_character_id", "resource_id", "war_ids", "raw_scale",
                    "time_basis", "source_scope", "future_war_cost_upper_ready", "treasury_raw")) {
                ObjectNode request = budgetRequest("negative_net_raised_once");
                ObjectNode row = object(object(object(request.get("cash")).get("military_expenses")).get(kind));
                switch (field) {
                    case "owner_character_id" -> row.put(field, 29830);
                    case "resource_id" -> row.put(field, "29830");
                    case "war_ids" -> row.putArray(field);
                    case "raw_scale" -> row.put(field, 1);
                    case "time_basis" -> row.put(field, "day");
                    case "source_scope" -> row.put(field, "per_war_military");
                    case "future_war_cost_upper_ready" -> row.put(field, true);
                    case "treasury_raw" -> row.put(field, 0);
                    default -> throw new IllegalStateException("unexpected mutation");
                }
                assertRejectedAtEveryCashEntry(object(request.get("cash")), request, kind + ":" + field);
            }
        }
    }

    @Test void missingNullBooleanAndFloatNeverBecomeTheOwnerOrScale() throws IOException {
        for (String field : List.of("owner_character_id", "raw_scale")) {
            for (String token : List.of("missing", "null", "true", "29829.0", "\"29829\"")) {
                ObjectNode request = budgetRequest("negative_net_raised_once");
                ObjectNode row = object(object(object(request.get("cash")).get("military_expenses")).get("current"));
                if (token.equals("missing")) row.remove(field); else row.set(field, JSON.readTree(token));
                assertRejectedAtEveryCashEntry(object(request.get("cash")), request, field + ":" + token);
            }
        }
    }

    @Test void unavailableAllRaisedRemainsUnknownWhileCurrentBudgetStaysUsable() throws IOException {
        ObjectNode request = budgetRequest("independent_current_when_raised_unknown");
        RawCashCodec.validateMonthlySourceContract(bytes(request.get("cash")));
        BudgetRequest decoded = ConstructionEconomyCodec.decodeBudgetRequest(bytes(request));
        Budget budget = ConstructionEconomy.projectBudget(decoded.cash(), decoded.policy());
        assertTrue(budget.current().ready());
        assertFalse(budget.allRaised().ready());
        assertTrue(budget.allRaised().netRate().isEmpty());
        assertTrue(budget.allRaised().missingInputs().containsKey(MissingInput.ALL_RAISED_MILITARY));
        JsonNode encoded = JSON.readTree(ConstructionEconomyCodec.encodeBudget(budget));
        assertTrue(encoded.path("scenarios").path("all_raised").path("net_monthly_gold_raw").isNull());
        assertFalse(encoded.get("future_war_cost_upper_ready").booleanValue());
    }

    @Test void originalCompletionCashAndPersistedReceiptUseTheSameSourceContract() throws IOException {
        ObjectNode entry = original("cash_net_and_wallet_verified_debit");
        ObjectNode request = object(entry.get("request")).deepCopy();
        request.put("schema", "xar.ck3.construction-economy-input.v1");
        var decoded = ConstructionEconomyCodec.decodeOutcomeRequest(bytes(request));
        JsonNode outcome = JSON.readTree(ConstructionEconomyCodec.encodeOutcome(ConstructionEconomy.classify(decoded)));
        assertEquals(entry.get("expected"), outcome);
        assertFalse(outcome.path("readiness").path("building_attribution_ready").booleanValue());
        assertFalse(outcome.path("readiness").path("net_benefit_ready").booleanValue());
        ObjectNode wrong = object(request.get("post_cash_v2")).deepCopy();
        object(object(wrong.get("military_expenses")).get("current")).put("owner_character_id", 29830);
        request.set("post_cash_v2", wrong);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeOutcomeRequest(bytes(request)));
        ObjectNode persisted = object(request.get("receipt")).deepCopy(); persisted.set("post_cash_v2", wrong);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt(bytes(persisted)));
    }

    @Test void publicPrepareCompletedQueryQuoteAndEnrichCannotBypassTheSharedOwner() throws IOException {
        ObjectNode prepare = object(original("formal_quote_prepare").get("request")).deepCopy();
        prepare.put("schema", ConstructionEconomyProjectionJson.PREPARE_SCHEMA); changeOwner(prepare);
        assertOwnerRejection(assertThrows(IllegalArgumentException.class,
                () -> ConstructionEconomyProjectionJson.prepare(bytes(prepare))));
        ObjectNode completed = object(original("material_completion_attach").get("request")).deepCopy();
        completed.put("schema", ConstructionEconomyProjectionJson.COMPLETED_SCHEMA); changeOwner(completed);
        assertOwnerRejection(assertThrows(IllegalArgumentException.class,
                () -> ConstructionEconomyProjectionJson.completed(bytes(completed))));
        ObjectNode query = object(original("single_read_current_zero_new_spend").get("request")).deepCopy();
        query.put("schema", ConstructionEconomyProjectionJson.QUERY_OUTCOME_SCHEMA); changeOwner(query);
        assertOwnerRejection(assertThrows(IllegalArgumentException.class,
                () -> ConstructionEconomyProjectionJson.queryOutcome(bytes(query))));
        ObjectNode enrich = query.deepCopy(); enrich.put("schema", ConstructionEconomyProjectionJson.ENRICH_SCHEMA);
        enrich.putObject("baseline");
        assertOwnerRejection(assertThrows(IllegalArgumentException.class,
                () -> ConstructionEconomyProjectionJson.enrich(bytes(enrich))));
        ObjectNode quote = JSON.createObjectNode(); quote.put("schema", ConstructionEconomyProjectionJson.QUOTE_SCHEMA);
        quote.set("quote", prepare.get("receipt")); quote.put("observation", "known"); quote.set("cash", prepare.get("cash"));
        quote.set("reserve_gold_raw", prepare.get("reserve_gold_raw")); quote.put("wartime", true); quote.put("require_same_frame", true);
        assertOwnerRejection(assertThrows(IllegalArgumentException.class,
                () -> ConstructionEconomyProjectionJson.quote(bytes(quote))));
    }

    private static void changeOwner(ObjectNode request) {
        object(object(object(request.get("cash")).get("military_expenses")).get("current")).put("owner_character_id", 29830);
    }
    private static void assertOwnerRejection(IllegalArgumentException rejected) {
        assertEquals("military expense lost actor-global semantics", rejected.getMessage());
    }

    private static void assertRejectedAtEveryCashEntry(ObjectNode cash, ObjectNode budget, String mutation) {
        byte[] original = bytes(cash);
        assertThrows(IllegalArgumentException.class, () -> RawCashCodec.validateMonthlySourceContract(original), mutation);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeCash(original), mutation);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeBudgetRequest(bytes(budget)), mutation);
        ObjectNode receipt = JSON.createObjectNode(); receipt.set("post_cash_v2", cash);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt(bytes(receipt)), mutation);
    }

    private static ObjectNode budgetRequest(String name) throws IOException {
        ObjectNode request = object(original(name).get("request")).deepCopy();
        request.put("schema", "xar.ck3.construction-monthly-budget-input.v1"); return request;
    }
    private static ObjectNode original(String name) throws IOException {
        try (InputStream compressed = ConstructionCashMonthlySourceTest.class.getResourceAsStream("original-producer-golden.json.gz")) {
            assertNotNull(compressed, "required retained original producer corpus must be installed; no substitute or skip");
            try (GZIPInputStream source = new GZIPInputStream(compressed)) {
                JsonNode capture = JSON.readTree(source);
                for (JsonNode row : capture.get("cases")) if (name.equals(row.path("name").textValue())) return object(row).deepCopy();
            }
        }
        throw new IOException("required original producer case absent: " + name);
    }
    private static ObjectNode object(JsonNode value) {
        assertTrue(value instanceof ObjectNode, "required original producer object"); return (ObjectNode) value;
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); }
        catch (IOException invalid) { throw new IllegalArgumentException("fixture JSON serialization failed", invalid); }
    }
}
