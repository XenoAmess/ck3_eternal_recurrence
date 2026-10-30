package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJsonTest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;

/** Actual original Root DATA -> strict normalized wire -> actual private candidate/Gift leaf -> persisted choice.
 * Software-only DATA; no Native SendGift, submit port, receipt, pending state or Game is constructed. */
final class RootSignedGiftConsumerTest {
    private static final long[][] PAIRS={{2,3},{2,0},{2,-2},{2,Integer.MIN_VALUE},{2,Integer.MAX_VALUE},
            {0,3},{-2,3},{Integer.MIN_VALUE,3},{Integer.MAX_VALUE,3}};
    private static final Set<String> SCALARS=Set.of("player_character_id","top_liege_character_id","immediate_liege_character_id",
            "first_heir_character_id","owner_character_id","incumbent_character_id","character_id");
    private static final Set<String> VECTORS=Set.of("primary_title_succession_character_ids","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids");
    private static Obj originalRoot,originalCandidateInput;
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static IntegerValue raw(long value){return new IntegerValue(BigInteger.valueOf(Integer.toUnsignedLong(Math.toIntExact(value))));}
    private record Input(Obj root,Obj snapshot,Obj privateResult,BigInteger reserve){}

    @Test void normalizedRootToPrivateCandidateAndPersistedGiftPreserveSignedRoles()throws Exception {
        var checks=new ArrayList<Executable>();
        for(long[] pair:PAIRS)checks.add(()->{
            Input input=input(pair[0],pair[1]);
            var root=FactionCandidateCodec.decodeRootProjection(encode(input.root()));
            assertEquals(BigInteger.valueOf(pair[0]),root.frame().orElseThrow(()->new AssertionError("normalized Root actor was lost: "+pair[0])).actorId());
            assertTrue(root.directLandedVassals().known().orElseThrow().contains(BigInteger.valueOf(pair[1])));
            var outcome=FactionCandidateCodec.evaluatePrivateCandidate(encode(input.snapshot()),root,encode(input.privateResult()),input.reserve());
            var evaluated=assertInstanceOf(FactionCandidatePolicy.Evaluated.class,outcome,outcome::toString);
            var selected=assertInstanceOf(FactionGiftChoice.Selected.class,evaluated.choice(),evaluated.choice()::toString);
            assertEquals(BigInteger.valueOf(pair[0]),selected.playerCharacterId());assertEquals(BigInteger.valueOf(pair[1]),selected.recipientCharacterId());
            assertEquals(FactionGiftChoice.MembershipRole.LEADER,selected.membershipRole());
            byte[] persisted=FactionGiftPolicy.encode(selected);assertEquals(selected,FactionGiftPolicy.decodeChoice(persisted));
            assertArrayEquals(persisted,FactionGiftPolicy.encode(FactionGiftPolicy.decodeChoice(persisted)));
            Obj candidate=DriverJson.object(FactionCandidateCodec.encodeCandidateResult(evaluated),FactionCandidateCodec.MAX_BYTES);
            assertEquals(new Bool(false),candidate.get("gift_submission_enabled"));assertEquals(new Bool(false),candidate.get("public_capability_advertised"));
            assertEquals(n(pair[1]),object(candidate.get("choice"),"candidate choice").get("recipient_character_id"));
        });assertAll("original normalized Root to real candidate/Gift/persistence",checks);
    }
    @Test void typedCharacterConstructorsRetainZeroNegativeAndSignedLimits(){
        var checks=new ArrayList<Executable>();
        for(long id:new long[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE}){
            checks.add(()->assertEquals(BigInteger.valueOf(id),new FactionCandidatePolicy.Frame(BigInteger.ONE,BigInteger.ZERO,BigInteger.valueOf(id)).actorId()));
            checks.add(()->assertEquals(List.of(BigInteger.valueOf(id)),new FactionCandidatePolicy.IdVector(Optional.of(List.of(BigInteger.valueOf(id)))).known().orElseThrow()));
            checks.add(()->assertEquals(BigInteger.valueOf(id),choice(2,id).recipientCharacterId()));
            checks.add(()->assertEquals(BigInteger.valueOf(id),choice(id,3).playerCharacterId()));
        }assertAll("typed CharacterID data constructors",checks);
    }
    @Test void invalidCharacterTokensAndUint32AliasesStayUnavailableOrReject()throws Exception {
        Input input=input(2,3);var checks=new ArrayList<Executable>();
        var good=FactionCandidateCodec.decodeCandidateInput(encode(candidateInput(input)));
        Obj originalChoice=DriverJson.object(FactionGiftPolicy.encode(choice(2,3)),FactionGiftPolicy.MAX_INPUT_BYTES);
        for(long bad:new long[]{-1,(long)Integer.MIN_VALUE-1,(long)Integer.MAX_VALUE+1,4294967294L}){
            checks.add(()->assertThrows(IllegalArgumentException.class,()->new FactionCandidatePolicy.Frame(BigInteger.ONE,BigInteger.ZERO,BigInteger.valueOf(bad))));
            checks.add(()->assertThrows(IllegalArgumentException.class,()->new FactionCandidatePolicy.IdVector(Optional.of(List.of(BigInteger.valueOf(bad))))));
            checks.add(()->assertThrows(IllegalArgumentException.class,()->choice(bad,3)));
            checks.add(()->assertThrows(IllegalArgumentException.class,()->choice(2,bad)));
            var observation=good.preview().observation().orElseThrow();
            checks.add(()->assertThrows(IllegalArgumentException.class,()->new FactionCandidatePolicy.Observation(observation.original(),observation.frame(),Optional.of(BigInteger.valueOf(bad)),observation.sourceFactionId())));
            var preview=good.preview();
            checks.add(()->assertThrows(IllegalArgumentException.class,()->new FactionCandidatePolicy.PrivatePreview(preview.acceptedEnvelope(),preview.status(),preview.hasNativeObject(),preview.receiverReady(),preview.nativeSourceId(),Optional.of(BigInteger.valueOf(bad)),preview.observation())));
        }
        for(Value bad:List.of(n(-1),n((long)Integer.MIN_VALUE-1),n((long)Integer.MAX_VALUE+1),n(4294967294L),new Bool(true),new DecimalValue("2.0"),new Text("0"),Nil.INSTANCE)){
            checks.add(()->assertThrows(IllegalArgumentException.class,()->FactionGiftPolicy.decodeChoice(encode(originalChoice.with("player_character_id",bad)))));
            checks.add(()->assertThrows(IllegalArgumentException.class,()->FactionGiftPolicy.decodeChoice(encode(originalChoice.with("recipient_character_id",bad)))));
            checks.add(()->assertTrue(FactionCandidateCodec.decodeRootProjection(encode(input.root().with("player_character_id",bad))).frame().isEmpty()));
            checks.add(()->assertTrue(FactionCandidateCodec.decodeRootProjection(encode(input.root().with("direct_landed_vassal_character_ids",new Arr(List.of(bad))))).directLandedVassals().known().isEmpty()));
            checks.add(()->{
                Obj nativeResult=object(input.privateResult().get("native"),"native");
                Obj observation=object(nativeResult.get("observation"),"observation").with("player_character_id",bad);
                Obj poisoned=input.privateResult().with("native",nativeResult.with("observation",observation));
                var result=FactionCandidateCodec.evaluatePrivateCandidate(encode(input.snapshot()),FactionCandidateCodec.decodeRootProjection(encode(input.root())),encode(poisoned),input.reserve());
                assertInstanceOf(FactionCandidatePolicy.Rejected.class,result);
            });
        }assertAll("invalid role DATA never narrows or aliases",checks);
    }
    @Test void factionRevisionHashCostBudgetAndFrameRemainIndependentDomains()throws Exception {
        Input input=input(2,3);Obj nativeResult=object(input.privateResult().get("native"),"native"),observation=object(nativeResult.get("observation"),"observation");
        Obj request=new Obj(Map.of("observations",new Arr(List.of(observation)),"complete_native_enumeration",new Bool(true),"minimum_gold_reserve_raw",new IntegerValue(input.reserve())));
        assertInstanceOf(FactionGiftChoice.Selected.class,FactionGiftPolicy.choose(encode(request)));
        for(String field:List.of("queried_source_faction_id","snapshot_revision","native_snapshot_revision")){
            Obj bad=request.with("observations",new Arr(List.of(observation.with(field,n(0)))));
            assertInstanceOf(FactionGiftChoice.Declined.class,FactionGiftPolicy.choose(encode(bad)));
        }
        Obj preview=object(observation.get("gift_preview"),"preview");
        for(String field:List.of("definition_stable_hash","gold_cost_raw","opinion_delta")){
            Obj bad=observation.with("gift_preview",preview.with(field,n(0)));
            assertInstanceOf(FactionGiftChoice.Declined.class,FactionGiftPolicy.choose(encode(request.with("observations",new Arr(List.of(bad))))));
        }
        assertInstanceOf(FactionGiftChoice.Declined.class,FactionGiftPolicy.choose(encode(request.with("minimum_gold_reserve_raw",n(-2)))));
        var projected=FactionCandidateCodec.decodeRootProjection(encode(input.root()));
        Obj drift=input.snapshot().with("native_revision",new IntegerValue(integer(input.snapshot().get("native_revision"),"revision").add(BigInteger.ONE)));
        assertInstanceOf(FactionCandidatePolicy.Rejected.class,FactionCandidateCodec.evaluatePrivateCandidate(encode(drift),projected,encode(input.privateResult()),input.reserve()));
        Obj unrelated=nativeResult.with("source_faction_id",new IntegerValue(integer(nativeResult.get("source_faction_id"),"faction").add(BigInteger.ONE)));
        assertInstanceOf(FactionCandidatePolicy.Rejected.class,FactionCandidateCodec.evaluatePrivateCandidate(encode(input.snapshot()),projected,encode(input.privateResult().with("native",unrelated)),input.reserve()));
        for(String field:List.of("source_faction_id","snapshot_revision","native_snapshot_revision","definition_stable_hash","gold_cost_raw","opinion_delta")){
            Obj selected=DriverJson.object(FactionGiftPolicy.encode(choice(2,3)),FactionGiftPolicy.MAX_INPUT_BYTES).with(field,n(0));
            assertThrows(IllegalArgumentException.class,()->FactionGiftPolicy.decodeChoice(encode(selected)));
        }
    }
    private static FactionGiftChoice.Selected choice(long player,long recipient){return new FactionGiftChoice.Selected(BigInteger.ONE,BigInteger.valueOf(recipient),FactionGiftChoice.MembershipRole.LEADER,
            BigInteger.ONE,BigInteger.ONE,BigInteger.ZERO,BigInteger.valueOf(player),BigInteger.ONE,BigInteger.ONE,BigInteger.ONE);}
    private static Obj candidateInput(Input input){return new Obj(Map.of("snapshot",input.snapshot(),"root",input.root(),"private_result",input.privateResult(),"minimum_gold_reserve_raw",new IntegerValue(input.reserve())));}
    private static Input input(long actor,long recipient)throws Exception {
        if(originalRoot==null)originalRoot=CampaignRootContextJsonTest.originalActual4RootFixture();
        if(originalCandidateInput==null)try(var stream=RootSignedGiftConsumerTest.class.getResourceAsStream("/root-gift-character/private-native-selected.original.json")){
            assertNotNull(stream);originalCandidateInput=DriverJson.object(stream.readAllBytes(),FactionCandidateCodec.MAX_BYTES);
        }
        Obj root=remap(originalRoot,BigInteger.valueOf(12345),BigInteger.valueOf(actor));root=remap(root,BigInteger.valueOf(23456),BigInteger.valueOf(recipient));
        root=root.with("player_targeting_faction_count",n(1));BigInteger date=integer(root.get("date_raw"),"date"),revision=integer(root.get("snapshot_revision"),"revision");
        Obj envelope=new Obj(Map.of("step",new Text("query-campaign-root-context-v1"),"accepted",new Bool(true),"status",root.get("status"),"query_sequence",new IntegerValue(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)),
                "snapshot_revision",new IntegerValue(revision),"campaign_root_context",root,"backend_id",new Text("native-headless")));
        root=object(CampaignRootContextJson.normalizeNativeResult(DriverJson.object(encode(envelope),1_048_576),date,revision).get("campaign_root_context"),"actual normalized root");
        Obj snapshot=object(originalCandidateInput.get("snapshot"),"snapshot").with("native_revision",new IntegerValue(revision)).with("date_raw",new IntegerValue(date));
        snapshot=snapshot.with("played_character",object(snapshot.get("played_character"),"actor").with("character_id",n(actor)));
        Obj result=object(originalCandidateInput.get("private_result"),"private result"),nativeResult=object(result.get("native"),"native");
        Obj observation=object(nativeResult.get("observation"),"observation").with("snapshot_revision",new IntegerValue(revision)).with("native_snapshot_revision",new IntegerValue(revision))
                .with("observed_date_raw",new IntegerValue(date)).with("player_character_id",raw(actor)).with("source_faction_target_character_id",raw(actor))
                .with("recipient_character_id",raw(recipient)).with("source_faction_leader_character_id",raw(recipient)).with("source_faction_member_character_ids",new Arr(List.of(raw(recipient))));
        return new Input(root,snapshot,result.with("native",nativeResult.with("recipient_character_id",raw(recipient)).with("observation",observation)),integer(originalCandidateInput.get("minimum_gold_reserve_raw"),"reserve"));
    }
    private static Obj remap(Obj root,BigInteger old,BigInteger replacement){
        Obj value=object(map(root,"",old,replacement),"root");
        for(String field:List.of("direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids")){
            var ids=new ArrayList<Value>(array(value.get(field),field));ids.sort(Comparator.comparing(id->integer(id,"character")));value=value.with(field,new Arr(ids));
        }
        var related=new ArrayList<Value>(array(value.get("related_character_contexts"),"related"));related.sort(Comparator.comparing(item->integer(object(item,"related").get("character_id"),"character")));
        return value.with("related_character_contexts",new Arr(related));
    }
    private static Value map(Value value,String field,BigInteger old,BigInteger replacement){
        if(SCALARS.contains(field)&&value instanceof IntegerValue number&&old.equals(number.value()))return new IntegerValue(replacement);
        if(value instanceof Obj object){var fields=new LinkedHashMap<String,Value>();object.members().forEach((key,item)->fields.put(key,map(item,key,old,replacement)));return new Obj(fields);}
        if(value instanceof Arr rows){var result=new ArrayList<Value>();for(Value item:rows.items())result.add(VECTORS.contains(field)&&item instanceof IntegerValue number&&old.equals(number.value())?new IntegerValue(replacement):map(item,"",old,replacement));return new Arr(result);}
        return value;
    }
}
