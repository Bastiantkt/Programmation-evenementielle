🔧 - Instructions détaillées d'installation -

🐧 - Arch Linux - : 

    </> $ sudo pacman -Syu python python-pip gcc base-devel jdk-openjdk

🎩 - Fedora - : 

    </> $ sudo dnf update --refresh -y && sudo dnf install -y python3 python3-pip gcc g++ java-17-openjdk-devel

🍥 - Debian / Ubuntu - : 

    </> $ sudo apt update && sudo apt install -y python3 python3-pip gcc g++ openjdk-17-jdk

🍎 - MacOS - : 

    </> $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    </> $ brew install python gcc openjdk

🔧 Vérifiez les versions et que les programmes sont bien installé dans le $PATH : 

    </> $ python --version (version 3)
    </> $ pip --version
    </> $ gcc --version
    </> $ g++ --version
    </> $ javac --version


