package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverPublicExecuteFailureRowProducer;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.OriginalPublicPlanningOracle;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.service.mcp.RootMcpPlanning;

/** Software policy -> actual shared EXECUTE wrapper -> actual SDK error serializer. It does not
 * construct a Managed Root, a private failure invocation, an action or a publication permission. */
final class RootPublicStepFailurePolicyTest {
    @Test void bothActuallyUnsupportedHireCommandsRetainEachOriginalCapabilityBranchAtTheSdkBoundary()throws Exception {
        for(String step:List.of("hire-mercenary-v1","hire-holy-order-v1")) for(int branch=0;branch<3;branch++) {
            String capabilities=switch(branch) {
                case 0->"{\"action_steps\":[\""+step+"\"],\"composite_action_steps\":[\""+step+"\"]}";
                case 1->"{\"action_steps\":[],\"composite_action_steps\":[\""+step+"\"]}";
                default->"{\"action_steps\":[],\"composite_action_steps\":[]}";
            };
            String expected=switch(branch) {
                // Exact original native_driver.py16179,11152,12878, in original dispatch order.
                case 0->"native Python bridge does not implement war step "+step;
                case 1->"native Python bridge does not implement composite step "+step;
                default->"native DLL does not implement gameplay step "+step;
            };
            var original=DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,
                    DriverJson.object(capabilities.getBytes(StandardCharsets.UTF_8),4096));
            assertEquals("UnsupportedStepError",original.pythonClass());assertEquals(expected,original.message());
            assertEquals("UnsupportedStepError: "+expected,original.recorded());
            var calls=new AtomicInteger();
            var bindings=new PublicBindings();
            new RootMcpPlanning(new RootMcpPlanning.Backend() {
                public RootMcpPlanning.Admission admission(){return new RootMcpPlanning.Admission(false,true,List.of());}
                public RawJson plan(PublicPlanningCodec.PlanRequest caller){throw new AssertionError("EXECUTE cannot enter PLAN");}
                public RawJson execute(PublicPlanningCodec.ExecuteRequest caller) {
                    calls.incrementAndGet();assertEquals(step,caller.step().value());
                    throw new PublicServiceFailure(PublicServiceFailure.Kind.exact(original.pythonClass()),original.message(),Optional.empty());
                }
            }).register(bindings,OriginalPublicPlanningOracle.bindingSource());
            bindings.freeze(Set.of(PublicMethod.EXECUTE_STEP));
            var actualBinding=bindings.lookup(PublicMethod.EXECUTE_STEP).orElseThrow();
            if (!(actualBinding instanceof PublicBindings.TypedBinding<?,?> typedBinding))throw new AssertionError("actual EXECUTE binding must retain its typed route");
            var directory=OriginalPublicPlanningOracle.directory("ck3_execute_step",typedBinding);
            String arguments="{\"step\":\""+step+"\",\"expected_revision\":\"0\"}";
            var failure=assertThrows(PublicMcpDirectory.ToolFailure.class,
                    ()->directory.invoke(OriginalPublicPlanningOracle.call("ck3_execute_step",arguments)));
            var typed=assertInstanceOf(PublicServiceFailure.class,failure.getCause());
            assertEquals(PublicServiceFailure.Kind.UNSUPPORTED_STEP,typed.kind());assertEquals(expected,failure.getMessage());
            var response=OriginalPublicPlanningOracle.rpc(directory,"ck3_execute_step",arguments);
            assertFalse(response.has("error"));var result=response.get("result");assertTrue(result.get("isError").booleanValue());
            assertFalse(result.has("structuredContent"));
            assertEquals("Error executing tool ck3_execute_step: "+expected,result.get("content").get(0).get("text").textValue());
            assertEquals(2,calls.get());
            assertThrows(PublicMcpDirectory.ToolFailure.class,()->directory.invoke(OriginalPublicPlanningOracle.call("ck3_execute_step",
                    arguments.replace("\"expected_revision\":\"0\"","\"expected_revision\":true"))));
            assertEquals(2,calls.get());
        }
    }
    @Test void theFiniteOriginalPolicyCannotClassifyUnmigratedStepsOrMalformedCapabilitiesAsOriginalFailures() {
        var empty=DriverJson.object("{\"action_steps\":[]}".getBytes(StandardCharsets.UTF_8),4096);
        for(String step:List.of("declare-war-v1","query-china-projects-v1","pause-map","assign-army-commander-v1-army-1-commander-2")) {
            assertFalse(DriverPublicExecuteFailureRowProducer.fixedUnsupportedHire(step));
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.unsupportedHireError(step,empty));
        }
        for(String malformed:List.of("{}","{\"action_steps\":null}","{\"action_steps\":true}","{\"action_steps\":[1]}",
                "{\"action_steps\":[],\"composite_action_steps\":false}")) {
            var actual=DriverJson.object(malformed.getBytes(StandardCharsets.UTF_8),4096);
            assertThrows(IllegalArgumentException.class,()->DriverPublicExecuteFailureRowProducer.unsupportedHireError("hire-mercenary-v1",actual));
        }
    }
}
