import sqlite3
from keyboard.inline.get_ban_unban import SERVERS

# Путь к БД
path_to_db = "data/botBD.sqlite"

def add_complaint(data):
    with sqlite3.connect(path_to_db) as db:
        db.execute("INSERT INTO storage_complaints "
                   "(user_id, server_type, server_number, violator_nickname, submission_time, unique_id, complaint_info, status, tags) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   [data['user'], data['type'], data['number'], data['nickname'], data['time'], data['id'], data['information'], 0, data['tags']])  # Assuming 0 as the default status
        db.commit()

import sqlite3

def find_complaint(data, status):
    with sqlite3.connect(path_to_db) as db:
        query = "SELECT * FROM storage_complaints WHERE status = :status"
        conditions = []

        if data.get('server', False):
            conditions.append(f"server_number = :server")
        if data.get('nick', False):
            conditions.append(f"violator_nickname = :nick")
        if data.get('tags', False):
            conditions.append(f"tags LIKE :tags")

        if conditions:
            query += " AND " + " AND ".join(conditions)

        if data.get('time', '') == 'new':
            query += " ORDER BY submission_time DESC"
        elif data.get('time', '') == 'old':
            query += " ORDER BY submission_time ASC"

        params = {
            'status': status,
            'server': data.get('server', ''),
            'nick': data.get('nick', ''),
            'tags': f"%{data.get('tags', '')}%"
        }

        result = db.execute(query, params)
        complaints = result.fetchall()

    return complaints

import sqlite3
from collections import Counter
from collections import Counter

def get_complaints_stats():
    with sqlite3.connect(path_to_db) as db:
        total_complaints_query = "SELECT COUNT(*) FROM storage_complaints WHERE status IN (0, 1)"
        total_complaints_result = db.execute(total_complaints_query).fetchone()
        total_complaints = total_complaints_result[0] if total_complaints_result else 0

        server_stats_query = """
        SELECT server_number, COUNT(*) AS total, 
               SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS checked, 
               SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS unchecked,
               GROUP_CONCAT(tags) AS all_tags
        FROM storage_complaints
        WHERE status IN (0, 1)
        GROUP BY server_number
        """
        server_stats_result = db.execute(server_stats_query).fetchall()

        tags_counter = Counter()
        stats = {
            'total_complaints': total_complaints,
            'server_stats': {}
        }

        for server_stat in server_stats_result:
            server_number, total, checked, unchecked, all_tags = server_stat
            tags_counter.update(all_tags.split(','))

            top_tags = tags_counter.most_common(3)
            server_stats = {
                'total': total,
                'checked': checked,
                'unchecked': unchecked,
                'top_tags': top_tags
            }
            stats['server_stats'][server_number] = server_stats

    return stats


def delete_complaint(unique_id):
    with sqlite3.connect(path_to_db) as db:
        db.execute("DELETE FROM storage_complaints WHERE user_id=?", [unique_id])
        db.commit()

def get_user_id_by_unique_id(unique_id):
    with sqlite3.connect(path_to_db) as db:
        result = db.execute("SELECT user_id FROM storage_complaints WHERE unique_id=?", [unique_id])
        user_id = result.fetchone()
        print(result)
        if user_id:
            return user_id[0]
        else:
            return None

def get_earliest_complaint():
    with sqlite3.connect(path_to_db) as db:
        result = db.execute("SELECT * FROM storage_complaints WHERE status IN (0) ORDER BY submission_time ASC LIMIT 1")
        earliest_complaint = result.fetchone()
    
    return earliest_complaint


def update_complaint_status(unique_id, new_status):
    with sqlite3.connect(path_to_db) as db:
        db.execute("UPDATE storage_complaints SET status=? WHERE unique_id=?", [new_status, unique_id])
        db.commit()


def update_status(user_id, status_will, status_was):
    with sqlite3.connect(path_to_db) as db:
        db.execute(f"UPDATE 'storage_users' SET status=? WHERE user_id=? AND status=?", [status_will, user_id, status_was])
        db.commit()

def delete_status(user_id):
    with sqlite3.connect(path_to_db) as db:
        db.execute(f"DELETE FROM 'storage_users' WHERE user_id=? AND status=? OR status=?", [user_id, 0, 1])
        db.commit()


def check_status(user_id):
    with sqlite3.connect(path_to_db) as db:
        textik = ((db.execute(f"SELECT message_text FROM 'storage_users' WHERE user_id=? AND status=?", [user_id, 1])).fetchall())[0][0]
        print(textik)
        return textik

def create_bdx(path_to_db="data/botBD.sqlite"):
    with sqlite3.connect(path_to_db) as db:
        # Check if the table exists and has the expected columns
        check_sql = db.execute("PRAGMA table_info(storage_complaints)")
        check_result = check_sql.fetchall()

        expected_columns = [
            ('id', 'INTEGER', 0, None, 1),
            ('user_id', 'INTEGER', 0, None, 0),
            ('server_type', 'TEXT', 0, None, 0),
            ('server_number', 'TEXT', 0, None, 0),
            ('violator_nickname', 'TEXT', 0, None, 0),
            ('submission_time', 'TEXT', 0, None, 0),
            ('unique_id', 'TEXT', 0, None, 0),
            ('complaint_info', 'TEXT', 0, None, 0),
            ('status', 'INTEGER', 0, None, 0),
            ('tags', 'TEXT', 0, None, 0)
        ]

        if len(check_result) == len(expected_columns) and all(col in check_result for col in expected_columns):
            print("DB table 'storage_complaints' was found and has the correct columns.")
        else:
            # Create the table if it doesn't exist or has incorrect columns
            db.execute("CREATE TABLE IF NOT EXISTS storage_complaints("
                       "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "user_id INTEGER, server_type TEXT, server_number TEXT, violator_nickname TEXT,"
                       "submission_time TEXT, unique_id TEXT, complaint_info TEXT, status INTEGER, tags TEXT)")
            print("DB table 'storage_complaints' was not found or had incorrect columns. Creating...")

        db.commit()