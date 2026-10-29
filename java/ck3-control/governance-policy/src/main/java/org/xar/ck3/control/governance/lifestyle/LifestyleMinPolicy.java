package org.xar.ck3.control.governance.lifestyle;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyleperks.AllLifestylePerkPolicyV3;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel;

/** Pure LIFE2 minimum policy. No native legality inference, request ID, or submit authority. */
public final class LifestyleMinPolicy {
    public static final String POLICY_ID = "g2-m4-lifestyle-min-v1";
    public static final String WAR_POLICY_ID = "g2-lifestyle-wartime-stewardship-perk-v1";
    public static final String STEWARDSHIP = "stewardship_lifestyle";
    public static final String MARTIAL = "martial_lifestyle";
    public static final String DIPLOMACY = "diplomacy_lifestyle";
    public static final String WEALTH_FOCUS = "stewardship_wealth_focus";
    public static final String MARTIAL_FOCUS = "martial_authority_focus";
    public static final List<String> STEWARDSHIP_ORDER = List.of(
            "cutting_corners_perk", "professional_workforce_perk", "centralization_perk", "tax_man_perk",
            "defensive_measures_perk", "organized_muster_rolls_perk", "popular_figurehead_perk",
            "divided_attention_perk", "architect_perk", "golden_obligations_perk", "heregeld_perk",
            "detailed_ledgers_perk", "war_profiteer_perk", "fearful_troops_perk", "it_is_my_domain_perk",
            "golden_aplomb_perk", "at_any_cost_perk", "avaricious_perk", "meritocracy_perk",
            "chains_of_loyalty_perk", "likable_perk", "positions_of_power_perk", "large_levies_perk",
            "soon_forgiven_perk", "toe_the_line_perk", "honored_to_serve_perk", "administrator_perk");

    private LifestyleMinPolicy() { }

