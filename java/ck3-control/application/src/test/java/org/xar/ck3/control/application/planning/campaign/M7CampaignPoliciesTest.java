package org.xar.ck3.control.application.planning.campaign;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.projectGoal;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.*;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.*;

// Software-only fixtures, no Native grant.
final class M7CampaignPoliciesTest {
private static final ExactRef SOURCE = new ExactRef("software-fixture-source", 1, "a".repeat(64));
private static final Instant BIRTH = Instant.parse("2026-10-23T00:00:00Z");
private static final CampaignDeadline.Configuration CONFIG = CampaignDeadline.configure(
new CampaignDeadline.Founding("software-campaign", "1066.9.15", bi(org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.9.15")), 2),
OrdinaryCampaignSchedule::calendar, Optional.empty());

@Test void boundaryFactory() {
long current = CONFIG.boundaryRaws().get(1).longValueExact() - 24;
PlanningRequest request = request(current, Optional.empty());
long proposed = current + 45 * 24;
var original = command(request, "battle-decision-epoch-advance-to-" + proposed, bi(proposed));
var before = draft(original);
AtomicInteger calls = new AtomicInteger();
var policy = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.of(CONFIG), (r, old, step, cap) -> {
calls.incrementAndGet(); assertSame(original, old);
assertEquals(CONFIG.boundaryRaws().get(1), cap.targetDateRaw());
return command(r, step, cap.targetDateRaw());
}, ignored -> Optional.empty());
var result = assertInstanceOf(Replace.class, policy.evaluate(request, before)).draft();
assertEquals("battle-decision-epoch-advance-to-" + CONFIG.boundaryRaws().get(1), result.command().orElseThrow().operation().value());
assertEquals(before.detail().get("original_evidence"), result.detail().get("original_evidence"));
assertNotEquals(original.expected(), result.command().orElseThrow().expected());
assertInstanceOf(Keep.class, policy.evaluate(request, result)); assertEquals(1, calls.get());
}

@Test void endpointNoAction() {
PlanningRequest request = request(CONFIG.endpointDateRaw().longValueExact(), Optional.empty());
var policy = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.of(CONFIG),
(r, old, step, cap) -> { fail("endpoint must not build an advance"); return old; }, ignored -> Optional.empty());
var result = assertInstanceOf(Replace.class,
policy.evaluate(request, draft(command(request, "battle-terminal-cruise", bi(0))))).draft();
assertTrue(result.command().isEmpty()); assertEquals("campaign_score_endpoint_reached", result.phase());
}

@Test void realmUnknownOneShot() {
PlanningRequest request = request(CONFIG.founding().startDateRaw().longValueExact(), Optional.empty());
var lifecycle = new RealmLifecycle(SOURCE);
var command = command(request, M7CampaignPolicies.FACTION_QUERY, bi(0)); var draft = draft(command);
assertThrows(IllegalArgumentException.class, () -> lifecycle.evaluate(request, draft));
var scope = lifecycle.begin(request); lifecycle.evaluate(request, draft);
lifecycle.finalizePlan(scope, new PlanningResult.ActionSelected(command,
new PlanTrace(request.before(), List.of(), Optional.of(draft))));
var unknown = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
new ActionState.Unknown(Optional.empty(), Optional.empty(), "software-unknown", List.of()));
assertEquals("original_query_not_confirmed", assertInstanceOf(RealmUnavailable.class, lifecycle.afterExecution(unknown)).reason());
assertEquals("original_query_plan_slot_unavailable", assertInstanceOf(RealmUnavailable.class, lifecycle.afterExecution(unknown)).reason());
var newer = lifecycle.begin(request); lifecycle.cancel(newer);
assertInstanceOf(RealmUnavailable.class, lifecycle.afterExecution(unknown));
}

