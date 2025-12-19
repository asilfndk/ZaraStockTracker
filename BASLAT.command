#!/bin/bash
# Bu dosyaya çift tıklayarak kurulumu başlatabilirsiniz

cd "$(dirname "$0")"

echo "=========================================="
echo "   Zara Stock Tracker - Kolay Kurulum"
echo "=========================================="
echo ""

# 1. Python Kontrolü
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 bulunamadı!"
    echo "Lütfen Python 3'ü yükleyin: https://www.python.org/downloads/"
    echo "Veya terminale şunu yazın: brew install python3"
    echo ""
    read -p "Çıkmak için bir tuşa basın..."
    exit 1
fi

echo "✅ Python 3 bulundu."

# 2. Sanal Ortam Kurulumu
echo "📦 Kurulum yapılıyor (Bu işlem 1-2 dakika sürebilir)..."

# Eski venv varsa temizle (temiz kurulum için)
rm -rf .venv

# Yeni venv oluştur
python3 -m venv .venv
source .venv/bin/activate

# 3. Kütüphanelerin Yüklenmesi
echo "📥 Kütüphaneler indiriliyor..."
pip install --upgrade pip > /dev/null 2>&1
pip install streamlit sqlalchemy httpx pandas pync rumps watchdog > /dev/null 2>&1

echo "✅ Kurulum tamamlandı!"
echo ""
echo "=========================================="
echo "Program Başlatılıyor..."
echo "=========================================="
echo ""
echo "1. Menü Çubuğu Uygulaması başlatılıyor..."
python menu_bar_app.py &

echo "2. Dashboard Uygulaması başlatılıyor..."
streamlit run app.py
