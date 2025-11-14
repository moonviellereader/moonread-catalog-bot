FROM python:3.11-slim

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY MoonCatalogBot.py .
COPY titles_and_links_alphabetical.csv .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run bot
CMD ["python", "MoonCatalogBot.py"]
```

4. **Scroll ke bawah**

5. **Commit message:** `Add Dockerfile`

6. **Klik "Commit new file"**

---

### **Step 3: Verifikasi**

Setelah commit, refresh halaman GitHub.

Kamu harus lihat file bernama: **`Dockerfile`** (dengan icon 🐳 Docker)

**BUKAN:**
- ❌ `Dockerfile.txt`
- ❌ `Dockerfile.dockerfile`
- ❌ `dockerfile`

---

### **Step 4: Redeploy di Koyeb**

1. Buka Koyeb dashboard
2. **Hapus deployment yang gagal** (kalau ada)
3. **Create new app** lagi:
   - Repository: `moonread-catalog-bot`
   - Branch: `main`
   - Builder: Auto-detect (akan pilih Docker)
   - Environment variable: `BOT_TOKEN` = token bot kamu
4. **Deploy**

Sekarang akan success! ✅

---

## 📸 **Visual Check:**

File list di GitHub harus seperti ini:
```
📁 moonread-catalog-bot
  📄 MoonCatalogBot.py
  🐳 Dockerfile              ← Icon Docker, no extension
  📄 requirements.txt
  📄 titles_and_links_alphabetical.csv
  📁 .choreo/
