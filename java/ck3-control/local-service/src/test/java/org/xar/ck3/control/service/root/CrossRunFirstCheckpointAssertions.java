package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.planning.campaign.CrossRunFirstCheckpointReader;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Assertions for the sole Root fixture's genuine private objects. No proof, manifest, SAVE or writer is created here. */
public final class CrossRunFirstCheckpointAssertions {
    private CrossRunFirstCheckpointAssertions(){ }

    /** Historical test DATA only; the original live NEXT proof is deliberately not retained as a reusable permit. */
    public static final class Observed {
        private final RootApplicationAssembly.Core core;
        private final SessionIdentity before,after;
        private final CrossRunFirstCheckpointReader.Saved saved;
        private final byte[] originalDriver;
        private Observed(RootApplicationAssembly.Core core,SessionIdentity before,SessionIdentity after,
                CrossRunFirstCheckpointReader.Saved saved){
            this.core=core;this.before=before;this.after=after;this.saved=saved;originalDriver=saved.material().savedDriver().encode();
        }
        public CrossRunFirstCheckpointReader.Saved saved(){return saved;}
    }

    /** Invoke in the actual Core NEXT DOMAIN_IMPORT scope before cycle rebind or Host publication. */
    public static Observed assertNextBeforeRebind(ContinuityStorePort.Session same,RootCrossRunPlanning.Prepared actual,
            RootRuntimeContext context,RootApplicationAssembly.NextEpisodeDomainProof proof)throws IOException {
        Objects.requireNonNull(proof);String head=same.head().digest();
        var saved=actual.requireNextFirst(context,same,proof);
        var binding=proof.baseline();var first=binding.firstCheckpoint();var baseline=binding.baseline();
        assertSame(proof.baselineMaterial(),saved.material());
        assertEquals(first.pair(),saved.material().pair());
        assertEquals(first.pairReference(),baseline.baseline().pairRef());
        assertEquals(first.baseline(),baseline.baseline());
        assertEquals(first.digest(),saved.material().checkpointDigest());
        assertEquals(baseline,saved.material().baseline());
        assertEquals(binding.semantic(),saved.material().sourceSemantic());
        assertEquals(binding.semantic(),proof.savedSemantic());
        assertArrayEquals(first.savedDriver().encode(),binding.driver().encode());
        assertArrayEquals(binding.driver().encode(),saved.material().savedDriver().encode());
        assertArrayEquals(binding.driver().encode(),proof.firstSavedDriver().encode());
        assertEquals(proof.beforeSession(),binding.beforeOwner());assertEquals(proof.afterSession(),binding.afterOwner());
        assertEquals(saved.plan(),CrossRunFirstCheckpointReader.requireNextPlan(binding.predecessorDriver(),
                binding.proof().encodedResult(),saved.state()));
        assertEquals(0,binding.savedDayCredit());assertEquals(0,binding.completedCycleCredit());
        assertEquals(head,same.head().digest());
        return new Observed(context.core(),proof.beforeSession(),proof.afterSession(),saved);
    }

    /** Later real SAVE/NEXT may replace the physical current pair; only the original historical branch is read here. */
    public static void assertRetainedOriginal(ContinuityStorePort.Session same,Observed original)throws IOException {
        Objects.requireNonNull(original);String head=same.head().digest();
        var reread=CrossRunFirstCheckpointReader.read(same,original.saved.material(),original.core.archive());
        assertEquals(original.saved.material().witness(),reread.material().witness());
        assertEquals(original.saved.material().firstMaterial().witness(),reread.material().firstMaterial().witness());
        assertEquals(original.saved.material().pair(),reread.material().pair());
        assertEquals(original.saved.material().baseline(),reread.material().baseline());
        assertEquals(original.saved.body(),reread.body());assertEquals(original.saved.strategySource(),reread.strategySource());
        assertEquals(original.saved.state(),reread.state());assertEquals(original.saved.plan(),reread.plan());
        assertArrayEquals(original.originalDriver,reread.material().savedDriver().encode());
        assertEquals(head,same.head().digest());
    }

