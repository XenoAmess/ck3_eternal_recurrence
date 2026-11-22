package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual fixed IsShown observation; a false value is valid and grants no initialization credit. */
public record CurrentDesInitGuardSource(int characterId, boolean characterAlive, boolean nativeIsPlayer,
        boolean nativeDefinitionFound, boolean nativeShown, boolean scopeBound, boolean sampledTwice) {
    public CurrentDesInitGuardSource {
        StrictJson.require(characterId != -1, "Actual full packed actor required");
        StrictJson.require(characterAlive && nativeIsPlayer && nativeDefinitionFound && scopeBound && sampledTwice,
                "Complete native fixed-guard source required");
    }

    public static CurrentDesInitGuardSource decode(JsonNode value) throws IOException {
        try {
            var source = StrictJson.object(value, Set.of("schema", "guard_key", "character_id", "character_alive",
                    "native_is_player", "native_definition_found", "native_shown", "scope_bound", "sampled_twice"));
            CurrentDesInitGuard.identity(source, "schema", CurrentDesInitGuard.SOURCE_SCHEMA);
            CurrentDesInitGuard.identity(source, "guard_key", CurrentDesInitGuard.GUARD_KEY);
            return new CurrentDesInitGuardSource(CurrentDesInitGuard.i32(source.get("character_id")),
                    CurrentDesInitGuard.bool(source, "character_alive"), CurrentDesInitGuard.bool(source, "native_is_player"),
                    CurrentDesInitGuard.bool(source, "native_definition_found"), CurrentDesInitGuard.bool(source, "native_shown"),
                    CurrentDesInitGuard.bool(source, "scope_bound"), CurrentDesInitGuard.bool(source, "sampled_twice"));
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact DES init guard source DATA", invalid);
        }
    }

    public ObjectNode encode() {
        return StrictJson.object().put("schema", CurrentDesInitGuard.SOURCE_SCHEMA)
                .put("guard_key", CurrentDesInitGuard.GUARD_KEY).put("character_id", characterId)
                .put("character_alive", characterAlive).put("native_is_player", nativeIsPlayer)
                .put("native_definition_found", nativeDefinitionFound).put("native_shown", nativeShown)
                .put("scope_bound", scopeBound).put("sampled_twice", sampledTwice);
    }
}
