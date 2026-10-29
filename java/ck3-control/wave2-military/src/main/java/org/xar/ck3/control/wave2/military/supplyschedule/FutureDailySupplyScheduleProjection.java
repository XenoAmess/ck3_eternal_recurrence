package org.xar.ck3.control.wave2.military.supplyschedule;

import java.util.ArrayList;
import java.util.List;

/** Separately supplied dates select current buckets conditionally; no calendar or future effect is inferred. */
public final class FutureDailySupplyScheduleProjection {
    public static final String CONDITION = "separately_supplied_native_date_and_day_with_observed_buckets_unchanged";
    private FutureDailySupplyScheduleProjection() { }
    public record NativeFrame(int dateRawI32, int nativeDayIndexRawI32) { }
    public record MatchingPhase(int phaseIndexI32, List<Integer> matchingPositions, int subjectOccurrenceCountI32) {
        public MatchingPhase { matchingPositions = List.copyOf(matchingPositions); }
    }
    public record SelectedFrame(int prospectiveIndex, int dateRawI32, int nativeDayIndexRawI32,
            int selectedPhaseIndexI32, boolean conditionalBucketOccurrencesReady, List<Integer> matchingPositions,
            Integer subjectOccurrenceCountI32, String unavailableReason) {
        public SelectedFrame { if (matchingPositions != null) matchingPositions = List.copyOf(matchingPositions); }
        public boolean actualCallbackObserved() { return false; }
    }
    public record Projection(FutureDailySupplySchedule observedSchedule, List<MatchingPhase> observedMatchingPhases,
            List<Integer> unavailablePhases, List<SelectedFrame> prospectiveFrames) {
        public Projection {
            java.util.Objects.requireNonNull(observedSchedule);
            observedMatchingPhases = List.copyOf(observedMatchingPhases);
            unavailablePhases = List.copyOf(unavailablePhases);
            prospectiveFrames = List.copyOf(prospectiveFrames);
        }
        public boolean ready() { return observedSchedule.ready(); }
        public FutureDailySupplySchedule.Status status() { return observedSchedule.status(); }
        public boolean calendarDerived() { return false; }
        public boolean actualFutureCallbackObserved() { return false; }
        public boolean futureBucketMutationsReconstructed() { return false; }
        public boolean futureSupplyEligibilityReady() { return false; }
        public boolean futureStockOrStrengthReady() { return false; }
        public boolean fullDailySupplyTransitionReady() { return false; }
        public boolean fullMonthlyReady() { return false; }
    }
    public static Projection project(FutureDailySupplySchedule schedule) { return project(schedule, List.of()); }
    public static Projection project(FutureDailySupplySchedule schedule, List<NativeFrame> prospectiveFrames) {
        if (schedule == null) return null;
        List<MatchingPhase> matching = new ArrayList<>(); List<Integer> missing = new ArrayList<>();
        for (var phase : schedule.phases()) {
            if (!phase.ready()) missing.add(phase.phaseIndexI32());
            else if (phase.subjectOccurrenceCountI32() > 0) matching.add(new MatchingPhase(phase.phaseIndexI32(), phase.matchingPositions(), phase.subjectOccurrenceCountI32()));
        }
        List<SelectedFrame> selected = new ArrayList<>();
        for (NativeFrame frame : prospectiveFrames) {
            int phaseIndex = FutureDailySupplySchedule.phaseIndex(frame.nativeDayIndexRawI32());
            var phase = schedule.phases().isEmpty() ? null : schedule.phases().get(phaseIndex);
            boolean ready = phase != null && phase.ready();
            selected.add(new SelectedFrame(selected.size(), frame.dateRawI32(), frame.nativeDayIndexRawI32(), phaseIndex,
                    ready, ready ? phase.matchingPositions() : null, ready ? phase.subjectOccurrenceCountI32() : null,
                    ready ? null : phase == null ? schedule.unavailableReason() : phase.unavailableReason()));
        }
        return new Projection(schedule, matching, missing, selected);
    }
}
