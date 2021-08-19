import base_juno_pipeline
import csv
import os
import pathlib
from sys import path
import unittest

main_script_path = str(pathlib.Path(pathlib.Path(__file__).parent.absolute()).parent.absolute())
path.insert(0, main_script_path)
import juno_assembly



class TestJunoAssemblyDryRun(unittest.TestCase):
    """Testing the junoassembly class (code specific for this pipeline)"""

    def setUpClass():
        fake_dirs = ['fake_dir_wsamples',
                    'fake_empty_dir']

        fake_files = ['fake_dir_wsamples/sample1_R1.fastq',
                    'fake_dir_wsamples/sample1_R2.fastq.gz',
                    'fake_dir_wsamples/sample2_R1_filt.fq',
                    'fake_dir_wsamples/sample2_R2_filt.fq.gz', 
                    'fake_dir_wsamples/1234_R1.fastq.gz',
                    'fake_dir_wsamples/1234_R2.fastq.gz']
                            
        for folder in fake_dirs:
            pathlib.Path(folder).mkdir(exist_ok = True)
        for file_ in fake_files:
            pathlib.Path(file_).touch(exist_ok = True)

        with open('fake_dir_wsamples/fake_metadata.csv', mode='w') as metadata_file:
            metadata_writer = csv.writer(metadata_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            metadata_writer.writerow(['Sample', 'Genus', 'Species'])
            metadata_writer.writerow(['sample1', 'Salmonella', 'enterica'])
            metadata_writer.writerow(['sample2', 'Escherichia', 'coli'])
            metadata_writer.writerow(['1234', 'campylobacter', 'jejuni'])

    def tearDownClass():
        fake_dirs = ['fake_dir_wsamples', 
                    'fake_empty_dir',
                    'test_output']
        for folder in fake_dirs:
            os.system('rm -rf {}'.format(str(folder)))
    
    def test_fails_with_empty_dir(self):
        """Testing the pipeline fails if input_dir is empty"""
        with self.assertRaisesRegex(ValueError, 'does not contain files that end with one of the expected extensions'):
            juno_assembly.JunoAssemblyRun(input_dir = 'fake_empty_dir', 
                                    metadata= None,
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
    
    def test_junoassembly_dryrun(self):
        """Testing the pipeline runs properly as a dry run"""
        pipeline_dry_run = juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    metadata= None,
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
        expected_sample_sheet = {'sample1': {'R1': 'fake_dir_wsamples/sample1_R1.fastq',
                                            'R2': 'fake_dir_wsamples/sample1_R2.fastq.gz',
                                            'genus': None},
                                'sample2': {'R1': 'fake_dir_wsamples/sample2_R1_filt.fq',
                                            'R2': 'fake_dir_wsamples/sample2_R2_filt.fq.gz',
                                            'genus': None},
                                '1234': {'R1': 'fake_dir_wsamples/1234_R1.fastq.gz',
                                            'R2': 'fake_dir_wsamples/1234_R2.fastq.gz',
                                            'genus': None} }
        self.assertTrue(pipeline_dry_run.successful_run, 'Exception raised when running a dryrun')
        self.assertEqual(pipeline_dry_run.startup.sample_dict, expected_sample_sheet, pipeline_dry_run.startup.sample_dict)

    def test_junoassembly_dryrun_if_genus_provided(self):
        """Testing the pipeline runs properly as a dry run"""
        pipeline_dry_run = juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    metadata= None,
                                    genus='salmonella',
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
        expected_sample_sheet = {'sample1': {'R1': 'fake_dir_wsamples/sample1_R1.fastq',
                                            'R2': 'fake_dir_wsamples/sample1_R2.fastq.gz',
                                            'genus': 'salmonella'},
                                'sample2': {'R1': 'fake_dir_wsamples/sample2_R1_filt.fq',
                                            'R2': 'fake_dir_wsamples/sample2_R2_filt.fq.gz',
                                            'genus': 'salmonella'},
                                '1234': {'R1': 'fake_dir_wsamples/1234_R1.fastq.gz',
                                            'R2': 'fake_dir_wsamples/1234_R2.fastq.gz',
                                            'genus': 'salmonella'} }
        self.assertTrue(pipeline_dry_run.successful_run, 'Exception raised when running a dryrun')
        self.assertEqual(pipeline_dry_run.startup.sample_dict, expected_sample_sheet, pipeline_dry_run.startup.sample_dict)

    def test_junoassembly_dryrun_wMetadata(self):
        """Testing the pipeline runs properly as a dry run when providing 
        a metadata file
        """
        pathlib.Path('fake_dir_wsamples/missingsamp_1.fastq').unlink()
        pathlib.Path('fake_dir_wsamples/missingsamp_2.fastq').unlink()
        pipeline_dry_run = juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    metadata= 'fake_dir_wsamples/fake_metadata.csv',
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
        expected_sample_sheet = {'sample1': {'R1': 'fake_dir_wsamples/sample1_R1.fastq',
                                            'R2': 'fake_dir_wsamples/sample1_R2.fastq.gz',
                                            'genus': 'salmonella'},
                                'sample2': {'R1': 'fake_dir_wsamples/sample2_R1_filt.fq',
                                            'R2': 'fake_dir_wsamples/sample2_R2_filt.fq.gz',
                                            'genus': 'escherichia'},
                                '1234': {'R1': 'fake_dir_wsamples/1234_R1.fastq.gz',
                                            'R2': 'fake_dir_wsamples/1234_R2.fastq.gz',
                                            'genus': 'campylobacter'} }
        self.assertTrue(pipeline_dry_run.successful_run, 'Exception raised when running a dryrun')
        self.assertEqual(pipeline_dry_run.startup.sample_dict, expected_sample_sheet, pipeline_dry_run.startup.sample_dict)

    def test_metadata_overwrites_genus(self):
        """Testing the pipeline runs properly as a dry run when providing 
        a metadata file. If both a genus and metadata are provided, the
        metadata should overwrite the genus (unless sample not present)
        """
        pathlib.Path('fake_dir_wsamples/missingsamp_1.fastq').touch(exist_ok = True)
        pathlib.Path('fake_dir_wsamples/missingsamp_2.fastq').touch(exist_ok = True)
        
        pipeline_dry_run = juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    metadata= 'fake_dir_wsamples/fake_metadata.csv',
                                    genus='salmonella',
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
        expected_sample_sheet = {'sample1': {'R1': 'fake_dir_wsamples/sample1_R1.fastq',
                                            'R2': 'fake_dir_wsamples/sample1_R2.fastq.gz',
                                            'genus': 'salmonella'},
                                'sample2': {'R1': 'fake_dir_wsamples/sample2_R1_filt.fq',
                                            'R2': 'fake_dir_wsamples/sample2_R2_filt.fq.gz',
                                            'genus': 'escherichia'},
                                '1234': {'R1': 'fake_dir_wsamples/1234_R1.fastq.gz',
                                            'R2': 'fake_dir_wsamples/1234_R2.fastq.gz',
                                            'genus': 'campylobacter'},
                                'missingsamp': {'R1': 'fake_dir_wsamples/missingsamp_1.fastq',
                                            'R2': 'fake_dir_wsamples/missingsamp_2.fastq',
                                            'genus': 'salmonella'} }
        self.assertTrue(pipeline_dry_run.successful_run, 'Exception raised when running a dryrun')
        self.assertEqual(pipeline_dry_run.startup.sample_dict, expected_sample_sheet, pipeline_dry_run.startup.sample_dict)

    def test_junoassembly_dryrun_if_metadata_incomplete(self):
        """Testing the pipeline runs properly as a dry run when providing a 
        metadata file and if a sample is not present in the metadata, then no genus
        is assigned
        """
        pathlib.Path('fake_dir_wsamples/missingsamp_1.fastq').touch(exist_ok = True)
        pathlib.Path('fake_dir_wsamples/missingsamp_2.fastq').touch(exist_ok = True)
        pipeline_dry_run = juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    metadata= 'fake_dir_wsamples/fake_metadata.csv',
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)
        expected_sample_sheet = {'sample1': {'R1': 'fake_dir_wsamples/sample1_R1.fastq',
                                            'R2': 'fake_dir_wsamples/sample1_R2.fastq.gz',
                                            'genus': 'salmonella'},
                                'sample2': {'R1': 'fake_dir_wsamples/sample2_R1_filt.fq',
                                            'R2': 'fake_dir_wsamples/sample2_R2_filt.fq.gz',
                                            'genus': 'escherichia'},
                                '1234': {'R1': 'fake_dir_wsamples/1234_R1.fastq.gz',
                                            'R2': 'fake_dir_wsamples/1234_R2.fastq.gz',
                                            'genus': 'campylobacter'},
                                'missingsamp': {'R1': 'fake_dir_wsamples/missingsamp_1.fastq',
                                            'R2': 'fake_dir_wsamples/missingsamp_2.fastq',
                                            'genus': None} }
        self.assertTrue(pipeline_dry_run.successful_run, 'Exception raised when running a dryrun')
        self.assertEqual(pipeline_dry_run.startup.sample_dict, expected_sample_sheet, pipeline_dry_run.startup.sample_dict)

    def test_junoassembly_fails_with_unsupported_genus(self):
        """Testing the pipeline runs properly as a dry run when providing a metadata file"""
        with self.assertRaisesRegex(ValueError, 'not supported. You can leave the "genus" empty'):
            juno_assembly.JunoAssemblyRun(input_dir = 'fake_dir_wsamples', 
                                    genus= 'fakegenus',
                                    output_dir = pathlib.Path('test_output'), 
                                    dryrun = True)



@unittest.skipIf(not pathlib.Path('/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly').exists(),
                    "Skipped in non-RIVM environments (because test data is needed)")
class TestJunoAssemblyPipeline(unittest.TestCase):
    """Testing the junoassembly class (code specific for this pipeline)"""

    def setUpClass():
        os.system('rm -rf test_output')

    def tearDownClass():
        os.system('rm -rf test_output')

    def test_junoassembly_run_wMetadata(self):
        """Testing the pipeline runs properly with real samples when providing
        a metadata file
        """
        juno_assembly_run = juno_assembly.JunoAssemblyRun(input_dir = '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly', 
                                    metadata = '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/metadata.csv',
                                    dryrun=False,
                                    output_dir = pathlib.Path('test_output'))
        expected_sample_sheet = {'sample1': {'R1': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample1_S14_R1_001.fastq.gz',
                                                'R2': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample1_S14_R2_001.fastq.gz',
                                                'genus': 'salmonella'},
                                'sample2': {'R1': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample2_R1.fastq.gz',
                                                'R2': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample2_R2.fastq.gz',
                                                'genus': 'escherichia'},
                                'sample3': {'R1': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample3_R1_001.fastq.gz',
                                                'R2': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample3_R2_001.fastq.gz',
                                                'genus': 'streptococcus'},
                                'sample4': {'R1': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample4_R1.fastq.gz',
                                                'R2': '/data/BioGrid/hernanda/test_data_per_pipeline/Juno_assembly/sample4_R2.fastq.gz',
                                                'genus': 'shigella'} }

        self.assertEqual(juno_assembly_run.startup.sample_dict, expected_sample_sheet, juno_assembly_run.startup.sample_dict)
        self.assertTrue(juno_assembly_run.successful_run, 'Exception raised when running Juno assembly')
        self.assertTrue(pathlib.Path('test_output').joinpath('multiqc', 'multiqc.html').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'log_git.yaml').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'log_pipeline.yaml').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'log_conda.txt').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'snakemake_report.html').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'sample_sheet.yaml').exists())
        self.assertTrue(pathlib.Path('test_output').joinpath('audit_trail', 'log_parameters.yaml').exists())


if __name__ == '__main__':
	unittest.main()