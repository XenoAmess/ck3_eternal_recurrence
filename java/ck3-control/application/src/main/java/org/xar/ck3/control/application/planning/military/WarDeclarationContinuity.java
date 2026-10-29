package org.xar.ck3.control.application.planning.military;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;

/**
 * The original declaration continuity DATA reducer. The canonical INTENT and
 * retained preflight inputs supply durable arming; this class owns no sidecar,
 * writer, waiter or dispatch authority.
 */
public final class WarDeclarationContinuity {
    public static final String SCHEMA="war-declaration-continuity-v1";
    private static final String SCOPE="unique_new_primary_attacker_opponent_and_target_titles";
    private static final int MAX_BYTES=32768;
    private WarDeclarationContinuity() { }
    public enum Status {
        SUBMISSION_UNKNOWN("submission_unknown"),DECLARATION_SUBMITTED("declaration_submitted"),WAR_STARTED("war_started"),
        NATIVE_REJECTED("native_rejected"),NOT_SUBMITTED("not_submitted");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status exact(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("unknown declaration continuity status");}
    }
    public enum NativeResponse { UNKNOWN,ACCEPTED,REJECTED }
    public enum Reason {
        ORIGINAL_REQUEST_NOT_YET_OBSERVED("original_request_not_yet_observed"),
        AWAITING_UNIQUE_ACTUAL_WAR("awaiting_unique_actual_war"),
        ACTUAL_PROCESS_CONNECTION_OR_EPISODE_CHANGED("actual_process_connection_or_episode_changed"),
        UNIQUE_NEW_WAR_MATCHES_ACTUAL_PUBLISHED_IDENTITY("unique_new_war_matches_actual_published_identity"),
        AMBIGUOUS_NEW_WARS("ambiguous_new_wars"),
        ACTUAL_ROLE_TITLE_OR_FRESH_FRAME_IDENTITY_UNAVAILABLE("actual_role_title_or_fresh_frame_identity_unavailable"),
        ORIGINAL_NATIVE_REQUEST_REFUSED("original_native_request_refused"),
        PRIMITIVE_REJECTED_BEFORE_SEND("primitive_rejected_before_send");
        private final String wire;Reason(String wire){this.wire=wire;}public String wire(){return wire;}
        static Reason exact(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("unknown declaration continuity reason");}
    }
    public record Owner(int actorCharacterId,Value episodeRunId,int bridgePid,int helloPid,BigInteger connectionGeneration) {
        public Owner {
            StrictJson.require(actorCharacterId>0 && bridgePid>0 && helloPid==bridgePid,"original declaration actor/process/HELLO identity required");
            Objects.requireNonNull(episodeRunId);Objects.requireNonNull(connectionGeneration);
            StrictJson.require(connectionGeneration.signum()>0,"original declaration connection must be positive");
        }
    }
    public record Roles(int primaryAttacker,int primaryDefender) {
        public Roles {StrictJson.require(primaryAttacker>0 && primaryDefender>0,"actual finalized positive declaration roles required");}
    }
    public record Origin(String requestId,DeclarationContract.Choice declaration,List<Integer> beforeWarIds,
            Optional<Roles> finalRoles,Owner owner,String submittedSnapshotId,BigInteger submittedRevision,
            BigInteger submittedNativeRevision,BigInteger submittedDateRaw) {
        public Origin {
            StrictJson.text(requestId);Objects.requireNonNull(declaration);beforeWarIds=List.copyOf(beforeWarIds);
            StrictJson.require(beforeWarIds.size()<=256 && beforeWarIds.stream().allMatch(id->id>=0)
                    && beforeWarIds.stream().distinct().count()==beforeWarIds.size(),"bounded unique original before-war IDs required");
            Objects.requireNonNull(finalRoles);Objects.requireNonNull(owner);StrictJson.text(submittedSnapshotId);
            Objects.requireNonNull(submittedRevision);Objects.requireNonNull(submittedNativeRevision);Objects.requireNonNull(submittedDateRaw);
        }
    }
    public record Observed(String snapshotId,BigInteger nativeRevision) {
        public Observed {StrictJson.text(snapshotId);Objects.requireNonNull(nativeRevision);}
    }
    public record Record(Origin origin,Status status,NativeResponse nativeResponse,boolean inFlight,
            OptionalInt warId,boolean postconditionVerified,Optional<Observed> observed,Reason reason) {
        public Record {
            Objects.requireNonNull(origin);Objects.requireNonNull(status);Objects.requireNonNull(nativeResponse);
            Objects.requireNonNull(warId);Objects.requireNonNull(observed);Objects.requireNonNull(reason);
            StrictJson.require(warId.isEmpty()||warId.getAsInt()>=0,"complete nonnegative observed war ID required");
            boolean started=status==Status.WAR_STARTED;
            StrictJson.require(started==postconditionVerified && started==warId.isPresent() && started==observed.isPresent(),
                    "declaration success requires all actual observation fields");
            StrictJson.require(!started || nativeResponse==NativeResponse.ACCEPTED && !inFlight
                    && reason==Reason.UNIQUE_NEW_WAR_MATCHES_ACTUAL_PUBLISHED_IDENTITY,"war started requires the original accepted request and unique observed identity");
            StrictJson.require(!started || observed.orElseThrow().nativeRevision().compareTo(origin.submittedNativeRevision())>0
                    && !origin.beforeWarIds().contains(warId.orElseThrow()) && origin.finalRoles().isPresent()
                    && origin.owner().actorCharacterId()==origin.finalRoles().orElseThrow().primaryAttacker()
                    && !origin.declaration().targetTitleIds().isEmpty(),"persisted declaration success lacks its fresh role/title/new-war prerequisites");
            StrictJson.require(started || reason!=Reason.UNIQUE_NEW_WAR_MATCHES_ACTUAL_PUBLISHED_IDENTITY,"non-success cannot claim the unique observed declaration reason");
            StrictJson.require(switch(status) {
                case SUBMISSION_UNKNOWN -> nativeResponse==NativeResponse.UNKNOWN;
                case DECLARATION_SUBMITTED,WAR_STARTED -> nativeResponse==NativeResponse.ACCEPTED && !inFlight;
                case NATIVE_REJECTED -> nativeResponse==NativeResponse.REJECTED && !inFlight;
                case NOT_SUBMITTED -> nativeResponse==NativeResponse.UNKNOWN && !inFlight;
            },"persisted declaration response/status differs");
        }
    }

