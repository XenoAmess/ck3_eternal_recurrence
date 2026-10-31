package org.xar.ck3.research.m3;

import java.util.List;
import java.util.ArrayList;

public final class FreeEffectsCases170 {
    private FreeEffectsCases170() {}

    private static FreeEffectsCasesApi170.Word w(long address, long value) {
        return new FreeEffectsCasesApi170.Word(address, value);
    }

    public static List<FreeEffectsCasesApi170.Scenario> cases() {
        List<FreeEffectsCasesApi170.Scenario> list = new ArrayList<>();

        // 1. Inline: rows == receiver + 8. No memory reads, no callbacks.
        {
            long receiver = 0x1000;
            long rows = receiver + 8;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "inline",
                0,
                receiver,
                rows,
                0,
                new FreeEffectsApi170.Targets(0, 0),
                List.of(),
                0,
                0,
                0,
                0x76543210,
                0x76543210,
                List.of(),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.SKIPPED_INLINE, 0)
            ));
        }

        // 2. Unsupported Selector: Read receiver vptr, then vptr+0x38. Code != target.selectorCode.
        {
            long receiver = 0x2000;
            long vptr = 0x2100;
            long selectorCode = 0x9999;
            long targetSelector = 0x1111;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "unsupported_selector",
                0,
                receiver,
                0x100,
                0,
                new FreeEffectsApi170.Targets(targetSelector, 0),
                List.of(
                    w(receiver, vptr),
                    w(vptr + 0x38, selectorCode)
                ),
                0,
                0,
                0,
                0x76543210,
                0x76543210,
                List.of(
                    "R64:2000",
                    "R64:2138"
                ),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.UNSUPPORTED_SELECTOR, selectorCode)
            ));
        }

        // 3. Unsupported Release: Selector matches. Read receiver+0x408 (getter), then returnedReceiver vptr, then vptr+0x10. Code != target.globalReleaseCode.
        {
            long receiver = 0x3000;
            long vptr = 0x3100;
            long selectorCode = 0x1111;
            long returnedReceiver = 0x3200;
            long returnedVptr = 0x3300;
            long releaseCode = 0x8888;
            long targetRelease = 0x2222;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "unsupported_release",
                0,
                receiver,
                0x100,
                0,
                new FreeEffectsApi170.Targets(selectorCode, targetRelease),
                List.of(
                    w(receiver, vptr),
                    w(vptr + 0x38, selectorCode),
                    w(receiver + 0x408, returnedReceiver),
                    w(returnedReceiver, returnedVptr),
                    w(returnedVptr + 0x10, releaseCode)
                ),
                0,
                0,
                0,
                0x76543210,
                0x76543210,
                List.of(
                    "R64:3000",
                    "R64:3138",
                    "R64:3408",
                    "R64:3200",
                    "R64:3310"
                ),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.UNSUPPORTED_RELEASE, releaseCode)
            ));
        }

        // 4. Selected Null Rows: Codes match. Rows == 0. No heap read/callback.
        {
            long receiver = 0x4000;
            long vptr = 0x4100;
            long selectorCode = 0x1111;
            long returnedReceiver = 0x4200;
            long returnedVptr = 0x4300;
            long releaseCode = 0x2222;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "selected_null_rows",
                0,
                receiver,
                0,
                0,
                new FreeEffectsApi170.Targets(selectorCode, releaseCode),
                List.of(
                    w(receiver, vptr),
                    w(vptr + 0x38, selectorCode),
                    w(receiver + 0x408, returnedReceiver),
                    w(returnedReceiver, returnedVptr),
                    w(returnedVptr + 0x10, releaseCode)
                ),
                0,
                0,
                0,
                0x76543210,
                0x76543210,
                List.of(
                    "R64:4000",
                    "R64:4138",
                    "R64:4408",
                    "R64:4200",
                    "R64:4310"
                ),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.SKIPPED_NULL, 0)
            ));
        }

        // 5. Selected Success: Codes match. Rows != 0. Heap handle 0 (validity check). HeapFree returns nonzero (success).
        {
            long receiver = 0x5000;
            long vptr = 0x5100;
            long selectorCode = 0x1111;
            long returnedReceiver = 0x5200;
            long returnedVptr = 0x5300;
            long releaseCode = 0x2222;
            long moduleBase = 0x10000000;
            long heapHandle = 0;
            long rows = 0x8000000000000100L;
            long alignment = 0xffff000000000040L;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "selected_success",
                moduleBase,
                receiver,
                rows,
                alignment,
                new FreeEffectsApi170.Targets(selectorCode, releaseCode),
                List.of(
                    w(receiver, vptr),
                    w(vptr + 0x38, selectorCode),
                    w(receiver + 0x408, returnedReceiver),
                    w(returnedReceiver, returnedVptr),
                    w(returnedVptr + 0x10, releaseCode),
                    w(moduleBase + 0x5C5DE30, heapHandle)
                ),
                0x80000000,
                0,
                0,
                0x76543210,
                0x76543210,
                List.of(
                    "R64:5000",
                    "R64:5138",
                    "R64:5408",
                    "R64:5200",
                    "R64:5310",
                    "R64:15c5de30",
                    "HEAP:0:0:8000000000000100"
                ),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.CALLEE_RETURNED, 0)
            ));
        }

        // 6. Selected Failure: Codes match. Rows != 0. Heap handle high bits. HeapFree returns 0 (failure). Error mapping occurs.
        {
            long receiver = 0x6000;
            long vptr = 0x6100;
            long selectorCode = 0x1111;
            long returnedReceiver = 0x6200;
            long returnedVptr = 0x6300;
            long releaseCode = 0x2222;
            long moduleBase = 0x20000000;
            long heapHandle = 0xFFFFFFFFFFFFFFFFL;
            long rows = 0x200;
            int lastError = 0x80000001;
            int mapped = 0xf1234567;
            list.add(new FreeEffectsCasesApi170.Scenario(
                "selected_failure",
                moduleBase,
                receiver,
                rows,
                0,
                new FreeEffectsApi170.Targets(selectorCode, releaseCode),
                List.of(
                    w(receiver, vptr),
                    w(vptr + 0x38, selectorCode),
                    w(receiver + 0x408, returnedReceiver),
                    w(returnedReceiver, returnedVptr),
                    w(returnedVptr + 0x10, releaseCode),
                    w(moduleBase + 0x5C5DE30, heapHandle)
                ),
                0,
                lastError,
                mapped,
                0x76543210,
                mapped,
                List.of(
                    "R64:6000",
                    "R64:6138",
                    "R64:6408",
                    "R64:6200",
                    "R64:6310",
                    "R64:25c5de30",
                    "HEAP:ffffffffffffffff:0:200",
                    "FAILURE_CELL",
                    "LAST_ERROR",
                    "MAP:80000001"
                ),
                new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.CALLEE_RETURNED, 0)
            ));
        }

        return list;
    }
}