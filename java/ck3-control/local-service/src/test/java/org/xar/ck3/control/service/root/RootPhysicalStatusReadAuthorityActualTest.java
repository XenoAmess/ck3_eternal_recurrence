package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.readiness.PhysicalStatusReadAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.reconciliation.LateOutcome;
import org.xar.ck3.control.nativebridge.PhysicalStatusReadBoundaryTest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;
import org.xar.ck3.control.service.mcp.McpCancellation;

/** Actual installed inputs only. Absence of a Managed/source producer is a hard missing result, never a synthetic positive or skip. */
public final class RootPhysicalStatusReadAuthorityActualTest {
    public enum Scenario { RUNNING_NO_PENDING, UNKNOWN, TERMINAL, MISSING_PLAYER, CHANGED_PLAYER, PRE_GAME_NO_DRIVER, ADVANCE_DURING_QUERY }
    public record Input(Scenario scenario,RootRuntimeContext context,RootPhysicalStatusReadAuthority authority,
            ReadContract<LateOutcome.Status> profile,Instant deadline,java.util.Optional<String> unresolvedActionId) {
        public Input { Objects.requireNonNull(scenario);Objects.requireNonNull(context);Objects.requireNonNull(authority);
            Objects.requireNonNull(profile);Objects.requireNonNull(deadline);unresolvedActionId=Objects.requireNonNull(unresolvedActionId); }
    }
    /** Implemented only by an actual managed acceptance environment; no live inputs escape its callback. */
    @FunctionalInterface public interface InputWork { void consume(Input input)throws Exception; }
    public interface InputsProducer { void withActualInstalledInputs(InputWork consumer)throws Exception; }
    private enum Phase { NOT_STARTED,RUNNING,COMPLETE,FAILED }
    private static Phase phase=Phase.NOT_STARTED;
    private static Throwable originalFailure;
    /** Both original consumers execute before the same Main cleans up. Only terminal facts are retained. */
    static synchronized void actualChecksOnce()throws Exception {
        if(phase==Phase.FAILED)rethrowOriginal();
        if(phase==Phase.COMPLETE)return;
        if(phase==Phase.RUNNING)throw new IOException("actual physical Status checks cannot enter a second Main");
        phase=Phase.RUNNING;
        try {
            var producers=ServiceLoader.load(InputsProducer.class).stream().map(ServiceLoader.Provider::get).toList();
            if(producers.size()!=1)throw new IOException("MISSING_NOT_RUN: exactly one actual Managed physical Status InputsProducer is required");
            if(!(producers.getFirst() instanceof RootTransportPublicEntryActualTest.PublicInputsProducer actual))
                throw new IOException("MISSING_NOT_RUN: same genuine physical Status InputsProducer must supply actual public Context and complete Root directory");
            var seen=EnumSet.noneOf(Scenario.class);
            actual.withActualPublicInputs((input,supplied)->{
                assertTrue(seen.add(input.scenario()),"actual physical Status scenario must occur exactly once");
                assertSame(input,supplied.original());exercise(input);RootTransportPublicEntryActualTest.exercise(supplied);
            });
            if(!seen.equals(EnumSet.allOf(Scenario.class)))throw new IOException("MISSING_NOT_RUN: actual physical Status scenario coverage incomplete: "+seen);
            assertEquals(EnumSet.allOf(Scenario.class),seen,"MISSING_NOT_RUN: complete actual public Status phase coverage is mandatory");
            phase=Phase.COMPLETE;
        } catch(Throwable actual) {originalFailure=actual;phase=Phase.FAILED;rethrowOriginal();}
    }
    private static void rethrowOriginal()throws Exception {
        if(originalFailure instanceof Exception actual)throw actual;
        if(originalFailure instanceof Error actual)throw actual;
        throw new AssertionError("actual physical Status failed without its original failure",originalFailure);
    }
    @Test void actualPhysicalStatusScopesCoverTheOriginalRunningUnknownTerminalAndPreDriverRoutes()throws Exception {
        actualChecksOnce();
    }
    /** Genuine capture callbacks may use these checks; neither overload constructs a scope or grants an ordinary runtime. */
    public static void assertCaptureBoundary(RootStartupInputsProducer.MenuActual actual)throws Exception {
        actual.requireScope();var context=actual.context();
        assertTrue(context.optionalDriverProducer().isEmpty());
        assertThrows(IllegalArgumentException.class,context::collector);assertThrows(IllegalArgumentException.class,context::actions);
        assertSame(actual.directory(),actual.publicHost().current().orElseThrow());
        assertTrue(context.readCatalog().containsIdentity(actual.status()));
        assertPublicUnavailable(context,actual.publicHost(),actual.directory());
    }
    public static void assertCaptureBoundary(RootStartupInputsProducer.PhysicalActual actual)throws Exception {
        actual.requireScope();var context=actual.context();
        assertSame(actual.admitted().driver(),context.adopted());
        assertSame(context.adopted().producer(),context.optionalDriverProducer().orElseThrow());
        context.adopted().producer().requireSameTransport(context.transport(),context.source());
        assertThrows(IllegalArgumentException.class,context::collector);assertThrows(IllegalArgumentException.class,context::actions);
        assertSame(actual.directory(),actual.publicHost().current().orElseThrow());
        assertTrue(context.readCatalog().containsIdentity(actual.status()));
        assertPublicUnavailable(context,actual.publicHost(),actual.directory());
    }
    private static void assertPublicUnavailable(RootRuntimeContext context,PublicMcpHost host,PublicMcpDirectory directory)throws Exception {
        var before=context.withSession(same->same.head());
        for(String name:List.of("ck3_plan_turn","ck3_auto_turn","ck3_execute_step")) {
            assertSame(directory,host.current().orElseThrow());
            String arguments=name.equals("ck3_execute_step")
                    ? "{\"step\":\""+RootPublicPauseRuntime.PUBLIC_STEP.value()+"\"}" : "{}";
            var call=new PublicMcpDirectory.ToolCall(name,new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
                    java.util.Optional.of(new RawJson(arguments.getBytes(java.nio.charset.StandardCharsets.UTF_8)))),
                    java.util.Optional.empty(),new McpCancellation());
            var descriptor=directory.tools().stream().filter(value->value.name().equals(name)).findFirst().orElseThrow();
            descriptor.validateArguments(call.arguments());
            var unavailable=assertThrows(java.io.UncheckedIOException.class,()->directory.invoke(call),
                    "capture must reach the original public handler and refuse its unavailable ordinary Root");
            assertEquals("actual current Root session is not admitted or is awaiting restored publication",unavailable.getCause().getMessage());
            assertSame(directory,host.current().orElseThrow());
            context.withSession(same->{assertHead(before,same.head());return null;});
        }
    }
    public static void exercise(Input input)throws IOException {
        var context=input.context();input.authority().requireContext(context);
        RootUnknownSentinelReadProfile.requirePhysicalProfile(input.profile());
        assertTrue(context.readCatalog().containsIdentity(input.profile()),"actual same installed profile is mandatory");
        context.withSession(same->{
            var originalHead=same.head();
            final PhysicalStatusIdentity[] escaped=new PhysicalStatusIdentity[1];
            input.authority().withObserved(same,input.deadline(),lease->{
                escaped[0]=lease.identity();
                assertSame(input.authority(),context.bindings().requirePhysicalStatusAuthority(lease.identity()));
                assertSourceScenario(input,same,lease);
                var foreign=new PhysicalStatusIdentity(lease.identity().transport(),lease.identity().snapshotId()+"-foreign",
                        lease.identity().nativeRevision(),lease.identity().source(),lease.identity().nativeEvidence(),lease.identity().helloEvidence(),
                        lease.identity().heartbeatEvidence(),lease.identity().sourceQualification(),lease.identity().epochManifest(),lease.identity().observedAt());
                assertThrows(IOException.class,()->input.authority().current(same,foreign,input.deadline(),value->null));
                assertThrows(IOException.class,()->input.authority().requireOutside(same),"actual mutation boundary is closed before INTENT");
                assertSame(lease,input.authority().current(same,lease.identity(),input.deadline(),value->value));
                var request=PlanningReadRequest.newStatusOnly(lease.identity(),input.profile().operation(),new OpportunityJson.Obj(java.util.Map.of()),input.deadline());
                var result=context.reads().read(same,input.profile(),request);
                assertInstanceOf(PlanningReadResult.Known.class,result,"the actual native query must produce a real typed read receipt");
                if(!(result instanceof PlanningReadResult.Known<LateOutcome.Status> known))throw new IOException("MISSING_NOT_RUN: actual physical Status known result absent");
                assertActualConsumers(same,input.profile(),known,context);
                rejectMissingOriginalExecutableClosure(input,same,known.receipt().before().binding());
                rejectLegacyHashOnlySourceProof(input,same,known.receipt().before().binding());
                if(input.scenario()==Scenario.ADVANCE_DURING_QUERY)
                    assertTrue(context.transport().currentSnapshot(input.deadline()).nativeRevision().compareTo(lease.identity().nativeRevision())>0,
                            "MISSING_NOT_RUN: actual query must receive a naturally later native state while retaining its original issued identity");
                assertHead(originalHead,same.head());
                return null;
            });
            assertNotNull(escaped[0]);
            assertThrows(IOException.class,()->input.authority().current(same,escaped[0],input.deadline(),value->null),"escaped DATA cannot reopen a private scope");
            input.authority().requireOutside(same);assertHead(originalHead,same.head());return null;
        });
    }
    private static void assertSourceScenario(Input input,ContinuityStorePort.Session same,PhysicalStatusReadAuthority.Lease lease)throws IOException {
        var actual=input.context();
        assertEquals(actual.game().generation(),lease.identity().game());assertEquals(actual.source(),lease.identity().source());
        assertEquals(actual.game().sessionId(),lease.identity().sessionId());
        if(input.scenario()==Scenario.PRE_GAME_NO_DRIVER)
            assertTrue(actual.optionalDriverProducer().isEmpty(),"pre-Game coverage cannot borrow an adopted Driver or create one for Status");
        if(input.scenario()==Scenario.RUNNING_NO_PENDING||input.scenario()==Scenario.ADVANCE_DURING_QUERY) {
            var state=org.xar.ck3.control.application.driver.DriverJson.object(lease.frame().state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            assertFalse(OpportunityJson.bool(state.get("paused"),"actual paused"));
            assertTrue(input.unresolvedActionId().isEmpty(),"running no-pending scenario cannot relabel a reconciliation read");
            assertTrue(ContinuityActionJournal.receipts(same.head().state(),actual.archive().withSession(same)).stream().allMatch(ActionReceipt::settled),
                    "actual running no-pending canonical history still contains an unresolved primitive");
        }
        if(input.scenario()==Scenario.UNKNOWN) {
            String action=input.unresolvedActionId().orElseThrow(()->new IOException("MISSING_NOT_RUN: actual canonical UNKNOWN action required"));
            var receipt=ContinuityActionJournal.lookup(same.head().state(),action,actual.archive().withSession(same))
                    .orElseThrow(()->new IOException("actual canonical UNKNOWN row absent"));
            assertInstanceOf(ActionState.Unknown.class,receipt.state());
        }
        var state=org.xar.ck3.control.application.driver.DriverJson.object(lease.frame().state().bytes(),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
        var player=state.get("played_character");
        if(input.scenario()==Scenario.MISSING_PLAYER)
            assertTrue(player==null||player==OpportunityJson.Nil.INSTANCE,"actual raw missing-player source is required");
        if(input.scenario()==Scenario.TERMINAL) {
            assertInstanceOf(OpportunityJson.Obj.class,player);
            assertFalse(OpportunityJson.bool(((OpportunityJson.Obj)player).get("alive"),"actual player alive"));
        }
        if(input.scenario()==Scenario.CHANGED_PLAYER) {
            if(actual.optionalDriverProducer().isEmpty())throw new IOException("MISSING_NOT_RUN: actual retained prior Driver required to prove changed player");
            assertInstanceOf(OpportunityJson.Obj.class,player);
            var observed=org.xar.ck3.control.contracts.NativeCharacterId.of(OpportunityJson.integer(((OpportunityJson.Obj)player).get("character_id"),"actual played actor")).asBigInteger();
            actual.adopted().authority().withFrozenFacts(same,frozen->{
                if(!(frozen.state() instanceof org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known known))
                    throw new IOException("MISSING_NOT_RUN: actual original prior Driver facts required");
                assertNotEquals(org.xar.ck3.control.contracts.NativeCharacterId.of(known.driver().session().actorId()).asBigInteger(),observed,
                        "changed-player coverage requires actual native actor distinct from the retained prior Driver");return null;
            });
        }
        // These facts stay raw Status data; no terminal reason, actor or Driver is added to the read identity.
        assertEquals(actual.transport().currentSnapshot(input.deadline()).session(),lease.frame().session());
    }
    private static void assertActualConsumers(ContinuityStorePort.Session same,ReadContract<LateOutcome.Status> profile,
            PlanningReadResult.Known<LateOutcome.Status> known,RootRuntimeContext context)throws IOException {
        try {
            PhysicalStatusReadBoundaryTest.assertActualPhysicalReceipt(same,profile,known,context.archive().withSession(same));
            RootUnknownSentinelReadProfileTest.assertActualRead(profile,known,context.archive().withSession(same));
        } catch(IOException failure) { throw failure; }
        catch(Exception failure) { throw new IOException("actual physical Status receipt/archive/public SDK consumer failed",failure); }
    }
    private static void assertHead(org.xar.ck3.control.continuity.writer.WriterContracts.Head before,
            org.xar.ck3.control.continuity.writer.WriterContracts.Head after) {
        assertEquals(before.digest(),after.digest(),"pure Status cannot create canonical ACTION/history/Driver CAS rows");
        assertEquals(before.documents(),after.documents());assertEquals(before.absent(),after.absent());
        assertEquals(before.indexRepairs(),after.indexRepairs());assertEquals(before.snapshotNeedsRecovery(),after.snapshotNeedsRecovery());
    }
    /** Start with the real issued guard. This altered archival DATA must fail and never becomes a current lease/permit. */
    private static void rejectMissingOriginalExecutableClosure(Input input,ContinuityStorePort.Session same,GuardEvidence original)throws IOException {
        var context=input.context();var identity=original.origin().requirePhysicalStatusOnly();
        assertEquals(identity,input.authority().verifyArchived(original,context.archive().withSession(same),same,context.originals()));
        var parsed=org.xar.ck3.control.application.driver.DriverJson.toNode(
                org.xar.ck3.control.application.driver.DriverJson.object(context.originals().read(same,identity.sourceQualification(),16<<20),16<<20));
        assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,parsed);
        var proof=(com.fasterxml.jackson.databind.node.ObjectNode)parsed;
        var executable=org.xar.ck3.control.contracts.ExactRef.fromJson(proof.get("game_executable"));
        var closure=assertInstanceOf(com.fasterxml.jackson.databind.node.ArrayNode.class,proof.get("complete_evidence_closure"));
        int removed=0;
        for(int i=closure.size()-1;i>=0;i--) {
            var ref=org.xar.ck3.control.contracts.ExactRef.fromJson(closure.get(i));
            if(java.nio.file.Path.of(ref.path()).toRealPath().equals(java.nio.file.Path.of(executable.path()).toRealPath())){closure.remove(i);removed++;}
        }
        assertEquals(1,removed,"real complete native qualification must contain its unique original executable");
        assertFalse(closure.isEmpty(),"regression must exercise a nonempty incomplete closure, not the existing empty-closure guard");
        var altered=withSourceProof(context,same,original,proof);
        assertThrows(IllegalArgumentException.class,()->input.authority().verifyArchived(altered,context.archive().withSession(same),same,context.originals()),
                "a nonempty closure that lost the actual HELLO executable must not pass archived source qualification");
    }

    /** Keep the real source bytes and all hashes, then remove the durable Witness contract. No v2 upgrade is inferred. */
    private static void rejectLegacyHashOnlySourceProof(Input input,ContinuityStorePort.Session same,GuardEvidence original)throws IOException {
        var context=input.context();var identity=original.origin().requirePhysicalStatusOnly();
        byte[] bytes=context.originals().read(same,identity.sourceQualification(),16<<20);
        var actual=org.xar.ck3.control.application.readiness.NativeSourceProofCodec.decode(bytes);
        assertFalse(actual.liveWitnesses().isEmpty(),"the actual producer must retain native identities before this negative regression");
        var proof=assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                org.xar.ck3.control.application.driver.DriverJson.toNode(org.xar.ck3.control.application.driver.DriverJson.object(bytes,16<<20)));
        proof.put("schema","xar.java-root-native-source-proof/v2");proof.remove("live_witnesses");
        var altered=withSourceProof(context,same,original,proof);
        assertThrows(IOException.class,()->input.authority().verifyArchived(altered,context.archive().withSession(same),same,context.originals()),
                "original v2 hashes cannot be assigned new Witness/FileID identity or current qualification");
    }

    private static GuardEvidence withSourceProof(RootRuntimeContext context,ContinuityStorePort.Session same,
            GuardEvidence original,com.fasterxml.jackson.databind.node.ObjectNode proof)throws IOException {
        var identity=original.origin().requirePhysicalStatusOnly();
        var badProof=context.archive().preserveArtifact(same,org.xar.ck3.control.application.driver.DriverJson.encodeNode(proof),16<<20);
        var changed=new PhysicalStatusIdentity(identity.transport(),identity.snapshotId(),identity.nativeRevision(),identity.source(),identity.nativeEvidence(),
                identity.helloEvidence(),identity.heartbeatEvidence(),badProof,identity.epochManifest(),identity.observedAt());
        var basis=org.xar.ck3.control.contracts.StrictJson.parse(context.originals().read(same,original.supportingEvidence().getFirst(),128<<10),128<<10);
        assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,basis);
        ((com.fasterxml.jackson.databind.node.ObjectNode)basis).set("identity",PhysicalStatusIdentityCodec.encode(changed));
        var badBasis=context.archive().preserveArtifact(same,org.xar.ck3.control.contracts.StrictJson.canonical(basis,128<<10),128<<10);
        return new GuardEvidence(new CommandOrigin.PhysicalStatusOnly(changed),original.source(),original.sessionId(),original.connectionGeneration(),
                original.operation(),original.nativeEvidence(),original.capabilityEvidence(),original.authorityId(),original.observedAt(),original.validUntil(),List.of(badBasis));
    }
}
