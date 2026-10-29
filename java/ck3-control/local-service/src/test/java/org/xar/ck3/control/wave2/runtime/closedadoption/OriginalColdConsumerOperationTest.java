package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

class OriginalColdConsumerOperationTest {
    private static final ExactRef PLAN = new ExactRef("D:/owned/plan.json",7,"a".repeat(64));
    private static final ExactRef QUOTE = new ExactRef("D:/owned/quote.json",9,"b".repeat(64));
    private static final Path RUNTIME = Path.of("D:/owned/runtime");

    @Test void everyFixedFormalConsumerHasOneStrictArgumentShape() {
        List<OriginalColdConsumerSession.Operation> operations = List.of(
                new OriginalColdConsumerSession.ColdInputs(),new OriginalColdConsumerSession.SdkClosure(),
                new OriginalColdConsumerSession.LoadColdInputs(RUNTIME),new OriginalColdConsumerSession.WarmInputs(RUNTIME),
                new OriginalColdConsumerSession.Prepared(RUNTIME,"a".repeat(32),"b".repeat(32)),
                new OriginalColdConsumerSession.Compose(PLAN),new OriginalColdConsumerSession.ColdOwner(PLAN,QUOTE));
        for (var operation : operations) {
            assertEquals(operation,OriginalColdConsumerSession.decodeOperation(
                    StrictJson.object().put("kind",operation.kind().name()).get("kind"),operation.arguments()));
        }
    }

    @Test void genericToolPauseLaunchAndUnknownMethodsAreNotConsumerOperations() {
        for (String name : List.of("execute_step","CANCEL","ARM","AUTO","SAVE","FULL","CLOSED_INPUTS_CALLBACK","")) {
            var kind = StrictJson.object().put("kind",name).get("kind");
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(kind,StrictJson.object()));
        }
    }

    @Test void emptyArgumentOperationsRejectExtraOrMissingObjects() {
        for (String kind : List.of("COLD_INPUTS","SDK_CLOSURE")) {
            var name = StrictJson.object().put("kind",kind).get("kind");
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(name,StrictJson.object().put("ready",true)));
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(name,null));
        }
    }

    @Test void operationDiscriminatorRejectsNonTextTokens() {
        for (String raw : List.of("null","true","1","1.0","[]","{}")) {
            var value = StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(value,StrictJson.object()));
        }
    }

    @Test void preparedRequiresBothExactNoncesAndNormalizedAbsoluteRuntime() {
        assertThrows(ContractViolationException.class,() -> new OriginalColdConsumerSession.Prepared(RUNTIME,"A".repeat(32),"b".repeat(32)));
        assertThrows(ContractViolationException.class,() -> new OriginalColdConsumerSession.Prepared(RUNTIME,"a".repeat(31),"b".repeat(32)));
        assertThrows(ContractViolationException.class,() -> new OriginalColdConsumerSession.Prepared(Path.of("relative"),"a".repeat(32),"b".repeat(32)));
        ObjectNode args = new OriginalColdConsumerSession.Prepared(RUNTIME,"a".repeat(32),"b".repeat(32)).arguments(); args.remove("task_nonce");
        assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(StrictJson.object().put("kind","PREPARED").get("kind"),args));
    }

    @Test void sourceRefsRetainStrictIntegerAndUnknownFieldContracts() {
        for (String bad : List.of("true","7.0","\"7\"","null")) {
            String raw = "{\"plan_ref\":{\"path\":\"D:/owned/plan.json\",\"bytes\":"+bad+",\"sha256\":\""+"a".repeat(64)+"\"}}";
            var value = StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(StrictJson.object().put("kind","COMPOSE").get("kind"),value));
        }
        ObjectNode args = new OriginalColdConsumerSession.Compose(PLAN).arguments(); args.put("metadata_overlay",true);
        assertThrows(ContractViolationException.class,() -> OriginalColdConsumerSession.decodeOperation(StrictJson.object().put("kind","COMPOSE").get("kind"),args));
    }

    @Test void originalTransportFrameKeepsDecimalLexemesLargeIdsAndUnicodeBytes() throws Exception {
        byte[] raw = " {\"f\":1e-7,\"elapsed\":6.0,\"id\":18446744073709551615,\"text\":\"原始回执\"} ".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        var line = new java.io.ByteArrayOutputStream(); line.write(raw); line.write('\n');
        assertArrayEquals(raw,OriginalWriterTransaction.readFrame(new java.io.ByteArrayInputStream(line.toByteArray())));
        byte[] trailing = "{\"id\":1}garbage\n".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class,() -> OriginalWriterTransaction.readFrame(new java.io.ByteArrayInputStream(trailing)));
    }
}
