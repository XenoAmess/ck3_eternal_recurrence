package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreview12003;
import org.xar.ck3.control.wave2.prisoners.negotiatedpreview.NegotiatedPreviewCodec;

/** The original public pending-only result. This codec cannot grant a material effect or an action retry. */
public final class PrisonerPublicPendingCodec12004 {
    public record Ransom(long payer,PrisonerVanillaResearch.Option option,long quotedGoldRaw){public Ransom{validId(payer);Objects.requireNonNull(option);StrictJson.require(quotedGoldRaw>0,"positive native quote required");}}
    public record Release(BigInteger sequence,PrisonerOptionIntent options,RawJson costs,RawJson acceptance){public Release{Objects.requireNonNull(options);Objects.requireNonNull(costs);Objects.requireNonNull(acceptance);
        StrictJson.require(sequence.signum()>0&&sequence.compareTo(StrictJson.UINT64_MAX)<=0,"exact native query sequence required");
        ReleasePreviewValues12003.readCosts(StrictJson.parse(costs.bytes()));requireAcceptance(options,acceptance);}}
    public record Pending(PrisonerPlanningPorts.Family family,BigInteger nativeRevision,int dateRaw,long player,long prisoner,
            String requestId,Optional<Ransom> ransom,Optional<Release> release){public Pending{Objects.requireNonNull(family);Objects.requireNonNull(nativeRevision);NativeCharacterId.of(player);validId(prisoner);StrictJson.text(requestId);
        StrictJson.require(nativeRevision.signum()>0&&nativeRevision.compareTo(StrictJson.UINT64_MAX)<=0&&player!=prisoner,"native current identity required");
        Objects.requireNonNull(ransom);Objects.requireNonNull(release);StrictJson.require((family==PrisonerPlanningPorts.Family.RANSOM)==ransom.isPresent()&&ransom.isPresent()!=release.isPresent(),"one exact pending branch required");}}
    private PrisonerPublicPendingCodec12004(){}
    public static RawJson fromAcknowledgement(ActionCommand command,NativeActionPort.AckReceived ack,PrisonerActionBinding12004.SelectedRead selected){
        PrisonerActionBinding12004.requireOperation(command.operation());
        StrictJson.require(PrisonerActionBinding12004.isPublic(command)&&PrisonerActionBinding12004.selectedFrameMatches(command,selected.receipt()),"actual public command/original pair required");
        var result=StrictJson.object().put("step",command.operation().value()).put("accepted",true).put("status","submitted_verification_pending");
        var outer=StrictJson.object(StrictJson.parse(ack.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));
        StrictJson.require("command_result".equals(StrictJson.text(outer.get("type")))&&StrictJson.integer(outer.get("protocol_version"),1,1)==1
                &&ack.requestId().equals(StrictJson.text(outer.get("request_id")))&&ack.nativeOk(),"actual native pending ACK envelope required");
        StrictJson.trueValue(outer.get("ok"));StrictJson.require(outer.get("result").equals(result)
                &&ack.originalResultToken().isPresent()&&StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()).equals(result),"native pending ACK is not a material result");
        var args=StrictJson.parse(OpportunityJson.encode(command.arguments()));long target=PrisonerActionBinding12004.id(args.get("prisoner_character_id"));
        StrictJson.require(org.xar.ck3.control.contracts.ExactRef.fromJson(args.get("selected_collection_read")).equals(selected.reference())
                &&selected.receipt().request().source().equals(command.source())&&selected.receipt().request().sessionId().equals(command.sessionId()),"public ACK changed its selected source original");
        Optional<Ransom> ransom=Optional.empty();Optional<Release> release=Optional.empty();var family=command.operation().equals(PrisonerOrdinaryPolicy12004.RELEASE)?PrisonerPlanningPorts.Family.RELEASE:PrisonerPlanningPorts.Family.RANSOM;
        if(family==PrisonerPlanningPorts.Family.RANSOM)ransom=Optional.of(new Ransom(PrisonerActionBinding12004.id(args.get("payer_character_id")),option(StrictJson.text(args.get("selected_option"))),StrictJson.integer(args.get("quoted_gold_raw"),1,Long.MAX_VALUE)));
        else{var row=StrictJson.parse(selected.normalized().bytes()).path("player_prisoner_collection").path("prisoners").get(selected.ordinal());var preview=row.get(selected.intent().options() instanceof PrisonerOptionIntent.Negotiated?"negotiated_release_preview":"unconditional_release_preview");
            release=Optional.of(new Release(StrictJson.integer(args.get("release_query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX),selected.intent().options(),new RawJson(StrictJson.canonical(preview.get("costs"))),new RawJson(StrictJson.canonical(preview.get("acceptance")))));}
        return encode(new Pending(family,command.before().frame().identity().nativeRevision(),command.before().frame().identity().dateRaw().intValueExact(),command.before().frame().identity().player().longValueExact(),target,ack.requestId(),ransom,release));
    }
    public static RawJson encode(Pending value){var row=StrictJson.object().put("exact_ck3_build","1.20.0.4").put("exe_sha256",PrisonerVanillaResearch.EXE_SHA256.toUpperCase(java.util.Locale.ROOT))
        .put("schema",value.family()==PrisonerPlanningPorts.Family.RELEASE?"xar.ck3.prisoner-release-private-action.v1":"xar.ck3.prisoner-ransom-private-action.v1")
        .put("status","submitted_verification_pending").put("material_result",false).put("advertised",false).put("pre_native_revision",value.nativeRevision()).put("pre_date_raw",value.dateRaw())
        .put("player_character_id",value.player()).put("prisoner_character_id",value.prisoner()).put("request_id",value.requestId());
        if(value.ransom().isPresent()){var terms=value.ransom().orElseThrow();row.put("payer_character_id",terms.payer()).put("selected_option",terms.option().name().toLowerCase(java.util.Locale.ROOT)).put("quoted_gold_raw",terms.quotedGoldRaw());}
        else{var terms=value.release().orElseThrow();row.put("release_query_sequence",terms.sequence());var keys=row.putArray("selected_option_keys");int mask=0;
            if(terms.options() instanceof PrisonerOptionIntent.Negotiated selected){selected.options().forEach(option->keys.add(option.key()));mask=selected.mask();}
            row.put("release_option_mask_bits",mask);row.set("costs",StrictJson.parse(terms.costs().bytes()));row.set("acceptance",StrictJson.parse(terms.acceptance().bytes()));}
        return new RawJson(StrictJson.canonical(row));}
    public static Pending decode(RawJson original){var row=StrictJson.parse(original.bytes(),1_048_576);boolean release="xar.ck3.prisoner-release-private-action.v1".equals(StrictJson.text(row.get("schema")));
        var fields=new HashSet<>(Set.of("exact_ck3_build","exe_sha256","schema","status","material_result","advertised","pre_native_revision","pre_date_raw","player_character_id","prisoner_character_id","request_id"));
        fields.addAll(release?Set.of("release_query_sequence","selected_option_keys","release_option_mask_bits","costs","acceptance"):Set.of("payer_character_id","selected_option","quoted_gold_raw"));StrictJson.object(row,fields);
        StrictJson.require((release||"xar.ck3.prisoner-ransom-private-action.v1".equals(StrictJson.text(row.get("schema"))))&&"1.20.0.4".equals(StrictJson.text(row.get("exact_ck3_build")))
                &&PrisonerVanillaResearch.EXE_SHA256.toUpperCase(java.util.Locale.ROOT).equals(StrictJson.text(row.get("exe_sha256")))&&"submitted_verification_pending".equals(StrictJson.text(row.get("status"))),"exact original pending schema/source required");
        StrictJson.require(row.get("material_result").isBoolean()&&!row.get("material_result").booleanValue()&&row.get("advertised").isBoolean()&&!row.get("advertised").booleanValue(),"ACK grants no material or advertised result");
        Optional<Ransom> ransom=Optional.empty();Optional<Release> terms=Optional.empty();if(!release)ransom=Optional.of(new Ransom(PrisonerActionBinding12004.id(row.get("payer_character_id")),option(StrictJson.text(row.get("selected_option"))),StrictJson.integer(row.get("quoted_gold_raw"),1,Long.MAX_VALUE)));
        else{var keys=row.get("selected_option_keys");StrictJson.require(keys.isArray(),"original option key array required");PrisonerOptionIntent intent=new PrisonerOptionIntent.Unconditional();
            if(!keys.isEmpty()){var request=StrictJson.object();request.set("release_option_keys",keys);intent=PrisonerOptionIntent.decode(request).options();}
            int mask=intent instanceof PrisonerOptionIntent.Negotiated negotiated?negotiated.mask():0;StrictJson.integer(row.get("release_option_mask_bits"),mask,mask);
            terms=Optional.of(new Release(StrictJson.integer(row.get("release_query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX),intent,new RawJson(StrictJson.canonical(row.get("costs"))),new RawJson(StrictJson.canonical(row.get("acceptance")))));}
        return new Pending(release?PrisonerPlanningPorts.Family.RELEASE:PrisonerPlanningPorts.Family.RANSOM,StrictJson.integer(row.get("pre_native_revision"),BigInteger.ONE,StrictJson.UINT64_MAX),(int)StrictJson.integer(row.get("pre_date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE),NativeCharacterId.fromJson(row.get("player_character_id")).value(),PrisonerActionBinding12004.id(row.get("prisoner_character_id")),StrictJson.text(row.get("request_id")),ransom,terms);
    }
    private static void validId(long value){StrictJson.require(value>0&&value<0xffff_ffffL,"valid full character ID required");}
    private static void requireAcceptance(PrisonerOptionIntent options,RawJson original){
        var node=StrictJson.parse(original.bytes());StrictJson.require(node.isObject(),"actual acceptance object required");
        NegotiatedPreview12003.Acceptance typed=switch(StrictJson.text(node.get("kind"))){
            case "auto_accept"->new NegotiatedPreview12003.AutoAccept();
            case "native_answer"->new NegotiatedPreview12003.NativeAnswer(StrictJson.integer(node.get("recipient_acceptance_score_raw"),Long.MIN_VALUE,Long.MAX_VALUE),
                    NegotiatedPreview12003.AnswerStatus.fromRaw((int)StrictJson.integer(node.get("recipient_answer_status_raw"),0,2)));
            default->throw new IllegalArgumentException("accepted queried release answer required");};
        StrictJson.require(node.equals(NegotiatedPreviewCodec.writeAcceptance(typed))
                &&(!(options instanceof PrisonerOptionIntent.Unconditional)||typed instanceof NegotiatedPreview12003.AutoAccept)
                &&(!(typed instanceof NegotiatedPreview12003.NativeAnswer answer)||answer.wouldAcceptNow()),
                "pending acceptance differs from the sole native answer codec or original accepted terms");
    }
    private static PrisonerVanillaResearch.Option option(String value){return switch(value){case "gold"->PrisonerVanillaResearch.Option.GOLD;case "current_gold"->PrisonerVanillaResearch.Option.CURRENT_GOLD;default->throw new IllegalArgumentException("native gold option required");};}
}
