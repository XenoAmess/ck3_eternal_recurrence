package com.xenoamess.kaishek.cli;

import com.xenoamess.kaishek.syntax.CstNode;
import com.xenoamess.kaishek.syntax.Parser;
import com.xenoamess.kaishek.syntax.ParseResult;
import com.xenoamess.kaishek.syntax.SyntaxKind;
import com.xenoamess.kaishek.validator.Validator;
import com.xenoamess.kaishek.profile.Ck3Profile11906;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.stream.Stream;

/** Dependency-free batch entry point. It intentionally never loads Quarkus. */
public final class KaishekCli {
  private static final String VERSION = "0.1.0-cli";
  private static final String EXE_SHA = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
  public static void main(String[] args) { System.exit(run(args, System.out, System.err)); }

  static int run(String[] args, PrintStream out, PrintStream err) {
    if (args.length == 0 || "--help".equals(args[0]) || "-h".equals(args[0])) { usage(out); return 0; }
    if ("--version".equals(args[0]) || "-V".equals(args[0])) { out.println(VERSION); return 0; }
    String command = args[0].toLowerCase(Locale.ROOT);
    try {
      return switch (command) {
        case "parse" -> parse(args, out);
        case "validate" -> validate(args, out);
        case "hash" -> hash(args, out);
        case "corpus" -> corpus(args, out);
        case "profile", "profiles" -> profile(args, out);
        default -> unsupported("command:" + command, out);
      };
    } catch (IllegalArgumentException e) { out.println(json("status", "ERROR", "error", e.getMessage())); return 2; }
      catch (IOException e) { out.println(json("status", "ERROR", "error", e.toString())); return 3; }
  }

