<p align="center">
  <img src="hotel-bookings-analysis/reports/project_cover.png" alt="Hotel booking cancellation analysis" width="100%">
</p>

<h2 align="center">تحليل الحجوزات الفندقية ومخاطر الإلغاء</h2>
<p align="center">تحليل وصفي ومقارنة نماذج تعلم آلي باستخدام بيانات حجوزات City Hotel وResort Hotel.</p>

---

## عن المشروع

يركز المشروع على سؤال عملي: ما الأنماط المرتبطة بإلغاء الحجوزات، وإلى أي مدى يمكن تقدير خطر الإلغاء من تفاصيل الحجز؟ يبدأ العمل بفحص البيانات وتنظيفها، ثم يستعرض معدلات الإلغاء حسب نوع الفندق وفترة الحجز المسبق وشهر الوصول. بعد ذلك يقارن نموذج Logistic Regression مع Random Forest.

## النتائج الرئيسية

| المؤشر | النتيجة |
|---|---:|
| السجلات في الملف الأصلي | 119,390 |
| الصفوف المتطابقة بالكامل | 31,994 |
| السجلات بعد استبعاد التطابق | 87,396 |
| معدل الإلغاء بعد التنظيف | 27.5% |
| أفضل ROC-AUC على مجموعة الاختبار | 0.875 — Random Forest |

بعد التنظيف، بلغ معدل الإلغاء 30.0% في City Hotel و23.5% في Resort Hotel. وكان وسيط الفترة بين الحجز والوصول 80 يومًا للحجوزات الملغاة، مقابل 38 يومًا للحجوزات المكتملة.

### مقارنة النماذج

| النموذج | ROC-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.856 | 0.550 | 0.810 | 0.655 |
| **Random Forest** | **0.875** | 0.539 | **0.849** | **0.659** |

Random Forest التقط نسبة أكبر من الإلغاءات في مجموعة الاختبار، مع عدد أكبر من التنبيهات التي لا تنتهي بإلغاء. اختيار عتبة التنبيه في الاستخدام العملي يعتمد على تكلفة التواصل مع النزيل وتكلفة تفويت حجز معرض للإلغاء.

## استكشف الرسوم

<p align="center">
  <img src="hotel-bookings-analysis/reports/cancellation_by_hotel.png" alt="Cancellation rate by hotel" width="32%">
  <img src="hotel-bookings-analysis/reports/cancellation_by_lead_time.png" alt="Cancellation rate by lead time" width="32%">
  <img src="hotel-bookings-analysis/reports/cancellation_by_month.png" alt="Cancellation rate by arrival month" width="32%">
</p>

<p align="center"><em>معدلات الإلغاء حسب نوع الفندق، والفترة بين الحجز والوصول، وشهر الوصول.</em></p>

## المنهجية

- عولجت القيم الناقصة داخل مسار تجهيز البيانات، واستُبعد عمود `company` لارتفاع نسبة القيم المفقودة فيه.
- استُبعدت حالة الحجز النهائية وتاريخ تسجيلها من النموذج لأنها تكشف النتيجة بعد وقوعها. استُبعد كذلك نوع الغرفة المخصصة وتعديلات الحجز لتجنب استخدام معلومات قد لا تكون متاحة عند إنشاء الحجز.
- أزيلت الصفوف المتطابقة عبر الأعمدة الـ32 قبل تقسيم البيانات. لا يحتوي المصدر على معرّف حجز؛ لذلك قد تكون بعض الصفوف المتطابقة حجوزات مستقلة وليست نسخًا مكررة. تغيّر معدل الإلغاء من 37.0% في الملف الأصلي إلى 27.5% بعد هذه الخطوة، ويعرض التقرير أثر ذلك صراحة.
- التقييم يستخدم تقسيمًا عشوائيًا طبقيًا بنسبة 75/25 وبذرة ثابتة. النتيجة تقدير على هذا التقسيم وليست ضمانًا لأداء مستقبلي.

## التقرير والملفات

- [التقرير الكامل](hotel-bookings-analysis/reports/report.md)
- [تقرير HTML](hotel-bookings-analysis/reports/report.html)
- [المقاييس بصيغة JSON](hotel-bookings-analysis/reports/metrics.json)
- [كود التحليل والتدريب](hotel-bookings-analysis/src/analyze.py)
- [تعليمات التشغيل](hotel-bookings-analysis/README.md)

## التشغيل محليًا

يتطلب Python 3.10 أو أحدث.

```bash
cd hotel-bookings-analysis
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/analyze.py
```

## مصدر البيانات

Hotel Booking Demand dataset. يوثق المصدر البحثي سجلات حجوزات لفندق مدينة ومنتجع في البرتغال. [Antonio, de Almeida & Nunes (2019), *Data in Brief*](https://doi.org/10.1016/j.dib.2018.11.126).

---

<p align="center"><sub>Python · Pandas · Scikit-learn · Matplotlib</sub></p>