    /** Both actual NEXT proofs established their own predecessor; a genuine restore may occur between them. */
    public static void assertDistinctNextSameCore(Observed earlier,Observed later) {
        assertSame(earlier.core,later.core);
        assertNotEquals(earlier.after.game(),later.after.game());
        assertNotEquals(earlier.saved.material().pair(),later.saved.material().pair());
        assertNotEquals(earlier.saved.material().pair().saveActionId(),later.saved.material().pair().saveActionId());
        assertNotEquals(earlier.saved.material().witness(),later.saved.material().witness());
        assertTrue(earlier.saved.material().baseline().sequence()<later.saved.material().baseline().sequence());
    }

    /** Keep original saved owner/material separate from the genuinely admitted physical replacement and its SEM. */
    public static void assertRestoredFirst(ContinuityStorePort.Session same,RootCrossRunPlanning.Prepared actual,
            RootRuntimeContext context,Observed savedOriginal)throws IOException {
        assertSame(savedOriginal.core,context.core());String head=same.head().digest();
        var original=context.restorationOriginal(same);
        assertEquals(SavedCheckpointMaterial.Kind.FIRST_BASELINE,original.material().kind());
        var material=assertInstanceOf(SavedFirstCheckpointMaterialStore.BaselinedMaterial.class,original.material());
        assertEquals(savedOriginal.saved.material().witness(),material.witness());
        assertEquals(savedOriginal.saved.material().pair(),material.pair());
        assertEquals(savedOriginal.after,material.session());
        assertNotEquals(material.session().game(),original.game());
        assertEquals(context.game().generation(),original.game());
        assertEquals(original.game(),original.semantic().frame().game());
        assertEquals(material.session().game(),material.sourceSemantic().frame().game());
        var compared=actual.requireRestoredFirst(context,same).orElseThrow();
        assertEquals(savedOriginal.saved.state(),compared.state());assertEquals(savedOriginal.saved.plan(),compared.plan());
        assertEquals(savedOriginal.saved.strategySource(),compared.strategySource());
        assertEquals(savedOriginal.saved.body(),compared.body());
        assertArrayEquals(savedOriginal.originalDriver,compared.material().savedDriver().encode());
        assertEquals(head,same.head().digest());
    }

    public static void assertOrdinaryRestoreUsesItsExistingBranch(ContinuityStorePort.Session same,
            RootCrossRunPlanning.Prepared actual,RootRuntimeContext context)throws IOException {
        var original=context.restorationOriginal(same);
        assertEquals(SavedCheckpointMaterial.Kind.ORDINARY,original.material().kind());
        assertTrue(actual.requireRestoredFirst(context,same).isEmpty());
    }

    /** Invoke on the actual restored-FIRST initialization proof, without treating its saved SEM as current. */
    public static void assertRestoredInitialization(ContinuityStorePort.Session same,RootCrossRunPlanning.Prepared actual,
            RootRuntimeContext context,RootApplicationAssembly.RestoredFirstEpisodeDomainProof proof,Observed savedOriginal)throws IOException {
        assertSame(savedOriginal.core,context.core());String head=same.head().digest();
        var read=actual.requireEpisodeFirst(context,same,proof);
        assertEquals(RootApplicationAssembly.EpisodeDomainInitializationProof.Kind.RESTORED_FIRST,proof.kind());
        assertEquals(savedOriginal.saved.material().witness(),proof.baselineMaterial().witness());
        assertEquals(savedOriginal.saved.material().pair(),proof.baselineMaterial().pair());
        assertEquals(savedOriginal.saved.material().sourceSemantic(),proof.savedSemantic());
        assertEquals(proof.afterSession().game(),proof.currentSemantic().frame().game());
        assertNotEquals(proof.savedSemantic().frame().game(),proof.currentSemantic().frame().game());
        assertArrayEquals(savedOriginal.originalDriver,proof.firstSavedDriver().encode());
        assertEquals(proof.currentSemantic().originalDriver().sha256(),
                org.xar.ck3.control.application.driver.DriverJson.sha256(proof.currentDriver().encode()));
        assertEquals(savedOriginal.saved.state(),read.state());assertEquals(savedOriginal.saved.plan(),read.plan());
        assertEquals(savedOriginal.saved.strategySource(),read.strategySource());assertEquals(head,same.head().digest());
    }
}
