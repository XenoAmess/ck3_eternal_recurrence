package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Real configuration file producer/codec boundary, without Core, transport, Native or Game admission. */
final class RootHostModeConfigurationContractTest {
    @TempDir Path root;
    private static ExactRef original(Path path,String bytes)throws Exception {
        Files.writeString(path,bytes);var actual=ControlBuild.FileRef.measure(path);
        return new ExactRef(actual.path(),actual.bytes(),actual.sha256());
    }
    @Test void threeExplicitModesReachTheActualApplicationProducerAndSolePersistentCodec()throws Exception {
        for(HostMode mode:HostMode.values()) {
            Path folder=Files.createDirectory(root.resolve(mode.name()));String machine=WindowsJobProcess.currentMachineId();
            var plan=original(folder.resolve("native-plan-data.json"),"{\"source_data_only\":true}");
            var anchor=original(folder.resolve("anchor-data.json"),"{\"source_data_only\":true}");
            var writer=original(folder.resolve("writer-source.java"),"source data only");
            var actual=new RootApplicationConfiguration(machine,mode,Instant.now().plusSeconds(3600),plan,
                    new WriterContracts.Layout(folder.resolve("ledger/snapshot.json"),anchor,machine),List.of(writer),folder.resolve("artifacts"),64L<<20);
            var quoted=RootApplicationConfigurationProducer.prepare(actual,folder.resolve("application.json"),Clock.systemUTC());
            var decoded=RootApplicationConfiguration.fromJson(StrictJson.parse(quoted.bytes(),RootApplicationConfiguration.MAXIMUM_BYTES));
            assertEquals(actual,decoded);assertEquals(mode,decoded.mode());
            var modeJson=actual.toJson();
            for(var wrong:List.of(com.fasterxml.jackson.databind.node.NullNode.instance,
                    com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                    com.fasterxml.jackson.databind.node.IntNode.valueOf(1),
                    com.fasterxml.jackson.databind.node.TextNode.valueOf("complete-migration"))) {
                var bad=modeJson.deepCopy();bad.set("mode",wrong);
                assertThrows(IllegalArgumentException.class,()->RootApplicationConfiguration.fromJson(bad));
            }
            var missing=modeJson.deepCopy();missing.remove("mode");
            assertThrows(IllegalArgumentException.class,()->RootApplicationConfiguration.fromJson(missing));
            var args=new ArrayList<String>();args.add("QUOTE");args.add(machine);args.add(mode.name());args.add(actual.reviewAt().toString());
            add(args,plan);args.add(actual.ledger().snapshot().toString());add(args,anchor);args.add(actual.artifactRoot().toString());
            args.add(Long.toString(actual.maximumArtifactBytes()));args.add(folder.resolve("cli-application.json").toString());args.add("1");add(args,writer);
            assertEquals(mode,RootApplicationConfigurationProducer.arguments(args.toArray(String[]::new)).actual().mode());
            for(String invalid:List.of("complete-migration","complete_migration","unknown","true")) {
                var bad=new ArrayList<>(args);bad.set(2,invalid);
                assertThrows(IllegalArgumentException.class,()->RootApplicationConfigurationProducer.arguments(bad.toArray(String[]::new)));
            }
            assertFalse(Files.exists(folder.resolve("application.json")));assertFalse(Files.exists(folder.resolve("cli-application.json")));
        }
    }
    private static void add(ArrayList<String> args,ExactRef ref) {
        args.add(ref.path());args.add(Long.toString(ref.bytes()));args.add(ref.sha256());
    }
}
