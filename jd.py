import re

def extract_cards_by_date(file_path, target_year="26"):
    extracted_data = []
    
    # النمط للبحث عن البيانات داخل القوسين (تجاوزنا الـ ID والاسم وركزنا على التاريخ)
    # هذا النمط يبحث عن: 'شهر', 'سنة'
    pattern = r"\((.*?),.*?,.*?,.*?,.*?'(\d{2})',.*?'(\d{2})',.*?\)"

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # البحث عن المطابقات في كل سطر
                matches = re.findall(pattern, line)
                for match in matches:
                    full_line = match[0] # باقي البيانات
                    month = match[1]     # الشهر
                    year = match[2]      # السنة
                    
                    if year == target_year:
                        extracted_data.append({
                            "month": month,
                            "year": year,
                            "raw_data": line.strip()
                        })

        # عرض النتائج بشكل مرتب
        if extracted_data:
            print(f"--- تم العثور على {len(extracted_data)} بطاقة لعام 20{target_year} ---")
            for item in extracted_data:
                print(f"📅 التاريخ: {item['month']}/{item['year']} | السجل: {item['raw_data']}")
        else:
            print("لم يتم العثور على بيانات تطابق هذا التاريخ.")

    except FileNotFoundError:
        print("خطأ: لم يتم العثور على ملف الـ SQL. تأكد من مسار الملف.")

# استدعاء الدالة (تأكد من تغيير 'data.sql' لاسم ملفك الحقيقي)
extract_cards_by_date('user_cards.sql', target_year="26")