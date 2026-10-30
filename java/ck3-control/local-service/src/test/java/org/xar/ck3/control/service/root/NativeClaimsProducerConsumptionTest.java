package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Real C++ command_result bytes through actual Java transport, installed reader and Root public route.
 * The fixed-id test permit preserves producer bytes. There is no physical pipe or Managed Root here.
 */
final class NativeClaimsProducerConsumptionTest {
    private static final String RESOURCE="native/m0-player-claims-v1-resume90/";
    private static final String REQUEST_ID="software-claims-route";
    private static final String CAPABILITY="game.command.query-player-claims-v1-IDS";
    private static final BigInteger REV=BigInteger.valueOf(73),DATE=BigInteger.valueOf(53288256);
    private static final String MACHINE="software-m0-claims";
    @TempDir Path temporary;

    @TestFactory Stream<DynamicTest> originalTwentyCommandResultsReachBusinessConsumers() throws Exception {
        JsonNode index=StrictJson.parse(readProducer("RESULT.json"));
        assertEquals(20,index.get("wires").size());
        var tests=new java.util.ArrayList<DynamicTest>();
        for(var entry:index.get("wires")) {
            String file=StrictJson.text(entry.get("path"));
            tests.add(DynamicTest.dynamicTest(Path.of(file).getFileName().toString(),()->consume(file)));
        }
        return tests.stream();
    }

    private void consume(String file) throws Exception {
        byte[] original=readProducer(file);var outer=StrictJson.parse(original);
        assertTrue(outer.get("ok").isBoolean());boolean nativeOk=outer.get("ok").booleanValue();
        JsonNode result=outer.get("result");
        int actor=nativeOk?Math.toIntExact(StrictJson.integer(result.path("player_claims").get("actor_character_id"),Integer.MIN_VALUE,Integer.MAX_VALUE)):-2147453819;
        List<Int32Id> titles=nativeOk?StreamSupport.ids(result.path("player_claims").get("title_ids")):List.of(new Int32Id(16777217));
        var selector=new InteractionTitleSelectorReads.ClaimsSelector(titles);
        var operation=InteractionTitleSelectorReads.operation(selector);
        assertEquals(selector,RootWarPublicStepProducts.titleSelector(operation).orElseThrow());
        assertEquals(RootWarPublicStepProducts.ReadKind.TITLE,RootWarPublicStepProducts.readKind(operation).orElseThrow());
        try(var rig=new Rig(Path.of(file).getFileName().toString(),actor,original,selector)) {
            var registry=new PublicBindings();
            RootTitleClaimsPublicProducts.register(registry,rig.helloRef,request->{
                assertEquals(selector,request.selector());assertEquals(BigInteger.valueOf(7),request.expectedRevision());
                try{return rig.invoke(request);}catch(IOException|InterruptedException failure){throw new IllegalStateException(failure);}
            });
            registry.freeze(Set.of(PublicMethod.QUERY_TITLE_OWN_LAWS_V1,PublicMethod.QUERY_PLAYER_CLAIMS_V1,
                    PublicMethod.QUERY_TITLE_HOLDER_V1,PublicMethod.QUERY_CURRENT_TITLE_APPOINTMENT_V1));
            var binding=registry.lookup(PublicMethod.QUERY_PLAYER_CLAIMS_V1).orElseThrow();
            var request=new TitleClaimsPublicCodec.Request(BigInteger.valueOf(7),selector);
            assertEquals(request,TitleClaimsPublicCodec.decode(InteractionTitleSelectorReads.Kind.CLAIMS,TitleClaimsPublicCodec.encode(request)));
            if(nativeOk) {
                var published=StrictJson.parse(binding.invoke(PublicBindings.present(TitleClaimsPublicCodec.encode(request))).bytes());
                assertEquals(actor,published.path("player_claims").get("actor_character_id").intValue());
                assertTrue(published.path("player_claims").get("actor_character_id").isIntegralNumber());
                assertEquals("73",published.get("snapshot_revision").textValue());
                assertEquals("73",published.path("player_claims").get("snapshot_revision").textValue());
                assertEquals("7",published.get("queried_revision").textValue());
                assertEquals(result.path("player_claims").get("claims"),published.path("player_claims").get("claims"));
                if(!result.path("player_claims").get("available").booleanValue()) {
                    assertTrue(published.path("player_claims").get("claims").isNull());
                    assertEquals("typed_mailbox_read_unavailable",published.path("player_claims").get("unavailable_reason").textValue());
                }
                assertEquals(1,rig.publications);
                assertEquals(rig.decoded,rig.contract.replay(rig.receipt));
            } else {
                assertThrows(IllegalStateException.class,()->binding.invoke(PublicBindings.present(TitleClaimsPublicCodec.encode(request))));
                assertEquals(0,rig.publications);assertNull(rig.receipt);
                assertFalse(rig.ack.nativeOk());
                assertEquals(outer.get("error"),StrictJson.parse(rig.ack.originalFrame().bytes()).get("error"));
            }
            assertArrayEquals(original,rig.ack.originalFrame().bytes());
            assertArrayEquals(NativeWire.packet(original),rig.ack.originalPacket());
            assertEquals(1,rig.port.writes);
            var repeated=rig.transport.read(rig.permit,rig.prepared,rig.context.deadline());
            assertInstanceOf(NativeActionPort.Unknown.class,repeated);
            assertEquals(1,rig.port.writes,"the original fixed request is never replayed");
            assertArrayEquals(original,readProducer(file));
        }
    }

