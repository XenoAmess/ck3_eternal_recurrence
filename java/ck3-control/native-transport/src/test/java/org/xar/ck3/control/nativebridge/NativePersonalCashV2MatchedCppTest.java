package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

/** Requires externally pinned Native-owner C++ paired output, never a V1 JSON rewrite.
 * HELLO, READ ACK and CASH ACK envelopes below are controlled software protocol fixtures.
 * The actual C++ Full/CASH value tokens are immutable DATA, not actual Bridge ACKs or live authority.
 */
final class NativePersonalCashV2MatchedCppTest {
    private static final String STEP="query-war-cash-current-resources-v2",CAP="game.query.war-cash-current-resources.v2";
    private static final String BRIDGE="software-cash-v2-actual-data",ADAPTER="ck3-1.21.0-msvc-x64";
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final int MAXIMUM_PAIR=16384;
    private static final int[] ARMY17_BYTES={1599,1619,1588};
    private static final String[] ARMY17_SHA={
        "a4a2c51c76c06837259e3b1039f7d0ad29a471169aa41b414bc160baa09541d2",
        "876d7b6e347a3e9bac096543ca56fd588955f818d272cd391282572d27e29ef9",
        "57b81036e92a7de9beba3a5963aec623bafc84ad94fe2e7a88ba7273a9c166ec"};
    private record Pair(byte[] original,byte[] full,byte[] cash,byte[] rawCash) { }

    @Test void actualPairedCppFullAndCashReachRawCodecAndPrivateReceiptWithIdenticalCompleteArmyScope() throws Exception {
        for(int variant=0;variant<3;variant++) {
            var pair=pair(variant);assertArrayEquals(army17(variant),pair.full(),"paired Full must exactly match retained Army17 value");
            byte[] original=pair.original().clone();
            try(var f=new Fixture(pair)) {
                var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
                var projection=PersonalCashFullProjection.snapshotData(before.frame(),f.transport.diagnostics().originalHello().orElseThrow().original());
                var direct=RawCashCodec.normalize(pair.rawCash(),projection.bytes());
                var receipt=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
                int actor=variant==1?-2130706431:1,unit=variant==2?0:-2080374784;
                assertEquals(actor,direct.frame().playedCharacterId());assertEquals(BigInteger.valueOf(10+variant),direct.frame().snapshotRevision());
                assertEquals(List.of(BigInteger.valueOf(unit)),direct.playerArmyIds());
                assertEquals(RawCashCodec.PlayerArmyIdDomain.FLORIN_SIGNED_FULL,direct.playerArmyIdDomain());
                assertArrayEquals(StrictJson.canonical(StrictJson.parse(direct.toJson())),StrictJson.canonical(StrictJson.parse(receipt.cash().toJson())));
                assertEquals(direct.frame(),receipt.cash().frame());assertEquals(direct.playerArmyIdDomain(),receipt.cash().playerArmyIdDomain());assertEquals(BigInteger.valueOf(-1234567),receipt.cash().metrics().currentTreasury().value().raw());
                var canonical=DriverJson.toNode(DriverObservationAssembler.canonicalNativeState(before.frame()).semantic(),DriverJson.MAX_NATIVE_BYTES);
                assertEquals(unit,canonical.path("player_armies").get(0).path("army_id").intValue());
                assertTrue(canonical.path("player_armies").get(0).get("soldiers").isNull());
                receipt.requireOriginal(f.transport,until);assertArrayEquals(pair.cash(),receipt.original().originalResultToken().orElseThrow().bytes());
                receipt.original().custody().orElseThrow().verify(receipt.original());
                assertFalse(StrictJson.parse(receipt.cash().toJson()).path("formal_action_ready").booleanValue());
                zero(f.transport.readPersonalCashSignedScopeReceived(before,until));zero(f.transport.readPersonalCashReceived(before,until));
                assertEquals(1,f.source.fullWrites);assertEquals(1,f.source.cashWrites);
            }
            assertArrayEquals(original,pair.original());
        }
    }

