package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.wave2.runtime.closedadoption.OriginalColdConsumerSession;
import org.xar.ck3.control.wave2.runtime.closedadoption.CampaignScoreJunction;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootConsumerProtocol;

/** Software metadata peer only: no Root authority, process creator, Game or Native fixture. */
final class RootNativeMapCommandsTest {
    @TempDir Path directory;
    private static final RootConsumerProtocol.Binding BINDING = new RootConsumerProtocol.Binding(
            "software-map-command-test", "0123456789abcdef0123456789abcdef");

    @Test void realProtocolProducerConsumesOrderedTerminalsAndClosesOnlyAfterWorkflow() throws Exception {
        Path consumer = ready(Instant.now().plusSeconds(10));
        try (var workers = Executors.newSingleThreadExecutor()) {
            Future<RootNativeMapCommands.Completed> actual = workers.submit(() -> run(consumer));
            var first = request(consumer,1);
            assertInstanceOf(RootConsumerProtocol.Consumer.class,first.request());
            publish(consumer,1,"PREPARED","VERIFIED_ORIGINAL_CONSUMER",true,false);
            assertInstanceOf(RootConsumerProtocol.BeginRestoreReads.class,request(consumer,2).request());
            publish(consumer,2,"BEGIN_RESTORE_READS","RESTORE_INPUT_VIEW_REGISTERED",false,false);
            assertInstanceOf(RootConsumerProtocol.OpenColdSession.class,request(consumer,3).request());
            assertFalse(Files.exists(consumer.resolve("close.json")));
            publish(consumer,3,"OPEN_COLD_SESSION","COLD_WORKFLOW_RETURNED",false,false);
            assertEquals(consumer.resolve("0003.result.json"),actual.get(5,TimeUnit.SECONDS).workflowResult());
            assertEquals(new RootConsumerProtocol.Close(BINDING), RootConsumerProtocol.decodeClose(
                    Files.readAllBytes(consumer.resolve("close.json")),BINDING));
            assertFalse(Files.exists(consumer.resolve("0004.request.json")));
        }
    }
    @Test void originalPreparedFailureStopsBeforeRestoreReadsAndColdGameIntent() throws Exception {
        Path consumer = ready(Instant.now().plusSeconds(10));
        try (var workers = Executors.newSingleThreadExecutor()) {
            Future<RootNativeMapCommands.Completed> actual = workers.submit(() -> run(consumer));
            request(consumer,1); publish(consumer,1,"PREPARED","ORIGINAL_CONSUMER_FAILED",true,false);
            assertInstanceOf(IOException.class,assertThrows(ExecutionException.class,() -> actual.get(5,TimeUnit.SECONDS)).getCause());
            assertNoDependentIntent(consumer);
        }
    }
    @Test void nonemptyOriginalJobDoesNotAuthorizeTheNextRequest() throws Exception {
        Path consumer = ready(Instant.now().plusSeconds(10));
        try (var workers = Executors.newSingleThreadExecutor()) {
            Future<RootNativeMapCommands.Completed> actual = workers.submit(() -> run(consumer));
            request(consumer,1); publish(consumer,1,"PREPARED","VERIFIED_ORIGINAL_CONSUMER",true,true);
            assertThrows(ExecutionException.class,() -> actual.get(5,TimeUnit.SECONDS));
            assertNoDependentIntent(consumer);
        }
    }
    @Test void wrongLiveSessionResultIsRejectedBeforeAnyDependentIntent() throws Exception {
        Path consumer = ready(Instant.now().plusSeconds(10));
        try (var workers = Executors.newSingleThreadExecutor()) {
            Future<RootNativeMapCommands.Completed> actual = workers.submit(() -> run(consumer));
            request(consumer,1);
            ObjectNode result = result(1,"PREPARED","VERIFIED_ORIGINAL_CONSUMER",true,false);
            result.put("session_nonce","fedcba9876543210fedcba9876543210");
            Files.write(consumer.resolve("0001.result.json"),StrictJson.canonical(result));
            assertInstanceOf(IOException.class,assertThrows(ExecutionException.class,() -> actual.get(5,TimeUnit.SECONDS)).getCause());
            assertNoDependentIntent(consumer);
        }
    }
    @Test void preparationUsesTheSameMaterializedQuoteAndCompletesEveryOriginalStageBeforeOpen() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));
        var input=preparationInput();
        try (var workers=Executors.newSingleThreadExecutor()) {
            var actual=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(8)));
            assertInstanceOf(OriginalColdConsumerSession.ComposeBundle.class,
                    ((RootConsumerProtocol.Consumer)request(consumer,1).request()).operation());
            ExactRef quote=materialize(input);
            publishCompose(consumer,quote);
            var junction=(OriginalColdConsumerSession.PrepareJunction)
                    ((RootConsumerProtocol.Consumer)request(consumer,2).request()).operation();
            assertEquals(quote,junction.quote()); assertEquals(input.planRef(),junction.plan());
            assertEquals(input.runtimeRoot(),junction.runtimeRoot());
            publishJunction(consumer,input,false);
            var offline=(OriginalColdConsumerSession.PrepareOffline)
                    ((RootConsumerProtocol.Consumer)request(consumer,3).request()).operation();
            assertEquals(quote,offline.quote()); assertEquals(input.metadataRoot(),offline.metadataRoot());
            assertEquals(input.historicalFixture(),offline.fixture());
            publish(consumer,3,"PREPARE_OFFLINE","VERIFIED_ORIGINAL_CONSUMER",true,false);
            assertInstanceOf(OriginalColdConsumerSession.Prepared.class,
                    ((RootConsumerProtocol.Consumer)request(consumer,4).request()).operation());
            publish(consumer,4,"PREPARED","VERIFIED_ORIGINAL_CONSUMER",true,false);
            var begin=(RootConsumerProtocol.BeginRestoreReads)request(consumer,5).request();
            assertEquals(4,begin.preparedSequence());
            var begun=result(5,"BEGIN_RESTORE_READS","RESTORE_INPUT_VIEW_REGISTERED",false,false);
            begun.put("prepared_sequence",4);
            Files.write(consumer.resolve("0005.result.json"),StrictJson.canonical(begun));
            assertInstanceOf(RootConsumerProtocol.OpenColdSession.class,request(consumer,6).request());
            assertFalse(Files.exists(consumer.resolve("close.json")));
            publish(consumer,6,"OPEN_COLD_SESSION","COLD_WORKFLOW_RETURNED",false,false);
            var complete=actual.get(5,TimeUnit.SECONDS);
            assertEquals(quote,complete.materializedQuote());
            assertEquals(consumer.resolve("0004.result.json"),complete.completed().preparedResult());
            assertEquals(consumer.resolve("0006.result.json"),complete.completed().workflowResult());
            assertTrue(Files.exists(consumer.resolve("close.json")));
            assertFalse(Files.exists(consumer.resolve("0007.request.json")));
        }
    }
    @Test void anotherMaterializedQuoteCannotAuthorizeJunctionOrOfflinePreparation() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10)); var input=preparationInput();
        try (var workers=Executors.newSingleThreadExecutor()) {
            var actual=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1); materialize(input);
            Path other=Files.writeString(input.metadataRoot().resolve("other-quote.json"),"{}\n");
            publishCompose(consumer,exact(other));
            assertInstanceOf(IOException.class,assertThrows(ExecutionException.class,()->actual.get(5,TimeUnit.SECONDS)).getCause());
            assertNoDependentIntent(consumer);
        }
    }
    @Test void incompleteJunctionJobStopsBeforeOfflineProducerPreparedAndGameIntent() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10)); var input=preparationInput();
        try (var workers=Executors.newSingleThreadExecutor()) {
            var actual=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1); publishCompose(consumer,materialize(input));
            request(consumer,2); publishJunction(consumer,input,true);
            assertInstanceOf(IOException.class,assertThrows(ExecutionException.class,()->actual.get(5,TimeUnit.SECONDS)).getCause());
            for (int index=3;index<=6;index++) assertFalse(Files.exists(consumer.resolve(String.format(java.util.Locale.ROOT,"%04d.request.json",index))));
            assertFalse(Files.exists(consumer.resolve("close.json")));
        }
    }
    @Test void missingActualWriterHandoffStopsBeforeOfflineAndPrepared() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));var input=preparationInput();
        try(var workers=Executors.newSingleThreadExecutor()) {
            var pending=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1);publishCompose(consumer,materialize(input));request(consumer,2);
            var value=junctionResult(consumer,input,false);
            value.remove("junction_writer_handoff");Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(value));
            assertThrows(ExecutionException.class,()->pending.get(5,TimeUnit.SECONDS));
            assertFalse(Files.exists(consumer.resolve("0003.request.json")));assertFalse(Files.exists(consumer.resolve("close.json")));
        }
    }
    @Test void unknownOrFailedOriginalWriterNeverAdvancesToOfflinePreparation() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));var input=preparationInput();
        try(var workers=Executors.newSingleThreadExecutor()) {
            var pending=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1);publishCompose(consumer,materialize(input));request(consumer,2);
            var value=result(2,"PREPARE_JUNCTION","VERIFIED_ORIGINAL_CONSUMER",true,false);
            ((ObjectNode)value.get("junction_writer_handoff")).put("active_processes",1);
            Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(value));
            assertThrows(ExecutionException.class,()->pending.get(5,TimeUnit.SECONDS));
            assertFalse(Files.exists(consumer.resolve("0003.request.json")));assertFalse(Files.exists(consumer.resolve("0004.request.json")));
        }
    }
    @Test void missingJavaReceiptNeverAdvancesToOfflinePreparation() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));var input=preparationInput();
        try(var workers=Executors.newSingleThreadExecutor()) {
            var pending=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1);publishCompose(consumer,materialize(input));request(consumer,2);
            var value=junctionResult(consumer,input,false);value.remove("java_junction_ref");
            Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(value));
            assertThrows(ExecutionException.class,()->pending.get(5,TimeUnit.SECONDS));
            assertFalse(Files.exists(consumer.resolve("0003.request.json")));
        }
    }
    @Test void aReceiptForAnotherExactQuotedBindingNeverGrantsOfflinePreparation() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));var input=preparationInput();
        try(var workers=Executors.newSingleThreadExecutor()) {
            var pending=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1);publishCompose(consumer,materialize(input));request(consumer,2);
            var value=junctionResult(consumer,input,false);
            Path receiptPath=consumer.resolve("0002.java-junction.json");
            var receipt=(ObjectNode)StrictJson.parse(Files.readAllBytes(receiptPath));
            ((ObjectNode)receipt.get("campaign_score_junction")).put("target_file_id","9");
            ((ObjectNode)receipt.get("target_identity")).put("file_id","9");
            Files.write(receiptPath,StrictJson.canonical(receipt));
            value.set("java_junction_ref",exact(receiptPath).toJson());
            Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(value));
            assertThrows(ExecutionException.class,()->pending.get(5,TimeUnit.SECONDS));
            assertFalse(Files.exists(consumer.resolve("0003.request.json")));
        }
    }
    @Test void samePathReceiptReplacementCannotBeAcceptedWithTheOriginalExactReference() throws Exception {
        Path consumer=ready(Instant.now().plusSeconds(10));var input=preparationInput();
        try(var workers=Executors.newSingleThreadExecutor()) {
            var pending=workers.submit(()->RootNativeMapCommands.runPreparation(consumer,BINDING.machineId(),input,Instant.now().plusSeconds(5)));
            request(consumer,1);publishCompose(consumer,materialize(input));request(consumer,2);
            var value=junctionResult(consumer,input,false);
            Path receiptPath=consumer.resolve("0002.java-junction.json");
            Files.writeString(receiptPath,"{}");
            Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(value));
            assertThrows(ExecutionException.class,()->pending.get(5,TimeUnit.SECONDS));
            assertFalse(Files.exists(consumer.resolve("0003.request.json")));
        }
    }
    private RootNativeMapCommands.PreparationInput preparationInput() throws IOException {
        ExactRef plan=exact(Files.writeString(directory.resolve("plan.json"),"{}\n"));
        ExactRef fixture=exact(Files.writeString(directory.resolve("historical-fixture.json"),"{}\n"));
        Path metadata=directory.resolve("preparation-metadata");
        return new RootNativeMapCommands.PreparationInput(plan,directory.resolve("new-runtime"),metadata.resolve("quote.json"),
                metadata,directory.resolve("preparation-historical-fixture"),fixture,
                "11111111111111111111111111111111","22222222222222222222222222222222");
    }
    private static ExactRef materialize(RootNativeMapCommands.PreparationInput input) throws IOException {
        Files.createDirectory(input.runtimeRoot()); Files.createDirectory(input.metadataRoot());
        Path target=input.runtimeRoot().resolveSibling("original").resolve("campaign-score");
        var binding=new CampaignScoreJunction.Binding(input.runtimeRoot().resolve("campaign-score"),target,"7","0",
                new ExactRef(target.resolve("CAMPAIGN-ANCHOR.json").toString(),9,"c".repeat(64)));
        ObjectNode quote=StrictJson.object();quote.set("campaign_score_junction",binding.toJson());
        return exact(Files.write(input.quoteOutput(),StrictJson.canonical(quote)));
    }
    private static ObjectNode junctionResult(Path consumer,RootNativeMapCommands.PreparationInput input,
            boolean compatibilityProcess) throws IOException {
        var value=result(2,"PREPARE_JUNCTION",CampaignScoreJunction.ROOT_RESULT_STATUS,compatibilityProcess,false);
        var binding=CampaignScoreJunction.Binding.decode(
                StrictJson.parse(Files.readAllBytes(input.quoteOutput())).get("campaign_score_junction"));
        var receipt=new CampaignScoreJunction.PreparedReceipt(BINDING.machineId(),Instant.now(),binding,
                new CampaignScoreJunction.NativeIdentity("7","0","1"),new CampaignScoreJunction.NativeIdentity("8","0","2"));
        Path receiptPath=consumer.resolve("0002.java-junction.json");
        Files.write(receiptPath,StrictJson.canonical(receipt.toJson()));
        value.set("java_junction_ref",exact(receiptPath).toJson());
        return value;
    }
    private static void publishJunction(Path consumer,RootNativeMapCommands.PreparationInput input,
            boolean compatibilityProcess) throws IOException {
        Files.write(consumer.resolve("0002.result.json"),StrictJson.canonical(junctionResult(consumer,input,compatibilityProcess)));
    }
    private static void publishCompose(Path consumer,ExactRef quote) throws IOException {
        var value=result(1,"COMPOSE_BUNDLE","VERIFIED_ORIGINAL_CONSUMER",true,false);
        value.set("materialized_quote_ref",quote.toJson());
        Files.write(consumer.resolve("0001.result.json"),StrictJson.canonical(value));
    }
    private static ExactRef exact(Path path) throws IOException {
        var ref=ControlBuild.FileRef.measure(path); return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    private RootNativeMapCommands.Completed run(Path consumer) throws IOException,InterruptedException {
        Path runtime = directory.resolve("materialized");
        return RootNativeMapCommands.run(consumer,BINDING.machineId(),new RootNativeMapCommands.PreparedInput(
                runtime,"11111111111111111111111111111111","22222222222222222222222222222222"),Instant.now().plusSeconds(5));
    }
    private Path ready(Instant deadline) throws IOException {
        Path consumer = Files.createDirectory(directory.resolve("consumer"));
        Files.createDirectory(directory.resolve("materialized"));
        ObjectNode ready = StrictJson.object();
        ready.put("schema","xar.java-closed-partial-root-consumer-session/v1");
        ready.put("machine_id",BINDING.machineId()); ready.put("session_nonce",BINDING.sessionNonce());
        ready.put("status","READY"); ready.put("deadline_utc",deadline.toString());
        Files.write(consumer.resolve("session-ready.json"),StrictJson.canonical(ready)); return consumer;
    }
    private static RootConsumerProtocol.Command request(Path consumer,int sequence) throws Exception {
        Path path = consumer.resolve(RootConsumerProtocol.requestFileName(sequence));
        Instant until = Instant.now().plusSeconds(5);
        while (!Files.exists(path) && Instant.now().isBefore(until)) Thread.sleep(10);
        assertTrue(Files.exists(path),"actual Java producer published typed request");
        return RootConsumerProtocol.decodeCommand(Files.readAllBytes(path),BINDING,sequence);
    }
    private static void publish(Path consumer,int sequence,String operation,String status,boolean process,boolean active) throws IOException {
        Files.write(consumer.resolve(String.format(java.util.Locale.ROOT,"%04d.result.json",sequence)),
                StrictJson.canonical(result(sequence,operation,status,process,active)));
    }
    private static ObjectNode result(int sequence,String operation,String status,boolean process,boolean active) {
        ObjectNode value = StrictJson.object(); value.put("schema","xar.java-closed-partial-root-consumer-session/v1");
        value.put("machine_id",BINDING.machineId()); value.put("session_nonce",BINDING.sessionNonce());
        value.put("sequence",sequence); value.put("operation",operation); value.put("status",status);
        if (sequence == 2) value.put("prepared_sequence",1);
        var jobs = value.putArray("actual_original_processes");
        if (process) jobs.addObject().put("status","PASSED").put("exit_code",0).put("active_processes",active ? 1 : 0);
        if ("PREPARE_JUNCTION".equals(operation)) {
            var handoff=value.putObject("junction_writer_handoff");
            handoff.put("schema","xar.java-junction-original-writer-handoff/v1");handoff.put("machine_id",BINDING.machineId());
            handoff.put("terminal_path",Path.of("D:/synthetic/junction-writer-terminal.json").toString());
            handoff.put("stdout_path",Path.of("D:/synthetic/junction-writer-stdout.jsonl").toString());
            handoff.put("status","PASSED");handoff.put("pid",10);handoff.put("creation_filetime","18446744073709551615");
            handoff.put("exit_code",0);handoff.put("active_processes",0);handoff.put("peak_job_memory_bytes",1);
            handoff.put("ledger_modified",false);handoff.put("raw_pending_modified",false);handoff.put("original_actions_replayed",false);
        }
        return value;
    }
    private static void assertNoDependentIntent(Path consumer) {
        for (String name : new String[]{"0002.request.json","0003.request.json","close.json"}) assertFalse(Files.exists(consumer.resolve(name)),name);
    }
}
