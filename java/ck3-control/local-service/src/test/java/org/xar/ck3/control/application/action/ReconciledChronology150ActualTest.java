package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual immutable ARM384/ACK plus explicitly software query custody. Grants no Root lease or business settlement. */
final class ReconciledChronology150ActualTest {
    private static final Path ROOT=Path.of(System.getProperty("xar.reconciliation150.fixtureDir", "reconciliation150")).toAbsolutePath();
    private static final String CONTRACT="java.tactical-daily-sentinel.status.reconciliation.v1";
    private static final UUID QUERY_EPOCH=UUID.fromString("3b7ddba1-6711-40bf-95ce-10f50e7f0150");
    private static final NativeArchiveDataCodec DATA=new NativeArchiveDataCodec((ref,max)->{assertTrue(ref.bytes()<=max);return fixture("artifacts/"+ref.sha256()+".bin");});
    private static final ActionPorts.OutcomeArchive ORIGINALS=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
        if(method.getName().equals("load"))return DATA.decodeDispatchData((ExactRef)args[0]);
        if(method.getName().equals("loadRequest"))return DATA.decodePreparedRequestData((ExactRef)args[0]);
        throw new AssertionError("no Native query/archive write: "+method.getName());
    });
    private record Input(ActionReceipt original,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,PlanningReadReceipt read) { }
    private Input input(int connectionDelta,boolean sameEpoch,long queryMillisAfterAck)throws Exception {
        var raw=fixture("ACTUAL384-CHILD.json");var original=ActionReceiptCodec.decodeReceipt(raw,ORIGINALS);
        assertEquals(384,original.sequence());assertInstanceOf(ActionState.Unknown.class,original.state());
        var attempt=ActionTransitions.attempt(original.state()).orElseThrow();var ack=original.ack().orElseThrow();assertTrue(ack.nativeOk());
        var old=ack.custody().orElseThrow();var command=original.command();var currentConnection=old.session().connectionGeneration().add(BigInteger.valueOf(connectionDelta));
        var basis=StrictJson.parse(fixture("artifacts/"+attempt.guard().supportingEvidence().getFirst().sha256()+".bin"),StrictJson.EXPLICIT_MAX_BYTES);
        var beforeDriver=ExactRef.fromJson(basis.get("original_driver"));
        var queryAt=old.responseReceived().observedAt().plusMillis(queryMillisAfterAck);
        var evidence=new ReconciliationIdentity.Evidence(attempt.guard().nativeEvidence(),connectionDelta==0?attempt.guard().capabilityEvidence():ref("software-new-hello"),
                ref("software-heartbeat"),ref("software-observation-manifest"),beforeDriver,Optional.empty());
        var originalRef=new ExactRef("D:/ck3-state/ck3-java-g2-resume85-vanilla02/continuity/artifacts/4460a6e00a217062401fff0f9dc20a25b945da4ea95154c4f8e42eecb15cc698.bin",raw.length,ActionCodec.sha256(raw));
        var identity=ReconciliationIdentity.fromCanonical(original,command.before(),command.source(),command.sessionId(),currentConnection,originalRef,beforeDriver,evidence,queryAt.minusSeconds(1));
        var session=new NativeObservationPort.TransportSession(command.origin().machineId(),command.origin().game(),currentConnection,command.sessionId());
        var requestId="software-reconciliation-status-150";
        var outbound=packet("{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"step\":\""+ClockStatusRead.STEP+"\",\"expected_revision\":"+command.before().frame().identity().nativeRevision()+"}");
        var frame="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"ok\":true,\"result\":{\"software_status_only\":true}}";
        var inbound=packet(frame);var first=sameEpoch?old.responseReceived().order().add(BigInteger.ONE):BigInteger.ONE;
        var custody=new NativeRequestChronology(session,sameEpoch?old.custodyEpoch():QUERY_EPOCH,requestId,NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(inbound),
                new NativeRequestChronology.Event(first,queryAt),new NativeRequestChronology.Event(first.add(BigInteger.ONE),queryAt.plusMillis(1)),new NativeRequestChronology.Event(first.add(BigInteger.TWO),queryAt.plusMillis(2)));
        var queryAck=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson("{\"software_status_only\":true}".getBytes(StandardCharsets.UTF_8))),new RawJson(frame.getBytes(StandardCharsets.UTF_8)),inbound,
                Optional.of(new NativeActionPort.OutboundPacket(requestId,outbound)),Optional.of(custody));
        return new Input(original,attempt,ack,read(identity,queryAck,CONTRACT));
    }
    private static PlanningReadReceipt read(ReconciliationIdentity identity,NativeActionPort.AckReceived ack,String contract){
        var at=ack.custody().orElseThrow().writeEntered().observedAt();
        var request=PlanningReadRequest.newReconciliation(identity,new OperationKey(ClockStatusRead.STEP),new Obj(Map.of()),at.plusSeconds(30));
        var binding=new GuardEvidence(request.origin(),identity.source(),identity.sessionId(),identity.connectionGeneration(),request.operation(),identity.nativeEvidence(),identity.capabilityEvidence(),
                "software-query-150-authority",at.minusSeconds(1),at.plusSeconds(60),identity.supportingEvidence());
        var guard=new PlanningReadGuard(binding,new PlanningReadGuard.Reconciliation(),identity.bindingSha256());
        return new PlanningReadReceipt(request,contract,ack.requestId(),guard,guard,ack);
    }
    private static void validate(Input value,PlanningReadReceipt read){NativeRequestChronology.requireReconciledSampledAfter(read,value.original().command(),value.attempt(),value.ack());}
    private static NativeActionPort.AckReceived with(NativeActionPort.AckReceived ack,NativeRequestChronology custody,byte[] response){return new NativeActionPort.AckReceived(ack.requestId(),true,ack.originalResultToken(),ack.originalFrame(),response,ack.outbound(),Optional.of(custody));}
    @Test void actual384AckCanBindOnlyTypedNewConnectionQueryWithoutComparingRestartedCounters()throws Exception {
        var value=input(1,false,3600000);validate(value,value.read());
        assertTrue(value.read().original().custody().orElseThrow().writeEntered().observedAt().isAfter(value.original().command().deadline()));
        assertTrue(value.read().original().custody().orElseThrow().writeEntered().order().compareTo(value.ack().custody().orElseThrow().responseReceived().order())<0);
        var control=new ActionState.ControlApplied(value.read(),AdvancePrimitives.CLOCK_OBSERVER,value.original().command().expected().values());
        ActionEffects.validate(value.original().command(),value.attempt(),value.ack(),control);
        assertFalse(value.original().settled());assertThrows(IllegalArgumentException.class,()->NativeRequestChronology.requireSampledAfter(value.read(),value.attempt(),value.ack()));
        System.out.println("PASS actual immutable UNKNOWN ARM384 + successful old ACK/conn64 -> software typed Status query/conn65/new epoch/localcounter1; chronology+ControlApplied validation only, no canonical settlement/query/action/day");
    }
    @Test void pendingBodyWrongGameStaleQueryWrongProfileAndPacketDriftReject()throws Exception {
        var value=input(1,false,10000);var identity=value.read().request().origin().requireReconciliation();var pending=identity.pending();
        var wrongIdentity=new ReconciliationIdentity(identity.factual(),identity.source(),identity.sessionId(),identity.connectionGeneration(),
                new ReconciliationIdentity.Pending(pending.actionId(),"0".repeat(64),pending.requestId(),pending.originalBefore(),pending.originalReceipt(),pending.originalBeforeDriver()),identity.evidence(),identity.observedAt());
        assertThrows(IllegalArgumentException.class,()->validate(value,read(wrongIdentity,value.read().original(),CONTRACT)));
        var ack=value.read().original();var actual=ack.custody().orElseThrow();
        var otherGame=new GameGeneration(actual.session().game().pid()+1,new PythonOnlyUInt64(actual.session().game().creationFiletime().value()));
        var wrongSession=new NativeObservationPort.TransportSession(actual.session().machineId(),otherGame,actual.session().connectionGeneration(),actual.session().sessionId());
        var crossed=new NativeRequestChronology(wrongSession,actual.custodyEpoch(),actual.requestId(),actual.originalRequest(),actual.originalResponse(),actual.writeEntered(),actual.writeCompleted(),actual.responseReceived());
        assertThrows(IllegalArgumentException.class,()->validate(value,read(identity,with(ack,crossed,ack.originalPacket()),CONTRACT)));
        var stale=input(1,false,-1000);assertThrows(IllegalArgumentException.class,()->validate(stale,stale.read()));
        assertThrows(IllegalArgumentException.class,()->validate(value,read(identity,ack,"software-wrong-profile")));
        byte[] changed=ack.originalPacket();changed[changed.length-1]^=1;
        assertThrows(IllegalArgumentException.class,()->validate(value,read(identity,with(ack,actual,changed),CONTRACT)));
    }
    @Test void sameConnectionCannotChangeEpochAndOrdinarySamplingStillUsesOriginalStrictRule()throws Exception {
        var wrong=input(0,false,10000);assertThrows(IllegalArgumentException.class,()->validate(wrong,wrong.read()));
        var same=input(0,true,10000);validate(same,same.read());
        NativeRequestChronology.requireSampledAfter(ordinary(same.read()),same.attempt(),same.ack());
        var reconnected=input(1,false,10000);var ordinary=ordinary(reconnected.read());
        assertThrows(IllegalArgumentException.class,()->NativeRequestChronology.requireSampledAfter(ordinary,reconnected.attempt(),reconnected.ack()));
        var control=new ActionState.ControlApplied(ordinary,AdvancePrimitives.CLOCK_OBSERVER,reconnected.original().command().expected().values());
        assertThrows(IllegalArgumentException.class,()->ActionEffects.validate(reconnected.original().command(),reconnected.attempt(),reconnected.ack(),control));
    }
    private static PlanningReadReceipt ordinary(PlanningReadReceipt read){
        var identity=read.request().origin().requireReconciliation();var old=read.before().binding();
        var request=new PlanningReadRequest(identity.factual(),read.request().source(),read.request().sessionId(),read.request().operation(),read.request().arguments(),read.request().deadline());
        var binding=new GuardEvidence(identity.factual(),old.source(),old.sessionId(),old.connectionGeneration(),old.operation(),old.nativeEvidence(),old.capabilityEvidence(),old.authorityId(),old.observedAt(),old.validUntil());
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));return new PlanningReadReceipt(request,ClockStatusRead.CONTRACT_ID,read.requestId(),guard,guard,read.original());
    }
    private static ExactRef ref(String value){byte[] bytes=value.getBytes(StandardCharsets.UTF_8);return new ExactRef(ROOT.resolve("software-only/"+value).toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static byte[] packet(String value){byte[] raw=value.getBytes(StandardCharsets.UTF_8);return ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();}
    private static byte[] fixture(String relative)throws java.io.IOException {
        try(var resource=ReconciledChronology150ActualTest.class.getResourceAsStream("/reconciliation150/"+relative)) {
            if(resource!=null)return resource.readAllBytes();
        }
        return Files.readAllBytes(ROOT.resolve(relative));
    }
}
