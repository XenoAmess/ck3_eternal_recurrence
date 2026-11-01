package org.xar.ck3.control.application.planning.events;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.math.BigInteger;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

public final class NativeWindowDiagnostic220Probe {
    private static int checks = 0;
    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }

    private static ProposalLifecycle.ObservationIdentity identity() {
        var source = new org.xar.ck3.control.g2.common.G2Source("probe-machine", "2026-10-23T18:00:00Z", "1.20.0.4", new org.xar.ck3.control.contracts.ExactRef("D:/probe/source.json", 1, "a".repeat(64)));
        var generation = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var frame = new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(1), BigInteger.valueOf(100));
        var proposalFrame = new JointBudgetSelector.ProposalFrame(frame, "native-1", BigInteger.valueOf(1), "episode-1");
        return new ProposalLifecycle.ObservationIdentity(source.machineId(), generation, proposalFrame, 1);
    }

    private static void complete(OpportunityJson.Obj plan, NativeWindowDiagnostic.Source source) {
        var body = OpportunityJson.object(plan.get("unhandled_native_window_diagnostic"), "diagnostic body");
        check(plan.get("selected_step") == OpportunityJson.Nil.INSTANCE, "top selection null");
        check(body.get("selection") == OpportunityJson.Nil.INSTANCE, "diagnostic selection null");
        check(body.get("schema").equals(new OpportunityJson.Text("xar.unhandled-native-window-diagnostic/v1")), "schema intact");
        check(body.get("kind").equals(new OpportunityJson.Text("unhandled_event")), "kind intact");
        check(body.get("diagnostic_reason").equals(new OpportunityJson.Text(source.reason())), "reason intact");
        check(body.get("offline_followup_required").equals(new OpportunityJson.Bool(true)), "follow-up flag intact");
        check(body.get("snapshot").equals(source.snapshot()), "complete snapshot including opaque values intact");
        check(body.get("retained_history").equals(new OpportunityJson.Arr(source.retainedHistory())), "complete history intact");
        check(body.get("context").equals(source.context().orElse(OpportunityJson.Nil.INSTANCE)), "complete context intact");
        check(body.get("original_plan").equals(source.originalPlan().<OpportunityJson.Value>map(v -> v).orElse(OpportunityJson.Nil.INSTANCE)), "complete original plan intact");
        check(body.get("origin").equals(DriverJson.fromNode(org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(source.origin()))), "complete origin intact");
        check(body.get("current_event_instance_id").equals(new OpportunityJson.IntegerValue(BigInteger.valueOf(42))), "current event id intact");
        check(body.get("event_definition_key").equals(new OpportunityJson.Text("def-key")), "definition key intact");
        check(source.snapshot().get("opaque").equals(new OpportunityJson.IntegerValue(new BigInteger("99999999999999999999"))), "opaque integer exact");
        if (source.snapshot().members().containsKey("neg_zero"))
            check(OpportunityJson.object(body.get("snapshot"), "result snapshot").get("neg_zero").equals(new OpportunityJson.DecimalValue("-0.0")), "negative-zero token exact");
        check(source.snapshot().get("unicode").equals(new OpportunityJson.Text("\u00e9")), "Unicode exact");
        check(source.snapshot().get("null_field") == OpportunityJson.Nil.INSTANCE, "snapshot null exact");
    }

    public static void main(String[] args) throws Exception {
        var origin = identity();
        var snapshot = new OpportunityJson.Obj(Map.of(
            "active_event", new OpportunityJson.Obj(Map.of("instance_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(42)))),
            "opaque", new OpportunityJson.IntegerValue(new BigInteger("99999999999999999999")),
            "unicode", new OpportunityJson.Text("\u00e9"),
            "null_field", OpportunityJson.Nil.INSTANCE
        ));
        List<OpportunityJson.Value> history = List.of(new OpportunityJson.Text("h1"), new OpportunityJson.IntegerValue(BigInteger.ONE));
        Optional<OpportunityJson.Value> context = Optional.of(new OpportunityJson.Obj(Map.of("event_definition_key", new OpportunityJson.Text("def-key"))));
        var originalPlan = Optional.of(new OpportunityJson.Obj(Map.of("step", new OpportunityJson.Text("s1"))));
        var reason = "probe-reason";
        var source = new NativeWindowDiagnostic.Source(origin, snapshot, history, context, originalPlan, reason);

        var planOpt = NativeWindowDiagnostic.plan(source);
        check(planOpt.isPresent(), "small plan present");
        var plan = planOpt.get();
        var planNode = DriverJson.toNode(plan);
        var encodedPlan = DriverJson.encode(plan);
        var canonicalPlan = StrictJson.canonical(planNode, ActionCommand.MAX_ARGUMENT_BYTES);
        check(java.util.Arrays.equals(encodedPlan, canonicalPlan), "canonical ordering preserved");

        var body = planNode.get("unhandled_native_window_diagnostic");
        check(body.get("kind").asText().equals("unhandled_event"), "kind event");
        check(body.get("diagnostic_reason").asText().equals(reason), "reason match");
        check(body.get("selection").isNull(), "selection null");
        check(planNode.get("selected_step").isNull(), "selected_step null");
        check(body.get("current_event_instance_id").asLong() == 42, "event id 42");
        check(body.get("event_definition_key").asText().equals("def-key"), "def key");
        check(body.get("retained_history").size() == 2, "history size 2");

        complete(plan, source);
        var largeSnapshot = snapshot.with("padding", new OpportunityJson.Arr(java.util.Collections.<OpportunityJson.Value>nCopies(275, new OpportunityJson.Text("a".repeat(4000)))));
        var largeSource = new NativeWindowDiagnostic.Source(origin, largeSnapshot, history, context, originalPlan, reason);
        // Deliberately uncaught: the frozen old producer must fail here at its real canonical budget.
        var largePlan = NativeWindowDiagnostic.plan(largeSource).orElseThrow();
        complete(largePlan, largeSource);
        int largeBytes = DriverJson.encode(largePlan).length;
        check(largeBytes > ActionCommand.MAX_ARGUMENT_BYTES, "actual large plan exceeds 1MiB");

        var completeSnapshot = snapshot.with("padding", new OpportunityJson.Text("c".repeat(1_100_000)))
                .with("neg_zero", new OpportunityJson.DecimalValue("-0.0"));
        var completeSource = new NativeWindowDiagnostic.Source(origin, completeSnapshot, history, context, originalPlan, reason);
        var completePlan = NativeWindowDiagnostic.plan(completeSource).orElseThrow();
        complete(completePlan, completeSource);
        check(DriverJson.encode(completePlan).length > ActionCommand.MAX_ARGUMENT_BYTES, "decimal full-material branch also exceeds 1MiB");

        var middleSnapshot = snapshot.with("padding", new OpportunityJson.Arr(java.util.Collections.<OpportunityJson.Value>nCopies(50, new OpportunityJson.Text("b".repeat(4000)))));
        var middleSource = new NativeWindowDiagnostic.Source(origin, middleSnapshot, history, context, originalPlan, reason);
        var middlePlan = NativeWindowDiagnostic.plan(middleSource).orElseThrow();
        complete(middlePlan, middleSource);
        int middleBytes = DriverJson.encode(middlePlan).length;
        check(middleBytes > 131072 && middleBytes < ActionCommand.MAX_ARGUMENT_BYTES, "actual middle plan crosses only the 128KiB parse boundary");

        var nonForegroundSnapshot = new OpportunityJson.Obj(Map.of("other", new OpportunityJson.Text("x")));
        var nonForegroundSource = new NativeWindowDiagnostic.Source(origin, nonForegroundSnapshot, history, context, originalPlan, reason);
        check(NativeWindowDiagnostic.plan(nonForegroundSource).isEmpty(), "nonforeground empty");

        System.out.println("PASS checks=" + checks + " smallBytes=" + encodedPlan.length + " largeBytes=" + largeBytes + " middleBytes=" + middleBytes);
    }
}