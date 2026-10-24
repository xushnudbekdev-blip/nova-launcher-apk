# 📱 Nova Launcher — Android APK

Java Minecraft uchun mobil launcher (Kivy bilan qurilgan)

## 🎮 Ilovaning xususiyatlari

- **Minecraft versiyalar**: 1.7.10 dan 1.20.4 gacha (Release, Fabric, Forge, Snapshot)
- **RAM sozlash**: 1-8 GB
- **Modlar**: OptiFine, Fabric, Sodium, JEI, Iris va boshqalar
- **Profil**: Username, o'rnatilgan versiyalar
- **Sozlamalar**: Tema, til, papka va boshqalar
- **Offline rejim**: Hisob kerak emas

## 📦 APK QURISH — Google Colab orqali (BEPUL!)

### 1-qadam: Google Colab ga boring
👉 [colab.research.google.com](https://colab.research.google.com)

### 2-qadam: Notebook ni oching
- **File** → **Upload notebook** → `NovaLauncher_APK_Builder.ipynb` faylni tanlang

### 3-qadam: Fayllarni yuklang
Quyidagi fayllarni Colab ga yuklang:
```
main.py
assets/logo.png
assets/background.png
buildozer.spec
```

### 4-qadam: Barcha celllarni ishga tushiring
- ▶ tugmasini bosib har bir cellni yuring
- **30-60 daqiqa** kuting

### 5-qadam: APK ni yuklab oling
- Oxirgi cell APK ni avtomatik yuklab beradi

---

## 📲 Telefoningizga o'rnatish

1. **Sozlamalar** → **Xavfsizlik** → **Noma'lum manbalar** → yoqing
2. APK faylni oching
3. **O'rnatish** tugmasini bosing

---

## 🏗️ Loyiha tuzilmasi

```
nova_mobile/
├── main.py              ← Asosiy kod (Kivy)
├── buildozer.spec       ← Android build konfiguratsiyasi
├── assets/
│   ├── logo.png         ← Ilovaning ikonkasi
│   └── background.png   ← Fon rasmi
└── NovaLauncher_APK_Builder.ipynb  ← Colab notebook
```

## ⚙️ Talablar

| Parametr | Qiymat |
|----------|--------|
| Python | 3.8+ |
| Kivy | 2.2+ |
| Android API | 21+ (Android 5.0+) |
| Arxitektura | arm64-v8a, armeabi-v7a |
