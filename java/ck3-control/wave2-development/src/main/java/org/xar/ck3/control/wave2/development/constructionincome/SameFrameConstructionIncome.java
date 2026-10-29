package org.xar.ck3.control.wave2.development.constructionincome;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;

/** The existing latest same-native-frame public-root scalar observer; no finance calculation. */
public final class SameFrameConstructionIncome {
    public static final String ROOT_QUERY_STEP = "query-campaign-root-context-v1";
    public static final BigInteger INCOME_SCALE = BigInteger.valueOf(100_000);
    private SameFrameConstructionIncome() { }

    public record Frame(BigInteger nativeRevision, BigInteger dateRaw, BigInteger actorCharacterId) { }
    public record Income(BigInteger raw, BigInteger scale) { }
    public record RootContext(String status, Frame frame, Income income) {
        public RootContext { Objects.requireNonNull(frame); }
    }
    public record HistoryRow(String command, Evidence ok, RootContext rootContext) {
        public HistoryRow { Objects.requireNonNull(ok); }
    }
    public enum RootObservation { NOT_OBSERVED, OBSERVED }
    public record Observation(RootObservation rootObservation, BigInteger incomeRaw) {
        public Observation {
            Objects.requireNonNull(rootObservation);
            if (rootObservation == RootObservation.NOT_OBSERVED && incomeRaw != null) {
                throw new IllegalArgumentException("an absent public root has no observed income");
            }
        }
    }

    public static Observation observe(Frame snapshot, List<HistoryRow> history) {
        Objects.requireNonNull(snapshot);
        Objects.requireNonNull(history);
        for (int index = history.size() - 1; index >= 0; index--) {
            HistoryRow row = Objects.requireNonNull(history.get(index));
            if (!ROOT_QUERY_STEP.equals(row.command()) || row.ok() != Evidence.TRUE) { continue; }
            RootContext root = row.rootContext();
            if (root == null || !"available".equals(root.status()) || !root.frame().equals(snapshot)) { continue; }
            Income income = root.income();
            return new Observation(RootObservation.OBSERVED,
                    income != null && INCOME_SCALE.equals(income.scale()) ? income.raw() : null);
        }
        return new Observation(RootObservation.NOT_OBSERVED, null);
    }
}
