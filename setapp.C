// setapp
// Copyright 2020
// Al Danial
// Tom Kowalski

#include <string>
#include <iostream>
#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>
#include <fmt/format.h>
#include <yaml-cpp/yaml.h>

using namespace boost::program_options;

typedef struct Args { // {{{
    std::string show_app;
    std::string shell;
    std::string configfile;
} Args;
// }}}
Args parse_args(int argc, const char *argv[]) // {{{
{

    variables_map vm;
    Args cli_args;
    cli_args.show_app   = "";
    cli_args.shell      = "";
    cli_args.configfile = "Setapp_inputs.yaml";
    // based on https://theboostcpplibraries.com/boost.program_options
    try
    {
        options_description desc{"Options"};
        desc.add_options()
          ("config"   , value<std::string>()->implicit_value("Setapp_inputs.yaml"),
                       "Application definition file (YAML format).")
          ("help,h"  , "Help screen")
          ("show-app", value<std::string>()->implicit_value("all"),
                       "Print information about the given applications.  "
                       "Without arguments, prints all.")
          ("shell"   , value<std::string>()->implicit_value("bash"),
                       "Shell (csh/bash)")
          ;
  
        command_line_parser parser{argc, argv};
        parser.options(desc).allow_unregistered().style(
          command_line_style::default_style |
          command_line_style::allow_slash_for_short);
        parsed_options parsed_options = parser.run();
  
        variables_map vm;
        store(parsed_options, vm);
        notify(vm);
  
        if (vm.count("help")) {
            std::cout << desc << std::endl;
            exit(0);
        }

        if (vm.count("shell")) {
            cli_args.shell    = vm["shell"].as<std::string>();
        }
        if (vm.count("show-app")) {
            cli_args.show_app = vm["show-app"].as<std::string>();
        }
        if (vm.count("config")) {
            cli_args.configfile = vm["config"].as<std::string>();
        }

        if (!boost::filesystem::exists(cli_args.configfile))
        {
            fmt::print("Cannot find {0:s}, exit.\n", cli_args.configfile);
            exit(1);
        }
    }
    catch (const error &e) {
      std::cerr << e.what() << '\n';
    }
    return cli_args;
}
// }}}
void print_args(Args cli) // {{{
{
    fmt::print("config   : {0:s}\n", cli.configfile);
    fmt::print("shell    : {0:s}\n", cli.shell);
    fmt::print("show-app : {0:s}\n", cli.show_app);
}
// }}}

int main(int argc, const char *argv[])
{
    Args cli_args = parse_args(argc, argv);
    print_args(cli_args);
    try {
        YAML::Node config = YAML::LoadFile(cli_args.configfile);
    } catch (YAML::ParserException& e) {
        std::cerr << e.what() << '\n';
        exit(1);
    } catch (const error &e) {
        std::cerr << e.what() << '\n';
        exit(1);
    }
}
