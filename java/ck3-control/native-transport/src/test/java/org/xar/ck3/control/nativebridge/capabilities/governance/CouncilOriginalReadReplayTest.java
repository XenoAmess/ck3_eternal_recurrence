package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.governance.CouncilSelection;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Synthetic final-gates envelope around retained native candidate material; actual preparer/encoder/decoder/replay. No live qualification. */
final class CouncilOriginalReadReplayTest {
    private static final Instant T=Instant.parse("2026-10-23T22:35:00Z");
    private static final String SHA="AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
    private static final ExactRef REF=new ExactRef("software-original-group-no-native-qualification",1,"a".repeat(64));
    private static final UUID EPOCH=UUID.fromString("e08f634f-e4d0-4ab9-b319-a37f37922893");
    private record Scene(NativeCouncilReadPort.ReplayConfiguration configuration,PlanningReadReceipt gates,PlanningReadReceipt terminal) { }
    private static ObjectNode fixture(String name)throws Exception {
        String repository=System.getProperty("xar.repository.root");assertNotNull(repository);
        return (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(repository,"ck3_autonomous_player/tests/fixtures/native_12002/governance/"+name+".json")));
    }
    private static PlanningReadRequest request(ReadContract<?> contract,Obj arguments) {
        var source=new G2Source("xenoamess-full-tower-eb9d2c1186",T.toString(),"1.20.0.2",REF);
        var before=new ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(16777217),BigInteger.valueOf(13),BigInteger.valueOf(53175816)),"public:900",BigInteger.valueOf(900),"software-original-read-episode"),1);
        return new PlanningReadRequest(before,source,"software-original-read-session",contract.operation(),arguments,T.plusSeconds(30));
    }
    private static PlanningReadReceipt read(ReadContract<?> contract,PlanningReadRequest request,String id,ObjectNode result,long order,Optional<BigInteger> wrongStatusOrRevision)throws Exception {
        NativeRequest prepared=contract.prepare(request,id);
        byte[] outbound=contract.wireProfile()==ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS&&wrongStatusOrRevision.isEmpty()
                ?NativeWire.executeCouncilMailboxStatus(id,prepared.step(),prepared.additionalFields().bytes())
                :NativeWire.execute(id,prepared.step(),wrongStatusOrRevision.orElse(request.before().frame().identity().nativeRevision()),prepared.additionalFields().bytes());
        var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",result);
        byte[] body=StrictJson.canonical(frame),incoming=NativeWire.packet(body);
        var guard=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,contract.operation(),REF,REF,"software-order-only",T,T.plusSeconds(30));
        var custody=new NativeRequestChronology(new NativeObservationPort.TransportSession(request.before().machineId(),request.before().game(),BigInteger.ONE,request.sessionId()),EPOCH,id,
                NativeRequestChronology.PacketIdentity.of(outbound),NativeRequestChronology.PacketIdentity.of(incoming),
                new NativeRequestChronology.Event(BigInteger.valueOf(order),T.plusMillis(order)),new NativeRequestChronology.Event(BigInteger.valueOf(order+1),T.plusMillis(order+1)),
                new NativeRequestChronology.Event(BigInteger.valueOf(order+2),T.plusMillis(order+2)));
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(body),incoming,
                Optional.of(new NativeActionPort.OutboundPacket(id,outbound)),Optional.of(custody));
        var readGuard=new PlanningReadGuard(guard,true,true,true,"b".repeat(64));
        return new PlanningReadReceipt(request,contract.contractId(),id,readGuard,readGuard,ack);
    }
    private static Scene scene()throws Exception {
        var definitions=new PrivateCouncilReads(REF);var configuration=new NativeCouncilReadPort.ReplayConfiguration(definitions,4,"1.20.0.2",SHA);
        var initial=request(definitions.gates(),new Obj(java.util.Map.of()).with("position_key",new Text("councillor_steward")));
        var status=request(definitions.status(),new Obj(java.util.Map.of()));
        var pending=StrictJson.object().put("private_council_transport",true).put("advertised",false).put("step",CouncilPrivateCodec.GATES).put("status","pending");
        var available=(ObjectNode)fixture("council-private-query-available").get("result");
        var finalGates=((ObjectNode)fixture("council-gates").get("result").get("council_final_gates")).deepCopy();
        finalGates.set("council_composition_candidates",available.get("council_composition_candidates"));
        var terminal=available.deepCopy().put("step",CouncilPrivateCodec.GATES);terminal.remove("council_composition_candidates");terminal.set("council_final_gates",finalGates);
        return new Scene(configuration,read(definitions.gates(),initial,"real-software-gates",pending,1,Optional.empty()),
                read(definitions.status(),status,"real-software-status",terminal,4,Optional.empty()));
    }
    private static CouncilSelection.Query replay(Scene scene,List<PlanningReadReceipt> reads) {
        return NativeCouncilReadPort.replayPrivateOriginals(reads,CouncilSelection.Position.STEWARD,scene.configuration());
    }
    @Test void actualGateProducerAndStatusWireFeedTheSamePureRootPendingReplay()throws Exception {
        var scene=scene();var actual=replay(scene,List.of(scene.gates(),scene.terminal()));
        var choice=CouncilSelection.choose(actual);assertEquals(CouncilSelection.Outcome.REPLACE_REQUIRED,choice.outcome());
        assertEquals(16777232,choice.selected().orElseThrow().characterId().intValueExact());
        var original=scene.terminal();var ack=original.original();
        var restored=NativeRequestChronologyCodec.decode(StrictJson.parse(StrictJson.canonical(NativeRequestChronologyCodec.encode(ack.custody().orElseThrow()))));
        var coldAck=new NativeActionPort.AckReceived(ack.requestId(),true,ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),ack.outbound(),Optional.of(restored));
        var cold=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),coldAck);
        assertEquals(actual,replay(scene,List.of(scene.gates(),cold)));
    }
    @Test void coldReplayRefusesCrossEpochMissingCustodyAndOutOfOrderOriginalGroups()throws Exception {
        var scene=scene();assertThrows(IllegalArgumentException.class,()->replay(scene,List.of(scene.terminal(),scene.gates())));
        assertThrows(IllegalArgumentException.class,()->replay(scene,List.of(scene.gates(),scene.gates())));
        var original=scene.terminal();var ack=original.original();
        var stripped=new NativeActionPort.AckReceived(ack.requestId(),true,ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),ack.outbound());
        var missing=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),stripped);
        assertThrows(IllegalArgumentException.class,()->replay(scene,List.of(scene.gates(),missing)));
        var row=NativeRequestChronologyCodec.encode(ack.custody().orElseThrow()).put("custody_epoch","f5413ed5-eac4-42f2-8536-4bfe56c5676c");
        var crossed=new NativeActionPort.AckReceived(ack.requestId(),true,ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),ack.outbound(),Optional.of(NativeRequestChronologyCodec.decode(row)));
        var otherEpoch=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),crossed);
        assertThrows(IllegalArgumentException.class,()->replay(scene,List.of(scene.gates(),otherEpoch)));
    }
    @Test void originalDecoderRejectsWrongNativeRevisionAndAnInjectedStatusRevision()throws Exception {
        var scene=scene();var definitions=scene.configuration().definitions();
        var pending=(ObjectNode)StrictJson.parse(scene.gates().original().originalResultToken().orElseThrow().bytes());
        var changed=read(definitions.gates(),scene.gates().request(),scene.gates().requestId(),pending,1,Optional.of(BigInteger.valueOf(14)));
        assertThrows(IllegalArgumentException.class,()->definitions.gates().decode(changed));
        var terminal=(ObjectNode)StrictJson.parse(scene.terminal().original().originalResultToken().orElseThrow().bytes());
        var statusWithRevision=read(definitions.status(),scene.terminal().request(),scene.terminal().requestId(),terminal,4,Optional.of(BigInteger.valueOf(13)));
        assertThrows(IllegalArgumentException.class,()->definitions.status().decode(statusWithRevision));
    }
}
