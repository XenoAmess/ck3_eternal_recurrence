package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.LifecycleProjection;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Loaded;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics.AdoptionRefusalReason;
import org.xar.ck3.control.service.root.OriginalDriverJournal;
import org.xar.ck3.control.service.root.RootOriginalDriverJournal;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Actual WAL reader -> persisted projection -> sole normalizer -> actual adoption policy DATA.
 * This never manufactures a private load, frozen profile, ManagedGameSession or accepted capture. */
final class OriginalLifecycleImportTest {
    private static final String PIPE="software-lifecycle-import";

    @Test void actualJournalReplayPreservesExplicitNullThroughImportAndNativeCampaignClassification() throws Exception {
        var replay=replaySealed(base().with("succession_lifecycle",Nil.INSTANCE));
        assertEquals(OriginalDriverJournal.Status.REPLAYED,replay.status());
        assertInstanceOf(RootOriginalDriverJournal.ExplicitNullLifecycle.class,
                RootOriginalDriverJournal.readPersistedLifecycle(replay.payload()));
        Loaded normalized=normalize(replay,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN);
        assertSame(Nil.INSTANCE,normalized.normalizedLifecycle());assertFalse(normalized.lifecycleMigrationRequired());
        assertTrue(DriverBootstrap.lifecycleRefusal(normalized,new LegacyResumeMigration.ExplicitNativeCampaign()).isEmpty());
        assertEquals(Optional.of(AdoptionRefusalReason.PERSISTED_LIFECYCLE_MISMATCH),
                DriverBootstrap.lifecycleRefusal(normalized,new LegacyResumeMigration.BoundLifecycle(SuccessionLifecycleBinding.legacyRogue())));
        byte[] full=OriginalDriverJournal.canonical(replay.payload(),OriginalDriverJournal.MAXIMUM_DRIVER_BYTES).bytes();
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8),DriverJson.encode(DriverJson.object(full,1<<20).get("succession_lifecycle")));
    }

    @Test void missingLegacyAndOrdinaryBindingKeepTheirExistingDistinctAdoptionRules() throws Exception {
        Obj noLifecycle=withoutLifecycle(base());
        var missing=OriginalDriverJournal.replay(DriverJson.encode(noLifecycle),Optional.empty());
        assertInstanceOf(RootOriginalDriverJournal.MissingLegacyLifecycle.class,
                RootOriginalDriverJournal.readPersistedLifecycle(missing.payload()));
        Loaded legacy=normalize(missing,LifecycleProjection.BOUND_OR_LEGACY);
        assertTrue(legacy.lifecycleMigrationRequired());
        assertTrue(DriverBootstrap.lifecycleRefusal(legacy,new LegacyResumeMigration.BoundLifecycle(SuccessionLifecycleBinding.legacyRogue())).isEmpty());
        assertEquals(Optional.of(AdoptionRefusalReason.LEGACY_LIFECYCLE_INCOMPATIBLE),
                DriverBootstrap.lifecycleRefusal(legacy,new LegacyResumeMigration.ExplicitNativeCampaign()));
        Obj bound=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),SuccessionLifecycleCodec.MAX_BYTES);
        var ordinary=replaySealed(base().with("succession_lifecycle",bound));
        var projection=assertInstanceOf(RootOriginalDriverJournal.BoundPersistedLifecycle.class,
                RootOriginalDriverJournal.readPersistedLifecycle(ordinary.payload()));
        assertEquals(SuccessionLifecycleBinding.legacyRogue(),projection.binding());
        Loaded loaded=normalize(ordinary,LifecycleProjection.BOUND_OR_LEGACY);
        assertTrue(DriverBootstrap.lifecycleRefusal(loaded,new LegacyResumeMigration.BoundLifecycle(projection.binding())).isEmpty());
        assertEquals(Optional.of(AdoptionRefusalReason.PERSISTED_LIFECYCLE_MISMATCH),
                DriverBootstrap.lifecycleRefusal(loaded,new LegacyResumeMigration.ExplicitNativeCampaign()));
    }

    @Test void wrongLifecycleTypesAndWalTamperingRemainRejectedBeforeAnyAdoptionPermission() throws Exception {
        for(Value invalid:List.of(new Bool(false),new Text("null"),new IntegerValue(BigInteger.ZERO),new Arr(List.of()))) {
            var replay=OriginalDriverJournal.replay(DriverJson.encode(base().with("succession_lifecycle",invalid)),Optional.empty());
            assertThrows(java.io.IOException.class,()->RootOriginalDriverJournal.readPersistedLifecycle(replay.payload()));
            Obj full=DriverJson.object(OriginalDriverJournal.canonical(replay.payload(),1<<20).bytes(),1<<20);
            assertInstanceOf(LegacyResumeNormalizer.Rejected.class,LegacyResumeNormalizer.normalize(full,PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        }
        byte[] sealed=sealed(base().with("succession_lifecycle",Nil.INSTANCE));byte[] journal=journal(sealed);
        byte[] altered=sealed(base().with("succession_lifecycle",Nil.INSTANCE).with("bridge_pid",new IntegerValue(BigInteger.valueOf(43))));
        assertThrows(OriginalDriverJournal.JournalInvalid.class,()->OriginalDriverJournal.replay(altered,Optional.of(journal)));
    }

    private static Loaded normalize(OriginalDriverJournal.Replayed original,LifecycleProjection projection) {
        byte[] complete=OriginalDriverJournal.canonical(original.payload(),OriginalDriverJournal.MAXIMUM_DRIVER_BYTES).bytes();
        return assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(DriverJson.object(complete,1<<20),PIPE,projection));
    }
    private static OriginalDriverJournal.Replayed replaySealed(Obj full) {
        byte[] base=sealed(full);return OriginalDriverJournal.replay(base,Optional.of(journal(base)));
    }
    private static byte[] sealed(Obj full) {
        return DriverJson.encode(new Obj(Map.of("format_version",new IntegerValue(BigInteger.valueOf(3)),
                "schema",new Text(OriginalDriverJournal.SEALED_SCHEMA),"sealed_full_state",full)));
    }
    private static byte[] journal(byte[] originalBase) {
        return DriverJson.encode(new Obj(Map.of("schema",new Text(OriginalDriverJournal.JOURNAL_SCHEMA),
                "base_sha256",new Text(DriverJson.sha256(originalBase)),"base_history_rows",new IntegerValue(BigInteger.ZERO),
                "entries",new Arr(List.of()),"consolidated_sha256",Nil.INSTANCE)));
    }
    private static Obj withoutLifecycle(Obj original) {
        var fields=new java.util.LinkedHashMap<>(original.members());fields.remove("succession_lifecycle");return new Obj(fields);
    }
    private static Obj base() {
        var fields=new java.util.LinkedHashMap<String,Value>();fields.put("format_version",new IntegerValue(BigInteger.TWO));
        fields.put("pipe_name",new Text(PIPE));fields.put("bridge_pid",new IntegerValue(BigInteger.valueOf(42)));
        fields.put("episode_character_id",new IntegerValue(BigInteger.valueOf(7)));fields.put("episode_run_id",new Text("software-episode"));
        fields.put("command_history",new Arr(List.of()));fields.put("last_checkpoint",Nil.INSTANCE);
        fields.put("rollback_war_failure",Nil.INSTANCE);fields.put("managed_restore_transaction",Nil.INSTANCE);
        fields.put("succession_expectation",Nil.INSTANCE);fields.put("succession_lifecycle",Nil.INSTANCE);fields.put("campaign_goal",Nil.INSTANCE);
        return new Obj(fields);
    }
}
