package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.time.Instant;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;

/** Portable resource-only unified planning-filter terminal matrix.
 * Original ExactRef paths remain immutable DATA and are never opened.
 * Resources are verified by their exact size/SHA; this is not file custody.
 * Unified real planning-filter terminal matrix. C1-C5 are actual canonical
 * original DATA, untouched. Every other row is explicitly counterfactual DATA
 * and is neither a native producer result, a Root capability nor a WAL event.
 * No ACK packet, original Frame, permission, query or world effect is invented.
 * This pure filter still requires installed archived/source verification first.
 */
final class TimelinePrimitiveTerminalPortableTest {
    private static final String CAS="D:\\ck3-state\\ck3-java-resume91_offline04_20261111T071454Z\\business\\continuity\\artifacts\\";
    private static final ExactRef ARM=artifact(7382,"f42a94b5be9efc2c19d4b01d237b02cda9b09f6527fb38aa03fc070537fd88a8");
    private static final ExactRef RESUME=artifact(7350,"24e7e34f8fa8b8ce52f2dd966ba5fb687caf368ea2ff97d5d74bf8a2fd1d9399");
    private static final ExactRef PAUSE=artifact(7879,"76945824decaaea3cf8c0393880c56faff97cf587089cc3508a347f0fb81a690");
    private static final ExactRef C4=artifact(2734,"8a3ccb1431262067daed5c9cbc7559ac4ad3c4bb653f2860825ee806adb9dfb5");
    private static final ExactRef C5=artifact(3146,"8e78ab2472a34651e10594aa54ca0af3543a68613d5cc6dea00ecab6be78fa63");
    private static final List<ExactRef> ORIGINALS=List.of(ARM,RESUME,PAUSE,C4,C5);
    private static final ExactRef U1=new ExactRef("unqualified-software-terminal-data:one",2,ActionCodec.sha256(new byte[]{123,125}));
    private static final ExactRef U2=new ExactRef("unqualified-software-terminal-data:two",2,ActionCodec.sha256(new byte[]{123,125}));
    private static final RootPlanningInputsFactory.SystemControl TIMELINE=new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.TIMELINE_PRIMITIVE);

    @Test void allFiveActualCanonicalTimelineTerminalsPassWithoutChangingAnyOriginalBodyOrCredit()throws Exception{
        var originals=new Originals();var receipts=new ArrayList<ActionReceipt>();for(var ref:ORIGINALS)receipts.add(originals.receipt(ref));
        assertInstanceOf(ActionState.ControlApplied.class,((ActionState.Settled)receipts.get(0).state()).settlement());
        assertInstanceOf(ActionState.Applied.class,((ActionState.Settled)receipts.get(1).state()).settlement());
        assertInstanceOf(ActionState.PauseConfirmed.class,((ActionState.Settled)receipts.get(2).state()).settlement());
        assertInstanceOf(ActionState.CleanupNoEffectConfirmed.class,receipts.get(3).state());assertInstanceOf(ActionState.PreparedCleanupNoEffectConfirmed.class,receipts.get(4).state());
        for(int i=0;i<receipts.size();i++){
            var actual=receipts.get(i);var before=originals.read(ORIGINALS.get(i),64*1024);
            assertEquals(AdvancePrimitives.expected(actual.command().before(),actual.command().source(),actual.command().operation(),actual.command().arguments()),actual.command().expected());
            RootPlanningInputsFactory.requireSettledControl(TIMELINE,actual,receipts);
            assertFalse(actual.eligibleAdvance());assertArrayEquals(before,ActionReceiptCodec.encodeReceipt(actual,originals.archive));
        }
        var pause=receipts.get(2);assertEquals("pause-map",pause.command().operation().value());assertEquals(AdvancePrimitives.TIMELINE_OBSERVER,pause.command().expected().observerSchema());
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,pause.outcome());assertTrue(pause.ack().orElseThrow().nativeOk());
        assertTrue(pause.applied().isEmpty());assertFalse(pause.visibleGameplay());
        for(var actual:receipts.subList(3,5)){assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,actual.outcome());assertTrue(actual.ack().isEmpty());assertTrue(actual.applied().isEmpty());assertFalse(actual.visibleGameplay());}
        assertEquals(0,originals.unexpectedCalls);
    }

    @Test void legacyRejectedShapesRemainStructuralDataOnlyAndNonAppliedCannotReuseItsBeforeFrame()throws Exception{
        var originals=new Originals();var arm=originals.receipt(ARM);var settled=(ActionState.Settled)arm.state();var command=softwareCommand(arm.command(),"software-legacy-terminal");
        var requestId=RequestIds.forCommand(command);var attempt=new ActionState.Attempt(requestId,settled.attempt().submittedAt(),settled.attempt().guard(),settled.attempt().preparedRequest());
        // Public zero-byte proof DATA is a counterfactual fixture. No real
        // NoDispatch or rejected Native packet is asserted or archived.
        var zero=new NativeActionPort.RejectedBeforeDispatch(requestId,new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"counterfactual source-before-write rejection",Optional.empty()));
        var rejectedBefore=new ActionReceipt(1,arm.sequence(),command,ActionCodec.bodySha256(command),new ActionState.RejectedBeforeDispatch(attempt,zero));
        assertDoesNotThrow(()->RootPlanningInputsFactory.requireSettledControl(TIMELINE,rejectedBefore,List.of(rejectedBefore)));
        assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,rejectedBefore.outcome());assertTrue(rejectedBefore.ack().isEmpty());assertFalse(rejectedBefore.eligibleAdvance());
        var unknown=new NativeActionPort.Unknown(requestId,"counterfactual unclassified dispatch; not evidence of zero writes",new byte[0],Optional.empty());
        var rejected=new ActionReceipt(1,arm.sequence(),command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,unknown,new ActionState.Rejected(requestId,"counterfactual rejection metadata",U1)));
        assertDoesNotThrow(()->RootPlanningInputsFactory.requireSettledControl(TIMELINE,rejected,List.of(rejected)));
        assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,rejected.outcome());assertTrue(rejected.ack().isEmpty());assertFalse(rejected.eligibleAdvance());
        // The actual primitive archived replay additionally requires pause-map
        // and an actual negative ACK for Rejected. This shape is not that proof.
        reject(()->receipt(arm,command,new ActionState.Settled(attempt,unknown,new ActionState.Rejected("software-wrong-RID","counterfactual mismatch",U1))));
        var read=((ActionState.ControlApplied)settled.settlement()).read();
        var invalid=new ActionTerminalObservation(ActionCodec.bodySha256(command),requestId,new ActionTerminalObservation.PrisonerTargetDead(BigInteger.ONE),
                command.before(),command.before(),command.source(),command.sessionId(),new ObservationProvenance.Query("software-distinct-query"),
                attempt.submittedAt(),U1,U2,read,read,List.of(U1));
        var nonApplied=receipt(arm,command,new ActionState.Settled(attempt,unknown,new ActionState.NonAppliedTerminal(invalid)));
        var rejection=assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,()->RootPlanningInputsFactory.requireSettledControl(TIMELINE,nonApplied,List.of(nonApplied)));
        assertEquals("terminal requires an independent actual later frame",rejection.getMessage());
        // A real accepted NonApplied producer would need its independent domain
        // collection/frame originals. None are fabricated from this ARM Status.
        assertEquals(0,originals.unexpectedCalls);
    }

    @Test void wrongRoleExpectationAndPauseWithoutItsPositiveAckCannotBorrowAnyTimelineTerminal()throws Exception{
        var originals=new Originals();var arm=originals.receipt(ARM);var pause=originals.receipt(PAUSE);var settled=(ActionState.Settled)pause.state();
        for(var ref:List.of(PAUSE,C4,C5)){
            var actual=originals.receipt(ref);var command=actual.command();
            reject(()->{
                var operation=new OperationKey("resume-map");var changed=new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),operation,command.arguments(),
                        AdvancePrimitives.expected(command.before(),command.source(),operation,command.arguments()),command.claims(),command.deadline());
                return receipt(actual,changed,actual.state());
            });
            reject(()->{var row=(ObjectNode)StrictJson.parse(ActionCodec.encodeCommand(command),64*1024);((ObjectNode)row.get("expected")).put("observer_schema","software-wrong-schema");return receipt(actual,ActionCodec.decodeCommand(StrictJson.canonical(row)),actual.state());});
            reject(()->receipt(actual,command,new ActionState.Unknown(Optional.empty(),Optional.empty(),"software-unresolved",List.of())));
            reject(()->receipt(actual,command,new ActionState.ReservedPreparedCleanupNoEffectConfirmed(U1,U2)));
            assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,()->new ActionReceipt(1,actual.sequence(),command,"0".repeat(64),actual.state()));
        }
        var originalAck=pause.ack().orElseThrow();var outbound=originalAck.outbound().orElseThrow().originalPacket();
        var absentAck=new NativeActionPort.Unknown(settled.attempt().requestId(),"counterfactual missing ACK preserves actual outbound bytes",outbound,Optional.empty());
        reject(()->receipt(pause,pause.command(),new ActionState.Settled(settled.attempt(),absentAck,settled.settlement())));
        var a=(ActionState.Settled)arm.state();var read=((ActionState.ControlApplied)a.settlement()).read();
        var basis=new NativeEffectEvidence.FrameBasis(U1,U2);var values=FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE,1,2,0);
        var family=new FamilySendObservation(FamilySendObservation.Profile.MARRIAGE,arm.command().actionId(),arm.bodySha256(),a.attempt().requestId(),U1,U2,basis,basis,
                arm.command().before(),arm.command().before(),arm.command().source(),arm.command().sessionId(),read,read,List.of(U1),0,0,values);
        reject(()->receipt(arm,arm.command(),new ActionState.Settled(a.attempt(),a.dispatch(),new ActionState.FamilySendConfirmed(family))));
        var owner=new FrontendWindowCaptureRequest.Owner("software-negative-owner","software-negative-session",1,"1","0".repeat(64),"1");
        var capture=new FrontendWindowCaptureRequest("software-physical-negative",Instant.EPOCH,Instant.EPOCH.plusSeconds(1),owner,U1,U2,List.of(U1,U2),
                new FrontendWindowCaptureRequest.Window("1",new FrontendWindowCaptureRequest.ScreenRect(0,0,2560,1440)),"1");
        var physical=new PhysicalActionState(new PreparedAction.WindowCaptureRequest(capture),a.attempt().submittedAt(),a.attempt().guard(),PhysicalActionState.Phase.NOT_POSTED,Optional.empty(),List.of(),"counterfactual foreign physical-plane terminal");
        reject(()->receipt(arm,arm.command(),physical));
        assertEquals(0,originals.unexpectedCalls);
    }

    private static ActionCommand softwareCommand(ActionCommand original,String id){return new ActionCommand(id,original.before(),original.source(),original.sessionId(),original.operation(),original.arguments(),original.expected(),original.claims(),original.deadline());}
    private static ActionReceipt receipt(ActionReceipt original,ActionCommand command,ActionState state){return new ActionReceipt(original.version(),original.sequence(),command,ActionCodec.bodySha256(command),state);}
    private static void reject(Supplier<ActionReceipt> fixture){ActionReceipt value;try{value=fixture.get();}catch(IllegalArgumentException strictDataConstructor){return;}
        assertThrows(RuntimeException.class,()->RootPlanningInputsFactory.requireSettledControl(TIMELINE,value,List.of(value)));}
    private static ExactRef artifact(long bytes,String sha){return new ExactRef(CAS+sha+".bin",bytes,sha);}
    static final class Originals {
        private static final int MAX_FILE=256*1024;
        final Map<ExactRef,byte[]> bytes=new HashMap<>();
        final Map<ActionReceipt,ExactRef> receiptRefs=new HashMap<>();
        final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();
        final Map<PlanningReadReceipt,ExactRef> readRefs=new HashMap<>();
        final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        final Map<NativeActionPort.DispatchOutcome,ExactRef> outcomeRefs=new HashMap<>();
        final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        final Map<ExactRef,NativeRequest> requests=new HashMap<>();
        final Map<NativeRequest,ExactRef> requestRefs=new java.util.IdentityHashMap<>();
        final NativeArchiveDataCodec codec=new NativeArchiveDataCodec(this::read);
        long retained;int unexpectedCalls;
        final ActionPorts.OutcomeArchive archive=ActionPorts.OutcomeArchive.class.cast(Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                    try {
                        return switch(method.getName()){
                            case "load"->outcome((ExactRef)args[0]);
                            case "referenceOf"->Optional.ofNullable(outcomeRefs.get((NativeActionPort.DispatchOutcome)args[0])).orElseThrow();
                            case "loadRequest"->request((ExactRef)args[0]);
                            case "requestReferenceOf"->Optional.ofNullable(requestRefs.get((NativeRequest)args[0]))
                                    .orElseThrow(()->new AssertionError("only the identical actually decoded original request has an archive reference"));
                            case "loadRead"->readReceipt((ExactRef)args[0]);
                            case "readReferenceOf"->Optional.ofNullable(readRefs.get((PlanningReadReceipt)args[0])).orElseThrow();
                            case "loadReceipt"->receipt((ExactRef)args[0]);
                            case "receiptReferenceOf"->Optional.ofNullable(receiptRefs.get((ActionReceipt)args[0])).orElseThrow();
                            case "loadMaterial"->new RawJson(read((ExactRef)args[0],MAX_FILE));
                            case "loadFullMaterial"->RawJson.fullMaterial(read((ExactRef)args[0],MAX_FILE));
                            case "loadNativeFrame","readOriginalPacket"->read((ExactRef)args[0],MAX_FILE);
                            default->{
                                if(method.isDefault())yield InvocationHandler.invokeDefault(proxy,method,args);
                                unexpectedCalls++;throw new AssertionError("no issuer, control or publication in DATA archive: "+method.getName());
                            }
                        };
                    }catch(IOException failure){throw new UncheckedIOException(failure);}
                }));
        ExactRef softwareUnknown(NativeActionPort.Unknown value){
            var ref=index(StrictJson.object().put("counterfactual_unknown_data",value.requestId()));
            outcomes.put(ref,value);outcomeRefs.put(value,ref);return ref;
        }
        NativeRequest request(ExactRef reference)throws IOException{
            var prior=requests.get(reference);if(prior!=null)return prior;
            // The strict production DATA codec independently checks the exact
            // metadata, additional-fields and retained preparation-evidence bytes/SHA.
            var actual=codec.decodePreparedRequestData(reference);
            requests.put(reference,actual);requestRefs.put(actual,reference);return actual;
        }
        NativeActionPort.DispatchOutcome outcome(ExactRef reference)throws IOException{
            var prior=outcomes.get(reference);if(prior!=null)return prior;
            var result=codec.decodeDispatchData(reference);outcomes.put(reference,result);outcomeRefs.put(result,reference);return result;
        }
        PlanningReadReceipt readReceipt(ExactRef reference)throws IOException{
            var prior=reads.get(reference);if(prior!=null)return prior;
            var result=codec.readData(reference).receipt();reads.put(reference,result);readRefs.put(result,reference);
            var dispatch=ExactRef.fromJson(json(reference).get("original_ref"));
            outcomes.put(dispatch,result.original());outcomeRefs.put(result.original(),dispatch);return result;
        }
        ActionReceipt receipt(ExactRef reference)throws IOException{
            var prior=receipts.get(reference);if(prior!=null)return prior;
            var result=ActionReceiptCodec.decodeReceipt(read(reference,StrictJson.EXPLICIT_MAX_BYTES),archive);
            receipts.put(reference,result);receiptRefs.put(result,reference);return result;
        }
        ObjectNode json(ExactRef reference)throws IOException{return (ObjectNode)StrictJson.parse(read(reference,64*1024),64*1024);}
        ObjectNode jsonUnchecked(ExactRef reference){try{return json(reference);}catch(IOException original){throw new UncheckedIOException(original);}}
        ExactRef index(JsonNode row){return indexBytes(StrictJson.canonical(row));}
        ExactRef indexBytes(byte[] original){
            if(original.length>64*1024)throw new IllegalArgumentException("unqualified DATA index exceeds finite size");
            var ref=new ExactRef("unqualified-test-data-index:"+DriverJson.sha256(original),original.length,DriverJson.sha256(original));
            if(!bytes.containsKey(ref)){bytes.put(ref,original.clone());retained+=original.length;}return ref;
        }
        byte[] read(ExactRef reference,int maximum)throws IOException{
            if(reference.bytes()<1||reference.bytes()>maximum||reference.bytes()>MAX_FILE)throw new IOException("finite named original required");
            var prior=bytes.get(reference);if(prior!=null)return prior.clone();
            if(bytes.size()>=128||retained+reference.bytes()>1024L*1024)throw new IOException("finite actual C81 DATA closure exceeded");
            byte[] original;
            InputStream input=TimelinePrimitiveTerminalPortableTest.class.getResourceAsStream("/org/xar/ck3/control/service/root/timeline-terminal-materials/"+reference.sha256()+".bin");
            if(input==null)throw new IOException("missing frozen portable DATA material: "+reference.sha256());
            try(input){original=input.readNBytes(Math.toIntExact(reference.bytes())+1);}
            if(original.length!=reference.bytes()||!DriverJson.sha256(original).equals(reference.sha256()))throw new IOException("named original DATA changed exact bytes/SHA");
            retained+=original.length;bytes.put(reference,original);return original.clone();
        }
    }

}
