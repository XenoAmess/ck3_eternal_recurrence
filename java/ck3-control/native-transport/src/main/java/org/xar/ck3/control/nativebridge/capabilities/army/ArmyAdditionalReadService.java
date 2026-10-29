package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.military.CommanderBindings;
import org.xar.ck3.control.application.planning.military.CommanderObservationCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.commander.CommanderQualityCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Three complete public reads. Market and commander reuse their existing exact installed producer instances. */
public final class ArmyAdditionalReadService {
    @FunctionalInterface public interface Deadline {Instant open();}
    public sealed interface Reply permits Mercenary,Commander,Reinforcement {ArmyCalls.Call input();Context context();Obj result();}
    public record Mercenary(ArmyCalls.Frame input,Context context,PlanningReadResult.Known<FinanceReadContracts.Packet> original,ArmyMercenaryContextCodec.Observation observed,Obj result) implements Reply { }
    public record Commander(ArmyCalls.Commander input,Context context,PlanningReadResult.Known<CommanderObservationCollector.Observation> original,Obj result) implements Reply { }
    public record Reinforcement(ArmyCalls.Unit input,Context context,PlanningReadResult.Known<BattleResponses.Reinforcement> original,ArmyReinforcementAssessment.Assessment arrivalAssessment,Obj result) implements Reply { }
    private final ContinuityStorePort writer;private final ArmyRetreatFrames frames;private final PlanningReadPort reads;private final Supplier<RootReadContractCatalog> catalog;
    private final FinanceReadContracts finance;private final CommanderBindings commanders;private final ArmyReinforcementReads reinforcements;private final Deadline deadline;
    public ArmyAdditionalReadService(ContinuityStorePort actualWriter,ArmyRetreatFrames actualFrames,PlanningReadPort sameReads,Supplier<RootReadContractCatalog> catalog,FinanceReadContracts exactFinance,
            CommanderBindings exactCommander,ArmyReinforcementReads actualReinforcement,Deadline actualDeadline) {
        writer=Objects.requireNonNull(actualWriter);frames=Objects.requireNonNull(actualFrames);reads=Objects.requireNonNull(sameReads);this.catalog=Objects.requireNonNull(catalog);finance=Objects.requireNonNull(exactFinance);commanders=Objects.requireNonNull(exactCommander);reinforcements=Objects.requireNonNull(actualReinforcement);deadline=Objects.requireNonNull(actualDeadline);
    }
    public Reply query_player_mercenary_context_v1(ArmyCalls.Frame input){require(input.method()==PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,"wrong market public method");return execute(input);}
    public Reply query_army_commander_candidates_v1(ArmyCalls.Commander input){return execute(input);}
    public Reply query_battle_reinforcement_assignment_v1(ArmyCalls.Unit input){require(input.method()==PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,"wrong reinforcement public method");return execute(input);}
    private Reply execute(ArmyCalls.Call input){try{return writer.locked(same->read(same,input,deadline.open()));}catch(IOException failure){throw new UncheckedIOException(failure);}}
    public Reply read(ContinuityStorePort.Session same,ArmyCalls.Call input,Instant deadline) {
        try {
            var before=frames.current(deadline);input.revision().requireCurrent(before.context().before().frame().revision());Context c=before.context();Reply reply;
            if(input instanceof ArmyCalls.Frame call&&call.method()==PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1) {
                var contract=finance.contract(FinanceReadContracts.Query.MERCENARIES);var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),FinanceReadContracts.Query.MERCENARIES.operation(),new Obj(java.util.Map.of()),deadline);
                var actual=known(reads.read(same,contract,request));ArmyNativeReadEvidence.verifyContext(c,actual.receipt());var packet=actual.value();
                var result=ArmyJson.object(OpportunityJson.toNode(packet.originalResult())).deepCopy();ArmyJson.equal(result.get("step"),FinanceReadContracts.Query.MERCENARIES.operation().value());ArmyJson.yes(result.get("accepted"));ArmyJson.equal(result.get("status"),"completed");ArmyJson.yes(result.get("read_only"));ArmyJson.positive(result.get("query_sequence"));ArmyJson.equal(result.get("snapshot_revision"),c.nativeRevision());ArmyJson.equal(result.get("date_raw"),c.dateRaw());
                var payload=DriverJson.object(ArmyJson.bytes(result.get("player_mercenary_context")),DriverJson.MAX_NATIVE_BYTES);var observation=ArmyMercenaryContextCodec.decode(payload,before.actual().semantic());result.set("player_mercenary_context",OpportunityJson.toNode(observation.normalized()));
                reply=new Mercenary(call,c,actual,observation,freeze(result));
            } else if(input instanceof ArmyCalls.Commander call) {
                var actualInput=new CommanderObservationCollector.ObservedInput(c.before(),c.source(),c.sessionId(),deadline,before.actual().semantic(),actualCapabilities(before));
                Optional<Integer> target=call.target() instanceof Present<PositiveId> present?Optional.of(present.value().value()):Optional.empty();
                var actual=known(commanders.read(actualInput,call.army().value(),target,Objects.requireNonNull(catalog.get()),same));ArmyNativeReadEvidence.verifyContext(c,actual.receipt());var result=ArmyNativeReadEvidence.result(c,actual.receipt()).deepCopy();
                result.set("army_commander_candidates",actual.value().observed().normalizedJson());result.set("commander_quality_proposal",CommanderQualityCodec.encodeProposal(actual.value().proposal()));reply=new Commander(call,c,actual,freeze(result));
            } else if(input instanceof ArmyCalls.Unit call&&call.method()==PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1) {
                var actual=reinforcements.read(same,Objects.requireNonNull(catalog.get()),new ArmyReinforcementReads.Selection(call,c));var observed=actual.value();var result=ArmyNativeReadEvidence.result(c,actual.receipt()).deepCopy();var normalized=ArmyJson.object(OpportunityJson.toNode(observed.originalFrame()));
                result.put("backend_id","native-headless").put("schema_version",1).put("scope","native-ai-reinforcement-assignment");result.set("battle_reinforcement_assignment",normalized);
                for(String key:List.of("selected_public_cunit_id","selected_native_carmy_id","coordinator_id","unit_stack_stored_index","subunit_stored_index","signal","assignment","route","native_order","contact_projection","battle_reinforcement_assignment_ready","unavailable_reason"))result.set(key,normalized.get(key));
                result.set("source",new ArmyPublicSnapshot(c,before.actual().semantic()).source());reply=new Reinforcement(call,c,actual,ArmyReinforcementAssessment.derive(observed),freeze(result));
            } else throw new IllegalArgumentException("Army additional read is not an installed finite query");
            ArmyRetreatFrames.same(before,frames.current(deadline));return reply;
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IllegalStateException("actual Army read interrupted before its final same-frame qualification",interrupted);}
    }
    public List<PublicBindings.BoundBinding> install(PublicBindings bindings,ExactRef actualService) {
        return List.of(register(bindings,PublicMethod.QUERY_PLAYER_MERCENARY_CONTEXT_V1,ArmyCalls.Frame.class,this::query_player_mercenary_context_v1,actualService),register(bindings,PublicMethod.QUERY_ARMY_COMMANDER_CANDIDATES_V1,ArmyCalls.Commander.class,this::query_army_commander_candidates_v1,actualService),register(bindings,PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,ArmyCalls.Unit.class,this::query_battle_reinforcement_assignment_v1,actualService));
    }
    private static <T extends ArmyCalls.Call> PublicBindings.TypedBinding<T,Reply> register(PublicBindings bindings,PublicMethod method,Class<T> type,PublicRoutes.Handler<T,Reply> handler,ExactRef source) {
        return bindings.register(method,type,Reply.class,handler,args->{if(!(args instanceof PublicBindings.Value value))throw new IllegalArgumentException("Army read requires named typed arguments");return type.cast(ArmyCallCodec.decode(method,value.original()));},ArmyAdditionalReadService::encode,new PublicRoutes.Target(ArmyAdditionalReadService.class.getName(),method.pythonName(),source),PublicRoutes.Status.IMPLEMENTED,"actual sole owner read contracts and complete shared typed payloads; source candidate awaits Root verification");
    }
    public static RawJson encode(Reply reply){var result=ArmyJson.object(OpportunityJson.toNode(reply.result())).deepCopy();result.remove(List.of("queried_snapshot_id","queried_revision","queried_native_revision"));return ArmyPublicWire.encode(freeze(result),reply.context());}
    private static Set<String> actualCapabilities(ArmyRetreatFrames.Current frame) {var snapshot=frame.actual().semantic();var hello=OpportunityJson.object(OpportunityJson.object(snapshot.get("diagnostics"),"actual diagnostics").get("hello"),"actual hello");var values=OpportunityJson.array(hello.get("capabilities"),"actual hello capabilities");return values.stream().map(v->OpportunityJson.text(v,"actual capability")).collect(java.util.stream.Collectors.toUnmodifiableSet());}
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result){if(result instanceof PlanningReadResult.Known<T> known)return known;throw new IllegalStateException(((PlanningReadResult.Unavailable<T>)result).reason());}
    private static Obj freeze(com.fasterxml.jackson.databind.node.ObjectNode value){return DriverJson.object(ArmyJson.bytes(value),DriverJson.MAX_NATIVE_BYTES);}
}
