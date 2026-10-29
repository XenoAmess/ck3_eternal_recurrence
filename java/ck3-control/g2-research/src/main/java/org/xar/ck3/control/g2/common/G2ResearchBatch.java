package org.xar.ck3.control.g2.common;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.BatchDecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Terminal;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Tick;

/** One retained pure host batch. No native, source-reader, dispatcher or writer authority is created. */
public final class G2ResearchBatch {
    public record Evaluation(G2Response response, DecisionMetrics.Snapshot metrics) {
        public Evaluation { Objects.requireNonNull(response); Objects.requireNonNull(metrics); }
    }
    private final G2ResearchEngine engine;
    private final BatchDecisionMetrics.Context context;
    private final DecisionMetricRecorder.Clock clock;
    private final Thread owner = Thread.currentThread();
    private final Tick began;
    private final List<DecisionMetrics.Snapshot> requests = new ArrayList<>();
    private final Set<String> requestIds = new HashSet<>();
    private Terminal terminal = Terminal.RETURNED;
    private boolean failed;
    private boolean finished;

    public G2ResearchBatch(G2ResearchEngine engine, BatchDecisionMetrics.Context context, DecisionMetricRecorder.Clock clock) {
        this.engine = Objects.requireNonNull(engine); this.context = Objects.requireNonNull(context); this.clock = Objects.requireNonNull(clock);
        StrictJson.require(context.clockDomainId().equals(clock.domainId()), "retained original batch clock required");
        began = clock.now(); validateTick(began);
    }
    public Evaluation evaluate(G2Request request) {
        owner(); StrictJson.require(!finished && !failed, "closed or failed batch cannot continue or replay");
        Objects.requireNonNull(request);
        StrictJson.require(requestIds.add(request.requestId()), "request identity cannot replay inside retained batch");
        DecisionMetricRecorder recorder = new DecisionMetricRecorder(new DecisionMetrics.Context(context.machineId(), context.scopeId(),
                context.batchId(), request.requestId(), context.clockDomainId()), clock);
        try {
            G2Response response = engine.evaluate(request, recorder);
            DecisionMetrics.Snapshot metrics = recorder.snapshot(); requests.add(metrics);
            return new Evaluation(response, metrics);
        } catch (RuntimeException | Error failure) {
            failed = true; terminal = Terminal.UNKNOWN;
            try { requests.add(recorder.snapshot()); } catch (RuntimeException metricFailure) { failure.addSuppressed(metricFailure); }
            throw failure;
        }
    }
    /** Finish observes the original clock once; it never sums request spans or starts a new T0. */
    public BatchDecisionMetrics.Batch finish() {
        owner(); StrictJson.require(!finished, "batch already finished"); finished = true;
        Tick ended = clock.now(); validateTick(ended);
        return new BatchDecisionMetrics.Batch(context, new BatchDecisionMetrics.Window(began, ended, terminal), requests);
    }
    private void validateTick(Tick tick) {
        StrictJson.require(context.clockDomainId().equals(tick.clockDomainId()) && tick.threadId() == owner.threadId(),
                "batch tick changed original clock domain or owner thread");
    }
    private void owner() { StrictJson.require(Thread.currentThread() == owner, "batch observations belong to retained original owner thread"); }
}
