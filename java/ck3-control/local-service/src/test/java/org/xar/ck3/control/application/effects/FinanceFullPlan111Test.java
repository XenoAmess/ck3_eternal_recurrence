package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;
import org.xar.ck3.control.wave2.finance.giftpending.*;

/** Public software packet/collector/writer/archive integration, never a live Game or action/SAVE qualification.
 * The checkpoint and seven clear domain producers are explicitly software fixtures in this same writer.
 * Read results adapt retained producer DATA to actor73/native2/date INITIAL_DATE_RAW; they are not original packets. */
final class FinanceFullPlan111Test {
    @TempDir Path directory;
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final int LIMIT=1024*1024;
    private static final List<FinanceStatePort.Domain> DOMAINS=List.of(FinanceStatePort.Domain.CONSTRUCTION,FinanceStatePort.Domain.FACTION_GIFT,
            FinanceStatePort.Domain.MERCENARY,FinanceStatePort.Domain.FEAST,FinanceStatePort.Domain.FIRST_HEIR_MARRIAGE,
            FinanceStatePort.Domain.CHILD_MARRIAGE,FinanceStatePort.Domain.CHILD_DEFAULT_MARRIAGE);
    private record Body(FinanceStatePort.ReaderBinding reader,DomainBodies.Registration registration,byte[] raw) { }
    @FunctionalInterface private interface ArchiveWork { void run()throws IOException; }

    @Test void smallRequestKeepsLegacyInlineQuoteAndReplaysTheCompletePublicChain()throws Exception { exercise(false); }
    @Test void largeRequestUsesExactFullMaterialAndBothReadersRejectMissingWrongOrForeignOriginals()throws Exception { exercise(true); }

