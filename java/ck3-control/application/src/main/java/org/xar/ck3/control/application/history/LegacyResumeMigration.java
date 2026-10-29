package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Loaded;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.HistoryMaterialization;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Sole legacy pending-migration DATA reducer. It grants no writer, file custody, Seed, Game or cold admission.
 * The actual private import resolver owns every input's original source and revalidates it before publication. */
public final class LegacyResumeMigration {
    private LegacyResumeMigration() { }
    public enum SaveDirectoryState { CONFIGURED, ABSENT }
    public enum QueueStatus { MISSING, FAILED, PRESENT, UNAVAILABLE }
    public enum Pending { EPISODE_BINDING, ROLLBACK_MIGRATION, MANAGED_RESTORE_REQUEST }
    public enum ColdCause { DIFFERENT_PID, MANAGED_TRANSACTION_CROSSED_PROCESS }
    public enum Reason { LEGACY_LIFECYCLE_INCOMPATIBLE, PERSISTED_LIFECYCLE_MISMATCH, QUEUE_OBSERVATION_MISMATCH, MALFORMED_INPUT }
    /** Typed DATA only: runtime's private physical queue observation remains mandatory in the actual resolver. */
    public record ManagedQueueData(String requestId,QueueStatus status) {
        public ManagedQueueData {StrictJson.text(requestId);Objects.requireNonNull(status);}
    }
    /** Supplied by the Root's existing single-attempt identity producer, never randomly minted here. */
    public record BindingIdentity(BigInteger characterId,String runId) {
        public BindingIdentity {characterId=NativeCharacterId.of(characterId).asBigInteger();StrictJson.text(runId);}
    }
    /** The one typed DATA projection. Explicit native_campaign has exact JSON null, never a default binding. */
    public sealed interface FrozenLifecycle permits BoundLifecycle,ExplicitNativeCampaign { }
    public record BoundLifecycle(SuccessionLifecycleBinding binding) implements FrozenLifecycle {
        public BoundLifecycle {Objects.requireNonNull(binding);}
    }
    public record ExplicitNativeCampaign() implements FrozenLifecycle { }
    public record Request(Loaded original,BigInteger actualBridgePid,FrozenLifecycle frozenLifecycle,
            SaveDirectoryState saveDirectory,Optional<Obj> actualFirstPlayableSnapshot,Optional<ManagedQueueData> managedQueue) {
        public Request {
            Objects.requireNonNull(original);Objects.requireNonNull(actualBridgePid);Objects.requireNonNull(frozenLifecycle);
            Objects.requireNonNull(saveDirectory);Objects.requireNonNull(actualFirstPlayableSnapshot);Objects.requireNonNull(managedQueue);
            require(actualBridgePid.signum()>0,"actual bridge PID required");
            require(original.historyMaterialization()==HistoryMaterialization.INCLUDE,"complete original history is mandatory; OMIT is never an empty-history import");
        }
        /** Preserves the existing ordinary typed API; null never selects native_campaign. */
        public Request(Loaded original,BigInteger actualBridgePid,SuccessionLifecycleBinding boundLifecycle,
                SaveDirectoryState saveDirectory,Optional<Obj> actualFirstPlayableSnapshot,Optional<ManagedQueueData> managedQueue) {
            this(original,actualBridgePid,new BoundLifecycle(boundLifecycle),saveDirectory,actualFirstPlayableSnapshot,managedQueue);
        }
    }
    public sealed interface Plan permits SamePidData,PendingColdData,NeedsManagedQueue,RequiredBinding,Rejected { }
    public static final class SamePidData implements Plan {
        private final Obj payload;private final String pipe;private final Set<Pending> pending;
        private final boolean anchorUpgraded,transactionDisarmed;private final boolean anchorReady;
        private SamePidData(Obj payload,String pipe,Set<Pending> pending,boolean upgraded,boolean disarmed,boolean anchorReady) {
            this.payload=payload;this.pipe=pipe;this.pending=Set.copyOf(pending);anchorUpgraded=upgraded;transactionDisarmed=disarmed;this.anchorReady=anchorReady;
        }
        public Obj normalizedPayload(){return payload;}
        public Set<Pending> pending(){return pending;}
        public boolean anchorUpgraded(){return anchorUpgraded;}
        public boolean transactionDisarmed(){return transactionDisarmed;}
        public boolean anchorReady(){return anchorReady;}
        /** Complete modern-format DATA only. The caller still needs its private original/physical/native/writer admission. */
        public Obj modernDriverPayload() {
            if(!pending.isEmpty())throw new IllegalStateException("legacy migration still has pending original work: "+pending);
            var fields=new java.util.LinkedHashMap<>(payload.members());fields.put("pipe_name",new Text(pipe));
            fields.remove("rollback_war_failures_migration_required");fields.remove("succession_lifecycle_migration_required");return new Obj(fields);
        }
    }
    public static final class PendingColdData implements Plan {
        private final Obj candidate;private final ColdCause cause;private final boolean anchorReady;
        private PendingColdData(Obj candidate,ColdCause cause,boolean ready){this.candidate=candidate;this.cause=cause;anchorReady=ready;}
        public Obj candidate(){return candidate;}
        public ColdCause cause(){return cause;}
        /** The original structural predicate only; never file identity, SAVE hash, replacement custody or reducer permission. */
        public boolean anchorReady(){return anchorReady;}
    }
    public static final class NeedsManagedQueue implements Plan {
        private final Request request;private final String requestId;
        private NeedsManagedQueue(Request request,String id){this.request=request;requestId=id;}
        public String requestId(){return requestId;}
        public Obj normalizedPayload(){return request.original().normalizedPayload();}
        public Optional<QueueStatus> lastStatus(){return request.managedQueue().map(ManagedQueueData::status);}
    }
    public static final class RequiredBinding implements Plan {
        private final Request request;private final Obj payload;private final BigInteger actor;private final Set<Pending> pending;
        private RequiredBinding(Request request,Obj payload,BigInteger actor,Set<Pending> pending){this.request=request;this.payload=payload;this.actor=actor;this.pending=Set.copyOf(pending);}
        public Obj normalizedPayload(){return payload;}
        public BigInteger actualCharacterId(){return actor;}
        public Set<Pending> pending(){return pending;}
    }
    public static final class Rejected implements Plan {
        private final Reason reason;private final String diagnostic;private final Obj original;
        private Rejected(Reason reason,String diagnostic,Obj original){this.reason=reason;this.diagnostic=diagnostic;this.original=original;}
        public Reason reason(){return reason;}
        public String diagnostic(){return diagnostic;}
        public Obj originalPayload(){return original;}
    }
    public static Plan resolve(Request request){return resolve(request,Optional.empty());}
    public static Plan withManagedQueue(NeedsManagedQueue pending,ManagedQueueData actualQueue) {
        Objects.requireNonNull(pending);Objects.requireNonNull(actualQueue);Request r=pending.request;
        return resolve(new Request(r.original(),r.actualBridgePid(),r.frozenLifecycle(),r.saveDirectory(),r.actualFirstPlayableSnapshot(),Optional.of(actualQueue)));
    }
    public static Plan bind(RequiredBinding pending,BindingIdentity actualRootMinted) {
        Objects.requireNonNull(pending);Objects.requireNonNull(actualRootMinted);
        require(pending.actualCharacterId().equals(actualRootMinted.characterId()),"single-attempt binding differs from the actual native character");
        return resolve(pending.request,Optional.of(actualRootMinted));
    }
    private static Plan resolve(Request request,Optional<BindingIdentity> binding) {
        Objects.requireNonNull(request);Loaded original=request.original();Obj source=original.normalizedPayload();
        try {
            FrozenLifecycle projection=request.frozenLifecycle();Value frozen=lifecycleData(projection);
            if(original.lifecycleMigrationRequired()&&(!(projection instanceof BoundLifecycle bound)
                    ||bound.binding().profile()!=SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE))
                return rejected(Reason.LEGACY_LIFECYCLE_INCOMPATIBLE,"legacy state requires the actual frozen rogue xar_on profile",source);
            if(projection instanceof ExplicitNativeCampaign&&(!source.members().containsKey("succession_lifecycle")
                    ||source.get("succession_lifecycle")!=Nil.INSTANCE))
                return rejected(Reason.PERSISTED_LIFECYCLE_MISMATCH,"explicit native_campaign requires persisted explicit null lifecycle",source);
            if(!original.lifecycleMigrationRequired()&&!frozen.equals(original.normalizedLifecycle()))
                return rejected(Reason.PERSISTED_LIFECYCLE_MISMATCH,"persisted lifecycle differs from the actual frozen profile",source);
            Value transaction=value(source,"managed_restore_transaction");
            boolean crossed=transaction instanceof Obj tx&&(new IntegerValue(request.actualBridgePid()).equals(value(tx,"replacement_bridge_pid"))
                    ||!new IntegerValue(request.actualBridgePid()).equals(tx.get("source_bridge_pid")));
            if(!original.persistedBridgePid().equals(request.actualBridgePid())||crossed) {
                require(binding.isEmpty(),"a pending physical cold candidate cannot accept a new episode binding");
                return new PendingColdData(source,crossed?ColdCause.MANAGED_TRANSACTION_CROSSED_PROCESS:ColdCause.DIFFERENT_PID,
                        coldCandidateReady(source,request.saveDirectory()));
            }
            boolean disarmed=false;
            if(transaction instanceof Obj tx&&value(tx,"replacement_bridge_pid")==Nil.INSTANCE) {
                String requestId=((Text)tx.get("request_id")).value();
                if(request.managedQueue().isEmpty())return new NeedsManagedQueue(request,requestId);
                ManagedQueueData queue=request.managedQueue().orElseThrow();
                if(!queue.requestId().equals(requestId))return rejected(Reason.QUEUE_OBSERVATION_MISMATCH,"actual managed queue belongs to another request",source);
                if(queue.status()==QueueStatus.UNAVAILABLE)return new NeedsManagedQueue(request,requestId);
                if(queue.status()==QueueStatus.MISSING||queue.status()==QueueStatus.FAILED){transaction=Nil.INSTANCE;disarmed=true;}
            }else if(request.managedQueue().isPresent()) {
                return rejected(Reason.QUEUE_OBSERVATION_MISMATCH,"there is no original orphan candidate for this queue observation",source);
            }
            List<Obj> history=original.commandHistory();Value checkpoint=value(source,"last_checkpoint"),upgraded=checkpoint;
            // Python upgrades at hot adoption, before an unbound first-map identity is later minted.
            if(checkpoint instanceof Obj saved&&original.episode().isPresent()) {
                var episode=original.episode().orElseThrow();upgraded=DriverHistoryProjection.upgradeCheckpointAnchor(saved,history,episode.characterId(),episode.runId());
            }
            Obj output=source.with("format_version",number(2)).with("bridge_pid",new IntegerValue(request.actualBridgePid()))
                    .with("last_checkpoint",upgraded).with("managed_restore_transaction",transaction)
                    .with("succession_lifecycle",frozen).with("succession_lifecycle_migration_required",new Bool(false));
            boolean ready=request.actualFirstPlayableSnapshot().map(LegacyResumeMigration::mapReady).orElse(false);
            if(truth(source,"rollback_war_failures_migration_required")&&ready) {
                Obj snapshot=request.actualFirstPlayableSnapshot().orElseThrow();
                List<Obj> failures=objects((Arr)source.get("rollback_war_failures"));
                List<Obj> completed=upgraded instanceof Obj saved&&value(output,"episode_run_id") instanceof Text run
                        ?RollbackWarFailures.deriveCompletedLegacyDriverFailures(history,saved,snapshot,run.value(),2):List.of();
                List<Obj> merged=RollbackWarFailures.boundedLegacyDriverFailures(failures,completed);
                output=output.with("rollback_war_failures",array(merged)).with("rollback_war_failure",merged.isEmpty()?Nil.INSTANCE:merged.getFirst())
                        .with("rollback_war_failures_migration_required",new Bool(false));
            }
            EnumSet<Pending> pending=EnumSet.noneOf(Pending.class);
            if(truth(output,"rollback_war_failures_migration_required"))pending.add(Pending.ROLLBACK_MIGRATION);
            if(transaction!=Nil.INSTANCE)pending.add(Pending.MANAGED_RESTORE_REQUEST);
            if(original.episode().isEmpty()) {
                pending.add(Pending.EPISODE_BINDING);
                Optional<BigInteger> actor=ready?actualActor(request.actualFirstPlayableSnapshot().orElseThrow()):Optional.empty();
                if(binding.isPresent()) {
                    require(actor.isPresent()&&actor.orElseThrow().equals(binding.orElseThrow().characterId()),"binding requires the same actual playable native character");
                    BindingIdentity identity=binding.orElseThrow();output=output.with("episode_character_id",new IntegerValue(identity.characterId())).with("episode_run_id",new Text(identity.runId()));
                    pending.remove(Pending.EPISODE_BINDING);
                }else if(actor.isPresent())return new RequiredBinding(request,output,actor.orElseThrow(),pending);
            }else require(binding.isEmpty(),"an already bound original episode cannot be silently rebound");
            return new SamePidData(output,original.expectedPipe(),pending,!Objects.equals(checkpoint,upgraded),disarmed,
                    coldCandidateReady(output,request.saveDirectory()));
        }catch(IllegalArgumentException malformed) {
            return rejected(Reason.MALFORMED_INPUT,malformed.getMessage()==null?"legacy migration data is malformed":malformed.getMessage(),source);
        }
    }
    /** Sole memory-to-JSON domain projection, shared by the physical Root consumer. */
    public static Value lifecycleData(FrozenLifecycle frozen) {
        Objects.requireNonNull(frozen);
        if(frozen instanceof ExplicitNativeCampaign)return Nil.INSTANCE;
        return DriverJson.object(SuccessionLifecycleCodec.encode(((BoundLifecycle)frozen).binding()),SuccessionLifecycleCodec.MAX_BYTES);
    }
    private static boolean coldCandidateReady(Obj candidate,SaveDirectoryState directory) {
        if(directory!=SaveDirectoryState.CONFIGURED||!number(2).equals(candidate.get("format_version"))
                ||!(candidate.get("episode_character_id") instanceof IntegerValue actor)
                ||!(candidate.get("episode_run_id") instanceof Text run)||run.value().isEmpty()
                ||!(candidate.get("command_history") instanceof Arr rows)||!(candidate.get("last_checkpoint") instanceof Obj saved))return false;
        if(!actor.equals(value(saved,"episode_character_id"))||!run.equals(value(saved,"episode_run_id")))return false;
        return DriverHistoryProjection.checkpointHistoryIndex(saved,objects(rows)).isPresent();
    }
    private static boolean mapReady(Obj snapshot) {
        Value state=value(snapshot,"map_ready");
        require(state==Nil.INSTANCE||state instanceof Bool,"actual map_ready must retain its native boolean type");
        if(new Bool(true).equals(state))require(snapshot.get("date_raw") instanceof IntegerValue,"actual playable native date requires an integer token");
        return new Bool(true).equals(state);
    }
    private static Optional<BigInteger> actualActor(Obj snapshot) {
        if(!(snapshot.get("played_character") instanceof Obj actor))return Optional.empty();Value id=value(actor,"character_id");
        if(id==Nil.INSTANCE)return Optional.empty();
        require(id instanceof IntegerValue,"actual native character requires an integer token");BigInteger exact=((IntegerValue)id).value();
        // Native -1 is absence; zero and every other signed-i32 identity retain their original value.
        return exact.equals(BigInteger.valueOf(-1))?Optional.empty():Optional.of(NativeCharacterId.of(exact).asBigInteger());
    }
    private static List<Obj> objects(Arr rows) {
        List<Obj> result=new ArrayList<>();for(Value value:rows.items()){require(value instanceof Obj,"complete original object rows required");result.add((Obj)value);}return List.copyOf(result);
    }
    private static Arr array(List<Obj> rows){return new Arr(new ArrayList<Value>(rows));}
    private static boolean truth(Obj row,String field){require(row.get(field) instanceof Bool,"canonical migration flag must remain boolean: "+field);return ((Bool)row.get(field)).value();}
    private static Value value(Obj row,String field){return row.members().containsKey(field)?row.get(field):Nil.INSTANCE;}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Rejected rejected(Reason reason,String diagnostic,Obj source){return new Rejected(reason,diagnostic,source);}
    private static void require(boolean condition,String diagnostic){StrictJson.require(condition,diagnostic);}
}
