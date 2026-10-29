package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.lang.ref.WeakReference;
import java.util.Arrays;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.WeakHashMap;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Three exact read-only profiles over the same installed native Clock Status decoder.
 * Factory issuance is installation DATA, never a Root lease, pending membership, Ready or action permit.
 * The ordinary ClockStatusRead contract and its living/paused Observation remain unchanged. */
public final class RootUnknownSentinelReadProfile {
    public static final String CONTRACT_ID="java.tactical-daily-sentinel.status.reconciliation.v1";
    public static final String TERMINAL_CONTRACT_ID="java.tactical-daily-sentinel.status.terminal-observation.v1";
    public static final String PHYSICAL_CONTRACT_ID=PhysicalStatusIdentity.CONTRACT_ID;
    public static final String PERMISSION=PhysicalStatusIdentity.PERMISSION;
    private RootUnknownSentinelReadProfile(){ }
    private enum Scope {
        RECONCILIATION(CONTRACT_ID,ReadContract.GuardMode.RECONCILIATION_OBSERVATION),
        TERMINAL(TERMINAL_CONTRACT_ID,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION),
        PHYSICAL(PHYSICAL_CONTRACT_ID,ReadContract.GuardMode.STATUS_ONLY);
        final String id;final ReadContract.GuardMode guard;
        Scope(String id,ReadContract.GuardMode guard){this.id=id;this.guard=guard;}
    }
    private record Profiles(ReadContract<Status> reconciliation,ReadContract<Status> terminal,ReadContract<Status> physical){ }
    private record Issued(WeakReference<ReadContract<Status>> ordinary,Scope scope){ }
    private static final Object LOCK=new Object();
    private static final Map<ReadContract<Status>,Profiles> BY_CLOCK=new WeakHashMap<>();
    private static final Map<ReadContract<?>,Issued> ISSUED=new WeakHashMap<>();

