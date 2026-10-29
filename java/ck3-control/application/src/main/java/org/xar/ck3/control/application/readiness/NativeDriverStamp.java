package org.xar.ck3.control.application.readiness;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One versioned binding of full Driver bytes to the actual received semantic/native observation. */
public final class NativeDriverStamp {
    public static final String SCHEMA = "xar.native-semantic-driver-stamp/v2";
    private NativeDriverStamp() { }
    public static byte[] encode(Complete frame, Known driver) {
        var stamp = driver.stamp(); var id = frame.identity(); var f = id.frame();
        StrictJson.require(stamp.game().equals(id.game()) && stamp.episodeRunId().equals(f.episodeRunId())
                && driver.observation().isPresent(), "same held observed Driver required for a semantic stamp");
        var observed = driver.observation().orElseThrow();
        StrictJson.require(observed.driverVersion() == stamp.driverVersion() && observed.episodeEpoch() == stamp.episodeEpoch()
                && observed.snapshotId().equals(f.snapshotId()) && observed.nativeRevision().equals(f.identity().nativeRevision())
                && observed.publicRevision().equals(f.revision()) && observed.observationVersion() == id.observationVersion()
                && observed.transport().machineId().equals(id.machineId()) && observed.transport().game().equals(id.game())
                && observed.transport().sessionId().equals(frame.sessionId())
                && observed.transport().connectionGeneration().equals(frame.connectionGeneration()), "Driver stamp crossed the actual observation");
        Map<String, OpportunityJson.Value> row = new LinkedHashMap<>();
        row.put("schema", text(SCHEMA)); row.put("machine_id", text(id.machineId()));
        row.put("game_pid", integer(id.game().pid()));
        row.put("game_creation_filetime", text(id.game().creationFiletime().value().toString()));
        row.put("session_id", text(frame.sessionId())); row.put("connection_generation", new OpportunityJson.IntegerValue(frame.connectionGeneration()));
        row.put("driver_version", integer(stamp.driverVersion())); row.put("episode_epoch", integer(stamp.episodeEpoch()));
        row.put("observation_version", integer(id.observationVersion()));
        StrictJson.require(frame.fullBindingSha256().equals(DriverObservationAssembler.bindingSha256(frame.semantic())),
                "full semantic binding differs before stamp publication");
        row.put("full_binding_sha256", text(frame.fullBindingSha256()));
        row.put("driver_sha256", text(stamp.driverSha256())); row.put("episode_run_id", text(f.episodeRunId()));
        row.put("snapshot_id", text(f.snapshotId())); row.put("revision", new OpportunityJson.IntegerValue(f.revision()));
        row.put("native_revision", new OpportunityJson.IntegerValue(f.identity().nativeRevision()));
        row.put("date_raw", new OpportunityJson.IntegerValue(f.identity().dateRaw()));
        row.put("actor_character_id", new OpportunityJson.IntegerValue(f.identity().player()));
        row.put("observed_at", text(frame.observedAt().toString()));
        return DriverJson.encode(new OpportunityJson.Obj(row));
    }
    private static OpportunityJson.Text text(String value) { return new OpportunityJson.Text(value); }
    private static OpportunityJson.IntegerValue integer(long value) { return new OpportunityJson.IntegerValue(BigInteger.valueOf(value)); }
}
