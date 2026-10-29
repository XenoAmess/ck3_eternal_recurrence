package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CollectiveGroups.*;

public record CollectiveWorkforceFrame(Header header, Case al_case, Receipt m360_receipt,
        Phase phase, Collective collective, List<Cohort> cohorts, Debt route_c_debt, History history,
        CharterStatus charter_status, Charter charter_gate, CareerReadiness.Collective readiness, CareerProvenance provenance) {
    public CollectiveWorkforceFrame { cohorts = List.copyOf(cohorts); }
    public enum Phase { UNAVAILABLE, NOT_REACHED, ROUTE_A_EXCEPTION, ROUTE_B_FORCED, ROUTE_C_DEBT }
    public enum HistoryStatus { UNAVAILABLE, EMPTY, PARTIAL, THREE_CYCLE }
    public enum CharterStatus { UNAVAILABLE, NOT_ELIGIBLE, AWAITING_GATE, READY, CONSUMED }
    public record History(HistoryStatus status, Datum<BigInteger> count, int effective_count, List<HistorySlot> slots) {
        public History { slots = List.copyOf(slots); }
    }
    public static CollectiveWorkforceFrame decode(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "case_kind", "request_nonce", "snapshot_revision", "date_raw", "paused",
                "player_character_id", "subject_character_id", "requested_owner_character_id", "al_case", "m360_receipt",
                "collective", "cohorts", "route_c_debt", "history", "charter_gate", "readiness", "unavailable_reason", "provenance");
        require(text(row.get("case_kind")).equals("zhongguo.workforce-collective"), "collective case kind changed");
        Header header = CareerJson.header(row, binding, true, true);
        Case al = Case.parse(row.get("al_case")); Receipt receipt = Receipt.parse(row.get("m360_receipt"));
        JsonNode rawCollective = row.get("collective");
        Phase phase = Phase.valueOf(text(rawCollective.get("phase")).toUpperCase(java.util.Locale.ROOT));
        Collective collective = Collective.parse(without(rawCollective, "phase"));
        List<Cohort> cohorts = three(row.get("cohorts")).stream().map(Cohort::parse).toList();
        Debt debt = Debt.parse(row.get("route_c_debt"));
        JsonNode h = exact(row.get("history"), "status", "count", "effective_count", "slots");
        History history = new History(HistoryStatus.valueOf(text(h.get("status")).toUpperCase(java.util.Locale.ROOT)),
                number(h.get("count"), REASONS), int32(h.get("effective_count")), three(h.get("slots")).stream().map(HistorySlot::parse).toList());
        require(history.effective_count() >= -1 && history.effective_count() <= 3, "invalid effective history count");
        JsonNode rawCharter = row.get("charter_gate");
        CharterStatus charterStatus = CharterStatus.valueOf(text(rawCharter.get("status")).toUpperCase(java.util.Locale.ROOT));
        Charter charter = Charter.parse(without(rawCharter, "status"));
        CareerReadiness.Collective readiness = CareerReadiness.Collective.parse(row.get("readiness"));
        CareerProvenance provenance = CareerProvenance.parse(row.get("provenance"), CareerProvenance.Profile.COLLECTIVE);
        boolean aggregate = readiness.player_subject_binding_ready() && readiness.owner_binding_ready() && readiness.case_identity_ready()
                && readiness.m360_receipt_projection_ready() && readiness.collective_lifecycle_ready() && readiness.cohort_identity_ready()
                && readiness.cohort_conservation_ready() && readiness.route_conservation_ready() && readiness.history_ledger_ready()
                && readiness.history_order_ready() && readiness.charter_gate_lifecycle_ready() && readiness.same_frame_ready();
        require(readiness.ready() == aggregate, "collective readiness aggregate mismatch");
        CollectiveWorkforceFrame frame = new CollectiveWorkforceFrame(header, al, receipt, phase, collective, cohorts, debt, history, charterStatus, charter, readiness, provenance);
        if (header.status() == Availability.UNAVAILABLE) {
            require(Set.of("unsupported_build", "requires_application_main", "requires_paused", "map_not_ready", "case_not_found",
                    "case_inconsistent", "owner_filter_mismatch", "variable_identifier_unavailable", "variable_context_unavailable",
                    "collective_inconsistent", "history_inconsistent", "state_changed", "internal_error").contains(header.unavailable_reason().orElseThrow())
                    && readiness.flags().stream().noneMatch(Boolean::booleanValue), "unavailable collective fabricated readiness");
            require(phase == Phase.UNAVAILABLE && history.status() == HistoryStatus.UNAVAILABLE && history.effective_count() == -1
                    && List.<Group>of(al, receipt, collective, debt, charter).stream().allMatch(g -> allReason(g, "case_unavailable"))
                    && cohorts.stream().allMatch(g -> allReason(g, "case_unavailable"))
                    && history.slots().stream().allMatch(g -> allReason(g, "case_unavailable"))
                    && !history.count().available() && history.count().unavailable_reason().orElseThrow().equals("case_unavailable"),
                    "unavailable collective leaked semantic payload");
        } else frame.validateAvailable(binding);
        return frame;
    }
    private void validateAvailable(FrameBinding b) {
        require(readiness.ready() && all(al_case), "available collective lacks AL case identity");
        long owner = b.owner_character_id(), player = b.player_character_id(), cycle = n(al_case.cycle_serial()), serial = n(al_case.case_serial());
        require(eq(al_case.owner_character_id(), owner) && eq(al_case.subject_character_id(), player) && cycle >= 1 && serial > 0
                && n(al_case.state()) >= 1 && n(al_case.state()) <= 8 && n(al_case.revision()) >= 1, "AL case identity mismatch");
        if (phase == Phase.NOT_REACHED) {
            require(allReason(m360_receipt, "receipt_not_recorded") && allReason(collective, "lifecycle_not_reached")
                    && cohorts.stream().allMatch(g -> allReason(g, "lifecycle_not_reached")) && allReason(route_c_debt, "lifecycle_not_reached"), "not-reached collective fabricated products");
        } else {
            require(all(m360_receipt) && receiptIdentity(m360_receipt, owner, player, cycle, serial), "M360 collective receipt identity mismatch");
            long choice = n(m360_receipt.choice()); require(choice >= 1 && choice <= 3, "M360 collective route outside A/B/C");
            if (phase == Phase.ROUTE_A_EXCEPTION || phase == Phase.ROUTE_B_FORCED) validateCollectiveRoute(owner, player, cycle, serial, choice);
            else {
                require(phase == Phase.ROUTE_C_DEBT && choice == 3 && allReason(collective, "not_applicable")
                        && cohorts.stream().allMatch(g -> allReason(g, "not_applicable")) && all(route_c_debt), "route C surface mismatch");
                Debt d = route_c_debt;
                require(eq(d.owner_character_id(), owner) && eq(d.subject_character_id(), player) && eq(d.cycle_serial(), cycle)
                        && eq(d.case_serial(), serial) && eq(d.state(), 4) && d.due_cycle_serial().observed().equals(BigInteger.valueOf(cycle).add(BigInteger.ONE))
                        && f(d.open()) != f(d.consumed()), "route C debt lifecycle mismatch");
            }
        }
        int count = validateHistory(owner, player, cycle, serial);
        validateCharter(owner, player, cycle, serial, count);
        require(readiness.flags().stream().filter(value -> !value).count() == (count == 3 ? 0 : 1)
                && readiness.three_cycle_ready() == (count == 3), "collective readiness differs from decoded facts");
    }
    private static boolean receiptIdentity(Receipt r, long owner, long player, long cycle, long serial) {
        return eq(r.owner_character_id(), owner) && eq(r.subject_character_id(), player) && eq(r.cycle_serial(), cycle) && eq(r.case_serial(), serial) && eq(r.state(), 4);
    }
    private void validateCollectiveRoute(long owner, long player, long cycle, long serial, long choice) {
        boolean routeA = phase == Phase.ROUTE_A_EXCEPTION;
        require(choice == (routeA ? 1 : 2) && allReason(route_c_debt, "not_applicable") && all(collective)
                && cohorts.stream().allMatch(CareerJson::all), "A/B collective surface mismatch");
        require(cohorts.stream().map(c -> n(c.manager_character_id())).distinct().count() == 3
                && cohorts.stream().map(c -> n(c.cohort_id())).distinct().count() == 3, "cohort identities are not distinct");
        BigInteger members = BigInteger.ZERO, quota = BigInteger.ZERO, forced = BigInteger.ZERO, exceptions = BigInteger.ZERO, cost = BigInteger.ZERO;
        for (Cohort c : cohorts) {
            long q = n(c.quota());
            require(q >= 0 && q <= 6 && n(c.member_count()) >= q && f(c.partition_verified()), "invalid cohort partition");
            require(eq(c.forced_count(), routeA ? 0 : q) && eq(c.exception_count(), routeA ? q : 0)
                    && eq(c.manager_cost(), routeA ? q : 0) && eq(c.approval_verified(), routeA), "cohort route conservation mismatch");
            require(List.of(c.b1_cycle_serial(), c.b1_case_serial(), c.b1_source_id(), c.b1_source_hash(), c.mg_cycle_serial(),
                    c.mg_case_serial(), c.mg_snapshot_source_serial(), c.mg_snapshot_revision()).stream().allMatch(v -> v.observed().signum() > 0), "cohort source evidence missing");
            members = members.add(c.member_count().observed()); quota = quota.add(c.quota().observed()); forced = forced.add(c.forced_count().observed());
            exceptions = exceptions.add(c.exception_count().observed()); cost = cost.add(c.manager_cost().observed());
        }
        Collective c = collective;
        require(!f(c.submission_active()) && f(c.submission_sealed()) && f(c.submission_consumed()) && f(c.settled())
                && eq(c.owner_character_id(), owner) && eq(c.subject_character_id(), player) && eq(c.cycle_serial(), cycle)
                && eq(c.case_serial(), serial) && eq(c.state(), 4) && eq(c.collective_case_serial(), serial)
                && eq(c.submitted_cycle_serial(), cycle) && eq(c.cohort_count(), 3) && n(c.settlement_id()) > 0 && n(c.settlement_hash()) > 0
                && eq(c.route(), choice) && c.total_members().observed().equals(members) && c.total_quota().observed().equals(quota)
                && quota.signum() > 0 && quota.compareTo(BigInteger.valueOf(6)) <= 0 && c.forced_count().observed().equals(forced)
                && c.exception_count().observed().equals(exceptions) && c.manager_cost_total().observed().equals(cost), "collective totals/settlement mismatch");
    }
    private int validateHistory(long owner, long player, long cycle, long serial) {
        int count;
        if (history.status() == HistoryStatus.EMPTY) {
            require(!history.count().available() && history.count().unavailable_reason().orElseThrow().equals("variable_absent")
                    && history.effective_count() == 0 && history.slots().stream().allMatch(s -> allReason(s, "lifecycle_not_reached")), "empty history fabricated evidence");
            count = 0;
        } else {
            require(history.count().available(), "history count unavailable");
            count = Math.toIntExact(n(history.count()));
            require(count >= 1 && count <= 3 && history.effective_count() == count
                    && history.status() == (count == 3 ? HistoryStatus.THREE_CYCLE : HistoryStatus.PARTIAL), "history count/status mismatch");
            long previous = 0;
            for (int index = 0; index < 3; index++) {
                HistorySlot s = history.slots().get(index);
                if (index >= count) { require(allReason(s, "lifecycle_not_reached"), "future history slot fabricated"); continue; }
                require(all(s), "partial historical receipt");
                List<Long> ids = List.of(n(s.m357_receipt_id()), n(s.m358_receipt_id()), n(s.m359_receipt_id()));
                List<Long> hashes = List.of(n(s.m357_receipt_hash()), n(s.m358_receipt_hash()), n(s.m359_receipt_hash()));
                require(eq(s.owner_character_id(), owner) && n(s.cycle_serial()) > previous && n(s.case_serial()) > 0
                        && ids.stream().allMatch(v -> v > 0) && hashes.stream().allMatch(v -> v > 0)
                        && ids.stream().distinct().count() == 3 && hashes.stream().distinct().count() == 3, "history order/source receipt identity mismatch");
                previous = n(s.cycle_serial());
            }
            if (count == 3) {
                HistorySlot tail = history.slots().get(2);
                require(eq(tail.subject_character_id(), player) && eq(tail.cycle_serial(), cycle) && eq(tail.case_serial(), serial), "three-cycle tail mismatch");
            }
        }
        require(readiness.history_ledger_ready() && readiness.history_order_ready() && readiness.three_cycle_ready() == (count == 3), "history readiness mismatch");
        return count;
    }
    private void validateCharter(long owner, long player, long cycle, long serial, int count) {
        Charter c = charter_gate;
        List<Datum<?>> evidence = List.of(c.evidence_count(), c.evidence_ready(), c.evidence_consumed(), c.owner_character_id(),
                c.subject_character_id(), c.cycle_serial(), c.case_serial(), c.state(), c.prepared_report_id(), c.prepared_charter_id(),
                c.previous_charter_id(), c.previous_version(), c.adopted_cycle_serial(), c.effective_cycle_serial());
        boolean absent = evidence.stream().allMatch(f -> !f.available() && f.unavailable_reason().orElseThrow().equals("lifecycle_not_reached"));
        boolean full = evidence.stream().allMatch(Datum::available);
        boolean identity = full && eq(c.evidence_count(), 3) && eq(c.owner_character_id(), owner) && eq(c.subject_character_id(), player)
                && eq(c.cycle_serial(), cycle) && eq(c.case_serial(), serial) && eq(c.state(), 5);
        if (charter_status == CharterStatus.NOT_ELIGIBLE || charter_status == CharterStatus.AWAITING_GATE) {
            require(charter_status == (count == 3 ? CharterStatus.AWAITING_GATE : CharterStatus.NOT_ELIGIBLE)
                    && (absent || count == 3 && identity && !f(c.evidence_ready()) && !f(c.evidence_consumed())), "charter pre-gate mismatch");
        } else {
            require(count == 3 && identity && (charter_status == CharterStatus.READY || charter_status == CharterStatus.CONSUMED)
                    && eq(c.evidence_ready(), charter_status == CharterStatus.READY) && eq(c.evidence_consumed(), charter_status == CharterStatus.CONSUMED)
                    && n(c.prepared_report_id()) > 0 && n(c.prepared_charter_id()) > 0 && n(c.previous_version()) >= 0
                    && eq(c.adopted_cycle_serial(), cycle) && c.effective_cycle_serial().observed().equals(BigInteger.valueOf(cycle).add(BigInteger.ONE)), "charter lifecycle evidence mismatch");
        }
    }
}