    @Test void actualProviderWalletDriftInnerDataRemainsUnknownUnderAControlledPositiveAck() throws Exception {
        var pair=pair(3);assertArrayEquals(army17(0),pair.full());
        var cash=NativeWire.object(NativeWire.parse(pair.rawCash()));
        for(String key:List.of("current_treasury","player_monthly_gross_income","player_monthly_total_expenses","player_monthly_net_income"))
            assertTrue(cash.get(key).isNull(),key);
        assertFalse(cash.path("readiness").path("same_frame_ready").booleanValue());
        try(var f=new Fixture(pair)) {
            var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
            var data=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
            var metrics=data.cash().metrics();
            for(var money:List.of(metrics.currentTreasury(),metrics.monthlyGrossIncome(),metrics.monthlyTotalExpenses(),metrics.monthlyNetIncome())) {
                assertEquals(RawCashCodec.Presence.NULL,money.presence());assertFalse(money.known());
            }
            assertTrue(metrics.readiness().sameFrameReady().known());assertFalse(metrics.readiness().sameFrameReady().value());
            assertFalse(StrictJson.parse(data.cash().toJson()).path("formal_action_ready").booleanValue());
            assertArrayEquals(pair.cash(),data.original().originalResultToken().orElseThrow().bytes());
            data.requireOriginal(f.transport,until);zero(f.transport.readPersonalCashSignedScopeReceived(before,until));
            assertEquals(1,f.source.fullWrites);assertEquals(1,f.source.cashWrites);
        }
    }

