package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original Driver EXECUTE READ results. Dedicated Service projections and action receipts are different contracts. */
public final class RootCombatPublicStepProducts {
    private RootCombatPublicStepProducts(){ }
    private static final List<PublicMethod> METHODS=List.of(PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,
            PublicMethod.QUERY_BATTLE_TRANSITION_V1,PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1,
            PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1,
            PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS,PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3);
    private static final List<String> CONTROL=List.of("selected_public_cunit_id","selected_native_carmy_id","selected_owner_character_id",
            "combat_province_id","side_index","side_scope","affected_public_cunit_ids_in_stored_order",
            "unaffected_same_side_public_cunit_ids_in_stored_order","side_flags","legality");
    private static final List<String> TRANSITION=List.of("combat_id","province_id","phase","phase_raw","phase_day","winner_side","winner_raw",
            "forced_winner_side","forced_winner_raw","finalized","battle_result_id","attacker_public_cunit_ids_in_stored_order",
            "defender_public_cunit_ids_in_stored_order","battle_transition_ready");
    private static final List<String> TERMINAL=List.of("prior_combat_id","subject_public_cunit_id","terminal_journal","prior","removal",
            "subject","successor","battle_terminal_transition_ready","unavailable_reason");
    private static final List<String> REINFORCEMENT=List.of("selected_public_cunit_id","selected_native_carmy_id","coordinator_id",
            "unit_stack_stored_index","subunit_stored_index","signal","assignment","route","native_order","contact_projection",
            "battle_reinforcement_assignment_ready","unavailable_reason");

