package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts.FileIdentity;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.service.root.RootApplicationAssembly.EpisodeDomainInitializationProof.Kind;
import static org.junit.jupiter.api.Assertions.*;

/** Actual producer/consumer data and reducer boundaries; no Core proof or qualified native packet is fabricated. */
final class GovernanceDomainInitializationInputTest {
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static ExactRef ref(String name) {return new ExactRef(Path.of("synthetic-governance-dual-origin",name).toAbsolutePath().toString(),17,"a".repeat(64));}
    private static final G2Source SOURCE=new G2Source("governance-origin-fixture",AT.toString(),"1.20.0.4",ref("source"));
    private static ObservationIdentity frame(long pid,long actor,long revision,String episode) {
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(pid,new PythonOnlyUInt64(new BigInteger("133700000000000001").add(BigInteger.valueOf(pid)))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(revision),BigInteger.valueOf(1000)),
                        "synthetic-native-"+revision,BigInteger.valueOf(revision),episode),1);
    }
    private static SemanticEvidence semantic(ObservationIdentity value,String name) {return new SemanticEvidence(value,ref(name+"-semantic"),ref(name+"-native"),ref(name+"-stamp"),ref(name+"-driver"),AT);}
    private static SessionIdentity owner(ObservationIdentity value,String name) {return new SessionIdentity(value.machineId(),value.game(),name);}
    private static CheckpointPair.FileWitness witness(String name) {return new CheckpointPair.FileWitness(ref(name),new FileStatIdentity(BigInteger.valueOf(17),"18446744073709551615","1792800000000000001"));}
    private static DomainBodies.BodyRef body(String name) {return new DomainBodies.BodyRef(DomainBodies.Slot.OPENING_GATE,"synthetic-opening/v1",ref(name),new FileIdentity("1","18446744073709551614","133700000000000001",AT.toString(),17),List.of(SOURCE.sourceRef()));}
    private static GovernanceDomainInitializationInput input(Kind kind) {
        var saved=frame(124,30000,900,"new-episode");var current=kind==Kind.NEXT?saved:frame(125,30000,7,"new-episode");
        var savedSemantic=semantic(saved,"saved");var currentSemantic=kind==Kind.NEXT?savedSemantic:semantic(current,"current");
        var read=frame(current.game().pid(),30000,kind==Kind.NEXT?901:8,"new-episode");
        var pair=new CheckpointPair(witness("save"),witness("driver"),frame(124,30000,899,"new-episode"),"synthetic-lineage",1,"synthetic-save-action",ref("native-ack"),AT);
        return new GovernanceDomainInitializationInput(kind,body("old-domain"),body("old-domain"),witness("material"),pair,owner(saved,"saved-session"),savedSemantic,
                currentSemantic,ref("hosted"),semantic(read,"read"),ref("source-proof"),owner(frame(123,29829,800,"old-episode"),"old-session"),
                owner(current,kind==Kind.NEXT?"saved-session":"restored-session"),SOURCE,kind==Kind.NEXT?20:45,"b".repeat(64));
    }
    private static ObjectNode json(GovernanceDomainInitializationInput input) {return (ObjectNode)StrictJson.parse(input.encode());}
    @Test void bothActualProducerKindsRoundTripWithoutRelabellingTheSavedOriginal() {
        for(var kind:Kind.values()) {
            var original=input(kind);var decoded=GovernanceDomainInitializationInput.decode(original.encode());
            assertEquals(original,decoded);assertArrayEquals(original.encode(),decoded.encode());
            assertEquals("18446744073709551615",decoded.material().identity().fileId());
            assertEquals(original.savedSemantic(),decoded.savedSemantic());assertEquals(original.currentSemantic(),decoded.currentSemantic());
            assertEquals(kind==Kind.NEXT,decoded.savedSession().equals(decoded.after()));
        }
    }
    @Test void restoredNativeRevisionIsComparedOnlyWithinTheCurrentPhysicalGame() {
        var original=input(Kind.RESTORED_FIRST);assertEquals(BigInteger.valueOf(900),original.savedSemantic().frame().frame().identity().nativeRevision());
        assertEquals(BigInteger.valueOf(8),GovernanceDomainInitializationInput.decode(original.encode()).readSemantic().frame().frame().identity().nativeRevision());
        var stale=json(original);stale.set("read_semantic",OpeningCheckpointInput.semanticToJson(semantic(frame(125,30000,6,"new-episode"),"stale")));
        assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(stale)));
        var oldPhysical=json(original);oldPhysical.set("read_semantic",OpeningCheckpointInput.semanticToJson(original.savedSemantic()));
        assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(oldPhysical)));
    }
    @Test void kindOwnersAndInitializationAnchorAreMandatoryAndStrictlyTyped() {
        var original=input(Kind.RESTORED_FIRST);
        for(var name:List.of("kind","saved_session","saved_semantic","current_semantic","initialization_sequence","initialization_digest","original")) {
            var missing=json(original);missing.remove(name);assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(missing)));
            var nulled=json(original);nulled.putNull(name);assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(nulled)));
        }
        var absentSourceProof=json(original);absentSourceProof.remove("source_proof");
        assertEquals(Optional.empty(),GovernanceDomainInitializationInput.decode(StrictJson.canonical(absentSourceProof)).sourceProof());
        var nullSourceProof=json(original);nullSourceProof.putNull("source_proof");
        var absent=GovernanceDomainInitializationInput.decode(StrictJson.canonical(nullSourceProof));
        assertEquals(Optional.empty(),absent.sourceProof());assertTrue(json(absent).get("source_proof").isNull());
        assertEquals(absent,GovernanceDomainInitializationInput.decode(absent.encode()));
        assertEquals(original.savedSemantic(),absent.savedSemantic());assertEquals(original.readSemantic(),absent.readSemantic());
        assertEquals(original.sourceProof(),GovernanceDomainInitializationInput.decode(original.encode()).sourceProof());
        for(var token:List.of("true","1.0","[]","{}")) {
            var malformedSourceProof=json(original);malformedSourceProof.set("source_proof",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(malformedSourceProof)));
        }
        for(var token:List.of("true","1.0","\"45\"")) {
            var wrong=json(original);wrong.set("initialization_sequence",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(wrong)));
        }
        var wrongKind=json(original);wrongKind.put("kind","NEXT");assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(wrongKind)));
        var changed=json(original);((ObjectNode)changed.get("material_witness").get("identity")).put("file_id",184467440737095516L);
        assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(changed)));
    }
    @Test void currentActorAndEpisodeCannotBeInheritedFromAnotherSavedBody() {
        var original=input(Kind.RESTORED_FIRST);
        for(var value:List.of(frame(125,30001,7,"new-episode"),frame(125,30000,7,"other-episode"))) {
            var wrong=json(original);wrong.set("current_semantic",OpeningCheckpointInput.semanticToJson(semantic(value,"wrong")));
            assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(wrong)));
        }
        var extra=json(original);extra.put("ordinary_ready",true);
        assertThrows(IllegalArgumentException.class,()->GovernanceDomainInitializationInput.decode(StrictJson.canonical(extra)));
    }
    @Test void registeredOpeningRebindRetainsItsBaselineAndRejectsUnknownActions() {
        var base=input(Kind.RESTORED_FIRST);var wire=json(base);wire.set("previous",body("prior-next-body").toJson());
        var input=GovernanceDomainInitializationInput.decode(StrictJson.canonical(wire));
        var refs=List.of(input.original().payload(),input.material().reference(),input.pair().save().reference(),input.pair().driver().reference());
        var prior=new GovernanceOpeningDocument.Document(input.savedSemantic().frame(),SOURCE,input.savedSession().sessionId(),OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),refs);
        byte[] original=StrictJson.canonical(StrictJson.object().put("retained","original-data"));
        byte[] output=GovernanceNextInitialization.nextOpening(GovernanceOpeningDocument.encode(new GovernanceOpeningDocument.Document(frame(123,29829,800,"old-episode"),SOURCE,"old-session",OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),List.of(ref("old-evidence")))),
                input.readSemantic().frame(),SOURCE,input.after().sessionId(),refs);
        GovernanceNextInitialization.requireRegisteredContinuation(input,original,GovernanceOpeningDocument.encode(prior),output);
        GovernanceNextInitialization.requireRegisteredContinuation(input,original,output,output);
        var priorRestore=new GovernanceOpeningDocument.Document(frame(126,30000,3,"new-episode"),SOURCE,"prior-restored-session",OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),refs);
        GovernanceNextInitialization.requireRegisteredContinuation(input,original,GovernanceOpeningDocument.encode(priorRestore),output);
        var changedCurrent=new GovernanceOpeningDocument.Document(input.currentSemantic().frame(),SOURCE,input.after().sessionId(),OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),refs);
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireRegisteredContinuation(input,original,GovernanceOpeningDocument.encode(changedCurrent),output));
        var pending=new GovernanceOpeningDocument.Document(input.savedSemantic().frame(),SOURCE,input.savedSession().sessionId(),OpeningStage.AWAIT_RECEIPT,Optional.empty(),Optional.empty(),refs,Optional.of(ref("prepared-unknown")),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireRegisteredContinuation(input,original,GovernanceOpeningDocument.encode(pending),output));
        var otherBaseline=new GovernanceOpeningDocument.Document(input.savedSemantic().frame(),SOURCE,input.savedSession().sessionId(),OpeningStage.AWAIT_SUBMIT,Optional.empty(),Optional.empty(),List.of(ref("unrelated-baseline")));
        assertThrows(IllegalArgumentException.class,()->GovernanceNextInitialization.requireRegisteredContinuation(input,original,GovernanceOpeningDocument.encode(otherBaseline),output));
    }
}