    /** Explicit JSON field state: missing and null never collapse into an empty collection or zero. */
    public enum FieldState { MISSING, NULL, PRESENT }
    public record Field<T>(FieldState state, T value) {
        public Field {
            Objects.requireNonNull(state, "state");
            StrictJson.require((state == FieldState.PRESENT) == (value != null), "field state/value mismatch");
        }
        public static <T> Field<T> missing() { return new Field<>(FieldState.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(FieldState.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(FieldState.PRESENT, Objects.requireNonNull(value)); }
        public boolean present() { return state == FieldState.PRESENT; }
        public boolean is(T other) { return present() && value.equals(other); }
    }
    public record Focus(Field<String> presence, Field<String> key, Field<String> lifestyleKey) {
        public Focus { Objects.requireNonNull(presence); Objects.requireNonNull(key); Objects.requireNonNull(lifestyleKey); }
    }
    public record Progress(Field<String> presence, Field<String> lifestyleKey, Field<BigInteger> unspentPoints) {
        public Progress { Objects.requireNonNull(presence); Objects.requireNonNull(lifestyleKey); Objects.requireNonNull(unspentPoints); }
    }
    public record Readiness(Field<Boolean> currentFocus, Field<Boolean> lifestyleProgress,
            Field<Boolean> ownedPerks, Field<Boolean> sameFrame, Field<Boolean> legalPerks, Field<Boolean> legalFocus) {
        public Readiness { Objects.requireNonNull(currentFocus); Objects.requireNonNull(lifestyleProgress);
            Objects.requireNonNull(ownedPerks); Objects.requireNonNull(sameFrame);
            Objects.requireNonNull(legalPerks); Objects.requireNonNull(legalFocus); }
    }
    public record Candidate(String key, String lifestyleKey) {
        public Candidate { Objects.requireNonNull(key); Objects.requireNonNull(lifestyleKey); }
    }
    public record Candidates(Field<String> status, Field<List<Candidate>> items) {
        public Candidates { Objects.requireNonNull(status); Objects.requireNonNull(items);
            if (items.present()) { items = Field.of(List.copyOf(items.value())); } }
    }
    public record Snapshot(Field<String> status, Field<String> snapshotId, Field<String> episodeRunId,
            Field<BigInteger> publicRevision, Field<BigInteger> nativeRevision, Field<BigInteger> proofEpoch,
            Field<BigInteger> dateRaw, Field<BigInteger> playerCharacterId, Field<Focus> currentFocus,
            Field<Progress> currentProgress, Field<Progress> targetProgress, Field<List<String>> ownedPerks,
            Field<Candidates> legalPerks, Field<Candidates> legalFocus, Field<Readiness> readiness) {
        public Snapshot { Objects.requireNonNull(status); Objects.requireNonNull(snapshotId); Objects.requireNonNull(episodeRunId);
            Objects.requireNonNull(publicRevision); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(proofEpoch);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(playerCharacterId); Objects.requireNonNull(currentFocus);
            Objects.requireNonNull(currentProgress); Objects.requireNonNull(targetProgress); Objects.requireNonNull(ownedPerks);
            Objects.requireNonNull(legalPerks); Objects.requireNonNull(legalFocus); Objects.requireNonNull(readiness);
            if (ownedPerks.present()) { ownedPerks = Field.of(List.copyOf(ownedPerks.value())); } }
    }
    public record PendingAction(Field<String> status) { public PendingAction { Objects.requireNonNull(status); } }
    public record Request(Field<Snapshot> snapshot, Field<Boolean> feudalScopeAdmitted, Field<Boolean> atPeace,
            Field<Boolean> collectTaxesActive, boolean allowWartimePerk, boolean allowWartimeInitialFocus,
            String preferredFocusTargetKey, Field<PendingAction> pendingAction, Field<Boolean> focusScopeAdmitted) {
        public Request { Objects.requireNonNull(snapshot); Objects.requireNonNull(feudalScopeAdmitted); Objects.requireNonNull(atPeace);
            Objects.requireNonNull(collectTaxesActive); Objects.requireNonNull(preferredFocusTargetKey);
            Objects.requireNonNull(pendingAction); Objects.requireNonNull(focusScopeAdmitted); }
    }
    public enum Status {
        SCOPE_OBSERVATION_UNAVAILABLE("scope_observation_unavailable"), OUTSIDE_ADMITTED_SCENE("outside_admitted_scene"),
        VERIFY_PENDING_RECEIPT("verify_pending_receipt"), CONSUME_APPLIED_RECEIPT("consume_applied_receipt"),
        ACTION_STATE_UNKNOWN("action_state_unknown"), OBSERVATION_UNAVAILABLE("observation_unavailable"),
        LEGAL_CANDIDATES_UNAVAILABLE("legal_candidates_unavailable"), NO_LEGAL_MINIMUM("no_legal_minimum"),
        TARGET_PROGRESS_SOURCE_UNAVAILABLE("target_progress_source_unavailable"),
        UNSUPPORTED_FOCUS_TARGET("unsupported_focus_target"), RECOMMEND_ACTION("recommend_action");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Kind { FOCUS, PERK }
    public record Binding(String snapshotId, String episodeRunId, BigInteger publicRevision,
            BigInteger nativeRevision, BigInteger proofEpoch, BigInteger dateRaw, BigInteger playerCharacterId) {
        public Binding { StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            StrictJson.require(publicRevision != null && nativeRevision != null && proofEpoch != null && playerCharacterId != null
                    && publicRevision.signum() > 0 && nativeRevision.signum() > 0 && proofEpoch.signum() > 0
                    && playerCharacterId.signum() >= 0 && dateRaw != null, "invalid LIFE expected frame"); }
    }
    public record Action(Kind kind, String targetKey, String targetLifestyleKey, Binding expected, String reason) {
        public Action { Objects.requireNonNull(kind); StrictJson.text(targetKey); StrictJson.text(targetLifestyleKey);
            Objects.requireNonNull(expected); StrictJson.text(reason); }
    }
    public record Decision(String policyId, Status status, Action selectedAction, String reason, BigInteger unspentPoints) {
        public Decision { StrictJson.text(policyId); Objects.requireNonNull(status);
            StrictJson.require((status == Status.RECOMMEND_ACTION) == (selectedAction != null), "decision/action mismatch");
            if (unspentPoints != null) { StrictJson.require(unspentPoints.signum() >= 0, "negative reported points"); } }
    }
    public record FocusProgress(BigInteger xpTotalRaw, BigInteger xpWithinLevelRaw, BigInteger xpPerLevel,
            BigInteger unspentPoints, BigInteger usedPoints) {
        public FocusProgress { Objects.requireNonNull(xpTotalRaw); Objects.requireNonNull(xpWithinLevelRaw);
            Objects.requireNonNull(xpPerLevel); Objects.requireNonNull(unspentPoints); Objects.requireNonNull(usedPoints); }
        public boolean valid() { return xpTotalRaw.signum() >= 0 && xpWithinLevelRaw.signum() >= 0 && xpPerLevel.signum() > 0
                && unspentPoints.signum() >= 0 && usedPoints.signum() >= 0
                && xpWithinLevelRaw.compareTo(xpPerLevel.multiply(BigInteger.valueOf(100_000))) < 0; }
    }
    public record FocusObservation(String status, Field<Boolean> nativeLegal, String targetKey,
            String targetLifestyleKey, String progressPresence, Field<FocusProgress> progress) {
        public FocusObservation { Objects.requireNonNull(status); Objects.requireNonNull(nativeLegal); Objects.requireNonNull(targetKey);
            Objects.requireNonNull(targetLifestyleKey); Objects.requireNonNull(progressPresence); Objects.requireNonNull(progress); }
    }
    public record Traits(Field<String> status, Field<List<String>> observedKeys) {
        public Traits { Objects.requireNonNull(status); Objects.requireNonNull(observedKeys);
            if (observedKeys.present()) { observedKeys = Field.of(List.copyOf(observedKeys.value())); } }
    }
    public record FirstFocusRequest(Field<FocusObservation> wealth, Field<FocusObservation> martial, Field<Traits> actorTraits,
            boolean atPeace) {
        public FirstFocusRequest { Objects.requireNonNull(wealth); Objects.requireNonNull(martial); Objects.requireNonNull(actorTraits); }
    }
    public record ObservedTarget(boolean nativeLegal, FocusProgress progress) { public ObservedTarget { Objects.requireNonNull(progress); } }
    public record FirstFocusDecision(boolean selected, String targetKey, String reason, int martialEducationRank,
            boolean atPeace, ObservedTarget wealth, ObservedTarget martial) {
        public FirstFocusDecision { StrictJson.require(selected == (targetKey != null), "focus decision/target mismatch");
            StrictJson.require(martialEducationRank >= 0 && martialEducationRank <= 5, "education rank outside observed range");
            StrictJson.require(selected == (reason != null), "focus decision/reason mismatch"); }
    }

    public sealed interface RoutedDecision permits MinimumDecision, AllLifestyleDecision { Status status(); }
    public record MinimumDecision(Decision decision) implements RoutedDecision {
        public MinimumDecision { Objects.requireNonNull(decision); }
        @Override public Status status() { return decision.status(); }
    }
    public record AllLifestyleDecision(String policyId, LifestylePerksModel.Decision decision) implements RoutedDecision {
        public AllLifestyleDecision { StrictJson.text(policyId); Objects.requireNonNull(decision); }
        @Override public Status status() {
            return switch (decision.status()) {
                case OBSERVATION_UNAVAILABLE -> Status.OBSERVATION_UNAVAILABLE;
                case LEGAL_CANDIDATES_UNAVAILABLE -> Status.LEGAL_CANDIDATES_UNAVAILABLE;
                case NO_LEGAL_MINIMUM -> Status.NO_LEGAL_MINIMUM;
                case RECOMMEND_ACTION -> Status.RECOMMEND_ACTION;
            };
        }
    }

    /** Exact original V3 dispatch order. Null V3 evidence is unavailable; absent V3 retains LIFE2. */
    public static RoutedDecision chooseRouted(Request input, Field<LifestylePerksModel.Input> allLifestyleInput) {
        Objects.requireNonNull(input); Objects.requireNonNull(allLifestyleInput);
        if (allLifestyleInput.state() == FieldState.MISSING) { return new MinimumDecision(choose(input)); }
        String policy = policy(input);
        Decision gate = preliminary(input, true, policy);
        if (gate != null) { return new MinimumDecision(gate); }
        if (!allLifestyleInput.present()) {
            return new AllLifestyleDecision(policy, new LifestylePerksModel.ObservationUnavailable(
                    LifestylePerksModel.Reason.PROGRESS_BINDING_INVALID, java.util.Optional.empty()));
        }
        Snapshot snapshot = input.snapshot().value();
        Binding expected = binding(snapshot);
        LifestylePerksModel.Input perk = allLifestyleInput.value();
        LifestylePerksModel.ExpectedBinding v3 = perk.binding();
        StrictJson.require(expected != null && expected.snapshotId().equals(v3.expectedSnapshotId())
                && expected.episodeRunId().equals(v3.expectedEpisodeRunId())
                && expected.publicRevision().equals(v3.expectedPublicRevision())
                && expected.nativeRevision().equals(v3.expectedNativeRevision())
                && expected.proofEpoch().equals(v3.expectedProofEpoch()) && expected.dateRaw().equals(v3.expectedDateRaw())
                && expected.playerCharacterId().equals(v3.expectedPlayerCharacterId())
                && snapshot.ownedPerks().value().equals(perk.owned()), "V3 delegate differs from minimum source frame or owned list");
        StrictJson.require(sameCandidates(snapshot.legalPerks(), perk.candidates()), "V3 delegate differs from minimum candidate projection");
        LifestylePerksModel.Decision chosen = AllLifestylePerkPolicyV3.choose(perk);
        if (chosen.status() != LifestylePerksModel.Status.NO_LEGAL_MINIMUM || !snapshot.currentFocus().present()
                || !snapshot.currentFocus().value().presence().is("absent")) { return new AllLifestyleDecision(policy, chosen); }
        return new MinimumDecision(chooseAfterPreliminary(input, policy));
    }

    public static Decision choose(Request input) {
        Objects.requireNonNull(input);
        String policy = policy(input);
        Decision gate = preliminary(input, false, policy);
        return gate != null ? gate : chooseAfterPreliminary(input, policy);
    }

    private static String policy(Request input) { return input.atPeace().is(false) && input.allowWartimePerk() ? WAR_POLICY_ID : POLICY_ID; }

    private static Decision preliminary(Request input, boolean allLifestyleV3, String policy) {
        if (!input.feudalScopeAdmitted().present() || !input.atPeace().present()) { return no(policy, Status.SCOPE_OBSERVATION_UNAVAILABLE); }
        if (!input.feudalScopeAdmitted().is(true) || (!input.atPeace().is(true) && !input.allowWartimePerk())) {
            return no(policy, Status.OUTSIDE_ADMITTED_SCENE);
        }
        if (input.pendingAction().present()) {
            Field<String> status = input.pendingAction().value().status();
            String pending = status.present() ? status.value() : "";
            if (pending.equals("submitted_verification_pending")) { return no(policy, Status.VERIFY_PENDING_RECEIPT); }
            if (pending.equals("applied")) { return no(policy, Status.CONSUME_APPLIED_RECEIPT); }
            if (!pending.equals("rejected_before_submit")) { return no(policy, Status.ACTION_STATE_UNKNOWN); }
        }
        if (!input.snapshot().present()) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        Snapshot snapshot = input.snapshot().value();
        if (!snapshot.status().is("available") || !snapshot.readiness().present()) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        Readiness ready = snapshot.readiness().value();
        if (!(ready.currentFocus().is(true) && (allLifestyleV3 ? ready.legalPerks().is(true) : ready.lifestyleProgress().is(true)) && ready.ownedPerks().is(true)
                && ready.sameFrame().is(true))) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        Binding binding = binding(snapshot);
        if (binding == null || !snapshot.ownedPerks().present()) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        return null;
    }

    private static Decision chooseAfterPreliminary(Request input, String policy) {
        Snapshot snapshot = input.snapshot().value();
        Readiness ready = snapshot.readiness().value();
        Binding binding = binding(snapshot);
        if (!snapshot.currentFocus().present() || !snapshot.currentProgress().present()) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        Focus focus = snapshot.currentFocus().value();
        Progress progress = snapshot.currentProgress().value();
        Set<String> owned = new HashSet<>(snapshot.ownedPerks().value());
        if (focus.presence().is("present")) {
            if (!ready.legalPerks().is(true)) { return no(policy, Status.LEGAL_CANDIDATES_UNAVAILABLE); }
            if (!nonempty(focus.key()) || !nonempty(focus.lifestyleKey()) || !progress.presence().is("present")
                    || !progress.lifestyleKey().is(focus.lifestyleKey().value())) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
            String lifestyle = focus.lifestyleKey().value();
            Set<String> legal = keys(snapshot.legalPerks(), lifestyle);
            if (legal == null) { return no(policy, Status.LEGAL_CANDIDATES_UNAVAILABLE); }
            if (lifestyle.equals(MARTIAL) && input.atPeace().is(false)) { policy = "g2-lifestyle-wartime-martial-perk-v1"; }
            if (lifestyle.equals(DIPLOMACY) && input.atPeace().is(false)) { policy = "g2-lifestyle-wartime-diplomacy-perk-v1"; }
            if (Set.of(STEWARDSHIP, MARTIAL, DIPLOMACY).contains(lifestyle)) {
                if (!nonnegative(progress.unspentPoints())) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
                if (progress.unspentPoints().value().signum() > 0) {
                    if (lifestyle.equals(MARTIAL) && eligible("serve_the_crown_perk", legal, owned)) {
                        return action(policy, Kind.PERK, "serve_the_crown_perk", lifestyle, binding, "feudal_county_control_growth_add_0_3");
                    }
                    if (lifestyle.equals(DIPLOMACY) && eligible("thoughtful_perk", legal, owned)) {
                        return action(policy, Kind.PERK, "thoughtful_perk", lifestyle, binding, "send_gift_opinion_gain_doubled");
                    }
                    if (lifestyle.equals(STEWARDSHIP)) {
                        if (eligible("cutting_corners_perk", legal, owned)) { return action(policy, Kind.PERK,
                                "cutting_corners_perk", lifestyle, binding, "feudal_build_cost_reduction_5_percent"); }
                        if (owned.contains("cutting_corners_perk") && eligible("professional_workforce_perk", legal, owned)) {
                            return action(policy, Kind.PERK, "professional_workforce_perk", lifestyle, binding,
                                    "feudal_build_speed_modifier_minus_30_percent"); }
                        if (owned.contains("professional_workforce_perk") && eligible("centralization_perk", legal, owned)) {
                            return action(policy, Kind.PERK, "centralization_perk", lifestyle, binding,
                                    "capital_county_monthly_development_growth_add_0_3"); }
                        if (input.collectTaxesActive().is(true) && owned.containsAll(STEWARDSHIP_ORDER.subList(0, 3))
                                && eligible("tax_man_perk", legal, owned)) {
                            return action(policy, Kind.PERK, "tax_man_perk", lifestyle, binding,
                                    "active_collect_taxes_effectiveness_plus_25_percent"); }
                    }
                }
            }
            if (!lifestyle.equals(STEWARDSHIP)) { return no(policy, Status.NO_LEGAL_MINIMUM); }
            BigInteger points = progress.unspentPoints().value();
            if (points.signum() == 0) { return no(policy, Status.NO_LEGAL_MINIMUM, "no_unspent_points", BigInteger.ZERO); }
            if (!new HashSet<>(STEWARDSHIP_ORDER).containsAll(legal)) {
                return no(policy, Status.OBSERVATION_UNAVAILABLE, "outside_authored_stewardship_frontier", null); }
            for (String key : STEWARDSHIP_ORDER) {
                if (eligible(key, legal, owned)) { return action(policy, Kind.PERK, key, lifestyle, binding, "remaining_native_final_legal_perk"); }
            }
            if (!legal.isEmpty()) { return no(policy, Status.OBSERVATION_UNAVAILABLE, "native_final_legal_candidate_already_owned", null); }
            return no(policy, Status.NO_LEGAL_MINIMUM, "no_native_final_legal_candidate", points);
        }
        if (!input.atPeace().is(true) && !input.allowWartimeInitialFocus()) { return no(policy, Status.OUTSIDE_ADMITTED_SCENE); }
        if (input.focusScopeAdmitted().is(false)) {
            return no(policy, Status.OUTSIDE_ADMITTED_SCENE, "initial_focus_remains_feudal_scoped", null); }
        if (!focus.presence().is("absent") || !progress.presence().is("absent")) { return no(policy, Status.OBSERVATION_UNAVAILABLE); }
        if (!ready.legalFocus().is(true)) { return no(policy, Status.LEGAL_CANDIDATES_UNAVAILABLE); }
        String lifestyle = input.preferredFocusTargetKey().equals(WEALTH_FOCUS) ? STEWARDSHIP
                : input.preferredFocusTargetKey().equals(MARTIAL_FOCUS) ? MARTIAL : null;
        if (lifestyle == null) { return no(policy, Status.UNSUPPORTED_FOCUS_TARGET); }
        Set<String> legal = keys(snapshot.legalFocus(), lifestyle);
        if (legal == null) { return no(policy, Status.LEGAL_CANDIDATES_UNAVAILABLE); }
        if (!legal.contains(input.preferredFocusTargetKey())) { return no(policy, Status.NO_LEGAL_MINIMUM); }
        if (!snapshot.targetProgress().present()) { return no(policy, Status.TARGET_PROGRESS_SOURCE_UNAVAILABLE); }
        Progress target = snapshot.targetProgress().value();
        if (!target.presence().is("present") || !target.lifestyleKey().is(lifestyle) || !nonnegative(target.unspentPoints())) {
            return no(policy, Status.TARGET_PROGRESS_SOURCE_UNAVAILABLE); }
        return action(policy, Kind.FOCUS, input.preferredFocusTargetKey(), lifestyle, binding,
                lifestyle.equals(MARTIAL) ? "first_focus_martial_control_and_war_role" : "feudal_monthly_income_modifier_10_percent");
    }

    public static FirstFocusDecision chooseFirstFocus(FirstFocusRequest input) {
        Objects.requireNonNull(input);
        ObservedTarget wealth = target(input.wealth(), WEALTH_FOCUS, STEWARDSHIP);
        ObservedTarget martial = target(input.martial(), MARTIAL_FOCUS, MARTIAL);
        int rank = 0;
        if (input.actorTraits().present()) {
            Traits traits = input.actorTraits().value();
            if (traits.status().is("available") && traits.observedKeys().present()) {
                for (int candidate = 1; candidate <= 5; candidate++) {
                    if (traits.observedKeys().value().contains("education_martial_" + candidate)) { rank = candidate; }
                }
            }
        }
        boolean role = rank >= (input.atPeace() ? 4 : 3);
        boolean wealthDue = wealth != null && martial != null && wealth.progress().unspentPoints().signum() > 0
                && martial.progress().unspentPoints().signum() == 0;
        boolean educatedPoint = rank > 0 && wealth != null && martial != null && martial.progress().unspentPoints().signum() > 0
                && wealth.progress().unspentPoints().signum() == 0;
        boolean onlyMartial = wealth != null && !wealth.nativeLegal();
        if (wealth != null && martial != null && martial.nativeLegal()
                && (onlyMartial || ((role || educatedPoint) && (!input.atPeace() || !wealthDue)))) {
            String reason = onlyMartial ? "only_observed_final_legal_focus"
                    : educatedPoint && !role ? "martial_education_with_observed_martial_point"
                    : !input.atPeace() ? "martial_education_and_war_objective"
                    : "high_martial_education_without_ready_wealth_point";
            return new FirstFocusDecision(true, MARTIAL_FOCUS, reason, rank, input.atPeace(), wealth, martial);
        }
        if (wealth != null && wealth.nativeLegal()) {
            return new FirstFocusDecision(true, WEALTH_FOCUS, wealthDue && input.atPeace() ? "ready_wealth_point_in_peace"
                    : "existing_income_baseline", rank, input.atPeace(), wealth, martial);
        }
        return new FirstFocusDecision(false, null, null, rank, input.atPeace(), wealth, martial);
    }

    private static ObservedTarget target(Field<FocusObservation> source, String key, String lifestyle) {
        if (!source.present()) { return null; }
        FocusObservation row = source.value();
        if (!row.status().equals("observed") || !row.nativeLegal().present() || !row.targetKey().equals(key)
                || !row.targetLifestyleKey().equals(lifestyle) || !row.progressPresence().equals("present")
                || !row.progress().present() || !row.progress().value().valid()) { return null; }
        return new ObservedTarget(row.nativeLegal().value(), row.progress().value());
    }
    private static boolean nonempty(Field<String> value) { return value.present() && !value.value().isEmpty(); }
    private static boolean sameCandidates(Field<Candidates> minimum, LifestylePerksModel.CandidateObservation all) {
        if (!minimum.present() || !minimum.value().status().present()) { return false; }
        Candidates source = minimum.value();
        if (all instanceof LifestylePerksModel.UnavailableCandidates unavailable) { return source.status().is(unavailable.sourceStatus()); }
        LifestylePerksModel.LegalCandidates legal = (LifestylePerksModel.LegalCandidates) all;
        if (!source.status().is("available") || !source.items().present() || source.items().value().size() != legal.items().size()) { return false; }
        for (int index = 0; index < legal.items().size(); index++) {
            Candidate left = source.items().value().get(index); LifestylePerksModel.Candidate right = legal.items().get(index);
            if (!left.key().equals(right.key()) || !left.lifestyleKey().equals(right.lifestyleKey())) { return false; }
        }
        return true;
    }
    private static boolean nonnegative(Field<BigInteger> value) { return value.present() && value.value().signum() >= 0; }
    private static boolean eligible(String key, Set<String> legal, Set<String> owned) { return legal.contains(key) && !owned.contains(key); }
    private static Set<String> keys(Field<Candidates> field, String lifestyle) {
        if (!field.present()) { return null; }
        Candidates candidates = field.value();
        if (!candidates.status().is("available") || !candidates.items().present()) { return null; }
        Set<String> keys = new HashSet<>();
        for (Candidate row : candidates.items().value()) {
            if (row.key().isEmpty()) { return null; }
            if (row.lifestyleKey().equals(lifestyle)) { keys.add(row.key()); }
        }
        return keys;
    }
    private static Binding binding(Snapshot s) {
        if (!nonempty(s.snapshotId()) || !nonempty(s.episodeRunId()) || !s.dateRaw().present()
                || !nonnegative(s.playerCharacterId()) || !positive(s.publicRevision()) || !positive(s.nativeRevision())
                || !positive(s.proofEpoch())) { return null; }
        return new Binding(s.snapshotId().value(), s.episodeRunId().value(), s.publicRevision().value(), s.nativeRevision().value(),
                s.proofEpoch().value(), s.dateRaw().value(), s.playerCharacterId().value());
    }
    private static boolean positive(Field<BigInteger> value) { return value.present() && value.value().signum() > 0; }
    private static Decision no(String policy, Status status) { return no(policy, status, null, null); }
    private static Decision no(String policy, Status status, String reason, BigInteger points) { return new Decision(policy, status, null, reason, points); }
    private static Decision action(String policy, Kind kind, String target, String lifestyle, Binding binding, String reason) {
        return new Decision(policy, Status.RECOMMEND_ACTION, new Action(kind, target, lifestyle, binding, reason), null, null);
    }
}
