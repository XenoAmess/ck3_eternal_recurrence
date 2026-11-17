package org.xar.ck3.acceptance;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.acceptance.CasePhaseHandoff.*;

final class CasePhaseHandoffTest {
    @TempDir Path temporary;
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String MACHINE="test-machine", RUN=MACHINE+"--product--R0001", HASH="a".repeat(64);
    private Pin write(Path path, Object value) throws Exception {
        byte[] bytes=JSON.writeValueAsBytes(value);Files.createDirectories(path.getParent());Files.write(path,bytes);
        return new Pin(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
    }
    private record Fixture(Path live,Request request,Pin requestPin,ObjectNode report) {}
    private Fixture fixture() throws Exception {
        Path live=temporary.resolve(RUN);Files.createDirectories(live.resolve("controls"));Files.createDirectories(live.resolve("case-output"));
        ObjectNode context=JSON.createObjectNode().put("run_id",RUN).put("run_dir",live.toString());
        context.putObject("frozen_argv").put("sha256",HASH);
        Pin cp=write(live.resolve("root-context.json"),context);
        ObjectNode definition=JSON.createObjectNode();
        var phases=definition.putArray("gui_phases");
        phases.addObject().put("id","p2").putArray("requirements").add("actual");
        phases.addObject().put("id","p3").putArray("requirements").add("next");
        Pin dp=write(temporary.resolve("case.json"),definition);
        ObjectNode accepted=JSON.createObjectNode().put("run_id",RUN).put("machine_id",MACHINE).put("reviewer","/root");
        accepted.putObject("assertions").put("actual",true);write(live.resolve("case-output/p2-accepted.json"),accepted);
        ObjectNode report=JSON.createObjectNode().put("status","RUNNING").put("phase","hold").put("hold_until_utc_estimated",2000000000);
        report.putObject("readiness").putObject("managed_campaign_run_binding").put("run_id",RUN).put("frozen_argv_sha256",HASH);
        report.putArray("steps").addObject().put("id","controller-day").put("ok",true).put("finished_at","now");
        write(live.resolve("native-report.json"),report);
        ObjectNode control=JSON.createObjectNode();control.putArray("steps").addObject().put("id","controller-day");
        write(live.resolve("controls/control.json"),control);
        Request request=new Request(1,MACHINE,"b".repeat(40),RUN,cp,dp,"p2","p3","2000000000",1);
        Pin rp=write(temporary.resolve("request.json"),request);
        return new Fixture(live,request,rp,report);
    }
    private Result inspect(Fixture f) throws Exception {
        return CasePhaseHandoff.inspect(f.request,f.requestPin,Instant.ofEpochSecond(1999990000));
    }
    private void awaiting(Fixture f) throws Exception {
        ObjectNode n=JSON.createObjectNode().put("run_id",RUN).put("operator_reviewer","/root").put("original_hold_deadline",2000000000);
        n.putArray("required_assertions").add("next");write(f.live.resolve("case-output/p3-awaiting.json"),n);
    }
    @Test void acceptedPreviousAloneKeepsControllerOwnership() throws Exception {
        Fixture f=fixture();assertEquals(Decision.CONTROLLER_OWNS,inspect(f).decision());
    }
    @Test void nextAwaitingAndCompletedOriginalControlGrantRoot() throws Exception {
        Fixture f=fixture();awaiting(f);Result r=inspect(f);
        assertEquals(Decision.ROOT_OWNS_NEXT_CHECKPOINT,r.decision());assertFalse(r.sourceCapacityOrGameAdmissionGranted());
    }
    @Test void publishedButNotYetAppendedControlPreventsRootRace() throws Exception {
        Fixture f=fixture();awaiting(f);ObjectNode n=JSON.createObjectNode();
        n.putArray("steps").addObject().put("id","new-controller-day");write(f.live.resolve("controls/new.json"),n);
        assertEquals(Decision.CONTROLLER_OWNS,inspect(f).decision());
    }
    @Test void inFlightReportRowPreventsRootRace() throws Exception {
        Fixture f=fixture();awaiting(f);f.report.withArray("steps").addObject().put("id","new-controller-day");
        write(f.live.resolve("native-report.json"),f.report);assertEquals(Decision.CONTROLLER_OWNS,inspect(f).decision());
    }
    @Test void hostFailureIsTerminalEvenWhenOldAcceptedExists() throws Exception {
        Fixture f=fixture();awaiting(f);f.report.put("error","Original host controls are still in flight");
        write(f.live.resolve("native-report.json"),f.report);assertEquals(Decision.TERMINAL_OR_INVALID,inspect(f).decision());
    }
    @Test void consumedNextPhaseCannotBeReentered() throws Exception {
        Fixture f=fixture();awaiting(f);write(f.live.resolve("case-output/p3-root-result.json"),JSON.createObjectNode());
        assertEquals(Decision.TERMINAL_OR_INVALID,inspect(f).decision());
    }
    @Test void anotherRunOrChangedBudgetNeverGrants() throws Exception {
        Fixture f=fixture();awaiting(f);f.report.path("readiness").path("managed_campaign_run_binding");
        ((ObjectNode)f.report.path("readiness").path("managed_campaign_run_binding")).put("run_id",RUN+"other");
        write(f.live.resolve("native-report.json"),f.report);assertEquals(Decision.TERMINAL_OR_INVALID,inspect(f).decision());
        f.report.put("hold_until_utc_estimated",2000000001);write(f.live.resolve("native-report.json"),f.report);
        assertEquals(Decision.TERMINAL_OR_INVALID,inspect(f).decision());
    }
    @Test void preservesOriginalQuitReserve() throws Exception {
        Fixture f=fixture();assertThrows(Exception.class,()->CasePhaseHandoff.inspect(f.request,f.requestPin,Instant.ofEpochSecond(1999999820)));
    }
    @Test void strictRequestRejectsBooleanFloatingAndWrongFieldPins() throws Exception {
        Fixture f=fixture();assertEquals(f.request,readRequest(f.requestPin));
        ObjectNode n=(ObjectNode)JSON.valueToTree(f.request);
        n.put("timeoutSeconds",true);assertThrows(Exception.class,()->readRequest(write(temporary.resolve("bool.json"),n)));
        n.put("timeoutSeconds",1.0);assertThrows(Exception.class,()->readRequest(write(temporary.resolve("float.json"),n)));
        n.put("timeoutSeconds",1);((ObjectNode)n.path("runContext")).put("bytes",1.0);
        assertThrows(Exception.class,()->readRequest(write(temporary.resolve("pinfloat.json"),n)));
    }
    @Test void changedPinnedProducerInputIsRefused() throws Exception {
        Fixture f=fixture();Files.writeString(Path.of(f.request.runContext().path()),"{}");
        assertThrows(Exception.class,()->inspect(f));
    }
}

