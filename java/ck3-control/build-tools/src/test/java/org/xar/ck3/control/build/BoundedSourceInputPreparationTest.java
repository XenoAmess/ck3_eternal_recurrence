package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.BoundedSourceInputGuard.Manifest;
import org.xar.ck3.control.build.BoundedSourceInputGuard.PreparationRequest;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Future native software-fixture producer -> actual guard regressions; no build or operational authority. */
final class BoundedSourceInputPreparationTest {
    @TempDir Path temporary;
    private static final String OWNER="/root/lifecycle";
    private int sequence;
    private record Fixture(PreparationRequest request,Clock clock,Instant observed) {}

    @Test void actualTypedProducerUsesCanonicalUtcAndActualMachineThenClosesTheSoleNativeGuard()throws Exception {
        var fixture=fixture();var request=fixture.request();
        var prepared=BoundedSourceInputGuard.prepare(request,fixture.clock());
        prepared.manifestRef().verify();
        Manifest manifest=BoundedSourceInputGuard.decodeManifest(prepared.manifestRef(),Files.readAllBytes(request.target()));
        assertEquals(fixture.observed().toString(),manifest.observedAtUtc());
        assertEquals(request.reviewAt().toString(),manifest.reviewAtUtc());
        assertTrue(manifest.observedAtUtc().endsWith("Z"));assertTrue(manifest.reviewAtUtc().endsWith("Z"));
        assertEquals(WindowsJobProcess.currentMachineId(),manifest.machineId());
        assertEquals(request.files(),manifest.files());
        assertEquals("MATCH",prepared.readback().postcheck());
        assertEquals(request.files().size()+1,prepared.readback().observations().size());
        var mapper=ControlBuild.strictMapper();byte[] readback=mapper.writeValueAsBytes(prepared.readback());
        assertEquals(prepared.readback(),mapper.readValue(readback,BoundedSourceInputGuard.Receipt.class));
        assertArrayEquals(BoundedSourceInputGuard.encodeManifest(manifest),Files.readAllBytes(request.target()));
        // The preparation lease is closed. The protected operation must acquire its own complete live lease.
        try(var live=BoundedSourceInputGuard.open(prepared.manifestRef(),OWNER)){live.requireExactInputs(request.files());}
    }

    @Test void exactTableAndRealCliArgumentAdapterReachTheSamePublisherWithoutCallerMachineOrObservedFields()throws Exception {
        var fixture=fixture();var table=table(fixture.request().files());
        String[] args={fixture.request().target().toString(),OWNER,fixture.request().reviewAt().toString(),table.path(),Long.toString(table.bytes()),table.sha256()};
        var prepared=BoundedSourceInputGuard.prepareArguments(args,fixture.clock());
        assertEquals("MATCH",prepared.readback().postcheck());
        var manifest=BoundedSourceInputGuard.decodeManifest(prepared.manifestRef(),Files.readAllBytes(fixture.request().target()));
        assertEquals(fixture.request().files(),manifest.files());
        assertEquals(fixture.observed().toString(),manifest.observedAtUtc());
        byte[] before=Files.readAllBytes(fixture.request().target());
        assertThrows(FileAlreadyExistsException.class,()->BoundedSourceInputGuard.prepareArguments(args,fixture.clock()));
        assertArrayEquals(before,Files.readAllBytes(fixture.request().target()));
        var extra=java.util.Arrays.copyOf(args,7);extra[6]="caller-machine-forbidden";
        assertThrows(IOException.class,()->BoundedSourceInputGuard.prepareArguments(extra,fixture.clock()));
    }

