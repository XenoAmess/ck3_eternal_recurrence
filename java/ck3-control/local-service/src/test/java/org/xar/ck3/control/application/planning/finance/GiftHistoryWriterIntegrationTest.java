package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.Method;
import org.xar.ck3.control.service.root.FactionGiftPublicService;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;

/** Actual software packet/writer middle chain. Uses the production Gift material projector, reducer, archives and publisher.
 * The marker quote is explicitly unqualified: full Finance quote/permission/private Root/MCP/Game acceptance is excluded. */
final class GiftHistoryWriterIntegrationTest {
    @TempDir Path root;
    private static BigInteger n(long value){return BigInteger.valueOf(value);}
    private record Change(String kind,Function<Optional<Ledger>,Ledger> replay) { }
    private static final class Domain {
        private final ExactRef source;private final AtomicReference<ActionWriterIntegrationFixture> fixture;
        private final ThreadLocal<Change> active=new ThreadLocal<>();
        Domain(ExactRef source,AtomicReference<ActionWriterIntegrationFixture> fixture){this.source=source;this.fixture=fixture;}
        DomainBodies.Registration registration() {
            return new DomainBodies.Registration(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,GiftPendingCodec.MAX_BYTES,List.of(source),
                    (head,previous,request,raw)->{
                        var actual=fixture.get();Session same=actual.journal.borrowedWriterSession();actual.writer.requireSession(same);
                        Change change=java.util.Objects.requireNonNull(active.get(),"actual software reducer transition absent");
                        assertEquals(head.toJson(),same.head().state().toJson());assertEquals(DomainBodies.Slot.FACTION,request.slot());
                        assertArrayEquals(input(change.kind()),request.producerInput());
                        assertArrayEquals(GiftPendingCodec.encodeLedger(change.replay().apply(read(same,previous))),raw);
                        return ActionCodec.sha256(raw);
                    });
        }
        private Optional<Ledger> read(Session same,Optional<DomainBodies.BodyRef> previous)throws IOException {
            var value=same.readDomain(DomainBodies.Slot.FACTION);
            if(previous.isEmpty()){assertEquals(DomainBodies.Reason.UNIMPORTED,assertInstanceOf(DomainBodies.Unavailable.class,value).reason());return Optional.empty();}
            var actual=assertInstanceOf(DomainBodies.Available.class,value);assertEquals(previous.orElseThrow(),actual.reference());
            assertEquals(List.of(source),actual.reference().producerSources());return Optional.of(GiftPendingCodec.decodeLedger(actual.canonicalBody()));
        }
        Ledger current(Session same)throws IOException{return read(same,DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION)).orElseThrow();}
        void publish(Session same,Change change)throws IOException {
            var actual=fixture.get();actual.writer.requireSession(same);assertNull(active.get());
            var previous=DomainBodies.reference(same.head().state(),DomainBodies.Slot.FACTION);
            RawJson raw=new RawJson(GiftPendingCodec.encodeLedger(change.replay().apply(read(same,previous))));
            var archive=actual.archive.withSession(same);ExactRef body=archive.preserveMaterial(raw);assertEquals(raw,archive.loadMaterial(body));
            var request=new DomainBodies.ImportRequest(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,body,input(change.kind()),List.of(source),
                    "software-gift-"+change.kind()+"-"+same.head().state().sequence());
            active.set(change);try{same.commitImport(same.previewImport(request));}finally{active.remove();}
        }
        private static byte[] input(String kind){return DriverJson.encode(obj("software_gift_reducer_transition",new Text(kind)));}
    }
    @Test void actualHistoricalPendingAndIndependentWalletReadPublishTwoOriginalRowsAndReplayColdWithoutResubmission()throws Exception {
        var fixtureRef=new AtomicReference<ActionWriterIntegrationFixture>();var definitions=new AtomicReference<FinanceReadContracts>();
        var domain=new AtomicReference<Domain>();var selected=new AtomicReference<ExactRef>();var commandRef=new AtomicReference<ActionCommand>();
        ActionPorts.PostconditionPort observer=(command,attempt,dispatch)->{
            var actual=fixtureRef.get();Session same=actual.journal.borrowedWriterSession();var archive=actual.archive.withSession(same);
            try{return actual.collector.currentOwned(same,actual.observationIdentity(),command.deadline(),lease->{
                var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,actual.frameLoader());var after=lease.frame();
                var readRequest=new PlanningReadRequest(after.identity(),after.source(),after.sessionId(),FinanceReadContracts.Query.FACTION_GIFT_RECEIPT.operation(),new Obj(Map.of()),command.deadline());
                var read=known(actual.reads.read(same,definitions.get().contract(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT),readRequest));
                var pair=new NativeEffectSnapshots.Pair(before,after);
                var projected=NativeFinanceEffects.project(command,attempt,pair,read.receipt(),read.value());
                ExactRef basis=NativeEffectEvidence.preserve(command,attempt,pair,List.of(read.receipt()),projected.compatibleResult().orElseThrow(),archive);
                return NativeEffectSnapshots.withEvidence(projected,List.of(basis)).result();
            });}catch(IOException failure){throw new UncheckedIOException(failure);}
        };
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(OrdinaryFinancePolicies.GIFT,"software.gift-source",observer,
                ()->fixtureRef.get().enqueueSoftwareNativePacket(snapshot(3,85000000)),
                Optional.of(()->new RawJson(DriverJson.encode(submit(commandRef.get())))),
                Optional.of(source->new org.xar.ck3.control.nativebridge.NativePrivateActionPermission(OrdinaryFinancePolicies.GIFT,"software-gift-middle",source,
                        request->assertTrue(request.additionalFields().objectFieldNames().contains("source_faction_id")),(config,hello,guard,request)->source)),true,
                Optional.of(new ActionPorts.PreparationPort(){
                    @Override public NativeRequest prepare(ActionCommand command){throw new AssertionError("actual request-aware preparation required");}
                    @Override public NativeRequest prepare(Session same,ActionCommand command,String id){return NativeFinanceEffects.prepare(command,id);}
                }));
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("e".repeat(64),"software-gift-middle",source->{
            selected.set(source);var contracts=new FinanceReadContracts(query->new FinanceReadContracts.Registration(source,new FinanceReadContracts.Permission(
                    Optional.of("game.command."+query.operation().value()),"game.command."+query.operation().value(),ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP)));
            definitions.set(contracts);return List.of(contracts.contract(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT));
        },request->new RawJson(DriverJson.encode(receipt(commandRef.get()))),Optional.of("1.20.0.4"),Set.of());
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("actual-middle"),false,reads,List.of(action),List.of(),source->{
            var producer=new Domain(source,fixtureRef);domain.set(producer);return List.of(producer.registration());
        })) {
            fixtureRef.set(actual);
            actual.bindAdditionalArchivedVerifier(new NativeRecordedEvidenceVerifier.Binding(OrdinaryFinancePolicies.GIFT,selected.get(),(head,receipt,archive)->{
                var original=NativeEffectEvidence.load(receipt,archive,actual.frameLoader());
                assertEquals(1,original.independentReads().size());var read=original.independentReads().getFirst();
                var replay=NativeFinanceEffects.project(receipt.command(),((ActionState.Settled)receipt.state()).attempt(),original.frames(),read,
                        definitions.get().decodeOriginal(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT,read,original.frames().after().semantic()));
                replay=NativeEffectSnapshots.withEvidence(replay,receipt.applied().orElseThrow().observation().supportingEvidence());
                NativeEffectEvidence.requireSame(((ActionState.Settled)receipt.state()).settlement(),replay,original.compatibleResult());
            }));
            actual.bindAdditionalBeforeIntent((same,command)->{
                try{domain.get().publish(same,new Change("BEGIN",previous->GiftPendingReducer.begin(previous.orElseThrow(),
                        new BeginRequest(RequestIds.forActionBody(ActionCodec.bodySha256(command)),command.before().frame().episodeRunId(),"R"+command.before().frame().revision(),
                                GiftProcessIdentity.actual(command.before().game()),NativeFinanceEffects.giftBaseline(command.arguments()),n(10000000),"a".repeat(64)))));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            var materials=new Materials(actual,definitions.get(),selected.get());
            var publisher=new DriverActionHistoryPublisher(actual.driverAuthority(),actual.journal,actual.archive,materials,List.of(selected.get()));
            actual.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
            actual.writer.locked(same->{domain.get().publish(same,new Change("FRESH",previous->{assertTrue(previous.isEmpty());return Ledger.empty();}));return null;});
            actual.enqueueSoftwareNativePacket(snapshot(2,100000000));var seed=actual.command("gift-real-middle");
            var command=command(actual,seed);commandRef.set(command);var settled=actual.coordinator.execute(command);assertTrue(settled.applied().isPresent());
            var retained=new AtomicReference<ExactRef>();
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);var captured=GiftActionHistoryEvidence.capture(same,settled,archive,actual.frameLoader(),definitions.get());retained.set(captured.originals());
                // Commit the same actual reducer result after independent material verification; old pending is no longer current.
                domain.get().publish(same,new Change("COMPLETE",previous->{
                    var ack=GiftActionHistoryEvidence.decodeSubmission(settled.ack().orElseThrow());
                    var read=NativeEffectEvidence.archivedReads(settled,archive).getFirst();
                    var results=GiftActionHistoryEvidence.project(previous.orElseThrow(),ack,FinanceReadContracts.decodeArchivedGiftReceipt(read).result());
                    return GiftPendingCodec.decodeLedger(DriverJson.encode(object(DriverJson.object(results.receiptResult().bytes(),RawJson.MAXIMUM_BYTES).get("pending_ledger"),"completed original ledger")));
                }));assertTrue(domain.get().current(same).pending().isEmpty());
                RawJson presented=FactionGiftPublicService.presentOriginal(settled,archive,actual.frameLoader(),domain.get().current(same));
                var external=FactionGiftPublicCodec.businessPublic(Method.SEND,presented);
                Obj originalResult=DriverJson.object(presented.bytes(),RawJson.MAXIMUM_BYTES),publicResult=DriverJson.object(external.bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(new Text("applied"),publicResult.get("status"));
                assertInstanceOf(Text.class,object(publicResult.get("source_frame"),"public actual after frame").get("revision"));
                assertEquals(originalResult,DriverJson.object(FactionGiftPublicCodec.businessNative(Method.SEND,external).bytes(),RawJson.MAXIMUM_BYTES));
                assertEquals(captured.submitResult(),GiftActionHistoryEvidence.verifyArchived(same,settled,retained.get(),archive).submitResult());
                int nativeWrites=actual.nativeActionWrites(),nativeReads=actual.nativeReadWrites();
                assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,settled));
                var known=actual.driverAuthority().withFrozenFacts(same,held->assertInstanceOf(DriverSnapshotFacts.Known.class,held.state()));
                assertEquals(2,known.driver().commandHistory().size());assertEquals(1,known.actionRows().size());assertEquals(1,known.actionRows().getFirst().historyIndex());
                DriverStateSnapshot.Complete cold=DriverStateSnapshot.decodeComplete(known.driver().encode());assertArrayEquals(known.driver().encode(),cold.encode());
                for(var row:cold.commandHistory())DriverActionHistoryCodec.verifyLegacy(same,settled,DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES),archive);
                assertEquals(nativeWrites,actual.nativeActionWrites());assertEquals(nativeReads,actual.nativeReadWrites());assertEquals(1,nativeWrites);
                assertInstanceOf(DriverActionHistoryPublisher.Unchanged.class,publisher.completed(same,settled));return null;
            });
            actual.writer.locked(same->{
                int readsBefore=actual.nativeReadWrites();assertNotNull(GiftActionHistoryEvidence.verifyArchived(same,settled,retained.get(),actual.archive.withSession(same)));
                assertTrue(domain.get().current(same).pending().isEmpty());assertEquals(readsBefore,actual.nativeReadWrites());return null;
            });
        }
    }
    private static ActionCommand command(ActionWriterIntegrationFixture actual,ActionCommand seed)throws IOException {
        var id=seed.before().frame().identity();var choice=new FactionGiftChoice.Selected(n(771),n(33011),FactionGiftChoice.MembershipRole.CHARACTER_MEMBER,
                id.nativeRevision(),id.nativeRevision(),id.dateRaw(),id.player(),n(12345),n(15000000),n(37));
        Obj observation=obj("queried_source_faction_id",nvalue(771),"recipient_character_id",nvalue(33011),"snapshot_revision",new IntegerValue(id.nativeRevision()),
                "native_snapshot_revision",new IntegerValue(id.nativeRevision()),"observed_date_raw",new IntegerValue(id.dateRaw()),"player_character_id",new IntegerValue(id.player()),
                "player_gold_raw",nvalue(100000000),"recipient_opinion_of_player",nvalue(-25),"source_faction_power_raw",nvalue(11000000),"source_faction_discontent_raw",nvalue(5000000),
                "source_faction_member_character_ids",new Arr(List.of(nvalue(33011))),"gift_opinion_present",new Bool(false),"source_faction_targeting_player",new Bool(true),
                "gift_preview",obj("gold_cost_raw",nvalue(15000000),"opinion_delta",nvalue(37)));
        ExactRef marker=actual.writer.locked(same->actual.archive.withSession(same).preserveMaterial(new RawJson("{\"software_middle_quote\":\"UNQUALIFIED\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        Obj arguments=obj("choice",object(parse(FactionGiftPolicy.encode(choice)),"actual source choice DATA"),"candidate",obj("observation",observation),
                "minimum_gold_reserve_raw",nvalue(10000000),"checkpoint_sha256",new Text("a".repeat(64)),FinanceEvidenceArchive.ARGUMENT,object(parse(StrictJson.canonical(marker.toJson())),"unqualified marker ref"));
        var request=actual.writer.locked(same->actual.collector.current(same,seed.before(),seed.deadline(),lease->new PlanningRequest(seed.before(),seed.source(),seed.sessionId(),seed.deadline(),
                new PlanningObservation(lease.frame().semantic(),List.of(),Set.of(OrdinaryFinancePolicies.GIFT),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false))));
        return new ActionCommand(seed.actionId(),seed.before(),seed.source(),seed.sessionId(),seed.operation(),arguments,NativeFinanceEffects.expected(seed.operation(),request,arguments).orElseThrow(),seed.claims(),seed.deadline());
    }
    private static Obj submit(ActionCommand command) {
        return obj("step",new Text(OrdinaryFinancePolicies.GIFT.value()),"private_build",new Bool(true),"advertised",new Bool(false),"status",new Text("submitted_verification_pending"),
                "native",obj("ack",obj("schema_version",nvalue(1),"request_id",new Text(RequestIds.forCommand(command)),"status",new Text("submitted_verification_pending"),
                        "verification_pending",new Bool(true),"source_faction_id",nvalue(771),"recipient_character_id",nvalue(33011))));
    }
    private static Obj receipt(ActionCommand command) {
        return obj("step",new Text(FinanceReadContracts.Query.FACTION_GIFT_RECEIPT.operation().value()),"accepted",new Bool(true),"private_build",new Bool(true),"advertised",new Bool(false),"status",new Text("applied"),
                "receipt",obj("schema_version",nvalue(1),"request_id",new Text(RequestIds.forCommand(command)),"status",new Text("mitigated"),"postcondition_verified",new Bool(true),"mitigation_applied",new Bool(true),
                        "post_gift_opinion_present",new Bool(true),"source_faction_id",nvalue(771),"recipient_character_id",nvalue(33011),"player_character_id",new IntegerValue(command.before().frame().identity().player()),
                        "post_snapshot_revision",nvalue(3),"post_native_snapshot_revision",nvalue(3),"post_observed_date_raw",new IntegerValue(command.before().frame().identity().dateRaw()),"post_player_gold_raw",nvalue(85000000),"post_gift_opinion_modifier_value",nvalue(37)));
    }
    private static byte[] snapshot(int revision,long gold) {
        String state="{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":"+ActionWriterIntegrationFixture.INITIAL_DATE_RAW+",\"played_character\":{\"character_id\":73,\"alive\":true},\"played_character_gold\":{\"raw\":"+gold+",\"scale\":100000},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal\":false,\"one_life_terminal_reason\":null,\"episode_identity_pending\":false,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}";
        byte[] raw=("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"fixture-gift-"+revision+"\",\"revision\":"+revision+",\"state\":"+state+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
        return ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
    }
    private static IntegerValue nvalue(long value){return new IntegerValue(n(value));}
    private static PlanningReadResult.Known<FinanceReadContracts.Packet> known(PlanningReadResult<FinanceReadContracts.Packet> result){
        if(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)return known;
        throw new AssertionError(result);
    }
    private static final class Materials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture actual;private final FinanceReadContracts definitions;private final ExactRef source;
        Materials(ActionWriterIntegrationFixture actual,FinanceReadContracts definitions,ExactRef source){this.actual=actual;this.definitions=definitions;this.source=source;}
        @Override public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){assertSame(actual.driverAuthority(),authority);assertSame(actual.journal,journal);assertSame(actual.archive,archive);}
        @Override public List<ExactRef> sources(){return List.of(source);}
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt receipt,ActionPorts.OutcomeArchive archive)throws IOException {
            var value=GiftActionHistoryEvidence.capture(same,receipt,archive,actual.frameLoader(),definitions);
            ExactRef submit=archive.preserveMaterial(value.submitResult()),received=archive.preserveMaterial(value.receiptResult());
            var read=NativeEffectEvidence.archivedReads(receipt,archive).getFirst();
            return new DriverActionHistoryCodec.GiftLegacyPair(value.originals(),submit,received,PublicNumbers.fromResults(value.submitResult(),value.submitPublic()),PublicNumbers.fromResults(value.receiptResult(),value.receiptPublic()),
                    List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,value.originals()),new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,submit),
                            new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,received),new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.READ,archive.readReferenceOf(read))),List.of(source));
        }
        @Override public void requireOriginal(Session same,ActionReceipt receipt,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive archive)throws IOException {
            var pair=assertInstanceOf(DriverActionHistoryCodec.GiftLegacyPair.class,material);
            var original=GiftActionHistoryEvidence.verify(same,receipt,pair.originals(),archive,actual.frameLoader(),definitions);
            assertEquals(DriverJson.object(original.submitResult().bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(archive.loadMaterial(pair.submitResult()).bytes(),RawJson.MAXIMUM_BYTES));
            assertEquals(DriverJson.object(original.receiptResult().bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(archive.loadMaterial(pair.receiptResult()).bytes(),RawJson.MAXIMUM_BYTES));
        }
    }
}
