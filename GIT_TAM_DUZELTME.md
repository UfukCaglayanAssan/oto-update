# Git Repository Tam Düzeltme

## Sorun
Birden fazla bozuk nesne dosyası var:
- `.git/objects/34/97d022c122ce2a861a9cfc177c89d0269e6663`
- `.git/objects/60/22e5072cc2efcfb55dabda63a829b7d5ad71ef`
- `.git/objects/f0/7e029a88e6d8ca891a9ed370830432ef506f99`

## Çözüm: Agresif Temizlik

### Seçenek 1: Otomatik Script (Önerilen)
```bash
chmod +x fix_git_complete.sh
./fix_git_complete.sh
```

### Seçenek 2: Manuel Adımlar
```bash
# 1. Tüm bozuk nesne dosyalarını sil
find .git/objects -type f -empty -delete

# 2. Index'i temizle
rm -f .git/index

# 3. Referansları temizle
rm -f .git/refs/heads/main
rm -f .git/refs/remotes/origin/main
rm -f .git/refs/remotes/origin/HEAD

# 4. Remote'dan yeniden fetch et
git fetch origin --force

# 5. Remote branch'i local'e çek
git reset --hard origin/main
```

### Seçenek 3: Repository'yi Yeniden Clone Et (En Güvenli)
Eğer yukarıdaki yöntemler işe yaramazsa:

```bash
# Mevcut değişiklikleri kaydet
cd ..
cp -r oto-update oto-update-backup

# Repository URL'ini al
cd oto-update
git remote get-url origin

# Repository'yi yeniden clone et
cd ..
rm -rf oto-update
git clone <repository-url> oto-update

# Gerekli dosyaları geri kopyala
cp oto-update-backup/*.py oto-update/ 2>/dev/null || true
cp oto-update-backup/*.bin oto-update/ 2>/dev/null || true
cp oto-update-backup/*.md oto-update/ 2>/dev/null || true
```

## Hızlı Komutlar
```bash
# Tüm bozuk dosyaları temizle ve yeniden fetch
find .git/objects -type f -empty -delete && \
rm -f .git/index && \
rm -f .git/refs/heads/main .git/refs/remotes/origin/main .git/refs/remotes/origin/HEAD && \
git fetch origin --force && \
git reset --hard origin/main
```

