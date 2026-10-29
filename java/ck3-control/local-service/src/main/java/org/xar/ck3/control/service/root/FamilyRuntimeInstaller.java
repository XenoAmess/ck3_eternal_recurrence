package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Concrete family graph. Native products must be the real native owner's prepared actions, reads and pure archive replay. */
public final class FamilyRuntimeInstaller {
    public record Sources(ExactRef ordinaryPolicy,ExactRef pendingStore,RootFamilyReadProducts.Sources reads,List<ExactRef> completeDomainProducers) {
        public Sources {
            Objects.requireNonNull(ordinaryPolicy);Objects.requireNonNull(pendingStore);Objects.requireNonNull(reads);
            completeDomainProducers=List.copyOf(completeDomainProducers);
            StrictJson.require(ordinaryPolicy.bytes()>0 && pendingStore.bytes()>0 && !completeDomainProducers.isEmpty() && completeDomainProducers.size()<=64
                    && completeDomainProducers.contains(ordinaryPolicy) && completeDomainProducers.contains(pendingStore),"actual complete family implementation closure required");
        }
    }
    /** This contains concrete callable products, never a factory callback, selector or already chosen family plan. */
    public record NativeProducts(RootFamilyMarriageSendRuntime marriages,java.util.Optional<RootChildEducationFocusRuntime> education) {
        public NativeProducts {
            Objects.requireNonNull(marriages);Objects.requireNonNull(education);
            education.ifPresent(runtime->StrictJson.require(runtime.issued().action().effect().operation().value().equals("private-select-child-education-focus-v1")
                    &&runtime.domain().binding()==runtime.issued().action()&&runtime.issued().archived().operation().equals(runtime.issued().action().effect().operation()),
                    "actual child education runtime action/domain/archive differ"));
        }
        public List<RootExecutableBindings.ActionBinding> actions() {var all=new java.util.ArrayList<>(marriages.actions());education.ifPresent(runtime->all.add(runtime.issued().action()));return List.copyOf(all);}
        public List<NativeRecordedEvidenceVerifier.Binding> archived() {var all=new java.util.ArrayList<>(marriages.archivedVerifiers());education.ifPresent(runtime->all.add(runtime.issued().archived()));return List.copyOf(all);}
        public List<RootDomainInstallation.FixedDomain> actionDomains() {var all=new java.util.ArrayList<>(marriages.actionDomains());education.ifPresent(runtime->all.add(runtime.domain()));return List.copyOf(all);}
        public List<RootReadContractCatalog.InstalledRead> installedReads() {var all=new java.util.ArrayList<>(marriages.installedReads());education.ifPresent(runtime->all.addAll(runtime.installedReads()));return List.copyOf(all);}
        public RootExecutableBindings.Family<RulerMarriageIntent> rulerMarriage() {return marriages.rulerMarriage();}
        public RootDomainInstallation.FamilyDomain rulerDomain() {return marriages.rulerDomain();}
        public FamilyNativePreparation.Replay replay() {return marriages.replay();}
        public ExactRef replayImplementation() {return marriages.replayImplementation();}
    }
    /** Construct and register before Core.open; importOriginal consumes only explicitly selected full documents. */
    public static final class Prepared {
        private final Sources sources;private final FamilyPorts.Settings settings;private final RootFamilyOriginalDomains originals;
        public Prepared(Path originalWriterLock,Map<DomainBodies.Slot,ExactRef> selectedOriginalDocuments,Sources sources,FamilyPorts.Settings settings) {
            this.sources=Objects.requireNonNull(sources);this.settings=Objects.requireNonNull(settings);
            originals=new RootFamilyOriginalDomains(originalWriterLock,selectedOriginalDocuments,sources.completeDomainProducers());
        }
        /** Fresh definitions do not select historical Family documents; actual state is initialized after observation. */
        public Prepared(Path originalWriterLock,Sources sources,FamilyPorts.Settings settings) {
            this.sources=Objects.requireNonNull(sources);this.settings=Objects.requireNonNull(settings);
            originals=new RootFamilyOriginalDomains(originalWriterLock,sources.completeDomainProducers());
        }
        public List<DomainBodies.Registration> domainRegistrations() {return originals.registrations();}
        public RootFamilyReadProducts.Sources readSources() {return sources.reads();}
        public void bindCore(RootApplicationAssembly.Core actual) {originals.bindCore(actual);}
        public ExactRef importOriginal(ContinuityStorePort.Session same,DomainBodies.Slot slot)throws IOException {return originals.importOriginal(same,slot);}
    }
    private final RootRuntimeContext context;private final Prepared prepared;private final NativeProducts nativeProducts;
    private final RootFamilyBridge bridge;private final RootFamilyReadProducts reads;private final FamilyPorts.Commands advance;
    private final RootFamilyPlanningOriginals planningOriginals;
    private FamilyOrdinaryFactory.CompleteBinding complete;private RootDomainInstallation installed;
    public FamilyRuntimeInstaller(RootRuntimeContext context,Prepared prepared,RootFamilyReadProducts actualReads,NativeProducts actualNativeProducts,
            RootFamilyBridge actualBridge,FamilyPorts.Commands actualSharedDateAdvance,RootFamilyPlanningOriginals actualPlanningOriginals) {
        this.context=Objects.requireNonNull(context);this.prepared=Objects.requireNonNull(prepared);nativeProducts=Objects.requireNonNull(actualNativeProducts);
        bridge=Objects.requireNonNull(actualBridge);advance=Objects.requireNonNull(actualSharedDateAdvance);
        StrictJson.require(prepared.sources.completeDomainProducers().contains(nativeProducts.replayImplementation()),"native family replay is outside the registered complete source closure");
        reads=Objects.requireNonNull(actualReads);reads.requireContext(context);
        planningOriginals=Objects.requireNonNull(actualPlanningOriginals);planningOriginals.requireContext(context);nativeProducts.marriages().requireContext(context);
        nativeProducts.education().ifPresent(runtime->runtime.requireContext(context));
    }
    public List<FamilyPorts.Query> missingReads() {return FamilyOrdinaryFactory.requiredReads(prepared.settings).stream().filter(query->!reads.reads().available(query)).sorted().toList();}
    public Set<OperationKey> missingActions() {
        var required=new HashSet<OperationKey>();var settings=prepared.settings;
        if(settings.familyEnabled()) {required.add(FamilyPendingProducer.Branch.HEIR.operation());if(settings.fulfillCurrentBetrothal())required.add(FamilyPendingProducer.Branch.FULFILLMENT.operation());}
        if(settings.matrilinealPair().isPresent())required.add(FamilyPendingProducer.Branch.MATRILINEAL.operation());
        if(settings.childDefaultEnabled())required.add(FamilyPendingProducer.Branch.DEFAULT.operation());
        if(settings.familyEnabled() && settings.childFocusEnabled())required.add(new OperationKey("private-select-child-education-focus-v1"));
        nativeProducts.actions().forEach(binding->required.remove(binding.effect().operation()));return Set.copyOf(required);
    }
    public synchronized RootDomainInstallation install()throws IOException {
        StrictJson.require(installed==null,"family runtime installs once per actual Game");
        context.requireCurrent(context.clock().instant().plusSeconds(1));
        StrictJson.require(missingReads().isEmpty() && missingActions().isEmpty(),"actual family producers incomplete: reads="+missingReads()+" actions="+missingActions());
        var artifacts=context.writer().artifactStore().orElseThrow(()->new IllegalStateException("the original writer has no actual artifact store"));
        var pending=new RootFamilyPendingSources(context,bridge,nativeProducts.replay(),nativeProducts.replayImplementation());
        complete=FamilyOrdinaryFactory.bind(new FamilyOrdinaryFactory.Inputs(prepared.sources.ordinaryPolicy(),context.reads(),reads.reads(),context::borrowedSession,
                bridge,artifacts,context.archive(),advance,prepared.settings,planningOriginals),pending);
        prepared.originals.bindGame(context,complete);
        var pendingBinding=new RootDomainIntentPreparation.Binding("family-original-native-pending/v1",prepared.sources.pendingStore(),FamilyPendingProducer::supports,complete.pending());
        Set<OperationKey> requiredPending=FamilyPendingProducer.operations().stream().filter(operation->nativeProducts.actions().stream().anyMatch(action->action.effect().operation().equals(operation))).collect(java.util.stream.Collectors.toUnmodifiableSet());
        var installedReads=new java.util.ArrayList<>(reads.installedReads());installedReads.addAll(nativeProducts.installedReads());
        installed=new RootDomainInstallation("family-native-and-ordinary/v1",prepared.domainRegistrations(),installedReads,List.of(),nativeProducts.actions(),List.of(),nativeProducts.archived(),
                List.of(nativeProducts.rulerMarriage()),List.of(),List.of(),List.of(pendingBinding),requiredPending,List.of(complete.ordinary()),List.of(),nativeProducts.actionDomains(),List.of(nativeProducts.rulerDomain()),List.of());
        return installed;
    }
    public synchronized OrdinaryCorePolicy.CoreProducer rulerMarriage() {StrictJson.require(installed!=null,"actual family products not installed");return complete.rulerMarriage();}
    public synchronized List<DomainBodies.BodyRef> initializeFresh(ContinuityStorePort.Session same,FreshCampaignContext actual)throws IOException {
        StrictJson.require(installed!=null,"fresh Family requires its installed producer graph");
        actual.requireCurrent(same);var result=prepared.originals.initializeFresh(context,same,actual);actual.requireCurrent(same);return result;
    }
    public synchronized List<DomainBodies.BodyRef> initializeNext(ContinuityStorePort.Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
        StrictJson.require(installed!=null,"NEXT family requires its actual installed producer graph");
        proof.requireCurrent(same,context);var result=prepared.originals.initializeNext(context,same,proof);proof.requireCurrent(same,context);return result;
    }
    public synchronized List<DomainBodies.BodyRef> initializeNatural(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.CommittedNatural actual)throws IOException {
        StrictJson.require(installed!=null,"natural Family requires its actual installed producer graph");
        actual.requireCurrent(same);var result=prepared.originals.initializeNatural(context,same,actual);actual.requireCurrent(same);return result;
    }
    public synchronized List<DomainBodies.BodyRef> initializeOrdinaryRestored(ContinuityStorePort.Session same,
            RootRestorationOriginalProof actual)throws IOException {
        StrictJson.require(installed!=null,"ordinary restoration requires the actual installed Family producer graph");
        actual.requireCurrent(same);var result=prepared.originals.initializeOrdinaryRestored(context,same,actual);actual.requireCurrent(same);return result;
    }
    public RootFamilyReadProducts readProducts() {return reads;}
    public synchronized FamilyOrdinaryPolicy ordinary() {StrictJson.require(installed!=null,"actual family products not installed");return complete.ordinary();}
    public FamilyPorts.LedgerRead documents(org.xar.ck3.control.application.planning.PlanningRequest actual) {
        return new FamilyDomainSource(context::borrowedSession,bridge).readCurrent(actual);
    }
}
