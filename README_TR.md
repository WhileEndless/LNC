# LNC - Yerel Ağ Tarayıcısı

LNC, SMB paylaşımları ve FTP sunucuları gibi yerel ağ kaynaklarından veri keşfi ve çıkarımı için tasarlanmış güçlü bir araçtır. Bu kapsamlı program, kullanıcıların ağ ortamlarındaki hassas bilgileri verimli bir şekilde bulması, indirmesi ve analiz etmesi için çeşitli özellikler sunar.

## Özellikler

1. **SMB Paylaşım Listeleme**: LNC, hedef sistemlerdeki mevcut SMB paylaşımlarını listeleyebilir ve erişim izinlerini kontrol edebilir.
2. **SMB/FTP Paylaşım Tarama**: Kullanıcı tanımlı filtre ve desenlere göre SMB ve FTP paylaşımlarını özyinelemeli olarak tarayarak dosya ve dizinleri çıkarabilir.
3. **SMB/FTP Dosya İndirme**: SMB ve FTP paylaşımlarından belirli dosya ve dizinleri, dosya türü ve desenlerine göre filtreleyerek indirebilir.
4. **SMB/FTP Dosya Analizi**: İndirilen dosyaları analiz ederek şifreler, kredi kartı numaraları ve TCKN (Türkiye Cumhuriyeti Kimlik Numarası) gibi hassas bilgileri çıkarabilir.
5. **Ağ Dayanıklılığı ve Otomatik Kurtarma**: Gelişmiş ağ hatası algılama ve otomatik duraklatma/devam ettirme işlevselliği. Başarısız işlemler, ağ bağlantısı geri geldiğinde otomatik olarak yeniden denenir.
6. **Çiftleme Önleme**: Tarama işlemleri sırasında işlenen dosyaların akıllı takibi, kesintiler sonrası işlemler devam ettirildiğinde çiftleme işlemeyi önler.
7. **Gelişmiş Yapılandırma**: Kimlik doğrulama bilgileri, yeniden deneme ayarları, çıktı dosyası yönetimi ve çeşitli filtre ve desenler için kapsamlı yapılandırma seçenekleri sunar.

## Kurulum

1. Öncelikle pipx kurulu değilse, kurmanız gerekiyor. Kurulum talimatları için şu adresi ziyaret edin:
   
   https://github.com/pypa/pipx

2. LNC'yi pipx kullanarak kurun:

   ```bash
   pipx install git+https://github.com/WhileEndless/LNC.git
   ```

   Bu komut:
   - LNC için izole bir ortam oluşturur
   - Gerekli tüm bağımlılıkları kurar
   - `lnc` komutunu sisteminizde kullanılabilir hale getirir

3. Kurulumu doğrulayın:

   ```bash
   lnc --help
   ```

İleride LNC'yi güncellemek isterseniz:

```bash
pipx upgrade lnc
```

Kaldırmak için:

```bash
pipx uninstall lnc
```

## Kullanım

LNC, her işlev için çoklu alt komutlar sunan bir komut satırı arayüzü sağlar. Kullanıcılar, aracın davranışını özelleştirmek için çeşitli argümanlar ve yapılandırma seçenekleriyle bu komutları çalıştırabilir.

### Yardım

Dahili yardım belgelerine erişmek için aşağıdaki komutu kullanın:

   ```bash
   lnc -h
   ```

Bu komut, mevcut tüm komutların, argümanların ve açıklamalarının kapsamlı bir listesini görüntüler.

### SMB Paylaşım Listeleme

Hedef sistemdeki mevcut SMB paylaşımlarını listelemek için aşağıdaki komutu kullanın:

   ```bash
   lnc smb share -t 192.168.1.100 -u kullaniciAdi -p parola
   ```

Bu komut, hedef sistemdeki erişilebilir SMB paylaşımlarını ve erişim izinlerini listeler.

### SMB/FTP Paylaşım Tarama

SMB veya FTP paylaşımlarını özyinelemeli olarak taramak ve kullanıcı tanımlı filtre ve desenlere göre dosya ve dizinleri çıkarmak için aşağıdaki komutu kullanın:

   ```bash
   lnc smb crawl -t 192.168.1.100 -u kullaniciAdi -p parola -f paylasimlar.json
   ```

