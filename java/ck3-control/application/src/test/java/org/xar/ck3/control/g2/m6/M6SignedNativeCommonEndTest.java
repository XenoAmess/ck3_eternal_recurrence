package org.xar.ck3.control.g2.m6;
import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.planning.sway.SwaySignedNativeCommonEndTest;

/** Actual raw retained-return leaf; copied tuple is software identity, never an applied Start. */
final class M6SignedNativeCommonEndTest {
    @Test void actualRawReturnedOwnersRetainNeutralEndForCanonicalCopiedTuple() throws Exception {
        List<String> failures=new ArrayList<>();int count=0;
        try(var stream=getClass().getResourceAsStream("/sway/m6-native-common-end.json")) {
            assertNotNull(stream);for(JsonNode packet:StrictJson.parse(stream.readAllBytes(),M6SourceProducer.MAX_BYTES)) {
                JsonNode raw=packet.path("result").get("sway_completion_termination");long fullInstance=raw.get("scheme_instance_id").longValue();
                var id=new G2M6Contracts.Identity("software-common-tuple",NativeCharacterId.fromJson(raw.get("actor_character_id")).value(),NativeCharacterId.fromJson(raw.get("target_character_id")).value(),fullInstance,(int)(fullInstance>>>24));
                try {JsonNode read=StrictJson.parse(SwaySignedNativeCommonEndTest.decode(packet,packet).normalized().bytes()),family=read.get("common_native_end");
                    JsonNode retained=M6CommonEndSources.retained(family,read,M6TerminalSourceComposition.identityJson(id));assertNotNull(retained);
                    assertFalse(retained.get("terminal_cause_observed").booleanValue());assertTrue(retained.get("native_terminal_state_observed").booleanValue());
                    assertEquals(family.get("records").get(0),retained.get("copied_common_native_end_record"));
                }catch(IllegalArgumentException failure){failures.add(id.actorCharacterId()+"/"+id.targetCharacterId()+": "+failure.getMessage());}
                count++;
            }
        }
        assertEquals(5,count);assertEquals(List.of(),failures,"retained leaf rejected actual raw owner and canonical copied original actor");
    }
}
