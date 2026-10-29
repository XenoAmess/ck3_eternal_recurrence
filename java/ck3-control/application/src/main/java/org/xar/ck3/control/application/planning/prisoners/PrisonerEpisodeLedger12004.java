package org.xar.ck3.control.application.planning.prisoners;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.Family;

/** Versioned episode DATA. Only the sole writer's actual original producer may import it. */
public final class PrisonerEpisodeLedger12004 {
    public static final int MAX_BYTES=1_048_576;
    public enum Kind { FRESH, NEXT }
    public enum InitializationKind { NEXT, RESTORED_FIRST }
    public record Owner(SessionIdentity session,long player,String episodeRunId,G2Source source) {
        public Owner {Objects.requireNonNull(session);Objects.requireNonNull(source);NativeCharacterId.of(player);StrictJson.text(episodeRunId);
            need(session.machineId().equals(source.machineId()),"prisoner owner crossed its actual source machine");}
        public void require(ObservationIdentity frame,G2Source actualSource,String actualSession) {
            need(session.game().equals(frame.game())&&session.machineId().equals(frame.machineId())&&session.sessionId().equals(actualSession)
                    &&episodeRunId.equals(frame.frame().episodeRunId())&&BigInteger.valueOf(player).equals(frame.frame().identity().player())
                    &&source.equals(actualSource),"prisoner ledger belongs to a different Game/player/episode/source/session");
        }
    }
    /** Original FIRST save identity and current physical identity remain independent serialized DATA. */
    public record InitializationOrigins(InitializationKind kind,SessionIdentity savedSession,ObservationIdentity savedFrame,
            Owner currentOwner,ObservationIdentity currentFrame,Baseline initializationHead) {
        public InitializationOrigins {Objects.requireNonNull(kind);Objects.requireNonNull(savedSession);Objects.requireNonNull(savedFrame);
            Objects.requireNonNull(currentOwner);Objects.requireNonNull(currentFrame);Objects.requireNonNull(initializationHead);
            need(savedSession.machineId().equals(savedFrame.machineId())&&savedSession.game().equals(savedFrame.game()),"original saved SEM must retain its actual saved Game/session");
            currentOwner.require(currentFrame,currentOwner.source(),currentOwner.session().sessionId());
            need(savedFrame.machineId().equals(currentFrame.machineId())&&savedFrame.frame().identity().player().equals(BigInteger.valueOf(currentOwner.player()))
                    &&savedFrame.frame().episodeRunId().equals(currentOwner.episodeRunId())
                    &&savedFrame.frame().identity().dateRaw().equals(currentFrame.frame().identity().dateRaw()),"FIRST restoration must retain the saved actor/episode/day without borrowing its physical Game");
            need(kind==InitializationKind.NEXT?savedSession.equals(currentOwner.session()):!savedSession.game().equals(currentOwner.session().game()),
                    "NEXT and RESTORED_FIRST have distinct saved/current physical identity rules");}
    }
    public record Collection(ExactRef originalReceipt,ObservationIdentity observed,BigInteger querySequence,List<Long> prisonerIds) {
        public Collection {original(originalReceipt);Objects.requireNonNull(observed);u64(querySequence,true);prisonerIds=List.copyOf(prisonerIds);
            need(prisonerIds.size()<=64&&new HashSet<>(prisonerIds).size()==prisonerIds.size(),"complete distinct bounded current prisoner IDs required");prisonerIds.forEach(PrisonerEpisodeLedger12004::id);}
    }
    public record PriorInitialization(DomainBodies.BodyRef body,Owner owner,Collection collection,List<ExactRef> sourceProofs) {
        public PriorInitialization {Objects.requireNonNull(body);Objects.requireNonNull(owner);Objects.requireNonNull(collection);original(body.payload());
            need(body.slot()==DomainBodies.Slot.PRISONER_RELEASE||body.slot()==DomainBodies.Slot.PRISONER_RANSOM,"prior initialization must name an actual prisoner slot");
            sourceProofs=List.copyOf(sourceProofs);need(sourceProofs.size()<=2&&new HashSet<>(sourceProofs).size()==sourceProofs.size(),"precise prior physical source proof originals required");
            sourceProofs.forEach(PrisonerEpisodeLedger12004::original);owner.require(collection.observed(),owner.source(),owner.session().sessionId());}
    }
    public record Predecessor(Owner owner,DomainBodies.BodyRef body) {
        public Predecessor {Objects.requireNonNull(owner);Objects.requireNonNull(body);original(body.payload());}
    }
    public record Baseline(long sequence,String digest) {
        public Baseline {need(sequence>0&&sequence<=StrictJson.MAX_SAFE_INTEGER,"actual positive BASELINE sequence required");PrisonerEpisodeLedger12004.digest(digest);}
    }
    public record Epoch(Kind kind,Owner owner,ExactRef basis,Optional<Baseline> baseline,
            Optional<Predecessor> predecessor,Optional<Collection> collection) {
        public Epoch {Objects.requireNonNull(kind);Objects.requireNonNull(owner);original(basis);Objects.requireNonNull(baseline);Objects.requireNonNull(predecessor);Objects.requireNonNull(collection);
            need((kind==Kind.NEXT)==baseline.isPresent()&&(kind==Kind.NEXT)==predecessor.isPresent(),"fresh and actual NEXT have different closed original bases");
            need(kind!=Kind.NEXT||collection.isPresent(),"NEXT cannot initialize from unavailable/unobserved custody");
            predecessor.ifPresent(prior->need(prior.owner().session().machineId().equals(owner.session().machineId())
                    &&!prior.owner().session().game().equals(owner.session().game()),"NEXT requires the actual distinct replacement Game"));
            collection.ifPresent(value->owner.require(value.observed(),owner.source(),owner.session().sessionId()));}
    }
    public record RetainedUnknown(Owner owner,DomainBodies.BodyRef originalBody,RawJson originalPending) {
        public RetainedUnknown {Objects.requireNonNull(owner);Objects.requireNonNull(originalBody);Objects.requireNonNull(originalPending);original(originalBody.payload());}
    }
    public record Ledger(Family family,Epoch epoch,Optional<RawJson> pending,Optional<RawJson> resolved,List<RetainedUnknown> inheritedUnknowns) {
        public Ledger {Objects.requireNonNull(family);Objects.requireNonNull(epoch);Objects.requireNonNull(pending);Objects.requireNonNull(resolved);inheritedUnknowns=List.copyOf(inheritedUnknowns);
            need(inheritedUnknowns.size()<=256,"bounded retained UNKNOWN ancestry required; no truncation permitted");
            pending.ifPresent(value->{var identity=PrisonerPendingIdentity12004.decode(family,value);need(identity.actor()==epoch.owner().player(),"current pending belongs to another player");});
            resolved.ifPresent(value->need(StrictJson.parse(value.bytes(),MAX_BYTES).isObject(),"current resolved material must be an object"));
            var refs=new HashSet<ExactRef>();
            for(var inherited:inheritedUnknowns){need(inherited.originalBody().slot()==slot(family)&&refs.add(inherited.originalBody().payload()),"retained UNKNOWN original slot/body must be distinct");
                var pendingIdentity=PrisonerPendingIdentity12004.decode(family,inherited.originalPending());
                need(pendingIdentity.actor()==inherited.owner().player()&&!inherited.owner().session().game().equals(epoch.owner().session().game()),"old UNKNOWN cannot become new Game custody");}
            epoch.predecessor().ifPresent(prior->need(prior.body().slot()==slot(family),"NEXT previous body has a different prisoner slot"));}
    }
    private PrisonerEpisodeLedger12004() { }
    public static String schema(Family family) {Objects.requireNonNull(family);return family==Family.RELEASE?"xar.java.prisoner-release-ledger-body/v2":"xar.java.prisoner-ransom-ledger-body/v2";}
    public static String contractSchema(Family family) {Objects.requireNonNull(family);return family==Family.RELEASE?"xar.java.prisoner-release-ledger/v2":"xar.java.prisoner-ransom-ledger/v2";}
    public static boolean isV2(Family family,JsonNode value) {return value!=null&&value.isObject()&&schema(family).equals(value.path("schema").textValue());}
    public static RawJson fresh(Family family,Owner actual,ExactRef initialBasis) {
        return encode(new Ledger(family,new Epoch(Kind.FRESH,actual,initialBasis,Optional.empty(),Optional.empty(),Optional.empty()),Optional.empty(),Optional.empty(),List.of()));
    }
    /** Reads every old pending intact; original-body refs retain prior resolved material and earlier episode history. */
    public static RawJson next(Family family,RawJson previous,Owner previousOwner,DomainBodies.BodyRef originalBody,Epoch actualNext) {
        Objects.requireNonNull(previous);need(actualNext.kind()==Kind.NEXT&&actualNext.predecessor().orElseThrow().equals(new Predecessor(previousOwner,originalBody)),"exact actual previous owner/body required");
        JsonNode old=StrictJson.parse(previous.bytes(),MAX_BYTES);PrisonerLedgerReducer12004.validate(family,old);
        var retained=new ArrayList<RetainedUnknown>();
        if(isV2(family,old)){var decoded=decode(family,previous);need(decoded.epoch().owner().equals(previousOwner),"previous body belongs to another original episode");retained.addAll(decoded.inheritedUnknowns());}
        if(!old.get("pending").isNull()){
            RawJson pending=new RawJson(StrictJson.canonical(old.get("pending"),MAX_BYTES));
            need(PrisonerPendingIdentity12004.decode(family,pending).actor()==previousOwner.player(),"legacy original pending has no actual old actor binding");
            retained.add(new RetainedUnknown(previousOwner,originalBody,pending));
        }
        return encode(new Ledger(family,actualNext,Optional.empty(),Optional.empty(),retained));
    }
    public static RawJson encode(Ledger value) {
        ObjectNode row=StrictJson.object().put("schema",schema(value.family()));row.set("epoch",epoch(value.epoch()));
        put(row,"pending",value.pending());put(row,"resolved",value.resolved());var inherited=row.putArray("inherited_unknowns");
        for(var entry:value.inheritedUnknowns()){var item=inherited.addObject();item.set("owner",owner(entry.owner()));item.set("original_body",entry.originalBody().toJson());
            item.set("original_pending",StrictJson.parse(entry.originalPending().bytes(),MAX_BYTES));item.put("replay_allowed",false).put("current_custody_claim",false);}
        return new RawJson(StrictJson.canonical(row,MAX_BYTES));
    }
    public static Ledger decode(Family family,RawJson value) {
        JsonNode row=StrictJson.parse(value.bytes(),MAX_BYTES);StrictJson.object(row,Set.of("schema","epoch","pending","resolved","inherited_unknowns"));
        need(schema(family).equals(StrictJson.text(row.get("schema"))),"unsupported prisoner episode body schema");
        JsonNode unknowns=row.get("inherited_unknowns");need(unknowns.isArray()&&unknowns.size()<=256,"explicit bounded inherited UNKNOWN array required");
        var retained=new ArrayList<RetainedUnknown>();for(JsonNode item:unknowns){StrictJson.object(item,Set.of("owner","original_body","original_pending","replay_allowed","current_custody_claim"));
            need(!bool(item.get("replay_allowed"))&&!bool(item.get("current_custody_claim")),"inherited UNKNOWN cannot replay or claim current custody");
            need(item.get("original_pending").isObject(),"full inherited original pending required");retained.add(new RetainedUnknown(owner(item.get("owner")),DomainBodies.BodyRef.fromJson(item.get("original_body")),raw(item.get("original_pending"))));}
        return new Ledger(family,epoch(row.get("epoch")),optionalObject(row.get("pending")),optionalObject(row.get("resolved")),retained);
    }
    public static ObjectNode epoch(Epoch value) {
        var row=StrictJson.object().put("schema","xar.java.prisoner-episode-basis/v1").put("kind",value.kind().name());row.set("owner",owner(value.owner()));row.set("basis",value.basis().toJson());
        if(value.baseline().isPresent()){var baseline=value.baseline().orElseThrow();row.putObject("baseline").put("sequence",baseline.sequence()).put("digest",baseline.digest());}else row.putNull("baseline");
        if(value.predecessor().isPresent()){var prior=value.predecessor().orElseThrow();var n=row.putObject("predecessor");n.set("owner",owner(prior.owner()));n.set("body",prior.body().toJson());}else row.putNull("predecessor");
        if(value.collection().isPresent())row.set("collection",collection(value.collection().orElseThrow()));else row.putNull("collection");return row;
    }
    public static Epoch epoch(JsonNode row) {
        StrictJson.object(row,Set.of("schema","kind","owner","basis","baseline","predecessor","collection"));need("xar.java.prisoner-episode-basis/v1".equals(StrictJson.text(row.get("schema"))),"episode basis schema differs");
        Optional<Baseline> baseline=Optional.empty();if(!row.get("baseline").isNull()){var n=StrictJson.object(row.get("baseline"),Set.of("sequence","digest"));baseline=Optional.of(new Baseline(StrictJson.integer(n.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(n.get("digest"))));}
        Optional<Predecessor> prior=Optional.empty();if(!row.get("predecessor").isNull()){var n=StrictJson.object(row.get("predecessor"),Set.of("owner","body"));prior=Optional.of(new Predecessor(owner(n.get("owner")),DomainBodies.BodyRef.fromJson(n.get("body"))));}
        Optional<Collection> collection=Optional.empty();if(!row.get("collection").isNull())collection=Optional.of(collection(row.get("collection")));
        return new Epoch(Kind.valueOf(StrictJson.text(row.get("kind"))),owner(row.get("owner")),ExactRef.fromJson(row.get("basis")),baseline,prior,collection);
    }
    public static ObjectNode owner(Owner value) {var row=StrictJson.object();row.set("session",OrdinaryCycleTransitions.sessionToJson(value.session()));row.put("player_id",value.player()).put("episode_run_id",value.episodeRunId());row.set("source",ProposalLifecycleCodec.source(value.source()));return row;}
    public static Owner owner(JsonNode value) {var row=StrictJson.object(value,Set.of("session","player_id","episode_run_id","source"));return new Owner(OrdinaryCycleTransitions.sessionFromJson(row.get("session")),NativeCharacterId.fromJson(row.get("player_id")).value(),StrictJson.text(row.get("episode_run_id")),G2Wire.source(row.get("source")));}
    public static ObjectNode collection(Collection value) {
        Objects.requireNonNull(value);var row=StrictJson.object();row.set("original_receipt",value.originalReceipt().toJson());row.set("observed",ProposalLifecycleCodec.observation(value.observed()));
        row.put("query_sequence",value.querySequence().toString());var ids=row.putArray("prisoner_ids");value.prisonerIds().forEach(ids::add);return row;
    }
    public static Collection collection(JsonNode value) {
        var row=StrictJson.object(value,Set.of("original_receipt","observed","query_sequence","prisoner_ids"));JsonNode ids=row.get("prisoner_ids");
        need(ids.isArray()&&ids.size()<=64,"explicit complete prisoner IDs required");var values=new ArrayList<Long>();for(JsonNode id:ids)values.add(StrictJson.integer(id,1,0xFFFF_FFFEL));
        return new Collection(ExactRef.fromJson(row.get("original_receipt")),ProposalLifecycleCodec.decodeObservation(row.get("observed")),
                new BigInteger(new CrossJsDecimalUInt64(StrictJson.text(row.get("query_sequence"))).decimal()),values);
    }
    public static ObjectNode prior(PriorInitialization value) {
        Objects.requireNonNull(value);var row=StrictJson.object().put("schema","xar.java.prisoner-prior-initialization/v1");row.set("body",value.body().toJson());
        row.set("owner",owner(value.owner()));row.set("collection",collection(value.collection()));var refs=row.putArray("source_proofs");value.sourceProofs().forEach(ref->refs.add(ref.toJson()));return row;
    }
    public static PriorInitialization prior(JsonNode value) {
        var row=StrictJson.object(value,Set.of("schema","body","owner","collection","source_proofs"));need("xar.java.prisoner-prior-initialization/v1".equals(StrictJson.text(row.get("schema"))),"unsupported prior initialization provenance schema");
        var refs=row.get("source_proofs");need(refs.isArray()&&refs.size()<=2,"explicit prior original source proof refs required");var values=new ArrayList<ExactRef>();for(JsonNode ref:refs)values.add(ExactRef.fromJson(ref));
        return new PriorInitialization(DomainBodies.BodyRef.fromJson(row.get("body")),owner(row.get("owner")),collection(row.get("collection")),values);
    }
    public static ObjectNode origins(InitializationOrigins value) {
        Objects.requireNonNull(value);var row=StrictJson.object().put("schema","xar.java.prisoner-initialization-origins/v1").put("kind",value.kind().name());
        row.set("saved_session",OrdinaryCycleTransitions.sessionToJson(value.savedSession()));row.set("saved_frame",ProposalLifecycleCodec.observation(value.savedFrame()));
        row.set("current_owner",owner(value.currentOwner()));row.set("current_frame",ProposalLifecycleCodec.observation(value.currentFrame()));
        row.putObject("initialization_head").put("sequence",value.initializationHead().sequence()).put("digest",value.initializationHead().digest());return row;
    }
    public static InitializationOrigins origins(JsonNode value) {
        var row=StrictJson.object(value,Set.of("schema","kind","saved_session","saved_frame","current_owner","current_frame","initialization_head"));
        need("xar.java.prisoner-initialization-origins/v1".equals(StrictJson.text(row.get("schema"))),"unsupported initialization origin schema");
        var head=StrictJson.object(row.get("initialization_head"),Set.of("sequence","digest"));
        return new InitializationOrigins(InitializationKind.valueOf(StrictJson.text(row.get("kind"))),OrdinaryCycleTransitions.sessionFromJson(row.get("saved_session")),
                ProposalLifecycleCodec.decodeObservation(row.get("saved_frame")),owner(row.get("current_owner")),ProposalLifecycleCodec.decodeObservation(row.get("current_frame")),
                new Baseline(StrictJson.integer(head.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(head.get("digest"))));
    }
    private static void put(ObjectNode row,String key,Optional<RawJson> value){if(value.isPresent())row.set(key,StrictJson.parse(value.orElseThrow().bytes(),MAX_BYTES));else row.putNull(key);}
    private static Optional<RawJson> optionalObject(JsonNode value){need(value!=null&&(value.isNull()||value.isObject()),"explicit object/null required");return value.isNull()?Optional.empty():Optional.of(raw(value));}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value,MAX_BYTES));}
    private static boolean bool(JsonNode value){need(value!=null&&value.isBoolean(),"actual JSON boolean required");return value.booleanValue();}
    private static DomainBodies.Slot slot(Family family){return family==Family.RELEASE?DomainBodies.Slot.PRISONER_RELEASE:DomainBodies.Slot.PRISONER_RANSOM;}
    private static void id(long value){need(value>0&&value<0xFFFF_FFFFL,"exact full uint32 character ID required");}
    private static void u64(BigInteger value,boolean positive){need(value!=null&&value.signum()>=(positive?1:0)&&value.compareTo(StrictJson.UINT64_MAX)<=0,"exact canonical uint64 required");}
    private static void original(ExactRef value){Objects.requireNonNull(value);need(value.bytes()>0,"nonempty actual original reference required");}
    private static void digest(String value){need(value!=null&&value.matches("[a-f0-9]{64}"),"exact canonical digest required");}
    private static void need(boolean value,String message){StrictJson.require(value,message);}
}
