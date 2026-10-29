package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.Config;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import static org.xar.ck3.control.build.ManualBuildCapacityReleaseProducer.*;

/** Persistent producer -> actual ControlBuild manual reader tests. All authorities here are software fixtures,
 * never a real capacity reservation, original issuer delegation or permission to execute Maven.
 */
final class ManualBuildCapacityReleaseProducerTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(AT.plusSeconds(10),ZoneOffset.UTC);
    private int sequence;
    private record Fixture(Request request,Path base) {}

    @Test void typedProducerEmitsTheExactExistingManualWireAndActualReaderAcceptsIt()throws Exception {
        var fixture=fixture();var request=fixture.request();
        Prepared prepared=ManualBuildCapacityReleaseProducer.prepare(request,CLOCK);
        prepared.release().verify();
        assertEquals(PreparationStatus.PREPARED_EXISTING_MANUAL_READER_ACCEPTED,prepared.status());
        assertSame(request.issuer(),prepared.issuer());
        assertEquals(request.config().capacityRelease().toString(),prepared.release().path());
        var root=read(request);
        assertEquals(SCHEMA,root.path("schema").textValue());
        assertEquals(ManualStatus.RELEASED_JAVA_PHASE1_BOUNDED_BUILD_AND_LOCAL_SERVICE.name(),root.path("status").textValue());
        assertEquals(request.config().ownerTask(),root.path("single_Maven_writer").textValue());
        assertEquals(request.issuer().authorization(),root.path("preparation_narrative").path("authorization").textValue());
        assertNotEquals(root.path("status").textValue(),request.issuer().authorization());
        assertEquals(request.config().workRoot().resolve("m2").toString(),root.path("Maven_repository").textValue());
        assertEquals(request.config().workRoot().resolve("build").toString(),root.path("build_root").textValue());
        assertEquals(request.config().workRoot().resolve("scratch").toString(),root.path("temporary_root").textValue());
        assertEquals(Set.of("path","bytes","sha256"),keys(root.get("policy_ref")));
        assertEquals(Set.of("path","bytes","sha256"),keys(root.path("preparation_narrative").get("original_authorization_ref")));
        assertEquals(request.volumes().getFirst().requiredFree(),root.path("volumes").path(request.volumes().getFirst().root().toString()).path("required_free").longValue());
        // No private Lease is fabricated or inspected: use the exact production reader as the validator.
        ControlBuild.readLeaseAt(request.config(),request.machineId(),CLOCK.instant());
    }

    @Test void originalNarrativeStatusWrongWriterMachineAndPartTokenAreRejectedByTheActualReader()throws Exception {
        for(String corruption:List.of("narrative-status","writer","machine","bool-part","float-part","missing-part","path","formula","policy-ref")) {
            var request=fixture().request();ManualBuildCapacityReleaseProducer.prepare(request,CLOCK);var root=read(request);
            switch(corruption) {
                case "narrative-status" -> root.put("status","RELEASED_TRANSFER_UNSTARTED_C24_WHOLE96M_ONCE_TO_C24B_AFTER_ACTUAL_SOURCE02_PASS");
                case "writer" -> root.put("single_Maven_writer","different-software-writer");
                case "machine" -> root.put("machine_id","different-software-machine");
                case "bool-part" -> ((ObjectNode)root.get("parts")).put("m2",true);
                case "float-part" -> ((ObjectNode)root.get("parts")).put("m2",1.0);
                case "missing-part" -> ((ObjectNode)root.get("parts")).remove("m2");
                case "path" -> root.put("build_root",request.config().workRoot().resolve("wrong-build").toString());
                case "formula" -> {
                    var volume=(ObjectNode)root.get("volumes").get(request.volumes().getFirst().root().toString());
                    volume.put("required_free",volume.get("required_free").longValue()+1);
                }
                case "policy-ref" -> ((ObjectNode)root.get("policy_ref")).put("sha256","0".repeat(64));
                default -> throw new AssertionError(corruption);
            }
            write(request.config().capacityRelease(),root);
            assertThrows(IOException.class,()->ControlBuild.readLeaseAt(request.config(),request.machineId(),CLOCK.instant()),corruption);
        }
    }

    @Test void invalidApprovedRootsRetainAnExactFailedCandidateAndCreateNewPreventsAnyOverwrite()throws Exception {
        var good=fixture().request();
        var bad=copy(good,List.of(good.config().sourceRoot()));
        var failure=assertThrows(PreparationRejectedException.class,()->ManualBuildCapacityReleaseProducer.prepare(bad,CLOCK));
        assertEquals(good.config().capacityRelease().toString(),failure.retainedCandidate().path());
        failure.retainedCandidate().verify();
        byte[] rejected=Files.readAllBytes(good.config().capacityRelease());
        assertArrayEquals(ManualBuildCapacityReleaseProducer.encode(bad),rejected);
        assertThrows(FileAlreadyExistsException.class,()->ManualBuildCapacityReleaseProducer.prepare(good,CLOCK));
        assertArrayEquals(rejected,Files.readAllBytes(good.config().capacityRelease()));
        assertThrows(IOException.class,()->ControlBuild.readLeaseAt(good.config(),good.machineId(),CLOCK.instant()));
    }

    @Test void expiredPreparationAndSourceDriftFailBeforeCreatingACandidate()throws Exception {
        var expired=fixture().request();
        assertThrows(IOException.class,()->ManualBuildCapacityReleaseProducer.prepare(expired,Clock.fixed(expired.reviewAt(),ZoneOffset.UTC)));
        assertFalse(Files.exists(expired.config().capacityRelease()));
        var future=fixture().request();
        assertThrows(IOException.class,()->ManualBuildCapacityReleaseProducer.prepare(future,Clock.fixed(future.observedAt().minusNanos(1),ZoneOffset.UTC)));
        assertFalse(Files.exists(future.config().capacityRelease()));
        var drift=fixture().request();Files.writeString(Path.of(drift.issuer().authorizationSource().path()),"changed software issuer source");
        assertThrows(IOException.class,()->ManualBuildCapacityReleaseProducer.prepare(drift,CLOCK));
        assertFalse(Files.exists(drift.config().capacityRelease()));
    }

    @Test void malformedTypedBudgetOverflowDuplicateRootsAndHeapNeverBecomeReleasedInput()throws Exception {
        assertThrows(IllegalArgumentException.class,()->new Parts(0,1,1,1,1,1));
        assertThrows(IllegalArgumentException.class,()->new Memory(1024,1024));
        assertThrows(ArithmeticException.class,()->new Volume(temporary.toAbsolutePath(),Long.MAX_VALUE,1,1,Long.MAX_VALUE,1,1,1,Long.MAX_VALUE));
        var request=fixture().request();
        assertThrows(IllegalArgumentException.class,()->copy(request,List.of(temporary.toAbsolutePath(),temporary.toAbsolutePath())));
        assertThrows(IllegalArgumentException.class,()->new Request(request.config(),request.machineId(),request.reviewAt(),request.observedAt(),
                request.issuer(),request.policyRef(),request.approvedOutputRoots(),request.parts(),request.volumes(),request.memory()));
        assertFalse(Files.exists(request.config().capacityRelease()));
    }

    @Test void successfulPreparationStillRequiresLiveReaderRevalidationAndPreservesPureThreeFieldReferences()throws Exception {
        var request=fixture().request();var prepared=ManualBuildCapacityReleaseProducer.prepare(request,CLOCK);
        assertThrows(IOException.class,()->ControlBuild.readLeaseAt(request.config(),request.machineId(),request.reviewAt()));
        byte[] changed=Files.readAllBytes(request.config().capacityRelease());
        Files.write(request.config().capacityRelease(),java.util.Arrays.copyOf(changed,changed.length+1));
        assertThrows(IOException.class,prepared.release()::verify);
        var mapper=ControlBuild.strictMapper();
        var ref=mapper.valueToTree(prepared.release());
        assertEquals(Set.of("path","bytes","sha256"),keys(ref));
        assertEquals(prepared.release(),mapper.treeToValue(ref,FileRef.class));
        ((ObjectNode)ref).put("status","not-part-of-pure-three");
        assertThrows(IOException.class,()->mapper.treeToValue(ref,FileRef.class));
    }

    private Fixture fixture()throws Exception {
        Path base=Files.createDirectory(temporary.resolve("software-case-"+sequence++)).toRealPath();
        Path source=Files.createDirectory(base.resolve("source")),work=Files.createDirectory(base.resolve("work"));
        Path policy=base.resolve("software-policy.json"),authorization=base.resolve("software-issuer-source.txt");
        Files.writeString(policy,"{\"schema\":\"xar-storage-retention-policy-v1\"}",StandardCharsets.UTF_8);
        Files.writeString(authorization,"software fixture provenance only; no actual budget or Maven permission",StandardCharsets.UTF_8);
        var config=new Config(source,work,base.resolve("manual-capacity.json"),"software-manual-reader",
                "software-test-writer",null,base,"3.10.0",10,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        var issuer=new IssuerDomain("software-test-owner","software-test-issuer",FileRef.measure(authorization),
                "software narrative retained separately from wire status","reader preflight only; no execution authority");
        var volume=new Volume(base,100_000_000,80_000_000,1_000_000,2_000_000,3_000_000,4_000_000,5_000_000,100_000_000);
        var request=new Request(config,"software-test-machine",AT,AT.plusSeconds(60),issuer,FileRef.measure(policy),List.of(base),
                new Parts(1_000_000,1_000_000,1_000_000,1_000_000,1_000_000,1_000_000),List.of(volume),new Memory(128_000_000,64_000_000));
        return new Fixture(request,base);
    }
    private static Request copy(Request request,List<Path> approved) {
        return new Request(request.config(),request.machineId(),request.observedAt(),request.reviewAt(),request.issuer(),
                request.policyRef(),approved,request.parts(),request.volumes(),request.memory());
    }
    private static ObjectNode read(Request request)throws IOException {
        return (ObjectNode)ControlBuild.strictMapper().readTree(Files.readAllBytes(request.config().capacityRelease()));
    }
    private static void write(Path path,ObjectNode value)throws IOException {Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(value));}
    private static Set<String> keys(JsonNode value) {var result=new HashSet<String>();value.fieldNames().forEachRemaining(result::add);return Set.copyOf(result);}
}

