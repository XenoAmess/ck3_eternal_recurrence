package org.xar.ck3.control.wave3.planning.realmmembership;

import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedSummaryCodec;

/** One typed application used by the shared host and existing consumer adapters; no independent transport. */
public final class RealmFeedbackApplication {
    private RealmFeedbackApplication() { }
    public static RealmMembershipFeedback.Result feedback(RealmMembershipFeedback.Request request) {
        return RealmMembershipFeedback.projectRequest(request);
    }
    public static RealmDifference difference(RealmDifferenceCodec.Request request) {
        return RealmDifferenceCodec.projectRequest(request);
    }
    public static DatedRealmSummary.Result datedSummary(DatedSummaryCodec.Request request) {
        return DatedSummaryCodec.projectRequest(request);
    }
}

