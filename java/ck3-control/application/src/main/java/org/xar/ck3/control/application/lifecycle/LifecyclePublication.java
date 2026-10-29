package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Original committed publication DATA. Only the private lifecycle issuer grants an episode proof. */
public sealed interface LifecyclePublication permits LifecyclePublication.Warm, LifecyclePublication.RecordedEvent {
    ObjectNode detailsObject();
    String eventIdentity();
    long eventSequence();
    ContinuityState before();
    ContinuityState after();
    List<WriterContracts.Pin> committedDocuments();
    List<WriterContracts.Pin> proofDocuments();
    Optional<LifecycleCommit> warmCommit();

    final class Warm implements LifecyclePublication {
        private final LifecycleCommit actual;
        private final List<WriterContracts.Pin> originals;
        Warm(LifecycleCommit actual) {
            this.actual=Objects.requireNonNull(actual);
            var pins=new java.util.LinkedHashSet<WriterContracts.Pin>(LifecycleComposites.immutableCommitPins(actual));
            pins.addAll(actual.prepared().sources());pins.addAll(actual.prepared().evidence());
            originals=List.copyOf(pins);
        }
        public ObjectNode detailsObject(){return actual.prepared().request().detailsObject();}
        public String eventIdentity(){return actual.receipt().eventIdentity();}
        public long eventSequence(){return Math.addExact(actual.prepared().predecessor().state().sequence(),1);}
        public ContinuityState before(){return actual.prepared().predecessor().state();}
        public ContinuityState after(){
            var row=actual.prepared().reduced().toJson();row.put("sequence",eventSequence());row.put("last_event_identity",eventIdentity());
            return ContinuityState.fromJson(row,before().machineId());
        }
        public List<WriterContracts.Pin> committedDocuments(){return LifecycleComposites.immutableCommitPins(actual);}
        public List<WriterContracts.Pin> proofDocuments(){return originals;}
        public Optional<LifecycleCommit> warmCommit(){return Optional.of(actual);}
    }

    /** Constructed only beside the actual canonical reader; never fabricates a warm Prepared. */
    final class RecordedEvent implements LifecyclePublication {
        private final WriterContracts.Request request;
        private final ContinuityState before,after;
        private final WriterContracts.Pin event;
        private final List<WriterContracts.Pin> documents;
        RecordedEvent(WriterContracts.Request request,ContinuityState before,ContinuityState after,
                WriterContracts.Pin event,List<WriterContracts.Pin> documents) {
            this.request=Objects.requireNonNull(request);this.before=Objects.requireNonNull(before);
            this.after=Objects.requireNonNull(after);this.event=Objects.requireNonNull(event);this.documents=List.copyOf(documents);
            org.xar.ck3.control.contracts.StrictJson.require(after.sequence()==Math.addExact(before.sequence(),1)
                    &&this.documents.contains(event),"exact historical lifecycle event and original pins required");
        }
        public ObjectNode detailsObject(){return request.detailsObject();}
        public String eventIdentity(){return request.identity();}
        public long eventSequence(){return after.sequence();}
        public ContinuityState before(){return before;}
        public ContinuityState after(){return after;}
        public List<WriterContracts.Pin> committedDocuments(){return List.of(event);}
        public List<WriterContracts.Pin> proofDocuments(){return documents;}
        public Optional<LifecycleCommit> warmCommit(){return Optional.empty();}
    }
}
