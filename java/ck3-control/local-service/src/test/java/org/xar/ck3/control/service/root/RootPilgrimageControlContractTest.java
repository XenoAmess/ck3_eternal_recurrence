package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.*;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.Frame;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual controlled Native HELLO/frame -> same production command -> codec -> central selector contract. No Root is fabricated. */
final class RootPilgrimageControlContractTest {
    @TempDir Path directory;

    @Test void actualCommandProducerAndSerializationPreserveAllFourFiniteControlOperations()throws Exception {
        var source=new ActionWriterIntegrationFixture.SoftwareReadScenario(Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",ignored->List.of(),request->{throw new AssertionError("no optional native query belongs to this pure command test");},Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(directory.resolve("control-command"),false,source)){
            actual.ready();actual.writer.locked(same->actual.collector.currentOwned(same,actual.observationIdentity(),Instant.now().plusSeconds(20),lease->{
                var complete=lease.frame();var hello=assertInstanceOf(NativeWire.Hello.class,NativeWire.decode(Files.readAllBytes(Path.of(lease.originalHello().path()))));
                var frame=Frame.from(complete.identity(),complete.connectionGeneration(),hello);
                for(Operation operation:List.of(Operation.OPEN,Operation.CONFIRM,Operation.SELECT,Operation.START)){
                    var request=new ReligionPilgrimage.Request(operation,frame.publicRevision(),operation==Operation.SELECT||operation==Operation.START?new BigInteger("4294967294"):BigInteger.ZERO,0,Option.PIOUS,true,Reserves.zero(),BigDecimal.valueOf(30));
                    var command=RootReligionPilgrimage.controlCommand("controlled:"+operation.wire(),complete,frame,request,Instant.now().plusSeconds(10));
                    var restored=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,restored);
                    var parsed=RootReligionPilgrimage.controlContract(restored);assertEquals(operation,parsed.operation());assertEquals(frame.actor(),parsed.expectedActor());assertEquals(frame.date(),parsed.expectedDate());
                    assertEquals(Set.of("original-pilgrimage-process-ledger"),restored.claims().commitmentKeys());assertTrue(restored.claims().armyIds().isEmpty());assertTrue(restored.claims().allyCharacterIds().isEmpty());
                    var wrongSchema=new ExpectedPostcondition(1,restored.before(),restored.source(),"unrelated.control/v1",restored.expected().values());
                    assertThrows(IllegalArgumentException.class,()->RootReligionPilgrimage.controlContract(copy(restored,restored.arguments(),wrongSchema,restored.claims())));
                    var wrongFields=new ExpectedPostcondition(1,restored.before(),restored.source(),RootReligionPilgrimage.OBSERVER,List.of(new ExpectedText(new FieldKey("operation"),operation.wire()),new ExpectedBoolean(new FieldKey("native_control_observed"),false)));
                    assertThrows(IllegalArgumentException.class,()->RootReligionPilgrimage.controlContract(copy(restored,restored.arguments(),wrongFields,restored.claims())));
                    assertThrows(IllegalArgumentException.class,()->RootReligionPilgrimage.controlContract(copy(restored,restored.arguments(),restored.expected(),new Claims(Set.of(BigInteger.ONE),Set.of(),Set.of(frame.actor()),restored.claims().commitmentKeys()))));
                    var wrongActor=ReligionCodec.object(new RawJson(OpportunityJson.encode(restored.arguments()))).put("expected_actor_character_id",frame.actor().add(BigInteger.ONE));
                    var args=OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(wrongActor).bytes()),"tampered original actor");
                    assertThrows(IllegalArgumentException.class,()->RootReligionPilgrimage.controlContract(copy(restored,args,restored.expected(),restored.claims())));
                }
                assertEquals(0,actual.nativeActionWrites());assertEquals(0,actual.scenarioReadWrites());return null;
            }));
        }
    }
    private static ActionCommand copy(ActionCommand original,OpportunityJson.Obj args,ExpectedPostcondition expected,Claims claims){
        return new ActionCommand(original.actionId(),original.before(),original.source(),original.sessionId(),original.operation(),args,expected,claims,original.deadline());
    }
}
