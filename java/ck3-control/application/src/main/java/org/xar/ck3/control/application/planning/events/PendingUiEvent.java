package org.xar.ck3.control.application.planning.events;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual pending-successor UI DATA. Constructing this record grants no Ready, read, event or native authority.
 * The one installed Root private Source must revalidate its own parent/cause/publication on every callback. */
public final class PendingUiEvent {
    private PendingUiEvent(){ }
    public record Current(ActionCommand originalParent,FullSnapshot full,Known known,Complete frame,
            ExactRef originalDriver,ExactRef originalHistoryBasis,ExactRef canonicalPublication,
            ExactRef canonicalDomain,ExactRef qualifiedCause,Set<String> bridgeCapabilities){
        public Current{
            Objects.requireNonNull(originalParent);Objects.requireNonNull(full);Objects.requireNonNull(known);Objects.requireNonNull(frame);
            for(ExactRef ref:List.of(originalDriver,originalHistoryBasis,canonicalPublication,canonicalDomain,qualifiedCause))
                StrictJson.require(ref.bytes()>0,"actual pending parent/Driver/history/publication/cause originals required");
            bridgeCapabilities=Set.copyOf(bridgeCapabilities);
            StrictJson.require(originalParent.origin() instanceof CommandOrigin.LifecycleTerminal
                    &&originalParent.operation().value().equals("continue-as-reconciled-successor")
                    &&originalParent.lifecycleBefore().game().equals(frame.identity().game())
                    &&originalParent.source().equals(frame.source())&&originalParent.sessionId().equals(frame.sessionId()),
                    "private event DATA crossed its real terminal Continue parent/Game/source/session");
            var actual=full.actual();var facts=full.facts();var identity=frame.identity();
            StrictJson.require(actual.session().game().equals(identity.game())&&actual.session().machineId().equals(identity.machineId())
                    &&actual.session().sessionId().equals(frame.sessionId())&&actual.session().connectionGeneration().equals(frame.connectionGeneration())
                    &&actual.snapshotId().equals(identity.frame().snapshotId())&&actual.nativeRevision().equals(identity.frame().identity().nativeRevision())
                    &&facts.publicRevision().equals(identity.frame().revision())&&facts.source().equals(frame.source())
                    &&full.semantic().equals(frame.semantic())&&full.originalEvidence().equals(frame.originalEvidence())
                    &&full.fullBindingSha256().equals(frame.fullBindingSha256())&&actual.observedAt().equals(frame.observedAt()),
                    "private pending event DATA is not its exact actual full native/Driver projection");
            StrictJson.require(Arrays.equals(known.driver().encode(),facts.driver().encode())
                    &&originalDriver.bytes()==known.driver().encode().length&&originalDriver.sha256().equals(DriverJson.sha256(known.driver().encode()))
                    &&known.stamp().driverVersion()==facts.driverVersion()&&known.stamp().episodeEpoch()==facts.episodeEpoch()
                    &&known.stamp().game().equals(identity.game())&&originalHistoryBasis.equals(known.originalHistoryBasis())
                    &&known.driver().session().actorId().equals(identity.frame().identity().player())
                    &&known.driver().session().episodeRunId().equals(identity.frame().episodeRunId()),
                    "private pending event DATA lost its actual current successor Driver/actor/run");
            var snapshot=frame.semantic();var player=OpportunityJson.object(snapshot.get("played_character"),"actual pending successor player");
            StrictJson.require(OpportunityJson.bool(snapshot.get("paused"),"paused")&&OpportunityJson.bool(snapshot.get("map_ready"),"map_ready")
                    &&OpportunityJson.bool(player.get("alive"),"alive")
                    &&OpportunityJson.integer(player.get("character_id"),"character_id").equals(identity.frame().identity().player()),
                    "pending event DATA requires its actual paused living successor map");
        }
        public List<OpportunityJson.Obj> history(){return known.driver().commandHistory().stream()
                .map(row->DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES)).toList();}
        public List<ExactRef> originals(){return List.copyOf(new java.util.LinkedHashSet<>(List.of(originalDriver,originalHistoryBasis,canonicalPublication,canonicalDomain,qualifiedCause,frame.originalEvidence())));}
    }
    @FunctionalInterface public interface Work<T>{T run(Current actual)throws IOException;}
    /** The implementation is the actual per-Game Root pending issuer, not a caller-supplied DATA adapter. */
    public interface Source {
        void requireCurrent(Session same)throws IOException;
        <T>T withCurrent(Session same,Instant deadline,Work<T> work)throws IOException;
        /** Only the identical installed event-window or pending-interaction contract may enter this private scope. */
        <T>PlanningReadResult.Known<T> read(Session same,ReadContract<T> installed,PlanningReadRequest exact)throws IOException;
        /** Root alone proves the actual once-intent import/Driver CAS lineage and exact retained command.
         * The fresh command must have just come from this identical private Source callback. */
        void requireOriginalPreparation(Session same,ActionCommand retained,ActionCommand actualFresh)throws IOException;
    }
    @FunctionalInterface public interface ScopedWork<T>{T run()throws IOException;}
}
