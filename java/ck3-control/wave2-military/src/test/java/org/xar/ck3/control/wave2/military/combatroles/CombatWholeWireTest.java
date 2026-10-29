package org.xar.ck3.control.wave2.military.combatroles;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class CombatWholeWireTest {
    @TempDir Path directory;

    /** Deliberately incomplete parser carrier. It is never a native/golden input and must fail the domain codec. */
    private static ObjectNode parserCarrier() {
        ObjectNode root = StrictJson.object(); root.put("qualification", CombatWholeWire.QUALIFICATION);
        ObjectNode samples = root.putObject("samples");
        for (String name : CombatWholeWire.SCENE_NAMES) {
            ObjectNode row = samples.putObject(name);
            row.put("army_id", 11).put("current_soldiers", 20).put("maximum_soldiers", 40)
                    .put("ai_base_power_raw", 4_000_000).put("regiment_count", 1).put("scope_role", "player");
            row.putArray("war_ids"); row.putObject(CombatRolesCodec.MEMBER);
            row.putObject("current_army_flag31_inputs_v1"); row.putObject("current_post_admission_refresh_inputs_v1");
        }
        return root;
    }
    private static byte[] bytes(ObjectNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }

    @Test void parserFramingDoesNotGrantNativeOrDomainQualification() throws IOException {
        byte[] original = bytes(parserCarrier()); CombatWholeWire.Parsed parsed = CombatWholeWire.parse(original);
        assertEquals(14, parsed.scenes().size()); assertArrayEquals(original, parsed.originalBytes());
        assertThrows(UnsupportedOperationException.class, () -> parsed.scenes().clear());
        ObjectNode exposed = parsed.scenes().getFirst().originalWholeRow(); exposed.put("army_id", 99);
        assertEquals(11, parsed.scenes().getFirst().originalWholeRow().get("army_id").intValue());
        byte[] exposedBytes = parsed.originalBytes(); exposedBytes[0] = 0;
        assertArrayEquals(original, parsed.originalBytes());
        assertThrows(IllegalArgumentException.class, () -> CombatRolesCodec.decode(
                parsed.scenes().getFirst().originalWholeRow().get(CombatRolesCodec.MEMBER)));
    }
    @Test void exactFourteenNamesAndWholeRowsAreRequired() {
        ObjectNode wrong = parserCarrier(); ((ObjectNode) wrong.get("samples")).remove(CombatWholeWire.SCENE_NAMES.getFirst());
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.parse(bytes(wrong)));
        ObjectNode invented = parserCarrier(); ((ObjectNode) invented.get("samples")).set("invented", invented.get("samples").get(CombatWholeWire.SCENE_NAMES.getFirst()));
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.parse(bytes(invented)));
        ObjectNode leafOnly = parserCarrier();
        ((ObjectNode) leafOnly.get("samples").get(CombatWholeWire.SCENE_NAMES.getFirst())).remove("current_soldiers");
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.parse(bytes(leafOnly)));
    }
    @Test void originalRawTokensUtf8DuplicateAndTrailingInputAreNeverNormalizedAway() {
        String original = parserCarrier().toString();
        for (String token : new String[] {"11.0", "true", "\"11\"", "null"}) {
            byte[] altered = original.replace("\"army_id\":11", "\"army_id\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.parse(altered));
        }
        assertThrows(IOException.class, () -> CombatWholeWire.parse((original + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> CombatWholeWire.parse(original.replaceFirst("\\{", "{\"samples\":{},").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.parse(new byte[] {(byte) 0xc0, (byte) 0x80}));
    }
    @Test void referenceRejectsBoolFloatStringZeroMissingAndUnknownFields() throws IOException {
        Path source = directory.resolve("source.json").toAbsolutePath().normalize(); Files.writeString(source, "{}");
        String prefix = "{\"path\":" + quote(source.toString()) + ",\"sha256\":\"" + CombatWholeWire.sha256("{}".getBytes(StandardCharsets.UTF_8)) + "\",\"bytes\":";
        for (String size : new String[] {"true", "2.0", "\"2\"", "0", "-1", "16777217"}) {
            assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.reference((prefix + size + "}").getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.reference((prefix + "2,\"extra\":true}").getBytes(StandardCharsets.UTF_8)));
        CombatWholeWire.FileReference reference = CombatWholeWire.reference((prefix + "2}").getBytes(StandardCharsets.UTF_8));
        assertArrayEquals("{}".getBytes(StandardCharsets.UTF_8), CombatWholeWire.readPinned(reference, directory));
    }
    @Test void retainedReferenceRejectsActualByteDriftAndApprovedRootEscape() throws IOException {
        Path source = directory.resolve("source.json").toAbsolutePath().normalize(); byte[] original = "{}".getBytes(StandardCharsets.UTF_8);
        Files.write(source, original);
        CombatWholeWire.FileReference reference = new CombatWholeWire.FileReference(source, original.length, CombatWholeWire.sha256(original));
        Files.writeString(source, "[]");
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.readPinned(reference, directory));
        Files.write(source, original); Path other = Files.createDirectory(directory.resolve("other"));
        assertThrows(IllegalArgumentException.class, () -> CombatWholeWire.readPinned(reference, other));
    }
    private static String quote(String value) { return StrictJson.object().put("path", value).get("path").toString(); }
}
