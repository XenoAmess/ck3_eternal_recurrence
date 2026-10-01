from pathlib import Path
p=Path(__file__).parent
t=(p/'verify_R0143_UI_a01.py').read_text(encoding='utf-8')
old="day['complete_causal_chain'] is False"
if t.count(old)!=1:raise ValueError('exact pending predicate occurrence')
t=t.replace(old,"day['complete_causal_chain'] == 'pending independent original records and save verification'")
t=t.replace('independent-UI-endpoint-review-a01.json','independent-UI-endpoint-review-a02.json')
with (p/'verify_R0143_UI_a02.py').open('x',encoding='utf-8',newline='\n') as f:f.write(t)
print(p/'verify_R0143_UI_a02.py')