@Test void actualGoalConsumer() {
var goal = OrdinaryCampaignGoal.newGoal("software-campaign", 1);
PlanningRequest request = request(CONFIG.founding().startDateRaw().longValueExact(), Optional.of(goal));
var before = draft(command(request, "query-example-v1", bi(0)));
var missing = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(),
(r, old, step, cap) -> { fail("no clock shape"); return old; }, ignored -> Optional.empty());
assertEquals(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,
assertInstanceOf(Stop.class, missing.evaluate(request, before)).stopReason());
var observation = projectGoal(request, "a".repeat(64), SOURCE, Optional.empty()).orElseThrow().observation();
var present = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(),
(r, old, step, cap) -> old, ignored -> Optional.of(new GoalInput(observation, Optional.empty())));
var result = assertInstanceOf(Replace.class, present.evaluate(request, before)).draft();
byte[] consumed = OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption"));
var restored = M7KernelPlanConsumer.decode(consumed);
assertEquals(before.command().orElseThrow().operation().value(), restored.selectedStep());
assertArrayEquals(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(goal)), GoalCodec.encodePlan(restored.campaignGoalPlanUsed()));
assertNull(result.detail().get("m7_ordinary_plan_consumption"));
}

@Test void exactKernelBirthRejectsOneTickDriftAndPreservesUint64Maximum() {
var goal = OrdinaryCampaignGoal.newGoal("software-campaign", 1);
BigInteger maximum = new BigInteger("18446744073709551615");
var request = request(CONFIG.founding().startDateRaw().longValueExact(), Optional.of(goal), maximum);
var original = draft(command(request, "query-example-v1", bi(0)));
var projected = projectGoal(request, "a".repeat(64), SOURCE, Optional.empty()).orElseThrow();
var correct = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(), (r, old, step, cap) -> old,
ignored -> Optional.of(projected));
var result = assertInstanceOf(Replace.class, correct.evaluate(request, original)).draft();
var consumed = M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
assertEquals(maximum.toString(), consumed.observation().game().creationFiletime());
var value = projected.observation();
var drift = new KernelCheckpointContinuity.Observation(value.machineId(), value.sourceEpoch(),
new org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity(value.game().pid(), maximum.subtract(BigInteger.ONE).toString()),
value.executable(), value.snapshotId(), value.revision(), value.nativeRevision(), value.episodeRunId(),
value.actorCharacterId(), value.dateRaw(), value.goal(), value.governmentKey(), value.adapterFamily());
var wrong = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(), (r, old, step, cap) -> old,
ignored -> Optional.of(new GoalInput(drift, Optional.empty())));
assertThrows(IllegalArgumentException.class, () -> wrong.evaluate(request, original));
}

@Test void goalSourceCannotCrossTheCurrentSnapshotEpisodeOrPublicRevision() {
var goal = OrdinaryCampaignGoal.newGoal("software-campaign", 1);
var request = request(CONFIG.founding().startDateRaw().longValueExact(), Optional.of(goal));
var original = draft(command(request, "query-example-v1", bi(0)));
var value = projectGoal(request, "a".repeat(64), SOURCE, Optional.empty()).orElseThrow().observation();
for (int changed = 0; changed < 3; changed++) {
var wrong = new KernelCheckpointContinuity.Observation(value.machineId(), value.sourceEpoch(), value.game(), value.executable(),
changed == 0 ? "different-native-snapshot" : value.snapshotId(), changed == 1 ? value.revision().add(BigInteger.ONE) : value.revision(),
value.nativeRevision(), changed == 2 ? "different-episode" : value.episodeRunId(), value.actorCharacterId(), value.dateRaw(),
value.goal(), value.governmentKey(), value.adapterFamily());
var policy = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(), (r, old, step, cap) -> old,
ignored -> Optional.of(new GoalInput(wrong, Optional.empty())));
assertThrows(IllegalArgumentException.class, () -> policy.evaluate(request, original));
}
assertTrue(projectGoal(request(CONFIG.founding().startDateRaw().longValueExact(), Optional.empty()),
"a".repeat(64), SOURCE, Optional.empty()).isEmpty());
}

@Test void nativeCalendarRejectsPartialHourBeforeRewritingTheAdvance() {
var request = request(CONFIG.founding().startDateRaw().longValueExact() + 1, Optional.empty());
var policy = new CampaignAdvancePolicy(SOURCE, ignored -> Optional.of(CONFIG),
(r, old, step, cap) -> { fail("non-day native frame cannot reach the rewrite factory"); return old; }, ignored -> Optional.empty());
assertThrows(IllegalArgumentException.class, () -> policy.evaluate(request, draft(command(request, "life-advance", bi(0)))));
}

