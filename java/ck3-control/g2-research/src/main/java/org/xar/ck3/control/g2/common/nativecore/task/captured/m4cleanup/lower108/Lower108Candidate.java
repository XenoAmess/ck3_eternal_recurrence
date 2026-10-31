package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower108;

import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.qwordrelease.QwordReleaseSequence;

public final class Lower108Candidate {

    private static final List<QwordReleaseSequence.Slot> PLAN = List.of(
        new QwordReleaseSequence.Slot(0, 0x542f220L),
        new QwordReleaseSequence.Slot(8, 0x542f228L),
        new QwordReleaseSequence.Slot(16, 0x542f230L),
        new QwordReleaseSequence.Slot(88, 0x542f278L),
        new QwordReleaseSequence.Slot(96, 0x542f280L)
    );

    private Lower108Candidate() { }

    public static void execute(Lower108Inputs.CallInput input, Lower108Inputs.Memory memory, Lower108Inputs.Calls calls) {
        QwordReleaseSequence.execute(
            input.moduleBaseRaw(),
            input.objectRaw(),
            memory,
            calls::call424E364,
            PLAN
        );
    }
}