package org.xar.ck3.control.wave2.military.updaterwrites;

import java.util.Objects;

/** Native family projection only; this model grants no future execution or source qualification. */
public sealed interface SourceNextFrame permits SourceNextFrame.Legacy19, SourceNextFrame.Extended23 {
    enum Status { AVAILABLE, UNAVAILABLE }
    record Values(Status status, String unavailableReason, Long currentDateStorageRaw64,
                  Integer currentDateRawI32, Integer currentNativeDayIndexRawI32,
                  Integer nextDateRawI32, Integer nextNativeDayIndexRawI32,
                  Long subjectArmyIdU32, Long subjectCarmyIdU32) {
        public Values {
            Objects.requireNonNull(status);
            boolean available = status == Status.AVAILABLE;
            if (available && (unavailableReason != null || currentDateStorageRaw64 == null
                    || currentDateRawI32 == null || currentNativeDayIndexRawI32 == null
                    || nextDateRawI32 == null || nextNativeDayIndexRawI32 == null
                    || subjectArmyIdU32 == null || subjectCarmyIdU32 == null)) {
                throw new IllegalArgumentException("available source-next native operands are incomplete");
            }
            if (!available && (unavailableReason == null || unavailableReason.isEmpty())) {
                throw new IllegalArgumentException("unavailable source-next family requires reason");
            }
            if (subjectArmyIdU32 != null && (subjectArmyIdU32 < 0 || subjectArmyIdU32 > 0xffff_ffffL)
                    || subjectCarmyIdU32 != null && (subjectCarmyIdU32 < 0 || subjectCarmyIdU32 > 0xffff_ffffL)) {
                throw new IllegalArgumentException("source-next subject must be uint32 or null");
            }
        }
    }
    record Legacy19(Values values) implements SourceNextFrame {
        public Legacy19 { Objects.requireNonNull(values); }
    }
    record Extended23(Values values, boolean fullCdate64Ready, Long nextDateStorageRaw64,
                      Integer nextCalendarDayU8, Integer nextCalendarMonthU8) implements SourceNextFrame {
        public Extended23 {
            Objects.requireNonNull(values);
            if (nextCalendarDayU8 != null && (nextCalendarDayU8 < 0 || nextCalendarDayU8 > 255)
                    || nextCalendarMonthU8 != null && (nextCalendarMonthU8 < 0 || nextCalendarMonthU8 > 255)) {
                throw new IllegalArgumentException("source-next calendar values must be uint8 or null");
            }
            if (fullCdate64Ready && (values.status() != Status.AVAILABLE || nextDateStorageRaw64 == null
                    || nextCalendarDayU8 == null || nextCalendarMonthU8 == null)) {
                throw new IllegalArgumentException("ready complete CDate64 requires all source operands");
            }
        }
    }
    Values values();
    default boolean ready() { return values().status() == Status.AVAILABLE; }
    default Integer currentDateRawI32() { return values().currentDateRawI32(); }
    default Integer nextDateRawI32() { return values().nextDateRawI32(); }
    default Long currentDateStorageRaw64() { return values().currentDateStorageRaw64(); }
    default Long subjectArmyIdU32() { return values().subjectArmyIdU32(); }
    default Long subjectCarmyIdU32() { return values().subjectCarmyIdU32(); }
    default Long nextDateStorageRaw64() {
        return this instanceof Extended23 extended ? extended.nextDateStorageRaw64() : null;
    }
    default boolean fullCdate64Ready() {
        return this instanceof Extended23 extended && extended.fullCdate64Ready();
    }
    default boolean hasFullDateFields() { return this instanceof Extended23; }
}