    /** Same object for the exact ordinary Clock source-factory object. Prepared may register before
     * constructing ClockStatusRead; installation later binds the same object with requireInstalled. */
    public static ReadContract<Status> registeredContract(ClockStatusRead sameInstalled){return registeredContract(Objects.requireNonNull(sameInstalled).contract());}
    public static ReadContract<Status> registeredContract(ReadContract<Status> sameFactoryIssued){return contracts(sameFactoryIssued).reconciliation();}
    public static ReadContract<Status> registeredTerminalContract(ClockStatusRead sameInstalled){return registeredTerminalContract(Objects.requireNonNull(sameInstalled).contract());}
    public static ReadContract<Status> registeredTerminalContract(ReadContract<Status> sameFactoryIssued){return contracts(sameFactoryIssued).terminal();}
    public static ReadContract<Status> registeredPhysicalContract(ClockStatusRead sameInstalled){return registeredPhysicalContract(Objects.requireNonNull(sameInstalled).contract());}
    public static ReadContract<Status> registeredPhysicalContract(ReadContract<Status> sameFactoryIssued){return contracts(sameFactoryIssued).physical();}
    private static Profiles contracts(ReadContract<Status> clock) {
        Objects.requireNonNull(clock);requireOrdinary(clock);
        synchronized(LOCK) {
            Profiles prior=BY_CLOCK.get(clock);if(prior!=null)return prior;
            ReadContract<Status> reconciliation=make(clock,Scope.RECONCILIATION),terminal=make(clock,Scope.TERMINAL),physical=make(clock,Scope.PHYSICAL);
            Profiles actual=new Profiles(reconciliation,terminal,physical);BY_CLOCK.put(clock,actual);
            ISSUED.put(reconciliation,new Issued(new WeakReference<>(clock),Scope.RECONCILIATION));
            ISSUED.put(terminal,new Issued(new WeakReference<>(clock),Scope.TERMINAL));
            ISSUED.put(physical,new Issued(new WeakReference<>(clock),Scope.PHYSICAL));return actual;
        }
    }
    private static ReadContract<Status> make(ReadContract<Status> ordinary,Scope scope) {
        return new ReadContract<>(scope.id,new OperationKey(ClockStatusRead.STEP),Optional.of(ClockStatusRead.STATUS_CAP),
                PERMISSION,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                scope.guard,ordinary.sourceRef(),(request,requestId)->{
                    requireQuery(request,scope);
                    if(scope==Scope.RECONCILIATION)require(!requestId.equals(request.origin().requireReconciliation().pending().requestId()),"Status cannot replay the original unresolved request identity");
                    return new NativeRequest(ClockStatusRead.STEP,ClockStatusRead.STATUS_CAP,new RawJson(new byte[]{'{','}'}));
                },receipt->decode(receipt,scope),receipt->decode(receipt,scope));
    }
    private static void requireOrdinary(ReadContract<Status> actual) {
        ClockStatusRead.requireRegisteredContract(actual);
        require(ClockStatusRead.STEP.equals(PhysicalStatusIdentity.OPERATION)&&ClockStatusRead.STATUS_CAP.equals(PhysicalStatusIdentity.CAPABILITY),
                "physical Status profile changed the one native Clock operation/capability");
        require(actual.contractId().equals(ClockStatusRead.CONTRACT_ID)&&actual.operation().value().equals(ClockStatusRead.STEP)
                &&actual.requiredCapability().equals(Optional.of(ClockStatusRead.STATUS_CAP))&&actual.permissionKey().equals(PERMISSION)
                &&actual.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&actual.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&actual.hasPureReplay()
                &&actual.sourceRef().bytes()>0,"the actual installed ordinary Clock Status source/decoder differs");
    }
    public static void requireProfile(ReadContract<?> actual){requireIssued(actual,Scope.RECONCILIATION);}
    public static void requireTerminalProfile(ReadContract<?> actual){requireIssued(actual,Scope.TERMINAL);}
    public static void requirePhysicalProfile(ReadContract<?> actual){requireIssued(actual,Scope.PHYSICAL);}
    public static void requireInstalled(ReadContract<?> actual,ClockStatusRead sameInstalled) {
        Objects.requireNonNull(sameInstalled);synchronized(LOCK){Issued issued=ISSUED.get(actual);
            require(issued!=null&&issued.ordinary().get()==sameInstalled.contract(),
                    "Status profile is not derived from this same actual Clock installation");requireIssued(actual,issued.scope());}
    }
    private static void requireIssued(ReadContract<?> actual,Scope scope) {
        Objects.requireNonNull(actual);synchronized(LOCK){Issued issued=ISSUED.get(actual);
            require(issued!=null&&issued.scope()==scope&&issued.ordinary().get()!=null,"copied or foreign Status profile has no installed factory identity");
            requireOrdinary(issued.ordinary().get());
            if(scope==Scope.PHYSICAL)PhysicalStatusIdentity.requireProfile(actual);
            require(actual.contractId().equals(scope.id)&&actual.operation().value().equals(ClockStatusRead.STEP)
                    &&actual.requiredCapability().equals(Optional.of(ClockStatusRead.STATUS_CAP))&&actual.permissionKey().equals(PERMISSION)
                    &&actual.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                    &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&actual.guardMode()==scope.guard
                    &&actual.hasPureReplay()&&actual.sourceRef().equals(issued.ordinary().get().sourceRef()),"exact pure Status profile/source/decoder differs");}
    }
    private static void requireQuery(PlanningReadRequest request,Scope scope) {
        Objects.requireNonNull(request);require(request.operation().value().equals(ClockStatusRead.STEP)&&request.arguments().members().isEmpty(),
                "fixed native Status query has no caller-provided fields");
        require(switch(scope){
            case RECONCILIATION->request.origin() instanceof CommandOrigin.Reconciliation;
            case TERMINAL->request.origin() instanceof CommandOrigin.LifecycleTerminal;
            case PHYSICAL->request.origin() instanceof CommandOrigin.PhysicalStatusOnly;
        },"Status read cannot borrow another origin phase");
    }

