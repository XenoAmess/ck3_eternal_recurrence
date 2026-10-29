package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/** Identity/type/version ingress and legacy archive compatibility, without a native action. */
final class NativeInteractionRolesTest {
    @Test void signedGenerationAndExplicitAbsenceRoundTripWithoutInventingLegacyIdentities() {
        var observed = new NativeInteractionRoles.Observed(new NativeCharacterId(0),
                new NativeCharacterId(Integer.MIN_VALUE + 5), Optional.of(new NativeCharacterId(67108906)));
        assertEquals(observed, NativeInteractionRoles.decode(NativeInteractionRoles.toJson(observed)));
        var option = StrictJson.object(); NativeInteractionRoles.putOption(option, observed);
        assertEquals(observed, NativeInteractionRoles.fromOption(option));
        assertNotEquals(observed, new NativeInteractionRoles.Observed(new NativeCharacterId(0),
                new NativeCharacterId(Integer.MIN_VALUE + 5), Optional.of(new NativeCharacterId(42))));
        var legacy = new NativeInteractionRoles.LegacyWithoutRoles();
        NativeInteractionRoles.putOption(option, legacy);
        assertFalse(option.has(NativeInteractionRoles.FIELD));
        assertEquals(legacy, NativeInteractionRoles.fromOption(option));
        assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.toJson(legacy));
        var unavailable = new NativeInteractionRoles.Unavailable(NativeInteractionRoles.Reason.ROLES_CHANGED);
        assertEquals(unavailable, NativeInteractionRoles.decode(NativeInteractionRoles.toJson(unavailable)));
        assertThrows(IllegalArgumentException.class,
                () -> NativeInteractionRoles.requireSameProfile(observed, legacy, observed));
    }

    @Test void declaredCompanionsRejectMalformedTokensAndNeverDowngradeToLegacy() {
        for (String field : new String[] {"actor_character_id", "recipient_character_id", "intermediary_character_id"})
            for (String token : new String[] {"true", "1.0", "\"42\"", "-1", "2147483648", "-2147483649"}) {
                String text = valid().replace("\"" + field + "\":42", "\"" + field + "\":" + token);
                assertNotEquals(valid(), text);
                assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.decode(parse(text)), field + "=" + token);
            }
        ObjectNode valid = (ObjectNode) parse(valid());
        for (String field : NativeInteractionRoles.WIRE_FIELDS) {
            ObjectNode missing = valid.deepCopy(); missing.remove(field);
            assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.decode(missing), field);
        }
        for (JsonNode invalid : new JsonNode[] {parse("null"), parse("true"), parse("[]"),
                parse(valid().replace("\"schema_version\":1", "\"schema_version\":2")),
                parse(valid().replace("\"state\":\"observed\"", "\"state\":\"legacy\"")),
                parse(valid().replace("\"reason\":null", "\"reason\":\"roles_changed\""))}) {
            ObjectNode option = StrictJson.object(); option.set(NativeInteractionRoles.FIELD, invalid);
            assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.fromOption(option));
        }
        ObjectNode unknown = NativeInteractionRoles.toJson(new NativeInteractionRoles.Unavailable(
                NativeInteractionRoles.Reason.IDENTITY_UNRESOLVED));
        unknown.put("recipient_character_id", 0);
        assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.decode(unknown));
        ObjectNode nullActor = (ObjectNode) parse(valid()); nullActor.putNull("actor_character_id");
        assertThrows(IllegalArgumentException.class, () -> NativeInteractionRoles.decode(nullActor));
        ObjectNode noIntermediary = (ObjectNode) parse(valid()); noIntermediary.putNull("intermediary_character_id");
        assertEquals(Optional.empty(), ((NativeInteractionRoles.Observed) NativeInteractionRoles.decode(noIntermediary)).intermediaryCharacterId());
    }

    private static String valid() {
        return "{\"schema_version\":1,\"state\":\"observed\",\"actor_character_id\":42,\"recipient_character_id\":42,"
                + "\"intermediary_character_id\":42,\"reason\":null}";
    }
    private static JsonNode parse(String json) {
        return StrictJson.parse(json.getBytes(StandardCharsets.UTF_8), 65536);
    }
}
