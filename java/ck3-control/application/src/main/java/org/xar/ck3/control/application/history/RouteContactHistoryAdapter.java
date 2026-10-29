package org.xar.ck3.control.application.history;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.routecontact.RouteContactCodec;
import org.xar.ck3.control.application.routecontact.RouteContactComposite;
import org.xar.ck3.control.application.routecontact.RouteContactProofs;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Value;

/** The real Driver branch adapter for route admission. Failed/malformed latest reads are retained as scope tombstones. */
public final class RouteContactHistoryAdapter implements RouteContactComposite.History {
    private final DriverHistoryAccess histories;
    private final AdvanceObservationPort observations;
    public RouteContactHistoryAdapter(DriverHistoryAccess histories, AdvanceObservationPort observations) {
        this.histories = Objects.requireNonNull(histories); this.observations = Objects.requireNonNull(observations);
    }
    @Override public List<RouteContactProofs.QueryEntry> survivingQueries(ActionCommand parent) {
        return histories.withView(parent, view -> {
        var raw = observations.current(parent, parent.deadline());
        StrictJson.require(raw.identity().equals(parent.before()) && raw.source().equals(parent.source())
                && raw.sessionId().equals(parent.sessionId()), "route-history current native observation differs from parent");
        return queries(view.freshQueryRows(), RouteContactCodec.frame(raw));
        });
    }
    @Override public List<TimelineEntry> survivingTimeline(ActionCommand parent) {
        return timeline(histories.read(parent).rows());
    }
    public static List<RouteContactProofs.QueryEntry> queries(List<DriverSurvivingHistory.Row> freshRows, Frame current) {
        Objects.requireNonNull(current); List<RouteContactProofs.QueryEntry> results = new ArrayList<>();
        for (DriverSurvivingHistory.Row row : DriverSurvivingHistory.orderedSlice(freshRows)) {
            Optional<String> command = row.effective().command(); if (command.isEmpty()) continue;
            RouteContactSteps.Request parsed;
            try { parsed = RouteContactSteps.query(command.orElseThrow()); }
            catch (IllegalArgumentException notAQuery) { continue; }
            var scope = new RouteContactProofs.Scope(parsed.scope().subjectId(), parsed.scope().targetId(), parsed.scope().hostiles());
            Optional<RouteQuery> valid = Optional.empty();
            if (row.ok() && row.effective().result().isPresent()) {
                try { valid = Optional.of(RouteContactCodec.query(command.orElseThrow(), true, current, row.effective().result().orElseThrow())); }
                catch (IllegalArgumentException | ArithmeticException staleOrMalformed) { /* Actual scope remains as a tombstone. Never resurrect an older success. */ }
            }
            results.add(new RouteContactProofs.QueryEntry(scope, valid));
        }
        return List.copyOf(results);
    }
    /** All surviving life advances, including ones before a restore and non-route barriers, oldest first. */
    public static List<TimelineEntry> timeline(List<DriverSurvivingHistory.Row> completeSurvivingBranch) {
        List<TimelineEntry> results = new ArrayList<>();
        for (DriverSurvivingHistory.Row row : DriverSurvivingHistory.completeBranch(completeSurvivingBranch)) {
            Optional<String> command = row.effective().command();
            if (command.isEmpty() || !DriverSurvivingHistory.isLifeAdvanceStep(command.orElseThrow())) continue;
            results.add(timelineEntry(row, command.orElseThrow()));
        }
        return List.copyOf(results);
    }
    private static TimelineEntry timelineEntry(DriverSurvivingHistory.Row row, String command) {
        try {
            RouteContactSteps.Request request = RouteContactSteps.parse(command);
            if (request.days() != 1 || row.effective().result().isEmpty()) return barrier(command, "not_a_complete_exact_route_advance");
            Obj result = row.effective().result().orElseThrow(); int subject = request.scope().subjectId();
            if (!row.ok() && result.get("contact_followup") instanceof Obj followup
                    && (text(followup.get("status"), "pending_strong_transition") || text(followup.get("status"), "exhausted_without_strong_transition"))
                    && integer(followup.get("subject_army_id"), "subject_army_id") == subject) {
                return new AdvanceHistory(false, subject, OpportunityJson.text(followup.get("episode_run_id"), "episode_run_id"),
                        integer(followup.get("ending_date_raw"), "ending_date_raw"), Optional.empty(), true);
            }
            if (!row.ok() || !(result.get("contact_transition") instanceof Obj transition)
                    || !text(transition.get("status"), "predicted_only")
                    || !text(transition.get("proof_kind"), "unavoidable_current_province_contact")
                    || !text(transition.get("postcondition"), "predicted_contact_boundary_reached")
                    || !(transition.get("contact_observed") instanceof OpportunityJson.Bool observed) || observed.value()
                    || integer(transition.get("subject_army_id"), "subject_army_id") != subject)
                return barrier(command, "latest_route_advance_is_not_a_predicted_endpoint");
            int end = integer(transition.get("ending_date_raw"), "ending_date_raw");
            if (integer(result.get("ending_date_raw"), "ending_date_raw") != end) return barrier(command, "outer_and_marker_ending_dates_differ");
            List<Integer> changed = OpportunityJson.array(transition.get("conflict_hostile_army_ids"), "conflict_hostile_army_ids").stream()
                    .map(value -> integer(value, "conflict_hostile_army_id")).toList();
            Transition marker = new Transition(TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED, false,
                    OpportunityJson.text(transition.get("episode_run_id"), "episode_run_id"), subject,
                    integer(transition.get("contact_province_id"), "contact_province_id"), integer(transition.get("starting_date_raw"), "starting_date_raw"), end, changed);
            return new AdvanceHistory(true, subject, marker.episodeRunId(), end, Optional.of(marker), false);
        } catch (IllegalArgumentException | ArithmeticException malformedOrOtherLifeAdvance) {
            return barrier(command, "latest_life_advance_has_no_valid_route_endpoint_or_strict_failure");
        }
    }
    private static TimelineBarrier barrier(String step, String reason) { return new TimelineBarrier(step, reason); }
    private static int integer(Value value, String name) { return OpportunityJson.integer(value, name).intValueExact(); }
    private static boolean text(Value value, String expected) { return value instanceof OpportunityJson.Text text && text.value().equals(expected); }
}
