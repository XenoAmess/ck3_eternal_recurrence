package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyNativePrivatePermissions;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** The sole concrete family assembly called by the physical Game's Root domain assembler. */
public final class RootFamilyRuntimeFactory {
    private RootFamilyRuntimeFactory() { }
    public record Sources(FamilyRuntimeInstaller.Sources ordinary,RootFamilyNativeReadProducts.Sources nativeReads,
            RootFamilyMarriageSendRuntime.Sources marriage,FamilyNativePrivatePermissions.Sources nativeSubmissions,
            Optional<RootChildEducationFocusRuntime.Sources> childFocus,RootEpidemicTreatmentRead.Sources treatment) {
        public Sources {
            Objects.requireNonNull(ordinary);Objects.requireNonNull(nativeReads);Objects.requireNonNull(marriage);
            Objects.requireNonNull(nativeSubmissions);
            Objects.requireNonNull(childFocus);Objects.requireNonNull(treatment);
            StrictJson.require(ordinary.completeDomainProducers().containsAll(marriage.completeProducers()),
                    "registered family domain replay must include the complete actual marriage producer closure");
            for(var route:FamilyMarriageIntent.Route.values())StrictJson.require(ordinary.completeDomainProducers().contains(nativeSubmissions.forRoute(route)),
                    "private submission native producer is outside the actual registered family source closure");
            childFocus.ifPresent(source->StrictJson.require(ordinary.completeDomainProducers().containsAll(source.completeProducers()),
                    "actual child focus producer closure is outside the registered family source graph"));
        }
    }
    /** Business values for a genuinely new campaign; no selected historical document or Prepared product is configuration. */
    public record OrdinaryConfiguration(Path writerLock,FamilyPorts.Settings settings,Path relationExportRoot) {
        public OrdinaryConfiguration {
            writerLock=Objects.requireNonNull(writerLock).toAbsolutePath().normalize();
            Objects.requireNonNull(settings);relationExportRoot=Objects.requireNonNull(relationExportRoot).toAbsolutePath().normalize();
        }
    }
    public static Prepared prepareOrdinary(OrdinaryConfiguration configuration,Sources sources) {
        return new Prepared(Objects.requireNonNull(configuration),Objects.requireNonNull(sources));
    }
    /** Shared products already belong to this physical Root; no callback creates missing native leaves. */
    public record Shared(InteractionCapabilities interactions,InteractionCapabilities.Installation interactionInstallation,
            RootInteractionContextProjection projection,RootFamilyCampaignRead campaignRoot,FamilyPorts.Commands dateAdvance) {
        public Shared {Objects.requireNonNull(interactions);Objects.requireNonNull(interactionInstallation);Objects.requireNonNull(projection);
            Objects.requireNonNull(campaignRoot);Objects.requireNonNull(dateAdvance);interactions.requireInstallation(interactionInstallation);}
        public static Shared from(KnownInteractionsRuntimeInstaller actualKnown,FamilyPorts.Commands actualDateAdvance) {
            Objects.requireNonNull(actualKnown);return new Shared(actualKnown.capabilities(),actualKnown.definitions(),actualKnown.projection(),actualKnown.campaign(),actualDateAdvance);
        }
    }
    public static final class Prepared {
        private final Sources sources;
        private final FamilyPorts.Settings settings;
        private final Path relationExportRoot;
        private final FamilyRuntimeInstaller.Prepared original;
        private final RootEpidemicTreatmentRead.Prepared treatment;
        private RootApplicationAssembly.Core core;
        private record Attempt(Shared shared,Optional<Installed> installed) { }
        private final Map<RootRuntimeContext,Attempt> attempts=new java.util.IdentityHashMap<>();
        public Prepared(Path originalWriterLock,Map<DomainBodies.Slot,ExactRef> selectedOriginalDocuments,Sources sources,
                FamilyPorts.Settings settings,Path actualOwnedRelationExportRoot) {
            this.sources=Objects.requireNonNull(sources);this.settings=Objects.requireNonNull(settings);
            relationExportRoot=Objects.requireNonNull(actualOwnedRelationExportRoot).toAbsolutePath().normalize();
            original=new FamilyRuntimeInstaller.Prepared(originalWriterLock,selectedOriginalDocuments,sources.ordinary(),settings);
            treatment=new RootEpidemicTreatmentRead.Prepared(sources.treatment());
        }
        private Prepared(OrdinaryConfiguration configuration,Sources sources) {
            this.sources=sources;settings=configuration.settings();relationExportRoot=configuration.relationExportRoot();
            original=new FamilyRuntimeInstaller.Prepared(configuration.writerLock(),sources.ordinary(),settings);
            treatment=new RootEpidemicTreatmentRead.Prepared(sources.treatment());
        }
        public List<DomainBodies.Registration> domainRegistrations() {return original.domainRegistrations();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"family prepared definitions bind the actual Core once");core=Objects.requireNonNull(actual);original.bindCore(actual);treatment.bindCore(actual);
        }
        /** Real mutation permissions are available before a ManagedGameSession/context exists. */
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actual) {
            Objects.requireNonNull(actual);var result=new java.util.ArrayList<>(FamilyNativePrivatePermissions.privateMarriages(sources.nativeSubmissions(),actual));
            if(settings.familyEnabled()&&settings.childFocusEnabled()) {
                StrictJson.require(sources.childFocus().isPresent(),"enabled focus lacks its actual concrete preparation/effects source definition");
                result.add(FamilyNativePrivatePermissions.childFocus(sources.ordinary().reads().focusNative(),actual));
            }
            return List.copyOf(result);
        }
        public ExactRef importOriginal(Session same,DomainBodies.Slot slot)throws IOException {return original.importOriginal(same,slot);}
        public synchronized Installed requireInstalled(RootRuntimeContext context)throws IOException {
            var actual=attempts.get(Objects.requireNonNull(context));
            if(core!=context.core()||actual==null||actual.installed().isEmpty())throw new IOException("Driver Family view requires the same already installed Family Prepared/context");
            return actual.installed().orElseThrow();
        }
        public synchronized Installed install(RootRuntimeContext context,Shared shared)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(shared);context.requireCurrent(context.clock().instant().plusSeconds(1));
            StrictJson.require(core!=null&&context.core()==core,"family factory must consume its exact once-bound Core");
            shared.campaignRoot().requireContext(context);
            var prior=attempts.get(context);
            if(prior!=null) {
                StrictJson.require(prior.shared().equals(shared),"same physical Game family installation changed its actual shared products");
                return prior.installed().orElseThrow(()->new IllegalStateException("this physical Game's family installation previously failed or is incomplete"));
            }
            StrictJson.require(attempts.size()<64,"bounded physical Game family installation history exhausted");
            attempts.put(context,new Attempt(shared,Optional.empty()));
            StrictJson.require(!(settings.familyEnabled()&&settings.childFocusEnabled())||sources.childFocus().isPresent(),
                    "enabled child focus has no actual native action; empty products cannot qualify the full family runtime");
            if(core.storageGuard() instanceof RootRuntimeStorageGuard storage)storage.createManagedDirectories(relationExportRoot);
            var bridge=new RootFamilyBridge(context);var planningOriginals=new RootFamilyPlanningOriginals(context);
            var nativeReads=new RootFamilyNativeReadProducts(context,sources.nativeReads(),shared.interactions(),shared.interactionInstallation(),
                    shared.projection(),shared.campaignRoot(),relationExportRoot);
            var reads=nativeReads.complete(sources.ordinary().reads());
            var fresh=new RootFamilyMarriageFreshPreparation(context,bridge,nativeReads,reads,planningOriginals,sources.marriage().freshPreparation());
            var marriages=new RootFamilyMarriageSendRuntime(context,bridge,fresh,sources.marriage());
            Optional<RootChildEducationFocusRuntime> education;
            if(settings.familyEnabled()&&settings.childFocusEnabled())education=Optional.of(new RootChildEducationFocusRuntime(context,sources.childFocus().orElseThrow(),
                    reads.reads().find(FamilyPorts.Query.CHILD_FOCUS).orElseThrow(),reads.reads().find(FamilyPorts.Query.CHILD_FOCUS_RECEIPT).orElseThrow()));
            else education=Optional.empty();
            var products=new FamilyRuntimeInstaller.NativeProducts(marriages,education);
            var installer=new FamilyRuntimeInstaller(context,original,reads,products,bridge,shared.dateAdvance(),planningOriginals);
            var actualTreatment=treatment.install(context);
            var installation=installer.install();
            var installed=new Installed(installer,installation,marriages,nativeReads,education,actualTreatment);
            attempts.put(context,new Attempt(shared,Optional.of(installed)));return installed;
        }
    }
    public record Installed(FamilyRuntimeInstaller installer,RootDomainInstallation installation,RootFamilyMarriageSendRuntime marriages,
            RootFamilyNativeReadProducts nativeReads,Optional<RootChildEducationFocusRuntime> education,RootEpidemicTreatmentRead treatment) {
        public Installed {Objects.requireNonNull(installer);Objects.requireNonNull(installation);Objects.requireNonNull(marriages);Objects.requireNonNull(nativeReads);Objects.requireNonNull(education);Objects.requireNonNull(treatment);}
        public RootReconciliationAuthority.QueryPolicy reconciliationReads() {return (original,identity,current,deadline)->{
            var actual=new java.util.ArrayList<>(marriages.reconciliationReads().allowed(original,identity,current,deadline));
            if(education.isPresent())actual.addAll(education.orElseThrow().reconciliationReads().allowed(original,identity,current,deadline));return List.copyOf(actual);
        };}
        public List<DomainBodies.BodyRef> initializeFresh(Session same,FreshCampaignContext actual)throws IOException {
            return installer.initializeFresh(same,Objects.requireNonNull(actual));
        }
        public List<DomainBodies.BodyRef> initializeNext(Session same,RootApplicationAssembly.EpisodeDomainInitializationProof proof)throws IOException {
            return installer.initializeNext(same,Objects.requireNonNull(proof));
        }
        public List<DomainBodies.BodyRef> initializeNatural(Session same,
                org.xar.ck3.control.application.lifecycle.LifecycleComposites.CommittedNatural actual)throws IOException {
            return installer.initializeNatural(same,Objects.requireNonNull(actual));
        }
        public ReadContract<Obj> obligationsContract() {return installer.readProducts().reads().find(FamilyPorts.Query.CHILD_HOUSE_PREVIEW).orElseThrow(
                ()->new IllegalStateException("actual identical family obligations contract was not installed"));}
    }
}
