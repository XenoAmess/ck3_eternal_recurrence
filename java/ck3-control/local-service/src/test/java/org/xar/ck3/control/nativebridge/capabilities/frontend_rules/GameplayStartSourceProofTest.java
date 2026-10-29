package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;

/** Shape-only producer/consumer contract regression; this creates no live source or Game authority. */
class GameplayStartSourceProofTest {
    @Test void actualSourceProofCodecFeedsTheStartConsumerWithEveryOriginalWitness()throws Exception {
        var proof=original();byte[] wire=NativeSourceProofCodec.encode(proof);
        var decoded=GameplayStartEffects.sourceProof(wire,proof.machineId(),proof.sessionId(),proof.source());
        assertEquals(proof,decoded);
        assertEquals("340282366920938463463374607431768211455",decoded.liveWitnesses().getFirst().nativeFile().fileIdDecimal());
        assertEquals("18446744073709551615",decoded.liveWitnesses().getFirst().nativeFile().creationFiletimeDecimal());
        assertArrayEquals(wire,NativeSourceProofCodec.encode(decoded));
    }

    @Test void actualStartConsumerRejectsOldSchemasAndIncompleteWitnesses()throws Exception {
        var proof=original();byte[] wire=NativeSourceProofCodec.encode(proof);
        for(String schema:List.of("xar.java-root-native-source-proof/v1","xar.java-root-native-source-proof/v2")) {
            ObjectNode row=assertInstanceOf(ObjectNode.class,ControlBuild.strictMapper().readTree(wire));row.put("schema",schema);
            assertThrows(IOException.class,()->GameplayStartEffects.sourceProof(ContinuityJson.canonical(row),proof.machineId(),proof.sessionId(),proof.source()));
        }
        ObjectNode missing=assertInstanceOf(ObjectNode.class,ControlBuild.strictMapper().readTree(wire));missing.remove("live_witnesses");
        assertThrows(IOException.class,()->GameplayStartEffects.sourceProof(ContinuityJson.canonical(missing),proof.machineId(),proof.sessionId(),proof.source()));
        ObjectNode numeric=assertInstanceOf(ObjectNode.class,ControlBuild.strictMapper().readTree(wire));
        ((ObjectNode)numeric.get("live_witnesses").get(0).get("native_file")).put("file_id_decimal",1);
        assertThrows(IOException.class,()->GameplayStartEffects.sourceProof(ContinuityJson.canonical(numeric),proof.machineId(),proof.sessionId(),proof.source()));
    }

    @Test void actualStartConsumerKeepsTheOriginalMachineSessionAndSourceBindings()throws Exception {
        var proof=original();byte[] wire=NativeSourceProofCodec.encode(proof);
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.sourceProof(wire,"another-machine",proof.sessionId(),proof.source()));
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.sourceProof(wire,proof.machineId(),"another-session",proof.source()));
        assertThrows(IllegalArgumentException.class,()->GameplayStartEffects.sourceProof(wire,proof.machineId(),proof.sessionId(),reference("another.cpp","d")));
    }

    private static NativeSourceProofDocument original() {
        ExactRef host=reference("host.json","a"),source=reference("bridge.cpp","b"),epoch=reference("epoch.json","e"),exe=reference("ck3.exe","c");
        var identity=new NativeSourceFileIdentity("18446744073709551615","340282366920938463463374607431768211455",
                "4294967295","ffffffffffffffff","18446744073709551615","18446744073709551614","18446744073709551613",1,4096,1);
        return new NativeSourceProofDocument("software-test-machine","original-session","2026-10-24T19:00:00Z",
                NativeSourceProofDocument.Mode.MCP_STDIO,host,source,epoch.sha256(),epoch,exe,List.of(source,epoch),
                List.of(new SourceWitness(host,identity),new SourceWitness(source,identity),new SourceWitness(epoch,identity),new SourceWitness(exe,identity)));
    }
    private static ExactRef reference(String name,String digest){return new ExactRef("D:/source-proof-contract/"+name,1,digest.repeat(64));}
}
