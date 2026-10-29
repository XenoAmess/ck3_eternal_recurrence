package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.LaunchSettings;

/** Real negative producer entry and exact memory arithmetic. No Native/package positive is fabricated. */
final class RootRuntimePackageInputsProducerTest {
    @TempDir Path root;
    @Test void invocationBudgetUsesSelectedHeapRatherThanStageDefault() {
        var launch=new LaunchSettings(HostMode.COMPLETE_MIGRATION,8089,64L<<20,256L<<20,
                root.resolve("temp").toString(),root.resolve("temp/jna").toString());
        assertThrows(IllegalArgumentException.class,()->RootRuntimePackageInputsProducer.requireCommandMemory(launch,(384L<<20)-1));
        RootRuntimePackageInputsProducer.requireCommandMemory(launch,384L<<20);
        assertThrows(IllegalArgumentException.class,()->RootRuntimePackageInputsProducer.requireCommandMemory(launch,(32L<<30)+1));
    }
    @Test void malformedExistingParametersCannotPublishRequestQuoteOrPermit()throws Exception {
        Path metadata=root.resolve("runtime-inputs/generation");
        Path file=root.resolve("parameters.json");Files.writeString(file,"{}");
        FileRef pin=FileRef.measure(file);
        assertThrows(IOException.class,()->RootRuntimePackageInputsProducer.prepare(pin));
        assertFalse(Files.exists(metadata));
        try(var entries=Files.list(root)){assertEquals(List.of(file),entries.toList());}
    }
    @Test void missingReviewOrPermitDoesNotConstructAnActualCiBinding()throws Exception {
        Path file=root.resolve("empty-review.json");Files.writeString(file,"{}");
        var pin=FileRef.measure(file);Path output=root.resolve("binding.json");
        assertThrows(IOException.class,()->RootRuntimePackageInputsProducer.bindPermit(pin,pin,pin,List.of(),output));
        assertFalse(Files.exists(output));
        assertThrows(IllegalArgumentException.class,()->RootRuntimePackageInputsProducer.main(new String[]{"--prepare"}));
    }
    @Test void typedReviewDataRoundtripRejectsMissingUnknownAndCoercedFields()throws Exception {
        Path file=root.resolve("unqualified-metadata.json");Files.writeString(file,"{}");var pin=FileRef.measure(file);
        // This DTO fixture is not a genuine ReviewAvailable, permit or actual package proof.
        var data=new RootRuntimePackageInputsProducer.Review(RootRuntimePackageInputsProducer.REVIEW_SCHEMA,pin,pin,
                new org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Quote(1,2,1,16L<<20),4096,4096,(16L<<20)+8192);
        var mapper=org.xar.ck3.control.build.ControlBuild.strictMapper();byte[] raw=mapper.writeValueAsBytes(data);
        assertEquals(data,mapper.readValue(raw,RootRuntimePackageInputsProducer.Review.class));
        var bad=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(raw);bad.remove("request_ref");
        assertThrows(IOException.class,()->mapper.treeToValue(bad,RootRuntimePackageInputsProducer.Review.class));
        var unknown=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(raw);unknown.put("actual_status","PASS");
        assertThrows(IOException.class,()->mapper.treeToValue(unknown,RootRuntimePackageInputsProducer.Review.class));
        var coerced=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(raw);coerced.put("allocation_upper_bytes",true);
        assertThrows(IOException.class,()->mapper.treeToValue(coerced,RootRuntimePackageInputsProducer.Review.class));
    }
    @Test void publicAllocationApiRequiresGenuinePrivateReview() {
        assertThrows(NullPointerException.class,()->JavaRuntimePackage.allocationUpperBytes((JavaRuntimePackage.ReviewAvailable)null,4096,4096));
    }
}

