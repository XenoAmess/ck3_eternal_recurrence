package org.xar.ck3.control.application.history;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.governance.succession.SuccessionCodec;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** The one complete legacy resume DATA consumer. It grants no file custody, Seed, Game or recovery permission.
 * The actual private Driver/WAL consumer must retain its original before and after this pure operation and
 * map every non-Loaded journaled result to JournalInvalid. Full history is always validated;
 * only explicit receipt mode can omit its materialization. */
public final class LegacyResumeNormalizer {
    private LegacyResumeNormalizer() { }
    public enum IgnoreReason { UNSUPPORTED_FORMAT, PIPE_MISMATCH }
    public enum Presence { MISSING, NULL, VALUE }
    public enum HistoryMaterialization { INCLUDE, OMIT }
    /** Caller selects native null only after its actual private frozen fixture was verified. */
    public enum LifecycleProjection { BOUND_OR_LEGACY, EXPLICIT_NATIVE_CAMPAIGN }
    public record FieldPresence(Presence checkpoint,Presence rollbackSingular,Presence rollbackPlural,
            Presence managedRestore,Presence expectation,Presence lifecycle,Presence campaignGoal) {
        public FieldPresence {for(var field:List.of(checkpoint,rollbackSingular,rollbackPlural,managedRestore,expectation,lifecycle,campaignGoal))Objects.requireNonNull(field);}
    }
    /** Null episode is a legitimate legacy DATA state, never an invented positive actor. */
    public record Episode(BigInteger characterId,String runId) {
        public Episode {Objects.requireNonNull(characterId);nonempty(runId,"driver state episode identity is malformed");}
    }
    public sealed interface Result permits Loaded,Ignored,Rejected { }
    public record Ignored(IgnoreReason reason) implements Result {public Ignored {Objects.requireNonNull(reason);}}
    public record Rejected(String driverError) implements Result {public Rejected {nonempty(driverError,"canonical driver error required");}}
    /** Factory-only normalized DATA. A caller cannot deserialize or construct this as an adoption proof. */
    public static final class Loaded implements Result {
        private final int formatVersion;private final String pipe;private final BigInteger pid;private final Optional<Episode> episode;
        private final Optional<List<Obj>> history;private final Obj payload;private final Value lifecycle;private final boolean lifecycleMigration,rollbackMigration;
        private final FieldPresence presence;
        private Loaded(int version,String pipe,BigInteger pid,Optional<Episode> episode,Optional<List<Obj>> history,Obj payload,
                Value lifecycle,boolean lifecycleMigration,boolean rollbackMigration,FieldPresence presence) {
            formatVersion=version;this.pipe=pipe;this.pid=pid;this.episode=episode;this.history=history.map(List::copyOf);this.payload=payload;
            this.lifecycle=lifecycle;this.lifecycleMigration=lifecycleMigration;this.rollbackMigration=rollbackMigration;this.presence=presence;
        }
        public int formatVersion(){return formatVersion;}
        public String expectedPipe(){return pipe;}
        public BigInteger persistedBridgePid(){return pid;}
        public Optional<Episode> episode(){return episode;}
        public List<Obj> commandHistory(){return history.orElseThrow(()->new IllegalStateException("receipt-only normalization did not materialize history"));}
        public HistoryMaterialization historyMaterialization(){return history.isPresent()?HistoryMaterialization.INCLUDE:HistoryMaterialization.OMIT;}
        public Obj normalizedPayload(){return payload;}
        /** Explicit original JSON null is DATA, distinct from missing legacy migration. */
        public Value normalizedLifecycle(){return lifecycle;}
        public boolean lifecycleMigrationRequired(){return lifecycleMigration;}
        public boolean rollbackMigrationRequired(){return rollbackMigration;}
        public FieldPresence originalPresence(){return presence;}
        public byte[] encode(){return DriverJson.encode(payload);}
    }
    public static Result normalize(Obj originalFullPayload,String expectedPipe) {
        return normalize(originalFullPayload,expectedPipe,HistoryMaterialization.INCLUDE);
    }
    public static Result normalize(Obj originalFullPayload,String expectedPipe,HistoryMaterialization history) {
        return normalizeValue(originalFullPayload,expectedPipe,history,LifecycleProjection.BOUND_OR_LEGACY);
    }
    public static Result normalize(Obj originalFullPayload,String expectedPipe,LifecycleProjection lifecycle) {
        return normalizeValue(originalFullPayload,expectedPipe,HistoryMaterialization.INCLUDE,lifecycle);
    }
    /** Explicit projection retains the caller's original finite history materialization role. */
    public static Result normalize(Obj originalFullPayload,String expectedPipe,HistoryMaterialization history,LifecycleProjection lifecycle) {
        return normalizeValue(originalFullPayload,expectedPipe,history,lifecycle);
    }
    /** Generic JSON boundary for refusal regression; actual Root callers supply the original complete object. */
    public static Result normalizeValue(Value payload,String expectedPipe) {
        return normalizeValue(payload,expectedPipe,HistoryMaterialization.INCLUDE,LifecycleProjection.BOUND_OR_LEGACY);
    }
    private static Result normalizeValue(Value payload,String expectedPipe,HistoryMaterialization materialization,LifecycleProjection projection) {
        Objects.requireNonNull(expectedPipe);
        Objects.requireNonNull(materialization);
        Objects.requireNonNull(projection);
        try {
            require(payload instanceof Obj,"driver state must be a JSON object");Obj original=(Obj)payload;
            Value version=original.get("format_version");
            if(!(version instanceof IntegerValue integer)||!List.of(BigInteger.ONE,BigInteger.TWO).contains(integer.value()))return new Ignored(IgnoreReason.UNSUPPORTED_FORMAT);
            if(!new Text(expectedPipe).equals(original.get("pipe_name")))return new Ignored(IgnoreReason.PIPE_MISMATCH);
            BigInteger pid=integer(original.get("bridge_pid"),"driver state bridge_pid is malformed");
            require(pid.signum()>0,"driver state bridge_pid is malformed");
            Value actor=nullable(original,"episode_character_id"),run=nullable(original,"episode_run_id");Optional<Episode> episode;
            if(actor==Nil.INSTANCE){require(run==Nil.INSTANCE,"driver state has a run without a character");episode=Optional.empty();}
            else {require(actor instanceof IntegerValue&&run instanceof Text text&&!text.value().isEmpty(),"driver state episode identity is malformed");episode=Optional.of(new Episode(((IntegerValue)actor).value(),((Text)run).value()));}
            require(original.get("command_history") instanceof Arr,"driver state command_history is malformed");
            List<Obj> rawHistory=history((Arr)original.get("command_history"));
            Value checkpoint=nullable(original,"last_checkpoint");require(checkpoint==Nil.INSTANCE||checkpoint instanceof Obj,"driver state checkpoint is malformed");
            boolean pluralPresent=original.members().containsKey("rollback_war_failures");
            require(!pluralPresent||original.get("rollback_war_failures") instanceof Arr,"driver state rollback_war_failures is malformed");
            List<Obj> candidates=new ArrayList<>();
            if(pluralPresent)for(Value item:((Arr)original.get("rollback_war_failures")).items())RollbackWarFailures.normalizeLegacyDriverFailure(item).ifPresent(candidates::add);
            else RollbackWarFailures.normalizeLegacyDriverFailure(nullable(original,"rollback_war_failure")).ifPresent(candidates::add);
            List<Obj> failures=RollbackWarFailures.boundedLegacyDriverFailures(candidates);
            Value finalCheckpoint=checkpoint,finalRun=run;
            failures=failures.stream().filter(failure->finalCheckpoint instanceof Obj saved
                    &&Objects.equals(failure.get("checkpoint_sha256"),saved.get("sha256"))&&Objects.equals(failure.get("episode_run_id"),finalRun)).toList();
            boolean migration=!pluralPresent&&checkpoint instanceof Obj&&run instanceof Text text&&!text.value().isEmpty();
            if(migration&&!failures.isEmpty()) {
                List<Obj> completed=RollbackWarFailures.deriveCompletedLegacyDriverFailures(rawHistory,(Obj)checkpoint,scopeSnapshot(failures.getFirst()),((Text)run).value(),2);
                failures=RollbackWarFailures.boundedLegacyDriverFailures(failures,completed);migration=false;
            }
            Value managed=normalizeManaged(nullable(original,"managed_restore_transaction"),checkpoint,rawHistory,pid,actor,run);
            Value expectation=nullable(original,"succession_expectation");
            if(expectation!=Nil.INSTANCE) {
                expectation=DriverJson.object(SuccessionCodec.normalize(DriverJson.encode(expectation)),SuccessionCodec.MAX_BYTES);
                Obj binding=object(((Obj)expectation).get("binding"),"succession expectation binding");
                require(Objects.equals(binding.get("episode_character_id"),actor)&&Objects.equals(binding.get("episode_run_id"),run),"driver succession expectation changed episode");
            }
            boolean lifecycleMigration=!original.members().containsKey("succession_lifecycle");
            Value lifecycle;
            if(projection==LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN) {
                require(!lifecycleMigration&&original.get("succession_lifecycle")==Nil.INSTANCE,
                        "explicit native_campaign requires original present JSON null lifecycle");
                lifecycle=Nil.INSTANCE;
            } else lifecycle=DriverJson.object(lifecycleMigration?SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue())
                    :SuccessionLifecycleCodec.normalize(DriverJson.encode(original.get("succession_lifecycle"))),SuccessionLifecycleCodec.MAX_BYTES);
            Value goal=normalizeGoal(nullable(original,"campaign_goal"));
            Optional<List<Obj>> projected=materialization==HistoryMaterialization.INCLUDE?Optional.of(projectHistory(rawHistory)):Optional.empty();
            var output=new LinkedHashMap<String,Value>();output.put("format_version",version);output.put("bridge_pid",new IntegerValue(pid));
            output.put("episode_character_id",actor);output.put("episode_run_id",run);projected.ifPresent(rows->output.put("command_history",new Arr(new ArrayList<Value>(rows))));
            output.put("last_checkpoint",checkpoint);output.put("rollback_war_failure",failures.isEmpty()?Nil.INSTANCE:failures.getFirst());
            output.put("rollback_war_failures",new Arr(new ArrayList<Value>(failures)));output.put("rollback_war_failures_migration_required",new Bool(migration));
            output.put("managed_restore_transaction",managed);output.put("succession_expectation",expectation);output.put("succession_lifecycle",lifecycle);
            output.put("campaign_goal",goal);output.put("succession_lifecycle_migration_required",new Bool(lifecycleMigration));
            var presence=new FieldPresence(presence(original,"last_checkpoint"),presence(original,"rollback_war_failure"),presence(original,"rollback_war_failures"),
                    presence(original,"managed_restore_transaction"),presence(original,"succession_expectation"),presence(original,"succession_lifecycle"),presence(original,"campaign_goal"));
            return new Loaded(((IntegerValue)version).value().intValueExact(),expectedPipe,pid,episode,projected,new Obj(output),lifecycle,lifecycleMigration,migration,presence);
        }catch(IllegalArgumentException malformed){return new Rejected(malformed.getMessage()==null?"driver state failed the canonical resume consumer":malformed.getMessage());}
    }
    private static List<Obj> history(Arr history) {
        List<Obj> result=new ArrayList<>();int index=0;
        for(Value value:history.items()) {
            index++;require(value instanceof Obj,"driver state command history is malformed");Obj row=(Obj)value;
            require(new IntegerValue(BigInteger.valueOf(index)).equals(row.get("index"))&&row.get("command") instanceof Text command&&!command.value().isEmpty()
                    &&row.get("ok") instanceof Bool,"driver state command history is malformed");result.add(row);
        }return List.copyOf(result);
    }
    /** The original resume view removes only inactive legacy objective rows, preserving every other raw field. */
    private static List<Obj> projectHistory(List<Obj> history) {
        List<Obj> rows=new ArrayList<>();
        for(Obj row:history) {
            if(!(row.get("result") instanceof Obj original)){rows.add(row);continue;}
            Obj result=original;
            for(String key:List.of("war_progress_before","war_progress_after")) {
                if(!(original.get(key) instanceof Obj summary)||!(summary.get("wars") instanceof Arr wars))continue;
                List<Value> projected=new ArrayList<>();boolean changed=false;
                for(Value value:wars.items()) {
                    if(value instanceof Obj war&&war.get("objective_province_states") instanceof Arr states) {
                        var active=states.items().stream().filter(state->state instanceof Obj object&&object.get("active_siege") instanceof Obj).toList();
                        projected.add(war.with("objective_province_states",new Arr(active)));changed=true;
                    }else projected.add(value);
                }if(changed)result=result.with(key,summary.with("wars",new Arr(projected)));
            }rows.add(result==original?row:row.with("result",result));
        }return List.copyOf(rows);
    }
    private static Value normalizeManaged(Value value,Value checkpoint,List<Obj> history,BigInteger pid,Value actor,Value run) {
        if(!(value instanceof Obj transaction)||!(checkpoint instanceof Obj saved)||DriverHistoryProjection.checkpointIdentity(saved).isEmpty())return Nil.INSTANCE;
        Value source=transaction.get("source_bridge_pid"),replacement=nullable(transaction,"replacement_bridge_pid");
        Value digest=transaction.get("checkpoint_sha256"),size=transaction.get("checkpoint_size"),date=transaction.get("checkpoint_date_raw"),ordinal=transaction.get("history_index");
        var anchor=DriverHistoryProjection.checkpointHistoryIndex(saved,history);
        boolean valid=new Text("awaiting_checkpoint_rebind").equals(transaction.get("status"))
                &&transaction.get("request_id") instanceof Text request&&request.value().startsWith("restore-")
                &&positive(source)&&(replacement==Nil.INSTANCE||positive(replacement))
                &&new IntegerValue(pid).equals(replacement==Nil.INSTANCE?source:replacement)
                &&digest instanceof Text sha&&sha.value().matches("[0-9a-f]{64}")&&positive(size)&&date instanceof IntegerValue&&ordinal instanceof IntegerValue
                &&sameNullableInteger(nullable(transaction,"episode_character_id"),actor)&&Objects.equals(nullable(transaction,"episode_run_id"),run)
                &&Objects.equals(saved.get("sha256"),digest)&&Objects.equals(saved.get("size"),size)&&Objects.equals(saved.get("date_raw"),date)
                &&anchor.isPresent()&&new IntegerValue(BigInteger.valueOf(anchor.getAsInt())).equals(ordinal);
        return valid?transaction:Nil.INSTANCE;
    }
    /** Original legacy goal DATA ingress is wider than M7's planning GoalCodec; no planning qualification is granted. */
    private static Value normalizeGoal(Value value) {
        if(value==Nil.INSTANCE)return value;
        require(value instanceof Obj,"ordinary campaign goal is malformed");Obj goal=(Obj)value;
        require(new IntegerValue(BigInteger.ONE).equals(goal.get("format_version"))&&new Text("dynasty_continuity").equals(goal.get("goal_key"))
                &&goal.get("campaign_id") instanceof Text campaign&&!campaign.value().isEmpty(),"ordinary campaign goal is malformed");
        for(String key:List.of("origin_character_id","current_character_id")) {
            Value v=goal.get(key);
            require(v instanceof IntegerValue,"ordinary campaign goal "+key+" is malformed");
            BigInteger bi=((IntegerValue)v).value();
            // Wide positive legacy DATA is retained; bound character IDs use the shared domain.
            if(bi.signum()<=0)NativeCharacterId.of(bi);
        }
        require(goal.get("progress") instanceof Obj,"ordinary campaign goal progress is malformed");Obj progress=(Obj)goal.get("progress");
        require(progress.get("reconciled_successions") instanceof IntegerValue count&&count.value().signum()>=0
                &&(nullable(progress,"last_succession")==Nil.INSTANCE||progress.get("last_succession") instanceof Obj),"ordinary campaign goal progress is malformed");return goal;
    }
    private static Obj scopeSnapshot(Obj failure) {
        Obj army=new Obj(Map.of("army_id",failure.get("army_id"),"current_province_id",failure.get("restored_origin_province_id"),
                "move_target_province_id",Nil.INSTANCE,"route_province_ids",new Arr(List.of()),"army_state",new Text("regular"),"controllable",new Bool(true)));
        Value date=failure.members().containsKey("restored_date_raw")?failure.get("restored_date_raw"):nullable(failure,"checkpoint_date_raw");
        return new Obj(Map.of("date_raw",date,"player_armies",new Arr(List.of(army)),"active_wars",new Arr(List.of(new Obj(Map.of("war_id",failure.get("war_id"),"allied_armies",new Arr(List.of(army))))))));
    }
    private static Presence presence(Obj value,String key){return !value.members().containsKey(key)?Presence.MISSING:value.get(key)==Nil.INSTANCE?Presence.NULL:Presence.VALUE;}
    private static Value nullable(Obj value,String key){return value.members().containsKey(key)?value.get(key):Nil.INSTANCE;}
    private static boolean sameNullableInteger(Value first,Value second){return first==Nil.INSTANCE&&second==Nil.INSTANCE||first instanceof IntegerValue&&second instanceof IntegerValue&&first.equals(second);}
    private static boolean positive(Value value){return value instanceof IntegerValue integer&&integer.value().signum()>0;}
    private static BigInteger integer(Value value,String error){require(value instanceof IntegerValue,error);return ((IntegerValue)value).value();}
    private static Obj object(Value value,String error){require(value instanceof Obj,error);return (Obj)value;}
    private static void nonempty(String value,String error){require(value!=null&&!value.isEmpty(),error);}
    private static void require(boolean condition,String error){StrictJson.require(condition,error);}
}
