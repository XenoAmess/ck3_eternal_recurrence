package org.xar.ck3.study.m6.postdefault255;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.postfree253.DefaultFreePost253;
import org.xar.ck3.study.m6.postdefault252.DefaultPostForward252;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/**
 * Production factory binding DefaultFreePost253 and DefaultPostForward252.
 * Uses actual frame origins and same RAM; no invented state or side effects.
 */
public final class DefaultFreeChain255 {
    private DefaultFreeChain255() { }

    public static PostVtable247Api.Children bind(
            FreePostState251Api.Children freeChildren,
            DefaultStaticFp648Api.Calls defaultDelegate,
            PostVtable247Api.Children remaining) {
        Objects.requireNonNull(freeChildren);
        Objects.requireNonNull(defaultDelegate);
        Objects.requireNonNull(remaining);

        return new PostVtable247Api.Children() {
            @Override
            public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                Objects.requireNonNull(frame);
                Objects.requireNonNull(sameMemory);

                long origin = frame.childInput().originCallSiteRva();
                DefaultStaticFp648Api.Calls boundDelegate = DefaultFreePost253.bind(
                        sameMemory, freeChildren, origin, defaultDelegate);

                PostVtable247Api.Children boundChildren = DefaultPostForward252.bind(
                        boundDelegate, remaining);

                return boundChildren.invoke(frame, sameMemory);
            }

            @Override
            public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                Objects.requireNonNull(frame);
                Objects.requireNonNull(sameMemory);

                long origin = frame.targetInput().originCallSiteRva();
                DefaultStaticFp648Api.Calls boundDelegate = DefaultFreePost253.bind(
                        sameMemory, freeChildren, origin, defaultDelegate);

                PostVtable247Api.Children boundChildren = DefaultPostForward252.bind(
                        boundDelegate, remaining);

                return boundChildren.tail(frame, sameMemory);
            }
        };
    }
}