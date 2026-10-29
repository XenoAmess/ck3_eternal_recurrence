package org.xar.ck3.control.governance.lifestyleperks;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.governance.lifestyleperks.LifestylePerksModel.*;

/** Exact pure decision leaf: authorizes only the native single final-legal candidate. */
public final class AllLifestylePerkPolicyV3 {
    private AllLifestylePerkPolicyV3() { }

    public static Decision choose(Input input) {
        ProgressObservation observed = input.progress();
        if (!observed.frame().equals(input.snapshotFrame()) || observed.rows().size() != Lifestyle.values().length) {
            return unavailable(Reason.PROGRESS_BINDING_INVALID);
        }
        EnumMap<Lifestyle, ProgressRow> progress = new EnumMap<>(Lifestyle.class);
        List<Lifestyle> unavailable = new ArrayList<>();
        for (ProgressRow row : observed.rows()) {
            if (progress.putIfAbsent(row.lifestyle(), row) != null) { return unavailable(Reason.PROGRESS_BINDING_INVALID); }
            if (row instanceof UnavailableProgress) { unavailable.add(row.lifestyle()); }
        }
        boolean incomplete = !unavailable.isEmpty();
        if (progress.size() != Lifestyle.values().length || incomplete == (observed.completeness() == Completeness.COMPLETE)) {
            return unavailable(Reason.PROGRESS_BINDING_INVALID);
        }
        if (!(input.candidates() instanceof LegalCandidates candidates) || !candidates.scope().equals("policy_target")) {
            return new CandidatesUnavailable(Optional.empty());
        }
        if (candidates.items().size() > 1) { return new CandidatesUnavailable(Optional.of(Reason.TARGET_CARDINALITY_INVALID)); }
        if (candidates.items().isEmpty()) {
            if (incomplete) {
                unavailable.sort(java.util.Comparator.comparing(Lifestyle::wire));
                return new ObservationUnavailable(Reason.PARTIAL_NO_TARGET, Optional.of(unavailable));
            }
            EnumMap<Lifestyle, BigInteger> positive = new EnumMap<>(Lifestyle.class);
            for (ProgressRow row : observed.rows()) {
                if (row instanceof AvailableProgress available && available.unspentPerkPoints().signum() > 0) {
                    positive.put(row.lifestyle(), available.unspentPerkPoints());
                }
            }
            return new NoLegalMinimum(positive.isEmpty() ? Reason.NO_UNSPENT_POINTS : Reason.FINAL_LEGAL_NONE_WITH_POINTS, positive);
        }
        Candidate target = candidates.items().getFirst();
        Lifestyle lifestyle = AuthoredPerkCatalog.perks().get(target.key());
        if (lifestyle == null || !lifestyle.wire().equals(target.lifestyleKey())) { return unavailable(Reason.TARGET_OUTSIDE_AUTHORED); }
        ProgressRow row = progress.get(lifestyle);
        if (!(row instanceof AvailableProgress available) || available.unspentPerkPoints().signum() <= 0) {
            return unavailable(Reason.TARGET_NOT_POSITIVE);
        }
        if (input.owned().contains(target.key())) { return unavailable(Reason.TARGET_ALREADY_OWNED); }
        return new Recommendation(new Action(target.key(), lifestyle, input.binding()),
                incomplete ? Completeness.PARTIAL : Completeness.COMPLETE, available.unspentPerkPoints());
    }

    private static ObservationUnavailable unavailable(Reason reason) {
        return new ObservationUnavailable(reason, Optional.empty());
    }
}
