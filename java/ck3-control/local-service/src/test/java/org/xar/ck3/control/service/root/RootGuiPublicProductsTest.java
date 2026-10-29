package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionHolyUi;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.publicmethods.gui.GuiRealmCameraStatus;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Source-only until Root runs the actual selected full graph. Software packets confer no Game qualification. */
final class RootGuiPublicProductsTest {
 @TempDir Path root;
@Test
public void testActionOperationsExcludesSpecializedAndRetainsOthers() {
    Set<String> ops = RootGuiPublicProducts.actionOperations();
    Set<String> all = GuiActions.operations();
    String sel = org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.SELECT;
    String conf = org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.CONFIRM;
    assertFalse(ops.contains(sel));
    assertFalse(ops.contains(conf));
    Set<String> expected = new HashSet<>(all);
    expected.remove(sel);
    expected.remove(conf);
    expected.add("activate-ingame-decisions-v1");
    assertEquals(expected, ops);
    assertEquals(ops.size(), all.size() - 2 + 1);
    assertTrue(ops.contains("navigate-ingame-ui-v1"));
    assertTrue(ops.contains("activate-ingame-decisions-v1"));
    var union = new HashSet<>(ops);
    assertTrue(union.add(sel)); assertTrue(union.add(conf));
    assertEquals(ops.size() + 2, union.size());
    assertThrows(UnsupportedOperationException.class, () -> ops.add("x"));
}