    /** Only the identical already-installed families can issue contracts; this record grants no Root or writer authority. */
    record Reads(RootReadContractCatalog catalog,ArmyBattleReads battles,ArmyReinforcementReads reinforcement,ArmyForecastReads forecasts,NativeEffectEvidence.FrameLoader frames){
        Reads{Objects.requireNonNull(catalog);Objects.requireNonNull(battles);Objects.requireNonNull(reinforcement);Objects.requireNonNull(forecasts);Objects.requireNonNull(frames);
            for(var family:families(battles,reinforcement,forecasts))
                StrictJson.require(catalog.families().stream().anyMatch(installed->installed==family),"Combat EXECUTE requires its identical installed read families");}
    }
    /** Called once by the sole installed public-step aggregate; it performs no Native observation/query. */
    public static List<RootPublicStepExecution.Product> install(RootInstalledCatalog actual)throws IOException {
        Objects.requireNonNull(actual);RootRuntimeContext context=actual.context();
        Reads reads=new Reads(actual.bindings().readCatalog(),actual.army().products().battleContracts(),
                actual.additionalArmy().reinforcement(),actual.military().forecasts(),context.frameLoader());
        var closure=new LinkedHashSet<ExactRef>();closure.add(context.source().sourceRef());
        closure.add(actual.publicStepSourceAt("local-service/src/main/java/org/xar/ck3/control/service/root/RootCombatPublicStepProducts.java",RootCombatPublicStepProducts.class));
        closure.add(actual.publicStepSourceAt("application/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/ArmySteps.java",ArmySteps.class));
        closure.add(actual.publicStepSourceAt("application/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/BattleTerminalCodec.java",BattleTerminalCodec.class));
        for(var family:families(reads.battles(),reads.reinforcement(),reads.forecasts())){closure.add(family.definitionSource());closure.add(family.decoderSource());}
        List<ExactRef> sources=List.copyOf(closure);var products=new ArrayList<RootPublicStepExecution.Product>();
        RootPublicStepExecution.OwnerGuard owner=current->{
            if(current!=context||current.core()!=context.core()||current.readCatalog()!=reads.catalog()
                    ||actual.army().products().battleContracts()!=reads.battles()
                    ||actual.additionalArmy().reinforcement()!=reads.reinforcement()||actual.military().forecasts()!=reads.forecasts())
                throw new IOException("Combat EXECUTE crossed its installed physical Root/Core/read catalog");
            current.game().verify();
        };
        for(PublicMethod method:METHODS)products.add(new RootPublicStepExecution.Read("original-execute-combat-"+method.pythonName(),
                operation->matches(method,operation),owner,(original,frame,known,same,caller,archive)->{
                    owner.requireContext(context);context.writer().requireSession(same);Objects.requireNonNull(known);caller.requireCurrent(original);
                    StrictJson.require(frame.identity().equals(original.before())&&frame.source().equals(original.source())
                            &&frame.sessionId().equals(original.sessionId())&&frame.semantic().equals(original.observations().snapshot()),
                            "Combat EXECUTE must retain the original public planning Complete");
                    RawJson result=read(reads,frame,same,caller,archive,original.deadline());
                    context.writer().requireSession(same);owner.requireContext(context);return result;
                },sources));
        return List.copyOf(products);
    }
    static boolean matches(PublicMethod method,OperationKey operation){
        return ArmySteps.parseCombatRead(operation,new ArmyCalls.Revision(new Missing<>())).map(call->call.method()==method).orElse(false);
    }
    /** Shared producer seam for controlled software tests. The installed Root wrapper supplies/validates the private scope. */
    static RawJson read(Reads reads,Complete frame,Session same,PublicPlanningCodec.ExecuteRequest caller,OutcomeArchive archive,
            java.time.Instant deadline)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(archive);Objects.requireNonNull(frame);
        var current=new ArmyRetreatFrames.Current(frame,deadline);Context context=current.context();
        var revision=new ArmyCalls.Revision(new Present<>(context.before().frame().revision()));
        ArmyCalls.Call call=ArmySteps.parseCombatRead(caller.step(),revision).orElseThrow(()->new IOException("UnsupportedStepError: malformed original Combat READ"));
        if(caller.expectedRevision() instanceof PublicPlanningCodec.RevisionValue expected)
            StrictJson.require(expected.value().equals(context.before().frame().revision()),"public expected_revision is stale");
        try {
            if(call instanceof ArmyCalls.Unit unit&&call.method()==PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1){
                var subjects=OpportunityJson.array(frame.semantic().get("player_armies"),"actual player armies").stream()
                        .map(value->OpportunityJson.object(value,"actual player army"))
                        .filter(army->OpportunityJson.integer(army.get("army_id"),"public CUnit").intValueExact()==unit.army().value()).toList();
                StrictJson.require(subjects.size()==1&&new OpportunityJson.Bool(true).equals(subjects.getFirst().get("controllable"))
                        &&inCombat(subjects.getFirst()),"battle-control requires its actual current controllable in-combat public CUnit");
            }
            if(ArmyBattleReads.METHODS.contains(call.method())){
                Optional<OperationKey> literal=call instanceof ArmyCalls.Terminal?Optional.of(caller.step()):Optional.empty();
                var selection=new ArmyBattleReads.Selection(call,context,ArmyBattleReads.Capture.PUBLIC_QUERY,literal);
                var contract=reads.battles().issue(reads.catalog(),selection);
                var actual=reads.battles().read(same,reads.catalog(),selection);requireOriginal(reads,frame,context,caller,contract,actual,archive);
                return battle(context,actual);
            }
            if(call instanceof ArmyCalls.Unit unit&&call.method()==PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1){
                var selection=new ArmyReinforcementReads.Selection(unit,context,ArmyReinforcementReads.Capture.PUBLIC_QUERY);
                var contract=reads.reinforcement().issue(reads.catalog(),selection);var actual=reads.reinforcement().read(same,reads.catalog(),selection);
                requireOriginal(reads,frame,context,caller,contract,actual,archive);ObjectNode result=ArmyNativeReadEvidence.result(context,actual.receipt()).deepCopy();
                ObjectNode normalized=node(actual.value().originalFrame());result.set("battle_reinforcement_assignment",normalized);mirrors(result,normalized,REINFORCEMENT);
                queried(result,context);return encode(result,context);
            }
            var selection=new ArmyForecastReads.Selection(call,context);var contract=reads.forecasts().contract(reads.catalog(),selection);
            var collected=reads.forecasts().collect(same,reads.catalog(),selection);
            if(!(collected instanceof PlanningReadResult.Known<ForecastReadObservation> actual))
                throw new IOException("BridgeUnavailableError: "+((PlanningReadResult.Unavailable<ForecastReadObservation>)collected).reason());
            requireOriginal(reads,frame,context,caller,contract,actual,archive);
            ObjectNode result=node(actual.value().normalizedResult());
            StrictJson.require(result.path("queried_episode_run_id").asText().equals(context.before().frame().episodeRunId())
                    &&result.path("queried_connection_generation").isIntegralNumber()
                    &&result.path("queried_connection_generation").bigIntegerValue().equals(frame.connectionGeneration()),"forecast original publication source changed");
            result.remove(List.of("queried_episode_run_id","queried_connection_generation"));queried(result,context);
            return encode(result,context);
        }catch(IllegalArgumentException|IllegalStateException unavailable){
            throw new IOException("BridgeUnavailableError: original Combat READ unavailable: "+unavailable.getMessage(),unavailable);
        }
    }
    private static <T> void requireOriginal(Reads reads,Complete frame,Context context,PublicPlanningCodec.ExecuteRequest caller,ReadContract<T> contract,
            PlanningReadResult.Known<T> actual,OutcomeArchive archive){
        PlanningReadReceipt receipt=actual.receipt();ArmyNativeReadEvidence.verifyContext(context,receipt);
        StrictJson.require(contract.operation().equals(caller.step())&&receipt.request().operation().equals(caller.step())
                &&receipt.before().originalBindingSha256().equals(frame.fullBindingSha256())
                &&receipt.after().originalBindingSha256().equals(frame.fullBindingSha256()),"Combat READ changed its original literal or complete held binding");
        var before=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,reads.frames());
        var after=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,reads.frames());
        for(Complete guarded:List.of(before,after))StrictJson.require(guarded.identity().equals(frame.identity())
                &&guarded.source().equals(frame.source())&&guarded.sessionId().equals(frame.sessionId())
                &&guarded.connectionGeneration().equals(frame.connectionGeneration())&&guarded.fullBindingSha256().equals(frame.fullBindingSha256())
                &&guarded.semantic().equals(frame.semantic()),"Combat EXECUTE original guard crossed the complete public planning frame");
        ExactRef original=archive.readReferenceOf(receipt);
        StrictJson.require(original.equals(actual.originalReceipt())&&archive.loadRead(original).equals(receipt)
                &&contract.replay(receipt).equals(actual.value()),"Combat READ must retain/replay its full original central archive receipt");
    }
    private static RawJson battle(Context context,PlanningReadResult.Known<ArmyBattleReads.Observation> actual){
        ObjectNode result=ArmyNativeReadEvidence.result(context,actual.receipt()).deepCopy();var value=actual.value();ObjectNode normalized=node(value.normalized());
        String nested;
        if(value instanceof ArmyBattleReads.Control){nested="battle_control_snapshot";result.put("status","available");mirrors(result,normalized,CONTROL);}
        else if(value instanceof ArmyBattleReads.Transition){nested="battle_transition_snapshot";result.set("status",normalized.get("status"));mirrors(result,normalized,TRANSITION);
            optional(result,normalized,"current_observation");optional(result,normalized,"actual_geography_v1");}
        else{nested="battle_terminal_transition";result.set("status",normalized.get("status"));mirrors(result,normalized,TERMINAL);optional(result,normalized,"character_observations");}
        result.set(nested,normalized);ObjectNode extensions=node(value.extensions());extensions.fields().forEachRemaining(entry->result.set(entry.getKey(),entry.getValue().deepCopy()));
        queried(result,context);return encode(result,context);
    }
    private static void mirrors(ObjectNode result,ObjectNode normalized,List<String> fields){for(String field:fields){StrictJson.require(normalized.has(field),"missing normalized original mirror: "+field);result.set(field,normalized.get(field).deepCopy());}}
    private static void optional(ObjectNode result,ObjectNode normalized,String field){if(normalized.has(field))result.set(field,normalized.get(field).deepCopy());}
    private static void queried(ObjectNode result,Context context){result.put("backend_id","native-headless").put("queried_snapshot_id",context.before().frame().snapshotId())
            .put("queried_revision",context.before().frame().revision()).put("queried_native_revision",context.nativeRevision());}
    private static boolean inCombat(Obj army){
        return new OpportunityJson.Bool(true).equals(army.get("in_combat"))
                ||army.get("army_state") instanceof OpportunityJson.Text state&&state.value().equalsIgnoreCase("combat")
                ||new OpportunityJson.IntegerValue(java.math.BigInteger.TWO).equals(army.get("army_state_code"));
    }
    private static ObjectNode node(Obj value){return (ObjectNode)OpportunityJson.toNode(value);}
    private static RawJson encode(ObjectNode value,Context context){return ArmyPublicWire.encodeExactSourceBound(DriverJson.object(StrictJson.canonical(value),DriverJson.MAX_NATIVE_BYTES),context);}
    private static List<RootReadContractCatalog.Family<?,?>> families(ArmyBattleReads battle,ArmyReinforcementReads reinforcement,ArmyForecastReads forecast){
        var result=new ArrayList<RootReadContractCatalog.Family<?,?>>();result.addAll(battle.families());result.addAll(reinforcement.families());result.addAll(forecast.families());return List.copyOf(result);
    }
}
