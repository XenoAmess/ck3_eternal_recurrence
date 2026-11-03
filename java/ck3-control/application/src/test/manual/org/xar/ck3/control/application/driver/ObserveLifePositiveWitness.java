package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.UInt64;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Machine-specific manual software observe witness; no Game, live Ready, Runtime or speed credit. */
public final class ObserveLifePositiveWitness {
    private static final Path OWNED = Path.of("D:/ck3-state/resume91-m0-native/offline-next-nov04/observe-life-positive-fixture").toAbsolutePath().normalize();
    private static final String MACHINE = "software-observe-life-positive";
    private static final String EPISODE = "software-observe-episode";
    private static final Instant NOW = Instant.parse("2026-11-03T00:00:00Z");
    private static final BigInteger START = BigInteger.valueOf(53144328);
    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software-observe-life","bridge_pid":123,"episode_character_id":73,
         "episode_run_id":"software-observe-episode","last_checkpoint":null,
         "command_history":[{"index":1,"opaque":{"decimal":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"software-observe"},"rollback_war_failures":null}
        """;
    /** Historical software legacy input, not a newly issued DECL query or world action. */
    private static final String LEGACY = """
        {"schema":"xar.ck3.declaration-opportunity-cooldown/v1","actor_character_id":73,
         "episode_run_id":"software-observe-episode","consecutive_no_war_rounds":1,"cooldown_until_date_raw":null,
         "pending_query":{"query_sequence":7,"source_snapshot_id":"start-one","source_native_revision":9,
          "source_date_raw":53144328,"source_bridge_pid":123},"last_closed_query_sequence":6,"last_confirmed_war_id":null}
        """;

    private ObserveLifePositiveWitness() { }

    public static void main(String[] args) throws IOException {
        if (args.length != 1) throw new IllegalArgumentException("one fresh owned D work directory required");
        Path work = Path.of(args[0]).toAbsolutePath().normalize();
        check(work.startsWith(OWNED) && !work.equals(OWNED) && !Files.exists(work, LinkOption.NOFOLLOW_LINKS),
                "fresh exclusive work directory must remain below the owned fixture root");
        check(work.getParent().toRealPath().startsWith(OWNED.toRealPath()), "actual parent must remain owned");
        requireOwnedTemporary("java.io.tmpdir");
        requireOwnedTemporary("jna.tmpdir");
        try (Fixture fixture = new Fixture(work)) {
            fixture.writer.locked(same -> fixture.archive.inSession(same, archive -> {
                try {
                    exercise(fixture, same, archive);
                    return null;
                } catch (IOException failure) {
                    throw new UncheckedIOException(failure);
                }
            }));
        }
        System.out.println("PASS cases=1 life_receipts=2 existing_pending_closed_once=true actual_domain_replay=true authority=false performance=false");
    }

    private static void requireOwnedTemporary(String property) {
        String configured = System.getProperty(property);
        check(configured != null, "explicit " + property + " required before Windows/JNA fixture use");
        Path path = Path.of(configured).toAbsolutePath().normalize();
        check(path.startsWith(Path.of("D:/ck3-state")) && Files.isDirectory(path), "actual owned D " + property + " required");
    }

    private static void exercise(Fixture fixture, ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        var game = GameGeneration.fromJson(DriverJson.toNode(new Obj(Map.of(
                "pid", number(123), "creation_filetime", new Text("9007199254740993")))));
        var source = new G2Source(MACHINE, NOW.toString(), "software-observe-life", fixture.definition);
        Original startOne = original(archive, fixture.loader, game, source, START, 9, 2, "start-one", false, 0);
        Original endOne = original(archive, fixture.loader, game, source, START.add(AdvancePlan.DAY), 10, 3, "end-one", true, 1);
        Original startTwo = original(archive, fixture.loader, game, source, START.add(AdvancePlan.DAY), 11, 4, "start-two", false, 2);
        Original endTwo = original(archive, fixture.loader, game, source, START.add(AdvancePlan.DAY.multiply(BigInteger.TWO)), 12, 5, "end-two", true, 3);

        var configuration = DynamicCapabilities.encodeConfiguration(new DynamicCapabilities.Configuration(
                Optional.of(fixture.stateDir), Optional.empty(), 3, 3, false, false));
        DriverSnapshotFacts.Known input = withAuxiliary(startOne.known, new Obj(Map.of("capability_configuration", configuration)));
        CountingFiles files = new CountingFiles(fixture.files, fixture.saved);
        var initialized = DriverPersistentPlanningState.initializeCooldown(startOne.complete, input, files, archive);
        check(files.observes == 1 && files.reads == 1 && files.verifications == 1, "real existing-file observe/read/verify producer path");
        Obj initialProof = DriverJson.object(archive.loadMaterial(initialized.source()).bytes(), StrictJson.EXPLICIT_MAX_BYTES);
        Obj capturedInput = OpportunityJson.object(initialProof.get("input"), "actual initial input");
        Obj physical = OpportunityJson.object(capturedInput.get("original"), "actual saved physical capture");
        ExactRef savedOriginal = DriverObservationEvidenceReader.reference(physical.get("file"));
        check(savedOriginal.equals(fixture.files.observe(fixture.saved).orElseThrow().reference()), "actual saved file identity/reference retained");
        check(archive.loadMaterial(DriverObservationEvidenceReader.reference(physical.get("archived"))).contentEquals(bytes(LEGACY)),
                "actual producer archives the original saved bytes");

        byte[] hello = NativeWire.packet(bytes("{\"protocol_version\":1,\"type\":\"hello\",\"pid\":123,\"connection_generation\":5,"
                + "\"bridge_version\":\"software-fixture\",\"expected_ck3_sha256\":\"software-only\",\"game_adapter_id\":\"software-fixture\","
                + "\"game_adapter_status\":\"software-fixture\",\"ck3_build_match\":false,\"capabilities\":[]}"));
        byte[] heartbeat = NativeWire.packet(bytes("{\"protocol_version\":1,\"type\":\"heartbeat\",\"sequence\":1}"));
        check(NativeWire.decode(hello) instanceof NativeWire.Hello, "actual HELLO packet role parser");
        check(NativeWire.decode(heartbeat) instanceof NativeWire.Notice notice && notice.kind() == NativeWire.NoticeKind.HEARTBEAT,
                "actual heartbeat packet role parser");
        ExactRef helloRef = fixture.archive.preserveArtifact(same, hello, 65536);
        ExactRef heartbeatRef = fixture.archive.preserveArtifact(same, heartbeat, 65536);
        ExactRef capabilities = archive.preserveMaterial(new RawJson(bytes("{\"schema\":\"software.archived-capabilities/v1\",\"runtime_permission\":false}")));
        GuardEvidence guardOne = guard(startOne, same.head(), archive, helloRef, heartbeatRef, capabilities);
        GuardEvidence guardTwo = guard(startTwo, same.head(), archive, helloRef, heartbeatRef, capabilities);
        ActionReceipt first = preserveSoftwareLife("software-life-one", 1, startOne, endOne, guardOne, archive);
        ActionReceipt second = preserveSoftwareLife("software-life-two", 2, startTwo, endTwo, guardTwo, archive);
        ExactRef firstRef = archive.receiptReferenceOf(first), secondRef = archive.receiptReferenceOf(second);

        List<String> callbacks = new ArrayList<>();
        LifeAdvanceEvidence.BoundFrameVerifier productionFrames = createBoundFrameVerifier(fixture.loader);
        LifeAdvanceEvidence.BoundFrameVerifier frames = (parent, retained, originals) -> {
            AdvanceObservationPort.Frame rebuilt = productionFrames.rebuild(parent, retained, originals);
            callbacks.add("frame:" + rebuilt.identity().frame().snapshotId());
            return rebuilt;
        };
        NativeRecordedEvidenceVerifier actualVerifier = createVerifier(archive, () -> same, fixture.archive::readArtifact,
                fixture.loader, frames, new OperationKey("life-advance"), fixture.definition, callbacks);
        ActionPorts.RecordedEvidenceVerifier evidence = (head, receipt) -> {
            callbacks.add("evidence.begin:" + receipt.command().actionId());
            actualVerifier.verify(head, receipt);
            callbacks.add("evidence.end:" + receipt.command().actionId());
        };
        DriverSnapshotFacts.Known current = withAuxiliary(endTwo.known, initialized.auxiliary());
        var publication = DriverPersistentPlanningState.observe(endTwo.complete, current, List.of(first, second),
                evidence, same.head(), frames, archive).orElseThrow(() -> new AssertionError("new LIFE processing must publish"));

        equal(List.of("evidence.begin:software-life-one", "domain.begin:software-life-one", "frame:start-one", "frame:end-one",
                "domain.end:software-life-one", "evidence.end:software-life-one", "frame:end-one",
                "evidence.begin:software-life-two", "domain.begin:software-life-two", "frame:start-two", "frame:end-two",
                "domain.end:software-life-two", "evidence.end:software-life-two", "frame:end-two"), callbacks,
                "actual verifier/domain/ending-rebuild order for both newly processed receipts");
        var atCurrent = DeclarationOpportunityCooldown.frame(endTwo.complete);
        var state = DeclarationOpportunityCooldown.decode(OpportunityJson.toNode(publication.auxiliary().get(DriverPersistentPlanningState.COOLDOWN_STATE)), atCurrent);
        var view = DeclarationOpportunityCooldown.decodeView(OpportunityJson.toNode(publication.auxiliary().get(DeclarationOpportunityCooldown.VIEW_KEY)), atCurrent);
        check(state.consecutiveNoWarRounds() == 2 && state.pendingQuery().isEmpty(), "one existing pending closes the second saved streak round");
        equal(Optional.of(new UInt64(BigInteger.valueOf(7))), state.lastClosedQuerySequence(), "the saved pending closes once");
        equal(Optional.of(START.add(AdvancePlan.DAY).add(DeclarationOpportunityCooldown.COOLDOWN_RAW_DAYS)),
                state.cooldownUntilDateRaw(), "second LIFE without new DECL retains the first close deadline");
        check(view.active() && view.remainingDays().equals(BigInteger.valueOf(29)), "final197 view uses actual current +48 date");
        Obj finalProof = DriverJson.object(archive.loadMaterial(publication.source()).bytes(), StrictJson.EXPLICIT_MAX_BYTES);
        equal(new Text("LIFE"), finalProof.get("mode"), "final current view needs no extra VIEW proof");
        equal(new Arr(List.of(reference(firstRef), reference(secondRef))), finalProof.get("processed"), "each new receipt retained exactly once");
        Obj firstProof = DriverJson.object(archive.loadMaterial(DriverObservationEvidenceReader.reference(finalProof.get("previous"))).bytes(), StrictJson.EXPLICIT_MAX_BYTES);
        equal(new Text("LIFE"), firstProof.get("mode"), "both actual LIFE proofs are preserved");
        equal(reference(initialized.source()), firstProof.get("previous"), "actual INITIAL source is retained");
    }

    private static ActionReceipt preserveSoftwareLife(String id, long sequence, Original starting, Original ending,
            GuardEvidence originalGuard, ActionPorts.OutcomeArchive archive) {
        var before = advanceFrame(starting.complete);
        var after = advanceFrame(ending.complete);
        var start = before.identity().frame().identity().dateRaw();
        var target = after.identity().frame().identity().dateRaw();
        var plan = new AdvancePlan(start, target, 1, 3, "software_polled", false,
                AdvancePlan.ClockMode.POLLED, Optional.empty(), Optional.empty());
        var expected = new ExpectedPostcondition(1, before.identity(), before.source(), AdvancePlan.OBSERVER, plan.expected());
        var claims = ActionCodec.claims(DriverJson.toNode(new Obj(Map.of("army_ids", new Arr(List.of()),
                "ally_character_ids", new Arr(List.of()), "character_ids", new Arr(List.of()), "commitment_keys", new Arr(List.of())))));
        var command = new ActionCommand(id, before.identity(), before.source(), before.sessionId(), new OperationKey("life-advance"),
                new Obj(Map.of(AdvancePlan.KEY, plan.json())), expected, claims, NOW.plusSeconds(120));
        var diagnostics = new AdvanceClock.Diagnostics(start, target, 1, 1, 3, plan.policy(), AdvanceClock.ProgressStatus.POSTCONDITION,
                Optional.empty(), Optional.empty(), false, List.of(), 0, Optional.empty());
        ExactRef result = archive.preserveMaterial(new AdvanceResult(command, plan, before,
                new AdvanceClock.Outcome(after, diagnostics), List.of()).encode(archive));
        ExactRef basis = LifeAdvanceEvidence.preserve(command, before, after, AdvanceClock.ProgressStatus.POSTCONDITION,
                Optional.empty(), List.of(), Optional.of(result), archive);
        // Finite public input DATA. Full production Life replay independently re-derives this ordered observation.
        List<ExpectedValue> actual = new ArrayList<>(plan.expected());
        actual.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"), true));
        actual.add(new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), true));
        actual.add(new ExpectedText(new FieldKey("progress_status"), "postcondition"));
        actual.add(new ExpectedInteger(new FieldKey("advance.ending_date_raw"), target));
        actual.add(new ExpectedText(new FieldKey("advance.result.sha256"), result.sha256()));
        actual.add(new ExpectedInteger(new FieldKey("advance.result.bytes"), BigInteger.valueOf(result.bytes())));
        actual.add(new ExpectedText(new FieldKey("advance.result.path"), result.path()));
        var effect = new ActionState.EffectObservation(after.identity(), after.source(), after.sessionId(), AdvancePlan.OBSERVER,
                actual, after.provenance(), after.observedAt(), after.originalEvidence(), List.of(basis));
        var execution = new CompositeExecution(LifeAdvanceComposite.HANDLER, before.observedAt(), originalGuard, List.of());
        var receipt = new ActionReceipt(1, sequence, command, ActionCodec.bodySha256(command),
                new ActionState.CompositeSettled(execution, new ActionState.Applied(effect)));
        archive.preserveReceipt(receipt);
        return receipt;
    }

    private static GuardEvidence guard(Original original, Head head, ActionPorts.OutcomeArchive archive,
            ExactRef hello, ExactRef heartbeat, ExactRef capabilities) {
        var complete = original.complete;
        ExactRef semantic = archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(complete.semantic())));
        ExactRef stamp = archive.preserveMaterial(RawJson.fullMaterial(NativeDriverStamp.encode(complete, original.known)));
        var evidence = new SemanticEvidence(complete.identity(), semantic, complete.originalEvidence(), stamp, original.driver, complete.observedAt());
        var operation = new OperationKey("life-advance");
        ExactRef basis = RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(complete, evidence,
                hello, heartbeat, Optional.empty(), capabilities), operation, "software-observe-authority-data", archive, head);
        return new GuardEvidence(complete.identity(), complete.source(), complete.sessionId(), complete.connectionGeneration(), operation,
                complete.originalEvidence(), hello, "software-observe-authority-data", complete.observedAt(), NOW.plusSeconds(120), List.of(basis));
    }

    private record Original(DriverObservationAssembler.Complete complete, DriverSnapshotFacts.Known known, ExactRef driver) { }

    private static Original original(ActionPorts.OutcomeArchive archive, DriverFrameEvidenceLoader loader, GameGeneration game,
            G2Source source, BigInteger date, long nativeRevision, long publicRevision, String snapshot, boolean paused, long seconds) throws IOException {
        var driver = DriverStateSnapshot.decodeComplete(bytes(DRIVER));
        byte[] driverBytes = driver.encode();
        ExactRef driverRef = archive.preserveMaterial(RawJson.fullMaterial(driverBytes));
        var known = DriverFactsRepository.imported(driverRef, driverBytes, 3, 7, game, new Obj(Map.of()));
        String state = "{\"paused\":" + paused + ",\"map_ready\":true,\"speed\":3,\"date_raw\":" + date
                + ",\"played_character\":{\"character_id\":73,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,"
                + "\"one_life_terminal_reason\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{},\"original_metric\":1.00}";
        byte[] packet = NativeWire.packet(bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"" + snapshot
                + "\",\"revision\":" + nativeRevision + ",\"state\":" + state + "}"));
        var received = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game,
                BigInteger.valueOf(5), "software-observe-session"), snapshot, BigInteger.valueOf(nativeRevision), new RawJson(bytes(state)), packet, NOW.plusSeconds(seconds));
        ExactRef nativeRef = archive.preserveNativeFrame(received);
        RawJson manifest = DriverObservationEvidenceReader.encode(known, received, BigInteger.valueOf(publicRevision),
                DriverObservationAssembler.LEGACY_OBSERVATION_VERSION, source, new Obj(Map.of()), driverRef);
        ExactRef manifestRef = archive.preserveMaterial(manifest);
        var facts = DriverObservationEvidenceReader.decode(manifestRef, manifest, RawJson.fullMaterial(driverBytes), received);
        var complete = loader.load(new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef), archive);
        var observed = new DriverSnapshotFacts.Known(known.driver(), known.stamp(), known.originalHistoryBasis(), known.actionRows(),
                known.auxiliary(), known.loop(), Optional.of(facts));
        return new Original(complete, observed, driverRef);
    }

    private static AdvanceObservationPort.Frame advanceFrame(DriverObservationAssembler.Complete complete) {
        var provenance = new ObservationProvenance.Push(complete.identity().frame().snapshotId(),
                complete.identity().frame().identity().nativeRevision(), complete.originalEvidence());
        return new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                provenance, complete.observedAt(), complete.originalEvidence());
    }

    // First HTTP helper method adopted as source; its caller supplies the real final production loader.
    private static LifeAdvanceEvidence.BoundFrameVerifier createBoundFrameVerifier(NativeEffectEvidence.FrameLoader actualLoader) {
        return (ActionCommand parent, LifeAdvanceEvidence.FrameRecord retained, ActionPorts.OutcomeArchive archive) -> {
            NativeEffectEvidence.FrameBasis basis = new NativeEffectEvidence.FrameBasis(retained.nativeFrame(), retained.driverFacts());
            DriverObservationAssembler.Complete complete = actualLoader.load(basis, archive);
            return new AdvanceObservationPort.Frame(complete.identity(), complete.source(), complete.sessionId(), complete.semantic(),
                    retained.provenance(), complete.observedAt(), complete.originalEvidence());
        };
    }

    // Owner corrects the first HTTP factory's missing pre-registration Life-operation rejection and records actual callbacks.
    private static NativeRecordedEvidenceVerifier createVerifier(ActionPorts.OutcomeArchive actualArchive,
            java.util.function.Supplier<ContinuityStorePort.Session> actualBorrowedSession, OriginalEvidencePort actualOriginals,
            NativeEffectEvidence.FrameLoader actualLoader, LifeAdvanceEvidence.BoundFrameVerifier actualLifeFrames,
            OperationKey exactLifeOperation, ExactRef actualDefinitionSource, List<String> callbacks) {
        if (!LifeAdvanceComposite.accepts(exactLifeOperation.value())) throw new IllegalArgumentException("exact Life operation required");
        AdvanceClockArchivedReplay timeline = new AdvanceClockArchivedReplay(actualLoader);
        var binding = new NativeRecordedEvidenceVerifier.Binding(exactLifeOperation, actualDefinitionSource, (head, proposed, archive) -> {
            if (!proposed.command().operation().equals(exactLifeOperation)) throw new IllegalArgumentException("unregistered Life operation");
            callbacks.add("domain.begin:" + proposed.command().actionId());
            LifeAdvanceEvidence.verifyRecorded(proposed, archive, actualLifeFrames, timeline);
            callbacks.add("domain.end:" + proposed.command().actionId());
        });
        return new NativeRecordedEvidenceVerifier(actualArchive, actualBorrowedSession, actualOriginals, actualLoader, List.of(binding));
    }

    private static final class Fixture implements AutoCloseable {
        final Path stateDir, saved;
        final NativeCheckpointFiles files = new NativeCheckpointFiles();
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler());
        final StorageWriteGuardTestSupport storage;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        final ExactRef definition;

        Fixture(Path root) throws IOException {
            Files.createDirectory(root);
            stateDir = Files.createDirectory(root.resolve("legacy-state"));
            saved = stateDir.resolve(DeclarationOpportunityCooldown.LEGACY_FILENAME);
            Files.write(saved, bytes(LEGACY), StandardOpenOption.CREATE_NEW);
            byte[] state = ContinuityJson.canonical(writerState());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software Life source", StandardOpenOption.CREATE_NEW);
            definition = files.observe(root.resolve("source.txt")).orElseThrow().reference();
            Layout layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), files.observe(root.resolve("anchor.json")).orElseThrow().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            try {
                var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
                writer = new ContinuityWriter(layout, List.of(definition), new TransitionAuthority() {
                    @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                    @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new AssertionError("no fixture ledger transition"); }
                }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
                archive = new NativeOutcomeArchive(store, writer);
            } catch (IOException | RuntimeException | Error failure) {
                try { storage.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }
        @Override public void close() throws IOException { storage.close(); }
    }

    /** Only the production adapter probes/reads/verifies; this wrapper records the real producer boundary. */
    private static final class CountingFiles implements CheckpointFiles {
        private final NativeCheckpointFiles actual;
        private final Path expected;
        int observes, reads, verifications;
        CountingFiles(NativeCheckpointFiles actual, Path expected) { this.actual = actual; this.expected = expected; }
        @Override public Optional<FileWitness> observe(Path path) throws IOException {
            equal(expected, path, "actual configured legacy path"); observes++; return actual.observe(path);
        }
        @Override public byte[] read(FileWitness witness, int maximumBytes) throws IOException { reads++; return actual.read(witness, maximumBytes); }
        @Override public void verify(FileWitness witness) throws IOException { verifications++; actual.verify(witness); }
        @Override public FileWitness replace(Path target, byte[] bytes) { throw new AssertionError("initialize must not replace the saved input"); }
        @Override public FileWitness createNew(Path target, byte[] bytes) { throw new AssertionError("initialize must not create a saved input"); }
        @Override public FileWitness copyNew(FileWitness source, Path target) { throw new AssertionError("initialize must not copy a saved input"); }
    }

    private static ObjectNode writerState() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559);
        return row;
    }

    private static DriverSnapshotFacts.Known withAuxiliary(DriverSnapshotFacts.Known original, Obj auxiliary) {
        return new DriverSnapshotFacts.Known(original.driver(), original.stamp(), original.originalHistoryBasis(), original.actionRows(),
                auxiliary, original.loop(), original.observation());
    }
    private static Obj reference(ExactRef ref) { return DriverObservationEvidenceReader.reference(ref); }
    private static IntegerValue number(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static void check(boolean condition, String label) { if (!condition) throw new AssertionError(label); }
    private static void equal(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
    }
}
