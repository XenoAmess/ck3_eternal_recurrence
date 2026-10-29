package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Commitments;
import org.xar.ck3.control.planning.opportunity.ObservedOpportunitySelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Domain;
import org.xar.ck3.control.wave2.planning.jointintake.IntakeModel.Frame;

/**
 * Java continuation of M5FrameDispatcher.choose_observed. The existing caller owns
 * one shared instance for the entire paused frame. This is an in-memory analytic
 * reservation, never a durable intent, native submission or campaign ledger writer.
 */
public final class M5FrameDispatcher {
    public enum Status { reserved_observed_analytic, already_reserved_this_frame, wait }
    public record ObservedCost(BigInteger goldCostRaw, BigInteger warSlotClaim,
                               Optional<BigInteger> projectedSupplyMarginRaw) {
        public ObservedCost {
            nonnegativeAmount(goldCostRaw); nonnegativeAmount(warSlotClaim);
            require(warSlotClaim.compareTo(BigInteger.ONE) <= 0, "zero or one observed war slot required");
            Objects.requireNonNull(projectedSupplyMarginRaw);
        }
    }
    public record Reservation(Frame frame, String candidateId, Domain domain, String sourcePolicy,
                              Commitments commitmentsAfter, ObservedCost observedCost) {
        public Reservation {
            Objects.requireNonNull(frame); nonempty(candidateId); Objects.requireNonNull(domain);
            nonempty(sourcePolicy); Objects.requireNonNull(commitmentsAfter); Objects.requireNonNull(observedCost);
        }
    }
    public record Dispatch(Status status, Frame frame, Optional<String> selectedCandidateId,
                           Optional<Reservation> reservation, Optional<Obj> analysis) {
        public Dispatch {
            Objects.requireNonNull(status); Objects.requireNonNull(frame); Objects.requireNonNull(selectedCandidateId);
            Objects.requireNonNull(reservation); Objects.requireNonNull(analysis);
            reservation.ifPresent(value -> require(frame.equals(value.frame()), "reservation crossed the paused frame"));
            switch (status) {
                case reserved_observed_analytic -> {
                    require(selectedCandidateId.isPresent() && reservation.isPresent() && analysis.isPresent(), "actual reservation result required");
                    require(selectedCandidateId.orElseThrow().equals(reservation.orElseThrow().candidateId()), "selected reservation identity differs");
                }
                case already_reserved_this_frame -> require(selectedCandidateId.isEmpty() && reservation.isPresent() && analysis.isEmpty(), "existing reservation result required");
                case wait -> require(selectedCandidateId.isEmpty() && reservation.isEmpty() && analysis.isPresent(), "wait has no reservation");
            }
        }
        public boolean formalActionReady() { return false; }
        public boolean intentDurable() { return false; }
    }
    /** A lock-consistent read of this existing owner; it does not create an owner or a durable commitment. */
    public record ResourceSnapshot(G2Source source, Frame frame, Commitments commitments, Optional<Reservation> reservation) {
        public ResourceSnapshot {
            Objects.requireNonNull(source); Objects.requireNonNull(frame); Objects.requireNonNull(commitments); Objects.requireNonNull(reservation);
            reservation.ifPresent(value -> require(frame.equals(value.frame()) && commitments.equals(value.commitmentsAfter()), "resource snapshot differs from its actual owner reservation"));
        }
    }

    private final G2Source source;
    private final Frame frame;
    private final Obj snapshot;
    private final Commitments commitments;
    private Reservation reservation;

    public M5FrameDispatcher(G2Source source, Obj snapshot, Obj existingCommitments) {
        this.source = Objects.requireNonNull(source);
        require(source.sourceRef().bytes() > 0, "original source reference required for frame owner");
        this.snapshot = Objects.requireNonNull(snapshot);
        paused(snapshot); this.frame = frame(snapshot, false);
        this.commitments = commitments(existingCommitments, frame);
    }

