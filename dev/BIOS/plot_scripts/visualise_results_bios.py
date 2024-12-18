#!/usr/bin/env python3

"""
File:         visualise_results_bios.py
Created:      2021/11/09
Last Changed: 2022/03/25
Author:       M.Vochteloo

Copyright (C) 2020 University Medical Center Groningen.

A copy of the BSD 3-Clause "New" or "Revised" License can be found in the
LICENSE file in the root directory of this source tree.
"""

# Standard imports.
from __future__ import print_function
import argparse
import subprocess
import glob
import os

# Third party imports.
import pandas as pd

# Local application imports.

# Metadata
__program__ = "Visualise Results BIOS"
__author__ = "Martijn Vochteloo"
__maintainer__ = "Martijn Vochteloo"
__email__ = "m.vochteloo@rug.nl"
__license__ = "BSD (3-Clause)"
__version__ = 1.0
__description__ = "{} is a program developed and maintained by {}. " \
                  "This program is licensed under the {} license and is " \
                  "provided 'as-is' without any warranty or indemnification " \
                  "of any kind.".format(__program__,
                                        __author__,
                                        __license__)

"""
Syntax: 
./visualise_results_bios.py -h
"""


class main():
    def __init__(self):
        # Get the command line arguments.
        arguments = self.create_argument_parser()
        self.input_data_path = getattr(arguments, 'input_data')
        self.pf_path = getattr(arguments, 'picalo_files')
        self.expression_preprocessing_path = getattr(arguments, 'expression_preprocessing_dir')
        self.palette_path = getattr(arguments, 'palette')
        self.outname = getattr(arguments, 'outname')
        self.extensions = getattr(arguments, 'extensions')

        # Set variables.
        self.outdir = os.path.join(str(os.path.dirname(os.path.abspath(__file__))), 'plot')
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)

    @staticmethod
    def create_argument_parser():
        parser = argparse.ArgumentParser(prog=__program__,
                                         description=__description__)

        # Add optional arguments.
        parser.add_argument("-v",
                            "--version",
                            action="version",
                            version="{} {}".format(__program__,
                                                   __version__),
                            help="show program's version number and exit.")
        parser.add_argument("-id",
                            "--input_data",
                            type=str,
                            required=True,
                            help="The path to PICALO results.")
        parser.add_argument("-pf",
                            "--picalo_files",
                            type=str,
                            required=True,
                            help="The path to the picalo files.")
        parser.add_argument("-ep",
                            "--expression_preprocessing_dir",
                            type=str,
                            required=True,
                            help="The path to the expression preprocessing data.")
        parser.add_argument("-p",
                            "--palette",
                            type=str,
                            required=True,
                            help="The path to a json file with the"
                                 "dataset to color combinations.")
        parser.add_argument("-o",
                            "--outname",
                            type=str,
                            required=True,
                            help="The name of the output files.")
        parser.add_argument("-e",
                            "--extensions",
                            type=str,
                            nargs="+",
                            default=["png"],
                            choices=["eps", "pdf", "pgf", "png", "ps", "raw", "rgba", "svg", "svgz"],
                            help="The output file format(s), default: ['png']")

        return parser.parse_args()

    def start(self):
        self.print_arguments()

        # Plot overview lineplot.
        command = ['python3', 'overview_lineplot.py', '-i', self.input_data_path, '-p', self.palette_path, "-o", self.outname]
        self.run_command(command)

        # Plot covariate selection overview lineplot.
        command = ['python3', 'covariate_selection_lineplot.py', '-i', self.input_data_path, '-p', self.palette_path, "-o", self.outname]
        self.run_command(command)

        # Plot genotype stats.
        command = ['python3', 'create_histplot.py', '-d', os.path.join(self.input_data_path, "genotype_stats.txt.gz"), "-o", self.outname + "_GenotypeStats"]
        self.run_command(command)

        # Plot eQTL upsetplot.
        command = ['python3', 'create_upsetplot.py', '-i', self.input_data_path, '-e', os.path.join(self.pf_path, "eQTLProbesFDR0.05-ProbeLevel-Available.txt.gz"), '-p', self.palette_path, '-o', self.outname]
        self.run_command(command)

        # Plot interaction overview plot.
        command = ['python3', 'interaction_overview_plot.py', '-i', self.input_data_path, '-p', self.palette_path, '-o', self.outname]
        self.run_command(command)

        # Plot #ieQTLs per sample boxplot.
        command = ['python3', 'no_ieqtls_per_sample_plot.py', '-i', self.input_data_path, '-p', self.palette_path, '-o', self.outname]
        self.run_command(command)

        pics = []
        last_iter_fpaths = []
        for i in range(1, 50):
            pic = "PIC{}".format(i)
            comp_iterations_path = os.path.join(self.input_data_path, pic, "iteration.txt.gz")

            if os.path.exists(comp_iterations_path):
                pics.append(pic)
                fpaths = glob.glob(os.path.join(self.input_data_path, pic, "results_iteration*"))
                fpaths.sort()
                if len(fpaths) == 0:
                    break
                last_iter_fpaths.append(fpaths[-1])

                # Plot scatterplot.
                command = ['python3', 'create_scatterplot.py', '-d', comp_iterations_path,
                           "-hr", "0", "-ic", "0", "-a", "1", "-std", os.path.join(self.pf_path, "sample_to_dataset.txt.gz"), '-p', self.palette_path, "-o", self.outname + "_PIC{}".format(i)]
                self.run_command(command)

                # # Plot correlation_heatmap of iterations.
                # command = ['python3', 'create_correlation_heatmap.py', '-rd', comp_iterations_path, "-rn", self.outname, "-o", self.outname + "_{}".format(pic)]
                # self.run_command(command)

        # Compare iterative t-values .
        command = ['python3', 'compare_tvalues.py', '-d'] + last_iter_fpaths[:5] + ['-n'] + pics[:5] + ['-o', self.outname + '_IterativeTValuesOverview']
        self.run_command(command)

        # Create components_df if not exists.
        components_path = os.path.join(self.input_data_path, "components.txt.gz")
        if not os.path.exists(components_path):
            print("Components file does not exists, loading iteration files")
            data = []
            columns = []
            for i in range(1, 50):
                pic = "PIC{}".format(i)
                comp_iterations_path = os.path.join(self.input_data_path, pic, "iteration.txt.gz")
                if os.path.exists(comp_iterations_path):
                    df = self.load_file(comp_iterations_path, header=0, index_col=0)
                    last_iter = df.iloc[[df.shape[0] - 1], :].T
                    data.append(last_iter)
                    columns.append(pic)

            if len(data) > 0:
                components_df = pd.concat(data, axis=1)
                components_df.columns = columns
                self.save_file(components_df.T, outpath=components_path, header=True, index=True)

        # Plot comparison to expression mean correlation.
        for pic in pics:
            command = ['python3', 'create_regplot.py', '-xd', components_path,
                       "-xi", pic, '-yd', '/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/correlate_samples_with_avg_gene_expression/BIOS_CorrelationsWithAverageExpression.txt.gz', '-y_transpose', '-yi', 'AvgExprCorrelation', '-std', os.path.join(self.pf_path, "sample_to_dataset.txt.gz"), '-p', self.palette_path, '-o', self.outname + "_{}_vs_AvgExprCorrelation".format(pic)]
            self.run_command(command)

        # Check for which PICs we have the interaction stats.
        pics = []
        pic_interactions_fpaths = []
        for i in range(1, 6):
            pic = "PIC{}".format(i)
            fpath = os.path.join(self.input_data_path, "PIC_interactions", "{}.txt.gz".format(pic))
            if os.path.exists(fpath):
                pics.append(pic)
                pic_interactions_fpaths.append(fpath)

        if len(pic_interactions_fpaths) > 0:
            # Compare t-values.
            command = ['python3', 'compare_tvalues.py', '-d'] + pic_interactions_fpaths + ['-n'] + pics + ['-o', '{}_TValuesOverview'.format(self.outname)]
            self.run_command(command)

        # Plot comparison scatterplot.
        command = ['python3', 'create_comparison_scatterplot.py', '-d', components_path,
                   '-std', os.path.join(self.pf_path, "sample_to_dataset.txt.gz"), '-n', '5', '-p', self.palette_path, '-o', self.outname + "_ColoredByDataset"]
        self.run_command(command)

        # Plot comparison scatterplot.
        command = ['python3', 'create_comparison_scatterplot.py', '-d', components_path,
                   '-std', "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_sex.txt.gz", '-n', '5', '-p', self.palette_path, '-o', self.outname + "_ColoredBySex"]
        self.run_command(command)

        if os.path.exists(components_path):
            # Plot correlation_heatmap of components.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-o", self.outname, "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs expression correlations.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/correlate_samples_with_avg_gene_expression/BIOS_CorrelationsWithAverageExpression.txt.gz", "-cn", "AvgExprCorrelation", "-o", self.outname + "_vs_AvgExprCorrelation", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs datasets.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", os.path.join(self.pf_path, "datasets_table.txt.gz"), "-cn", "datasets", "-o", self.outname + "_vs_Datasets", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs RNA alignment metrics.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_RNA_AlignmentMetrics.txt.gz", "-cn", "RNAseq alignment metrics", "-o", self.outname + "_vs_RNASeqAlignmentMetrics", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs Sex.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_sex.txt.gz", "-cn", "Sex", "-o", self.outname + "_vs_Sex"]
            self.run_command(command)

            # Plot correlation_heatmap of components vs MDS.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", os.path.join(self.pf_path, "mds_table.txt.gz"), "-cn", "MDS", "-o", self.outname + "_vs_MDS", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs PCA without cov correction.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", os.path.join(self.expression_preprocessing_path, 'data', 'gene_read_counts_BIOS_and_LLD_passQC.tsv.SampleSelection.ProbesWithZeroVarianceRemoved.TMM.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.PCAOverSamplesEigenvectors.txt.gz'), "-cn", "PCA before cov. corr.", "-o", self.outname + "_vs_PCABeforeCorrection", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs PCA with cov correction.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", os.path.join(self.expression_preprocessing_path, "data", "gene_read_counts_BIOS_and_LLD_passQC.tsv.SampleSelection.ProbesWithZeroVarianceRemoved.TMM.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.CovariatesRemovedOLS.ScaleAndLocReturned.PCAOverSamplesEigenvectors.txt.gz"), "-cn", "PCA after cov. corr.", "-o", self.outname + "_vs_PCAAfterCorrection", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs PCA with centering and cov correction.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", os.path.join(self.expression_preprocessing_path, "data", "gene_read_counts_BIOS_and_LLD_passQC.tsv.SampleSelection.ProbesWithZeroVarianceRemoved.TMM.SampleSelection.ProbesWithZeroVarianceRemoved.Log2Transformed.ProbesCentered.SamplesZTransformed.PCAOverSamplesEigenvectors.txt.gz"), "-cn", "PCA centered after cov. corr.", "-o", self.outname + "_vs_PCACenteredAfterCorrection", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs cell fraction %.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_CellFractionPercentages.txt.gz", "-cn", "cell fractions %", "-o", self.outname + "_vs_CellFractionPercentages"]
            self.run_command(command)

            # Plot correlation_heatmap of components vs cell counts.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_CellCounts.txt.gz", "-cn", "cell counts", "-o", self.outname + "_vs_CellCounts", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs blood stats.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_BloodStats.txt.gz", "-cn", "blood stats", "-o", self.outname + "_vs_BloodStats", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs decon.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/data/BIOS_cell_types_DeconCell_2019-03-08.txt.gz", "-cn", "Decon-Cell cell fractions", "-o", self.outname + "_vs_decon", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs phenotypes.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_bios_phenotype_matrix/BIOS_phenotypes.txt.gz", "-cn", "phenotypes", "-o", self.outname + "_vs_Phenotypes", "-e"] + self.extensions
            self.run_command(command)

            # Plot correlation_heatmap of components vs SP140.
            command = ['python3', 'create_correlation_heatmap.py', '-rd', components_path, "-rn", self.outname, "-cd", "/groups/umcg-bios/tmp01/projects/PICALO/preprocess_scripts/prepare_picalo_files/BIOS-BIOS-cis-NoRNAPhenoNA-NoSexNA-NoMixups-NoMDSOutlier-NoRNAseqAlignmentMetrics/SP140.txt.gz", "-cn", "SP140", "-o", self.outname + "_vs_SP140", "-e"] + self.extensions
            self.run_command(command)

    @staticmethod
    def load_file(inpath, header, index_col, sep="\t", low_memory=True,
                  nrows=None, skiprows=None):
        df = pd.read_csv(inpath, sep=sep, header=header, index_col=index_col,
                         low_memory=low_memory, nrows=nrows, skiprows=skiprows)
        print("\tLoaded dataframe: {} "
              "with shape: {}".format(os.path.basename(inpath),
                                      df.shape))
        return df

    @staticmethod
    def save_file(df, outpath, header=True, index=False, sep="\t"):
        compression = 'infer'
        if outpath.endswith('.gz'):
            compression = 'gzip'

        df.to_csv(outpath, sep=sep, index=index, header=header,
                  compression=compression)
        print("\tSaved dataframe: {} "
              "with shape: {}".format(os.path.basename(outpath),
                                      df.shape))

    @staticmethod
    def run_command(command):
        print(" ".join(command))
        subprocess.call(command)

    def print_arguments(self):
        print("Arguments:")
        print("  > Input data path: {}".format(self.input_data_path))
        print("  > Picalo files path: {}".format(self.pf_path))
        print("  > Expression pre-processing data path: {}".format(self.expression_preprocessing_path))
        print("  > Palette path: {}".format(self.palette_path))
        print("  > Outname {}".format(self.outname))
        print("  > Output directory {}".format(self.outdir))
        print("  > Extensions: {}".format(self.extensions))
        print("")


if __name__ == '__main__':
    m = main()
    m.start()
