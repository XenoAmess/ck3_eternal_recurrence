package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;

public class SavedCheckpointMaterialEvidenceTest {
    private static final Instant FIXED_TIME = Instant.ofEpochSecond(1700000000);

    private static ProposalLifecycle.ObservationIdentity frame() {
        return new ProposalLifecycle.ObservationIdentity("test-machine-1", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(240)), "native:1", BigInteger.ONE, "episode-1"), 1);
    }

    private static CheckpointPair pair() {
        var save = new FileWitness(new ExactRef(Path.of("save.ck3").toAbsolutePath().toString(), 10, "a".repeat(64)), new FileStatIdentity(BigInteger.valueOf(10), "100", "1000"));
        var driver = new FileWitness(new ExactRef(Path.of("driver.json").toAbsolutePath().toString(), 20, "b".repeat(64)), new FileStatIdentity(BigInteger.valueOf(20), "200", "2000"));
        var ack = new ExactRef(Path.of("ack.json").toAbsolutePath().toString(), 5, "c".repeat(64));
        return new CheckpointPair(save, driver, frame(), "lineage-1", 1, "save-action-1", ack, FIXED_TIME);
    }

    private static SessionIdentity source() {
        return new SessionIdentity("test-machine-1", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))), "session-1");
    }

    private static FileWitness material() {
        return new FileWitness(new ExactRef(Path.of("material.json").toAbsolutePath().toString(), 30, "d".repeat(64)), new FileStatIdentity(BigInteger.valueOf(30), "9007199254740993", "13400000000000000100"));
    }

    @Test void roundTripPreservesDecimalIdentityAndDigests() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        assertEquals(SavedCheckpointMaterialEvidence.SCHEMA, StrictJson.text(json.get("schema")));
        assertEquals("100", json.get("original_head_sequence").asText());
        assertEquals("e".repeat(64), StrictJson.text(json.get("original_head_digest")));
        assertEquals("f".repeat(64), StrictJson.text(json.get("checkpoint_digest")));
        var decoded = SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json));
        assertEquals(evidence, decoded);
        assertEquals("9007199254740993", decoded.material().identity().fileId());
        assertEquals("13400000000000000100", decoded.material().identity().mtimeNs());
    }

    @Test void rejectsMissingFields() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        json.remove("schema");
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void rejectsNullFields() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        json.putNull("pair");
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void rejectsExtraFields() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        json.put("extra", "value");
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void rejectsWrongSchema() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        json.put("schema", "wrong.schema");
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void rejectsNumericAliasForDigest() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        json.put("original_head_digest", 123);
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void rejectsSourceMachineMismatch() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var json = evidence.toJson();
        var pairNode = StrictJson.object(json.get("pair"), Set.of("schema", "save", "driver", "frame", "lineage_id", "history_index", "save_action_id", "native_ack_ref", "observed_at_utc"));
        var frameNode = StrictJson.object(pairNode.get("frame"), Set.of("machine_id", "game", "frame", "observation_version"));
        frameNode.put("machine_id", "other-machine");
        assertThrows(Exception.class, () -> SavedCheckpointMaterialEvidence.decode(StrictJson.canonical(json)));
    }

    @Test void requireSavedBranchRejectsDifferentPair() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var differentPair = new CheckpointPair(pair().save(), pair().driver(), pair().frame(), "different-lineage", 1, "save-action-1", pair().nativeAckRef(), FIXED_TIME);
        assertThrows(Exception.class, () -> evidence.requireSavedBranch(differentPair, source()));
    }

    @Test void requireSavedBranchRejectsDifferentSource() {
        var evidence = new SavedCheckpointMaterialEvidence(pair(), source(), material(), 100, "e".repeat(64), "f".repeat(64));
        var differentSource = new SessionIdentity("test-machine-1", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))), "different-session");
        assertThrows(Exception.class, () -> evidence.requireSavedBranch(pair(), differentSource));
    }
}