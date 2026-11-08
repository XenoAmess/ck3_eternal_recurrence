package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;

import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.CleanupMode;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.FullMaterialStage;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Finite construction DATA/resource/cold-header tests. Reflection reads resource state or existing pure fixture methods only. */
final class ConstructionStagedMaterial129Test {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;

    @Test void completeModelsOwnedRawTypedResultAndExactCacheMatchOldByteFactory() throws Exception {
        for (boolean large : List.of(false,true)) {
            Obj full=fixture(large);byte[] raw=DriverJson.encode(full);
            var old=ObservedRequest.fromFullMaterial(raw);
            var expected=OrdinaryWartimeConstruction.compose(old.input());
            assertEquals(OrdinaryWartimeConstruction.Disposition.QUOTED_CANDIDATE,expected.disposition());
            byte[] expectedModel=DriverJson.encode(DriverJson.object(raw,FullJsonTree.MAXIMUM_BYTES));
            byte[] supplied=raw.clone();
            FullMaterialStage stage=OrdinaryWartimeConstructionCodec.stageFullMaterial(supplied);
            supplied[0]='!';
            Obj model;
            ObservedRequest actual;
            try(stage) {
                model=stage.model();
                assertArrayEquals(expectedModel,DriverJson.encode(model));
                assertArrayEquals(expectedModel,DriverJson.encode(stage.model()));
                actual=stage.finish();
                assertCleared(stage);
                assertThrows(IllegalStateException.class,stage::finish);
                assertThrows(IllegalStateException.class,stage::model);
            }
            stage.close();
            assertCleared(stage);
            assertArrayEquals(raw,actual.original());
            assertArrayEquals(expectedModel,DriverJson.encode(model));
            var observed=OrdinaryWartimeConstruction.compose(actual.input());
            assertEquals(expected.originalSelection(),observed.originalSelection());
            assertEquals(expected.stage(),observed.stage());
            assertEquals(expected.disposition(),observed.disposition());
            assertEquals(expected.reason(),observed.reason());
            assertEquals(expected.cash().status(),observed.cash().status());
            assertEquals(expected.financing().status(),observed.financing().status());
            assertFalse(observed.canSubmitAction());
            assertArrayEquals(OrdinaryWartimeConstructionCodec.encode(expected),OrdinaryWartimeConstructionCodec.encode(observed));
            var before=old.input().quoted().orElseThrow().nativeQuote();
            var after=actual.input().quoted().orElseThrow().nativeQuote();
            assertTrue(before.selected().isPresent());
            assertEquals(before.observation(),after.observation());
            assertEquals(before.constructionKind(),after.constructionKind());
            assertEquals(before.selected().orElseThrow().candidate(),after.selected().orElseThrow().candidate());
            assertEquals(before.selected().orElseThrow().sourceFrame(),after.selected().orElseThrow().sourceFrame());
            assertArrayEquals(before.selected().orElseThrow().original().bytes(),after.selected().orElseThrow().original().bytes());
            assertArrayEquals(before.original(),after.original());
            byte[] cache=after.exactFullFinalizedBytes().orElseThrow();
            assertArrayEquals(before.exactFullFinalizedBytes().orElseThrow(),cache);
            assertTrue(new String(cache,StandardCharsets.UTF_8).contains("0.123456789012345678901"));
            cache[0]='!';
            assertArrayEquals(before.exactFullFinalizedBytes().orElseThrow(),after.exactFullFinalizedBytes().orElseThrow());
            byte[] leaked=actual.original();leaked[0]='!';
            assertArrayEquals(raw,actual.original());
            assertArrayEquals(raw,DriverJson.encode(full));
            if (!large) {
                var legacy=new ObservedRequest(raw);
                assertTrue(legacy.input().quoted().orElseThrow().nativeQuote().exactFullFinalizedBytes().isEmpty());
                assertArrayEquals(raw,legacy.original());
            }
        }
    }

