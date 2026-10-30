package org.xar.ck3.control.events.vanilla;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

/** Pure option-mapping leaf, shared by registered choice and variant matching. */
public final class VanillaOptionProjection {
    private VanillaOptionProjection() { }

    public enum RegistryState { AVAILABLE, SOURCE_ANALYZED_NO_OCCURRENCE_CONTRACT, NOT_REGISTERED }
    public enum Status { PROJECTION_READY, BLOCKED, NOT_REGISTERED }

    public record SourceAnchor(String relativePath, String registrySha256, String indexedSha256) {
        public SourceAnchor {
            requireText(relativePath, "relative_path");
            if (!relativePath.startsWith("events/") || relativePath.contains("..") || relativePath.contains("\\")) {
                throw new IllegalArgumentException("relative_path must identify an event source");
            }
            requireDigest(registrySha256);
            requireDigest(indexedSha256);
        }
    }

    public record RegistryBinding(String eventDefinitionKey, String ck3Build, String ck3ExeSha256,
                                  RegistryState registryState, List<SourceAnchor> sourceAnchors) {
        public RegistryBinding {
            requireText(eventDefinitionKey, "event_definition_key");
            requireText(ck3Build, "ck3_build");
            requireDigest(ck3ExeSha256);
            Objects.requireNonNull(registryState, "registryState");
            sourceAnchors = List.copyOf(sourceAnchors);
            if (sourceAnchors.size() > 32) throw new IllegalArgumentException("too many source anchors");
            if (sourceAnchors.stream().map(SourceAnchor::relativePath).distinct().count() != sourceAnchors.size()) {
                throw new IllegalArgumentException("duplicate source path");
            }
        }
    }

    public record OptionContract(int optionCount, List<Integer> nativeOptionIndices,
                                 int selectedNativeOptionIndex, int selectedOptionNumber,
                                 List<Integer> disabledNativeOptionIndices, List<Integer> snapshotOptionCounts) {
        public OptionContract {
            bounded(optionCount, 0, 32, "option_count");
            bounded(selectedNativeOptionIndex, 0, 1023, "selected_native_option_index");
            bounded(selectedOptionNumber, 1, 1024, "selected_option_number");
            nativeOptionIndices = indices(nativeOptionIndices, 1023);
            disabledNativeOptionIndices = indices(disabledNativeOptionIndices, 1023);
            snapshotOptionCounts = indices(snapshotOptionCounts, 32);
        }
    }

    public record RenderedOption(int renderedIndex, int nativeOptionIndex, boolean shown, boolean enabled,
                                 boolean fallback, boolean cancel, GuiAvailabilityObservation guiAvailability) {
        public RenderedOption {
            Objects.requireNonNull(guiAvailability);
            bounded(renderedIndex, 0, 31, "rendered_index");
            bounded(nativeOptionIndex, 0, 1023, "native_option_index");
        }
        public RenderedOption(int renderedIndex, int nativeOptionIndex, boolean shown, boolean enabled, boolean fallback, boolean cancel) {
            this(renderedIndex, nativeOptionIndex, shown, enabled, fallback, cancel, new GuiAvailabilityObservation.LegacyNotReported());
        }
        public boolean selectionAllowed() { return guiAvailability.permitsSelectionWithRawFallback(enabled); }
    }

    /** contract is explicitly null when the registry supplies no occurrence contract. */
    public record Request(RegistryBinding binding, OptionContract contract, List<RenderedOption> options,
                          int snapshotOptionCount, int schemaVersion) {
        public Request {
            if (schemaVersion != 1 && schemaVersion != 2) throw new IllegalArgumentException("unsupported option projection version");
            if (options.stream().anyMatch(row -> (row.guiAvailability() instanceof GuiAvailabilityObservation.LegacyNotReported) != (schemaVersion == 1)))
                throw new IllegalArgumentException("option observation/version differs");
            Objects.requireNonNull(binding, "binding");
            options = List.copyOf(options);
            if (options.size() > 32) throw new IllegalArgumentException("too many rendered options");
            bounded(snapshotOptionCount, 0, 32, "snapshot_option_count");
            if (binding.registryState() == RegistryState.AVAILABLE && contract == null) {
                throw new IllegalArgumentException("available registry requires contract");
            }
            if (binding.registryState() != RegistryState.AVAILABLE && contract != null) {
                throw new IllegalArgumentException("unavailable registry must retain null contract");
            }
        }
        public Request(RegistryBinding binding, OptionContract contract, List<RenderedOption> options, int snapshotOptionCount) {
            this(binding, contract, options, snapshotOptionCount,
                    options.stream().anyMatch(row -> !(row.guiAvailability() instanceof GuiAvailabilityObservation.LegacyNotReported)) ? 2 : 1);
        }
    }

