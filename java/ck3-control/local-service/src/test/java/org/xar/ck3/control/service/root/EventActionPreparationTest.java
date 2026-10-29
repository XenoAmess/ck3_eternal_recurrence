package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

final class EventActionPreparationTest {
    @Test void originalOneBasedChoicePreparesTheNativeStepWithoutExtraEventPayload() {
        var args=object("{\"selected_step\":\"select-event-option-3\",\"event_instance_id\":901,\"option_number\":3,\"native_option_index\":2,\"rendered_index\":0}");
        var command=command("select-event-option-3",args,NativeEventPostconditionPort.EVENT_SCHEMA,901);
        var nativeRequest=EventActionPreparation.prepare(command);
        assertEquals("select-event-option-3",nativeRequest.step());assertEquals(EventActionPreparation.EVENT_CAPABILITY,nativeRequest.requiredCapability().orElseThrow());
        assertEquals(new RawJson(new byte[]{'{','}'}),nativeRequest.additionalFields());
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("select-event-option-3",args.with("native_option_index",number(0)),NativeEventPostconditionPort.EVENT_SCHEMA,901)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("select-event-option-3",args.with("event_instance_id",number(902)),NativeEventPostconditionPort.EVENT_SCHEMA,901)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("select-event-option-3",args.with("rendered_index",new OpportunityJson.Bool(true)),NativeEventPostconditionPort.EVENT_SCHEMA,901)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.option(new OperationKey("select-event-option-03")));
    }
    @Test void sourceReviewedLeftReplyRejectsSchemaIdOnlyCaptureAndAbsentCapture() {
        int pending=-2130706399;
        var args=object("{\"selected_step\":\"reject-pending-character-interaction\",\"unhandled_interaction_fallback\":{\"schema\":\"xar.pending-interaction-left-reply/v1\",\"pending_interaction_id\":-2130706399}}");
        var command=command("reject-pending-character-interaction",args,NativeEventPostconditionPort.PENDING_SCHEMA,pending);
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command),
                "a schema/id token cannot replace the original source-qualified buttons, legality and full frame capture");
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("reject-pending-character-interaction",object("{\"selected_step\":\"reject-pending-character-interaction\"}"),NativeEventPostconditionPort.PENDING_SCHEMA,pending)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("reject-pending-character-interaction",args,"unrecognized-schema",pending)));
        assertThrows(IllegalArgumentException.class,()->EventActionPreparation.prepare(command("reject-pending-character-interaction",args,NativeEventPostconditionPort.PENDING_SCHEMA,-1)));
    }
    private static ActionCommand command(String step,OpportunityJson.Obj args,String schema,int instance) {
        var sourceRef=new ExactRef("synthetic-event-producer",1,"a".repeat(64));
        var identity=new ObservationIdentity("synthetic-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(707),BigInteger.valueOf(41),BigInteger.valueOf(24000)),"synthetic-event-frame",BigInteger.valueOf(7),"synthetic-episode"),1);
        var source=new G2Source(identity.machineId(),"2026-10-23T21:00:00Z","synthetic-test-build",sourceRef);
        var expected=new ExpectedPostcondition(1,identity,source,schema,List.of(new ExpectedInteger(new FieldKey("old_instance_id"),BigInteger.valueOf(instance))));
        return new ActionCommand("synthetic-event-action",identity,source,"synthetic-session",new OperationKey(step),args,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.parse("2026-10-23T21:01:00Z"));
    }
    private static OpportunityJson.Obj object(String json) { return OpportunityJson.object(OpportunityJson.parse(json.getBytes(java.nio.charset.StandardCharsets.UTF_8)),"synthetic native plan"); }
    private static OpportunityJson.IntegerValue number(int value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
}
