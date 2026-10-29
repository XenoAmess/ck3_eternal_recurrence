package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual public producer, installed read coordinator, native original result, same-frame readback and cache publication. */
public final class ArmyStrengthsService {
    private static final java.math.BigInteger MAX_PUBLIC_INTEGER = new java.math.BigInteger("9007199254740991");
    public record CurrentFrame(Snapshot snapshot, NativeWire.Hello originalHello) { public CurrentFrame { Objects.requireNonNull(snapshot); Objects.requireNonNull(originalHello); } }
    @FunctionalInterface public interface Current { CurrentFrame current(); }
    public record Reply(ArmyStrengthsContracts.Selection selection, Read original, List<Row> selected,
            Status status, Status scopeStatus, ArmyStrengthsPipeline.Results projections) {
        public Reply {
            Objects.requireNonNull(selection); Objects.requireNonNull(original); selected = List.copyOf(selected); Objects.requireNonNull(status); Objects.requireNonNull(scopeStatus); Objects.requireNonNull(projections);
            require(status == ArmyStrengths.status(selected) && original.original().request().before().equals(selection.snapshot().context().before()), "Army reply does not match its actual source and selected rows");
        }
    }
    private record ReadOutcome(Reply value, ReadContract<Read> contract, PlanningReadResult.Known<Read> original) {
        private ReadOutcome { Objects.requireNonNull(value); Objects.requireNonNull(contract); Objects.requireNonNull(original); }
    }
    private final Current current; private final PlanningReadPort reads; private final RootReadContractCatalog catalog;
    private final ArmyStrengthsContracts contracts; private final ArmyStrengthsCache cache; private final ArmyStrengthsPipeline pipeline;
    private final ArmyPrivateScalarControl scalarControl;
    private final DriverReadHistoryPublisher readHistory;
    public enum HistoryDisposition { QUEUED, STORAGE_DIAGNOSTIC, UNRECORDED }
    /** Actual catch custody only. Neither a decoded error nor a caller-created exception can issue this token. */
    public static final class InvocationFailure {
        private final ArmyStrengthsService owner;
        private final Throwable thrown;
        private final HistoryDisposition disposition;
        private InvocationFailure(ArmyStrengthsService owner,Throwable thrown,HistoryDisposition disposition) {
            this.owner=owner;this.thrown=thrown;this.disposition=disposition;
        }
        public HistoryDisposition disposition(){return disposition;}
    }
    private static final class AutoInvocation {private HistoryDisposition disposition=HistoryDisposition.UNRECORDED;}
    private final ThreadLocal<AutoInvocation> activeAuto=new ThreadLocal<>();
    private final ThreadLocal<InvocationFailure> lastAutoFailure=new ThreadLocal<>();
    public ArmyStrengthsService(Current current, PlanningReadPort reads, RootReadContractCatalog catalog,
            ArmyStrengthsContracts contracts, ArmyStrengthsCache cache, ArmyStrengthsPipeline pipeline,
            ArmyPrivateScalarControl sameScalarControl, DriverReadHistoryPublisher sameReadHistory) {
        this.current = Objects.requireNonNull(current); this.reads = Objects.requireNonNull(reads); this.catalog = Objects.requireNonNull(catalog);
        this.contracts = Objects.requireNonNull(contracts); this.cache = Objects.requireNonNull(cache); this.pipeline = Objects.requireNonNull(pipeline);
        scalarControl = Objects.requireNonNull(sameScalarControl); readHistory = Objects.requireNonNull(sameReadHistory);
        require(scalarControl.current() == current, "Army service requires the identical installed current/gate provider");
        contracts.requirePipeline(pipeline);
    }
    public ArmyPrivateScalarControl scalarControl() { return scalarControl; }
    /** The sole Root catch must retain the identical installed production objects before calling this service. */
    public void requireSame(Current sameCurrent,PlanningReadPort sameReads,RootReadContractCatalog sameCatalog,
            ArmyStrengthsContracts sameContracts,ArmyStrengthsCache sameCache,ArmyStrengthsPipeline samePipeline,
            ArmyPrivateScalarControl sameScalarControl,DriverReadHistoryPublisher sameReadHistory) {
        require(current==sameCurrent&&reads==sameReads&&catalog==sameCatalog&&contracts==sameContracts
                &&cache==sameCache&&pipeline==samePipeline&&scalarControl==sameScalarControl&&readHistory==sameReadHistory,
                "Army query failure scope crossed its actual installed production objects");
    }
    /** Exact thrown-object match and one consumption; creates no row, source authority or Native result. */
    public InvocationFailure takeInvocationFailure(Throwable actualThrowable) {
        InvocationFailure actual=lastAutoFailure.get();
        require(actual!=null&&actual.owner==this&&actual.thrown==actualThrowable,
                "Army query failure has no identical actual service catch custody");
        lastAutoFailure.remove();return actual;
    }
    public Reply query_army_strengths(ArmyCalls.Strengths input) {
        Objects.requireNonNull(input); cache.invalidate(); readHistory.armyCoreRefreshStarted(); CurrentFrame before = Objects.requireNonNull(current.current()); input.revision().requireCurrent(before.snapshot().binding().publicRevision());
        Query query = new Query(Profile.valueOf(input.effectiveProfile().name()), Mode.EXPLICIT_RICH, new Present<>(input.armies()),
                EntryMode.valueOf(input.effectiveRefill().name()), EntryMode.valueOf(input.effectiveBesieging().name()));
        contracts.requireCompleteRich(); pipeline.requireComplete(); return completed(read(before, query, new Missing<>(), true, List.of()));
    }
    /** Ordinary automatic planner projection uses the original core-only validator, not the full public service. */
    public Reply queryAutoCore() {
        return queryAutoCore(Optional.empty());
    }
    /** The original query try-body starts before expected/current acquisition, not at the first Native read. */
    public Reply queryAutoCore(Optional<BigInteger> expectedRevision) {
        require(activeAuto.get()==null,"an Army AUTO query cannot replace its active invocation");
        AutoInvocation invocation=new AutoInvocation();activeAuto.set(invocation);lastAutoFailure.remove();
        var mode = ArmyPrivateScalarControl.Mode.OFF;
        ReadOutcome rich = null, scalar = null;
        try {
            Objects.requireNonNull(expectedRevision);cache.invalidate();readHistory.armyCoreRefreshStarted();
            expectedRevision.ifPresent(value->require(value!=null&&value.signum()>0,"positive expected_revision required"));
            CurrentFrame before = Objects.requireNonNull(current.current());
            expectedRevision.ifPresent(value->require(value.equals(before.snapshot().binding().publicRevision()),"Army query source revision is stale"));
            mode = scalarControl.selectedMode(before);
            var richQuery = new Query(Profile.ORDINARY_CORE_V1, Mode.AUTO_CORE, new Missing<>(),
                    EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED);
            if (mode == ArmyPrivateScalarControl.Mode.OFF) return completed(read(before, richQuery, new Missing<>(), false, List.of()));
            var privateQuery = new Query(Profile.ORDINARY_CORE_V1, Mode.PRIVATE_AUTO_SCALAR, new Missing<>(),
                    EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED);
            if (mode == ArmyPrivateScalarControl.Mode.USE)
                return completed(read(before, privateQuery, toField(scalarControl.qualification(before)), false, List.of()));
            rich = read(before, richQuery, new Missing<>(), false, List.of());
            scalar = read(before, privateQuery, toField(scalarControl.qualification(before)), false, List.of(rich.original()));
            try { scalarControl.markCompared(before, rich.value(), scalar.value()); }
            catch (RuntimeException actualComparisonFailure) {
                // The sole publisher matches its private retained exact Known/contract identities and independently
                // reproduces the installed fixed comparison. No caller Throwable, error JSON or Native-failure token is supplied.
                try { remember(readHistory.enqueuePostKnownFailure(scalar.contract(),scalar.original(),List.of(rich.original()))); }
                catch (RuntimeException publicationFailure) {
                    if(publicationFailure!=actualComparisonFailure)actualComparisonFailure.addSuppressed(publicationFailure);
                }
                throw actualComparisonFailure;
            }
            return completed(rich, List.of(rich, scalar));
        } catch (IOException unavailable) {
            abandon(rich, unavailable); abandon(scalar, unavailable);
            scalarControl.disable(); cache.invalidate();
            var original=new UncheckedIOException("actual private Army qualification is unavailable", unavailable);
            lastAutoFailure.set(new InvocationFailure(this,original,invocation.disposition));throw original;
        } catch (RuntimeException failure) {
            abandon(rich, failure); abandon(scalar, failure);
            if (mode != ArmyPrivateScalarControl.Mode.OFF) scalarControl.disable();
            cache.invalidate();lastAutoFailure.set(new InvocationFailure(this,failure,invocation.disposition));throw failure;
        } finally {activeAuto.remove();}
    }
    public Reply queryQualifiedPrivateAutoScalar(ExactRef actualQualification) { cache.invalidate(); readHistory.armyCoreRefreshStarted(); return completed(read(Objects.requireNonNull(current.current()), new Query(Profile.ORDINARY_CORE_V1, Mode.PRIVATE_AUTO_SCALAR,
            new Missing<>(), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED), new Present<>(actualQualification), false, List.of())); }
    private Reply completed(ReadOutcome actualFinal) { return completed(actualFinal, List.of(actualFinal)); }
    /** Retain the original native components; the sole publisher replays the installed final projector once. */
    private Reply completed(ReadOutcome actualFinal, List<ReadOutcome> actualComponents) {
        try {
            readHistory.enqueueRich(actualFinal.contract(), actualFinal.original(), actualComponents.stream().map(ReadOutcome::original).toList());
            // COMPARE may have left its scalar component in the cache; only the selected final result owns publication.
            var reply=actualFinal.value();var selected=reply.selection();var original=actualFinal.original().value();
            cache.publish(selected.snapshot(),original,selected.scopedExport());
            var cached=cache.forSnapshot(selected.snapshot(),original.profile());
            if(selected.scopedExport())require(cached.isEmpty(),"subset Core cache must remain unavailable");
            else {
                var exact=cached.orElseThrow(()->new IllegalArgumentException("completed full Core cache is unavailable"));
                require(exact.sequence().equals(original.sequence())&&exact.status()==original.status()
                        &&exact.rows().equals(original.rows().stream().map(Row::core).toList()),
                        "completed Core cache differs from its exact final original");
            }
            readHistory.publishCompletedArmyCore(actualFinal.contract(),actualFinal.original());
            return reply;
        } catch (RuntimeException failure) {
            for (ReadOutcome component : actualComponents) abandon(component, failure);
            cache.invalidate(); throw failure;
        }
    }
    /** Query failure grants no successful history row; remove only this owner's still-unfinalized components. */
    private void abandon(ReadOutcome actual, Throwable failure) {
        if (actual == null) return;
        try { readHistory.abandonRich(actual.contract(), actual.original()); }
        catch (RuntimeException cleanup) { if (cleanup != failure) failure.addSuppressed(cleanup); }
    }
    private ReadOutcome read(CurrentFrame actualBefore, Query query, Field<ExactRef> privateQualification, boolean fullService,
            List<? extends PlanningReadResult.Known<?>> actualEarlierComponents) {
        // Invalidate before any refresh failure, including contract construction and no-dispatch failures.
        cache.invalidate();
        var selected = new ArmyStrengthsContracts.Selection(actualBefore.snapshot(), query, actualBefore.originalHello(), privateQualification);
        ReadContract<Read> contract = contracts.issue(catalog, selected);
        var result = reads.read(contract, contracts.request(selected));
        if (!(result instanceof PlanningReadResult.Known<Read> known)) {
            if (!(result instanceof PlanningReadResult.Unavailable<Read> unavailable))
                throw new IllegalStateException("unknown sealed Army read result");
            // Only the actual central unavailable object can match its private consumed-attempt provenance.
            // A/B scalar failure retains only the real earlier rich Known, never an intermediate success row.
            // No original attempt remains an explicit Unrecorded outcome; it is not a fabricated Known/frame.
            remember(readHistory.enqueueFailedRich(contract, unavailable, List.copyOf(actualEarlierComponents)));
            throw DriverReadHistoryFailureMaterial.unavailableException(unavailable);
        }
        try {
            CurrentFrame after = Objects.requireNonNull(current.current());
            require(after.snapshot().binding().equals(selected.snapshot().binding()) && after.snapshot().scope().equals(selected.snapshot().scope())
                    && after.originalHello().connectionGeneration().equals(actualBefore.originalHello().connectionGeneration())
                    && after.originalHello().pid() == actualBefore.originalHello().pid(), "Army query crossed actor, playable state, frame, episode, Game, session or ordered scope");
            Read original = known.value();
            cache.publish(selected.snapshot(), original, selected.scopedExport());
            require(fullService == (query.mode() == Mode.EXPLICIT_RICH), "Army full-service projection policy changed");
            return new ReadOutcome(ArmyStrengthsDriverResult.project(selected, original, pipeline), contract, known);
        } catch (RuntimeException failure) {
            try { readHistory.abandonRich(contract, known); }
            catch (RuntimeException cleanup) { if (cleanup != failure) failure.addSuppressed(cleanup); }
            cache.invalidate(); throw failure;
        }
    }
    private static Field<ExactRef> toField(Optional<ExactRef> optional) {
        return optional.isPresent() ? new Present<>(optional.get()) : new Missing<>();
    }
    private void remember(DriverReadHistoryFailureMaterial.Outcome outcome) {
        AutoInvocation actual=activeAuto.get();if(actual==null)return;
        if(outcome instanceof DriverReadHistoryFailureMaterial.Queued)actual.disposition=HistoryDisposition.QUEUED;
        else if(outcome instanceof DriverReadHistoryFailureMaterial.StorageDiagnostic)actual.disposition=HistoryDisposition.STORAGE_DIAGNOSTIC;
    }
    private void remember(org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Outcome outcome) {
        AutoInvocation actual=activeAuto.get();if(actual==null)return;
        if(outcome instanceof org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Queued)actual.disposition=HistoryDisposition.QUEUED;
        else if(outcome instanceof org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.StorageDiagnostic)actual.disposition=HistoryDisposition.STORAGE_DIAGNOSTIC;
    }
    public PublicBindings.TypedBinding<ArmyCalls.Strengths,Reply> install(PublicBindings bindings, ExactRef actualServiceSource) {
        contracts.requireCompleteRich(); pipeline.requireComplete();
        return bindings.register(PublicMethod.QUERY_ARMY_STRENGTHS, ArmyCalls.Strengths.class, Reply.class, this::query_army_strengths, arguments -> {
            if (!(arguments instanceof PublicBindings.Value value)) throw new IllegalArgumentException("Army strength public arguments require their exact named object");
            return ArmyCalls.Strengths.class.cast(ArmyCallCodec.decode(PublicMethod.QUERY_ARMY_STRENGTHS, value.original()));
        }, ArmyStrengthsService::encodePublicV2, new PublicRoutes.Target(ArmyStrengthsService.class.getName(), "query_army_strengths", actualServiceSource),
                PublicRoutes.Status.IMPLEMENTED, "actual native strengths, complete rich normalizers and all service stages required; runtime acceptance remains separate");
    }
    /** Original internal numeric Driver result; public-v2 output has its own explicit encoder. */
    public static RawJson encodeDriver(Reply reply) { return ArmyStrengthsDriverResult.encode(reply); }
    /** V2 public metadata uses exact decimal strings; original native JSON remains in the archived receipt. */
    public static RawJson encodePublicV2(Reply reply) {
        Binding frame = reply.selection().snapshot().binding(); Read original = reply.original(); Query query = reply.selection().query();
        ObjectNode out = ArmyJson.empty().put("schema", "xar.army-strengths.public/v2").put("schema_version", 2).put("step", STEP).put("accepted", true)
                .put("status", ArmyStrengthsCodec.wire(reply.status())).put("scope_status", ArmyStrengthsCodec.wire(reply.scopeStatus()))
                .put("scope", "player-and-active-war-participants").put("query_sequence", original.sequence().toString()).put("backend_id", original.backendId())
                .put("army_strengths_profile", original.profile().wire()).put("army_observed_phase_coverage", original.profile().coverage())
                .put("queried_snapshot_id", frame.snapshotId()).put("queried_revision", frame.publicRevision().toString()).put("queried_native_revision", frame.nativeRevision().toString())
                .put("queried_date_raw", frame.dateRaw().toString()).put("queried_connection_generation", frame.connectionGeneration().toString())
                .put("ordered_refill_entry_mode", ArmyStrengthsCodec.wire(query.refillEntryMode())).put("ordered_besieging_entry_mode", ArmyStrengthsCodec.wire(query.besiegingEntryMode()));
        frame.episodeRunId().ifPresentOrElse(value -> out.put("queried_episode_run_id", value), () -> out.putNull("queried_episode_run_id"));
        var ids = out.putArray("army_ids"); reply.selected().forEach(row -> ids.add(row.core().army().value()));
        var scopeIds = out.putArray("scope_army_ids"); reply.selection().snapshot().scope().forEach(row -> scopeIds.add(row.army().value()));
        var rows = out.putArray("army_strengths"); reply.selected().forEach(row -> rows.add(reply.projections().rowPublicV2Json(row)));
        out.setAll(reply.projections().topLevelPublicV2Json());
        ObjectNode source = out.putObject("source").put("snapshot_id", frame.snapshotId()).put("revision", frame.publicRevision().toString()).put("native_revision", frame.nativeRevision().toString())
                .put("date_raw", frame.dateRaw().toString()).put("paused", true).put("executable_sha256", reply.selection().originalHello().gameSha256());
        try {
            byte[] hello = reply.selection().originalHello().packet().value(); var raw = NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello, 4, hello.length)));
            JsonNode version = raw.get("expected_ck3_version"); if (version == null) source.putNull("game_version"); else source.put("game_version", ArmyJson.nonempty(version));
        } catch (IOException invalid) { throw new UncheckedIOException("actual original hello cannot be decoded", invalid); }
        ObjectNode snapshot = ArmyJson.parse(reply.selection().snapshot().original().bytes());
        JsonNode backend = snapshot.get("backend_id"); if (backend == null || backend.isNull()) source.putNull("backend_id"); else source.put("backend_id", ArmyJson.nonempty(backend));
        if (original.timing() instanceof NullValue<?>) out.putNull("army_native_timing_v1");
        else if (original.timing() instanceof Present<NativeTiming> p) { NativeTiming n = p.value(); out.putObject("army_native_timing_v1").put("read_total_ns", n.readTotalNs().toString()).put("owner_query_ns", n.ownerQueryNs().toString()).put("baseline_read_ns", n.baselineReadNs().toString()).put("rich_attach_ns", n.richAttachNs().toString()).put("serialize_ns", n.serializeNs().toString()); }
        if (original.publishedScopeStatus() instanceof Present<Status> p) { var scope = out.putObject("army_strengths_query_scope").put("published_scope_status", ArmyStrengthsCodec.wire(p.value())); var selectedIds = scope.putArray("army_ids"); reply.selected().forEach(row -> selectedIds.add(row.core().army().value())); }
        requireSafePublicNumbers(out);
        return new RawJson(ArmyJson.bytes(out));
    }
    /** Refuse an unmigrated wide numeric extension; its exact native original is already retained in the receipt. */
    private static void requireSafePublicNumbers(JsonNode node) {
        if (node.isIntegralNumber()) require(node.bigIntegerValue().abs().compareTo(MAX_PUBLIC_INTEGER) <= 0,
                "public Army numeric field exceeds the exact JavaScript integer domain; its field codec must emit the declared decimal string");
        else if (node.isContainerNode()) node.forEach(ArmyStrengthsService::requireSafePublicNumbers);
    }
}
