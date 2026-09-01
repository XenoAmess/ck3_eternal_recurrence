package com.xenoamess.kaishek.profile;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Dependency-free structural validator for the zg361 Phase 0 domain catalogue.
 *
 * <p>This class validates graph and authority contracts only. It deliberately
 * does not execute a domain, compile CK3 script, or imply runtime readiness.</p>
 */
public final class DomainGraphValidator {
    public static final String REQUIRED_PERMISSION_POLICY =
            "celestial_manager_reviews_direct_vassal";

    public static final Set<String> REQUIRED_PROHIBITED_CAPABILITIES = Set.of(
            "religion", "faith", "doctrine", "tenet", "conversion",
            "reformation", "holy_order");

    /** Complete vocabulary used by the global boundary and text scan. */
    public static final Set<String> GLOBAL_PROHIBITED_CAPABILITIES = Set.of(
            "religion", "faith", "doctrine", "tenet", "fervor", "conversion",
            "reformation", "holy_order");

    public static final Set<String> REQUIRED_STALE_GUARD = Set.of(
            "owner", "cycle_serial", "case_serial", "expected_state");

    private static final List<String> DOMAIN_CODES = domainCodes();

    private DomainGraphValidator() {}

    public static List<String> validate(Catalogue catalogue) {
        List<String> errors = new ArrayList<>();
        if (catalogue == null) {
            return List.of("catalogue must not be null");
        }

        if (!"schema-and-validator-only".equals(catalogue.lifecycleStatus())) {
            errors.add("lifecycle_status must remain schema-and-validator-only in Phase 0");
        }
        validateAcl(catalogue.permissionPolicy(), errors);

        List<DomainSpec> domains = safe(catalogue.domains());
        if (domains.size() != 38) {
            errors.add("expected exactly 38 domains, got " + domains.size());
        }

        Map<String, DomainSpec> byCode = new HashMap<>();
        boolean[] mechanismIds = new boolean[362];
        for (DomainSpec domain : domains) {
            if (domain == null) {
                errors.add("domain entry must not be null");
                continue;
            }
            if (byCode.put(domain.code(), domain) != null) {
                errors.add("duplicate domain code: " + domain.code());
            }
            validateMechanismRange(domain, mechanismIds, errors);
            validateDomain(domain, errors);
        }

        if (!new ArrayList<>(byCode.keySet()).containsAll(DOMAIN_CODES)) {
            Set<String> missing = new LinkedHashSet<>(DOMAIN_CODES);
            missing.removeAll(byCode.keySet());
            errors.add("missing domain codes: " + missing);
        }
        for (int id = 1; id <= 361; id++) {
            if (!mechanismIds[id]) {
                errors.add("mechanism id is not covered: " + id);
            }
        }
        return List.copyOf(errors);
    }

    public static void validateOrThrow(Catalogue catalogue) {
        List<String> errors = validate(catalogue);
        if (!errors.isEmpty()) {
            throw new IllegalArgumentException(String.join(System.lineSeparator(), errors));
        }
    }

    private static void validateAcl(PermissionPolicy policy, List<String> errors) {
        if (policy == null) {
            errors.add("permission policy is required");
            return;
        }
        requireAll(policy.playerManagerAllOf(), Set.of(
                "is_ai=no", "zg361_is_celestial_liege_trigger=yes"),
                "player manager ACL", errors);
        requireAll(policy.aiManagerAllOf(), Set.of(
                "is_ai=yes", "zg361_is_celestial_liege_trigger=yes",
                "entry=backend_resolver_only"), "AI manager ACL", errors);
        requireAll(policy.subjectAllOf(), Set.of(
                "zg361_is_reviewable_vassal_trigger=yes"), "subject ACL", errors);
        requireAll(policy.denied(), Set.of(
                "baron_or_count_as_manager",
                "non_celestial_government_manager",
                "non_direct_vassal_subject",
                "ai_event_or_gui_entry",
                "religion_or_faith_system_entry"), "denied ACL", errors);
    }

    private static void validateMechanismRange(
            DomainSpec domain, boolean[] mechanismIds, List<String> errors) {
        if (domain.firstMechanismId() < 1
                || domain.lastMechanismId() > 361
                || domain.firstMechanismId() > domain.lastMechanismId()) {
            errors.add(domain.code() + ": invalid mechanism id range");
            return;
        }
        for (int id = domain.firstMechanismId(); id <= domain.lastMechanismId(); id++) {
            if (mechanismIds[id]) {
                errors.add(domain.code() + ": overlapping mechanism id " + id);
            }
            mechanismIds[id] = true;
        }
    }

