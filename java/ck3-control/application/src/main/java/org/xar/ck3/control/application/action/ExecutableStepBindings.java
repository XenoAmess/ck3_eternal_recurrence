package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Read-only view of the composition root's actual primitive and read registrations.
 * The sole implementation must seal real callable bindings; declarations and hello never populate it.
 */
public sealed interface ExecutableStepBindings permits RootExecutableBindings {
    enum Kind { ACTION, READ, COMPOSITE }
    record InstalledStep(OperationKey operation, Kind kind, ReadContract.GuardMode guardMode,
            Optional<String> requiredCapability, ExactRef implementationSource, ExactRef decoderSource) {
        public InstalledStep {
            Objects.requireNonNull(operation); Objects.requireNonNull(kind); Objects.requireNonNull(guardMode);
            Objects.requireNonNull(requiredCapability); requiredCapability.ifPresent(StrictJson::text);
            StrictJson.require(guardMode != ReadContract.GuardMode.STATUS_ONLY || kind == Kind.READ
                    && operation.value().equals(PhysicalStatusIdentity.OPERATION)
                    && requiredCapability.filter(PhysicalStatusIdentity.CAPABILITY::equals).isPresent(),
                    "physical status mode cannot register an action/composite or another native operation");
            NativeStepDiscriminator.requireRegistration(operation, kind, requiredCapability);
            Objects.requireNonNull(implementationSource); Objects.requireNonNull(decoderSource);
            StrictJson.require(implementationSource.bytes() > 0 && decoderSource.bytes() > 0,
                    "actual implementation and request/result decoder source references required");
        }
        public NativeStepDiscriminator.WireIdentity nativeIdentity() { return NativeStepDiscriminator.identity(operation); }
    }
    /** Installed source metadata only. It grants no origin, family membership, preparation or dispatch permission. */
    record PublicPlanningStep(InstalledStep descriptor, Optional<ExactRef> archivedVerifierSource) {
        public PublicPlanningStep {
            Objects.requireNonNull(descriptor); Objects.requireNonNull(archivedVerifierSource);
            archivedVerifierSource.ifPresent(source -> StrictJson.require(source.bytes() > 0, "actual archived verifier source required"));
            StrictJson.require(descriptor.kind() == Kind.READ || archivedVerifierSource.isPresent(),
                    "public planning action/composite metadata requires its actual installed verifier source");
        }
    }
    boolean frozen();
    List<InstalledStep> installed();
    /** Pure DATA projection of already installed definitions/strict family grammars; never calls resolve or issue. */
    Optional<PublicPlanningStep> describeForPublicPlanning(OperationKey operation);
    default Optional<InstalledStep> resolve(OperationKey operation) {
        Objects.requireNonNull(operation);
        if (!frozen()) return Optional.empty();
        var matches = installed().stream().filter(binding -> binding.operation().equals(operation)).distinct().toList();
        StrictJson.require(matches.size() <= 1, "operation-only lookup is ambiguous; actual origin is required");
        return matches.stream().findFirst();
    }
    /** Exact origin selection is descriptor lookup, never observation or dispatch qualification. */
    default Optional<InstalledStep> resolve(OperationKey operation, CommandOrigin actual) {
        return resolve(operation, originMode(Objects.requireNonNull(actual)));
    }
    /** For an actual source-owned issuer before its identity is minted; no permission is issued here. */
    default Optional<InstalledStep> resolve(OperationKey operation, ReadContract.GuardMode actualMode) {
        Objects.requireNonNull(operation); Objects.requireNonNull(actualMode);
        if (!frozen()) return Optional.empty();
        var matches = installed().stream().filter(binding -> binding.operation().equals(operation)
                && binding.guardMode() == actualMode).distinct().toList();
        StrictJson.require(matches.size() <= 1, "multiple actual bindings claim the same operation and origin");
        return matches.stream().findFirst();
    }
    static ReadContract.GuardMode originMode(CommandOrigin actual) {
        return switch (Objects.requireNonNull(actual)) {
            case CommandOrigin.Gameplay ignored -> ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP;
            case CommandOrigin.Frontend ignored -> ReadContract.GuardMode.FRONTEND_SESSION;
            case CommandOrigin.LifecycleTerminal ignored -> ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION;
            case CommandOrigin.Reconciliation ignored -> ReadContract.GuardMode.RECONCILIATION_OBSERVATION;
            case CommandOrigin.PhysicalStatusOnly ignored -> ReadContract.GuardMode.STATUS_ONLY;
        };
    }
    default boolean containsExact(OperationKey operation) {
        return resolve(operation).isPresent();
    }
    default boolean supportsCapability(String capability) {
        StrictJson.text(capability);
        return frozen() && installed().stream().anyMatch(binding -> binding.requiredCapability().filter(capability::equals).isPresent());
    }
}


