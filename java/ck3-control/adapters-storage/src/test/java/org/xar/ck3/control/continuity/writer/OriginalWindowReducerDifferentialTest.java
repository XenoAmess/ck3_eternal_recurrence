package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Real retained Python producer -> Java reducer, using valid JSON domain and matching error branches. */
class OriginalWindowReducerDifferentialTest {
    @Test void actualOriginalReducerAndJavaAgreeAcrossFourKindsAndSerialization() throws Exception {
        ObjectNode input = StrictJson.object(); ArrayNode cases = input.putArray("cases");
        for (String kind : new String[]{"repair_required", "attach_verified", "settled_batch", "automatic_recovery"}) {
            ObjectNode row = cases.addObject(); row.set("previous", WriterFixture.state()); row.put("kind", kind);
            ObjectNode details = row.putObject("details"); details.put("machine_id", WriterFixture.MACHINE);
            details.put("evidence_id", "original-" + kind); details.put("source", "native-original");
            details.put("completed_cycles", 2); details.put("date_raw", 1024); details.put("reason", "actual interrupted test frame");
            ObjectNode frame = details.putObject("frame"); frame.put("date_raw", 1024); frame.put("actor_character_id", 29829);
            frame.put("episode_run_id", "robert-episode"); frame.put("snapshot_id", "native:1"); frame.put("revision", 1); frame.put("native_revision", 1);
        }
        // Older completed observation remains a no-op; split monotonic coordinates are rejected.
        ObjectNode older = cases.addObject(); older.set("previous", WriterFixture.state()); older.put("kind", "settled_batch");
        ObjectNode oldDetails = older.putObject("details"); oldDetails.put("evidence_id", "old"); oldDetails.put("source", "native-original"); oldDetails.put("completed_cycles", 0); oldDetails.put("date_raw", 976);
        ObjectNode conflict = cases.addObject(); conflict.set("previous", WriterFixture.state()); conflict.put("kind", "settled_batch");
        ObjectNode bad = conflict.putObject("details"); bad.put("evidence_id", "bad"); bad.put("source", "native-original"); bad.put("completed_cycles", 0); bad.put("date_raw", 1024);
        ObjectNode initial = cases.addObject(); initial.putNull("previous"); initial.put("kind", "repair_required");
        initial.set("details", cases.get(0).get("details").deepCopy());
        ObjectNode game = ((ObjectNode)initial.get("details")).putObject("game"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
        String script = "import sys,json\nsys.path.insert(0,sys.argv[1])\nfrom tools.g2_saved_campaign.root_continuity_window import transition\nv=json.load(sys.stdin);out=[]\nfor row in v['cases']:\n try:out.append({'ok':transition(row['previous'],row['kind'],row['details'])})\n except (ValueError,KeyError,TypeError):out.append({'rejected':True})\nprint(json.dumps({'results':out},sort_keys=True,ensure_ascii=False,separators=(',',':')))\n";
        Process child = new ProcessBuilder(WindowsWriterInteropTest.python(), "-B", "-X", "utf8", "-c", script,
                WindowsWriterInteropTest.repository().toString()).redirectErrorStream(true).start();
        try {
            child.getOutputStream().write(ContinuityJson.canonical(input)); child.getOutputStream().close();
            assertTrue(child.waitFor(15, TimeUnit.SECONDS)); byte[] actual = child.getInputStream().readAllBytes(); assertEquals(0, child.exitValue());
            JsonNode results = WriterContracts.object(actual).get("results"); assertEquals(cases.size(), results.size());
            for (int i = 0; i < cases.size(); i++) {
                ObjectNode row = (ObjectNode)cases.get(i); JsonNode result = results.get(i);
                ObjectNode previous = row.get("previous").isNull() ? null : (ObjectNode)row.get("previous");
                if (result.has("rejected")) assertThrows(ContractViolationException.class,
                        () -> OriginalWindowReducer.reduce(previous, row.get("kind").textValue(), (ObjectNode)row.get("details")));
                else assertTrue(ContinuityJson.same(result.get("ok"), OriginalWindowReducer.reduce(previous,
                        row.get("kind").textValue(), (ObjectNode)row.get("details"))), "original reducer vector " + i);
            }
        } finally { child.destroyForcibly(); }
    }
    @Test void integerAliasMissingAndNullContractsReject() {
        for (String raw : new String[]{"true", "1.0", "null"}) {
            ObjectNode details = StrictJson.object(); details.put("evidence_id", "wrong-type"); details.put("source", "native");
            details.put("date_raw", 1024); details.set("completed_cycles", StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8), 16));
            assertThrows(ContractViolationException.class, () -> OriginalWindowReducer.reduce(WriterFixture.state(), "settled_batch", details));
        }
        assertThrows(ContractViolationException.class, () -> new WriterContracts.Request("settled_batch", "{}".getBytes(StandardCharsets.UTF_8), java.util.List.of()));
    }
}
