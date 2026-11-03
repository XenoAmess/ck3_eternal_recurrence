package org.xar.ck3.control.application.planning.sway;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.g2.m6.G2M6Contracts;
import org.xar.ck3.control.g2.m6.M6Research;
import org.xar.ck3.control.g2.m6.M6ServiceIntegration;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.application.planning.sway.SwayFormalState;
import org.xar.ck3.control.application.planning.sway.SwayFormalCodec;
import org.xar.ck3.control.application.planning.sway.SwayCanonicalDomain;

/**
 * Read-only assessment entry for the current resolved Sway projection.
 * It does not grant authority, submit actions, or modify the ledger.
 */
public final class SwayCanonicalAssessment234 {
    private SwayCanonicalAssessment234() { }

    public record Export(DomainBodies.Available canonicalOriginal, ProjectionJson derivedResolved,
            M6ServiceIntegration.Result result, boolean pendingPresent) {
        public Export {
            Objects.requireNonNull(canonicalOriginal);
            Objects.requireNonNull(derivedResolved);
            Objects.requireNonNull(result);
        }
    }

    public static Optional<Export> readCurrentResolved(SwayCanonicalDomain domain, ContinuityStorePort.Session borrowed,
            String observedAtUtc, M6Research research) throws IOException {
        Objects.requireNonNull(domain);
        Objects.requireNonNull(borrowed);
        Objects.requireNonNull(research);
        StrictJson.text(observedAtUtc);

        // 1. Load the actual domain state (this performs the requireWriter and readDomain checks)
        SwayCanonicalDomain.Loaded loaded = domain.load(borrowed);
        DomainBodies.Available available = loaded.original();
        SwayFormalState.Ledger ledger = loaded.ledger();

        // 2. Verify the canonical body integrity against the payload reference
        byte[] canonicalBody = available.canonicalBody();
        ExactRef payloadRef = available.reference().payload();
        StrictJson.require(payloadRef.bytes() == canonicalBody.length,
                "canonical body size differs from payload reference");
        StrictJson.require(ActionCodec.sha256(canonicalBody).equals(payloadRef.sha256()),
                "canonical body digest differs from payload reference");

        // 3. Check for a resolved episode
        Optional<SwayFormalState.Episode> resolved = ledger.resolved();
        if (resolved.isEmpty()) {
            return Optional.empty();
        }
        SwayFormalState.Episode episode = resolved.orElseThrow();

        // 4. Compute the derived resolved projection
        ObjectNode originalResolvedNode = SwayFormalCodec.originalResolved(episode);
        byte[] projectionBytes = StrictJson.canonical(originalResolvedNode, M6SourceProducer.MAX_BYTES);
        ProjectionJson derivedResolved = ProjectionJson.object(projectionBytes, M6SourceProducer.MAX_BYTES);

        // 5. Construct the G2Source for the assessment
        String path = payloadRef.path() + "#m6-current-resolved";
        ExactRef projectionRef = new ExactRef(path, projectionBytes.length, ActionCodec.sha256(projectionBytes));
        G2Source source = new G2Source(ledger.machineId(), observedAtUtc, M6SourceProducer.BUILD, projectionRef);

        // 6. Determine the inputs for the terminal source composition
        M6TerminalSourceComposition.Inputs inputs;
        Optional<SwayLifecycle.Terminal> terminal = episode.lifecycle().terminal();
        Optional<SwayLifecycle.Instance> latest = episode.lifecycle().latest();

        if (terminal.isPresent()) {
            SwayLifecycle.Terminal term = terminal.orElseThrow();
            // Use causeProof if present, otherwise the terminal's own proof
            SwayLifecycle.Proof proof = term.causeProof().orElse(term.proof());
            inputs = proof.inputs();
        } else if (latest.isPresent()) {
            SwayLifecycle.Instance inst = latest.orElseThrow();
            inputs = inst.proof().inputs();
        } else {
            inputs = M6TerminalSourceComposition.Inputs.unqueried();
        }

        // 7. Perform the assessment using the existing service integration
        M6ServiceIntegration.Result result = M6SourceProducer.assessResolvedProjection(
                projectionBytes, source, inputs, research);

        // 8. Return the export
        boolean pendingPresent = ledger.pending().isPresent();
        return Optional.of(new Export(available, derivedResolved, result, pendingPresent));
    }
}