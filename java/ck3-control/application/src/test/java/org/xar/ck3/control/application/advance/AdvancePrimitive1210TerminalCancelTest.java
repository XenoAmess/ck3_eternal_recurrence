package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Offline protocol DATA exercising the real primitive observer and settlement validator.
 * The in-memory endpoint has no Game, transport, writer, installed permission or durable WAL authority.
 * Native 1.21.0 RunDateSentinelCancel1210 returns available with the retained terminal Status.
 */
final class AdvancePrimitive1210TerminalCancelTest {
    private static final Instant T = Instant.parse("2026-11-18T00:00:00Z");
    private static final Instant DEADLINE = T.plusSeconds(60);
    private static final String MACHINE = "cancel-1210-data", SESSION = "cancel-1210-session";
    private static final String ACTION_ID = "cancel-1210-command", SUBMIT_ID = "cancel-1210-native";
    private static final String STATUS_ID = "cancel-1210-independent-status", FULL_ID = "cancel-1210-independent-full";
    private static final String STEP = ClockStatusRead.CANCEL_PREFIX + "37";
    private static final int START = 53_176_992, END = START + 24;
    private static final ExactRef DEFINITION = ref("source-definition", 'a');
    private static final G2Source SOURCE = source(ExactCk3Build.CK3_1210.executableSha256());
    private static final GameGeneration GAME = new GameGeneration(4242, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
    private static final UUID EPOCH = UUID.fromString("5a888bd1-917f-494e-a695-f9e6bb972129");
    private static final Claims CLAIMS = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final Obj EMPTY = new Obj(Map.of());

    @Test void postResumeCleanupReopensTheActualPreparationInsteadOfDemandingTheEmptyWireProducer() {
        Fixture f=new Fixture(status(State.TRIGGERED,true),SOURCE);
        var prepared=f.attempt.preparedRequest();var wire=AdvancePrimitives.prepareRequest(f.command);
        assertNotEquals(wire,prepared,"the real preflight is immutable metadata, not a change to native wire fields");
        assertThrows(RuntimeException.class,()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,prepared,Optional.empty()));
        assertThrows(RuntimeException.class,()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,prepared,Optional.of(f.archive)));
        f.archive.preserveRequest(prepared);
        assertDoesNotThrow(()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,prepared,Optional.of(f.archive)));
        f.archive.preserveRequest(wire);
        assertThrows(RuntimeException.class,()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,wire,Optional.of(f.archive)));
        var crossed=new NativeRequest(prepared.step(),prepared.requiredCapability(),raw(new Obj(Map.of("extra",new Text("changed")))),prepared.preparationEvidence());
        f.archive.preserveRequest(crossed);
        assertThrows(RuntimeException.class,()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,crossed,Optional.of(f.archive)));
        f.archive.reads.clear();
        assertThrows(RuntimeException.class,()->LifePostResumePauseCleanupProof.requirePreparedOriginal(f.command,prepared,Optional.of(f.archive)));
    }

    @Test void terminalProofVersionCannotDowngradeOrTurnTriggeredIntoThePartialDateIdleBoundary() {
        var legacy=source("legacy-build");var before=new Fixture(status(State.IDLE,false),legacy);
        assertDoesNotThrow(()->LifePostResumePauseCleanupProof.requirePreparedOriginal(before.command,before.attempt.preparedRequest(),Optional.empty()));
        Obj v1=new Obj(Map.of("schema",new Text(LifePostResumePauseCleanupEvidence.TERMINAL_SCHEMA)));
        Obj v2=new Obj(Map.of("schema",new Text(LifePostResumePauseCleanupEvidence.TERMINAL_1210_SCHEMA)));
        assertTrue(LifePostResumePauseCleanupEvidence.isTerminalSchema(v1));assertTrue(LifePostResumePauseCleanupEvidence.isTerminalSchema(v2));
        assertDoesNotThrow(()->LifePostResumePauseCleanupEvidence.requireTerminalVersion(v1,legacy));
        assertDoesNotThrow(()->LifePostResumePauseCleanupEvidence.requireTerminalVersion(v2,SOURCE));
        assertThrows(IllegalArgumentException.class,()->LifePostResumePauseCleanupEvidence.requireTerminalVersion(v1,SOURCE));
        assertThrows(IllegalArgumentException.class,()->LifePostResumePauseCleanupEvidence.requireTerminalVersion(v2,legacy));
        var plan=new AdvancePlan(BigInteger.valueOf(START),BigInteger.valueOf(END),1,1,"cleanup-idle-boundary",true,AdvancePlan.ClockMode.EXACT_SENTINEL,Optional.empty());
        var triggered=new Fixture(status(State.TRIGGERED,true),SOURCE);triggered.qualify();
        assertThrows(IllegalArgumentException.class,()->AdvanceClock.validateCancellation(status(State.ARMED,false),triggered.independentStatus,plan,BigInteger.valueOf(START)));
        var idle=new Fixture(status(State.IDLE,false),SOURCE);idle.qualify();
        assertDoesNotThrow(()->AdvanceClock.validateCancellation(status(State.ARMED,false),idle.independentStatus,plan,BigInteger.valueOf(START)));
    }

    @Test void availableAckPreservesIdleTriggeredAndFailedAsTheirActualTerminalStates() {
        for (State state : List.of(State.IDLE, State.TRIGGERED, State.FAILED)) {
            Fixture f = new Fixture(status(state, true), SOURCE);
            byte[] original = ActionCodec.encodeCommand(f.command);
            ActionState.ControlApplied control = f.qualify();
            assertEquals(f.independentStatus, ClockStatusRead.decode(control.read().original()));
            assertTrue(control.actual().contains(new ExpectedText(new FieldKey("sentinel.state"), state.name().toLowerCase(java.util.Locale.ROOT))));
            assertTrue(control.actual().contains(new ExpectedText(new FieldKey("sentinel.generation"), "37")));
            assertEquals(2, f.statusReads, "actual preflight and independent post-ACK Status are distinct queries");
            assertTrue(f.fullReads > 0, "terminal cancellation needs its separate paused semantic observation");
            assertTrue(control.actual().contains(new ExpectedBoolean(new FieldKey("sentinel.cancel_confirmed"), true)));
            assertEquals(FullSnapshotSentinelCancellation.references(control), ActionEffects.supportingEvidence(control));
            assertTrue(ActionEffects.supportingEvidence(control).size() >= 6, "WAL must pin the real pre/Status/Full proof closure");
            assertArrayEquals(original, ActionCodec.encodeCommand(f.command));
            assertEquals(DEADLINE, control.read().request().deadline());
        }
    }

    /** Protocol DATA only: this does not impersonate the actual Root continuation/token issuer. */
    @Test void retainedPhysicalPreflightKeepsItsOriginalProfileAndCannotBeInventedFromATerminalSlot() {
        Fixture f=new Fixture(status(State.IDLE,false),SOURCE);
        var physical=physicalPreflightData(f);int queries=f.statusReads;
        f.retainedPreflight=Optional.of(new ClockStatusRead.Observation(ClockStatusRead.decode(physical.original()),physical,
                f.archive.referenceOf(physical.original())));
        NativeRequest retained=f.primitives.prepare(f.command);
        assertEquals(queries,f.statusReads,"the actual supplied preflight is retained without a substituted query");
        assertEquals(physical,FullSnapshotSentinelCancellation.preparedRead(f.command,retained,f.archive));
        assertEquals(PhysicalStatusIdentity.CONTRACT_ID,f.archive.loadRead(retained.preparationEvidence().getFirst()).contractId());
        assertInstanceOf(CommandOrigin.PhysicalStatusOnly.class,physical.request().origin());
        Fixture terminal=new Fixture(status(State.TRIGGERED,true),SOURCE);
        var wrong=physicalPreflightData(terminal);
        terminal.retainedPreflight=Optional.of(new ClockStatusRead.Observation(ClockStatusRead.decode(wrong.original()),wrong,
                terminal.archive.referenceOf(wrong.original())));
        assertThrows(RuntimeException.class,()->terminal.primitives.prepare(terminal.command));
    }
    private static PlanningReadReceipt physicalPreflightData(Fixture f) {
        var before=f.archive.loadRead(f.attempt.preparedRequest().preparationEvidence().getFirst());
        var owner=new NativeObservationPort.TransportSession(MACHINE,GAME,BigInteger.ONE,SESSION);
        var physical=new PhysicalStatusIdentity(owner,"native:10",BigInteger.TEN,SOURCE,f.basis.originalEvidence(),DEFINITION,DEFINITION,
                Optional.empty(),Optional.empty(),T.minusMillis(20));
        var operation=new OperationKey(ClockStatusRead.STEP);
        var binding=new GuardEvidence(new CommandOrigin.PhysicalStatusOnly(physical),SOURCE,SESSION,BigInteger.ONE,operation,
                physical.nativeEvidence(),physical.helloEvidence(),"offline-physical-DATA",physical.observedAt(),DEADLINE,List.of(DEFINITION));
        var guard=new PlanningReadGuard(binding,new PlanningReadGuard.PhysicalStatus(physical),PhysicalStatusIdentityCodec.bindingSha256(physical));
        var request=PlanningReadRequest.newStatusOnly(physical,operation,EMPTY,DEADLINE);
        var read=new PlanningReadReceipt(request,PhysicalStatusIdentity.CONTRACT_ID,before.requestId(),guard,guard,before.original());
        f.archive.preserveRead(read);return read;
    }

    @Test void coldReadClassificationNeedsTheRealOriginalPreflightAndPositiveAck() {
        Fixture f = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ActionState.ControlApplied confirmation = f.qualify();
        ActionReceipt pending = new ActionReceipt(1, 1, f.command, ActionCodec.bodySha256(f.command),
                new ActionState.AckReceived(f.attempt, f.submitted));
        assertTrue(FullSnapshotSentinelCancellation.isPositiveAckCancellation(pending, f.archive));
        var observedUnknown = new ActionReceipt(1, 1, f.command, pending.bodySha256(),
                new ActionState.Unknown(Optional.of(f.attempt), Optional.of(f.submitted), "independent observation unavailable", List.of()));
        assertTrue(FullSnapshotSentinelCancellation.isPositiveAckCancellation(observedUnknown, f.archive),
                "the real retained positive ACK admits only observation, never another CANCEL");
        var unacknowledged = new ActionReceipt(1, 1, f.command, pending.bodySha256(),
                new ActionState.Unknown(Optional.of(f.attempt), Optional.of(new NativeActionPort.Unknown(SUBMIT_ID,
                        "actual original write outcome unknown", f.submitted.outbound().orElseThrow().originalPacket(), Optional.empty())),
                        "no original positive ACK", List.of()));
        assertFalse(FullSnapshotSentinelCancellation.isPositiveAckCancellation(unacknowledged, f.archive));
        var noPreflight = new ActionState.Attempt(f.attempt.requestId(), f.attempt.submittedAt(), f.attempt.guard(),
                AdvancePrimitives.prepareRequest(f.command));
        assertFalse(FullSnapshotSentinelCancellation.isPositiveAckCancellation(new ActionReceipt(1, 1, f.command,
                pending.bodySha256(), new ActionState.AckReceived(noPreflight, f.submitted)), f.archive));
        assertFalse(FullSnapshotSentinelCancellation.isPositiveAckCancellation(new ActionReceipt(1, 2, f.command,
                pending.bodySha256(), new ActionState.Settled(f.attempt, f.submitted, confirmation)), f.archive));
    }

    @Test void evaluationFailureCannotRelabelNativeAccessCleanupUnknownAsConfirmedCancellation() {
        ObjectNode raw = SentinelObservation.toJson(status(State.FAILED, true)).deepCopy();
        raw.put("trigger_flags", 1 | (1 << 15));
        raw.putArray("trigger_reasons").add("date_deadline").add("evaluation_failure");
        assertThrows(RuntimeException.class,()->new Fixture(SentinelObservation.decode(raw),SOURCE,SentinelObservation.decode(raw)),
                "a real failed preflight cannot issue a new CANCEL preparation");
        Fixture unknown = new Fixture(SentinelObservation.decode(raw), SOURCE);
        assertThrows(RuntimeException.class, unknown::qualify);
        var pending = new ActionReceipt(1, 1, unknown.command, ActionCodec.bodySha256(unknown.command),
                new ActionState.AckReceived(unknown.attempt, unknown.submitted));
        assertFalse(FullSnapshotSentinelCancellation.isPositiveAckCancellation(pending, unknown.archive),
                "existing 20-field Status cannot grant success for a latched native access cleanup UNKNOWN");
    }

    @Test void legacyCanceledIdleKeepsTheOriginalContractAndDoesNotAcquireAvailableSemantics() {
        Fixture f = new Fixture(status(State.IDLE, false), source(ExactCk3Build.CK3_12004.executableSha256()));
        f.ackStatus = "canceled";
        ActionState.ControlApplied control = f.qualify();
        assertEquals(State.IDLE, ClockStatusRead.decode(control.read().original()).state());
        assertEquals(List.of(new ExpectedText(new FieldKey("sentinel.state"), "idle"),
                new ExpectedText(new FieldKey("sentinel.generation"), "37")), f.command.expected().values());
        for (String rawBuild : List.of("1.21.0", "1.21.0@sha256:" + ExactCk3Build.CK3_1210.executableSha256(),
                ExactCk3Build.CK3_12004.executableSha256(), "unknown-build")) {
            Fixture wrongBranch = new Fixture(status(State.TRIGGERED, true), source(rawBuild));
            assertThrows(RuntimeException.class, wrongBranch::qualify, "available terminal acceptance must use the exact raw 1210 executable SHA");
        }
    }

    @Test void availableAckAloneAndAnArmedOrUnobservedPauseNeverConfirmCancellation() {
        for (State state : List.of(State.ARMED, State.UNAVAILABLE)) {
            Fixture f = new Fixture(status(state, false), SOURCE);
            assertThrows(RuntimeException.class, f::qualify);
        }
        for (State state : List.of(State.TRIGGERED, State.FAILED)) {
            Fixture f = new Fixture(status(state, false), SOURCE);
            assertThrows(RuntimeException.class, f::qualify, "a terminal label without pauseObserved cannot prove a safe clock boundary");
        }
        Fixture absent = new Fixture(status(State.TRIGGERED, true), SOURCE);
        absent.statusUnavailable = true;
        assertThrows(RuntimeException.class, absent::qualify);
    }

    @Test void everyRetainedStatusFieldMustMatchTheIndependentOriginalRatherThanJustGeneration() {
        for (String field : List.of("starting_date_raw", "target_date_raw", "last_observed_date_raw", "trigger_date_raw", "speed",
                "army_count", "combat_count", "completed_daily_ticks", "intermediate_pause_count", "signed_date_delta_from_target_raw", "overshoot_days")) {
            Fixture f = new Fixture(status(State.TRIGGERED, true), SOURCE);
            ObjectNode changed = SentinelObservation.toJson(f.ackSentinel).deepCopy();
            changed.put(field, changed.path(field).longValue() + 1);
            f.ackSentinel = SentinelObservation.decode(changed);
            assertThrows(RuntimeException.class, f::qualify, "ACK and independent Status differ at " + field);
        }
        Fixture state = new Fixture(status(State.TRIGGERED, true), SOURCE);
        state.ackSentinel = status(State.FAILED, true);
        assertThrows(RuntimeException.class, state::qualify);
        Fixture mode = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ObjectNode changedMode = SentinelObservation.toJson(mode.ackSentinel).deepCopy();
        changedMode.put("mode", "decision_epoch"); mode.ackSentinel = SentinelObservation.decode(changedMode);
        assertThrows(RuntimeException.class, mode::qualify);
        Fixture pause = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ObjectNode changedPause = SentinelObservation.toJson(pause.ackSentinel).deepCopy();
        changedPause.put("pause_wrapper_called", false); pause.ackSentinel = SentinelObservation.decode(changedPause);
        assertThrows(RuntimeException.class, pause::qualify);
        Fixture pauseObserved = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ObjectNode changedObserved = SentinelObservation.toJson(pauseObserved.ackSentinel).deepCopy();
        changedObserved.put("pause_observed", false); pauseObserved.ackSentinel = SentinelObservation.decode(changedObserved);
        assertThrows(RuntimeException.class, pauseObserved::qualify);
        Fixture flags = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ObjectNode changedFlags = SentinelObservation.toJson(flags.ackSentinel).deepCopy();
        changedFlags.put("trigger_flags", 257).put("terminal_observed", true);
        changedFlags.putArray("trigger_reasons").add("date_deadline").add("combat_terminal");
        flags.ackSentinel = SentinelObservation.decode(changedFlags);
        assertThrows(RuntimeException.class, flags::qualify);
    }

    @Test void aMatchingForeignGenerationOrNonTerminalWatchTupleIsNotOurRequestedCancel() {
        for (String field : List.of("generation", "army_count", "mode")) {
            ObjectNode changed = SentinelObservation.toJson(status(State.TRIGGERED, true)).deepCopy();
            if (field.equals("mode")) changed.put(field, "decision_epoch");
            else changed.put(field, field.equals("generation") ? 38 : 1);
            Fixture f = new Fixture(SentinelObservation.decode(changed), SOURCE);
            assertThrows(RuntimeException.class, f::qualify, "exact generation and ordinary terminal-a-0 ownership required: " + field);
        }
    }

    @Test void acceptedStepStatusAndOriginalSuccessfulAckAreAllRequired() {
        for (String wrongStatus : List.of("canceled", "submitted", "unavailable", "already_satisfied")) {
            Fixture f = new Fixture(status(State.TRIGGERED, true), SOURCE); f.ackStatus = wrongStatus;
            assertThrows(RuntimeException.class, f::qualify);
        }
        Fixture unaccepted = new Fixture(status(State.TRIGGERED, true), SOURCE); unaccepted.accepted = false;
        assertThrows(RuntimeException.class, unaccepted::qualify);
        Fixture wrongStep = new Fixture(status(State.TRIGGERED, true), SOURCE); wrongStep.ackStep = ClockStatusRead.CANCEL_PREFIX + "38";
        assertThrows(RuntimeException.class, wrongStep::qualify);
        Fixture noToken = new Fixture(status(State.TRIGGERED, true), SOURCE); noToken.tokenPresent = false;
        assertThrows(RuntimeException.class, noToken::qualify);
        Fixture rejected = new Fixture(status(State.TRIGGERED, true), SOURCE); rejected.nativeOk = false;
        assertThrows(RuntimeException.class, rejected::qualify);
    }

    @Test void pausedIndependentFullCannotBeReplacedByRunningMapUnavailableOrAckEvidence() {
        Fixture running = new Fixture(status(State.TRIGGERED, true), SOURCE);
        running.fullSemantic = running.fullSemantic.with("paused", new Bool(false));
        assertThrows(RuntimeException.class, running::qualify);
        Fixture noMap = new Fixture(status(State.TRIGGERED, true), SOURCE);
        noMap.fullSemantic = noMap.fullSemantic.with("map_ready", new Bool(false));
        assertThrows(RuntimeException.class, noMap::qualify);
        Fixture ackProvenance = new Fixture(status(State.TRIGGERED, true), SOURCE);
        ackProvenance.fullProvenance = new ObservationProvenance.Query(SUBMIT_ID);
        assertThrows(RuntimeException.class, ackProvenance::qualify);
        Fixture statusProvenance = new Fixture(status(State.TRIGGERED, true), SOURCE);
        statusProvenance.fullProvenance = new ObservationProvenance.Query(STATUS_ID);
        assertThrows(RuntimeException.class, statusProvenance::qualify);
        Fixture old = new Fixture(status(State.TRIGGERED, true), SOURCE); old.fullObservedAt = T.plusMillis(5);
        assertThrows(RuntimeException.class, old::qualify);
        Fixture regressed = new Fixture(status(State.TRIGGERED, true), SOURCE);
        regressed.fullSemantic = regressed.fullSemantic.with("snapshot_id", new Text("native:9"))
                .with("revision", number(9)).with("native_revision", number(9));
        assertThrows(RuntimeException.class, regressed::qualify);
    }

    @Test void independentFullRetainsExactSourceSessionGamePlayerEpisodeAndStableDate() {
        for (String component : List.of("source", "session", "game", "player", "episode", "date")) {
            Fixture f = new Fixture(status(State.TRIGGERED, true), SOURCE);
            switch (component) {
                case "source" -> f.fullSource = new G2Source(MACHINE, T.plusSeconds(1).toString(), SOURCE.exactBuild(), DEFINITION);
                case "session" -> f.fullSession = SESSION + "-foreign";
                case "game" -> f.fullGame = new GameGeneration(4243, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
                case "player" -> f.fullSemantic = f.fullSemantic.with("played_character", new Obj(Map.of("character_id", number(8), "alive", new Bool(true))));
                case "episode" -> f.fullSemantic = f.fullSemantic.with("episode_run_id", new Text("foreign-episode"));
                case "date" -> f.fullSemantic = f.fullSemantic.with("date_raw", number(END + 24));
                default -> fail("unknown component");
            }
            assertThrows(RuntimeException.class, f::qualify, "independent Full crossed " + component);
        }
    }

    @Test void aTerminalAckCannotInventAnAbsentOriginalPreflight() {
        Fixture missing = new Fixture(status(State.TRIGGERED, true), SOURCE);
        missing.dropPreparation = true;
        assertThrows(RuntimeException.class, missing::qualify);
    }

    @Test void originalAckAndStatusCustodyCannotBeMissingCrossedOrPreAck() {
        Fixture noAckCustody = new Fixture(status(State.TRIGGERED, true), SOURCE); noAckCustody.ackCustody = false;
        assertThrows(RuntimeException.class, noAckCustody::qualify);
        Fixture noQueryCustody = new Fixture(status(State.TRIGGERED, true), SOURCE); noQueryCustody.queryCustody = false;
        assertThrows(RuntimeException.class, noQueryCustody::qualify);
        Fixture preAck = new Fixture(status(State.TRIGGERED, true), SOURCE); preAck.statusOrder = 1; preAck.statusAt = T;
        assertThrows(RuntimeException.class, preAck::qualify);
        Fixture otherOwner = new Fixture(status(State.TRIGGERED, true), SOURCE); otherOwner.queryConnection = BigInteger.TWO;
        assertThrows(RuntimeException.class, otherOwner::qualify);
        Fixture expiredStatus = new Fixture(status(State.TRIGGERED, true), SOURCE); expiredStatus.statusAt = DEADLINE.plusMillis(1);
        assertThrows(RuntimeException.class, expiredStatus::qualify);
        Fixture expiredFull = new Fixture(status(State.TRIGGERED, true), SOURCE); expiredFull.fullObservedAt = DEADLINE.plusMillis(1);
        assertThrows(RuntimeException.class, expiredFull::qualify);
    }

    /** Protocol DATA: recognition alone never grants source/Root, dispatch, retry or parent completion authority. */
    @Test void zeroWriteInitializationKeepsActualPreflightAndReopensItsOriginals() {
        Fixture f = new Fixture(status(State.IDLE, false), SOURCE);
        var child = zeroWriteData(f, f.attempt.preparedRequest());
        assertTrue(LifeAdvanceComposite.isZeroWriteInitializationCancellation(child));
        assertThrows(RuntimeException.class, () -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(child, f.archive),
                "a matching preparation shape cannot replace the archived request original");
        f.archive.preserveRequest(f.attempt.preparedRequest());
        assertDoesNotThrow(() -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(child, f.archive));
        f.archive.outcomes.clear();
        assertThrows(RuntimeException.class, () -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(child, f.archive),
                "the original zero-write dispatch must still be readable");
        f.archive.preserve(((ActionState.RejectedBeforeDispatch) child.state()).dispatch());
        f.archive.reads.clear();
        assertThrows(RuntimeException.class, () -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(child, f.archive),
                "the exact preflight original must still be readable");
    }

    @Test void zeroWriteInitializationRejectsEmptyOrChangedWireAndPreservesUnknown() {
        Fixture f = new Fixture(status(State.IDLE, false), SOURCE);
        var prepared = f.attempt.preparedRequest();
        assertFalse(LifeAdvanceComposite.isZeroWriteInitializationCancellation(zeroWriteData(f, AdvancePrimitives.prepareRequest(f.command))));
        var changed = new NativeRequest(prepared.step(), prepared.requiredCapability(), raw(new Obj(Map.of("extra", new Text("changed")))), prepared.preparationEvidence());
        assertFalse(LifeAdvanceComposite.isZeroWriteInitializationCancellation(zeroWriteData(f, changed)));
        assertThrows(IllegalArgumentException.class, () -> new NativeRequest(prepared.step(), prepared.requiredCapability(), prepared.additionalFields(),
                List.of(prepared.preparationEvidence().getFirst(), prepared.preparationEvidence().getFirst())));
        var multiple = new NativeRequest(prepared.step(), prepared.requiredCapability(), prepared.additionalFields(),
                List.of(prepared.preparationEvidence().getFirst(), ref("additional-preflight", 'c')));
        assertFalse(LifeAdvanceComposite.isZeroWriteInitializationCancellation(zeroWriteData(f, multiple)));
        var unknown = new ActionReceipt(1, 1, f.command, ActionCodec.bodySha256(f.command),
                new ActionState.Unknown(Optional.of(f.attempt), Optional.empty(), "original write outcome unknown", List.of()));
        assertFalse(LifeAdvanceComposite.isZeroWriteInitializationCancellation(unknown));
        assertThrows(RuntimeException.class, () -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(unknown, f.archive));
    }

    @Test void legacyZeroWriteInitializationStillRequiresItsOriginalEmptyPreparation() {
        Fixture f = new Fixture(status(State.IDLE, false), source(ExactCk3Build.CK3_12004.executableSha256()));
        var child = zeroWriteData(f, f.attempt.preparedRequest());
        assertTrue(LifeAdvanceComposite.isZeroWriteInitializationCancellation(child));
        assertEquals(AdvancePrimitives.prepareRequest(f.command), f.attempt.preparedRequest());
        assertDoesNotThrow(() -> LifeAdvanceComposite.requireZeroWriteInitializationCancellationOriginal(child, f.archive));
    }

    private static ActionReceipt zeroWriteData(Fixture f, NativeRequest prepared) {
        var attempt = new ActionState.Attempt(f.attempt.requestId(), f.attempt.submittedAt(), f.attempt.guard(), prepared);
        var zero = new NativeActionPort.RejectedBeforeDispatch(attempt.requestId(), new NativeActionPort.ZeroDispatchProof(
                NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "offline zero-write DATA", Optional.empty()));
        f.archive.preserve(zero);
        return new ActionReceipt(1, 1, f.command, ActionCodec.bodySha256(f.command), new ActionState.RejectedBeforeDispatch(attempt, zero));
    }

    private static ExactRef ref(String name, char digest) { return new ExactRef("D:/software-fixtures/cancel1210/" + name, 1, String.valueOf(digest).repeat(64)); }
    private static G2Source source(String build) { return new G2Source(MACHINE, T.toString(), build, DEFINITION); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static RawJson raw(Obj value) { return new RawJson(encode(value)); }
    private static Status status(State state, boolean pauseObserved) {
        boolean terminal = state == State.TRIGGERED || state == State.FAILED;
        return new Status(state, new CrossJsDecimalUInt64("37"), START, END, terminal ? END : START,
                terminal ? END : 0, 1, Mode.TERMINAL_OR_SENTINEL, 0, 0, terminal ? 1 : 0, 0, terminal ? 1 : 0,
                terminal ? List.of("date_deadline") : List.of(), 0, terminal ? 0 : -1,
                terminal, terminal && pauseObserved, false, state == State.FAILED);
    }
    private static Obj token(String step, String resultStatus, Status sentinel, boolean accepted) {
        return new Obj(Map.of("step", new Text(step), "accepted", new Bool(accepted), "status", new Text(resultStatus),
                "tactical_daily_sentinel", parse(StrictJson.canonical(SentinelObservation.toJson(sentinel)))));
    }
    private static Obj semantic(Status status, int revision) {
        return object(parse(("""
                {"snapshot_id":"native:%d","revision":%d,"native_revision":%d,"date_raw":%d,
                 "paused":true,"map_ready":true,"speed":1,"episode_run_id":"cancel-1210-episode","episode_character_id":7,
                 "played_character":{"character_id":7,"alive":true},"active_event":null,
                 "pending_character_interaction":null,"one_life_terminal_reason":null,"diagnostics":{},"player_armies":[],"active_wars":[]}
                """).formatted(revision, revision, revision, status.lastObservedDateRaw()).getBytes(StandardCharsets.UTF_8)), "full semantic DATA");
    }
    private static ObservationIdentity identity(Obj semantic, G2Source source, GameGeneration game) {
        return new ObservationIdentity(source.machineId(), game,
                new ProposalFrame(new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(
                        integer(object(semantic.get("played_character"), "player").get("character_id"), "id"),
                        integer(semantic.get("native_revision"), "native_revision"), integer(semantic.get("date_raw"), "date_raw")),
                        text(semantic.get("snapshot_id"), "snapshot_id"), integer(semantic.get("revision"), "revision"),
                        text(semantic.get("episode_run_id"), "episode")), 1);
    }
    private static byte[] packet(RawJson raw) {
        byte[] bytes = raw.bytes(); return ByteBuffer.allocate(bytes.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
    }

    private static final class Fixture implements AdvanceObservationPort, PlanningReadPort {
        final MemoryArchive archive = new MemoryArchive();
        final G2Source source;
        final AdvanceObservationPort.Frame basis;
        final ActionCommand command;
        final ActionState.Attempt attempt;
        final AdvancePrimitives primitives;
        final Status independentStatus;
        final Status preStatus;
        boolean preparing, dropPreparation;
        NativeActionPort.AckReceived submitted;
        Status ackSentinel;
        String ackStatus = "available", ackStep = STEP;
        boolean accepted = true, nativeOk = true, tokenPresent = true, ackCustody = true, queryCustody = true, statusUnavailable;
        BigInteger queryConnection = BigInteger.ONE;
        long statusOrder = 7;
        Instant statusAt = T.plusMillis(10), fullObservedAt = T.plusMillis(30);
        Obj fullSemantic;
        G2Source fullSource;
        String fullSession = SESSION;
        GameGeneration fullGame = GAME;
        ObservationProvenance fullProvenance;
        Optional<ClockStatusRead.Observation> retainedPreflight=Optional.empty();
        int statusReads, fullReads;
        final List<Instant> requestedDeadlines = new ArrayList<>();
        Fixture(Status status, G2Source source) {
            this(status,source,status.lastObservedDateRaw()==END?status(status.state()==State.FAILED?State.FAILED:State.TRIGGERED,true):status(State.ARMED,false));
        }
        Fixture(Status status,G2Source source,Status actualBefore) {
            this.independentStatus = status; this.ackSentinel = status; this.source = source; this.fullSource = source;
            preStatus = actualBefore;
            Obj before = semantic(preStatus, 10); fullSemantic = semantic(status, 11);
            ExactRef driver = archive.preserveMaterial(raw(new Obj(Map.of("schema", new Text("offline-driver-DATA")))));
            fullSemantic = fullSemantic.with("java_driver_facts_evidence", parse(StrictJson.canonical(driver.toJson())));
            ExactRef evidence = archive.preserveMaterial(raw(before));
            basis = new AdvanceObservationPort.Frame(identity(before, source, GAME), source, SESSION, before,
                    "cancel-1210-basis-query", T.minusMillis(20), evidence);
            OperationKey operation = new OperationKey(STEP);
            command = new ActionCommand(ACTION_ID, basis.identity(), source, SESSION, operation, EMPTY,
                    AdvancePrimitives.expected(basis.identity(), source, operation, EMPTY), CLAIMS, DEADLINE);
            primitives = new AdvancePrimitives(this, new ClockStatusRead(this, DEFINITION, archive), Clock.fixed(T, ZoneOffset.UTC), 1);
            preparing = true;
            NativeRequest prepared;
            try { prepared = primitives.prepare(command); } finally { preparing = false; }
            attempt = new ActionState.Attempt(SUBMIT_ID, T, guard(operation, basis, T.minusMillis(20)), prepared);
        }
        ActionState.ControlApplied qualify() {
            NativeActionPort.AckReceived ack = ack(SUBMIT_ID, ackStep, token(ackStep, ackStatus, ackSentinel, accepted),
                    4, T, BigInteger.ONE, nativeOk, tokenPresent, ackCustody);
            submitted = ack;
            ActionState.Attempt observedAttempt = dropPreparation ? new ActionState.Attempt(attempt.requestId(), attempt.submittedAt(),
                    attempt.guard(), AdvancePrimitives.prepareRequest(command)) : attempt;
            ActionPorts.PostconditionResult observed = primitives.observe(command, observedAttempt, ack);
            if (!(observed instanceof ActionPorts.ControlObserved control))
                throw new IllegalArgumentException("CANCEL has no confirmed control postcondition: " + observed);
            ActionEffects.validate(command, observedAttempt, ack, control.observation());
            assertTrue(requestedDeadlines.stream().allMatch(DEADLINE::equals), "observation cannot refresh the original command deadline");
            return control.observation();
        }
        @Override public Optional<ClockStatusRead.Observation> retainedCancellationPreflight(ActionCommand command,Instant deadline) {
            return retainedPreflight;
        }
        @Override public <R> R withClockControlBasis(ActionCommand command, Instant deadline, java.util.function.Function<AdvanceObservationPort.Frame, R> work) {
            requestedDeadlines.add(deadline); return work.apply(basis);
        }
        @Override public AdvanceObservationPort.Frame current(ActionCommand command, Instant deadline) {
            requestedDeadlines.add(deadline); fullReads++;
            ExactRef original = archive.preserveMaterial(raw(new Obj(Map.of("semantic", fullSemantic, "query_id", new Text(FULL_ID)))));
            ObservationProvenance provenance = fullProvenance;
            if (provenance == null) {
                var fullAck = ack(FULL_ID, "query-fresh-full-state-v1", token("query-fresh-full-state-v1", "available", independentStatus, true),
                        10, T.plusMillis(20), BigInteger.ONE, true, true, true);
                provenance = new ObservationProvenance.FreshSnapshotQuery(FULL_ID, archive.referenceOf(fullAck),
                        new NativeRequestChronology.Event(BigInteger.valueOf(13), fullObservedAt),
                        new ObservationProvenance.LiveAfterSetter(archive.referenceOf(submitted)));
            }
            return new AdvanceObservationPort.Frame(identity(fullSemantic, fullSource, fullGame), fullSource, fullSession,
                    fullSemantic, provenance, fullObservedAt, original);
        }
        @Override public AdvanceObservationPort.Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) { return current(command, deadline); }
        @Override public <R> PlanningReadResult<R> read(ReadContract<R> contract, PlanningReadRequest request) {
            statusReads++; requestedDeadlines.add(request.deadline());
            if (statusUnavailable) return new PlanningReadResult.Unavailable<>("offline fixture withheld independent Status", Optional.empty());
            GuardEvidence binding = guard(request.operation(), basis, T.minusMillis(20));
            PlanningReadGuard readGuard = new PlanningReadGuard(binding, true, true, true, "b".repeat(64));
            String id = preparing ? "cancel-1210-preflight-status" : STATUS_ID;
            NativeActionPort.AckReceived ack = ack(id, ClockStatusRead.STEP,
                    token(ClockStatusRead.STEP, "available", preparing ? preStatus : independentStatus, true),
                    preparing ? 1 : statusOrder, preparing ? T.minusMillis(20) : statusAt,
                    preparing ? BigInteger.ONE : queryConnection, true, true, preparing || queryCustody);
            var receipt = new PlanningReadReceipt(request, contract.contractId(), id, readGuard, readGuard, ack);
            return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, archive.preserveRead(receipt));
        }
        private GuardEvidence guard(OperationKey operation, AdvanceObservationPort.Frame frame, Instant at) {
            return new GuardEvidence(frame.identity(), source, SESSION, BigInteger.ONE, operation,
                    frame.originalEvidence(), DEFINITION, "cancel-1210-offline-authority-DATA", at, DEADLINE);
        }
        private NativeActionPort.AckReceived ack(String id, String step, Obj token, long order, Instant entered,
                BigInteger connection, boolean ok, boolean includeToken, boolean includeCustody) {
            RawJson outgoing = raw(new Obj(Map.of("type", new Text("execute_step"), "protocol_version", number(1),
                    "request_id", new Text(id), "step", new Text(step), "expected_revision", number(10))));
            RawJson incoming = raw(new Obj(Map.of("type", new Text("command_result"), "protocol_version", number(1),
                    "request_id", new Text(id), "ok", new Bool(ok), "result", token)));
            byte[] outbound = packet(outgoing), inbound = packet(incoming);
            var held = new NativeObservationPort.TransportSession(source.machineId(), GAME, connection, SESSION);
            var chronology = new NativeRequestChronology(held, EPOCH, id,
                    NativeRequestChronology.PacketIdentity.of(outbound), NativeRequestChronology.PacketIdentity.of(inbound),
                    new NativeRequestChronology.Event(BigInteger.valueOf(order), entered),
                    new NativeRequestChronology.Event(BigInteger.valueOf(order + 1), entered.plusMillis(1)),
                    new NativeRequestChronology.Event(BigInteger.valueOf(order + 2), entered.plusMillis(2)));
            var result = new NativeActionPort.AckReceived(id, ok, includeToken ? Optional.of(raw(token)) : Optional.empty(), incoming, inbound,
                    Optional.of(new NativeActionPort.OutboundPacket(id, outbound)), includeCustody ? Optional.of(chronology) : Optional.empty());
            archive.preserve(result); return result;
        }
    }

    /** Deliberately local DATA storage; this class does not stand in for the real canonical archive. */
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, RawJson> materials = new HashMap<>();
        private final Map<ExactRef, NativeRequest> requests = new HashMap<>();
        private final Map<ExactRef, NativeActionPort.DispatchOutcome> outcomes = new HashMap<>();
        private final Map<NativeActionPort.DispatchOutcome, ExactRef> outcomeRefs = new HashMap<>();
        private final Map<ExactRef, PlanningReadReceipt> reads = new HashMap<>();
        private final Map<PlanningReadReceipt, ExactRef> readRefs = new HashMap<>();
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) {
            RawJson body = value instanceof NativeActionPort.AckReceived ack ? ack.originalFrame() : raw(new Obj(Map.of("request_id", new Text(value.requestId()))));
            ExactRef ref = preserveMaterial(body); outcomes.put(ref, value); outcomeRefs.put(value, ref); return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { return Optional.ofNullable(outcomes.get(ref)).orElseThrow(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return Optional.ofNullable(outcomeRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) {
            preserve(value.original()); ExactRef ref = preserveMaterial(raw(new Obj(Map.of("request_id", new Text(value.requestId()), "contract_id", new Text(value.contractId())))));
            reads.put(ref, value); readRefs.put(value, ref); return ref;
        }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { return Optional.ofNullable(reads.get(ref)).orElseThrow(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return Optional.ofNullable(readRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) {
            String sha = ActionCodec.sha256(value.bytes()); ExactRef ref = new ExactRef("D:/software-fixtures/cancel1210/archive/" + sha + ".json", value.bytes().length, sha);
            materials.put(ref, value); return ref;
        }
        @Override public RawJson loadMaterial(ExactRef ref) { return Optional.ofNullable(materials.get(ref)).orElseThrow(); }
        @Override public RawJson loadFullMaterial(ExactRef ref) { return RawJson.fullMaterial(loadMaterial(ref).bytes()); }
        @Override public ExactRef materialReferenceOf(RawJson value) {
            String sha = ActionCodec.sha256(value.bytes()); ExactRef ref = new ExactRef("D:/software-fixtures/cancel1210/archive/" + sha + ".json", value.bytes().length, sha);
            if (!value.equals(materials.get(ref))) throw unused(); return ref;
        }
        private static IllegalStateException unused() { return new IllegalStateException("unavailable archive operation in offline cancel fixture"); }
        @Override public ExactRef preserveRequest(NativeRequest value) {
            var row=StrictJson.object().put("step",value.step()).put("capability",value.requiredCapability().orElse(""));
            row.set("fields",StrictJson.parse(value.additionalFields().bytes()));var refs=row.putArray("preparation");value.preparationEvidence().forEach(ref->refs.add(ref.toJson()));
            var ref=preserveMaterial(new RawJson(StrictJson.canonical(row)));requests.put(ref,value);return ref;
        }
        @Override public NativeRequest loadRequest(ExactRef ref) { return Optional.ofNullable(requests.get(ref)).orElseThrow(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { return requests.entrySet().stream().filter(entry->entry.getValue().equals(value)).findFirst().orElseThrow().getKey(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw unused(); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw unused(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw unused(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { throw unused(); }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { throw unused(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { throw unused(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw unused(); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { return loadMaterial(ref).bytes(); }
    }
}