    /** Re-evaluates the actual shared selector while holding this same frame owner's lock. */
    public synchronized Dispatch chooseObserved(G2Source originalSource, Obj selectorRequest) {
        require(source.equals(originalSource), "reservation source differs from the existing frame owner");
        Objects.requireNonNull(selectorRequest);
        require(selectorRequest.members().keySet().equals(Set.of("snapshot", "proposals", "commitments", "gold_reserve_raw", "max_active_wars")), "exact observed selector request required");
        Obj current = object(selectorRequest.get("snapshot"), "current snapshot"); paused(current);
        require(frame.equals(frame(current, false)) && snapshot.equals(current), "reservation snapshot differs from the owner observation");
        require(commitments.equals(commitments(object(selectorRequest.get("commitments"), "current commitments"), frame)), "reservation commitments differ from the owner observation");
        if (reservation != null) return new Dispatch(Status.already_reserved_this_frame, frame, Optional.empty(), Optional.of(reservation), Optional.empty());
        Obj analysis = M5PayloadCodec.parseObject(ObservedOpportunitySelector.select(OpportunityJson.encode(selectorRequest)), "actual observed selector result");
        Value selectedId = analysis.get("selected_candidate_id");
        if (selectedId == Nil.INSTANCE) return new Dispatch(Status.wait, frame, Optional.empty(), Optional.empty(), Optional.of(analysis));
        String candidate = text(selectedId, "selected candidate");
        Obj selected = array(analysis.get("evaluated"), "evaluated candidates").stream().map(value -> object(value, "evaluated candidate"))
                .filter(value -> new Text(candidate).equals(value.get("candidate_id"))).findFirst().orElseThrow();
        require(new Text("eligible").equals(selected.get("reason")), "only the actual eligible selector winner can reserve");
        BigInteger gold = nonnegative(selected.get("gold_cost_raw"), "selected gold");
        BigInteger slots = nonnegative(selected.get("war_slot_claim"), "selected war slot");
        Claims selectedClaims = claims(selected);
        Commitments after = new Commitments(commitments.goldRaw().add(gold), commitments.pendingWarSlots().add(slots), union(commitments.claims(), selectedClaims));
        Value supply = selected.get("projected_supply_margin_raw");
        ObservedCost cost = new ObservedCost(gold, slots, supply == null || supply == Nil.INSTANCE ? Optional.empty() : Optional.of(integer(supply, "selected supply")));
        reservation = new Reservation(frame, candidate, Domain.valueOf(text(selected.get("domain"), "selected domain")), text(selected.get("source_policy"), "selected policy"), after, cost);
        return new Dispatch(Status.reserved_observed_analytic, frame, Optional.of(candidate), Optional.of(reservation), Optional.of(analysis));
    }

    public synchronized ResourceSnapshot resourceSnapshot() {
        return new ResourceSnapshot(source, frame, reservation == null ? commitments : reservation.commitmentsAfter(), Optional.ofNullable(reservation));
    }

    static Frame frame(Obj value, boolean exact) {
        if (exact) require(value.members().keySet().equals(Set.of("played_character_id", "native_revision", "date_raw", "snapshot_id", "revision", "episode_run_id")), "exact six-field frame required");
        Value player = value.get("played_character_id");
        if ((player == null || player == Nil.INSTANCE) && !exact) player = object(value.get("played_character"), "played character").get("character_id");
        return new Frame(integer(player, "played character ID"), integer(value.get("native_revision"), "native revision"), integer(value.get("date_raw"), "date raw"),
                text(value.get("snapshot_id"), "snapshot ID"), integer(value.get("revision"), "revision"), text(value.get("episode_run_id"), "episode"));
    }
    static Commitments commitments(Obj value, Frame expectedFrame) {
        require(value.members().keySet().equals(Set.of("frame", "gold_raw", "pending_war_slots", "army_ids", "ally_character_ids", "character_ids", "commitment_keys")), "exact observed commitment fields required");
        require(frame(object(value.get("frame"), "commitment frame"), true).equals(expectedFrame), "commitments crossed the paused frame");
        return new Commitments(nonnegative(value.get("gold_raw"), "committed gold"), nonnegative(value.get("pending_war_slots"), "pending war slots"), claims(value));
    }
    static Claims claims(Obj value) {
        Set<String> keys = new HashSet<>();
        for (Value key : array(value.get("commitment_keys"), "commitment keys")) require(keys.add(text(key, "commitment key")), "duplicate commitment key");
        return new Claims(ids(value.get("army_ids"), false), ids(value.get("ally_character_ids"), true), ids(value.get("character_ids"), true), keys);
    }
    private static Set<BigInteger> ids(Value value, boolean positive) {
        Set<BigInteger> result = new HashSet<>();
        for (Value item : array(value, "resource IDs")) {
            BigInteger id = integer(item, "exact resource integer"); require(id.signum() >= (positive ? 1 : 0), "resource ID out of range");
            require(result.add(id), "duplicate resource ID");
        }
        return result;
    }
    private static Claims union(Claims first, Claims second) {
        return new Claims(union(first.armyIds(), second.armyIds()), union(first.allyCharacterIds(), second.allyCharacterIds()), union(first.characterIds(), second.characterIds()), union(first.commitmentKeys(), second.commitmentKeys()));
    }
    private static <T> Set<T> union(Set<T> first, Set<T> second) { Set<T> result = new HashSet<>(first); result.addAll(second); return result; }
    private static void paused(Obj value) { require(new Bool(true).equals(value.get("paused")) && new Bool(true).equals(value.get("map_ready")), "paused map observation required"); }
    private static void nonnegativeAmount(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative resource amount required"); }
    private static void nonempty(String value) { require(value != null && !value.isEmpty(), "nonempty identity required"); }
}
