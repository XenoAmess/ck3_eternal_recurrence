package org.xar.ck3.control.application.checkpoint;

import java.io.IOException;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Only the two original stores mint these materials. Retained data alone grants no reload. */
public sealed interface SavedCheckpointMaterial permits SavedAttachmentSourceStore.SavedMaterial,
        SavedFirstCheckpointMaterialStore.BaselinedMaterial {
    enum Kind { ORDINARY, FIRST_BASELINE }
    Kind kind();
    CheckpointPair pair();
    SessionIdentity session();
    FileWitness witness();
    ExactRef reference();
    ContinuityState originalHead();
    String originalHeadDigest();
    long originalHeadSequence();
    String checkpointDigest();
    DriverStateSnapshot.Complete savedDriver();
    SemanticEvidence sourceSemantic();
    void requireRetained(ContinuityStorePort.Session same) throws IOException;
    void requirePhysical(ContinuityStorePort.Session same) throws IOException;
}