    private void exercise(boolean large)throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        var bodies=new ArrayList<Body>();
        var suppliedPrivate=new AtomicReference<RawJson>();
        var scenario=scenario(definitions,source,suppliedPrivate);
        var giftAction=new ActionWriterIntegrationFixture.SoftwareActionScenario(OrdinaryFinancePolicies.GIFT,"game.command."+OrdinaryFinancePolicies.GIFT.value(),
                (command,attempt,dispatch)->{throw new AssertionError("quote-only DATA cannot observe an action");},
                ()->{throw new AssertionError("quote-only DATA cannot dispatch an action");});
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve(large?"large":"small"),false,scenario,List.of(giftAction),List.of(),
                ref->registerBodies(ref,bodies))) {
            fixture.enqueueSoftwareNativePacket(snapshot(large));
            var initial=fixture.ready();
            var published=initial.request().observations();
            assertTrue(published.actionSteps().contains(OrdinaryFinancePolicies.GIFT),"actual published registration must include Gift");
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                for(var body:bodies) {
                    var scoped=fixture.archive.withSession(same);ExactRef original=scoped.preserveMaterial(new RawJson(body.raw()));
                    var submitted=new DomainBodies.ImportRequest(body.registration().slot(),body.registration().contractSchema(),original,
                            body.raw(),body.registration().producerSources(),"p111-software-import:"+body.registration().slot());
                    same.commitImport(same.previewImport(submitted));
                }
                byte[] ledgerBefore=fixture.ledgerBytes();var headBefore=same.persistedHead();
                var domainBefore=new java.util.EnumMap<DomainBodies.Slot,byte[]>(DomainBodies.Slot.class);
                for(var body:bodies)domainBefore.put(body.registration().slot(),assertInstanceOf(DomainBodies.Available.class,same.readDomain(body.registration().slot())).canonicalBody());
                var afterCapture=new AtomicReference<ArchiveWork>();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(25),lease->{
                    var complete=lease.frame();Instant deadline=Instant.now().plusSeconds(25);
                    var request=new PlanningRequest(complete.identity(),complete.source(),complete.sessionId(),deadline,
                            new PlanningObservation(complete.semantic(),published.history(),published.actionSteps(),published.bridgeCapabilities(),
                                    published.battleSpeedReadiness(),published.actionFacts(),published.campaignGoal(),published.crossRunPlan(),published.initialLifestyleFocusRequired()));
                    var checkpoint=fixture.archive.withSession(same).preserveMaterial(new RawJson("{\"SOFTWARE_CHECKPOINT_NOT_SAVE\":true}".getBytes(StandardCharsets.UTF_8)));
                    var bindings=bodies.stream().map(body->new CanonicalFinanceStateSource.Binding(body.reader(),body.registration().slot(),body.registration().contractSchema(),
                            body.registration().maximumBodyBytes(),body.registration().producerSources())).toList();
                    var originalState=new CanonicalFinanceStateSource(fixture.root.resolve("ROOT-CONTINUITY-WINDOW.lock"),fixture.writer,new ActionSnapshotReader(fixture.journal),
                            (held,expected)->fixture.collector.current(held,expected.before(),expected.deadline(),current->current.frame().identity()),
                            held->Optional.of(new FinanceStatePort.Checkpoint(checkpoint,complete.identity().frame().episodeRunId(),complete.identity().frame().identity().dateRaw())),bindings);
                    var state=new FinanceStatePort(originalState,originalState.owningReaders());
                    var collector=new OrdinaryFinanceCollector(definitions.get(),fixture.reads,state,()->same);
                    var current=known(collector.current(same,request));
                    var giftRead=collector.gift(same,request,current);
                    if(giftRead instanceof OrdinaryFinanceCollector.Unavailable<?>) {
                        var evaluated=org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec.evaluatePrivateCandidate(
                                DriverJson.encode(request.observations().snapshot()),
                                org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec.decodeRootProjection(DriverJson.encode(current.root())),
                                suppliedPrivate.get().bytes(),BigInteger.valueOf(10000000));
                        System.out.println("P111 source DATA diagnostic "+new String(org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec.encodeCandidateResult(evaluated),StandardCharsets.UTF_8));
                        System.out.println("P111 current frame "+request.before().frame()+" ROOT="+current.root().get("player_character_id")+"/"+current.root().get("snapshot_revision")+"/"+current.root().get("date_raw")
                                +" direct="+current.root().get("direct_landed_vassal_character_ids"));
                    }
                    var gift=known(giftRead);
                    assertEquals(4,gift.originalReads().size());assertTrue(gift.cash().newGiftSpendingAllowed());
                    var quotes=archive(fixture,same,definitions.get(),source.get(),originalState.owningReaders());
                    Obj args=obj("choice",object(parse(FactionGiftPolicy.encode(gift.selected())),"actual choice"),
                            "minimum_gold_reserve_raw",new IntegerValue(gift.minimumGoldReserveRaw()),"candidate",gift.candidate(),"pre_faction_alert",gift.nativeAlert(),
                            "source_frame",OrdinaryFinanceCollector.sourceFrame(request),"checkpoint_sha256",new Text(gift.checkpoint().saveReference().sha256()));
                    byte[] originalWire=PlanningWire.encodeRequest(request);assertEquals(large,originalWire.length>LIMIT);
                    Obj bound=quotes.bind(same,request,OrdinaryFinancePolicies.GIFT,current,Optional.of(gift),args);
                    var command=new ActionCommand("p111-quote-only-"+(large?"large":"small"),request.before(),request.source(),request.sessionId(),OrdinaryFinancePolicies.GIFT,bound,
                            NativeFinanceEffects.expected(OrdinaryFinancePolicies.GIFT,request,bound).orElseThrow(),
                            new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(gift.selected().recipientCharacterId()),Set.of("faction-gift:"+gift.selected().sourceFactionId())),deadline);
                    ArchiveWork replay=()->{
                    var scoped=fixture.archive.withSession(same);ExactRef quoteRef=FinanceEvidenceArchive.reference(bound);
                    byte[] quoteWire=scoped.loadMaterial(quoteRef).bytes();ObjectNode manifest=(ObjectNode)StrictJson.parse(quoteWire,LIMIT);
                    assertEquals(large?"xar.java.finance-original-quote/v3":FinanceEvidenceArchive.SCHEMA,manifest.path("schema").textValue());
                    assertEquals(!large,manifest.has("planning_request"));assertEquals(large,manifest.has("planning_request_ref"));assertTrue(quoteWire.length<=LIMIT);
                    assertEquals(6,manifest.path("documents").size());assertEquals(4,manifest.path("reads").size());
                    quotes.verify(same,command);
                    assertArrayEquals(originalWire,PlanningWire.encodeRequest(quotes.originalRequest(same,command)));
                    var cold=archive(fixture,same,definitions.get(),source.get(),originalState.owningReaders());
                    cold.verify(same,command);assertArrayEquals(originalWire,PlanningWire.encodeRequest(cold.originalRequest(same,command)));
                    if(large) {
                        ExactRef planRef=ExactRef.fromJson(manifest.get("planning_request_ref"));
                        assertEquals(originalWire.length,planRef.bytes());assertEquals(ActionCodec.sha256(originalWire),planRef.sha256());
                        assertArrayEquals(originalWire,scoped.loadFullMaterial(planRef).bytes());
                        assertArrayEquals(originalWire,PlanningWire.encodeRequest(PlanningWire.decodeRequest(scoped.loadFullMaterial(planRef).bytes())));
                        var fullReads=new AtomicInteger();var planOrdinaryReads=new AtomicInteger();
                        ActionPorts.OutcomeArchive strict=lane(scoped,planRef,fullReads,planOrdinaryReads,false);
                        quotes.verify(command,strict);assertTrue(fullReads.get()>0);assertEquals(0,planOrdinaryReads.get());
                        assertThrows(UnsupportedOperationException.class,()->quotes.verify(command,lane(scoped,planRef,new AtomicInteger(),new AtomicInteger(),true)));
                        invalidVersionsAndOriginals(quotes,same,command,manifest,scoped,planRef,originalWire);
                    } else {
                        assertArrayEquals(quoteWire,FinanceEvidenceArchive.quoteBytes(FinanceEvidenceArchive.quoteObject(new RawJson(quoteWire))));
                    }
                    assertArrayEquals(originalWire,PlanningWire.encodeRequest(request));
                    System.out.println("P111 "+(large?"v3":"v2")+" planning="+originalWire.length+" manifest="+quoteWire.length+" sha="+ActionCodec.sha256(originalWire));
                    };
                    // Cold/negative archive replay is read-only and needs the held writer, not an open physical capture.
                    // Keep the original request/command deadline; close and validate that capture before the long replay.
                    if(large)afterCapture.set(replay);else replay.run();
                    return null;
                });
                if(large)java.util.Objects.requireNonNull(afterCapture.get(),"original large quote capture must finish before replay").run();
                assertEquals(headBefore,same.persistedHead());assertArrayEquals(ledgerBefore,fixture.ledgerBytes());
                for(var body:bodies)assertArrayEquals(domainBefore.get(body.registration().slot()),assertInstanceOf(DomainBodies.Available.class,same.readDomain(body.registration().slot())).canonicalBody());
                assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    private void invalidVersionsAndOriginals(FinanceEvidenceArchive quotes,Session same,ActionCommand command,ObjectNode manifest,
            ActionPorts.OutcomeArchive scoped,ExactRef planRef,byte[] original)throws IOException {
        for(JsonNode schema:List.of(StrictJson.object().put("x","unsupported").get("x"),com.fasterxml.jackson.databind.node.NullNode.instance,
                com.fasterxml.jackson.databind.node.IntNode.valueOf(3))) {
            ObjectNode changed=manifest.deepCopy();changed.set("schema",schema);reject(quotes,same,command,scoped,changed);
        }
        ObjectNode missingSchema=manifest.deepCopy();missingSchema.remove("schema");reject(quotes,same,command,scoped,missingSchema);
        ObjectNode mixed=manifest.deepCopy();mixed.set("planning_request",StrictJson.object());reject(quotes,same,command,scoped,mixed);
        ObjectNode legacyWithRef=manifest.deepCopy();legacyWithRef.put("schema",FinanceEvidenceArchive.SCHEMA);reject(quotes,same,command,scoped,legacyWithRef);
        var foreign=directory.resolve("external-same-bytes.json");Files.write(foreign,original);
        var missing=Path.of(planRef.path()).getParent().resolve("f".repeat(64)+".bin");
        var badSha=new ExactRef(planRef.path(),planRef.bytes(),"0".repeat(64));
        var wrongBytes=scoped.preserveMaterial(RawJson.fullMaterial("{\"not_a_planning_request\":true}".getBytes(StandardCharsets.UTF_8)));
        for(ExactRef ref:List.of(new ExactRef(foreign.toAbsolutePath().toString(),original.length,ActionCodec.sha256(original)),
                new ExactRef(missing.toAbsolutePath().toString(),original.length,"f".repeat(64)),badSha,wrongBytes,
                new ExactRef(planRef.path(),(long)RawJson.MAXIMUM_BYTES+1,planRef.sha256()))) {
            ObjectNode changed=manifest.deepCopy();changed.set("planning_request_ref",ref.toJson());reject(quotes,same,command,scoped,changed);
        }
        // A framed Native packet is not an interchangeable full JSON document.
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(NativeWire.packet("{\"not_planning\":true}".getBytes(StandardCharsets.UTF_8))));
    }
    private static void reject(FinanceEvidenceArchive quotes,Session same,ActionCommand command,ActionPorts.OutcomeArchive scoped,ObjectNode changed) {
        ExactRef ref=scoped.preserveMaterial(new RawJson(StrictJson.canonical(changed,LIMIT)));
        Obj args=command.arguments().with(FinanceEvidenceArchive.ARGUMENT,object(parse(StrictJson.canonical(ref.toJson())),"changed quote ref"));
        var other=new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),command.operation(),args,command.expected(),command.claims(),command.deadline());
        assertThrows(RuntimeException.class,()->quotes.verify(same,other));
        assertThrows(RuntimeException.class,()->quotes.originalRequest(same,other));
    }
    private static ActionPorts.OutcomeArchive lane(ActionPorts.OutcomeArchive actual,ExactRef plan,AtomicInteger full,AtomicInteger ordinary,boolean unsupported) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(FinanceFullPlan111Test.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
            if(method.getName().equals("loadFullMaterial")){full.incrementAndGet();if(unsupported)throw new UnsupportedOperationException("strict legacy port has no full lane");}
            if(method.getName().equals("loadMaterial")&&plan.equals(args[0])){ordinary.incrementAndGet();throw new AssertionError("full planning original cannot use the ordinary lane");}
            try{return method.invoke(actual,args);}catch(InvocationTargetException failure){throw failure.getCause();}
        });
    }
    @Test void legacyStructureCodecRetainsItsOriginalBytesCapAndDecimalRejection() {
        ObjectNode legacy=StrictJson.object();for(String name:List.of("operation","before","source","session_id","arguments","canonical_head","head_archive","spending","documents","reads","planning_request"))legacy.putNull(name);
        legacy.put("schema",FinanceEvidenceArchive.SCHEMA);byte[] bytes=FinanceEvidenceArchive.quoteBytes(legacy);
        assertArrayEquals(bytes,FinanceEvidenceArchive.quoteBytes(FinanceEvidenceArchive.quoteObject(new RawJson(bytes))));
        ObjectNode tooLarge=legacy.deepCopy();tooLarge.put("planning_request","x".repeat(LIMIT));
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteBytes(tooLarge));
        byte[] decimal=new String(bytes,StandardCharsets.UTF_8).replace("\"planning_request\":null","\"planning_request\":1.0").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->FinanceEvidenceArchive.quoteBytes(FinanceEvidenceArchive.quoteObject(new RawJson(decimal))));
    }
    private static FinanceEvidenceArchive archive(ActionWriterIntegrationFixture fixture,Session same,FinanceReadContracts definitions,ExactRef source,List<FinanceStatePort.ReaderBinding> readers) {
        return new FinanceEvidenceArchive(fixture.writer,fixture.archive,()->same,fixture.physicalInputs().originals(),fixture.frameLoader(),definitions,readers,source,
                (held,root,guard,frame,scoped)->{throw new AssertionError("same-frame software quote must not use historical ROOT replay");});
    }
    private static <T>T known(OrdinaryFinanceCollector.Read<T> read) {
        assertInstanceOf(OrdinaryFinanceCollector.Known.class,read,read::toString);return ((OrdinaryFinanceCollector.Known<T>)read).value();
    }
    private static List<DomainBodies.Registration> registerBodies(ExactRef source,List<Body> bodies) {
        for(var domain:DOMAINS) {
            DomainBodies.Slot slot=slot(domain);String schema=domain==FinanceStatePort.Domain.MERCENARY?MercenaryProcurement.SCHEMA:domain==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingModel.SCHEMA:"fixture.owned-submission/v1";
            byte[] raw=domain==FinanceStatePort.Domain.MERCENARY?MercenaryProcurement.encode(MercenaryProcurement.emptyFreshEpisode()):
                    domain==FinanceStatePort.Domain.FACTION_GIFT?GiftPendingCodec.encodeLedger(GiftPendingModel.Ledger.empty()):encode(obj("schema",new Text(schema),"pending",Nil.INSTANCE));
            var reader=domain==FinanceStatePort.Domain.FACTION_GIFT?FinanceStatePort.giftReader(source):new FinanceStatePort.ReaderBinding(domain,source,original->{
                if(domain==FinanceStatePort.Domain.MERCENARY)return MercenaryProcurement.decode(original.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR;
                Obj decoded=object(parse(original.bytes()),"software domain body");assertEquals(Set.of("schema","pending"),decoded.members().keySet());
                assertEquals(new Text(schema),decoded.get("schema"));assertEquals(Nil.INSTANCE,decoded.get("pending"));return FinanceStatePort.Pending.CLEAR;
            });
            var registration=new DomainBodies.Registration(slot,schema,ContinuityJson.DOMAIN_MAX_BYTES,List.of(source),(head,previous,submitted,actual)->{
                assertTrue(previous.isEmpty());assertArrayEquals(raw,actual);assertArrayEquals(WriterContracts.canonical(raw),submitted.producerInput());
                reader.reader().decode(new FinanceStatePort.Document(domain,submitted.originalBody(),actual));return ActionCodec.sha256(actual);
            });bodies.add(new Body(reader,registration,raw));
        }
        return bodies.stream().map(Body::registration).toList();
    }
    private static DomainBodies.Slot slot(FinanceStatePort.Domain domain) {return switch(domain){
        case CONSTRUCTION->DomainBodies.Slot.CONSTRUCTION;case FACTION_GIFT->DomainBodies.Slot.FACTION;case MERCENARY->DomainBodies.Slot.MERCENARY;
        case FEAST->DomainBodies.Slot.FEAST;case FIRST_HEIR_MARRIAGE->DomainBodies.Slot.FAMILY;case CHILD_MARRIAGE->DomainBodies.Slot.CHILD_MATRILINEAL;
        case CHILD_DEFAULT_MARRIAGE->DomainBodies.Slot.DEFAULT_MARRIAGE;default->throw new AssertionError(domain);};}
    private static void initialize(ActionWriterIntegrationFixture fixture,Session same,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity initial)throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.withSession(same).preserveMaterial(new RawJson("{\"actual_software_start_policy\":true}".getBytes(StandardCharsets.UTF_8)));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }
    private static byte[] snapshot(boolean large)throws IOException {
        ObjectNode state=StrictJson.object().put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW);
        state.putObject("played_character").put("character_id",73).put("alive",true);state.putObject("played_character_gold").put("raw",100000000).put("scale",100000);
        state.putNull("active_event");state.putNull("pending_character_interaction");state.put("one_life_terminal",false).putNull("one_life_terminal_reason");state.put("episode_identity_pending",false);
        state.putArray("active_wars");state.putArray("player_armies");state.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",5);
        if(large) {
            ObjectNode extension=state.putObject("opaque_unconsumed_extension").put("y",2).put("x",1).put("retained_text","x".repeat(LIMIT+4096));
            extension.set("decimal_lexemes",FullJsonTree.parse("{\"one\":1.00,\"minus_zero\":-0.0}".getBytes(StandardCharsets.UTF_8),4096));
        }
        ObjectNode packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:2").put("revision",2);packet.set("state",state);
        return NativeWire.packet(org.xar.ck3.control.contracts.FullJsonTree.encode(packet,RawJson.MAXIMUM_BYTES));
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> selected,AtomicReference<ExactRef> source,AtomicReference<RawJson> suppliedPrivate)throws Exception {
        var preview=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(resource("/finance/faction-generation-native90/packets/faction-zero-final/private-query-faction-gift-member-v1.json.packet.bin")));
        ObjectNode privateResult=(ObjectNode)StrictJson.parse(preview.result().token().orElseThrow().value());
        ObjectNode observation=(ObjectNode)privateResult.path("native").path("observation");BigInteger actor=BigInteger.valueOf(73),recipient=observation.get("recipient_character_id").bigIntegerValue();
        observation.put("snapshot_revision",2).put("native_snapshot_revision",2).put("observed_date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW)
                .put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("player_character_id",actor).put("source_faction_target_character_id",actor).put("player_gold_raw",100000000);
        ObjectNode targeting=(ObjectNode)privateResult.path("native").path("direct_targeting_rows");targeting.put("snapshot_revision",2).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("player_character_id",actor);
        for(JsonNode row:targeting.path("factions"))((ObjectNode)row).put("target_character_id",actor);
        ObjectNode root=(ObjectNode)StrictJson.parse(resource("/finance/faction-generation-native90/authored-root.json"));remap(root,BigInteger.valueOf(12345),actor);remap(root,BigInteger.valueOf(23456),recipient);
        root.put("snapshot_revision",2).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("player_targeting_faction_count",1);root.putNull("player_heir_candidate_v1");
        ObjectNode alerts=alert(observation,actor,recipient);
        suppliedPrivate.set(new RawJson(StrictJson.canonical(privateResult)));
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA.toLowerCase(java.util.Locale.ROOT),"finance-full-plan111",ref->{
            source.set(ref);var definitions=new FinanceReadContracts(query->{String permission="game.command."+query.operation().value();
                return new FinanceReadContracts.Registration(ref,new FinanceReadContracts.Permission(Optional.of(permission),permission,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));});
            selected.set(definitions);return List.of(definitions.contract(FinanceReadContracts.Query.ROOT),definitions.contract(FinanceReadContracts.Query.MERCENARIES),
                    definitions.contract(FinanceReadContracts.Query.FACTION_GIFT),definitions.contract(FinanceReadContracts.Query.FACTION_ALERTS));
        },request->{
            if(request.step().equals(FinanceReadContracts.Query.FACTION_GIFT.operation().value()))return suppliedPrivate.get();
            if(request.step().equals(FinanceReadContracts.Query.FACTION_ALERTS.operation().value()))return new RawJson(StrictJson.canonical(alerts));
            ObjectNode result=StrictJson.object().put("step",request.step()).put("accepted",true).put("snapshot_revision",2);
            if(request.step().equals(FinanceReadContracts.Query.ROOT.operation().value())) {
                result.put("status","available").put("query_sequence",1).put("backend_id","native-headless");result.set("campaign_root_context",root);
            } else {
                assertEquals(FinanceReadContracts.Query.MERCENARIES.operation().value(),request.step());
                ObjectNode market=result.putObject("player_mercenary_context").put("schema","ck3_12004_player_mercenary_context_v1").put("game_version","1.20.0.4").put("executable_sha256",SHA)
                        .put("actor_character_id",actor).put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("capture_epoch",1).put("read_only",true).put("native_hire_mode",1).put("available",true);
                market.putNull("unavailable_reason");market.putArray("rows");
            }
            return new RawJson(StrictJson.canonical(result));
        },Optional.of("1.20.0.4"),Set.of());
    }
    private static byte[] resource(String path)throws IOException {try(var stream=FinanceFullPlan111Test.class.getResourceAsStream(path)){if(stream==null)throw new IOException("required retained DATA missing: "+path);return stream.readAllBytes();}}
    private static final Set<String> CHARACTER_FIELDS=Set.of("player_character_id","top_liege_character_id","immediate_liege_character_id","first_heir_character_id","owner_character_id","incumbent_character_id","character_id");
    private static final Set<String> CHARACTER_VECTORS=Set.of("primary_title_succession_character_ids","direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids");
    private static void remap(ObjectNode root,BigInteger old,BigInteger replacement) {
        remapValue(root,"",old,replacement);
        for(String field:List.of("direct_landed_vassal_character_ids","adjacent_external_province_holder_character_ids")) {
            var values=new ArrayList<JsonNode>();root.get(field).forEach(values::add);values.sort(Comparator.comparing(JsonNode::bigIntegerValue));root.putArray(field).addAll(values);
        }
        var related=new ArrayList<JsonNode>();root.get("related_character_contexts").forEach(related::add);
        related.sort(Comparator.comparing(item->item.get("character_id").bigIntegerValue()));root.putArray("related_character_contexts").addAll(related);
    }
    private static void remapValue(JsonNode value,String field,BigInteger old,BigInteger replacement) {
        if(value.isObject()) {
            var object=(ObjectNode)value;var names=new ArrayList<String>();object.fieldNames().forEachRemaining(names::add);
            for(String name:names) {
                JsonNode child=object.get(name);
                if(CHARACTER_FIELDS.contains(name)&&child.isIntegralNumber()&&old.equals(child.bigIntegerValue()))object.put(name,replacement);
                else remapValue(child,name,old,replacement);
            }
        } else if(value.isArray()) {
            var rows=(com.fasterxml.jackson.databind.node.ArrayNode)value;
            for(int index=0;index<rows.size();index++) {
                JsonNode child=rows.get(index);
                if(CHARACTER_VECTORS.contains(field)&&child.isIntegralNumber()&&old.equals(child.bigIntegerValue()))rows.set(index,com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(replacement));
                else remapValue(child,"",old,replacement);
            }
        }
    }
    private static ObjectNode alert(ObjectNode observation,BigInteger actor,BigInteger recipient)throws Exception {
        JsonNode corpus=StrictJson.parse(resource("/factionalerts/original-producer-golden.json"));JsonNode vector=null;
        for(JsonNode row:corpus.get("cases"))if(row.path("name").asText().equals("exact-build-1.20.0.4"))vector=row;
        assertNotNull(vector);ObjectNode frame=(ObjectNode)corpus.path("bases").get(vector.get("base").textValue()).deepCopy();
        for(JsonNode op:vector.get("operations")) {
            String path=op.get("path").textValue();int slash=path.lastIndexOf('/');ObjectNode parent=slash==0?frame:(ObjectNode)frame.at(path.substring(0,slash));
            if(op.path("remove").asBoolean(false))parent.remove(path.substring(slash+1));else parent.set(path.substring(slash+1),op.get("value").deepCopy());
        }
        ObjectNode selected=null;for(JsonNode row:frame.get("targeting_factions"))if(row.path("faction_id").asInt()==771)selected=(ObjectNode)row.deepCopy();
        assertNotNull(selected);BigInteger faction=observation.get("queried_source_faction_id").bigIntegerValue();
        selected.put("faction_id",faction).put("target_character_id",actor).put("leader_character_id",recipient);selected.putArray("character_member_ids").add(recipient);
        frame.put("snapshot_revision",observation.get("snapshot_revision").bigIntegerValue()).put("date_raw",observation.get("observed_date_raw").bigIntegerValue())
                .put("player_character_id",actor).put("targeting_faction_count",1);
        frame.putArray("targeting_factions").add(selected);frame.putArray("county_exposures");
        ObjectNode planner=(ObjectNode)frame.get("planner_projection");planner.putArray("dangerous_faction_ids").add(faction);
        for(String field:List.of("watch_faction_ids","war_handoff_faction_ids","exposed_county_title_ids"))planner.putArray(field);
        ObjectNode result=StrictJson.object().put("step",FactionAlertModel.STEP).put("accepted",true).put("status","available").put("query_sequence",1)
                .put("snapshot_revision",observation.get("snapshot_revision").bigIntegerValue()).put("player_faction_alerts_ready",true).put("backend_id","native-headless");
        result.set("player_faction_alerts",frame);return result;
    }
}
