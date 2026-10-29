package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual read producer/issuer/guard/writer/archive chain; no canonical mutation success or private Root is fabricated. */
final class CoaDesignerReadScopeTest {
    private static final String MACHINE="controlled-coa-read-source";
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String ROUTE="query-frontend-gui-route-v1",RULER="inspect-frontend-gui-tree-v1";
    private static final String TREE="inspect-frontend-coat-of-arms-tree-v1",GRID="inspect-frontend-coat-of-arms-pattern-grid-v1";
    @TempDir Path temporary;
    private static byte[] packet(String value)throws IOException {return NativeWire.packet(value.getBytes(StandardCharsets.UTF_8));}
    private static ObjectNode widget(String path,String name,int children) {
        return FrontendCoaCodec.empty().put("runtime_name",name).put("child_path",path).put("depth",path.isEmpty()?0:path.split("/").length)
                .put("child_count",children).put("vtable_rva",BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).put("effective_visible",true).put("enabled",true);
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();String route="coat_of_arms_designer";int routes,reads,writes;boolean malformed;
        Replay()throws IOException {
            var hello=FrontendCoaCodec.empty().put("type","hello").put("protocol_version",1).put("pid",123)
                    .put("connection_generation",BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)).put("bridge_version","controlled-coa-v1")
                    .put("expected_ck3_version","1.20.0.4").put("expected_ck3_sha256",SHA)
                    .put("game_adapter_id","ck3-1.20.0.4-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
            var caps=hello.putArray("capabilities");for(String step:List.of(ROUTE,RULER,TREE,GRID))caps.add("game.command."+step);
            for(var action:CoaPostconditions.DesignerAction.values())caps.add("game.command."+action.step());
            packets.add(NativeWire.packet(FrontendCoaCodec.raw(hello).bytes()));
        }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public void verify() { }
        @Override public byte[] readPacket(Instant deadline)throws IOException {
            if(packets.isEmpty())throw new IOException("no additional original software packet");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] bytes,Instant deadline)throws IOException {
            var request=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(bytes,4,bytes.length)));
            String step=NativeWire.text(request.get("step")),id=NativeWire.text(request.get("request_id"));
            assertTrue(List.of(ROUTE,RULER,TREE,GRID).contains(step),"this fixture cannot issue any native mutation");
            assertEquals(BigInteger.ZERO,request.get("expected_revision").bigIntegerValue());assertEquals(5,request.size());writes++;
            if(id.startsWith("frontend-route-"))routes++;else reads++;
            var result=FrontendCoaCodec.empty().put("step",step).put("accepted",true).put("backend_id","native-headless");
            if(step.equals(ROUTE))result.put("status",route);
            else {
                result.put("status","available").put("scope_root_name",step.equals(RULER)?"ruler_designer":step.equals(GRID)?"coat_of_arms_pattern_grid":"coat_of_arms_page")
                        .put("root_available",true).put("truncated",false);
                var rows=result.putArray("widgets");
                if(step.equals(GRID)){rows.add(widget("","",2));rows.add(widget("0","",0));rows.add(widget("1","",0));}
                else if(step.equals(RULER))rows.add(widget("0/0/0/0/0/0/0/3/1/0","",2));
                else rows.add(widget("0/3/0/2/1/0/0/1/1/0","button_custom_mode",0));
                result.put("widget_count",rows.size());if(malformed)result.put("widget_count",true);
            }
            packets.add(packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":"+writes+"}"));
            var response=FrontendCoaCodec.empty().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
            response.set("result",result);packets.add(NativeWire.packet(FrontendCoaCodec.raw(response).bytes()));
        }
        @Override public void close() { }
    }
    private static ObjectNode state() {
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE).put("sequence",0)
                .put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25)
                .put("start_date_raw",1000).put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1)
                .put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0);
        row.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);return row;
    }
    private static final class Fixture implements AutoCloseable {
        final Clock clock=Clock.systemUTC();final Replay replay;final ContinuityWriter writer;final NativeOutcomeArchive archive;
        final NativeGameTransport transport;final G2Source source;final CoaDesigner designer;final RootReadContractCatalog catalog;
        final RootExecutableBindings installed;final FrontendObservationSequence sequence;final NativeFrontendAuthority authority;
        final PlanningReadCoordinator coordinator;final StorageWriteGuardTestSupport storage;int snapshotLookups;
        Fixture(Path root)throws IOException {
            Files.createDirectory(root);byte[] initial=ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"),initial,StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"),initial,StandardOpenOption.CREATE_NEW);Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0],StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));
            Path sourcePath=root.resolve("controlled-designer-source.java");Files.writeString(sourcePath,"actual controlled CoA fixture source",StandardOpenOption.CREATE_NEW);
            ExactRef ref=LedgerFilesFixtureAccess.read(sourcePath,100).pin().reference();
            var layout=new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),LedgerFilesFixtureAccess.read(root.resolve("anchor.json"),65536).pin().reference(),MACHINE);
            storage=StorageWriteGuardTestSupport.create(layout);
            var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),8<<20),storage);
            writer=new ContinuityWriter(layout,List.of(ref),new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor,Request request){throw new IllegalStateException("no canonical business reducer in this read fixture");}
                @Override public ContinuityState reduce(ContinuityState predecessor,Request request){throw new IllegalStateException("no canonical business reducer in this read fixture");}
            },clock,new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
            archive=new NativeOutcomeArchive(artifacts,writer);replay=new Replay();
            var generation=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
            transport=new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\controlled-coa-read",MACHINE,generation,"coa-read-session","controlled-coa-v1",SHA,"ck3-1.20.0.4-msvc-x64"),16,64);
            source=new G2Source(MACHINE,clock.instant().toString(),"1.20.0.4",ref);
            var shared=new FrontendRulesDefinitions(FrontendRulesData.Build.CK3_12004,ref);var own=CoaDesigner.readDefinitions(ref);
            var definitions=new CoaDesigner.Definitions(shared.route(),shared.tree(),own);
            PlanningReadPort actualReads=new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
                    try{return coordinator.read(writer.borrowedSession(),contract,request);}catch(IOException failure){throw new UncheckedIOException(failure);}
                }
            };
            designer=new CoaDesigner(definitions,actualReads,archive,(value,ack)->FrontendCoaCodec.encode(FrontendCoaCodec.designer(value,ack)));
            catalog=RootReadContractCatalog.staticOnly(List.of(shared.route(),shared.tree(),own.tree(),own.grid()));
            var actions=designer.bindings(ref).stream().map(effect->new RootExecutableBindings.ActionBinding(effect,ReadContract.GuardMode.FRONTEND_SESSION,
                    Optional.of("game.command."+effect.operation().value()),ref)).toList();
            installed=RootExecutableBindings.freeze(actions,catalog,List.of(),designer.archivedVerifiers(ref),List.of(),8);installed.requireCompleteArchiveCoverage();
            var admissions=new ArrayList<FrontendRouteAdmission>();
            for(ReadContract<?> contract:List.of(shared.route(),shared.tree(),own.tree(),own.grid()))admissions.add(new FrontendRouteAdmission(contract.operation(),
                    Set.of(FrontendRulesData.Route.RULER_DESIGNER,FrontendRulesData.Route.COAT_OF_ARMS_DESIGNER),FrontendRouteAdmission.FrameMode.MENU,ref));
            for(var action:CoaPostconditions.DesignerAction.values())admissions.add(new FrontendRouteAdmission(new OperationKey(action.step()),Set.of(action.beforeRoute()),FrontendRouteAdmission.FrameMode.MENU,ref));
            sequence=new FrontendObservationSequence(transport,archive,source,installed,admissions,()->{snapshotLookups++;return Optional.empty();},
                    (same,held,exactSource,route,received,deadline)->{
                        writer.requireSession(same);var pin=same.capturePin(ref,100);same.verifyPin(pin);assertEquals(source,exactSource);assertEquals(held,received.session().orElseThrow());
                        assertTrue(((NativeWire.CommandResult)NativeWire.decode(archive.readArtifact(same,route,65536))).nativeOk());
                        var proof=StrictJson.object().put("schema","controlled.coa-read-source/v1").put("machine_id",MACHINE);proof.set("source",ref.toJson());proof.set("route",route.toJson());
                        var original=archive.preserveArtifact(same,ContinuityJson.canonical(proof),65536);
                        return new SourceQualification(original,retained->{writer.requireSession(retained);if(retained!=same)throw new IOException("foreign read writer");retained.verifyPin(pin);});
                    },clock,Duration.ofSeconds(5),Duration.ofSeconds(10),64);
            authority=new NativeFrontendAuthority(sequence);
            var guard=new RootFrontendReadGuard(authority,this::borrowed,archive,source,clock,"controlled-coa-read-root",new ArchiveOriginalEvidencePort(archive),catalog);
            coordinator=new PlanningReadCoordinator(catalog,new ContinuityActionJournal(writer,archive),guard,transport,archive,clock);
        }
        ContinuityStorePort.Session borrowed(){try{return writer.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}}
        Instant deadline(){return clock.instant().plusSeconds(30);}
        <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,FrontendAuthority.LeaseSnapshot lease,ReadContract<T> contract) {
            return coordinator.read(same,contract,new PlanningReadRequest(new CommandOrigin.Frontend(lease.identity()),source,"coa-read-session",contract.operation(),new OpportunityJson.Obj(Map.of()),deadline()));
        }
        @Override public void close()throws IOException {try(storage){transport.close();}}
    }
    private static <T> PlanningReadResult.Known<T> known(PlanningReadResult<T> result) {
        assertInstanceOf(PlanningReadResult.Known.class,result);if(result instanceof PlanningReadResult.Known<T> known)return known;throw new AssertionError(result);
    }
    @Test void bothActualDesignerReadsUseTheirSoleContractsTwoRootGuardsAndOneActualMenuLease()throws IOException {
        try(var f=new Fixture(temporary.resolve("reads"))) {
            f.writer.locked(same->f.authority.withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,f.deadline(),lease->{
                for(var contract:List.of(f.designer.definitions().tree(),f.designer.definitions().grid())) {
                    var value=known(f.read(same,lease,contract));assertEquals(value.receipt().before(),value.receipt().after());
                    assertEquals(lease.identity(),value.receipt().after().binding().origin().requireFrontend());
                    var original=f.archive.withSession(same);assertEquals(value.receipt(),original.loadRead(value.originalReceipt()));
                    NativeRecordedEvidenceVerifier.requireRead(value.receipt(),original);
                    assertEquals(value.receipt().before(),CommandOriginCodec.planningGuard(CommandOriginCodec.planningGuard(value.receipt().before())));
                    var publicValue=FrontendCoaCodec.tree(value.value());assertEquals("18446744073709551615",publicValue.get("widgets").get(0).get("vtable_rva").textValue());
                    if(contract==f.designer.definitions().grid())assertTrue(publicValue.get("direct_children_complete").booleanValue());
                    assertFalse(publicValue.has("available"));
                }
                assertEquals(0,same.head().state().sequence());assertEquals(0,f.snapshotLookups);return null;
            }));
            assertEquals(1,f.replay.routes);assertEquals(2,f.replay.reads);assertEquals(3,f.replay.writes);
        }
    }
    @Test void malformedActualNativeTreeRemainsUnavailableWithItsOriginalPacket()throws IOException {
        try(var f=new Fixture(temporary.resolve("bad-tree"))) {
            f.replay.malformed=true;f.writer.locked(same->f.authority.withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,f.deadline(),lease->{
                var result=f.read(same,lease,f.designer.definitions().tree());assertInstanceOf(PlanningReadResult.Unavailable.class,result);
                var unavailable=(PlanningReadResult.Unavailable<CoaData.Tree>)result;assertTrue(unavailable.original().isPresent());
                assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());assertEquals(0,same.head().state().sequence());return null;
            }));assertEquals(1,f.replay.routes);assertEquals(1,f.replay.reads);
        }
    }
    @Test void actualPrereadsProduceTheFullCommandAndUnknownObserverMakesNoAdditionalReadOrEffect()throws IOException {
        try(var f=new Fixture(temporary.resolve("unknown"))) {
            f.replay.route="ruler_designer";f.writer.locked(same->{
                ActionCommand command=f.authority.withSourceBoundFrontendRead(same,FrontendRouteAdmission.FrameMode.MENU,f.deadline(),lease->{
                    var route=known(f.read(same,lease,f.designer.definitions().route()));var tree=known(f.read(same,lease,f.designer.definitions().rulerTree()));
                    return f.designer.command("controlled-open-coa",CoaPostconditions.DesignerAction.OPEN,route,tree,f.deadline());
                });
                assertEquals(command,ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));var request=f.designer.prepare(command);
                assertEquals("activate-frontend-coat-of-arms-designer-v1",request.step());assertEquals(new RawJson(new byte[]{'{','}'}),request.additionalFields());
                var rootGuard=new RootFrontendActionGuard(f.authority,f::borrowed,f.archive,f.source,f.clock,"controlled-coa-action-root",new ArchiveOriginalEvidencePort(f.archive),f.installed);
                var guard=rootGuard.verify(same.head(),command);var attempt=new ActionState.Attempt("controlled-unsubmitted-request",f.clock.instant(),guard,request);
                int before=f.replay.writes;
                // This is an unresolved observer DATA branch, not a canonical mutation/permit or simulated successful native dispatch.
                var pending=f.designer.observe(command,attempt,new NativeActionPort.Unknown(attempt.requestId(),"controlled unresolved submission",new byte[0],Optional.empty()));
                assertInstanceOf(ActionPorts.Pending.class,pending.result());assertTrue(pending.compatibleResult().isEmpty());assertEquals(before,f.replay.writes);
                assertEquals(0,same.head().state().sequence());assertEquals(0,f.snapshotLookups);return null;
            });
        }
    }
}
