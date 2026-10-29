package org.xar.ck3.control.warbudget;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.warbudget.projection.WarBudgetProjectionCatalog;

/** Test-only persistent pipe to exercise existing synthetic consumers against actual Java results. */
public final class BudgetProbeMain {
    private BudgetProbeMain() { }
    public static void main(String[] arguments) throws IOException {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(
                java.util.List.of(new WarBudgetProjectionCatalog()));
        ByteArrayOutputStream line = new ByteArrayOutputStream(); int next;
        while ((next = System.in.read()) != -1) {
            if (next != '\n') {
                if (line.size() >= StrictJson.INPUT_MAX_BYTES) { throw new IOException("test request line budget exceeded"); }
                line.write(next); continue;
            }
            try {
                ProjectionCall call = new ProjectionCall(
                        new ProjectionCall.Identity("original-budget-consumer", ProjectionOperation.WAR_BUDGET_EVALUATE),
                        ProjectionJson.object(line.toByteArray(), 65_536));
                ProjectionResult result = dispatcher.dispatch(ProjectionWire.encodeCall(call));
                if (result instanceof ProjectionResult.Succeeded succeeded) {
                    System.out.write(succeeded.result().bytes());
                } else {
                    System.out.write("{\"test_transport_status\":\"invalid_contract\"}".getBytes(StandardCharsets.UTF_8));
                }
                System.out.write('\n'); System.out.flush();
            } catch (ContractViolationException error) {
                System.out.write("{\"test_transport_status\":\"invalid_contract\"}\n".getBytes(StandardCharsets.UTF_8));
                System.out.flush();
            }
            line.reset();
        }
        if (line.size() != 0) { throw new IOException("unterminated test request"); }
    }
}
