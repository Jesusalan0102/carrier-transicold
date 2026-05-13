import pymysql
import os
from passlib.context import CryptContext

# Configurar hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cargar .env manualmente
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

# Configuración SSL
ssl_config = {
    "ca": "isrgrootx1.pem",
    "check_hostname": True
}

print("Conectando a TiDB Cloud...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"Puerto: {os.getenv('DB_PORT')}")

try:
    conn = pymysql.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        ssl=ssl_config
    )
    cur = conn.cursor()
    
    # 1. Modificar la columna role
    print("\n1. Modificando columna role...")
    try:
        cur.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin','tecnico','visor') NOT NULL DEFAULT 'tecnico'")
        conn.commit()
        print("   ✅ Columna 'role' actualizada para aceptar 'visor'")
    except Exception as e:
        print(f"   ⚠️  {e}")
    
    # 2. Crear usuario visor de prueba
    print("\n2. Creando usuario visor...")
    hashed_password = pwd_context.hash("visor123")
    cur.execute("""
        INSERT INTO users (username, password, role) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE password=%s, role=%s
    """, ('visor', hashed_password, 'visor', hashed_password, 'visor'))
    conn.commit()
    print("   ✅ Usuario 'visor' creado (contraseña: visor123)")
    
    # 3. Verificar todos los usuarios
    print("\n3. Usuarios en la base de datos:")
    cur.execute("SELECT id, username, role FROM users")
    for user in cur.fetchall():
        role_icon = "🛡️" if user[2] == 'admin' else "🔧" if user[2] == 'tecnico' else "👁️"
        print(f"   {role_icon} ID:{user[0]} | {user[1]} | Rol: {user[2]}")
    
    conn.close()
    print("\n✅ Configuración completada exitosamente!")
    print("\n📝 Prueba de inicio de sesión:")
    print("   Usuario: visor")
    print("   Contraseña: visor123")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPosibles soluciones:")
    print("1. Verifica que el archivo 'isrgrootx1.pem' existe en la carpeta actual")
    print("2. Verifica que las credenciales en .env son correctas")
    print("3. Verifica que tu IP está autorizada en TiDB Cloud")