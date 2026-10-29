package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.nio.file.Path;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardAction;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardResults;
import org.xar.ck3.control.nativebridge.capabilities.governance.DevelopmentStewardService;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePublicService.ChangeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Source-bound current unsupported service behavior, with native mutation qualification kept separate. */
public final class RootStewardDevelopmentPublicAction {
    private RootStewardDevelopmentPublicAction() { }

    /** Construction is pre-Core; qualification resolves the current physical Core/writer at call time. */
    public static Factory factory(RootPublicHandlerProductsFactory.Context context) throws IOException {
        Objects.requireNonNull(context);
        DevelopmentStewardResults.SourceEvidence originals = originalSources(context);
        context.source(RootStewardDevelopmentPublicAction.class);
        var sources = new DevelopmentStewardRuntime.Sources(context.source(DevelopmentStewardRuntime.class),
                context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DevelopmentStewardAction.class),
                context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DevelopmentStewardResults.class),
                context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, DevelopmentStewardService.class), originals);
        return new Factory(context, sources);
    }

    /** Derives exact sibling producers from the existing configured original driver, then reads every actual file. */
    private static DevelopmentStewardResults.SourceEvidence originalSources(RootPublicHandlerProductsFactory.Context context) throws IOException {
        ExactRef driver = context.inputs().source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER);
        Path path = Path.of(driver.path()).toAbsolutePath().normalize();
        StrictJson.require(path.getFileName().toString().equals("native_driver.py")
                && path.getParent().getFileName().toString().equals("bridge"), "actual original bridge driver path required");
        ExactRef observedDriver = source(path);
        StrictJson.require(observedDriver.bytes() == driver.bytes() && observedDriver.sha256().equals(driver.sha256()),
                "Steward current configured original driver changed");
        Path bridge = path.getParent();
        Path project = bridge.getParent().getParent().getParent();
        return new DevelopmentStewardResults.SourceEvidence(source(bridge.resolve("service.py")), observedDriver,
                source(bridge.resolve("steward_develop_county_action_contract.py")),
                source(project.resolve("native_bridge/src/steward_develop_county_action_v1.cpp")),
                source(project.resolve("native_bridge/research/steward_develop_county_action_v1_abi.json")));
    }
    private static ExactRef source(Path path) throws IOException {
        var witness = SharedSourceFiles.observe(path);
        SharedSourceFiles.assertUnchanged(witness);
        var actual = witness.source();
        return new ExactRef(actual.path(), actual.bytes(), actual.sha256());
    }

    public static final class Factory {
        private final RootPublicHandlerProductsFactory.Context context;
        private final DevelopmentStewardRuntime.Sources sources;
        private Factory(RootPublicHandlerProductsFactory.Context context, DevelopmentStewardRuntime.Sources sources) {
            this.context = context; this.sources = sources;
        }

        public DevelopmentStewardRuntime.Sources sources() { return sources; }

        /** A real source-bound public service product for the current unsupported headless branch. */
        public RawJson invoke(ChangeRequest request) throws InterruptedException {
            Objects.requireNonNull(request);
            Instant deadline = context.clock().instant().plus(context.observationTimeout());
            try {
                return context.withCurrent(root -> {
                    DevelopmentStewardRuntime.verifyOriginalSources(sources.originals());
                    // This physical DATA scope ends before ordinary query readiness.
                    // It preserves original paused/revision error priority without
                    // treating its frame as permission for the later query.
                    root.withPublicSnapshot(deadline, new RootApplicationSession.SnapshotWork<Void>() {
                        @Override public Void ordinary(DriverObservationAssembler.Complete frame,
                                DriverSnapshotFacts.Known known, Session same) {
                            DevelopmentStewardRuntime.beforeQuery(request, frame);
                            return null;
                        }
                        @Override public Void terminal(DriverObservationAssembler.FullSnapshot frame,
                                LifecycleIdentity identity, DriverSnapshotFacts.Known known, Session same) throws IOException {
                            throw new IOException("actual physical snapshot has no ordinary steward frame");
                        }
                    });
                    return root.withPublicObservation(deadline, (frame, driver, same) -> {
                    var installed = context.installed(root);
                    var runtime = new DevelopmentStewardRuntime(installed.context(),
                            installed.nativeGovernance().publicReads().development(), sources);
                    return runtime.invoke(same, request, frame, deadline);
                    });
                });
            } catch (DevelopmentStewardService.Failure failure) {
                var fault = failure.fault();
                throw new PublicServiceFailure(PublicServiceFailure.Kind.exact(fault.kind().pythonName()),
                        fault.message(), fault.candidateOriginal());
            } catch (IOException failure) {
                throw new UncheckedIOException("actual Root steward service unavailable", failure);
            }
        }

        public DevelopmentStewardResults.Preparation qualify(ChangeRequest request) throws InterruptedException {
            Objects.requireNonNull(request);
            Instant deadline = context.clock().instant().plus(context.observationTimeout());
            try {
                return context.withCurrent(root -> root.withPublicObservation(deadline, (frame, driver, same) -> {
                    var installed = context.installed(root);
                    var runtime = new DevelopmentStewardRuntime(installed.context(),
                            installed.nativeGovernance().publicReads().development(), sources);
                    return runtime.prepare(same, request, frame, deadline);
                }));
            } catch (IOException failure) {
                throw new UncheckedIOException("actual Root steward factory qualification unavailable", failure);
            }
        }

        public String nativeQualificationGap() {
            return "The original headless driver has no typed executor and its source-pinned 1.19 command ABI is uncertified; "
                    + "current .4 native material is not action legality. The complete source-bound unsupported service "
                    + "branch grants no mutation permission, ActionBinding or actual postcondition observer.";
        }
    }
}
