package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class PeacetimeAssemblyApplicationTest {
    private static JsonNode golden() throws IOException {
        try (InputStream resource = PeacetimeAssemblyApplicationTest.class.getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            if (resource == null) throw new IOException("actual thirteen-case original producer golden required; missing is RED");
            try (GZIPInputStream stream = new GZIPInputStream(resource)) {
                byte[] raw = stream.readNBytes(1_048_577);
                if (raw.length > 1_048_576) throw new IOException("original assembly golden exceeds 1 MiB");
                // The corpus envelope has a larger declared budget; each actual domain payload stays at 128 KiB.
                return org.xar.ck3.control.contracts.StrictJson.parse(raw, 1_048_576);
            }
        }
    }

    private static RegisteredProjection port() {
        return RegisteredProjection.of(new PeacetimeAssemblyProjectionPort());
    }
    private static ProjectionResult invoke(byte[] raw, String id) {
        return port().execute(new ProjectionCall(new ProjectionCall.Identity(id, ProjectionOperation.PEACETIME_ASSEMBLY_COLLECT),
                ProjectionJson.object(raw, PeacetimeAssemblyApplication.MAXIMUM_BYTES)));
    }

    @Test void allOriginalCasesUseTypedApplicationAndActualIntakeSelector() throws IOException {
        JsonNode cases = golden().get("cases"); assertEquals(13, cases.size());
        for (JsonNode sample : cases) {
            byte[] input = SdkProjectionJson.encode(M5CompactWireFixtures.currentAssembly(sample.get("input")), PeacetimeAssemblyApplication.MAXIMUM_BYTES);
            ProjectionResult result = invoke(input, sample.get("name").textValue());
            if (!sample.get("accepted").booleanValue()) {
                ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, result);
                assertTrue(Set.of(ProjectionError.Code.DOMAIN_REJECTED, ProjectionError.Code.INVALID_PAYLOAD).contains(rejected.error().code()));
                continue;
            }
            ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, result);
            Obj packet = object(OpportunityJson.parse(succeeded.result().bytes()), "assembly result");
            assertEquals(Set.of("schema", "sources", "intake"), packet.members().keySet());
            assertEquals(new Text(PeacetimeAssemblyApplication.RESULT_SCHEMA), packet.get("schema"));
            assertEquals(OpportunityJson.parse(PeacetimeAssembly.assemble(input)), packet.get("sources"));
            assertEquals(OpportunityJson.parse(PeacetimeAssembly.assembleAndCollect(input)), packet.get("intake"));
            Obj intake = object(packet.get("intake"), "actual intake"), expected = object(OpportunityJson.parse(SdkProjectionJson.encode(sample.get("collector"))), "original collector");
            assertEquals(expected.get("collected_candidate_ids"), intake.get("collected_candidate_ids"));
            assertEquals(expected.get("collected_domains"), intake.get("collected_domains"));
            // Re-enter the actual selector in the regression only: no Python policy or fabricated analysis is substituted.
            assertEquals(OpportunityJson.parse(ObservedOpportunitySelector.select(OpportunityJson.encode(intake.get("selector_request")))), intake.get("analysis"));
            assertEquals(new Bool(false), intake.get("formal_action_ready"));
            assertEquals(new Bool(false), intake.get("resource_reservation_performed"));
        }
    }

    @Test void oneServiceLoaderRegistrationExposesTheExistingOperation() {
        long registrations = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .map(ServiceLoader.Provider::get).flatMap(catalog -> catalog.registrations().stream())
                .filter(registration -> registration.operation() == ProjectionOperation.PEACETIME_ASSEMBLY_COLLECT).count();
        assertEquals(1, registrations);
    }

    @Test void wholeRoleBudgetDoesNotClaimFullNativeInventoryQualification() {
        PeacetimeAssemblyProjectionPort typed = new PeacetimeAssemblyProjectionPort();
        assertEquals(131_072, typed.inputMaximumBytes()); assertEquals(131_072, typed.outputMaximumBytes());
        byte[] raw = ("{\"padding\":\"" + "x".repeat(131_072) + "\"}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ProjectionJson.object(raw, typed.inputMaximumBytes()));
    }

    @Test void originalOpaqueExponentAndNegativeZeroPassTheCodecIntakeAndSelector() throws IOException {
        byte[] captured = SdkProjectionJson.encode(M5CompactWireFixtures.currentAssembly(golden().get("cases").get(0).get("input")), PeacetimeAssemblyApplication.MAXIMUM_BYTES);
        Obj request = object(OpportunityJson.parse(captured), "captured request");
        Obj opaque = object(OpportunityJson.parse("{\"exponent\":1.2300e+4,\"negative_zero\":-0.0}".getBytes(StandardCharsets.UTF_8)), "opaque extension");
        Obj construction = object(request.get("construction"), "construction").with("retained_extension", opaque);
        byte[] raw = OpportunityJson.encode(request.with("construction", construction));
        assertTrue(new String(raw, StandardCharsets.UTF_8).contains("1.2300e+4"));
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class, invoke(raw, "opaque-original-token"));
        String output = new String(result.result().bytes(), StandardCharsets.UTF_8);
        assertTrue(output.contains("1.2300e+4")); assertTrue(output.contains("-0.0"));
        Obj packet = object(OpportunityJson.parse(result.result().bytes()), "packet");
        Obj intake = object(packet.get("intake"), "intake");
        assertEquals(OpportunityJson.parse(ObservedOpportunitySelector.select(OpportunityJson.encode(intake.get("selector_request")))), intake.get("analysis"));
        Obj source = object(packet.get("sources"), "source"), domains = object(source.get("domains"), "domains");
        Obj returned = object(object(domains.get("building"), "building").get("query"), "query");
        assertEquals(opaque, returned.get("retained_extension"));
    }

    @Test void actualIntakeRejectsDuplicateFamilyCandidatesAndGrandWeddingProof() throws IOException {
        ObjectNode original = null;
        for (JsonNode sample : golden().get("cases")) if (sample.get("name").textValue().equals("family-five-choices"))
            original = M5CompactWireFixtures.currentAssembly(sample.get("input"));
        assertNotNull(original, "full original five-choice case required");
        ObjectNode duplicate = original.deepCopy();
        ArrayNode plans = (ArrayNode) duplicate.get("family").get("pool").get("choice_indices");
        plans.set(1, plans.get(0).deepCopy());
        assertInstanceOf(ProjectionResult.Rejected.class, invoke(SdkProjectionJson.encode(duplicate, 131_072), "duplicate-family"));
        ObjectNode wedding = original.deepCopy();
        for (JsonNode plan : List.of(wedding.get("family").get("pool").get("original_plan")))
            ((ObjectNode) plan.get("family_marriage_private_diagnostic").get("rows").get(0)).put("grand_wedding_option_selected", true);
        assertInstanceOf(ProjectionResult.Rejected.class, invoke(SdkProjectionJson.encode(wedding, 131_072), "unpriced-grand-wedding"));
    }

    @Test void captureRecordsTheReviewedFullSharedFixtureSource() throws IOException {
        JsonNode correction = golden().get("effective_test_source_corrections");
        assertNotNull(correction); assertEquals("xar.m5-shared-test-fixture-corrections/v1", correction.get("schema").textValue());
        assertTrue(correction.get("normal_full_suite_no_policy_patch").booleanValue());
        JsonNode sources = correction.get("sources"); assertEquals(1, sources.size());
        assertEquals("ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py", sources.get(0).get("repository_path").textValue());
        assertEquals(71945, sources.get(0).get("bytes").intValue());
        assertEquals("01644bf52b25ef0b3de5a4cc92e2de7bed4a5d63ad3f6b5cb088d6d21334a6a6", sources.get(0).get("sha256").textValue());
        assertEquals(40, golden().get("original_tests_run").intValue());
    }

    @Test void explicitInputRefusalAndInternalProjectFailureKeepDifferentCategories() throws IOException {
        ObjectNode missing = M5CompactWireFixtures.currentAssembly(golden().get("cases").get(0).get("input"));
        ((ObjectNode) missing.get("construction").get("candidate")).remove("building_type_id");
        ProjectionResult.Rejected refused = assertInstanceOf(ProjectionResult.Rejected.class,
                invoke(SdkProjectionJson.encode(missing, 131_072), "known-building-field-refusal"));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, refused.error().code());
        PeacetimeAssemblyProjectionPort actual = new PeacetimeAssemblyProjectionPort();
        ProjectionPort<PeacetimeAssembly.Inputs, PeacetimeAssemblyApplication.Result> brokenProject = new ProjectionPort<>() {
            @Override public ProjectionOperation operation() { return actual.operation(); }
            @Override public int inputMaximumBytes() { return actual.inputMaximumBytes(); }
            @Override public int outputMaximumBytes() { return actual.outputMaximumBytes(); }
            @Override public PeacetimeAssembly.Inputs decode(byte[] raw) { return actual.decode(raw); }
            @Override public PeacetimeAssemblyApplication.Result project(PeacetimeAssembly.Inputs input) { throw new IllegalArgumentException("internal programming invariant"); }
            @Override public byte[] encode(PeacetimeAssemblyApplication.Result result) { return actual.encode(result); }
        };
        byte[] input = SdkProjectionJson.encode(M5CompactWireFixtures.currentAssembly(golden().get("cases").get(0).get("input")), 131_072);
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("internal-unknown", actual.operation()), ProjectionJson.object(input, 131_072));
        ProjectionResult.Rejected failed = assertInstanceOf(ProjectionResult.Rejected.class, RegisteredProjection.of(brokenProject).execute(call));
        assertEquals(ProjectionError.Code.PROJECTION_FAILED, failed.error().code());
    }
}
