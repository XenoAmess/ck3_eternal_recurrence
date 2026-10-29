package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SameGameTransportContinuity;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.application.session.SessionPorts.PendingSuccessorUi;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Real canonical software SAVE establishes a negative boundary; genuine NS/M3 inputs are required for the positive assertions. */
public final class SameGameTransportContinuityTest {
    @TempDir Path temporary;

    @Test void actualCanonicalSaveCannotReplaceMissingInstalledTransportCustodyOrRewriteItsSession()throws Exception {
        try(var f=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("no-actual-transport-custody"),false)) {
            var saved=assertInstanceOf(CheckpointResult.Confirmed.class,f.service.checkpoint(f.request));
            var freshOwner=new SessionIdentity(f.owner.machineId(),f.owner.game(),f.owner.sessionId()+"-fresh");
            byte[] ledger=f.actual.ledgerBytes();int writes=f.actual.nativeActionWrites(),reads=f.actual.nativeReadWrites();
            f.actual.writer.locked(same->{
                assertThrows(IOException.class,()->f.batch.rebindTransport(same,freshOwner,saved.action().command(),Instant.now().plusSeconds(5)));
                assertThrows(IllegalArgumentException.class,()->f.batch.currentSavedFrontier(same,freshOwner,f.proof));return null;
            });
            assertArrayEquals(ledger,f.actual.ledgerBytes());assertEquals(writes,f.actual.nativeActionWrites());assertEquals(reads,f.actual.nativeReadWrites());
            assertEquals(f.owner.sessionId(),saved.action().command().sessionId());
        }
    }

    /** Invoked by a genuine supplied NS adapter fixture, never an Evidence/Scope factory or a passing substitute for one. */
    public static void requireActualEvidenceRoundtrip(OutcomeArchive archive,SameGameTransportContinuity.Evidence actual) {
        ObjectNode encoded=actual.toJson(archive);
        var round=SameGameTransportContinuity.fromJson(encoded,archive);
        assertEquals(actual,round);assertEquals(encoded,round.toJson(archive));
        assertArrayEquals(ActionCodec.encodeCommand(actual.canonicalParent().command()),ActionCodec.encodeCommand(round.canonicalParent().command()));
        assertEquals(actual.references(archive),round.references(archive));
        ObjectNode missing=encoded.deepCopy();missing.remove("private_proof");
        assertThrows(IllegalArgumentException.class,()->SameGameTransportContinuity.fromJson(missing,archive));
        ObjectNode nil=encoded.deepCopy();nil.putNull("canonical_metadata");
        assertThrows(IllegalArgumentException.class,()->SameGameTransportContinuity.fromJson(nil,archive));
        for(String invalid:List.of("null","[]","{}","true","[null]")) {
            ObjectNode incomplete=encoded.deepCopy();incomplete.set("private_materials",StrictJson.parse(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->SameGameTransportContinuity.fromJson(incomplete,archive));
        }
        ObjectNode old=encoded.deepCopy();old.put("schema","xar.java-same-game-transport-evidence/v1");old.remove("private_materials");
        assertThrows(IllegalArgumentException.class,()->SameGameTransportContinuity.fromJson(old,archive));
        for(String invalid:List.of("true","1.0","\"1\"","null")) {
            ObjectNode wrong=encoded.deepCopy();wrong.set("canonical_sequence",StrictJson.parse(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->SameGameTransportContinuity.fromJson(wrong,archive));
        }
    }

    /** Genuine canonical transport rebind is historical zero-credit knowledge; no helper creates private custody. */
    public static void requireActualRebound(ContinuityBatchJournal journal,ContinuityStorePort.Session same,
            ContinuityBatchJournal.ReboundTransport actual)throws IOException {
        String head=same.head().digest();journal.requireHistoricalTransport(same,actual);
        assertEquals(0,actual.newCompletedCycleCredit());assertEquals(0,actual.newSavedDayCredit());
        assertEquals(actual.beforeOwner().machineId(),actual.owner().machineId());
        assertEquals(actual.beforeOwner().game(),actual.owner().game());
        assertEquals(head,same.head().digest());
        var frontier=journal.currentSavedFrontier(same,actual.owner(),actual.proof());
        assertEquals(actual.checkpointRequired(),frontier.checkpointRequired());assertEquals(actual.savedFrontier(),frontier.pair());
        assertEquals(head,same.head().digest());
    }

    /** The actual new Controller and current NS token must be supplied by their production construction path. */
    public static void requireActualPendingOwner(SessionController controller,ContinuityBatchJournal journal,
            ContinuityStorePort.Session same,PendingSuccessorUi current,ContinuityBatchJournal.ReboundTransport actual)throws IOException {
        String head=same.head().digest();journal.requireHistoricalTransport(same,actual);
        current.requireOwner(actual.owner(),actual);
        assertArrayEquals(ActionCodec.encodeCommand(actual.parent()),ActionCodec.encodeCommand(current.token().originalParent()));
        controller.adoptTransportRebound(same,actual);
        assertEquals(head,same.head().digest());
        assertEquals(0,actual.newCompletedCycleCredit());assertEquals(0,actual.newSavedDayCredit());
    }
}
