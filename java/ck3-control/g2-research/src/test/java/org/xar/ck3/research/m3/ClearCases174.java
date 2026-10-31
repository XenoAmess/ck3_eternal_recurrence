package org.xar.ck3.research.m3;
import java.util.List;
import java.util.ArrayList;

public final class ClearCases174 {
    private ClearCases174() { }

    public static List<ClearCasesApi174.Scenario> cases() {
        List<ClearCasesApi174.Scenario> list = new ArrayList<>();

        // Case 1: Empty (initial count 0)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("W32:" + Long.toUnsignedString(recv + 0xC4L, 16) + ":0");
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            list.add(new ClearCasesApi174.Scenario("empty", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.CLEARED, expectedEvents, finalWords));
        }

        // Case 2: Captured first base/end (2 rows, hook changes header, fresh count 0)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            long row0 = base;
            long row1 = base + 0x68L;
            long p0 = 0x3000L;
            long p1 = 0x4000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 2L));
            initial.add(new ClearCasesApi174.Word(row0, 8, p0));
            initial.add(new ClearCasesApi174.Word(row1, 8, p1));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<ClearCasesApi174.Word> changes = new ArrayList<>();
            changes.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, 0x9999L));
            changes.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            hooks.add(new ClearCasesApi174.Hook(ClearCasesApi174.Event.DESTROY, 1, changes));
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("DESTROY:" + Long.toUnsignedString(p0, 16) + ":" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(row1, 16));
            expectedEvents.add("DESTROY:" + Long.toUnsignedString(p1, 16) + ":" + Long.toUnsignedString(row1, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("W32:" + Long.toUnsignedString(recv + 0xC4L, 16) + ":0");
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, 0x9999L));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            finalWords.add(new ClearCasesApi174.Word(row0, 8, p0));
            finalWords.add(new ClearCasesApi174.Word(row1, 8, p1));
            list.add(new ClearCasesApi174.Scenario("captured", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.CLEARED, expectedEvents, finalWords));
        }

        // Case 3: Fresh cleanup base/count (1 row, hook changes header to 2, cleanup 4 calls)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            long row0 = base;
            long p0 = 0x3000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 1L));
            initial.add(new ClearCasesApi174.Word(row0, 8, p0));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<ClearCasesApi174.Word> changes = new ArrayList<>();
            changes.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, 0x5000L));
            changes.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 2L));
            hooks.add(new ClearCasesApi174.Hook(ClearCasesApi174.Event.DESTROY, 1, changes));
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("DESTROY:" + Long.toUnsignedString(p0, 16) + ":" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("CLEANUP:" + Long.toUnsignedString(0x5000L + 0x48L, 16));
            expectedEvents.add("CLEANUP:" + Long.toUnsignedString(0x5000L + 0x28L, 16));
            expectedEvents.add("CLEANUP:" + Long.toUnsignedString(0x5000L + 0x68L + 0x48L, 16));
            expectedEvents.add("CLEANUP:" + Long.toUnsignedString(0x5000L + 0x68L + 0x28L, 16));
            expectedEvents.add("W32:" + Long.toUnsignedString(recv + 0xC4L, 16) + ":0");
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, 0x5000L));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            finalWords.add(new ClearCasesApi174.Word(row0, 8, p0));
            list.add(new ClearCasesApi174.Scenario("fresh", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.CLEARED, expectedEvents, finalWords));
        }

        // Case 4: Nonpositive fresh cleanup count (initial 1, hook count negative, no cleanup)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            long row0 = base;
            long p0 = 0x3000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 1L));
            initial.add(new ClearCasesApi174.Word(row0, 8, p0));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<ClearCasesApi174.Word> changes = new ArrayList<>();
            changes.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, -1L));
            hooks.add(new ClearCasesApi174.Hook(ClearCasesApi174.Event.DESTROY, 1, changes));
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("DESTROY:" + Long.toUnsignedString(p0, 16) + ":" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("W32:" + Long.toUnsignedString(recv + 0xC4L, 16) + ":0");
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 0L));
            finalWords.add(new ClearCasesApi174.Word(row0, 8, p0));
            list.add(new ClearCasesApi174.Scenario("nonpos", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.CLEARED, expectedEvents, finalWords));
        }

        // Case 5: Java-only negative initial (unsupported)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, -1L));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, -1L));
            list.add(new ClearCasesApi174.Scenario("neginit", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.UNSUPPORTED_INITIAL_RANGE, expectedEvents, finalWords));
        }

        // Case 6: Java-only oversized cleanup (unsupported)
        {
            long recv = 0x1000L;
            long base = 0x2000L;
            long row0 = base;
            long p0 = 0x3000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 1L));
            initial.add(new ClearCasesApi174.Word(row0, 8, p0));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<ClearCasesApi174.Word> changes = new ArrayList<>();
            changes.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 100L));
            hooks.add(new ClearCasesApi174.Hook(ClearCasesApi174.Event.DESTROY, 1, changes));
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("R64:" + Long.toUnsignedString(recv + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("DESTROY:" + Long.toUnsignedString(p0, 16) + ":" + Long.toUnsignedString(row0, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(recv + 0xC4L, 16));
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(recv + 0xB8L, 8, base));
            finalWords.add(new ClearCasesApi174.Word(recv + 0xC4L, 4, 100L));
            finalWords.add(new ClearCasesApi174.Word(row0, 8, p0));
            list.add(new ClearCasesApi174.Scenario("oversize", false, 0L, 0L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.UNSUPPORTED_CLEANUP_RANGE, expectedEvents, finalWords));
        }

        // Case 7: Consumer identity mismatch (unsupported target)
        {
            long recv = 0x1000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<String> expectedEvents = new ArrayList<>();
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            list.add(new ClearCasesApi174.Scenario("mismatch", true, 0x1111L, 0x2222L, 0L, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.UNSUPPORTED_TARGET, expectedEvents, finalWords));
        }

        // Case 8: Consumer match (singleton return, empty core)
        {
            long recv = 0x1000L;
            long singletonRet = 0x5000L;
            long base = 0x6000L;
            List<ClearCasesApi174.Word> initial = new ArrayList<>();
            initial.add(new ClearCasesApi174.Word(singletonRet + 0xB8L, 8, base));
            initial.add(new ClearCasesApi174.Word(singletonRet + 0xC4L, 4, 0L));
            List<ClearCasesApi174.Hook> hooks = new ArrayList<>();
            List<String> expectedEvents = new ArrayList<>();
            expectedEvents.add("SINGLETON:" + Long.toUnsignedString(singletonRet, 16));
            expectedEvents.add("R64:" + Long.toUnsignedString(singletonRet + 0xB8L, 16));
            expectedEvents.add("R32:" + Long.toUnsignedString(singletonRet + 0xC4L, 16));
            expectedEvents.add("W32:" + Long.toUnsignedString(singletonRet + 0xC4L, 16) + ":0");
            List<ClearCasesApi174.Word> finalWords = new ArrayList<>();
            finalWords.add(new ClearCasesApi174.Word(singletonRet + 0xB8L, 8, base));
            finalWords.add(new ClearCasesApi174.Word(singletonRet + 0xC4L, 4, 0L));
            list.add(new ClearCasesApi174.Scenario("match", true, 0x281E7B0L, 0x281E7B0L, singletonRet, recv, new RegistrationClearApi174.Limits(10, 10), initial, hooks, RegistrationClearApi174.Completion.CLEARED, expectedEvents, finalWords));
        }

        return list;
    }
}