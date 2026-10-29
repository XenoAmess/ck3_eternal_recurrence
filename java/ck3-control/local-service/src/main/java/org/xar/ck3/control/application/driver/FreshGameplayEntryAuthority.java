package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ObservedGameplayEntry;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.InitialNoDispatchRecovery;

/** Binds this genuine START-after observation to the original canonical business ledger once. */
public final class FreshGameplayEntryAuthority implements WriterContracts.TransitionAuthority {
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private Capture retained;
    private WriterContracts.Prepared prepared;
    private WriterContracts.Receipt committed;

    private sealed interface EntryOrigin {}
    private record StartAfter(NativeActionPort.AckReceived ack) implements EntryOrigin {
        private StartAfter { Objects.requireNonNull(ack); }
    }
    private record CurrentMap() implements EntryOrigin {}

    private record Capture(ManagedGameSession game, EntryOrigin origin,
            NativeFreshSnapshotPort.Received read, InitialDriverState.Produced produced,
            DriverBootstrap.Adopted driver, DriverSnapshotFacts.Known known, WriterContracts.Request request) { }

    public FreshGameplayEntryAuthority(ContinuityWriter writer, NativeOutcomeArchive archive) {
        this.writer = Objects.requireNonNull(writer);
        this.archive = Objects.requireNonNull(archive);
        StrictJson.require(archive.writer() == writer, "first-map entry requires the identical canonical writer/archive");
    }