  private static int parse(String[] a, PrintStream out) throws IOException {
    byte[] source = readInputBytes(a, 1); ParseResult p = Parser.parse(source);
    StringBuilder b = new StringBuilder("{\"status\":\"PARSED\",\"bytes\":").append(source.length)
      .append(",\"tokens\":").append(countNodes(p.document())).append(",\"blocks\":").append(countKind(p.document(), SyntaxKind.BLOCK))
      .append(",\"diagnostics\":[");
    for (int i=0;i<p.diagnostics().size();i++) {
      var x=p.diagnostics().get(i);
      if(i>0)b.append(',');
      // Offsets are byte offsets and therefore part of the numeric JSON
      // contract, not strings.  Keeping them numeric also lets callers sort
      // and compare diagnostics without a second coercion step.
      b.append("{\"code\":").append(q(x.code()))
          .append(",\"message\":").append(q(x.message()))
          .append(",\"offset\":").append(x.span().start()).append('}');
    }
    out.println(b.append("],\"roundTrip\":").append(!p.hasErrors()).append('}'));
    return p.hasErrors() ? 1 : 0;
  }
  private static int validate(String[] a, PrintStream out) throws IOException {
    Path inputPath = pathOption(a, 1);
    byte[] source = readInputBytes(a, 1);
    String profile = option(a, "--profile", "ck3-1.19.0.6");
    ParseResult p = Parser.parse(source);
    List<String> d = new ArrayList<>(); p.diagnostics().forEach(x -> d.add(x.code()));
    // Only syntax checks are currently certified; schema/profile semantics remain explicit.
    boolean known = profile.equals("ck3-1.19.0.6") || profile.equals("ck3-1.19.0.6-zg361");
    if (!known) { out.println(json("status","UNSUPPORTED","reason","profile-not-registered","profile",profile)); return 4; }
    List<String> semantic = new ArrayList<>();
    boolean semanticSupported = profile.equals("ck3-1.19.0.6") && inputPath != null;
    if (semanticSupported && !p.hasErrors()) {
      // The ParseResult overload intentionally includes syntax diagnostics for
      // library callers.  The CLI reports syntax and semantic counts
      // separately, so validate the already parsed document here.
      Validator.validate(p.document(), inputPath.toString(), new Ck3Profile11906())
          .forEach(x -> semantic.add(x.code()));
    }
    boolean invalid = p.hasErrors() || !semantic.isEmpty();
    String semStatus = semanticSupported ? "VALIDATED" : "UNSUPPORTED";
    String status = invalid ? "INVALID" : (semanticSupported ? "VALIDATED" : "UNSUPPORTED");
    out.println("{\"status\":\""+status+"\",\"profile\":"+q(profile)+",\"syntaxDiagnostics\":"+d.size()+",\"semanticDiagnostics\":"+semantic.size()+",\"semantic\":\""+semStatus+"\"}");
    // A supported semantic check must fail the process when it finds a
    // semantic diagnostic.  Previously only syntax diagnostics affected the
    // exit code, making an INVALID response appear successful to CI.
    // Syntax errors are invalid input regardless of whether a file path was
    // supplied.  Only a syntactically valid input whose semantic layer is not
    // available uses the explicit UNSUPPORTED exit code.
    return invalid ? 1 : (!semanticSupported ? 4 : 0);
  }
  private static int hash(String[] a, PrintStream out) throws IOException {
    Path path = pathOption(a, 1); if (path != null && Files.isDirectory(path)) return corpus(a,out);
    byte[] bytes = path == null ? readInputBytes(a,1) : Files.readAllBytes(path);
    out.println("{\"status\":\"OK\",\"algorithm\":\"SHA-256\",\"sha256\":"+q(sha(bytes))+",\"bytes\":"+bytes.length+"}"); return 0;
  }
  private static int corpus(String[] a, PrintStream out) throws IOException {
    Path root = pathOption(a,1); if (root==null) throw new IllegalArgumentException("corpus requires a directory");
    if (!Files.isDirectory(root)) throw new IllegalArgumentException("not a directory: "+root);
     List<Path> files = new ArrayList<>();
     try(Stream<Path> s=Files.walk(root)){
       s.filter(Files::isRegularFile).filter(KaishekCli::isScript)
        .sorted(Comparator.comparing(p -> root.relativize(p).toString().replace('\\','/')))
        .forEach(files::add);
     }
     MessageDigest md = digest(); long bytes=0; int parsed=0, errors=0; List<String> errorFiles = new ArrayList<>();
     for(Path f:files){
       byte[] x=Files.readAllBytes(f); bytes+=x.length;
       String relative = root.relativize(f).toString().replace('\\','/');
       md.update(relative.getBytes(StandardCharsets.UTF_8)); md.update((byte)0); md.update(x);
       ParseResult p=Parser.parse(x); parsed++;
       if(p.hasErrors()){ errors++; errorFiles.add(relative); }
     }
     StringBuilder details = new StringBuilder("[");
     for (int i=0; i<errorFiles.size(); i++) { if (i > 0) details.append(','); details.append(q(errorFiles.get(i))); }
     out.println("{\"status\":\"OK\",\"root\":"+q(root.toString())+",\"files\":"+files.size()+",\"parsed\":"+parsed+",\"errors\":"+errors+",\"errorFiles\":"+details.append(']').toString()+",\"bytes\":"+bytes+",\"corpusSha256\":"+q(hex(md.digest()))+"}"); return errors==0?0:1;
  }
  private static int profile(String[] a, PrintStream out) {
    String positionalId = positional(a, 1);
    String id=option(a,"--id", positionalId == null ? "" : positionalId);
    if (id.isEmpty()) { out.println("{\"status\":\"OK\",\"profiles\":[{\"id\":\"ck3-1.19.0.6\",\"game\":\"Crusader Kings III\",\"build\":\"1.19.0.6\",\"semantic\":\"static\"},{\"id\":\"ck3-1.19.0.6-zg361\",\"game\":\"Crusader Kings III + mod_zhongguo_style\",\"build\":\"1.19.0.6\",\"semantic\":\"schema-only\"}]}"); return 0; }
    if (!id.equals("ck3-1.19.0.6")&&!id.equals("ck3-1.19.0.6-zg361")) return unsupported("profile:"+id,out);
    String semantic = id.endsWith("-zg361") ? "schema-only" : "static";
    out.println("{\"status\":\"OK\",\"id\":"+q(id)+",\"game\":\"Crusader Kings III\",\"build\":\"1.19.0.6\",\"exeSha256\":"+q(EXE_SHA)+",\"semantic\":"+q(semantic)+",\"runtime\":\"UNSUPPORTED\"}"); return 0;
  }
  private static int unsupported(String reason, PrintStream out){out.println(json("status","UNSUPPORTED","reason",reason)); return 4;}
  private static String readInput(String[] a,int start)throws IOException{return new String(readInputBytes(a,start),StandardCharsets.UTF_8);}

