package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Acceptance helper for genuine warm -> cold installed sources. A runner must supply real private Root/M3 products.
 * No fixture config, Managed session, retained M3 token, Prepared or episode proof is manufactured here.
 */
public final class CommittedPendingEpisodeRecoveryAssertions {
    private CommittedPendingEpisodeRecoveryAssertions(){ }
    public static LifecycleTransitionProof.ContinueSuccessor requireRecovered(ContinuityStorePort.Session same,
            LifecycleComposites genuinelyCold,LifecycleTransitionProof.Base originalWarm,ActionReceipt actualCanonicalParent)throws Exception {
        String before=same.head().digest();long sequence=same.head().state().sequence();
        var edge=genuinelyCold.recordedPendingEpisode(same,actualCanonicalParent);edge.requireCurrent(same);
        byte[] originalEncoded=assertInstanceOf(LifecycleTransitionProof.class,originalWarm).encode();
        assertArrayEquals(originalEncoded,edge.proof().encode());
        assertTrue(originalWarm.publication().proofDocuments().containsAll(originalWarm.publication().committedDocuments()));
        var proof=genuinelyCold.recoverCommittedPendingEpisode(same,actualCanonicalParent,edge);
        assertArrayEquals(originalEncoded,proof.encode());assertTrue(proof.publication().warmCommit().isEmpty());
        assertThrows(IllegalStateException.class,proof::commit);
        assertSame(proof,genuinelyCold.recoverCommittedPendingEpisode(same,actualCanonicalParent,edge));
        if(actualCanonicalParent.state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied)
            assertSame(proof,genuinelyCold.requireCommittedEpisode(same,actualCanonicalParent));
        else assertThrows(IllegalArgumentException.class,()->genuinelyCold.requireCommittedEpisode(same,actualCanonicalParent));
        assertEquals(sequence,same.head().state().sequence());assertEquals(before,same.head().digest());return proof;
    }
    public static void requirePrivateSourceRefusal(ContinuityStorePort.Session same,LifecycleComposites actualWithoutRetainedM3,
            ActionReceipt actualCanonicalParent)throws Exception {
        String head=same.head().digest();var edge=actualWithoutRetainedM3.recordedPendingEpisode(same,actualCanonicalParent);
        assertThrows(Exception.class,()->actualWithoutRetainedM3.recoverCommittedPendingEpisode(same,actualCanonicalParent,edge));
        assertEquals(head,same.head().digest());assertThrows(IllegalArgumentException.class,
                ()->actualWithoutRetainedM3.requireCommittedEpisode(same,actualCanonicalParent));
    }
    public static void requireSameWarmPublication(ContinuityStorePort.Session same,LifecycleComposites actualWarm,
            LifecycleTransitionProof.ContinueSuccessor originalWarm,ActionReceipt actualCanonicalParent)throws Exception {
        String head=same.head().digest();var edge=actualWarm.recordedPendingEpisode(same,actualCanonicalParent);
        var retained=actualWarm.recoverCommittedPendingEpisode(same,actualCanonicalParent,edge);
        assertSame(originalWarm,retained);assertTrue(retained.publication().warmCommit().isPresent());
        assertSame(originalWarm.commit(),retained.commit());assertEquals(head,same.head().digest());
    }
}
