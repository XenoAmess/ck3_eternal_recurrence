package org.xar.ck3.control.application.planning.warentry;

import static org.xar.ck3.control.application.planning.warentry.WarEntryJson.*;

import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.charset.StandardCharsets;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Direct migration of the bounded 256 x 120 aggregate prior. It never grants declaration authority. */
public final class PrewarBattlePrior {
    private static final BigInteger SCALE=BigInteger.valueOf(100000);
    private PrewarBattlePrior() { }
    public static Obj forecast(Obj assessment,String declarationId) {
        BigInteger actor=number(assessment,"actor_power_base_raw"),target=number(assessment,"target_power_total_raw");
        if(actor==null || actor.signum()<=0 || target==null || target.signum()<=0 || declarationId==null || declarationId.isEmpty())return obj().text("status","native_power_input_unavailable").build();
        // The original json.dumps(sort_keys=True,separators=(",",":")) order is part of the seed contract.
        Obj source=obj().value("actor_network_contribution_raw",assessment.get("actor_network_contribution_raw")).number("actor_power_base_raw",actor).text("declaration_id",declarationId).value("target_network_contribution_raw",assessment.get("target_network_contribution_raw")).number("target_power_total_raw",target).build();
        String digest=sha(asciiJson(source));long seed=Long.parseUnsignedLong(digest.substring(0,16),16);
        int wins=0,losses=0,unresolved=0;
        for(int trial=0;trial<256;trial++) {
            long first=splitmix(seed+trial*2L);int counter=(int)first,salt=(int)(first>>>32);int[] draw=new int[4];
            for(int i=0;i<4;i++)draw[i]=avalanche(salt-counter++*0x4AD685B3)&0x7fffffff;
            BigInteger ah=mul(actor,65000+draw[0]%35001),dh=mul(target,110000+draw[1]%35001);
            int advantage=draw[2]%21-draw[3]%21,am=100000+Math.max(advantage,0)*5000,dm=100000+Math.max(-advantage,0)*5000;
            int result=0;
            for(int day=0;day<120;day++) {
                BigInteger ad=mul(ah,am).multiply(BigInteger.valueOf(3)).divide(BigInteger.valueOf(100));
                BigInteger dd=mul(dh,dm).multiply(BigInteger.valueOf(3)).divide(BigInteger.valueOf(100));
                BigInteger na=ah.subtract(dd),nd=dh.subtract(ad);
                if(na.signum()<=0 || nd.signum()<=0) {result=na.signum()<=0 && nd.signum()<=0?0:nd.signum()<=0?1:-1;break;}
                ah=na;dh=nd;
            }
            if(result>0)wins++;else if(result<0)losses++;else unresolved++;
        }
        int resolved=wins+losses;Builder b=obj().text("status","estimated").text("model_fidelity","aggregate-prewar-surrogate-not-native-parity").bool("calibrated_probability",false).text("source_sha256",digest.toUpperCase(java.util.Locale.ROOT)).number("sample_count",256).number("horizon_days",120).number("wins",wins).number("losses",losses).number("no_resolution",unresolved);
        if(resolved==0)b.value("resolved_win_fraction",Nil.INSTANCE).value("resolved_win_wilson95_lower",Nil.INSTANCE);else b.decimal("resolved_win_fraction",(double)wins/resolved).decimal("resolved_win_wilson95_lower",wilson(wins,resolved));
        return b.value("assumptions",obj().value("actor_mobilized_power_fraction_raw",numbers(List.of(BigInteger.valueOf(65000),BigInteger.valueOf(100000)))).value("enemy_power_fraction_raw",numbers(List.of(BigInteger.valueOf(110000),BigInteger.valueOf(145000)))).value("roll_range_each",numbers(List.of(BigInteger.ZERO,BigInteger.valueOf(20)))).number("daily_damage_fraction_raw",3000).value("missing",strings(List.of("prewar_regiment_roster","terrain","reinforcement_timing","phase_events","casualty_types"))).build()).build();
    }
    public static Obj admission(Obj forecast) {
        Value lower=forecast.get("resolved_win_wilson95_lower");double probability=lower instanceof DecimalValue decimal?Double.parseDouble(decimal.token()):lower instanceof IntegerValue integer?integer.value().doubleValue():-1;
        BigInteger count=number(forecast,"sample_count"),unresolved=number(forecast,"no_resolution");
        boolean passed=is(forecast.get("status"),"estimated") && probability>=.95 && count!=null && count.signum()>0 && unresolved!=null && unresolved.compareTo(count.divide(BigInteger.valueOf(20)))<=0;
        return obj().bool("admitted",false).text("reason",passed?"independent_force_coalition_evidence_required":"aggregate_battle_prior_risk_too_high").bool("proxy_risk_budget_passed",passed).decimal("minimum_wilson_lower",.95).decimal("maximum_unresolved_fraction",.05).bool("native_parity_required",false).build();
    }
    private static BigInteger mul(BigInteger a,int b) {return a.multiply(BigInteger.valueOf(b)).divide(SCALE);}
    private static byte[] asciiJson(Obj source) {
        String json=new String(OpportunityJson.encode(source),StandardCharsets.UTF_8);StringBuilder ascii=new StringBuilder();
        for(int i=0;i<json.length();i++) {char c=json.charAt(i);if(c<128)ascii.append(c);else {ascii.append("\\u");String hex=Integer.toHexString(c);ascii.append("0".repeat(4-hex.length())).append(hex);}}
        return ascii.toString().getBytes(StandardCharsets.US_ASCII);
    }
    private static long splitmix(long v) {v+=0x9E3779B97F4A7C15L;v=(v^(v>>>30))*0xBF58476D1CE4E5B9L;v=(v^(v>>>27))*0x94D049BB133111EBL;return v^(v>>>31);}
    private static int avalanche(int v) {v^=v>>>8;v+=0x68E31DA4;v^=v<<8;v*=0x1B56C4E9;v^=v>>>8;v*=0x92D68CA2;v^=v>>>8;return v;}
    private static double wilson(int successes,int trials) {double z=1.959963984540054,p=(double)successes/trials,z2=z*z,d=1.0+z2/trials,c=(p+z2/(2.0*trials))/d,h=z*Math.sqrt(p*(1.0-p)/trials+z2/(4.0*trials*trials))/d;return Math.max(0.0,c-h);}
    private static String sha(byte[] value) {try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
}
