package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.effects.RootGuardEvidence.WriterPoint;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/**
 * DATA for a read-only query while one original primitive is unresolved.
 * Construction is neither canonical membership, ordinary readiness nor permission to submit.
 */
public record ReconciliationIdentity(ObservationIdentity factual,G2Source source,String sessionId,
        BigInteger connectionGeneration,Pending pending,Evidence evidence,Instant observedAt,
        DriverRelation driverRelation,Optional<WriterPoint> historyPoint) {
    public enum DriverRelation { EXACT, HISTORY_APPEND }
    /** Historical exact Driver DATA retains its original constructor and v1 semantics. */
    public ReconciliationIdentity(ObservationIdentity factual,G2Source source,String sessionId,
            BigInteger connectionGeneration,Pending pending,Evidence evidence,Instant observedAt) {
        this(factual,source,sessionId,connectionGeneration,pending,evidence,observedAt,DriverRelation.EXACT,Optional.empty());
    }
    public record Pending(String actionId,String bodySha256,String requestId,ObservationIdentity originalBefore,
            ExactRef originalReceipt,ExactRef originalBeforeDriver) {
        public Pending {
            StrictJson.require(actionId!=null&&actionId.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"),"bounded original pending action ID required");
            StrictJson.require(bodySha256!=null&&bodySha256.matches("[0-9a-f]{64}"),"exact original action body SHA required");
            StrictJson.text(requestId);Objects.requireNonNull(originalBefore);
            original(originalReceipt);original(originalBeforeDriver);
        }
    }
    public record Evidence(ExactRef actualNativePacket,ExactRef actualHello,ExactRef originalHeartbeat,
            ExactRef observationManifest,ExactRef currentOriginalDriver,Optional<ExactRef> completeSourceQualification) {
        public Evidence {
            Objects.requireNonNull(completeSourceQualification);
            List<ExactRef> originals=java.util.stream.Stream.concat(List.of(actualNativePacket,actualHello,originalHeartbeat,observationManifest,
                    currentOriginalDriver).stream(),completeSourceQualification.stream()).toList();
            originals.forEach(ReconciliationIdentity::original);
            StrictJson.require(new java.util.HashSet<>(originals).size()==originals.size(),"distinct complete reconciliation evidence roles required");
        }
        public Evidence(ExactRef actualNativePacket,ExactRef actualHello,ExactRef originalHeartbeat,
                ExactRef observationManifest,ExactRef currentOriginalDriver,ExactRef completeSourceQualification) {
            this(actualNativePacket,actualHello,originalHeartbeat,observationManifest,currentOriginalDriver,Optional.of(completeSourceQualification));
        }
        public List<ExactRef> originals(){return java.util.stream.Stream.concat(List.of(actualNativePacket,actualHello,originalHeartbeat,observationManifest,currentOriginalDriver).stream(),completeSourceQualification.stream()).toList();}
    }
    public ReconciliationIdentity {
        Objects.requireNonNull(factual);Objects.requireNonNull(source);StrictJson.text(sessionId);
        FrontendFrame.positive(connectionGeneration);Objects.requireNonNull(pending);Objects.requireNonNull(evidence);Objects.requireNonNull(observedAt);
        StrictJson.require(factual.machineId().equals(source.machineId()),"factual frame and actual source machine differ");
        requireSamePhysicalSubject(pending.originalBefore(),factual);
        Objects.requireNonNull(driverRelation);historyPoint=Objects.requireNonNull(historyPoint);
        boolean equal=sameBytes(pending.originalBeforeDriver(),evidence.currentOriginalDriver());
        StrictJson.require(driverRelation==DriverRelation.EXACT?equal&&historyPoint.isEmpty():!equal&&historyPoint.isPresent(),
                "exact v1 Driver DATA or explicit history-append v2 DATA with original writer point required");
    }
    /** Pure binding only. The real canonical writer/archive helper must separately prove this receipt. */
    public static ReconciliationIdentity fromCanonical(ActionReceipt original,ObservationIdentity factual,G2Source source,
            String sessionId,BigInteger connectionGeneration,ExactRef originalReceipt,ExactRef originalBeforeDriver,
            Evidence evidence,Instant observedAt) {
        return fromCanonical(original,factual,source,sessionId,connectionGeneration,originalReceipt,originalBeforeDriver,
                evidence,observedAt,DriverRelation.EXACT,Optional.empty());
    }
    /** Unqualified v2 DATA only. The real four-argument pending binder and its private Root provider must verify it. */
    public static ReconciliationIdentity fromCanonicalHistoryAppend(ActionReceipt original,ObservationIdentity factual,G2Source source,
            String sessionId,BigInteger connectionGeneration,ExactRef originalReceipt,ExactRef originalBeforeDriver,
            Evidence evidence,Instant observedAt,WriterPoint actualHistoryPoint) {
        return fromCanonical(original,factual,source,sessionId,connectionGeneration,originalReceipt,originalBeforeDriver,
                evidence,observedAt,DriverRelation.HISTORY_APPEND,Optional.of(Objects.requireNonNull(actualHistoryPoint)));
    }
    private static ReconciliationIdentity fromCanonical(ActionReceipt original,ObservationIdentity factual,G2Source source,
            String sessionId,BigInteger connectionGeneration,ExactRef originalReceipt,ExactRef originalBeforeDriver,
            Evidence evidence,Instant observedAt,DriverRelation relation,Optional<WriterPoint> point) {
        ActionState.Attempt attempt=primitiveAttempt(original);
        ActionCommand command=original.command();GuardEvidence guard=attempt.guard();
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay,"only an original gameplay primitive has reconciliation identity");
        ObservationIdentity before=command.before();
        StrictJson.require(original.bodySha256().equals(ActionCodec.bodySha256(command)),"original full canonical action body differs");
        StrictJson.require(guard.origin() instanceof CommandOrigin.Gameplay&&guard.observed().equals(before)
                &&guard.source().equals(command.source())&&guard.sessionId().equals(command.sessionId())
                &&guard.operation().equals(command.operation()),"original Attempt guard differs from its immutable gameplay command");
        StrictJson.require(command.source().equals(source)&&command.sessionId().equals(sessionId),
                "actual source/session crossed the original primitive");
        // Retain the actual cached frame publication time; native query freshness belongs to the private lease/wire chronology.
        Objects.requireNonNull(observedAt,"actual retained observation publication time required");
        var identity=new ReconciliationIdentity(factual,source,sessionId,connectionGeneration,
                new Pending(command.actionId(),original.bodySha256(),attempt.requestId(),before,originalReceipt,originalBeforeDriver),evidence,observedAt,relation,point);
        identity.requireOriginalConnection(guard);
        return identity;
    }
    static ActionState.Attempt primitiveAttempt(ActionReceipt original) {
        Objects.requireNonNull(original);
        StrictJson.require(!original.settled()&&(original.state() instanceof ActionState.Submitting
                ||original.state() instanceof ActionState.AckReceived||original.state() instanceof ActionState.Unknown),
                "only an unresolved original primitive with a durable Attempt may be queried");
        ActionState.Attempt attempt=ActionTransitions.attempt(original.state()).orElseThrow(
                ()->new IllegalArgumentException("unresolved intent/composite has no original primitive request identity"));
        StrictJson.require(original.command().origin() instanceof CommandOrigin.Gameplay,"frontend/terminal/reconciliation origins cannot borrow gameplay pending identity");
        StrictJson.require(original.bodySha256().equals(ActionCodec.bodySha256(original.command())),"canonical pending action body changed");
        ActionCommand command=original.command();GuardEvidence guard=attempt.guard();
        StrictJson.require(guard.origin() instanceof CommandOrigin.Gameplay&&guard.observed().equals(command.before())
                &&guard.source().equals(command.source())&&guard.sessionId().equals(command.sessionId())
                &&guard.operation().equals(command.operation()),"canonical primitive Attempt guard differs from its complete original command");
        return attempt;
    }
    public static void requireSameSubject(ObservationIdentity before,ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                &&before.frame().episodeRunId().equals(after.frame().episodeRunId())
                &&before.frame().identity().player().equals(after.frame().identity().player()),
                "factual query crossed the original actual machine/Game/player/episode");
        requireSamePhysicalSubject(before,after);
        StrictJson.require(after.frame().revision().compareTo(before.frame().revision())>=0,
                "same-connection factual public revision regressed");
    }
    /** A new HELLO can restore an earlier public Driver revision; native time and Game remain monotone. */
    public static void requireSamePhysicalSubject(ObservationIdentity before,ObservationIdentity after) {
        StrictJson.require(before.machineId().equals(after.machineId())&&before.game().equals(after.game())
                &&before.frame().episodeRunId().equals(after.frame().episodeRunId())
                &&before.frame().identity().player().equals(after.frame().identity().player()),
                "factual query crossed the original actual machine/Game/player/episode");
        StrictJson.require(before.observationVersion()==after.observationVersion()
                &&after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision())>=0
                &&after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw())>=0,
                "factual query regressed its original contract/native/date identity");
    }
    /** DATA relation only. Actual current HELLO, frame and wire custody are checked by the installed provider/scope.
     * A reconnect retains the original gameplay guard and requires a distinct current HELLO, never relabelled old evidence. */
    public void requireOriginalConnection(GuardEvidence original) {
        Objects.requireNonNull(original);
        StrictJson.require(original.origin() instanceof CommandOrigin.Gameplay
                &&original.observed().equals(pending.originalBefore())
                &&original.source().equals(source)&&original.sessionId().equals(sessionId),
                "reconciliation crossed the original gameplay frame/source/session");
        int order=connectionGeneration.compareTo(original.connectionGeneration());
        StrictJson.require(order>=0&&(order==0||!sameBytes(capabilityEvidence(),original.capabilityEvidence())),
                "reconciliation connection regressed or reused the original HELLO after reconnect");
        if (order==0) StrictJson.require(factual.frame().revision().compareTo(pending.originalBefore().frame().revision())>=0,
                "same-connection factual public revision regressed");
    }
    public boolean sameGuardFrame(ReconciliationIdentity other) {
        return other!=null&&factual.equals(other.factual)&&source.equals(other.source)&&sessionId.equals(other.sessionId)
                &&connectionGeneration.equals(other.connectionGeneration)&&pending.equals(other.pending)&&evidence.equals(other.evidence)
                &&driverRelation==other.driverRelation&&historyPoint.equals(other.historyPoint);
    }
    public ExactRef nativeEvidence(){return evidence.actualNativePacket();}
    public ExactRef capabilityEvidence(){return evidence.actualHello();}
    public List<ExactRef> supportingEvidence(){
        return java.util.stream.Stream.concat(evidence.originals().stream().skip(2),
                java.util.stream.Stream.of(pending.originalReceipt(),pending.originalBeforeDriver())).distinct().toList();
    }
    public String bindingSha256(){
        return ActionCodec.sha256(StrictJson.canonical(ReconciliationIdentityCodec.encode(this),65_536));
    }
    private static boolean sameBytes(ExactRef first,ExactRef second){return first.bytes()==second.bytes()&&first.sha256().equals(second.sha256());}
    private static void original(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0,"nonempty physical reconciliation original required");}
}

