package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** One immutable dispatch table for the original writer. No event may install its own reducer. */
public final class RootAuthorityRouter implements WriterContracts.TransitionAuthority {
    public record Binding(Set<String> kinds, WriterContracts.TransitionAuthority authority) {
        public Binding {
            kinds = Set.copyOf(kinds); Objects.requireNonNull(authority);
            StrictJson.require(!kinds.isEmpty() && kinds.size() <= 32, "bounded nonempty event kind binding required");
            kinds.forEach(RootAuthorityRouter::requireKind);
        }
    }

    private volatile Map<String, WriterContracts.TransitionAuthority> routes;

    /** Circular construction ends here, before any writer preview or host installation. */
    public synchronized void seal(List<Binding> bindings, Set<String> requiredKinds) {
        StrictJson.require(routes == null, "Root writer authority was already sealed");
        List<Binding> actual = List.copyOf(bindings); Set<String> required = Set.copyOf(requiredKinds);
        StrictJson.require(!actual.isEmpty() && actual.size() <= 32 && !required.isEmpty(), "complete bounded Root authority table required");
        required.forEach(RootAuthorityRouter::requireKind);
        Map<String, WriterContracts.TransitionAuthority> next = new LinkedHashMap<>();
        for (Binding binding : actual) {
            StrictJson.require(!(binding.authority() instanceof RootAuthorityRouter), "nested Root routers are not domain authorities");
            for (String kind : binding.kinds())
                StrictJson.require(next.putIfAbsent(kind, binding.authority()) == null, "two authorities claim event kind: " + kind);
        }
        StrictJson.require(next.keySet().equals(required), "Root authority table differs from its complete fixed kind set");
        routes = Map.copyOf(next);
    }

    public boolean isSealed() { return routes != null; }
    public Set<String> kinds() throws IOException { return sealed().keySet(); }

    @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        throw new IOException("Root qualification requires the actual original writer Head under its live lock");
    }

    @Override public String revalidate(WriterContracts.Head actualLockedHead, WriterContracts.Request request) throws IOException {
        Objects.requireNonNull(actualLockedHead); Objects.requireNonNull(request);
        // Do not reconstruct a Head from state: original file identities and recovery observations must survive dispatch.
        return selected(request).revalidate(actualLockedHead, request);
    }

    @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request request) throws IOException {
        Objects.requireNonNull(predecessor); Objects.requireNonNull(request);
        return selected(request).reduce(predecessor, request);
    }

    private WriterContracts.TransitionAuthority selected(WriterContracts.Request request) throws IOException {
        WriterContracts.TransitionAuthority selected = sealed().get(request.kind());
        if (selected == null) throw new IOException("No installed Root authority for event kind: " + request.kind());
        return selected;
    }

    private Map<String, WriterContracts.TransitionAuthority> sealed() throws IOException {
        Map<String, WriterContracts.TransitionAuthority> actual = routes;
        if (actual == null) throw new IOException("Root writer authority has not been sealed");
        return actual;
    }

    private static void requireKind(String kind) {
        StrictJson.require(kind != null && kind.matches("[A-Za-z][A-Za-z0-9_]{0,127}"), "bounded exact event kind required");
    }
}
