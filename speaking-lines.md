# Speaking Lines for Test Recordings

Companion to `test-scripts.md`, which holds the ground truth and expected results.

**How to use:**
- Each card has **two versions**: one for Chill (ch), one for the teammate (tm). Different wording from each speaker keeps the test honest.
- Read **naturally, like a patient**, not like reading aloud. Small changes, pauses and "umm" are fine and good. **Keep the facts the same.**
- If the app asks a follow-up that isn't listed, answer naturally from the card's facts.
- **Never use these exact sentences to tune prompts or rules.** They are held-out test data. Use your own different examples while developing.

Sex in P1: Chill says male, teammate says female.

---

## Set A: Medicines (answering "Kya aap abhi koi dawai le rahe hain?")

| ID | Chill (ch) | Teammate (tm) |
|---|---|---|
| M01 | "Haan, main Telma chaalis leta hoon, roz subah ek." | "Ji, Telma 40 chal rahi hai, din mein ek baar." |
| M02 | "Bukhaar ke liye Dolo chhe sau pachaas le raha hoon." | "Abhi bas Dolo 650 li hai, fever ke liye." |
| M03 | "Glycomet paanch sau aur Thyronorm pachaas, dono roz leta hoon." | "Sugar ke liye Glycomet 500 aur thyroid ke liye Thyronorm fifty." |
| M04 | "Subah naashte se pehle Pan chaalis, aur raat ko Ecosprin pachhattar." | "Pan 40 khaali pet leti hoon, aur raat mein Ecosprin 75." |
| M05 | "Amlong paanch leta hoon, BP ke liye." | "Ji, bas Amlong 5." |
| M06 | "Metformin aur Atorvastatin, generic wali." | "Doctor ne Metformin aur Atorvastatin di hai." |
| M07 | "Montair LC ki goli aur Asthalin ka pump." | "Raat ko Montair LC, aur zarurat pe Asthalin inhaler." |
| M08 | "Shelcal aur Uprise D3, calcium aur vitamin D ke liye." | "Calcium ki Shelcal, aur hafte mein ek Uprise D3." |
| M09 | "Sirf Thyronorm pachchees." | "Bas ek hi, Thyronorm 25." |
| M10 | "Janumet aur Ecosprin chal rahi hai." | "Sugar ki Janumet, aur ek Ecosprin." |
| M11 | "BP ki ek goli hai, naam yaad nahi aa raha... aur Pantocid." | "Ek BP wali tablet hai, naam bhool gayi, aur gas ke liye Pantocid." |
| M12 | "Kabhi kabhi dard ho toh Combiflam le leta hoon." | "Regular kuch nahi, bas dard mein Combiflam." |
| M13 | "Teen din se Azithral paanch sau chal rahi hai." | "Doctor ne Azithral 500 di thi, teen din ho gaye." |
| M14 | "Sardi ke liye Crocin aur Cetzine le raha hoon." | "Crocin, aur raat ko ek Cetzine." |
| M15 | "Rosuvas das aur Clopilet pachhattar." | "Rosuvas 10 aur Clopilet 75, dono raat ko." |
| M16 | "Sugar ki do goliyan hain, ek Glycomet hai, doosri ka naam yaad nahi." | "Do sugar ki tablet hain, ek Glycomet, doosri ka naam nahi pata." |
| M17 | "Budecort ka inhaler aur Deriphyllin." | "Asthma ke liye Budecort pump aur Deriphyllin tablet." |
| M18 | "Lantus insulin ka injection lagata hoon, aur Glycomet." | "Raat ko Lantus injection, aur Glycomet goli." |
| M19 | "Nahi, abhi koi dawai nahi le raha." | "Koi dawai nahi chal rahi abhi." |
| M20 | "Telma leta hoon... nahi nahi, Telma nahi, Amlong hai woh." | "Telma... arre nahi, Amlong leti hoon. Telma pehle thi." |

---

## Set B: Full sessions

Question key: **P0** token · **P1** age and sex · **P2** complaint · **P3** duration · **F** follow-ups (answer whichever the app asks) · **P4** red-flag check · **P5** medicines · **R1** medicine read-back · **P6** allergies · **P7** existing conditions

### S01: Fever
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Barah." | "Token number 12." |
| P1 | "Chauntees saal, aadmi hoon." | "Main thirty four ki hoon, female." |
| P2 | "Bukhaar hai, aur poore badan mein dard ho raha hai." | "Fever aa raha hai, body pain bhi hai." |
| P3 | "Teen din se." | "Teen din ho gaye." |
| F: measured? | "Haan naapa tha, ek sau ek tha." | "Thermometer mein 101 aaya tha." |
| F: chills? | "Haan, thand lag ke aata hai." | "Haan, kaanpkapi hoti hai." |
| P4 | "Nahi, aisa kuch nahi." | "Nahi, aisa kuch nahi hai." |
| P5 | "Dolo chhe sau pachaas li hai." | "Bas Dolo 650." |
| R1 | "Haan, sahi hai." | "Ji haan." |
| P6 | "Nahi, koi allergy nahi." | "Allergy nahi hai." |
| P7 | "Nahi, koi bimari nahi." | "Nahi, kuch nahi." |

