package org.xar.ck3.control.service.root;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ordinary.OrdinaryClaimDomain;
import org.xar.ck3.control.application.action.ordinary.OrdinaryOnceClaims;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.application.ritecreation.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.LegacyWindowsPathCanonicalizer;
import org.xar.ck3.control.contracts.ManagedCampaignRunBinding;
import org.xar.ck3.control.nativebridge.capabilities.family.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.ritecreation.RiteCreationNative;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.WindowsOriginalRuntimeHandoff;
import org.xar.ck3.control.service.sway.SwayRuntimeInstaller;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Plain ordinary configuration and actual implementation metadata; no Core, Prepared, history or Game is created here. */
public final class RootOrdinaryFamilySourcesFactory {
    private RootOrdinaryFamilySourcesFactory() { }

    public static RootRuntimeDomainAssembly.OrdinaryFamilyConfiguration configuration(
            RootOrdinaryRuntimeConfiguration config,RootApplicationConfiguration app,
            RootRuntimeSourceProducts.OrdinaryRuntimePorts ports,RootAdditionalDomains.ImplementationMetadata metadata) {
        Objects.requireNonNull(config);Objects.requireNonNull(app);Objects.requireNonNull(ports);Objects.requireNonNull(metadata);
        // These are normal enabled policy choices, never observations of a spouse, a candidate or a native action.
        var settings=new FamilyPorts.Settings(true,true,true,true,Optional.empty());
        return new RootRuntimeDomainAssembly.OrdinaryFamilyConfiguration(
                new RootFamilyRuntimeFactory.OrdinaryConfiguration(app.ledger().lock(),settings,
                        config.stateDirectory().resolve("family-relations")),
                new RootGuardianRuntimeFactory.OrdinaryConfiguration(app.ledger().lock()),
                new SwayRuntimeInstaller.OrdinaryConfiguration(app.ledger().lock(),
                        config.stateDirectory().resolve("strategy").resolve("ordinary-sway-formal-v1.json"),
                        new OrdinarySwayService.Capabilities(true,true,true),true),
                new RootRiteCreationRuntimeFactory.OrdinaryConfiguration(true,
                        new RootRiteCreationScopeAuthority(ports.core(),config.freshness(),ports.clock())));
    }

    public static RootRuntimeDomainAssembly.OrdinaryFamilySources sources(
            RootOrdinaryRuntimeConfiguration config,RootApplicationConfiguration app,
            RootRuntimeSourceProducts.OrdinaryRuntimePorts ports,RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef actualNativeDLL) {
        Objects.requireNonNull(config);Objects.requireNonNull(app);Objects.requireNonNull(ports);
        Objects.requireNonNull(metadata);Objects.requireNonNull(actualNativeDLL);
        return new RootRuntimeDomainAssembly.OrdinaryFamilySources(family(metadata,actualNativeDLL),
                guardian(metadata,actualNativeDLL),sway(metadata,actualNativeDLL),rite(metadata,actualNativeDLL));
    }

