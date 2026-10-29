package org.xar.ck3.control.wave2.military.projection;

import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec;
import org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel;
import org.xar.ck3.control.wave2.military.armyselector.CurrentReplenishmentSelector;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferCodec;
import org.xar.ck3.control.wave2.military.armytransfer.DailyQueueTransferProjection;

/** The parent military catalog collects these existing domain producers. */
public final class ArmyProjectionPorts {
    private ArmyProjectionPorts() { }
    private record QueueValue(ArmyDailyQueueInputs value) { }

    public static List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new QueuePort()),
                RegisteredProjection.of(new TransferPort()), RegisteredProjection.of(new SelectorPort()));
    }

    private static final class QueuePort implements ProjectionPort<QueueValue, QueueValue> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_ARMY_DAILY_QUEUE_INPUTS; }
        @Override public int inputMaximumBytes() { return 65_546; }
        @Override public int outputMaximumBytes() { return 65_536; }
        @Override public QueueValue decode(byte[] raw) {
            // Ten-byte wrapper preserves 64KiB inner; strict nodes retain floating 1.0.
            var wrapper = StrictJson.object(StrictJson.parse(raw, inputMaximumBytes()), Set.of("value"));
            return new QueueValue(ArmyDailyQueueInputsCodec.decodeNullable(wrapper.get("value")));
        }
        @Override public QueueValue project(QueueValue input) { return input; }
        @Override public byte[] encode(QueueValue result) { return ArmyDailyQueueInputsCodec.encode(result.value()); }
    }

    private static final class TransferPort
            implements ProjectionPort<DailyQueueTransferCodec.Input, DailyQueueTransferProjection.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_DAILY_QUEUE_TRANSFER; }
        @Override public int inputMaximumBytes() { return DailyQueueTransferCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return DailyQueueTransferCodec.MAX_BYTES; }
        @Override public DailyQueueTransferCodec.Input decode(byte[] raw) { return DailyQueueTransferCodec.decode(raw); }
        @Override public DailyQueueTransferProjection.Result project(DailyQueueTransferCodec.Input input) {
            return DailyQueueTransferProjection.project(input.availability(), input.queueFamily());
        }
        @Override public byte[] encode(DailyQueueTransferProjection.Result result) { return DailyQueueTransferCodec.encode(result); }
    }

    private static final class SelectorPort
            implements ProjectionPort<ArmySelectorModel.Input, ArmySelectorModel.Selection> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_ARMY_SELECTOR; }
        @Override public int inputMaximumBytes() { return ArmySelectorCodec.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return ArmySelectorCodec.MAX_BYTES; }
        @Override public ArmySelectorModel.Input decode(byte[] raw) { return ArmySelectorCodec.decode(raw); }
        @Override public ArmySelectorModel.Selection project(ArmySelectorModel.Input input) {
            return CurrentReplenishmentSelector.select(input);
        }
        @Override public byte[] encode(ArmySelectorModel.Selection result) { return ArmySelectorCodec.encode(result); }
    }
}
