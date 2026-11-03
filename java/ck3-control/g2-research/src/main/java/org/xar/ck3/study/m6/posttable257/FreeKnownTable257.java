package org.xar.ck3.study.m6.posttable257;

import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;

public final class FreeKnownTable257 {
    private FreeKnownTable257() { }

    public static FreePostState251Api.Children bind(PostState240Api.EntryExecutor table, FreePostState251Api.Children remaining) {
        return new FreePostState251Api.Children() {
            @Override public QueueFp604Api.Outcome invoke(FreePostState251Api.AlreadyPushedCallFrame frame, GovernmentCrtBoundary185Api.Memory sameMemory) {
                if (frame.ownerEntryRva() == 0x424E364L
                        && frame.call().callSiteRva() == 0x424E394L
                        && frame.instructionLength() == 5
                        && frame.call().kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && frame.call().targetBits() == 0x423B0D4L) {
                    return table.execute(frame.childInput(), sameMemory);
                }
                return remaining.invoke(frame, sameMemory);
            }
        };
    }
}