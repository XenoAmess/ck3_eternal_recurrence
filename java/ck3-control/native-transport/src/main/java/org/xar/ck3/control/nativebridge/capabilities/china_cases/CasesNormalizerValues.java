package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.*;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.*;
import java.util.function.Function;
import java.util.function.Supplier;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/** Internal value operations for the statically lowered original normalizers.
 * The public boundary remains JsonNode -> validated domain data. No source, AST, bytecode,
 * arbitrary callback, Python process or untyped Object map is accepted by production. */
final class CasesNormalizerValues {
    private CasesNormalizerValues() {}
    sealed interface V permits Nil,Missing,B,Num,Fp,S,Seq,D,SetV,Rx,Gen,T {}
    enum Nil implements V { VALUE }
    enum Missing implements V { REQUIRED }
    record B(boolean value) implements V {}
    record Num(BigInteger value) implements V { Num { Objects.requireNonNull(value); } }
    record Fp(double value) implements V {}
    record S(String value) implements V { S { Objects.requireNonNull(value); } }
    // Mutable containers are confined to one normalizer invocation, matching original copies/aliases.
    record Seq(boolean tuple,ArrayList<V> values) implements V {}
    record D(LinkedHashMap<String,V> values) implements V {}
    record SetV(ArrayList<V> values) implements V {}
    record Rx(Pattern pattern) implements V {}
    record Gen(Supplier<Stream<V>> values) implements V {}
    enum T implements V { INT,BOOL,STR,DICT,LIST,TUPLE,SET,FLOAT,NONE,OTHER }
    static final V NONE=Nil.VALUE,REQUIRED=Missing.REQUIRED,TRUE=new B(true),FALSE=new B(false);
    static V b(boolean x){return x?TRUE:FALSE;}
    static V n(String x){return new Num(new BigInteger(x));}
    static V s(String x){return new S(x);}
    static V fp(double x){return new Fp(x);}
    static final class Rejected extends IllegalArgumentException {
        private static final long serialVersionUID=1L;
        Rejected(String message){super(Objects.requireNonNull(message));}
    }
    @FunctionalInterface interface Dispatch { V call(String name,Args args); }
    record Kw(String name,V value) {}
    record Args(List<V> positional,List<Kw> keywords) {
        Args {positional=List.copyOf(positional);keywords=List.copyOf(keywords);}
    }
    record Param(String name,V fallback) {}
    record Sig(List<Param> positional,List<Param> keywordOnly,String vararg) {}
    static final class E {
        final Map<String,V> globals;
        final LinkedHashMap<String,V> locals;
        final Dispatch dispatch;
        E(Map<String,V> globals,Dispatch dispatch){this(globals,new LinkedHashMap<>(),dispatch);}
        E(Map<String,V> globals,LinkedHashMap<String,V> locals,Dispatch dispatch){
            this.globals=globals;this.locals=locals;this.dispatch=dispatch;
        }
        V get(String name){
            if(locals.containsKey(name))return locals.get(name);
            if(globals.containsKey(name))return globals.get(name);
            return switch(name){
                case "int"->T.INT;case "bool"->T.BOOL;case "str"->T.STR;case "dict"->T.DICT;
                case "list"->T.LIST;case "tuple"->T.TUPLE;case "set"->T.SET;case "float"->T.FLOAT;
                default->throw new IllegalStateException("unbound lowered name: "+name);
            };
        }
        void put(String name,V value){locals.put(name,Objects.requireNonNull(value));}
        E copy(){return new E(globals,new LinkedHashMap<>(locals),dispatch);}
    }
    static E bind(Map<String,V> globals,Dispatch dispatch,Sig sig,Args args){
        E e=new E(globals,dispatch);var seen=new HashSet<String>();
        for(int i=0;i<sig.positional.size();i++){
            Param p=sig.positional.get(i);
            if(i<args.positional.size()){e.put(p.name,args.positional.get(i));seen.add(p.name);}
            else if(p.fallback!=REQUIRED)e.put(p.name,p.fallback);
        }
        if(sig.vararg!=null)e.put(sig.vararg,new Seq(true,new ArrayList<>(
                args.positional.subList(Math.min(sig.positional.size(),args.positional.size()),args.positional.size()))));
        else if(args.positional.size()>sig.positional.size())throw new IllegalStateException("lowered call arity");
        for(Param p:sig.keywordOnly)if(p.fallback!=REQUIRED)e.put(p.name,p.fallback);
        for(Kw kw:args.keywords){
            boolean known=Stream.concat(sig.positional.stream(),sig.keywordOnly.stream()).anyMatch(p->p.name.equals(kw.name));
            if(!known||!seen.add(kw.name))throw new IllegalStateException("lowered keyword mismatch: "+kw.name);
            e.put(kw.name,kw.value);
        }
        for(Param p:sig.positional)if(!e.locals.containsKey(p.name))throw new IllegalStateException("lowered required parameter: "+p.name);
        for(Param p:sig.keywordOnly)if(!e.locals.containsKey(p.name))throw new IllegalStateException("lowered required keyword: "+p.name);
        return e;
    }
    record Part(V value,boolean spread) {}
    static Part p(V v){return new Part(v,false);}
    static Part spread(V v){return new Part(v,true);}
    static ArrayList<V> flatten(Part...parts){
        var result=new ArrayList<V>();for(Part p:parts){if(p.spread)result.addAll(iter(p.value));else result.add(p.value);}return result;
    }
    static Args args(Part[] parts,Kw...keywords){return new Args(flatten(parts),List.of(keywords));}
    static V seq(boolean tuple,Part...parts){return new Seq(tuple,flatten(parts));}
    static V set(Part...parts){var result=new ArrayList<V>();for(V v:flatten(parts))if(result.stream().noneMatch(x->eq(x,v)))result.add(v);return new SetV(result);}
    sealed interface Entry permits Item,Expansion {}
    record Item(V key,V value) implements Entry {}
    record Expansion(V dictionary) implements Entry {}
    static V dict(Entry...entries){
        var result=new LinkedHashMap<String,V>();
        for(Entry entry:entries){
            if(entry instanceof Item i)result.put(text(i.key),i.value);
            else if(entry instanceof Expansion x)result.putAll(dictionary(x.dictionary).values);
        }return new D(result);
    }
    static V dictFrom(Iterable<V> pairs){
        var result=new LinkedHashMap<String,V>();
        for(V pair:pairs){List<V> p=iter(pair);if(p.size()!=2)throw new IllegalStateException("dictionary pair");result.put(text(p.get(0)),p.get(1));}
        return new D(result);
    }
    static String text(V value){if(value instanceof S x)return x.value;throw new IllegalStateException("lowered string expected");}
    static D dictionary(V value){if(value instanceof D x)return x;throw new IllegalStateException("lowered dictionary expected");}
    static BigInteger integer(V value){
        if(value instanceof Num x)return x.value;
        if(value instanceof B x)return x.value?BigInteger.ONE:BigInteger.ZERO;
        throw new IllegalStateException("lowered integer expected");
    }
    static boolean numeric(V v){return v instanceof Num||v instanceof B||v instanceof Fp;}
    static BigDecimal decimal(V v){return v instanceof Fp f?new BigDecimal(f.value):new BigDecimal(integer(v));}
    static List<V> iter(V value){
        if(value instanceof Seq x)return x.values;
        if(value instanceof SetV x)return x.values;
        if(value instanceof D x)return x.values.keySet().stream().map(k->s(k)).toList();
        if(value instanceof S x)return x.value.codePoints().mapToObj(c->s(new String(Character.toChars(c)))).toList();
        if(value instanceof Gen x){try(Stream<V> st=x.values.get()){return st.toList();}}
        throw new IllegalStateException("lowered iterable expected");
    }
    static Stream<V> stream(V value){return value instanceof Gen x?x.values.get():iter(value).stream();}
    static boolean truth(V v){
        if(v==NONE)return false;
        if(v instanceof B x)return x.value;
        if(v instanceof Num x)return x.value.signum()!=0;
        if(v instanceof Fp x)return x.value!=0;
        if(v instanceof S x)return !x.value.isEmpty();
        if(v instanceof Seq x)return !x.values.isEmpty();
        if(v instanceof SetV x)return !x.values.isEmpty();
        if(v instanceof D x)return !x.values.isEmpty();
        return true;
    }
    static boolean eq(V a,V b){
        if(numeric(a)&&numeric(b)){
            if(nonfinite(a)||nonfinite(b))return a instanceof Fp x&&b instanceof Fp y&&x.value==y.value;
            return decimal(a).compareTo(decimal(b))==0;
        }
        if(a==NONE||b==NONE)return a==b;
        if(a instanceof S x&&b instanceof S y)return x.value.equals(y.value);
        if(a instanceof T||b instanceof T)return a==b;
        if(a instanceof Seq x&&b instanceof Seq y){
            if(x.tuple!=y.tuple||x.values.size()!=y.values.size())return false;
            for(int i=0;i<x.values.size();i++)if(!eq(x.values.get(i),y.values.get(i)))return false;return true;
        }
        if(a instanceof D x&&b instanceof D y){
            if(!x.values.keySet().equals(y.values.keySet()))return false;
            for(String k:x.values.keySet())if(!eq(x.values.get(k),y.values.get(k)))return false;return true;
        }
        if(a instanceof SetV x&&b instanceof SetV y)return x.values.size()==y.values.size()&&x.values.stream().allMatch(v->contains(b,v));
        return a==b;
    }
    static boolean contains(V container,V member){
        if(container instanceof SetV&&(member instanceof D||member instanceof Seq q&&!q.tuple||member instanceof SetV))
            throw new IllegalStateException("original unchecked unhashable membership");
        if(container instanceof D d)return member instanceof S s&&d.values.containsKey(s.value);
        if(container instanceof S s)return s.value.contains(text(member));
        return iter(container).stream().anyMatch(x->eq(x,member));
    }
    static V get(V container,V key){
        if(container instanceof D d){
            String k=text(key);if(!d.values.containsKey(k))throw new IllegalStateException("original unchecked missing key: "+k);
            return d.values.get(k);
        }
        List<V> values=iter(container);int i=integer(key).intValueExact();return values.get(i<0?values.size()+i:i);
    }
    static void put(V container,V key,V value){dictionary(container).values.put(text(key),value);}
    static V attribute(V container,String field){return get(container,s(field));}
    enum Cmp { EQ,NE,IS,IS_NOT,LT,LE,GT,GE,IN,NOT_IN }
    record Comparison(Cmp op,Function<E,V> right) {}
    static V compare(E e,V first,Comparison...rest){
        V left=first;
        for(Comparison c:rest){
            V right=c.right.apply(e);boolean unordered=nan(left)||nan(right);boolean ok=switch(c.op){
                case EQ->eq(left,right);case NE->!eq(left,right);case IS->left==right;case IS_NOT->left!=right;
                case IN->contains(right,left);case NOT_IN->!contains(right,left);
                case LT->!unordered&&order(left,right)<0;case LE->!unordered&&order(left,right)<=0;case GT->!unordered&&order(left,right)>0;case GE->!unordered&&order(left,right)>=0;
            };
            if(!ok)return FALSE;left=right;
        }return TRUE;
    }
    static boolean nonfinite(V v){return v instanceof Fp f&&!Double.isFinite(f.value);}
    static boolean nan(V v){return v instanceof Fp f&&Double.isNaN(f.value);}
    static int order(V a,V b){
        if(nonfinite(a))return nonfinite(b)?Double.compare(((Fp)a).value,((Fp)b).value):(((Fp)a).value>0?1:-1);
        if(nonfinite(b))return ((Fp)b).value>0?-1:1;
        if(numeric(a)&&numeric(b))return decimal(a).compareTo(decimal(b));
        if(a instanceof S x&&b instanceof S y)return x.value.compareTo(y.value);
        throw new IllegalStateException("lowered order domain");
    }
    enum Op { ADD,SUB,POW,OR }
    static V binary(Op op,V a,V b){
        if(a instanceof SetV&&b instanceof SetV){
            var values=new ArrayList<V>(iter(a));
            if(op==Op.SUB)values.removeIf(v->contains(b,v));
            else if(op==Op.OR){for(V v:iter(b))if(values.stream().noneMatch(x->eq(x,v)))values.add(v);}
            else throw new IllegalStateException("set operator");return new SetV(values);
        }
        if(op==Op.ADD&&a instanceof S x&&b instanceof S y)return s(x.value+y.value);
        return new Num(switch(op){
            case ADD->integer(a).add(integer(b));case SUB->integer(a).subtract(integer(b));
            case POW->integer(a).pow(integer(b).intValueExact());case OR->integer(a).or(integer(b));
        });
    }
    static V negate(V v){return v instanceof Fp f?fp(-f.value):new Num(integer(v).negate());}
    @SafeVarargs static V and(E e,Function<E,V>...parts){V value=TRUE;for(var p:parts){value=p.apply(e);if(!truth(value))return value;}return value;}
    @SafeVarargs static V or(E e,Function<E,V>...parts){V value=FALSE;for(var p:parts){value=p.apply(e);if(truth(value))return value;}return value;}
    static T type(V v){
        if(v==NONE)return T.NONE;if(v instanceof B)return T.BOOL;if(v instanceof Num)return T.INT;
        if(v instanceof Fp)return T.FLOAT;if(v instanceof S)return T.STR;if(v instanceof D)return T.DICT;
        if(v instanceof SetV)return T.SET;if(v instanceof Seq x)return x.tuple?T.TUPLE:T.LIST;return T.OTHER;
    }
    static boolean instance(V value,V types){
        if(types instanceof Seq s)return s.values.stream().anyMatch(t->instance(value,t));
        return type(value)==types||(types==T.INT&&value instanceof B);
    }
    static V call(E e,String name,Args a){
        List<V> p=a.positional;
        return switch(name){
            case "isinstance"->b(instance(p.get(0),p.get(1)));
            case "type"->type(p.get(0));
            case "bool"->b(truth(p.get(0)));
            case "int"->p.get(0)instanceof Fp f?new Num(new BigDecimal(f.value).toBigInteger()):
                    p.get(0)instanceof S s?n(s.value):new Num(integer(p.get(0)));
            case "str"->s(py(p.get(0)));
            case "dict"->new D(new LinkedHashMap<>(dictionary(p.get(0)).values));
            case "set","frozenset"->set(iter(p.get(0)).stream().map(CasesNormalizerValues::p).toArray(Part[]::new));
            case "list"->new Seq(false,new ArrayList<>(iter(p.get(0))));
            case "tuple"->new Seq(true,new ArrayList<>(iter(p.get(0))));
            case "all"->{try(Stream<V> st=stream(p.get(0))){yield b(st.allMatch(CasesNormalizerValues::truth));}}
            case "any"->{try(Stream<V> st=stream(p.get(0))){yield b(st.anyMatch(CasesNormalizerValues::truth));}}
            case "sum"->{V result=n("0");try(Stream<V> st=stream(p.get(0))){for(var it=st.iterator();it.hasNext();)result=binary(Op.ADD,result,it.next());}yield result;}
            case "len"->new Num(BigInteger.valueOf(p.get(0)instanceof S s?s.value.codePointCount(0,s.value.length()):iter(p.get(0)).size()));
            case "enumerate"->{var result=new ArrayList<V>();int i=0;for(V v:iter(p.get(0)))result.add(seq(true,p(n(Integer.toString(i++))),p(v)));yield new Seq(false,result);}
            default->e.dispatch.call(name,a);
        };
    }
    static V method(V receiver,String name,Args a){
        List<V> p=a.positional;
        return switch(name){
            case "get"->{D d=dictionary(receiver);yield d.values.getOrDefault(text(p.get(0)),p.size()>1?p.get(1):NONE);}
            case "items"->{var result=new ArrayList<V>();for(var x:dictionary(receiver).values.entrySet())result.add(seq(true,p(s(x.getKey())),p(x.getValue())));yield new Seq(false,result);}
            case "values"->new Seq(false,new ArrayList<>(dictionary(receiver).values.values()));
            case "append"->{if(!(receiver instanceof Seq x)||x.tuple)throw new IllegalStateException("append domain");x.values.add(p.get(0));yield NONE;}
            case "update"->{dictionary(receiver).values.putAll(dictionary(p.get(0)).values);yield NONE;}
            case "startswith"->b(text(receiver).startsWith(text(p.get(0))));
            case "fullmatch"->{if(!(receiver instanceof Rx rx))throw new IllegalStateException("regex domain");yield b(rx.pattern.matcher(text(p.get(0))).matches());}
            default->throw new IllegalStateException("unlowered method: "+name);
        };
    }
    sealed interface Target permits NameTarget,TupleTarget {}
    record NameTarget(String name) implements Target {}
    record TupleTarget(List<Target> names) implements Target {}
    static void assign(E e,Target target,V value){
        if(target instanceof NameTarget n)e.put(n.name,value);
        else if(target instanceof TupleTarget t){
            List<V> values=iter(value);if(values.size()!=t.names.size())throw new IllegalStateException("unpack arity");
            for(int i=0;i<values.size();i++)assign(e,t.names.get(i),values.get(i));
        }
    }
    record Clause(Target target,Function<E,V> source,List<Function<E,V>> filters) {}
    static V generator(E outer,Function<E,V> value,Clause...clauses){
        return new Gen(()->generate(outer,value,clauses,0));
    }
    private static Stream<V> generate(E outer,Function<E,V> value,Clause[] clauses,int index){
        if(index==clauses.length)return Stream.of(value.apply(outer));
        Clause c=clauses[index];
        return stream(c.source.apply(outer)).flatMap(v->{
            E child=outer.copy();assign(child,c.target,v);
            if(c.filters.stream().anyMatch(f->!truth(f.apply(child))))return Stream.empty();
            return generate(child,value,clauses,index+1);
        });
    }
    static String py(V value){
        if(value==NONE)return "None";if(value instanceof S x)return x.value;if(value instanceof Num x)return x.value.toString();
        if(value instanceof B x)return x.value?"True":"False";if(value instanceof Fp x)return Double.toString(x.value);
        if(value instanceof T x)return "<class '"+x.name().toLowerCase(Locale.ROOT)+"'>";
        if(value instanceof Seq x){
            String joined=String.join(", ",x.values.stream().map(CasesNormalizerValues::repr).toList());
            return x.tuple?"("+joined+(x.values.size()==1?",":"")+")":"["+joined+"]";
        }
        if(value instanceof SetV x)return x.values.isEmpty()?"set()":"{"+String.join(", ",x.values.stream().map(CasesNormalizerValues::repr).toList())+"}";
        if(value instanceof D x)return "{"+String.join(", ",x.values.entrySet().stream().map(p->repr(s(p.getKey()))+": "+repr(p.getValue())).toList())+"}";
        throw new IllegalStateException("unserializable lowered value");
    }
    static String repr(V value){
        if(!(value instanceof S s))return py(value);
        String q=s.value.contains("'")&&!s.value.contains("\"")?"\"":"'";
        return q+s.value.replace("\\","\\\\").replace(q,"\\"+q).replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")+q;
    }
    static V joined(V...values){var result=new StringBuilder();for(V v:values)result.append(py(v));return s(result.toString());}
    static V regex(String pattern){return new Rx(Pattern.compile(pattern));}
    static V fromJson(JsonNode node){
        if(node==null)throw new IllegalStateException("missing JSON is not null");if(node.isNull())return NONE;
        if(node.isBoolean())return b(node.booleanValue());if(node.isIntegralNumber())return new Num(node.bigIntegerValue());
        if(node.isFloatingPointNumber())return fp(node.doubleValue());if(node.isTextual())return s(node.textValue());
        if(node.isArray()){var result=new ArrayList<V>();for(JsonNode x:node)result.add(fromJson(x));return new Seq(false,result);}
        if(node.isObject()){var result=new LinkedHashMap<String,V>();node.properties().forEach(x->result.put(x.getKey(),fromJson(x.getValue())));return new D(result);}
        throw new IllegalStateException("unsupported JSON value");
    }
    static JsonNode toJson(V value){
        JsonNodeFactory f=JsonNodeFactory.instance;
        if(value==NONE)return f.nullNode();if(value instanceof B x)return f.booleanNode(x.value);
        if(value instanceof Num x)return f.numberNode(x.value);if(value instanceof Fp x)return f.numberNode(x.value);
        if(value instanceof S x)return f.textNode(x.value);
        if(value instanceof Seq x){ArrayNode a=f.arrayNode();x.values.forEach(v->a.add(toJson(v)));return a;}
        if(value instanceof D x){ObjectNode o=f.objectNode();x.values.forEach((k,v)->o.set(k,toJson(v)));return o;}
        throw new IllegalStateException("normalizer returned a non-JSON value");
    }
}