    @Test void stageConsumesOnceAndDropsPrivateResourcesOnSuccessFailureAndClose() throws Exception {
        var type=FullMaterialStage.class;
        assertTrue(Modifier.isFinal(type.getModifiers()));
        var constructors=type.getDeclaredConstructors();
        assertEquals(1,constructors.length);
        assertTrue(Modifier.isPrivate(constructors[0].getModifiers()));
        assertArrayEquals(new Class<?>[]{byte[].class},constructors[0].getParameterTypes());
        for (String method : List.of("model","finish","close"))
            assertTrue(Modifier.isSynchronized(type.getDeclaredMethod(method).getModifiers()));
        Arrays.stream(type.getDeclaredMethods()).filter(method->Modifier.isPublic(method.getModifiers())).forEach(method->{
            assertFalse(com.fasterxml.jackson.databind.JsonNode.class.isAssignableFrom(method.getReturnType()));
            assertNotEquals(byte[].class,method.getReturnType());
        });
        Obj full=fixture(false);byte[] raw=DriverJson.encode(full);
        var closed=OrdinaryWartimeConstructionCodec.stageFullMaterial(raw);
        closed.close();closed.close();assertCleared(closed);
        assertThrows(IllegalStateException.class,closed::model);
        assertThrows(IllegalStateException.class,closed::finish);

        var abort=OrdinaryWartimeConstructionCodec.stageFullMaterial(raw);
        IllegalArgumentException sentinel=new IllegalArgumentException("software header-phase sentinel");
        IllegalArgumentException same=assertThrows(IllegalArgumentException.class,()->{
            try(abort) {abort.model();throw sentinel;}
        });
        assertSame(sentinel,same);assertEquals(0,same.getSuppressed().length);assertCleared(abort);
        assertThrows(IllegalStateException.class,abort::finish);

        for (Obj bad : List.of(full.with("schema",new Text("p129-invalid-schema")),
                full.with("stage",new Text("P129_INVALID_STAGE")))) {
            byte[] encoded=DriverJson.encode(bad);
            RuntimeException old=assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(encoded));
            var failing=OrdinaryWartimeConstructionCodec.stageFullMaterial(encoded);
            assertArrayEquals(DriverJson.encode(DriverJson.object(encoded,FullJsonTree.MAXIMUM_BYTES)),DriverJson.encode(failing.model()));
            RuntimeException actual=assertThrows(RuntimeException.class,failing::finish);
            assertEquals(old.getClass(),actual.getClass());assertEquals(old.getMessage(),actual.getMessage());
            assertCleared(failing);
            assertThrows(IllegalStateException.class,failing::finish);
            failing.close();assertCleared(failing);
        }

        // Independent literal values and structural depth, not an expected model produced by the moved converter.
        for (int depth : List.of(33,64)) {
            int arrays=depth-1;
            String literal="{\"deep\":"+"[".repeat(arrays)+"0"+"]".repeat(arrays)
                    +",\"opaque\":{\"z\":-0.0,\"a\":1e+0,\"unicode\":\"\\u96ea\\ud83d\\ude00\",\"order\":{\"second\":2,\"first\":1}}}";
            byte[] encoded=literal.getBytes(StandardCharsets.UTF_8);
            assertThrows(RuntimeException.class,()->parseComplete(encoded,FullJsonTree.MAXIMUM_BYTES));
            var bounded=OrdinaryWartimeConstructionCodec.stageFullMaterial(encoded);
            try(bounded) {
                Obj complete=bounded.model();
                Value leaf=complete.get("deep");
                for(int index=0;index<arrays;index++)leaf=array(leaf,"literal depth").get(0);
                assertEquals(new IntegerValue(java.math.BigInteger.ZERO),leaf);
                Obj opaque=object(complete.get("opaque"),"opaque");
                assertEquals(new DecimalValue("-0.0"),opaque.get("z"));
                assertEquals(new DecimalValue("1e+0"),opaque.get("a"));
                assertEquals(new Text("\u96ea\uD83D\uDE00"),opaque.get("unicode"));
                assertEquals(List.of("z","a","unicode","order"),List.copyOf(opaque.members().keySet()));
                assertEquals(List.of("second","first"),List.copyOf(object(opaque.get("order"),"order").members().keySet()));
                assertEquals(List.of("deep","opaque"),List.copyOf(complete.members().keySet()));
            }
            assertCleared(bounded);
        }
        byte[] tooDeep=("{\"deep\":"+"[".repeat(64)+"0"+"]".repeat(64)+"}").getBytes(StandardCharsets.UTF_8);
        assertThrows(RuntimeException.class,()->DriverJson.object(tooDeep,FullJsonTree.MAXIMUM_BYTES));
        assertThrows(RuntimeException.class,()->OrdinaryWartimeConstructionCodec.stageFullMaterial(tooDeep));