    /** Privately issued entry-only recovery. Historical observations are DATA, never the new connection's custody. */
    public static final class RecoveryAdmission {
        private final FreshGameplayEntryAuthority issuer;
        private final ManagedGameSession game;
        private final long sequence;
        private final String digest;
        private final ObservedGameplayEntry.Details entry;
        private final DriverSnapshotFacts.Known facts;
        private final java.util.Optional<InitialNoDispatchRecovery> initialNoDispatch;
        private RecoveryAdmission(FreshGameplayEntryAuthority issuer,ManagedGameSession game,long sequence,String digest,
                ObservedGameplayEntry.Details entry,DriverSnapshotFacts.Known facts,java.util.Optional<InitialNoDispatchRecovery> initialNoDispatch) {
            this.issuer=issuer;this.game=game;this.sequence=sequence;this.digest=digest;this.entry=entry;this.facts=facts;this.initialNoDispatch=Objects.requireNonNull(initialNoDispatch);
        }
        public ObservedGameplayEntry.Details entry(){return entry;}
        public DriverSnapshotFacts.Known facts(){return facts;}
        public java.util.Optional<InitialNoDispatchRecovery> initialNoDispatchRecovery(){return initialNoDispatch;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            issuer.writer.requireSession(same);
            if(initialNoDispatch.isEmpty())same.requireDomainImportContinuation(sequence,digest);
            issuer.requireInitialRecoveryHead(same,game,entry,initialNoDispatch);
            var current=issuer.loadRecoveryFacts(same,entry,initialNoDispatch);
            StrictJson.require(Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(current).bytes(),DriverSnapshotFacts.encodeKnownOriginal(facts).bytes()),
                    "entry recovery originals changed after actual admission");
        }
        ContinuityStorePort.Session activeSession()throws IOException {return issuer.writer.borrowedSession();}
        void requireArchive(org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive actual) {
            StrictJson.require(actual==issuer.archive,"entry recovery must retain its original archive owner");
        }
    }
    /** No new entry, SAVE, Controller state or ordinary credit is fabricated by this read-only admission. */
    public synchronized RecoveryAdmission admitRecovery(ContinuityStorePort.Session same,ManagedGameSession game)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(game);
        var head=same.head();
        var entry=ObservedGameplayEntry.decode(head.state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
        requireInitialRecoveryHead(same,game,entry);
        return new RecoveryAdmission(this,game,head.state().sequence(),head.digest(),entry,loadInitialRecoveryFacts(same,entry),java.util.Optional.empty());
    }
    /** The original journal alone may prove this first interrupted batch had no dispatch. */
    public synchronized RecoveryAdmission admitRecovery(ContinuityStorePort.Session same,ManagedGameSession game,
            InitialNoDispatchRecovery actual)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(game);Objects.requireNonNull(actual);
        var head=same.head();
        var entry=ObservedGameplayEntry.decode(head.state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD));
        var proof=java.util.Optional.of(actual);requireInitialRecoveryHead(same,game,entry,proof);
        return new RecoveryAdmission(this,game,head.state().sequence(),head.digest(),entry,loadRecoveryFacts(same,entry,proof),proof);
    }
    private void requireInitialRecoveryHead(ContinuityStorePort.Session same,ManagedGameSession game,ObservedGameplayEntry.Details entry)throws IOException {
        requireInitialRecoveryHead(same,game,entry,java.util.Optional.empty());
    }
    private void requireInitialRecoveryHead(ContinuityStorePort.Session same,ManagedGameSession game,
            ObservedGameplayEntry.Details entry,java.util.Optional<InitialNoDispatchRecovery> proof)throws IOException {
        writer.requireSession(same);game.verify();
        if(proof.isPresent()) {
            var actual=proof.orElseThrow();actual.requireCurrent(same);var owner=actual.owner();
            StrictJson.require(owner.machineId().equals(game.machineId())&&owner.game().equals(game.generation())
                    &&owner.sessionId().equals(game.sessionId()),"initial interruption proof crossed the actual Game owner");
        }
        var head=same.head().state();var row=head.toJson();
        var captured=proof.flatMap(InitialNoDispatchRecovery::capturedManifest);
        if(captured.isPresent()) {
            var manifest=captured.orElseThrow();var retained=proof.orElseThrow().capturedFacts().orElseThrow();
            StrictJson.require((head.status()==ContinuityState.Status.RUNNING||head.status()==ContinuityState.Status.REPAIR_REQUIRED)
                    &&head.machineId().equals(game.machineId())&&entry.machineId().equals(game.machineId())
                    &&entry.game().equals(game.generation())&&entry.sessionId().equals(game.sessionId())
                    &&entry.game().equals(org.xar.ck3.control.contracts.GameGeneration.fromJson(row.get("game_binding")))
                    &&ContinuityJson.same(entry.toJson(),row.get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                    &&retained.originalHistoryBasis().equals(org.xar.ck3.control.contracts.ExactRef.fromJson(row.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD)))
                    &&manifest.dateRaw()>=head.settledDateRaw(),"captured recovery crossed its retained Game/entry/history/date");
            var binding=StrictJson.object(row.get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision"));
            StrictJson.require(StrictJson.integer(binding.get("date_raw"),0,Integer.MAX_VALUE)>=head.settledDateRaw()
                    &&StrictJson.integer(binding.get("actor_character_id"),java.math.BigInteger.valueOf(Integer.MIN_VALUE),java.math.BigInteger.valueOf(Integer.MAX_VALUE)).equals(retained.driver().session().actorId())
                    &&retained.stamp().episodeRunId().equals(StrictJson.text(binding.get("episode_run_id")))
                    &&StrictJson.integer(binding.get("native_revision"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX).compareTo(entry.nativeRevision())>=0,
                    "captured recovery changed its retained canonical frontier: actor="+binding.get("actor_character_id")+" expected="+retained.driver().session().actorId()
                            +", episode="+binding.get("episode_run_id")+" expected="+retained.stamp().episodeRunId()
                            +", canonical_native="+binding.get("native_revision")+" entry_floor="+entry.nativeRevision()+" captured_read_native="+manifest.nativeRevision());
            return;
        }
        StrictJson.require((head.status()==ContinuityState.Status.RUNNING
                ||proof.isPresent()&&head.status()==ContinuityState.Status.REPAIR_REQUIRED)&&head.settledCycles()==0
                &&head.origin().startDateRaw()==entry.dateRaw()&&head.settledDateRaw()==entry.dateRaw()
                &&entry.machineId().equals(head.machineId())&&entry.machineId().equals(game.machineId())
                &&entry.game().equals(game.generation())&&entry.sessionId().equals(game.sessionId())
                &&entry.game().equals(org.xar.ck3.control.contracts.GameGeneration.fromJson(row.get("game_binding")))
                &&ContinuityJson.same(entry.toJson(),row.get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                &&entry.fullDriver().equals(org.xar.ck3.control.contracts.ExactRef.fromJson(row.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),
                "entry-only recovery must retain the actual unchanged Game/episode/date/history basis");
        for(String field:java.util.List.of(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD,WriterContracts.ORDINARY_CYCLE_FIELD,
                WriterContracts.ORDINARY_CYCLE_REBIND_FIELD,WriterContracts.ORDINARY_SAVED_CYCLE_FIELD,
                WriterContracts.DRIVER_ACTION_HISTORY_FIELD,WriterContracts.DRIVER_READ_HISTORY_FIELD))
            if(proof.isEmpty()||!java.util.List.of(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD,
                    WriterContracts.ORDINARY_CYCLE_FIELD,WriterContracts.ORDINARY_CYCLE_REBIND_FIELD).contains(field))
                StrictJson.require(!row.has(field),"entry-only recovery cannot rewind a later canonical business publication: "+field);
        for(String field:WriterContracts.PRESERVED_RUNTIME_FIELDS)
            if(row.has(field))StrictJson.require(row.get(field).isNull()||row.get(field).isContainerNode()&&row.get(field).isEmpty(),
                    "entry-only recovery cannot discard pending/UNKNOWN/NEXT: "+field);
        StrictJson.require(ContinuityActionJournal.receipts(head,archive.withSession(same)).isEmpty(),
                "entry-only recovery cannot replace canonical action history");
        var binding=StrictJson.object(row.get("latest_binding"),Set.of("date_raw","actor_character_id","episode_run_id","snapshot_id","revision","native_revision"));
        var nativeRevision=StrictJson.integer(binding.get("native_revision"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX);
        StrictJson.require(StrictJson.integer(binding.get("date_raw"),0,Integer.MAX_VALUE)==entry.dateRaw()
                &&StrictJson.integer(binding.get("actor_character_id"),1,StrictJson.MAX_SAFE_INTEGER)==entry.actorId()
                &&entry.episodeId().equals(StrictJson.text(binding.get("episode_run_id")))
                &&(proof.isPresent()?nativeRevision.compareTo(entry.nativeRevision())>=0:entry.nativeRevision().equals(nativeRevision)),
                "entry-only recovery cannot replace a changed canonical actor/date/revision");
    }
    private DriverSnapshotFacts.Known loadRecoveryFacts(ContinuityStorePort.Session same,ObservedGameplayEntry.Details entry,
            java.util.Optional<InitialNoDispatchRecovery> proof)throws IOException {
        if(proof.isPresent()&&proof.orElseThrow().capturedFacts().isPresent()) {
            // Both callers validate the proof in requireInitialRecoveryHead within this held writer scope.
            return proof.orElseThrow().capturedFacts().orElseThrow();
        }
        return loadInitialRecoveryFacts(same,entry);
    }
private DriverSnapshotFacts.Known loadInitialRecoveryFacts(ContinuityStorePort.Session same, ObservedGameplayEntry.Details entry) throws IOException {
    writer.requireSession(same);
    var bound = archive.withSession(same);
    var originalKnown = bound.loadFullMaterial(entry.driverFacts());
    var manifestRef = DriverSnapshotFacts.observationOriginalReference(originalKnown).orElseThrow(() -> new IOException("missing manifest reference"));
    var manifest = bound.loadFullMaterial(manifestRef);
    var full = bound.loadFullMaterial(entry.fullDriver());
    var historicalFrame = DriverObservationEvidenceReader.nativeFrame(manifestRef, manifest, bound.loadNativeFrame(entry.nativeFrame()));
    var oldObservation = DriverObservationEvidenceReader.decode(manifestRef, manifest, full, historicalFrame);
    var known = DriverSnapshotFacts.decodeKnownOriginal(originalKnown, java.util.Optional.of(oldObservation));

    if (!known.originalHistoryBasis().equals(entry.fullDriver())) {
        throw new IOException("history basis mismatch");
    }
    if (!java.util.Arrays.equals(known.driver().encode(), full.bytes())) {
        throw new IOException("full driver bytes mismatch");
    }
    if (!known.stamp().game().equals(entry.game())) {
        throw new IOException("stamp game mismatch");
    }
    if (!known.driver().session().actorId().equals(java.math.BigInteger.valueOf(entry.actorId()))) {
        throw new IOException("driver actor mismatch");
    }
    if (known.driver().session().bridgePid() != entry.game().pid()) {
        throw new IOException("driver bridge pid mismatch");
    }
    if (!known.driver().session().episodeRunId().equals(entry.episodeId())) {
        throw new IOException("driver episode mismatch");
    }
    if (!oldObservation.transport().machineId().equals(entry.machineId())) {
        throw new IOException("transport machine mismatch");
    }
    if (!oldObservation.transport().sessionId().equals(entry.sessionId())) {
        throw new IOException("transport session mismatch");
    }
    if (!oldObservation.transport().game().equals(entry.game())) {
        throw new IOException("transport game mismatch");
    }
    if (!oldObservation.transport().connectionGeneration().equals(entry.connectionGeneration())) {
        throw new IOException("transport connection generation mismatch");
    }

    return known;
}

    /** Retains only the private actual Driver factory's first projection, not a caller-created entry receipt. */
    public synchronized void retain(ManagedGameSession game, NativeActionPort.AckReceived originalStartAck,
            NativeFreshSnapshotPort.Received read, InitialDriverState.Produced produced, DriverBootstrap.Adopted driver) throws IOException {
        StrictJson.require(retained == null, "first-map entry already retains its original observation");
        Objects.requireNonNull(game);
        Objects.requireNonNull(originalStartAck);
        Objects.requireNonNull(read);
        Objects.requireNonNull(produced);
        Objects.requireNonNull(driver);
        var active = writer.activeSession();
        if (active.isPresent()) capture(active.orElseThrow(), game, new StartAfter(originalStartAck), read, produced, driver);
        else writer.locked(same -> { capture(same, game, new StartAfter(originalStartAck), read, produced, driver); return null; });
    }

    /** New public synchronized retainCurrentMap works with private genuine Received+fresh DriverBootstrap.Adopted from this same attachedGame, no original START success claimed. */
    public synchronized void retainCurrentMap(ManagedGameSession game, NativeFreshSnapshotPort.Received read, InitialDriverState.Produced produced, DriverBootstrap.Adopted driver) throws IOException {
        StrictJson.require(retained == null, "first-map entry already retains its original observation");
        Objects.requireNonNull(game);
        Objects.requireNonNull(read);
        Objects.requireNonNull(produced);
        Objects.requireNonNull(driver);
        var active = writer.activeSession();
        if (active.isPresent()) capture(active.orElseThrow(), game, new CurrentMap(), read, produced, driver);
        else writer.locked(same -> { capture(same, game, new CurrentMap(), read, produced, driver); return null; });
    }

    private void capture(ContinuityStorePort.Session same, ManagedGameSession game, EntryOrigin origin,
            NativeFreshSnapshotPort.Received read, InitialDriverState.Produced produced, DriverBootstrap.Adopted driver) throws IOException {
        writer.requireSession(same);
        var known = driver.repository().locked(value -> {
            StrictJson.require(value instanceof DriverSnapshotFacts.Known, "actual first Driver unavailable");
            return (DriverSnapshotFacts.Known) value;
        });
        verifyActual(game, origin, read, produced, driver, known);
        var bound = archive.withSession(same);
        var frame = driver.first().identity().frame();
        var details = new ObservedGameplayEntry.Details(same.head().state().machineId(), read.originalFrame().session().sessionId(),
                frame.episodeRunId(), frame.snapshotId(), read.originalFrame().session().game(), frame.revision().longValueExact(),
                frame.identity().dateRaw().longValueExact(), frame.identity().player().longValueExact(), frame.identity().nativeRevision(),
                read.originalFrame().session().connectionGeneration(),
                origin instanceof StartAfter sa
                        ?new ObservedGameplayEntry.Origin.StartAfter(bound.preserve(sa.ack()))
                        :new ObservedGameplayEntry.Origin.CurrentMap(),
                bound.preserve(read.acknowledgement()),
                bound.preserveNativeFrame(read.originalFrame()), driver.seed().fullDriver(),
                bound.preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(known)));
        if(origin instanceof CurrentMap) {
            ObservedGameplayEntry.reduce(same.head().state(),details.request(),false);
            StrictJson.require(ContinuityActionJournal.receipts(same.head().state(),bound).isEmpty(),"current-map entry cannot absorb prior canonical gameplay actions");
        }
        StrictJson.require(details.machineId().equals(game.machineId()), "first-map writer belongs to another machine");
        retained = new Capture(game, origin, read, produced, driver, known, details.request());
    }

    /** Called after installing this authority in the original router, before ordinary domain initialization. */
    public synchronized WriterContracts.Receipt commitInitial(ContinuityStorePort.Session same) throws IOException {
        writer.requireSession(same);
        StrictJson.require(retained != null, "no genuine initial-map Driver has been retained");
        if (prepared == null) prepared = same.preview(retained.request());
        if (committed == null) {
            var existing = same.queryCommitted(prepared);
            committed = existing.isPresent() ? existing.orElseThrow() : same.commit(prepared);
        }
        same.requireCommitted(prepared, committed);
        return committed;
    }

    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        throw new IOException("actual first-map entry requires the original locked writer Head");
    }

    @Override public synchronized String revalidate(WriterContracts.Head predecessor, WriterContracts.Request request) throws IOException {
        var same = writer.borrowedSession();
        writer.requireSession(same);
        var actual = retained;
        StrictJson.require(actual != null && predecessor.digest().equals(same.head().digest())
                && request.kind().equals(ObservedGameplayEntry.KIND) && Arrays.equals(request.details(), actual.request().details())
                && request.evidence().equals(actual.request().evidence()), "entry differs from this actual retained START-after observation");
        var details = ObservedGameplayEntry.decode(request.detailsObject());
        ObservedGameplayEntry.reduce(predecessor.state(), request, false);
        var bound = archive.withSession(same);
        StrictJson.require(ContinuityActionJournal.receipts(predecessor.state(), bound).isEmpty(), "first-map entry cannot absorb prior canonical gameplay actions");
        actual.driver().repository().locked(value -> {
            StrictJson.require(value instanceof DriverSnapshotFacts.Known, "actual first Driver unavailable");
            try { verifyActual(actual.game(), actual.origin(), actual.read(), actual.produced(), actual.driver(), (DriverSnapshotFacts.Known) value); }
            catch (IOException failure) { throw new java.io.UncheckedIOException(failure); }
            return null;
        });
        if (actual.origin() instanceof StartAfter sa) {
            StrictJson.require(details.origin() instanceof ObservedGameplayEntry.Origin.StartAfter
                    &&sa.ack().equals(bound.load(details.startAck())), "actual START original changed before canonical entry");
        }
        if(actual.origin() instanceof CurrentMap)
            StrictJson.require(details.origin() instanceof ObservedGameplayEntry.Origin.CurrentMap,"current-map entry cannot claim START");
        StrictJson.require(actual.read().acknowledgement().equals(bound.load(details.readAck()))
                && Arrays.equals(actual.read().originalFrame().originalPacket(), bound.loadNativeFrame(details.nativeFrame()))
                && Arrays.equals(actual.produced().driver().encode(), archive.readArtifact(same, details.fullDriver(), Math.min(org.xar.ck3.control.application.checkpoint.DriverCheckpointStore.MAX_DRIVER_BYTES, WriterContracts.MAX_PIN_BYTES)))
                && Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(actual.known()).bytes(), bound.loadFullMaterial(details.driverFacts()).bytes()),
                "actual first-map Driver or native originals changed before canonical entry");
        var digest = StrictJson.object();
        digest.put("head_sha256", predecessor.digest());
        digest.set("entry", details.toJson());
        return ContinuityJson.digest(digest);
    }

    private static void verifyActual(ManagedGameSession game, EntryOrigin origin, NativeFreshSnapshotPort.Received read,
            InitialDriverState.Produced produced, DriverBootstrap.Adopted driver, DriverSnapshotFacts.Known known) throws IOException {
        if (origin instanceof StartAfter sa) {
            NativeFreshSnapshotPort.verifyAfter(sa.ack(), read);
            var outbound = sa.ack().outbound().orElseThrow(() -> new IOException("actual START outbound is absent")).originalPacket();
            var packet = StrictJson.object(StrictJson.parse(Arrays.copyOfRange(outbound, 4, outbound.length), StrictJson.EXPLICIT_MAX_BYTES),
                    Set.of("type", "protocol_version", "request_id", "step", "expected_revision"));
            StrictJson.require("execute_step".equals(StrictJson.text(packet.get("type")))
                    && sa.ack().requestId().equals(StrictJson.text(packet.get("request_id")))
                    && Primitive.START_BOOKMARK.operation().value().equals(StrictJson.text(packet.get("step"))), "initial entry requires the original actual bookmark START request");
            FrontendRulesCodec.nativeAck(sa.ack().originalResultToken().orElseThrow(() -> new IOException("actual START result absent")), Primitive.START_BOOKMARK.operation().value());
        }
        game.verify();
        var session = read.originalFrame().session();
        var first = driver.first();
        var frame = first.identity().frame();
        var raw = DriverObservationAssembler.originalNativeState(read.originalFrame());
        StrictJson.require(org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(raw.get("paused"), "paused")
                && org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(raw.get("map_ready"), "map_ready"), "actual initial paused map required");
        StrictJson.require(driver.status() == DriverBootstrap.AdoptionStatus.FRESH_OBSERVED && driver.session().equals(session)
                && game.generation().equals(session.game()) && game.sessionId().equals(session.sessionId()) && game.machineId().equals(session.machineId())
                && game.nativeTransport().diagnostics().session().filter(session::equals).isPresent()
                && first.identity().game().equals(session.game()) && first.connectionGeneration().equals(session.connectionGeneration())
                && frame.snapshotId().equals(read.originalFrame().snapshotId()) && frame.identity().nativeRevision().equals(read.originalFrame().nativeRevision())
                && produced.driver().session().actorId().equals(frame.identity().player()) && produced.driver().session().episodeRunId().equals(frame.episodeRunId())
                && produced.driver().session().pipeName().equals(game.nativeTransport().pipeName())
                && Arrays.equals(produced.driver().encode(), known.driver().encode()) && produced.auxiliary().equals(known.auxiliary())
                && known.stamp().driverVersion() == 0 && known.stamp().episodeEpoch() == 0 && known.actionRows().isEmpty() && known.driver().commandHistory().isEmpty()
                && known.loop().isEmpty() && known.originalHistoryBasis().equals(driver.seed().fullDriver()), "first-map entry crossed its actual Game, initial Driver, actor or episode");
    }

    @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) {
        return ObservedGameplayEntry.reduce(predecessor, request, false);
    }
}