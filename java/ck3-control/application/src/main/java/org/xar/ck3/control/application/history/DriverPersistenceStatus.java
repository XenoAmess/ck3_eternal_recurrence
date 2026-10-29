package org.xar.ck3.control.application.history;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Root-local technical persistence diagnostics. This cache grants no action, replay, restore or Ready authority. */
public final class DriverPersistenceStatus {
    public static final String SCHEMA="xar.java.driver-persistence-status/v1";
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    public enum FailureKind { RETRYABLE, LOST_ORIGINAL, COMMIT_UNKNOWN, WAL_BARRIER }
    public record Failure(String errorType,String message,Optional<ExactRef> originalDiagnostic) {
        public Failure { StrictJson.text(errorType);Objects.requireNonNull(message);Objects.requireNonNull(originalDiagnostic);
            originalDiagnostic.ifPresent(ref->StrictJson.require(ref.bytes()>0,"actual nonempty diagnostic required")); }
        public String display(){return errorType+": "+message;}
        public static Failure storage(DriverReadHistoryRichMaterial.StorageDiagnostic actual) {
            Objects.requireNonNull(actual);return new Failure(actual.failureType(),actual.message(),actual.originalDiagnostic());
        }
        public ObjectNode toJson(){var row=StrictJson.object().put("error_type",errorType).put("message",message);
            row.set("original_diagnostic",originalDiagnostic.<JsonNode>map(ExactRef::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));return row;}
        public static Failure fromJson(JsonNode value){var row=StrictJson.object(value,Set.of("error_type","message","original_diagnostic"));
            return new Failure(StrictJson.text(row.get("error_type")),string(row.get("message")),row.get("original_diagnostic").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(row.get("original_diagnostic"))));}
    }
    /** A dirty token is minted only by this particular technical cache; JSON DATA cannot recreate it. */
    public static final class Attempt {
        private final DriverPersistenceStatus owner;private final BigInteger id;private final String operation;
        private Attempt(DriverPersistenceStatus owner,BigInteger id,String operation){this.owner=owner;this.id=id;this.operation=operation;}
        public BigInteger id(){return id;}public String operation(){return operation;}
    }
    public record Dirty(BigInteger attempt,String operation,Optional<FailureKind> failureKind,Optional<Failure> failure) {
        public Dirty { uint(attempt,true);StrictJson.text(operation);Objects.requireNonNull(failureKind);Objects.requireNonNull(failure);
            StrictJson.require(failureKind.isPresent()==failure.isPresent(),"failure kind and original failure must appear together"); }
        public boolean sticky(){return failureKind.filter(kind->kind==FailureKind.LOST_ORIGINAL||kind==FailureKind.WAL_BARRIER).isPresent();}
        public ObjectNode toJson(){var row=StrictJson.object().put("attempt",attempt.toString()).put("operation",operation);
            if(failureKind.isPresent())row.put("failure_kind",failureKind.orElseThrow().name());else row.putNull("failure_kind");
            row.set("failure",failure.<JsonNode>map(Failure::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));return row;}
        public static Dirty fromJson(JsonNode value){var row=StrictJson.object(value,Set.of("attempt","operation","failure_kind","failure"));
            return new Dirty(decimal(row.get("attempt")),StrictJson.text(row.get("operation")),row.get("failure_kind").isNull()?Optional.empty():Optional.of(FailureKind.valueOf(StrictJson.text(row.get("failure_kind")))),
                    row.get("failure").isNull()?Optional.empty():Optional.of(Failure.fromJson(row.get("failure"))));}
    }
    public record Commit(String eventIdentity,BigInteger sequence) {
        public Commit { StrictJson.require(eventIdentity!=null&&eventIdentity.matches("[0-9a-f]{64}"),"actual commit digest required");uint(sequence,false); }
        public ObjectNode toJson(){return StrictJson.object().put("event_identity",eventIdentity).put("sequence",sequence.toString());}
        public static Commit fromJson(JsonNode value){var row=StrictJson.object(value,Set.of("event_identity","sequence"));return new Commit(StrictJson.text(row.get("event_identity")),decimal(row.get("sequence")));}
    }
    /** Immutable diagnostic DATA only. Decoding a snapshot does not create a mutable status owner or recover dirty originals. */
    public record Snapshot(BigInteger revision,BigInteger nextAttempt,List<Dirty> attempts,Optional<String> inheritedError,
            Optional<Failure> lastError,Optional<Commit> lastCommit) {
        public Snapshot { uint(revision,false);uint(nextAttempt,true);attempts=List.copyOf(attempts);Objects.requireNonNull(inheritedError);
            Objects.requireNonNull(lastError);Objects.requireNonNull(lastCommit);inheritedError.ifPresent(StrictJson::text);
            var ids=new LinkedHashSet<BigInteger>();for(var entry:attempts)StrictJson.require(ids.add(entry.attempt())&&entry.attempt().compareTo(nextAttempt)<0,"unique earlier dirty attempts required");
            StrictJson.require(!attempts.isEmpty()||inheritedError.isPresent()||lastError.isEmpty(),"cleared status cannot retain an unbound error");
            StrictJson.require(attempts.stream().noneMatch(entry->entry.failure().isPresent())||lastError.isPresent(),"dirty failures require the retained technical error"); }
        public boolean dirty(){return !attempts.isEmpty()||inheritedError.isPresent();}
        public boolean walBarrierRequired(){return attempts.stream().anyMatch(Dirty::sticky);}
        public Optional<String> driverStateError(){return lastError.map(Failure::display).or(()->inheritedError);}
        public ObjectNode toJson(){var row=StrictJson.object().put("schema",SCHEMA).put("revision",revision.toString()).put("next_attempt",nextAttempt.toString());
            var array=row.putArray("attempts");attempts.forEach(entry->array.add(entry.toJson()));
            if(inheritedError.isPresent())row.put("inherited_error",inheritedError.orElseThrow());else row.putNull("inherited_error");
            row.set("last_error",lastError.<JsonNode>map(Failure::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
            row.set("last_commit",lastCommit.<JsonNode>map(Commit::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));return row;}
        public static Snapshot fromJson(JsonNode value){var row=StrictJson.object(value,Set.of("schema","revision","next_attempt","attempts","inherited_error","last_error","last_commit"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&row.get("attempts").isArray(),"exact persistence snapshot schema and attempts array required");
            var attempts=new ArrayList<Dirty>();row.get("attempts").forEach(entry->attempts.add(Dirty.fromJson(entry)));
            return new Snapshot(decimal(row.get("revision")),decimal(row.get("next_attempt")),attempts,row.get("inherited_error").isNull()?Optional.empty():Optional.of(StrictJson.text(row.get("inherited_error"))),
                    row.get("last_error").isNull()?Optional.empty():Optional.of(Failure.fromJson(row.get("last_error"))),row.get("last_commit").isNull()?Optional.empty():Optional.of(Commit.fromJson(row.get("last_commit"))));}
    }
    private final Optional<String> inheritedError;
    private final LinkedHashMap<Attempt,Dirty> pending=new LinkedHashMap<>();
    private BigInteger revision=BigInteger.ZERO,next=BigInteger.ONE;
    private Optional<Failure> error=Optional.empty();private Optional<Commit> commit=Optional.empty();
    /** An inherited error without the corresponding retained dirty originals remains sticky in this owner. */
    public DriverPersistenceStatus(Optional<String> actualPriorError){inheritedError=Objects.requireNonNull(actualPriorError);actualPriorError.ifPresent(StrictJson::text);}
    public synchronized Attempt dirty(String operation){StrictJson.text(operation);uint(next.add(BigInteger.ONE),true);bump();
        var actual=new Attempt(this,next,operation);next=next.add(BigInteger.ONE);pending.put(actual,new Dirty(actual.id,operation,Optional.empty(),Optional.empty()));return actual;}
    public synchronized void failed(Attempt actual,Failure failure,FailureKind kind){Dirty before=requireAttempt(actual);Objects.requireNonNull(failure);Objects.requireNonNull(kind);
        // A later retry cannot turn a lost original or a WAL barrier into an ordinary retryable error.
        FailureKind effective=before.sticky()?before.failureKind().orElseThrow():kind;
        bump();pending.put(actual,new Dirty(actual.id,actual.operation,Optional.of(effective),Optional.of(failure)));error=Optional.of(failure);}
    /** Call only after the sole writer's requireCommitted and the actual Driver compare-and-publish both returned. */
    public synchronized void committed(List<Attempt> actualCovered,WriterContracts.Prepared prepared,WriterContracts.Receipt receipt){
        List<Attempt> covered=List.copyOf(actualCovered);Objects.requireNonNull(prepared);Objects.requireNonNull(receipt);
        StrictJson.require(!covered.isEmpty()&&new LinkedHashSet<>(covered).size()==covered.size(),"exact nonempty unique covered attempts required");
        for(var attempt:covered)requireAttempt(attempt);
        StrictJson.require(WriterContracts.DRIVER_READ_HISTORY_KIND.equals(prepared.request().kind())&&receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                &&receipt.eventIdentity().equals(prepared.request().identity()),"matching actual committed read-history replacement required");
        long eventSequence=Math.addExact(prepared.predecessor().state().sequence(),1);
        StrictJson.require(receipt.head().sequence()>=eventSequence&&receipt.head().machineId().equals(prepared.reduced().machineId()),"actual committed writer lineage required");
        var projected=prepared.reduced().toJson();projected.put("sequence",eventSequence);projected.put("last_event_identity",prepared.request().identity());
        if(receipt.disposition()==WriterContracts.Disposition.COMMITTED||receipt.head().sequence()==eventSequence)
            StrictJson.require(org.xar.ck3.control.continuity.ContinuityJson.same(receipt.head().toJson(),projected),"actual sequenced committed replacement differs");
        // ALREADY_COMMITTED may name a later canonical head; the sole caller must already have
        // proved that exact descendant with Session.requireCommitted before Driver CAS publication.
        bump();for(var attempt:covered)if(!pending.get(attempt).sticky())pending.remove(attempt);
        commit=Optional.of(new Commit(receipt.eventIdentity(),BigInteger.valueOf(receipt.head().sequence())));
        if(pending.isEmpty())error=Optional.empty(); // An inherited uncovered error still remains through driverStateError().
    }
    public synchronized Snapshot snapshot(){return new Snapshot(revision,next,new ArrayList<>(pending.values()),inheritedError,error,commit);}
    private Dirty requireAttempt(Attempt actual){Objects.requireNonNull(actual);StrictJson.require(actual.owner==this&&pending.containsKey(actual),"dirty attempt is not pending in this same status owner");return pending.get(actual);}
    private void bump(){uint(revision.add(BigInteger.ONE),false);revision=revision.add(BigInteger.ONE);}
    private static void uint(BigInteger value,boolean positive){StrictJson.require(value!=null&&value.compareTo(positive?BigInteger.ONE:BigInteger.ZERO)>=0&&value.compareTo(MAX)<=0,"uint64 diagnostic counter required");}
    private static BigInteger decimal(JsonNode value){return new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(value)).decimal());}
    private static String string(JsonNode value){StrictJson.require(value!=null&&value.isTextual(),"actual textual message required");return value.textValue();}
}
