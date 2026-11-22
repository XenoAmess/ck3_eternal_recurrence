package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Full immutable query DATA. Constructors do not mint a Native lease or permission. */
public record CurrentRiteCreateSource(Phase phase, long sourceRiteId, int actorId,
        Optional<Draft> draft, Optional<Confirmation> confirmation) {
    public enum Phase {
        DRAFT("draft"), CONFIRMATION("confirmation");
        private final String wire;
        Phase(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        static Phase parse(String text) throws IOException {
            for (var value : values()) if (value.wire.equals(text)) return value;
            throw new IOException("Unknown Rite CREATE source phase");
        }
    }

    public record Draft(boolean isCreating, boolean nativeCanCreate, long pietyCostRaw, long pietyMissingRaw,
            boolean knownDynastic, boolean selectedDynastic, boolean createButtonFound, boolean createButtonVisible,
            boolean createButtonEnabled, boolean blockedByUnrelatedModal, boolean createAdmissible) {
        public Draft {
            if (createAdmissible) StrictJson.require(isCreating && nativeCanCreate && pietyMissingRaw <= 0
                    && knownDynastic && selectedDynastic && createButtonFound && createButtonVisible && createButtonEnabled
                    && !blockedByUnrelatedModal, "Admitted actual CREATE draft lacks native prerequisites");
        }
        ObjectNode encode() {
            return StrictJson.object().put("is_creating", isCreating).put("native_can_create", nativeCanCreate)
                    .put("piety_cost_raw", Long.toString(pietyCostRaw)).put("piety_missing_raw", Long.toString(pietyMissingRaw))
                    .put("known_dynastic", knownDynastic).put("selected_dynastic", selectedDynastic)
                    .put("create_button_found", createButtonFound).put("create_button_visible", createButtonVisible)
                    .put("create_button_enabled", createButtonEnabled).put("blocked_by_unrelated_modal", blockedByUnrelatedModal)
                    .put("create_admissible", createAdmissible);
        }
    }
    public record Confirmation(boolean modalFound, boolean nativeCanAccept, boolean acceptButtonVisible,
            boolean acceptButtonEnabled, boolean originalCreateBound, boolean acceptAdmissible) {
        public Confirmation {
            StrictJson.require(modalFound && originalCreateBound, "Complete actual CREATE confirmation and original claim required");
            if (acceptAdmissible) StrictJson.require(nativeCanAccept && acceptButtonVisible && acceptButtonEnabled,
                    "Admitted actual CREATE confirmation lacks native prerequisites");
        }
        ObjectNode encode() {
            return StrictJson.object().put("modal_found", modalFound).put("native_can_accept", nativeCanAccept)
                    .put("accept_button_visible", acceptButtonVisible).put("accept_button_enabled", acceptButtonEnabled)
                    .put("original_create_bound", originalCreateBound).put("accept_admissible", acceptAdmissible);
        }
    }

    public CurrentRiteCreateSource {
        Objects.requireNonNull(phase); Objects.requireNonNull(draft); Objects.requireNonNull(confirmation);
        CurrentRiteCreate.requireRiteId(sourceRiteId);
        StrictJson.require(actorId != -1, "Actual full packed actor required");
        StrictJson.require(phase == Phase.DRAFT ? draft.isPresent() && confirmation.isEmpty()
                : draft.isEmpty() && confirmation.isPresent(), "Rite CREATE source union differs");
    }
    public static CurrentRiteCreateSource decode(JsonNode value) throws IOException {
        try {
            var source = StrictJson.object(value, Set.of("schema", "phase", "source_rite_id", "actor_id", "draft", "confirmation"));
            CurrentRiteCreate.identity(source, "schema", CurrentRiteCreate.SOURCE_SCHEMA);
            Optional<Draft> draft = Optional.empty(); Optional<Confirmation> confirmation = Optional.empty();
            if (!source.get("draft").isNull()) {
                var d = StrictJson.object(source.get("draft"), Set.of("is_creating", "native_can_create", "piety_cost_raw", "piety_missing_raw",
                        "known_dynastic", "selected_dynastic", "create_button_found", "create_button_visible", "create_button_enabled",
                        "blocked_by_unrelated_modal", "create_admissible"));
                draft = Optional.of(new Draft(CurrentRiteCreate.bool(d, "is_creating"), CurrentRiteCreate.bool(d, "native_can_create"),
                        CurrentRiteCreate.signedRaw(d, "piety_cost_raw"), CurrentRiteCreate.signedRaw(d, "piety_missing_raw"),
                        CurrentRiteCreate.bool(d, "known_dynastic"), CurrentRiteCreate.bool(d, "selected_dynastic"),
                        CurrentRiteCreate.bool(d, "create_button_found"), CurrentRiteCreate.bool(d, "create_button_visible"),
                        CurrentRiteCreate.bool(d, "create_button_enabled"), CurrentRiteCreate.bool(d, "blocked_by_unrelated_modal"),
                        CurrentRiteCreate.bool(d, "create_admissible")));
            }
            if (!source.get("confirmation").isNull()) {
                var c = StrictJson.object(source.get("confirmation"), Set.of("modal_found", "native_can_accept", "accept_button_visible",
                        "accept_button_enabled", "original_create_bound", "accept_admissible"));
                confirmation = Optional.of(new Confirmation(CurrentRiteCreate.bool(c, "modal_found"), CurrentRiteCreate.bool(c, "native_can_accept"),
                        CurrentRiteCreate.bool(c, "accept_button_visible"), CurrentRiteCreate.bool(c, "accept_button_enabled"),
                        CurrentRiteCreate.bool(c, "original_create_bound"), CurrentRiteCreate.bool(c, "accept_admissible")));
            }
            return new CurrentRiteCreateSource(Phase.parse(NativeWire.text(source.get("phase"))),
                    CurrentRiteCreate.riteId(source.get("source_rite_id")), CurrentRiteCreate.i32(source.get("actor_id")), draft, confirmation);
        } catch (IllegalArgumentException | ArithmeticException invalid) {
            throw new IOException("Invalid exact Rite CREATE source DATA", invalid);
        }
    }
    public ObjectNode encode() {
        var source = StrictJson.object().put("schema", CurrentRiteCreate.SOURCE_SCHEMA).put("phase", phase.wire())
                .put("source_rite_id", sourceRiteId).put("actor_id", actorId);
        if (draft.isPresent()) source.set("draft", draft.orElseThrow().encode()); else source.putNull("draft");
        if (confirmation.isPresent()) source.set("confirmation", confirmation.orElseThrow().encode()); else source.putNull("confirmation");
        return source;
    }
}
