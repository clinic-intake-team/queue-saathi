"""Expanded P7 conditions; all other extraction/repair rules remain v2."""
import copy
import json
import meds
import extract as legacy
import extract_partB_v2 as v2

CONDITIONS={'diabetes','BP','thyroid','asthma','TB','heart disease','epilepsy','other'}
P7_PROMPT=legacy.SYSTEM_PROMPT.replace('"asthma", "other" (sugar means diabetes)',
    '"asthma", "TB", "heart disease", "epilepsy", "other" (sugar means diabetes; tuberculosis means TB; dil ki bimari means heart disease; mirgi/fits means epilepsy)')


def validate(question,transcript,parsed,*,errors=None,**kwargs):
    if question!='P7':
        checked=v2.validate(question,transcript,parsed,errors=errors,**kwargs)
        return meds.guard_extraction(transcript,checked) if question=='P5' else checked
    errors=errors if errors is not None else []
    parsed=v2._wrap_primary(parsed,('conditions',))
    item=v2._normalize_item(parsed.get('conditions') if isinstance(parsed,dict) else None)
    try:
        if not isinstance(item,dict):raise ValueError('Invalid conditions envelope')
        item=copy.deepcopy(item)
        item['value']=legacy.normalize_absence(item.get('value'))
        candidate=copy.deepcopy(item)
        if candidate.get('status')=='ok' and isinstance(candidate.get('value'),list):
            if not candidate['value'] or any(not isinstance(v,str) or v not in CONDITIONS for v in candidate['value']) or len(candidate['value'])!=len(set(candidate['value'])):
                raise ValueError('Invalid value for conditions')
            # Delegate envelope, status and verbatim-evidence checks to the existing
            # validator using its supported sentinel, then restore accepted labels.
            candidate['value']=['other']
        checked=v2.validate('P7',transcript,{'conditions':candidate},errors=errors)
        if checked['conditions']['status']==item.get('status') and not errors:
            checked['conditions']['value']=item['value']
        return checked
    except (ValueError,TypeError) as error:
        errors.append({'field':'conditions','error':str(error)})
        return {'conditions':{'value':None,'status':'unclear','evidence':''}}


def extract(question,transcript,*,allow_real=False,details=None,**kwargs):
    if question!='P7':
        checked=v2.extract(question,transcript,allow_real=allow_real,details=details,**kwargs)
        checked=meds.guard_extraction(transcript,checked) if question=='P5' else checked
        if details is not None:details['extracted']=checked
        return checked
    saved={}
    v2.extract(question,transcript,allow_real=allow_real,details=saved,base_prompt=P7_PROMPT,**kwargs)
    parsed=legacy._parsed_from_raw(saved.get('raw_primary'))
    parsed=v2._wrap_primary(parsed,('conditions',))
    repair=legacy._parsed_from_raw(saved.get('raw_repair'))
    if isinstance(parsed,dict) and isinstance(repair,dict):
        for field,quote in repair.items():
            if isinstance(parsed.get(field),dict) and isinstance(quote,str):parsed[field]['evidence']=quote
    errors=[];checked=validate(question,transcript,parsed,errors=errors)
    saved.update(version='clinical_schema_v3',extracted=checked,validation_errors=errors)
    if details is not None:details.update(saved)
    return checked
