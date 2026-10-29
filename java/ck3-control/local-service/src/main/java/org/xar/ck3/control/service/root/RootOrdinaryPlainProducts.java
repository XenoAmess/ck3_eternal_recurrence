package org.xar.ck3.control.service.root;
import org.xar.ck3.control.application.planning.military.ActiveCombatDateGuards;
import org.xar.ck3.control.application.planning.military.ActiveCombatGuardProducers;
import org.xar.ck3.control.application.planning.military.ActiveCombatObservedComparison;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityReadCodec;
import org.xar.ck3.control.application.advance.AdvanceClock;
import org.xar.ck3.control.application.advance.AdvanceClockArchivedReplay;
import org.xar.ck3.control.application.advance.AdvancePrimitiveArchivedReplay;
import org.xar.ck3.control.application.advance.AdvancePrimitiveEvidence;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.AdvanceResult;
import org.xar.ck3.control.application.advance.AdvanceWait;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollection;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationCollectionCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentDataProjection;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsAssaultInstaller;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsBaselinePublicRules;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsDetachment;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsDriverResult;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsExistingFamilies;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsInstallation;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsLossAllocation;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsManagers;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMaterialQuery;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMonthly;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsMovement;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsNativeFields;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsPhases;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsRefill;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsStages;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsSupply;
import org.xar.ck3.control.wave2.military.zerostockclock.ArmyUpdateClockCodec;
import org.xar.ck3.control.application.planning.military.AssaultLifecycle;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceArchive;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceArchivedReplay;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceComposite;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceFrame;
import org.xar.ck3.control.application.battleadvance.BattleAdvancePlan;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceResultCodec;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceStep;
import org.xar.ck3.control.application.planning.military.BattleControlPrelude;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.application.planning.finance.ConstructionDomainLifecycle;
import org.xar.ck3.control.application.planning.finance.ConstructionSnapshotVerifier;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeReads;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.application.action.council.CouncilContinuationCoordinator;
import org.xar.ck3.control.nativebridge.capabilities.governance.CouncilContinuationPolicy;
import org.xar.ck3.control.application.action.council.CouncilContinuationPorts;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTermsCodec;
import org.xar.ck3.control.application.planning.governance.CrownRetryDue;
import org.xar.ck3.control.application.planning.governance.CrownRetryPublication;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CurrentSupplyDispatchCodec;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservationCodec;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.application.history.DriverHistoryImport;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.planning.military.EarlyWarCoreLeaves;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowService;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesEffects;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionBindings;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionPreparation;
import org.xar.ck3.control.application.planning.governance.GovernanceCadencePublication;
import org.xar.ck3.control.application.planning.governance.GovernanceDomainDocument;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads;
import org.xar.ck3.control.application.planning.governance.GovernancePolicies;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiReads;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPolicy;
import org.xar.ck3.control.application.planning.military.LateWarCoreFallback;
import org.xar.ck3.control.application.planning.military.LateWarCoreLeaves;
import org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy;
import org.xar.ck3.control.application.advance.LifeAdvanceCommands;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleReducer;
import org.xar.ck3.control.application.planning.military.M5PeacetimePolicy;
import org.xar.ck3.control.application.planning.military.M5WartimeObservationPolicy;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.application.effects.NativeConstructionEffects;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.application.effects.NativeFeastEffects;
import org.xar.ck3.control.application.effects.NativeGovernanceEffects;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.application.effects.NativePrisonerEffects12004;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.finance.OrdinaryConstructionCollector;
import org.xar.ck3.control.application.planning.finance.OrdinaryConstructionPolicy;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.governance.OrdinaryFeastPolicy;
import org.xar.ck3.control.application.planning.prisoners.OrdinaryPrisonerPolicies12004;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.application.planning.warentry.PeacetimeWarEntryPlanner;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContextRead;
import org.xar.ck3.control.application.planning.warentry.PrewarBattlePrior;
import org.xar.ck3.control.application.planning.prisoners.PrisonerActionBinding12004;
import org.xar.ck3.control.application.planning.prisoners.PrisonerEpisodeLedger12004;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.g2.m6.prisonerransom.PrisonerRansomFormalPolicy12004;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerTerminalQueries;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory;
import org.xar.ck3.control.application.planning.events.RegisteredEventCore;
import org.xar.ck3.control.application.effects.RootCouncilContinuationGuard;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.routecontact.RouteContactArchivedFrames;
import org.xar.ck3.control.application.routecontact.RouteContactArchivedHistory;
import org.xar.ck3.control.application.routecontact.RouteContactArchivedVerifier;
import org.xar.ck3.control.application.routecontact.RouteContactCodec;
import org.xar.ck3.control.application.routecontact.RouteContactComposite;
import org.xar.ck3.control.application.routecontact.RouteContactEvidenceArchive;
import org.xar.ck3.control.application.routecontact.RouteContactEvidenceCodec;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.application.routecontact.RouteContactModel;
import org.xar.ck3.control.application.routecontact.RouteContactPostconditions;
import org.xar.ck3.control.application.routecontact.RouteContactProofs;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.application.planning.military.RouteOriginExposurePolicy;
import org.xar.ck3.control.application.routecontact.SharedRouteContactArchivedClocks;
import org.xar.ck3.control.application.routecontact.SharedRouteContactClocks;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.application.planning.prisoners.SuccessionOrdinaryPolicy12004;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.application.planning.military.WarBattleControlCore;
import org.xar.ck3.control.application.planning.military.WarContactPolicy;
import org.xar.ck3.control.application.planning.warentry.WarEntryCandidates;
import org.xar.ck3.control.application.planning.warentry.WarEntryCollector;
import org.xar.ck3.control.application.planning.warentry.WarEntryForceAdmission;
import org.xar.ck3.control.application.planning.warexit.WarExitPolicies;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.application.planning.military.WarSiegeDaily;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.util.*;
import java.util.stream.Collectors;


