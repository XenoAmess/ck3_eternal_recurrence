package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.*;
import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.WindowsOriginalRuntimeHandoff;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.warexit.WarExitPolicies;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.aub.*;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContextRead;
import org.xar.ck3.control.nativebridge.capabilities.ritecreation.RiteCreationNative;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservationCodec;

/** The one concrete pre-Core source composition. Domain owners retain their real constructors and codecs.
 * This composition does not install a Game, import state, create a ledger or grant readiness. */
public final class RootRuntimeSourceProducts {
    private RootRuntimeSourceProducts(){ }
    public record Prepared(RootRuntimeCatalogFactory catalogs,RootFrontendRuntime.Sources frontend,
            RootRuntimeDomainAssembly.Prepared domains,RootRuntimeDomainSettings.Bound settings,
            RootRuntimeNativeOriginals.Bound originals,RootDriverProductSourcesFactory driverProductSources) {
        public Prepared {Objects.requireNonNull(catalogs);Objects.requireNonNull(frontend);Objects.requireNonNull(domains);
            Objects.requireNonNull(settings);Objects.requireNonNull(originals);Objects.requireNonNull(driverProductSources);}
    }

    /** Real read and policy admissions are supplied by their owner, never replaced by a permissive callback. */
    public record ActivityConfiguration(List<ActivityNativeContracts.Source> reads,
            List<ActivityActionRoutes.Source> actions,ActivityNativeContracts.Admission readAdmission,
            ActivityActionRoutes.Admission actionAdmission,RootRuntimeDefinitionModel.Build build,ExactRef codec) {
        public ActivityConfiguration {
            reads=List.copyOf(reads);actions=List.copyOf(actions);Objects.requireNonNull(readAdmission);
            Objects.requireNonNull(actionAdmission);Objects.requireNonNull(build);Objects.requireNonNull(codec);
        }
    }

    /** Ordinary configuration and real products from domain constructors, all available before Core.open. */
    public record OrdinaryConfiguration(RootRuntimePreparedSources.Governance governance,
            RootRuntimePreparedSources.Finance finance,ArmyRuntimeInstaller.Prepared army,
            RootRuntimePreparedSources.MilitaryConfiguration military,RootSaveRuntime.Sources save,
            RootAubRuntimeFactory.Prepared aub,RootContactRuntime.Sources contactScopes,
            RootRuntimeDomainAssembly.Prepared domains,RootAdditionalDomains.Prepared additionalDomains,
            ConstructionRuntimeInstaller.Sources construction,PrisonersRuntimeInstaller.Sources prisoners,
            PrisonersRuntimeInstaller.Configuration prisonerConfiguration,ActivityConfiguration activity,
            RootFrontendRuntime.Sources frontend,KnownInteractionsRuntimeInstaller.Sources interactions,
            List<ExactRef> readHistoryProducers,RootCrossRunPlanning.Prepared crossRun,
            EpisodeIncidentJournal.Configuration incidents,ExactRef incidentImplementation,CheckpointFiles checkpointFiles,
            List<DomainBodies.Registration> additionalRegistrations,int retainedEffects) {
        public OrdinaryConfiguration {
            Objects.requireNonNull(governance);Objects.requireNonNull(finance);Objects.requireNonNull(army);
            Objects.requireNonNull(military);Objects.requireNonNull(save);Objects.requireNonNull(aub);
            Objects.requireNonNull(contactScopes);Objects.requireNonNull(domains);Objects.requireNonNull(additionalDomains);
            Objects.requireNonNull(construction);Objects.requireNonNull(prisoners);Objects.requireNonNull(prisonerConfiguration);
            Objects.requireNonNull(activity);Objects.requireNonNull(frontend);Objects.requireNonNull(interactions);
            readHistoryProducers=List.copyOf(readHistoryProducers);Objects.requireNonNull(crossRun);
            Objects.requireNonNull(incidents);Objects.requireNonNull(incidentImplementation);Objects.requireNonNull(checkpointFiles);
            additionalRegistrations=List.copyOf(additionalRegistrations);
            StrictJson.require(!readHistoryProducers.isEmpty()&&retainedEffects>=1&&retainedEffects<=4096,
                    "bounded ordinary history and effects configuration required");
        }
    }

    public record OrdinaryPrepared(RootRuntimeCatalogFactory catalogs,RootRuntimeCatalogFactory.Sources sources) {
        public OrdinaryPrepared {
            Objects.requireNonNull(catalogs);Objects.requireNonNull(sources);
            StrictJson.require(catalogs.sources()==sources&&sources.historicalPackage().isEmpty(),
                    "ordinary catalog must retain its identical products without historical package metadata");
        }
    }

