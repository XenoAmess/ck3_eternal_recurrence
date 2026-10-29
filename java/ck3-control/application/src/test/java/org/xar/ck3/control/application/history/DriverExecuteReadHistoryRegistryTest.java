package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;

/** Original operation-role DATA only. No native, actual installed contract, receipt or writer authority is fabricated. */
final class DriverExecuteReadHistoryRegistryTest {
    @Test void originalCaseAndCareerCommandsKeepEncodedCommandDifferentFromFixedReportStep() {
        for(String[] vector:List.of(new String[]{"ai-owned-case-snapshot","12-34-6131"},new String[]{"b1-cycle-snapshot","6131"},
                new String[]{"b2-pip-snapshot","12-6131"},new String[]{"case-snapshot","b1-34-0-6131"},
                new String[]{"compensation-af5-snapshot","12-6131"},new String[]{"incident-snapshot","12-x-6131"},
                new String[]{"projects-metrics-postcondition","12-34-6131"},new String[]{"promotion-compensation-postcondition","12-6131"},
                new String[]{"result-case-snapshot","12-6131"},new String[]{"scoreboard-state","a1-b:c"},
                new String[]{"career-hc-workforce-postcondition","12-6131"},new String[]{"manager-governance-snapshot","34-12-6131"},
                new String[]{"manager-subordinate-selector","6131"},new String[]{"workforce-collective-snapshot","12-6131"},
                new String[]{"workforce-normal-exit-snapshot","12-6131"},new String[]{"workforce-owner-snapshot","12-6131"})) {
            OperationKey base=base(vector[0]),encoded=new OperationKey(base.value()+"-"+vector[1]);Obj numeric=report(base);
            var actual=DriverExecuteReadHistoryRegistry.requireRow(base,encoded,numeric);
            assertEquals(base,actual.logicalOperation());assertEquals(DriverExecuteReadHistoryRegistry.ReportStepRule.FIXED_LOGICAL,actual.reportStepRule());
            assertNotEquals(base,encoded);assertEquals(new Text(base.value()),numeric.get("step"));
            assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(base,encoded,numeric.with("step",new Text(encoded.value()))));
        }
        assertEquals(16,DriverExecuteReadHistoryRegistry.entries().size());
    }
    @Test void unrelatedOperationsAndMalformedOriginalArgumentEncodingsAreRejectedRatherThanAliased() {
        OperationKey logical=base("case-snapshot");
        for(String bad:List.of("b2-34-0-6131","b1-0-0-6131","b1-34-00-6131","b1-34-2147483648-6131","b1-34-0-6A","b1-34-0-6","b1-34-0-ff",
                "b1-34-0-2d","b1-34-0-6131-extra","b1-34-0-"+"61".repeat(65)))
            assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(logical,new OperationKey(logical.value()+"-"+bad),report(logical)));
        var projects=base("projects-metrics-postcondition");
        assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(projects,new OperationKey(projects.value()+"-12-12-6131"),report(projects)));
        var incident=base("incident-snapshot");
        assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(incident,new OperationKey(incident.value()+"-12-q-6131"),report(incident)));
        var unknown=base("future-unregistered-query");
        assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(unknown,new OperationKey(unknown.value()+"-6131"),report(unknown)));
        assertThrows(IllegalArgumentException.class,()->DriverExecuteReadHistoryRegistry.requireRow(logical,new OperationKey(logical.value()),report(logical)));
    }
    @Test void completeProjectionAndPublicNumbersPreserveBothOperationRolesWithoutForcingEquality() {
        OperationKey logical=base("scoreboard-state"),original=new OperationKey(logical.value()+"-nonce-1");
        Obj numeric=report(logical).with("snapshot_revision",new IntegerValue(new BigInteger("18446744073709551615")));
        Obj exposed=numeric.with("snapshot_revision",new Text("18446744073709551615"));
        PublicNumbers roles=PublicNumbers.fromResults(raw(numeric),raw(exposed));
        var projection=new ExecuteProjection(logical,original,raw(numeric),roles,List.of(source()));
        assertEquals(Kind.PUBLIC_EXECUTE_QUERY,projection.kind());assertEquals(original,projection.originalCommand());
        assertEquals(DriverExecuteReadHistoryRegistry.Entry.CASES_SCOREBOARD,DriverExecuteReadHistoryRegistry.requireRow(logical,original,numeric));
        PublicNumbers retained=PublicNumbers.fromJson(OpportunityJson.parse(OpportunityJson.encode(roles.toJson())));
        assertEquals(exposed,retained.toPublic(numeric));assertEquals(numeric,retained.fromPublic(exposed));
        assertEquals(numeric,DriverJson.object(projection.fullResult().bytes(),RawJson.MAXIMUM_BYTES));
        assertThrows(IllegalArgumentException.class,()->new ExecuteProjection(logical,original,raw(numeric),new PublicNumbers(List.of()),List.of(source())));
        assertThrows(IllegalArgumentException.class,()->new ExecuteProjection(logical,original,raw(numeric),roles,List.of()));
        assertThrows(IllegalArgumentException.class,()->new Projection(Kind.PUBLIC_EXECUTE_QUERY,raw(numeric),roles,List.of(source())));
    }
    private static OperationKey base(String suffix){return new OperationKey("query-zhongguo-"+suffix+"-v1");}
    private static Obj report(OperationKey operation){return new Obj(Map.of("step",new Text(operation.value()),"accepted",new Bool(true),"status",new Text("completed")));}
    private static RawJson raw(Obj value){return new RawJson(OpportunityJson.encode(value));}
    private static ExactRef source(){return new ExactRef("data-only-owning-source",1,"1".repeat(64));}
}