`paylasimlar.json` dosyası, taranacak SMB veya FTP paylaşımlarının listesini içermelidir. LNC, yapılandırılan filtre ve desenlere göre dosya ve dizinleri indirecektir.

### SMB/FTP Dosya İndirme

SMB veya FTP paylaşımlarından dosya türleri veya desenlere göre belirli dosyaları indirmek için aşağıdaki komutu kullanın:

   ```bash
   lnc smb download -t 192.168.1.100 -u kullaniciAdi -p parola -f cikti_dosyalari.json
   ```

`cikti_dosyalari.json` dosyası, indirilecek dosyaların listesini içermelidir. LNC, yapılandırılan filtre ve desenlere göre dosyaları indirecektir.

### SMB/FTP Dosya Analizi

İndirilen SMB veya FTP dosyalarını analiz etmek ve şifreler, kredi kartı numaraları ve TCKN (Türkiye Cumhuriyeti Kimlik Numarası) gibi hassas bilgileri çıkarmak için aşağıdaki komutu kullanın:

   ```bash
   lnc smb analyze -t 192.168.1.100 -u kullaniciAdi -p parola -f cikti_dosyalari.json
   ```

`cikti_dosyalari.json` dosyası, analiz edilecek dosyaların listesini içermelidir. LNC, belirtilen hassas bilgileri dosyalardan çıkaracaktır.

## Yapılandırma

LNC, komut satırı argümanları veya YAML yapılandırma dosyası aracılığıyla sağlanabilen kapsamlı yapılandırma seçeneklerini destekler. Kullanıcılar, LNC'nin davranışını özel gereksinimlerine göre özelleştirmek için bir YAML yapılandırma dosyası oluşturabilir ve `--config` argümanıyla dosya yolunu belirtebilir. İşte örnek bir yapılandırma:

```yaml
output: output
disable_output_json: False
disable_output_text: False
write_errors_to_file: False
disable_output_end_prefix: False
enable_error_output: False
max_parallel_job: 3
retry_count: 3
delay_before_retry: 0.01
timeout: 0.1
smb_port: 445
smb_shares_check_read: True
smb_shares_check_write: True
smb_files_ignore_shares:
  - ipc$
  - print$
always_download:
  - \.config$
  - \.ini$
  - \.dll$
  - \.txt$
  - \.metadata$
  - \.rsc$
download_folder: ./donwloads/
max_download_size: 10
disable_password_check: False
disable_sensitive_check: False
disable_username_check: False
patterns:
  TCKN:
    - "[1-9]{1}[0-9]{9}[02468]{1}"
  credit_card:
    - "4[\\d\\s]{12}(?:[\\d\\s]{3})?"
    - "(?:5[1-5]|2[2-7])[\\d\\s]{14}"
    - "6(?:011|5[\\d\\s]{2})[\\d\\s]{12}"
    - "3[47][\\d\\s]{13}"
    - "3(?:0[0-5]|[68][\\d\\s])[\\d\\s]{11}"
    - "(?:2131|1800|35[\\d\\s]{3})[\\d\\s]{11}"
    - "(?:5[0678][\\d\\s]{2}|6304|6390|67[\\d\\s]{2})[\\d\\s]{8,15}"
  password:
    - "password"
    - "pwd="
    - "şifre"
    - "parola"
    - "sifre"
    - "contentHash"
add_filename_to_analyz: True
check_binarys: True
take_before: 50
take_after: 50
keep-extracted-files: False
always-keep-extracted-files: False
add-filename-to-analyze: True
thread: 20
ignore_folder_name_contains:
  - "audio"
  - "bin"
  - "boot"
  - "dev"
  - "etc"
  - "lib"
  - "lib64"
  - "lost+found"
  - "media"
  - "opt"
  - "proc"
  - "run"
  - "sbin"
  - "srv"
  - "sys"
  - "tmp"
  - "usr"
  - "snap"
  - "swapfile"
  - "vmlinuz"
```

