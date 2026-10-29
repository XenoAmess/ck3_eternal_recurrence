package org.xar.ck3.control.nativebridge.capabilities.china_career;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.china_career.CareerJson.*;

public final class OwnerCareerFrames {
    private OwnerCareerFrames() { }
    public enum TerminalKind { NONE, SUCCESS, HISTORY_ACCRUING, NOT_APPLICABLE }
    public record Owner(Header header, OwnerGroups.Central central, OwnerGroups.Source source,
            OwnerGroups.AlCase al_case, OwnerGroups.M360Receipt m360_receipt, OwnerGroups.Portfolio portfolio,
            CareerReadiness.Owner readiness, boolean terminal, TerminalKind terminal_kind) { }
    public record Career(Header header, CareerGroups.Identity m360_identity, CareerGroups.Receipt m360_receipt,
            CareerGroups.Partition career_hc_partition, CareerGroups.Cost route_b_cost,
            CareerReadiness.Career readiness, CareerProvenance provenance) { }

    public static Owner decodeOwner(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "capability", "source_backend_id", "request_nonce", "snapshot_revision",
                "date_raw", "paused", "player_character_id", "subject_character_id", "workforce", "readiness",
                "terminal", "terminal_kind", "unavailable_reason");
        require(text(row.get("capability")).equals("game.command.query-zhongguo-workforce-owner-snapshot-v1")
                && text(row.get("source_backend_id")).equals("ck3-1.19.0.6-native-zhongguo-workforce-owner-snapshot-v1")
                && binding.owner_character_id() == binding.player_character_id(), "owner collector source/player binding changed");
        Header header = header(row, binding, false, false);
        JsonNode workforce = exact(row.get("workforce"), "central", "source", "al_case", "m360_receipt", "portfolio");
        OwnerGroups.Central central = OwnerGroups.Central.parse(workforce.get("central"));
        OwnerGroups.Source source = OwnerGroups.Source.parse(workforce.get("source"));
        OwnerGroups.AlCase al = OwnerGroups.AlCase.parse(workforce.get("al_case"));
        OwnerGroups.M360Receipt receipt = OwnerGroups.M360Receipt.parse(workforce.get("m360_receipt"));
        OwnerGroups.Portfolio portfolio = OwnerGroups.Portfolio.parse(workforce.get("portfolio"));
        CareerReadiness.Owner readiness = CareerReadiness.Owner.parse(row.get("readiness"));
        require(readiness.ready() == (readiness.player_owner_binding_ready() && readiness.portfolio_subject_binding_ready()
                && readiness.case_identity_ready() && readiness.same_frame_ready()), "owner readiness aggregate changed");
        TerminalKind kind = switch (text(row.get("terminal_kind"))) {
            case "none" -> TerminalKind.NONE; case "success" -> TerminalKind.SUCCESS;
            case "history_accruing" -> TerminalKind.HISTORY_ACCRUING; case "not_applicable" -> TerminalKind.NOT_APPLICABLE;
            default -> throw new IllegalArgumentException("unknown Workforce terminal branch");
        };
        boolean terminal = bool(row.get("terminal"));
        require(terminal == (kind != TerminalKind.NONE) && (!terminal || readiness.ready()), "terminal frame is not observable");
        return new Owner(header, central, source, al, receipt, portfolio, readiness, terminal, kind);
    }
    public static Career decodeCareer(RawJson originalFrame, FrameBinding binding) {
        JsonNode row = parse(originalFrame);
        exact(row, "schema_version", "status", "capability", "case_kind", "source_backend_id", "request_nonce",
                "snapshot_revision", "date_raw", "paused", "player_character_id", "subject_character_id",
                "requested_owner_character_id", "m360_identity", "m360_receipt", "career_hc_partition", "route_b_cost",
                "readiness", "provenance", "unavailable_reason");
        require(text(row.get("capability")).equals("game.command.query-zhongguo-career-hc-workforce-postcondition-v1")
                && text(row.get("case_kind")).equals("zhongguo.career-hc.workforce.route-b-no-hc-debit")
                && text(row.get("source_backend_id")).equals("native-headless")
                && binding.owner_character_id() != binding.player_character_id(), "career received-self source binding changed");
        Header header = header(row, binding, true, true);
        CareerGroups.Identity identity = CareerGroups.Identity.parse(row.get("m360_identity"));
        CareerGroups.Receipt receipt = CareerGroups.Receipt.parse(row.get("m360_receipt"));
        CareerGroups.Partition partition = CareerGroups.Partition.parse(row.get("career_hc_partition"));
        CareerGroups.Cost cost = CareerGroups.Cost.parse(row.get("route_b_cost"));
        CareerReadiness.Career readiness = CareerReadiness.Career.parse(row.get("readiness"));
        CareerProvenance provenance = CareerProvenance.parse(row.get("provenance"), CareerProvenance.Profile.CAREER_HC);
        boolean aggregate = readiness.player_subject_binding_ready() && readiness.owner_binding_ready()
                && readiness.m360_identity_ready() && readiness.m360_route_b_receipt_ready() && readiness.career_hc_partition_ready()
                && readiness.career_hc_conservation_ready() && readiness.route_b_manager_cost_zero_ready() && readiness.same_frame_ready();
        require(readiness.ready() == aggregate, "career readiness aggregate changed");
        if (header.status() == Availability.AVAILABLE) {
            require(readiness.ready() && receipt.provider_observed() && partition.provider_observed() && cost.provider_observed()
                    && all(identity) && all(receipt) && all(partition) && all(cost), "career native products were not observed");
            require(identity.owner_character_id().equals(receipt.owner_character_id())
                    && identity.subject_character_id().equals(receipt.subject_character_id())
                    && identity.cycle_serial().equals(receipt.cycle_serial()) && identity.case_serial().equals(receipt.case_serial())
                    && eq(identity.owner_character_id(), binding.owner_character_id())
                    && eq(identity.subject_character_id(), binding.player_character_id())
                    && eq(receipt.state(), 4) && eq(receipt.choice(), 2), "M360 route-B receipt/identity mismatch");
            require(java.util.List.of(partition.authorized(), partition.available(), partition.reserved(), partition.occupied(),
                    partition.frozen(), partition.reclaimed()).stream().allMatch(field -> field.observed().signum() >= 0), "career HC bucket is negative");
            BigInteger sum = partition.available().observed().add(partition.reserved().observed()).add(partition.occupied().observed())
                    .add(partition.frozen().observed()).add(partition.reclaimed().observed());
            require(partition.authorized().observed().equals(sum) && f(partition.conserved()) && eq(cost.manager_cost_total(), 0),
                    "route B career-HC conservation/zero manager debit not observed");
        }
        return new Career(header, identity, receipt, partition, cost, readiness, provenance);
    }
}
