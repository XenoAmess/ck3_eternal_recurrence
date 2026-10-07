"""Strict source and metadata checks for the four explicit stock grant tools."""
import ast
from pathlib import Path
from r14_metadata_semantics import need,check_revision_schema,source_declarations,number
GRANT_TOOLS={
 'ck3_query_profile_grant_title_picker_v1':('query',['recipient_id','title_full_ids','expected_revision']),
 'ck3_prepare_profile_grant_title_picker_v1':('prepare',['recipient_id','title_full_ids','expected_revision']),
 'ck3_select_profile_grant_title_picker_v1':('select',['recipient_id','title_full_id','desired_selected','expected_selected_title_full_ids','expected_revision']),
 'ck3_send_profile_grant_title_picker_v1':('send',['recipient_id','expected_selected_title_full_ids','expected_revision'])}
def check_id(schema,character=False):
    need(type(schema) is dict and schema.get('type')=='integer','Exact integer full ID schema required')
    if character:
        need(type(schema.get('minimum')) is int and schema['minimum']==1 and type(schema.get('maximum')) is int and schema['maximum']==2**32-2,'Character full ID bounds differ')
    else:
        need(type(schema.get('minimum')) is int and schema['minimum']==0 and type(schema.get('exclusiveMaximum')) is int and schema['exclusiveMaximum']==2**32-1,'Title full ID bounds differ')
def check_grant_tool(tool):
    name=tool.get('name');need(name in GRANT_TOOLS,'Unknown grant tool')
    op,names=GRANT_TOOLS[name];schema=tool.get('inputSchema',{})
    need(schema.get('additionalProperties') is False and schema.get('required')==names and set(schema.get('properties',{}))==set(names),'Exact closed grant argument schema differs')
    p=schema['properties'];check_revision_schema(p['expected_revision']);check_id(p['recipient_id'],True)
    for key in ('title_full_ids','expected_selected_title_full_ids'):
        if key not in p:continue
        array=p[key]
        need(array.get('type')=='array' and array.get('uniqueItems') is True and type(array.get('maxItems')) is int and array['maxItems']==64,'Grant Title set bound/uniqueness differs')
        need(type(array.get('minItems',0)) is int and array.get('minItems',0)==(1 if op=='send' else 0),'Grant selected-set minimum differs')
        check_id(array.get('items'))
    if op=='select':
        check_id(p['title_full_id']);need(p['desired_selected'].get('type')=='boolean','Actual boolean desired state required')
    hints=tool.get('annotations',{})
    # Frozen Prepare/Select omit destructiveHint; official SDK preserves null.
    expected={'readOnlyHint':op=='query','idempotentHint':op=='query','openWorldHint':False,'destructiveHint':False if op=='query' else (True if op=='send' else None)}
    need(all(key in hints and hints[key] is value for key,value in expected.items()),'Stock grant annotations differ')
    return tool
def grant_source_declarations(path):
    result=source_declarations(path)
    tree=ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    aliases={node.targets[0].id:node.value for node in tree.body if isinstance(node,ast.Assign)
             and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
    def field(name,base,values):
        alias=aliases.get(name)
        need(isinstance(alias,ast.Subscript) and isinstance(alias.value,ast.Name) and alias.value.id=='Annotated'
             and isinstance(alias.slice,ast.Tuple),'Strict grant Annotated alias required: '+name)
        pieces=alias.slice.elts
        need(ast.unparse(pieces[0])==base,'Grant annotation base differs: '+name)
        declaration=next((x for x in pieces[1:] if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='Field'),None)
        need(declaration is not None,'Grant Field declaration missing: '+name)
        kw={x.arg:x.value for x in declaration.keywords}
        need(set(values)<=set(kw) and all(type(number(kw[k])) is type(v) and number(kw[k])==v for k,v in values.items()),'Strict grant bounds differ: '+name)
        return pieces,kw
    field('NormalExitRevisionV1','int',{'strict':True,'gt':0,'lt':2**64})
    field('OrdinaryRecipientIdV1','int',{'strict':True,'ge':1,'le':2**32-2})
    field('GrantTitleFullIdV1','int',{'strict':True,'ge':0,'lt':2**32-1})
    field('GrantDesiredSelectedV1','bool',{'strict':True})
    for name,minimum in (('GrantTitleIdsV1',0),('GrantSendTitleIdsV1',1)):
        values={'strict':True,'max_length':64}
        if minimum:values['min_length']=minimum
        pieces,kw=field(name,'list[GrantTitleFullIdV1]',values)
        need(('min_length' not in kw if not minimum else True) and ast.literal_eval(kw['json_schema_extra'])=={'uniqueItems':True},'Grant list cardinality/uniqueItems differs')
        validators=[x for x in pieces[1:] if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='AfterValidator']
        need(len(validators)==1 and len(validators[0].args)==1 and isinstance(validators[0].args[0],ast.Name),'Grant duplicate validator required')
        validator=next((x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==validators[0].args[0].id),None)
        need(validator is not None and any(isinstance(x,ast.Raise) for x in ast.walk(validator)) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='set' for x in ast.walk(validator)),'Grant duplicate rejection missing')
    factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_server')
    opts=dict(zip((arg.arg for arg in factory.args.kwonlyargs),factory.args.kw_defaults))
    need('grant_title_picker_tools' in opts and ast.literal_eval(opts['grant_title_picker_tools']) is False,'Grant factory opt-in must default to exact False')
    tools={n.name:n for n in ast.walk(factory) if isinstance(n,ast.FunctionDef) and n.name in GRANT_TOOLS}
    need(set(tools)==set(GRANT_TOOLS),'All four source grant tools required')
    for name,node in tools.items():
        op,names=GRANT_TOOLS[name]
        annotations={'recipient_id':'OrdinaryRecipientIdV1','title_full_ids':'GrantTitleIdsV1','title_full_id':'GrantTitleFullIdV1','desired_selected':'GrantDesiredSelectedV1',
                     'expected_selected_title_full_ids':'GrantSendTitleIdsV1' if op=='send' else 'GrantTitleIdsV1','expected_revision':'NormalExitRevisionV1'}
        need([arg.arg for arg in node.args.args]==names and not node.args.defaults and not node.args.kwonlyargs and node.args.vararg is None and node.args.kwarg is None,'Source grant signature differs')
        need(all(ast.unparse(arg.annotation)==annotations[arg.arg] for arg in node.args.args),'Strict grant typed signature differs')
        calls=[dec for dec in node.decorator_list if isinstance(dec,ast.Call)]
        annotation=next((kw.value for dec in calls for kw in dec.keywords if kw.arg=='annotations'),None)
        need(isinstance(annotation,ast.Call) and isinstance(annotation.func,ast.Name) and annotation.func.id=='ToolAnnotations','Source grant annotations absent')
        hints={kw.arg:ast.literal_eval(kw.value) for kw in annotation.keywords}
        need(all(hints.get(key) is value for key,value in {'readOnlyHint':op=='query','idempotentHint':op=='query','openWorldHint':False}.items()) and hints.get('destructiveHint',True) is (op!='query'),'Source grant tool hints differ')
        result[name]={'signature':names,'annotations':hints,'operation':op}
    return result
