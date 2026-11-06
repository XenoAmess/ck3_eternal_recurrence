package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Root planning completion. Read publication is outside Driver freeze and inside the original writer scope. */
public final class RootReadPublicationCompletion implements OrdinaryPlanCompletion.PlanningScope {
    private static final int POLICY_COUNT=org.xar.ck3.control.application.planning.PlanningStage.values().length;
    private static final int PHASE_OFFSET=14+3*POLICY_COUNT;
    private static final int PHASE_COUNT=4;
    private final RootApplicationAssembly.Core core;
    private final DriverReadHistoryPublisher reads;
    private final OrdinaryPlanCompletion downstream;
    private final org.xar.ck3.control.application.readiness.NativeReadinessCollector collector;
    private static final class PlanningRound {
        private final ContinuityStorePort.Session session;private boolean flushFailed;
        private final long[] timing;
        private Optional<Published> readPublication=Optional.empty();
        private PreparedSelection preparedSelection;
        private PlanningRound(ContinuityStorePort.Session session,long[] timing){this.session=session;this.timing=timing;}
    }
    /** Same-round DATA only; a domain publication is not a Driver READ publication. */
    private record PreparedSelection(PlanningRequest request, PlanningDisposition actual) {
        private PreparedSelection {
            Objects.requireNonNull(request); Objects.requireNonNull(actual);
            StrictJson.require(actual instanceof Published || actual instanceof Blocked,
                    "only a completed changed or blocked selection preparation is retained");
        }
    }
    /** A completed physical-read failure leaves the writer callback as DATA, so writer release errors remain primary. */
    private record ScopeExit<T>(Optional<ScopeResult<T>> result,
            Optional<org.xar.ck3.control.application.planning.PlanningReadFailure> readFailure) {
        private ScopeExit {Objects.requireNonNull(result);Objects.requireNonNull(readFailure);StrictJson.require(result.isPresent()!=readFailure.isPresent(),"one original scope outcome required");}
        private ScopeResult<T> released() throws IOException {
            if(readFailure.isPresent())throw readFailure.orElseThrow();
            return result.orElseThrow();
        }
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
        // A scope-presence bit only suppresses diagnostics; it never authorizes borrowing or proves unlock.
        long[] timing=core.writer().hasCurrentThreadWriterScope()?null:
                new long[PHASE_OFFSET+5*PHASE_COUNT];
        long started=timing==null?0L:System.nanoTime();boolean coreReturned=false;
        try {
            ScopeExit<T> actual=core.withBorrowed(()->{
                if(timing!=null)timing[1]=System.nanoTime()-started;
                ContinuityStorePort.Session borrowed=core.writer().borrowedSession();core.writer().requireSession(borrowed);
                PlanningRound current=new PlanningRound(borrowed,timing);round.set(current);
                try { return new ScopeExit<T>(Optional.of(collector.withPlanningRound(borrowed,()->finishPlanningReads(()->{
                    current.readPublication=Optional.empty();
                    current.preparedSelection=null;
                    return finishOriginalWork(()->timedPlanningWork(work,timing),()->flushInSession(borrowed),()->current.flushFailed);
                },()->current.readPublication.isPresent(),()->timedReadReplan(borrowed,timing)))),Optional.empty()); }
                catch(org.xar.ck3.control.application.planning.PlanningReadFailure failure) {
                    if(!org.xar.ck3.control.application.planning.PlanningReadFailure.hasCompletedPublication(failure))throw failure;
                    return new ScopeExit<T>(Optional.empty(),Optional.of(failure));
                }
                finally{round.remove();}
            });
            coreReturned=true;
            return actual.released();
        } finally {
            // Normal return of this own-scope Core call proves its Windows lock close succeeded.
            // Core throws (including close failure), and inherited scopes, deliberately emit nothing.
            if(timing!=null&&coreReturned){timing[0]=System.nanoTime()-started;logMethodTiming(timing);}
        }
    }
    @FunctionalInterface interface PublicationFlush { Optional<Published> flush()throws IOException; }
    @FunctionalInterface interface ReadReplan { boolean prepare()throws IOException; }
    /** Only successful real READ commits request another work pass; writer failures never enter this loop. */
    static <T> ScopeResult<T> finishPlanningReads(ScopeWork<ScopeResult<T>> work,
            java.util.function.BooleanSupplier readPublished,ReadReplan replan)throws IOException,InterruptedException {
        for(;;) {
            ScopeResult<T> completed=work.run();
            if(!readPublished.getAsBoolean()||!replan.prepare())return completed;
        }
    }
    /** Same production control flow; package-only for failure-preservation regression, never source/Ready authority. */
    static <T> ScopeResult<T> finishOriginalWork(ScopeWork<T> work,PublicationFlush publication,java.util.function.BooleanSupplier alreadyFailed)
            throws IOException,InterruptedException {
        T result;
        try { result=Objects.requireNonNull(work.run(),"actual planning round result required"); }
        catch(IOException|InterruptedException|RuntimeException|Error failure) {
            // The work's physical freeze has exited before this original writer callback runs.
            boolean publicationCompleted=false;
            if(!alreadyFailed.getAsBoolean())try { publication.flush(); publicationCompleted=true; }
            catch(IOException|RuntimeException|Error publicationFailure) {
                if(publicationFailure!=failure)failure.addSuppressed(publicationFailure);
            }
            if(publicationCompleted) {
                var readFailure=org.xar.ck3.control.application.planning.PlanningReadFailure.afterPublication(failure);
                if(readFailure.isPresent())throw readFailure.orElseThrow();
            }
            throw failure;
        }
        // A normal publication failure is outside the work catch and is never retried here.
        return new ScopeResult<>(result,publication.flush());
    }
    /** Root public-query/action edges call this only after their original Driver freeze has exited. */
    public Optional<Published> flushInSession(ContinuityStorePort.Session borrowed) throws IOException {
        PlanningRound current=round.get();
        long[] timing=current!=null&&current.session==borrowed?current.timing:null;
        if(timing==null)return flushOriginalInSession(borrowed);
        timing[5]++;long started=System.nanoTime();
        try {var result=flushOriginalInSession(borrowed);timing[6]++;return result;}
        finally {timing[7]+=System.nanoTime()-started;}
    }
    private Optional<Published> flushOriginalInSession(ContinuityStorePort.Session borrowed) throws IOException {
        try {
            core.writer().requireSession(borrowed);
            Optional<Published> actual=reads.flushActualReads(borrowed).map(committed->new Published(committed.predecessor(),committed.actual()));
            PlanningRound current=round.get();
            if(current!=null&&current.session==borrowed&&actual.isPresent())current.readPublication=actual;
            return actual;
        }catch(IOException|RuntimeException|Error failure) {
            PlanningRound current=round.get();
            if(current!=null&&current.session==borrowed)current.flushFailed=true;
            throw failure;
        }
    }
    @Override public Optional<Published> beforeSelection(PlanningRequest original,PlanningResult.ActionSelected proposed) {
        Objects.requireNonNull(original);Objects.requireNonNull(proposed);
        try {
            ContinuityStorePort.Session borrowed=core.writer().borrowedSession();
            StrictJson.require(round.get()!=null&&round.get().session==borrowed,"pre-selection publication must retain its actual writer scope");
            return flushInSession(borrowed);
        }catch(IOException failure){throw new UncheckedIOException("actual preparatory read publication failed; no model/action dispatch",failure);}
    }
    @Override public SelectionDisposition beforeModel(PlanningRequest original,PlanningResult.ActionSelected proposed) {
        Objects.requireNonNull(original); Objects.requireNonNull(proposed);
        try {
            ContinuityStorePort.Session borrowed=core.writer().borrowedSession();
            PlanningRound current=round.get();
            StrictJson.require(current!=null&&current.session==borrowed,
                    "pre-model preparation must retain its actual original writer round");
            core.writer().requireSession(borrowed);
            StrictJson.require(current.readPublication.isEmpty()&&current.preparedSelection==null,
                    "pre-model preparation requires the completed READ barrier and one actual proposal");
            long[] timing=current.timing;long started=timing==null?0L:System.nanoTime();
            if(timing!=null)timing[8]++;
            SelectionDisposition raw;
            try {raw=downstream.beforeModel(original,proposed);if(timing!=null)timing[9]++;}
            finally {if(timing!=null)timing[10]+=System.nanoTime()-started;}
            SelectionDisposition actual=Objects.requireNonNull(raw);
            if(actual instanceof Published published)current.preparedSelection=new PreparedSelection(original,published);
            else if(actual instanceof Blocked blocked)current.preparedSelection=new PreparedSelection(original,blocked);
            return actual;
        } catch(IOException failure) {
            throw new UncheckedIOException("actual pre-model writer preparation failed; no model/action dispatch",failure);
        }
    }
    @Override public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned) {
        Objects.requireNonNull(original);Objects.requireNonNull(planned);
        logPlanningOperation("ENTER", original, planned);
        try {
            ContinuityStorePort.Session borrowed=core.writer().borrowedSession();
            StrictJson.require(round.get()!=null&&round.get().session==borrowed,"planning completion must retain its original live writer callback");
            PlanningDisposition disposition;
            PreparedSelection prepared=round.get().preparedSelection;
            if(prepared!=null) {
                StrictJson.require(prepared.request()==original&&planned.trace().before().equals(original.before()),
                        "pre-model completion cannot cross its exact original request or frame");
                disposition=prepared.actual();
            } else {
                Optional<Published> changed=round.get().readPublication;
                if(changed.isEmpty())changed=flushInSession(borrowed);
                if(changed.isPresent())disposition=changed.orElseThrow(); // Domain publication waits for the new complete observation.
                else disposition=Objects.requireNonNull(downstream.afterPlanning(original,planned),"actual domain planning disposition required");
            }
            logPlanningOperation("RETURN", original, planned, disposition);
            return disposition;
        }catch(IOException failure){throw new UncheckedIOException("actual read publication failed; original query is retained without replay",failure);}
    }

    @Override public void policyEvaluationTiming(int stageOrdinal,long elapsedNanos,boolean returned) {
        PlanningRound current=round.get();long[] timing=current==null?null:current.timing;
        if(timing==null||stageOrdinal<0||stageOrdinal>=POLICY_COUNT||elapsedNanos<0)return;
        int offset=14+stageOrdinal*3;timing[offset]++;
        if(returned)timing[offset+1]++;
        timing[offset+2]+=elapsedNanos;
    }
    @Override public void phaseSpanTiming(int phaseOrdinal,int terminalOrdinal,long elapsedNanos) {
        PlanningRound current=round.get();long[] timing=current==null?null:current.timing;
        if(timing==null||elapsedNanos<0)return;
        var returned=org.xar.ck3.control.application.session.BatchReport.PhaseTerminal.RETURNED.ordinal();
        var failed=org.xar.ck3.control.application.session.BatchReport.PhaseTerminal.FAILED.ordinal();
        var interrupted=org.xar.ck3.control.application.session.BatchReport.PhaseTerminal.INTERRUPTED.ordinal();
        if(terminalOrdinal!=returned&&terminalOrdinal!=failed&&terminalOrdinal!=interrupted)return;
        int slot=phaseOrdinal==org.xar.ck3.control.application.session.BatchReport.Phase.OBSERVATION.ordinal()?0:
                phaseOrdinal==org.xar.ck3.control.application.session.BatchReport.Phase.PLANNING.ordinal()?1:
                phaseOrdinal==org.xar.ck3.control.application.session.BatchReport.Phase.OUTCOME_CONSUMPTION.ordinal()?2:
                phaseOrdinal==org.xar.ck3.control.application.session.BatchReport.Phase.IDLE_WAIT.ordinal()?3:-1;
        if(slot<0)return;
        int offset=PHASE_OFFSET+slot*5;timing[offset]++;
        if(terminalOrdinal==returned)timing[offset+1]++;
        else if(terminalOrdinal==failed)timing[offset+2]++;
        else timing[offset+3]++;
        timing[offset+4]+=elapsedNanos;
    }

    private static <T> T timedPlanningWork(ScopeWork<T> work,long[] timing) throws IOException,InterruptedException {
        if(timing==null)return work.run();
        timing[2]++;long started=System.nanoTime();
        try {T result=work.run();timing[3]++;return result;}
        finally {timing[4]+=System.nanoTime()-started;}
    }
    private boolean timedReadReplan(ContinuityStorePort.Session borrowed,long[] timing) throws IOException {
        if(timing==null)return collector.prepareReadPublicationReplan(borrowed);
        timing[11]++;long started=System.nanoTime();
        try {boolean result=collector.prepareReadPublicationReplan(borrowed);timing[12]++;return result;}
        finally {timing[13]+=System.nanoTime()-started;}
    }
    /** Inclusive method wall times only; called once after a normally released own writer scope. */
    private static void logMethodTiming(long[] timing) {
        try {
            ObjectNode row=StrictJson.object().put("schema","xar.java-planning-method-timing/v1")
                    .put("emitted_at_epoch_ms",System.currentTimeMillis())
                    .put("scope_elapsed_ns",timing[0]).put("pre_callback_elapsed_ns",timing[1])
                    .put("work_enter_count",timing[2]).put("work_return_count",timing[3]).put("work_elapsed_ns",timing[4])
                    .put("flush_enter_count",timing[5]).put("flush_return_count",timing[6]).put("flush_elapsed_ns",timing[7])
                    .put("before_model_enter_count",timing[8]).put("before_model_return_count",timing[9]).put("before_model_elapsed_ns",timing[10])
                    .put("replan_enter_count",timing[11]).put("replan_return_count",timing[12]).put("replan_elapsed_ns",timing[13]);
            var policies=row.putArray("policy_evaluations");
            for(int offset=14;offset<PHASE_OFFSET;offset+=3) {
                if(timing[offset]==0)continue;
                policies.addObject().put("stage_ordinal",(offset-14)/3)
                        .put("enter_count",timing[offset]).put("return_count",timing[offset+1])
                        .put("failed_count",timing[offset]-timing[offset+1]).put("elapsed_ns",timing[offset+2]);
            }
            var phases=row.putArray("controller_phase_spans");
            String[] names={"OBSERVATION","PLANNING","OUTCOME_CONSUMPTION","IDLE_WAIT"};
            int[] ordinals={org.xar.ck3.control.application.session.BatchReport.Phase.OBSERVATION.ordinal(),
                    org.xar.ck3.control.application.session.BatchReport.Phase.PLANNING.ordinal(),
                    org.xar.ck3.control.application.session.BatchReport.Phase.OUTCOME_CONSUMPTION.ordinal(),
                    org.xar.ck3.control.application.session.BatchReport.Phase.IDLE_WAIT.ordinal()};
            for(int slot=0;slot<PHASE_COUNT;slot++) {
                int offset=PHASE_OFFSET+slot*5;if(timing[offset]==0)continue;
                phases.addObject().put("phase_ordinal",ordinals[slot]).put("phase",names[slot])
                        .put("sample_count",timing[offset]).put("return_count",timing[offset+1])
                        .put("failed_count",timing[offset+2]).put("interrupted_count",timing[offset+3]).put("elapsed_ns",timing[offset+4]);
            }
            byte[] canonical=StrictJson.canonical(row,8192);
            System.out.write(canonical);System.out.write(10);System.out.flush();
        } catch(Throwable ignored) {
            // Diagnostics never replace the original result/error or mutate interruption/suppression.
        }
    }

    private void logPlanningOperation(String phase, PlanningRequest original, PlanningResult planned, PlanningDisposition... disposition) {
        try {
            ObjectNode row = StrictJson.object()
                .put("schema", "xar.java-ordinary-planning-operation/v1")
                .put("observed_at_utc", java.time.Instant.now().toString())
                .put("phase", phase)
                .put("result_class", planned.getClass().getSimpleName());

            // Result specific details
            if (planned instanceof PlanningResult.Stopped stopped) {
                row.put("reason", stopped.reason().name());
                row.put("detail", truncate(stopped.detail(), 1024));
            } else if (planned instanceof PlanningResult.ReadOnlyWait wait) {
                row.put("reason", truncate(wait.reason(), 1024));
            } else if (planned instanceof PlanningResult.RefreshRequired refresh) {
                row.put("reason", truncate(refresh.reason(), 1024));
            } else if (planned instanceof PlanningResult.ActionSelected selected) {
                selected.trace().finalPlan().ifPresent(plan -> row.put("reason", truncate(plan.reason(), 1024)));
            } else if (planned instanceof PlanningResult.ExistingActionReconciliation recon) {
                row.put("action_id", recon.actionId());
            } else if (planned instanceof PlanningResult.IncompleteMigration migration) {
                migration.missingStages().forEach(stage -> row.withArray("missing_stages").add(stage.name()));
            }

            // Last visited stage/outcome
            var visits = planned.trace().visits();
            row.putNull("last_stage");
            row.putNull("last_outcome");
            if (!visits.isEmpty()) {
                PlanTrace.StageVisit last = visits.get(visits.size() - 1);
                row.put("last_stage", last.stage().name());
                row.put("last_outcome", last.outcome().name());
            }

            // Before frame identity
            var before = planned.trace().before().frame();
            row.put("before_revision", before.revision().toString());
            row.put("before_native_revision", before.identity().nativeRevision().toString());
            row.put("before_actor_character_id", before.identity().player().toString());
            row.put("before_date_raw", before.identity().dateRaw().toString());
            row.put("before_snapshot_id", truncate(before.snapshotId(), 1024));
            row.put("before_episode", truncate(before.episodeRunId(), 1024));

            // Round state
            PlanningRound current = round.get();
            if (current != null) {
                row.put("round_read_present", current.readPublication.isPresent());
                row.put("round_flush_failed", current.flushFailed);
            }

            // Disposition (if RETURN phase)
            if (disposition.length > 0 && disposition[0] != null) {
                row.put("disposition_class", disposition[0].getClass().getSimpleName());
            }

            byte[] canonical = StrictJson.canonical(row, 8192);
            System.out.write(canonical);
            System.out.write(10);
            System.out.flush();
        } catch (Exception ignored) {
            // Best effort logging; never alter business flow
        }
    }

    private static String truncate(String value, int max) {
        if (value == null) return null;
        if (value.length() <= max) return value;
        return value.substring(0, max);
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
