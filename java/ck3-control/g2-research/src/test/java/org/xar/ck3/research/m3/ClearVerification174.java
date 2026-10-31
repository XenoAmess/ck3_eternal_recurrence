package org.xar.ck3.research.m3;

import java.util.List;
import java.util.Map;

/** Explicit comparison of recorded observation against scenario contract. */
public final class ClearVerification174 {
    private ClearVerification174() { }

    public static void verify(ClearCasesApi174.Scenario scenario, RecordedClear174.Observation actual, RecordedClear174.Checks checks) {
        String id = scenario.id();

        checks.check(actual.completion() == scenario.expected(), id + ": completion mismatch");

        List<String> actualEvents = actual.events();
        List<String> expectedEvents = scenario.expectedEvents();
        boolean eventsMatch = actualEvents.size() == expectedEvents.size();
        if (eventsMatch) {
            for (int i = 0; i < expectedEvents.size(); i++) {
                if (!actualEvents.get(i).equals(expectedEvents.get(i))) {
                    eventsMatch = false;
                    break;
                }
            }
        }
        checks.check(eventsMatch, id + ": events mismatch");

        Map<Long, ClearCasesApi174.Word> expectedFinalWords = RecordedClear174.words(scenario.expectedFinalWords());
        Map<Long, ClearCasesApi174.Word> actualFinalWords = actual.finalWords();
        checks.check(actualFinalWords.equals(expectedFinalWords), id + ": finalWords mismatch");

        for (ClearCasesApi174.Hook hook : scenario.hooks()) {
            int applied = actual.appliedHooks().getOrDefault(hook, 0);
            checks.check(applied == 1, id + ": hook " + hook.event() + " ordinal " + hook.ordinal() + " applied " + applied + " times");
        }
    }
}
