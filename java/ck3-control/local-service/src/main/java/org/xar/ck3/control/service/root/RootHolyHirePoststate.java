package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.effects.HolyHirePoststate.Scope;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import static org.xar.ck3.control.application.effects.HolyHirePoststate.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;


public final class RootHolyHirePoststate implements HolyHirePoststate.Port {
  private static final String ORIGINAL="xar.java.holy-hire-poststate-original/v1";
  private static final Set<String> FIELDS=Set.of("schema","model_source","collector_source","strengths_read","cash_read","hello_packet_base64","strengths_status","strengths_reason","cash_reason","report");
  interface RuntimeAccess {
      void requireFrame(Complete frame, Instant deadline) throws IOException;
      ActionPorts.OutcomeArchive archive();
      PlanningReadPort reads();
      RootReadContractCatalog catalog();
      ArmyStrengthsContracts strengths();
      NativeWire.Hello hello() throws IOException;
      ReadContract<FinanceReadContracts.Packet> cash();
  }
  private final Sources sources;
  private final RuntimeAccess runtime;
  public RootHolyHirePoststate(RootRuntimeContext context,Sources sources) {
      this(sources,new RuntimeAccess() {
      @Override public void requireFrame(Complete frame,Instant deadline)throws IOException {
          context.requireCurrent(deadline);context.writer().requireSession(context.borrowedSession());
          StrictJson.require(frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())
              &&frame.identity().game().equals(context.game().generation())&&frame.identity().machineId().equals(context.game().machineId()),"holy poststate Game/source/session differs");
      }
      @Override public ActionPorts.OutcomeArchive archive(){return context.archive();}
      @Override public PlanningReadPort reads(){return context.reads();}
      @Override public RootReadContractCatalog catalog(){return context.readCatalog();}
      @Override public ArmyStrengthsContracts strengths(){return context.remainingDomains().strengths().contracts();}
      @Override public NativeWire.Hello hello()throws IOException{return context.transport().originalHello();}
      @Override public ReadContract<FinanceReadContracts.Packet> cash(){return context.finance().definitions().contract(FinanceReadContracts.Query.CASH);}
      });
  }
  RootHolyHirePoststate(Sources sources,RuntimeAccess runtime){this.sources=Objects.requireNonNull(sources);this.runtime=Objects.requireNonNull(runtime);}
  private record Originals(Optional<PlanningReadReceipt> strengths,Optional<PlanningReadReceipt> cash,
      Optional<NativeWire.Hello> hello,Status strengthStatus,Optional<String> strengthReason,Optional<String> cashReason) {
      private Originals {
      Objects.requireNonNull(strengths);Objects.requireNonNull(cash);Objects.requireNonNull(hello);Objects.requireNonNull(strengthStatus);Objects.requireNonNull(strengthReason);Objects.requireNonNull(cashReason);
      StrictJson.require((strengthStatus==Status.AVAILABLE)==strengths.isPresent()&&strengths.isPresent()==hello.isPresent()
          &&strengths.isPresent()==strengthReason.isEmpty()&&cash.isPresent()==cashReason.isEmpty(),"holy original read disposition differs");
      }
  }
  @Override public Supplement collect(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,ArmyWarWindowReads.HolyHire selected,JsonNode beforeContext,JsonNode context) {
      Scope scope=Scope.of(command,attempt,pair,selected.holyOrderId());
      Originals originals;
      if(ActionReconciliationScope.activeFor(command))
      originals=new Originals(Optional.empty(),Optional.empty(),Optional.empty(),Status.NOT_REQUESTED,
          Optional.of("supplementary reconciliation not admitted"),Optional.of("supplementary reconciliation not admitted"));
      else originals=collectOriginals(command,pair,selected,association(context,scope));
      Report report=project(command,attempt,pair,selected,beforeContext,context,originals,false,runtime.archive());
      RawJson material=encodeOriginal(originals,report,runtime.archive());
      ExactRef preserved=runtime.archive().preserveMaterial(material);
      StrictJson.require(material.equals(runtime.archive().loadMaterial(preserved)),"holy supplement archive changed");
      return new Supplement(report,preserved);
  }
  private Originals collectOriginals(ActionCommand command,NativeEffectSnapshots.Pair pair,ArmyWarWindowReads.HolyHire selected,Association association) {
      var after=pair.after();Instant deadline=ActionObservationWindow.deadline(command);
      Optional<PlanningReadReceipt> strength=Optional.empty(),cash=Optional.empty();Optional<NativeWire.Hello> hello=Optional.empty();
      Status status=Status.NOT_REQUESTED;Optional<String> strengthReason=Optional.of("no resolved associated troops or public armies");Optional<String> cashReason=Optional.of("current military expenses unavailable");
      List<PublicUnitId> ids=publicArmies(after).stream().map(army->new PublicUnitId(army.armyId().intValueExact())).toList();
      if((association.status()==Status.AVAILABLE||association.status()==Status.PARTIAL)&&association.members().stream().anyMatch(member->member.available()&&member.nativeArmyResolved()&&member.nativeArmyId().isPresent())&&!ids.isEmpty()) {
      status=Status.UNAVAILABLE;
      try {
          runtime.requireFrame(after,deadline);NativeWire.Hello original=runtime.hello();
          var input=selection(after,deadline,original,ids);var contract=runtime.strengths().issue(runtime.catalog(),input);
          var read=runtime.reads().read(contract,runtime.strengths().request(input));
          if(read instanceof PlanningReadResult.Known<ArmyStrengths.Read> known) {
          requireRead(after,selected,deadline,known.receipt());strength=Optional.of(known.receipt());hello=Optional.of(original);status=Status.AVAILABLE;strengthReason=Optional.empty();
          } else strengthReason=Optional.of(((PlanningReadResult.Unavailable<ArmyStrengths.Read>)read).reason());
      } catch(IOException|RuntimeException failure) {strengthReason=Optional.of(diagnostic("army strength",failure));}
      }
      try {
      runtime.requireFrame(after,deadline);var contract=runtime.cash();
      var request=new PlanningReadRequest(after.identity(),after.source(),after.sessionId(),contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),deadline);
      var read=runtime.reads().read(contract,request);
      if(read instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known) {
          requireRead(after,selected,deadline,known.receipt());cash=Optional.of(known.receipt());cashReason=Optional.empty();
      } else cashReason=Optional.of(((PlanningReadResult.Unavailable<FinanceReadContracts.Packet>)read).reason());
      } catch(IOException|RuntimeException failure) {cashReason=Optional.of(diagnostic("military expenses",failure));}
      return new Originals(strength,cash,hello,status,strengthReason,cashReason);
  }
  @Override public Supplement replay(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,ArmyWarWindowReads.HolyHire selected,JsonNode beforeContext,JsonNode context,ExactRef original,ActionPorts.OutcomeArchive archive) {
      RawJson bytes=archive.loadMaterial(original);StrictJson.require(original.bytes()==bytes.bytes().length&&original.sha256().equals(ActionCodec.sha256(bytes.bytes())),"archived original bytes/SHA changed");
      ObjectNode row=StrictJson.object(StrictJson.parse(bytes.bytes(),StrictJson.EXPLICIT_MAX_BYTES),FIELDS);
      StrictJson.require(ORIGINAL.equals(StrictJson.text(row.get("schema")))&&sources.model().equals(ExactRef.fromJson(row.get("model_source")))
          &&sources.collector().equals(ExactRef.fromJson(row.get("collector_source"))),"holy supplement source differs");
      Optional<PlanningReadReceipt> strength=loadRead(row.get("strengths_read"),archive),cash=loadRead(row.get("cash_read"),archive);
      Optional<NativeWire.Hello> hello=Optional.empty();
      if(!row.get("hello_packet_base64").isNull()) {
      try {
          var frame=NativeWire.decode(Base64.getDecoder().decode(StrictJson.text(row.get("hello_packet_base64"))));
          StrictJson.require(frame instanceof NativeWire.Hello,"holy original HELLO required");hello=Optional.of((NativeWire.Hello)frame);
      } catch(IOException failure){throw new IllegalArgumentException("original holy strength HELLO rejected",failure);}
      }
      Originals originals=new Originals(strength,cash,hello,Status.valueOf(StrictJson.text(row.get("strengths_status"))),optionalText(row.get("strengths_reason")),optionalText(row.get("cash_reason")));
      Report report=project(command,attempt,pair,selected,beforeContext,context,originals,true,archive);
      StrictJson.require(HolyHirePoststate.json(report).equals(row.get("report")),"holy supplement replay differs");
      return new Supplement(report,original);
  }
  private Report project(ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,ArmyWarWindowReads.HolyHire selected,JsonNode beforeHoly,JsonNode holy,Originals originals,boolean archived,ActionPorts.OutcomeArchive archive) {
      Scope scope=Scope.of(command,attempt,pair,selected.holyOrderId());Association association=association(holy,scope);
      List<Strength> strengths=List.of();Status status=originals.strengthStatus();Optional<String> reason=originals.strengthReason();
      if(originals.strengths().isPresent()) {
      var read=originals.strengths().orElseThrow();requireRead(pair.after(),selected,read.request().deadline(),read);
      var ids=publicArmies(pair.after()).stream().map(army->new PublicUnitId(army.armyId().intValueExact())).toList();
      var selection=selection(pair.after(),read.request().deadline(),originals.hello().orElseThrow(),ids);
      var contract=runtime.strengths().issue(runtime.catalog(),selection);
      StrictJson.require(contract.contractId().equals(read.contractId())&&runtime.strengths().request(selection).equals(read.request()),"holy strength original contract/arguments differ");
      var decoded=archived?contract.replay(read):contract.decode(read);strengths=joinedStrengths(pair.after(),decoded);
      }
      Expenses expenses=Expenses.unavailable(originals.cashReason().orElse("current military expenses unavailable"));
      if(originals.cash().isPresent()) {
      var read=originals.cash().orElseThrow();requireRead(pair.after(),selected,read.request().deadline(),read);
      var contract=runtime.cash();StrictJson.require(contract.contractId().equals(read.contractId())&&contract.operation().equals(read.request().operation())&&read.request().arguments().members().isEmpty(),"holy cash original contract/arguments differ");
      var decoded=archived?contract.replay(read):contract.decode(read);
      try {
          JsonNode component=OpportunityJson.toNode(decoded.result()).get("war_cash_current_resources");
          StrictJson.require(component!=null,"current cash component missing");
          var normalized=RawCashCodec.normalize(StrictJson.canonical(component),OpportunityJson.encode(pair.after().semantic()));
          var metrics=normalized.metrics();
          expenses=new Expenses(Status.AVAILABLE,expense(metrics.currentMilitaryExpenses()),expense(metrics.allRaisedMilitaryExpenses()),fixed(metrics.monthlyNetIncome()),Optional.empty());
      } catch(IllegalArgumentException malformed) {
          expenses=Expenses.unavailable(diagnostic("military expense normalization",malformed));
      }
      }
      JsonNode beforeOrder=selectedOrder(beforeHoly,scope);
      List<BigInteger> quote=rows(beforeOrder.path("military_terms").get("resource_costs_raw")).stream().map(RootHolyHirePoststate::number).toList();
      return new Report(scope,HolyHirePoststate.wallet(scope,stocks(OpportunityJson.toNode(pair.before().semantic())),stocks(OpportunityJson.toNode(pair.after().semantic())),quote),HolyHirePoststate.troops(association,status,strengths,reason),expenses);
  }
  private static JsonNode selectedOrder(JsonNode context,Scope scope) {
    StrictJson.require(bool(context,"available")&&number(context.get("played_character_id")).equals(scope.actorId()),"holy quote actor differs");
    var matches=rows(context.get("rows")).stream().filter(row->number(row.get("holy_order_id")).equals(scope.holyOrderId())).toList();
    StrictJson.require(matches.size()==1,"one original selected holy quote required");return matches.getFirst();
  }
  private static ArmyStrengthsContracts.Selection selection(Complete frame,Instant deadline,NativeWire.Hello hello,List<PublicUnitId> ids) {
      var context=new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),deadline);
      var snapshot=ArmyStrengthsCodec.snapshot(context,new RawJson(OpportunityJson.encode(frame.semantic())));
      var query=new ArmyStrengths.Query(ArmyStrengths.Profile.ORDINARY_CORE_V1,ArmyStrengths.Mode.EXPLICIT_RICH,new Present<>(ids),ArmyStrengths.EntryMode.OBSERVED_PREPARED,ArmyStrengths.EntryMode.OBSERVED_PREPARED);
      return new ArmyStrengthsContracts.Selection(snapshot,query,hello,new Missing<>());
  }
  private record PublicArmy(BigInteger armyId,boolean controllable,Optional<BigInteger> ownerId,Optional<BigInteger> provinceId) { }
  private static List<PublicArmy> publicArmies(Complete frame) {
      List<PublicArmy> out=new ArrayList<>();JsonNode semantic=OpportunityJson.toNode(frame.semantic());
      for(JsonNode row:rows(semantic.get("player_armies")))out.add(new PublicArmy(number(row.get("army_id")),bool(row,"controllable"),optionalNumber(row.get("owner_character_id")),optionalNumber(row.get("current_province_id"))));
      return List.copyOf(out);
  }
  private static List<Strength> joinedStrengths(Complete frame,ArmyStrengths.Read read) {
      var publicRows=publicArmies(frame);List<Strength> out=new ArrayList<>();
      for(var row:read.rows()) {
      var core=row.core();BigInteger publicId=BigInteger.valueOf(core.army().value());
      var matches=publicRows.stream().filter(army->army.armyId().equals(publicId)).toList();StrictJson.require(matches.size()<=1,"duplicate public holy army identity");
      if(matches.isEmpty())continue;var army=matches.getFirst();
      Optional<BigInteger> nativeId=core.nativeArmy() instanceof Present<FullId> value?Optional.of(BigInteger.valueOf(Integer.toUnsignedLong(value.value().value()))):Optional.empty();
      Quantity soldiers=core.status()==ArmyStrengths.Status.AVAILABLE&&core.currentSoldiers() instanceof Present<Integer> value?Quantity.value(BigInteger.valueOf(value.value())):Quantity.unavailable();
      out.add(new Strength(publicId,nativeId,soldiers,army.controllable(),army.ownerId(),army.provinceId()));
      }
      return List.copyOf(out);
  }
  private static Quantity expense(RawCashCodec.Expense expense){return expense.available()?quantity(expense.goldRaw()):Quantity.unavailable();}
  private static Quantity quantity(RawCashCodec.Read<BigInteger> read){return read.presence()==RawCashCodec.Presence.VALUE?Quantity.value(read.value()):read.presence()==RawCashCodec.Presence.NULL?Quantity.knownNull():Quantity.unavailable();}
  private static Quantity fixed(RawCashCodec.Read<RawCashCodec.FixedPoint> read){return read.presence()==RawCashCodec.Presence.VALUE&&read.value().scale()==100000?Quantity.value(read.value().raw()):read.presence()==RawCashCodec.Presence.NULL?Quantity.knownNull():Quantity.unavailable();}
  private RawJson encodeOriginal(Originals originals,Report report,ActionPorts.OutcomeArchive archive) {
      ObjectNode row=StrictJson.object().put("schema",ORIGINAL).put("strengths_status",originals.strengthStatus().name());
      row.set("model_source",sources.model().toJson());row.set("collector_source",sources.collector().toJson());
      putRead(row,"strengths_read",originals.strengths(),archive);putRead(row,"cash_read",originals.cash(),archive);
      if(originals.hello().isPresent())row.put("hello_packet_base64",Base64.getEncoder().encodeToString(originals.hello().orElseThrow().packet().value()));else row.putNull("hello_packet_base64");
      putText(row,"strengths_reason",originals.strengthReason());putText(row,"cash_reason",originals.cashReason());row.set("report",HolyHirePoststate.json(report));
      return new RawJson(StrictJson.canonical(row,StrictJson.EXPLICIT_MAX_BYTES));
  }
  private static void putRead(ObjectNode row,String key,Optional<PlanningReadReceipt> read,ActionPorts.OutcomeArchive archive){if(read.isPresent())row.set(key,archive.readReferenceOf(read.orElseThrow()).toJson());else row.putNull(key);}
  private static void putText(ObjectNode row,String key,Optional<String> value){if(value.isPresent())row.put(key,value.orElseThrow());else row.putNull(key);}
  private static Optional<String> optionalText(JsonNode value){return value.isNull()?Optional.empty():Optional.of(StrictJson.text(value));}
  private static Optional<PlanningReadReceipt> loadRead(JsonNode value,ActionPorts.OutcomeArchive archive){if(value.isNull())return Optional.empty();var ref=ExactRef.fromJson(value);var read=archive.loadRead(ref);StrictJson.require(archive.readReferenceOf(read).equals(ref),"holy original read locator differs");NativeRecordedEvidenceVerifier.requireRead(read,archive);return Optional.of(read);}
  private static void requireRead(Complete frame,ArmyWarWindowReads.HolyHire selected,Instant deadline,PlanningReadReceipt read){new ArmyWarWindowReads.Request(frame,selected,deadline).requireReceipt(read);}
  private static String diagnostic(String part,Exception failure){return part+" unavailable: "+(failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage());}
  static Stocks stocks(JsonNode semantic) {
      return new Stocks(stock(semantic,"gold"),stock(semantic,"prestige"),stock(semantic,"piety"));
  }
  private static Quantity stock(JsonNode semantic,String key) {
      JsonNode field=semantic.get("played_character_"+key);
      if(field==null)return Quantity.unavailable();
      if(field.isNull())return Quantity.knownNull();
      if(!field.isObject()||!field.has("scale")||!field.get("scale").isIntegralNumber()||!field.get("scale").bigIntegerValue().equals(BigInteger.valueOf(100000)))return Quantity.unavailable();
      JsonNode raw=field.get("raw");return raw==null?Quantity.unavailable():raw.isNull()?Quantity.knownNull():raw.isIntegralNumber()?Quantity.value(raw.bigIntegerValue()):Quantity.unavailable();
  }
  static Association association(JsonNode context, Scope scope) {
      StrictJson.require(bool(context,"available")&&number(context.get("played_character_id")).equals(scope.actorId()),"holy actor differs");
      List<JsonNode> selected=rows(context.get("rows")).stream().filter(row->number(row.get("holy_order_id")).equals(scope.holyOrderId())).toList();
      StrictJson.require(selected.size()==1,"one post-hire order required");
      JsonNode order=selected.getFirst();
      StrictJson.require(number(order.get("employer_id")).equals(scope.actorId()),"holy employer absent");
      JsonNode association=order.path("military_terms").get("troop_association");
      if(association==null)return new Association(Status.UNAVAILABLE,List.of(),Optional.of("native troop association absent"));
      boolean available=bool(association,"available");
      StrictJson.require(bool(association,"applies_to_player"),"holy association actor differs");
      List<Member> members=new ArrayList<>();
      for(JsonNode row:rows(association.get("rows")))members.add(new Member(number(row.get("regiment_id")),bool(row,"available"),bool(row,"regiment_resolved"),
          bool(row,"native_carmy_resolved"),optionalNumber(row.get("native_carmy_id")),bool(row,"combat_resolved"),optionalNumber(row.get("combat_id"))));
      return new Association(available?Status.AVAILABLE:Status.PARTIAL,members,available?Optional.empty():Optional.of("native association partially unavailable"));
  }

  private static BigInteger number(JsonNode value){StrictJson.require(value!=null&&value.isIntegralNumber(),"exact integer token required");return value.bigIntegerValue();}
  private static Optional<BigInteger> optionalNumber(JsonNode value){return value==null||value.isNull()?Optional.empty():Optional.of(number(value));}
  private static boolean bool(JsonNode row,String key){JsonNode value=row.get(key);StrictJson.require(value!=null&&value.isBoolean(),"exact boolean required: "+key);return value.booleanValue();}
  private static List<JsonNode> rows(JsonNode value){StrictJson.require(value!=null&&value.isArray()&&value.size()<=65536,"bounded source rows required");List<JsonNode> out=new ArrayList<>();value.forEach(out::add);return List.copyOf(out);}

}
