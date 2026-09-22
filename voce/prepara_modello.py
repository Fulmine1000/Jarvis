#!/usr/bin/env python3
"""Scarica il modello vocale italiano maschile Riccardo per Jarvis."""

import hashlib
import os
import sys
import subprocess
import urllib.request
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE, "voce", "modelli")

MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx"
)
CONFIG_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "it/it_IT/riccardo/x_low/it_IT-riccardo-x_low.onnx.json"
)

MODEL_PATH = os.path.join(MODEL_DIR, "it_IT-riccardo-x_low.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "it_IT-riccardo-x_low.onnx.json")
MODEL_SHA256 = "1368de15f123275a7ef951c9e5e30be0f58a032daa14a0da44037443c1d1d21b"

CMAKE_HIGH_SIERRA_URL = (
    "https://github.com/Kitware/CMake/releases/download/v3.31.12/"
    "cmake-3.31.12-macos10.10-universal.tar.gz"
)


def trova_cmake(temporanea):
    """Restituisce CMake >= 3.24, scaricandone una copia locale su macOS vecchi."""
    cmake = shutil.which("cmake")
    if cmake:
        versione = subprocess.run(
            [cmake, "--version"],
            capture_output=True,
            check=False,
        ).stdout.decode("utf-8", errors="replace")
        try:
            numero = versione.split()[2]
            parti = tuple(int(x) for x in numero.split(".")[:2])
        except (IndexError, ValueError):
            parti = (0, 0)
        if parti >= (3, 24):
            return cmake

    locale_dir = os.path.join(temporanea, "cmake-high-sierra")
    locale_cmake = os.path.join(locale_dir, "cmake-3.31.12", "CMake.app", "Contents", "bin", "cmake")
    if os.path.isfile(locale_cmake):
        return locale_cmake

    archivio = os.path.join(MODEL_DIR, "cmake-high-sierra.tar.gz")
    print("CMake di sistema troppo vecchio: preparo CMake 3.31.12 compatibile con macOS 10.13...")
    scarica(CMAKE_HIGH_SIERRA_URL, archivio)

    if os.path.isdir(locale_dir):
        subprocess.run(["rm", "-rf", locale_dir], check=False)
    os.makedirs(locale_dir, exist_ok=True)
    risultato = subprocess.run(
        ["tar", "-xzf", archivio, "-C", locale_dir],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("estrazione di CMake 3.31.12 fallita")

    if not os.path.isfile(locale_cmake):
        candidati = []
        for radice, _, file in os.walk(locale_dir):
            if "cmake" in file and os.access(os.path.join(radice, "cmake"), os.X_OK):
                candidati.append(os.path.join(radice, "cmake"))
        if not candidati:
            raise RuntimeError("eseguibile CMake 3.31.12 non trovato")
        locale_cmake = candidati[0]

    os.chmod(locale_cmake, 0o755)
    return locale_cmake


# Il runtime espeak-ng distribuito con piper-phonemize 2023.11.14-4
# usa un formato Mach-O che High Sierra 10.13 non sa caricare. Per
# questa versione di macOS ricostruiamo espeak-ng dallo stesso commit
# usato dal progetto Piper, impostando il deployment target 10.13.
ESPEAK_COMMIT = "0f65aa301e0d6bae5e172cc74197d32a6182200f"
ESPEAK_URL = (
    "https://github.com/rhasspy/espeak-ng/archive/"
    f"{ESPEAK_COMMIT}.zip"
)


def scarica(url, destinazione):
    """Scarica il modello usando curl su macOS e urllib come fallback."""
    print(f"Download: {os.path.basename(destinazione)}")

    # Su macOS High Sierra il Python 3.11 installato può non avere
    # una catena CA aggiornata. curl usa invece il trust store di macOS.
    curl = shutil.which("curl")
    if curl:
        risultato = subprocess.run(
            [
                curl,
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--output",
                destinazione,
                url,
            ],
            check=False,
        )
        if risultato.returncode == 0:
            return

    try:
        urllib.request.urlretrieve(url, destinazione)
    except Exception:
        try:
            if os.path.exists(destinazione):
                os.remove(destinazione)
        except OSError:
            pass
        raise


def verifica_modello():
    if not os.path.isfile(MODEL_PATH):
        return False

    sha256 = hashlib.sha256()
    with open(MODEL_PATH, "rb") as file:
        for blocco in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(blocco)

    return sha256.hexdigest() == MODEL_SHA256


def compila_espeak_high_sierra(temporanea, lib_destinazione):
    """Costruisce eSpeak NG con target macOS 10.13 per evitare dylib incompatibili."""
    cmake = trova_cmake(temporanea)
    if not cmake:
        raise RuntimeError(
            "CMake non disponibile: per High Sierra serve CMake per ricostruire "
            "espeak-ng con deployment target 10.13"
        )

    sorgente_zip = os.path.join(MODEL_DIR, "espeak-ng-high-sierra.zip")
    sorgente = os.path.join(temporanea, "espeak-ng-src")
    build = os.path.join(temporanea, "espeak-ng-build")
    prefix = os.path.join(temporanea, "espeak-ng-install")

    print("High Sierra rilevato: ricompilo eSpeak NG con deployment target 10.13...")
    scarica(ESPEAK_URL, sorgente_zip)

    os.makedirs(sorgente, exist_ok=True)
    risultato = subprocess.run(
        ["unzip", "-q", sorgente_zip, "-d", sorgente],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("estrazione dei sorgenti eSpeak NG fallita")

    cartelle = [
        os.path.join(sorgente, nome)
        for nome in os.listdir(sorgente)
        if os.path.isdir(os.path.join(sorgente, nome))
    ]
    if not cartelle:
        raise RuntimeError("sorgenti eSpeak NG non trovati")
    sorgente_reale = cartelle[0]

    os.makedirs(build, exist_ok=True)
    configurazione = [
        cmake, "-S", sorgente_reale, "-B", build,
        f"-DCMAKE_INSTALL_PREFIX={prefix}",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.13",
        "-DBUILD_SHARED_LIBS=ON",
        "-DUSE_ASYNC=OFF",
        "-DUSE_MBROLA=OFF",
        "-DUSE_LIBSONIC=OFF",
        "-DUSE_LIBPCAUDIO=OFF",
        "-DUSE_KLATT=OFF",
        "-DUSE_SPEECHPLAYER=OFF",
        "-DEXTRA_cmn=ON",
        "-DEXTRA_ru=ON",
        "-DCMAKE_C_FLAGS=-D_FILE_OFFSET_BITS=64",
    ]
    risultato = subprocess.run(configurazione, check=False)
    if risultato.returncode != 0:
        raise RuntimeError("configurazione CMake di eSpeak NG fallita")

    risultato = subprocess.run(
        [cmake, "--build", build, "--config", "Release"],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("compilazione di eSpeak NG fallita")

    risultato = subprocess.run([cmake, "--install", build], check=False)
    if risultato.returncode != 0:
        raise RuntimeError("installazione locale di eSpeak NG fallita")

    libreria = None
    dati = None
    for radice, _, file in os.walk(prefix):
        if "libespeak-ng.1.dylib" in file:
            libreria = os.path.join(radice, "libespeak-ng.1.dylib")
        if os.path.basename(radice) == "espeak-ng-data":
            dati = radice

    if not libreria:
        raise RuntimeError("libespeak-ng.1.dylib non trovata dopo la compilazione")

    os.makedirs(lib_destinazione, exist_ok=True)
    shutil.copy2(
        libreria,
        os.path.join(lib_destinazione, "libespeak-ng.1.dylib"),
    )

    if dati:
        dati_destinazione = os.path.join(
            os.path.dirname(lib_destinazione),
            "espeak-ng-data",
        )
        if os.path.isdir(dati_destinazione):
            subprocess.run(["rm", "-rf", dati_destinazione], check=False)
        shutil.copytree(dati, dati_destinazione)

    return True

def compila_onnxruntime_high_sierra(temporanea, lib_destinazione):
    """Ricompila ONNX Runtime 1.14.1 senza CoreML con target macOS 10.13."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError(
            "Git non disponibile: per High Sierra serve Git per ricompilare "
            "ONNX Runtime 1.14.1"
        )

    sorgente = os.path.join(temporanea, "onnxruntime-src")
    build = os.path.join(temporanea, "onnxruntime-build")
    cmake = trova_cmake(temporanea)
    url = "https://github.com/microsoft/onnxruntime.git"

    print(
        "High Sierra rilevato: ricompilo ONNX Runtime 1.14.1 "
        "con deployment target 10.13 e CoreML disabilitato..."
    )

    if os.path.isdir(sorgente):
        subprocess.run(["rm", "-rf", sorgente], check=False)

    risultato = subprocess.run(
        [
            git,
            "clone",
            "--depth", "1",
            "--branch", "v1.14.1",
            "--recurse-submodules",
            url,
            sorgente,
        ],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("clone dei sorgenti ONNX Runtime 1.14.1 fallito")

    build_script = os.path.join(sorgente, "build.sh")
    if not os.path.isfile(build_script):
        raise RuntimeError("build.sh di ONNX Runtime non trovato")

    os.makedirs(build, exist_ok=True)

    configurazione = [
        build_script,
        "--config", "Release",
        "--build_shared_lib",
        "--parallel", "2",
        "--skip_tests",
        "--skip_submodule_sync",
        "--apple_deploy_target", "10.13",
        "--osx_arch", "x86_64",
        "--cmake_extra_defines",
        "CMAKE_OSX_DEPLOYMENT_TARGET=10.13",
        "CMAKE_OSX_ARCHITECTURES=x86_64",
        "onnxruntime_USE_COREML=OFF",
        "onnxruntime_BUILD_UNIT_TESTS=OFF",
    ]

    risultato = subprocess.run(
        configurazione,
        cwd=sorgente,
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("compilazione di ONNX Runtime 1.14.1 fallita")

    libreria = None
    for radice, _, file in os.walk(os.path.join(sorgente, "build")):
        if "libonnxruntime.1.14.1.dylib" in file:
            libreria = os.path.join(radice, "libonnxruntime.1.14.1.dylib")
            break

    if not libreria:
        raise RuntimeError(
            "libonnxruntime.1.14.1.dylib non trovata dopo la compilazione"
        )

    os.makedirs(lib_destinazione, exist_ok=True)
    destinazione = os.path.join(
        lib_destinazione, "libonnxruntime.1.14.1.dylib"
    )
    shutil.copy2(libreria, destinazione)

    # Rende il nome installato indipendente dal percorso della build.
    install_name_tool = shutil.which("install_name_tool")
    if not install_name_tool:
        raise RuntimeError("install_name_tool non disponibile")

    subprocess.run(
        [
            install_name_tool,
            "-id",
            "@rpath/libonnxruntime.1.14.1.dylib",
            destinazione,
        ],
        check=False,
    )

    # Controllo fondamentale: la libreria ricompilata non deve contenere
    # riferimenti al CoreML moderno che ha causato il crash su High Sierra.
    otool = shutil.which("otool")
    if otool:
        info = subprocess.run(
            [otool, "-L", destinazione],
            capture_output=True,
            check=False,
        )
        dipendenze = info.stdout.decode("utf-8", errors="replace")
        if "CoreML.framework" in dipendenze:
            raise RuntimeError(
                "ONNX Runtime ricompilato contiene ancora una dipendenza CoreML"
            )

    return True

def compila_piper_phonemize_high_sierra(temporanea, lib_destinazione):
    """Ricompila libpiper_phonemize con target macOS 10.13."""
    cmake = shutil.which("cmake")
    if not cmake:
        raise RuntimeError(
            "CMake non disponibile: per High Sierra serve CMake per "
            "ricostruire piper-phonemize con deployment target 10.13"
        )

    sorgente_zip = os.path.join(
        MODEL_DIR, "piper-phonemize-high-sierra.zip"
    )
    sorgente = os.path.join(temporanea, "piper-phonemize-src")
    build = os.path.join(temporanea, "piper-phonemize-build")
    prefix = os.path.join(temporanea, "piper-phonemize-install")

    url = (
        "https://github.com/rhasspy/piper-phonemize/archive/"
        "refs/tags/2023.11.14-4.zip"
    )

    print(
        "High Sierra rilevato: ricompilo piper-phonemize "
        "con deployment target 10.13..."
    )
    scarica(url, sorgente_zip)

    os.makedirs(sorgente, exist_ok=True)
    risultato = subprocess.run(
        ["unzip", "-q", sorgente_zip, "-d", sorgente],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("estrazione dei sorgenti piper-phonemize fallita")

    cartelle = [
        os.path.join(sorgente, nome)
        for nome in os.listdir(sorgente)
        if os.path.isdir(os.path.join(sorgente, nome))
    ]
    if not cartelle:
        raise RuntimeError("sorgenti piper-phonemize non trovati")
    sorgente_reale = cartelle[0]

    # Clang incluso in High Sierra non digerisce correttamente alcune
    # dichiarazioni constexpr generate da uni-algo nella release 2023.11.14-4.
    # Dopo l'estrazione applichiamo una correzione compatibile che mantiene
    # identico il comportamento, inizializzando esplicitamente i due piccoli
    # wrapper di locale.
    header_uni_algo = os.path.join(sorgente_reale, "src", "uni_algo.h")
    if os.path.isfile(header_uni_algo):
        with open(header_uni_algo, "r", encoding="utf-8") as file:
            header = file.read()
        header_originale = header
        header = header.replace(
            "constexpr region() noexcept = default;",
            "constexpr region() noexcept : value(0) {}",
        )
        header = header.replace(
            "constexpr script() noexcept = default;",
            "constexpr script() noexcept : value(0) {}",
        )
        if header == header_originale:
            raise RuntimeError(
                "correzione High Sierra di uni_algo.h non applicata"
            )
        with open(header_uni_algo, "w", encoding="utf-8") as file:
            file.write(header)

    # La release 2023.11.14-4 non offre un'opzione CMake per disabilitare
    # la CLI/test. Su High Sierra <filesystem> non esiste nel libc++ di sistema,
    # quindi rimuoviamo i due target che non servono al runtime di Jarvis.
    cmake_lists = os.path.join(sorgente_reale, "CMakeLists.txt")
    with open(cmake_lists, "r", encoding="utf-8") as file:
        cmake_source = file.read()

    blocco_cli = cmake_source.find("# ---- Declare executable ----")
    blocco_test = cmake_source.find("# ---- Declare test ----")
    blocco_install = cmake_source.find("# ---- Declare install targets ----")
    if blocco_cli < 0 or blocco_test < 0 or blocco_install < 0:
        raise RuntimeError("struttura CMake di piper-phonemize non riconosciuta")

    cmake_source = (
        cmake_source[:blocco_cli]
        + "# ---- High Sierra: CLI e test disabilitati ----\\n\\n"
        + cmake_source[blocco_install:]
    )
    cmake_source = cmake_source.replace(
        "install(\n    TARGETS piper_phonemize_exe\n    ARCHIVE DESTINATION " + "${CMAKE_INSTALL_BINDIR}" + ")\n\n",
        "",
    )
    with open(cmake_lists, "w", encoding="utf-8") as file:
        file.write(cmake_source)
    # Il CMake ufficiale scarica automaticamente ONNX Runtime 1.14.1 e
    # ricompila eSpeak NG. Passiamo esplicitamente il target 10.13 a tutte
    # le parti del progetto; il CMake di piper-phonemize inoltra le opzioni
    # necessarie al progetto esterno eSpeak NG.
    os.makedirs(build, exist_ok=True)
    # Su High Sierra il clang di sistema non fornisce <filesystem>.
    # L'eseguibile di esempio piper_phonemize_exe non è necessario a Jarvis:
    # ci serve esclusivamente la libreria condivisa usata dal binario Piper.
    # Disabilitiamo quindi la costruzione dell'eseguibile e delle CLI di test.
    configurazione = [
        cmake, "-S", sorgente_reale, "-B", build,
        f"-DCMAKE_INSTALL_PREFIX={prefix}",
        "-DCMAKE_OSX_DEPLOYMENT_TARGET=10.13",
        "-DBUILD_SHARED_LIBS=ON",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_EXAMPLES=OFF",
    ]
    risultato = subprocess.run(configurazione, check=False)
    if risultato.returncode != 0:
        raise RuntimeError("configurazione CMake di piper-phonemize fallita")

    risultato = subprocess.run(
        [cmake, "--build", build, "--config", "Release"],
        check=False,
    )
    if risultato.returncode != 0:
        raise RuntimeError("compilazione di piper-phonemize fallita")

    risultato = subprocess.run([cmake, "--install", build], check=False)
    if risultato.returncode != 0:
        raise RuntimeError("installazione locale di piper-phonemize fallita")

    libreria = None
    for radice, _, file in os.walk(prefix):
        if "libpiper_phonemize.1.dylib" in file:
            libreria = os.path.join(radice, "libpiper_phonemize.1.dylib")
            break

    if not libreria:
        raise RuntimeError(
            "libpiper_phonemize.1.dylib non trovata dopo la compilazione"
        )

    os.makedirs(lib_destinazione, exist_ok=True)
    shutil.copy2(
        libreria,
        os.path.join(lib_destinazione, "libpiper_phonemize.1.dylib"),
    )

    # Copia anche l'eventuale nome senza versione, se generato dal linker.
    for nome in ("libpiper_phonemize.dylib", "libpiper_phonemize.1.2.0.dylib"):
        candidato = None
        for radice, _, file in os.walk(prefix):
            if nome in file:
                candidato = os.path.join(radice, nome)
                break
        if candidato:
            shutil.copy2(candidato, os.path.join(lib_destinazione, nome))

    # libpiper_phonemize deve usare la libreria eSpeak NG ricompilata per
    # High Sierra, non una copia precompilata proveniente dall'archivio.
    espeak_compilato = os.path.join(
        lib_destinazione, "libespeak-ng.1.dylib"
    )
    if not os.path.isfile(espeak_compilato):
        raise RuntimeError(
            "libespeak-ng.1.dylib compilata per High Sierra non trovata"
        )

    install_name_tool = shutil.which("install_name_tool")
    if not install_name_tool:
        raise RuntimeError("install_name_tool non disponibile")

    # Il binario compilato da eSpeak può esportare il nome versionato;
    # rendiamo il riferimento usato da piper-phonemize esplicito e locale.
    piper_lib = os.path.join(
        lib_destinazione, "libpiper_phonemize.1.dylib"
    )
    if os.path.isfile(piper_lib):
        subprocess.run(
            [
                install_name_tool,
                "-change",
                "@rpath/libespeak-ng.dylib",
                "@rpath/libespeak-ng.1.dylib",
                piper_lib,
            ],
            check=False,
        )

    return True


def installa_piper():
    """Installa il binario Piper macOS x86_64 senza dipendere da onnxruntime."""
    destinazione = os.path.join(BASE, "voce", "bin")
    piper_path = os.path.join(destinazione, "piper")

    # Anche se il binario esiste, controlliamo e ripariamo le librerie
    # dinamiche: il pacchetto Piper macOS può essere presente senza
    # libespeak-ng.1.dylib.

    if sys.platform != "darwin" or os.uname().machine not in ("x86_64", "amd64"):
        print("AVVISO: installazione automatica del binario Piper prevista per macOS Intel.")
        return False

    url = (
        "https://github.com/rhasspy/piper/releases/download/"
        "2023.11.14-2/piper_macos_x64.tar.gz"
    )
    phonemize_url = (
        "https://github.com/rhasspy/piper-phonemize/releases/download/"
        "2023.11.14-4/piper-phonemize_macos_x64.tar.gz"
    )
    archivio = os.path.join(MODEL_DIR, "piper_macos_x64.tar.gz")
    archivio_phonemize = os.path.join(
        MODEL_DIR, "piper-phonemize_macos_x64.tar.gz"
    )
    temporanea = os.path.join(MODEL_DIR, "_piper_extract")
    lib_destinazione = os.path.join(destinazione, "piper-phonemize", "lib")

    print("Piper Python non è installabile su High Sierra perché manca una wheel compatibile di onnxruntime.")
    print("Preparo il binario Piper macOS Intel e tutte le librerie runtime necessarie...")

    try:
        if not os.path.isfile(piper_path):
            scarica(url, archivio)

        scarica(phonemize_url, archivio_phonemize)

        if os.path.isdir(temporanea):
            subprocess.run(["rm", "-rf", temporanea], check=False)
        os.makedirs(temporanea, exist_ok=True)

        if os.path.isfile(archivio):
            risultato = subprocess.run(
                ["tar", "-xzf", archivio, "-C", temporanea],
                check=False,
            )
            if risultato.returncode != 0:
                raise RuntimeError("estrazione del binario Piper fallita")

        risultato = subprocess.run(
            ["tar", "-xzf", archivio_phonemize, "-C", temporanea],
            check=False,
        )
        if risultato.returncode != 0:
            raise RuntimeError("estrazione delle librerie Piper fallita")

        trovato = None
        for radice, _, file in os.walk(temporanea):
            candidato = os.path.join(radice, "piper")
            if os.path.isfile(candidato):
                trovato = candidato
                break

        if trovato:
            os.makedirs(destinazione, exist_ok=True)
            shutil.copy2(trovato, piper_path)
            os.chmod(piper_path, 0o755)
        elif not os.path.isfile(piper_path):
            raise RuntimeError("binario Piper non trovato nell'archivio")

        # Gli archivi Piper possono contenere anche i file di debug dSYM.
        # Un dSYM può avere estensione .dylib ma NON è una libreria caricabile:
        # copiarlo dopo la libreria reale la sovrascriverebbe e produrrebbe
        # l'errore "mach-o, but wrong filetype" su High Sierra.
        dylib_trovate = []
        for radice, _, file in os.walk(temporanea):
            # Non attraversiamo directory dSYM: contengono companion file
            # Mach-O di tipo DSYM, non dylib eseguibili.
            parti = radice.split(os.sep)
            if any(parte.endswith(".dSYM") for parte in parti):
                continue
            for nome in file:
                if nome.endswith(".dylib"):
                    dylib_trovate.append(os.path.join(radice, nome))

        if not dylib_trovate:
            raise RuntimeError("nessuna libreria .dylib caricabile trovata nel pacchetto Piper")

        os.makedirs(lib_destinazione, exist_ok=True)
        for origine in dylib_trovate:
            nome = os.path.basename(origine)
            shutil.copy2(origine, os.path.join(lib_destinazione, nome))

        versione_macos = subprocess.run(
            ["sw_vers", "-productVersion"],
            capture_output=True,
            check=False,
        ).stdout.decode("utf-8", errors="replace").strip()

        # High Sierra non riesce a caricare la libpiper_phonemize precompilata
        # del pacchetto 2023.11.14-4 (load command 0x80000034). Non basta
        # ricostruire eSpeak NG: anche piper-phonemize deve essere compilato
        # con deployment target 10.13. Il suo CMake ufficiale usa ONNX
        # Runtime 1.14.1 ed eSpeak NG come dipendenze.
        if versione_macos.startswith("10.13."):
            # Il pacchetto piper-phonemize 2023.11.14-4 porta ONNX Runtime
            # 1.14.1 precompilato per macOS 10.14. Su High Sierra quel
            # binario richiama MLModelConfiguration, assente in CoreML 10.13.
            # Ricostruiamo quindi ONNX Runtime con target 10.13 e senza CoreML
            # prima di compilare piper-phonemize, così entrambe le librerie
            # restano compatibili con il sistema.
            compila_onnxruntime_high_sierra(
                temporanea,
                lib_destinazione,
            )
            compila_espeak_high_sierra(temporanea, lib_destinazione)
            compila_piper_phonemize_high_sierra(
                temporanea,
                lib_destinazione,
            )

        install_name_tool = shutil.which("install_name_tool")
        if not install_name_tool:
            raise RuntimeError("install_name_tool non disponibile")

        otool = shutil.which("otool")
        rpath = "@executable_path/piper-phonemize/lib"
        ha_rpath = False
        if otool:
            info = subprocess.run(
                [otool, "-l", piper_path],
                capture_output=True,
                check=False,
            )
            testo = info.stdout.decode("utf-8", errors="replace")
            ha_rpath = rpath in testo

        if not ha_rpath:
            risultato = subprocess.run(
                [install_name_tool, "-add_rpath", rpath, piper_path],
                check=False,
            )
            if risultato.returncode != 0:
                raise RuntimeError("configurazione della rpath di Piper fallita")

        controllo = subprocess.run(
            [piper_path, "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if controllo.returncode != 0:
            errore = controllo.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                "Piper installato ma non avviabile"
                + (f": {errore}" if errore else "")
            )

        print(f"Piper installato: {piper_path}")
        return True
    except Exception as errore:
        print(f"AVVISO: installazione del binario Piper non riuscita: {errore}")
        return False
    finally:
        try:
            if os.path.isdir(temporanea):
                subprocess.run(["rm", "-rf", temporanea], check=False)
            for file_temporaneo in (
                archivio,
                archivio_phonemize,
                os.path.join(MODEL_DIR, "espeak-ng-high-sierra.zip"),
                os.path.join(MODEL_DIR, "piper-phonemize-high-sierra.zip"),
                os.path.join(MODEL_DIR, "cmake-high-sierra.tar.gz"),
            ):
                if os.path.isfile(file_temporaneo):
                    os.remove(file_temporaneo)
        except OSError:
            pass


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not verifica_modello():
        scarica(MODEL_URL, MODEL_PATH)

    if not verifica_modello():
        print("ERRORE: checksum del modello non valido.")
        try:
            os.remove(MODEL_PATH)
        except OSError:
            pass
        return 1

    if not os.path.isfile(CONFIG_PATH):
        scarica(CONFIG_URL, CONFIG_PATH)

    piper_ok = installa_piper()

    print("Voce italiana maschile Riccardo installata.")
    print(f"Modello: {MODEL_PATH}")
    if piper_ok:
        print("Motore Piper TTS: disponibile.")
    else:
        print("Motore Piper TTS: NON disponibile; Jarvis userà temporaneamente la voce di sistema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
