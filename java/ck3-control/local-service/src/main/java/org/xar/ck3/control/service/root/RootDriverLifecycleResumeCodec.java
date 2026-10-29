package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Original App resume result DATA. The Runtime supplies actual originals; this formatter cannot
 * issue a pending cause, certify a handoff, observe, submit Close, advance a date or update Goal.
 * Native/archive integer and decimal domains remain unchanged. */
public final class RootDriverLifecycleResumeCodec {
    private RootDriverLifecycleResumeCodec() { }
    public enum Status {
        CLEAR("clear"),CLOSE_REQUIRED("close_required"),DEFERRED_PLAYER_DECISION("deferred_player_decision"),UI_UNRESOLVED("ui_unresolved");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        static Status parse(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("original resume status required");}
    }
    public enum Qualification {
        CAUSE_QUALIFIED("cause_qualified"),VERIFIED("verified");
        private final String wire;Qualification(String wire){this.wire=wire;}public String wire(){return wire;}
        static Qualification parse(String wire){for(var value:values())if(value.wire.equals(wire))return value;throw new IllegalArgumentException("actual transition qualification required");}
    }
    public record Failure(String stage,String kind,String message,Optional<String> errorType,Optional<String> error) {
        public Failure {text(stage);text(kind);Objects.requireNonNull(message);Objects.requireNonNull(errorType);Objects.requireNonNull(error);require(errorType.isPresent()==error.isPresent(),"original captured exception class/message presence differs");errorType.ifPresent(RootDriverLifecycleResumeCodec::text);}
    }
    public record Diagnostic(String error,List<Failure> failures) {
        public Diagnostic {Objects.requireNonNull(error);failures=List.copyOf(failures);require(failures.size()<=256,"bounded original failure capture required");}
    }
    /** Cold binding is the retained original DATA. A digest here never grants connection-rebind authority. */
    public record ColdBinding(RawJson originalNumeric) {
        public ColdBinding {cold(object(originalNumeric),true);}
    }
    /** Typed frame projection used for comparison; the retained JSON keeps its original branch shape. */
    public record ColdFrame(long bridgePid,BigInteger connectionGeneration,String snapshotId,BigInteger revision,
            BigInteger nativeRevision,int dateRaw,int actorCharacterId,String episodeRunId) {
        public ColdFrame {
            require(bridgePid>0&&bridgePid<=0xffff_ffffL,"actual uint32 cold Game PID required");
            new PythonOnlyUInt64(connectionGeneration);new PythonOnlyUInt64(revision);new PythonOnlyUInt64(nativeRevision);
            require(nativeRevision.signum()>0&&dateRaw>=0,"actual nonnegative cold date and positive native revision required");
            text(snapshotId);text(episodeRunId);actor(actorCharacterId);
        }
    }
    public record ColdGame(long pid,String creationDate,String executable) {
        public ColdGame {require(pid>0&&pid<=0xffff_ffffL,"actual uint32 cold Game PID required");text(creationDate);text(executable);}
    }
    /** DATA supplied only after the actual Runtime's writer/M3/source checks. The formatter issues no ticket. */
    public record ColdBindingMaterial(TransitionMaterial actualTransition,Optional<RawJson> originalObservation,
            ColdFrame retainedFrame,ColdFrame resumedFrame,String machineId,Optional<String> sourceEpoch,ColdGame game,
            ExactRef canonicalPendingLedger,boolean connectionRebound) {
        public ColdBindingMaterial {
            Objects.requireNonNull(actualTransition);Objects.requireNonNull(originalObservation);
            originalObservation.ifPresent(value->{observation(object(value),true);coldDigest(object(value));});
            Objects.requireNonNull(retainedFrame);Objects.requireNonNull(resumedFrame);text(machineId);
            require(!machineId.equals("unknown"),"actual cold machine identity required");Objects.requireNonNull(sourceEpoch);sourceEpoch.ifPresent(epoch->sha(new Text(epoch)));
            Objects.requireNonNull(game);Objects.requireNonNull(canonicalPendingLedger);
            require(canonicalPendingLedger.bytes()>0,"actual nonempty canonical pending ledger reference required");
        }
        public ColdBindingMaterial(TransitionMaterial actualTransition,Optional<RawJson> originalObservation,
                ColdFrame retainedFrame,ColdFrame resumedFrame,String machineId,String sourceEpoch,ColdGame game,
                ExactRef canonicalPendingLedger,boolean connectionRebound) {
            this(actualTransition,originalObservation,retainedFrame,resumedFrame,machineId,Optional.of(sourceEpoch),game,canonicalPendingLedger,connectionRebound);
        }
    }
    private static final List<String> COLD_PROOF=List.of("status","predecessor_character_id","successor_character_id",
            "source_episode_run_id","episode_run_id","same_campaign_frame","ck3_command_submitted","process_restarted",
            "succession_lifecycle","reconciliation","predecessor_binding","successor_episode_binding");

