package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual temporary file custody is exercised, never a qualified Native cut or Game authority. */
class RootRuntimeMaaOriginalsTest {
    @TempDir Path root;
    private static final List<RootRuntimeNativeOriginals.Role> MAA=List.of(RootRuntimeNativeOriginals.Role.REGULAR_MAA_PRODUCER,
            RootRuntimeNativeOriginals.Role.REGULAR_MAA_MAILBOX,RootRuntimeNativeOriginals.Role.REGULAR_MAA_CREATE,RootRuntimeNativeOriginals.Role.REGULAR_MAA_BUILD4_BINDING);
    @Test void allRequiredOriginalsRetainTheirNativeIdentity()throws IOException {
        var entries=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values()){
            Path target=root.resolve(Path.of(role.repositoryRelative()).getFileName());Files.write(target,("temporary custody fixture "+role.name()).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            entries.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),FileRef.measure(target)));
        }
        Clock clock=Clock.systemUTC();var value=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,
                WindowsJobProcess.currentMachineId(),clock.instant().minusSeconds(1).toString(),clock.instant().plusSeconds(3600).toString(),entries);
        byte[] encoded=RootRuntimeNativeOriginals.encode(value);Path path=root.resolve("native-originals-v3.json");Files.write(path,encoded);
        var bound=RootRuntimeNativeOriginals.readExact(FileRef.measure(path),clock);assertEquals(RootRuntimeNativeOriginals.Role.values().length,entries.size());
        for(var role:MAA)assertEquals(value.source(role).exact(),bound.source(role));
        assertEquals(RootRuntimeNativeOriginals.Role.values().length+1,bound.retainedOriginals().size());bound.requireCurrent(clock);
        Path changed=Path.of(bound.source(RootRuntimeNativeOriginals.Role.REGULAR_MAA_CREATE).path());Files.writeString(changed,"different actual source");
        assertThrows(IOException.class,()->bound.requireCurrent(clock));
    }
    @Test void oldSchemaCannotSilentlyOmitRequiredMaaNativeAndPythonProvenance()throws IOException {
        var entries=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values())entries.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),
                new FileRef(root.resolve(Path.of(role.repositoryRelative()).getFileName()).toString(),7,"1".repeat(64))));
        var configuration=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,WindowsJobProcess.currentMachineId(),
                "2026-10-24T01:00:00Z","2026-10-24T02:00:00Z",entries);
        var encoded=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeNativeOriginals.encode(configuration));
        assertEquals(configuration,RootRuntimeNativeOriginals.decode(StrictJson.canonical(encoded)));
        encoded.put("schema","xar.java-root-native-originals/v1");
        assertThrows(IOException.class,()->RootRuntimeNativeOriginals.decode(StrictJson.canonical(encoded)));
        var missing=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeNativeOriginals.encode(configuration));
        var rows=(com.fasterxml.jackson.databind.node.ArrayNode)missing.get("originals");
        for(int index=0;index<rows.size();index++)if(rows.get(index).get("role").textValue().equals(RootRuntimeNativeOriginals.Role.REGULAR_MAA_MAILBOX.name())){rows.remove(index);break;}
        assertThrows(IOException.class,()->RootRuntimeNativeOriginals.decode(StrictJson.canonical(missing)));
        assertEquals(RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON,RootRuntimeNativeOriginals.Role.REGULAR_MAA_PRODUCER.kind());
        for(var role:MAA.subList(1,4))assertEquals(RootRuntimeSelectedSources.OriginalKind.NATIVE_CPP,role.kind());
    }
    @Test void riteSourcesAreMandatoryAndCannotReuseJavaOrWrongNativeSource()throws IOException {
        var rows=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values())rows.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),
                new FileRef(root.resolve(Path.of(role.repositoryRelative()).getFileName()).toString(),9,"2".repeat(64))));
        var source=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,WindowsJobProcess.currentMachineId(),
                "2026-10-24T02:00:00Z","2026-10-24T03:00:00Z",rows);
        var encoded=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeNativeOriginals.encode(source));
        encoded.put("schema","xar.java-root-native-originals/v2");
        assertThrows(IOException.class,()->RootRuntimeNativeOriginals.decode(StrictJson.canonical(encoded)));
        rows.removeIf(row->row.role()==RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_MAILBOX_HEADER);
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,
                WindowsJobProcess.currentMachineId(),"2026-10-24T02:00:00Z","2026-10-24T03:00:00Z",rows));
        assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Original(
                RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_WIRE,RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_WIRE.repositoryRelative(),
                new FileRef(root.resolve("RiteCreationCodec.java").toString(),9,"2".repeat(64))));
    }

    @Test void actionHistoryPolicyOriginalsAreMandatoryPythonAndOldV3CannotOmitThem()throws IOException {
        var rows=new ArrayList<RootRuntimeNativeOriginals.Original>();
        for(var role:RootRuntimeNativeOriginals.Role.values())rows.add(new RootRuntimeNativeOriginals.Original(role,role.repositoryRelative(),
                new FileRef(root.resolve(Path.of(role.repositoryRelative()).getFileName()).toString(),9,"3".repeat(64))));
        var value=new RootRuntimeNativeOriginals.Configuration(RootRuntimeNativeOriginals.SCHEMA,WindowsJobProcess.currentMachineId(),
                "2026-10-24T03:00:00Z","2026-10-24T04:00:00Z",rows);
        var encoded=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(RootRuntimeNativeOriginals.encode(value));
        encoded.put("schema","xar.java-root-native-originals/v3");
        assertThrows(IOException.class,()->RootRuntimeNativeOriginals.decode(StrictJson.canonical(encoded)));
        for(var role:List.of(RootRuntimeNativeOriginals.Role.WAR_DECLARED_OVERVIEW_POLICY,RootRuntimeNativeOriginals.Role.WAR_RECORDING_POLICY,
                RootRuntimeNativeOriginals.Role.BATTLE_RECORDING_POLICY)){
            assertEquals(RootRuntimeSelectedSources.OriginalKind.ORIGINAL_PYTHON,role.kind());
            var missing=new ArrayList<>(rows);missing.removeIf(row->row.role()==role);
            assertThrows(IllegalArgumentException.class,()->new RootRuntimeNativeOriginals.Configuration(value.schema(),value.machineId(),
                    value.observedAtUtc(),value.reviewAtUtc(),missing));
        }
    }

}
