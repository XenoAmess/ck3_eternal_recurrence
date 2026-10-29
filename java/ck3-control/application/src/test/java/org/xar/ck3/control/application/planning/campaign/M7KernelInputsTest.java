package org.xar.ck3.control.application.planning.campaign;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.LifecycleReducer;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;

/** Complete native-envelope -> Driver assembler -> held kernel supplier -> real ordinary consumer. Software only. */
public final class M7KernelInputsTest {
    private static final ExactRef SOURCE = ref(bytes("software-source"));
    private static final Instant AT = Instant.parse("2026-10-23T18:40:00Z");
    private static final String MACHINE = "m7-kernel-software";
    private static final BigInteger ACTOR = BigInteger.valueOf(Integer.MAX_VALUE);
    private static final long RAW = 53_169_072;

    @Test void optionalEmptyEpochAndExecutableRoundTripThroughRealPolicyAndConsumer() throws Exception {
        Fixture f = new Fixture(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("optional-metadata-campaign", ACTOR.longValueExact()))));
        M7KernelInputs service = f.service();
        var captured = service.capture(f.session, f.request, f.complete, Optional.empty(), Optional.empty(), Optional.empty());
        assertEquals(f.known.stamp(), captured.driverStamp());
        assertEquals(f.complete.originalEvidence(), captured.originalNative());
        var policy = new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(),
                (request, original, step, cap) -> { fail("query is not a clock rewrite"); return original; }, service);
        var result = assertInstanceOf(Replace.class, policy.evaluate(f.request, draft(command(f.request)))).draft();
        var consumed = M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
        assertEquals(f.request.observations().campaignGoal().orElseThrow(), consumed.observation().goal());
        assertEquals(Optional.<String>empty(), consumed.observation().sourceEpoch());
        assertEquals(Optional.<ExactRef>empty(), consumed.observation().executable());
        assertEquals(consumed,M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed)));
        assertEquals(0, consumed.savedDayCredit()); assertFalse(consumed.coldAuthorityGranted());
        assertFalse(consumed.gameActionsSubmitted()); assertFalse(consumed.replayAuthorized());
    }

    @Test void actualHeldCaptureFeedsFullKernelConsumerWithoutOpeningAnotherNativeFrame() throws Exception {
        Fixture f = new Fixture(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("actual-software-campaign", ACTOR.longValueExact()))));
        M7KernelInputs service = f.service();
        var captured = service.capture(f.session, f.request, f.complete, "a".repeat(64), SOURCE, Optional.empty());
        assertEquals(f.known.stamp(), captured.driverStamp());
        assertEquals(f.complete.originalEvidence(), captured.originalNative());
        assertEquals(f.session.head().digest(), captured.writerHeadDigest());
        var policy = new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE, ignored -> Optional.empty(),
                (request, original, step, cap) -> { fail("query is not a clock rewrite"); return original; }, service);
        var result = assertInstanceOf(Replace.class, policy.evaluate(f.request, draft(command(f.request)))).draft();
        var consumed = M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
        assertEquals("18446744073709551615", consumed.observation().game().creationFiletime());
        assertEquals(ACTOR.longValueExact(), consumed.observation().actorCharacterId());
        assertEquals(f.request.observations().campaignGoal().orElseThrow(), consumed.observation().goal());
        assertArrayEquals(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(consumed.observation().goal())),
                GoalCodec.encodePlan(consumed.campaignGoalPlanUsed()));
        assertEquals(0, consumed.savedDayCredit()); assertFalse(consumed.coldAuthorityGranted());
        var equalCopy = new PlanningRequest(f.request.before(), f.request.source(), f.request.sessionId(),
                f.request.deadline(), f.request.observations());
        assertEquals(f.request, equalCopy); assertNotSame(f.request, equalCopy);
        assertTrue(service.current(equalCopy).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> captured.current(equalCopy));
    }

    @Test void fullUint64ReadinessFrameFeedsActualHeldSupplierAndOrdinaryConsumer() throws Exception {
        var maximum=StrictJson.UINT64_MAX;
        Fixture f=new Fixture(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("full64-readiness",ACTOR.longValueExact()))),maximum,maximum);
        M7KernelInputs service=f.service();
        var captured=service.capture(f.session,f.request,f.complete,"a".repeat(64),SOURCE,Optional.empty());
        assertEquals(maximum,captured.current(f.request).orElseThrow().observation().revision());
        var policy=new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE,ignored->Optional.empty(),
                (request,original,step,cap)->{throw new AssertionError("query must not rewrite clock");},service);
        var result=assertInstanceOf(Replace.class,policy.evaluate(f.request,draft(command(f.request)))).draft();
        var consumed=M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
        assertEquals(maximum,consumed.observation().revision());assertEquals(maximum,consumed.observation().nativeRevision());
        assertEquals(0,consumed.savedDayCredit());assertFalse(consumed.coldAuthorityGranted());
    }

    @Test void actualMatchedLifecycleReducerFeedsWholeReadinessKernelAndOrdinaryPlan() throws Exception {
        BigInteger maximum=StrictJson.UINT64_MAX;
        var beforeDriver=ordinaryDriver(73,"actual-episode",OrdinaryCampaignGoal.newGoal("whole-reducer-campaign",73));
        Fixture before=new Fixture(beforeDriver,maximum.subtract(BigInteger.ONE),maximum.subtract(BigInteger.ONE));
        Fixture changed=new Fixture(ordinaryDriver(74,"actual-episode",OrdinaryCampaignGoal.newGoal("whole-reducer-campaign",74)),maximum,maximum);
        var actual=changed.actual;
        var originalFacts=new DriverObservationFacts(beforeDriver,3,7,actual.session(),actual.snapshotId(),actual.nativeRevision(),
                sha(actual.state().bytes()),maximum,1,before.source,new OpportunityJson.Obj(Map.of()),ref(bytes("original-terminal-facts")));
        var full=new DriverObservationAssembler().projectFull(actual,originalFacts,ref(actual.originalPacket()));
        var title=new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Title(1,BigInteger.TWO,
                new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.WireObject(bytes("{\"title_id\":1,\"tier_raw\":2}")));
        var rows=List.of(new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.TitleRow(title,74,true));
        var oldFrame=new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Frame(before.actual.snapshotId(),maximum.subtract(BigInteger.ONE),maximum.subtract(BigInteger.ONE),(int)RAW);
        var postFrame=new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Frame(actual.snapshotId(),maximum,maximum,(int)RAW);
        var frozen=org.xar.ck3.control.wave2.governance.succession.SuccessionPolicy.freeze(
                new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.TurnBundle(oldFrame,
                        new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Actor(73,true),rows,74,
                        org.xar.ck3.control.wave2.governance.succession.SuccessionModel.RiskState.SINGLE_SUCCESSOR),"actual-episode",73);
        var reconciled=org.xar.ck3.control.wave2.governance.succession.SuccessionPolicy.reconcile(frozen,
                new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Snapshot(postFrame,"actual-episode",73,true,true,true,
                        "played_character_changed",new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Actor(74,true),false,false,
                        org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION),
                new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.TurnBundle(postFrame,
                        new org.xar.ck3.control.wave2.governance.succession.SuccessionModel.Actor(74,true),rows,74,
                        org.xar.ck3.control.wave2.governance.succession.SuccessionModel.RiskState.SINGLE_SUCCESSOR));
        var semantic=full.semantic().with("one_life_terminal_reason",new OpportunityJson.Text("played_character_changed"))
                .with("one_life_settlement",OpportunityJson.Nil.INSTANCE)
                .with("succession_reconciliation",OpportunityJson.parse(org.xar.ck3.control.wave2.governance.succession.SuccessionCodec.encodeReconciliation(reconciled)));
        var old=before.known;
        // This is serialized old DATA, never a private preclock permit for the successor.
        var stalePreclockSource=OpportunityJson.parse(StrictJson.canonical(ref(bytes("old-episode-preclock-data")).toJson()));
        var terminalFacts=new DriverSnapshotFacts.Known(old.driver(),old.stamp(),old.originalHistoryBasis(),old.actionRows(),
                old.auxiliary().with("family_marriage_ledger",OpportunityJson.Nil.INSTANCE)
                        .with("driver_preclock_expectation_source",stalePreclockSource),Optional.empty(),Optional.empty());
        byte[] originalAuxiliary=OpportunityJson.encode(terminalFacts.auxiliary());
        var reduced=LifecycleReducer.continueSuccessor(new LifecycleObservationPort.Snapshot(actual,before.source,semantic,terminalFacts,ref(actual.originalPacket())),
                "actual-successor-episode",AT.plusSeconds(1));
        assertFalse(reduced.auxiliary().members().containsKey("driver_preclock_expectation_source"));
        assertEquals(stalePreclockSource,terminalFacts.auxiliary().get("driver_preclock_expectation_source"));
        assertArrayEquals(originalAuxiliary,OpportunityJson.encode(terminalFacts.auxiliary()));
        byte[] originalBefore=beforeDriver.encode();
        // A completed worker or copied reconciliation is not the actual native character transition.
        // These source-backed scalar diagnostics remain DATA; they supply no terminal cause or preclock permit.
        var schedulerDiagnostic=OpportunityJson.parse(bytes("{\"selector_code\":57,\"controller_field\":608,\"independent_controller_literal\":10,\"independent_controller_field\":232,\"player_heir_character_id\":74}"));
        // The proved native last-reference path writes state3 before releasing its functor and allocator object.
        var releaseDiagnostic=OpportunityJson.parse(bytes("{\"state_after_last_release\":3,\"references_before_release\":1,\"references_after_release\":0}"));
        for (OpportunityJson.Value unprovedTerminal : List.<OpportunityJson.Value>of(OpportunityJson.Nil.INSTANCE,
                new OpportunityJson.Text("complete"), new OpportunityJson.Text("task_terminal"))) {
            var noNativeTransition=semantic.with("one_life_terminal_reason",unprovedTerminal)
                    .with("unqualified_scheduler_diagnostic",schedulerDiagnostic)
                    .with("unqualified_job_release_diagnostic",releaseDiagnostic);
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(
                    new LifecycleObservationPort.Snapshot(actual,before.source,noNativeTransition,terminalFacts,ref(actual.originalPacket())),
                    "unproved-terminal-episode",AT.plusSeconds(1)));
            assertArrayEquals(originalBefore,beforeDriver.encode());
        }
        var incomplete=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, StrictJson.parse(org.xar.ck3.control.wave2.governance.succession.SuccessionCodec.encodeReconciliation(reconciled)));
        incomplete.remove("predecessor_binding");
        var malformed=semantic.with("succession_reconciliation",OpportunityJson.parse(StrictJson.canonical(incomplete)));
        assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(
                new LifecycleObservationPort.Snapshot(actual,before.source,malformed,terminalFacts,ref(actual.originalPacket())),"bad-episode",AT.plusSeconds(1)));
        assertArrayEquals(originalBefore,beforeDriver.encode());
        Fixture current=new Fixture(reduced.driver(),maximum,maximum,AT.plusSeconds(2));
        M7KernelInputs service=current.service();service.capture(current.session,current.request,current.complete,"a".repeat(64),SOURCE,Optional.empty());
        var policy=new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE,ignored->Optional.empty(),
                (request,original,step,cap)->{throw new AssertionError("query cannot rewrite clock");},service);
        var result=assertInstanceOf(Replace.class,policy.evaluate(current.request,draft(command(current.request)))).draft();
        var consumed=M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
        assertEquals(73,consumed.observation().goal().originCharacterId());assertEquals(74,consumed.observation().goal().currentCharacterId());
        assertEquals(1,consumed.observation().goal().progress().reconciledSuccessions());
        assertEquals("actual-successor-episode",consumed.observation().episodeRunId());assertEquals(maximum,consumed.observation().nativeRevision());
        assertEquals(0,consumed.savedDayCredit());assertFalse(consumed.coldAuthorityGranted());
    }

    private static DriverStateSnapshot.Complete ordinaryDriver(long actor,String episode,OrdinaryCampaignGoal.Goal goal) {
        var lifecycle=StrictJson.object().put("schema","xar.ck3.succession-lifecycle-binding/v1").put("lifecycle","ordinary_campaign_succession")
                .put("xar_enabled","xar_off").put("pact_contract","absent_by_fresh_campaign_xar_off_contract")
                .put("source","whole-reducer-software").put("environment_sha256","a".repeat(64));
        return new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("software-pipe",321,BigInteger.valueOf(actor),episode),List.of(),
                new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.Value(StrictJson.canonical(lifecycle)),new DriverStateSnapshot.Value(GoalCodec.encodeGoal(goal)),new DriverStateSnapshot.Value(bytes("[]")));
    }

    @Test void completeDriverRejectsMissingGoalWhileExplicitNullRemainsARealNull() throws Exception {
        Fixture f = new Fixture(new DriverStateSnapshot.NullValue());
        var service = f.service(); service.capture(f.session, f.request, f.complete, "a".repeat(64), SOURCE, Optional.empty());
        assertTrue(service.current(f.request).isEmpty());
        assertSame(OpportunityJson.Nil.INSTANCE, f.complete.semantic().get("campaign_goal"));
        var original = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class, StrictJson.parse(f.known.driver().encode())); original.remove("campaign_goal");
        assertThrows(IllegalArgumentException.class, () -> DriverStateSnapshot.decodeComplete(StrictJson.canonical(original)));
        assertThrows(IllegalArgumentException.class, () -> new Fixture(new DriverStateSnapshot.Missing()));
    }

    @Test void failedNewCaptureRetiresTheOldRequestSlotAndDoesNotReuseAStaleGoal() throws Exception {
        Fixture f = new Fixture(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("actual-software-campaign", ACTOR.longValueExact()))));
        var service = f.service(); service.capture(f.session, f.request, f.complete, "a".repeat(64), SOURCE, Optional.empty());
        assertTrue(service.current(f.request).isPresent());
        var crossed = new DriverObservationAssembler.Complete(f.complete.identity(), f.complete.source(), "other-session",
                f.complete.connectionGeneration(), f.complete.semantic(), f.complete.originalEvidence(), AT, f.complete.fullBindingSha256());
        assertThrows(IllegalArgumentException.class, () -> service.capture(f.session, f.request, crossed,
                "a".repeat(64), SOURCE, Optional.empty()));
        assertTrue(service.current(f.request).isEmpty());
    }

    @Test void completeLookingFramesCannotCrossPublishedDriverTransportRevisionOrGoal() throws Exception {
        Fixture f = new Fixture(new DriverStateSnapshot.Value(GoalCodec.encodeGoal(
                OrdinaryCampaignGoal.newGoal("actual-software-campaign", ACTOR.longValueExact()))));
        M7KernelInputs.validateJoin(f.request, f.complete, f.known);
        var wrong = new DriverObservationFacts(f.facts.driver(), f.facts.driverVersion(), f.facts.episodeEpoch(),
                new NativeObservationPort.TransportSession(MACHINE,
                        new GameGeneration(321, new PythonOnlyUInt64(new BigInteger("18446744073709551614"))),
                        BigInteger.ONE, "held-session"), f.facts.snapshotId(), f.facts.nativeRevision(), f.facts.nativeStateSha256(),
                f.facts.publicRevision(), f.facts.observationVersion(), f.facts.source(), f.facts.originalSemanticFields(), f.facts.semanticFactsEvidence());
        var otherStamp = new DriverSnapshotFacts.Stamp(f.known.stamp().driverVersion(), f.known.stamp().episodeEpoch(),
                wrong.transport().game(), f.known.stamp().episodeRunId(), f.known.stamp().driverSha256());
        var differentBirth = new DriverSnapshotFacts.Known(f.known.driver(), otherStamp, f.known.originalHistoryBasis(),
                List.of(), f.known.auxiliary(), Optional.empty(), Optional.of(wrong));
        assertEquals(wrong.transport().game(), differentBirth.stamp().game());
        assertNotEquals(f.known.stamp().game(), differentBirth.stamp().game());
        assertThrows(IllegalArgumentException.class, () -> M7KernelInputs.validateJoin(f.request, f.complete, differentBirth));
        var missingFacts = new DriverSnapshotFacts.Known(f.known.driver(), f.known.stamp(), f.known.originalHistoryBasis(),
                List.of(), f.known.auxiliary(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> M7KernelInputs.validateJoin(f.request, f.complete, missingFacts));
        var changedGoal = f.complete.semantic().with("campaign_goal", OpportunityJson.Nil.INSTANCE);
        var changedComplete = new DriverObservationAssembler.Complete(f.complete.identity(), f.complete.source(), f.complete.sessionId(),
                f.complete.connectionGeneration(), changedGoal, f.complete.originalEvidence(), AT, f.complete.fullBindingSha256());
        assertThrows(IllegalArgumentException.class, () -> M7KernelInputs.validateJoin(f.request, changedComplete, f.known));
    }

    private static final class Fixture {
        private final G2Source source = new G2Source(MACHINE, AT.toString(), "software-only/.4", SOURCE);
        private final GameGeneration game = new GameGeneration(321,
                new PythonOnlyUInt64(new BigInteger("18446744073709551615")));
        private final DriverObservationFacts facts;
        private final DriverSnapshotFacts.Known known;
        private final DriverObservationAssembler.Complete complete;
        private final PlanningRequest request;
        private final NativeObservationPort.ObservedFrame actual;
        private final Session session = new Session();
        private Fixture(DriverStateSnapshot.Slot goal) throws Exception {
            this(goal,BigInteger.valueOf(14),BigInteger.valueOf(9));
        }
        private Fixture(DriverStateSnapshot.Slot goal,BigInteger publicRevision,BigInteger nativeRevision) throws Exception {
            this(new DriverStateSnapshot.Complete(
                    new DriverStateSnapshot.Session("software-pipe", 321, ACTOR, "actual-episode"), List.of(),
                    new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.NullValue(),
                    new DriverStateSnapshot.NullValue(), new DriverStateSnapshot.Value(bytes("\"ordinary_campaign\"")), goal,
                    new DriverStateSnapshot.Value(bytes("[]"))), publicRevision, nativeRevision);
        }
        private Fixture(DriverStateSnapshot.Complete driver,BigInteger publicRevision,BigInteger nativeRevision) throws Exception {
            this(driver,publicRevision,nativeRevision,AT);
        }
        private Fixture(DriverStateSnapshot.Complete driver,BigInteger publicRevision,BigInteger nativeRevision,Instant observedAt) throws Exception {
            String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":" + RAW
                    + ",\"played_character\":{\"character_id\":" + driver.session().actorId() + ",\"alive\":true},\"active_event\":null,"
                    + "\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[],"
                    + "\"diagnostics\":{\"bridge_pid\":321,\"connection_generation\":1}}";
            String snapshotId="actual-native-"+nativeRevision;
            byte[] envelope = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\""+snapshotId+"\",\"revision\":"+nativeRevision+",\"state\":" + state + "}");
            byte[] packet = ByteBuffer.allocate(envelope.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
            actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game,
                    BigInteger.ONE, "held-session"), snapshotId, nativeRevision, new RawJson(bytes(state)), packet, observedAt);
            facts = new DriverObservationFacts(driver, 3, 7, actual.session(), actual.snapshotId(), actual.nativeRevision(),
                    sha(actual.state().bytes()), publicRevision, 1, source, new OpportunityJson.Obj(Map.of()), ref(bytes("actual-observation-facts")));
            known = new DriverSnapshotFacts.Known(driver, new DriverSnapshotFacts.Stamp(3, 7, game, driver.session().episodeRunId(), sha(driver.encode())),
                    ref(driver.encode()), List.of(), new OpportunityJson.Obj(Map.of()), Optional.empty(), Optional.of(facts));
            complete = assertInstanceOf(DriverObservationAssembler.Complete.class,
                    new DriverObservationAssembler().assemble(actual, facts, ref(packet)));
            Optional<OrdinaryCampaignGoal.Goal> typedGoal = driver.campaignGoal() instanceof DriverStateSnapshot.Value retained
                    ? Optional.of(GoalCodec.parseGoal(StrictJson.parse(retained.json()))) : Optional.empty();
            var observations = new PlanningObservation(complete.semantic(), List.of(), Set.of(), Set.of(), Optional.empty(),
                    List.of(), typedGoal, Optional.empty(), false);
            request = new PlanningRequest(complete.identity(), source, "held-session", AT.plusSeconds(60), observations);
        }
        private M7KernelInputs service() {
            var state = new DriverFactsRepository(known);
            var assembler = new DriverStateAssembler(new ActionSnapshotReader(journal()), state,
                    ignored -> { throw new AssertionError("kernel supplier must not collect another native frame"); });
            return new M7KernelInputs(store(), borrowed -> assertSame(session, borrowed), assembler);
        }
        private ActionJournal journal() {
            return new ActionJournal() {
                public <T> T locked(Function<LockedJournal,T> work) { throw new AssertionError("no new writer scope"); }
                public <T> T locked(ContinuityStorePort.Session borrowed, Function<LockedJournal,T> work) {
                    assertSame(session, borrowed);
                    return work.apply(new LockedJournal() {
                        public Optional<ActionReceipt> find(String id) { return Optional.empty(); }
                        public List<ActionReceipt> unresolved() { return List.of(); }
                        public ActionReceipt append(ActionCommand command, String body, ActionState next) { throw new AssertionError("no action write"); }
                        public Snapshot snapshot() { return new Snapshot(0, session.head().digest(), List.of(), new BoundHistoryBasis(known.originalHistoryBasis())); }
                    });
                }
            };
        }
        private ContinuityStorePort store() {
            return new ContinuityStorePort() {
                public WriterContracts.Prepared preview(WriterContracts.Request request) { throw new AssertionError("no ledger write"); }
                public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw new AssertionError("no ledger write"); }
                public ExactRef persistedHead() { return session.persistedHead(); }
                public <T> T locked(SessionWork<T> work) throws IOException { return work.run(session); }
            };
        }
    }
    private static final class Session implements ContinuityStorePort.Session {
        private final ContinuityState state;
        private Session() {
            String raw = "{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"" + MACHINE
                    + "\",\"sequence\":0,\"window_id\":1,\"start_date_raw\":" + RAW + ",\"target_date_raw\":"
                    + (RAW + 100 * 24) + ",\"target_days\":100,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":" + RAW + "}";
            state = ContinuityState.fromJson((com.fasterxml.jackson.databind.node.ObjectNode) StrictJson.parse(bytes(raw)), MACHINE);
        }
        public void requireWriter(Path expected) { }
        public WriterContracts.Pin capturePin(ExactRef reference, int maximum) { throw new AssertionError("no physical file read"); }
        public void verifyPin(WriterContracts.Pin pin) { throw new AssertionError("no physical file read"); }
        public WriterContracts.Head head() { return new WriterContracts.Head(state, List.of(), List.of(), List.of(), false); }
        public WriterContracts.Prepared preview(WriterContracts.Request request) { throw new AssertionError("no ledger write"); }
        public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { throw new AssertionError("no ledger write"); }
        public ExactRef persistedHead() { return ref(state.canonicalBytes()); }
    }
    private static ActionCommand command(PlanningRequest request) {
        return new ActionCommand("software-query", request.before(), request.source(), request.sessionId(), new OperationKey("query-software-v1"),
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, request.before(), request.source(), "software/v1",
                        List.of(new ExpectedBoolean(new FieldKey("paused"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
    }
    private static Draft draft(ActionCommand command) {
        return new Draft("software-policy", "ordinary", "full capture fixture", Kind.ORDINARY, Optional.of(command), Purpose.READ_ONLY,
                Optional.empty(), new OpportunityJson.Obj(Map.of()));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] value) { return new ExactRef("software-only-" + sha(value), value.length, sha(value)); }
    private static String sha(byte[] value) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }

    @Test void signedActorsReachHeldNativeSupplierPolicyAndPersistedKernelConsumer() throws Exception {
        for(long actor:new long[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}) {
            var goal=OrdinaryCampaignGoal.newGoal("signed-application-campaign",actor);
            Fixture f=new Fixture(ordinaryDriver(actor,"actual-episode",goal),BigInteger.valueOf(14),BigInteger.valueOf(9));
            assertEquals(BigInteger.valueOf(actor),DriverStateSnapshot.decodeComplete(f.known.driver().encode()).session().actorId());
            var service=f.service();
            var captured=service.capture(f.session,f.request,f.complete,Optional.empty(),Optional.empty(),Optional.empty());
            assertEquals(f.complete.originalEvidence(),captured.originalNative());
            var policy=new M7CampaignPolicies.CampaignAdvancePolicy(SOURCE,ignored->Optional.empty(),
                    (request,original,step,cap)->{throw new AssertionError("query must retain the held native frame");},service);
            var result=assertInstanceOf(Replace.class,policy.evaluate(f.request,draft(command(f.request)))).draft();
            var consumed=M7KernelPlanConsumer.decode(OpportunityJson.encode(result.detail().get("m7_kernel_plan_consumption")));
            assertEquals(actor,consumed.observation().actorCharacterId());assertEquals(goal,consumed.observation().goal());
            assertEquals("18446744073709551615",consumed.observation().game().creationFiletime());
            assertEquals(consumed,M7KernelPlanConsumer.decode(M7KernelPlanConsumer.encode(consumed)));
            assertEquals(0,consumed.savedDayCredit());assertFalse(consumed.coldAuthorityGranted());
            assertFalse(consumed.gameActionsSubmitted());assertFalse(consumed.replayAuthorized());
        }
    }
}
