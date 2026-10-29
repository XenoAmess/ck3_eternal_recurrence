package org.xar.ck3.control.continuity;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.contracts.NativeCharacterId;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One pure, closed original-resume transition. Descriptor DATA never grants physical adoption. */
public final class OriginalLegacyResume {
    public static final String KIND="JAVA_ORIGINAL_LEGACY_RESUME_V1";
    public static final String STATE_FIELD="java_legacy_resume";
    public static final String SCHEMA="xar.java-original-legacy-resume/v1";
    private static final Set<String> FIELDS=Set.of("schema","evidence_id","source","machine_id","expected_head_sha256",
            "before_history","route","session_id","pipe_name","game","actor_id","episode_run_id","driver_version","episode_epoch",
            "original_driver","canonical_original","full_driver","original_hello","original_native","canonical_native",
            "migration_plan","managed_queue","original_inputs");
    private OriginalLegacyResume(){ }

    public enum Route { SAME_PID, BIND_UNBOUND, COLD_CHECKPOINT, COLD_REJECTED_NEW_EPISODE }
    public sealed interface BeforeHistory permits MissingHistory, BoundHistory { }
    public record MissingHistory() implements BeforeHistory { }
    public record BoundHistory(ExactRef original) implements BeforeHistory {
        public BoundHistory {reference(original);}
    }
    /** Full birth is decimal text throughout the cross-runtime descriptor. */
    public record Game(long pid,String creationFiletime) {
        public Game {
            StrictJson.integer(StrictJson.object().put("pid",pid).get("pid"),1,0xffff_ffffL);
            var birth=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(creationFiletime);
            StrictJson.require(new BigInteger(birth.decimal()).signum()>0,"positive actual Game birth required");
        }
    }
    public record Delta(ExactRef source,String machineId,String expectedHeadSha256,BeforeHistory beforeHistory,Route route,
            String sessionId,String pipeName,Game game,long actorId,String episodeRunId,long driverVersion,long episodeEpoch,
            ExactRef originalDriver,ExactRef canonicalOriginal,ExactRef fullDriver,ExactRef originalHello,ExactRef originalNative,
            ExactRef canonicalNative,ExactRef migrationPlan,Optional<ExactRef> managedQueue,List<ExactRef> originalInputs) {
        public Delta {
            reference(source);StrictJson.text(machineId);WriterContracts.requireDigest(expectedHeadSha256);
            Objects.requireNonNull(beforeHistory);Objects.requireNonNull(route);StrictJson.text(sessionId);StrictJson.text(pipeName);
            Objects.requireNonNull(game);NativeCharacterId.of(actorId);StrictJson.text(episodeRunId);
            StrictJson.safe(driverVersion,0);StrictJson.safe(episodeEpoch,0);
            for(ExactRef ref:List.of(originalDriver,canonicalOriginal,fullDriver,originalHello,originalNative,canonicalNative,migrationPlan))reference(ref);
            managedQueue=Objects.requireNonNull(managedQueue);managedQueue.ifPresent(OriginalLegacyResume::reference);
            originalInputs=List.copyOf(originalInputs);StrictJson.require(!originalInputs.isEmpty()&&originalInputs.size()<=48,"complete finite actual input closure required");
            originalInputs.forEach(OriginalLegacyResume::reference);
            StrictJson.require(originalInputs.stream().distinct().count()==originalInputs.size(),"unique original inputs required");
        }
        public List<ExactRef> evidence() {
            var refs=new LinkedHashSet<ExactRef>();refs.add(source);refs.addAll(originalInputs);
            if(beforeHistory instanceof BoundHistory bound)refs.add(bound.original());
            refs.addAll(List.of(originalDriver,canonicalOriginal,fullDriver,originalHello,originalNative,canonicalNative,migrationPlan));
            managedQueue.ifPresent(refs::add);StrictJson.require(refs.size()<=64,"finite complete resume source closure required");return List.copyOf(refs);
        }
        public ObjectNode toJson() {
            ObjectNode row=fields();row.put("evidence_id","legacy-resume:"+ContinuityJson.digest(row));return row;
        }
        private ObjectNode fields() {
            var row=StrictJson.object();row.put("schema",SCHEMA);row.set("source",source.toJson());row.put("machine_id",machineId);
            row.put("expected_head_sha256",expectedHeadSha256);var prior=row.putObject("before_history");
            switch(beforeHistory) {
                case MissingHistory ignored->prior.put("kind","ABSENT");
                case BoundHistory bound->{prior.put("kind","BOUND");prior.set("original",bound.original().toJson());}
            }
            row.put("route",route.name());row.put("session_id",sessionId);row.put("pipe_name",pipeName);
            var generation=row.putObject("game");generation.put("pid",game.pid());generation.put("creation_filetime",game.creationFiletime());
            row.put("actor_id",actorId);row.put("episode_run_id",episodeRunId);row.put("driver_version",driverVersion);row.put("episode_epoch",episodeEpoch);
            row.set("original_driver",originalDriver.toJson());row.set("canonical_original",canonicalOriginal.toJson());row.set("full_driver",fullDriver.toJson());
            row.set("original_hello",originalHello.toJson());row.set("original_native",originalNative.toJson());row.set("canonical_native",canonicalNative.toJson());
            row.set("migration_plan",migrationPlan.toJson());row.set("managed_queue",managedQueue.<JsonNode>map(ExactRef::toJson).orElseGet(()->com.fasterxml.jackson.databind.node.NullNode.instance));
            var inputs=row.putArray("original_inputs");originalInputs.forEach(ref->inputs.add(ref.toJson()));return row;
        }
        public WriterContracts.Request request(){return new WriterContracts.Request(KIND,ContinuityJson.canonical(toJson()),evidence());}
    }

