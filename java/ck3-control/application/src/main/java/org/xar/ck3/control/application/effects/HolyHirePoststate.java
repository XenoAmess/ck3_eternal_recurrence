package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;


public final class HolyHirePoststate {
  public static final String SCHEMA = "xar.java.holy-hire-poststate/v1";
  private HolyHirePoststate() { }
  public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE, NOT_REQUESTED }
  public enum Presence { VALUE, NULL, UNAVAILABLE }
  public enum QuoteMatch { MATCH, MISMATCH, UNAVAILABLE }
  public record Sources(ExactRef model, ExactRef collector) {
      public Sources { Objects.requireNonNull(model); Objects.requireNonNull(collector); StrictJson.require(model.bytes()>0&&collector.bytes()>0,"holy sources required"); }
  }
  public record Scope(String actionId, String requestId, BigInteger holyOrderId, BigInteger actorId,
      String episodeRunId, String beforeSnapshotId, String afterSnapshotId, BigInteger publicRevision,
      BigInteger nativeRevision, BigInteger beforeDateRaw, BigInteger afterDateRaw, String fullBindingSha256) {
      public Scope {
      for(String value:List.of(actionId,requestId,episodeRunId,beforeSnapshotId,afterSnapshotId)) StrictJson.text(value);
      id(holyOrderId); id(actorId); Objects.requireNonNull(publicRevision); Objects.requireNonNull(nativeRevision);
      Objects.requireNonNull(beforeDateRaw); Objects.requireNonNull(afterDateRaw);
      StrictJson.require(fullBindingSha256!=null&&fullBindingSha256.matches("[0-9a-f]{64}"),"holy after binding required");
      }
      public static Scope of(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair, long order) {
      var before=pair.before().identity().frame(); var after=pair.after().identity().frame();
      StrictJson.require(command.before().equals(pair.before().identity()),"holy before frame differs");
      return new Scope(command.actionId(),attempt.requestId(),BigInteger.valueOf(order),after.identity().player(),
          after.episodeRunId(),before.snapshotId(),after.snapshotId(),after.revision(),after.identity().nativeRevision(),
          before.identity().dateRaw(),after.identity().dateRaw(),pair.after().fullBindingSha256());
      }
  }
  public record Quantity(Presence presence, Optional<BigInteger> value) {
      public Quantity { Objects.requireNonNull(presence); Objects.requireNonNull(value); StrictJson.require((presence==Presence.VALUE)==value.isPresent(),"quantity presence/value differ"); }
      public static Quantity value(BigInteger value) { return new Quantity(Presence.VALUE,Optional.of(value)); }
      public static Quantity knownNull() { return new Quantity(Presence.NULL,Optional.empty()); }
      public static Quantity unavailable() { return new Quantity(Presence.UNAVAILABLE,Optional.empty()); }
  }
  public record Stocks(Quantity gold, Quantity prestige, Quantity piety) {
      public Stocks { Objects.requireNonNull(gold); Objects.requireNonNull(prestige); Objects.requireNonNull(piety); }
  }
  public record Wallet(Stocks before, Stocks after, Stocks delta, QuoteMatch quoteMatch) {
      public Wallet { Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(delta); Objects.requireNonNull(quoteMatch); }
  }
  public record Member(BigInteger regimentId, boolean available, boolean regimentResolved, boolean nativeArmyResolved,
      Optional<BigInteger> nativeArmyId, boolean combatResolved, Optional<BigInteger> combatId) {
      public Member { id(regimentId); Objects.requireNonNull(nativeArmyId); Objects.requireNonNull(combatId); nativeArmyId.ifPresent(HolyHirePoststate::id); combatId.ifPresent(HolyHirePoststate::id); }
  }
  public record Association(Status status, List<Member> members, Optional<String> reason) {
      public Association { Objects.requireNonNull(status); members=List.copyOf(members); reason=HolyHirePoststate.reason(status,reason); StrictJson.require(status==Status.AVAILABLE||status==Status.PARTIAL||members.isEmpty(),"unavailable association has members"); }
  }
  
  public record Strength(BigInteger armyId, Optional<BigInteger> nativeArmyId, Quantity soldiers,
      boolean controllable, Optional<BigInteger> ownerId, Optional<BigInteger> provinceId) {
      public Strength { publicId(armyId); Objects.requireNonNull(nativeArmyId); nativeArmyId.ifPresent(HolyHirePoststate::id); Objects.requireNonNull(soldiers); Objects.requireNonNull(ownerId); Objects.requireNonNull(provinceId); }
  }
  public record MaterialArmy(BigInteger armyId, BigInteger nativeArmyId, BigInteger currentSoldiers,
      Optional<BigInteger> ownerId, Optional<BigInteger> provinceId) {
      public MaterialArmy { publicId(armyId); id(nativeArmyId); positive(currentSoldiers); Objects.requireNonNull(ownerId); Objects.requireNonNull(provinceId); }
  }
  public record Troops(Association association, Status strengthStatus, List<MaterialArmy> materialArmies, Optional<String> reason) {
      public Troops { Objects.requireNonNull(association); Objects.requireNonNull(strengthStatus); materialArmies=List.copyOf(materialArmies); reason=HolyHirePoststate.reason(strengthStatus,reason); StrictJson.require(((association.status()==Status.AVAILABLE||association.status()==Status.PARTIAL)&&strengthStatus==Status.AVAILABLE)||materialArmies.isEmpty(),"unobserved troops gained availability"); }
      public boolean usableArmyObserved() { return !materialArmies.isEmpty(); }
  }
  public record Expenses(Status status, Quantity currentMilitaryGoldRaw, Quantity allRaisedMilitaryGoldRaw,
      Quantity monthlyNetIncomeRaw, Optional<String> reason) {
      public Expenses { Objects.requireNonNull(status); Objects.requireNonNull(currentMilitaryGoldRaw); Objects.requireNonNull(allRaisedMilitaryGoldRaw); Objects.requireNonNull(monthlyNetIncomeRaw); reason=HolyHirePoststate.reason(status,reason); }
      public static Expenses unavailable(String reason) { return new Expenses(Status.UNAVAILABLE,Quantity.unavailable(),Quantity.unavailable(),Quantity.unavailable(),Optional.of(reason)); }
  }
  public record Report(Scope scope, Wallet wallet, Troops troops, Expenses expenses) {
      public Report { Objects.requireNonNull(scope); Objects.requireNonNull(wallet); Objects.requireNonNull(troops); Objects.requireNonNull(expenses); }
  }
  public record Supplement(Report report, ExactRef originalMaterial) {
      public Supplement { Objects.requireNonNull(report); Objects.requireNonNull(originalMaterial); }
  }
  public interface Port {
      Supplement collect(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair, ArmyWarWindowReads.HolyHire selected, JsonNode beforeHolyContext, JsonNode afterHolyContext);
      Supplement replay(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair, ArmyWarWindowReads.HolyHire selected, JsonNode beforeHolyContext, JsonNode afterHolyContext, ExactRef original, ActionPorts.OutcomeArchive archive);
  }
  private static Optional<String> reason(Status status, Optional<String> reason) {
      Objects.requireNonNull(reason); reason.ifPresent(StrictJson::text);
      StrictJson.require((status==Status.AVAILABLE)==reason.isEmpty(),"read status/reason differ"); return reason;
  }
  public static Wallet wallet(Scope scope, Stocks before, Stocks after, List<BigInteger> quote) {
      StrictJson.require(quote.size()==10,"ten original quoted resources required");
      Stocks delta=new Stocks(delta(before.gold(),after.gold()),delta(before.prestige(),after.prestige()),delta(before.piety(),after.piety()));
      QuoteMatch match=QuoteMatch.UNAVAILABLE;
      if(scope.beforeDateRaw().equals(scope.afterDateRaw())&&quote.subList(3,10).stream().allMatch(value->value.signum()==0)
          &&List.of(delta.gold(),delta.prestige(),delta.piety()).stream().allMatch(value->value.presence()==Presence.VALUE))
      match=delta.gold().value().orElseThrow().equals(quote.get(0))&&delta.prestige().value().orElseThrow().equals(quote.get(1))
          &&delta.piety().value().orElseThrow().equals(quote.get(2))?QuoteMatch.MATCH:QuoteMatch.MISMATCH;
      return new Wallet(before,after,delta,match);
  }
  private static Quantity delta(Quantity before, Quantity after) {
      return before.presence()==Presence.VALUE&&after.presence()==Presence.VALUE?Quantity.value(before.value().orElseThrow().subtract(after.value().orElseThrow())):Quantity.unavailable();
  }
  public static Troops troops(Association association, Status status, List<Strength> strengths, Optional<String> reason) {
      Set<BigInteger> refs=association.members().stream().filter(member->member.available()&&member.nativeArmyResolved()&&member.nativeArmyId().isPresent())
          .map(member->member.nativeArmyId().orElseThrow()).collect(java.util.stream.Collectors.toUnmodifiableSet());
      List<MaterialArmy> armies=status==Status.AVAILABLE&&(association.status()==Status.AVAILABLE||association.status()==Status.PARTIAL)?strengths.stream()
          .filter(row->row.controllable()&&row.nativeArmyId().filter(refs::contains).isPresent()&&row.soldiers().value().filter(value->value.signum()>0).isPresent())
          .map(row->new MaterialArmy(row.armyId(),row.nativeArmyId().orElseThrow(),row.soldiers().value().orElseThrow(),row.ownerId(),row.provinceId())).toList():List.of();
      return new Troops(association,status,armies,reason);
  }
  public static RawJson encode(Report report) { return new RawJson(StrictJson.canonical(json(report))); }
  public static ObjectNode json(Report r) {
      ObjectNode out=StrictJson.object().put("schema",SCHEMA).put("raw_scale",BigInteger.valueOf(100000)).put("full_hire_loop_complete",false).put("automatic_retry",false).put("debit_attribution_observed",false);
      Scope s=r.scope(); ObjectNode scope=out.putObject("scope").put("action_id",s.actionId()).put("request_id",s.requestId()).put("holy_order_id",s.holyOrderId()).put("actor_id",s.actorId())
          .put("episode_run_id",s.episodeRunId()).put("before_snapshot_id",s.beforeSnapshotId()).put("after_snapshot_id",s.afterSnapshotId()).put("public_revision",s.publicRevision())
          .put("native_revision",s.nativeRevision()).put("before_date_raw",s.beforeDateRaw()).put("after_date_raw",s.afterDateRaw()).put("full_binding_sha256",s.fullBindingSha256());
      ObjectNode w=out.putObject("wallet");w.set("before",stocksJson(r.wallet().before()));w.set("after",stocksJson(r.wallet().after()));w.set("observed_stock_delta_raw",stocksJson(r.wallet().delta()));
      if(r.wallet().quoteMatch()==QuoteMatch.UNAVAILABLE)w.putNull("unchanged_date_quote_delta_match");else w.put("unchanged_date_quote_delta_match",r.wallet().quoteMatch()==QuoteMatch.MATCH);
      ObjectNode t=out.putObject("troops").put("strength_status",r.troops().strengthStatus().name()).put("usable_army_observed",r.troops().usableArmyObserved());nullable(t,"reason",r.troops().reason());
      ObjectNode a=t.putObject("association").put("status",r.troops().association().status().name());nullable(a,"reason",r.troops().association().reason());var members=a.putArray("members");
      for(Member m:r.troops().association().members()){ObjectNode n=members.addObject().put("regiment_id",m.regimentId()).put("available",m.available()).put("regiment_resolved",m.regimentResolved())
          .put("native_carmy_resolved",m.nativeArmyResolved()).put("combat_resolved",m.combatResolved());nullableNumber(n,"native_carmy_id",m.nativeArmyId());nullableNumber(n,"combat_id",m.combatId());}
      var armies=t.putArray("material_armies");for(MaterialArmy m:r.troops().materialArmies()){ObjectNode n=armies.addObject().put("army_id",m.armyId()).put("native_carmy_id",m.nativeArmyId()).put("current_soldiers",m.currentSoldiers()).put("controllable",true);nullableNumber(n,"owner_character_id",m.ownerId());nullableNumber(n,"current_province_id",m.provinceId());}
      Expenses e=r.expenses();ObjectNode expense=out.putObject("expenses").put("status",e.status().name());nullable(expense,"reason",e.reason());expense.set("current_military_gold_raw",quantityJson(e.currentMilitaryGoldRaw()));expense.set("all_raised_military_gold_raw",quantityJson(e.allRaisedMilitaryGoldRaw()));expense.set("monthly_net_income_raw",quantityJson(e.monthlyNetIncomeRaw()));
      return out;
  }
  private static ObjectNode stocksJson(Stocks s){ObjectNode n=StrictJson.object();n.set("gold",quantityJson(s.gold()));n.set("prestige",quantityJson(s.prestige()));n.set("piety",quantityJson(s.piety()));return n;}
  private static ObjectNode quantityJson(Quantity q){ObjectNode n=StrictJson.object().put("presence",q.presence().name());nullableNumber(n,"value",q.value());return n;}
  private static void nullable(ObjectNode n,String key,Optional<String> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
  private static void nullableNumber(ObjectNode n,String key,Optional<BigInteger> value){if(value.isPresent())n.put(key,value.orElseThrow());else n.putNull(key);}
  private static void id(BigInteger value){StrictJson.require(value!=null&&value.signum()>=0&&value.compareTo(new BigInteger("4294967295"))<0,"native identity required");}
  private static void publicId(BigInteger value){StrictJson.require(value!=null&&value.signum()>=0&&value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"public CUnit identity required");}
  private static void positive(BigInteger value){StrictJson.require(value!=null&&value.signum()>0,"positive exact quantity required");}
}
