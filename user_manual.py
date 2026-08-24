#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Taktik SDR Terminali - Eğitim & Sistem Kullanım Rehberi (Built-in User Manual)
Zengin HTML/CSS formatında biçimlendirilmiş taktik temalı interaktif kullanıcı kılavuzu.
"""


def get_user_manual_html() -> str:
    """Taktik Koyu Tema uyumlu, zengin HTML formatında hazırlanmış Türkçe sistem kullanım kılavuzunu döndürür."""
    return r"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {
        background-color: #080b10;
        color: #c9d1d9;
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
        line-height: 1.6;
        padding: 20px;
    }
    h1 {
        color: #00ff66;
        border-bottom: 2px solid #00ff66;
        padding-bottom: 8px;
        font-size: 22px;
        letter-spacing: 1px;
    }
    h2 {
        color: #00e676;
        border-bottom: 1px solid #30363d;
        padding-bottom: 6px;
        margin-top: 24px;
        font-size: 17px;
        letter-spacing: 0.5px;
    }
    h3 {
        color: #58a6ff;
        margin-top: 16px;
        font-size: 14px;
    }
    p, li {
        color: #c9d1d9;
        font-size: 13px;
    }
    ul, ol {
        margin-left: 20px;
    }
    li {
        margin-bottom: 6px;
    }
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 14px 18px;
        margin: 14px 0;
    }
    .highlight {
        color: #00ff66;
        font-weight: bold;
    }
    .accent-blue {
        color: #58a6ff;
        font-weight: bold;
    }
    .accent-yellow {
        color: #ffd33d;
        font-weight: bold;
    }
    .accent-red {
        color: #ff7b72;
        font-weight: bold;
    }
    .badge {
        display: inline-block;
        background-color: #21262d;
        border: 1px solid #30363d;
        color: #00ff66;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        font-family: Consolas, monospace;
    }
    .code-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 10px;
        font-family: Consolas, 'Courier New', monospace;
        font-size: 12px;
        color: #38d39f;
        margin: 8px 0;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
    }
    th {
        background-color: #21262d;
        color: #00ff66;
        border: 1px solid #30363d;
        padding: 8px;
        font-size: 12px;
        text-align: left;
    }
    td {
        border: 1px solid #30363d;
        padding: 8px;
        font-size: 12px;
        color: #c9d1d9;
    }
    tr:nth-child(even) {
        background-color: #0d1117;
    }
    .alert-tip {
        border-left: 4px solid #00ff66;
        background-color: #0d1b14;
        padding: 10px 14px;
        margin: 10px 0;
        border-radius: 0 4px 4px 0;
    }
</style>
</head>
<body>

<h1>📖 ANTIGRAVITY TAKTİK SDR TERMİNALİ // SİSTEM KULLANIM REHBERİ</h1>

<div class="card">
    <p><strong>Hoş Geldiniz!</strong> Bu rehber, <strong>Antigravity Taktik SDR Terminali</strong>'nin mimarisini, sinyal işleme prensiplerini, spektrum analizini, yazılımsal demodülatörünü, kayıt/oynatma işlevlerini ve RF kapsama hesaplayıcısını detaylı olarak açıklamak amacıyla hazırlanmıştır.</p>
</div>

<!-- BÖLÜM 1 -->
<h2>1. SİSTEMİN ÇALIŞMA MANTIĞI VE MİMARİSİ</h2>
<p>Antigravity Terminali; modern radar, elektronik harp (EH) ve haberleşme sinyallerini analiz etmek üzere tasarlanmış <strong>Yazılım Tanımlı Radyo (Software Defined Radio - SDR)</strong> çalışma istasyonudur.</p>

<div class="card">
    <h3>Temel Yapı Taşları ve Akış Modeli:</h3>
    <ul>
        <li><span class="highlight">Mock DSP Sinyal Motoru (mock_dsp_node.py):</span> Fiziksel bir SDR donanımını (RTL-SDR, HackRF, USRP vb.) taklit eden bağımsız sentetik sinyal üretecidir. Gauss taban gürültüsü, frekans taramalı taşıyıcı (chirp), sabit CW referans sinyalleri ve taktik darbeli yayınlar üretir.</li>
        <li><span class="highlight">ZeroMQ (pyzmq) Ara Katmanı:</span> DSP motoru ile grafik kullanıcı arayüzü (GUI) arasında <span class="badge">tcp://127.0.0.1:5555</span> adresi üzerinden çalışan yüksek hızlı, asenkron ve bloklamasız PUB/SUB (Yayınla/Abone Ol) köprüsüdür.</li>
        <li><span class="highlight">Çoklu İş Parçacıklı DSP Motoru (QThread):</span> Gelen ikili (binary) karmaşık I/Q verileri, ana grafik arayüzünü (GUI) dondurmamak için arka planda çalışan <span class="badge">DSPWorkerThread</span> içinde Hanning pencerelemeden, 1024-noktalı FFT'den ve demodülasyondan geçirilir.</li>
    </ul>
</div>

<!-- BÖLÜM 2 -->
<h2>2. HIZLI BAŞLANGIÇ ADIMLARI</h2>
<p>Sistemi ilk kez çalıştırırken aşağıdaki adımları sırasıyla takip edebilirsiniz:</p>

<ol>
    <li><strong>Sinyal Motorunu Başlatın:</strong> Ayrı bir PowerShell veya CMD terminalinde sentetik sinyal motorunu çalıştırın:
        <div class="code-box">python mock_dsp_node.py</div>
    </li>
    <li><strong>Terminal Alımını Başlatın:</strong> Sol kontrol panelindeki yeşil <span class="highlight">"Sistemi Başlat"</span> butonuna tıklayın. Buton <em>"Sistemi Durdur"</em> haline gelecek ve durum <em>"● DURUM: ÇALIŞIYOR"</em> olarak güncellenecektir.</li>
    <li><strong>Canlı Akışı İzleyin:</strong> <span class="accent-blue">"📡 Spektrum & Şelale"</span> sekmesine geçerek gerçek zamanlı FFT spektrumunu ve 2D spektrogram şelale akışını gözlemleyin.</li>
    <li><strong>Bağlantıyı Doğrulayın:</strong> Sol paneldeki <span class="accent-blue">"Bağlantı Testi"</span> butonuna basarak ZMQ köprüsünün milisaniye gecikmeli PING/PONG yanıtını Sistem Logları konsolunda doğrulayın.</li>
</ol>

<!-- BÖLÜM 3 -->
<h2>3. SPEKTRUM VE ŞELALE (WATERFALL) EKRANI NASIL OKUNUR?</h2>
<p>Terminalin ana görselleştirme alanı iki birbirine bağlı (X-Link) taktik göstergeden oluşur:</p>

<table>
    <tr>
        <th>Gösterge</th>
        <th>Eksenler</th>
        <th>Açıklama & Yorumlama</th>
    </tr>
    <tr>
        <td><strong>Spektrum Analizörü (Üst Panel)</strong></td>
        <td>X: Frekans (Bant - MHz)<br>Y: Genlik (dB)</td>
        <td>Sinyalin anlık frekans bileşenlerini gösterir. Belirgin dikey sivri tepeler (peaks) aktif taşıyıcıları veya modüleli yayınları temsil eder. <span class="accent-blue">Mavi kesikli çizgi (Max-Hold)</span> tepe hafızasını tutarak maksimum enerji seviyelerini saklar.</td>
    </tr>
    <tr>
        <td><strong>Şelale Göstergesi (Alt Panel)</strong></td>
        <td>X: Frekans (Bant - MHz)<br>Y: Zaman Geçmişi</td>
        <td>Sinyallerin zaman içerisindeki frekans değişim geçmişini (spektrogram) aşağı doğru kaydırarak görselleştirir. Taktik renk haritası sayesinde sinyal yoğunluğu renklendirilir:
        <br>• <span style="color:#6e7681;">Koyu Zemin:</span> Taban Gürültüsü (-115 dB)
        <br>• <span class="highlight">Canlı Yeşil:</span> Orta Güçlü Sinyaller
        <br>• <span class="accent-blue">Camgöbeği & Beyaz:</span> Yüksek Güçlü Taşıyıcı Tepe Noktaları</td>
    </tr>
</table>

<div class="alert-tip">
    <strong>İpucu:</strong> Spektrum veya Şelale grafiği üzerinde fare tekerleğiyle yakınlaştırma (zoom) veya sürükleme (pan) yaptığınızda, her iki grafiğin frekans eksenleri <strong>senkronize</strong> hareket eder.
</div>

<!-- BÖLÜM 4 -->
<h2>4. I/Q SİNYAL KAYDI VE OYNATMA (RECORD & PLAYBACK)</h2>
<p>Terminal, tespit edilen RF sinyallerini ham karmaşık (complex64) formatında diske kaydetme ve kaydedilmiş sinyalleri donanım gibi tekrar oynatma yeteneğine sahiptir:</p>

<div class="card">
    <h3>🔴 Canlı Sinyal Kaydı Yapma:</h3>
    <ol>
        <li>Sistem aktifken sol paneldeki <span class="accent-red">"Kaydı Başlat"</span> butonuna tıklayın.</li>
        <li>Gelen tüm ham I/Q örnekleri <span class="badge">records/taktik_iq_TARIH.raw</span> dosyasına ikili biçimde yazılır.</li>
        <li>Aynı anda SigMF standardında <span class="badge">records/taktik_iq_TARIH.meta.json</span> metaveri dosyası (örnekleme hızı, merkez frekansı, toplam örnek sayısı vb.) oluşturulur.</li>
        <li><span class="accent-red">"Kaydı Durdur"</span> butonuna basarak kaydı güvenle tamamlayın.</li>
    </ol>

    <h3>🟢 Kayıtlı Sinyali Oynatma (Playback):</h3>
    <ol>
        <li>Sol paneldeki <span class="highlight">"Dosya Seç"</span> butonuna tıklayarak <span class="badge">records/</span> klasöründeki bir <code>.raw</code> veya <code>.dat</code> dosyasını seçin.</li>
        <li>Sürekli akış için <span class="accent-yellow">"Döngüsel Oynat (Loop)"</span> kutucuğunu işaretli bırakın.</li>
        <li><span class="highlight">"Oynatmayı Başlat"</span> butonuna bastığınızda dosya okunarak ZeroMQ üzerinden canlı sinyal şeklinde Spektrum ve Şelale ekranına yansıtılır.</li>
    </ol>
</div>

<!-- BÖLÜM 5 -->
<h2>5. YAZILIMSAL DEMODÜLASYON VE DİJİTAL TELEMETRİ ÇÖZÜCÜ</h2>
<p><span class="accent-blue">"📻 Demodülasyon & Çözücü"</span> sekmesi, RF spektrumundan ses ve dijital veri çıkartmayı sağlar:</p>

<div class="card">
    <h3>Modülasyon Tipleri ve Ayarlar:</h3>
    <ul>
        <li><strong>AM Alıcısı (Genlik Modülasyonu):</strong> Zarf algılayıcı (envelope detector) algoritması ile \(|I + jQ|\) büyüklüğünü hesaplar ve DC bileşeni süzerek genlik modülasyonlu sesleri çıkarır.</li>
        <li><strong>FM Alıcısı (Frekans Modülasyonu):</strong> Polar diskriminatör algoritması ile ardışık I/Q örnekleri arasındaki faz fark türevini \(\Delta\theta\) hesaplayarak frekans modülasyonlu sinyalleri çözer.</li>
        <li><strong>NBFM (Dar Bant FM):</strong> Dar bant filtreleme ve de-emphasis uygulayarak telsiz/haberleşme seslerini netleştirir.</li>
        <li><strong>Susturma (Squelch):</strong> Sinyal gücü belirlenen eşik değerinin (örn. -80 dB) altına düştüğünde parazit ve gürültüyü otomatik olarak keser.</li>
        <li><strong>Sesi Başlat / Kapat:</strong> <span class="highlight">"Sesi Başlat"</span> butonu ile demodüle edilen ses doğrudan sistem hoparlörlerine (PCM 16-bit) aktarılır.</li>
    </ul>

    <h3>Dijital Veri Çözücü (Digital Decoder):</h3>
    <p>FSK dijital telemetri çerçevelerini çözerek çağrı kodlarını (Callsign), GPS konum koordinatlarını, RSSI sinyal güçlerini ve durum raporlarını terminal alanına canlı basar.</p>
</div>

<!-- BÖLÜM 6 -->
<h2>6. RF KAPSAMA ALANI VE LİNK BÜTÇESİ (FRIIS TRANSMISSION)</h2>
<p><span class="accent-blue">"📊 RF Kapsama Alanı"</span> sekmesi, ideal serbest uzay ortamında RF dalga yayılımını modeller:</p>

<div class="card">
    <h3>Matematiksel Yayılım Modeli:</h3>
    <div class="code-box">FSPL (dB) = 20 * log10(Mesafe_km) + 20 * log10(Frekans_MHz) + 32.4478</div>
    <div class="code-box">Prx (dBm) = Ptx (dBm) + Gtx (dBi) + Grx (dBi) - FSPL (dB)</div>

    <p>Kullanıcı girişlerine göre (Frekans, İletim Gücü, Anten Kazançları ve Hedef Mesafe) hesaplanan metrikler:</p>
    <ul>
        <li><span class="highlight">FSPL:</span> Serbest Uzay Yol Kaybı (dB).</li>
        <li><span class="highlight">Prx:</span> Alıcıya ulaşan teorik sinyal gücü (dBm).</li>
        <li><span class="highlight">EIRP:</span> Eşdeğer İzotropik Işıma Gücü (dBm).</li>
        <li><span class="highlight">Bağlantı Kalitesi:</span> Alınan güce göre bağlantının kararlılık durumu (<span class="highlight">Mükemmel</span>, <span class="accent-blue">İyi</span>, <span class="accent-yellow">Zayıf</span> veya <span class="accent-red">Kopuk</span>).</li>
    </ul>
</div>

<!-- BÖLÜM 7 -->
<h2>7. SİSTEM LOGLARI KONSOLU VE RENK KODLARI</h2>
<p>Tüm terminal olayları alt paneldeki canlı konsol günlüğüne zaman damgalı formatta kaydedilir:</p>

<ul>
    <li><span style="color:#00ff66; font-weight:bold;">[SİSTEM]</span> Başlangıç, kapanış ve çekirdek servis durumları.</li>
    <li><span style="color:#58a6ff; font-weight:bold;">[BİLGİ]</span> ZMQ soket bağlantıları, yapılandırma değişiklikleri ve rapor oluşturma.</li>
    <li><span style="color:#39ff14; font-weight:bold;">[DURUM]</span> DSP iş parçacığı ve veri akışı başlatma/durdurma olayları.</li>
    <li><span style="color:#ff7b72; font-weight:bold;">[KAYIT]</span> Ham I/Q kayıt dosyası oluşturma ve tamamlama bildirimleri.</li>
    <li><span style="color:#38d39f; font-weight:bold;">[OYNATMA]</span> I/Q kayıt oynatıcısı durumu ve dosya yükleme bilgileri.</li>
    <li><span style="color:#38d39f; font-weight:bold;">[RF ANALİZ]</span> Friis Link bütçesi hesaplama sonuçları.</li>
    <li><span style="color:#ffd33d; font-weight:bold;">[UYARI]</span> ve <span style="color:#ff7b72; font-weight:bold;">[HATA]</span> Sistem uyarıları, paket kayıpları ve istisnalar.</li>
</ul>

<!-- BÖLÜM 8 -->
<h2>8. OTOMATİK WORD RAPOR ÜRETECİ (WORD REPORT GENERATOR)</h2>
<p>Terminal, projenin tüm teknik aşamalarını ve mimarisini içeren resmi bir mühendislik raporu oluşturabilir:</p>

<div class="card">
    <h3>📄 Rapor Oluşturma Adımları:</h3>
    <ol>
        <li>Sol kontrol panelindeki <span class="accent-blue">"Rapor Oluştur (Word)"</span> butonuna tıklayın.</li>
        <li>Sistem, Git geçmişini (git log) otomatik analiz eder ve tüm tamamlanmış aşamaları kronolojik olarak derler.</li>
        <li>Proje ana dizininde <span class="badge">Antigravity_Gelistirme_Raporu.docx</span> dosyası oluşturulur.</li>
        <li>İşlem tamamlandığında konsolda <span class="accent-blue">[BİLGİ] Geliştirme raporu (Word) başarıyla oluşturuldu.</span> bildirimi görüntülenir.</li>
    </ol>
</div>

<!-- BÖLÜM 9 -->
<h2>9. ELEKTRONİK HARP (EW) VE RF JAMMER SİSTEMİ</h2>
<p>Terminal, aktif radar ve telsiz haberleşme yayınlarını engellemek ve simüle etmek amacıyla taktik Elektronik Harp alt yapısı barındırır:</p>

<div class="card">
    <h3>⚡ Karıştırıcı (Barrage Jammer) Çalışma Modeli:</h3>
    <ul>
        <li><span class="accent-red">Baraj Karıştırma (Barrage Jamming):</span> Jammer aktif edildiğinde geniş bant yüksek genlikli Gauss gürültüsü I/Q spektrumuna basılır ve temiz sinyaller spektrum/şelale ekranında gürültüye gömülür.</li>
        <li><span class="highlight">Dinamik Güç Kontrolü:</span> Jammer gücü (%0 - %100) ZMQ kontrol kanalı (<code>tcp://127.0.0.1:5556</code>) üzerinden DSP motoruna anlık aktarılır.</li>
        <li><span class="accent-yellow">Telemetri Bozulması (BER):</span> Yüksek gürültü altında FSK dijital telemetri çözücüsü kilitlenir, Bit Hata Oranı (BER) kritik seviyelere fırlar ve arayüzde karıştırma alarmı verilir.</li>
    </ul>
</div>

<div class="card" style="text-align: center; color: #8b949e; font-size: 11px;">
    ANTIGRAVITY TAKTİK SDR TERMİNALİ // GELİŞMİŞ RADYO VE SPEKTRUM ANALİZ SİSTEMİ v1.5.0
</div>

</body>
</html>
"""
