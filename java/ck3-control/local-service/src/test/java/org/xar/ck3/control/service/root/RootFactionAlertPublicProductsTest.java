package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Retained original producer -> actual service/catalog -> shared Root registration -> decimal64/replay.
 * The outer C++ eight-field envelope and read guards are protocol DATA, never an actual Root lease or native capture. */
final class RootFactionAlertPublicProductsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static final String FIXTURE_SHA="41b30820281d4d58163826fb1c6aa7c5f487323737b37e8f4e60e9647e057837";
    private static final ExactRef DEF=new ExactRef("synthetic-faction-definition",1,"a".repeat(64));
    private static final ExactRef DEC=new ExactRef("synthetic-faction-decoder",1,"b".repeat(64));
    private static final ExactRef REF=new ExactRef("synthetic-faction-protocol-original",1,"c".repeat(64));
    private record Vector(ObjectNode result,Complete frame,Instant deadline) {
        RawJson token(){return new RawJson(StrictJson.canonical(result));}
    }
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static JsonNode parse(RawJson value){return StrictJson.parse(value.bytes(),1_000_000);}
    private static Vector vector(BigInteger nativeRevision)throws Exception {
        byte[] bytes;
        try(var input=RootFactionAlertPublicProductsTest.class.getResourceAsStream("/factionalerts/original-producer-golden.json")){
            assertNotNull(input,"NOT EXECUTED: selected local-service POM must route the one original wave2-finance factionalerts test resource");
            bytes=input.readAllBytes();
        }
        assertEquals(FIXTURE_SHA,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode root=StrictJson.parse(bytes,1_000_000),selected=null;
        for(JsonNode candidate:root.get("cases"))if(candidate.get("name").textValue().equals("exact-build-1.20.0.4"))selected=candidate;
        assertNotNull(selected);
        ObjectNode alert=(ObjectNode)root.get("bases").get(selected.get("base").textValue()).deepCopy();
        for(JsonNode operation:selected.get("operations")){
            String path=operation.get("path").textValue();int slash=path.lastIndexOf('/');
            ObjectNode parent=slash==0?alert:(ObjectNode)alert.at(path.substring(0,slash));
            if(operation.path("remove").asBoolean(false))parent.remove(path.substring(slash+1));
            else parent.set(path.substring(slash+1),operation.get("value").deepCopy());
        }
        alert.put("snapshot_revision",nativeRevision);
        ObjectNode result=StrictJson.object().put("step",FactionAlertReadService.STEP).put("accepted",true)
                .put("status",alert.get("status").textValue()).put("query_sequence",MAX).put("snapshot_revision",nativeRevision)
                .put("player_faction_alerts_ready",alert.at("/readiness/alert_ready").booleanValue()).put("backend_id","native-headless");
        result.set("player_faction_alerts",alert);
        var source=new G2Source("synthetic-faction-public-machine",NOW.toString(),"1.20.0.4",REF);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(alert.get("player_character_id").bigIntegerValue(),
                nativeRevision,alert.get("date_raw").bigIntegerValue()),"native:faction-public-protocol",BigInteger.valueOf(9),"synthetic-faction-public-episode");
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        ObjectNode snapshot=StrictJson.object().put("backend_id","native-headless");
        snapshot.set("active_wars",selected.get("active_wars").deepCopy());
        var complete=new Complete(before,source,"synthetic-faction-public-session",BigInteger.ONE,
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snapshot)),"protocol complete snapshot"),REF,NOW,"d".repeat(64));
        return new Vector(result,complete,NOW.plusSeconds(30));
    }
    private static final class OriginalPort implements PlanningReadPort {
        final Vector vector;int reads;boolean changePacket;PlanningReadReceipt last;
        OriginalPort(Vector vector){this.vector=vector;}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
            reads++;var prepared=contract.prepare(request,"faction-public-protocol-request");
            assertEquals(FactionAlertReadService.STEP,prepared.step());assertEquals(raw("{}"),prepared.additionalFields());
            var binding=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),
                    REF,REF,"protocol-only-no-Root-authority",NOW,vector.deadline());
            var guard=new PlanningReadGuard(binding,true,true,true,vector.frame().fullBindingSha256());
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1)
                    .put("request_id","faction-public-protocol-request").put("ok",true);
            envelope.set("result",vector.result().deepCopy());var original=new RawJson(StrictJson.canonical(envelope));
            byte[] packet;
            try{packet=NativeWire.packet(original.bytes());}
            catch(java.io.IOException failure){throw new AssertionError("controlled faction fixture packet construction failed",failure);}
            if(changePacket)packet[packet.length-1]^=1;
            var ack=new NativeActionPort.AckReceived("faction-public-protocol-request",true,Optional.of(vector.token()),original,packet);
            last=new PlanningReadReceipt(request,contract.contractId(),ack.requestId(),guard,guard,ack);
            return new PlanningReadResult.Known<>(contract.decode(last),last,REF);
        }
        @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,PlanningReadRequest request,
                PlanningReadPort.FailureEvidenceObserver observer) {
            assertNotNull(observer);return read(contract,request); // Successful protocol DATA only; no failed-attempt authority is minted.
        }
    }
    private static PublicBindings registry(Vector vector,OriginalPort port,Contracts contracts,RootReadContractCatalog catalog) {
        var registry=new PublicBindings();
        RootFactionAlertPublicProducts.register(registry,query->RootFactionAlertPublicProducts.queryCurrent(query,vector.frame(),vector.deadline(),port,catalog,contracts),REF);
        registry.freeze(Set.of(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1));return registry;
    }
    private static PublicBindings registry(Vector vector,OriginalPort port,Contracts contracts) {
        return registry(vector,port,contracts,new RootReadContractCatalog(List.of(),contracts.families()));
    }
    private static PublicBindings.BoundBinding binding(PublicBindings registry){
        return registry.lookup(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1).orElseThrow();
    }
    @Test void retainedCurrentProducerPassesActualRootRegistrationServiceAndDecimal64Replay()throws Exception {
        var vector=vector(MAX);var port=new OriginalPort(vector);var contracts=new Contracts(DEF,DEC);
        var catalog=new RootReadContractCatalog(List.of(),contracts.families());var registry=registry(vector,port,contracts,catalog);
        var binding=binding(registry);var encoded=binding.invoke(PublicBindings.present(raw("{\"expected_revision\":\"9\"}")));
        var selected=new Selection(new Query(BigInteger.valueOf(9)),RootFactionAlertPublicProducts.context(new Query(BigInteger.valueOf(9)),vector.frame(),vector.deadline()));
        var projection=FactionAlertReadService.decodePublic(selected,encoded);
        assertEquals(MAX,projection.querySequence());assertEquals(MAX.toString(),parse(encoded).get("snapshot_revision").textValue());
        assertEquals("9",parse(encoded).get("queried_revision").textValue());
        assertTrue(parse(vector.token()).get("query_sequence").isIntegralNumber());assertEquals(1,port.reads);
        var original=contracts.issue(catalog,selected).replay(port.last);
        assertEquals(original.frame(),projection.frame());assertFalse(original.exactDemandClockObserved());
        assertFalse(original.componentStrengthCachesObserved());assertArrayEquals(vector.token().bytes(),original.originalResult().bytes());
        assertEquals(Query.class,binding.requestType());assertEquals(Reply.class,binding.resultType());
        assertTrue(registry.lookup(PublicMethod.QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1).isEmpty());
    }
    @Test void wrongMissingNullAliasAndFloatingArgumentsFailBeforeAnyActualRead()throws Exception {
        var vector=vector(BigInteger.valueOf(41));var port=new OriginalPort(vector);var binding=binding(registry(vector,port,new Contracts(DEF,DEC)));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->binding.invoke(new PublicBindings.Null()));
        for(var input:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":true}","{\"expected_revision\":9.0}",
                "{\"expected_revision\":\"09\"}","{\"expected_revision\":9007199254740992}","{\"expected_revision\":9,\"native_revision\":41}"))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(input))),input);
        for(var revision:List.of(8,41)) {
            var failure=assertThrows(FactionAlertReadService.QueryFailure.class,()->binding.invoke(PublicBindings.present(raw("{\"expected_revision\":"+revision+"}"))));
            assertEquals(FactionAlertReadService.QueryFailureKind.BRIDGE_UNAVAILABLE,failure.kind());
            assertEquals("player faction alert revision mismatch: expected "+revision+", current 9",failure.getMessage());
            assertTrue(failure.originalCandidate().isEmpty());
        }
        assertEquals(0,port.reads);
    }
    @Test void sameSourceFieldsCannotSubstituteForTheIdenticalInstalledFinanceFamily()throws Exception {
        var vector=vector(BigInteger.valueOf(41));var port=new OriginalPort(vector);
        var original=new Contracts(DEF,DEC);var other=new Contracts(DEF,DEC);
        var registry=registry(vector,port,other,new RootReadContractCatalog(List.of(),original.families()));
        assertThrows(IllegalArgumentException.class,()->binding(registry).invoke(PublicBindings.present(raw("{\"expected_revision\":9}"))));
        assertEquals(0,port.reads);
        RootFactionAlertPublicProducts.requireDefinitions(original,DEF,DEC);
        assertThrows(IllegalArgumentException.class,()->RootFactionAlertPublicProducts.requireDefinitions(original,DEC,DEF));
    }
    @Test void currentNativeOuterFieldsAndPacketRemainStrictAfterPublicDecoding()throws Exception {
        for(var mutation:List.of("accepted","snapshot_revision","extra","packet")){
            var vector=vector(BigInteger.valueOf(41));
            switch(mutation){
                case "accepted"->vector.result().put("accepted",false);
                case "snapshot_revision"->vector.result().put("snapshot_revision",9);
                case "extra"->vector.result().put("exact_ultimatum_clock",true);
                default->{}
            }
            var port=new OriginalPort(vector);port.changePacket=mutation.equals("packet");
            var binding=binding(registry(vector,port,new Contracts(DEF,DEC)));
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw("{\"expected_revision\":9}"))),mutation);
            assertEquals(1,port.reads);
        }
    }
    @Test void sameFrameWarHandoffCannotUseAnEmptyOrMalformedCurrentSnapshot()throws Exception {
        var vector=vector(BigInteger.valueOf(41));var query=new Query(BigInteger.valueOf(9));
        for(var wars:List.of("[]","null","{}")){
            ObjectNode snapshot=StrictJson.object().put("backend_id","native-headless");snapshot.set("active_wars",parse(raw(wars)));
            var frame=vector.frame();var changed=new Complete(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),
                    OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snapshot)),"changed protocol snapshot"),frame.originalEvidence(),NOW,frame.fullBindingSha256());
            var port=new OriginalPort(vector);var owner=new Contracts(DEF,DEC);var catalog=new RootReadContractCatalog(List.of(),owner.families());
            assertThrows(IllegalArgumentException.class,()->RootFactionAlertPublicProducts.queryCurrent(query,changed,vector.deadline(),port,catalog,owner));
            assertEquals(wars.equals("[]")?1:0,port.reads);
        }
    }
    @Test void unavailableInstalledReadIsNotAReplyAndCannotBePubliclySerialized()throws Exception {
        var vector=vector(BigInteger.valueOf(41));var owner=new Contracts(DEF,DEC);int[] calls={0};
        PlanningReadPort unavailable=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){
                calls[0]++;return new PlanningReadResult.Unavailable<>("actual original faction read unavailable",Optional.empty());
            }
            @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,PlanningReadRequest request,
                    PlanningReadPort.FailureEvidenceObserver observer) {
                assertNotNull(observer);return read(contract,request); // Unqualified DATA keeps the original diagnostic, never a Native rejection class.
            }
        };
        var registry=new PublicBindings();RootFactionAlertPublicProducts.register(registry,
                query->RootFactionAlertPublicProducts.queryCurrent(query,vector.frame(),vector.deadline(),unavailable,
                        new RootReadContractCatalog(List.of(),owner.families()),owner),REF);
        registry.freeze(Set.of(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1));
        var failure=assertThrows(IllegalStateException.class,()->binding(registry).invoke(PublicBindings.present(raw("{\"expected_revision\":9}"))));
        assertTrue(failure.getMessage().contains("actual original faction read unavailable"));assertEquals(1,calls[0]);
    }
}
