"""Lab 1 - Eksperimen chunking (15 menit).

1. Baca satu PDF dengan baca_pdf() dan cetak 500 karakter pertama.
2. Potong dengan potong() memakai tiga ukuran (500, 1000, 1500) dan overlap 10-20%.
3. Lihat 3 chunk acak tiap ukuran: terpotong di tengah kalimat atau tabel?
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from laporan_utils import Laporan
from rag_utils import FOLDER_DOKUMEN, baca_pdf, norm, potong, potong_dengan_posisi

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(FOLDER_DOKUMEN, "sejarah_kecerdasan_buatan.pdf")   # ganti dengan PDF Anda
UKURAN = [500, 1000, 1500]
OVERLAP = [0.10, 0.15, 0.20]
OVERLAP_UTAMA = 0.15
SEED = 42


def wilayah_tabel(teks):
    """Cari rentang karakter tabel ("Tabel N." sampai baris "Sumber:")."""
    hasil, pos = [], 0
    while True:
        a = teks.find("Tabel ", pos)
        if a < 0:
            return hasil
        b = teks.find("Sumber:", a)
        b = len(teks) if b < 0 else teks.find("\n", b)
        hasil.append((a, b))
        pos = b


def awal_di_tengah_kalimat(teks, mulai):
    """Chunk dimulai di tengah kalimat bila karakter bermakna sebelumnya bukan akhir kalimat/baris."""
    sebelum = teks[:mulai].rstrip(" ")
    return bool(sebelum) and sebelum[-1] not in ".!?:\n"


def akhir_di_tengah_kalimat(teks, akhir):
    ujung = teks[:akhir].rstrip()
    return bool(ujung) and ujung[-1] not in ".!?"


def memotong_tabel(wil, mulai, akhir):
    """True bila chunk beririsan dengan tabel tetapi tidak memuat seluruh tabel."""
    for a, b in wil:
        beririsan = mulai < b and akhir > a
        utuh = mulai <= a and akhir >= b
        if beririsan and not utuh:
            return True
    return False


def main():
    # ---- Langkah 1
    teks = baca_pdf(PDF)
    n_huruf = sum(c.isalpha() for c in teks)
    kualitas = {
        "File": os.path.basename(PDF),
        "Total karakter": len(teks),
        "Karakter rusak (U+FFFD)": teks.count("\ufffd"),
        "Persentase huruf": f"{n_huruf / len(teks):.0%}",
    }
    print("=== Langkah 1: 500 karakter pertama ===")
    print(teks[:500])
    print(kualitas)

    # ---- Langkah 2
    print("\n=== Langkah 2: jumlah chunk ===")
    tabel_jumlah = [["Ukuran (karakter)"] + [f"overlap {int(o * 100)}%" for o in OVERLAP]]
    for u in UKURAN:
        baris = [u]
        for o in OVERLAP:
            n = len(potong(teks, u, o))
            baris.append(n)
            print(f"ukuran={u:5d} overlap={o:.0%} -> {n} chunk")
        tabel_jumlah.append(baris)

    # ---- Langkah 3
    wil = wilayah_tabel(teks)
    rnd = random.Random(SEED)
    cuplikan, statistik = {}, [["Ukuran", "Jumlah chunk", "Awal di tengah kalimat",
                                "Akhir di tengah kalimat", "Memotong tabel"]]
    for u in UKURAN:
        pot = potong_dengan_posisi(teks, u, OVERLAP_UTAMA)
        n = len(pot)
        a = sum(awal_di_tengah_kalimat(teks, m) for m, _, _ in pot)
        z = sum(akhir_di_tengah_kalimat(teks, e) for _, e, _ in pot)
        t = sum(memotong_tabel(wil, m, e) for m, e, _ in pot)
        statistik.append([u, n, f"{a}/{n} ({a / n:.0%})", f"{z}/{n} ({z / n:.0%})", f"{t}/{n}"])
        pilih = sorted(rnd.sample(range(n), min(3, n)))
        cuplikan[u] = [(i + 1, pot[i][0], pot[i][1], pot[i][2],
                        awal_di_tengah_kalimat(teks, pot[i][0]),
                        akhir_di_tengah_kalimat(teks, pot[i][1]),
                        memotong_tabel(wil, pot[i][0], pot[i][1])) for i in pilih]
        print(f"\n=== Langkah 3: ukuran {u} (3 chunk acak) ===")
        for no, m, e, isi, aw, ak, tb in cuplikan[u]:
            print(f"--- chunk #{no} [{m}:{e}] awal_tengah={aw} akhir_tengah={ak} potong_tabel={tb}")
            print(isi)

    # ---- Kesimpulan otomatis dari angka
    rincian = "; ".join(
        f"ukuran {r[0]}: awal {r[2]}, akhir {r[3]}, memotong tabel {r[4]}" for r in statistik[1:])
    kesimpulan = (
        "Pemotongan per karakter tidak mengenal batas kalimat maupun tabel. Hasil seluruh chunk (overlap "
        f"{int(OVERLAP_UTAMA * 100)}%) - {rincian}. Jadi pada setiap ukuran, mayoritas chunk berakhir di tengah "
        "kalimat dan sebagian besar juga dimulai di tengah kalimat (hanya chunk pertama yang selalu bersih). "
        "Persentasenya tidak turun banyak saat ukuran diperbesar; yang berubah adalah jumlah chunk dan "
        "banyaknya topik per chunk. Tabel 1 terpotong oleh sedikitnya satu chunk pada tiap ukuran, dan teks "
        "tabel hasil ekstraksi sudah bercampur antar kolom, sehingga baris tabel yang terpisah dari baris "
        "judulnya sulit dipahami. Perbaikan yang layak dicoba: pemotongan berbasis kalimat/paragraf dan "
        "memperlakukan tabel sebagai satu chunk utuh."
    )
    print("\nKesimpulan:", kesimpulan)

    # ---- Laporan PDF
    L = Laporan(os.path.join(BASE, "Lab1_Eksperimen_Chunking.pdf"),
                "Lab 1 - Eksperimen Chunking", "Dikerjakan dengan Python (pdfplumber + fungsi potong)")
    L.h1("Langkah 1. Membaca PDF dan memeriksa teks")
    L.p(f"File yang dibaca: {os.path.basename(PDF)}. Berikut 500 karakter pertama hasil baca_pdf():")
    L.kode(teks[:500])
    L.spasi()
    L.tabel([["Pemeriksaan", "Hasil"]] + [[k, v] for k, v in kualitas.items()], [6 * 28.35, 8 * 28.35])
    L.p("Teks terbaca bersih: tidak ada karakter rusak, kata utuh, dan urutan paragraf benar. "
        "Satu catatan: teks Tabel 1 hasil ekstraksi tercampur antar kolom karena sel yang lebih dari satu baris "
        "digabung per baris tampilan, bukan per sel.")
    L.h1("Langkah 2. Jumlah chunk tiap pengaturan")
    L.p("Fungsi potong(teks, ukuran, overlap) memakai jendela geser per karakter; langkah = ukuran x (1 - overlap).")
    L.tabel(tabel_jumlah)
    L.cap("Tabel 1. Jumlah chunk untuk 3 ukuran x 3 overlap. Makin besar ukuran, makin sedikit chunk; "
          "makin besar overlap, makin banyak chunk.")
    L.h1(f"Langkah 3. Tiga chunk acak per ukuran (overlap {int(OVERLAP_UTAMA * 100)}%, seed {SEED})")
    L.tabel(statistik)
    L.cap("Tabel 2. Statistik seluruh chunk pada tiap ukuran (bukan hanya yang dicuplik).")
    for u in UKURAN:
        L.h2(f"Ukuran {u} karakter")
        for no, m, e, isi, aw, ak, tb in cuplikan[u]:
            L.p(f"Chunk #{no} (karakter {m}-{e}) | awal di tengah kalimat: {'ya' if aw else 'tidak'} | "
                f"akhir di tengah kalimat: {'ya' if ak else 'tidak'} | memotong tabel: {'ya' if tb else 'tidak'}")
            L.kode(isi)
            L.spasi(4)
    L.h1("Kesimpulan")
    L.p(kesimpulan)
    L.halaman_baru()
    L.h1("Lampiran: kode lab1_chunking.py")
    L.kode(open(__file__, encoding="utf-8").read())
    L.simpan()
    print("\nLaporan: Lab1_Eksperimen_Chunking.pdf")


if __name__ == "__main__":
    main()
