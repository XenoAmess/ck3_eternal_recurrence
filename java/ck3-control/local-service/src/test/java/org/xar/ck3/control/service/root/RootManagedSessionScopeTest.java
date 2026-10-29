package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Core/finite storage guard/canonical history, without creating a Game, Complete or live authority.
 * The constructed observations below are explicitly archive DATA. They cannot call bind/withScope,
 * acquire a store lease, authorize a Native request or replace the separately required actual Game run.
 */
public final class RootManagedSessionScopeTest {
    @TempDir Path temporary;
    private record Fixture(RootApplicationConfiguration configuration, ExactRef source) { }
    private static final Instant DEADLINE=Instant.parse("2026-10-25T00:00:00Z");
    private static ExactRef ref(Path path,byte[] bytes){return new ExactRef(path.toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static Fixture initialize(Path root)throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(),"actual Windows writer and finite OS storage guard required");
        Files.createDirectories(root);String machine=WindowsJobProcess.currentMachineId();
        Path source=root.resolve("reviewed-business-source.txt"),launch=root.resolve("fixture-launch-source.json");
        byte[] sourceBytes="controlled historical DATA source; no live managed Game".getBytes(StandardCharsets.UTF_8);
        byte[] launchBytes="{\"fixture\":\"no Game launch\"}".getBytes(StandardCharsets.UTF_8);Files.write(source,sourceBytes);Files.write(launch,launchBytes);
        Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");byte[] initial=ContinuityJson.canonical(initial(machine));Files.write(snapshot,initial);Files.write(anchor,initial);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var configuration=new RootApplicationConfiguration(machine,HostMode.HTTP,Instant.now().plusSeconds(3600),ref(launch,launchBytes),
                new WriterContracts.Layout(snapshot,ref(anchor,initial),machine),List.of(ref(source,sourceBytes)),Files.createDirectory(root.resolve("archive")),32L<<20);
        Files.write(root.resolve("configuration.json"),StrictJson.canonical(configuration.toJson()));return new Fixture(configuration,ref(source,sourceBytes));
    }
    private static ObjectNode initial(String machine) {
        ObjectNode n=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",machine).put("sequence",0).put("window_id",1).put("status","running")
                .put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",1000+10958*24)
                .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0);
        n.putObject("game_binding").put("pid",121).put("creation_date","2026-10-23T01:00:00Z");n.putNull("latest_binding");
        n.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);n.put("NEXT",11559);return n;
    }
    private static Fixture read(Path root)throws IOException {
        var configuration=RootApplicationConfiguration.fromJson(StrictJson.parse(Files.readAllBytes(root.resolve("configuration.json")),1<<20));
        return new Fixture(configuration,configuration.writerSources().getFirst());
    }
    private static RootApplicationAssembly.Core open(Fixture fixture)throws IOException {
        var configuration=fixture.configuration();return RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(),Optional.empty(),StorageWriteGuardTestSupport.create(configuration.ledger()));
    }
    /** Shared real storage fixture for archive-only consumers; contains no RootContext, Game or live scope. */
    public record DataCore(RootApplicationAssembly.Core core,RootApplicationConfiguration configuration,ExactRef source) { }
    public static DataCore dataCore(Path root)throws Exception {
        Fixture fixture=initialize(root);return new DataCore(open(fixture),fixture.configuration(),fixture.source());
    }
    private static ActionCommand command(Fixture fixture,String operation,String id) {
        String machine=fixture.configuration().machineId();
        var before=new ProposalLifecycle.ObservationIdentity(machine,new GameGeneration(121,new PythonOnlyUInt64(new BigInteger("18446744073709551609"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),BigInteger.valueOf(11),BigInteger.valueOf(1000)),"native:7",BigInteger.ONE,"software-episode"),1);
        var source=new G2Source(machine,"2026-10-24T00:00:00Z","1.20.0.3",fixture.source());
        var empty=new OpportunityJson.Obj(Map.of());var expected=new ProposalLifecycle.ExpectedPostcondition(1,before,source,"software-data-observer",List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("software_data_only"),true)));
        return new ActionCommand(id,before,source,"software-session",new OperationKey(operation),empty,expected,
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(BigInteger.valueOf(73)),Set.of("foreground-window")),DEADLINE);
    }
    private static RootManagedSessionScope.Observation frame(Fixture fixture,ActionCommand command,long sequence,String digest) {
        Path root=fixture.configuration().ledger().snapshot().getParent();return new RootManagedSessionScope.Observation(fixture.configuration().machineId(),command.sessionId(),command.before(),command.source(),
                "software-no-live-launch",root,root,fixture.configuration().ledger().lock(),List.of(fixture.source()),sequence,digest,Optional.empty());
    }
    @Test void frameDataAndExactCommandAssociationPreserveUnsigned64AndCanonicalSerde()throws Exception {
        Fixture fixture=initialize(temporary.resolve("serde"));var core=open(fixture);var command=command(fixture,"prepare-grant-title-picker-v1","data-command");
        core.writer().locked(same->{var head=same.head();var observed=frame(fixture,command,head.state().sequence(),head.digest());byte[] original=RootManagedSessionScope.encode(observed);
            assertEquals(observed,RootManagedSessionScope.decode(original,command,List.of(fixture.source())));
            byte[] bound=RootManagedSessionScope.bindCommand(original,command,List.of(fixture.source()));
            var decoded=RootManagedSessionScope.verifyArchived(core,same,bound,command,List.of(fixture.source()),head.digest());
            assertEquals(Optional.of(ActionCodec.bodySha256(command)),decoded.actionBodySha256());assertEquals("18446744073709551609",decoded.before().game().creationFiletime().value().toString());
            assertArrayEquals(bound,RootManagedSessionScope.encode(decoded));assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
            assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.bindCommand(bound,command,List.of(fixture.source())));
            assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.verifyArchived(core,same,original,command,List.of(fixture.source()),head.digest()));return null;});
    }
    @Test void boundDataRejectsAnotherDomainCommandAndForeignSourceRatherThanIssuingPermission()throws Exception {
        Fixture fixture=initialize(temporary.resolve("cross-domain"));var core=open(fixture);var grant=command(fixture,"prepare-grant-title-picker-v1","grant-data");var holy=command(fixture,"create-holy-order-v1","holy-data");
        core.writer().locked(same->{var head=same.head();byte[] bound=RootManagedSessionScope.bindCommand(RootManagedSessionScope.encode(frame(fixture,grant,head.state().sequence(),head.digest())),grant,List.of(fixture.source()));
            assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.decode(bound,holy,List.of(fixture.source())));
            ExactRef foreign=new ExactRef(fixture.source().path(),fixture.source().bytes(),"b".repeat(64));assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.decode(bound,grant,List.of(foreign)));
            for(String field:List.of("schema","kind","binding","action_body_sha256","head_sequence","writer_lock")) {
                ObjectNode changed=(ObjectNode)StrictJson.parse(bound,RootManagedSessionScope.MAX_BYTES);changed.remove(field);
                assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.decode(StrictJson.canonical(changed),grant,List.of(fixture.source())),field);
            }
            for(var wrong:List.of(StrictJson.object().put("head_sequence",1),StrictJson.object().put("head_sequence","01"),StrictJson.object().put("head_sequence",true))) {
                ObjectNode changed=(ObjectNode)StrictJson.parse(bound,RootManagedSessionScope.MAX_BYTES);changed.set("head_sequence",wrong.get("head_sequence"));
                assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.decode(StrictJson.canonical(changed),grant,List.of(fixture.source())));
            }return null;});
    }
    @Test void realCoreAndSessionRejectForeignWriterAndUnknownHistoricalPredecessor()throws Exception {
        Fixture fixture=initialize(temporary.resolve("original")),foreignFixture=initialize(temporary.resolve("foreign"));var core=open(fixture);var foreign=open(foreignFixture);var command=command(fixture,"send-grant-title-picker-v1","original");
        core.writer().locked(same->{var head=same.head();byte[] original=RootManagedSessionScope.bindCommand(RootManagedSessionScope.encode(frame(fixture,command,head.state().sequence(),head.digest())),command,List.of(fixture.source()));
            assertThrows(IOException.class,()->RootManagedSessionScope.verifyArchived(foreign,same,original,command,List.of(fixture.source()),head.digest()));
            byte[] unknown=RootManagedSessionScope.bindCommand(RootManagedSessionScope.encode(frame(fixture,command,head.state().sequence()+1,"a".repeat(64))),command,List.of(fixture.source()));
            assertThrows(IOException.class,()->RootManagedSessionScope.verifyArchived(core,same,unknown,command,List.of(fixture.source()),"a".repeat(64)));
            assertThrows(IllegalArgumentException.class,()->RootManagedSessionScope.verifyArchived(core,same,original,command,List.of(fixture.source()),"a".repeat(64)));return null;});
    }
    private static void produce(Path root)throws Exception {
        Fixture fixture=initialize(root);var core=open(fixture);var command=command(fixture,"send-grant-title-picker-v1","retained-unknown-data");
        core.writer().locked(same->{var head=same.head();byte[] observed=RootManagedSessionScope.bindCommand(RootManagedSessionScope.encode(frame(fixture,command,head.state().sequence(),head.digest())),command,List.of(fixture.source()));
            var archive=core.archive().withSession(same);ExactRef original=archive.preserveMaterial(new RawJson(observed));Files.write(root.resolve("observation-ref.json"),StrictJson.canonical(original.toJson()));
            Files.write(root.resolve("command.json"),ActionCodec.encodeCommand(command));Files.writeString(root.resolve("capture-head.txt"),head.digest());return null;});
    }
    private static void cold(Path root)throws Exception {
        Fixture fixture=read(root);var core=open(fixture);byte[] initial=Files.readAllBytes(fixture.configuration().ledger().snapshot());
        var command=ActionCodec.decodeCommand(Files.readAllBytes(root.resolve("command.json")));var original=ExactRef.fromJson(StrictJson.parse(Files.readAllBytes(root.resolve("observation-ref.json")),65536));String digest=Files.readString(root.resolve("capture-head.txt"));
        core.writer().locked(same->{byte[] observed=core.archive().withSession(same).loadMaterial(original).bytes();RootManagedSessionScope.verifyArchived(core,same,observed,command,List.of(fixture.source()),digest);return null;});
        assertArrayEquals(initial,Files.readAllBytes(fixture.configuration().ledger().snapshot()),"historical DATA never starts a new action or imports a live authority");
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("exact closed mode/root required");Path root=Path.of(args[1]).toAbsolutePath().normalize();switch(args[0]){case "produce"->produce(root);case "cold"->cold(root);default->throw new IllegalArgumentException("closed mode");}
    }
    private void process(String mode,Path root)throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows());Path java=Path.of(System.getProperty("java.home"),"bin","java.exe"),log=temporary.resolve(mode+".log");
        Process child=new ProcessBuilder(java.toString(),"-cp",System.getProperty("surefire.test.class.path",System.getProperty("java.class.path")),RootManagedSessionScopeTest.class.getName(),mode,root.toString()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try{assertTrue(child.waitFor(45,TimeUnit.SECONDS),"finite independent JVM regression timeout");assertTrue(Files.size(log)<=65536,"bounded child output required");assertEquals(0,child.exitValue(),Files.readString(log));}finally{if(child.isAlive())child.destroyForcibly();}
    }
    @Test void independentColdJavaProcessReadsOnlySameWriterHistoryAndActualArchive()throws Exception {
        Path root=temporary.resolve("independent-cold");process("produce",root);process("cold",root);
    }
}
