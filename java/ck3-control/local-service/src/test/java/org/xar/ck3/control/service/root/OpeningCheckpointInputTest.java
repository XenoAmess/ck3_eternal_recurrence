package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterial;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;

/** Pure boundary regression over the actual producer/consumer contract; these values grant no SAVE or restoration authority. */
final class OpeningCheckpointInputTest {
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static ExactRef ref(String name) { return new ExactRef(Path.of("synthetic-opening-boundary",name).toAbsolutePath().toString(),17,"a".repeat(64)); }
    private static ObservationIdentity frame(String episode, long actor, int date) {
        return new ObservationIdentity("opening-boundary-fixture",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.TEN,BigInteger.valueOf(date)),
                        "synthetic-native-10",BigInteger.TEN,episode),1);
    }
    private static SemanticEvidence semantic(ObservationIdentity observed) {
        return new SemanticEvidence(observed,ref("semantic"),ref("native"),ref("stamp"),ref("driver-original"),AT);
    }
    private static CheckpointPair.FileWitness witness(String name, String id) {
        return new CheckpointPair.FileWitness(ref(name),new FileStatIdentity(BigInteger.valueOf(17),id,"1792800000000000001"));
    }
    private static OpeningCheckpointInput input(Optional<ExactRef> basis) {
        return input(SavedCheckpointMaterial.Kind.ORDINARY,basis);
    }
    private static OpeningCheckpointInput input(SavedCheckpointMaterial.Kind kind,Optional<ExactRef> basis) {
        var saved=frame("episode-1",29829,1000);
        var pair=new CheckpointPair(witness("save","18446744073709551613"),witness("driver","18446744073709551614"),saved,
                "synthetic-lineage",1,"synthetic-save-action",ref("native-ack"),AT);
        return new OpeningCheckpointInput(ref("planning-request"),semantic(saved),pair,ref("save-receipt"),kind,
                witness("saved-material","18446744073709551615"),basis);
    }
    @Test void producerRoundTripsThroughTheConsumerWithExactOriginalFileIdentity() {
        for(var kind:SavedCheckpointMaterial.Kind.values())
        for(var basis:java.util.List.of(Optional.<ExactRef>empty(),Optional.of(ref("private-restoration-basis")))) {
            var original=input(kind,basis);byte[] wire=StrictJson.canonical(original.toJson());
            var decoded=OpeningCheckpointInput.fromJson(StrictJson.parse(wire));
            assertEquals(original,decoded);assertArrayEquals(wire,StrictJson.canonical(decoded.toJson()));
            assertEquals("18446744073709551615",decoded.savedMaterial().identity().fileId());
            assertEquals("133700000000000001",decoded.semantic().frame().game().creationFiletime().value().toString());
            assertEquals(original.savedMaterial(),CheckpointPairCodec.fileWitnessFromJson(decoded.toJson().get("saved_material")));
            assertEquals(kind,decoded.materialKind());
        }
    }
    @Test void legacyReferenceMissingIdentityAndNumericFileIdNeverBecomeAnOriginalWitness() {
        var original=input(Optional.empty());var legacy=original.toJson();legacy.set("saved_material",original.savedMaterial().reference().toJson());
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(legacy));
        var missing=original.toJson();((ObjectNode)missing.get("saved_material")).remove("identity");
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(missing));
        for(var value:java.util.List.of(StrictJson.parse("true".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("18446744073709551615".getBytes(StandardCharsets.UTF_8)),StrictJson.parse("18446744073709551615.0".getBytes(StandardCharsets.UTF_8)))) {
            var wrong=original.toJson();((ObjectNode)wrong.get("saved_material").get("identity")).set("file_id",value);
            assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(wrong));
        }
    }
    @Test void absentNullAndEmptyDoNotAliasOneAnotherAtTheRestorationBoundary() {
        var original=input(Optional.empty());assertTrue(OpeningCheckpointInput.fromJson(original.toJson()).restorationBasis().isEmpty());
        var missing=original.toJson();missing.remove("restoration_basis");
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(missing));
        var empty=original.toJson();empty.set("restoration_basis",StrictJson.object());
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(empty));
        var extra=original.toJson();extra.put("file_id","18446744073709551615");
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(extra));
    }
    @Test void checkpointSourceMismatchFailsBeforeAnySavedMaterialPathCanBeObserved() {
        var original=input(Optional.empty());
        for(var current:java.util.List.of(frame("other-episode",29829,1000),frame("episode-1",29830,1000),frame("episode-1",29829,999)))
            assertThrows(IllegalArgumentException.class,()->new OpeningCheckpointInput(original.request(),semantic(current),original.pair(),
                    original.saveReceipt(),original.materialKind(),original.savedMaterial(),original.restorationBasis()));
        var changed=original.toJson();((ObjectNode)changed.get("saved_material").get("identity")).put("bytes",18);
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(changed));
    }
    @Test void materialKindIsMandatoryAndCannotFallBackToAnOrdinaryStore() {
        var original=input(SavedCheckpointMaterial.Kind.FIRST_BASELINE,Optional.of(ref("private-restoration-basis")));
        var missing=original.toJson();missing.remove("saved_material_kind");
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(missing));
        var nulled=original.toJson();nulled.putNull("saved_material_kind");
        assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(nulled));
        for(var token:java.util.List.of("true","1","1.0","\"FIRST\"","\"UNKNOWN\"")) {
            var wrong=original.toJson();wrong.set("saved_material_kind",StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->OpeningCheckpointInput.fromJson(wrong));
        }
        assertEquals(SavedCheckpointMaterial.Kind.FIRST_BASELINE,OpeningCheckpointInput.fromJson(original.toJson()).materialKind());
    }
}
