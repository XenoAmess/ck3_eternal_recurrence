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
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Two new real public replay DATA cases; no Session, issuer, handmade Complete or world authority. */
public final class PersistentReplayProjectionLaneWitness {
    private static final String MACHINE = "software-projection-lane";
    private static final String SCHEMA = "xar.driver-persistent-planning-source/v2";
    private static final Instant NOW = Instant.parse("2026-11-03T00:00:00Z");
    private static final BigInteger DATE = BigInteger.valueOf(53144328);
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software-projection-lane","bridge_pid":123,
         "episode_character_id":73,"episode_run_id":"software-projection-episode","last_checkpoint":null,
         "command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"software-projection-lane"},"rollback_war_failures":null}
        """;

    private PersistentReplayProjectionLaneWitness() { }

    public static void main(String[] args) {
        if (args.length != 0) throw new IllegalArgumentException("no files or runtime arguments accepted");
        initialThenViewWithUnusedTree();
        profile1SelectedDecimalIsRejected();
        System.out.println("PASS cases=2 public_replay=true initial_view=true profile1_decimal_rejected=true authority=false performance=false");
    }

    private static void initialThenViewWithUnusedTree() {
        DataArchive archive = new DataArchive();
        Original frame = original(archive, false, true);
        var identity = DeclarationOpportunityCooldown.frame(frame.complete);
        var initial = DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.decode(null, identity),
                DriverPersistentPlanningState.cooldownSnapshot(frame.complete.semantic()), identity);
        ExactRef initialRef = archive.preserveMaterial(proof("INITIAL", Nil.INSTANCE, frame, initialInput(), initial));
        var view = DeclarationOpportunityCooldown.view(initial.state(),
                DriverPersistentPlanningState.cooldownSnapshot(frame.complete.semantic()), identity);
        ExactRef viewRef = archive.preserveMaterial(proof("VIEW", reference(initialRef), frame, Nil.INSTANCE, view));
        Obj auxiliary = auxiliary(view, viewRef);
        List<String> expectedTrace = List.of(event("material", viewRef), event("material", initialRef),
                event("material", frame.manifest), event("native", frame.nativePacket), event("material", frame.driver),
                event("material", frame.manifest), event("native", frame.nativePacket), event("material", frame.driver));
        check(frame.complete.semantic().get("unused_projection_tree") instanceof Obj,
                "unused tree reached the actual historical Reader/Assembler semantic result");
        Obj unused = OpportunityJson.object(frame.complete.semantic().get("unused_projection_tree"), "actual unused tree");
        check(OpportunityJson.array(unused.get("rows"), "actual unused rows").size() == 512,
                "all original unused rows survived the actual material join");
        archive.trace.clear();
        DriverPersistentPlanningState.replay(auxiliary, archive);
        equal(expectedTrace, archive.trace, "actual INITIAL then VIEW instrumented archive load order");
    }

    private static void profile1SelectedDecimalIsRejected() {
        DataArchive archive = new DataArchive();
        Original frame = original(archive, true, false);
        List<Value> rows = OpportunityJson.array(frame.complete.semantic().get("active_wars"), "actual profile1 wars");
        check(rows.size() == 1, "actual original decimal war row retained");
        Value warId = OpportunityJson.object(rows.get(0), "actual original war").get("war_id");
        check(warId instanceof DecimalValue decimal && decimal.token().equals("0.0"),
                "historical profile1 retained the exact decimal token before public replay");
        var identity = DeclarationOpportunityCooldown.frame(frame.complete);
        // Legal initial record DATA only. The public replay must reject the selected original row before proof comparison.
        var initial = DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.decode(null, identity),
                DeclarationOpportunityCooldown.Snapshot.empty(), identity);
        ExactRef initialRef = archive.preserveMaterial(proof("INITIAL", Nil.INSTANCE, frame, initialInput(), initial));
        Obj auxiliary = auxiliary(initial, initialRef);
        List<String> expectedTrace = List.of(event("material", initialRef), event("material", frame.manifest),
                event("native", frame.nativePacket), event("material", frame.driver));
        archive.trace.clear();
        try {
            DriverPersistentPlanningState.replay(auxiliary, archive);
            throw new AssertionError("selected war_id0.0 must retain the original Snapshot integer-token rejection");
        } catch (IllegalArgumentException actual) {
            equal("integer token required; bool/float/string forbidden", actual.getMessage(), "actual selected numeric first error");
        }
        equal(expectedTrace, archive.trace, "actual profile1 rebuild completes before Snapshot rejects and proof comparison is not reached");
    }

    private record Original(DriverObservationAssembler.Complete complete, ExactRef manifest, ExactRef nativePacket, ExactRef driver) { }

    private static Original original(DataArchive archive, boolean decimalWarId, boolean unusedTree) {
        var game = GameGeneration.fromJson(DriverJson.toNode(new Obj(Map.of(
                "pid", number(123), "creation_filetime", new Text("9007199254740993")))));
        ExactRef sourceRef = archive.preserveMaterial(new RawJson(bytes("{\"schema\":\"software.projection.source/v1\"}")));
        G2Source source = new G2Source(MACHINE, NOW.toString(), "software-projection-source", sourceRef);
        var driver = DriverStateSnapshot.decodeComplete(bytes(DRIVER));
        byte[] driverBytes = driver.encode();
        ExactRef driverRef = archive.preserveMaterial(RawJson.fullMaterial(driverBytes));
        var stamp = new DriverSnapshotFacts.Stamp(3, 7, game, driver.session().episodeRunId(), DriverJson.sha256(driverBytes));
        var known = new DriverSnapshotFacts.Known(driver, stamp, driverRef, List.of(), new Obj(Map.of()), Optional.empty(), Optional.empty());
        String wars = decimalWarId ? "[{\"war_id\":0.0,\"player_side\":\"attacker\"}]" : "[]";
        String state = "{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":" + DATE
                + ",\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,"
                + "\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"active_wars\":" + wars
                + ",\"player_armies\":[],\"diagnostics\":{}"
                + (unusedTree ? ",\"unused_projection_tree\":" + unusedTree() : "") + "}";
        byte[] envelope = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"software-projection-original\",\"revision\":9,\"state\":" + state + "}");
        byte[] packet = ByteBuffer.allocate(envelope.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game,
                BigInteger.valueOf(5), "software-projection-session"), "software-projection-original", BigInteger.valueOf(9),
                new RawJson(bytes(state)), packet, NOW);
        ExactRef nativeRef = archive.preserveNativeFrame(actual);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO,
                DriverObservationAssembler.LEGACY_OBSERVATION_VERSION, source, new Obj(Map.of()), driverRef);
        ExactRef manifestRef = archive.preserveMaterial(manifest);
        var rebuilt = DriverObservationEvidenceReader.replayOriginals(manifestRef, manifest, RawJson.fullMaterial(driverBytes), packet, nativeRef);
        check(rebuilt instanceof DriverObservationAssembler.Complete, "actual historical original-material join must be Complete");
        return new Original((DriverObservationAssembler.Complete) rebuilt, manifestRef, nativeRef, driverRef);
    }

    /** Fixed software packet DATA, not a projection/guard implementation or performance payload. */
    private static String unusedTree() {
        var body = new StringBuilder("{\"rows\":[");
        for (int index = 0; index < 512; index++) {
            if (index > 0) body.append(',');
            body.append("{\"ordinal\":").append(index).append(",\"numbers\":[1,2,3],\"nested\":{\"text\":\"unused-original\",\"flag\":true}}");
        }
        return body.append("]}").toString();
    }

    private static Obj initialInput() {
        String configured = Path.of("software-projection-lane", DeclarationOpportunityCooldown.LEGACY_FILENAME).toAbsolutePath().normalize().toString();
        return new Obj(Map.of("configured_path", new Text(configured), "observed_at", new Text(NOW.toString()),
                "original", Nil.INSTANCE, "saved", Nil.INSTANCE, "baseline_receipts", new Arr(List.of())));
    }

    private static RawJson proof(String mode, Value previous, Original frame, Value input, DeclarationOpportunityCooldown.Reduction reduction) {
        Obj basis = new Obj(Map.of("manifest", reference(frame.manifest), "native", reference(frame.nativePacket)));
        return new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text(SCHEMA), "mode", new Text(mode),
                "previous", previous, "frame", basis, "input", input,
                "state", typed(DeclarationOpportunityCooldown.encode(reduction.state())),
                "view", typed(DeclarationOpportunityCooldown.encodeView(reduction.view())), "processed", new Arr(List.of())))));
    }

    private static Obj auxiliary(DeclarationOpportunityCooldown.Reduction reduction, ExactRef source) {
        return new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_STATE, typed(DeclarationOpportunityCooldown.encode(reduction.state())),
                DeclarationOpportunityCooldown.VIEW_KEY, typed(DeclarationOpportunityCooldown.encodeView(reduction.view())),
                DriverPersistentPlanningState.COOLDOWN_SOURCE, reference(source)));
    }

    private static Obj typed(JsonNode node) { return OpportunityJson.object(DriverJson.fromNode(node), "actual reducer DATA"); }
    private static Obj reference(ExactRef ref) { return DriverObservationEvidenceReader.reference(ref); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static String event(String role, ExactRef ref) { return role + ":" + ref.path(); }
    private static void check(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    private static void equal(Object expected, Object actual, String message) {
        if (!expected.equals(actual)) throw new AssertionError(message + ": expected=" + expected + ", actual=" + actual);
    }

    /** Actual in-memory software originals; unsupported action/authority paths fail immediately. */
    private static final class DataArchive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef, byte[]> materials = new HashMap<>();
        private final Map<ExactRef, byte[]> packets = new HashMap<>();
        private final List<String> trace = new ArrayList<>();
        private ExactRef put(String role, byte[] input, Map<ExactRef, byte[]> storage) {
            byte[] body = input.clone();
            String sha = DriverJson.sha256(body);
            ExactRef ref = new ExactRef("software/projection-lane/" + role + "/" + sha, body.length, sha);
            byte[] previous = storage.putIfAbsent(ref, body);
            check(previous == null || Arrays.equals(previous, body), "software immutable original conflict");
            return ref;
        }
        private byte[] read(ExactRef ref, Map<ExactRef, byte[]> storage) {
            byte[] body = storage.get(ref);
            check(body != null && ref.bytes() == body.length && ref.sha256().equals(DriverJson.sha256(body)), "exact software original not found");
            return body.clone();
        }
        @Override public ExactRef preserveMaterial(RawJson original) { return put("material", original.bytes(), materials); }
        @Override public RawJson loadMaterial(ExactRef ref) { trace.add(event("material", ref)); return RawJson.fullMaterial(read(ref, materials)); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { return put("native", original.originalPacket(), packets); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { trace.add(event("native", ref)); return read(ref, packets); }
        private AssertionError unexpected(String method) { return new AssertionError("unexpected archive/authority callback " + method); }
        @Override public RawJson loadFullMaterial(ExactRef ref) { throw unexpected("loadFullMaterial"); }
        @Override public ExactRef materialReferenceOf(RawJson original) { throw unexpected("materialReferenceOf"); }
        @Override public ExactRef preserveReceipt(ActionReceipt original) { throw unexpected("preserveReceipt"); }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { throw unexpected("loadReceipt"); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) { throw unexpected("receiptReferenceOf"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { throw unexpected("preserve"); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { throw unexpected("load"); }
        @Override public ExactRef preserveRequest(NativeRequest original) { throw unexpected("preserveRequest"); }
        @Override public NativeRequest loadRequest(ExactRef ref) { throw unexpected("loadRequest"); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { throw unexpected("referenceOf"); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { throw unexpected("requestReferenceOf"); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { throw unexpected("preserveRead"); }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { throw unexpected("loadRead"); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { throw unexpected("readReferenceOf"); }
        @Override public ExactRef preserveRecord(ActionRecord original) { throw unexpected("preserveRecord"); }
        @Override public ActionRecord loadRecord(ExactRef ref) { throw unexpected("loadRecord"); }
        @Override public ExactRef recordReferenceOf(ActionRecord original) { throw unexpected("recordReferenceOf"); }
    }
}
