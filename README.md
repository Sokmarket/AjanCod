# AEGIS PRO v0.3.0

**AI destekli kod ajanı · yerel teşhis · kontrollü dosya düzenleme · izinli ekran analizi**

AEGIS PRO; Python projelerini incelemek, görev planlarını doğrulamak/çalıştırmak, log hataları için olası çözümler sunmak ve OpenAI uyumlu bir modelden kod değişikliği önerileri almak için tasarlanmış yerel öncelikli bir mühendislik çekirdeğidir. Çekirdek çalışma zamanı Python standart kütüphanesiyle çalışır. Görsel ekran yakalama için isteğe bağlı iki paket gerekir.

> **Doğruluk taahhüdü:** Hiçbir test yazılımın kusursuz olduğunu kanıtlamaz. Model bağlantısı, ekran yakalama, Android/Termux uyumu ve işletim sistemi seviyesinde sandbox bu teslimatta gerçek ortamda doğrulanmış gibi gösterilmez. `doctor` bağlantı testi yapmaz; durumu açıkça `NOT_CHECKED` olarak raporlar.

## Neler eklendi?

- **Plan ve görev motoru:** Katı JSON şema doğrulaması, yinelenen görev/bağımlılık ve döngü denetimi, kararlı bağımlılık sıralaması.
- **Çalıştırma:** Shell kullanmadan izin verilen görev türlerini çalıştırma, zaman aşımı, POSIX süreç grubu sonlandırma, sınırlı rapor çıktısı ve atomik metin yazma.
- **Kod ajanı:** OpenAI uyumlu `/chat/completions` uç noktası, sınırlı proje bağlamı, sık karşılaşılan gizli değerlerin maskelemesi, JSON/şema/yol denetimi, öneri raporunda unified diff, `--apply` sırasında yedek oluşturma ve yazım hatasında geri alma denemesi.
- **Yerel inceleme:** Python dosyalarını AST ile sözdizimi açısından tarama, TODO/FIXME/XXX işaretlerini raporlama, yaygın traceback/log hataları için açıklama ve doğrulama adımı önerme.
- **İzinli ekran analizi:** Ekran izni varsayılan olarak kapalıdır. Önce `screen-permission grant`, sonra **her yakalama öncesinde** ayrı onay gerekir. Ana monitör görüntüsü bellekte işlenir, AEGIS tarafından diske kaydedilmez ve yapılandırılmış model uç noktasına gönderilir.
- **Görsel kimlik:** Düzenlenebilir SVG ve PNG logoları, uygulama ikonu ve 1080×1920 splash ekranı.
- **Kanıt odaklı teslimat:** Birim testleri ve GitHub Actions iş akışı.

## Kurulum

Python 3.11 veya üzeri gerekir.

