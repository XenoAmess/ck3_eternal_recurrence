package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.reconciliation.LateOutcome;

/** Original ACK DATA only: no independent status confirmation, source authority or permission to replay. */
public final class DateSentinelArmResult {
    public enum Disposition { ARMED,REJECTED_BEFORE_QUEUE,UNKNOWN }
    public record Assessment(Disposition disposition,Optional<LateOutcome.Status> status) {
        public Assessment {
            Objects.requireNonNull(disposition);Objects.requireNonNull(status);
            if(disposition==Disposition.ARMED&&(status.isEmpty()||status.orElseThrow().state()!=LateOutcome.State.ARMED))
                throw new IllegalArgumentException("ARMED assessment requires its original armed status");
        }
    }
    private DateSentinelArmResult(){ }
    public static Assessment decode(NativeActionPort.AckReceived original,String expectedArmStep)throws IOException {
        var arm=FullSnapshotClockControlResult.dateArmSpec(expectedArmStep);
        var decoded=FullSnapshotClockControlResult.correlatedAck(original,expectedArmStep);
        var envelope=NativeWire.object(NativeWire.parse(decoded.payload().value()));
        var row=NativeWire.object(NativeWire.parse(decoded.result().token().orElseThrow().value()));
        if(row.has("schema")){
            var rejected=FullSnapshotClockControlResult.decodeDateArmRejection(original,expectedArmStep);
            return new Assessment(rejected.disposition()==FullSnapshotClockControlResult.Disposition.REJECTED_BEFORE_QUEUE
                    ?Disposition.REJECTED_BEFORE_QUEUE:Disposition.UNKNOWN,Optional.empty());
        }
        try {
            keys(envelope,Set.of("type","protocol_version","request_id","ok","result"));
            keys(row,Set.of("step","accepted","status","tactical_daily_sentinel"));
            require(original.nativeOk()&&row.get("accepted").isBoolean()&&row.get("accepted").booleanValue()
                    &&"available".equals(NativeWire.text(row.get("status"))),"successful available sentinel result required");
            var status=AdvancePrimitives.acknowledgedSentinel(original,expectedArmStep);
            require(status.generation().decimal().matches("[1-9][0-9]*"),"Date ARM generation must be nonzero");
            require(status.startingDateRaw()==arm.startingDateRaw()&&status.targetDateRaw()==arm.targetDateRaw()
                    &&status.speed()==arm.speed()&&status.mode()==LateOutcome.Mode.TERMINAL_OR_SENTINEL
                    &&status.armyCount()==0&&status.combatCount()==0,"Date ARM original status differs from its canonical request");
            return new Assessment(status.state()==LateOutcome.State.ARMED?Disposition.ARMED:Disposition.UNKNOWN,Optional.of(status));
        }catch(IllegalArgumentException invalid){throw new IOException("invalid original Date ARM sentinel status",invalid);}
    }
    private static void keys(ObjectNode row,Set<String> expected)throws IOException {
        Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected),"closed Date ARM result fields differ");
    }
    private static void require(boolean condition,String reason)throws IOException {if(!condition)throw new IOException(reason);}
}
