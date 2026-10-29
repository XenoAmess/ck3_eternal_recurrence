package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Executes the actual strict review consumer without creating an actual challenge, Root approval or Game. */
class RootColdStageReviewTest {
    private static final Instant CREATED=Instant.parse("2026-10-23T05:00:00Z"),NOW=CREATED.plusSeconds(1),END=CREATED.plusSeconds(30);
    private static final ExactRef REF=new ExactRef("D:/synthetic/challenge.json",7,"a".repeat(64));
    private static ObjectNode challenge() {
        ObjectNode value=StrictJson.object(); value.put("machine_id","synthetic-only"); value.put("stage","SAVED_GAME_CREATE");
        value.put("session_nonce","b".repeat(32)); value.put("challenge_nonce","c".repeat(32));
        value.put("binding_sha256","d".repeat(64)); value.put("deadline_utc",END.toString()); value.put("created_at_utc",CREATED.toString());
        return value;
    }
    private static ObjectNode review() {
        ObjectNode value=challenge(); value.remove("created_at_utc");
        value.put("schema","xar.root-saved-cold-stage-review/v1"); value.put("reviewer","/root"); value.put("status","APPROVED_STAGE_ONCE");
        value.set("challenge_ref",REF.toJson()); value.put("reviewed_at_utc",NOW.toString()); return value;
    }
    @Test void exactIndependentReviewConsumerAcceptsDataWithoutMintingAReviewedResource() {
        assertDoesNotThrow(()->RootColdStageReview.validateReview(challenge(),REF,review(),NOW));
    }
    @Test void anotherStageNonceMachineCommandOrDeadlineCannotBorrowTheReview() {
        for(String field:List.of("machine_id","stage","session_nonce","challenge_nonce","binding_sha256","deadline_utc")) {
            ObjectNode value=review(); value.put(field,"changed");
            assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,value,NOW));
        }
    }
    @Test void approvalBooleanExtraFieldMissingRefAndWrongReviewerAreRejectedByActualConsumer() {
        ObjectNode bool=review(); bool.put("status",true);
        assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,bool,NOW));
        for(String field:List.of("challenge_ref","reviewer","schema","reviewed_at_utc")) {
            ObjectNode value=review(); value.remove(field);
            assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,value,NOW));
        }
        ObjectNode value=review(); value.put("approved",true);
        assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,value,NOW));
    }
    @Test void staleFutureAndPreChallengeReviewsCannotAuthorizeCurrentSubmission() {
        for(Instant time:List.of(CREATED.minusSeconds(1),NOW.plusSeconds(1))) {
            ObjectNode value=review(); value.put("reviewed_at_utc",time.toString());
            assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,value,NOW));
        }
        assertThrows(RuntimeException.class,()->RootColdStageReview.validateReview(challenge(),REF,review(),END));
    }
    @Test void concreteCommandSourcePinsCannotReadPersistenceBodiesOrDelegateToAShell() {
        var command=new WindowsJobProcess.CommandSpec(Path.of("D:/synthetic/ck3.exe"),List.of("-loadsave=xar_checkpoint"),
                Path.of("D:/synthetic"),Map.of(),Path.of("D:/synthetic/out"),Path.of("D:/synthetic/err"),128L<<20);
        for(String path:List.of("D:/synthetic/driver-state.json","D:/synthetic/checkpoint.ck3","D:/synthetic/checkpoint.sav")) {
            assertThrows(RuntimeException.class,()->new RootColdStageReview.PlannedCommand(command,
                    new ExactRef(command.executable().toString(),7,"a".repeat(64)),List.of(new ExactRef(path,7,"a".repeat(64))),END));
        }
        var shell=new WindowsJobProcess.CommandSpec(Path.of("D:/synthetic/cmd.exe"),List.of("/c","anything"),command.cwd(),
                command.environment(),command.stdout(),command.stderr(),command.memoryLimitBytes());
        assertThrows(RuntimeException.class,()->new RootColdStageReview.PlannedCommand(shell,
                new ExactRef(shell.executable().toString(),7,"a".repeat(64)),List.of(REF),END));
    }
    @Test void completeLargeSourceInventoryUsesExplicitFiniteMetadataBudgetWithoutTruncation() {
        var command=new WindowsJobProcess.CommandSpec(Path.of("D:/synthetic/python.exe"),List.of("D:/synthetic/entry.py"),
                Path.of("D:/synthetic"),Map.of(),Path.of("D:/synthetic/out"),Path.of("D:/synthetic/err"),128L<<20);
        var inputs=new java.util.ArrayList<ExactRef>();
        for(int index=0;index<600;index++) { inputs.add(new ExactRef("D:/synthetic/source/"+index+"/"+"longpath".repeat(12)+".java",7,"a".repeat(64))); }
        var planned=new RootColdStageReview.PlannedCommand(command,new ExactRef(command.executable().toString(),7,"b".repeat(64)),inputs,END);
        byte[] raw=RootColdStageReview.bindingBytes(planned);
        assertTrue(raw.length>65536); assertEquals(600,StrictJson.parse(raw,StrictJson.EXPLICIT_MAX_BYTES).get("immutable_inputs").size());
        assertEquals(inputs.getLast(),ExactRef.fromJson(StrictJson.parse(raw,StrictJson.EXPLICIT_MAX_BYTES).get("immutable_inputs").get(599)));
    }
}
