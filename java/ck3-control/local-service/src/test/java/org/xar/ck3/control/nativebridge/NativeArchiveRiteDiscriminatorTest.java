package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Physical cold DATA custody only: historical empty-basis guards and software packets grant no
 * Rite source/readiness, transport chronology, native submit, applied effect or gameplay credit.
 */
final class NativeArchiveRiteDiscriminatorTest {
    @TempDir Path root;
    private static RawJson fields(String selector){return new RawJson(StrictJson.canonical(StrictJson.object().put("operation",selector)));}
    private static GuardEvidence guard(GuardEvidence old,OperationKey logical) {
        return new GuardEvidence(old.origin(),old.source(),old.sessionId(),old.connectionGeneration(),logical,
                old.nativeEvidence(),old.capabilityEvidence(),"historical-rite-data-only",old.observedAt(),old.validUntil());
    }
    private static NativeActionPort.AckReceived ack(String id,byte[] outgoing) throws Exception {
        var body=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
        body.set("result",StrictJson.object().put("archived_data_only",true));
        byte[] packet=NativeWire.packet(StrictJson.canonical(body));var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        return new NativeActionPort.AckReceived(id,true,decoded.result().token().map(value->new RawJson(value.value())),
                new RawJson(decoded.payload().value()),packet,Optional.of(new NativeActionPort.OutboundPacket(id,outgoing)));
    }
    private static PlanningReadReceipt read(ActionWriterIntegrationFixture fixture,OperationKey logical,String nativeStep,RawJson additions,String nativeId) throws Exception {
        var old=fixture.lastNestedRead.get();var binding=guard(old.before().binding(),logical);
        String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(CommandOriginCodec.guard(binding))));
        var observed=new PlanningReadGuard(binding,old.before().readiness(),hash);
        var request=new PlanningReadRequest(binding.origin(),binding.source(),binding.sessionId(),logical,new OpportunityJson.Obj(Map.of()),binding.validUntil());
        byte[] outgoing=NativeWire.execute(nativeId,nativeStep,binding.origin().expectedRevision(),additions.bytes());
        return new PlanningReadReceipt(request,"historical-rite-custody-only/v1","rite-read-data",observed,observed,ack("rite-read-data",outgoing));
    }
    private static ActionReceipt action(ActionCommand base,GuardEvidence old,OperationKey logical,NativeRequest prepared,RawJson outgoingFields) throws Exception {
        var command=new ActionCommand(base.actionId(),base.origin(),base.source(),base.sessionId(),logical,base.arguments(),base.expectation(),base.claims(),base.deadline());
        var binding=guard(old,logical);String id="rite-action-data";
        var attempt=new ActionState.Attempt(id,binding.observedAt(),binding,prepared);
        byte[] outgoing=NativeWire.execute(id,prepared.step(),binding.origin().expectedRevision(),outgoingFields.bytes());
        return new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.AckReceived(attempt,ack(id,outgoing)));
    }
    private static NativeOutcomeArchive cold(ActionWriterIntegrationFixture fixture) throws Exception {
        return new NativeOutcomeArchive(fixture.archive.artifactStore(),fixture.writer);
    }
    @Test void previewLogicalReadAndPlainStepColdRoundtripKeepActualWireBytes() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("preview"),false)) {
            fixture.ready();byte[] ledger=fixture.ledgerBytes();int writes=fixture.nativeReadWrites();
            RiteCreation preview=RiteCreation.PREVIEW;
            var receipt=read(fixture,preview.operationKey(),preview.nativeStep(),fields(preview.wire()),"rite-read-data");
            ExactRef ref=fixture.archive.preserveRead(receipt);var restored=cold(fixture).loadRead(ref);
            assertEquals(receipt,restored);assertEquals(ref,cold(fixture).readReferenceOf(restored));
            var decoded=NativeWire.decodeExecuteRequest(restored.original().outbound().orElseThrow().originalPacket());
            assertEquals(preview.nativeStep(),decoded.step());assertNotEquals(preview.operationKey().value(),decoded.step());
            assertArrayEquals(receipt.original().outbound().orElseThrow().originalPacket(),restored.original().outbound().orElseThrow().originalPacket());
            var plain=read(fixture,new OperationKey("historical-plain-query"),"historical-plain-query",new RawJson("{}".getBytes(StandardCharsets.UTF_8)),"rite-read-data");
            assertEquals(plain,cold(fixture).loadRead(fixture.archive.preserveRead(plain)));
            assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(writes,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void allSevenWriteVariantsRetainSharedSelectorPreparedFieldsAndColdReceipt() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("writes"),false)) {
            var template=fixture.command("historical-rite-actions");var old=fixture.lastNestedRead.get().before().binding();
            byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();int count=0;
            for(RiteCreation variant:RiteCreation.values())if(variant.kind()==ExecutableStepBindings.Kind.ACTION) {
                RawJson additions=fields(variant.wire());var prepared=new NativeRequest(variant.nativeStep(),Optional.of(variant.capability()),additions);
                var receipt=action(template,old,variant.operationKey(),prepared,additions);
                ExactRef ref=fixture.archive.preserveReceipt(receipt);assertEquals(receipt,cold(fixture).loadReceipt(ref));
                assertEquals(ref,cold(fixture).receiptReferenceOf(receipt));count++;
                var changed=action(template,old,variant.operationKey(),prepared,fields(RiteCreation.PREVIEW.wire()));
                assertThrows(RuntimeException.class,()->fixture.archive.preserveReceipt(changed));
            }
            assertEquals(7,count);assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void readBareUnknownWrongSelectorCrossKindAndRequestIdRefuseBeforeArchivePublication() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("refusals"),false)) {
            fixture.ready();RiteCreation preview=RiteCreation.PREVIEW;byte[] ledger=fixture.ledgerBytes();
            var invalid=new PlanningReadReceipt[]{
                read(fixture,new OperationKey(preview.nativeStep()),preview.nativeStep(),fields(preview.wire()),"rite-read-data"),
                read(fixture,new OperationKey(preview.nativeStep()+":unknown"),preview.nativeStep(),fields("unknown"),"rite-read-data"),
                read(fixture,preview.operationKey(),preview.nativeStep(),fields(RiteCreation.CONFIRM_ONCE.wire()),"rite-read-data"),
                read(fixture,RiteCreation.CONFIRM_ONCE.operationKey(),preview.nativeStep(),fields(RiteCreation.CONFIRM_ONCE.wire()),"rite-read-data"),
                read(fixture,preview.operationKey(),"different-wire-step",fields(preview.wire()),"rite-read-data"),
                read(fixture,preview.operationKey(),preview.nativeStep(),fields(preview.wire()),"wrong-original-id")};
            for(var receipt:invalid) {
                long retained=fixture.archive.artifactStore().retainedNativeBytes();
                assertThrows(RuntimeException.class,()->fixture.archive.preserveRead(receipt));
                assertThrows(RuntimeException.class,()->fixture.archive.readReferenceOf(receipt));
                assertEquals(retained,fixture.archive.artifactStore().retainedNativeBytes());
            }
            assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void previewCannotEnterActionAndAlteredColdOutboundOriginalIsNotRepaired() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("cold-originals"),false)) {
            var template=fixture.command("historical-rite-reject");var old=fixture.lastNestedRead.get().before().binding();RiteCreation preview=RiteCreation.PREVIEW;
            var prepared=new NativeRequest(preview.nativeStep(),Optional.of(preview.capability()),fields(preview.wire()));
            var crossed=action(template,old,preview.operationKey(),prepared,prepared.additionalFields());
            assertThrows(RuntimeException.class,()->fixture.archive.preserveReceipt(crossed));
            var receipt=read(fixture,preview.operationKey(),preview.nativeStep(),fields(preview.wire()),"rite-read-data");ExactRef ref=fixture.archive.preserveRead(receipt);
            var row=StrictJson.parse(fixture.writer.locked(session->fixture.archive.readArtifact(session,ref,StrictJson.EXPLICIT_MAX_BYTES)));
            ExactRef dispatch=ExactRef.fromJson(row.get("original_ref"));
            var dispatchRow=StrictJson.parse(fixture.writer.locked(session->fixture.archive.readArtifact(session,dispatch,StrictJson.EXPLICIT_MAX_BYTES)));
            Path outgoing=Path.of(ExactRef.fromJson(dispatchRow.get("outbound_packet_ref")).path());byte[] damaged={9,8,7};Files.write(outgoing,damaged);
            byte[] ledger=fixture.ledgerBytes();int reads=fixture.nativeReadWrites();assertThrows(RuntimeException.class,()->cold(fixture).loadRead(ref));
            assertArrayEquals(damaged,Files.readAllBytes(outgoing));assertArrayEquals(ledger,fixture.ledgerBytes());assertEquals(reads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
}
