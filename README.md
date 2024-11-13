# LNC - Locale Network Crawler

LNC is a powerful tool designed to facilitate the exploration and extraction of data from local network resources, such as SMB shares and FTP servers. This comprehensive utility provides a versatile set of features that enable users to efficiently locate, download, and analyze sensitive information within their network environment.

## Features

1. **SMB Share Enumeration**: LNC can list and enumerate available SMB shares on target systems, allowing users to identify shared resources and their access permissions.
2. **SMB/FTP Share Crawling**: The tool can recursively crawl through SMB and FTP shares, extracting files and directories based on user-defined filters and patterns.
3. **SMB/FTP File Download**: LNC can download specific files or directories from SMB and FTP shares, allowing filtering based on file types and patterns.
4. **SMB/FTP File Analysis**: The tool can analyze downloaded files, extracting sensitive information such as passwords, credit card numbers, and TCKN (Turkish Citizenship ID) numbers.
5. **Robust Configuration**: LNC provides a comprehensive set of configuration options, including authentication credentials, retry settings, output file management, and various filters and patterns.

## Installation

1. First, install pipx if you haven't already installed it. For installation instructions, visit:
   
   https://github.com/pypa/pipx

2. Install LNC using pipx:

   ```bash
   pipx install git+https://github.com/WhileEndless/LNC.git
   ```

   This command will:
   - Create an isolated environment for LNC
   - Install all required dependencies
   - Make the `lnc` command available in your system

3. Verify the installation:

   ```bash
   lnc --help
   ```

If you need to upgrade LNC in the future, you can use:

```bash
pipx upgrade lnc
```

To uninstall LNC:

```bash
pipx uninstall lnc
```

## Usage

LNC provides a command-line interface with multiple sub-commands for each functionality. Users can run the tool with various arguments and configuration options to customize its behavior.

### Help

To access the built-in help documentation, run the following command:

   ```bash
   lnc -h
   ```

This will display a comprehensive list of all available commands, arguments, and their descriptions.

### SMB Share Enumeration

To list and enumerate available SMB shares on a target system, use the following command:

   ```bash
   lnc smb share -t 192.168.1.100 -u myUsername -p myPassword
   ```

This will list all the accessible SMB shares on the target system, including their access permissions.

### SMB/FTP Share Crawling

To recursively crawl through SMB or FTP shares and extract files and directories based on user-defined filters and patterns, use the following command:

   ```bash
   lnc smb crawl -t 192.168.1.100 -u myUsername -p myPassword -f shares.json
   ```

The `shares.json` file should contain a list of SMB or FTP shares to crawl. LNC will download the files and directories based on the configured filters and patterns.

### SMB/FTP File Download

To download specific files from SMB or FTP shares based on file types or patterns, use the following command:

   ```bash
   lnc smb download -t 192.168.1.100 -u myUsername -p myPassword -f output_files.json
   ```

The `output_files.json` file should contain a list of files to download. LNC will download the files based on the configured filters and patterns.

### SMB/FTP File Analysis

To analyze downloaded SMB or FTP files and extract sensitive information, such as passwords, credit card numbers, and TCKN (Turkish Citizenship ID) numbers, use the following command:

   ```bash
   lnc smb analyze -t 192.168.1.100 -u myUsername -p myPassword -f output_files.json
   ```

The `output_files.json` file should contain a list of files to analyze. LNC will analyze the files and extract the specified sensitive information.

## Configuration

LNC supports a comprehensive set of configuration options, which can be provided either through command-line arguments or a YAML configuration file. Users can create a YAML configuration file and specify its path using the `--config` argument to customize LNC's behavior according to their specific requirements. Here is an example configuration:

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

To use a custom configuration file, run the following command:

   ```bash
   lnc [command] [options] -c config.yaml
   ```

Where `config.yaml` is the path to your custom configuration file.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). See the [LICENSE](LICENSE) file for details.
