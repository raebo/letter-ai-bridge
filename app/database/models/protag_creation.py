from app.database.connection import DBConnection

class ProtagCreation:
    """Model for handling Protagcreation -related database operations"""

    @classmethod
    def entity_profile(cls, key: str) -> dict:
        """
        Fetches place data from the database by its unique key.
        Returns a dictionary of columns or None if not found.
        """
        # Using a context manager for the connection to ensure it closes properly
        conn = DBConnection.get_connection()
        try:
            with conn.cursor() as cur:
                # We select exactly the columns the Service needs for _build_info_string
                # Adjust 'name' and 'country_name' to your actual column names
                query = """
                SELECT 
                    c.id,
                    c.name AS creation_name,
                    c.key AS creation_key,
                    c.info AS creation_info,
                    c.mwv AS creation_mwv,
                    c.op AS creation_op,
                    c.notes AS creation_notes,
                    p.name AS parent_name,
                    p.key AS parent_key,
                    p.info AS parent_info,
                    p.mwv AS parent_mwv,
                    p.op AS parent_op,
                    p.notes AS parent_notes,
                    c.updated_at AS last_updated_at
                FROM protag_creations c
                LEFT JOIN protag_creations p ON c.parent_id = p.id
                WHERE c.key = %s;
                """
                cur.execute(query, (key,))
                row = cur.fetchone()

                if not row:
                    return {}

                protag_creation_id = row[0]
                data = {
                    "c_name": row[1],
                    "c_key": row[2],
                    "c_info": row[3],
                    "c_mwv": row[4],
                    "c_op": row[5],
                    "c_notes": row[6],
                    "p_name": row[7],
                    "p_key": row[8],
                    "p_info": row[9],
                    "p_mwv": row[10],
                    "p_op": row[11],
                    "p_notes": row[12],
                    "c_last_updated_at": row[13],
                    "categories": []
                    }
                categories_query = """
                WITH RECURSIVE category_path AS (
                    -- 1. Base Case: Get the starting category using the Creation ID
                    SELECT 
                        id, 
                        protag_creation_category_id, 
                        name, 
                        1 AS depth
                    FROM protag_creation_categories
                    WHERE id = (SELECT protag_creation_category_id FROM protag_creations WHERE id = %s)

                    UNION ALL

                    -- 2. Recursive Step: Move up to the parent
                    SELECT 
                        parent.id, 
                        parent.protag_creation_category_id, 
                        parent.name, 
                        cp.depth + 1
                    FROM protag_creation_categories parent
                    INNER JOIN category_path cp ON cp.protag_creation_category_id = parent.id
                )
                -- 3. Final selection ordered from the top-most parent (Root) to the specific category
                SELECT 
                    name, 
                    id
                FROM 
                    category_path
                ORDER BY depth DESC;
                """
                cur.execute(categories_query, (protag_creation_id,))
                category_rows = cur.fetchall()

                for cat in category_rows:
                    data["categories"].append({
                        "name": cat[0],
                    })

                return data    
        except Exception as e:
            print(f"Error fetching place with key {key}: {e}")
            return {}
        finally:
            conn.close()
