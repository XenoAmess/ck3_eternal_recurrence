package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Final role fields of one observed native interaction context. This grants no action or answer credit. */
public sealed interface NativeInteractionRoles permits NativeInteractionRoles.LegacyWithoutRoles,
        NativeInteractionRoles.Observed, NativeInteractionRoles.Unavailable {
    String FIELD = "recipient_context_v1";
    Set<String> WIRE_FIELDS = Set.of("schema_version", "state", "actor_character_id",
            "recipient_character_id", "intermediary_character_id", "reason");

    record LegacyWithoutRoles() implements NativeInteractionRoles { }

    record Observed(NativeCharacterId actorCharacterId, NativeCharacterId recipientCharacterId,
            Optional<NativeCharacterId> intermediaryCharacterId) implements NativeInteractionRoles {
        public Observed {
            Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(recipientCharacterId);
            Objects.requireNonNull(intermediaryCharacterId);
        }
    }

    record Unavailable(Reason reason) implements NativeInteractionRoles {
        public Unavailable { Objects.requireNonNull(reason); }
    }

    enum Reason {
        LAYOUT_UNQUALIFIED("layout_unqualified"), CONTEXT_NOT_CONSTRUCTED("context_not_constructed"),
        IDENTITY_UNRESOLVED("identity_unresolved"), ROLES_CHANGED("roles_changed");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Reason exact(String value) {
            for (Reason reason : values()) if (reason.wire.equals(value)) return reason;
            throw new IllegalArgumentException("unknown native interaction role reason");
        }
    }

    /** Only an actually absent companion is legacy. A declared null or malformed version is rejected. */
    static NativeInteractionRoles fromOption(JsonNode option) {
        StrictJson.require(option != null && option.isObject(), "native interaction option object required");
        return option.has(FIELD) ? decode(option.get(FIELD)) : new LegacyWithoutRoles();
    }

    static NativeInteractionRoles decode(JsonNode raw) {
        ObjectNode value = StrictJson.object(raw, WIRE_FIELDS);
        StrictJson.integer(value.get("schema_version"), 1, 1);
        String state = StrictJson.text(value.get("state"));
        if (state.equals("observed")) {
            StrictJson.require(value.get("reason").isNull(), "observed context roles require null reason");
            return new Observed(NativeCharacterId.fromJson(value.get("actor_character_id")),
                    NativeCharacterId.fromJson(value.get("recipient_character_id")),
                    value.get("intermediary_character_id").isNull() ? Optional.empty()
                            : Optional.of(NativeCharacterId.fromJson(value.get("intermediary_character_id"))));
        }
        StrictJson.require(state.equals("unavailable"), "unknown native interaction roles state");
        for (String field : new String[] {"actor_character_id", "recipient_character_id", "intermediary_character_id"})
            StrictJson.require(value.get(field).isNull(), "unavailable context roles require explicit null identities");
        return new Unavailable(Reason.exact(StrictJson.text(value.get("reason"))));
    }

    static ObjectNode toJson(NativeInteractionRoles roles) {
        Objects.requireNonNull(roles);
        StrictJson.require(!(roles instanceof LegacyWithoutRoles), "legacy roles have no v1 companion");
        ObjectNode value = StrictJson.object().put("schema_version", 1);
        if (roles instanceof Observed observed) {
            value.put("state", "observed");
            value.set("actor_character_id", observed.actorCharacterId().toJson());
            value.set("recipient_character_id", observed.recipientCharacterId().toJson());
            if (observed.intermediaryCharacterId().isPresent())
                value.set("intermediary_character_id", observed.intermediaryCharacterId().orElseThrow().toJson());
            else value.putNull("intermediary_character_id");
            value.putNull("reason");
        } else {
            value.put("state", "unavailable");
            value.putNull("actor_character_id"); value.putNull("recipient_character_id");
            value.putNull("intermediary_character_id");
            value.put("reason", ((Unavailable) roles).reason().wire());
        }
        return value;
    }

    static void putOption(ObjectNode option, NativeInteractionRoles roles) {
        Objects.requireNonNull(option); Objects.requireNonNull(roles);
        if (roles instanceof LegacyWithoutRoles) option.remove(FIELD);
        else option.set(FIELD, toJson(roles));
    }

    static void requireSameProfile(NativeInteractionRoles first, NativeInteractionRoles second,
            NativeInteractionRoles third) {
        boolean legacy = Objects.requireNonNull(first) instanceof LegacyWithoutRoles;
        StrictJson.require((Objects.requireNonNull(second) instanceof LegacyWithoutRoles) == legacy
                && (Objects.requireNonNull(third) instanceof LegacyWithoutRoles) == legacy,
                "one query must retain the same explicit legacy or context-v1 profile for all options");
    }
}
