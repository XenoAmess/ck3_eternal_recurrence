package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent raw-body normal-port data. Events impose one shared port order. */
public final class GovernmentCrtBoundary185WitnessApi {
    private GovernmentCrtBoundary185WitnessApi() { }
    public enum Subject { RVA_4223A84, RVA_4223A24, RVA_4223F24 }
    public sealed interface Event permits CallStep,TailStep,GsStep,LoopStep { }
    public record CallStep(Call expected,Map<Long,Integer> expectedMemoryBefore,
            Map<Long,Integer> mutation,VolatileBits normalPost) implements Event {
        public CallStep { Objects.requireNonNull(expected);Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore);mutation=Map.copyOf(mutation); }
    }
    public record TailStep(Tail expected,Map<Long,Integer> expectedMemoryBefore,
            Map<Long,Integer> mutation,NormalReturn normalPost) implements Event {
        public TailStep { Objects.requireNonNull(expected);Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore);mutation=Map.copyOf(mutation); }
    }
    public record GsStep(long returnedBits) implements Event { }
    public record LoopStep(long loopHeaderRva,long guardAddressBits) implements Event { }
    public record Witness(String name,Subject subject,Entry entry,Map<Long,Integer> memorySeed,
            List<Event> events,Map<Long,Integer> expectedFinalBytes,NormalReturn expected) {
        public Witness { Objects.requireNonNull(name);Objects.requireNonNull(subject);
            Objects.requireNonNull(entry);Objects.requireNonNull(expected);
            memorySeed=Map.copyOf(memorySeed);events=List.copyOf(events);expectedFinalBytes=Map.copyOf(expectedFinalBytes); }
    }
    public interface Book { List<Witness> witnesses(); }
}
