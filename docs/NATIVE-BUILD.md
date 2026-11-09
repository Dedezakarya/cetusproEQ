# cetusproEQ v0.1 — Build AU/VST3 asli untuk macOS dan Windows

**PENTING:** File ZIP ini berisi *source code* dan workflow. Tidak ada file binary `.vst3` atau `.component` yang sudah dibangun di dalam ZIP ini. Proses kompilasi harus selesai pada Windows/macOS, atau pada runner Windows/macOS di GitHub Actions.

## Jalur termudah: GitHub Actions

1. Buat repository GitHub baru, misalnya `cetusproEQ` (boleh private; kuota Actions tergantung paket GitHub).
2. Ekstrak file ZIP ini. Commit **isi folder** `cetusproEQ-v0.1`, bukan ZIP-nya, sehingga `CMakeLists.txt` berada di root dan `.github/workflows/build-plugins.yml` tetap ada.
3. Dari folder root project, jalankan (pastikan Git terinstal):

```bash
git init
git branch -M main
git add .
git commit -m "Add cetusproEQ cross-platform AU and VST3 builds"
git remote add origin https://github.com/USERNAME/cetusproEQ.git
git push -u origin main
```

Ganti `USERNAME` dengan akun GitHub Anda. Jika repository sudah diinisialisasi di GitHub, sesuaikan proses git agar tidak menimpa riwayat.

4. Pada halaman repository, buka **Actions** → **Build cetusproEQ VST3 + AU** → **Run workflow** (atau lihat build yang otomatis berjalan setelah push).
5. Setelah job berstatus hijau, buka run → **Artifacts**, unduh:
   - `cetusproEQ-v0.1-Windows-x64-VST3` → ZIP berisi folder `cetusproEQ.vst3` untuk Windows 64-bit.
   - `cetusproEQ-v0.1-macOS-Universal-AU-and-VST3` → dua ZIP: `cetusproEQ-v0.1-macOS-Universal-VST3.zip` dan `cetusproEQ-v0.1-macOS-Universal-AU.zip`.
6. Jika build **merah**, buka log step yang gagal. Project belum pernah dicompile di mesin Windows/macOS dalam sesi pembuatan ini; kegagalan build awal masih mungkin dan perlu ditindaklanjuti.

Workflow menggunakan runner `windows-2022` serta `macos-15-intel` untuk menghasilkan AU/VST3 universal (x86_64 dan arm64) dan mengunduh JUCE 8.0.10 saat configure. Diperlukan internet runner. Kompilasi pertama bisa agak lama karena JUCE belum di-cache. Workflow melakukan tes keberadaan artefak dan pemeriksaan arsitektur (`lipo`) pada Mac, bukan tes kualitas audio.

## Build langsung di komputer

### macOS (Xcode + CMake + Git)

```bash
bash scripts/build-macos.sh
```

Hasil di `build-mac/cetusproEQ_artefacts/Release` untuk AU dan VST3.

### Windows (Visual Studio 2022 Desktop development with C++ + CMake + Git)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-windows.ps1
```

Hasil di `build-win/cetusproEQ_artefacts/Release/VST3`.

## Instal plugin hasil build

- macOS AU: salin folder `cetusproEQ.component` ke `~/Library/Audio/Plug-Ins/Components/` (Logic Pro, dan DAW yang mendukung AU).
- macOS VST3: salin folder `cetusproEQ.vst3` ke `~/Library/Audio/Plug-Ins/VST3/`.
- Windows VST3: salin folder `cetusproEQ.vst3` ke `C:\Program Files\Common Files\VST3\` (admin diperlukan).
- Tutup DAW, lalu buka/rescan. AU dapat dicek dengan `auval -a` dan `auval -v aufx CpEq CtPr` bila empat-karakter ID sesuai build.

## Penting sebelum dibagikan

- macOS hasil Actions di-*ad-hoc sign* dan **belum dinotarize** Apple. Gatekeeper dapat memblokir plugin dari Internet. Untuk distribusi publik dibutuhkan Developer ID, hardening, notarization dan testing lebih lanjut.
- DAW dapat melakukan proses host/plugin terpisah, sehingga **Cetus Link antarinstance tidak selalu tersedia**. DAW sidechain bus merupakan fallback yang lebih aman.
- Kualitas DSP belum divalidasi secara produksi: koefisien EQ diperbarui per block; potensi artefak dan biaya alokasi tetap harus ditangani sebelum rilis.
- Format **AAX belum tersedia** (Pro Tools memerlukannya).
- Windows build target x64. macOS target Universal (Intel dan Apple Silicon), minimum macOS 11 untuk hasil CI ini.
- Perhatikan lisensi JUCE saat akan merilis/mengkomersialkan cetusproEQ.
