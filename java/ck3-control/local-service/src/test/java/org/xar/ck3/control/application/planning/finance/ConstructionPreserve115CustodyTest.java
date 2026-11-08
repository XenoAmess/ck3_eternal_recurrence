package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** New preserved-byte/custody DATA regression. No action membership, permission issuer, Native or Root admission.
 * Only the two qualified pure quote/command builders are reused, never prior @Test or private fixture authority.
 */
final class ConstructionPreserve115CustodyTest {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;
    @Test void largeOwnedRawSurvivesCallerMutationAndColdConsumersStillRequireActualFullOriginal()throws Exception {
        Obj full=quote(true);byte[] exact=DriverJson.encode(full),caller=exact.clone();
        assertTrue(exact.length>6_000_000);var observed=ObservedRequest.fromFullMaterial(caller);
        caller[0]='[';byte[] getter=observed.original();getter[0]='!';assertArrayEquals(exact,observed.original());
        try(var f=new Store(directory.resolve("large"))) {
            Obj manifest=f.writer.locked(same->{String before=same.head().digest();
                var source=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession);Obj first=source.preserve(observed),again=source.preserve(observed);
                assertArrayEquals(DriverJson.encode(first),DriverJson.encode(again));
                ExactRef ref=reference(first);assertEquals(exact.length,ref.bytes());assertEquals(ActionCodec.sha256(exact),ref.sha256());
                assertArrayEquals(exact,f.archive.withSession(same).loadFullMaterial(ref).bytes());assertEquals(before,same.head().digest());return first;
            });
            ActionCommand command=command(f.source,full,manifest,"p115-new-software-data");
            byte[] canonical=ActionCodec.encodeCommand(command);ActionCommand decoded=ActionCodec.decodeCommand(canonical);
            var receipt=new ActionReceipt(1,1,decoded,ActionCodec.bodySha256(decoded),new ActionState.IntentDurable());
            var delegates=new AtomicInteger();
            var binding=ConstructionOriginalSource.archivedBinding(new NativeRecordedEvidenceVerifier.Binding(command.operation(),f.source,
                    (head,actual,archive)->delegates.incrementAndGet()),f.writer::borrowedSession);
            f.writer.locked(same->{
                var cold=new NativeOutcomeArchive(f.store,f.writer);String before=same.head().digest();
                assertArrayEquals(exact,ConstructionOriginalSource.resolveCommand(same,cold,decoded).observed().original());
                binding.verifier().verify(same.head(),receipt,cold.withSession(same));assertEquals(1,delegates.get());
                Obj header=object(manifest.get("financing_request"),"financing");
                Obj changed=manifest.with("financing_request",header.with("schema",new Text("p115-corrupted-current-header")));
                var mismatch=command(f.source,full,changed,"p115-mismatched-header-data");
                var mismatchReceipt=new ActionReceipt(1,1,mismatch,ActionCodec.bodySha256(mismatch),new ActionState.IntentDurable());
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolveCommand(same,cold,mismatch));
                assertThrows(RuntimeException.class,()->binding.verifier().verify(same.head(),mismatchReceipt,cold.withSession(same)));
                assertEquals(1,delegates.get(),"source/header rejection precedes DATA-only delegate; never a native-verifier positive claim");
                ExactRef ref=reference(manifest);Path payload=Path.of(ref.path()),held=payload.resolveSibling(payload.getFileName()+".held");
                Path alias=directory.resolve("same-bytes-other-path.json");Files.write(alias,exact);
                Obj foreign=manifest.with("input_ref",DriverJson.object(StrictJson.canonical(exact(alias).toJson(),4096),4096));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,foreign));
                Files.move(payload,held);
                try {
                    assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolveCommand(same,cold,decoded));
                    assertThrows(RuntimeException.class,()->binding.verifier().verify(same.head(),receipt,cold.withSession(same)));
                    assertEquals(1,delegates.get());
                }finally{Files.move(held,payload);}
                binding.verifier().verify(same.head(),receipt,cold.withSession(same));assertEquals(2,delegates.get());
                assertArrayEquals(exact,cold.withSession(same).loadFullMaterial(ref).bytes());assertArrayEquals(canonical,ActionCodec.encodeCommand(command));
                assertArrayEquals(exact,observed.original());assertEquals(before,same.head().digest());return null;
            });
        }
    }
    @Test void oldSmallPreserveStillUsesItsOriginalInlineAndCanonicalCommandContracts()throws Exception {
        Obj small=quote(false);byte[] original=DriverJson.encode(small),caller=original.clone();var observed=new ObservedRequest(caller);caller[0]='[';
        try(var f=new Store(directory.resolve("small"))) {
            f.writer.locked(same->{String before=same.head().digest();Obj inline=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed);
                assertEquals(small.get("schema"),inline.get("schema"));assertFalse(inline.members().containsKey("input_ref"));
                assertArrayEquals(original,DriverJson.encode(inline));assertArrayEquals(original,observed.original());
                var command=command(f.source,small,inline,"p115-unchanged-small-data");var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
                byte[] expected=new ObservedRequest(encode(object(decoded.arguments().get("ordinary_cash_request"),"canonical old inline"))).original();
                assertArrayEquals(expected,ConstructionOriginalSource.resolveCommand(same,f.archive,decoded).observed().original());
                assertEquals(before,same.head().digest());return null;
            });
        }
    }
    private static Obj quote(boolean large)throws Exception {
        var method=ConstructionFullCustody113Test.class.getDeclaredMethod("quote",boolean.class);method.setAccessible(true);return (Obj)method.invoke(null,large);
    }
    private static ActionCommand command(ExactRef source,Obj full,Obj supplied,String id) {
        try {
            var method=ConstructionFullCustody113Test.class.getDeclaredMethod("command",ExactRef.class,Obj.class,Obj.class,String.class);method.setAccessible(true);
            return (ActionCommand)method.invoke(null,source,full,supplied,id);
        }catch(ReflectiveOperationException failure){throw new IllegalStateException(failure instanceof java.lang.reflect.InvocationTargetException?failure.getCause():failure);}
    }
    private static ExactRef reference(Obj manifest){return ExactRef.fromJson(StrictJson.parse(DriverJson.encode(object(manifest.get("input_ref"),"reference"))));}
    private static ExactRef exact(Path path)throws IOException{byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static final class Store implements AutoCloseable {
        final StorageWriteGuardTestSupport guard;final ImmutableArtifactStore store;final ContinuityWriter writer;final NativeOutcomeArchive archive;final ExactRef source;
        Store(Path root)throws IOException {
            Files.createDirectories(root);var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1").put("machine_id","construction-full-original-software-machine")
                    .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25)
                    .put("start_date_raw",1000).put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                    .put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=root.resolve("p115-software-source.txt");Files.writeString(producer,"P115 independent SOFTWARE source metadata, never Root authority",StandardCharsets.UTF_8);source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),"construction-full-original-software-machine");Path objects=root.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(root,layout.lock(),32*1024*1024);store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),32*1024*1024),guard);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("no action/domain mutation in custody DATA");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no action/domain mutation in custody DATA");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);archive=new NativeOutcomeArchive(store,writer);
        }
        public void close()throws IOException{guard.close();}
    }
}
