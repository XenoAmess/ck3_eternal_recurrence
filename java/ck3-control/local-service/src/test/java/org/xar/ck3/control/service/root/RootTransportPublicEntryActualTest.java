package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.util.EnumSet;
import java.util.Objects;
import java.util.Optional;
import java.util.ServiceLoader;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;

/** Mandatory genuine installed inputs; no Context, Complete, Source or lease is fabricated here. */
public final class RootTransportPublicEntryActualTest {
    private static final String TOOL="ck3_read_tactical_daily_sentinel_status_private_v1";
    public record PublicInput(RootPhysicalStatusReadAuthorityActualTest.Input original,
            RootPublicHandlerProductsFactory.Context publicContext,PublicMcpHost actualAlreadyInstalledHost,PublicMcpDirectory directory) {
        public PublicInput {Objects.requireNonNull(original);Objects.requireNonNull(publicContext);Objects.requireNonNull(actualAlreadyInstalledHost);Objects.requireNonNull(directory);}
    }
    @FunctionalInterface public interface ActualPublicInputWork {
        void consume(RootPhysicalStatusReadAuthorityActualTest.Input original,PublicInput supplied)throws Exception;
    }
    /** The same live callback supplies the identical original Input, Context and installed Root host. */
    public interface PublicInputsProducer extends RootPhysicalStatusReadAuthorityActualTest.InputsProducer {
        void withActualPublicInputs(ActualPublicInputWork consumer)throws Exception;
        @Override default void withActualInstalledInputs(RootPhysicalStatusReadAuthorityActualTest.InputWork consumer)throws Exception {
            Objects.requireNonNull(consumer);
            withActualPublicInputs((original,supplied)->{
                if(original!=supplied.original())throw new IOException("actual public callback replaced its original physical input");
                consumer.consume(original);
            });
        }
    }
    @Test void actualTypedDirectoryInvokesPhysicalSupplierAcrossAllOriginalPhases()throws Exception {
        RootPhysicalStatusReadAuthorityActualTest.actualChecksOnce();
    }
    public static void exercise(PublicInput input)throws Exception {
        var original=input.original();var context=original.context();
        original.authority().requireContext(context);assertSame(original.authority(),context.physicalStatusReads());
        input.publicContext().withInstalledData(original.deadline(),(installed,same)->{
            assertSame(context,installed.context());
            assertSame(original.profile(),installed.remainingDomains().life().infrastructure().physicalStatuses());
            var transport=installed.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.TRANSPORT,
                    RootDriverTransportRuntimeFactory.Runtime.class);transport.requireContext(context);assertTrue(transport.privateSemanticReadonly());
            if(original.scenario()==RootPhysicalStatusReadAuthorityActualTest.Scenario.PRE_GAME_NO_DRIVER)
                assertTrue(context.optionalDriverProducer().isEmpty());
            return null;
        });
        assertSame(input.directory(),input.actualAlreadyInstalledHost().current().orElseThrow(),"actual already-installed host directory identity is required");
        assertEquals(PublicMcpDirectory.Scope.COMPLETE_MIGRATION,input.directory().scope(),"a software-only directory cannot stand in for the real installed host");
        var descriptor=input.directory().tools().stream().filter(value->value.name().equals(TOOL)).findFirst().orElseThrow();
        var call=new PublicMcpDirectory.ToolCall(TOOL,new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,
                Optional.of(new RawJson(new byte[]{'{','}'}))),Optional.empty(),new McpCancellation());
        descriptor.validateArguments(call.arguments());
        WriterContracts.Head before=context.withSession(same->same.head());
        Optional<ActionReceipt> unresolved=context.withSession(same->{
            if(original.unresolvedActionId().isEmpty())return Optional.<ActionReceipt>empty();
            return ContinuityActionJournal.lookup(same.head().state(),original.unresolvedActionId().orElseThrow(),context.archive().withSession(same));
        });
        if(original.scenario()==RootPhysicalStatusReadAuthorityActualTest.Scenario.UNKNOWN)
            assertInstanceOf(ActionState.Unknown.class,unresolved.orElseThrow().state());
        var response=input.directory().invoke(call);descriptor.validateResult(response);
        assertSame(input.directory(),input.actualAlreadyInstalledHost().current().orElseThrow());
        var encoded=DriverJson.object(response.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new OpportunityJson.Bool(false),encoded.get("isError"));
        var business=OpportunityJson.object(encoded.get("structuredContent"),"actual public Status result");
        assertEquals(new OpportunityJson.Text("native-headless"),business.get("backend_id"));
        var status=OpportunityJson.object(business.get("tactical_daily_sentinel"),"actual public Status token");
        assertInstanceOf(OpportunityJson.Text.class,status.get("generation"));
        var content=OpportunityJson.array(encoded.get("content"),"actual text content");
        var text=(OpportunityJson.Text)OpportunityJson.object(content.getFirst(),"actual text block").get("text");
        assertEquals(business,DriverJson.object(text.value().getBytes(java.nio.charset.StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES));
        var received=NativeWire.decode(context.transport().diagnostics().lastOriginalPacket().value());
        assertInstanceOf(NativeWire.CommandResult.class,received);var ack=(NativeWire.CommandResult)received;
        assertTrue(ack.nativeOk());assertTrue(context.transport().originalRequestChronology(ack.requestId()).isPresent());
        context.withSession(same->{
            assertEquals(before.digest(),same.head().digest());assertEquals(before.documents(),same.head().documents());
            assertEquals(before.absent(),same.head().absent());assertEquals(before.indexRepairs(),same.head().indexRepairs());
            assertEquals(before.snapshotNeedsRecovery(),same.head().snapshotNeedsRecovery());
            if(unresolved.isPresent())assertEquals(unresolved,ContinuityActionJournal.lookup(same.head().state(),
                    unresolved.orElseThrow().command().actionId(),context.archive().withSession(same)));
            return null;
        });
    }
}
