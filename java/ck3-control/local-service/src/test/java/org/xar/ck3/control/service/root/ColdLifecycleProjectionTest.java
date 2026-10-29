package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.LegacyResumeMigration;
import org.xar.ck3.control.application.history.LegacyResumeNormalizer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import static org.junit.jupiter.api.Assertions.*;

final class ColdLifecycleProjectionTest {
    private static final String SHA="a".repeat(64);
    private static final Path PROFILE=Path.of("D:/fixture-profile");
    private static Obj document() {
        String json="""
                {"format_version":2,"bridge_pid":200,"pipe_name":"pipe","episode_character_id":1,"episode_run_id":"episode",
                 "rollback_war_failures":[],"succession_lifecycle":null,
                 "last_checkpoint":{"name":"xar_checkpoint.ck3","size":123,"sha256":"%s","date_raw":12,"history_index":1,
                     "episode_character_id":1,"episode_run_id":"episode","succession_lifecycle":null},
                 "command_history":[{"index":1,"command":"save-checkpoint","ok":true,"result":{"checkpoint":{
                     "size":123,"sha256":"%s","date_raw":12,"succession_lifecycle":null}}}]}
                """.formatted(SHA,SHA);
        return DriverJson.object(json.getBytes(java.nio.charset.StandardCharsets.UTF_8),65536);
    }
    private static FileWitness save(){return new FileWitness(new ExactRef(PROFILE.resolve("save games/xar_checkpoint.ck3").toString(),123,SHA),new FileStatIdentity(BigInteger.valueOf(123),"18446744073709551615","1792857600000000001"));}
    @Test void actualNormalizerMigrationAndAnchorConsumersPreserveExplicitNull() {
        assertInstanceOf(LegacyResumeNormalizer.Rejected.class,LegacyResumeNormalizer.normalize(document(),"pipe"));
        var result=LegacyResumeNormalizer.normalize(document(),"pipe",LegacyResumeNormalizer.LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN);
        assertInstanceOf(LegacyResumeNormalizer.Loaded.class,result);var loaded=(LegacyResumeNormalizer.Loaded)result;
        assertEquals(Nil.INSTANCE,loaded.normalizedLifecycle());assertFalse(loaded.lifecycleMigrationRequired());
        var plan=LegacyResumeMigration.resolve(new LegacyResumeMigration.Request(loaded,BigInteger.valueOf(201),
                new LegacyResumeMigration.ExplicitNativeCampaign(),LegacyResumeMigration.SaveDirectoryState.CONFIGURED,Optional.empty(),Optional.empty()));
        assertInstanceOf(LegacyResumeMigration.PendingColdData.class,plan);
        assertThrows(IllegalArgumentException.class,()->RootColdCheckpointValidator.normalizeLegacyPayload(document(),"pipe",PROFILE,save()));
        var anchor=RootColdCheckpointValidator.normalizeLegacyPayload(document(),"pipe",PROFILE,save(),LegacyResumeNormalizer.LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN);
        assertEquals(Nil.INSTANCE,anchor.get("succession_lifecycle"));
        assertEquals(Nil.INSTANCE,LegacyResumeMigration.lifecycleData(new LegacyResumeMigration.ExplicitNativeCampaign()));
    }
    @Test void ordinaryBindingCannotConsumeExplicitNullAndMissingCannotSelectFixture() {
        var loaded=(LegacyResumeNormalizer.Loaded)LegacyResumeNormalizer.normalize(document(),"pipe",LegacyResumeNormalizer.LifecycleProjection.EXPLICIT_NATIVE_CAMPAIGN);
        var ordinary=LegacyResumeMigration.resolve(new LegacyResumeMigration.Request(loaded,BigInteger.valueOf(201),SuccessionLifecycleBinding.legacyRogue(),
                LegacyResumeMigration.SaveDirectoryState.CONFIGURED,Optional.empty(),Optional.empty()));
        assertInstanceOf(LegacyResumeMigration.Rejected.class,ordinary);
        var fields=new java.util.LinkedHashMap<>(document().members());fields.remove("succession_lifecycle");
        var missing=(LegacyResumeNormalizer.Loaded)LegacyResumeNormalizer.normalize(new Obj(fields),"pipe");
        assertTrue(missing.lifecycleMigrationRequired());
        var fixture=LegacyResumeMigration.resolve(new LegacyResumeMigration.Request(missing,BigInteger.valueOf(201),new LegacyResumeMigration.ExplicitNativeCampaign(),
                LegacyResumeMigration.SaveDirectoryState.CONFIGURED,Optional.empty(),Optional.empty()));
        assertInstanceOf(LegacyResumeMigration.Rejected.class,fixture);
    }
    @Test void partialNullMissingAndObjectAnchorSourcesReject() {
        Obj original=document(),checkpoint=(Obj)original.get("last_checkpoint");
        var missing=new java.util.LinkedHashMap<>(checkpoint.members());missing.remove("succession_lifecycle");
        assertThrows(IllegalArgumentException.class,()->RootColdCheckpointValidator.normalizePayload(original.with("last_checkpoint",new Obj(missing)),"pipe",PROFILE,save()));
        Value bound=LegacyResumeMigration.lifecycleData(new LegacyResumeMigration.BoundLifecycle(SuccessionLifecycleBinding.legacyRogue()));
        assertThrows(IllegalArgumentException.class,()->RootColdCheckpointValidator.normalizePayload(original.with("last_checkpoint",checkpoint.with("succession_lifecycle",bound)),"pipe",PROFILE,save()));
        assertThrows(NullPointerException.class,()->new LegacyResumeMigration.BoundLifecycle(null));
    }
}
