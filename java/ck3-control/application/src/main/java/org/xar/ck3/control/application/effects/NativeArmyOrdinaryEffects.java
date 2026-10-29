package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyAssaultSelection;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyGatheringCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;

/** Actual ordinary troop effects. No dispatch method; every archived branch reuses the live reducer. */
public final class NativeArmyOrdinaryEffects implements NativeEffectRegistry.Observer {
    public static final String MATERIAL_SCHEMA="xar.java.army-ordinary-material/v1";
    public static final String SAMPLING_SCHEMA="xar.java.army-gathering-control/v1";
    public enum ReadKind { OCCUPATION, GATHERING }
    public record Query(ReadKind kind,int warId) {
        public Query { Objects.requireNonNull(kind);StrictJson.require(kind==ReadKind.OCCUPATION?warId>0:warId==0,"exact Army postquery subject required"); }
        public OperationKey operation() { return new OperationKey(kind==ReadKind.OCCUPATION?"query-war-occupation-targets-v1-"+warId:ArmyGatheringCodec.QUERY); }
    }
    /** Root supplies its registered real read catalog and currently borrowed writer Session. Empty means unavailable. */
    @FunctionalInterface public interface IndependentReadPort {
        Optional<PlanningReadReceipt> read(Query query,ActionCommand command,ActionState.Attempt attempt,Complete actualFrame);
    }
    /** Root installs M0's one full source-bound occupation decoder for both live and cold paths. */
    @FunctionalInterface public interface OccupationDecoder {
        List<ArmyAssaultSelection.Holding> holdings(Complete actualFrame,PlanningReadReceipt original,ActionPorts.OutcomeArchive archive);
    }
    private record Selection(Kind kind,int subject,boolean enabled) { }
    private final NativeEffectSnapshots snapshots;
    private final IndependentReadPort queries;
    private final NativeEffectEvidence.FrameLoader frames;
    private final Optional<OccupationDecoder> occupations;
    public NativeArmyOrdinaryEffects(NativeEffectSnapshots snapshots,IndependentReadPort actualQueries,
            NativeEffectEvidence.FrameLoader actualFrames,Optional<OccupationDecoder> actualOccupationDecoder) {
        this.snapshots=Objects.requireNonNull(snapshots);queries=Objects.requireNonNull(actualQueries);
        frames=Objects.requireNonNull(actualFrames);occupations=Objects.requireNonNull(actualOccupationDecoder);
    }
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source,OperationKey operation,RawJson arguments) {
        Selection selected=selection(before,operation,ArmyOrdinaryActionArguments.decode(arguments));
        return new ExpectedPostcondition(1,before,source,selected.kind()==Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1?SAMPLING_SCHEMA:MATERIAL_SCHEMA,values(selected));
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        ArmyOrdinaryActionArguments args=ArmyOrdinaryActionArguments.decode(command.arguments());
        Selection selected=selection(command.before(),command.operation(),args);
        if(selected.kind()==Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1)return sampling(command,attempt,dispatch,args,selected);
        // Decode the actual submission without turning its validator/queue observations into material.
        if(selected.kind()==Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1)
            return maaPending(command,attempt,dispatch,selected);
        if(!hasOutbound(dispatch))return NativeEffectRegistry.Projected.pending("original native outbound quote is unavailable; no action is replayed",List.of(attempt.guard().nativeEvidence()));
        NativeEffectSnapshots.Pair pair=snapshots.read(command,attempt);
        return snapshots.withArchive(archive->{
            List<PlanningReadReceipt> originals=originals(args,archive);
            List<ArmyAssaultSelection.Holding> holdings=holdings(pair.before(),originals,attempt,archive);
            Optional<PlanningReadReceipt> afterRead=Optional.empty();
            if(isAssault(selected)) {
                var original=ArmyAssaultSelection.select(pair.before().semantic(),holdings,selected.subject());
                if(original.isEmpty())return pending(pair,"original exact observable assault subject is unavailable");
                if(original.orElseThrow().source()==ArmyAssaultSelection.Source.OCCUPATION) {
                    if(occupations.isEmpty())return pending(pair,"source-bound occupation decoder is not installed");
                    afterRead=queries.read(new Query(ReadKind.OCCUPATION,original.orElseThrow().warId()),command,attempt,pair.after());
                    if(afterRead.isEmpty())return pending(pair,"independent owning-thread occupation query is unavailable");
                }
            }
            var projected=projectMaterial(command,attempt,dispatch,pair,args,selected,originals,afterRead,archive);
            if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
            List<PlanningReadReceipt> reads=new ArrayList<>(originals);afterRead.ifPresent(reads::add);
            ExactRef basis=snapshots.evidence(command,attempt,pair,reads,projected.compatibleResult().orElseThrow());
            return NativeEffectSnapshots.withEvidence(projected,List.of(basis));
        });
    }
    private NativeEffectRegistry.Projected maaPending(ActionCommand command,ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch,Selection selected) {
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty()||!hasOutbound(dispatch))
            return NativeEffectRegistry.Projected.pending(NativeRegularMaaSubmission.MATERIAL_GAP+"; original submission unresolved, never replay",List.of(attempt.guard().nativeEvidence()));
        return snapshots.withArchive(archive->{
            var original=NativeRegularMaaSubmission.original(command,attempt,ack,archive);
            var pair=snapshots.read(command,attempt);samePaused(pair.before(),pair.after());
            StrictJson.require(pair.before().identity().frame().identity().player().equals(pair.after().identity().frame().identity().player()),"MAA transport crossed the actual living player");
            if(original.submission().status()==NativeRegularMaaSubmission.Status.REJECTED)
                return maaRejection(command,attempt,original.submission(),archive.referenceOf(dispatch));
            return maaSubmissionPending(original.submission(),List.of(attempt.guard().nativeEvidence(),archive.referenceOf(dispatch)));
        });
    }
    private static NativeEffectRegistry.Projected maaRejection(ActionCommand command,ActionState.Attempt attempt,
            NativeRegularMaaSubmission.Submission original,ExactRef originalDispatch) {
        StrictJson.require(original.status()==NativeRegularMaaSubmission.Status.REJECTED,"only exact native MAA validator/queue rejection may settle without material");
        var rejected=new ActionState.Rejected(attempt.requestId(),"native_regular_maa_rejected:"+original.reason(),originalDispatch);
        ActionEffects.validate(command,attempt,rejected);
        return new NativeEffectRegistry.Projected(new ActionPorts.RejectionObserved(rejected),Optional.empty());
    }
    static NativeEffectRegistry.Projected maaSubmissionPending(NativeRegularMaaSubmission.Submission original,List<ExactRef> evidence) {
        return NativeEffectRegistry.Projected.pending(Objects.requireNonNull(original).pendingReason(),List.copyOf(evidence));
    }
    private NativeEffectRegistry.Projected projectMaterial(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair,ArmyOrdinaryActionArguments args,Selection selected,List<PlanningReadReceipt> originals,
            Optional<PlanningReadReceipt> afterRead,ActionPorts.OutcomeArchive archive) {
        requireDispatch(command,attempt,dispatch,archive);samePaused(pair.before(),pair.after());
        List<ArmyAssaultSelection.Holding> beforeHoldings=holdings(pair.before(),originals,attempt,archive);
        ObjectNode before=EffectJson.object(pair.before().semantic()),after=EffectJson.object(pair.after().semantic());
        BigInteger actor=command.before().frame().identity().player();ObjectNode result=StrictJson.object().put("step",command.operation().value());
        ObjectNode action=result.putObject("war_action");
        if(selected.kind()==Kind.RAISE_TROOPS_DEFAULT) {
            Map<Integer,ObjectNode> previous=armies(before),current=armies(after);List<Integer> raised=current.entrySet().stream()
                    .filter(entry->owned(entry.getValue(),actor) && !previous.containsKey(entry.getKey())).map(Map.Entry::getKey).sorted().toList();
            if(raised.isEmpty())return pending(pair,"no new independently observed controllable owned Army");
            action.put("status","raised");var ids=action.putArray("raised_army_ids");raised.forEach(ids::add);
        } else if(selected.kind()==Kind.DISBAND_ARMY) {
            Map<Integer,ObjectNode> previous=armies(before),current=armies(after);
            if(!previous.containsKey(selected.subject()) || !owned(previous.get(selected.subject()),actor))return pending(pair,"disband original owned controllable public Army is unavailable");
            if(current.containsKey(selected.subject()))return pending(pair,"selected public Army remains in the complete independently observed roster");
            action.put("status","disbanded").put("army_id",selected.subject());
        } else {
            var initial=ArmyAssaultSelection.select(pair.before().semantic(),beforeHoldings,selected.subject());
            if(initial.isEmpty())return pending(pair,"original exact assault location is unavailable or ambiguous");
            var origin=initial.orElseThrow();boolean start=selected.kind()==Kind.START_ASSAULT;
            StrictJson.require(start?!origin.siege().inProgress() && origin.siege().canStart():origin.siege().inProgress() && origin.siege().canStop(),"original assault eligibility changed");
            List<ArmyAssaultSelection.Holding> postHoldings=List.of();
            if(origin.source()==ArmyAssaultSelection.Source.OCCUPATION) {
                if(afterRead.isEmpty() || occupations.isEmpty())return pending(pair,"required independent occupation result is unavailable");
                PlanningReadReceipt read=afterRead.orElseThrow();
                NativeEffectSnapshots.requireAfterRead(command,attempt,pair.after(),read,new Query(ReadKind.OCCUPATION,origin.warId()).operation());
                NativeRecordedEvidenceVerifier.requireRead(read,archive);
                postHoldings=List.copyOf(occupations.orElseThrow().holdings(pair.after(),read,archive));
            } else StrictJson.require(afterRead.isEmpty(),"objective assault cannot borrow unrelated postquery evidence");
            var observed=ArmyAssaultSelection.select(pair.after().semantic(),postHoldings,selected.subject());
            if(observed.isEmpty() || observed.orElseThrow().warId()!=origin.warId() || observed.orElseThrow().provinceId()!=origin.provinceId()
                    || observed.orElseThrow().siege().inProgress()!=start)return pending(pair,"same complete SiegeID/war/province flag transition is not independently observed");
            action.put("status",start?"assault_started":"assault_stopped").put("siege_id",selected.subject()).put("war_id",origin.warId())
                    .put("province_id",origin.provinceId()).put("assault_in_progress",start)
                    .put("observation_source",observed.orElseThrow().source()==ArmyAssaultSelection.Source.OBJECTIVE?"war_objective_snapshot":"war_occupation_query");
            result.set("assault_action",action.deepCopy());
        }
        action.put("postcondition_verified",true);result.put("snapshot_id",pair.after().identity().frame().snapshotId())
                .put("revision",pair.after().identity().frame().revision()).put("original_outbound_sha256",DriverJson.sha256(outbound(dispatch)));
        return NativeEffectSnapshots.observed(command,attempt,pair.after(),MATERIAL_SCHEMA,values(selected),NativeEffectSnapshots.publication(pair.after()),EffectJson.raw(result),List.of());
    }
    private NativeEffectRegistry.Projected sampling(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            ArmyOrdinaryActionArguments args,Selection selected) {
        if(!(dispatch instanceof NativeActionPort.AckReceived actualAck) || !actualAck.nativeOk() || !hasOutbound(dispatch))
            return NativeEffectRegistry.Projected.pending("sampling requires its exact successful original submission and outbound packet; no control is inferred from UNKNOWN",List.of(attempt.guard().nativeEvidence()));
        if(args.preflightReads().size()!=1)return NativeEffectRegistry.Projected.pending("original independent sampling state baseline is unavailable; do not repeat the submitted control",List.of(attempt.guard().nativeEvidence()));
        return snapshots.withArchive(archive->{
            Complete before=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
            List<PlanningReadReceipt> pre=originals(args,archive);
            StrictJson.require(pre.size()==1,"sampling requires exactly its original independent preflight state query");
            requireBeforeRead(before,pre.getFirst(),attempt,ArmyGatheringCodec.QUERY);
            var post=queries.read(new Query(ReadKind.GATHERING,0),command,attempt,before);
            if(post.isEmpty())return NativeEffectRegistry.Projected.pending("independent Gathering state query unavailable; capture state is not inferred from ACK",List.of(before.originalEvidence()));
            return projectSampling(command,attempt,dispatch,args,selected,before,pre.getFirst(),post.orElseThrow(),archive,frames);
        });
    }
    private static NativeEffectRegistry.Projected projectSampling(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,
            ArmyOrdinaryActionArguments args,Selection selected,Complete before,PlanningReadReceipt pre,PlanningReadReceipt post,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames) {
        requireDispatch(command,attempt,dispatch,archive);requireBeforeRead(before,pre,attempt,ArmyGatheringCodec.QUERY);
        NativeRecordedEvidenceVerifier.requireRead(post,archive);
        Complete postBefore=RootGuardEvidence.loadFrame(post.before().binding(),archive,frames),after=RootGuardEvidence.loadFrame(post.after().binding(),archive,frames);
        sameControlFrame(before,postBefore);sameControlFrame(postBefore,after);samePaused(before,after);
        StrictJson.require(post.request().operation().equals(new OperationKey(ArmyGatheringCodec.QUERY)) && post.request().before().equals(postBefore.identity())
                && post.request().source().equals(command.source()) && post.request().sessionId().equals(command.sessionId())
                && post.before().originalBindingSha256().equals(post.after().originalBindingSha256())
                && !post.requestId().equals(attempt.requestId()) && !post.requestId().equals(pre.requestId()),"sampling postquery crossed actual frame/source/session/submission");
        if(!(dispatch instanceof NativeActionPort.AckReceived submission) || submission.custody().isEmpty()
                || pre.original().custody().isEmpty() || post.original().custody().isEmpty())
            return NativeEffectRegistry.Projected.pending("original endpoint chronology is unavailable; historical ACK or native frame time cannot grant sampling freshness",List.of(archive.readReferenceOf(post)));
        NativeRequestChronology.requireBeforeSubmission(pre,attempt,submission);
        NativeRequestChronology.requireSampledAfter(post,attempt,submission);
        ArmyGatheringCodec.State previous=ArmyGatheringCodec.decode(token(pre).bytes(),ArmyGatheringCodec.QUERY);
        ArmyGatheringCodec.State observed=ArmyGatheringCodec.decode(token(post).bytes(),ArmyGatheringCodec.QUERY);
        if(!samplingTransition(previous,observed,selected.enabled()))
            return NativeEffectRegistry.Projected.pending("independent capture gate/epoch/clear state does not prove requested sampling control",List.of(archive.readReferenceOf(post)));
        var control=new ActionState.ControlApplied(post,SAMPLING_SCHEMA,values(selected));ActionEffects.validate(command,attempt,dispatch,control);
        ObjectNode result=StrictJson.object().put("step",command.operation().value()).put("status",selected.enabled()?"enabled":"disabled")
                .put("capture_enabled",observed.enabled()).put("capture_epoch",observed.epoch()).put("control_verified",true)
                .put("native_gameplay_verified",false).put("military_readiness_verified",false).put("automatic_retry",false)
                .put("original_outbound_sha256",DriverJson.sha256(outbound(dispatch)));
        return new NativeEffectRegistry.Projected(new ActionPorts.ControlObserved(control),Optional.of(EffectJson.raw(result)));
    }
    public static boolean samplingTransition(ArmyGatheringCodec.State previous,ArmyGatheringCodec.State observed,boolean enabled) {
        if(observed.enabled()!=enabled || !enabled && (!observed.clearCompleted() || observed.busy()))return false;
        BigInteger expected=previous.epoch();
        if(enabled?!previous.enabled():previous.enabled() || !previous.clearCompleted())expected=expected.add(BigInteger.ONE);
        return observed.epoch().equals(expected);
    }
    public NativeRecordedEvidenceVerifier.Binding archivedVerifier(OperationKey operation,ExactRef source,NativeEffectEvidence.FrameLoader originalFrames) {
        Objects.requireNonNull(originalFrames);
        return new NativeRecordedEvidenceVerifier.Binding(operation,source,(head,receipt,archive)->{
            StrictJson.require(receipt.command().operation().equals(operation) && receipt.state() instanceof ActionState.Settled,"ordinary Army replay requires original settled command");
            var settled=(ActionState.Settled)receipt.state();var args=ArmyOrdinaryActionArguments.decode(receipt.command().arguments());
            Selection selected=selection(receipt.command().before(),operation,args);
            if(selected.kind()==Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1) {
                StrictJson.require(settled.settlement() instanceof ActionState.Rejected&&settled.dispatch() instanceof NativeActionPort.AckReceived,NativeRegularMaaSubmission.MATERIAL_GAP+"; only original native rejection is importable");
                var rejected=(ActionState.Rejected)settled.settlement();var ack=(NativeActionPort.AckReceived)settled.dispatch();
                var original=NativeRegularMaaSubmission.original(receipt.command(),settled.attempt(),ack,archive);
                StrictJson.require(rejected.originalEvidence().equals(archive.referenceOf(ack)),"archived MAA rejection lost exact original dispatch custody");
                var replayed=maaRejection(receipt.command(),settled.attempt(),original.submission(),rejected.originalEvidence());
                StrictJson.require(replayed.result() instanceof ActionPorts.RejectionObserved actual&&actual.rejection().equals(rejected)&&replayed.compatibleResult().isEmpty(),"archived MAA rejected settlement differs from actual original submission");
                return;
            }
            if(selected.kind()==Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1) {
                StrictJson.require(settled.settlement() instanceof ActionState.ControlApplied,"sampling replay cannot grant gameplay settlement");
                var control=(ActionState.ControlApplied)settled.settlement();StrictJson.require(control.supportingReads().isEmpty(),"sampling original query cannot borrow another control's evidence");
                Complete before=RootGuardEvidence.loadFrame(settled.attempt().guard(),archive,originalFrames);
                List<PlanningReadReceipt> pre=originals(args,archive);StrictJson.require(pre.size()==1,"original sampling preflight lost");
                var projected=projectSampling(receipt.command(),settled.attempt(),settled.dispatch(),args,selected,before,pre.getFirst(),control.read(),archive,originalFrames);
                StrictJson.require(projected.result() instanceof ActionPorts.ControlObserved && ((ActionPorts.ControlObserved)projected.result()).observation().equals(control),"sampling archived independent-state replay differs");
                return;
            }
            var original=NativeEffectEvidence.load(receipt,archive,originalFrames);
            StrictJson.require(original.supportingMaterials().isEmpty(),"ordinary Army cannot borrow unrelated domain materials");
            List<PlanningReadReceipt> pre=originals(args,archive);List<PlanningReadReceipt> all=original.independentReads();
            StrictJson.require(all.size()>=pre.size() && all.subList(0,pre.size()).equals(pre) && all.size()<=pre.size()+1,"Army original preflight/postquery custody changed");
            Optional<PlanningReadReceipt> post=all.size()==pre.size()?Optional.empty():Optional.of(all.getLast());
            var replayed=projectMaterial(receipt.command(),settled.attempt(),settled.dispatch(),original.frames(),args,selected,pre,post,archive);
            replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
        });
    }
    private List<ArmyAssaultSelection.Holding> holdings(Complete before,List<PlanningReadReceipt> reads,ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive) {
        List<ArmyAssaultSelection.Holding> rows=new ArrayList<>();
        for(PlanningReadReceipt read:reads) {
            String operation=read.request().operation().value();requireBeforeRead(before,read,attempt,operation);
            if(operation.startsWith("query-war-occupation-targets-v1-")) {
                if(occupations.isEmpty())continue;
                rows.addAll(occupations.orElseThrow().holdings(before,read,archive));
            } else StrictJson.require(operation.equals("query-player-default-raise-v1"),"unrelated original preflight cannot become Army material evidence");
        }
        return List.copyOf(rows);
    }
    private static List<PlanningReadReceipt> originals(ArmyOrdinaryActionArguments args,ActionPorts.OutcomeArchive archive) {
        return args.preflightReads().stream().map(ref->{PlanningReadReceipt read=archive.loadRead(ref);StrictJson.require(archive.readReferenceOf(read).equals(ref),"Army original preflight reference changed");NativeRecordedEvidenceVerifier.requireRead(read,archive);return read;}).toList();
    }
    private static void requireBeforeRead(Complete before,PlanningReadReceipt read,ActionState.Attempt attempt,String operation) {
        StrictJson.require(read.request().operation().value().equals(operation) && read.request().before().equals(before.identity())
                && read.request().source().equals(before.source()) && read.request().sessionId().equals(before.sessionId())
                && !read.requestId().equals(attempt.requestId()),"Army original preflight source/frame/request changed");
        for(var guard:List.of(read.before(),read.after()))
            StrictJson.require(guard.binding().observed().equals(before.identity()) && guard.binding().nativeEvidence().equals(before.originalEvidence())
                    && guard.binding().source().equals(before.source()) && guard.binding().sessionId().equals(before.sessionId())
                    && guard.binding().connectionGeneration().equals(before.connectionGeneration()) && guard.originalBindingSha256().equals(before.fullBindingSha256())
                    && !guard.binding().observedAt().isAfter(attempt.submittedAt()),"Army original preflight crossed full Driver/native source or submission");
        token(read);
    }
    private static RawJson token(PlanningReadReceipt read) {
        StrictJson.require(read.original().nativeOk() && read.original().originalResultToken().isPresent(),"successful actual independent Native result required");
        return read.original().originalResultToken().orElseThrow();
    }
    private static Selection selection(ObservationIdentity before,OperationKey operation,ArmyOrdinaryActionArguments args) {
        ObjectNode n=EffectJson.object(EffectJson.parse(args.publicArguments()));Set<String> required=new HashSet<>(),optional=new HashSet<>(Set.of("expected_revision"));
        int subject=0;boolean enabled=false;String expected;
        switch(args.kind()) {
            case RAISE_TROOPS_DEFAULT -> expected="raise-troops-default";
            case DISBAND_ARMY -> {required.add("army_id");subject=(int)StrictJson.integer(n.get("army_id"),0,Integer.MAX_VALUE);expected="disband-army-"+subject;}
            case START_ASSAULT,STOP_ASSAULT -> {required.add("siege_id");subject=(int)StrictJson.integer(n.get("siege_id"),1,Integer.MAX_VALUE);expected=(args.kind()==Kind.START_ASSAULT?"start-assault-":"stop-assault-")+subject;}
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> {required.addAll(Set.of("enabled","expected_revision"));enabled=EffectJson.bool(n.get("enabled"));expected=enabled?ArmyGatheringCodec.ENABLE:ArmyGatheringCodec.DISABLE;}
            case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> {required.addAll(Set.of("type_index","action_id","expected_revision"));optional.add("timeout_seconds");subject=(int)StrictJson.integer(n.get("type_index"),0,Integer.MAX_VALUE);String action=StrictJson.text(n.get("action_id"));StrictJson.require(!action.isEmpty() && action.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=63,"original MAA action identity required");if(n.has("timeout_seconds"))StrictJson.require(n.get("timeout_seconds").isNumber() && n.get("timeout_seconds").decimalValue().signum()>0,"positive native MAA timeout required");expected="maa-regular-personal-create-private-v1";}
            default -> throw new IllegalArgumentException("ordinary Army effect belongs to a different sole owner");
        }
        Set<String> names=new HashSet<>();n.fieldNames().forEachRemaining(names::add);Set<String> allowed=new HashSet<>(required);allowed.addAll(optional);
        StrictJson.require(names.containsAll(required) && allowed.containsAll(names) && operation.value().equals(expected),"exact Army operation/public arguments differ");
        if(n.has("expected_revision") && !n.get("expected_revision").isNull()) {
            String revision=StrictJson.text(n.get("expected_revision"));StrictJson.require(revision.matches("0|[1-9][0-9]*") && new BigInteger(revision).equals(before.frame().revision()),"canonical original public revision differs");
        } else StrictJson.require(!required.contains("expected_revision"),"required original public revision missing");
        return new Selection(args.kind(),subject,enabled);
    }
    private static List<ExpectedValue> values(Selection s) {
        List<ExpectedValue> values=new ArrayList<>();values.add(new ExpectedText(new FieldKey("army_action_kind"),s.kind().wire()));
        if(s.kind()==Kind.SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1) {
            values.add(new ExpectedBoolean(new FieldKey("capture_enabled"),s.enabled()));values.add(new ExpectedBoolean(new FieldKey("sampling_control_verified"),true));
            values.add(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false));values.add(new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false));
        } else {
            values.add(new ExpectedBoolean(new FieldKey("material_verified"),true));
            if(s.kind()!=Kind.RAISE_TROOPS_DEFAULT)values.add(new ExpectedInteger(new FieldKey(isAssault(s)?"siege_id":s.kind()==Kind.DISBAND_ARMY?"army_id":"type_index"),BigInteger.valueOf(s.subject())));
        }
        return List.copyOf(values);
    }
    private static boolean isAssault(Selection s) { return s.kind()==Kind.START_ASSAULT || s.kind()==Kind.STOP_ASSAULT; }
    private static NativeEffectRegistry.Projected pending(NativeEffectSnapshots.Pair pair,String reason) { return NativeEffectRegistry.Projected.pending(reason,List.of(pair.after().originalEvidence())); }
    private static Map<Integer,ObjectNode> armies(ObjectNode snapshot) {
        JsonNode rows=snapshot.get("player_armies");StrictJson.require(rows!=null && rows.isArray(),"complete actual player Army roster required");Map<Integer,ObjectNode> result=new LinkedHashMap<>();
        for(JsonNode raw:rows) {ObjectNode row=EffectJson.object(raw);int id=(int)StrictJson.integer(row.get("army_id"),0,Integer.MAX_VALUE);StrictJson.require(result.putIfAbsent(id,row)==null,"duplicate complete public Army identity");}
        return result;
    }
    private static boolean owned(ObjectNode row,BigInteger actor) {
        JsonNode owner=row.get("owner_character_id"),controllable=row.get("controllable");
        if(owner==null || owner.isNull() || controllable==null || controllable.isNull())return false;
        StrictJson.require(owner.isIntegralNumber() && owner.bigIntegerValue().signum()>=0,"exact nonnegative observed Army owner required");
        return actor.equals(owner.bigIntegerValue()) && EffectJson.bool(controllable);
    }
    private static void samePaused(Complete before,Complete after) {
        for(Complete frame:List.of(before,after)) {ObjectNode semantic=EffectJson.object(frame.semantic());StrictJson.trueValue(semantic.get("paused"));StrictJson.trueValue(semantic.get("map_ready"));StrictJson.trueValue(EffectJson.object(semantic.get("played_character")).get("alive"));}
        StrictJson.require(before.identity().frame().identity().dateRaw().equals(after.identity().frame().identity().dateRaw()),"paused Army action crossed native date");
    }
    private static void sameControlFrame(Complete before,Complete after) {
        StrictJson.require(before.identity().game().equals(after.identity().game()) && before.source().equals(after.source()) && before.sessionId().equals(after.sessionId())
                && before.connectionGeneration().equals(after.connectionGeneration()) && before.identity().frame().episodeRunId().equals(after.identity().frame().episodeRunId())
                && before.identity().frame().identity().equals(after.identity().frame().identity()) && after.identity().frame().revision().compareTo(before.identity().frame().revision())>=0,"capture control crossed actual native/player/date/Game/source frame");
    }
    private static boolean hasOutbound(NativeActionPort.DispatchOutcome outcome) {
        return outcome instanceof NativeActionPort.AckReceived ack?ack.nativeOk() && ack.outbound().isPresent():outcome instanceof NativeActionPort.Unknown unknown && unknown.originalRequestPacket().length>4;
    }
    private static byte[] outbound(NativeActionPort.DispatchOutcome outcome) {
        if(outcome instanceof NativeActionPort.AckReceived ack)return ack.outbound().orElseThrow().originalPacket();
        return ((NativeActionPort.Unknown)outcome).originalRequestPacket();
    }
    private static void requireDispatch(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(hasOutbound(dispatch) && dispatch.requestId().equals(attempt.requestId()) && dispatch.equals(archive.load(archive.referenceOf(dispatch))),"actual original Army dispatch custody changed");
        byte[] bytes=outbound(dispatch);StrictJson.require(bytes.length>4 && ByteBuffer.wrap(bytes,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==bytes.length-4,"original native outbound packet framing changed");
        ObjectNode packet=EffectJson.object(StrictJson.parse(Arrays.copyOfRange(bytes,4,bytes.length)));
        ObjectNode expected=EffectJson.object(EffectJson.parse(attempt.preparedRequest().additionalFields())).deepCopy();
        StrictJson.require(!expected.has("type") && !expected.has("protocol_version") && !expected.has("request_id") && !expected.has("step") && !expected.has("expected_revision"),"prepared native fields collide with wire envelope");
        expected.put("type","execute_step").put("protocol_version",1).put("request_id",attempt.requestId()).put("step",command.operation().value())
                .put("expected_revision",command.before().frame().identity().nativeRevision());
        StrictJson.require(Arrays.equals(StrictJson.canonical(expected,StrictJson.EXPLICIT_MAX_BYTES),StrictJson.canonical(packet,StrictJson.EXPLICIT_MAX_BYTES))
                && attempt.preparedRequest().step().equals(command.operation().value()),"original actual outbound differs from sole durable native preparation");
    }
}
