package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;

final class RootMcpAubOperationsTest {
    private static final String FIRST="aub_policy_treasury_only_pause_choice";
    private static final String LAST="aub_policy_treasury_first_continue_choice";
    @Test void originalFourPublicEntriesKeepSemanticKeysAndOptionalRevisionPresence() {
        assertInstanceOf(RootMcpAubReads.Missing.class,RootMcpAubOperations.query(arguments("{}")).revision());
        assertInstanceOf(RootMcpAubReads.NullValue.class,RootMcpAubOperations.confirmation(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"expected_revision\":null}")).revision());
        var selection=RootMcpAubOperations.selection(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"desired_key\":\""+LAST+"\",\"expected_revision\":0}"));
        assertEquals(new Select(PolicyKey.TREASURY_PAUSE,PolicyKey.TREASURY_FIRST_CONTINUE),selection.mutation());
        assertEquals(Optional.of(BigInteger.ZERO),selection.revision().expected());
        String maximum="\"18446744073709551615\"";
        assertEquals(Optional.of(new BigInteger("18446744073709551615")),RootMcpAubOperations.query(arguments("{\"expected_revision\":"+maximum+"}")).revision().expected());
        assertEquals(Optional.of(new BigInteger("18446744073709551615")),RootMcpAubOperations.selection(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"desired_key\":\""+LAST+"\",\"expected_revision\":"+maximum+"}")).revision().expected());
        assertEquals(Optional.of(new BigInteger("18446744073709551615")),RootMcpAubOperations.confirmation(arguments("{\"expected_selected_key\":\""+FIRST+"\",\"expected_revision\":"+maximum+"}")).revision().expected());
    }
    @Test void neitherTypedWrapperNorPublicJsonPermitsNativePointersOrUnsafeNumericRevision() {
        for(String value:new String[]{"true","1.0","-1","9007199254740992","\"01\"","\"18446744073709551616\"","\"+1\""})assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.query(arguments("{\"expected_revision\":"+value+"}")));
        for(String bad:new String[]{"{\"expected_selected_key\":null}","{\"expected_selected_key\":true}","{\"expected_selected_key\":\"unknown\"}","{\"expected_selected_key\":\""+FIRST+"\",\"target_child_path\":\"confirm\"}"})assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.confirmation(arguments(bad)));
        assertThrows(IllegalArgumentException.class,()->RootMcpAubOperations.selection(arguments("{\"expected_selected_key\":\""+FIRST+"\"}")));
    }
    private static PublicMcpDirectory.Arguments arguments(String json){return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(json.getBytes(StandardCharsets.UTF_8))));}
}