    private static void validateDomain(DomainSpec domain, List<String> errors) {
        String prefix = domain.code() + ": ";
        if (!DOMAIN_CODES.contains(domain.code())) {
            errors.add(prefix + "unknown domain code");
        }
        if (!REQUIRED_PERMISSION_POLICY.equals(domain.permissionPolicy())) {
            errors.add(prefix + "must use the unified celestial manager permission policy");
        }
        if (blank(domain.objectType()) || blank(domain.ownerScope()) || blank(domain.subjectScope())) {
            errors.add(prefix + "object_type, owner_scope and subject_scope are required");
        }
        if (safe(domain.entryHooks()).isEmpty()) {
            errors.add(prefix + "at least one allowed entry hook is required");
        }
        if (containsForbiddenText(domain)) {
            errors.add(prefix + "religion/faith/holy-order semantics are prohibited");
        }
        requireAll(domain.prohibitedCapabilities(), REQUIRED_PROHIBITED_CAPABILITIES,
                prefix + "prohibited capabilities", errors);

        Capacity capacity = domain.capacity();
        if (capacity == null
                || capacity.maxActivePerSubject() != 1
                || capacity.maxActivePerOwner() < 1
                || blank(capacity.invariant())) {
            errors.add(prefix + "bounded capacity and its conservation invariant are required");
        }
        Cleanup cleanup = domain.cleanup();
        if (cleanup == null) {
            errors.add(prefix + "cleanup contract is required");
        } else {
            if (!"no_op_with_marker".equals(cleanup.staleDeadline())) {
                errors.add(prefix + "stale deadline must be a marked no-op");
            }
            requireAll(cleanup.guard(), REQUIRED_STALE_GUARD, prefix + "stale guard", errors);
            if (cleanup.retentionCycles() < 0 || blank(cleanup.onTerminal())) {
                errors.add(prefix + "cleanup retention and terminal action are invalid");
            }
        }

        Set<String> states = new LinkedHashSet<>(safe(domain.states()));
        if (states.size() != safe(domain.states()).size() || states.size() < 2) {
            errors.add(prefix + "states must be unique and contain at least two entries");
        }
        if (!states.contains(domain.initialState())) {
            errors.add(prefix + "initial_state is not declared");
        }
        Set<String> terminals = new LinkedHashSet<>(safe(domain.terminalStates()));
        if (terminals.isEmpty() || !states.containsAll(terminals)) {
            errors.add(prefix + "at least one declared terminal state is required");
        }

        Map<String, Set<String>> edges = new HashMap<>();
        for (Transition transition : safe(domain.transitions())) {
            if (transition == null
                    || !states.contains(transition.from())
                    || !states.contains(transition.to())
                    || transition.from().equals(transition.to())
                    || blank(transition.hook())
                    || blank(transition.actor())) {
                errors.add(prefix + "invalid transition: " + transition);
                continue;
            }
            if (terminals.contains(transition.from())) {
                errors.add(prefix + "terminal state has outgoing transition: " + transition.from());
            }
            edges.computeIfAbsent(transition.from(), ignored -> new HashSet<>()).add(transition.to());
        }
        Set<String> reachable = reachable(domain.initialState(), edges);
        if (!reachable.containsAll(states)) {
            Set<String> missing = new LinkedHashSet<>(states);
            missing.removeAll(reachable);
            errors.add(prefix + "unreachable states: " + missing);
        }
    }

    private static boolean containsForbiddenText(DomainSpec domain) {
        List<String> values = new ArrayList<>();
        values.add(domain.objectType());
        values.add(domain.ownerScope());
        values.add(domain.subjectScope());
        values.addAll(safe(domain.states()));
        values.addAll(safe(domain.entryHooks()));
        for (String value : values) {
            String lower = value == null ? "" : value.toLowerCase();
            for (String forbidden : GLOBAL_PROHIBITED_CAPABILITIES) {
                if (lower.contains(forbidden)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static Set<String> reachable(String initial, Map<String, Set<String>> edges) {
        Set<String> visited = new HashSet<>();
        ArrayDeque<String> queue = new ArrayDeque<>();
        if (initial != null) {
            queue.add(initial);
        }
        while (!queue.isEmpty()) {
            String state = queue.removeFirst();
            if (!visited.add(state)) {
                continue;
            }
            queue.addAll(edges.getOrDefault(state, Set.of()));
        }
        return visited;
    }

    private static void requireAll(
            List<String> actual, Set<String> required, String label, List<String> errors) {
        Set<String> actualSet = new HashSet<>(safe(actual));
        if (!actualSet.containsAll(required)) {
            Set<String> missing = new LinkedHashSet<>(required);
            missing.removeAll(actualSet);
            errors.add(label + " is missing " + missing);
        }
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }

    private static <T> List<T> safe(List<T> values) {
        return values == null ? List.of() : values;
    }

    private static List<String> domainCodes() {
        List<String> codes = new ArrayList<>();
        for (char code = 'A'; code <= 'Z'; code++) {
            codes.add(String.valueOf(code));
        }
        for (char code = 'A'; code <= 'L'; code++) {
            codes.add("A" + code);
        }
        return List.copyOf(codes);
    }

    public record Catalogue(
            String lifecycleStatus,
            PermissionPolicy permissionPolicy,
            List<DomainSpec> domains) {}

    public record PermissionPolicy(
            List<String> playerManagerAllOf,
            List<String> aiManagerAllOf,
            List<String> subjectAllOf,
            List<String> denied) {}

    public record DomainSpec(
            String code,
            int firstMechanismId,
            int lastMechanismId,
            String objectType,
            String ownerScope,
            String subjectScope,
            String permissionPolicy,
            List<String> entryHooks,
            List<String> states,
            String initialState,
            List<Transition> transitions,
            List<String> terminalStates,
            Capacity capacity,
            Cleanup cleanup,
            List<String> prohibitedCapabilities) {}

    public record Transition(String from, String to, String hook, String actor) {}

    public record Capacity(
            String scope,
            int maxActivePerSubject,
            int maxActivePerOwner,
            String invariant) {}

    public record Cleanup(
            String onTerminal,
            String staleDeadline,
            List<String> guard,
            int retentionCycles) {}
}
