package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import java.math.BigInteger;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Software DATA contract tests. These do not mint Root/source qualification or substitute for the actual central-read integration. */
final class ArmyPrivateScalarControlTest {
    @TempDir Path temporary;
    @Test void actualSnapshotHelloProducerInvalidatesOnIdentityDriftAndNeverArmsUseWithoutComparison()throws Exception {
        var held=new AtomicReference<>(frame(7,"fixture-episode",true));ArmyStrengthsService.Current current=held::get;
        var gate=new ArmyPrivateScalarControl(current,actual->proof());assertSame(current,gate.current());
        assertEquals(ArmyPrivateScalarControl.Mode.OFF,gate.query(BigInteger.valueOf(7)).mode());
        assertThrows(IllegalArgumentException.class,()->gate.set(ArmyPrivateScalarControl.Mode.USE,BigInteger.valueOf(7)));
        gate.set(ArmyPrivateScalarControl.Mode.COMPARE,BigInteger.valueOf(7));assertEquals(Optional.of(proof()),gate.qualification(held.get()));
        held.set(frame(8,"next-episode",true));assertEquals(ArmyPrivateScalarControl.Mode.OFF,gate.selectedMode(held.get()));
        assertFalse(gate.query(BigInteger.valueOf(7)).comparisonVerified());
        held.set(frame(7,"fixture-episode",false));assertThrows(IllegalArgumentException.class,()->gate.set(ArmyPrivateScalarControl.Mode.COMPARE,BigInteger.valueOf(7)));
        assertEquals(ArmyPrivateScalarControl.Mode.OFF,gate.set(ArmyPrivateScalarControl.Mode.OFF,BigInteger.valueOf(7)).mode());
        assertThrows(IllegalArgumentException.class,()->gate.query(BigInteger.ONE));
    }
    @Test void twoIndependentOriginalPacketsAreRequiredForCertificateAndMismatchDisablesIt()throws Exception {
        var frame=frame(7,"fixture-episode",true);var gate=new ArmyPrivateScalarControl(()->frame,actual->proof());gate.set(ArmyPrivateScalarControl.Mode.COMPARE,BigInteger.valueOf(7));
        var rich=reply(frame,ArmyStrengths.Mode.AUTO_CORE,"rich-original");var scalar=reply(frame,ArmyStrengths.Mode.PRIVATE_AUTO_SCALAR,"scalar-original");
        gate.markCompared(frame,rich,scalar);assertTrue(gate.query(BigInteger.valueOf(7)).comparisonVerified());
        assertEquals(ArmyPrivateScalarControl.Mode.USE,gate.set(ArmyPrivateScalarControl.Mode.USE,BigInteger.valueOf(7)).mode());
        var readback=ArmyJson.parse(ArmyTransportPublicCodec.scalar(gate.query(BigInteger.valueOf(7))).bytes());assertTrue(readback.get("source_revision").isTextual());assertEquals(0,readback.get("business_actions_submitted").intValue());
        gate.set(ArmyPrivateScalarControl.Mode.COMPARE,BigInteger.valueOf(7));
        assertThrows(IllegalArgumentException.class,()->gate.markCompared(frame,rich,rich));assertEquals(ArmyPrivateScalarControl.Mode.OFF,gate.query(BigInteger.valueOf(7)).mode());
    }
    @Test void missingProvenanceKeepsActualPrivateComparisonAndUseAvailable()throws Exception {
        var frame=frame(7,"fixture-episode",true);var calls=new java.util.concurrent.atomic.AtomicInteger();
        var gate=ArmyPrivateScalarControl.ordinary(()->frame,actual->{calls.incrementAndGet();return Optional.empty();});
        gate.set(ArmyPrivateScalarControl.Mode.COMPARE,BigInteger.valueOf(7));
        assertEquals(Optional.empty(),gate.qualification(frame));assertEquals(1,calls.get());
        var query=new ArmyStrengths.Query(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Mode.PRIVATE_AUTO_SCALAR,
                new Missing<>(),ArmyStrengths.EntryMode.OBSERVED_PREPARED,ArmyStrengths.EntryMode.OBSERVED_PREPARED);
        var selection=new ArmyStrengthsContracts.Selection(frame.snapshot(),query,frame.originalHello(),new Missing<>());
        var registry=new ArmyStrengthsFamilies.Registry();registry.freeze();var source=proof();
        var contracts=new ArmyStrengthsContracts(source,source,registry,new ArmyStrengthsPipeline(),List.of(source),Optional.empty(),source);
        var catalog=new RootReadContractCatalog(List.of(),contracts.families());
        assertDoesNotThrow(()->contracts.issue(catalog,selection));
        gate.markCompared(frame,reply(frame,ArmyStrengths.Mode.AUTO_CORE,"rich-empty-source"),reply(frame,ArmyStrengths.Mode.PRIVATE_AUTO_SCALAR,"scalar-empty-source"));
        assertEquals(ArmyPrivateScalarControl.Mode.USE,gate.set(ArmyPrivateScalarControl.Mode.USE,BigInteger.valueOf(7)).mode());
        assertEquals(Optional.empty(),gate.qualification(frame));assertEquals(2,calls.get());
    }
    private ExactRef proof()throws java.io.IOException {Path p=temporary.resolve("actual-controlled-source");if(!Files.exists(p))Files.writeString(p,"controlled source DATA, no Root qualification");byte[] b=Files.readAllBytes(p);return new ExactRef(p.toString(),b.length,ActionCodec.sha256(b));}
    private ArmyStrengthsService.CurrentFrame frame(int actor,String episode,boolean privateCap)throws Exception {
        var seed=ArmyStrengthsSourceTest.input(ArmyJson.empty(),ArmyStrengthsSourceTest.projectedHello());var old=seed.snapshot();var before=old.context().before();var f=before.frame();
        var actualFrame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),f.identity().nativeRevision(),f.identity().dateRaw()),f.snapshotId(),f.revision(),episode);
        var identity=new ProposalLifecycle.ObservationIdentity(before.machineId(),before.game(),actualFrame,1);var context=new Context(identity,old.context().source(),old.context().sessionId(),old.context().deadline());
        var raw=ArmyJson.parse(old.original().bytes());raw.put("episode_run_id",episode);ArmyJson.object(raw.get("played_character")).put("character_id",actor);
        var snapshot=ArmyStrengthsCodec.snapshot(context,new RawJson(ArmyJson.bytes(raw)));byte[] oldHello=seed.originalHello().orElseThrow().packet().value();var hello=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(oldHello,4,oldHello.length)));
        hello.withArray("capabilities").add(ArmyStrengths.CAPABILITY);if(privateCap)hello.withArray("capabilities").add(ArmyPrivateScalarControl.CAPABILITY);hello.put("game_build","exact-software-fixture");
        return new ArmyStrengthsService.CurrentFrame(snapshot,(NativeWire.Hello)NativeWire.decode(NativeWire.packet(ArmyJson.bytes(hello))));
    }
    private ArmyStrengthsService.Reply reply(ArmyStrengthsService.CurrentFrame frame,ArmyStrengths.Mode mode,String requestId)throws Exception {
        var snapshot=frame.snapshot();var context=snapshot.context();var query=new ArmyStrengths.Query(ArmyStrengths.Profile.ORDINARY_CORE_V1,mode,new Missing<>(),ArmyStrengths.EntryMode.OBSERVED_PREPARED,ArmyStrengths.EntryMode.OBSERVED_PREPARED);
        Field<ExactRef> qualification=mode==ArmyStrengths.Mode.PRIVATE_AUTO_SCALAR?new Present<>(proof()):new Missing<>();
        var selected=new ArmyStrengthsContracts.Selection(snapshot,query,frame.originalHello(),qualification);var op=new OperationKey(ArmyStrengths.STEP);
        var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),op,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),context.deadline());
        byte[] hello=frame.originalHello().packet().value();var cap=new ExactRef("software-original-hello",hello.length,ActionCodec.sha256(hello));
        var evidence=new GuardEvidence(context.before(),context.source(),context.sessionId(),snapshot.binding().connectionGeneration(),op,cap,cap,"controlled-only",context.deadline().minusSeconds(30),context.deadline());
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
        var token=ArmyJson.empty().put("step",ArmyStrengths.STEP).put("status","available").put("accepted",true);token.putArray("army_strengths");
        var packet=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",true);packet.set("result",token);
        var decoded=(NativeWire.CommandResult)NativeWire.decode(NativeWire.packet(ArmyJson.bytes(packet)));
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(decoded.result().token().orElseThrow().value())),new RawJson(decoded.payload().value()),decoded.packet().value());
        var receipt=new PlanningReadReceipt(request,"controlled-"+mode,requestId,guard,guard,ack);
        var read=new ArmyStrengths.Read(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Status.AVAILABLE,BigInteger.ONE,"controlled",List.of(),new Missing<>(),new Missing<>(),receipt);
        return new ArmyStrengthsService.Reply(selected,read,List.of(),ArmyStrengths.Status.AVAILABLE,ArmyStrengths.Status.AVAILABLE,new ArmyStrengthsPipeline.Results(List.of()));
    }
}
