package org.xar.ck3.control.application.planning.warentry;

import java.math.BigInteger;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Exact legacy history classification; recognizing progress grants no action capability. */
final class WarEntryHistoryAdvance {
    private WarEntryHistoryAdvance() { }
    private static final String POS="([1-9][0-9]*)", UNIT="(0|[1-9][0-9]*)";
    private static final Pattern EPOCH=Pattern.compile("battle-decision-epoch-advance-to-"+POS);
    private static final Pattern ROUTE=Pattern.compile("committed-route-sentinel-advance-army-"+UNIT+"-to-"+POS+"-until-"+POS+"(?:-speed-([1245]))?");
    private static final Pattern HOLD=Pattern.compile("war-objective-hold-sentinel-advance-war-"+POS+"-army-"+UNIT+"-at-"+POS+"-until-"+POS+"(?:-speed-([1245]))?");
    static boolean isAdvance(String step) {
        if(step==null)return false;
        if(Set.of("life-advance","life-advance-one-day","battle-decision-epoch-advance","battle-terminal-cruise").contains(step))return true;
        Matcher epoch=EPOCH.matcher(step);if(epoch.matches())return fits(epoch.group(1),Long.MAX_VALUE);
        Matcher route=ROUTE.matcher(step);if(route.matches())return fits(route.group(1),Integer.MAX_VALUE)&&fits(route.group(2),Integer.MAX_VALUE)&&fits(route.group(3),Long.MAX_VALUE);
        Matcher hold=HOLD.matcher(step);if(hold.matches())return fits(hold.group(1),Integer.MAX_VALUE)&&fits(hold.group(2),Integer.MAX_VALUE)&&fits(hold.group(3),Integer.MAX_VALUE)&&fits(hold.group(4),Long.MAX_VALUE);
        if(step.startsWith("advance-route-contact-horizon-v1-"))return contact(step.substring("advance-route-contact-horizon-v1-".length()),false);
        if(step.startsWith("advance-route-contact-window-v1-"))return contact(step.substring("advance-route-contact-window-v1-".length()),true);
        return false;
    }
    private static boolean contact(String payload,boolean window) {
        String[] p=payload.split("-",-1);int hi=window?6:4,start=hi+1;
        if(p.length<=start || !p[1].equals("to") || !p[window?5:3].equals("h"))return false;
        if(window && (!p[3].equals("days") || !Set.of("2","3").contains(p[4])))return false;
        if(!canonical(p[0]) || !fits(p[0],Integer.MAX_VALUE) || !digits(p[2]) || !fits(p[2],Integer.MAX_VALUE) || new BigInteger(p[2]).signum()<=0 || !digits(p[hi]))return false;
        if(window && (!canonical(p[2]) || !canonical(p[hi])))return false;
        BigInteger count=new BigInteger(p[hi]);if(count.signum()<=0 || count.compareTo(BigInteger.valueOf(64))>0 || count.intValue()!=p.length-start)return false;
        BigInteger previous=BigInteger.valueOf(-1),subject=new BigInteger(p[0]);
        for(int i=start;i<p.length;i++) {if(!canonical(p[i]) || !fits(p[i],Integer.MAX_VALUE))return false;BigInteger n=new BigInteger(p[i]);if(n.compareTo(previous)<=0 || n.equals(subject))return false;previous=n;}
        return true;
    }
    private static boolean digits(String s) { return s.matches("[0-9]+"); }
    private static boolean canonical(String s) {return s.matches("0|[1-9][0-9]*");}
    private static boolean fits(String s,long max) {return new BigInteger(s).compareTo(BigInteger.valueOf(max))<=0;}
}