/** Ordinary business configuration to the same concrete installed products. */
public final class RootOrdinaryPlainProducts {
    private RootOrdinaryPlainProducts() { }

    public static RootRuntimeSourceProducts.PlainPrepared prepare(
            RootOrdinaryRuntimeConfiguration config, RootApplicationConfiguration app,
            RootRuntimeSourceProducts.OrdinaryRuntimePorts ports, InitialEpisodePolicy policy,
            NativeLaunchPlan samePlan) throws IOException {
        return new Builder(config,app,ports,policy,samePlan).prepare();
    }

    private static final class Builder {
        private final RootOrdinaryRuntimeConfiguration config;
        private final RootApplicationConfiguration app;
        private final RootRuntimeSourceProducts.OrdinaryRuntimePorts ports;
        private final InitialEpisodePolicy policy;
        private final NativeLaunchPlan samePlan;
        private final RootAdditionalDomains.ImplementationMetadata metadata;
        private final RootOrdinaryImplementationMetadata fileMetadata;
        private final ExactRef nativeDll;
        private final ExactRef wholeConfig;
        private final DynamicCapabilities.Configuration capabilities;

        private Builder(RootOrdinaryRuntimeConfiguration config,RootApplicationConfiguration app,
                RootRuntimeSourceProducts.OrdinaryRuntimePorts ports,InitialEpisodePolicy policy,
                NativeLaunchPlan samePlan)throws IOException {
            this.config=Objects.requireNonNull(config);this.app=Objects.requireNonNull(app);
            this.ports=Objects.requireNonNull(ports);this.policy=Objects.requireNonNull(policy);
            this.samePlan=Objects.requireNonNull(samePlan);metadata=ports.metadata();
            fileMetadata=metadata instanceof RootOrdinaryImplementationMetadata actual?actual:new RootOrdinaryImplementationMetadata();
            nativeDll=file(config.nativeImplementation());wholeConfig=file(config.configurationFile());
            capabilities=new DynamicCapabilities.Configuration(Optional.of(config.stateDirectory()),
                    Optional.of(samePlan.profileDirectory().resolve("save games")),3,3,false,false);
        }
        private ExactRef m(Class<?> actualClass){return metadata.implementation(actualClass);}
        private List<ExactRef> refs(Class<?>... actualClasses){
            return Arrays.stream(actualClasses).map(this::m).distinct().toList();
        }
        private ExactRef file(Path actual)throws IOException{return fileMetadata.file(actual);}
        private ExactRef warEntryMetadata(String className)throws IOException{
            try{
                Class<?> c=Class.forName("org.xar.ck3.control.application.planning.warentry."+className,false,PeacetimeWarEntryPlanner.class.getClassLoader());
                return metadata.implementation(c);
            }catch(ClassNotFoundException e){throw new IOException(e);}
        }
        private RootRuntimeSourceProducts.PlainPrepared prepare()throws IOException {
            var armies=RootOrdinaryArmySourcesFactory.army(config,ports,metadata,nativeDll);
            var prisoners=prisoners();
            var eventContext=new EventSourceReadContext(config.machineId(),config.stateDirectory(),config.stockGameRoot());
            Path incidentInputs=config.stateDirectory().resolve("incidents/inputs");
            Path incidentScan=config.stateDirectory().resolve("incidents/scan");
            var incidentSettings=new EpisodeIncidentJournal.Configuration(incidentInputs,incidentScan,ports.clock(),
                    ports.storage().incidentGuard(List.of(incidentInputs,incidentScan)),
                    Optional.of(TrustedEventSourceContext.open(eventContext)));
            var configuration=new RootRuntimeSourceProducts.PlainConfiguration(
                    governance(),RootOrdinaryFinanceSourcesFactory.sources(config,metadata,nativeDll),armies,
                    RootOrdinaryArmySourcesFactory.military(config,ports,metadata,nativeDll),
                    new RootSaveRuntime.Sources(m(RootSaveRuntime.class),m(CheckpointService.class),m(CanonicalSaveReceiptVerifier.class)),
                    new RootAubRuntimeFactory.Sources(new AubOperations.Sources(nativeDll,nativeDll,m(AubOperations.class)),
                            m(RootAubRuntimeFactory.class),List.of(nativeDll,m(AubOperations.class),m(RootAubRuntimeFactory.class))),
                    new RootContactRuntime.Sources(m(ContactScopeReads.class),m(ContactScopeReads.class)),
                    RootOrdinaryFamilySourcesFactory.configuration(config,app,ports,metadata),
                    RootOrdinaryFamilySourcesFactory.sources(config,app,ports,metadata,nativeDll),
                    domains(),additional(),construction(),prisoners,prisoners.domainClosure().stream().distinct().toList(),
                    activity(),frontend(),interactions(),
                    RootRuntimeSourceProducts.requiredReadHistorySources().stream().map(row->m(row.type())).distinct().toList(),
                    crossRun(),incidentSettings,m(EpisodeIncidentJournal.class),List.of(),128);
            return RootRuntimeSourceProducts.prepareOrdinary(configuration,ports);
        }

