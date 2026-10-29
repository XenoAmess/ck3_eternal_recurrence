package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.military.OrdinaryAutomaticSurrenderPolicy;
import org.xar.ck3.control.application.planning.military.OrdinaryWhitePeacePolicy;
import org.xar.ck3.control.application.planning.military.WarDeclarationContinuity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.wave2.military.exitresult.OrdinaryWarExitObservationCodec;

/**
 * Original generic Driver results from one canonical action's retained originals.
 * This is a pure presenter: no query, submission, writer mutation or qualification.
 */
public final class RootWarActionExecutionResult {
    private RootWarActionExecutionResult() { }
    private static final Set<ArmyOrdinaryActionArguments.Kind> KINDS=Set.of(
            ArmyOrdinaryActionArguments.Kind.MOVE_ARMY,ArmyOrdinaryActionArguments.Kind.START_ASSAULT,
            ArmyOrdinaryActionArguments.Kind.STOP_ASSAULT,ArmyOrdinaryActionArguments.Kind.DECLARE_WAR,
            ArmyOrdinaryActionArguments.Kind.ENFORCE_DEMANDS,ArmyOrdinaryActionArguments.Kind.SURRENDER_WAR,
            ArmyOrdinaryActionArguments.Kind.OFFER_WHITE_PEACE);
    private static final Set<String> TERMINATION_ACK=Set.of("step","accepted","status","backend_id");

