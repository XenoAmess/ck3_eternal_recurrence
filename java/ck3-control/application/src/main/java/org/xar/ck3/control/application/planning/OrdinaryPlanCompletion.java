package org.xar.ck3.control.application.planning;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * The one application completion boundary for actual domain plan publications.
 * Implementations own typed aggregate decoding and the sole writer session.
 * The planner and loop never infer a ledger write from an annotation or ACK.
 */
public interface OrdinaryPlanCompletion {
    PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned);
    ExecutionDisposition afterExecution(ActionReceipt actual);

    sealed interface PlanningDisposition permits Unchanged, AwaitingOutcome, Published, Blocked, CheckpointRequired { }
    sealed interface ExecutionDisposition permits Unchanged, Published, Blocked { }

    /** Root holds the original writer Session through capture, pure planning and publication after all Driver freezes exit. */
    interface PlanningScope extends OrdinaryPlanCompletion {
        <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException,InterruptedException;
    }
    @FunctionalInterface interface ScopeWork<T> { T run() throws IOException,InterruptedException; }
    record ScopeResult<T>(T value,Optional<Published> readPublication) {
        public ScopeResult {Objects.requireNonNull(value);Objects.requireNonNull(readPublication);}
    }

    record Unchanged(String reason) implements PlanningDisposition, ExecutionDisposition {
        public Unchanged { StrictJson.text(reason); }
    }

    /** Retained exact command only: no no-action publication is postponed behind a fabricated action. */
    record AwaitingOutcome(ActionCommand command) implements PlanningDisposition {
        public AwaitingOutcome { Objects.requireNonNull(command); }
    }

    /** The actual domain publisher verifies this completed original focus and its source; this record alone grants no SAVE. */
    record CheckpointRequired(ActionReceipt original,List<ExactRef> evidence) implements PlanningDisposition {
        public CheckpointRequired {
            Objects.requireNonNull(original);evidence=List.copyOf(evidence);
            StrictJson.require(original.settled()&&original.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,
                    "checkpoint requirement needs its actual confirmed original action");
            StrictJson.require(!evidence.isEmpty(),"checkpoint requirement needs actual source evidence");
            evidence.forEach(ref->StrictJson.require(Objects.requireNonNull(ref).bytes()>0,"actual checkpoint request evidence required"));
        }
    }

    /** A changed authoritative head requires a new planning observation before another dispatch. */
    record Published(WriterContracts.Head predecessor, WriterContracts.Receipt actual)
            implements PlanningDisposition, ExecutionDisposition {
        public Published {
            Objects.requireNonNull(predecessor); Objects.requireNonNull(actual);
            StrictJson.require(actual.disposition() != WriterContracts.Disposition.NO_CHANGE,
                    "unchanged publication cannot claim a changed authoritative head");
            StrictJson.require(!predecessor.digest().equals(ContinuityJson.digest(actual.head().toJson())),
                    "published disposition requires the actual changed authoritative head");
        }
    }

    record Blocked(String reason, List<ExactRef> evidence) implements PlanningDisposition, ExecutionDisposition {
        public Blocked {
            StrictJson.text(reason); evidence = List.copyOf(evidence);
            evidence.forEach(Objects::requireNonNull);
        }
    }
}
