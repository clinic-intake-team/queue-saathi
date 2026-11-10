import { Globe, ChevronDown, Check } from 'lucide-react'
import './language.css'
import { createContext, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
export type Language='hi'|'en'|'hinglish'
export const languageNames:Record<Language,string>={hi:'हिन्दी (Hindi)',en:'English',hinglish:'Hinglish'}
const allowed=(value:string|null):value is Language=>value==='hi'||value==='en'||value==='hinglish'
function saved(key:string):Language{try{const value=localStorage.getItem(key);return allowed(value)?value:'hinglish'}catch{return 'hinglish'}}
const translations:Record<string,[string,string]>={
 'Theek hai':['ठीक है','Okay'],
 'Mock mode — sample data':['मॉक मोड — नमूना डेटा','Mock mode — sample data'],
 'Interface language':['इंटरफ़ेस की भाषा','Interface language'], 'Question language':['सवालों की भाषा','Question language'],
 'Choose your language':['अपनी भाषा चुनें','Choose your language'],
 'Your language, your comfort.':['आपकी भाषा, आपकी सुविधा।','Your language, your comfort.'],
 'How it works':['यह कैसे काम करता है','How it works'],'Results':['नतीजे','Results'],'Doctor view':['डॉक्टर के लिए','Doctor view'],
 'Start intake':['जानकारी देना शुरू करें','Start intake'],'Start patient intake':['मरीज़ की जानकारी देना शुरू करें','Start patient intake'],
 'Open doctor view':['डॉक्टर का पेज खोलें','Open doctor view'],'Start a conversation':['बातचीत शुरू करें','Start a conversation'],
 'Doctor ko pehle se pata ho.':['डॉक्टर को पहले से पता हो।','Give your doctor the context in advance.'],
 'Your history, before':['आपकी जानकारी,','Your history, before'],'you':['आपके','you'],'walk in.':['आने से पहले।','walk in.'],
 'New: Hinglish voice intake':['नया: आपकी भाषा में आवाज़ से जानकारी','New: voice intake in your language'],
 'A few words in your language. A clearer picture for your doctor.':['आपकी भाषा में कुछ बातें। डॉक्टर के लिए बेहतर जानकारी।','A few words in your language. A clearer picture for your doctor.'],
 'Voice intake that listens, checks, and brings your story together.':['आपकी बात सुनकर, जाँचकर, एक जगह जोड़ता है।','Voice intake that listens, checks, and brings your story together.'],
 'Hindi + English, naturally':['हिन्दी या अंग्रेज़ी, जैसे आपको सुविधा हो','Hindi or English, naturally'],
 'Your words stay visible':['आपके शब्द सुरक्षित रहते हैं','Your words stay visible'],
 'Your history reaches the doctor before you do.':['आपसे पहले आपकी जानकारी डॉक्टर तक पहुँचती है।','Your history reaches the doctor before you do.'],
 'Speak in Hinglish.':['अपनी भाषा में बोलिए।','Speak in your language.'],
 'Hindi, English, or a little of both. Share your symptoms and medicines in your own words.':['हिन्दी, अंग्रेज़ी या दोनों में अपने लक्षण और दवाओं के बारे में बताइए।','Hindi, English, or a little of both. Share your symptoms and medicines in your own words.'],
 'Checked, not guessed.':['जाँच होती है, अंदाज़ा नहीं।','Checked, not guessed.'],
 'Fields are validated. Red flags get an extra check. Unclear answers are kept visible.':['जानकारी की जाँच होती है। ज़रूरी लक्षणों पर ध्यान दिया जाता है और अस्पष्ट जवाब साफ़ दिखते हैं।','Fields are validated. Red flags get an extra check. Unclear answers are kept visible.'],
 'Doctor gets a summary.':['डॉक्टर को सारांश मिलता है।','Doctor gets a summary.'],
 'Hear your medicines read back. Your doctor gets a clear summary with your words as evidence.':['दवाओं के नाम दोबारा सुनकर पुष्टि करें। डॉक्टर को आपके शब्दों के साथ सारांश मिलता है।','Hear your medicines read back. Your doctor gets a clear summary with your words as evidence.'],
 'Your words. A clearer':['आपके शब्द। बेहतर','Your words. A clearer'],'picture.':['जानकारी।','picture.'],
 'Make room for the':['ज़रूरी बात के लिए','Make room for the'],'conversation.':['समय बचाएँ।','conversation.'],
 'Collects information only. Does not diagnose.':['केवल जानकारी एकत्र करता है। निदान नहीं करता।','Collects information only. Does not diagnose.'],
 'Exit':['बाहर जाएँ','Exit'],'Replay question':['सवाल दोबारा सुनें','Replay question'],'Question audio preview':['सवाल की आवाज़ का नमूना','Question audio preview'],
 'Aaram se bataiye. Hindi, English, ya dono mein.':['आराम से बताइए। हिन्दी, अंग्रेज़ी या दोनों में।','Take your time. You may answer in Hindi, English, or both.'],
 'APNI BAAT, APNE SHABDON MEIN':['अपनी बात, अपने शब्दों में','YOUR STORY, IN YOUR WORDS'],
 'EK BAAR PHIR':['एक बार फिर','LET’S TRY AGAIN'],'HUM SUN RAHE HAIN':['हम सुन रहे हैं','WE’RE LISTENING'],'AAPKI BAAT':['आपकी बात','YOUR ANSWER'],
 'Maine suna:':['मैंने सुना:','I heard:'],
 'Microphone ki permission dijiye':['माइक्रोफ़ोन की अनुमति दीजिए','Please allow microphone access'],
 'Bolte rahiye. Rokne ke liye tap karein.':['बोलते रहिए। रोकने के लिए दबाइए।','Keep speaking. Tap to stop.'],
 'Bolne ke liye mic par tap karein.':['बोलने के लिए माइक्रोफ़ोन दबाइए।','Tap the microphone to speak.'],
 'Use a sample answer':['नमूना जवाब इस्तेमाल करें','Use a sample answer'],
 'Koi baat nahi. Ek baar phir poochte hain.':['कोई बात नहीं। एक बार फिर पूछते हैं।','That is okay. Let’s ask once more.'],
 'Aapki baat note kar li hai. Agle sawaal par chalein?':['आपकी बात लिख ली है। अगले सवाल पर चलें?','Your answer has been noted. Ready for the next question?'],
 'Phir se bataiye':['फिर से बताइए','Try answering again'],'Pura karein':['पूरा करें','Finish intake'],'Agla sawaal':['अगला सवाल','Next question'],
 'Record again / Dobara record karein':['दोबारा रिकॉर्ड करें','Record again'],
 'EK BAAR PAKKA KAR LEIN':['एक बार पक्का कर लें','LET’S CONFIRM'],
 'Maine yeh dawai suni.':['मैंने ये दवाएँ सुनीं।','These are the medicines I heard.'],'Kya yeh sahi hai?':['क्या यह सही है?','Is that correct?'],
 'Naam yaad nahi hai? Koi baat nahi. Hum use saaf likhenge.':['नाम याद नहीं है? कोई बात नहीं। हम इसे साफ़ लिखेंगे।','Do not remember the name? That is okay. We will mark it clearly.'],
 'Please confirm':['कृपया पुष्टि करें','Please confirm'],'Naam maloom nahi':['नाम मालूम नहीं','Name unknown'],
 'Koi dawai nahi batayi':['कोई दवा नहीं बताई','No medicines reported'],'Read-back dobara suniye':['दवाओं के नाम दोबारा सुनें','Replay medicine read-back'],
 'Haan, sahi hai':['हाँ, सही है','Yes, that is correct'],'Nahi, badalna hai':['नहीं, बदलना है','No, I need to change it'],
 'Ya bolkar bataiye':['या बोलकर बताइए','Or tell us by voice'],'Voice se confirm karein':['बोलकर पुष्टि करें','Confirm by voice'],
 'Use a sample voice answer':['नमूना बोलकर दिया जवाब इस्तेमाल करें','Use a sample voice answer'],
 'EK BAAR CHECK KARNA ZAROORI HAI':['एक बार जाँच करना ज़रूरी है','PLEASE CHECK WITH RECEPTION'],
 'RECEPTION KO ABHI BATAYEIN':['रिसेप्शन को अभी बताएँ','TELL RECEPTION NOW'],
 'Aapki baat ko ek baar check karna hai.':['आपकी बात को एक बार जाँचना है।','We need someone to check your answer.'],
 'Yeh zaroori lag raha hai.':['यह ज़रूरी लग रहा है।','This sounds important.'],
 'Kripya reception par baat kar lijiye, taaki aapki jaankari sahi samajh sakein.':['कृपया रिसेप्शन पर बात कर लीजिए ताकि आपकी जानकारी सही समझ सकें।','Please speak to reception so your information can be understood correctly.'],
 'Kripya abhi reception par bataiye.':['कृपया अभी रिसेप्शन पर बताइए।','Please tell reception right away.'],
 'Is jawab ko hum pakka nahi samajh paaye.':['हम इस जवाब को पक्का नहीं समझ पाए।','We could not understand this answer clearly.'],
 'Aapne jo bataya, use staff ko pehle dekhna chahiye.':['आपने जो बताया, उसे स्टाफ़ को पहले देखना चाहिए।','Staff should review what you reported first.'],
 'Message dobara suniye':['संदेश दोबारा सुनें','Replay message'],'Back to home':['होम पेज पर जाएँ','Back to home'],
 'AAPKI BAAT NOTE HO GAYI':['आपकी बात लिख ली गई है','YOUR ANSWERS HAVE BEEN SAVED'],'Shukriya!':['शुक्रिया!','Thank you!'],
 'Aapki jaankari doctor tak':['आपकी जानकारी डॉक्टर तक','Your information has been sent'],'pahunch gayi hai.':['पहुँच गई है।','to the doctor.'],
 'AAPKA TOKEN':['आपका टोकन','YOUR TOKEN'],'Apni baari ka intezaar kijiye.':['अपनी बारी का इंतज़ार कीजिए।','Please wait for your turn.'],
 'Back to QueueSaathi':['QueueSaathi पर वापस जाएँ','Back to QueueSaathi'],'Open final doctor record':['डॉक्टर के लिए अंतिम रिकॉर्ड खोलें','Open final doctor record'],
 'Start another mock intake':['नया मॉक सत्र शुरू करें','Start another mock intake'],'Retry upload':['दोबारा भेजें','Retry upload'],'Try again':['फिर कोशिश करें','Try again'],
 'Ek pal… aapki baat jod rahe hain.':['एक पल… आपकी बात जोड़ रहे हैं।','One moment… saving your answer.'],
 'Aapka intake shuru ho raha hai.':['आपका सत्र शुरू हो रहा है।','Your intake is starting.'],
 'Please wait while your answer is saved.':['आपका जवाब सेव हो रहा है, कृपया रुकिए।','Please wait while your answer is saved.'],
 'Getting your first question ready.':['पहला सवाल तैयार हो रहा है।','Getting your first question ready.'],
 'Question audio is not cached in this language yet.':['इस भाषा में सवालों की आवाज़ अभी तैयार नहीं है। सवाल पढ़कर जवाब दे सकते हैं।','Question audio is not cached in this language yet. You can read the question and answer.'],
 'Recording · 45 sec maximum':['रिकॉर्डिंग · अधिकतम 45 सेकंड','Recording · 45 sec maximum'],
 'Mock mode · sample answers':['मॉक मोड · नमूना जवाब','Mock mode · sample answers'],'Live voice intake · real recognition':['लाइव जानकारी · असली आवाज़ की पहचान','Live voice intake · real recognition'],
 'Mock mode — sample transcript':['मॉक मोड — नमूना ट्रांसक्रिप्ट','Mock mode — sample transcript'],
 'Your spoken answers are transcribed and validated. You can re-record if something is wrong.':['आपके बोले गए जवाब लिखे और जाँचे जाते हैं। कुछ गलत हो तो दोबारा रिकॉर्ड करें।','Your spoken answers are transcribed and validated. You can re-record if something is wrong.'],
 'This demo uses fixed sample answers, not a transcription of your recording.':['इस मॉक सत्र में तय नमूना जवाब दिखते हैं, आपकी रिकॉर्डिंग का असली ट्रांसक्रिप्ट नहीं।','This demo uses fixed sample answers, not a transcription of your recording.'],
 'Question audio is silent in this mock demo.':['मॉक सत्र में सवाल की आवाज़ मौन नमूना है।','Question audio is silent in this mock demo.']
}
Object.assign(translations,{
 'TESTED WITH REAL HINGLISH RECORDINGS':['असली हिंग्लिश रिकॉर्डिंग पर जाँच','TESTED WITH REAL HINGLISH RECORDINGS'],
 'Medicine-name accuracy':['दवाओं के नाम की सटीकता','Medicine-name accuracy'],
 'With Prisma medicine keyterms':['Prisma में दवाओं के नाम की सूची के साथ','With Prisma medicine keyterms'],
 'Red flags caught':['गंभीर लक्षण पहचाने गए','Red flags caught'],
 'Keyword checks + validated extraction':['कीवर्ड और जाँची गई जानकारी','Keyword checks + validated extraction'],
 'False alarms after fixes':['सुधार के बाद गलत अलर्ट','False alarms after fixes'],
 'Safety with fewer interruptions':['कम रुकावटों के साथ सुरक्षा','Safety with fewer interruptions'],
 'On our recorded Hinglish test set.':['हमारे रिकॉर्ड किए गए हिंग्लिश परीक्षण पर।','On our recorded Hinglish test set.'],
 'See results context':['नतीजों का संदर्भ देखें','See results context'],
 'A LITTLE TALK. A BETTER HANDOFF.':['थोड़ी बातचीत। बेहतर जानकारी।','A LITTLE TALK. A BETTER HANDOFF.'],
 'Less repetition at the desk.':['बार-बार बताने की ज़रूरत कम।','Less repetition at the desk.'],
 'More context for the conversation that matters.':['डॉक्टर से ज़रूरी बातचीत के लिए बेहतर जानकारी।','More context for the conversation that matters.'],
 'Real recordings. Honest limits.':['असली रिकॉर्डिंग। सीमाएँ स्पष्ट।','Real recordings. Honest limits.'],
 'These results come from a small, two-speaker recorded test set in quiet conditions. Set B v1 is the official held-out result; v2 reflects development fixes. An alert is a prompt for staff to check, not a diagnosis.':['ये नतीजे शांत वातावरण में दो वक्ताओं के छोटे रिकॉर्ड किए गए परीक्षण से हैं। Set B v1 अलग रखे गए परीक्षण का आधिकारिक नतीजा है; v2 में सुधार शामिल हैं। अलर्ट स्टाफ़ को जाँचने का संकेत है, निदान नहीं।','These results come from a small, two-speaker recorded test set in quiet conditions. Set B v1 is the official held-out result; v2 reflects development fixes. An alert is a prompt for staff to check, not a diagnosis.'],
 'Back to the numbers':['आँकड़ों पर वापस जाएँ','Back to the numbers'],
 'BEFORE THE CONSULTATION BEGINS':['डॉक्टर से मिलने से पहले','BEFORE THE CONSULTATION BEGINS'],
 'LESS TO REPEAT. MORE TO UNDERSTAND.':['कम दोहराएँ। बेहतर समझें।','LESS TO REPEAT. MORE TO UNDERSTAND.'],
 'A little conversation.':['थोड़ी बातचीत।','A little conversation.'],'A clearer':['बेहतर','A clearer'],'handoff.':['जानकारी।','handoff.'],
 "The essentials in one place, with uncertainty kept visible and the patient's own words close by.":['ज़रूरी जानकारी एक जगह, अस्पष्ट बातें साफ़ और मरीज़ के अपने शब्द साथ में।',"The essentials in one place, with uncertainty kept visible and the patient's own words close by."],
 'Red flags stay at the top':['गंभीर लक्षण सबसे ऊपर','Red flags stay at the top'],
 'Medicines are read back, not assumed':['दवाओं के नाम सुनाकर पुष्टि होती है','Medicines are read back, not assumed'],
 'Evidence travels with the summary':['मरीज़ के शब्द सारांश के साथ रहते हैं','Evidence travels with the summary'],
 'Try the patient experience':['मरीज़ का अनुभव देखें','Try the patient experience'],
 'Illustrative sample · fictional patient data':['उदाहरण · काल्पनिक मरीज़ की जानकारी','Illustrative sample · fictional patient data'],
 'Red flag: breathlessness reported':['गंभीर लक्षण: साँस फूलने की शिकायत','Red flag: breathlessness reported'],
 'Flagged for staff review':['स्टाफ़ की जाँच के लिए चिह्नित','Flagged for staff review'],
 'Doctor summary':['डॉक्टर के लिए सारांश','Doctor summary'],'Visit reason':['आने की वजह','Visit reason'],
 'Complaint':['तकलीफ़','Complaint'],'Duration':['अवधि','Duration'],'Medicines':['दवाएँ','Medicines'],
 'Allergies':['एलर्जी','Allergies'],'Conditions':['पुरानी बीमारियाँ','Conditions'],'SAMPLE':['नमूना','SAMPLE'],
 'Named medicine confirmed during read-back':['दवा के नाम की दोबारा पुष्टि की गई','Named medicine confirmed during read-back'],
 'AI-collected intake. Verify with the patient.':['एआई द्वारा एकत्र जानकारी। मरीज़ से पुष्टि करें।','AI-collected intake. Verify with the patient.'],
 'Question language could not be changed. Please try again.':['सवालों की भाषा नहीं बदली जा सकी। फिर कोशिश करें।','Question language could not be changed. Please try again.'],
 'Question audio: Timbre v3.0.':['सवाल की आवाज़: Timbre v3.0।','Question audio: Timbre v3.0.'],
 'Questions and medicine read-back use Timbre v3.0.':['सवालों और दवाओं की आवाज़ के लिए Timbre v3.0।','Questions and medicine read-back use Timbre v3.0.'],
 'Zaroor. Dawai ka naam phir se bataiye.':['ज़रूर। दवा का नाम फिर से बताइए।','Of course. Please tell us the medicine name again.'],
 'Zaroor. Isi sawaal ka jawab phir se record karein.':['ज़रूर। इसी सवाल का जवाब फिर से रिकॉर्ड करें।','Of course. Please record your answer to the same question again.'],
 'This is a mock session saved in the local demo queue.':['यह स्थानीय डेमो में सेव किया गया मॉक सत्र है।','This is a mock session saved in the local demo queue.'],
 'Your live intake has been saved for the doctor.':['आपकी असली जानकारी डॉक्टर के लिए सेव हो गई है।','Your live intake has been saved for the doctor.'],
 'Try full flow':['पूरा सत्र आज़माएँ','Try full flow'],'Start recording':['रिकॉर्डिंग शुरू करें','Start recording'],'Stop recording':['रिकॉर्डिंग रोकें','Stop recording'],
 'Fictional sample screen. No recording is started automatically.':['यह काल्पनिक नमूना है। रिकॉर्डिंग अपने आप शुरू नहीं होती।','Fictional sample screen. No recording is started automatically.'],
 'Simulated recording · mic is off':['नमूना रिकॉर्डिंग · माइक्रोफ़ोन बंद है','Simulated recording · mic is off'],
 'Waiting for microphone…':['माइक्रोफ़ोन की अनुमति की प्रतीक्षा…','Waiting for microphone…'],
 'Sample screen · no live session':['नमूना स्क्रीन · असली सत्र नहीं','Sample screen · no live session'],
 'Silent audio placeholder in this mock demo.':['मॉक डेमो में आवाज़ का मौन नमूना।','Silent audio placeholder in this mock demo.'],
 'Tap Replay to play the silent demo question.':['मौन नमूना चलाने के लिए दोबारा सुनें दबाएँ।','Tap Replay to play the silent demo question.'],
 'Tap Replay to hear the question.':['सवाल सुनने के लिए दोबारा सुनें दबाएँ।','Tap Replay to hear the question.'],
 'Question audio is unavailable. You can read the question and try Replay again.':['आवाज़ उपलब्ध नहीं है। सवाल पढ़ सकते हैं और फिर से सुनने की कोशिश कर सकते हैं।','Question audio is unavailable. You can read the question and try Replay again.']
})
Object.assign(translations,{
 'Recorded results are temporarily unavailable.':['रिकॉर्ड किए गए नतीजे अभी उपलब्ध नहीं हैं।','Recorded results are temporarily unavailable.'],
 'Built on Gnani Prisma v3.0 and Timbre v3.0':['Gnani Prisma v3.0 और Timbre v3.0 पर आधारित','Built on Gnani Prisma v3.0 and Timbre v3.0'],
 'This sample screen has no recorded audio.':['इस नमूना स्क्रीन में रिकॉर्ड की गई आवाज़ नहीं है।','This sample screen has no recorded audio.'],
 'This answer was already saved. We have restored your place.':['यह जवाब सेव हो चुका था। आपका स्थान वापस खोल दिया है।','This answer was already saved. We have restored your place.'],
 'Please reload to restore your saved place.':['सेव किए गए स्थान पर लौटने के लिए पेज दोबारा खोलें।','Please reload to restore your saved place.'],
 'Recording is unavailable in this browser. Please try Chrome with microphone access.':['इस ब्राउज़र में रिकॉर्डिंग उपलब्ध नहीं है। माइक्रोफ़ोन की अनुमति के साथ Chrome आज़माएँ।','Recording is unavailable in this browser. Please try Chrome with microphone access.'],
 'The microphone stopped unexpectedly. Please try again.':['माइक्रोफ़ोन अचानक रुक गया। कृपया फिर कोशिश करें।','The microphone stopped unexpectedly. Please try again.'],
 'No audio was recorded. Please try again.':['कोई आवाज़ रिकॉर्ड नहीं हुई। कृपया फिर कोशिश करें।','No audio was recorded. Please try again.'],
 'Your choice could not be saved. Please try again.':['आपकी पसंद सेव नहीं हो सकी। कृपया फिर कोशिश करें।','Your choice could not be saved. Please try again.'],
 'We could not reopen that question. Please try again.':['सवाल दोबारा नहीं खुल पाया। कृपया फिर कोशिश करें।','We could not reopen that question. Please try again.'],
 'Illustrative completion screen.':['पूरा होने की नमूना स्क्रीन।','Illustrative completion screen.'],
 'Token 18':['टोकन 18','Token 18'], 'New breathing discomfort':['साँस लेने में नई तकलीफ़','New breathing discomfort'],
 'Cough, chest tightness and breathlessness on walking':['खाँसी, सीने में जकड़न और चलने पर साँस फूलना','Cough, chest tightness and breathlessness on walking'],
 '46 years':['46 साल','46 years'],'Female':['महिला','Female'],'3 days':['3 दिन','3 days'],
 'Penicillin — patient reported':['पेनिसिलिन — मरीज़ ने बताया','Penicillin — patient reported'],
 'High blood pressure — patient reported':['उच्च रक्तचाप — मरीज़ ने बताया','High blood pressure — patient reported'],
 "unclear: 'small white tablet'":["अस्पष्ट: 'छोटी सफ़ेद गोली'","unclear: 'small white tablet'"],
 "Patient's words · illustrative quote, no audio recording":['मरीज़ के शब्द · उदाहरण, रिकॉर्ड की गई आवाज़ नहीं',"Patient's words · illustrative quote, no audio recording"]
})
Object.assign(translations,{
 '40 recorded clips · 2 speakers':['40 रिकॉर्ड किए गए क्लिप · 2 वक्ता','40 recorded clips · 2 speakers'],
 'Every emergency case flagged':['हर आपातकालीन मामले पर चेतावनी','Every emergency case flagged'],
 '20 full patient sessions':['मरीज़ों के 20 पूरे सत्र','20 full patient sessions'],
 'After fixes · see Results':['सुधारों के बाद · नतीजे देखें','After fixes · see Results'],
 'These results come from a small, two-speaker recorded test set in quiet conditions. See Results for evaluation details and development changes. An alert is a prompt for staff to check, not a diagnosis.':['ये नतीजे शांत जगह पर दो वक्ताओं की रिकॉर्डिंग के एक छोटे परीक्षण से हैं। परीक्षण और सुधारों की जानकारी के लिए नतीजे देखें। चेतावनी का मतलब स्टाफ से जाँच करवाना है, निदान नहीं।','These results come from a small, two-speaker recorded test set in quiet conditions. See Results for evaluation details and development changes. An alert is a prompt for staff to check, not a diagnosis.']
})
Object.assign(translations,{
 'AAPKI BHASHA, AAPKA AARAAM':['आपकी भाषा, आपकी सुविधा','YOUR LANGUAGE, YOUR COMFORT'],
 'Kis bhasha mein baat karein?':['किस भाषा में बात करें?','Which language would you like to use?'],
 'Jis bhasha mein aaram ho, chuniye. Hindi aur English mix kar sakte hain.':['जिस भाषा में आप सहज हों, वह चुनिए। आप हिंदी और अंग्रेज़ी मिला सकते हैं।',"Choose how you'd like to talk. You can mix Hindi and English anytime."],
 'Recommended':['सुझाया गया','Recommended'],
 'Awaaz suniye':['आवाज़ सुनिए','Preview voice'],
 'Awaaz rokein':['आवाज़ रोकें','Stop preview'],
 'Shuru karein':['शुरू करें','Start'],
 'Sawaal alag bhasha mein chahiye? Aur options':['सवाल किसी और भाषा में चाहिए? और विकल्प','Different language for questions? More options']
})
type Context={uiLanguage:Language;questionLanguage:Language;setUiLanguage:(l:Language)=>void;setQuestionLanguage:(l:Language)=>void;t:(key:string,language?:Language)=>string;prompts:Record<string,Record<string,string>>;audioCached:Record<string,number>}
const Locale=createContext<Context|null>(null)
export function LanguageProvider({children}:{children:ReactNode}){
 const [uiLanguage,setUi]=useState<Language>(()=>saved('queuesaathi.uiLanguage'))
 const [questionLanguage,setQuestion]=useState<Language>(()=>saved('queuesaathi.questionLanguage'))
 const [prompts,setPrompts]=useState<Context['prompts']>({});const [audioCached,setAudioCached]=useState<Record<string,number>>({})
 useEffect(()=>{document.documentElement.lang=uiLanguage==='hinglish'?'hi-Latn':uiLanguage;try{localStorage.setItem('queuesaathi.uiLanguage',uiLanguage);localStorage.setItem('queuesaathi.questionLanguage',questionLanguage)}catch{/* preferences still work without storage */}},[uiLanguage,questionLanguage])
 useEffect(()=>{let active=true;fetch('/api/languages').then(r=>{if(!r.ok)throw new Error();return r.json()}).then(data=>{if(active){setPrompts(data.prompts);setAudioCached(data.audio_cached)}}).catch(()=>{});return ()=>{active=false}},[])
 function t(key:string,language:Language=uiLanguage){return language==='hi'?translations[key]?.[0]??key:language==='en'?translations[key]?.[1]??key:key}
 return <Locale.Provider value={{uiLanguage,questionLanguage,setUiLanguage:setUi,setQuestionLanguage:setQuestion,t,prompts,audioCached}}>{children}</Locale.Provider>
}
export function useLanguage(){const context=useContext(Locale);if(!context)throw new Error('LanguageProvider missing');return context}
const choices:Language[]=['hinglish','hi','en']
export function LanguageSegments({value,onChange,disabled=false,label='Question language'}:{value:Language;onChange:(l:Language)=>void;disabled?:boolean;label?:string}){
 return <div className="language-segments" role="group" aria-label={label}>{choices.map(l=><button type="button" key={l} disabled={disabled} aria-pressed={value===l} onClick={()=>onChange(l)}>{l==='hi'?'हिंदी':languageNames[l]}</button>)}</div>
}
export function SiteLanguage(){
 const {uiLanguage,setUiLanguage}=useLanguage();const [open,setOpen]=useState(false);const root=useRef<HTMLDivElement>(null);const trigger=useRef<HTMLButtonElement>(null)
 useEffect(()=>{if(!open)return;const close=(e:PointerEvent)=>{if(!root.current?.contains(e.target as Node))setOpen(false)};document.addEventListener('pointerdown',close);return ()=>document.removeEventListener('pointerdown',close)},[open])
 return <div className="site-language" ref={root} onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(false)}} onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);trigger.current?.focus()}if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(!open){setOpen(true);setTimeout(()=>root.current?.querySelector<HTMLButtonElement>('[role="menuitemradio"]')?.focus(),0)}else{const items=Array.from(root.current!.querySelectorAll<HTMLButtonElement>('[role="menuitemradio"]'));const i=items.indexOf(document.activeElement as HTMLButtonElement);items[(i+(e.key==='ArrowDown'?1:items.length-1)+items.length)%items.length]?.focus()}}}}><button ref={trigger} className="language-pill" aria-label={'Site language: '+languageNames[uiLanguage]} aria-haspopup="menu" aria-expanded={open} aria-controls="site-language-menu" onClick={()=>setOpen(!open)}><Globe size={16}/><span>{uiLanguage==='hi'?'हिंदी':languageNames[uiLanguage]}</span><ChevronDown size={13}/></button>{open&&<div id="site-language-menu" className="language-dropdown" role="menu" aria-label="Site text language">{choices.map(l=><button key={l} role="menuitemradio" aria-checked={uiLanguage===l} onClick={()=>{setUiLanguage(l);setOpen(false);trigger.current?.focus()}}>{l==='hi'?'हिंदी':languageNames[l]}{uiLanguage===l&&<Check size={15}/>}</button>)}</div>}</div>
}
export function LanguageControls({disabled=false,onQuestionChange}:{compact?:boolean;disabled?:boolean;onQuestionChange?:(language:Language)=>void}){
 const {questionLanguage,setQuestionLanguage}=useLanguage()
 return <details className="language-options"><summary>Question language</summary><LanguageSegments value={questionLanguage} disabled={disabled} onChange={onQuestionChange||setQuestionLanguage}/></details>
}

export function LanguageText({text}:{text:string}){
 const {uiLanguage,t}=useLanguage()
 return <span className="language-crossfade">{(['hinglish','hi','en'] as Language[]).map(language=><span key={language} lang={language==='hinglish'?'hi-Latn':language} aria-hidden={language!==uiLanguage} className={language===uiLanguage?'is-current':''}>{t(text,language)}</span>)}</span>
}