@Test void actualKernelPolicyPreservesUnsigned64PublicAndNativeRevisionsThroughItsConsumer() {
var maximum=new BigInteger("18446744073709551615");
var goal=OrdinaryCampaignGoal.newGoal("software-campaign",1);
var request=request(CONFIG.founding().startDateRaw().longValueExact(),Optional.of(goal),maximum,maximum,maximum.subtract(BigInteger.ONE));
var projected=projectGoal(request,"a".repeat(64),SOURCE,Optional.empty()).orElseThrow();
assertEquals(maximum,projected.observation().revision());
assertEquals(maximum.subtract(BigInteger.ONE),projected.observation().nativeRevision());
var policy=new CampaignAdvancePolicy(SOURCE,ignored->Optional.empty(),(r,old,step,cap)->old,ignored->Optional.of(projected));
var result=assertInstanceOf(Replace.class,policy.evaluate(request,draft(command(request,"query-example-v1",bi(0))))).draft();
var restored=M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
assertEquals(projected.observation(),restored.observation());
assertEquals(maximum,restored.observation().revision());
assertEquals(maximum.subtract(BigInteger.ONE),restored.observation().nativeRevision());
assertThrows(IllegalArgumentException.class,()->projectGoal(request(CONFIG.founding().startDateRaw().longValueExact(),Optional.of(goal),
maximum,maximum.add(BigInteger.ONE),BigInteger.ONE),"a".repeat(64),SOURCE,Optional.empty()));
}

private static PlanningRequest request(long raw, Optional<OrdinaryCampaignGoal.Goal> goal) {
return request(raw, goal, bi(BIRTH.getEpochSecond()).add(bi(11644473600L)).multiply(bi(10000000)));
}
private static PlanningRequest request(long raw, Optional<OrdinaryCampaignGoal.Goal> goal, BigInteger birth) {
return request(raw,goal,birth,BigInteger.ONE,BigInteger.ONE);
}
private static PlanningRequest request(long raw, Optional<OrdinaryCampaignGoal.Goal> goal, BigInteger birth,BigInteger revision,BigInteger nativeRevision) {
var snapshot = OpportunityJson.object(OpportunityJson.parse(("{\"snapshot_id\":\"native:1\",\"episode_run_id\":\"episode\",\"revision\":"+revision+",\"native_revision\":"+nativeRevision+",\"date_raw\":" + raw
+ ",\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":1,\"alive\":true},\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":11,\"connection_generation\":1}}")
.getBytes(StandardCharsets.UTF_8)), "software snapshot");
var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(bi(1), nativeRevision, bi(raw)), "native:1", revision, "episode");
var identity = new ObservationIdentity("m7-software-test", new GameGeneration(1,
new PythonOnlyUInt64(birth)), frame, 1);
var source = new G2Source("m7-software-test", "2026-10-23T00:00:00Z", "software-only", SOURCE);
return new PlanningRequest(identity, source, "software-session", Instant.parse("2099-01-01T00:00:00Z"),
new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(), Optional.empty(), List.of(), goal, Optional.empty(), false));
}
private static ActionCommand command(PlanningRequest request, String step, BigInteger target) {
var arguments = new OpportunityJson.Obj(java.util.Map.of()).with("target_date_raw", new OpportunityJson.IntegerValue(target));
var expected = new ExpectedPostcondition(1, request.before(), request.source(), "software-only/v1",
List.of(new ExpectedInteger(new FieldKey("target_date_raw"), target)));
return new ActionCommand("software-action", request.before(), request.source(), request.sessionId(), new OperationKey(step), arguments,
expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
}
private static Draft draft(ActionCommand command) {
return new Draft("software-policy", "ordinary", "software fixture", Kind.ORDINARY,
Optional.of(command), Purpose.DATE_ADVANCE, Optional.empty(),
new OpportunityJson.Obj(java.util.Map.of()).with("original_evidence", new OpportunityJson.Text("retained")));
}
private static BigInteger bi(long value) { return BigInteger.valueOf(value); }
}
