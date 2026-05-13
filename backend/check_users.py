import pymysql
import os

# Cargar manualmente el archivo .env
env_file = '.env'
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

print("Conectando a TiDB...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"Puerto: {os.getenv('DB_PORT')}")

try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cur = conn.cursor()
    
    # Ver estructura de la tabla
    cur.execute("SHOW COLUMNS FROM users")
    print("\n--- Estructura de la tabla users ---")
    for col in cur.fetchall():
        print(col)
    
    # Ver usuarios existentes
    cur.execute("SELECT id, username, role FROM users")
    print("\n--- Usuarios actuales ---")
    for user in cur.fetchall():
        print(user)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")