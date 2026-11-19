package org.xar.ck3.control.application.checkpoint;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import static org.junit.jupiter.api.Assertions.*;

@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.saved.material168.inputs",matches=".+")
final class SavedConfirmationV2DataTest {
    record Fixture(ObjectNode current,ObjectNode legacy,CheckpointPair pair,SessionIdentity source,
            CheckpointPair legacyPair,SessionIdentity legacySource) { }
    static byte[] read(JsonNode ref)throws Exception {
        byte[] bytes=Files.readAllBytes(Path.of(ref.get("path").textValue()));
        assertEquals(ref.get("bytes").longValue(),bytes.length);
        assertEquals(ref.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return bytes;
    }
    static Fixture fixture()throws Exception {
        JsonNode inputs=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.saved.material168.inputs"))),1<<20);
        ObjectNode current=(ObjectNode)StrictJson.parse(read(inputs.get("current_event")),1<<20).get("details");
        ObjectNode legacy=(ObjectNode)StrictJson.parse(read(inputs.get("legacy_event")),1<<20).get("details");
        CheckpointPair pair=CheckpointPairCodec.decode(read(inputs.get("current_pair")));
        var legacyPair=CheckpointPairCodec.decode(read(inputs.get("legacy_pair")));
        return new Fixture(current,legacy,pair,OrdinaryCycleTransitions.sessionFromJson(current.get("session")),
                legacyPair,OrdinaryCycleTransitions.sessionFromJson(legacy.get("session")));
    }
    static java.util.Optional<SavedCheckpointMaterialEvidence> bind(ObjectNode value,CheckpointPair pair,SessionIdentity source) {
        var decoded=SavedAttachmentSourceStore.confirmedSourceDetails(ContinuityJson.canonical(value));
        return SavedAttachmentSourceStore.confirmedSourceMaterial(decoded,pair,source);
    }
    @Test void actualV2AndLegacyV1UseSeparateExactLanes()throws Exception {
        var f=fixture();assertEquals("java-ordinary-session/v2",f.current.get("source").textValue());
        assertEquals("java-ordinary-session/v1",f.legacy.get("source").textValue());
        var parsed=SavedAttachmentSourceStore.confirmedSourceDetails(ContinuityJson.canonical(f.current));
        assertEquals(f.current,parsed);
        var evidence=bind(f.current,f.pair,f.source).orElseThrow();
        assertEquals(SavedCheckpointMaterialEvidence.decode(f.current.get(SavedCheckpointMaterialEvidence.FIELD)),evidence);
        assertEquals(f.pair,evidence.pair());assertEquals(f.source,evidence.source());
        assertEquals(47,evidence.originalHeadSequence());
        assertTrue(bind(f.legacy,f.legacyPair,f.legacySource).isEmpty());
    }
    @Test void unknownLaneExtraMissingAndMisplacedMaterialAreRejected()throws Exception {
        var f=fixture();
        var missing=f.current.deepCopy();missing.remove(SavedCheckpointMaterialEvidence.FIELD);
        assertThrows(IllegalArgumentException.class,()->bind(missing,f.pair,f.source));
        var extra=f.current.deepCopy();extra.put("made_up_restore_ready",true);
        assertThrows(IllegalArgumentException.class,()->bind(extra,f.pair,f.source));
        var future=f.current.deepCopy();future.put("source","java-ordinary-session/v3");
        assertThrows(IllegalArgumentException.class,()->bind(future,f.pair,f.source));
        var oldWithMaterial=f.legacy.deepCopy();oldWithMaterial.set(SavedCheckpointMaterialEvidence.FIELD,f.current.get(SavedCheckpointMaterialEvidence.FIELD));
        assertThrows(IllegalArgumentException.class,()->bind(oldWithMaterial,f.pair,f.source));
        var nullMaterial=f.current.deepCopy();nullMaterial.putNull(SavedCheckpointMaterialEvidence.FIELD);
        assertThrows(IllegalArgumentException.class,()->bind(nullMaterial,f.pair,f.source));
        var boundary=f.current.deepCopy();boundary.put("boundary","BATCH_STARTED");
        assertThrows(IllegalArgumentException.class,()->bind(boundary,f.pair,f.source));
    }
    @Test void actualMaterialCannotCrossPairSessionOrItsClosedWitnessSchema()throws Exception {
        var f=fixture();var pair=(ObjectNode)StrictJson.parse(CheckpointPairCodec.encode(f.pair));
        pair.put("history_index",f.pair.historyIndex()+1);
        var crossedPair=CheckpointPairCodec.decode(ContinuityJson.canonical(pair));
        assertThrows(IllegalArgumentException.class,()->bind(f.current,crossedPair,f.source));
        var owner=OrdinaryCycleTransitions.sessionToJson(f.source);owner.put("session_id",f.source.sessionId()+"-crossed");
        var crossedSource=OrdinaryCycleTransitions.sessionFromJson(owner);
        assertThrows(IllegalArgumentException.class,()->bind(f.current,f.pair,crossedSource));
        var schema=f.current.deepCopy();((ObjectNode)schema.get(SavedCheckpointMaterialEvidence.FIELD)).put("schema","unqualified-material");
        assertThrows(IllegalArgumentException.class,()->bind(schema,f.pair,f.source));
        var witness=f.current.deepCopy();((ObjectNode)witness.get(SavedCheckpointMaterialEvidence.FIELD).get("material_witness")).put("restoration_permit",true);
        assertThrows(IllegalArgumentException.class,()->bind(witness,f.pair,f.source));
    }
}
