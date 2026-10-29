package org.xar.ck3.control.application.presentation;

import java.time.Duration;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import static org.xar.ck3.control.contracts.StrictJson.require;
import org.xar.ck3.control.contracts.presentation.*;
import static org.xar.ck3.control.application.presentation.AutoCameraModel.*;

/** Original quiet/fresh-frame policy and bounded target backoff; no Native or writer authority. */
public final class AutoCameraPolicy {
 private Frame last;private Instant quiet,lastClock;private Integer realmDate;
 private String mode="idle",title="",lastTarget="";private boolean mayHaveActive;private int lastSentDate;
 private final LinkedHashMap<String,Integer> retries=new LinkedHashMap<>();
 public synchronized Optional<Decision> observe(Frame frame,Map<Integer,String> land,Instant now,Optional<PresentationIntent.Scope> tracking){
  Objects.requireNonNull(now);Objects.requireNonNull(tracking);
  boolean reset=last==null||!frame.follows(last)||lastClock!=null&&now.isBefore(lastClock);
  if(reset){quiet=null;realmDate=null;mode="idle";title="";mayHaveActive=false;retries.clear();lastTarget="";}
  boolean fresh=last==null||reset||!last.marker().equals(frame.marker());last=frame;lastClock=now;
  if(!frame.alive()||!frame.mapReady()||frame.mandatory()){quiet=null;realmDate=null;boolean cancel=mayHaveActive||!mode.equals("idle");mode="idle";mayHaveActive=false;
   return cancel?Optional.of(new Decision(PresentationRequest.Mode.CANCEL,"","mandatory_choice",Optional.empty())):Optional.empty();}
  if(tracking.isPresent()){mode="tracking";mayHaveActive=true;return Optional.of(new Decision(PresentationRequest.Mode.TRACKED_HOTSPOT,"","validated_armed_tactical_scope",tracking));}
  Optional<Hotspot> hotspot=AutoCameraModel.hotspot(frame,land);
  Decision desired=null;boolean changed=false;
  if(hotspot.isPresent()&&Set.of("battle","siege","objective_siege","moving_player_army","army_destination").contains(hotspot.orElseThrow().reason())){
   var h=hotspot.orElseThrow();quiet=null;realmDate=null;changed=!mode.equals("hotspot")||!title.equals(h.title());
   mode="hotspot";title=h.title();desired=new Decision(PresentationRequest.Mode.HOTSPOT,title,h.reason(),Optional.empty(),h.war()+":"+h.army()+":"+h.province()+":"+h.reason());
  }else{
   if(quiet==null){if(!fresh)return Optional.empty();quiet=now;}
   if(Duration.between(quiet,now).compareTo(Duration.ofSeconds(10))<0||!fresh)return Optional.empty();
   if(realmDate!=null&&frame.source().dateRaw()-realmDate<30*24)return Optional.empty();
   mode="realm";realmDate=frame.source().dateRaw();changed=true;desired=new Decision(PresentationRequest.Mode.REALM,"","no_hotspot_realm_overview",Optional.empty());
  }
  String key=key(frame,desired);Integer retry=retries.get(key);
  if(retry!=null&&frame.source().dateRaw()<retry)return Optional.empty();
  if(!changed&&key.equals(lastTarget)&&frame.source().dateRaw()<lastSentDate+30*24&&retry==null)return Optional.empty();
  retries.remove(key);lastTarget=key;lastSentDate=frame.source().dateRaw();return Optional.of(desired);
 }
 public synchronized void queued(Frame frame,Decision decision){last=Objects.requireNonNull(frame);if(decision.mode()==PresentationRequest.Mode.CANCEL){mayHaveActive=false;mode="idle";}
  else if(decision.mode()!=PresentationRequest.Mode.QUERY)mayHaveActive=true;}
 public synchronized void failed(Frame frame,Decision decision){failed(frame,decision,frame.source().dateRaw());}
 public synchronized void failed(Frame frame,Decision decision,int actualDate){
  if(decision.mode()==PresentationRequest.Mode.CANCEL)return;
  String key=key(frame,decision);retries.remove(key);retries.put(key,Math.addExact(actualDate,720));
  while(retries.size()>16)retries.remove(retries.keySet().iterator().next());
  realmDate=null;mode="idle";title="";
 }
 private static String key(Frame f,Decision d){return f.owner()+":"+f.source().actor()+":"+d.mode()+":"+d.title()+":"+d.target();}
 public synchronized int backoffs(){return retries.size();}
 /** Armed Status and watch IDs must be from this parent's actual original ACK, never a requested generation. */
 public static Optional<PresentationIntent.Scope> tracking(Frame frame,List<ActionReceipt> history,ActionReceipt parent,Map<Integer,String> land){
  var children=ActionTransitions.composite(parent.state()).orElseThrow().children();
  for(ActionReceipt child:history){
   String step=child.command().operation().value();
   if(!step.startsWith("research-arm-tactical-daily-sentinel-v1-")||children.stream().noneMatch(c->c.actionId().equals(child.command().actionId()))
      ||child.outcome()!=ActionReceipt.Outcome.APPLIED_CONFIRMED)continue;
   var dispatch=ActionTransitions.dispatch(child.state());
   if(dispatch.isEmpty()||!(dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack))continue;
   var status=AdvancePrimitives.acknowledgedSentinel(ack,step);var spec=AdvancePrimitives.armSpec(step);
   if(!status.state().name().equals("ARMED")||status.startingDateRaw()!=frame.source().dateRaw()||status.targetDateRaw()<=status.startingDateRaw()
      ||(long)status.targetDateRaw()-status.startingDateRaw()>720)return Optional.empty();
   Map<Integer,Army> candidates=new TreeMap<>();
   for(War war:frame.wars())for(Army a:war.armies())if(spec.armyIds().contains(a.id())&&a.id()>0&&a.own()&&!a.retreat()){
    Army old=candidates.putIfAbsent(a.id(),a);if(old!=null&&!old.equals(a))return Optional.empty();}
   var selected=candidates.values().stream().min(Comparator.comparing(Army::combat).reversed().thenComparingInt(Army::id));
   if(selected.isEmpty())return Optional.empty();Army a=selected.orElseThrow();
   if(a.route().size()>32||a.province()<=0)return Optional.empty();var ids=new TreeSet<Integer>(a.route());ids.add(a.province());if(a.destination()>0)ids.add(a.destination());
   if(ids.size()>32||ids.stream().anyMatch(p->!land.containsKey(p)))return Optional.empty();
   return Optional.of(new PresentationIntent.Scope(status.generation().decimal(),a.id(),status.startingDateRaw(),status.targetDateRaw(),
    ids.stream().map(p->new PresentationRequest.Province(p,land.get(p))).toList()));
  }return Optional.empty();
 }
}
