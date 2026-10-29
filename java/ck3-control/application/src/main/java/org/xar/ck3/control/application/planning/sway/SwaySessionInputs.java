package org.xar.ck3.control.application.planning.sway;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.swayreuse.ReusedSwayOpportunity;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Actual canonical SWAY producer for the existing ordinary planning factory. No missing-ledger empty fallback. */
public final class SwaySessionInputs implements OrdinarySwayReadSource.InputsPort {
    private final SwayCanonicalDomain domain;
    private final Supplier<ContinuityStorePort.Session> actualSession;
    public SwaySessionInputs(SwayCanonicalDomain domain, Supplier<ContinuityStorePort.Session> actualSession) {
        this.domain = Objects.requireNonNull(domain); this.actualSession = Objects.requireNonNull(actualSession);
    }
    @Override public Optional<OrdinarySwayReadSource.BoundInputs> load(PlanningRequest request) {
        try {
            var ledger = domain.load(Objects.requireNonNull(actualSession.get(), "actual borrowed Sway planning writer missing")).ledger();
            return Optional.of(new OrdinarySwayReadSource.BoundInputs(request.before(), project(ledger, request.before())));
        } catch (IOException failure) { throw new OrdinarySwayService.Unavailable("actual canonical Sway input unavailable: " + failure.getMessage()); }
    }
    public static OrdinarySwayService.Inputs project(SwayFormalState.Ledger ledger, org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before) {
            StrictJson.require(ledger.machineId().equals(before.machineId()) && ledger.episodeRunId().equals(before.frame().episodeRunId()), "Sway planning original domain crossed machine/episode");
            Optional<OrdinarySwaySchedule.Pending> pending = ledger.pending().map(value -> new OrdinarySwaySchedule.Pending(value.actionId(), value.original().binding().actor(), value.original().target()));
            if (pending.isEmpty() && ledger.resolved().isEmpty()) pending = ledger.imported().flatMap(SwayLegacyImport.Imported::pending).map(value -> new OrdinarySwaySchedule.Pending(value.actionId(), value.actor(), value.target()));
            Optional<OrdinarySwaySchedule.Resolved> resolved = ledger.resolved().map(value -> {
                var input = StrictJson.object(); var original = SwayFormalCodec.originalResolved(value);
                original.retain("status", "postcondition_verified", "action_id", "actor_character_id", "target_character_id", "pre_capture_epoch", "post_capture_epoch", "post_date_raw", "native_receipt", "recovered_instance_observation", "latest_instance_observation", "terminal_intervention");
                input.set("resolved", original); input.put("actor_character_id", before.frame().identity().player()); input.put("date_raw", before.frame().identity().dateRaw());
                var reuse = value.lifecycle().origin().game().equals(before.game()) ? ReusedSwayOpportunity.decodeObservationGap(StrictJson.canonical(input)) : Optional.<ReusedSwayOpportunity.ObservationGap>empty();
                return new OrdinarySwaySchedule.Resolved(value.identity(), true, true, value.lifecycle().terminal().isPresent(), reuse);
            });
            if (resolved.isEmpty()) resolved = ledger.imported().flatMap(SwayLegacyImport.Imported::resolved).map(value -> new OrdinarySwaySchedule.Resolved(value.identity(), true, true, false, Optional.empty()));
            return new OrdinarySwayService.Inputs(new OrdinarySwaySchedule.Ledger(pending, resolved), ledger.schedule());
    }
}
