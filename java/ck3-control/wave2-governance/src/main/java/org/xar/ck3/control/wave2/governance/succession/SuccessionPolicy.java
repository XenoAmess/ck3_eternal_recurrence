package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.function.Predicate;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Pure retained-estate and actual post-transition comparison; never queries or commits. */
public final class SuccessionPolicy {
    private SuccessionPolicy() { }
    public static Expectation freeze(TurnBundle bundle, String episodeRunId, int episodeCharacterId) {
        domainCheck(bundle.ruler().characterId() == episodeCharacterId && bundle.ruler().alive(), "bundle ruler does not bind living episode");
        Integer successor = bundle.primaryHeirCharacterId();
        return new Expectation(new Binding(bundle.frame(), episodeRunId, episodeCharacterId),
                successor == null ? ExpectationState.NO_PRIMARY_HEIR : ExpectationState.SUCCESSOR_EXPECTED,
                episodeCharacterId, successor, bundle.titleRows(), bundle.riskState());
    }
    public static Reconciliation reconcile(Expectation before, Snapshot post, TurnBundle bundle) {
        domainCheck(post != null && Objects.equals(post.episodeCharacterId(), before.predecessorCharacterId())
                && "played_character_changed".equals(post.terminalReason()) && Boolean.TRUE.equals(post.terminal())
                && Boolean.TRUE.equals(post.paused()), "post snapshot is not paused succession transition");
        Actor actor = post.actor(); domainCheck(actor != null && actor.alive() && actor.characterId() != before.predecessorCharacterId(), "living changed successor required");
        domainCheck(bundle.frame().equals(post.frame()), "post snapshot and turn bundle frame disagree");
        domainCheck(bundle.frame().dateRaw() >= before.binding().frame().dateRaw(), "post date precedes expectation");
        domainCheck(bundle.ruler().alive() && bundle.ruler().characterId() == actor.characterId(), "post ruler disagrees with successor");
        List<Integer> inherited = ids(before.titleExpectations(), row -> row.firstHeirCharacterId() != null && Objects.equals(row.firstHeirCharacterId(), before.expectedSuccessorCharacterId()));
        List<Integer> elsewhere = ids(before.titleExpectations(), row -> row.firstHeirCharacterId() != null && !Objects.equals(row.firstHeirCharacterId(), before.expectedSuccessorCharacterId()));
        List<Integer> without = ids(before.titleExpectations(), row -> row.firstHeirCharacterId() == null);
        List<Integer> observed = ids(bundle.titleRows(), row -> true);
        List<Integer> allBefore = ids(before.titleExpectations(), row -> true);
        List<Integer> matched = sorted(inherited.stream().filter(observed::contains).toList());
        List<Integer> missing = sorted(inherited.stream().filter(id -> !observed.contains(id)).toList());
        List<Integer> unexpected = sorted(observed.stream().filter(id -> elsewhere.contains(id) || without.contains(id)).toList());
        boolean successorMatch = Objects.equals(actor.characterId(), before.expectedSuccessorCharacterId());
        boolean distributionMatch = missing.isEmpty() && unexpected.isEmpty();
        Verdict verdict = !successorMatch ? Verdict.UNEXPECTED_SUCCESSOR : distributionMatch ? Verdict.MATCHED : Verdict.TITLE_DISTRIBUTION_MISMATCH;
        return new Reconciliation(before.binding(), bundle.frame(), before.predecessorCharacterId(), before.expectedSuccessorCharacterId(), actor.characterId(), successorMatch,
                sorted(inherited), matched, missing, unexpected, sorted(elsewhere), sorted(without), sorted(observed.stream().filter(id -> !allBefore.contains(id)).toList()), distributionMatch, verdict);
    }
    public static OperatingResult operating(Snapshot snapshot, Expectation current, Expectation previous, boolean previousSupplied) {
        if (snapshot == null) { return new UnavailableOperating(false, "current_snapshot_unavailable"); }
        if (snapshot.activeEvent() || snapshot.pendingInteraction()) { return new UnavailableOperating(true, "resolve_original_player_decision_before_operating_review"); }
        Actor actor = snapshot.actor();
        if (!Boolean.TRUE.equals(snapshot.paused()) || !Boolean.TRUE.equals(snapshot.mapReady()) || !Boolean.FALSE.equals(snapshot.terminal())
                || snapshot.terminalReason() != null || actor == null || !actor.alive() || !Objects.equals(actor.characterId(), snapshot.episodeCharacterId())) {
            return new UnavailableOperating(false, "current_living_paused_episode_unavailable");
        }
        if (snapshot.lifecycle() != Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION) { return new UnavailableOperating(false, "ordinary_campaign_lifecycle_unavailable"); }
        if (current == null) { return new UnavailableOperating(false, "complete_retained_title_expectation_unavailable"); }
        Binding binding = current.binding();
        if (!binding.frame().equals(snapshot.frame()) || !binding.episodeRunId().equals(snapshot.episodeRunId()) || !Objects.equals(binding.episodeCharacterId(), snapshot.episodeCharacterId())) {
            return new UnavailableOperating(false, "retained_estate_requires_original_same_frame_refresh");
        }
        if (current.predecessorCharacterId() != actor.characterId()) { return new UnavailableOperating(false, "retained_estate_belongs_to_another_actor"); }
        Integer heir = current.expectedSuccessorCharacterId(); List<TitleRow> rows = current.titleExpectations();
        List<Integer> primaryTitles = ids(rows, row -> heir != null && Objects.equals(row.firstHeirCharacterId(), heir));
        List<Integer> other = ids(rows, row -> row.firstHeirCharacterId() != null && !Objects.equals(row.firstHeirCharacterId(), heir));
        List<Integer> without = ids(rows, row -> row.firstHeirCharacterId() == null);
        var tier = current.primary().title().integerTier();
        List<Integer> equalOrHigher = ids(rows, row -> other.contains(row.title().titleId()) && tier != null && row.title().integerTier() != null && row.title().integerTier().compareTo(tier) >= 0);
        List<Integer> unknown = ids(rows, row -> other.contains(row.title().titleId()) && (tier == null || row.title().integerTier() == null));
        List<Issue> issues = new ArrayList<>();
        if (heir == null) { issues.add(new Issue(IssueKind.NO_OBSERVED_PRIMARY_TITLE_HEIR, List.of(current.primary().title().titleId()))); }
        if (!other.isEmpty()) { issues.add(new Issue(IssueKind.PERSONAL_ESTATE_SPLIT_BETWEEN_OBSERVED_HEIRS, other)); }
        if (!equalOrHigher.isEmpty()) { issues.add(new Issue(IssueKind.OTHER_HEIR_RECEIVES_EQUAL_OR_HIGHER_RANK_TITLE, equalOrHigher)); }
        if (!without.isEmpty()) { issues.add(new Issue(IssueKind.HELD_TITLES_WITHOUT_OBSERVED_HEIR, without)); }
        Changes changes = null; String priorReason = previousSupplied ? "previous_projection_not_comparable_to_current_episode" : "previous_complete_projection_not_supplied";
        if (previous != null && previous.binding().episodeRunId().equals(binding.episodeRunId()) && previous.predecessorCharacterId() == current.predecessorCharacterId()
                && previous.binding().frame().dateRaw() <= binding.frame().dateRaw()
                && previous.binding().frame().revision().compareTo(binding.frame().revision()) <= 0
                && previous.binding().frame().nativeRevision().compareTo(binding.frame().nativeRevision()) <= 0) {
            List<Integer> oldIds = ids(previous.titleExpectations(), row -> true), newIds = ids(rows, row -> true);
            List<Integer> changed = new ArrayList<>();
            for (TitleRow row : rows) {
                previous.titleExpectations().stream().filter(old -> old.title().titleId() == row.title().titleId()).findFirst()
                        .filter(old -> !Objects.equals(old.firstHeirCharacterId(), row.firstHeirCharacterId())).ifPresent(old -> changed.add(row.title().titleId()));
            }
            changes = new Changes(previous.binding(), sorted(newIds.stream().filter(id -> !oldIds.contains(id)).toList()), sorted(oldIds.stream().filter(id -> !newIds.contains(id)).toList()), sorted(changed),
                    previous.primary().title().titleId() != current.primary().title().titleId(), !Objects.equals(previous.expectedSuccessorCharacterId(), heir)); priorReason = null;
        }
        return new AvailableOperating(binding, new Estate(current.primary().title().titleId(), heir, current.riskState(), rows, primaryTitles, other, without, equalOrHigher, unknown), issues, changes, priorReason);
    }
    private static void domainCheck(boolean admitted, String reason) {
        if (!admitted) { throw new ProjectionDomainRejection(reason); }
    }
    private static List<Integer> ids(List<TitleRow> rows, Predicate<TitleRow> filter) { return rows.stream().filter(filter).map(row -> row.title().titleId()).toList(); }
    private static List<Integer> sorted(List<Integer> ids) { return ids.stream().sorted().toList(); }
}
