package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/**
 * Two new public replay DATA cases; source reviewed for Werror/serial, never run here.
 * Real production codecs/Reader/Assembler/reducers; no Session, verifier or runtime authority.
 */
public final class PersistentParsedEndingReplayWitness {
    private static final String MACHINE = "software-persistent-replay";
    private static final String PROOF_SCHEMA = "xar.driver-persistent-planning-source/v2";
    private static final Instant NOW = Instant.parse("2026-11-03T00:00:00Z");
    private static final BigInteger START = BigInteger.valueOf(53144328);
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software-persistent-replay","bridge_pid":123,
         "episode_character_id":73,"episode_run_id":"software-replay-episode","last_checkpoint":null,
         "command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"software-replay"},"rollback_war_failures":null}
        """;

    private PersistentParsedEndingReplayWitness() { }

    public static void main(String[] args) {
        Fixture success = fixture();
        success.archive.trace.clear();
        DriverPersistentPlanningState.replay(success.auxiliary, success.archive);
        equal(success.expectedTrace, success.archive.trace, "R1 complete INITIAL/LIFE callback order");

        Fixture wrong = fixture();
        wrong.archive.faultReference = wrong.endingSemantic;
        wrong.archive.faultBody = new RawJson(bytes("{}"));
        wrong.archive.trace.clear();
        try {
            DriverPersistentPlanningState.replay(wrong.auxiliary, wrong.archive);
            throw new AssertionError("R2 expected production ending byte identity rejection");
        } catch (RuntimeException actual) {
            equal("persistent original bytes/SHA differ", actual.getMessage(), "R2 exact bytes/SHA is first error");
        }
        equal(wrong.expectedTrace.subList(0, wrong.expectedTrace.size() - 3), wrong.archive.trace,
                "R2 stops before ending manifest/native/Driver reconstruction");
        System.out.println("PASS cases=2 public_replay=true actual_material_readers=true authority=false performance=false");
    }

    private record Fixture(DataArchive archive, Obj auxiliary, ExactRef endingSemantic, List<String> expectedTrace) { }
    private record Original(DriverObservationAssembler.Complete complete, ExactRef manifest, ExactRef nativePacket,
            ExactRef driver) { }

    private static Fixture fixture() {
        DataArchive archive = new DataArchive();
        var game = GameGeneration.fromJson(DriverJson.toNode(new Obj(Map.of(
                "pid", number(123), "creation_filetime", new Text("9007199254740993")))));
        ExactRef sourceRef = archive.preserveMaterial(new RawJson(bytes("{\"schema\":\"software.replay.source/v1\"}")));
        G2Source source = new G2Source(MACHINE, NOW.toString(), "software-replay-source", sourceRef);
        Original before = original(archive, game, source, START, 9, 2, "software-before");
        Original after = original(archive, game, source, START.add(AdvancePlan.DAY), 10, 3, "software-after");
        var beforeFrame = advanceFrame(before.complete);
        var afterFrame = advanceFrame(after.complete);
        var plan = new AdvancePlan(START, START.add(AdvancePlan.DAY), 1, 3, "software_polled",
                false, AdvancePlan.ClockMode.POLLED, Optional.empty(), Optional.empty());
        var expected = new ExpectedPostcondition(1, before.complete.identity(), source, AdvancePlan.OBSERVER, plan.expected());
        var claims = ActionCodec.claims(DriverJson.toNode(new Obj(Map.of(
                "army_ids", new Arr(List.of()), "ally_character_ids", new Arr(List.of()),
                "character_ids", new Arr(List.of()), "commitment_keys", new Arr(List.of())))));
        var command = new ActionCommand("software-life-replay", before.complete.identity(), source,
                before.complete.sessionId(), new OperationKey("life-advance"),
                new Obj(Map.of(AdvancePlan.KEY, plan.json())), expected, claims, NOW.plusSeconds(60));
        var diagnostics = new AdvanceClock.Diagnostics(START, START.add(AdvancePlan.DAY), 1, 1, 3,
                plan.policy(), AdvanceClock.ProgressStatus.POSTCONDITION, Optional.empty(), Optional.empty(),
                false, List.of(), 0, Optional.empty());
        RawJson result = new AdvanceResult(command, plan, beforeFrame,
                new AdvanceClock.Outcome(afterFrame, diagnostics), List.of()).encode(archive);
        ExactRef resultRef = archive.preserveMaterial(result);
        List<ExpectedValue> actual = new ArrayList<>(plan.expected());
        actual.add(new ExpectedText(new FieldKey("progress_status"), "postcondition"));
        actual.add(new ExpectedText(new FieldKey("advance.result.path"), resultRef.path()));
        actual.add(new ExpectedText(new FieldKey("advance.result.sha256"), resultRef.sha256()));
        actual.add(new ExpectedInteger(new FieldKey("advance.result.bytes"), BigInteger.valueOf(resultRef.bytes())));
        var effect = new ActionState.EffectObservation(after.complete.identity(), source, after.complete.sessionId(),
                AdvancePlan.OBSERVER, actual, afterFrame.provenance(), after.complete.observedAt(), after.nativePacket);
        var guard = new GuardEvidence(before.complete.identity(), source, before.complete.sessionId(),
                before.complete.connectionGeneration(), command.operation(), before.nativePacket, sourceRef,
                "software-data-only-no-submit-authority", NOW, NOW.plusSeconds(60));
        var execution = new CompositeExecution(LifeAdvanceComposite.HANDLER, NOW, guard, List.of());
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.CompositeSettled(execution, new ActionState.Applied(effect)));
        ExactRef receiptRef = archive.preserveReceipt(receipt);

        var beforeCooldown = DeclarationOpportunityCooldown.frame(before.complete);
        var afterCooldown = DeclarationOpportunityCooldown.frame(after.complete);
        var initialState = DeclarationOpportunityCooldown.decode(null, beforeCooldown);
        var initial = DeclarationOpportunityCooldown.view(initialState,
                DriverPersistentPlanningState.cooldownSnapshot(before.complete.semantic()), beforeCooldown);
        String configured = Path.of("software-persistent-replay", DeclarationOpportunityCooldown.LEGACY_FILENAME)
                .toAbsolutePath().normalize().toString();
        Obj initialInput = new Obj(Map.of("configured_path", new Text(configured), "observed_at", new Text(NOW.toString()),
                "original", Nil.INSTANCE, "saved", Nil.INSTANCE, "baseline_receipts", new Arr(List.of())));
        ExactRef initialProof = archive.preserveMaterial(proof("INITIAL", Nil.INSTANCE, before, initialInput,
                initial, List.of()));

        var completed = AdvanceCompletedRead.read(archive.loadReceipt(receiptRef), archive).orElseThrow();
        var turn = new DeclarationOpportunityCooldown.TurnResult(completed.step().value(),
                AdvanceResult.progressStatus(completed.progressStatus()), completed.paused(),
                Optional.of(completed.startDateRaw()), Optional.of(completed.endDateRaw()));
        var outcome = new DeclarationOpportunityCooldown.Outcome(true, Optional.of(completed.step().value()), Optional.of(turn));
        var rebound = DeclarationOpportunityCooldown.decode(DeclarationOpportunityCooldown.encode(initial.state()), beforeCooldown);
        var life = DeclarationOpportunityCooldown.afterTurn(rebound, beforeCooldown, outcome,
                DriverPersistentPlanningState.cooldownSnapshot(after.complete.semantic()), afterCooldown);
        var finalReduction = DeclarationOpportunityCooldown.view(life.state(),
                DriverPersistentPlanningState.cooldownSnapshot(after.complete.semantic()), afterCooldown);
        ExactRef ending = archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(after.complete.semantic())));
        Obj lifeInput = new Obj(Map.of("receipt", reference(receiptRef), "result", reference(resultRef),
                "ending_semantic", reference(ending)));
        ExactRef lifeProof = archive.preserveMaterial(proof("LIFE", reference(initialProof), after, lifeInput,
                finalReduction, List.of(receiptRef)));
        Obj auxiliary = new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_STATE, typed(DeclarationOpportunityCooldown.encode(finalReduction.state())),
                DeclarationOpportunityCooldown.VIEW_KEY, typed(DeclarationOpportunityCooldown.encodeView(finalReduction.view())),
                DriverPersistentPlanningState.COOLDOWN_SOURCE, reference(lifeProof)));
        List<String> expectedTrace = List.of(event("material", lifeProof), event("material", initialProof),
                event("material", before.manifest), event("native", before.nativePacket), event("material", before.driver),
                event("material", after.manifest), event("native", after.nativePacket), event("material", after.driver),
                event("receipt", receiptRef), event("material", resultRef), event("material-ref", resultRef), event("full", ending),
                event("material", after.manifest), event("native", after.nativePacket), event("material", after.driver));
        return new Fixture(archive, auxiliary, ending, expectedTrace);
    }

    private static Original original(DataArchive archive, GameGeneration game, G2Source source,
            BigInteger date, long nativeRevision, long publicRevision, String snapshot) {
        var driver = DriverStateSnapshot.decodeComplete(bytes(DRIVER));
        byte[] driverBytes = driver.encode();
        ExactRef driverRef = archive.preserveMaterial(RawJson.fullMaterial(driverBytes));
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, game, driver.session().episodeRunId(), DriverJson.sha256(driverBytes));
        var known = new DriverSnapshotFacts.Known(driver, stamp, driverRef, List.of(), new Obj(Map.of()),
                Optional.empty(), Optional.empty());
        String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":" + date
                + ",\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,"
                + "\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":[],"
                + "\"player_armies\":[],\"diagnostics\":{},\"original_metric\":1.00}";
        byte[] envelope = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"" + snapshot
                + "\",\"revision\":" + nativeRevision + ",\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(envelope.length + 4).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(envelope.length).put(envelope).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game,
                BigInteger.valueOf(5), "software-session"), snapshot, BigInteger.valueOf(nativeRevision),
                new RawJson(bytes(state)), packet, NOW);
        ExactRef nativeRef = archive.preserveNativeFrame(actual);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.valueOf(publicRevision),
                DriverObservationAssembler.LEGACY_OBSERVATION_VERSION, source, new Obj(Map.of()), driverRef);
        ExactRef manifestRef = archive.preserveMaterial(manifest);
        var rebuilt = DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest,
                RawJson.fullMaterial(driverBytes), packet, nativeRef);
        check(rebuilt instanceof DriverObservationAssembler.Complete, "actual original material join must be Complete");
        return new Original((DriverObservationAssembler.Complete) rebuilt, manifestRef, nativeRef, driverRef);
    }

    private static AdvanceObservationPort.Frame advanceFrame(DriverObservationAssembler.Complete complete) {
        var push = new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                complete.identity().frame().identity().nativeRevision(), complete.originalEvidence());
        return new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(),
                complete.semantic(), push, complete.observedAt(), complete.originalEvidence());
    }

    private static RawJson proof(String mode, Value previous, Original frame, Value input,
            DeclarationOpportunityCooldown.Reduction reduction, List<ExactRef> processed) {
        Obj basis = new Obj(Map.of("manifest", reference(frame.manifest), "native", reference(frame.nativePacket)));
        return new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text(PROOF_SCHEMA), "mode", new Text(mode),
                "previous", previous, "frame", basis, "input", input,
                "state", typed(DeclarationOpportunityCooldown.encode(reduction.state())),
                "view", typed(DeclarationOpportunityCooldown.encodeView(reduction.view())),
                "processed", new Arr(processed.stream().map(ref -> (Value) reference(ref)).toList())))));
    }

    private static Obj typed(JsonNode value) { return OpportunityJson.object(DriverJson.fromNode(value), "actual reducer DATA"); }
    private static Obj reference(ExactRef ref) { return DriverObservationEvidenceReader.reference(ref); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static String event(String role, ExactRef ref) { return role + ":" + ref.path(); }
    private static void check(boolean condition, String label) { if (!condition) throw new AssertionError(label); }
    private static void equal(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
    }

    /** Exact in-memory software originals only. No canonical/native/writer capability is implemented. */
    private static final class DataArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, byte[]> materials = new HashMap<>();
        private final Map<ExactRef, byte[]> packets = new HashMap<>();
        private final Map<ExactRef, byte[]> receipts = new HashMap<>();
        private final List<String> trace = new ArrayList<>();
        private ExactRef faultReference;
        private RawJson faultBody;

        private ExactRef put(String role, byte[] raw, Map<ExactRef, byte[]> storage) {
            byte[] copy = raw.clone();
            String digest = DriverJson.sha256(copy);
            ExactRef ref = new ExactRef("software/persistent-replay/" + role + "/" + digest, copy.length, digest);
            byte[] previous = storage.putIfAbsent(ref, copy);
            check(previous == null || Arrays.equals(previous, copy), "fixture immutable originals conflict");
            return ref;
        }
        private byte[] read(ExactRef ref, Map<ExactRef, byte[]> storage) {
            byte[] raw = storage.get(ref);
            check(raw != null && ref.bytes() == raw.length && ref.sha256().equals(DriverJson.sha256(raw)),
                    "fixture exact original not found: " + ref.path());
            return raw.clone();
        }
        @Override public ExactRef preserveMaterial(RawJson original) { return put("material", original.bytes(), materials); }
        @Override public RawJson loadMaterial(ExactRef original) {
            trace.add(event("material", original)); return RawJson.fullMaterial(read(original, materials));
        }
        @Override public RawJson loadFullMaterial(ExactRef original) {
            trace.add(event("full", original));
            if (original.equals(faultReference)) return faultBody;
            return RawJson.fullMaterial(read(original, materials));
        }
        @Override public ExactRef materialReferenceOf(RawJson original) {
            byte[] raw = original.bytes();
            ExactRef ref = new ExactRef("software/persistent-replay/material/" + DriverJson.sha256(raw), raw.length, DriverJson.sha256(raw));
            check(Arrays.equals(raw, read(ref, materials)), "actual material reference lookup");
            trace.add(event("material-ref", ref)); return ref;
        }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) {
            return put("native", original.originalPacket(), packets);
        }
        @Override public byte[] loadNativeFrame(ExactRef original) {
            trace.add(event("native", original)); return read(original, packets);
        }
        @Override public ExactRef preserveReceipt(ActionReceipt original) {
            return put("receipt", ActionReceiptCodec.encodeReceipt(original, this), receipts);
        }
        @Override public ActionReceipt loadReceipt(ExactRef original) {
            trace.add(event("receipt", original)); return ActionReceiptCodec.decodeReceipt(read(original, receipts), this);
        }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) {
            byte[] raw = ActionReceiptCodec.encodeReceipt(original, this);
            ExactRef ref = new ExactRef("software/persistent-replay/receipt/" + DriverJson.sha256(raw), raw.length, DriverJson.sha256(raw));
            check(Arrays.equals(raw, read(ref, receipts)), "actual receipt reference lookup"); return ref;
        }
        private AssertionError unexpected(String method) { return new AssertionError("unexpected authority/archive callback " + method); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { throw unexpected("preserve"); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { throw unexpected("load"); }
        @Override public ExactRef preserveRequest(NativeRequest original) { throw unexpected("preserveRequest"); }
        @Override public NativeRequest loadRequest(ExactRef original) { throw unexpected("loadRequest"); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { throw unexpected("referenceOf"); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { throw unexpected("requestReferenceOf"); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { throw unexpected("preserveRead"); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { throw unexpected("loadRead"); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { throw unexpected("readReferenceOf"); }
        @Override public ExactRef preserveRecord(ActionRecord original) { throw unexpected("preserveRecord"); }
        @Override public ActionRecord loadRecord(ExactRef original) { throw unexpected("loadRecord"); }
        @Override public ExactRef recordReferenceOf(ActionRecord original) { throw unexpected("recordReferenceOf"); }
    }
}
