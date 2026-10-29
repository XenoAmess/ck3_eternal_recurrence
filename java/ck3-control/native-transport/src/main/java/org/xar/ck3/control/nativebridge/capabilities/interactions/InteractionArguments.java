package org.xar.ck3.control.nativebridge.capabilities.interactions;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Canonical application arguments and native wire fields have explicitly different contracts. */
final class InteractionArguments {
    private InteractionArguments() { }
    static ObjectNode body(Context c) {
        ObjectNode n=F.objectNode(),ctx=n.putObject("group_context"); ctx.put("build",c.build().name()).put("connection_generation",c.connectionGeneration());
        ControlFrame f=c.controls(); ObjectNode controls=ctx.putObject("controls");
        controls.put("paused",f.paused()).put("map_ready",f.mapReady()).put("alive",f.alive()).put("speed",f.speed()).put("episode_character_id",f.episodeCharacterId()).put("episode_run_id",f.episodeRunId()).put("active_event",f.activeEvent());
        if(f.localPlayerId()==null) controls.putNull("local_player_id"); else controls.put("local_player_id",f.localPlayerId());
        if(f.betrothedId()==null) controls.putNull("betrothed_id"); else controls.put("betrothed_id",f.betrothedId());
        var spouses=controls.putArray("spouse_ids"); for(Long id:f.spouseIds()) spouses.add(id);
        if(f.pending()==null) controls.putNull("pending"); else controls.putObject("pending").put("instance_id",f.pending().instance().value()).put("sender_id",f.pending().sender().value()).put("notification",f.pending().autoAcceptNotification());
        return n;
    }
    static OpportunityJson.Obj app(ObjectNode n) {
        OpportunityJson.Value value=DriverJson.object(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
        need(value instanceof OpportunityJson.Obj,"application arguments must be a strict object"); return (OpportunityJson.Obj)value;
    }
    static ObjectNode parseApp(OpportunityJson.Obj value) { return parse(new RawJson(OpportunityJson.encode(value))); }
    static Context context(PlanningReadRequest r) {
        var origin=r.origin();
        if(origin instanceof org.xar.ck3.control.application.action.CommandOrigin.Gameplay)
            return context(parseApp(r.arguments()),r.before(),r.source(),r.sessionId(),r.deadline());
        if(origin instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation)
            return context(parseApp(r.arguments()),r.reconciliationBefore(),r.source(),r.sessionId(),r.deadline());
        throw new IllegalArgumentException("interaction context requires an explicit gameplay or reconciliation origin");
    }
    static Context context(ActionCommand c) { return context(parseApp(c.arguments()),c.before(),c.source(),c.sessionId(),c.deadline()); }
    private static Context context(JsonNode body,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,org.xar.ck3.control.g2.common.G2Source source,String session,java.time.Instant deadline) {
        JsonNode ctx=field(body,"group_context"); closed(ctx,"build","connection_generation","controls");
        JsonNode f=field(ctx,"controls"); closed(f,"paused","map_ready","alive","speed","episode_character_id","episode_run_id","active_event","local_player_id","betrothed_id","spouse_ids","pending");
        PendingSummary pending=null; if(!field(f,"pending").isNull()) {
            JsonNode p=field(f,"pending"); closed(p,"instance_id","sender_id","notification"); pending=new PendingSummary(new PendingId(integer(p,"instance_id",Integer.MIN_VALUE,Integer.MAX_VALUE)),NativeCharacterId.of(number(p,"sender_id",BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE))),bool(p,"notification"));
        }
        ControlFrame frame=new ControlFrame(bool(f,"paused"),bool(f,"map_ready"),bool(f,"alive"),integer(f,"speed",0,5),nullablePlayer(f,"local_player_id"),contextCharacterId(f,"episode_character_id"),text(f,"episode_run_id"),bool(f,"active_event"),pending,nullableContextCharacterId(f,"betrothed_id"),contextCharacterIds(f,"spouse_ids"));
        return new Context(before,source,session,positive64(ctx,"connection_generation"),enumeration(ctx,"build",Build.class),deadline,frame);
    }
    static long contextCharacterId(JsonNode n,String key) { return NativeCharacterId.fromJson(field(n,key)).value(); }
    static Long nullableContextCharacterId(JsonNode n,String key) { return field(n,key).isNull()?null:contextCharacterId(n,key); }
    static List<Long> contextCharacterIds(JsonNode n,String key) { return list(n,key,65536,value->(long)NativeCharacterId.fromJson(value).value()); }
    static void ordinary(ObjectNode n,OrdinaryRequest r) {
        n.put("interaction_key",r.interaction().value()).put("recipient_id",r.recipient().value());
        if(r.education().isEmpty()) n.putNull("education"); else {
            EducationIntent e=r.education().orElseThrow(); ObjectNode a=n.putObject("education");
            if(e.child().isPresent()) a.put("child_full_id",e.child().orElseThrow().value()); else a.putNull("child_full_id");
            if(e.guardian().isPresent()) a.put("guardian_full_id",e.guardian().orElseThrow().value()); else a.putNull("guardian_full_id");
            if(e.options().isPresent()) { var options=a.putArray("option_keys"); for(InteractionKey k:e.options().orElseThrow()) options.add(k.value()); } else a.putNull("option_keys");
        }
    }
    static OrdinaryRequest ordinary(JsonNode n) {
        Optional<EducationIntent> education=Optional.empty();
        if(!field(n,"education").isNull()) {
            JsonNode e=field(n,"education"); closed(e,"child_full_id","guardian_full_id","option_keys");
            Long child=nullableId(e,"child_full_id"),guardian=nullableId(e,"guardian_full_id");
            Optional<List<InteractionKey>> options=field(e,"option_keys").isNull()?Optional.empty():Optional.of(list(e,"option_keys",4096,v->{ need(v.isTextual(),"education key string required"); return new InteractionKey(v.textValue()); }));
            education=Optional.of(new EducationIntent(Optional.ofNullable(child).map(CharacterId::new),Optional.ofNullable(guardian).map(CharacterId::new),options));
        }
        return new OrdinaryRequest(new InteractionKey(text(n,"interaction_key")),new CharacterId(id(n,"recipient_id")),education);
    }
    static void grant(ObjectNode n,GrantRequest r) {
        n.put("grant_operation",r.operation().name()).put("recipient_id",r.recipient().value()); var targets=n.putArray("targets"); for(FullId id:r.targets()) targets.add(id.value());
        var selected=n.putArray("expected_selected"); for(FullId id:r.expectedSelected()) selected.add(id.value());
        if(r.title().isPresent()) n.put("title",r.title().orElseThrow().value()); else n.putNull("title"); if(r.desiredSelected().isPresent()) n.put("desired_selected",r.desiredSelected().orElseThrow()); else n.putNull("desired_selected");
    }
    static GrantRequest grant(JsonNode n) {
        Long title=nullableId(n,"title"); Boolean desired=nullableBool(n,"desired_selected");
        return new GrantRequest(enumeration(n,"grant_operation",GrantOperation.class),new CharacterId(id(n,"recipient_id")),ids(n,"targets",64).stream().map(FullId::new).toList(),ids(n,"expected_selected",64).stream().map(FullId::new).toList(),Optional.ofNullable(title).map(FullId::new),Optional.ofNullable(desired));
    }
    static void control(ObjectNode n,ControlRequest r) {
        n.put("control_action",r.action().name()); if(r.contextSignature().isPresent()) n.put("control_signature",r.contextSignature().orElseThrow().value()); else n.putNull("control_signature");
        if(r.candidate().isPresent()) n.put("candidate_id",r.candidate().orElseThrow().value()); else n.putNull("candidate_id");
        n.put("creation_filetime_decimal",r.source().creationFiletime().decimal()).put("source_inventory_sha256",r.source().inventorySha256().value()); ref(n.putObject("verified_inventory"),r.source().verifiedInventory());
    }
    static ControlRequest control(JsonNode n) {
        Long candidate=nullableId(n,"candidate_id"); String signature=nullableText(n,"control_signature");
        return new ControlRequest(enumeration(n,"control_action",ControlAction.class),Optional.ofNullable(signature).map(Signature::new),Optional.ofNullable(candidate).map(CharacterId::new),
            new ControlSource(new CreationFiletime(text(n,"creation_filetime_decimal")),new Signature(text(n,"source_inventory_sha256")),ref(field(n,"verified_inventory"))));
    }
    static void appointment(ObjectNode n,AppointmentRequest r) {
        n.put("requested_title_id",r.title().map(CharacterId::value).orElse(0L)).put("candidate_offset",r.offset()).put("candidate_limit",r.limit())
            .put("breakdown_character_id",r.breakdown().map(CharacterId::value).orElse(0L)).put("diagnostic_character_id",r.diagnostic().map(CharacterId::value).orElse(0L));
    }
    static AppointmentRequest appointment(JsonNode n) {
        long title=id(n,"requested_title_id"),breakdown=id(n,"breakdown_character_id"),diagnostic=id(n,"diagnostic_character_id");
        return new AppointmentRequest(title==0?Optional.empty():Optional.of(new CharacterId(title)),integer(n,"candidate_offset",0,4096),integer(n,"candidate_limit",1,64),breakdown==0?Optional.empty():Optional.of(new CharacterId(breakdown)),diagnostic==0?Optional.empty():Optional.of(new CharacterId(diagnostic)));
    }
    static RawJson appointmentNative(AppointmentRequest r) { ObjectNode n=F.objectNode().put("window_kind","title_appointment").put("subject_id",0); appointment(n,r); return encode(n); }
    static void ref(ObjectNode n,ExactRef r) { n.put("path",r.path()).put("bytes",r.bytes()).put("sha256",r.sha256()); }
    static ExactRef ref(JsonNode n) { closed(n,"path","bytes","sha256"); return new ExactRef(text(n,"path"),number(n,"bytes",BigInteger.ZERO,I64_MAX).longValueExact(),text(n,"sha256")); }
}
