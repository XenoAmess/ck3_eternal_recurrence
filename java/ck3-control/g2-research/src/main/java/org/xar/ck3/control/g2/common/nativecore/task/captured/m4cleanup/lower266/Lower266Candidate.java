package org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.lower266;

import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.qwordrelease.QwordReleaseSequence;

public final class Lower266Candidate {

    private static final List<QwordReleaseSequence.Slot> PLAN = List.of(
        new QwordReleaseSequence.Slot(24, 0x542f238L),
        new QwordReleaseSequence.Slot(32, 0x542f240L),
        new QwordReleaseSequence.Slot(40, 0x542f248L),
        new QwordReleaseSequence.Slot(48, 0x542f250L),
        new QwordReleaseSequence.Slot(56, 0x542f258L),
        new QwordReleaseSequence.Slot(64, 0x542f260L),
        new QwordReleaseSequence.Slot(72, 0x542f268L),
        new QwordReleaseSequence.Slot(104, 0x542f288L),
        new QwordReleaseSequence.Slot(112, 0x542f290L),
        new QwordReleaseSequence.Slot(120, 0x542f298L),
        new QwordReleaseSequence.Slot(128, 0x542f2a0L),
        new QwordReleaseSequence.Slot(136, 0x542f2a8L),
        new QwordReleaseSequence.Slot(144, 0x542f2b0L)
    );

    private Lower266Candidate() { }

    public static void execute(Lower266Inputs.CallInput input, Lower266Inputs.Memory memory, Lower266Inputs.Calls calls) {
        QwordReleaseSequence.execute(
            input.moduleBaseRaw(),
            input.objectRaw(),
            memory,
            calls::call424E364,
            PLAN
        );
    }
}