### S02: BP check
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Saat." | "Number seven." |
| P1 | "Atthaavan saal, aadmi." | "Fifty eight, mahila." |
| P2 | "BP check karwana hai, aur sir dard bahut rehta hai." | "BP dikhana tha, headache bhi rehta hai roz." |
| P3 | "Ek hafte se." | "Ek week se." |
| F: last BP? | "Pichhli baar ek sau pachaas by pachaanve aaya tha." | "Last time 150 by 95 tha." |
| F: where is the pain? | "Sir ke peeche ki taraf." | "Peeche gardan ke paas." |
| F: pain 1–10? | "Paanch." | "Around five." |
| P4 | "Nahi." | "Nahi, aisa nahi hai." |
| P5 | "Telma chaalis aur Amlong paanch." | "Telma 40 aur Amlong 5 leti hoon." |
| R1 | "Haan, theek hai." | "Haan sahi." |
| P6 | "Nahi." | "Koi allergy nahi." |
| P7 | "BP hai, bas." | "Sirf BP." |

### S03: ⚠ Chest pain (RED FLAG)
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Ikkees." | "Twenty one." |
| P1 | "Baasath saal, aadmi." | "Sixty two, female." |
| P2 | "Subah se seene mein dard hai, bhaari bhaari lag raha hai." | "Chest mein pain hai, jaise koi daba raha ho." |
| P3 | "Aaj subah se." | "Subah se, kuch ghante ho gaye." |
| F: where? | "Beech mein, aur baayen haath tak jaata hai." | "Chest ke beech mein, left arm tak." |
| F: pain 1–10? | "Aath." | "Eight." |
| P4 | "Haan, seene mein dard hai aur saans bhi phool rahi hai." | "Haan ji, chest pain hai aur saans lene mein dikkat hai." |
| P5 | "Ecosprin pachhattar aur Atorva." | "Ecosprin 75 aur Atorva leti hoon." |
| R1 | "Haan." | "Ji haan." |
| P6 | "Nahi." | "Nahi." |
| P7 | "Sugar aur BP dono hai." | "Haan, diabetes aur BP." |

### S04: Cough
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Teen." | "Three." |
| P1 | "Sattaais saal, male." | "Twenty seven, mahila." |
| P2 | "Khaansi ho rahi hai, ruk hi nahi rahi." | "Cough hai, bahut zyada." |
| P3 | "Paanch din se." | "Five days se." |
| F: phlegm? | "Haan balgam aata hai, peela sa." | "Haan, yellow colour ka balgam." |
| F: breathless? | "Nahi, saans nahi phoolti." | "Nahi, breathing theek hai." |
| P4 | "Nahi, aisa kuch nahi." | "Nahi." |
| P5 | "Asthalin ka pump hai, zarurat pe." | "Bas Asthalin inhaler." |
| R1 | "Haan." | "Haan sahi hai." |
| P6 | "Haan, Augmentin se rash ho gaya tha ek baar." | "Augmentin se allergy hai, skin pe daane aa gaye the." |
| P7 | "Asthma hai bachpan se." | "Mujhe asthma hai." |

### S05: Stomach
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Pandrah." | "Fifteen." |
| P1 | "Iktaalees, aadmi." | "Forty one, female." |
| P2 | "Pet kharab hai, dast ho rahe hain, ek baar ulti bhi hui." | "Loose motions ho rahe hain, aur ek baar vomit hua." |
| P3 | "Do din se." | "Parson se." |
| F: how often? | "Din mein paanch chhe baar." | "Five six times a day." |
| P4 | "Nahi." | "Nahi, aisa kuch nahi." |
| P5 | "ORS pi raha hoon, aur Thyronorm pachaas roz." | "ORS le rahi hoon, aur Thyronorm 50 chalti hai." |
| R1 | "Haan." | "Ji." |
| P6 | "Koi allergy nahi." | "Nahi." |
| P7 | "Thyroid hai." | "Thyroid ki problem hai." |

### S06: Sugar follow-up
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Nau." | "Nine." |
| P1 | "Unchaas saal, aadmi." | "Forty nine, mahila." |
| P2 | "Sugar check karwana hai, aur thakaan bahut rehti hai." | "Sugar dikhani thi, hamesha tired feel hota hai." |
| P3 | "Do hafte se." | "Two weeks se." |
| F: last sugar? | "Khaali pet do sau das aayi thi." | "Fasting 210 aayi thi last time." |
| P4 | "Nahi." | "Nahi." |
| P5 | "Glycomet paanch sau aur Janumet." | "Glycomet 500 aur Janumet." |
| R1 | "Haan sahi." | "Haan." |
| P6 | "Nahi." | "Koi nahi." |
| P7 | "Sugar hai." | "Diabetes hai." |

