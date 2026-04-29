import psycopg2
import json
import csv
from datetime import datetime
from new_connect import connect

conn = connect()
cursor = conn.cursor()

# Initialize database schema
def init_db():
    """Initialize database with extended schema"""
    try:
        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            cursor.execute(f.read())
        conn.commit()
        print("Database schema initialized successfully")
    except Exception as e:
        print(f"Error initializing schema: {e}")
        conn.rollback()

def create_contact():
    """Create a new contact with multiple phone numbers"""
    try:
        name = input("Enter name: ").strip()
        if not name:
            print("Name is required!")
            return
        
        email = input("Enter email (optional): ").strip()
        birthday = input("Enter birthday (YYYY-MM-DD, optional): ").strip()
        group = input("Enter group (Family/Work/Friend/Other, optional): ").strip()
        
        # Insert contact
        cursor.execute("""
            INSERT INTO contacts (name, email, birthday, group_id)
            VALUES (%s, %s, %s, (SELECT id FROM groups WHERE name = %s))
            RETURNING id
        """, (name, email, birthday if birthday else None, group if group else None))
        
        contact_id = cursor.fetchone()[0]
        conn.commit()
        
        # Add phones
        while True:
            add_more = input("Add phone number? (y/n): ").lower()
            if add_more != 'y':
                break
            
            phone = input("Enter phone number: ").strip()
            phone_type = input("Enter phone type (home/work/mobile): ").lower()
            while phone_type not in ['home', 'work', 'mobile']:
                phone_type = input("Invalid! Enter type (home/work/mobile): ").lower()
            
            cursor.execute("INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                          (contact_id, phone, phone_type))
            conn.commit()
        
        print(f"Contact '{name}' created successfully!")
    except psycopg2.IntegrityError:
        conn.rollback()
        print("Error: Contact with this name already exists!")
    except Exception as e:
        conn.rollback()
        print(f"Error creating contact: {e}")

def search_contacts():
    """Search contacts by pattern (name, email, or phone)"""
    pattern = input("Enter search pattern: ").strip()
    
    cursor.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    results = cursor.fetchall()
    
    if not results:
        print("No contacts found!")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(results)} contact(s):")
    print(f"{'='*80}")
    for row in results:
        print(f"\nName: {row[1]}")
        if row[2]: print(f"Email: {row[2]}")
        if row[3]: print(f"Birthday: {row[3]}")
        if row[4]: print(f"Group: {row[4]}")
        if row[5]: print(f"Phones: {row[5]}")

def filter_by_group():
    """Filter and display contacts by group"""
    cursor.execute("SELECT name FROM groups ORDER BY name")
    groups = cursor.fetchall()
    
    print("\nAvailable groups:")
    for idx, group in enumerate(groups, 1):
        print(f"{idx}. {group[0]}")
    
    choice = input("Select group number (or enter group name): ").strip()
    
    if choice.isdigit():
        group_name = groups[int(choice)-1][0]
    else:
        group_name = choice
    
    cursor.execute("""
        SELECT c.name, c.email, c.birthday, 
               STRING_AGG(p.phone || '(' || p.type || ')', ', ') as phones
        FROM contacts c
        LEFT JOIN phones p ON c.id = p.contact_id
        WHERE c.group_id = (SELECT id FROM groups WHERE name = %s)
        GROUP BY c.id, c.name, c.email, c.birthday
        ORDER BY c.name
    """, (group_name,))
    
    results = cursor.fetchall()
    
    if not results:
        print(f"No contacts found in group '{group_name}'")
        return
    
    print(f"\n{'='*80}")
    print(f"Contacts in group '{group_name}':")
    print(f"{'='*80}")
    for row in results:
        print(f"\nName: {row[0]}")
        if row[1]: print(f"Email: {row[1]}")
        if row[2]: print(f"Birthday: {row[2]}")
        if row[3]: print(f"Phones: {row[3]}")

