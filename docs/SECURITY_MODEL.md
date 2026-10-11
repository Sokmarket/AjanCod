# AEGIS PRO güvenlik ve güven sınırları

## Varlıklar

- Kaynak kodu ve yapılandırma dosyaları
- API anahtarları/erişim belirteçleri
- Ekranda açık olabilecek parola, özel mesaj veya iş verileri
- Model önerisi, olay günlüğü, rapor ve yedekler
- Komut çalıştırılan kullanıcının dosyaları ve yetkileri

## Kontroller

1. Plan görev türleri allowlist ile sınırlandırılmıştır: `write_text`, `python_compile`, `python_unittest`.
2. Alt süreçler shell üzerinden başlatılmaz; süre sınırı uygulanır. POSIX'te timeout sırasında süreç grubu sonlandırılır.
3. Dosya yolu workspace dışına çıkamaz; var olan symlink bileşenleri reddedilir. Bu, işletim sistemi izolasyonu yerine geçmez.
4. Model bağlamı sınırlıdır, bilinen hassas adlar atlanır ve yaygın token/anahtar atamaları maskelenir. Bu redaksiyon kusursuz değildir.
5. Ajan cevabı JSON şemasından geçirilir. Kaynak dosyası değişikliği varsayılan olarak kapalıdır; `--apply` gerekir.
6. Uygulamadan önce hedef yolların tamamı doğrulanır. Mevcut dosyalar yedeklenir, yazım sırasında hata olursa rollback denenir.
7. Ekran okuma izni varsayılan kapalıdır. Kalıcı izin bir interaktif terminalde verilir ve her ekran yakalama öncesinde yeniden açık onay alınır.
8. Ekran görüntüsü geçici olarak bellekte işlenir, AEGIS tarafından diske yazılmaz. Bununla birlikte model endpoint'ine gönderilir; remote endpoint seçimi kullanıcı sorumluluğundadır.

## Açık riskler / uygulanmamış kontroller

- Kod çalıştırma ve birim testleri, özel bir kullanıcı hesabı/konteyner içinde otomatik izole edilmez.
- Dosya yolu kontrolü ile yazma arasındaki zamanlama aralığı TOCTOU yarışlarına açıktır; çok kullanıcılı tehdit modeline karşı güvenli dosya sistemi API'si olarak değerlendirilmemelidir.
- Secret redaction regex tabanlıdır, tüm gizli veri biçimlerini tanıyamaz.
- Çok dosyalı rollback işlem düzeyinde en iyi çabadır; güç/OS çökmesi veya yedek dosya sistemi hatalarında tam atomiklik garantisi yoktur.
- Ekran okuma donanım/masaüstü platformlarına bağlıdır ve bu teslimatta yalnızca izin kapısı birim test edilmiştir. Gerçek masaüstü yakalama ve yerel/uzak modelin vision desteği ayrıca doğrulanmalıdır. Bu Python CLI Android'in diğer uygulamalarının ekranını okuyamaz; native Android uygulamasında MediaProjection ve sistem onayı gerekir.
- Ağ erişimi kontrollü sandbox değildir. Model yanıtı untrusted data sayılmalı, hiçbir istem metni yeni araç/izin sağlamamalıdır.
- Otomatik GitHub push, deployment ve kendi kendine kalıcı izin verme yoktur.

## Önerilen üretim yaklaşımı

- Kod yürütmeyi ayrı ve geçici konteyner/OS hesabında, en az dosya ve ağ erişimiyle çalıştır.
- Uygulama öncesi diff incelemesini zorunlu tut; değişiklikleri Git branch/commit ile izlenebilir kıl.
- Test, lint, SAST, bağımlılık ve insan incelemesini birbirinden bağımsız kapılar olarak çalıştır.
- Ekran analizini onaylanmış veri sınıflarında kullan; gizli veri içeren ekranlarda görüntüyü göndermeden kapat.
- İzinleri ve logları düzenli denetle; secrets içeren raporları repoya commit etme.
