package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Root planning completion. Read publication is outside Driver freeze and inside the original writer scope. */
public final class RootReadPublicationCompletion implements OrdinaryPlanCompletion.PlanningScope {
    private final RootApplicationAssembly.Core core;
    private final DriverReadHistoryPublisher reads;
    private final OrdinaryPlanCompletion downstream;
    private final org.xar.ck3.control.application.readiness.NativeReadinessCollector collector;
    private static final class PlanningRound {
        private final ContinuityStorePort.Session session;private boolean flushFailed;
        private PlanningRound(ContinuityStorePort.Session session){this.session=session;}
    }
    private final ThreadLocal<PlanningRound> round=new ThreadLocal<>();
    public RootReadPublicationCompletion(RootApplicationAssembly.Core originalCore,DriverReadHistoryPublisher actualReadPublisher,
            OrdinaryPlanCompletion actualDomainCompletion,org.xar.ck3.control.application.readiness.NativeReadinessCollector actualCollector) {
        core=Objects.requireNonNull(originalCore);reads=Objects.requireNonNull(actualReadPublisher);
        downstream=Objects.requireNonNull(actualDomainCompletion);collector=Objects.requireNonNull(actualCollector);
        StrictJson.require(downstream!=this,"Root read completion cannot delegate to itself");
    }
    @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException,InterruptedException {
        Objects.requireNonNull(work);StrictJson.require(round.get()==null,"one actual original-writer planning round per thread");
        return core.withBorrowed(()->{
            ContinuityStorePort.Session borrowed=core.writer().borrowedSession();core.writer().requireSession(borrowed);
            PlanningRound current=new PlanningRound(borrowed);round.set(current);
            try { return finishOriginalWork(()->collector.withPlanningRound(borrowed,work::run),()->flushInSession(borrowed),()->current.flushFailed); }
            finally{round.remove();}
        });
    }
    @FunctionalInterface interface PublicationFlush { Optional<Published> flush()throws IOException; }
    /** Same production control flow; package-only for failure-preservation regression, never source/Ready authority. */
    static <T> ScopeResult<T> finishOriginalWork(ScopeWork<T> work,PublicationFlush publication,java.util.function.BooleanSupplier alreadyFailed)
            throws IOException,InterruptedException {
        T result;
        try { result=Objects.requireNonNull(work.run(),"actual planning round result required"); }
        catch(IOException|InterruptedException|RuntimeException|Error failure) {
            // The work's physical freeze has exited before this original writer callback runs.
            if(!alreadyFailed.getAsBoolean())try { publication.flush(); }
            catch(IOException|RuntimeException|Error publicationFailure) {
                if(publicationFailure!=failure)failure.addSuppressed(publicationFailure);
            }
            throw failure;
        }
        // A normal publication failure is outside the work catch and is never retried here.
        return new ScopeResult<>(result,publication.flush());
    }
    /** Root public-query/action edges call this only after their original Driver freeze has exited. */
    public Optional<Published> flushInSession(ContinuityStorePort.Session borrowed) throws IOException {
        try {
            core.writer().requireSession(borrowed);
            return reads.flushActualReads(borrowed).map(committed->new Published(committed.predecessor(),committed.actual()));
        }catch(IOException|RuntimeException|Error failure) {
            PlanningRound current=round.get();
            if(current!=null&&current.session==borrowed)current.flushFailed=true;
            throw failure;
        }
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
        Objects.requireNonNull(original);Objects.requireNonNull(planned);
        try {
            ContinuityStorePort.Session borrowed=core.writer().borrowedSession();
            StrictJson.require(round.get()!=null&&round.get().session==borrowed,"planning completion must retain its original live writer callback");
            Optional<Published> changed=flushInSession(borrowed);
            if(changed.isPresent())return changed.orElseThrow(); // Domain publication waits for the new complete observation.
            return Objects.requireNonNull(downstream.afterPlanning(original,planned),"actual domain planning disposition required");
        }catch(IOException failure){throw new UncheckedIOException("actual read publication failed; original query is retained without replay",failure);}
    }
    @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
        Objects.requireNonNull(actual);
        try {
            return core.withBorrowed(()->{
                ContinuityStorePort.Session borrowed=core.writer().borrowedSession();
                Optional<Published> before=flushInSession(borrowed);
                // Every original ordinary outcome, including UNKNOWN, still reaches its sole actual domain consumer once.
                ExecutionDisposition consumed=Objects.requireNonNull(downstream.afterExecution(actual),"actual domain execution disposition required");
                Optional<Published> after=flushInSession(borrowed);
                if(consumed instanceof Blocked||consumed instanceof Published)return consumed;
                if(after.isPresent())return after.orElseThrow();
                return before.<ExecutionDisposition>map(value->value).orElse(consumed);
            });
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("actual original-writer outcome completion interrupted; no replay",interrupted);}
        catch(IOException failure){throw new UncheckedIOException("actual read outcome publication failed; no action/query replay",failure);}
    }
}
