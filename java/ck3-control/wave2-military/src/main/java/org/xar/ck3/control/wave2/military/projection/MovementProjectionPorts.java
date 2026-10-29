package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryInputs;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Observation;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Projection;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.prestore.PrestoreCodec;
import org.xar.ck3.control.wave2.military.prestore.PrestoreDisembark;

/** Pure adapters for the existing host's one military catalog. No native or action authority. */
public final class MovementProjectionPorts {
    public static final int MAXIMUM_BYTES = 65_536;
    private MovementProjectionPorts() { }

    /** The military catalog owner includes this list once in its module-wide union. */
    public static List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new CountyEntry()), RegisteredProjection.of(new Movement()),
                RegisteredProjection.of(new Prestore()), RegisteredProjection.of(new DisembarkNormalize()),
                RegisteredProjection.of(new DisembarkProject()));
    }

    public static final class CountyEntry implements ProjectionPort<CountyEntryInputs, CountyEntryInputs> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_COUNTY_ENTRY_NORMALIZE; }
        @Override public CountyEntryInputs decode(byte[] raw) {
            ObjectNode node = StrictJson.object(StrictJson.parse(raw), Set.of("value", "current_soldiers"));
            int soldiers = (int) StrictJson.integer(node.get("current_soldiers"), 0, Integer.MAX_VALUE);
            return CountyEntryCodec.decode(node.get("value"), soldiers);
        }
        @Override public CountyEntryInputs project(CountyEntryInputs input) { return input; }
        @Override public byte[] encode(CountyEntryInputs result) { return CountyEntryCodec.encode(result); }
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
    }

    public static final class Movement implements ProjectionPort<Optional<CurrentMovement>, Optional<CurrentMovement>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_CURRENT_MOVEMENT_NORMALIZE; }
        @Override public Optional<CurrentMovement> decode(byte[] raw) {
            ObjectNode node = StrictJson.object(StrictJson.parse(raw), Set.of("value"));
            return CurrentMovementCodec.normalize(node.get("value"));
        }
        @Override public Optional<CurrentMovement> project(Optional<CurrentMovement> input) { return input; }
        @Override public byte[] encode(Optional<CurrentMovement> result) { return CurrentMovementCodec.encode(result); }
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
    }

    public static final class Prestore implements ProjectionPort<PrestoreDisembark.Input, PrestoreDisembark.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_PRESTORE_PROJECT; }
        @Override public PrestoreDisembark.Input decode(byte[] raw) { return PrestoreCodec.decode(raw); }
        @Override public PrestoreDisembark.Result project(PrestoreDisembark.Input input) { return PrestoreDisembark.project(input); }
        @Override public byte[] encode(PrestoreDisembark.Result result) { return PrestoreCodec.encode(result); }
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
    }

    public static final class DisembarkNormalize implements ProjectionPort<Observation, Observation> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_DISEMBARK_NORMALIZE; }
        @Override public Observation decode(byte[] raw) {
            EvidenceJson.ObjectValue node = EvidenceJson.object(EvidenceJson.parse(raw));
            node.exactFields(Set.of("value"));
            return DisembarkCodec.normalize(node.required("value"));
        }
        @Override public Observation project(Observation input) { return input; }
        @Override public byte[] encode(Observation result) { return DisembarkCodec.encodeObservation(result); }
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
    }

    public static final class DisembarkProject implements ProjectionPort<Projection, Projection> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_DISEMBARK_PROJECT; }
        @Override public Projection decode(byte[] raw) { return DisembarkCodec.decodeProjectionRequest(raw); }
        @Override public Projection project(Projection input) { return input; }
        @Override public byte[] encode(Projection result) { return DisembarkCodec.encodeProjection(result); }
        @Override public int inputMaximumBytes() { return MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return MAXIMUM_BYTES; }
    }
}
