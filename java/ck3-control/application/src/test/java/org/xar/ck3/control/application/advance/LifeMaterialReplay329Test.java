package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.reconciliation.LateOutcome.*;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Exercises Life -> Clock -> actual primitive observer/reducer -> Status -> archive consumer.
 * The protocol fixture is offline; this suite grants no actual CK3 or Root installation qualification. */
final class LifeMaterialReplay329Test {
    private static final Instant NOW = Instant.parse("2026-10-23T17:00:00Z");
    private static final BigInteger START = BigInteger.valueOf(53_288_256);
    private static final ExactRef DEFINITION = new ExactRef("fixture/actual-native-definition.json", 1, "b".repeat(64));
    private static final G2Source SOURCE = new G2Source("software-life-replay329", NOW.toString(), "1.20.0.4", DEFINITION);
    private static final Set<OperationKey> STEPS = Set.of(new OperationKey("set-speed-1"), new OperationKey("resume-map"), new OperationKey("pause-map"));
    private static final Set<String> CAPS = Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP);
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    private static RawJson raw(Obj value) { return new RawJson(DriverJson.encode(value)); }
    private static Value reference(ExactRef value) { return org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(org.xar.ck3.control.contracts.StrictJson.canonical(value.toJson())); }
    private static Obj json(String value) { return DriverJson.object(value.getBytes(StandardCharsets.UTF_8), RawJson.MAXIMUM_BYTES); }
    private static Status sentinel(State state) {
        return new Status(state, new CrossJsDecimalUInt64("37"), START.intValueExact(), START.add(AdvancePlan.DAY).intValueExact(), START.intValueExact(),
                0, 1, Mode.TERMINAL_OR_SENTINEL, 0, 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
    }
    private static Obj nativeToken(String step, String status, Status sentinel) {
        var fields = new java.util.LinkedHashMap<String, Value>();
        fields.put("step", new Text(step)); fields.put("accepted", new Bool(true)); fields.put("status", new Text(status));
        fields.put("tactical_daily_sentinel", org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(
                org.xar.ck3.control.contracts.StrictJson.canonical(SentinelObservation.toJson(sentinel))));
        return new Obj(fields);
    }
    private static ObservationIdentity identity(Obj semantic) {
        return new ObservationIdentity(SOURCE.machineId(), new GameGeneration(4242, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(29829), integer(semantic.get("native_revision"), "native_revision"), integer(semantic.get("date_raw"), "date_raw")),
                        text(semantic.get("snapshot_id"), "snapshot_id"), integer(semantic.get("revision"), "revision"), text(semantic.get("episode_run_id"), "episode")), 1);

    }
    @Test void sameQualifiedRecordedResultReusesOneCompleteReplayWithoutAnotherSoftwareDispatch() {
        Fixture fixture = new Fixture(false, false, false, true, true, 1);
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, fixture.life.run(fixture.parent, fixture));
        var receipt = new ActionReceipt(1, 100, fixture.parent, ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeSettled(fixture.execution(), new ActionState.Applied(observed.observation())));
        var loads = new java.util.concurrent.atomic.AtomicInteger();
        LifeAdvanceRootReplay replay = new LifeAdvanceRootReplay((basis, archive) -> {
            loads.incrementAndGet(); return fixture.complete(basis, archive);
        });
        int requests = fixture.requests, observations = fixture.reads;
        List<String> submitted = List.copyOf(fixture.steps);
        replay.verify(fixture.originalHead, receipt, fixture.archive);
        LifeAdvanceEvidence.Recorded expected = replay.readRecorded(receipt, fixture.archive);
        int originalTwoCallLoads = loads.get();
        assertTrue(originalTwoCallLoads > 0);
        loads.set(0);
        var actual = replay.verifyAndReadRecorded(fixture.originalHead, receipt, fixture.archive).orElseThrow();
        int oneReplayLoads = loads.get();
        assertEquals(expected, actual);
        assertTrue(oneReplayLoads > 0);
        assertEquals(originalTwoCallLoads, Math.multiplyExact(oneReplayLoads, 2));
        assertEquals(fixture.parent.before(), actual.starting().identity());
        assertEquals(observed.observation().after(), actual.ending().identity());
        assertTrue(actual.originalCompatible().isPresent());
        replay.verifyAndReadRecorded(fixture.originalHead, receipt, fixture.archive).orElseThrow();
        assertEquals(oneReplayLoads * 2, loads.get(), "a new call must independently replay, never cache across callbacks");
        loads.set(0);
        replay.verify(fixture.originalHead, receipt, fixture.archive);
        assertEquals(oneReplayLoads, loads.get(), "original void verification must not gain a second full replay");
        assertEquals(requests, fixture.requests); assertEquals(observations, fixture.reads);
        assertEquals(submitted, fixture.steps);
    }

    @Test void machineUnknownAndOriginalBasisFailuresPrecedeRecordedDataAndFirstFrameFailurePropagates() {
        Fixture fixture = new Fixture(false, false, false, true, true, 1);
        var observed = assertInstanceOf(ActionPorts.EffectObserved.class, fixture.life.run(fixture.parent, fixture));
        var receipt = new ActionReceipt(1, 100, fixture.parent, ActionCodec.bodySha256(fixture.parent),
                new ActionState.CompositeSettled(fixture.execution(), new ActionState.Applied(observed.observation())));
        var loads = new java.util.concurrent.atomic.AtomicInteger();
        LifeAdvanceRootReplay replay = new LifeAdvanceRootReplay((basis, archive) -> {
            loads.incrementAndGet(); return fixture.complete(basis, archive);
        });
        var foreignJson = fixture.originalHead.state().toJson(); foreignJson.put("machine_id", "foreign-software-writer329");
        var foreign = new WriterContracts.Head(ContinuityState.fromJson(foreignJson, "foreign-software-writer329"),
                List.of(), List.of(), List.of(), false);
        var oldMachine = assertThrows(IllegalArgumentException.class, () -> replay.verify(foreign, receipt, fixture.archive));
        var newMachine = assertThrows(IllegalArgumentException.class, () -> replay.verifyAndReadRecorded(foreign, receipt, fixture.archive));
        assertEquals(oldMachine.getMessage(), newMachine.getMessage()); assertEquals(0, loads.get());
        var unknown = new ActionReceipt(1, 101, fixture.parent, receipt.bodySha256(),
                new ActionState.CompositeUnknown(fixture.execution(), "retained original remains unknown", List.of()));
        var oldUnknown = assertThrows(IllegalArgumentException.class, () -> replay.verify(fixture.originalHead, unknown, fixture.archive));
        var newUnknown = assertThrows(IllegalArgumentException.class, () -> replay.verifyAndReadRecorded(fixture.originalHead, unknown, fixture.archive));
        assertEquals(oldUnknown.getMessage(), newUnknown.getMessage()); assertEquals(0, loads.get());
        ExactRef basisRef = observed.observation().supportingEvidence().getFirst();
        RawJson saved = fixture.archive.loadMaterial(basisRef);
        Obj body = DriverJson.object(saved.bytes(), RawJson.MAXIMUM_BYTES);
        // Adversarial in-memory bytes only; no physical immutable archive qualification is claimed here.
        fixture.archive.materials.put(basisRef, raw(body.with("action_body_sha256", new Text("0".repeat(64)))));
        var oldBasis = assertThrows(IllegalArgumentException.class, () -> replay.verify(fixture.originalHead, receipt, fixture.archive));
        var newBasis = assertThrows(IllegalArgumentException.class, () -> replay.verifyAndReadRecorded(fixture.originalHead, receipt, fixture.archive));
        assertEquals(oldBasis.getMessage(), newBasis.getMessage()); assertEquals(0, loads.get());
        fixture.archive.materials.put(basisRef, saved);
        var marker = new IllegalStateException("first original frame unavailable329");
        LifeAdvanceRootReplay failing = new LifeAdvanceRootReplay((basis, archive) -> {throw marker;});
        assertSame(marker, assertThrows(IllegalStateException.class, () -> failing.verify(fixture.originalHead, receipt, fixture.archive)));
        assertSame(marker, assertThrows(IllegalStateException.class, () -> failing.verifyAndReadRecorded(fixture.originalHead, receipt, fixture.archive)));
    }
    private static final class Fixture implements AdvanceObservationPort, PlanningReadPort, CompositeActionPort.Children {
        final MemoryArchive archive = new MemoryArchive();
        final WriterContracts.Head originalHead = softwareHead();
        final java.util.UUID custodyEpoch = java.util.UUID.randomUUID();
        long observationTicks; long endpointOrder;
        final List<ActionReceipt> children = new ArrayList<>(); final List<String> steps = new ArrayList<>();
        final Map<ExactRef, AdvanceObservationPort.Frame> produced = new HashMap<>();
        final boolean modalAfterArm; final boolean unknownResume; final boolean modalAfterResume; final boolean watchMode; final boolean finishDay;
        boolean armed; boolean canceled; boolean resumed; boolean rosterDriftAfterSpeed; boolean laggingPause;
        int reads; int requests; int entryReads; int actualSpeed; int nativeRevision=1; int postResumeReads;
        final Obj base; final AdvancePlan plan; final ActionCommand parent; final AdvancePrimitives primitives; final LifeAdvanceComposite life;
        private static WriterContracts.Head softwareHead() {
            Obj state = json("""
                    {"schema":"root.ck3.continuity-window/v1","sequence":100,"window_id":1,
                     "start_date_raw":53288256,"target_date_raw":53288280,"target_days":1,
                     "status":"running","last_settled_cycles":0,"last_settled_date_raw":53288256}
                    """).with("machine_id", new Text(SOURCE.machineId()));
            return new WriterContracts.Head(ContinuityState.fromJson(toNode(state), SOURCE.machineId()),
                    List.of(), List.of(), List.of(), false);
        }
        Fixture(boolean modalAfterArm, boolean unknownResume, boolean modalAfterResume) {
            this(modalAfterArm,unknownResume,modalAfterResume,false,false,1);
        }
        Fixture(boolean modalAfterArm, boolean unknownResume, boolean modalAfterResume, boolean watchMode, boolean finishDay, int initialSpeed) {
            this.modalAfterArm = modalAfterArm; this.unknownResume = unknownResume; this.modalAfterResume = modalAfterResume;
            this.watchMode=watchMode; this.finishDay=finishDay; this.actualSpeed=initialSpeed;
            ExactRef manifest = archive.preserveMaterial(raw(json("{\"schema\":\"fixture-original-driver-facts\",\"actual_full_driver\":true}")));
            Obj initial = json("""
                    {"snapshot_id":"native:1","revision":1,"native_revision":1,"date_raw":53288256,
                     "paused":true,"map_ready":true,"speed":1,"episode_run_id":"fixture-episode","episode_character_id":29829,
                     "local_player_id":0,"played_character":{"character_id":29829,"alive":true},
                     "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
                     "diagnostics":{"bridge_pid":4242,"connection_generation":1},"player_armies":[],"active_wars":[],
                     "top_exclusive_modal_choice_hint":{"status":"absent"},"war_objective_assault_supported":true}
                    """).with("java_driver_facts_evidence", reference(manifest));
            if (watchMode) {
                Obj own=watchArmy(11,29829,2510,true), ally=watchArmy(22,40000,2511,false), enemy=watchArmy(33,50000,3011,false);
                Obj hello=new Obj(Map.of("ck3_build_match",new Bool(true),"expected_ck3_version",new Text(ExactCk3Build.CK3_12004.version()),"expected_ck3_sha256",new Text(ExactCk3Build.CK3_12004.executableSha256())));
                initial=initial.with("speed",new IntegerValue(BigInteger.valueOf(initialSpeed))).with("one_life_terminal",new Bool(false))
                        .with("top_exclusive_modal_choice_hint",json("{\"status\":\"absent\",\"owner_verified\":true}"))
                        .with("diagnostics",json("{\"bridge_pid\":4242,\"connection_generation\":1,\"connected\":true}").with("hello",hello))
                        .with("player_armies",new Arr(List.of(own))).with("active_wars",new Arr(List.of(new Obj(Map.of("war_id",new IntegerValue(BigInteger.ONE),
                                "player_relative_war_score",new IntegerValue(BigInteger.ZERO),"allied_armies",new Arr(List.of(own,ally)),"enemy_armies",new Arr(List.of(enemy)))))));
            }
            base=initial;
            ClockStatusRead status = new ClockStatusRead(this, DEFINITION, archive);
            Set<OperationKey> available=watchMode ? Set.of(new OperationKey("life-advance-one-day"),new OperationKey("set-speed-1"),new OperationKey("set-speed-2"),new OperationKey("set-speed-5"),new OperationKey("resume-map"),new OperationKey("pause-map")) : STEPS;
            Set<String> capabilities=watchMode ? new java.util.HashSet<>(CAPS) : CAPS;
            if (watchMode) capabilities.add("game.state.pending-character-interaction");
            AdvanceReadiness.Port readiness = (command, frame) -> watchMode ? AdvanceHistory.verifiedFacts(command,frame,List.of(),available,capabilities,45,true,manifest)
                    : new AdvanceReadiness.Facts(frame.identity(), STEPS, CAPS, false, false, false, 45, manifest);
            AdvanceClock clock = new AdvanceClock(this, status, readiness, CLOCK, 16, Duration.ofSeconds(1), Duration.ofSeconds(2));
            primitives = new AdvancePrimitives(this, status, CLOCK, 16);
            life = new LifeAdvanceComposite(this, readiness, clock, status, new ActionSnapshotReader(new SnapshotJournal(this)), archive, CLOCK,
                    (command, guard, store) -> { entryReads++; return Optional.empty(); });
            if (watchMode) {
                var request=new PlanningRequest(identity(base),SOURCE,"fixture-session",NOW.plusSeconds(30),
                        new PlanningObservation(base,List.of(),available,capabilities,Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
                var original=new ActionCommand("fixture-life",identity(base),SOURCE,"fixture-session",new OperationKey("life-advance-one-day"),new Obj(Map.of()),
                        new ExpectedPostcondition(1,identity(base),SOURCE,"fixture/skeleton",List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                        new Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
                parent=life.prepare(request,original); plan=AdvancePlan.decode(parent);
            } else {
                plan = new AdvancePlan(START, START.add(AdvancePlan.DAY), 1, 1, "fixture_exact_native_clock", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
                parent = new ActionCommand("fixture-life", identity(base), SOURCE, "fixture-session", new OperationKey("life-advance"),
                        new Obj(Map.of(AdvancePlan.KEY, plan.json())), new ExpectedPostcondition(1, identity(base), SOURCE, AdvancePlan.OBSERVER, plan.expected()),
                        new Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
            }
        }
        private static Obj watchArmy(int id,int owner,int province,boolean controllable) {
            return new Obj(Map.of("army_id",new IntegerValue(BigInteger.valueOf(id)),"owner_character_id",new IntegerValue(BigInteger.valueOf(owner)),
                    "current_province_id",new IntegerValue(BigInteger.valueOf(province)),"move_target_province_id",Nil.INSTANCE,"in_combat",new Bool(false),
                    "retreating",new Bool(false),"controllable",new Bool(controllable),"army_state",new Text("regular"),"army_state_code",new IntegerValue(BigInteger.ONE),"route_province_ids",new Arr(List.of())));
        }
        @Override public AdvanceObservationPort.Frame current(ActionCommand command, Instant deadline) {
            reads++;
            Obj semantic = base;
            if (watchMode) {
                if (resumed) postResumeReads++;
                int revision=nativeRevision+(resumed && finishDay ? laggingPause && postResumeReads>=3 ? 2 : 1 : 0);
                semantic=semantic.with("speed",new IntegerValue(BigInteger.valueOf(actualSpeed))).with("native_revision",new IntegerValue(BigInteger.valueOf(revision)))
                        .with("revision",new IntegerValue(BigInteger.valueOf(revision))).with("snapshot_id",new Text("native:"+revision));
                if (resumed && finishDay) semantic=semantic.with("date_raw",new IntegerValue(START.add(AdvancePlan.DAY)));
                if (resumed && finishDay && laggingPause && postResumeReads<3) semantic=semantic.with("paused",new Bool(false));
                if (rosterDriftAfterSpeed && nativeRevision>1) {
                    Obj war=object(array(semantic.get("active_wars"),"wars").getFirst(),"war");
                    Obj enemy=object(array(war.get("enemy_armies"),"enemies").getFirst(),"enemy").with("current_province_id",new IntegerValue(BigInteger.valueOf(3012)));
                    semantic=semantic.with("active_wars",new Arr(List.of(war.with("enemy_armies",new Arr(List.of(enemy))))));
                }
            }
            if (armed && modalAfterArm || resumed && modalAfterResume) semantic = semantic.with("top_exclusive_modal_choice_hint",
                    json("{\"status\":\"present\",\"source\":\"application_main_pump_observed_modal_receiver\",\"owner_verified\":true,\"max_observation_age_ms\":2000,\"opaque_root_id\":\"fixture-modal-1\"}"))
                    .with("revision", new IntegerValue(BigInteger.TWO)).with("snapshot_id", new Text("native:modal"));
            ExactRef packet = archive.preserveMaterial(raw(new Obj(Map.of("semantic", semantic, "actual_read", new Text("semantic-" + reads)))));
            var observed = identity(semantic);
            var provenance = new ObservationProvenance.Push(observed.frame().snapshotId(), observed.frame().identity().nativeRevision(), packet);
            var frame = new AdvanceObservationPort.Frame(observed, SOURCE, "fixture-session", semantic, provenance, nextObservation(), packet);
            produced.put(packet, frame); return frame;
        }
        @Override public AdvanceObservationPort.Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) { return current(command, deadline); }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            String id = "status-query-" + ++requests;
            var frame = current(parent, request.deadline());
            var binding = guard(request.operation(), frame);
            var readGuard = new PlanningReadGuard(binding, true, true, true, "c".repeat(64));
            var exchange = write(id, ClockStatusRead.STEP, frame);
            var ack = ack(exchange, nativeToken(ClockStatusRead.STEP, "available", currentStatus()));
            var receipt = new PlanningReadReceipt(request, contract.contractId(), id, readGuard, readGuard, ack);
            ExactRef originalReceipt = archive.preserveRead(receipt); return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, originalReceipt);
        }
        @Override public String nextActionId() { return "fixture-life.child." + (children.size() + 1); }
        @Override public List<ActionReceipt> completed() { return List.copyOf(children); }
        @Override public ActionReceipt submit(ActionCommand command) {
            steps.add(command.operation().value()); String id = "child-native-" + ++requests;
            var frame = current(parent, command.deadline());
            var attempt = new ActionState.Attempt(id, frame.observedAt(), guard(command.operation(), frame), primitives.prepare(command));
            archive.preserveRequest(attempt.preparedRequest());
            var exchange = write(id, command.operation().value(), frame);
            NativeActionPort.DispatchOutcome dispatch;
            if (command.operation().value().equals("resume-map") && unknownResume)
                dispatch = new NativeActionPort.Unknown(id, "original resume write outcome unknown", exchange.outbound().originalPacket(), Optional.empty());
            else {
                if (command.operation().value().startsWith("set-speed-")) { actualSpeed=Integer.parseInt(command.operation().value().substring(10)); if (watchMode) nativeRevision++; }
                if (command.operation().value().equals(plan.armStep())) armed = true;
                if (command.operation().value().startsWith(ClockStatusRead.CANCEL_PREFIX)) canceled = true;
                if (command.operation().value().equals("resume-map")) resumed = true;
                dispatch = ack(exchange, nativeToken(command.operation().value(), canceled ? "canceled" : "available", currentStatus()));
            }
            ActionPorts.PostconditionResult observed = primitives.observe(command, attempt, dispatch);
            ActionState state;
            if (observed instanceof ActionPorts.Pending pending) state = new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), pending.reason(), pending.evidence());
            else {
                ActionState.Settlement settlement = observed instanceof ActionPorts.ControlObserved value ? value.observation()
                        : new ActionState.Applied(((ActionPorts.EffectObserved) observed).observation());
                try { ActionEffects.validate(command, attempt, dispatch, settlement); state = new ActionState.Settled(attempt, dispatch, settlement); }
                catch (IllegalArgumentException invalid) { state = new ActionState.Unknown(Optional.of(attempt), Optional.of(dispatch), invalid.getMessage(), List.of(frame.originalEvidence())); }
            }
            ActionReceipt receipt = new ActionReceipt(1, children.size() + 1, command, ActionCodec.bodySha256(command), state);
            children.add(receipt); archive.preserveReceipt(receipt); return receipt;
        }
        private Status currentStatus() {
            if (!watchMode) return sentinel(canceled ? State.IDLE : State.ARMED);
            boolean stop=resumed && finishDay; int end=START.add(AdvancePlan.DAY).intValueExact();
            return new Status(canceled ? State.IDLE : stop ? State.TRIGGERED : State.ARMED,new CrossJsDecimalUInt64("37"),START.intValueExact(),end,
                    stop ? end : START.intValueExact(),stop ? end : 0,2,Mode.TERMINAL_OR_SENTINEL,3,0,stop ? 1 : 0,0,stop ? 1 : 0,
                    stop ? List.of("date_deadline") : List.of(),0,stop ? 0 : -1,stop,stop,false,false);
        }
        private record SoftwareExchange(NativeActionPort.OutboundPacket outbound,
                NativeRequestChronology.Event entered, NativeRequestChronology.Event completed) { }
        private Instant nextObservation() { return NOW.plusMillis(++observationTicks); }
        private NativeRequestChronology.Event endpointEvent() {
            return new NativeRequestChronology.Event(BigInteger.valueOf(++endpointOrder), nextObservation());
        }
        private static byte[] packet(RawJson frame) {
            byte[] body = frame.bytes();
            return java.nio.ByteBuffer.allocate(body.length + 4).order(java.nio.ByteOrder.LITTLE_ENDIAN)
                    .putInt(body.length).put(body).array();
        }
        /** Software I/O edge only: record actual local write/receive calls, not times inferred from SEM or ACK meaning. */
        private SoftwareExchange write(String id, String step, AdvanceObservationPort.Frame before) {
            RawJson original = raw(new Obj(Map.of("type", new Text("execute_step"), "protocol_version", new IntegerValue(BigInteger.ONE),
                    "request_id", new Text(id), "step", new Text(step),
                    "expected_revision", new IntegerValue(before.identity().frame().identity().nativeRevision()))));
            var entered = endpointEvent();
            var wire = new java.io.ByteArrayOutputStream(); wire.writeBytes(packet(original));
            var completed = endpointEvent();
            return new SoftwareExchange(new NativeActionPort.OutboundPacket(id, wire.toByteArray()), entered, completed);
        }
        private NativeActionPort.AckReceived ack(SoftwareExchange exchange, Obj token) {
            String id = exchange.outbound().requestId(); RawJson result = raw(token);
            RawJson original = raw(new Obj(Map.of("type", new Text("command_result"), "protocol_version", new IntegerValue(BigInteger.ONE),
                    "request_id", new Text(id), "ok", new Bool(true), "result", token)));
            byte[] received = new java.io.ByteArrayInputStream(packet(original)).readAllBytes();
            var response = endpointEvent();
            var session = new NativeObservationPort.TransportSession(SOURCE.machineId(), parent.before().game(), BigInteger.ONE, "fixture-session");
            var custody = new NativeRequestChronology(session, custodyEpoch, id,
                    NativeRequestChronology.PacketIdentity.of(exchange.outbound().originalPacket()),
                    NativeRequestChronology.PacketIdentity.of(received), exchange.entered(), exchange.completed(), response);
            var ack = new NativeActionPort.AckReceived(id, true, Optional.of(result), original, received,
                    Optional.of(exchange.outbound()), Optional.of(custody));
            custody.verify(ack); archive.preserve(ack); return ack;
        }
        private GuardEvidence guard(OperationKey operation, AdvanceObservationPort.Frame frame) {
            ExactRef semantic = archive.preserveMaterial(raw(frame.semantic()));
            Value driver = frame.semantic().get("java_driver_facts_evidence");
            ExactRef driverRef = ExactRef.fromJson(toNode(driver));
            var assembled = complete(new NativeEffectEvidence.FrameBasis(frame.originalEvidence(), driverRef), archive);
            var originalSemantic = new org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence(
                    frame.identity(), semantic, frame.originalEvidence(), driverRef, driverRef, frame.observedAt());
            var originals = new RootGuardEvidence.PhysicalReadOriginals(assembled, originalSemantic,
                    DEFINITION, DEFINITION, driverRef, driverRef);
            ExactRef originalBasis = RootGuardEvidence.preservePhysicalRead(originals, operation,
                    "fixture-real-primitive-observer", archive, originalHead);
            return new GuardEvidence(frame.identity(), SOURCE, "fixture-session", BigInteger.ONE, operation, frame.originalEvidence(), DEFINITION,
                    "fixture-real-primitive-observer", frame.observedAt(), NOW.plusSeconds(30), List.of(originalBasis));
        }
        CompositeExecution execution() {
            var start = produced.values().stream().filter(value -> value.identity().equals(parent.before())).min(java.util.Comparator.comparing(AdvanceObservationPort.Frame::observedAt)).orElseThrow();
            return new CompositeExecution(life.handlerId(), NOW, guard(parent.operation(), start), children.stream().map(value -> new CompositeExecution.Child(value.command().actionId(), value.bodySha256())).toList());
        }
        AdvanceObservationPort.Frame rebuild(ActionCommand parent, LifeAdvanceEvidence.FrameRecord retained, ActionPorts.OutcomeArchive store) {
            return Optional.ofNullable(produced.get(retained.nativeFrame())).orElseThrow();
        }
        DriverObservationAssembler.Complete complete(NativeEffectEvidence.FrameBasis retained, ActionPorts.OutcomeArchive store) {
            var original = Optional.ofNullable(produced.get(retained.nativeFrame())).orElseThrow();
            assertEquals(reference(retained.driverFacts()), original.semantic().get("java_driver_facts_evidence"));
            return new DriverObservationAssembler.Complete(original.identity(), original.source(), original.sessionId(), BigInteger.ONE,
                    original.semantic(), original.originalEvidence(), original.observedAt(), DriverObservationAssembler.bindingSha256(original.semantic()));
        }
        ActionReceipt withActual(CompositeControlObservation control, List<ExpectedValue> values) {
            var effect = control.semantic(); var changed = new ActionState.EffectObservation(effect.after(), effect.source(), effect.sessionId(), effect.observerSchema(), List.copyOf(values),
                    effect.provenance(), effect.observedAt(), effect.originalEvidence(), effect.supportingEvidence());
            return new ActionReceipt(1, 100, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(), control.supportingReads(), changed))));
        }
        ActionReceipt withBasis(CompositeControlObservation control, ExactRef basis) {
            var effect = control.semantic();
            var changed = new ActionState.EffectObservation(effect.after(), effect.source(), effect.sessionId(), effect.observerSchema(), effect.actual(),
                    effect.provenance(), effect.observedAt(), effect.originalEvidence(), List.of(basis));
            return new ActionReceipt(1, 100, parent, ActionCodec.bodySha256(parent), new ActionState.CompositeSettled(execution(),
                    new ActionState.CompositeControlApplied(new CompositeControlObservation(control.terminalStatus(), control.supportingReads(), changed))));
        }
    }
    private static final class SnapshotJournal implements ActionJournal {
        private final Fixture fixture;
        SnapshotJournal(Fixture fixture) { this.fixture = fixture; }
        @Override public <T> T locked(Function<LockedJournal,T> work) {
            return work.apply(new LockedJournal() {
                @Override public Optional<ActionReceipt> find(String actionId) {
                    if (fixture.parent != null && actionId.equals(fixture.parent.actionId())) return Optional.of(new ActionReceipt(1,100,fixture.parent,ActionCodec.bodySha256(fixture.parent),new ActionState.CompositeRunning(fixture.execution())));
                    return fixture.children.stream().filter(value -> value.command().actionId().equals(actionId)).findFirst();
                }
                @Override public ActionJournal.Snapshot snapshot() { return new ActionJournal.Snapshot(100,fixture.originalHead.digest(),List.copyOf(fixture.children),new ActionJournal.MissingHistoryBasis()); }
                @Override public List<ActionReceipt> unresolved() { return fixture.children.stream().filter(value -> !value.settled()).toList(); }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) { throw new IllegalStateException("reconciliation fixture cannot mutate the journal"); }
            });
        }
        @Override public <T> T locked(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session session, Function<LockedJournal,T> work) { throw new IllegalStateException("unexpected borrowed journal call"); }
    }
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,RawJson> materials = new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes = new HashMap<>();
        private final Map<NativeActionPort.DispatchOutcome,ExactRef> outcomeRefs = new HashMap<>();
        private final Map<ExactRef,PlanningReadReceipt> reads = new HashMap<>();
        private final Map<PlanningReadReceipt,ExactRef> readRefs = new HashMap<>();
        private final Map<ExactRef,ActionReceipt> receipts = new HashMap<>();
        private final Map<ActionReceipt,ExactRef> receiptRefs = new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests = new HashMap<>();
        private final Map<NativeRequest,ExactRef> requestRefs = new HashMap<>();
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("native_request_id", new Text(value.requestId()))))); outcomes.put(ref, value); outcomeRefs.put(value, ref); return ref;
        }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { return Optional.ofNullable(outcomes.get(ref)).orElseThrow(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return Optional.ofNullable(outcomeRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) {
            preserve(value.original()); ExactRef ref = preserveMaterial(raw(new Obj(Map.of("read_request_id", new Text(value.requestId()))))); reads.put(ref, value); readRefs.put(value, ref); return ref;
        }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { return Optional.ofNullable(reads.get(ref)).orElseThrow(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return Optional.ofNullable(readRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("action_id", new Text(value.command().actionId()), "sequence", new IntegerValue(BigInteger.valueOf(value.sequence())), "body", new Text(value.bodySha256())))));
            receipts.put(ref, value); receiptRefs.put(value, ref); return ref;
        }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return Optional.ofNullable(receipts.get(ref)).orElseThrow(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return Optional.ofNullable(receiptRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) {
            ExactRef ref = new ExactRef("D:/software-fixtures/life-advance/archive/" + DriverJson.sha256(value.bytes()) + ".json", value.bytes().length, DriverJson.sha256(value.bytes())); materials.put(ref, value); return ref;
        }
        @Override public RawJson loadMaterial(ExactRef ref) { return Optional.ofNullable(materials.get(ref)).orElseThrow(); }
        @Override public RawJson loadFullMaterial(ExactRef ref) {
            byte[] original = loadMaterial(ref).bytes();
            assertEquals(ref.bytes(), original.length); assertEquals(ref.sha256(), ActionCodec.sha256(original));
            return RawJson.fullMaterial(original);
        }
        @Override public ExactRef materialReferenceOf(RawJson value) {
            ExactRef ref = new ExactRef("D:/software-fixtures/life-advance/archive/" + DriverJson.sha256(value.bytes()) + ".json", value.bytes().length, DriverJson.sha256(value.bytes()));
            if (!value.equals(materials.get(ref))) throw new IllegalStateException("unarchived original material"); return ref;
        }
        @Override public ExactRef preserveRequest(NativeRequest value) {
            ExactRef ref = preserveMaterial(raw(new Obj(Map.of("step", new Text(value.step()), "capability", value.requiredCapability().<Value>map(Text::new).orElse(Nil.INSTANCE)))));
            requests.put(ref, value); requestRefs.put(value, ref); return ref;
        }
        @Override public NativeRequest loadRequest(ExactRef ref) { return Optional.ofNullable(requests.get(ref)).orElseThrow(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { return Optional.ofNullable(requestRefs.get(value)).orElseThrow(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { throw new IllegalStateException("unused record archive"); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw new IllegalStateException("unused record archive"); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { throw new IllegalStateException("unused record archive"); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { throw new IllegalStateException("offline fixture native frame storage is explicit"); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { return loadMaterial(ref).bytes(); }
    }
}
