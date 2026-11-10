"""Human-authored question translations. Clinical rules and extraction stay shared."""
import json
from pathlib import Path
LANGUAGES=('hinglish','hi','en')
TRANSLATIONS=json.loads((Path(__file__).resolve().parents[2]/'data/prompts_languages.json').read_text())

def prompts(language,original):
    if language not in LANGUAGES:raise ValueError('Unsupported language')
    if language=='hinglish':
        from .prompt_cache import RETRY
        return dict(original,RP=RETRY)
    return dict(TRANSLATIONS[language])

def readback(medicines,language):
    if language=='hinglish':
        import meds
        return meds.readback(medicines)
    names=[]
    for med in medicines:
        if med.get('name'):names.append(med['name']+(' '+str(med['strength']) if med.get('strength') else ''))
        elif language=='hi':names.append((med.get('purpose')+' की दवा' if med.get('purpose') else 'दवा')+' (नाम स्पष्ट नहीं)')
        else:names.append((med.get('purpose')+' medicine' if med.get('purpose') else 'medicine')+' (name unclear)')
    if language=='hi':return 'आपने बताया: '+', '.join(names)+'। क्या यह सही है?' if names else 'आपने कोई दवा नहीं बताई। क्या यह सही है?'
    return 'You mentioned: '+', '.join(names)+'. Is that correct?' if names else 'You did not report any medicines. Is that correct?'
