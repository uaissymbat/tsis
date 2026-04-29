-- Procedure to add phone to existing contact
CREATE OR REPLACE PROCEDURE add_phone(p_contact_name VARCHAR, p_phone VARCHAR, p_type VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Get contact ID
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact % not found', p_contact_name;
    END IF;
    
    -- Insert phone
    INSERT INTO phones(contact_id, phone, type) 
    VALUES(v_contact_id, p_phone, p_type);
    
    RAISE NOTICE 'Phone added successfully to contact %', p_contact_name;
END;
$$;

-- Procedure to move contact to group (creates group if not exists)
CREATE OR REPLACE PROCEDURE move_to_group(p_contact_name VARCHAR, p_group_name VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
    v_contact_id INTEGER;
BEGIN
    -- Get contact ID
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact % not found', p_contact_name;
    END IF;
    
    -- Get or create group
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    
    IF v_group_id IS NULL THEN
        INSERT INTO groups(name) VALUES(p_group_name) RETURNING id INTO v_group_id;
        RAISE NOTICE 'Created new group: %', p_group_name;
    END IF;
    
    -- Update contact's group
    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
    
    RAISE NOTICE 'Contact % moved to group %', p_contact_name, p_group_name;
END;
$$;

-- Extended search function (searches across name, email, and all phones)
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id INTEGER, 
    name VARCHAR, 
    email VARCHAR, 
    birthday DATE, 
    group_name VARCHAR,
    phones TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name AS group_name,
        STRING_AGG(DISTINCT p.phone || '(' || p.type || ')', ', ') AS phones
    FROM contacts c
    LEFT JOIN groups g ON c.group_id = g.id
    LEFT JOIN phones p ON c.id = p.contact_id
    WHERE c.name ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR EXISTS (SELECT 1 FROM phones WHERE contact_id = c.id AND phone ILIKE '%' || p_query || '%')
    GROUP BY c.id, c.name, c.email, c.birthday, g.name
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;