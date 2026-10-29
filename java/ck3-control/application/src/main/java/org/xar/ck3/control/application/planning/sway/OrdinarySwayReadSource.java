package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Consumes the installed root query through the one guarded read coordinator. No native client or writer. */
public final class OrdinarySwayReadSource implements OrdinarySwayPolicy.CopiedSource {
    public static final OperationKey ROOT = new OperationKey("query-campaign-root-context-v1");

    /** The original ledger/scheduler reader freezes these inputs for this exact Game/episode/frame. */
    public record BoundInputs(ObservationIdentity before, OrdinarySwayService.Inputs inputs) {
        public BoundInputs { Objects.requireNonNull(before); Objects.requireNonNull(inputs); }
    }
    @FunctionalInterface public interface InputsPort {
        Optional<BoundInputs> load(PlanningRequest request) throws OrdinarySwayService.Unavailable;
    }
    /** The root supplies current registered permissions; this adapter never guesses them from names. */
    @FunctionalInterface public interface CapabilitiesPort {
        OrdinarySwayService.Capabilities current(PlanningRequest request);
    }

    private final PlanningReadPort reads;
    private final SwaySharedRoot root;
    private final InputsPort inputs;
    private final CapabilitiesPort capabilities;

    public OrdinarySwayReadSource(PlanningReadPort reads, ReadContract<Obj> installedRoot,
            InputsPort inputs, CapabilitiesPort capabilities) {
        this(reads,SwaySharedRoot.original(installedRoot),inputs,capabilities);
    }
    public OrdinarySwayReadSource(PlanningReadPort reads,SwaySharedRoot installedRoot,
            InputsPort inputs,CapabilitiesPort capabilities) {
        this.reads = Objects.requireNonNull(reads); root = Objects.requireNonNull(installedRoot);
        require(root.operation().equals(ROOT), "the installed campaign-root definition is required");
        this.inputs = Objects.requireNonNull(inputs); this.capabilities = Objects.requireNonNull(capabilities);
    }

    @Override public OrdinarySwayPolicy.CapturedView collect(PlanningRequest request) {
        Objects.requireNonNull(request);
        var enabled = Objects.requireNonNull(capabilities.current(request));
        OrdinarySwayService.InputPort lazy = () -> Objects.requireNonNull(inputs.load(request)).map(value -> {
            require(value.before().equals(request.before()), "ordinary Sway inputs crossed Game/episode/frame");
            return value.inputs();
        });
        // Retain the original disabled-reader short circuit before both query and storage work.
        if (!enabled.formal() && !enabled.lifecycleReader()) return empty(request, enabled, lazy);
        var query = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), ROOT,
                root.arguments(), request.deadline());
        var result = root.read(reads,query);
        if (result instanceof PlanningReadResult.Unavailable<Obj>) return empty(request, enabled, lazy);
        PlanningReadResult.Known<Obj> known = (PlanningReadResult.Known<Obj>) result;
        require(known.originalReceipt().bytes() > 0, "the guarded root read must retain its original receipt");
        bind(query, root.actualContract(), known.receipt());
        Obj original = originalResult(known.receipt());
        require(original.equals(known.value()), "root decoder projection differs from the original native result");
        return OrdinarySwayPolicy.project(request.before(), original, enabled, lazy);
    }

    private static OrdinarySwayPolicy.CapturedView empty(PlanningRequest request,
            OrdinarySwayService.Capabilities capabilities, OrdinarySwayService.InputPort lazy) {
        // Missing root must not erase the original pending reconciliation or applied-instance observation.
        return new OrdinarySwayPolicy.CapturedView(request.before(), Optional.empty(), capabilities, lazy);
    }

    /** Full envelope and separate result token must agree before any domain field is consumed. */
    public static Obj originalResult(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(),
                "root ACK has no accepted original result");
        Obj frame = DriverJson.object(receipt.original().originalFrame().bytes(), DriverJson.MAX_NATIVE_BYTES);
        require(new Text("command_result").equals(frame.get("type"))
                && new IntegerValue(BigInteger.ONE).equals(frame.get("protocol_version"))
                && new Text(receipt.requestId()).equals(frame.get("request_id"))
                && new Bool(true).equals(frame.get("ok")), "root native command-result identity differs");
        Obj result = object(frame.get("result"), "root native result");
        require(new Text(ROOT.value()).equals(result.get("step")) && new Bool(true).equals(result.get("accepted")),
                "root native operation was not accepted");
        Obj token = DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(), DriverJson.MAX_NATIVE_BYTES);
        require(token.equals(result), "root token differs from the complete original frame");
        return result;
    }

    private static void bind(PlanningReadRequest request, ReadContract<?> contract, PlanningReadReceipt receipt) {
        SwaySharedRoot.requirePublicCapture(receipt);
        require(receipt.request().equals(request) && receipt.contractId().equals(contract.contractId()),
                "root read request or exact registration changed");
        for (PlanningReadGuard guard : List.of(receipt.before(), receipt.after())) {
            GuardEvidence binding = guard.binding();
            require(binding.observed().equals(request.before()) && binding.source().equals(request.source())
                    && binding.sessionId().equals(request.sessionId()) && binding.operation().equals(ROOT)
                    && guard.paused() && guard.mapReady() && guard.playerAlive(),
                    "root read lost the living paused Game/source/session/frame binding");
        }
        require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration())
                && receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId()),
                "root query crossed native custody or full semantic binding");
    }
}