  /**
   * Read an input argument in any option order.  A positional argument that
   * names an existing file is treated as a path; otherwise it is retained as
   * inline source text for the parse/hash convenience form.
   */
  private static byte[] readInputBytes(String[] a,int start)throws IOException{
    Path p=pathOption(a,start);
    if(p!=null)return Files.readAllBytes(p);
    String inline = positional(a,start);
    if(inline!=null)return inline.getBytes(StandardCharsets.UTF_8);
    return System.in.readAllBytes();
  }

  /** Resolve an explicit --file or an existing positional path. */
  private static Path pathOption(String[] a,int start){
    String p=option(a,"--file",null);
    if(p!=null)return Paths.get(p);
    String candidate=positional(a,start);
    if(candidate!=null){Path x=Paths.get(candidate);if(Files.exists(x))return x;}
    return null;
  }

  /**
   * Return the first positional token after the command, skipping value
   * options.  Strict option handling prevents a misspelled/missing option
   * from silently switching a file operation to stdin.
   */
  private static String positional(String[] a,int start){
    boolean endOptions=false;
    String first=null;
    for(int i=start;i<a.length;i++){
      String token=a[i];
      if(token==null)throw new IllegalArgumentException("null argument at index "+i);
      if(endOptions || !token.startsWith("-")){
        if(first!=null)throw new IllegalArgumentException("unexpected argument: "+token);
        first=token;
        continue;
      }
      if("--".equals(token)){endOptions=true;continue;}
      String valueOption=valueOption(token);
      if(valueOption!=null){
        if(token.equals(valueOption)){
          if(++i>=a.length)throw new IllegalArgumentException(valueOption+" requires a value");
          String value=a[i];
          if(value==null||value.isBlank()||value.startsWith("--"))
            throw new IllegalArgumentException(valueOption+" requires a value");
        } else if(token.substring(valueOption.length()+1).isBlank()) {
          throw new IllegalArgumentException(valueOption+" requires a value");
        }
        continue;
      }
      throw new IllegalArgumentException("unknown option: "+token);
    }
    return first;
  }

  /** Return an option value; supports both --key value and --key=value. */
  private static String option(String[] a,String key,String fallback){
    String found=null;
    String equalsPrefix=key+"=";
    for(int i=1;i<a.length;i++){
      String token=a[i];
      if(key.equals(token)){
        if(++i>=a.length)throw new IllegalArgumentException(key+" requires a value");
        String value=a[i];
        if(value==null||value.isBlank()||value.startsWith("--"))
          throw new IllegalArgumentException(key+" requires a value");
        found=value;
      }else if(token!=null&&token.startsWith(equalsPrefix)){
        String value=token.substring(equalsPrefix.length());
        if(value.isBlank())throw new IllegalArgumentException(key+" requires a value");
        found=value;
      }
    }
    return found==null?fallback:found;
  }

  /** Identify a supported value option while scanning positional arguments. */
  private static String valueOption(String token){
    for(String key:List.of("--file","--profile","--id"))
      if(token.equals(key)||token.startsWith(key+"="))return key;
    return null;
  }
  // The Phase 0 corpus contract is deliberately limited to Paradox script
  // sources.  Localization YAML has a different grammar and is reported by
  // a future localization adapter rather than being misclassified here.
  private static boolean isScript(Path p){String n=p.getFileName().toString().toLowerCase(Locale.ROOT);return n.endsWith(".txt")||n.endsWith(".gui");}
  private static MessageDigest digest(){try{return MessageDigest.getInstance("SHA-256");}catch(Exception e){throw new AssertionError(e);}}
  private static String sha(byte[] b){return hex(digest().digest(b));} private static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.ROOT,"%02x",x));return s.toString();}
  private static String q(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\r","\\r").replace("\n","\\n")+"\"";}
  private static String json(String... kv){StringBuilder b=new StringBuilder("{");for(int i=0;i<kv.length;i+=2){if(i>0)b.append(',');b.append(q(kv[i])).append(':').append(q(kv[i+1]));}return b.append('}').toString();}
  private static void usage(PrintStream o){o.println("kaishek-cli "+VERSION+" (pure Java; Quarkus is not started)\nUsage: parse|validate|hash|corpus|profile [--file PATH|PATH]\nUnknown semantics return status UNSUPPORTED.");}

  private static int countNodes(CstNode n){int c=1; for(CstNode x:n.children()) c+=countNodes(x); return c;}
  private static int countKind(CstNode n,SyntaxKind k){int c=n.kind()==k?1:0; for(CstNode x:n.children()) c+=countKind(x,k); return c;}
}