    /** Pure current/historical binder. Root separately proves its actual canonical chain and held physical source.
     * This never looks up today's settled receipt as a replacement for the retained original UNKNOWN/ACK. */
    public static void requireRequest(PlanningReadRequest request,ActionReceipt original,ActionState.Attempt attempt,
            Complete before,Complete actual,ActionPorts.OutcomeArchive originals)throws IOException {
        requireQuery(request,Scope.RECONCILIATION);Objects.requireNonNull(original);Objects.requireNonNull(attempt);
        require(!original.settled()&&(original.state() instanceof ActionState.Unknown||original.state() instanceof ActionState.AckReceived),
                "Status reconciliation requires an actual unresolved dispatched primitive");
        var identity=request.origin().requireReconciliation();var pending=identity.pending();var command=original.command();
        require(command.origin() instanceof CommandOrigin.Gameplay&&original.bodySha256().equals(ActionCodec.bodySha256(command))
                &&command.actionId().equals(pending.actionId())&&original.bodySha256().equals(pending.bodySha256())
                &&command.before().equals(pending.originalBefore())&&attempt.requestId().equals(pending.requestId())
                &&ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent()
                &&before.identity().equals(command.before())&&actual.identity().equals(identity.factual())
                &&command.source().equals(actual.source())&&command.sessionId().equals(actual.sessionId())
                &&request.source().equals(actual.source())&&request.sessionId().equals(actual.sessionId())
                &&actual.connectionGeneration().equals(identity.connectionGeneration())
                &&actual.connectionGeneration().equals(attempt.guard().connectionGeneration()),
                "Status read changed its actual canonical pending/Attempt/source/Game/session/connection");
        require(originals instanceof NativeOutcomeArchive,"Status reconciliation requires actual same-writer archive custody");
        var bound=(NativeOutcomeArchive)originals;var same=bound.writer().borrowedSession();
        var retained=bound.loadReceipt(pending.originalReceipt());
        require(bound.receiptReferenceOf(original).equals(pending.originalReceipt())
                &&Arrays.equals(ActionReceiptCodec.encodeReceipt(original,bound),ActionReceiptCodec.encodeReceipt(retained,bound)),
                "Status pending original is not the complete retained canonical receipt");
        // Historical membership is checked on the genuine retained chain; no current-head pending permission is minted here.
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),original,bound);
        RootGuardEvidence.requireHistory(attempt.guard(),bound,same);
        var prepared=attempt.preparedRequest();var preparedRef=bound.requestReferenceOf(prepared);
        require(prepared.equals(bound.loadRequest(preparedRef)),"Status source changed the archived prepared original");
        var dispatch=ActionTransitions.dispatch(original.state()).orElseThrow();
        require(dispatch instanceof NativeActionPort.AckReceived||dispatch instanceof NativeActionPort.Unknown,"unresolved original is not an actual dispatched ACK/UNKNOWN");
        byte[] packet=dispatch instanceof NativeActionPort.AckReceived ack?ack.outbound().orElseThrow().originalPacket():
                ((NativeActionPort.Unknown)dispatch).originalRequestPacket();
        require(packet.length>0,"unresolved original has no genuine outbound request");var sent=NativeWire.decodeExecuteRequest(packet);
        require(sent.requestId().equals(attempt.requestId())&&sent.step().equals(prepared.step()),"Status source changed original outbound identity/step");
        // Outbound normalization is owned by NativeWire. Comparing its parsed DATA on both sides
        // preserves that exact wire domain without treating a decimal token as an identity role.
        var additions=NativeWire.object(NativeWire.parse(prepared.additionalFields().bytes()));
        if(additions.has("expected_snapshot_revision")) {
            require(NativeWire.integer(additions.remove("expected_snapshot_revision"),java.math.BigInteger.ZERO,
                    org.xar.ck3.control.contracts.StrictJson.UINT64_MAX).equals(attempt.guard().origin().expectedRevision())
                    &&sent.expectedSnapshotRevision().isPresent(),"original snapshot-revision wire changed");
        }
        require(NativeWire.object(NativeWire.parse(sent.normalizedAdditionalFields().value())).equals(additions)
                &&(sent.expectedRevision().isPresent()||sent.expectedSnapshotRevision().isPresent())
                &&sent.expectedRevision().map(attempt.guard().origin().expectedRevision()::equals).orElse(true)
                &&sent.expectedSnapshotRevision().map(attempt.guard().origin().expectedRevision()::equals).orElse(true),
                "actual original outbound differs from the durable prepared fields/native revision");
    }
    private static Status decode(PlanningReadReceipt receipt,Scope scope) {
        Objects.requireNonNull(receipt);requireQuery(receipt.request(),scope);
        require(receipt.contractId().equals(scope.id)&&receipt.before().guardMode()==scope.guard&&receipt.after().guardMode()==scope.guard,
                "Status original receipt crossed its exact profile");
        if(scope==Scope.RECONCILIATION)require(!receipt.requestId().equals(receipt.request().origin().requireReconciliation().pending().requestId()),
                "Status is an independent query, never an original action replay");
        receipt.original().custody().orElseThrow(()->new IllegalArgumentException("actual Status query chronology is absent")).verify(receipt);
        return ClockStatusRead.decode(receipt.original());
    }
    /** Retained typed DATA, not a Gameplay ClockStatusRead.Observation or permission to submit.
     * The actual owner must separately resolve originalEvidence through its same-writer archive. */
    public record ReconObservation(Status status,PlanningReadReceipt receipt,ExactRef originalEvidence) {
        public ReconObservation{Objects.requireNonNull(status);Objects.requireNonNull(originalEvidence);require(originalEvidence.bytes()>0&&status.equals(decode(receipt,Scope.RECONCILIATION)),"actual reconciliation Status/value/original custody differs");}
    }
    public record PhysicalObservation(Status status,PlanningReadReceipt receipt,ExactRef originalEvidence) {
        public PhysicalObservation{Objects.requireNonNull(status);Objects.requireNonNull(originalEvidence);require(originalEvidence.bytes()>0&&status.equals(decode(receipt,Scope.PHYSICAL)),"actual physical Status/value/original custody differs");}
    }
    public record TerminalObservation(Status status,PlanningReadReceipt receipt,ExactRef originalEvidence) {
        public TerminalObservation{Objects.requireNonNull(status);Objects.requireNonNull(originalEvidence);require(originalEvidence.bytes()>0&&status.equals(decode(receipt,Scope.TERMINAL)),"actual terminal Status/value/original custody differs");}
    }
}
