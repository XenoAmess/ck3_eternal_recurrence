package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Clock;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;

/** Plain offline entry point; does not start Quarkus, a model, HTTP, a worker or Native/Game access. */
public final class CodexSessionDecisionMain {
    private CodexSessionDecisionMain() { }
    public static void main(String[] args) throws Exception {
        byte[] output = FullJsonTree.encode(execute(Clock.systemUTC(), args), CodexSessionDecisionFiles.MAX_RESPONSE_BYTES);
        System.out.write(output); System.out.write(10); System.out.flush();
    }

    /** inspect REQUEST SHA MATERIAL_ROOT [ORIGINAL_REF_JSON]; respond REQUEST SHA MATERIAL_ROOT SELECTION_JSON INSPECTION_JSON. */
    public static ObjectNode execute(Clock clock, String... args) throws java.io.IOException {
        StrictJson.require((args.length == 4 || args.length == 5) && "inspect".equals(args[0]) || args.length == 6 && "respond".equals(args[0]),
                "expected inspect REQUEST SHA MATERIAL_ROOT [ORIGINAL_REF_JSON] or respond REQUEST SHA MATERIAL_ROOT SELECTION_JSON INSPECTION_JSON");
        com.fasterxml.jackson.databind.JsonNode inspection = null;
        ExactRef original = null;
        if ("respond".equals(args[0])) {
            inspection = FullJsonTree.parse(CodexSessionDecisionFiles.readSelectionFile(Path.of(args[5])), CodexSessionDecisionFiles.MAX_RESPONSE_BYTES);
            StrictJson.require("xar.ordinary-codex-session-inspection/v1".equals(StrictJson.text(inspection.get("schema"))), "original inspection required");
            original = org.xar.ck3.control.continuity.writer.WriterContracts.Pin.fromJson(inspection.path("custody").get("original_command")).reference();
        } else if (args.length == 5) original = ExactRef.fromJson(FullJsonTree.parse(
                CodexSessionDecisionFiles.readSelectionFile(Path.of(args[4])), CodexSessionDecisionFiles.MAX_RESPONSE_BYTES));
        var pending = CodexSessionDecisionFiles.readWithOriginalCommand(Path.of(args[1]), args[2], Path.of(args[3]), original, clock);
        if (inspection != null) pending.requireCustody(inspection.get("custody"));
        ObjectNode result = StrictJson.object().put("provider", "codex-session");
        if ("respond".equals(args[0])) {
            var selection = CodexSessionDecisionFiles.Selection.fromJson(FullJsonTree.parse(
                    CodexSessionDecisionFiles.readSelectionFile(Path.of(args[4])), CodexSessionDecisionFiles.MAX_RESPONSE_BYTES));
            var response = CodexSessionDecisionFiles.respond(pending, selection);
            result.put("schema", "xar.ordinary-codex-session-response-published/v1");
            result.set("response", response.toJson());
        } else {
            var row = FullJsonTree.parse(pending.envelopeBytes(), CodexSessionDecisionFiles.MAX_REQUEST_BYTES);
            result.put("schema", "xar.ordinary-codex-session-inspection/v1");
            result.put("request_id", StrictJson.text(row.get("request_id")));
            result.set("request", new ExactRef(pending.requestFile().toString(), pending.envelopeBytes().length, pending.requestSha256()).toJson());
            result.set("payload", row.get("payload")); result.set("original_command", pending.custody().path("original_command").get("ref"));
            result.set("custody", pending.custody());
            result.set("before", row.get("before")); result.put("deadline_utc", pending.deadline().toString());
            result.set("original_source", FullJsonTree.parse(pending.originalCommandBytes(),
                    org.xar.ck3.control.application.action.ActionCodec.MAX_COMMAND_BYTES).get("source"));
        }
        return result;
    }
}
