package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.LifecycleProjection;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.HistoryMaterialization;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Loaded;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Presence;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer.Rejected;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Normalization produces DATA; only the private frozen fixture caller may select the null projection. */
final class LegacyNativeCampaignNormalizationTest {
    private static final String PIPE="software-native-campaign-projection";

    @Test void explicitNullRetainsJsonTypePresenceAndFalseMigrationAcrossActualNormalizerRoundtrip() {
        Obj original=base().with("succession_lifecycle",Nil.INSTANCE);
        Loaded normalized=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        assertSame(Nil.INSTANCE,normalized.normalizedLifecycle());
        assertEquals(Presence.NULL,normalized.originalPresence().lifecycle());
        assertFalse(normalized.lifecycleMigrationRequired());
        assertTrue(normalized.normalizedPayload().members().containsKey("succession_lifecycle"));
        assertSame(Nil.INSTANCE,normalized.normalizedPayload().get("succession_lifecycle"));
        assertEquals(new Bool(false),normalized.normalizedPayload().get("succession_lifecycle_migration_required"));
        Obj wire=DriverJson.object(normalized.encode(),1<<20);
        Loaded again=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(wire.with("pipe_name",new Text(PIPE)),PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        assertSame(Nil.INSTANCE,again.normalizedLifecycle());
        assertFalse(again.lifecycleMigrationRequired());
    }

    @Test void missingFieldRemainsLegacyMigrationAndCannotSelectNativeNull() {
        Loaded legacy=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(base(),PIPE));
        assertEquals(Presence.MISSING,legacy.originalPresence().lifecycle());assertTrue(legacy.lifecycleMigrationRequired());
        assertInstanceOf(Obj.class,legacy.normalizedLifecycle());
        assertEquals(SuccessionLifecycleBinding.legacyRogue(),SuccessionLifecycleCodec.decode(DriverJson.encode(legacy.normalizedLifecycle())));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base(),PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
    }

    @Test void ordinaryObjectGuardAndDefaultNullRejectionRemainUnchanged() {
        Obj bound=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),SuccessionLifecycleCodec.MAX_BYTES);
        Loaded ordinary=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",bound),PIPE));
        assertEquals(bound,ordinary.normalizedLifecycle());assertFalse(ordinary.lifecycleMigrationRequired());
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",Nil.INSTANCE),PIPE));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",bound),PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
    }

    @Test void explicitNativeProjectionDoesNotCoerceOtherJsonValuesOrRelaxUnrelatedStrictFields() {
        for(Value invalid:List.of(new Bool(false),new Text("null"),new Arr(List.of()),new IntegerValue(BigInteger.ZERO),new DecimalValue("0.0")))
            assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",invalid),PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(base().with("succession_lifecycle",Nil.INSTANCE).with("bridge_pid",new Bool(true)),PIPE,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
    }

    @Test void explicitNativeOmitPreservesNullAndStillValidatesOriginalHistoryWithoutMaterializingIt() {
        Obj row=new Obj(Map.of("index",new IntegerValue(BigInteger.ONE),"command",new Text("software-query"),"ok",new Bool(true)));
        Obj original=base().with("succession_lifecycle",Nil.INSTANCE).with("command_history",new Arr(List.of(row)));
        Loaded omitted=assertInstanceOf(Loaded.class,LegacyResumeNormalizer.normalize(original,PIPE,
                HistoryMaterialization.OMIT,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        assertEquals(HistoryMaterialization.OMIT,omitted.historyMaterialization());
        assertFalse(omitted.normalizedPayload().members().containsKey("command_history"));
        assertThrows(IllegalStateException.class,omitted::commandHistory);
        assertSame(Nil.INSTANCE,omitted.normalizedLifecycle());assertFalse(omitted.lifecycleMigrationRequired());
        Obj invalid=original.with("command_history",new Arr(List.of(row.with("ok",new Text("true")))));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(invalid,PIPE,
                HistoryMaterialization.OMIT,LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN));
        assertInstanceOf(Rejected.class,LegacyResumeNormalizer.normalize(original,PIPE,
                HistoryMaterialization.OMIT,LifecycleProjection.BOUND_OR_LEGACY));
    }

    private static Obj base() {
        return new Obj(Map.of("format_version",new IntegerValue(BigInteger.TWO),"pipe_name",new Text(PIPE),
                "bridge_pid",new IntegerValue(BigInteger.valueOf(42)),"episode_character_id",new IntegerValue(BigInteger.valueOf(7)),
                "episode_run_id",new Text("software-episode"),"command_history",new Arr(List.of()),"last_checkpoint",Nil.INSTANCE));
    }
}