    private static RootFamilyRuntimeFactory.Sources family(RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef nativeCode) {
        var complete=carriers(metadata,nativeCode,
                RootOrdinaryFamilySourcesFactory.class,RootFamilyRuntimeFactory.class,FamilyRuntimeInstaller.class,
                RootFamilyOriginalDomains.class,RootFamilyOrdinaryRestoreDomains.class,RootRuntimeDomainAssembly.class,
                RootFamilyNativeReadProducts.class,FamilyDomainSource.class,FamilyNaturalEpisodeMigration.class,
                FamilyNextEpisodeMigration.class,FamilyOrdinaryRestoreMigration.class,FamilyInitialData.class,
                FamilyOrdinaryPolicy.class,FamilyPendingStore.class,FamilyPendingProducer.class,FamilyResultReducer.class,
                FamilyMarriagePreparationReview.class,FamilyNativePreparation.class,LifecycleComposites.class,
                FamilyObligationsCodec.class,ChildEducationFocus.class,FamilyCurrentRelation.class,
                FamilyMarriageProjectionQueries.class,FamilyChildMarriageSubject.class,FamilyChildMarriageQueries.class,
                FamilyMarriageResults.class,FamilyMarriageAlliance.class,FamilyOutgoingCodec.class,
                FamilyMarriageNativeRequests.class,RootFamilyMarriageFreshPreparation.class,MarriageSendEffects.class,
                RootFamilyMarriageSendRuntime.class,RootChildEducationFocusRuntime.class,ChildEducationFocusEffects.class,
                ChildEducationFocusQueries.class,EpidemicTreatmentPresenceQueries.class,RootEpidemicTreatmentRead.class);
        var reads=new RootFamilyReadProducts.Sources(nativeCode,metadata.implementation(FamilyObligationsCodec.class),
                nativeCode,metadata.implementation(ChildEducationFocus.class));
        var nativeReads=new RootFamilyNativeReadProducts.Sources(
                leaf(metadata,nativeCode,FamilyCurrentRelation.class),
                leaf(metadata,nativeCode,FamilyMarriageProjectionQueries.class),
                leaf(metadata,nativeCode,FamilyChildMarriageSubject.class),
                leaf(metadata,nativeCode,FamilyChildMarriageQueries.class),
                leaf(metadata,nativeCode,FamilyMarriageResults.class),
                leaf(metadata,nativeCode,FamilyMarriageResults.class),
                leaf(metadata,nativeCode,FamilyMarriageAlliance.class),
                leaf(metadata,nativeCode,FamilyMarriageAlliance.class),
                leaf(metadata,nativeCode,FamilyMarriageAlliance.class));
        var marriages=new RootFamilyMarriageSendRuntime.Sources(nativeCode,metadata.implementation(FamilyOutgoingCodec.class),
                metadata.implementation(FamilyMarriageNativeRequests.class),metadata.implementation(RootFamilyMarriageFreshPreparation.class),
                metadata.implementation(MarriageSendEffects.class),metadata.implementation(FamilyOutgoingCodec.class),
                metadata.implementation(RootFamilyMarriageSendRuntime.class),complete);
        var submissions=new FamilyNativePrivatePermissions.Sources(nativeCode,nativeCode,nativeCode,nativeCode);
        var focus=new RootChildEducationFocusRuntime.Sources(metadata.implementation(RootChildEducationFocusRuntime.class),
                metadata.implementation(ChildEducationFocusEffects.class),metadata.implementation(ChildEducationFocus.class),
                metadata.implementation(ChildEducationFocusQueries.class),complete);
        var treatment=new RootEpidemicTreatmentRead.Sources(nativeCode,
                metadata.implementation(EpidemicTreatmentPresenceQueries.class),complete);
        return new RootFamilyRuntimeFactory.Sources(
                new FamilyRuntimeInstaller.Sources(metadata.implementation(FamilyOrdinaryPolicy.class),
                        metadata.implementation(FamilyPendingStore.class),reads,complete),
                nativeReads,marriages,submissions,Optional.of(focus),treatment);
    }

    private static RootFamilyNativeReadProducts.Source leaf(RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef nativeCode,Class<?> actualDecoder) {
        return new RootFamilyNativeReadProducts.Source(nativeCode,metadata.implementation(actualDecoder));
    }

    private static RootGuardianRuntimeFactory.OrdinarySources guardian(
            RootAdditionalDomains.ImplementationMetadata metadata,ExactRef nativeCode) {
        var claimCarriers=carriers(metadata,nativeCode,RootOrdinaryFamilySourcesFactory.class,
                RootOrdinaryClaimRuntime.class,RootOrdinaryClaimOriginals.class,OrdinaryClaimDomain.class,
                OrdinaryOnceClaims.class,RootOrdinaryClaimRuntime.SourceConsumptionAuthority.class);
        // Legacy-role fields identify the Java import/refusal implementations, without asserting any legacy state or release.
        var claims=new RootOrdinaryClaimRuntime.Sources(metadata.implementation(RootOrdinaryClaimRuntime.class),
                metadata.implementation(RootOrdinaryClaimOriginals.class),metadata.implementation(OrdinaryClaimDomain.class),
                metadata.implementation(OrdinaryOnceClaims.class),metadata.implementation(RootOrdinaryClaimOriginals.class),
                metadata.implementation(RootOrdinaryClaimRuntime.SourceConsumptionAuthority.class),claimCarriers);
        var complete=union(claimCarriers,carriers(metadata,nativeCode,RootGuardianRuntimeFactory.class,
                RootGuardianReconciliationReads.class,GuardianOutgoingInstaller.class,OrdinaryPendingPublication.class,
                OrdinaryInitiationPreparation.class,GuardianOutgoingEffects.class,GuardianOutgoingCodec.class,
                GuardianReconciliationQueries.class,InteractionReads.class,RootOrdinaryFamilySourcesFactory.class));
        // The final source assembler supplies the identical Army claim Sources before the sole Guardian Prepared is made.
        return new RootGuardianRuntimeFactory.OrdinarySources(claims,metadata.implementation(OrdinaryInitiationPreparation.class),
                metadata.implementation(GuardianOutgoingEffects.class),metadata.implementation(GuardianOutgoingCodec.class),
                metadata.implementation(GuardianReconciliationQueries.class),nativeCode,
                metadata.implementation(InteractionReads.class),complete);
    }