    /** Original schema and Python canonical integer-domain digest; ledger SHA binds the actual Java writer body.
     * This performs no I/O, private cold admission, M3 qualification or Game/connection rebind. */
    public static ColdBinding formatColdBinding(ColdBindingMaterial actual) {
        Objects.requireNonNull(actual);TransitionMaterial transition=actual.actualTransition();
        Obj previous=actual.originalObservation().map(RootDriverLifecycleResumeCodec::object).orElse(null);
        if(previous!=null)observation(previous,true);
        Obj retained=previous==null?object(transition.successorEpisodeBinding()):asObject(member(previous,"frame"));
        requireColdProjection(actual.retainedFrame(),retained);
        ColdFrame old=actual.retainedFrame(),current=actual.resumedFrame();
        require(old.actorCharacterId()==transition.successorCharacterId()&&current.actorCharacterId()==transition.successorCharacterId()
                &&old.episodeRunId().equals(transition.episodeRunId())&&current.episodeRunId().equals(transition.episodeRunId()),
                "cold DATA changed its actual successor actor/run");
        require(actual.game().pid()==old.bridgePid()&&actual.game().pid()==current.bridgePid(),"cold DATA changed its actual Game PID");
        boolean rebound=!current.connectionGeneration().equals(old.connectionGeneration());
        require(actual.connectionRebound()==rebound,"cold DATA connection-rebound flag differs from its actual frames");
        require(current.nativeRevision().compareTo(old.nativeRevision())>=0&&current.dateRaw()>=old.dateRaw()
                &&(rebound||current.revision().compareTo(old.revision())>=0),"cold DATA regressed its original frame");
        var fields=new LinkedHashMap<String,Value>();fields.put("schema",new Text("xar.ck3.successor-ui-cold-binding/v1"));
        fields.put("transition_sha256",new Text(coldDigest(numericProof(transition))));
        fields.put("observation_sha256",new Text(coldDigest(previous==null?Nil.INSTANCE:previous)));
        fields.put("retained_frame",retained);fields.put("resumed_frame",coldFrame(current));
        fields.put("machine_id",new Text(actual.machineId()));fields.put("source_epoch",actual.sourceEpoch().<Value>map(Text::new).orElse(Nil.INSTANCE));
        fields.put("game_identity",new Obj(Map.of("pid",number(actual.game().pid()),"creation_date",new Text(actual.game().creationDate()),
                "executable",new Text(actual.game().executable()))));
        fields.put("ledger_sha256",new Text(actual.canonicalPendingLedger().sha256()));fields.put("connection_rebound",new Bool(rebound));
        fields.put("binding_sha256",new Text(coldDigest(new Obj(fields))));
        return new ColdBinding(json(new Obj(fields)));
    }
    private static Obj numericProof(TransitionMaterial actual) {
        var values=new LinkedHashMap<String,Value>();values.put("status",new Text(actual.qualification().wire()));
        values.put("predecessor_character_id",number(actual.predecessorCharacterId()));values.put("successor_character_id",number(actual.successorCharacterId()));
        values.put("source_episode_run_id",new Text(actual.sourceEpisodeRunId()));values.put("episode_run_id",new Text(actual.episodeRunId()));
        values.put("same_campaign_frame",new Bool(true));values.put("ck3_command_submitted",new Bool(false));values.put("process_restarted",new Bool(false));
        values.put("succession_lifecycle",object(actual.successionLifecycle()));values.put("reconciliation",object(actual.reconciliation()));
        values.put("predecessor_binding",object(actual.predecessorBinding()));values.put("successor_episode_binding",object(actual.successorEpisodeBinding()));
        Obj proof=new Obj(values);exact(proof,Set.copyOf(COLD_PROOF));return proof;
    }
    private static Obj coldFrame(ColdFrame actual) {
        return new Obj(Map.of("bridge_pid",number(actual.bridgePid()),"connection_generation",new IntegerValue(actual.connectionGeneration()),
                "snapshot_id",new Text(actual.snapshotId()),"revision",new IntegerValue(actual.revision()),"native_revision",new IntegerValue(actual.nativeRevision()),
                "date_raw",number(actual.dateRaw()),"actor_character_id",number(actual.actorCharacterId()),"episode_run_id",new Text(actual.episodeRunId())));
    }
    private static void requireColdProjection(ColdFrame expected,Obj actual) {
        require(new IntegerValue(BigInteger.valueOf(expected.bridgePid())).equals(member(actual,"bridge_pid"))
                &&new IntegerValue(expected.connectionGeneration()).equals(member(actual,"connection_generation"))
                &&new Text(expected.snapshotId()).equals(member(actual,"snapshot_id"))&&new IntegerValue(expected.revision()).equals(member(actual,"revision"))
                &&new IntegerValue(expected.nativeRevision()).equals(member(actual,"native_revision"))&&number(expected.dateRaw()).equals(member(actual,"date_raw"))
                &&number(expected.actorCharacterId()).equals(member(actual,"played_character_id"))&&new Text(expected.episodeRunId()).equals(member(actual,"episode_run_id")),
                "cold projection differs from the identical retained transition/observation frame");
    }

