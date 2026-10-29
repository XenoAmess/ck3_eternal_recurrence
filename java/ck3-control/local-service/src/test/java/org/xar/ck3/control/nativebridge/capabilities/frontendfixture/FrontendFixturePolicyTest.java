package org.xar.ck3.control.nativebridge.capabilities.frontendfixture;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed original policy boundary, distinct preparation/ACK/actual business proof stages. */
final class FrontendFixturePolicyTest {
    static ObjectNode policy(boolean scenario) {
        ObjectNode n=StrictJson.object();n.put("schema",scenario?"ck3-frontend-fixture-start-policy-v2":"ck3-frontend-fixture-start-policy-v1");n.put("schema_version",scenario?2:1);
        n.putObject("preparation").put("path",Path.of("external-preparation.json").toAbsolutePath().toString()).put("sha256","a".repeat(64));
        n.putObject("profile_input_sha256").put("dlc_load.json","b".repeat(64)).put("pdx_settings.txt","c".repeat(64)).put("mod/fixture.mod","d".repeat(64));
        n.putObject("post_start").put("government_key",scenario?"clan_government":"celestial_government").put("primary_title_tier_key",scenario?"empire":"hegemony").put("independent",true);
        n.putArray("required_log_markers").add("FIXTURE: qualified").add("FIXTURE: switched");n.putArray("forbidden_log_markers").add("FIXTURE: FAIL");
        if(scenario){n.put("profile_id",FrontendFixturePolicy.PROFILE_ID);n.set("frontend_target",FrontendFixturePolicy.SCENARIO_TARGET.toJson());n.putObject("startup_event_admission").put("mode","observe_only").put("event_definition_key",FrontendFixturePolicy.STARTUP_EVENT).put("option_count",2);}return n;
    }
    @Test void originalClosedPoliciesAndBindingsRoundtripWithoutDefaultOrAlias() {
        for(boolean scenario:new boolean[]{false,true}) {
            ObjectNode raw=policy(scenario);var parsed=FrontendFixturePolicy.fromJson(raw);assertEquals(raw,parsed.toJson());
            assertEquals(parsed,FrontendFixturePolicy.fromJson(StrictJson.parse(StrictJson.canonical(raw,1<<20),1<<20)));
            var binding=parsed.binding("e".repeat(64));assertEquals(binding,FrontendFixturePolicy.Binding.fromJson(binding.toJson()));
            assertEquals(scenario?FrontendFixturePolicy.Kind.SCENARIO:FrontendFixturePolicy.Kind.ROBERT,parsed.kind());
        }
    }
    @Test void missingFieldsBooleanVersionInvalidProfileUnknownTargetOrObserveModeFail() {
        for(String key:new String[]{"schema","schema_version","preparation","profile_input_sha256","post_start","required_log_markers","forbidden_log_markers"}) {
            ObjectNode raw=policy(false);raw.remove(key);assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(raw));
        }
        ObjectNode bool=policy(false);bool.put("schema_version",true);assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(bool));
        ObjectNode profile=policy(true);profile.put("profile_id","other");assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(profile));
        ObjectNode target=policy(true);((ObjectNode)target.get("frontend_target")).put("start_date_raw",51394920.0);assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(target));
        ObjectNode action=policy(true);((ObjectNode)action.get("startup_event_admission")).put("mode","choose_first");assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(action));
    }
    @Test void profileEscapeDuplicateMarkersWrongGovernmentAndUnboundedLiteralsFail() {
        for(String relative:new String[]{"../outside","mod/../../outside","C:/outside","mod\\outside"}) {
            ObjectNode raw=policy(false);((ObjectNode)raw.get("profile_input_sha256")).put(relative,"e".repeat(64));assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(raw));
        }
        ObjectNode repeated=policy(false);repeated.withArray("forbidden_log_markers").add("FIXTURE: qualified");assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(repeated));
        ObjectNode longMarker=policy(false);longMarker.withArray("required_log_markers").add("x".repeat(161));assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(longMarker));
        ObjectNode clan=policy(false);((ObjectNode)clan.get("post_start")).put("government_key","clan_government");assertThrows(IllegalArgumentException.class,()->FrontendFixturePolicy.fromJson(clan));
    }
}
