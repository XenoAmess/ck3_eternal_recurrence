package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.coa.NativeSourceObservation;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.LedgerFilesFixtureAccess;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;
import static org.junit.jupiter.api.Assertions.*;

/** Real immutable archive, original Native wire, domain producer and receipt consumers; software facts grant no live Root authority. */
public final class CoaSourceEffectsProductionTest {
    private static final Instant NOW=Instant.parse("2026-10-24T04:00:00Z");
    private static final String SOURCE="coa={}\r\n";
    @TempDir Path temporary;
    @FunctionalInterface public interface ProducedWork {void accept(Produced actual)throws IOException;}
    public record Produced(ActionReceipt receipt,ActionPorts.OutcomeArchive archive,CoaSourceEffects effects){
        public NativeSourceObservation observation(){return ((ActionState.NativeSourceCompleted)((ActionState.Settled)receipt.state()).settlement()).observation();}
        public ActionReceipt withObservation(NativeSourceObservation changed){var s=(ActionState.Settled)receipt.state();return new ActionReceipt(1,receipt.sequence(),receipt.command(),receipt.bodySha256(),new ActionState.Settled(s.attempt(),s.dispatch(),new ActionState.NativeSourceCompleted(changed)));}
        public ActionReceipt wrongClipboard(){var old=observation();ExactRef different=archive.preserveMaterial(sample("wrong source",NOW.plusSeconds(3)).encode());return withObservation(new NativeSourceObservation(old.operation(),old.commandBodySha256(),old.requestId(),old.outcome(),old.observedAt(),old.originalDispatch(),different,old.afterScope(),old.compatibleResult(),old.sourceOriginals()));}
        public ActionReceipt wrongScope(){var old=observation();ObjectNode pair=object(archive.loadMaterial(old.afterScope()));((ObjectNode)((ObjectNode)pair.get("after")).get("binding")).put("connection_generation",4);ExactRef changed=archive.preserveMaterial(raw(pair));return withObservation(new NativeSourceObservation(old.operation(),old.commandBodySha256(),old.requestId(),old.outcome(),old.observedAt(),old.originalDispatch(),old.independentClipboard(),changed,old.compatibleResult(),old.sourceOriginals()));}
    }
    /** Runs inside the one actual software writer scope. Other regression consumers may install the same deep replay callback. */
    public static void withProduced(Path directory,OperationKey operation,ProducedWork work)throws IOException{
        withProduced(directory,operation,false,work);
    }
    private static void withProduced(Path directory,OperationKey operation,boolean legacyProof,ProducedWork work)throws IOException{
        try(var fixture=new CoaSourceArchiveBoundaryTest.Fixture(directory,8*1024*1024)){
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);var materials=new CoaSourceMaterials(archive);var binding=new FrontendBinding(BigInteger.valueOf(3),4242);var origin=fixture.origin();
                var source=EncodedSource.encode(SOURCE,false);var material=materials.preserve(source,binding,origin,"software-coa-session",false);
                var expected=new CommandExpectation.Frontend(new FrontendExpectedPostcondition(origin.requireFrontend(),fixture.source,CoaUpload.EXPECTATION,List.of(new ExpectedBoolean(new FieldKey("independent_game_effect_proven"),false))));
                var arguments=operation.value().equals(PROBE_STEP)?CoaSourceMaterials.arguments(material,false):new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of());
                var command=new ActionCommand("coa-original-"+operation.value(),origin,fixture.source,"software-coa-session",operation,arguments,expected,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(60));
                var preparation=new CoaUpload.Preparation(fixture.pin,materials,(held,original)->fixture.writer.requireSession(held),()->same);
                var request=preparation.prepare(command);archive.preserveRequest(request);
                var guard=new GuardEvidence(origin,fixture.source,command.sessionId(),binding.connectionGeneration(),operation,origin.requireFrontend().nativeEvidence(),origin.requireFrontend().capabilityEvidence(),"software-source-observer",NOW,NOW.plusSeconds(60));
                var attempt=new ActionState.Attempt("coa-original-request",NOW,guard,request);
                ObjectNode token=operation.value().equals(PROBE_STEP)?CoaUploadProductionTest.nativeProbe(source,binding,false):CoaUploadProductionTest.nativeExport(binding,SOURCE);
                ObjectNode returned=empty().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",true);returned.set("result",token);
                var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(raw(token)),raw(returned),NativeWire.packet(raw(returned).bytes()),Optional.of(new NativeActionPort.OutboundPacket(attempt.requestId(),NativeWire.execute(attempt.requestId(),operation.value(),binding.nativeRevision(),request.additionalFields().bytes()))));archive.preserve(ack);
                ObjectNode hello=empty().put("type","hello").put("protocol_version",1).put("pid",4242).put("connection_generation",3).put("bridge_version","software-v1").put("expected_ck3_sha256",EXE_SHA256).put("game_adapter_id",ADAPTER_ID).put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(CoaUpload.capability(operation.value()));
                ExactRef helloRef=original(fixture.directory,"hello.native",NativeWire.packet(raw(hello).bytes()));
                var before=scope(fixture,binding,helloRef,2,legacyProof);var after=scope(fixture,binding,helloRef,4,legacyProof);var calls=new AtomicInteger();
                CoaSourceEffects.OriginalReader reader=(ref,max)->{if(!LedgerFilesFixtureAccess.read(Path.of(ref.path()),max).pin().reference().equals(ref))throw new IOException("software original identity changed");return Files.readAllBytes(Path.of(ref.path()));};
                var effects=new CoaSourceEffects(materials,archive,(c,a)->calls.getAndIncrement()%2==0?before:after,()->sample(SOURCE,NOW.plusSeconds(3)),reader,List.of(fixture.pin));
                var projected=effects.observe(command,attempt,ack);
                if(legacyProof){assertInstanceOf(ActionPorts.Pending.class,projected.result());assertTrue(projected.compatibleResult().isEmpty());return null;}
                assertInstanceOf(ActionPorts.NativeSourceObserved.class,projected.result());assertTrue(projected.compatibleResult().isPresent());
                var observation=((ActionPorts.NativeSourceObserved)projected.result()).observation();
                var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.NativeSourceCompleted(observation)));
                effects.replay(receipt,archive);work.accept(new Produced(receipt,archive,effects));return null;
            });
        }
    }
    private static CoaSourceEffects.Scope scope(CoaSourceArchiveBoundaryTest.Fixture f,Binding binding,ExactRef hello,int second,boolean legacyProof)throws IOException{
        ObjectNode route=empty().put("step","query-frontend-gui-route-v1").put("accepted",true).put("status","coat_of_arms_designer");
        ObjectNode packet=empty().put("type","command_result").put("protocol_version",1).put("request_id","independent-route-"+second).put("ok",true);packet.set("result",route);
        ExactRef nativeRef=original(f.directory,"route-"+second+".native",NativeWire.packet(raw(packet).bytes()));
        ExactRef epoch=original(f.directory,"epoch-"+second+".json",new byte[]{1,2,3});
        var witnesses=RootNativeSourceProofProducer.persistWitnesses(List.of(SharedSourceFiles.observe(Path.of(f.pin.path()))));
        var qualified=new NativeSourceProofDocument(f.source.machineId(),"software-coa-session",NOW.plusSeconds(second).toString(),NativeSourceProofDocument.Mode.MCP_STDIO,
                f.pin,f.pin,epoch.sha256(),epoch,f.pin,List.of(f.pin),witnesses);
        byte[] proofBytes=NativeSourceProofCodec.encode(qualified);
        assertEquals(qualified,NativeSourceProofCodec.decode(proofBytes));
        ObjectNode wire=object(new RawJson(proofBytes));
        assertTrue(wire.path("live_witnesses").get(0).path("native_file").path("file_id_decimal").isTextual());
        assertTrue(wire.path("live_witnesses").get(0).path("native_file").path("legacy_file_id_decimal").isTextual());
        if(legacyProof){wire.put("schema","xar.java-root-native-source-proof/v2");wire.remove("live_witnesses");proofBytes=raw(wire).bytes();}
        ExactRef proof=original(f.directory,"qualification-"+second+".json",proofBytes);return new CoaSourceEffects.Scope(binding,Optional.of(BigInteger.valueOf(second)),nativeRef,hello,proof,NOW.plusSeconds(second),NOW.plusSeconds(60),List.of(proof));
    }
    private static ExactRef original(Path directory,String name,byte[] bytes)throws IOException{Path file=directory.resolve(name);Files.write(file,bytes);return LedgerFilesFixtureAccess.read(file,2*1024*1024).pin().reference();}
    private static NativeCoaClipboard.Sample sample(String source,Instant time){byte[] unicode=(source+'\0').getBytes(StandardCharsets.UTF_16LE);return new NativeCoaClipboard.Sample(17,17,time,NativeCoaClipboard.Status.TEXT,Base64.getEncoder().encodeToString(unicode));}
    @Test void actualProducerPassesReceiptV5SerdeAndSameInstalledDeepReplayWithoutGameCredit()throws Exception{
        for(String operation:List.of(PROBE_STEP,EXPORT_STEP))withProduced(temporary.resolve(operation),new OperationKey(operation),actual->{
            var observed=actual.observation();assertEquals(observed,NativeSourceObservation.decode(observed.encode()));assertFalse(observed.visibleGameplayCredit());assertFalse(observed.gameDayCredit());assertFalse(observed.renderedTextureVerified());
            byte[] durable=ActionReceiptCodec.encodeReceipt(actual.receipt(),actual.archive());var restored=ActionReceiptCodec.decodeReceipt(durable,actual.archive());assertEquals(actual.receipt(),restored);actual.effects().replay(restored,actual.archive());
            assertTrue(restored.settled());assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,restored.outcome());assertFalse(restored.visibleGameplay());assertFalse(restored.eligibleAdvance());assertTrue(restored.applied().isEmpty());
        });
    }
    @Test void retainedThreeMaterialsCannotHideClipboardTamperingOrWrongCommandIdentity()throws Exception{
        withProduced(temporary.resolve("wrong-original"),new OperationKey(EXPORT_STEP),actual->{
            ActionReceipt changed=actual.wrongClipboard();assertThrows(RuntimeException.class,()->actual.effects().replay(changed,actual.archive()));
            assertThrows(RuntimeException.class,()->actual.effects().replay(actual.wrongScope(),actual.archive()));
            var n=object(new RawJson(actual.observation().encode()));n.put("request_id","other-instance");var different=NativeSourceObservation.decode(raw(n).bytes());assertThrows(RuntimeException.class,()->actual.effects().replay(actual.withObservation(different),actual.archive()));
            n=object(new RawJson(actual.observation().encode()));n.put("visible_gameplay_credit",true);ObjectNode rejected=n;assertThrows(RuntimeException.class,()->NativeSourceObservation.decode(raw(rejected).bytes()));
            ObjectNode original=object(new RawJson(actual.observation().encode()));
            for(String field:original.properties().stream().map(java.util.Map.Entry::getKey).toList()){
                ObjectNode missing=original.deepCopy();missing.remove(field);assertThrows(RuntimeException.class,()->NativeSourceObservation.decode(raw(missing).bytes()));
                ObjectNode nul=original.deepCopy();nul.putNull(field);assertThrows(RuntimeException.class,()->NativeSourceObservation.decode(raw(nul).bytes()));
            }
            var pending=actual.effects().observe(actual.receipt().command(),((ActionState.Settled)actual.receipt().state()).attempt(),new NativeActionPort.Unknown("coa-original-request","software ACK missing",new byte[]{1},Optional.empty()));assertInstanceOf(ActionPorts.Pending.class,pending.result());assertTrue(pending.compatibleResult().isEmpty());
        });
    }
    @Test void independentClipboardCodecRejectsMissingNullWrongTypesAndUnstableSequence(){
        var value=sample(SOURCE,NOW);assertEquals(value,NativeCoaClipboard.Sample.decode(value.encode()));
        var maximum=sample("a".repeat(V2_MAX_BYTES),NOW);assertEquals(V2_MAX_BYTES,NativeCoaClipboard.Sample.decode(maximum.encode()).source().orElseThrow().length());
        for(String field:List.of("schema","sequence_before","sequence_after","observed_at","status","unicode_base64","read_only")){
            ObjectNode missing=object(value.encode());missing.remove(field);assertThrows(RuntimeException.class,()->NativeCoaClipboard.Sample.decode(raw(missing)));
            ObjectNode nul=object(value.encode());nul.putNull(field);assertThrows(RuntimeException.class,()->NativeCoaClipboard.Sample.decode(raw(nul)));
        }
        ObjectNode bad=object(value.encode());bad.put("sequence_before",true);assertThrows(RuntimeException.class,()->NativeCoaClipboard.Sample.decode(raw(bad)));
        assertThrows(RuntimeException.class,()->new NativeCoaClipboard.Sample(1,2,NOW,NativeCoaClipboard.Status.TEXT,value.unicodeBase64()));
        assertThrows(RuntimeException.class,()->new NativeCoaClipboard.Sample(1,1,NOW,NativeCoaClipboard.Status.TEXT,Base64.getEncoder().encodeToString(new byte[]{65,0})));
        assertTrue(new NativeCoaClipboard.Sample(1,1,NOW,NativeCoaClipboard.Status.NO_UNICODE,"").source().isEmpty());
    }
    @Test void retainedV2ProofCannotBeUpgradedByMatchingCurrentSourceBytes()throws Exception{
        withProduced(temporary.resolve("legacy-v2"),new OperationKey(EXPORT_STEP),true,actual->{throw new AssertionError("v2 cannot produce source completion");});
    }
}
