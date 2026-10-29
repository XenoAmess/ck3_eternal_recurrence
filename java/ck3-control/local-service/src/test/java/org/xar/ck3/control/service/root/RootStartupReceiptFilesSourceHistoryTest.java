package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Exercises the production receipt binding with real JSON, ordinary storage guard and native file port. */
class RootStartupReceiptFilesSourceHistoryTest {
    @TempDir Path root;
    private static final Instant AT=Instant.parse("2026-10-29T12:00:00Z");

    @Test void retainedConfigurationSurvivesDeletedHistoricalReferences()throws Exception {
        try(var f=new Fixture(root)) {
            f.receipts.bindStartup(f.startupRef);
            var retained=f.receipts.requireCurrent();
            f.deleteHistory();
            assertSame(retained,f.receipts.requireCurrent());f.receipts.requireStartup(retained);
            f.receipts.bindStartup(f.startupRef);
            assertEquals(f.startup.toJson(),retained.toJson());
        }
    }
    @Test void initialBindingReadsRequiredJsonWithoutQualifyingHistoricalRefs()throws Exception {
        try(var f=new Fixture(root)) {
            f.deleteHistoricalInputs();
            f.receipts.bindStartup(f.startupRef);
            assertEquals(f.startup,f.receipts.requireCurrent());
        }
    }
    @Test void expiredHistoricalReviewDoesNotInvalidateRetainedConfiguration()throws Exception {
        try(var f=new Fixture(root)) {
            f.receipts.bindStartup(f.startupRef);var retained=f.receipts.requireCurrent();
            f.clock.now=AT.plus(Duration.ofDays(2));
            assertSame(retained,f.receipts.requireCurrent());f.receipts.requireStartup(retained);
        }
    }
    @Test void changedStartupFileDoesNotReplaceAlreadyDecodedConfiguration()throws Exception {
        try(var f=new Fixture(root)) {
            f.receipts.bindStartup(f.startupRef);var retained=f.receipts.requireCurrent();
            Files.writeString(f.startupPath,"changed historical startup file");
            assertSame(retained,f.receipts.requireCurrent());f.receipts.bindStartup(f.startupRef);
        }
    }
    @Test void differentReferenceAndDifferentTypedStartupRemainRejected()throws Exception {
        try(var f=new Fixture(root)) {
            assertThrows(IOException.class,f.receipts::requireCurrent);
            f.receipts.bindStartup(f.startupRef);var retained=f.receipts.requireCurrent();
            var other=f.startup.toJson();other.put("authority_id","other-authority");
            var different=f.writeStartup("other-startup.json",other);
            assertThrows(IOException.class,()->f.receipts.bindStartup(different));
            assertThrows(IOException.class,()->f.receipts.requireStartup(RootStartupConfiguration.fromJson(other)));
            assertSame(retained,f.receipts.requireCurrent());
        }
    }
    @Test void machineApplicationAndDefinitionsMustStillMatchActualConfiguration()throws Exception {
        try(var f=new Fixture(root)) {
            var foreign=f.startup.toJson();foreign.put("machine_id","foreign-machine");
            ((ObjectNode)foreign.get("source")).put("machine_id","foreign-machine");
            FileRef foreignMachine=f.writeStartup("foreign-machine.json",foreign);
            assertThrows(IOException.class,()->f.receipts.bindStartup(foreignMachine));
            FileRef other=FileRef.measure(Files.writeString(root.resolve("foreign-input.json"),"{}"));
            var application=f.startup.toJson();application.set("application",exact(other).toJson());
            FileRef foreignApplication=f.writeStartup("foreign-application.json",application);
            assertThrows(IOException.class,()->f.receipts.bindStartup(foreignApplication));
            var definitions=f.startup.toJson();definitions.set("runtime_definitions",exact(other).toJson());
            FileRef foreignDefinitions=f.writeStartup("foreign-definitions.json",definitions);
            assertThrows(IOException.class,()->f.receipts.bindStartup(foreignDefinitions));
            assertThrows(IOException.class,f.receipts::requireCurrent);
            f.receipts.bindStartup(f.startupRef);assertEquals(f.startup,f.receipts.requireCurrent());
        }
    }
    @Test void initialBindingStillRequiresDecodableActualJson()throws Exception {
        try(var f=new Fixture(root)) {
            FileRef invalid=FileRef.measure(Files.writeString(root.resolve("invalid-startup.json"),"{"));
            assertThrows(IOException.class,()->f.receipts.bindStartup(invalid));
            assertThrows(IOException.class,f.receipts::requireCurrent);
            var wrong=f.startup.toJson();wrong.put("freshness_ms",true);
            FileRef wrongType=f.writeStartup("wrong-type.json",wrong);
            assertThrows(IOException.class,()->f.receipts.bindStartup(wrongType));
            f.receipts.bindStartup(f.startupRef);assertEquals(f.startup,f.receipts.requireCurrent());
        }
    }
    @Test void retainedDataDoesNotGrantAnAbsentCoreReceiptWriteAuthority()throws Exception {
        try(var f=new Fixture(root)) {
            f.receipts.bindStartup(f.startupRef);
            Path target=f.startup.receiptDirectory().resolve("receipt.json");
            assertThrows(IOException.class,()->f.receipts.writeRuntimeReceipt(target,new byte[]{1}));
            assertFalse(Files.exists(target));
        }
    }

    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static final class MutableClock extends Clock {
        private Instant now=AT;
        @Override public ZoneId getZone(){return ZoneOffset.UTC;}
        @Override public Clock withZone(ZoneId zone){return Clock.fixed(now,zone);}
        @Override public Instant instant(){return now;}
    }
    private static final class Fixture implements AutoCloseable {
        private final Path root,applicationPath,definitionsPath,sourcePath,startupPath;
        private final MutableClock clock=new MutableClock();
        private final RootRuntimeStorageGuard guard;
        private final RootStartupReceiptFiles receipts;
        private final RootStartupConfiguration startup;
        private final FileRef startupRef;
        Fixture(Path root)throws IOException {
            this.root=root;
            Path state=Files.createDirectory(root.resolve("state")),artifacts=Files.createDirectory(root.resolve("artifacts"));
            Path continuity=Files.createDirectory(state.resolve("continuity"));
            applicationPath=Files.writeString(root.resolve("application.json"),"{}");
            definitionsPath=Files.writeString(root.resolve("definitions.json"),"{}");
            sourcePath=Files.writeString(root.resolve("historical-source.json"),"{}");
            var applicationRef=FileRef.measure(applicationPath);var definitionsRef=FileRef.measure(definitionsPath);
            var source=exact(FileRef.measure(sourcePath));String machine=WindowsJobProcess.currentMachineId();
            var app=new RootApplicationConfiguration(machine,HostMode.COMPLETE_MIGRATION,AT.plusSeconds(300),source,
                    new WriterContracts.Layout(continuity.resolve("snapshot.json"),source,machine),List.of(source),artifacts,1L<<20);
            guard=RootRuntimeStorageGuard.ordinary(app,()->{throw new IOException("no actual writer was bootstrapped");},
                    List.of(state,artifacts),1L<<20,clock);
            var files=guard.checkpointFiles(new NativeCheckpointFiles());
            receipts=new RootStartupReceiptFiles(app,applicationRef,definitionsRef,new RootCoreBoundPorts(app),guard,files,clock);
            startup=new RootStartupConfiguration(machine,AT.plusSeconds(60),applicationRef,definitionsRef,"fixture-authority",
                    new G2Source(machine,AT.toString(),"1.20.0.4",source),new RootStartupConfiguration.FreshRobert("fresh-fixture"),
                    new RootStartupConfiguration.CheckpointPaths(state.resolve("driver.json"),state.resolve("checkpoint"),
                            state.resolve("attachments"),"fixture-lineage",state.resolve("saved.ck3")),
                    new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(1),true),Duration.ofSeconds(10),
                    List.of(new BatchLimits("fixture-batch",1,Duration.ofSeconds(5),Duration.ofSeconds(2),Duration.ofMillis(10),1)),
                    artifacts.resolve("receipts"));
            startupPath=root.resolve("startup.json");startupRef=writeStartup("startup.json",startup.toJson());
        }
        FileRef writeStartup(String name,ObjectNode wire)throws IOException {
            return FileRef.measure(Files.write(root.resolve(name),StrictJson.canonical(wire,RootStartupConfiguration.MAXIMUM_BYTES)));
        }
        void deleteHistoricalInputs()throws IOException {
            Files.delete(applicationPath);Files.delete(definitionsPath);Files.delete(sourcePath);
        }
        void deleteHistory()throws IOException {deleteHistoricalInputs();Files.delete(startupPath);}
        @Override public void close()throws IOException {guard.close();}
    }
}
