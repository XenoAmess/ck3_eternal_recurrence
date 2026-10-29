package org.xar.ck3.control.application.planning.finance;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.runtime.creationtime.ProcessCreationTime;

/** Preserves original birth spelling and never treats lost timestamp precision as a process replacement. */
public final class GiftProcessIdentity {
    public enum Relation { SAME, DIFFERENT, UNAVAILABLE }
    private record Birth(Instant instant, long uncertaintyNanos) { }
    private static final BigInteger TICKS_PER_SECOND=BigInteger.valueOf(10000000);
    private static final BigInteger WINDOWS_EPOCH_SECONDS=new BigInteger("11644473600");
    private GiftProcessIdentity() { }

    /** FILETIME remains exact to its original 100 ns tick; no floating point or microsecond conversion. */
    public static ProcessIdentity actual(GameGeneration game) {
        Objects.requireNonNull(game);
        BigInteger[] ticks=game.creationFiletime().value().divideAndRemainder(TICKS_PER_SECOND);
        Instant birth=Instant.ofEpochSecond(ticks[0].subtract(WINDOWS_EPOCH_SECONDS).longValueExact(),ticks[1].longValueExact()*100L);
        return new ProcessIdentity(BigInteger.valueOf(game.pid()),birth.toString());
    }

    /** An unavailable relation must block cold admission; callers must not turn it into boolean inequality. */
    public static Relation compare(ProcessIdentity original,GameGeneration current) {
        Objects.requireNonNull(original);Objects.requireNonNull(current);
        Birth old;
        try { old=parse(original.creationDate()); }
        catch(IllegalArgumentException unsupported) { return Relation.UNAVAILABLE; }
        ProcessIdentity actual=actual(current);
        if(!original.pid().equals(actual.pid()))return Relation.DIFFERENT;
        Instant now=Instant.parse(actual.creationDate());
        if(old.instant().equals(now))return Relation.SAME;
        Duration difference=Duration.between(old.instant(),now).abs();
        if(difference.compareTo(Duration.ofNanos(old.uncertaintyNanos()))<0)return Relation.UNAVAILABLE;
        return Relation.DIFFERENT;
    }

    private static Birth parse(String original) {
        if(original==null||original.length()>32768)throw new IllegalArgumentException("bounded original Gift process birth required");
        try { return new Birth(ProcessCreationTime.parse(original).instant(),1000L); }
        catch(IllegalArgumentException unsupportedWindowsSpelling) {
            final Instant parsed;
            try { parsed=Instant.parse(original); }
            catch(java.time.DateTimeException unsupportedIso) { throw new IllegalArgumentException("original Gift process birth is unavailable",unsupportedIso); }
            if(parsed.getNano()%100!=0)throw new IllegalArgumentException("Gift process birth cannot originate from a FILETIME tick");
            int point=original.indexOf('.');int digits=0;
            if(point>=0)for(int index=point+1;index<original.length()&&original.charAt(index)>='0'&&original.charAt(index)<='9';index++)digits++;
            long quantum=1000000000L;
            for(int index=0;index<digits;index++)quantum/=10;
            return new Birth(parsed,Math.max(100L,quantum));
        }
    }
}
