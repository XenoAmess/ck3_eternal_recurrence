import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import org.xar.ck3.save.SaveContracts.Pin;

/** Typed linkage to the shared capacity implementation; no accounting or facts implementation. */
final class SharedSourceCapacity {
    private SharedSourceCapacity() { }
    private static F15ReadOnlyBuildBudget20261029.Pin wire(Pin value) {
        return new F15ReadOnlyBuildBudget20261029.Pin(value.path(), value.bytes(), value.sha256());
    }
    static void consumeFacts(String machine, String head, Pin facts, Pin qualification, Path outputPrefix) throws Exception {
        SourceContinuationCapacity.consumeFacts(machine, head, wire(facts), wire(qualification), outputPrefix);
    }
    static void validateFreshBinding(JsonNode fresh, String machine, String head, Pin authority, Pin facts) throws Exception {
        SourceContinuationCapacity.validateFreshBinding(fresh, machine, head, wire(authority), wire(facts));
    }
}
