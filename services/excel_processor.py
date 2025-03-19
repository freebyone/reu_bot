import pandas as pd
from collections import defaultdict

df = pd.read_excel("file.xlsx", header=1, names=[
    "Секция",
    "Название проекта", 
    "Школа_лидера",
    "Класс",
    "Формат выступления",
    "Дата_время",
    "Слот",
    "Лидер проекта",
    "Школа_уч1",
    "Участник 1",
    "Школа_уч2",
    "Участник 2", 
    "Школа_апр",
    "Аудитория"
])

all_schools = []
for school_col in ['Школа_лидера', 'Школа_уч1', 'Школа_уч2', 'Школа_апр']:
    all_schools.extend(df[school_col].dropna().unique())

# Нормализация названий школ
all_schools = [str(s).strip() for s in all_schools if pd.notna(s)]
unique_schools = sorted(list(set(all_schools)))

# Создаем словари для школ
schools = [{"id": idx+1, "name": school} for idx, school in enumerate(unique_schools)]
school_name_to_id = {s['name']: s['id'] for s in schools}

products = []
product_name_to_id = {}

for idx, row in df.iterrows():
    product = {
        "id_product": idx + 1,
        "section": row['Секция'],
        "product_name": row['Название проекта'],
        "date_time": row['Дата_время'],
        "id_school": school_name_to_id.get(str(row['Школа_лидера']).strip(), None),
        "location": row['Аудитория']
    }
    products.append(product)
    product_name_to_id[row['Название проекта']] = idx + 1

students = []

for idx, row in df.iterrows():
    participants = {
        'Лидер проекта': row['Лидер проекта'],
        'Участник 1': row['Участник 1'],
        'Участник 2': row['Участник 2']
    }
    
    school_mapping = {
        'Лидер проекта': row['Школа_лидера'],
        'Участник 1': row['Школа_уч1'],
        'Участник 2': row['Школа_уч2']
    }
    
    for role, fio in participants.items():
        if pd.notna(fio):
            fio_clean = str(fio).strip()
            school = str(school_mapping[role]).strip()
            
            students.append({
                "FIO": fio_clean,
                "id_school": school_name_to_id.get(school, None),
                "id_product": product_name_to_id[row['Название проекта']],
                "grade": row['Класс']
            })
            
for idx, row in df.iterrows():
    participants = {
        'Лидер проекта': row['Лидер проекта'],
        'Участник 1': row['Участник 1'],
        'Участник 2': row['Участник 2']
    }
    
    school_mapping = {
        'Лидер проекта': row['Школа_лидера'],
        'Участник 1': row['Школа_уч1'],
        'Участник 2': row['Школа_уч2']
    }
    
    for role, fio in participants.items():
        if pd.notna(fio):
            fio_clean = str(fio).strip()
            school = str(school_mapping[role]).strip()
            
            students.append({
                "FIO": fio_clean,
                "id_school": school_name_to_id.get(school, None),
                "id_product": product_name_to_id[row['Название проекта']],
                "grade": row['Класс']
            })
# Вывод результатов
print("="*50)
print("Школы:")
for school in schools:
    print(f"{school['id']}: {school['name']}")

print("\n" + "="*50)
print("Продукты (первые 3):")
for product in products[:10]:
    print(product)

print("\n" + "="*50)
print("Участники (первые 5):")
for student in students[:10]:
    print(student)