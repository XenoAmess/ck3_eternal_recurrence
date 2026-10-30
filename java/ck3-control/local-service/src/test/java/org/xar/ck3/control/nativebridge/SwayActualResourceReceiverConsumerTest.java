package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.sway.SwayCanonicalDomain;
import org.xar.ck3.control.application.planning.sway.SwayFormalState;
import org.xar.ck3.control.application.planning.sway.SwayNativeWire;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact Native owned-peer HELLO and full-reader packets through the production Java receive/facts chain.
 * Endpoint I/O and Driver lifecycle DATA are software seams; no physical pipe, Game or Fresh READ is claimed. */
final class SwayActualResourceReceiverConsumerTest {
    private record Joined(int actor,DriverObservationAssembler.Complete complete,SwayNativeWire.Binding binding) { }

    @Test void actualNativeHelloAndResourceSnapshotsReachRealReceiverFactsAndComplete() throws Exception {
        Set<Integer> actors=new HashSet<>();int count=0;
        for(JsonNode row:originals()) {actors.add(receive(row).actor());count++;}
        assertEquals(2,count);assertEquals(Set.of(-2,0),actors);
    }

    @Test void actualCompleteNativeResourceSnapshotsReachCanonicalStartContext() throws Exception {
        List<String> failures=new ArrayList<>();Set<Integer> actors=new HashSet<>();int count=0;
        for(JsonNode row:originals()) {
            var joined=receive(row);
            try {assertEquals(SwayFormalState.MandatoryContext.CLEAR,SwayCanonicalDomain.context(joined.complete(),joined.binding()));actors.add(joined.actor());}
            catch(IllegalArgumentException unavailable) {failures.add(joined.actor()+": "+unavailable.getMessage());}
            count++;
        }
        assertEquals(2,count);assertEquals(List.of(),failures,"actual complete Native packets rejected by canonical context");assertEquals(Set.of(-2,0),actors);
    }

