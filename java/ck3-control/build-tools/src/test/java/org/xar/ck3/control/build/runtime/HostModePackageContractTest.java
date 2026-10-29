package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;

/** Actual request and proof codecs; physical test inputs remain unqualified DATA. */
final class HostModePackageContractTest {
    @TempDir Path root;
    @Test void exactThreeModesRoundTripThroughActualPackageRequestAndNativeProofCodecs()throws Exception {
        var mapper=ControlBuild.strictMapper();
        for(HostMode mode:HostMode.values()) {
            var request=JavaRuntimePackageTest.request(root.resolve(mode.name()),mode);
            var raw=JavaRuntimePackageCodec.encodeRequest(request);
            assertEquals(request,JavaRuntimePackageCodec.decodeRequest(raw));
            var closure=new java.util.ArrayList<>(request.nativeInputs().mandatoryEvidence());closure.add(request.hostConfiguration());
            var proof=new NativeProof(request.machineId(),mode,request.hostConfiguration(),request.nativeInputs(),List.copyOf(closure));
            assertEquals(proof,JavaRuntimePackageCodec.decode(JavaRuntimePackageCodec.encode(proof),NativeProof.class));
            for(var wrong:List.of(com.fasterxml.jackson.databind.node.NullNode.instance,
                    com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                    com.fasterxml.jackson.databind.node.IntNode.valueOf(1),
                    com.fasterxml.jackson.databind.node.TextNode.valueOf("complete-migration"))) {
                var bad=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(raw);
                ((com.fasterxml.jackson.databind.node.ObjectNode)bad.get("launch")).set("mode",wrong);
                assertThrows(java.io.IOException.class,()->JavaRuntimePackageCodec.decodeRequest(mapper.writeValueAsBytes(bad)));
            }
            var missing=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(raw);
            ((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("launch")).remove("mode");
            assertThrows(java.io.IOException.class,()->JavaRuntimePackageCodec.decodeRequest(mapper.writeValueAsBytes(missing)));
        }
    }
}
