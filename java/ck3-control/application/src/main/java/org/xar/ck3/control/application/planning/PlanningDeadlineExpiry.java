package org.xar.ck3.control.application.planning;

import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact original planning budget expiry; this DATA carrier grants no action authority. */
public final class PlanningDeadlineExpiry extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final transient PlanningRequest request;
    private final Instant observed;

    public PlanningDeadlineExpiry(PlanningRequest request, Instant observed) {
        this.request = Objects.requireNonNull(request);
        this.observed = Objects.requireNonNull(observed);
        StrictJson.require(!request.deadline().isAfter(observed), "planning deadline expiry requires observed time at or after request deadline");
    }

    public PlanningRequest request() { return request; }
    public Instant observed() { return observed; }
}
