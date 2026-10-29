package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Public boundary specimens exercise the actual summary/error branches; they grant no action or Game result. */
final class OriginalAutoDecimalPresentationTest {
    @Test void fullStructuredAutoSummaryRetainsExactOriginalDecimalTokens() {
        var original=raw("{\"status\":\"executed\",\"selected_step\":\"query-player-mercenary-context-v1\","
                +"\"plan\":{\"selected_step\":\"query-player-mercenary-context-v1\"},"
                +"\"result\":{\"step\":\"query-player-mercenary-context-v1\",\"accepted\":true,\"status\":\"completed\","
                +"\"backend_id\":\"native-headless\",\"read_only\":true,\"opaque\":[-0.0,1.0,1.2500e+2,1.25e2,1.0e1,9007199254740992.0],"
                +"\"player_mercenary_context\":{\"available\":true,\"read_only\":true,\"rows\":[]}}}");
        var result=OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN,new Arguments(Presence.MISSING,Optional.empty()),original);
        assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(McpJson.token(result.bytes(),"structuredContent"),RawJson.MAXIMUM_BYTES));
    }
    @Test void retainedOriginalTurnInBothSourceOwnedErrorBranchesKeepsTheActualRawDomain() {
        for(boolean persistence:new boolean[]{true,false}) {
            String branch=persistence?"\"result\":{\"step\":\"continue-as-reconciled-successor\",\"accepted\":true,\"status\":\"continued\",\"driver_state_persistence_diagnostic\":{\"status\":\"failed\"}}"
                    :"\"successor_ui_obligation_v1\":{\"status\":\"handoff_unverified\"}";
            var original=raw("{\"status\":\"observed\",\"plan\":null,\"opaque\":[-0.0,1.0,1.25e2,1.0e1,9007199254740992.0],"+branch+"}");
            var result=OriginalMcpPresenters.present(OriginalMcpPresenters.Entry.AUTO_TURN,new Arguments(Presence.MISSING,Optional.empty()),original);
            byte[] structured=McpJson.token(result.bytes(),"structuredContent");byte[] diagnostics=McpJson.token(structured,"diagnostics");
            byte[] retained=McpJson.token(diagnostics,persistence?"natural_succession_driver_state_persistence_v1":"successor_ui_obligation_v1");
            assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(McpJson.token(retained,"original_turn"),RawJson.MAXIMUM_BYTES));
        }
    }
    private static RawJson raw(String json){return new RawJson(json.getBytes(StandardCharsets.UTF_8));}
}
