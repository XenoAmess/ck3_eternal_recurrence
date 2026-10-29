package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.*;

/** Semantic joins are checked independently of a transport ACK; no caller-supplied readiness grants permission. */
final class ChinaCasesSemantics {
private ChinaCasesSemantics() { }
private static boolean all(Field<?>... fields) { return java.util.Arrays.stream(fields).allMatch(Field::available); }
private static boolean eq(Field<?> field,Object value) { return field.optional().map(value::equals).orElse(false); }
private static boolean n(Field<BigInteger> field,long value) { return eq(field,BigInteger.valueOf(value)); }
private static boolean range(Field<BigInteger> f,long low,long high) { return f.optional().map(v->v.compareTo(BigInteger.valueOf(low))>=0 && v.compareTo(BigInteger.valueOf(high))<=0).orElse(false); }
private static boolean unavailable(Field<?> field,String reason) { return field instanceof Unavailable<?> u && u.reason().equals(reason); }
private static boolean absentFalse(Field<Boolean> f) { return eq(f,false)||unavailable(f,"variable_absent"); }
private static boolean absentZero(Field<BigInteger> f) { return n(f,0)||unavailable(f,"variable_absent"); }
private static void noValues(JsonNode node,String reason) {
if(node.isObject() && node.has("value") && node.has("unavailable_reason") && node.has("status")) {
check(text(node.get("status")).equals("unavailable") && node.get("value").isNull(),"unavailable frame leaks semantic values");
if(reason!=null)check(text(node.get("unavailable_reason")).equals(reason),"unavailable field reason differs");
} else if(node.isContainerNode()) for(JsonNode child:node)noValues(child,reason);
}
private static void aggregate(ObjectNode frame,Set<String> excluded) {
JsonNode r=frame.get("readiness"); boolean ready=true;
for(var it=r.properties().iterator();it.hasNext();) { var e=it.next(); if(!e.getKey().equals("ready")&&!excluded.contains(e.getKey()))ready &= bool(e.getValue()); }
check(bool(r.get("ready"))==ready,"ready aggregate disagrees");
}
/** The original unavailable flow has an exact diagnostic tuple, not merely ready=false. */
private static void unavailableReadiness(ObjectNode frame,Set<String> sameFrameReasons) {
boolean sameFrame=sameFrameReasons.contains(text(frame.get("unavailable_reason")));
ObjectNode readiness=(ObjectNode)frame.get("readiness");
for(var iterator=readiness.properties().iterator();iterator.hasNext();) {
var field=iterator.next();boolean expected=field.getKey().equals("same_frame_ready")&&sameFrame;
check(bool(field.getValue())==expected,"unavailable frame fabricates component readiness: "+field.getKey());
}
}
static void verify(Frame value,PlanningReadReceipt receipt) {
ObjectNode args=(ObjectNode)OpportunityJson.toNode(receipt.request().arguments());
var h=value.header(); CharacterId player=h.player();
switch(value) {
case B1Frame f -> {
check(f.managerCharacterId().equals(player),"played manager changed");
if(h.status()==Status.AVAILABLE)check(f.readiness().ready() && all(f.cycle().cycleSerial(),f.cycle().caseSerial(),f.cycle().state(),f.cycle().active()) && range(f.cycle().state(),1,8),"available B1 identity incomplete");
else check(!f.readiness().ready(),"unavailable B1 leaks ready");
}
case CaseFrame f -> verifyCase(f,args,receipt);
case AiOwnedFrame f -> verifyAi(f,args,receipt);
case ResultFrame f -> verifyResult(f,args,receipt);
case PipFrame f -> verifyPip(f,args,receipt);
case PromotionFrame f -> {
check(character(args.get("owner_character_id")).equals(player),"promotion owner must be player");
var p=f.promotionCompensation(); check(p.frozenCase().frozen(),"case is not frozen");
aggregate(envelope(receipt,Family.PROMOTION),Set.of());
}
case Af5Frame f -> {
check(character(args.get("owner_character_id")).equals(player),"AF5 owner must be player");
aggregate(envelope(receipt,Family.AF5),Set.of()); check(!f.terminal()||f.readiness().ready(),"terminal AF5 is not observable");
}
case ProjectsFrame f -> {
check(f.requestedOwnerCharacterId().equals(character(args.get("owner_character_id"))) && f.requestedSubjectCharacterId().equals(character(args.get("subject_character_id"))),"project owner/subject changed");
check(!f.requestedOwnerCharacterId().equals(f.requestedSubjectCharacterId()) && (player.equals(f.requestedOwnerCharacterId())||player.equals(f.requestedSubjectCharacterId())),"project player binding");
check(f.creditProjectPortfolio().providerObserved() && f.projectsMetrics().contribution().providerObserved() && f.projectsMetrics().metricsResult().providerObserved(),"project producer observation missing");
check(f.sourceIdentity().equals(f.projectsMetrics().sourceIdentity()) && f.resultIdentity().equals(f.projectsMetrics().resultIdentity()),"project identities disagree");
aggregate(envelope(receipt,Family.PROJECTS),Set.of());
var r=f.readiness(); if(h.status()==Status.AVAILABLE) {
check(f.checkpointState()!=CheckpointState.UNAVAILABLE && r.ownerBindingReady() && r.portfolioObserved() && r.sourceIdentityReady() && r.contributionReady() && r.sameFrameReady(),"project direct source missing");
if(f.checkpointState()==CheckpointState.CP26_READY_P3_ABSENT)check(!(r.resultIdentityReady()||r.metricsReady()||r.sameProjectCaseIdentity()||r.receiptLineageReady()||r.resultOperationCommitted()||r.ready()),"CP26 exposes nonexistent P3");
if(f.checkpointState()==CheckpointState.P3_RESULT_COMMITTED)check(r.ready(),"committed project is not ready");
} else check(f.checkpointState()==CheckpointState.UNAVAILABLE,"unavailable project state changed");
}
case IncidentFrame f -> verifyIncident(f,args,receipt);
case ScoreboardFrame f -> verifyScoreboard(f);
case ProgressFrame f -> {
check(character(args.get("owner_character_id")).equals(player),"progress owner is not played");
check(h.sourceBackendId().equals("ck3-1.19.0.6-native-zhongguo-promotion-source-progress-v1"),"progress backend drift");
var identities=PROGRESS_WIDGETS;
check(f.widgets().size()==identities.size(),"progress widget set incomplete");
for(int i=0;i<identities.size();i++)check(f.widgets().get(i).stableIdentity().equals(identities.get(i)) && f.widgets().get(i).runtimeName().equals(identities.get(i)),"progress fixed widget identity");
}
}
if(value instanceof PromotionFrame)check(h.sourceBackendId().equals("ck3-1.19.0.6-native-zhongguo-promotion-compensation-postcondition-v1"),"promotion backend drift");
if(value instanceof Af5Frame)check(h.sourceBackendId().equals("ck3-1.19.0.6-native-zhongguo-compensation-af5-snapshot-v1"),"AF5 backend drift");
if(value instanceof ProjectsFrame)check(h.sourceBackendId().equals("native-headless"),"project backend drift");
}
private static boolean caseAll(CaseIdentity c) { return all(c.ownerCharacterId(),c.subjectCharacterId(),c.cycleSerial(),c.caseSerial(),c.state(),c.active(),c.revision(),c.timelineSerial(),c.feedbackRevision()); }
private static boolean policyAll(Policy p) { return all(p.policyId(),p.choice()); }
private static boolean operationAll(Operation o) { return all(o.operationId(),o.operationKey(),o.hook(),o.preState(),o.postState()); }
private static boolean receiptAll(Receipt r) { return all(r.key(),r.ownerCharacterId(),r.subjectCharacterId(),r.cycleSerial(),r.caseSerial(),r.state(),r.choice()); }
private static void receiptJoin(Receipt r,CaseIdentity c,Operation o,CharacterId owner,CharacterId subject) {
check(receiptAll(r)&&eq(r.key(),"roster_lock")&&eq(r.ownerCharacterId(),owner.integer())&&eq(r.subjectCharacterId(),subject.integer())&&r.cycleSerial().equals(c.cycleSerial())&&r.caseSerial().equals(c.caseSerial())&&n(r.choice(),1)&&range(r.state(),1,Long.MAX_VALUE),"receipt identity/choice changed");
check(r.state().equals(o.preState())&&o.preState().equals(o.postState()),"receipt operation state changed");
}
private static void caseJoin(CaseIdentity c,CharacterId owner,CharacterId subject) {
check(caseAll(c)&&eq(c.ownerCharacterId(),owner.integer())&&eq(c.subjectCharacterId(),subject.integer())&&range(c.cycleSerial(),1,Long.MAX_VALUE)&&range(c.caseSerial(),1,Long.MAX_VALUE)&&range(c.revision(),1,Long.MAX_VALUE)&&range(c.timelineSerial(),1,Long.MAX_VALUE)&&range(c.feedbackRevision(),1,Long.MAX_VALUE),"case identity changed");
}
private static void verifyCase(CaseFrame f,ObjectNode args,PlanningReadReceipt receipt) {
var c=f.caseRecord(); var r=f.readiness(); var p=f.policy(); var o=f.operation(); var rec=f.receipt(); var d=f.deadline();
check(f.subjectCharacterId().equals(character(args.get("subject_character_id"))),"case requested subject changed");
BigInteger filter=integer(args.get("owner_character_id")); check(f.requestedOwnerCharacterId().map(CharacterId::integer).orElse(BigInteger.ZERO).equals(filter),"case owner filter changed");
check(r.ready()==(r.playerBindingReady()&&r.caseIdentityReady()&&r.policyReady()&&r.operationReady()&&r.receiptReady()&&r.deadlineIdentityReady()&&r.deadlineDueDateReady()&&r.sameFrameReady()),"case ready aggregate");
check(r.caseIdentityReady()==caseAll(c)&&r.policyReady()==policyAll(p)&&r.operationReady()==operationAll(o),"case readiness differs from fields");
if(r.caseIdentityReady()) { caseJoin(c,f.header().player(),f.subjectCharacterId()); check(range(c.state(),1,Long.MAX_VALUE),"positive case state"); if(filter.signum()>0)check(eq(c.ownerCharacterId(),filter),"case filter mismatch"); }
if(r.policyReady())check(eq(p.policyId(),"mechanism_039")&&n(p.choice(),1),"policy outside allowlist");
if(r.operationReady())check(r.policyReady()&&n(o.operationId(),39)&&eq(o.operationKey(),"roster_lock")&&eq(o.hook(),"roster_lock")&&range(o.preState(),1,Long.MAX_VALUE)&&range(o.postState(),1,Long.MAX_VALUE),"operation outside allowlist");
if(rec.status()!=ReceiptStatus.RECORDED)noValues(envelope(receipt,Family.CASE).get("receipt"),null);
if(d.status()==DeadlineStatus.NOT_SCHEDULED||d.status()==DeadlineStatus.UNAVAILABLE)noValues(envelope(receipt,Family.CASE).get("deadline"),null);
boolean rr=rec.status()==ReceiptStatus.RECORDED?receiptAll(rec):rec.status()==ReceiptStatus.NOT_RECORDED&&!receiptAll(rec);
check(r.receiptReady()==rr && r.operationReady()==(rec.status()==ReceiptStatus.RECORDED),"receipt/operation readiness");
if(rec.status()==ReceiptStatus.RECORDED)receiptJoin(rec,c,o,f.header().player(),f.subjectCharacterId());
boolean scheduled=d.status()==DeadlineStatus.PENDING||d.status()==DeadlineStatus.EXPIRED;
boolean di=d.status()==DeadlineStatus.NOT_SCHEDULED || scheduled&&all(d.targetCharacterId(),d.ownerCharacterId(),d.cycleSerial(),d.caseSerial(),d.expectedState(),d.days(),d.pending(),d.expired(),d.onDueOperation());
check(r.deadlineIdentityReady()==di && r.deadlineDueDateReady()==(d.status()==DeadlineStatus.NOT_SCHEDULED||scheduled&&d.dueDateRaw().available()),"deadline readiness");
if(scheduled&&di) {
check(eq(d.onDueOperation(),"resolve_pending_milestone")&&eq(d.targetCharacterId(),f.subjectCharacterId().integer())&&eq(d.pending(),d.status()==DeadlineStatus.PENDING)&&eq(d.expired(),d.status()==DeadlineStatus.EXPIRED),"deadline tuple changed");
if(r.caseIdentityReady())check(d.ownerCharacterId().equals(c.ownerCharacterId())&&d.cycleSerial().equals(c.cycleSerial())&&d.caseSerial().equals(c.caseSerial()),"deadline lineage changed");
check(range(d.targetCharacterId(),1,Integer.MAX_VALUE)&&range(d.ownerCharacterId(),1,Integer.MAX_VALUE)&&range(d.cycleSerial(),1,Long.MAX_VALUE)&&range(d.caseSerial(),1,Long.MAX_VALUE)&&range(d.expectedState(),1,Long.MAX_VALUE)&&range(d.days(),1,Long.MAX_VALUE),"deadline bounds");
if(d.dueDateRaw().available()) { check(range(d.dueDateRaw(),Integer.MIN_VALUE,Integer.MAX_VALUE),"due date bounds"); if(d.openDateRaw().available())check(range(d.openDateRaw(),Integer.MIN_VALUE,Integer.MAX_VALUE)&&d.dueDateRaw().required().compareTo(d.openDateRaw().required())>=0,"deadline order"); }
}
if(f.header().status()==Status.AVAILABLE)check(r.playerBindingReady()&&r.caseIdentityReady(),"available case lacks identity");
else {check(!r.ready()&&rec.status()==ReceiptStatus.UNAVAILABLE&&d.status()==DeadlineStatus.UNAVAILABLE,"unavailable case ready");noValues(envelope(receipt,Family.CASE),null);}
}
private static void verifyAi(AiOwnedFrame f,ObjectNode args,PlanningReadReceipt receipt) {
var c=f.caseRecord();var e=f.ownerEligibility();var s=f.stage();var route=f.route();var o=f.operation();var p=f.policy();var rec=f.receipt();var r=f.readiness();
check(f.requestedOwnerCharacterId().equals(character(args.get("owner_character_id")))&&f.subjectCharacterId().equals(character(args.get("subject_character_id"))),"AI case requested identity drift");
if(f.header().status()==Status.UNAVAILABLE) { check(!r.ready()&&rec.status()==ReceiptStatus.UNAVAILABLE,"unavailable AI ready");var original=envelope(receipt,Family.AIOWNED);unavailableReadiness(original,Set.of("case_not_found","owner_filter_mismatch"));noValues(original,"case_unavailable"); return; }
check(!f.requestedOwnerCharacterId().equals(f.header().player()),"AI owner equals player");caseJoin(c,f.requestedOwnerCharacterId(),f.subjectCharacterId());
int tier=e.primaryTitleTierRaw().required().intValueExact(); List<String> tiers=List.of("duchy","kingdom","empire","hegemony");
check(eq(e.ownerCharacterId(),f.requestedOwnerCharacterId().integer())&&eq(e.ownerAlive(),true)&&eq(e.ownerIsAi(),true)&&range(e.primaryTitleId(),1,Long.MAX_VALUE)&&tier>=3&&tier<=6&&eq(e.primaryTitleTierKey(),tiers.get(tier-3))&&eq(e.governmentKey(),"celestial_government")&&eq(e.subjectImmediateLiegeCharacterId(),f.requestedOwnerCharacterId().integer())&&eq(e.subjectIsDirectSubject(),true)&&eq(e.authorized(),true),"AI eligibility not authorized");
check(s.state().equals(c.state())&&s.active().equals(c.active()),"stage projection mismatch");int state=s.state().required().intValueExact();
boolean stageReady=state>=1&&state<=8&&eq(s.active(),state<8);
List<String> stages=List.of("targets_open","midcycle_open","evidence_open","facts_frozen","shadow_open","quota_ready","calibration_open","published");
check(stageReady?eq(s.key(),stages.get(state-1)):unavailable(s.key(),"stage_inconsistent"),"stage semantic key");
check(eq(route.kind(),"authorized_ai_background")&&eq(route.visibleEventAllowed(),false)&&eq(route.ownerIsAi(),true)&&eq(route.managerEligible(),true)&&eq(route.directSubjectEligible(),true),"AI background route changed");
boolean semantic=n(o.operationId(),39)&&n(p.choice(),1),zero=n(o.operationId(),0);
if(semantic)check(eq(p.policyId(),"mechanism_039")&&eq(o.operationKey(),"roster_lock")&&eq(o.hook(),"roster_lock"),"AI semantic operation changed");
else { String reason=zero?"no_operation_recorded":"unknown_allowlisted_operation";check(unavailable(p.policyId(),reason)&&unavailable(o.operationKey(),reason)&&unavailable(o.hook(),reason),"AI negative operation invented"); }
boolean rr=false;if(rec.status()==ReceiptStatus.RECORDED) { check(semantic,"recorded AI receipt has no semantic op");receiptJoin(rec,c,o,f.requestedOwnerCharacterId(),f.subjectCharacterId());rr=true; }
else if(rec.status()==ReceiptStatus.NOT_RECORDED) { noValues(envelope(receipt,Family.AIOWNED).get("receipt"),"receipt_not_recorded");check(zero&&unavailable(o.preState(),"receipt_not_recorded")&&unavailable(o.postState(),"receipt_not_recorded"),"AI not-recorded operation state");rr=true; }
else {noValues(envelope(receipt,Family.AIOWNED).get("receipt"),"receipt_inconsistent");check(!zero&&unavailable(o.preState(),"receipt_inconsistent")&&unavailable(o.postState(),"receipt_inconsistent"),"AI inconsistent operation state");}
check(r.ownerEligibilityReady()&&r.caseIdentityReady()&&r.stageReady()==stageReady&&r.routeReady()&&r.receiptReady()==rr&&r.sameFrameReady()&&r.ready()==(stageReady&&rr),"AI readiness tuple changed");
}
private static void verifyResult(ResultFrame f,ObjectNode args,PlanningReadReceipt receipt) {
var c=f.caseRecord();var n=f.notice();var d=f.delivery();var r=f.readiness();
check(f.requestedOwnerCharacterId().equals(character(args.get("owner_character_id")))&&f.subjectCharacterId().equals(f.header().player())&&!f.requestedOwnerCharacterId().equals(f.header().player()),"received-self owner/subject changed");
boolean cr=all(c.ownerCharacterId(),c.subjectCharacterId(),c.cycleSerial(),c.caseSerial(),c.state(),c.grade());
check(r.caseIdentityReady()==cr&&r.playerSubjectBindingReady()==cr&&r.ownerBindingReady()==cr,"result identity readiness");
if(cr)check(eq(c.ownerCharacterId(),f.requestedOwnerCharacterId().integer())&&eq(c.subjectCharacterId(),f.header().player().integer())&&range(c.cycleSerial(),1,Long.MAX_VALUE)&&range(c.caseSerial(),1,999999)&&range(c.state(),1,5)&&range(c.grade(),1,3),"result identity bounds");
boolean nr=all(n.absoluteGrade(),n.cohortNFrozen(),n.kpiFrozenQ100000(),n.rankFrozen())&&range(n.absoluteGrade(),1,3)&&range(n.rankFrozen(),1,Long.MAX_VALUE)&&range(n.cohortNFrozen(),1,Long.MAX_VALUE)&&n.rankFrozen().required().compareTo(n.cohortNFrozen().required())<=0;
boolean dr=cr&&all(d.method(),d.objectionRecorded(),d.settlementPostedSerial(),d.appealOpen())&&n(c.grade(),1)&&(
n(c.state(),1)&&n(d.method(),0)&&n(d.settlementPostedSerial(),0)&&eq(d.appealOpen(),false)&&eq(d.objectionRecorded(),false) ||
n(c.state(),3)&&n(d.method(),1)&&d.settlementPostedSerial().equals(c.caseSerial())&&eq(d.appealOpen(),true)&&eq(d.objectionRecorded(),false) ||
n(c.state(),3)&&n(d.method(),2)&&d.settlementPostedSerial().equals(c.caseSerial())&&eq(d.appealOpen(),true)&&eq(d.objectionRecorded(),true) ||
n(c.state(),2)&&n(d.method(),3)&&n(d.settlementPostedSerial(),0)&&eq(d.appealOpen(),false)&&eq(d.objectionRecorded(),false));
check(r.noticeFactsReady()==nr&&r.deliveryStateReady()==dr&&r.ready()==(cr&&nr&&dr&&r.sameFrameReady()),"result facts/delivery readiness");
if(f.header().status()==Status.AVAILABLE)check(cr,"available result lacks case");else {check(!r.ready(),"unavailable result readiness");noValues(envelope(receipt,Family.RESULT),null);}
}
private static void verifyScoreboard(ScoreboardFrame f) {
boolean available=f.header().status()==Status.AVAILABLE;check(f.widgets().size()==SCOREBOARD_WIDGETS.size(),"scoreboard fixed widget count");
for(int i=0;i<f.widgets().size();i++) {var w=f.widgets().get(i);String id=SCOREBOARD_WIDGETS.get(i);
check(w.stableIdentity().equals(id)&&w.runtimeName().equals(i==0?"zg361_scoreboard_toggle":id),"scoreboard widget identity");
if(available)check(w.instancePointer().available()&&w.vtablePointer().available(),"available scoreboard lacks pointers");}
check(!f.readiness().fullWidgetGateReady()&&!f.readiness().productionLiveReady(),"static provider falsely claims live");
for(Field<Boolean> action:List.of(f.actions().activate(),f.actions().close(),f.actions().reopen()))check(unavailable(action,"read_only_provider_action_not_exposed"),"read-only provider advertises write");
if(available)check(f.readiness().stateAclQueryReady()&&f.treeFingerprintV1().matches("[0-9A-F]{64}")&&f.semanticFingerprintV1().matches("[0-9A-F]{64}")&&f.providerSessionId().matches("[0-9A-F]{32}")&&f.observationSequence().signum()>0&&f.observedStateRevision().signum()>0,"scoreboard provider binding");
else check((f.treeFingerprintV1().isEmpty()||f.treeFingerprintV1().matches("[0-9A-F]{64}"))&&(f.semanticFingerprintV1().isEmpty()||f.semanticFingerprintV1().matches("[0-9A-F]{64}"))&&(f.providerSessionId().isEmpty()||f.providerSessionId().matches("[0-9A-F]{32}")),"unavailable scoreboard diagnostics");
if(available)check(f.acl().managed().surfaceAvailable()==f.acl().managed().currentPlayerCanAssessOthers()&&(!f.acl().receivedSelf().currentPlayerIsSubject()||f.acl().receivedSelf().surfaceAvailable()),"scoreboard ACL not surface-derived");
}
private static void verifyPip(PipFrame f,ObjectNode args,PlanningReadReceipt receipt) {
var r=f.readiness();var gate=f.gate();var p=f.pip();var owner=character(args.get("owner_character_id"));var player=f.header().player();
check(f.requestedOwnerCharacterId().equals(owner)&&f.subjectCharacterId().equals(player)&&!owner.equals(player),"PIP owner/subject drift");
check(r.ready()==(r.playerSubjectBindingReady()&&r.ownerBindingReady()&&r.gateReady()&&r.sameFrameReady()),"PIP identity aggregate");
if(f.header().status()==Status.UNAVAILABLE) { check(!r.ready(),"unavailable PIP ready");var original=envelope(receipt,Family.PIP);unavailableReadiness(original,Set.of("case_not_found","case_inconsistent","owner_filter_mismatch","not_received_self"));noValues(original,"case_unavailable");return; }
boolean gr=all(gate.ownerCharacterId(),gate.subjectCharacterId(),gate.cycleSerial(),gate.caseSerial(),gate.threshold(),gate.negativeComponentCount(),gate.evidenceComplete(),gate.status());
if(gr)gr=eq(gate.ownerCharacterId(),owner.integer())&&eq(gate.subjectCharacterId(),player.integer())&&range(gate.cycleSerial(),1,Long.MAX_VALUE)&&range(gate.caseSerial(),1,999999)&&n(gate.threshold(),3)&&range(gate.negativeComponentCount(),0,10)&&range(gate.status(),0,3)&&eq(gate.evidenceComplete(),!n(gate.status(),0));
check(r.gateReady()==gr,"frozen gate readiness");
boolean anyPip=!List.of(p.ownerCharacterId(),p.subjectCharacterId(),p.cycleSerial(),p.caseSerial(),p.state(),p.taskKind(),p.policyRoute(),p.taskControllable()).stream().allMatch(x->unavailable(x,"variable_absent"));
boolean pr=gr&&all(p.ownerCharacterId(),p.subjectCharacterId(),p.cycleSerial(),p.caseSerial(),p.state(),p.taskKind(),p.policyRoute(),p.taskControllable());
if(pr)pr=eq(p.ownerCharacterId(),owner.integer())&&eq(p.subjectCharacterId(),player.integer())&&range(p.cycleSerial(),1,Long.MAX_VALUE-1)&&range(p.caseSerial(),1,999999)&&p.cycleSerial().equals(gate.cycleSerial())&&p.caseSerial().equals(gate.caseSerial())&&range(p.state(),1,5)&&range(p.taskKind(),1,3)&&range(p.policyRoute(),1,2);
check(r.pipIdentityReady()==pr&&(!anyPip||pr),"PIP identity inconsistency");
boolean pb=eq(gate.subjectCharacterId(),player.integer())&&(!anyPip||eq(p.subjectCharacterId(),player.integer()));
boolean ob=eq(gate.ownerCharacterId(),owner.integer())&&(!anyPip||eq(p.ownerCharacterId(),owner.integer()));
check(pb&&ob&&r.playerSubjectBindingReady()==pb&&r.ownerBindingReady()==ob&&r.sameFrameReady(),"PIP paused bindings");
var evidence=List.of(gate.governanceQ100000(),gate.capabilityQ100000(),gate.growthQ100000(),gate.superiorQ100000(),gate.valuesQ100000(),gate.collaborationQ100000(),gate.jingchaQ100000(),gate.organizationQ100000());
boolean er=gr&&all(gate.resultCaseSerial(),gate.resultGrade(),gate.absoluteGrade(),gate.kpiFrozenQ100000())&&evidence.stream().allMatch(Field::available);
if(er){long negatives=(n(gate.absoluteGrade(),1)?1:0)+(gate.kpiFrozenQ100000().required().signum()<0?1:0)+evidence.stream().filter(x->x.required().signum()<0).count();
er=eq(gate.evidenceComplete(),true)&&gate.resultCaseSerial().equals(gate.caseSerial())&&range(gate.resultGrade(),1,3)&&range(gate.absoluteGrade(),1,3)&&n(gate.negativeComponentCount(),negatives);}
check(r.gateEvidenceReady()==er,"PIP evidence count");
var response=f.response();boolean rr=false;
if(pr){var pc=p.caseSerial();boolean pending=n(p.state(),1)&&n(response.subjectResponse(),0)&&n(response.responseCaseSerial(),0)&&unavailable(response.responseAuthorCharacterId(),"variable_absent")&&n(response.refusalReceiptSerial(),0);
boolean accepted=range(p.state(),2,4)&&range(response.subjectResponse(),1,2)&&response.responseCaseSerial().equals(pc)&&eq(response.responseAuthorCharacterId(),player.integer())&&n(response.refusalReceiptSerial(),0);
boolean refused=n(p.state(),5)&&n(response.subjectResponse(),3)&&response.responseCaseSerial().equals(pc)&&eq(response.responseAuthorCharacterId(),player.integer())&&response.refusalReceiptSerial().equals(pc);
rr=response.acknowledgementReceiptSerial().equals(pc)&&response.goalRevisionUsed().available()&&(pending||accepted||refused);}
check(r.responseReady()==rr,"PIP response receipt");
var s=f.support();boolean sr=false;
if(pr){boolean core=all(s.capacityReserved(),s.supportAbsent())&&range(s.hours(),0,12)&&range(s.attentionUnits(),0,1)&&range(s.treasuryBudgetAllocated(),0,25)&&range(s.treasuryBudgetSpent(),0,25)&&s.supportReceiptSerial().equals(p.caseSerial());
boolean reserved=n(p.state(),2)&&eq(s.capacityReserved(),true)&&eq(s.supportAbsent(),false)&&n(s.hours(),12)&&n(s.attentionUnits(),1)&&range(s.mentorCharacterId(),1,Integer.MAX_VALUE)&&eq(s.budgetOwnerCharacterId(),owner.integer())&&n(s.treasuryBudgetAllocated(),25)&&n(s.treasuryBudgetSpent(),25)&&range(s.ownerCapacityUsed(),1,2)&&absentFalse(s.released())&&absentFalse(s.withheld())&&absentFalse(s.atomicShortfall());
boolean absent=n(p.state(),2)&&eq(s.capacityReserved(),false)&&eq(s.supportAbsent(),true)&&n(s.hours(),0)&&n(s.attentionUnits(),0)&&n(s.treasuryBudgetAllocated(),0)&&n(s.treasuryBudgetSpent(),0)&&absentFalse(s.released())&&(
n(p.policyRoute(),1)&&absentFalse(s.withheld())&&eq(s.atomicShortfall(),true)||n(p.policyRoute(),2)&&eq(s.withheld(),true)&&absentFalse(s.atomicShortfall()));
sr=core&&(reserved||absent);}
check(r.supportReady()==sr,"PIP support package");
var ledger=f.budgetLedger();boolean lr=pr&&ledger.resultCaseSerial().equals(p.caseSerial())&&range(ledger.treasuryPenaltyPaid(),0,Long.MAX_VALUE)&&range(ledger.personalGoldPenaltyPaid(),0,Long.MAX_VALUE)&&range(ledger.supportTreasuryAllocated(),0,25)&&range(ledger.supportTreasurySpent(),0,25);
check(r.budgetLedgerReady()==lr,"PIP budget ledger");
check(!r.d180TicketObservationReady()&&!r.d365TicketObservationReady()&&!r.modifierObservationReady()&&unavailable(f.pipModifierPresent(),"native_observation_unavailable"),"PIP ticket/modifier fabricated");
var original=envelope(receipt,Family.PIP);for(String ticket:List.of("d180_ticket","d365_ticket"))for(var it=original.get(ticket).properties().iterator();it.hasNext();){var entry=it.next();JsonNode v=entry.getValue();check(text(v.get("status")).equals("unavailable")&&text(v.get("unavailable_reason")).equals(entry.getKey().equals("due_date_raw")?"product_not_persisted":"native_observation_unavailable"),"PIP ticket fabricated");}
var mid=f.midpoint();boolean mr=pr&&mid.receiptSerial().equals(p.caseSerial())&&mid.resourceDeliveryValid().available()&&n(mid.progressStatus(),0)&&n(mid.progressRedCode(),1)&&n(mid.state(),2);
check(r.midpointReady()==mr,"PIP midpoint receipt");
var out=f.outcome();boolean or=false;
if(pr&&(n(p.state(),3)||n(p.state(),4))){var pc=p.caseSerial();boolean graduated=n(p.state(),3)&&n(out.code(),1)&&out.graduationReceiptSerial().equals(pc)&&absentZero(out.failureReceiptSerial());
boolean failed=n(p.state(),4)&&n(out.code(),2)&&out.failureReceiptSerial().equals(pc)&&absentZero(out.graduationReceiptSerial());
or=out.settlementReceiptSerial().equals(pc)&&range(out.resultCycleSerial(),1,Long.MAX_VALUE)&&range(out.resultCaseSerial(),1,999999)&&range(out.resultGrade(),1,3)&&n(out.stabilityDaysObserved(),365)&&n(out.independentReviewStatus(),0)&&n(out.independentReviewRedCode(),2)&&(graduated||failed);}
check(r.outcomeReady()==or,"PIP outcome settlement");
var next=f.nextCycleEvidence();boolean nr=false;
if(pr&&range(next.status(),1,2)){boolean base=eq(next.ownerCharacterId(),owner.integer())&&eq(next.subjectCharacterId(),player.integer())&&next.sourceCycleSerial().equals(p.cycleSerial())&&next.sourceCaseSerial().equals(p.caseSerial())&&eq(next.dueCycleSerial(),p.cycleSerial().required().add(BigInteger.ONE))&&(n(next.delta(),10)||n(next.delta(),-10)||n(next.delta(),-15));
boolean pending=n(next.status(),1)&&unavailable(next.consumedCycleSerial(),"variable_absent")&&unavailable(next.consumedCaseSerial(),"variable_absent");
boolean consumed=n(next.status(),2)&&range(next.consumedCycleSerial(),0,Long.MAX_VALUE)&&next.consumedCycleSerial().required().compareTo(next.dueCycleSerial().required())>=0&&next.consumedCaseSerial().equals(p.caseSerial());nr=base&&(pending||consumed);}
check(r.nextCycleEvidenceReady()==nr,"PIP next-cycle lineage");
}
private static void verifyIncident(IncidentFrame f,ObjectNode args,PlanningReadReceipt receipt) {
var owner=character(args.get("owner_character_id"));var player=f.header().player();var r=f.readiness();var p=f.probe();var terminal=f.terminal();var k=f.kpi();
check(f.profile()==enumeration(args.get("profile"),IncidentProfile.class)&&f.requestedOwnerCharacterId().equals(owner)&&f.subjectCharacterId().equals(player)&&!owner.equals(player),"incident owner/profile drift");
aggregate(envelope(receipt,Family.INCIDENT),Set.of());
if(f.header().status()==Status.UNAVAILABLE){check(!r.ready()&&terminal.kind()==TerminalKind.UNAVAILABLE&&terminal.na().isEmpty()&&terminal.incident().isEmpty()&&k.disposition()==KpiDisposition.UNAVAILABLE,"unavailable incident exposes terminal");noValues(envelope(receipt,Family.INCIDENT),null);return;}
check(eq(p.ownerCharacterId(),owner.integer())&&eq(p.subjectCharacterId(),player.integer())&&range(p.cycleSerial(),1,Long.MAX_VALUE)&&range(p.probeSerial(),1,Long.MAX_VALUE)&&range(p.result(),0,1)&&r.probeReady()&&r.playerSubjectBindingReady()&&r.ownerBindingReady()&&r.profileBindingReady()&&r.sameFrameReady(),"incident probe binding");
check(r.resourceSnapshotReady()==all(f.resources().capitalControlQ100000(),f.resources().managerTreasuryQ100000(),f.resources().subjectPersonalGoldQ100000()),"incident resource ready");
boolean kr;
if(terminal.kind()==TerminalKind.NA){var a=terminal.na().orElseThrow();check(terminal.incident().isEmpty()&&n(p.result(),0)&&n(p.sourceKind(),0)&&n(p.consequenceKind(),0)&&eq(a.ownerCharacterId(),owner.integer())&&eq(a.subjectCharacterId(),player.integer())&&a.cycleSerial().equals(p.cycleSerial())&&a.probeSerial().equals(p.probeSerial())&&n(a.reason(),1)&&range(a.receiptSerial(),1,Long.MAX_VALUE)&&n(a.applicable(),0)&&n(a.kpiStaged(),0)&&k.disposition()==KpiDisposition.NOT_STAGED,"N/A receipt does not join probe");
noValues(envelope(receipt,Family.INCIDENT).get("kpi"),null);kr=true;
}else {check(terminal.kind()==TerminalKind.INCIDENT&&terminal.na().isEmpty(),"incident union");var a=terminal.incident().orElseThrow();
boolean consequence=n(p.sourceKind(),1)&&n(p.consequenceKind(),1)||(n(p.sourceKind(),3)||n(p.sourceKind(),4))&&n(p.consequenceKind(),2)||n(p.sourceKind(),5)&&n(p.consequenceKind(),3);
check(n(p.result(),1)&&consequence&&eq(a.ownerCharacterId(),owner.integer())&&eq(a.subjectCharacterId(),player.integer())&&a.cycleSerial().equals(p.cycleSerial())&&range(a.caseSerial(),1,999999)&&n(a.state(),f.profile()==IncidentProfile.X?8:6)&&range(a.revision(),1,Long.MAX_VALUE)&&range(a.incidentSerial(),1,Long.MAX_VALUE)&&a.sourceKind().equals(p.sourceKind())&&a.consequenceKind().equals(p.consequenceKind())&&range(a.finalScore(),-4,4)&&n(a.applicable(),1)&&range(a.kpiStaged(),0,1),"incident terminal lineage");
if(k.disposition()==KpiDisposition.UNAVAILABLE){noValues(envelope(receipt,Family.INCIDENT).get("kpi"),null);kr=false;}
else {check(k.disposition()==KpiDisposition.PENDING||k.disposition()==KpiDisposition.CONSUMED,"incident KPI disposition");
check(k.ownerCharacterId().equals(a.ownerCharacterId())&&k.subjectCharacterId().equals(a.subjectCharacterId())&&k.originCycle().equals(a.cycleSerial())&&eq(k.dueCycle(),k.originCycle().required().add(BigInteger.ONE))&&n(k.dueOffset(),1)&&k.caseSerial().equals(a.caseSerial())&&k.state().equals(a.state())&&k.score().equals(a.finalScore())&&k.incidentSerial().equals(a.incidentSerial())&&k.sourceKind().equals(a.sourceKind())&&k.consequenceKind().equals(a.consequenceKind()),"incident KPI tuple join");
boolean consumed=k.disposition()==KpiDisposition.CONSUMED;check(n(k.pending(),consumed?0:1)&&n(k.consumed(),consumed?1:0),"KPI bits");
if(consumed)check(range(k.receiptSerial(),1,Long.MAX_VALUE)&&k.consumedOwnerCharacterId().equals(k.ownerCharacterId())&&k.consumedSubjectCharacterId().equals(k.subjectCharacterId())&&k.consumedOriginCycle().equals(k.originCycle())&&k.consumedDueCycle().equals(k.dueCycle())&&k.consumedCycle().required().compareTo(k.dueCycle().required())>=0&&k.consumedCaseSerial().equals(k.caseSerial())&&k.consumedScore().equals(k.score())&&k.consumedIncidentSerial().equals(k.incidentSerial()),"consumed KPI receipt");
else for(String key:List.of("receipt_serial","consumed_owner_character_id","consumed_subject_character_id","consumed_origin_cycle","consumed_due_cycle","consumed_cycle","consumed_case_serial","consumed_score","consumed_incident_serial"))noValues(envelope(receipt,Family.INCIDENT).get("kpi").get(key),null);
kr=true;}
}
check(r.terminalReady()&&r.kpiStateReady()==kr,"incident terminal/KPI readiness");
}
static final List<String> SCOREBOARD_WIDGETS=List.of("zg361_open_scoreboard","zg361_scoreboard_window","zg361_scoreboard_modal","zg361_scoreboard_panel","zg361_scoreboard_entry_managed","zg361_scoreboard_entry_received","zg361_scoreboard_entry_system","zg361_scoreboard_tab_managed","zg361_scoreboard_tab_received","zg361_scoreboard_tab_system","zg361_scoreboard_page_managed","zg361_scoreboard_page_received","zg361_scoreboard_page_system","zg361_scoreboard_modal_backdrop_close","zg361_scoreboard_header_close");
static final List<String> PROGRESS_WIDGETS=List.of("zg361_promotion_source_bridge_window","zg361_promotion_source_review_now_action","zg361_promotion_source_b1_active","zg361_promotion_source_central_active","zg361_promotion_source_pp_active","zg361_promotion_source_central_stage_1","zg361_promotion_source_central_stage_2","zg361_promotion_source_central_stage_3","zg361_promotion_source_central_stage_4","zg361_promotion_source_central_stage_5","zg361_promotion_source_central_stage_6","zg361_promotion_source_central_stage_7","zg361_promotion_source_central_stage_8","zg361_promotion_source_central_stage_9","zg361_promotion_source_central_stage_10","zg361_promotion_source_central_stage_11","zg361_promotion_source_central_status_0","zg361_promotion_source_central_status_1","zg361_promotion_source_central_status_2","zg361_promotion_source_central_status_3","zg361_promotion_source_central_status_4","zg361_promotion_source_central_status_5","zg361_promotion_source_cl_partial_open","zg361_promotion_source_cl_digest_pending","zg361_promotion_source_cl_cycle_matches","zg361_promotion_source_cl_frozen_positive","zg361_promotion_source_cl_expectations_match","zg361_promotion_source_cl_ah_complete","zg361_promotion_source_cl_ai_complete");
}

