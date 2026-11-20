// Exact92 software selection only; all old61 ACK/old56 receipt DATA remains historical, never92 live custody.
package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Producer DATA on a closed historical before, never a Root context, live SAVE, deadline renewal or dispatch. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.save92.inputs",matches=".+")
final class MappedSave92RootProducerTest {
    private static byte[] exact(com.fasterxml.jackson.databind.JsonNode r)throws Exception {
        byte[] b=Files.readAllBytes(Path.of(r.path("path").textValue()));assertEquals(r.path("bytes").longValue(),b.length);
        assertEquals(r.path("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b)));return b;
    }
    @Test void actualRootProducerSelectsOnlyExplicitMapped92AndKeepsTheOriginalBeforeAndDeadline()throws Exception {
        var in=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.save92.inputs"))));
        var old=ActionCodec.decodeCommand(exact(in.path("closed25_command")));var before=old.before();var src=old.source();
        // New software DATA identity and the real common checkpoint expectation; no old action is replayed.
        var values=List.<ExpectedValue>of(new ExpectedInteger(new FieldKey("date_raw"),before.frame().identity().dateRaw()),
                new ExpectedInteger(new FieldKey("played_character_id"),before.frame().identity().player()),new ExpectedBoolean(new FieldKey("checkpoint_pair_verified"),true));
        var command=new ActionCommand("software-mapped-save61-producer",before,src,old.sessionId(),RootSaveRuntime.OPERATION,
                new OpportunityJson.Obj(Map.of()),new ExpectedPostcondition(1,before,src,CheckpointRequestFactory.OBSERVER_SCHEMA,values),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),old.deadline());
        var r=in.path("bridge");exact(r);var bridge=new ExactRef(r.path("path").textValue(),r.path("bytes").longValue(),r.path("sha256").textValue());
        assertThrows(IllegalArgumentException.class,()->RootSaveRuntime.preparedSaveRequest(command));
        var request=RootSaveRuntime.preparedSaveRequest(command,bridge);
        var claim=StrictJson.parse(request.additionalFields().bytes()).path("full_snapshot_clock_control");
        assertEquals(before.frame().snapshotId(),claim.path("snapshot_id").textValue());
        assertEquals(before.frame().identity().nativeRevision(),claim.path("native_revision").bigIntegerValue());
        assertEquals(old.deadline().toEpochMilli(),claim.path("deadline_unix_ms").longValue());
        assertEquals("game.command.save-checkpoint",request.requiredCapability().orElseThrow());
        assertThrows(IllegalArgumentException.class,()->RootSaveRuntime.preparedSaveRequest(command,new ExactRef(bridge.path(),bridge.bytes(),"0".repeat(64))));
        assertThrows(IllegalArgumentException.class,()->RootSaveRuntime.preparedSaveRequest(old,bridge));
    }
}
