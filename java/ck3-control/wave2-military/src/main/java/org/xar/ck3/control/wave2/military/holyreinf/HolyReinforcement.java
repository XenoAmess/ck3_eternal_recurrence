package org.xar.ck3.control.wave2.military.holyreinf;

import java.math.BigInteger;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Current blocked-siege quote comparison. It neither submits a hire nor predicts arrival or victory. */
public final class HolyReinforcement {
    public static final String SCHEMA = "xar.ck3.holy-order-siege-reinforcement-proposal.v1";
    public static final String STEP = "hire-holy-order-v1";
    public static final String CAPABILITY = "game.command." + STEP;
    private HolyReinforcement() { }

    public enum Status { NOT_APPLICABLE, INPUT_UNAVAILABLE, NO_ELIGIBLE_REINFORCEMENT, ACTIONABLE }
    public enum PostStatus { VERIFICATION_PENDING, NOT_SUBMITTED, EMPLOYER_OBSERVED_ARMY_PENDING,
        EMPLOYER_AND_USABLE_ARMY_OBSERVED }
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision,
            BigInteger dateRaw, Long playedCharacterId) { }
    public record Stocks(BigInteger gold, BigInteger prestige, BigInteger piety) {
        public List<BigInteger> orderedNullable() { return java.util.Arrays.asList(gold, prestige, piety); }
    }
    public record PublicArmy(long armyId, Long ownerCharacterId, Boolean controllable, Long currentProvinceId) { }
    public record Snapshot(Frame frame, Boolean paused, Boolean mapReady, Boolean actorAlive,
            List<BigInteger> activeWarIds, Stocks stocks, List<PublicArmy> playerArmies, String version, String sha) {
        public Snapshot {
            Objects.requireNonNull(frame); Objects.requireNonNull(stocks);
            activeWarIds = activeWarIds == null ? null : List.copyOf(activeWarIds);
            playerArmies = List.copyOf(playerArmies);
        }
    }
    public record Siege(String status, Boolean playerArmyBesieging, BigInteger provinceId,
            BigInteger garrisonSize, BigInteger besiegingStrength) { }
    public record Plan(String phase, String selectedStep, Siege siege, BigInteger pursuitWarId) { }
    public record Need(BigInteger warId, BigInteger targetProvinceId, BigInteger garrisonSize,
            BigInteger besiegingStrength, BigInteger additionalSoldiersRequired) { }
    public record Strength(boolean available, String unavailableReason, Integer currentSoldiers) { }
    public record AssociationMember(long regimentId, boolean available, String unavailableReason,
            boolean regimentResolved, Long nativeCarmyId, boolean nativeCarmyResolved,
            Long combatId, boolean combatResolved) { }
    public record Association(boolean available, String unavailableReason, boolean appliesToPlayer,
            List<AssociationMember> rows) {
        public Association { rows = List.copyOf(rows); }
    }
    public record Terms(boolean available, String unavailableReason, Boolean canHire, Boolean canAfford,
            String canHireReason, String canAffordReason, List<BigInteger> resourceCostsRaw,
            Strength troopStrength, Association troopAssociation) {
        public Terms { resourceCostsRaw = resourceCostsRaw == null ? null : List.copyOf(resourceCostsRaw); }
    }
    public record Order(long holyOrderId, boolean military, Long employerId, Terms terms) { }
    public record Context(boolean available, String unavailableReason, long playedCharacterId,
            BigInteger queriedRevision, BigInteger queriedNativeRevision, List<Order> rows) {
        public Context { rows = List.copyOf(rows); }
    }
    public record CandidateEvaluation(long holyOrderId, int sourceOrdinal, Boolean canHire, Boolean canAfford,
            String canHireReason, String canAffordReason, String reason) { }
    public record Selection(long holyOrderId, int sourceOrdinal, Long priorEmployerId,
            List<BigInteger> nativeQuoteRaw, int currentSoldiers) {
        public Selection { nativeQuoteRaw = List.copyOf(nativeQuoteRaw); }
    }
    public record Proposal(Status status, Frame sourceFrame, Need militaryNeed, Stocks beforeStocks,
            String unavailableReason, List<CandidateEvaluation> candidates, Selection selection) {
        public Proposal { candidates = List.copyOf(candidates); }
    }
    public record ArmyStrength(long armyId, String status, Long nativeCarmyId, BigInteger currentSoldiers) { }
    public record MaterialArmy(long armyId, long nativeCarmyId, BigInteger currentSoldiers,
            Long ownerCharacterId, Long currentProvinceId) { }
    public record NextFormal(long armyId, BigInteger targetProvinceId, BigInteger expectedRevision) {
        public String selectedStep() { return "preview-move-army-" + armyId + "-to-" + targetProvinceId; }
    }
    public record Postcondition(PostStatus status, long holyOrderId, boolean employerObserved,
            List<MaterialArmy> materialArmies, List<BigInteger> quote, Stocks beforeStocks,
            Stocks afterStocks, Stocks observedDelta, Boolean unchangedDateQuoteDeltaMatch,
            Frame afterSourceFrame, Long actualEmployerId, Association troopAssociation, NextFormal nextFormal) {
        public Postcondition { materialArmies = List.copyOf(materialArmies); quote = List.copyOf(quote); }
        public boolean usableArmyObserved() { return !materialArmies.isEmpty(); }
        public boolean fullHireLoopComplete() { return false; }
    }

    public static Need siegeNeed(Snapshot snapshot, Plan plan) {
        if (!"native_war_siege_exit_blocked".equals(plan.phase()) || plan.selectedStep() != null
                || !Boolean.TRUE.equals(snapshot.paused()) || !Boolean.TRUE.equals(snapshot.mapReady())
                || !Boolean.TRUE.equals(snapshot.actorAlive()) || plan.siege() == null
                || !"insufficient_strength".equals(plan.siege().status())
                || !Boolean.TRUE.equals(plan.siege().playerArmyBesieging())) { return null; }
        Siege siege = plan.siege(); BigInteger war = plan.pursuitWarId();
        if (!positive(war) || !positive(siege.provinceId()) || siege.garrisonSize() == null
                || siege.besiegingStrength() == null || siege.besiegingStrength().signum() < 0
                || siege.besiegingStrength().compareTo(siege.garrisonSize()) >= 0
                || snapshot.activeWarIds() == null || !snapshot.activeWarIds().contains(war)) { return null; }
        return new Need(war, siege.provinceId(), siege.garrisonSize(), siege.besiegingStrength(),
                siege.garrisonSize().subtract(siege.besiegingStrength()));
    }

    public static Proposal choose(Snapshot snapshot, Plan plan, Context context) {
        Need need = siegeNeed(snapshot, plan);
        if (need == null) { return new Proposal(Status.NOT_APPLICABLE, snapshot.frame(), null, null, null, List.of(), null); }
        Objects.requireNonNull(context, "current holy-order context required");
        if (!Objects.equals(context.queriedRevision(), snapshot.frame().revision())
                || !Objects.equals(context.queriedNativeRevision(), snapshot.frame().nativeRevision())) {
            throw new ProjectionDomainRejection("holy-order proposal differs from its actual queried frame");
        }
        if (!context.available()) {
            return new Proposal(Status.INPUT_UNAVAILABLE, snapshot.frame(), need, snapshot.stocks(),
                    context.unavailableReason(), List.of(), null);
        }
        List<CandidateEvaluation> evaluations = new ArrayList<>(); List<Selection> eligible = new ArrayList<>();
        for (int ordinal = 0; ordinal < context.rows().size(); ordinal++) {
            Order order = context.rows().get(ordinal); if (!order.military()) { continue; }
            Terms terms = order.terms(); Strength strength = terms.troopStrength(); String reason = null;
            if (Objects.equals(order.employerId(), context.playedCharacterId())) { reason = "already_employed_by_player"; }
            else if (!terms.available()) { reason = terms.unavailableReason(); }
            else if (!Boolean.TRUE.equals(terms.canHire())) { reason = "native_can_hire_false"; }
            else if (!Boolean.TRUE.equals(terms.canAfford())) { reason = "native_can_afford_false"; }
            else if (strength == null || !strength.available()) { reason = "current_soldiers_unavailable"; }
            else if (BigInteger.valueOf(strength.currentSoldiers()).compareTo(need.additionalSoldiersRequired()) < 0) {
                reason = "current_troops_do_not_cover_measured_deficit";
            } else {
                List<BigInteger> stocks = snapshot.stocks().orderedNullable(); String[] names = {"gold", "prestige", "piety"};
                for (int slot = 0; slot < 3; slot++) {
                    BigInteger stock = stocks.get(slot), cost = terms.resourceCostsRaw().get(slot);
                    if (stock == null) { reason = "current_" + names[slot] + "_stock_unavailable"; break; }
                    if (cost.signum() > 0 && cost.compareTo(stock) > 0) { reason = "quoted_" + names[slot] + "_exceeds_current_stock"; break; }
                }
                if (reason == null) { eligible.add(new Selection(order.holyOrderId(), ordinal, order.employerId(),
                        terms.resourceCostsRaw(), strength.currentSoldiers())); }
            }
            evaluations.add(new CandidateEvaluation(order.holyOrderId(), ordinal, terms.canHire(), terms.canAfford(),
                    terms.canHireReason(), terms.canAffordReason(), reason));
        }
        Selection selected = eligible.stream().min(Comparator.comparing((Selection row) -> row.nativeQuoteRaw().get(2))
                .thenComparing(row -> row.nativeQuoteRaw().get(0)).thenComparing(row -> row.nativeQuoteRaw().get(1))
                .thenComparingLong(Selection::holyOrderId).thenComparingInt(Selection::sourceOrdinal)).orElse(null);
        return new Proposal(selected == null ? Status.NO_ELIGIBLE_REINFORCEMENT : Status.ACTIONABLE,
                snapshot.frame(), need, snapshot.stocks(), null, evaluations, selected);
    }

    /** Independently compares measured values after an existing ACK; ACK alone never proves an army. */
    public static Postcondition comparePost(Proposal proposal, boolean accepted, Snapshot after,
            Context context, List<ArmyStrength> strengths) {
        if (proposal.status() != Status.ACTIONABLE || proposal.selection() == null) {
            throw new ProjectionDomainRejection("holy-order reinforcement lacks its valued current native proposal");
        }
        Selection selection = proposal.selection();
        if (!accepted || after == null || context == null) {
            return new Postcondition(accepted ? PostStatus.VERIFICATION_PENDING : PostStatus.NOT_SUBMITTED,
                    selection.holyOrderId(), false, List.of(), selection.nativeQuoteRaw(), proposal.beforeStocks(),
                    null, null, null, null, null, null, null);
        }
        List<Order> matches = context.rows().stream().filter(row -> row.holyOrderId() == selection.holyOrderId()).toList();
        Long employer = matches.size() == 1 ? matches.getFirst().employerId() : null;
        boolean employed = employer != null && Objects.equals(employer, after.frame().playedCharacterId());
        Stocks delta = delta(proposal.beforeStocks(), after.stocks()); Boolean quoteMatch = null;
        if (Objects.equals(after.frame().dateRaw(), proposal.sourceFrame().dateRaw())
                && selection.nativeQuoteRaw().subList(3, 10).stream().allMatch(value -> value.signum() == 0)
                && delta.orderedNullable().stream().allMatch(Objects::nonNull)) {
            quoteMatch = delta.orderedNullable().equals(selection.nativeQuoteRaw().subList(0, 3));
        }
        Association association = employed && matches.getFirst().terms() != null ? matches.getFirst().terms().troopAssociation() : null;
        Set<Long> references = new HashSet<>();
        if (association != null) {
            for (AssociationMember member : association.rows()) {
                if (member.available() && member.nativeCarmyResolved() && member.nativeCarmyId() != null) { references.add(member.nativeCarmyId()); }
            }
        }
        List<MaterialArmy> material = new ArrayList<>();
        for (ArmyStrength strength : strengths) {
            PublicArmy army = null;
            for (PublicArmy row : after.playerArmies()) { if (row.armyId() == strength.armyId()) { army = row; } }
            if ("available".equals(strength.status()) && references.contains(strength.nativeCarmyId()) && army != null
                    && Boolean.TRUE.equals(army.controllable()) && positive(strength.currentSoldiers())) {
                material.add(new MaterialArmy(army.armyId(), strength.nativeCarmyId(), strength.currentSoldiers(),
                        army.ownerCharacterId(), army.currentProvinceId()));
            }
        }
        MaterialArmy selected = material.stream().max(Comparator.comparing(MaterialArmy::currentSoldiers)
                .thenComparing(Comparator.comparingLong(MaterialArmy::armyId).reversed())).orElse(null);
        NextFormal next = selected == null ? null : new NextFormal(selected.armyId(), proposal.militaryNeed().targetProvinceId(), after.frame().revision());
        return new Postcondition(selected != null ? PostStatus.EMPLOYER_AND_USABLE_ARMY_OBSERVED
                : employed ? PostStatus.EMPLOYER_OBSERVED_ARMY_PENDING : PostStatus.VERIFICATION_PENDING,
                selection.holyOrderId(), employed, material, selection.nativeQuoteRaw(), proposal.beforeStocks(), after.stocks(), delta,
                quoteMatch, after.frame(), employer, association, next);
    }
    private static Stocks delta(Stocks before, Stocks after) {
        return new Stocks(subtract(before.gold(), after.gold()), subtract(before.prestige(), after.prestige()), subtract(before.piety(), after.piety()));
    }
    private static BigInteger subtract(BigInteger before, BigInteger after) { return before == null || after == null ? null : before.subtract(after); }
    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
}
