{
  description = "Reconocimiento facial con Python 3.12";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      libraries = with pkgs; [
        stdenv.cc.cc.lib
        zlib
        zstd
        libxcb
        libGL
        glib
        libx11
        libxext
        libxrender
        libxkbcommon
        libsm
        libice
        libxrandr
        libxi
        libxfixes
        libxcursor
        libxinerama
        fontconfig
        freetype
      ];

    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python312
          uv
          pkg-config
        ];

        UV_PYTHON = "${pkgs.python312}/bin/python3.12";
        UV_PYTHON_DOWNLOADS = "never";

        shellHook = ''
          export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath libraries}"
          echo "Entorno de reconocimiento facial listo"
        '';
      };
    };
}
