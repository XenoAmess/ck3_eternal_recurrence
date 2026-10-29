package org.xar.ck3.control.nativebridge.capabilities.army;

import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Dedicated read-only original-pending factories. No gameplay request, readiness, public history or submit authority is constructed. */
public final class ArmyBattleReconciliationReads {
    public record Selection(ReconciliationIdentity identity,ArmyCalls.Call input,Instant deadline){
        public Selection{Objects.requireNonNull(identity);Objects.requireNonNull(input);Objects.requireNonNull(deadline);require(ArmyBattleReads.METHODS.contains(input.method()),"not a finite M5 reconciliation read");input.revision().requireCurrent(identity.factual().frame().revision());}
        public Context facts(){return new Context(identity.factual(),identity.source(),identity.sessionId(),deadline);}
    }
    public record Issued(ReadContract<ArmyBattleReads.Observation> contract,PlanningReadRequest request){
        public Issued{Objects.requireNonNull(contract);Objects.requireNonNull(request);require(contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION&&request.origin() instanceof CommandOrigin.Reconciliation,"M5 reconciliation cannot borrow gameplay permission");}
    }
    private final EnumMap<PublicMethod,RootReadContractCatalog.Family<Selection,ArmyBattleReads.Observation>> families=new EnumMap<>(PublicMethod.class);
    private final PlanningReadPort reads;
    public ArmyBattleReconciliationReads(ExactRef definition,ExactRef decoder,PlanningReadPort actualReads){
        reads=Objects.requireNonNull(actualReads);
        for(var method:ArmyBattleReads.METHODS){
            String cap=capability(method);families.put(method,new RootReadContractCatalog.Family<>("army-m5-reconciliation-"+method.pythonName(),Selection.class,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,Optional.of(cap),definition,decoder,ArmyBattleReconciliationReads::key,s->new OperationKey(primitive(s).request().step()),s->{
                var prepared=primitive(s);var operation=new OperationKey(prepared.request().step());
                return new ReadContract<>("army-m5-reconciliation-"+method.pythonName()+"-"+ArmyReadKey.digest(key(s)),operation,Optional.of(cap),prepared.permissionKey(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,prepared.wire(),ReadContract.GuardMode.RECONCILIATION_OBSERVATION,definition,
                        (request,id)->{verify(s,request);return prepared.request();},receipt->decode(s,receipt),receipt->decode(s,receipt),
                        (original,value,current,semantic)->{require(original.request().origin().equals(current.origin())&&original.request().source().equals(current.source())&&original.request().sessionId().equals(current.sessionId())&&original.request().operation().equals(current.operation())&&original.request().arguments().equals(current.arguments()),"reconciliation cannot reuse a different pending/source/selection");});
            }));
        }
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(x->x).toList();}
    public Issued issue(RootReadContractCatalog catalog,Selection selected){var contract=catalog.issue(Objects.requireNonNull(families.get(selected.input().method())),selected);return new Issued(contract,PlanningReadRequest.newReconciliation(selected.identity(),contract.operation(),arguments(selected.input()),selected.deadline()));}
    public PlanningReadResult<ArmyBattleReads.Observation> collect(ContinuityStorePort.Session same,RootReadContractCatalog catalog,Selection selected){var issued=issue(catalog,selected);return reads.read(same,issued.contract(),issued.request());}
    public PlanningReadResult.Known<ArmyBattleReads.Observation> read(ContinuityStorePort.Session same,RootReadContractCatalog catalog,Selection selected){var result=collect(same,catalog,selected);if(result instanceof PlanningReadResult.Known<ArmyBattleReads.Observation> known)return known;throw new IllegalStateException(((PlanningReadResult.Unavailable<ArmyBattleReads.Observation>)result).reason());}
    public static ArmyBattleReads.Observation decode(Selection selected,PlanningReadReceipt receipt){verify(selected,receipt.request());var context=ArmyReconciliationReadEvidence.context(selected.identity(),receipt.request());return ArmyBattleReads.decodePayload(selected.input(),context,ArmyReconciliationReadEvidence.result(selected.identity(),receipt));}
    public static Obj arguments(ArmyCalls.Call input){return OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(input).bytes()),"closed M5 reconciliation arguments");}
    private static void verify(Selection selected,PlanningReadRequest request){ArmyReconciliationReadEvidence.context(selected.identity(),request);require(request.arguments().equals(arguments(selected.input()))&&request.operation().value().equals(primitive(selected).request().step()),"M5 reconciliation crossed its actual typed subject");}
    private static ArmyNativeRecipes.Primitive primitive(Selection selected){var value=ArmyNativeRecipes.prepare(selected.input(),selected.facts(),new ArmyNativeRecipes.NoFacts(),false);require(value instanceof ArmyNativeRecipes.Primitive,"M5 post read is not a primitive");var primitive=(ArmyNativeRecipes.Primitive)value;require(primitive.effect()==ArmyNativeRecipes.Effect.READ_ONLY,"reconciliation cannot submit a mutation");return primitive;}
    private static String capability(PublicMethod method){return switch(method){case QUERY_BATTLE_CONTROL_SNAPSHOT_V1->"game.command.query-battle-control-snapshot-v1-N";case QUERY_BATTLE_TRANSITION_V1->"game.command.query-battle-transition-v1-N";case QUERY_BATTLE_TERMINAL_TRANSITION_V1->"game.command.query-battle-terminal-transition-v1-N";default->throw new IllegalArgumentException("not M5");};}
    private static RawJson key(Selection selected){var n=ArmyJson.empty();n.set("identity",ReconciliationIdentityCodec.encode(selected.identity()));n.set("public_arguments",OpportunityJson.toNode(arguments(selected.input())));return new RawJson(StrictJson.canonical(n));}
}
