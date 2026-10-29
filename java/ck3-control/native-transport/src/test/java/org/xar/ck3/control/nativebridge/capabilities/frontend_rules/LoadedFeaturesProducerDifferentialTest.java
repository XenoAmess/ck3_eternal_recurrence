package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.LoadedFeaturesData.*;

/** Cross-language producer/consumer, full registry and unavailable/null regression. Never reports a skipped producer as PASS. */
final class LoadedFeaturesProducerDifferentialTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String PRODUCER = """
        import json, pathlib, sys
        root = pathlib.Path(sys.argv[1]).resolve()
        sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
        from xar_autoplayer.bridge import loaded_feature_manifest_contract as c
        cases = []
        for build in (c.CK3_11906, c.CK3_12002, c.CK3_12003, c.CK3_12004):
            for available in (True, False):
                reason = None if available else 'state_changed'
                frame = {'schema':'loaded-feature-manifest-v1','schema_version':1,
                    'status':'available' if available else 'unavailable','snapshot_revision':31,'date_raw':53182016,
                    'unavailable_reason':reason,'build':{'version':build.game_version,'exe_sha256':build.executable_sha256},
                    'effective_feature_flags':{'status':'available' if available else 'unavailable','unavailable_reason':reason,
                        'native_count':44 if available else None,'items':[
                            {'native_index':i,'cstring_id':v[0],'key':v[1],'enabled':i%3==0}
                            for i,v in enumerate(c._FEATURE_DEFINITIONS_BY_BUILD[build.game_version])] if available else None},
                    'script_dlc_keys':{'status':'available' if available else 'unavailable','unavailable_reason':reason,
                        'enumerated_count':3 if available else None,'keys':['dlc_001','dlc_002','expansion_001'] if available else None},
                    'entitlements':{'status':'unavailable','unavailable_reason':'store_verdict_provenance_unclosed','items':None},
                    'readiness':{'effective_feature_flags_ready':available,'script_dlc_keys_ready':available,
                        'entitlements_ready':False,'same_frame_ready':available,'actionable_ready':available},
                    'provenance':c._PROVENANCE_BY_BUILD[build.game_version]}
                frame = c.normalize_loaded_feature_manifest_v1(frame, expected_date_raw=53182016, expected_snapshot_revision=31)
                cases.append({'step':c.QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,'accepted':True,
                    'status':frame['status'],'query_sequence':12,'snapshot_revision':31,'loaded_feature_manifest':frame})
        print(json.dumps({'cases':cases}, separators=(',',':')))
        """;
    private static ObjectNode originalProducer() throws IOException, InterruptedException {
        String configured = System.getProperty("xar.repository.root");
        assertNotNull(configured, "actual original producer must be configured"); assertFalse(configured.isBlank(), "xar.repository.root is mandatory"); Path root = Path.of(configured).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/loaded_feature_manifest_contract.py")));
        String python = System.getProperty("xar.python"); assertNotNull(python, "xar.python is mandatory"); assertFalse(python.isBlank(), "xar.python is mandatory");
        Process child = new ProcessBuilder(python, "-X", "utf8", "-c", PRODUCER, root.toString()).redirectErrorStream(true).start();
        try {
            assertTrue(child.waitFor(30, TimeUnit.SECONDS), "original loaded-feature producer timed out"); byte[] output = child.getInputStream().readNBytes(1024 * 1024);
            assertEquals(0, child.exitValue(), () -> new String(output, StandardCharsets.UTF_8)); return FrontendRulesCodec.object(new RawJson(output));
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static RawJson raw(JsonNode value) { try { return new RawJson(JSON.writeValueAsBytes(value)); } catch (IOException error) { throw new IllegalArgumentException(error); } }
    @Test void fullOriginalRegistryAndUnavailableNullsRoundTripAcrossEveryAdmittedBuild() throws Exception {
        ObjectNode original = originalProducer(); assertEquals(8, original.get("cases").size());
        for (JsonNode row : original.get("cases")) {
            JsonNode frame = row.get("loaded_feature_manifest"); Build build = Build.require(frame.get("build").get("version").textValue(), frame.get("build").get("exe_sha256").textValue());
            var decoded = LoadedFeaturesCodec.decode(raw(row), build, BigInteger.valueOf(31), 53182016); Manifest manifest = decoded.manifest();
            assertFalse(manifest.entitlementsProven()); assertFalse(manifest.readiness().entitlementsReady());
            assertEquals(decoded, LoadedFeaturesCodec.decode(new RawJson(raw(row).bytes()), build, BigInteger.valueOf(31), 53182016));
            if (frame.get("status").textValue().equals("available")) {
                var flags = assertInstanceOf(AvailableFlags.class, manifest.flags()); assertEquals(44, flags.items().size());
                assertEquals(build == Build.CK3_11906 ? "songs_of_the_realm" : "by_god_alone", flags.items().get(43).key());
                assertEquals(3, assertInstanceOf(AvailableScriptDlcs.class, manifest.scriptDlcKeys()).keys().size());
            } else {
                assertEquals(UnavailableReason.STATE_CHANGED, assertInstanceOf(UnavailableFlags.class, manifest.flags()).reason());
                assertEquals(UnavailableReason.STATE_CHANGED, assertInstanceOf(UnavailableScriptDlcs.class, manifest.scriptDlcKeys()).reason());
            }
        }
    }
    @Test void wrongFieldsBooleanRevisionAndProvenanceDriftCannotEnterTypedDomain() throws Exception {
        JsonNode valid = originalProducer().get("cases").get(0);
        ObjectNode boolRevision = valid.deepCopy(); boolRevision.put("snapshot_revision", true);
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(boolRevision), Build.CK3_11906, BigInteger.valueOf(31), 53182016));
        ObjectNode extra = valid.deepCopy(); ((ObjectNode) extra.get("loaded_feature_manifest")).put("alias", "available");
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(extra), Build.CK3_11906, BigInteger.valueOf(31), 53182016));
        ObjectNode missing = valid.deepCopy(); ((ObjectNode) missing.get("loaded_feature_manifest")).remove("entitlements");
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(missing), Build.CK3_11906, BigInteger.valueOf(31), 53182016));
        ObjectNode provenance = valid.deepCopy(); ((ObjectNode) provenance.get("loaded_feature_manifest").get("provenance")).put("feature_root_slot_rva", "0x0");
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(provenance), Build.CK3_11906, BigInteger.valueOf(31), 53182016));
        ObjectNode feature = valid.deepCopy(); ((ObjectNode) feature.get("loaded_feature_manifest").get("effective_feature_flags").get("items").get(0)).put("enabled", 1);
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(feature), Build.CK3_11906, BigInteger.valueOf(31), 53182016));
        assertThrows(IllegalArgumentException.class, () -> LoadedFeaturesCodec.decode(raw(valid), Build.CK3_12004, BigInteger.valueOf(31), 53182016));
    }
}
