package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.closedadoption.OriginalColdConsumerSession;
import org.xar.ck3.control.wave2.runtime.closedadoption.CampaignScoreJunction;
import org.xar.ck3.control.wave2.runtime.closedadoption.RootConsumerProtocol;

/** Metadata producer for the existing Root consumer; every operation is submitted at most once. */
public final class RootNativeMapCommands {
    private static final int MAX_BYTES = 1_048_576;
    private RootNativeMapCommands() { }

    public record PreparedInput(Path runtimeRoot, String attemptNonce, String taskNonce) {
        public PreparedInput {
            absolute(runtimeRoot);
            if (attemptNonce == null || !attemptNonce.matches("[0-9a-f]{32}")
                    || taskNonce == null || !taskNonce.matches("[0-9a-f]{32}"))
                throw new IllegalArgumentException("Exact original preparation nonces required");
        }
    }
    /** Data for the original preparation producers; constructing it does not create Prepared. */
    public record PreparationInput(ExactRef planRef, Path runtimeRoot, Path quoteOutput,
            Path metadataRoot, Path fixtureRoot, ExactRef historicalFixture,
            String attemptNonce, String taskNonce) {
        public PreparationInput {
            Objects.requireNonNull(planRef); Objects.requireNonNull(historicalFixture);
            new PreparedInput(runtimeRoot, attemptNonce, taskNonce);
            absolute(quoteOutput); absolute(metadataRoot); absolute(fixtureRoot);
            if (!metadataRoot.equals(quoteOutput.getParent()) || runtimeRoot.startsWith(metadataRoot)
                    || metadataRoot.startsWith(runtimeRoot) || fixtureRoot.startsWith(runtimeRoot)
                    || runtimeRoot.startsWith(fixtureRoot) || metadataRoot.startsWith(fixtureRoot)
                    || fixtureRoot.startsWith(metadataRoot))
                throw new IllegalArgumentException("Separate exact preparation write roots required");
        }
        public PreparedInput expectedPrepared() { return new PreparedInput(runtimeRoot, attemptNonce, taskNonce); }
    }
    public record Completed(Path preparedResult, Path restoreReadsResult, Path workflowResult) {
        public Completed { absolute(preparedResult); absolute(restoreReadsResult); absolute(workflowResult); }
    }
    public record PreparationCompleted(Path composeResult, Path junctionResult, Path offlineResult,
            ExactRef materializedQuote, Completed completed) {
        public PreparationCompleted {
            absolute(composeResult); absolute(junctionResult); absolute(offlineResult);
            Objects.requireNonNull(materializedQuote); Objects.requireNonNull(completed);
        }
    }
    private record MetadataSession(Path directory, RootConsumerProtocol.Binding binding,
            SharedSourceFiles.Witness ready, Instant deadline) { }

    /** Use only when the actual immutable preparation already exists. */
    public static Completed run(Path directory, String machineId, PreparedInput prepared, Instant deadline)
            throws IOException, InterruptedException {
        Objects.requireNonNull(prepared);
        return finish(open(directory, machineId, deadline), prepared, 1);
    }

    /** Complete original preparation before requesting restore reads or the cold workflow. */
    public static PreparationCompleted runPreparation(Path directory, String machineId,
            PreparationInput input, Instant deadline) throws IOException, InterruptedException {
        Objects.requireNonNull(input);
        MetadataSession session = open(directory, machineId, deadline);
        JsonNode composed = consumer(session, 1, new OriginalColdConsumerSession.ComposeBundle(input.planRef()));
        require(composed, "operation", "COMPOSE_BUNDLE");
        requireVerifiedProcess(composed);
        ExactRef quote = ExactRef.fromJson(composed.get("materialized_quote_ref"));
        if (!Path.of(quote.path()).equals(input.quoteOutput()))
            throw new IOException("Actual Java materialization returned another quote path");
        new ControlBuild.FileRef(quote.path(), quote.bytes(), quote.sha256()).verify();
        JsonNode junction = consumer(session, 2, new OriginalColdConsumerSession.PrepareJunction(
                input.planRef(), quote, input.runtimeRoot()));
        require(junction, "operation", "PREPARE_JUNCTION");
        requireJunctionHandoff(junction,machineId);
        requireJavaJunction(session,junction,input,quote);
        SharedSourceFiles.plainAncestors(input.metadataRoot());
        if (!Files.isDirectory(input.metadataRoot(), java.nio.file.LinkOption.NOFOLLOW_LINKS)
                || Files.exists(input.fixtureRoot(), java.nio.file.LinkOption.NOFOLLOW_LINKS))
            throw new IOException("Existing owned metadata root and fresh historical fixture required");
        JsonNode offline = consumer(session, 3, new OriginalColdConsumerSession.PrepareOffline(
                input.planRef(), quote, input.runtimeRoot(), input.metadataRoot(), input.fixtureRoot(),
                input.historicalFixture(), input.attemptNonce(), input.taskNonce()));
        require(offline, "operation", "PREPARE_OFFLINE");
        requireVerifiedProcess(offline);
        Completed completed = finish(session, input.expectedPrepared(), 4);
        return new PreparationCompleted(resultPath(session, 1), resultPath(session, 2),
                resultPath(session, 3), quote, completed);
    }

