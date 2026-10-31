package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Full normal CPU-state contract missing from the previously accepted scalar292 producer. */
public final class GovernmentTokenLookup182Api {
    private GovernmentTokenLookup182Api() { }
    public record Entry(long imageBaseBits,long rspBits,VolatileBits volatileBits,NonvolatileBits nonvolatileBits) {
        public Entry { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public record NormalReturn(VolatileBits volatileBits,long returnRipBits,long callerRspBits,NonvolatileBits nonvolatileBits) {
        public NormalReturn { Objects.requireNonNull(volatileBits);Objects.requireNonNull(nonvolatileBits); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory {
        int readUnsignedWord(long addressBits);
        void writeWord(long addressBits,int lowWordBits);
    }
    public interface Calls extends GovernmentPrimaryTail155Api.Calls { }
    public interface Pause {
        /** One represented PAUSE; an owned external actor may update shared memory, but never supplies guessed V. */
        void at(long pauseRva);
    }
    public interface LoopBudget {
        /** Software stopping port before each actual3F4F910 lock-read header, not a hidden iteration cap. */
        void beforeStep(long headerRva,long lockAddressBits);
    }
}
