package org.xar.ck3.control.g2.m0;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.*;

/** Original full provider envelopes through raw M0 and G2 ingress; no native qualification. */
final class RaiktorConfigurationWireTest {
    @Test void independentProvidersAndCombinedConfigurationHaveTheOriginalCompleteEnvelopes(@TempDir Path directory) throws Exception {
        ObjectNode budget = resource(directory, "raiktor_exit_budget_v1.json");
        ObjectNode model = resource(directory, "raiktor_exit_utility_v1.json");
        ObjectNode budgetRequest = budgetRequest(budget);
        JsonNode budgetProvider = outer(budgetRequest);
        assertEquals("xar.ck3.raiktor_owner_budget_profile_provider.v1", budgetProvider.path("schema").textValue());
        assertEquals("available", budgetProvider.path("status").textValue());
        assertEquals("repository_default", budgetProvider.path("source_kind").textValue());
        assertEquals(budget.path("sha256").textValue().toUpperCase(), budgetProvider.at("/source/sha256").textValue());
        assertTrue(budgetProvider.path("default_source_used").booleanValue());
        assertTrue(budgetProvider.path("profile_production_eligible").booleanValue());
        assertEquals("raiktor-owner-budget-profile-v1", budgetProvider.at("/owner_budget_profile/contract").textValue());
        JsonNode modelProvider = outer(modelRequest(budget, model));
        assertEquals("xar.ck3.raiktor_exit_utility_model_provider.v1", modelProvider.path("schema").textValue());
        assertEquals("raiktor-exit-utility-model-file-provider-v1", modelProvider.path("provider").textValue());
        assertEquals(budget.path("sha256").textValue().toUpperCase(),
                modelProvider.at("/exit_utility_model/budget_profile_binding/profile_source_sha256").textValue());
        assertFalse(modelProvider.at("/downstream_readiness/automatic_surrender_ready").booleanValue());
        ObjectNode combined = StrictJson.object().put("operation", "load-strategy-configuration");
        ObjectNode sources = combined.putObject("configuration_sources");
        sources.set("default_budget", budget); sources.set("default_model", model);
        sources.putNull("budget_override"); sources.putNull("model_override");
        JsonNode pair = outer(combined);
        assertTrue(RaiktorRawJson.same(budgetProvider, pair.path("budget_provider")));
        assertTrue(RaiktorRawJson.same(modelProvider, pair.path("model_provider")));
        Files.delete(Path.of(model.path("path").textValue()));
        assertEquals("available", outer(budgetRequest).path("status").textValue());
        rejects(modelRequest(budget, model));
    }

    @Test void explicitBudgetAndModelOverridesKeepIndependentBaseBindingAndDraftApproval(@TempDir Path directory) throws Exception {
        ObjectNode budget = resource(directory, "raiktor_exit_budget_v1.json");
        ObjectNode model = resource(directory, "raiktor_exit_utility_v1.json");
        ObjectNode baseBudget = document(budget); ObjectNode baseModel = document(model);
        ObjectNode overrideBudget = baseBudget.deepCopy();
        activation(overrideBudget, "profile", baseBudget);
        overrideBudget.put("profile_id", "fixture-complete-override");
        ObjectNode budgetRequest = budgetRequest(budget);
        ObjectNode overrideRef = write(directory.resolve("budget-override.json"), overrideBudget);
        budgetRequest.set("budget_override", overrideRef);
        JsonNode producedBudget = outer(budgetRequest);
        assertFalse(producedBudget.path("default_source_used").booleanValue());
        assertEquals("operator_override", producedBudget.path("source_kind").textValue());
        assertEquals("fixture-complete-override", producedBudget.at("/owner_budget_profile/profile_id").textValue());
        ObjectNode modelOverride = baseModel.deepCopy(); activation(modelOverride, "model", baseModel);
        modelOverride.put("model_id", "fixture-complete-model-override");
        ObjectNode modelRequest = modelRequest(budget, model);
        modelRequest.set("model_override", write(directory.resolve("model-override.json"), modelOverride));
        JsonNode producedModel = outer(modelRequest);
        assertEquals("operator_override", producedModel.path("source_kind").textValue());
        assertEquals(baseBudget.path("profile_id"), producedModel.at("/exit_utility_model/budget_profile_binding/profile_id"));
        ObjectNode wrongBase = modelOverride.deepCopy();
        ((ObjectNode) wrongBase.path("activation")).put("base_model_version", "999.0.0");
        modelRequest.set("model_override", write(directory.resolve("model-wrong-base.json"), wrongBase)); rejects(modelRequest);
        ObjectNode draft = baseBudget.deepCopy();
        draft.remove(java.util.List.of("profile_version", "activation"));
        draft.put("schema_version", 1).put("contract", "raiktor-owner-budget-profile-source-v1");
        draft.putObject("approval").put("status", "draft").putNull("approved_by").putNull("approved_at_utc");
        budgetRequest.set("budget_override", write(directory.resolve("draft.json"), draft));
        JsonNode draftProvider = outer(budgetRequest);
        assertEquals("incomplete", draftProvider.path("status").textValue());
        assertFalse(draftProvider.path("profile_production_eligible").booleanValue());
        assertTrue(draftProvider.path("source_profile_version").isNull());
        assertEquals("owner_budget_profile_not_owner_approved", draftProvider.at("/blockers/0").textValue());
    }

