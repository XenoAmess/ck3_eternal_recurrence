package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.Optional;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatFrames;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsCache;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsDriverResult;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyPrivateScalarControl;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsInstallation;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPipeline;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Concrete complete Strengths definitions, followed by one current-frame provider per actual physical Game. */
public final class RootArmyStrengthsRuntimeFactory {
    private RootArmyStrengthsRuntimeFactory() { }
    public record Sources(ArmyStrengthsInstallation.Sources normalizationAndStages, ExactRef nativeDefinition, ExactRef decoder, ExactRef driverResult, ExactRef richMaterial, ExactRef historyStore, ExactRef historyReference, ExactRef historySettingsCodec) {
        public Sources {
            Objects.requireNonNull(normalizationAndStages); source(nativeDefinition); source(decoder); source(driverResult); source(richMaterial); source(historyStore); source(historyReference); source(historySettingsCodec);
        }
        public List<ExactRef> sourceRefs() {
            List<ExactRef> refs = new ArrayList<>(normalizationAndStages.sourceRefs()); refs.add(nativeDefinition); refs.add(decoder); refs.add(driverResult); refs.add(richMaterial); refs.add(historyStore); refs.add(historyReference); refs.add(historySettingsCodec);
            return List.copyOf(refs);
        }
    }
    public record Configuration(Duration commandReadTimeout) {
        public Configuration {
            Objects.requireNonNull(commandReadTimeout);
            StrictJson.require(!commandReadTimeout.isZero() && !commandReadTimeout.isNegative()
                    && commandReadTimeout.compareTo(Duration.ofMinutes(1)) <= 0, "finite positive Strengths read timeout required");
        }
    }
    public record Installed(ArmyStrengthsContracts contracts, ArmyStrengthsPipeline pipeline, ArmyStrengthsService.Current current,
            RootDomainInstallation installation, ArmyStrengthsCache cache, ArmyPrivateScalarControl scalarControl, Optional<ArmyQueryHistoryStore> sidecarStore) {
        public Installed {
            Objects.requireNonNull(contracts); Objects.requireNonNull(pipeline); Objects.requireNonNull(current); Objects.requireNonNull(installation); Objects.requireNonNull(cache); Objects.requireNonNull(scalarControl); Objects.requireNonNull(sidecarStore);
            StrictJson.require(contracts.sidecarStore().isEmpty()==sidecarStore.isEmpty()
                    && (sidecarStore.isEmpty()||contracts.sidecarStore().orElseThrow()==sidecarStore.orElseThrow()), "Strengths must retain its identical configured history store");
            StrictJson.require(scalarControl.current() == current, "Strengths gate must share its exact actual current provider");
            contracts.requireCompleteRich(); pipeline.requireComplete();
            StrictJson.require(installation.readFamilies().equals(contracts.families()), "Strengths must expose its identical installed read family");
        }
    }
    private record ContextInstallation(ArmyRetreatFrames frames, Installed installed) { }
    public static final class Prepared {
        private final Sources sources;
        private final Configuration configuration;
        private final OriginalDriverQueryHistorySettings.Bound historySettings;
        private final IdentityHashMap<RootRuntimeContext, ContextInstallation> contexts = new IdentityHashMap<>();
        private RootApplicationAssembly.Core owner;
        public Prepared(Sources exactSources, Configuration actualConfiguration, OriginalDriverQueryHistorySettings.Bound actualHistorySettings) {
            sources = Objects.requireNonNull(exactSources); configuration = Objects.requireNonNull(actualConfiguration); historySettings=Objects.requireNonNull(actualHistorySettings);
        }
        public OriginalDriverQueryHistorySettings.Bound queryHistorySettings() { return historySettings; }
        /** Pure construction before adoption; actual observation/source authority is consulted only by Current.current. */
        public synchronized Installed install(RootRuntimeContext context, ArmyRetreatFrames identicalSharedFrames) throws IOException {
            Objects.requireNonNull(context); Objects.requireNonNull(identicalSharedFrames);
            historySettings.requireSame(context.game().launchPlan(),context.clock());
            if (owner == null) owner = context.core();
            StrictJson.require(owner == context.core(), "one original Core owns the prepared Strengths factory");
            ContextInstallation prior = contexts.get(context);
            if (prior != null) {
                StrictJson.require(prior.frames() == identicalSharedFrames, "the same actual runtime cannot replace its shared Army frames");
                return prior.installed();
            }
            Optional<ArmyQueryHistoryStore> store=historyStore(context,historySettings,configuration);
            Definitions definitions = definitions(sources,store,historySettings.original(),historySettings.sourceRefs());
            ArmyStrengthsService.Current current = new ActualCurrent(context, identicalSharedFrames, configuration, historySettings);
            ArmyStrengthsCache cache = new ArmyStrengthsCache();
            ArmyPrivateScalarControl gate = ArmyPrivateScalarControl.ordinary(current, before -> qualify(context, before, configuration));
            Installed installed = new Installed(definitions.contracts(), definitions.pipeline(), current, definitions.installation(), cache, gate, store);
            contexts.put(context, new ContextInstallation(identicalSharedFrames, installed));
            return installed;
        }
    }
    /** Source-only assembly is shared by the real installer and its closure regression; it issues no runtime authority. */
    record Definitions(ArmyStrengthsContracts contracts, ArmyStrengthsPipeline pipeline, RootDomainInstallation installation) { }
    static Definitions definitions(Sources sources, Optional<ArmyQueryHistoryStore> identicalConfiguredStore,
            ExactRef actualHistorySettingsOriginal, List<ExactRef> actualHistorySettingsSources) throws IOException {
        Objects.requireNonNull(identicalConfiguredStore); source(actualHistorySettingsOriginal);
        actualHistorySettingsSources=List.copyOf(actualHistorySettingsSources);
        StrictJson.require(!actualHistorySettingsSources.isEmpty(),"actual history configuration source closure required");
        var closure=new LinkedHashSet<ExactRef>(sources.sourceRefs());
        actualHistorySettingsSources.forEach(ref->{source(ref);closure.add(ref);});closure.add(actualHistorySettingsOriginal);
        List<ExactRef> actualProjectionSources=List.copyOf(closure);
        ArmyStrengthsInstallation.Installed normalization = ArmyStrengthsInstallation.install(sources.normalizationAndStages());
        var contracts = new ArmyStrengthsContracts(sources.nativeDefinition(), sources.decoder(), normalization.families(), normalization.pipeline(), actualProjectionSources, identicalConfiguredStore, actualHistorySettingsOriginal);
        var installation = new RootDomainInstallation("army-strengths", List.of(), List.of(), contracts.families(), List.of(), List.of(), List.of(),
                List.of(), List.of(), List.of(), List.of(), Set.of(), List.of(), List.of(), List.of(), List.of(), List.of());
        contracts.requireCompleteRich(); normalization.pipeline().requireComplete();
        return new Definitions(contracts, normalization.pipeline(), installation);
    }
    private static Optional<ArmyQueryHistoryStore> historyStore(RootRuntimeContext context,
            OriginalDriverQueryHistorySettings.Bound actualSettings, Configuration configuration) throws IOException {
        actualSettings.requireSame(context.game().launchPlan(),context.clock());
        if(actualSettings.effective() instanceof OriginalDriverQueryHistorySettings.NoStateDirectory)return Optional.empty();
        var selected=(OriginalDriverQueryHistorySettings.WithStateDirectory)actualSettings.effective();
        // This is the original Driver-state parent, not the managed evidence directory or a guessed default.
        Path leaf=selected.stateDirectory().resolve("native-session").resolve("army-query-history-results");
        var io=new ArmyQueryHistoryStore.GuardedFileIO(context.core().storageGuard(),context.writer().originalLockPath());
        ArmyQueryHistoryStore.AdmissionGuard admission=()->{
            var same=context.borrowedSession();context.writer().requireSession(same);
            actualSettings.requireSame(context.game().launchPlan(),context.clock());
            context.requireCurrent(context.clock().instant().plus(configuration.commandReadTimeout()));
            context.writer().requireSession(same);
        };
        // Java explicitly selects the Root storage admission. A captured legacy None stays None;
        // the physical write still uses the same mandatory Root StorageWriteGuard and original lock.
        Optional<ArmyQueryHistoryStore.AdmissionGuard> configuredAdmission;
        if(actualSettings.configuration() instanceof OriginalDriverQueryHistorySettings.JavaConfigured) configuredAdmission=Optional.of(admission);
        else {
            var legacy=(OriginalDriverQueryHistorySettings.LegacyCaptured)actualSettings.configuration();
            if(!(legacy.admissionGuard() instanceof OriginalDriverQueryHistorySettings.NullGuard))
                throw new IOException("original legacy admission callable is not bound to an actual Java authority");
            configuredAdmission=Optional.empty();
        }
        return Optional.of(new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(leaf,selected.limitBytes()),configuredAdmission,io));
    }
    private static final class ActualCurrent implements ArmyStrengthsService.Current {
        private final RootRuntimeContext context;
        private final ArmyRetreatFrames frames;
        private final Configuration configuration;
        private final OriginalDriverQueryHistorySettings.Bound historySettings;
        private ActualCurrent(RootRuntimeContext context, ArmyRetreatFrames sameFrames, Configuration configuration, OriginalDriverQueryHistorySettings.Bound sameHistorySettings) {
            this.context = context; frames = sameFrames; this.configuration = configuration; historySettings = sameHistorySettings;
        }
        @Override public ArmyStrengthsService.CurrentFrame current() {
            Instant deadline = context.clock().instant().plus(configuration.commandReadTimeout());
            try {
                historySettings.requireSame(context.game().launchPlan(),context.clock());
                context.requireCurrent(deadline);
                ArmyRetreatFrames.Current current = frames.current(deadline);
                StrictJson.require(current.context().source().equals(context.source()) && current.context().sessionId().equals(context.game().sessionId())
                        && current.context().before().game().equals(context.game().generation())
                        && current.context().before().machineId().equals(context.game().machineId()), "Strengths frame crossed its actual Root Game/source/session");
                var snapshot = ArmyStrengthsCodec.snapshot(current.context(), new RawJson(OpportunityJson.encode(current.actual().semantic())));
                var hello = context.transport().originalHello();
                StrictJson.require(hello.pid() == snapshot.binding().game().pid()
                        && hello.connectionGeneration().equals(snapshot.binding().connectionGeneration()), "Strengths current frame crossed its actual original HELLO");
                context.requireCurrent(deadline);
                historySettings.requireSame(context.game().launchPlan(),context.clock());
                return new ArmyStrengthsService.CurrentFrame(snapshot, hello);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IllegalStateException("actual Strengths current observation interrupted", interrupted);
            } catch (IOException unavailable) { throw new UncheckedIOException("actual Strengths current frame unavailable", unavailable); }
        }
    }
    private static Optional<ExactRef> qualify(RootRuntimeContext context, ArmyStrengthsService.CurrentFrame before, Configuration configuration) throws IOException {
        Instant deadline=context.clock().instant().plus(configuration.commandReadTimeout());context.requireCurrent(deadline);
        var transport=context.transport();var original=transport.latestObservedSnapshot().orElseThrow(()->new IOException("actual private scalar original snapshot absent"));
        var binding=before.snapshot().binding();
        StrictJson.require(original.session().machineId().equals(binding.machineId())&&original.session().game().equals(binding.game())
                &&original.session().sessionId().equals(binding.sessionId())&&original.session().connectionGeneration().equals(binding.connectionGeneration())
                &&original.snapshotId().equals(binding.snapshotId())&&original.nativeRevision().equals(binding.nativeRevision())
                &&transport.originalHello().equals(before.originalHello()),"private scalar qualification crossed its actual original transport/frame");
        var same=context.borrowedSession();context.writer().requireSession(same);
        try { return context.archive().inSession(same,scoped->{ try {
            ExactRef packet=scoped.preserveNativeFrame(original);
            var actual=context.sources().verifyPhysicalOrigin(same,original.session(),context.source(),packet,transport.diagnostics(),deadline);
            actual.assertCurrent(same);context.requireCurrent(deadline);return actual.proof();
            } catch(IOException unavailable) { throw new UncheckedIOException(unavailable); }
        }); } catch(UncheckedIOException unavailable) { throw unavailable.getCause(); }
    }
    private static void source(ExactRef ref) { Objects.requireNonNull(ref); StrictJson.require(ref.bytes() > 0, "actual Strengths source required"); }
}