    private static MetadataSession open(Path directory, String machineId, Instant deadline)
            throws IOException, InterruptedException {
        absolute(directory); StrictJson.text(machineId); Objects.requireNonNull(deadline); checkDeadline(deadline);
        Path readyPath = directory.resolve("session-ready.json");
        JsonNode ready = await(readyPath, deadline);
        require(ready, "schema", "xar.java-closed-partial-root-consumer-session/v1");
        require(ready, "machine_id", machineId); require(ready, "status", "READY");
        Instant serverDeadline = Instant.parse(StrictJson.text(ready.get("deadline_utc")));
        if (deadline.isAfter(serverDeadline)) throw new IOException("Caller exceeds actual Root consumer lease");
        return new MetadataSession(directory, new RootConsumerProtocol.Binding(machineId,
                StrictJson.text(ready.get("session_nonce"))), SharedSourceFiles.observe(readyPath), deadline);
    }

    private static Completed finish(MetadataSession session, PreparedInput input, int sequence)
            throws IOException, InterruptedException {
        input.runtimeRoot().toRealPath();
        JsonNode prepared = consumer(session, sequence, new OriginalColdConsumerSession.Prepared(
                input.runtimeRoot(), input.attemptNonce(), input.taskNonce()));
        require(prepared, "operation", "PREPARED"); requireVerifiedProcess(prepared);
        JsonNode begin = exchange(session, new RootConsumerProtocol.Command(session.binding(), sequence + 1,
                new RootConsumerProtocol.BeginRestoreReads(sequence)));
        require(begin, "operation", "BEGIN_RESTORE_READS"); require(begin, "status", "RESTORE_INPUT_VIEW_REGISTERED");
        StrictJson.integer(begin.get("prepared_sequence"), sequence, sequence);
        JsonNode workflow = exchange(session, new RootConsumerProtocol.Command(session.binding(), sequence + 2,
                new RootConsumerProtocol.OpenColdSession(sequence)));
        require(workflow, "operation", "OPEN_COLD_SESSION"); require(workflow, "status", "COLD_WORKFLOW_RETURNED");
        SharedSourceFiles.assertUnchanged(session.ready());
        RootConsumerProtocol.Close close = new RootConsumerProtocol.Close(session.binding());
        Files.write(session.directory().resolve(close.fileName()), close.wireBytes(), StandardOpenOption.CREATE_NEW);
        return new Completed(resultPath(session, sequence), resultPath(session, sequence + 1),
                resultPath(session, sequence + 2));
    }
    private static JsonNode consumer(MetadataSession session, int sequence,
            OriginalColdConsumerSession.Operation operation) throws IOException, InterruptedException {
        return exchange(session, new RootConsumerProtocol.Command(session.binding(), sequence,
                new RootConsumerProtocol.Consumer(operation)));
    }
    private static Path resultPath(MetadataSession session, int sequence) {
        return session.directory().resolve(String.format(java.util.Locale.ROOT, "%04d.result.json", sequence));
    }
    private static JsonNode exchange(MetadataSession session, RootConsumerProtocol.Command command)
            throws IOException, InterruptedException {
        checkDeadline(session.deadline()); SharedSourceFiles.assertUnchanged(session.ready());
        Files.write(session.directory().resolve(command.fileName()), command.wireBytes(), StandardOpenOption.CREATE_NEW);
        JsonNode result = await(resultPath(session, command.sequence()), session.deadline());
        SharedSourceFiles.assertUnchanged(session.ready());
        require(result, "machine_id", command.binding().machineId());
        require(result, "session_nonce", command.binding().sessionNonce());
        StrictJson.integer(result.get("sequence"), command.sequence(), command.sequence());
        return result;
    }
    private static void requireJavaJunction(MetadataSession session,JsonNode result,
            PreparationInput input,ExactRef quote) throws IOException {
        require(result,"status",CampaignScoreJunction.ROOT_RESULT_STATUS);
        JsonNode processes=result.get("actual_original_processes");
        if(processes==null || !processes.isArray() || !processes.isEmpty() || result.has("original_consumer_ref"))
            throw new IOException("Java junction requires zero compatibility consumer processes");
        ExactRef reference=ExactRef.fromJson(result.get("java_junction_ref"));
        Path expected=resultPath(session,2).resolveSibling("0002.java-junction.json");
        if(!Path.of(reference.path()).equals(expected) || reference.bytes()<1 || reference.bytes()>16_384)
            throw new IOException("Exact same-operation Java junction receipt required");
        SharedSourceFiles.Witness receiptWitness=SharedSourceFiles.observe(expected);
        if(receiptWitness.source().bytes()!=reference.bytes() || !receiptWitness.source().sha256().equals(reference.sha256()))
            throw new IOException("Actual Java junction receipt differs");
        byte[] raw=Files.readAllBytes(expected);
        SharedSourceFiles.assertUnchanged(receiptWitness);
        CampaignScoreJunction.PreparedReceipt receipt=CampaignScoreJunction.PreparedReceipt.decode(raw);
        var quoteWitness=SharedSourceFiles.observe(Path.of(quote.path()));
        if(quoteWitness.source().bytes()!=quote.bytes() || !quoteWitness.source().sha256().equals(quote.sha256()))
            throw new IOException("Actual materialized quote differs");
        byte[] quoteBytes=Files.readAllBytes(Path.of(quote.path()));
        SharedSourceFiles.assertUnchanged(quoteWitness);
        CampaignScoreJunction.Binding binding=CampaignScoreJunction.Binding.decode(
                StrictJson.parse(quoteBytes,MAX_BYTES).get("campaign_score_junction"));
        if(!receipt.machineId().equals(session.binding().machineId()) || receipt.observedAt().isAfter(Instant.now())
                || !receipt.observedAt().isBefore(session.deadline()) || !receipt.binding().equals(binding)
                || !binding.path().equals(input.runtimeRoot().resolve("campaign-score")))
            throw new IOException("Actual Java junction receipt must retain this quote, machine, root and finite observation");
        SharedSourceFiles.assertUnchanged(receiptWitness);
        SharedSourceFiles.assertUnchanged(quoteWitness);
    }
    private static void requireJunctionHandoff(JsonNode result,String machineId) throws IOException {
        JsonNode row=StrictJson.object(result.get("junction_writer_handoff"),java.util.Set.of(
                "schema","machine_id","terminal_path","stdout_path","status","pid","creation_filetime","exit_code",
                "active_processes","peak_job_memory_bytes","ledger_modified","raw_pending_modified","original_actions_replayed"));
        require(row,"schema","xar.java-junction-original-writer-handoff/v1");require(row,"machine_id",machineId);require(row,"status","PASSED");
        absolute(Path.of(StrictJson.text(row.get("terminal_path"))));absolute(Path.of(StrictJson.text(row.get("stdout_path"))));
        StrictJson.integer(row.get("pid"),1,StrictJson.MAX_SAFE_INTEGER);
        String birth=StrictJson.text(row.get("creation_filetime"));
        if(!birth.matches("[1-9][0-9]*") || new java.math.BigInteger(birth).bitLength()>64)
            throw new IOException("Exact original-writer FILETIME string required");
        StrictJson.integer(row.get("exit_code"),0,0);StrictJson.integer(row.get("active_processes"),0,0);
        StrictJson.integer(row.get("peak_job_memory_bytes"),0,StrictJson.MAX_SAFE_INTEGER);
        for(String field:java.util.Set.of("ledger_modified","raw_pending_modified","original_actions_replayed")) {
            JsonNode value=row.get(field);
            if(!value.isBoolean() || value.booleanValue()) throw new IOException("Original writer handoff must preserve "+field);
        }
    }
    private static void requireVerifiedProcess(JsonNode result) throws IOException {
        require(result, "status", "VERIFIED_ORIGINAL_CONSUMER");
        JsonNode jobs = result.get("actual_original_processes");
        if (jobs == null || !jobs.isArray() || jobs.size() != 1)
            throw new IOException("One actual original process terminal required");
        JsonNode job = jobs.get(0); require(job, "status", "PASSED");
        StrictJson.integer(job.get("exit_code"), 0, 0);
        StrictJson.integer(job.get("active_processes"), 0, 0);
    }
    private static JsonNode await(Path path, Instant deadline) throws IOException, InterruptedException {
        for (;;) {
            checkDeadline(deadline); SharedSourceFiles.plainAncestors(path.getParent());
            if (Files.exists(path, java.nio.file.LinkOption.NOFOLLOW_LINKS)) {
                SharedSourceFiles.Witness witness = SharedSourceFiles.observe(path);
                if (witness.source().bytes() < 1 || witness.source().bytes() > MAX_BYTES)
                    throw new IOException("Bounded actual Root metadata required");
                byte[] raw = Files.readAllBytes(path); SharedSourceFiles.assertUnchanged(witness);
                JsonNode result = StrictJson.parse(raw, MAX_BYTES);
                if (!result.isObject()) throw new IOException("Actual Root metadata must be an object");
                return result;
            }
            Thread.sleep(Math.min(50, Math.max(1, java.time.Duration.between(Instant.now(), deadline).toMillis())));
        }
    }
    private static void require(JsonNode value, String field, String expected) throws IOException {
        JsonNode actual = value.get(field);
        if (actual == null || !actual.isTextual() || !expected.equals(actual.textValue()))
            throw new IOException("Actual Root consumer " + field + " rejected");
    }
    private static void checkDeadline(Instant deadline) throws IOException {
        if (!Instant.now().isBefore(deadline)) throw new IOException("Root metadata deadline expired; no request replay");
    }
    private static void absolute(Path path) {
        Objects.requireNonNull(path);
        if (!path.isAbsolute() || !path.normalize().equals(path))
            throw new IllegalArgumentException("Normalized absolute Root path required");
    }
}
