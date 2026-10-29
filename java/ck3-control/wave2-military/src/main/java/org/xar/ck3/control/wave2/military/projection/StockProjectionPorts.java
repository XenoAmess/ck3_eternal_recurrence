package org.xar.ck3.control.wave2.military.projection;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterInput;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterProjection;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.UpdaterWriteProjection;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyCodec;
import org.xar.ck3.control.wave2.military.stocksupply.StockSupplyProjection;
import org.xar.ck3.control.wave2.military.stocksupply.NextFleetRate;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRisk;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffects;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSoldierEffectsCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CallbackSupplyRiskCodec;

/** Typed pure ports in the one resident host; no native, file or writer capabilities. */
public final class StockProjectionPorts {
    public record Operations(ProjectionOperation updaterWrites, ProjectionOperation stockSupply,
                             ProjectionOperation nextFleetRate, ProjectionOperation callbackSupplyRisk,
                             ProjectionOperation callbackSoldierEffects) {
        public Operations {
            java.util.Objects.requireNonNull(updaterWrites);
            java.util.Objects.requireNonNull(stockSupply);
            java.util.Objects.requireNonNull(nextFleetRate);
            java.util.Objects.requireNonNull(callbackSupplyRisk);
            java.util.Objects.requireNonNull(callbackSoldierEffects);
            if (java.util.Set.of(updaterWrites, stockSupply, nextFleetRate, callbackSupplyRisk, callbackSoldierEffects).size() != 5) {
                throw new IllegalArgumentException("five distinct stock projection operations required");
            }
        }
    }
    private StockProjectionPorts() { }
    public static List<RegisteredProjection> registrations(Operations operations) {
        java.util.Objects.requireNonNull(operations);
        return List.of(RegisteredProjection.of(new UpdaterPort(operations.updaterWrites())),
                RegisteredProjection.of(new StockPort(operations.stockSupply())),
                RegisteredProjection.of(new RatePort(operations.nextFleetRate())),
                RegisteredProjection.of(new RiskPort(operations.callbackSupplyRisk())),
                RegisteredProjection.of(new EffectsPort(operations.callbackSoldierEffects())));
    }
    private record UpdaterPort(ProjectionOperation operation) implements ProjectionPort<UpdaterInput, UpdaterProjection> {
        @Override public UpdaterInput decode(byte[] raw) { return UpdaterWriteCodec.decode(raw); }
        @Override public UpdaterProjection project(UpdaterInput input) { return UpdaterWriteProjection.project(input); }
        @Override public byte[] encode(UpdaterProjection output) {
            return StrictJson.canonical(UpdaterWriteCodec.encode(output), 65_536);
        }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
    private record StockPort(ProjectionOperation operation) implements ProjectionPort<StockSupplyProjection.Input, StockSupplyProjection.Result> {
        @Override public StockSupplyProjection.Input decode(byte[] raw) { return StockSupplyCodec.decode(raw); }
        @Override public StockSupplyProjection.Result project(StockSupplyProjection.Input input) { return StockSupplyProjection.project(input); }
        @Override public byte[] encode(StockSupplyProjection.Result output) {
            return StrictJson.canonical(StockSupplyCodec.encode(output), 65_536);
        }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
    private record RatePort(ProjectionOperation operation) implements ProjectionPort<NextFleetRate.Input, NextFleetRate.Result> {
        @Override public NextFleetRate.Input decode(byte[] raw) { return StockSupplyCodec.decodeRate(raw); }
        @Override public NextFleetRate.Result project(NextFleetRate.Input input) { return NextFleetRate.project(input); }
        @Override public byte[] encode(NextFleetRate.Result output) {
            return StrictJson.canonical(StockSupplyCodec.encodeRate(output), 65_536);
        }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
    private record RiskPort(ProjectionOperation operation) implements ProjectionPort<CallbackSupplyRisk.Input, CallbackSupplyRisk.Result> {
        @Override public CallbackSupplyRisk.Input decode(byte[] raw) { return CallbackSupplyRiskCodec.decode(raw); }
        @Override public CallbackSupplyRisk.Result project(CallbackSupplyRisk.Input input) { return CallbackSupplyRisk.project(input); }
        @Override public byte[] encode(CallbackSupplyRisk.Result output) {
            return StrictJson.canonical(CallbackSupplyRiskCodec.encode(output), 65_536);
        }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
    private record EffectsPort(ProjectionOperation operation) implements ProjectionPort<CallbackSoldierEffects.Input, CallbackSoldierEffects.Result> {
        @Override public CallbackSoldierEffects.Input decode(byte[] raw) { return CallbackSoldierEffectsCodec.decodeExternal(raw); }
        @Override public CallbackSoldierEffects.Result project(CallbackSoldierEffects.Input input) { return CallbackSoldierEffects.project(input); }
        @Override public byte[] encode(CallbackSoldierEffects.Result output) {
            return StrictJson.canonical(CallbackSoldierEffectsCodec.encode(output), 65_536);
        }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
}
