package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentCaller153Api.Calls;
import org.xar.ck3.research.m5.GovernmentCaller153Api.DiagnosticCall;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Entry;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Memory;
import org.xar.ck3.research.m5.GovernmentCaller153Api.Outcome;
import org.xar.ck3.research.m5.GovernmentTierLookupKey150.LookupKey32;
import org.xar.ck3.research.m5.InternedLookup155Api;

/** Genuine typed caller153 binding, no replacement of existing conversion/caller/selection. */
public final class InternedLookup155Binder {
    private InternedLookup155Binder() { }

    public static GovernmentCaller153Api.Calls bind(long imageBaseBits,
            InternedLookup155Api.Memory memory, InternedLookup155Api.Calls lookupCalls,
            GovernmentCaller153Api.Calls outerCalls) {

        // Create an adapter that implements GovernmentCaller153Api.Calls
        // It delegates readGsQword58, call3F5F970, callABBAF0 to outerCalls.
        // It implements call3F4F8E0 by calling InternedLookup155.execute.

        return new GovernmentCaller153Api.Calls() {
            @Override
            public long readGsQword58() {
                return outerCalls.readGsQword58();
            }

            @Override
            public long call3F4F8E0(LookupKey32 ecxBits) {
                // Caller153 binder supplies concrete call3F4F8E0(key) by InternedLookup155.execute(new Entry(imageBase,key),memory,lookupCalls);
                InternedLookup155Api.Entry entry = new InternedLookup155Api.Entry(imageBaseBits, ecxBits);
                return InternedLookup155.execute(entry, memory, lookupCalls);
            }

            @Override
            public long call3F5F970(int ecxBits) {
                return outerCalls.call3F5F970(ecxBits);
            }

            @Override
            public void callABBAF0(DiagnosticCall arguments) {
                outerCalls.callABBAF0(arguments);
            }
        };
    }
}
