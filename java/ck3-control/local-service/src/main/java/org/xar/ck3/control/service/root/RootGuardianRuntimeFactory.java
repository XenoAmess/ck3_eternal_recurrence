package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Constructs the one actual guardian ordinary preparer/effect/archive and its pure canonical query supplier per physical Root. */
public final class RootGuardianRuntimeFactory {
    private RootGuardianRuntimeFactory(){}
    public record Sources(RootOrdinaryClaimRuntime.Prepared claims,ExactRef preparation,ExactRef effects,ExactRef decoder,
            ExactRef reconciliationProfile,List<ExactRef> completeProducers) {
        public Sources {
            Objects.requireNonNull(claims);completeProducers=List.copyOf(completeProducers);
            StrictJson.require(!completeProducers.isEmpty()&&completeProducers.size()<=128
                    &&new HashSet<>(completeProducers).size()==completeProducers.size(),"complete unique actual guardian source closure required");
            for(var source:List.of(preparation,effects,decoder,reconciliationProfile))
                StrictJson.require(source.bytes()>0&&completeProducers.contains(source),"guardian implementation is outside its complete actual source closure");
            completeProducers.forEach(source->StrictJson.require(source.bytes()>0,"nonempty guardian producer source required"));
        }
    }
    /** Ordinary business configuration contains no already constructed claim or Guardian products. */
    public record OrdinaryConfiguration(Path writerLock) {
        public OrdinaryConfiguration {writerLock=Objects.requireNonNull(writerLock).toAbsolutePath().normalize();}
    }
    public record OrdinarySources(RootOrdinaryClaimRuntime.Sources claims,ExactRef preparation,ExactRef effects,
            ExactRef decoder,ExactRef reconciliationProfile,ExactRef ordinaryDefinition,ExactRef ordinaryReadDecoder,
            List<ExactRef> supportingProducers) {
        public OrdinarySources {
            Objects.requireNonNull(claims);Objects.requireNonNull(preparation);Objects.requireNonNull(effects);
            Objects.requireNonNull(decoder);Objects.requireNonNull(reconciliationProfile);Objects.requireNonNull(ordinaryDefinition);
            Objects.requireNonNull(ordinaryReadDecoder);supportingProducers=List.copyOf(supportingProducers);
        }
    }
    /** Creates the single shared claim Prepared once; Army supplies claim source metadata, not another claim product. */
    public static Prepared prepareOrdinary(OrdinaryConfiguration configuration,OrdinarySources sources) {
        Objects.requireNonNull(configuration);Objects.requireNonNull(sources);
        var complete=new java.util.LinkedHashSet<ExactRef>(sources.claims().completeProducers());
        complete.addAll(sources.supportingProducers());complete.addAll(List.of(sources.preparation(),sources.effects(),
                sources.decoder(),sources.reconciliationProfile(),sources.ordinaryDefinition(),sources.ordinaryReadDecoder()));
        var claims=RootOrdinaryClaimRuntime.prepareOrdinary(configuration.writerLock(),sources.claims());
        return new Prepared(new Sources(claims,sources.preparation(),sources.effects(),sources.decoder(),
                sources.reconciliationProfile(),List.copyOf(complete)),true);
    }
    private static final class Attempt {
        final KnownInteractionsRuntimeInstaller interactions;boolean entered;Installed installed;IOException failure;
        Attempt(KnownInteractionsRuntimeInstaller actual){interactions=actual;}
    }
    public static final class Prepared {
        private final Sources sources;
        private final boolean ordinary;
        private final Map<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(Sources sources){this(sources,false);}
        private Prepared(Sources sources,boolean ordinary){this.sources=Objects.requireNonNull(sources);this.ordinary=ordinary;}
        public Sources sources(){return sources;}
        /** Register before Core.open. Root may instead register this identical claims product directly, never a second importer. */
        public List<DomainBodies.Registration> domainRegistrations(){return sources.claims().domainRegistrations();}
        public synchronized void bindCore(RootApplicationAssembly.Core actual){
            StrictJson.require(core==null,"guardian Prepared binds its one actual original Core once");
            core=Objects.requireNonNull(actual);sources.claims().bindCore(actual);
        }
        public void importOriginal(RootRuntimeContext context,Session same,Instant deadline)throws IOException {
            requireCore(context);context.writer().requireSession(same);sources.claims().importOriginal(context,same,deadline);
        }
        public void initializeFresh(RootRuntimeContext context,Session same,FreshCampaignContext actual)throws IOException {
            requireCore(context);sources.claims().initializeFresh(context,same,actual);
        }
        private void requireCore(RootRuntimeContext context){
            StrictJson.require(core!=null&&context.core()==core,"guardian factory crossed its actual original Core/claim registration");
        }
        public synchronized Installed install(RootRuntimeContext context,KnownInteractionsRuntimeInstaller actualKnown)throws IOException {
            Objects.requireNonNull(context);Objects.requireNonNull(actualKnown);requireCore(context);actualKnown.requireContext(context);
            context.requireCurrent(context.clock().instant().plusSeconds(1));
            Attempt attempt=attempts.get(context);
            if(attempt==null){StrictJson.require(attempts.size()<64,"bounded actual guardian installation history required");attempt=new Attempt(actualKnown);attempts.put(context,attempt);}
            StrictJson.require(attempt.interactions==actualKnown,"same physical guardian cannot replace the actual shared ordinary query producer");
            if(attempt.installed!=null)return attempt.installed;
            if(attempt.entered)throw new IOException("partial actual guardian installation is not replayed",attempt.failure);
            attempt.entered=true;
            try {
                if(!ordinary) {
                for(Class<?> loaded:List.of(RootGuardianRuntimeFactory.class,RootGuardianReconciliationReads.class,GuardianOutgoingInstaller.class,
                        GuardianReconciliationQueries.class,GuardianOutgoingEffects.class,OrdinaryInitiationPreparation.class,GuardianOutgoingCodec.class))
                    context.game().launchPlan().sources().requireLoadedClass(loaded);
                for(var source:sources.completeProducers()) {
                    var witness=SharedSourceFiles.observe(Path.of(source.path()));
                    StrictJson.require(witness.source().bytes()==source.bytes()&&witness.source().sha256().equals(source.sha256()),
                            "guardian source pin changed before actual installation");
                    SharedSourceFiles.assertUnchanged(witness);
                }
                }
                var claimRuntime=sources.claims().install(context);claimRuntime.requireContext(context);
                var ordinary=actualKnown.definitions().ordinaryQuery();

                var queryReads=new RootGuardianReconciliationReads(context,ordinary,actualKnown.sources().qualifiedBuild(),
                        sources.reconciliationProfile(),sources.decoder());
                var products=new GuardianOutgoingInstaller(()->{
                    try{return context.transport();}catch(IOException failure){throw new UncheckedIOException(failure);}
                },()->context.adopted().observations(),actualKnown.sources().qualifiedBuild(),context.reads(),ordinary,claimRuntime.claims(),
                        context.archive(),context.frameLoader(),()->{
                    try{return context.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}
                },sources.effects(),sources.decoder(),queryReads.queries());
                queryReads.bind(products);
                var installed=new RootDomainInstallation("guardian-original-ordinary-send/v1",List.of(),queryReads.installedReads(),List.of(),
                        products.actions(),List.of(),products.archivedVerifiers(),List.of(),List.of(),List.of(),List.of(),java.util.Set.of(),
                        List.of(),List.of(),products.actions().stream().map(action->new RootDomainInstallation.FixedDomain(action,Domain.marriage)).toList(),
                        List.of(),List.of());
                attempt.installed=new Installed(context,actualKnown,claimRuntime,products,queryReads,installed);return attempt.installed;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual guardian original products are INCOMPLETE",failure);throw attempt.failure;}
        }
    }
    public record Installed(RootRuntimeContext context,KnownInteractionsRuntimeInstaller interactions,RootOrdinaryClaimRuntime.Installed claims,
            GuardianOutgoingInstaller products,RootGuardianReconciliationReads reads,RootDomainInstallation installation) {
        public Installed {
            Objects.requireNonNull(context);Objects.requireNonNull(interactions);Objects.requireNonNull(claims);Objects.requireNonNull(products);Objects.requireNonNull(reads);Objects.requireNonNull(installation);
            claims.requireContext(context);reads.requireContext(context);
        }
        public OrdinaryInitiationPreparation preparation(){return products.preparation();}
        public GuardianOutgoingEffects effects(){return products.effects();}
        public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return reads.reconciliationReads();}
        public List<NativeRecordedEvidenceVerifier.Binding> archivedVerifiers(){return products.archivedVerifiers();}
    }
}

