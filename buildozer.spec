[app]
# (string) Judul aplikasi Anda
title = Sistem Entri Data Excel

# (string) Nama paket aplikasi
package.name = exceldatainput

# (string) Domain paket aplikasi
package.domain = org.example

# (string) Direktori sumber yang berisi main.py
source.dir = .

# (list) Ekstensi file sumber yang akan disertakan (jangan kosongkan untuk menyertakan semua file)
source.include_exts = py,png,jpg,kv,atlas,xlsx,ttc

# (string) Versi aplikasi Anda
version = 0.1

# (list) Daftar dependensi Python yang akan diinstal dari PyPI
requirements = python3,kivy,pandas,openpyxl,plyer

# (string) Orientasi layar yang diinginkan
orientation = portrait

# (string) Arsitektur target
android.arch = arm64-v8a

# (list) Izin yang dibutuhkan aplikasi Anda
android.permissions = ReadExternalStorage,WriteExternalStorage

[buildozer]
# (int) Tingkat verbositas output buildozer
log_level = 2

# (int) Tampilkan peringatan jika versi buildozer sudah usang
warn_on_root = 1
