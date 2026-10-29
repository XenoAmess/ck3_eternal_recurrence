package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.gui.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing software transport -> sole writer -> archive/replay -> public consumer; no live CK3 qualification. */
final class GuiDecisionWriterOriginalsTest {
 @TempDir Path root;
 private static final String KEY="ervc_courtier_creator_decision";
 private static RawJson raw(ObjectNode value){return PublicDataJson.encodeFullMaterial(value);}
 private static final class Run implements AutoCloseable {
  final ActionWriterIntegrationFixture fixture;final GuiReads contracts;final GuiActions actions;
  final GuiService.NavigationPorts ports;final GuiService service;final GuiService.Invocation invocation;
  final Request request;final RawJson beforeSource;final Method method;final boolean afterMatches;
  boolean rootAbsent;
  final AtomicReference<GuiModels.Context> context=new AtomicReference<>();final AtomicInteger dispatches=new AtomicInteger();
  Run(Path path,Method method,boolean afterMatches,Consumer<ObjectNode> changedAck,boolean loseAck)throws Exception{
   this.method=method;this.afterMatches=afterMatches;var readOwner=new AtomicReference<GuiReads>();var actionOwner=new AtomicReference<GuiActions>();
   String step=switch(method){case SELECT_DECISION->"select-ingame-decision-item-v1";case CONFIRM_ITEM->"confirm-ingame-decision-item-v1";case CONFIRM_OUTCOME->"confirm-ingame-decision-outcome-v1";default->throw new IllegalArgumentException("finite decision action");};
   var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(GuiModels.Build.CROZIER4.sha256(),"ck3-1.20.0.4-msvc-x64",source->{
    var actual=new GuiReads(new GuiReads.Sources(source,source,source,source,source,source,source));assertTrue(readOwner.compareAndSet(null,actual));return actual.registered();
   },nativeRequest->{assertNotNull(context.get());return raw(switch(nativeRequest.step()){
    case "query-ingame-decision-item-v1"->model(method!=Method.SELECT_DECISION||dispatches.get()>0&&afterMatches);
    case "inspect-gui-window-tree-v1"->tree();default->throw new AssertionError(nativeRequest.step());
   });},Optional.of(GuiModels.Build.CROZIER4.version()),Set.of());
   var actionScenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey(step),"game.command."+step,
    (command,attempt,outcome)->actionOwner.get().observe(command,attempt,outcome),()->assertEquals(1,dispatches.incrementAndGet()),
    Optional.of(()->{ObjectNode value=ack(step);changedAck.accept(value);return raw(value);}),Optional.empty(),false,
    Optional.of(command->actionOwner.get().prepare(command)));
   fixture=new ActionWriterIntegrationFixture(path,loseAck,readScenario,List.of(actionScenario));contracts=readOwner.get();
   actions=new GuiActions(fixture.reads,contracts,()->fixture.archive.withSession(fixture.writer.borrowedSession()));assertTrue(actionOwner.compareAndSet(null,actions));
   ports=new GuiService.NavigationPorts(actions,contracts,fixture.reads,List.of());
   fixture.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(new OperationKey(step),contracts.semantic.sourceRef(),ports::replay));
   var actual=fixture.ready().request();var c=new GuiModels.Context(actual.before(),actual.source(),actual.sessionId(),BigInteger.valueOf(5),GuiModels.Build.CROZIER4,actual.deadline());context.set(c);
   invocation=new GuiService.Invocation(c,c.before().frame().revision(),true,true);var snapshot=actual.observations().snapshot();
   beforeSource=GuiPublicMetadata.beforeSource(PublicDataJson.encodeFullMaterial(snapshot),PublicDataJson.encodeFullMaterial(OpportunityJson.object(snapshot.get("diagnostics"),"actual diagnostics")));
   ActionCoordinatorPort borrowedActions=new ActionCoordinatorPort(){
    @Override public ActionReceipt execute(ActionCommand command){try{return fixture.coordinator.execute(fixture.writer.borrowedSession(),command);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}
    @Override public ActionReceipt reconcile(String actionId){try{return fixture.coordinator.reconcile(fixture.writer.borrowedSession(),actionId);}catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}
   };
   service=new GuiService(new GuiCapabilities(borrowedActions,fixture.reads,contracts),contracts,fixture.reads,borrowedActions,()->fixture.archive.withSession(fixture.writer.borrowedSession()),Optional.empty(),Optional.empty(),Optional.empty());
   ObjectNode args=StrictJson.object().put("expected_revision",invocation.publicRevision()).put("decision_key",KEY);
   if(method==Method.CONFIRM_ITEM)args.put("expected_window_kind","vivhite_courtier");
   if(method==Method.CONFIRM_OUTCOME)args.put("expected_outcome","decision_closed").putNull("expected_event_definition_key");
   request=GuiCodec.decode(method.originalName(),args);
  }
  ObjectNode binding(){var c=context.get();return StrictJson.object().put("game_pid",c.before().game().pid()).put("native_revision",c.before().frame().identity().nativeRevision()).put("connection_generation",c.connectionGeneration()).put("played_character_id",c.before().frame().identity().player()).put("date_raw",c.before().frame().identity().dateRaw());}
  ObjectNode model(boolean selected){var c=context.get();var r=binding().put("schema","ck3-ingame-decision-item-v1").put("step","query-ingame-decision-item-v1").put("read_only",true).put("game_version",c.build().version()).put("executable_sha256",c.build().sha256()).put("available",true).put("unavailable_reason","")
   .put("decision_key",KEY).put("group_count",1).put("row_count",1).put("matching_row_count",1).put("row_context_reference_key",c.before().frame().identity().player()).put("row_scope_reference_available",true)
   .put("detail_tree_complete",true).put("detail_root_visible",selected).put("detail_definition_available",selected).put("detail_definition_matches_target",selected).put("detail_decision_key",selected?KEY:"")
   .put("detail_actor_binding_verified",selected).put("detail_actor_reference_key",selected?c.before().frame().identity().player():BigInteger.valueOf(-1)).put("row_widget_datacontext_verified",false).put("action_qualified",false);
   for(String field:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","decisions_tree_complete","decisions_root_visible","row_owner_verified"))r.put(field,true);return r;
  }
  ObjectNode ack(String step){var c=context.get();boolean select=method==Method.SELECT_DECISION,generic=method==Method.CONFIRM_OUTCOME;
   var r=binding().put("schema",generic?"ck3-ingame-decision-outcome-confirm-v1":"ck3-ingame-decision-item-action-v1").put("step",step).put("action",select?"select":generic?"confirm_outcome":"confirm").put("decision_key",KEY).put("game_version",c.build().version()).put("executable_sha256",c.build().sha256()).put("unavailable_reason","")
    .put("dispatch_invoked",true).put("native_call_completed",select).put("before_already_selected",false).put("native_handled",false).put("native_after_read",true).put("selected_after_verified",false).put("inner_modal_visible",false).put("inner_modal_tree_complete",true).put("postcondition_verified",false).put("verification_pending",true).put("detail_actor_binding_verified",!select).put("no_blocking_modal_verified",method!=Method.CONFIRM_ITEM).put("status","acknowledged_verification_pending");
   for(String field:List.of("owner_thread_verified","source_abi_pins_verified","action_abi_pins_verified","receiver_qualified","gui_owner_binding_verified","frame_verified"))r.put(field,true);
   r.set("before_actual_model",model(!select));r.putObject("after_actual_model").put("available",false).put("unavailable_reason","actual row disappeared after take");
   if(generic)r.put("expected_outcome","decision_closed").put("expected_event_definition_key","");return r;
  }
  ObjectNode tree(){GuiModels.TreeKind kind=method==Method.CONFIRM_ITEM?GuiModels.TreeKind.WHITE:GuiModels.TreeKind.DECISION_DETAIL;
   var r=StrictJson.object().put("step","inspect-gui-window-tree-v1").put("scope_root_name",kind.root()).put("accepted",true).put("root_available",true).put("truncated",false).put("status","available").put("widget_count",method==Method.CONFIRM_ITEM?2:1);
   if(rootAbsent){r.put("root_available",false).put("status","unavailable").put("widget_count",0);r.putArray("widgets");return r;}
   var rows=r.putArray("widgets");boolean rootVisible=method==Method.CONFIRM_ITEM||!afterMatches;
   rows.addObject().put("runtime_name",kind.root()).put("child_path","").put("depth",0).put("child_count",method==Method.CONFIRM_ITEM?1:0).put("vtable_rva",4096).put("effective_visible",rootVisible).put("enabled",rootVisible);
   if(method==Method.CONFIRM_ITEM)rows.addObject().put("runtime_name","ervc_courtier_creator_modal").put("child_path","0").put("depth",1).put("child_count",0).put("vtable_rva",8192).put("effective_visible",afterMatches).put("enabled",afterMatches);return r;
  }
  ActionReply execute()throws Exception{return fixture.writer.locked(same->{var original=(ActionReply)service.invoke(request,invocation);return new ActionReply(original.receipt(),original.archivedReceipt(),original.originalReference(),Optional.of(beforeSource),original.parsedReturnReference());});}
  ObjectNode present(ActionReply reply)throws Exception{
   final Optional<RawJson> snapshotAfter=reply.receipt().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&method==Method.CONFIRM_OUTCOME?Optional.of(PublicDataJson.encodeFullMaterial(fixture.ready().request().observations().snapshot())):Optional.empty();
   return fixture.writer.locked(same->{
    var archive=fixture.archive.withSession(same);Optional<RawJson> later=Optional.empty(),after=Optional.empty();
    if(reply.receipt().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED){var settled=(ActionState.Settled)reply.receipt().state();var control=(ActionState.ControlApplied)settled.settlement();later=Optional.of(GuiCodec.encode(new ReadReply(control.read(),archive.readReferenceOf(control.read()),Optional.empty(),Optional.empty())));after=snapshotAfter;}
    return PublicDataJson.object(GuiPublicBinder.action(request,reply,new GuiPublicBinder.Before(context.get(),beforeSource),later,after,Optional.empty()));
   });
  }
  @Override public void close()throws Exception{fixture.close();}
 }
 @Test void originalDecisionCallbacksNeedActualSelectedModalOrClosedAfterAndReplaySameAck()throws Exception{
  for(Method method:List.of(Method.SELECT_DECISION,Method.CONFIRM_ITEM,Method.CONFIRM_OUTCOME))try(var run=new Run(root.resolve("success-"+method),method,true,ignored->{},false)){
   var reply=run.execute();assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,reply.receipt().outcome());assertEquals(1,run.dispatches.get());assertEquals(2,run.fixture.scenarioReadWrites());
   run.fixture.writer.locked(same->{var archive=run.fixture.archive.withSession(same);byte[] bytes=ActionReceiptCodec.encodeReceipt(reply.receipt(),archive);var reopened=ActionReceiptCodec.decodeReceipt(bytes,archive);assertEquals(reply.receipt(),reopened);int reads=run.fixture.scenarioReadWrites();run.ports.replay(same.head(),reopened,archive);assertEquals(reads,run.fixture.scenarioReadWrites());return null;});
   var output=run.present(reply);assertTrue(output.path("postcondition_verified").booleanValue());assertFalse(output.path("verification_pending").booleanValue());assertEquals(1,run.fixture.nativeActionWrites());
   if(method==Method.CONFIRM_OUTCOME){assertFalse(output.path("business_effects_verified").booleanValue());assertFalse(output.path("full_product_acceptance_credit").booleanValue());assertFalse(output.path("event_option_selection_authorized").booleanValue());}
  }
 }
 @Test void invalidDecisionReceiverAckNeverQueriesAfterOrBecomesCompleteOnReconcile()throws Exception{
  int index=0;
  for(Method method:List.of(Method.SELECT_DECISION,Method.CONFIRM_ITEM,Method.CONFIRM_OUTCOME)){
   List<Consumer<ObjectNode>> changes=new ArrayList<>();changes.add(r->r.put("receiver_qualified",false));changes.add(r->r.put("game_pid",true));changes.add(r->r.remove("action_abi_pins_verified"));
   if(method==Method.SELECT_DECISION)changes.add(r->r.put("before_already_selected",true));
   else changes.add(r->((ObjectNode)r.get("before_actual_model")).put("detail_root_visible",false));
   if(method==Method.CONFIRM_OUTCOME){changes.add(r->r.put("no_blocking_modal_verified",false));changes.add(r->r.put("expected_outcome","event_window"));}
   for(var change:changes)try(var run=new Run(root.resolve("bad-ack-"+(index++)),method,true,change,false)){
    var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());assertInstanceOf(ActionState.Unknown.class,reply.receipt().state());assertEquals(1,run.fixture.scenarioReadWrites(),"invalid original ACK must fail before any after READ");
    var output=run.present(reply);assertFalse(output.has("later_actual_observation"));assertFalse(output.has("snapshot_after"));assertEquals("unresolved",output.path("canonical_gui_action").path("outcome").textValue());
    assertEquals(reply.receipt(),run.fixture.reopenAndReturnExisting(reply.receipt().command()));
    run.fixture.writer.locked(same->{assertEquals(ActionReceipt.Outcome.UNRESOLVED,run.fixture.coordinator.reconcile(same,reply.receipt().command().actionId()).outcome());return null;});
    assertEquals(1,run.dispatches.get());assertEquals(1,run.fixture.nativeActionWrites());assertEquals(1,run.fixture.scenarioReadWrites());
   }
  }
 }
 @Test void validAckWithoutActualUiAfterAndLostAckRemainUnknownWithoutSecondCallback()throws Exception{
  for(Method method:List.of(Method.SELECT_DECISION,Method.CONFIRM_ITEM,Method.CONFIRM_OUTCOME))try(var run=new Run(root.resolve("no-after-"+method),method,false,ignored->{},false)){
   var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());assertEquals(2,run.fixture.scenarioReadWrites());assertFalse(run.present(reply).has("later_actual_observation"));assertEquals(1,run.fixture.nativeActionWrites());
  }
  try(var run=new Run(root.resolve("lost-ack"),Method.CONFIRM_OUTCOME,true,ignored->{},true)){
   var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());assertEquals(1,run.fixture.scenarioReadWrites());
   assertEquals(reply.receipt(),run.fixture.reopenAndReturnExisting(reply.receipt().command()));
   run.fixture.writer.locked(same->{run.fixture.coordinator.reconcile(same,reply.receipt().command().actionId());return null;});assertEquals(1,run.dispatches.get());assertEquals(1,run.fixture.nativeActionWrites());
  }
 }
 @Test void absentDecisionRootIsUnavailableAndCannotBeObservedClosed()throws Exception{
  try(var run=new Run(root.resolve("absent-root"),Method.CONFIRM_OUTCOME,true,ignored->{},false)){
   run.rootAbsent=true;var reply=run.execute();assertEquals(ActionReceipt.Outcome.UNRESOLVED,reply.receipt().outcome());assertEquals(2,run.fixture.scenarioReadWrites());assertFalse(run.present(reply).has("snapshot_after"));assertEquals(1,run.fixture.nativeActionWrites());
  }
 }
}