Özel yapılandırma dosyasını kullanmak için aşağıdaki komutu çalıştırın:

   ```bash
   lnc [komut] [seçenekler] -c config.yaml
   ```

Burada `config.yaml`, özel yapılandırma dosyanızın yoludur.

### Temel Yapılandırma Seçenekleri

#### Ağ Erişilebilirliği ve Kurtarma
- `network_accessibility_check`: Otomatik ağ hatası algılamayı etkinleştir/devre dışı bırak (varsayılan: True)
- `auto_resume_on_recovery`: Ağ geri geldiğinde işlemleri otomatik olarak devam ettir (varsayılan: True)
- `error_threshold_for_check`: Ağ kontrolünü tetiklemeden önceki ardışık hata sayısı (varsayılan: 10)
- `accessibility_check_interval`: Ağ kurtarma kontrolleri arasındaki saniye (varsayılan: 30)
- `accessibility_check_timeout`: Ağ erişilebilirlik testleri için zaman aşımı (varsayılan: 5)

#### Performans ve Thread Yönetimi
- `thread`: Paralel işleme için worker thread sayısı (varsayılan: 10)
- `max_parallel_job`: Hostlara maksimum paralel bağlantı (varsayılan: 5)
- `max_dir_entries`: Bu sayıdan fazla girişi olan dizinleri atla (varsayılan: 1000)

#### Dosya İşleme
- `check_binaries`: Analiz sırasında binary dosyaları atla (varsayılan: True)
- `max_download_size`: İndirilecek maksimum dosya boyutu MB cinsinden (varsayılan: 10)
- `always_download`: Filtrelerden bağımsız olarak her zaman indirilecek dosyalar için regex desenleri

#### Desen Eşleştirme
- `patterns`: Hassas veri algılama için özel regex desenleri (TCKN, credit_card, password)
- `take_before`: Desen eşleşmesinden önce yakalanacak karakter sayısı (varsayılan: 50)
- `take_after`: Desen eşleşmesinden sonra yakalanacak karakter sayısı (varsayılan: 50)

## Ağ Dayanıklılığı Özellikleri

LNC, ağ kesintilerini otomatik olarak ele alan gelişmiş ağ dayanıklılığı yetenekleri içerir:

### Otomatik Hata Algılama
- İşlemler sırasında ağ hatalarını izler
- Hata eşiği aşıldığında otomatik olarak algılar
- Son başarılı bağlantı parametrelerini kullanarak ağ bağlantısını test eder

### Akıllı Kurtarma
- **Otomatik Devam Modu**: Ağ geri geldiğinde işlemleri otomatik olarak devam ettirir
- **Manuel Mod**: İşlemleri devam ettirmeden önce kullanıcı onayı ister
- **Başarısız Öğe Yeniden Deneme**: Ağ kurtarımından sonra başarısız işlemleri otomatik olarak yeniden dener

### Çiftleme Önleme
- Tarama işlemleri sırasında işlenen dosyaları takip eder
- Kesintiler sonrası işlemler devam ettirildiğinde çiftleme işlemeyi önler
- Durumu geçici takip dosyalarında tutar (`.lnc_crawl_tracking_*.json`)

### Kullanım Örnekleri

#### Otomatik Kurtarmalı Temel SMB Analizi
```bash
lnc smb analyze -t 192.168.1.100 -u administrator -p password
```
Çalıştırma sırasında ağ hatası olursa, LNC otomatik olarak durur, ağ kurtarımını izler ve kaldığı yerden devam eder.

#### Manuel Kurtarma Modu
```yaml
# config.yaml
auto_resume_on_recovery: False
```
```bash
lnc smb crawl -t 192.168.1.100 -u user -p pass -c config.yaml
```
Ağ hatası olursa, LNC devam etmeden önce kullanıcı onayı ister.

#### Ağ İzlemeyi Devre Dışı Bırakma
```yaml
# config.yaml
network_accessibility_check: False
```
Otomatik ağ izleme ve yeniden deneme işlevselliğini devre dışı bırakır.

## Lisans

Bu proje GNU Affero Genel Kamu Lisansı v3.0 (AGPL-3.0) ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.
