package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.GovernanceGroups.*;

/** F035 distribution and F032 component-8 are read as separate, proven lifecycle branches. */
public record ManagerGovernanceFrame(Header header, SubjectBinding subject_binding, Case f_case, Team team_snapshot,
        F035 f035, F032 f032, CareerReadiness.Governance readiness, CareerProvenance provenance) {
    public enum BindingKind { UNAVAILABLE, PLAYED_CHARACTER, BOUNDED_AI_DIRECT_MANAGER }
    public record SubjectBinding(BindingKind kind, Datum<BigInteger> manager_character_id, Datum<BigInteger> owner_character_id,
            Datum<String> bounded_ai_manager_dependency) implements Group {
        public List<Datum<?>> fields() { return List.of(manager_character_id, owner_character_id, bounded_ai_manager_dependency); }
    }
    public record F035(Receipt receipt, Distribution snapshot, Policy next_cycle_policy, Effective effective) { }
    public record F032(Receipt receipt, Score manager_score, Component component8) { }
    public static ManagerGovernanceFrame decode(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "case_kind", "request_nonce", "snapshot_revision", "date_raw", "paused",
                "player_character_id", "subject_character_id", "requested_owner_character_id", "subject_binding", "f_case",
                "team_snapshot", "f035", "f032", "readiness", "unavailable_reason", "provenance");
        require(text(row.get("case_kind")).equals("zhongguo.manager-governance"), "manager-governance case kind changed");
        Header header = CareerJson.header(row, binding, false, true);
        JsonNode sb = exact(row.get("subject_binding"), "kind", "manager_character_id", "owner_character_id", "bounded_ai_manager_dependency");
        SubjectBinding subject = new SubjectBinding(BindingKind.valueOf(text(sb.get("kind")).toUpperCase(java.util.Locale.ROOT)),
                number(sb.get("manager_character_id"), REASONS), number(sb.get("owner_character_id"), REASONS), string(sb.get("bounded_ai_manager_dependency"), REASONS));
        Case fcase = Case.parse(row.get("f_case")); Team team = Team.parse(row.get("team_snapshot"));
        JsonNode d = exact(row.get("f035"), "receipt", "snapshot", "next_cycle_policy", "effective");
        F035 f035 = new F035(Receipt.parse(d.get("receipt")), Distribution.parse(d.get("snapshot")), Policy.parse(d.get("next_cycle_policy")), Effective.parse(d.get("effective")));
        JsonNode c = exact(row.get("f032"), "receipt", "manager_score", "component8");
        F032 f032 = new F032(Receipt.parse(c.get("receipt")), Score.parse(c.get("manager_score")), Component.parse(c.get("component8")));
        CareerReadiness.Governance readiness = CareerReadiness.Governance.parse(row.get("readiness"));
        CareerProvenance provenance = CareerProvenance.parse(row.get("provenance"), CareerProvenance.Profile.GOVERNANCE);
        ManagerGovernanceFrame frame = new ManagerGovernanceFrame(header, subject, fcase, team, f035, f032, readiness, provenance);
        if (header.status() == Availability.UNAVAILABLE) {
            require(Set.of("unsupported_build", "requires_application_main", "requires_paused", "map_not_ready", "case_not_found",
                    "case_inconsistent", "ai_manager_owner_not_player", "bounded_ai_manager_dependency_unavailable",
                    "subject_not_bounded_ai_manager", "owner_filter_mismatch", "variable_identifier_unavailable",
                    "variable_context_unavailable", "state_changed", "internal_error").contains(header.unavailable_reason().orElseThrow())
                    && subject.kind() == BindingKind.UNAVAILABLE && readiness.flags().stream().noneMatch(Boolean::booleanValue)
                    && List.<Group>of(subject, fcase, team, f035.receipt(), f035.snapshot(), f035.next_cycle_policy(), f035.effective(),
                    f032.receipt(), f032.manager_score(), f032.component8()).stream().allMatch(CareerJson::none), "unavailable governance leaked manager semantics");
        } else frame.validate(binding);
        return frame;
    }
    private static boolean receiptReady(Receipt r, long owner, long subject, long cycle, long serial) {
        return all(r) && eq(r.owner_character_id(), owner) && eq(r.subject_character_id(), subject) && eq(r.cycle_serial(), cycle)
                && eq(r.case_serial(), serial) && eq(r.state(), 1) && n(r.choice()) >= 1 && n(r.choice()) <= 3;
    }
    private static long expectedBottom(long cohort, long mode) {
        return switch (Math.toIntExact(mode)) { case 1 -> Math.max(cohort >= 5 ? 1 : 0, Math.floorDiv(cohort, 10));
            case 2 -> Math.floorDiv(cohort, 20); case 3 -> 0; default -> throw new IllegalArgumentException("distribution mode outside 1..3"); };
    }
    private static BigInteger topSlots(long cohort) {
        BigInteger product = BigInteger.valueOf(cohort).multiply(BigInteger.valueOf(30));
        BigInteger[] division = product.divideAndRemainder(BigInteger.valueOf(100));
        return product.signum() < 0 && division[1].signum() != 0 ? division[0].subtract(BigInteger.ONE) : division[0];
    }
    private void validate(FrameBinding b) {
        long subject = b.subject_character_id(), owner = b.owner_character_id(), player = b.player_character_id();
        SubjectBinding sb = subject_binding;
        boolean bindingReady = eq(sb.manager_character_id(), subject) && eq(sb.owner_character_id(), owner), boundedReady = false;
        if (subject == player) {
            bindingReady &= sb.kind() == BindingKind.PLAYED_CHARACTER;
            require(!sb.bounded_ai_manager_dependency().available() && sb.bounded_ai_manager_dependency().unavailable_reason().orElseThrow().equals("not_applicable"), "player subject invented AI dependency");
        } else {
            bindingReady &= owner == player && sb.kind() == BindingKind.BOUNDED_AI_DIRECT_MANAGER && eq(sb.bounded_ai_manager_dependency(), DEPENDENCY);
            boundedReady = bindingReady;
        }
        require(bindingReady, "governance lacks typed subject binding");
        Case fc = f_case;
        boolean caseReady = all(fc) && eq(fc.owner_character_id(), owner) && eq(fc.subject_character_id(), subject)
                && n(fc.cycle_serial()) >= 1 && n(fc.case_serial()) >= 1 && n(fc.state()) >= 1 && n(fc.state()) <= 5 && n(fc.revision()) >= 1;
        require(caseReady, "governance lacks F case identity");
        long cycle = n(fc.cycle_serial()), serial = n(fc.case_serial());
        Team t = team_snapshot;
        boolean teamReady = all(t) && eq(t.status(), 1) && eq(t.owner_character_id(), owner) && eq(t.subject_character_id(), subject)
                && eq(t.cycle_serial(), cycle) && eq(t.case_serial(), serial) && n(t.revision()) >= 1 && n(t.source_cycle()) < cycle && n(t.cohort_n()) >= 0;
        long teamRevision = teamReady ? n(t.revision()) : -1, cohort = teamReady ? n(t.cohort_n()) : -1;
        boolean r35 = receiptReady(f035.receipt(), owner, subject, cycle, serial);
        boolean distributionReady = false, conservationReady = false, policyReady = false, effectiveReady = false,
                settlementReady = false, actualBottomReady = false, distributionLifecycle = false;
        Distribution d = f035.snapshot(); Policy p = f035.next_cycle_policy(); Effective e = f035.effective();
        if (r35) {
            long choice = n(f035.receipt().choice());
            if (choice == 3) {
                require(none(d) && none(p) && none(e), "F035 C route leaked stale business values");
                distributionLifecycle = true;
            } else {
                long mode = -1;
                if (all(d)) {
                    mode = n(d.mode());
                    distributionReady = f(d.available()) && mode >= 1 && mode <= 3 && n(d.rule_source()) >= 1 && n(d.rule_source()) <= 3
                            && List.of(d.top_slots(), d.middle_slots(), d.bottom_slots(), d.conserved_slots()).stream().allMatch(v -> v.observed().signum() >= 0)
                            && d.top_slots().observed().equals(topSlots(cohort)) && eq(d.bottom_slots(), expectedBottom(cohort, mode));
                    conservationReady = distributionReady && d.top_slots().observed().add(d.middle_slots().observed()).add(d.bottom_slots().observed()).equals(d.conserved_slots().observed())
                            && eq(d.conserved_slots(), cohort);
                }
                policyReady = all(p) && n(p.status()) >= 1 && n(p.status()) <= 2 && eq(p.owner_character_id(), subject)
                        && eq(p.subject_character_id(), subject) && eq(p.source_reviewer_character_id(), owner) && eq(p.source_cycle(), cycle)
                        && eq(p.source_case(), serial) && n(p.source_revision()) >= 1 && eq(p.input_revision(), teamRevision)
                        && eq(p.mode(), mode) && p.rule_source().observed().equals(d.rule_source().observed())
                        && p.due_cycle().observed().equals(BigInteger.valueOf(cycle).add(BigInteger.ONE));
                if (policyReady && eq(p.status(), 2)) {
                    effectiveReady = List.of(e.mode(), e.cycle(), e.source_cycle(), e.source_case(), e.input_revision()).stream().allMatch(Datum::available);
                    if (effectiveReady) {
                        effectiveReady = eq(e.mode(), mode) && e.cycle().observed().compareTo(p.due_cycle().observed()) >= 0
                                && e.source_cycle().equals(p.source_cycle()) && e.source_case().equals(p.source_case()) && e.input_revision().equals(p.input_revision());
                        settlementReady = effectiveReady && e.settled_cycle().available() && e.settlement_receipt().available()
                                && e.settled_cycle().observed().equals(e.cycle().observed()) && eq(e.settlement_receipt(), serial);
                        actualBottomReady = effectiveReady && e.actual_cohort_n().available() && e.actual_bottom_slots().available()
                                && n(e.actual_cohort_n()) >= 0 && eq(e.actual_bottom_slots(), expectedBottom(n(e.actual_cohort_n()), mode));
                    }
                } else require(none(e), "pending F035 token leaked effective values");
                distributionLifecycle = distributionReady && conservationReady && policyReady
                        && (eq(p.status(), 1) || effectiveReady && settlementReady && actualBottomReady);
            }
        }
        boolean r32 = receiptReady(f032.receipt(), owner, subject, cycle, serial);
        Score score = f032.manager_score(); Component component = f032.component8();
        boolean scoreReady = false, componentReady = false, componentSettlement = false, componentLifecycle = false;
        if (r32) {
            long choice = n(f032.receipt().choice());
            if (choice == 3) {
                require(none(score) && none(component), "F032 C route leaked stale business values"); componentLifecycle = true;
            } else {
                scoreReady = all(score) && eq(score.mode(), choice);
                List<Datum<BigInteger>> base = List.of(component.status(), component.owner_character_id(), component.subject_character_id(),
                        component.source_cycle(), component.source_case(), component.source_revision(), component.input_revision(),
                        component.component(), component.value(), component.due_cycle());
                List<Datum<BigInteger>> settled = List.of(component.settled_by_owner_character_id(), component.settled_cycle(), component.settled_value(), component.settlement_receipt());
                componentReady = base.stream().allMatch(Datum::available) && scoreReady && n(component.status()) >= 1 && n(component.status()) <= 2
                        && eq(component.owner_character_id(), owner) && eq(component.subject_character_id(), subject) && eq(component.source_cycle(), cycle)
                        && eq(component.source_case(), serial) && n(component.source_revision()) >= 1 && eq(component.input_revision(), teamRevision)
                        && eq(component.component(), 8) && component.value().observed().equals(score.sum().observed())
                        && component.due_cycle().observed().equals(BigInteger.valueOf(cycle).add(BigInteger.ONE));
                if (componentReady && eq(component.status(), 2)) {
                    componentSettlement = settled.stream().allMatch(Datum::available)
                            && component.settled_cycle().observed().compareTo(component.due_cycle().observed()) >= 0
                            && component.settled_value().observed().equals(component.value().observed()) && eq(component.settlement_receipt(), serial);
                } else if (componentReady) require(settled.stream().noneMatch(Datum::available), "pending component-8 leaked settlement");
                componentLifecycle = componentReady && (eq(component.status(), 1) || componentSettlement);
            }
        }
        boolean ready = bindingReady && caseReady && teamReady && r35 && distributionLifecycle && r32 && componentLifecycle;
        CareerReadiness.Governance expected = new CareerReadiness.Governance(actualBottomReady, boundedReady, caseReady, componentLifecycle,
                componentSettlement, componentReady, conservationReady, distributionLifecycle, settlementReady, distributionReady,
                effectiveReady, r32, r35, scoreReady, policyReady, ready, true, bindingReady, teamReady);
        require(readiness.equals(expected), "manager readiness disagrees with independent lifecycle facts");
    }
}
