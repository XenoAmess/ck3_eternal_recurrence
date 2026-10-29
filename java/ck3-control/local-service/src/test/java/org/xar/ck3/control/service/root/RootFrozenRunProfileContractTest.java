package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;

final class RootFrozenRunProfileContractTest {
    @TempDir Path directory;
    private RootFrozenRunProfile.Request actual(RootFrozenRunProfile.ImportMode mode) {
        return new RootFrozenRunProfile.Request("source-contract-fixture",Instant.parse("2026-10-24T00:00:00Z"),Instant.parse("2026-10-25T00:00:00Z"),"request","session",
                new ExactRef(directory.resolve("environment.json").toString(),37,"a".repeat(64)),(mode instanceof RootFrozenRunProfile.DisabledFreshFixture||mode instanceof RootFrozenRunProfile.EnabledNativeCampaign)?RootFrozenRunProfile.LifecycleMode.NATIVE_CAMPAIGN:RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,false,mode);
    }
    @Test void strictWirePreservesTheExplicitFreshAndLegacyBranches() {
        for(var mode:List.of(new RootFrozenRunProfile.DisabledFreshRobert(),new RootFrozenRunProfile.DisabledFreshFixture(new ExactRef(directory.resolve("fixture-policy.json").toString(),37,"b".repeat(64))),new RootFrozenRunProfile.Enabled(directory),new RootFrozenRunProfile.EnabledNativeCampaign(directory))) {
            var original=actual(mode);assertEquals(original,RootFrozenRunProfile.decode(RootFrozenRunProfile.encode(original)));
        }
    }
    @Test void missingNullAndWrongScalarTypesNeverBecomeDisabledFresh() {
        String wire=new String(RootFrozenRunProfile.encode(actual(new RootFrozenRunProfile.Enabled(directory))),StandardCharsets.UTF_8);
        for(String invalid:List.of(wire.replace("\"ordinary_campaign_no_pact\":false","\"ordinary_campaign_no_pact\":0"),
                wire.replace("\"ordinary_campaign_no_pact\":false","\"ordinary_campaign_no_pact\":null"),
                wire.replace("\"kind\":\"ENABLED\"","\"kind\":\"unknown\""),
                wire.replace("\"bytes\":37","\"bytes\":37.0"),wire.replace("\"bytes\":37","\"bytes\":true"),
                wire.replace("\"schema\":","\"unrecognized\":1,\"schema\":")))
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode("{}".getBytes(StandardCharsets.UTF_8)));
    }
    @Test void fixtureModeRequiresAnExactExplicitPolicyWithoutRobertAlias() {
        var request=actual(new RootFrozenRunProfile.DisabledFreshFixture(new ExactRef(directory.resolve("fixture-policy.json").toString(),37,"b".repeat(64))));
        String wire=new String(RootFrozenRunProfile.encode(request),StandardCharsets.UTF_8);
        assertTrue(wire.contains("DISABLED_FRESH_FIXTURE"));
        for(String invalid:List.of(wire.replace("\"policy_source\":{","\"policy_source\":null,\"unrecognized\":{"),
                wire.replace("\"bytes\":37","\"bytes\":true"),wire.replace("\"kind\":\"DISABLED_FRESH_FIXTURE\"","\"kind\":\"DISABLED_FRESH_ROBERT\""),
                wire.replace("xar.java-original-driver-import-run-profile/v4","xar.java-original-driver-import-run-profile/v1"),wire.replace("xar.java-original-driver-import-run-profile/v4","xar.java-original-driver-import-run-profile/v2")))
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        assertFalse(java.util.Arrays.stream(RootFrozenRunProfile.FrozenRunProfile.class.getConstructors()).findAny().isPresent());
    }

    @Test void externalStartupCaseIsExplicitNullableSourceAndFixtureCannotClaimOrdinaryPact() {
        var policy=new ExactRef(directory.resolve("fixture-policy.json").toString(),37,"b".repeat(64));
        var contract=new ExactRef(directory.resolve("startup-case.json").toString(),41,"c".repeat(64));
        for(var optional:List.of(java.util.Optional.<ExactRef>empty(),java.util.Optional.of(contract))) {
            var request=actual(new RootFrozenRunProfile.DisabledFreshFixture(policy,optional));
            assertEquals(request,RootFrozenRunProfile.decode(RootFrozenRunProfile.encode(request)));
            var wire=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(RootFrozenRunProfile.encode(request));
            var mode=(com.fasterxml.jackson.databind.node.ObjectNode)wire.get("legacy_import");
            assertEquals(optional.isEmpty(),mode.get("startup_case_source").isNull());
            mode.remove("startup_case_source");reject(wire);
            for(var bad:List.of(com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.TextNode.valueOf("source"),org.xar.ck3.control.contracts.StrictJson.object().putArray("a"))) {
                wire=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(RootFrozenRunProfile.encode(request));
                ((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("legacy_import")).set("startup_case_source",bad);reject(wire);
            }
            wire=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(RootFrozenRunProfile.encode(request));wire.put("lifecycle","ordinary_campaign_succession");reject(wire);
            wire=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(RootFrozenRunProfile.encode(request));wire.put("ordinary_campaign_no_pact",true);reject(wire);
        }
    }
    @Test void explicitSavedNativeModeRoundTripsWithoutFreshFixtureAliasOrPact() {
        var value=actual(new RootFrozenRunProfile.EnabledNativeCampaign(directory));
        assertEquals(value,RootFrozenRunProfile.decode(RootFrozenRunProfile.encode(value)));
        var wire=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(RootFrozenRunProfile.encode(value));
        assertEquals("ENABLED_NATIVE_CAMPAIGN",wire.get("legacy_import").get("kind").textValue());
        for(String old:List.of("xar.java-original-driver-import-run-profile/v1","xar.java-original-driver-import-run-profile/v2","xar.java-original-driver-import-run-profile/v3")) {
            var changed=wire.deepCopy();changed.put("schema",old);reject(changed);
        }
        var changed=wire.deepCopy();changed.put("ordinary_campaign_no_pact",true);reject(changed);
        changed=wire.deepCopy();changed.put("lifecycle","rogue_one_life");reject(changed);
        changed=wire.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("legacy_import")).put("kind","ENABLED");reject(changed);
    }
    private static void reject(com.fasterxml.jackson.databind.node.ObjectNode wire) {
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.decode(org.xar.ck3.control.contracts.StrictJson.canonical(wire,65536)));
    }
}
