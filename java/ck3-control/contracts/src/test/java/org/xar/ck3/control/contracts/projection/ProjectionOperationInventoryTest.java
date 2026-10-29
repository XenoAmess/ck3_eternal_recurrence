package org.xar.ck3.control.contracts.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Full selected enum/wire contract only. A token never grants a domain port or native authority. */
class ProjectionOperationInventoryTest {
    @Test void everySelectedOperationHasOneExactWireToken() {
        Set<String> wires=new HashSet<>();
        for(ProjectionOperation operation:ProjectionOperation.values()) {
            assertTrue(wires.add(operation.wire()),"duplicate operation wire token");
            assertEquals(operation,ProjectionOperation.fromWire(operation.wire()));
            assertThrows(ProjectionProtocolException.class,()->ProjectionOperation.fromWire(operation.name()));
        }
        assertEquals(ProjectionOperation.values().length,wires.size());
    }

    @Test void newDomainOperationsAndCrownShareTheSingleClosedInventory() {
        assertEquals("governance-crown-choose",ProjectionOperation.GOVERNANCE_CROWN_CHOOSE.wire());
        assertEquals("military-holy-defender-observation",ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION.wire());
        assertEquals("military-route-geometry",ProjectionOperation.MILITARY_ROUTE_GEOMETRY.wire());
        assertEquals("campaign-arithmetic-evaluate",ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE.wire());
        for(String alias:List.of("MILITARY_ROUTE_GEOMETRY","military_route_geometry","military-route-geometry ",
                "military-holy-defender","campaign-arithmetic"))
            assertThrows(ProjectionProtocolException.class,()->ProjectionOperation.fromWire(alias));
    }

    @Test void completeInventorySurvivesActualRequestAndResultSerialization() {
        byte[] raw="{\"missing_vs_present\":[null,[],{}],\"file_id\":\"18446744073709551615\"}"
                .getBytes(StandardCharsets.UTF_8);
        for(ProjectionOperation operation:ProjectionOperation.values()) {
            ProjectionCall call=new ProjectionCall(new ProjectionCall.Identity("inventory:"+operation.wire(),operation),
                    ProjectionJson.object(raw,8192));
            ProjectionCall reloaded=ProjectionWire.decodeCall(ProjectionWire.encodeCall(call));
            assertEquals(call.identity(),reloaded.identity());
            assertArrayEquals(raw,reloaded.payload().bytes());
            ProjectionResult expected=new ProjectionResult.Succeeded(call.identity(),ProjectionJson.value(raw,8192));
            var result=assertInstanceOf(ProjectionResult.Succeeded.class,
                    ProjectionWire.decodeResult(ProjectionWire.encodeResult(expected)));
            assertEquals(call.identity(),result.identity());
            assertArrayEquals(raw,result.result().bytes());
        }
    }

    @Test void newTokensWithoutRealRegisteredPortsRemainUnavailable() {
        ProjectionDispatcher dispatcher=new ProjectionDispatcher(List.of());
        for(ProjectionOperation operation:List.of(ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION,
                ProjectionOperation.MILITARY_ROUTE_GEOMETRY,ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE)) {
            ProjectionCall call=new ProjectionCall(new ProjectionCall.Identity("unregistered",operation),
                    ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8),8192));
            ProjectionResult.Rejected result=assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatcher.dispatch(ProjectionWire.encodeCall(call)));
            assertEquals(Optional.of(call.identity()),result.identity());
            assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE,result.error().code());
            var reloaded=assertInstanceOf(ProjectionResult.Rejected.class,
                    ProjectionWire.decodeResult(ProjectionWire.encodeResult(result)));
            assertEquals(result,reloaded);
        }
    }
}
