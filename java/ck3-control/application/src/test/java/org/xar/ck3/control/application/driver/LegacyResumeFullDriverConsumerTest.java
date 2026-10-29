package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Actual canonical and migration DATA producers through the full modern Driver codec, without a private Root ticket. */
final class LegacyResumeFullDriverConsumerTest {
    private static final String PIPE="original-data-consumer";
    @Test void originalFormatOneUnboundHistorySurvivesRootSuppliedBindingAndFullDriverSerde() {
        Obj original=json("{\"format_version\":1,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":42,\"episode_character_id\":null,\"episode_run_id\":null,"
                +"\"command_history\":[{\"index\":1,\"command\":\"unrecognized-original-command\",\"ok\":false,\"error\":\"UNKNOWN\",\"opaque\":[-0.0,1.0,1e999]}],"
                +"\"last_checkpoint\":null,\"rollback_war_failures\":[]}").with("succession_lifecycle",lifecycle());
        var loaded=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE));
        var request=new LegacyResumeMigration.Request(loaded,BigInteger.valueOf(42),SuccessionLifecycleBinding.legacyRogue(),
                LegacyResumeMigration.SaveDirectoryState.CONFIGURED,Optional.of(nativeState()),Optional.empty());
        var needs=assertInstanceOf(LegacyResumeMigration.RequiredBinding.class,LegacyResumeMigration.resolve(request));
        assertEquals(BigInteger.valueOf(7),needs.actualCharacterId());
        assertEquals(loaded.commandHistory(),((Arr)needs.normalizedPayload().get("command_history")).items());
        var bound=assertInstanceOf(LegacyResumeMigration.SamePidData.class,LegacyResumeMigration.bind(needs,
                new LegacyResumeMigration.BindingIdentity(BigInteger.valueOf(7),"root-actual-identity")));
        assertTrue(bound.pending().isEmpty());
        var modern=DriverStateSnapshot.decodeComplete(DriverJson.encode(bound.modernDriverPayload()));
        assertEquals("root-actual-identity",modern.session().episodeRunId());assertEquals(BigInteger.valueOf(7),modern.session().actorId());
        assertEquals(1,modern.commandHistory().size());
        Obj row=DriverJson.object(modern.commandHistory().getFirst().originalRow().json(),65536);
        assertEquals(loaded.commandHistory().getFirst(),row);assertEquals(new Text("UNKNOWN"),row.get("error"));
        assertEquals(new Arr(List.of(new DecimalValue("-0.0"),new DecimalValue("1.0"),new DecimalValue("1e999"))),row.get("opaque"));
        assertArrayEquals(modern.encode(),DriverStateSnapshot.decodeComplete(modern.encode()).encode());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,modern.lastCheckpoint());
        assertFalse(original.members().containsKey("campaign_goal"),"original absence is retained independently of normalized slots");
    }
    @Test void actualManagedQueueStatesDoNotClearAnOriginalTransactionWithoutMissingOrFailedEvidence() {
        Obj transaction=json("{\"status\":\"awaiting_checkpoint_rebind\",\"request_id\":\"restore-actual\",\"source_bridge_pid\":42,\"replacement_bridge_pid\":null,"
                +"\"checkpoint_sha256\":\""+"a".repeat(64)+"\",\"checkpoint_size\":17,\"checkpoint_date_raw\":24000,\"history_index\":1,\"episode_character_id\":7,\"episode_run_id\":\"e\"}");
        Obj original=json("{\"format_version\":2,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":42,\"episode_character_id\":7,\"episode_run_id\":\"e\",\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failures\":[]}")
                .with("succession_lifecycle",lifecycle()).with("managed_restore_transaction",transaction);
        var loaded=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE));
        var request=new LegacyResumeMigration.Request(loaded,BigInteger.valueOf(42),SuccessionLifecycleBinding.legacyRogue(),
                LegacyResumeMigration.SaveDirectoryState.CONFIGURED,Optional.of(nativeState()),Optional.empty());
        var waiting=assertInstanceOf(LegacyResumeMigration.NeedsManagedQueue.class,LegacyResumeMigration.resolve(request));
        var present=assertInstanceOf(LegacyResumeMigration.SamePidData.class,LegacyResumeMigration.withManagedQueue(waiting,
                new LegacyResumeMigration.ManagedQueueData(waiting.requestId(),LegacyResumeMigration.QueueStatus.PRESENT)));
        assertEquals(transaction,present.normalizedPayload().get("managed_restore_transaction"));assertFalse(present.transactionDisarmed());
        assertThrows(IllegalStateException.class,present::modernDriverPayload);
        for(var state:List.of(LegacyResumeMigration.QueueStatus.MISSING,LegacyResumeMigration.QueueStatus.FAILED)) {
            var disarmed=assertInstanceOf(LegacyResumeMigration.SamePidData.class,LegacyResumeMigration.withManagedQueue(waiting,
                    new LegacyResumeMigration.ManagedQueueData(waiting.requestId(),state)));
            assertTrue(disarmed.transactionDisarmed());assertEquals(Nil.INSTANCE,disarmed.modernDriverPayload().get("managed_restore_transaction"));
            assertEquals(loaded.commandHistory(),disarmed.modernDriverPayload().get("command_history") instanceof Arr history?history.items():List.of());
        }
        assertInstanceOf(LegacyResumeMigration.NeedsManagedQueue.class,LegacyResumeMigration.withManagedQueue(waiting,
                new LegacyResumeMigration.ManagedQueueData(waiting.requestId(),LegacyResumeMigration.QueueStatus.UNAVAILABLE)));
    }
    private static Obj nativeState(){return json("{\"map_ready\":true,\"date_raw\":24000,\"played_character\":{\"character_id\":7,\"alive\":true,\"source\":\"native\"}}");}
    private static Obj lifecycle(){return DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),65536);}
    private static Obj json(String wire){return DriverJson.object(wire.getBytes(StandardCharsets.UTF_8),65536);}
}
