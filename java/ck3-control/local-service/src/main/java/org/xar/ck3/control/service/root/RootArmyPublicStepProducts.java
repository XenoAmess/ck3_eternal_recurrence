package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.NativeArmyWarWindowEffects;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.application.planning.military.CommanderObservationCollector;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.root.RootPublicStepExecution.Product;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Original explicit Army, Commander and fixed-window steps. The installed owner prepares; only Root submits once. */
public final class RootArmyPublicStepProducts {
    private static final Pattern COMMANDER=Pattern.compile("assign-army-commander-v1-army-(0|[1-9][0-9]*)-to-character-(0|[1-9][0-9]*)");
    private static final Obj EMPTY=new Obj(Map.of());
    enum Kind { RAISE,DISBAND,COMMANDER }
    private RootArmyPublicStepProducts(){ }

    public static List<Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        var remaining=actual.remainingDomains();RootRuntimeCommands commands=remaining.commands();
        RootPublicStepExecution.OwnerGuard owner=identical->{
            if(identical!=context||actual.context()!=context||actual.remainingDomains()!=remaining
                    ||remaining.commands()!=commands)throw new IOException("Army public step crossed its actual installed Root owners");
            remaining.requireContext(identical);
        };
        List<ExactRef> sources=List.of(actual.publicStepSource(Module.LOCAL_SERVICE,RootArmyPublicStepProducts.class),
                actual.publicStepSource(Module.LOCAL_SERVICE,RootRuntimeCommands.class),
                actual.publicStepSource(Module.NATIVE_TRANSPORT,ArmyOrdinaryPlannerCalls.class),
                actual.publicStepSource(Module.APPLICATION,ArmyPublicWire.class),
                actual.publicStepSource(Module.APPLICATION,CommanderAssignmentPostcondition.class),
                actual.publicStepSource(Module.APPLICATION,CommanderBindings.class),
                actual.publicStepSource(Module.APPLICATION,NativeEffectEvidence.class),
                actual.publicStepSource(Module.LOCAL_SERVICE,RootPublicStepFailureOriginals.class));
        var products=new ArrayList<Product>();
        for(Kind kind:Kind.values())products.add(new RootPublicStepExecution.Action("original-army-"+kind.name().toLowerCase(java.util.Locale.ROOT),
                step->classify(step).filter(kind::equals).isPresent(),owner,
                (original,frame,known,same,caller)->{
                  try{
                    if(kind==Kind.COMMANDER){requireCommanderRevision(caller);
                        if(!new Bool(true).equals(original.observations().snapshot().get("paused")))
                            throw bridge("native commander assignment requires a paused snapshot");}
                    requireArmyRevision(kind,caller,original.before().frame().revision());context.writer().requireSession(same);
                    StrictJson.require(frame.identity().equals(original.before())&&frame.source().equals(original.source())
                            &&frame.sessionId().equals(original.sessionId()),"Army public preparation changed its actual held frame");
                    if(kind==Kind.COMMANDER){
                        ArmyCalls.AssignCommander input=commanderCall(caller.step(),original.before().frame().revision());
                        currentCommanderScope(original.observations().snapshot(),input.army().value());
                        var parent=actual.military().commander().read(original,input.army().value(),context.readCatalog(),same);
                        if(!(parent instanceof PlanningReadResult.Known<CommanderObservationCollector.Observation> observed))
                            throw bridge("actual native Commander parent identity is unavailable");
                        Obj arguments=commanderArguments(original,caller,observed.value());
                        return actual.military().commander().assignment(original,CommanderAssignmentPostcondition.arguments(arguments),
                                context.bindings(),RootPublicStepExecution.actionId(original,caller));
                    }
                    MilitaryPlanningDecision.Select selection=selection(original,caller);
                    var prepared=commands.prepare(original,selection);
                    return prepared.requireOriginalChoice(original,selection.operation(),selection.arguments(),selection.detail());
                  }catch(PublicServiceFailure failure){throw RootPublicStepFailureOriginals.recordDriverFailure(original,frame,known,same,caller,
                          failure,Optional.empty(),Optional.empty());}
                },(receipt,archive,same,caller)->{
                    RawJson numeric;
                  try{
                    context.writer().requireSession(same);
                    StrictJson.require(ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive)
                            .filter(receipt::equals).isPresent(),"Army public result lacks its actual canonical writer receipt");
                    StrictJson.require(receipt.command().operation().equals(caller.step()),"Army public result crossed the original caller step");
                    NativeActionPort.AckReceived ack=successfulAck(receipt,archive);
                    Optional<NativeEffectEvidence.Original> effect=kind==Kind.COMMANDER?Optional.empty()
                            :NativeEffectEvidence.loadIfPresent(receipt,archive,context.frameLoader());
                    if(kind!=Kind.COMMANDER&&effect.isEmpty())throw bridge(kind==Kind.RAISE
                            ?"native raise-troops-default did not expose a new controllable army"
                            :"native "+caller.step().value()+" did not remove the army");
                    numeric=formatNumeric(kind,caller.step(),ack.originalResultToken().orElseThrow(),
                            effect.map(NativeEffectEvidence.Original::compatibleResult),
                            effect.map(value->value.frames().after().semantic()));
                  }catch(PublicServiceFailure failure){
                    Optional<RawJson> report=Optional.empty(),exposed=Optional.empty();
                    if(kind==Kind.COMMANDER&&failure.kind()==PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED){
                        try{
                            var original=commanderRejectedOriginal(receipt,archive);
                            if(original.isPresent()){
                                RawJson publicResult=encodeOriginal(original.orElseThrow(),new ArmyTypes.Context(receipt.command().before(),
                                        receipt.command().source(),receipt.command().sessionId(),receipt.command().deadline()));
                                report=original;exposed=Optional.of(publicResult);
                            }
                        }catch(IllegalArgumentException|java.io.UncheckedIOException unavailable){
                            failure.addSuppressed(new IOException("actual Commander failure report/public projection is unavailable",unavailable));
                        }
                    }
                    throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,failure,report,exposed);
                  }
                    return encodeOriginal(numeric,new ArmyTypes.Context(receipt.command().before(),receipt.command().source(),
                            receipt.command().sessionId(),receipt.command().deadline()));
                },sources,RootPublicStepExecution.ActionValidation.OWNER_ORDERED));
        RootArmyStructuralStepRuntime structural=actual.armyStructural();
        var structuralSources=new java.util.LinkedHashSet<>(structural.sources());structuralSources.add(sources.getFirst());
        products.add(new RootPublicStepExecution.Action("original-army-structural",RootArmyStructuralStepRuntime::accepts,
                identical->{
                    if(identical!=context||actual.armyStructural()!=structural)throw new IOException("Army structure crossed its actual once-installed Root runtime");
                    structural.requireContext(identical);
                },structural::prepare,structural::present,List.copyOf(structuralSources)));
        var windowOwner=remaining.armyOrdinary();ArmyOrdinaryActionService windowService=windowOwner.service();
        var windowSources=new java.util.LinkedHashSet<>(sources);
        windowSources.add(actual.publicStepSource(Module.LOCAL_SERVICE,ArmyOrdinaryRuntimeBindings.class));
        windowSources.add(actual.publicStepSource(Module.NATIVE_TRANSPORT,ArmyOrdinaryActionService.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,ArmyOrdinaryActionArguments.class));
        windowSources.add(actual.publicStepSource(Module.NATIVE_TRANSPORT,ArmyOrdinaryActionPreparation.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,ArmyWindowCodec.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,ArmyWindowQueryFailure.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,NativeArmyWarWindowEffects.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,NativeDirectFixedWindowObservation.class));
        windowSources.add(actual.publicStepSource(Module.APPLICATION,NativeEffectSnapshots.class));
        for(var kind:ArmyWindowCodec.Kind.values())products.add(new RootPublicStepExecution.Action(
                "original-army-window-"+kind.name().toLowerCase(java.util.Locale.ROOT),
                step->windowKind(step).filter(kind::equals).isPresent(),identical->{
                    owner.requireContext(identical);
                    if(remaining.armyOrdinary()!=windowOwner||windowOwner.service()!=windowService)
                        throw new IOException("fixed-window public step crossed its actual installed producer");
                },(original,frame,known,same,caller)->{
                  try{
                    ArmyCalls.Frame input=windowSelection(caller);
                    try{ArmyOrdinaryActionPreparation.requireDirectFixedWindowBefore(input.method(),frame);}
                    catch(IllegalArgumentException invalid){throw bridge(invalid.getMessage());}
                    requireWindowRevisionCurrent(input,original.before().frame().revision());
                    context.writer().requireSession(same);
                    StrictJson.require(frame.identity().equals(original.before())&&frame.source().equals(original.source())
                            &&frame.sessionId().equals(original.sessionId()),"direct fixed-window preparation changed its actual held frame");
                    return windowService.prepareDirectFixedWindowCommand(same,input,new ArmyTypes.Context(original.before(),
                            original.source(),original.sessionId(),original.deadline()),RootPublicStepExecution.actionId(original,caller));
                  }catch(PublicServiceFailure failure){throw RootPublicStepFailureOriginals.recordDriverFailure(original,frame,known,same,caller,
                          failure,Optional.empty(),Optional.empty());}
                },(receipt,archive,same,caller)->{
                    RawJson numeric;
                  try{
                    context.writer().requireSession(same);
                    StrictJson.require(receipt.command().operation().equals(caller.step())
                            &&ContinuityActionJournal.lookup(same.head().state(),receipt.command().actionId(),archive).filter(receipt::equals).isPresent(),
                            "fixed-window result lacks its original same-writer canonical receipt");
                    var selection=ArmyOrdinaryActionArguments.decode(receipt.command().arguments());
                    StrictJson.require(selection.executionProfile()==ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW
                            &&selection.kind()==(kind==ArmyWindowCodec.Kind.OVERVIEW?ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1
                                    :ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1),"fixed-window result changed its canonical direct selection");
                    var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->bridge("fixed-window action has no original native attempt"));
                    var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->bridge("fixed-window action has no original dispatch evidence"));
                    var originalRef=Optional.of(archive.referenceOf(dispatch));
                    if(!(dispatch instanceof NativeActionPort.AckReceived ack))throw windowDispatchFailure(kind,dispatch,originalRef);
                    StrictJson.require(ack.requestId().equals(attempt.requestId()),"fixed-window return crossed its original canonical attempt");
                    if(!ack.nativeOk()){
                        StrictJson.require(ack.outbound().isPresent()&&ack.custody().isPresent(),"fixed-window refusal lacks actual transport custody");
                        ack.custody().orElseThrow().verify(ack,attempt.guard());
                        var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
                        StrictJson.require(before.identity().equals(receipt.command().before())&&before.source().equals(receipt.command().source())
                                &&before.sessionId().equals(receipt.command().sessionId()),"fixed-window refusal crossed its actual original frame");
                        throw windowNativeFailure(kind,ack.originalFrame(),attempt.requestId(),originalRef);
                    }
                    var observed=NativeDirectFixedWindowObservation.load(receipt,archive,context.frameLoader());
                    StrictJson.require(observed.observation().kind()==kind&&observed.observation().operation()==ArmyWindowCodec.Operation.CLOSE,
                            "fixed-window original after witness belongs to another close operation");
                    numeric=observed.normalized();
                  }catch(PublicServiceFailure failure){throw RootPublicStepFailureOriginals.recordActionDriverFailure(receipt,archive,same,caller,
                          failure,Optional.empty(),Optional.empty());}
                    var source=new ArmyTypes.Context(receipt.command().before(),receipt.command().source(),receipt.command().sessionId(),receipt.command().deadline());
                    return encodeOriginal(numeric,source);
                },List.copyOf(windowSources),RootPublicStepExecution.ActionValidation.OWNER_ORDERED));
        return List.copyOf(products);
    }

    /** Exact selector inventory: route/assault/war/hire/combat/query steps belong to other installed owners. */
    static Optional<Kind> classify(OperationKey operation){
        String step=Objects.requireNonNull(operation).value();
        if(step.equals("raise-troops-default")&&ArmyOrdinaryPlannerCalls.supports(operation))return Optional.of(Kind.RAISE);
        if(step.startsWith("disband-army-")&&ArmyOrdinaryPlannerCalls.supports(operation))return Optional.of(Kind.DISBAND);
        if(COMMANDER.matcher(step).matches()){
            try{commanderCall(operation,BigInteger.ONE);return Optional.of(Kind.COMMANDER);}
            catch(IllegalArgumentException invalid){return Optional.empty();}
        }
        return Optional.empty();
    }
    /** Public selection metadata records the explicit caller; it does not run an ordinary planner policy. */
    static MilitaryPlanningDecision.Select selection(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller){
        caller.requireCurrent(original);Kind kind=classify(caller.step()).orElseThrow(()->new IllegalArgumentException("unrelated Army public step"));
        StrictJson.require(kind!=Kind.COMMANDER,"Commander uses its same installed typed assignment producer");
        Obj arguments=EMPTY;
        var detail=new Obj(Map.of("policy",new Text("public_execute_step"),"phase",new Text("explicit_army"),
                "reason",new Text("caller_selected_original_step"),"selected_step",new Text(caller.step().value()),
                "original_public_call",DriverJson.object(PublicPlanningCodec.encodeExecute(caller).bytes(),65536)));
        return new MilitaryPlanningDecision.Select("public_execute_step","explicit_army","caller_selected_original_step",
                caller.step(),arguments,OrdinaryPolicy.Purpose.WORLD_ACTION,detail);
    }
    private static ArmyCalls.AssignCommander commanderCall(OperationKey operation,BigInteger revision){
        var match=COMMANDER.matcher(operation.value());StrictJson.require(match.matches(),"canonical Commander step required");
        var args=StrictJson.object().put("army_id",new BigInteger(match.group(1)))
                .put("commander_character_id",new BigInteger(match.group(2))).put("expected_revision",revision.toString());
        return (ArmyCalls.AssignCommander)ArmyCallCodec.decode(PublicMethod.ASSIGN_ARMY_COMMANDER_V1,
                new RawJson(StrictJson.canonical(args)));
    }
    /** Original Commander public route checks the current controllable CUnit, without candidate scoring. */
    static Obj commanderArguments(PlanningRequest original,PublicPlanningCodec.ExecuteRequest caller,CommanderObservationCollector.Observation originalParent){
        requireCommanderRevision(caller);
        ArmyCalls.AssignCommander input=commanderCall(caller.step(),original.before().frame().revision());
        currentCommanderScope(original.observations().snapshot(),input.army().value());
        var parent=Objects.requireNonNull(originalParent).observed().normalized();
        StrictJson.require(parent.army().value()==input.army().value()&&parent.nativeArmy().value()!=null&&parent.owner().value()!=null
                &&BigInteger.valueOf(parent.owner().value().value()).equals(original.before().frame().identity().player())
                &&parent.dateRaw().equals(original.before().frame().identity().dateRaw()),"actual Commander parent query crossed the original native subject/owner/date");
        BigInteger nativeArmy=BigInteger.valueOf(parent.nativeArmy().value().value()),owner=BigInteger.valueOf(parent.owner().value().value());
        var actual=new CommanderAssignmentPostcondition.Arguments(BigInteger.valueOf(input.army().value()),
                BigInteger.valueOf(input.character().value()),nativeArmy,owner,original.before().frame().identity().dateRaw());
        StrictJson.require(actual.step().equals(caller.step().value()),"Commander typed arguments changed the original exact step");
        return new Obj(Map.of("army_id",new IntegerValue(actual.army()),"commander_character_id",new IntegerValue(actual.character()),
                "native_carmy_id",new IntegerValue(actual.nativeArmy()),"owner_character_id",new IntegerValue(actual.owner()),"date_raw",new IntegerValue(actual.date())));
    }
    static void requireCommanderRevision(PublicPlanningCodec.ExecuteRequest caller){
        if(!(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)||value.value().signum()<0)
            throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,"expected_revision must be a non-negative integer",Optional.empty());
    }
    static void requireArmyRevision(Kind kind,PublicPlanningCodec.ExecuteRequest caller,BigInteger current){
        if(kind==Kind.COMMANDER)requireCommanderRevision(caller);
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value&&!value.value().equals(current))
            throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                    kind==Kind.COMMANDER?"native commander assignment source revision is stale"
                            :"native gameplay revision mismatch: expected "+value.value()+", current "+current,Optional.empty());
    }
    private static Optional<RawJson> commanderRejectedOriginal(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var attempt=ActionTransitions.attempt(receipt.state());var dispatch=ActionTransitions.dispatch(receipt.state());
        if(attempt.isEmpty()||!(dispatch.orElse(null) instanceof NativeActionPort.AckReceived ack)||ack.nativeOk()
                ||ack.outbound().isEmpty()||ack.custody().isEmpty())return Optional.empty();
        StrictJson.require(ack.equals(archive.load(archive.referenceOf(ack)))&&ack.requestId().equals(attempt.orElseThrow().requestId()),
                "Commander rejection differs from its actual archived dispatch");
        ack.custody().orElseThrow().verify(ack,attempt.orElseThrow().guard());
        byte[] packet=ack.outbound().orElseThrow().originalPacket();
        StrictJson.require(packet.length>4&&packet.length<=65540&&java.nio.ByteBuffer.wrap(packet,0,4)
                .order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4,"Commander original request framing differs");
        Obj request=DriverJson.object(java.util.Arrays.copyOfRange(packet,4,packet.length),65536);
        StrictJson.require(new IntegerValue(receipt.command().before().frame().identity().nativeRevision()).equals(request.get("expected_revision")),
                "Commander failure changed its actual original Native revision");
        return Optional.of(commanderRejectedResult(receipt.command().operation(),ack.requestId(),request,
                DriverJson.object(ack.originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES)));
    }
    static RawJson commanderRejectedResult(OperationKey operation,String requestId,Obj request,Obj response){
        StrictJson.require(classify(operation).filter(Kind.COMMANDER::equals).isPresent()
                &&request.members().keySet().equals(java.util.Set.of("type","protocol_version","request_id","step","expected_revision"))
                &&new Text("execute_step").equals(request.get("type"))&&new IntegerValue(BigInteger.ONE).equals(request.get("protocol_version"))
                &&new Text(requestId).equals(request.get("request_id"))&&new Text(operation.value()).equals(request.get("step"))
                &&request.get("expected_revision") instanceof IntegerValue value&&value.value().signum()>=0
                &&value.value().compareTo(StrictJson.UINT64_MAX)<=0&&new Text("command_result").equals(response.get("type"))
                &&new IntegerValue(BigInteger.ONE).equals(response.get("protocol_version"))&&new Text(requestId).equals(response.get("request_id"))
                &&new Bool(false).equals(response.get("ok")),"Commander original rejection frames changed their exact request binding");
        return new RawJson(DriverJson.encode(new Obj(Map.of("schema",new Text("army-commander-native-rejection-v1"),
                "native_request_id",new Text(requestId),"native_request_frame",request,"native_command_result_frame",response,
                "dispatch_status",new Text("unknown-unless-native-diagnostic-proves-predispatch"),"never_replay",new Bool(true)))));
    }
    /** Same original public CUnit scope; no inferred CArmy identity or candidate eligibility. */
    static Obj currentCommanderScope(Obj snapshot,int publicArmy){
        if(!new Bool(true).equals(snapshot.get("paused")))throw bridge("native commander assignment requires a paused snapshot");
        if(!(snapshot.get("player_armies") instanceof Arr armies))throw bridge("commander query requires current player_armies");
        List<Obj> matches=armies.items().stream().filter(Obj.class::isInstance).map(Obj.class::cast)
                .filter(row->new IntegerValue(BigInteger.valueOf(publicArmy)).equals(row.get("army_id"))&&new Bool(true).equals(row.get("controllable"))).toList();
        if(matches.size()!=1)throw bridge("army_id is outside the current controllable player scope");
        return matches.getFirst();
    }
    private static NativeActionPort.AckReceived successfulAck(ActionReceipt receipt,ActionPorts.OutcomeArchive archive){
        var dispatch=ActionTransitions.dispatch(receipt.state());
        if(dispatch.isEmpty())throw bridge("actual Army action has no native dispatch evidence");
        if(!(dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack))
            throw dispatchFailure(receipt.command().operation(),dispatch.orElseThrow(),Optional.of(archive.referenceOf(dispatch.orElseThrow())));
        StrictJson.require(ActionTransitions.attempt(receipt.state()).map(value->value.requestId().equals(ack.requestId())).orElse(false),
                "Army return crossed its original canonical native attempt");
        if(!ack.nativeOk()){
            Obj frame=DriverJson.object(ack.originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES);
            throw nativeFailure(frame,Optional.of(archive.referenceOf(ack)));
        }
        StrictJson.require(ack.originalResultToken().isPresent()&&ack.outbound().isPresent()&&ack.custody().isPresent(),
                "Army original result requires actual successful inbound/outbound custody");
        StrictJson.require(ack.equals(archive.load(archive.referenceOf(ack))),"Army result differs from its actual archived dispatch");
        ack.custody().orElseThrow().verify(ack,ActionTransitions.attempt(receipt.state()).orElseThrow().guard());
        Obj originalTop=DriverJson.object(ack.originalFrame().bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES)
                .equals(originalTop.get("result")),"Army primitive token differs from its actual original command_result");
        return ack;
    }
    static PublicServiceFailure dispatchFailure(OperationKey operation,NativeActionPort.DispatchOutcome dispatch,Optional<ExactRef> actualOriginal){
        String message;
        if(dispatch instanceof NativeActionPort.RejectedBeforeDispatch rejected)message=rejected.proof().reason();
        else if(dispatch instanceof NativeActionPort.Unknown)message="native command_result timed out for gameplay step "+operation.value();
        else throw new IllegalArgumentException("successful or native-rejected ACK must use its original return decoder");
        return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,actualOriginal);
    }
    static PublicServiceFailure nativeFailure(Obj frame,Optional<ExactRef> actualOriginal){
        String message=frame.get("error") instanceof Text text?text.value():"unknown error";
        return new PublicServiceFailure(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,
                "native gameplay step failed: "+message,actualOriginal);
    }
    /** Pure original Driver formatter; archive/Root qualification is mandatory in the actual callback above. */
    static RawJson formatNumeric(Kind kind,OperationKey step,RawJson primitive,Optional<RawJson> material,Optional<Obj> after){
        Obj original=DriverJson.object(primitive.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Text(step.value()).equals(original.get("step"))&&original.get("accepted") instanceof Bool,
                "Army primitive result crossed its original step or strict accepted flag");
        var fields=new java.util.LinkedHashMap<>(original.members());fields.put("backend_id",new Text("native-headless"));
        if(kind==Kind.COMMANDER)return new RawJson(DriverJson.encode(new Obj(fields)));
        StrictJson.require(material.isPresent()&&after.isPresent(),"Army original full result requires its independently observed effect basis");
        Obj source=DriverJson.object(material.orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(new Bool(true).equals(original.get("accepted"))&&new Text(step.value()).equals(source.get("step")),
                "Army effect cannot promote a rejected or different native primitive");
        StrictJson.require(source.get("war_action") instanceof Obj,"Army effect lacks its original action result");Obj action=(Obj)source.get("war_action");
        String status=kind==Kind.RAISE?"raised":"disbanded";
        StrictJson.require(new Text(status).equals(action.get("status")),"Army result action differs from the selected route");
        String key=kind==Kind.RAISE?"raised_army_ids":"army_id";Value subject=action.get(key);
        StrictJson.require(kind==Kind.RAISE?subject instanceof Arr:subject instanceof IntegerValue,"Army original action subject is malformed");
        if(kind==Kind.RAISE){
            var ids=((Arr)subject).items();StrictJson.require(!ids.isEmpty()&&ids.stream().allMatch(value->value instanceof IntegerValue integer
                    &&integer.value().signum()>=0&&integer.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0)
                    &&new java.util.HashSet<>(ids).size()==ids.size(),"original raised CUnit list is malformed");
        }else{
            var selected=(ArmyCalls.Unit)ArmyOrdinaryPlannerCalls.decode(step,EMPTY,BigInteger.ONE);
            StrictJson.require(new IntegerValue(BigInteger.valueOf(selected.army().value())).equals(subject),"Army effect changed the selected disband CUnit");
        }
        Obj projected=new Obj(Map.of("status",new Text(status),key,subject));Obj frame=after.orElseThrow();
        StrictJson.require(frame.get("player_armies") instanceof Arr&&frame.get("snapshot_id") instanceof Text
                &&frame.get("revision") instanceof IntegerValue&&Objects.equals(source.get("snapshot_id"),frame.get("snapshot_id"))
                &&Objects.equals(source.get("revision"),frame.get("revision")),"Army original full roster crossed its effect frame");
        fields.put("war_action",projected);fields.put("player_armies",frame.get("player_armies"));
        fields.put("snapshot_id",frame.get("snapshot_id"));fields.put("revision",frame.get("revision"));
        return new RawJson(DriverJson.encode(new Obj(fields)));
    }
    static RawJson encodeOriginal(RawJson numeric,ArmyTypes.Context source){
        return ArmyPublicWire.encodeExactSourceBound(DriverJson.object(numeric.bytes(),DriverJson.MAX_NATIVE_BYTES),source);
    }
    /** Only these two original fixed-window close names belong to this adapter. */
    static Optional<ArmyWindowCodec.Kind> windowKind(OperationKey operation){
        return switch(Objects.requireNonNull(operation).value()){
            case "close-war-declared-overview-v1" -> Optional.of(ArmyWindowCodec.Kind.OVERVIEW);
            case "close-war-results-window-v1" -> Optional.of(ArmyWindowCodec.Kind.RESULTS);
            default -> Optional.empty();
        };
    }
    static ArmyCalls.Frame windowCall(PublicPlanningCodec.ExecuteRequest caller,BigInteger actualPublicRevision){
        ArmyCalls.Frame input=windowSelection(caller);requireWindowRevisionCurrent(input,actualPublicRevision);return input;
    }
    /** Original expected type is checked before the shared actual-frame validator and stale comparison. */
    static ArmyCalls.Frame windowSelection(PublicPlanningCodec.ExecuteRequest caller){
        var kind=windowKind(caller.step()).orElseThrow(()->new IllegalArgumentException("unrelated fixed-window close step"));
        String label=kind==ArmyWindowCodec.Kind.OVERVIEW?"war overview":"war results";
        if(!(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue value)||value.value().signum()<=0)
            throw new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,label+" expected_revision is outside its native integer range",Optional.empty());
        return new ArmyCalls.Frame(kind==ArmyWindowCodec.Kind.OVERVIEW?PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                :PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1,new ArmyCalls.Revision(new ArmyTypes.Present<>(value.value())));
    }
    static void requireWindowRevisionCurrent(ArmyCalls.Frame input,BigInteger actualPublicRevision){
        String label=switch(input.method()){
            case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> "war overview";
            case CLOSE_WAR_RESULTS_WINDOW_V1 -> "war results";
            default -> throw new IllegalArgumentException("unrelated fixed-window close method");
        };
        if(!(input.revision().value() instanceof ArmyTypes.Present<BigInteger> selected))
            throw new IllegalArgumentException("selected window call lost its explicit public revision");
        if(!selected.value().equals(actualPublicRevision))throw new PublicServiceFailure(PublicServiceFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH,
                label+" public revision is stale",Optional.empty());
    }
    static PublicServiceFailure windowDispatchFailure(ArmyWindowCodec.Kind kind,NativeActionPort.DispatchOutcome actual,Optional<ExactRef> source){
        if(actual instanceof NativeActionPort.Unknown)return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                ArmyWindowQueryFailure.timeoutMessage(kind),source);
        if(actual instanceof NativeActionPort.RejectedBeforeDispatch rejected)return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                rejected.proof().reason(),source);
        throw new IllegalArgumentException("fixed-window ACK requires its original native TOP decoder");
    }
    static PublicServiceFailure windowNativeFailure(ArmyWindowCodec.Kind kind,RawJson top,String actualRequestId,Optional<ExactRef> source){
        return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                ArmyWindowQueryFailure.refusalMessage(kind,top,actualRequestId),source);
    }
    /** The source-owned full TOP decoder preserves no-op and unresolved results without close credit. */
    static RawJson windowNumeric(OperationKey step,RawJson actualOriginalTop,String actualRequestId,
            ArmyTypes.Context actualSource,BigInteger actualNativeConnection,BigInteger actualDriverConnection){
        var kind=windowKind(step).orElseThrow(()->new IllegalArgumentException("unrelated fixed-window close step"));
        var observed=ArmyWindowCodec.decode(kind,ArmyWindowCodec.Operation.CLOSE,actualOriginalTop.bytes(),
                actualRequestId,actualSource,actualNativeConnection,actualDriverConnection);
        return new RawJson(StrictJson.canonical(observed.normalized()));
    }
    private static PublicServiceFailure bridge(String message){return new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,message,Optional.empty());}
}
