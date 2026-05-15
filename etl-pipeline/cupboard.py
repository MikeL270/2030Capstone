from werkzeug.security import generate_password_hash

def salt_shaker(records):
    for record in records:
        record['password_hash'] = generate_password_hash(record['password'])

    return records