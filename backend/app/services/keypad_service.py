"""
Cyber Raksha AI - Keypad User Protection Service
Guardianship, Scam Intelligence, SMS/Call Risk Assessment & Multilingual Fraud Education
Supports elderly citizens using traditional keypad phones (Nokia, Samsung, itel, Lava, Jio Bharat).
"""
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.keypad_protection import KeypadElderlyUser, KeypadScamReport, KeypadIncident
from app.models.phone_reputation import PhoneReputation
from app.services.phone_reputation_service import PhoneReputationService
from app.services.sms_analysis_service import SmsAnalysisService


class KeypadService:
    """
    Central service for the Keypad User Protection System.
    Operates the Guardian-Assisted Family Shield.
    """

    # Multilingual translation dictionaries for explanations & actions
    TRANSLATIONS = {
        "en": {
            "lang_label": "English",
            "golden_rule_title": "THE GOLDEN RULE OF DIGITAL SAFETY",
            "golden_rule_desc": "NEVER share your OTP, UPI PIN, ATM PIN, passwords, or bank account details with anyone on a phone call or SMS. Real bank employees and police officers will NEVER ask for your secret PIN or ask you to transfer money to prove innocence.",
            "do_not_share": [
                "6-digit or 4-digit OTP received via SMS",
                "UPI PIN used for Google Pay / PhonePe / Paytm",
                "ATM Card 4-digit PIN",
                "Bank Account number and full debit card details",
                "Passwords or security codes"
            ],
            "helpline_guidance": "If money was debited or someone is threatening you, IMMEDIATELY call National Cyber Crime Helpline 1930 and report on sancharsaathi.gov.in (Chakshu portal).",
            "safe_sms": "No obvious fraud indicators detected in this SMS. However, always verify directly with the organization if it discusses financial transactions.",
            "high_risk_sms": "HIGH RISK FRAUD DETECTED! This message contains patterns typical of scam attempts (fake urgency, credential theft, or suspicious links). Do NOT reply, do NOT call numbers inside, and NEVER share any OTP or PIN.",
            "critical_risk_sms": "CRITICAL THREAT DETECTED! This SMS attempts to steal banking credentials, impersonate government/police authority, or manipulate the recipient into sharing OTP/PIN. Advise the elder to delete immediately.",
            "unknown_call": "This number has no verified scam reports in our national intelligence repository. Always advise caution and remind the elder never to disclose banking or personal details.",
            "suspicious_call": "WARNING: This number has been reported by community members for fraudulent activities. Advise the elder NOT to attend or engage with this caller.",
            "confirmed_scam_call": "DANGER! CONFIRMED FRAUDULENT NUMBER. Multiple verified reports identify this caller as an active cybercriminal. Advise the elder to hang up immediately and do not return the call.",
            "disclaimer_sms": "Cyber Raksha AI analyzes SMS entered or submitted by the guardian. Traditional keypad feature phones (Nokia, itel, Lava, Jio Bharat) do not permit automated software background interception without telecom carrier hardware access.",
            "disclaimer_call": "Cyber Raksha AI provides reputation intelligence based on verified reports. Traditional keypad feature phones do not support automated third-party call interception or blocking."
        },
        "hi": {
            "lang_label": "हिन्दी (Hindi)",
            "golden_rule_title": "डिजिटल सुरक्षा का स्वर्ण नियम",
            "golden_rule_desc": "फोन कॉल या एसएमएस पर कभी भी अपना ओटीपी (OTP), यूपीआई पिन (UPI PIN), एटीएम पिन, पासवर्ड या बैंक विवरण किसी के साथ साझा न करें। वास्तविक बैंक कर्मचारी या पुलिस अधिकारी कभी भी आपका गोपनीय पिन नहीं मांगते और न ही पैसे भेजने के लिए कहते हैं।",
            "do_not_share": [
                "एसएमएस द्वारा प्राप्त 6-अंकीय या 4-अंकीय ओटीपी (OTP)",
                "गूगल पे / फोनपे / पेटीएम का यूपीआई पिन (UPI PIN)",
                "एटीएम कार्ड का 4-अंकीय गोपनीय पिन",
                "बैंक खाता संख्या और डेबिट कार्ड के 16 अंक",
                "पासवर्ड या नेट बैंकिंग सुरक्षा कोड"
            ],
            "helpline_guidance": "यदि पैसे कट गए हैं या कोई आपको डरा-धमका रहा है, तो तुरंत 1930 पर कॉल करें और sancharsaathi.gov.in (चक्षु पोर्टल) पर शिकायत दर्ज करें।",
            "safe_sms": "इस एसएमएस में कोई संदिग्ध धोखाधड़ी संकेत नहीं मिला। फिर भी किसी भी वित्तीय लेन-देन से पहले सीधे संबंधित बैंक शाखा से पुष्टि करें।",
            "high_risk_sms": "सावधान! उच्च जोखिम वाला फर्जी एसएमएस! इस संदेश में जालसाजी के संकेत (फर्जी धमकी, क्रेडेंशियल चोरी या संदिग्ध लिंक) मिले हैं। कोई जवाब न दें और ओटीपी कभी साझा न करें।",
            "critical_risk_sms": "गंभीर खतरा! यह एसएमएस सरकारी अधिकारी/पुलिस बनकर डराने या बैंक खाते से पैसे चुराने का प्रयास है। बुजुर्ग परिजन को तुरंत यह संदेश मिटाने की सलाह दें।",
            "unknown_call": "इस नंबर का कोई पूर्व धोखाधड़ी रिकॉर्ड दर्ज नहीं है। फिर भी बुजुर्गों को किसी भी अज्ञात कॉलर को बैंक विवरण न देने की सलाह दें।",
            "suspicious_call": "चेतावनी: इस नंबर को नागरिकों द्वारा धोखाधड़ी और स्पैम कॉल के रूप में रिपोर्ट किया गया है। कॉल न उठाने की सलाह दें।",
            "confirmed_scam_call": "खतरा! सत्यापित साइबर अपराधी का नंबर। कई नागरिकों और जांच एजेंसियों द्वारा इसे प्रमाणित फ्रॉड घोषित किया गया है। तुरंत फोन काट दें।",
            "disclaimer_sms": "साइबर रक्षा एआई केवल अभिभावक द्वारा दर्ज एसएमएस का विश्लेषण करता है। पारंपरिक कीपैड फोन पर टेलीकॉम ऑपरेटर स्तर के बिना स्वचालित सॉफ्टवेयर इंटरसेप्शन संभव नहीं है।",
            "disclaimer_call": "साइबर रक्षा एआई सत्यापित डेटाबेस के आधार पर कॉलर इंटेलिजेंस देता है। सामान्य कीपैड फोन में स्वचालित सॉफ्टवेयर कॉल ब्लॉकिंग समर्थित नहीं है।"
        },
        "kn": {
            "lang_label": "ಕನ್ನಡ (Kannada)",
            "golden_rule_title": "ಡಿಜಿಟಲ್ ಸುರಕ್ಷತೆಯ ಸುವರ್ಣ ನಿಯಮ",
            "golden_rule_desc": "ಫೋನ್ ಕರೆ ಅಥವಾ SMS ಮೂಲಕ ನಿಮ್ಮ OTP, UPI PIN, ATM PIN, ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ಖಾತೆ ವಿವರಗಳನ್ನು ಎಂದಿಗೂ ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ. ನಿಜವಾದ ಬ್ಯಾಂಕ್ ಉದ್ಯೋಗಿಗಳು ಅಥವಾ ಪೊಲೀಸ್ ಅಧಿಕಾರಿಗಳು ಎಂದಿಗೂ ನಿಮ್ಮ ಗೌಪ್ಯ PIN ಅಥವಾ OTP ಕೇಳುವುದಿಲ್ಲ ಮತ್ತು ಹಣ ವರ್ಗಾಯಿಸಲು ಹೇಳುವುದಿಲ್ಲ.",
            "do_not_share": [
                "SMS ಮೂಲಕ ಬಂದ 6 ಅಥವಾ 4 ಅಂಕಿಯ OTP",
                "Google Pay / PhonePe / Paytm ಗಾಗಿ ಬಳಸುವ UPI PIN",
                "ATM ಕಾರ್ಡ್‌ನ 4 ಅಂಕಿಯ ರಹಸ್ಯ PIN",
                "ಬ್ಯಾಂಕ್ ಖಾತೆ ಸಂಖ್ಯೆ ಮತ್ತು ಡೆಬಿಟ್ ಕಾರ್ಡ್ ವಿವರಗಳು",
                "ಪಾಸ್‌ವರ್ಡ್ ಅಥವಾ ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ ಭದ್ರತಾ ಕೋಡ್‌ಗಳು"
            ],
            "helpline_guidance": "ಹಣ ಕಡಿತಗೊಂಡಿದ್ದರೆ ಅಥವಾ ಯಾರಾದರೂ ಬೆದರಿಕೆ ಹಾಕುತ್ತಿದ್ದರೆ, ತಕ್ಷಣ ರಾಷ್ಟ್ರೀಯ ಸೈಬರ್ ಕ್ರೈಮ್ ಸಹಾಯವಾಣಿ 1930 ಗೆ ಕರೆ ಮಾಡಿ ಹಾಗೂ sancharsaathi.gov.in (ಚಕ್ಷು) ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ವರದಿ ಮಾಡಿ.",
            "safe_sms": "ಈ SMS ನಲ್ಲಿ ಯಾವುದೇ ಸ್ಪಷ್ಟ ವಂಚನೆಯ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಹಣಕಾಸಿನ ವಿಷಯವಾಗಿದ್ದರೆ ಬ್ಯಾಂಕ್ ಶಾಖೆಯನ್ನು ನೇರವಾಗಿ ಸಂಪರ್ಕಿಸಿ ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.",
            "high_risk_sms": "ಎಚ್ಚರಿಕೆ! ಅಪಾಯಕಾರಿ ನಕಲಿ SMS ಪತ್ತೆಯಾಗಿದೆ! ಇದರಲ್ಲಿ ನಕಲಿ ಬೆದರಿಕೆ ಅಥವಾ ಮೋಸದ ಲಿಂಕ್ ಇದೆ. ಇದಕ್ಕೆ ಉತ್ತರಿಸಬೇಡಿ ಮತ್ತು ಯಾವುದೇ OTP ಅಥವಾ PIN ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.",
            "critical_risk_sms": "ತೀವ್ರ ಅಪಾಯ! ಈ ಸಂದೇಶವು ಪೊಲೀಸ್ ಅಧಿಕಾರಿ ಅಥವಾ ಬ್ಯಾಂಕ್ ನಂತೆ ನಟಿಸಿ ಹಣ ಕದಿಯುವ ಹುನ್ನಾರವಾಗಿದೆ. ಹಿರಿಯ ನಾಗರಿಕರಿಗೆ ಇದನ್ನು ತಕ್ಷಣ ಅಳಿಸಲು ತಿಳಿಸಿ.",
            "unknown_call": "ಈ ಸಂಖ್ಯೆಯ ಬಗ್ಗೆ ಯಾವುದೇ ಸೈಬರ್ ವಂಚನೆ ವರದಿಗಳು ದಾಖಲಾಗಿಲ್ಲ. ಅಪರಿಚಿತ ಕರೆ ಸ್ವೀಕರಿಸುವಾಗ ಹಿರಿಯರು ಜಾಗರೂಕರಾಗಿರಲು ತಿಳಿಸಿ.",
            "suspicious_call": "ಎಚ್ಚರಿಕೆ: ಈ ಸಂಖ್ಯೆಯನ್ನು ಸಾರ್ವಜನಿಕರು ವಂಚನೆಯ ಕರೆ ಎಂದು ವರದಿ ಮಾಡಿದ್ದಾರೆ. ಕರೆಯನ್ನು ಸ್ವೀಕರಿಸದಂತೆ ಹಿರಿಯರಿಗೆ ತಿಳಿಸಿ.",
            "confirmed_scam_call": "ಅಪಾಯ! ಇದು ದೃಢಪಟ್ಟ ಸೈಬರ್ ಅಪರಾಧಿಗಳ ಸಂಖ್ಯೆ. ಹಿರಿಯರು ತಕ್ಷಣ ಕರೆಯನ್ನು ಕಡಿತಗೊಳಿಸಬೇಕು ಮತ್ತು ಮರುಕರೆ ಮಾಡಬಾರದು.",
            "disclaimer_sms": "ಸೈಬರ್ ರಕ್ಷಾ AI ಪೋಷಕರು ನಮೂದಿಸಿದ ಸಂದೇಶವನ್ನು ವಿಶ್ಲೇಷಿಸುತ್ತದೆ. ಸಾಂಪ್ರದಾಯಿಕ ಕೀಪ್ಯಾಡ್ ಫೋನ್‌ಗಳಲ್ಲಿ ಸ್ವಯಂಚಾಲಿತ SMS ಇಂಟರ್‌ಸೆಪ್ಶನ್ ತಾಂತ್ರಿಕವಾಗಿ ಸಾಧ್ಯವಿಲ್ಲ.",
            "disclaimer_call": "ಸೈಬರ್ ರಕ್ಷಾ AI ಕಾಲರ್ ಇಂಟೆಲಿಜೆನ್ಸ್ ಒದಗಿಸುತ್ತದೆ. ಸಾಂಪ್ರದಾಯಿಕ ಕೀಪ್ಯಾಡ್ ಫೋನ್‌ಗಳಲ್ಲಿ ಸ್ವಯಂಚಾಲಿತ ಸಾಫ್ಟ್‌ವೇರ್ ಕರೆ ಬ್ಲಾಕಿಂಗ್ ಸಾಧ್ಯವಿಲ್ಲ."
        }
    }

    # Common scam educational modules across 3 languages
    EDUCATION_MODULES = {
        "en": [
            {
                "topic_id": "digital_arrest",
                "title": "Digital Arrest Scam (Fake Police / CBI / Customs)",
                "summary": "Scammers call claiming to be CBI, Police, or Customs officers, asserting that illegal parcels, drugs, or bank warrants have been issued against you, demanding isolation on video calls or immediate money transfers.",
                "danger_indicators": [
                    "Threatening arrest or immediate warrant unless you pay money",
                    "Claiming you are under 'Digital Arrest' via phone or Skype",
                    "Asking you not to inform family members or local police",
                    "Demanding fund transfer to 'Reserve Bank safe accounts' for verification"
                ],
                "safe_behavior": "Indian Law and Police have NO concept of 'Digital Arrest'. Police never conduct arrests over phone calls or demand money. Disconnect immediately and call 1930."
            },
            {
                "topic_id": "electricity_bill",
                "title": "Electricity Bill Disconnection Threat",
                "summary": "SMS sent to keypad phones stating: 'Your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill. Immediately call electricity officer at XXXXX.'",
                "danger_indicators": [
                    "Urgent deadline claiming power will be cut in a few hours",
                    "Personal 10-digit mobile number given as 'Electricity Officer'",
                    "Asking you to install QuickSupport/AnyDesk or send Rs 10 to update bill"
                ],
                "safe_behavior": "Electricity boards (BESCOM, MSEDCL, UPPCL, etc.) never send personal mobile numbers for disconnection. Always pay at authorized sub-stations or through official portals."
            },
            {
                "topic_id": "bank_kyc",
                "title": "Bank Account KYC Suspension Scam",
                "summary": "SMS or call claiming your SBI, HDFC, ICICI, or PNB bank account or SIM card will be deactivated within 24 hours because KYC has expired.",
                "danger_indicators": [
                    "Threat of immediate account block",
                    "Asking for debit card details, net banking passwords, or OTP",
                    "Unrecognized links like bit.ly or apk download URLs"
                ],
                "safe_behavior": "Banks NEVER ask for OTP or PIN to update KYC. Visit your local bank branch physically with your passbook and Aadhaar card."
            },
            {
                "topic_id": "lottery_prize",
                "title": "Lottery, KBC & Cash Prize Fraud",
                "summary": "Call or SMS claiming you have won Rs 25 Lakh in a national lottery or TV show contest, but you must pay a processing tax or deposit fee first.",
                "danger_indicators": [
                    "Winning a contest you never entered",
                    "Demanding processing fee, GST, or release fees beforehand",
                    "Urging secrecy from family members"
                ],
                "safe_behavior": "You never have to pay money to receive a legitimate prize. Never transfer any amount."
            },
            {
                "topic_id": "pension_scheme",
                "title": "Pension & Government Subsidy Scam",
                "summary": "Scammers targeting elderly pensioners claiming life certificates (Jeevan Pramaan) or pension arrears will be cancelled without immediate verification.",
                "danger_indicators": [
                    "Caller claiming to be from the Pension Treasury or EPFO",
                    "Asking for Aadhaar OTP or bank details over the phone",
                    "Asking for upfront processing charge"
                ],
                "safe_behavior": "Submit Jeevan Pramaan life certificates only at post offices, Citizen Service Centers (CSC), or official bank branches."
            }
        ],
        "hi": [
            {
                "topic_id": "digital_arrest",
                "title": "डिजिटल अरेस्ट घोटाला (फर्जी पुलिस / सीबीआई)",
                "summary": "जालसाज सीबीआई, पुलिस या नारकोटिक्स अधिकारी बनकर कॉल करते हैं और कहते हैं कि आपके नाम पर नशीले पदार्थों का पार्सल पकड़ा गया है। वे डराकर पैसे ट्रांसफर करवाते हैं।",
                "danger_indicators": [
                    "पैसे न देने पर तुरंत गिरफ्तारी की धमकी देना",
                    "फोन या व्हाट्सएप पर 'डिजिटल अरेस्ट' का दावा करना",
                    "परिवार वालों या स्थानीय पुलिस को न बताने का दबाव बनाना",
                    "सत्यापन के नाम पर सरकारी 'सुरक्षित खाते' में पैसे भेजने को कहना"
                ],
                "safe_behavior": "भारतीय कानून में 'डिजिटल अरेस्ट' नाम की कोई चीज नहीं है। पुलिस कभी फोन पर अरेस्ट वारंट नहीं भेजती और न पैसे मांगती है। तुरंत 1930 पर कॉल करें।"
            },
            {
                "topic_id": "electricity_bill",
                "title": "बिजली बिल कटने का फर्जी संदेश",
                "summary": "कीपैड फोन पर संदेश आता है: 'आपका बिजली कनेक्शन आज रात 9:30 बजे काट दिया जाएगा क्योंकि पुराना बिल अपडेट नहीं है। तुरंत बिजली अधिकारी से संपर्क करें।'",
                "danger_indicators": [
                    "कुछ ही घंटों में बिजली काटने की गंभीर धमकी",
                    "संदेश में किसी सामान्य 10-अंकीय मोबाइल नंबर का होना",
                    "बिल अपडेट करने के लिए 10 रुपये भेजने या ऐप डाउनलोड करने को कहना"
                ],
                "safe_behavior": "बिजली विभाग कभी भी निजी मोबाइल नंबरों से बिल कटने का संदेश नहीं भेजता। बिल का भुगतान केवल आधिकारिक काउंटर पर करें।"
            },
            {
                "topic_id": "bank_kyc",
                "title": "बैंक खाता / केवाईसी बंद होने का फर्जीवाड़ा",
                "summary": "एसएमएस या कॉल जिसमें दावा किया जाता है कि केवाईसी न होने के कारण आपका बैंक खाता या सिम कार्ड 24 घंटे में बंद कर दिया जाएगा।",
                "danger_indicators": [
                    "खाता तुरंत ब्लॉक होने का डर दिखाना",
                    "ओटीपी (OTP), एटीएम पिन या कार्ड नंबर मांगना",
                    "संदेश में संदिग्ध लिंक या फोन नंबर देना"
                ],
                "safe_behavior": "बैंक कभी भी फोन पर या एसएमएस से केवाईसी अपडेट नहीं करता। हमेशा अपनी स्थानीय बैंक शाखा में पासबुक लेकर जाएं।"
            },
            {
                "topic_id": "lottery_prize",
                "title": "लॉटरी और केबीसी ईनाम का झांसा",
                "summary": "कॉल या एसएमएस में कहा जाता है कि आपने 25 लाख की लॉटरी जीती है, लेकिन पैसे पाने के लिए पहले टैक्स या प्रोसेसिंग फीस जमा करनी होगी।",
                "danger_indicators": [
                    "ऐसी लॉटरी जीतना जिसमें आपने कभी भाग नहीं लिया",
                    "ईनाम पाने के लिए पहले पैसे ट्रांसफर करने की मांग",
                    "बात को गोपनीय रखने का दबाव"
                ],
                "safe_behavior": "असली ईनाम पाने के लिए कभी पहले पैसे नहीं देने पड़ते। किसी भी खाते में पैसे न भेजें।"
            },
            {
                "topic_id": "pension_scheme",
                "title": "पेंशन व सरकारी योजना धोखाधड़ी",
                "summary": "बुजुर्गों को निशाना बनाकर कॉल किया जाता है कि उनका जीवन प्रमाण पत्र या पेंशन रुक जाएगी यदि उन्होंने तुरंत सत्यापन नहीं किया।",
                "danger_indicators": [
                    "ट्रेजरी या पेंशन विभाग का अधिकारी बनकर कॉल करना",
                    "फोन पर आधार ओटीपी या बैंक खाते का विवरण मांगना",
                    "पेंशन जारी करने के नाम पर शुल्क मांगना"
                ],
                "safe_behavior": "जीवन प्रमाण पत्र केवल डाकघर, जन सेवा केंद्र या अपनी बैंक शाखा में जाकर ही जमा करें।"
            }
        ],
        "kn": [
            {
                "topic_id": "digital_arrest",
                "title": "ಡಿಜಿಟಲ್ ಬಂಧನ ವಂಚನೆ (ನಕಲಿ ಪೊಲೀಸ್ / ಸಿಬಿಐ)",
                "summary": "ವಂಚಕರು ಸಿಬಿಐ, ಪೊಲೀಸ್ ಅಥವಾ ಕಸ್ಟಮ್ಸ್ ಅಧಿಕಾರಿಗಳಂತೆ ಕರೆ ಮಾಡಿ, ನಿಮ್ಮ ಹೆಸರಿನಲ್ಲಿ ಮಾದಕ ದ್ರವ್ಯದ ಪಾರ್ಸೆಲ್ ಸಿಕ್ಕಿದೆ ಎಂದು ಬೆದರಿಸಿ ಹಣ ವರ್ಗಾವಣೆ ಮಾಡುವಂತೆ ಒತ್ತಾಯಿಸುತ್ತಾರೆ.",
                "danger_indicators": [
                    "ಹಣ ನೀಡದಿದ್ದರೆ ತಕ್ಷಣ ಬಂಧಿಸುವುದಾಗಿ ಬೆದರಿಕೆ ಹಾಕುವುದು",
                    "ಫೋನ್ ಮೂಲಕ 'ಡಿಜಿಟಲ್ ಬಂಧನ' ಮಾಡಲಾಗಿದೆ ಎಂದು ಹೇಳುವುದು",
                    "ಕುಟುಂಬದವರಿಗೆ ಅಥವಾ ಸ್ಥಳೀಯ ಪೊಲೀಸರಿಗೆ ತಿಳಿಸದಂತೆ ಹೆದರಿಸುವುದು",
                    "ತನಿಖೆಗಾಗಿ ಸುರಕ್ಷಿತ ಖಾತೆಗೆ ಹಣ ಕಳುಹಿಸುವಂತೆ ಕೇಳುವುದು"
                ],
                "safe_behavior": "ಭಾರತೀಯ ಕಾನೂನಿನಲ್ಲಿ 'ಡಿಜಿಟಲ್ ಬಂಧನ' ಎಂಬ ಯಾವುದೇ ಪರಿಕಲ್ಪನೆ ಇಲ್ಲ. ಪೊಲೀಸರು ಎಂದಿಗೂ ಫೋನ್‌ನಲ್ಲಿ ಹಣ ಕೇಳುವುದಿಲ್ಲ. ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ."
            },
            {
                "topic_id": "electricity_bill",
                "title": "ವಿದ್ಯುತ್ ಬಿಲ್ ರದ್ದತಿ ಬೆದರಿಕೆ ವಂಚನೆ",
                "summary": "ಕೀಪ್ಯಾಡ್ ಫೋನ್‌ಗಳಿಗೆ ಬರುವ ಸಂದೇಶ: 'ಹಿಂದಿನ ಬಿಲ್ ಅಪ್‌ಡೇಟ್ ಆಗದ ಕಾರಣ ಇಂದು ರಾತ್ರಿ 9:30 ಕ್ಕೆ ನಿಮ್ಮ ಮನೆಯ ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಡಿತಗೊಳಿಸಲಾಗುವುದು. ತಕ್ಷಣ ಕರೆ ಮಾಡಿ.'",
                "danger_indicators": [
                    "ಕೆಲವೇ ಗಂಟೆಗಳಲ್ಲಿ ವಿದ್ಯುತ್ ಕಡಿತಗೊಳಿಸುವುದಾಗಿ ಬೆದರಿಕೆ",
                    "ಅಧಿಕಾರಿಯ ಹೆಸರಿನಲ್ಲಿ ವೈಯಕ್ತಿಕ 10 ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನೀಡುವುದು",
                    "ಬಿಲ್ ಅಪ್‌ಡೇಟ್‌ಗಾಗಿ 10 ರೂ ಕಳುಹಿಸಲು ಅಥವಾ ಆ್ಯಪ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು ಕೇಳುವುದು"
                ],
                "safe_behavior": "ಬೆಸ್ಕಾಂ ಅಥವಾ ಯಾವುದೇ ವಿದ್ಯುತ್ ಇಲಾಖೆಯು ವೈಯಕ್ತಿಕ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಗಳಿಂದ ಇಂತಹ ಸಂದೇಶಗಳನ್ನು ಕಳುಹಿಸುವುದಿಲ್ಲ. ಅಧಿಕೃತ ಕಚೇರಿಯಲ್ಲಿ ಮಾತ್ರ ಪಾವತಿಸಿ."
            },
            {
                "topic_id": "bank_kyc",
                "title": "ಬ್ಯಾಂಕ್ ಕೆವೈಸಿ ಬ್ಲಾಕ್ ವಂಚನೆ",
                "summary": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಅಥವಾ ಸಿಮ್ ಕಾರ್ಡ್ ಕೆವೈಸಿ ಅವಧಿ ಮುಗಿದಿದೆ, ತಕ್ಷಣ ನವೀಕರಿಸದಿದ್ದರೆ ಖಾತೆ ಶಾಶ್ವತವಾಗಿ ಸ್ಥಗಿತಗೊಳ್ಳುತ್ತದೆ ಎಂಬ ನಕಲಿ ಸಂದೇಶ ಅಥವಾ ಕರೆ.",
                "danger_indicators": [
                    "ಖಾತೆ ತಕ್ಷಣ ಬ್ಲಾಕ್ ಆಗುತ್ತದೆ ಎಂಬ ಭಯ ಹುಟ್ಟಿಸುವುದು",
                    "ಫೋನ್‌ನಲ್ಲಿ OTP, ATM PIN ಅಥವಾ ಕಾರ್ಡ್ ವಿವರಗಳನ್ನು ಕೇಳುವುದು",
                    "ಸಂದೇಶದಲ್ಲಿ ಅನುಮಾನಾಸ್ಪದ ಲಿಂಕ್ ಅಥವಾ ನಂಬರ್ ಇರುವುದು"
                ],
                "safe_behavior": "ಬ್ಯಾಂಕುಗಳು ಎಂದಿಗೂ ಫೋನ್ ಮೂಲಕ OTP ಅಥವಾ PIN ಕೇಳುವುದಿಲ್ಲ. ನಿಮ್ಮ ಸ್ಥಳೀಯ ಬ್ಯಾಂಕ್ ಶಾಖೆಗೆ ನೇರವಾಗಿ ಭೇಟಿ ನೀಡಿ."
            },
            {
                "topic_id": "lottery_prize",
                "title": "ಲಾಟರಿ ಮತ್ತು ನಗದು ಬಹುಮಾನ ವಂಚನೆ",
                "summary": "ನೀವು 25 ಲಕ್ಷ ಲಾಟರಿ ಅಥವಾ ಕೆಬಿಸಿ ಬಹುಮಾನ ಗೆದ್ದಿದ್ದೀರಿ, ಹಣ ಪಡೆಯಲು ಮೊದಲು ಪ್ರೊಸೆಸಿಂಗ್ ಶುಲ್ಕ ಪಾವತಿಸಬೇಕು ಎಂದು ಹೇಳುವ ಕರೆ ಅಥವಾ SMS.",
                "danger_indicators": [
                    "ನೀವು ಭಾಗವಹಿಸದ ಸ್ಪರ್ಧೆಯಲ್ಲಿ ಬಹುಮಾನ ಬಂದಿದೆ ಎನ್ನುವುದು",
                    "ಬಹುಮಾನದ ಹಣ ಪಡೆಯಲು ಮೊದಲೇ ಹಣ ಪಾವತಿಸುವಂತೆ ಕೇಳುವುದು",
                    "ಯಾರಿಗೂ ಹೇಳದಂತೆ ರಹಸ್ಯವಾಗಿಡಲು ಒತ್ತಾಯಿಸುವುದು"
                ],
                "safe_behavior": "ನಿಜವಾದ ಬಹುಮಾನಕ್ಕೆ ಮುಂಚಿತವಾಗಿ ಹಣ ನೀಡಬೇಕಾಗಿಲ್ಲ. ಯಾವುದೇ ಅಪರಿಚಿತ ಖಾತೆಗೆ ಹಣ ವರ್ಗಾಯಿಸಬೇಡಿ."
            },
            {
                "topic_id": "pension_scheme",
                "title": "ಪಿಂಚಣಿ ಮತ್ತು ಸರ್ಕಾರಿ ಯೋಜನೆ ವಂಚನೆ",
                "summary": "ಹಿರಿಯ ನಾಗರಿಕರ ಜೀವನ ಪ್ರಮಾಣ ಪತ್ರ ಅಥವಾ ಪಿಂಚಣಿ ಹಣ ರದ್ದಾಗುತ್ತದೆ ಎಂದು ಹೆದರಿಸಿ ಆಧಾರ್ OTP ಅಥವಾ ಬ್ಯಾಂಕ್ ವಿವರ ಪಡೆಯುವ ಹುನ್ನಾರ.",
                "danger_indicators": [
                    "ಪಿಂಚಣಿ ಖಜಾನೆಯ ಅಧಿಕಾರಿ ಎಂದು ಹೇಳಿಕೊಂಡು ಕರೆ ಮಾಡುವುದು",
                    "ಫೋನ್‌ನಲ್ಲಿ ಆಧಾರ್ OTP ಅಥವಾ ಖಾತೆ ವಿವರಗಳನ್ನು ಕೇಳುವುದು",
                    "ಪಿಂಚಣಿ ಬಿಡುಗಡೆ ಮಾಡಲು ಶುಲ್ಕ ಕೇಳುವುದು"
                ],
                "safe_behavior": "ಜೀವನ ಪ್ರಮಾಣ ಪತ್ರವನ್ನು ಅಂಚೆ ಕಚೇರಿ, ಗ್ರಾಮ ಒನ್, ಕರ್ನಾಟಕ ಒನ್ ಅಥವಾ ಬ್ಯಾಂಕ್ ಶಾಖೆಯಲ್ಲಿ ಮಾತ್ರ ಸಲ್ಲಿಸಿ."
            }
        ]
    }

    # ── 1. Family Registration ───────────────────────────────────────────────

    @classmethod
    def register_elderly_member(
        cls,
        db: Session,
        guardian_user_id: int,
        full_name: str,
        mobile_number: str,
        relationship: str,
        device_type: str,
        preferred_language: str = "en",
        consent_given: bool = True,
        consent_notes: Optional[str] = None
    ) -> KeypadElderlyUser:
        """
        Registers an elderly family member under the guardian's account.
        Stores normalized mobile number and consent verification.
        """
        normalized_num = PhoneReputationService.normalize_number(mobile_number)
        lang = preferred_language if preferred_language in ("en", "hi", "kn") else "en"

        # Check if already registered under this guardian
        existing = db.query(KeypadElderlyUser).filter(
            KeypadElderlyUser.guardian_user_id == guardian_user_id,
            KeypadElderlyUser.mobile_number == normalized_num
        ).first()

        if existing:
            existing.full_name = full_name.strip()
            existing.relationship = relationship.strip()
            existing.device_type = device_type.strip()
            existing.preferred_language = lang
            existing.consent_given = consent_given
            existing.consent_notes = consent_notes
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        elderly = KeypadElderlyUser(
            guardian_user_id=guardian_user_id,
            full_name=full_name.strip(),
            mobile_number=normalized_num,
            relationship=relationship.strip(),
            device_type=device_type.strip(),
            preferred_language=lang,
            consent_given=consent_given,
            consent_notes=consent_notes,
            is_active=True
        )
        db.add(elderly)
        db.commit()
        db.refresh(elderly)
        return elderly

    @classmethod
    def get_elderly_members(cls, db: Session, guardian_user_id: int) -> List[KeypadElderlyUser]:
        """Lists active elderly members under a guardian."""
        return db.query(KeypadElderlyUser).filter(
            KeypadElderlyUser.guardian_user_id == guardian_user_id,
            KeypadElderlyUser.is_active == True
        ).order_by(KeypadElderlyUser.created_at.desc()).all()

    @classmethod
    def delete_elderly_member(cls, db: Session, guardian_user_id: int, elderly_user_id: int) -> bool:
        """Deactivates an elderly member record."""
        elderly = db.query(KeypadElderlyUser).filter(
            KeypadElderlyUser.id == elderly_user_id,
            KeypadElderlyUser.guardian_user_id == guardian_user_id
        ).first()
        if not elderly:
            return False
        elderly.is_active = False
        elderly.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True

    # ── 2. SMS Risk Analysis ─────────────────────────────────────────────────

    @classmethod
    def analyze_keypad_sms(
        cls,
        db: Session,
        guardian_user_id: int,
        message: str,
        sender: Optional[str] = None,
        elderly_user_id: Optional[int] = None,
        preferred_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Analyzes SMS text received on an elderly user's keypad phone.
        Detects malicious URLs, fake KYC threats, banking fraud, digital arrest, urgency.
        Generates multilingual explanations, logs an incident, and provides safety rules.
        """
        lang = preferred_language if preferred_language in ("en", "hi", "kn") else "en"
        trans = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS["en"])

        # Retrieve elderly user's preferred language if provided and not overridden
        if elderly_user_id:
            elder = db.query(KeypadElderlyUser).filter(
                KeypadElderlyUser.id == elderly_user_id,
                KeypadElderlyUser.guardian_user_id == guardian_user_id
            ).first()
            if elder and preferred_language == "en" and elder.preferred_language:
                lang = elder.preferred_language
                trans = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS["en"])

        # Perform comprehensive pattern analysis using SmsAnalysisService regex rules
        signatures = []
        risk_score = 0.0
        category = "GENERAL"

        lower_msg = message.lower()

        # Check for Digital Arrest & Govt Impersonation (Extreme threat for elderly)
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("GOV_IMPERSONATION", [])):
            signatures.append("GOV_IMPERSONATION_OR_ARREST_THREAT")
            risk_score += 45.0
            category = "DIGITAL_ARREST"

        # Check for OTP or PIN credential theft
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("OTP_FRAUD", [])):
            signatures.append("OTP_OR_PIN_THEFT_REQUEST")
            risk_score += 40.0
            category = "OTP_FRAUD"

        # Check for Electricity Bill Disconnection
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("UTILITY_FRAUD", [])) or (
            "electricity" in lower_msg and ("disconnect" in lower_msg or "bill" in lower_msg or "power" in lower_msg)
        ):
            signatures.append("ELECTRICITY_BILL_DISCONNECTION_SCAM")
            risk_score += 35.0
            category = "ELECTRICITY_BILL"

        # Check for Bank KYC Suspension
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("BANK_IMPERSONATION", [])) or (
            "kyc" in lower_msg and ("block" in lower_msg or "expire" in lower_msg or "suspend" in lower_msg)
        ):
            signatures.append("BANK_KYC_ACCOUNT_SUSPENSION_SCAM")
            risk_score += 35.0
            category = "BANK_KYC"

        # Check for Lottery or Prize Scams
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("LOTTERY_FRAUD", [])) or (
            "lottery" in lower_msg or "winner" in lower_msg or "25 lakh" in lower_msg or "kbc" in lower_msg
        ):
            signatures.append("LOTTERY_OR_PRIZE_SCAM")
            risk_score += 30.0
            category = "LOTTERY_PRIZE"

        # Check for Fake Urgency
        if any(re.search(pat, lower_msg) for pat in SmsAnalysisService.PATTERNS.get("URGENCY", [])):
            signatures.append("ARTIFICIAL_URGENCY_DEADLINE")
            risk_score += 15.0

        # Check for embedded URLs and malicious shorteners
        urls = SmsAnalysisService.URL_REGEX.findall(message)
        if urls:
            signatures.append(f"UNVERIFIED_URL_PRESENT ({len(urls)} link(s))")
            risk_score += 20.0
            # Check shorteners
            for u in urls:
                for s in SmsAnalysisService.SUSPICIOUS_SHORTENERS:
                    if s in u.lower():
                        signatures.append("SUSPICIOUS_URL_SHORTENER")
                        risk_score += 15.0
                        break

        # Check sender reputation if sender provided
        if sender:
            norm_sender = PhoneReputationService.normalize_number(sender)
            rep = db.query(PhoneReputation).filter(PhoneReputation.phone_number == norm_sender).first()
            if rep and rep.risk_score >= 60.0:
                signatures.append("SENDER_IN_KNOWN_FRAUD_REPOSITORY")
                risk_score += 25.0

        # Calculate final risk level
        risk_score = min(100.0, max(0.0, risk_score))
        if risk_score >= 70.0:
            risk_level = "CRITICAL"
            explanation = trans["critical_risk_sms"]
            recommended_action = trans["golden_rule_desc"]
        elif risk_score >= 40.0:
            risk_level = "HIGH"
            explanation = trans["high_risk_sms"]
            recommended_action = trans["golden_rule_desc"]
        elif risk_score >= 20.0:
            risk_level = "MEDIUM"
            explanation = trans["high_risk_sms"]
            recommended_action = trans["golden_rule_desc"]
        else:
            risk_level = "SAFE"
            explanation = trans["safe_sms"]
            recommended_action = "No immediate danger found. Remind elder: Never share PIN or OTP."

        # Save Keypad Incident record for the guardian
        incident = KeypadIncident(
            guardian_user_id=guardian_user_id,
            elderly_user_id=elderly_user_id,
            incident_type="SMS_CHECK",
            indicator=sender or (message[:40] + "..."),
            raw_content=message[:2000],
            risk_score=risk_score,
            severity=risk_level,
            category=category,
            explanation=explanation,
            recommended_action=recommended_action,
            guardian_notified=True,
            is_acknowledged=(risk_level == "SAFE")
        )
        db.add(incident)
        db.commit()

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "category": category,
            "matched_signatures": signatures,
            "explanation": explanation,
            "recommended_action": recommended_action,
            "golden_rule": trans["golden_rule_desc"],
            "helpline": trans["helpline_guidance"],
            "is_automatic_detection": False,
            "disclaimer": trans["disclaimer_sms"]
        }

    # ── 3. Call Risk Check ───────────────────────────────────────────────────

    @classmethod
    def check_keypad_call(
        cls,
        db: Session,
        guardian_user_id: int,
        phone_number: str,
        claimed_caller_identity: Optional[str] = None,
        elderly_user_id: Optional[int] = None,
        preferred_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Evaluates incoming call from an elderly user's keypad phone.
        Cross-references community reports, authoritative databases, and local scam intelligence.
        Applies a reputation Sybil guard: single report does not trigger CRITICAL without corroboration.
        """
        lang = preferred_language if preferred_language in ("en", "hi", "kn") else "en"
        trans = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS["en"])

        normalized = PhoneReputationService.normalize_number(phone_number)

        # 1. Query Keypad Scam Reports & count distinct reporting guardians
        reports = db.query(KeypadScamReport).filter(
            KeypadScamReport.normalized_number == normalized
        ).all()
        unique_reporters = db.query(func.count(func.distinct(KeypadScamReport.guardian_user_id))).filter(
            KeypadScamReport.normalized_number == normalized
        ).scalar() or len(reports)
        report_count = unique_reporters
        has_verified_authority = any(r.is_verified_authority for r in reports)

        # 2. Query Central PhoneReputation table
        phone_rep = db.query(PhoneReputation).filter(
            PhoneReputation.phone_number == normalized
        ).first()

        # Calculate risk score & status
        base_risk = 0.0
        fraud_category = None
        verification_status = "NO_REPORTS"

        if phone_rep:
            base_risk = max(base_risk, phone_rep.risk_score)
            if phone_rep.category and phone_rep.category != "UNKNOWN":
                fraud_category = phone_rep.category

        if reports:
            latest_report = reports[-1]
            if not fraud_category:
                fraud_category = latest_report.fraud_category

            # Sybil Guard: Distinct reporting entities evaluate risk
            if has_verified_authority:
                verification_status = "OFFICIAL_AUTHORITY_VERIFIED"
                base_risk = max(base_risk, 90.0)
            elif unique_reporters >= 3:
                verification_status = "CORROBORATED"
                base_risk = max(base_risk, min(85.0, 40.0 + (unique_reporters * 10.0)))
            elif unique_reporters == 2:
                verification_status = "CORROBORATED"
                base_risk = max(base_risk, 55.0)
            else:
                verification_status = "COMMUNITY_UNVERIFIED"
                # Single report caps at MEDIUM (35.0) to prevent single-report false positives
                base_risk = max(base_risk, 35.0)

        # Determine level & explanation
        if base_risk >= 80.0 or (has_verified_authority and report_count >= 1):
            risk_level = "CRITICAL"
            explanation = trans["confirmed_scam_call"]
            recommended_action = "Instruct the elderly person to disconnect immediately and not pick up if they call back."
        elif base_risk >= 50.0:
            risk_level = "HIGH"
            explanation = trans["suspicious_call"]
            recommended_action = "Tell the elder to avoid answering. Report to 1909 or Chakshu portal."
        elif base_risk >= 25.0:
            risk_level = "MEDIUM"
            explanation = trans["suspicious_call"]
            recommended_action = "Advise caution. Emphasize the Golden Rule: Never share OTP or PIN."
        elif report_count == 0 and not phone_rep:
            risk_level = "UNKNOWN"
            explanation = trans["unknown_call"]
            recommended_action = "Advise elder to verify caller identity. Never share OTP or bank details."
        else:
            risk_level = "SAFE"
            explanation = "No adverse threat activity recorded for this number."
            recommended_action = "Maintain general awareness."

        # If elevated threat, log a Keypad Incident for the guardian
        if risk_level in ("MEDIUM", "HIGH", "CRITICAL"):
            incident = KeypadIncident(
                guardian_user_id=guardian_user_id,
                elderly_user_id=elderly_user_id,
                incident_type="CALL_CHECK",
                indicator=normalized,
                raw_content=f"Claimed Identity: {claimed_caller_identity or 'None'} | Reports: {report_count}",
                risk_score=base_risk,
                severity=risk_level,
                category=fraud_category or "SUSPICIOUS_CALL",
                explanation=explanation,
                recommended_action=recommended_action,
                guardian_notified=True,
                is_acknowledged=False
            )
            db.add(incident)
            db.commit()

        return {
            "phone_number": phone_number,
            "normalized_number": normalized,
            "risk_level": risk_level,
            "risk_score": base_risk,
            "fraud_category": fraud_category,
            "report_count": report_count,
            "is_verified_authority": has_verified_authority,
            "verification_status": verification_status,
            "explanation": explanation,
            "recommended_action": recommended_action,
            "reporting_helpline": "Call 1930 (Cyber Crime) or report on sancharsaathi.gov.in/sfc/ (Chakshu)",
            "is_automatic_blocking": False,
            "disclaimer": trans["disclaimer_call"]
        }

    # ── 4. Scam Number Reporting ─────────────────────────────────────────────

    @classmethod
    def report_scam_number(
        cls,
        db: Session,
        guardian_user_id: int,
        phone_number: str,
        fraud_category: str = "SUSPICIOUS_CALL",
        claimed_caller_identity: Optional[str] = None,
        evidence_notes: Optional[str] = None,
        elderly_user_id: Optional[int] = None,
        source: str = "GUARDIAN_SUBMITTED"
    ) -> KeypadScamReport:
        """
        Allows guardians to report predatory phone numbers targeting their elderly family members.
        Adds to KeypadScamReport and also feeds into the PhoneReputation repository.
        """
        normalized = PhoneReputationService.normalize_number(phone_number)

        # Anti-Sybil Check: check if this guardian already reported this number
        existing_user_report = db.query(KeypadScamReport).filter(
            KeypadScamReport.normalized_number == normalized,
            KeypadScamReport.guardian_user_id == guardian_user_id
        ).first()

        if existing_user_report:
            existing_user_report.fraud_category = fraud_category.strip().upper()
            if claimed_caller_identity:
                existing_user_report.claimed_caller_identity = claimed_caller_identity.strip()
            if evidence_notes:
                existing_user_report.evidence_notes = evidence_notes.strip()
            existing_user_report.created_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_user_report)
            report = existing_user_report
        else:
            report = KeypadScamReport(
                phone_number=phone_number.strip(),
                normalized_number=normalized,
                guardian_user_id=guardian_user_id,
                elderly_user_id=elderly_user_id,
                fraud_category=fraud_category.strip().upper(),
                claimed_caller_identity=claimed_caller_identity.strip() if claimed_caller_identity else None,
                evidence_notes=evidence_notes.strip() if evidence_notes else None,
                source=source,
                is_verified_authority=(source == "GOV_DATABASE"),
                verification_status="OFFICIAL_AUTHORITY_VERIFIED" if source == "GOV_DATABASE" else "COMMUNITY_UNVERIFIED"
            )
            db.add(report)
            db.commit()
            db.refresh(report)

        # Update or create PhoneReputation entry based on distinct reporting entities
        try:
            unique_reporters = db.query(
                func.count(func.distinct(KeypadScamReport.guardian_user_id))
            ).filter(
                KeypadScamReport.normalized_number == normalized
            ).scalar() or 1

            existing_rep = db.query(PhoneReputation).filter(
                PhoneReputation.phone_number == normalized
            ).first()

            if existing_rep:
                existing_rep.report_count = unique_reporters
                if unique_reporters >= 3:
                    existing_rep.risk_score = max(existing_rep.risk_score, 75.0)
                    existing_rep.reputation_status = "CONFIRMED_SCAM"
                elif unique_reporters == 2:
                    existing_rep.risk_score = max(existing_rep.risk_score, 50.0)
                    existing_rep.reputation_status = "SUSPICIOUS"
                existing_rep.updated_at = datetime.now(timezone.utc)
            else:
                new_rep = PhoneReputation(
                    phone_number=normalized,
                    category=fraud_category.strip().upper(),
                    risk_score=35.0 if unique_reporters == 1 else 60.0,
                    report_count=unique_reporters,
                    reputation_status="REPORTED" if unique_reporters == 1 else "SUSPICIOUS",
                    source="KEYPAD_GUARDIAN_NETWORK"
                )
                db.add(new_rep)
            db.commit()
        except Exception:
            db.rollback()

        return report

    # ── 5. Guardian Alert System ─────────────────────────────────────────────

    @classmethod
    def get_guardian_alert_summary(cls, db: Session, guardian_user_id: int) -> Dict[str, Any]:
        """
        Summarizes alerts, dependents, and recent threat incidents for a guardian.
        Guarantees no phantom alerts without actual submitted events.
        """
        dependents_count = db.query(func.count(KeypadElderlyUser.id)).filter(
            KeypadElderlyUser.guardian_user_id == guardian_user_id,
            KeypadElderlyUser.is_active == True
        ).scalar() or 0

        incidents_query = db.query(KeypadIncident).filter(
            KeypadIncident.guardian_user_id == guardian_user_id
        )

        total_incidents = incidents_query.count()
        unacknowledged = incidents_query.filter(KeypadIncident.is_acknowledged == False).count()
        critical_alerts = incidents_query.filter(
            KeypadIncident.severity == "CRITICAL",
            KeypadIncident.is_acknowledged == False
        ).count()
        high_alerts = incidents_query.filter(
            KeypadIncident.severity == "HIGH",
            KeypadIncident.is_acknowledged == False
        ).count()

        recent = incidents_query.order_by(KeypadIncident.created_at.desc()).limit(15).all()

        recent_dtos = []
        for inc in recent:
            elderly_name = None
            if inc.elderly_user_id:
                el = db.query(KeypadElderlyUser).filter(KeypadElderlyUser.id == inc.elderly_user_id).first()
                if el:
                    elderly_name = el.full_name

            recent_dtos.append({
                "id": inc.id,
                "guardian_user_id": inc.guardian_user_id,
                "elderly_user_id": inc.elderly_user_id,
                "elderly_user_name": elderly_name,
                "incident_type": inc.incident_type,
                "indicator": inc.indicator,
                "risk_score": inc.risk_score,
                "severity": inc.severity,
                "category": inc.category,
                "explanation": inc.explanation,
                "recommended_action": inc.recommended_action,
                "is_acknowledged": inc.is_acknowledged,
                "created_at": inc.created_at
            })

        return {
            "total_dependents": dependents_count,
            "total_incidents": total_incidents,
            "unacknowledged_alerts": unacknowledged,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
            "recent_incidents": recent_dtos
        }

    @classmethod
    def acknowledge_incident(cls, db: Session, guardian_user_id: int, incident_id: int) -> bool:
        """Marks an alert or incident as reviewed/acknowledged by the guardian."""
        incident = db.query(KeypadIncident).filter(
            KeypadIncident.id == incident_id,
            KeypadIncident.guardian_user_id == guardian_user_id
        ).first()
        if not incident:
            return False
        incident.is_acknowledged = True
        db.commit()
        return True

    # ── 6. Elderly Fraud Education ───────────────────────────────────────────

    @classmethod
    def get_education_content(cls, language: str = "en") -> Dict[str, Any]:
        """
        Returns high-contrast, simple, multilingual fraud education modules
        specifically designed for elderly users and their guardians.
        Languages: English ('en'), Hindi ('hi'), Kannada ('kn').
        """
        lang = language if language in ("en", "hi", "kn") else "en"
        trans = cls.TRANSLATIONS.get(lang, cls.TRANSLATIONS["en"])
        modules = cls.EDUCATION_MODULES.get(lang, cls.EDUCATION_MODULES["en"])

        return {
            "language": lang,
            "language_label": trans["lang_label"],
            "golden_rule_title": trans["golden_rule_title"],
            "golden_rule_description": trans["golden_rule_desc"],
            "do_not_share_items": trans["do_not_share"],
            "common_scams": modules,
            "helpline_guidance": trans["helpline_guidance"]
        }

    # ── 7. Official Reporting Guidance ───────────────────────────────────────

    @classmethod
    def get_official_helpdesks(cls) -> Dict[str, Any]:
        """
        Returns verified official government portals, helplines, and reporting mechanisms.
        Accurately distinguishes reporting from automatic prevention.
        """
        return {
            "disclaimer": (
                "Cyber Raksha AI operates as a diagnostic intelligence and alert system for families. "
                "Traditional keypad feature phones (Nokia, Samsung, itel, Lava, Jio Bharat) do not permit automated "
                "software background call/SMS blocking without telecom carrier hardware access. "
                "Official legal prosecution, fraudulent communication investigations, and phone number disconnection "
                "are executed by the Department of Telecommunications (via Sanchar Saathi Chakshu) and Cyber Police (via 1930)."
            ),
            "portals": [
                {
                    "name": "Sanchar Saathi (Chakshu)",
                    "url": "https://sancharsaathi.gov.in/sfc/",
                    "purpose": "Citizen reporting of suspected fraud communications (calls/SMS) before being duped.",
                    "operator": "Department of Telecommunications (DoT), Govt of India"
                },
                {
                    "name": "National Cyber Crime Reporting Portal",
                    "url": "https://cybercrime.gov.in",
                    "purpose": "Formal FIR / complaint registration for cyber frauds, financial loss, or extortion.",
                    "operator": "Ministry of Home Affairs (MHA), Govt of India"
                },
                {
                    "name": "TRAI Do Not Disturb (DND)",
                    "url": "https://trai.gov.in",
                    "purpose": "Commercial telemarketing registration and unsolicited commercial communication complaints.",
                    "operator": "Telecom Regulatory Authority of India (TRAI)"
                }
            ],
            "helplines": [
                {
                    "name": "National Cyber Crime Helpline",
                    "purpose": "Financial fraud freeze & incident reporting",
                    "access_channel": "Toll-Free Helpline (Call 1930)",
                    "contact_or_url": "1930",
                    "how_it_helps": "Immediately call 1930 if money was debited from any bank account or wallet. Fast action within 2-3 hours enables financial transaction freezing."
                },
                {
                    "name": "TRAI UCC / DND Complaint Helpline",
                    "purpose": "Spam call & SMS telemarketer reporting",
                    "access_channel": "SMS / Call to 1909",
                    "contact_or_url": "1909",
                    "how_it_helps": "Send SMS 'COMP TEL NO XXXXXXXXXX, dd/mm/yy, Time' to 1909 to register spam telemarketer complaints."
                },
                {
                    "name": "Emergency Police Assistance",
                    "purpose": "Physical security & emergency response",
                    "access_channel": "Emergency Call (Dial 112)",
                    "contact_or_url": "112",
                    "how_it_helps": "Call 112 if someone is physically threatening, extorting, or harassing an elderly person at home."
                }
            ],
            "legal_clarification": (
                "Cyber Raksha AI operates as a diagnostic intelligence and alert system for families. "
                "Official legal prosecution and phone number disconnection are executed by the Department of "
                "Telecommunications (via Sanchar Saathi) and State Cyber Police (via 1930)."
            )
        }
