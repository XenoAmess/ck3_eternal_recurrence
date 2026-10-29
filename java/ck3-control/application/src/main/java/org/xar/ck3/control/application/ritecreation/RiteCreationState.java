package org.xar.ck3.control.application.ritecreation;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;

/** Pure canonical-writer domain. A new revision, preview, connection or action ID cannot escape an original final once claim. */
public final class RiteCreationState {
    public static final String SCHEMA="xar.java.rite-creation-once/v1";
    private RiteCreationState() { }
    public record Key(Scope scope,int actor,SourceRite source){public Key{Objects.requireNonNull(scope);need(actor>0,"actual Rite claim actor required");Objects.requireNonNull(source);}}
    public record Preview(Frame frame,SourceRite source,ExactRef originalRead,ExactRef originalNativeResult){
        public Preview{Objects.requireNonNull(frame);Objects.requireNonNull(source);reference(originalRead);reference(originalNativeResult);}}
    public enum Status { CLAIMED_RESULT_UNKNOWN_NO_RETRY,KNOWN_RESULT_RETAINED_NO_RETRY,KNOWN_NO_DISPATCH_RELEASED }
    public enum Initialization { FRESH,NEXT,RESTORED_FIRST }
    public record Basis(Initialization kind,Scope scope,int actor,List<ExactRef> originalRootProof){
        public Basis{Objects.requireNonNull(kind);Objects.requireNonNull(scope);need(actor>0,"actual initialized Rite actor required");originalRootProof=List.copyOf(originalRootProof);need(!originalRootProof.isEmpty()&&originalRootProof.size()<=64,"complete bounded original Root initialization proof required");originalRootProof.forEach(RiteCreationState::reference);}}
    public enum ResultKind { ORIGINAL_NATIVE_RESULT, CANONICAL_ZERO_DISPATCH_BEFORE_WRITE }
    public record OriginalResult(String protocolRequestId,ExactRef originalPacket,ExactRef canonicalActionReceipt,ResultKind kind){
        public OriginalResult{need(protocolRequestId!=null&&protocolRequestId.matches("[A-Za-z0-9_.:-]{1,128}"),"original native request identity required");reference(originalPacket);reference(canonicalActionReceipt);Objects.requireNonNull(kind);}
        public OriginalResult(String id,ExactRef packet,ExactRef receipt){this(id,packet,receipt,ResultKind.ORIGINAL_NATIVE_RESULT);}}
    public record Claim(ActionId id,Frame frame,Execute request,ExactRef originalPreviewRead,Status status,Optional<OriginalResult> result){
        public Claim{Objects.requireNonNull(id);Objects.requireNonNull(frame);Objects.requireNonNull(request);reference(originalPreviewRead);Objects.requireNonNull(status);Objects.requireNonNull(result);
            need(request.action() instanceof Confirm&&request.expectedRevision().equals(frame.publicRevision()),"only actual final confirm enters the Rite once domain");
            need((status==Status.CLAIMED_RESULT_UNKNOWN_NO_RETRY)==result.isEmpty(),"Rite once status/original-result presence differs");}
        public Key key(){return new Key(frame.scope(),frame.actor(),request.source());}
        public boolean blocksRetry(){return status!=Status.KNOWN_NO_DISPATCH_RELEASED;}
    }
    public record State(Optional<Basis> basis,Optional<Preview> preview,List<Claim> claims){
        public State{Objects.requireNonNull(basis);Objects.requireNonNull(preview);claims=List.copyOf(claims);need(claims.size()<=128&&claims.stream().map(Claim::id).distinct().count()==claims.size(),"bounded unique canonical Rite attempt history required");
            need(basis.isPresent()||preview.isEmpty()&&claims.isEmpty(),"uninitialized Rite basis cannot own historical claims or preview");
            for(int i=0;i<claims.size();i++)if(claims.get(i).blocksRetry())for(int j=i+1;j<claims.size();j++)need(!claims.get(j).blocksRetry()||!claims.get(i).key().equals(claims.get(j).key()),"duplicate unresolved original Rite intent scope");}
        public static State empty(){return new State(Optional.empty(),Optional.empty(),List.of());}
        public Optional<Claim> find(ActionId id){return claims.stream().filter(v->v.id().equals(id)).findFirst();}
        public Optional<Claim> blocking(Key key){return claims.stream().filter(v->v.key().equals(key)&&v.blocksRetry()).findFirst();}
    }
    /** Root supplies a private qualified basis. Neither a new epoch nor a saved FIRST state clears old once/UNKNOWN history. */
    public static State initialize(State previous,Basis actual){if(previous.basis().equals(Optional.of(actual)))return previous;return new State(Optional.of(actual),Optional.empty(),previous.claims());}
    public static void requireBasis(State state,Frame current){Basis basis=state.basis().orElseThrow(()->new IllegalArgumentException("Rite domain has no actual initialized basis"));need(basis.scope().equals(current.scope())&&basis.actor()==current.actor(),"Rite basis differs from the actual current episode/campaign actor");}
    public static State observedPreview(State old,Preview retained,Result actual){
        requireBasis(old,retained.frame());need(actual.operation()==RiteCreation.PREVIEW,"only original preview can populate final native proof");same(retained.frame(),actual.frame());
        need(actual.draft().source().map(retained.source()::equals).orElse(!actual.draft().observed()),"retained preview source differs");
        return new State(old.basis(),actual.preview().isPresent()?Optional.of(retained):Optional.empty(),old.claims());
    }
    public static State invalidatePreview(State old){return new State(old.basis(),Optional.empty(),old.claims());}
    /** Runtime first verifies originalRead/token against the actual archive and current Complete, under the one writer lock. */
    public static State start(State old,Claim claim,Result originalPreview){
        requireBasis(old,claim.frame());need(claim.status()==Status.CLAIMED_RESULT_UNKNOWN_NO_RETRY&&claim.result().isEmpty(),"new Rite claim cannot carry a fabricated result");
        need(old.find(claim.id()).isEmpty()&&old.blocking(claim.key()).isEmpty(),"original Rite confirmation already claimed; collect without resend");
        Preview cached=old.preview().orElseThrow(()->new IllegalArgumentException("original post-modal preview is not retained"));
        need(cached.frame().equals(claim.frame())&&cached.source().equals(claim.request().source())&&cached.originalRead().equals(claim.originalPreviewRead()),"final confirm changed its retained post-modal native frame/request");
        same(claim.frame(),originalPreview.frame());originalPreview.requireFinalPreview((Confirm)claim.request().action());
        List<Claim> all=new ArrayList<>(old.claims());all.add(claim);return new State(old.basis(),Optional.empty(),all);
    }
    /** A matching original Native result proves no dispatch only with both native attempted=false and possible queue=false. */
    public static State originalResult(State old,ActionId id,Result actual,OriginalResult proof){
        Claim original=old.find(id).orElseThrow(()->new IllegalArgumentException("no original canonical Rite claim"));
        need(proof.kind()==ResultKind.ORIGINAL_NATIVE_RESULT&&actual.operation()==RiteCreation.CONFIRM_ONCE&&actual.originalProtocolActionId().equals(Optional.of(proof.protocolRequestId())),"retained result belongs to another original Rite request");same(original.frame(),actual.frame());
        if(original.result().isPresent()){need(original.result().equals(Optional.of(proof)),"Rite original result custody changed");return old;}
        Status status=actual.knownNoDispatch()?Status.KNOWN_NO_DISPATCH_RELEASED:Status.KNOWN_RESULT_RETAINED_NO_RETRY;
        List<Claim> all=new ArrayList<>();for(Claim claim:old.claims())all.add(claim.id().equals(id)?new Claim(claim.id(),claim.frame(),claim.request(),claim.originalPreviewRead(),status,Optional.of(proof)):claim);
        return new State(old.basis(),old.preview(),all);
    }
    /** Runtime verifies the canonical RejectedBeforeDispatch, BEFORE_WRITE and zero bytes under the original writer lock. */
    public static State beforeSendRejected(State old,ActionId id,OriginalResult proof){
        need(proof.kind()==ResultKind.CANONICAL_ZERO_DISPATCH_BEFORE_WRITE,"dedicated actual zero-write proof required");
        Claim original=old.find(id).orElseThrow();if(original.result().isPresent()){need(original.result().equals(Optional.of(proof)),"original Rite zero-write proof changed");return old;}
        List<Claim> all=new ArrayList<>();for(Claim claim:old.claims())all.add(claim.id().equals(id)?new Claim(claim.id(),claim.frame(),claim.request(),claim.originalPreviewRead(),Status.KNOWN_NO_DISPATCH_RELEASED,Optional.of(proof)):claim);
        return new State(old.basis(),old.preview(),all);
    }
    public static void same(Frame actual,NativeFrame sampled){need(actual.connectionGeneration().equals(sampled.connectionGeneration())&&actual.nativeRevision().equals(sampled.nativeRevision())&&actual.dateRaw()==sampled.dateRaw()&&actual.actor()==sampled.actor(),"original Rite result crossed actual native binding");}
    public static RawJson encode(State state){
        ObjectNode n=empty().put("schema",SCHEMA);if(state.basis().isPresent()){Basis basis=state.basis().orElseThrow();ObjectNode b=empty().put("kind",basis.kind().name()).put("scope_kind",basis.scope().kind()).put("scope_key",basis.scope().stableKey()).put("actor",basis.actor());var refs=b.putArray("original_root_proof");basis.originalRootProof().forEach(ref->refs.add(ref.toJson()));n.set("basis",b);}else n.putNull("basis");
        if(state.preview().isPresent()){Preview p=state.preview().orElseThrow();ObjectNode v=empty();v.set("frame",frame(p.frame()));v.put("source_rite_id",p.source().value());v.set("original_read",p.originalRead().toJson());v.set("original_native_result",p.originalNativeResult().toJson());n.set("preview",v);}else n.putNull("preview");
        var all=n.putArray("claims");for(Claim claim:state.claims()){
            ObjectNode v=empty().put("action_request_id",claim.id().value()).put("status",claim.status().name());v.set("frame",frame(claim.frame()));v.set("request",object(execution(claim.request())));v.set("original_preview_read",claim.originalPreviewRead().toJson());
            if(claim.result().isPresent()){var proof=claim.result().orElseThrow();ObjectNode r=empty().put("protocol_request_id",proof.protocolRequestId()).put("kind",proof.kind().name());r.set("original_packet",proof.originalPacket().toJson());r.set("canonical_action_receipt",proof.canonicalActionReceipt().toJson());v.set("original_result",r);}else v.putNull("original_result");all.add(v);
        }return raw(n);
    }
    public static State decode(RawJson original){
        ObjectNode n=object(original);shape(n,Set.of("schema","basis","preview","claims"),Set.of());equal(get(n,"schema"),SCHEMA);
        Optional<Basis> basis=nullable(n,"basis",value->{ObjectNode b=object(value);shape(b,Set.of("kind","scope_kind","scope_key","actor","original_root_proof"),Set.of());JsonNode refs=get(b,"original_root_proof");need(refs.isArray()&&refs.size()<=64,"bounded original Root proof required");List<ExactRef> proof=new ArrayList<>();refs.forEach(ref->proof.add(ExactRef.fromJson(ref)));return new Basis(Initialization.valueOf(text(get(b,"kind"))),scope(text(get(b,"scope_kind")),text(get(b,"scope_key"))),integer(get(b,"actor"),1,Integer.MAX_VALUE).intValueExact(),proof);});
        Optional<Preview> preview=nullable(n,"preview",value->{ObjectNode p=object(value);shape(p,Set.of("frame","source_rite_id","original_read","original_native_result"),Set.of());return new Preview(frame(get(p,"frame")),source(get(p,"source_rite_id")),ExactRef.fromJson(get(p,"original_read")),ExactRef.fromJson(get(p,"original_native_result")));});
        JsonNode rows=get(n,"claims");need(rows.isArray()&&rows.size()<=128,"bounded canonical Rite attempt list required");List<Claim> claims=new ArrayList<>();
        for(JsonNode item:rows){ObjectNode c=object(item);shape(c,Set.of("action_request_id","status","frame","request","original_preview_read","original_result"),Set.of());
            Optional<OriginalResult> result=nullable(c,"original_result",value->{ObjectNode r=object(value);shape(r,Set.of("protocol_request_id","original_packet","canonical_action_receipt","kind"),Set.of());return new OriginalResult(text(get(r,"protocol_request_id")),ExactRef.fromJson(get(r,"original_packet")),ExactRef.fromJson(get(r,"canonical_action_receipt")),ResultKind.valueOf(text(get(r,"kind"))));});
            claims.add(new Claim(new ActionId(text(get(c,"action_request_id"))),frame(get(c,"frame")),execute(raw(get(c,"request"))),ExactRef.fromJson(get(c,"original_preview_read")),Status.valueOf(text(get(c,"status"))),result));
        }State state=new State(basis,preview,claims);need(encode(state).equals(original),"canonical Rite state representation changed");return state;
    }
    public static ObjectNode frame(Frame value){ObjectNode n=empty().put("snapshot_id",value.snapshotId()).put("public_revision",value.publicRevision().toString()).put("native_revision",value.nativeRevision().toString()).put("connection_generation",value.connectionGeneration().toString()).put("game_pid",value.gamePid()).put("played_character_id",value.actor()).put("date_raw",value.dateRaw());n.putObject("intent_scope").put("kind",value.scope().kind()).put("stable_key",value.scope().stableKey());return n;}
    public static Frame frame(JsonNode value){ObjectNode n=object(value);shape(n,Set.of("snapshot_id","public_revision","native_revision","connection_generation","game_pid","played_character_id","date_raw","intent_scope"),Set.of());ObjectNode scope=object(get(n,"intent_scope"));shape(scope,Set.of("kind","stable_key"),Set.of());String kind=text(get(scope,"kind")),key=text(get(scope,"stable_key"));Scope bound=switch(kind){case "actual_episode_v1"->new EpisodeScope(key);case "managed_campaign_state_v1"->new ManagedScope(key);default->throw new IllegalArgumentException("foreign Rite intent scope");};return new Frame(text(get(n,"snapshot_id")),publicU64(get(n,"public_revision")),publicU64(get(n,"native_revision")),publicU64(get(n,"connection_generation")),integer(get(n,"game_pid"),1,0xffff_ffffL).longValueExact(),integer(get(n,"played_character_id"),1,Integer.MAX_VALUE).intValueExact(),integer(get(n,"date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE).intValueExact(),bound);}
    private static void reference(ExactRef ref){need(ref!=null&&ref.bytes()>0,"original nonempty Rite custody reference required");}
    private static Scope scope(String kind,String key){return switch(kind){case "actual_episode_v1"->new EpisodeScope(key);case "managed_campaign_state_v1"->new ManagedScope(key);default->throw new IllegalArgumentException("foreign Rite intent scope");};}
}
