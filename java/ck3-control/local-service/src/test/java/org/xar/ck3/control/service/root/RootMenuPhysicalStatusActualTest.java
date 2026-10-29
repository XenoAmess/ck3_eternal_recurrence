package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.PublicMcpHost;
import static org.junit.jupiter.api.Assertions.*;

/** Runs through the real pre-Driver menu read coordinator and its installed physical issuer.
 * Exact actual startup inputs are mandatory; no fake Root, physical lease or successful guard is constructed. */
public final class RootMenuPhysicalStatusActualTest {
    public record Inputs(RootStartupInputsProducer.MenuActual scope) {
        public Inputs {Objects.requireNonNull(scope);}
        public RootRuntimeContext context()throws IOException {return scope.context();}
        public ReadContract<?> status()throws IOException {return scope.status();}
        public Instant deadline()throws IOException {return scope.deadline();}
    }
    private enum Phase { NOT_STARTED, RUNNING, COMPLETE, FAILED }
    private static Phase phase=Phase.NOT_STARTED;
    private static Throwable failure;
    private static boolean physicalCheck,foreignCheck;
    /** Both original checks consume one real menu scope. Any terminal failure is retained, never retried. */
    private static synchronized void actualChecksOnce()throws Exception {
        if(phase==Phase.FAILED){
            if(failure instanceof Exception actual)throw actual;
            if(failure instanceof Error actual)throw actual;
            throw new IllegalStateException("original actual menu failed",failure);
        }
        if(phase==Phase.COMPLETE){assertTrue(physicalCheck&&foreignCheck);return;}
        if(phase!=Phase.NOT_STARTED)throw new IllegalStateException("original actual menu is already running; no second Main/Game");
        phase=Phase.RUNNING;
        try {
            var request=RootStartupInputsProducer.fromEnvironment(System.getenv());
            RootStartupInputsProducer.MenuActual[] originalScope={null};
            RootStartupInputsProducer.executeMenu(request,new OrdinarySessionHost(),new PublicMcpHost(),actual->{
                try {
                    originalScope[0]=actual;
                    var capture=actual.capturedReview();capture.verifyCurrent();
                    assertEquals(ControlBuild.CaptureQualification.TEST_COMPILED_CAPTURE_ONLY,capture.qualification());
                    assertEquals(ControlBuild.CaptureTestState.NOT_RUN,capture.tests());
                    AtomicBoolean nativeReached=new AtomicBoolean();
                    var ordinary=JavaRuntimePackage.review(capture.request(),(requestInput,host)->{
                        nativeReached.set(true);throw new IOException("ordinary reader must reject capture before Native verification");
                    });
                    assertInstanceOf(JavaRuntimePackage.Unavailable.class,ordinary);
                    assertFalse(nativeReached.get(),"capture cannot enter ordinary full-verify package review");
                    var input=new Inputs(actual);requireActual(input);
                    verifyPendingUiBeforeDriver(input);
                    verifyPhysicalStatus(input);physicalCheck=true;
                    verifyForeignContract(input);foreignCheck=true;
                }catch(AssertionError assertion){
                    throw new IOException("actual pre-Driver Menu assertions failed inside the original Main",assertion);
                }
            });
            assertTrue(physicalCheck&&foreignCheck,"both checks must execute before original Main/cleanup succeeds");
            assertNotNull(originalScope[0]);assertThrows(IOException.class,originalScope[0]::context);
            phase=Phase.COMPLETE;
        }catch(Exception|Error actual){failure=actual;phase=Phase.FAILED;throw actual;}
    }
    /** Distinct exact Request for an independent validation attempt; the original menu startup is never replayed. */
    private static RootStartupInputsProducer.Request physicalEntryRequest()throws IOException {
        String prefix="XAR_ROOT_PHYSICAL_ENTRY_INPUTS_REQUEST";
        var environment=new java.util.HashMap<String,String>();
        for(String suffix:java.util.List.of("","_BYTES","_SHA256")) {
            String value=System.getenv(prefix+suffix);
            if(value==null)throw new IOException("MISSING_NOT_RUN: independent exact physical entry Request "+prefix+suffix+" required");
            environment.put(RootStartupInputsProducer.REQUEST_ENV+suffix,value);
        }
        var request=RootStartupInputsProducer.fromEnvironment(environment);
        var originalMenu=RootStartupInputsProducer.fromEnvironment(System.getenv());
        if(request.startup().path().equals(originalMenu.startup().path()))
            throw new IOException("independent physical entry cannot replay the original menu startup");
        var next=RootStartupConfiguration.readExact(request.startup());
        var previous=RootStartupConfiguration.readExact(originalMenu.startup());
        var nextApplication=RootApplicationConfiguration.readExact(next.application());
        var previousApplication=RootApplicationConfiguration.readExact(previous.application());
        if(next.receiptDirectory().equals(previous.receiptDirectory())
                ||nextApplication.ledger().snapshot().equals(previousApplication.ledger().snapshot())
                ||nextApplication.artifactRoot().startsWith(previousApplication.artifactRoot())
                ||previousApplication.artifactRoot().startsWith(nextApplication.artifactRoot()))
            throw new IOException("physical entry requires its independent receipt, canonical ledger and artifact roots");
        return request;
    }
    /** One real START attempt; UNKNOWN is observed without replay, an admitted Driver never becomes ordinary Root. */
    @Test void fresh1066AttemptReadsTheActualUnknownOrPhysicalDriverWithoutOrdinaryAuthority()throws Exception {
        var request=physicalEntryRequest();var ordinaryHost=new OrdinarySessionHost();var publicHost=new PublicMcpHost();
        var menuScope=new RootStartupInputsProducer.MenuActual[1];
        var driverScope=new RootStartupInputsProducer.PhysicalActual[1];
        boolean[] unknown={false},driver={false};
        RootStartupInputsProducer.executePhysicalValidation(request,ordinaryHost,publicHost,new RootStartupInputsProducer.PhysicalWork() {
            @Override public void menu(RootStartupInputsProducer.MenuActual actual)throws Exception {
                menuScope[0]=actual;RootPhysicalStatusReadAuthorityActualTest.assertCaptureBoundary(actual);
                var input=new Inputs(actual);requireActual(input);
                verifyPendingUiBeforeDriver(input);verifyPhysicalStatus(input);verifyForeignContract(input);
            }
            @Override public void entry(RootStartupInputsProducer.MenuActual actual,GameplayEntryService.Result result)throws Exception {
                RootPhysicalStatusReadAuthorityActualTest.assertCaptureBoundary(actual);
                if(result instanceof GameplayEntryService.Awaiting waiting&&waiting.actual().state() instanceof ActionState.Unknown) {
                    var context=actual.context();
                    var input=new RootPhysicalStatusReadAuthorityActualTest.Input(RootPhysicalStatusReadAuthorityActualTest.Scenario.UNKNOWN,
                            context,context.physicalStatusReads(),actual.status(),actual.deadline(),
                            java.util.Optional.of(waiting.actual().command().actionId()));
                    RootPhysicalStatusReadAuthorityActualTest.exercise(input);
                    RootTransportPublicEntryActualTest.exercise(new RootTransportPublicEntryActualTest.PublicInput(input,
                            actual.publicContext(),actual.publicHost(),actual.directory()));unknown[0]=true;
                } else {
                    // The original Main retains the real non-admission and returns its failure; no expected state is manufactured.
                    verifyPhysicalStatus(new Inputs(actual));
                }
            }
            @Override public void driver(RootStartupInputsProducer.PhysicalActual actual)throws Exception {
                driverScope[0]=actual;RootPhysicalStatusReadAuthorityActualTest.assertCaptureBoundary(actual);
                var context=actual.context();
                context.core().withBorrowed(()->{
                    var same=context.core().activeBorrowedSession();var head=same.head();
                    context.physicalStatusReads().withObserved(same,actual.deadline(),lease->{
                        var read=PlanningReadRequest.newStatusOnly(lease.identity(),actual.status().operation(),
                                new OpportunityJson.Obj(Map.of()),actual.deadline());
                        var result=context.reads().read(same,actual.status(),read);
                        if(!(result instanceof PlanningReadResult.Known<org.xar.ck3.control.reconciliation.LateOutcome.Status> known))
                            throw new IOException("MISSING_NOT_RUN: original admitted Driver physical Status did not produce a Known receipt");
                        org.xar.ck3.control.nativebridge.PhysicalStatusReadBoundaryTest.assertActualPhysicalReceipt(same,actual.status(),known,context.archive().withSession(same));
                        try {RootUnknownSentinelReadProfileTest.assertActualRead(actual.status(),known,context.archive().withSession(same));}
                        catch(Exception failure){if(failure instanceof IOException io)throw io;throw new IOException("captured Status consumer failed",failure);}
                        assertEquals(context.game().generation(),lease.identity().game());
                        assertEquals(context.source(),lease.identity().source());return null;
                    });
                    assertEquals(head.digest(),same.head().digest());assertEquals(head.documents(),same.head().documents());
                    assertEquals(head.absent(),same.head().absent());assertEquals(head.indexRepairs(),same.head().indexRepairs());
                    assertEquals(head.snapshotNeedsRecovery(),same.head().snapshotNeedsRecovery());return null;
                });
                actual.publicContext().withInstalledData(actual.deadline(),(installed,same)->{
                    assertSame(context,installed.context());
                    assertSame(actual.status(),installed.remainingDomains().life().infrastructure().physicalStatuses());return null;
                });
                String tool="ck3_read_tactical_daily_sentinel_status_private_v1";
                var descriptor=actual.directory().tools().stream().filter(value->value.name().equals(tool)).findFirst().orElseThrow();
                var call=new org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolCall(tool,
                        new org.xar.ck3.control.service.mcp.PublicMcpDirectory.Arguments(org.xar.ck3.control.service.mcp.PublicMcpDirectory.Presence.VALUE,
                                java.util.Optional.of(new RawJson(new byte[]{'{','}'}))),java.util.Optional.empty(),
                        new org.xar.ck3.control.service.mcp.McpCancellation());
                descriptor.validateArguments(call.arguments());var response=actual.directory().invoke(call);descriptor.validateResult(response);
                var encoded=org.xar.ck3.control.application.driver.DriverJson.object(response.bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(new OpportunityJson.Bool(false),encoded.get("isError"));
                var business=OpportunityJson.object(encoded.get("structuredContent"),"actual captured physical Status result");
                assertEquals(new OpportunityJson.Text("native-headless"),business.get("backend_id"));
                assertTrue(business.get("tactical_daily_sentinel") instanceof OpportunityJson.Obj);
                assertSame(actual.directory(),actual.publicHost().current().orElseThrow());driver[0]=true;
            }
        });
        assertTrue(unknown[0]||driver[0],"one genuine original UNKNOWN or admitted physical Driver callback is required");
        assertFalse(unknown[0]&&driver[0],"original UNKNOWN cannot be replayed into an admitted Driver");
        assertTrue(ordinaryHost.current().isEmpty());assertNotNull(menuScope[0]);
        assertThrows(IOException.class,menuScope[0]::context);
        if(driverScope[0]!=null)assertThrows(IOException.class,driverScope[0]::context);
        var start=RootStartupConfiguration.readExact(request.startup());
        var cleanup=org.xar.ck3.control.contracts.StrictJson.parse(java.nio.file.Files.readAllBytes(
                start.receiptDirectory().resolve("game-cleanup.json")),1<<20);
        assertEquals("ORIGINAL_GAME_CLEANUP_CONSUMED",cleanup.get("status").textValue());
        assertTrue(cleanup.get("cleanup_proven").booleanValue());assertTrue(cleanup.get("full_job_terminal_passed").booleanValue());
    }
    private static void requireActual(Inputs input)throws Exception {
        assertTrue(input.context().optionalDriverProducer().isEmpty(),"fixture must be genuinely before Driver admission");
        PhysicalStatusIdentity.requireProfile(input.status());
        assertTrue(input.context().readCatalog().containsIdentity(input.status()));
    }
    /** Real installed PendingUI must exist before Driver, while actual business facts remain unavailable. */
    private static void verifyPendingUiBeforeDriver(Inputs input)throws Exception {
        var context=input.context();var natural=context.remainingDomains().lifecycle().natural();
        var pending=natural.pendingRuntime();pending.requireContext(context);assertSame(natural,pending.natural());
        assertTrue(context.optionalDriverProducer().isEmpty());
        context.withSession(same->{
            String head=same.head().digest();
            var missing=assertThrows(IllegalArgumentException.class,pending::hasPending);
            assertEquals("actual current Driver has not been bound",missing.getMessage(),
                    "an unrelated early error cannot stand in for the actual adoption guard");
            assertEquals(head,same.head().digest(),"rejected pre-Driver business lookup must not mutate the writer");
            assertTrue(context.optionalDriverProducer().isEmpty());return null;
        });
    }
    private static <T> PlanningReadResult<T> read(Inputs input,ReadContract<T> status)throws Exception {
        var context=input.context();
        return context.core().withBorrowed(()->{
            var same=context.core().activeBorrowedSession();context.writer().requireSession(same);
            return context.physicalStatusReads().withObserved(same,input.deadline(),lease->{
                PlanningReadRequest request=PlanningReadRequest.newStatusOnly(lease.identity(),status.operation(),
                        new OpportunityJson.Obj(Map.of()),input.deadline());
                return context.reads().read(same,status,request);
            });
        });
    }
    @Test void preGameMenuUsesActualStatusIssuerWithoutDriverOrOrdinaryReady()throws Exception {
        actualChecksOnce();assertTrue(physicalCheck);
    }
    private static void verifyPhysicalStatus(Inputs input)throws Exception {
        var result=read(input,input.status());
        assertTrue(input.context().optionalDriverProducer().isEmpty());
        if(result instanceof PlanningReadResult.Known<?> known) {
            assertEquals(PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3,known.receipt().archiveVersion());
            assertInstanceOf(CommandOrigin.PhysicalStatusOnly.class,known.receipt().request().origin());
            assertEquals(ReadContract.GuardMode.STATUS_ONLY,known.receipt().before().guardMode());
            assertEquals(ReadContract.GuardMode.STATUS_ONLY,known.receipt().after().guardMode());
        } else {
            if(result instanceof PlanningReadResult.Unavailable<?> unavailable)
                fail("actual preGame physical query did not complete: "+unavailable.reason());
            else fail("actual preGame physical read returned an unknown state");
        }
    }
    @Test void menuPhysicalMuxCannotAuthorizeAnotherInstalledContract()throws Exception {
        actualChecksOnce();assertTrue(foreignCheck);
    }
    private static void verifyForeignContract(Inputs input)throws Exception {
        var context=input.context();
        context.core().withBorrowed(()->{
            var same=context.core().activeBorrowedSession();
            return context.physicalStatusReads().withObserved(same,input.deadline(),lease->{
                PlanningReadRequest request=PlanningReadRequest.newStatusOnly(lease.identity(),input.status().operation(),
                        new OpportunityJson.Obj(Map.of()),input.deadline());
                var foreign=context.readCatalog().installed().stream().map(binding->binding.contract())
                        .filter(contract->{try{return contract!=input.status();}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}}).findFirst().orElseThrow(
                                ()->new IllegalStateException("MISSING_ACTUAL_FOREIGN_INSTALLED_READ_INPUT_NOT_RUN"));
                var actualMux=new RootMenuPhysicalStatusReads(context.bindings(),context.source(),()->same);
                assertThrows(IllegalArgumentException.class,()->actualMux.verify(same.head(),request,foreign));
                return null;
            });
        });
    }
}
