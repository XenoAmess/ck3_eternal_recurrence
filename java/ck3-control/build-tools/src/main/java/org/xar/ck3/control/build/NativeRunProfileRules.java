package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.regex.Pattern;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Installed vanilla defaults and the three actual mod rule declarations; no policy defaults. */
public final class NativeRunProfileRules {
    private static final Pattern RULE = Pattern.compile("^([A-Za-z0-9_]+)\\s*=\\s*\\{");
    private static final Pattern DEFAULT = Pattern.compile("^\\s*default\\s*=\\s*([A-Za-z0-9_]+)\\s*$");
    private NativeRunProfileRules() { }
    public enum XarMode { XAR_ON("xar_on"), XAR_OFF("xar_off");
        private final String setting; XarMode(String setting) { this.setting=setting; }
        public String setting() { return setting; }
    }
    public record Rule(String rule,String setting) {
        public Rule { token(rule); token(setting); }
    }
    public record Contract(FileRef source,int declaredVanillaRuleCount,List<Rule> profile,String profileSha256,boolean ironman) {
        public Contract {
            Objects.requireNonNull(source); profile=List.copyOf(profile);
            require(declaredVanillaRuleCount>=70 && declaredVanillaRuleCount<=4096
                    && profile.size()==declaredVanillaRuleCount+3 && !ironman,"complete vanilla plus three mod rules required");
            require(profile.stream().map(Rule::rule).distinct().count()==profile.size()
                    && profile.stream().map(Rule::setting).distinct().count()==profile.size(),"unique rule/default setting identities required");
            require(profile.get(declaredVanillaRuleCount).rule().equals("xar_enabled")
                    &&List.of("xar_on","xar_off").contains(profile.get(declaredVanillaRuleCount).setting())
                    &&profile.get(declaredVanillaRuleCount+1).equals(new Rule("xar_inheritance","xar_inherit_100"))
                    &&profile.get(declaredVanillaRuleCount+2).equals(new Rule("xar_score_basis","xar_score_growth")),
                    "exact original three mod rule settings required");
            require(sha(profileBytes(profile)).equals(profileSha256),"rule profile digest must derive from actual rows");
        }
    }
    /** Ports the actual line/depth contract, including comments, missing defaults and duplicate settings. */
    public static Contract derive(FileRef actualSource,byte[] original,XarMode mode) throws IOException {
        Objects.requireNonNull(mode);
        if(original==null || original.length==0 || original.length>4<<20
                || original.length!=actualSource.bytes() || !sha(original).equals(actualSource.sha256()))
            throw new IOException("bounded exact installed vanilla rules source required");
        String text;
        try{text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                .decode(java.nio.ByteBuffer.wrap(original)).toString();}
        catch(java.nio.charset.CharacterCodingException malformed){throw new IOException("vanilla rules must be exact UTF-8",malformed);}
        if(text.startsWith("\ufeff"))text=text.substring(1);
        var rows=new ArrayList<Rule>(); int depth=0; String current=null,setting=null;
        for(String raw:text.split("\\R",-1)) {
            String line=raw.split("#",2)[0];
            if(depth==0) {
                var match=RULE.matcher(line);
                if(match.find()){current=match.group(1);setting=null;}
            }
            if(current!=null && depth==1 && setting==null) {
                var match=DEFAULT.matcher(line); if(match.matches())setting=match.group(1);
            }
            depth+=count(line,'{')-count(line,'}');
            if(depth<0)throw new IOException("unbalanced vanilla game-rule declaration braces");
            if(current!=null && depth==0) {
                if(setting==null)throw new IOException("vanilla game rule has no declared default: "+current);
                rows.add(new Rule(current,setting));current=null;
            }
        }
        if(current!=null || depth!=0)throw new IOException("unbalanced vanilla game-rule declaration braces");
        if(rows.size()<70 || rows.size()>4096)throw new IOException("vanilla rule profile outside reviewed finite contract");
        int count=rows.size(); rows.add(new Rule("xar_enabled",mode.setting()));
        rows.add(new Rule("xar_inheritance","xar_inherit_100"));rows.add(new Rule("xar_score_basis","xar_score_growth"));
        if(new HashSet<>(rows.stream().map(Rule::setting).toList()).size()!=rows.size())
            throw new IOException("combined game-rule profile contains duplicate settings");
        try{return new Contract(actualSource,count,rows,sha(profileBytes(rows)),false);}
        catch(IllegalArgumentException invalid){throw new IOException("invalid actual game-rule contract",invalid);}
    }
    public static byte[] profileBytes(List<Rule> rows) {
        var result=new StringBuilder("[");
        for(Rule row:rows){if(result.length()>1)result.append(',');result.append("{\"rule\":\"").append(row.rule())
                .append("\",\"setting\":\"").append(row.setting()).append("\"}");}
        return result.append(']').toString().getBytes(StandardCharsets.US_ASCII);
    }
    public static byte[] renderPresets(Contract contract) {
        Objects.requireNonNull(contract);
        return ("game_rules_preset={\n\tname=\"LastAppliedRules\"\n\tsetting={ "+
                String.join(" ",contract.profile().stream().map(Rule::setting).toList())+
                " }\n\tironman=no\n}\n").getBytes(StandardCharsets.UTF_8);
    }
    private static int count(String text,char wanted){int count=0;for(int i=0;i<text.length();i++)if(text.charAt(i)==wanted)count++;return count;}
    private static void token(String text){require(text!=null && text.matches("[A-Za-z0-9_]{1,256}"),"finite native rule token required");}
    public static String sha(byte[] bytes){try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
}
