package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;

/** Actual installed Game's fixed independent native core query; no full Snapshot or Driver mutation. */
public final class RootCoreFrameRuntime {
    private final RootRuntimeContext context;
    public RootCoreFrameRuntime(RootRuntimeContext actual) {context=Objects.requireNonNull(actual);}
    public void requireOwner(RootApplicationSession actual)throws IOException {
        Objects.requireNonNull(actual);
        StrictJson.require(context.actions()==actual&&actual.writer()==context.writer()&&actual.archive()==context.archive()
                &&actual.identity().game().equals(context.game().generation())&&actual.identity().sessionId().equals(context.game().sessionId())
                &&actual.identity().machineId().equals(context.game().machineId())&&actual.nativeTransport()==context.transport(),
                "standalone core runtime crossed its actual installed Root/Game/writer");
    }
    /** Caller holds Root's standalone call scope and the original writer Session; a failed result is preserved before refusal. */
    public CoreFrame read(RootApplicationSession actual,ContinuityStorePort.Session same,Instant deadline)throws IOException,InterruptedException {
        context.writer().requireSession(Objects.requireNonNull(same));requireOwner(actual);context.requireCurrent(Objects.requireNonNull(deadline));
        var transport=context.transport();var original=transport.readCoreFrame(deadline);
        context.writer().requireSession(same);context.archive().withSession(same).preserve(original);
        CoreFrame result=CoreFramePublicCodec.decodeOutcome(original);
        requireOwner(actual);context.requireCurrent(deadline);context.writer().requireSession(same);return result;
    }
}
