package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Council/Crown value domains. Explicit null means observed empty; a missing body never does. */
public final class GovernanceDomainDocument {
    public static final String COUNCIL_SCHEMA="xar.ck3.private-council-formal/v1";
    public static final String CROWN_SCHEMA="xar.ck3.crown-authority-formal/v1";
    public enum Domain { COUNCIL,CROWN }
    public enum Stage { SUBMISSION_UNRESOLVED,RECEIPT_PENDING }
    /** Copied query/decision/native originals stay opaque only after their owning strict codec has consumed them. */
    public record Pending(Domain domain,Stage stage,String episodeRunId,String requestId,RawJson original) {
        public Pending {Objects.requireNonNull(domain);Objects.requireNonNull(stage);StrictJson.text(episodeRunId);StrictJson.text(requestId);Objects.requireNonNull(original);}
    }
    public record Document(Domain domain,Optional<Pending> pending,Optional<RawJson> latest,Optional<RawJson> retry) {
        public Document {Objects.requireNonNull(domain);Objects.requireNonNull(pending);Objects.requireNonNull(latest);Objects.requireNonNull(retry);
            StrictJson.require(pending.isEmpty()||pending.orElseThrow().domain()==domain,"pending belongs to another original domain");
            pending.ifPresent(value->StrictJson.require(decodePending(domain,value.original()).equals(value),"typed pending metadata differs from the complete original body"));
            StrictJson.require(domain==Domain.CROWN||retry.isEmpty(),"Council has no Crown retry field");latest.ifPresent(GovernanceDomainDocument::object);retry.ifPresent(GovernanceDomainDocument::object);}
    }
    private GovernanceDomainDocument() { }
    public static Document initial(Domain domain) {return new Document(domain,Optional.empty(),Optional.empty(),Optional.empty());}
    public static Document decode(Domain domain,byte[] bytes) {
        ObjectNode row=StrictJson.object(StrictJson.parse(bytes),domain==Domain.COUNCIL?Set.of("schema","pending","applied"):Set.of("pending","resolved","retry"));
        if(domain==Domain.COUNCIL)StrictJson.require(COUNCIL_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact original Council schema required");
        Optional<Pending> pending=nullable(row.get("pending")).map(raw->decodePending(domain,raw));
        return new Document(domain,pending,nullable(row.get(domain==Domain.COUNCIL?"applied":"resolved")),domain==Domain.CROWN?nullable(row.get("retry")):Optional.empty());
    }
    public static Pending decodePending(Domain domain,RawJson raw) {
        ObjectNode row=object(raw);String stage=StrictJson.text(row.get("stage"));
        Stage typed=switch(stage) {case "submission_unresolved"->Stage.SUBMISSION_UNRESOLVED;case "receipt_pending"->Stage.RECEIPT_PENDING;default->throw new IllegalArgumentException("unknown original pending stage");};
        String episode=StrictJson.text(row.get("episode_run_id"));String request=StrictJson.text(row.get(domain==Domain.COUNCIL?"action_request_id":"action_id"));
        integer(row.get("pre_native_revision"),BigInteger.ONE,new BigInteger("18446744073709551615"));integer(row.get("pre_date_raw"),BigInteger.ZERO,BigInteger.valueOf(Integer.MAX_VALUE));
        if(domain==Domain.COUNCIL) {
            StrictJson.object(row,Set.of("stage","episode_run_id","action_request_id","candidate_character_id","source_query","source_decision","pre_native_revision","pre_date_raw","request","action_ack"));
            integer(row.get("candidate_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
            for(String key:List.of("source_query","source_decision"))object(row.get(key));nullable(row.get("action_ack"));
            var wire=StrictJson.object(row.get("request"),Set.of("request_id","position_key","expected_snapshot_id","expected_public_revision","expected_native_revision","expected_date_raw","expected_owner_character_id","candidate_character_id","expected_has_incumbent","expected_incumbent_character_id"));
            StrictJson.require(request.equals(StrictJson.text(wire.get("request_id")))&&Set.of("councillor_steward","councillor_chancellor","councillor_court_chaplain").contains(StrictJson.text(wire.get("position_key")))
                    &&integer(wire.get("candidate_character_id")).equals(integer(row.get("candidate_character_id")))&&integer(wire.get("expected_native_revision")).equals(integer(row.get("pre_native_revision")))
                    &&integer(wire.get("expected_date_raw")).equals(integer(row.get("pre_date_raw"))),"original Council wire request differs from pending identity/frame");
            StrictJson.text(wire.get("expected_snapshot_id"));integer(wire.get("expected_public_revision"),BigInteger.ONE,new BigInteger("18446744073709551615"));integer(wire.get("expected_owner_character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
            var has=wire.get("expected_has_incumbent");StrictJson.require(has.isBoolean(),"incumbent presence must be boolean");var incumbent=integer(wire.get("expected_incumbent_character_id"),BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MAX_VALUE));StrictJson.require(has.booleanValue()?incumbent.signum()>0:incumbent.equals(BigInteger.valueOf(-1)),"original incumbent presence/identity disagree");
            StrictJson.require(typed==Stage.SUBMISSION_UNRESOLVED?row.get("action_ack").isNull():row.get("action_ack").isObject(),"Council stage/helper ACK presence disagree");
        } else {
            Set<String> base=Set.of("stage","episode_run_id","actor_character_id","action_id","law_key","readback","choice","budgets","source_context","pre_native_revision","pre_date_raw","ack");
            var allowed=new java.util.HashSet<>(base);if(row.has("last_receipt"))allowed.add("last_receipt");if(row.has("last_checked_frame"))allowed.add("last_checked_frame");StrictJson.object(row,Set.copyOf(allowed));
            integer(row.get("actor_character_id"),BigInteger.ONE,new BigInteger("4294967294"));StrictJson.text(row.get("law_key"));
            for(String key:List.of("readback","choice","budgets"))object(row.get(key));context(row.get("source_context"));nullable(row.get("ack"));
            StrictJson.require(typed==Stage.SUBMISSION_UNRESOLVED?row.get("ack").isNull():row.get("ack").isObject(),"Crown stage/helper ACK presence disagree");
            if(row.has("last_receipt"))object(row.get("last_receipt"));if(row.has("last_checked_frame"))object(row.get("last_checked_frame"));
        }
        return new Pending(domain,typed,episode,request,raw);
    }
    public static byte[] encode(Document value) {
        var row=StrictJson.object();if(value.domain()==Domain.COUNCIL)row.put("schema",COUNCIL_SCHEMA);
        row.set("pending",value.pending().map(p->StrictJson.parse(p.original().bytes())).orElse(null));
        row.set(value.domain()==Domain.COUNCIL?"applied":"resolved",value.latest().map(raw->StrictJson.parse(raw.bytes())).orElse(null));
        if(value.domain()==Domain.CROWN)row.set("retry",value.retry().map(raw->StrictJson.parse(raw.bytes())).orElse(null));return StrictJson.canonical(row);
    }
    public static Document pending(Document old,RawJson next) {return new Document(old.domain(),Optional.of(decodePending(old.domain(),next)),old.latest(),old.retry());}
    public static Document result(Document old,Optional<RawJson> next) {return new Document(old.domain(),Optional.empty(),next,old.retry());}
    public static Document latest(Document old,RawJson next) {return new Document(old.domain(),old.pending(),Optional.of(next),old.retry());}
    public static RawJson raw(JsonNode value) {object(value);return new RawJson(StrictJson.canonical(value));}
    public static ObjectNode object(RawJson raw) {return object(StrictJson.parse(raw.bytes()));}
    public static ObjectNode object(JsonNode value) {StrictJson.require(value!=null&&value.isObject(),"actual original object required");return (ObjectNode)value;}
    public static Optional<RawJson> nullable(JsonNode value) {StrictJson.require(value!=null,"missing is not explicit null");return value.isNull()?Optional.empty():Optional.of(raw(value));}
    public static BigInteger integer(JsonNode value,BigInteger minimum,BigInteger maximum) {StrictJson.require(value!=null&&value.isIntegralNumber(),"integer token required, bool/float/string rejected");var number=value.bigIntegerValue();StrictJson.require(number.compareTo(minimum)>=0&&number.compareTo(maximum)<=0,"integer outside original domain");return number;}
    public static BigInteger integer(JsonNode value) {return integer(value,BigInteger.valueOf(Long.MIN_VALUE),new BigInteger("18446744073709551615"));}
    public static ObjectNode context(JsonNode value) {var row=StrictJson.object(value,Set.of("bridge_pid","episode_run_id"));integer(row.get("bridge_pid"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));StrictJson.text(row.get("episode_run_id"));return row;}
    /** Existing native job values only. The projection never estimates yield, attribution or an ETA. */
    public static ObjectNode jobProgress(ObjectNode root,String episode,String position,Optional<RawJson> previous) {
        var result=StrictJson.object().put("position_key",position).put("episode_run_id",episode);result.set("source_native_revision",required(root,"snapshot_revision"));result.set("source_date_raw",required(root,"date_raw"));
        Optional<ObjectNode> seat=seat(root,position);if(seat.isEmpty())return result.put("status","unavailable");var row=seat.orElseThrow();
        result.put("status",required(row,"incumbent_character_id").isNull()?"vacant":"available").put("effect_attribution","not_observed");
        for(String key:List.of("incumbent_character_id","task_key","task_type","target","frozen","progress"))result.set(key,required(row,key));
        JsonNode progress=row.get("progress");if(progress.isObject()&&!"infinite".equals(StrictJson.text(progress.get("kind")))) {
            var current=object(progress.get("current"));var maximum=object(progress.get("maximum"));sameScale(current,maximum);
            result.set("remaining_progress",StrictJson.object().put("raw",integer(maximum.get("raw")).subtract(integer(current.get("raw")))).put("scale",integer(current.get("scale"))));
        }
        if(previous.isPresent()) {
            var old=object(previous.orElseThrow());var prior=old.get("independent_position");var comparison=StrictJson.object().put("status","job_changed");
            if(prior!=null&&prior.isObject()&&List.of("incumbent_character_id","task_key","task_type","target").stream().allMatch(key->Objects.equals(row.get(key),prior.get(key)))) {
                comparison.put("status","same_job");var oldProgress=prior.get("progress");
                if(progress.isObject()&&oldProgress!=null&&oldProgress.isObject()&&Objects.equals(progress.get("kind"),oldProgress.get("kind"))
                        &&!"infinite".equals(StrictJson.text(progress.get("kind")))&&Objects.equals(progress.get("maximum"),oldProgress.get("maximum"))) {
                    var current=object(progress.get("current"));var before=object(oldProgress.get("current"));sameScale(current,before);
                    comparison.set("progress_change",StrictJson.object().put("raw",integer(current.get("raw")).subtract(integer(before.get("raw")))).put("scale",integer(current.get("scale"))));
                }
            }
            if(old.has("post_date_raw"))comparison.put("previous_date_raw",integer(old.get("post_date_raw"))).put("elapsed_game_hours",integer(root.get("date_raw")).subtract(integer(old.get("post_date_raw"))));result.set("following_comparison",comparison);
        }
        return result;
    }
    public static Optional<ObjectNode> seat(ObjectNode root,String position) {
        var council=object(required(root,"council"));var rows=required(council,"positions");StrictJson.require(rows.isArray(),"actual Council positions collection required");
        ObjectNode found=null;for(JsonNode raw:rows) {var row=object(raw);if(position.equals(StrictJson.text(row.get("position_key")))) {StrictJson.require(found==null,"duplicate native Council seat");required(row,"incumbent_character_id");found=row;}}return Optional.ofNullable(found);
    }
    public static JsonNode required(ObjectNode row,String field) {JsonNode value=row.get(field);StrictJson.require(value!=null,"missing original field: "+field);return value;}
    private static void sameScale(ObjectNode first,ObjectNode second) {StrictJson.require(integer(first.get("scale")).equals(integer(second.get("scale")))&&integer(first.get("scale")).signum()>0,"native fixed point scales differ");}
}
