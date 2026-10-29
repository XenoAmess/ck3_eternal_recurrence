package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionJournal;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * An original public Driver invocation is distinct from a Native read attempt or an action receipt.
 * DATA constructors do not admit a failure: the installed source must recognize the identical private
 * invocation before the sole publisher can prepare a history row.
 */
public final class DriverPublicExecuteFailureMaterial {
    /** Immutable loaded Java/original-source closure; not a Native permission or registration count. */
    public static final int MAX_PRODUCER_SOURCES=256;
    private DriverPublicExecuteFailureMaterial() { }

    public interface Source {
        ActionJournal journal();
        void requireOwner(DriverStateAssembler authority,ActionJournal journal,OutcomeArchive archive,
                RootReadContractCatalog catalog);
        List<ExactRef> sources();
        Originals requireOriginal(Session same,DriverStateAssembler authority,OutcomeArchive bound,
                OriginalInvocation identicalInvocation)throws IOException;
        /** Settled publication cleanup only. UNKNOWN retains its identical invocation. */
        void release(OriginalInvocation identicalInvocation)throws IOException;
    }
    public interface OriginalInvocation {
        Source issuer();
    }
    /** Original exception DATA; the spelling does not load a class or grant public fault authority. */
    public record OriginalError(String pythonClass,String message) {
        public OriginalError {
            StrictJson.require(pythonClass!=null&&pythonClass.matches("[A-Za-z_][A-Za-z0-9_]*"),
                    "original Python exception class spelling required");
            Objects.requireNonNull(message);
        }
        public String recorded(){return pythonClass+": "+message;}
    }
    /** No after-frame, successful READ receipt, Native ACK or manufactured result is present here. */
    public record Originals(OperationKey originalCommand,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            Known before,ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,
            ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,
            long headSequence,String headDigest,List<ExactRef> producerSources) {
        public Originals {
            Objects.requireNonNull(originalCommand);Objects.requireNonNull(error);Objects.requireNonNull(result);Objects.requireNonNull(publicNumbers);
            StrictJson.require(result.isPresent()==publicNumbers.isPresent(),"actual result requires its owning public number roles");
            Objects.requireNonNull(before);
            for(ExactRef ref:List.of(beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverPublicExecuteFailureMaterial::positive);
            result.ifPresent(DriverPublicExecuteFailureMaterial::positive);
            Objects.requireNonNull(unsupportedCapabilities);unsupportedCapabilities.ifPresent(DriverPublicExecuteFailureMaterial::positive);
            Objects.requireNonNull(unresolvedAction);unresolvedAction.ifPresent(DriverPublicExecuteFailureMaterial::positive);
            StrictJson.safe(headSequence,0);
            StrictJson.require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}"),"actual invocation writer head required");
            producerSources=List.copyOf(producerSources);
            StrictJson.require(!producerSources.isEmpty()&&producerSources.size()<=MAX_PRODUCER_SOURCES
                    &&new java.util.LinkedHashSet<>(producerSources).size()==producerSources.size(),
                    "finite distinct active failure producers required");
            producerSources.forEach(DriverPublicExecuteFailureMaterial::positive);
        }
        public Originals(OperationKey originalCommand,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
                Known before,ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef invocation,ExactRef caller,
                ExactRef epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {
            this(originalCommand,error,result,publicNumbers,before,beforeDriver,originalKnown,nativeFrame,driverFacts,invocation,caller,Optional.of(epochManifest),unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);
        }
    }
    /** Typed serializer input. This is historical DATA and cannot mint an OriginalInvocation. */
    public record InvocationData(OperationKey originalCommand,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef caller,
            Optional<ExactRef> epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public InvocationData {
            Objects.requireNonNull(originalCommand);Objects.requireNonNull(error);Objects.requireNonNull(result);Objects.requireNonNull(publicNumbers);
            StrictJson.require(result.isPresent()==publicNumbers.isPresent(),"actual result requires its owning public number roles");
            for(ExactRef ref:List.of(beforeDriver,originalKnown,nativeFrame,driverFacts,caller))positive(ref);
            Objects.requireNonNull(epochManifest).ifPresent(DriverPublicExecuteFailureMaterial::positive);
            result.ifPresent(DriverPublicExecuteFailureMaterial::positive);StrictJson.safe(headSequence,0);
            Objects.requireNonNull(unsupportedCapabilities);unsupportedCapabilities.ifPresent(DriverPublicExecuteFailureMaterial::positive);
            Objects.requireNonNull(unresolvedAction);unresolvedAction.ifPresent(DriverPublicExecuteFailureMaterial::positive);
            StrictJson.require(headDigest!=null&&headDigest.matches("[0-9a-f]{64}"),"actual invocation writer head required");
            producerSources=List.copyOf(producerSources);StrictJson.require(!producerSources.isEmpty()&&producerSources.size()<=MAX_PRODUCER_SOURCES
                    &&new java.util.LinkedHashSet<>(producerSources).size()==producerSources.size(),"finite active failure sources required");
            producerSources.forEach(DriverPublicExecuteFailureMaterial::positive);
        }
        public InvocationData(OperationKey originalCommand,OriginalError error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
                ExactRef beforeDriver,ExactRef originalKnown,ExactRef nativeFrame,ExactRef driverFacts,ExactRef caller,ExactRef epochManifest,
                Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {
            this(originalCommand,error,result,publicNumbers,beforeDriver,originalKnown,nativeFrame,driverFacts,caller,Optional.of(epochManifest),unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);
        }
    }
    public sealed interface Outcome permits Queued,StorageDiagnostic { }
    /** Retention has succeeded; publication still belongs to the original same-writer final flush. */
    public record Queued(ExactRef originalRow) implements Outcome {
        public Queued {positive(originalRow);}
    }
    public record StorageDiagnostic(String errorType,String message) implements Outcome {
        public StorageDiagnostic {StrictJson.text(errorType);Objects.requireNonNull(message);}
    }
    private static void positive(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty original reference required");}
}
