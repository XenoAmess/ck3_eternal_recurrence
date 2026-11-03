package org.xar.ck3.study.m6.postdefault252;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.DefaultAllocateWithFp648;
import org.xar.ck3.control.g2.m2.nativecode.DefaultReleaseWithFp648;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/** Exact247 continuation consumers of the held complete648 18/14 producers. */
public final class DefaultPostForward252 {
    private DefaultPostForward252() { }

    public static PostVtable247Api.Children bind(DefaultStaticFp648Api.Calls explicitDefaults,
            PostVtable247Api.Children remaining) {
        Objects.requireNonNull(explicitDefaults);
        Objects.requireNonNull(remaining);
        return new PostVtable247Api.Children() {
            @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                Objects.requireNonNull(frame);
                var call=frame.call();
                if(frame.ownerEntryRva()!=0x855830L||call.callSiteRva()!=0x85585bL
                        ||frame.instructionLength()!=4
                        ||call.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        ||call.targetBits()!=frame.imageBaseBits()+0x8571c0L)
                    return remaining.invoke(frame,sameMemory);
                var actual=frame.childInput();
                return DefaultReleaseWithFp648.fromSlot10(new DefaultStaticFp648Api.Input(
                        actual.entry(),actual.directionFlagSet(),actual.mxcsr()),sameMemory,explicitDefaults);
            }

            @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,
                    GovernmentCrtBoundary185Api.Memory sameMemory) {
                Objects.requireNonNull(frame);
                var transfer=frame.transfer();var actual=frame.targetInput();
                if(frame.ownerEntryRva()!=0x855870L||transfer.jumpSiteRva()!=0x8558a0L
                        ||frame.instructionLength()!=3
                        ||transfer.kind()!=GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        ||transfer.targetBits()!=actual.entry().imageBaseBits()+0x8571d0L)
                    return remaining.tail(frame,sameMemory);
                //648 Input has only Entry/DF/MXCSR. No fabricated origin, push, RET or Outcome wrapper.
                return DefaultAllocateWithFp648.fromSlot08(new DefaultStaticFp648Api.Input(
                        actual.entry(),actual.directionFlagSet(),actual.mxcsr()),sameMemory,explicitDefaults);
            }
        };
    }
}
