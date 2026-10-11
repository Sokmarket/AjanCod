# Seçilmiş açık kaynak mühendislik kaynakları

**Araştırma tarihi:** 2026-10-11. Bu belge tüm GitHub dünyasının tarandığını iddia etmez; belirli mühendislik sorularına yönelik seçilmiş kaynakları listeler. v0.3.0 içine bu projelerden kaynak kodu kopyalanmadı.

| Kaynak | İlk karar | AEGIS için öğrenilecek yaklaşım |
|---|---|---|
| [Aider](https://github.com/Aider-AI/aider) — Apache-2.0 lisans işareti upstream depoda | **INSPIRE** | Kod tabanı bağlamı, yinelemeli düzenleme/test döngüsü, diff ve Git iş akışı. Lisans işareti ve depodaki `LICENSE.txt` üzerinden ilk kontrol yapıldı. |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) — MIT lisans işareti upstream depoda | **INSPIRE** | Ajan/SDK/sunucu/araç katmanlarını ayırma, çalışma alanı yaşam döngüsü ve otomasyon mimarisi. |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent) — MIT lisansı, geniş bağımlılık kümesi | **INSPIRE** | Sorundan yamaya görev akışı, araç arayüzleri ve tekrarlanabilir değerlendirme. Kurulum script'leri ve yürütülebilir araçlar ayrı güvenlik incelemesi gerektirir. |
| [Ollama OpenAI uyumluluğu](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx) | **ADAPT** | Yerel model endpoint'i ve görsel giriş desteği. Vision özelliği kullandığın model/endpoint'e göre ayrıca kontrol edilmelidir. |
| [OWASP Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html) | **ADAPT** | Diff tabanlı güvenlik incelemesi, veri akışı, erişim kontrolü, konfigürasyon, log ve sırların korunması. |

## Bu incelemenin sınırı

Upstream ana dalı değişebilir. Bu nedenle gerçek kodu yeniden kullanmadan önce değişmez commit veya release seçilmeli; ilgili kaynak, test, `pyproject.toml`, lisans/NOTICE, CI ve güvenlik kayıtları tekrar incelenmelidir. Bu çalışma bir tam kaynak kodu güvenlik denetimi değildir. Resmî OWASP rehberi manuel incelemenin otomatik taramaları tamamladığını ve bağlamsal mantık hatalarında insan değerlendirmesinin önemini açıklar ([OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)). Ollama'nın resmi uyumluluk belgesi Chat Completions API'sinde görüntü girdisi desteğini bildirir; bu, her modelin görsel anlama kabiliyeti olduğu anlamına gelmez ([Ollama docs](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx)).

## Uyarlama kapıları

1. Kaynak URL'si ve immutable commit/release kaydı.
2. Lisans ve ek bildirimlerin kontrolü.
3. Yalnızca gerekli dosya/test/dependency/CI alanlarının incelenmesi.
4. Bağımlılık ve bakım durumunun değerlendirilmesi.
5. Kodun bir kaynaktan geldiğini ve hangi değişikliklerin yapıldığını kaydetme.
6. Sadece README okumayla lisans veya güvenlik uygunluğu iddia etmeme.
7. `REUSE`, `ADAPT`, `INSPIRE`, `DO NOT USE` kararı ve kanıt notu tutma.
