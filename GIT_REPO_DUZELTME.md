# Git Repository Düzeltme

## Sorun
Git repository'sinde bozuk bir nesne dosyası var:
```
.git/objects/34/97d022c122ce2a861a9cfc177c89d0269e6663
```

## Çözüm Seçenekleri

### Seçenek 1: Bozuk Dosyayı Sil ve Yeniden Fetch (Önerilen)
```bash
# Bozuk nesne dosyasını sil
rm -f .git/objects/34/97d022c122ce2a861a9cfc177c89d0269e6663

# Git repository'yi kontrol et
git fsck --full

# Remote'dan yeniden fetch et
git fetch origin

# Pull yap
git pull
```

### Seçenek 2: Otomatik Script Kullan
```bash
chmod +x fix_git_repo.sh
./fix_git_repo.sh
```

### Seçenek 3: Repository'yi Yeniden Clone Et (Son Çare)
Eğer yukarıdaki yöntemler işe yaramazsa:
```bash
# Mevcut değişiklikleri kaydet
cd ..
cp -r oto-update oto-update-backup

# Repository'yi yeniden clone et
rm -rf oto-update
git clone <repository-url> oto-update

# Gerekli dosyaları geri kopyala
cp oto-update-backup/*.py oto-update/
cp oto-update-backup/*.bin oto-update/
```

## Hızlı Çözüm
```bash
rm -f .git/objects/34/97d022c122ce2a861a9cfc177c89d0269e6663
git fetch origin
git pull
```

