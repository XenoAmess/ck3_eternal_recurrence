package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions.CoaUpload;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import static org.junit.jupiter.api.Assertions.*;

/** Uses the actual finite CAS, canonical writer session, immutable commit/FileID verification and source preparer.
 * Software fixtures grant no live Root, native permission, or Game-effect qualification. */
final class CoaSourceArchiveBoundaryTest {
    @TempDir Path temporary;
    private static final String MACHINE="coa-source-software-machine";
    private static final Instant NOW=Instant.parse("2026-10-24T04:00:00Z");
    @Test void completeActualSourceMaterialReachesPreparerAndReopensWithoutAnotherPublisher()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("full"),8*1024*1024)){
            f.writer.locked(same->{
                var actual=f.archive.withSession(same);var materials=new CoaSourceMaterials(actual);var binding=new FrontendBinding(BigInteger.valueOf(3),4242);CommandOrigin origin=f.origin();
                EncodedSource source=EncodedSource.encode("coa={\r\n"+" colored_emblem={}\r\n".repeat(9000)+"}\r\n",true);assertTrue(source.sourceBytes()>V1_MAX_BYTES);
                var material=materials.preserve(source,binding,origin,"software-coa-session",true);var identity=LedgerFilesFixtureAccess.identity(Path.of(material.reference().path()));long writes=f.guard.successfulBatches();
                var again=materials.preserve(source,binding,origin,"software-coa-session",true);assertEquals(material.reference(),again.reference());assertEquals(identity,LedgerFilesFixtureAccess.identity(Path.of(material.reference().path())));assertEquals(writes,f.guard.successfulBatches());
                var expected=new CommandExpectation.Frontend(new FrontendExpectedPostcondition(origin.requireFrontend(),f.source,CoaUpload.EXPECTATION,List.of(new ExpectedBoolean(new FieldKey("independent_game_effect_proven"),false))));
                var command=new ActionCommand("coa-software-source",origin,f.source,"software-coa-session",new OperationKey(PROBE_STEP),CoaSourceMaterials.arguments(material,true),expected,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(60));
                var preparer=new CoaUpload.Preparation(f.pin,materials,(held,exact)->{f.writer.requireSession(held);assertEquals(command,exact);},()->same);
                NativeRequest nativeRequest=preparer.prepare(command);assertEquals(PROBE_STEP,nativeRequest.step());assertEquals(Optional.of("game.command."+PROBE_STEP),nativeRequest.requiredCapability());
                var fields=FrontendCoaCodec.object(nativeRequest.additionalFields());assertEquals(source.sourceBase64(),fields.get("source_base64").textValue());assertTrue(fields.get("apply").booleanValue());assertEquals(Set.of("source_base64","apply"),fields.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()));
                var reopened=new CoaSourceMaterials(new NativeOutcomeArchive(f.store,f.writer).withSession(same));assertEquals(material,reopened.load(material.reference(),origin,binding,"software-coa-session"));
                assertThrows(IllegalArgumentException.class,()->reopened.load(material.reference(),origin,new FrontendBinding(BigInteger.valueOf(4),4242),"software-coa-session"));
                assertThrows(IllegalArgumentException.class,()->reopened.load(material.reference(),origin,binding,"other-session"));
                assertThrows(RuntimeException.class,()->reopened.load(new ExactRef(temporary.resolve("not-an-owned-CAS-path").toString(),1,"a".repeat(64)),origin,binding,"software-coa-session"));
                return null;
            });
            assertFalse(f.guard.hasUnknownWrite());
        }
    }
    @Test void finiteBudgetRejectsSourceBeforeWritingAndSameBytesDifferentFileIdCannotReplaceOriginal()throws Exception{
        try(Fixture small=new Fixture(temporary.resolve("finite"),65536)){
            small.writer.locked(same->{var materials=new CoaSourceMaterials(small.archive.withSession(same));long writes=small.guard.successfulBatches();
                assertThrows(RuntimeException.class,()->materials.preserve(EncodedSource.encode("a".repeat(150000),true),new FrontendBinding(BigInteger.valueOf(3),4242),small.origin(),"software-coa-session",true));assertEquals(writes,small.guard.successfulBatches());return null;});
            assertFalse(small.guard.hasUnknownWrite());
        }
        try(Fixture f=new Fixture(temporary.resolve("identity"),8*1024*1024)){
            f.writer.locked(same->{var materials=new CoaSourceMaterials(f.archive.withSession(same));var binding=new FrontendBinding(BigInteger.valueOf(3),4242);var origin=f.origin();
                var material=materials.preserve(EncodedSource.encode("coa={}\r\n",false),binding,origin,"software-coa-session",false);
                Path payload=Path.of(material.reference().path()).toAbsolutePath().normalize(),old=payload.resolveSibling(payload.getFileName()+".original-retained");
                assertTrue(payload.startsWith(f.directory));assertTrue(old.startsWith(f.directory));byte[] bytes=Files.readAllBytes(payload);var before=LedgerFilesFixtureAccess.identity(payload);
                Files.move(payload,old);Files.write(payload,bytes,StandardOpenOption.CREATE_NEW);
                try{assertNotEquals(before,LedgerFilesFixtureAccess.identity(payload));assertThrows(RuntimeException.class,()->materials.load(material.reference(),origin,binding,"software-coa-session"));}
                finally{Files.delete(payload);Files.move(old,payload);}
                assertEquals(before,LedgerFilesFixtureAccess.identity(payload));assertEquals(material,materials.load(material.reference(),origin,binding,"software-coa-session"));return null;
            });
        }
    }
    static final class Fixture implements AutoCloseable {
        final Path directory;final ExactRef pin;final G2Source source;final StorageWriteGuardTestSupport guard;final ImmutableArtifactStore store;final ContinuityWriter writer;final NativeOutcomeArchive archive;
        Fixture(Path directory,long budget)throws IOException{
            assertTrue(System.getProperty("os.name").startsWith("Windows"),"actual Windows FileID/native allocation required; missing is failure, never skip");this.directory=directory.toAbsolutePath().normalize();Files.createDirectory(this.directory);
            var state=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE).put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",4242).put("creation_date","2026-10-24T00:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=this.directory.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=this.directory.resolve("anchor.json");Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));Files.write(this.directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(this.directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path sourceFile=this.directory.resolve("source.java");Files.writeString(sourceFile,"software CoA material/archive source");pin=LedgerFilesFixtureAccess.read(sourceFile,1024).pin().reference();source=new G2Source(MACHINE,NOW.toString(),GAME_VERSION,pin);
            var layout=new Layout(snapshot,LedgerFilesFixtureAccess.read(anchor,65536).pin().reference(),MACHINE);guard=StorageWriteGuardTestSupport.create(layout.snapshot().getParent(),layout.lock(),16*1024*1024);
            try{store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(this.directory.resolve("objects"),layout.lock(),budget),guard);
                writer=new ContinuityWriter(layout,List.of(pin),new TransitionAuthority(){
                    @Override public String revalidate(ContinuityState before,Request request){throw new AssertionError("material test cannot reduce real continuity state");}
                    @Override public ContinuityState reduce(ContinuityState before,Request request){throw new AssertionError("material test cannot commit a Game/continuity event");}
                },Clock.fixed(NOW,ZoneOffset.UTC),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);archive=new NativeOutcomeArchive(store,writer);
            }catch(IOException|RuntimeException|Error failure){try{guard.close();}catch(IOException close){failure.addSuppressed(close);}throw failure;}
        }
        CommandOrigin origin(){return new CommandOrigin.Frontend(new FrontendIdentity(MACHINE,new GameGeneration(4242,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),"software-coa-session",BigInteger.valueOf(3),4242,new FrontendFrame.Menu(BigInteger.ONE),pin,pin));}
        @Override public void close()throws IOException{guard.close();}
    }
}
