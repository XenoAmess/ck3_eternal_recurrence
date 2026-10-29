package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import static org.xar.ck3.control.contracts.StrictJson.require;

/** Single strict public boundary; native wire integer domains remain in their original decoders. */
public final class GuiCodec {
 private GuiCodec(){}
 public static Request decode(String originalName,RawJson original){JsonNode value=StrictJson.parse(Objects.requireNonNull(original).bytes(),65536);require(value instanceof ObjectNode,"original GUI arguments object required");return decode(originalName,(ObjectNode)value);}
 public static Request decode(String originalName,ObjectNode in){
  Objects.requireNonNull(in);Method method=Method.exact(originalName);
  Set<String> required=new HashSet<>(),optional=new HashSet<>();
  boolean noRevision=method==Method.TREE||method==Method.CAMERA_STATUS;
  boolean nullableRevision=Set.of(Method.WHITE_AGE,Method.WHITE_NUMERIC,Method.CONFIRM_ITEM,Method.OPEN_DECISIONS,Method.WHITE_BUSINESS,Method.WHITE_TEXT,Method.SELECT_DECISION,Method.QUERY_DECISION).contains(method);
  if(!noRevision){if(nullableRevision)optional.add("expected_revision");else required.add("expected_revision");}
  Arguments args=switch(method){
   case CENTER_TITLE->{required.add("title_key");yield new Title(new GuiModels.TitleKey(text(in,"title_key")));}
   case OPEN_CHARACTER,OPEN_COMBAT,FIT_COMBAT,OPEN_FAITH,SELECT_ARMY->{
    String field=method==Method.OPEN_CHARACTER?"character_id":method==Method.OPEN_FAITH?"faith_id":method==Method.SELECT_ARMY?"subject_army_id":"combat_id";
    required.add(field);yield new Subject(new GuiModels.Subject(integer(in,field,0,method==Method.SELECT_ARMY?2147483647L:4294967294L)));}
   case HOVER_KNIGHTS->{required.addAll(Set.of("combat_id","ui_side"));yield new KnightHover(new GuiModels.Subject(integer(in,"combat_id",1,4294967294L)),GuiModels.Side.valueOf(literal(in,"ui_side").toUpperCase(Locale.ROOT)));}
   case HOVER_ARMY,LEAVE_ARMY,QUERY_ARMY->{
    required.addAll(Set.of("subject_army_id","tooltip_kind"));Slot<GuiModels.ReceiptId> receipt=new Absent<>();
    if(method!=Method.HOVER_ARMY){required.add("action_receipt");receipt=new Present<>(new GuiModels.ReceiptId(text(in,"action_receipt")));}
    yield new ArmyTooltip(new GuiModels.Subject(integer(in,"subject_army_id",0,2147483647L)),GuiModels.TooltipKind.parse(literal(in,"tooltip_kind")),receipt);}
   case TREE->{required.add("window_kind");yield new TreeQuery(GuiModels.TreeKind.parse(text(in,"window_kind")));}
   case QUERY_WINDOW->{required.add("window_kind");yield new WindowQuery(text(in,"window_kind"));}
   case SELECT_DECISION,QUERY_DECISION->{required.add("decision_key");yield new Decision(new GuiModels.DecisionKey(text(in,"decision_key")));}
   case CONFIRM_ITEM->{required.addAll(Set.of("decision_key","expected_window_kind"));yield new ConfirmItem(new GuiModels.DecisionKey(text(in,"decision_key")),GuiModels.TreeKind.parse(text(in,"expected_window_kind")));}
   case CONFIRM_OUTCOME->{required.addAll(Set.of("decision_key","expected_outcome"));optional.add("expected_event_definition_key");
    yield new ConfirmOutcome(new GuiModels.DecisionKey(text(in,"decision_key")),GuiModels.Outcome.valueOf(literal(in,"expected_outcome").toUpperCase(Locale.ROOT)),stringSlot(in,"expected_event_definition_key"));}
   case WHITE_AGE->{required.addAll(Set.of("control","expected_before_age","intent_id"));require(text(in,"control").equals("age_plus_1"),"original fixed age control");yield new WhiteAge(integer(in,"expected_before_age",0,119).intValueExact(),text(in,"intent_id"));}
   case WHITE_NUMERIC->{required.addAll(Set.of("control","expected_before_value","expected_before_price_text","intent_id"));yield new WhiteNumeric(GuiModels.NumericControl.parse(text(in,"control")),integer(in,"expected_before_value",0,99).intValueExact(),text(in,"expected_before_price_text"),text(in,"intent_id"));}
   case PRESENT,QUERY_PRESENT,QUERY_PRESENT_TOOLTIP->{
    required.add("window_kind");String operation=method==Method.PRESENT?text(in,"operation"):method==Method.QUERY_PRESENT_TOOLTIP?"query":"query";
    if(method==Method.PRESENT)required.add("operation");
    GuiModels.WindowKind window=GuiModels.WindowKind.parse(literal(in,"window_kind"));
    require(Set.of(GuiModels.WindowKind.FAITH,GuiModels.WindowKind.HOLDING,GuiModels.WindowKind.PERSONAL_BELIEFS,GuiModels.WindowKind.RITE_CREATION,GuiModels.WindowKind.CLERICAL_INTERACTION,GuiModels.WindowKind.TOOLTIPS).contains(window),"original presentation kind");
    Slot<GuiModels.Subject> subject;
    if(method==Method.QUERY_PRESENT){optional.add("subject_id");subject=subjectSlot(in,"subject_id");}else{required.add("subject_id");subject=new Present<>(new GuiModels.Subject(integer(in,"subject_id",0,4294967294L)));}
    optional.addAll(Set.of("presentation_target","presentation_receipt"));
    if(method==Method.PRESENT)optional.addAll(Set.of("presentation_index","presentation_tab"));
    if(method==Method.QUERY_PRESENT)optional.add("presentation_tab");
    Slot<String> target=stringSlot(in,"presentation_target"),tab=stringSlot(in,"presentation_tab");Slot<Integer> index=intSlot(in,"presentation_index",0,127);Slot<GuiModels.ReceiptId> receipt=receiptSlot(in,"presentation_receipt");
    if(method==Method.QUERY_PRESENT_TOOLTIP){required.addAll(Set.of("presentation_target","presentation_index","presentation_receipt"));optional.removeAll(required);
      require(target instanceof Present<?> && index instanceof Present<?> && receipt instanceof Present<?>,"tooltip selector and original receipt required");
      require(Set.of(GuiModels.WindowKind.FAITH,GuiModels.WindowKind.HOLDING,GuiModels.WindowKind.PERSONAL_BELIEFS,GuiModels.WindowKind.RITE_CREATION).contains(window),"original tooltip window");}
    Set<String> tooltipTargets=Set.of("faith_core_tenet","faith_doctrine","personal_tenet","rite_core_tenet_choice","rite_core_tenet_slot","holding_building","holding_building_preview","holding_construct_conditions");
    optional(target).ifPresent(value->require(method==Method.QUERY_PRESENT?Set.of("clerical_puppet","external_clerical_puppet").contains(value):method==Method.QUERY_PRESENT_TOOLTIP?tooltipTargets.contains(value):value.isEmpty()||tooltipTargets.contains(value)||Set.of("clerical_puppet","external_clerical_puppet").contains(value),"original finite presentation target"));
    optional(tab).ifPresent(value->require(Set.of("","beliefs","holy_sites","tenets","doctrines").contains(value),"original finite presentation tab"));
    if(method==Method.QUERY_PRESENT)require(!(tab instanceof Null<?>),"original default presentation_tab is not nullable");
    yield new Presentation(operation,window,subject,target,index,tab,receipt);}
   default->new Empty();
  };
  for(String name:required)require(in.has(name)&&!in.get(name).isNull(),"required original field "+name);
  in.fieldNames().forEachRemaining(name->require(required.contains(name)||optional.contains(name),"unknown original GUI field "+name));
  PublicUnsigned64.Field revision=PublicUnsigned64.read(in,"expected_revision",PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);
  return new Request(method,args,revision);
 }
 public static ObjectNode encodeRequest(Request request){
  Objects.requireNonNull(request);ObjectNode out=StrictJson.object();Arguments a=request.arguments();Method m=request.method();
  if(a instanceof Title v)out.put("title_key",v.key().value());
  else if(a instanceof Subject v)out.put(m==Method.OPEN_CHARACTER?"character_id":m==Method.OPEN_FAITH?"faith_id":m==Method.SELECT_ARMY?"subject_army_id":"combat_id",v.value().value());
  else if(a instanceof ArmyTooltip v){out.put("subject_army_id",v.army().value()).put("tooltip_kind",v.kind().wire());put(out,"action_receipt",v.receipt(),r->com.fasterxml.jackson.databind.node.TextNode.valueOf(r.value()));}
  else if(a instanceof KnightHover v)out.put("combat_id",v.combat().value()).put("ui_side",v.side().wire());
  else if(a instanceof WindowQuery v)out.put("window_kind",v.kind());
  else if(a instanceof TreeQuery v)out.put("window_kind",v.kind().wire());
  else if(a instanceof Decision v)out.put("decision_key",v.key().value());
  else if(a instanceof ConfirmItem v)out.put("decision_key",v.key().value()).put("expected_window_kind",v.window().wire());
  else if(a instanceof ConfirmOutcome v){out.put("decision_key",v.key().value()).put("expected_outcome",v.outcome().wire());put(out,"expected_event_definition_key",v.eventDefinition(),com.fasterxml.jackson.databind.node.TextNode::valueOf);}
  else if(a instanceof WhiteAge v)out.put("control","age_plus_1").put("expected_before_age",v.before()).put("intent_id",v.intentId());
  else if(a instanceof WhiteNumeric v)out.put("control",v.control().wire()).put("expected_before_value",v.before()).put("expected_before_price_text",v.price()).put("intent_id",v.intentId());
  else if(a instanceof Presentation v){out.put("window_kind",v.window().wire());if(m==Method.PRESENT)out.put("operation",v.operation());
   put(out,"subject_id",v.subject(),s->com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(s.value()));
   put(out,"presentation_target",v.target(),com.fasterxml.jackson.databind.node.TextNode::valueOf);put(out,"presentation_index",v.index(),com.fasterxml.jackson.databind.node.IntNode::valueOf);
   put(out,"presentation_tab",v.tab(),com.fasterxml.jackson.databind.node.TextNode::valueOf);put(out,"presentation_receipt",v.receipt(),r->com.fasterxml.jackson.databind.node.TextNode.valueOf(r.value()));}
  if(request.expectedRevision() instanceof PublicUnsigned64.NullValue)out.putNull("expected_revision");
  else if(request.expectedRevision() instanceof PublicUnsigned64.Value v)out.put("expected_revision",PublicUnsigned64.canonical(v.value(),PublicUnsigned64.Minimum.ZERO));
  return out;
 }
 /** Query tokens are actual Native originals; UNKNOWN remains an unresolved canonical receipt. */
 public static RawJson encode(Reply reply){
  Objects.requireNonNull(reply);
  if(reply instanceof CameraReply camera)return GuiRealmCameraStatus.encode(camera.status());
  if(reply instanceof NativeReply nativeReply)return publicOriginal(nativeReply.original());
  if(reply instanceof ReadReply read){RawJson original=read.receipt().original().originalResultToken().orElseThrow(()->new IllegalArgumentException("actual native query result absent"));
   if(read.receipt().request().operation().value().equals("inspect-gui-window-tree-v1")){ObjectNode out=PublicDataJson.object(original);var fields=(ObjectNode)org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(read.receipt().request().arguments());String kind=StrictJson.text(fields.get("window_kind"));
    out.put("schema","ck3-native-gui-window-tree-inspection-v1").put("window_kind",kind).put("rendered_text_available",false).put("selected_state_available",false).put("tooltip_state_available",false).put("business_model_available",false);
    return PublicDataJson.encodePreservingDecimals(publicIdentities(out),original);}
   return publicOriginal(original);}
  ActionReply action=(ActionReply)reply;ObjectNode out=action.receipt().ack().flatMap(a->a.originalResultToken()).map(PublicDataJson::object).orElseGet(()->StrictJson.object().put("schema","xar.ck3.gui-action-result/v1"));
  out.put("postcondition_verified",action.receipt().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED);
  out.put("verification_pending",action.receipt().outcome()==ActionReceipt.Outcome.UNRESOLVED);
  ObjectNode canonical=out.putObject("canonical_gui_action").put("outcome",action.receipt().outcome().name().toLowerCase(Locale.ROOT)).put("action_id",action.receipt().command().actionId()).put("ack_received",action.receipt().ack().isPresent());
  canonical.set("original_receipt",action.originalReference().toJson());return PublicDataJson.encode(publicIdentities(out));
 }
 public static RawJson encodePublicOriginal(RawJson actual){return PublicDataJson.encodePreservingDecimals(publicIdentities(PublicDataJson.object(Objects.requireNonNull(actual))),actual);}
 private static RawJson publicOriginal(RawJson actual){return encodePublicOriginal(actual);}
 private static final Set<String> PUBLIC_U64=Set.of("connection_generation","expected_connection_generation","queried_connection_generation","application_pump_epoch","application_tls_context","variable_context","character_address","native_revision","queried_native_revision","revision","queried_revision","snapshot_revision","query_sequence","pump_epoch","capture_epoch","action_epoch","later_epoch","action_owner_epoch","later_owner_epoch","observation_owner_epoch","gui_context_address","gui_owner_address","query_epoch","observation_epoch","game_creation_filetime","process_creation_filetime","observation_uptime_ms");
 /** Explicit public representation only; actual native/original/archive bytes remain unchanged. */
 private static JsonNode publicIdentities(JsonNode value){
  if(value.isObject()){ObjectNode out=((ObjectNode)value).deepCopy();var fields=new ArrayList<String>();out.fieldNames().forEachRemaining(fields::add);for(String name:fields){JsonNode token=out.get(name);if(PUBLIC_U64.contains(name)&&!token.isNull()){BigInteger actual=token.isIntegralNumber()?token.bigIntegerValue():PublicUnsigned64.parse(token,PublicUnsigned64.Minimum.ZERO,PublicUnsigned64.NumericInput.DECIMAL_ONLY);out.put(name,PublicUnsigned64.canonical(actual,PublicUnsigned64.Minimum.ZERO));}else out.set(name,publicIdentities(token));}return out;}
  if(value.isArray()){var out=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.arrayNode();value.forEach(v->out.add(publicIdentities(v)));return out;}return value;
 }
 private static String text(ObjectNode in,String field){JsonNode n=in.get(field);require(n!=null&&n.isTextual(),"text required: "+field);return n.textValue();}
 private static String literal(ObjectNode in,String field){String value=text(in,field);require(value.matches("[a-z_]+"),"exact original lower-case literal: "+field);return value;}
 private static BigInteger integer(ObjectNode in,String field,long min,long max){JsonNode n=in.get(field);require(n!=null&&n.isIntegralNumber(),"integer token required: "+field);BigInteger value=n.bigIntegerValue();require(value.compareTo(BigInteger.valueOf(min))>=0&&value.compareTo(BigInteger.valueOf(max))<=0,"integer domain: "+field);return value;}
 private static Slot<String> stringSlot(ObjectNode in,String field){if(!in.has(field))return new Absent<>();if(in.get(field).isNull())return new Null<>();return new Present<>(text(in,field));}
 private static Slot<Integer> intSlot(ObjectNode in,String field,long min,long max){if(!in.has(field))return new Absent<>();if(in.get(field).isNull())return new Null<>();return new Present<>(integer(in,field,min,max).intValueExact());}
 private static Slot<GuiModels.Subject> subjectSlot(ObjectNode in,String field){if(!in.has(field))return new Absent<>();require(!in.get(field).isNull(),"default subject is not nullable");return new Present<>(new GuiModels.Subject(integer(in,field,0,4294967294L)));}
 private static Slot<GuiModels.ReceiptId> receiptSlot(ObjectNode in,String field){Slot<String>s=stringSlot(in,field);if(s instanceof Present<String>v)return new Present<>(new GuiModels.ReceiptId(v.value()));return s instanceof Null<?>?new Null<>():new Absent<>();}
 private static <T>void put(ObjectNode out,String name,Slot<T>slot,java.util.function.Function<T,JsonNode> encode){if(slot instanceof Present<T> v)out.set(name,encode.apply(v.value()));else if(slot instanceof Null<?>)out.putNull(name);}
}

