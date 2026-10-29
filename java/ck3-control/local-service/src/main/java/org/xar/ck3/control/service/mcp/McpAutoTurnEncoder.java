package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SuccessorUiContinuationJson;
import org.xar.ck3.control.application.session.SessionController.TurnReport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual one-turn application report -> original status/plan/result wire, never the private HTTP batch summary. */
public final class McpAutoTurnEncoder {
    public enum Status { EXECUTED("executed"),OBSERVED("observed"),PENDING("pending"),BLOCKED("blocked"),TERMINAL("terminal");
        private final String token;Status(String token){this.token=token;}public String token(){return token;}
        static Status parse(String token){for(Status status:values())if(status.token.equals(token))return status;throw new IllegalArgumentException("unrecognized actual AUTO status");}}
    /** Validated original bytes preserve absent/null fields and every source-owned domain extension. */
    public static final class Payload {
        private final RawJson original;private final Status status;
        private Payload(RawJson original,Status status){this.original=original;this.status=status;}
        public RawJson original(){return original;}public Status status(){return status;}
    }
    private McpAutoTurnEncoder() { }

    public static Payload encode(TurnReport actual,Known heldDriver,ActionPorts.OutcomeArchive sameWriterArchive,List<AutoFailureDiagnostic.Port> actualDiagnostics) {
        Objects.requireNonNull(actual);Objects.requireNonNull(heldDriver);Objects.requireNonNull(sameWriterArchive);actualDiagnostics=List.copyOf(actualDiagnostics);
        BatchReport report=actual.execution();int outcomes=report.turns().size()+report.reconciliations().size()+report.lifecycleTurns().size()+report.readPublicationReconciliations().size();
        McpJson.require(outcomes<=1,"AUTO must contain at most one actual ordinary action or original reconciliation");
        McpJson.require(heldDriver.stamp().game().equals(report.session().game()) && heldDriver.driver().session().bridgePid()==report.session().game().pid(),"AUTO public serialization crossed actual held Game");
        ObjectNode payload=McpJson.object();
        if(outcomes==0) {
            if(report.lastTerminalObservation().isPresent()) {
                var terminal=report.lastTerminalObservation().orElseThrow();var before=terminal.identity();
                McpJson.require(before.game().equals(report.session().game()) && before.sessionId().equals(report.session().sessionId()) && before.machineId().equals(report.session().machineId()),"actual no-action lifecycle source crossed Root session");
                Status status=terminal.decision() instanceof org.xar.ck3.control.application.session.SessionPorts.TerminalBlocked?Status.BLOCKED:Status.PENDING;
                payload.put("status",status.token());payload.putNull("plan");payload.putNull("planning_source_frame");
                payload.put("snapshot_id",before.frame().snapshotId()).put("revision",before.frame().revision().toString());payload.set("lifecycle_source_frame",LifecycleIdentityCodec.encode(before));
                payload.put("reason",report.detail());return finish(payload);
            }
            Optional<PlanTrace> trace=report.lastPlan();Status status=trace.flatMap(PlanTrace::finalPlan).filter(plan -> plan.kind()==OrdinaryPolicy.Kind.TERMINAL).isPresent()?Status.TERMINAL:Status.BLOCKED;
            payload.put("status",status.token());
            if(trace.isPresent()){PlanTrace plan=trace.orElseThrow();ObjectNode frame=sourceFrame(plan.before(),Optional.empty());payload.set("plan",plan(plan,Optional.empty()));payload.put("snapshot_id",plan.before().frame().snapshotId());payload.put("revision",plan.before().frame().revision().toString());payload.set("planning_source_frame",frame);}
            else {payload.putNull("plan");payload.putNull("snapshot_id");payload.putNull("revision");payload.putNull("planning_source_frame");}
            payload.put("reason",report.detail());return finish(payload,Optional.empty(),trace);
        }
        boolean terminalTurn=!report.lifecycleTurns().isEmpty(),readPublicationReconciliation=!report.readPublicationReconciliations().isEmpty();
        boolean reconciliation=readPublicationReconciliation || (terminalTurn?report.lifecycleTurns().getFirst().reconciliation():!report.reconciliations().isEmpty());ActionReceipt receipt;Optional<PlanTrace> trace;
        if(readPublicationReconciliation){receipt=report.readPublicationReconciliations().getFirst().originalReceipt();trace=Optional.empty();}
        else if(terminalTurn){receipt=report.lifecycleTurns().getFirst().receipt();trace=Optional.empty();}
        else if(reconciliation){var original=report.reconciliations().getFirst();receipt=original.originalReceipt();trace=Optional.of(original.plan());}
        else {var turn=report.turns().getFirst();receipt=turn.receipt();trace=Optional.of(turn.plan());}
        McpJson.require(receipt.command().sessionId().equals(report.session().sessionId()) && receipt.command().origin().game().equals(report.session().game())
                && receipt.command().origin().machineId().equals(report.session().machineId()),"AUTO outcome belongs to another original Root session");
        McpJson.require(receipt.equals(sameWriterArchive.loadReceipt(sameWriterArchive.receiptReferenceOf(receipt))),"AUTO actual original retained receipt changed");
        boolean lifecycle=receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal;
        requireOrdinaryOrigin(receipt,sameWriterArchive);
        var diagnostics=actualDiagnostics.stream().map(port -> Objects.requireNonNull(port.project(receipt,sameWriterArchive)))
                .flatMap(Optional::stream).toList();
        for(AutoFailureDiagnostic.Kind kind:AutoFailureDiagnostic.Kind.values()) {
            var matching=diagnostics.stream().filter(value -> value.kind()==kind).toList();
            McpJson.require(matching.size()<=1,"multiple source-owned AUTO diagnostics for one kind");
            if(!matching.isEmpty())throw McpAutoFailure.fromDiagnostic(matching.getFirst(),receipt);
        }
        McpAutoFailure.fromReceipt(receipt).ifPresent(failure -> {throw failure;});
        String selected=receipt.command().operation().value();
        Status status=switch(receipt.outcome()){case UNRESOLVED -> Status.PENDING;case REJECTED_BEFORE_DISPATCH,REJECTED_CONFIRMED -> Status.BLOCKED;
            case APPLIED_CONFIRMED -> receipt.visibleGameplay()?Status.EXECUTED:Status.OBSERVED;
            case SEND_CONFIRMED,TERMINAL_WITHOUT_EFFECT -> Status.OBSERVED;};
        payload.put("status",status.token());payload.put("selected_step",selected);
        if(lifecycle) {
            var before=receipt.command().lifecycleBefore();payload.putNull("plan");payload.putNull("planning_source_frame");
            payload.put("snapshot_id",before.frame().snapshotId());payload.put("revision",before.frame().revision().toString());
            payload.set("lifecycle_source_frame",LifecycleIdentityCodec.encode(before));
            if(terminalTurn && reconciliation)payload.set("lifecycle_reconciliation_frame",LifecycleIdentityCodec.encode(report.lifecycleTurns().getFirst().current()));
        } else {
            if(trace.isPresent())payload.set("plan",plan(trace.orElseThrow(),Optional.of(selected)));else {
                McpJson.require(reconciliation && (terminalTurn || readPublicationReconciliation),"absent original PlanTrace requires its actual original-parent read-only reconciliation");payload.putNull("plan");
                if(terminalTurn)payload.set("terminal_reconciliation_frame",LifecycleIdentityCodec.encode(report.lifecycleTurns().getFirst().current()));
            }
            var before=receipt.command().before();payload.put("snapshot_id",before.frame().snapshotId());payload.put("revision",before.frame().revision().toString());
            payload.set("planning_source_frame",sourceFrame(before,guard(receipt).map(GuardEvidence::connectionGeneration)));
        }
        Optional<RawJson> business=originalBusiness(receipt,heldDriver,sameWriterArchive);
        if(business.isPresent()) payload.set("result",McpJson.parse(business.orElseThrow().bytes()));
        else {
            ObjectNode missing=McpJson.object().put("step",selected).put("status",receipt.settled()?"public_result_unavailable":"action_state_unknown");
            missing.put("canonical_outcome",receipt.outcome().name()).put("action_id",receipt.command().actionId()).put("action_body_sha256",receipt.bodySha256());
            missing.put("never_replay",true).put("material_result_available",false);missing.set("original_receipt",sameWriterArchive.receiptReferenceOf(receipt).toJson());
            payload.set("result",missing);payload.put("public_result_available",false);
        }
        if(reconciliation)payload.putObject("original_action_reconciliation").put("action_id",receipt.command().actionId()).put("new_action_submitted",false);
        if(terminalTurn&&report.lifecycleTurns().getFirst().successorUiContinuation().isPresent()) {
            var pass=report.lifecycleTurns().getFirst().successorUiContinuation().orElseThrow();
            McpJson.require(!reconciliation&&pass.actual().parent().equals(receipt),"actual UI continuation is not a read-only reconciliation");
            for(ActionReceipt child:pass.actual().children())McpJson.require(child.equals(sameWriterArchive.loadReceipt(sameWriterArchive.receiptReferenceOf(child))),
                    "actual UI child attempt lost original canonical receipt custody");
            payload.set("successor_ui_continuation",SuccessorUiContinuationJson.encode(pass));
        }
        if(readPublicationReconciliation) {
            var publication=report.readPublicationReconciliations().getFirst().readPublication();
            var source=payload.putObject("read_publication_reconciliation");source.put("schema","xar.ck3.java-auto-read-publication-reconciliation/v1");
            source.put("event_identity",publication.actual().eventIdentity()).put("predecessor_sha256",publication.predecessor().digest())
                    .put("resulting_head_sha256",org.xar.ck3.control.continuity.ContinuityJson.digest(publication.actual().head().toJson()));
            source.put("original_action_id",receipt.command().actionId()).put("new_action_submitted",false);
        }
        return finish(payload,business,trace);
    }
    /** Pure public projection guard; no fixture proof grants ordinary AUTO admission. */
    static void requireOrdinaryOrigin(ActionReceipt receipt,ActionPorts.OutcomeArchive sameWriterArchive) {
        Objects.requireNonNull(receipt);Objects.requireNonNull(sameWriterArchive);
        if(receipt.command().origin() instanceof CommandOrigin.Frontend && FixturePlan.isParent(receipt.command()))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.UNSUPPORTED_STEP,
                    "native DLL does not implement gameplay step "+receipt.command().operation().value(),
                    Optional.of(sameWriterArchive.receiptReferenceOf(receipt)));
        McpJson.require(receipt.command().origin() instanceof CommandOrigin.LifecycleTerminal
                || receipt.command().origin() instanceof CommandOrigin.Gameplay,
                "AUTO report cannot silently present a frontend action as ordinary or terminal");
    }
    /** Reads the original producer row only after its canonical action/sequence/body and exact bytes have matched. */
    static Optional<RawJson> originalBusiness(ActionReceipt actual,Known driver,ActionPorts.OutcomeArchive archive) {
        var watch=org.xar.ck3.control.application.advance.WarDailyWatchUnresolved.read(actual,archive);
        if(watch.isPresent()) {
            // This source-owned schema already uses its typed Context codec for every full-width role.
            ObjectNode original=McpJson.object(McpJson.parse(watch.orElseThrow().bytes())).deepCopy();McpJson.publicNumbers(original);return Optional.of(new RawJson(watch.orElseThrow().bytes()));
        }
        ActionState.Settlement settlement=actual.state() instanceof ActionState.CompositeSettled composite?composite.settlement():actual.state() instanceof ActionState.Settled primitive?primitive.settlement():null;
        if(settlement instanceof ActionState.LifecycleApplied applied) {
            applied.proof().validateParent(actual.command());
            RawJson encoded=LifecyclePublicResultCodec.encode(applied.proof().kind(),new RawJson(applied.proof().encodedResult()));
            ObjectNode original=McpJson.object(McpJson.parse(encoded.bytes()));
            if(original.has("step"))McpJson.require(original.get("step").isTextual() && original.get("step").textValue().equals(actual.command().operation().value()),"actual lifecycle result step differs");
            McpJson.publicNumbers(original);return Optional.of(encoded);
        }
        var matching=driver.actionRows().stream().filter(row -> row.actionId().equals(actual.command().actionId())).toList();
        if(matching.isEmpty())return Optional.empty();McpJson.require(matching.size()==1,"one actual original history coverage row required");var coverage=matching.getFirst();
        McpJson.require(coverage.bodySha256().equals(actual.bodySha256()) && coverage.durableSequence()==actual.sequence(),"AUTO history action body or durable sequence differs");
        if(coverage.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly canonical) {
            try {DriverActionHistoryCodec.verifyCanonicalOnly(actual,canonical.originalSource(),archive);}
            catch(IOException failure){throw new UncheckedIOException("canonical-only AUTO original source unavailable",failure);}
            return Optional.empty();
        }
        var legacy=(DriverSnapshotFacts.LegacyHistoryRow)coverage.coverageSource();
        int index=Math.toIntExact(legacy.historyIndex()-1);McpJson.require(index>=0 && index<driver.driver().commandHistory().size(),"actual original history index out of range");
        byte[] originalRow=driver.driver().commandHistory().get(index).originalRow().json();RawJson archived=archive.loadMaterial(legacy.originalRow());
        McpJson.require(legacy.originalRow().bytes()==originalRow.length && legacy.originalRow().sha256().equals(DriverJson.sha256(originalRow))
                && Arrays.equals(originalRow,archived.bytes()),"AUTO source is not this exact original producer history row; no synthesized fallback");
        var typed=DriverJson.object(originalRow,DriverJson.MAX_NATIVE_BYTES);
        // Older SAVE/import rows have separate issuer paths. Absent this recording source is not permission to guess ok or a business result.
        if(!typed.members().containsKey(DriverActionHistoryCodec.SOURCE_FIELD))return Optional.empty();
        try {DriverActionHistoryCodec.verifyLegacy(actual,typed,archive);}
        catch(IOException failure){throw new UncheckedIOException("AUTO original legacy recording source unavailable",failure);}
        ObjectNode row=McpJson.object(McpJson.parse(originalRow));
        McpJson.require(row.path("index").isIntegralNumber() && row.get("index").bigIntegerValue().equals(BigInteger.valueOf(legacy.historyIndex()))
                && row.path("command").isTextual() && row.get("command").textValue().equals(actual.command().operation().value()) && row.path("ok").isBoolean()
                && row.get("ok").booleanValue()==DriverActionHistoryCodec.recordedOk(actual,typed),"AUTO original history recording identity/status differs");
        if(!row.has("result") || row.get("result").isNull())return Optional.empty();ObjectNode result=McpJson.object(row.get("result")).deepCopy();
        // Result step is the original producing query/native selector, which may differ from the logical submitted command.
        if(result.has("step"))McpJson.require(result.get("step").isTextual(),"original AUTO result selector must be text");
        if(result.has("accepted"))McpJson.require(result.get("accepted").isBoolean(),"original AUTO accepted field must be boolean");
        // Domain results are open. Their qualified public encoders must already have serialized full64 roles.
        // Unknown unsafe numeric fields are rejected, never guessed or replaced by desired effects.
        McpJson.publicNumbers(result);return Optional.of(new RawJson(McpJson.token(originalRow,"result")));
    }
    private static ObjectNode plan(PlanTrace trace,Optional<String> selected) {
        ObjectNode result=trace.finalPlan().map(value -> McpJson.object(McpJson.parse(DriverJson.encode(value.detail()))).deepCopy()).orElseGet(McpJson::object);
        trace.finalPlan().ifPresent(value -> {sameOrPut(result,"policy",value.policy());sameOrPut(result,"phase",value.phase());sameOrPut(result,"reason",value.reason());});
        if(selected.isPresent())sameOrPut(result,"selected_step",selected.orElseThrow());else if(!result.has("selected_step"))result.putNull("selected_step");
        return result;
    }
    private static void sameOrPut(ObjectNode row,String key,String expected){if(row.has(key))McpJson.require(row.get(key).isTextual() && row.get(key).textValue().equals(expected),"source plan conflicts with actual "+key);else row.put(key,expected);}
    private static ObjectNode sourceFrame(ObservationIdentity before,Optional<BigInteger> connection) {
        ObjectNode frame=McpJson.object().put("schema","xar.ck3.planning-source-frame/v1").put("status",connection.isPresent()?"complete":"partial");
        frame.put("snapshot_id",before.frame().snapshotId()).put("revision",before.frame().revision().toString()).put("native_revision",before.frame().identity().nativeRevision().toString());
        frame.put("date_raw",before.frame().identity().dateRaw()).put("actor_character_id",before.frame().identity().player()).put("episode_run_id",before.frame().episodeRunId());
        if(connection.isPresent())frame.put("connection_generation",connection.orElseThrow().toString());else frame.putNull("connection_generation");frame.put("bridge_pid",before.game().pid());return frame;
    }
    private static Optional<GuardEvidence> guard(ActionReceipt receipt){return switch(receipt.state()){
        case ActionState.IntentDurable ignored -> Optional.empty();case ActionState.Submitting value -> Optional.of(value.attempt().guard());case ActionState.AckReceived value -> Optional.of(value.attempt().guard());
        case ActionState.Unknown value -> value.attempt().map(ActionState.Attempt::guard);case ActionState.Settled value -> Optional.of(value.attempt().guard());case ActionState.RejectedBeforeDispatch value -> Optional.of(value.attempt().guard());
        case ActionState.CompositeRunning value -> Optional.of(value.execution().guard());case ActionState.CompositeUnknown value -> Optional.of(value.execution().guard());case ActionState.CompositeSettled value -> Optional.of(value.execution().guard());
        case PhysicalActionState value -> Optional.of(value.guard());};}
    private static Payload finish(ObjectNode original){return finish(original,Optional.empty(),Optional.empty());}
    private static Payload finish(ObjectNode original,Optional<RawJson> result,Optional<PlanTrace> trace){
        byte[] encoded=McpJson.encode(original);
        if(result.isPresent())encoded=McpJson.member(encoded,"result",result.orElseThrow().bytes());
        if(trace.isPresent()&&trace.orElseThrow().finalPlan().isPresent()){
            var detail=trace.orElseThrow().finalPlan().orElseThrow().detail();
            var plan=PublicDataJson.encodePreservingDecimals(original.get("plan"),new RawJson(DriverJson.encode(detail)));
            encoded=McpJson.member(encoded,"plan",plan.bytes());
        }
        return parse(new RawJson(encoded));
    }
    public static Payload parse(RawJson original) {
        ObjectNode row=McpJson.object(McpJson.parse(original.bytes()));McpJson.publicNumbers(row);Status status=Status.parse(McpJson.text(row.get("status")));
        McpJson.require(row.has("plan") && (row.get("plan").isObject() || row.get("plan").isNull()) && row.has("planning_source_frame"),"original AUTO plan and source presence required");
        if(row.has("lifecycle_source_frame")) {
            var before=LifecycleIdentityCodec.decode(row.get("lifecycle_source_frame"));
            McpJson.require(row.get("plan").isNull() && row.get("planning_source_frame").isNull(),"lifecycle source cannot masquerade as ordinary planning");
            McpJson.require(before.frame().snapshotId().equals(McpJson.text(row.get("snapshot_id"))) && before.frame().revision().toString().equals(McpJson.text(row.get("revision"))),"lifecycle AUTO outer frame differs");
            if(row.has("lifecycle_reconciliation_frame"))McpJson.require(before.sameSession(LifecycleIdentityCodec.decode(row.get("lifecycle_reconciliation_frame"))),"lifecycle reconciliation crossed actual session");
        } else McpJson.require(!row.has("lifecycle_reconciliation_frame"),"lifecycle reconciliation requires its original source");
        if(row.has("selected_step")){McpJson.require(row.get("selected_step").isTextual() && !row.get("selected_step").textValue().isBlank(),"actual AUTO selected step required");
            if(!row.has("lifecycle_source_frame")) {
                if(row.has("terminal_reconciliation_frame") || row.has("read_publication_reconciliation"))McpJson.require(row.get("plan").isNull() && row.has("original_action_reconciliation"),"original-parent read-only reconciliation cannot invent a new plan");
                else {var plan=McpJson.object(row.get("plan"));McpJson.require(row.get("selected_step").equals(plan.get("selected_step")),"AUTO selected step/plan mismatch");}
            }
            McpJson.require(row.has("result") && row.get("result").isObject(),"AUTO original result object absent");
            if(row.get("result").has("step"))McpJson.require(row.get("result").get("step").isTextual(),"AUTO original result selector must be text; logical selection remains bound to plan/receipt");
            if(row.has("public_result_available"))McpJson.require(row.get("public_result_available").isBoolean(),"actual public result availability must be boolean");
            if(!row.has("public_result_available") || row.get("public_result_available").booleanValue()) {
                String selected=row.get("selected_step").textValue();
                LifecyclePublicResultCodec.kindOfOperation(selected).ifPresent(value->LifecyclePublicResultCodec.decode(value,new RawJson(McpJson.encode(row.get("result")))));
            }
        }
        if(!row.get("planning_source_frame").isNull()) {var frame=McpJson.object(row.get("planning_source_frame"));
            var fields=java.util.Set.of("schema","status","snapshot_id","revision","native_revision","date_raw","actor_character_id","episode_run_id","connection_generation","bridge_pid");McpJson.fields(frame,fields,fields);
            McpJson.require("xar.ck3.planning-source-frame/v1".equals(McpJson.text(frame.get("schema"))),"original planning-source schema required");
            McpJson.require(java.util.Set.of("complete","partial").contains(McpJson.text(frame.get("status"))) && frame.get("date_raw").isIntegralNumber()
                    && frame.get("actor_character_id").isIntegralNumber() && frame.get("bridge_pid").isIntegralNumber(),"original planning-source scalar types differ");
            McpJson.require(!McpJson.text(frame.get("snapshot_id")).isBlank() && !McpJson.text(frame.get("episode_run_id")).isBlank()
                    && frame.get("actor_character_id").bigIntegerValue().signum()>0 && frame.get("bridge_pid").bigIntegerValue().signum()>0,
                    "original planning-source identity must be explicit and positive");
            McpJson.require(!"complete".equals(McpJson.text(frame.get("status"))) || !frame.get("connection_generation").isNull(),"complete source requires actual connection evidence");
            decimal(frame.get("revision"),false);decimal(frame.get("native_revision"),true);if(!frame.get("connection_generation").isNull())decimal(frame.get("connection_generation"),false);
            McpJson.require(frame.get("snapshot_id").equals(row.get("snapshot_id")) && frame.get("revision").equals(row.get("revision")),"AUTO outer frame identity differs");}
        if(row.has("terminal_reconciliation_frame")) {
            McpJson.require(!row.has("lifecycle_source_frame") && !row.get("planning_source_frame").isNull() && row.has("selected_step"),"terminal ordinary reconciliation requires its original ordinary source");
            var current=LifecycleIdentityCodec.decode(row.get("terminal_reconciliation_frame"));var originalFrame=row.get("planning_source_frame");
            McpJson.require(current.subject().episodeRunId().equals(McpJson.text(originalFrame.get("episode_run_id")))
                    && current.subject().characterId().equals(originalFrame.get("actor_character_id").bigIntegerValue())
                    && BigInteger.valueOf(current.game().pid()).equals(originalFrame.get("bridge_pid").bigIntegerValue()),"terminal ordinary reconciliation source crossed actual old subject/Game");
        }
        if(row.has("read_publication_reconciliation")) {
            var source=McpJson.object(row.get("read_publication_reconciliation"));
            var fields=java.util.Set.of("schema","event_identity","predecessor_sha256","resulting_head_sha256","original_action_id","new_action_submitted");McpJson.fields(source,fields,fields);
            McpJson.require("xar.ck3.java-auto-read-publication-reconciliation/v1".equals(McpJson.text(source.get("schema")))
                    && McpJson.text(source.get("event_identity")).matches("[0-9a-f]{64}") && McpJson.text(source.get("predecessor_sha256")).matches("[0-9a-f]{64}")
                    && McpJson.text(source.get("resulting_head_sha256")).matches("[0-9a-f]{64}") && source.get("new_action_submitted").isBoolean()
                    && !source.get("predecessor_sha256").equals(source.get("resulting_head_sha256"))
                    && !source.get("new_action_submitted").booleanValue() && row.has("original_action_reconciliation")
                    && source.get("original_action_id").equals(row.get("original_action_reconciliation").get("action_id")),"actual read-publication reconciliation metadata differs");
        }
        if(row.has("original_action_reconciliation")) {
            var source=McpJson.object(row.get("original_action_reconciliation"));var fields=java.util.Set.of("action_id","new_action_submitted");McpJson.fields(source,fields,fields);
            McpJson.require(McpJson.text(source.get("action_id")).matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
                    && source.get("new_action_submitted").isBoolean() && !source.get("new_action_submitted").booleanValue(),"read-only reconciliation cannot claim a new submission");
        }
        if(row.has("successor_ui_continuation")) {
            McpJson.require(row.has("lifecycle_source_frame")&&!row.has("original_action_reconciliation")
                    &&!row.has("read_publication_reconciliation")&&row.has("selected_step")
                    &&org.xar.ck3.control.application.lifecycle.LifecycleComposites.parentKind(new OperationKey(McpJson.text(row.get("selected_step"))))
                        .filter(kind->kind==org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR).isPresent(),
                    "actual successor UI continuation requires its original terminal CONTINUE parent");
            SuccessorUiContinuationJson.validate(row.get("successor_ui_continuation"));
            if(row.get("result").has("action_id"))McpJson.require(row.get("result").get("action_id").equals(row.get("successor_ui_continuation").get("original_parent_action_id")),
                    "UI continuation result changed its original parent action");
        }
        return new Payload(original,status);
    }
    private static BigInteger decimal(JsonNode value,boolean positive){String text=McpJson.text(value);McpJson.require(text.length()<=4300 && text.matches(positive?"[1-9][0-9]*":"0|[1-9][0-9]*"),"canonical decimal public revision required");return new BigInteger(text);}
}
