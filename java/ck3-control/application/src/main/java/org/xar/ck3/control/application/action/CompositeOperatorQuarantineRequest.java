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
        long expectedHeadSequence,String expectedHeadDigest,List<Child> children,Instant issuedAt,Instant observationDeadline) {
    public static final String SCHEMA="xar.java.composite-operator-quarantine-request/v1";
    public static final String SCOPE="optional-sway-episode";
    public record Child(int ordinal,String actionId,String bodySha256) {
        public Child {require(ordinal>=1&&ordinal<=64,"bounded retired child ordinal");StrictJson.text(actionId);digest(bodySha256);}
    }
    public CompositeOperatorQuarantineRequest {
        Objects.requireNonNull(authorizedBy);StrictJson.text(machineId);Objects.requireNonNull(game);StrictJson.text(episodeRunId);
        StrictJson.text(parentActionId);digest(parentBodySha256);Objects.requireNonNull(originalReceipt);StrictJson.safe(expectedHeadSequence,1);digest(expectedHeadDigest);
        children=List.copyOf(children);require(!children.isEmpty()&&children.size()<=64,"complete original child vector required");
        for(int i=0;i<children.size();i++)require(children.get(i).ordinal()==i+1,"original child ordinal order differs");
        Objects.requireNonNull(issuedAt);Objects.requireNonNull(observationDeadline);
        require(observationDeadline.isAfter(issuedAt)&&java.time.Duration.between(issuedAt,observationDeadline).compareTo(java.time.Duration.ofHours(1))<=0,"fresh bounded operator decision window required; original action deadline is not modified");
    }
    public static CompositeOperatorQuarantineRequest decode(byte[] raw) {
        var row=StrictJson.object(StrictJson.parse(raw,65536),Set.of("schema","authorized_by","machine_id","game","episode_run_id","parent_action_id","parent_body_sha256","original_receipt_ref","expected_head_sequence","expected_head_digest","children","scope","issued_at_utc","observation_deadline_utc"));
        require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&SCOPE.equals(StrictJson.text(row.get("scope"))),"explicit operator quarantine version/scope required");
        JsonNode list=row.get("children");require(list.isArray()&&!list.isEmpty()&&list.size()<=64,"complete bounded original child vector required");
        var children=new java.util.ArrayList<Child>();for(JsonNode value:list){StrictJson.object(value,Set.of("ordinal","action_id","body_sha256"));children.add(new Child(Math.toIntExact(StrictJson.integer(value.get("ordinal"),1,64)),StrictJson.text(value.get("action_id")),StrictJson.text(value.get("body_sha256"))));}
        return new CompositeOperatorQuarantineRequest(ExactRef.fromJson(row.get("authorized_by")),StrictJson.text(row.get("machine_id")),GameGeneration.fromJson(row.get("game")),StrictJson.text(row.get("episode_run_id")),StrictJson.text(row.get("parent_action_id")),StrictJson.text(row.get("parent_body_sha256")),ExactRef.fromJson(row.get("original_receipt_ref")),StrictJson.integer(row.get("expected_head_sequence"),1,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("expected_head_digest")),children,Instant.parse(StrictJson.text(row.get("issued_at_utc"))),Instant.parse(StrictJson.text(row.get("observation_deadline_utc"))));
    }
    public void requireParent(ActionReceipt original) {
        require(original.state() instanceof ActionState.CompositeUnknown,"operator request requires the exact original CompositeUnknown");
        var command=original.command();var execution=((ActionState.CompositeUnknown)original.state()).execution();
        require(command.actionId().equals(parentActionId)&&original.bodySha256().equals(parentBodySha256)&&command.origin().machineId().equals(machineId)
                &&command.origin().game().equals(game)&&command.before().frame().episodeRunId().equals(episodeRunId),"operator request changed original Game/episode/parent/body");
        require(children.size()==execution.children().size(),"operator request cannot discard original reservations");
        for(int i=0;i<children.size();i++){var expected=children.get(i);var actual=execution.children().get(i);require(expected.actionId().equals(actual.actionId())&&expected.bodySha256().equals(actual.bodySha256()),"operator request changed original child vector");}
    }
    private static void digest(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"exact SHA256 required");}
}
