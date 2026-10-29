package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Strict original data boundary only. The Root guard separately authenticates live pending membership and archived custody. */
public final class ArmyReconciliationReadEvidence {
    private ArmyReconciliationReadEvidence(){}
    public static Context context(ReconciliationIdentity identity,PlanningReadRequest request){
        require(request.origin() instanceof CommandOrigin.Reconciliation&&request.origin().requireReconciliation().equals(identity),"Army reconciliation request crossed its complete original pending identity");
        require(request.source().equals(identity.source())&&request.sessionId().equals(identity.sessionId()),"Army reconciliation source/session changed");
        return new Context(identity.factual(),identity.source(),identity.sessionId(),request.deadline());
    }
    public static ObjectNode result(ReconciliationIdentity identity,PlanningReadReceipt receipt){
        verifyContext(identity,receipt);
        ObjectNode top=closed(parse(receipt.original().originalFrame().bytes()),"type","protocol_version","request_id","ok","result");
        equal(top.get("type"),"command_result");require(i32(top.get("protocol_version"))==1,"Army post read Native protocol differs");equal(top.get("request_id"),receipt.requestId());yes(top.get("ok"));
        ObjectNode result=object(top.get("result"));
        require(receipt.original().nativeOk()&&receipt.original().originalResultToken().isPresent()
                &&parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(result),"Army reconciliation token differs from complete actual Native result");
        equal(result.get("step"),receipt.request().operation().value());return result;
    }
    /** Context guard only. Strict versioned TOP6/window or execution-receipt codecs still validate their own complete envelopes. */
    public static void verifyContext(ReconciliationIdentity identity,PlanningReadReceipt receipt){
        context(identity,receipt.request());
        for(var guard:List.of(receipt.before(),receipt.after())){
            require(guard.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION,"Army post read borrowed ordinary gameplay readiness");
            var binding=guard.binding();
            require(binding.origin() instanceof CommandOrigin.Reconciliation&&binding.origin().requireReconciliation().sameGuardFrame(identity),"Army post read guard crossed original pending/current evidence");
            require(binding.source().equals(identity.source())&&binding.sessionId().equals(identity.sessionId())&&binding.operation().equals(receipt.request().operation())
                    &&binding.connectionGeneration().equals(identity.connectionGeneration())&&binding.nativeEvidence().equals(identity.nativeEvidence())&&binding.capabilityEvidence().equals(identity.capabilityEvidence()),"Army reconciliation guard source/original evidence differs");
            require(guard.originalBindingSha256().equals(identity.bindingSha256()),"Army reconciliation complete original guard digest differs");
        }
    }
}