    /** Plain domain inputs; the settings DTOs describe business configuration, not runtime qualification. */
    public record OrdinaryDomainConfiguration(RootLifeRuntimeFactory.Sources life,RootAdvanceRuntimeFacts.Settings lifeSettings,
            RootAdvanceInfrastructureFactory.Sources infrastructure,RootAdvanceInfrastructureFactory.Timings timings,
            RootArmyStrengthsRuntimeFactory.Sources strengths,RootArmyStrengthsRuntimeFactory.Configuration strengthSettings,
            OriginalDriverQueryHistorySettings.Bound queryHistory,EventRuntimeInstaller.Sources events,EventSourceReadContext eventSources,
            RootLifecycleRuntimeFactory.Sources lifecycle,RootLifecycleRuntimeFactory.Configuration lifecycleSettings,
            RootCampaignPoliciesFactory.Sources campaign,RootHolyWarPlanningPolicies.Sources holy,
            RootActiveCombatDateGuardFactory.Sources activeCombat,ExactRef successionPolicies,RootWarCoreFactory.Sources war,
            RootPeacetimeWarEntryRuntime.Sources warEntry,RootRuntimeDomainAssembly.PolicySources policies,
            OrdinaryMilitaryInstaller.PolicySources militaryPolicies,RaiktorActualRecommendationFactory.Configuration formalWar,
            M5PeacetimePolicy.Options peacetime,Duration physicalFreshness,RootActionHistoryMaterialSourceFactory.Sources actionHistory,
            RootRouteContactAdvanceRuntime.Sources routeAdvance,RootRouteContactAdvanceRuntime.Configuration routeSettings) {
        public OrdinaryDomainConfiguration {
            Objects.requireNonNull(life);Objects.requireNonNull(lifeSettings);Objects.requireNonNull(infrastructure);Objects.requireNonNull(timings);
            Objects.requireNonNull(strengths);Objects.requireNonNull(strengthSettings);Objects.requireNonNull(queryHistory);
            Objects.requireNonNull(events);Objects.requireNonNull(eventSources);Objects.requireNonNull(lifecycle);Objects.requireNonNull(lifecycleSettings);
            Objects.requireNonNull(campaign);Objects.requireNonNull(holy);Objects.requireNonNull(activeCombat);Objects.requireNonNull(successionPolicies);
            Objects.requireNonNull(war);Objects.requireNonNull(warEntry);Objects.requireNonNull(policies);Objects.requireNonNull(militaryPolicies);
            Objects.requireNonNull(formalWar);Objects.requireNonNull(peacetime);Objects.requireNonNull(physicalFreshness);
            Objects.requireNonNull(actionHistory);Objects.requireNonNull(routeAdvance);Objects.requireNonNull(routeSettings);
            StrictJson.require(routeSettings.deadline()==campaign.deadline(),"Route and campaign must retain the same configured deadline");
        }
    }

    /** Exports the same products needed by Driver; consumers never rebuild family, lifecycle, Events or Life. */
    public record OrdinaryDomainProducts(RootRuntimeDomainAssembly.Prepared domains,RootLifeRuntimeFactory.Prepared life,
            RootLifecycleRuntimeFactory.Prepared lifecycle,EventRuntimeInstaller.Prepared events) {
        public OrdinaryDomainProducts {Objects.requireNonNull(domains);Objects.requireNonNull(life);Objects.requireNonNull(lifecycle);Objects.requireNonNull(events);}
    }

    public record GovernanceConfiguration(Path writerLock,GovernanceRuntimeInstaller.Sources nativeSources,
            GovernanceRuntimeInstaller.Config nativeSettings,GovernanceOrdinaryRuntimeInstaller.Sources ordinarySources,
            RootCrownRetryRuntime.Sources retry,RootGovernanceDomains.Sources domains) {
        public GovernanceConfiguration {
            Objects.requireNonNull(writerLock);Objects.requireNonNull(nativeSources);Objects.requireNonNull(nativeSettings);
            Objects.requireNonNull(ordinarySources);Objects.requireNonNull(retry);Objects.requireNonNull(domains);
        }
    }
    public record ArmyConfiguration(ArmyRuntimeInstaller.Sources sources,ArmyRuntimeInstaller.Configuration settings,
            RootArmyOrdinaryRuntimeInputs.Sources ordinarySources,RootArmyOrdinaryRuntimeInputs.Configuration ordinarySettings,
            RootOrdinaryClaimRuntime.Sources claims) {
        public ArmyConfiguration {
            Objects.requireNonNull(sources);Objects.requireNonNull(settings);Objects.requireNonNull(ordinarySources);
            Objects.requireNonNull(ordinarySettings);Objects.requireNonNull(claims);
        }
    }
    public record FrontendConfiguration(FrontendRulesData.Build build,ExactRef nativeDriver,ExactRef effects,ExactRef decoder,
            InitialEpisodePolicy initialPolicy,DynamicCapabilities.Configuration capabilities,CapabilitySessionPresentation presentation,
            Duration freshness,Duration heartbeatMaximumAge,int retainedFrames,int retainedOrigins,String authorityId) {
        public FrontendConfiguration {
            Objects.requireNonNull(build);Objects.requireNonNull(nativeDriver);Objects.requireNonNull(effects);Objects.requireNonNull(decoder);
            Objects.requireNonNull(initialPolicy);Objects.requireNonNull(capabilities);Objects.requireNonNull(presentation);
            Objects.requireNonNull(freshness);Objects.requireNonNull(heartbeatMaximumAge);Objects.requireNonNull(authorityId);
        }
        public RootFrontendRuntime.Sources sources() {
            return RootFrontendRuntime.Sources.ordinary(build,nativeDriver,effects,decoder,initialPolicy,capabilities,presentation,
                    freshness,heartbeatMaximumAge,retainedFrames,retainedOrigins,authorityId);
        }
    }

