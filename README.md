# Molakhasat Bot 🤖📚

بوت تليجرام بيّاع ملخصات: الطالب يختار الملخص، يحوّل الفلوس فودافون كاش أو إنستاباي، يبعت صورة الإيصال، وإنت توافق بضغطة زرار فيوصله الملف لوحده.

A small Telegram bot for selling study summaries (PDFs) in Egypt, with manual Vodafone Cash / InstaPay payment confirmation. No payment gateway, no website, no monthly cost.

---

## الفكرة

- **مين بيدفع؟** طلبة الكلية (زمايلك والدفعات اللي قبلك وبعدك) اللي بيشتروا ملخصات ومراجعات قبل الامتحانات.
- **بيدفعوا إزاي؟** فودافون كاش أو إنستاباي، وإنت بتأكد التحويل بعينك قبل ما البوت يبعت الملف. مفيش بوابة دفع ومفيش عمولات.
- **إنت بتعمل إيه؟** بتكتب الملخص (أو تجمّع مراجعة كويسة)، ترفعها للبوت مرة واحدة، والبوت يكمل البيع والتسليم.

## المميزات

- كتالوج منتجات بأسعار (أزرار جاهزة للمشتري).
- استقبال صورة الإيصال وتحويلها ليك بزرارين: ✅ قبول / ❌ رفض.
- تسليم الملف تلقائياً بعد القبول.
- أوامر أدمن: إضافة منتج، إيقاف منتج، الطلبات المستنية، إحصائيات المبيعات.
- قاعدة بيانات SQLite: مفيش سيرفر قواعد بيانات، كل حاجة في ملف واحد.

## التشغيل خطوة بخطوة

### 1. اعمل البوت على تليجرام

1. افتح تليجرام وكلم [@BotFather](https://t.me/BotFather).
2. ابعت `/newbot` واختار اسم ويوزرنيم للبوت.
3. هيديك **توكن** شكله كده: `123456:ABC-DEF...` — خده ومتبعتهوش لحد.

### 2. اعرف رقم حسابك (Admin ID)

كلم [@userinfobot](https://t.me/userinfobot) وهو يقولك رقمك.

### 3. جهّز الإعدادات

```bash
cp .env.example .env
```

وافتح ملف `.env` واملأ:

- `BOT_TOKEN` التوكن اللي جالك من BotFather.
- `ADMIN_ID` رقمك من userinfobot.
- `PAYMENT_DETAILS` رقم الفودافون كاش أو حساب الإنستاباي بتاعك (ده اللي هيظهر للمشتري).

### 4. شغّل البوت

على جهازك:

```bash
pip install -r requirements.txt
python bot.py
```

### 5. ارفع أول ملخص

ابعت للبوت ملف الـPDF وفي الوصف (caption) اكتب:

```
مراجعة علم النفس العام | 25
```

يعني: الاسم، علامة `|`، السعر بالجنيه. البوت هيرد برقم المنتج ويبقى متاح للبيع.

## تشغيله ٢٤ ساعة ببلاش

البوت لازم يفضل شغال عشان يرد على الناس. أسهل طرق مجانية:

- **موبايلك أو لابتوبك:** شغّله وسيبه، بس لو اتقفل الجهاز البوت يقف.
- **PythonAnywhere** (خطة مجانية): ارفع الملفات وشغّل `python bot.py` من Always-on task أو كونسول مفتوح.
- **Railway / Render:** خطط مجانية للمشاريع الصغيرة (محتاجة ربط بالريبو ده).

## أوامر الأدمن

| الأمر | الوظيفة |
| --- | --- |
| إرسال PDF + وصف `الاسم \| السعر` | إضافة منتج جديد |
| `/list` | عرض كل المنتجات وأرقامها |
| `/remove رقم` | إيقاف منتج عن البيع |
| `/orders` | الطلبات اللي مستنية مراجعة |
| `/stats` | عدد الطلبات وإجمالي المبيعات |
| `/help` | تذكير بالأوامر |

## الحدود (بصراحة)

- تأكيد الدفع **يدوي**: لازم تبص على رصيدك وتتأكد إن التحويل وصل قبل ما تدوس قبول. البوت بيوصّلك الصورة بس.
- البوت بيبيع **ملفات رقمية بس** (PDF ونحوها)، مش شحن ولا منتجات حقيقية.
- لو حد عمل رفض بالغلط مفيش تراجع تلقائي، بس تقدر تبعتله الملف بنفسك من الشات.
- البوت مش بيمنع حد يشارك الملف بعد ما يشتريه، دي طبيعة الملفات الرقمية.

## English

A minimal Telegram shop bot (Python + `python-telegram-bot` + SQLite) for selling PDF study notes in Egypt:

1. Buyer picks a product from an inline catalog.
2. Bot replies with manual payment details (Vodafone Cash / InstaPay).
3. Buyer sends a receipt photo; the admin gets it with approve/reject buttons.
4. On approval, the bot delivers the PDF automatically.

Setup: copy `.env.example` to `.env`, fill in `BOT_TOKEN` (from @BotFather), `ADMIN_ID` (from @userinfobot), and `PAYMENT_DETAILS`. Then `pip install -r requirements.txt && python bot.py`. Admin adds products by sending the bot a PDF with caption `Name | Price`.
