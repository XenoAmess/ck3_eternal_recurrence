package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Actual software packet/read producer to the complete public consumer. No Root/private qualification is minted here. */
class RootCampaignPublicProductsTest {
    @TempDir Path temp;
    private static final BigInteger MAX=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final String SHA="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";

    @Test void actualFinanceRootOriginalFeedsCompletePublicResultAndExactWireRoundtrip()throws Exception {
        AtomicReference<FinanceReadContracts> definitions=new AtomicReference<>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA,"campaign-root-public-software",ref->{
            var actual=new FinanceReadContracts(query->new FinanceReadContracts.Registration(ref,
                    new FinanceReadContracts.Permission(Optional.of("game.command."+query.operation().value()),"game.command."+query.operation().value(),
                            ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP)));
            assertTrue(definitions.compareAndSet(null,actual));return List.of(actual.contract(FinanceReadContracts.Query.ROOT));
        },request->{
            assertEquals(FinanceReadContracts.Query.ROOT.operation().value(),request.step());
            assertTrue(DriverJson.object(request.additionalFields().bytes(),65536).members().isEmpty());
            return originalRoot();
        },Optional.of("1.20.0.4"),Set.of());
        try(var fixture=new ActionWriterIntegrationFixture(temp,false,scenario)) {
            var ready=fixture.ready();Instant deadline=Instant.now().plusSeconds(20);
            var result=fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),deadline,lease->{
                var current=lease.frame();var contract=definitions.get().contract(FinanceReadContracts.Query.ROOT);
                RootCampaignPublicProducts.requirePublicRevision(current,new CampaignRootPublicCodec.Request(current.identity().frame().revision()));
                for(BigInteger expected:List.of(BigInteger.ZERO,current.identity().frame().revision().add(BigInteger.ONE),BigInteger.ONE.shiftLeft(100))) {
                    if(expected.equals(current.identity().frame().revision()))continue;
                    var failure=assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,
                            ()->RootCampaignPublicProducts.requirePublicRevision(current,new CampaignRootPublicCodec.Request(expected)));
                    assertEquals(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,failure.kind());
                    assertEquals("campaign-root revision mismatch: expected "+expected+", current "+current.identity().frame().revision(),failure.getMessage());
                    assertTrue(failure.originalCandidate().isEmpty());
                    var original=OriginalRootRevisionOracle.failure(current.identity().frame().revision(),expected);
                    assertEquals(original.kind(),failure.kind().pythonClassName());assertEquals(original.message(),failure.getMessage());
                    assertEquals(0,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
                }
                var request=new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),contract.operation(),
                        FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),deadline);
                var read=fixture.reads.read(same,contract,request);
                if(!(read instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> actual))throw new AssertionError("actual ROOT software read unavailable: "+read);
                var packet=actual.value();
                assertSame(contract,definitions.get().contract(FinanceReadContracts.Query.ROOT));
                assertEquals(packet.receipt(),actual.receipt());assertArrayEquals(packet.originalFrame(),actual.receipt().original().originalFrame().bytes());
                var publicRequest=new CampaignRootPublicCodec.Request(current.identity().frame().revision());
                var response=CampaignRootPublicCodec.fromActual(current,publicRequest,packet);
                var execution=CampaignRootPublicCodec.executeFromActual(current,publicRequest.expectedRevision(),packet);
                Obj executionWire=DriverJson.object(execution.bytes(),RawJson.MAXIMUM_BYTES);
                for(String extra:Set.of("scope","build","source","binding"))assertFalse(executionWire.members().containsKey(extra));
                assertEquals(new Text(MAX.toString()),executionWire.get("query_sequence"));
                Obj executionNumeric=CampaignRootPublicCodec.decodeExecution(execution);
                assertEquals(response.body().get("campaign_root_context"),executionNumeric.get("campaign_root_context"));
                assertEquals(response.body().get("readiness"),executionNumeric.get("readiness"));
                assertEquals(response.body().get("campaign_root_context_ready"),executionNumeric.get("campaign_root_context_ready"));
                assertEquals(response.body().get("player_heir_fixed_dynasty_projection_v1"),executionNumeric.get("player_heir_fixed_dynasty_projection_v1"));
                RawJson extraWrapper=new RawJson(DriverJson.encode(executionWire.with("scope",new Text("wrong-tool-wrapper"))));
                RawJson missingReadiness=new RawJson(DriverJson.encode(without(executionWire,"readiness")));
                RawJson unsafeQuery=new RawJson(DriverJson.encode(executionWire.with("query_sequence",new IntegerValue(MAX))));
                assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeExecution(extraWrapper));
                assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeExecution(missingReadiness));
                assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeExecution(unsafeQuery));
                assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.fromActual(current,
                        new CampaignRootPublicCodec.Request(publicRequest.expectedRevision().add(BigInteger.ONE)),packet));
                return response;
            }));
            assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
            Obj root=object(result.body().get("campaign_root_context"),"root");
            assertEquals(root.get("readiness"),result.body().get("readiness"));
            assertEquals(root.get("primary_title"),result.body().get("primary_title"));
            assertEquals(new Bool(true),result.body().get("campaign_root_context_ready"));
            assertEquals(new Text("unknown"),object(result.body().get("player_heir_fixed_dynasty_projection_v1"),"unqualified projection").get("status"));
            Obj wire=DriverJson.object(CampaignRootPublicCodec.encode(result).bytes(),RawJson.MAXIMUM_BYTES);
            assertEquals(new Text(MAX.toString()),wire.get("query_sequence"));assertEquals(new Text("1"),wire.get("snapshot_revision"));
            Obj binding=object(wire.get("binding"),"binding");assertInstanceOf(Text.class,binding.get("revision"));
            assertInstanceOf(Text.class,binding.get("native_revision"));assertInstanceOf(Text.class,binding.get("expected_revision"));
            assertInstanceOf(IntegerValue.class,binding.get("date_raw"));
            assertEquals(result.body(),CampaignRootPublicCodec.decode(new RawJson(DriverJson.encode(wire))).body());
            // Serialization domain only: changed public counters do not attest another physical frame.
            for(BigInteger revision:List.of(BigInteger.ZERO,BigInteger.ONE.shiftLeft(64),BigInteger.ONE.shiftLeft(100))) {
                var decimal=new Text(revision.toString());
                Obj changed=replace(wire,"queried_revision",decimal);
                changed=replace(changed,"binding",replace(replace(binding,"revision",decimal),"expected_revision",decimal));
                changed=replace(changed,"source",replace(object(wire.get("source"),"source"),"revision",decimal));
                var decoded=CampaignRootPublicCodec.decode(new RawJson(DriverJson.encode(changed)));
                assertEquals(new IntegerValue(revision),object(decoded.body().get("binding"),"binding").get("revision"));
                assertEquals(changed,DriverJson.object(CampaignRootPublicCodec.encode(decoded).bytes(),RawJson.MAXIMUM_BYTES));
                assertEquals(wire.get("snapshot_revision"),changed.get("snapshot_revision"));
                assertEquals(binding.get("native_revision"),object(changed.get("binding"),"binding").get("native_revision"));
            }
            assertInvalidResponse(without(wire,"readiness"));
            assertInvalidResponse(replace(wire,"query_sequence",new IntegerValue(MAX)));
            assertInvalidResponse(replace(wire,"query_sequence",new Text("018446744073709551615")));
            assertInvalidResponse(replace(wire,"campaign_root_context_ready",new Bool(false)));
            assertInvalidResponse(replace(wire,"binding",replace(binding,"expected_revision",new Text("999"))));
            assertInvalidResponse(replace(wire,"source",replace(object(wire.get("source"),"source"),"executable_sha256",new Text("0".repeat(64)))));
            assertInvalidResponse(replace(wire,"player_heir_fixed_dynasty_projection_v1",replace(object(wire.get("player_heir_fixed_dynasty_projection_v1"),"projection"),"positive_same_dynasty_legal_witness",new Bool(true))));
        }
    }

    @Test void publicRequestPreservesNonnegativePublicCounterAndRejectsAbsentNullWrongTypesAndNoncanonicalNumbers(){
        for(BigInteger value:List.of(BigInteger.ZERO,MAX,MAX.add(BigInteger.ONE),BigInteger.ONE.shiftLeft(100))) {
            var request=new CampaignRootPublicCodec.Request(value);
            assertEquals(request,CampaignRootPublicCodec.decodeRequest(new PublicBindings.Value(CampaignRootPublicCodec.encodeRequest(request))));
        }
        var maximum=new CampaignRootPublicCodec.Request(MAX);
        assertEquals(maximum,CampaignRootPublicCodec.decodeRequest(new PublicBindings.Value(CampaignRootPublicCodec.encodeRequest(maximum))));
        assertEquals(new CampaignRootPublicCodec.Request(BigInteger.ZERO),CampaignRootPublicCodec.decodeRequest(arguments("{\"expected_revision\":0}")));
        assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeRequest(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeRequest(new PublicBindings.Null()));
        for(String bad:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":1.0}",
                "{\"expected_revision\":9007199254740992}","{\"expected_revision\":\"01\"}","{\"expected_revision\":\"-1\"}",
                "{\"expected_revision\":\"+1\"}","{\"expected_revision\":\"0\",\"extra\":0}"))
            assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decodeRequest(arguments(bad)),bad);
    }
    @Test void exactOriginalServiceAcceptsZeroAndWideEqualPublicRevisionsBeforeNativeValidation() throws Exception {
        for(BigInteger revision:List.of(BigInteger.ZERO,BigInteger.ONE.shiftLeft(64),BigInteger.ONE.shiftLeft(100))) {
            var original=OriginalRootRevisionOracle.failure(revision,revision);
            assertEquals("BridgeUnavailableError",original.kind());
            assertEquals("campaign-root query lacks a positive native revision",original.message());
            var request=new CampaignRootPublicCodec.Request(revision);
            assertEquals(request,CampaignRootPublicCodec.decodeRequest(new PublicBindings.Value(CampaignRootPublicCodec.encodeRequest(request))));
        }
    }
    private static RawJson originalRoot(){
        try(var input=RootCampaignPublicProductsTest.class.getResourceAsStream("/org/xar/ck3/control/application/driver/campaign-root-native-v1-fixture.json")){
            assertNotNull(input,"reuse the sole driver_history ROOT original resource; do not manufacture another packet fixture");return new RawJson(input.readAllBytes());
        }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
    }
    private static PublicBindings.Value arguments(String json){return new PublicBindings.Value(new RawJson(json.getBytes(StandardCharsets.UTF_8)));}
    private static Obj replace(Obj source,String field,Value replacement){var values=new LinkedHashMap<String,Value>(source.members());values.put(field,replacement);return new Obj(values);}
    private static Obj without(Obj source,String field){var values=new LinkedHashMap<String,Value>(source.members());values.remove(field);return new Obj(values);}
    private static void assertInvalidResponse(Obj wire){assertThrows(IllegalArgumentException.class,()->CampaignRootPublicCodec.decode(new RawJson(DriverJson.encode(wire))));}
}
