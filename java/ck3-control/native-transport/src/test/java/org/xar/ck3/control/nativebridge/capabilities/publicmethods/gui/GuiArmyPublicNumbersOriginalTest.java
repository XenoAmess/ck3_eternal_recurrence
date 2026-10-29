package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual original Army tooltip normalizer -> sole public GUI codec -> persisted JSON readback. */
final class GuiArmyPublicNumbersOriginalTest {
    private static final BigInteger MAX = new BigInteger("18446744073709551615");

    @Test void actualOriginalTooltipEpochsAndGuiPointersKeepFullUnsignedPrecisionAndExplicitNulls() throws Exception {
        ObjectNode cases = originals();
        for (String name : List.of("query", "hover", "unavailable")) {
            ObjectNode original = (ObjectNode) cases.get(name);
            RawJson source = raw(original);
            RawJson encoded = GuiCodec.encodePublicOriginal(source);
            ObjectNode wire = (ObjectNode) StrictJson.parse(encoded.bytes());
            ObjectNode expected = original.deepCopy();
            for (String role : List.of("native_revision", "pump_epoch", "gui_context_address", "gui_owner_address")) {
                assertTrue(original.get(role).isIntegralNumber(), "original native integer " + role);
                expected.put(role, original.get(role).bigIntegerValue().toString());
            }
            ObjectNode tooltip = (ObjectNode) expected.get("army_tooltip");
            for (String role : List.of("action_owner_epoch", "later_owner_epoch")) {
                JsonNode actual = original.path("army_tooltip").get(role);
                if (!actual.isNull()) tooltip.put(role, actual.bigIntegerValue().toString());
            }
            assertEquals(expected, wire, "only declared actual native wide roles change representation: " + name);
            assertEquals(encoded, GuiCodec.encodePublicOriginal(new RawJson(encoded.bytes())), "persistent public JSON is idempotent");
            assertArrayEquals(source.bytes(), raw(original).bytes(), "native/original DATA is unchanged");
            assertTrue(wire.path("current_subject_id").isIntegralNumber(), "bounded public CUnit remains numeric");
            assertTrue(wire.path("tree").path("widget_count").isIntegralNumber());
            assertTrue(wire.path("army_tooltip").get("gui_update_epoch").isNull(), "no GUI refresh observation is invented");
        }
        assertEquals(MAX, cases.path("query").path("gui_context_address").bigIntegerValue());
        assertEquals(MAX, cases.path("query").path("army_tooltip").path("later_owner_epoch").bigIntegerValue());
        assertTrue(cases.path("hover").path("army_tooltip").get("later_owner_epoch").isNull());
        assertTrue(cases.path("unavailable").path("army_tooltip").get("action_owner_epoch").isNull());
    }

    @Test void actualWideRoleNamesRejectBooleanFloatOverflowAndNoncanonicalDecimal() throws Exception {
        ObjectNode original = (ObjectNode) originals().get("query");
        for (String role : List.of("gui_context_address", "gui_owner_address", "action_owner_epoch", "later_owner_epoch")) {
            for (String bad : List.of("true", "1.0", "-1", "18446744073709551616", "\"01\"", "\"+1\"")) {
                ObjectNode changed = original.deepCopy();
                ObjectNode owner = role.endsWith("_owner_epoch") ? (ObjectNode) changed.get("army_tooltip") : changed;
                owner.set(role, StrictJson.parse(bad.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> GuiCodec.encodePublicOriginal(raw(changed)), role + ":" + bad);
            }
        }
    }

    private static RawJson raw(ObjectNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode originals() throws Exception {
        Path root = required("xar.repository.root"), python = required("xar.python"); verify(root);
        String code = """
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(sys.argv[1])
sys.path[:0]=[str(root/'ck3_autonomous_player'/'tests'/'unit'),str(root/'ck3_autonomous_player'/'src')]
from test_ingame_ui_navigation_v1 import army_tooltip_result,HOVER_RECEIPT
from xar_autoplayer.bridge.ingame_ui_contract import normalize_ui_result
from xar_autoplayer.bridge.version_identity import CK3_12003
cases={}
for name,operation,phase in [('query','query','cache'),('hover','hover_army_tooltip','ack'),('unavailable','query','unavailable')]:
 raw=army_tooltip_result(operation,phase=phase)
 raw['gui_context_address']=2**64-1;raw['gui_owner_address']=2**53+1
 if phase!='unavailable':
  raw['army_tooltip']['action_owner_epoch']=2**64-2
  if operation=='query':raw['army_tooltip']['later_owner_epoch']=2**64-1
 cases[name]=normalize_ui_result(raw,operation=operation,kind='army',subject_id=0,native_revision=3,date_raw=53146848,
  actor_id=29829,expected_build=CK3_12003,army_tooltip_kind='supply_state',
  army_tooltip_receipt=None if operation=='hover_army_tooltip' else HOVER_RECEIPT)
print(json.dumps(cases,ensure_ascii=False,allow_nan=False))
""";
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", code, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        FutureTask<byte[]> output = new FutureTask<>(() -> process.getInputStream().readNBytes(65_537));
        FutureTask<byte[]> errors = new FutureTask<>(() -> process.getErrorStream().readNBytes(16_385));
        Thread.ofVirtual().start(output); Thread.ofVirtual().start(errors); process.getOutputStream().close();
        try {
            if (!process.waitFor(30, TimeUnit.SECONDS)) throw new IllegalStateException("original Army tooltip producer timed out");
            byte[] out = output.get(5, TimeUnit.SECONDS), err = errors.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || out.length > 65_536 || err.length > 16_384)
                throw new IllegalStateException("original Army tooltip producer failed: " + new String(err, StandardCharsets.UTF_8));
            verify(root); JsonNode node = StrictJson.parse(out); assertInstanceOf(ObjectNode.class, node); return (ObjectNode) node;
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); }
        }
    }
    private static Path required(String property) throws Exception {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException("required original producer property missing: " + property);
        Path path = Path.of(value); if (!path.isAbsolute()) throw new IllegalArgumentException("absolute original producer path required");
        return path.toRealPath();
    }
    private static void verify(Path root) throws Exception {
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py", "74608d05074a48e1139a17fea360e34cf65cb01144d0a9a0e1dcf4ca49065ed4"},
            {"ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py", "878f239b24591b30e4830403c6bc912688ebea8edfa55d20c970402bdc1ea847"}
        };
        for (String[] pin : pins) {
            Path source = root.resolve(pin[0]).toRealPath(); assertTrue(source.startsWith(root));
            String actual = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
            assertEquals(pin[1], actual, "actual original producer source drift");
        }
    }
}
