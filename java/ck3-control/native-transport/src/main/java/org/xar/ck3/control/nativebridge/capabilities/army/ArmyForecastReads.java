package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.planning.military.NativeMilitaryInputView;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWarEntryReadBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.forecast.CombatNativeEnvelope;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real finite Native readers. Domain decoders and the one shared combat cache remain their original producers. */
public final class ArmyForecastReads {
    public static final Set<PublicMethod> METHODS=Set.of(PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3,
            PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS,PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1,PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1);
    public record Selection(ArmyCalls.Call input,Context context,Optional<EventWarEntryReadBindings.SavedScope> eventSavedScope) {
        public Selection(ArmyCalls.Call input,Context context){this(input,context,Optional.empty());}
        public Selection {
            Objects.requireNonNull(input);Objects.requireNonNull(context);Objects.requireNonNull(eventSavedScope);
            require(METHODS.contains(input.method()),"not one of the five forecast read routes");input.revision().requireCurrent(context.before().frame().revision());
            if(eventSavedScope.isPresent())require(input instanceof ArmyCalls.WarEntry call&&call.targets().size()==1
                    &&call.targets().getFirst().value()==eventSavedScope.orElseThrow().targetCharacterId(),"event saved scope requires its sole original target");
        }
    }
    private final EnumMap<PublicMethod,RootReadContractCatalog.Family<Selection,ForecastReadObservation>> families=new EnumMap<>(PublicMethod.class);
    private final PlanningReadPort reads;
    private final CombatObservationCache combat;
    private final NativeEffectEvidence.FrameLoader frames;
    private final ActionPorts.OutcomeArchive originals;
    private final java.util.function.Supplier<ContinuityStorePort.Session> currentSession;
    public ArmyForecastReads(ExactRef definitionSource,ExactRef strictDecoder,PlanningReadPort actualReads,
            CombatObservationCache sharedCombatCache,NativeEffectEvidence.FrameLoader originalFrames,
            ActionPorts.OutcomeArchive sameWriterArchive,java.util.function.Supplier<ContinuityStorePort.Session> borrowedSession) {
        reads=Objects.requireNonNull(actualReads);combat=Objects.requireNonNull(sharedCombatCache);frames=Objects.requireNonNull(originalFrames);
        originals=Objects.requireNonNull(sameWriterArchive);currentSession=Objects.requireNonNull(borrowedSession);
        for(PublicMethod method:METHODS) {
            String capability=capability(method);
            families.put(method,new RootReadContractCatalog.Family<>("army-forecast-"+method.pythonName(),Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.of(capability),definitionSource,strictDecoder,s->key(s),s->new OperationKey(primitive(s).request().step()),s-> {
                        var primitive=primitive(s);return new ReadContract<>("army-forecast-"+ArmyReadKey.digest(key(s)),new OperationKey(primitive.request().step()),
                                Optional.of(capability),primitive.permissionKey(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,primitive.wire(),ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definitionSource,
                                (request,id)->{verify(request,s);return primitive.request();},receipt->{verify(receipt.request(),s);return decode(s,receipt);},receipt->{verify(receipt.request(),s);return replay(s,receipt);},
                                (original,value,current,semantic)->{
                                    verify(original.request(),s);verify(current,s);
                                    var before=RootGuardEvidence.loadFrame(original.before().binding(),archive(),frames);
                                    require(NativeMilitaryInputView.sameNativeOperands(before.semantic(),semantic),"forecast native military operands changed after original read");
                                    require(value.equals(replay(s,original)),"forecast canonical value differs from original complete decoder");
                                });
                    }));
        }
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(value->value).toList();}
    public ReadContract<ForecastReadObservation> contract(RootReadContractCatalog catalog,Selection selected){return catalog.issue(families.get(selected.input().method()),selected);}
    public PlanningReadResult<ForecastReadObservation> collect(ContinuityStorePort.Session borrowed,RootReadContractCatalog catalog,Selection selected) {
        Objects.requireNonNull(borrowed);var contract=contract(catalog,selected);Context context=selected.context();
        return reads.read(borrowed,contract,new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),arguments(selected),context.deadline()));
    }
    public ForecastReadObservation decode(Selection selected,PlanningReadReceipt receipt) {
        return normalize(selected,receipt,false,null);
    }
    public ForecastReadObservation replay(Selection selected,PlanningReadReceipt receipt) {
        return normalize(selected,receipt,true,null);
    }
    /** The Root private canonical witness must be revalidated before this local current-frame cache activation. */
    public ForecastReadObservation activateCanonical(Selection originalSelection,PlanningReadReceipt original,Obj actualCurrentSnapshot) {
        require(originalSelection.input() instanceof ArmyCalls.Combat,"only combat observations have a shared cache slot");
        return normalize(originalSelection,original,false,Objects.requireNonNull(actualCurrentSnapshot));
    }
    private ForecastReadObservation normalize(Selection selected,PlanningReadReceipt receipt,boolean pureReplay,Obj actualCurrentSnapshot) {
        verify(receipt.request(),selected);Context context=ArmyNativeReadEvidence.contextForRequest(selected.context(),receipt.request());ObjectNode result=ArmyNativeReadEvidence.result(context,receipt);
        var before=RootGuardEvidence.loadFrame(receipt.before().binding(),archive(),frames);
        var after=RootGuardEvidence.loadFrame(receipt.after().binding(),archive(),frames);
        require(before.identity().equals(context.before())&&after.identity().equals(context.before())&&before.source().equals(context.source())&&after.source().equals(context.source())
                &&before.sessionId().equals(context.sessionId())&&after.sessionId().equals(context.sessionId())&&before.connectionGeneration().equals(after.connectionGeneration())
                &&before.fullBindingSha256().equals(after.fullBindingSha256())&&before.semantic().equals(after.semantic()),"forecast read crossed complete current native/Driver evidence");
        Obj observed;
        if(selected.input() instanceof ArmyCalls.Combat call) {
            Obj ending=actualCurrentSnapshot==null?after.semantic():actualCurrentSnapshot;
            if(actualCurrentSnapshot!=null)require(NativeMilitaryInputView.sameNativeOperands(before.semantic(),actualCurrentSnapshot),"canonical combat no longer has the original native operands");
            forecastEnvelope(result,CombatNativeEnvelope.Payload.COMBAT_INPUTS);String status=text(result.get("status"));
            var version=call.method()==PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS?CombatObservationCache.Version.V2:CombatObservationCache.Version.V3;
            require(version==CombatObservationCache.Version.V2?Set.of("available","partial").contains(status):Set.of("available","unavailable").contains(status),"combat version status differs");
            var normalized=pureReplay?combat.replay(version,result,OpportunityJson.toNode(before.semantic()),OpportunityJson.toNode(ending),call.selection(),context.before().frame().revision())
                    :combat.receive(version,result,OpportunityJson.toNode(before.semantic()),OpportunityJson.toNode(ending),call.selection(),context.before().frame().revision());
            result.set("combat_simulation_inputs",normalized.normalizedJson());observed=enrich(result,context,receipt);
            return new ForecastReadObservation.CombatInputs(normalized,observed);
        }
        if(selected.input() instanceof ArmyCalls.WarEntry call) {
            warEntryEnvelope(result);equal(result.get("status"),"available");
            List<Integer> targets=call.targets().stream().map(PositiveId::value).toList();
            selected.eventSavedScope().ifPresent(scope->scope.requireAssessmentReceipt(receipt));
            var scopes=selected.eventSavedScope().map(scope->scope.scopes(context,before.semantic(),archive()))
                    .orElseGet(()->WarEntryAssessmentCodec.targetScopes(OpportunityJson.toNode(before.semantic()),targets));
            var endingScopes=selected.eventSavedScope().map(scope->scope.scopes(context,after.semantic(),archive()))
                    .orElseGet(()->WarEntryAssessmentCodec.targetScopes(OpportunityJson.toNode(after.semantic()),targets));
            require(scopes.equals(endingScopes),"war-entry complete target scope changed");
            var normalized=WarEntryAssessmentCodec.normalize(result.get("war_entry_assessments"),new WarEntryAssessmentCodec.Expected(targets,context.playerId(),context.nativeRevision(),context.dateRaw()));
            result.set("war_entry_assessments",normalized.toNativeJson());result.set("target_scopes",scopes.toNativeJson());
            observed=enrich(result,context,receipt);return new ForecastReadObservation.WarEntry(freeze(normalized.toNativeJson()),new OpportunityJson.Arr(OpportunityJson.array(OpportunityJson.parse(bytes(scopes.toNativeJson())),"target scopes")),observed);
        }
        if(selected.input() instanceof ArmyCalls.Knight call) {
            require(names(result).equals(Set.of("step","accepted","status","query_sequence","snapshot_revision","current_battle_knight")),"current knight exact original outer fields required");
            yes(result.get("accepted"));positive(result.get("query_sequence"));equal(result.get("snapshot_revision"),context.nativeRevision());
            knightSource(before.semantic(),call.selection(),context);knightSource(after.semantic(),call.selection(),context);
            BattleResponseCodec.knight(bytes(result),context,call.selection());
            observed=enrich(result,context,receipt);return new ForecastReadObservation.CurrentKnight(freeze(object(result.get("current_battle_knight"))),observed);
        }
        var call=(ArmyCalls.CombatId)selected.input();forecastEnvelope(result,CombatNativeEnvelope.Payload.PHASE_TRACE);
        var normalized=CombatPhaseEventTraceCodec.normalize(result.get("combat_phase_event_trace"),call.combat().value());
        require((text(result.get("status")).equals("evaluator_probe_available"))==normalized.evaluatorReady()
                &&Set.of("evaluator_probe_available","unavailable").contains(text(result.get("status"))),"phase trace original status differs from probe readiness");
        result.set("combat_phase_event_trace",normalized.toNativeJson());observed=enrich(result,context,receipt);
        return new ForecastReadObservation.PhaseTrace(freeze(normalized.toNativeJson()),observed);
    }
    /** The supplier resolves only inside the current read/decode callback; no borrowed Session is retained. */
    private ActionPorts.OutcomeArchive archive(){return originals.withSession(Objects.requireNonNull(currentSession.get(),"forecast decode needs the actual current writer session"));}
    private static void knightSource(Obj snapshot,ArmyRequests.Knight request,Context context) {
        require(request.player().value()==context.playerId().intValueExact()&&request.dateRaw()==context.dateRaw().longValueExact()
                &&request.nativeRevision().value().equals(context.nativeRevision())&&request.snapshotId().equals(context.before().frame().snapshotId()),"knight exact expected frame differs");
        var armies=OpportunityJson.array(snapshot.get("player_armies"),"player armies");var matches=armies.stream().map(value->OpportunityJson.object(value,"army"))
                .filter(army->new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(request.subject().value())).equals(army.get("army_id"))).toList();
        require(matches.size()==1,"knight public subject is not unique");Obj subject=matches.getFirst();
        require(new OpportunityJson.Bool(true).equals(subject.get("controllable"))&&new OpportunityJson.Bool(true).equals(subject.get("in_combat"))
                &&new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(request.province().value())).equals(subject.get("current_province_id")),"knight subject is not current controllable combat army");
        long count=OpportunityJson.array(snapshot.get("active_wars"),"wars").stream().map(value->OpportunityJson.object(value,"war"))
                .filter(war->new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(request.war())).equals(war.get("war_id"))).count();require(count==1,"knight expected war is not unique and active");
    }
    private static void forecastEnvelope(ObjectNode result,CombatNativeEnvelope.Payload payload){
        CombatNativeEnvelope.validate(result,payload);
        yes(result.get("accepted")); positive(result.get("query_sequence"));
    }
    /** Actual WarEntryAssessmentsResultFrame emits these five fields; backend_id belongs to later Driver wrapping. */
    static void warEntryEnvelope(ObjectNode result){require(names(result).equals(Set.of("step","accepted","status","query_sequence","war_entry_assessments")),"exact five-key original native WarEntry result required");yes(result.get("accepted"));positive(result.get("query_sequence"));}
    private static Obj enrich(ObjectNode result,Context context,PlanningReadReceipt receipt){var n=result.deepCopy().put("queried_snapshot_id",context.before().frame().snapshotId()).put("queried_revision",context.before().frame().revision()).put("queried_native_revision",context.nativeRevision())
            .put("queried_episode_run_id",context.before().frame().episodeRunId()).put("queried_connection_generation",receipt.before().binding().connectionGeneration());return freeze(n);}
    private static Obj freeze(ObjectNode result){return DriverJson.object(bytes(result),DriverJson.MAX_NATIVE_BYTES);}
    /** Saved-window custody is internal read identity, never a public/native argument alias. */
    private static RawJson key(Selection selected){
        var original=ArmyReadKey.key(selected.input(),selected.context());
        if(selected.eventSavedScope().isEmpty())return original;
        var value=parse(original.bytes());
        selected.eventSavedScope().ifPresent(scope->value.set("event_saved_scope_read",parse(scope.key().bytes())));
        return new RawJson(bytes(value));
    }
    private static Obj arguments(Selection selected){
        var value=parse(ArmyCallCodec.encode(selected.input()).bytes());
        selected.eventSavedScope().ifPresent(scope->value.set("event_saved_scope_read",parse(scope.key().bytes())));
        return freeze(value);
    }
    private static void verify(PlanningReadRequest request,Selection selected){Context context=selected.context();require(request.before().equals(context.before())&&request.source().equals(context.source())&&request.sessionId().equals(context.sessionId())
            &&request.operation().value().equals(primitive(selected).request().step())&&request.arguments().equals(arguments(selected)),"forecast read crossed selected original source/arguments");}
    private static ArmyNativeRecipes.Primitive primitive(Selection selected){var prepared=ArmyNativeRecipes.prepare(selected.input(),selected.context(),new ArmyNativeRecipes.NoFacts(),false);require(prepared instanceof ArmyNativeRecipes.Primitive actual&&actual.effect()==ArmyNativeRecipes.Effect.READ_ONLY,"forecast route is not a native read");return (ArmyNativeRecipes.Primitive)prepared;}
    public static String capability(PublicMethod method){return switch(method){case QUERY_COMBAT_SIMULATION_INPUTS->"game.command.query-combat-simulation-inputs-v2-N";case QUERY_COMBAT_SIMULATION_INPUTS_V3->"game.command.query-combat-simulation-inputs-v3-N";case QUERY_WAR_ENTRY_ASSESSMENTS->"game.command.query-war-entry-assessments-v1-N";case QUERY_CURRENT_BATTLE_KNIGHT_V1->"game.command.query-current-battle-knight-v1-N-N-N";case QUERY_COMBAT_PHASE_EVENT_TRACE_V1->"game.command.query-combat-phase-event-trace-v1-N";default->throw new IllegalArgumentException("not a forecast reader");};}
}
