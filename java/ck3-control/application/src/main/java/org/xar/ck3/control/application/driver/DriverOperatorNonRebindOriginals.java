package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.LinkedHashSet;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Original operator rejection/zero-write DATA. Neither branch supplies a Driver replacement, Window, effect or Ready. */
public final class DriverOperatorNonRebindOriginals {
    private DriverOperatorNonRebindOriginals(){ }
    /** Pure classification of an already canonical snapshot. This does not validate archive membership or source authority. */
    public static boolean isRecordedNonRebound(ActionReceipt actual){
        Objects.requireNonNull(actual);
        if(!(actual.command().expectation() instanceof CommandExpectation.OperatorRebind))return false;
        if(actual.state() instanceof ActionState.RejectedBeforeDispatch zero)return zero.dispatch().proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                &&zero.dispatch().proof().requestBytesWritten()==0&&zero.attempt().requestId().equals(zero.dispatch().requestId());
        if(!(actual.state() instanceof ActionState.Settled settled)||!(settled.settlement() instanceof ActionState.Rejected rejected)
                ||!(settled.dispatch() instanceof NativeActionPort.AckReceived ack))return false;
        return OperatorPlayerSwitch.knownRejection(ack).filter(code->code.wire().equals(rejected.reason())).isPresent()
                &&ack.requestId().equals(settled.attempt().requestId())&&ack.requestId().equals(rejected.requestId());
    }
    /** The actual archive must replay its installed Root operator guard, complete prepared/outbound and native packet roles. */
    public static void requireCanonical(Session same,ActionReceipt actual,OutcomeArchive archive)throws IOException {
        StrictJson.require(!(actual.state() instanceof ActionState.RejectedBeforeDispatch),"operator zero dispatch needs its actual installed Root source verifier");
        requireCanonical(same,actual,archive,null);
    }
    /** Root's private coverage reader supplies its identical installed binding; a bare zero-write DTO is insufficient. */
    public static void requireCanonical(Session same,ActionReceipt actual,OutcomeArchive archive,
            org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.Binding identicalInstalled)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(archive);
        StrictJson.require(isRecordedNonRebound(actual),"only actual finite known operator rejection or proved zero dispatch is eligible");
        StrictJson.require(!(actual.state() instanceof ActionState.RejectedBeforeDispatch)||identicalInstalled!=null,"actual operator zero-dispatch domain verifier missing");
        var expected=((CommandExpectation.OperatorRebind)actual.command().expectation()).expected();expected.validateCommand(actual.command());
        String head=same.head().digest();var receipt=archive.receiptReferenceOf(actual);
        // NativeOutcomeArchive's mandatory operator branch replays the owning Root guard codec:
        // exact .6 executable/build/HELLO/source epoch, full original Driver/native/auxiliary,
        // qualified living or terminal origin and actual historical writer point. No app -> service import.
        StrictJson.require(archive.loadReceipt(receipt).equals(actual),"operator non-rebind lost its real source/prepared/outbound receipt originals");
        var record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
        StrictJson.require(archive.loadRecord(record).receipt().equals(actual),"operator non-rebind is not its actual canonical action record");
        if(identicalInstalled!=null){
            StrictJson.require(identicalInstalled.operation().equals(actual.command().operation()),"operator non-rebind borrowed another installed operation verifier");
            identicalInstalled.verifier().verify(same.head(),actual,archive);
        }
        var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();var request=attempt.preparedRequest();
        StrictJson.require(request.requiredCapability().filter(OperatorPlayerSwitch.CAPABILITY::equals).isPresent(),"operator non-rebind borrowed another native capability");
        NativeStepDiscriminator.requireRequest(actual.command().operation(),ExecutableStepBindings.Kind.ACTION,request);
        var prepared=archive.requestReferenceOf(request);StrictJson.require(archive.loadRequest(prepared).equals(request),"operator non-rebind changed its complete original preparation");
        var references=new LinkedHashSet<ExactRef>();references.add(receipt);references.add(record);references.add(prepared);
        var guard=attempt.guard();references.add(guard.source().sourceRef());references.add(guard.nativeEvidence());references.add(guard.capabilityEvidence());references.addAll(guard.supportingEvidence());
        if(actual.state() instanceof ActionState.Settled settled){
            var rejected=(ActionState.Rejected)settled.settlement();var ack=(NativeActionPort.AckReceived)settled.dispatch();
            var code=OperatorPlayerSwitch.knownRejection(ack).orElseThrow();
            StrictJson.require(code.wire().equals(rejected.reason())&&archive.referenceOf(ack).equals(rejected.originalEvidence())
                    &&archive.load(rejected.originalEvidence()).equals(ack)&&!ack.nativeOk()&&ack.outbound().isPresent(),"operator known rejection lost its exact original ACK/error evidence");
            ack.custody().orElseThrow(()->new IllegalArgumentException("operator rejection original chronology missing")).verify(ack,guard);
            references.add(rejected.originalEvidence());
        }else{
            var zero=(ActionState.RejectedBeforeDispatch)actual.state();
            StrictJson.require(zero.dispatch().proof().stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE
                    &&zero.dispatch().proof().requestBytesWritten()==0,"operator zero-dispatch proof has actual bytes written");
        }
        byte[] driver=archive.loadFullMaterial(expected.beforeDriver()).bytes();
        StrictJson.require(expected.beforeDriver().bytes()==driver.length&&expected.beforeDriver().sha256().equals(DriverJson.sha256(driver)),"operator original full Driver material differs");
        StrictJson.require(DriverStateSnapshot.decodeComplete(driver).session().episodeRunId().equals(expected.episodeRunId()),"operator non-rebind crossed its actual original episode");references.add(expected.beforeDriver());
        for(var ref:references){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        StrictJson.require(same.head().digest().equals(head),"operator non-rebind verification changed the original canonical head");
    }
}