    @Test void exactFileIdentityAndMissingNullTypeDistinctionsApplyBeforeProviderRendering(@TempDir Path directory) throws Exception {
        ObjectNode budget = resource(directory, "raiktor_exit_budget_v1.json");
        ObjectNode model = resource(directory, "raiktor_exit_utility_v1.json");
        ObjectNode request = budgetRequest(budget);
        ObjectNode missing = request.deepCopy(); missing.remove("budget_override"); rejects(missing);
        ObjectNode wrongName = request.deepCopy(); wrongName.set("override", wrongName.remove("budget_override")); rejects(wrongName);
        ObjectNode booleanSize = request.deepCopy(); ((ObjectNode) booleanSize.path("default_budget")).put("bytes", true); rejects(booleanSize);
        ObjectNode floatSize = request.deepCopy(); ((ObjectNode) floatSize.path("default_budget")).put("bytes", 12.0); rejects(floatSize);
        ObjectNode badHash = request.deepCopy(); ((ObjectNode) badHash.path("default_budget")).put("sha256", "A".repeat(64)); rejects(badHash);
        ObjectNode extraModel = request.deepCopy(); extraModel.set("default_model", model); rejects(extraModel);
        ObjectNode invalidBudget = document(budget);
        invalidBudget.put("profile_id", "drifted-current-default");
        ObjectNode driftedRef = write(directory.resolve("drifted-default-budget.json"), invalidBudget);
        rejects(modelRequest(driftedRef, model));
        ObjectNode changedFileRequest = request.deepCopy();
        Files.writeString(Path.of(budget.path("path").textValue()), "{}");
        rejects(changedFileRequest);
    }

    private static ObjectNode budgetRequest(ObjectNode budget) {
        ObjectNode request = StrictJson.object().put("operation", "provide-owner-budget-profile");
        request.set("default_budget", budget); request.putNull("budget_override"); return request;
    }
    private static ObjectNode modelRequest(ObjectNode budget, ObjectNode model) {
        ObjectNode request = StrictJson.object().put("operation", "provide-exit-utility-model");
        request.set("default_budget", budget); request.set("default_model", model); request.putNull("model_override"); return request;
    }
    private static void activation(ObjectNode chosen, String kind, ObjectNode base) {
        chosen.putObject("activation").put("kind", "operator_override").put("source", "synthetic-wire-regression")
                .put("base_" + kind + "_id", base.path(kind + "_id").textValue())
                .put("base_" + kind + "_version", base.path(kind + "_version").textValue());
    }
    private static JsonNode outer(ObjectNode request) {
        var source = new G2Source("fixture-machine", "2026-10-23T18:45:00Z", "synthetic-provider-wire-only",
                new ExactRef("synthetic-raw-input", 1, "a".repeat(64)));
        var input = new G2Request("raw-m0-provider-fixture", Milestone.M0, source,
                ProjectionJson.object(RaiktorExitObservationCodec.encodeWire(request), ProjectionJson.MAX_BYTES));
        var result = new M0Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(input)));
        return StrictJson.parse(G2Wire.decodeResponse(G2Wire.encodeResponse(result)).result().bytes(), StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static void rejects(ObjectNode request) { assertThrows(IllegalArgumentException.class, () -> outer(request)); }
    private static ObjectNode resource(Path directory, String name) throws Exception {
        try (InputStream input = RaiktorConfigurationWireTest.class.getResourceAsStream("/g2/m0/raw-producers/" + name)) {
            if (input == null) throw new IllegalStateException("actual repository policy resource is missing: " + name);
            byte[] bytes = input.readNBytes(65537);
            if (bytes.length == 0 || bytes.length > 65536) throw new IllegalStateException("policy resource outside bound");
            return writeBytes(directory.resolve(name), bytes);
        }
    }
    private static ObjectNode document(ObjectNode ref) throws Exception {
        return (ObjectNode) StrictJson.parse(Files.readAllBytes(Path.of(ref.path("path").textValue())), StrictJson.EXPLICIT_MAX_BYTES);
    }
    private static ObjectNode write(Path path, ObjectNode value) throws Exception {
        return writeBytes(path, RaiktorExitObservationCodec.encodeWire(value));
    }
    private static ObjectNode writeBytes(Path path, byte[] raw) throws Exception {
        Files.write(path, raw, java.nio.file.StandardOpenOption.CREATE_NEW);
        return StrictJson.object().put("path", path.toString()).put("bytes", raw.length)
                .put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    }
}

