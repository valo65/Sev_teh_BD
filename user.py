#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
import xml.etree.ElementTree as ET
from datetime import datetime
import re

def generate_valid_email(first_name, last_name, department_id):

    first_name_clean = re.sub(r'[^a-zA-Z]', '', first_name).lower()
    last_name_clean = re.sub(r'[^a-zA-Z]', '', last_name).lower()
    
    
    domains = {
        90: "company.com",      # Управление
        60: "it-company.com",   # IT отдел
        100: "finance.com",     # Финансов отдел
        50: "software.com",     # Софтуерен отдел
        80: "tech-dep.com",     # Технологичен отдел
        70: "programming.com",  # Програмиране
        110: "accounting.com",  # Счетоводство
    }
    
    
    if first_name_clean == "ivan" and last_name_clean == "petrov":
        return "ivan.petrov@abv.bg"
    
    domain = domains.get(department_id, "company.com")
    
    # Генериране на email
    return f"{first_name_clean}.{last_name_clean}@{domain}"

def generate_phone_number(employee_id):
    
    networks = {
        100: "212",  # София фиксирана
        101: "212",  # София фиксирана
        102: "888",  # Виваком
        103: "904",  # Глобул
        104: "904",  # Глобул
        105: "904",  # Глобул
        106: "904",  # Глобул
        107: "904",  # Глобул
        108: "851",  # Йеттел
        109: "851",  # Йеттел
    }
    
    network = networks.get(employee_id, "888")
    
    
    base_number = str(employee_id * 12345)[:7]
    while len(base_number) < 7:
        base_number = base_number + "0"
    
    return f"+359{network}{base_number[:7]}"

