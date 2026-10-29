package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/** Pure original generic pause policy and replay DATA. No constructor, decision or decoded proof grants a retry ticket. */
public final class GenericPublicPauseRecovery {
    private GenericPublicPauseRecovery(){ }
    public static final String PUBLIC_STEP="pause-map";
    public static final OperationKey OPERATION=ControlSequenceObservation.OPERATION;
    public static final String OBSERVER=ControlSequenceObservation.OBSERVER;
    public static final String SCHEMA="xar.java.generic-public-pause-recovery/v2";
    public static final int MAX_PROOF_BYTES=2*1024*1024;
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final BigInteger U32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    private static final BigInteger I32=BigInteger.valueOf(Integer.MAX_VALUE);
    private static final BigInteger I63=BigInteger.valueOf(Long.MAX_VALUE);
    public static List<ExpectedValue> expected(){return ControlSequenceObservation.expected();}
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source){
        return new ExpectedPostcondition(1,before,source,OBSERVER,expected());
    }
    public static void validateArguments(Obj actual){require(Objects.requireNonNull(actual).members().isEmpty(),"public pause parent arguments must be empty");}
    public static void validateParent(ActionCommand parent){ControlSequenceObservation.validateParent(parent);}
    public enum Paused { TRUE,FALSE,UNAVAILABLE }
    public enum FailureReason {
        INITIAL_OWNER_UNAVAILABLE("initial running exact-build owner binding unavailable"),
        NO_FRESH_SEMANTIC_FRAME("no fresh semantic frame after rejected pause"),
        OWNER_CHANGED_BEFORE_RETRY("runtime owner or event binding changed before retry"),
        DEADLINE_BEFORE_RETRY("total pause deadline exhausted before retry"),
        SECOND_REQUEST_FAILED("second pause request failed"),
        REFRESHED_PAUSE_UNAVAILABLE("refreshed pause state unavailable"),
        ENDING_NOT_PAUSED("same-owner paused map not observed after recovery");
        private final String message;
        FailureReason(String message){this.message=message;}
        public String message(){return message;}
    }
    /** Frozen build identity is DATA, never an assertion about an executing process. */
    public record Build(String version,String sha256){
        public Build {StrictJson.text(version);require(sha256!=null&&sha256.matches("[0-9a-f]{64}"),"canonical build digest required");}
    }
    public sealed interface Owner permits OrdinaryOwner,ManagedCampaignOwner { }
    public record OrdinaryOwner(Build build,BigInteger connectionGeneration,BigInteger bridgePid,Value adapter,
            String episodeRunId,BigInteger actor,Value localPlayer,Value speed,Value activeEvent,Value pendingInteraction) implements Owner { }
    /** The native campaign identity is not coerced into a one-life episode or ordinary actor domain. */
    public record ManagedCampaignOwner(Build build,BigInteger bridgePid,BigInteger connectionGeneration,String adapter,
            String pipe,String runId,String stateDirectory,String hostPath,String frozenArgvSha256,BigInteger actor,
            BigInteger localPlayer,BigInteger speed,Value activeEvent,Value pendingInteraction) implements Owner { }
    public static final class Snapshot {
        private final Obj semantic;
        private final ExactRef originalSemantic;
        private final Optional<BigInteger> publicRevision,nativeRevision,dateRaw;
        private final Paused paused;
        private final Optional<Owner> owner;
        private Snapshot(Obj semantic,ExactRef reference){
            this.semantic=Objects.requireNonNull(semantic);originalSemantic=Objects.requireNonNull(reference);
            require(reference.bytes()>0,"actual semantic reference required");
            publicRevision=integer(semantic.get("revision"));nativeRevision=integer(semantic.get("native_revision"));dateRaw=integer(semantic.get("date_raw"));
            paused=semantic.get("paused") instanceof Bool b?(b.value()?Paused.TRUE:Paused.FALSE):Paused.UNAVAILABLE;
            owner=ownerOf(semantic);
        }
        public Obj semantic(){return semantic;}
        public ExactRef originalSemantic(){return originalSemantic;}
        public Optional<BigInteger> publicRevision(){return publicRevision;}
        public Optional<BigInteger> nativeRevision(){return nativeRevision;}
        public Optional<BigInteger> dateRaw(){return dateRaw;}
        public Paused paused(){return paused;}
        public Optional<Owner> owner(){return owner;}
        @Override public boolean equals(Object other){return other instanceof Snapshot x&&semantic.equals(x.semantic)&&originalSemantic.equals(x.originalSemantic);}
        @Override public int hashCode(){return Objects.hash(semantic,originalSemantic);}
    }
    public static Snapshot snapshot(Obj actualInternalSemantic,ExactRef originalSemantic){return new Snapshot(actualInternalSemantic,originalSemantic);}
    public record Times(Instant first,Optional<Instant> refresh,Optional<Instant> retry,Optional<Instant> ending,Optional<Instant> unavailableAt){
        public Times{
            Objects.requireNonNull(first);refresh=Objects.requireNonNull(refresh);retry=Objects.requireNonNull(retry);ending=Objects.requireNonNull(ending);unavailableAt=Objects.requireNonNull(unavailableAt);
            Instant previous=first;
            for(var t:List.of(refresh,retry,ending,unavailableAt))if(t.isPresent()){require(!t.orElseThrow().isBefore(previous),"pause phase clock regressed");previous=t.orElseThrow();}
        }
    }
    public record Attempt(String requestId,Optional<ActionReceipt> receipt,Optional<String> failure){
        public Attempt{
            StrictJson.text(requestId);receipt=Objects.requireNonNull(receipt);failure=Objects.requireNonNull(failure);
            require(receipt.isPresent()!=failure.isPresent(),"exactly one recorded original receipt or failure diagnostic required");
            failure.ifPresent(StrictJson::text);
            receipt.ifPresent(x->require(PUBLIC_STEP.equals(x.command().operation().value())&&x.command().arguments().members().isEmpty(),"only actual pause children are accepted"));
        }
        public boolean needsOriginalReconciliation(){return receipt.isEmpty()||!receipt.orElseThrow().settled();}
    }
    public record Partial(Snapshot starting,Optional<Snapshot> refreshed,Optional<Snapshot> ending,
            List<Attempt> attempts,Instant deadline,Times times){
        public Partial{
            Objects.requireNonNull(starting);refreshed=Objects.requireNonNull(refreshed);ending=Objects.requireNonNull(ending);
            attempts=List.copyOf(attempts);Objects.requireNonNull(deadline);Objects.requireNonNull(times);
            require(attempts.size()>=1&&attempts.size()<=2&&attempts.getFirst().receipt().isPresent(),"one original first child and at most one recovery child required");
            require(refreshed.isPresent()==times.refresh().isPresent(),"refreshed snapshot/time differ");
            require((attempts.size()==2)==times.retry().isPresent(),"retry time/attempt differ");
            require(ending.isPresent()==times.ending().isPresent(),"ending snapshot/time differ");
        }
        public boolean needsOriginalReconciliation(){return attempts.stream().anyMatch(Attempt::needsOriginalReconciliation);}
    }
    public sealed interface Decision permits Completed,AwaitFresh,Retry,AwaitEnding,Failed,Original {Partial partial();}
    public record Completed(Partial partial,ControlSequenceObservation.Mode mode) implements Decision{
        public Completed{Objects.requireNonNull(partial);Objects.requireNonNull(mode);}
    }
    public record AwaitFresh(Partial partial) implements Decision {public AwaitFresh{requireRecovery(partial);require(partial.attempts().size()==1,"fresh wait cannot replay a second child");}}
    public record Retry(Partial partial) implements Decision{
        public Retry{requireRecovery(partial);require(partial.attempts().size()==1&&partial.refreshed().isPresent(),"retry needs its original fresh snapshot");}
        public BigInteger expectedNativeRevision(){return partial.refreshed().orElseThrow().nativeRevision().orElseThrow();}
        public Optional<BigInteger> callerPublicRevision(){return Optional.empty();}
    }
    public record AwaitEnding(Partial partial) implements Decision {public AwaitEnding{requireRecovery(partial);require(partial.attempts().size()==2,"ending wait cannot submit another child");}}
    public record Failed(Partial partial,FailureReason reason) implements Decision {public Failed{Objects.requireNonNull(partial);Objects.requireNonNull(reason);}}
    public record Original(Partial partial) implements Decision {public Original{Objects.requireNonNull(partial);}}
    private static Attempt recorded(ActionReceipt receipt){return new Attempt(receipt.ack().map(NativeActionPort.AckReceived::requestId).orElse(receipt.command().actionId()),Optional.of(receipt),Optional.empty());}
    public static Decision afterFirst(Snapshot starting,ActionReceipt actualFirst,Instant totalDeadline,Instant now){
        var p=new Partial(starting,Optional.empty(),Optional.empty(),List.of(recorded(actualFirst)),totalDeadline,new Times(now,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()));
        if(control(actualFirst))return new Completed(p,ControlSequenceObservation.Mode.DIRECT_PAUSE);
        try{ControlSequenceObservation.requireMapUnavailable(actualFirst);}catch(IllegalArgumentException invalid){return new Original(p);}
        if(starting.paused()!=Paused.FALSE||starting.owner().isEmpty())return new Failed(p,FailureReason.INITIAL_OWNER_UNAVAILABLE);
        if(!now.isBefore(totalDeadline))return new Failed(p,FailureReason.NO_FRESH_SEMANTIC_FRAME);
        return new AwaitFresh(p);
    }
    public static Decision afterRefresh(AwaitFresh original,Snapshot actualFresh,Instant now){
        var old=original.partial();var p=new Partial(old.starting(),Optional.of(actualFresh),Optional.empty(),old.attempts(),old.deadline(),
                new Times(old.times().first(),Optional.of(now),Optional.empty(),Optional.empty(),Optional.empty()));
        boolean publicFresh=greater(actualFresh.publicRevision(),old.starting().publicRevision());
        if(!publicFresh)return now.isBefore(old.deadline())?new AwaitFresh(p):new Failed(p,FailureReason.NO_FRESH_SEMANTIC_FRAME);
        if(!greater(actualFresh.nativeRevision(),old.starting().nativeRevision()))return new Failed(p,FailureReason.NO_FRESH_SEMANTIC_FRAME);
        if(!sameOwner(old.starting(),actualFresh))return new Failed(p,FailureReason.OWNER_CHANGED_BEFORE_RETRY);
        if(actualFresh.paused()==Paused.TRUE)return completed(p,actualFresh,now,ControlSequenceObservation.Mode.ALREADY_PAUSED_AFTER_REJECTION);
        if(actualFresh.paused()==Paused.UNAVAILABLE)return new Failed(p,FailureReason.REFRESHED_PAUSE_UNAVAILABLE);
        if(!now.isBefore(old.deadline()))return new Failed(p,FailureReason.DEADLINE_BEFORE_RETRY);
        return new Retry(p);
    }
    public static Decision afterRetry(Retry original,ActionReceipt actualSecond,Optional<Snapshot> actualEnding,Instant now){
        var old=original.partial();var first=old.attempts().getFirst().receipt().orElseThrow().command();var second=actualSecond.command();
        var fresh=old.refreshed().orElseThrow();
        require(second.source().equals(first.source())&&second.sessionId().equals(first.sessionId())
                &&second.before().game().equals(first.before().game())&&!second.actionId().equals(first.actionId())
                &&second.before().frame().revision().equals(fresh.publicRevision().orElseThrow())
                &&second.before().frame().identity().nativeRevision().equals(original.expectedNativeRevision())
                &&!second.deadline().isAfter(old.deadline()),"recovery child changed source/owner/fresh revision/total deadline");
        var p=new Partial(old.starting(),old.refreshed(),Optional.empty(),List.of(old.attempts().getFirst(),recorded(actualSecond)),old.deadline(),
                new Times(old.times().first(),old.times().refresh(),Optional.of(now),Optional.empty(),Optional.empty()));
        if(!control(actualSecond))return new Failed(p,FailureReason.SECOND_REQUEST_FAILED);
        var wait=new AwaitEnding(p);
        return actualEnding.isPresent()?afterEnding(wait,actualEnding.orElseThrow(),now):wait;
    }
    public static Failed afterRetryFailure(Retry original,String actualRequestId,String actualError,Instant now){
        var old=original.partial();return new Failed(new Partial(old.starting(),old.refreshed(),Optional.empty(),
                List.of(old.attempts().getFirst(),new Attempt(actualRequestId,Optional.empty(),Optional.of(StrictJson.text(actualError)))),
                old.deadline(),new Times(old.times().first(),old.times().refresh(),Optional.of(now),Optional.empty(),Optional.empty())),FailureReason.SECOND_REQUEST_FAILED);
    }
    public static Decision afterEnding(AwaitEnding original,Snapshot actualEnding,Instant now){
        var old=original.partial();var p=new Partial(old.starting(),old.refreshed(),Optional.of(actualEnding),old.attempts(),old.deadline(),
                new Times(old.times().first(),old.times().refresh(),old.times().retry(),Optional.of(now),Optional.empty()));
        if(!sameOwner(old.starting(),actualEnding))return new Failed(p,FailureReason.ENDING_NOT_PAUSED);
        if(actualEnding.paused()!=Paused.TRUE)return now.isBefore(old.deadline())?new AwaitEnding(p):new Failed(p,FailureReason.ENDING_NOT_PAUSED);
        if(!atLeast(actualEnding.publicRevision(),old.refreshed().orElseThrow().publicRevision()))return new Failed(p,FailureReason.ENDING_NOT_PAUSED);
        return new Completed(p,ControlSequenceObservation.Mode.RETRIED_PAUSE);
    }
    /** Actual wait/read failure, without inventing a refreshed semantic original or another native request. */
    public static Failed afterRefreshUnavailable(AwaitFresh original,Instant now){
        Partial p=original.partial();return unavailable(p,FailureReason.NO_FRESH_SEMANTIC_FRAME,now);
    }
    /** Actual final observation unavailable; retain the original second canonical receipt. */
    public static Failed afterEndingUnavailable(AwaitEnding original,Instant now){
        Partial p=original.partial();return unavailable(p,FailureReason.ENDING_NOT_PAUSED,now);
    }
    private static Failed unavailable(Partial p,FailureReason reason,Instant now){
        require(p.times().unavailableAt().isEmpty(),"an unavailable terminal observation cannot be reused");
        return new Failed(new Partial(p.starting(),p.refreshed(),p.ending(),p.attempts(),p.deadline(),
                new Times(p.times().first(),p.times().refresh(),p.times().retry(),p.times().ending(),Optional.of(now))),reason);
    }
    private static Completed completed(Partial p,Snapshot end,Instant now,ControlSequenceObservation.Mode mode){
        return new Completed(new Partial(p.starting(),p.refreshed(),Optional.of(end),p.attempts(),p.deadline(),
                new Times(p.times().first(),p.times().refresh(),p.times().retry(),Optional.of(now),Optional.empty())),mode);
    }
    private static void requireRecovery(Partial p){
        Objects.requireNonNull(p);
        require(p.times().unavailableAt().isEmpty(),"a terminal unavailable observation cannot be reopened as a wait or retry");
        ControlSequenceObservation.requireMapUnavailable(p.attempts().getFirst().receipt().orElseThrow());
    }
    private static boolean control(ActionReceipt x){
        return x.state() instanceof ActionState.Settled s&&(s.settlement() instanceof ActionState.PauseConfirmed
                ||s.settlement() instanceof ActionState.ControlApplied c&&c.actual().stream().anyMatch(v->v instanceof ExpectedBoolean b&&b.field().value().equals("control.paused")&&b.value()));
    }
    public static boolean sameOwner(Snapshot before,Snapshot after){
        return before.owner().isPresent()&&before.owner().equals(after.owner())&&atLeast(after.dateRaw(),before.dateRaw());
    }
    private static boolean greater(Optional<BigInteger> a,Optional<BigInteger> b){return a.isPresent()&&b.isPresent()&&a.orElseThrow().compareTo(b.orElseThrow())>0;}
    private static boolean atLeast(Optional<BigInteger> a,Optional<BigInteger> b){return a.isPresent()&&b.isPresent()&&a.orElseThrow().compareTo(b.orElseThrow())>=0;}
    private static Optional<BigInteger> integer(Value v){return v instanceof IntegerValue x?Optional.of(x.value()):Optional.empty();}
    private static Value get(Obj v,String key){Value x=v.get(key);return x==null?Nil.INSTANCE:x;}
    private static Optional<Obj> object(Value v){return v instanceof Obj x?Optional.of(x):Optional.empty();}
    private static Optional<String> text(Value v){return v instanceof Text x&&!x.value().isEmpty()&&x.value().indexOf(0)<0?Optional.of(x.value()):Optional.empty();}
    private static boolean truth(Value v){return v instanceof Bool x&&x.value();}
    private static boolean nil(Value v){return v==null||v instanceof Nil;}
    private static BigInteger bounded(Value v,BigInteger min,BigInteger max){
        BigInteger n=integer(v).orElseThrow(()->new IllegalArgumentException("exact native integer required"));require(n.compareTo(min)>=0&&n.compareTo(max)<=0,"native integer outside original range");return n;
    }
    private static Build build(Value version,Value sha){
        String v=text(version).orElseThrow(),s=text(sha).orElseThrow().toLowerCase(java.util.Locale.ROOT);
        boolean known=ExactCk3Build.CK3_12004.matches(v,s)
                ||v.equals("1.19.0.6")&&s.equals("2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86")
                ||v.equals("1.20.0.2")&&s.equals("ae1ba6ff060ba603842f6f4a2dedd0af4b7d3666b3dd271f75fb01b0da8e81b2d")
                ||v.equals("1.20.0.3")&&s.equals("94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6");
        require(known,"unrecognized frozen exact build");return new Build(v,s);
    }
    private static Optional<Owner> ownerOf(Obj row){
        try{
            Obj d=object(row.get("diagnostics")).orElseThrow(),h=object(d.get("hello")).orElseThrow(),a=object(row.get("played_character")).orElseThrow();
            if("native_campaign".equals(text(row.get("episode_projection")).orElse(""))){
                Obj run=object(row.get("managed_campaign_run_binding")).orElseThrow();
                require(nil(row.get("episode_run_id"))&&text(row.get("backend_id")).orElse("").equals("native-headless")
                        &&text(row.get("source")).orElse("").equals("injected-dll-named-pipe")&&truth(row.get("map_ready"))&&nil(row.get("one_life_terminal_reason"))
                        &&truth(a.get("alive"))&&text(a.get("source")).orElse("").equals("native")&&truth(d.get("connected"))&&truth(h.get("ck3_build_match"))
                        &&run.members().keySet().equals(Set.of("run_id","state_dir","bridge_pipe","host_path","frozen_argv_sha256")),"managed owner unavailable");
                bounded(row.get("format_version"),BigInteger.ONE,BigInteger.ONE);bounded(row.get("revision"),BigInteger.ONE,I63);
                bounded(row.get("native_revision"),BigInteger.ONE,I63);bounded(row.get("date_raw"),BigInteger.ONE,I32);
                Build b=build(h.get("expected_ck3_version"),h.get("expected_ck3_sha256"));
                BigInteger pid=bounded(d.get("bridge_pid"),BigInteger.ONE,U32),gen=bounded(d.get("connection_generation"),BigInteger.ONE,U64);
                require(pid.equals(bounded(h.get("pid"),BigInteger.ONE,U32))&&gen.equals(bounded(h.get("connection_generation"),BigInteger.ONE,U64)),"managed hello owner differs");
                String pipe=text(d.get("pipe_name")).orElseThrow(),sha=text(run.get("frozen_argv_sha256")).orElseThrow(),adapter=text(h.get("game_adapter_id")).orElseThrow();
                require(pipe.equals(text(run.get("bridge_pipe")).orElseThrow())&&sha.matches("[0-9a-f]{64}")&&adapter.equals("ck3-"+b.version()+"-msvc-x64"),"managed allocated pipe/build/argv differs");
                return Optional.of(new ManagedCampaignOwner(b,pid,gen,adapter,pipe,text(run.get("run_id")).orElseThrow(),text(run.get("state_dir")).orElseThrow(),
                        text(run.get("host_path")).orElseThrow(),sha,bounded(a.get("character_id"),BigInteger.ONE,U32.subtract(BigInteger.ONE)),
                        bounded(row.get("local_player_id"),BigInteger.ZERO,I32),bounded(row.get("speed"),BigInteger.ONE,BigInteger.valueOf(5)),get(row,"active_event"),get(row,"pending_character_interaction")));
            }
            require(truth(h.get("ck3_build_match"))&&truth(d.get("connected"))&&truth(row.get("map_ready"))&&nil(row.get("one_life_terminal_reason"))&&truth(a.get("alive")),"ordinary owner unavailable");
            BigInteger actor=integer(a.get("character_id")).orElseThrow();require(actor.signum()>0&&integer(row.get("episode_character_id")).filter(actor::equals).isPresent(),"ordinary episode actor differs");
            String episode=text(row.get("episode_run_id")).orElseThrow();BigInteger generation=integer(d.get("connection_generation")).orElseThrow(),pid=integer(d.get("bridge_pid")).orElseThrow();
            Value v=h.get("expected_ck3_version");if(v==null)v=h.get("game_version");
            Value sha=h.get("expected_ck3_sha256");if(sha==null)sha=h.get("executable_sha256");
            Build b=build(v,sha);integer(row.get("date_raw")).orElseThrow();
            return Optional.of(new OrdinaryOwner(b,generation,pid,get(h,"game_adapter_id"),episode,actor,get(row,"local_player_id"),get(row,"speed"),get(row,"active_event"),get(row,"pending_character_interaction")));
        }catch(IllegalArgumentException|java.util.NoSuchElementException invalid){return Optional.empty();}
    }

    /** The only APP parent-call field contract. A decoded proof is DATA and cannot replace the installed source callback. */
    public record ParentProof(ActionCommand parent,RawJson originalCaller,ExactRef beforeNative,ExactRef beforeDriver,
            ExactRef runtimeSource,ExactRef productSource,List<ExactRef> sourceClosure,long writerSequence,String writerDigest){
        public static final String SCHEMA="xar.java.public-pause-parent-call-proof/v1";
        public ParentProof{
            validateParent(parent);Objects.requireNonNull(originalCaller);
            require(originalCaller.bytes().length<=65536&&StrictJson.parse(originalCaller.bytes()).isObject(),"bounded exact original caller object required");
            for(ExactRef ref:List.of(beforeNative,beforeDriver,runtimeSource,productSource))require(Objects.requireNonNull(ref).bytes()>0,"actual parent original/source required");
            sourceClosure=List.copyOf(sourceClosure);require(sourceClosure.size()<=64&&new HashSet<>(sourceClosure).size()==sourceClosure.size(),"finite unique actual source closure required");
            sourceClosure.forEach(ref->require(ref.bytes()>0,"nonempty source original required"));
            require(sourceClosure.contains(runtimeSource)&&sourceClosure.contains(productSource)&&writerSequence>=1&&writerDigest!=null&&writerDigest.matches("[0-9a-f]{64}"),"actual source/head locators required");
        }
        public String actionId(){return parent.actionId();}
        public String bodySha256(){return ActionCodec.bodySha256(parent);}
        public String catalogHandler(){return PUBLIC_STEP;}
        public boolean matchesGuard(GuardEvidence actual,ExactRef actualDriver,ExactRef actualProofRef){
            return actual.origin().equals(parent.origin())&&actual.source().equals(parent.source())&&actual.sessionId().equals(parent.sessionId())
                    &&actual.operation().equals(parent.operation())&&actual.nativeEvidence().equals(beforeNative)&&beforeDriver.equals(actualDriver)
                    &&actual.supportingEvidence().contains(actualProofRef);
        }
        public List<ExactRef> references(){var all=new ArrayList<>(sourceClosure);all.add(beforeNative);all.add(beforeDriver);return all.stream().distinct().toList();}
        public byte[] encode(){
            var row=StrictJson.object().put("schema",SCHEMA).put("action_id",actionId()).put("body_sha256",bodySha256()).put("catalog_handler",catalogHandler());
            row.put("parent_command_base64",b64(ActionCodec.encodeCommand(parent)));row.put("original_caller_base64",b64(originalCaller.bytes()));
            row.put("original_caller_sha256",ActionCodec.sha256(originalCaller.bytes()));row.set("before_native",beforeNative.toJson());row.set("before_driver",beforeDriver.toJson());
            row.set("runtime_source",runtimeSource.toJson());row.set("product_source",productSource.toJson());var list=row.putArray("source_closure");sourceClosure.forEach(ref->list.add(ref.toJson()));
            row.put("writer_sequence",Long.toString(writerSequence)).put("writer_digest",writerDigest);return boundedBytes(row,256*1024);
        }
        public static ParentProof decode(byte[] bytes){
            require(bytes!=null&&bytes.length<=256*1024,"bounded parent proof required");
            var row=StrictJson.object(StrictJson.parse(bytes,256*1024),Set.of("schema","action_id","body_sha256","catalog_handler","parent_command_base64","original_caller_base64","original_caller_sha256",
                    "before_native","before_driver","runtime_source","product_source","source_closure","writer_sequence","writer_digest"));
            require(SCHEMA.equals(txt(row,"schema"))&&row.get("source_closure").isArray()&&row.get("source_closure").size()<=64,"parent proof schema/closure differs");
            var refs=new ArrayList<ExactRef>();row.get("source_closure").forEach(v->refs.add(ExactRef.fromJson(v)));
            byte[] caller=originalBytes(row,"original_caller_base64",65536);require(ActionCodec.sha256(caller).equals(txt(row,"original_caller_sha256")),"original caller digest differs");
            long sequence=new BigInteger(new CrossJsDecimalUInt64(txt(row,"writer_sequence")).decimal()).longValueExact();
            var proof=new ParentProof(ActionCodec.decodeCommand(originalBytes(row,"parent_command_base64",ActionCodec.MAX_COMMAND_BYTES)),new RawJson(caller),ExactRef.fromJson(row.get("before_native")),ExactRef.fromJson(row.get("before_driver")),
                    ExactRef.fromJson(row.get("runtime_source")),ExactRef.fromJson(row.get("product_source")),refs,sequence,txt(row,"writer_digest"));
            require(proof.actionId().equals(txt(row,"action_id"))&&proof.bodySha256().equals(txt(row,"body_sha256"))&&proof.catalogHandler().equals(txt(row,"catalog_handler")),"parent caller/body/handler changed");
            return proof;
        }
    }
    @FunctionalInterface public interface ReceiptReferences {ExactRef reference(ActionReceipt actual)throws IOException;}
    public interface ReplayReader {Snapshot snapshot(ExactRef original)throws IOException;ActionReceipt receipt(ExactRef canonical)throws IOException;}
    /** Bounded locators only. Complete semantic/receipt material remains in the existing archive and its original lease. */
    public static byte[] encode(Decision decision,ReceiptReferences refs)throws IOException{
        var p=decision.partial();var row=StrictJson.object().put("schema",SCHEMA).put("state",decision.getClass().getSimpleName()).put("deadline",p.deadline().toString());
        row.set("starting",p.starting().originalSemantic().toJson());putSnapshot(row,"refreshed",p.refreshed());putSnapshot(row,"ending",p.ending());
        row.put("first_at",p.times().first().toString());putTime(row,"refresh_at",p.times().refresh());putTime(row,"retry_at",p.times().retry());putTime(row,"ending_at",p.times().ending());putTime(row,"unavailable_at",p.times().unavailableAt());
        var list=row.putArray("attempts");for(var a:p.attempts()){
            var n=list.addObject().put("request_id",a.requestId());
            if(a.receipt().isPresent()){ActionReceipt actual=a.receipt().orElseThrow();ExactRef ref=Objects.requireNonNull(refs.reference(actual));require(ref.bytes()>0,"actual receipt reference required");
                n.set("canonical_receipt",ref.toJson());n.put("action_id",actual.command().actionId()).put("body_sha256",actual.bodySha256());n.putNull("failure");}
            else{n.putNull("canonical_receipt");n.putNull("action_id");n.putNull("body_sha256");n.put("failure",a.failure().orElseThrow());}
        }
        if(decision instanceof Completed x)row.put("mode",x.mode().name());else row.putNull("mode");
        if(decision instanceof Failed x)row.put("failure",x.reason().name());else row.putNull("failure");
        return boundedBytes(row,MAX_PROOF_BYTES);
    }
    public static Decision decode(byte[] bytes,ReplayReader reader)throws IOException{
        require(bytes!=null&&bytes.length<=MAX_PROOF_BYTES,"bounded pause DATA required");
        var row=StrictJson.object(DriverJson.toNode(DriverJson.object(bytes,MAX_PROOF_BYTES)),Set.of("schema","state","deadline","starting","refreshed","ending","first_at","refresh_at","retry_at","ending_at","unavailable_at","attempts","mode","failure"));
        require(SCHEMA.equals(txt(row,"schema"))&&row.get("attempts").isArray()&&row.get("attempts").size()>=1&&row.get("attempts").size()<=2,"finite pause DATA differs");
        var attempts=new ArrayList<Attempt>();
        for(var node:row.get("attempts")){
            var n=StrictJson.object(node,Set.of("request_id","canonical_receipt","action_id","body_sha256","failure"));String id=txt(n,"request_id");
            if(n.get("canonical_receipt").isNull()){require(n.get("action_id").isNull()&&n.get("body_sha256").isNull(),"failed diagnostic cannot claim a receipt");attempts.add(new Attempt(id,Optional.empty(),Optional.of(txt(n,"failure"))));}
            else{require(n.get("failure").isNull(),"receipt cannot be a failure diagnostic");var actual=reader.receipt(ExactRef.fromJson(n.get("canonical_receipt")));
                require(actual.command().actionId().equals(txt(n,"action_id"))&&actual.bodySha256().equals(txt(n,"body_sha256")),"canonical action locator changed");
                require(recorded(actual).requestId().equals(id),"original protocol request identity changed");attempts.add(recorded(actual));}
        }
        var p=new Partial(loadSnapshot(reader,ExactRef.fromJson(row.get("starting"))),loadOptional(reader,row.get("refreshed")),loadOptional(reader,row.get("ending")),attempts,
                Instant.parse(txt(row,"deadline")),new Times(Instant.parse(txt(row,"first_at")),time(row,"refresh_at"),time(row,"retry_at"),time(row,"ending_at"),time(row,"unavailable_at")));
        String state=txt(row,"state");Decision result=switch(state){
            case "Completed" -> new Completed(p,ControlSequenceObservation.Mode.valueOf(txt(row,"mode")));
            case "AwaitFresh" -> new AwaitFresh(p);case "Retry" -> new Retry(p);case "AwaitEnding" -> new AwaitEnding(p);
            case "Failed" -> new Failed(p,FailureReason.valueOf(txt(row,"failure")));case "Original" -> new Original(p);
            default -> throw new IllegalArgumentException("unknown pause decision");
        };
        require((result instanceof Completed)==!row.get("mode").isNull()&&(result instanceof Failed)==!row.get("failure").isNull(),"mode/failure presence differs");
        require(equivalent(result,replay(result)),"pause DATA does not match pure original policy replay");return result;
    }
    public static Decision replay(Decision declared){
        var p=declared.partial();Decision result=afterFirst(p.starting(),p.attempts().getFirst().receipt().orElseThrow(),p.deadline(),p.times().first());
        if(p.refreshed().isPresent()){
            require(result instanceof AwaitFresh,"unrequested refreshed snapshot");result=afterRefresh((AwaitFresh)result,p.refreshed().orElseThrow(),p.times().refresh().orElseThrow());
        }
        if(p.attempts().size()==2){
            require(result instanceof Retry,"unrequested second pause child");var a=p.attempts().getLast();Retry retry=(Retry)result;
            result=a.receipt().isPresent()?afterRetry(retry,a.receipt().orElseThrow(),Optional.empty(),p.times().retry().orElseThrow()):
                    afterRetryFailure(retry,a.requestId(),a.failure().orElseThrow(),p.times().retry().orElseThrow());
        }
        if(p.ending().isPresent()&&!(result instanceof Completed x&&x.mode()==ControlSequenceObservation.Mode.ALREADY_PAUSED_AFTER_REJECTION)){
            require(result instanceof AwaitEnding,"unrequested ending snapshot");result=afterEnding((AwaitEnding)result,p.ending().orElseThrow(),p.times().ending().orElseThrow());
        }
        if(p.times().unavailableAt().isPresent()){
            Instant unavailable=p.times().unavailableAt().orElseThrow();
            if(result instanceof AwaitFresh waiting)result=afterRefreshUnavailable(waiting,unavailable);
            else if(result instanceof AwaitEnding waiting)result=afterEndingUnavailable(waiting,unavailable);
            else throw new IllegalArgumentException("unavailable observation must follow its actual unresolved wait phase");
        }
        return result;
    }
    private static boolean equivalent(Decision a,Decision b){return a.equals(b);}
    private static Snapshot loadSnapshot(ReplayReader reader,ExactRef ref)throws IOException{Snapshot s=reader.snapshot(ref);require(s.originalSemantic().equals(ref),"semantic reference changed");return s;}
    private static Optional<Snapshot> loadOptional(ReplayReader r,JsonNode node)throws IOException{return node.isNull()?Optional.empty():Optional.of(loadSnapshot(r,ExactRef.fromJson(node)));}
    private static void putSnapshot(ObjectNode row,String name,Optional<Snapshot> snapshot){if(snapshot.isPresent())row.set(name,snapshot.orElseThrow().originalSemantic().toJson());else row.putNull(name);}
    private static void putTime(ObjectNode row,String name,Optional<Instant> time){if(time.isPresent())row.put(name,time.orElseThrow().toString());else row.putNull(name);}
    private static Optional<Instant> time(ObjectNode row,String name){return row.get(name).isNull()?Optional.empty():Optional.of(Instant.parse(txt(row,name)));}
    private static String txt(ObjectNode row,String key){return StrictJson.text(row.get(key));}
    private static String b64(byte[] bytes){return Base64.getEncoder().encodeToString(bytes);}
    /** Binary originals use their own byte budget, not the smaller generic textual metadata limit. */
    private static byte[] originalBytes(ObjectNode row,String key,int maximumBytes){
        JsonNode node=row.get(key);require(node!=null&&node.isTextual(),"original base64 field must be a JSON string");
        String value=node.textValue();require(!value.isEmpty()&&value.length()<=((maximumBytes+2)/3)*4,"bounded original base64 required");
        byte[] original=unb64(value);require(original.length>0&&original.length<=maximumBytes,"original decoded byte budget exceeded");
        return original;
    }
    private static byte[] unb64(String value){byte[] b=Base64.getDecoder().decode(value);require(b64(b).equals(value),"canonical base64 required");return b;}
    private static byte[] boundedBytes(JsonNode value,int limit){byte[] b=StrictJson.canonical(value);require(b.length>0&&b.length<=limit,"bounded pause proof exceeded");return b;}

    /** Original numeric compositor only. Public JSON uint64 presentation remains an explicit boundary of the actual product. */
    public static RawJson result(Decision decision,List<Optional<RawJson>> actualPrimitiveNumericResults){
        var p=decision.partial();actualPrimitiveNumericResults=List.copyOf(actualPrimitiveNumericResults);
        require(equivalent(decision,replay(decision)),"public pause report must match pure original replay");
        require(actualPrimitiveNumericResults.size()==p.attempts().size(),"one explicit optional primitive result per attempt required");
        if(decision instanceof Original){require(actualPrimitiveNumericResults.getLast().isPresent(),"original failure has no successful result to relabel");return actualPrimitiveNumericResults.getLast().orElseThrow();}
        if(decision instanceof AwaitFresh||decision instanceof Retry||decision instanceof AwaitEnding)throw new IllegalArgumentException("unfinished pause cannot be published as a completed result");
        if(decision instanceof Completed x&&x.mode()==ControlSequenceObservation.Mode.DIRECT_PAUSE)return actualPrimitiveNumericResults.getFirst().orElseThrow();
        ObjectNode base;
        if(decision instanceof Failed)base=StrictJson.object().put("step",PUBLIC_STEP).put("accepted",false).put("status","pause_recovery_failed").put("backend_id","native-headless");
        else if(((Completed)decision).mode()==ControlSequenceObservation.Mode.ALREADY_PAUSED_AFTER_REJECTION)
            base=StrictJson.object().put("step",PUBLIC_STEP).put("accepted",true).put("status","already_paused").put("backend_id","native-headless");
        else{
            JsonNode parsed=StrictJson.parse(actualPrimitiveNumericResults.getLast().orElseThrow().bytes());
            require(parsed instanceof ObjectNode,"actual primitive object required");base=((ObjectNode)parsed).deepCopy();
        }
        var recovery=StrictJson.object().put("source","generic_pause_map_unavailable_recovery");var attempts=recovery.putArray("attempts");
        for(int i=0;i<p.attempts().size();i++){
            Attempt a=p.attempts().get(i);var n=attempts.addObject().put("request_id",a.requestId());
            if(i==0)n.put("accepted",false).put("status","rejected").put("error",ControlSequenceObservation.MAP_UNAVAILABLE);
            else if(a.failure().isPresent())n.put("accepted",false).put("status","failed").put("error",a.failure().orElseThrow());
            else if(actualPrimitiveNumericResults.get(i).isPresent()){
                JsonNode parsed=StrictJson.parse(actualPrimitiveNumericResults.get(i).orElseThrow().bytes());
                require(parsed instanceof ObjectNode,"actual primitive attempt object required");n.setAll((ObjectNode)parsed);
            }
            else n.put("accepted",false).put("status","failed").put("error","original pause result unresolved");
        }
        fields(recovery,"starting",p.starting());p.refreshed().ifPresent(s->fields(recovery,"refreshed",s));
        if(p.ending().isPresent()){fields(recovery,"ending",p.ending().orElseThrow());recovery.set("ending_paused",StrictJson.parse(DriverJson.encode(new Obj(java.util.Map.of("value",get(p.ending().orElseThrow().semantic(),"paused"))))).get("value"));recovery.put("postcondition_verified",decision instanceof Completed);}
        if(decision instanceof Failed failure)recovery.put("failure",failure.reason().message());
        base.set("map_control_recovery",recovery);return new RawJson(StrictJson.canonical(base));
    }
    private static void fields(ObjectNode target,String prefix,Snapshot snapshot){
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw")){
            Value v=get(snapshot.semantic(),key);JsonNode n=StrictJson.parse(DriverJson.encode(new Obj(java.util.Map.of("value",v)))).get("value");target.set(prefix+"_"+key,n);
        }
    }
}
