"""Local medicine matching. No network; vocabulary is data/medicines.txt."""
from pathlib import Path
import re

from rapidfuzz.fuzz import ratio
from eval.run_meds import normalize

ROOT = Path(__file__).resolve().parent
THRESHOLD = 85


def vocabulary():
    # A strength in the keyterm list is not evidence that a patient said it.
    terms = []
    for line in (ROOT / 'data/medicines.txt').read_text().splitlines():
        name = re.sub(r'\s+\d+(?:\.\d+)?$', '', line.strip())
        if name and name not in terms:
            terms.append(name)
    return terms


# Words that describe complaints/anatomy are never medicine identities.
NON_MEDICINES = set('palm palms pain pains dard pet haath hath hand hands sir head headache stomach arm leg chest throat back fever cough blood'.split()) | {'दर्द','पेट','हाथ','सिर','बुखार','खांसी'}
CONTEXT = r'\b(?:goli|tablet|tablets|dawai|dawa|medicine|medicines|take|taking|drink|drinking|peeta|peeti|pi raha|pi rahi|leta|leti|le raha|le rahi)\b|गोली|गोलियाँ|दवा|लेता|लेती|ले रहा|ले रही|पी रहा|पी रही|पीता|पीती'
DENIAL = r'\b(?:no\s+(?:\w+\s+){0,2}medicines?|not taking any|koi (?:dawai|dawa|goli) nahi|nahi le raha|nahi le rahi|nahi leta|nahi leti)\b|कोई दवा नहीं|दवाई नहीं|नहीं ले रहा|नहीं ले रही'


def explicit_denial(transcript):
    return bool(re.search(DENIAL, transcript.lower()))


def _denied(tokens, start, end):
    before = tokens[max(0,start-4):start]
    # Contrast starts a new assertion ("no BP medicine but I take Dolo").
    for boundary in ('but','lekin','लेकिन'):
        if boundary in before:before=before[before.index(boundary)+1:]
    # In a correction 'X nahi, Y hai', the postposed denial belongs to X.
    if len(before)>=2 and before[-1] in {'nahi','nahin','नहीं'} and any(before[-2]==normalize(name).split()[-1] for name in vocabulary()):
        before=[]
    after = tokens[end:end+4]
    return (any(t in {'no','not','nahi','nahin','नहीं'} for t in before)
            or any(t in {'nahi','nahin','नहीं'} for t in after[:2]))


def parse(transcript, *, extracted=None, fuzzy=True):
    """Confirm ONLY validated LLM medicine candidates; never discover names in free text.

    Missing/invalid extraction fails closed. Short brands require exact tokens and
    nearby medication context or strength. Strength is taken only from the audio
    transcript's immediately following number, never the vocabulary's default.
    """
    item = extracted.get('medicines', extracted) if isinstance(extracted, dict) else None
    if not isinstance(item, dict) or item.get('status') != 'ok' or not isinstance(item.get('value'), list):
        return []
    tokens = normalize(transcript).split()
    medicines = []
    for candidate in item['value']:
        if not isinstance(candidate, dict):continue
        name = candidate.get('name')
        if not name:
            purpose = candidate.get('purpose')
            if not isinstance(purpose,str) or not purpose.strip():continue
            aliases={'BP':['bp','blood pressure','ब्लड प्रेशर','बीपी'],'sugar':['sugar','diabetes','शुगर','मधुमेह'],'thyroid':['thyroid','थायरॉइड','थायराइड']}
            purpose=next((key for key,values in aliases.items() if normalize(purpose) in values),purpose)
            phrases=[normalize(v).split() for v in aliases.get(purpose,[purpose])]
            positions=[(i,len(words)) for words in phrases for i in range(len(tokens)) if tokens[i:i+len(words)]==words]
            if not any(not _denied(tokens,i,i+size) for i,size in positions):continue
            if not re.search(CONTEXT, normalize(transcript)):continue
            medicines.append(dict(name=None,strength=None,purpose=purpose,display=purpose+' medicine (name unknown)',match_score=None,status='unknown_name_with_purpose'))
            continue
        if not isinstance(name,str):continue
        raw=normalize(name);raw_tokens=raw.split()
        if set(raw_tokens)&NON_MEDICINES:continue
        options=[]
        for canonical in vocabulary():
            compact=normalize(canonical).replace(' ','')
            canonical_tokens=normalize(canonical).split()
            # A validated multiword identity may include a form/variant suffix.
            # Confirm its complete vocabulary base, never an arbitrary word.
            base_prefix=raw_tokens[:len(canonical_tokens)]==canonical_tokens
            score=100 if base_prefix else ratio(raw.replace(' ',''),compact)
            if score < (THRESHOLD if fuzzy else 100):continue
            short=len(compact)<=4
            for start in range(len(tokens)):
                for size in range(1,len(raw_tokens)+2):
                    end=start+size;phrase=tokens[start:end]
                    if len(phrase)!=size or set(phrase)&NON_MEDICINES or any(t.isdecimal() for t in phrase):continue
                    if short:
                        if phrase!=normalize(canonical).split():continue
                        nearby=' '.join(tokens[max(0,start-4):min(len(tokens),end+4)])
                        if not ((end<len(tokens) and re.fullmatch(r'\d+(?:\.\d+)?',tokens[end])) or re.search(CONTEXT,nearby)):continue
                    elif not (base_prefix and phrase==canonical_tokens) and ratio(''.join(phrase),raw.replace(' ','')) < (THRESHOLD if fuzzy else 100):continue
                    if _denied(tokens,start,end):continue
                    options.append((score,len(compact),start,end,canonical))
        if not options:continue
        score,_,start,end,canonical=max(options,key=lambda v:(v[0],v[1],-v[2]))
        strength=tokens[end] if end<len(tokens) and re.fullmatch(r'\d+(?:\.\d+)?',tokens[end]) else None
        medicine=dict(name=canonical,strength=strength,purpose=candidate.get('purpose'),display=canonical+(' '+strength if strength else ''),match_score=round(score,2),status='needs_confirmation')
        if not any(m['name']==canonical and m['strength']==strength for m in medicines):medicines.append(medicine)
    return medicines


def guard_extraction(transcript, checked):
    """Apply deterministic medicine policy after schema/evidence validation."""
    import copy
    result=copy.deepcopy(checked)
    item=result.get('medicines',{})
    matches=parse(transcript,extracted=result)
    if explicit_denial(transcript) and not matches:
        result['medicines']={'value':[],'status':'ok','evidence':transcript}
    elif item.get('status')=='ok' and isinstance(item.get('value'),list):
        if item['value'] and not matches:
            result['medicines']={'value':None,'status':'unclear','evidence':''}
        else:
            result['medicines']=dict(item,value=[{k:m[k] for k in ('name','strength','purpose')} for m in matches])
    return result


def readback(medicines):
    if not medicines:
        return 'Kya aap koi dawai nahi le rahe hain?'
    return 'Aapne bataya: ' + ', '.join(m['display'] for m in medicines) + '. Kya yeh sahi hai?'


def apply_confirmation(medicines, transcript, extracted):
    """Only accept a validated explicit R1 agreement; corrections need new read-back."""
    import extract
    checked = extract.validate('R1', transcript, extracted)
    accepted = (checked['confirmed']['status'] == 'ok'
                and checked['confirmed']['value'] is True
                and checked['correction']['status'] != 'ok')
    return [dict(m, status='confirmed' if accepted else m['status']) for m in medicines]
