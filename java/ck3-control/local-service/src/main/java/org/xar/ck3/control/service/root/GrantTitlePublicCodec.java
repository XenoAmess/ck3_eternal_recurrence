package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.GrantTitleCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Exact original four public inputs and their sole native-decoder-backed publication. */
public final class GrantTitlePublicCodec {
    private GrantTitlePublicCodec() { }
    public sealed interface Request permits Query,Prepare,Select,Send {
        CharacterId recipient(); BigInteger expectedRevision(); GrantRequest nativeRequest();
    }
    public record Query(CharacterId recipient,List<FullId> titles,BigInteger expectedRevision) implements Request {
        public Query { Objects.requireNonNull(recipient);titles=ids(titles,false);revision(expectedRevision); }
        @Override public GrantRequest nativeRequest(){return GrantTitlePublicCodec.nativeRequest(GrantOperation.QUERY,recipient,titles,List.of(),Optional.empty(),Optional.empty());}
    }
    public record Prepare(CharacterId recipient,List<FullId> titles,BigInteger expectedRevision) implements Request {
        public Prepare { Objects.requireNonNull(recipient);titles=ids(titles,false);revision(expectedRevision); }
        @Override public GrantRequest nativeRequest(){return GrantTitlePublicCodec.nativeRequest(GrantOperation.PREPARE,recipient,titles,List.of(),Optional.empty(),Optional.empty());}
    }
    public record Select(CharacterId recipient,FullId title,boolean desiredSelected,List<FullId> expectedSelected,BigInteger expectedRevision) implements Request {
        public Select { Objects.requireNonNull(recipient);Objects.requireNonNull(title);expectedSelected=ids(expectedSelected,false);revision(expectedRevision);
            var targets=new ArrayList<>(expectedSelected);if(!targets.contains(title))targets.add(title);ids(targets,false); }
        @Override public GrantRequest nativeRequest(){var targets=new ArrayList<>(expectedSelected);if(!targets.contains(title))targets.add(title);
            return GrantTitlePublicCodec.nativeRequest(GrantOperation.SELECT,recipient,targets,expectedSelected,Optional.of(title),Optional.of(desiredSelected));}
    }
    public record Send(CharacterId recipient,List<FullId> expectedSelected,BigInteger expectedRevision) implements Request {
        public Send { Objects.requireNonNull(recipient);expectedSelected=ids(expectedSelected,true);revision(expectedRevision); }
        @Override public GrantRequest nativeRequest(){return GrantTitlePublicCodec.nativeRequest(GrantOperation.SEND,recipient,expectedSelected,expectedSelected,Optional.empty(),Optional.empty());}
    }
    private static GrantRequest nativeRequest(GrantOperation operation,CharacterId recipient,List<FullId> targets,List<FullId> selected,Optional<FullId> title,Optional<Boolean> desired) {
        return new GrantRequest(operation,recipient,targets,selected,title,desired);
    }
    public record Reply(RawJson original) { public Reply { Objects.requireNonNull(original); } }
    public static Query query(PublicBindings.Arguments arguments) {
        ObjectNode n=arguments(arguments,Set.of("recipient_id","title_full_ids","expected_revision"));
        return new Query(recipient(n),titles(n,"title_full_ids",false),revision(n));
    }
    public static Prepare prepare(PublicBindings.Arguments arguments) {
        ObjectNode n=arguments(arguments,Set.of("recipient_id","title_full_ids","expected_revision"));
        return new Prepare(recipient(n),titles(n,"title_full_ids",false),revision(n));
    }
    public static Select select(PublicBindings.Arguments arguments) {
        ObjectNode n=arguments(arguments,Set.of("recipient_id","title_full_id","desired_selected","expected_selected_title_full_ids","expected_revision"));
        JsonNode desired=n.get("desired_selected");need(desired!=null&&desired.isBoolean(),"desired_selected must be an actual boolean");
        return new Select(recipient(n),new FullId(id(n.get("title_full_id"),false)),desired.booleanValue(),titles(n,"expected_selected_title_full_ids",false),revision(n));
    }
    public static Send send(PublicBindings.Arguments arguments) {
        ObjectNode n=arguments(arguments,Set.of("recipient_id","expected_selected_title_full_ids","expected_revision"));
        return new Send(recipient(n),titles(n,"expected_selected_title_full_ids",true),revision(n));
    }
    public static Reply observed(RawJson original,Context before,GrantRequest request) {
        GrantTitleCodec.decode(original,before,request);
        ObjectNode row=object(StrictJson.parse(original.bytes(),DriverJson.MAX_NATIVE_BYTES));
        row.put("queried_revision",before.before().frame().revision()).put("episode_run_id",before.controls().episodeRunId())
                .put("uses_mouse",false).put("uses_keyboard",false).put("uses_ocr",false);
        return new Reply(raw(row));
    }
    /** Canonical Root claims replace the original attempt directory; no fabricated .claim.json path is emitted. */
    public static Reply action(ActionReceipt original,ActionPorts.OutcomeArchive archive,Context before,GrantRequest request) {
        var reference=archive.receiptReferenceOf(original);need(original.equals(archive.loadReceipt(reference)),"grant canonical receipt original changed");
        ObjectNode row;
        var material=original.ack().flatMap(NativeActionPort.AckReceived::originalResultToken);
        if(material.isPresent())row=object(StrictJson.parse(observed(material.orElseThrow(),before,request).original().bytes(),DriverJson.MAX_NATIVE_BYTES));
        else row=StrictJson.object().put("operation",request.operation().wire()).put("recipient_character_full_id",request.recipient().value())
                .put("status","grant_state_unknown").put("native_publication_available",false).put("business_full_credit",false)
                .put("queried_revision",before.before().frame().revision()).put("episode_run_id",before.controls().episodeRunId())
                .put("uses_mouse",false).put("uses_keyboard",false).put("uses_ocr",false);
        need(!row.has("action_receipt")&&!row.has("replay_allowed")&&!row.has("java_public_schema"),"native grant body conflicts with canonical Java metadata");
        row.put("java_public_schema","xar.java.grant-title-picker-public/v1").put("replay_allowed",false);
        row.putObject("action_receipt").put("action_id",original.command().actionId()).put("canonical_outcome",original.outcome().name())
                .put("native_ack_received",original.ack().isPresent()).put("settled",original.settled()).put("postcondition_verified",original.state() instanceof ActionState.Settled s && s.settlement() instanceof ActionState.ControlApplied)
                .set("original_receipt",reference.toJson());
        return new Reply(raw(row));
    }
    public static RawJson encode(Reply reply) {
        ObjectNode row=object(StrictJson.parse(reply.original().bytes(),DriverJson.MAX_NATIVE_BYTES));
        for(String field:List.of("native_revision","connection_generation","queried_revision","query_sequence","date_raw"))
            if(row.has(field)&&!row.get(field).isNull())row.put(field,StrictJson.integer(row.get(field),BigInteger.ZERO,StrictJson.UINT64_MAX).toString());
        safe(row);return raw(row);
    }
    public static RawJson encodeRequest(Request request) {
        ObjectNode n=StrictJson.object().put("recipient_id",request.recipient().value()).put("expected_revision",request.expectedRevision().toString());
        switch(request){case Query q->array(n,"title_full_ids",q.titles());case Prepare p->array(n,"title_full_ids",p.titles());
            case Select s->{n.put("title_full_id",s.title().value()).put("desired_selected",s.desiredSelected());array(n,"expected_selected_title_full_ids",s.expectedSelected());}
            case Send s->array(n,"expected_selected_title_full_ids",s.expectedSelected());}
        return raw(n);
    }
    private static void array(ObjectNode row,String key,List<FullId> values){var array=row.putArray(key);values.forEach(v->array.add(v.value()));}
    private static CharacterId recipient(ObjectNode n){return new CharacterId(id(n.get("recipient_id"),true));}
    private static long id(JsonNode n,boolean positive){return StrictJson.integer(n,positive?BigInteger.ONE:BigInteger.ZERO,new BigInteger("4294967294")).longValueExact();}
    private static List<FullId> titles(ObjectNode n,String key,boolean nonempty){JsonNode a=n.get(key);need(a!=null&&a.isArray(),"explicit actual Title ID array required");var values=new ArrayList<FullId>();a.forEach(v->values.add(new FullId(id(v,false))));return ids(values,nonempty);}
    private static List<FullId> ids(List<FullId> values,boolean nonempty){var copy=List.copyOf(values);need(copy.size()<65&&(!nonempty||!copy.isEmpty())&&new HashSet<>(copy).size()==copy.size(),"unique bounded complete Title IDs required");return copy;}
    private static BigInteger revision(ObjectNode n){JsonNode value=n.get("expected_revision");need(value!=null&&value.isTextual()&&value.textValue().matches("[1-9][0-9]{0,19}"),"positive canonical decimal public revision required");var revision=new BigInteger(value.textValue());revision(revision);return revision;}
    private static void revision(BigInteger value){need(value!=null&&value.signum()>0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 public revision required");}
    private static ObjectNode arguments(PublicBindings.Arguments value,Set<String> keys){need(value instanceof PublicBindings.Value,"exact named public grant arguments required");var row=object(StrictJson.parse(((PublicBindings.Value)value).original().bytes(),16384));need(row.size()==keys.size(),"missing/extra public grant fields");row.properties().forEach(e->need(keys.contains(e.getKey()),"unknown public grant argument"));return row;}
    private static ObjectNode object(JsonNode n){need(n instanceof ObjectNode,"actual grant object required");return (ObjectNode)n;}
    private static RawJson raw(JsonNode n){return new RawJson(StrictJson.canonical(n));}
    private static void safe(JsonNode n){if(n.isIntegralNumber())need(n.bigIntegerValue().abs().compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER))<=0,"undeclared unsafe public grant integer");else if(n.isFloatingPointNumber())throw new IllegalArgumentException("floating grant field");else if(n.isContainerNode())n.forEach(GrantTitlePublicCodec::safe);}
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
}
