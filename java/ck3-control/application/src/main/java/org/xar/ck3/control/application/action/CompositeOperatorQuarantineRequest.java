package org.xar.ck3.control.application.action;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicitly installed operator request DATA; parsing this object is not authority. */
public record CompositeOperatorQuarantineRequest(ExactRef authorizedBy,String machineId,GameGeneration game,
        String episodeRunId,String parentActionId,String parentBodySha256,ExactRef originalReceipt,
        long expectedHeadSequence,String expectedHeadDigest,List<Child> children,Instant issuedAt,Instant observationDeadline,
        String scope,List<ExactRef> priorRequests) {
    public static final String SCHEMA="xar.java.composite-operator-quarantine-request/v1";
    public static final String SCOPE="optional-sway-episode";
    public static final String LIFE_SCHEMA="xar.java.composite-operator-quarantine-request/v2";
    public static final String LIFE_SCOPE="retained-life-interruption";
    public static final String RESERVED_LIFE_SCHEMA="xar.java.composite-operator-quarantine-request/v3";
    public static final String RESERVED_LIFE_SCOPE="retained-life-reserved-tail-interruption";
    public CompositeOperatorQuarantineRequest(ExactRef authorizedBy,String machineId,GameGeneration game,
            String episodeRunId,String parentActionId,String parentBodySha256,ExactRef originalReceipt,
            long expectedHeadSequence,String expectedHeadDigest,List<Child> children,Instant issuedAt,Instant observationDeadline) {
        this(authorizedBy,machineId,game,episodeRunId,parentActionId,parentBodySha256,originalReceipt,expectedHeadSequence,
                expectedHeadDigest,children,issuedAt,observationDeadline,SCOPE,List.of());
    }
    public boolean lifeInterruption(){return LIFE_SCOPE.equals(scope)||reservedTailInterruption();}
    public boolean reservedTailInterruption(){return RESERVED_LIFE_SCOPE.equals(scope);}
    public record Child(int ordinal,String actionId,String bodySha256) {
        public Child {require(ordinal>=1&&ordinal<=64,"bounded retired child ordinal");StrictJson.text(actionId);digest(bodySha256);}
    }
    public CompositeOperatorQuarantineRequest {
        Objects.requireNonNull(authorizedBy);StrictJson.text(machineId);Objects.requireNonNull(game);StrictJson.text(episodeRunId);
        StrictJson.text(parentActionId);digest(parentBodySha256);Objects.requireNonNull(originalReceipt);StrictJson.safe(expectedHeadSequence,1);digest(expectedHeadDigest);
        children=List.copyOf(children);require(!children.isEmpty()&&children.size()<=64,"complete original child vector required");
        for(int i=0;i<children.size();i++)require(children.get(i).ordinal()==i+1,"original child ordinal order differs");
        require(SCOPE.equals(scope)||LIFE_SCOPE.equals(scope)||RESERVED_LIFE_SCOPE.equals(scope),"explicit operator scope required");
        if(RESERVED_LIFE_SCOPE.equals(scope))require(children.size()==6,"reserved Life interruption retains exactly six reservations");
        priorRequests=List.copyOf(priorRequests);require(priorRequests.size()<=16&&new java.util.HashSet<>(priorRequests).size()==priorRequests.size(),"bounded distinct prior operator requests required");
        require(!SCOPE.equals(scope)||priorRequests.isEmpty(),"legacy optional Sway request has no new prior-request authority");
        Objects.requireNonNull(issuedAt);Objects.requireNonNull(observationDeadline);
        require(observationDeadline.isAfter(issuedAt)&&java.time.Duration.between(issuedAt,observationDeadline).compareTo(java.time.Duration.ofHours(1))<=0,"fresh bounded operator decision window required; original action deadline is not modified");
    }
    public static CompositeOperatorQuarantineRequest decode(byte[] raw) {
        var parsed=StrictJson.parse(raw,65536);
        if(RESERVED_LIFE_SCHEMA.equals(StrictJson.text(parsed.get("schema"))))return decodeReservedLife(parsed);
        boolean life=LIFE_SCHEMA.equals(StrictJson.text(parsed.get("schema")));
        var fields=new java.util.HashSet<>(Set.of("schema","authorized_by","machine_id","game","episode_run_id","parent_action_id","parent_body_sha256","original_receipt_ref","expected_head_sequence","expected_head_digest","children","scope","issued_at_utc","observation_deadline_utc"));
        if(life)fields.add("prior_requests");var row=StrictJson.object(parsed,fields);
        require((life?LIFE_SCOPE:SCOPE).equals(StrictJson.text(row.get("scope")))&&(life||SCHEMA.equals(StrictJson.text(row.get("schema")))),"explicit operator quarantine version/scope required");
        var prior=new java.util.ArrayList<ExactRef>();if(life){var refs=row.get("prior_requests");require(refs!=null&&refs.isArray()&&refs.size()<=16,"bounded explicit prior requests required");for(var ref:refs)prior.add(ExactRef.fromJson(ref));}
        JsonNode list=row.get("children");require(list.isArray()&&!list.isEmpty()&&list.size()<=64,"complete bounded original child vector required");
        var children=new java.util.ArrayList<Child>();for(JsonNode value:list){StrictJson.object(value,Set.of("ordinal","action_id","body_sha256"));children.add(new Child(Math.toIntExact(StrictJson.integer(value.get("ordinal"),1,64)),StrictJson.text(value.get("action_id")),StrictJson.text(value.get("body_sha256"))));}
        return new CompositeOperatorQuarantineRequest(ExactRef.fromJson(row.get("authorized_by")),StrictJson.text(row.get("machine_id")),GameGeneration.fromJson(row.get("game")),StrictJson.text(row.get("episode_run_id")),StrictJson.text(row.get("parent_action_id")),StrictJson.text(row.get("parent_body_sha256")),ExactRef.fromJson(row.get("original_receipt_ref")),StrictJson.integer(row.get("expected_head_sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("expected_head_digest")),children,Instant.parse(StrictJson.text(row.get("issued_at_utc"))),Instant.parse(StrictJson.text(row.get("observation_deadline_utc"))),life?LIFE_SCOPE:SCOPE,prior);
    }
    private static CompositeOperatorQuarantineRequest decodeReservedLife(JsonNode parsed) {
        var row=StrictJson.object(parsed,Set.of("schema","authorized_by","machine_id","game","episode_run_id","parent_action_id","parent_body_sha256","original_receipt_ref","expected_head_sequence","expected_head_digest","children","scope","issued_at_utc","observation_deadline_utc","prior_requests"));
        require(RESERVED_LIFE_SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&RESERVED_LIFE_SCOPE.equals(StrictJson.text(row.get("scope"))),"exact reserved Life operator version/scope required");
        var refs=row.get("prior_requests");require(refs!=null&&refs.isArray()&&refs.size()<=16,"bounded explicit prior requests required");
        var prior=new java.util.ArrayList<ExactRef>();for(var ref:refs)prior.add(ExactRef.fromJson(ref));
        JsonNode list=row.get("children");require(list!=null&&list.isArray()&&list.size()==6,"reserved Life operator request requires exactly six reservations");
        var children=new java.util.ArrayList<Child>();for(JsonNode value:list){StrictJson.object(value,Set.of("ordinal","action_id","body_sha256"));children.add(new Child(Math.toIntExact(StrictJson.integer(value.get("ordinal"),1,64)),StrictJson.text(value.get("action_id")),StrictJson.text(value.get("body_sha256"))));}
        return new CompositeOperatorQuarantineRequest(ExactRef.fromJson(row.get("authorized_by")),StrictJson.text(row.get("machine_id")),GameGeneration.fromJson(row.get("game")),StrictJson.text(row.get("episode_run_id")),StrictJson.text(row.get("parent_action_id")),StrictJson.text(row.get("parent_body_sha256")),ExactRef.fromJson(row.get("original_receipt_ref")),StrictJson.integer(row.get("expected_head_sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("expected_head_digest")),children,Instant.parse(StrictJson.text(row.get("issued_at_utc"))),Instant.parse(StrictJson.text(row.get("observation_deadline_utc"))),RESERVED_LIFE_SCOPE,prior);
    }
    public void requireParent(ActionReceipt original) {
        require(original.state() instanceof ActionState.CompositeUnknown,"operator request requires the exact original CompositeUnknown");
        var command=original.command();var execution=((ActionState.CompositeUnknown)original.state()).execution();
        if(reservedTailInterruption()) {
            var unknown=(ActionState.CompositeUnknown)original.state();
            require(org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                    &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER.equals(execution.handlerId())
                    &&unknown.reason().startsWith(org.xar.ck3.control.application.advance.PreparedCleanupSuccessorEvidence.CURSOR_PREFIX)
                    &&execution.children().size()==6&&children.size()==6&&unknown.evidence().size()>=3,
                    "reserved Life interruption requires its exact six-reservation prepared-successor UNKNOWN prefix");
        }
        if(lifeInterruption())require(org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                &&org.xar.ck3.control.application.advance.LifeAdvanceComposite.HANDLER.equals(execution.handlerId()),"Life interruption retires only its exact original Life parent");
        require(command.actionId().equals(parentActionId)&&original.bodySha256().equals(parentBodySha256)&&command.origin().machineId().equals(machineId)
                &&command.origin().game().equals(game)&&command.before().frame().episodeRunId().equals(episodeRunId),"operator request changed original Game/episode/parent/body");
        require(children.size()==execution.children().size(),"operator request cannot discard original reservations");
        for(int i=0;i<children.size();i++){var expected=children.get(i);var actual=execution.children().get(i);require(expected.actionId().equals(actual.actionId())&&expected.bodySha256().equals(actual.bodySha256()),"operator request changed original child vector");}
    }
    private static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"exact SHA256 required");}
}
