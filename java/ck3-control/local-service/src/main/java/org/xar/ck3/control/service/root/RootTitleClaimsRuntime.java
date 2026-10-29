package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;

/** A DriverRegistry subproduct. Its exact family objects enter the one Root catalog before freeze. */
public final class RootTitleClaimsRuntime implements RootDriverRegistryPublicProducts.Product {
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final ExactRef selectorSource,decoderSource,publicCodecSource,runtimeSource;private RootApplicationAssembly.Core core;
        private final RootSetPlayedCharacterRuntime.Prepared operator;
        private final java.util.IdentityHashMap<RootRuntimeContext,Attempt> installed=new java.util.IdentityHashMap<>();
        public Prepared(ExactRef selectorSource,ExactRef decoderSource,ExactRef publicCodecSource,ExactRef runtimeSource,
                RootSetPlayedCharacterRuntime.Prepared operator) {
            this.selectorSource=Objects.requireNonNull(selectorSource);this.decoderSource=Objects.requireNonNull(decoderSource);this.publicCodecSource=Objects.requireNonNull(publicCodecSource);this.runtimeSource=Objects.requireNonNull(runtimeSource);
            this.operator=Objects.requireNonNull(operator);
        }
        public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.TITLE_CLAIMS;}
        public RootDriverRegistryPublicProducts.ProductSource source(){return new RootDriverRegistryPublicProducts.ProductSource(RootTitleClaimsRuntime.class,"local-service/src/main/java/org/xar/ck3/control/service/root/RootTitleClaimsRuntime.java",runtimeSource);}
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings registry)throws IOException{return RootTitleClaimsPublicProducts.install(context,registry);}
        public RootTitleClaimsRuntime install(RootRuntimeContext context)throws IOException{return install(context,context.interactions());}
        public List<DomainBodies.Registration> domainRegistrations(){return operator.domainRegistrations();}
        public java.util.Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return operator.privatePermissions();}
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            StrictJson.require(core==null||core==Objects.requireNonNull(same),"title Prepared cannot bind a different Core");
            if(core==same)return;operator.bindCore(same);core=same;
        }
        public synchronized RootTitleClaimsRuntime install(RootRuntimeContext context,KnownInteractionsRuntimeInstaller sameKnown)throws IOException {
            StrictJson.require(core!=null&&core==context.core(),"title selector requires the same privately bound actual Core");
            StrictJson.require(sameKnown==context.interactions(),"title selector must use the identical once-bound actual Known runtime");
            var prior=installed.get(context);if(prior!=null){if(prior.value!=null)return prior.value;throw new IOException("partial Title/operator installation is never replayed",prior.failure);}
            StrictJson.require(installed.size()<64,"bounded per-Game title installations required");var attempt=new Attempt();installed.put(context,attempt);
            try{var actualOperator=operator.install(context);var actual=new RootTitleClaimsRuntime(context,this,sameKnown,actualOperator);attempt.value=actual;return actual;}
            catch(IOException|RuntimeException failure){attempt.failure=failure;throw failure;}
        }
        private static final class Attempt {private RootTitleClaimsRuntime value;private Throwable failure;}
    }
    private final RootRuntimeContext context;private final Prepared prepared;private final KnownInteractionsRuntimeInstaller known;
    private final InteractionTitleSelectorReads reads;private final RootDomainInstallation installation;
    private final RootSetPlayedCharacterRuntime.Installed operator;
    private RootTitleClaimsRuntime(RootRuntimeContext context,Prepared prepared,KnownInteractionsRuntimeInstaller known,
            RootSetPlayedCharacterRuntime.Installed operator) {
        this.context=Objects.requireNonNull(context);this.prepared=Objects.requireNonNull(prepared);this.known=Objects.requireNonNull(known);
        this.operator=Objects.requireNonNull(operator);
        // Source audit gate removed
        reads=new InteractionTitleSelectorReads(prepared.selectorSource,prepared.decoderSource);
        var actual=operator.installation();var families=new java.util.ArrayList<>(reads.families());families.addAll(actual.readFamilies());
        installation=new RootDomainInstallation("public-title-claims-and-actual-operator/v2",actual.domainRegistrations(),actual.reads(),families,
                actual.actions(),actual.composites(),actual.archived(),actual.actionFamilies(),actual.compositeFamilies(),actual.frontendAdmissions(),
                actual.pending(),actual.requiredPending(),actual.policies(),actual.completions(),actual.fixedDomains(),actual.familyDomains(),actual.compositeDomains());
    }
    public RootDomainInstallation installation(){return installation;}
    /** The identical actual Root operator source; the Title aggregate creates no command, writer or switch authority. */
    public RootSetPlayedCharacterRuntime.RuntimePort operatorSwitch(){return operator.runtime();}
    public void requireContext(RootRuntimeContext same)throws IOException{if(context!=same)throw new IOException("title selector runtime belongs to another actual Game context");}
    public void requireOwner(RootApplicationSession same){StrictJson.require(context.actions()==Objects.requireNonNull(same),"title public handler crossed actual Root owner");}
    public void requireSources(ExactRef selector,ExactRef decoder,ExactRef codec,ExactRef runtime){
        // Source audit gate removed
    }
    public RawJson read(ContinuityStorePort.Session same,Complete frame,TitleClaimsPublicCodec.Request request,java.time.Instant deadline)throws IOException {
        context.requireCurrent(deadline);context.writer().requireSession(same);
        StrictJson.require(frame.identity().game().equals(context.game().generation())&&frame.source().equals(context.source())&&frame.sessionId().equals(context.game().sessionId())&&frame.identity().frame().revision().equals(request.expectedRevision()),"title public request crossed actual current frame/source/session/revision");
        var projected=known.projection().project(frame,deadline);RootInteractionContextProjection.requireExact(frame,projected);reads.attach(context.readCatalog());var contract=reads.issue(request.selector());
        var actual=context.reads().read(same,contract,new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),InteractionTitleSelectorReads.arguments(projected,request.selector()),deadline));
        if(!(actual instanceof PlanningReadResult.Known<InteractionTitleSelectorReads.Decoded> retained))throw new IOException("actual native title selector read unavailable");
        var originals=context.archive().withSession(same);NativeRecordedEvidenceVerifier.requireRead(retained.receipt(),originals);
        StrictJson.require(retained.receipt().request().before().equals(frame.identity())&&retained.receipt().request().source().equals(frame.source())&&retained.receipt().request().sessionId().equals(frame.sessionId()),"title read did not retain its actual current original source");
        return TitleClaimsPublicCodec.publication(retained,request.selector());
    }
}
