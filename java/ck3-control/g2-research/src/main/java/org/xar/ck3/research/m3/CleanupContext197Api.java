package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestE92780;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.InlineStorageCleanupPlan;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower61.Lower61Inputs;

/** Business memory/normal-effect contract, without Native stack or CPU execution. */
public final class CleanupContext197Api {
    private CleanupContext197Api() { }
    public interface Memory extends RequestE92780.Memory, Lower61Inputs.Memory { }
    public enum Completion { RETURNED, UNSUPPORTED_ERROR_BRANCH }
    public record Result(Completion completion, InlineStorageCleanupPlan.Plan plan) { }
}