    private static Joined receive(JsonNode row) throws Exception {
        byte[] helloBody=body(row,"hello_original_utf8","hello_sha256"),helloPacket=frame(row,"hello_frame_base64","hello_frame_sha256",helloBody);
        byte[] raw=body(row,"original_utf8","sha256"),packet=frame(row,"frame_base64","frame_sha256",raw);
        var hello=assertInstanceOf(NativeWire.Hello.class,NativeWire.decode(helloPacket));
        var game=new GameGeneration(hello.pid(),new PythonOnlyUInt64(BigInteger.ONE));
        // This configuration is explicit software DATA selected from this original owned peer,
        // not an independently observed CK3 process, build qualification or Game birth time.
        String slash=Character.toString(92),pipe=slash+slash+"."+slash+"pipe"+slash+"owned-resource-originals";
        var config=new NativePipeEndpoint.Config(pipe,"xenoamess-full-tower-eb9d2c1186",game,"software-actual-resource-session",hello.bridgeVersion(),hello.gameSha256(),hello.adapterId());
        var port=new OriginalPackets(helloPacket,packet);
        try(var transport=new NativeGameTransport(port,config,8,4)) {
            var actual=transport.observe(Instant.now().plusSeconds(10));
            assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED,transport.diagnostics().receivedState());
            assertArrayEquals(helloPacket,transport.originalHello().packet().value());assertArrayEquals(packet,actual.originalPacket());
            assertSame(actual,transport.latestObservedSnapshot().orElseThrow());
            assertTrue(transport.acceptedSnapshotRevision(actual).publicRevision().signum()>0);
            int actor=NativeCharacterId.fromJson(StrictJson.parse(actual.state().bytes()).at("/played_character/character_id")).value();
            var initial=InitialDriverState.create(actual,pipe,"software-actual-resource-episode-"+actor,policy());
            byte[] full=initial.driver().encode();assertArrayEquals(full,DriverStateSnapshot.decodeComplete(full).encode());
            var archive=new OriginalArchive();var driverRef=archive.preserve(full);var helloRef=archive.preserve(helloPacket);var nativeRef=archive.preserve(packet);
            var stamp=new DriverSnapshotFacts.Stamp(0,0,game,initial.driver().session().episodeRunId(),ActionCodec.sha256(full));
            var known=new DriverSnapshotFacts.Known(initial.driver(),stamp,driverRef,List.of(),initial.auxiliary(),Optional.empty(),Optional.empty());
            var repository=new DriverFactsRepository(known);
            var source=new G2Source(config.machineId(),actual.observedAt().toString(),SwayNativeWire.BUILD,helloRef);
            var producer=new NativeDriverObservationProducer(repository,transport,source,archive);
            var facts=assertInstanceOf(DriverObservationFacts.Known.class,producer.read(actual)).facts();
            var diagnostics=OpportunityJson.object(facts.originalSemanticFields().get("diagnostics"),"actual produced diagnostics");
            assertEquals(StrictJson.parse(helloBody),OpportunityJson.toNode(diagnostics.get("hello")));
            assertEquals(new OpportunityJson.Bool(true),diagnostics.get("connected"));
            var manifest=archive.read(facts.semanticFactsEvidence());
            var savedDriver=DriverObservationEvidenceReader.currentDriverReference(facts.semanticFactsEvidence(),manifest);
            var replayActual=DriverObservationEvidenceReader.nativeFrame(facts.semanticFactsEvidence(),manifest,packet);
            var replay=DriverObservationEvidenceReader.decode(facts.semanticFactsEvidence(),manifest,archive.read(savedDriver),replayActual);
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(replayActual,replay,nativeRef));
            assertEquals(BigInteger.valueOf(actor),complete.identity().frame().identity().player());
            assertEquals(BigInteger.valueOf(7),OpportunityJson.integer(OpportunityJson.object(complete.semantic().get("played_character"),"player").get("stress_points"),"stress"));
            assertEquals(2,port.reads);assertEquals(0,port.writes);
            assertArrayEquals(raw,Arrays.copyOfRange(actual.originalPacket(),4,actual.originalPacket().length));
            return new Joined(actor,complete,new SwayNativeWire.Binding(complete.identity(),complete.sessionId(),complete.connectionGeneration(),"software-owned-resource-context-authority",SwayNativeWire.BUILD,SwayNativeWire.EXE));
        }
    }
    private static InitialEpisodePolicy policy() {
        var lifecycle=StrictJson.object();lifecycle.put("schema","xar.ck3.succession-lifecycle-binding/v1");lifecycle.put("lifecycle","ordinary_campaign_succession");
        lifecycle.putNull("xar_enabled");lifecycle.put("pact_contract","software_owned_fixture_no_pact");lifecycle.put("source","software_owned_fixture");lifecycle.putNull("environment_sha256");
        return InitialEpisodePolicy.ordinary(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,new RawJson(StrictJson.canonical(lifecycle)));
    }
    private static JsonNode originals() throws IOException {
        try(var in=SwayActualResourceReceiverConsumerTest.class.getResourceAsStream("/sway/m6-native-resource-receiver-originals.json")) {
            if(in==null)throw new IOException("NOT EXECUTED: actual same-peer Native HELLO and snapshots required; no hand-authored HELLO");
            var rows=StrictJson.parse(in.readAllBytes());assertTrue(rows.isArray());assertEquals(2,rows.size());return rows;
        }
    }
    private static byte[] body(JsonNode row,String field,String hash) {byte[] raw=row.get(field).textValue().getBytes(StandardCharsets.UTF_8);assertEquals(row.get(hash).textValue(),ActionCodec.sha256(raw));return raw;}
    private static byte[] frame(JsonNode row,String field,String hash,byte[] raw) throws IOException {byte[] framed=Base64.getDecoder().decode(row.get(field).textValue());assertEquals(row.get(hash).textValue(),ActionCodec.sha256(framed));assertArrayEquals(NativeWire.packet(raw),framed);return framed;}
    private static final class OriginalArchive implements NativeDriverObservationProducer.SemanticEvidencePort {
        private final Map<String,byte[]> originals=new HashMap<>();
        @Override public ExactRef preserve(byte[] raw) {String sha=ActionCodec.sha256(raw);var ref=new ExactRef("software-owned-native-original:"+sha,raw.length,sha);var prior=originals.putIfAbsent(sha,raw.clone());if(prior!=null)assertArrayEquals(prior,raw);return ref;}
        RawJson read(ExactRef ref) {byte[] original=originals.get(ref.sha256());assertNotNull(original);assertEquals(ref.bytes(),original.length);assertEquals(ref.sha256(),ActionCodec.sha256(original));return new RawJson(original);}
    }
    private static final class OriginalPackets implements NativePacketPort {
        private final ArrayDeque<byte[]> packets=new ArrayDeque<>();int reads,writes;
        OriginalPackets(byte[]... originals) {for(byte[] original:originals)packets.add(original.clone());}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {reads++;if(packets.isEmpty())throw new IOException("original Native packet stream exhausted");return packets.removeFirst().clone();}
        @Override public void writePacket(byte[] packet,Instant deadline) {writes++;throw new AssertionError("snapshot replay must not send a request");}
        @Override public void close() { }
    }
}
