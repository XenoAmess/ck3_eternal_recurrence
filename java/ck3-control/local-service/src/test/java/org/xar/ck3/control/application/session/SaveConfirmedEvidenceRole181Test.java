package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Pure request DATA assembly. No native ACK, Ready, physical-pair verifier, writer Session or SAVE authority is supplied. */
final class SaveConfirmedEvidenceRole181Test {
    @TempDir Path temporary;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private ExactRef data(String name,String text)throws Exception {
        Path path=temporary.resolve(name);Files.writeString(path,text);return files.observe(path).orElseThrow().reference();
    }
    @Test void onlyConfirmedExactSaveLeavesGenericEvidenceWhileFullPairAndOtherOriginalsRemain() throws Exception {
        ExactRef save=data("save-DATA.ck3","physical software SAVE DATA");
        ExactRef driver=data("driver-DATA.json","complete Driver DATA");
        ExactRef ack=data("ack-DATA-only.json","ordinary DATA; no native ACK is asserted");
        ExactRef sameBytes=data("other-same-bytes.json","physical software SAVE DATA");
        ExactRef unrelated=data("unrelated.json","unrelated original DATA");
        var owner=new SessionIdentity("data-machine-181",new GameGeneration(1,new PythonOnlyUInt64(BigInteger.ONE)),"data-session-181");
        var frame=new ObservationIdentity(owner.machineId(),owner.game(),new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.ONE,BigInteger.valueOf(24000)),
                "data-snapshot",BigInteger.ONE,"data-episode"),1);
        var semantic=new SemanticEvidence(frame,data("semantic.json","semantic DATA"),data("packet-DATA.json","packet DATA"),
                data("stamp.json","stamp DATA"),data("before-driver.json","before Driver DATA"),Instant.now());
        var proof=new CompletedCycleProof(1,semantic,semantic.semantic().sha256());
        var pair=new CheckpointPair(files.observe(Path.of(save.path())).orElseThrow(),files.observe(Path.of(driver.path())).orElseThrow(),
                frame,"data-lineage",1,"data-save-action",ack,Instant.now());
        var noArchive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{throw new AssertionError("DATA assembly cannot use archive: "+method.getName());});
        var transitions=new OrdinaryCycleTransitions(noArchive,
                (same,source,value)->{throw new AssertionError("DATA assembly cannot verify semantic");},
                (same,source,value,completed)->{throw new AssertionError("DATA assembly cannot qualify a physical pair");},
                new OriginalWindowReducer.Policy(10958),same->{throw new AssertionError("DATA assembly cannot qualify a writer Session");});
        var input=List.of(save,driver,ack,sameBytes,unrelated,save);
        var request=transitions.batchRequest(new JournalInput(owner,"batch-save-181",JournalKind.SAVE_CONFIRMED,
                Optional.of(frame),Optional.of(pair),Optional.of(proof),input));
        assertFalse(request.evidence().contains(save));
        var expected=new ArrayList<>(List.of(driver,ack,sameBytes,unrelated));expected.addAll(semantic.references());
        assertEquals(new HashSet<>(expected),new HashSet<>(request.evidence()));
        assertEquals(expected.size(),request.evidence().size());
        assertEquals(save.sha256(),sameBytes.sha256());assertNotEquals(save,sameBytes);
        var details=request.detailsObject();
        assertArrayEquals(CheckpointPairCodec.encode(pair),ContinuityJson.canonical(details.get("checkpoint_pair")));
        assertEquals(pair,CheckpointPairCodec.decode(ContinuityJson.canonical(details.get("checkpoint_pair"))));
        assertFalse(details.get("completed_cycle_proof").isNull());
        var control=transitions.batchRequest(new JournalInput(owner,"batch-start-181",JournalKind.BATCH_STARTED,
                Optional.of(frame),Optional.empty(),Optional.empty(),input));
        assertEquals(List.of(save,driver,ack,sameBytes,unrelated),control.evidence());
    }
}
