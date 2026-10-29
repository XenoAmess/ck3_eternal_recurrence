package org.xar.ck3.control.nativebridge.capabilities.aub;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Validated native DATA stamps. This record grants no observation, source, read or action authority. */
record AubNativeStamp(BigInteger nativeRevision,BigInteger generation,BigInteger gamePid,BigInteger actor,BigInteger dateRaw) {
    private static final BigInteger U32=new BigInteger("4294967295"),I32=BigInteger.valueOf(Integer.MAX_VALUE),MIN=BigInteger.valueOf(Integer.MIN_VALUE);
    AubNativeStamp {
        range(nativeRevision,BigInteger.ONE,NativeWire.UINT64_MAX);range(generation,BigInteger.ONE,NativeWire.UINT64_MAX);
        range(gamePid,BigInteger.ONE,U32);range(actor,BigInteger.ONE,I32);range(dateRaw,MIN,I32);
    }
    static AubNativeStamp expected(ObservationIdentity before,BigInteger generation) {
        Objects.requireNonNull(before);return new AubNativeStamp(before.frame().identity().nativeRevision(),generation,
                BigInteger.valueOf(before.game().pid()),before.frame().identity().player(),before.frame().identity().dateRaw());
    }
    static AubNativeStamp read(ObjectNode row)throws IOException {
        return new AubNativeStamp(NativeWire.integer(row.get("native_revision"),BigInteger.ONE,NativeWire.UINT64_MAX),
                NativeWire.integer(row.get("connection_generation"),BigInteger.ONE,NativeWire.UINT64_MAX),
                NativeWire.integer(row.get("game_pid"),BigInteger.ONE,U32),NativeWire.integer(row.get("played_character_id"),BigInteger.ONE,I32),
                NativeWire.integer(row.get("date_raw"),MIN,I32));
    }
    void require(ObjectNode row)throws IOException {StrictJson.require(equals(read(row)),"AUB native DATA stamps differ");}
    boolean sameOwner(AubNativeStamp other) {return gamePid.equals(other.gamePid)&&actor.equals(other.actor)&&dateRaw.equals(other.dateRaw)&&generation.equals(other.generation);}
    private static void range(BigInteger value,BigInteger min,BigInteger max) {
        Objects.requireNonNull(value);StrictJson.require(value.compareTo(min)>=0&&value.compareTo(max)<=0,"AUB native stamp outside its actual numeric role");
    }
}