    @Test void originalPlusOffsetObservationAndReviewRemainRejectedBeforeAnyPreparationCanAuthorizeThem()throws Exception {
        var fixture=fixture();var table=table(fixture.request().files());
        String noncanonicalReview=fixture.request().reviewAt().toString().replace("Z","+00:00");
        assertThrows(IOException.class,()->BoundedSourceInputGuard.prepareFromTable(table,fixture.request().target(),OWNER,noncanonicalReview,fixture.clock()));
        assertFalse(Files.exists(fixture.request().target()));
        assertThrows(IllegalArgumentException.class,()->new Manifest(BoundedSourceInputGuard.SCHEMA,WindowsJobProcess.currentMachineId(),OWNER,
                fixture.observed().toString().replace("Z","+00:00"),fixture.request().reviewAt().toString(),fixture.request().files()));
        var mapper=ControlBuild.strictMapper();
        ObjectNode original=mapper.valueToTree(new Manifest(BoundedSourceInputGuard.SCHEMA,WindowsJobProcess.currentMachineId(),OWNER,
                fixture.observed().toString(),fixture.request().reviewAt().toString(),fixture.request().files()));
        original.put("observed_at_utc",fixture.observed().toString().replace("Z","+00:00"));
        Path retained=temporary.resolve("retained-original-offset.json");Files.write(retained,mapper.writeValueAsBytes(original));
        FileRef pin=FileRef.measure(retained);
        assertThrows(IOException.class,()->BoundedSourceInputGuard.decodeManifest(pin,Files.readAllBytes(retained)));
        assertThrows(IOException.class,()->BoundedSourceInputGuard.open(pin,OWNER));pin.verify();
    }

    @Test void tableBodyShaAndStrictPureThreeFieldsRejectWrongMissingNullAndNonintegralInputsBeforeCreate()throws Exception {
        for(String corruption:List.of("hash","unknown","bool","float","missing","null","null-list","object","bytes-lexeme")) {
            var fixture=fixture();var mapper=ControlBuild.strictMapper();
            ArrayNode rows=mapper.valueToTree(fixture.request().files());
            ObjectNode row=(ObjectNode)rows.get(0);
            switch(corruption) {
                case "unknown" -> row.put("machine_id","caller-machine-forbidden");
                case "bool" -> row.put("bytes",true);case "float" -> row.put("bytes",1.0);
                case "missing" -> row.remove("sha256");case "null" -> row.putNull("path");
                default -> { }
            }
            Path path=temporary.resolve("table-"+(sequence++)+".json");
            byte[] bytes=switch(corruption) {
                case "null-list" -> "null".getBytes(java.nio.charset.StandardCharsets.UTF_8);
                case "object" -> "{}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
                default -> mapper.writeValueAsBytes(rows);
            };
            Files.write(path,bytes);var table=FileRef.measure(path);
            if(corruption.equals("hash"))table=new FileRef(table.path(),table.bytes(),"0".repeat(64));
            var exact=table;
            if(corruption.equals("bytes-lexeme")) {
                String[] args={fixture.request().target().toString(),OWNER,fixture.request().reviewAt().toString(),table.path(),"+"+table.bytes(),table.sha256()};
                assertThrows(IOException.class,()->BoundedSourceInputGuard.prepareArguments(args,fixture.clock()));
            } else assertThrows(IOException.class,()->BoundedSourceInputGuard.prepareFromTable(exact,fixture.request().target(),OWNER,fixture.request().reviewAt().toString(),fixture.clock()),corruption);
            assertFalse(Files.exists(fixture.request().target()),corruption);
        }
    }

