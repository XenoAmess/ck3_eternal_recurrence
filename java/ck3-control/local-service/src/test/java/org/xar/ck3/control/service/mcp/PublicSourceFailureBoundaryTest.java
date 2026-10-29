package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeFailure;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.service.root.PrisonerPublicFailure12004;
import org.xar.ck3.control.service.root.RootAubRuntimeFactory;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;

/** Actual pure failure producers and packet parsers -> software MCP Directory/Session/both RPC.
 * Packet/reference inputs below are error DATA, never a live Native or canonical archive qualification. */
final class PublicSourceFailureBoundaryTest {
    private record Tool(String name,String arguments) { }
    private static final String POLICY="aub_policy_treasury_only_pause_choice";
    private static final String DESIRED="aub_policy_treasury_only_continue_choice";
    private static final BigInteger WIDE=new BigInteger("18446744073709551615");

    @Test void actualAubMutationGuardPreservesBothMessagesAndOriginalPreSubmissionDefaults() throws Exception {
        List<AubOperations.Mutation> mutations=List.of(
                new AubOperations.Select(AubOperations.PolicyKey.TREASURY_PAUSE,AubOperations.PolicyKey.TREASURY_CONTINUE),
                new AubOperations.Confirm(AubOperations.PolicyKey.TREASURY_PAUSE));
        for(var mutation:mutations) {
            var original=assertThrows(RootAubRuntimeFactory.PreSubmissionRevisionMismatch.class,
                    ()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.of(WIDE),BigInteger.ONE));
            boolean select=mutation instanceof AubOperations.Select;
            assertEquals(select?"AUB select public revision changed":"AUB Confirm public revision changed",original.getMessage());
            assertSame(mutation,original.mutation());assertEquals(WIDE,original.expectedRevision());
            assertEquals(BigInteger.ONE,original.actualRevision());
            Tool tool=new Tool(select?"ck3_select_aub_policy_option_v1":"ck3_confirm_aub_policy_v1",
                    "{\"expected_selected_key\":\""+POLICY+"\","+(select?"\"desired_key\":\""+DESIRED+"\",":"")
                    +"\"expected_revision\":\""+WIDE+"\"}");
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values()) {
                var publicFailure=boundary(consumer,tool,original,PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH);
                publicFailure.ifPresent(PublicSourceFailureBoundaryTest::assertDefaults);
            }
            assertDoesNotThrow(()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.of(WIDE),WIDE));
            assertDoesNotThrow(()->RootAubRuntimeFactory.requireExpectedPublicRevision(mutation,Optional.empty(),BigInteger.ONE));
        }
    }

    @Test void actualContactRevisionGuardsPreserveBothOriginalMessagesAndDefaultFields() throws Exception {
        for(var query:queries()) {
            var original=assertThrows(ContactScopeFailure.class,
                    ()->ContactScopeFailure.requireExpectedRevision(query,WIDE,BigInteger.ONE));
            assertEquals(ContactScopeFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,original.kind());
            assertEquals(query instanceof ContactScopeObservation.Projected?"projected-contact source revision is stale"
                    :"native gameplay revision mismatch: expected "+WIDE+", current 1",original.getMessage());
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
                boundary(consumer,tool(query),original,PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH)
                        .ifPresent(PublicSourceFailureBoundaryTest::assertDefaults);
        }
    }

    @Test void actualContactIoKeepsItsIdenticalCauseAndUnknownNeverAcquiresATimeoutClass() throws Exception {
        for(var query:queries()) {
            var io=new IOException("actual Root contact observation read failed");
            var source=ContactScopeFailure.fromIo(query,io);assertSame(io,source.getCause());
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
                boundary(consumer,tool(query),source,PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE)
                        .ifPresent(value->{assertTrue(value.preSubmissionDefaults().isEmpty());assertTrue(value.nativeAttributes().isEmpty());});
            var outcome=new NativeActionPort.Unknown("contact-data","native command_result timed out; native gameplay step failed",
                    new byte[]{1},Optional.empty());
            var unavailable=new PlanningReadResult.Unavailable<ContactScopeObservation>("outer read unavailable",Optional.of(outcome));
            var unknown=ContactScopeFailure.from(query,unavailable);
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE,unknown.kind());assertSame(unavailable,unknown.unavailable().orElseThrow());
            assertSame(outcome,unknown.original().orElseThrow());assertEquals(outcome.reason(),unknown.getMessage());
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
                PublicSourceFailureRpcAssertions.assertOriginal(consumer,tool(query).name(),tool(query).arguments(),unknown,Optional.empty());
        }
    }

    @Test void matchingContactFalseTopUsesTheSourceRejectedKindAndWrongQueryStaysUnclassified() throws Exception {
        for(var query:queries()) {
            var ack=ack(query.step());
            var unavailable=new PlanningReadResult.Unavailable<ContactScopeObservation>("actual read failed",Optional.of(ack));
            var original=ContactScopeFailure.from(query,unavailable);
            assertEquals(ContactScopeFailure.Kind.NATIVE_COMMAND_REJECTED,original.kind());
            assertEquals("native gameplay step failed: original contact refusal",original.getMessage());
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
                boundary(consumer,tool(query),original,PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED)
                        .ifPresent(value->{assertSame(unavailable,((ContactScopeFailure)value.originalFailure().orElseThrow()).unavailable().orElseThrow());
                            assertSame(ack,original.original().orElseThrow());assertTrue(value.preSubmissionDefaults().isEmpty());});
            var wrong=ContactScopeFailure.from(query,new PlanningReadResult.Unavailable<>("wrong original request",Optional.of(ack("another-step"))));
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE,wrong.kind());
            for(var consumer:PublicPlanningRpcAssertions.Consumer.values())
                PublicSourceFailureRpcAssertions.assertOriginal(consumer,tool(query).name(),tool(query).arguments(),wrong,Optional.empty());
        }
    }

    @Test void actualPrisonerReadFailureKeepsTheSameUnavailableOutcomeReferencesAndExplicitBridgeType() throws Exception {
        var outcome=new NativeActionPort.Unknown("prison-data","original unknown reason includes timeout but has no typed timeout proof",
                new byte[]{1},Optional.empty());
        var unavailable=new PlanningReadResult.Unavailable<RawJson>("outer prisoner read unavailable",Optional.of(outcome));
        var reference=new ExactRef("software-error-data:prisoner-source",1,"a".repeat(64));
        var original=PrisonerPublicFailure12004.read(unavailable,reference,
                new OperationKey(PrisonerNativeQueries.step(0)),Instant.parse("2026-10-25T02:00:00Z"));
        assertEquals("BridgeUnavailableError",original.pythonClassName());assertEquals(outcome.reason(),original.getMessage());
        Tool tool=new Tool("ck3_query_player_prisoner_collection_private_v1","{\"expected_revision\":1}");
        for(var consumer:PublicPlanningRpcAssertions.Consumer.values()) {
            boundary(consumer,tool,original,PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE).ifPresent(value->{
                var same=assertInstanceOf(PrisonerPublicFailure12004.class,value.originalFailure().orElseThrow());
                assertSame(original,same);assertSame(unavailable,same.originalRead().orElseThrow());
                assertSame(outcome,same.originalOutcome().orElseThrow());assertSame(reference,same.originalReferences().get(0));
                assertTrue(value.originalCandidate().isEmpty(),"full source references are retained; no arbitrary primary ref is invented");
                assertTrue(value.nativeAttributes().isEmpty());assertTrue(value.preSubmissionDefaults().isEmpty());
            });
        }
    }

    @Test void publicDetailsRejectMessageChangesAndAttributesOutsideTheirExactProfiles() {
        var original=new IllegalStateException("original data error");
        var defaults=Optional.of(PublicServiceFailure.PreSubmissionDefaults.ORIGINAL);
        var details=new PublicServiceFailure.Details(original,Optional.empty(),defaults);
        assertThrows(IllegalArgumentException.class,()->new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                "changed data error",Optional.empty(),details));
        assertThrows(IllegalArgumentException.class,()->new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                original.getMessage(),Optional.empty(),details));
        var attributes=new PublicServiceFailure.NativeAttributes(raw("null"),"actual-source-request-id");
        assertThrows(IllegalArgumentException.class,()->new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                original.getMessage(),Optional.empty(),new PublicServiceFailure.Details(original,Optional.of(attributes),Optional.empty())));
        var legacy=new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,original.getMessage(),Optional.empty());
        assertTrue(legacy.details().isEmpty());assertTrue(legacy.originalFailure().isEmpty());
    }

    private static Optional<PublicServiceFailure> boundary(PublicPlanningRpcAssertions.Consumer consumer,Tool tool,
            RuntimeException original,PublicServiceFailure.Kind kind) throws Exception {
        return PublicSourceFailureRpcAssertions.assertOriginal(consumer,tool.name(),tool.arguments(),original,Optional.of(kind));
    }
    private static void assertDefaults(PublicServiceFailure failure) {
        var defaults=failure.preSubmissionDefaults().orElseThrow();assertTrue(defaults.selectedStep().isEmpty());
        assertTrue(defaults.plan().isEmpty());assertEquals(0,defaults.replanCount());
        assertTrue(failure.nativeAttributes().isEmpty());assertTrue(failure.originalCandidate().isEmpty());
    }
    private static List<ContactScopeObservation.Query> queries() {
        return List.of(new ContactScopeObservation.Projected(new ProjectedContactPolicy.QueryKey(0,31,30)),
                new ContactScopeObservation.Actual(new ActualContactModel.Query(0,31)));
    }
    private static Tool tool(ContactScopeObservation.Query query) {
        boolean projected=query instanceof ContactScopeObservation.Projected;
        return new Tool(projected?"ck3_query_projected_contact_scope_v1":"ck3_query_actual_contact_scope",
                "{\"subject_army_id\":0,\"target_province_id\":31,"+(projected?"\"incoming_entry_province_id\":30,":"")
                +"\"expected_revision\":1}");
    }
    private static NativeActionPort.AckReceived ack(String step) {
        var body=raw("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"contact-data\",\"ok\":false,\"error\":\"original contact refusal\"}");
        var request=raw("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"contact-data\",\"step\":\""+step+"\",\"expected_revision\":1}");
        return new NativeActionPort.AckReceived("contact-data",false,Optional.empty(),body,packet(body.bytes()),
                Optional.of(new NativeActionPort.OutboundPacket("contact-data",packet(request.bytes()))));
    }
    private static byte[] packet(byte[] body) {
        return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
    }
    private static RawJson raw(String value) {return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
}
