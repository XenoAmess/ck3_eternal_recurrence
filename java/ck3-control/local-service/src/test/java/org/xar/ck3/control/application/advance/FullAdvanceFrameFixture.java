package org.xar.ck3.control.application.advance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Test-only real software packet/transport/facts/assembler/guarded filesystem edges.
 * The returned complete frame is DATA; this fixture issues no action, Ready, permit or fake canonical receipt.
 */
public final class FullAdvanceFrameFixture implements AutoCloseable {
    public final ActionWriterIntegrationFixture actual;
    public final DriverObservationAssembler.Complete complete;
    public final AdvanceObservationPort.Frame frame;
    public final ActionCommand command;
    public FullAdvanceFrameFixture(Path directory)throws Exception {
        actual=new ActionWriterIntegrationFixture(directory,false);
        var original=actual.command("full-original-data-only");var ports=actual.physicalInputs();
        var before=ports.transport().currentSnapshot(Instant.now().plusSeconds(20));
        var value=DriverJson.toNode(DriverJson.object(before.state().bytes(),DriverJson.MAX_NATIVE_BYTES));
        StrictJson.require(value instanceof ObjectNode,"software original native state must remain an object");var state=(ObjectNode)value;
        var diagnostics=state.get("diagnostics");StrictJson.require(diagnostics instanceof ObjectNode,"software original native diagnostics missing");
        ((ObjectNode)diagnostics).put("software_original_full_material_padding","x".repeat(131072));
        var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1)
                .put("snapshot_id",before.snapshotId()+"-full-original").put("revision",before.nativeRevision().add(java.math.BigInteger.ONE));
        packet.set("state",state);actual.enqueueSoftwareNativePacket(NativeWire.packet(DriverJson.encodeNode(packet)));
        var observed=ports.transport().observe(Instant.now().plusSeconds(20));
        complete=actual.writer.locked(same->{
            var archive=actual.archive.withSession(same);var reference=archive.preserveNativeFrame(observed);
            var result=actual.driverAuthority().read(observed);
            StrictJson.require(result instanceof DriverObservationFacts.Known,"actual software Driver facts unavailable");
            var known=((DriverObservationFacts.Known)result).facts();
            var assembled=ports.observationAssembler().assemble(observed,known,reference);
            StrictJson.require(assembled instanceof DriverObservationAssembler.Complete,"actual full native/Driver frame incomplete");
            return (DriverObservationAssembler.Complete)assembled;
        });
        var push=new ObservationProvenance.Push(complete.identity().frame().snapshotId(),complete.identity().frame().identity().nativeRevision(),complete.originalEvidence());
        frame=new AdvanceObservationPort.Frame(complete.identity(),complete.source(),complete.sessionId(),complete.semantic(),push,complete.observedAt(),complete.originalEvidence());
        command=AdvancePrimitives.child(original,frame,"full-original-data-basis","pause-map",original.deadline());
        Objects.requireNonNull(command);StrictJson.require(actual.nativeActionWrites()==0,"DATA fixture cannot submit a native control");
    }
    @Override public void close()throws Exception{actual.close();}
}
