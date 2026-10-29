package org.xar.ck3.control.wave3.runtime.timelineowner;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Assessment;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwner.Frame;
import org.xar.ck3.control.wave3.runtime.timelineowner.TimelineOwnerCodec.Operation;

/** Typed adapter of the existing pure domain functions into the single shared projection host. */
public final class TimelineOwnerProjectionPort implements ProjectionPort<TimelineOwnerProjectionPort.Input, Assessment> {
    public sealed interface Input permits Paired, Popup { }

    public record Paired(Operation operation, Frame previous, Frame refreshed) implements Input {
        public Paired {
            Objects.requireNonNull(operation); Objects.requireNonNull(previous); Objects.requireNonNull(refreshed);
            require(operation != Operation.POPUP_OWNER, "popup operation requires three actual frames");
        }
    }

    public record Popup(Frame previous, Frame refreshed, Frame settled) implements Input {
        public Popup { Objects.requireNonNull(previous); Objects.requireNonNull(refreshed); Objects.requireNonNull(settled); }
    }

    @Override public ProjectionOperation operation() { return ProjectionOperation.TIMELINE_OWNER_PROJECT; }

    @Override public Input decode(byte[] rawPayload) {
        JsonNode row = StrictJson.parse(rawPayload);
        require(row.isObject(), "timeline owner request object required");
        require(TimelineOwnerCodec.INPUT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "timeline owner schema differs");
        Operation operation = switch (StrictJson.text(row.get("operation"))) {
            case "change" -> Operation.CHANGE;
            case "pause_owner" -> Operation.PAUSE_OWNER;
            case "resume_owner" -> Operation.RESUME_OWNER;
            case "popup_owner" -> Operation.POPUP_OWNER;
            default -> throw new IllegalArgumentException("unknown timeline owner operation");
        };
        StrictJson.object(row, operation == Operation.POPUP_OWNER
                ? Set.of("schema", "operation", "previous", "refreshed", "settled")
                : Set.of("schema", "operation", "previous", "refreshed"));
        Frame previous = TimelineOwnerCodec.frame(row.get("previous"));
        Frame refreshed = TimelineOwnerCodec.frame(row.get("refreshed"));
        return operation == Operation.POPUP_OWNER
                ? new Popup(previous, refreshed, TimelineOwnerCodec.frame(row.get("settled")))
                : new Paired(operation, previous, refreshed);
    }

    @Override public Assessment project(Input input) {
        return switch (input) {
            case Popup popup -> TimelineOwner.popupOwner(popup.previous(), popup.refreshed(), popup.settled());
            case Paired paired -> switch (paired.operation()) {
                case CHANGE -> TimelineOwner.change(paired.previous(), paired.refreshed());
                case PAUSE_OWNER -> TimelineOwner.pauseOwner(paired.previous(), paired.refreshed());
                case RESUME_OWNER -> TimelineOwner.resumeOwner(paired.previous(), paired.refreshed());
                case POPUP_OWNER -> throw new IllegalStateException("validated paired operation became popup");
            };
        };
    }

    @Override public byte[] encode(Assessment result) { return TimelineOwnerCodec.encode(result); }
}
