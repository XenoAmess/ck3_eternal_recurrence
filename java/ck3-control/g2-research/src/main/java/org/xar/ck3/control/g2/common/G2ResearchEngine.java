package org.xar.ck3.control.g2.common;

import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.ServiceLoader;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Stage;

/** Pure routing inside the existing host. It neither submits actions nor writes receipts or campaign state. */
public final class G2ResearchEngine {
    private final EnumMap<Milestone,G2Domain> domains = new EnumMap<>(Milestone.class);
    public G2ResearchEngine(List<? extends G2Domain> registrations) {
        for (G2Domain domain : List.copyOf(registrations)) {
            Objects.requireNonNull(domain); Milestone milestone=Objects.requireNonNull(domain.milestone());
            if (domains.putIfAbsent(milestone,domain)!=null) throw new IllegalArgumentException("duplicate G2 domain: "+milestone);
        }
    }
    public static G2ResearchEngine standard() {
        List<G2Domain> domains=ServiceLoader.load(G2Domain.class).stream().map(ServiceLoader.Provider::get).toList();
        G2ResearchEngine result=new G2ResearchEngine(domains);
        if(result.domains.size()!=Milestone.values().length) throw new G2Exception(G2HttpError.Code.ENGINE_UNAVAILABLE,"all eight G2 domains required");
        return result;
    }
    public Set<Milestone> milestones() { return Set.copyOf(domains.keySet()); }
    /** Same actual pure domain route, with observations owned by the existing caller receipt. */
    public G2Response evaluate(G2Request request, DecisionMetricRecorder metrics) {
        Objects.requireNonNull(request); Objects.requireNonNull(metrics);
        // Context identifies the observing machine; G2Source is portable caller provenance and remains echoed below.
        StrictJson.require(metrics.context().requestId().equals(request.requestId()), "G2 metrics request identity differs");
        return metrics.measurePure(Stage.DOMAIN_EVALUATION, () -> evaluate(request));
    }
    public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request); G2Domain domain=domains.get(request.milestone());
        if(domain==null) throw new G2Exception(G2HttpError.Code.ENGINE_UNAVAILABLE,"G2 domain unavailable");
        G2Response response=domain.evaluate(request);
        if(response==null) throw new G2Exception(G2HttpError.Code.INVALID_RESULT,"G2 domain returned no result");
        if(!request.requestId().equals(response.requestId()) || request.milestone()!=response.milestone()
                || !request.source().equals(response.source()))
            throw new G2Exception(G2HttpError.Code.SOURCE_MISMATCH,"G2 response identity or source mismatch");
        return response;
    }
}

