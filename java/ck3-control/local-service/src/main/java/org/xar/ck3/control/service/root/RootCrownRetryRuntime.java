package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.NativeCrownFinalTermsRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownfinalterms.CrownFinalTerms;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** One Core-lifetime retry producer; each physical Game uses its installed native contracts and current Driver. */
public final class RootCrownRetryRuntime {
    public static final String BODY_SCHEMA="xar.ck3.crown-authority-formal/v1";
    private RootCrownRetryRuntime() { }
    public record Sources(ExactRef implementation,List<ExactRef> runtimeSources,List<ExactRef> producerSources) {
        public Sources {
            Objects.requireNonNull(implementation);runtimeSources=List.copyOf(runtimeSources);producerSources=List.copyOf(producerSources);
            StrictJson.require(implementation.bytes()>0 && !runtimeSources.isEmpty() && runtimeSources.size()<=16
                    && !producerSources.isEmpty() && producerSources.size()<=32
                    && runtimeSources.stream().allMatch(ref->ref.bytes()>0) && producerSources.stream().allMatch(ref->ref.bytes()>0)
                    && producerSources.contains(implementation),"complete actual Crown retry implementation/runtime/producer source roles required");
        }
    }
    /** Pre-Core getters expose one service instance, never a proof or a clear-state default. */
    public static final class Prepared implements ContinuityStorePort {
        final Path lock;final Sources sources;
        private final CrownRetryPublication publication;
        private final CrownRetryDue due;
        private final RootCrownActualMaterialPort materials;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Installed> installations=new IdentityHashMap<>();
        private CrownRetryPublication.ImportProof retained;
        public Prepared(Path originalWriterLock,Sources actualSources) {
            lock=Objects.requireNonNull(originalWriterLock).toAbsolutePath().normalize();sources=Objects.requireNonNull(actualSources);
            materials=new RootCrownActualMaterialPort(this);
            publication=new CrownRetryPublication(lock,BODY_SCHEMA,sources.runtimeSources(),sources.producerSources(),materials,
                    (id,body)->core().archive().preserveArtifact(session(),body,CrownRetryPublication.MAX_BODY_BYTES));
            due=new CrownRetryDue(this,this::requireSession,publication);
        }
        public CrownRetryPublication pub() {return publication;}
        public CrownRetryDue due() {return due;}
        public Supplier<Optional<CrownRetryPublication.ImportProof>> retainedProof() {return this::proof;}
        private synchronized Optional<CrownRetryPublication.ImportProof> proof() {return Optional.ofNullable(retained);}
        synchronized void retain(CrownRetryPublication.ImportProof actual) {retained=Objects.requireNonNull(actual);}
        public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            StrictJson.require(core==null && Objects.requireNonNull(actual).archive().writer()==actual.writer()
                    && actual.writer().originalLockPath().equals(lock),"retry producer binds the exact original Core/writer/archive once");core=actual;
        }
        synchronized RootApplicationAssembly.Core core()throws IOException {
            if(core==null)throw new IOException("actual Crown retry Core is not bound");return core;
        }
        ContinuityStorePort.Session session()throws IOException {var same=core().writer().borrowedSession();requireSession(same);return same;}
        @Override public void requireSession(ContinuityStorePort.Session same)throws IOException {core().writer().requireSession(same);same.requireWriter(lock);}
        Installed active()throws IOException {
            var root=core().sessionAccess().current();
            StrictJson.require(!root.isRetired(),"retry producer requires the actual admitted Root session");
            List<Installed> candidates;synchronized(this){candidates=List.copyOf(installations.values());}
            for(var product:candidates)if(root.identity().game().equals(product.context.game().generation())
                    && root.identity().sessionId().equals(product.context.game().sessionId()) && root.driver()==product.context.adopted())return product;
            throw new IOException("actual admitted Root has no installed Crown retry runtime");
        }
        public synchronized Installed install(RootRuntimeContext actualContext,GovernanceRuntimeInstaller.Installed nativeGovernance)throws IOException {
            StrictJson.require(Objects.requireNonNull(actualContext).core()==core(),"retry installation must retain its original Core");
            Objects.requireNonNull(nativeGovernance);var existing=installations.get(actualContext);
            if(existing!=null){StrictJson.require(existing.nativeGovernance==nativeGovernance,"same retry context cannot replace its actual native contracts");return existing;}
            StrictJson.require(installations.size()<64,"finite actual physical retry installations exceeded");
            var candidate=new Installed(this,actualContext,nativeGovernance);installations.put(actualContext,candidate);return candidate;
        }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request)throws IOException {return core().writer().preview(request);}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared)throws IOException {return core().writer().commit(prepared);}
        @Override public ExactRef persistedHead()throws IOException {return core().writer().persistedHead();}
        @Override public <T>T locked(ContinuityStorePort.SessionWork<T> work)throws IOException {return core().writer().locked(work);}
    }
    private record Quote(PlanningRequest request,PlanningReadReceipt receipt,ExactRef receiptRef,ExactRef readback) { }
    private record Terms(PlanningRequest request,PlanningReadReceipt receipt,ExactRef receiptRef,ExactRef consume) { }
    public static final class Installed {
        final Prepared prepared;final RootRuntimeContext context;final GovernanceRuntimeInstaller.Installed nativeGovernance;
        private Quote quote;private Terms terms;
        private Installed(Prepared prepared,RootRuntimeContext context,GovernanceRuntimeInstaller.Installed nativeGovernance) {
            this.prepared=prepared;this.context=context;this.nativeGovernance=nativeGovernance;
        }
        public void requireStateDomains(GovernanceOrdinaryRuntimeInstaller.StateDomains domains) {
            StrictJson.require(domains.retryPublication()==prepared.pub() && domains.retryDue()==prepared.due(),
                    "ordinary policy and actual publisher must share the identical retry publication and Due producer");
        }
        private void current(PlanningRequest request)throws IOException {
            StrictJson.require(prepared.active()==this,"Crown observer belongs to a retired runtime");
            context.requireCurrent(request.deadline());prepared.requireSession(context.borrowedSession());
            StrictJson.require(request.before().game().equals(context.game().generation()) && request.source().equals(context.source())
                    && request.sessionId().equals(context.game().sessionId()),"Crown request crossed its actual current source/Game/session");
        }
        /** The same final-terms query feeds the clock and retains the full law payload, including absent-clock results. */
        public GovernanceCollector.CrownCooldownReadPort clockReads() {
            return request->{
                try {
                    current(request);var same=prepared.session();var contract=nativeGovernance.crownFinalTermsRead().contract();
                    var read=context.reads().read(same,contract,new PlanningReadRequest(request.before(),request.source(),request.sessionId(),
                            contract.operation(),new OpportunityJson.Obj(Map.of()),request.deadline()));
                    if(read instanceof PlanningReadResult.Unavailable<NativeCrownFinalTermsRead.Terms> missing)return new Unavailable<>(missing.reason());
                    var known=(PlanningReadResult.Known<NativeCrownFinalTermsRead.Terms>)read;
                    var archive=context.archive().withSession(same);var original=archive.loadRead(known.originalReceipt());
                    StrictJson.require(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt()),"retained final-terms receipt differs from actual query readback");
                    var decoded=nativeGovernance.crownFinalTermsRead().consumeTerms(original);
                    StrictJson.require(Arrays.equals(decoded.completeConsume().bytes(),known.value().completeConsume().bytes())
                            && decoded.clock().equals(known.value().clock()),"installed full final-terms decoder changed actual result");
                    if(decoded.readback().build()!=CrownFinalTerms.Build.CK3_12004) {
                        synchronized(this){terms=null;}
                        return new Unavailable<>("native calendar retry projection is not qualified for this exact game build");
                    }
                    var consume=archive.preserveMaterial(decoded.completeConsume());
                    synchronized(this) {terms=new Terms(request,original,known.originalReceipt(),consume);}
                    if(decoded.clock().isEmpty())return new Unavailable<>("complete native law material has no qualified .4 cooldown observer");
                    return new Known<>(decoded.clock().orElseThrow(),List.of(known.originalReceipt(),contract.sourceRef()));
                }catch(IOException failure){return new Unavailable<>("actual Crown final-terms query unavailable: "+failure.getMessage());}
            };
        }
        /** Observe the actual returned Crown read; no second Crown query is issued by the publisher. */
        public GovernanceObservationSupplier observe(GovernanceObservationSupplier delegate) {
            Objects.requireNonNull(delegate);
            return new GovernanceObservationSupplier() {
                @Override public Read<Crown> crown(PlanningRequest request) {
                    Read<Crown> result=delegate.crown(request);
                    if(result instanceof Known<Crown> known)try {
                        current(request);var same=prepared.session();var archive=context.archive().withSession(same);
                        var receiptRef=known.originals().getFirst();var receipt=archive.loadRead(receiptRef);
                        var contract=nativeGovernance.planningReads().crown();
                        StrictJson.require(receipt.contractId().equals(contract.contractId()) && receipt.request().before().equals(request.before())
                                && receipt.request().source().equals(request.source()) && receipt.request().sessionId().equals(request.sessionId()),"actual Crown quote original receipt/frame required");
                        var decoded=contract.decode(receipt);
                        StrictJson.require(decoded.equals(known.value().originalReadback()),"actual Crown quote decoder differs from retained returned policy input");
                        var raw=new RawJson(OpportunityJson.encode(decoded));var ref=archive.preserveMaterial(raw);
                        synchronized(Installed.this) {quote=new Quote(request,receipt,receiptRef,ref);terms=null;}
                    }catch(IOException failure){throw new UncheckedIOException("actual Crown quote custody failed",failure);}
                    return result;
                }
                @Override public Read<Durable> durable(PlanningRequest r){return delegate.durable(r);}
                @Override public Read<Life> lifestyle(PlanningRequest r,String f,boolean o){return delegate.lifestyle(r,f,o);}
                @Override public Read<OpeningComparison> openingComparison(PlanningRequest r){return delegate.openingComparison(r);}
                @Override public Read<CouncilSelection.Query> council(PlanningRequest r,CouncilSelection.Position p){return delegate.council(r,p);}
                @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest r){return delegate.coreCouncil(r);}
                @Override public Read<CouncilRoot> councilRoot(PlanningRequest r){return delegate.councilRoot(r);}
                @Override public Read<CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest r,String law){return delegate.crownRetry(r,law);}
                @Override public Read<CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest r){return delegate.crownCooldown(r);}
                @Override public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest r){return delegate.crownRetryDue(r);}
            };
        }
        /** Called by the existing READ-first completion only after the actual observation freeze has exited. */
        public OrdinaryPlanCompletion completion(OrdinaryPlanCompletion downstream) {
            Objects.requireNonNull(downstream);
            return new OrdinaryPlanCompletion() {
                @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
                    try {
                        var same=prepared.session();var changed=publish(same,original);
                        return changed.<PlanningDisposition>map(value->value).orElseGet(()->downstream.afterPlanning(original,planned));
                    }catch(IOException failure){throw new UncheckedIOException("actual Crown retry publication failed without query/action replay",failure);}
                }
                @Override public ExecutionDisposition afterExecution(ActionReceipt actual){return downstream.afterExecution(actual);}
            };
        }
        private Optional<OrdinaryPlanCompletion.Published> publish(ContinuityStorePort.Session same,PlanningRequest request)throws IOException {
            Quote q;Terms t;synchronized(this) {q=quote;t=terms;}
            if(q==null || t==null || q.request()!=request || t.request()!=request)return Optional.empty();
            current(request);prepared.requireSession(same);
            var before=same.readDomain(DomainBodies.Slot.CROWN);
            if(!(before instanceof DomainBodies.Available body))return Optional.empty();
            var input=context.collector().currentPlanning(same,request,request.deadline(),(exact,lease)->{
                StrictJson.require(exact==request,"retry capture requires the actual planning request instance");
                var query=t.receipt().after().binding().observed();
                return new CrownRetryPublication.Input(lease.frame().identity(),query,lease.frame().source(),body.reference().payload(),
                        q.readback(),q.receiptRef(),t.consume(),t.receiptRef(),prepared.sources.runtimeSources());
            });
            var head=same.head();var material=prepared.materials.capture(head,input,request.deadline());var after=CrownRetryPublication.reduce(input,material);
            if(Arrays.equals(after,body.canonicalBody())) {
                var retained=prepared.proof();
                if(retained.isPresent())prepared.pub().requireCurrentPublication(retained.orElseThrow(),same,input.currentObserved(),input.source(),request.deadline());
                synchronized(this){if(quote==q){quote=null;terms=null;}}
                return Optional.empty();
            }
            var proof=prepared.pub().publish(same,input,request.deadline());prepared.retain(proof);
            synchronized(this){if(quote==q){quote=null;terms=null;}}
            return Optional.of(new OrdinaryPlanCompletion.Published(head,proof.committed()));
        }
    }
}
