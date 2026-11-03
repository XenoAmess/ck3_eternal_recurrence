package org.xar.ck3.study.m6.posterror256;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Selects the held61 error-cell CALL from an already-pushed full-Outcome frame. */
public final class FreeKnownError256 {
    private FreeKnownError256() { }

    /** Explicit whole entry port; its type does not establish native provenance or authority. */
    public static FreePostState251Api.Children bind(PostState240Api.EntryExecutor error32,
            FreePostState251Api.Children remaining) {
        return (frame, sameMemory) -> {
            GovernmentCrtBoundary185Api.Call call = frame.call();
            if (frame.ownerEntryRva() == 0x424E364L
                    && call.callSiteRva() == 0x424E384L
                    && frame.instructionLength() == 5
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x423B18CL) {
                return error32.execute(frame.childInput(), sameMemory);
            }
            return remaining.invoke(frame, sameMemory);
        };
    }
}
