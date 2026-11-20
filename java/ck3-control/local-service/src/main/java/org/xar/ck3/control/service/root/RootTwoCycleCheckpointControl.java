package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Fixed two completed ordinary cycles, then one explicit terminal checkpoint. No decision or Native issuer. */
final class RootTwoCycleCheckpointControl {
    static final String SCHEMA="xar.java-two-selected-cycles-checkpoint-control/v1";
    private static final int MAX=1<<20;
    private static final Set<String> DECLARATION=Set.of("schema","machine_id","session_id","game","watcher_ready",
            "result_path","stop_before_utc","checkpoint_timeout_ms");
    private static final Set<String> TOP=Set.of("schema","at_utc","pid","creation_filetime","config","script_sha256","prefix",
            "actual_configuration","owner_descriptor","machine_id","session_id","game","actually_running_before_Main",
            "maximum_requests","source_started_at_utc","stop_before_utc","source_expires_at_utc","automatic_decision",
            "zero_request_retries","no_Game_pipe_HTTP_writer_API");
    private static final Set<String> CONFIG=Set.of("schema","queue_root","material_root","output_root","prefix",
            "actual_configuration","owner_descriptor","main_begin","main_end","own_stop","source_started_at_utc",
            "stop_before_utc","source_expires_at_utc","maximum_requests");
    private static final Set<String> REVIEW=Set.of("schema","at_utc","pid","creation_filetime","ordinal","request","inspection",
            "payload","original_command","request_id","proposal_id","body_sha256","before","original_file_deadline",
            "original_command_deadline","earliest_deadline","selection_path","requires_current_executor_review",
            "no_automatic_decision","no_deadline_renewal","previous_original_archive_verified");
    private static final Set<String> CYCLE=Set.of("schema","session","basis_cycles","completed_cycles","head","pending_receipt",
            "retained_legacy_pending_digest","origin_frame","episode_origin");

    record Watcher(ExactRef ready,ExactRef config,ExactRef actualConfiguration,ExactRef ownerDescriptor,
            Path output,Path queue,Path materials,Path mainEnd,Path ownStop,long pid,String birth,int maximumRequests,
            Instant started,Instant stop,Instant expires) { }
    record Declaration(ExactRef original,String machine,String session,byte[] game,Watcher watcher,
            Path result,Instant stop,Duration checkpointTimeout) {
        Declaration {game=game.clone();}
        @Override public byte[] game(){return game.clone();}
    }
    record SelectedInput(int ordinal,String requestId,ExactRef request,ExactRef command,ExactRef response,
            ExactRef archive,ExactRef attempt,Instant created,Instant fileDeadline,Instant archivedAt,RootSelectedCheckpointControl.Selected selected) { }
    record Completed(SelectedInput input,ExactRef receipt,ExactRef cycleRecord,ExactRef head,CompletedCycleProof proof) { }