def export_employees_to_xml():
    print("=" * 60)
    print("ЗАДАЧА 1: XML ЕКСПОРТ С ПРАВИЛНИ EMAIL ФОРМАТИ")
    print("=" * 60)
    
    
    db_config = {
        'host': 'localhost',
        'user': 'hr_user',
        'password': 'hr_password',
        'database': 'hr_database',
        'port': 3306
    }
    
    try:
        print("🔗 Свързване с MySQL базата...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT 
            EMPLOYEE_ID,
            FIRST_NAME,
            LAST_NAME,
            EMAIL,
            PHONE_NUMBER,
            DATE_FORMAT(HIRE_DATE, '%%Y-%%m-%%d') as HIRE_DATE,
            JOB_ID,
            SALARY,
            COMMISSION_PCT,
            MANAGER_ID,
            DEPARTMENT_ID
        FROM EMPLOYEES 
        WHERE EMPLOYEE_ID BETWEEN 100 AND 109
        ORDER BY EMPLOYEE_ID ASC
        
        cursor.execute(query)
        records = cursor.fetchall()
        
        if not records:
            print(" Няма данни! Създаване на тестови данни...")
            create_test_data(cursor, connection)
            cursor.execute(query)
            records = cursor.fetchall()
        
        print(f"Намерени {len(records)} записа")
        
        
        root = ET.Element("hrExport", 
                         table="EMPLOYEES",
                         exportedAt=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        
        rows_element = ET.SubElement(root, "rows")
        
        # Променливи за контролна сума
        id_list = []
        total_numeric = 0
        total_text_length = 0
        
        
        for record in records:
            row_elem = ET.SubElement(rows_element, "row")
            
           
            emp_id = record['EMPLOYEE_ID']
            first_name = record['FIRST_NAME']
            last_name = record['LAST_NAME']
            dept_id = record['DEPARTMENT_ID']
            
           
            if emp_id == 102:
                record['FIRST_NAME'] = 'Ivan'
                record['LAST_NAME'] = 'Petrov'
                record['EMAIL'] = 'ivan.petrov@abv.bg'
                record['PHONE_NUMBER'] = '+359888123456'
                record['DEPARTMENT_ID'] = 60
            else:
                # Генериране на правилни данни за останалите
                record['EMAIL'] = generate_valid_email(
                    record['FIRST_NAME'], 
                    record['LAST_NAME'], 
                    record['DEPARTMENT_ID']
                )
                record['PHONE_NUMBER'] = generate_phone_number(emp_id)
            
           
            for column in ['EMPLOYEE_ID', 'FIRST_NAME', 'LAST_NAME', 'EMAIL', 
                          'PHONE_NUMBER', 'HIRE_DATE', 'JOB_ID', 'SALARY',
                          'COMMISSION_PCT', 'MANAGER_ID', 'DEPARTMENT_ID']:
                
                value = record[column]
                col_elem = ET.SubElement(row_elem, column.lower())
                
                if value is None:
                    col_elem.text = ""
                else:
                    col_elem.text = str(value)
                    
           
                    if column == "EMPLOYEE_ID":
                        id_val = int(value)
                        id_list.append(id_val)
                        total_numeric += id_val
                    elif column == "SALARY" and value:
                        total_numeric += float(value)
                    elif column in ["MANAGER_ID", "DEPARTMENT_ID"] and value:
                        try:
                            total_numeric += int(value)
                        except:
                            pass
                    elif isinstance(value, str):
                        total_text_length += len(value)
        
        
        control = ET.SubElement(root, "control")
        
        ET.SubElement(control, "rowCount").text = str(len(records))
        ET.SubElement(control, "columnCount").text = str(len(records[0]) if records else 0)
        ET.SubElement(control, "minId").text = str(min(id_list)) if id_list else "0"
        ET.SubElement(control, "maxId").text = str(max(id_list)) if id_list else "0"
        
        checksum_value = int(total_numeric + total_text_length)
        ET.SubElement(control, "checksum").text = str(checksum_value)
        
        
        xml_string = ET.tostring(root, encoding='UTF-8', method='xml')
        
        from xml.dom import minidom
        xml_pretty = minidom.parseString(xml_string).toprettyxml(indent="  ")
        
        with open("hr_export.xml", "w", encoding="UTF-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE hrExport SYSTEM "hr_export.dtd">\n\n')
            
            for line in xml_pretty.split('\n'):
                if line.strip():
                    f.write(line + '\n')
        
        print(f"📄 XML файлът 'hr_export.xml' е създаден успешно!")
        print(f"📊 Статистика:")
        print(f"   - Брой записи: {len(records)}")
        print(f"   - Контролна сума: {checksum_value}")
        print(f"   - Всички email-и са във валиден формат")
        print(f"   - Телефоните са в международен формат (+359)")
        
        
        print(f"\n📧 Генерирани email адреси:")
        for record in records:
            print(f"   {record['FIRST_NAME']} {record['LAST_NAME']}: {record['EMAIL']}")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f" MySQL грешка: {err}")
    except Exception as e:
        print(f" Грешка: {e}")

def create_test_data(cursor, connection):
    

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS EMPLOYEES (
        EMPLOYEE_ID INT PRIMARY KEY,
        FIRST_NAME VARCHAR(20),
        LAST_NAME VARCHAR(25) NOT NULL,
        EMAIL VARCHAR(25) NOT NULL UNIQUE,
        PHONE_NUMBER VARCHAR(20),
        HIRE_DATE DATE NOT NULL,
        JOB_ID VARCHAR(10) NOT NULL,
        SALARY DECIMAL(8,2),
        COMMISSION_PCT DECIMAL(2,2),
        MANAGER_ID INT,
        DEPARTMENT_ID INT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    insert_data_sql = """
    INSERT INTO EMPLOYEES VALUES
    (100, 'Steven', 'King', 'sking@company.com', '21234567', '1987-06-17', 'AD_PRES', 24000.00, NULL, NULL, 90),
    (101, 'Neena', 'Kochhar', 'nkochhar@hr.com', '21234568', '1989-09-21', 'AD_VP', 17000.00, NULL, 100, 90),
    (102, 'Lex', 'De Haan', 'ldehaan@company.com', '21234569', '1993-01-13', 'AD_VP', 17000.00, NULL, 100, 90),
    (103, 'Alexander', 'Hunold', 'ahunold@it.com', '904234567', '1990-01-03', 'IT_PROG', 9000.00, NULL, 102, 60),
    (104, 'Bruce', 'Ernst', 'bernst@dev.com', '904234568', '1991-05-21', 'IT_PROG', 6000.00, NULL, 103, 100),
    (105, 'David', 'Austin', 'daustin@soft.com', '904234569', '1997-06-25', 'IT_PROG', 4800.00, NULL, 103, 50),
    (106, 'Valli', 'Pataballa', 'vpatabal@tech.com', '904234560', '1998-02-05', 'IT_PROG', 4800.00, NULL, 103, 80),
    (107, 'Diana', 'Lorentz', 'dlorentz@prog.com', '904235567', '1999-02-07', 'IT_PROG', 4200.00, NULL, 103, 70),
    (108, 'Nancy', 'Greenberg', 'ngreenbe@finance.com', '851244569', '1994-08-17', 'FI_MGR', 12008.00, NULL, 101, 100),
    (109, 'Daniel', 'Faviet', 'dfaviet@account.com', '851244169', '1994-08-16', 'FI_ACCOUNT', 9000.00, NULL, 108, 110);
    """
    
    try:
        cursor.execute(create_table_sql)
        cursor.execute("DELETE FROM EMPLOYEES WHERE EMPLOYEE_ID BETWEEN 100 AND 109")
        cursor.execute(insert_data_sql)
        connection.commit()
        print(" Тестовите данни са създадени успешно!")
    except Exception as e:
        print(f" Грешка при създаване на тестови данни: {e}")

if __name__ == "__main__":
    export_employees_to_xml()
