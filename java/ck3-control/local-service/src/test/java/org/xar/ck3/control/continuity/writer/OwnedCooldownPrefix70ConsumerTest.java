package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverPersistentPlanningState;
import org.xar.ck3.control.application.capabilities.DriverRuntimeCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown;
import org.xar.ck3.control.nativebridge.capabilities.army.DeclarationOpportunityCooldown.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Store/Writer/Archive historical consumer; archived pure JSON is never a Root or action authority. */
final class OwnedCooldownPrefix70ConsumerTest {
    private static final String MACHINE = "driver-complete333";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(8, 4L * 1024 * 1024, 32);
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) try { storage.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        final Layout layout;
        final ExactRef source;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(String name) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software source320", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no fixture ledger commits"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer, loader);
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }


    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software333","bridge_pid":123,"episode_character_id":73,"episode_run_id":"episode333",
         "last_checkpoint":null,"command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"goal333"},"rollback_war_failures":null}
        """;
    private static byte[] driver(int revision) { return bytes(DRIVER.replace("goal333", "goal333-" + revision)); }
    private static final String NATIVE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
         "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"original_metric":1.00}
        """;

    private record Originals(RawJson driver, RawJson manifest, ExactRef manifestRef, byte[] packet,
            ExactRef nativeRef, NativeEffectEvidence.FrameBasis basis) { }
    private Originals originals(Fixture f,long version) { return originals(f,version,73); }
    private Originals originals(Fixture f,long version,int nativeActor) {
        byte[] raw = DriverStateSnapshot.decodeComplete(driver(0)).encode();
        var material = RawJson.fullMaterial(raw); ExactRef driverRef = f.archive.preserveMaterial(material);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var known = DriverFactsRepository.imported(driverRef, raw, 3, 7, game, new OpportunityJson.Obj(Map.of()));
        String nativeState=NATIVE.strip().replace("\"character_id\":73","\"character_id\":"+nativeActor);
        byte[] packetJson = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot333\",\"revision\":9,\"state\":" + nativeState + "}");
        byte[] packet = ByteBuffer.allocate(packetJson.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packetJson.length).put(packetJson).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game, BigInteger.valueOf(5), "session333"),
                "snapshot333", BigInteger.valueOf(9), new RawJson(bytes(nativeState)), packet, NOW);
        ExactRef nativeRef = f.archive.preserveNativeFrame(actual);
        var source = new G2Source(MACHINE, NOW.toString(), "source333", f.source);
        var extras=version==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                ? new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign"))) : new OpportunityJson.Obj(Map.of());
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO, version, source, extras, driverRef);
        ExactRef manifestRef = f.archive.preserveMaterial(manifest);
        return new Originals(material, manifest, manifestRef, packet, nativeRef, new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef));
    }



    private record Chain(DriverObservationAssembler.Complete frame,Originals originals,
            DeclarationOpportunityCooldown.Reduction reduction,OpportunityJson.Obj frameRefs,
            ExactRef first,ExactRef second,OpportunityJson.Obj auxiliary) { }

    @Test void actualHeldHistoricalScopeReplaysTwoProofsReentersAndAppendsSuffixWhilePublicFacadeRemainsFull() throws IOException {
        var f=new Fixture("prefix-consumer");var original=originals(f,1);
        Chain chain=f.writer.locked(session->f.archive.inSession(session,bound->{
            var frame=f.loader.load(original.basis(),bound);
            Frame identity=DeclarationOpportunityCooldown.frame(frame);
            Snapshot snapshot=DeclarationOpportunityCooldown.snapshot(DriverJson.toNode(frame.semantic()));
            State state=DeclarationOpportunityCooldown.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(),identity);
            Reduction initial=DeclarationOpportunityCooldown.view(state,snapshot,identity);
            Obj frameRefs=new Obj(Map.of("manifest",frame.semantic().get("java_driver_facts_evidence"),"native",reference(frame.originalEvidence())));
            Obj input=new Obj(Map.of("configured_path",new Text("D:/pure-data70/"+DeclarationOpportunityCooldown.LEGACY_FILENAME),
                    "observed_at",new Text(NOW.toString()),"original",Nil.INSTANCE,"saved",Nil.INSTANCE,"baseline_receipts",new Arr(List.of())));
            ExactRef first=bound.preserveMaterial(new RawJson(DriverJson.encode(proof("INITIAL",Nil.INSTANCE,frameRefs,input,initial,new Arr(List.of())))));
            Reduction view=DeclarationOpportunityCooldown.view(initial.state(),snapshot,identity);
            ExactRef second=bound.preserveMaterial(new RawJson(DriverJson.encode(proof("VIEW",reference(first),frameRefs,Nil.INSTANCE,view,new Arr(List.of())))));
            assertNotEquals(first,second);
            return new Chain(frame,original,view,frameRefs,first,second,auxiliary(second,view));
        }));
        Frame suffixIdentity=DeclarationOpportunityCooldown.frame(chain.frame());
        Snapshot suffixSnapshot=DeclarationOpportunityCooldown.snapshot(DriverJson.toNode(chain.frame().semantic()));
        Reduction suffix=DeclarationOpportunityCooldown.view(chain.reduction().state(),suffixSnapshot,suffixIdentity);
        Obj next=proof("VIEW",reference(chain.second()),chain.frameRefs(),Nil.INSTANCE,suffix,new Arr(List.of()));
        ExactRef third=f.archive.preserveMaterial(new RawJson(DriverJson.encode(next)));
        Obj appended=auxiliary(third,suffix);
        byte[] before=DriverJson.encode(chain.auxiliary());
        scope(f,"cold-one",(session,bound)->{
            assertNotNull(f.archive.ownedPersistentPrefixAccess(bound,session));
            assertTrue(f.archive.ownedPersistentPrefixAccess(bound,session).accepts(bound));
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);return null;
        });
        scope(f,"warm-two",(session,bound)->{
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            var alias=bound.withSession(session);
            assertNotNull(f.archive.ownedPersistentPrefixAccess(alias,session));
            DriverPersistentPlanningState.replay(chain.auxiliary(),alias);
            return null;
        });
        scope(f,"public-full-two",(session,bound)->{
            var calls=new ArrayList<String>();var publicFacade=observedPublicFacade(bound,calls);
            assertNull(f.archive.ownedPersistentPrefixAccess(publicFacade,session),"a public proxy is never the installed private source facade");
            DriverPersistentPlanningState.replay(chain.auxiliary(),publicFacade);
            List<String> first=List.copyOf(calls);calls.clear();
            DriverPersistentPlanningState.replay(chain.auxiliary(),publicFacade);
            assertEquals(first,calls,"the public facade always executes its original full route");
            ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(original.manifestRef(),original.manifest());
            assertEquals(List.of("M:"+chain.second().sha256(),"M:"+chain.first().sha256(),
                    "M:"+original.manifestRef().sha256(),"N:"+original.nativeRef().sha256(),"M:"+driver.sha256(),
                    "M:"+original.manifestRef().sha256(),"N:"+original.nativeRef().sha256(),"M:"+driver.sha256()),first);
            return null;
        });
        scope(f,"warm-append",(session,bound)->{
            ExactRef head=session.persistedHead();
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            assertNotEquals(chain.second(),third);
            DriverPersistentPlanningState.replay(appended,bound);DriverPersistentPlanningState.replay(appended,bound);
            assertEquals(chain.auxiliary().get(DriverPersistentPlanningState.COOLDOWN_STATE),appended.get(DriverPersistentPlanningState.COOLDOWN_STATE));
            assertEquals(chain.auxiliary().get(DeclarationOpportunityCooldown.VIEW_KEY),appended.get(DeclarationOpportunityCooldown.VIEW_KEY));
            assertEquals(head,session.persistedHead(),"CAS source JSON publication never commits a canonical ledger transition");
            return null;
        });
        assertArrayEquals(before,DriverJson.encode(chain.auxiliary()));
    }

    @Test void changedAuxiliaryAndProcessedSuffixStillRejectAfterARealVerifiedPrefix() throws IOException {
        var f=new Fixture("prefix-failure");var original=originals(f,1);
        Chain chain=f.writer.locked(session->f.archive.inSession(session,bound->{
            var frame=f.loader.load(original.basis(),bound);Frame identity=DeclarationOpportunityCooldown.frame(frame);
            Reduction initial=DeclarationOpportunityCooldown.view(DeclarationOpportunityCooldown.decode(com.fasterxml.jackson.databind.node.NullNode.getInstance(),identity),
                    DeclarationOpportunityCooldown.snapshot(DriverJson.toNode(frame.semantic())),identity);
            Obj frameRefs=new Obj(Map.of("manifest",frame.semantic().get("java_driver_facts_evidence"),"native",reference(frame.originalEvidence())));
            Obj input=new Obj(Map.of("configured_path",new Text("D:/pure-data70/"+DeclarationOpportunityCooldown.LEGACY_FILENAME),"observed_at",new Text(NOW.toString()),
                    "original",Nil.INSTANCE,"saved",Nil.INSTANCE,"baseline_receipts",new Arr(List.of())));
            ExactRef first=bound.preserveMaterial(new RawJson(DriverJson.encode(proof("INITIAL",Nil.INSTANCE,frameRefs,input,initial,new Arr(List.of())))));
            Reduction view=DeclarationOpportunityCooldown.view(initial.state(),DeclarationOpportunityCooldown.snapshot(DriverJson.toNode(frame.semantic())),identity);
            ExactRef second=bound.preserveMaterial(new RawJson(DriverJson.encode(proof("VIEW",reference(first),frameRefs,Nil.INSTANCE,view,new Arr(List.of())))));
            return new Chain(frame,original,view,frameRefs,first,second,auxiliary(second,view));
        }));
        Obj badProcessed=proof("VIEW",reference(chain.second()),chain.frameRefs(),Nil.INSTANCE,chain.reduction(),new Arr(List.of(reference(chain.first()))));
        ExactRef badProcessedRef=f.archive.preserveMaterial(new RawJson(DriverJson.encode(badProcessed)));
        scope(f,"bad-auxiliary",(session,bound)->{
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            var bad=chain.auxiliary().with(DriverPersistentPlanningState.COOLDOWN_STATE,new Bool(true));
            var failure=assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(bad,bound));
            assertEquals("persistent cooldown auxiliary differs from its complete source chain",failure.getMessage());
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            return null;
        });
        scope(f,"bad-processed",(session,bound)->{
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);
            var failure=assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(auxiliary(badProcessedRef,chain.reduction()),bound));
            assertEquals("non-life transition changed processed receipts",failure.getMessage());
            DriverPersistentPlanningState.replay(chain.auxiliary(),bound);return null;
        });
    }

    @FunctionalInterface private interface Scoped<T>{T run(ContinuityStorePort.Session session,ActionPorts.OutcomeArchive archive)throws IOException;}
    private <T>T scope(Fixture f,String label,Scoped<T> operation)throws IOException{
        System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"PREFIX70_TEST_SCOPE_BEGIN label="+label);
        T result=f.writer.locked(session->f.archive.inHistoricalReadScope(session,LIMITS,bound->operation.run(session,bound)));
        System.getLogger(ImmutableArtifactStore.class.getName()).log(System.Logger.Level.INFO,"PREFIX70_TEST_SCOPE_END label="+label);
        return result;
    }
    private static ActionPorts.OutcomeArchive observedPublicFacade(ActionPorts.OutcomeArchive target,List<String> calls){
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(method.getName().equals("loadMaterial"))calls.add("M:"+((ExactRef)args[0]).sha256());
            if(method.getName().equals("loadNativeFrame"))calls.add("N:"+((ExactRef)args[0]).sha256());
            try{return method.invoke(target,args);}catch(java.lang.reflect.InvocationTargetException problem){throw problem.getCause();}
        });
    }
    private static Obj proof(String mode,Value previous,Obj frame,Value input,Reduction reduction,Arr processed){
        return new Obj(Map.of("schema",new Text("xar.driver-persistent-planning-source/v2"),"mode",new Text(mode),"previous",previous,
                "frame",frame,"input",input,"state",node(DeclarationOpportunityCooldown.encode(reduction.state())),
                "view",node(DeclarationOpportunityCooldown.encodeView(reduction.view())),"processed",processed));
    }
    private static Obj auxiliary(ExactRef source,Reduction reduction){
        return new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_SOURCE,reference(source),DriverPersistentPlanningState.COOLDOWN_STATE,
                node(DeclarationOpportunityCooldown.encode(reduction.state())),DeclarationOpportunityCooldown.VIEW_KEY,node(DeclarationOpportunityCooldown.encodeView(reduction.view()))));
    }
    private static Obj node(com.fasterxml.jackson.databind.JsonNode value){return object(parse(StrictJson.canonical(value)),"typed cooldown DATA");}
    private static Obj reference(ExactRef ref){return DriverRuntimeCapabilities.referenceJson(ref);}
}
