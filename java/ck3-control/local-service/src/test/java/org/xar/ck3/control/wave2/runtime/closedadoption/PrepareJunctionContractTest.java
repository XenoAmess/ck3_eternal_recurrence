package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Strict actual command wire and denial of source-only/public completion authority.
 * Synthetic SDK fixtures never qualify a Root retained measurement or Native stage. */
final class PrepareJunctionContractTest {
    private static final ExactRef PLAN=new ExactRef("D:/owned/plan.json",7,"a".repeat(64));
    private static final ExactRef QUOTE=new ExactRef("D:/owned/quote.json",9,"b".repeat(64));
    private static final Path RUNTIME=Path.of("D:/owned/runtime");
    private static OriginalColdConsumerSession.PrepareJunction operation() {
        return new OriginalColdConsumerSession.PrepareJunction(PLAN,QUOTE,RUNTIME);
    }
    private static JsonNode kind() {return StrictJson.object().put("kind","PREPARE_JUNCTION").get("kind");}
    @Test void actualCommandProducerRoundTripsThroughTheSharedConsumerDecoder() {
        var binding=new RootConsumerProtocol.Binding("junction-wire-fixture","a".repeat(32));
        var command=new RootConsumerProtocol.Command(binding,2,new RootConsumerProtocol.Consumer(operation()));
        var decoded=RootConsumerProtocol.decodeCommand(command.wireBytes(),binding,2);
        assertEquals(command,decoded);
        assertEquals(operation(),((RootConsumerProtocol.Consumer)decoded.request()).operation());
    }
    @Test void junctionArgumentsRejectMissingExtraNullAndWrongTokenFields() {
        for(String field:List.of("plan_ref","quote_ref","approved_runtime_root")) {
            var missing=operation().arguments();missing.remove(field);
            assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.decodeOperation(kind(),missing));
            var nil=operation().arguments();nil.putNull(field);
            assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.decodeOperation(kind(),nil));
        }
        var extra=operation().arguments();extra.put("approved",true);
        assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.decodeOperation(kind(),extra));
        for(String raw:List.of("true","1","1.0","[]","{}")) {
            var bad=operation().arguments();bad.set("approved_runtime_root",StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.decodeOperation(kind(),bad));
        }
    }
    @Test void junctionRefsRejectNonIntegerSizesAndUnboundedOrEmptyEvidence() {
        for(String raw:List.of("true","7.0","null","\"7\"")) {
            var bad=operation().arguments();
            ((ObjectNode)bad.get("plan_ref")).set("bytes",StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.decodeOperation(kind(),bad));
        }
        for(long size:new long[]{0,1_048_577}) {
            var bad=new ExactRef(PLAN.path(),size,PLAN.sha256());
            assertThrows(ContractViolationException.class,()->new OriginalColdConsumerSession.PrepareJunction(bad,QUOTE,RUNTIME));
            assertThrows(ContractViolationException.class,()->new OriginalColdConsumerSession.PrepareJunction(PLAN,bad,RUNTIME));
        }
        assertThrows(ContractViolationException.class,()->new OriginalColdConsumerSession.PrepareJunction(PLAN,QUOTE,Path.of("relative")));
        assertThrows(ContractViolationException.class,()->new OriginalColdConsumerSession.PrepareJunction(PLAN,QUOTE,Path.of("D:/owned/../runtime")));
    }
    private static ObjectNode junction() {
        var row=StrictJson.object();row.put("path",RUNTIME.resolve("campaign-score").toString());
        row.put("exact_target","D:/owned/origin/campaign-score");row.put("must_verify_same_FileID",true);
        row.put("target_file_id","18446744073709551615");row.put("target_device","0");
        row.set("anchor_ref",new ExactRef("D:/owned/origin/campaign-score/CAMPAIGN-ANCHOR.json",9,"c".repeat(64)).toJson());
        return row;
    }
    @Test void uint64IdentityStringsKeepTheirExactWireRepresentation() {
        var value=CampaignScoreJunction.Binding.decode(junction());
        assertEquals("18446744073709551615",value.fileId());assertEquals("0",value.device());
        for(String field:List.of("target_file_id","target_device")) {
            for(String raw:List.of("true","1","1.0","null","\"01\"","\"18446744073709551616\"","\"-1\"")) {
                var bad=junction();bad.set(field,StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(ContractViolationException.class,()->CampaignScoreJunction.Binding.decode(bad));
            }
        }
        var zero=junction();zero.put("target_file_id","0");
        assertThrows(ContractViolationException.class,()->CampaignScoreJunction.Binding.decode(zero));
    }
    @Test void junctionBindingRejectsIncompleteAndLooseSameFileFlags() {
        for(String field:List.of("path","exact_target","must_verify_same_FileID","target_file_id","target_device","anchor_ref")) {
            var bad=junction();bad.remove(field);
            assertThrows(ContractViolationException.class,()->CampaignScoreJunction.Binding.decode(bad));
        }
        for(String raw:List.of("false","1","null","\"true\"")) {
            var bad=junction();bad.set("must_verify_same_FileID",StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class,()->CampaignScoreJunction.Binding.decode(bad));
        }
        var extra=junction();extra.put("authorized",true);
        assertThrows(ContractViolationException.class,()->CampaignScoreJunction.Binding.decode(extra));
    }
    @Test void javaJunctionCannotEnterTheCompatibilityPythonTransport() throws Exception {
        AtomicInteger launched=new AtomicInteger();
        assertThrows(ContractViolationException.class,()->OriginalColdConsumerSession.runOperation(null,operation(),()-> {
            launched.incrementAndGet(); throw new java.io.IOException("unexpected Python launch");
        }));
        assertEquals(0,launched.get());
    }
    private static RecoveryEvidence publish(Path path,byte[] raw) throws java.io.IOException {
        Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        return new RecoveryEvidence(new ExactRef(path.toString(),raw.length,RecoveryEvidence.sha256(raw)),raw);
    }
    @Test void publicActualCompletedWriterCannotMintTheRetainedRootJunctionScope() throws Exception {
        var fixture=ClosedAdoptionTransactionTest.fixture();
        var completed=ClosedAdoptionApplication.runOriginal(fixture.target(),fixture::material,fixture::material,fixture::canonical,
                raw->publish(fixture.root().resolve("junction-denial-basis.json"),raw),
                raw->publish(fixture.root().resolve("junction-denial-qualification.json"),raw),
                ClosedAdoptionTransactionTest.settings(fixture),value->{});
        try(var authority=ClosedInputsSessionAuthority.open(fixture::material,completed.writer(),fixture::canonical,
                completed.basis(),completed.qualification(),Instant.now().plusSeconds(30))) {
            assertThrows(ContractViolationException.class,()->authority.prepareJunction(operation()));
            assertFalse(authority.grantsWarmAttachment());
        }
    }
}
