{
  description = "usdAecoBuildUp shared layered sections";
  inputs = {
    toolchain.url = "github:criad-com/usdaeco-toolchain?ref=v0.3.10";
    datacentre.url = "github:criad-com/usdaeco-datacentre?ref=v0.4.8";
    datacentre.flake = false;
    nixpkgs.follows = "toolchain/nixpkgs";
    core.url = "github:criad-com/usdaeco-core?ref=v0.9.4";
    core.flake = false;
  };
  outputs = { self, nixpkgs, toolchain, core, datacentre, ... }:
    let
      eachSystem = nixpkgs.lib.genAttrs [ "aarch64-darwin" "x86_64-linux" ];
      forSystem = system:
        let
          kit = toolchain.lib.forSystem system;
          pkgs = nixpkgs.legacyPackages.${system};
          corePlugin = (kit.buildCodelessSchema {
            name = "usdAeco"; src = core;
          }).overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              cp -RL tools/usdaeco_core tools/usdaeco_tools "$out/python/"
            '';
          });
          schema = (kit.buildCodelessSchema {
            name = "usdAecoBuildUp"; src = self; deps = [ corePlugin ];
          }).overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              cp -RL tools/usdaeco_buildup "$out/python/"
            '';
          });
          plugins = kit.pluginSet { plugins = [ schema ]; };
          setup = ''
            export TOOLCHAIN_DIR=${toolchain}
            export AECO_CORE_ROOT=${core}
            export AECO_DATACENTRE_ROOT=${datacentre}
            export CORE_PLUGIN_DIR=${corePlugin}/plugins/usdAeco/resources
          '';
          example = pkgs.writeShellApplication {
            name = "example";
            runtimeInputs = [ kit.pythonEnv kit.usd-dev ];
            text = setup + ''
              cp -R ${self} example-work
              chmod -R u+w example-work
              env -u PYTHONPATH PYTHONPATH="${core}:$PWD/example-work" python \
                example-work/examples/datacentre/run.py "$@"
            '';
          };
          render = pkgs.writeShellApplication {
            name = "render";
            runtimeInputs = [ kit.pythonEnv kit.usd-dev ];
            text = setup + ''
              cp -R ${self} render-work
              chmod -R u+w render-work
              env -u PYTHONPATH python render-work/tools/render_example.py "$@"
            '';
          };
        in { inherit kit pkgs schema plugins setup example render; };
    in {
      packages = eachSystem (system: let p = forSystem system; in {
        default = p.schema;
        pluginSet = p.plugins;
      });
      checks = eachSystem (system: let p = forSystem system; in {
        library = p.pkgs.runCommand "usdAecoBuildUp-check" {
          nativeBuildInputs = [ p.kit.pythonEnv p.kit.usd-dev p.pkgs.git ];
        } (p.setup + ''
          cp -R ${self} source
          chmod -R u+w source
          cd source
          env -u PYTHONPATH PYTHONPATH="${core}:$PWD" python check.py
          env -u PYTHONPATH python -m pytest -q
          mkdir -p "$out"
        '');
        structure = p.pkgs.runCommand "usdAecoBuildUp-structure" {
          nativeBuildInputs = [ p.kit.pythonEnv p.kit.usd-dev ];
        } (p.setup + ''
          env -u PYTHONPATH python ${self}/tools/check_structure.py
          mkdir -p "$out"
        '');
      });
      devShells = eachSystem (system: let p = forSystem system; in {
        default = p.pkgs.mkShell {
          packages = [ p.kit.pythonEnv p.kit.usd-dev p.pkgs.git ];
          shellHook = p.setup + "unset PYTHONPATH";
        };
      });
      apps = eachSystem (system: let p = forSystem system; in {
        example = { type = "app"; program = "${p.example}/bin/example"; };
        render = { type = "app"; program = "${p.render}/bin/render"; };
      });
    };
}
