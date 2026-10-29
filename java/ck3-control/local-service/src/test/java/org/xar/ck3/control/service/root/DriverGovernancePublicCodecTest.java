package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

final class DriverGovernancePublicCodecTest {
    private RawJson raw(String value) {return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    @Test void actualRequestContractRoundTripsWidthsAndOptionalPresence() {
        var q=DriverGovernancePublicCodec.council(raw("{\"expected_revision\":\"18446744073709551615\"}"));assertEquals(q,DriverGovernancePublicCodec.council(DriverGovernancePublicCodec.encode(q)));
        for(String optional:List.of("",",\"action_request_id\":null",",\"action_request_id\":\"original-id\"")) {
            var assign=DriverGovernancePublicCodec.assign(raw("{\"query\":{},\"candidate_character_id\":1,\"expected_revision\":\"1\""+optional+"}"));
            assertEquals(assign,DriverGovernancePublicCodec.assign(DriverGovernancePublicCodec.encode(assign)));
        }
        var enact=DriverGovernancePublicCodec.enact(raw("{\"readback\":{},\"law_key\":\"crown_authority_2\",\"budgets\":{\"gold\":\"9223372036854775807\"},\"action_id\":\"native-id\"}"));
        assertEquals(enact,DriverGovernancePublicCodec.enact(DriverGovernancePublicCodec.encode(enact)));
    }
    @Test void originalLawBudgetActionOrderCrossesTheSharedValueErrorBoundary() {
        String args="{\"readback\":{},\"law_key\":\"bad\",\"budgets\":{\"unknown\":-1},\"action_id\":\"\"}";
        var law=assertThrows(PublicServiceFailure.class,()->DriverGovernancePublicCodec.enact(raw(args)));assertEquals("ValueError",law.kind().pythonClassName());assertEquals("law_key must identify a crown-authority candidate",law.getMessage());
        String validLaw=args.replace("\"bad\"","\"crown_authority_2\"");var budget=assertThrows(PublicServiceFailure.class,()->DriverGovernancePublicCodec.enact(raw(validLaw)));assertEquals("budgets must contain supported nonnegative raw currency limits",budget.getMessage());
        var action=assertThrows(PublicServiceFailure.class,()->DriverGovernancePublicCodec.enact(raw(validLaw.replace("{\"unknown\":-1}","{}"))));assertEquals("action_id must be nonempty and fit the native request ID",action.getMessage());
    }
    @Test void wrongJsonKindsUnsafeNumbersAndNarrowIdsFailRepresentationAdmission() {
        for(String value:List.of("true","1.0","null","9007199254740992","\"01\""))assertThrows(IllegalArgumentException.class,()->DriverGovernancePublicCodec.revision(raw("{\"expected_revision\":"+value+"}")));
        assertThrows(IllegalArgumentException.class,()->DriverGovernancePublicCodec.assign(raw("{\"query\":{},\"candidate_character_id\":2147483648,\"expected_revision\":1}")));
    }
    @Test void actualCompleteSdkDescriptorConsumesTheSoleRevisionAndBudgetContract()throws Exception {
        var descriptors=RootOriginalPublicTestInputs.tools();
        for(String name:List.of("ck3_query_realm_law_final_terms_private_v1","ck3_query_realm_law_crown_action_private_v1","ck3_query_realm_law_crown_receipt_private_v1","ck3_query_government_runtime_adapter_private_v1")) {
            var input=raw(name.contains("receipt")?"{\"expected_revision\":\"18446744073709551615\",\"submitted_request_id\":\"native-id\"}":"{\"expected_revision\":\"18446744073709551615\"}");
            var descriptor=descriptors.stream().filter(value->value.name().equals(name)).findFirst().orElseThrow();
            descriptor.validateArguments(new org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments(org.xar.ck3.control.service.mcp.PublicMcpDirectory.Presence.VALUE,java.util.Optional.of(input)));
            if(name.contains("receipt"))assertEquals(input,DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.crownReceipt(input)));
            else assertEquals(input,DriverGovernancePublicCodec.encode(DriverGovernancePublicCodec.revision(input)));
        }
    }
}