        private RootRuntimeSourceProducts.GovernanceConfiguration governance() {
            var natives=new GovernanceActionBindings.Sources(nativeDll,nativeDll,nativeDll);
            var continuation=refs(CouncilContinuationCoordinator.class,CouncilContinuationPolicy.class,
                    CouncilContinuationPorts.class,RootCouncilContinuationSeeds.class,RootCouncilContinuationGuard.class,
                    CouncilActionCodec.class,GovernanceRuntimeInstaller.class);
            var nativeSources=new GovernanceRuntimeInstaller.Sources(natives,m(GovernancePlanningReads.class),
                    m(CouncilActionCodec.class),m(GovernanceActionPreparation.class),m(NativeGovernanceEffects.class),
                    m(NativeGovernanceEffects.class),nativeDll,m(CrownFinalTermsCodec.class),continuation,
                    Optional.of(m(RootDriverGovernancePublicService.class)));
            var nativeConfig=new GovernanceRuntimeInstaller.Config(config.configuredBuild().version(),
                    config.configuredBuild().sha256(),config.authorityId(),
                    GovernanceActionPreparation.OPERATIONS.stream().map(OperationKey::new).collect(Collectors.toUnmodifiableSet()),64,64);
            var ordinary=new GovernanceOrdinaryRuntimeInstaller.Sources(m(GovernancePolicies.class),
                    m(OrdinaryFeastPolicy.class),m(NativeFeastEffects.class),m(ActivityActionRoutes.class),
                    refs(GovernanceOpeningRuntime.class,OpeningTransitions.class),
                    refs(GovernanceCadenceActions.class,GovernanceCadencePublication.class,GovernanceNextInitialization.class),
                    m(OpeningTransitions.class),
                    new FeastDomainRuntime.Sources(m(FeastDomainRuntime.class),
                            refs(FeastDomainRuntime.class,OrdinaryFeastPolicy.class,NativeFeastEffects.class)));
            var retryRuntimeSources=refs(RootCrownRetryRuntime.class,CrownRetryPublication.class,CrownRetryDue.class,RootCrownActualMaterialPort.class);
            var sharedProducerSources=refs(RootCrownRetryRuntime.class,CrownRetryPublication.class,CrownRetryDue.class,RootCrownActualMaterialPort.class,RootGovernanceDomains.class,CrownAuthorityCodec.class,GovernanceDomainDocument.class);
            var retry=new RootCrownRetryRuntime.Sources(m(RootCrownRetryRuntime.class),retryRuntimeSources,sharedProducerSources);
            var domains=new RootGovernanceDomains.Sources(m(RootGovernanceDomains.class),
                    refs(RootGovernanceDomains.class,CouncilActionCodec.class,GovernanceDomainDocument.class),
                    sharedProducerSources);
            return new RootRuntimeSourceProducts.GovernanceConfiguration(app.ledger().lock(),nativeSources,nativeConfig,ordinary,retry,domains);
        }
        private ConstructionRuntimeInstaller.Sources construction() {
            var policy=m(OrdinaryConstructionPolicy.class);var collector=m(OrdinaryConstructionCollector.class);
            var action=m(NativeConstructionEffects.class);var observer=m(NativeConstructionEffects.class);
            var replay=m(NativeConstructionEffects.class);var lifecycle=m(ConstructionDomainLifecycle.class);
            var snapshot=m(ConstructionSnapshotVerifier.class);var originals=m(RootConstructionDomainOriginals.class);
            var closure=List.of(policy,collector,action,observer,replay,lifecycle,snapshot,originals).stream().distinct().toList();
            return new ConstructionRuntimeInstaller.Sources(policy,collector,action,observer,replay,lifecycle,snapshot,originals,
                    ConstructionDomainLifecycle.prepare(closure,observer));
        }
        private RaiktorActualRecommendationFactory.Configuration formalWarConfiguration()throws IOException {
            ExactRef budget=file(config.formalWarBudget()),model=file(config.formalWarModel());
            return RaiktorActualRecommendationFactory.loadConfiguration(new RaiktorActualRecommendationFactory.ConfigurationSources(
                    new RaiktorActualRecommendationFactory.FileRef(Path.of(budget.path()),budget.bytes(),budget.sha256()),
                    new RaiktorActualRecommendationFactory.FileRef(Path.of(model.path()),model.bytes(),model.sha256()),
                    Optional.empty(),Optional.empty()));
        }
        private RootRuntimeSourceProducts.ActivityConfiguration activity() {
            var reads=Arrays.stream(ActivityNativeContracts.Query.values())
                    .map(query->new ActivityNativeContracts.Source(query,nativeDll)).toList();
            var actions=Arrays.stream(ActivityActionRoutes.Kind.values())
                    .map(kind->new ActivityActionRoutes.Source(kind,nativeDll,ports.core()::qualifyPrivate)).toList();
            return new RootRuntimeSourceProducts.ActivityConfiguration(reads,actions,ports.core()::verifyActivityRead,
                    ports.core()::verifyActivityAction,new RootRuntimeDefinitionModel.Build(config.configuredBuild().version(),
                    config.configuredBuild().sha256()),m(ActivityReadCodec.class));
        }
        private RootRuntimeSourceProducts.FrontendConfiguration frontend() {
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.empty(),
                    CapabilitySessionPresentation.BindingState.UNBOUND,Optional.empty(),Optional.empty(),
                    Optional.of(config.stateDirectory().resolve("queue")),
                    Optional.of(config.stateDirectory().resolve("driver/checkpoint.json")));
            return new RootRuntimeSourceProducts.FrontendConfiguration(config.configuredBuild(),nativeDll,
                    m(FrontendRulesEffects.class),m(FrontendRulesData.class),policy,capabilities,presentation,
                    config.freshness(),config.heartbeatMaximumAge(),config.retainedFrames(),config.retainedOrigins(),config.authorityId());
        }
        private RootAdditionalDomains.Config additional() {
            var gui=new RootGuiPublicProducts.Config(new GuiReads.Sources(nativeDll,nativeDll,nativeDll,
                    nativeDll,nativeDll,nativeDll,nativeDll),List.of(nativeDll));
            var gov=new RootRuntimeDefinitionModel.GovInputs(new RootRuntimeDefinitionModel.Build(config.configuredBuild().version(),
                    config.configuredBuild().sha256()),config.authorityId(),List.copyOf(GovernanceActionPreparation.OPERATIONS),64,64);
            var nativeSources=new RootDriverProductSourcesFactory.NativeSources(nativeDll,nativeDll,nativeDll,nativeDll,List.of(nativeDll));
            var driver=new RootDriverProductSourcesFactory.PlainConfig(samePlan,gov,false,nativeSources,Optional.empty());
            return new RootAdditionalDomains.Config(gui,new RootReligionPublicProducts.Config(true,true),
                    new RootArtifactsPublicProducts.Config(new RootArtifactsPublicProducts.InventoryDeferred(
                            "No current native inventory digest has been observed")),driver);
        }
        private KnownInteractionsRuntimeInstaller.Sources interactions() {
            var definitions=new InteractionCapabilities.Sources(nativeDll,nativeDll,nativeDll,nativeDll,nativeDll,
                    nativeDll,nativeDll,nativeDll,nativeDll,nativeDll);
            var readPlan=new InteractionCapabilities.ReadPlan(List.of(),List.of(),List.of());
            var build=Arrays.stream(InteractionModels.Build.values()).filter(row->row.version().equals(config.configuredBuild().version())
                    &&row.sha256().equalsIgnoreCase(config.configuredBuild().sha256())).findFirst()
                    .orElseThrow(()->new IllegalArgumentException("unsupported configured interaction build"));
            return new KnownInteractionsRuntimeInstaller.Sources(definitions,readPlan,build,m(InteractionModels.class),
                    m(KnownPendingInteractionPolicy.class),m(KnownPendingInteractionEffects.class),m(KnownPendingInteractionEffects.class));
        }
        private PrisonersRuntimeInstaller.Sources prisoners()throws IOException {
            ExactRef stock=file(config.stockGameRoot().resolve("common/character_interactions/00_prison_interactions.txt"));
            return new PrisonersRuntimeInstaller.Sources(m(PrisonerNativeQueries.class),m(PrisonerNativeQueries.class),
                    nativeDll,m(PrisonerRansomFormalPolicy12004.class),nativeDll,m(PrisonerActionBinding12004.class),
                    m(NativePrisonerEffects12004.class),m(NativePrisonerEffects12004.class),m(NativePrisonerEffects12004.class),
                    m(OrdinaryPrisonerPolicies12004.class),m(SuccessionOrdinaryPolicy12004.class),stock,
                    m(PrisonersRuntimeDefinitions.class),m(PrisonerEpisodeLedger12004.class));
        }
        private RootCrossRunPlanning.Sources crossRun() {
            var roles=new EnumMap<RootCrossRunPlanning.ProducerRole,ExactRef>(RootCrossRunPlanning.ProducerRole.class);
            roles.put(RootCrossRunPlanning.ProducerRole.CORE_PRODUCER,m(RootCrossRunPlanning.class));
            roles.put(RootCrossRunPlanning.ProducerRole.DOMAIN,m(CrossRunPlanningDomain.class));
            roles.put(RootCrossRunPlanning.ProducerRole.STRATEGY_SOURCE,m(CrossRunStrategySource.class));
            roles.put(RootCrossRunPlanning.ProducerRole.STRATEGY_REDUCER,m(CrossRunPlanning.class));
            roles.put(RootCrossRunPlanning.ProducerRole.LIFECYCLE_REDUCER,m(LifecycleReducer.class));
            roles.put(RootCrossRunPlanning.ProducerRole.TERMINAL_JOIN,m(TerminalLifecycleDecisionProducer.class));
            return new RootCrossRunPlanning.Sources(ports.files(),config.stateDirectory().resolve("strategy/one-life-history.json"),roles);
        }
        private RootRuntimeSourceProducts.OrdinaryDomainConfiguration domains() throws IOException {
            // 1. Life & Infrastructure
            var lifeSettings = RootAdvanceRuntimeFacts.Settings.ordinary(wholeConfig, true, true, true);
            var timings = RootAdvanceInfrastructureFactory.Timings.ordinary(wholeConfig, config.maximumFramesPerOperation(), config.operationTimeout(), config.operationTimeout());
            var life = new RootLifeRuntimeFactory.Sources(
                m(LifeAdvanceComposite.class),
                m(LifeAdvanceCommands.class),
                m(AdvanceResult.class),
                m(LifeAdvanceRootReplay.class)
            );
            var infrastructure = new RootAdvanceInfrastructureFactory.Sources(
                m(AdvancePrimitives.class),
                m(AdvancePrimitives.class),
                m(AdvancePrimitiveArchivedReplay.class),
                nativeDll,
                m(ClockStatusRead.class),
                m(RootUnknownSentinelReadProfile.class)
            );
        
            // 2. Strengths
            var nativeFields = new ArmyStrengthsNativeFields.Sources(
                m(ArmyStrengthsNativeFields.class),
                m(CurrentMovementCodec.class),
                m(ArmyUpdateClockCodec.class)
            );
            var existing = new ArmyStrengthsExistingFamilies.Sources(
                m(MonthlyLossCodec.class),
                m(ArmyDailyQueueInputsCodec.class),
                m(CountyEntryCodec.class),
                m(SourceNextFrameCodec.class),
                m(FleetSupplyCodec.class),
                m(CurrentSupplyDispatchCodec.class),
                m(FutureDailySupplyScheduleCodec.class),
                m(CombatRolesCodec.class)
            );
            var normalization = new ArmyStrengthsInstallation.Sources(
                nativeFields,
                existing,
                m(ArmyStrengthsStages.class),
                m(ArmyStrengthsBaselinePublicRules.class),
                m(ArmyStrengthsRefill.class),
                m(ArmyStrengthsAssaultInstaller.class),
                m(ArmyStrengthsPhases.class),
                m(ArmyStrengthsSupply.class),
                m(ArmyStrengthsMonthly.class),
                m(ArmyStrengthsMovement.class),
                m(ArmyStrengthsManagers.class),
                m(ArmyStrengthsDetachment.class),
                m(ArmyDetachmentDataProjection.class),
                m(ArmyStrengthsLossAllocation.class)
            );
            var strengths = new RootArmyStrengthsRuntimeFactory.Sources(
                normalization,
                nativeDll,
                m(ArmyStrengthsCodec.class),
                m(ArmyStrengthsDriverResult.class),
                m(DriverReadHistoryRichMaterial.class),
                m(ArmyQueryHistoryStore.class),
                m(ArmyQueryHistoryReference.class),
                m(OriginalDriverQueryHistorySettings.class)
            );
            var strengthSettings = new RootArmyStrengthsRuntimeFactory.Configuration(config.operationTimeout());
        
            // 3. Query History
            var queryHistory = OriginalDriverQueryHistorySettings.ordinary(
                new OriginalDriverQueryHistorySettings.JavaConfigured(
                    new OriginalDriverQueryHistorySettings.Directory(config.stateDirectory()),
                    33554432L,
                    OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE
                ),
                wholeConfig,
                m(OriginalDriverQueryHistorySettings.class)
            );
        
            // 4. Events
            var eventSources = new EventSourceReadContext(config.machineId(), config.stateDirectory(), config.stockGameRoot());
            var events = new EventRuntimeInstaller.Sources(
                m(EventRuntimeInstaller.class),
                m(EventWindowRead.class),
                m(EventWindowRead.class),
                m(EventWindowService.class),
                m(PlayerReligionContextRead.class),
                new PlayerReligionContextRead.Sources(
                    nativeDll,
                    nativeDll,
                    nativeDll
                ),
                m(EventPolicies.class),
                m(RegisteredEventCore.class),
                m(NativeEventEffects.class),
                m(NativeEventPostconditionPort.class),
                m(EventActionPreparation.class),
                m(RootPendingInteractionEffects.class),
                m(ArmyStrengthsMaterialQuery.class),
                m(RootMandatoryChoiceRuntime.class)
            );
        
            // 5. Lifecycle
            var lifecycleProducers = new ArrayList<>(refs(
                RootNaturalSuccessionOriginals.class,
                RootNaturalTimeline.class,
                RootLifecycleRuntimeFactory.class,
                LifecycleComposites.class,
                LifecycleProofCodec.class,
                PrisonerNativeQueries.class,
                PrisonerTerminalQueries.class
            ));
            lifecycleProducers.add(nativeDll);
            var lifecycle = new RootLifecycleRuntimeFactory.Sources(
                lifecycleProducers.stream().distinct().toList(),
                nativeDll,
                nativeDll,
                m(PrisonerNativeQueries.class),
                m(RootNaturalSuccessionOriginals.class),
                m(RootNaturalTimeline.class),
                m(PrisonerTerminalQueries.class),
                m(LifecycleComposites.class),
                m(LifecycleComposites.class)
            );
            var lifecycleSettings = new RootLifecycleRuntimeFactory.Configuration(
                config.stateDirectory(),
                samePlan.profileDirectory().resolve("save games"),
                samePlan.profileDirectory().resolve("save games/tutorial"),
                samePlan.evidenceRoot(),
                Set.of(LifeAdvanceComposite.HANDLER),
                config.operationTimeout()
            );
        
            // 6. Campaign & Policies
            var campaignDeadline = new RootCampaignPoliciesFactory.BoundDeadline(file(config.campaignDeadlineFile()), Files.readAllBytes(config.campaignDeadlineFile()));
            var campaign = new RootCampaignPoliciesFactory.Sources(
                m(RootCampaignPoliciesFactory.class),
                m(M7CampaignPolicies.class),
                campaignDeadline
            );
            var holy = new RootHolyWarPlanningPolicies.Sources(
                m(RootHolyWarPlanningPolicies.class)
            );
            var successionPolicies = m(RootSuccessionPlanningPolicies.class);
        
            // 7. War & Entry
            var war = new RootWarCoreFactory.Sources(
                m(RootWarCoreFactory.class),
                new EarlyWarCoreLeaves.Sources(
                    m(EarlyWarCoreLeaves.class),
                    m(WarContactPolicy.class),
                    m(WarSiegeDaily.class)
                ),
                m(WarBattleControlCore.class),
                m(BattleControlPrelude.class),
                m(AssaultLifecycle.class),
                m(LateWarCoreLeaves.class),
                m(LateWarCoreFallback.class),
                m(LegacyWarExitPolicy.class),
                m(WarExitPolicies.class),
                m(WarExitReads.class)
            );
            var warEntry = new RootPeacetimeWarEntryRuntime.Sources(
                m(RootPeacetimeWarEntryRuntime.class),
                m(PeacetimeWarEntryPlanner.class),
                m(WarEntryCollector.class),
                m(WarEntryCandidates.class),
                m(WarEntryForceAdmission.class),
                m(PrewarBattlePrior.class),
                warEntryMetadata("WarEntryHistoryAdvance"),
                warEntryMetadata("WarEntryJson"),
                m(ArmyDeclarationCollection.class),
                m(ArmyDeclarationCollectionCodec.class)
            );
        
            // 8. Route Advance
            var routeReaders = new ArrayList<ExactRef>();
            for (Class<?> type : List.of(
                RouteContactComposite.class, RouteContactSteps.class, RouteContactProofs.class, RouteContactModel.class,
                RouteContactCodec.class, RouteContactPostconditions.class, RouteContactEvidenceCodec.class, RouteContactEvidenceArchive.class,
                RouteContactArchivedVerifier.class, RouteContactArchivedFrames.class, RouteContactArchivedHistory.class, SharedRouteContactClocks.class,
                SharedRouteContactArchivedClocks.class, DriverHistoryAccess.class, RouteContactHistoryAdapter.class, DriverSurvivingHistory.class,
                DriverHistoryImport.class, BattleAdvanceComposite.class, BattleAdvanceArchive.class, BattleAdvanceResultCodec.class, BattleAdvanceArchivedReplay.class,
                BattleAdvancePlan.class, BattleAdvanceFrame.class, BattleAdvanceStep.class, AdvanceClock.class, AdvanceWait.class, AdvanceResult.class,
                AdvanceClockArchivedReplay.class, LifeAdvanceRootReplay.class, NativeEffectEvidence.class, RootGuardEvidence.class, DriverObservationEvidenceReader.class,
                DynamicCapabilities.class, AdvancePrimitiveEvidence.class, RootRouteContactAdvanceRuntime.class, RootRouteContactAdvanceResult.class,
                RootRouteContactAdvancePublicProducts.class, RootRuntimeDomainAssembly.class, RootPublicStepExecution.class, RootPublicStepFailureOriginals.class,
                RootLifeAdvancePublicResult.class, RootBattleAdvancePublicResult.class, RootAdvanceInfrastructureFactory.class, RootLifeRuntimeFactory.class,
                RootRouteContactAdvanceSourcesFactory.class
            )) {
                routeReaders.add(m(type));
            }
            var routeAdvance = new RootRouteContactAdvanceRuntime.Sources(
                m(RouteContactComposite.class),
                m(RouteContactEvidenceCodec.class),
                m(RouteContactArchivedVerifier.class),
                routeReaders.stream().distinct().toList()
            );
            var routeSettings = RootRouteContactAdvanceRuntime.Configuration.ordinary(wholeConfig, capabilities, campaignDeadline);
        
            // 9. Military & Peacetime
            var activeCombat = new RootActiveCombatDateGuardFactory.Sources(
                m(ActiveCombatDateGuards.class),m(ActiveCombatGuardProducers.class),m(ActiveCombatObservedComparison.class),m(DefenderExitObservationCodec.class)
            );
            var militaryPolicies = new OrdinaryMilitaryInstaller.PolicySources(
                m(RouteOriginExposurePolicy.class),m(M5PeacetimePolicy.class),m(M5WartimeObservationPolicy.class)
            );
            var policies = new RootRuntimeDomainAssembly.PolicySources(
                m(OrdinaryCorePolicy.class),m(WarExitPolicies.class)
            );
            var formalWar = formalWarConfiguration();
            var peacetime = new M5PeacetimePolicy.Options(true, true, true);
            var physicalFreshness = config.freshness();
        
            // 10. Action History
            var actionHistory = RootActionHistorySourcesFactory.ordinary(Map.of(), metadata);
        
            return new RootRuntimeSourceProducts.OrdinaryDomainConfiguration(
                life, lifeSettings,
                infrastructure, timings,
                strengths, strengthSettings,
                queryHistory, events, eventSources,
                lifecycle, lifecycleSettings,
                campaign, holy, activeCombat, successionPolicies,
                war, warEntry, policies, militaryPolicies,
                formalWar, peacetime, physicalFreshness,
                actionHistory, routeAdvance, routeSettings
            );
        }
    }
}

