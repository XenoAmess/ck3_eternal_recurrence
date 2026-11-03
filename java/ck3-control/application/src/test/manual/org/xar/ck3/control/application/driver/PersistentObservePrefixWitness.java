package org.xar.ck3.control.application.driver;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;

/**
 * First-run software witness; see the recorded Native results.
 * Two real public observe prefix cases. No memo-positive, world or authority claim.
 */
public final class PersistentObservePrefixWitness {
    private PersistentObservePrefixWitness() { }

    public static void main(String[] args) {
        RawJson sourceBody = new RawJson(DriverJson.encode(new Obj(Map.of("processed", new Arr(List.of())))));
        byte[] sourceBytes = sourceBody.bytes();
        ExactRef source = new ExactRef("software/cooldown-prefix/source", sourceBytes.length, DriverJson.sha256(sourceBytes));

        PrefixArchive unused = new PrefixArchive(source);
        var empty = DriverPersistentPlanningState.observe(null, known(new Obj(Map.of())), List.of(),
                null, null, null, unused);
        check(empty.isEmpty(), "PFX1 absent state returns empty before frame access");
        check(unused.materialLoads == 0, "PFX1 absent state performs no material callback");

        Obj auxiliary = new Obj(Map.of(DriverPersistentPlanningState.COOLDOWN_STATE, Nil.INSTANCE,
                DriverPersistentPlanningState.COOLDOWN_SOURCE, DriverObservationEvidenceReader.reference(source)));
        PrefixArchive failing = new PrefixArchive(source);
        try {
            DriverPersistentPlanningState.observe(null, known(auxiliary), List.of(), null, null, null, failing);
            throw new AssertionError("PFX2 expected actual archive callback failure");
        } catch (RuntimeException actual) {
            if (actual != failing.marker) {
                throw new AssertionError("PFX2 archive marker must precede invalid-frame access", actual);
            }
        }
        check(failing.materialLoads == 1, "PFX2 exactly one real loadMaterial callback");
        System.out.println("PASS cases=2 observe_prefix_only=true memo_positive=false authority=false");
    }

    private static DriverSnapshotFacts.Known known(Obj auxiliary) {
        var driverSession = new DriverStateSnapshot.Session("software-cooldown-prefix", 123,
                BigInteger.valueOf(7), "software-episode");
        var nil = new DriverStateSnapshot.NullValue();
        var driver = new DriverStateSnapshot.Complete(driverSession, List.of(), nil, nil, nil, nil, nil, nil, nil);
        byte[] original = driver.encode();
        String digest = DriverJson.sha256(original);
        var game = GameGeneration.fromJson(DriverJson.toNode(new Obj(Map.of(
                "pid", new IntegerValue(BigInteger.valueOf(123)), "creation_filetime", new Text("1")))));
        var stamp = new DriverSnapshotFacts.Stamp(0, 0, game, driverSession.episodeRunId(), digest);
        var basis = new ExactRef("software/cooldown-prefix/driver", original.length, digest);
        return new DriverSnapshotFacts.Known(driver, stamp, basis, List.of(), auxiliary, Optional.empty(), Optional.empty());
    }

    private static void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
    }

    /** Public DATA callback failure, not a real Native/archive/writer authority implementation. */
    private static final class PrefixArchive implements ActionPorts.OutcomeArchive {
        private final ExactRef expected;
        private final RuntimeException marker = new IllegalStateException("software observe archive prefix marker");
        private int materialLoads;

        PrefixArchive(ExactRef expected) { this.expected = expected; }

        @Override public RawJson loadMaterial(ExactRef original) {
            materialLoads++;
            check(expected.equals(original), "actual processed source metadata requested");
            throw marker;
        }

        private AssertionError unexpected(String method) {
            return new AssertionError("unexpected public archive callback " + method);
        }

        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { throw unexpected("preserve"); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { throw unexpected("load"); }
        @Override public ExactRef preserveRequest(NativeRequest original) { throw unexpected("preserveRequest"); }
        @Override public NativeRequest loadRequest(ExactRef original) { throw unexpected("loadRequest"); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { throw unexpected("referenceOf"); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { throw unexpected("requestReferenceOf"); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { throw unexpected("preserveRead"); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { throw unexpected("loadRead"); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { throw unexpected("readReferenceOf"); }
        @Override public ExactRef preserveRecord(ActionRecord original) { throw unexpected("preserveRecord"); }
        @Override public ActionRecord loadRecord(ExactRef original) { throw unexpected("loadRecord"); }
        @Override public ExactRef recordReferenceOf(ActionRecord original) { throw unexpected("recordReferenceOf"); }
        @Override public ExactRef preserveReceipt(ActionReceipt original) { throw unexpected("preserveReceipt"); }
        @Override public ActionReceipt loadReceipt(ExactRef original) { throw unexpected("loadReceipt"); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt original) { throw unexpected("receiptReferenceOf"); }
        @Override public ExactRef preserveMaterial(RawJson original) { throw unexpected("preserveMaterial"); }
        @Override public ExactRef materialReferenceOf(RawJson original) { throw unexpected("materialReferenceOf"); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { throw unexpected("preserveNativeFrame"); }
        @Override public byte[] loadNativeFrame(ExactRef original) { throw unexpected("loadNativeFrame"); }
    }
}
