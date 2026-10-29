package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Saved full Driver auxiliary DATA must not overwrite the actual Native episode domain. No private Saved authority is fabricated. */
final class SavedNativeCampaignProjectionTest {
    @Test void restoredDriverOverlayDoesNotInventOrReplaceOriginalEpisodeFieldsAcrossTheActualManifestAndPublicSnapshot() {
        for(String episode:List.of("",",\"episode_run_id\":null,\"succession_lifecycle\":null",
                ",\"episode_run_id\":\"actual-native-run\",\"episode_character_id\":922,\"succession_lifecycle\":{\"retained\":true},\"one_life_terminal\":null")) {
            String raw=DriverObservationAssemblerTest.STATE.strip();
            raw=raw.substring(0,raw.length()-1)+episode+"}";
            var actual=DriverObservationAssemblerTest.actual(raw);var base=DriverStateAssemblerTest.known();var old=base.driver();
            var driver=new DriverStateSnapshot.Complete(old.session(),old.commandHistory(),old.lastCheckpoint(),old.rollbackWarFailure(),
                    old.managedRestoreTransaction(),old.successionExpectation(),new DriverStateSnapshot.NullValue(),old.campaignGoal(),old.rollbackWarFailures());
            var stamp=new DriverSnapshotFacts.Stamp(base.stamp().driverVersion(),base.stamp().episodeEpoch(),base.stamp().game(),
                    base.stamp().episodeRunId(),DriverJson.sha256(driver.encode()));
            var originalAuxiliary=new OpportunityJson.Obj(Map.of("episode_run_id",new OpportunityJson.Text("retained-private-run"),
                    "episode_character_id",new OpportunityJson.IntegerValue(BigInteger.ONE),"succession_lifecycle",OpportunityJson.Nil.INSTANCE,
                    "episode_identity_pending",new OpportunityJson.Bool(false),"one_life_terminal",new OpportunityJson.Bool(false),
                    "one_life_terminal_reason",OpportunityJson.Nil.INSTANCE,"retained_saved_metadata",new OpportunityJson.Text("original")));
            var clean=NativeCampaignProjection.withoutDriverEpisodeOverlay(originalAuxiliary);
            var fields=new LinkedHashMap<>(clean.members());fields.put("episode_projection",new OpportunityJson.Text(NativeCampaignProjection.WIRE_MODE));
            var semanticFields=new OpportunityJson.Obj(fields);
            var known=new DriverSnapshotFacts.Known(driver,stamp,base.originalHistoryBasis(),base.actionRows(),originalAuxiliary,base.loop(),Optional.empty());
            var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.valueOf(2),
                    DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,DriverStateAssemblerTest.source(),semanticFields,
                    DriverStateAssemblerTest.ref(driver.encode()));
            var facts=DriverObservationEvidenceReader.decode(DriverStateAssemblerTest.ref(manifest.bytes()),manifest,RawJson.fullMaterial(driver.encode()),actual);
            var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,
                    DriverStateAssemblerTest.ref(actual.originalPacket())));
            var original=DriverObservationAssembler.originalNativeState(actual);
            var exposed=PublicSnapshotCodec.decode(DriverPublicContext.from(complete).snapshot());
            for(String field:List.of("episode_run_id","episode_character_id","succession_lifecycle",
                    "episode_identity_pending","one_life_terminal","one_life_terminal_reason")) {
                assertEquals(original.members().containsKey(field),complete.semantic().members().containsKey(field),field);
                assertEquals(original.get(field),complete.semantic().get(field),field);
                assertEquals(original.members().containsKey(field),exposed.members().containsKey(field),field);
                assertEquals(original.get(field),exposed.get(field),field);
            }
            assertEquals(new OpportunityJson.Text("original"),complete.semantic().get("retained_saved_metadata"));
            assertEquals(new OpportunityJson.Text("retained-private-run"),known.auxiliary().get("episode_run_id"));
            assertArrayEquals(known.driver().encode(),driver.encode());
            NativeCampaignProjection.requireJoinedSnapshot(complete.originalProjection().orElseThrow(),
                    RawJson.fullMaterial(DriverJson.encode(complete.semantic())));
        }
    }
}
