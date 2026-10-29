package org.xar.ck3.control.service;

import io.quarkus.runtime.Startup;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.List;
import java.util.Objects;
import java.util.ServiceLoader;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.metrics.BatchDecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2ResearchBatch;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.m2.M2Research;

/** Pure G2 engine assembly inside the existing resident Quarkus application. */
@ApplicationScoped
@Startup
public class G2ResearchHost {
    public record MeasuredEvaluation(G2Response response, BatchDecisionMetrics.Batch metrics) {
        public MeasuredEvaluation { Objects.requireNonNull(response); Objects.requireNonNull(metrics); }
    }
    private final G2ResearchEngine engine;

    @Inject public G2ResearchHost(ProjectionHost existingHost) { this(assemble(Objects.requireNonNull(existingHost))); }

    public G2ResearchHost(G2ResearchEngine engine) { this.engine = Objects.requireNonNull(engine); }

    public G2Response evaluate(G2Request request) { return evaluateMeasured(Objects.requireNonNull(request)).response(); }

    /** Existing HTTP response stays unchanged; in-process callers can consume the exact typed observations. */
    public MeasuredEvaluation evaluateMeasured(G2Request request) {
        Objects.requireNonNull(request);
        DecisionMetricRecorder.SystemClock clock = new DecisionMetricRecorder.SystemClock();
        G2ResearchBatch batch = beginBatch(new BatchDecisionMetrics.Context(WindowsJobProcess.currentMachineId(), "g2-host",
                "g2-request:" + request.requestId(), clock.domainId()), clock);
        G2ResearchBatch.Evaluation result = batch.evaluate(request);
        return new MeasuredEvaluation(result.response(), batch.finish());
    }

    /** Caller opens this at its actual batch admission boundary and retains it until the batch terminal. */
    public G2ResearchBatch beginBatch(BatchDecisionMetrics.Context context, DecisionMetricRecorder.Clock clock) {
        Objects.requireNonNull(context);
        if (!WindowsJobProcess.currentMachineId().equals(context.machineId())) {
            throw new IllegalArgumentException("host metrics must identify the actual observing machine");
        }
        return new G2ResearchBatch(engine, context, clock);
    }

    private static G2ResearchEngine assemble(ProjectionHost existingHost) {
        List<G2Domain> domains = ServiceLoader.load(G2Domain.class).stream().map(provider -> {
            G2Domain domain = provider.get();
            if (domain.milestone() == Milestone.M2 && existingHost.context().eventSources().isPresent()) {
                return new M2Research(existingHost.context().eventSources().orElseThrow());
            }
            return domain;
        }).toList();
        G2ResearchEngine engine = new G2ResearchEngine(domains);
        if (engine.milestones().size() != Milestone.values().length) {
            throw new G2Exception(G2HttpError.Code.ENGINE_UNAVAILABLE, "all eight G2 domains required in the existing host");
        }
        return engine;
    }
}
