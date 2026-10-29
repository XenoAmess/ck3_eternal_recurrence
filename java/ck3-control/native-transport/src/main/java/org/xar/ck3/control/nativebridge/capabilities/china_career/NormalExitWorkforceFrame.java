package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.NormalExitGroups.*;

/** Independently derives the highest complete lifecycle from the original native fields. */
public record NormalExitWorkforceFrame(Header header, Lifecycle lifecycle, Source source, Workflow workflow,
        CurrentHc current_hc, Receipt receipt, Rehire rehire, CareerReadiness.NormalExit readiness, CareerProvenance provenance) {
    public enum Lifecycle { UNAVAILABLE, PRE, MIGRATING, SEALED, REHIRE_CAPTURED }
    public static NormalExitWorkforceFrame decode(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "case_kind", "request_nonce", "snapshot_revision", "date_raw", "paused",
                "player_character_id", "subject_character_id", "requested_owner_character_id", "lifecycle", "source",
                "workflow", "current_hc", "receipt", "rehire", "readiness", "unavailable_reason", "provenance");
        require(text(row.get("case_kind")).equals("zhongguo.workforce.normal-exit.received-self"), "normal-exit case kind changed");
        Header header = CareerJson.header(row, binding, true, true);
        Lifecycle lifecycle = Lifecycle.valueOf(text(row.get("lifecycle")).toUpperCase(java.util.Locale.ROOT));
        Source source = Source.parse(row.get("source")); Workflow workflow = Workflow.parse(row.get("workflow"));
        CurrentHc hc = CurrentHc.parse(row.get("current_hc")); Receipt receipt = Receipt.parse(row.get("receipt"));
        Rehire rehire = Rehire.parse(row.get("rehire"));
        CareerReadiness.NormalExit readiness = CareerReadiness.NormalExit.parse(row.get("readiness"));
        CareerProvenance provenance = CareerProvenance.parse(row.get("provenance"), CareerProvenance.Profile.NORMAL_EXIT);
        NormalExitWorkforceFrame frame = new NormalExitWorkforceFrame(header, lifecycle, source, workflow, hc, receipt, rehire, readiness, provenance);
        if (header.status() == Availability.UNAVAILABLE) {
            require(lifecycle == Lifecycle.UNAVAILABLE && !readiness.ready()
                    && List.<Group>of(source, workflow, hc, receipt, rehire).stream().allMatch(CareerJson::none)
                    && Set.of("unsupported_build", "requires_application_main", "requires_paused", "map_not_ready", "case_not_found",
                    "case_inconsistent", "owner_filter_mismatch", "not_received_self", "variable_identifier_unavailable",
                    "variable_context_unavailable", "state_changed", "internal_error").contains(header.unavailable_reason().orElseThrow()), "unavailable normal-exit leaked lifecycle fields");
        } else frame.validate(binding);
        return frame;
    }
    static boolean conserved(Partition p) {
        if (!all(p)) return false;
        return p.authorized().observed().signum() > 0 && List.of(p.available(), p.reserved(), p.occupied(), p.frozen(), p.reclaimed())
                .stream().allMatch(v -> v.observed().signum() >= 0)
                && p.authorized().observed().equals(p.available().observed().add(p.reserved().observed()).add(p.occupied().observed()).add(p.frozen().observed()).add(p.reclaimed().observed()));
    }
    static boolean migration(Partition before, Partition after) {
        return conserved(before) && conserved(after) && before.authorized().equals(after.authorized()) && before.available().equals(after.available())
                && before.reserved().equals(after.reserved()) && before.reclaimed().equals(after.reclaimed())
                && after.occupied().observed().equals(before.occupied().observed().subtract(BigInteger.ONE))
                && after.frozen().observed().equals(before.frozen().observed().add(BigInteger.ONE));
    }
    private void validate(FrameBinding b) {
        Source s = source; Workflow w = workflow; CurrentHc hc = current_hc; Receipt r = receipt; Rehire h = rehire;
        require(s.fields().stream().filter(field -> field != s.consumer_receipt_case_serial()).allMatch(Datum::available)
                && all(hc), "source and live HC must be complete");
        long owner = b.owner_character_id(), player = b.player_character_id(), cycle = n(s.cycle_serial()), serial = n(s.case_serial());
        boolean sourcePost = eq(s.state(), 3);
        require(owner != player && eq(s.owner_character_id(), owner) && eq(s.subject_character_id(), player) && cycle > 0 && serial > 0
                && eq(s.route(), 1) && eq(s.offer_gold(), 50) && eq(s.receipt_serial(), serial)
                && eq(s.object_owner_character_id(), owner) && eq(s.object_subject_character_id(), player) && eq(s.object_cycle_serial(), cycle)
                && eq(s.object_receipt_case_serial(), serial) && eq(s.object_route(), 1)
                && (eq(s.state(), 1) && f(s.object_active()) && !f(s.object_consumed()) && !s.consumer_receipt_case_serial().available()
                || sourcePost && !f(s.object_active()) && f(s.object_consumed()) && eq(s.consumer_receipt_case_serial(), serial)), "#075 source is not canonical route A");
        require(conserved(hc.partition()) && n(hc.formal_case_serial()) > 0, "live HC conservation/formal lineage missing");
        long formalCase = n(hc.formal_case_serial()); boolean formalActive = f(hc.formal_active());
        boolean receiptTouched = !none(r), rehireTouched = !none(h);
        boolean workflowState = w.state().available();
        List<Datum<?>> pendingFields = List.of(w.pending(), w.pending_owner_character_id(), w.pending_subject_character_id(),
                w.pending_cycle_serial(), w.pending_case_serial(), w.pending_slot_case_serial());
        boolean pendingTouched = pendingFields.stream().anyMatch(Datum::available) || !none(w.pending_hc_before());
        boolean pendingReady = false, migrationReady = false, sealedReady = false, rehireReady = false, currentMatches = false;
        Lifecycle derived;
        if (rehireTouched || receiptTouched) {
            require(all(r) && sourcePost && !pendingTouched && workflowState && eq(w.state(), 4)
                    && !w.pending_hc_migration_authorized().available() && none(w.pending_hc_before()), "sealed stage incomplete or retains pending fields");
            require(migration(r.hc_before(), r.hc_after()) && f(r.active()) && f(r.sealed()) && f(r.published()) && f(r.consumed())
                    && f(r.hc_ledger_settled()) && f(r.hc_destination_frozen()) && f(r.hc_conservation_verified())
                    && f(r.formal_hc_active_before()) && !f(r.formal_hc_active_after()) && eq(r.consumed_operation(), 75)
                    && eq(r.owner_character_id(), owner) && eq(r.subject_character_id(), player) && eq(r.cycle_serial(), cycle)
                    && eq(r.case_serial(), serial) && eq(r.state(), 6) && n(r.receipt_id()) > 0 && n(r.receipt_hash()) > 0
                    && n(r.formal_hc_case_serial()) > 0, "sealed normal-exit receipt inconsistent");
            migrationReady = true; sealedReady = true;
            currentMatches = hc.partition().equals(r.hc_after()) && !formalActive && eq(r.formal_hc_case_serial(), formalCase);
            if (rehireTouched) {
                require(all(h) && n(h.state()) >= 1 && eq(h.subject_character_id(), player) && eq(h.exit_owner_character_id(), owner)
                        && eq(h.exit_cycle_serial(), cycle) && eq(h.exit_case_serial(), serial) && eq(h.exit_state(), 6)
                        && h.exit_receipt_id().equals(r.receipt_id()) && h.exit_receipt_hash().equals(r.receipt_hash())
                        && f(h.normal_exit_verified()) && f(h.exit_hc_destination_frozen()) && f(h.exit_hc_conservation_verified())
                        && f(h.exit_formal_hc_active_before()) && !f(h.exit_formal_hc_active_after())
                        && h.exit_formal_hc_case_serial().equals(r.formal_hc_case_serial())
                        && h.exit_hc_before().equals(r.hc_before()) && h.exit_hc_after().equals(r.hc_after()), "rehire did not preserve sealed provenance");
                rehireReady = true; derived = Lifecycle.REHIRE_CAPTURED;
            } else { require(none(h), "sealed stage leaked partial rehire"); derived = Lifecycle.SEALED; }
        } else {
            require(none(r) && none(h), "pre-seal stage leaked receipts");
            derived = workflowState && eq(w.state(), 3) ? Lifecycle.MIGRATING : Lifecycle.PRE;
            if (pendingTouched) {
                require(pendingFields.stream().allMatch(Datum::available) && all(w.pending_hc_before()) && conserved(w.pending_hc_before())
                        && f(w.pending()) && eq(w.pending_owner_character_id(), owner) && eq(w.pending_subject_character_id(), player)
                        && eq(w.pending_cycle_serial(), cycle) && eq(w.pending_case_serial(), serial)
                        && eq(w.pending_slot_case_serial(), formalCase), "pending snapshot is not bound to #075/live HC");
                pendingReady = true;
            } else require(none(w), "workflow/HC exists without pending identity");
            if (derived == Lifecycle.MIGRATING) {
                require(pendingReady && sourcePost && f(w.pending_hc_migration_authorized())
                        && migration(w.pending_hc_before(), hc.partition()) && !formalActive, "migration lacks occupied-to-frozen delta");
                migrationReady = true; currentMatches = true;
            } else if (sourcePost) {
                require(pendingReady && workflowState && eq(w.state(), 2) && !w.pending_hc_migration_authorized().available()
                        && hc.partition().equals(w.pending_hc_before()) && formalActive, "accepted-before-migration stage inconsistent");
                currentMatches = true;
            } else if (pendingReady) {
                require(!workflowState && !w.pending_hc_migration_authorized().available()
                        && hc.partition().equals(w.pending_hc_before()) && formalActive, "pre-migration HC drift");
                currentMatches = true;
            }
        }
        CareerReadiness.NormalExit expected = new CareerReadiness.NormalExit(currentMatches, true, true, migrationReady, true,
                pendingReady, true, true, rehireReady, true, sealedReady, true);
        require(lifecycle == derived && readiness.equals(expected), "normal-exit lifecycle/readiness is not the highest complete proven stage");
    }
}