        // Query failure must still precede a different, independently witnessed cash failure.
        Obj outlay=object(full.get("quoted_outlay"),"outlay"),query=object(outlay.get("query_observation"),"query");
        Obj badQuery=full.with("quoted_outlay",outlay.with("query_observation",query.with("schema",new Text("p129-bad-query-schema"))));
        Obj badCash=full.with("cash_input",object(full.get("cash_input"),"cash input").with("schema",new Text("p129-bad-cash-schema")));
        Obj both=badQuery.with("cash_input",badCash.get("cash_input"));
        byte[] queryWire=DriverJson.encode(badQuery),cashWire=DriverJson.encode(badCash),bothWire=DriverJson.encode(both);
        RuntimeException queryError=assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(queryWire));
        RuntimeException cashError=assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(cashWire));
        assertNotEquals(queryError.getMessage(),cashError.getMessage());
        RuntimeException bothOld=assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(bothWire));
        assertEquals(queryError.getClass(),bothOld.getClass());assertEquals(queryError.getMessage(),bothOld.getMessage());
        var ordered=OrdinaryWartimeConstructionCodec.stageFullMaterial(bothWire);
        ordered.model();
        RuntimeException bothNew=assertThrows(RuntimeException.class,ordered::finish);
        assertEquals(queryError.getClass(),bothNew.getClass());assertEquals(queryError.getMessage(),bothNew.getMessage());
        assertCleared(ordered);
        assertThrows(IllegalStateException.class,ordered::finish);

        byte[] array="[]".getBytes(StandardCharsets.UTF_8);
        RuntimeException oldRoot=assertThrows(RuntimeException.class,()->DriverJson.object(array,FullJsonTree.MAXIMUM_BYTES));
        var scalarRoot=OrdinaryWartimeConstructionCodec.stageFullMaterial(array);
        RuntimeException rootError=assertThrows(RuntimeException.class,()->{
            try(scalarRoot) {scalarRoot.model();}
        });
        assertEquals(oldRoot.getClass(),rootError.getClass());assertEquals(oldRoot.getMessage(),rootError.getMessage());
        assertCleared(scalarRoot);
        for (byte[] invalid : new byte[][]{null,new byte[0]}) {
            RuntimeException old=assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(invalid));
            RuntimeException actual=assertThrows(RuntimeException.class,()->OrdinaryWartimeConstructionCodec.stageFullMaterial(invalid));
            assertEquals(old.getClass(),actual.getClass());assertEquals(old.getMessage(),actual.getMessage());
        }
    }

    @Test void physicalColdHeaderMismatchWinsBeforeSdkSchemaEnumAndClosedShapeFailures() throws Exception {
        Obj full=fixture(true);
        List<Obj> invalid=List.of(
                full.with("schema",new Text("p129-bad-schema")).with("stage",new Text("P129_BAD_STAGE")),
                full.with("stage",new Text("P129_BAD_STAGE")),
                full.with("opaque_p129_unknown_root",new Text("retained complete model, rejected only by SDK closed shape")));
        List<byte[]> inputs=invalid.stream().map(DriverJson::encode).toList();
        List<RuntimeException> expected=inputs.stream().map(raw->
                assertThrows(RuntimeException.class,()->ObservedRequest.fromFullMaterial(raw))).toList();
        try(var f=new Store(directory.resolve("ordered-errors"))) {
            f.writer.locked(same->{
                String head=same.head().digest();
                var scoped=f.archive.withSession(same);
                for (int index=0;index<inputs.size();index++) {
                    byte[] raw=inputs.get(index);
                    assertTrue(raw.length>6_000_000);
                    ExactRef reference=scoped.preserveMaterial(RawJson.fullMaterial(raw));
                    Obj correct=manifest(reference,invalid.get(index).get("financing_request"));
                    Obj mismatch=correct.with("financing_request",new Text("p129-header-mismatch"));
                    RuntimeException first=assertThrows(RuntimeException.class,()->
                            ConstructionOriginalSource.resolve(same,new NativeOutcomeArchive(f.store,f.writer),mismatch));
                    assertEquals("construction manifest financing differs from full original",first.getMessage());
                    RuntimeException sdk=assertThrows(RuntimeException.class,()->
                            ConstructionOriginalSource.resolve(same,new NativeOutcomeArchive(f.store,f.writer),correct));
                    assertEquals(expected.get(index).getClass(),sdk.getClass());
                    assertEquals(expected.get(index).getMessage(),sdk.getMessage());
                    assertArrayEquals(raw,scoped.loadFullMaterial(reference).bytes());
                }
                assertEquals(head,same.head().digest());
                return null;
            });
        }
    }

    private static Obj fixture(boolean large) throws Exception {
        var quote=ConstructionIntentResult117Test.class.getDeclaredMethod("quote",boolean.class);quote.setAccessible(true);
        Obj full=(Obj)quote.invoke(null,large);
        var precise=ConstructionIntentResult117Test.class.getDeclaredMethod("precise",Obj.class);precise.setAccessible(true);
        return (Obj)precise.invoke(null,full);
    }
    private static Obj manifest(ExactRef reference,Value financing) {
        return obj("schema",new Text(ConstructionOriginalSource.SCHEMA),
                "input_ref",DriverJson.object(StrictJson.canonical(reference.toJson(),4096),4096),
                "financing_request",financing);
    }
    private static void assertCleared(FullMaterialStage stage) throws Exception {
        for (String field : List.of("root","exactFull")) {
            var member=FullMaterialStage.class.getDeclaredField(field);member.setAccessible(true);assertNull(member.get(stage));
        }
        var consumed=FullMaterialStage.class.getDeclaredField("consumed");consumed.setAccessible(true);assertTrue(consumed.getBoolean(stage));
    }
    private static ExactRef exact(Path path)throws IOException {
        byte[] raw=Files.readAllBytes(path);
        return new ExactRef(path.toAbsolutePath().normalize().toString(),raw.length,ActionCodec.sha256(raw));
    }

    /** Existing public software writer/store construction pattern; no private authority issuer is reflected. */
    private static final class Store implements AutoCloseable {
        final StorageWriteGuardTestSupport guard;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Store(Path root)throws IOException {
            Files.createDirectories(root);
            var state=StrictJson.object();
            state.put("schema","root.ck3.continuity-window/v1").put("machine_id","construction-full-original-software-machine")
                    .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30)
                    .put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                    .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                    .put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");
            state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");
            Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=root.resolve("p129-software-source.txt");
            Files.writeString(producer,"P129 independent SOFTWARE DATA source metadata, never Root authority",StandardCharsets.UTF_8);
            ExactRef source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),"construction-full-original-software-machine");
            Path objects=root.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(root,layout.lock(),32*1024*1024);
            store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),32*1024*1024),guard);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("no transition in DATA test");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no transition in DATA test");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);
            archive=new NativeOutcomeArchive(store,writer);
        }
        public void close()throws IOException {guard.close();}
    }
}
