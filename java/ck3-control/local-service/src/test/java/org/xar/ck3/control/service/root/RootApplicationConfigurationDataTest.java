package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Actual Main configuration read chain only; no Core, ledger, process or Game permission is produced. */
final class RootApplicationConfigurationDataTest {
    @TempDir Path root;
    private static final String SHA="a".repeat(64);
    private static final Clock CLOCK=Clock.fixed(Instant.parse("2030-01-01T00:00:00Z"),ZoneOffset.UTC);
    private RootApplicationConfiguration configuration() {
        String machine="application-fixture-machine";
        return new RootApplicationConfiguration(machine,HostMode.COMPLETE_MIGRATION,Instant.parse("2020-01-01T00:00:00Z"),
                new ExactRef(root.resolve("removed-native-plan.json").toString(),1,SHA),
                new WriterContracts.Layout(root.resolve("ledger/snapshot.json"),new ExactRef(root.resolve("removed-anchor.json").toString(),1,SHA),machine),
                List.of(new ExactRef(root.resolve("removed-writer.java").toString(),1,SHA)),root.resolve("artifacts"),1048576);
    }
    private FileRef write(String name,byte[] bytes)throws IOException {
        Path target=root.resolve(name);Files.write(target,bytes,java.nio.file.StandardOpenOption.CREATE_NEW);return FileRef.measure(target);
    }
    private FileRef actual()throws IOException {return write("application.json",StrictJson.canonical(configuration().toJson(),RootApplicationConfiguration.MAXIMUM_BYTES));}
    @Test void actualMainReadAndRequireCurrentConsumeApplicationDataWithoutHistoricalQualification()throws Exception {
        var exact=actual();var read=RootApplicationConfiguration.readExact(exact);read.requireCurrent(CLOCK);
        assertEquals(configuration(),read);read.requireCurrent(Clock.fixed(Instant.parse("2040-01-01T00:00:00Z"),ZoneOffset.UTC));
        assertThrows(NullPointerException.class,()->read.requireCurrent(null));
        assertFalse(Files.exists(Path.of(read.nativeLaunchPlan().path())));assertFalse(Files.exists(Path.of(read.ledger().anchor().path())));
        assertFalse(Files.exists(Path.of(read.writerSources().getFirst().path())));assertFalse(Files.exists(read.ledger().snapshot()));assertFalse(Files.exists(read.artifactRoot()));
    }
    @Test void sameDecodedValueCannotReplaceRecordedBytesAndRequiredCountBoundOrSha()throws Exception {
        var exact=actual();Path target=Path.of(exact.path());byte[] bytes=Files.readAllBytes(target);var mapper=ControlBuild.strictMapper();
        ObjectNode reordered=(ObjectNode)mapper.readTree(bytes);var schema=reordered.remove("schema");reordered.set("schema",schema);byte[] changed=mapper.writeValueAsBytes(reordered);
        assertFalse(Arrays.equals(bytes,changed));assertEquals(configuration(),RootApplicationConfiguration.fromJson(StrictJson.parse(changed,RootApplicationConfiguration.MAXIMUM_BYTES)));
        Files.write(target,changed);assertThrows(IOException.class,()->RootApplicationConfiguration.readExact(exact));
        Files.write(target,bytes);assertThrows(IOException.class,()->RootApplicationConfiguration.readExact(new FileRef(exact.path(),exact.bytes()+1,exact.sha256())));
        assertThrows(IOException.class,()->RootApplicationConfiguration.readExact(new FileRef(exact.path(),RootApplicationConfiguration.MAXIMUM_BYTES+1L,exact.sha256())));
    }
    @Test void identicalApplicationBytesRemainReadableAfterFileReplacement()throws Exception {
        var exact=actual();Path target=Path.of(exact.path()),replacement=root.resolve("replacement.json");
        Files.copy(target,replacement);Files.move(replacement,target,StandardCopyOption.REPLACE_EXISTING);
        assertEquals(configuration(),RootApplicationConfiguration.readExact(exact));
    }
    @Test void actualDataReaderKeepsTheSoleStrictSchemaModeAndNumericContract()throws Exception {
        ObjectNode original=configuration().toJson();var bad=new java.util.ArrayList<ObjectNode>();
        var missing=original.deepCopy();missing.remove("mode");bad.add(missing);
        var nil=original.deepCopy();nil.putNull("native_launch_plan");bad.add(nil);
        var unknown=original.deepCopy();unknown.put("runtime_permission",true);bad.add(unknown);
        var version=original.deepCopy();version.put("schema","old");bad.add(version);
        var mode=original.deepCopy();mode.put("mode",true);bad.add(mode);
        var bool=original.deepCopy();bool.put("maximum_artifact_bytes",true);bad.add(bool);
        var fraction=original.deepCopy();fraction.put("maximum_artifact_bytes",1.0);bad.add(fraction);
        var empty=original.deepCopy();empty.putArray("writer_sources");bad.add(empty);
        int count=0;for(var value:bad){var exact=write("invalid-"+(count++)+".json",ControlBuild.strictMapper().writeValueAsBytes(value));assertThrows(IOException.class,()->RootApplicationConfiguration.readExact(exact));}
        var duplicate=write("duplicate.json",("{\"schema\":\"old\","+new String(StrictJson.canonical(original),java.nio.charset.StandardCharsets.UTF_8).substring(1)).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertThrows(IOException.class,()->RootApplicationConfiguration.readExact(duplicate));
    }
}
