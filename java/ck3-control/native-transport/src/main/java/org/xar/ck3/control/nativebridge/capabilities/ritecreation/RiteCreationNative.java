package org.xar.ck3.control.nativebridge.capabilities.ritecreation;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.ritecreation.RiteCreationCodec;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.application.ritecreation.RiteCreationContract.*;
import static org.xar.ck3.control.application.ritecreation.RiteCreationCodec.*;

/** Concrete original single-step Native boundary. Actual Root guards qualify source; Native still decides owner/Can/token. */
public final class RiteCreationNative {
    public record Sources(ExactRef definition,ExactRef decoder,List<ExactRef> originalProducerClosure){
        public Sources{Objects.requireNonNull(definition);Objects.requireNonNull(decoder);originalProducerClosure=List.copyOf(originalProducerClosure);need(definition.bytes()>0&&decoder.bytes()>0&&!originalProducerClosure.isEmpty()&&originalProducerClosure.size()<=32&&originalProducerClosure.stream().allMatch(v->v.bytes()>0),"exact original Rite Native/source closure required");}}
    public record Selection(Complete captured,Frame frame,Query query,Instant deadline){
        public Selection{Objects.requireNonNull(captured);Objects.requireNonNull(frame);Objects.requireNonNull(query);Objects.requireNonNull(deadline);need(query.expectedRevision().equals(frame.publicRevision()),"Rite expected public revision is stale");}}
    private final NativeGameTransport transport;private final Sources sources;private final RootReadContractCatalog.Family<Selection,Result> previews;
    public RiteCreationNative(NativeGameTransport actualTransport,Sources actualSources){
        transport=Objects.requireNonNull(actualTransport);sources=Objects.requireNonNull(actualSources);
        previews=new RootReadContractCatalog.Family<>("original-rite-creation-preview/v1",Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAPABILITY),sources.definition(),sources.decoder(),RiteCreationNative::key,s->RiteCreation.PREVIEW.operationKey(),selection->new ReadContract<>(
                "original-rite-creation-preview-"+ActionCodec.sha256(key(selection).bytes()),RiteCreation.PREVIEW.operationKey(),Optional.of(CAPABILITY),CAPABILITY,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.definition(),
                (request,id)->{requireRequest(selection,request);return prepare(selection.frame(),NativeFields.preview(selection.query().source()));},receipt->decode(selection,receipt),receipt->decode(selection,receipt)));
    }
    public RootReadContractCatalog.Family<Selection,Result> previewFamily(){return previews;}
    public ReadContract<Result> issue(RootReadContractCatalog catalog,Selection selection){return catalog.issue(previews,selection);}
    public PlanningReadRequest request(Selection selection){var actual=selection.captured();return new PlanningReadRequest(actual.identity(),actual.source(),actual.sessionId(),RiteCreation.PREVIEW.operationKey(),obj(object(key(selection))),selection.deadline());}
    public Result decode(Selection selection,PlanningReadReceipt receipt){
        requireRequest(selection,receipt.request());need(receipt.original().nativeOk()&&receipt.requestId().equals(receipt.original().requestId()),"original Rite preview ACK unavailable");
        need(receipt.before().binding().observed().equals(selection.captured().identity())&&receipt.after().binding().observed().equals(selection.captured().identity())
                &&receipt.before().binding().connectionGeneration().equals(selection.frame().connectionGeneration())&&receipt.after().binding().connectionGeneration().equals(selection.frame().connectionGeneration()),"Rite preview crossed its original full guard frame");
        requireWire(receipt.original(),receipt.requestId(),selection.frame(),NativeFields.preview(selection.query().source()));
        return result(receipt.original().originalResultToken().orElseThrow(),selection.frame(),NativeFields.preview(selection.query().source()));
    }
    public NativeRequest prepare(Frame frame,NativeFields fields){
        try {requireHeld(frame);
            var request=new NativeRequest(STEP,Optional.of(CAPABILITY),raw(node(nativeFields(fields,frame))));NativeStepDiscriminator.requireRequest(fields.operation().operationKey(),fields.operation().kind(),request);return request;
        }catch(IOException unavailable){throw new UncheckedIOException("actual Rite held source/capability unavailable",unavailable);}
    }
    public void requireHeld(Frame frame)throws IOException {
        var hello=transport.originalHello();need(hello.pid()==frame.gamePid()&&hello.connectionGeneration().equals(frame.connectionGeneration())&&hello.gameSha256().equalsIgnoreCase(SHA)
                &&hello.adapterId().equals("ck3-1.20.0.4-msvc-x64")&&hello.buildMatch()&&hello.capabilities().contains(CAPABILITY),"exact actual .4 Rite candidate capability/owner unavailable");
        var held=transport.latestObservedSnapshot().orElseThrow(()->new IOException("actual Rite held snapshot unavailable"));need(held.nativeRevision().equals(frame.nativeRevision())&&held.snapshotId().equals(frame.snapshotId())&&held.session().connectionGeneration().equals(frame.connectionGeneration())&&held.session().game().pid()==frame.gamePid(),"Rite held Native frame drift");
        ObjectNode state=object(held.state());yes(get(state,"paused"));yes(get(state,"map_ready"));equal(get(state,"date_raw"),java.math.BigInteger.valueOf(frame.dateRaw()));ObjectNode player=object(get(state,"played_character"));yes(get(player,"alive"));equal(get(player,"character_id"),java.math.BigInteger.valueOf(frame.actor()));
    }
    public static void requireWire(NativeActionPort.AckReceived ack,String requestId,Frame frame,NativeFields fields){
        try {var outgoing=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(()->new IllegalArgumentException("original Rite outgoing packet absent")).originalPacket());
            need(outgoing.requestId().equals(requestId)&&ack.requestId().equals(requestId)&&outgoing.step().equals(STEP)&&outgoing.expectedRevision().equals(Optional.of(frame.nativeRevision())),"actual Rite outgoing request ID/native revision/step differs");
            need(object(new RawJson(outgoing.normalizedAdditionalFields().value())).equals(node(nativeFields(fields,frame))),"actual Rite outgoing finite selector/frame fields differ");
            var decoded=NativeWire.decode(ack.originalPacket());need(decoded instanceof NativeWire.CommandResult,"actual Rite original command_result packet required");var packet=(NativeWire.CommandResult)decoded;
            need(packet.nativeOk()&&packet.requestId().equals(requestId)&&packet.result().presence()==NativeWire.Presence.VALUE&&ack.nativeOk()
                    &&java.util.Arrays.equals(packet.payload().value(),ack.originalFrame().bytes())&&java.util.Arrays.equals(packet.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"Rite retained packet/token/custody differs");
        }catch(IOException unavailable){throw new UncheckedIOException("original Rite wire evidence unavailable",unavailable);}
    }
    public Optional<NativeActionPort.AckReceived> collect(String originalProtocolRequestId,Instant deadline)throws IOException,InterruptedException{return transport.collectOriginalOutcome(originalProtocolRequestId,deadline);}
    private static RawJson key(Selection selection){ObjectNode n=empty();n.set("frame",org.xar.ck3.control.application.ritecreation.RiteCreationState.frame(selection.frame()));n.put("expected_source_rite_id",selection.query().source().value()).put("captured_full_binding_sha256",selection.captured().fullBindingSha256());n.set("captured_original_evidence",selection.captured().originalEvidence().toJson());return raw(n);}
    private static void requireRequest(Selection selection,PlanningReadRequest request){need(request.operation().equals(RiteCreation.PREVIEW.operationKey())&&request.before().equals(selection.captured().identity())&&request.source().equals(selection.captured().source())&&request.sessionId().equals(selection.captured().sessionId())&&request.deadline().equals(selection.deadline())&&request.arguments().equals(obj(object(key(selection)))),"Rite preview request changed actual source/arguments");}
}
