package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;

/** Java correction for the observed native actor domain, not parity with the old Python positive-only bug.
 * Canonical legacy DATA -> migration -> modern complete DATA; no original journal, private Root or cold permission. */
final class LegacyResumeMigrationNativeActorTest {
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static Obj base() {
        return new Obj(Map.of("format_version",number(2),"pipe_name",new Text("source-native-actor"),"bridge_pid",number(42),
                "episode_character_id",Nil.INSTANCE,"episode_run_id",Nil.INSTANCE,"command_history",new Arr(List.of()),"last_checkpoint",Nil.INSTANCE));
    }
    private static LegacyResumeMigration.Plan resolve(Value actor) {
        var loaded=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(base(),"source-native-actor"));
        Obj actual=new Obj(Map.of("map_ready",new Bool(true),"date_raw",number(24000),"played_character",new Obj(Map.of("character_id",actor))));
        return LegacyResumeMigration.resolve(new LegacyResumeMigration.Request(loaded,BigInteger.valueOf(42),SuccessionLifecycleBinding.legacyRogue(),
                LegacyResumeMigration.SaveDirectoryState.ABSENT,Optional.of(actual),Optional.empty()));
    }
    @Test void actualSignedActorBindsWithoutChangingItsNativeValueAndRoundTripsModernData() {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}) {
            var pending=assertInstanceOf(LegacyResumeMigration.RequiredBinding.class,resolve(number(actor)));
            assertEquals(BigInteger.valueOf(actor),pending.actualCharacterId());
            var bound=assertInstanceOf(LegacyResumeMigration.SamePidData.class,LegacyResumeMigration.bind(pending,
                    new LegacyResumeMigration.BindingIdentity(NativeCharacterId.of(actor).asBigInteger(),"actual-root-issued-run")));
            assertTrue(bound.pending().isEmpty());Obj modern=bound.modernDriverPayload();
            assertEquals(number(actor),modern.get("episode_character_id"));
            assertEquals(new Text("actual-root-issued-run"),modern.get("episode_run_id"));
            assertEquals(modern,DriverJson.object(DriverJson.encode(modern),1048576));
            var retained=assertInstanceOf(LegacyResumeNormalizer.Loaded.class,LegacyResumeNormalizer.normalize(modern,"source-native-actor"));
            assertEquals(BigInteger.valueOf(actor),retained.episode().orElseThrow().characterId());
            assertEquals(new Arr(List.of()),modern.get("command_history"));
        }
    }
    @Test void absentAndMalformedNativeActorNeverMintEpisodeBinding() {
        assertFalse(resolve(number(-1)) instanceof LegacyResumeMigration.RequiredBinding);
        for(Value bad:List.of(new Bool(true),new Text("-2"),new DecimalValue("-2.0"),number(2147483648L)))
            assertInstanceOf(LegacyResumeMigration.Rejected.class,resolve(bad));
        assertThrows(IllegalArgumentException.class,()->new LegacyResumeMigration.BindingIdentity(BigInteger.valueOf(-1),"run"));
        assertThrows(IllegalArgumentException.class,()->new LegacyResumeMigration.BindingIdentity(BigInteger.valueOf(2147483648L),"run"));
        var original=assertInstanceOf(LegacyResumeMigration.RequiredBinding.class,resolve(number(-2)));
        assertThrows(IllegalArgumentException.class,()->LegacyResumeMigration.bind(original,new LegacyResumeMigration.BindingIdentity(BigInteger.valueOf(2),"run")));
    }
}
