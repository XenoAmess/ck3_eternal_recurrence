package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageResults.*;

/** Complete native alliance result and original private-wrapper normalization.
 * A possible alliance, one-sided answer or constructor does not establish an actual alliance. */
public final class FamilyMarriageAlliance {
    private FamilyMarriageAlliance() { }
    public enum AllianceStatus {ALLIED,NOT_ALLIED,UNKNOWN}
    /** Same captured actual material pair. Live custody is independently checked by FamilyDomainReadBinding.Authority. */
    public record Binding(Route route,Build build,String snapshotId,BigInteger publicRevision,BigInteger nativeRevision,
                          BigInteger dateRaw,BigInteger actor,BigInteger recipient,BigInteger subject,
                          BigInteger candidate,Relationship relationship) {
        public Binding {
            for(Object required:new Object[]{route,build,snapshotId,publicRevision,nativeRevision,dateRaw,actor,recipient,subject,candidate,relationship})Objects.requireNonNull(required);
            need(!snapshotId.isBlank(),"alliance requires actual selected snapshot identity");range(publicRevision,BigInteger.ZERO,U64);range(nativeRevision,BigInteger.ONE,U64);
            range(dateRaw,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE));
            for(BigInteger id:new BigInteger[]{actor,recipient,subject,candidate})range(id,BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));
            need(!subject.equals(candidate),"alliance requires distinct original marriage subjects");
            if(route==Route.FAMILY)need(!actor.equals(recipient),"first-heir alliance requires distinct original player and recipient");
        }
    }
    public record Observation(Binding binding,AllianceStatus status,Boolean playedHasRecipient,Boolean recipientHasPlayed) {
        public Observation {
            Objects.requireNonNull(binding);Objects.requireNonNull(status);
            boolean valid=switch(status){
                case ALLIED->Boolean.TRUE.equals(playedHasRecipient)&&Boolean.TRUE.equals(recipientHasPlayed);
                case NOT_ALLIED->Boolean.FALSE.equals(playedHasRecipient)&&Boolean.FALSE.equals(recipientHasPlayed);
                case UNKNOWN->playedHasRecipient==null&&recipientHasPlayed==null||playedHasRecipient!=null&&recipientHasPlayed!=null&&!playedHasRecipient.equals(recipientHasPlayed);
            };
            need(valid,"actual alliance status contradicts the two observed native directions");
        }
    }
    public static String step(Route route){return switch(route){
        case FAMILY->"query-observed-first-heir-marriage-alliance-result-v1-private";
        case MATRILINEAL->"query-player-child-matrilineal-alliance-result-v1-private";
        case DEFAULT->"query-player-child-default-alliance-result-v1-private";};}
    public static String schema(Route route){return switch(route){
        case FAMILY->"xar.ck3.first-heir-marriage-alliance-result.v1";
        case MATRILINEAL->"xar.ck3.player-child-matrilineal-alliance-result.v1";
        case DEFAULT->"xar.ck3.player-child-default-alliance-result.v1";};}
    public static Binding binding(Context context,Resolved resolved){
        Objects.requireNonNull(context);Objects.requireNonNull(resolved);FamilyMarriageResults.verifyResolved(resolved);Pending pending=resolved.pending();
        need(pending.playedCharacterId()!=null&&pending.recipientCharacterId()!=null,"alliance source pending lacks the actual player/recipient tuple");
        need(pending.route()==resolved.route()&&pending.playedCharacterId().equals(context.actor()),"alliance material pair differs from actual played character");
        JsonNode material=OpportunityJson.toNode(resolved.original());eq(material,"heir_character_id",pending.subjectCharacterId());eq(material,"candidate_character_id",pending.candidateCharacterId());
        if(resolved.route()!=Route.FAMILY)need(pending.matrilinealOptionSelected()==(resolved.route()==Route.MATRILINEAL),"alliance original selected route/lineality differs");
        return new Binding(resolved.route(),context.build(),context.before().frame().snapshotId(),context.before().frame().revision(),context.revision(),context.date(),
                pending.playedCharacterId(),pending.recipientCharacterId(),pending.subjectCharacterId(),pending.candidateCharacterId(),resolved.relationship());
    }
    public static Observation decodeNative(RawJson original,Binding binding){
        ObjectNode row=parse(original);closed(row,"step","accepted","private_build","advertised","read_only","native_revision",
                "played_character_id","recipient_character_id","heir_character_id","candidate_character_id","relationship_status",
                "alliance_status","played_has_recipient_alliance","recipient_has_played_alliance");
        eq(row,"step",step(binding.route()));yes(row,"accepted");yes(row,"private_build");no(row,"advertised");yes(row,"read_only");
        eq(row,"native_revision",binding.nativeRevision());eq(row,"played_character_id",binding.actor());eq(row,"recipient_character_id",binding.recipient());
        eq(row,"heir_character_id",binding.subject());eq(row,"candidate_character_id",binding.candidate());
        eq(row,"relationship_status",wire(binding.relationship()));
        String status=text(row,"alliance_status");need(status.equals("allied")||status.equals("not_allied")||status.equals("unknown"),"actual alliance status token differs");
        return new Observation(binding,AllianceStatus.valueOf(status.toUpperCase(Locale.ROOT)),nullableBool(row,"played_has_recipient_alliance"),nullableBool(row,"recipient_has_played_alliance"));
    }
    public static RawJson encodeNative(Observation value){
        Binding b=value.binding();ObjectNode out=F.objectNode().put("step",step(b.route())).put("accepted",true).put("private_build",true)
                .put("advertised",false).put("read_only",true).put("native_revision",b.nativeRevision()).put("played_character_id",b.actor())
                .put("recipient_character_id",b.recipient()).put("heir_character_id",b.subject()).put("candidate_character_id",b.candidate())
                .put("relationship_status",wire(b.relationship())).put("alliance_status",wire(value.status()));
        nullable(out,"played_has_recipient_alliance",value.playedHasRecipient());nullable(out,"recipient_has_played_alliance",value.recipientHasPlayed());return encode(out);
    }
    /** Original Python wrapper envelope, before Root's selected-query tuple is added. */
    public static Obj normalized(Observation value){
        Binding b=value.binding();ObjectNode out=parse(encodeNative(value));out.put("schema",schema(b.route())).put("schema_version",1).put("exact_ck3_build",b.build().version());
        if(b.build()!=Build.WANDERER6)out.put("exe_sha256",b.build().sha256());return app(out);
    }
    public static Obj project(Observation value){
        ObjectNode out=object(OpportunityJson.toNode(normalized(value)));Binding b=value.binding();
        out.put("queried_snapshot_id",b.snapshotId()).put("queried_revision",b.publicRevision()).put("queried_native_revision",b.nativeRevision());return app(out);
    }
    /** The inverse is strict; queried tuple and private schema do not substitute for source custody. */
    public static Observation decodeNormalized(Obj value,Binding binding,boolean queried){
        ObjectNode out=object(OpportunityJson.toNode(value)).deepCopy();
        eq(out,"schema",schema(binding.route()));eq(out,"schema_version",BigInteger.ONE);eq(out,"exact_ck3_build",binding.build().version());
        out.remove("schema");out.remove("schema_version");out.remove("exact_ck3_build");
        if(binding.build()!=Build.WANDERER6){need(text(out,"exe_sha256").equalsIgnoreCase(binding.build().sha256()),"alliance private exact executable differs");out.remove("exe_sha256");}
        if(queried){eq(out,"queried_snapshot_id",binding.snapshotId());eq(out,"queried_revision",binding.publicRevision());eq(out,"queried_native_revision",binding.nativeRevision());out.remove("queried_snapshot_id");out.remove("queried_revision");out.remove("queried_native_revision");}
        return decodeNative(encode(out),binding);
    }
    private static void nullable(ObjectNode out,String key,Boolean value){if(value==null)out.putNull(key);else out.put(key,value);}
    private static Obj app(ObjectNode value){return DriverJson.object(value.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static String wire(Enum<?> value){return value.name().toLowerCase(Locale.ROOT);}
}
