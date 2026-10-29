package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.ArrayList;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure startup policy SPI. Decisions carry source evidence and never grant a read or submit permit. */
public sealed interface FixtureStartupHandler permits FixtureStartupCase {
    sealed interface Decision permits AutomaticSharedPolicy,SelectDisplayedOption,ObserveOnly {
        ExactRef implementationSource();
    }
    record AutomaticSharedPolicy(ExactRef implementationSource) implements Decision {
        public AutomaticSharedPolicy {Objects.requireNonNull(implementationSource);}
    }
    record SelectDisplayedOption(long eventInstanceId,int optionNumber,ScopeEvidence proof,
            ExactRef implementationSource) implements Decision {
        public SelectDisplayedOption {
            if(eventInstanceId<=0||optionNumber<=0)throw new IllegalArgumentException("positive original displayed event/option required");
            Objects.requireNonNull(proof);Objects.requireNonNull(implementationSource);
        }
    }
    record ObserveOnly(ExactRef implementationSource) implements Decision {
        public ObserveOnly {Objects.requireNonNull(implementationSource);}
    }
    record ActorScope(int runtimeCharacterId,String historicalCharacterId,String scopeName,
            int beginLine,int passLine,int endLine,long byteStart,long byteEnd,String blockSha256) {
        public ActorScope {
            if(runtimeCharacterId<=0||beginLine<=0||passLine<=beginLine||endLine<=passLine||byteStart<0||byteEnd<=byteStart
                    ||!blockSha256.matches("[0-9a-f]{64}"))throw new IllegalArgumentException("actual unique ordered actor scope required");
            Objects.requireNonNull(historicalCharacterId);Objects.requireNonNull(scopeName);
        }
    }
    record ScopeEvidence(ExactRef actualLog,List<ActorScope> scopes,boolean businessPass) {
        public ScopeEvidence {
            Objects.requireNonNull(actualLog);scopes=List.copyOf(scopes);
            if(scopes.isEmpty()||businessPass)throw new IllegalArgumentException("startup scope is evidence, not product acceptance");
        }
    }
    Decision decide(PreparedFixture identicalFixture,OpportunityJson.Obj actualSnapshot,
            OpportunityJson.Obj actualEventWindow)throws IOException;
    void verifySources()throws IOException;
    List<ExactRef> sourceClosure();
    static List<ExactRef> decisionSources(Decision decision) {
        return decision instanceof SelectDisplayedOption selected?List.of(selected.implementationSource(),selected.proof().actualLog()):List.of(decision.implementationSource());
    }
    static OpportunityJson.Obj encodeDecision(Decision decision) {
        ObjectNode n=StrictJson.object().put("schema","xar.java.fixture-startup-decision/v1");
        n.set("implementation_source",decision.implementationSource().toJson());
        if(decision instanceof SelectDisplayedOption selected) {
            n.put("kind","select_displayed_option").put("event_instance_id",Long.toString(selected.eventInstanceId())).put("option_number",selected.optionNumber());
            ObjectNode proof=StrictJson.object().put("business_pass",false);proof.set("actual_log",selected.proof().actualLog().toJson());var scopes=proof.putArray("scopes");
            for(ActorScope scope:selected.proof().scopes())scopes.add(StrictJson.object().put("runtime_character_id",scope.runtimeCharacterId())
                    .put("historical_character_id",scope.historicalCharacterId()).put("scope_name",scope.scopeName()).put("begin_line",scope.beginLine())
                    .put("pass_line",scope.passLine()).put("end_line",scope.endLine()).put("byte_start",Long.toString(scope.byteStart()))
                    .put("byte_end",Long.toString(scope.byteEnd())).put("block_sha256",scope.blockSha256()));
            n.set("proof",proof);
        }else n.put("kind",decision instanceof ObserveOnly?"observe_only":"automatic_shared_policy");
        return DriverJson.object(StrictJson.canonical(n,65536),65536);
    }
    static Decision decodeDecision(OpportunityJson.Obj input) {
        JsonNode raw=DriverJson.toNode(input);String kind=StrictJson.text(raw.get("kind"));
        ObjectNode n=StrictJson.object(raw,kind.equals("select_displayed_option")?Set.of("schema","kind","implementation_source","event_instance_id","option_number","proof"):Set.of("schema","kind","implementation_source"));
        StrictJson.require(StrictJson.text(n.get("schema")).equals("xar.java.fixture-startup-decision/v1"),"exact startup decision schema required");ExactRef source=ExactRef.fromJson(n.get("implementation_source"));
        return switch(kind) {
            case "automatic_shared_policy"->new AutomaticSharedPolicy(source);
            case "observe_only"->new ObserveOnly(source);
            case "select_displayed_option"->{
                ObjectNode p=StrictJson.object(n.get("proof"),Set.of("business_pass","actual_log","scopes"));
                StrictJson.require(p.get("business_pass").isBoolean()&&!p.get("business_pass").booleanValue()&&p.get("scopes").isArray(),"startup proof cannot claim product acceptance");
                var scopes=new ArrayList<ActorScope>();for(JsonNode item:p.get("scopes")) {
                    var s=StrictJson.object(item,Set.of("runtime_character_id","historical_character_id","scope_name","begin_line","pass_line","end_line","byte_start","byte_end","block_sha256"));
                    scopes.add(new ActorScope(Math.toIntExact(StrictJson.integer(s.get("runtime_character_id"),1,Integer.MAX_VALUE)),StrictJson.text(s.get("historical_character_id")),StrictJson.text(s.get("scope_name")),
                            Math.toIntExact(StrictJson.integer(s.get("begin_line"),1,Integer.MAX_VALUE)),Math.toIntExact(StrictJson.integer(s.get("pass_line"),1,Integer.MAX_VALUE)),Math.toIntExact(StrictJson.integer(s.get("end_line"),1,Integer.MAX_VALUE)),
                            decimal(s.get("byte_start"),true),decimal(s.get("byte_end"),false),StrictJson.text(s.get("block_sha256"))));
                }
                yield new SelectDisplayedOption(decimal(n.get("event_instance_id"),false),Math.toIntExact(StrictJson.integer(n.get("option_number"),1,Integer.MAX_VALUE)),new ScopeEvidence(ExactRef.fromJson(p.get("actual_log")),scopes,false),source);
            }
            default->throw new IllegalArgumentException("unsupported startup decision branch");
        };
    }
    private static long decimal(JsonNode node,boolean zero) {
        String value=StrictJson.text(node);StrictJson.require(value.matches(zero?"0|[1-9][0-9]*":"[1-9][0-9]*"),"canonical decimal identity/range string required");return Long.parseLong(value);
    }
}
