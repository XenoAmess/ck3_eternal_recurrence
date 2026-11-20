package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.AdvancePrimitiveArchivedReplay;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.semantic.NativeSemanticNormalizer;
import org.xar.ck3.control.contracts.semantic.NativePlayedCharacter;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Packet DATA tests, not a verified Root guard, archive registration, actual C++111 packet or Native source role. */
final class Full111OriginalPreparationPacketDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final Instant DEADLINE=Instant.parse("2030-01-02T03:04:05.123456789Z");
    @TempDir Path temporary;

    @Test void completeOriginalTupleRebuildsTheExplicitCanonicalData()throws Exception {
        var command=command(FULL);
        assertEquals(AdvancePrimitives.prepareRequest(command,FULL),
                RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(state(),"native:10",BigInteger.TEN)));
        assertEquals(DEADLINE,command.deadline());
    }

    @Test void sameExecutableCoreAdapterAndWrongBackendCannotSelectFullProfile()throws Exception {
        var command=command(FULL);
        var core=state().put("adapter_id",ExactCk3Build.CK3_121003_STEAM_26785313.coreFrameAdapterId());
        assertThrows(RuntimeException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(core,"native:10",BigInteger.TEN)));
        var backend=state().put("backend","ck3-1.21.0-native-headless-main-thread");
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(backend,"native:10",BigInteger.TEN)));
    }

    @Test void originalSnapshotAndEmptyDomainsMustMatchIndependentlyOfPreparedClaims()throws Exception {
        var command=command(FULL);
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(state(),"native:11",BigInteger.valueOf(11))));
        for(String field:new String[]{"player_armies","active_wars"}) {
            var nonempty=state();nonempty.withArray(field).addObject().put("unqualified",true);
            assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(nonempty,"native:10",BigInteger.TEN)));
        }
        var event=state();event.putObject("active_event").put("unqualified",true);
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(event,"native:10",BigInteger.TEN)));
        var actor=state();((ObjectNode)actor.path("played_character")).put("adapter_id",ExactCk3Build.CK3_1210.coreFullAdapterId());
        assertThrows(IllegalArgumentException.class,()->RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(command,packet(actor,"native:10",BigInteger.TEN)));
    }

    @Test void historicalLegacyProducerDoesNotBorrowTheNewCurrentProfile()throws Exception {
        var old=command(ExactCk3Build.CK3_1210);
        assertEquals(AdvancePrimitives.prepareRequest(old),RootAdvanceInfrastructureFactory.canonicalPreparationDataFromPacket(old,new byte[0]));
    }

    @Test void frameCompositionCarriesDataAndStillRequiresItsOriginalCompleteGuard()throws Exception {
        var delegate=new NativeEffectEvidence.FrameLoader() {
            @Override public DriverObservationAssembler.Complete load(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive archive) {
                throw new IllegalStateException("DATA fixture has no complete original guard");
            }
        };
        var wrapper=RootAdvanceInfrastructureFactory.freshFrameLoader(delegate);
        var data=assertInstanceOf(AdvancePrimitiveArchivedReplay.CanonicalPreparationFrames.class,wrapper);
        var old=command(ExactCk3Build.CK3_1210);
        assertEquals(AdvancePrimitives.prepareRequest(old),data.prepare(old,null,null));
        assertEquals("DATA fixture has no complete original guard",
                assertThrows(IllegalStateException.class,()->wrapper.load(null,null)).getMessage());
        // No verified complete frame was produced, so no replay, source role or Native operation is authorized.
    }

    private static ObjectNode identity(String schema) {
        return StrictJson.object().put("schema",schema).put("game_version",FULL.version()).put("executable_sha256",FULL.executableSha256())
                .put("adapter_id",FULL.coreFullAdapterId()).put("backend",FULL.coreFullBackend());
    }
    private static ObjectNode state() {
        var root=identity(NativeSemanticNormalizer.FLORIN_SCHEMA).put("date_raw",53179368);
        root.set("played_character",identity(NativePlayedCharacter.FLORIN_SCHEMA).put("character_id",1).put("alive",true));
        root.putNull("active_event");root.putArray("active_wars");root.putArray("player_armies");return root;
    }
    private static byte[] packet(ObjectNode state,String snapshotId,BigInteger revision)throws Exception {
        var envelope=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",snapshotId).put("revision",revision);
        envelope.set("state",state);return NativeWire.packet(StrictJson.canonical(envelope));
    }
    private ActionCommand command(ExactCk3Build build)throws Exception {
        byte[] data=new byte[]{'{','}'};Path file=temporary.resolve(build.name()+".json");Files.write(file,data);
        var source=new G2Source("software-fixture-machine","2030-01-02T03:00:00Z",build.executableSha256(),
                new ExactRef(file.toString(),data.length,ActionCodec.sha256(data)));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.TEN,BigInteger.valueOf(53179368)),
                "native:10",BigInteger.ONE,"software-fixture-episode");
        var before=new ProposalLifecycle.ObservationIdentity(source.machineId(),
                new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))),frame,1);
        var operation=new OperationKey("resume-map");var arguments=new OpportunityJson.Obj(Map.of());
        return new ActionCommand("software111-original-resume",before,source,"software-fixture-session",operation,arguments,
                AdvancePrimitives.expected(before,source,operation,arguments),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
    }
}
