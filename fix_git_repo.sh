#!/bin/bash
# Git repository düzeltme scripti

echo "=== Git Repository Düzeltme ==="
echo ""

# Bozuk nesne dosyasını sil
echo "1. Bozuk nesne dosyası siliniyor..."
rm -f .git/objects/34/97d022c122ce2a861a9cfc177c89d0269e6663
echo "   ✓ Silindi"

# Git repository'yi temizle
echo ""
echo "2. Git repository temizleniyor..."
git fsck --full
echo "   ✓ Fsck tamamlandı"

# Remote'u yeniden fetch et
echo ""
echo "3. Remote repository'den yeniden fetch ediliyor..."
git fetch origin
echo "   ✓ Fetch tamamlandı"

# Pull yap
echo ""
echo "4. Pull yapılıyor..."
git pull
echo "   ✓ Pull tamamlandı"

echo ""
echo "=== Tamamlandı ==="

