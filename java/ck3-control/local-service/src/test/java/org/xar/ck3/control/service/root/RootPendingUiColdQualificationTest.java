package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/**
 * Actual temporary writer/import/archive -> cold reader historical-head and native-file identity
 * regressions. These are storage originals, not a qualified ManagedGameSession or private M3 cause.
 * A full old-terminal -> private retained-cause -> current Root positive remains MISSING_NOT_RUN.
 */
final class RootPendingUiColdQualificationTest {
    @TempDir Path temp;
    private static final String MACHINE="cold-original-writer-software-fixture";
    private static final String SCHEMA="xar.test.cold-historical-body/v1";
    private static ExactRef reference(Path file)throws IOException {
        byte[] bytes=Files.readAllBytes(file);return new ExactRef(file.toAbsolutePath().toString(),bytes.length,ActionCodec.sha256(bytes));
    }
    private record Fixture(ContinuityWriter writer,NativeOutcomeArchive archive,DomainBodies.Registration registration,Path source) {
        ExactRef importBody(ContinuityStorePort.Session same,int ordinal)throws IOException {
            byte[] bytes=StrictJson.canonical(StrictJson.object().put("schema",SCHEMA).put("ordinal",ordinal));
            ExactRef body=archive.preserveArtifact(same,bytes,4096);
            var request=new DomainBodies.ImportRequest(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,SCHEMA,body,bytes,List.of(body),"cold-body-"+ordinal);
            var prepared=same.previewImport(request);var committed=same.commitImport(prepared);same.requireCommitted(prepared,committed);
            return body;
        }
    }
    private Fixture fixture()throws IOException {
        Path directory=Files.createDirectory(temp.resolve("writer"));Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json");
        Path anchor=directory.resolve("anchor.json"),lock=directory.resolve("ROOT-CONTINUITY-WINDOW.lock");
        ObjectNode row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE)
                .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30)
                .put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                .put("automatic_recovery_count",0).put("binding_lineage_count",0);
        row.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);
        byte[] state=ContinuityJson.canonical(row);Files.write(snapshot,state);Files.write(anchor,state);Files.write(lock,new byte[0]);
        Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Path materials=Files.createDirectory(directory.resolve("artifacts"));
        Path source=directory.resolve("actual-fixture-source.txt");Files.writeString(source,"reviewed finite cold historical reader fixture",StandardCharsets.UTF_8);
        ExactRef sourceRef=reference(source);
        Path writerSource=directory.resolve("actual-fixture-writer-source.txt");
        Files.writeString(writerSource,"stable writer fixture source",StandardCharsets.UTF_8);ExactRef writerSourceRef=reference(writerSource);
        var registration=new DomainBodies.Registration(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,SCHEMA,4096,List.of(sourceRef),
                (head,previous,request,original)->{
                    var body=StrictJson.object(StrictJson.parse(original,4096),Set.of("schema","ordinal"));
                    StrictJson.require(SCHEMA.equals(StrictJson.text(body.get("schema")))&&request.slot()==DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS
                            &&request.contractSchema().equals(SCHEMA)&&java.util.Arrays.equals(original,request.producerInput())
                            &&request.evidence().equals(List.of(request.originalBody())),"actual fixture producer input/original mismatch");
                    StrictJson.integer(body.get("ordinal"),1,2);return ActionCodec.sha256(original);
                });
        var layout=new Layout(snapshot,reference(anchor),MACHINE);
        var storage=StorageWriteGuardTestSupport.create(layout);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(materials,lock,8*1024*1024),storage);
        var writer=new ContinuityWriter(layout,List.of(writerSourceRef),new TransitionAuthority(){
            @Override public String revalidate(ContinuityState head,Request request){return request.identity();}
            @Override public ContinuityState reduce(ContinuityState head,Request request){return OriginalWindowReducer.reduce(head,request);}
        },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(registration),Optional.of(artifacts),Optional.empty()),storage);
        return new Fixture(writer,new NativeOutcomeArchive(artifacts,writer),registration,source);
    }
    @Test void actualOriginalImportSurvivesLaterDomainReplacementAndReadDoesNotPublish()throws Exception {
        Fixture f=fixture();f.writer().locked(same->{
            ExactRef first=f.importBody(same,1);Head old=same.head();ExactRef second=f.importBody(same,2);Head live=same.head();
            assertNotEquals(first,second);assertNotEquals(old.digest(),live.digest());
            Head actual=same.requireHistoricalHead(old.state().sequence(),old.digest());
            assertFalse(actual.documents().isEmpty());
            var historical=RootPendingUiColdQualification.requireHistoricalDomain(same,actual,f.registration());
            assertEquals(first,historical.payload());assertEquals(second,((DomainBodies.Available)same.readDomain(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS)).reference().payload());
            assertEquals(live.digest(),same.head().digest());
            assertEquals(old.state().toJson().get("pending_cycle"),live.state().toJson().get("pending_cycle"));
            assertEquals(old.state().toJson().get("NEXT"),live.state().toJson().get("NEXT"));return null;
        });
    }
    @Test void wrongAncestorOrRegistrationCannotTurnAStateIntoAnOriginalCauseBody()throws Exception {
        Fixture f=fixture();f.writer().locked(same->{
            Head anchor=same.head();f.importBody(same,1);Head retained=same.head();f.importBody(same,2);
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalHead(retained.state().sequence(),"0".repeat(64)));
            assertThrows(Exception.class,()->same.requireHistoricalHead(same.head().state().sequence()+1,retained.digest()));
            assertThrows(IOException.class,()->RootPendingUiColdQualification.requireHistoricalDomain(same,
                    same.requireHistoricalHead(anchor.state().sequence(),anchor.digest()),f.registration()));
            var wrong=new DomainBodies.Registration(f.registration().slot(),"different-contract/v1",4096,f.registration().producerSources(),f.registration().verifier());
            assertThrows(IllegalArgumentException.class,()->RootPendingUiColdQualification.requireHistoricalDomain(same,
                    same.requireHistoricalHead(retained.state().sequence(),retained.digest()),wrong));return null;
        });
    }
    @Test void sameBytesNewMaterialFileIdentityIsNotTheRetainedHistoricalOriginal()throws Exception {
        Fixture f=fixture();f.writer().locked(same->{
            ExactRef original=f.importBody(same,1);Head old=same.head();f.importBody(same,2);
            Head actual=same.requireHistoricalHead(old.state().sequence(),old.digest());
            Path material=Path.of(original.path()),replacement=temp.resolve("replacement-material.json");
            Files.write(replacement,Files.readAllBytes(material));Files.move(replacement,material,StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,()->RootPendingUiColdQualification.requireHistoricalDomain(same,actual,f.registration()));return null;
        });
    }
    @Test void producerCodeChangeDoesNotRejectRetainedHistoricalBody()throws Exception {
        Fixture f=fixture();f.writer().locked(same->{
            ExactRef first=f.importBody(same,1);Head old=same.head();f.importBody(same,2);Head live=same.head();
            Head actual=same.requireHistoricalHead(old.state().sequence(),old.digest());
            Files.writeString(f.source(),"updated runtime producer code after retained import",StandardCharsets.UTF_8);
            var historical=RootPendingUiColdQualification.requireHistoricalDomain(same,actual,f.registration());
            assertEquals(first,historical.payload());assertEquals(live.digest(),same.head().digest());return null;
        });
    }
}
