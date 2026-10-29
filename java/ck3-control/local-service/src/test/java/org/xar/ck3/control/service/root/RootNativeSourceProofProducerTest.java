package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeInputs;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Uses real Windows identities. It never constructs ManagedGameSession or live qualification. */
final class RootNativeSourceProofProducerTest {
    @TempDir Path temporary;

    @Test void actualObservedWitnessProducerAndCodecRetainOriginalFileIdAfterSameBytesCopy() throws Exception {
        Path original = temporary.resolve("original.dat"); Files.write(original, new byte[] {1, 2, 3});
        var live = SharedSourceFiles.observe(original);
        var retained = RootNativeSourceProofProducer.persistWitnesses(List.of(live, live));
        assertEquals(1, retained.size());
        var source = retained.get(0).source();
        var epoch = new ExactRef(temporary.resolve("epoch.json").toString(), 3, "a".repeat(64));
        var data = new NativeSourceProofDocument("software-data-machine", "software-data-session", "2026-10-24T19:00:00Z",
                NativeSourceProofDocument.Mode.MCP_STDIO, source, source, epoch.sha256(), epoch, source, List.of(source), retained);
        var decoded = NativeSourceProofCodec.decode(NativeSourceProofCodec.encode(data));
        assertEquals(live.nativeFile().fileIdDecimal(), decoded.liveWitnesses().get(0).nativeFile().fileIdDecimal());
        assertEquals(live.nativeFile().creationFiletimeDecimal(), decoded.liveWitnesses().get(0).nativeFile().creationFiletimeDecimal());
        Path copy = temporary.resolve("copy.dat"); Files.copy(original, copy);
        var differentFile = SharedSourceFiles.observe(copy);
        assertEquals(live.source().sha256(), differentFile.source().sha256());
        assertNotEquals(live.nativeFile().identityKey(), differentFile.nativeFile().identityKey());
        Files.move(copy, original, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class, () -> SharedSourceFiles.assertUnchanged(live));
        assertEquals(live.nativeFile().fileIdDecimal(), decoded.liveWitnesses().get(0).nativeFile().fileIdDecimal());
    }

    @Test void emptyWitnessesCannotUpgradeOldHashOnlyProof() {
        assertThrows(IOException.class, () -> RootNativeSourceProofProducer.persistWitnesses(List.of()));
    }

    @Test void allThreeSharedModesReachTheActualProducerAndSoleCodecWithOriginalPhysicalWitnesses() throws Exception {
        var materials=materials();
        for(HostMode mode:List.of(HostMode.HTTP,HostMode.MCP_STDIO,HostMode.COMPLETE_MIGRATION)) {
            NativeSourceProofDocument document=produce(materials,mode);
            byte[] bytes=NativeSourceProofCodec.encode(document);
            NativeSourceProofDocument decoded=NativeSourceProofCodec.decode(bytes);
            assertEquals(mode.name(),decoded.mode().name());assertEquals(document,decoded);
            assertEquals(materials.held().get(0).nativeFile().fileIdDecimal(),decoded.liveWitnesses().get(0).nativeFile().fileIdDecimal());
            assertEquals(materials.expected().mandatoryEvidence().size(),decoded.completeEvidenceClosure().size());
            assertArrayEquals(bytes,NativeSourceProofCodec.encode(decoded));
        }
    }

    @Test void thirdModeDoesNotAddAliasesNullOrDefaultModesAtTheWireBoundary() throws Exception {
        byte[] valid=NativeSourceProofCodec.encode(produce(materials(),HostMode.COMPLETE_MIGRATION));
        ObjectMapper json=new ObjectMapper();
        for(String invalid:List.of("complete_migration","COMPLETE","COMPLETE_MIGRATION ","MCP","http","")) {
            ObjectNode row=(ObjectNode)json.readTree(valid);row.put("mode",invalid);
            byte[] encoded=json.writeValueAsBytes(row);
            assertThrows(IOException.class,()->NativeSourceProofCodec.decode(encoded));
        }
        ObjectNode missing=(ObjectNode)json.readTree(valid);missing.remove("mode");
        byte[] missingBytes=json.writeValueAsBytes(missing);
        assertThrows(IOException.class,()->NativeSourceProofCodec.decode(missingBytes));
        ObjectNode nil=(ObjectNode)json.readTree(valid);nil.putNull("mode");
        byte[] nullBytes=json.writeValueAsBytes(nil);
        assertThrows(IOException.class,()->NativeSourceProofCodec.decode(nullBytes));
    }

    /** Physical input observations plus software-only proof DTOs; no SourceAuthority/Game is made. */
    private record Materials(NativeInputs expected,FileRef host,ExactRef originalSource,ExactRef epoch,
            List<SharedSourceFiles.Witness> held) {
        private Materials {held=List.copyOf(held);}
    }
    private Materials materials() throws IOException {
        var environment=physical("environment.actual.json");var build=physical("build.actual.json");
        var registration=physical("registration.actual.json");var source=physical("native-src/proof.cpp");
        var bridge=physical("xar_ck3_bridge.dll");var injector=physical("xar_ck3_bridge_injector.exe");
        var game=physical("ck3.exe");var settings=physical("launcher-settings.json");var host=physical("host.json");
        var expected=new NativeInputs(environment.source(),build.source(),registration.source(),temporary.resolve("native-src").toString(),
                List.of(source.source()),bridge.source(),injector.source(),game.source(),settings.source(),"software-data-version","software-data-adapter");
        var held=new ArrayList<>(List.of(environment,build,registration,source,bridge,injector,game,settings,host));
        var original=physical("original-source.json");var epoch=physical("epoch.json");
        return new Materials(expected,host.source(),exact(original.source()),exact(epoch.source()),held);
    }
    private SharedSourceFiles.Witness physical(String relative) throws IOException {
        Path path=temporary.resolve(relative);Files.createDirectories(path.getParent());Files.write(path,new byte[]{1,2,3});
        return SharedSourceFiles.observe(path);
    }
    private static NativeSourceProofDocument produce(Materials materials,HostMode mode) throws IOException {
        var proof=new NativeProof("software-data-machine",mode,materials.host(),materials.expected(),materials.expected().mandatoryEvidence());
        var identity=new SessionIdentity("software-data-machine",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),"software-data-session");
        return RootNativeSourceProofProducer.document(identity,"2026-10-25T01:00:00Z",proof,materials.host(),
                materials.originalSource(),materials.epoch(),materials.held());
    }
    private static ExactRef exact(FileRef source) {return new ExactRef(source.path(),source.bytes(),source.sha256());}
}
