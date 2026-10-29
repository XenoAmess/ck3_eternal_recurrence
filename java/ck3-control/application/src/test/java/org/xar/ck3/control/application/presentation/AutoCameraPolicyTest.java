package org.xar.ck3.control.application.presentation;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.presentation.PresentationIntent;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.contracts.presentation.PresentationRequest.Owner;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.contracts.presentation.PresentationRequest.Mode.*;
import static org.xar.ck3.control.application.presentation.AutoCameraModel.*;
class AutoCameraPolicyTest {
private static final Instant NOW=Instant.parse("2026-10-27T00:00:00Z");
private static final int DAY=10000;
private static final Map<Integer,String> LAND=Map.of(11,"b_first",21,"b_second",31,"b_third",41,"b_fourth",51,"b_fifth");
private static Owner owner(long pid,String birth,String episode) {
 return new Owner("machine","held",pid,birth,PresentationRequest.EXECUTABLE_SHA256,episode,"5");
}
private static final Owner OWNER=owner(42,"9007199254740993","episode");
private static Frame frame(Owner owner,int actor,int date,int rev,int nativeRev,String marker,List<War> wars,boolean mandatory) {
 return new Frame(owner,new PresentationRequest.Frame(marker,Integer.toString(rev),Integer.toString(nativeRev),actor,date),true,true,true,mandatory,wars);
}
private static Frame frame(int date,int rev,List<War> wars,boolean mandatory) {return frame(OWNER,73,date,rev,rev,"snapshot-"+rev,wars,mandatory);}
private static Army army(int id,int province,boolean own,boolean combat,boolean siege,int destination) {return new Army(id,province,own,combat,siege,false,destination,List.of());}
private static List<War> battle(int war) {return List.of(new War(war,List.of(army(0,11,true,true,false,0)),List.of()));}
private static Optional<Decision> observe(AutoCameraPolicy policy,Frame frame,long seconds) {return policy.observe(frame,LAND,NOW.plusSeconds(seconds),Optional.empty());}
private static PresentationIntent.Scope scope() {return new PresentationIntent.Scope("7",9,DAY,DAY+24,List.of(new PresentationRequest.Province(11,"b_first")));}
@Test void priorityUsesCurrentLandObservationAndKeepsPublicCunitZero() {
 Army zero=army(0,11,true,true,false,0),hostileBattle=army(2,21,false,true,false,0),ownSiege=army(3,31,true,false,true,0),hostileSiege=army(4,41,false,false,true,0);
 Frame priority=frame(DAY,1,List.of(new War(8,List.of(zero,hostileBattle,ownSiege,hostileSiege),List.of(new Objective(51,true)))),false);
 assertEquals(0,AutoCameraModel.hotspot(priority,LAND).orElseThrow().army());
 Frame f=frame(DAY,1,List.of(new War(8,List.of(zero),List.of())),false);
 Decision d=observe(new AutoCameraPolicy(),f,0).orElseThrow();
 assertEquals(HOTSPOT,d.mode());assertEquals("b_first",d.title());assertEquals("8:0:11:battle",d.target());
 Army sea=army(0,99,true,true,false,0);
 Frame onlySea=frame(DAY,1,List.of(new War(8,List.of(sea),List.of(new Objective(99,true)))),false);
 assertTrue(AutoCameraModel.hotspot(onlySea,LAND).isEmpty());assertTrue(observe(new AutoCameraPolicy(),onlySea,0).isEmpty());
 Frame mixed=frame(DAY,1,List.of(new War(8,List.of(sea,hostileBattle),List.of())),false);
 assertEquals(21,AutoCameraModel.hotspot(mixed,LAND).orElseThrow().province());
 Frame moving=frame(DAY,1,List.of(new War(8,List.of(army(0,11,true,false,false,21)),List.of(new Objective(31,false)))),false);
 assertEquals("moving_player_army",AutoCameraModel.hotspot(moving,LAND).orElseThrow().reason());
}
@Test void realmRequiresTenQuietSecondsFreshMarkerAndThirtyDayRefresh() {
 AutoCameraPolicy policy=new AutoCameraPolicy();Frame start=frame(DAY,1,List.of(),false);
 assertTrue(observe(policy,start,0).isEmpty());assertTrue(observe(policy,start,10).isEmpty());
 Frame fresh=frame(DAY,2,List.of(),false);Decision first=observe(policy,fresh,10).orElseThrow();
 assertEquals(REALM,first.mode());policy.queued(fresh,first);
 assertTrue(observe(policy,frame(DAY+719,3,List.of(),false),11).isEmpty());
 assertEquals(REALM,observe(policy,frame(DAY+720,4,List.of(),false),12).orElseThrow().mode());
}
@Test void ownerClockDateAndEachRevisionRollbackRestartQuietPeriod() {
 List<Frame> resets=List.of(
  frame(OWNER,73,DAY-1,11,11,"date-back",List.of(),false),
  frame(OWNER,73,DAY,9,11,"public-back",List.of(),false),
  frame(OWNER,73,DAY,11,9,"native-back",List.of(),false),
  frame(owner(43,"9007199254740993","episode"),73,DAY,11,11,"pid",List.of(),false),
  frame(owner(42,"9007199254740994","episode"),73,DAY,11,11,"birth",List.of(),false),
  frame(owner(42,"9007199254740993","next-episode"),73,DAY,11,11,"episode",List.of(),false),
  frame(OWNER,74,DAY,11,11,"actor",List.of(),false));
 for(Frame reset:resets) {
  AutoCameraPolicy policy=new AutoCameraPolicy();
  assertTrue(observe(policy,frame(OWNER,73,DAY,10,10,"baseline",List.of(),false),0).isEmpty());
  assertTrue(observe(policy,reset,10).isEmpty(),reset.toString());
  Frame next=frame(reset.owner(),reset.source().actor(),reset.source().dateRaw()+1,12,12,"after-reset",List.of(),false);
  assertTrue(observe(policy,next,19).isEmpty());
  Frame ready=frame(reset.owner(),reset.source().actor(),reset.source().dateRaw()+2,13,13,"ready",List.of(),false);
  assertEquals(REALM,observe(policy,ready,20).orElseThrow().mode());
 }
 AutoCameraPolicy clock=new AutoCameraPolicy();
 assertTrue(observe(clock,frame(DAY,1,List.of(),false),10).isEmpty());
 assertTrue(observe(clock,frame(DAY,2,List.of(),false),9).isEmpty());
 assertTrue(observe(clock,frame(DAY,3,List.of(),false),18).isEmpty());
 assertEquals(REALM,observe(clock,frame(DAY,4,List.of(),false),19).orElseThrow().mode());
}
@Test void sameBaronyNewWarCanFollowNextDayWhileSameTargetStaysSuppressed() {
 AutoCameraPolicy policy=new AutoCameraPolicy();Frame first=frame(DAY,1,battle(7),false);
 Decision old=observe(policy,first,0).orElseThrow();policy.queued(first,old);
 assertTrue(observe(policy,frame(DAY+24,2,battle(7),false),1).isEmpty());
 Decision next=observe(policy,frame(DAY+24,3,battle(8),false),2).orElseThrow();
 assertEquals(old.title(),next.title());assertNotEquals(old.target(),next.target());
}
@Test void failedTargetBackoffUsesActualDateAndMandatoryCancelBypassesIt() {
 AutoCameraPolicy policy=new AutoCameraPolicy();Frame first=frame(DAY,1,battle(7),false);
 Decision d=observe(policy,first,0).orElseThrow();policy.queued(first,d);policy.failed(first,d,DAY+2);
 assertEquals(1,policy.backoffs());assertTrue(observe(policy,frame(DAY+721,2,battle(7),false),1).isEmpty());
 Frame mandatory=frame(DAY+721,3,battle(7),true);Decision cancel=observe(policy,mandatory,2).orElseThrow();
 assertEquals(CANCEL,cancel.mode());policy.queued(mandatory,cancel);
 assertTrue(observe(policy,frame(DAY+721,4,battle(7),true),3).isEmpty());
 assertEquals(HOTSPOT,observe(policy,frame(DAY+722,5,battle(7),false),4).orElseThrow().mode());assertEquals(0,policy.backoffs());
}
@Test void firstPreAdvanceTrackedQueueStillCancelsAtMandatorySuccessor() {
 AutoCameraPolicy policy=new AutoCameraPolicy();Frame first=frame(DAY,1,List.of(),false);
 Decision tracking=new Decision(TRACKED_HOTSPOT,"","validated_armed_tactical_scope",Optional.of(scope()));
 policy.queued(first,tracking);assertEquals(CANCEL,observe(policy,frame(DAY+1,2,List.of(),true),1).orElseThrow().mode());
}
@Test void observedTrackingFailureRetainsPossibleActiveCameraUntilCancel() {
 AutoCameraPolicy policy=new AutoCameraPolicy();Frame first=frame(DAY,1,List.of(),false);
 Decision tracking=policy.observe(first,LAND,NOW,Optional.of(scope())).orElseThrow();assertEquals(TRACKED_HOTSPOT,tracking.mode());
 policy.queued(first,tracking);policy.failed(first,tracking);
 assertEquals(CANCEL,observe(policy,frame(DAY+1,2,List.of(),true),1).orElseThrow().mode());
}
}
