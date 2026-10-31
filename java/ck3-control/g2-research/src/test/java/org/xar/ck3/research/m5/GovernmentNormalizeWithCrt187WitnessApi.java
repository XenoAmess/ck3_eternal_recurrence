package org.xar.ck3.research.m5;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Independent ONE raw174->182->185 combination, with one shared ordered script. */
public final class GovernmentNormalizeWithCrt187WitnessApi {
    private GovernmentNormalizeWithCrt187WitnessApi() { }
    public enum Port { ORDINARY,CRT }
    public sealed interface Event permits AtomicStep,GsStep,CrtCallStep,CrtTailStep,CrtLoopStep { }
    public record AtomicStep(long addressBits,int addendBits,int oldBits,int storedBits) implements Event { }
    public record GsStep(Port port,long returnedBits) implements Event { }
    public record CrtCallStep(Call expected,Map<Long,Integer> expectedMemoryBefore,
            Map<Long,Integer> mutation,VolatileBits normalPost) implements Event {
        public CrtCallStep { Objects.requireNonNull(expected);Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore);mutation=Map.copyOf(mutation); }
    }
    public record CrtTailStep(Tail expected,Map<Long,Integer> expectedMemoryBefore,Map<Long,Integer> mutation,
            GovernmentCrtBoundary185Api.NormalReturn normalPost) implements Event {
        public CrtTailStep { Objects.requireNonNull(expected);Objects.requireNonNull(normalPost);
            expectedMemoryBefore=Map.copyOf(expectedMemoryBefore);mutation=Map.copyOf(mutation); }
    }
    public record CrtLoopStep(long loopHeaderRva,long guardAddressBits) implements Event { }
    public record Witness(String name,GovernmentNormalizeFull174Api.Entry entry,Map<Long,Integer> memorySeed,
            List<Event> events,Map<Long,Integer> expectedFinalBytes,GovernmentNormalizeFull174Api.NormalReturn expected) {
        public Witness { Objects.requireNonNull(name);Objects.requireNonNull(entry);Objects.requireNonNull(expected);
            memorySeed=Map.copyOf(memorySeed);events=List.copyOf(events);expectedFinalBytes=Map.copyOf(expectedFinalBytes); }
    }
    public interface Book { List<Witness> witnesses(); }
}
