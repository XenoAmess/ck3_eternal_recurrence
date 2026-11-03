package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual shared production helper versus unchanged old decoder; public DATA only, no archive/native issuer. */
public final class PersistentCooldownProjectionWitness {
    private static int checks;
    private PersistentCooldownProjectionWitness() { }
    public static void main(String[] args) {
        fullFiveFieldsAndIgnoredMaterial();
        presenceAndNullablePayloads();
        hiddenNullFirstFailure();
        decimalAndSurrogateKinds();
        manualDeepFallback();
        foreignNumericOperations();
        distinctLifeAndCurrentWorld();
        viewExpiryAndNullRoot();
        System.out.println("PASS cases=8 checks="+checks+" pure_DATA_only=true Archive_Game=false");
    }
    private static Snapshot legacy(Obj input) {
        return DeclarationOpportunityCooldown.snapshot(OpportunityJson.toNode(input));
    }
    private static Snapshot actual(Obj input) {return DriverPersistentPlanningState.cooldownSnapshot(input);}
    private static Snapshot equalSnapshots(Obj input) {
        Snapshot a=legacy(input),b=actual(input);equal(a,b,"actual shared helper equals unchanged decoder");return b;
    }
    private static void fullFiveFieldsAndIgnoredMaterial() {
        BigInteger id=new BigInteger("18446744073709551615");
        Map<String,Value> data=new LinkedHashMap<>(semantic(true,id,true).members());
        List<Value> large=new ArrayList<>();
        for(int i=0;i<256;i++)large.add(new Obj(Map.of("command",new Text("opaque-command-"+i),
                "payload",new Arr(List.of(new DecimalValue("-0.0"),new IntegerValue(BigInteger.valueOf(i)),new Text("x".repeat(64)))))));
        data.put("unrelated_complete_command_history",new Arr(large));
        data.put("active_event",new Obj(Map.of("unused",new Text("event body"))));
        Snapshot got=equalSnapshots(new Obj(data));
        equal(new Snapshot(true,Optional.of(List.of(new War(new NumericWarId(id),true))),true,false,
                Optional.of(new Continuity(true,Optional.of("war_started"),true,true,Optional.of(new NumericWarId(id))))),
                got,"literal five-field result and exact arbitrary precision id");
    }
    private static void presenceAndNullablePayloads() {
        Obj input=new Obj(Map.of("paused",new Text("true"),"active_wars",new Arr(List.of(
                new Bool(false),Nil.INSTANCE,new Obj(Map.of()),new Obj(Map.of("war_id",Nil.INSTANCE)),
                new Obj(Map.of("war_id",new IntegerValue(null),"player_side",new Text(null))))),
                "war_declaration_continuity_v1",new Obj(Map.of("schema",new Text(null),"status",new Text(null),"war_id",new IntegerValue(null))),
                "active_event",new Arr(List.of()),"pending_character_interaction",new Obj(Map.of())));
        Snapshot got=equalSnapshots(input);
        check(!got.paused(),"text true is not boolean true");equal(Optional.of(List.of()),got.activeWars(),"ignored rows and actual null numeric id");
        check(!got.activeEvent()&&got.pendingInteraction(),"object presence only");
        equal(Optional.of(new Continuity(false,Optional.empty(),false,false,Optional.empty())),got.continuity(),"nullable scalar payloads preserve null-node behavior");
        Map<String,Value> nullKey=new LinkedHashMap<>();nullKey.put(null,new Text("ignored"));nullKey.put("paused",new Bool(true));
        compareOutcome(new Obj(nullKey));
    }
    private static void hiddenNullFirstFailure() {
        Map<String,Value> bad=new LinkedHashMap<>();
        bad.put("active_wars",new Arr(List.of(new Obj(Map.of("war_id",new DecimalValue("-0.0"))))));
        Map<String,Value> hidden=new LinkedHashMap<>();hidden.put("bad",null);
        bad.put("unrelated",new Obj(hidden));Obj input=new Obj(bad);
        Failure a=failure(()->legacy(input)),b=failure(()->actual(input));
        equal(a,b,"whole-tree hidden null still precedes selected-war decoder error");
        equal(new Failure(IllegalArgumentException.class,"null Java value is not JSON null"),b,"original first error literal");
        bad.remove("unrelated");
        Failure selected=failure(()->actual(new Obj(bad)));
        equal(new Failure(IllegalArgumentException.class,"integer token required; bool/float/string forbidden"),selected,"selected error remains when hidden invalid node absent");
    }
    private static void decimalAndSurrogateKinds() {
        for(String token:List.of("-0.0","1e3","0E-999999999999999999999")) {
            Obj input=new Obj(Map.of("active_wars",new Arr(List.of(new Obj(Map.of("war_id",new DecimalValue(token)))))));
            Failure a=failure(()->legacy(input)),b=failure(()->actual(input));equal(a,b,"decimal war id keeps old token-kind error");
            equal(IllegalArgumentException.class,b.type(),"actual decimal mismatch type");
        }
        String unpaired=String.valueOf((char)0xD800);
        Obj input=new Obj(Map.of("active_wars",new Arr(List.of(new Obj(Map.of(
                "war_id",new Text(unpaired),"player_side",new Text(unpaired))))),
                "unrelated",new Obj(Map.of("token",new DecimalValue("-0.0"),"text",new Text(unpaired)))));
        Snapshot got=equalSnapshots(input);War row=got.activeWars().orElseThrow().get(0);
        equal(new TextWarId(unpaired),row.id(),"existing tree projection does not invent surrogate rejection");check(!row.playerAttacker(),"surrogate text is not attacker");
    }
    private static void manualDeepFallback() {
        Value deep=new Text("leaf");for(int i=0;i<70;i++)deep=new Obj(Map.of("nested",deep));
        Obj input=new Obj(Map.of("paused",new Bool(true),"active_wars",new Arr(List.of()),"unrelated",deep));
        Snapshot got=equalSnapshots(input);check(got.paused(),"eligibility depth cutoff falls back, never newly rejects handmade tree");
    }
    private static void foreignNumericOperations() {
        ForeignInteger baselineId=new ForeignInteger("7"),candidateId=new ForeignInteger("7");
        Obj baseline=semantic(true,baselineId,true),candidate=semantic(true,candidateId,true);
        baselineId.operations.clear();candidateId.operations.clear();
        Snapshot a=legacy(baseline),b=actual(candidate);
        equal(List.copyOf(baselineId.operations),List.copyOf(candidateId.operations),"qualification adds no foreign calls");
        check(((NumericWarId)a.activeWars().orElseThrow().get(0).id()).value()==baselineId,"legacy foreign raw id identity");
        check(((NumericWarId)b.activeWars().orElseThrow().get(0).id()).value()==candidateId,"actual foreign raw id identity");
        State state=DeclarationOpportunityCooldown.initial(frame(1000,10));
        DeclarationOpportunityCooldown.view(state,a,frame(1000,10));DeclarationOpportunityCooldown.view(state,b,frame(1000,10));
        equal(List.copyOf(baselineId.operations),List.copyOf(candidateId.operations),"same later reducer foreign operations and order");
        check(candidateId.operations.contains("signum"),"real later verified-war predicate exercised");
    }
    private static void distinctLifeAndCurrentWorld() {
        Frame before=frame(1000,10),after=frame(1024,12);
        UInt64 seq=new UInt64(BigInteger.TEN);
        State state=new State(BigInteger.valueOf(7),"episode",1,Optional.empty(),
                Optional.of(new Pending(seq,Optional.of("source"),BigInteger.TEN,BigInteger.valueOf(1000),BigInteger.valueOf(77))),Optional.empty(),Optional.empty());
        Outcome outcome=new Outcome(true,Optional.of("life-advance"),Optional.of(new TurnResult("life-advance","postcondition",true,
                Optional.of(BigInteger.valueOf(1000)),Optional.of(BigInteger.valueOf(1024)))));
        Obj ending=semantic(true,null,false),current=semantic(true,BigInteger.valueOf(999),true);
        Reduction oldTurn=DeclarationOpportunityCooldown.afterTurn(state,before,outcome,legacy(ending),after);
        Reduction newTurn=DeclarationOpportunityCooldown.afterTurn(state,before,outcome,actual(ending),after);
        equal(oldTurn,newTurn,"LIFE ending actual reducer equality");number(2,newTurn.state().consecutiveNoWarRounds(),"second source-bound round closes");
        equal(Optional.of(BigInteger.valueOf(1744)),newTurn.state().cooldownUntilDateRaw(),"30-day raw deadline preserved");
        equal(BigInteger.valueOf(30),newTurn.view().remainingDays(),"actual 30-day view");
        Reduction oldView=DeclarationOpportunityCooldown.view(oldTurn.state(),legacy(current),after);
        Reduction newView=DeclarationOpportunityCooldown.view(newTurn.state(),actual(current),after);
        equal(oldView,newView,"distinct current-frame VIEW actual reducer equality");number(0,newView.state().consecutiveNoWarRounds(),"current verified war resets independently of ending");
        equal(Optional.of(new NumericWarId(BigInteger.valueOf(999))),newView.state().lastConfirmedWarId(),"actual current world retained, never ending snapshot reused");
    }
    private static void viewExpiryAndNullRoot() {
        State state=new State(BigInteger.valueOf(7),"episode",2,Optional.of(BigInteger.valueOf(1744)),Optional.empty(),Optional.empty(),Optional.empty());
        Obj input=semantic(true,null,false);Frame at=frame(1744,13);
        Reduction a=DeclarationOpportunityCooldown.view(state,legacy(input),at),b=DeclarationOpportunityCooldown.view(state,actual(input),at);
        equal(a,b,"expired view actual reducer equality");check(!b.view().active(),"deadline equality is expired");equal(BigInteger.ZERO,b.view().remainingDays(),"expired zero days");
        number(2,b.state().consecutiveNoWarRounds(),"expiry retains streak");equal(Optional.of(BigInteger.valueOf(1744)),b.state().cooldownUntilDateRaw(),"expiry retains source deadline");
        equal(failure(()->legacy(null)),failure(()->actual(null)),"null root original first failure");
    }
    private static Obj semantic(boolean paused,BigInteger war,boolean verified) {
        Value wars=war==null?new Arr(List.of()):new Arr(List.of(new Obj(Map.of("war_id",new IntegerValue(war),"player_side",new Text("attacker")))));
        Value continuity=verified?new Obj(Map.of("schema",new Text("war-declaration-continuity-v1"),"status",new Text("war_started"),
                "native_response",new Text("accepted"),"postcondition_verified",new Bool(true),"war_id",new IntegerValue(war))):Nil.INSTANCE;
        return new Obj(Map.of("paused",new Bool(paused),"active_wars",wars,"war_declaration_continuity_v1",continuity,
                "active_event",Nil.INSTANCE,"pending_character_interaction",Nil.INSTANCE));
    }
    private static Frame frame(long date,long revision) {return new Frame(BigInteger.valueOf(7),"episode",BigInteger.valueOf(date),BigInteger.valueOf(revision),BigInteger.valueOf(77),Optional.of("snapshot-"+revision));}
    private record Failure(Class<?> type,String message) { }
    private static Failure failure(Supplier<Snapshot> call) {
        try{call.get();}catch(RuntimeException e){return new Failure(e.getClass(),e.getMessage());}
        throw new AssertionError("expected original DATA error");
    }
    private static void compareOutcome(Obj input) {
        Snapshot original;
        try{original=legacy(input);}catch(RuntimeException e){equal(new Failure(e.getClass(),e.getMessage()),failure(()->actual(input)),"nullable-key original failure");return;}
        equal(original,actual(input),"nullable-key original success");
    }
    private static void check(boolean value,String name){checks++;if(!value)throw new AssertionError(name);}
    private static void equal(Object a,Object b,String name){check(a.equals(b),name);}
    private static void number(long a,long b,String name){check(a==b,name);}
    private static final class ForeignInteger extends BigInteger {
        private static final long serialVersionUID=1L;
        transient final List<String> operations=new ArrayList<>();
        ForeignInteger(String value){super(value);}
        @Override public int signum(){operations.add("signum");return super.signum();}
        @Override public int bitLength(){operations.add("bitLength");return super.bitLength();}
        @Override public int compareTo(BigInteger other){operations.add("compareTo");return super.compareTo(other);}
        @Override public boolean equals(Object other){operations.add("equals");return super.equals(other);}
        @Override public int hashCode(){operations.add("hashCode");return super.hashCode();}
        @Override public String toString(){operations.add("toString");return super.toString();}
    }
}