def sort_contacts():
    """Sort and display contacts by different criteria"""
    print("\nSort by:")
    print("1. Name")
    print("2. Birthday")
    print("3. Date added")
    
    choice = input("Choose sorting option (1-3): ").strip()
    
    sort_map = {
        '1': 'c.name',
        '2': 'c.birthday NULLS LAST',
        '3': 'c.created_at'
    }
    
    sort_by = sort_map.get(choice, 'c.name')
    
    cursor.execute(f"""
        SELECT c.name, c.email, c.birthday, g.name as group_name,
               STRING_AGG(p.phone || '(' || p.type || ')', ', ') as phones
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name
        ORDER BY {sort_by}
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No contacts found!")
        return
    
    print(f"\n{'='*80}")
    print(f"Sorted contacts:")
    print(f"{'='*80}")
    for row in results:
        print(f"\nName: {row[0]}")
        if row[1]: print(f"Email: {row[1]}")
        if row[2]: print(f"Birthday: {row[2]}")
        if row[3]: print(f"Group: {row[3]}")
        if row[4]: print(f"Phones: {row[4]}")

def paginated_navigation():
    """Interactive paginated navigation"""
    limit = 5  # items per page
    offset = 0
    
    while True:
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.birthday, g.name as group_name,
                   STRING_AGG(p.phone || '(' || p.type || ')', ', ') as phones
            FROM contacts c
            LEFT JOIN groups g ON c.group_id = g.id
            LEFT JOIN phones p ON c.id = p.contact_id
            GROUP BY c.id, c.name, c.email, c.birthday, g.name
            ORDER BY c.name
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        contacts = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total = cursor.fetchone()[0]
        
        if not contacts:
            print("No more contacts!")
            break
        
        print(f"\n{'='*80}")
        print(f"Page {offset//limit + 1} (Showing {len(contacts)} of {total} contacts)")
        print(f"{'='*80}")
        
        for row in contacts:
            print(f"\nName: {row[1]}")
            if row[2]: print(f"Email: {row[2]}")
            if row[3]: print(f"Birthday: {row[3]}")
            if row[4]: print(f"Group: {row[4]}")
            if row[5]: print(f"Phones: {row[5]}")
            print("-" * 40)
        
        action = input("\n[n]ext, [p]revious, [q]uit: ").lower()
        
        if action == 'n' and offset + limit < total:
            offset += limit
        elif action == 'p' and offset - limit >= 0:
            offset -= limit
        elif action == 'q':
            break
        elif action == 'n':
            print("No more pages!")
        elif action == 'p':
            print("Already on first page!")

def add_phone_to_contact():
    """Add phone number to existing contact"""
    name = input("Enter contact name: ").strip()
    phone = input("Enter phone number: ").strip()
    phone_type = input("Enter phone type (home/work/mobile): ").lower()
    
    while phone_type not in ['home', 'work', 'mobile']:
        phone_type = input("Invalid! Enter type (home/work/mobile): ").lower()
    
    try:
        cursor.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
        conn.commit()
        print(f"Phone added to '{name}' successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")

def move_contact_to_group():
    """Move contact to a different group"""
    name = input("Enter contact name: ").strip()
    group = input("Enter group name: ").strip()
    
    try:
        cursor.execute("CALL move_to_group(%s, %s)", (name, group))
        conn.commit()
        print(f"Contact '{name}' moved to group '{group}' successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")

def export_to_json():
    """Export all contacts to JSON file"""
    cursor.execute("""
        SELECT c.name, c.email, c.birthday, g.name as group_name,
               json_agg(json_build_object('phone', p.phone, 'type', p.type)) as phones
        FROM contacts c
        LEFT JOIN groups g ON c.group_id = g.id
        LEFT JOIN phones p ON c.id = p.contact_id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name
    """)
    
    contacts = cursor.fetchall()
    
    output = []
    for contact in contacts:
        contact_data = {
            'name': contact[0],
            'email': contact[1],
            'birthday': str(contact[2]) if contact[2] else None,
            'group': contact[3],
            'phones': contact[4] if contact[4] else []
        }
        output.append(contact_data)
    
    filename = input("Enter JSON filename (default: contacts.json): ").strip()
    if not filename:
        filename = "contacts.json"
    if not filename.endswith('.json'):
        filename += '.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Exported {len(output)} contacts to {filename}")

def import_from_json():
    """Import contacts from JSON file"""
    filename = input("Enter JSON filename: ").strip()
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            contacts = json.load(f)
        
        for contact in contacts:
            name = contact.get('name')
            email = contact.get('email')
            birthday = contact.get('birthday')
            group = contact.get('group')
            phones = contact.get('phones', [])
            
            # Check if contact exists
            cursor.execute("SELECT id FROM contacts WHERE name = %s", (name,))
            existing = cursor.fetchone()
            
            if existing:
                choice = input(f"Contact '{name}' exists. [s]kip or [o]verwrite? ").lower()
                if choice == 's':
                    continue
                # Delete existing contact and phones (cascade will handle phones)
                cursor.execute("DELETE FROM contacts WHERE name = %s", (name,))
                conn.commit()
            
            # Insert contact
            cursor.execute("""
                INSERT INTO contacts (name, email, birthday, group_id)
                VALUES (%s, %s, %s, (SELECT id FROM groups WHERE name = %s))
                RETURNING id
            """, (name, email, birthday if birthday else None, group if group else None))
            
            contact_id = cursor.fetchone()[0]
            
            # Insert phones
            for phone_data in phones:
                cursor.execute("""
                    INSERT INTO phones (contact_id, phone, type)
                    VALUES (%s, %s, %s)
                """, (contact_id, phone_data['phone'], phone_data['type']))
            
            conn.commit()
            print(f"Imported contact: {name}")
        
        print(f"Successfully imported {len(contacts)} contacts!")
    except Exception as e:
        conn.rollback()
        print(f"Error importing from JSON: {e}")

def import_from_csv():
    """Extended CSV import with new fields"""
    filename = input("Enter CSV filename (default: contacts.csv): ").strip()
    if not filename:
        filename = "contacts.csv"
    
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                
                name = row[0].strip()
                phone = row[1].strip() if len(row) > 1 else None
                email = row[2].strip() if len(row) > 2 else None
                birthday = row[3].strip() if len(row) > 3 else None
                group = row[4].strip() if len(row) > 4 else None
                phone_type = row[5].strip() if len(row) > 5 else 'mobile'
                
                if phone_type not in ['home', 'work', 'mobile']:
                    phone_type = 'mobile'
                
                # Check if contact exists
                cursor.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    choice = input(f"Contact '{name}' exists. [s]kip or [o]verwrite? ").lower()
                    if choice == 's':
                        continue
                    cursor.execute("DELETE FROM contacts WHERE name = %s", (name,))
                    conn.commit()
                
                # Insert contact
                cursor.execute("""
                    INSERT INTO contacts (name, email, birthday, group_id)
                    VALUES (%s, %s, %s, (SELECT id FROM groups WHERE name = %s))
                    RETURNING id
                """, (name, email, birthday if birthday else None, group if group else None))
                
                contact_id = cursor.fetchone()[0]
                
                # Insert phone
                if phone:
                    cursor.execute("""
                        INSERT INTO phones (contact_id, phone, type)
                        VALUES (%s, %s, %s)
                    """, (contact_id, phone, phone_type))
                
                conn.commit()
                print(f"Imported contact: {name}")
        
        print("CSV import completed!")
    except Exception as e:
        conn.rollback()
        print(f"Error importing CSV: {e}")

def display_menu():
    """Display main menu"""
    print("\n" + "="*50)
    print("EXTENDED PHONEBOOK APPLICATION")
    print("="*50)
    print("1. Add new contact")
    print("2. Add phone to existing contact")
    print("3. Move contact to group")
    print("4. Search contacts")
    print("5. Filter by group")
    print("6. Sort contacts")
    print("7. Paginated navigation")
    print("8. Export to JSON")
    print("9. Import from JSON")
    print("10. Import from CSV (extended)")
    print("11. Delete contact")
    print("12. Quit")
    print("="*50)

def delete_contact():
    """Delete a contact"""
    term = input("Enter name or phone number to delete: ").strip()
    cursor.execute("DELETE FROM contacts WHERE name = %s OR id IN (SELECT contact_id FROM phones WHERE phone = %s)", (term, term))
    conn.commit()
    print(f"Deleted contacts matching '{term}'")

def main():
    """Main application loop"""
    init_db()  # Initialize database schema
    
    while True:
        display_menu()
        choice = input("Choose an option (1-12): ").strip()
        
        if choice == '1':
            create_contact()
        elif choice == '2':
            add_phone_to_contact()
        elif choice == '3':
            move_contact_to_group()
        elif choice == '4':
            search_contacts()
        elif choice == '5':
            filter_by_group()
        elif choice == '6':
            sort_contacts()
        elif choice == '7':
            paginated_navigation()
        elif choice == '8':
            export_to_json()
        elif choice == '9':
            import_from_json()
        elif choice == '10':
            import_from_csv()
        elif choice == '11':
            delete_contact()
        elif choice == '12':
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed")