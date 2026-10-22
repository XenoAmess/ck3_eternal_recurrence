package org.xar.ck3.control.military.defenderrisk;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure observation envelope. Soldier counts and clocks never become exit authority. */
public final class DefenderContinueRisk {
    public static final String POLICY = "formal-defender-continue-risk-envelope-v1";
    public static final BigInteger RAW_TICKS_PER_DAY = BigInteger.valueOf(24);
    public static final BigInteger MAX_SIEGE_DAYS = BigInteger.valueOf(Integer.MAX_VALUE / 24);

    private DefenderContinueRisk() { }

    /** Python-only numeric wire domain: retain arbitrary precision, without a JS Number hop. */
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                        BigInteger dateRaw, String episodeRunId, BigInteger connectionGeneration,
                        BigInteger playedCharacterId, BigInteger warId,
                        BigInteger playerRelativeWarScore) {
        public Frame {
            StrictJson.text(snapshotId);
            StrictJson.text(episodeRunId);
            positive(revision, "revision");
            positive(nativeRevision, "native_revision");
            positive(connectionGeneration, "connection_generation");
            positive(playedCharacterId, "played_character_id");
            positive(warId, "war_id");
            present(dateRaw, "date_raw");
            present(playerRelativeWarScore, "player_relative_war_score");
        }
    }

    public record OffsiteArrival(BigInteger armyId, BigInteger arrivalDateRaw) {
        public OffsiteArrival {
            positive(armyId, "offsite army ID");
            present(arrivalDateRaw, "offsite arrival date");
        }
    }

    /** Opaque conflicts are not interpreted by this policy; only list emptiness is observed. */
    public record ConflictEvidence(String json) {
        public ConflictEvidence {
            require(json != null, "conflict JSON required");
            json = DefenderContinueRiskCodec.normalizeConflictJson(json);
        }
    }

    public record Contact(Frame sourceFrame, String sourceSha256, BigInteger subjectArmyId,
                          BigInteger targetProvinceId, BigInteger horizonStartDateRaw,
                          BigInteger horizonEndDateRaw, boolean oneDayContactFree,
                          List<ConflictEvidence> conflicts, BigInteger firstWaypointArrivalDateRaw,
                          BigInteger subjectTargetArrivalDateRaw, List<OffsiteArrival> offsiteTargetArrivals) {
        public Contact {
            require(sourceFrame != null, "contact source frame required");
            sha(sourceSha256);
            positive(subjectArmyId, "subject_army_id");
            positive(targetProvinceId, "target_province_id");
            present(horizonStartDateRaw, "horizon_start_date_raw");
            present(horizonEndDateRaw, "horizon_end_date_raw");
            require(horizonStartDateRaw.equals(sourceFrame.dateRaw())
                    && horizonEndDateRaw.compareTo(horizonStartDateRaw) > 0
                    && horizonEndDateRaw.compareTo(horizonStartDateRaw.add(RAW_TICKS_PER_DAY)) <= 0,
                    "contact horizon is not a bounded current game day");
            require(conflicts != null && offsiteTargetArrivals != null, "contact lists required");
            conflicts = List.copyOf(conflicts);
            offsiteTargetArrivals = List.copyOf(offsiteTargetArrivals);
            futureOrNull(firstWaypointArrivalDateRaw, horizonStartDateRaw, "first waypoint");
            futureOrNull(subjectTargetArrivalDateRaw, horizonStartDateRaw, "target arrival");
            require(firstWaypointArrivalDateRaw == null || subjectTargetArrivalDateRaw == null
                    || firstWaypointArrivalDateRaw.compareTo(subjectTargetArrivalDateRaw) <= 0,
                    "first waypoint cannot arrive after target");
            Set<BigInteger> seen = new HashSet<>();
            for (OffsiteArrival row : offsiteTargetArrivals) {
                require(!row.armyId().equals(subjectArmyId) && seen.add(row.armyId())
                        && row.arrivalDateRaw().compareTo(horizonStartDateRaw) > 0,
                        "offsite arrival ID/date invalid");
            }
        }
    }

    public record Siege(Frame sourceFrame, String sourceSha256, BigInteger provinceId,
                        List<BigInteger> besiegingArmyIds, BigInteger remainingDaysEstimate) {
        public Siege {
            require(sourceFrame != null, "siege source frame required");
            sha(sourceSha256);
            positive(provinceId, "siege province ID");
            require(besiegingArmyIds != null && !besiegingArmyIds.isEmpty(), "siege besieger list invalid");
            besiegingArmyIds = List.copyOf(besiegingArmyIds);
            Set<BigInteger> seen = new HashSet<>();
            for (BigInteger armyId : besiegingArmyIds) {
                positive(armyId, "besieging army ID");
                require(seen.add(armyId), "siege besieger list invalid");
            }
            require(remainingDaysEstimate != null && remainingDaysEstimate.signum() >= 0
                    && remainingDaysEstimate.compareTo(MAX_SIEGE_DAYS) <= 0, "siege timer estimate invalid");
        }
    }

    /** Null contact/siege means absent observation, not an empty or partial object. */
    public record Request(Frame frame, Contact contact, Siege siege) {
        public Request {
            require(frame != null, "complete defender war frame required");
            require(contact == null || contact.sourceFrame().equals(frame), "contact crossed native frame");
            require(siege == null || siege.sourceFrame().equals(frame), "siege crossed native frame");
            require(contact == null || siege == null || siege.provinceId().equals(contact.targetProvinceId()),
                    "siege clock and route target crossed provinces");
        }
    }

    public enum ContactStatus {
        TYPED_UNAVAILABLE("typed_unavailable"),
        BOUNDED_CURRENT_ORDERS_ONE_DAY_ONLY("bounded_current_orders_one_day_only"),
        CONTACT_RISK_OR_HORIZON_UNAVAILABLE("contact_risk_or_horizon_unavailable");
        private final String wire;
        ContactStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum ArrivalOrder {
        UNAVAILABLE("unavailable"),
        LISTED_OFFSITE_HOSTILE_MAY_PRECEDE_TARGET_ENTRY("listed_offsite_hostile_may_precede_target_entry"),
        LISTED_OFFSITE_ARRIVALS_LATER_UNDER_CURRENT_ORDERS("listed_offsite_arrivals_later_under_current_orders");
        private final String wire;
        ArrivalOrder(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public enum Blocker {
        CURRENT_CB_MATERIAL_TERMS_REQUIRED("current_cb_material_terms_required"),
        CURRENT_ASSET_EXPOSURE_AND_VALUATION_REQUIRED("current_asset_exposure_and_valuation_required"),
        FINITE_HORIZON_TAIL_LOSS_UPPER_REQUIRED("finite_horizon_tail_loss_upper_required"),
        FINITE_HORIZON_WAR_CASH_UPPER_REQUIRED("finite_horizon_war_cash_upper_required"),
        COMPLETE_ENCOUNTER_PARTICIPANT_SCOPE_REQUIRED("complete_encounter_participant_scope_required"),
        SAME_FRAME_ROUTE_CONTACT_REQUIRED("same_frame_route_contact_required"),
        SAME_FRAME_CONTACT_FREE_DAY_NOT_PROVEN("same_frame_contact_free_day_not_proven"),
        OFFSITE_HOSTILE_MAY_JOIN_BY_TARGET_ENTRY("offsite_hostile_may_join_by_target_entry"),
        SAME_FRAME_SIEGE_CLOCK_REQUIRED("same_frame_siege_clock_required");
        private final String wire;
        Blocker(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    public sealed interface ContactResult permits UnavailableContact, ObservedContact { }
    public record UnavailableContact() implements ContactResult { }
    public record ObservedContact(ContactStatus status, BigInteger contactFreeThroughRaw,
                                  Boolean firstWaypointOutsideProvenWindow, ArrivalOrder arrivalOrder,
                                  BigInteger targetArrivalDateRaw, String sourceSha256) implements ContactResult {
        public ObservedContact {
            require(status != null && status != ContactStatus.TYPED_UNAVAILABLE && arrivalOrder != null,
                    "observed contact status required");
            require(status == ContactStatus.BOUNDED_CURRENT_ORDERS_ONE_DAY_ONLY
                    ? contactFreeThroughRaw != null
                    : contactFreeThroughRaw == null && firstWaypointOutsideProvenWindow == null,
                    "contact bound must follow its typed status");
            sha(sourceSha256);
        }
    }
    public sealed interface SiegeResult permits UnavailableSiege, ObservedSiege { }
    public record UnavailableSiege() implements SiegeResult { }
    public record ObservedSiege(BigInteger provinceId, List<BigInteger> besiegingArmyIds,
                                BigInteger remainingDaysEstimate, BigInteger completionEstimateRaw,
                                String sourceSha256) implements SiegeResult {
        public ObservedSiege {
            positive(provinceId, "siege province ID");
            require(besiegingArmyIds != null && remainingDaysEstimate != null && completionEstimateRaw != null,
                    "complete observed siege required");
            besiegingArmyIds = List.copyOf(besiegingArmyIds);
            require(!besiegingArmyIds.isEmpty() && new HashSet<>(besiegingArmyIds).size() == besiegingArmyIds.size(),
                    "siege besieger list invalid");
            besiegingArmyIds.forEach(army -> positive(army, "besieging army ID"));
            require(remainingDaysEstimate.signum() >= 0 && remainingDaysEstimate.compareTo(MAX_SIEGE_DAYS) <= 0,
                    "siege timer estimate invalid");
            sha(sourceSha256);
        }
    }
    public record Envelope(Frame frame, ContactResult contact, SiegeResult siege, List<Blocker> blockers) {
        public Envelope {
            require(frame != null && contact != null && siege != null && blockers != null, "complete risk envelope required");
            blockers = List.copyOf(blockers);
        }
    }

    public static Envelope observe(Request request) {
        require(request != null, "risk request required");
        Set<Blocker> blockers = new TreeSet<>((left, right) -> left.wire().compareTo(right.wire()));
        blockers.addAll(List.of(Blocker.CURRENT_CB_MATERIAL_TERMS_REQUIRED,
                Blocker.CURRENT_ASSET_EXPOSURE_AND_VALUATION_REQUIRED,
                Blocker.FINITE_HORIZON_TAIL_LOSS_UPPER_REQUIRED,
                Blocker.FINITE_HORIZON_WAR_CASH_UPPER_REQUIRED,
                Blocker.COMPLETE_ENCOUNTER_PARTICIPANT_SCOPE_REQUIRED));
        ContactResult contactResult;
        Contact contact = request.contact();
        if (contact == null) {
            contactResult = new UnavailableContact();
            blockers.add(Blocker.SAME_FRAME_ROUTE_CONTACT_REQUIRED);
        } else {
            boolean free = contact.oneDayContactFree() && contact.conflicts().isEmpty()
                    && contact.horizonStartDateRaw().equals(request.frame().dateRaw())
                    && contact.horizonEndDateRaw().equals(request.frame().dateRaw().add(RAW_TICKS_PER_DAY));
            ArrivalOrder order = ArrivalOrder.UNAVAILABLE;
            if (!contact.offsiteTargetArrivals().isEmpty() && contact.subjectTargetArrivalDateRaw() != null) {
                boolean earlier = contact.offsiteTargetArrivals().stream().anyMatch(row ->
                        row.arrivalDateRaw().compareTo(contact.subjectTargetArrivalDateRaw()) <= 0);
                order = earlier ? ArrivalOrder.LISTED_OFFSITE_HOSTILE_MAY_PRECEDE_TARGET_ENTRY
                        : ArrivalOrder.LISTED_OFFSITE_ARRIVALS_LATER_UNDER_CURRENT_ORDERS;
            }
            contactResult = new ObservedContact(free ? ContactStatus.BOUNDED_CURRENT_ORDERS_ONE_DAY_ONLY
                    : ContactStatus.CONTACT_RISK_OR_HORIZON_UNAVAILABLE,
                    free ? contact.horizonEndDateRaw() : null,
                    free && contact.firstWaypointArrivalDateRaw() != null
                            ? contact.firstWaypointArrivalDateRaw().compareTo(contact.horizonEndDateRaw()) > 0 : null,
                    order, contact.subjectTargetArrivalDateRaw(), contact.sourceSha256());
            if (!free) { blockers.add(Blocker.SAME_FRAME_CONTACT_FREE_DAY_NOT_PROVEN); }
            if (order == ArrivalOrder.LISTED_OFFSITE_HOSTILE_MAY_PRECEDE_TARGET_ENTRY) {
                blockers.add(Blocker.OFFSITE_HOSTILE_MAY_JOIN_BY_TARGET_ENTRY);
            }
        }
        SiegeResult siegeResult;
        Siege siege = request.siege();
        if (siege == null) {
            siegeResult = new UnavailableSiege();
            blockers.add(Blocker.SAME_FRAME_SIEGE_CLOCK_REQUIRED);
        } else {
            siegeResult = new ObservedSiege(siege.provinceId(), siege.besiegingArmyIds(), siege.remainingDaysEstimate(),
                    request.frame().dateRaw().add(siege.remainingDaysEstimate().multiply(RAW_TICKS_PER_DAY)),
                    siege.sourceSha256());
        }
        return new Envelope(request.frame(), contactResult, siegeResult, List.copyOf(blockers));
    }

    private static void positive(BigInteger value, String name) {
        require(value != null && value.signum() > 0, name + " must be positive integer");
    }
    private static void present(BigInteger value, String name) {
        require(value != null, name + " must be integer");
    }
    private static void futureOrNull(BigInteger value, BigInteger start, String name) {
        require(value == null || value.compareTo(start) > 0, name + " must be future raw date or null");
    }
    private static void sha(String value) {
        require(value != null && value.matches("[0-9A-F]{64}"), "source SHA-256 required");
    }
}
