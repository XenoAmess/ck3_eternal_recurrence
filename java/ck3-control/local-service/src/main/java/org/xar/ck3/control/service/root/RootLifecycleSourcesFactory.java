package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.driver.DriverPreclockExpectationSource;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.driver.DriverSuccessionReconciliation;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerTerminalQueries;
import org.xar.ck3.control.runtime.lifecycle.NaturalEngineClockProof;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;
import org.xar.ck3.control.service.root.RootRuntimeNativeOriginals.Role;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;

/** Source construction only. Startup retains the sole Core, native plan, loaded closure and admission assembly. */
public final class RootLifecycleSourcesFactory {
    private RootLifecycleSourcesFactory(){ }
    public record Input(RootRuntimeDefinitions.Inputs definitions,PrisonersRuntimeInstaller.Sources samePrisoners,
            CheckpointFiles sameGuardedFiles,RootRuntimeStorageGuard sameGuard,Clock clock) {
        public Input {Objects.requireNonNull(definitions);Objects.requireNonNull(samePrisoners);Objects.requireNonNull(sameGuardedFiles);Objects.requireNonNull(sameGuard);Objects.requireNonNull(clock);}
    }
    private enum JavaLeaf {
        NATURAL(LOCAL_SERVICE,RootNaturalSuccessionOriginals.class),CLOCK_ORIGINALS(LOCAL_SERVICE,NaturalClockOriginals.class),
        TIMELINE(LOCAL_SERVICE,RootNaturalTimeline.class),LIFECYCLE_GUARD(LOCAL_SERVICE,RootLifecycleGuardEvidence.class),
        NATIVE_SOURCE_AUTHORITY(LOCAL_SERVICE,RootNativeSourceAuthority.class),RUNTIME_CONTEXT(LOCAL_SERVICE,RootRuntimeContext.class),
        LIFECYCLE_FACTORY(LOCAL_SERVICE,RootLifecycleRuntimeFactory.class),LIFE_FACTORY(LOCAL_SERVICE,RootLifeRuntimeFactory.class),
        ADVANCE_FACTORY(LOCAL_SERVICE,RootAdvanceInfrastructureFactory.class),TERMINAL_DECISIONS(LOCAL_SERVICE,TerminalLifecycleDecisionProducer.class),
        NATURAL_VERIFIER(LOCAL_SERVICE,RootOriginalNaturalSuccessionVerifier.class),CLOCK_PROOF(LOCAL_SERVICE,NaturalEngineClockProof.class),
        PLAYER_HEIR(CONTRACTS,NativePlayerHeirObservation12004.class),TIMELINE_BLOCKER(G2_RESEARCH,NativeTimelineBlocker12004.class),
        COLLECTION(NATIVE_TRANSPORT,PrisonerNativeQueries.class),TERMINAL_PRISONER(NATIVE_TRANSPORT,PrisonerTerminalQueries.class),
        PRISONER_MATERIAL("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/family/PrisonerMaterial12004.java",Optional.of(PrisonerMaterial12004.class)),
        CAMPAIGN_ROOT(APPLICATION,CampaignRootContextJson.class),RECONCILIATION(LOCAL_SERVICE,DriverSuccessionReconciliation.class),
        LIFECYCLE_ORIGIN(APPLICATION,LifecycleOriginFactory.class),COMPOSITE(APPLICATION,LifecycleComposites.class),PROOF_CODEC(APPLICATION,LifecycleProofCodec.class),
        // These are the separate lifecycle metadata reader/record carriers, selected by the same global source epoch.
        // They do not import or mutate the Natural originals domain; the actual COMPOSITE remains its causal leaf.
        LIFECYCLE_PUBLICATION(APPLICATION,org.xar.ck3.control.application.lifecycle.LifecyclePublication.class,false),
        LIFECYCLE_PENDING_ORIGINALS(APPLICATION,org.xar.ck3.control.application.lifecycle.LifecyclePendingOriginals.class,false),
        PHYSICAL_STATUS_IDENTITY(APPLICATION,org.xar.ck3.control.application.action.PhysicalStatusIdentity.class,false),
        LIFECYCLE_HISTORICAL_PUBLICATION(APPLICATION,org.xar.ck3.control.application.lifecycle.LifecycleHistoricalPublication.class,false),
        LIFECYCLE_CURRENT_ADOPTION(APPLICATION,org.xar.ck3.control.application.lifecycle.LifecycleEpisodeInputs.class,false),
        ACTUAL_EPISODE_JOURNAL(APPLICATION,org.xar.ck3.control.application.session.ContinuityBatchJournal.class,false),
        ADMITTED_EPISODE(LOCAL_SERVICE,RootPendingUiAdmittedEpisodeQualification.class,false),
        TRANSPORT_EVIDENCE(APPLICATION,org.xar.ck3.control.application.session.SameGameTransportContinuity.class,false),
        // Helpers seal/compare DATA under the selected full source epoch. PENDING_RUNTIME
        // remains the sole canonical natural-domain producer; no extra publisher is added.
        ROOT_CONTINUITY(LOCAL_SERVICE,RootPendingUiContinuity.class,false),
        ROOT_SOURCE_CONTINUITY(LOCAL_SERVICE,RootSourceProofContinuity.class,false),
        CHANGED_PREFLIGHT(LOCAL_SERVICE,RootChangedSuccessionPreflight.class,false),
        TRANSPORT_BINDING(LOCAL_SERVICE,org.xar.ck3.control.runtime.lifecycle.PendingSameGameContinuity.class,false),
        PRECLOCK_SOURCE(APPLICATION,DriverPreclockExpectationSource.class),
        // This package-private app class cannot be named by a service class literal; its exact selected target is still mandatory.
        PRECLOCK_PRODUCER("application/src/main/java/org/xar/ck3/control/application/driver/DriverPreclockExpectationProducer.java",Optional.empty()),
        DRIVER_ASSEMBLER(APPLICATION,DriverStateAssembler.class),
        PRIVATE_DATE(APPLICATION,org.xar.ck3.control.application.advance.PendingUiLifeAdvance.class),
        LIFE_COMMANDS(APPLICATION,org.xar.ck3.control.application.advance.LifeAdvanceCommands.class),
        LIFE_MATERIAL(APPLICATION,org.xar.ck3.control.application.advance.LifeAdvanceEvidence.class),
        PRIVATE_EVENT(APPLICATION,org.xar.ck3.control.application.planning.events.PendingUiEvent.class),
        PRIVATE_EVENT_PREPARATION(LOCAL_SERVICE,PendingUiEventPreparation.class),
        EVENT_PREPARATION(LOCAL_SERVICE,EventActionPreparation.class),EVENT_INSTALLER(LOCAL_SERVICE,EventRuntimeInstaller.class),
        EVENT_RECOVERY(LOCAL_SERVICE,RootPendingUiEventRecovery.class),
        EVENT_AFTER(APPLICATION,org.xar.ck3.control.application.effects.NativeEffectSnapshots.class),
        EVENT_EFFECTS(APPLICATION,org.xar.ck3.control.application.effects.NativeEventEffects.class),
        CLOSE_RECONCILIATION(LOCAL_SERVICE,RootPendingUiCloseReconciliation.class),
        PENDING_MODAL(G2_RESEARCH,org.xar.ck3.control.wave2.governance.succession.PendingModalClearance.class),
        PENDING_RUNTIME(LOCAL_SERVICE,RootPendingUiRuntime.class),PENDING_COLD(LOCAL_SERVICE,RootPendingUiColdQualification.class),
        DRIVER_FACTS(APPLICATION,org.xar.ck3.control.application.driver.DriverSnapshotFacts.class),
        PENDING_INSTALLER(LOCAL_SERVICE,RootDriverLifecycleRuntimeInstaller.class),
        // Public boundary consumers remain selected and loaded through this same Root cut; they do not produce causal domain authority.
        PENDING_SUPPLIER(LOCAL_SERVICE,RootDriverLifecyclePublicSupplier.class,false),PENDING_PUBLIC_CODEC(LOCAL_SERVICE,RootDriverLifecyclePublicCodec.class,false),
        PENDING_RESUME_CODEC(LOCAL_SERVICE,RootDriverLifecycleResumeCodec.class,false),
        PENDING_QUALIFIER(LOCAL_SERVICE,org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.class),
        PENDING_CAUSE_PROOF(LOCAL_SERVICE,org.xar.ck3.control.runtime.lifecycle.PendingNaturalCauseProof.class),
        UI_STATE(APPLICATION,org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.class),
        UI_CODEC(APPLICATION,org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.class),
        UI_REDUCER(APPLICATION,org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer.class),
        FINAL_REDUCER(APPLICATION,org.xar.ck3.control.application.lifecycle.LifecycleReducer.class),
        NATURAL_PREPARATION(APPLICATION,org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation.class),
        NATURAL_CONTINUATION(APPLICATION,org.xar.ck3.control.application.lifecycle.NaturalSuccessionContinuationSource.class),
        PENDING_SOURCE(APPLICATION,org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.class),
        PENDING_PROJECTION(APPLICATION,org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection.class),
        PENDING_MUTATIONS(APPLICATION,org.xar.ck3.control.application.driver.DriverPendingEpisodeMutations.class),
        PENDING_PRODUCER("application/src/main/java/org/xar/ck3/control/application/driver/DriverPendingEpisodeProducer.java",Optional.empty());
        private final String target;private final Optional<Class<?>> actualClass;private final boolean naturalProducer;
        JavaLeaf(Module module,Class<?> actualClass){this(module,actualClass,true);}
        JavaLeaf(Module module,Class<?> actualClass,boolean naturalProducer){this(module.directory()+"/src/main/java/"+actualClass.getName().replace('.','/')+".java",Optional.of(actualClass),naturalProducer);}
        JavaLeaf(String target,Optional<Class<?>> actualClass){this(target,actualClass,true);}
        JavaLeaf(String target,Optional<Class<?>> actualClass,boolean naturalProducer){this.target=target;this.actualClass=actualClass;this.naturalProducer=naturalProducer;}
    }
    private static final List<Role> NATIVE_LEAVES=List.of(Role.LIFECYCLE_CAMPAIGN_ROOT,Role.LIFECYCLE_ROOT_SERIALIZER,Role.LIFECYCLE_ROOT_MAILBOX,
            Role.LIFECYCLE_TIMELINE,Role.LIFECYCLE_TIMELINE_NATIVE,Role.LIFECYCLE_TIMELINE_MAILBOX,Role.LIFECYCLE_CLOSE,
            Role.LIFECYCLE_CLOSE_MAILBOX,Role.LIFECYCLE_SUCCESSION_MODAL,Role.LIFECYCLE_PRISONER_RETAINED,Role.LIFECYCLE_PRISONER_COLLECTION);
    public static RootLifecycleRuntimeFactory.Prepared prepare(Input actual,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,RootRuntimeDomainSettings.Bound settings)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(selected);Objects.requireNonNull(originals);Objects.requireNonNull(settings);
        var definitions=actual.definitions();var clock=actual.clock();
        originals.requireCurrent(clock);settings.requireCurrent(clock);selected.requireCurrent();definitions.originalRef().verify();
        String machine=definitions.configuration().machineId();
        require(machine.equals(originals.configuration().machineId())&&machine.equals(settings.configuration().machineId()),"lifecycle sources crossed actual runtime input machine");
        Instant now=clock.instant();require(!now.isBefore(Instant.parse(definitions.configuration().observedAtUtc()))
                &&now.isBefore(Instant.parse(definitions.configuration().reviewAtUtc())),"actual lifecycle runtime definitions are future-dated or expired");
        require(same(definitions.data(RootRuntimeDefinitionModel.DataRole.NATIVE_DOMAIN_ORIGINALS),originals.original())
                &&same(definitions.data(RootRuntimeDefinitionModel.DataRole.REMAINING_DOMAIN_SETTINGS),settings.original()),"lifecycle must consume the identical actual native/settings data-role originals");
        RootRuntimeDefinitions.verifySources(definitions.configuration(),definitions.sourceIndex());
        var configuration=settings.configuration().lifecycle().configuration();
        actual.sameGuard().requireFilePort(actual.sameGuardedFiles());
        actual.sameGuard().requireManagedRoots(List.of(configuration.stateRoot(),configuration.saveGames(),configuration.evidenceRoot()));
        // The helper is itself part of the actual selected loaded source graph, but is not an extra natural-domain producer leaf.
        selectJava(selected,definitions.sourceIndex(),"local-service/src/main/java/org/xar/ck3/control/service/root/RootLifecycleSourcesFactory.java",Optional.of(RootLifecycleSourcesFactory.class));
        var java=new EnumMap<JavaLeaf,ExactRef>(JavaLeaf.class);
        for(var leaf:JavaLeaf.values())java.put(leaf,selectJava(selected,definitions.sourceIndex(),leaf.target,leaf.actualClass));
        ExactRef sameCollection=actual.samePrisoners().collectionProducer();
        require(same(java.get(JavaLeaf.COLLECTION),sameCollection)
                &&same(definitions.source(RootRuntimeDefinitionModel.SourceRole.PRISONER_COLLECTION_PRODUCER),sameCollection),"lifecycle prisoner definition differs from actual shared Java collection producer role");
        // Preserve the identical injected reference that the actual Prisoners ordinal0 contract will retain.
        java.put(JavaLeaf.COLLECTION,sameCollection);
        var nativeSources=new EnumMap<Role,ExactRef>(Role.class);
        for(Role role:NATIVE_LEAVES){
            var original=originals.configuration().source(role);ExactRef retained=selected.original(original.original(),role.kind());
            require(same(retained,originals.source(role)),"lifecycle native source crossed its actual typed original role: "+role);
            nativeSources.put(role,retained);
        }
        var producers=new ArrayList<ExactRef>();for(var leaf:JavaLeaf.values())if(leaf.naturalProducer)producers.add(java.get(leaf));
        for(Role role:NATIVE_LEAVES)producers.add(nativeSources.get(role));
        require(producers.size()==64&&producers.stream().distinct().count()==64,"complete unique actual lifecycle64 causal source leaves required");
        var sources=new RootLifecycleRuntimeFactory.Sources(producers,nativeSources.get(Role.LIFECYCLE_TIMELINE),nativeSources.get(Role.LIFECYCLE_CLOSE),
                sameCollection,java.get(JavaLeaf.NATURAL),java.get(JavaLeaf.TIMELINE),java.get(JavaLeaf.TERMINAL_PRISONER),
                java.get(JavaLeaf.COMPOSITE),java.get(JavaLeaf.COMPOSITE));
        // Source custody only: no Core/writer, loaded plan, permissions, managed creator or live admission is constructed here.
        selected.requireCurrent();originals.requireCurrent(clock);settings.requireCurrent(clock);definitions.originalRef().verify();
        var prepared=new RootLifecycleRuntimeFactory.Prepared(sources,configuration,actual.sameGuardedFiles(),actual.sameGuard(),clock);
        prepared.bindChangedPreflightSource(java.get(JavaLeaf.CHANGED_PREFLIGHT));return prepared;
    }
    /** Actual selector producer -> exact declared winner guard. Package-private for source-only custody regressions. */
    static ExactRef selectJava(RootRuntimeSelectedSources selected,List<SelectedSource> actualIndex,String target,Optional<Class<?>> actualClass)throws IOException {
        Objects.requireNonNull(selected);actualIndex=List.copyOf(actualIndex);Objects.requireNonNull(target);Objects.requireNonNull(actualClass);
        var declarations=actualIndex.stream().filter(row->row.targetRelative().equals(target)).toList();
        require(declarations.size()==1,"actual runtime input must declare exactly one lifecycle Java winner: "+target);
        ExactRef result=actualClass.isPresent()?selected.javaSourceAt(target,actualClass.orElseThrow()):selected.javaTarget(target);
        require(same(declarations.getFirst().sourceRef(),result),"lifecycle Java selector crossed the actual runtime input winner: "+target);
        return result;
    }
    private static boolean same(FileRef left,FileRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static boolean same(ExactRef left,ExactRef right){return Path.of(left.path()).equals(Path.of(right.path()))&&left.bytes()==right.bytes()&&left.sha256().equalsIgnoreCase(right.sha256());}
    private static void require(boolean value,String reason)throws IOException {if(!value)throw new IOException(reason);}
}
