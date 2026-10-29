package org.xar.ck3.control.wave3.governance.guardianskills;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.governance.educationneeds.EducationNeedsModel.FocusState;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.GuardianProfile;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.Skill;
import org.xar.ck3.control.wave2.governance.educationpreference.EducationPreferenceModel.SkillObservation;
import org.xar.ck3.control.wave3.governance.guardianskills.GuardianSkillsModel.*;

/** Exact old native-context profile join and independent raw-focus/learning projection. */
public final class GuardianSkillInputs {
    private GuardianSkillInputs() { }

    public static GuardianProfile validateContextBinding(GuardianProfile profile, Context context) {
        requireDomain("1.20.0.4".equals(context.exactBuild()) && "educate_child_interaction".equals(context.interactionKey())
                && "available".equals(context.status()), "guardian profile requires available exact .4 education context");
        requireDomain(profile.owningNativeRevision().equals(context.frame().nativeRevision()), "guardian profile query revision mismatch");
        requireDomain(Objects.equals(profile.childCharacterId(), context.secondaryRecipientId()), "guardian child/final secondary recipient mismatch");
        requireDomain(Objects.equals(profile.characterId(), context.secondaryActorId()), "guardian/final secondary actor mismatch");
        return profile;
    }

    public static Projection project(Input input) {
        FocusSubject needs = input.needs(); GuardianProfile profile = input.profile().orElse(null);
        if (profile != null) {
            validateContextBinding(profile, input.context().orElseThrow(() -> new ProjectionDomainRejection("observed profile requires owning query context")));
        }
        Join join;
        if (profile == null) { join = Join.PROFILE_NOT_OBSERVED; }
        else if (profile.childCharacterId() == null || profile.childCharacterId() != needs.childFullId()) { join = Join.CHILD_MISMATCH; }
        else if (needs.familyFrame().isEmpty()) { join = Join.FRAME_NOT_OBSERVED; }
        else {
            QueryFrame query = input.context().orElseThrow(() -> new ProjectionDomainRejection("observed profile requires owning query context")).frame();
            FamilyFrame family = needs.familyFrame().get();
            join = Objects.equals(family.nativeRevision(), query.nativeRevision()) && family.dateRaw() != null && family.dateRaw() == query.dateRaw()
                    && family.playedCharacterId() != null && family.playedCharacterId() == query.playerCharacterId() ? Join.JOINED : Join.FRAME_MISMATCH;
        }
        SkillObservation learning = profile != null ? profile.skills().get(Skill.LEARNING) : unavailable(Join.PROFILE_NOT_OBSERVED.reason());
        SkillObservation focused;
        if (!join.available()) { focused = unavailable(join.reason()); }
        else if (needs.focusManagement().state() == FocusState.EDUCATION_FOCUS_PRESENT) {
            Optional<Skill> key = Skill.forFocus(needs.focusManagement().currentKey());
            requireDomain(key.isPresent(), "observed education focus must name one of five actual skill operands");
            // The old observation projection is raw, including martial. The separate preference uses total-martial.
            focused = profile.skills().get(key.get());
        } else {
            focused = unavailable(switch (needs.focusManagement().state()) {
                case KNOWN_ABSENT -> "education_focus_known_absent";
                case OTHER_FOCUS_PRESENT -> "current_focus_is_not_education";
                case UNKNOWN -> "education_focus_not_observed";
                case EDUCATION_FOCUS_PRESENT -> throw new IllegalStateException("education focus already handled");
            });
        }
        return new Projection(needs, input.profile(), join, focused, learning);
    }

    private static void requireDomain(boolean condition, String reason) {
        if (!condition) { throw new ProjectionDomainRejection(reason); }
    }

    private static SkillObservation unavailable(String reason) { return new SkillObservation(false, null, reason); }
}
