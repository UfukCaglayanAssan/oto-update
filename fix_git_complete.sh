#!/bin/bash
# Git repository tam düzeltme scripti

echo "=== Git Repository Tam Düzeltme ==="
echo ""

# Tüm bozuk nesne dosyalarını bul ve sil
echo "1. Bozuk nesne dosyaları temizleniyor..."
find .git/objects -type f -empty -delete
echo "   ✓ Bozuk dosyalar silindi"

# Index'i temizle
echo ""
echo "2. Git index temizleniyor..."
rm -f .git/index
echo "   ✓ Index silindi"

# Ref'leri düzelt (HEAD'i remote'tan al)
echo ""
echo "3. HEAD referansı düzeltiliyor..."
rm -f .git/refs/heads/main
rm -f .git/refs/remotes/origin/main
rm -f .git/refs/remotes/origin/HEAD
echo "   ✓ Referanslar temizlendi"

# Remote'dan yeniden fetch et
echo ""
echo "4. Remote repository'den yeniden fetch ediliyor..."
git fetch origin --force
echo "   ✓ Fetch tamamlandı"

# Remote branch'i local'e çek
echo ""
echo "5. Remote branch local'e çekiliyor..."
git reset --hard origin/main
echo "   ✓ Reset tamamlandı"

echo ""
echo "=== Tamamlandı ==="
echo ""
echo "Repository düzeltildi. Şimdi çalışıyor olmalı."