    /** The production input contains business settings and source data, with no caller-created Prepared graph. */
    public record PlainConfiguration(GovernanceConfiguration governance,FinanceRuntimeInstaller.Sources finance,
            ArmyConfiguration army,RootRuntimePreparedSources.MilitaryConfiguration military,RootSaveRuntime.Sources save,
            RootAubRuntimeFactory.Sources aub,RootContactRuntime.Sources contactScopes,
            RootRuntimeDomainAssembly.OrdinaryFamilyConfiguration family,RootRuntimeDomainAssembly.OrdinaryFamilySources familySources,
            OrdinaryDomainConfiguration domains,RootAdditionalDomains.Config additionalDomains,
            ConstructionRuntimeInstaller.Sources construction,PrisonersRuntimeInstaller.Sources prisoners,List<ExactRef> prisonerProducers,
            ActivityConfiguration activity,FrontendConfiguration frontend,KnownInteractionsRuntimeInstaller.Sources interactions,
            List<ExactRef> readHistoryProducers,RootCrossRunPlanning.Sources crossRun,
            EpisodeIncidentJournal.Configuration incidents,ExactRef incidentImplementation,
            List<DomainBodies.Registration> additionalRegistrations,int retainedEffects) {
        public PlainConfiguration {
            Objects.requireNonNull(governance);Objects.requireNonNull(finance);Objects.requireNonNull(army);Objects.requireNonNull(military);
            Objects.requireNonNull(save);Objects.requireNonNull(aub);Objects.requireNonNull(contactScopes);Objects.requireNonNull(family);
            Objects.requireNonNull(familySources);Objects.requireNonNull(domains);Objects.requireNonNull(additionalDomains);
            Objects.requireNonNull(construction);Objects.requireNonNull(prisoners);prisonerProducers=List.copyOf(prisonerProducers);
            Objects.requireNonNull(activity);Objects.requireNonNull(frontend);Objects.requireNonNull(interactions);
            readHistoryProducers=List.copyOf(readHistoryProducers);Objects.requireNonNull(crossRun);
            Objects.requireNonNull(incidents);Objects.requireNonNull(incidentImplementation);additionalRegistrations=List.copyOf(additionalRegistrations);
            StrictJson.require(!prisonerProducers.isEmpty()&&!readHistoryProducers.isEmpty()&&retainedEffects>=1&&retainedEffects<=4096,
                    "ordinary producer inventories and effects bounds required");
        }
    }
    public record OrdinaryRuntimePorts(RootCoreBoundPorts core,CheckpointFiles files,RootRuntimeStorageGuard storage,
            OriginalRuntimeHandoffProof.Provider grants,RootSetPlayedCharacterRuntime.SourceFactory operatorSource,
            RootAdditionalDomains.ImplementationMetadata metadata,Clock clock) {
        public OrdinaryRuntimePorts {
            Objects.requireNonNull(core);Objects.requireNonNull(files);Objects.requireNonNull(storage);Objects.requireNonNull(grants);
            Objects.requireNonNull(operatorSource);Objects.requireNonNull(metadata);Objects.requireNonNull(clock);
        }
    }
    public record PlainPrepared(OrdinaryPrepared runtime,OrdinaryDomainProducts domains,
            RootRuntimeDomainAssembly.OrdinaryFamilyProducts family,RootArmySourcesFactory.Products army,
            RootRuntimePreparedSources.Governance governance,RootRuntimePreparedSources.Finance finance,
            RootCrossRunPlanning.Prepared crossRun,RootAdditionalDomains.Prepared additionalDomains) {
        public PlainPrepared {
            Objects.requireNonNull(runtime);Objects.requireNonNull(domains);Objects.requireNonNull(family);Objects.requireNonNull(army);
            Objects.requireNonNull(governance);Objects.requireNonNull(finance);Objects.requireNonNull(crossRun);Objects.requireNonNull(additionalDomains);
        }
    }

