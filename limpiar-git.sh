#!/bin/bash

echo "🚀 Iniciando limpieza del repositorio Carrier Transicold..."

# ==================== CONFIGURACIÓN ====================
REPO_ROOT=$(pwd)

echo "📂 Repositorio: $REPO_ROOT"

# Archivos sensibles a eliminar
SENSITIVE_FILES=(
    "backend/.env"
    "backend/.env.txt"
    "backend/.env.local"
    ".env"
    ".env.txt"
    "isrgrootx1.pem"
)

# Archivos basura
TRASH_FILES=(
    "backend/.gitignore.txt"
    "Thumbs.db"
    ".DS_Store"
)

echo "🧹 Eliminando archivos sensibles del historial..."

# Usar git filter-repo (recomendado y más moderno)
if ! command -v git-filter-repo &> /dev/null; then
    echo "❌ git-filter-repo no está instalado."
    echo "Instálalo con: pip install git-filter-repo"
    echo "Luego vuelve a ejecutar este script."
    exit 1
fi

# Eliminar archivos del historial
for file in "${SENSITIVE_FILES[@]}" "${TRASH_FILES[@]}"; do
    if [ -f "$file" ] || git ls-files --error-unmatch "$file" &> /dev/null; then
        echo "🗑️  Eliminando: $file"
        git filter-repo --path "$file" --invert-paths --force
    fi
done

echo "✅ Archivos sensibles removidos del historial."

# ==================== CONFIGURAR .GITIGNORE ====================
cat > backend/.gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.*.local
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
EOF

echo "✅ .gitignore actualizado."

# Remover archivos que aún estén en el working directory
for file in "${SENSITIVE_FILES[@]}"; do
    rm -f "$file"
done

echo "🔄 Actualizando índice..."
git add backend/.gitignore
git rm --cached -r --ignore-unmatch "${SENSITIVE_FILES[@]}" "${TRASH_FILES[@]}" 2>/dev/null

git commit -m "chore: limpieza de archivos sensibles y configuración de .gitignore" --no-verify

echo ""
echo "🎉 Limpieza completada exitosamente!"
echo ""
echo "⚠️  ACCIONES IMPORTANTES DESPUÉS DE EJECUTAR ESTE SCRIPT:"
echo "1. Fuerza push (cuidado, reescribe historial):"
echo "   git push origin main --force"
echo "2. Cambia inmediatamente todas las contraseñas (especialmente TiDB Cloud)"
echo ""
echo "¿Quieres que genere también un README.md profesional ahora?"