```bash
python -m venv .venv
# Linux / macOS / Termux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Ekran yakalama bağımlılıkları gerekiyorsa:

```bash
python -m pip install -e ".[screen]"
```

Ekran yakalama desteği masaüstü monitörünü `mss` ile okumaya dayanır. Bu çekirdek, Android/Termux üzerinden Android'in diğer uygulamalarının ekranını okuyabildiğini **iddia etmez**; Android uygulama sürümünde bunun için Android'in yerel MediaProjection izin akışı ve bir native bridge gerekir. `Termux:X11` etkin bir Linux masaüstüsünü yakalayabilir, ancak telefonun tüm Android ekranını yakalamakla aynı şey değildir. Termux API'nin [resmî komut listesi](https://github.com/termux/termux-api-package/blob/master/CMakeLists.txt) ekran yakalama komutu sunmadığı için böyle bir yetenek varsayılmamıştır.

## İlk kontroller

Komutları proje kök dizininde çalıştır:

```bash
python -m aegis --help
python -m aegis doctor
python -m aegis init --workspace ./workspace
python -m aegis validate-plan examples/plan-example.json
python -m aegis run-checks --workspace ./workspace
python -m aegis inspect --workspace .
python -m unittest discover -s tests -v
```

`doctor`, ortam bilgilerini gösterir ama AI sunucusuna bağlanmaz, sandbox bulunduğunu veya GitHub gönderiminin yapıldığını iddia etmez.

## Model bağlantısı

AEGIS, OpenAI uyumlu Chat Completions API'si kullanır. Varsayılan ayar yerel Ollama uç noktasıdır; bunun çalışıyor olduğunu varsaymaz.

```bash
# Yerel Ollama örneği; modelin önceden indirilmiş ve servisinin çalışıyor olması gerekir.
export AEGIS_API_BASE="http://127.0.0.1:11434/v1"
export AEGIS_MODEL="qwen2.5-coder:7b"
# Hosted API kullanılıyorsa anahtar yalnızca ortam değişkeninde tutulur:
# export AEGIS_API_KEY="..."
```

Uzak uç noktalar için HTTPS zorunludur. Yerel loopback HTTP desteklenir. Anahtarı kaynak koda, plan dosyasına veya Git deposuna koyma. Kod bağlamı bir modele gönderildiği için gizli/özel proje verilerinin gönderilmesine ilişkin karar kullanıcıya aittir.

### Öneri üret (dosyaları değiştirmez)

Önce çalışma alanını oluştur ve içine analiz edilmesini istediğin projeyi koy:

```bash
python -m aegis agent --workspace ./workspace --task "Python yapılandırma doğrulamasını incele ve gerekli düzeltmeleri öner"
```

Çıktı `workspace/reports/agent-proposal.json` içinde diff'lerle birlikte saklanır. Varsayılan mod kaynak dosyalarını değiştirmez.

### Öneriyi uygula

```bash
python -m aegis agent --workspace ./workspace --task "Python yapılandırma doğrulamasını geliştir" --apply
```

Bu modda hedef yolların tamamı yazma öncesi doğrulanır; var olan dosyalar `.aegis/backups/<run-id>/` altına yedeklenir. Yazım sırasında hata çıkarsa geri alma **deneniyor**, ancak işletim sistemi çökmesi, harici eşzamanlı değişiklik veya dosya sistemi hatasında tam işlem garantisi verilemez. Uygulama sonrası testleri ayrıca çalıştır ve diff'i gözden geçir. Modelin “test geçti” demesi test kanıtı değildir.

## Hataları inceleme

### Python kaynak kodu

```bash
python -m aegis inspect --workspace ./workspace
```

Tüm Python dosyaları için sözdizimi incelemesi yapar, TODO/FIXME/XXX notlarını listeler. Statik AST taraması çalışma zamanı hatalarını, güvenlik açıklarını veya iş mantığı doğruluğunu kanıtlamaz.

### Log / traceback

```bash
python -m aegis diagnose --log ./workspace/error.log
```

Logdaki yaygın hata sınıflarına dayalı olası neden ve önerilen doğrulama adımlarını verir. Bu bir uzman incelemesinin veya gerçek testin yerine geçmez.

## Ekran okuma ve gizlilik

1. `python -m aegis screen-permission grant --workspace ./workspace` komutunu interaktif terminalde çalıştırıp kalıcı izni açıkça ver.
2. `python -m aegis screen-permission status --workspace ./workspace` ile durumu kontrol et.
3. `python -m aegis screen-analyze --workspace ./workspace` çalıştır; her yakalama öncesi ayrıca izin sorulur.
4. İzni kapatmak için `python -m aegis screen-permission revoke --workspace ./workspace` kullan.

Ekran görüntüsünü göndermeden önce araç hangi model uç noktasına gideceğini gösterir. Uzak bir sağlayıcı yapılandırdıysan görüntü cihazdan çıkar. Parola, kişisel mesaj veya başka bir gizli veri görünüyorsa onay verme. Ekran analizinin çalışması için seçilen modelin görsel girdiyi desteklemesi gerekir; uç nokta/vision desteği bu test ortamında doğrulanmamıştır. Başarılı analiz, dosyaların değiştirildiği veya test edildiği anlamına gelmez. Android uygulaması için bu CLI onayı tek başına Android ekran kaydı izni yerine geçmez; native Android sürümünde MediaProjection'un kendi sistem izni ayrıca alınmalıdır.

## Raporlar ve dosyalar

- `.aegis/state.json`: en son görev durumları
- `.aegis/events.jsonl`: olay günlüğü
- `.aegis/screen-permission.json`: ekran izni tercihi
- `.aegis/backups/`: ajan uygulama yedekleri
- `reports/aegis-report.json` ve `reports/aegis-report.html`: plan çalıştırma raporu
- `reports/agent-proposal.json`: model önerisi ve diff kaydı
- `assets/`: SVG/PNG sistem logosu, uygulama ikonu ve splash ekranı

Raporlar kaynak kodunun kusursuzluğunu değil, kaydedilen işlemleri ve sonuçları gösterir. Ekran görüntüleri AEGIS tarafından kaydedilmez.

## Güvenlik sınırları

- Bu paket bir işletim sistemi sandbox'ı değildir. `python_unittest` görevleri, test kodunu geçerli kullanıcı haklarıyla çalıştırır.
- Genel amaçlı, modelden dönen shell komutlarını çalıştırma aracı yoktur. Plan motoru yalnızca sabitlenmiş görev türlerini destekler.
- Path/symlink kontrolleri savunma katmanıdır; TOCTOU yarışlarına karşı tam, işletim sistemi seviyesinde izolasyon sağlamaz.
- Kod ajanı kendi çıktısını güvenilir kabul etmez. Yine de model tarafından önerilen kod, insan incelemesi ve test gerekir.
- Uzak modeller proje bağlamını veya ekran görüntüsünü alabilir; endpoint'i ve veri politikasını kontrol et.

Güvenlik modeli: [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md)
Araştırılmış referanslar: [`docs/REPOSITORY_RESEARCH.md`](docs/REPOSITORY_RESEARCH.md)
Değişiklik günlüğü: [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

## GitHub'a gönderme

Bu ZIP dosyası yerel kaynak teslimatıdır; bu oluşturma adımında GitHub'a push yapılmış değildir. Bağlı GitHub aracında yeni repository oluşturma işlemi bulunmadığından burada yeni uzak depo açamıyorum. Kendi GitHub hesabında boş bir `AEGIS-PRO` deposu oluşturduktan sonra proje kökünde aşağıdaki script'i çalıştırabilirsin:

```bash
./scripts/publish-to-github.sh git@github.com:YOUR-ACCOUNT/AEGIS-PRO.git
```

Script yalnızca GitHub HTTPS/SSH URL'si kabul eder, mevcut `origin` adresini sessizce değiştirmez ve kimlik bilgisini kaynak koda yazmaz. SSH veya Git credential manager oturumun önceden yapılandırılmış olmalıdır. İlk push öncesinde dosyaları kendin incele; `.env`, model anahtarı, proje workspace'i veya özel logları depoya ekleme.

### Canlı proje dosyası izleme

```bash
python -m aegis watch --workspace ./workspace --interval 5
```

Komut Python dosyalarının değişimini izler; değişiklik algılanınca sözdizimi taramasını yeniden çalıştırır. `Ctrl+C` ile durdur. Bu bir sistem servisi veya güvenlik izleme ürünü değildir; sadece komut çalıştığı sürece proje dosyalarını izler. Ekran yakalamayı otomatik başlatmaz.
