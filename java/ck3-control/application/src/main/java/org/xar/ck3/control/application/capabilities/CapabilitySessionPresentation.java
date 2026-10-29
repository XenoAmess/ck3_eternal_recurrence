package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Presentation of the actual session owner; no restore or episode authority is created here. */
public record CapabilitySessionPresentation(boolean driverStateRestored,Optional<String> driverStateError,
        Optional<RestoreKind> restoreKind,BindingState bindingState,Optional<String> coldCandidateRejection,
        Optional<String> episodeTransitionError,Optional<Path> queueDirectory,Optional<Path> driverStatePath) {
    public enum BindingState {
        UNBOUND, ACTIVE_NEW, ACTIVE_OPERATOR_REBIND, EPISODE_SEED_BLOCKED, PENDING_COLD_CANDIDATE,
        BINDING_EPISODE_SEED, ACTIVE_RESUMED, RELAUNCHING_EPISODE_SEED, ACTIVE_NATURAL_SUCCESSOR;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        public static BindingState decode(String wire) {
            return java.util.Arrays.stream(values()).filter(v -> v.wire().equals(wire)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown actual episode binding state"));
        }
    }
    public enum RestoreKind {
        NEW_EPISODE, OPERATOR_PLAYED_CHARACTER_REBIND, NEW_EPISODE_SEED, SAME_PID_HOT,
        MANAGED_RESTORE_CHECKPOINT_REBIND, MANAGED_HOT_RESTORE, COLD_CHECKPOINT, NATURAL_SUCCESSION;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
        public static RestoreKind decode(String wire) {
            return java.util.Arrays.stream(values()).filter(v -> v.wire().equals(wire)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown actual Driver restore kind"));
        }
    }
    public CapabilitySessionPresentation {
        Objects.requireNonNull(driverStateError);Objects.requireNonNull(restoreKind);Objects.requireNonNull(bindingState);
        Objects.requireNonNull(coldCandidateRejection);Objects.requireNonNull(episodeTransitionError);
        Objects.requireNonNull(queueDirectory);Objects.requireNonNull(driverStatePath);
        for (Optional<Path> path : java.util.List.of(queueDirectory,driverStatePath))
            path.ifPresent(p -> require(p.isAbsolute(),"actual absolute session path required"));
    }
    public static CapabilitySessionPresentation decode(Obj row) {
        require(row.members().keySet().equals(Set.of("driver_state_restored","driver_state_error","driver_state_restore_kind",
                "episode_binding_state","cold_candidate_rejection","episode_transition_error","queue_dir","driver_state_path")),"complete actual session presentation required");
        return new CapabilitySessionPresentation(bool(row.get("driver_state_restored"),"driver_state_restored"),optionalText(row,"driver_state_error"),
                optionalText(row,"driver_state_restore_kind").map(RestoreKind::decode),BindingState.decode(text(row.get("episode_binding_state"),"episode_binding_state")),
                optionalText(row,"cold_candidate_rejection"),optionalText(row,"episode_transition_error"),
                optionalText(row,"queue_dir").map(Path::of),optionalText(row,"driver_state_path").map(Path::of));
    }
    public Obj toJson(DynamicCapabilities.Configuration config,Optional<Obj> transition,boolean restoreCheckpoint) {
        Objects.requireNonNull(config);Objects.requireNonNull(transition);
        validateConfiguration(config);
        Map<String,Value> row=new LinkedHashMap<>(original().members());
        row.put("configured",new Bool(config.stateDir().isPresent()));row.put("restore_checkpoint",new Bool(restoreCheckpoint));
        row.put("episode_transition",transition.<Value>map(v -> v).orElse(Nil.INSTANCE));return new Obj(row);
    }
    public void validateConfiguration(DynamicCapabilities.Configuration config) {
        Objects.requireNonNull(config);
        require(config.stateDir().isPresent() == queueDirectory.isPresent() && queueDirectory.isPresent() == driverStatePath.isPresent(),
                "configured state directory and actual session owner paths disagree");
    }
    public Obj original() {
        Map<String,Value> row=new LinkedHashMap<>();row.put("driver_state_restored",new Bool(driverStateRestored));
        row.put("driver_state_error",nullable(driverStateError));row.put("driver_state_restore_kind",nullable(restoreKind.map(RestoreKind::wire)));
        row.put("episode_binding_state",new Text(bindingState.wire()));row.put("cold_candidate_rejection",nullable(coldCandidateRejection));
        row.put("episode_transition_error",nullable(episodeTransitionError));row.put("queue_dir",nullable(queueDirectory.map(Path::toString)));
        row.put("driver_state_path",nullable(driverStatePath.map(Path::toString)));return new Obj(row);
    }
    private static Optional<String> optionalText(Obj row,String field) {
        return row.get(field)==Nil.INSTANCE ? Optional.empty() : Optional.of(text(row.get(field),field));
    }
    private static Value nullable(Optional<String> value) { return value.<Value>map(Text::new).orElse(Nil.INSTANCE); }
}