    /** Reopens the two pre-INTENT originals. Caller separately checks same-writer canonical membership. */
    public static Record replay(ActionReceipt canonical,List<ActionReceipt> canonicalBeforeIntent,Complete before,
            Complete after,ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(canonical);Objects.requireNonNull(canonicalBeforeIntent);Objects.requireNonNull(before);
        Objects.requireNonNull(after);Objects.requireNonNull(archive);
        var command=canonical.command();var args=ArmyOrdinaryActionArguments.decode(command.arguments());
        StrictJson.require(args.kind()==ArmyOrdinaryActionArguments.Kind.DECLARE_WAR && args.preflightReads().size()==2
                && command.before().equals(before.identity()) && command.source().equals(before.source())
                && command.sessionId().equals(before.sessionId()),"declaration original command/frame/ref inventory changed");
        StrictJson.require(OrdinaryWarAdmissionRules.declaration(before.semantic(),canonicalBeforeIntent)==OrdinaryWarAdmissionRules.Declaration.CLEAR,
                "an earlier canonical declaration remained unresolved at this INTENT; no second arming");
        var attempt=ActionTransitions.attempt(canonical.state()).orElseThrow(()->new IllegalArgumentException("canonical declaration has no durable original attempt"));
        var call=(ArmyCalls.Declaration)ArmyCallCodec.decode(PublicMethod.DECLARE_WAR,args.publicArguments());
        StrictJson.require(command.operation().value().equals("declare-war-"+call.declarationId())
                && attempt.preparedRequest().step().equals(command.operation().value()),"canonical declaration request changed");
        var declarations=original(args.preflightReads().getFirst(),before,archive);
        StrictJson.require(declarations.request().operation().value().equals("query-declarable-wars"),"first original is not the declaration catalogue");
        var context=new ArmyTypes.Context(before.identity(),before.source(),before.sessionId(),declarations.request().deadline());
        var query=ArmyCallCodec.decode(PublicMethod.QUERY_DECLARABLE_WARS,new RawJson(DriverJson.encode(declarations.request().arguments())));
        var decoded=(ArmyWarReadCodec.Declarations)ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(query,context,before.semantic(),Optional.empty()),declarations);
        List<DeclarationContract.Choice> selected=decoded.choices().stream().filter(value->value.declarationId().equals(call.declarationId())).toList();
        StrictJson.require(selected.size()==1,"actual pre-INTENT chosen declaration is absent or ambiguous");
        var finalRead=original(args.preflightReads().getLast(),before,archive);
        var roleCall=ArmyCallCodec.decode(PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2,new RawJson(DriverJson.encode(finalRead.request().arguments())));
        StrictJson.require(roleCall instanceof ArmyCalls.Declaration role && role.declarationId().equals(call.declarationId()),
                "original final-role read changed the selected declaration");
        var finalContext=new ArmyTypes.Context(before.identity(),before.source(),before.sessionId(),finalRead.request().deadline());
        var coalition=(ArmyWarReadCodec.CoalitionV2)ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(roleCall,finalContext,before.semantic(),
                Optional.of(selected.getFirst())),finalRead);
        Obj domain=object(coalition.normalizedResult().get("prewar_force_coalition_coverage_v2"),"actual final CB coverage");
        Optional<Roles> roles=roles(domain.get("final_cb_roles"));
        Origin origin=arm(before.semantic(),selected.getFirst(),roles,attempt.requestId());
        var retained=ActionTransitions.dispatch(canonical.state());
        Record armed=new Record(origin,Status.SUBMISSION_UNKNOWN,NativeResponse.UNKNOWN,
                canonical.state() instanceof ActionState.Submitting,OptionalInt.empty(),false,Optional.empty(),Reason.ORIGINAL_REQUEST_NOT_YET_OBSERVED);
        // Canonical SUBMITTING/UNKNOWN already owns the original request. A missing
        // response is DATA, never permission to reconstruct or resend a request.
        if(retained.isEmpty())return observe(armed,after.semantic());
        var dispatch=retained.orElseThrow();
        StrictJson.require(dispatch.equals(archive.load(archive.referenceOf(dispatch))) && dispatch.requestId().equals(origin.requestId()),
                "original canonical declaration dispatch custody changed");
        if(dispatch instanceof NativeActionPort.RejectedBeforeDispatch)
            return new Record(origin,Status.NOT_SUBMITTED,NativeResponse.UNKNOWN,false,OptionalInt.empty(),false,Optional.empty(),Reason.PRIMITIVE_REJECTED_BEFORE_SEND);
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))return observe(armed,after.semantic());
        if(!ack.nativeOk())return mark(armed,false);
        StrictJson.require(ack.originalResultToken().isPresent(),"declaration original ACK token is missing");
        Obj raw=DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),MAX_BYTES);
        StrictJson.require(text(raw,"step").equals(command.operation().value()),"declaration ACK belongs to another primitive");
        StrictJson.require(raw.get("accepted") instanceof Bool,"original declaration response accepted must be a boolean");
        Record marked=mark(armed,bool(raw,"accepted"));
        return observe(marked,after.semantic());
    }

    private static PlanningReadReceipt original(org.xar.ck3.control.contracts.ExactRef ref,Complete before,ActionPorts.OutcomeArchive archive) {
        var read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);
        StrictJson.require(archive.readReferenceOf(read).equals(ref),"declaration original read custody changed");
        ArmyOrdinaryPreflight.bind(read,before);return read;
    }
    /** DATA construction is not durable arming; only replay above binds these values to an existing canonical INTENT. */
    public static Origin arm(Obj before,DeclarationContract.Choice declaration,Optional<Roles> roles,String requestId) {
        var physical=OrdinaryWarAdmissionRules.declarationBefore(before);
        var actualOwner=new Owner(physical.actorCharacterId(),getOr(before,"episode_run_id",Nil.INSTANCE),physical.bridgePid(),
                physical.bridgePid(),physical.connectionGeneration());
        return new Origin(requestId,declaration,physical.fullWarIds(),roles,actualOwner,text(before,"snapshot_id"),
                integer(before,"revision"),integer(before,"native_revision"),integer(before,"date_raw"));
    }
    public static Record mark(Record original,boolean accepted) {
        StrictJson.require(original.status()==Status.SUBMISSION_UNKNOWN,"only the original unresolved declaration can receive its response");
        return new Record(original.origin(),accepted?Status.DECLARATION_SUBMITTED:Status.NATIVE_REJECTED,
                accepted?NativeResponse.ACCEPTED:NativeResponse.REJECTED,false,OptionalInt.empty(),false,Optional.empty(),
                accepted?Reason.AWAITING_UNIQUE_ACTUAL_WAR:Reason.ORIGINAL_NATIVE_REQUEST_REFUSED);
    }
    public static Record observe(Record pending,Obj snapshot) {
        if(pending.status()==Status.WAR_STARTED || pending.status()==Status.NATIVE_REJECTED || pending.status()==Status.NOT_SUBMITTED)return pending;
        Owner current;
        try{current=owner(snapshot);}catch(IllegalArgumentException invalid){return reason(pending,Reason.ACTUAL_PROCESS_CONNECTION_OR_EPISODE_CHANGED);}
        if(!current.equals(pending.origin().owner()))return reason(pending,Reason.ACTUAL_PROCESS_CONNECTION_OR_EPISODE_CHANGED);
        var origin=pending.origin();var selected=origin.finalRoles();
        Obj choice=DriverJson.object(StrictJson.canonical(DeclarationContract.encodeChoice(origin.declaration())),MAX_BYTES);
        Value titles=choice.get("target_title_ids"),wars=snapshot.get("active_wars");
        boolean canMatch=snapshot.get("native_revision") instanceof IntegerValue rev && rev.value().compareTo(origin.submittedNativeRevision())>0
                && flag(snapshot,"paused") && flag(snapshot,"map_ready") && wars instanceof Arr rows && rows.items().size()<=256
                && selected.isPresent() && titles instanceof Arr values && !values.items().isEmpty()
                && origin.owner().actorCharacterId()==selected.orElseThrow().primaryAttacker();
        var matches=new ArrayList<Integer>();
        if(canMatch)for(Value value:((Arr)wars).items()) {
            if(!(value instanceof Obj row) || !(row.get("war_id") instanceof IntegerValue id)
                    || id.value().signum()<0 || id.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))>0)continue;
            int war=id.value().intValueExact();
            if(!origin.beforeWarIds().contains(war) && textEquals(row,"player_side","attacker")
                    && flag(row,"player_is_primary_war_leader") && integerEquals(row.get("primary_opponent_character_id"),selected.orElseThrow().primaryDefender())
                    && titles.equals(row.get("targeted_title_ids")))matches.add(war);
        }
        if(matches.size()==1 && pending.nativeResponse()==NativeResponse.ACCEPTED)
            return new Record(origin,Status.WAR_STARTED,NativeResponse.ACCEPTED,false,OptionalInt.of(matches.getFirst()),true,
                    Optional.of(new Observed(text(snapshot,"snapshot_id"),integer(snapshot,"native_revision"))),
                    Reason.UNIQUE_NEW_WAR_MATCHES_ACTUAL_PUBLISHED_IDENTITY);
        return reason(pending,matches.size()>1?Reason.AMBIGUOUS_NEW_WARS:canMatch?Reason.AWAITING_UNIQUE_ACTUAL_WAR
                :Reason.ACTUAL_ROLE_TITLE_OR_FRESH_FRAME_IDENTITY_UNAVAILABLE);
    }
    private static Record reason(Record original,Reason reason) {
        return new Record(original.origin(),original.status(),original.nativeResponse(),original.inFlight(),original.warId(),
                original.postconditionVerified(),original.observed(),reason);
    }
    private static Owner owner(Obj snapshot) {
        Obj player=object(get(snapshot,"played_character"),"declaration player");
        Obj diagnostics=object(get(snapshot,"diagnostics"),"declaration diagnostics");
        Obj hello=object(get(diagnostics,"hello"),"declaration actual HELLO");
        return new Owner(i32(player,"character_id",1),getOr(snapshot,"episode_run_id",Nil.INSTANCE),i32(diagnostics,"bridge_pid",1),
                i32(hello,"pid",1),integer(diagnostics,"connection_generation"));
    }
    private static Optional<Roles> roles(Value raw) {
        if(!(raw instanceof Obj value) || !flag(value,"available") || !textEquals(value,"source","finalized_selected_cb_context"))return Optional.empty();
        if(!(value.get("primary_attacker_character_id") instanceof IntegerValue attacker)
                || !(value.get("primary_defender_character_id") instanceof IntegerValue defender)
                || attacker.value().signum()<=0 || defender.value().signum()<=0
                || attacker.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))>0
                || defender.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))>0)return Optional.empty();
        return Optional.of(new Roles(attacker.value().intValueExact(),defender.value().intValueExact()));
    }
    public static Obj json(Record record) {
        Origin origin=record.origin();var out=new LinkedHashMap<String,Value>();
        out.put("schema",new Text(SCHEMA));out.put("request_id",new Text(origin.requestId()));
        out.put("declaration",DriverJson.object(StrictJson.canonical(DeclarationContract.encodeChoice(origin.declaration())),MAX_BYTES));
        out.put("before_war_ids",new Arr(origin.beforeWarIds().stream().<Value>map(id->number(id)).toList()));
        out.put("final_cb_roles",origin.finalRoles().<Value>map(value->new Obj(Map.of(
                "primary_attacker_character_id",number(value.primaryAttacker()),"primary_defender_character_id",number(value.primaryDefender()),
                "source",new Text("finalized_selected_cb_context")))).orElse(Nil.INSTANCE));
        Owner owner=origin.owner();out.put("owner",new Obj(Map.of("actor_character_id",number(owner.actorCharacterId()),
                "episode_run_id",owner.episodeRunId(),"bridge_pid",number(owner.bridgePid()),"hello_pid",number(owner.helloPid()),
                "connection_generation",new IntegerValue(owner.connectionGeneration()))));
        out.put("submitted_snapshot_id",new Text(origin.submittedSnapshotId()));out.put("submitted_revision",new IntegerValue(origin.submittedRevision()));
        out.put("submitted_native_revision",new IntegerValue(origin.submittedNativeRevision()));out.put("submitted_date_raw",new IntegerValue(origin.submittedDateRaw()));
        out.put("status",new Text(record.status().wire()));out.put("native_response",new Text(record.nativeResponse().name().toLowerCase(java.util.Locale.ROOT)));
        out.put("in_flight",new Bool(record.inFlight()));out.put("request_retried",new Bool(false));
        out.put("war_id",record.warId().isPresent()?number(record.warId().getAsInt()):Nil.INSTANCE);
        out.put("postcondition_verified",new Bool(record.postconditionVerified()));out.put("casus_belli_identity_observed",new Bool(false));
        out.put("postcondition_scope",new Text(SCOPE));out.put("reason",new Text(record.reason().wire()));
        record.observed().ifPresent(value->{out.put("observed_snapshot_id",new Text(value.snapshotId()));out.put("observed_native_revision",new IntegerValue(value.nativeRevision()));});
        return new Obj(out);
    }
    public static byte[] encode(Record value) {
        byte[] bytes=DriverJson.encode(json(Objects.requireNonNull(value)));StrictJson.require(bytes.length<=MAX_BYTES,"bounded declaration continuity record required");return bytes;
    }
    public static Record decode(byte[] raw) {
        Obj row=DriverJson.object(raw,MAX_BYTES);
        var fields=new java.util.HashSet<>(Set.of("schema","request_id","declaration","before_war_ids","final_cb_roles","owner",
                "submitted_snapshot_id","submitted_revision","submitted_native_revision","submitted_date_raw","status","native_response",
                "in_flight","request_retried","war_id","postcondition_verified","casus_belli_identity_observed","postcondition_scope","reason"));
        boolean observed=row.members().containsKey("observed_snapshot_id")||row.members().containsKey("observed_native_revision");
        if(observed){fields.add("observed_snapshot_id");fields.add("observed_native_revision");}
        StrictJson.require(row.members().keySet().equals(fields) && text(row,"schema").equals(SCHEMA)
                && text(row,"postcondition_scope").equals(SCOPE) && !bool(row,"request_retried") && !bool(row,"casus_belli_identity_observed"),
                "strict original declaration continuity fields differ");
        var choices=DeclarationContract.normalize(OpportunityJson.toNode(new Arr(List.of(get(row,"declaration")))));
        var ids=OpportunityJson.array(get(row,"before_war_ids"),"original before-war ids").stream().map(value->{
            BigInteger id=OpportunityJson.integer(value,"before-war id");StrictJson.require(id.signum()>=0&&id.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"complete before-war ID required");return id.intValueExact();
        }).toList();
        Obj source=object(get(row,"owner"),"continuity owner");
        StrictJson.require(source.members().keySet().equals(Set.of("actor_character_id","episode_run_id","bridge_pid","hello_pid","connection_generation")),"closed declaration owner required");
        Owner owner=new Owner(i32(source,"actor_character_id",1),get(source,"episode_run_id"),i32(source,"bridge_pid",1),i32(source,"hello_pid",1),integer(source,"connection_generation"));
        Optional<Roles> roles;
        if(get(row,"final_cb_roles")==Nil.INSTANCE)roles=Optional.empty();
        else {
            Obj r=object(get(row,"final_cb_roles"),"retained final roles");
            StrictJson.require(r.members().keySet().equals(Set.of("primary_attacker_character_id","primary_defender_character_id","source"))
                    && text(r,"source").equals("finalized_selected_cb_context"),"strict retained declaration roles required");
            roles=Optional.of(new Roles(i32(r,"primary_attacker_character_id",1),i32(r,"primary_defender_character_id",1)));
        }
        var origin=new Origin(text(row,"request_id"),choices.getFirst(),ids,roles,owner,text(row,"submitted_snapshot_id"),
                integer(row,"submitted_revision"),integer(row,"submitted_native_revision"),integer(row,"submitted_date_raw"));
        OptionalInt war=get(row,"war_id")==Nil.INSTANCE?OptionalInt.empty():OptionalInt.of(i32(row,"war_id",0));
        var response=switch(text(row,"native_response")){case "accepted"->NativeResponse.ACCEPTED;case "unknown"->NativeResponse.UNKNOWN;case "rejected"->NativeResponse.REJECTED;default->throw new IllegalArgumentException("unknown native declaration response");};
        return new Record(origin,Status.exact(text(row,"status")),response,bool(row,"in_flight"),war,bool(row,"postcondition_verified"),
                observed?Optional.of(new Observed(text(row,"observed_snapshot_id"),integer(row,"observed_native_revision"))):Optional.empty(),Reason.exact(text(row,"reason")));
    }
    private static Value get(Obj row,String name){Value value=row.get(name);StrictJson.require(value!=null,"missing original declaration "+name);return value;}
    private static Value getOr(Obj row,String name,Value fallback){Value value=row.get(name);return value==null?fallback:value;}
    private static Obj object(Value value,String name){return OpportunityJson.object(value,name);}
    private static String text(Obj row,String name){return OpportunityJson.text(get(row,name),name);}
    private static BigInteger integer(Obj row,String name){return OpportunityJson.integer(get(row,name),name);}
    private static boolean bool(Obj row,String name){return OpportunityJson.bool(get(row,name),name);}
    private static boolean flag(Obj row,String name){return row.get(name) instanceof Bool value&&value.value();}
    private static boolean textEquals(Obj row,String name,String expected){return row.get(name) instanceof Text value&&value.value().equals(expected);}
    private static boolean integerEquals(Value raw,int expected){return raw instanceof IntegerValue value&&value.value().equals(BigInteger.valueOf(expected));}
    private static IntegerValue number(int value){return new IntegerValue(BigInteger.valueOf(value));}
    private static int i32(Obj row,String name,int minimum){BigInteger value=integer(row,name);StrictJson.require(value.compareTo(BigInteger.valueOf(minimum))>=0&&value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"complete declaration "+name+" required");return value.intValueExact();}
}

