package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.xar.ck3.control.nativebridge.NativeWire;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.*;

/** Root installs these preparation/postcondition handlers in its existing unique coordinator, never a second submitter. */
public final class ChinaCasesActions implements ActionPorts.PreparationPort,ActionPorts.PostconditionPort {
public static final String REVIEW="activate-zhongguo-review-now-v1", SCOREBOARD="activate-zhongguo-scoreboard-v1";
public static final String REVIEW_SCHEMA="china-cases/review-now-post/v1", SCOREBOARD_SCHEMA="china-cases/scoreboard-post/v1";
public enum ScoreboardAction { OPEN,SWITCH_MANAGED,SWITCH_RECEIVED,SWITCH_SYSTEM,CLOSE,REOPEN;
public String wire() { return name().toLowerCase(Locale.ROOT).replace('_','-'); }
}
public record ProviderBinding(String sessionId,BigInteger observationSequence,BigInteger stateRevision,String treeFingerprint,String semanticFingerprint) {
public ProviderBinding { check(sessionId!=null&&sessionId.matches("[0-9A-F]{32}"),"provider session");positive(observationSequence);positive(stateRevision);fingerprint(treeFingerprint);fingerprint(semanticFingerprint); }
}
public record Pointer(String value) { public Pointer { check(value!=null&&value.matches("0x[0-9A-F]+"),"uppercase native pointer"); } }
public record ReviewRequest(Nonce nonce,BigInteger sourceQuerySequence,BigInteger nativeRevision,BigInteger generation,CharacterId player) {
public ReviewRequest { Objects.requireNonNull(nonce);positive(sourceQuerySequence);positive(nativeRevision);positive(generation);Objects.requireNonNull(player); }
public OpportunityJson.Obj arguments() {
ObjectNode n=base(nonce,sourceQuerySequence,nativeRevision,generation,player);return immutable(n);
}
}
public record ScoreboardRequest(Nonce nonce,ScoreboardAction action,BigInteger publicRevision,BigInteger nativeRevision,
BigInteger generation,CharacterId player,ProviderBinding provider,Pointer window,Pointer target,Pointer vtable) {
public ScoreboardRequest { Objects.requireNonNull(nonce);Objects.requireNonNull(action);check(publicRevision!=null&&publicRevision.signum()>=0&&publicRevision.compareTo(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX)<=0,"public uint64");positive(nativeRevision);positive(generation);Objects.requireNonNull(player);Objects.requireNonNull(provider);Objects.requireNonNull(window);Objects.requireNonNull(target);Objects.requireNonNull(vtable); }
public OpportunityJson.Obj arguments() {
ObjectNode n=base(nonce,publicRevision,nativeRevision,generation,player);n.put("action",action.wire());
n.put("expected_provider_session_id",provider.sessionId());n.put("expected_observation_sequence",provider.observationSequence());n.put("expected_observed_state_revision",provider.stateRevision());
n.put("expected_tree_fingerprint_v1",provider.treeFingerprint());n.put("expected_semantic_fingerprint_v1",provider.semanticFingerprint());
n.put("expected_window_instance_pointer",window.value());n.put("expected_target_instance_pointer",target.value());n.put("expected_target_vtable_pointer",vtable.value());return immutable(n);
}
}
private final ChinaCasesFacade queries;
private final Function<ActionCommand,ChinaCasesFacade.Context> freshContext;
private final ActionPorts.OutcomeArchive archive;
public ChinaCasesActions(ChinaCasesFacade queries,Function<ActionCommand,ChinaCasesFacade.Context> freshContext,ActionPorts.OutcomeArchive archive) {
this.queries=Objects.requireNonNull(queries);this.freshContext=Objects.requireNonNull(freshContext);this.archive=Objects.requireNonNull(archive);
}
private static void positive(BigInteger value) { check(value!=null&&value.signum()>0&&value.compareTo(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX)<=0,"positive uint64"); }
private static void fingerprint(String value) { check(value!=null&&value.matches("[0-9A-F]{64}"),"uppercase SHA256 fingerprint"); }
private static OpportunityJson.Obj immutable(ObjectNode node) { return (OpportunityJson.Obj)OpportunityJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(node)); }
private static ObjectNode base(Nonce nonce,BigInteger revision,BigInteger nativeRevision,BigInteger generation,CharacterId player) {
ObjectNode n=org.xar.ck3.control.contracts.StrictJson.object();n.put("request_nonce",nonce.value());n.put("expected_public_revision",revision);n.put("expected_native_revision",nativeRevision);n.put("expected_connection_generation",generation);n.put("expected_player_character_id",player.value());return n;
}
private static ObjectNode args(ActionCommand c) { return (ObjectNode)OpportunityJson.toNode(c.arguments()); }
public static ReviewRequest reviewRequest(ActionCommand c) {
check(c.operation().value().equals(REVIEW),"review operation mismatch");ObjectNode n=exact(args(c),Set.of("request_nonce","expected_public_revision","expected_native_revision","expected_connection_generation","expected_player_character_id"));
ReviewRequest r=new ReviewRequest(new Nonce(text(n.get("request_nonce"))),uint64(n.get("expected_public_revision"),true),uint64(n.get("expected_native_revision"),true),uint64(n.get("expected_connection_generation"),true),character(n.get("expected_player_character_id")));
check(c.before().frame().identity().nativeRevision().equals(r.nativeRevision())&&c.before().frame().identity().player().equals(r.player().integer()),"review original frame binding");return r;
}
public static ScoreboardRequest scoreboardRequest(ActionCommand c) {
check(c.operation().value().equals(SCOREBOARD),"scoreboard operation mismatch");ObjectNode n=exact(args(c),Set.of("request_nonce","action","expected_public_revision","expected_native_revision","expected_connection_generation","expected_player_character_id","expected_provider_session_id","expected_observation_sequence","expected_observed_state_revision","expected_tree_fingerprint_v1","expected_semantic_fingerprint_v1","expected_window_instance_pointer","expected_target_instance_pointer","expected_target_vtable_pointer"));
ScoreboardRequest r=new ScoreboardRequest(new Nonce(text(n.get("request_nonce"))),enumeration(n.get("action"),ScoreboardAction.class),uint64(n.get("expected_public_revision"),false),uint64(n.get("expected_native_revision"),true),uint64(n.get("expected_connection_generation"),true),character(n.get("expected_player_character_id")),
new ProviderBinding(text(n.get("expected_provider_session_id")),uint64(n.get("expected_observation_sequence"),true),uint64(n.get("expected_observed_state_revision"),true),text(n.get("expected_tree_fingerprint_v1")),text(n.get("expected_semantic_fingerprint_v1"))),
new Pointer(text(n.get("expected_window_instance_pointer"))),new Pointer(text(n.get("expected_target_instance_pointer"))),new Pointer(text(n.get("expected_target_vtable_pointer"))));
check(c.before().frame().revision().equals(r.publicRevision())&&c.before().frame().identity().nativeRevision().equals(r.nativeRevision())&&c.before().frame().identity().player().equals(r.player().integer()),"scoreboard original frame binding");
check(r.action().wire().equals(text(n.get("action"))),"canonical action token");check(r.action()!=ScoreboardAction.REOPEN,"reopen requires reviewed two-phase close/open sequence; no duplicate primitive");return r;
}
private static void bound(ActionCommand c,PlanningReadReceipt source,BigInteger generation) {
check(c.before().equals(source.request().before())&&c.source().equals(source.request().source())&&c.sessionId().equals(source.request().sessionId())&&source.before().binding().connectionGeneration().equals(generation),"action source differs from original bound query");
}
private static boolean visible(ProgressFrame f,int index) { return f.widgets().get(index).effectiveVisible().optional().orElse(false); }
private static boolean visible(Widget w) { return w.effectiveVisible().required(); }
private static Widget widget(ScoreboardFrame f,String id) { return f.widgets().stream().filter(w->w.stableIdentity().equals(id)).findFirst().orElseThrow(); }
public static void validateReview(ActionCommand c,PlanningReadResult.Known<ProgressFrame> source) {
ReviewRequest r=reviewRequest(c);ProgressFrame s=ChinaCasesCodec.decodeProgressFrame(source.receipt());
check(s.equals(source.value()),"review supplied projection differs from original");bound(c,source.receipt(),r.generation());
check(s.header().status()==Status.AVAILABLE&&visible(s,1)&&!visible(s,2)&&!visible(s,3)&&!visible(s,4),"review-now ineligible");
check(ChinaCasesCodec.querySequence(source.receipt(),Family.PROGRESS).equals(r.sourceQuerySequence()),"review source query sequence changed");
check(c.expected().observerSchema().equals(REVIEW_SCHEMA)&&c.expected().values().equals(reviewExpected()),"review expected contract changed");
}
public static void validateScoreboard(ActionCommand c,PlanningReadResult.Known<ScoreboardFrame> source) {
ScoreboardRequest r=scoreboardRequest(c);ScoreboardFrame s=ChinaCasesCodec.decodeScoreboardFrame(source.receipt());
check(s.equals(source.value()),"scoreboard supplied projection differs from original");bound(c,source.receipt(),r.generation());check(s.header().status()==Status.AVAILABLE,"scoreboard source unavailable");
check(r.provider().equals(new ProviderBinding(s.providerSessionId(),s.observationSequence(),s.observedStateRevision(),s.treeFingerprintV1(),s.semanticFingerprintV1())),"scoreboard provider binding changed");
check(s.readiness().playerBindingReady()&&s.readiness().guiRootReady()&&s.readiness().entryWindowStateReady()&&s.readiness().aclReady()&&s.readiness().sameFrameReady()&&s.readiness().stateAclQueryReady(),"scoreboard source gate");
check(r.provider().observationSequence().compareTo(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX)<0&&r.provider().stateRevision().compareTo(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX)<0,"provider revision overflow");
var window=widget(s,"zg361_scoreboard_window");check(window.exists().required()&&window.instancePointer().required().equals(r.window().value()),"scoreboard window pointer");
boolean modal=visible(widget(s,"zg361_scoreboard_modal"));String target;String tab="";
if(r.action()==ScoreboardAction.OPEN){check(!modal,"scoreboard already open");var entries=s.widgets().stream().filter(w->w.stableIdentity().startsWith("zg361_scoreboard_entry_")&&w.effectiveVisible().optional().orElse(false)).toList();check(entries.size()==1,"entry target not unique");target=entries.get(0).stableIdentity();tab=target.substring("zg361_scoreboard_entry_".length());}
else if(r.action()==ScoreboardAction.CLOSE){check(modal,"scoreboard not open");target="zg361_scoreboard_header_close";}
else {check(modal,"scoreboard not open");tab=r.action().wire().substring(7);target="zg361_scoreboard_tab_"+tab;
check(!visible(widget(s,"zg361_scoreboard_page_"+tab)),"scoreboard no-op");
if(tab.equals("managed"))check(s.acl().managed().currentPlayerCanAssessOthers(),"managed ACL denied");
if(tab.equals("received"))check(s.acl().receivedSelf().surfaceAvailable(),"received ACL denied");}
var w=widget(s,target);check(w.exists().required()&&visible(w)&&w.enabled().required()&&w.instancePointer().required().equals(r.target().value())&&w.vtablePointer().required().equals(r.vtable().value())&&w.runtimeName().equals(target),"target exact paused eligibility");
check(c.expected().observerSchema().equals(SCOREBOARD_SCHEMA)&&c.expected().values().equals(scoreboardExpected(r.action()!=ScoreboardAction.CLOSE,tab)),"scoreboard expected contract changed");
}
public static List<ExpectedValue> reviewExpected() { return List.of(new ExpectedBoolean(new FieldKey("played_owner_b1_active"),true)); }
public static List<ExpectedValue> scoreboardExpected(boolean modal,String tab) { return List.of(new ExpectedBoolean(new FieldKey("scoreboard_modal_effective_visible"),modal),new ExpectedText(new FieldKey("scoreboard_active_tab"),tab)); }
@Override public NativeRequest prepare(ActionCommand c) {
String capability;
if(c.operation().value().equals(REVIEW)){reviewRequest(c);check(c.expected().observerSchema().equals(REVIEW_SCHEMA),"review observer schema");capability="game.contract.zhongguo-review-now-action-v1-fail-closed";ChinaCasesSources.verify(Family.PROGRESS);}
else {scoreboardRequest(c);check(c.expected().observerSchema().equals(SCOREBOARD_SCHEMA),"scoreboard observer schema");capability="game.contract.zhongguo-scoreboard-action-v1-fail-closed";ChinaCasesSources.verify(Family.SCOREBOARD);}
return new NativeRequest(c.operation().value(),capability,new RawJson(OpportunityJson.encode(c.arguments())));
}
private static boolean production(ActionState.Attempt a,String cap) {
try {var r=a.guard().capabilityEvidence();byte[] b=Files.readAllBytes(Path.of(r.path()));
check(b.length==r.bytes()&&HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)).equals(r.sha256()),"capability evidence drift");
var h=(NativeWire.Hello)NativeWire.decode(b);check(h.connectionGeneration().equals(a.guard().connectionGeneration()),"hello generation drift");return h.capabilities().contains(cap);
}catch(java.io.IOException|java.security.NoSuchAlgorithmException e){throw new IllegalStateException("original hello unavailable",e);}
}
private static void checkedAck(ActionCommand c,ObjectNode result,ObjectNode request,boolean review) {
ObjectNode a=exact(result.get("action_ack"),review?Set.of("schema_version","status","accepted","capability","step","request_nonce","source","target","expected_postcondition","native_handled","postcondition_verified"):
Set.of("schema_version","status","accepted","capability","step","request_nonce","action","source","target","expected_postcondition","native_handled","postcondition_verified","provenance"));
check(integer(a.get("schema_version")).equals(BigInteger.ONE)&&text(a.get("status")).equals("acknowledged_verification_pending")&&bool(a.get("accepted"))&&text(a.get("capability")).equals("game.command."+c.operation().value())&&text(a.get("step")).equals(c.operation().value())&&text(a.get("request_nonce")).equals(text(request.get("request_nonce")))&&bool(a.get("native_handled"))&&!bool(a.get("postcondition_verified")),"pending ACK contract drift");
ObjectNode s=exact(a.get("source"),review?Set.of("revision","native_revision","connection_generation","date_raw","player_character_id"):Set.of("revision","native_revision","connection_generation","date_raw","player_character_id","provider_session_id","observation_sequence","observed_state_revision","tree_fingerprint_v1","semantic_fingerprint_v1","window_instance_pointer"));
for(String pair:List.of("revision:expected_public_revision","native_revision:expected_native_revision","connection_generation:expected_connection_generation","player_character_id:expected_player_character_id")){String[] p=pair.split(":");check(integer(s.get(p[0])).equals(integer(request.get(p[1]))),"ACK source binding changed");}
check(integer(s.get("date_raw")).equals(c.before().frame().identity().dateRaw()),"ACK date changed");
ObjectNode t=exact(a.get("target"),Set.of("stable_identity","runtime_name","instance_pointer","vtable_pointer"));String target=text(t.get("stable_identity"));check(text(t.get("runtime_name")).equals(target),"ACK target identity");
new Pointer(text(t.get("instance_pointer")));new Pointer(text(t.get("vtable_pointer")));
ObjectNode p=(ObjectNode)a.get("expected_postcondition");
if(review){exact(p,Set.of("requires_independent_progress_query","predicate"));check(target.equals("zg361_promotion_source_review_now_action")&&bool(p.get("requires_independent_progress_query"))&&text(p.get("predicate")).equals("played_owner_b1_active_on_independent_paused_progress_query"),"review ACK predicate drift");return;}
check(text(a.get("action")).equals(text(request.get("action"))),"ACK action drift");
for(String pair:List.of("provider_session_id:expected_provider_session_id","observation_sequence:expected_observation_sequence","observed_state_revision:expected_observed_state_revision","tree_fingerprint_v1:expected_tree_fingerprint_v1","semantic_fingerprint_v1:expected_semantic_fingerprint_v1","window_instance_pointer:expected_window_instance_pointer")){String[] keys=pair.split(":");check(s.get(keys[0]).equals(request.get(keys[1])),"ACK provider binding drift");}
check(t.get("instance_pointer").equals(request.get("expected_target_instance_pointer"))&&t.get("vtable_pointer").equals(request.get("expected_target_vtable_pointer")),"ACK target pointer drift");
String action=text(request.get("action"));String tab=action.startsWith("switch-")?action.substring(7):action.equals("close")?"":target.replace("zg361_scoreboard_entry_","");
check(action.startsWith("switch-")?target.equals("zg361_scoreboard_tab_"+tab):action.equals("close")?target.equals("zg361_scoreboard_header_close"):List.of("managed","received","system").contains(tab),"ACK target outside allowlist");
exact(p,Set.of("requires_independent_query","minimum_observation_sequence","minimum_observed_state_revision","expected_provider_session_id","expected_tree_fingerprint_v1","modal_effective_visible","active_tab","list_view_required","expected_window_instance_pointer"));
check(bool(p.get("requires_independent_query"))&&uint64(p.get("minimum_observation_sequence"),true).equals(integer(s.get("observation_sequence")).add(BigInteger.ONE))&&uint64(p.get("minimum_observed_state_revision"),true).equals(integer(s.get("observed_state_revision")).add(BigInteger.ONE))&&p.get("expected_provider_session_id").equals(s.get("provider_session_id"))&&p.get("expected_tree_fingerprint_v1").equals(s.get("tree_fingerprint_v1"))&&p.get("expected_window_instance_pointer").equals(s.get("window_instance_pointer"))&&bool(p.get("modal_effective_visible"))==!action.equals("close")&&bool(p.get("list_view_required"))==!action.equals("close")&&(tab.isEmpty()?p.get("active_tab").isNull():text(p.get("active_tab")).equals(tab)),"ACK expected postcondition drift");
ObjectNode provenance=exact(a.get("provenance"),Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","contract_stage"));
check(text(provenance.get("game_version")).equals("1.19.0.6")&&text(provenance.get("executable_sha256")).equals("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86")&&text(provenance.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1")&&text(provenance.get("consumer_id")).equals("xar-autoplayer-zhongguo-scoreboard-action-v1")&&text(provenance.get("allowlist_id")).equals("zg361-scoreboard-named-widget-action-v1")&&text(provenance.get("contract_stage")).equals("exact_dispatch_ack_provider_revision_live_unverified"),"ACK provenance drift");
}
@Override public ActionPorts.PostconditionResult observe(ActionCommand c,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk())return new ActionPorts.Pending("original native result unavailable; no replay",List.of());
boolean review=c.operation().value().equals(REVIEW);check(review||c.operation().value().equals(SCOREBOARD),"unregistered ZhongGuo mutation");
ObjectNode result=parse(ack.originalResultToken().orElseThrow());exact(result,review?Set.of("step","accepted","status","request_nonce","action_sequence","snapshot_revision","rejection_reason","action_ack","production_capability_advertised","backend_id"):Set.of("step","accepted","status","request_nonce","action","action_sequence","snapshot_revision","rejection_reason","action_ack","production_capability_advertised","backend_id"));
ObjectNode request=args(c);check(text(result.get("step")).equals(c.operation().value())&&text(result.get("request_nonce")).equals(text(request.get("request_nonce")))&&uint64(result.get("snapshot_revision"),true).equals(c.before().frame().identity().nativeRevision()),"action result binding");
uint64(result.get("action_sequence"),true);check(text(result.get("backend_id")).equals("native-headless"),"action backend drift");boolean advertised=bool(result.get("production_capability_advertised"));if(review)check(!advertised,"review production falsely advertised");else check(advertised==production(attempt,"game.command.activate-zhongguo-scoreboard-v1"),"production capability mirror drift");
if(!bool(result.get("accepted"))){check(text(result.get("status")).equals("unavailable")&&result.get("action_ack").isNull()&&!advertised&&!text(result.get("rejection_reason")).isEmpty(),"native rejection malformed");return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),text(result.get("rejection_reason")),archive.referenceOf(dispatch)));}
check(text(result.get("status")).equals("acknowledged_verification_pending")&&result.get("rejection_reason").isNull(),"ACK is not pending");
checkedAck(c,result,request,review);
var context=Objects.requireNonNull(freshContext.apply(c));check(context.sessionId().equals(c.sessionId()),"post read session changed");
Nonce postNonce=new Nonce("post:"+attempt.requestId().substring(0,Math.min(56,attempt.requestId().length())));
if(review){ReviewRequest r=reviewRequest(c);var after=queries.query_zhongguo_promotion_source_progress_v1(context,postNonce);
if(!(after instanceof PlanningReadResult.Known<ProgressFrame> known))return new ActionPorts.Pending("independent progress unavailable",List.of());
ProgressFrame p=known.value();check(ChinaCasesCodec.querySequence(known.receipt(),Family.PROGRESS).compareTo(r.sourceQuerySequence())>0&&known.receipt().before().binding().connectionGeneration().equals(r.generation())&&p.header().player().equals(r.player())&&visible(p,2)&&!visible(p,1),"independent progress did not prove B1 entry");
return new ActionPorts.ControlObserved(new ActionState.ControlApplied(known.receipt(),REVIEW_SCHEMA,reviewExpected()));}
ScoreboardRequest r=scoreboardRequest(c);check(text(result.get("action")).equals(r.action().wire()),"action name drift");
var after=queries.query_zhongguo_scoreboard_state_v1(context,postNonce);
if(!(after instanceof PlanningReadResult.Known<ScoreboardFrame> known))return new ActionPorts.Pending("independent scoreboard unavailable",List.of());
ScoreboardFrame p=known.value();check(p.header().status()==Status.AVAILABLE&&p.header().nativeRevision().equals(r.nativeRevision())&&p.header().player().equals(r.player())&&known.receipt().before().binding().connectionGeneration().equals(r.generation())&&context.before().frame().revision().equals(r.publicRevision())&&p.providerSessionId().equals(r.provider().sessionId())&&p.observationSequence().compareTo(r.provider().observationSequence())>0&&p.observedStateRevision().compareTo(r.provider().stateRevision())>0&&p.treeFingerprintV1().equals(r.provider().treeFingerprint())&&!p.semanticFingerprintV1().equals(r.provider().semanticFingerprint())&&!p.header().nonce().equals(r.nonce())&&widget(p,"zg361_scoreboard_window").instancePointer().required().equals(r.window().value()),"independent scoreboard provider binding failed");
boolean modal=visible(widget(p,"zg361_scoreboard_modal"));List<String> pages=List.of("managed","received","system").stream().filter(tab->visible(widget(p,"zg361_scoreboard_page_"+tab))).toList();
check(modal==(r.action()!=ScoreboardAction.CLOSE)&&(modal?pages.size()==1:pages.isEmpty()),"scoreboard modal/page postcondition");String tab=pages.isEmpty()?"":pages.get(0);
if(r.action().wire().startsWith("switch-"))check(tab.equals(r.action().wire().substring(7)),"scoreboard tab changed");
check(c.before().frame().identity().dateRaw().equals(BigInteger.valueOf(p.header().dateRaw())),"scoreboard date changed");
return new ActionPorts.ControlObserved(new ActionState.ControlApplied(known.receipt(),SCOREBOARD_SCHEMA,scoreboardExpected(modal,tab)));
}
}

