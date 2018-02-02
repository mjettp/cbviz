"""
This is a module
author: Bill Flynn
email: wflynny AT gmail DOT com
"""
import argparse
import numpy as np

from .colorspace import (MonochromeColorSpace,
                         ProtanopiaColorSpace,
                         DeuteranopiaColorSpace,
                         TritanopiaColorSpace,
                         OriginalColorSpace,
                         colordiff_1d,
                         colordiff_3d)
from .plotting import (load_image,
                       plot_individually,
                       plot_together)


def generate_colorspaces(types, severity, run_all=True,
                         dest_space_name='sRGB1') -> list:
    """
    Given either `run_all` or specified `types`, return corresponding
    ColorSpace objects with the correct severity
    """
    # prepare colorspace converters
    translator = {'p': ProtanopiaColorSpace,
                  'd': DeuteranopiaColorSpace,
                  't': TritanopiaColorSpace,
                  'm': MonochromeColorSpace}

    colorspaces = []
    if not run_all:
        for deficiency in types:
            cspace = translator[deficiency[0]]
            colorspaces.append(cspace(severity, dest_space_name))
    else:
        # 100 if severity != 100 else 50
        next_round = 50 * (int(severity != 100) + 1)
        for colorspace in translator.values():
            colorspaces.append(colorspace(severity, dest_space_name))
            colorspaces.append(colorspace(next_round, dest_space_name))
    return colorspaces


def simulate_colorblindness(arguments):
    """
    Placeholder
    """
    colorspaces = generate_colorspaces(arguments.type,
                                       arguments.severity,
                                       run_all=arguments.all)

    inpath = arguments.infile
    outpath = arguments.outfile
    save_params = dict(dpi=300)

    if arguments.individual_plots:
        plot_individually(inpath, colorspaces, outpath, **save_params)
    else:
        plot_together(inpath, colorspaces, outpath,
                      show_original=not arguments.no_original,
                      **save_params)

def test_colorblindness(arguments):
    """
    Honestly, this just doesn't work at the moment.  Computing deltaE isn't
    the best way to do this because things can still be colorblind friendly if
    the colors have large distances.  For example, imagine comparing `255 - im`
    and `im`;  those will have maximal differences between black and white but
    will stil be colorblind friendly.

    Instead, I think this should rely on the luminance/lightness component of
    CAM02-UCS (aka J) but even that doesn't work (monochrome passes for example
    when it shouldn't). I'm not sure what to do.
    """
    # prepare colorspace converters
    colorspaces = generate_colorspaces(arguments.type,
                                       arguments.severity,
                                       run_all=arguments.all)

    original_image = load_image(arguments.infile)

    overall_failed = False
    for colorspace in colorspaces:
        deltaEs = colordiff_1d(original_image, colorspace, channel=0)
        comparison = np.any(deltaEs > 100 * arguments.epsilon)
        if comparison:
            import matplotlib.pyplot as plt
            from colorspacious import cspace_convert
            im1 = cspace_convert(original_image, 'sRGB1', 'CAM02-UCS')
            im2 = cspace_convert(colorspace.convert(original_image), 'sRGB1', 'CAM02-UCS')
            plt.figure()
            im3 = plt.imshow(np.abs(im2[...,1] - im1[...,1]))
            plt.colorbar(im3)
            plt.figure()
            plt.imshow(cspace_convert(im2, 'CAM02-UCS', 'sRGB1'))
            plt.show()

        pass_fail_msg = f"\t{colorspace.name:<20}: "
        pass_fail_msg += "Fail" if comparison else "Pass"
        print(pass_fail_msg)
        overall_failed = comparison or overall_failed

    if overall_failed:
        print(f"Image [{arguments.infile}] is not colorblind friendly.")
    else:
        print(f"Image [{arguments.infile}] is colorblind friendly.")


class ValidateChoices(argparse.Action):
    """
    Split `types` string on ',' and validate choices
    """
    def __call__(self, parser, args, values, option_string=None):
        valid_prefixes = ['protan', 'deuteran', 'tritan', 'mono']
        values = values.split(',')
        for value in values:
            invalid = True
            for prefix in valid_prefixes:
                if value.startswith(prefix):
                    invalid = False
            if invalid:
                raise ValueError(f"Invalid choice {value!r}")
        setattr(args, self.dest, list(set(values)))

def build_parser():
    """Setup argument parser for this script"""
    parser = argparse.ArgumentParser()

    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument('-s', '--severity', type=int, default=100,
                        help=("[0-100]: severity of colorblindess, 0 being"
                              " no deficiency, 100 being completely *opic"))
    type_group = parent.add_mutually_exclusive_group(required=True)
    type_group.add_argument('-t', '--type', action=ValidateChoices,
                            help=("One or more of 'protan*', 'deuteran*', "
                                  "'tritan*', 'mono*' in **comma** separated "
                                  "list."))
    type_group.add_argument('-a', '--all', action='store_true',
                            help=("Include completely *opic versions as well "
                                  "as anomalous versions with given severity."
                                  "If severity is 100, then show anomalous "
                                  "versions at severity=50 too."))
    parent.add_argument('infile', help="Input image path")

    subparsers = parser.add_subparsers(title='commands', dest='command')
    test_parser = subparsers.add_parser('test', parents=[parent],
                                        help=("Brief text-based test to see if "
                                              "image is colorblind friendly"))
    test_parser.set_defaults(main_func=test_colorblindness)
    test_parser.add_argument('-e', '--epsilon', type=float, default=0.1,
                             help=("[0-1]: error threshold under which "
                                   "transformed image is declared 'similar'"))
    test_parser.add_argument('-q', '--quiet', action='store_true',
                             help="Print as little information as possible")

    sim_parser = subparsers.add_parser('simulate', parents=[parent],
                                       help=("Simulate colorblindess on the "
                                             "provided image and plot"))
    sim_parser.set_defaults(main_func=simulate_colorblindness)
    sim_parser.add_argument('outfile', help="Path to save resulting image(s)")
    sim_parser.add_argument('--individual-plots', action='store_true',
                            help="Store each image as separate file")
    sim_parser.add_argument('--no-original', action='store_true',
                            help="Don't show original for comparison")

    return parser

def fast_main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--severity', type=int, default=100,
                        help=("[0-100]: severity of colorblindess, 0 being"
                              " no deficiency, 100 being completely *opic"))
    parser.add_argument('infile', help="Input image path")
    parser.add_argument('outfile', help="Path to save resulting image(s)")
    parser.add_argument('-m', '--monochrome', action='store_true',
                        help='show monochrome instead of original')
    parser.set_defaults(command='simulate', no_original=False,
                        individual_plots=False, all=False,
                        type=['protan', 'deuteran', 'tritan'],
                        main_func=simulate_colorblindness)
    arguments = parser.parse_args()
    if arguments.monochrome:
        arguments.no_original = True
        arguments.type = ['protan', 'deuteran', 'tritan', 'monochrome']
    arguments.main_func(arguments)

def main():
    """
    Placeholder
    """
    argument_parser = build_parser()
    arguments = argument_parser.parse_args()
    arguments.main_func(arguments)
