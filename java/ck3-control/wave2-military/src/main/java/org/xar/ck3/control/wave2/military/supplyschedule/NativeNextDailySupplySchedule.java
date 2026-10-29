package org.xar.ck3.control.wave2.military.supplyschedule;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrame;

/** Join of independently validated current membership and the same-row source-derived next clock. */
public record NativeNextDailySupplySchedule(FutureDailySupplyScheduleProjection.Projection scheduleProjection,
        SourceNextFrame sourceFrame) {
    public NativeNextDailySupplySchedule { Objects.requireNonNull(scheduleProjection); }
    public boolean nativeNextPairUsed() { return sourceFrame != null && sourceFrame.ready(); }
    public boolean fullFutureCdate64Reconstructed() { return sourceFrame != null && sourceFrame.fullCdate64Ready(); }
    public Long nextDateStorageRaw64() { return sourceFrame == null ? null : sourceFrame.nextDateStorageRaw64(); }
    public Integer nextCalendarDayU8() { return sourceFrame instanceof SourceNextFrame.Extended23 extended ? extended.nextCalendarDayU8() : null; }
    public Integer nextCalendarMonthU8() { return sourceFrame instanceof SourceNextFrame.Extended23 extended ? extended.nextCalendarMonthU8() : null; }
    public static NativeNextDailySupplySchedule project(FutureDailySupplySchedule schedule, SourceNextFrame frame) {
        if (schedule == null) return null;
        if (frame == null || !frame.ready()) return new NativeNextDailySupplySchedule(FutureDailySupplyScheduleProjection.project(schedule), frame);
        same(schedule.subjectArmyIdU32(), frame.subjectArmyIdU32()); same(schedule.subjectCarmyIdU32(), frame.subjectCarmyIdU32());
        same(schedule.currentDateStorageRaw64(), frame.currentDateStorageRaw64()); same(schedule.currentDateRawI32(), frame.currentDateRawI32());
        same(schedule.nativeDayIndexRawI32(), frame.values().currentNativeDayIndexRawI32());
        var projected = FutureDailySupplyScheduleProjection.project(schedule,
                List.of(new FutureDailySupplyScheduleProjection.NativeFrame(frame.nextDateRawI32(), frame.values().nextNativeDayIndexRawI32())));
        return new NativeNextDailySupplySchedule(projected, frame);
    }
    private static void same(Number observed, Number expected) {
        if (!(observed == null || expected != null && observed.longValue() == expected.longValue()))
            throw new org.xar.ck3.control.contracts.projection.ProjectionDomainRejection("native next supply frame clock differs from the same-row schedule");
    }
}
