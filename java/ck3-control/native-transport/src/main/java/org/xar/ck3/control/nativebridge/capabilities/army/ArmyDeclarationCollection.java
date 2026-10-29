package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Data-only result of collecting one original UNKNOWN. No variant grants a Native action or read authority. */
public final class ArmyDeclarationCollection {
    public static final String SCHEMA = "ck3-declarable-war-result-collection-v1";
    private ArmyDeclarationCollection() { }
    public enum Status {
        PENDING("pending"), STALE("stale"), NATIVE_REJECTED("native-rejected"), AVAILABLE("available");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static Status fromWire(String wire) {
            for (Status value : values()) if (value.wire.equals(wire)) return value;
            throw new IllegalArgumentException("unknown original declaration collection status");
        }
    }
    public record Binding(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision, String episode,
            int dateRaw, boolean paused, boolean mapReady, int playerCharacterId, long bridgePid, BigInteger connectionGeneration) {
        public Binding {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(publicRevision); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(episode); Objects.requireNonNull(connectionGeneration);
            require(!snapshotId.isEmpty() && !episode.isEmpty() && publicRevision.signum() >= 0 && playerCharacterId != -1
                    && bridgePid > 0 && bridgePid <= 4294967295L, "complete current declaration collection binding required");
            UInt64.positive(nativeRevision); UInt64.positive(connectionGeneration);
        }
    }
    public record Scope(String requestId, Binding originalBinding, Binding currentBinding) {
        public Scope {
            Objects.requireNonNull(requestId); Objects.requireNonNull(originalBinding); Objects.requireNonNull(currentBinding);
            require(!requestId.isEmpty() && originalBinding.paused() && originalBinding.mapReady(), "original paused declaration scope required");
        }
        public boolean current() { return originalBinding.equals(currentBinding) && currentBinding.paused(); }
    }
    public sealed interface Result permits Pending, Stale, NativeRejected, Available {
        Scope scope(); Status status();
    }
    public record Pending(Scope scope) implements Result {
        public Pending { Objects.requireNonNull(scope); require(scope.current(), "changed original binding is stale"); }
        public Status status() { return Status.PENDING; }
    }
    public record Stale(Scope scope, Optional<RawJson> nativeResultFrame) implements Result {
        public Stale {
            Objects.requireNonNull(scope); Objects.requireNonNull(nativeResultFrame);
            require(!scope.current(), "stale requires a changed actual original binding");
            nativeResultFrame.ifPresent(frame -> ArmyDeclarationCollectionCodec.requireFrame(scope.requestId(), frame));
        }
        public Status status() { return Status.STALE; }
    }
    public record NativeRejected(Scope scope, RawJson nativeResultFrame) implements Result {
        public NativeRejected {
            Objects.requireNonNull(scope); Objects.requireNonNull(nativeResultFrame);
            require(scope.current(), "native rejection requires the unchanged current binding");
            require(!ArmyDeclarationCollectionCodec.requireFrame(scope.requestId(), nativeResultFrame), "native-rejected requires the original rejected frame");
        }
        public Status status() { return Status.NATIVE_REJECTED; }
    }
    public record Available(Scope scope, RawJson nativeResultFrame, ArmyWarReadCodec.Declarations declarations) implements Result {
        public Available {
            Objects.requireNonNull(scope); Objects.requireNonNull(nativeResultFrame); Objects.requireNonNull(declarations);
            require(scope.current() && ArmyDeclarationCollectionCodec.requireFrame(scope.requestId(), nativeResultFrame), "available requires the actual same-frame successful result");
            ArmyDeclarationCollectionCodec.requireDeclarations(scope, nativeResultFrame, declarations);
        }
        public Status status() { return Status.AVAILABLE; }
    }
    /** The actual current complete projection is retained even for an unpaused stale result. */
    public record Reply(Complete current, Instant deadline, Result result) {
        public Reply {
            Objects.requireNonNull(current); Objects.requireNonNull(deadline); Objects.requireNonNull(result);
            require(ArmyDeclarationCollectionCodec.binding(current).equals(result.scope().currentBinding()), "collection reply differs from the actual current complete source");
        }
        public Context context() { return new Context(current.identity(), current.source(), current.sessionId(), deadline); }
    }
    static RawJson originalFrame(NativeActionPort.AckReceived actual) { return actual.originalFrame(); }
}
