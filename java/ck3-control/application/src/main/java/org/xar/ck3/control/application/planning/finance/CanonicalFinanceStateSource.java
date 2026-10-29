package org.xar.ck3.control.application.planning.finance;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionSnapshotReader;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual read-only finance state producer over the original writer's imported domain registry. */
public final class CanonicalFinanceStateSource implements FinanceStatePort.SourcePort {
    /** One Root-owned catalog binds the owning body's real slot/schema/producer closure; no filename inference. */
    public record Binding(FinanceStatePort.ReaderBinding decoder,DomainBodies.Slot slot,String contractSchema,
            int maximumBodyBytes,List<ExactRef> actualProducerSources) {
        public Binding {
            Objects.requireNonNull(decoder);Objects.requireNonNull(slot);StrictJson.text(contractSchema);
            StrictJson.require(maximumBodyBytes>0&&maximumBodyBytes<=ContinuityJson.DOMAIN_MAX_BYTES,"bounded actual finance domain body required");
            actualProducerSources=List.copyOf(actualProducerSources);
            StrictJson.require(!actualProducerSources.isEmpty()&&actualProducerSources.size()<=64,"complete actual owning domain producer closure required");
        }
    }
    @FunctionalInterface public interface CurrentFrame {
        /** Root returns its actual held Driver observation, never the request's constructor values. */
        ObservationIdentity current(Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface Checkpoints {
        /** The actual save store supplies its current original checkpoint; absence is retained. */
        Optional<FinanceStatePort.Checkpoint> current(Session borrowed) throws IOException;
    }
    @FunctionalInterface public interface CurrentRequestFrame {
        ObservationIdentity current(Session borrowed,PlanningRequest expected) throws IOException;
    }
    private final Path writerLock;
    private final ContinuityStorePort store;
    private final ActionSnapshotReader actions;
    private final CurrentRequestFrame frame;
    private final Checkpoints checkpoints;
    private final List<Binding> catalog;
    public CanonicalFinanceStateSource(Path writerLock,ContinuityStorePort store,ActionJournal actions,CurrentFrame frame,
            Checkpoints checkpoints,List<Binding> catalog) {
        this(writerLock,store,new ActionSnapshotReader(actions),(borrowed,request)->frame.current(borrowed),checkpoints,catalog);
    }
    /** Actual Root shares its original read-only action lease and current physical Game readiness. */
    public CanonicalFinanceStateSource(Path writerLock,ContinuityStorePort store,ActionSnapshotReader actions,CurrentRequestFrame frame,
            Checkpoints checkpoints,List<Binding> catalog) {
        this.writerLock=Objects.requireNonNull(writerLock).toAbsolutePath().normalize();this.store=Objects.requireNonNull(store);
        this.actions=Objects.requireNonNull(actions);this.frame=Objects.requireNonNull(frame);this.checkpoints=Objects.requireNonNull(checkpoints);
        this.catalog=List.copyOf(catalog);var domains=EnumSet.noneOf(FinanceStatePort.Domain.class);var slots=EnumSet.noneOf(DomainBodies.Slot.class);
        for(var binding:this.catalog)StrictJson.require(domains.add(binding.decoder().domain())&&slots.add(binding.slot()),"one actual domain and one actual imported slot per finance catalog entry");
    }
    public List<FinanceStatePort.ReaderBinding> owningReaders() { return catalog.stream().map(Binding::decoder).toList(); }
    @Override public FinanceStatePort.Read readUnderOriginalLock(PlanningRequest request) {
        try { return store.locked(session->readUnderOriginalLock(session,request)); }
        catch(IOException failure) { return new FinanceStatePort.Unavailable("original finance writer read unavailable: "+failure.getMessage()); }
    }
    @Override public FinanceStatePort.Read readUnderOriginalLock(Session session,PlanningRequest request) {
        Objects.requireNonNull(session);Objects.requireNonNull(request);
        try {
            session.requireWriter(writerLock);var actual=session.head();ExactRef persisted=session.persistedHead();
            if(!actual.state().machineId().equals(request.before().machineId())||!frame.current(session,request).equals(request.before()))
                return new FinanceStatePort.Unavailable("original finance writer/current Driver belongs to another Game/frame/machine");
            var bodyDocuments=new ArrayList<FinanceStatePort.Document>();
            for(var binding:catalog) {
                var imported=DomainBodies.reference(actual.state(),binding.slot());var read=session.readDomain(binding.slot());
                if(read instanceof DomainBodies.Unavailable)continue; // Missing is represented by absence, never CLEAR.
                var available=(DomainBodies.Available)read;var reference=available.reference();
                StrictJson.require(imported.isPresent()&&imported.orElseThrow().equals(reference)&&available.head().equals(persisted)
                        &&reference.slot()==binding.slot()&&reference.contractSchema().equals(binding.contractSchema()),"actual imported domain reference/schema/head changed");
                for(var pin:available.headSources())session.verifyPin(pin);
                // Producer refs record the original import; incremental workers may use newer implementations.
                var payloadPin=session.capturePin(reference.payload(),binding.maximumBodyBytes());session.verifyPin(payloadPin);
                byte[] bytes=session.readPinned(payloadPin,binding.maximumBodyBytes());StrictJson.require(reference.identity().equals(payloadPin.identity())
                        &&reference.payload().bytes()==bytes.length&&reference.payload().sha256().equals(ActionCodec.sha256(bytes)),"actual imported domain native identity or bytes changed");
                StrictJson.require(sameOriginalBody(available.canonicalBody(),bytes,binding.maximumBodyBytes()),
                        "actual imported canonical body differs from its unchanged original bytes");
                var document=new FinanceStatePort.Document(binding.decoder().domain(),reference.payload(),bytes);
                Objects.requireNonNull(binding.decoder().reader().decode(document));bodyDocuments.add(document);session.verifyPin(payloadPin);
            }
            ActionJournal.Snapshot snapshot=actions.withFrozen(session,lease->{var frozen=lease.snapshot();lease.assertCurrent();return frozen;});
            StrictJson.require(snapshot.headSha256().equals(actual.digest())&&session.head().digest().equals(actual.digest())
                    &&session.persistedHead().equals(persisted),"finance domain/action snapshots crossed the original held head");
            Optional<FinanceStatePort.Checkpoint> checkpoint=Objects.requireNonNull(checkpoints.current(session));
            session.requireWriter(writerLock);
            StrictJson.require(session.head().digest().equals(actual.digest())&&session.persistedHead().equals(persisted),"finance checkpoint read changed the original canonical head");
            return new FinanceStatePort.Head(request.before(),persisted,bodyDocuments,snapshot.actions(),checkpoint);
        } catch(IOException|IllegalArgumentException|IllegalStateException failure) {
            return new FinanceStatePort.Unavailable("actual finance domain state rejected: "+failure.getMessage());
        }
    }
    /** Numeric JSON types stay distinct; equivalent decimal spellings in opaque extensions are compared as values. */
    public static boolean sameOriginalBody(byte[] first,byte[] second,int maximumBytes) {
        return org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(originalBody(first,maximumBytes))
                .equals(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(originalBody(second,maximumBytes)));
    }
    /** Compare the JSON domain while retaining the independently pinned original bytes, including a UTF-8 BOM. */
    public static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj originalBody(byte[] raw,int maximumBytes) {
        StrictJson.require(raw!=null&&raw.length>0&&raw.length<=maximumBytes,"bounded original finance body required");
        byte[] json=raw.length>=3&&raw[0]==(byte)0xef&&raw[1]==(byte)0xbb&&raw[2]==(byte)0xbf
                ?java.util.Arrays.copyOfRange(raw,3,raw.length):raw;
        return org.xar.ck3.control.application.driver.DriverJson.object(json,maximumBytes);
    }
}
