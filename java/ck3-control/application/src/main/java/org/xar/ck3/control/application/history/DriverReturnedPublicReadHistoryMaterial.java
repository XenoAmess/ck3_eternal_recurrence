package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.reads.PlanningPublicReadCollection;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Returned negative public READ DATA is distinct from a thrown error, successful read and action receipt. */
public final class DriverReturnedPublicReadHistoryMaterial {
    private DriverReturnedPublicReadHistoryMaterial(){ }
    public enum Kind { HORIZON_UNAVAILABLE,PREVIEW_DEFERRED }
    /** Only the identical private Root source installed in the publisher may issue a live OriginalReturned. */
    public interface Source {
        ActionJournal journal();
        RootReadContractCatalog catalog();
        void requireOwner(DriverStateAssembler authority,ActionJournal journal,OutcomeArchive archive,RootReadContractCatalog catalog);
        void requireCatalog(RootReadContractCatalog identical);
        List<ExactRef> sources();
        Originals requireOriginal(Session same,DriverStateAssembler authority,OutcomeArchive bound,OriginalReturned identical)throws IOException;
        void release(OriginalReturned identical)throws IOException;
        /** Sole owning fixed formatter, reconstructing original packets/frames/caller only; no Native query or live qualification. */
        Projection project(PlanningPublicReadCollection.Recorded recorded,InvocationData invocation,OutcomeArchive bound)throws IOException;
    }
    public interface OriginalReturned { Source issuer(); }
    public record FrameOriginals(ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,
            ExactRef readbackNativeFrame,ExactRef readbackDriverFacts) {
        public FrameOriginals {for(var ref:List.of(beforeDriver,originalKnown,nativeFrame,driverFacts,readbackNativeFrame,readbackDriverFacts))positive(ref);}
    }
    public record Originals(PlanningPublicReadCollection.Rejected<?> live,PlanningPublicReadCollection.Recorded recorded,
            ExactRef collectionMetadata,OperationKey originalCommand,Known before,FrameOriginals frames,
            ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public Originals(PlanningPublicReadCollection.Rejected<?> live,PlanningPublicReadCollection.Recorded recorded,
            ExactRef collectionMetadata,OperationKey originalCommand,Known before,FrameOriginals frames,
            ExactRef invocation,ExactRef caller,ExactRef epochManifest,long headSequence,String headDigest,List<ExactRef> producerSources) {this(live,recorded,collectionMetadata,originalCommand,before,frames,invocation,caller,Optional.of(epochManifest),headSequence,headDigest,producerSources);}
        public Originals {
            Objects.requireNonNull(live);Objects.requireNonNull(recorded);Objects.requireNonNull(originalCommand);
            Objects.requireNonNull(before);Objects.requireNonNull(frames);
            for(var ref:List.of(collectionMetadata,invocation,caller))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverReturnedPublicReadHistoryMaterial::positive);
            head(headSequence,headDigest);producerSources=references(producerSources,1,256);
        }
    }
    /** Canonical serializer input only: it cannot create a live private invocation or successful after guard. */
    public record InvocationData(ExactRef collectionMetadata,OperationKey originalCommand,FrameOriginals frames,ExactRef caller,
            Optional<ExactRef> epochManifest,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public InvocationData(ExactRef collectionMetadata,OperationKey originalCommand,FrameOriginals frames,ExactRef caller,
            ExactRef epochManifest,long headSequence,String headDigest,List<ExactRef> producerSources) {this(collectionMetadata,originalCommand,frames,caller,Optional.of(epochManifest),headSequence,headDigest,producerSources);}
        public InvocationData {
            Objects.requireNonNull(originalCommand);Objects.requireNonNull(frames);
            for(var ref:List.of(collectionMetadata,caller))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverReturnedPublicReadHistoryMaterial::positive);
            head(headSequence,headDigest);producerSources=references(producerSources,1,256);
        }
    }
    /** Both reports/number roles come from the one source-owned formatter, never from field-name inference. */
    public record Projection(Kind kind,OperationKey logicalOperation,OperationKey originalCommand,RawJson fullResult,
            PublicNumbers publicNumbers,List<ExactRef> sourceClosure) {
        public Projection {
            Objects.requireNonNull(kind);Objects.requireNonNull(logicalOperation);Objects.requireNonNull(originalCommand);
            Objects.requireNonNull(fullResult);Objects.requireNonNull(publicNumbers);sourceClosure=references(sourceClosure,1,260);
            var result=org.xar.ck3.control.application.driver.DriverJson.object(fullResult.bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            DriverReturnedPublicReadHistoryRowProducer.requireReport(kind,logicalOperation,result);
            publicNumbers.toPublic(result);
        }
    }
    public sealed interface Outcome permits Queued,StorageDiagnostic { }
    public record Queued(ExactRef originalRow) implements Outcome {public Queued{positive(originalRow);}}
    public record StorageDiagnostic(String errorType,String message) implements Outcome {
        public StorageDiagnostic {StrictJson.text(errorType);Objects.requireNonNull(message);}
    }
    static void positive(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty returned public-read original required");}
    static List<ExactRef> references(List<ExactRef> values,int minimum,int maximum) {
        values=List.copyOf(values);StrictJson.require(values.size()>=minimum&&values.size()<=maximum
                &&new java.util.LinkedHashSet<>(values).size()==values.size(),"finite distinct actual public-read references required");
        values.forEach(DriverReturnedPublicReadHistoryMaterial::positive);return values;
    }
    static void head(long sequence,String digest){StrictJson.safe(sequence,0);StrictJson.require(digest!=null&&digest.matches("[0-9a-f]{64}"),"actual returned public-read writer head required");}
}