    @Test void sourceDriftAndExpiredWindowFailBeforeCreateWhileExpiryAfterCreateRetainsExactCandidate()throws Exception {
        var drift=fixture();Files.writeString(Path.of(drift.request().files().getFirst().path()),"changed");
        assertThrows(IOException.class,()->BoundedSourceInputGuard.prepare(drift.request(),drift.clock()));
        assertFalse(Files.exists(drift.request().target()));
        var expired=fixture();
        assertThrows(IOException.class,()->BoundedSourceInputGuard.prepare(expired.request(),Clock.fixed(expired.request().reviewAt(),ZoneOffset.UTC)));
        assertFalse(Files.exists(expired.request().target()));
        for(boolean afterGuard:List.of(false,true)) {
            var fixture=fixture();var calls=new java.util.concurrent.atomic.AtomicInteger();
            int expireAt=fixture.request().files().size()+2+(afterGuard?1:0);
            Clock advancing=new Clock() {
                public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
                public Clock withZone(java.time.ZoneId zone){if(!ZoneOffset.UTC.equals(zone))throw new IllegalArgumentException("UTC fixture only");return this;}
                public Instant instant(){return calls.getAndIncrement()<expireAt?fixture.observed():fixture.request().reviewAt();}
            };
            var failure=assertThrows(BoundedSourceInputGuard.PreparationRejectedException.class,()->BoundedSourceInputGuard.prepare(fixture.request(),advancing));
            failure.retainedCandidate().verify();
            byte[] originalCandidate=Files.readAllBytes(fixture.request().target());
            var encodedFailure=new ByteArrayOutputStream();
            try(var output=new ObjectOutputStream(encodedFailure)){output.writeObject(failure);}
            BoundedSourceInputGuard.PreparationRejectedException restored;
            try(var input=new ObjectInputStream(new ByteArrayInputStream(encodedFailure.toByteArray()))){
                restored=assertInstanceOf(BoundedSourceInputGuard.PreparationRejectedException.class,input.readObject());
            }
            assertEquals(failure.retainedCandidate(),restored.retainedCandidate());
            assertEquals(failure.getMessage(),restored.getMessage());
            assertArrayEquals(failure.getStackTrace(),restored.getStackTrace());
            assertNotNull(restored.getCause());
            assertEquals(failure.getCause().getClass(),restored.getCause().getClass());
            assertEquals(failure.getCause().getMessage(),restored.getCause().getMessage());
            assertArrayEquals(failure.getCause().getStackTrace(),restored.getCause().getStackTrace());
            restored.retainedCandidate().verify();
            assertArrayEquals(originalCandidate,Files.readAllBytes(fixture.request().target()));
            assertEquals(OWNER,BoundedSourceInputGuard.decodeManifest(failure.retainedCandidate(),Files.readAllBytes(fixture.request().target())).taskOwner());
            assertThrows(FileAlreadyExistsException.class,()->BoundedSourceInputGuard.prepare(fixture.request(),fixture.clock()));
        }
    }

    @Test void finiteLogicalWireAndFileCountBoundsRemainMandatoryAndExistingManifestContractsAreNotWeakened()throws Exception {
        var fixture=fixture();var first=fixture.request().files().getFirst();
        assertThrows(IllegalArgumentException.class,()->new PreparationRequest(fixture.request().target(),OWNER,fixture.request().reviewAt(),List.of(first,first)));
        var tooMany=new ArrayList<FileRef>();for(int i=0;i<=BoundedSourceInputGuard.MAX_FILES;i++)tooMany.add(first);
        assertThrows(IllegalArgumentException.class,()->new PreparationRequest(fixture.request().target(),OWNER,fixture.request().reviewAt(),tooMany));
        var oversized=new FileRef(first.path(),BoundedSourceInputGuard.MAX_LOGICAL_BYTES+1,first.sha256());
        assertThrows(IllegalArgumentException.class,()->BoundedSourceInputGuard.prepare(new PreparationRequest(fixture.request().target(),OWNER,fixture.request().reviewAt(),List.of(oversized)),fixture.clock()));
        var tooLargeTable=new FileRef(first.path(),BoundedSourceInputGuard.MAX_MANIFEST_BYTES+1,first.sha256());
        assertThrows(IOException.class,()->BoundedSourceInputGuard.prepareFromTable(tooLargeTable,fixture.request().target(),OWNER,fixture.request().reviewAt().toString(),fixture.clock()));
        assertFalse(Files.exists(fixture.request().target()));
    }

    private Fixture fixture()throws Exception {
        Path base=Files.createDirectory(temporary.resolve("case-"+sequence++)).toRealPath();
        Path a=base.resolve("a"),b=base.resolve("b");Files.writeString(a,"source-a");Files.writeString(b,"source-b");
        Instant observed=Instant.now().minusSeconds(1);
        var request=new PreparationRequest(base.resolve("new-manifest.json"),OWNER,observed.plusSeconds(600),List.of(FileRef.measure(b),FileRef.measure(a)));
        return new Fixture(request,Clock.fixed(observed,ZoneOffset.UTC),observed);
    }
    private FileRef table(List<FileRef> inputs)throws Exception {
        Path path=temporary.resolve("input-table-"+(sequence++)+".json");
        Files.write(path,ControlBuild.strictMapper().writeValueAsBytes(inputs));return FileRef.measure(path);
    }
}
