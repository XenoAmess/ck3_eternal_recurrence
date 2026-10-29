package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Explicit software facts exercise the strict persisted contract; they never mint Root's private domain proof. */
final class SwayNextEpisodeImportTest {
    @Test void distinctEpisodeSourceRetainsWholePredecessorAndBothActualPlayerDocumentsInCanonicalRoundtrip() {
        var basis=basis();var encoded=SwayNextEpisodeImport.encode(basis);var restored=SwayNextEpisodeImport.decode(encoded);
        assertArrayEquals(encoded,SwayNextEpisodeImport.encode(restored));assertEquals(basis,restored);
        assertTrue(restored.evidence().contains(basis.predecessor().payload()));assertTrue(restored.evidence().contains(basis.predecessorDriver()));
        assertTrue(restored.evidence().contains(basis.firstSavedDriver()));assertTrue(restored.evidence().contains(basis.canonicalParent()));
        assertTrue(restored.evidence().containsAll(basis.savedSemantic().references()));
        assertNotEquals(restored.beforeSession().game(),restored.afterSession().game());
        assertNotEquals(restored.baseline().baseline().begin().begin().before().actorId(),restored.baseline().baseline().savedIdentity().actorId());
        var restartedOriginalActor=basis(50331649);assertEquals(restartedOriginalActor.baseline().baseline().begin().begin().before().actorId(),restartedOriginalActor.baseline().baseline().savedIdentity().actorId());
        assertArrayEquals(SwayNextEpisodeImport.encode(restartedOriginalActor),SwayNextEpisodeImport.encode(SwayNextEpisodeImport.decode(SwayNextEpisodeImport.encode(restartedOriginalActor))),"a real new Game/episode may restart the same seed character");
    }
    @Test void missingNullWrongNativeIdentityAndRoundedGenerationFailBeforeAnyDomainPreview() {
        for(String defect:List.of("missing","null","float-pid","bool-filetime","unknown-field","wrong-schema","replay","native-ready")) {
            var row=(ObjectNode)StrictJson.parse(SwayNextEpisodeImport.encode(basis()));
            switch(defect) {
                case "missing"->row.remove("predecessor_driver");
                case "null"->row.putNull("canonical_parent");
                case "float-pid"->((ObjectNode)row.at("/after_session/game")).put("pid",80.0);
                case "bool-filetime"->((ObjectNode)row.at("/after_session/game")).put("creation_filetime",true);
                case "unknown-field"->row.put("ready",true);
                case "wrong-schema"->row.put("schema","unversioned-empty-seed");
                case "replay"->row.put("old_request_replayed",true);
                case "native-ready"->row.put("current_native_sway_observation","ready");
                default->throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class,()->SwayNextEpisodeImport.decode(StrictJson.canonical(row)),defect);
        }
    }
    @Test void constructorRejectsSamePhysicalGameAndChangedArchivedBaselineBytes() {
        var original=basis();
        assertThrows(IllegalArgumentException.class,()->new SwayNextEpisodeImport.Basis(original.predecessor(),original.beforeSession(),original.beforeSession(),original.predecessorDriver(),original.firstSavedDriver(),original.originalBaselineMaterial(),original.archivedBaselineMaterial(),original.baseline(),original.savedSemantic(),original.source(),original.canonicalParent(),original.lifecycleProof()));
        assertThrows(IllegalArgumentException.class,()->new SwayNextEpisodeImport.Basis(original.predecessor(),original.beforeSession(),original.afterSession(),original.predecessorDriver(),original.firstSavedDriver(),original.originalBaselineMaterial(),new ExactRef("D:/software/changed",1,"c".repeat(64)),original.baseline(),original.savedSemantic(),original.source(),original.canonicalParent(),original.lifecycleProof()));
    }
    @Test void currentNextOriginRetainsExplicitLegacyV1WithoutRelabelingItsSavedFrame() {
        var legacy=basis();var legacyBytes=SwayNextEpisodeImport.encode(legacy);
        assertEquals(SwayNextEpisodeImport.LEGACY_SCHEMA,StrictJson.text(StrictJson.parse(legacyBytes).get("schema")));
        assertEquals(SwayNextEpisodeImport.Format.LEGACY_NEXT,SwayNextEpisodeImport.decode(legacyBytes).format());
        var current=upgraded(false);var encoded=SwayNextEpisodeImport.encode(current);
        assertEquals(SwayNextEpisodeImport.SCHEMA,StrictJson.text(StrictJson.parse(encoded).get("schema")));
        assertEquals(current.savedSession(),current.afterSession());assertNotEquals(current.savedSemantic().semantic(),current.currentSemantic().semantic());
        assertEquals(current,SwayNextEpisodeImport.decode(encoded));assertArrayEquals(legacyBytes,SwayNextEpisodeImport.encode(SwayNextEpisodeImport.decode(legacyBytes)));
    }
    @Test void firstRestoreOriginKeepsOriginalBaselineAndDistinctActualCurrentPhysicalFrameInRoundtrip() {
        var original=upgraded(true);var encoded=SwayNextEpisodeImport.encode(original);var actual=SwayNextEpisodeImport.decode(encoded);
        assertArrayEquals(encoded,SwayNextEpisodeImport.encode(actual));assertEquals(original,actual);
        assertEquals(SwayNextEpisodeImport.Kind.RESTORED_FIRST,actual.kind());assertEquals(actual.savedSession().game(),actual.savedSemantic().frame().game());
        assertEquals(actual.afterSession().game(),actual.currentSemantic().frame().game());assertNotEquals(actual.savedSession().game(),actual.afterSession().game());
        assertTrue(actual.evidence().contains(actual.firstSavedDriver()));assertTrue(actual.evidence().contains(actual.currentDriver()));
        assertTrue(actual.evidence().containsAll(actual.savedSemantic().references()));assertTrue(actual.evidence().containsAll(actual.currentSemantic().references()));
        assertEquals(7,actual.initializationHeadSequence());assertEquals(3,actual.baseline().sequence());assertNotEquals(actual.initializationHeadDigest(),actual.baseline().headDigest());
    }
    @Test void restoredOriginRejectsBorrowedSavedOwnerMissingCurrentEvidenceAndInvalidInitializationAnchor() {
        for(String defect:List.of("saved-is-current","saved-sem-is-current","missing-current","null-current","wrong-kind","number-anchor","float-anchor","zero-anchor","leading-zero-anchor","borrowed-baseline-anchor","changed-saved-owner")) {
            var row=(ObjectNode)StrictJson.parse(SwayNextEpisodeImport.encode(upgraded(true)));
            switch(defect) {
                case "saved-is-current"->row.set("after_session",row.get("saved_session").deepCopy());
                case "saved-sem-is-current"->row.set("current_semantic",row.get("saved_semantic").deepCopy());
                case "missing-current"->row.remove("current_driver");
                case "null-current"->row.putNull("current_semantic");
                case "wrong-kind"->row.put("initialization_kind","RESTORE");
                case "number-anchor"->row.put("initialization_head_sequence",7);
                case "float-anchor"->row.put("initialization_head_sequence",7.0);
                case "zero-anchor"->row.put("initialization_head_sequence","0");
                case "leading-zero-anchor"->row.put("initialization_head_sequence","07");
                case "borrowed-baseline-anchor"->row.put("initialization_head_sequence","3");
                case "changed-saved-owner"->((ObjectNode)row.at("/saved_session/game")).put("pid",81);
                default->throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class,()->SwayNextEpisodeImport.decode(StrictJson.canonical(row)),defect);
        }
    }
    private static SwayNextEpisodeImport.Basis upgraded(boolean restored) {
        var old=basis();var saved=old.afterSession();var game=restored?new GameGeneration(91,new PythonOnlyUInt64(new BigInteger("134370000000000091"))):saved.game();
        var currentOwner=restored?new SessionPorts.SessionIdentity(saved.machineId(),game,"current-restored-session"):saved;
        var oldFrame=old.savedSemantic().frame();var frame=new ObservationIdentity(oldFrame.machineId(),game,oldFrame.frame(),oldFrame.observationVersion());
        var current=new SessionPorts.SemanticEvidence(frame,ref("current-semantic"),ref("current-native"),ref("current-stamp"),ref("current-driver"),old.savedSemantic().observedAt());
        return new SwayNextEpisodeImport.Basis(SwayNextEpisodeImport.Format.CURRENT,restored?SwayNextEpisodeImport.Kind.RESTORED_FIRST:SwayNextEpisodeImport.Kind.NEXT,old.predecessor(),old.beforeSession(),saved,currentOwner,
                old.predecessorDriver(),old.firstSavedDriver(),ref("current-driver"),old.originalBaselineMaterial(),old.archivedBaselineMaterial(),old.baseline(),old.savedSemantic(),current,old.source(),old.canonicalParent(),old.lifecycleProof(),restored?7:old.baseline().sequence(),restored?"e".repeat(64):old.baseline().headDigest());
    }
    private static SwayNextEpisodeImport.Basis basis() {return basis(50331699);}
    private static SwayNextEpisodeImport.Basis basis(long nextActor) {
        var oldGame=new GameGeneration(73,new PythonOnlyUInt64(new BigInteger("134370000000000073")));var newGame=new GameGeneration(80,new PythonOnlyUInt64(new BigInteger("134370000000000080")));
        var old=new EpisodeWindow.Identity("test-machine",oldGame,"before-session","before-episode",1,50331649,53220000);
        var next=new EpisodeWindow.Identity("test-machine",newGame,"after-session","after-episode",2,nextActor,53219000);
        var begin=new EpisodeWindow.Begin("software-next",old,next,1,2,"next-parent",1,"a".repeat(64),ref("lifecycle-event"),ref("adopted-driver"),List.of(ref("next-proof")));
        var committedBegin=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),"b".repeat(64),pin("begin-event"));
        var first=new EpisodeWindow.Baseline(committedBegin,"save-next",ref("pair"),ref("pair").sha256(),ref("save-receipt"),"c".repeat(64),next);
        var baseline=new EpisodeWindow.CommittedBaseline(first,3,first.request().identity(),"d".repeat(64),pin("baseline-event"));
        var nativeFrame=new JointBudgetSelector.Frame(BigInteger.valueOf(next.actorId()),BigInteger.valueOf(7),BigInteger.valueOf(next.dateRaw()));
        var before=new ObservationIdentity("test-machine",newGame,new JointBudgetSelector.ProposalFrame(nativeFrame,"saved-snapshot",BigInteger.valueOf(8),next.episodeRunId()),1);
        var semantic=new SessionPorts.SemanticEvidence(before,ref("semantic"),ref("native-packet"),ref("stamp"),ref("original-driver"),Instant.parse("2026-10-24T00:00:00Z"));
        var prior=new DomainBodies.BodyRef(DomainBodies.Slot.SWAY,SwayFormalState.SCHEMA,ref("old-full-sway-body"),identity(),List.of(ref("producer")));
        return new SwayNextEpisodeImport.Basis(prior,new SessionPorts.SessionIdentity("test-machine",oldGame,"before-session"),new SessionPorts.SessionIdentity("test-machine",newGame,"after-session"),ref("old-driver"),ref("first-saved-driver"),ref("original-baseline"),ref("archived-baseline"),baseline,semantic,new G2Source("test-machine","2026-10-24T00:00:00Z",SwayNativeWire.BUILD,ref("source")),ref("canonical-parent"),ref("lifecycle-proof"));
    }
    private static ExactRef ref(String name){return new ExactRef("D:/software/"+name,1,"a".repeat(64));}
    private static WriterContracts.FileIdentity identity(){return new WriterContracts.FileIdentity("1","9007199254740993","134370000000000001","2026-10-24T00:00:00Z",1);}
    private static WriterContracts.Pin pin(String name){return new WriterContracts.Pin(ref(name),identity());}
}
