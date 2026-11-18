package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RawRankedRulerCandidates1210;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RawRankedRulerCandidates1210.Partial;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RawRankedRulerCandidates1210.Unavailable;

/** Actual raw Family query DATA alongside independent manager membership; never a joined legality/chooser source.
 * Original query bytes, native ranking order and signed native score remain separate from manager lifecycle bits.
 */
public final class FamilyRosterData1210 {
    private FamilyRosterData1210() { }
    public enum UnjoinedReason {
        FAMILY_QUERY_UNAVAILABLE, MANAGER_DATA_UNAVAILABLE, MANAGER_OWNER_NOT_OBSERVED,
        REPORTED_OWNER_OR_FRAME_MISMATCH, TRANSPORT_INSTANCE_AND_MODEL_SOURCE_NOT_OBSERVED
    }
    public record Audit(RawJson originalFamily, RawRankedRulerCandidates1210.Request originalRequest,
            RawRankedRulerCandidates1210.Result familyData, CharacterRosterRead1210.ScopedRoster separateManagerData,
            UnjoinedReason reason, Optional<String> originalFamilyReason) {
        public Audit {
            Objects.requireNonNull(originalFamily); Objects.requireNonNull(originalRequest); Objects.requireNonNull(familyData);
            Objects.requireNonNull(separateManagerData); Objects.requireNonNull(reason);
            originalFamilyReason = Objects.requireNonNull(originalFamilyReason);
        }
        public boolean sameOwnerFamilyJoinAvailable() { return false; }
        public boolean transportInstanceObserved() { return false; }
        public boolean allLivingComplete() { return false; }
        public boolean interactionCandidatesComplete() { return false; }
    }
    /** Membership is an independent archived dataset annotation, not an eligibility filter or source-proof substitute. */
    public static Audit audit(CharacterRosterRead1210.Capture manager, RawJson originalFamily,
            RawRankedRulerCandidates1210.Request actualRequest) {
        Objects.requireNonNull(manager);
        var family = RawRankedRulerCandidates1210.decode(Objects.requireNonNull(originalFamily), Objects.requireNonNull(actualRequest));
        var ids = family instanceof Partial partial ? partial.sample().rows().stream().map(row -> row.candidate()).toList()
                : List.<org.xar.ck3.control.contracts.NativeCharacterId>of();
        var separate = manager.lookup(manager.manager().observation().frame(), ids);
        if (family instanceof Unavailable unavailable)
            return new Audit(originalFamily, actualRequest, family, separate, UnjoinedReason.FAMILY_QUERY_UNAVAILABLE,
                    Optional.of(unavailable.reason()));
        UnjoinedReason reason;
        if (!manager.manager().observation().available()) reason = UnjoinedReason.MANAGER_DATA_UNAVAILABLE;
        else if (!manager.applicationMainObserved() || manager.sourceProof().isEmpty()) reason = UnjoinedReason.MANAGER_OWNER_NOT_OBSERVED;
        else {
            var proof = manager.sourceProof().orElseThrow(); var frame = ((Partial) family).frame();
            var prefix = manager.manager().observation().frame();
            boolean sameReportedFields = proof.nativeRevision().toString().equals(frame.nativeRevision().decimal())
                    && proof.connectionGeneration().toString().equals(frame.connectionGeneration().decimal())
                    && proof.pumpEpoch().toString().equals(frame.pumpEpoch().decimal())
                    && proof.ownerThreadId() == frame.ownerThreadId() && proof.dateRaw() == frame.dateRaw()
                    && proof.actor().equals(frame.actor()) && proof.actor().equals(frame.subject())
                    && prefix.localPlayerId() == frame.localPlayerId();
            reason = sameReportedFields ? UnjoinedReason.TRANSPORT_INSTANCE_AND_MODEL_SOURCE_NOT_OBSERVED : UnjoinedReason.REPORTED_OWNER_OR_FRAME_MISMATCH;
        }
        return new Audit(originalFamily, actualRequest, family, separate, reason, Optional.empty());
    }
}