    public static Delta decode(JsonNode original) {
        ObjectNode row=StrictJson.object(original,FIELDS);StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact original-resume schema required");
        JsonNode prior=row.get("before_history");BeforeHistory before;
        String kind=StrictJson.text(prior.get("kind"));
        if(kind.equals("ABSENT")){StrictJson.object(prior,Set.of("kind"));before=new MissingHistory();}
        else if(kind.equals("BOUND")){StrictJson.object(prior,Set.of("kind","original"));before=new BoundHistory(ExactRef.fromJson(prior.get("original")));}
        else throw new IllegalArgumentException("exact history presence branch required");
        var generation=StrictJson.object(row.get("game"),Set.of("pid","creation_filetime"));
        var queue=row.get("managed_queue");Objects.requireNonNull(queue,"nullable queue proof must be present");
        var inputs=row.get("original_inputs");StrictJson.require(inputs!=null&&inputs.isArray(),"complete original inputs array required");
        var refs=new java.util.ArrayList<ExactRef>();for(JsonNode value:inputs)refs.add(ExactRef.fromJson(value));
        Delta result=new Delta(ExactRef.fromJson(row.get("source")),StrictJson.text(row.get("machine_id")),StrictJson.text(row.get("expected_head_sha256")),
                before,Route.valueOf(StrictJson.text(row.get("route"))),StrictJson.text(row.get("session_id")),StrictJson.text(row.get("pipe_name")),
                new Game(StrictJson.integer(generation.get("pid"),1,0xffff_ffffL),StrictJson.text(generation.get("creation_filetime"))),
                NativeCharacterId.fromJson(row.get("actor_id")).value(),StrictJson.text(row.get("episode_run_id")),
                StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER),StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER),
                ExactRef.fromJson(row.get("original_driver")),ExactRef.fromJson(row.get("canonical_original")),ExactRef.fromJson(row.get("full_driver")),
                ExactRef.fromJson(row.get("original_hello")),ExactRef.fromJson(row.get("original_native")),ExactRef.fromJson(row.get("canonical_native")),
                ExactRef.fromJson(row.get("migration_plan")),queue.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(queue)),refs);
        StrictJson.require(ContinuityJson.same(result.toJson(),row),"resume descriptor differs from its exact typed encoding and derived identity");return result;
    }
    /** Pure closed validation. Root's concrete private authority must separately prove actual inputs. */
    public static Delta checked(ContinuityState before,WriterContracts.Request request) {
        StrictJson.require(KIND.equals(request.kind()),"exact legacy-resume event kind required");Delta delta=decode(request.detailsObject());
        StrictJson.require(before.machineId().equals(delta.machineId())&&request.evidence().equals(delta.evidence())
                &&delta.expectedHeadSha256().equals(ContinuityJson.digest(before.toJson())),"actual same-machine original head and complete resume closure required");
        var state=before.toJson();StrictJson.require(!state.has(STATE_FIELD)&&!state.has(WriterContracts.GAMEPLAY_ENTRY_FIELD),"legacy resume is independent from fresh entry and may initialize once");
        boolean baseline=state.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD);
        switch(delta.beforeHistory()) {
            case MissingHistory ignored->StrictJson.require(!baseline,"absent original history must remain absent before this binding");
            case BoundHistory bound->StrictJson.require(baseline&&!state.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD).isNull()
                    &&bound.original().equals(ExactRef.fromJson(state.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),"resume cannot replace another or null original history basis");
        }
        StrictJson.require(!state.has("pending_cycle")||state.get("pending_cycle").isNull(),"unresolved original cycle cannot be migrated");
        return delta;
    }
    public static ContinuityState reduce(ContinuityState before,WriterContracts.Request request) {
        Delta delta=checked(before,request);ObjectNode next=before.toJson();next.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,delta.fullDriver().toJson());
        next.set(STATE_FIELD,delta.toJson());return ContinuityState.fromJson(next,before.machineId());
    }
    /** The actual cold event/history reader uses the same reducer as the live original writer. */
    public static void requireReduction(ContinuityState before,ContinuityState after,WriterContracts.Request request,boolean sequenced) {
        ObjectNode expected=reduce(before,request).toJson();
        if(sequenced){expected.put("sequence",Math.addExact(before.sequence(),1));expected.put("last_event_identity",request.identity());}
        StrictJson.require(ContinuityJson.same(expected,after.toJson()),"legacy resume changed fields outside its exact pure reducer");
    }
    private static void reference(ExactRef ref){Objects.requireNonNull(ref);StrictJson.require(ref.bytes()>0&&ref.bytes()<=WriterContracts.MAX_PIN_BYTES,"complete original resume reference exceeds writer material lease");}
}
