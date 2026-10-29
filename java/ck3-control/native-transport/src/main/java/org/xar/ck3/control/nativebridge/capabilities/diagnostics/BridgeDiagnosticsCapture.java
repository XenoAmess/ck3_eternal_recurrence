package org.xar.ck3.control.nativebridge.capabilities.diagnostics;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Pure DATA projection of original received packets; it does not observe, read from a pipe, or qualify a source. */
public final class BridgeDiagnosticsCapture {
    private BridgeDiagnosticsCapture() { }
    public static BridgeDiagnostics.Received capture(String pipeName,NativeGameTransport.TransportDiagnostics original,
            Optional<ObservedFrame> retainedSnapshot) throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(retainedSnapshot);
        Optional<Obj> hello=Optional.empty();
        if(original.originalHello().isPresent()) {
            var actual=original.originalHello().orElseThrow().original();
            NativeWire.Frame decoded=NativeWire.decode(actual.packet().value());
            StrictJson.require(decoded instanceof NativeWire.Hello,"original diagnostic HELLO packet required");
            var rebuilt=(NativeWire.Hello)decoded;
            StrictJson.require(rebuilt.pid()==actual.pid()&&rebuilt.connectionGeneration().equals(actual.connectionGeneration())
                    &&rebuilt.bridgeVersion().equals(actual.bridgeVersion())&&rebuilt.gameSha256().equals(actual.gameSha256())
                    &&rebuilt.adapterId().equals(actual.adapterId())&&rebuilt.adapterStatus().equals(actual.adapterStatus())
                    &&rebuilt.buildMatch()==actual.buildMatch()&&rebuilt.capabilities().equals(actual.capabilities()),"diagnostic HELLO differs from its original packet");
            StrictJson.require(original.session().isPresent()&&original.session().orElseThrow().game().pid()==actual.pid()
                    &&original.session().orElseThrow().connectionGeneration().equals(actual.connectionGeneration()),"diagnostic HELLO/session identity differs");
            hello=Optional.of(packet(actual.packet().value()));
        } else StrictJson.require(original.session().isEmpty(),"diagnostic session cannot exist without its actual HELLO");
        Optional<Obj> heartbeat=notice(original.latestHeartbeat(),NativeWire.NoticeKind.HEARTBEAT);
        Optional<Obj> pong=notice(original.latestPong(),NativeWire.NoticeKind.PONG);
        Optional<Obj> error=notice(original.latestError(),NativeWire.NoticeKind.ERROR);
        Optional<Obj> publish=notice(original.latestSnapshotDiagnostic(),NativeWire.NoticeKind.SNAPSHOT_PUBLISH_DIAGNOSTIC);
        Obj heartbeatValue=heartbeat.orElse(new Obj(java.util.Map.of()));
        var observers=new BridgeDiagnostics.PrivateObservers(optionalObject(heartbeatValue,"g2_truce_preview_entry_observer_v1"),
                optionalObject(heartbeatValue,"vfs_mount_lifecycle_observer_v1"),optionalObject(heartbeatValue,"physfs_mounted_data_observer_v1"));
        Optional<Obj> hint=Optional.empty();
        if(original.production().isPresent()) {
            var production=original.production().orElseThrow();StrictJson.require(production.session().equals(original.session()),"raw diagnostic lifetime differs from actual transport");
            if(production.lastReceivedSnapshot().isPresent()) {
                var raw=production.lastReceivedSnapshot().orElseThrow();raw.fields();
                StrictJson.require(original.session().filter(raw.session()::equals).isPresent(),"latest raw diagnostic snapshot crossed current session");
                Obj envelope=packet(raw.originalPacket().value());
                if(envelope.get("state") instanceof Obj state)hint=optionalObject(state,"top_exclusive_modal_choice_hint");
            }
        }
        if(retainedSnapshot.isPresent()) {
            ObservedFrame actual=retainedSnapshot.orElseThrow();StrictJson.require(original.session().filter(actual.session()::equals).isPresent(),"diagnostic retained raw snapshot crossed transport session");
            NativeWire.Frame decoded=NativeWire.decode(actual.originalPacket());StrictJson.require(decoded instanceof NativeWire.Snapshot,"diagnostic retained state requires its original native snapshot");
            var nativeFrame=(NativeWire.Snapshot)decoded;
            StrictJson.require(nativeFrame.snapshotId().equals(actual.snapshotId())&&nativeFrame.revision().equals(actual.nativeRevision())
                    &&Arrays.equals(nativeFrame.state().value(),actual.state().bytes()),"diagnostic modal hint raw source differs");
            // This optional accepted packet is checked only as its own source. A rejected newer raw packet above
            // owns the diagnostic modal hint, while semantic readiness retains its last accepted observation.
        }
        return new BridgeDiagnostics.Received(pipeName,original,hello,heartbeat,pong,error,publish,observers,hint,retainedSnapshot);
    }
    private static Optional<Obj> notice(Optional<NativeGameTransport.ReceivedNotice> received,NativeWire.NoticeKind expected) throws IOException {
        if(received.isEmpty())return Optional.empty();var actual=received.orElseThrow().original();
        NativeWire.Frame decoded=NativeWire.decode(actual.packet().value());
        StrictJson.require(decoded instanceof NativeWire.Notice,"original diagnostic notice packet required");
        var rebuilt=(NativeWire.Notice)decoded;
        StrictJson.require(actual.kind()==expected&&rebuilt.kind()==expected&&Arrays.equals(actual.payload().value(),rebuilt.payload().value()),"diagnostic notice role/payload differs from original");
        return Optional.of(DriverJson.object(actual.payload().value(),DriverJson.MAX_NATIVE_BYTES));
    }
    private static Obj packet(byte[] framed){return DriverJson.object(Arrays.copyOfRange(framed,4,framed.length),DriverJson.MAX_NATIVE_BYTES);}
    private static Optional<Obj> optionalObject(Obj value,String field){Value item=value.get(field);return item instanceof Obj object?Optional.of(object):Optional.empty();}
}
