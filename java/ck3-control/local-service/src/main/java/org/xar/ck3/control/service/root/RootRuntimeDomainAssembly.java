package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.LifeAdvanceRootReplay;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.M5PeacetimePolicy;
import org.xar.ck3.control.application.planning.warexit.WarExitPolicies;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m0.RaiktorActualRecommendationFactory;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.sway.SwayRuntimeInstaller;

/** Concrete remaining-domain composition over one original Core and one physical Game.
 * Installation constructs actual producers. The complete pipeline and live admission remain separate checks.
 */
public final class RootRuntimeDomainAssembly {
    private RootRuntimeDomainAssembly() { }

    public record Shared(GovernanceRuntimeInstaller.Installed nativeGovernance,
            GovernanceOrdinaryRuntimeInstaller.Installed governance,GovernanceActivityRuntime activity,
            PrisonersRuntimeInstaller prisoners,ArmyRuntimeInstaller army,ConstructionRuntimeInstaller construction,
            OrdinaryMilitaryInstaller military,ArmyAdditionalReadInstaller.Installed additionalArmy,
            KnownInteractionsRuntimeInstaller interactions,RootIncidentRuntime incidents,RootFrontendRuntime frontend) {
        public Shared {
            Objects.requireNonNull(nativeGovernance);Objects.requireNonNull(governance);Objects.requireNonNull(activity);
            Objects.requireNonNull(prisoners);Objects.requireNonNull(army);Objects.requireNonNull(construction);
            Objects.requireNonNull(military);Objects.requireNonNull(additionalArmy);Objects.requireNonNull(interactions);
            Objects.requireNonNull(incidents);Objects.requireNonNull(frontend);
        }
    }
    public record PolicySources(ExactRef ordinaryCore,ExactRef formalWarExit) {
        public PolicySources {
            for(ExactRef source:List.of(ordinaryCore,formalWarExit))
                StrictJson.require(source.bytes()>0,"actual selected complete policy source required");
        }
    }
    public sealed interface SwayInitialization permits SwayFresh,SwayOriginals { }
    /** Explicit fresh automation history; actual canonical initial-entry proof is supplied only after Game entry. */
    public record SwayFresh() implements SwayInitialization { }
    /** These are selected real originals, not freshly manufactured empty domain bodies. */
    public record SwayOriginals(ExactRef formal,Optional<ExactRef> scheduler,ExactRef guardedOriginRead) implements SwayInitialization {
        public SwayOriginals {
            Objects.requireNonNull(formal);Objects.requireNonNull(scheduler);Objects.requireNonNull(guardedOriginRead);
            StrictJson.require(formal.bytes()>0&&guardedOriginRead.bytes()>0,"actual Sway original ledger and guarded read required");
        }
    }
    /** Plain values for the four remaining ordinary domains. These records never hold Prepared products. */
    public record OrdinaryFamilyConfiguration(RootFamilyRuntimeFactory.OrdinaryConfiguration family,
            RootGuardianRuntimeFactory.OrdinaryConfiguration guardian,SwayRuntimeInstaller.OrdinaryConfiguration sway,
            RootRiteCreationRuntimeFactory.OrdinaryConfiguration rite) {
        public OrdinaryFamilyConfiguration {Objects.requireNonNull(family);Objects.requireNonNull(guardian);Objects.requireNonNull(sway);Objects.requireNonNull(rite);}
    }
    public record OrdinaryFamilySources(RootFamilyRuntimeFactory.Sources family,
            RootGuardianRuntimeFactory.OrdinarySources guardian,SwayRuntimeInstaller.Sources sway,
            RootRiteCreationRuntimeFactory.OrdinarySources rite) {
        public OrdinaryFamilySources {Objects.requireNonNull(family);Objects.requireNonNull(guardian);Objects.requireNonNull(sway);Objects.requireNonNull(rite);}
    }
    /** Executable products for the final 25-component assembly, constructed exactly once by this factory. */
    public record OrdinaryFamilyProducts(RootFamilyRuntimeFactory.Prepared family,RootGuardianRuntimeFactory.Prepared guardian,
            SwayRuntimeInstaller.Prepared sway,RootRiteCreationRuntimeFactory.Prepared rite) {
        public OrdinaryFamilyProducts {Objects.requireNonNull(family);Objects.requireNonNull(guardian);Objects.requireNonNull(sway);Objects.requireNonNull(rite);}
    }
    public static OrdinaryFamilyProducts prepareOrdinaryFamily(OrdinaryFamilyConfiguration configuration,OrdinaryFamilySources sources) {
        Objects.requireNonNull(configuration);Objects.requireNonNull(sources);
        return new OrdinaryFamilyProducts(RootFamilyRuntimeFactory.prepareOrdinary(configuration.family(),sources.family()),
                RootGuardianRuntimeFactory.prepareOrdinary(configuration.guardian(),sources.guardian()),
                SwayRuntimeInstaller.prepareOrdinary(configuration.sway(),sources.sway()),
                RootRiteCreationRuntimeFactory.prepareOrdinary(configuration.rite(),sources.rite()));
    }
    private static final class Attempt {
        final Shared shared;Installed installed;boolean entered;IOException failure;
        Attempt(Shared actual) {shared=actual;}
    }
    /** All inputs are concrete source-owning products from their sole domain producers. */
    public static final class Prepared {
        /** The identical event source-owning Prepared consumed by the installed EXECUTE products. */
        public EventRuntimeInstaller.Prepared eventsPrepared(){return events;}
        /** The identical strengths source-owning Prepared retained by the installed runtime. */
        public RootArmyStrengthsRuntimeFactory.Prepared strengths(){return strengths;}
        public RootRouteContactAdvanceRuntime.Prepared routeAdvancePrepared(){return routeAdvance;}
        private final RootLifeRuntimeFactory.Prepared life;
        private final RootRouteContactAdvanceRuntime.Prepared routeAdvance;
        private final RootFamilyRuntimeFactory.Prepared family;
        private final RootArmyOrdinaryRuntimeInputs.Prepared army;
        private final RootArmyStrengthsRuntimeFactory.Prepared strengths;
        private final EventRuntimeInstaller.Prepared events;
        private final RootLifecycleRuntimeFactory.Prepared lifecycle;
        private final SwayRuntimeInstaller.Prepared sway;
        private final SwayInitialization swayInitialization;
        private final RootCrownRetryRuntime.Prepared crown;
        private final RootCrossRunPlanning.Prepared crossRun;
        private final RootCampaignPoliciesFactory.Prepared campaign;
        private final RootGuardianRuntimeFactory.Prepared guardian;
        private final RootHolyWarPlanningPolicies.Prepared holy;
        private final RootActiveCombatDateGuardFactory.Sources activeCombat;
        private final ExactRef successionPolicies;
        private final RootWarCoreFactory.Sources war;
        private final RootPeacetimeWarEntryRuntime.Prepared warEntry;
        private final RootRiteCreationRuntimeFactory.Prepared rite;
        private final RootActionHistoryMaterialSourceFactory.Prepared actionHistory;
        private final PolicySources policies;
        private final OrdinaryMilitaryInstaller.PolicySources militaryPolicies;
        private final RaiktorActualRecommendationFactory.Configuration formalWar;
        private final M5PeacetimePolicy.Options peacetime;
        private final Duration physicalFreshness;
        private final List<DomainBodies.Registration> registrations;
        private final Map<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        /** Source factory identity check only; no product reconstruction or runtime permission is granted. */
        public void requireDriverDependencies(RootFamilyRuntimeFactory.Prepared identicalFamily,RootLifecycleRuntimeFactory.Prepared identicalLifecycle)throws IOException {
            if(family!=Objects.requireNonNull(identicalFamily)||lifecycle!=Objects.requireNonNull(identicalLifecycle))
                throw new IOException("Driver source products must retain the identical original family and lifecycle Prepared instances");
        }
        public Prepared(RootLifeRuntimeFactory.Prepared life,RootFamilyRuntimeFactory.Prepared family,
                RootArmyOrdinaryRuntimeInputs.Prepared army,RootArmyStrengthsRuntimeFactory.Prepared strengths,
                EventRuntimeInstaller.Prepared events,RootLifecycleRuntimeFactory.Prepared lifecycle,
                SwayRuntimeInstaller.Prepared sway,SwayInitialization swayInitialization,RootCrownRetryRuntime.Prepared crown,
                RootCrossRunPlanning.Prepared crossRun,RootCampaignPoliciesFactory.Prepared campaign,
                RootGuardianRuntimeFactory.Prepared guardian,RootHolyWarPlanningPolicies.Prepared holy,
                RootActiveCombatDateGuardFactory.Sources activeCombat,ExactRef successionPolicies,RootWarCoreFactory.Sources war,
                RootPeacetimeWarEntryRuntime.Prepared warEntry,RootRiteCreationRuntimeFactory.Prepared rite,PolicySources policies,
                OrdinaryMilitaryInstaller.PolicySources militaryPolicies,
                RaiktorActualRecommendationFactory.Configuration formalWar,M5PeacetimePolicy.Options peacetime,
                Duration physicalFreshness,RootActionHistoryMaterialSourceFactory.Prepared actionHistory,
                RootRouteContactAdvanceRuntime.Prepared routeAdvance) {
            this.actionHistory=Objects.requireNonNull(actionHistory);
            this.routeAdvance=Objects.requireNonNull(routeAdvance);
            this.life=Objects.requireNonNull(life);this.family=Objects.requireNonNull(family);this.army=Objects.requireNonNull(army);
            this.strengths=Objects.requireNonNull(strengths);this.events=Objects.requireNonNull(events);
            this.lifecycle=Objects.requireNonNull(lifecycle);this.sway=Objects.requireNonNull(sway);
            this.swayInitialization=Objects.requireNonNull(swayInitialization);this.crown=Objects.requireNonNull(crown);
            this.crossRun=Objects.requireNonNull(crossRun);this.campaign=Objects.requireNonNull(campaign);this.war=Objects.requireNonNull(war);
            this.guardian=Objects.requireNonNull(guardian);this.holy=Objects.requireNonNull(holy);
            this.activeCombat=Objects.requireNonNull(activeCombat);this.successionPolicies=Objects.requireNonNull(successionPolicies);
            StrictJson.require(successionPolicies.bytes()>0,"actual succession policy source required");
            this.warEntry=Objects.requireNonNull(warEntry);this.rite=Objects.requireNonNull(rite);this.policies=Objects.requireNonNull(policies);
            this.militaryPolicies=Objects.requireNonNull(militaryPolicies);this.formalWar=Objects.requireNonNull(formalWar);
            this.peacetime=Objects.requireNonNull(peacetime);this.physicalFreshness=Objects.requireNonNull(physicalFreshness);
            StrictJson.require(!physicalFreshness.isNegative()&&!physicalFreshness.isZero()
                    &&physicalFreshness.compareTo(Duration.ofMinutes(1))<=0,"bounded actual physical observation freshness required");
            Map<DomainBodies.Slot,DomainBodies.Registration> actual=new LinkedHashMap<>();
            List<DomainBodies.Registration> all=new ArrayList<>(family.domainRegistrations());
            all.addAll(lifecycle.domainRegistrations());all.add(sway.registration());all.addAll(guardian.domainRegistrations());
            all.addAll(rite.domainRegistrations());
            for(var registration:all) {
                var previous=actual.putIfAbsent(registration.slot(),registration);
                StrictJson.require(previous==null||previous==registration,"different actual remaining producers claim one canonical domain");
            }
            registrations=List.copyOf(actual.values());
        }
        public List<DomainBodies.Registration> domainRegistrations(){return registrations;}
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"remaining definitions bind the actual sole Core once");
            core=Objects.requireNonNull(actual);family.bindCore(actual);events.bindCore(actual);
            lifecycle.bindCore(actual);sway.bindCore(actual);guardian.bindCore(actual);rite.bindCore(actual);
        }
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
            Objects.requireNonNull(actual);List<NativePrivateActionPermission> permissions=new ArrayList<>(family.privatePermissions(actual));
            permissions.addAll(events.privatePermissions(actual));permissions.addAll(lifecycle.privatePermissions(actual));
            permissions.addAll(army.privatePermissions(actual));permissions.addAll(rite.privatePermissions());
            return List.copyOf(permissions);
        }
        public void bindManagedLifecycle(JavaGameLifecycle actual,NativeLaunchPlan retainedPlan)throws IOException {
            lifecycle.bindManagedLifecycle(actual,retainedPlan);
        }
        public synchronized Installed install(RootRuntimeContext context,Shared shared)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(shared);
            StrictJson.require(core!=null&&context.core()==core&&crown.core()==core,
                    "remaining domains crossed their original Core or shared Crown runtime");
            Attempt attempt=attempts.get(context);
            if(attempt==null){StrictJson.require(attempts.size()<64,"bounded actual remaining-domain installation history required");attempt=new Attempt(shared);attempts.put(context,attempt);}
            StrictJson.require(attempt.shared.equals(shared),"same physical Game cannot replace its actual shared producers");
            if(attempt.installed!=null)return attempt.installed;
            if(attempt.entered)throw new IOException("actual remaining-domain assembly already entered; partial installation is not replayed",attempt.failure);
            attempt.entered=true;
            try {
                var actualLife=life.install(context,crown);
                var actualRouteAdvance=routeAdvance.install(context,actualLife);
                var actualFamily=family.install(context,RootFamilyRuntimeFactory.Shared.from(shared.interactions(),actualLife.commands()));
                actualFamily.installer().ordinary().setFirstHeirMarriageEnabled(context.core().firstHeirMarriageEnabled());
                actualFamily.installer().ordinary().setNewMarriageProposalsEnabled(context.core().newMarriageProposalsEnabled());
                var actualArmy=army.install(context,shared,actualFamily);
                var actualGuardian=guardian.install(context,shared.interactions());
                var actualStrengths=strengths.install(context,shared.army().products().frames());
                var commands=new RootRuntimeCommands(context,actualArmy.service(),actualLife.commands(),shared.military().commander());
                var actualEvents=events.install(context,shared.interactions(),shared.incidents(),
                        new EventRuntimeInstaller.ArmySources(actualStrengths.contracts(),actualStrengths.pipeline(),actualStrengths.current(),shared.military().forecasts()),
                        commands);
                var actualWar=new RootWarCoreFactory(context,war,shared.military(),shared.interactions(),commands);
                var actualEntry=RootPeacetimeWarEntryRuntime.install(warEntry,context,commands,shared.military(),actualArmy,actualWar);
                var actualCore=OrdinaryCorePolicy.assemble(policies.ordinaryCore(),actualWar,actualEvents.registeredCore(),
                        shared.governance().coreCouncil(),actualFamily.installer().rulerMarriage(),actualEntry,commands,LifeAdvanceComposite::accepts);
                actualWar.bind(actualCore);
                var actualGift=context.finance().policies().stages().stream().filter(policy->policy.stage()==PlanningStage.FACTION_GIFT).toList();
                StrictJson.require(actualGift.size()==1,"the same actual finance factory must own exactly one faction-gift policy");
                var actualPeacetime=new MilitaryPeacetimeRuntime(context,shared.construction(),actualFamily.installer(),actualGift.getFirst(),peacetime);
                var physical=new RootLifecycleAuthority(core.writer(),core.archive(),context.transport(),same->{
                    core.writer().requireSession(same);return context.adopted().authority();
                },core.observationAssembler(),context.source(),context.sources()::verifyLifecycle,context.clock(),physicalFreshness);
                var campaignRoot=context.finance().definitions().contract(org.xar.ck3.control.application.planning.finance.FinanceReadContracts.Query.ROOT);
                var actualLifecycle=lifecycle.install(context,physical,shared.prisoners(),crossRun,campaignRoot,actualLife);
                var actualGame=context.game();
                actualLifecycle.composite().bindNaturalFamilyMigration(
                        new SessionIdentity(actualGame.machineId(),actualGame.generation(),actualGame.sessionId()),
                        (same,actual)->actualFamily.initializeNatural(same,actual));
                var fullPlanner=new PlannerLink(context);
                var actualSway=new SwayRuntimeInstaller(context,sway,fullPlanner);
                var actualRite=rite.install(context);
                var installed=new ArrayList<RootDomainInstallation>(actualLife.installations());
                installed.add(actualRouteAdvance.installation());
                installed.add(actualFamily.installation());installed.add(actualArmy.installation());installed.add(actualStrengths.installation());
                installed.add(actualEvents.installation());installed.add(actualLifecycle.installation());installed.add(actualSway.install());
                installed.add(actualRite.installation());
                installed.add(campaign.install(context,actualLife,commands).installation());
                installed.add(actualGuardian.installation());
                installed.add(holy.install(context,shared,actualArmy,commands));
                installed.add(RootActiveCombatDateGuardFactory.install(activeCombat).installation());
                installed.add(policyInstallation(RootSuccessionPlanningPolicies.install(successionPolicies,context,actualLifecycle,shared.prisoners()).policies()));
                installed.add(shared.military().install(actualCore.war(),commands,militaryPolicies,actualPeacetime));
                installed.add(policyInstallation(List.of(actualCore.core(),
                        new WarExitPolicies(PlanningStage.THREE_WAY_WAR_EXIT,policies.formalWarExit(),actualEntry.actualExitReads(),formalWar,actualEntry.declarationLeaseSource()),
                        new WarExitPolicies(PlanningStage.PREWAR_FORCE_COALITION,policies.formalWarExit(),actualEntry.actualExitReads(),formalWar,actualEntry.declarationLeaseSource()))));
                attempt.installed=new Installed(this,context,shared,List.copyOf(installed),actualLife,actualFamily,actualArmy,
                        actualStrengths,actualEvents,actualLifecycle,actualSway,actualGuardian,commands,actualEntry,fullPlanner,actualRite.runtime(),actualRouteAdvance);
                return attempt.installed;
            } catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("INCOMPLETE_ROOT_RUNTIME: actual remaining producer installation failed",failure);throw attempt.failure;}
        }
    }
    public static final class Installed {
        private final Prepared prepared;private final RootRuntimeContext context;private final Shared shared;
        private final List<RootDomainInstallation> installations;
        private final RootLifeRuntimeFactory.Installed life;private final RootFamilyRuntimeFactory.Installed family;
        private final RootRouteContactAdvanceRuntime.Installed routeAdvance;
        private final ArmyOrdinaryRuntimeBindings.Installed army;private final RootArmyStrengthsRuntimeFactory.Installed strengths;
        private final EventRuntimeInstaller events;private final RootLifecycleRuntimeFactory.Installed lifecycle;
        private final SwayRuntimeInstaller sway;private final RootGuardianRuntimeFactory.Installed guardian;private final RootRuntimeCommands commands;
        private final RootPeacetimeWarEntryRuntime warEntry;private final PlannerLink fullPlanner;
        private final RootRiteCreationRuntimeFactory.Runtime rite;
        private Installed(Prepared prepared,RootRuntimeContext context,Shared shared,List<RootDomainInstallation> installations,
                RootLifeRuntimeFactory.Installed life,RootFamilyRuntimeFactory.Installed family,ArmyOrdinaryRuntimeBindings.Installed army,
                RootArmyStrengthsRuntimeFactory.Installed strengths,EventRuntimeInstaller events,RootLifecycleRuntimeFactory.Installed lifecycle,
                SwayRuntimeInstaller sway,RootGuardianRuntimeFactory.Installed guardian,RootRuntimeCommands commands,RootPeacetimeWarEntryRuntime warEntry,PlannerLink fullPlanner,
                RootRiteCreationRuntimeFactory.Runtime rite,RootRouteContactAdvanceRuntime.Installed routeAdvance) {
            this.prepared=prepared;this.context=context;this.shared=shared;this.installations=List.copyOf(installations);
            this.life=life;this.family=family;this.army=army;this.strengths=strengths;this.events=events;this.lifecycle=lifecycle;
            this.sway=sway;this.guardian=guardian;this.commands=commands;this.warEntry=warEntry;this.fullPlanner=fullPlanner;this.rite=Objects.requireNonNull(rite);
            this.routeAdvance=Objects.requireNonNull(routeAdvance);
        }
        public RootActionHistoryMaterialSourceFactory.Products actionHistory(RootRuntimeContext actual,RootInstalledCatalog catalog)throws IOException {
            StrictJson.require(actual==context&&catalog.context()==context&&catalog.remainingDomains()==this,
                    "actual action history materials crossed the identical installed catalog/context");
            return prepared.actionHistory.install(context,catalog);
        }
        public void requireContext(RootRuntimeContext actual)throws IOException {
            if(actual!=context||actual.core()!=prepared.core)throw new IOException("remaining domain products belong to another actual Root context/Core");
        }
        public List<RootDomainInstallation> installations(){return installations;}
        public RootDomainInstallation knownInteractions(){return shared.interactions().readAndPolicyInstallation();}
        public RootLifeRuntimeFactory.Installed life(){return life;}
        public RootRouteContactAdvanceRuntime.Installed routeAdvance(){return routeAdvance;}
        public RootFamilyRuntimeFactory.Installed family(){return family;}
        public ArmyOrdinaryRuntimeBindings.Installed armyOrdinary(){return army;}
        public RootArmyStrengthsRuntimeFactory.Installed strengths(){return strengths;}
        public EventRuntimeInstaller events(){return events;}
        public RootLifecycleRuntimeFactory.Installed lifecycle(){return lifecycle;}
        public SwayRuntimeInstaller sway(){return sway;}
        public RootRiteCreationRuntimeFactory.Runtime riteCreation(){return rite;}
        public RootGuardianRuntimeFactory.Installed guardian(){return guardian;}
        public RootRuntimeCommands commands(){return commands;}
        public RootPeacetimeWarEntryRuntime warEntry(){return warEntry;}
        public LifeAdvanceRootReplay lifeReplay(){return life.replay();}
        /** Called only after the final immutable catalog has verified all 34 concrete stages. */
        public void bindFullPipeline(OrdinaryPlanningPipeline actual){fullPlanner.bind(actual);}
        /** Pure allowlist derivation from the original canonical intent; this performs no Native reads or publication. */
        public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return (original,identity,current,deadline)->{
            context.writer().requireSession(context.borrowedSession());
            List<RootReconciliationAuthority.AllowedRead> actual=new ArrayList<>();
            actual.addAll(shared.army().reconciliationReads(original,identity,current,deadline));
            actual.addAll(shared.nativeGovernance().reconciliationReads().allowed(original,identity,current,deadline));
            actual.addAll(shared.military().reconciliationReads(original,identity,current,deadline));
            actual.addAll(army.reconciliationReads(original,identity,current,deadline));
            if(original.command().operation().equals(org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies.MERCENARY)) {
                var contract=context.finance().definitions().mercenaryEmployerContract();
                var request=PlanningReadRequest.newReconciliation(identity,contract.operation(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),deadline);
                org.xar.ck3.control.application.effects.NativeFinanceEffects.requireCanonicalMercenaryReconciliation(
                        original,ActionTransitions.attempt(original.state()).orElseThrow(),identity,contract,request);
                actual.add(new RootReconciliationAuthority.AllowedRead(contract,request.arguments(),RootReconciliationAuthority.QueryKind.MERCENARY_EMPLOYER));
            }
            var command = original.command(); var operation = command.operation();
            if (org.xar.ck3.control.application.advance.AdvancePrimitives.supports(operation)
                    && (operation.value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.ARM_PREFIX)
                    || operation.value().startsWith(org.xar.ck3.control.application.advance.ClockStatusRead.CANCEL_PREFIX))
                    && command.arguments().members().isEmpty()
                    && org.xar.ck3.control.application.advance.AdvancePrimitives.expected(command.before(), command.source(),
                            operation, command.arguments()).equals(command.expected())) {
                var clock = life.infrastructure();
                RootUnknownSentinelReadProfile.requireInstalled(clock.unknownStatuses(), clock.statuses());
                actual.add(new RootReconciliationAuthority.AllowedRead(clock.unknownStatuses(),
                        new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),
                        RootReconciliationAuthority.QueryKind.UNKNOWN_SENTINEL_STATUS));
            }
            actual.addAll(family.reconciliationReads().allowed(original,identity,current,deadline));
            actual.addAll(guardian.reconciliationReads().allowed(original,identity,current,deadline));
            actual.addAll(lifecycle.natural().pendingRuntime().reconciliationReads().allowed(original,identity,current,deadline));
            return List.copyOf(actual);
        };}
        public void afterInitialEntry(ContinuityStorePort.Session same,RootInitialEpisodeProof actual)throws IOException {
            context.writer().requireSession(same);actual.requireCurrent(same);
            StrictJson.require(actual.adopted()==context.adopted(),"remaining domain import crossed the actual initial Driver");
            for(var registration:prepared.family.domainRegistrations())prepared.family.importOriginal(same,registration.slot());
            prepared.guardian.importOriginal(context,same,context.clock().instant().plus(physicalFreshness()));
            switch (prepared.swayInitialization) {
                case SwayFresh fresh -> sway.initializeFresh(same,actual);
                case SwayOriginals originals -> sway.importOriginal(originals.formal(),originals.scheduler(),originals.guardedOriginRead());
            }
            rite.initializeFresh(context,same,actual);
            requireActualBodies(same);
        }
        /** Initialize automation state from this actual observed new campaign, never configured legacy originals. */
        public void afterInitialEntry(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
            context.writer().requireSession(same);actual.requireCurrent(same);
            StrictJson.require(actual.context()==context,"fresh remaining domains crossed their physical context");
            family.initializeFresh(same,actual);
            prepared.guardian.initializeFresh(context,same,actual);
            sway.initializeFresh(same,actual);
            rite.initializeFresh(context,same,actual);
            requireActualBodies(same);
        }
        public List<DomainBodies.BodyRef> initializeNextFamilyAndSway(ContinuityStorePort.Session same,
                RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
            proof.requireCurrent(same,context);var bodies=new ArrayList<DomainBodies.BodyRef>();
            bodies.addAll(family.initializeNext(same,proof));bodies.add(sway.initializeNext(same,proof));
            bodies.add(rite.initializeNext(context,same,proof));
            prepared.crossRun.requireEpisodeFirst(context,same,proof);
            proof.requireCurrent(same,context);return List.copyOf(bodies);
        }
        public void adoptRestored(ContinuityStorePort.Session same,RootRestorationOriginalProof actual,
                RestoreCheckpointService.RestoreBinding binding,Instant deadline)throws IOException {
            context.writer().requireSession(same);actual.requireCurrent(same);
            lifecycle.natural().admitRestoredSource(same,binding,deadline);
            if(binding.savedMaterial().kind()==org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial.Kind.ORDINARY)
                family.installer().initializeOrdinaryRestored(same,actual);
            requireActualBodies(same);prepared.sway.domain().load(same);
        }
        private Duration physicalFreshness(){return prepared.physicalFreshness;}
        private void requireActualBodies(ContinuityStorePort.Session same)throws IOException {
            for(var registration:prepared.family.domainRegistrations()) {
                var body=same.readDomain(registration.slot());
                if(!(body instanceof DomainBodies.Available known))throw new IOException("INCOMPLETE_ROOT_RUNTIME: actual family original missing "+registration.slot());
                same.verifyPin(same.capturePin(known.reference().payload(),WriterContracts.MAX_PIN_BYTES));
            }
            prepared.sway.domain().load(same);
            var actualRite=same.readDomain(rite.registration().slot());
            if(!(actualRite instanceof DomainBodies.Available known))throw new IOException("INCOMPLETE_ROOT_RUNTIME: actual Rite original missing");
            same.verifyPin(same.capturePin(known.reference().payload(),WriterContracts.MAX_PIN_BYTES));
        }
    }
    private static final class PlannerLink implements java.util.function.Supplier<OrdinaryPlanner> {
        private final RootRuntimeContext context;private OrdinaryPlanningPipeline pipeline;private OrdinaryPlanner planner;
        PlannerLink(RootRuntimeContext actual){context=actual;}
        synchronized void bind(OrdinaryPlanningPipeline actual) {
            StrictJson.require(pipeline==null,"the actual full ordinary pipeline binds once after catalog completion");
            pipeline=Objects.requireNonNull(actual);planner=actual.create(context.clock());
            context.core().decisionSelector().ifPresent(planner::bindSelector);
            planner.setM5JointPeacetimeEnabled(context.core().m5JointPeacetimeEnabled());
        }
        @Override public synchronized OrdinaryPlanner get(){
            StrictJson.require(planner!=null,"INCOMPLETE_ROOT_RUNTIME: Sway continuation requires the actual complete current ordinary planner");return planner;
        }
    }
    private static RootDomainInstallation policyInstallation(List<OrdinaryPolicy> policies) {
        return new RootDomainInstallation("actual-core-and-formal-war-policies",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                List.of(),List.of(),List.of(),List.of(),Set.of(),policies,List.of(),List.of(),List.of(),List.of());
    }
}
