package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Retained native producer -> installed decoder -> actual shared registration -> original public encoder.
 * Enclosing guards are synthetic protocol data. These tests cannot mint Context, Core or native qualification. */
final class RootGovernancePublicProductsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef REF=new ExactRef("synthetic-governance-products-only",1,"a".repeat(64));
    private static final String DEVELOP_SHA="94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
    private static final String COUNCIL_SHA="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final Set<PublicMethod> QUERIES=Set.of(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1,PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1);
    private static RawJson raw(String text) {return new RawJson(text.getBytes(StandardCharsets.UTF_8));}
    private static byte[] fixture(String path)throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository,"original fixture repository is required");
        return Files.readAllBytes(Path.of(repository,path));
    }
    private static PlanningRequest planning(boolean council) {
        var source=new G2Source("governance-products-fixture",NOW.toString(),council?"1.20.0.2":"1.20.0.3",REF);
        long actor=council?16777217:16777258,nativeRevision=council?7:77,publicRevision=council?8:177,date=council?53178264:53328600;
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(date)),
                        council?"native:council12002":"material-fixture:177",BigInteger.valueOf(publicRevision),"public-products-protocol-fixture"),1);
        return new PlanningRequest(identity,source,"protocol-only-session",NOW.plusSeconds(30),
                new PlanningObservation(new Obj(java.util.Map.of()).with("backend_id",new Text("native-headless")).with("snapshot_id",new Text(identity.frame().snapshotId())).with("revision",new IntegerValue(BigInteger.valueOf(publicRevision))).with("native_revision",new IntegerValue(BigInteger.valueOf(nativeRevision))).with("date_raw",new IntegerValue(BigInteger.valueOf(date))).with("paused",new Bool(true)).with("map_ready",new Bool(true)).with("episode_run_id",new Text(identity.frame().episodeRunId())).with("played_character",new Obj(java.util.Map.of()).with("character_id",new IntegerValue(BigInteger.valueOf(actor))).with("alive",new Bool(true))).with("active_wars",new Arr(List.of())).with("player_armies",new Arr(List.of())).with("active_event",Nil.INSTANCE).with("pending_character_interaction",Nil.INSTANCE),
                    List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static final class OriginalPort implements PlanningReadPort {
        private final byte[] bytes;private int reads;
        OriginalPort(byte[] bytes) {this.bytes=bytes.clone();}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            reads++;try {var full=StrictJson.parse(bytes);String id=full.get("request_id").textValue();
            var prepared=contract.prepare(request,id);assertEquals(request.operation().value(),prepared.step());
            var original=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),REF,REF,"protocol-data-not-native-authority",NOW,NOW.plusSeconds(30));
            var guard=new PlanningReadGuard(original,true,true,true,"b".repeat(64));
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(full.get("result")))),new RawJson(bytes),NativeWire.packet(bytes));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,REF);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
    private static GovernancePublicService service(PlanningRequest request,OriginalPort port) {
        var reads=new GovernanceNativeReads(REF,request.source().exactBuild(),request.source().exactBuild().equals("1.20.0.2")?COUNCIL_SHA:DEVELOP_SHA);
        ActionCoordinatorPort noAction=new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command){throw new AssertionError("read-only product cannot submit an action");}
            @Override public ActionReceipt reconcile(String id){throw new AssertionError("this fixture has no original action");}
        };
        return new GovernancePublicService(()->request,port,reads,noAction,Optional.empty());
    }
    private static PublicBindings registry(GovernancePublicService service) {
        var registry=new PublicBindings();
        var actual=RootGovernancePublicProducts.register(registry,service::query_council_composition_candidates_v1,service::query_steward_develop_county_candidates_v1,REF);
        assertEquals(2,actual.size());registry.freeze(QUERIES);return registry;
    }
    @Test void retainedDevelopmentMaterialPassesTypedRegistrationAndTheSharedPublicEncoder()throws Exception {
        byte[] bytes=fixture("ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json");
        var port=new OriginalPort(bytes);var registry=registry(service(planning(false),port));
        var binding=registry.lookup(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1).orElseThrow();
        var encoded=binding.invoke(PublicBindings.present(raw("{\"expected_revision\":177}")));sdkResult(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1,encoded);var decoded=StrictJson.parse(encoded.bytes());
        assertEquals("177",decoded.get("source").get("revision").textValue());assertEquals("77",decoded.get("source").get("native_revision").textValue());
        assertEquals("native-headless",decoded.get("source").get("backend_id").textValue());
        var publicPayload=decoded.get("steward_develop_county_candidates");assertEquals("77",publicPayload.get("snapshot_revision").textValue());
        assertEquals("8250",publicPayload.get("candidates").get(0).get("monthly_development_rate").get("raw").textValue());
        assertEquals(67108874,publicPayload.get("candidates").get(0).get("county_title_id").intValue());
        assertTrue(StrictJson.parse(bytes).get("result").get("steward_develop_county_candidates").get("snapshot_revision").isIntegralNumber());
        assertArrayEquals(StrictJson.canonical(decoded),encoded.bytes());assertEquals(1,port.reads);
        assertEquals(GovernancePublicService.DevelopmentRequest.class,binding.requestType());assertEquals(GovernancePublicService.DevelopmentReply.class,binding.resultType());
        assertTrue(registry.lookup(PublicMethod.CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1).isEmpty());
        assertFalse(QUERIES.contains(PublicMethod.CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1));
    }
    @Test void missingNullUnknownAndWrongNumericFieldsFailBeforeAnyDomainRead()throws Exception {
        var port=new OriginalPort(fixture("ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
        var registry=registry(service(planning(false),port));var development=registry.lookup(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->development.invoke(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->development.invoke(new PublicBindings.Null()));
        for(var fields:List.of("{}","{\"expected_revision\":true}","{\"expected_revision\":177.0}","{\"expected_revision\":null}","{\"expected_revision\":177,\"native_revision\":77}"))
            assertThrows(IllegalArgumentException.class,()->development.invoke(PublicBindings.present(raw(fields))));
        var council=registry.lookup(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->council.invoke(PublicBindings.present(raw("{\"expected_snapshot_id\":\"native:council12002\",\"public_revision\":8,\"native_revision\":true,\"date_raw\":53178264,\"owner_character_id\":16777217}"))));
        assertEquals(0,port.reads);
    }
    @Test void stalePublicRevisionDoesNotTurnTheNativeRevisionIntoPermission()throws Exception {
        var port=new OriginalPort(fixture("ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
        var registry=registry(service(planning(false),port));var binding=registry.lookup(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1).orElseThrow();
        for(var revision:List.of(77,176))assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw("{\"expected_revision\":"+revision+"}"))));
        assertEquals(0,port.reads);
    }
    @Test void actualDecoderRejectsChangedNativeEnvelopeAfterPublicArgumentDecoding()throws Exception {
        byte[] original=fixture("ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json");
        for(var name:List.of("snapshot_revision","accepted")) {
            var changed=(ObjectNode)StrictJson.parse(original);var result=(ObjectNode)changed.get("result");
            if(name.equals("snapshot_revision"))result.put(name,177);else result.put(name,false);
            var port=new OriginalPort(StrictJson.canonical(changed));var binding=registry(service(planning(false),port)).lookup(PublicMethod.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1).orElseThrow();
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw("{\"expected_revision\":177}"))));assertEquals(1,port.reads);
        }
        assertArrayEquals(original,fixture("ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json"));
    }
    @Test void unchangedHistoricalCouncilProducerPassesDistinctPublicAndNativeRevisionsAsData()throws Exception {
        byte[] original=fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json");
        var port=new OriginalPort(original);var binding=registry(service(planning(true),port)).lookup(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1).orElseThrow();
        // Actual C++ query envelope uses public revision 8; the payload independently retains native revision 7.
        // Historical DATA decode is not a current .4 source, Core or native qualification.
        var encoded=binding.invoke(PublicBindings.present(raw("{\"expected_snapshot_id\":\"native:council12002\",\"public_revision\":8,\"native_revision\":7,\"date_raw\":53178264,\"owner_character_id\":16777217}")));sdkResult(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1,encoded);var output=StrictJson.parse(encoded.bytes());
        assertEquals("8",output.get("queried_revision").textValue());assertEquals("7",output.get("queried_native_revision").textValue());
        var normalized=output.get("council_composition_candidates");var nativePayload=StrictJson.parse(original).get("result").get("council_composition_candidates");
        assertEquals(6,normalized.size());
        for(var field:org.xar.ck3.control.governance.council.CouncilCodec.PAYLOAD_FIELDS)if(field.equals("snapshot")) {
            assertEquals(nativePayload.get(field).get("public_revision").asText(),normalized.get(field).get("public_revision").textValue());
            assertEquals(nativePayload.get(field).get("native_revision").asText(),normalized.get(field).get("native_revision").textValue());
            assertEquals(nativePayload.get(field).get("date_raw"),normalized.get(field).get("date_raw"));
        }else assertEquals(nativePayload.get(field),normalized.get(field));
        assertEquals("xar.ck3.council-composition-candidates/v1",output.get("schema").textValue());
        assertEquals(1,port.reads);assertArrayEquals(original,fixture("ck3_autonomous_player/tests/fixtures/native_12002/governance/council-query.json"));
    }
    /** Same actual pinned SDK metadata as the complete public-catalog CI step; no reduced descriptor fallback. */
    private static void sdkResult(PublicMethod method,RawJson actualEncoded)throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals("ck3_"+method.pythonName())).findFirst().orElseThrow();
        var result=org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult.fromBusinessJson(actualEncoded);descriptor.validateResult(result);
        var envelope=StrictJson.parse(result.bytes());var business=StrictJson.parse(actualEncoded.bytes());
        assertEquals(business,envelope.get("structuredContent"));
        assertEquals(business,StrictJson.parse(envelope.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8)));
    }
}