### S07: Knee pain
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Atthaarah." | "Eighteen." |
| P1 | "Pachpan, aadmi." | "Fifty five, female." |
| P2 | "Ghutne mein dard rehta hai, chalne mein dikkat hoti hai." | "Knee pain hai, seedhiyan chadhne mein problem." |
| P3 | "Teen mahine se." | "Three months ho gaye." |
| F: where? | "Daayen ghutne mein." | "Right knee." |
| F: pain 1–10? | "Chhe." | "Six." |
| P4 | "Nahi." | "Nahi, aisa kuch nahi." |
| P5 | "Kabhi kabhi Combiflam, aur Shelcal roz." | "Shelcal leti hoon, aur dard mein kabhi Combiflam." |
| R1 | "Haan." | "Ji haan." |
| P6 | "Pata nahi, kabhi dhyaan nahi diya." | "Pata nahi mujhe." |
| P7 | "Nahi, aur kuch nahi." | "Nahi." |

### S08: Headache (negation trap: must NOT alert)
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Paanch." | "Five." |
| P1 | "Tees saal, male." | "Thirty, mahila." |
| P2 | "Sir mein dard hai." | "Headache ho raha hai." |
| P3 | "Do din se." | "Do din ho gaye." |
| F: where? | "Aage maathe pe." | "Forehead pe." |
| F: pain 1–10? | "Paanch." | "Five." |
| P4 | "Nahi, seene mein dard ya saans ki koi dikkat nahi hai." | "Nahi nahi, chest pain ya breathing problem kuch nahi hai." |
| P5 | "Crocin li thi." | "Bas Crocin." |
| R1 | "Haan." | "Haan." |
| P6 | "Nahi." | "Nahi." |
| P7 | "Nahi." | "Kuch nahi." |

### S09: ⚠ Weakness (RED FLAG; should alert at P2 even before P4)
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Teyees." | "Twenty three." |
| P1 | "Sadsath saal, aadmi." | "Sixty seven, female." |
| P2 | "Kal se baayan haath kamzor lag raha hai, aur bolne mein thodi dikkat ho rahi hai." | "Kal se left hand mein jaan nahi lag rahi, aur bolne mein problem ho rahi hai." |
| P3 | "Kal se." | "Kal shaam se." |
| P4 | "Haan, haath kamzor hai aur bolne mein dikkat hai." | "Haan, weakness hai ek side mein." |
| P5 | "Telma chaalis aur Glycomet." | "Telma 40 aur Glycomet." |
| R1 | "Haan." | "Haan ji." |
| P6 | "Nahi." | "Nahi." |
| P7 | "BP aur sugar." | "BP aur diabetes dono." |

### S10: Messy patient
| Q | Chill | Teammate |
|---|---|---|
| P0 | "Pachchees." | "Twenty five." |
| P1 | "Pachpan saal... haan, pachpan. Aadmi." | "Pachpan ki hoon, mahila." |
| P2 | "Bukhaar hai, aur poora badan toot raha hai." | "Fever hai, aur body bahut dard kar rahi hai." |
| P3 | "Teen din... nahi, chaar din ho gaye." | "Teen... nahi nahi, chaar din se." |
| F: measured? | "Nahi, naapa nahi." | "Check nahi kiya." |
| P4 | "Nahi." | "Nahi." |
| P5 | "BP ki goli leta hoon, naam yaad nahi." | "BP ki ek tablet hai, naam nahi pata." |
| R1 | "Haan, wahi." | "Haan." |
| P6 | "Nahi." | "Nahi." |
| P7 | "BP hai." | "BP." |

---

## Set C: Edge cases

| ID | Q | Chill | Teammate |
|---|---|---|---|
| C01 | P2 | "Haan... hello? Awaaz aa rahi hai?" | "Hello? Sun rahe ho? Kuch sunai nahi diya." |
| C02 | P1 | "Umar nahi bataunga." | "Age nahi batana mujhe." |
| C03 | P5 | "Aap dawai ka naam kyun pooch rahe ho?" | "Yeh medicine ka kyun chahiye aapko?" |
| C04 | P1 | "Baavan saal, aadmi." | "Baavan ki hoon, female." |
| C05 | P3 | "Parson se." | "Parson raat se." |
| C06 | P3 | "Pichhle hafte se." | "Last week se." |
| C07 | P2 | "Since last Monday I have a severe headache." | "I've had a bad headache since Monday." |
| C08 | P4 | "Saans phool rahi hai, seedhi nahi chadh pa raha." | "Breathing mein bahut problem hai, saans nahi aa rahi." |
| C09 | P4 | "Kal ulti mein khoon aaya tha." | "Vomit mein blood tha kal." |
| C10 | P2 | (TV/fan loud) "Gale mein kharash hai aur halka bukhaar hai." | (TV/fan loud) "Throat pain hai aur thoda fever." |
| C11 | P4 | "Behoshi nahi hui, bas thoda chakkar aaya tha." | "Behosh nahi hui, bas halka chakkar aaya." |
| C12 | P2 | "Dekhiye, pichhle kuch dinon se khaansi hai, raat ko zyada hoti hai, phir bukhaar bhi aa jaata hai shaam ko, aur kamzori itni hai ki kaam pe dhyaan nahi lagta." | "Actually kaafi time se cough hai, raat mein badh jaati hai, evening mein fever aata hai, aur weakness bahut hai, kuch karne ka mann nahi karta." |
