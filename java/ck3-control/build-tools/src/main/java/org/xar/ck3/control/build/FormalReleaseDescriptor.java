package org.xar.ck3.control.build;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Java projection of the source-bound native publication registry. No remote operation or write. */
public final class FormalReleaseDescriptor {
    public static final String REGISTRY_PATH="ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py";
    public static final String REGISTRY_BLOB="947c26f2e36443a7f564b09d0975f2c96edf6baa";
    public static final String REGISTRY_SHA256="47ff303baf94867db406ec9dab52037b83551b8c39a8dff0a0bdceafed7c2d90";
    public static final int REGISTRY_BYTES=3226;
    private static final Pattern SUPPORTED=Pattern.compile("^\\s*supported_version\\s*=\\s*\"([^\"\\r\\n]+)\"\\s*(?:#.*)?$",Pattern.MULTILINE|Pattern.UNICODE_CHARACTER_CLASS);
    private static final Pattern ASSIGNMENT=Pattern.compile("^\\s*supported_version\\s*=",Pattern.MULTILINE);
    private static final Pattern VERSION=Pattern.compile("([0-9]+)\\.([0-9]+)(?:\\.(?:[0-9]+|\\*)){0,2}");
    private static final Pattern COMPATIBILITY=Pattern.compile("[0-9]+\\.[0-9]+(?: '[^'\\r\\n]+')?");
    private static final Pattern TAGS=Pattern.compile("\\btags\\s*=\\s*\\{([^{}]*)\\}",Pattern.DOTALL|Pattern.UNICODE_CHARACTER_CLASS);
    private static final Pattern TOKEN=Pattern.compile("#[^\\r\\n]*|\"(?:[^\"\\\\]|\\\\.)*\"");
    private FormalReleaseDescriptor(){ }

    /** Every migrated registry semantic is admitted only for the exact original Git object. */
    public static void requireRegistry(byte[] original)throws IOException {
        if(original.length!=REGISTRY_BYTES||!NativeRunProfileRules.sha(original).equals(REGISTRY_SHA256))
            throw new IOException("native compatibility registry changed; migrate its real producer and consumers before release");
    }
    public static byte[] project(byte[] original,byte[] registry)throws IOException {
        requireRegistry(registry);String descriptor=decode(original);
        String label=compatibilityLabel(descriptor);if(label==null)return original.clone();
        Matcher blocks=TAGS.matcher(descriptor);
        if(!blocks.find())throw new IOException("descriptor must contain exactly one tags block");
        int begin=blocks.start(1),end=blocks.end(1);String body=blocks.group(1);
        if(blocks.find())throw new IOException("descriptor must contain exactly one tags block");
        record Token(int begin,int end,String value){ }
        var versions=new ArrayList<Token>();Matcher tokens=TOKEN.matcher(body);
        while(tokens.find())if(tokens.group().startsWith("\"")){
            String value=ControlBuild.strictMapper().readValue(tokens.group(),String.class);
            if(COMPATIBILITY.matcher(value).matches())versions.add(new Token(tokens.start(),tokens.end(),value));
        }
        if(versions.size()==1&&versions.getFirst().value().equals(label))return original.clone();
        for(int i=versions.size()-1;i>=0;i--){
            Token token=versions.get(i);int left=token.begin(),right=token.end();
            int lineStart=body.lastIndexOf('\n',left-1)+1,lineEnd=body.indexOf('\n',right);
            if(lineEnd>=0&&pythonStrip(body.substring(lineStart,left)).isEmpty()&&pythonStrip(body.substring(right,lineEnd)).isEmpty()){
                left=lineStart;right=lineEnd+1;
            }
            body=body.substring(0,left)+body.substring(right);
        }
        String encoded=ControlBuild.strictMapper().writeValueAsString(label);
        if(body.contains("\n")){
            String newline=body.contains("\r\n")?"\r\n":"\n";
            Matcher indentation=Pattern.compile("(?:^|\\n)([ \\t]+)\"").matcher(body);
            String indent=indentation.find()?indentation.group(1):"\t";
            Matcher closing=Pattern.compile("[ \\t]*$").matcher(body);closing.find();String suffix=closing.group();
            body=body.substring(0,body.length()-suffix.length());
            if(!body.endsWith("\n"))body+=newline;
            body+=indent+encoded+newline+suffix;
        }else body=stripTrailing(body)+" "+encoded+" ";
        return encode(descriptor.substring(0,begin)+body+descriptor.substring(end),hasBom(original));
    }
    /** Package-visible for producer-to-consumer regression, with no qualification side effect. */
    static String compatibilityLabel(String descriptor)throws IOException {
        while(descriptor.startsWith("\ufeff"))descriptor=descriptor.substring(1);
        Matcher matches=SUPPORTED.matcher(descriptor);if(!matches.find())throw new IOException("exactly one supported_version required");
        String raw=matches.group(1);if(matches.find()||ASSIGNMENT.matcher(descriptor).results().count()!=1)
            throw new IOException("exactly one supported_version required");
        Matcher version=VERSION.matcher(raw);if(!version.matches())throw new IOException("invalid supported_version");
        BigInteger major=new BigInteger(version.group(1)),minor=new BigInteger(version.group(2));
        if(major.compareTo(BigInteger.ONE)<0||(major.equals(BigInteger.ONE)&&minor.compareTo(BigInteger.valueOf(20))<0))return null;
        if(major.equals(BigInteger.ONE)&&minor.equals(BigInteger.valueOf(20)))return "1.20 'Crozier'";
        throw new IOException("no confirmed CK3 Workshop compatibility tag for "+major+"."+minor);
    }
    static boolean hasBom(byte[] bytes){return bytes.length>=3&&bytes[0]==(byte)0xef&&bytes[1]==(byte)0xbb&&bytes[2]==(byte)0xbf;}
    static String decode(byte[] bytes)throws IOException {
        int begin=hasBom(bytes)?3:0;
        try{return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes,begin,bytes.length-begin)).toString();}
        catch(CharacterCodingException invalid){throw new IOException("release text is not strict UTF-8",invalid);}
    }
    static byte[] encode(String text,boolean bom){
        byte[] bytes=text.getBytes(StandardCharsets.UTF_8);if(!bom)return bytes;
        byte[] result=new byte[bytes.length+3];result[0]=(byte)0xef;result[1]=(byte)0xbb;result[2]=(byte)0xbf;System.arraycopy(bytes,0,result,3,bytes.length);return result;
    }
    static boolean pythonWhitespace(char ch){return Character.isWhitespace(ch)||Character.isSpaceChar(ch)||ch=='\u0085';}
    static String pythonStrip(String text){int start=0;while(start<text.length()&&pythonWhitespace(text.charAt(start)))start++;return stripTrailing(text.substring(start));}
    private static String stripTrailing(String text){int end=text.length();while(end>0&&pythonWhitespace(text.charAt(end-1)))end--;return text.substring(0,end);}
}

