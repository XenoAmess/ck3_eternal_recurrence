package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** The router's actual data gate rejects a recycled PID after the canonical pair codec roundtrip. */
final class RootCheckpointVerifierRouterTest {
    @Test void samePidDifferentFullBirthOrMachineCannotSelectThePhysicalPairRoute() {
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("18446744073709551615")));
        var observation=new ObservationIdentity("controlled-machine",game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.ONE),
                        "native:1",BigInteger.ONE,"controlled-episode"),1);
        var file=new FileStatIdentity(BigInteger.ONE,"18446744073709551615","1792800000000000000");
        var pair=new CheckpointPair(new CheckpointPair.FileWitness(new ExactRef("controlled-save",1,"a".repeat(64)),file),
                new CheckpointPair.FileWitness(new ExactRef("controlled-driver",1,"b".repeat(64)),file),observation,
                "controlled-lineage",1,"controlled-save-action",new ExactRef("controlled-ack",1,"c".repeat(64)),Instant.parse("2026-10-24T00:00:00Z"));
        var decoded=CheckpointPairCodec.decode(CheckpointPairCodec.encode(pair));
        assertDoesNotThrow(()->RootCheckpointVerifierRouter.requirePairOwner(new SessionIdentity("controlled-machine",game,"controlled-session"),decoded));
        var recycled=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("18446744073709551614")));
        assertThrows(java.io.IOException.class,()->RootCheckpointVerifierRouter.requirePairOwner(new SessionIdentity("controlled-machine",recycled,"controlled-session"),decoded));
        assertThrows(java.io.IOException.class,()->RootCheckpointVerifierRouter.requirePairOwner(new SessionIdentity("other-machine",game,"controlled-session"),decoded));
    }
}
