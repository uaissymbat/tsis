import psycopg2
import json
import csv
from new_connect import connect

conn = connect()
cursor = conn.cursor()

def init_db():
    try:
        with open('schema.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        conn.commit()
        with open('procedures.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        conn.commit()
    except Exception as e:
        conn.rollback()

def create_contact():
    name = input("Enter name: ").strip()
    email = input("Enter email: ").strip()
    birthday = input("Enter birthday (YYYY-MM-DD): ").strip()
    group = input("Enter group: ").strip()
    
    cursor.execute("""
        INSERT INTO contacts (name, email, birthday, group_id)
        VALUES (%s, %s, %s, (SELECT id FROM groups WHERE name = %s))
        RETURNING id
    """, (name, email, birthday if birthday else None, group if group else None))
    
    contact_id = cursor.fetchone()[0]
    
    phone = input("Enter phone number: ").strip()
    phone_type = input("Enter phone type (home/work/mobile): ").strip()
    
    cursor.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                  (contact_id, phone, phone_type))
    conn.commit()
    print(f"Contact '{name}' created!")

def search_contacts():
    pattern = input("Enter search pattern: ").strip()
    cursor.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    results = cursor.fetchall()
    
    for row in results:
        print(f"Name: {row[1]}, Email: {row[2]}, Phones: {row[5]}")

def add_phone_to_contact():
    name = input("Enter contact name: ").strip()
    phone = input("Enter phone number: ").strip()
    phone_type = input("Enter phone type (home/work/mobile): ").strip()
    
    cursor.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
    conn.commit()
    print(f"Phone added to '{name}'!")

def move_contact_to_group():
    name = input("Enter contact name: ").strip()
    group = input("Enter group name: ").strip()
    
    cursor.execute("CALL move_to_group(%s, %s)", (name, group))
    conn.commit()
    print(f"Contact '{name}' moved to group '{group}'!")

def delete_contact():
    name = input("Enter contact name: ").strip()
    cursor.execute("DELETE FROM contacts WHERE name = %s", (name,))
    conn.commit()
    print(f"Contact '{name}' deleted!")

def view_all():
    cursor.execute("""
        SELECT c.name, c.email, STRING_AGG(p.phone || '(' || p.type || ')', ', ')
        FROM contacts c
        LEFT JOIN phones p ON c.id = p.contact_id
        GROUP BY c.id, c.name, c.email
    """)
    
    for name, email, phones in cursor.fetchall():
        print(f"{name} - {email} - {phones}")

def filter_by_group():
    group = input("Enter group name: ").strip()
    cursor.execute("""
        SELECT c.name, c.email, STRING_AGG(p.phone || '(' || p.type || ')', ', ')
        FROM contacts c
        LEFT JOIN phones p ON c.id = p.contact_id
        WHERE c.group_id = (SELECT id FROM groups WHERE name = %s)
        GROUP BY c.id, c.name, c.email
    """, (group,))
    
    for name, email, phones in cursor.fetchall():
        print(f"{name} - {email} - {phones}")

def sort_contacts():
    print("1. By name")
    print("2. By birthday")
    choice = input("Choose: ")
    
    if choice == '1':
        cursor.execute("SELECT name, email FROM contacts ORDER BY name")
    else:
        cursor.execute("SELECT name, email FROM contacts ORDER BY birthday NULLS LAST")
    
    for name, email in cursor.fetchall():
        print(f"{name} - {email}")

def pagination():
    limit = int(input("Limit: "))
    offset = int(input("Offset: "))
    
    cursor.execute("""
        SELECT name, email FROM contacts ORDER BY name LIMIT %s OFFSET %s
    """, (limit, offset))
    
    for name, email in cursor.fetchall():
        print(f"{name} - {email}")

def export_json():
    cursor.execute("SELECT name, email FROM contacts")
    data = [{"name": row[0], "email": row[1]} for row in cursor.fetchall()]
    
    with open("export.json", "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("Exported to export.json")

def import_json():
    with open("export.json", "r", encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        cursor.execute("INSERT INTO contacts (name, email) VALUES (%s, %s) ON CONFLICT DO NOTHING", 
                      (item["name"], item["email"]))
    conn.commit()
    print("Imported from export.json")

def import_csv():
    filename = input("CSV filename: ")
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                name = parts[0]
                phone = parts[1]
                
                cursor.execute("INSERT INTO contacts (name) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id", (name,))
                contact_id = cursor.fetchone()
                
                if contact_id:
                    cursor.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, 'mobile')", 
                                  (contact_id[0], phone))
    conn.commit()
    print("CSV imported")

def display_menu():
    print("\n1. Add contact")
    print("2. Search")
    print("3. Add phone")
    print("4. Move to group")
    print("5. Delete")
    print("6. View all")
    print("7. Filter by group")
    print("8. Sort contacts")
    print("9. Pagination")
    print("10. Export JSON")
    print("11. Import JSON")
    print("12. Import CSV")
    print("13. Exit")

def main():
    init_db()
    
    while True:
        display_menu()
        choice = input("Choose: ")
        
        if choice == '1':
            create_contact()
        elif choice == '2':
            search_contacts()
        elif choice == '3':
            add_phone_to_contact()
        elif choice == '4':
            move_contact_to_group()
        elif choice == '5':
            delete_contact()
        elif choice == '6':
            view_all()
        elif choice == '7':
            filter_by_group()
        elif choice == '8':
            sort_contacts()
        elif choice == '9':
            pagination()
        elif choice == '10':
            export_json()
        elif choice == '11':
            import_json()
        elif choice == '12':
            import_csv()
        elif choice == '13':
            break

if __name__ == "__main__":
    main()
    cursor.close()
    conn.close()
