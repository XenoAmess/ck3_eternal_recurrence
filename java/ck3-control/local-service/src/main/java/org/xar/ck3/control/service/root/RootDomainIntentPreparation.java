package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Domain-owned pending producers run once before the coordinator's original INTENT. */
public final class RootDomainIntentPreparation implements ActionPorts.IntentPreparationPort {
    public record Binding(String id, ExactRef implementationSource, Predicate<ActionCommand> supports,
            ActionPorts.IntentPreparationPort producer) {
        public Binding {
            StrictJson.text(id); Objects.requireNonNull(implementationSource); Objects.requireNonNull(supports); Objects.requireNonNull(producer);
            StrictJson.require(implementationSource.bytes() > 0, "actual domain pending producer source required");
        }
    }
    private final ContinuityWriter writer;
    private final List<Binding> bindings;
    private final Set<OperationKey> required;
    public RootDomainIntentPreparation(ContinuityWriter writer, List<Binding> bindings, Set<OperationKey> required) {
        this.writer = Objects.requireNonNull(writer); this.bindings = List.copyOf(bindings); this.required = Set.copyOf(required);
        StrictJson.require(this.bindings.size() <= 128 && this.required.size() <= 4096, "bounded exact pending producer inventory required");
        Set<String> ids = new HashSet<>();
        for (Binding binding : this.bindings) StrictJson.require(ids.add(binding.id()), "duplicate pending producer registration");
    }
    @Override public void prepare(ContinuityStorePort.Session actualOriginal, ActionCommand command) {
        Objects.requireNonNull(command);
        try {
            writer.requireSession(actualOriginal);
            List<Binding> selected = bindings.stream().filter(binding -> binding.supports().test(command)).toList();
            StrictJson.require(selected.size() <= 1, "two pending producers claim the same action");
            StrictJson.require(!required.contains(command.operation()) || selected.size() == 1, "required durable pending producer missing");
            if (selected.isEmpty()) return;
            Binding binding = selected.getFirst();
            WriterContracts.Pin source = actualOriginal.capturePin(binding.implementationSource(), WriterContracts.MAX_PIN_BYTES);
            binding.producer().prepare(actualOriginal, command);
            writer.requireSession(actualOriginal); actualOriginal.verifyPin(source);
        } catch (IOException failure) { throw new UncheckedIOException("original domain pending preparation unavailable", failure); }
    }
}
