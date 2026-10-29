package org.xar.ck3.control.application.routecontact;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;

/** Executes pinned, unchanged Python AST through the centrally selected interpreter; it never imports or modifies production Python. */
final class RouteContactOriginalProducerTest {
    private static final String DRIVER_SHA = "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603";
    private static final String WAR_SHA = "b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937";
    private static final String UNIT_SHA = "0de76f3bf10ae24d3202177bb527bcb3ec903432a38af64f55e08c95698cab4e";
    private static final String SCRIPT = """
            import ast,copy,json,pathlib,sys,__future__
            driver,war,unit=map(pathlib.Path,sys.argv[1:4])
            namespace={'copy':copy}
            exec(compile(unit.read_text(encoding='utf-8'),str(unit),'exec'),namespace)
            sources=[(driver,{'_unavoidable_contact_transition_postcondition','_predicted_contact_boundary_postcondition',
                '_army_by_id','_army_in_active_combat','_army_retreating','_canonical_remaining_route','_positive_native_id',
                '_same_paused_contact_refresh_owner','_newer_native_contact_refresh_frame',
                '_retarget_timeline_step_result','_date_raw','_war_progress_summary'}),
                (war,{'enemy_armies_from_wars','deduplicate_armies'})]
            for path,wanted in sources:
                selected=[node for node in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(node,ast.FunctionDef) and node.name in wanted]
                assert {node.name for node in selected}==wanted
                exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),str(path),'exec',
                    flags=__future__.annotations.compiler_flag),namespace)
            request=json.load(sys.stdin)
            operation=request['operation']
            if operation=='observed':
                value=namespace['_unavoidable_contact_transition_postcondition'](request['starting'],request['ending'],
                    proof=request['proof'],strong_only=request['strict'])
            elif operation=='predicted':
                value=namespace['_predicted_contact_boundary_postcondition'](request['starting'],request['ending'],proof=request['proof'])
            elif operation=='refresh':
                value=namespace['_same_paused_contact_refresh_owner'](request['starting'],request['ending'])
            elif operation=='retarget':
                value=namespace['_retarget_timeline_step_result'](request['result'],request['ending'])
            else: raise ValueError('unknown operation')
            print(json.dumps({'value':value},ensure_ascii=False,separators=(',',':')))
            """;
    @Test void actualOriginalObservedTransitionsMatchAllStrongAndWeakJavaBranches() throws IOException, InterruptedException {
        Frame start = RouteContactProofsTest.starting(); Proof proof = RouteContactPostconditionsTest.proof(false);
        List<Frame> endings = new ArrayList<>();
        endings.add(RouteContactPostconditionsTest.after(start.ownArmies(), start.hostileArmies()));
        endings.add(RouteContactPostconditionsTest.after(start.ownArmies(), List.of(RouteContactProofsTest.army(8, 10, null, List.of()))));
        endings.add(RouteContactPostconditionsTest.after(List.of(new Army(0, true, 10, Optional.of(20), List.of(20), Optional.of("combat"), Optional.of(2), true, false)), start.hostileArmies()));
        endings.add(RouteContactPostconditionsTest.after(List.of(new Army(0, true, 10, Optional.of(20), List.of(20), Optional.of("retreating"), Optional.of(6), false, true)), start.hostileArmies()));
        endings.add(RouteContactPostconditionsTest.after(List.of(), start.hostileArmies()));
        endings.add(RouteContactPostconditionsTest.after(start.ownArmies(), List.of(RouteContactProofsTest.army(8, 99, 88, List.of(88)))));
        Frame base = endings.getFirst();
        endings.add(new Frame(base.owner(), base.snapshotId(), base.revision(), base.nativeRevision(), base.dateRaw(), true, true, base.speed(), false, true,
                base.activeEvent(), base.pendingInteraction(), base.modal(), List.of(2), base.ownArmies(), base.hostileArmies()));
        endings.add(new Frame(base.owner(), base.snapshotId(), base.revision(), base.nativeRevision(), base.dateRaw(), true, true, base.speed(), true, false,
                base.activeEvent(), base.pendingInteraction(), base.modal(), base.activeWarIds(), base.ownArmies(), base.hostileArmies()));
        for (boolean strict : List.of(false, true)) for (Frame end : endings) {
            Value original = call(request("observed", start, end, proof, strict));
            Optional<Transition> actual = RouteContactPostconditions.observed(start, end, strict ? RouteContactPostconditionsTest.proof(true) : proof);
            assertEquals(original != Nil.INSTANCE, actual.isPresent());
            if (actual.isPresent()) {
                Obj row = object(original, "original transition"); Transition transition = actual.orElseThrow();
                assertEquals(text(row.get("postcondition"), "postcondition"), transition.kind().wire());
                assertEquals(integer(row.get("starting_date_raw"), "starting_date_raw").intValueExact(), transition.startingDateRaw());
                assertEquals(integer(row.get("ending_date_raw"), "ending_date_raw").intValueExact(), transition.endingDateRaw());
                assertEquals(transition.kind() == TransitionKind.ACTIVE_COMBAT_OBSERVED, transition.contactObserved());
            }
        }
    }
    @Test void actualOriginalClosedEndpointAndStrictRefusalMatchCompleteSerializedMarkers() throws IOException, InterruptedException {
        Frame start = RouteContactProofsTest.starting(); Frame end = RouteContactPostconditionsTest.after(start.ownArmies(), start.hostileArmies());
        for (boolean strict : List.of(false, true)) {
            Proof proof = RouteContactPostconditionsTest.proof(strict); Value original = call(request("predicted", start, end, proof, strict));
            Value actual = RouteContactPostconditions.predictedEndpoint(start, end, proof).<Value>map(RouteContactEvidenceCodec::transition).orElse(Nil.INSTANCE);
            assertEquals(original, actual);
        }
    }
    @Test void actualOriginalSameDateRefreshRequiresBothRevisionsAndStableOwner() throws IOException, InterruptedException {
        Frame start = RouteContactProofsTest.frame(2, 124, RouteContactProofsTest.starting().ownArmies(), RouteContactProofsTest.starting().hostileArmies());
        List<Frame> endings = List.of(RouteContactProofsTest.frame(3, 124, start.ownArmies(), start.hostileArmies()),
                RouteContactProofsTest.frame(3, 148, start.ownArmies(), start.hostileArmies()),
                new Frame(start.owner(), "public-new", start.revision().add(java.math.BigInteger.ONE), start.nativeRevision(), 124, true, true, 3, false, true,
                    Nil.INSTANCE, Nil.INSTANCE, Nil.INSTANCE, start.activeWarIds(), start.ownArmies(), start.hostileArmies()));
        for (Frame end : endings) assertEquals(bool(call(request("refresh", start, end, RouteContactPostconditionsTest.proof(false), false)), "original refresh"),
                RouteContactPostconditions.samePausedRefreshOwner(start, end));
    }
    @Test void actualOriginalRetargetPreservesTheCompleteClockAndChangesOnlyOriginalEndingFields() throws IOException, InterruptedException {
        var fixture = new RouteContactCompositeTest.Fixture(); var parent = RouteContactCompositeTest.command(false);
        var proof = fixture.handler().project(parent);
        // Explicit formatter DATA: an empty original war slice avoids granting any Native/Root qualification.
        var clockEnd = withoutWars(fixture.end); var publication = withoutWars(fixture.refreshed);
        var clock = RouteContactEvidenceTest.reportedExact(parent, fixture.start, clockEnd, 1);
        var child = RouteContactCompositeTest.pauseReceipt(parent, clockEnd, false);
        var refresh = new RouteContactComposite.ContactRefresh(clockEnd, Optional.of(child), Optional.of(publication), Optional.of("already_paused"));
        var completion = new RouteContactComposite.Completion(fixture.start, publication, proof, Optional.empty(), clock, List.of(child), Optional.of(refresh));
        Obj actual = RouteContactEvidenceCodec.result(new RouteContactEvidenceCodec.Completed(parent, completion));
        Obj originalClock = DriverJson.object(clock.originalReport().orElseThrow().bytes(), org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES);
        var actions = new ArrayList<Value>(array(originalClock.get("actions"), "clock actions"));
        Obj originalPause = DriverJson.object(child.ack().orElseThrow().originalResultToken().orElseThrow().bytes(), org.xar.ck3.control.application.action.RawJson.MAXIMUM_BYTES);
        actions.add(new Obj(Map.of("step", new Text("pause-map"), "result", originalPause)));
        originalClock = originalClock.with("actions", new Arr(actions));
        Obj expected = object(call(new Obj(Map.of("operation", new Text("retarget"), "result", originalClock, "ending", publication.semantic()))), "original retarget");
        for (var field : expected.members().entrySet()) assertEquals(field.getValue(), actual.get(field.getKey()), field.getKey());
        assertEquals(new Arr(actions), actual.get("actions"));
        assertEquals(new Text("already_paused"), object(actual.get("contact_refresh"), "refresh").get("ack_status"));
    }
    private static org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame withoutWars(org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame frame) {
        return new org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame(frame.identity(), frame.source(), frame.sessionId(),
                frame.semantic().with("active_wars", new Arr(List.of())), frame.provenance(), frame.observedAt(), frame.originalEvidence());
    }
    private static Obj request(String operation, Frame start, Frame end, Proof proof, boolean strict) {
        Obj horizon = object(RouteContactEvidenceCodec.queryResult(proof.query()).get("route_contact_horizon"), "horizon");
        Obj originalProof = new Obj(Map.of("proof_kind", new Text("unavoidable_current_province_contact"), "subject_army_id", RouteContactCompositeTest.n(proof.subjectId()),
                "target_province_id", RouteContactCompositeTest.n(proof.targetProvinceId()), "hostile_army_ids", horizon.get("hostile_army_ids"),
                "contact_horizon", horizon, "strict_endpoint_followup", new Bool(strict)));
        return new Obj(Map.of("operation", new Text(operation), "starting", semantic(start),
                "ending", semantic(end), "proof", originalProof, "strict", new Bool(strict)));
    }
    private static Obj semantic(Frame frame) {
        Arr enemies = new Arr(frame.hostileArmies().stream().map(RouteContactCompositeTest::armyJson).map(Value.class::cast).toList());
        return RouteContactCompositeTest.raw(frame).semantic().with("active_wars", new Arr(frame.activeWarIds().stream()
                .map(id -> (Value)new Obj(Map.of("war_id", RouteContactCompositeTest.n(id), "enemy_armies", enemies))).toList()));
    }
    private static Value call(Obj request) throws IOException, InterruptedException {
        String python = required("xar.native.producer.python"); Path driver = Path.of(required("xar.native.producer.source"));
        assertEquals(DRIVER_SHA, required("xar.native.producer.sha256"), "central original producer pin differs"); check(driver, DRIVER_SHA);
        Path root = Path.of(required("xar.repository.root")); Path war = root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py");
        Path unit = root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py"); check(war, WAR_SHA); check(unit, UNIT_SHA);
        ProcessBuilder command = new ProcessBuilder(List.of(python, "-I", "-B", "-c", SCRIPT, driver.toString(), war.toString(), unit.toString()));
        command.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process child = command.start();
        try {
            try (var input = child.getOutputStream()) { input.write(DriverJson.encode(request)); }
            if (!child.waitFor(Duration.ofSeconds(30).toMillis(), TimeUnit.MILLISECONDS)) { child.destroyForcibly(); throw new AssertionError("original route producer exceeded finite deadline"); }
            byte[] output = child.getInputStream().readAllBytes(), error = child.getErrorStream().readAllBytes();
            assertEquals(0, child.exitValue(), () -> new String(error, StandardCharsets.UTF_8));
            assertTrue(output.length > 0 && output.length <= 1024 * 1024, "bounded original route producer output required");
            return DriverJson.object(output, 1024 * 1024).get("value");
        } finally { if (child.isAlive()) child.destroyForcibly(); }
    }
    private static void check(Path path, String sha256) throws IOException { assertEquals(sha256, ActionCodec.sha256(Files.readAllBytes(path)), "actual original producer source drifted: " + path); }
    private static String required(String key) { String value = System.getProperty(key); assertTrue(value != null && !value.isBlank(), "original route producer NOT RUN: missing " + key); return value; }
}
