package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** One actual read family. Reinforcement is an observation of native AI intent, never a future combat admission. */
public final class ArmyReinforcementReads {
    public static final String CAPABILITY="game.command.query-battle-reinforcement-assignment-v1-N";
    public enum Capture {PUBLIC_QUERY,INTERNAL_OBSERVATION}
    public record Selection(ArmyCalls.Unit input,Context context,Capture capture) {
        public Selection(ArmyCalls.Unit input,Context context){this(input,context,Capture.PUBLIC_QUERY);}
        public Selection {Objects.requireNonNull(input);Objects.requireNonNull(context);Objects.requireNonNull(capture);require(input.method()==PublicMethod.QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1,"wrong reinforcement query method");input.revision().requireCurrent(context.before().frame().revision());}
        public String step(){return "query-battle-reinforcement-assignment-v1-"+input.army().value();}
    }
    private final RootReadContractCatalog.Family<Selection,BattleResponses.Reinforcement> family;
    private final PlanningReadPort reads;
    public ArmyReinforcementReads(ExactRef definition,ExactRef decoder,PlanningReadPort reads) {
        this.reads=Objects.requireNonNull(reads);
        family=new RootReadContractCatalog.Family<>("army-reinforcement-assignment",Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAPABILITY),definition,decoder,
                ArmyReinforcementReads::key,s->new OperationKey(s.step()),s->new ReadContract<>("army-reinforcement-"+ArmyReadKey.digest(key(s)),new OperationKey(s.step()),Optional.of(CAPABILITY),CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,
                    (request,id)->{verify(s,request);return new NativeRequest(s.step(),Optional.of(CAPABILITY),new RawJson(new byte[]{'{','}'}));},receipt->decode(s,receipt),receipt->decode(s,receipt),
                    (original,value,current,semantic)->ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current)));
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.of(family);}
    public ReadContract<BattleResponses.Reinforcement> issue(RootReadContractCatalog catalog,Selection s){return catalog.issue(family,s);}
    public PlanningReadRequest request(Selection s){var c=s.context();return new PlanningReadRequest(c.before(),c.source(),c.sessionId(),new OperationKey(s.step()),arguments(s),c.deadline());}
    public PlanningReadResult.Known<BattleResponses.Reinforcement> read(ContinuityStorePort.Session same,RootReadContractCatalog catalog,Selection s){var result=reads.read(same,issue(catalog,s),request(s));if(result instanceof PlanningReadResult.Known<BattleResponses.Reinforcement> known)return known;throw new IllegalStateException(((PlanningReadResult.Unavailable<BattleResponses.Reinforcement>)result).reason());}
    public static BattleResponses.Reinforcement decode(Selection s,PlanningReadReceipt receipt){verify(s,receipt.request());var current=ArmyNativeReadEvidence.contextForRequest(s.context(),receipt.request());return ArmyReinforcementCodec.decode(ArmyJson.bytes(ArmyNativeReadEvidence.result(current,receipt)),current,new ArmyRequests.Unit(s.input().army()));}
    private static RawJson key(Selection s){var n=ArmyJson.parse(ArmyReadKey.key(s.input(),s.context()).bytes()).put("capture_context",s.capture().name());return new RawJson(ArmyJson.bytes(n));}
    private static OpportunityJson.Obj arguments(Selection s){var n=ArmyJson.empty().put("capture_context",s.capture().name());n.set("public_arguments",ArmyJson.parse(ArmyCallCodec.encode(s.input()).bytes()));return OpportunityJson.object(OpportunityJson.parse(ArmyJson.bytes(n)),"reinforcement arguments");}
    private static void verify(Selection s,PlanningReadRequest request){var c=s.context();require(request.before().equals(c.before())&&request.source().equals(c.source())&&request.sessionId().equals(c.sessionId())&&request.arguments().equals(arguments(s))&&request.operation().value().equals(s.step()),"reinforcement read crossed actual source or selected subject");}
}
