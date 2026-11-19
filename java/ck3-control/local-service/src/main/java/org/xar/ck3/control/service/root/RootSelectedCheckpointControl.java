package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit single-selection diagnostic control. The original annual checkpoint policy is unchanged. */
final class RootSelectedCheckpointControl {
    private static final int MAX=1<<20;
    record Declaration(String machineId,String sessionId,byte[] game,Path publishedResponse,Path result,
            Instant stopBefore,Duration checkpointTimeout) {
        Declaration {
            StrictJson.text(machineId);StrictJson.text(sessionId);game=Objects.requireNonNull(game).clone();
            Objects.requireNonNull(publishedResponse);Objects.requireNonNull(result);Objects.requireNonNull(stopBefore);Objects.requireNonNull(checkpointTimeout);
            StrictJson.require(publishedResponse.isAbsolute()&&publishedResponse.normalize().equals(publishedResponse)
                    &&result.isAbsolute()&&result.normalize().equals(result)&&!publishedResponse.equals(result),"absolute distinct diagnostic control paths required");
            StrictJson.require(!checkpointTimeout.isNegative()&&!checkpointTimeout.isZero()
                    &&checkpointTimeout.compareTo(Duration.ofMinutes(2))<=0,"finite new checkpoint timeout required");
        }
        @Override public byte[] game(){return game.clone();}
    }
    static Declaration read(ExactRef original,Clock clock)throws IOException {
        var value=StrictJson.object(StrictJson.parse(readExact(original,MAX)),Set.of("schema","machine_id","session_id","game",
                "response_published_path","result_path","stop_before_utc","checkpoint_timeout_ms"));
        StrictJson.require("xar.java-single-selected-checkpoint-control/v1".equals(StrictJson.text(value.get("schema"))),"single selected checkpoint control schema required");
        var game=StrictJson.object(value.get("game"),Set.of("pid","creation_filetime"));
        StrictJson.require(game.get("pid").isIntegralNumber()&&game.get("pid").canConvertToLong()&&game.get("pid").longValue()>0
                &&StrictJson.text(game.get("creation_filetime")).matches("[0-9]{1,20}"),"actual Game generation required");
        var timeout=value.get("checkpoint_timeout_ms");
        StrictJson.require(timeout.isIntegralNumber()&&timeout.canConvertToLong()&&timeout.longValue()>0&&timeout.longValue()<=120000,"bounded new SAVE deadline required");
        var stop=Instant.parse(StrictJson.text(value.get("stop_before_utc")));
        StrictJson.require(clock.instant().isBefore(stop)&&!stop.isAfter(clock.instant().plus(Duration.ofMinutes(45))),"original finite source stop required");
        return new Declaration(StrictJson.text(value.get("machine_id")),StrictJson.text(value.get("session_id")),StrictJson.canonical(game),
                Path.of(StrictJson.text(value.get("response_published_path"))),Path.of(StrictJson.text(value.get("result_path"))),stop,Duration.ofMillis(timeout.longValue()));
    }
    private final Declaration declaration;
    private final RootSessionAccess actualAccess;
    private final Clock clock;
    private boolean finished,attempted;
    RootSelectedCheckpointControl(Declaration declaration,RootSessionAccess actualAccess,Clock clock) {
        this.declaration=Objects.requireNonNull(declaration);this.actualAccess=Objects.requireNonNull(actualAccess);this.clock=Objects.requireNonNull(clock);
    }
    boolean finished(){return finished;}
    record Selected(String actionId,String bodySha256,ActionCommand original,String decision) { }
    /** Read only already published original response DATA, without extending its old decision deadline. */
    static Selected selected(Declaration declaration)throws IOException {
        var published=StrictJson.object(StrictJson.parse(readPath(declaration.publishedResponse(),262144)),Set.of("provider","schema","response"));
        StrictJson.require("codex-session".equals(StrictJson.text(published.get("provider")))
                &&"xar.ordinary-codex-session-response-published/v1".equals(StrictJson.text(published.get("schema"))),"actual public response publication required");
        var responseRef=ExactRef.fromJson(published.get("response"));
        var response=StrictJson.object(StrictJson.parse(readExact(responseRef,262144)),Set.of("schema","request_id","request_sha256","selection"));
        StrictJson.require("xar.ordinary-codex-file-response/v1".equals(StrictJson.text(response.get("schema"))),"actual file response required");
        var selection=StrictJson.object(response.get("selection"),Set.of("decision","proposal_id","body_sha256","reason"));
        String decision=StrictJson.text(selection.get("decision"));StrictJson.require(Set.of("SELECT_PROPOSAL","WAIT").contains(decision),"original decision required");
        Path requestPath=Path.of(responseRef.path()).getParent().resolve("request.json");byte[] requestRaw=readPath(requestPath,16384);
        StrictJson.require(ActionCodec.sha256(requestRaw).equals(StrictJson.text(response.get("request_sha256"))),"response changed its original request");
        var request=StrictJson.parse(requestRaw,16384);
        StrictJson.require(StrictJson.text(response.get("request_id")).equals(StrictJson.text(request.get("request_id")))
                &&declaration.machineId().equals(StrictJson.text(request.get("machine_id"))),"selected request identity changed");
        var commandRef=ExactRef.fromJson(request.get("original_command"));var command=ActionCodec.decodeCommand(readExact(commandRef,MAX));
        String id=StrictJson.text(selection.get("proposal_id")),body=StrictJson.text(selection.get("body_sha256"));
        StrictJson.require(id.equals(command.actionId())&&body.equals(ActionCodec.bodySha256(command))&&body.equals(commandRef.sha256())
                &&id.equals(StrictJson.text(request.get("proposal_id")))&&body.equals(StrictJson.text(request.get("body_sha256")))
                &&declaration.machineId().equals(command.origin().machineId())&&declaration.sessionId().equals(command.sessionId())
                &&Arrays.equals(declaration.game(),StrictJson.canonical(command.origin().game().toJson())),"selection crossed original command/body/Game/session");
        return new Selected(id,body,command,decision);
    }
    static boolean eligible(BatchReport report,Selected selected) {
        if(!selected.decision().equals("SELECT_PROPOSAL")||report.terminal()!=BatchReport.Terminal.TURN_BOUND)return false;
        var matches=report.turns().stream().filter(turn->turn.receipt().command().actionId().equals(selected.actionId())
                &&turn.receipt().bodySha256().equals(selected.bodySha256())).toList();
        if(matches.size()!=1)return false;
        var turn=matches.getFirst();var receipt=turn.receipt();
        return receipt.command().equals(selected.original())&&receipt.settled()&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                &&receipt.command().operation().value().equals("life-advance")&&receipt.eligibleAdvance()
                &&turn.facts().visibleGameplay()&&turn.facts().eligibleAdvance()&&report.committedLedgerHead().isPresent();
    }
    void afterBatch(BatchReport actual)throws IOException,InterruptedException {
        if(finished||!Files.exists(declaration.publishedResponse(),LinkOption.NOFOLLOW_LINKS))return;
        var selected=selected(declaration);
        var result=StrictJson.object().put("schema","xar.java-single-selected-checkpoint-result/v1")
                .put("observed_at_utc",clock.instant().toString()).put("selected_action_id",selected.actionId())
                .put("selected_body_sha256",selected.bodySha256()).put("actual_batch_id",actual.batchId())
                .put("actual_batch_terminal",actual.terminal().name()).put("selected_command_original_deadline",selected.original().deadline().toString())
                .put("annual_checkpoint_policy_changed",false).put("save_attempted",false).put("physical_save_confirmed",false);
        if(!selected.decision().equals("SELECT_PROPOSAL")){finish(result.put("status","WAIT_CONSUMED_NO_CHECKPOINT"));return;}
        if(!eligible(actual,selected)){finish(result.put("status","SELECTED_ACTION_NOT_APPLIED_NO_CHECKPOINT"));return;}
        StrictJson.require(!attempted,"one explicit checkpoint attempt only");attempted=true;
        Instant until=clock.instant().plus(declaration.checkpointTimeout());if(declaration.stopBefore().isBefore(until))until=declaration.stopBefore();
        if(!clock.instant().isBefore(until)){finish(result.put("status","SOURCE_STOP_NO_CHECKPOINT"));return;}
        final Instant newSaveDeadline=until;result.put("new_checkpoint_deadline",until.toString()).put("save_attempted",true);
        try {
            var call=actualAccess.withCurrent(root->{
                StrictJson.require(root.identity().machineId().equals(declaration.machineId())&&root.identity().sessionId().equals(declaration.sessionId())
                        &&root.identity().equals(actual.session())&&Arrays.equals(declaration.game(),StrictJson.canonical(root.identity().game().toJson())),
                        "checkpoint requires the same current Root/session/Game as the completed actual batch");
                return root.saveCheckpointPublic(new RootCheckpointPublicCalls.Request(new RootCheckpointPublicCalls.MissingRevision()),newSaveDeadline);
            });
            call.canonicalReceipt().ifPresent(ref->result.set("canonical_save_receipt",ref.toJson()));
            RootCheckpointPublicCalls.action(call.actual()).ifPresent(action->result.put("new_save_action_id",action.command().actionId()).put("new_save_body_sha256",action.bodySha256()));
            if(call.actual() instanceof CheckpointResult.Confirmed confirmed) {
                StrictJson.require(!confirmed.action().command().actionId().equals(selected.actionId())&&call.savedDriver().isPresent()
                        &&call.canonicalReceipt().isPresent(),"new confirmed physical checkpoint needs its actual saved Driver and canonical receipt");
                result.put("status","CANONICAL_CHECKPOINT_CONFIRMED").put("physical_save_confirmed",true)
                        .put("advanced_days",confirmed.advancedDays().toPlainString());
                result.set("checkpoint_pair",StrictJson.parse(CheckpointPairCodec.encode(confirmed.pair()),MAX));
            }else if(call.actual() instanceof CheckpointResult.Rejected rejected)result.put("status","CANONICAL_CHECKPOINT_REJECTED").put("reason",rejected.reason());
            else result.put("status","CANONICAL_CHECKPOINT_UNKNOWN").put("reason",((CheckpointResult.Unknown)call.actual()).reason());
            finish(result);
        } catch(IOException|InterruptedException|RuntimeException failure) {
            finish(result.put("status","CHECKPOINT_CALL_FAILED").put("exception_type",failure.getClass().getName()));throw failure;
        }
    }
    private void finish(ObjectNode result)throws IOException {
        finished=true;Files.write(declaration.result(),StrictJson.canonical(result),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
    }
    private static byte[] readExact(ExactRef source,int maximum)throws IOException {
        StrictJson.require(source.bytes()>0&&source.bytes()<=maximum,"bounded diagnostic original required");
        byte[] raw=readPath(Path.of(source.path()),maximum);
        StrictJson.require(raw.length==source.bytes()&&ActionCodec.sha256(raw).equals(source.sha256()),"diagnostic original changed");return raw;
    }
    private static byte[] readPath(Path path,int maximum)throws IOException {
        if(!path.isAbsolute()||!path.normalize().equals(path)||Files.isSymbolicLink(path)
                ||!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("plain absolute diagnostic original required");
        try(var stream=Files.newInputStream(path)) {
            byte[] raw=stream.readNBytes(maximum+1);if(raw.length==0||raw.length>maximum)throw new IOException("diagnostic original exceeds role bound");return raw;
        }
    }
}
