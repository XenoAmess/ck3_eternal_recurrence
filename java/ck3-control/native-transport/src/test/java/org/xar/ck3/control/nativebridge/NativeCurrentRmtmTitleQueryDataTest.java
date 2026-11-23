package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA draft only: no original C++ frames, exchange, getter or qualification is fabricated. */
final class NativeCurrentRmtmTitleQueryDataTest {
    private static final BigInteger MAX=new BigInteger("18446744073709551615");
    private static CoreFrame.Prefix core(int date,int actor){return new CoreFrame.Prefix(date,2,true,0,true,true,actor,true);}
    private static CurrentRmtmTitleQuerySource empty(int actor,long title){return new CurrentRmtmTitleQuerySource(actor,title,Optional.empty(),Optional.empty(),0,List.of(),0,true);}
    private static CurrentRmtmTitleQueryResult available(int date,CurrentRmtmTitleQuerySource source){return new CurrentRmtmTitleQueryResult(
            CurrentRmtmTitleQueryResult.Status.AVAILABLE,true,MAX,MAX,Optional.of(core(date,source.actorId())),
            Optional.of(new CurrentLetterResult.OwnerWitness(MAX,MAX,MAX,0xffff_ffffL)),Optional.of(source),Optional.empty());}
    private static ObjectNode token(CurrentRmtmTitleQueryResult value)throws IOException{return NativeWire.object(NativeWire.parse(value.encode().bytes()));}
    private static CurrentRmtmTitleQueryResult decode(ObjectNode value)throws IOException{return CurrentRmtmTitleQueryResult.decode(new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)));}

    @Test void fixedRequestHasSevenClaimFieldsAndNoCallerTitleOrAuthority()throws IOException{
        var request=CurrentRmtmTitleQuery.request(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,core(0,-2)));
        assertEquals("query-current-rmtm-title-v1",request.step());assertEquals(Optional.of("game.query.current-rmtm-title.v1"),request.requiredCapability());
        var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("rmtm_title","arguments"));assertEquals(0,fields.get("arguments").size());
        var claim=StrictJson.object(fields.get("rmtm_title"),Set.of("schema","game_version","executable_sha256","adapter_id","backend","action","expected_core"));
        assertEquals("query_primary_title",claim.get("action").textValue());assertEquals(8,claim.get("expected_core").size());
        for(String key:List.of("title_id","expected_full_title_id","phase","role","provider_generation","query_sequence","CCC_epoch","law_key"))assertFalse(claim.has(key));
    }
    @Test void signedDateAndActorGuardsAreDataWithoutPositiveDateOrSignedFullIdCoercion()throws IOException{
        for(int date:new int[]{Integer.MIN_VALUE,-24,0,Integer.MAX_VALUE})for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE}){
            var p=core(date,actor);CurrentRmtmTitleQuery.request(new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,p));
            var s=empty(actor,0xffff_fffeL);var value=available(date,s);assertEquals(value,CurrentRmtmTitleQueryResult.decode(value.encode()));assertEquals(0xffff_fffeL,s.fullTitleId());
        }
        assertThrows(IllegalArgumentException.class,()->empty(-1,0));
        assertThrows(IllegalArgumentException.class,()->CurrentRmtmTitleQuery.request(new CoreFrame.Partial(ExactCk3Build.CK3_12004,core(0,0))));
    }
    @Test void fullGenerationIdsAcceptZeroAndHighBitsButRejectOnlySentinelAndOutOfRange()throws IOException{
        for(long id:new long[]{0,1,0x8000_0000L,0xffff_fffeL}){
            var s=new CurrentRmtmTitleQuerySource(0,id,Optional.of(new CurrentRmtmTitleQuerySource.CharacterRef(id,false)),Optional.empty(),1,List.of(new CurrentRmtmTitleQuerySource.Law(id,"law.key-1:scope")),0,true);
            assertEquals(s,CurrentRmtmTitleQuerySource.decode(s.encode()));
        }
        for(long id:new long[]{-1,0xffff_ffffL,0x1_0000_0000L}){
            assertThrows(IllegalArgumentException.class,()->empty(0,id));assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource.CharacterRef(id,true));
            assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource.Law(id,"law"));
        }
        var s=empty(0,0).encode();s.put("full_title_id","0");assertThrows(IOException.class,()->CurrentRmtmTitleQuerySource.decode(s));
        s.put("full_title_id",0.0);assertThrows(IOException.class,()->CurrentRmtmTitleQuerySource.decode(s));
    }
    @Test void knownEmptyOwnLawDataAndNullableHolderAreNotUnavailableOrEffectiveLaws()throws IOException{
        var s=empty(36423,47);assertEquals(s,CurrentRmtmTitleQuerySource.decode(s.encode()));assertEquals(0,s.nativeLawCount());assertTrue(s.physicalOwnLaws().isEmpty());
        assertTrue(s.holder().isEmpty());assertTrue(s.engineCurrentHeir().isEmpty());assertTrue(available(0,s).sourceAvailable());
        var absent=new CurrentRmtmTitleQueryResult(CurrentRmtmTitleQueryResult.Status.UNAVAILABLE,true,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(""));
        assertFalse(absent.sourceAvailable());assertEquals(absent,CurrentRmtmTitleQueryResult.decode(absent.encode()));
        assertThrows(IOException.class,()->CurrentRmtmTitleQuerySource.decode(StrictJson.object()));
    }
    @Test void completeOrderedPhysicalArrayRequiresExactCountsUniqueIdsAndKeys()throws IOException{
        var laws=new ArrayList<CurrentRmtmTitleQuerySource.Law>();for(int i=0;i<64;i++)laws.add(new CurrentRmtmTitleQuerySource.Law(i,"law_"+i));
        var s=new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),64,laws,0,true);laws.clear();assertEquals(64,s.physicalOwnLaws().size());assertEquals(s,CurrentRmtmTitleQuerySource.decode(s.encode()));
        assertThrows(UnsupportedOperationException.class,()->s.physicalOwnLaws().clear());
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),1,List.of(),0,true));
        for(var duplicate:List.of(List.of(new CurrentRmtmTitleQuerySource.Law(1,"a"),new CurrentRmtmTitleQuerySource.Law(1,"b")),List.of(new CurrentRmtmTitleQuerySource.Law(1,"a"),new CurrentRmtmTitleQuerySource.Law(2,"a"))))
            assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),2,duplicate,0,true));
        for(String key:List.of("","x".repeat(257),"a b","\0","\u4e2d","\ud800"))assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource.Law(1,key));
    }
    @Test void currentHeirCountAndDeadHeirDataNeverBecomeExecuteTimeWitness()throws IOException{
        var dead=new CurrentRmtmTitleQuerySource.CharacterRef(0xffff_fffeL,false);
        var s=new CurrentRmtmTitleQuerySource(-2,0,Optional.empty(),Optional.of(dead),0,List.of(),4096,true);
        assertEquals(s,CurrentRmtmTitleQuerySource.decode(s.encode()));assertFalse(s.engineCurrentHeir().orElseThrow().alive());
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.of(dead),0,List.of(),0,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),0,List.of(),1,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.of(dead),0,List.of(),4097,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),0,List.of(),0,false));
    }
    @Test void resultU64CountersAreCanonicalStringsAndOwnerThreadIsUint32()throws IOException{
        var original=available(0,empty(0,0));assertEquals(22,token(original).size());assertEquals(MAX,CurrentRmtmTitleQueryResult.decode(original.encode()).querySequence());
        for(String key:List.of("provider_generation","query_sequence","claim_sequence")){
            for(String text:List.of("00","+1","-1","18446744073709551616")){var n=token(original);n.put(key,text);assertThrows(IOException.class,()->decode(n));}
            var n=token(original);n.put(key,1);assertThrows(IOException.class,()->decode(n));
        }
        var hugeThread=token(original);((ObjectNode)hugeThread.get("owner")).put("thread_id",0x1_0000_0000L);assertThrows(IOException.class,()->decode(hugeThread));
        var zeroThread=token(original);((ObjectNode)zeroThread.get("owner")).put("thread_id",0);assertThrows(IOException.class,()->decode(zeroThread));
    }
    @Test void refusalEmptyReasonAndVerifiedFactsRemainDataButCleanupUnknownStaysIndeterminate()throws IOException{
        for(var status:List.of(CurrentRmtmTitleQueryResult.Status.UNAVAILABLE,CurrentRmtmTitleQueryResult.Status.EXPIRED,CurrentRmtmTitleQueryResult.Status.STALE_SOURCE,CurrentRmtmTitleQueryResult.Status.INDETERMINATE)){
            var q=new CurrentRmtmTitleQueryResult(status,status!=CurrentRmtmTitleQueryResult.Status.INDETERMINATE,BigInteger.ZERO,BigInteger.ZERO,Optional.of(core(-1,0)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.TEN,1)),Optional.empty(),Optional.of(""));
            assertEquals(q,CurrentRmtmTitleQueryResult.decode(q.encode()));assertFalse(q.successful());assertEquals("",q.unavailableReason().orElseThrow());
        }
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmTitleQueryResult(CurrentRmtmTitleQueryResult.Status.UNAVAILABLE,false,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("why")));
        var n=token(available(0,empty(0,0)));n.put("cleanup_known",false);assertThrows(IOException.class,()->decode(n));
    }
    @Test void strictShapesPreserveIntegerKindsAndOnlyExeHashHasCaseEquivalence()throws IOException{
        var original=available(0,empty(0,0));var n=token(original);n.put("executable_sha256",ExactCk3Build.CK3_121003_STEAM_26785313.executableSha256().toLowerCase(java.util.Locale.ROOT));assertEquals(original,decode(n));
        n=token(original);n.put("backend",CurrentRmtmTitleQuery.BACKEND.toUpperCase(java.util.Locale.ROOT));var wrong=n;assertThrows(IOException.class,()->decode(wrong));
        var extra=token(original);extra.put("effective_law",true);assertThrows(IOException.class,()->decode(extra));
        var floating=token(original);((ObjectNode)floating.get("source")).put("native_law_count",0.0);assertThrows(IOException.class,()->decode(floating));
        var missing=token(original);missing.remove("source");assertThrows(IOException.class,()->decode(missing));
    }
    @Test void allMutationAndDateSaveFlagsStayFalseEvenWithKnownSource()throws IOException{
        var q=available(0,empty(0,0));assertEquals(BigInteger.ZERO,q.claimSequence());assertFalse(q.effectAttempted());assertFalse(q.nativeReturned());assertFalse(q.nativeHandled());assertFalse(q.newDateObserved());assertFalse(q.physicalSaveConfirmed());
        for(String key:List.of("effect_attempted","native_returned","native_handled","new_date_observed","physical_save_confirmed")){var n=token(q);n.put(key,true);assertThrows(IOException.class,()->decode(n));}
        var n=token(q);n.put("claim_sequence","1");assertThrows(IOException.class,()->decode(n));
    }
}
