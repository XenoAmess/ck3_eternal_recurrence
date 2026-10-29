package org.xar.ck3.control.application.presentation;

import java.util.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** A copy of one actual semantic frame; constructing it performs no Native read. */
public final class AutoCameraModel {
 private AutoCameraModel(){}
 public record Army(int id,int province,boolean own,boolean combat,boolean siege,boolean retreat,int destination,List<Integer> route){
  public Army{StrictJson.require(id>=0&&province>=0&&destination>=0,"actual army/province IDs required");route=List.copyOf(route);}
 }
 public record Objective(int province,boolean siege){}
 public record War(int id,List<Army> armies,List<Objective> objectives){
  public War{StrictJson.require(id>0,"positive war ID required");armies=List.copyOf(armies);objectives=List.copyOf(objectives);}
 }
 public record Frame(PresentationRequest.Owner owner,PresentationRequest.Frame source,boolean paused,boolean alive,
   boolean mapReady,boolean mandatory,List<War> wars){
  public Frame{Objects.requireNonNull(owner);Objects.requireNonNull(source);wars=List.copyOf(wars);}
  public String marker(){return source.snapshotId()+":"+source.revision()+":"+source.nativeRevision()+":"+source.dateRaw();}
  public boolean sameOwner(Frame other){return owner.equals(other.owner)&&source.actor()==other.source.actor();}
  public boolean follows(Frame old){return sameOwner(old)&&source.dateRaw()>=old.source.dateRaw()
    &&new java.math.BigInteger(source.revision()).compareTo(new java.math.BigInteger(old.source.revision()))>=0
    &&new java.math.BigInteger(source.nativeRevision()).compareTo(new java.math.BigInteger(old.source.nativeRevision()))>=0;}
 }
 public record Hotspot(int priority,int war,int army,int province,String title,String reason){}
 public record Decision(PresentationRequest.Mode mode,String title,String reason,Optional<PresentationIntent.Scope> tracking,String target){
  public Decision(PresentationRequest.Mode mode,String title,String reason,Optional<PresentationIntent.Scope> tracking){this(mode,title,reason,tracking,"");}
  public Decision{Objects.requireNonNull(mode);Objects.requireNonNull(title);StrictJson.text(reason);Objects.requireNonNull(tracking);Objects.requireNonNull(target);StrictJson.require(target.length()<=256,"bounded observed target identity required");}
 }
 public static Frame copy(DriverObservationAssembler.Complete actual,PresentationRequest.Owner owner){
  var id=actual.identity();var f=id.frame();var n=actual.semantic();
  StrictJson.require(owner.machineId().equals(id.machineId())&&owner.sessionId().equals(actual.sessionId())
   &&owner.processId()==id.game().pid()&&owner.processBirthFiletime().equals(id.game().creationFiletime().value().toString())
   &&owner.connectionGeneration().equals(actual.connectionGeneration().toString())&&owner.episodeRunId().equals(f.episodeRunId()),"camera frame crossed actual owner");
  Obj player=object(n.get("played_character"),"played_character");
  StrictJson.require(integer(player.get("character_id"),"character_id").equals(f.identity().player()),"camera actor differs");
  List<War> wars=new ArrayList<>();
  for(Value w:rows(n.get("active_wars"))){Obj war=object(w,"war");List<Army> armies=new ArrayList<>();List<Objective> objectives=new ArrayList<>();
   for(Value v:rows(war.get("allied_armies"))){Obj a=object(v,"army");String state=a.get("army_state") instanceof Text t?t.value():"";
    armies.add(new Army(nonnegative(a.get("army_id")),positiveOrZero(a.get("current_province_id")),yes(a.get("controllable")),yes(a.get("in_combat")),
      Set.of("siege","sieging").contains(state)||present(a.get("siege_days_left")),yes(a.get("retreating")),positiveOrZero(a.get("move_target_province_id")),
      rows(a.get("route_province_ids")).stream().map(v0->{int p=integer(v0,"route province").intValueExact();StrictJson.require(p>0,"complete positive route required");return p;}).toList()));}
   for(Value v:rows(war.get("objective_province_states"))){Obj a=object(v,"objective");int p=positiveOrZero(a.get("province_id"));if(p>0)objectives.add(new Objective(p,present(a.get("active_siege"))));}
   for(Value v:rows(war.get("war_objective_province_ids"))){int p=positiveOrZero(v);if(p>0)objectives.add(new Objective(p,false));}
   int wid=positiveOrZero(war.get("war_id"));wars.add(new War(wid>0?wid:Integer.MAX_VALUE,armies,objectives));}
  boolean mandatory=yes(n.get("mandatory_choice"))||present(n.get("active_event"))||present(n.get("pending_character_interaction"));
  Value hint=n.get("top_exclusive_modal_choice_hint");if(hint instanceof Obj h)mandatory|=new Text("present").equals(h.get("status"));
  Value activity=n.get("player_activity");if(activity instanceof Obj a)mandatory|=yes(a.get("mandatory_choice"));
  return new Frame(owner,new PresentationRequest.Frame(f.snapshotId(),f.revision().toString(),f.identity().nativeRevision().toString(),
   f.identity().player().intValueExact(),f.identity().dateRaw().intValueExact()),yes(n.get("paused")),yes(player.get("alive")),yes(n.get("map_ready")),mandatory,wars);
 }
 public static Optional<Hotspot> hotspot(Frame frame,Map<Integer,String> land){
  List<Hotspot> all=new ArrayList<>();
  for(War w:frame.wars()){
   for(Army a:w.armies()){
    if(a.combat())add(all,land,a.own()?0:1,w.id(),a.id(),a.province(),"battle");
    else if(a.siege())add(all,land,a.own()?2:3,w.id(),a.id(),a.province(),"siege");
    if(a.own()&&!a.retreat()){if(a.destination()>0){add(all,land,5,w.id(),a.id(),a.province(),"moving_player_army");add(all,land,6,w.id(),a.id(),a.destination(),"army_destination");}
     else add(all,land,8,w.id(),a.id(),a.province(),"player_army");}}
   for(Objective o:w.objectives()){if(o.siege())add(all,land,4,w.id(),-1,o.province(),"objective_siege");add(all,land,7,w.id(),-1,o.province(),"war_objective");}}
  return all.stream().min(Comparator.comparingInt(Hotspot::priority).thenComparingInt(Hotspot::war)
   .thenComparingInt(h->h.army()<0?Integer.MAX_VALUE:h.army()).thenComparingInt(Hotspot::province).thenComparing(Hotspot::reason));
 }
 private static void add(List<Hotspot> all,Map<Integer,String> land,int priority,int war,int army,int province,String reason){
  String title=land.get(province);if(province>0&&title!=null)all.add(new Hotspot(priority,war,army,province,title,reason));
 }
 private static List<Value> rows(Value v){if(v==null||v==Nil.INSTANCE)return List.of();StrictJson.require(v instanceof Arr,"camera list required");return ((Arr)v).items();}
 private static boolean yes(Value v){return v instanceof Bool b&&b.value();}
 private static boolean present(Value v){return v!=null&&v!=Nil.INSTANCE;}
 private static int positiveOrZero(Value v){return v instanceof IntegerValue i&&i.value().signum()>0?i.value().intValueExact():0;}
 private static int nonnegative(Value v){int n=integer(v,"army_id").intValueExact();StrictJson.require(n>=0,"public CUnit zero is valid; negative is not");return n;}
}
