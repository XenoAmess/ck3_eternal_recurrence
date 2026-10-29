package org.xar.ck3.control.service.sway;

import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.planning.sway.SwayFormalCodec;
import org.xar.ck3.control.application.planning.sway.SwayNextEpisodeImport;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.service.root.RootApplicationAssembly;

/** Actual Root fixture consumes its privately minted proof here. This helper cannot construct a proof or a Game. */
public final class SwayNextEpisodeRootAssertions {
    private SwayNextEpisodeRootAssertions() { }
    public static DomainBodies.BodyRef initializeActualAndAssert(ContinuityStorePort.Session same,
            RootApplicationAssembly.EpisodeDomainInitializationProof actualPrivateProof,SwayRuntimeInstaller actualInstalledSway)throws Exception {
        var before=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.SWAY));
        var head=same.head();var originalActions=head.state().toJson().get(ContinuityActionJournal.STATE_FIELD);
        var actual=actualInstalledSway.initializeNext(same,actualPrivateProof);
        var after=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.SWAY));assertEquals(actual,after.reference());
        var ledger=SwayFormalCodec.decode(after.canonicalBody());assertEquals(actualPrivateProof.currentDriver().session().episodeRunId(),ledger.episodeRunId());
        var origin=same.capturePin(ledger.originalMigrationInput(),SwayFormalCodec.MAX);
        var basis=SwayNextEpisodeImport.decode(same.readPinned(origin,SwayFormalCodec.MAX));same.verifyPin(origin);
        assertEquals(before.reference(),basis.predecessor());assertEquals(actualPrivateProof.oldDomain(DomainBodies.Slot.SWAY),basis.predecessor());assertEquals(actualPrivateProof.beforeSession(),basis.beforeSession());assertEquals(actualPrivateProof.afterSession(),basis.afterSession());
        assertEquals(actualPrivateProof.baselineMaterial().baseline(),basis.baseline());assertEquals(actualPrivateProof.baselineMaterial().session(),basis.savedSession());
        assertEquals(actualPrivateProof.savedSemantic(),basis.savedSemantic());assertEquals(actualPrivateProof.currentSemantic(),basis.currentSemantic());
        assertEquals(actualPrivateProof.kind().name(),basis.kind().name());assertEquals(actualPrivateProof.initializationHeadSequence(),basis.initializationHeadSequence());assertEquals(actualPrivateProof.initializationHeadDigest(),basis.initializationHeadDigest());
        if(basis.kind()==SwayNextEpisodeImport.Kind.RESTORED_FIRST){assertNotEquals(basis.savedSession().game(),basis.afterSession().game());assertNotEquals(basis.savedSemantic().frame().game(),basis.currentSemantic().frame().game());}
        else assertEquals(basis.savedSession(),basis.afterSession());
        var retained=same.capturePin(before.reference().payload(),SwayFormalCodec.MAX);assertArrayEquals(before.canonicalBody(),same.readPinned(retained,SwayFormalCodec.MAX));same.verifyPin(retained);
        assertEquals(originalActions,same.head().state().toJson().get(ContinuityActionJournal.STATE_FIELD),"NEXT Sway must preserve every original action and UNKNOWN exactly");
        var oldFields=head.state().toJson();var newFields=same.head().state().toJson();
        oldFields.remove(java.util.List.of(DomainBodies.FIELD,"sequence","last_event_identity"));newFields.remove(java.util.List.of(DomainBodies.FIELD,"sequence","last_event_identity"));
        assertTrue(ContinuityJson.same(oldFields,newFields),"Sway initialization can only publish its domain, never mutate another canonical field");
        String published=same.head().digest();assertEquals(actual,actualInstalledSway.initializeNext(same,actualPrivateProof));assertEquals(published,same.head().digest(),"same actual proof is idempotent without a second domain import");
        assertFalse(ledger.originalMigrationInput().equals(SwayFormalCodec.decode(before.canonicalBody()).originalMigrationInput()),"new episode needs the nonempty exact next-origin rather than an old migration input or empty seed");
        return actual;
    }
}
