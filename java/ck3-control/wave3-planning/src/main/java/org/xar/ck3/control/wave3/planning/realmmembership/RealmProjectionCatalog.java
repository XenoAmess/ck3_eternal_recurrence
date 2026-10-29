package org.xar.ck3.control.wave3.planning.realmmembership;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference;
import org.xar.ck3.control.wave2.planning.realmcompare.RealmDifferenceCodec;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedRealmSummary;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedSummaryCodec;

/** Standard service provider in the existing wave3-planning artifact, not a service or JVM per leaf. */
public final class RealmProjectionCatalog implements ProjectionPortCatalog {
    public RealmProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new FeedbackPort()),
                RegisteredProjection.of(new DifferencePort()), RegisteredProjection.of(new SummaryPort()));
    }
    private static final class FeedbackPort implements ProjectionPort<RealmMembershipFeedback.Request, RealmMembershipFeedback.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.REALM_MEMBERSHIP_FEEDBACK; }
        @Override public int inputMaximumBytes() { return RealmMembershipFeedback.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return RealmMembershipFeedback.MAX_BYTES; }
        @Override public RealmMembershipFeedback.Request decode(byte[] input) { return RealmMembershipFeedback.decodeRequest(input); }
        @Override public RealmMembershipFeedback.Result project(RealmMembershipFeedback.Request input) { return RealmFeedbackApplication.feedback(input); }
        @Override public byte[] encode(RealmMembershipFeedback.Result output) { return output.wireJson(); }
    }
    private static final class DifferencePort implements ProjectionPort<RealmDifferenceCodec.Request, RealmDifference> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.REALM_DIFFERENCE; }
        @Override public int inputMaximumBytes() { return RealmDifferenceCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return RealmDifferenceCodec.MAX_BYTES; }
        @Override public RealmDifferenceCodec.Request decode(byte[] input) { return RealmDifferenceCodec.decodeRequest(input); }
        @Override public RealmDifference project(RealmDifferenceCodec.Request input) { return RealmFeedbackApplication.difference(input); }
        @Override public byte[] encode(RealmDifference output) { return RealmDifferenceCodec.encode(output); }
    }
    private static final class SummaryPort implements ProjectionPort<DatedSummaryCodec.Request, DatedRealmSummary.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.REALM_DATED_SUMMARY; }
        @Override public int inputMaximumBytes() { return RealmDifferenceCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return RealmDifferenceCodec.MAX_BYTES; }
        @Override public DatedSummaryCodec.Request decode(byte[] input) { return DatedSummaryCodec.decodeRequest(input); }
        @Override public DatedRealmSummary.Result project(DatedSummaryCodec.Request input) { return RealmFeedbackApplication.datedSummary(input); }
        @Override public byte[] encode(DatedRealmSummary.Result output) { return DatedSummaryCodec.encode(output); }
    }
}

