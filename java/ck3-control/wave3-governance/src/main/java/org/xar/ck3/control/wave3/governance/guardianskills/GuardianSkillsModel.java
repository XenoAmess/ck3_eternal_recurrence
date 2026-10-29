package org.xar.ck3.control.wave3.governance.guardianskills;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusManagement;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.GuardianProfile;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.SkillObservation;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.SourceBasis;

/** Typed observed request-role facts; no effect educator, native AI or action authority. */
public final class GuardianSkillsModel {
    private GuardianSkillsModel() { }
    public record FamilyFrame(BigInteger nativeRevision, Long playedCharacterId, Long heirCharacterId, Long dateRaw) {
        public FamilyFrame {
            if (nativeRevision != null) { revision(nativeRevision); }
            if (playedCharacterId != null) { characterId(playedCharacterId); }
            if (heirCharacterId != null) { characterId(heirCharacterId); }
        }
    }
    public record QueryFrame(BigInteger nativeRevision, long dateRaw, long playerCharacterId) {
        public QueryFrame {
            revision(nativeRevision); StrictJson.require(dateRaw >= Integer.MIN_VALUE && dateRaw <= Integer.MAX_VALUE, "ordinary native signed date range");
            StrictJson.require(playerCharacterId >= 1 && playerCharacterId <= Integer.MAX_VALUE, "ordinary played-character range");
        }
    }
    public record Context(String exactBuild, String interactionKey, String status, QueryFrame frame,
            Long secondaryActorId, Long secondaryRecipientId) {
        public Context {
            StrictJson.text(exactBuild); StrictJson.text(interactionKey); StrictJson.text(status); Objects.requireNonNull(frame);
            if (secondaryActorId != null) { characterId(secondaryActorId); }
            if (secondaryRecipientId != null) { characterId(secondaryRecipientId); }
        }
    }
    public record FocusSubject(long childFullId, FocusManagement focusManagement, Optional<FamilyFrame> familyFrame) {
        public FocusSubject {
            StrictJson.require(childFullId >= 0 && childFullId <= 4_294_967_294L, "native child full-ID range");
            Objects.requireNonNull(focusManagement); Objects.requireNonNull(familyFrame);
        }
    }
    public record Input(FocusSubject needs, Optional<GuardianProfile> profile, Optional<Context> context) {
        public Input { Objects.requireNonNull(needs); Objects.requireNonNull(profile); Objects.requireNonNull(context); }
    }
    public enum Join {
        JOINED(null), PROFILE_NOT_OBSERVED("request_guardian_skill_profile_not_observed"),
        CHILD_MISMATCH("request_guardian_skill_child_mismatch"), FRAME_NOT_OBSERVED("family_education_focus_frame_not_observed"),
        FRAME_MISMATCH("family_education_focus_frame_mismatch");
        private final String reason;
        Join(String reason) { this.reason = reason; }
        public String reason() { return reason; }
        public boolean available() { return this == JOINED; }
    }
    public record Projection(FocusSubject needs, Optional<GuardianProfile> profile, Join join,
            SkillObservation focusSkill, SkillObservation learningSkill) {
        public Projection { Objects.requireNonNull(needs); Objects.requireNonNull(profile); Objects.requireNonNull(join); Objects.requireNonNull(focusSkill); Objects.requireNonNull(learningSkill); }
        public SourceBasis focusSourceBasis() { return SourceBasis.RAW; }
        public SourceBasis learningSourceBasis() { return SourceBasis.RAW; }
    }
    private static void characterId(long value) { StrictJson.require(value >= 0 && value <= 4_294_967_294L, "native full-ID range"); }
    private static void revision(BigInteger value) { StrictJson.require(value != null && value.signum() >= 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "native uint64 revision range"); }
}
