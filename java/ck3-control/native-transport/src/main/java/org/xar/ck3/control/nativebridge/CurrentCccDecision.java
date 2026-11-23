package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** One fixed ordinary CCC decision claim; construction does not confer private custody. */
public final class CurrentCccDecision {
    public static final String SCHEMA="ck3.ccc_decision.current267_request.v1";
    public static final String SOURCE_SCHEMA="ck3.ccc_decision.current267_source.v1";
    public static final String RESULT_SCHEMA="ck3.ccc_decision.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-ccc-decision";
    public enum Action {
        QUERY("query","query-ccc-decision-current-v1","game.query.current-ccc-decision.v1"),
        OPEN_LIST("open_list","open-ccc-decisions-current-v1","game.command.open-current-ccc-decisions.v1"),
        OPEN_DETAIL("open_detail","open-ccc-decision-current-v1","game.command.open-current-ccc-decision.v1"),
        CONFIRM("confirm","confirm-ccc-decision-current-v1","game.command.confirm-current-ccc-decision.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;} public String step(){return step;} public String capability(){return capability;}
        public boolean queryOnly(){return this==QUERY;}
        public static Action parse(String value)throws IOException{for(var a:values())if(a.wire.equals(value))return a;throw new IOException("Unknown CCC decision action");}
    }
    public enum DecisionKey {
        CORRUPTION_POLICY("xccc_corruption_policy_decision");
        private final String wire;DecisionKey(String wire){this.wire=wire;}public String wire(){return wire;}
        public static DecisionKey parse(String value)throws IOException{for(var k:values())if(k.wire.equals(value))return k;throw new IOException("Unknown fixed CCC decision");}
    }
    private CurrentCccDecision() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Optional<DecisionKey> decisionKey){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(decisionKey);
        CurrentCccActorTransition.unsigned(provider,false);CurrentCccActorTransition.unsigned(query,false);CurrentCccActorTransition.requireCore(actual.prefix());
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        StrictJson.require(action==Action.QUERY?provider.signum()==0&&query.signum()==0&&decisionKey.isEmpty()
                :provider.signum()>0&&query.signum()>0&&(action==Action.OPEN_LIST?decisionKey.isEmpty():decisionKey.isPresent()),"Exact decision selector/private query role differs");
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256()).put("adapter_id",b.coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider).put("query_sequence",query);
        claim.set("expected_core",CurrentCccActorTransition.core(actual.prefix()));
        if(decisionKey.isPresent())claim.put("decision_key",decisionKey.orElseThrow().wire());else claim.putNull("decision_key");
        var fields=StrictJson.object();fields.set("ccc_decision",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    static Optional<DecisionKey> key(JsonNode value)throws IOException{return value.isNull()?Optional.empty():Optional.of(DecisionKey.parse(NativeWire.text(value)));}
}
