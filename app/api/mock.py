"""Synthetic API demo, not STT or model predictions; never used in real mode."""
TRANSCRIPTS = {
 'P0': 'Mera token 24 hai.', 'P1': 'Main 34 saal ki mahila hoon.',
 'P2': 'Mujhe do din se khansi hai.', 'P3': 'Do din se.',
 'P4': 'Koi dikkat nahi.', 'P5': 'Main Dolo 650 leti hoon.',
 'R1': 'Haan, sahi hai.', 'P6': 'Koi nahi.', 'P7': 'Koi nahi.',
}
def response(q, *, scenario="normal", retry=False, correcting=False):
    t = TRANSCRIPTS[q]
    values = {'P0': {'token':24}, 'P1':{'age':34,'sex':'female'},
      'P2':{'complaint':{'summary':'Cough for two days','symptoms':['cough']}, 'red_flag_symptoms':[],'visit_reason':None},
      'P3':{'duration_days':2}, 'P4':{'red_flag_symptoms':[]},
      'P5':{'medicines':[{'name':'Dolo','strength':'650','purpose':None}]},
      'R1':{'confirmed':True,'correction':None}, 'P6':{'allergies':'none'}, 'P7':{'conditions':'none'}}
    if scenario == 'unclear' and q == 'P1' and not retry:
        return 'Ek baar phir poochiye.', {field:{'value':None,'status':'question','evidence':'Ek baar phir poochiye.'} for field in ('age','sex')}
    if scenario == 'needs_check' and q == 'P4':
        return 'Samajh nahi aaya.', {'red_flag_symptoms':{'value':None,'status':'unclear','evidence':''}}
    if scenario == 'red_flag' and q == 'P2':
        t='Mujhe seene mein dard hai.'
        values[q]={'complaint':{'summary':'Chest pain','symptoms':['chest pain']},'red_flag_symptoms':['chest pain'],'visit_reason':None}
    if correcting and q == 'P5':
        t='Main Paracetamol 500 leti hoon.'
        values[q]={'medicines':[{'name':'Paracetamol','strength':'500','purpose':None}]}
    return t, {k:{'value':v,'status':'ok' if v is not None or k=='visit_reason' else 'unclear','evidence':t if v is not None else ''} for k,v in values[q].items()}
