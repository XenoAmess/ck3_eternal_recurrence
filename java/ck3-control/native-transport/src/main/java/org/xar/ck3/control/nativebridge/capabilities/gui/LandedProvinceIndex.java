package org.xar.ck3.control.nativebridge.capabilities.gui;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.regex.Pattern;
import org.xar.ck3.control.contracts.ExactRef;

/** Installed title-file parser from war_hotspot_camera.py; no game command or viewport inference. */
public final class LandedProvinceIndex {
    private static final Pattern TOKEN=Pattern.compile("\"(?:\\\\.|[^\"\\\\])*\"|#[^\\r\\n]*|[{}=]|[A-Za-z_][A-Za-z0-9_]*|[0-9]+");
    public record ProvinceTitle(int province,String barony,Optional<String> county){public ProvinceTitle{county=java.util.Objects.requireNonNull(county);}}
    private final List<ProvinceTitle> provinces;private final List<ExactRef> sourceFiles;
    private LandedProvinceIndex(List<ProvinceTitle> provinces,List<ExactRef> files){this.provinces=List.copyOf(provinces);sourceFiles=List.copyOf(files);}
    public List<ProvinceTitle> provinces(){return provinces;}public List<ExactRef> sourceFiles(){return sourceFiles;}
    public Optional<ProvinceTitle> province(int id){return provinces.stream().filter(p->p.province()==id).findFirst();}
    public static LandedProvinceIndex fromGameDirectory(Path gameDirectory)throws IOException{
        Path root=gameDirectory.toRealPath().resolve("game/common/landed_titles");List<Path> files;
        try(var stream=Files.list(root)){files=stream.filter(p->p.getFileName().toString().endsWith(".txt")).sorted().toList();}
        if(files.isEmpty())throw new IOException("installation has no landed-title files");List<ProvinceTitle> values=new ArrayList<>();List<ExactRef> refs=new ArrayList<>();
        for(Path file:files){byte[] before=Files.readAllBytes(file);if(before.length>64*1024*1024)throw new IOException("landed-title source exceeds finite budget");
            values=merge(values,parse(new String(before,StandardCharsets.UTF_8).replaceFirst("^\\uFEFF","")));
            byte[] after=Files.readAllBytes(file);if(!java.util.Arrays.equals(before,after))throw new IOException("installed title source changed during parse");refs.add(new ExactRef(file.toRealPath().toString(),before.length,GuiJson.sha256(before)));}
        if(values.isEmpty())throw new IOException("installed title files yielded no actual province mapping");values.sort(Comparator.comparingInt(ProvinceTitle::province));return new LandedProvinceIndex(values,refs);
    }
    public static List<ProvinceTitle> parse(String source){List<String> tokens=new ArrayList<>();var m=TOKEN.matcher(source);while(m.find()){String t=m.group();if(!t.startsWith("#")&&!t.startsWith("\""))tokens.add(t);}
        List<String> scopes=new ArrayList<>();List<ProvinceTitle> rows=new ArrayList<>();
        for(int i=0;i<tokens.size();i++){String token=tokens.get(i);if(token.equals("{")){scopes.add(i>=2&&tokens.get(i-1).equals("=")?tokens.get(i-2):"");}
            else if(token.equals("}")){GuiJson.need(!scopes.isEmpty(),"unbalanced installed title braces");scopes.removeLast();}
            else if(token.equals("province")&&i+2<tokens.size()&&tokens.get(i+1).equals("=")&&tokens.get(i+2).matches("[0-9]+")&&!scopes.isEmpty()&&scopes.getLast().startsWith("b_")){
                int province=Integer.parseInt(tokens.get(i+2));if(province<=0)continue;String barony=scopes.getLast();Optional<String> county=Optional.empty();for(int j=scopes.size()-1;j>=0;j--)if(scopes.get(j).startsWith("c_")){county=Optional.of(scopes.get(j));break;}
                rows=merge(rows,List.of(new ProvinceTitle(province,barony,county)));}}
        GuiJson.need(scopes.isEmpty(),"unbalanced installed title braces");return List.copyOf(rows);
    }
    private static List<ProvinceTitle> merge(List<ProvinceTitle> prior,List<ProvinceTitle> incoming){List<ProvinceTitle> merged=new ArrayList<>(prior);for(ProvinceTitle p:incoming){var old=merged.stream().filter(v->v.province()==p.province()).findFirst();
        if(old.isPresent())GuiJson.need(old.orElseThrow().barony().equals(p.barony()),"province maps to two installed baronies");else merged.add(p);}return merged;}
    public void verifySourcesUnchanged()throws IOException{for(ExactRef ref:sourceFiles){byte[] actual=Files.readAllBytes(Path.of(ref.path()));if(actual.length!=ref.bytes()||!GuiJson.sha256(actual).equals(ref.sha256()))throw new IOException("installed landed-title source identity changed");}}
}
