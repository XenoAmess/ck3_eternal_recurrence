package org.xar.ck3.control.wave2.planning.scoretarget;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedCountyMembership;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipInput;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;

/** Existing saved-score domains in the one host; request and result caps remain 64 KiB. */
public final class SavedScoreProjectionPortCatalog implements ProjectionPortCatalog {
    public SavedScoreProjectionPortCatalog() { }

    @Override public List<RegisteredProjection> registrations() {
        return List.of(
                RegisteredProjection.of(new ProjectionPort<SavedWarScan, RebellionMetricDelta>() {
                    @Override public ProjectionOperation operation() { return ProjectionOperation.SCORE_REBELLION_PROJECT; }
                    @Override public int inputMaximumBytes() { return 65536; }
                    @Override public int outputMaximumBytes() { return 65536; }
                    @Override public SavedWarScan decode(byte[] raw) { return RebellionMetricCodec.decode(raw); }
                    @Override public RebellionMetricDelta project(SavedWarScan input) { return RebellionMetricAdapter.project(input); }
                    @Override public byte[] encode(RebellionMetricDelta result) { return RebellionMetricCodec.encode(result); }
                }),
                RegisteredProjection.of(new ProjectionPort<SavedMembershipInput, SavedMembershipResult>() {
                    @Override public ProjectionOperation operation() { return ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT; }
                    @Override public int inputMaximumBytes() { return 65536; }
                    @Override public int outputMaximumBytes() { return 65536; }
                    @Override public SavedMembershipInput decode(byte[] raw) { return SavedMembershipCodec.decode(raw); }
                    @Override public SavedMembershipResult project(SavedMembershipInput input) { return SavedCountyMembership.audit(input); }
                    @Override public byte[] encode(SavedMembershipResult result) { return SavedMembershipCodec.encode(result); }
                }));
    }
}
