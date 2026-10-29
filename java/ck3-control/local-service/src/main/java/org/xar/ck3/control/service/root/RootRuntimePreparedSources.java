package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.NATIVE_GOV_CONTINUATION;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.OPENING_PRODUCERS;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.CADENCE_PRODUCERS;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.FEAST_STATE;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.CONSTRUCTION_DOMAIN;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.ClosureRole.PRISONER_DOMAIN;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SourceRole.*;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.Objects;
import java.util.stream.Collectors;
import org.xar.ck3.control.application.planning.finance.ConstructionDomainLifecycle;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatOrderService;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionBindings;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.application.planning.finance.CanonicalFinanceStateSource;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceFactory;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.continuity.writer.RollbackPair;
import org.xar.ck3.control.contracts.ExactRef;

/** Explicit source-role to concrete Java definitions. These constructors never grant live admission. */
public final class RootRuntimePreparedSources {
    private RootRuntimePreparedSources() { }
    public static RootAubRuntimeFactory.Prepared aub(AubOperations.Sources nativeSources,ExactRef preparationAndReplay,
            List<ExactRef> producerClosure) {
        Objects.requireNonNull(nativeSources);Objects.requireNonNull(preparationAndReplay);Objects.requireNonNull(producerClosure);
        return new RootAubRuntimeFactory.Prepared(new RootAubRuntimeFactory.Sources(nativeSources,preparationAndReplay,producerClosure));
    }

    /** Absence explicitly disables this cold route; a prepared authority still requires the actual writer reducer. */
    public record Rollback(Optional<RootOriginalRollbackAuthority> authority,Optional<ExactRef> originalProof) {
        public Rollback {
            Objects.requireNonNull(authority);Objects.requireNonNull(originalProof);
            if(authority.isPresent()!=originalProof.isPresent())
                throw new IllegalArgumentException("original rollback authority and explicit proof must have identical presence");
        }
        public Optional<RollbackPair.Authority> writerAuthority(){return authority.map(actual->actual);}
    }

    public static Rollback rollback(RootRuntimeDefinitions.Inputs inputs,RootCoreBoundPorts ports,
            CheckpointFiles actualFiles,Clock clock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(ports);Objects.requireNonNull(actualFiles);Objects.requireNonNull(clock);
        var configured=inputs.optionalData(RootRuntimeDefinitionModel.DataRole.ROLLBACK_PROOF);
        if(configured.isEmpty())return new Rollback(Optional.empty(),Optional.empty());
        var reference=configured.orElseThrow();
        var proof=new ExactRef(reference.path(),reference.bytes(),reference.sha256());
        OriginalRollbackProof decoded=OriginalRollbackProof.decode(RootRuntimeDefinitions.read(reference,32768),
                inputs.application().machineId());
        var actual=RootOriginalRollbackAuthority.prepare(ports::requireWriter,actualFiles,proof,
                inputs.application().machineId(),decoded.runtimeRoot(),clock,Instant.parse(inputs.configuration().reviewAtUtc()));
        return new Rollback(Optional.of(actual),Optional.of(proof));
    }

