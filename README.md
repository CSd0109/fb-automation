# 🚀 Facebook Reels 24/7 Auto Uploader (Personal Profile ID)

> 🇳🇵 **नेपाली समय:** बिहान ७:०० बजे, दिउँसो १:०० बजे, दिउँसो ४:०० बजे र साँझ ७:०० बजे (7:00 AM, 1:00 PM, 4:00 PM, 7:00 PM NPT)  
> ☁️ **GitHub Actions** मा २४/७ अटोमेशन — तपाईँ अनलाइन हुनुहोस् वा अफलाइन, कम्प्युटर बन्द भए पनि रिलहरू समयमै अपलोड हुन्छन्।  
> 👤 **Personal Profile / Facebook ID** मा सिधै अपलोड (कुनै Page चाहिदैन)।

---

## 📌 यो अटोमेशनले कसरी काम गर्छ?

1. **समय तालिका (Nepali Time Schedule):**
   - 🌅 बिहान **०७:०० AM NPT** (01:15 UTC)
   - ☀️ दिउँसो **०१:०० PM NPT** (07:15 UTC)
   - 🌤️ दिउँसो **०४:०० PM NPT** (10:15 UTC)
   - 🌙 साँझ **०७:०० PM NPT** (13:15 UTC)

2. **Personal Profile Support:**
   फेसबुकको अफिसियल Graph API ले Personal ID (व्यक्तिगत प्रोफाइल) मा रिल अपलोड गर्न दिँदैन (Page मा मात्र दिन्छ)। त्यसैले यो अटोमेशनले **Playwright Headless Browser** र **सुरक्षित Session State** प्रयोग गरेर तपाईँकै फेसबुक आइडीमा रिल अपलोड गर्छ।

3. **Auto AI Caption & Hashtags:**
   यदि तपाईँले `GEMINI_API_KEY` राख्नुभयो भने, Gemini AI ले भिडियो एनालाइसिस गरेर आफैँ आकर्षक नेपाली/अंग्रेजी क्याप्सन र भाइरल ह्यासट्यागहरू (`#fyp #reels #nepal #trending`) जेनेरेट गर्छ।

4. **डुप्लिकेट नहुने प्रणाली (Queue & History):**
   `posted_history.json` ले कुन भिडियो अपलोड भइसक्यो भनेर रेकर्ड राख्छ र अर्को पटक नयाँ भिडियो मात्र अपलोड गर्छ।

---

## 🛠️ Step-by-Step Setup Guide (कसरी सेटअप गर्ने?)

### १. पहिलो पटक लगइन सेसन सेभ गर्नुहोस् (One-Time Local Login)
आफ्नो कम्प्युटरको टर्मिनलमा यो कमाण्ड चलाउनुहोस्:

```bash
cd facebook_reels_auto_uploader
python save_session.py
```

- एउटा क्रोम ब्राउजर खुल्नेछ।
- त्यसमा आफ्नो फेसबुक आइडी लगइन गर्नुहोस् (र 2FA कोड हाल्नुहोस्)।
- लगइन पूरा भएपछि टर्मिनलमा आएर `ENTER` थिच्नुहोस्।
- यसले `facebook_session.json` फाइल बनाइदिनेछ (जसमा लगइन कुकी सुरक्षित हुन्छ)।

---

### २. GitHub मा नयाँ Private Repository बनाउनुहोस्
1. [GitHub.com](https://github.com/new) मा गएर नयाँ **Private Repository** बनाउनुहोस् (नाम: `facebook-reels-uploader`)।
2. यो प्रोजेक्टलाई गिटहबमा पुश गर्नुहोस्:

```bash
git init
git add .
git commit -m "Initial Facebook Reels Uploader"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/facebook-reels-uploader.git
git push -u origin main
```

---

### ३. GitHub Secrets थप्नुहोस् (Add Secrets)
1. आफ्नो GitHub Repository खोल्नुहोस्।
2. **Settings** -> **Secrets and variables** -> **Actions** मा जानुहोस्।
3. **"New repository secret"** मा क्लिक गरेर निम्न सेक्रेट्स थप्नुहोस्:

| Secret Name | विवरण (Value) | अनिवार्य? |
|---|---|---|
| `FB_STORAGE_STATE` | `facebook_session.json` फाइलको सम्पूर्ण JSON टेक्स्ट कपि गरेर यहाँ पेस्ट गर्नुहोस् | ✅ **अनिवार्य** |
| `GEMINI_API_KEY` | तपाईँको Google Gemini API Key | 🌟 ऐच्छिक (AI क्याप्सनको लागि) |
| `TELEGRAM_BOT_TOKEN` | टेलिग्राम बोट टोकन (मोबाइलमा अलर्ट पाउन) | 🌟 ऐच्छिक |
| `TELEGRAM_CHAT_ID` | तपाईँको टेलिग्राम च्याट आइडी | 🌟 ऐच्छिक |

---

### ४. नयाँ भिडियोहरू कसरी थप्ने?
1. आफ्ना रिल भिडियोहरू (`.mp4` फाइलहरू) `videos/` फोल्डर भित्र राख्नुहोस्। उदाहरणका लागि: `videos/reel1.mp4`, `videos/reel2.mp4`
2. यदि आफैँ क्याप्सन लेख्न चाहनुहुन्छ भने `queue.json` मा क्याप्सन लेख्न सक्नुहुन्छ वा खाली छोडिदिन सक्नुहुन्छ (Gemini ले आफैँ लेख्छ):
```json
[
  {
    "filename": "reel1.mp4",
    "caption": "🔥 Check out this awesome Reel! #nepal #viral"
  },
  {
    "filename": "reel2.mp4",
    "caption": ""
  }
]
```
3. गिटहबमा कमिट गरेर पुश गर्नुहोस्:
```bash
git add videos/ queue.json
git commit -m "Added new reels to queue"
git push origin main
```

---

### ५. परीक्षण गर्नुहोस् (Instant Manual Test)
नियमित समय (७ बजे, १ बजे, ४ बजे, ७ बजे) सम्म नपर्खीकन तुरुन्तै परीक्षण गर्न:
1. GitHub Repository मा गएर **"Actions"** ट्याबमा क्लिक गर्नुहोस्।
2. बायाँपट्टी **"Facebook Reels 24/7 Auto Uploader"** छान्नुहोस्।
3. दायाँपट्टी **"Run workflow"** बटन थिच्नुहोस्।
4. केही मिनेटमै रिल तपाईँको व्यक्तिगत फेसबुक प्रोफाइलमा अपलोड हुनेछ र स्क्रिनसट लगमा सुरक्षित हुनेछ!

---

## 📁 फोल्डर संरचना (Project Structure)
```
facebook_reels_auto_uploader/
├── .github/
│   └── workflows/
│       └── upload_reels.yml       # २४/७ नेपाली समय तालिकामा चल्ने GitHub Action
├── videos/                        # अपलोड हुने भिडियोहरू राख्ने ठाउँ (.mp4)
├── logs/                          # अपलोड स्क्रिनसट र लगहरू
├── queue.json                     # भिडियोहरूको सूची र क्याप्सन
├── posted_history.json            # अपलोड भइसकेका भिडियोहरूको इतिहास
├── save_session.py                # पहिलो पटक फेसबुक लगइन गर्ने टुल
├── uploader.py                    # मुख्य Playwright अटोमेशन इन्जिन
├── requirements.txt               # आवश्यक Python लाइब्रेरीहरू
├── .env.example                   # कन्फिगरेसन उदाहरण
└── README.md                      # पूर्ण गाइड
```
