package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** The actual worker projection decoder, without a measurement owner, body read or Native permit. */
final class ColdRestoreDriverLineageTest {
    @Test void exactWorkerProjectionRoundTrips() {
        var original=projection();
        var lineage=ColdRestoreDriverLineage.decode(original);
        assertEquals(2222,lineage.bridgePid());assertEquals(40526,lineage.episodeCharacterId());
        assertArrayEquals(StrictJson.canonical(original),StrictJson.canonical(lineage.toJson()));
        var wire=assertInstanceOf(ObjectNode.class,StrictJson.parse(StrictJson.canonical(original)));
        assertArrayEquals(StrictJson.canonical(original),
                StrictJson.canonical(ColdRestoreDriverLineage.decode(wire).toJson()));
        var returned=lineage.successionLifecycle();returned.put("source","changed-caller-copy");
        assertNotEquals(returned,lineage.successionLifecycle());
    }
    @Test void booleanPidIsRejected() {var value=projection();value.put("bridge_pid",true);assertThrows(IllegalArgumentException.class,()->ColdRestoreDriverLineage.decode(value));}
    @Test void floatEpisodeIsRejected() {var value=projection();value.put("episode_character_id",40526.0);assertThrows(IllegalArgumentException.class,()->ColdRestoreDriverLineage.decode(value));}
    @Test void missingLifecycleMemberIsRejected() {var value=projection();((ObjectNode)value.get("succession_lifecycle")).remove("xar_enabled");assertThrows(IllegalArgumentException.class,()->ColdRestoreDriverLineage.decode(value));}
    @Test void booleanXarSettingIsRejectedButOriginalTextSettingsRoundTrip() {
        var value=projection();((ObjectNode)value.get("succession_lifecycle")).put("xar_enabled",true);
        assertThrows(IllegalArgumentException.class,()->ColdRestoreDriverLineage.decode(value));
        for(String setting:java.util.List.of("xar_on","xar_off")) {
            ((ObjectNode)value.get("succession_lifecycle")).put("xar_enabled",setting);
            var wire=assertInstanceOf(ObjectNode.class,StrictJson.parse(StrictJson.canonical(value)));
            assertArrayEquals(StrictJson.canonical(value),
                    StrictJson.canonical(ColdRestoreDriverLineage.decode(wire).toJson()));
        }
    }
    private static ObjectNode projection() {
        var value=StrictJson.object();value.put("schema","xar.original-sdk-cold-restore-lineage/v1");value.put("format_version",2);
        value.put("bridge_pid",2222);value.put("episode_character_id",40526);value.put("episode_run_id","native-40526-1bec95182886");
        var lifecycle=value.putObject("succession_lifecycle");lifecycle.put("schema","xar.ck3.succession-lifecycle-binding/v1");
        lifecycle.put("lifecycle","ordinary_campaign_succession");lifecycle.putNull("xar_enabled");
        lifecycle.put("pact_contract","absent_by_verified_xar_mod_not_loaded");lifecycle.put("source","absent_by_verified_xar_mod_not_loaded");
        lifecycle.put("environment_sha256","d33bf569cbd5cd08659a4cf78cabf92c60642332c598c5ae0b3e1eb823514366");return value;
    }
}