    /** Compose the real complete graph once, before Core.open and actual campaign-state initialization. */
    public static PlainPrepared prepareOrdinary(PlainConfiguration configuration,OrdinaryRuntimePorts ports)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(ports);
        var g=configuration.governance();
        var governance=RootRuntimePreparedSources.governance(g.writerLock(),g.nativeSources(),g.nativeSettings(),
                g.ordinarySources(),g.retry(),g.domains(),ports.clock());
        var a=configuration.army();
        var army=RootArmySourcesFactory.ordinary(a.sources(),a.settings(),a.ordinarySources(),a.ordinarySettings(),a.claims());
        var suppliedFamily=configuration.familySources();var suppliedGuardian=suppliedFamily.guardian();
        var sameGuardian=new RootGuardianRuntimeFactory.OrdinarySources(army.ordinaryClaimSources(),suppliedGuardian.preparation(),
                suppliedGuardian.effects(),suppliedGuardian.decoder(),suppliedGuardian.reconciliationProfile(),suppliedGuardian.ordinaryDefinition(),
                suppliedGuardian.ordinaryReadDecoder(),suppliedGuardian.supportingProducers());
        var family=RootRuntimeDomainAssembly.prepareOrdinaryFamily(configuration.family(),new RootRuntimeDomainAssembly.OrdinaryFamilySources(
                suppliedFamily.family(),sameGuardian,suppliedFamily.sway(),suppliedFamily.rite()));
        var externalGold=RootFinanceBodyBindings.prepare(configuration.construction(),family.family(),governance.ordinary(),
                ports.metadata().implementation(org.xar.ck3.control.application.planning.finance.ConstructionLedgerCodec.class),
                ports.metadata().implementation(org.xar.ck3.control.application.planning.family.FamilyDomainSource.class));
        var finance=RootRuntimePreparedSources.finance(configuration.finance(),externalGold);
        var crossRun=new RootCrossRunPlanning.Prepared(configuration.crossRun());
        var domains=prepareOrdinaryDomains(configuration.domains(),governance,army,family,crossRun,ports.files(),ports.storage(),ports.clock());
        var shared=new RootDriverProductSourcesFactory.SharedServices(finance.prepared(),configuration.construction(),family.family(),
                domains.lifecycle(),governance.nativeGovernance(),ports.grants(),ports.operatorSource());
        var additional=RootAdditionalDomains.ordinary(configuration.additionalDomains(),shared,ports.core(),ports.metadata(),ports.clock());
        var frontend=configuration.frontend().sources();
        var aub=configuration.aub();
        var actualConfiguration=new OrdinaryConfiguration(governance,finance,army.army(),configuration.military(),configuration.save(),
                RootRuntimePreparedSources.aub(aub.nativeSources(),aub.preparationAndReplay(),aub.producerClosure()),configuration.contactScopes(),
                domains.domains(),additional,configuration.construction(),configuration.prisoners(),
                new PrisonersRuntimeInstaller.Configuration(new PrisonersRuntimeDefinitions(configuration.prisonerProducers())),
                configuration.activity(),frontend,configuration.interactions(),configuration.readHistoryProducers(),crossRun,
                configuration.incidents(),configuration.incidentImplementation(),ports.files(),configuration.additionalRegistrations(),configuration.retainedEffects());
        return new PlainPrepared(prepareOrdinary(actualConfiguration,ports.core()),domains,family,army,governance,finance,crossRun,additional);
    }

    public static OrdinaryDomainProducts prepareOrdinaryDomains(OrdinaryDomainConfiguration configuration,
            RootRuntimePreparedSources.Governance governance,RootArmySourcesFactory.Products army,
            RootRuntimeDomainAssembly.OrdinaryFamilyProducts family,RootCrossRunPlanning.Prepared crossRun,
            CheckpointFiles files,RootRuntimeStorageGuard storage,Clock clock)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(governance);Objects.requireNonNull(army);
        Objects.requireNonNull(family);Objects.requireNonNull(crossRun);Objects.requireNonNull(files);Objects.requireNonNull(storage);Objects.requireNonNull(clock);
        var infrastructure=new RootAdvanceInfrastructureFactory.Prepared(configuration.infrastructure(),configuration.timings());
        var life=new RootLifeRuntimeFactory.Prepared(configuration.life(),configuration.lifeSettings(),infrastructure);
        var strengths=new RootArmyStrengthsRuntimeFactory.Prepared(configuration.strengths(),configuration.strengthSettings(),configuration.queryHistory());
        var events=new EventRuntimeInstaller.Prepared(configuration.events(),configuration.eventSources());
        var lifecycle=new RootLifecycleRuntimeFactory.Prepared(configuration.lifecycle(),configuration.lifecycleSettings(),files,storage,clock);
        var campaign=new RootCampaignPoliciesFactory.Prepared(configuration.campaign());
        var holy=new RootHolyWarPlanningPolicies.Prepared(configuration.holy());
        var actionHistory=new RootActionHistoryMaterialSourceFactory.Prepared(configuration.actionHistory());
        var routeAdvance=new RootRouteContactAdvanceRuntime.Prepared(configuration.routeAdvance(),configuration.routeSettings());
        var domains=new RootRuntimeDomainAssembly.Prepared(life,family.family(),army.ordinary(),strengths,events,lifecycle,
                family.sway(),new RootRuntimeDomainAssembly.SwayFresh(),governance.retry(),crossRun,campaign,family.guardian(),holy,
                configuration.activeCombat(),configuration.successionPolicies(),configuration.war(),RootPeacetimeWarEntryRuntime.prepare(configuration.warEntry()),
                family.rite(),configuration.policies(),configuration.militaryPolicies(),configuration.formalWar(),configuration.peacetime(),
                configuration.physicalFreshness(),actionHistory,routeAdvance);
        return new OrdinaryDomainProducts(domains,life,lifecycle,events);
    }

    /** No Definitions reader, selected-source registration, package publication or post-Core context is required. */
    public static OrdinaryPrepared prepareOrdinary(OrdinaryConfiguration configuration,RootCoreBoundPorts ports)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(ports);
        var governance=configuration.governance();var activityConfiguration=configuration.activity();
        var activity=RootRuntimePreparedSources.activity(activityConfiguration.reads(),activityConfiguration.readAdmission());
        var actions=RootRuntimePreparedSources.activityActions(activityConfiguration.actions(),activityConfiguration.actionAdmission());
        var sources=new RootRuntimeCatalogFactory.Sources(governance.nativeGovernance(),configuration.finance().prepared(),
                configuration.army(),RootRuntimePreparedSources.military(configuration.military()),configuration.save(),configuration.aub(),
                RootContactRuntime.prepare(configuration.contactScopes()),configuration.domains(),configuration.additionalDomains(),
                configuration.construction(),configuration.prisoners(),configuration.prisonerConfiguration(),governance.ordinary(),
                governance.retry(),governance.states(),governance.domains(),activity,actions,activityConfiguration.codec(),
                configuration.frontend(),configuration.interactions(),configuration.readHistoryProducers(),configuration.crossRun(),
                RootRuntimePreparedSources.incidents(configuration.incidents(),configuration.incidentImplementation()),
                configuration.checkpointFiles(),Optional.empty(),configuration.additionalRegistrations(),configuration.retainedEffects());
        var catalogs=new RootRuntimeCatalogFactory(sources);
        ports.bindActivityProducts(activity,governance.ordinary().feastDomain(),activityConfiguration.build());
        ports.bindCatalogs(catalogs);
        return new OrdinaryPrepared(catalogs,sources);
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeDomainSettings.Bound settings,RootRuntimeNativeOriginals.Bound originals,
            RootSelectedRegistrationConfiguration.Bound registration,RootFrontendRuntime.Sources frontend,
            RootCoreBoundPorts ports,RootRuntimeStorageGuard storage,CheckpointFiles files,
            Request actualPackage,NativeLaunchPlan plan,Clock clock)throws IOException {
        for(Object actual:List.of(inputs,selected,settings,originals,registration,frontend,ports,storage,files,actualPackage,plan,clock))
            Objects.requireNonNull(actual);
        settings.requireCurrent(clock);originals.requireCurrent(clock);registration.requireCurrent(inputs,clock);selected.requireInputs(inputs);
        selected.javaSource(CONTRACTS,org.xar.ck3.control.contracts.NativeCharacterId.class);
        var activityPublic=selected.javaSource(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.activity.ActivityPublic64.class);
        if(plan.sources().review().completeRuntimeSources().stream().noneMatch(ref->Path.of(ref.path()).equals(Path.of(activityPublic.path()))
                &&ref.bytes()==activityPublic.bytes()&&ref.sha256().equalsIgnoreCase(activityPublic.sha256())))
            throw new IOException("actual Activity public formatter is outside the identical complete runtime source cut");
        for(Class<?> actualRuntime:List.of(RootManagedSessionScope.class,RootSavedOrdinaryReopen.class,RootSaveCheckpointCommandProducer.class,
                RootArmyReadPacketVerifier.class,RootPublicStepFailureOriginals.class,RootUnresolvedHistoryQualification.class,RootRejectedPublicReadCollector.class,
                RootPhysicalStatusReadAuthority.class,RootDirectFixedWindowQueryAuthority.class,RootMenuPhysicalStatusReads.class)){
            var source=selected.javaSource(LOCAL_SERVICE,actualRuntime);
            if(plan.sources().review().completeRuntimeSources().stream().noneMatch(ref->Path.of(ref.path()).equals(Path.of(source.path()))
                    &&ref.bytes()==source.bytes()&&ref.sha256().equalsIgnoreCase(source.sha256())))
                throw new IOException("actual private runtime producer is outside the identical complete runtime source cut: "+actualRuntime.getName());
        }
        var rejectedReads=selected.javaSource(APPLICATION,org.xar.ck3.control.application.reads.PlanningPublicReadCollection.class);
        if(plan.sources().review().completeRuntimeSources().stream().noneMatch(ref->Path.of(ref.path()).equals(Path.of(rejectedReads.path()))
                &&ref.bytes()==rejectedReads.bytes()&&ref.sha256().equalsIgnoreCase(rejectedReads.sha256())))
            throw new IOException("actual public read collection is outside the identical complete runtime source cut");
        var publicCapture=selected.javaSource(APPLICATION,org.xar.ck3.control.application.checkpoint.PublicCheckpointMaterialCapture.class);
        if(plan.sources().review().completeRuntimeSources().stream().noneMatch(ref->Path.of(ref.path()).equals(Path.of(publicCapture.path()))
                &&ref.bytes()==publicCapture.bytes()&&ref.sha256().equalsIgnoreCase(publicCapture.sha256())))
            throw new IOException("actual public checkpoint material capture is outside the identical complete runtime source cut");
        storage.requireFilePort(files);settings.requireManagedRoots(storage);
        var nativeGovernance=RootRuntimePreparedSources.nativeGovernance(inputs,selected,clock);
        var governance=RootRuntimePreparedSources.ordinaryGovernance(inputs,clock);
        var retry=RootRuntimePreparedSources.crownRetry(inputs);
        var civic=RootRuntimePreparedSources.governanceDomains(inputs,retry);
        var construction=RootRuntimePreparedSources.construction(inputs);
        var prisoners=RootRuntimePreparedSources.prisoners(inputs);
        var prisonerDefinitions=RootRuntimePreparedSources.prisonerDefinitions(inputs);
        var family=RootNativeFamilySourcesFactory.prepare(inputs,selected,originals,settings,
                new RootNativeFamilySourcesFactory.OriginalDocuments(exact(inputs.data(FAMILY_DOMAIN)),
                        exact(inputs.data(CHILD_MATRILINEAL_DOMAIN)),exact(inputs.data(DEFAULT_MARRIAGE_DOMAIN))));
        var externalGold=RootFinanceBodyBindings.prepare(construction,family,governance,selected);
        var finance=RootRuntimePreparedSources.finance(inputs,externalGold);
        var ids=new RootPublicArmyActionIds(ports,inputs.configuration().army().actionIdPrefix());
        var stockRead=Optional.ofNullable(settings.configuration().stockRead()).map(RootRuntimeDomainSettings.StockRead::configuration);
        var armies=RootRuntimePreparedSources.army(inputs,selected,originals,ids,stockRead);
        var guardian=RootGuardianSourcesFactory.prepare(inputs,selected,originals,settings,armies.ordinaryClaimSources());
        var queryHistory=RootArmyQueryHistoryConfigurationProducer.readBound(inputs,selected,settings,plan,storage,clock);
        var strengths=RootArmyStrengthsSourcesFactory.prepare(inputs,selected,originals,queryHistory);
        var restoredOriginCodec=selected.javaSource(APPLICATION,org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData.class);
        requireRestoredOriginClosure(inputs.configuration(),restoredOriginCodec);
        var lifecycle=RootLifecycleSourcesFactory.prepare(new RootLifecycleSourcesFactory.Input(inputs,prisoners,files,storage,clock),
                selected,originals,settings);
        var life=life(inputs,selected,originals);
        var events=events(inputs,selected,originals);
        var sway=RootSwaySourcesFactory.prepare(inputs,selected,settings,finance.root());
        var crossRun=RootRuntimePreparedSources.crossRun(inputs,files);
        var holy=new RootHolyWarPlanningPolicies.Prepared(new RootHolyWarPlanningPolicies.Sources(
                selected.javaSource(LOCAL_SERVICE,RootHolyWarPlanningPolicies.class)));
        var active=new RootActiveCombatDateGuardFactory.Sources(
                selected.javaSource(APPLICATION,ActiveCombatDateGuards.class),selected.javaSource(APPLICATION,ActiveCombatGuardProducers.class),
                selected.javaSource(APPLICATION,ActiveCombatObservedComparison.class),selected.javaSource(WAVE2_MILITARY,DefenderExitObservationCodec.class));
        var policies=new RootRuntimeDomainAssembly.PolicySources(selected.javaSource(APPLICATION,OrdinaryCorePolicy.class),
                selected.javaSource(APPLICATION,WarExitPolicies.class));
        var militaryPolicies=new OrdinaryMilitaryInstaller.PolicySources(selected.javaSource(APPLICATION,RouteOriginExposurePolicy.class),
                selected.javaSource(APPLICATION,M5PeacetimePolicy.class),selected.javaSource(APPLICATION,M5WartimeObservationPolicy.class));
        Duration freshness=Duration.ofMillis(inputs.configuration().startup().ordinaryFreshnessMs());
        var campaign=campaign(inputs,selected);
        var routeAdvance=RootRouteContactAdvanceSourcesFactory.prepare(inputs,selected,campaign.sources().deadline());
        var domains=new RootRuntimeDomainAssembly.Prepared(life,family,armies.ordinary(),strengths,events,lifecycle,
                sway.prepared(),sway.initialization(),retry,crossRun,campaign,guardian,holy,active,
                selected.javaSource(LOCAL_SERVICE,RootSuccessionPlanningPolicies.class),RootWarCoreFactory.prepare(inputs),
                RootPeacetimeWarEntryRuntime.prepare(inputs),RootRiteCreationSourcesFactory.prepare(inputs,selected,originals,registration,ports,freshness,clock),
                policies,militaryPolicies,settings.configuration().formalWar().loadConfiguration(),settings.configuration().peacetime().options(),freshness,RootActionHistorySourcesFactory.prepare(inputs,selected,originals,clock),routeAdvance);
        var gui=RootGuiPublicProducts.prepare(inputs);
        var religion=RootReligionSourcesFactory.prepare(inputs,selected,originals,registration,clock);
        var artifacts=RootArtifactsSourcesFactory.prepare(new RootArtifactsSourcesFactory.Input(inputs,selected,originals,
                settings,registration,plan,storage,ports,WindowsOriginalRuntimeHandoff.relicOriginalOwnedLaunch(Optional.empty()),
                religion.sharedKernel(),clock),gui);
        var operatorAuthority=RootOperatorCharacterAuthority.prepare(inputs,selected);
        var driverSources=new RootDriverProductSourcesFactory(new RootDriverProductSourcesFactory.Input(inputs,selected,originals,
                settings,registration,plan,storage,frontend,finance.prepared(),construction,family,governance,retry,lifecycle,
                ports,nativeGovernance,OriginalRuntimeHandoffProof.unavailable(),clock,queryHistory,operatorAuthority));
        var driver=driverSources.prepare();
        var additional=new RootAdditionalDomains.Prepared(new RootFrontendRulesPublicProducts.Prepared(),
                RootFrontendCoaSources.prepare(inputs,selected,settings.configuration().coaReadLimits().limits(),
                        Duration.ofMillis(inputs.configuration().publicCatalog().observationTimeoutMs())),gui,religion,artifacts,
                RootChinaCasesSourcesFactory.prepare(inputs,selected),RootChinaCareerSourcesFactory.prepare(inputs,selected),driver);
        var activity=RootRuntimePreparedSources.activity(inputs,ports::verifyActivityRead);
        var activityActions=RootRuntimePreparedSources.activityActions(inputs,ports::qualifyPrivate,ports::verifyActivityAction);
        ports.bindActivityProducts(activity,governance.feastDomain(),inputs.configuration().frontend().build());
        var incidentGuard=storage.incidentGuard(List.of(Path.of(inputs.configuration().incidents().incidentBase()),
                Path.of(inputs.configuration().incidents().scanBase())));
        var contactSource=selected.javaSource(NATIVE_TRANSPORT,ContactScopeReads.class);
        var sources=new RootRuntimeCatalogFactory.Sources(nativeGovernance,finance.prepared(),armies.army(),
                RootRuntimePreparedSources.military(inputs,selected,plan),RootRuntimePreparedSources.save(inputs),aub(selected,originals),
                RootContactRuntime.prepare(new RootContactRuntime.Sources(contactSource,contactSource)),domains,additional,construction,prisoners,
                new PrisonersRuntimeInstaller.Configuration(prisonerDefinitions),governance,retry,RootRuntimePreparedSources.governanceStates(civic,retry),civic,
                activity,activityActions,inputs.source(RootRuntimeDefinitionModel.SourceRole.ACTIVITY_CODEC),frontend,
                RootRuntimePreparedSources.interactions(inputs),readHistory(inputs,selected),crossRun,
                RootRuntimePreparedSources.incidents(inputs,clock,incidentGuard),files,actualPackage,inputs.configuration().applicationRef(),
                List.of(),inputs.configuration().startup().retainedEffects());
        driverSources.requireDefinitions(sources);
        var catalogs=new RootRuntimeCatalogFactory(sources);ports.bindCatalogs(catalogs);
        selected.javaSource(LOCAL_SERVICE,RootRuntimeSourceProducts.class);selected.javaSource(LOCAL_SERVICE,RootFinanceBodyBindings.class);
        selected.javaSource(LOCAL_SERVICE,RootPublicArmyActionIds.class);selected.javaSource(LOCAL_SERVICE,RootRiteCreationScopeAuthority.class);
        settings.requireCurrent(clock);originals.requireCurrent(clock);registration.requireCurrent(inputs,clock);
        originals.requireQualifiedCut(plan);selected.requireCurrent();selected.requireLoadedClasses(plan);
        return new Prepared(catalogs,frontend,domains,settings,originals,driverSources);
    }
    /** Shared actual consumer of the producer's original configuration; this issues no runtime authority. */
    static void requireRestoredOriginClosure(RootRuntimeDefinitionModel.Configuration configuration,
            ExactRef exactSelectedCodec)throws IOException {
        Objects.requireNonNull(configuration);Objects.requireNonNull(exactSelectedCodec);
        if(RootRuntimeDefinitions.configuredSources(configuration).stream().noneMatch(row->row.sourceRef().equals(exactSelectedCodec)))
            throw new IOException("actual restored-origin codec is absent from the original configured source closure");
    }
    /** The configured complete closure must explicitly contain the actual rich producer/reader sources. */
    private static List<ExactRef> readHistory(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected)throws IOException {
        var configured=inputs.closure(RootRuntimeDefinitionModel.ClosureRole.READ_HISTORY);
        requireReadHistoryClosure(inputs,selected,configured);
        return configured;
    }
    /** The actual builder and persisted-configuration checks use the same exact selected producer closure. */
    static void requireReadHistoryClosure(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            List<ExactRef> configured)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(configured);
        selected.requireInputs(inputs);
        for(RequiredSource actual:requiredReadHistorySources()){
            var source=selected.javaSource(actual.module(),actual.type());
            if(!configured.contains(source))throw new IOException("configured read-history closure omitted the exact selected producer: "+actual.type().getName());
        }
    }
    /** The one typed roster consumed by both default configuration production and actual runtime composition. */
    public record RequiredSource(RootRuntimeSelectedSources.Module module,Class<?> type) {
        public RequiredSource {Objects.requireNonNull(module);Objects.requireNonNull(type);}
        public String targetRelative(){return module.directory()+"/src/main/java/"+type.getName().replace('.','/')+".java";}
    }
    public static List<RequiredSource> requiredReadHistorySources() {
        var required=new LinkedHashSet<RequiredSource>();
        for(Class<?> actual:List.of(org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.class,
                org.xar.ck3.control.application.history.DriverObservedHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial.class,
                org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverExecuteReadHistoryRegistry.class,
                org.xar.ck3.control.application.history.DriverExecuteQueryHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverPublicExecuteFailureMaterial.class,
                org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer.class,
                org.xar.ck3.control.application.history.DriverEarlyExecuteFailure.class,
                org.xar.ck3.control.application.history.DriverEarlyExecuteFailureRowProducer.class,
                org.xar.ck3.control.application.history.DriverReturnedActionHistoryMaterial.class,
                org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryMaterial.class,
                org.xar.ck3.control.application.history.DriverReturnedPublicReadHistoryRowProducer.class,
                org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.class,
                org.xar.ck3.control.application.history.DriverPostKnownReadFailureRowProducer.class,
                org.xar.ck3.control.application.history.DriverReturnedControlHistoryRowProducer.class,
                org.xar.ck3.control.application.planning.finance.GiftResolvedEvidence.class,
                org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.class)){
            required.add(new RequiredSource(APPLICATION,actual));
        }
        for(Class<?> actual:org.xar.ck3.control.application.driver.DriverReadHistoryPublisher.implementationTypes()){
            required.add(new RequiredSource(APPLICATION,actual));
        }
        for(Class<?> actual:List.of(RootPublicStepFailureOriginals.class,RootApplicationAssembly.class,
                RootApplicationSession.class,RootNativeSourceAuthority.class)){
            required.add(new RequiredSource(LOCAL_SERVICE,actual));
        }
        return List.copyOf(required);
    }
    private static RootLifeRuntimeFactory.Prepared life(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals)throws IOException {
        selected.javaSource(APPLICATION,PendingUiLifeAdvance.class);
        selected.javaSource(APPLICATION,org.xar.ck3.control.application.action.PauseConfirmation.class);
        var primitive=selected.javaSource(APPLICATION,AdvancePrimitives.class);
        var timings=RootAdvanceInfrastructureFactory.Timings.decode(exact(inputs.data(ADVANCE_TIMINGS)),
                new RawJson(RootRuntimeDefinitions.readData(new RootRuntimeDefinitionModel.DataPin(ADVANCE_TIMINGS,inputs.data(ADVANCE_TIMINGS)))));
        var infrastructure=new RootAdvanceInfrastructureFactory.Prepared(new RootAdvanceInfrastructureFactory.Sources(primitive,primitive,
                selected.javaSource(APPLICATION,AdvancePrimitiveArchivedReplay.class),
                originals.source(RootRuntimeNativeOriginals.Role.CLOCK_STATUS_DEFINITION),selected.javaSource(APPLICATION,ClockStatusRead.class),
                selected.javaSource(LOCAL_SERVICE,RootUnknownSentinelReadProfile.class)),timings);
        var actual=RootAdvanceRuntimeFacts.Settings.decode(exact(inputs.data(LIFE_SETTINGS)),
                new RawJson(RootRuntimeDefinitions.readData(new RootRuntimeDefinitionModel.DataPin(LIFE_SETTINGS,inputs.data(LIFE_SETTINGS)))));
        return new RootLifeRuntimeFactory.Prepared(new RootLifeRuntimeFactory.Sources(selected.javaSource(APPLICATION,LifeAdvanceComposite.class),
                selected.javaSource(APPLICATION,LifeAdvanceCommands.class),selected.javaSource(APPLICATION,AdvanceResult.class),
                selected.javaSource(APPLICATION,LifeAdvanceRootReplay.class)),actual,infrastructure);
    }
    private static EventRuntimeInstaller.Prepared events(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals)throws IOException {
        var window=selected.javaSource(NATIVE_TRANSPORT,EventWindowRead.class);
        return new EventRuntimeInstaller.Prepared(new EventRuntimeInstaller.Sources(selected.javaSource(LOCAL_SERVICE,EventRuntimeInstaller.class),
                window,window,selected.javaSource(NATIVE_TRANSPORT,EventWindowService.class),selected.javaSource(NATIVE_TRANSPORT,PlayerReligionContextRead.class),
                new PlayerReligionContextRead.Sources(originals.source(RootRuntimeNativeOriginals.Role.RELIGION_PRODUCER),
                        originals.source(RootRuntimeNativeOriginals.Role.RELIGION_MAILBOX),originals.source(RootRuntimeNativeOriginals.Role.RELIGION_CONTEXT)),
                selected.javaSource(APPLICATION,EventPolicies.class),selected.javaSource(APPLICATION,RegisteredEventCore.class),
                selected.javaSource(APPLICATION,NativeEventEffects.class),selected.javaSource(APPLICATION,NativeEventPostconditionPort.class),
                selected.javaSource(LOCAL_SERVICE,EventActionPreparation.class),selected.javaSource(LOCAL_SERVICE,RootPendingInteractionEffects.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsMaterialQuery.class),selected.javaSource(LOCAL_SERVICE,RootMandatoryChoiceRuntime.class)),inputs.eventSources());
    }
    private static RootCampaignPoliciesFactory.Prepared campaign(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected)throws IOException {
        return new RootCampaignPoliciesFactory.Prepared(new RootCampaignPoliciesFactory.Sources(
                selected.javaSource(LOCAL_SERVICE,RootCampaignPoliciesFactory.class),selected.javaSource(APPLICATION,M7CampaignPolicies.class),
                new RootCampaignPoliciesFactory.BoundDeadline(exact(inputs.data(CAMPAIGN_DEADLINE)),
                        RootRuntimeDefinitions.readData(new RootRuntimeDefinitionModel.DataPin(CAMPAIGN_DEADLINE,inputs.data(CAMPAIGN_DEADLINE))))));
    }
    private static RootAubRuntimeFactory.Prepared aub(RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals)throws IOException {
        var closure=new ArrayList<ExactRef>();
        for(var role:RootRuntimeNativeOriginals.Role.values())if(role.name().startsWith("AUB_")||role==RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER)
            closure.add(originals.source(role));
        closure.add(selected.javaSource(NATIVE_TRANSPORT,AubBusinessStateRead.class));closure.add(selected.javaSource(NATIVE_TRANSPORT,AubPublicCodec.class));
        closure.add(selected.javaTarget("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/aub/AubNativeStamp.java"));
        var runtime=selected.javaSource(LOCAL_SERVICE,RootAubRuntimeFactory.class);closure.add(runtime);
        var nativeSources=new AubOperations.Sources(originals.source(RootRuntimeNativeOriginals.Role.AUB_BUSINESS),
                originals.source(RootRuntimeNativeOriginals.Role.AUB_POLICY_MAILBOX),selected.javaSource(NATIVE_TRANSPORT,AubOperations.class));
        return new RootAubRuntimeFactory.Prepared(new RootAubRuntimeFactory.Sources(nativeSources,runtime,closure.stream().distinct().toList()));
    }
    static ExactRef exact(FileRef source){return new ExactRef(source.path(),source.bytes(),source.sha256());}
}