    static boolean accepts(ExactRef original)throws IOException {
        return SCHEMA.equals(StrictJson.text(StrictJson.parse(readExact(original,65536),65536).get("schema")));
    }
    static Declaration read(ExactRef original,Clock clock)throws IOException {
        ObjectNode row=StrictJson.object(StrictJson.parse(readExact(original,65536),65536),DECLARATION);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"explicit fixed two-cycle checkpoint schema required");
        String machine=StrictJson.text(row.get("machine_id")),session=StrictJson.text(row.get("session_id"));
        byte[] game=game(row.get("game"));
        var watcher=watcher(ExactRef.fromJson(row.get("watcher_ready")),machine,session,game);
        Path result=absolute(row.get("result_path"));
        Instant stop=Instant.parse(StrictJson.text(row.get("stop_before_utc")));
        long timeout=StrictJson.integer(row.get("checkpoint_timeout_ms"),1,120000);
        StrictJson.require(!watcher.started().isAfter(clock.instant())&&clock.instant().isBefore(stop)&&!stop.isAfter(watcher.stop()),"two-cycle stop must narrow the original watcher source");
        StrictJson.require(result.getParent()!=null&&Files.isDirectory(result.getParent(),LinkOption.NOFOLLOW_LINKS)
                &&!Files.isSymbolicLink(result.getParent())&&!Files.exists(result,LinkOption.NOFOLLOW_LINKS)
                &&!result.startsWith(watcher.output())&&!result.startsWith(watcher.queue())&&!result.startsWith(watcher.materials()),
                "fresh external two-cycle result target required");
        return new Declaration(original,machine,session,game,watcher,result,stop,Duration.ofMillis(timeout));
    }
    /** Independent Main originals, never request self-identification. No current Root/Game role is created. */
    static void requireMainInputs(Declaration declaration,ExactRef actualOwner,ExactRef actualConfiguration,int maximumTurns) {
        StrictJson.require(declaration.watcher().ownerDescriptor().equals(actualOwner)
                &&declaration.watcher().actualConfiguration().equals(actualConfiguration),
                "two-cycle watcher differs from the actual Main owner/config originals");
        StrictJson.require(maximumTurns==1,"only the explicit two-cycle variant requires one turn per batch");
    }
    private static Watcher watcher(ExactRef original,String machine,String session,byte[] expectedGame)throws IOException {
        ObjectNode top=StrictJson.object(StrictJson.parse(readExact(original,65536),65536),TOP);
        StrictJson.require("ck3.multi-original-review-watcher-running/v2".equals(StrictJson.text(top.get("schema")))
                &&machine.equals(StrictJson.text(top.get("machine_id")))&&session.equals(StrictJson.text(top.get("session_id")))
                &&Arrays.equals(expectedGame,game(top.get("game"))),"watcher top crossed its actual owner");
        requireBoolean(top,"actually_running_before_Main",true);requireBoolean(top,"automatic_decision",false);
        requireBoolean(top,"zero_request_retries",true);requireBoolean(top,"no_Game_pipe_HTTP_writer_API",true);
        long pid=StrictJson.integer(top.get("pid"),1,0xffffffffL);String birth=decimal(top.get("creation_filetime"));
        int maximum=Math.toIntExact(StrictJson.integer(top.get("maximum_requests"),3,64));
        ExactRef cfg=ExactRef.fromJson(top.get("config"));
        ObjectNode config=StrictJson.object(StrictJson.parse(readExact(cfg,65536),65536),CONFIG);
        StrictJson.require("ck3.multi-original-review-watch/v2".equals(StrictJson.text(config.get("schema")))
                &&StrictJson.integer(config.get("maximum_requests"),3,64)==maximum,"watcher must remain alive after its second archive");
        ExactRef actual=ExactRef.fromJson(top.get("actual_configuration")),owner=ExactRef.fromJson(top.get("owner_descriptor"));
        StrictJson.require(actual.equals(ExactRef.fromJson(config.get("actual_configuration")))
                &&owner.equals(ExactRef.fromJson(config.get("owner_descriptor")))
                &&ExactRef.fromJson(top.get("prefix")).equals(ExactRef.fromJson(config.get("prefix"))),"watcher input originals differ");
        var main=StrictJson.parse(readExact(actual,MAX),MAX);var owned=StrictJson.parse(readExact(owner,MAX),MAX);
        StrictJson.require("xar.java-ordinary-runtime-configuration/v1".equals(StrictJson.text(main.get("schema")))
                &&"xar.java-game-supervisor-owner/v1".equals(StrictJson.text(owned.get("schema")))
                &&machine.equals(StrictJson.text(main.get("machine_id")))&&machine.equals(StrictJson.text(owned.get("machine_id")))
                &&session.equals(StrictJson.text(owned.get("session_id"))),"independent Main/owner identity differs");
        ObjectNode ownerGame=StrictJson.object(owned.get("game"),Set.of("pid","creation_filetime","executable"));
        ObjectNode projected=StrictJson.object();projected.set("pid",ownerGame.get("pid"));projected.set("creation_filetime",ownerGame.get("creation_filetime"));
        StrictJson.require(Arrays.equals(expectedGame,game(projected)),"watcher Game differs from actual Main owner metadata");
        Path output=absolute(config.get("output_root"));
        StrictJson.require(Path.of(original.path()).getParent().equals(output),"watcher top must be its actual output root");
        Path queue=absolute(config.get("queue_root"));var provider=main.get("decision_provider");
        StrictJson.require(provider!=null&&"codex-session".equals(StrictJson.text(provider.get("model")))
                &&Path.of(java.net.URI.create(StrictJson.text(provider.get("endpoint")))).equals(queue),
                "watcher queue must be the actual Main file decision endpoint");
        Instant started=Instant.parse(StrictJson.text(top.get("source_started_at_utc"))),stop=Instant.parse(StrictJson.text(top.get("stop_before_utc"))),
                expires=Instant.parse(StrictJson.text(top.get("source_expires_at_utc")));
        StrictJson.require(started.equals(Instant.parse(StrictJson.text(config.get("source_started_at_utc"))))
                &&stop.equals(Instant.parse(StrictJson.text(config.get("stop_before_utc"))))
                &&expires.equals(Instant.parse(StrictJson.text(config.get("source_expires_at_utc"))))
                &&started.isBefore(stop)&&!stop.isAfter(expires)&&Duration.between(started,expires).compareTo(Duration.ofMinutes(45))<=0,
                "one original nonrenewed watcher source window required");
        var ownerPlan=owned.get("configuration");
        StrictJson.require(session.equals(StrictJson.text(ownerPlan.get("session_id")))
                &&machine.equals(StrictJson.text(ownerPlan.get("review").get("machine_id")))
                &&!expires.isAfter(Instant.parse(StrictJson.text(ownerPlan.get("deadline"))))
                &&!expires.isAfter(Instant.parse(StrictJson.text(ownerPlan.get("review").get("expires_at")))),
                "two-cycle source cannot extend the actual owner plan/review deadline");
        return new Watcher(original,cfg,actual,owner,output,queue,absolute(config.get("material_root")),
                absolute(config.get("main_end")),absolute(config.get("own_stop")),pid,birth,maximum,started,stop,expires);
    }
    private final Declaration declaration;
    private final RootSessionAccess access;
    private final RootApplicationSession originalRoot;
    private final Clock clock;
    private final long baseline,monotonicStop;
    private final List<Completed> completed=new ArrayList<>(2);
    private volatile boolean finished;
    private boolean saveAttempted;

    RootTwoCycleCheckpointControl(Declaration declaration,RootSessionAccess access,Clock clock)throws IOException {
        this.declaration=Objects.requireNonNull(declaration);this.access=Objects.requireNonNull(access);this.clock=Objects.requireNonNull(clock);
        requireSource();originalRoot=access.current();requireOwner(originalRoot);
        StrictJson.require(!originalRoot.controllerForPublication().isRunning(),"two-cycle boundary binds only before the same Root worker");
        baseline=originalRoot.writer().locked(same->completedCount(same.head().state(),originalRoot.identity()));
        long remaining=Duration.between(clock.instant(),declaration.stop()).toNanos();
        StrictJson.require(remaining>0,"original two-cycle source stop exhausted");monotonicStop=System.nanoTime()+remaining;
    }
    boolean finished(){return finished;}
    boolean stopRequested(){return finished||!clock.instant().isBefore(declaration.stop())||monotonicStop-System.nanoTime()<=0
            ||Files.exists(declaration.watcher().output().resolve("WATCHER.END.json"))
            ||Files.exists(declaration.watcher().mainEnd())||Files.exists(declaration.watcher().ownStop());}
    private void requireSource()throws IOException {
        readExact(declaration.original(),65536);
        var current=watcher(declaration.watcher().ready(),declaration.machine(),declaration.session(),declaration.game());
        StrictJson.require(current.equals(declaration.watcher())&&clock.instant().isBefore(declaration.stop())
                &&!Files.exists(current.output().resolve("WATCHER.END.json"))&&!Files.exists(current.mainEnd())&&!Files.exists(current.ownStop()),
                "two-cycle source or global stream is terminal; never waive END for checkpoint");
    }
    private void requireOwner(RootApplicationSession root) {
        StrictJson.require(root.identity().machineId().equals(declaration.machine())&&root.identity().sessionId().equals(declaration.session())
                &&Arrays.equals(declaration.game(),StrictJson.canonical(root.identity().game().toJson())),"two-cycle Root crossed the actual Main/Game/session");
    }
    static long completedCount(ContinuityState state,SessionIdentity owner) {
        StrictJson.require(state.machineId().equals(owner.machineId())&&!(state.pendingCycle() instanceof ContinuityState.Present),
                "current canonical cycle baseline cannot contain a pending original");
        var value=state.toJson().get(OrdinaryCycleTransitions.STATE_FIELD);
        if(value==null)return state.settledCycles();
        var cycle=StrictJson.object(value,CYCLE);
        StrictJson.require("xar.java-ordinary-cycle-state/v2".equals(StrictJson.text(cycle.get("schema")))
                &&OrdinaryCycleTransitions.sessionFromJson(cycle.get("session")).equals(owner)&&cycle.get("pending_receipt").isNull(),
                "canonical cycle baseline belongs to another owner or pending receipt");
        return StrictJson.integer(cycle.get("completed_cycles"),state.settledCycles(),StrictJson.MAX_SAFE_INTEGER);
    }
    static ActionReceipt matched(BatchReport report,RootSelectedCheckpointControl.Selected selected) {
        StrictJson.require(selected.decision().equals("SELECT_PROPOSAL")&&report.terminal()==BatchReport.Terminal.TURN_BOUND
                &&report.turns().size()==1,"two-cycle boundary needs one selected actual completed ordinary turn");
        var turn=report.turns().getFirst();var receipt=turn.receipt();
        StrictJson.require(receipt.command().equals(selected.original())&&receipt.command().actionId().equals(selected.actionId())
                &&receipt.bodySha256().equals(selected.bodySha256())&&receipt.settled()
                &&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&receipt.applied().isPresent()
                &&receipt.visibleGameplay()&&turn.facts().visibleGameplay()&&report.committedLedgerHead().isPresent(),
                "response publication or an unrelated/ACK-only report is not the selected applied post");
        return receipt;
    }
    /** DATA comparison only. Production obtains proof and record exclusively from the identical current canonical writer. */
    static void requireCompletedData(ActionReceipt receipt,SessionIdentity owner,CompletedCycleProof proof,long expected,
            ExactRef actualReceipt,JsonNode record) {
        var row=StrictJson.object(record,Set.of("schema","session","receipt_ref","semantic","previous","completed_cycles","classification"));
        StrictJson.require("xar.java-ordinary-cycle-record/v1".equals(StrictJson.text(row.get("schema")))
                &&OrdinaryCycleTransitions.sessionFromJson(row.get("session")).equals(owner)
                &&ExactRef.fromJson(row.get("receipt_ref")).equals(actualReceipt)
                &&proof.completedCycles()==expected&&StrictJson.integer(row.get("completed_cycles"),0,StrictJson.MAX_SAFE_INTEGER)==expected
                &&OrdinaryCycleTransitions.semanticFromJson(row.get("semantic")).equals(proof.semantic())
                &&Set.of("VISIBLE_GAMEPLAY","ELIGIBLE_ADVANCE").contains(StrictJson.text(row.get("classification"))),
                "actual cycle head must be this selected receipt and exactly one new completed cycle");
        var post=receipt.applied().orElseThrow().observation();var frame=proof.frame();
        StrictJson.require(receipt.command().sessionId().equals(owner.sessionId())
                &&receipt.command().origin().machineId().equals(owner.machineId())&&receipt.command().origin().game().equals(owner.game())
                &&post.source().equals(receipt.command().source())&&post.sessionId().equals(owner.sessionId())
                &&frame.machineId().equals(owner.machineId())&&frame.game().equals(owner.game())
                &&frame.frame().identity().player().equals(post.after().frame().identity().player())
                &&frame.frame().episodeRunId().equals(post.after().frame().episodeRunId())
                &&proof.semantic().observedAt().isAfter(post.observedAt())
                &&frame.frame().identity().nativeRevision().compareTo(post.after().frame().identity().nativeRevision())>=0
                &&frame.frame().identity().dateRaw().compareTo(post.after().frame().identity().dateRaw())>=0,
                "retained after-SEM must really follow the selected post in the same Game/actor/episode");
    }
    private SelectedInput selected(int ordinal)throws IOException {
        var watch=declaration.watcher();Path requests=watch.output().resolve("requests");
        List<Path> paths;
        try(var stream=Files.newDirectoryStream(requests,String.format("%04d-codex-*",ordinal))){
            paths=new ArrayList<>();for(Path path:stream){if(paths.size()>=2)throw new IOException("ambiguous original ordinal");paths.add(path);}
        }
        StrictJson.require(paths.size()==1,"actual ordinal response is absent");Path directory=paths.getFirst();
        StrictJson.require(!Files.isSymbolicLink(directory)&&directory.toRealPath().equals(directory)
                &&directory.getFileName().toString().matches(String.format("%04d-",ordinal)+"codex-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"),"plain actual ordinal directory required");
        ObjectNode review=StrictJson.object(StrictJson.parse(readPath(directory.resolve("REVIEW.READY.json"),65536),65536),REVIEW);
        String id=StrictJson.text(review.get("request_id"));
        StrictJson.require("ck3.multi-original-codex-review-required/v2".equals(StrictJson.text(review.get("schema")))
                &&StrictJson.integer(review.get("ordinal"),1,2)==ordinal&&directory.getFileName().toString().equals(String.format("%04d-",ordinal)+id)
                &&StrictJson.integer(review.get("pid"),1,0xffffffffL)==watch.pid()&&decimal(review.get("creation_filetime")).equals(watch.birth())
                &&absolute(review.get("selection_path")).equals(directory.resolve("selection.json")),"review crossed its one actual watcher/ordinal");
        requireBoolean(review,"requires_current_executor_review",true);requireBoolean(review,"no_automatic_decision",true);
        requireBoolean(review,"no_deadline_renewal",true);requireBoolean(review,"previous_original_archive_verified",ordinal>1);
        ExactRef request=ExactRef.fromJson(review.get("request")),command=ExactRef.fromJson(review.get("original_command"));
        StrictJson.require(Path.of(request.path()).equals(watch.queue().resolve(id).resolve("request.json"))
                &&Path.of(command.path()).startsWith(watch.materials()),"review source is outside its actual queue/material roots");
        var envelope=StrictJson.parse(readExact(request,16384),16384);
        var old=new RootSelectedCheckpointControl.Declaration(declaration.machine(),declaration.session(),declaration.game(),
                directory.resolve("respond.stdout"),declaration.result(),declaration.stop(),declaration.checkpointTimeout());
        var selected=RootSelectedCheckpointControl.selected(old);
        StrictJson.require(id.equals(StrictJson.text(envelope.get("request_id")))&&selected.actionId().equals(StrictJson.text(review.get("proposal_id")))
                &&selected.bodySha256().equals(StrictJson.text(review.get("body_sha256")))
                &&command.equals(ExactRef.fromJson(envelope.get("original_command")))
                &&ExactRef.fromJson(review.get("payload")).equals(ExactRef.fromJson(envelope.get("payload")))
                &&Arrays.equals(StrictJson.canonical(review.get("before")),StrictJson.canonical(envelope.get("before")))
                &&Arrays.equals(StrictJson.canonical(envelope.get("before")),StrictJson.canonical(ProposalLifecycleCodec.observation(selected.original().before()))),
                "review crossed its selected original command/before/payload");
        var inspection=StrictJson.parse(readExact(ExactRef.fromJson(review.get("inspection")),262144),262144);
        StrictJson.require("xar.ordinary-codex-session-inspection/v1".equals(StrictJson.text(inspection.get("schema")))
                &&request.equals(ExactRef.fromJson(inspection.get("request")))&&command.equals(ExactRef.fromJson(inspection.get("original_command")))
                &&Arrays.equals(StrictJson.canonical(inspection.get("before")),StrictJson.canonical(envelope.get("before"))),
                "original public inspection differs from the completed selected command");
        var publication=StrictJson.parse(readPath(directory.resolve("respond.stdout"),262144),262144);
        ExactRef response=ExactRef.fromJson(publication.get("response"));
        var archive=StrictJson.object(StrictJson.parse(readPath(watch.queue().resolve(id).resolve("archived.json"),16384),16384),
                Set.of("schema","request_id","request_sha256","observed_at_utc","attempt","request_pin","response_pin"));
        StrictJson.require("xar.ordinary-codex-file-archived/v2".equals(StrictJson.text(archive.get("schema")))
                &&id.equals(StrictJson.text(archive.get("request_id")))&&request.sha256().equals(StrictJson.text(archive.get("request_sha256")))
                &&ExactRef.fromJson(archive.get("request_pin").get("ref")).equals(request)
                &&ExactRef.fromJson(archive.get("response_pin").get("ref")).equals(response),"actual archive consumed another original request/response");
        ExactRef attempt=ExactRef.fromJson(archive.get("attempt"));
        StrictJson.require(Path.of(attempt.path()).startsWith(watch.materials()),"actual attempt is outside the source material root");
        var actualAttempt=StrictJson.parse(readExact(attempt,MAX),MAX);
        StrictJson.require("xar.ordinary-codex-file-attempt/v1".equals(StrictJson.text(actualAttempt.get("schema")))
                &&declaration.machine().equals(StrictJson.text(actualAttempt.get("machine_id")))
                &&StrictJson.integer(actualAttempt.get("attempt"),1,1)==1
                &&Base64.getDecoder().decode(StrictJson.text(actualAttempt.get("request_wire_base64"))).length==request.bytes(),
                "actual source attempt differs");
        requireBoolean(actualAttempt,"complete",true);
        StrictJson.require(actualAttempt.get("failure").isTextual()&&actualAttempt.get("failure").textValue().isEmpty()
                &&Arrays.equals(Base64.getDecoder().decode(StrictJson.text(actualAttempt.get("request_wire_base64"))),readExact(request,16384))
                &&Arrays.equals(Base64.getDecoder().decode(StrictJson.text(actualAttempt.get("wire_base64"))),readExact(response,262144)),
                "actual selected attempt is incomplete or its original wire changed");
        Instant created=Instant.parse(StrictJson.text(envelope.get("created_at_utc"))),fileDeadline=Instant.parse(StrictJson.text(envelope.get("deadline_utc")));
        StrictJson.require(created.isBefore(fileDeadline)&&Duration.between(created,fileDeadline).compareTo(Duration.ofSeconds(120))<=0
                &&fileDeadline.equals(Instant.parse(StrictJson.text(review.get("original_file_deadline"))))
                &&selected.original().deadline().equals(Instant.parse(StrictJson.text(review.get("original_command_deadline")))),"original decision deadlines changed");
        Instant earliest=fileDeadline.isBefore(selected.original().deadline())?fileDeadline:selected.original().deadline();
        if(watch.stop().isBefore(earliest))earliest=watch.stop();
        StrictJson.require(earliest.equals(Instant.parse(StrictJson.text(review.get("earliest_deadline")))),"original min-deadline differs");
        var archivedAt=Instant.parse(StrictJson.text(archive.get("observed_at_utc")));
        if(ordinal==2){var first=completed.getFirst().input();
            StrictJson.require(!id.equals(first.requestId())&&!selected.actionId().equals(first.selected().actionId())
                    &&!selected.bodySha256().equals(first.selected().bodySha256())&&!created.isBefore(first.archivedAt()),
                    "second request must be independently minted after the first real archive, never a replay");}
        return new SelectedInput(ordinal,id,request,command,response,measure(watch.queue().resolve(id).resolve("archived.json"),16384),
                attempt,created,fileDeadline,archivedAt,selected);
    }
    void afterBatch(BatchReport actual)throws IOException,InterruptedException {
        if(finished)return;
        ObjectNode result=StrictJson.object().put("schema","xar.java-two-selected-cycles-checkpoint-result/v1")
                .put("observed_at_utc",clock.instant().toString()).put("annual_checkpoint_policy_changed",false)
                .put("save_attempted",false).put("physical_save_confirmed",false);
        try {
            requireSource();StrictJson.require(!stopRequested(),"original source boundary ended");
            int ordinal=completed.size()+1;var selected=selected(ordinal);
            if(!selected.selected().decision().equals("SELECT_PROPOSAL")){finish(result.put("status","WAIT_CONSUMED_NO_TERMINAL_CHECKPOINT"));return;}
            ActionReceipt receipt=matched(actual,selected.selected());
            Completed evidence=access.withCurrent(root->{
                StrictJson.require(root==originalRoot,"two-cycle checkpoint cannot follow another Root or restored host");requireOwner(root);
                var controller=root.controllerForPublication();
                StrictJson.require(!controller.isRunning()&&!controller.isRetired()&&!controller.isQuarantined()
                        &&controller.lastReport().filter(value->value==actual).isPresent()
                        &&controller.lastBatchBoundary().filter(boundary->boundary.batchId().equals(actual.batchId())
                            &&boundary.session().equals(actual.session())&&!boundary.pendingAction()).isPresent()
                        &&actual.session().equals(root.identity()),"only this actual completed batch may supply the selected cycle");
                var proof=root.batchJournal().retainedCycleProof(root.identity()).orElseThrow(()->new IOException("real retained completed-cycle proof is absent"));
                long expected=Math.addExact(baseline,ordinal);
                return root.writer().locked(same->{
                    var head=same.head();root.cycles().verifyHistoricalCompletedCycleProof(same,root.identity(),proof,head.state());
                    var archive=root.archive().withSession(same);var reference=archive.receiptReferenceOf(receipt);
                    StrictJson.require(archive.loadReceipt(reference).equals(receipt),"selected result differs from its actual canonical receipt");
                    var cycle=StrictJson.object(head.state().toJson().get(OrdinaryCycleTransitions.STATE_FIELD),CYCLE);
                    ExactRef record=ExactRef.fromJson(cycle.get("head"));
                    requireCompletedData(receipt,root.identity(),proof,expected,reference,StrictJson.parse(archive.loadMaterial(record).bytes(),MAX));
                    StrictJson.require(completedCount(head.state(),root.identity())==expected,"canonical completed count changed");
                    return new Completed(selected,reference,record,same.persistedHead(),proof);
                });
            });
            completed.add(evidence);
            if(completed.size()==1)return; // Same Main/Game/Root and dirty frontier continue; no checkpoint or stop here.
            requireSource();StrictJson.require(!stopRequested()&&!saveAttempted,"one terminal checkpoint only after both actual cycles");saveAttempted=true;
            Instant until=clock.instant().plus(declaration.checkpointTimeout());if(declaration.stop().isBefore(until))until=declaration.stop();
            StrictJson.require(clock.instant().isBefore(until),"original source stop leaves no new checkpoint window");
            final Instant deadline=until;result.put("save_attempted",true).put("new_checkpoint_deadline",until.toString());
            // Every canonical proof/writer scope above has ended before the public SAVE acquires its original call lock.
            var call=access.withCurrent(root->{requireSource();StrictJson.require(!stopRequested()&&root==originalRoot,"terminal checkpoint changed its actual Root/source");requireOwner(root);
                return root.saveCheckpointPublic(new RootCheckpointPublicCalls.Request(new RootCheckpointPublicCalls.MissingRevision()),deadline);});
            call.canonicalReceipt().ifPresent(ref->result.set("canonical_save_receipt",ref.toJson()));
            RootCheckpointPublicCalls.action(call.actual()).ifPresent(action->result.put("new_save_action_id",action.command().actionId())
                    .put("new_save_body_sha256",action.bodySha256()));
            if(call.actual() instanceof CheckpointResult.Confirmed confirmed) {
                StrictJson.require(call.savedDriver().isPresent()&&call.canonicalReceipt().isPresent()
                        &&completed.stream().noneMatch(value->value.input().selected().actionId().equals(confirmed.action().command().actionId())),
                        "terminal confirmation requires a distinct real SAVE, captured Driver and canonical receipt");
                result.put("status","TWO_CYCLES_CANONICAL_TERMINAL_CHECKPOINT_CONFIRMED").put("physical_save_confirmed",true);
                result.set("checkpoint_pair",StrictJson.parse(CheckpointPairCodec.encode(confirmed.pair()),MAX));
            }else if(call.actual() instanceof CheckpointResult.Rejected rejected)result.put("status","TERMINAL_CHECKPOINT_REJECTED").put("reason",rejected.reason());
            else result.put("status","TERMINAL_CHECKPOINT_UNKNOWN").put("reason",((CheckpointResult.Unknown)call.actual()).reason());
            finish(result);
            if(!(call.actual() instanceof CheckpointResult.Confirmed))throw new IOException("terminal checkpoint is not canonically confirmed; retain its original without replay");
        }catch(IOException|InterruptedException|RuntimeException failure) {
            if(!finished)try{finish(result.put("status","TWO_CYCLE_BOUNDARY_FAILED_NO_REPLAY").put("exception_type",failure.getClass().getName()));}
                catch(IOException|RuntimeException writing){failure.addSuppressed(writing);}
            throw failure;
        }
    }
    private void finish(ObjectNode result)throws IOException {
        result.put("completed_cycles_in_this_control",completed.size()).put("canonical_baseline_cycles",baseline);
        var rows=result.putArray("completed");
        for(var value:completed){var row=rows.addObject().put("ordinal",value.input().ordinal()).put("request_id",value.input().requestId())
                .put("action_id",value.input().selected().actionId()).put("body_sha256",value.input().selected().bodySha256())
                .put("original_request_created",value.input().created().toString()).put("original_file_deadline",value.input().fileDeadline().toString())
                .put("original_command_deadline",value.input().selected().original().deadline().toString())
                .put("completed_cycles",value.proof().completedCycles()).put("cycle_state_digest",value.proof().cycleStateDigest());
            row.set("request",value.input().request().toJson());row.set("actual_attempt",value.input().attempt().toJson());
            row.set("canonical_receipt",value.receipt().toJson());row.set("cycle_record",value.cycleRecord().toJson());
            row.set("canonical_head",value.head().toJson());row.set("after_semantic",OrdinaryCycleTransitions.semanticToJson(value.proof().semantic()));}
        byte[] bytes=StrictJson.canonical(result,MAX);Path target=declaration.result();
        Path temporary=target.resolveSibling(".two-cycle-"+UUID.randomUUID()+".tmp");
        try {
            Files.write(temporary,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            try(var output=FileChannel.open(temporary,StandardOpenOption.WRITE)){output.force(true);}
            Files.createLink(target,temporary); // Complete immutable publication; never overwrite or fall back.
            finished=true;
        }finally{Files.deleteIfExists(temporary);}
    }
    private static void requireBoolean(JsonNode node,String field,boolean expected) {
        StrictJson.require(node.has(field)&&node.get(field).isBoolean()&&node.get(field).booleanValue()==expected,"explicit boolean differs: "+field);
    }
    private static String decimal(JsonNode value) {
        String actual=StrictJson.text(value);StrictJson.require(actual.matches("[1-9][0-9]{0,19}")
                &&new java.math.BigInteger(actual).bitLength()<=64,"canonical positive uint64 decimal string required");return actual;
    }
    private static byte[] game(JsonNode value) {
        var row=StrictJson.object(value,Set.of("pid","creation_filetime"));StrictJson.integer(row.get("pid"),1,0xffffffffL);decimal(row.get("creation_filetime"));
        return StrictJson.canonical(row);
    }
    private static Path absolute(JsonNode value) {
        Path path=Path.of(StrictJson.text(value));StrictJson.require(path.isAbsolute()&&path.normalize().equals(path),"absolute normalized control path required");return path;
    }
    private static ExactRef measure(Path path,int maximum)throws IOException {byte[] raw=readPath(path,maximum);return new ExactRef(path.toString(),raw.length,ActionCodec.sha256(raw));}
    private static byte[] readExact(ExactRef source,int maximum)throws IOException {
        StrictJson.require(source.bytes()>0&&source.bytes()<=maximum,"bounded original required");byte[] raw=readPath(Path.of(source.path()),maximum);
        StrictJson.require(raw.length==source.bytes()&&ActionCodec.sha256(raw).equals(source.sha256()),"control original changed");return raw;
    }
    private static byte[] readPath(Path path,int maximum)throws IOException {
        if(!path.isAbsolute()||!path.normalize().equals(path)||Files.isSymbolicLink(path)||!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("plain absolute control original required");
        try(var input=Files.newInputStream(path)){byte[] raw=input.readNBytes(maximum+1);if(raw.length==0||raw.length>maximum)throw new IOException("bounded control original required");return raw;}
    }
}