    /** The selected row can be present on a blocked projection; status remains authoritative. */
    public record Result(Status status, RegistryBinding binding, Map<String, Boolean> checks,
                         RenderedOption selectedOption, List<String> failedChecks, int schemaVersion) {
        public Result {
            if (schemaVersion != 1 && schemaVersion != 2) throw new IllegalArgumentException("unsupported projection result version");
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(binding, "binding");
            checks = Collections.unmodifiableMap(new LinkedHashMap<>(checks));
            failedChecks = List.copyOf(failedChecks);
        }
        public Result(Status status, RegistryBinding binding, Map<String, Boolean> checks, RenderedOption selectedOption, List<String> failedChecks) {
            this(status, binding, checks, selectedOption, failedChecks,
                    selectedOption != null && !(selectedOption.guiAvailability() instanceof GuiAvailabilityObservation.LegacyNotReported) ? 2 : 1);
        }
        public boolean actionAuthorized() { return false; }
        public boolean semanticDecisionReady() { return false; }
    }

    private static final Map<String, String> EXACT_BUILDS = Map.of(
        "1.19.0.6", "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
        "1.20.0.2", "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D",
        "1.20.0.3", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6",
        "1.20.0.4", "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518");

    public static Result project(Request request) {
        Objects.requireNonNull(request, "request");
        RegistryBinding binding = request.binding();
        if (binding.registryState() != RegistryState.AVAILABLE) {
            return new Result(Status.NOT_REGISTERED, binding, Map.of(), null, List.of(), request.schemaVersion());
        }
        LinkedHashMap<String, Boolean> checks = new LinkedHashMap<>();
        checks.put("registry_exact_build", binding.ck3ExeSha256().equals(EXACT_BUILDS.get(binding.ck3Build())));
        checks.put("registry_source_index_binding", !binding.sourceAnchors().isEmpty()
            && binding.sourceAnchors().stream().allMatch(row -> row.registrySha256().equals(row.indexedSha256())));
        OptionContract contract = Objects.requireNonNull(request.contract(), "contract");
        boolean nativeUnique = new HashSet<>(contract.nativeOptionIndices()).size() == contract.nativeOptionIndices().size();
        boolean disabledUnique = new HashSet<>(contract.disabledNativeOptionIndices()).size() == contract.disabledNativeOptionIndices().size();
        HashSet<Integer> disabled = new HashSet<>(contract.disabledNativeOptionIndices());
        List<Integer> actualNative = request.options().stream().map(RenderedOption::nativeOptionIndex).toList();
        checks.put("snapshot_option_count", contract.snapshotOptionCounts().contains(request.snapshotOptionCount()));
        checks.put("rendered_option_count", contract.optionCount() == request.options().size());
        checks.put("native_option_indices_exact", nativeUnique && actualNative.equals(contract.nativeOptionIndices()));
        checks.put("disabled_option_contract", nativeUnique && disabledUnique
            && contract.nativeOptionIndices().containsAll(disabled)
            && !disabled.contains(contract.selectedNativeOptionIndex()));
        checks.put("selected_option_mapping", contract.selectedOptionNumber() == contract.selectedNativeOptionIndex() + 1);
        RenderedOption selected = null;
        for (int index = 0; index < request.options().size(); index++) {
            RenderedOption option = request.options().get(index);
            checks.put("option:" + index + ":projection", option.renderedIndex() == index && option.shown()
                && option.selectionAllowed() == !disabled.contains(option.nativeOptionIndex()) && !option.fallback() && !option.cancel());
            if (option.nativeOptionIndex() == contract.selectedNativeOptionIndex()) {
                // Keep the old leaf's actual toggle behavior; duplicate native rows still fail exactness.
                selected = selected == null ? option : null;
            }
        }
        checks.put("selected_native_option_unique", selected != null);
        checks.put("selected_native_option_enabled", selected != null && selected.selectionAllowed());
        ArrayList<String> failed = new ArrayList<>();
        checks.forEach((name, passed) -> { if (!passed) failed.add(name); });
        Collections.sort(failed);
        return new Result(failed.isEmpty() ? Status.PROJECTION_READY : Status.BLOCKED,
            binding, checks, selected, failed, request.schemaVersion());
    }

    private static List<Integer> indices(List<Integer> values, int maximum) {
        List<Integer> result = List.copyOf(values);
        if (result.size() > 32) throw new IllegalArgumentException("too many option indices");
        for (int value : result) bounded(value, 0, maximum, "option index");
        return result;
    }
    private static void bounded(int value, int minimum, int maximum, String name) {
        if (value < minimum || value > maximum) throw new IllegalArgumentException(name + " outside domain");
    }
    private static void requireText(String value, String name) {
        if (value == null || value.isBlank() || value.length() > 512) throw new IllegalArgumentException(name + " invalid");
    }
    private static void requireDigest(String value) {
        if (value == null || !value.matches("[0-9A-Fa-f]{64}")) throw new IllegalArgumentException("invalid SHA-256");
    }
}
