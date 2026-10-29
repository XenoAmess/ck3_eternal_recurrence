package org.xar.ck3.control.application.history;

import java.io.IOException;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Early original Driver exceptions: no new frame, actor, readiness or Native attempt is manufactured. */
public final class DriverEarlyExecuteFailure {
    private DriverEarlyExecuteFailure(){}
    public static final int MAX_PRODUCER_SOURCES=256;
    public enum ErrorOrigin { MIGRATED_PUBLIC_FAULT, ACTUAL_JAVA_FAILURE }
    /** Exception DATA only. The sole installed private issuer must prove the actual thrown object and call stage. */
    public record Error(ErrorOrigin origin,String className,Optional<String> message) {
        public Error {
            Objects.requireNonNull(origin);Objects.requireNonNull(message);StrictJson.text(className);
            StrictJson.require(className.length()<=1024&&className.matches("[A-Za-z_$][A-Za-z0-9_.$/]*"),"actual exception class name required");
            if(origin==ErrorOrigin.MIGRATED_PUBLIC_FAULT)StrictJson.require(className.matches("[A-Za-z_][A-Za-z0-9_]*")&&message.isPresent(),"migrated public error requires its original class and message");
        }
        public String recorded(){return className+": "+message.orElse("");}
    }
    public record Missing(List<String> reasons) {
        public Missing {reasons=List.copyOf(reasons);StrictJson.require(!reasons.isEmpty()&&reasons.size()<=256,"explicit finite missing cached facts required");reasons.forEach(StrictJson::text);}
    }
    public interface Source {
        ActionJournal journal();
        List<ExactRef> sources();
        void requireOwner(DriverStateAssembler authority,ActionJournal journal,OutcomeArchive archive,RootReadContractCatalog catalog);
        Originals requireOriginal(Session same,DriverStateAssembler authority,OutcomeArchive bound,OriginalInvocation identical)throws IOException;
        void release(OriginalInvocation identical)throws IOException;
    }
    public interface OriginalInvocation { Source issuer(); }
    public sealed interface Retained permits Absent,Cached {}
    public record Absent(Missing reason) implements Retained {public Absent{Objects.requireNonNull(reason);}}
    /** Historical complete cached facts only. Its optional semantic source is never a fresh observation. */
    public record Cached(Known before,ExactRef beforeDriver,ExactRef originalKnown,Optional<ExactRef> historicalSource) implements Retained {
        public Cached {Objects.requireNonNull(before);positive(beforeDriver);positive(originalKnown);Objects.requireNonNull(historicalSource);historicalSource.ifPresent(DriverEarlyExecuteFailure::positive);
            StrictJson.require(before.observation().map(DriverObservationFacts::semanticFactsEvidence).equals(historicalSource),"cached semantic source differs from retained Known");}
    }
    /** Pure wire references cannot deserialize into a live cached Known or an OriginalInvocation. */
    public sealed interface RetainedData permits AbsentData,CachedData {}
    public record AbsentData(Missing reason) implements RetainedData {public AbsentData{Objects.requireNonNull(reason);}}
    public record CachedData(ExactRef beforeDriver,ExactRef originalKnown,Optional<ExactRef> historicalSource) implements RetainedData {
        public CachedData {positive(beforeDriver);positive(originalKnown);Objects.requireNonNull(historicalSource);historicalSource.ifPresent(DriverEarlyExecuteFailure::positive);}
    }
    public static RetainedData retainedData(Retained actual){Objects.requireNonNull(actual);if(actual instanceof Absent absent)return new AbsentData(absent.reason());var cached=(Cached)actual;return new CachedData(cached.beforeDriver(),cached.originalKnown(),cached.historicalSource());}
    public record Originals(OperationKey originalCommand,Error error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            Retained retained,ExactRef invocation,ExactRef caller,Optional<ExactRef> epochManifest,Optional<ExactRef> unsupportedCapabilities,
            Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {
        public Originals(OperationKey originalCommand,Error error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            Retained retained,ExactRef invocation,ExactRef caller,ExactRef epochManifest,Optional<ExactRef> unsupportedCapabilities,
            Optional<ExactRef> unresolvedAction,long headSequence,String headDigest,List<ExactRef> producerSources) {this(originalCommand,error,result,publicNumbers,retained,invocation,caller,Optional.of(epochManifest),unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);}
        public Originals {Objects.requireNonNull(retained);positive(invocation);validate(originalCommand,error,result,publicNumbers,caller,epochManifest,unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);producerSources=refs(producerSources);}
    }
    public record InvocationData(OperationKey originalCommand,Error error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            RetainedData retained,ExactRef caller,Optional<ExactRef> epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,
            long headSequence,String headDigest,List<ExactRef> producerSources) {
        public InvocationData(OperationKey originalCommand,Error error,Optional<ExactRef> result,Optional<PublicNumbers> publicNumbers,
            RetainedData retained,ExactRef caller,ExactRef epochManifest,Optional<ExactRef> unsupportedCapabilities,Optional<ExactRef> unresolvedAction,
            long headSequence,String headDigest,List<ExactRef> producerSources) {this(originalCommand,error,result,publicNumbers,retained,caller,Optional.of(epochManifest),unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);}
        public InvocationData {Objects.requireNonNull(retained);validate(originalCommand,error,result,publicNumbers,caller,epochManifest,unsupportedCapabilities,unresolvedAction,headSequence,headDigest,producerSources);producerSources=refs(producerSources);}
    }
    public static InvocationData invocationData(Originals actual){return new InvocationData(actual.originalCommand(),actual.error(),actual.result(),actual.publicNumbers(),retainedData(actual.retained()),actual.caller(),actual.epochManifest(),actual.unsupportedCapabilities(),actual.unresolvedAction(),actual.headSequence(),actual.headDigest(),actual.producerSources());}
    public sealed interface Outcome permits Queued,StorageDiagnostic,MissingFacts {}
    public record Queued(ExactRef originalRow) implements Outcome {public Queued{positive(originalRow);}}
    public record StorageDiagnostic(String errorType,String message) implements Outcome {public StorageDiagnostic{StrictJson.text(errorType);Objects.requireNonNull(message);}}
    public record MissingFacts(Missing missing) implements Outcome,DriverEarlyExecuteFailureRowProducer.Preparation {public MissingFacts{Objects.requireNonNull(missing);}}
    private static void validate(OperationKey command,Error error,Optional<ExactRef> result,Optional<PublicNumbers> numbers,ExactRef caller,Optional<ExactRef> epoch,
            Optional<ExactRef> caps,Optional<ExactRef> unresolved,long sequence,String digest,List<ExactRef> sources){
        Objects.requireNonNull(command);Objects.requireNonNull(error);Objects.requireNonNull(result);Objects.requireNonNull(numbers);
        StrictJson.require(result.isPresent()==numbers.isPresent(),"actual early error result requires source-owned public number roles");result.ifPresent(DriverEarlyExecuteFailure::positive);positive(caller);Objects.requireNonNull(epoch).ifPresent(DriverEarlyExecuteFailure::positive);
        Objects.requireNonNull(caps);caps.ifPresent(DriverEarlyExecuteFailure::positive);Objects.requireNonNull(unresolved);unresolved.ifPresent(DriverEarlyExecuteFailure::positive);
        StrictJson.safe(sequence,0);StrictJson.require(digest!=null&&digest.matches("[0-9a-f]{64}"),"actual early invocation writer head required");refs(sources);
    }
    static List<ExactRef> refs(List<ExactRef> original){var refs=List.copyOf(original);StrictJson.require(!refs.isEmpty()&&refs.size()<=MAX_PRODUCER_SOURCES&&new LinkedHashSet<>(refs).size()==refs.size(),"finite distinct actual producer sources required");refs.forEach(DriverEarlyExecuteFailure::positive);return refs;}
    static void positive(ExactRef ref){StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"nonempty original reference required");}
}
