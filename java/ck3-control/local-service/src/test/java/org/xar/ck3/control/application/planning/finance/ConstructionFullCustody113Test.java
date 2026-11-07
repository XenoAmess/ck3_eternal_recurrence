package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;

/** Actual temporary writer/CAS and owning DATA consumers. No Game, Root admission, native dispatch or SAVE proof. */
final class ConstructionFullCustody113Test {
    @TempDir Path directory;
    private static final String MACHINE="construction-full-original-software-machine";

    @Test void manifestsReopenFullBytesAndEveryWrongLaneOrHeaderFailsClosed() throws Exception {
        try(var f=new Fixture(directory.resolve("manifest"))) {
            Obj small=quote(false),large=quote(true);byte[] full=DriverJson.encode(large),smallBytes=DriverJson.encode(small);
            assertTrue(full.length>4_194_304);assertThrows(IllegalArgumentException.class,()->new OrdinaryWartimeConstructionCodec.ObservedRequest(full));
            f.writer.locked(same->{
                var owner=new ConstructionOriginalSource(f.archive,()->same);
                Obj old=owner.preserve(new OrdinaryWartimeConstructionCodec.ObservedRequest(smallBytes));
                assertArrayEquals(smallBytes,DriverJson.encode(old));
                Obj manifest=owner.preserve(OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(full));
                assertEquals(Set.of("schema","input_ref","financing_request"),manifest.members().keySet());
                assertTrue(DriverJson.encode(manifest).length<262_144);
                ExactRef ref=reference(manifest.get("input_ref"));
                assertArrayEquals(full,f.archive.withSession(same).loadFullMaterial(ref).bytes());
                // A new archive object still performs the existing canonical/FileID/pin/full-byte read.
                var cold=new NativeOutcomeArchive(f.store,f.writer);
                var legacyReopened=ConstructionOriginalSource.resolve(same,cold,old);
                var oldDecoder=new OrdinaryWartimeConstructionCodec.ObservedRequest(encode(old));
                assertArrayEquals(oldDecoder.original(),legacyReopened.observed().original());
                assertArrayEquals(oldDecoder.original(),DriverJson.encode(legacyReopened.original()));
                Obj beforeOnly=old.with("stage",new Text("BEFORE_OPTIONAL_QUERY")).with("quoted_outlay",Nil.INSTANCE);
                var historicalBefore=command(f.source,small,beforeOnly,"legacy-before-stage-data");
                assertEquals(org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.Stage.BEFORE_OPTIONAL_QUERY,
                        ConstructionOriginalSource.resolveCommand(same,cold,historicalBefore).observed().input().stage());
                Value nested=new Text("finite legacy encoder depth DATA");
                for(int depth=0;depth<35;depth++)nested=obj("child",nested);
                Obj oldOutlay=object(old.get("quoted_outlay"),"old outlay"),oldQuery=object(oldOutlay.get("query_observation"),"old query");
                Obj deep=old.with("quoted_outlay",oldOutlay.with("query_observation",oldQuery.with("starting_snapshot",
                        object(oldQuery.get("starting_snapshot"),"old snapshot").with("opaque_legacy_depth",nested))));
                assertThrows(IllegalArgumentException.class,()->encode(deep));
                assertThrows(IllegalArgumentException.class,()->ConstructionOriginalSource.resolve(same,cold,deep));
                var reopened=ConstructionOriginalSource.resolve(same,cold,manifest);
                assertArrayEquals(full,reopened.observed().original());assertArrayEquals(full,DriverJson.encode(reopened.original()));
                var command=command(f.source,large,manifest,"future-full-software");byte[] canonical=ActionCodec.encodeCommand(command);
                var canonicalCommand=ActionCodec.decodeCommand(canonical);
                assertArrayEquals(canonical,ActionCodec.encodeCommand(canonicalCommand));
                assertArrayEquals(full,ConstructionOriginalSource.resolveCommand(same,cold,command).observed().original());
                assertArrayEquals(full,ConstructionOriginalSource.resolveCommand(same,cold,canonicalCommand).observed().original());
                assertArrayEquals(canonical,ActionCodec.encodeCommand(canonicalCommand));
                Obj financing=object(manifest.get("financing_request"),"financing").with("unconsumed_changed_header",new Bool(true));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,manifest.with("financing_request",financing)));
                for(Value schema:List.of(new Text("unknown-schema"),Nil.INSTANCE,new IntegerValue(BigInteger.ONE)))
                    assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,manifest.with("schema",schema)));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,manifest.with("cash_input",obj())));
                var missingSchema=new LinkedHashMap<>(manifest.members());missingSchema.remove("schema");
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,new Obj(missingSchema)));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,withRef(manifest,new ExactRef(ref.path(),ref.bytes(),"a".repeat(64)))));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,withRef(manifest,new ExactRef(ref.path(),ref.bytes()+1,ref.sha256()))));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,withRef(manifest,new ExactRef(ref.path(),RawJson.MAXIMUM_BYTES+1L,ref.sha256()))));
                Path alias=directory.resolve("same-bytes-external.json");Files.write(alias,full);
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,withRef(manifest,exact(alias))));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,fullLaneUnsupported(cold),manifest));
                byte[] packet=new byte[full.length+4];java.nio.ByteBuffer.wrap(packet).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(full.length).put(full);
                ExactRef packetRef=cold.withSession(same).preserveMaterial(RawJson.fullMaterial("{}".getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(packet));
                assertNotEquals(packetRef,ref);assertArrayEquals(canonical,ActionCodec.encodeCommand(command));
                Path original=Path.of(ref.path()),held=original.resolveSibling(original.getFileName()+".held");
                Files.move(original,held);
                try {assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,manifest));}
                finally {Files.move(held,original);}
                System.out.println("P113 exact full original "+full.length+" -> future command manifest "+DriverJson.encode(manifest).length);
                return null;
            });
        }
    }

    @Test void intentRestoreAndColdBindingConsumeResolvedFullWithoutChangingCanonicalCommand() throws Exception {
        try(var f=new Fixture(directory.resolve("consumers"))) {
            Obj small=quote(false),large=quote(true);
            f.writer.locked(same->{
                Obj manifest=new ConstructionOriginalSource(f.archive,()->same).preserve(OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(DriverJson.encode(large)));
                var current=command(f.source,large,manifest,"future-full-consumers");var legacy=command(f.source,small,small,"legacy-inline-consumers");
                byte[] canonical=ActionCodec.encodeCommand(current);var clear=ConstructionLedgerCodec.decodeLedger(DriverJson.encode(empty()));
                var loaded=ConstructionOriginalSource.resolveCommand(same,f.archive,current);
                Obj actual=ConstructionDomainLifecycle.intent(clear,current,loaded),reference=ConstructionDomainLifecycle.intent(clear,legacy);
                reference=DriverJson.object(ConstructionDomainLifecycle.Prepared.canonicalBody(reference),ConstructionLedgerCodec.MAX_BYTES);
                Obj pending=object(actual.get("pending"),"pending"),referencePending=object(reference.get("pending"),"reference pending");
                Set<String> identities=Set.of("action_request_id","coordinator_action_id","coordinator_body_sha256");
                assertEquals(referencePending.members().keySet(),pending.members().keySet());
                for(String key:pending.members().keySet())if(!identities.contains(key))
                    assertArrayEquals(DriverJson.encode(referencePending.get(key)),DriverJson.encode(pending.get(key)),key);
                assertEquals(new IntegerValue(BigInteger.valueOf(584686)),pending.get("pre_player_monthly_gold_income_raw"));
                var receipt=new ActionReceipt(1,1,current,ActionCodec.bodySha256(current),new ActionState.IntentDurable());
                // These are declared software reducer DATA, not a canonical coordinator/UNKNOWN receipt or restore admission.
                var witness=f.archive.withSession(same).preserveMaterial(new RawJson("{\"software_restore_data\":true}".getBytes(StandardCharsets.UTF_8)));
                var provenance=new ConstructionRestoreProvenance(witness,witness,witness,0,"b".repeat(64),current.before().frame().episodeRunId(),
                        current.before().frame().identity().player(),current.before().game(),"future-software-session");
                var row=new ConstructionRestoreReducer.Canonical(receipt,witness);
                assertThrows(RuntimeException.class,()->ConstructionRestoreReducer.reduce(clear,Optional.empty(),List.of(row),provenance));
                Obj derived=ConstructionRestoreReducer.reduce(clear,Optional.empty(),List.of(row),provenance,Map.of(receipt.bodySha256(),loaded));
                Obj retained=ConstructionRestoreReducer.reduce(clear,Optional.of(ConstructionLedgerCodec.decodeLedger(DriverJson.encode(actual))),List.of(row),provenance,Map.of(receipt.bodySha256(),loaded));
                assertArrayEquals(DriverJson.encode(derived),DriverJson.encode(retained));
                AtomicInteger delegates=new AtomicInteger();
                var spy=new NativeRecordedEvidenceVerifier.Binding(OrdinaryConstructionPolicy.OPERATION,f.source,(head,received,archive)->{
                    assertSame(receipt,received);delegates.incrementAndGet();
                });
                // This checks the new real-custody-before-delegate wrapper, not the old native-effect verifier's positive proof.
                var binding=ConstructionOriginalSource.archivedBinding(spy,()->same);
                binding.verifier().verify(same.head(),receipt,f.archive);assertEquals(1,delegates.get());
                Obj wrong=manifest.with("financing_request",obj());
                var badCommand=command(f.source,large,wrong,"bad-financing-header");
                var badReceipt=new ActionReceipt(1,2,badCommand,ActionCodec.bodySha256(badCommand),new ActionState.IntentDurable());
                assertThrows(RuntimeException.class,()->binding.verifier().verify(same.head(),badReceipt,f.archive));assertEquals(1,delegates.get());
                ExactRef ref=reference(manifest.get("input_ref"));Path original=Path.of(ref.path()),held=original.resolveSibling(original.getFileName()+".held");
                Files.move(original,held);
                try {
                    assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolveCommand(same,f.archive,current));
                    assertThrows(RuntimeException.class,()->binding.verifier().verify(same.head(),receipt,f.archive));assertEquals(1,delegates.get());
                } finally {Files.move(held,original);}
                assertArrayEquals(canonical,ActionCodec.encodeCommand(current));return null;
            });
        }
    }

    @Test void newMaterialVersionKeepsWholeInputAndOwningBodyReadersPhysicallyReopenIt() throws Exception {
        try(var f=new Fixture(directory.resolve("material"))) {
            Obj query=materialQuery(),smallInput=ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL,
                    ConstructionLedgerCodec.decodeLedger(DriverJson.encode(materialLedger())),"original-request",query,Optional.empty(),Optional.empty());
            byte[] reference=DriverJson.encode(ConstructionMaterialReducer.reduce(DriverJson.encode(smallInput)).originalBody());
            Obj expanded=largeQuery(query);byte[] fullQuery=DriverJson.encode(expanded);
            f.writer.locked(same->{
                var legacy=ConstructionMaterialSource.preserve(same,f.archive,smallInput);
                var originalLedger=ConstructionLedgerCodec.decodeLedger(DriverJson.encode(legacy.retainIn(materialLedger())));
                Obj full=ConstructionMaterialReducer.fullInput(ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL,originalLedger,
                        "original-request",expanded,Optional.empty(),Optional.empty());byte[] inputBytes=DriverJson.encode(full);
                assertTrue(inputBytes.length>ConstructionMaterialReducer.MAX_INPUT_BYTES);
                assertThrows(IllegalArgumentException.class,()->ConstructionMaterialReducer.decode(inputBytes));
                var source=ConstructionFullMaterialSource.preserve(same,f.archive,full);
                var cold=new NativeOutcomeArchive(f.store,f.writer);var loaded=source.load(same,cold);
                assertEquals(ConstructionMaterialReducer.InputVersion.FULL_V3,loaded.version());
                assertArrayEquals(inputBytes,cold.withSession(same).loadFullMaterial(source.input()).bytes());
                assertArrayEquals(fullQuery,DriverJson.encode(loaded.queryObservation()));
                assertArrayEquals(DriverJson.encode(originalLedger.original()),DriverJson.encode(loaded.ledger().original()));
                Obj reduced=ConstructionMaterialReducer.reduce(loaded).originalBody();
                var clean=new LinkedHashMap<>(reduced.members());clean.remove(ConstructionMaterialSource.BODY_FIELD);
                assertArrayEquals(reference,DriverJson.encode(new Obj(clean)));
                Obj body=source.retainIn(reduced);assertFalse(body.members().containsKey(ConstructionMaterialSource.BODY_FIELD));
                assertEquals(source.toJson(),body.get(ConstructionFullMaterialSource.BODY_FIELD));
                assertThrows(IllegalArgumentException.class,()->ConstructionFullMaterialSource.fromBody(body.with(ConstructionMaterialSource.BODY_FIELD,legacy.toJson())));
                assertThrows(IllegalArgumentException.class,()->ConstructionMaterialSource.decode(source.toJson()));
                assertThrows(IllegalArgumentException.class,()->ConstructionFullMaterialSource.decode(legacy.toJson()));
                ConstructionFullMaterialSource.requireRetained(same,cold,body);
                f.domain.publishOriginal(same,ConstructionDomainLifecycle.Kind.FRESH,obj("body",body),List.of(f.source));
                var known=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.CONSTRUCTION));
                assertArrayEquals(ConstructionDomainLifecycle.Prepared.canonicalBody(body),known.canonicalBody());
                assertArrayEquals(known.canonicalBody(),DriverJson.encode(f.domain.read(same).original()));
                var document=new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION,known.reference().payload(),known.canonicalBody());
                assertEquals(FinanceStatePort.Pending.CLEAR,f.domain.financePending(document));
                Path original=Path.of(source.input().path()),held=original.resolveSibling(original.getFileName()+".held");Files.move(original,held);
                try {
                    assertThrows(Exception.class,()->source.load(same,cold));
                    assertThrows(Exception.class,()->ConstructionFullMaterialSource.requireRetained(same,cold,body));
                    assertThrows(Exception.class,()->f.domain.read(same));
                    assertThrows(RuntimeException.class,()->f.domain.financePending(document));
                } finally {Files.move(held,original);}
                System.out.println("P113 exact material input "+inputBytes.length+"; retained body "+DriverJson.encode(body).length);return null;
            });
        }
    }

    private static Obj quote(boolean large)throws Exception {
        // Reuse only the new SDK test's pure DATA builder; no old @Test, private permission issuer or Runtime API is invoked.
        Class<?> data=Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");
        var method=data.getDeclaredMethod("complete");method.setAccessible(true);
        Obj original=DriverJson.object(FullJsonTree.encode((com.fasterxml.jackson.databind.JsonNode)method.invoke(null),FullJsonTree.MAXIMUM_BYTES),FullJsonTree.MAXIMUM_BYTES);
        Obj outlay=object(original.get("quoted_outlay"),"outlay"),query=object(outlay.get("query_observation"),"query");
        for(String key:List.of("starting_snapshot","ending_snapshot")) {
            Obj snap=object(query.get(key),key),diag=object(snap.get("diagnostics"),"diagnostics");
            query=query.with(key,snap.with("diagnostics",diag.with("bridge_pid",n(42)).with("bridge_creation_date",new Text("software-retained-birth"))));
        }
        if(large)query=largeQuery(query);
        Obj cash=object(original.get("cash_input"),"cash"),root=object(cash.get("root"),"root");
        Obj snapshot=object(query.get("starting_snapshot"),"starting snapshot");
        root=root.with("player_character_id",object(snapshot.get("played_character"),"actor").get("character_id"))
                .with("snapshot_revision",snapshot.get("native_revision")).with("date_raw",snapshot.get("date_raw"))
                .with("player_monthly_gold_income",obj("raw",n(584686),"scale",n(100000)));
        return original.with("quoted_outlay",outlay.with("query_observation",query)).with("cash_input",cash.with("root",root));
    }
    private static Obj largeQuery(Obj query)throws Exception {
        Class<?> data=Class.forName("org.xar.ck3.control.wave3.development.wartimesequencing.ConstructionFullOriginal113SdkTest");
        var method=data.getDeclaredMethod("retainedHistory139");method.setAccessible(true);
        Value history=FullValue((com.fasterxml.jackson.databind.JsonNode)method.invoke(null));
        for(String key:List.of("starting_snapshot","ending_snapshot")) {
            Obj snap=object(query.get(key),key).with("native_command_history",history)
                    .with("opaque_unknown",DriverJson.object("{\"y\":2,\"x\":1.00,\"minus_zero\":-0.0}".getBytes(StandardCharsets.UTF_8),4096));
            query=query.with(key,snap);
        }return query;
    }
    private static Value FullValue(com.fasterxml.jackson.databind.JsonNode value) {
        return DriverJson.fromNode(value);
    }
    private static ActionCommand command(ExactRef sourceRef,Obj full,Obj supplied,String id) {
        Obj query=object(object(full.get("quoted_outlay"),"outlay").get("query_observation"),"query");
        Obj snapshot=object(query.get("starting_snapshot"),"snapshot");
        var identity=new ProposalLifecycle.ObservationIdentity(MACHINE,new GameGeneration(99,new PythonOnlyUInt64(new BigInteger("133000000000000099"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(integer(object(snapshot.get("played_character"),"actor").get("character_id"),"actor"),
                        integer(snapshot.get("native_revision"),"native"),integer(snapshot.get("date_raw"),"date")),text(snapshot.get("snapshot_id"),"snapshot"),
                        integer(snapshot.get("revision"),"revision"),text(snapshot.get("episode_run_id"),"episode")),1);
        var source=new G2Source(MACHINE,"2026-11-07T00:00:00Z","1.20.0.4",sourceRef);
        Obj finalized=DriverJson.object(ConstructionOriginalSource.finalizeQuery(DriverJson.encode(query)),262_144);
        Obj args=obj("candidate",finalized.get("candidate"),"pre_proof_epoch",finalized.get("proof_epoch"),"ordinary_cash_request",supplied,
                "ordinary_cash_result",DriverJson.object(OrdinaryWartimeConstructionCodec.encode(org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction.compose(
                        OrdinaryWartimeConstructionCodec.ObservedRequest.fromFullMaterial(DriverJson.encode(full)).input())),262_144));
        return new ActionCommand(id,identity,source,"construction-full-software-session",OrdinaryConstructionPolicy.OPERATION,args,
                NativeConstructionEffects.expected(identity,source,args),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(120));
    }
    private static Obj empty(){return obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",Nil.INSTANCE,"applied_prior",new Arr(List.of()));}
    private static ExactRef exact(Path path)throws IOException {byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static ExactRef reference(Value value){return ExactRef.fromJson(StrictJson.parse(DriverJson.encode(value)));}
    private static Obj withRef(Obj manifest,ExactRef ref){return manifest.with("input_ref",DriverJson.object(StrictJson.canonical(ref.toJson(),4096),4096));}
    private static IntegerValue n(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static ActionPorts.OutcomeArchive fullLaneUnsupported(ActionPorts.OutcomeArchive original) {
        return (ActionPorts.OutcomeArchive)java.lang.reflect.Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(method.getName().equals("withSession"))return proxy;
            if(method.getName().equals("loadFullMaterial"))throw new UnsupportedOperationException("explicit full lane unsupported software port");
            try{return method.invoke(original,args);}catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
        });
    }
    private static final class SoftwareBodies implements ConstructionDomainLifecycle.OriginalBodyProducer {
        private final ExactRef source;
        SoftwareBodies(ExactRef source){this.source=source;}
        public ConstructionDomainLifecycle.OriginalBody replay(Session same,Head head,ConstructionDomainLifecycle.Kind kind,Obj input,Optional<ConstructionLedgerCodec.Ledger> previous){
            assertEquals(ConstructionDomainLifecycle.Kind.FRESH,kind);assertTrue(previous.isEmpty());
            return new ConstructionDomainLifecycle.OriginalBody(object(input.get("body"),"declared software body"),List.of(source));
        }
    }
    private static final class Fixture implements AutoCloseable {
        final ExactRef source;final ContinuityWriter writer;final NativeOutcomeArchive archive;final ImmutableArtifactStore store;
        final StorageWriteGuardTestSupport guard;final ConstructionDomainLifecycle.Prepared domain;
        Fixture(Path directory)throws IOException {
            Files.createDirectories(directory);var state=StrictJson.object();
            state.put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE).put("sequence",0).put("window_id",1).put("status","running")
                    .put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000).put("target_date_raw",263992)
                    .put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=directory.resolve("anchor.json");
            Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=directory.resolve("actual-software-producer.java");Files.writeString(producer,"P113 public temporary writer fixture; no Root or Game authority");source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),MACHINE);Path objects=directory.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(directory,layout.lock(),32*1024*1024);
            store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),32*1024*1024),guard);
            domain=ConstructionDomainLifecycle.prepare(List.of(source),source);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("software fixture permits registered domain imports only");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no action transition or Game write");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(domain.registration()),Optional.of(store),Optional.empty()),guard);
            archive=new NativeOutcomeArchive(store,writer);
            var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(source,new FinanceReadContracts.Permission(Optional.empty(),
                    "p113-software-definition:"+query.name(),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP)));
            domain.bindCore(writer,archive,(basis,originals)->{throw new AssertionError("this CAS/DATA test grants no full native/SEM frame");},definitions);
            domain.bindOriginals(source,new SoftwareBodies(source));
        }
        public void close()throws IOException{guard.close();}
    }
    // Copied only the finite pure material ledger/query builders from ConstructionLargeMaterialProductionTest.
    private static Obj materialLedger(){return obj("schema",new Text(ConstructionLedgerCodec.SCHEMA),"pending",Nil.INSTANCE,"applied",materialReceipt(),"applied_prior",new Arr(List.of()));}
    private static Obj materialReceipt(){return DriverJson.object(("{\"action_request_id\":\"original-request\",\"episode_run_id\":\"episode\",\"actor_character_id\":1,\"pre_native_revision\":2,\"pre_date_raw\":100,\"pre_proof_epoch\":5,\"source_bridge_pid\":42,\"source_bridge_creation_date\":\"old-process\",\"status\":\"applied\",\"postcondition_verified\":true,\"completion_status\":\"in_progress\",\"post_native_revision\":3,\"post_date_raw\":100,\"post_proof_epoch\":6,\"post_bridge_pid\":42,\"post_bridge_creation_date\":\"old-process\",\"completion_last_check_date_raw\":100,\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0,\"gold_before_raw\":100,\"stock_gold_cost_raw\":25}}").getBytes(StandardCharsets.UTF_8),262_144);}
    private static Obj materialQuery(){
        Obj snapshot=obj("snapshot_id",new Text("native:3"),"revision",n(3),"native_revision",n(3),"date_raw",n(820),"episode_run_id",new Text("episode"),
                "paused",new Bool(true),"map_ready",new Bool(true),"active_event",Nil.INSTANCE,"pending_character_interaction",Nil.INSTANCE,
                "played_character",obj("character_id",n(1),"alive",new Bool(true)),"active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()),
                "diagnostics",obj("bridge_pid",n(80),"bridge_creation_date",new Text("new-process"),"hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"))));
        Obj tuple=obj("barony_title_id",n(2),"province_id",n(3),"building_type_id",n(11),"slot_index",n(0));
        Obj idle=obj("barony_title_id",n(2),"province_id",n(3),"active",new Bool(false),"native_province_monthly_income_observed",new Bool(false),"native_province_monthly_income_raw",Nil.INSTANCE);
        Obj world=obj("status",new Text("source_available"),"snapshot_revision",n(3),"date_raw",n(820),"player_character_id",n(1),"native_final_legality_evaluated",new Bool(true),"native_cost_evaluated",new Bool(false),"player_gold_raw",n(75),
                "active_constructions",new Arr(List.of(idle)),"completed_buildings_observed",new Bool(true),"completed_buildings",new Arr(List.of(tuple)),"positive_income_coverage_complete",new Bool(true),"legal_samples",new Arr(List.of()));
        Obj probe=obj("advertised",new Bool(false),"snapshot_revision",n(3),"date_raw",n(820),"proof_epoch",n(2),"player_world_building_sources",world);
        Obj envelope=obj("type",new Text("command_result"),"protocol_version",n(1),"request_id",new Text("current-material-read"),"ok",new Bool(true),"result",obj("step",new Text("g2_player_construction_view_probe_v1"),"accepted",new Bool(true),"private_probe",probe));
        return obj("schema",new Text("xar.construction-query-observation-input.v1"),"starting_snapshot",snapshot,"ending_snapshot",snapshot,"native_envelope",envelope,"expected_revision",n(3),"native_query_request_id",new Text("current-material-read"),"material_receipt",new Bool(true),"wartime_observation",new Bool(false));
    }
}
