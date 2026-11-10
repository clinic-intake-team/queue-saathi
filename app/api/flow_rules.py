"""UI flow applicability only. Never changes extractor output or safety decisions."""
import re

ROUTINE=re.compile(r'\b(?:routine|check[ -]?up|follow[ -]?up|monitoring|regular\s+(?:bp|blood pressure|sugar|diabetes)\s+check)\b|नियमित.*(?:जांच|जाँच|चेक)|फॉलो[ -]?अप|चेक[ -]?अप',re.I)
NO_SYMPTOMS=re.compile(r"\b(?:no\s+(?:(?:current|present|active|other|any)\s+)?symptoms|(?:do\s+not|don['’]?t)\s+have\s+(?:any\s+)?(?:(?:current|present|active)\s+)?symptoms|asymptomatic|no\s+(?:current\s+)?complaints)\b|\bkoi\s+(?:bhi\s+)?(?:takleef|dikkat|lakshan|symptoms?)\s+(?:nahi|nahin|nhi)\b|(?:कोई\s*)?(?:लक्षण|तकली[फफ़]|परेशानी)\s*नहीं",re.I)

def okay(item):return isinstance(item,dict) and item.get('status')=='ok' and item.get('value') is not None

def classify(question,transcript,checked,previous):
    if question not in {'P2','P3'}:return None
    complaint=checked.get('complaint',{}) if question=='P2' else previous.get('complaint',{})
    reason=checked.get('visit_reason',{}) if question=='P2' else previous.get('visit_reason',{})
    content=complaint.get('value') if okay(complaint) else None
    symptoms=content.get('symptoms') if isinstance(content,dict) else None
    positive=bool(isinstance(symptoms,list) and symptoms)
    reason_text=reason['value'] if okay(reason) and isinstance(reason['value'],str) else ''
    summary=content.get('summary','') if isinstance(content,dict) else ''
    routine=bool(ROUTINE.search(reason_text+' '+summary))
    denial=NO_SYMPTOMS.search(transcript)
    if positive:return None
    if not (denial or routine):return None
    # The phrase that establishes no symptoms must be explicit; a routine visit
    # alone does not justify inventing a negative symptom history.
    return {'routine_visit':routine,'no_current_symptoms':bool(denial),
            'symptom_denial_evidence':denial[0] if denial else '',
            'duration_not_applicable':True,'skip_followups':True,
            'skipped_questions':['P3','F'],'applicability_reason':'routine visit' if routine else 'no current symptoms'}