    /** Caller must hold the original writer session; every locator is reopened from that same archive. */
    public static RawJson present(ActionReceipt actual,ActionPorts.OutcomeArchive archive,Session same,
            PublicPlanningCodec.ExecuteRequest caller,NativeEffectEvidence.FrameLoader actualFrames) throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(archive);Objects.requireNonNull(same);
        Objects.requireNonNull(caller);Objects.requireNonNull(actualFrames);
        StrictJson.require(caller.step().equals(actual.command().operation()),"war result belongs to another public step");
        ActionPorts.OutcomeArchive bound=archive.withSession(same);
        ActionReceipt canonical=ContinuityActionJournal.lookup(same.head().state(),actual.command().actionId(),bound)
                .orElseThrow(()->new IOException("war result is absent from the actual canonical writer"));
        StrictJson.require(canonical.equals(actual),"war result is not the exact current canonical receipt");
        requireObservedState(actual.state());
        var command=actual.command();var args=ArmyOrdinaryActionArguments.decode(command.arguments());
        StrictJson.require(KINDS.contains(args.kind()) && command.origin() instanceof CommandOrigin.Gameplay,
                "result presenter received another action family or origin");
        ArmyCalls.Call call=ArmyCallCodec.decode(PublicMethod.valueOf(args.kind().name()),args.publicArguments());
        call.revision().requireCurrent(command.before().frame().revision());
        StrictJson.require(step(call).equals(command.operation().value()),"war arguments changed the actual primitive");
        var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();
        StrictJson.require(attempt.preparedRequest().equals(bound.loadRequest(bound.requestReferenceOf(attempt.preparedRequest()))),
                "original prepared primitive custody changed");
        var dispatch=ActionTransitions.dispatch(actual.state()).orElseThrow();
        StrictJson.require(dispatch.equals(bound.load(bound.referenceOf(dispatch))) && dispatch.requestId().equals(attempt.requestId()),
                "original war dispatch custody changed");
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))
            throw new IOException("original war ACK is UNKNOWN; no original full result or resubmission is available");
        DispatchMaterial originalDispatch=ack(command,attempt,ack);
        Obj primitive=originalDispatch.primitive().orElse(null);
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),bound,actualFrames);
        RootGuardEvidence.requireHistory(attempt.guard(),bound,same);
        var material=NativeEffectEvidence.loadIfPresent(actual,bound,actualFrames)
                .orElseThrow(()->new IOException("actual independent post-frame originals are missing for the full war result"));
        StrictJson.require(material.frames().before().equals(before),"effect and guard reconstruct different original before frames");
        Complete after=material.frames().after();
        var reads=replayReads(before,args,bound);
        Obj result=!ack.nativeOk()?negativeMove(call,before.semantic(),after.semantic(),originalDispatch.request(),
                originalDispatch.response(),originalDispatch.requestId()):switch(args.kind()) {
            case MOVE_ARMY -> move((ArmyCalls.Move)call,primitive,before.semantic(),after.semantic());
            case START_ASSAULT,STOP_ASSAULT -> assault((ArmyCalls.Siege)call,primitive,before,after,reads,material,bound);
            case ENFORCE_DEMANDS -> enforce((ArmyCalls.War)call,primitive,before.semantic(),after.semantic());
            case OFFER_WHITE_PEACE -> {
                var decision=OrdinaryWhitePeacePolicy.evaluate(NativeOrdinaryWarAdmission.policyView(before,reads,bound),
                        ((ArmyCalls.War)call).warId().intValueExact());
                StrictJson.require(decision instanceof OrdinaryWhitePeacePolicy.Ready,"original white-peace evidence no longer reproduces its policy");
                yield white((ArmyCalls.War)call,primitive,before.semantic(),after.semantic(),(OrdinaryWhitePeacePolicy.Ready)decision);
            }
            case SURRENDER_WAR -> {
                StrictJson.require(args.executionProfile()==ArmyOrdinaryActionArguments.ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER,
                        "generic surrender result requires its original automatic producer, never the SDK explicit route");
                var ready=ArmyOrdinaryActionPreparation.replayAutomaticSurrenderEvidence(command,before,bound);
                StrictJson.require(args.automaticSurrender().orElseThrow()==ready.variant(),"original surrender variant changed");
                yield surrender((ArmyCalls.War)call,primitive,before.semantic(),after.semantic(),ready);
            }
            case DECLARE_WAR -> {
                var prior=ContinuityActionJournal.receiptsBeforeIntent(same.head().state(),command.actionId(),bound);
                var continuity=WarDeclarationContinuity.replay(actual,prior,before,after,bound);
                yield declaration((ArmyCalls.Declaration)call,primitive,after.semantic(),continuity);
            }
            default -> throw new IllegalArgumentException("finite original war result family");
        };
        return ArmyPublicWire.encodeExactSourceBound(result,new ArmyTypes.Context(command.before(),command.source(),
                command.sessionId(),command.deadline()));
    }

    /** Missing after-frame evidence remains UNKNOWN. This check does not collect or replay a request. */
    static void requireObservedState(ActionState state) throws IOException {
        if(!(state instanceof ActionState.Settled settled) || !(settled.settlement() instanceof ActionState.Applied))
            throw new IOException("full original war result requires a retained independently observed post-frame; UNKNOWN is never resubmitted");
    }

    private static String step(ArmyCalls.Call call) {
        return switch(call.method()) {
            case MOVE_ARMY -> "move-army-"+((ArmyCalls.Move)call).army().value()+"-to-"+((ArmyCalls.Move)call).target().value();
            case START_ASSAULT -> "start-assault-"+((ArmyCalls.Siege)call).siege().value();
            case STOP_ASSAULT -> "stop-assault-"+((ArmyCalls.Siege)call).siege().value();
            case DECLARE_WAR -> "declare-war-"+((ArmyCalls.Declaration)call).declarationId();
            case ENFORCE_DEMANDS -> "enforce-demands-"+((ArmyCalls.War)call).warId();
            case SURRENDER_WAR -> "surrender-war-"+((ArmyCalls.War)call).warId();
            case OFFER_WHITE_PEACE -> "offer-white-peace-"+((ArmyCalls.War)call).warId();
            default -> throw new IllegalArgumentException("not one of the seven original generic war actions");
        };
    }

    /** Validate the retained actual framed packets, not the expected action result. */
    private record DispatchMaterial(Optional<Obj> primitive,Obj request,Obj response,String requestId) { }
    private static DispatchMaterial ack(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived actual) {
        StrictJson.require(actual.requestId().equals(attempt.requestId()) && actual.outbound().isPresent(),
                "actual original ACK/outbound request pair is missing");
        Obj response=packet(actual.originalPacket());
        StrictJson.require(response.equals(json(actual.originalFrame())) && text(response,"type").equals("command_result")
                && integer(response,"protocol_version").equals(BigInteger.ONE)
                && text(response,"request_id").equals(attempt.requestId()) && bool(response,"ok")==actual.nativeOk(),
                "original command-result frame/custody differs");
        Obj outgoing=packet(actual.outbound().orElseThrow().originalPacket());
        var expected=fields(json(attempt.preparedRequest().additionalFields()));
        for(String field:List.of("type","protocol_version","request_id","step","expected_revision"))
            StrictJson.require(!expected.containsKey(field),"prepared fields overlap native envelope");
        expected.put("type",new Text("execute_step"));expected.put("protocol_version",new IntegerValue(BigInteger.ONE));
        expected.put("request_id",new Text(attempt.requestId()));expected.put("step",new Text(command.operation().value()));
        expected.put("expected_revision",new IntegerValue(command.before().frame().identity().nativeRevision()));
        StrictJson.require(outgoing.equals(new Obj(expected)) && attempt.preparedRequest().step().equals(command.operation().value()),
                "retained outbound differs from the original canonical preparation");
        if(!actual.nativeOk()) {
            text(response,"error");
            StrictJson.require(actual.originalResultToken().isEmpty(),"negative native ACK cannot substitute a successful result token");
            return new DispatchMaterial(Optional.empty(),outgoing,response,attempt.requestId());
        }
        StrictJson.require(actual.originalResultToken().isPresent(),"successful original ACK token is missing");
        Obj result=json(actual.originalResultToken().orElseThrow());
        StrictJson.require(result.equals(response.get("result")) && text(result,"step").equals(command.operation().value()),
                "original native result token differs from its command-result frame");
        var output=fields(result);output.put("backend_id",new Text("native-headless"));
        return new DispatchMaterial(Optional.of(new Obj(output)),outgoing,response,attempt.requestId());
    }
    private static Obj packet(byte[] bytes) {
        StrictJson.require(bytes.length>4 && bytes.length<=DriverJson.MAX_NATIVE_BYTES+4
                && ByteBuffer.wrap(bytes,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==bytes.length-4,
                "original native packet length prefix differs");
        return DriverJson.object(Arrays.copyOfRange(bytes,4,bytes.length),DriverJson.MAX_NATIVE_BYTES);
    }

    private static List<ArmyOrdinaryPreflight.Read> replayReads(Complete before,ArmyOrdinaryActionArguments args,
            ActionPorts.OutcomeArchive bound) {
        var result=new ArrayList<ArmyOrdinaryPreflight.Read>();
        for(ExactRef reference:args.preflightReads()) {
            var read=bound.loadRead(reference);NativeRecordedEvidenceVerifier.requireRead(read,bound);
            StrictJson.require(bound.readReferenceOf(read).equals(reference),"preflight read reference changed");
            ArmyOrdinaryPreflight.bind(read,before);
            String op=read.request().operation().value();
            PublicMethod method;ArmyOrdinaryPreflight.Role role;
            if(op.equals("query-declarable-wars")){method=PublicMethod.QUERY_DECLARABLE_WARS;role=ArmyOrdinaryPreflight.Role.DECLARATIONS;}
            else if(op.startsWith("query-prewar-force-coalition-coverage-v2-")){method=PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2;role=ArmyOrdinaryPreflight.Role.DECLARATION_FINAL_ROLES;}
            else if(op.startsWith("query-war-termination-options-")){method=PublicMethod.QUERY_WAR_TERMINATION_OPTIONS;role=ArmyOrdinaryPreflight.Role.WAR_OPTIONS;}
            else if(op.startsWith("query-war-termination-terms-v1-")){method=PublicMethod.QUERY_WAR_TERMINATION_TERMS;role=ArmyOrdinaryPreflight.Role.WAR_TERMS;}
            else if(op.startsWith("query-war-occupation-targets-v1-")){method=PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1;role=ArmyOrdinaryPreflight.Role.HOLDING_SIEGE;}
            else throw new IllegalArgumentException("unrelated original read in war result");
            // Declaration final-role replay requires its same actual chosen declaration and is handled by its owner below.
            if(role==ArmyOrdinaryPreflight.Role.DECLARATION_FINAL_ROLES) {
                result.add(new ArmyOrdinaryPreflight.Read(role,read,reference,read.original().originalResultToken().orElseThrow()));
            } else {
                var decoded=decode(before,read,method);
                result.add(new ArmyOrdinaryPreflight.Read(role,read,reference,ArmyWarReadCodec.encode(decoded)));
            }
        }
        int size=result.size();
        switch(args.kind()) {
            case MOVE_ARMY,ENFORCE_DEMANDS -> StrictJson.require(size==0,"this original war action has no preflight read");
            case OFFER_WHITE_PEACE -> StrictJson.require(size>=1 && size<=2 && result.getFirst().role()==ArmyOrdinaryPreflight.Role.WAR_OPTIONS
                    && (size==1 || result.getLast().role()==ArmyOrdinaryPreflight.Role.WAR_TERMS),"white-peace original quote order changed");
            case SURRENDER_WAR -> StrictJson.require(size==1 && result.getFirst().role()==ArmyOrdinaryPreflight.Role.WAR_OPTIONS,"surrender requires its one original options quote");
            case DECLARE_WAR -> StrictJson.require(size==2 && result.getFirst().role()==ArmyOrdinaryPreflight.Role.DECLARATIONS
                    && result.getLast().role()==ArmyOrdinaryPreflight.Role.DECLARATION_FINAL_ROLES,"declaration quote/final-role inventory changed");
            case START_ASSAULT,STOP_ASSAULT -> StrictJson.require(size<=15 && result.stream().allMatch(read->read.role()==ArmyOrdinaryPreflight.Role.HOLDING_SIEGE),"assault preflight inventory changed");
            default -> throw new IllegalArgumentException("unrelated war preflight");
        }
        return List.copyOf(result);
    }
    private static ArmyWarReadCodec.Observation decode(Complete frame,PlanningReadReceipt original,PublicMethod method) {
        var context=new ArmyTypes.Context(frame.identity(),frame.source(),frame.sessionId(),original.request().deadline());
        ArmyCalls.Call call=ArmyCallCodec.decode(method,new RawJson(DriverJson.encode(original.request().arguments())));
        return ArmyWarReadCodec.decode(new ArmyWarReadCodec.Scope(call,context,frame.semantic(),Optional.empty()),original);
    }

    static Obj move(ArmyCalls.Move call,Obj raw,Obj before,Obj after) {
        requirePrimitive(raw,step(call),null,false);
        Obj starting=army(before,call.army().value());
        StrictJson.require(starting!=null && flag(starting,"controllable"),"original move army is not controllable");
        boolean routes=flag(before,"army_routes_supported");
        String status;
        if(Boolean.FALSE.equals(optionalBoolean(starting,"move_target_observable")) && !routes
                && (flag(raw,"accepted") || Set.of("accepted","submitted").contains(text(raw,"status")))) {
            var action=new LinkedHashMap<String,Value>();
            action.put("status",new Text("move_submitted"));action.put("army_id",number(call.army().value()));
            action.put("target_province_id",number(call.target().value()));action.put("submitted_date_raw",get(before,"date_raw"));
            action.put("move_target_observable",new Bool(false));
            return movementResult(raw,new Obj(action),after);
        }
        status=movePostcondition(before,after,call.army().value(),call.target().value(),routes);
        StrictJson.require(status!=null,"actual move postcondition is absent");
        return movementResult(raw,obj("status",new Text(status),"army_id",number(call.army().value()),
                "target_province_id",number(call.target().value()),"submitted_date_raw",get(before,"date_raw")),after);
    }
    private static Obj movementResult(Obj raw,Obj action,Obj after) {
        var out=fields(raw);out.put("war_action",action);out.put("player_armies",getOr(after,"player_armies",new Arr(List.of())));
        out.put("snapshot_id",get(after,"snapshot_id"));out.put("revision",get(after,"revision"));return new Obj(out);
    }
    /** Retains negative ACK identity. Actual later-frame custody is established by present before this pure replay. */
    static Obj negativeMove(ArmyCalls.Call selected,Obj before,Obj after,Obj request,Obj response,String requestId) throws IOException {
        if(!(selected instanceof ArmyCalls.Move call))throw new IOException("original non-movement native rejection has no successful Driver result");
        String operation=step(call),error=text(response,"error");
        StrictJson.text(requestId);
        StrictJson.require(text(request,"type").equals("execute_step") && integer(request,"protocol_version").equals(BigInteger.ONE)
                && text(request,"request_id").equals(requestId) && text(request,"step").equals(operation)
                && integer(request,"expected_revision").equals(integer(before,"native_revision"))
                && text(response,"type").equals("command_result") && integer(response,"protocol_version").equals(BigInteger.ONE)
                && text(response,"request_id").equals(requestId) && !bool(response,"ok"),"negative move original request/response differs");
        if(Set.of("CK3 army cannot move to the destination","CK3 army has no move mode for the destination",
                "CK3 army state rejects movement").contains(error)) {
            return obj("step",new Text(operation),"accepted",new Bool(false),"status",new Text("deferred"),
                    "backend_id",new Text("native-headless"),"war_action",obj("status",new Text("move_deferred"),
                    "reason",new Text("army_not_move_ready"),"army_id",number(call.army().value()),
                    "target_province_id",number(call.target().value()),"submitted_date_raw",get(before,"date_raw")),
                    "player_armies",getOr(after,"player_armies",new Arr(List.of())),"snapshot_id",get(after,"snapshot_id"),"revision",get(after,"revision"));
        }
        if(!error.equals("CK3 move-army state is unavailable"))throw new IOException("original move native rejection: "+error);
        Obj first=army(before,call.army().value()),last=army(after,call.army().value());
        StrictJson.require(first!=null && last!=null,"original rejected move has no same actual army");
        sameTerminationFrame(before,after);
        Obj firstPlayer=object(get(before,"played_character"),"before move player"),lastPlayer=object(get(after,"played_character"),"after move player");
        Obj firstDiagnostics=object(get(before,"diagnostics"),"before move diagnostics");
        Value route=last.get("route_province_ids"),oldRoute=first.get("route_province_ids");
        StrictJson.require(flag(before,"paused") && flag(before,"map_ready") && flag(after,"map_ready")
                && flag(firstPlayer,"alive") && flag(lastPlayer,"alive") && integer(firstDiagnostics,"bridge_pid").signum()>0
                && integer(after,"native_revision").compareTo(integer(before,"native_revision"))>0
                && integer(after,"revision").compareTo(integer(before,"revision"))>=0
                && text(after,"snapshot_id").equals("native:"+integer(after,"native_revision"))
                && get(first,"owner_character_id").equals(get(firstPlayer,"character_id"))
                && get(last,"owner_character_id").equals(get(firstPlayer,"character_id"))
                && !intEquals(first.get("move_target_province_id"),call.target().value())
                && flag(last,"controllable") && flag(last,"move_target_observable")
                && intEquals(last.get("move_target_province_id"),call.target().value()) && text(last,"route_read_status").equals("complete_nonempty")
                && get(first,"current_province_id").equals(get(last,"current_province_id")) && !bool(last,"in_combat") && !bool(last,"retreating")
                && route instanceof Arr rows && !rows.items().isEmpty() && intEquals(rows.items().getLast(),call.target().value())
                && !route.equals(oldRoute) && "moving".equals(movePostcondition(before,after,call.army().value(),call.target().value(),true)),
                "negative move ACK lacks the actual newer same-owner independent route postcondition");
        return obj("step",new Text(operation),"accepted",new Bool(false),"status",new Text("observed_after_native_error"),
                "backend_id",new Text("native-headless"),"native_ack_verified",new Bool(false),"native_ack_status",new Text("unknown_after_error"),
                "native_error",new Text(error),"native_error_evidence",obj("native_request_id",new Text(requestId),
                "native_request",request,"native_command_result",response),"business_submission_may_have_applied",new Bool(true),
                "war_action",obj("status",new Text("route_intent_observed"),"army_id",number(call.army().value()),
                "target_province_id",number(call.target().value()),"submitted_date_raw",get(before,"date_raw"),
                "postcondition_verified",new Bool(true),"original_native_ack_verified",new Bool(false)),
                "source_frame",moveFrame(before),"observed_frame",moveFrame(after),
                "starting_army_route",oldRoute instanceof Arr?oldRoute:Nil.INSTANCE,"starting_army_target",getOr(first,"move_target_province_id",Nil.INSTANCE),
                "observed_army_route",route,"player_armies",getOr(after,"player_armies",new Arr(List.of())),
                "snapshot_id",get(after,"snapshot_id"),"revision",get(after,"revision"));
    }
    private static Obj moveFrame(Obj snapshot) {
        Obj player=object(get(snapshot,"played_character"),"move actual player"),diagnostics=object(get(snapshot,"diagnostics"),"move actual diagnostics");
        return obj("snapshot_id",get(snapshot,"snapshot_id"),"revision",get(snapshot,"revision"),"native_revision",get(snapshot,"native_revision"),
                "date_raw",get(snapshot,"date_raw"),"actor_character_id",get(player,"character_id"),"episode_run_id",get(snapshot,"episode_run_id"),
                "connection_generation",get(diagnostics,"connection_generation"),"bridge_pid",get(diagnostics,"bridge_pid"));
    }
    static String movePostcondition(Obj before,Obj after,int id,int target,boolean requireRoute) {
        Obj original=army(before,id),current=army(after,id);
        if(original!=null && intEquals(original.get("current_province_id"),target)) {
            if(current==null || !flag(current,"controllable") || !intEquals(current.get("army_id"),id)
                    || !intEquals(current.get("current_province_id"),target) || getOr(current,"move_target_province_id",Nil.INSTANCE)!=Nil.INSTANCE
                    || !new Arr(List.of()).equals(current.get("route_province_ids")) || !stationary(current) || combat(current)
                    || integer(after,"revision").compareTo(integer(before,"revision"))<=0
                    || integer(after,"native_revision").compareTo(integer(before,"native_revision"))<=0)return null;
            return "arrived";
        }
        if(current==null)return "army_no_longer_present";
        if(intEquals(current.get("current_province_id"),target))return "arrived";
        if(intEquals(current.get("move_target_province_id"),target)) {
            if(requireRoute) {
                Value route=current.get("route_province_ids");
                if(!(route instanceof Arr rows) || rows.items().isEmpty() || !intEquals(rows.items().getLast(),target))return null;
            }
            return "moving";
        }
        return null;
    }
    private static boolean stationary(Obj army) {
        Value state=army.get("army_state");
        return state instanceof Text text?Set.of("regular","sieging").contains(text.value().toLowerCase(Locale.ROOT))
                :intEquals(army.get("army_state_code"),1)||intEquals(army.get("army_state_code"),3);
    }
    private static boolean combat(Obj army) {
        Value state=army.get("army_state");
        return flag(army,"in_combat") || flag(army,"retreating")
                || state instanceof Text text && Set.of("combat","retreating").contains(text.value().toLowerCase(Locale.ROOT))
                || intEquals(army.get("army_state_code"),2)||intEquals(army.get("army_state_code"),6);
    }

    private record SiegeMaterial(ArmyAssaultSelection.Observation selection,Obj fullSiege) { }
    private static Obj assault(ArmyCalls.Siege call,Obj raw,Complete before,Complete after,
            List<ArmyOrdinaryPreflight.Read> preflights,NativeEffectEvidence.Original material,ActionPorts.OutcomeArchive bound) {
        var beforeHoldings=new ArrayList<ArmyWarOccupationCodec.Occupation>();
        for(var read:preflights)beforeHoldings.add(((ArmyWarReadCodec.Occupation)decode(before,read.original(),
                PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1)).value());
        var afterHoldings=new ArrayList<ArmyWarOccupationCodec.Occupation>();
        for(var read:material.independentReads()) {
            if(!read.request().operation().value().startsWith("query-war-occupation-targets-v1-")
                    || !read.request().before().equals(after.identity()))continue;
            ArmyOrdinaryPreflight.bind(read,after);NativeRecordedEvidenceVerifier.requireRead(read,bound);
            afterHoldings.add(((ArmyWarReadCodec.Occupation)decode(after,read,PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1)).value());
        }
        return assault(call,raw,before.semantic(),after.semantic(),beforeHoldings,afterHoldings);
    }
    static Obj assault(ArmyCalls.Siege call,Obj raw,Obj before,Obj after,
            List<ArmyWarOccupationCodec.Occupation> beforeHoldings,List<ArmyWarOccupationCodec.Occupation> afterHoldings) {
        boolean start=call.method()==PublicMethod.START_ASSAULT;
        String submitted=start?"start_submitted":"stop_submitted";
        requirePrimitive(raw,step(call),submitted,false);
        StrictJson.require(flag(before,"war_objective_assault_supported"),"exact original assault capability is absent");
        SiegeMaterial first=siege(before,beforeHoldings,call.siege().value());
        var original=first.selection().siege();
        StrictJson.require(original.inProgress()!=start && (start?original.canStart():original.canStop()),"original assault eligibility is false");
        SiegeMaterial last=siege(after,afterHoldings,call.siege().value());
        StrictJson.require(flag(after,"paused") && first.selection().warId()==last.selection().warId()
                && first.selection().provinceId()==last.selection().provinceId() && last.selection().siege().inProgress()==start,
                "same-SiegeID actual assault postcondition is absent");
        if(first.selection().source()==ArmyAssaultSelection.Source.OCCUPATION)
            StrictJson.require(!afterHoldings.isEmpty(),"holding assault requires its actual independent post-query");
        Obj action=obj("status",new Text(start?"assault_started":"assault_stopped"),"submission_status",new Text(submitted),
                "siege_id",number(call.siege().value()),"war_id",number(first.selection().warId()),
                "province_id",number(first.selection().provinceId()),"assault_in_progress",new Bool(start),
                "observation_source",new Text(first.selection().source()==ArmyAssaultSelection.Source.OCCUPATION
                        ?"war_occupation_query":"war_objective_snapshot"));
        var out=fields(raw);out.put("war_action",action);out.put("assault_action",action);out.put("active_siege",last.fullSiege());
        out.put("snapshot_id",get(after,"snapshot_id"));out.put("revision",get(after,"revision"));return new Obj(out);
    }
    private static SiegeMaterial siege(Obj snapshot,List<ArmyWarOccupationCodec.Occupation> occupations,int id) {
        var holdings=new ArrayList<ArmyAssaultSelection.Holding>();
        for(var occupation:occupations) {
            StrictJson.require(occupation.available() && occupation.collectionComplete(),"incomplete occupation cannot supply assault result");
            for(var holding:occupation.holdings()) {
                var selected=holding.siege().map(value->{
                    var assault=value.assault().orElse(null);
                    return new ArmyAssaultSelection.Siege(value.id(),assault!=null,assault!=null && assault.inProgress(),
                            assault!=null && assault.canStart(),assault!=null && assault.canStop(),value.playerBesieging());
                });
                holdings.add(new ArmyAssaultSelection.Holding(occupation.requestedWar(),holding.province(),holding.siegeObservable(),selected));
            }
        }
        var selected=ArmyAssaultSelection.select(snapshot,holdings,id).orElseThrow(()->new IllegalArgumentException("same full siege is absent or ambiguous"));
        var candidates=new ArrayList<Obj>();
        if(selected.source()==ArmyAssaultSelection.Source.OBJECTIVE) {
            Obj war=Objects.requireNonNull(war(snapshot,BigInteger.valueOf(selected.warId())));
            for(Value value:arrayOrEmpty(war,"objective_province_states")) {
                Obj row=object(value,"objective province");
                if(intEquals(row.get("province_id"),selected.provinceId()) && flag(row,"siege_observable")) {
                    Obj active=nullableObject(row.get("active_siege"));
                    if(active!=null && intEquals(active.get("siege_id"),id))candidates.add(active);
                }
            }
        } else {
            for(var occupation:occupations)if(occupation.requestedWar()==selected.warId())
                for(var row:occupation.holdings())if(row.province()==selected.provinceId())
                    row.siege().filter(value->value.id()==id).ifPresent(value->candidates.add(value.normalized()));
        }
        StrictJson.require(candidates.size()==1,"full original selected siege material is absent or ambiguous");
        return new SiegeMaterial(selected,candidates.getFirst());
    }

    static Obj enforce(ArmyCalls.War call,Obj raw,Obj before,Obj after) {
        requirePrimitive(raw,step(call),null,false);
        StrictJson.require(war(before,call.warId())!=null && war(after,call.warId())==null,"actual victory did not remove the same WarID");
        Obj action=obj("status",new Text("victory_enforced"),"war_id",new IntegerValue(call.warId()));
        var out=fields(raw);out.put("ordinary_war_exit_observation_v1",warExit(before,after,raw));
        out.put("war_action",action);out.put("war_victory",action);out.put("active_wars",getOr(after,"active_wars",new Arr(List.of())));
        out.put("player_armies",getOr(after,"player_armies",new Arr(List.of())));out.put("snapshot_id",get(after,"snapshot_id"));
        out.put("revision",get(after,"revision"));return new Obj(out);
    }
    static Obj white(ArmyCalls.War call,Obj raw,Obj before,Obj after,OrdinaryWhitePeacePolicy.Ready ready) {
        requirePrimitive(raw,step(call),"submitted",true);sameTerminationFrame(before,after);
        StrictJson.require(intEquals(ready.war().get("war_id"),call.warId()),"white-peace policy changed selected war");
        Obj option=ready.whitePeace(),response=object(get(option,"recipient_response"),"actual white-peace recipient response");
        var action=terminationBase(call,before,after,"white_peace",response);
        action.put("casus_belli",getOr(ready.options(),"active_casus_belli_identity",Nil.INSTANCE));
        action.put("claimant_character_id",ready.terms().map(value->getOr(value,"claimant_character_id",Nil.INSTANCE)).orElse(Nil.INSTANCE));
        action.put("target_title_ids",ready.terms().map(value->getOr(value,"target_title_ids",Nil.INSTANCE))
                .orElseGet(()->getOr(ready.war(),"targeted_title_ids",Nil.INSTANCE)));
        if(ready.variant()!=OrdinaryWhitePeacePolicy.Variant.CLAIM_CB) {
            copy(action,ready.options(),"player_side","player_relative_war_score","war_duration_days");
            Obj acceptance=nullableObject(option.get("ai_acceptance"));
            action.put("recipient_ai_acceptance_raw",acceptance==null?Nil.INSTANCE:getOr(acceptance,"raw",Nil.INSTANCE));
        }
        return terminated(raw,before,after,new Obj(action));
    }
    static Obj surrender(ArmyCalls.War call,Obj raw,Obj before,Obj after,OrdinaryAutomaticSurrenderPolicy.Ready ready) {
        requirePrimitive(raw,step(call),"submitted",true);sameTerminationFrame(before,after);
        StrictJson.require(intEquals(ready.war().get("war_id"),call.warId()),"surrender policy changed selected war");
        Obj response=object(get(ready.surrender(),"recipient_response"),"actual surrender recipient response");
        var action=terminationBase(call,before,after,"attacker_defeat",response);
        action.put("recipient_auto_accept",getOr(ready.surrender(),"auto_accept",Nil.INSTANCE));
        if(ready.variant()!=OrdinaryAutomaticSurrenderPolicy.Variant.DE_JURE_NO_SAFE_ROUTE) {
            action.put("surrender_variant",new Text(ready.variant().wire()));
            copy(action,ready.options(),"absolute_war_scores_observable","attacker_war_score","defender_war_score");
        }
        action.put("casus_belli",getOr(ready.options(),"active_casus_belli_identity",Nil.INSTANCE));
        copy(action,ready.options(),"player_side","player_relative_war_score","war_duration_days");
        return terminated(raw,before,after,new Obj(action));
    }
    private static LinkedHashMap<String,Value> terminationBase(ArmyCalls.War call,Obj before,Obj after,String outcome,Obj response) {
        Obj remaining=war(after,call.warId());var fields=new LinkedHashMap<String,Value>();
        fields.put("status",new Text(remaining==null?"applied":"submitted_pending"));fields.put("war_id",new IntegerValue(call.warId()));
        fields.put("outcome",new Text(outcome));fields.put("submitted_date_raw",getOr(before,"date_raw",Nil.INSTANCE));
        fields.put("observed_date_raw",getOr(after,"date_raw",Nil.INSTANCE));fields.put("episode_run_id",getOr(before,"episode_run_id",Nil.INSTANCE));
        fields.put("starting_snapshot_id",getOr(before,"snapshot_id",Nil.INSTANCE));fields.put("observed_snapshot_id",getOr(after,"snapshot_id",Nil.INSTANCE));
        fields.put("command_acknowledged",new Bool(true));fields.put("war_id_absent_after_ack",new Bool(remaining==null));
        fields.put("recipient_decision_status_raw",getOr(response,"decision_status_raw",Nil.INSTANCE));
        fields.put("recipient_would_accept_now",getOr(response,"would_accept_now",Nil.INSTANCE));
        fields.put("remaining_active_war",remaining==null?Nil.INSTANCE:remaining);return fields;
    }
    private static Obj terminated(Obj raw,Obj before,Obj after,Obj action) {
        var out=fields(raw);out.put("ordinary_war_exit_observation_v1",warExit(before,after,raw));out.put("war_termination_result",action);return new Obj(out);
    }
    static Value warExit(Obj before,Obj after,Obj action) {
        // These three optional inputs are deliberately null in the original generic Driver call.
        // The shared typed entry consumes the already decoded complete originals: no 1 MiB generic byte parser.
        var receipt=OrdinaryWarExitObservationCodec.compose(OpportunityJson.toNode(before),OpportunityJson.toNode(after),
                OpportunityJson.toNode(action),com.fasterxml.jackson.databind.node.NullNode.instance,
                com.fasterxml.jackson.databind.node.NullNode.instance,com.fasterxml.jackson.databind.node.NullNode.instance);
        if(receipt==null)return Nil.INSTANCE;
        return DriverJson.object(OrdinaryWarExitObservationCodec.encode(receipt),DriverJson.MAX_NATIVE_BYTES);
    }
    private static void sameTerminationFrame(Obj before,Obj after) {
        StrictJson.require(flag(after,"paused") && getOr(before,"episode_run_id",Nil.INSTANCE).equals(getOr(after,"episode_run_id",Nil.INSTANCE))
                && integer(before,"date_raw").equals(integer(after,"date_raw")),"termination changed paused date/episode");
        Obj first=object(get(before,"diagnostics"),"before diagnostics"),last=object(get(after,"diagnostics"),"after diagnostics");
        for(String field:List.of("bridge_pid","connection_generation"))
            StrictJson.require(get(first,field).equals(get(last,field)),"termination changed process/connection");
        StrictJson.require(get(object(get(before,"played_character"),"before player"),"character_id").equals(
                get(object(get(after,"played_character"),"after player"),"character_id")),"termination changed played character");
    }

    static Obj declaration(ArmyCalls.Declaration call,Obj raw,Obj after,WarDeclarationContinuity.Record continuity) {
        requirePrimitive(raw,step(call),null,false);
        StrictJson.require(flag(raw,"accepted") && continuity.origin().declaration().declarationId().equals(call.declarationId())
                && continuity.nativeResponse()==WarDeclarationContinuity.NativeResponse.ACCEPTED,
                "original declaration continuity belongs to another request or rejected response");
        Obj record=WarDeclarationContinuity.json(continuity);
        Obj selected=object(get(record,"declaration"),"full original selected declaration");
        var action=fields(record);
        action.put("status",new Text(continuity.status()==WarDeclarationContinuity.Status.WAR_STARTED?"war_started":"declaration_submitted"));
        action.put("native_request_id",new Text(continuity.origin().requestId()));action.put("declaration_id",new Text(call.declarationId()));
        action.put("target_character_id",get(selected,"target_character_id"));action.put("casus_belli_key",get(selected,"casus_belli_key"));
        var out=fields(raw);out.put("declaration",selected);out.put("war_action",new Obj(action));
        Value wars=after.get("active_wars");out.put("active_wars",wars instanceof Arr?wars:new Arr(List.of()));
        out.put("snapshot_id",get(after,"snapshot_id"));out.put("revision",get(after,"revision"));return new Obj(out);
    }

    private static void requirePrimitive(Obj raw,String step,String status,boolean closed) {
        StrictJson.require(text(raw,"step").equals(step) && raw.get("accepted") instanceof Bool && text(raw,"backend_id").equals("native-headless"),
                "original native primitive result fields differ for this exact step");
        if(status!=null)StrictJson.require(text(raw,"status").equals(status),"original primitive submission status differs");
        if(closed)StrictJson.require(flag(raw,"accepted") && raw.members().keySet().equals(TERMINATION_ACK),"original termination ACK fields differ");
    }
    static Obj json(RawJson value){return DriverJson.object(value.bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private static LinkedHashMap<String,Value> fields(Obj value){return new LinkedHashMap<>(value.members());}
    private static Obj obj(Object... fields) {
        StrictJson.require(fields.length%2==0,"complete typed JSON members required");var result=new LinkedHashMap<String,Value>();
        for(int i=0;i<fields.length;i+=2) {
            StrictJson.require(fields[i] instanceof String && fields[i+1] instanceof Value,"typed JSON key/value required");
            StrictJson.require(result.put((String)fields[i],(Value)fields[i+1])==null,"duplicate result field");
        }
        return new Obj(result);
    }
    private static void copy(Map<String,Value> to,Obj from,String... names){for(String name:names)to.put(name,getOr(from,name,Nil.INSTANCE));}
    private static Value get(Obj row,String name){Value value=row.get(name);StrictJson.require(value!=null,"missing original field "+name);return value;}
    private static Value getOr(Obj row,String name,Value absent){Value value=row.get(name);return value==null?absent:value;}
    private static String text(Obj row,String name){return OpportunityJson.text(get(row,name),name);}
    private static BigInteger integer(Obj row,String name){return OpportunityJson.integer(get(row,name),name);}
    private static boolean bool(Obj row,String name){return OpportunityJson.bool(get(row,name),name);}
    private static boolean flag(Obj row,String name){Value value=row.get(name);return value instanceof Bool flag && flag.value();}
    private static Boolean optionalBoolean(Obj row,String name){Value value=row.get(name);return value==null||value==Nil.INSTANCE?null:OpportunityJson.bool(value,name);}
    private static Obj object(Value value,String name){return OpportunityJson.object(value,name);}
    private static Obj nullableObject(Value value){return value==null||value==Nil.INSTANCE?null:object(value,"nullable original object");}
    private static List<Value> arrayOrEmpty(Obj row,String name){Value value=row.get(name);return value==null||value==Nil.INSTANCE?List.of():OpportunityJson.array(value,name);}
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static boolean intEquals(Value value,long expected){return intEquals(value,BigInteger.valueOf(expected));}
    private static boolean intEquals(Value value,BigInteger expected){return value instanceof IntegerValue integer && integer.value().equals(expected);}
    private static Obj army(Obj frame,int id){for(Value value:arrayOrEmpty(frame,"player_armies"))if(value instanceof Obj row && intEquals(row.get("army_id"),id))return row;return null;}
    private static Obj war(Obj frame,BigInteger id){for(Value value:arrayOrEmpty(frame,"active_wars"))if(value instanceof Obj row && intEquals(row.get("war_id"),id))return row;return null;}
}

