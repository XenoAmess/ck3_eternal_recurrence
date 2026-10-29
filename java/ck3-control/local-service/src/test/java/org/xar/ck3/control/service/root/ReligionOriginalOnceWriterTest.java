package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual canonical writer/archive/collector/central coordinator over a declared software packet edge. */
final class ReligionOriginalOnceWriterTest {
    @TempDir Path temporary;
    @Test void bothPrivateOperationsKeepUnknownWithoutASecondNativeWriteAcrossReopen()throws Exception {
        for(var kind:ReligionConversionActions.Kind.values()) {
            var original=new AtomicReference<ReligionCapabilities.Registration>();
            var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(PlayerReligionContext.Build.CROZIER3.sha256().toLowerCase(java.util.Locale.ROOT),"software-religion-original",
                    reviewed->List.of(),request->{throw new AssertionError("no independent effect READ is supplied by this UNKNOWN test");},Optional.of("1.20.0.3"),Set.of());
            var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(kind.operation(),"software.original-religion.permission",
                    (command,attempt,dispatch)->new ActionPorts.Pending("controlled missing independent post-state; preserve original UNKNOWN",List.of(attempt.guard().nativeEvidence())),()->{},
                    Optional.empty(),Optional.of(reviewed->{
                        var registration=new ReligionCapabilities.Registration(Arrays.stream(ReligionCapabilities.ReadKind.values()).map(k->new ReligionCapabilities.ReadSource(k,reviewed)).toList(),
                                Arrays.stream(ReligionCapabilities.MutationSource.values()).map(k->new ReligionCapabilities.ActionSource(k,reviewed)).toList(),List.of(),
                                (k,r)->assertEquals(reviewed,r.source().sourceRef()),(k,c)->assertEquals(reviewed,c.source().sourceRef()));original.set(registration);
                        // Controlled qualification edge only. This fixture never proves a loaded CK3 module or live permission.
                        return registration.privateActions((config,hello,guard,request)->{assertEquals(readScenario.profileSha256(),hello.gameSha256().toLowerCase(java.util.Locale.ROOT));assertEquals(kind.operation().value(),request.step());return reviewed;},
                                (config,hello,guard,request)->{assertEquals(readScenario.profileSha256(),hello.gameSha256().toLowerCase(java.util.Locale.ROOT));assertEquals(kind.operation().value(),request.step());return reviewed;})
                                .stream().filter(p->p.operation().equals(kind.operation())).findFirst().orElseThrow();
                    }),false,Optional.of(command->original.get().prepare(command)));
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve(kind.name()),true,readScenario,List.of(scenario))) {
                ActionCommand command=command(fixture,kind,"caller-once",BigInteger.valueOf(5));ActionReceipt first=execute(fixture,command);assertFalse(first.settled());assertEquals(1,fixture.nativeActionWrites());
                byte[] durable=fixture.ledgerBytes();assertEquals(first,fixture.coordinator.execute(command));assertArrayEquals(durable,fixture.ledgerBytes());assertEquals(1,fixture.nativeActionWrites());
                var retained=RootReligionConversionRuntime.retainedOriginal(kind,List.of(first),command.before().frame().episodeRunId(),command.before().frame().identity().player(),"new-caller-cannot-clear-unknown");assertEquals(first,retained.orElseThrow());
                assertEquals(first,fixture.reopenAndReturnExisting(command));assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(durable,fixture.ledgerBytes());
                ObjectNode changed=ReligionCodec.object(new RawJson(OpportunityJson.encode(command.arguments())));if(kind==ReligionConversionActions.Kind.CONVERSION)changed.put("target_rite_id",6);else changed.put("province_id",6);
                var collision=new ActionCommand(command.actionId(),command.before(),command.source(),command.sessionId(),command.operation(),OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(changed).bytes()),"changed once parameters"),command.expected(),command.claims(),command.deadline());
                assertThrows(RuntimeException.class,()->fixture.coordinator.execute(collision));assertEquals(1,fixture.nativeActionWrites());assertArrayEquals(durable,fixture.ledgerBytes());
            }
        }
    }
    @Test void canonicalCallerScopeKeepsUnicodeAndExcludesRevisionConnectionAndTarget(){
        var kind=ReligionConversionActions.Kind.CONVERSION;String id=RootReligionConversionRuntime.canonicalActionId(kind,"actual-episode",BigInteger.valueOf(73),"原始一次ID");
        assertEquals(id,RootReligionConversionRuntime.canonicalActionId(kind,"actual-episode",BigInteger.valueOf(73),"原始一次ID"));
        assertNotEquals(id,RootReligionConversionRuntime.canonicalActionId(kind,"new-episode",BigInteger.valueOf(73),"原始一次ID"));assertNotEquals(id,RootReligionConversionRuntime.canonicalActionId(ReligionConversionActions.Kind.COUNTY,"actual-episode",BigInteger.valueOf(73),"原始一次ID"));
        assertThrows(IllegalArgumentException.class,()->RootReligionConversionRuntime.canonicalActionId(kind,"actual-episode",BigInteger.valueOf(73),"界".repeat(22)));
    }
    private static ActionCommand command(ActionWriterIntegrationFixture fixture,ReligionConversionActions.Kind kind,String caller,BigInteger target)throws Exception {
        var base=fixture.command("temporary-original-data");var frame=base.before().frame();var nativeFrame=frame.identity();ObjectNode args=StrictJson.object().put("expected_snapshot_revision",nativeFrame.nativeRevision()).put("expected_public_revision",frame.revision()).put("expected_date_raw",nativeFrame.dateRaw()).put("expected_player_character_id",nativeFrame.player()).put("action_id",caller);
        if(kind==ReligionConversionActions.Kind.CONVERSION)args.put("target_rite_id",target).put("max_piety_cost_raw",BigInteger.valueOf(100000));else args.put("expected_active_task_id",4).put("expected_incumbent_character_id",8).put("province_id",target).put("replace_existing_task",true);
        var expected=new ExpectedPostcondition(1,base.before(),base.source(),kind.observer(),ReligionConversionActions.expected(kind,args));return new ActionCommand(RootReligionConversionRuntime.canonicalActionId(kind,frame.episodeRunId(),nativeFrame.player(),caller),base.before(),base.source(),base.sessionId(),kind.operation(),OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(args).bytes()),"actual original private request"),expected,new Claims(Set.of(),Set.of(),Set.of(nativeFrame.player()),Set.of()),base.deadline());
    }
    private static ActionReceipt execute(ActionWriterIntegrationFixture fixture,ActionCommand command)throws Exception {
        AtomicReference<ActionReceipt> retained=new AtomicReference<>();try{fixture.physicalInputs().transport().withMailbox(command.deadline(),scope->{retained.set(fixture.coordinator.execute(command));return null;});}
        catch(IOException poisoned){if(retained.get()==null)throw poisoned;assertFalse(retained.get().settled(),"mailbox poison cannot create an applied effect");}return retained.get();
    }
}
