import sqlite3
import pandas as pd
import os
import glob

def stoklari_sifirla_ve_yukle():
    db_path = os.path.join(os.getcwd(), 'yemekhane.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        print("🗑️ Eski depo ve lot kayıtları siliniyor...")
        c.execute('DELETE FROM depo')
        c.execute('DELETE FROM stok_lotlari')

        # KLASÖRDEKİ İLK EXCEL DOSYASINI OTOMATİK BUL
        excel_dosyalari = glob.glob('*.xlsx')
        if not excel_dosyalari:
            print("❌ BİR HATA OLUŞTU: Klasörde .xlsx uzantılı Excel dosyası bulunamadı!")
            return
        
        dosya_adi = excel_dosyalari[0]
        print(f"📂 '{dosya_adi}' orijinal Excel dosyası okunuyor...")

        # Pandas ile Excel'i direkt oku
        df = pd.read_excel(dosya_adi)
            
        eklenen_sayi = 0
        birlestirilen_sayi = 0
        
        for index, row in df.iterrows():
            # Boş satırları atla
            if pd.isna(row.iloc[0]): continue 
            
            urun_adi = str(row.iloc[0]).strip().title()
            if not urun_adi or urun_adi.lower() in ['nan', 'none', 'isim']: continue
            
            try:
                miktar = float(row.iloc[1])
            except (ValueError, TypeError):
                miktar = 0.0
                
            birim = str(row.iloc[2]).strip().upper()

            # Zeki Kategori Tahmini
            kategori = 'Genel'
            u_upper = urun_adi.upper()
            if any(x in u_upper for x in ['ET', 'KÖFTE', 'TAVUK', 'DÖNER', 'MANTI']): kategori = '🥩 Kırmızı Et / Tavuk'
            elif any(x in u_upper for x in ['BİBER', 'TUZ', 'KİMYON', 'BAHARAT', 'FESLEĞEN', 'YENİBAHAR', 'SUMAK', 'KÖRİ', 'HAŞHAŞ', 'KARBONAT', 'VANİLYA']): kategori = 'Baharat'
            elif any(x in u_upper for x in ['KAĞIT', 'PEÇETE', 'ELDİVEN', 'ÇÖP', 'KOSTİK', 'KAP', 'KOLLUK', 'KASE', 'STREÇ']): kategori = 'Ambalaj / Temizlik'
            elif any(x in u_upper for x in ['ELMA', 'KABAK', 'DOMATES', 'ISPANAK', 'BROKOLİ', 'HAVUÇ', 'SOĞAN', 'PATATES', 'LAHANA', 'MAYDANOZ', 'SARIMSAK', 'KEREVİZ', 'SALATALIK', 'VİŞNE', 'BÖĞÜRTLEN', 'AYVA', 'DERE OTU', 'LİMON', 'NANE']): kategori = 'Sebze / Meyve'
            elif any(x in u_upper for x in ['UN', 'NİŞASTA', 'GALETA', 'PİZZA', 'BÖREĞİ', 'BÖREK', 'YUFKA', 'KADAYIF']): kategori = 'Unlu Mamüller'
            elif any(x in u_upper for x in ['MERCİMEK', 'NOHUT', 'FASULYE', 'BULGUR', 'PİRİNÇ', 'MAKARNA', 'ŞEHRİYE', 'BÖRÜLCE', 'BUĞDAY', 'İRMİK']): kategori = 'Bakliyat'
            elif any(x in u_upper for x in ['YAĞ', 'SALÇA', 'ZEYTİN', 'SİRKE', 'SOS']): kategori = 'Yağ / Sos'

            # --- SİHİRLİ KISIM: Mükerrer Ürün Kontrolü ---
            c.execute('SELECT id FROM depo WHERE urun_adi COLLATE NOCASE = ?', (urun_adi,))
            mevcut = c.fetchone()
            
            if mevcut:
                # Ürün zaten varsa, yeni miktarı eskisinin üzerine ekle
                c.execute('UPDATE depo SET miktar = miktar + ? WHERE id = ?', (miktar, mevcut[0]))
                birlestirilen_sayi += 1
            else:
                # Ürün ilk defa geliyorsa sıfırdan oluştur
                c.execute('INSERT INTO depo (kategori, urun_adi, miktar, birim) VALUES (?, ?, ?, ?)', (kategori, urun_adi, miktar, birim))
                eklenen_sayi += 1
            
            # Üretimde kullanılabilmesi için 'Sistem Devri' lotu oluştur
            c.execute('INSERT INTO stok_lotlari (urun_adi, marka, lot_damga_no, baslangic_miktar, kalan_miktar, birim) VALUES (?, ?, ?, ?, ?, ?)',
                      (urun_adi, 'Sistem Devri', 'DEVIR-01', miktar, miktar, birim))
            
        conn.commit()
        print(f"✅ HARİKA! {eklenen_sayi} yeni ürün eklendi ve {birlestirilen_sayi} mükerrer ürünün miktarı başarıyla birleştirildi.")
        
    except Exception as e:
        print(f"❌ BİR HATA OLUŞTU: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    stoklari_sifirla_ve_yukle()