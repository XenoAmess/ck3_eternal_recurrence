package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** New actual intent DATA consumer regression; real same-writer full custody first.
 * Reflection invokes only the existing private pure five-argument calculation to force an old fallback oracle.
 * No private authority issuer, public raw/typed pair, action execution, Native or Runtime admission.
 */
final class ConstructionIntentResult117Test {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;

    @Test void fullResolvedIntentMatchesOldFinalizerBodyWithExactPrecisionAndOwnedCache()throws Exception {
        Obj small=precise(quote(false)),full=precise(quote(true));byte[] raw=DriverJson.encode(full);
        var observed=ObservedRequest.fromFullMaterial(raw);assertTrue(raw.length>6_000_000);
        var quote=observed.input().quoted().orElseThrow().nativeQuote();byte[] queryBytes=DriverJson.encode(query(full));
        assertArrayEquals(queryBytes,quote.original());byte[] fixed=ConstructionOriginalSource.finalizeQuery(queryBytes);
        assertTrue(new String(fixed,StandardCharsets.UTF_8).contains("0.123456789012345678901"));
        assertArrayEquals(fixed,quote.exactFullFinalizedBytes().orElseThrow());byte[] altered=quote.exactFullFinalizedBytes().orElseThrow();altered[0]='!';
        assertArrayEquals(fixed,quote.exactFullFinalizedBytes().orElseThrow());
        try(var f=new Store(directory.resolve("full"))) {
            f.writer.locked(same->{String head=same.head().digest();
                Obj manifest=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed);
                var command=command(f.source,full,manifest,"p117-full-consumer-data");byte[] canonical=ActionCodec.encodeCommand(command);
                var decoded=ActionCodec.decodeCommand(canonical);var loaded=ConstructionOriginalSource.resolveCommand(same,new NativeOutcomeArchive(f.store,f.writer),decoded);
                assertArrayEquals(queryBytes,loaded.observed().input().quoted().orElseThrow().nativeQuote().original());
                byte[] consumerGetter=loaded.observed().input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow();consumerGetter[0]='!';
                Obj actual=ConstructionDomainLifecycle.intent(clear(),decoded,loaded);
                var oldSmall=new ObservedRequest(DriverJson.encode(small));assertTrue(oldSmall.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().isEmpty());
                // The same command/request with an equivalent original small typed input forces the unchanged finalizer.
                // This private pure calculation is only an oracle, not a constructed Loaded or source permission.
                Obj reference=canonicalBody(pureIntent(clear(),decoded,oldSmall,loaded.original()));
                assertArrayEquals(DriverJson.encode(reference),DriverJson.encode(actual));
                assertEquals(new IntegerValue(BigInteger.valueOf(584686)),object(actual.get("pending"),"pending").get("pre_player_monthly_gold_income_raw"));
                assertArrayEquals(canonical,ActionCodec.encodeCommand(decoded));assertArrayEquals(raw,loaded.observed().original());assertEquals(head,same.head().digest());return null;
            });
        }
    }
    @Test void unequalRawQueryWithPresentOtherInstanceCacheUsesOriginalFinalizer()throws Exception {
        Obj a=precise(quote(true)),b=proof(a,BigInteger.TWO);byte[] rawA=DriverJson.encode(a),rawB=DriverJson.encode(b);
        var observedA=ObservedRequest.fromFullMaterial(rawA);var observedB=ObservedRequest.fromFullMaterial(rawB);
        byte[] cacheA=observedA.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow();
        byte[] queryB=DriverJson.encode(query(b)),fixedB=ConstructionOriginalSource.finalizeQuery(queryB);
        assertFalse(Arrays.equals(queryB,observedA.input().quoted().orElseThrow().nativeQuote().original()));
        assertFalse(Arrays.equals(cacheA,fixedB));assertArrayEquals(fixedB,observedB.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow());
        byte[] getter=observedB.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow();getter[0]='!';
        assertArrayEquals(cacheA,observedA.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().orElseThrow());
        try(var f=new Store(directory.resolve("mismatch"))) {
            f.writer.locked(same->{String head=same.head().digest();
                Obj manifest=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observedB);
                var command=command(f.source,b,manifest,"p117-mismatched-query-pure-data");
                var loadedB=ConstructionOriginalSource.resolveCommand(same,new NativeOutcomeArchive(f.store,f.writer),command);
                Obj expected=ConstructionDomainLifecycle.intent(clear(),command,loadedB);
                // Deliberately different DATA inputs only to this private pure helper. No public raw/typed pair or Loaded is fabricated.
                // Reusing cacheA would retain proof_epoch1 and fail the command's proof_epoch2 guard; exact mismatch must finalize B.
                Obj actual=canonicalBody(pureIntent(clear(),command,observedA,loadedB.original()));
                assertArrayEquals(DriverJson.encode(expected),DriverJson.encode(actual));
                assertEquals(new IntegerValue(BigInteger.TWO),object(actual.get("pending"),"pending").get("pre_proof_epoch"));
                assertArrayEquals(rawA,observedA.original());assertArrayEquals(rawB,loadedB.observed().original());assertEquals(head,same.head().digest());return null;
            });
        }
    }
    @Test void legacySmallEmptyCacheKeepsOriginalIntentBytesAndCurrentHeaderIsStillPhysicallyChecked()throws Exception {
        Obj small=precise(quote(false)),full=precise(quote(true));byte[] original=DriverJson.encode(small);var observed=new ObservedRequest(original);
        assertTrue(observed.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().isEmpty());
        try(var f=new Store(directory.resolve("small"))) {
            f.writer.locked(same->{String head=same.head().digest();
                Obj inline=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed);
                var command=command(f.source,small,inline,"p117-legacy-small-data");
                var loaded=ConstructionOriginalSource.resolveCommand(same,f.archive,command);
                Obj actual=ConstructionDomainLifecycle.intent(clear(),command),old=pureIntent(clear(),command,loaded.observed(),loaded.original());
                assertArrayEquals(DriverJson.encode(old),DriverJson.encode(actual));assertArrayEquals(original,observed.original());
                Obj manifest=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(ObservedRequest.fromFullMaterial(DriverJson.encode(full)));
                var current=command(f.source,full,manifest,"p117-current-header-data");var currentLoaded=ConstructionOriginalSource.resolveCommand(same,f.archive,current);
                ConstructionDomainLifecycle.intent(clear(),current,currentLoaded);
                Obj changed=manifest.with("financing_request",object(manifest.get("financing_request"),"header").with("schema",new Text("p117-invalid-current-header")));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolveCommand(same,new NativeOutcomeArchive(f.store,f.writer),command(f.source,full,changed,"p117-bad-header-data")));
                assertEquals(head,same.head().digest());return null;
            });
        }
    }
    private static Obj query(Obj full){return object(object(full.get("quoted_outlay"),"outlay").get("query_observation"),"query");}
    private static Obj precise(Obj full) {
        Obj q=query(full),envelope=object(q.get("native_envelope"),"envelope"),result=object(envelope.get("result"),"result"),probe=object(result.get("private_probe"),"probe");
        Obj world=object(probe.get("player_world_building_sources"),"world");
        Obj opaque=DriverJson.object("{\"z\":1.00,\"a\":-0.0,\"fraction\":0.123456789012345678901,\"exp\":1e+0}".getBytes(StandardCharsets.UTF_8),4096);
        probe=probe.with("player_world_building_sources",world.with("opaque_result117",opaque));
        return full.with("quoted_outlay",object(full.get("quoted_outlay"),"outlay").with("query_observation",q.with("native_envelope",envelope.with("result",result.with("private_probe",probe)))));
    }
    private static Obj proof(Obj full,BigInteger epoch) {
        Obj q=query(full),envelope=object(q.get("native_envelope"),"envelope"),result=object(envelope.get("result"),"result"),probe=object(result.get("private_probe"),"probe");
        probe=probe.with("proof_epoch",new IntegerValue(epoch));
        return full.with("quoted_outlay",object(full.get("quoted_outlay"),"outlay").with("query_observation",q.with("native_envelope",envelope.with("result",result.with("private_probe",probe)))));
    }
    private static ConstructionLedgerCodec.Ledger clear(){return ConstructionLedgerCodec.decodeLedger(DriverJson.encode(obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()))));}
    private static Obj canonicalBody(Obj body){return DriverJson.object(ConstructionDomainLifecycle.Prepared.canonicalBody(body),ConstructionLedgerCodec.MAX_BYTES);}
    private static Obj pureIntent(ConstructionLedgerCodec.Ledger ledger,ActionCommand command,ObservedRequest observed,Obj full) {
        try {
            var method=ConstructionDomainLifecycle.class.getDeclaredMethod("intent",ConstructionLedgerCodec.Ledger.class,ActionCommand.class,Optional.class,ObservedRequest.class,Obj.class);method.setAccessible(true);
            return (Obj)method.invoke(null,ledger,command,Optional.empty(),observed,full);
        }catch(ReflectiveOperationException failure){throw new IllegalStateException(failure instanceof java.lang.reflect.InvocationTargetException?failure.getCause():failure);}
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
            Path producer=root.resolve("p117-software-source.txt");Files.writeString(producer,"P117 independent SOFTWARE source metadata, never Root authority",StandardCharsets.UTF_8);source=exact(producer);
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