    /** Called after the sole Core is bound, before native launch; commit still repeats the authority under its lock. */
    public static void preflightRollback(Rollback actual,RootCoreBoundPorts ports,RootApplicationAssembly.Core core)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(ports);Objects.requireNonNull(core);
        if(ports.requireCore()!=core||ports.requireWriter()!=core.writer()||core.archive().writer()!=core.writer())
            throw new IOException("rollback preflight requires the identical bound Core/writer/archive");
        if(actual.authority().isEmpty())return;
        core.writer().locked(same->{
            core.writer().requireSession(same);
            var before=same.head();
            var evidence=actual.authority().orElseThrow().revalidate(before,actual.originalProof().orElseThrow());
            // The same actual two-event reducer is run here and again by the writer's original commit path.
            RollbackPair.validate(RollbackPair.plan(before,evidence));
            if(!same.head().digest().equals(before.digest()))throw new IOException("read-only original rollback preflight changed the writer head");
            core.writer().requireSession(same);return null;
        });
    }

    public static GovernanceRuntimeInstaller.Prepared nativeGovernance(RootRuntimeDefinitions.Inputs inputs, RootRuntimeSelectedSources selected, Clock clock)throws IOException {
        Objects.requireNonNull(inputs); Objects.requireNonNull(clock);
        var settings = inputs.configuration().governance();
        var sources = new GovernanceRuntimeInstaller.Sources(
                new GovernanceActionBindings.Sources(inputs.source(NATIVE_GOV_LIFESTYLE),
                        inputs.source(NATIVE_GOV_COUNCIL), inputs.source(NATIVE_GOV_CROWN)),
                inputs.source(GOV_PLANNING_DECODER), inputs.source(GOV_COUNCIL_DECODER),
                inputs.source(GOV_ACTION_DECODER), inputs.source(GOV_EFFECT_VERIFIER),
                inputs.source(GOV_COUNCIL_EFFECT_VERIFIER), inputs.source(NATIVE_GOV_FINAL_TERMS),
                inputs.source(GOV_FINAL_TERMS_DECODER), inputs.closure(NATIVE_GOV_CONTINUATION),
                Optional.of(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootDriverGovernancePublicService.class)));
        var config = new GovernanceRuntimeInstaller.Config(settings.build().gameVersion(),
                settings.build().executableSha256(), settings.authorityId(),
                settings.admittedActions().stream().map(OperationKey::new).collect(Collectors.toUnmodifiableSet()),
                settings.maximumStatusPolls(), settings.maximumContinuations());
        return nativeGovernance(inputs.application().ledger().lock(),sources,config,clock);
    }

    /** Business composition also accepts the real domain inputs directly, without a Definitions reader. */
    public static GovernanceRuntimeInstaller.Prepared nativeGovernance(Path writerLock,
            GovernanceRuntimeInstaller.Sources sources,GovernanceRuntimeInstaller.Config configuration,
            Clock clock)throws IOException {
        return GovernanceRuntimeInstaller.prepare(Objects.requireNonNull(writerLock),Objects.requireNonNull(sources),
                Objects.requireNonNull(configuration),Objects.requireNonNull(clock));
    }

    public static GovernanceOrdinaryRuntimeInstaller.Prepared ordinaryGovernance(RootRuntimeDefinitions.Inputs inputs, Clock clock) {
        Objects.requireNonNull(inputs); Objects.requireNonNull(clock);
        var sources = new GovernanceOrdinaryRuntimeInstaller.Sources(inputs.source(ORDINARY_GOV_POLICY),
                inputs.source(ORDINARY_GOV_FEAST_POLICY), inputs.source(ORDINARY_GOV_FEAST_EFFECTS),
                inputs.source(ORDINARY_GOV_ACTIVITY_ACTION_DECODER), inputs.closure(OPENING_PRODUCERS),
                inputs.closure(CADENCE_PRODUCERS), inputs.source(ORDINARY_GOV_OPENING_TRANSITIONS),
                new FeastDomainRuntime.Sources(inputs.source(FEAST_STATE_IMPLEMENTATION), inputs.closure(FEAST_STATE)));
        return ordinaryGovernance(inputs.application().ledger().lock(),sources,clock);
    }

    public static GovernanceOrdinaryRuntimeInstaller.Prepared ordinaryGovernance(Path writerLock,
            GovernanceOrdinaryRuntimeInstaller.Sources sources,Clock clock) {
        return GovernanceOrdinaryRuntimeInstaller.prepare(Objects.requireNonNull(writerLock),
                Objects.requireNonNull(sources),Objects.requireNonNull(clock));
    }

    public static ConstructionRuntimeInstaller.Sources construction(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        var domain = ConstructionDomainLifecycle.prepare(inputs.closure(CONSTRUCTION_DOMAIN), inputs.source(CONSTRUCTION_OBSERVER));
        return new ConstructionRuntimeInstaller.Sources(inputs.source(CONSTRUCTION_POLICY),
                inputs.source(CONSTRUCTION_COLLECTOR), inputs.source(CONSTRUCTION_NATIVE_ACTION),
                inputs.source(CONSTRUCTION_OBSERVER), inputs.source(CONSTRUCTION_ARCHIVE_VERIFIER),
                inputs.source(CONSTRUCTION_LIFECYCLE), inputs.source(CONSTRUCTION_SNAPSHOT_VERIFIER),
                inputs.source(CONSTRUCTION_ORIGINALS), domain);
    }

    public static PrisonersRuntimeInstaller.Sources prisoners(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        return new PrisonersRuntimeInstaller.Sources(inputs.source(PRISONER_COLLECTION_PRODUCER),
                inputs.source(PRISONER_COLLECTION_DECODER), inputs.source(PRISONER_WAR_PRODUCER),
                inputs.source(PRISONER_WAR_DECODER), inputs.source(PRISONER_ACTION_PRODUCER),
                inputs.source(PRISONER_ACTION_PREPARATION), inputs.source(PRISONER_ACTION_OBSERVER),
                inputs.source(PRISONER_ACTION_DECODER), inputs.source(PRISONER_RECORDED_VERIFIER),
                inputs.source(PRISONER_ORDINARY_POLICIES), inputs.source(PRISONER_SUCCESSION_POLICIES),
                inputs.source(PRISONER_STOCK_INTERACTIONS), inputs.source(PRISONER_LEDGER_PRODUCER),inputs.source(PRISONER_EPISODE_LEDGER));
    }

    public static PrisonersRuntimeDefinitions prisonerDefinitions(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        if(!inputs.closure(PRISONER_DOMAIN).contains(inputs.source(PRISONER_EPISODE_LEDGER)))
            throw new IllegalArgumentException("prisoner definitions/domain must retain the identical mandatory episode-ledger producer");
        return new PrisonersRuntimeDefinitions(inputs.closure(PRISONER_DOMAIN));
    }

    /** The one Army source factory owns both installed contracts and ordinary/claim source facts. */
    public static RootArmySourcesFactory.Products army(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,RootPublicArmyActionIds sameActualIds,
            Optional<RootArmyStockReadRuntime.Configuration> stockRead)throws IOException {
        return RootArmySourcesFactory.prepare(Objects.requireNonNull(inputs),Objects.requireNonNull(selected),Objects.requireNonNull(originals),
                Objects.requireNonNull(sameActualIds),sameActualIds,Objects.requireNonNull(stockRead));
    }
    public static RootCrownRetryRuntime.Prepared crownRetry(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        return crownRetry(inputs.application().ledger().lock(),
                new RootCrownRetryRuntime.Sources(inputs.source(CROWN_RETRY_IMPLEMENTATION),
                        inputs.closure(RootRuntimeDefinitionModel.ClosureRole.CROWN_RETRY),
                        inputs.closure(RootRuntimeDefinitionModel.ClosureRole.CROWN_RETRY_PRODUCERS)));
    }

    public static RootCrownRetryRuntime.Prepared crownRetry(Path writerLock,RootCrownRetryRuntime.Sources sources) {
        return new RootCrownRetryRuntime.Prepared(Objects.requireNonNull(writerLock),Objects.requireNonNull(sources));
    }

    public static RootGovernanceDomains governanceDomains(RootRuntimeDefinitions.Inputs inputs,
            RootCrownRetryRuntime.Prepared retry) {
        Objects.requireNonNull(inputs); Objects.requireNonNull(retry);
        return governanceDomains(inputs.application().ledger().lock(),
                new RootGovernanceDomains.Sources(inputs.source(GOVERNANCE_DOMAINS_IMPLEMENTATION),
                        inputs.closure(RootRuntimeDefinitionModel.ClosureRole.COUNCIL_DOMAIN),
                        inputs.closure(RootRuntimeDefinitionModel.ClosureRole.CROWN_DOMAIN)),retry);
    }

    public static RootGovernanceDomains governanceDomains(Path writerLock,RootGovernanceDomains.Sources sources,
            RootCrownRetryRuntime.Prepared retry) {
        return new RootGovernanceDomains(Objects.requireNonNull(writerLock),Objects.requireNonNull(sources),
                Objects.requireNonNull(retry).pub());
    }

    public static GovernanceOrdinaryRuntimeInstaller.StateDomains governanceStates(
            RootGovernanceDomains civic, RootCrownRetryRuntime.Prepared retry) {
        Objects.requireNonNull(civic); Objects.requireNonNull(retry);
        return new GovernanceOrdinaryRuntimeInstaller.StateDomains(civic.councilBody(), civic.crownBody(),
                retry.pub(), retry.retainedProof(), civic, retry.due());
    }

    /** These are the identical producers shared by catalog registration and later domain installation. */
    public record Governance(GovernanceRuntimeInstaller.Prepared nativeGovernance,
            GovernanceOrdinaryRuntimeInstaller.Prepared ordinary,RootCrownRetryRuntime.Prepared retry,
            RootGovernanceDomains domains,GovernanceOrdinaryRuntimeInstaller.StateDomains states) {
        public Governance {
            Objects.requireNonNull(nativeGovernance);Objects.requireNonNull(ordinary);Objects.requireNonNull(retry);
            Objects.requireNonNull(domains);Objects.requireNonNull(states);
            if(states.retryPublication()!=retry.pub()||states.retryDue()!=retry.due()
                    ||domains.retryPublication()!=retry.pub())
                throw new IllegalArgumentException("one actual Crown retry producer must serve all ordinary domains");
        }
    }

    public static Governance governance(Path writerLock,GovernanceRuntimeInstaller.Sources nativeSources,
            GovernanceRuntimeInstaller.Config nativeConfiguration,GovernanceOrdinaryRuntimeInstaller.Sources ordinarySources,
            RootCrownRetryRuntime.Sources retrySources,RootGovernanceDomains.Sources domainSources,Clock clock)throws IOException {
        var nativeRuntime=nativeGovernance(writerLock,nativeSources,nativeConfiguration,clock);
        var ordinary=ordinaryGovernance(writerLock,ordinarySources,clock);
        var retry=crownRetry(writerLock,retrySources);
        var domains=governanceDomains(writerLock,domainSources,retry);
        return new Governance(nativeRuntime,ordinary,retry,domains,governanceStates(domains,retry));
    }

    public static RootCrossRunPlanning.Prepared crossRun(RootRuntimeDefinitions.Inputs inputs,
            org.xar.ck3.control.application.checkpoint.CheckpointFiles actualFiles) {
        Objects.requireNonNull(inputs); Objects.requireNonNull(actualFiles);
        return new RootCrossRunPlanning.Prepared(new RootCrossRunPlanning.Sources(actualFiles,
                java.nio.file.Path.of(inputs.configuration().crossRun().originalOneLifeHistory().path()),
                inputs.closure(RootRuntimeDefinitionModel.ClosureRole.CROSS_RUN)));
    }

    public record Finance(FinanceRuntimeInstaller.Prepared prepared,FinanceReadContracts.Registration root) {
        public Finance {Objects.requireNonNull(prepared);Objects.requireNonNull(root);}
    }
    /** Same actual ROOT Registration is retained for Sway; no parallel ReadContract or registration is constructed. */
    public static Finance finance(RootRuntimeDefinitions.Inputs inputs,
            List<CanonicalFinanceStateSource.Binding> actualExternalBodies) {
        Objects.requireNonNull(inputs);Objects.requireNonNull(actualExternalBodies);
        var configuration=inputs.configuration().finance();
        List<FinanceRuntimeInstaller.ReadSource> reads=configuration.reads().stream().map(row->
                new FinanceRuntimeInstaller.ReadSource(FinanceReadContracts.Query.valueOf(row.query().name()),
                        financeRead(row.definition().sourceRef(),row.permission()))).toList();
        var cold=new FinanceRuntimeInstaller.GiftColdSources(
                financeRead(configuration.giftColdDefinition().sourceRef(),configuration.giftColdPermission()),
                inputs.source(FINANCE_GIFT_COLD_READ_CODEC),inputs.source(FINANCE_GIFT_COLD_CLASSIFIER),
                inputs.source(FINANCE_GIFT_COLD_CLASSIFIER_CODEC),inputs.source(FINANCE_GIFT_COLD_PROVIDER),
                inputs.source(FINANCE_GIFT_PROCESS_IDENTITY));
        return finance(new FinanceRuntimeInstaller.Sources(
                new OrdinaryFinanceFactory.Sources(inputs.source(FINANCE_POLICY),inputs.source(FINANCE_MERCENARY_MATERIAL),
                        inputs.source(FINANCE_GIFT_MATERIAL),inputs.source(FINANCE_QUOTE_ARCHIVE)),
                inputs.source(FINANCE_READ_CODEC),inputs.source(FINANCE_HIRE_ACK_CODEC),inputs.source(FINANCE_DOMAIN),
                inputs.source(FINANCE_DOMAIN_REDUCER),inputs.source(FINANCE_WAR_PRIORITY),inputs.source(FINANCE_FACTION_DEFINITION),
                inputs.source(FINANCE_FACTION_CODEC),inputs.source(FINANCE_GIFT_DOMAIN),inputs.source(FINANCE_GIFT_BODY_CODEC),
                inputs.source(FINANCE_GIFT_BODY_REDUCER),reads,List.copyOf(actualExternalBodies),cold));
    }

    public static Finance finance(FinanceRuntimeInstaller.Sources sources) {
        Objects.requireNonNull(sources);
        var prepared=new FinanceRuntimeInstaller.Prepared(sources);
        var reads=sources.readSources();
        var root=reads.stream().filter(row->row.query()==FinanceReadContracts.Query.ROOT).toList();
        if(root.size()!=1)throw new IllegalArgumentException("one actual configured shared Finance ROOT registration required");
        return new Finance(prepared,root.getFirst().registration());
    }
    public static Finance finance(FinanceRuntimeInstaller.Sources configuration,
            List<CanonicalFinanceStateSource.Binding> actualExternalBodies) {
        Objects.requireNonNull(configuration);Objects.requireNonNull(actualExternalBodies);
        return finance(new FinanceRuntimeInstaller.Sources(configuration.finance(),configuration.readCodec(),configuration.hireAckCodec(),
                configuration.domainSource(),configuration.domainReducer(),configuration.warPriority(),configuration.factionDefinition(),
                configuration.factionCodec(),configuration.giftDomainSource(),configuration.giftBodyCodec(),configuration.giftBodyReducer(),
                configuration.readSources(),List.copyOf(actualExternalBodies),configuration.giftCold()));
    }

    private static FinanceReadContracts.Registration financeRead(org.xar.ck3.control.contracts.ExactRef definition,
            RootRuntimeDefinitionModel.ReadPermission permission) {
        return new FinanceReadContracts.Registration(definition,new FinanceReadContracts.Permission(
                Optional.ofNullable(permission.capability()),permission.permissionKey(),
                ReadContract.PermissionMode.valueOf(permission.mode().name()),
                ReadContract.WireProfile.valueOf(permission.wireProfile().name())));
    }

    public static RootSaveRuntime.Sources save(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        return new RootSaveRuntime.Sources(inputs.source(SAVE_PREPARATION),inputs.source(SAVE_POSTSTATE),
                inputs.source(SAVE_ARCHIVED_REPLAY));
    }

    public static RootRuntimeCatalogFactory.MilitarySources military(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,org.xar.ck3.control.platform.NativeLaunchPlan samePlan)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(samePlan);
        selected.requireInputs(inputs);samePlan.sources().verify();
        selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootMilitaryControlStepRuntime.class);
        var controls=RootMilitaryControlStepRuntime.prepare(inputs);
        // Generic returned-action history remains a retained startup dependency, outside structural Sources.
        selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryMaterial.class);
        selected.javaSource(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.history.DriverReturnedActionHistoryRowProducer.class);
        var structural=new RootArmyStructuralStepRuntime.Prepared(new RootArmyStructuralStepRuntime.Sources(
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActions.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralActionCodec.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.army.ArmyStructuralEffects.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArmyStructuralStepRuntime.class)),
                Duration.ofMillis(inputs.configuration().army().commandReadTimeoutMs()));
        var commander=new org.xar.ck3.control.application.planning.military.CommanderBindings.Sources(
                inputs.source(COMMANDER_READ_DEFINITION),inputs.source(COMMANDER_READ_DECODER),
                inputs.source(COMMANDER_ACTION_DEFINITION),inputs.source(COMMANDER_ACTION_DECODER),
                inputs.source(COMMANDER_ARCHIVED_VERIFIER),inputs.source(COMMANDER_RECONCILIATION_QUERY));
        var ordinary=new OrdinaryMilitaryInstaller.Sources(inputs.source(MILITARY_RETREAT_POLICY),
                inputs.source(MILITARY_COMMANDER_POLICY),inputs.source(MILITARY_RENDEZVOUS_POLICY),
                inputs.source(MILITARY_FORECAST_POLICY),commander,inputs.source(ARMY_FORECAST_READS),
                inputs.source(ARMY_FORECAST_DECODER),inputs.source(ARMY_PLANNING_READS),inputs.source(ARMY_PLANNING_DECODER),
                inputs.source(ARMY_WAR_READS),inputs.source(ARMY_WAR_DECODER));
        var additional=new ArmyAdditionalReadInstaller.Sources(inputs.source(ARMY_REINFORCEMENT_DEFINITION),
                inputs.source(ARMY_REINFORCEMENT_DECODER),inputs.source(ARMY_ADDITIONAL_SERVICE));
        var simulation=new org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec();
        var phases=new org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec(simulation,
                new org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime());
        var diagnostics=new RootArmyDeclarationDiagnostics.Sources(
                selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootArmyDeclarationDiagnostics.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,
                        org.xar.ck3.control.nativebridge.capabilities.army.ArmyDeclarationDiagnostics.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,
                        org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarReads.class));
        var publicPause=RootPublicPauseRuntime.prepare(inputs,selected);
        return new RootRuntimeCatalogFactory.MilitarySources(ordinary,additional,simulation,phases,diagnostics,
                Duration.ofMillis(inputs.configuration().publicCatalog().observationTimeoutMs()),controls,structural,publicPause);
    }

    public record MilitaryConfiguration(OrdinaryMilitaryInstaller.Sources ordinary,
            ArmyAdditionalReadInstaller.Sources additional,RootArmyDeclarationDiagnostics.Sources diagnostics,
            Duration publicReadTimeout,RootMilitaryControlStepRuntime.Sources controls,
            RootArmyStructuralStepRuntime.Sources structural,Duration commandTimeout,RootPublicPauseRuntime.Sources publicPause) {
        public MilitaryConfiguration {
            Objects.requireNonNull(ordinary);Objects.requireNonNull(additional);Objects.requireNonNull(diagnostics);
            Objects.requireNonNull(publicReadTimeout);Objects.requireNonNull(controls);Objects.requireNonNull(structural);
            Objects.requireNonNull(commandTimeout);Objects.requireNonNull(publicPause);
        }
    }

    /** Construct the original codecs and callable products directly from ordinary business configuration. */
    public static RootRuntimeCatalogFactory.MilitarySources military(MilitaryConfiguration configuration) {
        Objects.requireNonNull(configuration);
        var simulation=new org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec();
        var phases=new org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec(simulation,
                new org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime());
        return new RootRuntimeCatalogFactory.MilitarySources(configuration.ordinary(),configuration.additional(),simulation,phases,
                configuration.diagnostics(),configuration.publicReadTimeout(),RootMilitaryControlStepRuntime.prepare(configuration.controls()),
                new RootArmyStructuralStepRuntime.Prepared(configuration.structural(),configuration.commandTimeout()),
                RootPublicPauseRuntime.prepare(configuration.publicPause()));
    }

    public static KnownInteractionsRuntimeInstaller.Sources interactions(RootRuntimeDefinitions.Inputs inputs) {
        Objects.requireNonNull(inputs);
        var settings=inputs.configuration().interactions();
        InteractionModels.Build build=java.util.Arrays.stream(InteractionModels.Build.values()).filter(value->
                value.version().equals(settings.build().gameVersion())
                        &&value.sha256().equalsIgnoreCase(settings.build().executableSha256())).findFirst()
                .orElseThrow(()->new IllegalArgumentException("unknown exact interaction build"));
        var definitions=new InteractionCapabilities.Sources(inputs.source(INTERACTION_MARRIAGE),inputs.source(INTERACTION_LAWS),
                inputs.source(INTERACTION_CLAIMS),inputs.source(INTERACTION_HOLDER),inputs.source(INTERACTION_APPOINTMENT),
                inputs.source(INTERACTION_ORDINARY),inputs.source(INTERACTION_PLAYER_CONTROL),inputs.source(INTERACTION_GRANT),
                inputs.source(INTERACTION_PENDING),inputs.source(INTERACTION_HEIR));
        var plan=new InteractionCapabilities.ReadPlan(settings.lawTitles().stream().map(InteractionModels.FullId::new).toList(),
                settings.claimTitleSets().stream().map(group->group.stream().map(InteractionModels.Int32Id::new).toList()).toList(),
                settings.holderTitles().stream().map(InteractionModels.Int32Id::new).toList());
        return new KnownInteractionsRuntimeInstaller.Sources(definitions,plan,build,inputs.source(INTERACTION_READ_DECODER),
                inputs.source(INTERACTION_POLICY),inputs.source(INTERACTION_EFFECTS),inputs.source(INTERACTION_EFFECTS_DECODER));
    }

    public static RootFrontendRuntime.Sources frontend(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeStorageGuard storage,CheckpointFiles identicalFiles,org.xar.ck3.control.platform.NativeLaunchPlan retainedPlan,
            Clock actualClock)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(storage);Objects.requireNonNull(retainedPlan);
        storage.requireFilePort(identicalFiles);
        var settings=inputs.configuration().frontend();
        var policyRef=inputs.data(RootRuntimeDefinitionModel.DataRole.INITIAL_POLICY);
        var runRef=inputs.configuration().explicitFreshPactProfile();
        var frozen=RootFrozenRunProfile.readExact(new ExactRef(runRef.path(),runRef.bytes(),runRef.sha256()),retainedPlan,
                new ExactRef(policyRef.path(),policyRef.bytes(),policyRef.sha256()),actualClock);
        var policy=frozen.initialPolicy();
        var environment=inputs.data(RootRuntimeDefinitionModel.DataRole.INITIAL_PREPARED_ENVIRONMENT);
        if(!policy.environment().equals(new ExactRef(environment.path(),environment.bytes(),environment.sha256())))
            throw new IOException("actual frozen initial policy differs from the explicitly configured prepared environment");
        var journal=new RootOriginalDriverJournal.Prepared(identicalFiles,storage,retainedPlan,frozen,actualClock);
        var diagnostics=new RootFrontendStartQueryDiagnostics.Prepared(new RootFrontendStartQueryDiagnostics.Sources(
                selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootFrontendStartQueryDiagnostics.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,
                        org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendStartRootQueries.class),
                inputs.source(FRONTEND_START_EFFECTS)),storage);
        var configuration=DynamicCapabilities.decodeConfiguration(DriverJson.object(
                RootRuntimeDefinitions.read(inputs.data(RootRuntimeDefinitionModel.DataRole.CAPABILITY_CONFIGURATION),1<<20),1<<20));
        var session=CapabilitySessionPresentation.decode(DriverJson.object(
                RootRuntimeDefinitions.read(inputs.data(RootRuntimeDefinitionModel.DataRole.CAPABILITY_SESSION_PRESENTATION),1<<20),1<<20));
        session.validateConfiguration(configuration);
        if(configuration.stateDir().isEmpty()||configuration.saveDir().isEmpty()
                ||session.queueDirectory().isEmpty()||session.driverStatePath().isEmpty())
            throw new IOException("complete migration requires actual configured state/SAVE/queue/Driver storage paths");
        for(Path path:List.of(configuration.stateDir().orElseThrow(),configuration.saveDir().orElseThrow(),
                session.queueDirectory().orElseThrow(),session.driverStatePath().orElseThrow())){
            if(!path.isAbsolute()||!path.normalize().equals(path)||inputs.storageLease().roots().stream()
                    .noneMatch(root->path.startsWith(Path.of(root.path()))))
                throw new IOException("actual capability storage path is outside the current Root runtime lease: "+path);
        }
        return new RootFrontendRuntime.Sources(FrontendRulesData.Build.require(settings.build().gameVersion(),
                settings.build().executableSha256()),inputs.source(FRONTEND_ORIGINAL_DRIVER),inputs.source(FRONTEND_RULES_EFFECTS),
                inputs.source(FRONTEND_RULES_DECODER),inputs.source(FRONTEND_START_EFFECTS),inputs.source(FRONTEND_START_DECODER),
                inputs.source(FRONTEND_ENTRY_GUARD),inputs.source(FRONTEND_ENTRY_AUTHORITY),diagnostics,journal,policy,configuration,session,
                Duration.ofMillis(settings.freshnessMs()),Duration.ofMillis(settings.heartbeatMaximumAgeMs()),
                settings.retainedFrames(),settings.retainedOrigins(),settings.authorityId(),
                frozen.fixture().isPresent()?Optional.of(RootFrontendRuntime.fixtureSources(inputs,selected)):Optional.empty());
    }

    /** No default callback exists. Startup must supply the actual same-writer source/read admission. */
    public static ActivityNativeContracts.Installation activity(RootRuntimeDefinitions.Inputs inputs,
            ActivityNativeContracts.Admission actualReadAdmission) {
        Objects.requireNonNull(inputs);Objects.requireNonNull(actualReadAdmission);
        return activity(inputs.configuration().activity().reads().stream().map(row->
                new ActivityNativeContracts.Source(row.query(),row.definition().sourceRef())).toList(),actualReadAdmission);
    }

    public static ActivityNativeContracts.Installation activity(List<ActivityNativeContracts.Source> sources,
            ActivityNativeContracts.Admission actualReadAdmission) {
        return new ActivityNativeContracts.Installation(List.copyOf(sources),Objects.requireNonNull(actualReadAdmission));
    }

    public static ActivityActionRoutes activityActions(RootRuntimeDefinitions.Inputs inputs,
            NativePrivateActionPermission.QualificationVerifier actualSourceQualifier,
            ActivityActionRoutes.Admission actualPolicyAdmission) {
        Objects.requireNonNull(inputs);Objects.requireNonNull(actualSourceQualifier);Objects.requireNonNull(actualPolicyAdmission);
        return activityActions(inputs.configuration().activity().mutations().stream().map(row->
                new ActivityActionRoutes.Source(row.kind(),row.definition().sourceRef(),actualSourceQualifier)).toList(),actualPolicyAdmission);
    }

    public static ActivityActionRoutes activityActions(List<ActivityActionRoutes.Source> sources,
            ActivityActionRoutes.Admission actualPolicyAdmission) {
        return new ActivityActionRoutes(List.copyOf(sources),Objects.requireNonNull(actualPolicyAdmission));
    }

    /** Runtime storage qualification is a concrete prerequisite, never replaced by a per-write numeric check. */
    public static RootIncidentRuntime.Prepared incidents(RootRuntimeDefinitions.Inputs inputs,Clock clock,
            EpisodeIncidentJournal.IoGuard actualRuntimeStorageGuard) {
        Objects.requireNonNull(inputs);Objects.requireNonNull(clock);Objects.requireNonNull(actualRuntimeStorageGuard);
        var settings=inputs.configuration().incidents();
        EpisodeIncidentJournal.IoGuard bounded=pending->{
            if(pending<0||pending>settings.maximumSingleWriteBytes())
                throw new IOException("actual incident write exceeds its configured runtime bound");
            actualRuntimeStorageGuard.require(pending);
        };
        return incidents(new EpisodeIncidentJournal.Configuration(Path.of(settings.incidentBase()),
                Path.of(settings.scanBase()),clock,bounded,Optional.of(TrustedEventSourceContext.open(inputs.eventSources()))),
                inputs.source(INCIDENT_IMPLEMENTATION));
    }

    public static RootIncidentRuntime.Prepared incidents(EpisodeIncidentJournal.Configuration configuration,
            ExactRef implementation) {
        return new RootIncidentRuntime.Prepared(Objects.requireNonNull(configuration),Objects.requireNonNull(implementation));
    }

}