    @Test void malformedPublicTitleSelectorsFailBeforeTheFinalReadPort() throws Exception {
        var registry=new PublicBindings();int[] reads={0};
        var source=new ExactRef("software-only-claims-source",1,"a".repeat(64));
        RootTitleClaimsPublicProducts.register(registry,source,request->{reads[0]++;throw new AssertionError("invalid selector reached a read");});
        var binding=registry.lookup(PublicMethod.QUERY_PLAYER_CLAIMS_V1).orElseThrow();
        for(String value:List.of("-1","2147483648","true","1.0","null","\"1\"")) {
            var arguments=new RawJson(("{\"expected_revision\":\"7\",\"title_ids\":["+value+"]}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(arguments)));
        }
        assertEquals(0,reads[0]);
    }

    private final class Rig implements AutoCloseable {
        final Replay port;final NativeGameTransport transport;final Context context;final ExactRef helloRef,nativeRef;
        final ReadContract<InteractionTitleSelectorReads.Decoded> contract;
        ReadPermit permit;NativeRequest prepared;NativeActionPort.AckReceived ack;
        PlanningReadReceipt receipt;InteractionTitleSelectorReads.Decoded decoded;int publications;
        Rig(String name,int actor,byte[] producer,InteractionTitleSelectorReads.ClaimsSelector selector) throws Exception {
            Instant now=Instant.now(),deadline=now.plusSeconds(30);
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42)
                    .put("connection_generation",4).put("bridge_version","software-m0")
                    .put("expected_ck3_version",Build.CROZIER4.version()).put("expected_ck3_sha256",Build.CROZIER4.sha256())
                    .put("game_adapter_id","software-m0-claims-adapter").put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(CAPABILITY);
            var state=StrictJson.object().put("date_raw",DATE).put("paused",true).put("map_ready",true);
            state.putObject("played_character").put("character_id",actor).put("alive",true);
            var snapshot=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:73").put("revision",REV);
            snapshot.set("state",state);
            byte[] helloPacket=NativeWire.packet(StrictJson.canonical(hello));
            port=new Replay(helloPacket,NativeWire.packet(StrictJson.canonical(snapshot)),NativeWire.packet(producer));
            var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\software-m0-claims",MACHINE,
                    new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"software-m0-claims-session","software-m0",Build.CROZIER4.sha256(),"software-m0-claims-adapter");
            transport=ClaimsNativeTransportFixture.create(port,config);
            var observed=transport.observe(deadline);
            helloRef=preserve(name+"-hello",helloPacket);nativeRef=preserve(name+"-snapshot",observed.originalPacket());
            var source=new G2Source(MACHINE,now.toString(),Build.CROZIER4.version(),helloRef);
            var identity=new ObservationIdentity(MACHINE,config.game(),new JointBudgetSelector.ProposalFrame(
                    new JointBudgetSelector.Frame(BigInteger.valueOf(actor),REV,DATE),"native:73",BigInteger.valueOf(7),"software-m0-episode"),1);
            context=new Context(identity,source,config.sessionId(),BigInteger.valueOf(4),Build.CROZIER4,deadline,
                    new ControlFrame(true,true,true,1,0L,actor,"software-m0-episode",false,null,null,List.of()));
            var definitions=new InteractionTitleSelectorReads(helloRef,nativeRef);
            var catalog=new RootReadContractCatalog(List.of(),definitions.families());definitions.attach(catalog);
            contract=definitions.issue(selector);
        }
        RawJson invoke(TitleClaimsPublicCodec.Request input) throws IOException,InterruptedException {
            var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),contract.operation(),
                    InteractionTitleSelectorReads.arguments(context,input.selector()),context.deadline());
            prepared=contract.prepare(request,REQUEST_ID);
            var guard=new PlanningReadGuard(new GuardEvidence(context.before(),context.source(),context.sessionId(),context.connectionGeneration(),
                    contract.operation(),nativeRef,helloRef,"software-m0-claims-authority",Instant.now(),context.deadline()),true,true,true,"b".repeat(64));
            permit=ClaimsReadPermitFixture.issue(contract,request,prepared,guard,REQUEST_ID);
            var outcome=transport.read(permit,prepared,context.deadline());
            ack=assertInstanceOf(NativeActionPort.AckReceived.class,outcome);
            assertTrue(permit.consumed());
            if(!ack.nativeOk())throw new IllegalStateException("retained original Native query rejected; no business result");
            receipt=new PlanningReadReceipt(request,contract.contractId(),REQUEST_ID,guard,guard,ack);
            decoded=contract.decode(receipt);var original=preserveUnchecked("read-"+publications,ack.originalPacket());
            var known=new PlanningReadResult.Known<>(decoded,receipt,original);
            RawJson result=TitleClaimsPublicCodec.publication(known,input.selector());publications++;return result;
        }
        @Override public void close() throws IOException{transport.close();}
    }
    private ExactRef preserve(String name,byte[] original) throws Exception {
        Path file=temporary.resolve(name+".bin");Files.write(file,original);
        return new ExactRef(file.toString(),original.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
    }
    private ExactRef preserveUnchecked(String name,byte[] original) throws IOException {
        try{return preserve(name,original);}catch(IOException failure){throw failure;}catch(Exception failure){throw new IOException(failure);}
    }
    private static byte[] readProducer(String relative) throws IOException {
        String external=System.getProperty("xar.m0.producer");
        if(external!=null)return Files.readAllBytes(Path.of(external).resolve(relative));
        try(var stream=NativeClaimsProducerConsumptionTest.class.getClassLoader().getResourceAsStream(RESOURCE+relative)) {
            if(stream==null)throw new IOException("NOT EXECUTED: missing original Native producer resource "+relative);
            return stream.readAllBytes();
        }
    }
    private static final class StreamSupport {
        private StreamSupport() { }
        static List<Int32Id> ids(JsonNode values) {
            var result=new java.util.ArrayList<Int32Id>();
            for(var value:values)result.add(new Int32Id(Math.toIntExact(StrictJson.integer(value,0,Integer.MAX_VALUE))));
            return List.copyOf(result);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> frames=new ArrayDeque<>();final byte[] response;int writes;
        Replay(byte[] hello,byte[] snapshot,byte[] response){frames.add(hello);frames.add(snapshot);this.response=response.clone();}
        public void verify() { }
        public void awaitConnection(Instant deadline) { }
        public byte[] readPacket(Instant deadline) throws IOException {
            if(frames.isEmpty())throw new IOException("software replay exhausted");return frames.removeFirst().clone();
        }
        public void writePacket(byte[] packet,Instant deadline) throws IOException {
            var request=NativeWire.decodeExecuteRequest(packet);
            assertEquals(REQUEST_ID,request.requestId());assertEquals(Optional.of(REV),request.expectedRevision());
            assertTrue(request.step().startsWith("query-player-claims-v1-"));
            assertEquals("{}",new String(request.normalizedAdditionalFields().value(),java.nio.charset.StandardCharsets.UTF_8));
            writes++;frames.addLast(response.clone());
        }
        public void close() { }
    }
}
