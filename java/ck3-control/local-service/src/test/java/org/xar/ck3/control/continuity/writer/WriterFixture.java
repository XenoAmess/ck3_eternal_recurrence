package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

final class WriterFixture {
    static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    final Layout layout;
    final Path source;
    final ContinuityWriter writer;
    final StorageWriteGuardTestSupport storage;
    WriterFixture(Path root) throws IOException {
        this(root,67_108_864);
    }
    WriterFixture(Path root,long maximumChargedBytes) throws IOException {
        Files.createDirectories(root);
        Path snapshot = root.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = root.resolve("anchor.json");
        byte[] state = ContinuityJson.canonical(state()); Files.write(snapshot, state); Files.write(anchor, state);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]);
        Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        source = root.resolve("reviewed-source.txt"); Files.writeString(source, "reviewed fixture source v1");
        layout = new Layout(snapshot, LedgerFiles.read(anchor, 65_536).pin().reference(), MACHINE);
        storage = StorageWriteGuardTestSupport.create(layout.snapshot().getParent(),layout.lock(),maximumChargedBytes);
        writer = new ContinuityWriter(layout, List.of(LedgerFiles.read(source, 65_536).pin().reference()), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, Request request) {
                return ContinuityJson.digest(request.detailsObject());
            }
            @Override public ContinuityState reduce(ContinuityState predecessor, Request request) {
                return OriginalWindowReducer.reduce(predecessor, request);
            }
        }, StorageWriteGuardTestSupport.forLayout(layout));
    }
    static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10_958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000);
        row.put("target_date_raw", 1000 + 10_958 * 24); row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1);
        row.put("manual_repair_count", 1); row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        ObjectNode game = row.putObject("game_binding"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
        row.putNull("latest_binding");
        ObjectNode pending = row.putObject("pending_cycle"); pending.put("stage", "auto_unsettled"); pending.put("auto_sequence", 11558);
        row.put("NEXT", 11559); return row;
    }
    static Request settled(String evidence, long date, long cycles) {
        ObjectNode details = StrictJson.object(); details.put("machine_id", MACHINE); details.put("evidence_id", evidence);
        details.put("source", "original-actual-pair"); details.put("date_raw", date); details.put("completed_cycles", cycles);
        return new Request("settled_batch", ContinuityJson.canonical(details), List.of());
    }
}
