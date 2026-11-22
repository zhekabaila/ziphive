"""Isi laporan UAS ZipHive (PLAN.md P10-T2).

Seluruh angka pada berkas ini disalin dari `results/summary.csv`,
`results/summary_agg.csv`, dan `docs/ANALYSIS.md`. Tidak ada angka baru yang
dihitung di sini. Bagian yang datanya belum tersedia ditandai
`PERLU DIISI USER` sesuai SUBMISSION.md bagian 2.

Penanda format di dalam teks: **teks** menjadi tebal dan `teks` menjadi huruf
monospasi. Kedua penanda diolah oleh `scripts/build_report.py` dan tidak muncul
pada dokumen akhir.
"""

from __future__ import annotations

from typing import Any

BLOCKS: list[tuple[str, Any]] = [
    # ------------------------------------------------------------------ BAB I
    ("h1", ("BAB I", "PENDAHULUAN")),
    ("h2", "1.1 Latar Belakang"),
    (
        "p",
        "Komputasi paralel merupakan pendekatan pemrosesan yang membagi satu pekerjaan besar "
        "menjadi beberapa bagian yang dikerjakan secara bersamaan, baik pada satu mesin dengan "
        "beberapa proses maupun pada beberapa mesin yang terhubung melalui jaringan. Pendekatan "
        "ini dipakai ketika beban kerja bersifat komputasi intensif dan bagian-bagian pekerjaannya "
        "dapat diselesaikan tanpa saling menunggu. Kompresi data termasuk pekerjaan semacam itu, "
        "karena setiap potongan data dapat dikompresi secara mandiri tanpa mengetahui isi potongan "
        "lain.",
    ),
    (
        "p",
        "Kompresi data bertujuan memperkecil ukuran berkas agar biaya penyimpanan dan pengiriman "
        "berkurang. Pada algoritma berbasis kamus seperti `lzma`, proses kompresi menuntut CPU dan "
        "memori yang besar. Satu proses kompresi pada satu mesin karena itu hanya memakai sebagian "
        "kecil kapasitas perangkat yang tersedia, sedangkan waktu penyelesaian menjadi panjang. "
        "Kondisi tersebut mendorong penggunaan beberapa proses sekaligus dalam satu mesin, lalu "
        "ditingkatkan lagi dengan membagi pekerjaan ke beberapa mesin.",
    ),
    (
        "p",
        "Pemrosesan pada satu mesin dibatasi jumlah inti prosesor dan kapasitas memori. Ketika "
        "beban kerja harus diselesaikan dalam waktu yang lebih singkat, kapasitas tambahan "
        "diperoleh dengan memakai beberapa mesin yang saling terhubung. Sistem terdistribusi "
        "memungkinkan penambahan mesin tanpa mengganti perangkat yang sudah berjalan, tetapi "
        "memunculkan persoalan baru berupa pembagian beban, pemantauan kondisi setiap mesin, dan "
        "penanganan mesin yang berhenti di tengah pekerjaan.",
    ),
    (
        "p",
        "Arsitektur Master-Worker dipilih karena memisahkan pengelolaan pekerjaan dari pelaksanaan "
        "pekerjaan. Master memegang daftar bagian pekerjaan yang belum selesai, membagikannya, dan "
        "memeriksa hasil, sedangkan Worker hanya mengerjakan bagian yang diberikan. Pemisahan ini "
        "membuat penambahan atau pengurangan Worker tidak mengubah logika pembagian pekerjaan. "
        "Seluruh komunikasi melewati Master sehingga setiap Worker tidak perlu mengetahui "
        "keberadaan Worker lain, dan pembagian beban dapat dipusatkan pada satu tempat.",
    ),
    (
        "p",
        "Pada pelaksanaan tugas UAS Tema 16 Distributed Data Compression, dirancang aplikasi "
        "bernama ZipHive yang memecah dataset menjadi chunk berukuran 4 MiB, membagikan chunk "
        "tersebut ke sembilan Worker melalui koneksi TCP, dan mengumpulkan kembali hasil kompresi "
        "beserta verifikasi SHA-256. Soal menuntut minimal sepuluh node fisik. Pelaksanaan pada "
        "2026-11-22 memakai sepuluh node virtual pada satu laptop, yaitu satu Master pada sistem "
        "utama dan sembilan Worker berupa container, "
        "sesuai keputusan ADR-015. Deviasi ini diungkap "
        "pada Bab III dan Bab IV agar pembaca tidak menyimpulkan bahwa pengukuran dilakukan pada "
        "sepuluh perangkat terpisah.",
    ),
    ("h2", "1.2 Rumusan Masalah"),
    (
        "p",
        "Berdasarkan latar belakang tersebut, masalah yang dibahas dirumuskan sebagai berikut:",
    ),
    (
        "numbers",
        [
            "Bagaimana merancang sistem kompresi data "
            "terdistribusi dengan arsitektur Master-Worker "
            "yang dapat dijalankan pada sepuluh node.",
            "Bagaimana membagi tugas secara seimbang di antara Worker yang kecepatannya berbeda.",
            "Bagaimana menjaga agar proses tetap selesai ketika satu atau beberapa Worker berhenti "
            "di tengah pekerjaan.",
            "Seberapa besar percepatan yang diperoleh dibanding pemrosesan berurutan pada satu "
            "mesin, serta faktor apa yang membatasi percepatan tersebut.",
        ],
    ),
    ("h2", "1.3 Tujuan"),
    (
        "p",
        "Tujuan yang ingin dicapai pada tugas ini adalah sebagai berikut:",
    ),
    (
        "numbers",
        [
            "Membangun sistem kompresi data terdistribusi berbasis Master-Worker yang memakai "
            "protokol TCP, proses paralel di setiap Worker, penjadwalan dinamis, dan pemantauan "
            "heartbeat.",
            "Mengukur waktu penyelesaian pemrosesan berurutan sebagai dasar pembanding, lalu "
            "membandingkannya dengan pemrosesan paralel pada satu mesin.",
            "Mengukur kinerja sistem terdistribusi dengan sembilan Worker serta membandingkan "
            "penjadwalan statis dan dinamis pada kondisi terdapat Worker yang lebih lambat.",
            "Menguji ketahanan sistem terhadap kegagalan "
            "Worker dan mengukur lama deteksi serta lama "
            "pemulihan.",
            "Menganalisis penyebab percepatan yang diperoleh tidak mencapai jumlah proses atau "
            "jumlah Worker yang dipakai.",
        ],
    ),
    ("h2", "1.4 Batasan Masalah"),
    (
        "p",
        "Ruang lingkup pembahasan dibatasi sebagai berikut:",
    ),
    (
        "bullets",
        [
            "Sepuluh node dijalankan sebagai node virtual "
            "pada satu laptop, bukan sepuluh perangkat "
            "fisik terpisah, sesuai ADR-015.",
            "Dataset yang dipakai adalah dataset sintetis "
            "2048 MiB berisi delapan berkas dengan seed "
            "20261122, bukan korpus Silesia, karena korpus tersebut tidak tersedia secara luring.",
            "Algoritma kompresi yang diuji adalah `lzma` preset 6 dengan ukuran chunk 4 MiB.",
            "Master tidak direplikasi sehingga menjadi titik kegagalan tunggal, dan hal ini "
            "diperlakukan sebagai keterbatasan, bukan bagian yang diuji.",
            "Pengukuran dilakukan pada satu mesin sehingga angka yang dilaporkan memuat overhead "
            "virtualisasi dan tidak mewakili jaringan laboratorium dengan perangkat terpisah.",
        ],
    ),
    ("h2", "1.5 Sistematika Penulisan"),
    (
        "p",
        "Laporan disusun dalam empat bab. Bab I memuat latar belakang, rumusan masalah, tujuan, "
        "batasan, dan sistematika penulisan. Bab II "
        "memuat studi pustaka mengenai komputasi paralel "
        "dan terdistribusi, arsitektur Master-Worker, multiprocessing pada Python, penyeimbangan "
        "beban, fault tolerance, algoritma kompresi, serta metrik evaluasi yang dipakai. Bab III "
        "memuat metodologi yang mencakup rancangan sistem, topologi sepuluh node, mekanisme kerja, "
        "dan rancangan eksperimen. Bab IV memuat hasil implementasi, hasil pengukuran setiap "
        "eksperimen, pembahasan, dan keterbatasan pengukuran. Bagian terakhir memuat kesimpulan, "
        "keterbatasan, dan saran.",
    ),
    (
        "p",
        "Istilah teknis yang dipakai berulang pada laporan ini dirangkum pada Tabel 1.1 agar "
        "pembaca memiliki acuan yang sama sejak awal.",
    ),
    (
        "table",
        {
            "caption": "Tabel 1.1 Istilah dan Singkatan yang Dipakai pada Laporan",
            "widths": [2000, 6700],
            "header": ["Istilah", "Penjelasan"],
            "rows": [
                [
                    "Master",
                    "Proses pusat yang memecah dataset, membagikan task, dan memverifikasi hasil.",
                ],
                ["Worker", "Proses pekerja yang mengambil task, mengompresi, dan mengirim hasil."],
                [
                    "Task",
                    "Satu chunk berkas berukuran 4 MiB yang menjadi satuan pembagian pekerjaan.",
                ],
                [
                    "Scheduler",
                    "Penentu task berikutnya untuk setiap Worker, bersifat statis atau dinamis.",
                ],
                [
                    "Heartbeat",
                    "Pesan berkala dari Worker ke Master sebagai penanda Worker masih hidup.",
                ],
                [
                    "Imbalance factor",
                    "Rasio waktu sibuk terbesar terhadap rata-rata waktu sibuk Worker.",
                ],
                ["Makespan", "Waktu dari task pertama dikirim sampai hasil terakhir ditulis."],
                ["Manifest", "Berkas catatan hasil setiap chunk beserta ukuran dan SHA-256."],
                [
                    "Speedup",
                    "Perbandingan waktu pemrosesan dasar terhadap waktu konfigurasi yang diuji.",
                ],
                ["Efficiency", "Speedup dibagi jumlah proses atau Worker yang dipakai."],
            ],
        },
    ),
    # ----------------------------------------------------------------- BAB II
    ("h1", ("BAB II", "STUDI PUSTAKA")),
    ("h2", "2.1 Komputasi Paralel dan Terdistribusi"),
    (
        "p",
        "Komputasi paralel adalah pelaksanaan beberapa "
        "bagian program secara bersamaan dengan tujuan "
        "memperpendek waktu penyelesaian. Pada satu mesin, paralelisme diperoleh melalui beberapa "
        "proses atau thread yang dijadwalkan oleh sistem operasi pada inti prosesor yang tersedia. "
        "Percepatan yang dicapai tidak pernah sebanding "
        "dengan jumlah inti karena selalu ada bagian "
        "pekerjaan yang berurutan, biaya pembuatan proses, "
        "dan perebutan sumber daya bersama seperti "
        "bandwidth memori dan cache.",
    ),
    (
        "p",
        "Komputasi terdistribusi melibatkan beberapa mesin yang saling terhubung melalui jaringan, "
        "sehingga kapasitas yang tersedia dapat melampaui kapasitas satu mesin. Konsekuensinya, "
        "pekerjaan harus dikirim melalui jaringan, hasilnya "
        "dikumpulkan kembali, dan kegagalan salah "
        "satu mesin harus ditangani tanpa menghentikan keseluruhan proses. Hal ini berbeda dengan "
        "komputasi paralel pada satu mesin, di mana seluruh proses berbagi memori dan tidak ada "
        "risiko mesin lain terputus.",
    ),
    (
        "p",
        "Pada tugas ini kedua pendekatan dipakai bersama. Pemrosesan paralel berjalan di dalam "
        "setiap Worker melalui sekumpulan proses, sedangkan pemrosesan terdistribusi berjalan di "
        "antara Master dan sembilan Worker. Pemisahan ini membuat beban kompresi dapat tersebar ke "
        "banyak inti prosesor yang berada di beberapa node.",
    ),
    ("h2", "2.2 Arsitektur Master-Worker"),
    (
        "p",
        "Arsitektur Master-Worker memisahkan peran pengelola pekerjaan dari peran pelaksana "
        "pekerjaan. Master memegang daftar task, mencatat status setiap task, dan memutuskan task "
        "mana yang dikirim ke Worker tertentu. Worker menerima task, mengerjakannya, lalu "
        "mengirimkan hasil kembali. Pada rancangan ini Worker tidak berkomunikasi satu sama lain, "
        "sehingga topologi yang terbentuk menyerupai bintang dengan Master sebagai pusat.",
    ),
    (
        "p",
        "Pemisahan peran tersebut memberikan dua keuntungan. Pertama, penambahan atau pengurangan "
        "Worker tidak mengubah logika pembagian task karena seluruh keputusan berada di Master. "
        "Kedua, pemantauan kondisi Worker dan pengembalian task yang gagal dapat dilakukan di satu "
        "tempat. Sebaliknya, Master menjadi titik kegagalan tunggal dan pusat lalu lintas data, "
        "sehingga kapasitasnya membatasi kinerja keseluruhan sistem.",
    ),
    ("h2", "2.3 Multiprocessing pada Python"),
    (
        "p",
        "Modul `multiprocessing` menyediakan proses "
        "terpisah yang masing-masing memiliki interpreter "
        "Python sendiri. Pendekatan ini dipilih karena proses kompresi bersifat terikat CPU, "
        "sehingga thread tidak memberi percepatan akibat adanya global interpreter lock. Setiap "
        "Worker menjalankan `Pool` berisi sejumlah proses, dan fungsi kompresi diletakkan pada "
        "tingkat teratas modul agar dapat dipanggil pada proses anak.",
    ),
    (
        "p",
        "Metode pembuatan proses disetel ke `spawn` agar kode berjalan sama pada macOS, Linux, dan "
        "Windows. Konsekuensi `spawn` adalah setiap proses anak memuat ulang modul dan tidak "
        "mewarisi keadaan proses induk, sehingga fungsi yang dikirim ke `Pool` harus berupa fungsi "
        "tingkat teratas tanpa lambda dan tanpa keadaan global yang dapat berubah. Rancangan ini "
        "memperlambat pembentukan proses pertama, tetapi membuat perilaku program seragam di semua "
        "platform.",
    ),
    ("h2", "2.4 Penyeimbangan Beban"),
    (
        "p",
        "Penyeimbangan beban menentukan cara task dibagikan ke Worker. Pada penjadwalan statis, "
        "seluruh task dibagi rata sejak awal berdasarkan urutan, tanpa memperhatikan kecepatan "
        "Worker. Cara ini sederhana dan murah, tetapi hasil akhirnya ditentukan oleh Worker "
        "terlambat karena Worker tersebut tetap menerima jumlah task yang sama. Pada penjadwalan "
        "dinamis, pembagian dilakukan sedikit demi sedikit sesuai permintaan Worker, sehingga "
        "Worker yang cepat akan mengambil lebih banyak task.",
    ),
    (
        "p",
        "Rancangan ZipHive memakai mekanisme credit. Worker mengirim permintaan sejumlah credit "
        "sesuai jumlah proses yang dimilikinya, dan Master mengirim satu task untuk setiap credit "
        "yang tersedia. Setiap kali satu task selesai, "
        "Worker mengirim permintaan satu credit baru. "
        "Antrean task diurutkan dari ukuran terbesar agar task besar tidak tertinggal pada akhir "
        "pekerjaan. Perbandingan kedua cara penjadwalan dirangkum pada Tabel 2.1.",
    ),
    (
        "table",
        {
            "caption": "Tabel 2.1 Perbandingan Penjadwalan Statis dan Dinamis",
            "widths": [1400, 3650, 3650],
            "header": ["Aspek", "Statis", "Dinamis"],
            "rows": [
                [
                    "Pembagian awal",
                    "Seluruh task dibagi rata secara round-robin sebelum pekerjaan dimulai.",
                    "Task dikirim satu per satu sesuai permintaan credit Worker.",
                ],
                [
                    "Penyesuaian kecepatan",
                    "Tidak ada, Worker lambat tetap menerima jumlah task yang sama.",
                    "Worker cepat meminta lebih banyak task sehingga menerima porsi lebih besar.",
                ],
                [
                    "Pengaruh Worker lambat",
                    "Menentukan akhir pekerjaan karena sisa task menumpuk di sana.",
                    "Berkurang karena porsi task Worker lambat menyusut dengan sendirinya.",
                ],
                [
                    "Biaya pengelolaan",
                    "Sangat kecil karena pembagian dilakukan sekali di awal.",
                    "Sedikit lebih besar karena setiap task memerlukan pertukaran credit.",
                ],
                [
                    "Ukuran pembeda",
                    "Makespan dan imbalance factor.",
                    "Makespan dan imbalance factor dengan beban Worker yang tidak seragam.",
                ],
            ],
        },
    ),
    ("h2", "2.5 Fault Tolerance"),
    (
        "p",
        "Fault tolerance adalah kemampuan sistem menyelesaikan pekerjaan walaupun sebagian "
        "komponennya berhenti. Pada arsitektur Master-Worker, kegagalan yang paling sering dibahas "
        "adalah Worker yang berhenti mendadak sehingga task yang sedang dikerjakannya tidak pernah "
        "menghasilkan jawaban. Tanpa penanganan, task tersebut tetap berstatus terkirim dan "
        "pekerjaan tidak pernah selesai.",
    ),
    (
        "p",
        "ZipHive mendeteksi kegagalan melalui dua jalur. Pertama, koneksi socket yang tertutup "
        "langsung terbaca sebagai akhir aliran data sehingga Worker dapat ditandai mati tanpa "
        "menunggu batas waktu. Kedua, Master memeriksa tanda terakhir hidup setiap Worker, dan "
        "Worker yang tidak mengirim pesan apa pun melebihi batas waktu dinyatakan mati. Setelah "
        "Worker dinyatakan mati, seluruh task yang masih tercatat padanya dikembalikan ke antrean "
        "dengan penghitung percobaan ditambah satu, lalu diambil Worker lain.",
    ),
    (
        "p",
        "Hasil yang datang terlambat dari Worker yang sudah dinyatakan mati diabaikan agar tidak "
        "menggandakan hasil. Task yang gagal dikerjakan juga diulang sampai batas percobaan "
        "tertentu, dan setelah batas tersebut tercapai "
        "task dicatat sebagai gagal beserta alasannya. "
        "Pendekatan ini menjaga agar sistem tetap menyelesaikan pekerjaan selama masih ada Worker "
        "yang hidup, tanpa memerlukan penyimpanan status ke disk.",
    ),
    ("h2", "2.6 Algoritma Kompresi"),
    (
        "p",
        "Python menyediakan tiga modul kompresi lossless "
        "pada pustaka standar, yaitu `lzma`, `bz2`, "
        "dan `gzip`. Ketiganya menerima masukan berupa byte dan menghasilkan byte terkompresi yang "
        "dapat dikembalikan ke bentuk semula. Pilihan algoritma memengaruhi dua hal yang saling "
        "bertukar, yaitu ukuran hasil dan beban CPU. "
        "Perbandingan ketiganya dirangkum pada Tabel 2.2.",
    ),
    (
        "table",
        {
            "caption": "Tabel 2.2 Algoritma Kompresi yang Tersedia pada Pustaka Standar Python",
            "widths": [1200, 2300, 5200],
            "header": ["Modul", "Tingkat kompresi", "Keterangan pemakaian pada ZipHive"],
            "rows": [
                [
                    "`lzma`",
                    "Preset 1 sampai 9",
                    "Dipakai sebagai algoritma utama dengan preset 6 karena beban "
                    "CPU-nya besar, sehingga percepatan paralel terlihat jelas.",
                ],
                [
                    "`bz2`",
                    "Level 1 sampai 9",
                    "Tersedia sebagai pilihan algoritma melalui opsi "
                    "`--algo` dan dipakai pada pengujian integrasi.",
                ],
                [
                    "`gzip`",
                    "Level 1 sampai 9",
                    "Tersedia sebagai pilihan algoritma dan dipakai pada "
                    "pengujian end-to-end yang menuntut waktu singkat.",
                ],
                [
                    "`sim`",
                    "Tidak berlaku",
                    "Hanya untuk pengujian otomatis, tidak dipakai pada "
                    "eksperimen resmi dan hasilnya dipisahkan dari data laporan.",
                ],
            ],
        },
    ),
    (
        "p",
        "Pemotongan data menjadi chunk 4 MiB dilakukan sebelum kompresi. Pemotongan ini membuat "
        "setiap bagian dapat dikerjakan secara mandiri dan hasilnya dapat diverifikasi satu per "
        "satu, tetapi menurunkan rasio kompresi dibandingkan mengompresi berkas utuh karena setiap "
        "chunk kehilangan konteks dari chunk sebelumnya. Konsekuensi ini diterima agar pembagian "
        "pekerjaan menjadi sederhana dan setiap task memiliki ukuran yang seragam.",
    ),
    ("h2", "2.7 Metrik Evaluasi"),
    (
        "p",
        "Penilaian kinerja memakai metrik yang lazim pada evaluasi sistem paralel. Waktu "
        "penyelesaian pemrosesan berurutan dijadikan dasar, lalu setiap konfigurasi lain "
        "dibandingkan terhadap dasar tersebut. Selain percepatan, diukur pula pemerataan beban dan "
        "lama pemulihan setelah kegagalan. Rumus yang "
        "dipakai implementasi tercantum pada Tabel 2.3.",
    ),
    (
        "table",
        {
            "caption": "Tabel 2.3 Rumus Metrik yang Dipakai pada Pengukuran",
            "widths": [1800, 4200, 2700],
            "header": ["Metrik", "Rumus", "Implementasi"],
            "rows": [
                ["Speedup", "S(n) = T dasar / T(n)", "`calc.speedup`"],
                ["Efficiency", "E(n) = S(n) / n", "`calc.efficiency`"],
                ["Throughput", "(total byte / MiB) / waktu detik", "`calc.throughput_mbs`"],
                [
                    "Imbalance factor",
                    "max(waktu sibuk) / rata-rata waktu sibuk",
                    "`calc.imbalance_factor`",
                ],
                [
                    "Detection latency",
                    "waktu event worker_dead dikurangi waktu Worker dimatikan",
                    "`calc.detection_latency`",
                ],
                [
                    "Recovery time",
                    "waktu task ulangan terakhir selesai dikurangi waktu Worker dimatikan",
                    "`calc.recovery_time`",
                ],
            ],
        },
    ),
    (
        "p",
        "Rujukan buku atau paper untuk rumus speedup, efficiency, dan hukum Amdahl ditandai "
        "PERLU DIISI USER pada `ASSETS.md` karena belum "
        "dapat diverifikasi saat laporan ini disusun. "
        "Angka yang dilaporkan selalu disertai simpangan baku dari tiga ulangan agar pembaca dapat "
        "menilai apakah selisih antar konfigurasi berada di atas sebaran pengukuran.",
    ),
    # ----------------------------------------------------------------- BAB III
    ("h1", ("BAB III", "METODOLOGI")),
    ("h2", "3.1 Gambaran Umum Sistem"),
    (
        "p",
        "ZipHive terdiri atas satu Master dan sembilan Worker. Master memindai folder dataset, "
        "memecah setiap berkas menjadi chunk berukuran "
        "4 MiB, dan menyimpan seluruh task pada tabel "
        "task yang dilindungi satu lock. Setiap Worker "
        "menghubungi Master melalui satu koneksi TCP, "
        "mendaftarkan identitasnya, lalu mengambil task sesuai kapasitas proses yang dimilikinya. "
        "Hasil kompresi dikirim kembali ke Master untuk diperiksa dan ditulis ke folder keluaran.",
    ),
    (
        "p",
        "Master menjalankan beberapa komponen dengan "
        "tanggung jawab terpisah. Bagian server menerima "
        "koneksi dan menjalankan satu thread penanganan untuk setiap Worker. Bagian scheduler "
        "memilih task berikutnya. Bagian monitor memeriksa "
        "tanda hidup Worker dan mengembalikan task "
        "dari Worker yang mati. Bagian collector menulis hasil, menyusun manifest, dan mengakhiri "
        "run. Seluruh kejadian penting dicatat pada berkas "
        "log berformat JSONL dengan cap waktu dari "
        "jam Master.",
    ),
    (
        "p",
        "Worker menjalankan tiga thread, yaitu thread pembaca socket, thread pengirim, dan thread "
        "heartbeat, serta sejumlah proses kompresi. "
        "Fungsi kompresi diletakkan pada tingkat teratas "
        "modul agar aman dijalankan dengan metode `spawn`. Worker tidak saling berkomunikasi "
        "sehingga penambahan Worker tidak menambah jalur komunikasi antarnode. Rancangan topologi "
        "yang dipakai ditunjukkan pada Gambar 3.1.",
    ),
    (
        "placeholder",
        {
            "number": "3.1",
            "isi": (
                "diagram topologi bintang yang memuat satu Master beserta alamat dan port 5050, "
                "sembilan Worker beserta hostname dan alamat "
                "IP masing-masing, arah panah komunikasi "
                "hanya dari setiap Worker ke Master, serta keterangan bahwa seluruh node berjalan "
                "sebagai node virtual pada satu laptop"
            ),
            "cara": (
                "buat diagram dengan draw.io atau Figma memakai daftar node pada Tabel 3.1, ekspor "
                "sebagai PNG dengan lebar penuh halaman, lalu simpan sebagai "
                "reports/img/topologi-10-node.png"
            ),
            "caption": "Gambar 3.1 Topologi Bintang Satu Master dan Sembilan Worker",
            "height_cm": 7,
        },
    ),
    ("h2", "3.2 Topologi dan Konfigurasi Sepuluh Node"),
    (
        "p",
        "Kesepuluh node dijalankan pada satu laptop. Node pertama berperan sebagai Master dan "
        "berjalan langsung pada sistem operasi utama, "
        "sedangkan sembilan node lain berperan sebagai "
        "Worker dan berjalan sebagai container Linux di atas satu mesin virtual. Setiap container "
        "memperoleh hostname dan alamat IP sendiri sehingga dapat diperlakukan sebagai node "
        "terpisah, tetapi seluruhnya berbagi inti prosesor dan memori mesin virtual yang sama. "
        "Spesifikasi setiap node tercantum pada Tabel 3.1.",
    ),
    (
        "table",
        {
            "caption": "Tabel 3.1 Spesifikasi Sepuluh Node Virtual",
            "widths": [700, 900, 1600, 1200, 1500, 1500, 1300],
            "header": [
                "Node",
                "Peran",
                "Hostname",
                "IP",
                "Sistem operasi",
                "CPU dan memori",
                "Python",
            ],
            "rows": [
                [
                    "n1",
                    "Master",
                    "Zhekas-MacBook-Air.local",
                    "192.168.0.105",
                    "macOS 26.6.2",
                    "Apple M1, 8 core logis, 8 GiB",
                    "3.14.4",
                ],
                [
                    "n2",
                    "Worker",
                    "w1",
                    "172.17.0.2",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n3",
                    "Worker",
                    "w2",
                    "172.17.0.3",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n4",
                    "Worker",
                    "w3",
                    "172.17.0.4",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n5",
                    "Worker",
                    "w4",
                    "172.17.0.5",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n6",
                    "Worker",
                    "w5",
                    "172.17.0.6",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n7",
                    "Worker",
                    "w6",
                    "172.17.0.7",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n8",
                    "Worker",
                    "w7",
                    "172.17.0.8",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n9",
                    "Worker",
                    "w8",
                    "172.17.0.9",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
                [
                    "n10",
                    "Worker",
                    "w9",
                    "172.17.0.10",
                    "Alpine Linux 3.20",
                    "6 core logis, 3,8 GiB",
                    "3.12.13",
                ],
            ],
            "mono": [3],
        },
    ),
    (
        "p",
        "Alamat IP pada Tabel 3.1 adalah alamat dinamis yang diberikan oleh jaringan container dan "
        "jaringan rumah, sehingga dapat berubah ketika container dijalankan ulang. Nilai CPU dan "
        "memori pada sembilan Worker mengikuti batas mesin virtual yang dipakai, bukan kapasitas "
        "penuh laptop. Daftar node beserta alamatnya "
        "sebagaimana terlihat pada saat pengambilan bukti "
        "ditunjukkan pada Gambar 3.2.",
    ),
    (
        "image",
        {
            "path": "reports/img/10-node-virtual.png",
            "number": "3.2",
            "isi": (
                "daftar sepuluh container yang berjalan "
                "beserta hostname dan alamat IP masing-masing"
            ),
            "cara": (
                "jalankan docker ps lalu docker inspect pada "
                "setiap container, ambil tangkapan layar "
                "terminal penuh, dan simpan sebagai reports/img/10-node-virtual.png"
            ),
            "caption": "Gambar 3.2 Daftar Sepuluh Node Virtual Beserta Alamat IP",
        },
    ),
    ("h2", "3.3 Mekanisme Kerja Sistem"),
    ("h3", "3.3.1 Pemecahan Tugas dan Model Status"),
    (
        "p",
        "Pemecahan tugas dilakukan dengan memindai folder dataset secara terurut, lalu memotong "
        "setiap berkas per 4 MiB. Berkas kosong dilewati, sedangkan potongan terakhir boleh lebih "
        "kecil daripada ukuran chunk. Setiap task menyimpan "
        "nomor, nama berkas, indeks, posisi awal, "
        "panjang, status, jumlah percobaan, Worker "
        "pemegang, dan cap waktu. Dataset 2048 MiB dengan "
        "delapan berkas menghasilkan 513 task pada setiap run.",
    ),
    (
        "p",
        "Status task mengikuti empat keadaan, yaitu menunggu, terkirim, selesai, dan gagal. Task "
        "berpindah ke keadaan terkirim ketika dikirim ke Worker, dan penghitung percobaan ditambah "
        "pada saat pengiriman agar satu task tidak pernah dicoba melebihi batas percobaan. Task "
        "dinyatakan selesai hanya jika hasil datang dari "
        "Worker yang sedang memegangnya. Hasil dari "
        "Worker lain atau hasil kedua untuk task yang sama diabaikan dan dicatat sebagai kejadian "
        "terlambat atau ganda.",
    ),
    (
        "p",
        "Master membaca isi chunk pada saat pengiriman, bukan pada saat pemecahan, sehingga memori "
        "yang dipakai sebanding dengan jumlah task yang sedang berjalan. Setiap chunk dikirim "
        "bersama nilai SHA-256 sebagai pemeriksa keutuhan "
        "data. Worker menghitung ulang SHA-256 atas "
        "data yang diterima dan mengirimkan nilainya bersama hasil kompresi, sehingga Master dapat "
        "memastikan data yang dikompresi sama dengan data yang dikirim.",
    ),
    ("h3", "3.3.2 Protokol Komunikasi"),
    (
        "p",
        "Komunikasi memakai TCP dengan satu koneksi dua arah untuk setiap Worker. Setiap pesan "
        "dibungkus dalam frame berisi panjang header, panjang payload, header berformat JSON, dan "
        "payload biner. Panjang header dibatasi 64 KiB "
        "dan panjang payload dibatasi 64 MiB, sehingga "
        "penerima dapat menolak frame yang tidak wajar "
        "sebelum membaca isinya. Header selalu memuat "
        "jenis pesan dan versi protokol, dan versi yang berbeda ditolak saat pendaftaran.",
    ),
    (
        "p",
        "Jenis pesan yang dipakai tercantum pada Tabel 3.2. Pesan pertama dari Worker wajib berupa "
        "pendaftaran, dan pesan lain yang datang lebih "
        "dahulu dijawab dengan kesalahan lalu koneksi "
        "ditutup. Setiap pesan yang diterima Master memperbarui tanda terakhir hidup Worker, "
        "sehingga Worker yang sibuk mengerjakan task tetap dianggap hidup asalkan heartbeat tetap "
        "terkirim.",
    ),
    (
        "table",
        {
            "caption": "Tabel 3.2 Jenis Pesan pada Protokol Master-Worker Versi 1",
            "widths": [900, 1900, 3200, 2700],
            "header": ["Arah", "Jenis", "Isi header", "Payload"],
            "rows": [
                ["W ke M", "`REGISTER`", "worker_id, hostname, cores, procs, version", "tidak ada"],
                [
                    "M ke W",
                    "`REGISTER_ACK`",
                    "accepted, reason, heartbeat_interval, algo, level",
                    "tidak ada",
                ],
                ["W ke M", "`REQUEST`", "credits", "tidak ada"],
                [
                    "M ke W",
                    "`TASK`",
                    "task_id, file, index, algo, level, orig_size, sha256",
                    "data chunk asli",
                ],
                [
                    "W ke M",
                    "`RESULT`",
                    "task_id, ok, orig_size, comp_size, sha256_in, compute_sec",
                    "data terkompresi",
                ],
                ["W ke M", "`HEARTBEAT`", "ts, cpu_percent, mem_percent, inflight", "tidak ada"],
                ["M ke W", "`HEARTBEAT_ACK`", "ts", "tidak ada"],
                ["M ke W", "`SHUTDOWN`", "reason", "tidak ada"],
                ["W ke M", "`BYE`", "worker_id", "tidak ada"],
                ["M ke W", "`ERROR`", "code, message", "tidak ada"],
            ],
        },
    ),
    (
        "p",
        "Batas waktu dipakai pada seluruh operasi socket. "
        "Koneksi Worker diulang sampai sepuluh kali "
        "dengan jeda yang meningkat, pembacaan socket "
        "dibatasi 30 detik, interval heartbeat 2 detik, "
        "dan batas tidak ada kabar 6 detik. Batas waktu tersebut membuat koneksi yang terputus "
        "terdeteksi tanpa menggantungkan proses. Urutan pertukaran pesan pada satu run normal "
        "ditunjukkan pada Gambar 3.3.",
    ),
    (
        "placeholder",
        {
            "number": "3.3",
            "isi": (
                "diagram urutan pesan dari REGISTER, REGISTER_ACK, REQUEST, TASK, RESULT, "
                "HEARTBEAT, hingga SHUTDOWN dan BYE antara "
                "Master dan Worker, termasuk penanda saat "
                "Master memulai penghitungan waktu"
            ),
            "cara": (
                "ekspor diagram urutan pada FLOW.md bagian 1 memakai Mermaid Live Editor atau "
                "draw.io, simpan sebagai PNG lebar penuh halaman di reports/img/urutan-pesan.png"
            ),
            "caption": "Gambar 3.3 Urutan Pertukaran Pesan pada Satu Run Normal",
            "height_cm": 7,
        },
    ),
    ("h3", "3.3.3 Penjadwalan Tugas"),
    (
        "p",
        "Penjadwalan dinamis menjadi cara utama pada sistem ini. Setelah pendaftaran diterima, "
        "Worker mengirim permintaan sejumlah credit sesuai jumlah proses yang dimilikinya. Master "
        "menyimpan saldo credit setiap Worker dan mengirim "
        "satu task untuk setiap credit yang masih "
        "tersedia. Setiap kali satu task selesai, Worker mengirim permintaan satu credit baru, "
        "sehingga Worker yang menyelesaikan task lebih cepat akan memperoleh task berikutnya lebih "
        "awal.",
    ),
    (
        "p",
        "Penjadwalan statis disediakan sebagai pembanding. Pada cara ini seluruh task dibagi rata "
        "secara round-robin saat pekerjaan dimulai, dan "
        "tidak ada penyesuaian setelahnya. Kedua cara "
        "memakai aturan pengurutan yang sama, yaitu task berukuran terbesar dikirim lebih dahulu, "
        "agar task besar tidak tertinggal di akhir dan memperpanjang waktu penyelesaian.",
    ),
    (
        "p",
        "Untuk menguji keadilan pembagian, satu Worker dapat diberi perlambatan tetap pada setiap "
        "task. Pada eksperimen perbandingan, Worker kesembilan diberi perlambatan 0,25 detik per "
        "task sehingga menjadi Worker paling lambat. Beban setiap Worker kemudian dibandingkan "
        "melalui waktu sibuk dan imbalance factor, yaitu rasio waktu sibuk terbesar terhadap "
        "rata-rata waktu sibuk seluruh Worker.",
    ),
    ("h3", "3.3.4 Deteksi Kegagalan dan Pemulihan"),
    (
        "p",
        "Kegagalan Worker terdeteksi melalui dua jalur. Koneksi socket yang tertutup langsung "
        "terbaca sebagai akhir aliran data, sehingga Worker dapat ditandai mati segera setelah "
        "prosesnya berhenti. Jalur kedua adalah pemeriksaan berkala oleh thread monitor, yang "
        "menandai Worker mati apabila tidak ada pesan "
        "apa pun melebihi batas waktu yang ditetapkan.",
    ),
    (
        "p",
        "Setelah Worker ditandai mati, seluruh task yang tercatat padanya dikembalikan ke antrean "
        "dengan penghitung percobaan ditambah satu, lalu diambil Worker lain yang masih hidup. "
        "Kejadian ini dicatat pada log sebagai tiga peristiwa berurutan, yaitu penandaan Worker "
        "mati, pengembalian task, dan penyelesaian task "
        "oleh Worker baru. Batas percobaan ditetapkan "
        "tiga kali, dan task yang melewati batas tersebut dicatat gagal beserta alasannya.",
    ),
    (
        "p",
        "Lama deteksi dihitung dari waktu Worker dimatikan sampai waktu Master menandainya mati, "
        "sedangkan lama pemulihan dihitung dari waktu "
        "Worker dimatikan sampai task ulangan terakhir "
        "selesai dikerjakan Worker lain. Kedua nilai diambil dari log kejadian pada setiap run, "
        "bukan dari perkiraan.",
    ),
    ("h2", "3.4 Rancangan Eksperimen"),
    (
        "p",
        "Eksperimen disusun mengikuti kebutuhan soal, yaitu pengukuran pemrosesan berurutan, "
        "pemrosesan paralel pada satu mesin, pemrosesan terdistribusi, penyeimbangan beban, "
        "ketahanan terhadap kegagalan, dan skalabilitas jumlah Worker. Setiap konfigurasi diulang "
        "tiga kali dengan jeda 30 detik, dan urutan ulangan diletakkan di luar urutan konfigurasi "
        "agar pergeseran beban mesin tidak membiaskan satu konfigurasi tertentu. Rancangan lengkap "
        "tercantum pada Tabel 3.3.",
    ),
    (
        "table",
        {
            "caption": "Tabel 3.3 Rancangan Eksperimen E1 sampai E7",
            "widths": [700, 3400, 4600],
            "header": ["ID", "Konfigurasi", "Yang dibandingkan"],
            "rows": [
                [
                    "E1",
                    "Satu proses pada satu mesin",
                    "Waktu dasar sebagai pembanding seluruh konfigurasi lain.",
                ],
                [
                    "E2",
                    "Pemrosesan paralel satu mesin dengan 1, 2, 4, dan 8 proses",
                    "Waktu, speedup, dan efficiency terhadap jumlah proses.",
                ],
                [
                    "E3",
                    "Terdistribusi satu Master dan sembilan Worker",
                    "Waktu, speedup, efficiency, dan imbalance factor.",
                ],
                [
                    "E4",
                    "Penjadwalan statis dan dinamis dengan satu Worker diperlambat",
                    "Makespan, imbalance factor, dan waktu sibuk setiap Worker.",
                ],
                [
                    "E5",
                    "Satu dan tiga Worker dimatikan pada sekitar 50 persen progres",
                    "Lama deteksi, lama pemulihan, jumlah task ulangan, dan status verifikasi.",
                ],
                [
                    "E6",
                    "Jumlah Worker 1, 2, 4, 6, dan 9",
                    "Skalabilitas waktu, speedup, dan efficiency terhadap jumlah Worker.",
                ],
                [
                    "E7",
                    "Ukuran chunk 1, 4, dan 16 MiB (opsional)",
                    "Waktu, rasio kompresi, dan overhead jaringan. Tidak "
                    "dijalankan pada pelaksanaan ini sehingga tidak memiliki data.",
                ],
            ],
        },
    ),
    (
        "p",
        "Seluruh konfigurasi memakai parameter yang sama "
        "agar perbandingan sahih. Parameter tersebut "
        "mencakup dataset, algoritma, ukuran chunk, jumlah pengulangan berkas, jumlah ulangan, dan "
        "nilai batas waktu heartbeat. Nilai yang dipakai tercantum pada Tabel 3.4.",
    ),
    (
        "table",
        {
            "caption": "Tabel 3.4 Parameter Tetap pada Seluruh Eksperimen",
            "widths": [2600, 6100],
            "header": ["Parameter", "Nilai"],
            "rows": [
                ["Dataset", "Sintetis data/bench, 2048 MiB, 8 berkas, seed 20261122"],
                ["Algoritma dan level", "lzma preset 6"],
                ["Ukuran chunk", "4 MiB"],
                ["Jumlah pengulangan berkas", "1"],
                ["Jumlah task per run", "513"],
                ["Ulangan", "3 kali per konfigurasi, jeda 30 detik"],
                ["Worker terdistribusi", "9 Worker, satu proses kompresi per Worker"],
                ["Heartbeat", "interval 2,0 detik, batas 6,0 detik, batas percobaan 3"],
            ],
        },
    ),
    (
        "p",
        "Eksperimen E7 ditandai opsional pada rancangan awal dan tidak dijalankan pada pelaksanaan "
        "ini. Bagian hasil karena itu tidak memuat data "
        "E7, dan pembahasan mengenai pengaruh ukuran "
        "chunk terhadap overhead jaringan dinyatakan sebagai hal yang belum diukur.",
    ),
    ("h2", "3.5 Prosedur Pengukuran dan Validasi"),
    (
        "p",
        "Waktu mulai dicatat saat task pertama dikirim, yaitu setelah seluruh Worker yang diminta "
        "terdaftar, dan waktu selesai dicatat saat hasil terakhir ditulis. Pengukuran dipisahkan "
        "antara waktu kompresi di Worker dan perkiraan waktu pengiriman, sehingga sumber penundaan "
        "dapat ditelusuri. Penggunaan CPU dan memori "
        "dicatat setiap detik melalui psutil, sedangkan "
        "setiap kejadian penting dicatat pada log JSONL.",
    ),
    (
        "p",
        "Setiap run disimpan pada folder tersendiri yang memuat manifest, metrik, log kejadian, "
        "berkas lingkungan, dan berkas spesifikasi run. Setelah run selesai, hasil kompresi "
        "didekompresi, digabungkan, lalu dibandingkan dengan berkas asli melalui SHA-256. Keluaran "
        "verifikasi disimpan sebagai berkas log, dan "
        "seluruh berkas hasil diperiksa ulang oleh alat "
        "validasi yang memastikan tidak ada run yang "
        "tidak lengkap atau memakai algoritma simulasi.",
    ),
    (
        "p",
        "Alat validasi menolak hasil yang tidak memenuhi "
        "syarat, yaitu metadata yang tidak lengkap, "
        "verifikasi yang tidak berstatus berhasil, jumlah ulangan kurang dari tiga, serta hasil "
        "algoritma `sim` yang hanya dipakai untuk "
        "pengujian. Keluaran alat validasi pada data resmi "
        "menjadi bukti bahwa seluruh angka yang dilaporkan berasal dari run yang benar-benar "
        "dijalankan.",
    ),
    # ------------------------------------------------------------------ BAB IV
    ("h1", ("BAB IV", "HASIL DAN PEMBAHASAN")),
    ("h2", "4.1 Implementasi Sistem"),
    (
        "p",
        "Sistem diimplementasikan dengan Python 3.11 atau lebih baru dan hanya memakai pustaka "
        "standar ditambah psutil untuk pengukuran sumber "
        "daya. Kode dibagi menjadi modul inti, modul "
        "sisi Master, modul sisi Worker, modul metrik, "
        "harness benchmark, dan alat bantu. Pembagian "
        "modul beserta tanggung jawabnya tercantum pada Tabel 4.1.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.1 Modul Utama dan Tanggung Jawabnya",
            "widths": [2500, 6200],
            "header": ["Modul", "Tanggung jawab"],
            "rows": [
                [
                    "`protocol`",
                    "Membentuk dan membaca frame pesan, memvalidasi versi dan batas ukuran.",
                ],
                ["`net`", "Operasi socket dengan batas waktu, pengiriman dan penerimaan utuh."],
                ["`chunker`", "Memecah berkas menjadi chunk dan menyusun daftar task."],
                [
                    "`compressor`",
                    "Mengompresi dan mendekompresi data memakai lzma, bz2, atau gzip.",
                ],
                ["`manifest`", "Menulis manifes hasil beserta ukuran dan SHA-256 setiap chunk."],
                [
                    "`master.server`",
                    "Menerima koneksi, menjalankan thread per Worker, dan mengatur barrier.",
                ],
                [
                    "`master.scheduler`",
                    "Memilih task berikutnya untuk penjadwalan statis atau dinamis.",
                ],
                [
                    "`master.monitor`",
                    "Memeriksa heartbeat, menandai Worker mati, dan mengembalikan task.",
                ],
                ["`master.collector`", "Menulis hasil, menyusun manifest, dan mengakhiri run."],
                [
                    "`worker.client`",
                    "Mendaftar ke Master, menerima task, mengirim hasil, dan mengatur credit.",
                ],
                [
                    "`worker.executor`",
                    "Menjalankan Pool proses dan fungsi kompresi yang aman untuk spawn.",
                ],
                [
                    "`worker.heartbeat`",
                    "Mengirim heartbeat berisi CPU, memori, dan jumlah task berjalan.",
                ],
                [
                    "`metrics.calc`",
                    "Menghitung speedup, efficiency, throughput, dan imbalance factor.",
                ],
                ["`bench.runner`", "Menjalankan eksperimen berulang dan menulis ringkasan hasil."],
            ],
        },
    ),
    (
        "p",
        "Menjalankan sistem memerlukan dua perintah terpisah, yaitu satu perintah untuk Master dan "
        "satu perintah untuk setiap Worker. Perintah yang dipakai pada pelaksanaan ini adalah "
        "sebagai berikut:",
    ),
    (
        "code",
        [
            "# 1. Master di host, menunggu sembilan Worker",
            "PYTHONPATH=src python -m pcomp.master --input data/bench --out output/run1 \\",
            "  --expect-workers 9 --scheduler dynamic --host 0.0.0.0 --port 5050",
            "",
            "# 2. Satu Worker di dalam container (diulang untuk w1 sampai w9)",
            "python3 -m pcomp.worker --master host.docker.internal:5050 --id w1 --procs 1",
            "",
            "# 3. Verifikasi hasil setelah run selesai",
            "python -m pcomp.tools.verify --manifest output/run1/manifest.json",
        ],
    ),
    (
        "p",
        "Master mencetak ringkasan jumlah task dan status akhir setelah seluruh task selesai, "
        "sedangkan setiap Worker mencetak identitasnya saat pendaftaran diterima. Tampilan Master "
        "yang sedang menunggu dan kemudian memproses "
        "task ditunjukkan pada Gambar 4.1, dan tampilan "
        "salah satu Worker ditunjukkan pada Gambar 4.2.",
    ),
    (
        "image",
        {
            "path": "reports/img/master-terminal.png",
            "number": "4.1",
            "isi": (
                "terminal Master yang memperlihatkan banner kelompok, jumlah Worker terdaftar, "
                "progres task, dan ringkasan akhir run"
            ),
            "cara": (
                "jalankan Master pada satu jendela terminal, ambil tangkapan layar penuh saat run "
                "berjalan dan saat run selesai, simpan sebagai reports/img/master-terminal.png"
            ),
            "caption": "Gambar 4.1 Keluaran Master Selama Satu Run Terdistribusi",
        },
    ),
    (
        "image",
        {
            "path": "reports/img/worker-terminal.png",
            "number": "4.2",
            "isi": (
                "terminal salah satu Worker yang memperlihatkan identitas Worker, proses kompresi "
                "yang berjalan, dan pengiriman hasil ke Master"
            ),
            "cara": (
                "tampilkan log container salah satu Worker dengan docker logs, ambil tangkapan "
                "layar terminal penuh, simpan sebagai reports/img/worker-terminal.png"
            ),
            "caption": "Gambar 4.2 Keluaran Salah Satu Worker Selama Satu Run Terdistribusi",
        },
    ),
    ("h2", "4.2 Pemrosesan Berurutan dan Paralel Satu Mesin"),
    (
        "p",
        "Pemrosesan berurutan pada satu proses menjadi dasar pembanding seluruh konfigurasi lain. "
        "Pada dataset 2048 MiB dengan 513 task, pemrosesan "
        "berurutan memerlukan waktu 143,56 ± 6,79 "
        "detik dengan throughput 14,29 ± 0,66 MB/s dan penggunaan CPU sebesar 99,69 ± 0,06 persen. "
        "Nilai CPU tersebut menunjukkan bahwa pemrosesan berurutan memang terikat pada satu inti "
        "prosesor. Ringkasan hasil tersebut tercantum pada Tabel 4.2.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.2 Hasil Eksperimen E1 Pemrosesan Berurutan",
            "widths": [3200, 5500],
            "header": ["Metrik", "Nilai"],
            "rows": [
                ["Waktu penyelesaian", "143,56 ± 6,79 detik"],
                ["Throughput", "14,29 ± 0,66 MB/s"],
                ["Jumlah task", "513"],
                ["Rasio kompresi", "2,632"],
                ["Penggunaan CPU", "99,69 ± 0,06 persen"],
                ["Ulangan", "138,26 detik, 141,20 detik, dan 151,21 detik"],
            ],
        },
    ),
    (
        "p",
        "Sebaran tiga ulangan pada E1 sebesar 6,79 detik atau sekitar 4,7 persen dari rata-rata. "
        "Nilai ini dipakai sebagai acuan pembacaan seluruh eksperimen lain, yaitu selisih antar "
        "konfigurasi yang lebih kecil daripada sebaran "
        "tersebut tidak ditafsirkan sebagai perbedaan "
        "yang nyata. Pada konfigurasi p = 1 dari E2, waktu yang tercatat 152,46 ± 3,80 detik atau "
        "sekitar 6 persen lebih lama daripada E1 karena "
        "harness menyiapkan dataset, mencatat sumber "
        "daya setiap detik, dan menjalankan Worker sebagai proses terpisah.",
    ),
    (
        "p",
        "Penambahan proses pada satu mesin menurunkan waktu penyelesaian, tetapi efisiensinya "
        "menurun seiring bertambahnya proses. Waktu turun "
        "dari 152,46 detik pada p = 1 menjadi 42,31 "
        "detik pada p = 8, sedangkan efficiency turun dari 1,010 menjadi 0,463. Hasil lengkap E2 "
        "tercantum pada Tabel 4.3.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.3 Hasil Eksperimen E2 Pemrosesan Paralel Satu Mesin",
            "widths": [700, 2000, 2000, 2000, 2000],
            "header": ["p", "Waktu (detik)", "Speedup", "Efficiency", "Throughput (MB/s)"],
            "rows": [
                ["1", "152,46 ± 3,80", "1,010 ± 0,025", "1,010 ± 0,025", "13,44 ± 0,34"],
                ["2", "88,42 ± 2,09", "1,742 ± 0,041", "0,871 ± 0,021", "23,17 ± 0,55"],
                ["4", "51,48 ± 2,39", "2,995 ± 0,138", "0,749 ± 0,034", "39,84 ± 1,83"],
                ["8", "42,31 ± 6,71", "3,708 ± 0,646", "0,463 ± 0,081", "49,31 ± 8,59"],
            ],
        },
    ),
    (
        "p",
        "Penurunan efisiensi pada jumlah proses yang besar bukan disebabkan komunikasi jaringan, "
        "karena seluruh proses berada pada satu mesin. Penyebab utamanya adalah perebutan sumber "
        "daya bersama, yaitu delapan proses `lzma` preset 6 memakai memori besar dan bersaing pada "
        "bandwidth memori serta cache, sementara harness juga mencatat penggunaan sumber daya pada "
        "satu inti. Konfigurasi p = 8 juga memiliki sebaran terbesar dengan simpangan baku 6,71 "
        "detik atau 16 persen dari rata-rata, sehingga "
        "nilainya dibaca sebagai batas praktis, bukan "
        "angka yang presisi.",
    ),
    (
        "p",
        "Hubungan antara jumlah proses dan percepatan yang diperoleh ditunjukkan pada Gambar 4.3, "
        "hubungan antara jumlah proses dan throughput ditunjukkan pada Gambar 4.4, dan penurunan "
        "efisiensi ditunjukkan pada Gambar 4.5.",
    ),
    (
        "image",
        {
            "path": "results/figures/speedup.png",
            "number": "4.3",
            "isi": "grafik speedup terhadap jumlah proses dan jumlah Worker",
            "cara": "jalankan python -m pcomp.bench.report dari "
            "results/summary.csv lalu salin results/figures/speedup.png",
            "caption": "Gambar 4.3 Speedup terhadap Jumlah Proses dan Jumlah Worker",
        },
    ),
    (
        "image",
        {
            "path": "results/figures/throughput.png",
            "number": "4.4",
            "isi": "grafik throughput dalam MB/s untuk setiap konfigurasi",
            "cara": "jalankan python -m pcomp.bench.report dari "
            "results/summary.csv lalu salin results/figures/throughput.png",
            "caption": "Gambar 4.4 Throughput Setiap Konfigurasi",
        },
    ),
    (
        "image",
        {
            "path": "results/figures/efficiency.png",
            "number": "4.5",
            "isi": "grafik efficiency terhadap jumlah proses dan jumlah Worker",
            "cara": "jalankan python -m pcomp.bench.report dari "
            "results/summary.csv lalu salin results/figures/efficiency.png",
            "caption": "Gambar 4.5 Efficiency terhadap Jumlah Proses dan Jumlah Worker",
        },
    ),
    ("h2", "4.3 Kinerja Sistem Terdistribusi"),
    (
        "p",
        "Konfigurasi terdistribusi dengan satu Master dan sembilan Worker menyelesaikan pekerjaan "
        "dalam 62,31 ± 5,84 detik atau sekitar 2,301 kali "
        "lebih cepat daripada pemrosesan berurutan. "
        "Dibandingkan satu Worker container yang memerlukan "
        "247,15 detik, konfigurasi sembilan Worker "
        "sekitar 3,97 kali lebih cepat. Kedua angka "
        "berbeda karena satu Worker container lebih lambat "
        "daripada pemrosesan berurutan pada mesin yang sama. Hasil lengkap E3 tercantum pada Tabel "
        "4.4.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.4 Hasil Eksperimen E3 Satu Master dan Sembilan Worker",
            "widths": [4200, 4500],
            "header": ["Metrik", "Nilai"],
            "rows": [
                ["Waktu penyelesaian", "62,31 ± 5,84 detik"],
                ["Speedup terhadap E1", "2,301 ± 0,205"],
                ["Speedup terhadap satu Worker container", "3,97"],
                ["Efficiency terhadap sembilan Worker", "0,256 ± 0,023"],
                ["Imbalance factor", "1,026 ± 0,020"],
                ["Penggunaan CPU Master", "8,10 ± 0,26 persen"],
                ["Throughput", "33,05 ± 2,94 MB/s"],
            ],
        },
    ),
    (
        "p",
        "Imbalance factor sebesar 1,026 menunjukkan bahwa penjadwalan dinamis membagi task hampir "
        "merata, karena selisih waktu sibuk antar Worker hanya sekitar 2,6 persen. Penggunaan CPU "
        "Master hanya 8,10 persen, sehingga Master tidak terikat oleh CPU. Yang membatasi kinerja "
        "adalah penulisan hasil dan penghitungan hash di "
        "Master yang berjalan berurutan untuk setiap "
        "chunk yang masuk, ditambah sembilan Worker yang berbagi enam inti prosesor mesin virtual.",
    ),
    (
        "p",
        "Tiga ulangan E3 menghasilkan 58,53 detik, 69,03 detik, dan 59,37 detik. Nilai 69,03 detik "
        "merupakan pencilan karena beban mesin meningkat sesaat, dan imbalance factor pada run "
        "tersebut juga naik menjadi 1,048. Sebaran ini "
        "tetap lebih kecil daripada selisih antara E3 "
        "dan konfigurasi lain yang dibandingkan, sehingga kesimpulan perbandingan tidak berubah.",
    ),
    ("h2", "4.4 Efektivitas Penjadwalan Dinamis"),
    (
        "p",
        "Pada eksperimen perbandingan, Worker kesembilan diberi perlambatan 0,25 detik per task "
        "sehingga menjadi Worker paling lambat. Penjadwalan statis menghasilkan makespan 66,78 ± "
        "1,30 detik dengan imbalance factor 1,222, sedangkan penjadwalan dinamis menghasilkan "
        "makespan 57,16 ± 0,88 detik dengan imbalance factor 1,038. Makespan penjadwalan dinamis "
        "14,4 persen lebih pendek. Hasil tersebut tercantum pada Tabel 4.5.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.5 Perbandingan Penjadwalan Statis dan Dinamis pada E4",
            "widths": [2200, 2300, 2300, 1900],
            "header": ["Scheduler", "Makespan (detik)", "Imbalance factor", "Throughput (MB/s)"],
            "rows": [
                ["static", "66,78 ± 1,30", "1,222 ± 0,014", "30,67 ± 0,60"],
                ["dynamic", "57,16 ± 0,88", "1,038 ± 0,007", "35,83 ± 0,55"],
            ],
        },
    ),
    (
        "p",
        "Perbedaan tersebut terlihat jelas pada waktu "
        "sibuk setiap Worker. Pada penjadwalan statis, "
        "setiap Worker menerima tepat 57 task tanpa memperhatikan kecepatannya, sehingga Worker "
        "lambat menjadi penentu akhir dengan waktu sibuk "
        "60,7 detik dibanding 46,7 sampai 49,7 detik "
        "pada Worker lain. Pada penjadwalan dinamis, "
        "Worker lambat menerima lebih sedikit task, yaitu "
        "rata-rata 40,3 task berbanding sekitar 57 sampai 62 task pada Worker lain, sehingga waktu "
        "sibuknya turun menjadi 50,7 detik. Rincian beban tercantum pada Tabel 4.6.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.6 Waktu Sibuk Setiap Worker pada E4 (detik)",
            "widths": [3400, 2650, 2650],
            "header": ["Worker", "Penjadwalan statis", "Penjadwalan dinamis"],
            "rows": [
                ["w1", "48,2", "48,3"],
                ["w2", "49,2", "48,3"],
                ["w3", "48,5", "48,7"],
                ["w4", "47,9", "48,4"],
                ["w5", "47,8", "48,6"],
                ["w6", "46,7", "48,9"],
                ["w7", "48,4", "48,9"],
                ["w8", "49,7", "48,6"],
                ["w9 (diperlambat)", "60,7", "50,7"],
            ],
        },
    ),
    (
        "p",
        "Kedua konfigurasi memiliki simpangan baku kecil, yaitu 1,30 dan 0,88 detik, jauh di bawah "
        "selisih makespan sebesar 9,62 detik. Perbedaan "
        "tersebut karena itu dapat dinyatakan sebagai "
        "perbedaan yang nyata dan bukan kebetulan pengukuran. Sebaran beban setiap Worker pada "
        "penjadwalan dinamis ditunjukkan pada Gambar 4.6.",
    ),
    (
        "image",
        {
            "path": "results/figures/worker_load.png",
            "number": "4.6",
            "isi": "grafik batang waktu sibuk setiap Worker untuk "
            "konfigurasi terdistribusi yang dibandingkan",
            "cara": "jalankan python -m pcomp.bench.report dari "
            "results/summary.csv lalu salin results/figures/worker_load.png",
            "caption": "Gambar 4.6 Sebaran Waktu Sibuk Setiap Worker",
        },
    ),
    ("h2", "4.5 Ketahanan terhadap Kegagalan Worker"),
    (
        "p",
        "Pengujian fault tolerance dilakukan dengan mematikan satu Worker dan, pada skenario lain, "
        "tiga Worker pada sekitar 50 persen progres. Pada skenario satu Worker mati, run selesai "
        "dalam 66,27 ± 8,27 detik dengan lama deteksi "
        "0,26 ± 0,09 detik, lama pemulihan 1,37 ± 0,70 "
        "detik, dan satu task diulang. Pada skenario tiga Worker mati, run selesai dalam 108,21 ± "
        "3,82 detik dengan lama deteksi 0,38 ± 0,11 detik, "
        "lama pemulihan 5,60 ± 5,84 detik, dan 2,67 "
        "task diulang. Hasil tersebut tercantum pada Tabel 4.7.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.7 Hasil Eksperimen E5 Ketahanan terhadap Kegagalan Worker",
            "widths": [2600, 1800, 2300, 2000],
            "header": [
                "Skenario",
                "Makespan (detik)",
                "Lama deteksi (detik)",
                "Lama pemulihan (detik)",
            ],
            "rows": [
                ["Satu Worker mati", "66,27 ± 8,27", "0,26 ± 0,09", "1,37 ± 0,70"],
                ["Tiga Worker mati", "108,21 ± 3,82", "0,38 ± 0,11", "5,60 ± 5,84"],
            ],
        },
    ),
    (
        "p",
        "Setiap run pada skenario ini berakhir dengan status verifikasi berhasil, artinya hasil "
        "dekompresi tetap identik dengan data asli meskipun Worker dimatikan di tengah run. Log "
        "kejadian memuat tiga peristiwa berurutan, yaitu penandaan bahwa kegagalan disuntikkan, "
        "penandaan Worker mati, dan pengembalian task ke antrean. Lama deteksi di bawah 0,5 detik "
        "terjadi karena Master memeriksa heartbeat setiap 0,2 detik dan koneksi Worker yang mati "
        "langsung terlihat tertutup, tanpa menunggu batas 6 detik. Bukti Worker yang dimatikan "
        "ditunjukkan pada Gambar 4.7.",
    ),
    (
        "image",
        {
            "path": "reports/img/e5-worker-mati.png",
            "number": "4.7",
            "isi": (
                "terminal yang memperlihatkan satu container Worker berhenti dan event worker_dead "
                "serta task_requeued pada sisi Master"
            ),
            "cara": (
                "jalankan run E5, hentikan satu container dengan docker kill setelah docker ps "
                "menunjukkan semua container berjalan, lalu "
                "ambil tangkapan layar terminal penuh dan "
                "simpan sebagai reports/img/e5-worker-mati.png"
            ),
            "caption": "Gambar 4.7 Bukti Worker Dimatikan dan Task Dikembalikan ke Antrean",
        },
    ),
    (
        "p",
        "Skenario satu Worker mati hampir tidak menambah waktu dibandingkan E3, yaitu 66,27 detik "
        "berbanding 62,31 detik, karena delapan Worker yang tersisa menyerap task yang dilepas. "
        "Skenario tiga Worker mati menambah waktu menjadi 108,21 detik karena kapasitas turun dari "
        "sembilan menjadi enam Worker, tepat pada batas enam inti prosesor yang tersedia. Lama "
        "pemulihan pada skenario tiga Worker memiliki sebaran besar karena satu ulangan memerlukan "
        "12,34 detik akibat task yang diulang berupa "
        "chunk data acak yang paling lama dikompresi dan "
        "harus dimulai dari awal. Garis waktu pemulihan ditunjukkan pada Gambar 4.8.",
    ),
    (
        "image",
        {
            "path": "results/figures/recovery_timeline.png",
            "number": "4.8",
            "isi": "garis waktu kejadian pemulihan dari Worker mati sampai task ulangan selesai",
            "cara": "jalankan python -m pcomp.bench.report dari results/summary.csv "
            "lalu salin results/figures/recovery_timeline.png",
            "caption": "Gambar 4.8 Garis Waktu Pemulihan Setelah Worker Dimatikan",
        },
    ),
    ("h2", "4.6 Skalabilitas Jumlah Worker"),
    (
        "p",
        "Pengujian skalabilitas membandingkan jumlah Worker 1, 2, 4, 6, dan 9. Waktu menurun dari "
        "247,15 detik pada satu Worker menjadi 79,28 detik pada enam Worker, tetapi tidak berubah "
        "berarti ketika jumlah Worker dinaikkan menjadi sembilan, yaitu 79,32 detik. Speedup "
        "terhadap satu Worker naik dari 1,978 pada dua Worker menjadi 3,487 pada sembilan Worker, "
        "sedangkan efficiency turun dari 0,722 menjadi "
        "0,283. Hasil lengkap tercantum pada Tabel 4.8.",
    ),
    (
        "table",
        {
            "caption": "Tabel 4.8 Hasil Eksperimen E6 Skalabilitas Jumlah Worker",
            "widths": [900, 2000, 2000, 1900, 1900],
            "header": ["Worker", "Waktu (detik)", "Speedup", "Efficiency", "Throughput (MB/s)"],
            "rows": [
                ["1", "247,15 ± 27,82", "1,000", "0,805", "8,36 ± 0,99"],
                ["2", "140,50 ± 30,26", "1,978 ± 0,392", "0,722 ± 0,143", "15,00 ± 2,97"],
                ["4", "98,67 ± 22,00", "2,835 ± 0,663", "0,517 ± 0,121", "21,50 ± 5,03"],
                ["6", "79,28 ± 12,81", "3,473 ± 0,619", "0,423 ± 0,075", "26,34 ± 4,69"],
                ["9", "79,32 ± 14,09", "3,487 ± 0,690", "0,283 ± 0,056", "26,44 ± 5,23"],
            ],
        },
    ),
    (
        "p",
        "Dua hal menonjol pada hasil ini. Pertama, satu Worker container memerlukan 247,15 detik "
        "atau lebih lambat daripada pemrosesan berurutan pada mesin yang sama, sehingga speedup "
        "terhadap E1 untuk satu Worker hanya 0,805. Kedua, waktu enam Worker dan sembilan Worker "
        "praktis sama karena mesin virtual hanya diberi enam inti prosesor. Kurva waktu terhadap "
        "jumlah Worker ditunjukkan pada Gambar 4.9, dan "
        "kurva tersebut mendatar setelah enam Worker.",
    ),
    (
        "image",
        {
            "path": "results/figures/time_vs_workers.png",
            "number": "4.9",
            "isi": "grafik waktu penyelesaian terhadap jumlah Worker",
            "cara": "jalankan python -m pcomp.bench.report dari results/summary.csv "
            "lalu salin results/figures/time_vs_workers.png",
            "caption": "Gambar 4.9 Waktu Penyelesaian terhadap Jumlah Worker",
        },
    ),
    (
        "p",
        "Sebaran waktu pada E6 adalah yang terbesar, "
        "dengan simpangan baku sampai 30 detik pada dua "
        "Worker. Penyebabnya terlihat dari urutan run, yaitu ulangan pertama selalu paling lambat "
        "dan ulangan ketiga paling cepat karena mesin "
        "masih menyelesaikan pekerjaan latar pada awal "
        "pengukuran. Karena setiap ulangan memuat kelima "
        "konfigurasi secara berurutan, perbandingan "
        "antar jumlah Worker di dalam satu ulangan tetap sahih, sedangkan nilai absolutnya perlu "
        "dibaca bersama simpangan baku tersebut.",
    ),
    ("h2", "4.7 Pembahasan Penyebab Percepatan di Bawah Jumlah Proses"),
    (
        "p",
        "Percepatan yang diperoleh selalu lebih kecil daripada jumlah proses atau Worker yang "
        "dipakai. Berdasarkan hasil kelima eksperimen, "
        "terdapat lima penyebab yang dapat ditunjukkan "
        "oleh data:",
    ),
    (
        "bullets",
        [
            "Worker container lebih lambat daripada proses "
            "native. Kompresi dijalankan pada Pool di "
            "dalam container sehingga data melewati lapisan "
            "container dan mesin virtual. Satu Worker "
            "container memerlukan 247,15 detik untuk 513 task, sedangkan pemrosesan berurutan pada "
            "mesin yang sama hanya 143,56 detik, atau sekitar 1,72 kali lebih lambat per task.",
            "Jumlah inti prosesor mesin virtual lebih kecil daripada jumlah Worker. Mesin virtual "
            "diberi enam inti untuk sembilan Worker, dan buktinya adalah waktu enam Worker serta "
            "sembilan Worker yang sama, yaitu 79,28 dan 79,32 detik.",
            "Pemrosesan di Master bersifat berurutan. Master menerima, memverifikasi hash, dan "
            "menulis setiap chunk satu per satu. Throughput "
            "tertinggi yang tercatat sekitar 36 MB/s "
            "pada penjadwalan dinamis E4, sementara uji "
            "koneksi container ke host mencapai 353 MB/s, "
            "sehingga batasnya berada pada pemrosesan dan penulisan hasil, bukan pada jaringan.",
            "Overhead kerangka pengukuran. Harness mencatat "
            "penggunaan sumber daya setiap detik dan "
            "menghitung hash pada setiap task. Perbandingan "
            "E1 sebesar 143,56 detik dengan E2 p = 1 "
            "sebesar 152,46 detik menunjukkan tambahan sekitar 6 persen.",
            "Batas sumber daya bersama pada pemrosesan paralel satu mesin. Efficiency E2 turun "
            "menjadi 0,463 pada p = 8 karena delapan proses "
            "lzma bersaing pada bandwidth memori dan "
            "cache, bukan karena komunikasi jaringan.",
        ],
    ),
    (
        "p",
        "Penggunaan CPU dan memori selama run ditunjukkan pada Gambar 4.10. Kolom penggunaan CPU "
        "Worker tidak dipakai pada pembahasan karena "
        "sampler membaca proses utama Worker, sedangkan "
        "kompresi berjalan pada proses anak, sehingga nilai yang terbaca hampir selalu nol dengan "
        "lonjakan yang tidak wajar. Analisis beban Worker karena itu memakai waktu sibuk setiap "
        "Worker, sedangkan nilai penggunaan CPU Master "
        "tetap sahih karena Master mengerjakan sendiri "
        "seluruh pemrosesan chunk.",
    ),
    (
        "image",
        {
            "path": "results/figures/cpu_mem.png",
            "number": "4.10",
            "isi": "grafik penggunaan CPU dan memori selama run untuk peran Master dan Worker",
            "cara": "jalankan python -m pcomp.bench.report dari "
            "results/summary.csv lalu salin results/figures/cpu_mem.png",
            "caption": "Gambar 4.10 Penggunaan CPU dan Memori Selama Run",
        },
    ),
    ("h2", "4.8 Keterbatasan Pengukuran"),
    (
        "p",
        "Beberapa keterbatasan perlu disampaikan agar angka pada laporan ini dibaca sesuai "
        "konteksnya:",
    ),
    (
        "bullets",
        [
            "Seluruh node berada pada satu mesin sesuai ADR-015, sehingga angka tidak mewakili "
            "jaringan laboratorium dengan perangkat terpisah. Yang terukur adalah overhead "
            "virtualisasi dan pembagian inti prosesor, bukan latensi jaringan fisik.",
            "Beban latar sistem operasi tidak dapat "
            "dikendalikan penuh. Aplikasi berat sudah ditutup "
            "sebelum pengukuran, tetapi layanan sistem sempat aktif pada awal sesi dan menurunkan "
            "throughput, dengan dampak terlihat pada urutan ulangan E6.",
            "Payload chunk dihapus setelah verifikasi berhasil untuk menghemat ruang penyimpanan, "
            "sehingga verifikasi ulang memerlukan menjalankan eksperimen kembali. Bukti verifikasi "
            "tetap tersimpan pada berkas log dan manifest.",
            "Dataset bersifat sintetis karena korpus Silesia "
            "tidak tersedia secara luring. Komposisi "
            "dan seed dicatat sehingga hasil dapat "
            "direproduksi, tetapi rasio kompresi dan waktu per "
            "chunk tidak identik dengan korpus tersebut.",
            "Master tidak direplikasi sehingga menjadi "
            "titik kegagalan tunggal. Bila Master berhenti, "
            "run harus diulang dari awal.",
            "Eksperimen E7 mengenai pengaruh ukuran chunk "
            "tidak dijalankan, sehingga pengaruh ukuran "
            "chunk terhadap overhead jaringan belum diukur.",
        ],
    ),
    # ------------------------------------------------------------- KESIMPULAN
    ("h1", ("", "KESIMPULAN")),
    (
        "p",
        "Berdasarkan seluruh tahapan perancangan, implementasi, pengukuran, dan pembahasan yang "
        "telah dilakukan, dapat ditarik beberapa kesimpulan utama:",
    ),
    (
        "bullets",
        [
            "Sistem kompresi data terdistribusi berbasis Master-Worker berhasil dibangun dan "
            "dijalankan pada sepuluh node virtual, yaitu satu Master dan sembilan Worker, dengan "
            "seluruh pertukaran data melalui protokol TCP berframe dan verifikasi SHA-256 pada "
            "setiap chunk.",
            "Pemrosesan berurutan memerlukan waktu 143,56 ± 6,79 detik, sedangkan pemrosesan "
            "terdistribusi dengan sembilan Worker memerlukan 62,31 ± 5,84 detik atau sekitar 2,301 "
            "kali lebih cepat. Pemrosesan paralel pada satu mesin dengan delapan proses memerlukan "
            "42,31 ± 6,71 detik dengan efficiency 0,463.",
            "Penjadwalan dinamis menurunkan makespan 14,4 persen dibandingkan penjadwalan statis "
            "pada kondisi terdapat Worker yang lebih lambat, yaitu 57,16 ± 0,88 detik berbanding "
            "66,78 ± 1,30 detik, dan menurunkan imbalance factor dari 1,222 menjadi 1,038.",
            "Fault tolerance berjalan sebagaimana dirancang. Pada skenario satu Worker mati, "
            "kegagalan terdeteksi dalam 0,26 ± 0,09 detik dan pekerjaan pulih dalam 1,37 ± 0,70 "
            "detik, sedangkan pada skenario tiga Worker "
            "mati dibutuhkan 0,38 ± 0,11 detik dan 5,60 ± "
            "5,84 detik. Seluruh run tetap berakhir dengan verifikasi berhasil.",
            "Percepatan tidak mencapai jumlah proses atau Worker karena dibatasi kecepatan Worker "
            "container, jumlah inti prosesor mesin virtual, "
            "pemrosesan berurutan di Master, overhead "
            "kerangka pengukuran, dan perebutan sumber daya "
            "bersama pada pemrosesan satu mesin. Batas "
            "kapasitas terlihat jelas pada hasil enam dan sembilan Worker yang praktis sama.",
            "Skalabilitas jumlah Worker mendatar setelah enam Worker, sesuai jumlah inti prosesor "
            "yang tersedia pada mesin virtual, sehingga "
            "penambahan Worker tanpa penambahan inti tidak "
            "menambah throughput.",
        ],
    ),
    (
        "p",
        "Keterbatasan yang perlu dinyatakan adalah "
        "penggunaan sepuluh node virtual pada satu laptop, "
        "penggunaan dataset sintetis sebagai pengganti korpus Silesia, penghapusan payload setelah "
        "verifikasi, ketidaktersediaan eksperimen ukuran "
        "chunk, dan Master tunggal tanpa replikasi. "
        "Keterbatasan tersebut tidak mengubah kesimpulan "
        "mengenai cara kerja sistem, tetapi membatasi "
        "seberapa jauh angka dapat digeneralisasi ke jaringan dengan perangkat terpisah.",
    ),
    (
        "p",
        "Saran untuk pengembangan berikutnya adalah menjalankan pengukuran pada sepuluh perangkat "
        "fisik dalam satu jaringan lokal, menambah replikasi Master atau mekanisme checkpoint agar "
        "tidak bergantung pada satu proses, memindahkan penulisan dan penghitungan hash hasil ke "
        "proses terpisah agar tidak menjadi bagian berurutan, serta menjalankan eksperimen ukuran "
        "chunk untuk mengukur pengaruh overhead jaringan secara langsung.",
    ),
    # --------------------------------------------------------- DAFTAR PUSTAKA
    ("h1", ("", "DAFTAR PUSTAKA")),
    (
        "plain",
        "Python Software Foundation. The Python Standard Library, versi 3.11 dan lebih baru. "
        "https://docs.python.org/3/",
    ),
    (
        "plain",
        "Python Software Foundation. multiprocessing, Process-based parallelism. "
        "https://docs.python.org/3/library/multiprocessing.html",
    ),
    (
        "plain",
        "Python Software Foundation. socket, Low-level networking interface. "
        "https://docs.python.org/3/library/socket.html",
    ),
    (
        "plain",
        "Python Software Foundation. lzma, Compression using the LZMA algorithm. "
        "https://docs.python.org/3/library/lzma.html",
    ),
    (
        "plain",
        "Python Software Foundation. hashlib, Secure hashes and message digests. "
        "https://docs.python.org/3/library/hashlib.html",
    ),
    (
        "plain",
        "Rodola, G. psutil, Cross-platform lib for process and system monitoring in Python. "
        "https://psutil.readthedocs.io",
    ),
    (
        "plain",
        "Matplotlib Development Team. Matplotlib documentation. https://matplotlib.org/stable/",
    ),
    (
        "plain",
        "Rujukan buku atau paper untuk rumus speedup, efficiency, dan hukum Amdahl: PERLU DIISI "
        "USER (penulis, tahun, judul, halaman).",
    ),
    (
        "plain",
        "Tanggal akses seluruh tautan di atas belum dicatat pada ASSETS.md dan perlu dilengkapi "
        "sebelum laporan dikumpulkan.",
    ),
]
