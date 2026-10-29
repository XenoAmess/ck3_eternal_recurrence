package org.xar.ck3.control.application.history;

import java.util.*;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Finite post-Known Army pure-computation failures. DATA constructors and decoding grant no live
 * Known custody, Native failed attempt, publication, current-frame or READ-only lineage authority.
 * The installed source-owned verifier must reproduce the failure from its actual archived reads.
 */
public final class DriverPostKnownReadFailureMaterial {
    public static final String SCHEMA="xar.driver-post-known-read-failure/v1";
    public static final int MAX_SOURCE_CLOSURE=256;
    private DriverPostKnownReadFailureMaterial() { }
    public enum Kind {
        ARMY_EXPLICIT_PROJECT(0), ARMY_AUTO_CORE_COMPARE(1);
        private final int earlierReads;
        Kind(int earlierReads){this.earlierReads=earlierReads;}
        public int requiredEarlierReads(){return earlierReads;}
    }
    /** Only the project or comparison function's actual RuntimeException belongs here. Validation
     * of scope/receipt/mode/peer/frame remains outside that function's catch and must reject.
     * A fixed verifier does no storage, full encoding, capture, IO or Native query.
     */
    public record Failure(Kind kind,String failureType,String message,List<ExactRef> sourceClosure) {
        public Failure {
            Objects.requireNonNull(kind);
            StrictJson.require(failureType!=null&&failureType.matches("[A-Za-z_$][A-Za-z0-9_$]*"),
                    "actual pure-computation exception class spelling required");
            Objects.requireNonNull(message);sourceClosure=List.copyOf(sourceClosure);
            StrictJson.require(!sourceClosure.isEmpty()&&sourceClosure.size()<=MAX_SOURCE_CLOSURE
                    &&new LinkedHashSet<>(sourceClosure).size()==sourceClosure.size(),
                    "finite distinct installed pure verifier source closure required");
            sourceClosure.forEach(DriverPostKnownReadFailureMaterial::positive);
        }
        public String error(){return failureType+": "+message;}
        public Obj toJson(){
            return new Obj(Map.of("schema",new Text(SCHEMA),"kind",new Text(kind.name()),
                    "failure_type",new Text(failureType),"message",new Text(message),
                    "source_closure",new Arr(sourceClosure.stream()
                            .<Value>map(DriverObservationEvidenceReader::reference).toList())));
        }
    }
    /** Sole closed DATA decoder. The exact installed contract, actual live identities and canonical
     * membership must be independently checked before these values can become a history candidate.
     */
    public static Failure fromJson(Value original){
        Obj row=OpportunityJson.object(original,"post-Known read failure");
        StrictJson.require(row.members().keySet().equals(Set.of("schema","kind","failure_type","message","source_closure"))
                &&SCHEMA.equals(OpportunityJson.text(row.get("schema"),"schema")),"exact post-Known failure version/fields required");
        Kind kind=Kind.valueOf(OpportunityJson.text(row.get("kind"),"kind"));
        List<ExactRef> sources=OpportunityJson.array(row.get("source_closure"),"source_closure").stream()
                .map(DriverObservationEvidenceReader::reference).toList();
        return new Failure(kind,OpportunityJson.text(row.get("failure_type"),"failure_type"),
                message(row.get("message")),sources);
    }
    private static String message(Value value){
        if(!(value instanceof Text text))throw new IllegalArgumentException("actual failure message must be a text token");
        return text.value();
    }
    public enum Reason { NO_INSTALLED_VERIFIER, NO_LIVE_ORIGINALS, NO_REPRODUCED_FAILURE }
    public sealed interface Outcome permits Queued,Unrecorded,StorageDiagnostic { }
    /** An actual immutable row artifact is queued. This is not a committed history or clear event. */
    public record Queued(ExactRef originalRow) implements Outcome {
        public Queued {positive(originalRow);}
    }
    public record Unrecorded(Reason reason,String diagnostic) implements Outcome {
        public Unrecorded {Objects.requireNonNull(reason);StrictJson.text(diagnostic);}
    }
    /** Archive/publication IO is distinct from the original deterministic computation failure. */
    public record StorageDiagnostic(String failureType,String message) implements Outcome {
        public StorageDiagnostic {StrictJson.text(failureType);Objects.requireNonNull(message);}
    }
    private static void positive(ExactRef value){
        StrictJson.require(Objects.requireNonNull(value).bytes()>0,"nonempty actual original reference required");
    }
}
