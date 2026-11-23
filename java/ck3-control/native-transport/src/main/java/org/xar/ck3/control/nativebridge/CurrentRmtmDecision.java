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

/** One fixed ordinary RMTM decision claim; construction does not confer private custody. */
public final class CurrentRmtmDecision {
    public static final String SCHEMA="ck3.rmtm_decision.current267_request.v1";
    public static final String SOURCE_SCHEMA="ck3.rmtm_decision.current267_source.v1";
    public static final String RESULT_SCHEMA="ck3.rmtm_decision.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-rmtm-decision";
    public enum Action {
        QUERY("query","query-rmtm-decision-current-v1","game.query.current-rmtm-decision.v1"),
        OPEN_LIST("open_list","open-rmtm-decisions-current-v1","game.command.open-current-rmtm-decisions.v1"),
        OPEN_DETAIL("open_detail","open-rmtm-decision-current-v1","game.command.open-current-rmtm-decision.v1"),
        CONFIRM("confirm","confirm-rmtm-decision-current-v1","game.command.confirm-current-rmtm-decision.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;} public String step(){return step;} public String capability(){return capability;}
        public boolean queryOnly(){return this==QUERY;}
        public static Action parse(String value)throws IOException{for(var a:values())if(a.wire.equals(value))return a;throw new IOException("Unknown RMTM decision action");}
    }
    public enum DecisionKey {
        CONTINUE_CORE("rqa120_continue_decision"), PREPARE_FIFTY("rqaui_prepare_fifty_decision"),
        PREPARE_FIFTYONE("rqaui_prepare_fiftyone_decision"), RESTORE("rmtm_claim_restoration_decision"),
        VERIFY_RESTORE("rqaui_verify_actual_restoration_decision");
        private final String wire;DecisionKey(String wire){this.wire=wire;}public String wire(){return wire;}
        public static DecisionKey parse(String value)throws IOException{for(var k:values())if(k.wire.equals(value))return k;throw new IOException("Unknown fixed RMTM decision");}
    }
    private CurrentRmtmDecision() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Optional<DecisionKey> decisionKey){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(decisionKey);
        CurrentRmtmDecision.unsigned(provider,false);CurrentRmtmDecision.unsigned(query,false);CurrentRmtmDecision.requireCore(actual.prefix());
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        StrictJson.require(action==Action.QUERY?provider.signum()==0&&query.signum()==0&&decisionKey.isEmpty()
                :provider.signum()>0&&query.signum()>0&&(action==Action.OPEN_LIST?decisionKey.isEmpty():decisionKey.isPresent()),"Exact decision selector/private query role differs");
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256()).put("adapter_id",b.coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider).put("query_sequence",query);
        claim.set("expected_core",CurrentRmtmDecision.core(actual.prefix()));
        if(decisionKey.isPresent())claim.put("decision_key",decisionKey.orElseThrow().wire());else claim.putNull("decision_key");
        var fields=StrictJson.object();fields.set("rmtm_decision",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
    // Shared Core/JSON validation only; no Title, CCC or other family custody is imported.
    static void unsigned(BigInteger n,boolean positive){CurrentRmtmTitleQuery.unsigned(n,positive);}
    static void requireCore(CoreFrame.Prefix p){CurrentRmtmTitleQuery.requirePrefix(p);}
    static com.fasterxml.jackson.databind.node.ObjectNode core(CoreFrame.Prefix p){return CurrentRmtmTitleQuery.prefix(p);}
    static void identity(com.fasterxml.jackson.databind.node.ObjectNode n,String k,String expected)throws IOException{CurrentRmtmTitleQuery.identity(n,k,expected);}
    static BigInteger decimal(com.fasterxml.jackson.databind.node.ObjectNode n,String k)throws IOException{return CurrentRmtmTitleQuery.decimal(n,k);}
    static int i32(JsonNode n)throws IOException{return CurrentRmtmTitleQuery.i32(n);}
    static boolean bool(com.fasterxml.jackson.databind.node.ObjectNode n,String k)throws IOException{return CurrentRmtmTitleQuery.bool(n,k);}
    static Optional<DecisionKey> key(JsonNode value)throws IOException{return value.isNull()?Optional.empty():Optional.of(DecisionKey.parse(NativeWire.text(value)));}
}
