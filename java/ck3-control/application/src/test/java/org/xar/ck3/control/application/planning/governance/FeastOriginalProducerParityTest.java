package org.xar.ck3.control.application.planning.governance;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Compatibility oracle executes the pinned, untouched original producer body; no Python runtime dependency is installed. */
final class FeastOriginalProducerParityTest {
    private static final String ORIGINAL_SHA = "200e8500ac18bef4a71fa6f885285d344a62ebb28837a54d45efddabf7d9e7e9";
    private static final String ORACLE = """
            import ast, json, pathlib, sys
            source = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig')
            tree = ast.parse(source)
            kept = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_valid_payload'
                    or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCHEMA' for t in n.targets)]
            assert len(kept) == 2
            namespace = {}
            exec(compile(ast.Module(body=kept, type_ignores=[]), str(sys.argv[1]), 'exec'), namespace)
            rows = json.load(sys.stdin)
            result = [namespace['_valid_payload'](row, revision=9, date_raw=100, actor_id=29829) for row in rows]
            json.dump(result, sys.stdout)
            """;

    @Test void privateCouncilNativeFrameAndPublicOuterBindingStayDistinct() {
        var request = OrdinaryGovernanceFactoriesTest.feastRequest(); var role = CouncilSelection.Position.STEWARD;
        Obj original = councilRaw(request, role, 10, 12, 12);
        assertEquals(CouncilSelection.Outcome.REPLACE_REQUIRED, CouncilSelection.choose(CouncilSelection.decode(request, role, original)).outcome());
        Obj payload = object(original.get("council_composition_candidates"), "candidate payload");
        Obj nativeFrame = object(payload.get("snapshot"), "native inner frame");
        Obj wrongPublicFrame = nativeFrame.with("snapshot_id", new Text(request.before().frame().snapshotId()));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role,
                original.with("council_composition_candidates", payload.with("snapshot", wrongPublicFrame))));
        assertThrows(IllegalArgumentException.class, () -> CouncilSelection.decode(request, role, original.with("queried_native_revision", n(10))));
    }

    @Test void fullCurrentDiagnosticProducerAndSharedJavaDecoderAgreeOnRawBoundaryVectors() throws Exception {
        String repository = requiredProperty("xar.repository.root");
        String python = requiredProperty("xar.python");
        Path original = Path.of(repository).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/activity_planner_diag_private_transport.py");
        assertEquals(ORIGINAL_SHA, ActionCodec.sha256(Files.readAllBytes(original)), "original oracle source drift; preserve and recapture its producer");
        var request = OrdinaryGovernanceFactoriesTest.feastRequest(); Obj absent = OrdinaryGovernanceFactoriesTest.diagnostic(request);
        Obj stage = absent.with("planner_status", new Text("observed")).with("planner_present", new Bool(true))
                .with("planning_stage", n(2)).with("host_view_activity_key", new Text("activity_feast"));
        List<Value> vectors = new ArrayList<>(List.of(absent, stage.with("planning_stage", n(1)), stage, stage.with("planning_stage", n(5)),
                stage.with("host_view_activity_key", new Text("activity_hunt")), stage.with("planning_stage", new Bool(true)),
                stage.with("planning_stage", new DecimalValue("2.0")), stage.with("planning_stage", new Text("2")),
                absent.with("snapshot_revision", n(10)), absent.with("unrecognized", new Bool(true)), new Obj(java.util.Map.of()),
                stage.with("host_view_activity_key", new Text("activity_宴会")), absent.with("raw_pointer_fields_persisted", new Bool(true)),
                stage.with("widget_visible", new Bool(true)), absent.with("planner_present", new Bool(true))));
        List<Value> javaAccepted = new ArrayList<>();
        for (Value vector : vectors) {
            boolean accepted;
            try { FeastObservationCollector.decodePlanner(request, object(vector, "raw original vector")); accepted = true; }
            catch (IllegalArgumentException rejected) { accepted = false; }
            javaAccepted.add(new Bool(accepted));
        }
        ProcessBuilder invocation = new ProcessBuilder(python, "-B", "-c", ORACLE, original.toString());
        invocation.redirectErrorStream(true); invocation.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = invocation.start();
        try {
            process.getOutputStream().write(encode(new Arr(vectors))); process.getOutputStream().close();
            assertTrue(process.waitFor(20, TimeUnit.SECONDS), "original producer oracle timed out");
            byte[] result = process.getInputStream().readAllBytes();
            assertEquals(0, process.exitValue(), new String(result, StandardCharsets.UTF_8));
            assertEquals(new Arr(javaAccepted), OpportunityJson.parse(result), "actual original producer/raw-token parity");
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(5, TimeUnit.SECONDS)); }
        }
    }
    private static String requiredProperty(String key) {
        String value = System.getProperty(key); assertNotNull(value, "required original producer compatibility input: " + key);
        assertFalse(value.isBlank(), "empty original producer compatibility input: " + key); return value;
    }
}
