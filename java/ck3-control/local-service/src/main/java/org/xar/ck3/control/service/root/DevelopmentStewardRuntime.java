package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import java.util.Arrays;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.development.DevelopmentModels;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardResults;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardService;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService.ChangeRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real current-Root candidate producer and closed action factory; no unqualified native action is installed. */
public final class DevelopmentStewardRuntime {
    public record Sources(ExactRef runtime, ExactRef contract, ExactRef results, ExactRef service,
                          DevelopmentStewardResults.SourceEvidence originals) {
        public Sources {
            Objects.requireNonNull(originals);
            for (ExactRef source : List.of(runtime, contract, results, service))
                StrictJson.require(source != null && source.bytes() > 0, "actual selected development producer source required");
        }
    }

    private final RootRuntimeContext context;
    private final ReadContract<DevelopmentModels.Observation> candidates;
    private final Sources sources;

    public DevelopmentStewardRuntime(RootRuntimeContext context,
            ReadContract<DevelopmentModels.Observation> actualInstalledCandidates, Sources sources) throws IOException {
        this.context = Objects.requireNonNull(context);
        this.candidates = Objects.requireNonNull(actualInstalledCandidates);
        this.sources = Objects.requireNonNull(sources);
        context.requireCurrent(context.clock().instant().plusSeconds(1));
        requireInstalled();
    }

    public DevelopmentStewardResults.Preparation prepare(Session same, ChangeRequest input,
            Complete before, Instant deadline) {
        return withFacts(same, input, before, deadline, facts -> DevelopmentStewardResults.prepare(facts, sources.originals()));
    }

    /** Source-bound current backend service behavior; never creates or submits an ActionCommand. */
    public RawJson invoke(Session same, ChangeRequest input, Complete before, Instant deadline) {
        return withFacts(same, input, before, deadline, facts -> {
            DevelopmentStewardService.candidate(facts);
            var archive = context.archive().withSession(same);
            var hello = context.transport().originalHello();
            var transportSession = context.transport().diagnostics().session().orElseThrow();
            StrictJson.require(transportSession.game().equals(before.identity().game())
                    && transportSession.machineId().equals(before.identity().machineId())
                    && transportSession.sessionId().equals(before.sessionId())
                    && transportSession.connectionGeneration().equals(before.connectionGeneration()),
                    "Steward original HELLO crossed actual held transport/source session");
            var capabilities = DevelopmentStewardService.bindCapabilities(facts, hello.packet().value(),
                    archive.readOriginalPacket(facts.original().receipt().before().binding().capabilityEvidence()),
                    archive.readOriginalPacket(facts.original().receipt().after().binding().capabilityEvidence()));
            verifyOriginalSources(sources.originals());
            throw DevelopmentStewardService.currentHeadlessRejection(facts, capabilities, sources.originals());
        });
    }

    @FunctionalInterface private interface FactsWork<T> {
        T apply(DevelopmentStewardResults.SameFrameFacts facts) throws IOException;
    }

    /** Also used in the prior physical snapshot scope; grants no query/action permission. */
    public static void beforeQuery(ChangeRequest input, Complete before) {
        var action = request(input);
        DevelopmentStewardService.beforeQuery(action,
                before.semantic().get("paused") instanceof OpportunityJson.Bool paused && paused.value(),
                before.identity().frame().revision());
    }
    private static DevelopmentStewardAction.Request request(ChangeRequest input) {
        return new DevelopmentStewardAction.Request("steward-dev-" + UUID.randomUUID(),
                input.councillorId(), input.countyTitleId(), input.expectedRevision(), input.replaceExisting());
    }

    private <T> T withFacts(Session same, ChangeRequest input, Complete before, Instant deadline, FactsWork<T> work) {
        Objects.requireNonNull(input); Objects.requireNonNull(before); Objects.requireNonNull(deadline);
        try {
            context.writer().requireSession(same); context.requireCurrent(deadline); requireInstalled();
            verifyOriginalSources(sources.originals());
            var action = request(input);
            beforeQuery(input, before);
            return context.readiness().current(same, before.identity(), deadline, lease -> {
                StrictJson.require(lease.frame().fullBindingSha256().equals(before.fullBindingSha256()),
                        "steward qualification changed the original full Driver/Native frame");
                var actualHello = context.transport().originalHello();
                byte[] leaseHello = context.archive().withSession(same).readOriginalPacket(lease.originalHello());
                var helloIdentity = NativeRequestChronology.PacketIdentity.of(leaseHello);
                StrictJson.require(helloIdentity.bytes() == lease.originalHello().bytes()
                        && helloIdentity.sha256().equals(lease.originalHello().sha256())
                        && Arrays.equals(leaseHello, actualHello.packet().value())
                        && NativeWire.decode(leaseHello) instanceof NativeWire.Hello
                        && actualHello.pid() == before.identity().game().pid()
                        && actualHello.connectionGeneration().equals(before.connectionGeneration()),
                        "Steward query capability lacks the actual same-owner archived original HELLO");
                DevelopmentStewardService.beforeCandidateRead(actualHello, lease.executableSteps());
                var request = new PlanningReadRequest(before.identity(), before.source(), before.sessionId(),
                        candidates.operation(), new OpportunityJson.Obj(java.util.Map.of()), deadline);
                PlanningReadResult<DevelopmentModels.Observation> observed = context.reads().read(same, candidates, request);
                if (!(observed instanceof PlanningReadResult.Known<DevelopmentModels.Observation> known)) {
                    String reason = observed instanceof PlanningReadResult.Unavailable<DevelopmentModels.Observation> missing
                            ? missing.reason() : "unrecognized read result";
                    throw new IOException("actual steward candidate query unavailable: " + reason);
                }
                StrictJson.require(known.receipt().contractId().equals(candidates.contractId())
                        && known.receipt().request().equals(request)
                        && context.archive().withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt()),
                        "steward candidate did not retain its actual installed contract/archived original");
                var facts = DevelopmentStewardResults.bind(action, request, known);
                return context.readiness().current(same, before.identity(), deadline, after -> {
                    StrictJson.require(after.frame().fullBindingSha256().equals(before.fullBindingSha256()),
                            "steward fresh candidate crossed the complete original paused frame");
                    return work.apply(facts);
                });
            });
        } catch (IOException failure) {
            throw new UncheckedIOException("actual same-writer steward candidate/permission qualification unavailable", failure);
        }
    }

    static void verifyOriginalSources(DevelopmentStewardResults.SourceEvidence originals) throws IOException {
        for (ExactRef source : originals.all()) {
            var observed = SharedSourceFiles.observe(Path.of(source.path()));
            StrictJson.require(observed.source().bytes() == source.bytes() && observed.source().sha256().equals(source.sha256()),
                    "Steward actual original source changed; requalify backend service behavior");
            SharedSourceFiles.assertUnchanged(observed);
        }
    }

    private void requireInstalled() {
        StrictJson.require(candidates.operation().value().equals(DevelopmentStewardAction.QUERY_STEP)
                && candidates.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && context.readCatalog().containsIdentity(candidates),
                "identical installed paused steward candidate contract required");
    }
}
