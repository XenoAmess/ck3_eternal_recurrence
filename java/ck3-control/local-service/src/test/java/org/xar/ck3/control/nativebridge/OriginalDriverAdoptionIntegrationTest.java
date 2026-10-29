package org.xar.ck3.control.nativebridge;

import org.xar.ck3.control.service.root.RootOriginalDriverJournal;
import org.xar.ck3.control.service.root.RootFrozenRunProfile;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel;
import org.xar.ck3.control.service.root.RootOriginalDriverColdFixture;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.EnumSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.nativebridge.capabilities.diagnostics.BridgeDiagnosticsCodec;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePacketPort;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Shared exact v2 input/approved fixed writer, real private file issuer and actual NGT ingestion. No TempDir or manufactured token. */
final class OriginalDriverAdoptionIntegrationTest {
    @Test void actualFirstConnectionIssuerAndCanonicalNormalizerProduceTheFourOriginalRefusalsAndNeverPingThem()throws Exception {
        var inputs=RootOriginalDriverColdFixture.readRequiredSystemProperties();
        var expected=RootOriginalDriverColdFixture.readAdoptionRequiredSystemProperties();
        assertEquals(WindowsJobProcess.currentMachineId(),expected.machineId());assertEquals(inputs.machineId(),expected.machineId());
        var covered=EnumSet.noneOf(AdoptionRefusalReason.class);int successes=0;
        for(RootOriginalDriverColdFixture.Expected outcome:expected.cases()) {
            var test=inputs.cases().stream().filter(value->value.name().equals(outcome.caseName())).findFirst().orElseThrow();
            var plan=NativeLaunchPlan.readExact(test.launchPlan(),new NativeBridgeLaunchEvidence());
            Clock clock=Clock.systemUTC();RootOriginalDriverColdFixture.requirePrelaunch(plan,clock);
            var policy=InitialEpisodePolicy.readExact(test.episodePolicy(),plan.preparedProfile().environmentManifest());
            var profile=RootFrozenRunProfile.readExact(test.runRequest(),plan,policy,clock);
            try(var scope=RootOriginalDriverColdFixture.openReadOnlyScope(test.control(),test.storageLease(),expected.machineId(),clock)) {
            var writer=scope.writer();var storage=scope.storage();var files=scope.files();
            RootOriginalDriverColdFixture.requireStorage(plan,test.control(),storage);
            var issuer=new RootOriginalDriverJournal.Prepared(files,storage,plan,profile,clock);
            var game=new GameGeneration(outcome.gamePid(),new PythonOnlyUInt64(new BigInteger(outcome.gameCreationFiletime())));
            var config=new NativePipeEndpoint.Config(plan.pipeName(),expected.machineId(),game,plan.sessionId(),
                    plan.bridgeVersion(),plan.sources().review().gameExecutable().sha256(),plan.adapterId());
            var packet=new HelloOnly(read(outcome.originalFramedHello(),1048576));
            try(var transport=new NativeGameTransport(packet,config,16,16)) {
                Instant deadline=clock.instant().plusSeconds(30);transport.awaitHello(deadline);
                writer.locked(same->{
                    String head=same.head().digest();var original=issuer.load(writer,same,plan);
                    assertEquals(test.expectedStatus(),original.status());original.requireRetained(same);
                    if(outcome.expectedReason()!=null) {
                        var refusal=assertThrows(DriverBootstrap.OriginalAdoptionRefused.class,
                                ()->DriverBootstrap.requireOriginalAdoption(same,transport,original));
                        assertEquals(outcome.expectedReason(),refusal.reason());
                        var recorded=assertInstanceOf(NativeTransportDiagnostics.Observed.class,
                                transport.diagnostics().production().orElseThrow().adoption()).refusal().orElseThrow();
                        assertEquals(outcome.expectedReason(),recorded.reason());assertEquals(game,recorded.session().game());
                        assertEquals(refusal.getClass().getName(),recorded.exceptionType());assertEquals(refusal.getMessage(),recorded.message());
                        var fields=BridgeDiagnosticsCodec.nativeProductionFields(transport.diagnostics().production().orElseThrow());
                        var encoded=OpportunityJson.object(fields.get("transport_refusal"),"actual original refusal");
                        assertEquals(new OpportunityJson.Text(outcome.expectedReason().wire()),encoded.get("reason"));
                        assertEquals(fields,OpportunityJson.parse(OpportunityJson.encode(fields)));
                        assertTrue(transport.handshakeDiagnostics().attempt().isEmpty());assertEquals(0,packet.writes);
                        assertThrows(IOException.class,()->transport.startHandshake(deadline));assertEquals(0,packet.writes);
                    }else {
                        DriverBootstrap.requireOriginalAdoption(same,transport,original);
                        assertTrue(transport.handshakeDiagnostics().attempt().isEmpty());
                        try {
                            var ping=transport.startHandshake(deadline);assertEquals(NativeGameTransport.PingWriteState.RETURNED,ping.writeState());
                            assertSame(ping,transport.startHandshake(deadline));assertEquals(1,packet.writes);
                        } catch (InterruptedException interrupted) {
                            Thread.currentThread().interrupt();
                            throw new IOException("original Driver handshake interrupted",interrupted);
                        }
                        assertTrue(transport.handshakeDiagnostics().pong().isEmpty(),"the original Driver does not await a PONG");
                    }
                    original.requireRetained(same);assertEquals(head,same.head().digest());return null;
                });
                assertEquals(1,packet.reads,"classification and handshake must not query another frame");
                assertArrayEquals(packet.hello,read(outcome.originalFramedHello(),1048576));
            }
            }
            if(outcome.expectedReason()==null)successes++;else covered.add(outcome.expectedReason());
        }
        assertTrue(successes>0,"mandatory actual positive input missing");
        assertEquals(EnumSet.allOf(AdoptionRefusalReason.class),covered,"all four actual producer failures are required, not a skipped denominator");
    }
    private static byte[] read(ExactRef source,int limit)throws IOException {
        assertTrue(source.bytes()>0&&source.bytes()<=limit);var file=new ControlBuild.FileRef(source.path(),source.bytes(),source.sha256());
        file.verify();byte[] raw=Files.readAllBytes(Path.of(source.path()));file.verify();return raw;
    }
    private static final class HelloOnly implements NativePacketPort {
        private final byte[] hello;private int reads,writes;
        private HelloOnly(byte[] original){hello=original.clone();}
        @Override public void verify(){ }
        @Override public void awaitConnection(Instant deadline){ }
        @Override public byte[] readPacket(Instant deadline)throws IOException {if(++reads!=1)throw new IOException("fixture has only its original HELLO");return hello.clone();}
        @Override public void writePacket(byte[] packet,Instant deadline){writes++;assertEquals(1,writes);assertTrue(packet.length>4);}
        @Override public void close(){ }
    }
}