    private static SwayRuntimeInstaller.Sources sway(RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef nativeCode) {
        var complete=carriers(metadata,nativeCode,RootOrdinaryFamilySourcesFactory.class,SwayRuntimeInstaller.class,
                SwayNativeBindings.class,SwayNativeWire.class,SwayObservationReads.class,SwayActionLifecycle.class,
                OrdinarySwayPolicy.class,SwayOrdinaryExecutor.class,SwayOrdinaryComposite.class,SwayCanonicalDomain.class,
                SwayFormalState.class,SwayFormalCodec.class,SwayLegacyImport.class,SwayTransitionCodec.class,
                SwaySchedulerReplay.class,SwayNextEpisodeImport.class,SwayFollowingConsumption.class,SwaySessionInputs.class,
                OrdinarySwayReadSource.class,OrdinarySwayPolicyFactory.class,SwaySelectedFinish.class,SwaySelectedJournal.class,
                SwaySelectedObservation.class,SwayPublicCodec.class,SwaySelectedStart.class,SwayDriverCodec.class,FreshCampaignContext.class);
        var bindings=metadata.implementation(SwayNativeBindings.class);
        var decoder=metadata.implementation(SwayNativeWire.class);
        var lifecycle=metadata.implementation(SwayActionLifecycle.class);
        return new SwayRuntimeInstaller.Sources(new SwayRootReads.Sources(bindings,decoder,
                metadata.implementation(SwayObservationReads.class)),new SwayRootActions.Sources(bindings,decoder,lifecycle),
                metadata.implementation(OrdinarySwayPolicy.class),metadata.implementation(SwayOrdinaryExecutor.class),
                metadata.implementation(SwayOrdinaryComposite.class),lifecycle,complete);
    }

    private static RootRiteCreationRuntimeFactory.OrdinarySources rite(RootAdditionalDomains.ImplementationMetadata metadata,
            ExactRef nativeCode) {
        var complete=carriers(metadata,nativeCode,RiteCreationNative.class,RiteCreationContract.class,RiteCreationCodec.class,
                RiteCreationState.class,RiteCreationDomainState.class,RiteCreationLegacyStore.class,RootRiteCreationDomain.class,
                RootRiteCreationLegacyImport.class,RootRiteCreationLegacyArchive.class,RootRiteCreationRuntimeFactory.class,
                RootRiteCreationScopeAuthority.class,RootOrdinaryFamilySourcesFactory.class,ManagedCampaignRunBinding.class,
                LegacyWindowsPathCanonicalizer.class,OriginalRuntimeHandoffProof.class,WindowsOriginalRuntimeHandoff.class);
        return new RootRiteCreationRuntimeFactory.OrdinarySources(
                new RiteCreationNative.Sources(nativeCode,metadata.implementation(RiteCreationNative.class),complete),
                metadata.implementation(RootRiteCreationRuntimeFactory.class),complete);
    }

    /** Finite actual code carriers, deduplicated by the shared metadata cache; this is no source qualification. */
    private static List<ExactRef> carriers(RootAdditionalDomains.ImplementationMetadata metadata,ExactRef nativeCode,
            Class<?>... implementations) {
        var result=new LinkedHashSet<ExactRef>();result.add(Objects.requireNonNull(nativeCode));
        for(Class<?> implementation:implementations)result.add(metadata.implementation(implementation));
        return List.copyOf(result);
    }

    private static List<ExactRef> union(List<ExactRef> first,List<ExactRef> second) {
        var result=new LinkedHashSet<ExactRef>(first);result.addAll(second);return List.copyOf(result);
    }
}