 private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
 private static ToolCall call(String name,ObjectNode args){return new ToolCall(name,new PublicMcpDirectory.Arguments(Presence.VALUE,Optional.of(raw(args))),Optional.empty(),new McpCancellation());}
 private static ExactRef actualJavaSource()throws IOException{
  String value=System.getProperty("xar.public.gui.root.source.path");
  if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_GUI_JAVA_SOURCE: missing -Dxar.public.gui.root.source.path");
  Path path=Path.of(value);assertTrue(path.isAbsolute());assertEquals("RootGuiPublicProducts.java",path.getFileName().toString());
  var observed=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(observed);var ref=observed.source();return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
 }
 private static ToolDescriptor descriptor(List<ToolDescriptor> actual,String name){return actual.stream().filter(d->d.name().equals(name)).findFirst().orElseThrow(()->new AssertionError("mandatory original GUI descriptor absent: "+name));}
 private static ObjectNode sample(Method method){
  ObjectNode a=StrictJson.object();
  if(method!=Method.TREE&&method!=Method.CAMERA_STATUS)a.put("expected_revision",1);
  switch(method){
   case CENTER_TITLE->a.put("title_key","c_normandy");
   case OPEN_CHARACTER->a.put("character_id",73);case OPEN_FAITH->a.put("faith_id",0);
   case SELECT_ARMY->a.put("subject_army_id",0);case OPEN_COMBAT,FIT_COMBAT->a.put("combat_id",9);
   case HOVER_KNIGHTS->a.put("combat_id",9).put("ui_side","left");
   case HOVER_ARMY,LEAVE_ARMY,QUERY_ARMY->{a.put("subject_army_id",0).put("tooltip_kind","supply_state");if(method!=Method.HOVER_ARMY)a.put("action_receipt","a".repeat(32));}
   case TREE->a.put("window_kind","decisions");case QUERY_WINDOW->a.put("window_kind","character");
   case SELECT_DECISION,QUERY_DECISION->a.put("decision_key","enable_auto_build");
   case CONFIRM_ITEM->a.put("decision_key","create_white_courtier").put("expected_window_kind","vivhite_courtier");
   case CONFIRM_OUTCOME->a.put("decision_key","create_white_courtier").put("expected_outcome","decision_closed").putNull("expected_event_definition_key");
   case WHITE_AGE->a.put("control","age_plus_1").put("expected_before_age",18).put("intent_id","age_once");
   case WHITE_NUMERIC->a.put("control","martial_plus_1").put("expected_before_value",10).put("expected_before_price_text","100").put("intent_id","martial_once");
   case PRESENT->a.put("operation","open_holding").put("window_kind","holding").put("subject_id",1);
   case QUERY_PRESENT->a.put("window_kind","faith");
   case QUERY_PRESENT_TOOLTIP->a.put("window_kind","faith").put("subject_id",0).put("presentation_target","faith_core_tenet").put("presentation_index",0).put("presentation_receipt","b".repeat(32));
   default->{}
  }
  return a;
 }
 @Test void exactTwentyEightOriginalSdkDescriptorsAndSharedTypedSerde()throws Exception{
  List<ToolDescriptor> originals=RootOriginalPublicTestInputs.tools();assertEquals(28,Method.values().length);
  for(Method method:Method.values()){
   ToolDescriptor original=descriptor(originals,method.originalName());ObjectNode input=sample(method);ToolCall call=call(original.name(),input);
   original.validateArguments(call.arguments());Request request=GuiCodec.decode(original.name(),call.arguments().objectOrEmpty());
   assertEquals(request,GuiCodec.decode(original.name(),GuiCodec.encodeRequest(request)));
   ObjectNode extra=input.deepCopy().put("not_an_original_argument",0);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(original.name(),extra));
   JsonNode schema=StrictJson.parse(original.original().bytes(),StrictJson.EXPLICIT_MAX_BYTES).get("inputSchema");
   if(schema.has("required"))for(JsonNode required:schema.get("required")){ObjectNode missing=input.deepCopy();missing.remove(required.textValue());assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(original.name(),missing),method+" missing "+required);}
  }
 }
 @Test void originalNullableRevisionAndDefaultSelectorsKeepMissingNullSeparate(){
  ObjectNode missing=StrictJson.object().put("decision_key","enable_auto_build");ObjectNode nullable=missing.deepCopy().putNull("expected_revision");
  Request absent=GuiCodec.decode(Method.QUERY_DECISION.originalName(),missing),nullValue=GuiCodec.decode(Method.QUERY_DECISION.originalName(),nullable);
  assertInstanceOf(PublicUnsigned64.Missing.class,absent.expectedRevision());assertInstanceOf(PublicUnsigned64.NullValue.class,nullValue.expectedRevision());assertNotEquals(absent,nullValue);
  assertFalse(GuiCodec.encodeRequest(absent).has("expected_revision"));assertTrue(GuiCodec.encodeRequest(nullValue).get("expected_revision").isNull());
  ObjectNode presentation=sample(Method.PRESENT);Request a=GuiCodec.decode(Method.PRESENT.originalName(),presentation);presentation.putNull("presentation_target");Request b=GuiCodec.decode(Method.PRESENT.originalName(),presentation);
  assertNotEquals(a,b);assertEquals(a,GuiCodec.decode(a.method().originalName(),GuiCodec.encodeRequest(a)));assertEquals(b,GuiCodec.decode(b.method().originalName(),GuiCodec.encodeRequest(b)));
 }
 @Test void integerLiteralsIdentityDomainsAndFiniteSelectorsAreStrict(){
  for(JsonNode wrong:List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("1.0".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("\"1\"".getBytes(StandardCharsets.UTF_8)))){
   ObjectNode args=sample(Method.OPEN_CHARACTER);args.set("character_id",wrong);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.OPEN_CHARACTER.originalName(),args));}
  ObjectNode army=sample(Method.SELECT_ARMY);army.put("subject_army_id",2147483648L);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.SELECT_ARMY.originalName(),army));
  ObjectNode faith=sample(Method.OPEN_FAITH);assertEquals(BigInteger.ZERO,((Subject)GuiCodec.decode(Method.OPEN_FAITH.originalName(),faith).arguments()).value().value());
  ObjectNode character=sample(Method.OPEN_CHARACTER);character.put("character_id",0);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.OPEN_CHARACTER.originalName(),character));
  ObjectNode revision=sample(Method.OPEN_FAITH);revision.put("expected_revision","18446744073709551615");assertEquals(new BigInteger("18446744073709551615"),((PublicUnsigned64.Value)GuiCodec.decode(Method.OPEN_FAITH.originalName(),revision).expectedRevision()).value());
  revision.put("expected_revision",9007199254740992L);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.OPEN_FAITH.originalName(),revision));
  for(String wrong:List.of("01","18446744073709551616","-1")){revision.put("expected_revision",wrong);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.OPEN_FAITH.originalName(),revision));}
  ObjectNode hover=sample(Method.HOVER_KNIGHTS);hover.put("ui_side","LEFT");assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.HOVER_KNIGHTS.originalName(),hover));
  ObjectNode present=sample(Method.PRESENT);present.put("operation","query");Request queryPresentation=GuiCodec.decode(Method.PRESENT.originalName(),present);assertFalse(queryPresentation.submitsAction());assertEquals(queryPresentation,GuiCodec.decode(Method.PRESENT.originalName(),GuiCodec.encodeRequest(queryPresentation)));
  ObjectNode query=sample(Method.QUERY_PRESENT);query.put("presentation_index",1);assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.QUERY_PRESENT.originalName(),query));
  query.remove("presentation_index");query.putNull("presentation_tab");assertThrows(IllegalArgumentException.class,()->GuiCodec.decode(Method.QUERY_PRESENT.originalName(),query));
 }
 private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<GuiReads> owner){
  return new ActionWriterIntegrationFixture.SoftwareReadScenario(GuiModels.Build.CROZIER4.sha256(),"controlled-gui-public",source->{
   GuiReads actual=new GuiReads(new GuiReads.Sources(source,source,source,source,source,source,source));assertTrue(owner.compareAndSet(null,actual));return actual.registered();
  },request->{ObjectNode a=StrictJson.object(StrictJson.parse(request.additionalFields().bytes()),Set.of("window_kind"));GuiModels.TreeKind kind=GuiModels.TreeKind.parse(StrictJson.text(a.get("window_kind")));
   ObjectNode out=StrictJson.object().put("step","inspect-gui-window-tree-v1").put("scope_root_name",kind.root()).put("accepted",true).put("root_available",true).put("truncated",false).put("status","available").put("widget_count",1);
   out.putArray("widgets").addObject().put("runtime_name",kind.root()).put("child_path","").put("depth",0).put("child_count",0).put("vtable_rva",4096).put("effective_visible",true).put("enabled",true);
   return raw(out);
  },Optional.of(GuiModels.Build.CROZIER4.version()),Set.of());
 }
 private static GuiService service(ActionWriterIntegrationFixture f,GuiReads contracts){
  return new GuiService(new GuiCapabilities(f.coordinator,f.reads,contracts),contracts,f.reads,f.coordinator,()->f.archive.withSession(f.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
 }
 private static GuiService.Invocation invocation(ActionWriterIntegrationFixture f)throws Exception{
  var actual=f.ready().request();var before=actual.before();return new GuiService.Invocation(new GuiModels.Context(before,actual.source(),actual.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER4,actual.deadline()),before.frame().revision(),true,true);
 }
 @Test void actualRootParsedArtifactArchivePreservesCompleteMaterialAndValidatesReadback()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("parsed-complete-archive"),false,scenario(owner))){
   String id="root-parsed-complete-material";
   byte[] outbound=NativeWire.execute(id,"query-ingame-ui-window-v1",BigInteger.ONE,
    StrictJson.canonical(StrictJson.object().put("window_kind","character").put("subject_id",0)));
   var response=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true).put("error","");
   response.putObject("result").put("schema","software-original-ui-result");
   byte[] inbound=NativeWire.packet(StrictJson.canonical(response));
   var fullBefore=new OpportunityJson.Obj(Map.of("snapshot_id",new OpportunityJson.Text("software-before"),
    "complete_history_integer",new OpportunityJson.IntegerValue(new BigInteger("9".repeat(70000))),
    "exact_decimal",new OpportunityJson.DecimalValue("-0.0")));
   RawJson original=NativeUiParsedReturn.encode(outbound,inbound,fullBefore);
   assertThrows(IllegalArgumentException.class,original::requireProtocolBound);
   fixture.writer.locked(same->{
    var publicReference=RootGuiPublicProducts.preserveParsedReturn(fixture.archive,same,original);
    GuiPublicMetadata.requireParsedReturnReference(publicReference);
    ObjectNode fields=PublicDataJson.object(publicReference);assertEquals("unvalidated",fields.remove("validation_state").textValue());
    ExactRef exact=ExactRef.fromJson(fields);
    byte[] reloaded=fixture.archive.readArtifact(same,exact,NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
    assertArrayEquals(original.bytes(),reloaded);
    assertEquals(fullBefore,NativeUiParsedReturn.decode(reloaded).get("actual_pre_submission_snapshot"));
    var wrong=NativeUiParsedReturn.decode(original.bytes()).with("validation_state",new OpportunityJson.Text("validated"));
    assertThrows(IllegalArgumentException.class,()->RootGuiPublicProducts.preserveParsedReturn(fixture.archive,same,PublicDataJson.encodeFullMaterial(wrong)));
    return null;
   });
   assertEquals(0,fixture.nativeActionWrites());
  }
 }
 @Test void actualClosedOutcomeProducerUsesOriginalEmptyNativeEventKey()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("closed-outcome-native-key"),false,scenario(owner))){
   var frame=invocation(fixture);var captured=new AtomicReference<ActionCommand>();
   final class StopBeforeSubmit extends RuntimeException{}
   ActionCoordinatorPort capture=new ActionCoordinatorPort(){
    public ActionReceipt execute(ActionCommand command){captured.set(command);throw new StopBeforeSubmit();}
    public ActionReceipt reconcile(String actionId){throw new AssertionError("producer cannot reconcile");}};
   var capabilities=new GuiCapabilities(capture,fixture.reads,owner.get());
   for(Optional<String> event:List.of(Optional.<String>empty(),Optional.of(""))){
    assertThrows(StopBeforeSubmit.class,()->capabilities.confirm_ingame_decision_outcome_v1(new GuiModels.Intent(frame.nativeContext(),"closed-outcome-key"),new GuiModels.DecisionKey("create_white_courtier"),GuiModels.Outcome.DECISION_CLOSED,event));
    var produced=GuiService.argumentFields(captured.get());
    assertTrue(produced.get("expected_event_definition_key").isTextual());assertEquals("",produced.get("expected_event_definition_key").textValue());
   }
   assertEquals(0,fixture.nativeActionWrites());
  }
 }
 @Test void unavailableSelectedTermsAreValidatedBeforeOuterUnavailableReturn()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("selected-terms-unavailable"),false,scenario(owner))){
   var c=invocation(fixture).nativeContext();var key=new GuiModels.DecisionKey("create_white_courtier");
   ObjectNode terms=StrictJson.object().put("schema","ck3-selected-decision-terms-v1").put("read_only",true).put("action_ready",false)
    .put("decision_confirm_invoked",false).put("game_version",c.build().version()).put("executable_sha256",c.build().sha256())
    .put("decision_key",key.value()).put("played_character_id",c.before().frame().identity().player()).put("date_raw",c.before().frame().identity().dateRaw())
    .put("capture_epoch",0).put("context_adapter","actual_empty_named_parameters_only").put("available",false).put("unavailable_reason","controlled_missing_context").put("context_verified",false);
   for(String field:List.of("requirements_bypass_observed","ordinary_legality_observed","confirm_tooltip_available","requirements_description_available","cost_description_available","resource_quote_available","cooldown_observed"))terms.put(field,false);
   for(String field:List.of("can_confirm","requirements_bypass_raw","ordinary_can_confirm","confirm_tooltip","requirements_description","cost_description","resource_quote","cooldown","stock_default_parameter"))terms.putNull(field);
   ObjectNode outer=StrictJson.object().put("schema","ck3-ingame-decision-item-v1").put("step","query-ingame-decision-item-v1").put("read_only",true)
    .put("game_version",c.build().version()).put("executable_sha256",c.build().sha256()).put("row_widget_datacontext_verified",false).put("action_qualified",false).put("available",false).put("unavailable_reason","controlled_outer_unavailable");
   outer.set("selected_terms",terms);assertFalse(GuiDecoders.decisionItem(outer,c,key).availability().available());
   for(String field:List.of("context_verified","requirements_bypass_observed","resource_quote_available","can_confirm")){
    var bad=outer.deepCopy();((ObjectNode)bad.get("selected_terms")).put(field,true);
    assertThrows(IllegalArgumentException.class,()->GuiDecoders.decisionItem(bad,c,key));
   }
   var bad=outer.deepCopy();((ObjectNode)bad.get("selected_terms")).put("played_character_id",true);
   assertThrows(IllegalArgumentException.class,()->GuiDecoders.decisionItem(bad,c,key));
   terms.put("available",true).put("capture_epoch",1).put("context_verified",true).put("named_parameter_count",0)
    .put("can_confirm",true).put("requirements_bypass_observed",true).put("requirements_bypass_raw",0)
    .put("ordinary_legality_observed",true).put("ordinary_can_confirm",true).put("resource_quote_available",true).put("cooldown_observed",true);
   var quote=terms.putObject("resource_quote").put("raw_scale",100000).put("native_affordable",true);
   var amounts=quote.putArray("resource_vector_raw");amounts.add(Long.MIN_VALUE);for(int i=1;i<9;i++)amounts.add(0);amounts.add(Long.MAX_VALUE);
   terms.putObject("cooldown").put("present",false).put("current_counter_raw",Integer.MIN_VALUE).putNull("expiry_raw").put("active",false).put("counter_unit","native_decision_clock_counter");
   var checked=assertInstanceOf(GuiSelectedDecisionTerms.Available.class,GuiSelectedDecisionTerms.decode(terms,c,key));
   assertEquals(Long.MIN_VALUE,checked.resourceQuote().orElseThrow().resources().getFirst().longValue());
   assertEquals(Long.MAX_VALUE,checked.resourceQuote().orElseThrow().resources().getLast().longValue());assertFalse(checked.cooldown().orElseThrow().active());
   outer.set("selected_terms",terms);assertThrows(IllegalArgumentException.class,()->GuiDecoders.decisionItem(outer,c,key));
   var malformed=terms.deepCopy();((com.fasterxml.jackson.databind.node.ArrayNode)malformed.path("resource_quote").get("resource_vector_raw")).set(0,com.fasterxml.jackson.databind.node.BooleanNode.TRUE);
   assertThrows(IllegalArgumentException.class,()->GuiSelectedDecisionTerms.decode(malformed,c,key));
  }
 }
 @Test void actualTransportReadArchiveToOriginalGuiServiceCodecAndMcpEnvelope()throws Exception{
  List<ToolDescriptor> originals=RootOriginalPublicTestInputs.tools();ExactRef selected=actualJavaSource();var owner=new AtomicReference<GuiReads>();
  try(var fixture=new ActionWriterIntegrationFixture(root.resolve("tree"),false,scenario(owner))){
   GuiService service=service(fixture,owner.get());var frame=invocation(fixture);byte[] ledger=fixture.ledgerBytes();
   var routes=RootGuiPublicProducts.bindings(request->{try{return fixture.writer.locked(same->GuiCodec.encode(service.invoke(request,frame)));}catch(IOException e){throw new UncheckedIOException(e);}},selected);
   var binding=routes.stream().filter(r->r.name().equals(Method.TREE.originalName())).findFirst().orElseThrow();ToolDescriptor original=descriptor(originals,binding.name());ToolCall call=call(binding.name(),sample(Method.TREE));
   original.validateArguments(call.arguments());Request request=binding.decoder().decode(call);RawJson result=binding.actual().invoke(request);CallResult envelope=binding.encoder().encode(result);original.validateResult(envelope);
   JsonNode body=StrictJson.parse(envelope.bytes(),StrictJson.EXPLICIT_MAX_BYTES).get("structuredContent");
   assertEquals("ck3-native-gui-window-tree-inspection-v1",body.get("schema").textValue());assertEquals("decisions",body.get("window_kind").textValue());assertFalse(body.get("business_model_available").booleanValue());assertEquals(1,body.get("widgets").size());
   assertTrue(fixture.scenarioReadWrites()>0);assertEquals(0,fixture.nativeActionWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
  }
 }
 @Test void actualCameraStatusServiceToSameProductionBindingsAndMcpWithoutFrameQueryOrSubmission()throws Exception{
  var originals=RootOriginalPublicTestInputs.tools();ExactRef selected=actualJavaSource();var owner=new AtomicReference<GuiReads>();
  try(var fixture=new ActionWriterIntegrationFixture(root.resolve("status"),false,scenario(owner))){
   GuiService service=service(fixture,owner.get());int reads=fixture.nativeReadWrites();byte[] ledger=fixture.ledgerBytes();
   var binding=RootGuiPublicProducts.bindings(request->{assertEquals(Method.CAMERA_STATUS,request.method());try{return GuiCodec.encode(service.cameraStatus());}catch(IOException e){throw new UncheckedIOException(e);}},selected).stream().filter(b->b.name().equals(Method.CAMERA_STATUS.originalName())).findFirst().orElseThrow();
   ToolDescriptor original=descriptor(originals,binding.name());ToolCall call=call(binding.name(),StrictJson.object());original.validateArguments(call.arguments());
   CallResult response=binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call)));original.validateResult(response);
   JsonNode actual=StrictJson.parse(response.bytes(),StrictJson.EXPLICIT_MAX_BYTES).get("structuredContent");
   assertEquals("not_requested",actual.get("status").textValue());assertTrue(actual.get("native_actual").isNull());assertTrue(actual.get("requested_sequence").isNull());assertFalse(actual.get("same_frame_with_gameplay_claim").booleanValue());
   assertEquals(reads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
  }
 }
 @Test void originalCurrentBuildUnsupportedCombatRouteRefusesBeforeAnySubmission()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("unsupported"),false,scenario(owner))){
   var service=service(fixture,owner.get());var frame=invocation(fixture);ObjectNode args=sample(Method.OPEN_COMBAT);args.put("expected_revision",frame.publicRevision());
   int writes=fixture.nativeActionWrites();assertThrows(IllegalArgumentException.class,()->fixture.writer.locked(same->service.invoke(GuiCodec.decode(Method.OPEN_COMBAT.originalName(),args),frame)));assertEquals(writes,fixture.nativeActionWrites());
  }
 }
 private static final class BeforeNative extends RuntimeException{}
 @Test void originalPresentationOpeningDoesNotAcquireAnUnrequestedTabBeforeActualPreparation()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("opening"),false,scenario(owner))){
   var contracts=owner.get();var prepared=new AtomicReference<NativeRequest>();var actualPreparation=new GuiActions(fixture.reads,contracts,()->fixture.archive.withSession(fixture.writer.borrowedSession()));
   ActionCoordinatorPort intercept=new ActionCoordinatorPort(){
    @Override public ActionReceipt execute(ActionCommand command){assertTrue(prepared.compareAndSet(null,actualPreparation.prepare(command)));throw new BeforeNative();}
    @Override public ActionReceipt reconcile(String actionId){throw new AssertionError("preparation-only fixture must not reconcile");}
   };
   var caps=new GuiCapabilities(intercept,fixture.reads,contracts);var service=new GuiService(caps,contracts,fixture.reads,intercept,()->fixture.archive.withSession(fixture.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
   var actual=invocation(fixture);ObjectNode args=sample(Method.PRESENT);args.put("expected_revision",actual.publicRevision());
   assertThrows(BeforeNative.class,()->fixture.writer.locked(same->service.invoke(GuiCodec.decode(Method.PRESENT.originalName(),args),actual)));
   assertNotNull(prepared.get());assertEquals("navigate-ingame-ui-v1",prepared.get().step());
   var fields=StrictJson.parse(prepared.get().additionalFields().bytes());assertEquals("open_holding",fields.get("operation").textValue());assertEquals("holding",fields.get("window_kind").textValue());assertFalse(fields.has("presentation_tab"));
   assertEquals(0,fixture.nativeActionWrites());
  }
 }
 @Test void sameNativeReadOperationHasDistinctOriginalContractsAndCannotUseGameplayOriginAsFrontend()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("origins"),false,scenario(owner))){
   var actual=fixture.ready().request();GuiReads gameplay=owner.get();ReadContract<GuiModels.WindowTree> frontend=RootGuiPublicProducts.frontendCensus(gameplay.census.sourceRef());
   assertEquals(gameplay.census.operation(),frontend.operation());assertNotEquals(gameplay.census.contractId(),frontend.contractId());assertEquals(ReadContract.GuardMode.FRONTEND_SESSION,frontend.guardMode());
   var readCatalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(gameplay.census,gameplay.census.sourceRef()),new RootReadContractCatalog.InstalledRead(frontend,frontend.sourceRef())),List.of());
   var executable=RootExecutableBindings.freeze(List.of(),readCatalog,List.of(),1);
   assertTrue(readCatalog.containsIdentity(gameplay.census));assertTrue(readCatalog.containsIdentity(frontend));
   assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,executable.resolve(gameplay.census.operation(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP).orElseThrow().guardMode());
   assertEquals(ReadContract.GuardMode.FRONTEND_SESSION,executable.resolve(frontend.operation(),ReadContract.GuardMode.FRONTEND_SESSION).orElseThrow().guardMode());
   assertEquals(gameplay.census.sourceRef(),executable.resolve(gameplay.census.operation(),new CommandOrigin.Gameplay(actual.before())).orElseThrow().implementationSource());
   assertThrows(IllegalArgumentException.class,()->executable.resolve(frontend.operation()));
   var frame=new GuiModels.Context(actual.before(),actual.source(),actual.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER4,actual.deadline());
   var fields=GuiService.metadata(frame).put("window_kind","decisions");var wrong=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),frontend.operation(),GuiService.arguments(fields),actual.deadline());
   assertThrows(IllegalArgumentException.class,()->frontend.prepare(wrong,"controlled-wrong-origin"));assertEquals(0,fixture.nativeActionWrites());
  }
 }
 @Test void originalHolyProducerToCanonicalSerdeAndInstalledFiniteControlConsumer()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("holy-navigation"),false,scenario(owner))){
   var original=fixture.command("holy-control-serde");var control=new HashSet<GuiService.NavigationSelector>();var pending=new HashSet<GuiService.NavigationSelector>();
   for(var op:ReligionHolyUi.Operation.values())(op.finalWrite()?pending:control).add(new GuiService.NavigationSelector(op.window(),op.wire()));
   var metadata=new RootGuiPublicProducts.NavigationControlMetadata("xar.java.holy-original-ui-post/v1",control,pending);
   assertEquals(5,metadata.controlSelectors().size());assertEquals(2,metadata.pendingSelectors().size());
   for(var op:ReligionHolyUi.Operation.values()){
    var selection=new ReligionHolyUi.Selection(op,List.of(ReligionHolyUi.Operation.OPEN_CREATION,ReligionHolyUi.Operation.TYPE,ReligionHolyUi.Operation.CREATE).contains(op)?BigInteger.ZERO:BigInteger.valueOf(19),op==ReligionHolyUi.Operation.TYPE?Optional.of("regional"):Optional.empty(),Optional.empty(),op==ReligionHolyUi.Operation.CREATE?Optional.of("a".repeat(64)):Optional.empty());
    var fields=ReligionHolyUi.nativeFields(selection,new ReligionHolyUi.Frame(BigInteger.ONE,original.before().frame().identity().dateRaw(),BigInteger.valueOf(73),BigInteger.valueOf(5)));
    var expected=new ProposalLifecycle.ExpectedPostcondition(1,original.before(),original.source(),metadata.observerSchema(),List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("holy.control_postcondition_observed"),true)));
    var command=new ActionCommand("holy-"+op.name().toLowerCase(Locale.ROOT),original.before(),original.source(),original.sessionId(),new OperationKey("navigate-ingame-ui-v1"),GuiService.arguments(fields),expected,original.claims(),original.deadline());
    var restored=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));assertEquals(command,restored);
    assertEquals(!op.finalWrite(),RootGuiPublicProducts.matchesFiniteControl(metadata,restored));assertEquals(op.finalWrite(),RootGuiPublicProducts.matchesFinitePending(metadata,restored));
    assertEquals(selection,ReligionHolyUi.selection((ObjectNode)org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(restored.arguments())));
    var wrong=fields.deepCopy().put("operation","not-an-original-selector");
    var changed=new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),command.operation(),GuiService.arguments(wrong),command.expected(),command.claims(),command.deadline());
    assertFalse(RootGuiPublicProducts.matchesFiniteControl(metadata,changed));assertFalse(RootGuiPublicProducts.matchesFinitePending(metadata,changed));
   }
   var only=control.iterator().next();
   assertThrows(IllegalArgumentException.class,()->new RootGuiPublicProducts.NavigationControlMetadata(metadata.observerSchema(),Set.of(only),Set.of(only)));
   assertThrows(IllegalArgumentException.class,()->new RootGuiPublicProducts.NavigationDefinition(control,actualJavaSource(),Optional.empty(),same->{throw new AssertionError("descriptor validation cannot install");},Optional.of(metadata)));
   assertEquals(0,fixture.nativeActionWrites());
  }
 }

 @Test void actualGuiActionPreparationReturnsCanonicalCommandWithoutNativeOrLedgerWrite()throws Exception{
  var owner=new AtomicReference<GuiReads>();try(var fixture=new ActionWriterIntegrationFixture(root.resolve("prepare-action"),false,scenario(owner))){
   var contracts=owner.get();var port=GuiService.captureCapable(fixture.coordinator);var caps=new GuiCapabilities(port,fixture.reads,contracts);
   var service=new GuiService(caps,contracts,fixture.reads,port,()->fixture.archive.withSession(fixture.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
   var frame=invocation(fixture);ObjectNode args=sample(Method.PRESENT);args.put("expected_revision",frame.publicRevision());byte[] before=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();
   ActionCommand command=fixture.writer.locked(same->service.prepareAction(GuiCodec.decode(Method.PRESENT.originalName(),args),frame));
   assertEquals("navigate-ingame-ui-v1",command.operation().value());assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
   var actual=new GuiActions(fixture.reads,contracts,()->fixture.archive.withSession(fixture.writer.borrowedSession())).prepare(command);assertEquals("open_holding",StrictJson.parse(actual.additionalFields().bytes()).get("operation").textValue());
   assertEquals(0,fixture.nativeActionWrites());assertEquals(reads,fixture.nativeReadWrites());assertArrayEquals(before,fixture.ledgerBytes());
   assertThrows(IllegalArgumentException.class,()->fixture.writer.locked(same->service.prepareAction(GuiCodec.decode(Method.TREE.originalName(),sample(Method.TREE)),frame)));
  }
 }

}


