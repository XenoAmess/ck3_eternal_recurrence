package org.xar.ck3.control.wave2.development;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentJson;
import org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionCashCaptureContract;

/** Actual service discovery and original-producer evidence, before the unified host boundary tests. */
final class ConstructionProjectionCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test
    void actualServiceResourceDiscoversAllSeventeenOperationsAndTheirOwnBudgets() {
        List<RegisteredProjection> ports = ports();
        assertEquals(17, ports.size());
        assertEquals(17, ports.stream().map(RegisteredProjection::operation).distinct().count());
        for (ConstructionProjectionDispatcher.Operation operation : ConstructionProjectionDispatcher.Operation.values()) {
            ProjectionOperation global = ProjectionOperation.fromWire("construction-" + operation.wire());
            RegisteredProjection port = port(global);
            assertEquals(operation.maximumRequestBytes(), port.inputMaximumBytes());
            assertEquals(operation.maximumResponseBytes(), port.outputMaximumBytes());
        }
        assertEquals(1_048_576, port(ProjectionOperation.CONSTRUCTION_INCOME).inputMaximumBytes());
        assertEquals(131_072, port(ProjectionOperation.CONSTRUCTION_ECONOMY_ENRICH).inputMaximumBytes());
        assertEquals(65_536, port(ProjectionOperation.CONSTRUCTION_MODE3).inputMaximumBytes());
    }

    @Test
    void originalTwentyIntentResultsFlowThroughDiscoveredTypedPorts() throws IOException {
        JsonNode golden = resource("/constructionintent/golden.json", false, 65_536);
        assertEquals("xar.ck3.constructionintent-golden/v1", golden.path("schema").textValue());
        assertEquals("75d926271a46405b68858ea80df641c1eaf4962c4deb863995ae00c05aaf3a02",
                golden.path("source_sha256").textValue());
        assertEquals(20, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode request = objectCopy(vector);
            request.remove(List.of("name", "expected"));
            request.put("schema", ConstructionIntentJson.REQUEST_SCHEMA);
            assertEquals(vector.get("expected"), result(ProjectionOperation.CONSTRUCTION_INTENT, bytes(request)),
                    vector.path("name").textValue());
        }
    }

    @Test
    void originalEconomyOutcomesBudgetPrepareCompletedAndSingleReadQueryStayEquivalent() throws IOException {
        JsonNode fixture = resource("/constructioneconomy/original-producer-golden.json.gz", true, 160_000);
        assertEquals("xar.construction-economy-original-producer-golden.v1", fixture.path("schema").textValue());
        assertEquals(25, fixture.path("cases").size());
        for (JsonNode vector : fixture.path("cases")) {
            String kind = vector.path("kind").textValue();
            ProjectionOperation operation = switch (kind) {
                case "outcome" -> ProjectionOperation.CONSTRUCTION_ECONOMY_OUTCOME;
                case "budget" -> ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET;
                case "prepare" -> ProjectionOperation.CONSTRUCTION_ECONOMY_PREPARE;
                case "completed" -> ProjectionOperation.CONSTRUCTION_ECONOMY_COMPLETED;
                case "query" -> ProjectionOperation.CONSTRUCTION_ECONOMY_QUERY_OUTCOME;
                default -> throw new IllegalArgumentException("unrecognized original producer case");
            };
            ObjectNode request = objectCopy(vector.get("request"));
            request.put("schema", internal(operation).requestSchema());
            assertEquals(vector.get("expected"), result(operation, bytes(request)), vector.path("name").textValue());
            if ("query".equals(kind)) {
                assertEquals(3, request.path("cash").path("queried_revision").intValue());
                assertEquals(2, request.path("cash").path("snapshot_revision").intValue());
                ObjectNode wrongDomain = objectCopy(request);
                wrongDomain.set("expected_revision", request.path("cash").get("snapshot_revision"));
                assertInstanceOf(ProjectionResult.Rejected.class, execute(operation, bytes(wrongDomain)),
                        "native snapshot revision must not impersonate the public query revision");
            }
        }
    }

    @Test
    void originalQuoteAndM5ConsumersKeepAllTwelveResultsAndSeparateReferenceHostRequirements() throws IOException {
        JsonNode fixture = resource("/constructioneconomy/original-consumers-golden.json.gz", true, 160_000);
        ConstructionCashCaptureContract.validate(fixture);
        assertEquals(12, fixture.path("cases").size());
        for (JsonNode vector : fixture.path("cases")) {
            boolean quote = "quote".equals(vector.path("kind").textValue());
            ProjectionOperation operation = quote ? ProjectionOperation.CONSTRUCTION_ECONOMY_QUOTE
                    : ProjectionOperation.CONSTRUCTION_ECONOMY_ENRICH;
            ObjectNode request = objectCopy(vector.get("request"));
            request.put("schema", internal(operation).requestSchema());
            if (quote && !"known".equals(request.path("observation").textValue())) {
                request.putNull("cash");
                request.putNull("reserve_gold_raw");
            }
            assertEquals(vector.get("expected"), result(operation, bytes(request)), vector.path("name").textValue());
        }
    }

    @Test
    void rawBooleanFloatAndStringIdentityTokensAreRejectedWithoutNormalization() throws IOException {
        JsonNode fixture = resource("/constructionintent/golden.json", false, 65_536);
        JsonNode vector = null;
        for (JsonNode candidate : fixture.path("cases")) {
            if ("legacy-applied-without-explicit-flags".equals(candidate.path("name").textValue())) { vector = candidate; }
        }
        assertNotNull(vector, "original negative regression input must be present");
        ObjectNode request = objectCopy(vector);
        request.remove(List.of("name", "expected"));
        request.put("schema", ConstructionIntentJson.REQUEST_SCHEMA);
        String raw = new String(bytes(request), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"actor_character_id\":31254"));
        for (String token : List.of("true", "31254.0", "\"31254\"")) {
            String invalid = raw.replace("\"actor_character_id\":31254", "\"actor_character_id\":" + token);
            assertInstanceOf(ProjectionResult.Rejected.class,
                    execute(ProjectionOperation.CONSTRUCTION_INTENT, invalid.getBytes(StandardCharsets.UTF_8)), token);
        }
        ObjectNode missing = objectCopy(request);
        missing.remove("deferred_selected_step");
        assertInstanceOf(ProjectionResult.Rejected.class,
                execute(ProjectionOperation.CONSTRUCTION_INTENT, bytes(missing)));
    }

    @Test
    void incomeUsesItsOneMiBRoleBudgetForOpaqueUnrelatedHistory() throws IOException {
        ObjectNode request = JSON.createObjectNode();
        request.put("schema", internal(ProjectionOperation.CONSTRUCTION_INCOME).requestSchema());
        request.put("operation", "observe");
        request.putObject("snapshot").put("native_revision", 2).put("date_raw", 10)
                .putObject("played_character").put("character_id", 1);
        request.putArray("history").addObject().put("command", "unrelated-command").put("ok", true)
                .put("opaque_result", "x".repeat(70_000));
        byte[] raw = bytes(request);
        assertTrue(raw.length > 65_536);
        assertEquals(JSON.readTree("[false,null]"), result(ProjectionOperation.CONSTRUCTION_INCOME, raw));
        ObjectNode wrongSchema = objectCopy(request);
        wrongSchema.put("schema", internal(ProjectionOperation.CONSTRUCTION_INTENT).requestSchema());
        assertInstanceOf(ProjectionResult.Rejected.class,
                execute(ProjectionOperation.CONSTRUCTION_INTENT, bytes(wrongSchema)));
    }

    @Test
    void immutableStartingIncomeSampleUsesTheOriginalReceiptCarryAfterMaterialCompletion() throws IOException {
        JsonNode fixture = resource("/constructionincome/golden.json", false, 32_768);
        assertEquals("xar.ck3.constructionincome-golden/v1", fixture.path("schema").textValue());
        int receiptCases = 0;
        for (JsonNode vector : fixture.path("cases")) {
            if (!"receipt_income".equals(vector.path("operation").textValue())) { continue; }
            ObjectNode observe = JSON.createObjectNode();
            observe.put("schema", internal(ProjectionOperation.CONSTRUCTION_INCOME).requestSchema());
            observe.put("operation", "observe");
            observe.set("snapshot", vector.get("snapshot"));
            observe.set("history", vector.get("history"));
            JsonNode initialSample = result(ProjectionOperation.CONSTRUCTION_INCOME, bytes(observe));
            ObjectNode carry = JSON.createObjectNode();
            carry.put("schema", internal(ProjectionOperation.CONSTRUCTION_INCOME).requestSchema());
            carry.put("operation", "receipt_income_sample");
            carry.set("snapshot", vector.get("snapshot"));
            carry.set("observation", initialSample);
            carry.set("prior_receipt", vector.get("prior_receipt"));
            carry.set("cold_recheck", vector.get("cold_recheck"));
            carry.set("completed", vector.get("completed"));
            assertEquals(vector.get("expected"), result(ProjectionOperation.CONSTRUCTION_INCOME, bytes(carry)),
                    vector.path("name").textValue());
            ObjectNode changedLaterHistory = objectCopy(observe);
            changedLaterHistory.putArray("history").addObject().put("command", "unrelated-later-command");
            result(ProjectionOperation.CONSTRUCTION_INCOME, bytes(changedLaterHistory));
            assertEquals(vector.get("expected"), result(ProjectionOperation.CONSTRUCTION_INCOME, bytes(carry)),
                    "the immutable initial pair must not reread later history");
            receiptCases++;
        }
        assertTrue(receiptCases > 0, "original carry fixtures are mandatory");
    }

    @Test
    void unrelatedHistoryShortCircuitsBeforeItsWronglyTypedOkAndResultPayloads() throws IOException {
        ObjectNode request = JSON.createObjectNode();
        request.put("schema", internal(ProjectionOperation.CONSTRUCTION_INCOME).requestSchema());
        request.put("operation", "observe");
        request.putObject("snapshot").put("native_revision", 2).put("date_raw", 10)
                .putObject("played_character").put("character_id", 1);
        var history = request.putArray("history");
        history.addObject().put("command", "unrelated-command").putObject("ok").put("wrong_type", true);
        history.addObject().put("command", false).put("ok", 1.0).putArray("result").addNull();
        history.addObject().putNull("command").put("ok", "opaque").put("result", false);
        assertEquals(JSON.readTree("[false,null]"),
                result(ProjectionOperation.CONSTRUCTION_INCOME, bytes(request)));
        String invalidPair = """
                {"schema":"xar.ck3.construction-income-java-request/v1",
                 "operation":"receipt_income_sample","snapshot":{},"observation":[false,1.0],
                 "prior_receipt":{},"cold_recheck":false,"completed":false}
                """;
        assertInstanceOf(ProjectionResult.Rejected.class,
                execute(ProjectionOperation.CONSTRUCTION_INCOME, invalidPair.getBytes(StandardCharsets.UTF_8)));
    }


    @Test
    void originalBusinessRefusalsAndUnavailableSourceBindingsKeepTheirExactSharedCodes() throws IOException {
        JsonNode fixture = resource("/constructioneconomy/original-producer-golden.json.gz", true, 160_000);
        ObjectNode budget = namedEconomyRequest(fixture, "negative_net_raised_once", ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET);
        ObjectNode unnormalized = objectCopy(budget);
        ((ObjectNode) unnormalized.get("cash")).put("read_only", false);
        assertRejection(ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET, bytes(unnormalized),
                ProjectionError.Code.DOMAIN_REJECTED, "normalized current cash resources are required");
        ObjectNode wrongBuildSource = objectCopy(budget);
        ((ObjectNode) wrongBuildSource.get("cash")).put("executable_sha256", "0".repeat(64));
        assertRejection(ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET, bytes(wrongBuildSource),
                ProjectionError.Code.DOMAIN_REJECTED, "native source does not match a frozen exact build");
        ObjectNode wrongSemantics = objectCopy(budget);
        ((ObjectNode) wrongSemantics.path("cash").get("monthly_income_semantics")).put("time_basis", "day");
        assertRejection(ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET, bytes(wrongSemantics),
                ProjectionError.Code.DOMAIN_REJECTED, "war cash monthly flow lost its exact-build semantics");
        ObjectNode crossed = namedEconomyRequest(fixture, "cash_net_and_wallet_verified_debit", ProjectionOperation.CONSTRUCTION_ECONOMY_OUTCOME);
        crossed.put("exact_ck3_build", "1.20.0.3");
        assertRejection(ProjectionOperation.CONSTRUCTION_ECONOMY_OUTCOME, bytes(crossed),
                ProjectionError.Code.DOMAIN_REJECTED, "construction cash interval crossed its exact build");
        ObjectNode stale = namedEconomyRequest(fixture, "single_read_current_zero_new_spend", ProjectionOperation.CONSTRUCTION_ECONOMY_QUERY_OUTCOME);
        stale.put("expected_revision", stale.path("cash").get("queried_revision").bigIntegerValue().add(java.math.BigInteger.ONE));
        assertRejection(ProjectionOperation.CONSTRUCTION_ECONOMY_QUERY_OUTCOME, bytes(stale),
                ProjectionError.Code.OPERATION_UNAVAILABLE, "registered operation server context unavailable");
        byte[] noProcess = """
                {"schema":"xar.ck3.construction-readback-java-request/v1","operation":"priority",
                 "ledger":{"applied_prior":[],"applied":{"episode_run_id":"catalog-episode"}},
                 "snapshot":{"episode_run_id":"catalog-episode"},"process_identity":null}
                """.getBytes(StandardCharsets.UTF_8);
        assertRejection(ProjectionOperation.CONSTRUCTION_READBACK, noProcess,
                ProjectionError.Code.OPERATION_UNAVAILABLE, "registered operation server context unavailable");
    }

    private static ObjectNode namedEconomyRequest(JsonNode fixture, String name, ProjectionOperation operation) {
        for (JsonNode vector : fixture.path("cases")) {
            if (name.equals(vector.path("name").textValue())) {
                ObjectNode request = objectCopy(vector.get("request"));
                request.put("schema", internal(operation).requestSchema());
                return request;
            }
        }
        throw new IllegalStateException("required original economy request is absent: " + name);
    }

    private static void assertRejection(ProjectionOperation operation, byte[] raw, ProjectionError.Code code, String message) {
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute(operation, raw));
        assertEquals(code, rejected.error().code());
        assertEquals(message, rejected.error().message());
    }

    private static ConstructionProjectionDispatcher.Operation internal(ProjectionOperation operation) {
        return ConstructionProjectionDispatcher.Operation.fromWire(
                operation.wire().substring("construction-".length()));
    }

    private static List<RegisteredProjection> ports() {
        List<ProjectionPortCatalog> discovered = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type().equals(ConstructionProjectionCatalog.class))
                .map(ServiceLoader.Provider::get).toList();
        assertEquals(1, discovered.size(), "META-INF/services must discover the real public no-arg catalog");
        return discovered.getFirst().registrations();
    }

    private static RegisteredProjection port(ProjectionOperation operation) {
        return ports().stream().filter(value -> value.operation() == operation).findFirst()
                .orElseThrow(() -> new IllegalStateException("missing service-discovered construction operation"));
    }

    private static ProjectionResult execute(ProjectionOperation operation, byte[] raw) {
        ProjectionCall.Identity identity = new ProjectionCall.Identity("construction-catalog-regression", operation);
        ProjectionResult result = port(operation).execute(
                new ProjectionCall(identity, ProjectionJson.object(raw, ProjectionJson.MAX_BYTES)));
        if (result instanceof ProjectionResult.Succeeded success) { assertEquals(identity, success.identity()); }
        if (result instanceof ProjectionResult.Rejected rejected) { assertEquals(identity, rejected.identity().orElseThrow()); }
        return result;
    }

    private static JsonNode result(ProjectionOperation operation, byte[] raw) throws IOException {
        return JSON.readTree(assertInstanceOf(ProjectionResult.Succeeded.class, execute(operation, raw)).result().bytes());
    }

    private static ObjectNode objectCopy(JsonNode value) {
        assertInstanceOf(ObjectNode.class, value);
        return ((ObjectNode) value).deepCopy();
    }

    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }

    private static JsonNode resource(String name, boolean compressed, int maximumBytes) throws IOException {
        InputStream resource = ConstructionProjectionCatalogTest.class.getResourceAsStream(name);
        assertNotNull(resource, "actual original-producer capture is required; absent evidence is a failure");
        try (InputStream source = resource;
                InputStream input = compressed ? new GZIPInputStream(source) : source) {
            byte[] raw = input.readNBytes(maximumBytes + 1);
            assertTrue(raw.length <= maximumBytes, "bounded original evidence expansion");
            if ("/constructioneconomy/original-consumers-golden.json.gz".equals(name)) {
                raw = ConstructionCashCaptureContract.decode(raw).bytes();
            }
            return JSON.readTree(raw);
        }
    }
}