    /** The two source DTOs have integer/bool/text/null JSON. Unknown decimal domains fail instead of approximating Python floats. */
    private static String coldDigest(Value value) {
        try {var digest=new ColdDigest(MessageDigest.getInstance("SHA-256"));digest.value(value,0);return java.util.HexFormat.of().formatHex(digest.actual.digest());}
        catch(NoSuchAlgorithmException impossible){throw new AssertionError(impossible);}
    }
    private static final class ColdDigest {
        private final MessageDigest actual;private long bytes;
        ColdDigest(MessageDigest actual){this.actual=actual;}
        private void ascii(char value){require(value<=0x7f&&++bytes<=RawJson.MAXIMUM_BYTES,"bounded ASCII cold digest required");actual.update((byte)value);}
        private void ascii(String value){for(int index=0;index<value.length();index++)ascii(value.charAt(index));}
        private void string(String value) {
            ascii('"');for(int index=0;index<value.length();index++) {
                char current=value.charAt(index);
                if(Character.isHighSurrogate(current))require(index+1<value.length()&&Character.isLowSurrogate(value.charAt(index+1)),"cold text contains an unpaired high surrogate");
                else if(Character.isLowSurrogate(current))require(index>0&&Character.isHighSurrogate(value.charAt(index-1)),"cold text contains an unpaired low surrogate");
                switch(current) {
                    case '"'->ascii("\\\"");case '\\'->ascii("\\\\");case '\b'->ascii("\\b");case '\f'->ascii("\\f");
                    case '\n'->ascii("\\n");case '\r'->ascii("\\r");case '\t'->ascii("\\t");
                    default->{if(current<0x20||current>=0x7f){ascii("\\u");for(int shift=12;shift>=0;shift-=4)ascii("0123456789abcdef".charAt((current>>>shift)&15));}else ascii(current);}
                }
            }ascii('"');
        }
        private void value(Value value,int depth) {
            require(value!=null&&depth<=64,"bounded cold digest JSON required");
            switch(value) {
                case Obj object->{ascii('{');var keys=new ArrayList<>(object.members().keySet());keys.sort(RootDriverLifecycleResumeCodec::pythonKeyOrder);
                    boolean first=true;for(String key:keys){if(!first)ascii(',');first=false;string(key);ascii(':');value(object.get(key),depth+1);}ascii('}');}
                case Arr array->{ascii('[');boolean first=true;for(Value item:array.items()){if(!first)ascii(',');first=false;value(item,depth+1);}ascii(']');}
                case Text text->string(text.value());case IntegerValue integer->ascii(integer.value().toString());
                case Bool bool->ascii(bool.value()?"true":"false");case Nil ignored->ascii("null");
                case DecimalValue ignored->throw new IllegalArgumentException("cold source DTO digest does not admit decimal JSON values");
            }
        }
    }
    private static int pythonKeyOrder(String left,String right) {
        var first=left.codePoints().iterator();var second=right.codePoints().iterator();
        while(first.hasNext()&&second.hasNext()){int compared=Integer.compare(first.nextInt(),second.nextInt());if(compared!=0)return compared;}
        return Boolean.compare(first.hasNext(),second.hasNext());
    }
    public record TimelineContinuation(String status,RawJson initialQuery,
            Optional<RootDriverLifecyclePublicCodec.CloseMaterial> closeResult,
            Optional<RawJson> deferredEventObservation,Optional<RawJson> originalDeferredQuery,
            Optional<Boolean> closeAttempted,Optional<Boolean> uiClearanceVerified,Optional<RawJson> ownerInterception) {
        public TimelineContinuation {
            timelineStatus(status);RootDriverLifecyclePublicCodec.encodeTimelineOriginal(initialQuery);
            Objects.requireNonNull(closeResult);Objects.requireNonNull(deferredEventObservation);Objects.requireNonNull(originalDeferredQuery);
            require(deferredEventObservation.isPresent()==originalDeferredQuery.isPresent(),"original deferred observation/query pair required");
            deferredEventObservation.ifPresent(value->observation(object(value),true));
            originalDeferredQuery.ifPresent(RootDriverLifecyclePublicCodec::encodeTimelineOriginal);
            Objects.requireNonNull(closeAttempted);Objects.requireNonNull(uiClearanceVerified);Objects.requireNonNull(ownerInterception);
            closeAttempted.ifPresent(value->require(value,"original once marker cannot be false"));
            uiClearanceVerified.ifPresent(value->require(!value,"deferred observation cannot grant clearance"));
            require(closeResult.isEmpty()||closeAttempted.orElse(false),"retained actual Close requires its once marker");
            require(ownerInterception.isPresent()==status.equals("deferred_owner_interception"),"original owner interception presence differs");
            ownerInterception.ifPresent(RootDriverLifecycleResumeCodec::object);
        }
    }
    public record TransitionMaterial(Qualification qualification,int predecessorCharacterId,int successorCharacterId,
            String sourceEpisodeRunId,String episodeRunId,int dateRaw,RawJson successionLifecycle,RawJson reconciliation,
            RawJson predecessorBinding,RawJson successorEpisodeBinding,Optional<TimelineContinuation> timelineContinuation,
            Optional<RawJson> successorUiObservation) {
        public TransitionMaterial {
            Objects.requireNonNull(qualification);actor(predecessorCharacterId);actor(successorCharacterId);require(predecessorCharacterId!=successorCharacterId,"actual predecessor and successor differ");
            text(sourceEpisodeRunId);text(episodeRunId);require(!sourceEpisodeRunId.equals(episodeRunId),"actual successor run must be distinct");
            SuccessionLifecycleCodec.decode(successionLifecycle.bytes());
            GoalCodec.decodeReconciliation(reconciliation.bytes());
            var estate=object(reconciliation);require(new Text("matched").equals(estate.get("verdict"))&&new Bool(true).equals(estate.get("successor_match"))&&new Bool(true).equals(estate.get("title_distribution_match")),"actual matched M3 original required");
            require(integer(member(estate,"predecessor_character_id"),"predecessor").intValueExact()==predecessorCharacterId&&integer(member(estate,"actual_successor_character_id"),"successor").intValueExact()==successorCharacterId,"M3 original actor differs");
            binding(object(predecessorBinding),true);binding(object(successorEpisodeBinding),true);
            Objects.requireNonNull(timelineContinuation);Objects.requireNonNull(successorUiObservation);successorUiObservation.ifPresent(value->observation(object(value),true));
            if(qualification==Qualification.VERIFIED)verifiedBinding(object(successorEpisodeBinding),successorCharacterId,episodeRunId);
        }
    }
    public record ResumeResult(Status status,boolean pending,boolean playerDecisionPending,boolean dateAdvanced,
            RawJson originalNumericSnapshot,Optional<TransitionMaterial> transition,Optional<ColdBinding> coldBinding,
            Optional<Diagnostic> diagnostic) {
        public ResumeResult {
            Objects.requireNonNull(status);PublicSnapshotCodec.encodeSemanticData(originalNumericSnapshot);
            Objects.requireNonNull(transition);Objects.requireNonNull(coldBinding);Objects.requireNonNull(diagnostic);
            shape(status,pending,playerDecisionPending,dateAdvanced,transition.isPresent(),diagnostic.isPresent());
            if(transition.isEmpty())require(coldBinding.isEmpty(),"clear without an actual pending transition has no cold binding");
            else {
                var actual=transition.orElseThrow();if(actual.qualification()==Qualification.CAUSE_QUALIFIED)require(pending&&!dateAdvanced,"private prefinal cause is not a verified handoff/date");
                coldBinding.ifPresent(value->require(new Text(coldDigest(numericProof(actual))).equals(object(value.originalNumeric()).get("transition_sha256")),
                        "cold DATA changed its actual original transition proof"));
                if(actual.qualification()==Qualification.VERIFIED) {
                    verifiedSnapshot(object(originalNumericSnapshot),actual.successorCharacterId(),actual.episodeRunId());
                }
            }
        }
    }
    public static ResumeResult clear(RawJson originalNumericSnapshot) {
        return new ResumeResult(Status.CLEAR,false,false,false,originalNumericSnapshot,Optional.empty(),Optional.empty(),Optional.empty());
    }
    /** Validated public DATA cannot become a ResumeResult or any private Runtime token. */
    public static final class Data {
        private final RawJson original,snapshot;private final Status status;private final boolean pending;
        private Data(RawJson original,RawJson snapshot,Status status,boolean pending){this.original=original;this.snapshot=snapshot;this.status=status;this.pending=pending;}
        public RawJson original(){return original;}public RawJson originalNumericSnapshot(){return snapshot;}
        public Status status(){return status;}public boolean pending(){return pending;}
    }
    public static RawJson encode(ResumeResult actual) {
        Objects.requireNonNull(actual);var values=new LinkedHashMap<String,Value>();
        values.put("status",new Text(actual.status().wire()));values.put("pending",new Bool(actual.pending()));
        values.put("snapshot",object(PublicSnapshotCodec.encodeSemanticData(actual.originalNumericSnapshot())));
        values.put("transition",actual.transition().<Value>map(RootDriverLifecycleResumeCodec::transition).orElse(Nil.INSTANCE));
        if(actual.transition().isPresent()) {
            values.put("player_decision_pending",new Bool(actual.playerDecisionPending()));
            values.put("cold_resume_binding",actual.coldBinding().<Value>map(value->cold(object(value.originalNumeric()),true)).orElse(Nil.INSTANCE));
            if(actual.status()==Status.UI_UNRESOLVED) {
                values.put("diagnostic",diagnostic(actual.diagnostic().orElseThrow()));values.put("action_submitted",new Bool(false));
            } else values.put("date_advanced",new Bool(actual.dateAdvanced()));
        }
        var result=json(new Obj(values));var decoded=decode(result);
        require(object(decoded.originalNumericSnapshot()).equals(object(actual.originalNumericSnapshot())),"resume snapshot changed original numeric/decimal JSON domain");
        return result;
    }
    public static RawJson encode(Data actual){return json(object(Objects.requireNonNull(actual).original));}
    public static Data decode(RawJson original) {
        Obj row=object(original);Status status=Status.parse(text(member(row,"status"),"status"));boolean pending=bool(member(row,"pending"));
        boolean hasTransition=member(row,"transition")!=Nil.INSTANCE;boolean unresolved=status==Status.UI_UNRESOLVED;
        Set<String> fields=hasTransition?(unresolved?Set.of("status","pending","player_decision_pending","snapshot","transition","cold_resume_binding","diagnostic","action_submitted"):Set.of("status","pending","player_decision_pending","date_advanced","snapshot","transition","cold_resume_binding")):Set.of("status","pending","snapshot","transition");
        exact(row,fields);boolean player=hasTransition&&bool(member(row,"player_decision_pending"));boolean advanced=hasTransition&&!unresolved&&bool(member(row,"date_advanced"));
        shape(status,pending,player,advanced,hasTransition,unresolved);RawJson snapshot=PublicSnapshotCodec.decodeSemanticData(json(asObject(member(row,"snapshot"))));
        if(hasTransition) {
            Obj transition=asObject(member(row,"transition"));validatePublicTransition(transition);
            if(Qualification.parse(text(member(transition,"status"),"transition status"))==Qualification.CAUSE_QUALIFIED)require(pending&&!advanced,"cause-qualified public DATA cannot claim verified continuation/date");
            else verifiedSnapshot(object(snapshot),actor(member(transition,"successor_character_id")),text(member(transition,"episode_run_id"),"successor run"));
            if(member(row,"cold_resume_binding")!=Nil.INSTANCE) {
                Obj retained=cold(asObject(member(row,"cold_resume_binding")),false);
                var proof=new LinkedHashMap<String,Value>();for(String key:COLD_PROOF)proof.put(key,member(transition,key));
                proof.put("reconciliation",estate(asObject(member(transition,"reconciliation")),false));
                for(String key:List.of("predecessor_binding","successor_episode_binding"))proof.put(key,binding(asObject(member(transition,key)),false));
                require(new Text(coldDigest(new Obj(proof))).equals(member(retained,"transition_sha256")),"cold public DATA changed its retained transition proof");
            }
            if(unresolved){require(!bool(member(row,"action_submitted")),"resume read does not submit an action");validateDiagnostic(asObject(member(row,"diagnostic")));}
        }
        PublicSnapshotCodec.publicNumbers(DriverJson.toNode(row),"");return new Data(original,snapshot,status,pending);
    }
    private static void shape(Status status,boolean pending,boolean player,boolean advanced,boolean transition,boolean diagnostic) {
        require(transition||status==Status.CLEAR&&!pending&&!player&&!advanced&&!diagnostic,"no-pending resume retains original clear four-field branch");
        require(status==Status.CLEAR?!pending:pending,"resume status/pending differ");
        require(player==(status==Status.DEFERRED_PLAYER_DECISION),"original player-decision branch differs");
        require(diagnostic==(status==Status.UI_UNRESOLVED),"original unresolved diagnostic branch differs");
        require(!advanced,"original public resume uses allow_close=False and grants no new date credit");
    }
    private static Obj transition(TransitionMaterial actual) {
        var out=new LinkedHashMap<String,Value>();out.put("status",new Text(actual.qualification().wire()));
        out.put("predecessor_character_id",number(actual.predecessorCharacterId()));out.put("successor_character_id",number(actual.successorCharacterId()));
        out.put("source_episode_run_id",new Text(actual.sourceEpisodeRunId()));out.put("episode_run_id",new Text(actual.episodeRunId()));out.put("date_raw",number(actual.dateRaw()));
        out.put("same_campaign_frame",new Bool(true));out.put("ck3_command_submitted",new Bool(false));out.put("process_restarted",new Bool(false));
        out.put("succession_lifecycle",object(actual.successionLifecycle()));out.put("reconciliation",estate(object(actual.reconciliation()),true));
        out.put("predecessor_binding",binding(object(actual.predecessorBinding()),true));out.put("successor_episode_binding",binding(object(actual.successorEpisodeBinding()),true));
        actual.timelineContinuation().ifPresent(value->out.put("timeline_blocker_continuation",timeline(value)));
        actual.successorUiObservation().ifPresent(value->out.put("successor_ui_observation",observation(object(value),true)));
        return new Obj(out);
    }
    private static void validatePublicTransition(Obj row) {
        var allowed=new java.util.HashSet<>(Set.of("status","predecessor_character_id","successor_character_id","source_episode_run_id","episode_run_id","date_raw","same_campaign_frame","ck3_command_submitted","process_restarted","succession_lifecycle","reconciliation","predecessor_binding","successor_episode_binding"));
        if(row.members().containsKey("timeline_blocker_continuation"))allowed.add("timeline_blocker_continuation");if(row.members().containsKey("successor_ui_observation"))allowed.add("successor_ui_observation");exact(row,allowed);
        Qualification q=Qualification.parse(text(member(row,"status"),"qualification"));int predecessor=actor(member(row,"predecessor_character_id")),successor=actor(member(row,"successor_character_id"));require(predecessor!=successor,"public transition actors differ");
        String source=text(member(row,"source_episode_run_id"),"source run"),run=text(member(row,"episode_run_id"),"successor run");require(!source.equals(run),"successor run differs");signed(member(row,"date_raw"));
        require(bool(member(row,"same_campaign_frame"))&&!bool(member(row,"ck3_command_submitted"))&&!bool(member(row,"process_restarted")),"original read-only transition flags required");
        SuccessionLifecycleCodec.decode(json(asObject(member(row,"succession_lifecycle"))).bytes());Obj reconciliation=estate(asObject(member(row,"reconciliation")),false);GoalCodec.decodeReconciliation(json(reconciliation).bytes());
        require(number(predecessor).equals(reconciliation.get("predecessor_character_id"))&&number(successor).equals(reconciliation.get("actual_successor_character_id"))&&new Text("matched").equals(reconciliation.get("verdict")),"public original M3 actors/verdict differ");
        binding(asObject(member(row,"predecessor_binding")),false);Obj next=binding(asObject(member(row,"successor_episode_binding")),false);
        if(q==Qualification.VERIFIED)verifiedBinding(next,successor,run);
        if(row.members().containsKey("timeline_blocker_continuation"))validatePublicTimeline(asObject(row.get("timeline_blocker_continuation")));
        if(row.members().containsKey("successor_ui_observation"))observation(asObject(row.get("successor_ui_observation")),false);
    }
    private static Obj timeline(TimelineContinuation value) {
        var row=new LinkedHashMap<String,Value>();row.put("status",new Text(value.status()));row.put("initial_query",object(RootDriverLifecyclePublicCodec.encodeTimelineOriginal(value.initialQuery())));
        row.put("close_result",value.closeResult().<Value>map(material->object(RootDriverLifecyclePublicCodec.encodeCloseMaterial(material))).orElse(Nil.INSTANCE));
        value.deferredEventObservation().ifPresent(raw->row.put("deferred_event_observation",observation(object(raw),true)));
        value.originalDeferredQuery().ifPresent(raw->row.put("original_deferred_query",object(RootDriverLifecyclePublicCodec.encodeTimelineOriginal(raw))));
        value.closeAttempted().ifPresent(flag->row.put("close_attempted",new Bool(flag)));value.uiClearanceVerified().ifPresent(flag->row.put("ui_clearance_verified",new Bool(flag)));
        value.ownerInterception().ifPresent(raw->row.put("owner_interception",object(raw)));return new Obj(row);
    }
    private static void validatePublicTimeline(Obj row) {
        var keys=new java.util.HashSet<>(Set.of("status","initial_query","close_result"));for(String key:List.of("deferred_event_observation","original_deferred_query","close_attempted","ui_clearance_verified","owner_interception"))if(row.members().containsKey(key))keys.add(key);exact(row,keys);
        String status=text(member(row,"status"),"timeline status");timelineStatus(status);RootDriverLifecyclePublicCodec.decodeTimelineOriginal(json(asObject(member(row,"initial_query"))));
        if(member(row,"close_result")!=Nil.INSTANCE){RootDriverLifecyclePublicCodec.decodeCloseData(json(asObject(row.get("close_result"))));require(row.get("close_attempted") instanceof Bool flag&&flag.value(),"actual Close once marker required");}
        require(row.members().containsKey("deferred_event_observation")==row.members().containsKey("original_deferred_query"),"original deferred pair required");
        if(row.members().containsKey("deferred_event_observation")){observation(asObject(row.get("deferred_event_observation")),false);RootDriverLifecyclePublicCodec.decodeTimelineOriginal(json(asObject(row.get("original_deferred_query"))));}
        if(row.members().containsKey("close_attempted"))require(bool(row.get("close_attempted")),"once marker true required");
        if(row.members().containsKey("ui_clearance_verified"))require(!bool(row.get("ui_clearance_verified")),"deferred UI cannot claim clearance");
        require(row.members().containsKey("owner_interception")==status.equals("deferred_owner_interception"),"interception presence differs");if(row.members().containsKey("owner_interception"))asObject(row.get("owner_interception"));
    }
    private static void timelineStatus(String value){require(Set.of("already_clear","close_required","deferred_player_decision","deferred_owner_interception","materially_cleared","independent_identity_unverified").contains(value),"original finite timeline continuation status required");}
    private static Obj diagnostic(Diagnostic value) {
        var failures=new ArrayList<Value>();for(var actual:value.failures()){var row=new LinkedHashMap<String,Value>();row.put("stage",new Text(actual.stage()));row.put("kind",new Text(actual.kind()));row.put("message",new Text(actual.message()));actual.errorType().ifPresent(text->row.put("error_type",new Text(text)));actual.error().ifPresent(text->row.put("error",new Text(text)));failures.add(new Obj(row));}
        return new Obj(Map.of("error",new Text(value.error()),"failures",new Arr(failures)));
    }
    private static void validateDiagnostic(Obj row){exact(row,Set.of("error","failures"));textValue(member(row,"error"));var values=array(member(row,"failures"),"failure capture");require(values.size()<=256,"bounded failures required");for(Value value:values){Obj failure=asObject(value);boolean exception=failure.members().containsKey("error_type");exact(failure,exception?Set.of("stage","kind","message","error_type","error"):Set.of("stage","kind","message"));text(member(failure,"stage"),"stage");text(member(failure,"kind"),"kind");textValue(member(failure,"message"));if(exception){text(member(failure,"error_type"),"error class");textValue(member(failure,"error"));}}}
    private static Obj estate(Obj row,boolean encode) {
        if(encode)GoalCodec.decodeReconciliation(json(row).bytes());
        for(String key:List.of("predecessor_binding","successor_binding")){Obj frame=asObject(member(row,key));frame=counter(counter(frame,"revision",encode),"native_revision",encode);row=row.with(key,frame);}
        if(!encode)GoalCodec.decodeReconciliation(json(row).bytes());return row;
    }
    private static final Set<String> BINDING=Set.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","episode_character_id","one_life_terminal","one_life_terminal_reason","played_character_id","played_character_alive","episode_binding_state","driver_state_restore_kind","bridge_pid","connection_generation");
    private static Obj binding(Obj original,boolean encode) {
        exact(original,BINDING);Obj numeric=original;if(!encode)for(String key:List.of("revision","native_revision","connection_generation"))numeric=counter(numeric,key,false);
        for(String key:List.of("revision","native_revision","connection_generation"))uint(member(numeric,key));
        signed(member(numeric,"date_raw"));actor(member(numeric,"episode_character_id"));actor(member(numeric,"played_character_id"));positivePid(member(numeric,"bridge_pid"));
        for(String key:List.of("snapshot_id","episode_run_id"))text(member(numeric,key),key);
        for(String key:List.of("episode_binding_state","driver_state_restore_kind"))nullableText(member(numeric,key));
        bool(member(numeric,"one_life_terminal"));bool(member(numeric,"played_character_alive"));nullableText(member(numeric,"one_life_terminal_reason"));
        Obj out=numeric;if(encode)for(String key:List.of("revision","native_revision","connection_generation"))out=counter(out,key,true);return out;
    }
    private static void verifiedBinding(Obj row,int successor,String run){require(number(successor).equals(row.get("episode_character_id"))&&number(successor).equals(row.get("played_character_id"))&&new Text(run).equals(row.get("episode_run_id"))&&bool(member(row,"played_character_alive"))&&!bool(member(row,"one_life_terminal"))&&member(row,"one_life_terminal_reason")==Nil.INSTANCE,"verified original successor binding required");}
    private static void verifiedSnapshot(Obj snapshot,int successor,String run){Obj played=asObject(member(snapshot,"played_character"));require(number(successor).equals(snapshot.get("episode_character_id"))&&new Text(run).equals(snapshot.get("episode_run_id"))&&number(successor).equals(played.get("character_id"))&&bool(member(played,"alive"))&&!bool(member(snapshot,"one_life_terminal"))&&member(snapshot,"one_life_terminal_reason")==Nil.INSTANCE,"verified transition differs from actual published living successor snapshot");}
    private static Obj cold(Obj original,boolean encode) {
        var expected=new java.util.HashSet<>(Set.of("schema","transition_sha256","observation_sha256","retained_frame","resumed_frame","machine_id","game_identity","ledger_sha256","connection_rebound","binding_sha256"));if(original.members().containsKey("source_epoch"))expected.add("source_epoch");exact(original,expected);
        require(new Text("xar.ck3.successor-ui-cold-binding/v1").equals(original.get("schema")),"original cold schema required");
        for(String key:List.of("transition_sha256","observation_sha256","ledger_sha256","binding_sha256"))sha(member(original,key));if(original.members().containsKey("source_epoch")&&original.get("source_epoch")!=Nil.INSTANCE)sha(member(original,"source_epoch"));text(member(original,"machine_id"),"machine");bool(member(original,"connection_rebound"));
        Obj game=asObject(member(original,"game_identity"));exact(game,Set.of("pid","creation_date","executable"));positivePid(member(game,"pid"));text(member(game,"creation_date"),"actual Game birth");text(member(game,"executable"),"actual Game image");
        Obj out=original.with("retained_frame",retainedColdFrame(asObject(member(original,"retained_frame")),encode))
                .with("resumed_frame",coldFrame(asObject(member(original,"resumed_frame")),encode));
        Obj numeric=encode?original:out;var fields=new LinkedHashMap<>(numeric.members());fields.remove("binding_sha256");
        require(new Text(coldDigest(new Obj(fields))).equals(member(numeric,"binding_sha256")),"cold binding digest differs from its original numeric DATA");
        Obj old=asObject(member(numeric,"retained_frame")),current=asObject(member(numeric,"resumed_frame"));
        require(member(game,"pid").equals(member(old,"bridge_pid"))&&member(game,"pid").equals(member(current,"bridge_pid")),"cold DATA Game/frame PID differs");
        boolean rebound=!member(old,"connection_generation").equals(member(current,"connection_generation"));
        require(bool(member(numeric,"connection_rebound"))==rebound,"cold DATA rebound flag differs");
        String oldActor=old.members().containsKey("played_character_id")?"played_character_id":"actor_character_id";
        require(member(old,oldActor).equals(member(current,"actor_character_id"))&&member(old,"episode_run_id").equals(member(current,"episode_run_id")),
                "cold DATA changed its retained actor/run");
        require(integer(member(current,"native_revision"),"native revision").compareTo(integer(member(old,"native_revision"),"retained native revision"))>=0
                &&signed(member(current,"date_raw"))>=signed(member(old,"date_raw"))
                &&(rebound||integer(member(current,"revision"),"public revision").compareTo(integer(member(old,"revision"),"retained public revision"))>=0),
                "cold DATA regressed its retained frame");
        return out;
    }
    /** Exactly the two original retained branches; a projected actor frame is not an original retained DTO. */
    private static Obj retainedColdFrame(Obj row,boolean encode) {
        if(row.members().keySet().equals(BINDING)) {
            Obj presented=binding(row,encode),numeric=encode?row:presented;
            require(uint(member(numeric,"native_revision")).signum()>0&&signed(member(numeric,"date_raw"))>=0,
                    "positive retained native revision and nonnegative date required");
            return presented;
        }
        if(row.members().keySet().equals(Set.of("bridge_pid","connection_generation","snapshot_id","revision","native_revision","date_raw","played_character_id","episode_run_id")))
            return coldFrame(row,encode,"played_character_id");
        throw new IllegalArgumentException("original retained cold frame must be a complete successor binding or observation frame");
    }
    private static Obj coldFrame(Obj row,boolean encode){return coldFrame(row,encode,"actor_character_id");}
    private static Obj coldFrame(Obj row,boolean encode,String actorField) {
        exact(row,Set.of("bridge_pid","connection_generation","snapshot_id","revision","native_revision","date_raw",actorField,"episode_run_id"));
        Obj numeric=row;if(!encode)for(String key:List.of("connection_generation","revision","native_revision"))numeric=counter(numeric,key,false);
        for(String key:List.of("connection_generation","revision","native_revision"))uint(member(numeric,key));
        require(uint(member(numeric,"native_revision")).signum()>0&&signed(member(numeric,"date_raw"))>=0,"positive cold native revision and nonnegative date required");
        positivePid(member(numeric,"bridge_pid"));actor(member(numeric,actorField));text(member(numeric,"snapshot_id"),"snapshot");text(member(numeric,"episode_run_id"),"run");
        Obj out=numeric;if(encode)for(String key:List.of("connection_generation","revision","native_revision"))out=counter(out,key,true);return out;
    }
    private static Obj observation(Obj original,boolean encode) {
        String schema=text(member(original,"schema"),"observation schema");boolean verified=schema.equals("xar.ck3.verified-successor-ui-service/v1");require(verified||schema.equals("xar.ck3.successor-ui-observation/v1"),"original UI observation schema required");
        var keys=new java.util.HashSet<>(Set.of("schema","frame","exact_ck3_build","exe_sha256","ui_clearance","timeline","event_instance_id","event_context_status","event_definition_key","event_root_scope","event_semantic_decision_ready","fresh_timeline_read_after_event_required","ordinary_event_policy_unchanged","caller_owned_process_and_query_source_proof_required","authorizes_close_or_save","authorizes_event_selection","business_cycle_credit","action_replay_authorized"));
        if(verified)keys.addAll(Set.of("verified_transition_sha256","campaign_goal","initial_handoff_frame","checkpoint_deferred","event_disappearance_is_clearance","continue_replay_authorized","close_replay_authorized"));exact(original,keys);
        text(member(original,"exact_ck3_build"),"build");sha(member(original,"exe_sha256"));require(Set.of("unknown","modal_present","unresolved","clear").contains(text(member(original,"ui_clearance"),"clearance")),"closed original UI clearance required");
        for(String key:List.of("ordinary_event_policy_unchanged","caller_owned_process_and_query_source_proof_required"))require(bool(member(original,key)),"original true observation flag required");
        for(String key:List.of("authorizes_close_or_save","authorizes_event_selection","action_replay_authorized"))require(!bool(member(original,key)),"observation grants no action");require(number(0).equals(member(original,"business_cycle_credit")),"observation grants no cycle credit");
        Value event=member(original,"event_instance_id");if(event!=Nil.INSTANCE)require(integer(event,"event instance").signum()>0&&integer(event,"event instance").compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"original positive signed32 event instance required");
        require(bool(member(original,"fresh_timeline_read_after_event_required"))==(event!=Nil.INSTANCE),"event read obligation differs");text(member(original,"event_context_status"),"event context status");for(String key:List.of("event_definition_key","event_root_scope"))nullableText(member(original,key));Value ready=member(original,"event_semantic_decision_ready");require(ready==Nil.INSTANCE||ready instanceof Bool,"nullable event readiness required");
        Obj frame=asObject(member(original,"frame"));exact(frame,Set.of("played_character_id","native_revision","date_raw","snapshot_id","revision","episode_run_id","bridge_pid","connection_generation"));Obj numeric=frame;if(!encode)for(String key:List.of("revision","native_revision","connection_generation"))numeric=counter(numeric,key,false);for(String key:List.of("revision","native_revision","connection_generation"))uint(member(numeric,key));actor(member(numeric,"played_character_id"));positivePid(member(numeric,"bridge_pid"));signed(member(numeric,"date_raw"));text(member(numeric,"snapshot_id"),"snapshot");text(member(numeric,"episode_run_id"),"run");Obj presented=numeric;if(encode)for(String key:List.of("revision","native_revision","connection_generation"))presented=counter(presented,key,true);
        Obj timeline=asObject(member(original,"timeline"));require(timeline.members().containsKey("snapshot_revision"),"original timeline revision required");timeline=counter(timeline,"snapshot_revision",encode);
        Obj out=original.with("frame",presented).with("timeline",timeline);
        if(verified){sha(member(original,"verified_transition_sha256"));GoalCodec.decodeGoal(json(asObject(member(original,"campaign_goal"))).bytes());out=out.with("initial_handoff_frame",binding(asObject(member(original,"initial_handoff_frame")),encode));bool(member(original,"checkpoint_deferred"));for(String key:List.of("event_disappearance_is_clearance","continue_replay_authorized","close_replay_authorized"))require(!bool(member(original,key)),"verified observation still grants no replay/clearance from disappearance");}
        return out;
    }
    private static Obj counter(Obj row,String field,boolean encode){Value value=member(row,field);BigInteger exact;if(encode)exact=uint(value);else{String wire=text(value,"public uint64 "+field);require(wire.length()<=20&&wire.matches("0|[1-9][0-9]*"),"canonical uint64 string required");exact=new PythonOnlyUInt64(new BigInteger(wire)).value();}return row.with(field,encode?new Text(exact.toString()):new IntegerValue(exact));}
    private static Obj object(RawJson value){return DriverJson.object(Objects.requireNonNull(value).bytes(),RawJson.MAXIMUM_BYTES);}
    private static Obj asObject(Value value){return org.xar.ck3.control.planning.opportunity.OpportunityJson.object(value,"actual original object");}
    private static RawJson json(Obj value){return PublicDataJson.encodeFullMaterial(value);}
    private static void exact(Obj value,Set<String> fields){require(value.members().keySet().equals(fields),"original resume component fields changed");}
    private static Value member(Obj value,String field){Value result=value.get(field);require(result!=null,"required original resume field missing: "+field);return result;}
    private static String text(String value){require(value!=null&&!value.isEmpty(),"nonempty original text required");return value;}
    private static String textValue(Value value){require(value instanceof Text,"original text token required");return ((Text)value).value();}
    private static String text(Value value,String field){String result=textValue(value);require(!result.isEmpty(),"nonempty "+field+" required");return result;}
    private static void nullableText(Value value){require(value==Nil.INSTANCE||value instanceof Text,"original nullable text required");}
    private static boolean bool(Value value){require(value instanceof Bool,"strict original boolean required");return ((Bool)value).value();}
    private static BigInteger uint(Value value){return new PythonOnlyUInt64(integer(value,"original uint64")).value();}
    private static int signed(Value value){BigInteger exact=integer(value,"signed32");require(exact.compareTo(BigInteger.valueOf(Integer.MIN_VALUE))>=0&&exact.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"original signed32 field outside range");return exact.intValue();}
    private static int actor(Value value){int id=signed(value);actor(id);return id;}
    private static void actor(int value){new NativeCharacterId(value);}
    private static void positivePid(Value value){BigInteger pid=integer(value,"PID");require(pid.signum()>0&&pid.compareTo(BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE))<=0,"actual uint32 PID required");}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static void sha(Value value){require(text(value,"SHA256").matches("[0-9a-fA-F]{64}"),"actual SHA256 text required");}
}
