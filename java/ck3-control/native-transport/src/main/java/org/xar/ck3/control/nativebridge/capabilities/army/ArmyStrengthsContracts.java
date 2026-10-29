package org.xar.ck3.control.nativebridge.capabilities.army;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;

/** Actual installed planner read; public and native revisions retain their separate exact domains. */
public final class ArmyStrengthsContracts {
    public record Selection(Snapshot snapshot, Query query, NativeWire.Hello originalHello, Field<ExactRef> privateProfileQualification) {
        public Selection {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(query); Objects.requireNonNull(originalHello); Objects.requireNonNull(privateProfileQualification);
            require(originalHello.capabilities().contains(CAPABILITY) && originalHello.pid() == snapshot.binding().game().pid()
                    && originalHello.connectionGeneration().equals(snapshot.binding().connectionGeneration()), "Army query requires the actual matching hello capability and Game generation");
            if (query.mode() == Mode.PRIVATE_AUTO_SCALAR) {
                require(originalHello.capabilities().contains(ArmyPrivateScalarControl.CAPABILITY), "native private scalar capability is unavailable");
            } else require(privateProfileQualification instanceof Missing<?>, "ordinary profile cannot inherit a private qualification");
            ArmyStrengthsCodec.selectedScope(snapshot, query, originalHello.capabilities().contains(SCOPED_CAPABILITY) && query.requestedArmies() instanceof Present<?>);
        }
        public boolean scopedExport() { return originalHello.capabilities().contains(SCOPED_CAPABILITY) && query.requestedArmies() instanceof Present<?>; }
    }
    private final RootReadContractCatalog.Family<Selection,Read> family;
    private final ArmyStrengthsFamilies.Registry normalizers;
    private final ArmyStrengthsPipeline pipeline;
    private final List<ExactRef> projectionSources;
    private final Optional<ArmyQueryHistoryStore> sidecarStore;
    private final ExactRef historySettingsOriginal;
    public ArmyStrengthsContracts(ExactRef definitionSource, ExactRef decoderSource, ArmyStrengthsFamilies.Registry normalizers,
            ArmyStrengthsPipeline samePipeline, List<ExactRef> actualCompleteProjectionSources,
            Optional<ArmyQueryHistoryStore> identicalConfiguredStore, ExactRef actualHistorySettingsOriginal) {
        this.normalizers = Objects.requireNonNull(normalizers); pipeline = Objects.requireNonNull(samePipeline);
        projectionSources = List.copyOf(actualCompleteProjectionSources);
        sidecarStore = Objects.requireNonNull(identicalConfiguredStore);
        historySettingsOriginal = Objects.requireNonNull(actualHistorySettingsOriginal);
        require(!projectionSources.isEmpty() && projectionSources.size() <= 64
                && projectionSources.stream().distinct().count() == projectionSources.size()
                && projectionSources.contains(definitionSource) && projectionSources.contains(decoderSource)
                && projectionSources.containsAll(normalizers.sourceRefs()) && projectionSources.contains(historySettingsOriginal), "complete actual Army Driver projection sources required");
        family = new RootReadContractCatalog.Family<>("army-strengths-original-producer-v1", Selection.class,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(CAPABILITY), definitionSource, decoderSource,
                ArmyStrengthsContracts::key, selected -> new OperationKey(STEP), selected -> {
                    if (selected.query().mode() == Mode.EXPLICIT_RICH) normalizers.requireCompleteRich();
                    Function<PlanningReadReceipt,Read> pureDecode = receipt -> {
                        verify(receipt.request(), selected);
                        return ArmyStrengthsCodec.decode(selected.snapshot(), selected.query(), selected.scopedExport(), receipt, normalizers);
                    };
                    return new ReadContract<>("army-strengths-" + digest(key(selected).bytes()), new OperationKey(STEP), Optional.of(CAPABILITY),
                            "original-army-strengths", ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP,
                            ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource,
                            (request, requestId) -> { verify(request, selected); return nativeRequest(selected); }, pureDecode, pureDecode)
                            .withOriginalHistoryProjection((receipt, replayed) -> {
                                verify(receipt.request(), selected);
                                java.util.ArrayList<ExactRef> closure = new java.util.ArrayList<>(projectionSources);
                                if (selected.privateProfileQualification() instanceof Present<ExactRef> qualification
                                        && !closure.contains(qualification.value())) closure.add(qualification.value());
                                var value = ArmyStrengthsDriverResult.project(selected, replayed, pipeline);
                                if (sidecarStore.isPresent()) return ArmyStrengthsDriverResult.historySummary(value,
                                        sidecarStore.orElseThrow(), historySettingsOriginal, List.copyOf(closure));
                                RawJson complete = ArmyStrengthsDriverResult.encode(value);
                                var publicNumbers = DriverReadHistoryRichMaterial.PublicNumbers.fromResults(complete,
                                        ArmyStrengthsDriverResult.encodeHistoryPublic(value));
                                return new DriverReadHistoryRichMaterial.Projection(DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS,
                                        complete, publicNumbers, List.copyOf(closure));
                            });
                });
    }
    public Optional<ArmyQueryHistoryStore> sidecarStore() { return sidecarStore; }
    public ExactRef historySettingsOriginal() { return historySettingsOriginal; }
    public List<RootReadContractCatalog.Family<?,?>> families() { return List.of(family); }
    public ReadContract<Read> issue(RootReadContractCatalog installed, Selection selection) { return Objects.requireNonNull(installed).issue(family, selection); }
    public PlanningReadRequest request(Selection selection) {
        Context context = selection.snapshot().context();
        return new PlanningReadRequest(context.before(), context.source(), context.sessionId(), new OperationKey(STEP),
                OpportunityJson.object(OpportunityJson.parse(arguments(selection).bytes()), "Army strength arguments"), context.deadline());
    }
    public ArmyStrengthsFamilies.Coverage normalizationCoverage() { return normalizers.coverage(); }
    public void requireCompleteRich() { normalizers.requireCompleteRich(); }
    public void requirePipeline(ArmyStrengthsPipeline actual) {
        require(pipeline == actual, "Army live and original-history projection require the identical installed pipeline");
    }
    private static NativeRequest nativeRequest(Selection selection) {
        Query query = selection.query(); var fields = empty().put("army_strengths_profile", query.mode() == Mode.PRIVATE_AUTO_SCALAR ? "private_auto_scalar_v1" : query.profile().wire());
        if (selection.scopedExport() && query.requestedArmies() instanceof Present<List<PublicUnitId>> p) {
            var ids = fields.putArray("army_ids"); p.value().forEach(id -> ids.add(id.value()));
        }
        return new NativeRequest(STEP, Optional.of(CAPABILITY), new RawJson(bytes(fields)));
    }
    private static RawJson arguments(Selection selection) {
        Query query = selection.query(); var fields = empty().put("profile", query.profile().wire()).put("mode", query.mode().name())
                .put("ordered_refill_entry_mode", ArmyStrengthsCodec.wire(query.refillEntryMode())).put("ordered_besieging_entry_mode", ArmyStrengthsCodec.wire(query.besiegingEntryMode()));
        if (query.requestedArmies() instanceof Present<List<PublicUnitId>> p) { var ids = fields.putArray("army_ids"); p.value().forEach(id -> ids.add(id.value())); }
        return new RawJson(bytes(fields));
    }
    private static void verify(PlanningReadRequest request, Selection selection) {
        Context context = selection.snapshot().context();
        require(request.before().equals(context.before()) && request.source().equals(context.source()) && request.sessionId().equals(context.sessionId())
                && request.deadline().equals(context.deadline()) && request.operation().value().equals(STEP)
                && request.arguments().equals(OpportunityJson.object(OpportunityJson.parse(arguments(selection).bytes()), "Army arguments")), "Army query contract crossed its selected actual context");
    }
    private static RawJson key(Selection selection) {
        Snapshot snapshot = selection.snapshot(); Context context = snapshot.context(); Binding binding = snapshot.binding();
        var n = empty().put("snapshot_id", binding.snapshotId()).put("revision", binding.publicRevision().toString()).put("native_revision", binding.nativeRevision().toString())
                .put("date_raw", binding.dateRaw().toString()).put("connection_generation", binding.connectionGeneration().toString()).put("actor", binding.actorCharacterId())
                .put("machine_id", binding.machineId()).put("session_id", binding.sessionId()).put("snapshot_sha256", digest(snapshot.original().bytes()))
                .put("hello_sha256", digest(selection.originalHello().packet().value())).put("deadline", context.deadline().toString())
                .put("observation_version", context.before().observationVersion()).put("source_observed_at_utc", context.source().observedAtUtc()).put("source_exact_build", context.source().exactBuild());
        binding.episodeRunId().ifPresentOrElse(value -> n.put("episode_run_id", value), () -> n.putNull("episode_run_id"));
        n.set("game", binding.game().toJson()); n.set("source_ref", context.source().sourceRef().toJson()); n.set("arguments", parse(arguments(selection).bytes()));
        if (selection.privateProfileQualification() instanceof Present<ExactRef> p) n.set("private_profile_qualification", p.value().toJson());
        return new RawJson(bytes(n));
    }
    private static String digest(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
}