    @Test void providerDriftWithControlledNegativeOuterAckKeepsTheOriginalResultWithoutAReceipt() throws Exception {
        var pair=pair(3);
        // This rejection envelope is software DATA too. The real Bridge's failure
        // result shape is a separate producer, not this actual inner formatter token.
        try(var f=new Fixture(pair,false)) {
            var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
            var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());assertFalse(ack.nativeOk());
            assertArrayEquals(pair.cash(),ack.originalResultToken().orElseThrow().bytes());
            zero(f.transport.readPersonalCashSignedScopeReceived(before,until));assertEquals(1,f.source.cashWrites);
        }
    }

    @Test void crossPairActorAndRevisionMismatchRetainTheExactCppResultAndNeverRetry() throws Exception {
        var basis=pair(0);var foreign=pair(1);
        var crossed=new Pair(foreign.original(),basis.full(),foreign.cash(),foreign.rawCash());
        try(var f=new Fixture(crossed)) {
            var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
            var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());
            assertArrayEquals(foreign.cash(),ack.originalResultToken().orElseThrow().bytes());
            zero(f.transport.readPersonalCashSignedScopeReceived(before,until));assertEquals(1,f.source.cashWrites);
        }
    }

    @Test void identicalCppBytesAtANewFullOccurrenceCannotRefreshTheOldCashReceipt() throws Exception {
        var pair=pair(0);
        try(var f=new Fixture(pair)) {
            var until=f.clock.instant().plusSeconds(30);var originalFull=f.full(until);
            var originalCash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.transport.readPersonalCashSignedScopeReceived(originalFull,until));
            var latestFull=f.full(until);assertNotSame(originalFull.frame(),latestFull.frame());
            assertArrayEquals(originalFull.frame().state().bytes(),latestFull.frame().state().bytes());
            assertThrows(IOException.class,()->originalCash.requireOriginal(f.transport,until));
            zero(f.transport.readPersonalCashSignedScopeReceived(originalFull,until));
            assertEquals(2,f.source.fullWrites);assertEquals(1,f.source.cashWrites);
            var latestCash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.transport.readPersonalCashSignedScopeReceived(latestFull,until));
            assertNotEquals(originalCash.original().requestId(),latestCash.original().requestId());
            assertArrayEquals(pair.cash(),originalCash.original().originalResultToken().orElseThrow().bytes());
            latestCash.requireOriginal(f.transport,until);assertThrows(IOException.class,()->originalCash.requireOriginal(f.transport,until));
            assertEquals(2,f.source.fullWrites);assertEquals(2,f.source.cashWrites);
        }
    }

    @Test void anotherReceiverWithTheSameCppFrameCannotAdoptTheOriginalCashReceipt() throws Exception {
        var pair=pair(0);
        try(var owner=new Fixture(pair);var foreign=new Fixture(pair)) {
            var until=owner.clock.instant().plusSeconds(30);var before=owner.full(until);
            var cash=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,owner.transport.readPersonalCashSignedScopeReceived(before,until));
            var foreignFull=foreign.full(until);assertArrayEquals(before.frame().state().bytes(),foreignFull.frame().state().bytes());
            assertThrows(IOException.class,()->cash.requireOriginal(foreign.transport,until));
            cash.requireOriginal(owner.transport,until);assertEquals(0,foreign.source.cashWrites);assertEquals(1,owner.source.cashWrites);
        }
    }

    @Test void actualCppChangedUnitGenerationJoinsItsOwnFullAndRefusesOriginalFullWithSameActorRevisionAndWallet() throws Exception {
        var original=pair(0);var changed=pair(4);int changedUnit=-2046820352;
        try(var f=new Fixture(changed)) {
            var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
            var receipt=assertInstanceOf(NativeGameTransport.PersonalCashReceived.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
            assertEquals(List.of(BigInteger.valueOf(changedUnit)),receipt.cash().playerArmyIds());
            receipt.requireOriginal(f.transport,until);
        }
        // Both halves below are unmodified actual C++ value tokens from separately
        // identified RAM fixtures. This is an explicit negative cross-pair, not one Native read.
        var crossed=new Pair(changed.original(),original.full(),changed.cash(),changed.rawCash());
        try(var f=new Fixture(crossed)) {
            var until=f.clock.instant().plusSeconds(30);var before=f.full(until);
            var projection=PersonalCashFullProjection.snapshotData(before.frame(),f.transport.originalHello());
            var direct=RawCashCodec.normalize(changed.rawCash(),projection.bytes());
            assertEquals(1,direct.frame().playedCharacterId());assertEquals(BigInteger.TEN,direct.frame().snapshotRevision());
            assertEquals(BigInteger.valueOf(-1234567),direct.metrics().currentTreasury().value().raw());
            assertEquals(List.of(BigInteger.valueOf(changedUnit)),direct.playerArmyIds());
            assertEquals(-2080374784,NativeWire.object(NativeWire.parse(before.frame().state().bytes())).path("player_armies").get(0).path("army_id").intValue());
            var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,f.transport.readPersonalCashSignedScopeReceived(before,until));
            assertTrue(unavailable.reason().contains("scope"),unavailable.reason());
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original());
            assertArrayEquals(changed.cash(),ack.originalResultToken().orElseThrow().bytes());
            zero(f.transport.readPersonalCashSignedScopeReceived(before,until));assertEquals(1,f.source.cashWrites);
        }
    }

    private static Pair pair(int variant) throws Exception {
        String prefix="xar.native.personalCashV2.matched."+variant;
        Path path=Path.of(required(prefix+".path"));if(!path.isAbsolute())throw new IOException("absolute Native-owner C++ pair path required");
        int bytes=Integer.parseInt(required(prefix+".bytes"));
        if(bytes<1||bytes>MAXIMUM_PAIR)throw new IOException("bounded actual paired C++ output required");
        String sha=required(prefix+".sha256");if(!sha.matches("[0-9a-f]{64}"))throw new IOException("exact lower-case owner SHA256 required");
        byte[] original=readExact(path,bytes,sha);
        var wrapper=NativeWire.object(NativeWire.parse(original));
        assertEquals(2,wrapper.size());assertTrue(wrapper.get("full").isObject());assertTrue(wrapper.get("cash").isObject());
        byte[] full=NativeWire.token(original,"full"),cash=NativeWire.token(original,"cash");
        return new Pair(original,full,cash,NativeWire.token(cash,"war_cash_current_resources"));
    }
    private static byte[] army17(int variant) throws Exception {
        Path root=Path.of(required("xar.native.personalCashV2.army17.root"));
        if(!root.isAbsolute())throw new IOException("absolute retained Army17 packet root required");
        byte[] original=readExact(root.resolve("full-army-producer-"+variant+".json"),ARMY17_BYTES[variant],ARMY17_SHA[variant]);
        // Select the exact original value, excluding its console newline; never re-encode a parsed tree.
        var wrapper=new ByteArrayOutputStream();wrapper.writeBytes("{\"full\":".getBytes(StandardCharsets.UTF_8));
        wrapper.writeBytes(original);wrapper.write('}');return NativeWire.token(wrapper.toByteArray(),"full");
    }
    private static byte[] readExact(Path path,int bytes,String sha) throws Exception {
        byte[] body;try(var input=Files.newInputStream(path)){body=input.readNBytes(bytes+1);}
        assertEquals(bytes,body.length,path.toString());assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)),path.toString());
        return body;
    }
    private static String required(String key) throws IOException {
        String value=System.getProperty(key);
        if(value==null||value.isBlank())throw new IOException("required actual Native-owner input pin missing: "+key);
        return value;
    }
    private static void zero(NativeGameTransport.PersonalCashRead read) {
        var unavailable=assertInstanceOf(NativeGameTransport.PersonalCashReadUnavailable.class,read);
        var zero=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,unavailable.original());
        assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.proof().stage());assertEquals(0,zero.proof().requestBytesWritten());
    }
    private static ObjectNode hello() {
        var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version",BRIDGE).put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add(CAP);return hello;
    }
    private static final class Fixture implements AutoCloseable {
        final Clock clock=Clock.fixed(Instant.now(),ZoneOffset.UTC);final Replay source;final NativeGameTransport transport;
        Fixture(Pair pair) throws Exception { this(pair,true); }
        Fixture(Pair pair,boolean cashAckAccepted) throws Exception {
            source=new Replay(pair,clock,cashAckAccepted);String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"cash-v2-no-game","cash-v2-no-game",GAME,"cash-v2-no-game-session",BRIDGE,BUILD.executableSha256(),ADAPTER);
            transport=new NativeGameTransport(source,config,32,32,List.of(),clock,Duration.ofSeconds(60));
        }
        NativeGameTransport.FullClockReceived full(Instant until) throws Exception {
            var full=assertInstanceOf(NativeGameTransport.FullClockReceived.class,transport.readFullClockFrameReceived(until));
            assertArrayEquals(source.snapshot.state().value(),full.frame().state().bytes());
            var read=full.original();NativeFreshSnapshotPort.verifyOriginal(read.acknowledgement(),read.originalFrame(),read.snapshotReceived());
            return full;
        }
        @Override public void close() throws IOException {transport.close();}
    }
    private static final class Replay implements NativePacketPort {
        final Pair pair;final Clock clock;final NativeWire.Snapshot snapshot;final ArrayDeque<byte[]> packets=new ArrayDeque<>();
        int fullWrites,cashWrites;boolean closed;final boolean cashAckAccepted;
        Replay(Pair pair,Clock clock,boolean cashAckAccepted) throws IOException {
            this.pair=pair;this.clock=clock;this.cashAckAccepted=cashAckAccepted;snapshot=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(NativeWire.packet(pair.full())));
            packets.add(NativeWire.packet(StrictJson.canonical(hello())));
        }
        @Override public void verify() throws IOException {if(closed)throw new IOException("closed controlled software port");}
        @Override public void verifyCoreControlWindowPolicy() throws IOException {verify();}
        private void check(Instant until) throws IOException {verify();if(!clock.instant().isBefore(until))throw new IOException("controlled software deadline expired");}
        @Override public void awaitConnection(Instant until) throws IOException {check(until);}
        @Override public byte[] readPacket(Instant until) throws IOException {
            check(until);if(packets.isEmpty())throw new IOException("controlled software response absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] body,Instant until) throws IOException {
            check(until);var request=NativeWire.decodeExecuteRequest(body);
            if(request.step().equals(NativeFreshSnapshotPort.STEP)) {
                fullWrites++;assertEquals(Optional.of(BigInteger.ZERO),request.expectedRevision());
                // Only the software READ correlation envelope changes. The actual C++ state
                // is byte-compared before delivery; no decoded tree is serialized here.
                String q=Character.toString(34),field=q+"read_request_id"+q+":"+q;
                byte[] packet=NativeWire.packet(replaceOnce(new String(pair.full(),StandardCharsets.UTF_8),
                        field+"full-army-producer-original"+q,field+request.requestId()+q).getBytes(StandardCharsets.UTF_8));
                assertArrayEquals(snapshot.state().value(),assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(packet)).state().value());
                var result=StrictJson.object().put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",request.requestId())
                        .put("snapshot_id",snapshot.snapshotId()).put("revision",snapshot.revision());
                packets.add(packet);packets.add(softwareAck(request.requestId(),StrictJson.canonical(result)));
            } else {
                assertEquals(STEP,request.step());assertEquals(Optional.of(snapshot.revision()),request.expectedRevision());
                assertEquals(Optional.of(snapshot.revision()),request.expectedSnapshotRevision());cashWrites++;
                byte[] packet=softwareAck(request.requestId(),pair.cash(),cashAckAccepted);
                var ack=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
                assertArrayEquals(pair.cash(),ack.result().token().orElseThrow().value());packets.add(packet);
            }
        }
        private static byte[] softwareAck(String id,byte[] actualCppResult) throws IOException { return softwareAck(id,actualCppResult,true); }
        private static byte[] softwareAck(String id,byte[] actualCppResult,boolean accepted) throws IOException {
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",accepted);envelope.putNull("result");
            String q=Character.toString(34);
            String body=replaceOnce(new String(StrictJson.canonical(envelope),StandardCharsets.UTF_8),q+"result"+q+":null",q+"result"+q+":"+new String(actualCppResult,StandardCharsets.UTF_8));
            return NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
        }
        private static String replaceOnce(String body,String token,String replacement) {
            int at=body.indexOf(token);assertTrue(at>=0);assertEquals(at,body.lastIndexOf(token));
            return body.substring(0,at)+replacement+body.substring(at+token.length());
        }
        @Override public void close() {closed=true;}
    }
}
