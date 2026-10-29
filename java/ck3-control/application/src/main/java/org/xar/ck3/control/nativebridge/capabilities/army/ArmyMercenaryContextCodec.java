package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.finance.NativeMercenaryMarket;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Complete native market payload normalizer. Terms have one shared decoder, independently of payment or employment proof. */
public final class ArmyMercenaryContextCodec {
    private static final BigInteger U32=BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE), U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE), I32=BigInteger.valueOf(Integer.MAX_VALUE), I64=BigInteger.valueOf(Long.MAX_VALUE);
    public record Availability(boolean available,Optional<String> unavailableReason) { public Availability {Objects.requireNonNull(unavailableReason);} }
    public record Strength(Availability status,Optional<Integer> currentSoldiers) { public Strength {Objects.requireNonNull(status);Objects.requireNonNull(currentSoldiers);} }
    public record Location(Optional<Integer> homeTitle,Optional<Integer> homeProvince,Optional<Integer> hireProvince,Optional<Integer> activeWars,Optional<Boolean> attemptedInActiveWar,
            boolean homeReady,String homeFailure,String homeSource,boolean hirePositionReady,String hireFailure,String hireSource) { }
    public sealed interface RegimentType permits Maa,NotMaa { }
    public record Maa(String key,int signedSiegeTier) implements RegimentType {public Maa {require(key!=null&&!key.isEmpty(),"native MAA type key required");}}
    public record NotMaa() implements RegimentType { }
    public record Regiment(long ordinal,long persistentRegimentId,int currentSoldiers,int maximumSoldiers,RegimentType type,Obj original) { }
    public record Composition(Availability status,long companyId,Availability holder,Optional<Long> holderCharacterId,Optional<Long> regimentCount,long coveredRegimentCount,
            Optional<Long> currentRegimentSoldiers,Optional<Long> maximumRegimentSoldiers,Optional<Long> positiveSiegeTierCurrentSoldiers,Optional<Integer> maximumSiegeTier,List<Regiment> regiments,Obj original) {
        public Composition {regiments=List.copyOf(regiments);}
    }
    public record Readiness(boolean compositionReady,boolean hireTermsReady,boolean hireReady) { }
    public record Candidate(long companyId,Optional<Long> employerId,long managerSlot,Strength strength,NativeMercenaryMarket.Terms terms,Location location,Optional<Composition> composition,Readiness readiness,Obj normalized) { }
    public record Observation(String gameVersion,String executableSha256,BigInteger actor,BigInteger dateRaw,BigInteger captureEpoch,Availability status,List<Candidate> candidates,Obj normalized) {
        public Observation {candidates=List.copyOf(candidates);Objects.requireNonNull(normalized);}
    }
    private ArmyMercenaryContextCodec() { }
    public static Observation decode(Obj value,Obj actualSnapshot) {
        required(value,"schema","game_version","executable_sha256","actor_character_id","date_raw","capture_epoch","read_only","native_hire_mode","available","unavailable_reason","rows");
        String version=text(value.get("game_version"),"game version"),sha=text(value.get("executable_sha256"),"executable SHA");
        String expectedSha=switch(version) {case "1.20.0.3"->"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";case "1.20.0.4"->"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";default->throw new IllegalArgumentException("unsupported native mercenary build");};
        require(expectedSha.equalsIgnoreCase(sha)&&new Text(version.equals("1.20.0.4")?"ck3_12004_player_mercenary_context_v1":"ck3_12003_player_mercenary_context_v1").equals(value.get("schema")),"mixed or unknown mercenary native schema/build");
        if(version.equals("1.20.0.4")) currentBuild(actualSnapshot,version,expectedSha);
        BigInteger actor=integer(value.get("actor_character_id"),"actor"),date=integer(value.get("date_raw"),"date");
        require(actor.equals(integer(object(actualSnapshot.get("played_character"),"actual player").get("character_id"),"actual player ID")) && date.equals(integer(actualSnapshot.get("date_raw"),"actual date")) && new Bool(true).equals(value.get("read_only")) && BigInteger.ONE.equals(integer(value.get("native_hire_mode"),"hire mode")),"mercenary payload differs from actual actor/date/read mode");
        BigInteger epoch=bounded(value.get("capture_epoch"),BigInteger.ONE,U64,"capture epoch"); Availability status=availability(value,"collection");
        List<Candidate> candidates=new ArrayList<>(); List<Value> rows=new ArrayList<>();
        for(Value item:array(value.get("rows"),"market rows")) {
            Obj row=object(item,"mercenary candidate"); required(row,"company_id","employer_id","manager_slot_index","troop_strength","final_terms","location");
            long company=bounded(row.get("company_id"),BigInteger.ZERO,U32,"company full ID").longValueExact(),slot=bounded(row.get("manager_slot_index"),BigInteger.ZERO,U32,"manager slot").longValueExact();
            Optional<Long> employer=optional(row.get("employer_id"),BigInteger.ZERO,U32,"employer full ID");
            Obj rawStrength=object(row.get("troop_strength"),"current strength"); required(rawStrength,"available","unavailable_reason","current_soldiers"); Availability strengthStatus=availability(rawStrength,"current strength");
            Optional<Integer> soldiers=optional(rawStrength.get("current_soldiers"),BigInteger.ZERO,I32,"current soldiers").map(Math::toIntExact); require(strengthStatus.available()==soldiers.isPresent(),"unavailable troop strength invented soldiers");
            Obj terms=object(row.get("final_terms"),"final native hire terms"); NativeMercenaryMarket.Terms decodedTerms=NativeMercenaryMarket.decodeTerms(terms);
            Location location=location(object(row.get("location"),"native company location"));
            Optional<Composition> composition=row.members().containsKey("composition_v1")?Optional.of(composition(object(row.get("composition_v1"),"composition_v1"),company)):Optional.empty();
            boolean compositionReady=composition.map(c->c.status().available()).orElse(false); var readiness=new Readiness(compositionReady,decodedTerms.available(),compositionReady&&decodedTerms.available()&&decodedTerms.canHire()==NativeMercenaryMarket.Truth.TRUE);
            Obj normalized=row.with("readiness_v1",new Obj(java.util.Map.of("composition_ready",new Bool(readiness.compositionReady()),"hire_terms_ready",new Bool(readiness.hireTermsReady()),"hire_ready",new Bool(readiness.hireReady()))));
            candidates.add(new Candidate(company,employer,slot,new Strength(strengthStatus,soldiers),decodedTerms,location,composition,readiness,normalized)); rows.add(normalized);
        }
        return new Observation(version,sha,actor,date,epoch,status,candidates,value.with("rows",new Arr(rows)));
    }
    public static Obj normalize(Obj value,Obj actualSnapshot) {return decode(value,actualSnapshot).normalized();}
    private static Location location(Obj row) {
        required(row,"company_home_title_id","company_home_province_id","hire_auto_raise_province_id","actor_active_war_count","hire_auto_raise_attempted_in_active_war","company_home_ready","company_home_failure","company_home_source","hire_auto_raise_position_ready","hire_auto_raise_position_failure","hire_auto_raise_position_source");
        Optional<Integer> title=optional(row.get("company_home_title_id"),BigInteger.valueOf(Integer.MIN_VALUE),I32,"home title").map(Math::toIntExact),home=optional(row.get("company_home_province_id"),BigInteger.ONE,I32,"home province").map(Math::toIntExact),hire=optional(row.get("hire_auto_raise_province_id"),BigInteger.ONE,I32,"native hire province").map(Math::toIntExact),wars=optional(row.get("actor_active_war_count"),BigInteger.ZERO,I32,"active wars").map(Math::toIntExact);
        Value attempted=row.get("hire_auto_raise_attempted_in_active_war"); Optional<Boolean> war=attempted==Nil.INSTANCE?Optional.empty():Optional.of(bool(attempted,"native active-war raise attempt"));
        String homeFailure=nonempty(row.get("company_home_failure"),"home failure"),homeSource=nonempty(row.get("company_home_source"),"home source"),hireFailure=nonempty(row.get("hire_auto_raise_position_failure"),"hire failure"),hireSource=nonempty(row.get("hire_auto_raise_position_source"),"hire source");
        return new Location(title,home,hire,wars,war,bool(row.get("company_home_ready"),"home ready"),homeFailure,homeSource,bool(row.get("hire_auto_raise_position_ready"),"hire ready"),hireFailure,hireSource);
    }
    private static Composition composition(Obj row,long expectedCompany) {
        required(row,"available","unavailable_reason","company_id","holder_available","holder_unavailable_reason","holder_character_id","regiment_count","covered_regiment_count","current_regiment_soldiers","maximum_regiment_soldiers","positive_siege_tier_current_soldiers","maximum_siege_tier_raw","regiments");
        Availability status=availability(row,"composition"); long company=bounded(row.get("company_id"),BigInteger.ZERO,U32,"composition company").longValueExact();require(company==expectedCompany,"composition belongs to another candidate company");
        boolean holderReady=bool(row.get("holder_available"),"holder availability"); Value holderReason=row.get("holder_unavailable_reason"); require(holderReady?holderReason==Nil.INSTANCE:holderReason instanceof Text t&&!t.value().isEmpty(),"holder reason contradicts availability");
        Optional<Long> holder=optional(row.get("holder_character_id"),BigInteger.ZERO,U32,"holder full ID");require(holderReady==holder.isPresent(),"holder availability and ID disagree");
        Optional<Long> count=optional(row.get("regiment_count"),BigInteger.ZERO,U32,"regiment count"); require(!status.available()||count.isPresent(),"complete composition lost regiment count");
        long covered=bounded(row.get("covered_regiment_count"),BigInteger.ZERO,U32,"covered regiments").longValueExact();
        Optional<Long> current=aggregate(row,"current_regiment_soldiers",status.available()),maximum=aggregate(row,"maximum_regiment_soldiers",status.available()),siege=aggregate(row,"positive_siege_tier_current_soldiers",status.available());
        Optional<Integer> tier=optional(row.get("maximum_siege_tier_raw"),BigInteger.ZERO,I32,"maximum siege tier").map(Math::toIntExact);require(status.available()==tier.isPresent(),"partial composition invented aggregate siege tier");
        List<Regiment> regiments=new ArrayList<>();
        for(Value value:array(row.get("regiments"),"regiments")) {
            Obj regiment=object(value,"native regiment"); required(regiment,"ordinal","persistent_regiment_id","current_soldiers","maximum_soldiers","type_status","maa_type_key","siege_tier_raw");
            long ordinal=bounded(regiment.get("ordinal"),BigInteger.ZERO,U32,"regiment ordinal").longValueExact(),id=bounded(regiment.get("persistent_regiment_id"),BigInteger.ZERO,U32,"persistent regiment full ID").longValueExact();
            int soldiers=bounded(regiment.get("current_soldiers"),BigInteger.ZERO,I32,"regiment soldiers").intValueExact(),max=bounded(regiment.get("maximum_soldiers"),BigInteger.ZERO,I32,"maximum soldiers").intValueExact();
            RegimentType type; String typeStatus=text(regiment.get("type_status"),"regiment type status");
            if(typeStatus.equals("available")) type=new Maa(nonempty(regiment.get("maa_type_key"),"MAA key"),bounded(regiment.get("siege_tier_raw"),BigInteger.valueOf(Integer.MIN_VALUE),I32,"signed MAA siege tier").intValueExact());
            else {require(typeStatus.equals("not_maa")&&regiment.get("maa_type_key")==Nil.INSTANCE&&regiment.get("siege_tier_raw")==Nil.INSTANCE,"non-MAA regiment invented native type data");type=new NotMaa();}
            regiments.add(new Regiment(ordinal,id,soldiers,max,type,regiment));
        }
        require(covered==regiments.size()&&(!status.available()||count.orElseThrow()==covered),"composition complete/partial regiment coverage differs");
        return new Composition(status,company,new Availability(holderReady,holderReady?Optional.empty():Optional.of(text(holderReason,"holder reason"))),holder,count,covered,current,maximum,siege,tier,regiments,row);
    }
    private static Optional<Long> aggregate(Obj row,String key,boolean ready) {var value=optional(row.get(key),BigInteger.ZERO,I64,key);require(ready==value.isPresent(),"partial composition invented aggregate "+key);return value;}
    private static Availability availability(Obj row,String field) {required(row,"available","unavailable_reason");boolean available=bool(row.get("available"),field+" available");Value reason=row.get("unavailable_reason");require(available?reason==Nil.INSTANCE:reason instanceof Text t&&!t.value().isEmpty(),field+" availability/reason differs");return new Availability(available,available?Optional.empty():Optional.of(text(reason,field+" reason")));}
    private static Optional<Long> optional(Value value,BigInteger low,BigInteger high,String field) {require(value!=null,"missing required nullable "+field);return value==Nil.INSTANCE?Optional.empty():Optional.of(bounded(value,low,high,field).longValueExact());}
    private static BigInteger bounded(Value value,BigInteger low,BigInteger high,String field) {BigInteger n=integer(value,field);require(n.compareTo(low)>=0&&n.compareTo(high)<=0,"native integer outside "+field+" domain");return n;}
    private static String nonempty(Value value,String field) {String text=text(value,field);require(!text.isEmpty(),"nonempty native "+field+" required");return text;}
    private static void required(Obj row,String...fields) {for(String field:fields)require(row.members().containsKey(field),"missing mercenary field "+field);}
    private static void currentBuild(Obj snapshot,String version,String sha) {
        Obj hello=object(object(snapshot.get("diagnostics"),"actual diagnostics").get("hello"),"actual hello");
        Value announcedVersion=hello.get("expected_ck3_version"),announcedSha=hello.get("expected_ck3_sha256");
        if(announcedVersion==null) announcedVersion=hello.get("game_version"); if(announcedSha==null) announcedSha=hello.get("executable_sha256");
        require(new Text(version).equals(announcedVersion)&&sha.equalsIgnoreCase(text(announcedSha,"actual executable")),"market build differs from actual source hello");
        if(hello.members().containsKey("game_version"))require(new Text(version).equals(hello.get("game_version")),"native hello version declarations conflict");
        if(hello.members().containsKey("executable_sha256"))require(sha.equalsIgnoreCase(text(hello.get("executable_sha256"),"actual executable")),"native hello executable declarations conflict");
    }
}
