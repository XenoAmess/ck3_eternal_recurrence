package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.china_career.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacareer.ChinaCareerContract.*;

/** Six original public names, same actual per-Game registration and one original Root writer/read coordinator. */
public final class RootChinaCareerPublicProducts {
    /** Pure ordinary registration from the actual implementation metadata. */
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata) {
        Objects.requireNonNull(metadata);
        return new Prepared(metadata.implementation(ChinaCareerService.class),metadata.implementation(ChinaCareerCodec.class));
    }
    private RootChinaCareerPublicProducts() { }

    public static final class Prepared {
        private final ChinaCareerService.Registration registration;
        private final ExactRef decoder;
        private RootApplicationAssembly.Core core;
        private static final class Attempt { private Installed installed; }
        private final java.util.IdentityHashMap<RootRuntimeContext, Attempt> installs = new java.util.IdentityHashMap<>();
        public Prepared(ExactRef actualServiceSource, ExactRef actualCodecSource) {
            registration = new ChinaCareerService.Registration(Objects.requireNonNull(actualServiceSource),Objects.requireNonNull(actualCodecSource));
            decoder = Objects.requireNonNull(actualCodecSource);
        }
        public List<DomainBodies.Registration> domainRegistrations() { return List.of(); }
        public List<NativePrivateActionPermission> privatePermissions() { return List.of(); }
        public synchronized void bindCore(RootApplicationAssembly.Core same) {
            StrictJson.require(core == null || core == same, "China career prepared registration cannot change its actual Core");
            core = Objects.requireNonNull(same);
        }
        public synchronized Installed install(RootRuntimeContext same) throws IOException {
            StrictJson.require(core != null && same.core() == core,
                    "China career install requires its original prepared Core");
            same.requireCurrent(same.clock().instant().plusSeconds(1));
            Attempt prior = installs.get(same);
            if (prior != null) {
                if (prior.installed == null) throw new IOException("prior China career install attempt failed; no partial replay");
                return prior.installed;
            }
            StrictJson.require(installs.size() < 64, "bounded actual physical China career installation contexts required");
            Attempt attempt = new Attempt(); installs.put(same, attempt);
            List<RootReadContractCatalog.InstalledRead> reads = registration.all().stream()
                    .map(read -> new RootReadContractCatalog.InstalledRead(read, decoder)).toList();
            var installation = new RootDomainInstallation("public-china-career-six", List.of(), reads, List.of(),
                    List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), Set.of(),
                    List.of(), List.of(), List.of(), List.of(), List.of());
            attempt.installed = new Installed(installation, new ChinaCareerService(registration));
            return attempt.installed;
        }
    }
    public record Installed(RootDomainInstallation installation, ChinaCareerService service) {
        public Installed {
            Objects.requireNonNull(installation); Objects.requireNonNull(service);
            StrictJson.require(installation.reads().size() == Kind.values().length
                    && service.registration().all().stream().allMatch(read -> installation.reads().stream().anyMatch(actual -> actual.contract() == read)),
                    "all six identical China career contracts must be actual installed reads");
        }
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings unchangedRegistry) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(unchangedRegistry);
        ExactRef source = context.source(RootChinaCareerPublicProducts.class);
        for (Class<?> type : List.of(ChinaCareerContract.class, ChinaCareerCodec.class, ChinaCareerService.class,
                CareerJson.class, CareerGroups.class, CareerProvenance.class, CareerReadiness.class,
                OwnerCareerFrames.class, OwnerGroups.class, CollectiveGroups.class, CollectiveWorkforceFrame.class,
                NormalExitGroups.class, NormalExitWorkforceFrame.class, GovernanceGroups.class, ManagerGovernanceFrame.class, ManagerSelectorFrame.class))
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, type);
        var handler = new Handler(context);
        return new RootPublicHandlerProductsFactory.Contribution(bindings(handler::query, source), List.of(), List.of());
    }
    @FunctionalInterface public interface QueryPort {
        RawJson query(Request request) throws InterruptedException;
    }
    /** The production descriptor/decoder/producer/encoder seam is shared with the original-source compatibility tests. */
    public static List<McpExecutableDirectory.DirectBinding<?, ?>> bindings(QueryPort actual, ExactRef source) {
        Objects.requireNonNull(actual); Objects.requireNonNull(source);
        return Arrays.stream(Kind.values()).<McpExecutableDirectory.DirectBinding<?, ?>>map(kind -> new McpExecutableDirectory.DirectBinding<Request, RawJson>(kind.publicName(),
                PublicMcpBindings.Kind.DRIVER_DIRECT, Request.class, RawJson.class, actual::query,
                call -> ChinaCareerCodec.decodeRequest(kind, required(call.arguments())), PublicMcpDirectory.CallResult::fromBusinessJson,
                new PublicRoutes.Target(Handler.class.getName(), "query", source))).toList();
    }
    private static RawJson required(PublicMcpDirectory.Arguments arguments) {
        StrictJson.require(arguments.presence() == PublicMcpDirectory.Presence.VALUE,
                "China career requires its exact original named argument object; missing and null are distinct");
        return arguments.original().orElseThrow();
    }
    public static final class Handler {
        private final RootPublicHandlerProductsFactory.Context context;
        private Handler(RootPublicHandlerProductsFactory.Context context) { this.context = context; }
        public RawJson query(Request request) throws InterruptedException {
            Instant deadline = context.clock().instant().plus(context.observationTimeout());
            try {
                return context.withCurrent(root -> {
                    root.withPublicSnapshot(deadline, new RootApplicationSession.SnapshotWork<Void>() {
                        @Override public Void ordinary(DriverObservationAssembler.Complete actual,
                                DriverSnapshotFacts.Known known, Session same) {
                            ChinaCareerService.precheck(request, flag(actual, "paused"), flag(actual, "map_ready"), actual.identity().frame().revision());
                            return null;
                        }
                        @Override public Void terminal(DriverObservationAssembler.FullSnapshot actual,
                                LifecycleIdentity identity, DriverSnapshotFacts.Known known, Session same) throws IOException {
                            throw new IOException("actual physical snapshot has no ordinary China career player binding");
                        }
                    });
                    return root.withPublicObservation(deadline, (before, driver, same) -> {
                        var catalog = context.installed(root); var runtime = catalog.context();
                        ChinaCareerService service = catalog.additionalDomains().chinaCareer().service();
                        runtime.writer().requireSession(same);
                        ReadContract<NativeObservation> contract = service.registration().contract(request.kind());
                        StrictJson.require(runtime.readCatalog().containsIdentity(contract), "same actual China career read registration is not installed");
                        return runtime.readiness().current(same, before.identity(), deadline, lease -> {
                            StrictJson.require(lease.frame().fullBindingSha256().equals(before.fullBindingSha256()), "China career source frame changed before query");
                            var hello = runtime.transport().originalHello();
                            byte[] archived = runtime.archive().withSession(same).readOriginalPacket(lease.originalHello());
                            var digest = NativeRequestChronology.PacketIdentity.of(archived);
                            var transportSession = runtime.transport().diagnostics().session().orElseThrow(()->new IOException("China career original transport session unavailable"));
                            StrictJson.require(digest.bytes() == lease.originalHello().bytes()
                                    && digest.sha256().equals(lease.originalHello().sha256())
                                    && Arrays.equals(archived, hello.packet().value()) && hello.pid() == before.identity().game().pid()
                                    && transportSession.game().equals(before.identity().game())
                                    && transportSession.sessionId().equals(before.sessionId())
                                    && hello.connectionGeneration().equals(before.connectionGeneration()),
                                    "China career capabilities lack actual same-owner original archived HELLO");
                            Frame frame = new Frame(before.identity().frame().snapshotId(), before.identity().frame().revision(),
                                    before.identity().frame().identity().nativeRevision(), before.connectionGeneration(),
                                    before.identity().frame().identity().dateRaw().intValueExact(), before.identity().frame().identity().player().intValueExact(),
                                    flag(before, "paused"), flag(before, "map_ready"), before.identity().frame().episodeRunId(), hello, lease.originalHello());
                            var nativeRequest = new PlanningReadRequest(before.identity(), before.source(), before.sessionId(), contract.operation(),
                                    ChinaCareerService.arguments(request, frame), deadline);
                            Response result = service.query(request, frame, nativeRequest, (actualContract, actualRequest) -> {
                                var observed = runtime.reads().read(same, actualContract, actualRequest);
                                if (observed instanceof PlanningReadResult.Known<NativeObservation> known) {
                                    var archive = runtime.archive().withSession(same);
                                    StrictJson.require(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt()), "China career original read archive changed");
                                    for (var guard : List.of(known.receipt().before(), known.receipt().after())) {
                                        byte[] original = archive.readOriginalPacket(guard.binding().capabilityEvidence());
                                        var identity = NativeRequestChronology.PacketIdentity.of(original);
                                        StrictJson.require(identity.bytes() == guard.binding().capabilityEvidence().bytes()
                                                && identity.sha256().equals(guard.binding().capabilityEvidence().sha256())
                                                && Arrays.equals(original, archived), "China career read guard lost original held HELLO");
                                    }
                                }
                                return observed;
                            });
                            return runtime.readiness().current(same, before.identity(), deadline, after -> {
                                StrictJson.require(after.frame().fullBindingSha256().equals(before.fullBindingSha256()), "China career query crossed complete original frame");
                                return ChinaCareerCodec.encodeResponse(result);
                            });
                        });
                    });
                });
            } catch (Failure failure) {
                Fault fault = failure.fault();
                throw new PublicServiceFailure(PublicServiceFailure.Kind.exact(fault.pythonName()), fault.originalMessage(), fault.originalRead());
            } catch (IOException failure) { throw new UncheckedIOException("actual current Root China career query unavailable", failure); }
        }
    }
    private static boolean flag(DriverObservationAssembler.Complete frame, String field) {
        return frame.semantic().get(field) instanceof OpportunityJson.Bool value && value.value();
    }
}
