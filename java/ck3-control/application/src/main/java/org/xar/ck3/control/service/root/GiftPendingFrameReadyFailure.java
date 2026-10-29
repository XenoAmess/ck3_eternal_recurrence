package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.Proof;

/** APP control flow issued only by the same-package actual Gift source after its real bounded native wait.
 * There is no public constructor/factory: copied policy DATA cannot enter the public planning retry budget.
 * This is an in-process, thread-bound marker; Java object serialization is not a supported contract. */
public final class GiftPendingFrameReadyFailure extends RuntimeException {
    private static final long serialVersionUID = 1L;
    @FunctionalInterface interface Original { void require() throws IOException; }
    @SuppressWarnings("serial") private final Session same;
    @SuppressWarnings("serial") private final PlanningRequest request;
    @SuppressWarnings("serial") private final Obj projection;
    @SuppressWarnings("serial") private final Original original;
    @SuppressWarnings("serial") private final Thread thread;
    private boolean consumed;
    private GiftPendingFrameReadyFailure(Session same,PlanningRequest request,Proof proof,Original original) {
        super("private faction pending receipt has a newer same-date paused frame");
        this.same=Objects.requireNonNull(same);this.request=Objects.requireNonNull(request);
        this.original=Objects.requireNonNull(original);thread=Thread.currentThread();
        byte[] encoded=GiftPendingFrameCodec.encodeProof(Objects.requireNonNull(proof));
        if(!proof.equals(GiftPendingFrameCodec.decodeProof(encoded)))throw new IllegalArgumentException("sole Gift proof roundtrip changed");
        projection=DriverJson.object(GiftPendingFrameCodec.classifyProof(proof),1<<20);
    }
    static GiftPendingFrameReadyFailure issue(Session same,PlanningRequest request,Proof proof,Original original)throws IOException {
        Objects.requireNonNull(original).require();return new GiftPendingFrameReadyFailure(same,request,proof,original);
    }
    public Session session() { return same; }
    public PlanningRequest request() { return request; }
    public Obj projection() { return projection; }
    public RuntimeException originalFailure() { return this; }
    /** A live source callback may be consumed once, by its creating thread; old exceptions cannot feed a new budget. */
    public synchronized void requireOriginal()throws IOException {
        if(consumed||thread!=Thread.currentThread())throw new IOException("Gift frame marker lost its original single-use source callback");
        original.require();consumed=true;
    }
}
