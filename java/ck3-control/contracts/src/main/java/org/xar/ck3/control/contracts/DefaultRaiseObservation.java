package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** One payload validator for the native read codec and ordinary reserve planner. Grants no read/action authority. */
public final class DefaultRaiseObservation {
    public static final String STEP="query-player-default-raise-v1";
    private DefaultRaiseObservation() { }
    public enum Status { AVAILABLE,PARTIAL,UNAVAILABLE,REQUIRES_PAUSED,INVALID_REQUEST }
    public record Expected(String gameVersion,BigInteger actor,BigInteger nativeRevision,BigInteger dateRaw) {
        public Expected {
            Objects.requireNonNull(gameVersion);Objects.requireNonNull(actor);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(dateRaw);
            StrictJson.require(Set.of("1.20.0.3","1.20.0.4").contains(gameVersion)&&actor.signum()>=0&&actor.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0
                    &&nativeRevision.signum()>0&&nativeRevision.compareTo(StrictJson.UINT64_MAX)<=0
                    &&dateRaw.compareTo(BigInteger.valueOf(Integer.MIN_VALUE))>=0&&dateRaw.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"exact default raise actor/revision/date/build required");
        }
    }
    public record RaiseState(Status status,boolean ready,Optional<Boolean> legal,Optional<Integer> provinceId,String failure) {
        public RaiseState {Objects.requireNonNull(status);Objects.requireNonNull(legal);Objects.requireNonNull(provinceId);Objects.requireNonNull(failure);}
    }
    public record Reserve(boolean ready,Optional<Integer> unraisedSoldiers,String failure) {
        public Reserve {Objects.requireNonNull(unraisedSoldiers);Objects.requireNonNull(failure);}
    }
    public record Observed(String gameVersion,String executableSha256,int actor,BigInteger nativeRevision,int dateRaw,
            RaiseState raising,Reserve reserve) {
        public Observed {Objects.requireNonNull(gameVersion);Objects.requireNonNull(executableSha256);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(raising);Objects.requireNonNull(reserve);}
    }
    public static Observed parse(JsonNode value,Expected expected) {
        Objects.requireNonNull(expected);ObjectNode row=StrictJson.object(value,FIELDS);
        String version=StrictJson.text(row.get("game_version")),sha=StrictJson.text(row.get("executable_sha256"));
        String expectedSha=switch(version) {
            case "1.20.0.3"->"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
            case "1.20.0.4"->"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
            default->throw new ContractViolationException("unknown default raise native build");
        };
        StrictJson.require(version.equals(expected.gameVersion())&&expectedSha.equals(sha.toUpperCase(Locale.ROOT))
                &&StrictJson.text(row.get("schema")).equals(version.equals("1.20.0.4")?"ck3_12004_player_default_raise_v1":"ck3_12003_player_default_raise_v1"),"unknown or mixed default raise schema/build");
        int actor=(int)StrictJson.integer(row.get("actor_character_id"),0,Integer.MAX_VALUE);
        BigInteger revision=StrictJson.integer(row.get("snapshot_revision"),BigInteger.ONE,StrictJson.UINT64_MAX);
        int date=(int)StrictJson.integer(row.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);
        StrictJson.require(BigInteger.valueOf(actor).equals(expected.actor())&&revision.equals(expected.nativeRevision())&&BigInteger.valueOf(date).equals(expected.dateRaw()),"default raise payload differs from current actor/frame");
        String status=StrictJson.text(row.get("status"));
        StrictJson.require(Set.of("available","partial","unavailable","requires_paused","invalid_request").contains(status),"known default raise status required");
        boolean ready=bool(row.get("default_raise_legality_ready"));
        Optional<Boolean> legal=row.get("native_default_raise_legal").isNull()?Optional.empty():Optional.of(bool(row.get("native_default_raise_legal")));
        Optional<Integer> province=nullableInteger(row.get("default_raise_province_id"),1);
        String failure=StrictJson.text(row.get("failure"));
        StrictJson.require(ready==legal.isPresent()&&("available".equals(status)==ready)&&(!ready||province.isPresent()&&failure.equals("none")),"default raise final legality/readiness malformed");
        String reserveStatus=StrictJson.text(row.get("unraised_troops_status"));
        StrictJson.require(Set.of("available","unavailable").contains(reserveStatus),"known unraised reserve status");
        boolean reserveReady=bool(row.get("unraised_troops_ready"));
        StrictJson.require(reserveReady==reserveStatus.equals("available")&&StrictJson.integer(row.get("unraised_troops_scale"),1,1)==1
                &&StrictJson.text(row.get("unraised_troops_scope")).equals("native_all_actor_categories"),"default raise reserve scope/readiness malformed");
        Optional<Integer> soldiers=nullableInteger(row.get("unraised_soldiers"),0);
        String reserveFailure=StrictJson.text(row.get("unraised_troops_failure"));
        StrictJson.require(reserveReady?soldiers.isPresent()&&reserveFailure.equals("none"):soldiers.isEmpty()&&!reserveFailure.equals("none"),"native all-unraised observation malformed");
        return new Observed(version,sha,actor,revision,date,new RaiseState(Status.valueOf(status.toUpperCase(Locale.ROOT)),ready,legal,province,failure),new Reserve(reserveReady,soldiers,reserveFailure));
    }
    private static boolean bool(JsonNode value) {StrictJson.require(value!=null&&value.isBoolean(),"explicit default raise Boolean required");return value.booleanValue();}
    private static Optional<Integer> nullableInteger(JsonNode value,int minimum) {
        StrictJson.require(value!=null,"required nullable default raise field missing");
        return value.isNull()?Optional.empty():Optional.of((int)StrictJson.integer(value,minimum,Integer.MAX_VALUE));
    }
    private static final Set<String> FIELDS=Set.of("schema","game_version","executable_sha256","status","snapshot_revision","date_raw","actor_character_id",
            "default_raise_province_id","native_default_raise_legal","default_raise_legality_ready","failure","unraised_troops_status","unraised_soldiers",
            "unraised_troops_ready","unraised_troops_failure","unraised_troops_scale","unraised_troops_scope");
}
